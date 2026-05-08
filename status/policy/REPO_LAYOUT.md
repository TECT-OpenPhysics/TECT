# TECT Repository Layout Policy

**Binding from**: 2026-04-23
**Canonical from**: 2026-04-23 (Codes/ + Runs/ introduced; original paths retained during Task #54 execution; migration to canonical-only paths scheduled for post-Task-#54 commit)
**Policy hook**: `UPDATE_POLICY.md` §14 (NEW — this document's entry point)
**Maintainer**: Jusang Lee (jtkor@outlook.com)

---

## 1. Top-level directory layout

Every entity under `Contents/` belongs to one of the canonical top-level folders below. Any file or folder that does not fit one of these categories is either (a) orphan and should be removed, or (b) mis-filed and should be moved.

```
Contents/
├── Codes/              # ALL executable code (canonical from 2026-04-23)
├── Runs/               # ALL execution artifacts (canonical from 2026-04-23)
├── Docs/               # theory notes, manuals, papers, policy, runbooks, status
├── Website/            # static-site deliverable
├── Backup/             # pre-restructure snapshots; write-once, read-only
├── CHANGELOG.md        # single source of truth for change history
├── NAVIGATION.md       # human-readable map of the tree
├── tect-research.plugin  # Cowork plugin bundle (kept at root per Cowork convention)
├── .git/               # git state
├── .gitignore
└── .pytest_cache/      # transient pytest cache (ignored)
```

**As of 2026-04-24, all deprecated-but-live paths have been retired (Phase 2 A+B+C+D+E+F complete).** The repository root now matches the canonical layout in §1 exactly.

The following directories were retired in the 2026-04-24 cleanup commits:

```
Contents/tools/           # RETIRED (Phase C)   → Codes/tools/
Contents/tests/           # RETIRED (Phase C)   → Codes/tests/
Contents/scripts/         # RETIRED (Phase C)   → Codes/scripts/
Contents/runs/            # RETIRED (Phase C)   → Runs/legacy/
Contents/continuation_v263_smoke/  # RETIRED (Phase B; was empty)
Contents/results/         # RETIRED (Phase D)   → Runs/audit/
Contents/PDE/             # RETIRED (Phase E+F) → Codes/pde/ (modules)
                                                + Runs/historical/<32 subtrees>
                                                + Docs/policy/ (RECORDS_CUTOFF, RESULT_TEMPLATE, RETRO_MANIFEST_NOTE)
                                                + Codes/scripts/ (.bat)
                                                + Runs/legacy/ (Phase_1 result txt)
                                                + Backup/pre-PDE-retirement-2026-04-24/ (deprecated subtree)
```

The full cleanup audit trail is in:
- `Docs/math/TECT-Math82-Repo-Cleanup-Phase2.tex.txt` (Phases A+B+C)
- `Docs/math/TECT-Math82-Addendum-A-Phase-D-results-propagation.tex.txt` (Phase D)
- `Docs/math/TECT-Math82-Addendum-C-Phase-E-F-PDE-retirement.tex.txt` (Phase E+F)

---

## 2. Canonical layout (from 2026-04-23)

### 2.1 `Codes/` — executable code

`Codes/` is the single canonical home for every Python script, PowerShell script, shell script, pytest file, and code-adjacent configuration file in the repository. Inside `Codes/`, sub-folders are lowercase and named by role.

```
Codes/
├── pde/            # PDE / solver / backend / simulation drivers
│   ├── continuation_mu2_v25.py
│   ├── tect_newton_krylov.py
│   ├── real_backend_pt_bcc_mixed_v3.py
│   ├── bz_preconditioner.py
│   ├── math56_constants.py
│   ├── config_template_brazovskii.json
│   ├── config_mu2_target_5e3.json
│   └── ...  (38 .py + 4 .json)
├── tools/          # stand-alone diagnostic / audit / utility scripts
│   ├── check_jacobian_blocks.py
│   ├── check_jacobian_symmetry.py
│   ├── n64_continuum_audit.py
│   ├── monopole_vacuum_mc.py
│   └── ...  (9 .py)
├── tests/          # pytest module suite
│   ├── conftest.py
│   ├── test_v263_continuation_routing.py
│   ├── test_v262_cii_mask.py
│   ├── test_v26_phase_d.py
│   ├── test_n64_audit.py
│   ├── test_n64_audit_v1p2.py
│   ├── test_v24_gate_integration.py
│   ├── test_v24_thresholds.py
│   └── test_monopole_mc.py  (9 .py)
├── scripts/        # PowerShell / Bash orchestration scripts
│   ├── run_v25_diagnostic.ps1
│   ├── run_v25_diagnostic.sh
│   ├── commit_v25_diagnostic.ps1
│   ├── git_bootstrap.ps1
│   └── diag_tools_import.py  (5 files)
├── supplementary/  # verification / analytic-sanity scripts for theory notes
│   ├── verify_anisotropy_separation_v4_2.py
│   ├── Math_IR_Bound_v4_BZ_interval.py
│   ├── Math49_hrr_v3.py
│   ├── Math49d_BWB_Zomega_exact.py
│   ├── Math49d_equivariant_bott.py
│   ├── Math49d_gauge_flavor_audit.py
│   ├── Math49d_R5_replacement_search.py
│   ├── Math49d_R5_replacement_search_wave2.py
│   ├── Math57_shell_angular_interval.py
│   ├── Math57_v2_cubic_anisotropy_interval.py
│   └── v24_threshold_sympy_check.py  (11 .py)
└── README.md
```

### 2.2 `Runs/` — execution artifacts

`Runs/` is the single canonical home for every execution output, log, MANIFEST, endpoint JSON, and result snapshot. Inside `Runs/`, sub-folders are lowercase and named by artifact class.

```
Runs/
├── audit/          # JSON snapshots from tools/check_jacobian_* and audit scripts
│   ├── math64_decisive_cII_test*.json
│   ├── n64_audit_2026-04-22.json
│   ├── stage_alpha_*.json
│   └── stage_alpha_archive_sha256.txt
├── continuation/   # endpoint-JSON outputs from continuation_mu2_v25
│   ├── math55_endpoint_N32_L16_2026-04-23/
│   └── continuation_v263_smoke/
├── legacy/         # historical runs from v2.4 / v2.5 era
│   ├── R-2026-04-21-001-*.md
│   ├── R-2026-04-21-002-*.md
│   ├── R-2026-04-22-001-newton-krylov-v25-diagnostic/
│   ├── R-2026-04-23-001-task54-mu2target-5e-3/
│   ├── R-2026-04-23-002-task54-coarse-smoke/
│   ├── math49c_v3_sim_summary.json
│   └── math49c_v3_sim_summary_N1601.json
├── logs/           # long-running log files (N=256 BZ integrals, etc.)
│   └── Math_*.log
└── README.md
```

### 2.3 `Docs/` — theory and management content

`Docs/` is unchanged by the 2026-04-23 restructure. It holds non-executable content: theory notes, the code manual, papers, policy documents, runbooks, and status ledgers.

```
Docs/
├── archive/        # conversation dumps from upstream LLM sessions
├── manual/
│   └── CODE_MANUAL.md
├── math/           # TECT-Math<NN>-*.tex.txt (127 theory notes)
├── papers/         # publication-ready LaTeX manuscripts
├── policy/
│   ├── UPDATE_POLICY.md
│   └── REPO_LAYOUT.md  (this file)
├── runbooks/
│   └── v263_execution_verification_runbook.md
├── status/         # DEVILS-ADVOCATE, EVIDENCE-INDEX, OPEN-QUESTIONS, RIGOR-AUDIT, ...
└── supplementary/  # content PDFs (PDE-Blueprint.pdf, tect_toe_proof_roadmap.pdf)
                    # NOTE: the .py verification scripts previously under
                    # Docs/supplementary/ have moved to Codes/supplementary/
                    # as of 2026-04-23.
```

### 2.4 `Backup/` — immutable snapshots

`Backup/` contains pre-restructure snapshots. **Write-once, read-only after creation.** Do not modify files here. Use for recovery and audit only.

```
Backup/
└── pre-restructure-2026-04-23/
    └── code/
        ├── PDE_py/               (38 .py + 4 .json)
        ├── tools/                (9 .py)
        ├── tests/                (9 .py)
        ├── scripts/              (5 files)
        └── Docs_supplementary_py/  (11 .py)
```

---

## 3. Case-convention rules

Cross-platform robustness (Linux sandbox is case-sensitive; Windows NTFS is case-insensitive but preserves case) demands a strict convention.

| Layer | Rule | Example |
|---|---|---|
| Top-level folders under `Contents/` | PascalCase | `Codes`, `Runs`, `Docs`, `Website`, `Backup` |
| Subfolders under `Codes/` | lowercase | `pde`, `tools`, `tests`, `scripts`, `supplementary` |
| Subfolders under `Runs/` | lowercase | `audit`, `continuation`, `legacy`, `logs` |
| Subfolders under `Docs/` | lowercase | `math`, `manual`, `papers`, `policy`, `runbooks`, `status`, `archive`, `supplementary` |
| Python module files | snake_case.py | `continuation_mu2_v25.py`, `tect_newton_krylov.py` |
| Math notes | `TECT-Math<NN>-<descriptor>.tex.txt` with hyphens | `TECT-Math74-Addendum-B-v264-gate-semantic-fix.tex.txt` |
| Status ledgers | UPPER-CASE with hyphens | `OPEN-QUESTIONS.md`, `EVIDENCE-INDEX.md` |
| Policy + manual | UPPER_SNAKE_CASE or PascalCase | `UPDATE_POLICY.md`, `CODE_MANUAL.md`, `REPO_LAYOUT.md` |

**Past case-collision remediation.** Task #101 (closed 2026-04-22) renamed `Tools/` → `tools/` on the Windows-side repo. The git index may still contain stale `Tools/` entries (as observed 2026-04-23); a follow-up `git rm --cached Tools/... && git add Codes/tools/...` pass is required after this restructure lands. **Do NOT** simultaneously commit a file at both `Tools/X.py` and `tools/X.py` — the case collision re-emerges on Windows.

**Forbidden.** Mixed-case synonyms that differ only in casing (e.g.\ `Tools/` next to `tools/`, `Docs/` next to `docs/`) are forbidden at any layer. If a reference to a lower-case variant appears in code or documentation, treat it as a bug and fix it.

---

## 4. Migration status (updated 2026-04-24, Phase 2 A+B+C executed)

Migration phase: **Phase 2A+B+C executed (2026-04-24); Phase 2D-F deferred to post-Task-#54 closure**.

See `Docs/math/TECT-Math82-Repo-Cleanup-Phase2.tex.txt` for the cleanup
plan, audit trail, and rationale per phase.

| Old path | New canonical path | Status |
|---|---|---|
| `Contents/PDE/*.py` (38 files) | `Contents/Codes/pde/*.py` | copied; **PDE/ kept live** for Task #54 (Phase E-F pending) |
| `Contents/PDE/*.json` (4 files) | `Contents/Codes/pde/*.json` | copied |
| `Contents/PDE/<historical-data-subfolders>` (data_pt_*, continuation_*, newton_rigorous_*, emerge_*, backup_GL_*, bcc_compare/, bcc_recalib64/, deprecated/) | `Contents/Runs/historical/` (planned) | **Phase E pending** — per-folder review required |
| `Contents/tools/*.py` (9 files) | `Contents/Codes/tools/*.py` | **RETIRED 2026-04-24** (Phase C; byte-equal except __pycache__) |
| `Contents/tests/*.py` (9 files) | `Contents/Codes/tests/*.py` | **RETIRED 2026-04-24** (Phase C; byte-equal except __pycache__) |
| `Contents/scripts/*` (5 files + 1 unique) | `Contents/Codes/scripts/*` | **RETIRED 2026-04-24** (Phase C; unique `verify_dirac_casimir_toy.py` preserved by copy first) |
| `Contents/Docs/supplementary/*.py` | `Contents/Codes/supplementary/*.py` | copied (no retirement; Docs/supplementary/ also holds non-script PDF content) |
| `Contents/results/*` (11 files) | `Contents/Runs/audit/* + Runs/continuation/*` | copied; **Phase D pending** — `results/` still holds genuine recent outputs (`math55_endpoint_*`, `math64_*`, `dirac_casimir.png`) not yet propagated to `Runs/` |
| `Contents/runs/*` (16 files) | `Contents/Runs/legacy/*` | **RETIRED 2026-04-24** (Phase C; byte-equal except README) |
| `Contents/continuation_v263_smoke/` (empty in git) | `Contents/Runs/continuation/continuation_v263_smoke/` | **RETIRED 2026-04-24** (Phase B; was empty) |
| `Contents/AUTONOMOUS_SESSION_REPORT_2026-04-21.md` | `Contents/Docs/status/AUTONOMOUS_SESSION_REPORT_2026-04-21.md` | moved; **2026-04-24: root-level duplicate DELETED** (Phase A) |
| `Contents/AUTONOMOUS_SESSION_REPORT_2026-04-24-ROUND4-PROOF-A.md` | `Contents/Docs/status/round-summaries/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/ROUND6_SESSION_SUMMARY.txt` | `Contents/Docs/status/round-summaries/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/ROUND7-PROOF-B-SESSION-SUMMARY.txt` | `Contents/Docs/status/round-summaries/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/TECT-AUTONOMOUS-SESSION-SUMMARY-2026-04-24.txt` | `Contents/Docs/status/round-summaries/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/TECT-KOREAN-SUMMARY-ROADMAP.txt` | `Contents/Docs/status/round-summaries/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/FINAL_SESSION_STATUS.txt` | `Contents/Docs/status/round-summaries/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/INDEX-ROUND7-DELIVERABLES.txt` | `Contents/Docs/status/round-summaries/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/KOREAN-STATUS-REPORT-ROUND7.txt` | `Contents/Docs/status/round-summaries/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/.round7-proof-c-executive-summary.txt` | `Contents/Docs/status/round-summaries/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/.round7-proof-c-traceability.txt` | `Contents/Docs/status/round-summaries/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/PASTE-READY-MATH60-S3-ROUND7-CHANGELOG.txt` | `Contents/Docs/math/paste-ready-archive/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/PASTE-READY-MATH75-Q3-PILLAR4-FINAL.txt` | `Contents/Docs/math/paste-ready-archive/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/PASTE-READY-PILLAR11-v6-SUMMARY.txt` | `Contents/Docs/math/paste-ready-archive/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/CHANGELOG-Pillar1-v2.txt` | `Contents/Docs/math/paste-ready-archive/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/CHANGELOG-Pillar11-v6-Dirac-sector-closure.txt` | `Contents/Docs/math/paste-ready-archive/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/CODE_MANUAL-Math75-Q3-Entry.txt` | `Contents/Docs/manual/manual-entries-archive/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/CODE_MANUAL-Pillar11-v6-Dirac-entry.txt` | `Contents/Docs/manual/manual-entries-archive/` | **MOVED 2026-04-24** (Phase A) |
| `Contents/.test_write` | — | orphan; resolved on Windows side |
| `Contents/.tmp.driveupload` | — | orphan; resolved on Windows side |
| `Contents/tect-research.plugin` | (kept at root per Cowork convention) | unchanged |
| `Contents/CLAUDE.md` (NEW 2026-04-24) | (canonical at root per Cowork / Claude convention) | NEW — master AI-collaborator entry document |

**Retirement criteria (Phase 2).** After Task #54 closes with a valid `continuation_mu2_v25_endpoint/1.1` JSON at `Runs/continuation/math55_endpoint_N32_L16_2026-04-23/`:

1. Verify byte-equality between each file pair in the old/new paths (`diff -rq`).
2. Update every import / path reference in Math notes, CODE_MANUAL, CHANGELOG, runbooks, and scripts to use the `Codes/` / `Runs/` paths.
3. `git rm -r PDE tools tests scripts results runs continuation_v263_smoke` (on the Windows side, with `Tools/` ghost also cleared via `git rm -rf --cached Tools`).
4. Commit the retirement with a dedicated CHANGELOG entry citing this policy document.

Until Phase 2 is complete, **both locations hold live copies**. Edits should be made in `Codes/` / `Runs/`, not in the deprecated paths.

---

## 5. Enforcement

1. New code, new tests, and new scripts MUST be committed under `Codes/`.
2. New execution outputs MUST be written under `Runs/`.
3. New theory notes MUST be under `Docs/math/` with the `TECT-Math<NN>-*.tex.txt` naming rule.
4. Adding a new top-level folder under `Contents/` requires updating this policy document in the same commit.
5. Renaming any existing file or folder requires a CHANGELOG entry citing the reason, the old path, the new path, and the traceability chain (cause / evidence / decision).

## 6. Traceability chain (for this policy document)

- **Cause.** User request on 2026-04-23 to consolidate scattered code (PDE/, tools/, tests/, scripts/, Docs/supplementary/) under a single `Codes/` hierarchy and consolidate scattered results (results/, runs/, continuation_v263_smoke/) under a single `Runs/` hierarchy, and to adopt a strict case-convention rule.
- **Evidence.** 2026-04-23 inventory at repo root: 38 + 9 + 9 + 5 + 11 = 72 code files across 5 folders; ~20 result artifacts across 3 result folders; ~10 orphan / top-level stray files; one past case-collision incident (Task #101). Repository management observed to be difficult at this scale; mainline work is slowed by directory navigation overhead.
- **Decision.** (a) Create `Codes/` and `Runs/` as the canonical top-level namespaces for code and execution artifacts respectively. (b) Copy (not move) every tracked code file to the new location, preserving the deprecated paths to protect the in-flight Task #54 execution. (c) File this policy document and the accompanying `NAVIGATION.md` / per-folder `README.md`. (d) Schedule Phase-2 retirement of the deprecated paths for a dedicated commit after Task #54 closes. (e) Adopt the case-convention rules in §3.

---

## 6. Where new files go (binding from 2026-04-24, post-Turn-5)

This section is the **single most important rule** for autonomous research agents and any new contributor: **never create a file at the repository root** unless it is one of the four canonical root files (`CHANGELOG.md`, `CLAUDE.md`, `NAVIGATION.md`, `tect-research.plugin`). All other content has a designated home.

### 6.1 Mandatory destination table

| Content type | Canonical destination | Forbidden in root? |
|---|---|---|
| Math note (theorem / addendum / audit) | `Docs/math/TECT-Math<NN>-<descriptor>.tex.txt` | **YES** |
| Status note (scorecard / checklist) | `Docs/status/<name>.md` | **YES** |
| Policy / repo-discipline note | `Docs/policy/<name>.md` | **YES** |
| Code module — solver core | `Codes/pde/<module>.py` | **YES** |
| Code module — diagnostic / audit tool | `Codes/tools/<module>.py` | **YES** |
| Code module — Math-note-attached supplementary script | `Codes/supplementary/Math<NN>_<descriptor>.py` | **YES** |
| Run driver / sandbox-side helper | `Codes/scripts/<name>.{sh,ps1,bat,py}` | **YES** |
| Pytest test | `Codes/tests/test_<module>.py` | **YES** |
| Numerical seed file (`.npy`, `.npz`) | `Runs/seeds/<name>.npy` (and matching `<name>.npy.meta.json`) | **YES** |
| Run output directory | `Runs/{audit,continuation,logs}/<run_id>/` | **YES** |
| MANIFEST.md / per-run README | inside the run output directory | **YES** |
| Chat-archived session decisions | `Docs/math/TECT-Math<NN>-Session-<date>-decisions.tex.txt` | **YES** |
| Commit message (long) | inline argument to `Codes/scripts/sandbox_commit.sh` OR `/tmp/<id>.txt` (sandbox-only) | **YES** |
| Commit helper script | **never create new** — always use the canonical `Codes/scripts/sandbox_commit.sh` | **YES** |
| Plugin file | `<plugin-name>.plugin` at repo root (Cowork convention) | exception |

### 6.2 Forbidden-in-root patterns (auto-cleaned by `Codes/scripts/cleanup_root.ps1`)

The following file-name patterns indicate a violation of §6.1 and are removed by the cleanup utility:

```
commit_*.sh             commit_*.py             do_commit*.sh
run_commit*.sh          run_*_commit.sh         temp_commit_*.sh
temp_*_commit.sh        *_commit_msg.txt        COMMIT_MANIFEST_*.txt
.commit_message_temp.txt    .*_commit_trigger
Psi_BCC_*.npy           Psi_BCC_*.npy.meta.json    *.npy   *.npz
```

`*.npy` files are additionally excluded by `.gitignore`; the cleanup script *moves* them to `Runs/seeds/` before deletion so the data is preserved.

### 6.3 Why this matters

Repository-root pollution caused two concrete failures during the 2026-04-24 5-turn autonomous session:

1. **Stale lock cascade**: stray commit-helper scripts at root invoked `git commit` directly, leaving phantom `.git/index.lock` and `.git/HEAD.lock` files that blocked subsequent `git add` / `git commit` for the rest of the session (cf. `Codes/scripts/sandbox_commit.sh` header).
2. **Asset-copy contamination**: `--copy-assets` does not (and should not) copy from the repo root, so any code module mistakenly placed there is silently absent from `Website/assets/code/` and from the public download inventory in `Website/data/code.js`.

### 6.4 Defense-in-depth

Three layers enforce this discipline going forward:

1. **Pre-creation discipline** (CLAUDE.md §13): every Math note, code module, and script created by an autonomous agent must carry a comment header citing its canonical destination per §6.1.
2. **Post-creation cleanup** (`Codes/scripts/cleanup_root.ps1`): user-runnable PowerShell utility that detects and removes / relocates stray files matching §6.2 patterns. Dry-run by default; pass `-Apply` to execute.
3. **Pre-commit guard** (proposed `Codes/scripts/sandbox_commit.sh` extension): the commit helper should refuse to add files matching §6.2 patterns; instead it should print the canonical destination and abort. (Implementation queued; see UPDATE_POLICY §16 if added.)

### 6.5 Migration of existing strays (2026-04-24 cleanup)

The 2026-04-24 5-turn session left 19 stray files at root. They were:

- 11 stray commit-helper scripts (`commit_Turn4.sh`, `commit_math81.sh`, `commit_q6d.{sh,py}`, `direct_commit.sh`, `do_commit{,_math60c}.sh`, `run_commit.sh`, `run_q6d_commit.sh`, `temp_commit_math75_q2.sh`, `temp_q6d_commit.sh`)
- 4 orphan commit-message texts (`q6d_commit_msg.txt`, `COMMIT_MANIFEST_Math60C.txt`, `.commit_message_temp.txt`, `.q6d_commit_trigger`)
- 4 numerical seed files (`Psi_BCC_N32_phaseZ.npy{,.meta.json}`, `Psi_BCC_subset4_N32_phaseZ_E.npy{,.meta.json}`)

The seeds were relocated to `Runs/seeds/`. The commit helpers were superseded by `Codes/scripts/sandbox_commit.sh` (committed `6529bea`, 2026-04-24). All 15 stray scripts/messages are removed by `cleanup_root.ps1 -Apply`.
| Run driver / sandbox-side helper | `Codes/scripts/<name>.{sh,ps1,bat,py}` | **YES** |
| Pytest test | `Codes/tests/test_<module>.py` | **YES** |
| Numerical seed file (`.npy`, `.npz`) | `Runs/seeds/<name>.npy` (and matching `<name>.npy.meta.json`) | **YES** |
| Run output directory | `Runs/{audit,continuation,logs}/<run_id>/` | **YES** |
| MANIFEST.md / per-run README | inside the run output directory | **YES** |
| Chat-archived session decisions | `Docs/math/TECT-Math<NN>-Session-<date>-decisions.tex.txt` | **YES** |
| Commit message (long) | inline argument to `Codes/scripts/sandbox_commit.sh` OR `/tmp/<id>.txt` (sandbox-only) | **YES** |
| Commit helper script | **never create new** — always use the canonical `Codes/scripts/sandbox_commit.sh` | **YES** |
| Plugin file | `<plugin-name>.plugin` at repo root (Cowork convention) | exception |

### 6.2 Forbidden-in-root patterns (auto-cleaned by `Codes/scripts/cleanup_root.ps1`)

The following file-name patterns indicate a violation of §6.1 and are removed by the cleanup utility AND refused by the `sandbox_commit.sh` pre-commit guard (exit 8):

```
*commit*.sh             *commit*.py             *commit*.bat
direct_*.sh             do_commit*.sh           run_commit*.sh
run_*_commit.sh         temp_commit_*.sh        temp_*_commit.sh
*_commit_msg.txt        *_commit_*.txt          COMMIT_MANIFEST_*.txt
COMMIT_*.txt            .commit_message_temp.txt    .*_commit_trigger
.*_commit_msg
Psi_BCC_*.npy           Psi_BCC_*.npy.meta.json    *.npy   *.npz
*.tex.txt               (Math notes — must live in Docs/math/)
```

The `*commit*.{sh,py,bat}` glob is intentionally broad — it catches every plausible commit-helper variant. The canonical commit script `Codes/scripts/sandbox_commit.sh` is exempt because it lives under `Codes/scripts/`, not at root.

### 6.3 Why this matters

Repository-root pollution caused two concrete failures during the 2026-04-24 5-turn autonomous session:

1. **Stale lock cascade**: stray commit-helper scripts at root invoked `git commit` directly, leaving phantom `.git/index.lock` and `.git/HEAD.lock` files that blocked subsequent `git add` / `git commit` for the rest of the session (cf. `Codes/scripts/sandbox_commit.sh` header).
2. **Asset-copy contamination**: `--copy-assets` does not (and should not) copy from the repo root, so any code module mistakenly placed there is silently absent from `Website/assets/code/` and from the public download inventory in `Website/data/code.js`.

### 6.4 Defense-in-depth

Three layers enforce this discipline going forward:

1. **Pre-creation discipline** (CLAUDE.md §13): every Math note, code module, and script created by an autonomous agent must carry a comment header citing its canonical destination per §6.1.
2. **Post-creation cleanup** (`Codes/scripts/cleanup_root.ps1`): user-runnable PowerShell utility that detects and removes / relocates stray files matching §6.2 patterns. Dry-run by default; pass `-Apply` to execute.
3. **Pre-commit guard** (`Codes/scripts/sandbox_commit.sh`): refuses to add files matching §6.2 patterns; prints the canonical destination and aborts with exit 8.

### 6.5 Migration of existing strays

The 2026-04-24 5-turn session left ~20 stray files at root, removed by `cleanup_root.ps1 -Apply`:

- 12 stray commit-helper scripts: `commit_Turn4.sh`, `commit_math81.sh`, `commit_q6d.{sh,py}`, `direct_commit.sh`, `do_commit{,_math60c}.sh`, `run_commit.sh`, `run_q6d_commit.sh`, `temp_commit_math75_q2.sh`, `temp_q6d_commit.sh`
- 4 orphan commit-message texts: `q6d_commit_msg.txt`, `COMMIT_MANIFEST_Math60C.txt`, `.commit_message_temp.txt`, `.q6d_commit_trigger`
- 4 numerical seed files: `Psi_BCC_N32_phaseZ.npy{,.meta.json}`, `Psi_BCC_subset4_N32_phaseZ_E.npy{,.meta.json}`

The seeds were relocated to `Runs/seeds/`. The commit helpers were superseded by `Codes/scripts/sandbox_commit.sh` (committed `6529bea`, 2026-04-24).
