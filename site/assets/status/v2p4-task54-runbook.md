# v2.4 Task-#54 Operator Runbook — Math55 continuation @ $\mu^{2}_{\mathrm{target}}=5\times 10^{-3}$

**Created**: 2026-04-20
**Theory tag**: `Math56-Addendum-v2p4-2026-04-20`
**Parent task**: #54 (v2.4 Math55 continuation run @ $\mu^{2}_{\mathrm{target}}=5\mathrm{e}{-3}$)
**Scope of this runbook**: Sub-steps #54B and #54C, which require PyTorch + GPU and therefore cannot be executed inside the sandbox used for #54A. All commands below are to be run on the user's local workstation from the `TECT2/Contents` repository root.

---

## 0. Prerequisites

| Item | Required value |
|---|---|
| Python | 3.10+ |
| PyTorch | $\ge 2.0$ (CUDA build recommended; CPU fallback works but slow) |
| NumPy | 2.2.6 |
| Free disk (N=32) | ~200 MB |
| Free disk (N=64) | ~1.5 GB |
| Git branch | clean working tree, HEAD at the v2.4 patch commit |

Verify the v2.4 stamp chain BEFORE launching any solver run:

```bash
python3 -c "
from PDE.v24_thresholds import (BrazovskiiParams,
    brazovskii_critical_mu2, v24_separatrix_thresholds, v24_banner)
P = BrazovskiiParams(lam=-0.43, gam=1.62)
r_global, r_meta = brazovskii_critical_mu2(P)
sep = v24_separatrix_thresholds(5.0e-3, P)
print(v24_banner(5.0e-3, P))
assert r_meta > 5.0e-3,  f'mu2 target {5.0e-3} >= r_c^meta {r_meta}'
print('OK: mu2_target=5e-3 inside existence window.')
"
```

Expected output (last line): `OK: mu2_target=5e-3 inside existence window.`

Also run the gate-logic regression (numpy-only, takes <100 ms):

```bash
python3 -m unittest tests.test_v24_thresholds tests.test_v24_gate_integration -v
```

Expected: `OK` with 30 tests (22 thresholds + 8 gate integration).

---

## 1. Task #54B — Math55 continuation sweep, N=32

**Goal**: produce a non-trivial $\Psi^{*}$ at $\mu^{2}=5\times 10^{-3}$ on the N=32 grid, starting from a disordered vacuum at $\mu^{2}=-1$ and annealing up through the existence window.

**Invocation** (from `TECT2/Contents`):

```bash
python3 PDE/continuation_mu2.py \
    --config PDE/config_template_brazovskii.json \
    --N 32 --L 20pi \
    --mu2_start -1.0 \
    --mu2_end   5.0e-3 \
    --steps 41 \
    --outdir PDE/continuation_N32_v2p4 \
    --tol 1e-10 \
    --max-newton 50 \
    --krylov gmres \
    --gmres-restart 50 \
    --ew-eta-min 0.01 \
    --rng-seed 12345 \
    2>&1 | tee PDE/continuation_N32_v2p4.log
```

**What happens at startup**:

1. `v24_banner(5.0e-3, BrazovskiiParams(lam=-0.43, gam=1.62))` prints the critical scales and the target's position.
2. `_v24_precheck_mu2_end` asserts `5.0e-3 < r_c^meta = 0.01522` — if this ever fails, the run aborts *before* any solve.
3. A linearly-spaced schedule of 41 $\mu^{2}$ points from $-1.0$ to $5\times 10^{-3}$ is generated; consecutive solves warm-start from the previous $\Psi^{*}$.

**What the v2.4 gate does at each continuation point**:

- For $\mu^{2}\ge r_{c}^{\mathrm{meta}}$ (none in this schedule by construction): would skip silently.
- For $\mu^{2}<r_{c}^{\mathrm{meta}}$: after Phase 1 converges, the gate evaluates $V=\langle|\Psi|^{2}\rangle/\phi_{+}^{2}(\mu^{2})$ and the Class-II floor $\rho_{\star}=\kappa\phi_{+}^{2}$.
- A `RuntimeError("Class-II floor breach")` at any step indicates the continuation has fallen into the trivial vacuum — abort, diagnose, do **not** re-launch blindly.

