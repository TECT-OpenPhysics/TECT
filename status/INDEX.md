# TECT Records Index

**Records began**: 2026-04-15 (cutoff declared in `PDE/RECORDS_CUTOFF.md`)
**Governed by**: `docs/policy/UPDATE_POLICY.md`

This is the **single entry point** for anyone — the maintainer, the
AI collaborator, an external reviewer — who needs to locate a
record of any kind in the TECT repository. Every other status
ledger links back here.

---

## Ledgers (the four-ledger model)

| Role | File | Append-only? | Notes |
|---|---|---|---|
| 🏆 **Proved** | `CHANGELOG.md` (repo root), `docs/status/research-log.md`, `Website/data/timeline.json` | Yes | One row per theory tag / milestone |
| 💔 **Failed** | `docs/status/NEGATIVE-RESULTS.md` | Yes, never redacted | `F` (hypothesis) / `R` (result) / `D` (dead-end) |
| ❓ **Open** | `docs/status/OPEN-QUESTIONS.md` | Active + Archive sections | `Q-` tags; 30-/60-/90-day review cadence |
| 🗺️ **Index** | `docs/status/EVIDENCE-INDEX.md` | Live index, rot-repaired | Claim → evidence map; reverse index by file path |

## Sync & code

| Role | File |
|---|---|
| Theory ↔ code mapping | `docs/status/TECT-Theory-Code-Sync.md` |
| Module version registry | `PDE/stamp_version_headers.py::MODULE_VERSIONS` |
| Per-run provenance | `PDE/tect_version_manifest.py` + `PDE/RESULT_TEMPLATE.md` |
| Data artefacts (site) | `Website/data/version_index.json`, `Website/data/timeline.json` |

## Automation

| Tool | Role | Invocation |
|---|---|---|
| `tools/check_review_cadence.py` | Detect overdue `Last reviewed` / `Review by` in OPEN-QUESTIONS + EVIDENCE-INDEX §1–§3 (UPDATE_POLICY §10.3a, §12.2) | `python tools/check_review_cadence.py [--check] [--json]` |
| `tools/build_version_index.py` | Regenerate `Website/data/version_index.json` from `PDE/tect_version_manifest.py` | `python tools/build_version_index.py [--check]` |
| `PDE/stamp_version_headers.py` | Re-stamp `__version__` / `__theory_version__` in live `PDE/*.py` | `python PDE/stamp_version_headers.py` |

## Policy

| Role | File |
|---|---|
| Trigger → target rulebook | `docs/policy/UPDATE_POLICY.md` (§1–§6) |
| Full-repo audit procedure | `docs/policy/UPDATE_POLICY.md` §7 |
| Failure discipline | `docs/policy/UPDATE_POLICY.md` §9 |
| Records completeness + queryability | `docs/policy/UPDATE_POLICY.md` §10 |
| Manuscript authorship (manual-only) | `docs/policy/UPDATE_POLICY.md` §11 |
| Automation tooling | `docs/policy/UPDATE_POLICY.md` §12 |
| Git tags | `docs/policy/GIT_TAG_POLICY.md` |
| Records cutoff (pre-2026-04-15 treatment) | `PDE/RECORDS_CUTOFF.md` |

## Archive (pre-cutoff material, not cited as evidence)

- `docs/archive/chat-gpt/` — 40 exploratory transcripts.
- `docs/archive/gemini-notebooklm/` — 6 external-LLM transcripts.
- `docs/math/TECT_Math01-35_Merged_260409_214200.txt` — pre-cutoff merged compilation.
- Any pre-2026-04-15 run directory in `PDE/data_pt_*/`, `PDE/run_*/`: historical only.

---

## How to answer any question (seven-question contract)

| If asked… | Consult, in order: |
|---|---|
| 1. "Why this value / sign / regime?" | `EVIDENCE-INDEX.md` §1 or §2 → primary file. |
| 2. "Has this been retracted or disproved?" | `NEGATIVE-RESULTS.md` (search by claim). |
| 3. "What is currently open / unproven?" | `OPEN-QUESTIONS.md` `## Active` + Sync Manifest §2. |
| 4. "Provenance of this run?" | Run dir's `tect_version_manifest.json` + `RESULT.md` (post-cutoff only). |
| 5. "Which code version implements which claim?" | Sync Manifest §1 (has line-range pointers). |
| 6. "When and why did this change?" | `CHANGELOG.md` + Sync Manifest §5 Sync Log. |
| 7. "Where does the old file live now?" | `CHANGELOG.md` Math39-Reorg entry + `git log --follow`. |

Failure to answer any of the seven using at most three files is a
policy violation; repair in next commit (UPDATE_POLICY §10.5).

---

## Review cadence

| Artefact | Cadence |
|---|---|
| `OPEN-QUESTIONS.md` active entries | 30 days default (longer window must be justified in-entry) |
| `EVIDENCE-INDEX.md` §1–§3 rows | 60 days — stale rows flagged by the §7 full-repo audit |
| `NEGATIVE-RESULTS.md` | Never rotates; append-only |
| `CHANGELOG.md` | Append-only; one section per theory tag |
| Website per-page footer timestamps | Bumped only when the page content is actually edited |

---

## Maintainer

Jusang Lee (`jtkor@outlook.com`)
