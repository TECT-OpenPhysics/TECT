# v2.4 Newton-Krylov Patch Plan (concrete diffs, theorem-anchored thresholds)

**Date:** 2026-04-20
**Status:** PLAN (blocked on X5 — $\phi_0$-convention audit of Math37-AddA §A.3)
**Theoretical foundation:** `Docs/math/TECT-Math56-Addendum.tex.txt`
**Supersedes:** heuristic v2.4 draft (2026-04-20 early), where thresholds were guessed.

---

## 0. Why this plan (reading guide)

The early v2.4 draft (G0=0.3, ρ_cut=10⁻³, G2=0.8, G3=10⁻³) was written *before*
the Math56 Hessian-jump audit was theoretically hardened. Two things were
wrong:

1. **μ²_target was never chosen.** The draft implicitly kept the locked
   μ²=0.26. Theorem 1 of Math56-Addendum proves there is **no BCC extremum**
   at μ²=0.26 — it lies 17× above the metastability window r_c^meta =
   2λ²/(15γ) = 0.01522. Any continuation terminating there converges to the
   trivial vacuum *correctly*. The patch must fix μ²_target < r_c^global =
   0.01141 (recommended: 5×10⁻³).

2. **Thresholds were heuristics, not theorems.** Math56-Addendum now derives:
   - G0 from the Brazovskii separatrix α_sep = φ₋/φ₊ (§B): **G0 = 0.657 + 0.05**
   - ρ_* from solver-tolerance consistency (§C): **ρ_* = 6.2×10⁻⁵**
     (abort-floor, not additive regulariser — important semantic shift)
   - G2 from Rayleigh–Ritz perturbation (§D): **G2_min = 0.90** (not 0.8)
   - G3 from the Saad bound (§E): **G3_max = 10⁻¹ · m²_Ritz** (relative, not
     absolute)

This plan gives the concrete diffs to `PDE/*.py` and `tools/*.py` that apply
these theorem-level values. The patch does **not** execute until open item X5
is resolved.

---

## 1. Work order (cost-optimised, gate-aligned)

Each step is gated by the previous step. No code is committed until all theory
prerequisites are closed.

| Step | Class | Depends on | Deliverable | Est. cost |
|------|-------|------------|-------------|-----------|
| **A** | Theory | — | Math56-Addendum (§A–F) | ✅ DONE 2026-04-20 |
| **B** | Theory | A | Resolve **X5** (φ₀ convention audit Math37-AddA §A.3) | 1 turn |
| **C** | Decision | B | User picks μ²_target ∈ {0.003, 0.005, 0.008} | user-input |
| **D** | Code | A, B, C | v2.4 patch: see §3 below | 1 turn |
| **E** | Code | D | `hess_jump_audit.py` v1.1 (updated thresholds) | 0.5 turn |
| **F** | Execute | D, E | Math55 continuation μ²: −1 → μ²_target at N=32 | user-run |
| **G** | Execute | F | Phase-2.5 audit on continuation output | user-run |
| **H** | Execute | G | Phase-2 Newton-Krylov at μ²_target, N=32 | user-run |
| **I** | Execute | H | Cross-grid lift N=32 → N=64 + G2 check | user-run |
| **J** | Theory | I | If G2 passes, report m*² with uncertainty | 1 turn |

**Total engineering cost before any compute is spent:** 2–3 turns.
**User decisions required:** (i) X5 resolution, (ii) μ²_target selection.
**Abort condition:** if X5 cannot be cleanly resolved (both boxed and
re-derived φ₀ are wrong), stop and escalate to full Math37-AddA §A audit.

---

## 2. Prerequisite resolutions

### 2.1 X5 — φ₀ convention

Two candidate values:

- **Math37-AddA §A.3 (boxed):** $\phi_0^2 = -4\lambda/(15\gamma) = 0.0708$,
  $\phi_0 = 0.2660$.
- **Math56-Addendum §F re-derivation:** $\phi_0^2 = -\lambda/(5\gamma) = 0.0531$,
  $\phi_0 = 0.2305$.

Ratio 0.266/0.2305 = 1.154 (factor 4/3 in $\phi_0^2$). Math56-Addendum §F
provides the explicit two-equation derivation that gives 0.2305. The boxed
formula in Math37-AddA §A.3 appears to contain an algebraic slip (see
§F; deriving from either condition alone gives a different answer than the
simultaneous system). **Until audited, the code patch parametrises φ₀ via
the re-derivation and logs both candidates at startup for review.**

### 2.2 μ²_target selection

