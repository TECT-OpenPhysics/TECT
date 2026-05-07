#!/usr/bin/env python3
# =====================================================================
# paper_need_assessment.py v1.0 (2026-05-07)
#
# Reads recent STATUS-HISTORY.md entries and produces an advisory list of
# new-paper recommendations per the trigger table in
# Docs/policy/MATH_NOTE_AND_PAPER_DISCIPLINE.md §2.
#
# Output: appends a "## Suggested new papers" section to
# Docs/status/paper-impact-report.md (created by paper_status_impact.py).
#
# Recommendations are ALWAYS advisory and NEVER block snapshot promotion.
# The AI collaborator does not auto-draft any paper prose; the operator
# decides whether to act on each recommendation.
#
# Recommendation classes:
#   NEW_CONSOLIDATION_PAPER  : new MAIN-genre paper (T1/T2 -> T7 unconditional)
#   NEW_AUDIT_PAPER          : new TI-genre Comment (T6/T7 -> T0 refutation
#                              when an externally circulated paper claimed the
#                              prior tier)
#   NEW_NEGATIVE_RESULT_NOTE : new AUX-genre note (T1-T4 -> T0 falsification
#                              of a pre-registered gate)
#   PAPER_REVISION_ONLY      : existing draft revision suffices
#   NONE                     : tier change too small / no paper-level action
#
# Governed by Docs/policy/MATH_NOTE_AND_PAPER_DISCIPLINE.md §2.
#
# CLI:
#   python -u Codes/tools/paper_need_assessment.py
#   python -u Codes/tools/paper_need_assessment.py --since 2026-04-15
#   python -u Codes/tools/paper_need_assessment.py --since-days 30
#   python -u Codes/tools/paper_need_assessment.py --report-only        # print to stdout, do not append to report file
# =====================================================================
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HISTORY_MD = REPO_ROOT / "Docs" / "status" / "STATUS-HISTORY.md"
OUT_MD     = REPO_ROOT / "Docs" / "status" / "paper-impact-report.md"

# Reuse the parser from paper_status_impact for STATUS-HISTORY entries
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from paper_status_impact import parse_history_entries  # type: ignore
except ImportError:
    parse_history_entries = None  # type: ignore


def classify_recommendation(entry: Dict[str, object]) -> Dict[str, str]:
    """Return a recommendation dict per MATH_NOTE_AND_PAPER_DISCIPLINE.md §2."""
    cls = entry["class"]
    transition = (entry.get("transition") or "").upper()
    # Heuristic patterns inside the transition string
    targets_t0 = " T0" in transition or "REFUTED" in transition or "REFUTATION" in transition
    targets_t7 = " T7" in transition and ("-> T7" in transition or " UPGRADE" in cls)
    upgrade_to_t7 = (cls == "UPGRADE" and ("T7" in transition or "PROVED" in transition))
    if cls == "REFUTATION" and targets_t0:
        # T6/T7 -> T0 = NEW_AUDIT_PAPER ; T1-T4 -> T0 = NEW_NEGATIVE_RESULT_NOTE
        if any(tag in transition for tag in ("T7", "T6", "PROVED", "PROVED CONDITIONAL")):
            return {
                "class":   "NEW_AUDIT_PAPER",
                "genre":   "TI (PRL Comment)",
                "rationale": "T6/T7 claim refuted by counter-example or "
                              "numerical falsification; an externally citable "
                              "Comment is the appropriate vehicle",
                "title_seed": (
                    f"Paper-TI-NN-{entry['entry_id']}-Refutation-Comment"
                ),
            }
        return {
            "class":   "NEW_NEGATIVE_RESULT_NOTE",
            "genre":   "AUX",
            "rationale": "Lower-tier conjecture / pre-registered gate failed; "
                          "an Auxiliary-style negative-result note documents "
                          "the mechanism",
            "title_seed": (
                f"Auxiliary-NN-{entry['entry_id']}-Negative-Result"
            ),
        }
    if cls == "DOWNGRADE":
        return {
            "class":   "PAPER_REVISION_ONLY",
            "genre":   "n/a (revision)",
            "rationale": "Tier downgrade; existing paper(s) absorb via "
                          "wording calibration. See paper_status_impact.py "
                          "REVISION_REQUIRED list.",
            "title_seed": "",
        }
    if cls == "UPGRADE":
        if upgrade_to_t7:
            return {
                "class":   "NEW_CONSOLIDATION_PAPER",
                "genre":   "MAIN",
                "rationale": "Pillar reached T7 unconditional; a "
                              "self-contained closure paper is appropriate",
                "title_seed": (
                    f"Paper-NN-{entry['entry_id']}-Closure"
                ),
            }
        return {
            "class":   "PAPER_REVISION_ONLY",
            "genre":   "n/a (revision or new AUX if mechanism is novel)",
            "rationale": "Intermediate-tier upgrade; absorbed via existing "
                          "paper revision in most cases",
            "title_seed": "",
        }
    if cls in ("WORDING", "SPLIT"):
        return {
            "class":   "PAPER_REVISION_ONLY",
            "genre":   "n/a (revision)",
            "rationale": "Wording / scope change; revise existing paper(s) "
                          "if any cite the affected pillar tier",
            "title_seed": "",
        }
    return {
        "class":   "NONE",
        "genre":   "—",
        "rationale": "No recommended paper-level action",
        "title_seed": "",
    }


