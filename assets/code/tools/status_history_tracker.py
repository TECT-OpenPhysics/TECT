#!/usr/bin/env python3
# =====================================================================
# status_history_tracker.py v1.0 (2026-05-07)
#
# Verifies that Docs/status/STATUS-HISTORY.md is in sync with the
# canonical Stage-1 scoreboard at Website/data/status.js (the operational
# single source of truth, mirrored from Docs/status/TOE-FACT-SHEET.md).
#
# Operating modes:
#   --check        : compare scoreboard to STATUS-HISTORY top entries;
#                    report missing entries; exit 1 if any pillar tier
#                    appears in the scoreboard but no STATUS-HISTORY
#                    entry covers a recent (<= --window-days) tier
#                    transition reaching that pillar. Read-only.
#   --diff         : print the per-pillar tier from status.js side-by-
#                    side with the latest STATUS-HISTORY entry that
#                    mentions each pillar. Read-only; informational.
#   --emit-stub    : print a STATUS-HISTORY entry skeleton for a given
#                    pillar (--pillar N --transition T7-to-T0 --note ...);
#                    operator copies/edits before committing.
#                    Does NOT write to STATUS-HISTORY.md (operator-managed).
#
# This tool only emits diagnostics; it never auto-modifies STATUS-HISTORY.md.
# That ledger is operator-curated per CLAUDE.md §3 (atomic-write rule).
#
# Governed by Docs/policy/STATUS_PROPAGATION_POLICY.md §3 and §6.
# =====================================================================
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STATUS_JS = REPO_ROOT / "Website" / "data" / "status.js"
HISTORY_MD = REPO_ROOT / "Docs" / "status" / "STATUS-HISTORY.md"

# Reuse the parser from propagate_status to avoid duplication
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from propagate_status import parse_pillar_tiers  # type: ignore
except ImportError:
    parse_pillar_tiers = None  # type: ignore


def _parse_pillar_tiers_local(text: str) -> List[Dict[str, str]]:
    """Local fallback if propagate_status import fails."""
    section = re.search(r'11-Pillar scoreboard.*?</tbody>', text, re.DOTALL)
    if not section:
        raise ValueError("could not locate 11-Pillar scoreboard in status.js")
    body = section.group(0)
    rows: List[Dict[str, str]] = []
    row_re = re.compile(
        r'<tr><td>(\d+)</td>'
        r'<td>(.*?)</td>'
        r'<td>(.*?)</td>'
        r'<td>(.*?)</td></tr>',
        re.DOTALL,
    )
    for m in row_re.finditer(body):
        def strip_html(s: str) -> str:
            s = re.sub(r'<[^>]+>', '', s)
            s = re.sub(r'\s+', ' ', s).strip()
            return s
        rows.append({
            "pillar":            m.group(1).strip(),
            "subject":           strip_html(m.group(2)),
            "tier":              strip_html(m.group(3)),
            "conditional_input": strip_html(m.group(4)),
        })
    return rows


def parse_history_entries(text: str) -> List[Dict[str, str]]:
    """Parse STATUS-HISTORY.md entries; return list of dicts with keys:
    date, entry_id, direction, pillar_text, transition, body."""
    entries: List[Dict[str, str]] = []
    pat = re.compile(
        r'### Entry (\d{4}-\d{2}-\d{2})-(\d+)\s+(.+?)\s*\n(.*?)(?=\n### Entry |\n## |\Z)',
        re.DOTALL,
    )
    for m in pat.finditer(text):
        date, seq, header_rest, body = m.groups()
        # header_rest has the form "<arrow> -- Pillar X (...)" or similar
        arrow_match = re.match(r'(\S+)', header_rest)
        arrow = arrow_match.group(1) if arrow_match else ""
        pillar_text = header_rest
        transition = ""
        tmatch = re.search(r'\*\*Transition\*\*:\s*([^\n.]+?)(?:\.|$)', body, re.MULTILINE)
        if tmatch:
            transition = tmatch.group(1).strip()
        entries.append({
            "date":         date,
            "entry_id":     f"{date}-{seq}",
            "arrow":        arrow,
            "pillar_text":  pillar_text.strip(),
            "transition":   transition,
            "body":         body.strip(),
        })
    return entries


def latest_entry_for_pillar(entries: List[Dict[str, str]],
                              pillar_num: str) -> Optional[Dict[str, str]]:
    """Find the most recent entry that mentions Pillar <num>."""
    pat = re.compile(rf'Pillar\s*{re.escape(pillar_num)}\b')
    matching = [e for e in entries if pat.search(e["pillar_text"]) or pat.search(e["body"])]
    if not matching:
        return None
    matching.sort(key=lambda e: (e["date"], e["entry_id"]), reverse=True)
    return matching[0]


