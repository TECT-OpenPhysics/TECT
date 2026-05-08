# TECT Repository Navigation

**Last updated**: 2026-04-24 (Phase 2 A+B+C+D+E+F cleanup landed; CLAUDE.md added at root; PDE/ fully retired; only canonical paths remain)

This file is a one-screen human map of `Contents/`. The normative rules are in `Docs/policy/REPO_LAYOUT.md`.

## Quick map (post 2026-04-24 Phase A+B+C cleanup)

```
Contents/
├── CLAUDE.md                       # ★ master AI-collaborator entry document (NEW 2026-04-24)
├── CHANGELOG.md
├── NAVIGATION.md                   # this file
├── Codes/                          # ALL code (canonical from 2026-04-23)
│   ├── pde/                        # solver / backend / continuation driver
│   ├── tools/                      # diagnostic + audit scripts
│   ├── tests/                      # pytest suite
│   ├── scripts/                    # PowerShell / Bash orchestration
│   └── supplementary/              # theory-note verification scripts
├── Runs/                           # ALL execution artifacts (canonical from 2026-04-23)
│   ├── audit/                      # JSON audit snapshots
│   ├── continuation/               # endpoint JSONs + active Task #54 output path
│   ├── legacy/                     # historical runs
│   └── logs/                       # long-running log files
├── Docs/                           # theory notes, manuals, policy, runbooks, status
│   ├── manual/                     # CODE_MANUAL.md + manual-entries-archive/ (NEW)
│   ├── math/                       # TECT-Math<NN>-*.tex.txt + paste-ready-archive/ (NEW)
│   ├── papers/  policy/  runbooks/  archive/  supplementary/
│   └── status/                     # ledgers + round-summaries/ (NEW)
├── Website/                        # static-site deliverable
├── Backup/                         # pre-restructure snapshots (read-only)
│   └── pre-restructure-2026-04-23/
├── tect-research.plugin            # Cowork plugin bundle (root per Cowork convention)
│
```

(All deprecated-but-live paths retired in the 2026-04-24 Phase A+B+C+D+E+F cleanup. See bottom of this file.)

**Runs/ sub-tree after Phase E+F**:

```
Runs/
├── audit/             # JSON audit snapshots (11 files from Phase D)
├── continuation/      # endpoint JSONs + active task output paths
├── historical/        # 32 subtrees from PDE/<historical-data-dir> (Phase E)
├── legacy/            # historical runs + Phase_1_grid64_emergence_result.txt
└── logs/              # long-running log files
```

**Retired in 2026-04-24 Phase A+B+C+D+E+F cleanup** (no longer in tree):
`tools/`, `tests/`, `runs/`, `scripts/`, `continuation_v263_smoke/`, `results/`, **`PDE/`**,
plus 18 root-level orphan files relocated to
`Docs/status/round-summaries/`, `Docs/math/paste-ready-archive/`,
`Docs/manual/manual-entries-archive/`. The 11 tracked files from `results/`
are now in `Runs/audit/`. PDE/ is fully retired: 38 .py + 4 .json mirrors
preserved in `Codes/pde/`; 32 historical-data subtrees moved to
`Runs/historical/`; policy docs moved to `Docs/policy/`; .bat moved to
`Codes/scripts/`; PDE/deprecated/ preserved in
`Backup/pre-PDE-retirement-2026-04-24/PDE_deprecated/`. See
`Docs/math/TECT-Math82-Repo-Cleanup-Phase2.tex.txt` (Phases A+B+C),
`Docs/math/TECT-Math82-Addendum-A-Phase-D-results-propagation.tex.txt`
(Phase D), and
`Docs/math/TECT-Math82-Addendum-C-Phase-E-F-PDE-retirement.tex.txt`
(Phases E+F) for the cleanup plan and audit trail.

## Where do I find / put X?