| Option | Value | $\phi_+$ | $\phi_-$ | $\alpha_{sep}$ | $G_0^{op}$ | F-margin | Notes |
|--------|------:|--------:|--------:|-------------:|-----------:|----------|-------|
| A (deep) | 3×10⁻³ | 0.2590 | 0.0607 | 0.2342 | 0.667 | largest | safest but hardest continuation |
| **B (recommended)** | **5×10⁻³** | **0.2538** | **0.0799** | **0.3150** | **0.708** | moderate | optimal trade |
| C (shallow) | 8×10⁻³ | 0.2445 | 0.1050 | 0.4294 | 0.765 | small (F-margin ~20% of deep) | risky — near first-order |

Recommended: **Option B** (SymPy-verified 2026-04-20). Default in the patch; user can override.

---

## 3. Concrete code diffs (v2.4 patch)

### 3.1 `PDE/tect_solver_pt_v3.py` — module-level constants block

```python
# === v2.4 thresholds (theorem-anchored; see Docs/math/TECT-Math56-Addendum.tex.txt) ===
V24_MU2_TARGET       = 5.0e-3     # Corollary 1; user-overridable
V24_PHI0_DERIVED     = None       # computed from (lam, gam, mu2_target) at runtime
V24_G0_BASE          = 0.658      # Theorem 2 at mu2_target=5e-3 (SymPy-verified)
V24_G0_CUSHION       = 0.050      # finite-N RMS cushion
V24_RHO_STAR         = 6.4e-5     # Theorem 3 abort floor (NOT additive regulariser)
V24_G2_MIN           = 0.90       # Theorem 4 (was 0.80, bumped)
V24_G3_REL           = 1.0e-1     # Theorem 5: ||r|| <= V24_G3_REL * lam_Ritz  (RELATIVE)
V24_NEWTON_TOL       = 1.0e-9     # used in rho_* sanity check
# ==========================================================================================
```

### 3.2 New helper function (module level)

```python
def v24_separatrix_thresholds(lam: float, gam: float, mu2_target: float):
    """Return (phi_plus, phi_minus, alpha_sep, G0) from Math56-Addendum Thm 2."""
    import math
    R = 4.0 * lam * lam - 30.0 * gam * mu2_target
    if R < 0:
        raise ValueError(
            f"v2.4 precondition failed: mu2_target={mu2_target:.4e} lies above "
            f"metastability r_c^meta = 2*lam^2/(15*gam) = {2*lam*lam/(15*gam):.4e}. "
            f"No BCC extremum exists — refuse to start continuation."
        )
    sqrtR = math.sqrt(R)
    x_plus  = (-2.0 * lam + sqrtR) / (15.0 * gam)
    x_minus = (-2.0 * lam - sqrtR) / (15.0 * gam)
    phi_plus, phi_minus = math.sqrt(x_plus), math.sqrt(x_minus)
    alpha_sep = phi_minus / phi_plus
    G0 = 0.5 * (1.0 + alpha_sep) + V24_G0_CUSHION
    return phi_plus, phi_minus, alpha_sep, G0
```

### 3.3 Phase-0 gate hook (call before Phase-2 Newton-Krylov)

```python
def v24_phase0_gate(Psi: torch.Tensor, phi_plus: float, G0: float) -> bool:
    """Return True if Psi has escaped the vacuum basin past the separatrix."""
    rms = torch.sqrt((Psi.abs() ** 2).mean()).item()
    V = rms / phi_plus
    logger.info(f"[Phase-0] V = ||Psi||_RMS / phi_+ = {V:.4f}  threshold={G0:.4f}")
    return V >= G0
```

### 3.4 Class-II abort hook (inside Newton step)

```python
def v24_class2_guard(rho: torch.Tensor) -> None:
    """Abort Newton step if rho falls below theorem-anchored floor."""
    rho_min = rho.min().item()
    if rho_min < V24_RHO_STAR:
        raise RuntimeError(
            f"[Class-II abort] min(rho) = {rho_min:.4e} < rho_* = {V24_RHO_STAR:.4e}. "
            f"Solver is drifting into the regularised-quotient singularity. "
            f"Increase continuation steps or revise mu2_target."
        )
```

### 3.5 Phase-2.5 gate (call after Ritz solve)