def render_section(entries: List[Dict[str, object]],
                    since_date: datetime) -> Tuple[str, int]:
    """Build the markdown section. Returns (text, count_of_new_paper_recs)."""
    iso_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: List[str] = []
    lines.append("")
    lines.append("## Suggested new papers (advisory)")
    lines.append("")
    lines.append(f"Generated: `{iso_now}`")
    lines.append(f"Window-since: `{since_date.date().isoformat()}`")
    lines.append(f"Source: `Docs/status/STATUS-HISTORY.md`")
    lines.append(f"Policy: `Docs/policy/MATH_NOTE_AND_PAPER_DISCIPLINE.md` §2")
    lines.append("")
    lines.append("Recommendations below are advisory; the operator decides "
                  "whether to draft a new manuscript, revise an existing one, "
                  "defer to OPEN-QUESTIONS, or reject. The AI collaborator "
                  "does NOT auto-draft paper prose (CLAUDE.md §9 binding).")
    lines.append("")
    new_paper_recs = 0
    suggestions: List[Tuple[Dict[str, object], Dict[str, str]]] = []
    for e in entries:
        rec = classify_recommendation(e)
        if rec["class"] != "NONE":
            suggestions.append((e, rec))
        if rec["class"] in ("NEW_AUDIT_PAPER", "NEW_CONSOLIDATION_PAPER",
                             "NEW_NEGATIVE_RESULT_NOTE"):
            new_paper_recs += 1
    if not suggestions:
        lines.append("_No recommendations in this window._")
        lines.append("")
        return ("\n".join(lines) + "\n", 0)
    lines.append("| STATUS-HISTORY entry | Direction | Recommendation | Genre | Title seed |")
    lines.append("|---|---|---|---|---|")
    for e, rec in suggestions:
        title_seed = rec.get("title_seed") or "—"
        lines.append(
            f"| `{e['entry_id']}` ({e['transition'][:40]}) "
            f"| {e['arrow']} [{e['class']}] "
            f"| **{rec['class']}** "
            f"| {rec['genre']} "
            f"| `{title_seed}` |"
        )
    lines.append("")
    lines.append("### Per-recommendation rationale")
    lines.append("")
    for e, rec in suggestions:
        lines.append(f"- `{e['entry_id']}` -> **{rec['class']}**: {rec['rationale']}")
    lines.append("")
    return ("\n".join(lines) + "\n", new_paper_recs)


def append_or_overwrite_section(report_path: Path, section_text: str) -> None:
    """If report already has a 'Suggested new papers' section, replace it;
    otherwise append at end."""
    marker = "## Suggested new papers (advisory)"
    if not report_path.exists():
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(section_text, encoding="utf-8")
        return
    text = report_path.read_text(encoding="utf-8")
    if marker in text:
        idx = text.index(marker)
        # Find next ## heading or EOF
        rest = text[idx:]
        next_h = re.search(r'\n## (?!Suggested new papers)', rest)
        if next_h:
            text = text[:idx] + section_text.lstrip("\n") + rest[next_h.start():]
        else:
            text = text[:idx] + section_text.lstrip("\n")
    else:
        # Append at end
        text = text.rstrip() + "\n\n" + section_text
    report_path.write_text(text, encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--since", type=str, default=None,
                   help="parse only entries on or after this YYYY-MM-DD date")
    p.add_argument("--since-days", type=int, default=90,
                   help="if --since not set, use today - N days as cutoff (default 90)")
    p.add_argument("--report-only", action="store_true",
                   help="print to stdout instead of appending to report file")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    if args.since:
        since_date = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        since_date = datetime.now(timezone.utc) - timedelta(days=args.since_days)

    print(f" paper_need_assessment v1.0 — Window-since: {since_date.date().isoformat()}")

    if parse_history_entries is None:
        print("[paper-need] ERROR: cannot import parse_history_entries from "
              "paper_status_impact.py", file=sys.stderr)
        return 2

    try:
        history_text = HISTORY_MD.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[paper-need] ERROR loading history: {exc}", file=sys.stderr)
        return 2

    entries = parse_history_entries(history_text, since_date)
    print(f"   Parsed {len(entries)} entries")

    section_text, new_paper_recs = render_section(entries, since_date)

    if args.report_only:
        print(section_text)
    else:
        append_or_overwrite_section(OUT_MD, section_text)
        print(f"   Wrote suggested-new-papers section to "
              f"{OUT_MD.relative_to(REPO_ROOT)}")

    print(f"[paper-need] Summary: NEW_PAPER_RECS={new_paper_recs} "
          f"(advisory; never blocks snapshot)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