def cmd_check(rows: List[Dict[str, str]],
              entries: List[Dict[str, str]],
              window_days: int) -> int:
    """Detect pillars whose latest history entry is older than --window-days
    AND whose tier label has changed since (heuristic). Report only;
    operator decides whether to add new entries."""
    today = datetime.now(timezone.utc).date()
    cutoff = today - timedelta(days=window_days)
    print(f"[history-tracker] window-days={window_days} cutoff={cutoff.isoformat()}")
    print(f"[history-tracker] {len(entries)} entries parsed from STATUS-HISTORY.md")
    issues = 0
    for r in rows:
        pillar_num = r["pillar"]
        last = latest_entry_for_pillar(entries, pillar_num)
        if last is None:
            print(f"  Pillar {pillar_num} ({r['subject']}): no STATUS-HISTORY entry "
                  f"(tier {r['tier']!r}); not necessarily an issue (a pillar may "
                  f"never have changed since the ledger began).")
            continue
        try:
            last_date = datetime.strptime(last["date"], "%Y-%m-%d").date()
        except ValueError:
            print(f"  Pillar {pillar_num}: malformed entry date {last['date']!r}",
                  file=sys.stderr)
            issues += 1
            continue
        if last_date < cutoff:
            # Older than cutoff: only an issue if heuristic says tier could have changed.
            # Cheap heuristic: does the entry text mention the current tier label?
            tier_token = r["tier"].split()[0]  # e.g., "T6"
            if tier_token in last["body"] or tier_token in last["transition"]:
                print(f"  Pillar {pillar_num}: latest entry {last['entry_id']} "
                      f"({last['date']}) covers current tier {tier_token}; "
                      f"older than {window_days}d but consistent.")
            else:
                print(f"  Pillar {pillar_num}: latest entry {last['entry_id']} "
                      f"({last['date']}) does NOT mention current tier "
                      f"{tier_token!r}; consider whether a new entry is due.")
                issues += 1
        else:
            print(f"  Pillar {pillar_num}: latest entry {last['entry_id']} "
                  f"({last['date']}) within window; OK.")
    if issues:
        print(f"[history-tracker] {issues} pillar(s) flagged for review.")
        return 1
    print("[history-tracker] OK (no drift detected by current-tier heuristic)")
    return 0


def cmd_diff(rows: List[Dict[str, str]],
             entries: List[Dict[str, str]]) -> int:
    """Print scoreboard tier next to latest history entry per pillar."""
    print("Pillar | status.js tier | last history entry")
    print("-------|----------------|---------------------------------------")
    for r in rows:
        last = latest_entry_for_pillar(entries, r["pillar"])
        last_str = (f"{last['entry_id']} {last['arrow']} {last['transition'][:60]}"
                    if last else "(none)")
        print(f" {r['pillar']:>5s} | {r['tier'][:14]:<14s} | {last_str}")
    return 0


def cmd_emit_stub(pillar: str, transition: str, note: str) -> int:
    """Print a STATUS-HISTORY entry skeleton to stdout."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    arrow_map = {
        "upgrade":   "UPGRADE",
        "downgrade": "DOWNGRADE",
        "refute":    "REFUTATION",
        "wording":   "WORDING",
        "split":     "SPLIT",
    }
    arrow_ascii = ""
    for k, v in arrow_map.items():
        if k in transition.lower():
            arrow_ascii = v
            break
    if not arrow_ascii:
        arrow_ascii = "WORDING"
    print(f"### Entry {today}-NN [{arrow_ascii}] -- Pillar {pillar} (replace with subject)")
    print()
    print(f"**Pillar**: {pillar}")
    print(f"**Transition**: {transition}.")
    print()
    print(f"**Canonical evidence**:")
    print(f"- `Docs/math/TECT-Math<NN>-<descriptor>.tex.txt` (one-line description).")
    print()
    print(f"**R-tag**: `R-{today}-<descriptor>` (if applicable).")
    print()
    print(f"**Rationale**: {note}")
    print()
    print(f"---")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true", help="audit drift; read-only")
    p.add_argument("--diff", action="store_true",
                   help="print scoreboard vs latest entry per pillar")
    p.add_argument("--emit-stub", action="store_true",
                   help="emit a new STATUS-HISTORY entry skeleton to stdout")
    p.add_argument("--window-days", type=int, default=180,
                   help="--check window: pillars whose latest entry is older "
                        "than this AND whose current tier is not mentioned in "
                        "that entry are flagged (default 180)")
    p.add_argument("--pillar", type=str, default="",
                   help="pillar number for --emit-stub")
    p.add_argument("--transition", type=str, default="WORDING",
                   help="transition descriptor for --emit-stub "
                        "(e.g., 'T6 -> T0 refute', 'WORDING')")
    p.add_argument("--note", type=str, default="(rationale here)",
                   help="rationale text for --emit-stub")
    args = p.parse_args()

    if args.emit_stub:
        if not args.pillar:
            print("[history-tracker] --emit-stub requires --pillar N", file=sys.stderr)
            return 2
        return cmd_emit_stub(args.pillar, args.transition, args.note)

    # Read sources
    try:
        status_text = STATUS_JS.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[history-tracker] ERROR: cannot read status.js: {exc}", file=sys.stderr)
        return 2
    try:
        history_text = HISTORY_MD.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[history-tracker] ERROR: cannot read STATUS-HISTORY.md: {exc}",
              file=sys.stderr)
        return 2

    # Parse
    parser_fn = parse_pillar_tiers if parse_pillar_tiers is not None else _parse_pillar_tiers_local
    try:
        rows = parser_fn(status_text)
    except ValueError as exc:
        print(f"[history-tracker] ERROR: {exc}", file=sys.stderr)
        return 2
    entries = parse_history_entries(history_text)

    if args.diff:
        return cmd_diff(rows, entries)
    # default: --check (or no flag)
    return cmd_check(rows, entries, args.window_days)


if __name__ == "__main__":
    sys.exit(main())