```python
def v24_phase25_gate(
    v_N: torch.Tensor,           # Ritz eigenvector at grid N
    v_2N: torch.Tensor,          # Ritz eigenvector at grid 2N (zero-pad lifted)
    lam_Ritz: float,             # Ritz eigenvalue at N
    residual_norm: float         # ||H v - lam v||_2 at N
) -> dict:
    """Enforce G1 (Fourier localisation; in hess_jump_audit),
       G2 (cross-grid overlap), G3 (Saad residual).  Return pass/fail report."""
    # G2
    overlap = abs((v_N.conj() * v_2N).sum().item())
    g2_ok = overlap >= V24_G2_MIN
    # G3 (relative)
    g3_threshold = V24_G3_REL * abs(lam_Ritz)
    g3_ok = residual_norm <= g3_threshold
    return {
        "G2_overlap": overlap, "G2_min": V24_G2_MIN, "G2_pass": g2_ok,
        "G3_residual": residual_norm, "G3_max": g3_threshold, "G3_pass": g3_ok,
        "overall_pass": g2_ok and g3_ok,
    }
```

### 3.6 `PDE/hess_jump_audit.py` v1.1 updates

- Change default `G2_MIN` from 0.80 → 0.90 (line 34 area).
- Change `G3_MAX` from absolute 1e-3 → relative (pass `lam_Ritz`).
- Add `--mu2_target` CLI flag; recompute G0 from `v24_separatrix_thresholds`.
- Banner: print the current thresholds *with* their theorem references.

### 3.7 `tools/continuation_mu2.py` (Math55)

- Add guard: if `mu2_target > r_c^global = lam**2/(10*gam)`, warn that the
  terminal state will be metastable (still BCC-stable, but higher free energy
  than Ψ=0).
- Add guard: if `mu2_target > r_c^meta`, refuse to start.
- Arclength/predictor step size capped at
  `Δμ² ≤ 0.1 · (r_c^global − μ²_current)` near the transition (X1).
- After every step, call `v24_class2_guard` and `v24_phase0_gate`; if either
  fails, halve step size and retry (up to 5 times) before abort.

### 3.8 `Docs/manual/CODE_MANUAL.md`

- Add revision-history line for `tect_solver_pt_v3.py v2.4`.
- Expand `hess_jump_audit.py` entry to note v1.1 threshold changes.
- Revision for `continuation_mu2.py` guards.

---

## 4. Verification plan (post-patch)

1. **Unit test** (pure-Python, no torch):
   `tests/test_v24_thresholds.py` — check `v24_separatrix_thresholds(-0.43, 1.62, 0.005)`
   returns `(0.2482, 0.0781, 0.3146, 0.707)` within 1e-4.
2. **Smoke test**: call `v24_separatrix_thresholds(-0.43, 1.62, 0.26)` and
   confirm it raises `ValueError`.
3. **Integration**: run `continuation_mu2.py --mu2_target 5e-3 --N 32`,
   verify terminal state has `V ≥ G0` and `min(rho) ≥ ρ_*`.
4. **Audit**: run `hess_jump_audit.py` on the saved state; verify G1–G3 pass.
5. **Phase-2 rerun**: Newton-Krylov at μ²=5e-3, N=32 → report m*².
6. **Continuum audit**: lift to N=64 with zero-pad interpolator, rerun
   Phase-2, confirm G2 ≥ 0.9.

---

## 5. What this plan does *not* promise

- Does **not** guarantee that a BCC minimum physically exists at
  μ²_target = 5×10⁻³ — that is a prediction of the mean-field reduced
  potential, not of the full projected Hessian. It guarantees that *if* one
  exists, the solver will not mistake it for trivial vacuum.
- Does **not** guarantee X3 (sextic-mode correction ~1.6 at μ²=5×10⁻³).
  Quantitative m*² to better than 10% accuracy still requires the
  three-mode BCC ansatz; open in Math56-Addendum §F-X3.
- Does **not** resolve X5 — patch only *parametrises* over the
  φ₀-convention ambiguity; user must audit Math37-AddA §A.3 before the
  physical number is accepted.

---

## 6. Rollback plan

If steps F–I reveal the solver still collapses:

- First halve step size (arclength) in `continuation_mu2.py`.
- If that fails, try μ²_target = 3×10⁻³ (Option A, deeper into the stable
  phase).
- If that fails, this is evidence that the uniform-amplitude reduced
  potential is not a quantitatively good guide to the three-mode BCC
  minimum — escalate to Math57 (three-mode amplitude equations) as a new
  theoretical prerequisite.

---

## 7. Sign-off

- Theory derivations: see `Docs/math/TECT-Math56-Addendum.tex.txt` §A–§G.
- Threshold source-of-truth: §G summary table.
- Blocking prerequisite: X5 (Math37-AddA §A.3 audit).
- Ready for code once X5 closes and μ²_target is selected.