| I want to... | Path |
|---|---|
| Read / edit the continuation driver | `Codes/pde/continuation_mu2_v25.py` |
| Read / edit the Newton-Krylov solver core | `Codes/pde/tect_newton_krylov.py` |
| Run a PowerShell diagnostic | `Codes/scripts/run_v25_diagnostic.ps1` |
| Add a new pytest | `Codes/tests/test_<feature>.py` |
| Add a Math-note verification script | `Codes/supplementary/verify_<note>.py` |
| Read a theory note (TECT-MathNN-*) | `Docs/math/TECT-Math<NN>-*.tex.txt` |
| Read the code manual | `Docs/manual/CODE_MANUAL.md` |
| Read the layout policy | `Docs/policy/REPO_LAYOUT.md` |
| Read the GPU runbook | `Docs/runbooks/v263_execution_verification_runbook.md` |
| Read the master changelog | `CHANGELOG.md` |
| Read a recent endpoint JSON | `Runs/continuation/*/continuation_mu2_v25_endpoint.json` |
| Read an audit JSON | `Runs/audit/*.json` |
| Read a pre-restructure source snapshot | `Backup/pre-restructure-2026-04-23/code/...` |

## Executing Task #54 (the canonical single-shot CLI, post Phase Z)

**Updated 2026-04-24 (Phase Z runbook + Phase E+F PDE retirement)** — the
canonical CLI now uses `Codes\pde\` paths and includes the BCC analytic
seed (driver v2.6.5, `--load-psi` flag) and reversed schedule per
Math82-Addendum-B Phase Z.

```powershell
cd C:\Dev\TECT2\Contents

# Step 1: generate BCC analytic seed (one-time, per N)
python -u Codes\pde\bcc_analytic_seed.py `
    --N 32 --L 62.20036 --mu2 -1.0 --gamma 1.62 `
    --output Psi_BCC_N32_phaseZ.npy

# Step 2: run continuation with reversed schedule + BCC seed
python -u Codes\pde\continuation_mu2_v25.py `
    --config       Codes\pde\config_template_brazovskii.json `
    --N            32 `
    --L            62.20036 `
    --mu2          5e-3 -0.02 -0.1 -0.5 -1.0 `
    --tol-newton   1e-8 `
    --max-newton   12 `
    --ew-eta-min   0.05 `
    --ew-eta-max   0.9 `
    --tcg-max      3000 `
    --rho-min      0.05 `
    --load-psi     Psi_BCC_N32_phaseZ.npy `
    --output       Runs\continuation\math55_endpoint_N32_Lbcc7_phaseZ_2026-04-24
```

The `--mu2` schedule is now reversed (start at the easy meta-stable side
$\mu^2 = +5\!\times\!10^{-3}$, walk down to the deep $\mu^2 = -1.0$
endpoint with warm-start at each step). The BCC analytic seed
(12 first-shell peaks, $A_{\mathrm{BCC}} \approx 0.20$) replaces the
default thermal seed and drops the initial residual by several orders
of magnitude. See
`Docs/math/TECT-Math82-Addendum-B-Phase-Z-BCC-analytic-seed-runbook.tex.txt`
for the mathematical content and pre-registered success criteria.

The superseded $L = 16$ run from 2026-04-23 retains value only as a
software / integration smoke test (Math74 Addendum-C §5); it is not
physics-grade evidence for the endpoint observables $m_*^2$, $\Delta F$,
$F_{\mathrm{condensate}}$, $F_{\mathrm{vacuum}}$.

After PDE/ retirement (Phase E+F, 2026-04-24), `PDE\` paths are no
longer valid. All Task #54 work uses `Codes\pde\` exclusively.

## Case convention (short form)

- Top-level folders under `Contents/`: **PascalCase** (`Codes`, `Docs`, `Runs`, `Website`, `Backup`).
- Subfolders inside those namespaces: **lowercase** (`pde`, `tools`, `tests`, `scripts`, `math`, `policy`, ...).
- Python modules: snake_case.py; Math notes: `TECT-Math<NN>-*.tex.txt`; status ledgers: `UPPER-CASE-WITH-HYPHENS.md`.
- Past case-collision on `Tools` vs `tools` (Task #101) remains a git-index ghost; it will be cleared in the Phase-2 retirement commit. See `Docs/policy/REPO_LAYOUT.md` §3.