**Success criteria at the terminal $\mu^{2}=5\times 10^{-3}$ step**:

| Quantity | Threshold |
|---|---|
| `phase0_gate_v24.passed` | `true` |
| `phase0_gate_v24.skipped` | `false` |
| `phase0_gate_v24.V` | $\ge G_{0}^{\mathrm{op}}=\alpha_{\mathrm{sep}}(\mu^{2})+\delta$ (= 0.7075 for this $\mu^{2}$) |
| `phase0_gate_v24.mean_sq` | $\ge \rho_{\star}=\kappa\phi_{+}^{2}=6.44\times 10^{-5}$ |
| `phase1.converged` | `true` |
| `||Psi_star||_RMS / phi_+` | $\ge 1.0$ (well inside basin) |

**Expected wall-time on a single NVIDIA H100**: ~20–40 min (N=32, 41 steps, GMRES + EW forcing).

**Outputs of interest**:

```
PDE/continuation_N32_v2p4/
├── Psi_star.npy                              # final condensate on the terminal grid
├── schedule.json                             # 41 (mu2, converged, gate_verdict) rows
├── proof_results_step{NN}.json               # per-step full proof pipeline output
├── continuation_summary.json                 # aggregated verdict
└── v2p4_gate_trace.json                      # per-step (V, G0_op, mean_sq, rho_star)
```

**If the run succeeds**: proceed to Task #54C below.

**If the run fails**:

| Symptom | Likely cause | Diagnostic step |
|---|---|---|
| `RuntimeError: Class-II floor breach` early in schedule | seed amplitude too small | inspect `proof_results_step00.json::Psi_seed_rms`; bump initial seed |
| Phase 1 diverges at $\mu^{2}\approx 0$ | trust-region too aggressive near transition | shrink `--max-newton` to 30 and re-run |
| `skipped=True` at terminal step | $\mu^{2}_{\mathrm{end}}$ drifted above $r_{c}^{\mathrm{meta}}$ by numerical error | tighten schedule: `--steps 81 --mu2_end 4.9e-3` |
| Long GMRES count (> 500 per Newton) near end | forcing term frozen at $\eta_{\min}$ | raise `--ew-eta-min 0.05` |

---

## 2. Task #54C — Phase-2.5 Hessian-jump audit on the converged $\Psi^{*}$

**Goal**: confirm that the Ritz eigenvector produced from the N=32 Phase-2 solve at the terminal $\mu^{2}$ is IR-localised (G1), grid-stable (G2, requires N=64 companion), and Saad-converged (G3), thereby certifying $m^{*2}(N=32) > 0$ at the v2.4 theorem-anchored gate level.

**Invocation**:

```bash
python3 PDE/hess_jump_audit.py \
    --psi-star   PDE/continuation_N32_v2p4/Psi_star.npy \
    --phase2-dir PDE/continuation_N32_v2p4/newton_rigorous_N32 \
    --backend    PDE/real_backend_pt_bcc_mixed_v3.py \
    --outdir     PDE/phase2p5_N32_v2p4 \
    2>&1 | tee PDE/phase2p5_N32_v2p4.log
```

**What the v1.1 audit enforces**:

- **G1 (IR localisation)**: Ritz vector $v^{*}$ must satisfy $\langle v^{*},\Pi_{\mathrm{UV}}v^{*}\rangle < 0.05$ on each grid.
- **G2 (Rayleigh-Ritz overlap across grids)**: $|\langle v^{*}_{N}, \mathcal{I}_{N\to 2N} v^{*}_{2N}\rangle| \ge G_{2,\min}=0.90$ (Math56-Addendum Theorem 4).
- **G3 (Saad residual, relative)**: $\|Hv^{*} - m^{*2}v^{*}\| \le 10^{-1}\cdot|m^{*2}|$ (Math56-Addendum Theorem 5).
- **[H-1] guard**: $m^{*2}>0$ (strict) is required for G3 to report PASS. A negative $m^{*2}$ with small residual still fails closed.

