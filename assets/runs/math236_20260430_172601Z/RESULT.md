# Math236 Continuum-Limit Scan — RESULT

- Theory tag : Math236-Task115-Continuum-Limit-Scan
- Driver     : Codes/supplementary/Math236_continuum_limit_scan.py
- Timestamp  : 20260430_172601Z
- Config     : `C:\Dev\TECT2\Contents\Codes\pde\config_template_brazovskii.json`
- mu^2       : -0.7
- L (box)    : 16.0
- N list     : [16, 32, 64, 128]
- Output dir : `C:\Dev\TECT2\Contents\Runs\continuation\math236_20260430_172601Z`
- Elapsed    : 39394.1 s
- **Overall  : PARTIAL**

## Stage 1 + 2 — Per-N solve and amplitude

| N | a = L/N | solver exit | wall-time (s) | f(a) | extraction |
|---|---|---|---|---|---|
| 16 | 1.0000 | 0 | 39394.1 | 0.000000e+00 | OK |

## Stage 3 — Richardson fit  f(a) = f_inf + A_1·a + A_2·a^2

- fit_status: INSUFFICIENT_POINTS
- notes    : have 0 usable points, need >= 3

## Stage 4 — Falsification gates (Math235 §3 + Math236 §3)

| Gate | Pass | Detail |
|---|---|---|
| G1_min_points | ✗ | n_points=0, threshold>=3 |
| G2_residual_max_rel | ✗ | no fit available |
| G3_sign_consistency | ✗ | all f(a_k) > 0 = False |
| G4_power_law_window_rel | ✗ | insufficient points |
| G5_f_inf_lower | ✗ | no fit |
| G6_f_inf_upper | ✗ | no fit |

## Operator notes

- `run_diagnostics.json` in the output dir holds the structured payload.
- Per-N output subdirs hold the solver's own `proof_results.json` etc.
- For T6 promotion of Pillar 6 sub-task β (Math234 OPEN GAP β),
  G1+G2+G3+G5+G6 must all PASS and f_inf must reproduce the SM
  electroweak scale within 30 percent (Math234 §3 closure criterion).
