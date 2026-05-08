# Per-run RESULT.md template

Every `PDE/run_*/` directory MUST contain a `RESULT.md` filled from this template
before being considered complete. Website's `results.html` is (or will be)
generated from the aggregate of these files.

---

## Run identification

- **result_tag**: `R-<YYYY-MM-DD>-<seq>-<theory_tag>`
- **theory_tag**: `Math38-Brazovskii-2026-04-15`
- **regime**: `Brazovskii` | `Ginzburg-Landau`
- **git_sha**: `<40-char SHA or null if pre-git>`
- **run_label**: `<short human label>`
- **operator**: `<name>`
- **started_utc**: `<ISO 8601>`
- **ended_utc**: `<ISO 8601>`
- **node / GPU**: `<e.g. RTX 4090 / A100 / CPU-only>`

## Config snapshot

- `config_template`: `PDE/config_template_brazovskii.json` (or as applicable)
- Parameter override: $(\mu^{2},\lambda,\gamma) = (\,\_\_,\,\_\_,\,\_\_\,)$
- Grid: $N = \_\_^{3}$, $L = \_\_$, $h = \_\_$
- Step schedule: `IMEX dt=__ , n_steps=__`

## Key observables

| Quantity | Value | Expected | Pass/Fail |
|---|---|---|---|
| $m^{*2}_{\mathrm{num}}$ | | | |
| $R_{\mathrm{patch}} \cdot M_{2}/W_{0}$ | | $9.0\pm\delta$ | |
| $\phi_{0}^{2}$ | | $\approx 0.07078$ | |
| $\lambda_{\parallel}$ | | $\approx 0.0717$ | |
| residual (final) | | $\le 10^{-6}$ | |
| Dirac index (sum) | | $0$ (Nielsen–Ninomiya) | |

## Acceptance

- Band: $m^{*2}_{\mathrm{num,corr}} \in [1.8,\,45.0]$.
- Result: **ACCEPT** / **REJECT** / **INCONCLUSIVE**.
- If REJECT: auto-rollback path: `PDE/backup_GL_2026-04-15/configs/`.

## Artefacts produced

- `tect_version_manifest.json` — dual fingerprint (theory + code).
- `live_m_parallel_summary.json` — per-patch, per-pair, shell-mean $m_{\parallel}$.
- `<solver output .npy / .h5>`
- `<extractor observable block .json>`

## Open tickets opened by this run

- D1 / D4 / … — list any new discrepancies, with one-line description.

## One-sentence conclusion

> *e.g. "Step C converged under the Brazovskii config; $m^{*2}_{\mathrm{num,corr}} = 8.87$ inside the acceptance band, closing Math38 numerically."*