**Success criteria**:

```json
{
  "G1_pass": true,
  "G2_pass": true,         // requires N=64 companion — see §3
  "G3_pass": true,
  "m_star_squared_N32": <positive float, expected 0.1 - 0.5>,
  "lambda_ritz_sign": "positive",
  "class2_floor_pass": true
}
```

**Outputs**:

```
PDE/phase2p5_N32_v2p4/
├── phase2p5_gate_N32_v2p4.json
├── phase2p5_gate_summary.md
├── ritz_vector_N32.npy
└── spectra_vs_reference.pdf           # (if matplotlib available)
```

---

## 3. Scaling to N=64

If and only if #54B and #54C both pass on N=32, scale to N=64 with the same invocations:

```bash
# 54B at N=64 — warm-start from N=32 Psi_star upsampled:
python3 PDE/continuation_mu2.py \
    --config PDE/config_template_brazovskii.json \
    --N 64 --L 20pi \
    --mu2_start 5.0e-3 \
    --mu2_end   5.0e-3 \
    --steps 1 \
    --warm-start PDE/continuation_N32_v2p4/Psi_star.npy \
    --outdir PDE/continuation_N64_v2p4 \
    --tol 1e-10 --max-newton 50 --krylov gmres \
    --rng-seed 12345 \
    2>&1 | tee PDE/continuation_N64_v2p4.log

# 54C at N=64:
python3 PDE/hess_jump_audit.py \
    --psi-star   PDE/continuation_N64_v2p4/Psi_star.npy \
    --phase2-dir PDE/continuation_N64_v2p4/newton_rigorous_N64 \
    --companion  PDE/continuation_N32_v2p4/newton_rigorous_N32 \
    --backend    PDE/real_backend_pt_bcc_mixed_v3.py \
    --outdir     PDE/phase2p5_N32_N64_v2p4 \
    2>&1 | tee PDE/phase2p5_N32_N64_v2p4.log
```

**G2** at this stage requires the `--companion` flag pointing at the N=32 output directory so the cross-grid overlap can be computed.

**Expected wall-time N=64**: ~6–10 h on H100; budget accordingly.

---

## 4. Accept / reject decision tree (Math56-Addendum gate)

```
                       ┌─────────────────────────────────┐
                       │ #54B terminal  gate.passed?     │
                       └────────────┬────────────────────┘
                                    │
              ┌─────────── true ────┴────── false ──────────┐
              │                                             │
┌─────────────▼──────────────┐                 ┌────────────▼────────────┐
│ #54C  G1 & G3 pass (N=32)? │                 │ STOP. Diagnose with     │
└─────────────┬──────────────┘                 │ §1 failure-mode table.  │
              │                                 └─────────────────────────┘
      ┌───────┴────── true ──────┐
      │                          │
      ▼                          ▼
┌───────────────┐   ┌────────────────────────────────┐
│ Scale to N=64 │   │ G1/G3 fail: UV contamination   │
│ per §3 above. │   │ or Ritz residual too large;    │
└───────┬───────┘   │ re-run with tighter Lanczos tol│
        │           └────────────────────────────────┘
        ▼
┌──────────────────────────────────┐
│ #54C-N64  G1 & G2 & G3 all pass? │
└───────┬──────────────────────────┘
        │
  ┌─────┴── true ──────────┐
  ▼                        ▼
┌─────────────────────┐  ┌─────────────────────────────┐
│ Pillar 1 status     │  │ Report which gate failed;   │
│ SCAFFOLD → CLOSED-  │  │ do NOT promote Pillar 1.    │
│ AT-N64. Update      │  └─────────────────────────────┘
│ TOE-FACT-SHEET.     │
│ Queue Task #55 X6   │
│ (σ_V measurement)   │
│ and #56 X7 (κ).     │
└─────────────────────┘
```

