# Website Auto-Sync Policy

**Binding from**: 2026-04-29
**Maintainer**: Jusang Lee (`jtkor@outlook.com`)
**Governed by**: `CLAUDE.md` §10 (records completeness), this policy.

This document defines which website data files are auto-generated from canonical sources, which are hand-curated, and how the two are kept synchronised.

## §1. Per-page sync status

| Menu | Data file | Source | Sync mode | Generator command |
|---|---|---|---|---|
| Overview | `data/index.js` | hand-curated | `@MANUAL_OVERRIDE` | manual edit + latest-status banner card |
| Theory | `data/theory.js` | `_narrative/theory_*.md` + scorecard | `@MANUAL_OVERRIDE` (rendered via NARRATIVE_MAP) | manual narrative edit |
| States | `data/states.js` | hand-curated | `@MANUAL_OVERRIDE` | manual edit + latest-status banner |
| Papers | `data/papers.js` | hand-curated | `@MANUAL_OVERRIDE` | manual edit + admission rule |
| TOE | `data/toe.js` | hand-curated | `@MANUAL_OVERRIDE` | manual edit + latest-status banner |
| Notes | `data/math-notes.js` | `Docs/math/TECT-Math*.tex.txt` | **AUTO** | `python Codes/tools/generate_website.py --math-notes` |
| Code | `data/code.js` | `Codes/{pde,tools,supplementary,scripts,tests}/` | **AUTO** | `python Codes/tools/generate_website.py --code` |
| Results | `data/results.js` | `Runs/<class>/<run_id>/MANIFEST.md + RESULT.md + run_diagnostics.json` | **AUTO (NEW 2026-04-29 v0.6)** | `python Codes/tools/generate_website.py --results` |
| History | `data/history.js` + `data/_archive/history-page-*.js` + `data/timeline.json` | `CHANGELOG.md` | **AUTO** | `python Codes/tools/generate_website.py --history --timeline` |
| Records | `data/records.js` | `OPEN-QUESTIONS.md` + `NEGATIVE-RESULTS.md` | **AUTO** | `python Codes/tools/generate_website.py --records` |

## §2. Latest-status banner card (manual-override pages)

Each `@MANUAL_OVERRIDE` page (Overview / Theory / States / Papers / TOE) has a `Latest status (YYYY-MM-DD) — auto-aware banner` card at the top of its blocks array. The banner is hand-edited weekly (or whenever a major status change lands) to reflect:

- Pillar-level status changes (Pillar 4 sub-task 2/3, GAP-1/2/3/4, etc.)
- Methodology hardening (CLAUDE.md §6.3.x rules)
- Numerical-record infrastructure changes
- Honest-scope notices (what is NOT yet proved unconditionally)

Source narrative: `Website/data/_narrative/_latest_status_<YYYY-MM-DD>.md` — single source of truth, manually composed, propagated to all 5 manual pages on update.

## §3. Master regeneration command

```bash
python Codes/tools/generate_website.py --all
```

This regenerates all AUTO targets (math-notes, timeline, history, theory[narrative-composed], index[narrative-composed], records, results, code) and SKIPS all `@MANUAL_OVERRIDE` files with a `[skipped]` notice. The command is idempotent — running with no source changes produces no diff.

## §4. Stale-detection

- **AUTO files**: compare top-of-file timestamp (`// Generated: YYYY-MM-DD HH:MM UTC`) against latest CHANGELOG / Runs/ mtime; staleness = > 1 day.
- **MANUAL_OVERRIDE files**: compare file mtime against latest-status banner date; staleness = banner date > 7 days behind today.

## §5. New-page additions

When adding a new menu item:

1. Add HTML wrapper at `Website/<page>.html`.
2. Add data file at `Website/data/<page>.js`.
3. Update `Website/data/site.js` navigation array (also `@MANUAL_OVERRIDE`).
4. If hand-curated: add `@MANUAL_OVERRIDE` marker comment + latest-status banner card.
5. If auto-generated: add new `--<page>` argparse flag + `render_<page>_js()` function in `generate_website.py`, update `NARRATIVE_MAP` if the page composes hand-curated narrative.

## §6. Cross-references

- `Codes/tools/generate_website.py` — generator (v0.6, 2026-04-29: results.js auto-gen added).
- `Website/data/_narrative/` — hand-curated narrative cards (composed into AUTO pages).
- `Website/data/_narrative/_latest_status_<DATE>.md` — single-source-of-truth banner narrative.
- `Docs/policy/NUMERICAL_RUN_RECORDING.md` — Runs/<class>/<run_id>/ canonical archive (feeds results.js).
- `Codes/pde/RESULT_TEMPLATE.md` — RESULT.md per-run standard (feeds results.js).
- `Codes/pde/record_run.py` — universal recorder (feeds run_diagnostics.json → results.js).
- `CLAUDE.md` §10 — records completeness binding.

End of WEBSITE_AUTO_SYNC.md (binding from 2026-04-29).
