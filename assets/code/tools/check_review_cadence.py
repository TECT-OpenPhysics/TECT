#!/usr/bin/env python3
"""
check_review_cadence.py — review-cadence drift detector for the TECT
records system.

Scans the two ledgers that carry `Last reviewed` / `Review by` date
fields under `docs/policy/UPDATE_POLICY.md` §10.3a and §12.2:

  - docs/status/OPEN-QUESTIONS.md   `## Active` section (Q- entries)
  - docs/status/EVIDENCE-INDEX.md   §1, §2, §3 rows (60-day cadence)

For each entry it computes (today - last_reviewed) in days and
(review_by - today) in days, then prints a report grouped by ledger
and severity.

Severity classes
----------------
  OVERDUE      — today > Review by (days_past > 0)
  UPCOMING     — 0 <= days_until_due <= 7
  OK           — days_until_due > 7

Exit codes
----------
  0   — no OVERDUE entries; the ledger is drift-free.
  1   — one or more OVERDUE entries (only in `--check` mode).

Usage
-----
  python tools/check_review_cadence.py           # human report
  python tools/check_review_cadence.py --check   # CI / §7 audit Layer 3
  python tools/check_review_cadence.py --json    # machine-readable

This script is stdlib-only (no third-party imports). It treats missing
or unparseable date fields as policy violations (severity MISSING,
counted as OVERDUE for exit-code purposes).

Policy source : docs/policy/UPDATE_POLICY.md §10.3a, §12.2
Integration   : §7 audit Layer 3 no-miss checklist
Author owner  : TECT maintainer (jtkor@outlook.com)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Optional

# ---------------------------------------------------------------------------
# Paths (resolved relative to repo root, i.e. parent of this tools/ directory)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
OPEN_QUESTIONS = REPO_ROOT / "docs" / "status" / "OPEN-QUESTIONS.md"
EVIDENCE_INDEX = REPO_ROOT / "docs" / "status" / "EVIDENCE-INDEX.md"

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")

# Default cadences (days) per §10.3a
DEFAULT_CADENCE_OPEN = 30          # OPEN-QUESTIONS ##Active
DEFAULT_CADENCE_EVIDENCE = 60      # EVIDENCE-INDEX §1-§3

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entry:
    ledger: str            # "OPEN-QUESTIONS" | "EVIDENCE-INDEX"
    tag: str               # Q-2026-04-15-01 | INV-<id> | row label
    last_reviewed: Optional[_dt.date]
    review_by: Optional[_dt.date]
    section: str = ""      # e.g. "§2.1" or "Active"
    source_line: int = 0

    def days_overdue(self, today: _dt.date) -> Optional[int]:
        if self.review_by is None:
            return None
        return (today - self.review_by).days

    def severity(self, today: _dt.date) -> str:
        if self.review_by is None or self.last_reviewed is None:
            return "MISSING"
        delta = (self.review_by - today).days
        if delta < 0:
            return "OVERDUE"
        if delta <= 7:
            return "UPCOMING"
        return "OK"


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------
def _parse_date(token: str) -> Optional[_dt.date]:
    m = DATE_RE.search(token or "")
    if not m:
        return None
    try:
        return _dt.date.fromisoformat(m.group(1))
    except ValueError:
        return None


def parse_open_questions(path: Path) -> List[Entry]:
    """Parse OPEN-QUESTIONS.md `## Active` section.

    Entry schema (7 fields, §10.3a):
      - **Tag**:              Q-YYYY-MM-DD-NN
      - **Last reviewed**:    YYYY-MM-DD
      - **Review by**:        YYYY-MM-DD
    """
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    # Restrict to `## Active` section up to (not including) `## Archive`
    active_match = re.search(r"##\s+Active\b(.*?)(?=^##\s+Archive\b|\Z)",
                             text, re.DOTALL | re.MULTILINE)
    if not active_match:
        return []
    active_block = active_match.group(1)

    entries: List[Entry] = []
    # Each entry begins with `### Q-YYYY-MM-DD-NN`
    for m in re.finditer(r"###\s+(Q-\d{4}-\d{2}-\d{2}-\d{2})\b(.*?)(?=^###\s+Q-|\Z)",
                         active_block, re.DOTALL | re.MULTILINE):
        tag = m.group(1)
        body = m.group(2)
        last_reviewed = None
        review_by = None
        # Fields may co-inhabit a single line ("Last reviewed: X | Review by: Y").
        for line in body.splitlines():
            low = line.lower()
            lr = re.search(r"last reviewed[^0-9]*([0-9]{4}-[0-9]{2}-[0-9]{2})",
                           low)
            rb = re.search(r"review by[^0-9]*([0-9]{4}-[0-9]{2}-[0-9]{2})",
                           low)
            if lr and last_reviewed is None:
                last_reviewed = _parse_date(lr.group(1))
            if rb and review_by is None:
                review_by = _parse_date(rb.group(1))
        # Approx source line number
        src_line = text[: active_match.start() + m.start()].count("\n") + 1
        entries.append(Entry(
            ledger="OPEN-QUESTIONS",
            tag=tag,
            last_reviewed=last_reviewed,
            review_by=review_by,
            section="Active",
            source_line=src_line,
        ))
    return entries


def parse_evidence_index(path: Path) -> List[Entry]:
    """Parse EVIDENCE-INDEX.md §1, §2, §3 rows.

    Rows are Markdown table rows. We identify the active section by
    scanning top-level `## §N ...` headings. A row is harvested only
    when inside §1, §2 (and its subsections), or §3.

    A row participates in cadence scanning iff it contains BOTH a
    `Last reviewed: YYYY-MM-DD` and a `Review by: YYYY-MM-DD` token.
    Rows lacking these are treated as structural / not-under-cadence
    and skipped silently. Rows that contain one but not the other are
    flagged as MISSING.
    """
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")

    entries: List[Entry] = []
    current_section: Optional[str] = None
    # Accept "## §1" or "## §2" ... or "## Section 1" etc.
    section_re = re.compile(r"^##\s+(§?\d+[.\w ]*)\s*$")

    for lineno, line in enumerate(text.splitlines(), start=1):
        hm = section_re.match(line)
        if hm:
            label = hm.group(1).strip()
            # Grab leading digit to decide cadence eligibility
            digit_match = re.match(r"§?(\d+)", label)
            if digit_match:
                n = int(digit_match.group(1))
                current_section = label if 1 <= n <= 3 else None
            else:
                current_section = None
            continue

        if current_section is None:
            continue

        # Table row? (starts and ends with |) and contains date tokens
        if not line.lstrip().startswith("|"):
            continue
        if "last reviewed" not in line.lower() and "review by" not in line.lower():
            continue

        last_match = re.search(r"last reviewed[:\s]*([0-9]{4}-[0-9]{2}-[0-9]{2})",
                               line, re.IGNORECASE)
        reviewby_match = re.search(r"review by[:\s]*([0-9]{4}-[0-9]{2}-[0-9]{2})",
                                   line, re.IGNORECASE)

        # Tag: first non-empty cell of the table row
        cells = [c.strip() for c in line.strip("|").split("|")]
        tag = cells[0] if cells else "(unlabeled)"

        entries.append(Entry(
            ledger="EVIDENCE-INDEX",
            tag=tag or "(unlabeled)",
            last_reviewed=_parse_date(last_match.group(1)) if last_match else None,
            review_by=_parse_date(reviewby_match.group(1)) if reviewby_match else None,
            section=current_section,
            source_line=lineno,
        ))
    return entries


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
SEV_ORDER = {"OVERDUE": 0, "MISSING": 1, "UPCOMING": 2, "OK": 3}


def classify(entries: Iterable[Entry], today: _dt.date):
    buckets = {"OVERDUE": [], "MISSING": [], "UPCOMING": [], "OK": []}
    for e in entries:
        buckets[e.severity(today)].append(e)
    return buckets


def human_report(entries: List[Entry], today: _dt.date) -> str:
    lines: List[str] = []
    lines.append("=" * 72)
    lines.append(f" TECT review-cadence audit   (as of {today.isoformat()})")
    lines.append("=" * 72)
    by_ledger: dict = {}
    for e in entries:
        by_ledger.setdefault(e.ledger, []).append(e)

    total_overdue = 0
    total_missing = 0
    for ledger, group in sorted(by_ledger.items()):
        lines.append(f"\n[{ledger}]  ({len(group)} entries)")
        group.sort(key=lambda e: (SEV_ORDER[e.severity(today)],
                                  e.review_by or _dt.date.max))
        for e in group:
            sev = e.severity(today)
            if sev == "OK":
                continue
            if sev == "OVERDUE":
                total_overdue += 1
                days = e.days_overdue(today)
                note = f"OVERDUE by {days:>3} d  (Review by {e.review_by})"
            elif sev == "UPCOMING":
                days = (e.review_by - today).days
                note = f"UPCOMING in {days:>3} d  (Review by {e.review_by})"
            elif sev == "MISSING":
                total_missing += 1
                miss = []
                if e.last_reviewed is None:
                    miss.append("Last reviewed")
                if e.review_by is None:
                    miss.append("Review by")
                note = f"MISSING field(s): {', '.join(miss)}"
            lines.append(f"  - {e.tag:<22}  §{e.section:<8}  {note}"
                         f"   (line {e.source_line})")
        ok_count = sum(1 for e in group if e.severity(today) == "OK")
        lines.append(f"  ({ok_count} entries OK and current)")

    lines.append("")
    lines.append("-" * 72)
    lines.append(f" SUMMARY: {total_overdue} overdue, {total_missing} missing-field, "
                 f"{len(entries)} scanned")
    lines.append("-" * 72)
    if total_overdue == 0 and total_missing == 0:
        lines.append(" STATUS: clean — no drift detected.")
    else:
        lines.append(" STATUS: drift detected — update the flagged entries "
                     "(UPDATE_POLICY.md §10.3a).")
    return "\n".join(lines)


def json_report(entries: List[Entry], today: _dt.date) -> str:
    payload = {
        "as_of": today.isoformat(),
        "entries": [],
    }
    for e in entries:
        d = asdict(e)
        d["last_reviewed"] = e.last_reviewed.isoformat() if e.last_reviewed else None
        d["review_by"] = e.review_by.isoformat() if e.review_by else None
        d["severity"] = e.severity(today)
        d["days_overdue"] = e.days_overdue(today)
        payload["entries"].append(d)
    return json.dumps(payload, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="TECT review-cadence drift detector "
                    "(UPDATE_POLICY.md §10.3a / §12.2).")
    ap.add_argument("--check", action="store_true",
                    help="Exit non-zero if any entry is OVERDUE or has "
                         "MISSING date fields. Intended for §7 audit "
                         "Layer 3 and pre-commit hooks.")
    ap.add_argument("--json", action="store_true",
                    help="Emit a machine-readable JSON report instead of "
                         "the human-readable text report.")
    ap.add_argument("--today", default=None,
                    help="Override today's date (YYYY-MM-DD). Useful for "
                         "deterministic tests.")
    args = ap.parse_args(argv)

    today = _dt.date.today()
    if args.today:
        today = _dt.date.fromisoformat(args.today)

    entries: List[Entry] = []
    entries.extend(parse_open_questions(OPEN_QUESTIONS))
    entries.extend(parse_evidence_index(EVIDENCE_INDEX))

    report = json_report(entries, today) if args.json else human_report(entries, today)
    print(report)

    if args.check:
        bad = sum(1 for e in entries
                  if e.severity(today) in ("OVERDUE", "MISSING"))
        return 0 if bad == 0 else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
