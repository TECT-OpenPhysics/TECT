# Repository Restructure Roadmap (Phase B / C)

**Status**: planning + partial v0 scaffold (2026-05-07)
**Maintainer**: Jusang Lee (`jtkor@outlook.com`)
**Governed by**: `CLAUDE.md` §13 (file-location discipline), `REPO_LAYOUT.md` (canonical destination matrix), `STATUS_PROPAGATION_POLICY.md` (post-2026-05-07 automation foundation).

The 2026-05-07 work session installed the status-propagation automation (Phase A: A15--A20) and renamed the States page to Status for naming consistency. This document records the **deferred Phase B and Phase C work** in a single canonical place so the next session has a clear handoff and the operator has visibility into what is and is not complete.

---

## §1. What is COMPLETE (Phase A)

The following is binding from 2026-05-07.

| Item | Artefact | Status |
|---|---|---|
| Status propagation policy | `Docs/policy/STATUS_PROPAGATION_POLICY.md` | binding |
| Math-note + paper discipline policy | `Docs/policy/MATH_NOTE_AND_PAPER_DISCIPLINE.md` | binding |
| `states.js` -> `status.js` rename + redirect | site-wide | binding |
| `propagate_status.py` v1.0 | `Codes/tools/propagate_status.py` | working; idempotent |
| `paper_status_impact.py` v1.0 | `Codes/tools/paper_status_impact.py` | working |
| `paper_need_assessment.py` v1.0 | `Codes/tools/paper_need_assessment.py` | working |
| `status_history_tracker.py` v1.0 | `Codes/tools/status_history_tracker.py` | working |
| Externalised target list | `Codes/config/status_propagation_targets.json` | active |
| Snapshot pipeline integration | `Codes/scripts/snapshot.ps1` step 2.5b/c/d | wired |
| `verify_website.py` patch | sidecar + deprecation-stub recognition | applied |
| Audit log | `Docs/status/propagation-log.md` | active |
| Auto report | `Docs/status/paper-impact-report.md` | active |

Round-trip validated end-to-end: `propagate_status.py --check` and `verify_website.py` both exit 0; the snapshot pipeline integrates the new tools without breaking existing steps.

---

## §2. What is DEFERRED (Phase B) — partial closure 2026-05-07; §2.1/2.2/2.3 SUPERSEDED-BY-Math353

**2026-05-07 partial closure**: Phase B-1 (`/site` scaffold), Phase B-3 (`.gitignore` extension for `.tmp.driveupload/` + root orphan patterns), and Phase B-4 (Codes/deprecated/ audit — confirmed already cleaned, no `Codes/deprecated/` directory exists; one residual `*.old.*.py` archive in `Codes/pde/` excluded via integrity-tool filename pattern) are CLOSED. Phase B-2 (`github_sync_curate.py` v1.1 refactor to read `mirror.json`) is now LANDED in §2.4.

**2026-05-07 supersession (Math353)**: Phase B-5/6/7 (lowercase `code/` rename, `Runs/` -> `code/runs/`, `Docs/manual/` -> `code/manual/`) is **SUPERSEDED-BY-Math353** (`Docs/math/TECT-Math353-Mirror-First-Restructure-Strategy-Framework.tex.txt`). The lowercase-rename approach is REPLACED by a mirror-first plan: local tree retains `Codes/`, `Docs/`, `Runs/`, `Website/` naming; the rename + content-path-rewrite happens at the `github_sync_curate.py` v2 mirror boundary, not on the local canonical tree. See Math353 for full rationale, Phase B-revised work breakdown, and Phase C-revised. `Codes/scripts/migrate_to_lowercase_code.py` v1.1 retired with header banner. The original §2.1/2.2/2.3 text below is retained for audit history and is **NOT operative**.

Phase B is the major repository structural refactor. v0 scaffolds are in place under `Codes/config/` (mirror.json, website_pages.json, sweep_rules.json). The full refactor is deferred because:

1. The Phase A automation must demonstrate at least one snapshot cycle of stability before the layer beneath it is restructured.
2. `github_sync_curate.py` is large (~700 lines) and the v1 refactor (read from `Codes/config/mirror.json`) must preserve existing mirror behaviour exactly while changing only the source of the allowlist.
3. The operator wants to validate the v0 scaffold semantics first.

### §2.1 Repository tree restructure — [SUPERSEDED-BY-Math353 2026-05-07] automated migration script LANDED then RETIRED 2026-05-07

