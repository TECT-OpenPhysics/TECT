# Math236 Continuum-Limit Scan — RESULT

- Theory tag : Math236-Task115-Continuum-Limit-Scan
- Driver     : Codes/supplementary/Math236_continuum_limit_scan.py
- Timestamp  : 20260430_170121Z
- Config     : `C:\Dev\TECT2\Contents\Codes\pde\config_template_brazovskii.json`
- mu^2       : -0.7
- L (box)    : 16.0
- N list     : [16]
- Output dir : `C:\Dev\TECT2\Contents\Runs\continuation\math236_20260430_170121Z`
- Elapsed    : 5.6 s
- **Overall  : ERROR**

## Stage 1 + 2 — Per-N solve and amplitude

| N | a = L/N | solver exit | wall-time (s) | f(a) | extraction |
|---|---|---|---|---|---|
| 16 | 1.0000 | 1 | 5.5 | — | SOLVER_FAIL_EXIT_1 |

## Stage 3 — Richardson fit  f(a) = f_inf + A_1·a + A_2·a^2

- fit_status: SKIPPED
- notes    : --skip-stage <= 3

## Stage 4 — Falsification gates (Math235 §3 + Math236 §3)

| Gate | Pass | Detail |
|---|---|---|

## Operator notes

- `run_diagnostics.json` in the output dir holds the structured payload.
- Per-N output subdirs hold the solver's own `proof_results.json` etc.
- For T6 promotion of Pillar 6 sub-task β (Math234 OPEN GAP β),
  G1+G2+G3+G5+G6 must all PASS and f_inf must reproduce the SM
  electroweak scale within 30 percent (Math234 §3 closure criterion).