Only after **both** N=32 and N=64 clear all three gates may the result enter the continuum-limit extrapolation stage (Phase 4 of `tect_newton_krylov.py`).

---

## 5. Post-run bookkeeping (irrespective of pass/fail)

Upon completion of #54B and #54C, regardless of verdict:

1. Append a dated row to `docs/status/research-log.md` summarising the measured quantities $(V, \alpha_{\mathrm{sep}}, m^{*2}, \rho_{\mathrm{UV}})$.
2. Append a dated row to `docs/status/TECT-Theory-Code-Sync.md` §5 (Sync Manifest) with the run tag and the verdict.
3. Update `docs/status/TOE-FACT-SHEET.md` Pillar 1 row (SCAFFOLD → CLOSED-AT-N* / retained SCAFFOLD, as appropriate).
4. Append a `[Results]` sub-section to the `[Math56-Addendum-v2p4-2026-04-20]` CHANGELOG block.
5. **Only after** the ledger updates land, fire the deferred website batch listed in that CHANGELOG block (§Infrastructure).

---

## 6. What this runbook explicitly does NOT do

- It does **not** execute inside the sandboxed research session (no PyTorch available there).
- It does **not** modify any theory document; any theoretical issue uncovered at runtime must be raised as a new `Q-2026-04-20-*` entry in `OPEN-QUESTIONS.md` and routed through the Math-note pipeline.
- It does **not** perform the continuum extrapolation (Phase 4); that is a downstream task, gated on both N=32 and N=64 passing #54C.

---

## 7. Quick-reference numerics (locked for $\lambda=-0.43,\ \gamma=1.62,\ \mu^{2}=5\times 10^{-3}$)

| Symbol | Expression | Value |
|---|---|---|
| $r_{c}^{\mathrm{global}}$ | $\lambda^{2}/(10\gamma)$ | $1.141\times 10^{-2}$ |
| $r_{c}^{\mathrm{meta}}$ | $2\lambda^{2}/(15\gamma)$ | $1.522\times 10^{-2}$ |
| $\phi_{+}^{2}$ | $(-2\lambda+\sqrt{4\lambda^{2}-30\gamma\mu^{2}})/(15\gamma)$ | $6.44\times 10^{-2}$ |
| $\phi_{-}^{2}$ | $(-2\lambda-\sqrt{4\lambda^{2}-30\gamma\mu^{2}})/(15\gamma)$ | $6.38\times 10^{-3}$ |
| $\phi_{+}$ |  | $0.2538$ |
| $\phi_{-}$ |  | $0.0799$ |
| $\alpha_{\mathrm{sep}}$ | $(\phi_{-}/\phi_{+})^{2}$ | $0.0993$ |
| $G_{0}^{\mathrm{raw}}$ | $\tfrac12(1+\phi_{-}/\phi_{+})$ | $0.6575$ |
| $\delta$ | `V24_G0_CUSHION` | $0.0500$ |
| $G_{0}^{\mathrm{op}}$ | $G_{0}^{\mathrm{raw}}+\delta$ | $0.7075$ |
| $\kappa$ | `V24_RHO_STAR_FACTOR` | $1.0\times 10^{-3}$ |
| $\rho_{\star}$ | $\kappa\,\phi_{+}^{2}$ | $6.44\times 10^{-5}$ |
| $G_{2,\min}$ | Theorem 4 | $0.90$ |
| $G_{3,\mathrm{rel}}$ | Theorem 5 | $0.10$ |

These are the constants the solver, the continuation driver, and the Phase-2.5 audit will all key off. **Do not hand-override any of them** — if one looks wrong, re-run `Docs/supplementary/v24_threshold_sympy_check.py` and file the discrepancy as an `OPEN-QUESTIONS.md` entry.

---

**End of runbook.**