The intended end state per the 2026-05-07 plan was a lowercase-`code/`-rooted layout: `CITATION.cff, LICENSE, README.md, CHANGELOG.md, code/, math/, papers/, status/, site/`. The current canonical root still uses `Codes/`, `Docs/`, `Runs/`, etc.

**Migration helper (committed in this Math352 commit)**: `Codes/scripts/migrate_to_lowercase_code.py` v1.0 automates the entire B-5/6/7 rename atomically:

- Phase 1: three `git mv` operations (`Codes/` -> `code/`, `Runs/` -> `code/runs/`, `Docs/manual/` -> `code/manual/`).
- Phase 2: 2,022 cross-reference replacements across 223 files (Python imports, PowerShell paths, Markdown links, Math-note cite refs, JSON config), all via `safe_write.atomic_write` -> truncation-proof.
- Pre-flight: refuses to run --apply if git working tree is dirty OR if `Runs/` has active driver locks / recent JSON activity.
- Post-apply --verify: runs `check_file_integrity --strict` + `verify_website` + `propagate_status --check`; aborts with rollback hint if any fail.
- Rollback path: `git restore --source=HEAD --staged --worktree .` (script writes only working tree; HEAD is always safe).

**Operator instructions** (when ready to migrate):

```powershell
# 1) Verify current tree is clean + committed
git status

# 2) Dry-run preview — shows the 2,022 replacement plan
python -u Codes\scripts\migrate_to_lowercase_code.py

# 3) Apply (in a dedicated session, no in-flight runs)
python -u Codes\scripts\migrate_to_lowercase_code.py --apply --verify

# 4) Commit + snapshot
git -c user.email="jtkor@outlook.com" -c user.name="Jusang Lee" commit -m "Phase B-5/6/7: Codes/->code/ + Runs/->code/runs/ + Docs/manual/->code/manual/ atomic migration; 2,022 cross-refs updated"
.\Codes\scripts\snapshot.ps1 -Message "Phase B-5/6/7 closure"
```

**Recommended timing**: run between numerical campaigns when no driver is writing to Runs/. The script is idempotent at the dry-run level (re-running prints the same plan), but --apply is destructive in the sense that paths in code stop working until the snapshot regenerates the Website mirror.

### §2.2 `code/runs/` consolidation — [SUPERSEDED-BY-Math353 2026-05-07] (was: deferred; gated on §2.1 lowercase rename)

The 2026-05-07 plan called for `Runs/` to become `code/runs/`. The current `Runs/` tree contains many large `.npy` files in `Runs/seeds/` and run output in `Runs/<class>/<run_id>/`. The consolidation:

- moves the directory.
- updates every `RunRecorder` invocation in `Codes/pde/record_run.py` to use the new path.
- updates per-run citation paths in `Docs/math/*.tex.txt` and Website/data/results.js.

Risk: in-flight numerical runs that write to the old path will break. v1 plan: rename only between snapshot cycles, with a one-snapshot-cycle warning window where the old path emits a deprecation message.

### §2.3 `Docs/manual/` -> `code/manual/` — [SUPERSEDED-BY-Math353 2026-05-07] (was: deferred)

Same risk profile as §2.2. The v1 plan is to move `Docs/manual/CODE_MANUAL.md` and friends into `code/manual/` so the operator-level documentation lives next to the code it documents. UPDATE_POLICY §13 references must be updated atomically.

### §2.4 Code allowlist mirror — v1.1 LANDED 2026-05-07

**Status update (2026-05-07)**: After inspecting the actual code structure, the originally planned "CATEGORIES refactor" was not applicable: `github_sync_curate.py` does not have a code-allowlist constant; the public mirror simply reflects whatever `Website/assets` contains, and the actual filtering happens one layer earlier in `generate_website.py::copy_assets`.

The realised v1.1 refactor (committed in this Math352 commit) adds an `EXCLUDE_FROM_MIRROR` opt-in feature:

- New helper `_load_mirror_excludes()` reads `Codes/config/mirror.json`.
- `prune_stale_files()` translates `Website/...` paths to Github-relative form and adds the exclude list to its removal walker.
- Default `active_v1_0: []` -> behaviour identical to pre-v1.1 (no behaviour change unless operator opts in).
- Verified: `python -u Codes/tools/github_sync_curate.py --check` -> 46 modified, 982 unchanged, 0 removed (empty exclude list = unchanged).

**Operator instructions**: to hide internal-ops policy files from the public mirror, edit `Codes/config/mirror.json` -> `exclude_from_mirror.active_v1_0` -> add path entries (e.g., `"Website/assets/policy/POSTMORTEM_RECURRENCE_POLICY.md"`). The list of v1.1 candidates is in the same JSON file. Next snapshot will prune them from Github/.

The deeper v2 refactor (direct Codes/-allowlist that bypasses Website/assets entirely) remains deferred per `mirror.json::v2_planned_targets`.

### §2.5 `/site` for future GitHub Pages (deferred)

The current Website/ tree is the operational frontend. GitHub Pages activation in the future would mirror Website/ into a `/site` folder at the public-mirror root. The v0 scaffold is just a placeholder; v1 will:

- create `site/` at the public mirror's root with an explicit `Codes/tools/github_sync_curate.py --copy-to-site` flag.
- add a Pages-friendly default `_config.yml` (or `.nojekyll` plus relative-path discipline).
- update `github_sync_curate.py` so the `Github/` tree gains a `site/` sibling without disturbing `Github/`'s primary role.

### §2.6 Old code via git tags (deferred)

The 2026-05-07 plan established that git tags are the canonical version archive (no separate `code-old/` folder). The deferred work:

- migrate `Codes/deprecated/` content into git history with annotated tags `code-vN-<descriptor>`.
- collapse `Website/data/code-old.js` into a git-tag listing rather than a per-file mirror.
- update `audit_website_freshness.py` to recognise the new tag-driven listing.

---

## §3. What is DEFERRED (Phase C)

Phase C is the public-facing narrative + GitHub metadata sweep. v0 partial work landed in 2026-05-07.

### §3.1 BCC narrative softening (partial v0)

The 2026-05-07 session removed the most acute "BCC is the unique mean-field maximiser" claims from `theory.js` Honest Limitations card (covering Math348 refutation + Math350 deep-regime saddle). `Codes/config/sweep_rules.json` v0 documents the canonical replacement rules but does NOT auto-apply them. The deferred Phase C work:

- run `refine_continuum_language.py` v2 (reading `sweep_rules.json`) across `Website/data/_narrative/*.md`, `Github/README.md`, and `papers.js` cards.
- audit `Github/README.md` for forbidden phrases (CLAUDE.md §7 list).
- update Math-note narrative to reflect the regime-dependent BCC-stability picture.

### §3.2 README.md rewrite (deferred)

A new repo-root `README.md` is part of the final-state plan but has not been written. The current `Github/README.md` is auto-generated from `github_sync_curate.py`. The v1 plan:

- author a minimal repo-root `README.md` that points to `Github/README.md` for the public-facing version.
- include a "How to run the pipeline" 5-line operator-quickstart.
- the AI collaborator must NOT auto-draft this prose (CLAUDE.md §9); the operator authors.

### §3.3 GitHub metadata refresh (deferred)

Repo description + topics + about-page on github.com are set via the GitHub API or web UI. The 2026-05-07 plan called for a refresh; this requires explicit operator action. Recommended:

- Description: "Topological Energy Condensate Theory: a candidate Theory of Everything built on a two-axiom Brazovskii-universality foundation. Open physics independent research."
- Topics: `theory-of-everything`, `physics`, `brazovskii`, `topological-condensate`, `gauge-theory`, `general-relativity`, `numerical-relativity`, `lattice-gauge-theory`, `peer-reviewable-pre-print`.

The repo is currently set up; the metadata refresh is operator-only.

---

## §4. Recommended order for the next session

1. Validate one full snapshot cycle of the Phase A automation (Phase D).
2. Author Math352 documenting Phase A closure (this session's work).
3. Defer Phase B until at least one external reviewer (or the operator) has used the Phase A tools end-to-end.
4. Phase C narrative softening can be done piecewise as new content lands; no big-bang sweep is required.

---

## §5. Cross-references

- `CLAUDE.md` §13 — file-location discipline
- `Docs/policy/REPO_LAYOUT.md` — canonical destination matrix
- `Docs/policy/STATUS_PROPAGATION_POLICY.md` — Phase A foundation (binding)
- `Docs/policy/MATH_NOTE_AND_PAPER_DISCIPLINE.md` — paper-impact + new-paper rules (binding)
- `Codes/config/mirror.json` — v0 scaffold for §2.4
- `Codes/config/website_pages.json` — v0 scaffold for §2.5 / generate_website.py v1
- `Codes/config/sweep_rules.json` — v0 scaffold for §3.1

End of REPO_RESTRUCTURE_ROADMAP.md (binding from 2026-05-07 as a planning document; v1 supersedes when committed).
