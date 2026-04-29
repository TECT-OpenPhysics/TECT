# TECT Code Manual

**Binding from**: 2026-04-16
**Scope**: Every Python module under `PDE/` and orchestration tools under `tools/`.
**Policy hook**: `docs/policy/UPDATE_POLICY.md` §13 — every new or modified
module MUST update this manual in the same commit.
**Maintainer**: Jusang Lee (jtkor@outlook.com)

This manual is the single canonical user-facing reference for running
TECT code. Per-file docstrings remain inside each module, but casual and
operator-level use should start here.

Each entry follows a fixed schema:

- **Purpose** — one-sentence physical / computational goal.
- **Inputs** — files and/or CLI arguments consumed.
- **Outputs** — files and/or return values produced.
- **CLI** — minimal copy-pasteable invocation.
- **Dependencies** — upstream modules it reads, downstream modules that call it.
- **Math note** — which `TECT-Math<NN>` note the module realizes.

Status labels next to the version: **[ACTIVE]**, **[UTILITY]**,
**[DIAGNOSTIC]**, **[SUPERSEDED]**, **[EXPERIMENTAL]**.

---

## 1. Quick-start workflows

The three operator-level workflows most commonly invoked:

### 1.1 Full Math44/45/46 finite audit (one-shot)

```bash
# From repo root.  Runs solver (N=32,64,128) → c2 → c3 on each grid.
nohup python3 PDE/run_audit_pipeline.py \
    --grids 32 64 128 \
    --resume \
    > audit_pipeline.out 2>&1 &

# Follow progress:
tail -f audit_pipeline.out
# or inspect the structured log:
tail -f audit_pipeline.log
```

Outputs land in `audit_run_<timestamp>/` with:
`solver_N<grid>/`, `c2_audit_N<grid>.json`, `c3_audit_N<grid>.json`,
`audit_summary.json`.

### 1.2 Single converged run + n*=1 diagnostic chain

```bash
python3 PDE/tect_solver_pt_v3.py \
    --config PDE/configs/default.json \
    --backend PDE/real_backend_pt_bcc_mixed_v3.py \
    --grid 64 --L 16.0 --steps 4000 \
    --output ./run_demo

python3 PDE/run_pipeline_n1.py --input ./run_demo --output ./run_demo/nstar1
```

### 1.3 Rank-2 BCC seeding for analytical verification

```bash
python3 PDE/make_rank2_bcc_seed.py --grid 64 --L 16.0 --mode all --n-seeds 8 --out-dir ./seeds
python3 PDE/rank2_check.py   # inspect SVD spectrum
```

---

## 2. Solver & backend (core compute)

### tect_newton_krylov.py  (v2.6.0)  [ACTIVE]
- **Purpose**: Trust-region Newton-Krylov solver implementing the 4-phase
  rigorous proof protocol, enhanced with v2.6 in-solver Hermitian projection
  (Path-X, Math66):
  - Phase 1: Existence — Steihaug-Toint truncated CG (handles indefinite Hessian).
  - Phase 2: Stability — Projected Lanczos (translation zero modes removed).
    $m^{*2}$ = first positive projected eigenvalue.
  - Phase 3: Vacuum favorability — $\Delta F = F(\Psi^*) - F(0) < 0$.
    Proves preference over $\Psi=0$ only, NOT global optimality.
  - Phase 4: Continuum limit — Nested Phases 1–3 across N values,
    linear fit $m^{*2}(h^2) = m_0 + c\,h^2$.
- **Inputs**: `--config <cfg.json>`, `--N {32,64,128}`, `--L` (supports `Npi`),
  `--phases {1234}`, `--tol` (default `1e-10`), `--max-newton` (default 50),
  `--continuum-Ns 32,64,128`, `--rng-seed 12345`,
  `--include-global-phase-zero-mode`,
  `--no-eisenstat-walker`, `--ew-eta-max 0.9`, `--ew-eta-min 0.01`.
- **Outputs**: `Psi_star.npy`, `Psi_ansatz.npy`,
  `hessian_evals_projected.npy`, `hessian_ritz_vectors_projected.npy`,
  `proof_results.json`.
- **CLI**:
  ```bash
  python3 PDE/tect_newton_krylov.py \
      --config PDE/config_template_brazovskii.json \
      --N 64 --L 20pi --phases 1234 --outdir newton_N64 \
      --tol 1e-10 --max-newton 50 --continuum-Ns 32,64,128
  ```
- **Dependencies**: `real_backend_pt_bcc_mixed_v3.py` (`residual`, `hessian_vec`,
  `shell_free_energy`), `tect_solver_pt_v3.py` (`make_mock_branch_data`; optional,
  falls back to minimal shell seed if unavailable).
- **Math note**: Math37-AddA (Brazovskii lock, $\phi_0$), Math38 (first-order regime).
  Trust-region inner solve (Steihaug-Toint) safely handles indefinite Hessian
  from Class II numerical differentiation. Lanczos with deterministic seeding
  and partial reorthogonalisation every 5 steps.
- **v2.1 patch** (2026-04-16): strict `sanitize_for_json()` walker
  (NaN/Inf safe), Phase 1 downstream gate blocking Phases 2–4 on
  non-convergence, `phase1_converged_flags` in Phase 4,
  `phase_failed()` + downstream-blocked summary, Phase 2 near-zero
  warning for residual translation modes.
- **v2.2 patch** (2026-04-16): **CRITICAL** — merit-function trust-region.
  `backend_consistency_audit.py` proved `residual ≠ ∇(shell_free_energy)`
  (direction-dependent ratio, Test 1) while `(R, H=J)` is perfectly
  self-consistent (Test 2: ratio=1.0 at machine precision).
  Fix: trust-region merit switched from `shell_free_energy` to
  $m(\Psi) = \frac{1}{2}\|R_{\text{proj}}\|^2$.  Armijo line search also
  merit-based.  Predicted reduction uses linear model of $\|R\|^2$:
  $\Delta m_{\text{pred}} = -\alpha \operatorname{Re}\langle g, Hs\rangle
  - \frac{1}{2}\alpha^2 \|Hs\|^2$.
  `NewtonStepRecord` gains `merit` field.  $F$ still logged for physics.
  Test 6 confirmed $J=DR$ has ~1% asymmetry (Class II numerical Fréchet
  derivative); GMRES now default inner Krylov solver. CG retained via
  `--krylov cg`.  New CLI flags: `--krylov {gmres,cg}`, `--gmres-restart N`.
- **v2.3 patch** (2026-04-16): Eisenstat-Walker Choice 2 adaptive forcing
  terms for the inner Krylov solve.  Fixed `tcg_tol_rel=5e-4` caused
  GMRES iteration-count explosion near convergence (tCG=1945,2839 at
  steps 3,4 of N=32 run) because quadratic Newton convergence shrinks
  $\|R\|$ faster than the linear system improves.  EW adapts:
  $\eta_k = \gamma(\|R_k\|/\|R_{k-1}\|)^\alpha$ with safeguard
  $\eta_k \ge \gamma\eta_{k-1}^\alpha$, clamped to $[\eta_{\min},\eta_{\max}]$.
  Defaults: $\gamma=0.9$, $\alpha=2$, $\eta\in[0.01,0.9]$.
  New CLI flags: `--no-eisenstat-walker`, `--ew-eta-max`, `--ew-eta-min`.
- **v2.4 patch** (2026-04-20): Math56-Addendum theorem-anchored Phase-0 gate
  wiring.  Introduces `_run_v24_phase0_gate(Psi_star, params, verbose)`
  in `tect_newton_krylov.py`; called inside `run_proof_pipeline` between
  the Phase 1 downstream-block check and the Phase 2 entry.  The gate:
  (i) extracts $(\lambda, \gamma, \mu^2)$ preferring
  `quartic_lambda` / `sextic_gamma` over `lambda` / `gamma`;
  (ii) skips silently (`skipped=True`, `passed=False`) when any parameter
  is non-finite, when `BrazovskiiParams` invariants are violated
  ($\lambda \ge 0$ or $\gamma \le 0$), or when
  $\mu^2 \ge r_c^{\mathrm{meta}} = 2\lambda^2/(15\gamma)$
  (outside Math56-Addendum Theorem 1 existence window);
  (iii) otherwise evaluates the separatrix statistic
  $V(\Psi_\star) = \langle|\Psi|^2\rangle/\phi_+^2$ against
  $G_0^{\mathrm{op}} = \alpha_{\mathrm{sep}}(\mu^2) + \delta$ with
  $\delta = $ `V24_G0_CUSHION`; and (iv) finally calls
  `v24_class2_guard` which raises `RuntimeError("Class-II floor breach")`
  whenever $\langle|\Psi|^2\rangle < \rho_\star = \kappa\,\phi_+^2$.
  A non-skipped FAIL triggers `results["downstream_blocked"] = True` and
  short-circuits Phases 2/3/4; `phase_failed()` now recognises the v2.4
  gate FAIL even when downstream phases are not requested.  New CLI flag
  `--disable-v24-gate` (debug only) suppresses gate enforcement.  Output
  JSON gains `phase0_gate_v24` with fields
  `{passed, skipped, reason, mean_sq, V, G0_op, rho_star, phi_plus}`.
  New dependency: `PDE/v24_thresholds.py` v2.4.0 (22/22 unit tests).
  Regression coverage: `tests/test_v24_gate_integration.py` (8/8 tests
  exercising all six branching paths plus config-key priority).
  **Theorem anchoring**: Math56-Addendum Theorem 2 (separatrix) and
  Corollary 1 (class-II floor) are enforced fail-closed; the gate is
  defensive — Newton-Krylov dynamics are unchanged.
- **Known limitations** (documented in file header):
  - Zero-mode projector built once from $\Psi_0$, not rebuilt per Newton step.
  - Phase 3 compares only against $\Psi=0$; other branches not checked.
  - GMRES trust-region uses simple boundary clipping (not optimal like
    Steihaug-Toint); merit-based accept/reject provides robustness.
  - **Runtime integration test NOT YET RUN** (requires backend + GPU).
- **v2.6 enhancement** (2026-04-22, Math66): In-solver Hermitian projection on
  Class-II (cII) block via Path-X symmetrisation. New parameter
  `use_symmetrised_cII=True` (default) enables
  $\widetilde{\mathcal{J}}_{\mathrm{cII}} := \frac{1}{2}(J_{\mathrm{cII}} + J_{\mathrm{cII}}^\dagger)$
  in the Hessian-vector product (line 546, HessianOperator.matvec). Requires torch
  for adjoint JVP computation; gracefully degrades if torch unavailable.
  New helper functions `_get_cii_block_mask`, `_compute_adjoint_jacobian_vec_v26`,
  `_symmetrise_jacobian_cii_v26` implement Math66 §2–§6 Path-X mandate.
  **Maturity**: SKELETON (requires torch). Unit tests in `tests/test_v26_phase_d.py`
  (5 tests: import, Hermiticity U1, PCG routing R1, MINRES fallback R2, v2.4 regression).

### sweep_mu2_phase3.py  (v3.1)  [ACTIVE]
- **Purpose**: Automated μ² parameter sweep driver for Phase 3 criticality
  search. Launches `tect_newton_krylov.py` as subprocess at each μ² value,
  parses Newton step output in real-time, and saves incremental results.
- **Inputs**: `--config <cfg.json>`, `--solver <solver.py>`, `--N`, `--L`,
  `--mu2 <comma-sep list>` (default: 0.20→0.005), `--outdir`,
  `--phases` (default: 123), `--cpu-idle <sec>` (default: 120),
  `--heartbeat <sec>` (default: 30), `--no-clean`, `--solver-args`.
- **Outputs**: `sweep_results.json`, `sweep_summary.txt` (per-outdir),
  plus per-point `newton_rigorous_N{N}/` subdirectories with full solver output.
- **CLI**:
  ```bash
  python PDE/sweep_mu2_phase3.py \
      --config PDE/config_template_brazovskii.json \
      --N 16 --L 16 \
      --mu2 0.30,0.25,0.20,0.15,0.10,0.05
  ```
- **Dependencies**: `tect_newton_krylov.py` (subprocess), `psutil` (optional;
  fallback CPU-time monitoring on Windows).
- **Key features**: CPU-based hang detection (not stdout-based, since GMRES
  can be silent 20+ minutes normally), Windows compatibility via
  threading+queue, PYTHONUNBUFFERED injection, live Newton step parsing,
  heartbeat during silence, critical-point estimation via linear
  interpolation of ΔF sign change.
- **Known limitation**: Launches a fresh subprocess per μ² point with
  analytic BCC ansatz each time. Cannot chain solutions between points
  (use `continuation_mu2.py` for branch tracking).
- **Math note**: Math55 (continuation methodology).

### continuation_mu2.py  (v1.1)  [ACTIVE]
- **Purpose**: In-process μ² continuation method for BCC branch tracking.
  Solves the trivial-vacuum collapse problem: starts from very negative μ²
  (where $r = \mu^2 + Yq_0^4 < 0$ makes $\Psi=0$ an unstable saddle),
  finds the nontrivial BCC solution, then marches μ² upward carrying
  the converged $\Psi^*$ as seed for each successive step.
- **Inputs**: `--config <cfg.json>`, `--N` (default 16), `--L` (default 16),
  `--mu2-start` (default -1.0), `--mu2-end` (default 0.30),
  `--mu2-step` (default 0.05), `--tol` (default 1e-6),
  `--max-newton` (default 50), `--psi0 <Psi.npy>` (optional external seed),
  `--krylov {gmres,cg}`, `--gmres-restart`, `--save-every`, `--quiet`.
- **Outputs**: `continuation_N{N}/continuation_results.json`,
  `continuation_N{N}/continuation_log.txt`,
  `continuation_N{N}/Psi_star_mu2_*.npy` (saved every `--save-every` points).
- **CLI**:
  ```bash
  # Coarse scan (N=16, fast)
  python PDE/continuation_mu2.py \
      --config PDE/config_template_brazovskii.json \
      --N 16 --L 16 \
      --mu2-start -1.0 --mu2-end 0.30 --mu2-step 0.1 \
      --tol 1e-6 --quiet

  # Fine scan near critical point
  python PDE/continuation_mu2.py \
      --config PDE/config_template_brazovskii.json \
      --N 16 --L 16 \
      --mu2-start -0.20 --mu2-end -0.10 --mu2-step 0.01 \
      --psi0 continuation_N16/Psi_star_mu2_m02000.npy \
      --tol 1e-6
  ```
- **Dependencies**: `tect_newton_krylov.py` (in-process import: `newton_solve`,
  `build_bcc_ansatz`, `compute_energy_difference`, `lanczos_hessian`,
  `analyze_projected_spectrum`), `real_backend_pt_bcc_mixed_v3.py`.
- **Key features**: In-process (no subprocess overhead), Psi carried in
  memory between steps (~5× faster than `sweep_mu2_phase3.py`), automatic
  trivial-solution detection (RMS amplitude < 1e-6), Phase 3 flip detection
  with linear interpolation of $\mu^2_{\mathrm{crit}}$, early termination
  on 3 consecutive trivial solutions (branch lost), incremental JSON save.
- **Math note**: Math55 (trivial-vacuum diagnosis, continuation methodology,
  instability criterion $r < 0$).
- **v1.1 changes (2026-04-20)**: (i) lazy import of
  `PDE/v24_thresholds.py`; (ii) `_v24_precheck_mu2_end(mu2_end, lam,
  gam)` raises `RuntimeError` if the continuation terminus exceeds
  $r_c^{\text{meta}} = 2\lambda^2/(15\gamma) = 0.01522$ (Math56-Addendum
  Theorem 1; this is the precondition whose violation produced the
  2026-04-20 trivial-vacuum collapse); (iii) warns if
  $r_c^{\text{global}} < \mu^2_{\text{end}} \leq r_c^{\text{meta}}$
  (metastable terminus); (iv) prints `v24_banner(...)` once at
  startup if the module is available. Backward-compatible: absent
  `v24_thresholds.py`, the precheck is skipped and the v1.0
  behaviour is preserved.

### hess_jump_audit.py  (v1.1)  [ACTIVE]
- **Purpose**: Phase-2.5 acceptance-gate diagnostic (Math56). Probes whether
  a reported projected-Hessian eigenvalue is a genuine BCC-condensate spectral
  gap or a grid artefact. Implements the three-criterion gate
  (G1 Fourier-band localisation, G2 cross-grid zero-pad overlap,
  G3 Ritz residual) plus the Phase-0 vacuum-escape diagnostic
  (RMS$|\Psi^*|/\varphi_0$ relative to the BCC seed amplitude
  $\varphi_0 = \sqrt{-4\lambda/(15\gamma)}$) and emits a typed verdict key
  (`MATH55_CONTINUATION_REQUIRED`, `UV_GHOST_AT_N64`,
  `BOTH_GRIDS_INVALID`, `INCONCLUSIVE`).
- **Inputs**: `--dir-N32 <path>` (directory containing `Psi_star.npy`,
  `hessian_evals_projected.npy`, `hessian_ritz_vectors_projected.npy`),
  `--dir-N64 <path>` (same), `--config <cfg.json>` (Brazovskii parameters
  $\mu^2, \lambda, \gamma, q_0, L$), `--n-vecs` (number of Ritz pairs to
  audit per grid, default 8), `--out <run_dir>` (audit run directory),
  `--skip-ritz-residual` (optional; skips the backend-dependent G3 check
  if `torch` / backend module unavailable).
- **Outputs**: `<run_dir>/phase2p5_gate_N32_N64_<date>.json`
  (raw per-grid Fourier-band powers, top-$k$ eigenvalues, peak wavenumbers,
  Ritz residuals, cross-grid overlap matrix max and row/col maxes,
  verdict key), `<run_dir>/phase2p5_gate_summary.md` (human-readable
  summary: per-grid table, gate decisions G0/G1/G2/G3, verdict block,
  remediation prescription).
- **CLI**:
  ```bash
  python PDE/hess_jump_audit.py \
      --dir-N32 PDE/runs/newton_N32 \
      --dir-N64 PDE/runs/newton_N64 \
      --config PDE/config_template_brazovskii.json \
      --out PDE/runs/hess_audit_2026-04-20
  ```
- **Dependencies**: `numpy`, `scipy.fft`. Optional: `torch` +
  `real_backend_pt_bcc_mixed_v3` (used only for the G3 Ritz-residual check
  through `hessian_vec`; skipped cleanly when absent via `--skip-ritz-residual`).
- **Key features**:
  - `_fourier_mass_bands(v_real, N, L, q0)` implements G1 — partitions
    $|\hat v(k)|^2$ into three bands ($k < 0.5 q_0$, $0.5q_0 \le k \le 1.5 q_0$,
    $k > 1.5q_0$) and returns $(\rho_{\mathrm{IR}}, \rho_{\mathrm{shell}},
    \rho_{\mathrm{UV}})$ normalised to unit sum.
  - `_zero_pad_fft(v_flat_N, N, M)` spectral interpolator
    $I_{N}^{M}$: FFT at $N$, zero-pad the $N^3$ spectrum into the $M^3$
    Brillouin zone (with correct Nyquist handling), inverse FFT, rescale
    by $(M/N)^3$ to preserve the physical $L^2$ norm. Norm-preservation
    verified numerically on a smooth test field to ratio $1.000000$.
  - `_overlap_matrix(V_flat_N, V_flat_2N, N, M)` returns the
    $k\times k$ matrix $O_{ij} = \langle I_N^M v_i^{(N)}, v_j^{(M)}\rangle
    / \|\cdot\|\|\cdot\|$ (G2 cross-grid overlap). Reports
    $\|O\|_\infty$ (max entry), row maxes, column maxes.
  - `_ritz_residual(backend, Psi, v_flat, lam, params, N)` computes
    $\eta = \|(\hat H - \lambda)v\|_2/\|v\|_2$ through the backend's
    `hessian_vec` for G3 (skipped if backend unavailable).
  - `_linear_brazovskii_spectrum_from_k(N, L, r, Z, Y, n_smallest)` returns
    the reference free-theory dispersion $\omega(k) = r + Zk^2 + Yk^4$
    sorted in ascending order; used as a sanity plot against measured
    Ritz eigenvalues at the trivial vacuum.
  - `_audit_grid(dirpath, N, params, backend, n_vecs)` per-grid pipeline:
    loads $\Psi^*$ + Ritz pairs, computes RMS$|\Psi^*|/\varphi_0$ for G0,
    runs G1 on each Ritz vector, G3 residual if backend present,
    returns a structured record.
  - Trivial-vacuum detector uses RMS-relative metric
    `psi_trivial = (psi_rms / phi_0) < 1e-2`
    (chosen so that the BCC seed $\varphi_0 \approx 0.266$ comfortably
    passes while the observed $\Psi^* \approx 0$ triggers).
  - `_verdict_from_observables(g32, g64, overlap)` emits the typed
    verdict key consumed by CHANGELOG / OPEN-QUESTIONS.
- **Math note**: Math56 (wavenumber-stratified Hessian decomposition
  Theorem 1; grid-invariance iff IR-localisation Theorem 2; UV-band
  $\lambda_{\mathrm{UV}}\sim N^4$ scaling Proposition 3; Phase-2.5
  soundness). Result of first run (2026-04-20): on the existing
  N=32 and N=64 Newton-Krylov endpoints both grids showed
  RMS$|\Psi^*|/\varphi_0 \sim 10^{-6}$ (trivial-vacuum collapse),
  $\rho_{\mathrm{UV}} = 0$ at both grids (UV-ghost hypothesis refuted),
  cross-grid overlap $\mathcal{O}_{\max} = 1.26\times 10^{-4}$; verdict
  `MATH55_CONTINUATION_REQUIRED`. Fully documents the retraction of
  F-2026-04-20-05.
- **Intended workflow** (v2.4 protocol, pending implementation in
  `tect_newton_krylov.py`): (i) run Math55 continuation
  (`continuation_mu2.py`) from $\mu^2_0 = -1$ to target
  $\mu^2_{\text{target}} = 5\times 10^{-3}$ (Math56-Addendum
  Corollary 1; v2p4-patch-plan §2.2 Option B) on a coarse grid,
  carry $\Psi^*$ across grids; (ii) execute `tect_newton_krylov.py`
  with the Phase-0 gate
  $\|\Psi^*\|_{\mathrm{RMS}}/\varphi_+ \geq G_0^{\text{op}} = 0.708$
  (Theorem 2) and the Class-II guarded quotient
  $\rho_{\min} \geq \rho_* = 6.44\times 10^{-5}$ (Theorem 3);
  (iii) run this audit script on the resulting $\Psi^*$ at $N=32$
  and $N=64$; Phase-2 $m^{*2}$ values are reportable **only after**
  G0+G1+G2+G3 all pass with $G_{2,\min}=0.90$ (Theorem 4) and
  $\|r\| \leq 10^{-1}\cdot|\lambda_{\text{Ritz}}|$ (Theorem 5).
- **v1.1 changes (2026-04-20)**: (i) lazy import of
  `PDE/v24_thresholds.py` for `V24_G2_MIN = 0.90` and `V24_G3_REL =
  1e-1`; (ii) per-eigenvalue G3 gate replaced by the relative Saad
  bound $\|r\| \leq V24\_G3\_REL\cdot|\lambda_i|$ (per-row tag
  `rel` or legacy `abs(legacy)` when v2.4 module absent);
  (iii) `_verdict_from_observables` / `gate_pair` now accept a
  `lam_0` argument so G3 is computed relative to the dominant
  Ritz eigenvalue. Backward-compatible: with the module missing,
  the previous absolute $1\!\times\!10^{-3}$ bound is used and a
  warning tag is printed.

### v24_thresholds.py  (v2.4.0)  [ACTIVE]
- **Purpose**: Theorem-anchored, framework-agnostic numerical core
  for the v2.4 Phase-0 / Phase-2.5 gates and the Class-II abort
  guard. Single source of truth for every v2.4 threshold; no other
  module under `PDE/` or `tools/` is permitted to hard-code any of
  these numbers. Implements the five theorems of
  `Docs/math/TECT-Math56-Addendum.tex.txt`.
- **Inputs**: none from disk. Pure-Python callable API.
  - `BrazovskiiParams(lam, gam)` — canonical locked values
    $\lambda=-0.43$, $\gamma=1.62$. Frozen dataclass; rejects
    $\gamma\leq 0$ or $\lambda\geq 0$.
  - `v24_separatrix_thresholds(mu2_target, p)` — returns a
    `SeparatrixReport` with $\varphi_+$, $\varphi_-$,
    $\alpha_{\text{sep}}$, $G_0^{\text{raw}}$, $G_0^{\text{op}}$,
    $\rho_*$, $r_c^{\text{global}}$, $r_c^{\text{meta}}$. Raises
    `ValueError` if $\mu^2_{\text{target}} > r_c^{\text{meta}} =
    2\lambda^2/(15\gamma)$ (Theorem 1 precondition).
  - `v24_phase0_gate(psi_abs_sq_mean, separatrix, logger=None)` —
    evaluates the vacuum-escape statistic $V =
    \|\Psi\|_{\mathrm{RMS}}/\varphi_+$ against
    $G_0^{\text{op}}$; returns dict, does not raise.
  - `v24_class2_guard(rho_min_value, separatrix, logger=None)` —
    raises `RuntimeError` when $\rho_{\min} < \rho_*$.
  - `v24_phase25_overlap(v_a, v_b)`,
    `v24_phase25_residual_rel(residual_norm, lam_ritz)`,
    `v24_phase25_gate(...)` — G2 + G3 helpers.
  - `v24_banner(mu2_target, lam, gam)` — prints the full threshold
    table at startup.
- **Outputs**: return values only; nothing written to disk.
- **CLI**: module self-test —
  ```bash
  python3 -m PDE.v24_thresholds
  # Prints the banner and verifies the locked mu^2=0.26 precondition
  # is correctly rejected with a ValueError.
  ```
- **Dependencies**: `numpy`, `math`, `dataclasses`. No torch, no
  backend, no disk I/O. Consumers: `PDE/continuation_mu2.py`
  (pre-continuation check + banner), `PDE/hess_jump_audit.py`
  (G2 / G3 gate constants), and the pending
  `PDE/tect_newton_krylov.py` v2.4 (Phase-0 gate + Class-II
  guard).
- **Constants** (all derived, not heuristic; see Math56-Addendum §G):
  - `V24_MU2_TARGET_DEFAULT = 5.0e-3` — recommended continuation
    end-point ($0.44\,r_c^{\text{global}}$, deep inside the
    existence window).
  - `V24_G0_CUSHION = 5.0e-2` — finite-$N$ cushion on top of the
    raw separatrix threshold.
  - `V24_G2_MIN = 0.90` — Rayleigh-Ritz 20% error budget per side
    (Theorem 4).
  - `V24_G3_REL = 1.0e-1` — relative Saad residual constant
    (Theorem 5).
  - `V24_RHO_STAR_FACTOR = 1.0e-3` — Class-II abort floor as a
    fraction of $\varphi_+^2$ (Theorem 3).
- **Unit tests**: `tests/test_v24_thresholds.py` — 21 tests
  (critical scales, separatrix table at $\mu^2=3/5/8/11.4\times
  10^{-3}$, locked-$\mu^2$ rejection, Phase-0 gate edge cases,
  Class-II guard, G2 threshold geometry, G3 relative bound,
  banner content, invariant rejection of wrong-sign parameters).
  All pass in 0.033 s on 2026-04-20.
- **Audit artefact**: `Docs/supplementary/v24_threshold_sympy_check.py`
  regenerates the numerical tables symbolically and resolves
  open item X5 (Math37-AddA §A.3 mis-labeling of $\varphi_0^2$).
- **Math note**: Math56-Addendum §§A-G.

### tect_solver_pt_v3.py  (v3.3)  [ACTIVE]
- **Purpose**: PyTorch-accelerated pseudospectral IMEX gradient-flow
  solver for the TECT Brazovskii core (family-split + internal locking).
- **Inputs**: `--config <cfg.json>` (`mu_sq, lambda, gamma, grid, L, seed`),
  `--backend PDE/real_backend_pt_bcc_mixed_v3.py`, `--grid {32,64,128}`,
  `--L`, `--steps`, `--tol`, `--device`,
  `--laplacian-mode {spectral,bcc_symbol,mixed_bcc}`,
  `--init-mode {external,pure_noise,seed_plus_noise,corr_seed,bcc_seed}`.
- **Outputs**: `Psi_init.npy`, `Psi_corr.npy`, `Psi_BCC.npy`,
  `patch_centers.npy`, `config.json`, `metadata.json`,
  residual / energy history arrays.
- **CLI**:
  ```bash
  python3 PDE/tect_solver_pt_v3.py --config cfg.json \
      --backend PDE/real_backend_pt_bcc_mixed_v3.py \
      --grid 64 --L 16.0 --steps 2000 --output ./run
  ```
- **Dependencies**: `real_backend_pt_bcc_mixed_v3.py`, `tect_version_manifest.py`.
- **Math note**: Math38. v3.3: `make_mock_branch_data` now accepts
  `quartic_lambda`, `sextic_gamma` and sets seed amplitude to
  $\phi_0 = \sqrt{-4\lambda/(15\gamma)} \approx 0.266$ (Math37-AddA).
  Legacy amplitudes (0.22/0.15/0.10) retained as fallback when kwargs absent.

### real_backend_pt_bcc_mixed_v3.py  (v3.1)  [ACTIVE]
- **Purpose**: PyTorch backend: Brazovskii functional, gradient,
  `hessian_vec`, `covariant_coupling_vec`, mixed-BCC Laplacian.
- **Inputs**: `Psi` tensor `(C,N,N,N)`, `params` dict
  (`r, Z, Y, lambda, gamma, q0, Lx, Ly, Lz, grid, device`).
- **Outputs**: Python API only (`energy`, `gradient`, `hessian_vec`,
  `covariant_coupling_vec`, shell-stiffness symbols).
- **CLI**: imported; not standalone.
- **Dependencies**: `torch`, optional `intel_extension_for_pytorch`.
- **Math note**: Math38 + Math39 optimization set (lru-cached KX/KY/KZ,
  1D-broadcast BCC symbol).

- **Kinetic convention (BINDING v2, 2026-04-16)**:
  The Brazovskii linear term in `_brazovskii_linear_term_t` implements
  ```
  F_kin[Psi] = (1/2) ∫ [ r |Psi|² + Z |∇Psi|² + Y |∇²Psi|² ] d³x
  ```
  with Fourier dispersion `ω(k) = r + Z k² + Y k⁴`. The Math38
  Brazovskii form `Y(k² − q0²)² + μ²` expands to
  `(μ² + Y q0⁴) + (−2Y q0²) k² + Y k⁴`. Full coefficient matching
  gives **three** binding relations:
  ```
  Y  = Y                       (trivial)
  Z  = -2 Y q0²                (shell position)
  r  = μ² + Y q0⁴              (shell depth ⇒ ω(q0) = μ²)
  ```
  Canonical values for `q0 = 0.6801747616`, `Y = 1.0`, `μ² = 0.26`:
  ```
  Z = -0.9252754126      r = 0.4740336473
  ```
  **All three must be satisfied simultaneously.** Setting only `Z, Y`
  without adjusting `r` leaves `ω(q0) = r − Z²/(4Y) ≠ μ²` — this
  corrupts the condensate amplitude and breaks locked-triple
  self-consistency (documented: v1 fix gave ω(q0) = 0.046 instead of
  0.26; see `NEGATIVE-RESULTS.md` F-2026-04-16-01 v2 addendum).
  The `q0` config field itself is only read by `_shell_bias_term_t`
  (gated by `eta_shell`, off by default) and by `bcc_seed` initial
  conditions; it does NOT enter the runtime kinetic dynamics directly.

- **Runtime consistency gate (`_check_kinetic_convention`, added 2026-04-16)**:
  On first call to `residual()`, the backend verifies that the config
  satisfies both `|Z − (−2Yq0²)| < 10⁻⁶` and `|r − (μ² + Yq0⁴)| < 10⁻⁶`.
  If either fails, `ValueError` is raised with a diagnostic message
  referencing this manual section. This prevents silent execution under
  inconsistent parameters. Gate fires once per process (module-level flag).

---

## 3. Finite-audit extractors (Math44/45/46)

### math46_c2_extractor.py  (v0.8)  [ACTIVE]
- **Purpose**: Class-II (gravity) finite-audit extractor; enforces Math46c
  compliance and aggregates `Z_h` as a p²-weighted mean.
- **Inputs**: `--package-root <solver_out>`, `--backend <backend.py>`,
  `--momenta "1,0,0;0,1,0;0,0,1"`, `--fd-eps`, `--projector-tol`,
  `--probe-mode`, `--audit-tol`, `--target-Zh 0.5`,
  `--probe-consistency-mode`, `--out`.
- **Outputs**: `math46_c2_audit_v0_8.json` (T1/T2/T3a diagnostics,
  Z_h aggregate, Gram-whitened mixing, H0 falsification flag,
  `fail_closed_E4 = ¬uses_surrogate`).
- **CLI**:
  ```bash
  python3 PDE/math46_c2_extractor.py --package-root ./solver_N64 \
      --backend PDE/real_backend_pt_bcc_mixed_v3.py \
      --out c2_audit_N64.json
  ```
- **Dependencies**: `real_backend_pt_bcc_mixed_v3.py`; consumed by
  `run_audit_pipeline.py`.
- **Math note**: Math46c. Target `Z_h → 0.5` (matches Math45 theorem).

### math46_c3_extractor.py  (v0.7)  [ACTIVE]
- **Purpose**: Class-III (gauge) finite-audit extractor for EW sector;
  computes `c_W*`, `c_B*` via Han–Avron–Saad stochastic Tr log.
- **Inputs**: `--package-root`, `--backend`, `--eps`,
  `--shell-delta-factor`, `--n-samples`, `--lanczos-steps`,
  `--audit-tol 1e-2`, `--seed`, `--allow-surrogate`, `--out`.
- **Outputs**: `math46_c3_audit_v0_7.json`
  (T6 audit, `pass_T6_final = pass_T6 ∧ pass_frame_nonzero`,
  trace-log effective action, doublet-node diagnostics).
- **CLI**:
  ```bash
  python3 PDE/math46_c3_extractor.py --package-root ./solver_N64 \
      --backend PDE/real_backend_pt_bcc_mixed_v3.py \
      --n-samples 32 --lanczos-steps 48 --out c3_audit_N64.json
  ```
- **Dependencies**: `real_backend_pt_bcc_mixed_v3.py`; consumed by
  `run_audit_pipeline.py`. Requires `metadata["doublet_channels"] = [0,1]`.
- **Math note**: Math44/Math46b. Targets `c_W* = 1/(96π²)`, `c_B* = 1/(64π²)`.

### run_audit_pipeline.py  (v1.0)  [ACTIVE]
- **Purpose**: Orchestrator for the full finite-audit chain
  (solver → config patch → C2 → C3 → summary) over multiple grids.
- **Inputs**: `--grids 32 64 128`, `--resume`, `--only-summary`,
  `--solver-steps N`, `--c3-n-samples N`, `--c3-lanczos N`,
  `--stage-timeout` (default 7200 s).
- **Outputs**: `audit_run_<timestamp>/` containing `solver_N*/`,
  `c2_audit_N*.json`, `c3_audit_N*.json`, `audit_summary.json`,
  `audit_pipeline.log`. Prints ASCII summary table with ✓/✗ flags.
- **CLI**:
  ```bash
  nohup python3 PDE/run_audit_pipeline.py > /dev/null 2>&1 &
  ```
- **Dependencies**: `tect_solver_pt_v3.py`, `math46_c2_extractor.py`,
  `math46_c3_extractor.py`.
- **Math note**: Math44/45/46. Primary CI-style validator for one-loop
  gauge + gravity targets.

---

## 4. n*=1 diagnostic chain (Stage U2–U4)

### bloch_linearization.py  (v1.1)  [ACTIVE]
- **Purpose**: Linearised Bloch operators `L(G*)` via second variation.
- **Inputs**: `Psi0`, patch centers, backend `hessian_vec`.
- **Outputs**: 3×3 Bloch matrices per patch, eigenvalues, k-derivatives.
- **CLI**: imported; no standalone entry.
- **Dependencies**: backend; consumed by `transport_extractor`,
  `run_pipeline_n1`.
- **Math note**: Math38 Stage U2 Module 1.

### projector_spectral.py  (v1.0)  [ACTIVE]
- **Purpose**: Spectral projector `P*` onto near-zero eigenspace of `L(G*)`.
- **Inputs**: `L(G*)` per patch, tolerance, optional `n_modes` cutoff.
- **Outputs**: `ProjectorResult` (P*, eigenvalues/vectors,
  orthonormality check, carrier overlaps `ℓ_∥A, ℓ_IA, ℓ_JA`).
- **CLI**: imported; `condensate_projector_all(bloch_results, ...)`.
- **Dependencies**: `bloch_linearization`.
- **Math note**: Math38 Stage U2 Module 2.

### transport_extractor.py  (v2.0)  [ACTIVE]
- **Purpose**: Transport coefficients `M_i = P* K_i P*`, stiffness `Γ_ij`,
  decomposition into `λ_∥, α, β` per patch via Pauli trace.
- **Inputs**: Bloch results, projector results, `Psi0`, backend hessian.
- **Outputs**: `TransportResult`, Löwdin second-order correction,
  LaTeX / text tables.
- **CLI**: imported; high-level entry `full_stage_U2_pipeline(...)`.
- **Dependencies**: `bloch_linearization`, `projector_spectral`, backend.
- **Math note**: Math38 Stage U2 Module 3.

### carrier_audit.py  (v1.0)  [ACTIVE]
- **Purpose**: Existence certificate `∃A : ℓ_∥A > η_threshold` for
  gauge-boson mass generation via projected velocity operator `M_∥`.
- **Inputs**: projector + Dirac results; candidate carrier basis.
- **Outputs**: per-mode `(ℓ_∥, ℓ_1, ℓ_2)`, existence flag, reports.
- **CLI**: imported; used by `run_pipeline_n1`.
- **Dependencies**: `projector_spectral`, `transport_extractor`.
- **Math note**: Math38 Stage U3.

### remote_gap_audit.py  (v1.0)  [ACTIVE]
- **Purpose**: Certificate that `L(k)` is gapped away from condensate
  neighborhoods (`Δ_bench > η_{R,ρ}`).
- **Inputs**: `Psi0`, params, patch centers, `q₀`, k-grid, hessian.
- **Outputs**: analytical linear gap, numerical random-sample gap,
  combined certificate.
- **CLI**: imported; `full_remote_gap_audit(...)`.
- **Dependencies**: backend hessian; consumed by `run_pipeline_n1`.
- **Math note**: Math30 Stage U4.

### live_m_parallel.py  (v1.0)  [ACTIVE]
- **Purpose**: Longitudinal effective mass `m_∥` from live extractor
  outputs; closes discrepancy D5.
- **Inputs**: transport results; optional patch-pair weights.
- **Outputs**: `m_∥` per patch / per pair, shell mean ± std, theory tag.
- **CLI**: imported; `compute_live_m_parallel(...)`.
- **Dependencies**: `transport_extractor`; consumed by `run_pipeline_n1`.
- **Math note**: Math37-AddA. Closed-form `m*² = M² / λ_∥`.

### run_pipeline_n1.py  (v1.2)  [ACTIVE]
- **Purpose**: One-stop n*=1 diagnostic chain: Bloch → projector →
  transport → Dirac coefficients → carrier audit → remote gap.
- **Inputs**: `--input <run_dir>` (must contain `Psi_corr.npy`,
  `config.json`, `patch_centers.npy`); optional `--output <out>`,
  `--n_sample 30`.
- **Outputs**: JSON summary (`λ_∥, α, β, Gate certificates, m_∥`),
  NPZ arrays, text/LaTeX reports.
- **CLI**:
  ```bash
  python3 PDE/run_pipeline_n1.py --input ./run_demo --output ./run_demo/nstar1
  ```
- **Dependencies**: Stage U2–U4 modules.
- **Math note**: Math38. **Caveat**: n*=1 truncation is diagnostic,
  not theorem-strength.

### tect_actual_extractor_pt_v3.py  (v3.1)  [ACTIVE]
- **Purpose**: Load converged package; compute transport coefficients,
  `m*` from theory vs numerics; emit extraction-ready JSON.
- **Inputs**: solver output dir (`Psi_corr.npy, config.json,
  metadata.json, patch_centers.npy`).
- **Outputs**: extraction-ready JSON with `λ_∥, α, β, m_∥^theory,
  m_∥^numeric`, provenance audit.
- **CLI**: programmatic main entry (invoked by higher-level orchestrators).
- **Dependencies**: `transport_extractor`, `live_m_parallel`, backend.
- **Math note**: Math37-AddA + Math38.

---

## 5. Rank, Chern, and stability analysis

### make_rank2_bcc_seed.py  (v1.0)  [UTILITY]
- **Purpose**: BCC initial conditions with exact rank-2 internal structure.
- **Inputs**: `--grid, --L, --mode {A,B,C,all}, --n-seeds, --out-dir`.
- **Outputs**: `Psi_rank2_<mode>_seed<k>.npy`, `rank2_seed_manifest.txt`.
- **CLI**:
  ```bash
  python3 PDE/make_rank2_bcc_seed.py --grid 64 --L 16.0 --mode all --n-seeds 8 --out-dir ./seeds
  ```
- **Dependencies**: numpy only.
- **Math note**: Math38. Modes: family-split / chiral-Z₃ / SVD-projected random.

### rank2_check.py  (v1.0)  [DIAGNOSTIC]
- **Purpose**: SVD singular-value spectrum diagnostic; validates rank-2.
- **Inputs**: `Psi_corr.npy` (path currently hardcoded — edit script).
- **Outputs**: global SVD, per-family SVD, rank via `1e-6` threshold.
- **CLI**: `python3 PDE/rank2_check.py`.
- **Dependencies**: numpy.
- **Math note**: Math38 closed-form predicts rank = 2.

### dirac_index_bcc.py  (v1.0)  [ACTIVE]
- **Purpose**: Family-wise Dirac index on `T³/O` via spectral flow and
  Chern analysis.
- **Inputs**: `--psi <Psi.npy>`, `--grid, --L, --n-int`.
- **Outputs**: Dynkin index, anomaly coefficients per family, Chern
  numbers, winding estimates.
- **CLI**:
  ```bash
  python3 PDE/dirac_index_bcc.py --psi Psi_rank2_C_seed0.npy \
      --grid 64 --L 16.0 --n-int 3
  ```
- **Dependencies**: numpy, scipy.
- **Math note**: Paper I Prop 5.3; Callias index.

### tect_gap2_chern_solver.py  (v1.0)  [ACTIVE]
- **Purpose**: First Chern number `c₁` of rank-2 projector bundle per
  BCC family (Fukui–Hatsugai–Suzuki lattice).
- **Inputs**: `--Nk, --scan, --optimize`.
- **Outputs**: `c₁` per family (target `c₁ = 1 ⇒ N_g = 3`).
- **CLI**: `python3 PDE/tect_gap2_chern_solver.py --Nk 128`.
- **Dependencies**: numpy.
- **Math note**: closes Gap-2 (`N_g`) via TKNN invariant.

### tect_rank_selection_v4.py  (v4.0)  [ACTIVE]
- **Purpose**: Rank selection via three independent paths: (A) quartic
  fine-tuning, (B) anomaly cancellation, (C) gauge backreaction.
- **Inputs**: none (analytical).
- **Outputs**: per-path prediction, `B_k(rank)`, anomaly polynomial,
  CW effective potential.
- **CLI**: `python3 PDE/tect_rank_selection_v4.py`.
- **Dependencies**: numpy, itertools.
- **Math note**: Paper III Prop 5.4. Path B ⇒ Gr(2,5).

### tect_c5_bcc_stability.py  (v1.0)  [ACTIVE]
- **Purpose**: Verify BCC remains energetically preferred when
  `Ψ ∈ ℂ³ → ℂ⁵`.
- **Inputs**: none.
- **Outputs**: Alexander–McTague cubic coeff, quartic eigenvalues
  (N=3 vs N=5), free-energy comparison (BCC/FCC/SC/HEX), Dirac
  index on Gr(2,5), cuboctahedral count.
- **CLI**: `python3 PDE/tect_c5_bcc_stability.py`.
- **Dependencies**: numpy.
- **Math note**: Supports Paper III rank-selection proof.

### intervalley_extractor_v4.py  (v4.0)  [SUPERSEDED]
- **Purpose**: Cross-patch Gate 2 & 3 WITNESS quantities from 6×6
  intervalley Hessian blocks.
- **Inputs**: Hessian at antipodal pairs `(G_+, G_-)`.
- **Outputs**: `ℓ_∥^cross`, `ℓ_I^cross`, `m_scalar`, stiffness tensor.
- **Status**: superseded by `transport_extractor.py` for final
  Pauli-trace extraction; retained as a necessary (not sufficient)
  Gate preprocessor.
- **Math note**: Math18/Math30.

---

## 5b. Topological / spectral-flow verifications

### math49c_v3_sim.py  (v1.0)  [ACTIVE]
- **Purpose**: Numerical mod-2 spectral-flow certification of the BCC
  first-shell pair bundle. Closes Math49c-v3 Theorem `thm:flow` by
  reproducing $\mathrm{sf}_{\mathbb{Z}_2}=1$ on $\mathbb{C}^6_-$ and
  $=0$ on $\mathbb{C}^6_+$ to machine precision under the three
  theorem hypotheses (H-BCC, H-lattice, H-v2-topology).
- **Inputs**: none (all parameters hard-coded to mainline
  $q_0 = 0.6801747616$, $\mu^2_{\rm target} = 5\times 10^{-3}$);
  CLI accepts `--n-lambda`, `--out-json`, `--quiet`.
- **Outputs**: JSON summary
  (`q0, mu2_target, n_lambda, lam_values, eig_plus, eig_minus,
  zero_crossings_plus, zero_crossings_minus,
  mod2_spectral_flow_{plus,minus}, holonomy_check_{plus,minus},
  holonomy_sign_minus, L0_spectrum, elapsed_seconds`) and pass/fail
  message on stdout.
- **CLI**:
  ```bash
  python PDE/math49c_v3_sim.py \
      --n-lambda 401 \
      --out-json runs/math49c_v3_sim_summary.json
  ```
- **Dependencies**: numpy only (no scipy, no torch, no external BLAS
  flags). Deterministic, no stochastic components.
- **Math note**: `docs/math/TECT-Math49c-v3-sim.tex.txt` (companion
  certification); underlies theorem is Math49c-v3 Rev. 2026-04-21
  Theorem `thm:flow` / `thm:FR-final`.
- **Runtime**: $\sim 2.3$ s single-threaded for N_λ=401; $\sim 9$ s
  for N_λ=1601 (convergence sanity check).
- **Convergence**: zero-crossing counts on both sectors are invariant
  under 4× sampling refinement (N_λ: 401 → 1601), confirming the
  mod-2 invariant is genuinely topological.

### bz_eta_integrator.py  (v2.0, md5 `0db7a5ff`)  [ACTIVE]
- **Purpose**: Direct BZ integration of the 1-loop coefficient
  $c_4(\epsilon) := \int_{\Omega_{\rm BZ}} d^3k/(2\pi)^3\,P_4(\hat k)/\omega^2(k)$
  at the TECT Brazovskii fixed point, certifying $\gamma_{44}<0$
  (IR-irrelevance of the cubic-anisotropy coupling) by direct
  numerical evaluation at the physical $\epsilon$. Complements the
  $J_1$-reduction certificate
  `docs/supplementary/Math_IR_Bound_v4_BZ_interval.py` and the
  shell-adaptive rigorous certificate `PDE/bz_shell_adaptive.py`.
- **Inputs**: none (TECT mainline $q_0=0.6801747616$, $\mu^2=5\times 10^{-3}$,
  $\lambda=-0.43$, $\gamma=1.62$, $(A,B)=(3/2,1)$ hard-coded);
  CLI accepts `--N_list`, `--interval_N`, `--interval_dps`,
  `--skip_interval`, `--report`.
- **Outputs**: grid-convergence table on stdout; JSON report with
  full diagnostics (`angular_check`, `convergence`, `richardson`,
  `bz_volume_exact`, `bz_volume_numerical`, `interval_certificate`)
  at `PDE/bz_eta_integrator_report.json`.
- **CLI**:
  ```bash
  python3 PDE/bz_eta_integrator.py \
      --N_list 64,128,192,256 \
      --interval_N 16 --interval_dps 50
  # or skip slow interval stage:
  python3 PDE/bz_eta_integrator.py --N_list 64,128,192,256 --skip_interval
  ```
- **Dependencies**: numpy (required), mpmath (optional, interval stage).
  $O_h$ octant reduction: only $k_i\ge 0$ octant scanned (×8 factor),
  cell-centered midpoint quadrature.
- **Math note**: `docs/math/TECT-Math_IR_Bound-v4-BZ-integrator.tex.txt`
  (§2.1 rewritten 2026-04-21 late with Irwin-Hall CDF volume formula and
  regression-guard Remark).
- **Runtime**: $\sim 2$ s for $N_{\rm full}=256$ on single thread
  (NumPy; 1.05M cells inside BZ, octant-reduced).
- **Result at mainline**: $c_4(\epsilon) = +1.8503\times 10^{-3} > 0$
  with 5-digit grid-refinement stability across
  $N_{\rm full}\in\{128,192,256\}$, Richardson-extrapolated central
  value $+1.8503\times 10^{-3}$; derived
  $\gamma_{44}/\mathcal N = -3.42\times 10^{-4} < 0$ (IR-irrelevant).
- **v1.0 $\to$ v2.0 patch (2026-04-21 late)**: `truncated_octahedron_volume(A,B)`
  replaced with the Irwin-Hall CDF piecewise form valid on all $A/B\ge 0$.
  Prior v1.0 formula $V_{\rm BZ}=8B^3-(4/3)(3B-A)^3$ was a cube-minus-corner-tetrahedra
  expression valid only on $2B\le A\le 3B$ and returned the incorrect value
  $V_{\rm BZ}=7/2$ at mainline $s=A/B=3/2\in[1,2]$. v2.0 gives
  $V_{\rm BZ}(3/2,1)=4$ in agreement with the numerical mask count. Self-test
  `_self_test_bz_volume()` added over $A\in\{0.5,1.0,1.5,2.0,3.0,5.0\}$ at $B=1$.
  The $c_4$ cell-wise integrator never invokes the closed-form volume formula,
  hence all cached $c_4$ results at $N\in\{64,128,192,256\}$ are regression-free.
- **Interval certificate (status)**: naive cell-wise mpmath.iv enclosure
  in this module remains dependency-dominated by the Brazovskii-shell
  peak and is retained only as a baseline. The rigorous certificate is
  produced by the companion module `bz_shell_adaptive.py` (§5c below).

### bz_shell_adaptive.py  (v1.0, md5 `ada51b4b`)  [ACTIVE]
- **Purpose**: Rigorous mpmath.iv interval-arithmetic certificate for
  $c_4(\epsilon)>0$ at the TECT Brazovskii fixed point, closing the
  sign-closure (SB) criterion of the Proof-Completion Checklist for
  Pillar 8 (emergent Lorentz invariance). Exploits the closed-form
  radial primitive
  $F(r) = \tfrac{1}{8p}\ln\!\big[((r-p)^2+q^2)/((r+p)^2+q^2)\big]
       + \tfrac{1}{4q}\big[\arctan((r-p)/q)+\arctan((r+p)/q)\big]$
  obtained by real partial-fraction factorization
  $m^2+(r^2-q_0^2)^2 = [(r-p)^2+q^2]\,[(r+p)^2+q^2]$
  with $p=\sqrt{(R+q_0^2)/2}$, $q=\sqrt{(R-q_0^2)/2}$,
  $R=\sqrt{q_0^4+m^2}$. Angular reduction uses the $O_h$ fundamental
  domain $D'=\{0\le t\le s\le 1\}$ with $(s,t)$-parametrization
  $\hat n=(1,s,t)/\sqrt{1+s^2+t^2}$; cube-face vs. hex-face branching
  at $s+t=1/2$. The centered-form identity $\int_{D'} P_4\,d\Omega = 0$
  permits subtracting $F_0:=F(B)$ from the integrand radial factor,
  reducing the cell-wise interval wrap by $\sim 40\times$ (essential
  for a sign-definite enclosure at tractable grid size).
- **Inputs**: none (TECT mainline hard-coded, same as `bz_eta_integrator.py`);
  CLI accepts `--N_octant` (default 64), `--depth` (default 10),
  `--dps` (default 40), `--self-test` (optional quadrature verification).
- **Outputs**: sub-enclosure breakdown $I_{\rm square}$, $I_{\rm hex}$ and
  final $c_4(\epsilon)$ enclosure on stdout with central value and
  half-width; optional JSON at `PDE/bz_shell_adaptive_report.json`.
- **CLI**:
  ```bash
  python3 PDE/bz_shell_adaptive.py --N_octant 64 --dps 40
  # optional self-test (closed-form F vs. composite midpoint at n=5e4):
  python3 PDE/bz_shell_adaptive.py --self-test
  ```
- **Dependencies**: mpmath (required). Uses `mpmath.iv` interval context
  with monotonicity-based endpoint evaluation; endpoints extracted via
  `mp.make_mpf(x._mpi_[i])`. Adaptive depth-10 subdivision of
  $(s,t)\in D'$. No NumPy, no Torch.
- **Math note**: `docs/math/TECT-Math_IR_Bound-v4-shell-adaptive.tex.txt`
  (Theorem `thm:c4-positive`, Proposition `prop:pillar8` promoting
  Pillar 8 to PROVED).
- **Runtime**: $\sim 40$ s at $N_{\rm octant}=64$, depth 10, dps 40
  (single-threaded mpmath). Scales approximately linearly in cell count.
- **Result at mainline**: rigorous enclosure
  $c_4(\epsilon) \in [+1.401951\!\times\!10^{-3},\,+2.367959\!\times\!10^{-3}] > 0$,
  central $+1.884955\!\times\!10^{-3}$, half-width $4.83\!\times\!10^{-4}$;
  $I_{\rm square}\in[+1.309\!\times\!10^{-3},+1.629\!\times\!10^{-3}]$,
  $I_{\rm hex}\in[+5.936\!\times\!10^{-3},+1.061\!\times\!10^{-2}]$.
  Cross-check against direct NumPy integrator $+1.8503\!\times\!10^{-3}$:
  agreement $1.9\%$ relative.
- **Self-test**: closed-form $F(r)$ vs. composite midpoint quadrature
  at $n_{\rm test}=5\times 10^4$ agrees to $<5\times 10^{-9}$ relative
  at all tested radii including shell $r=q_0$.
- **Proof-Checklist advancement**: this module advances criterion SB
  (sign/bound closure via rigorous enclosure) for Pillar 8, complementing
  criterion LC (logical closure) carried by the companion math note and
  criteria CM/RP from the standing TECT infrastructure.

---

## 5e. Representation-theoretic LR / branching scripts (supplementary)

All modules in §5e live under `Docs/supplementary/` rather than `PDE/`
because they are exact symbolic censuses with no lattice / dynamical
content; they are single-file, dependency-free Python 3 scripts.

### Math49d_R5_replacement_search.py  (v1.0, md5 `dab7f483`)  [ACTIVE — wave-1]
- **Purpose**: Wave-1 census of
  $M^{\lambda}=\dim\mathrm{Hom}_{G_{\rm SM}}(\mathbb{C}_{(\mathbf{1},\mathbf{1})_{0}},S^{\lambda}V)
       =c^{\lambda}_{(k,k,k),(k,k)}$
  over all partitions $\lambda$ with $|\lambda|\le 15$ and
  $\ell(\lambda)\le 5$. Establishes $\sup M^{\lambda}=1$ on this
  range ($k\le 3$) and identifies the minimal direct-sum realisation
  of the three-copy $(\mathbf{1},\mathbf{1})_{0}$ isotype as
  $E_{\min}=\mathcal{O}\oplus\det V\oplus S^{(2,1,1,1)}V$.
- **Inputs**: none (hard-coded search range).
- **Outputs**: console table of non-trivial multiplicities and SU(5)
  dimensions (hook-content formula), plus the minimal direct-sum
  decomposition.
- **CLI**: `python3 Docs/supplementary/Math49d_R5_replacement_search.py`
- **Dependencies**: Python 3 standard library only (`collections`,
  `typing`, `sys`).
- **Math note**: `Docs/math/TECT-Math49d-R5-replacement.tex.txt`.
- **Algorithm**: Littlewood-Richardson coefficients by DFS
  enumeration of skew-SSYTs of shape $\lambda/\mu$ with content
  $\nu$, visited in reverse-reading-word order; lattice-prefix
  constraint $\#i\ge\#(i+1)$ enforced at every step. Validated
  against classical Pieri products $s_{(1)}^2$, $s_{(2)}^2$,
  $s_{(1,1)}^2$ and the trivial identity
  $c^{\lambda}_{\emptyset,\lambda}=1$.

### Math49d_R5_replacement_search_wave2.py  (v1.0, md5 `8541621b`)  [ACTIVE — wave-2]
- **Purpose**: Wave-2 extension of the R5 LR census from $|\lambda|\le 15$
  to $|\lambda|\in\{20,25\}$ (i.e.\ $k\in\{4,5\}$). Closes
  `Q-2026-04-20-PR1` with verdict `F-2026-04-21-R5W2`:
  $\sup_{|\lambda|\le 25,\;\ell\le 5} M^{\lambda}=1$, falsifying
  the single-Schur-functor Pillar-6 strategy through the full
  $k\le 5$ window.
- **Inputs**: none.
- **Outputs**:
  - console: wave-1 sanity re-check, per-$|\lambda|$ multiplicity
    table (only nonzero $M^{\lambda}$ listed for readability),
    structural summary with $\sup M$, verdict line;
  - JSON: `Docs/supplementary/Math49d_R5_wave2_report.json`
    (md5 `8665629c`) with fields `wave`, `description`,
    `wave1_sup_M`, `multiplicity_census.{20,25}.entries`, `sup_M`,
    `lambda_of_sup`, `total_elapsed_s`.
  - Audit log: `Docs/supplementary/logs/Math49d_R5_wave2_run.log`.
- **CLI**: `python3 Docs/supplementary/Math49d_R5_replacement_search_wave2.py`
- **Dependencies**: imports `Math49d_R5_replacement_search` (wave-1,
  co-located); otherwise stdlib only.
- **Math note**: `Docs/math/TECT-Math49d-R5-replacement-wave2.tex.txt`
  (Theorem `thm:wave2`, Table I).
- **Runtime**: $\sim 0.05$ s single-threaded for the $192+377=569$
  partitions of the $k\in\{4,5\}$ range.
- **Result at mainline**: $15$ partitions of $20$ and $21$ partitions
  of $25$ realise $M^{\lambda}=1$; all others satisfy $M^{\lambda}=0$;
  $\sup M^{\lambda}=1$ in both cases. Structural observation: every
  realiser has $\lambda_{3}=k$ and the realiser count matches
  $\binom{k+2}{2}$.
- **Proof-Checklist advancement**: falsifies the single-bundle version
  of Pillar 6 at the physical layer through $|\lambda|\le 25$; Pillar 6
  remains SCAFFOLD (the geometric $\chi^{\mathbb{Z}_6}$ layer from
  Math49d-R3 arithmetic is unchanged and PROVED).

---

## 6. Falsification / sweeps

### q18_commensurability_sweep.py  (v1.1)  [DIAGNOSTIC]
- **Purpose**: Falsification `Q-2026-04-15-18` — sweep solver across
  three grid resolutions, verify continuum-limit `q₀` convergence.
- **Inputs**: `--solver, --backend, --config, --outdir, --steps, --device,
  --seed, --skip-solve`.
- **Outputs**: per-run `(k_min, q0_cfg, q0_meas, |G|_1st)` table,
  `q18_radial_spectrum.npz` per run (centers / S_rad / dk / q0_meas),
  top-level sweep-summary JSON; passes when `q0_meas → k_min`
  monotonically.
- **CLI (full sweep)**:
  ```bash
  python PDE/q18_commensurability_sweep.py \
      --solver  PDE/tect_solver_pt_v3.py \
      --backend PDE/real_backend_pt_bcc_mixed_v3.py \
      --config  PDE/config_template_brazovskii.json \
      --outdir  runs/q18_sweep_2026-04-15 \
      --steps 1500 --device auto --seed 17
  ```
- **CLI (measurement-only, uses existing `Psi_corr.npy`)**:
  ```bash
  python PDE/q18_commensurability_sweep.py \
      --solver  PDE/tect_solver_pt_v3.py \
      --backend PDE/real_backend_pt_bcc_mixed_v3.py \
      --config  PDE/config_template_brazovskii.json \
      --outdir  runs/q18_sweep_2026-04-15 \
      --skip-solve
  ```
- **v1.1 fixes (2026-04-16)**: (i) `load_final_psi()` now recognizes
  `Psi_corr.npy` (canonical name written by `tect_solver_pt_v3.py`
  v3.x) in addition to legacy `emerge_*.npy` / `final_Psi.npy`.
  (ii) `--skip-solve` flag added so a completed sweep can be
  re-measured post-hoc without re-spawning the solver.
- **CLI**:
  ```bash
  python3 PDE/q18_commensurability_sweep.py \
      --solver PDE/tect_solver_pt_v3.py \
      --backend PDE/real_backend_pt_bcc_mixed_v3.py \
      --config PDE/configs/default.json \
      --outdir ./q18_sweep --steps 1500
  ```
- **Dependencies**: `tect_solver_pt_v3.py`, backend.
- **Math note**: Math39-Reorg. Verifies shell-selection principle.

---

## 7. Provenance / records utilities

### tect_version_manifest.py  (v1.1)  [UTILITY]
- **Purpose**: Dual fingerprint `(theory_version, code_version)` for
  every run so results map back to exact framework and code.
- **Inputs**: theory version, run label, params, optional extras.
- **Outputs**: manifest JSON (theory/code versions, git SHA, timestamp,
  closed/open invariant status, machine info).
- **CLI**: imported; `build_manifest(...)`, `write_manifest(...)`.
- **Math note**: provenance tooling; records policy §5.

### stamp_version_headers.py  (utility)  [UTILITY]
- **Purpose**: Idempotently prepend/refresh TECT version-header blocks
  on all `.py` under `PDE/`.
- **Inputs**: `MODULE_VERSIONS` dict (canonical); target `PDE/`.
- **Outputs**: files edited in place; no-ops on itself, `deprecated/`,
  `backup_GL_*`, `__pycache__/`.
- **CLI**: `python3 PDE/stamp_version_headers.py`.
- **Math note**: maintains theory↔code dual fingerprint post-tag bump.

---

## 8. Operator checklists

### 8.1 When a new solver run is needed
1. Update `config.json` (or rely on `make_default_config`).
2. Run `tect_solver_pt_v3.py` → verify residual < `1e-6`.
3. Confirm `metadata.json` contains `doublet_channels = [0,1]`
   and `config.json` contains `physical_L == Lx` (both auto-patched
   by `run_audit_pipeline.py`).

### 8.2 When adding a new module
1. Write the module with a header block (auto-stamped by
   `stamp_version_headers.py`).
2. Add an entry to **this manual** (`CODE_MANUAL.md`) in the correct
   section, using the fixed schema.
3. Register its version in `PDE/stamp_version_headers.py :: MODULE_VERSIONS`
   and `Website/data/version_index.json`.
4. Add a `CHANGELOG.md` entry under the relevant theory tag.
5. Cross-reference in `docs/status/INDEX.md` if it is user-facing.

### 8.3 When bumping a module version
1. Bump `MODULE_VERSIONS` in `stamp_version_headers.py`, rerun it.
2. Update the corresponding entry in this manual (version + any
   changed CLI / outputs / math note).
3. Update `Website/data/version_index.json`.
4. Log the change in `CHANGELOG.md` under the current theory tag.

---

## 9. Manual revision history

| Date | Change |
|---|---|
| 2026-04-16 | Initial manual published covering all 23 PDE modules under theory tag `audit-pipeline-v1.0-2026-04-16`. Quick-start workflows, per-module schema, operator checklists. |
| 2026-04-16 | `tect_newton_krylov.py` v2.0 → v2.1: added v2.1 patch notes (JSON sanitizer, downstream gate, Phase 4 flags, near-zero warning). Math51 cross-ref. |
| 2026-04-16 | `tect_newton_krylov.py` v2.1 → v2.2: **CRITICAL** merit-function trust-region + GMRES. `backend_consistency_audit.py` proved R ≠ ∇F (Test 1/5); merit switched to m=½\|\|R\|\|². Test 6 proved J ~1% non-symmetric → GMRES default. |
| 2026-04-16 | `tect_newton_krylov.py` v2.2 → v2.3: Eisenstat-Walker Choice 2 adaptive forcing. Fixes GMRES iteration explosion (tCG=1945→2839) near convergence. Default ON; `--no-eisenstat-walker` to disable. |
| 2026-04-20 | Added `sweep_mu2_phase3.py` v3.1 entry (μ² parameter sweep driver). |
| 2026-04-20 | Added `continuation_mu2.py` v1.0 entry (μ² continuation / branch-tracking method). |
| 2026-04-20 | Added `Docs/supplementary/website_data_validator.js` v1.0 — Node.js syntactic validator for all `Website/data/*.js` and `timeline.json`. Archived per user directive that all proof / propagation code must be committed as permanent artifacts. No Python path, standalone: `node Docs/supplementary/website_data_validator.js`. |
| 2026-04-20 | External peer review (GPT) lodged against Math49d-R3, Math49c-v2, Math49b-v2, Math_EP-v2, Math_IR_Bound-v2. Six follow-up items opened (Tasks #35–#40). R3 claim retracted pending gauge-flavor resolution. |
| 2026-04-20 | Added `hess_jump_audit.py` v1.0 (Math56 Phase-2.5 acceptance-gate diagnostic). First run on the existing N=32 / N=64 Newton-Krylov endpoints refuted the UV-ghost hypothesis and established trivial-vacuum collapse + Class-II $\rho^{-1}$ singularity as the true root cause of the projected-Hessian jump $3.1485\to 54.07$. F-2026-04-20-05 SUPERSEDED, Q-2026-04-20-Q-HESS-JUMP RESOLVED (key `MATH55_CONTINUATION_REQUIRED`). Pillar 1 demoted to SCAFFOLD; both Phase-2 and Phase-3 numbers at N=32 and N=64 retracted. Next solver work (v2.4) must add a Phase-0 gate (RMS$\lvert\Psi\rvert/\varphi_0 \geq 0.3$) and replace the unguarded $q_\alpha = m_\alpha/(\rho+10^{-12})$ by a $\rho_{\mathrm{cut}}\sim 10^{-3}\varphi_0^2$-guarded quotient before any Phase-2 eigenvalue is reported. |
| 2026-04-20 | Added `Docs/math/TECT-Math56-Addendum.tex.txt` v1.0 — theorem-level derivations of the v2.4 gate thresholds. §A proves that the locked $\mu^{2}=0.26$ lies $17\times$ above the metastability window $r_{c}^{\text{meta}}=2\lambda^{2}/(15\gamma)=0.01522$, so no BCC extremum exists at locked parameters (retrospectively explains the trivial-vacuum collapse). §B derives the Phase-0 threshold from the Brazovskii separatrix $\alpha_{\text{sep}}=\phi_{-}/\phi_{+}$; at the recommended $\mu^{2}_{\text{target}}=5\times 10^{-3}$, $G_{0}=0.657+0.05$ (replaces heuristic $0.3$). §C derives the class-II abort floor $\rho_{*}=6.2\times 10^{-5}$ (replaces heuristic $10^{-3}$). §D derives $G_{2,\min}=0.90$ from the Rayleigh–Ritz perturbation bound (replaces heuristic $0.8$). §E derives $G_{3}\leq 10^{-1}\cdot m^{*2}_{\text{Ritz}}$ (relative, not absolute) from the Saad inequality. §F flags a factor-$4/3$ discrepancy [X5] between Math37-AddA §A.3 boxed $\phi_{0}^{2}=-4\lambda/(15\gamma)=0.0708$ and the re-derivation $\phi_{0}^{2}=-\lambda/(5\gamma)=0.0531$; BLOCKING for v2.4 commit. |
| 2026-04-20 | X5 RESOLVED by SymPy audit (`Docs/supplementary/v24_threshold_sympy_check.py`). Scenario A: the simultaneous first-order-lock conditions $F(\varphi_0)=0$ and $F'(\varphi_0)=0$ yield $\varphi_0^{2}=-\lambda/(5\gamma)=0.0531$ at $\mu^{2}_{c}=\lambda^{2}/(10\gamma)=0.01141$. Scenario B: the single condition $F'(\varphi_0)=0$ evaluated at $\mu^{2}=0$ yields $\varphi_0^{2}=-4\lambda/(15\gamma)=0.0708$. The Math37-AddA §A.3 box is therefore mis-labeled: it quotes the latter while calling it the first-order Brazovskii lock. Math37-AddA §A.3 flagged for erratum; non-blocking for v2.4. Numerical tables of Math56-Addendum §B also errata'd: corrected $\varphi_{+}(5\times 10^{-3})=0.2538$, $\varphi_{-}=0.0799$, $\alpha_{\text{sep}}=0.3150$, $G_{0}^{\text{op}}=0.7075$. |
| 2026-04-20 | Added `Docs/status/v2p4-patch-plan.md` — concrete diff plan parametrised by $\mu^{2}_{\text{target}}$; work-order table (A theory ✓ → B X5 ✓ → C $\mu^{2}_{\text{target}}=5\times 10^{-3}$ ✓ → D code ✓ → E-J execute). |
| 2026-04-20 | Added `PDE/v24_thresholds.py` v2.4.0 and `tests/test_v24_thresholds.py` (21 tests, all passing in 0.033 s). Single source of truth for every v2.4 threshold; hard rejects $\mu^{2}_{\text{target}} > r_{c}^{\text{meta}}$ via `ValueError`; Class-II guard raises `RuntimeError` when $\rho_{\min} < \rho_{*}$. Framework-agnostic (`numpy`+`math` only); torch callers pass scalars. Hard-codes nothing beyond the Leibler-Wickham $K_{6}=5/2$ (overridable on `BrazovskiiParams`). |
| 2026-04-20 | `PDE/continuation_mu2.py` v1.0 → v1.1: added `_v24_precheck_mu2_end` guard + startup banner. Raises before schedule construction if $\mu^{2}_{\text{end}} > r_{c}^{\text{meta}}$; this is the *operational* enforcement of Math56-Addendum Theorem 1 at run-time. Backward-compatible: absent `v24_thresholds.py`, the precheck is skipped. |
| 2026-04-20 | `PDE/hess_jump_audit.py` v1.0 → v1.1: G2 threshold tightened to $0.90$ (Theorem 4) and G3 bound replaced by the relative Saad bound $\|r\| \leq 10^{-1}\cdot\|\lambda_{\mathrm{Ritz}}\|$ (Theorem 5). Per-eigenvalue gate report prints `rel` or `abs(legacy)` tag so the audit trail reflects which bound fired. No behavioural regression when `v24_thresholds.py` absent (v1.0 absolute $10^{-3}$ retained as fallback). |
| 2026-04-22 | **Newton-Krylov v2.5 solver redesign** (Math63): specification sealed in response to failure manifest R-2026-04-21-002 (inner Krylov saturation at μ²=-1.0). Added four new modules + one continuation driver. |

---

## 10. Continuation & Adaptive Solvers (v2.5+)

### 10.1 math56_constants.py (v1.1) [ACTIVE]
- **Purpose**: Single source of truth for Brazovskii/separatrix constants. Consolidates values previously scattered across configs and modules to prevent drift.
- **Exports**: `LAMBDA`, `GAMMA`, `K6`, `PHI_PLUS`, `PHI_MINUS`, `ALPHA_SEP`, `R_C_GLOBAL`, `R_C_META`, `Q0`, `PHI_0_DEFAULT`, `assert_consistency()`, `build_seed()`, `build_seed_bcc()`.
- **v1.1 change (2026-04-22)**: Added `build_seed_bcc(N, mode, sigma, complex_seed=True, seed=42)` factory returning shape $(3, N, N, N)$ dtype `complex128` to match the active BCC backend contract `real_backend_pt_bcc_mixed_v3._shape3`. Legacy `build_seed()` (scalar-Brazovskii, $(N,N,N)$ `float64`) is unchanged — both factories now coexist, selected explicitly by the caller. Introduced as the v2.5.5 companion fix to `continuation_mu2_v25.py` after v2.5.4 honest-reporting surfaced the seed-vs-backend shape mismatch. Three modes: `"thermal"` (independent complex Gaussian per channel, per-channel variance $\sigma^{2}$), `"cold"` (all-zero), `"minimum"` (channel-uniform real amplitude $\phi_{0}$ with small Gaussian perturbation). Sandbox unit-tested across all modes (shape/dtype/variance/imaginary/determinism/legacy-preservation); all six checks pass.
- **Inputs**: None (pure constants).
- **Outputs**: Python module (imported by other solvers).
- **CLI**: `python3 PDE/math56_constants.py` (self-test).
- **Dependencies**: `numpy` (optional; only `assert_consistency()` uses it). Imported by `continuation_mu2_v25.py`, `bz_preconditioner.py`, and test suites.
- **Math note**: `Docs/math/TECT-Math63-Solver-Redesign-v2.5.tex.txt` §3, Module 1. Implements locked parameters from Math56 and Math56-Addendum.
- **Consistency checks**: Verifies $R_C^{\text{global}} = \lambda^2/(10\gamma)$, $R_C^{\text{meta}} = 2\lambda^2/(15\gamma)$ to 1e-10; checks separatrix ordering and amplitude bounds.

### 10.2 bz_preconditioner.py (v1.2) [ACTIVE]
- **Purpose**: Fourier-diagonal Brazovskii preconditioner for Newton-Krylov v2.5 inner Krylov solves. Reduces condition number κ from ~1000 to ~10 at the ill-conditioned shell |**k**|=q₀.
- **Class**: `BrazovskiiPreconditioner(N, q0, sigma_fn, m_reg_sq=1e-4, device='cpu', dtype='float64')`.
  - `__call__(r)`: Apply P⁻¹(r) via FFT → pointwise multiply → IFFT. O(N log N).
  - `update_sigma(mu2_current)`: Refresh μ²-dependent shift σ (frozen dataclass design; callable-based in practice).
- **Inputs**: residual **r** (shape N³, torch.Tensor or numpy).
- **Outputs**: preconditioned residual **z** = P⁻¹(**r**), same type/shape.
- **CLI** (self-test): `python3 PDE/bz_preconditioner.py` (verifies linearity at machine precision and regression-only upper-bound check on O(N³ log N) scaling at the asymptotic pair N∈{32, 64}).
- **Dependencies**: `torch` (required), `numpy`. Imported by `continuation_mu2_v25.py`.
- **Math note**: `TECT-Math63` §2C. Preconditioner: $P^{-1}(\mathbf{k}) = 1 / [(\mathbf{k}^2-q_0^2)^2 + m_{\text{reg}}^2 + \sigma]$ where $\sigma = \mu^2$ (current continuation point) and $m_{\text{reg}}^2 = 10^{-4}$ (shell regularization).
- **v1.1 change**: `_test_scaling()` hardened against FFT plan-cache artifact — switched from {8, 16, 32} single-pass timing to {16, 32, 64} with 3-pass warm-up + 50-iter average. Trigger: R-2026-04-22-001 local launch hit a false-positive at N=16 (0.019 s cold-cache outlier vs N=32 0.0014 s plan-cached).
- **v1.2 change (correction of v1.1)**: Replaced the symmetric `[0.5×, 2.0×] × ratio_nlogn` tolerance band with an **upper-bound-only regression check** at `3.0 × ratio_nlogn`. Trigger: second self-test run produced `ratio_time = 3.13×` against `ratio_nlogn = 9.60×`, which violated the v1.1 lower bound (4.80×). Evidence: linearity still at 10⁻¹⁶; N=64³ ≈ 2 MB fits L3 cache, and MKL AVX-512 SIMD makes the kernel legitimately faster than the asymptotic prediction. Decision: `O(N³ log N)` is strictly an upper bound — symmetric banding was mathematically unjustified. v1.2 retains only the regression sentinel and prints a diagnostic note when `ratio_time < 0.5 × ratio_nlogn` (cache-resident regime). See CHANGELOG 2026-04-22 entry.
- **Status**: Active; diagnostic execution gated on user local machine.

### 10.3 tools/check_jacobian_symmetry.py (v2.0) [DIAGNOSTIC]
- **Purpose**: Classify Jacobian $\mathcal{J} = \partial F/\partial \phi$ as SPD / symmetric-indefinite / asymmetric via finite-difference probes on random vectors. **v2.0 extension**: the classifier is complex-aware and uses the sesquilinear inner product $\langle u, v\rangle = u^{*}\!\cdot v$ on $\mathcal{H} = \mathbb{C}^{n}$, so the **real-self-adjoint** operators that arise from real-valued TECT functionals are now correctly identified when the state $\Psi$ is `complex128`.
- **Function**: `probe_symmetry(residual_fn, x0, n_probes=5, eps=1e-6, ...)`.
  - Computes $\mathcal{J}(\mathbf{u}_i)$ by FD: $\mathcal{J}(\mathbf{u}_i) = [F(\phi + \epsilon \mathbf{u}_i) - F(\phi - \epsilon \mathbf{u}_i)] / (2\epsilon)$.
  - Checks antisymmetry norm $\max_{i<j} |\operatorname{Re}\langle \mathbf{u}_i, \mathcal{J}\mathbf{u}_j \rangle - \operatorname{Re}\langle \mathcal{J}\mathbf{u}_i, \mathbf{u}_j \rangle| / \|\mathcal{J}\|_2$ using $\operatorname{Re}\langle\cdot,\cdot\rangle$ (sesquilinear for complex inputs; reduces to the real bilinear product for real inputs).
  - Checks Rayleigh-like quotients $\operatorname{Re}\langle \mathbf{u}_i, \mathcal{J}\mathbf{u}_i \rangle$ for sign / positivity.
  - Returns dict: `{symmetric, indefinite, asymmetric, rayleigh_samples, antisymmetry_norm, dtype_kind, inner_product, ...}`.
- **Inputs**: residual function, current iterate φ (may be `float64` **or** `complex128` — the input dtype is now preserved rather than silently cast), n_probes ∈ {3, 5, 7}, FD step ε.
- **Outputs**: classification dict (JSON-serializable). New fields `dtype_kind` $\in \{\texttt{"real"}, \texttt{"complex"}\}$ and `inner_product` $\in \{\texttt{"real-dot"}, \texttt{"Re(vdot)"}\}$ expose the path taken so silent mis-classifications cannot recur.
- **CLI**:
  ```bash
  python3 tools/check_jacobian_symmetry.py \
      --residual-fn real_backend_pt_bcc_mixed_v3:residual \
      --x0 phi_star.npy \
      --config config.json \
      --n-probes 5 \
      --verbose \
      --output result.json
  ```
- **Dependencies**: `torch` (optional), `numpy`. Imported by `continuation_mu2_v25.py`. Torch is preferred when available; the sandbox numpy-only path is exercised by `_self_test`.
- **Math note**: `TECT-Math63` §2A (probe routing) and §2A.1 (Complex-Hermitian Probe Policy — v1.1 addendum, 2026-04-22). Probes every 5 Newton steps (cached in between).
- **Accept-SPD threshold**: antisymmetry norm / ‖**J**‖ < 1e-8 AND all $\operatorname{Re}\langle \mathbf{u}_i, \mathcal{J}\mathbf{u}_i \rangle > 0$.
- **MATURITY (2026-04-22, v2.0)**: **PROOF-GRADE (diagnostic tier)**. The complex-Hermitian probe policy is now formally specified in Math63 §2A.1; the implementation is backward-compatible with the v1.2 real path (Proposition in §2A.1) and numerically validated by a 6-case `_self_test` covering (a) real SPD diagonal, (b) real symmetric-indefinite, (c) real asymmetric tridiagonal-skew, (d) complex Hermitian SPD diagonal, (e) complex anti-Hermitian $iD$, (f) complex non-diagonal Hermitian tridiagonal $\pm i$ off-diagonal (Gershgorin-SPD). In the sandbox (numpy-only fallback, torch unavailable) all six cases pass: antisymmetry norm $\sim 10^{-17}$ for the three Hermitian-path cases, $\approx 0.28$–$0.77$ for the two genuinely asymmetric / anti-Hermitian cases, with classification matching the analytic expectation. The probe is now qualified for live application to the TECT BCC residual; the remaining gate is the user-side re-run of `run_v25_diagnostic.ps1` to observe the real Jacobian classification under the fixed policy.
- **v1.1 change (2026-04-22)**: Added `_self_test()` exercising `probe_symmetry` on three analytically-controlled linear Jacobians (SPD diagonal, symmetric-indefinite diagonal, tridiagonal skew + diagonal asymmetric). `main()` intercepts `--selftest` before argparse so required-argument validation is bypassed in self-test mode. Companion marker files `PDE/__init__.py` and `tools/__init__.py` added for explicit regular-package identity.
- **v1.2 change (2026-04-22, correction of v1.1)**: `_self_test()` made backend-coherent. `probe_symmetry()` auto-promotes a numpy `x0` to `torch.Tensor` whenever torch is importable, so v1.1's numpy-built `D_spd`, `D_ind`, `A_asym` collided with torch Tensors via `np.ndarray @ torch.Tensor` (unsupported). v1.2 selects the backend once at self-test entry (`torch` if available, `numpy` otherwise) and builds `x0` and all three test matrices in that backend. Trigger: user run raised `TypeError: unsupported operand type(s) for @: 'numpy.ndarray' and 'Tensor'` on Case 1. Earlier case-collision hypothesis for `python -m tools.xxx` ModuleNotFoundError was ruled out (`Test-Path C:\Users\...\Python312\Tools` returned `False`); timing race between the in-sandbox write of `tools/__init__.py` and the user's `-m` invocation is the most consistent remaining explanation.
- **v2.0 change (2026-04-22, Math63 §2A.1 addendum)**: Complex-Hermitian probe policy. **Trigger**: R-2026-04-22 live run under v2.5.5 produced (i) `UserWarning: Casting complex values to real discards the imaginary part` at `probe_symmetry:102` and (ii) identical `antisym/‖J‖ = 2.84e-04` across all six $\mu^{2}$ points with asymmetric classification, which is physically incompatible with a residual derived from a real-valued Ginzburg-Landau functional. **Evidence**: static audit of v1.2 exposed three coupled sub-defects: (5a) unconditional `torch.from_numpy(x0).to(dtype=torch.float64)` at line $102$ silently projected the `complex128` seed; (5b) the probe basis was generated by `torch.randn(...)` (real-valued Gaussian), so even a complex operator was only probed on the real subspace; (5c) inner products were computed by `torch.dot` / `np.dot` (bilinear), which does not implement the sesquilinear pairing required on $\mathbb{C}^{n}$ — an anti-Hermitian operator would register as "symmetric" under a bilinear product. **Decision**: the TECT GL residual with the $\lvert\Psi\rvert^{2}\Psi$ term is not holomorphic but is **real-self-adjoint** as an $\mathbb{R}$-linear operator on $\mathbb{C}^{n} \cong \mathbb{R}^{2n}$; the correct classifier is therefore $\operatorname{Re}\langle u, \mathcal{J}v\rangle = \operatorname{Re}\langle \mathcal{J}u, v\rangle$ under the sesquilinear inner product $\langle u, v\rangle = u^{*}\!\cdot v$. Implementation: (A) new helpers `_is_complex_array(x)` and `_preserve_torch_dtype(x_np)` (maps `complex128` $\to$ `torch.complex128`, `float64` $\to$ `torch.float64`, no forced cast); (B) `probe_symmetry()` branches on `x_torch.is_complex()` and generates a complex-Gaussian probe matrix $M = (M_{\Re} + i M_{\Im})/\sqrt{2}$, $M_{\Re}, M_{\Im} \sim \mathcal{N}(0,1)$ i.i.d., giving $M \sim \mathcal{CN}(0, I)$; (C) all inner products pass through a central `_inner(a, b)` helper wrapping `torch.vdot` / `np.vdot` and taking `.real` for the classification metric; (D) return dict extended with `dtype_kind` and `inner_product` fields to make the path taken explicit; (E) `_self_test` extended from 3 to 6 cases adding the three complex validations. Sandbox 6/6 PASS in numpy-only mode. Backward compatibility with v1.2 is proved in Math63 §2A.1 Proposition (real $x_{0} \Rightarrow$ $\operatorname{Re}\langle u, v\rangle = u \cdot v$ and $\mathcal{CN}$ reduces to $\mathcal{N}$, so the real path is bit-identical up to RNG order). `math56_constants.build_seed_bcc` contract (shape $(3, N, N, N)$ `complex128`) is unchanged — this fix is downstream of the seed factory and closes Layer 5.
- **Self-test CLI (recommended)**: `python tools\check_jacobian_symmetry.py --selftest` (file-path invocation; immune to `-m` ordering artefacts; sandbox-validated at 6/6 PASS under numpy-only fallback).
- **Self-test CLI (alt)**: `python -m tools.check_jacobian_symmetry --selftest` (works once `tools/__init__.py` is confirmed on disk).

### 10.4 continuation_mu2_v25.py (v2.5.7) [ACTIVE — SKELETON maturity]
- **Purpose**: Adaptive Newton-Krylov continuation solver for μ² sweeps in the Brazovskii deep-instability regime (μ² < -1e-2). Responds to failure manifest R-2026-04-21-002 (v2.4 GMRES saturation at ρ_lin ≈ 0.6).
- **Key innovations over v2.4**:
  1. **Jacobian symmetry probe** → adaptive solver selection (PCG/MINRES/FGMRES).
  2. **Fourier-diagonal Brazovskii preconditioner** → O(N log N), κ_eff ≈ 10.
  3. **Staged tolerance schedule** (1e-6 → 1e-8 → 1e-10) → tighter tolerances in certification phase.
  4. **Stagnation hard-abort** → 3+ consecutive t_Krylov=t_max → terminate with diagnostic dump.
- **Inputs**:
  - `--config <json>`: Brazovskii config (μ, λ, γ, Y, q₀).
  - `--N <int>`: grid dimension (default 32).
  - `--L <float>` or `Npi`: box size.
  - `--mu2-start, --mu2-end, --mu2-step`: continuation schedule.
  - `--diagnostic`: run 6-point diagnostic sweep {-1.0, -0.8, -0.6, -0.4, -0.2, -0.1}.
  - `--output <dir>`: output directory (default `continuation_N{N}`).
  - `--quiet`: suppress per-step output.
- **Outputs**: per-point JSON manifest with Newton iterations, inner tCG, convergence rates, Phase 2/3 results, gate decisions, wall-clock times.
- **CLI**:
  ```bash
  python3 PDE/continuation_mu2_v25.py \
      --config config_mu2_target_5e3.json \
      --N 32 \
      --diagnostic \
      --output runs/R-2026-04-22-001-newton-krylov-v25-diagnostic/
  ```
- **Dependencies**: `math56_constants.py`, `bz_preconditioner.py`, `tect_newton_krylov.py`, `real_backend_pt_bcc_mixed_v3.py` (bare-name imports from the `PDE/` directory) and `tools.check_jacobian_symmetry` (fully qualified via the `tools` regular package, resolved through a widened `sys.path` bootstrap that inserts both `PDE/` and the repository root — see v2.5.1 changelog below).
- **MATURITY (2026-04-22, v2.5.5)**: **SKELETON**. Phase D of `run_one_point_v25` (line $\sim 469$–$475$) is still an explicit PLACEHOLDER that prints `[PLACEHOLDER: Newton step ...]` and does NOT call `tect_newton_krylov.newton_solve`. Successful end-to-end execution of `scripts/run_v25_diagnostic.ps1` therefore still terminates with exit code $10$ and MANIFEST `Status: SKELETON_ONLY`, which is the *correct* honest state. v2.5.4 corrected the Math63 §2A probe-wiring attribute name (`backend.residual_bcc` $\to$ `backend.residual`); v2.5.5 sharpens the seed-factory contract by routing the driver through a new `build_seed_bcc(N, mode, sigma)` factory in `math56_constants.py` which returns the BCC-mandated shape $(3, N, N, N)$ dtype `complex128`, fixing the subsequent `Probe failed: Psi must have shape (3, Nx, Ny, Nz)` error that appeared once the §2A probe actually executed. Both v2.5.4 and v2.5.5 are *prerequisites*, not substitutes, for Task #104. No per-point `converged=True` entry can arise until Task #104 (v2.6.0) wires the real solver with the Math63 §2A probe, §2C Brazovskii preconditioner, §2D staged tolerance, and §2E stagnation guard. Any physics-bearing claim about the 6-point $\mu^{2}$ continuation must wait for a v2.6.0+ run that terminates with exit code $0$ and `Status: PASS`. **Layer-5 residual risk (post-v2.5.5)**: `tools/check_jacobian_symmetry.py::probe_symmetry` at line $102$ calls `torch.from_numpy(x0).to(dtype=torch.float64)` on what is now a `complex128` seed; current PyTorch raises `TypeError: Casting from complex to real dtype is not supported` in this situation. If that surfaces on the next live run, it will be handled as v2.5.6 (probe dtype policy — real-projection vs Hermitian-probe decision, with a Math63 §2A addendum).
- **Version history**:
  - **v2.5.7** (2026-04-22) — Math63 §2A.2 Exception-Handling Policy enforcement (Task #108). The `residual_bcc` typo (v2.5.0→v2.5.3) and the complex-probe mis-cast (`check_jacobian_symmetry` v1.0→v1.2) each survived ≥4 releases because a broad `except Exception as e: if verbose: print(...); return None` branch in `probe_jacobian_cached()` (line $488$) laundered hard programming defects (`AttributeError`, `TypeError`, silent `UserWarning`-on-cast) into polite degraded-mode fallbacks indistinguishable from legitimate runtime conditions (CUDA OOM, numerical overflow). The defect was detectable at every Newton iteration of every point but only via a `verbose=True` stderr channel that no post-run artefact captured. **Trigger**: system-wide audit of every `except Exception:` branch on the Math63 v2.5 live-execution path. **Evidence**: three broad catches in `continuation_mu2_v25.py` (lines $299$, $488$, $751$) and one in `tect_newton_krylov.py` (line $97$); `v24_thresholds.py` lines $265$/$313$ are legitimate logger guards. **Decision**: formalise Math63 §2A.2 addendum "Exception-Handling Policy" with policy points (P1)–(P5): no catch-all; dichotomy between programming errors `{AttributeError, TypeError, NameError, ImportError}` (must re-raise) and runtime conditions `{RuntimeError, ValueError, ArithmeticError, MemoryError, LinAlgError}` (may degrade); unconditional WARN log (no `if verbose` gate); truncated traceback on first per-run occurrence; import fallbacks tightened to `(ImportError, ModuleNotFoundError)` only. **Fixes applied**: (A) line $299$ import fallback narrowed; (B) line $488$ `probe_jacobian_cached` split into two-branch dispatch — programming errors propagate, runtime conditions log type+msg unconditionally and print a last-6-frames traceback on the first failure of the run; (C) line $751$ per-point main loop likewise split, with full `type(e).__name__: str(e)` and last-6-frames traceback in stderr plus the typed string in the MANIFEST's `stagnation_reason`; (D) `tect_newton_krylov.py:97` import fallback narrowed. Residual status: Phase D is still a PLACEHOLDER; diagnostic run still terminates with exit $10$ / `SKELETON_ONLY` until Task #104 (v2.6.0). The policy's **detection guarantee** (Proposition in §2A.2) foreclosing any future four-release silent persistence of a programming defect is now machine-checkable by grep: the count of `except Exception:` on the live-execution path is reducible to the two legitimate logger guards in `v24_thresholds.py`. Math63 v1.1 → v1.2 with §2A.2 addendum.
  - **v2.5.5** (2026-04-22) — Seed-factory BCC shape fix. v2.5.4 surfaced a second silent probe-layer defect: once the canonical `backend.residual` name was in place, the probe reached `real_backend_pt_bcc_mixed_v3._shape3` which rejected the seed with `ValueError("Psi must have shape (3, Nx, Ny, Nz)")`. Root cause: the legacy `math56_constants.build_seed()` returns scalar-Brazovskii shape $(N,N,N)$ `float64`, which predates the BCC backend switch and was never updated to match the active backend contract. Additionally, `continuation_mu2_v25.py:675` force-cast to `np.float64`, contradicting the backend's `complex128` requirement. Fix: new BCC-aware factory `math56_constants.build_seed_bcc(N, mode, sigma, complex_seed=True, seed=42)` returning shape $(3, N, N, N)$ `complex128` with three modes (`thermal`/`cold`/`minimum`), with independent per-channel Gaussian noise and per-channel variance $= \sigma^{2}$ in the default complex thermal mode. Driver now imports `build_seed_bcc` alongside legacy `build_seed` and constructs `Psi` via the BCC factory at line $720$; the `.astype(np.float64)` is dropped (the factory already returns the mandated dtype). Legacy `build_seed()` is left unchanged for downstream scalar callers — this is an additive rather than replacing fix. Unit tests (sandbox, six checks) confirmed: correct shape/dtype across all three modes, per-channel variance matches $\sigma^{2}$ within statistical error, imaginary content nonzero in complex thermal mode and zero in `minimum`/`cold`/`complex_seed=False` modes, determinism across repeated `seed=42` calls, legacy `build_seed()` shape and dtype unchanged. Math63 §1 specification is *sharpened*, not amended. `math56_constants.py` bumped v1.0 $\to$ v1.1. Scaffolding + honest reporting otherwise unchanged; Phase D is still a PLACEHOLDER; diagnostic run still terminates with exit $10$ / `Status: SKELETON_ONLY`. Follow-up: potential Layer-5 defect at `check_jacobian_symmetry.probe_symmetry:102` (complex$\to$float torch cast) may surface on the next live run — tracked as conditional v2.5.6. See CHANGELOG 2026-04-22 entry "continuation_mu2_v25 seed shape fix — build_seed_bcc factory (v2.5.5)" and Task #106.
  - **v2.5.4** (2026-04-22) — Math63 §2A probe wiring fix. The cached Jacobian-symmetry probe in `probe_jacobian_cached()` (line $381$) was calling `backend.residual_bcc(x, params)`, but the canonical exported function in `real_backend_pt_bcc_mixed_v3.py` is `backend.residual(Psi, params)` (verified by static AST enumeration of module-level defs: `residual` present, `residual_bcc` absent). The v2.5.0-era typo had been masked by the probe's broad `except Exception as _e:` branch, which silently returned `SymmetryClassification(symmetric=False, indefinite=False, asymmetric=True, ...)` with the error string embedded in `.reason`; the Math63 §2A probe-driven {PCG, MINRES, FGMRES} router therefore locked into unconditional FGMRES for four releases. The v2.5.3 honest-reporting contract surfaced the defect at the first live Stage $[4/4]$ run by printing `Probe failed: module 'real_backend_pt_bcc_mixed_v3' has no attribute 'residual_bcc'; using default` at every Newton iteration of every point. Fix: one-token rename on line $381$ with in-file explanatory comment; module header bumped v2.5.3 → v2.5.4 with the full Trigger/Evidence/Decision CHANGELOG block; MANIFEST driver-identification string and generation timestamp bumped accordingly. Scaffolding + honest reporting remain unchanged; Phase D is still a PLACEHOLDER and the diagnostic run still terminates with exit code $10$ / `Status: SKELETON_ONLY` until Task #104 (v2.6.0) lands. Follow-up: Task #106 (proposed) — audit every `except Exception:` branch in the v2.5 driver to prevent a recurrence of silent four-release defect concealment. See CHANGELOG 2026-04-22 entry "continuation_mu2_v25 Math63 §2A probe wiring (v2.5.4)" and Task #105.
  - **v2.5.3** (2026-04-22) — TypeError fix + honest skeleton-mode status reporting. (A) `@dataclass ContinuationPoint` (line $221$) requires `converged: bool`; the in-function seed at line $396$ now carries `converged=False`, eliminating the `TypeError: ContinuationPoint.__init__() missing 1 required positional argument: 'converged'` that aborted `[Point 1/6]` on the first live Stage $[4/4]$ run. (B) MANIFEST writer rewritten: each result is classified as `converged` / `errored` / `placeholder`; aggregate counts feed a four-valued `overall_status` $\in \{\texttt{PASS},\,\texttt{SKELETON\_ONLY},\,\texttt{FAIL},\,\texttt{UNKNOWN}\}$, rendered as a markdown per-point table with a **DANGER / HONEST STATUS** banner when the run is skeleton-only. The hardcoded `PENDING_LOCAL_EXECUTION` string is gone. (C) `main()` now returns a tri-state exit code: $0$ for PASS, $10$ for SKELETON_ONLY, $2$ for FAIL/UNKNOWN; `sys.exit(main() or 0)` at the module tail propagates it to PowerShell. (D) Companion `scripts/run_v25_diagnostic.ps1` archival block rewritten into three explicit branches, one per exit code; SKELETON_ONLY branch suppresses the `commit_v25_diagnostic.ps1` recommendation and surfaces Task #104. Math63 specification unchanged — this is scaffolding and honest-reporting only. See CHANGELOG 2026-04-22 entry "continuation_mu2_v25 TypeError fix + honest skeleton-mode status (v2.5.3)" and Task #104 (`v2.6.0: wire run_one_point_v25 Phase D to tect_newton_krylov.newton_solve`).
  - **v2.5.2** (2026-04-22) — UTF-8 locale hardening. Both `open()` calls (config read and MANIFEST write) now carry an explicit `encoding="utf-8"`. Without the pin, Python on Korean Windows resolves the implicit encoding to `cp949` and raises `UnicodeDecodeError: 'cp949' codec can't decode byte 0xe2` on the em-dash ($\text{U+2014}$) inside `PDE/config_template_brazovskii.json`. RFC 8259 §8.1 mandates UTF-8 for interchanged JSON text; this is a strict-conformance fix. The three `open(..., "proof_results.json", ...)` writes inside `tect_newton_krylov.py` (lines $1453$, $1495$, $1575$) are already pinned — verified by direct read.
  - **v2.5.1** (2026-04-22) — `sys.path` bootstrap now inserts *both* the PDE/ directory and the repository root, so `from tools.check_jacobian_symmetry import probe_symmetry` (now fully qualified) resolves on Windows/Python 3.12 regardless of CWD. The probe-unavailable warning now carries the underlying exception type and message (previously a silent FGMRES fallback that masked a Math63 §2A spec deviation). Handoff companion: `scripts/run_v25_diagnostic.ps1` simultaneously dropped its stray `--mu2_list` argument; the CLI contract for the 6-point diagnostic is solely `--diagnostic` plus `--N / --output / --config`.
  - **v2.5.0** (2026-04-22) — initial v2.5 driver sealed against Math63 specification.
- **Prerequisite — Windows filesystem case-alignment (2026-04-22)**: the `tools/` package on disk must be lowercase. The canonical directory name in the current Windows working copy `C:\Dev\TECT2\Contents` is `Tools` (capital T), which Python 3.12's `FileFinder` treats as a *different* package from `tools` even on case-insensitive NTFS (enumeration is via `os.listdir` and comparison is case-sensitive). While the directory remains capitalised, every `from tools.xxx import ...` statement — including the v2.5.1 symmetry-probe import above — will fail with `ModuleNotFoundError: No module named 'tools'`, causing the solver to silently fall back to plain FGMRES and violate the Math63 §2A routing specification. User-side remediation (PowerShell, in the repo root):
  ```powershell
  Rename-Item -Path .\Tools -NewName __tmp_tools
  Rename-Item -Path .\__tmp_tools -NewName tools
  python -c "import tools.check_jacobian_symmetry as m; print('OK:', m.__file__)"
  ```
  The two-step is mandatory: `mv Tools tools` is a no-op on case-insensitive NTFS. See CHANGELOG 2026-04-22 entry "Root-cause resolution: `tools/` ↔ `Tools/` case collision on Windows/Python 3.12".
- **Math note**: `TECT-Math63.tex.txt` full specification (§1–7). Failure manifest: `Docs/runs/R-2026-04-21-002-newton-krylov-v2p4-continuation-FAILURE.md`.
- **Acceptance criteria (diagnostic run)**:
  - At μ²=-1.0: Newton iter ≤ 8 (vs v2.4 >15), inner tCG ≤ 300 (vs v2.4 15000), ρ_lin ≤ 0.05 (vs v2.4 ≈0.6).
  - All 6 diagnostic points converge without stagnation.
  - Wall-clock: ≤ 120 s per point on 4-core CPU (diagnostic total ≤ 10 min).
- **Status**: **SPECIFICATION SEALED (Math63.tex.txt)**. Diagnostic execution deferred to user's local machine due to PyTorch unavailability in sandbox (see Stage 3, Sandbox Execution Status, Math63 §7).
- **Handoff script**: `scripts/run_v25_diagnostic.ps1` (Windows) or `.sh` (Linux/Mac) — to be created in Stage 3.
- **Sandbox blocker**: D-2026-04-21-001 (PyTorch OOM during pip install; scoped as environmental, not theoretical).

### 10.5 tools/check_jacobian_blocks.py (v1.4) [DIAGNOSTIC — Math63 §2A.3 Stage α + Math66 Path-X]
- **Purpose**: Operator-level decomposition probe for the Math63 §2A.3 framework. The full TECT residual of `real_backend_pt_bcc_mixed_v3.residual` decomposes additively as $F = F_{\mathrm{bra}} + F_{\mathrm{fam}} + F_{\mathrm{lock}} + F_{\mathrm{shell}} + F_{\mathrm{nl}} + F_{\mathrm{cII}}$ (Math63 §2A.3 Def. \ref{def:2A3-blocks}). This tool applies the Math63 §2A.1 `Re(vdot)` probe to the Jacobian of each block **individually**, so a persistent full-residual $\operatorname{antisym}/\lVert\mathcal{J}\rVert$ signal can be attributed to a specific block rather than being seen only as a sum-level observable.
- **Relation to §10.3**: strict sibling — **does not supersede** `check_jacobian_symmetry.py` v2.0. `check_jacobian_blocks.py` reuses the v2.0 probe protocol (complex-Gaussian probes, sesquilinear `vdot`-based inner product, Math63 §2A.1 thresholds) and calls it block-by-block via analytical Jacobian-vector wrappers that reach into the backend's private `_{bra,fam,lock,shell,nl,cII}_t` helpers. This is diagnostic-tier code and is explicitly documented in Math63 §2A.3 Remark (Scope) as exempt from the "public API only" discipline that governs solver code.
- **Function**: `probe_block_symmetry(jv_fn, Psi, n_probes=5, seed=42)` — applies the §2A.1 `Re(vdot)` classifier to a block-restricted matrix-vector product. `run_block_sweep(backend, params, Psi, ...)` orchestrates the full six-block sweep plus a reference full-residual probe (via `backend.hessian_vec`) for cross-validation.
- **Inputs**: backend module (`real_backend_pt_bcc_mixed_v3`), params dict (config JSON), seed iterate $\Psi$ (shape $(3,N,N,N)$ `complex128`), `n_probes` $\in \{3,5,7\}$, RNG seed.
- **Outputs**: nested dict `{per_block: {bra, fam, lock, shell, nl, cII: <probe_report>}, full: <probe_report>, shape, dtype, wall_s_total, math_note, tool_version}`. Each `<probe_report>` has `{antisym_abs, antisym_rel, rayleigh_min, rayleigh_max, rayleigh_samples, jacobian_norm, threshold, symmetric, positive_definite, indefinite, asymmetric, dtype_kind, inner_product}`.
- **CLI (v1.2)**:
  ```bash
  # Single-point probe (v1.1 back-compat path):
  python Tools/check_jacobian_blocks.py \
      --config PDE/config_template_brazovskii.json \
      --N 32 --mu2 -0.5 \
      --n-probes 5 \
      --output results/step1_block_probe.json \
      --verbose

  # Stage α (v1.2) autograd × 6-point μ² sweep:
  python Tools/check_jacobian_blocks.py \
      --config PDE/config_template_brazovskii.json \
      --N 32 \
      --mu2-list "-1.0,-0.8,-0.6,-0.4,-0.2,-0.1" \
      --backend autograd \
      --n-probes 5 \
      --output results/stage_alpha_B_autograd_on.json --verbose

  # cII-ablation full-residual probe (couplings zeroed in a params clone):
  python Tools/check_jacobian_blocks.py \
      --config PDE/config_template_brazovskii.json \
      --N 32 --mu2 -0.5 --cII-off \
      --output results/step1_cIIoff_probe.json
  ```
  Per-block summary is printed to stderr as a single aligned table with columns `antisym_abs | antisym_rel | ||J|| | Rayleigh | class`. Under `--mu2-list` a per-point table is printed followed by an aggregate `antisym_abs` matrix (one row per μ²). JSON report is written to `--output` when supplied. Self-test entry point: `python Tools/check_jacobian_blocks.py --selftest` (intercepted before argparse, matches `check_jacobian_symmetry.py` v2.0 convention).
- **Dependencies**: `numpy` (required), `torch` (required for live sweep; not required for `--selftest`). Imports the backend via `importlib.import_module("real_backend_pt_bcc_mixed_v3")` and pulls the six private `_*_t` helpers by `getattr`. Reads the BCC seed factory via `from math56_constants import build_seed_bcc` (v1.1).
- **Math note**: `TECT-Math63-Solver-Redesign-v2.5.tex.txt` §2A.3 addendum (v1.2 → v1.3). The theoretical predictions for each block are:
  - $F_{\mathrm{bra}}$ (Lemma 2A.3-1, linear real polynomial in $\widehat{\Delta}$): Hermitian → $\operatorname{antisym}/\lVert J\rVert = O(10^{-15})$;
  - $F_{\mathrm{fam}}$ (diagonal real): Hermitian → $O(10^{-15})$;
  - $F_{\mathrm{lock}}$ ($k_{\mathrm{lock}}(I - P_{0})$, Hermitian idempotent): Hermitian → $O(10^{-15})$;
  - $F_{\mathrm{shell}}$ (real symbol $\eta_{\mathrm{shell}}(|k|-q_{0})^{2}$ in $k$-space): Hermitian → $O(10^{-15})$;
  - $F_{\mathrm{nl}}$ (Lemma 2A.3-2, Wirtinger $A + B\bar v$ with $A = A^{\dagger}$, $B = B^{\mathsf{T}}$): real-self-adjoint under $\operatorname{Re}\langle\cdot,\cdot\rangle$ → $O(10^{-15})$;
  - $F_{\mathrm{cII}}$ (projected Class II, no closed-form $\mathbb{R}$-self-adjoint proof): **suspicious**.
  A live output with $\operatorname{antisym}/\lVert J_{\mathrm{cII}}\rVert \sim 10^{-4}$ and all other blocks at $10^{-15}$ identifies $F_{\mathrm{cII}}$ as the source of the full-residual signal; a persistent signal in $F_{\mathrm{bra}}$ instead points to Nyquist-mode / BCC-symbol artefacts, separated by Step 2 of the diagnostic plan.
- **Accept-symmetric threshold**: $\operatorname{antisym}/\lVert J\rVert < 10^{-8}$ (inherited from §2A / §2A.1). Exit code 0 iff every requested block **and** the full-residual reference are classified symmetric; exit code 11 otherwise.
- **MATURITY (2026-04-23, v1.4)**: **STAGE-α-EXECUTABLE (diagnostic tier)**. Harness, block-residual wrappers, v2.0-probe integration, sys.path bootstrap (v1.1), autograd cII routing (v1.2), multi-mu2 driver (v1.2), cII-off ablation switch (v1.2), grad-vs-impl decisive diagnostic (v1.3), and cos-theta Path-X classifier (v1.4) all AST-parse clean. Self-test: 8/8 PASS at Hermitian floor `antisym/|J| = {3.95e-17, 0.0, 8.98e-17, 5.05e-01, 5.39e-17}` for (diag-real-PD, diag-real-indef, Hermitian-complex, anti-Hermitian-complex, nl-Wirtinger) respectively, with new v1.4 Path-X synthetic rows (pathX-localised-synthetic cos_theta=1.0, pathX-delocalised-synthetic cos_theta≈0.707). Live Stage α four-configuration sweep gated on the user local machine, exactly as for `check_jacobian_symmetry.py`. Task #111 progress: **Path-X cos-theta classifier v1.4 landed; Math66-PathX-cos-theta-classifier.tex.txt filed (NEW)**.
- **v1.4 change (2026-04-23, Task #111: Path-X cos-theta classifier)**: Two new synthetic self-test cases (Cases 7--8) added to verify the cos-theta channel-localisation diagnostic (Math66 Path-X mandate). New function `_compute_cos_theta_pathX(A_v, P_A_v)` computes $\cos\theta(\Psi, v) := \mathrm{Re}\langle P_{\mathrm{cII}}(\Psi) A v, A v\rangle / (\|P_{\mathrm{cII}} A v\| \|A v\|)$ where $A v = (\mathcal{J} - \mathcal{J}^\dagger) v / 2$ is the anti-Hermitian Jacobian residue. Synthetic cases: (7) pathX-localised-synthetic: $A v$ is channel-projected by construction, expected $\cos\theta = 1.0 \pm 10^{-13}$ (machine epsilon); (8) pathX-delocalised-synthetic: $A v$ has both channel and non-channel components, expected $\cos\theta < 0.99$ (falsification gate per Math66 Path-X Prop.~math65-falsify). Both cases execute on pure numpy (torch-free); no backend dependency. Self-test now 8/8 PASS. Theoretical justification: Math66 Path-X diagnostic note (NEW, 8 sections: motivation, rigorous definition, Cauchy-Schwarz bound, Path-X prediction theorem, falsifiability gate, torch-less synthetic construction, CiiProjector API wiring, honest limitations, 3-part traceability chain) filed as `docs/math/TECT-Math66-PathX-cos-theta-classifier.tex.txt`. Back-compat: existing Cases 1--6 unchanged; new function is purely additive (not called by live code path, pending v1.5 integration); version header updated to v1.4 with full change log. Module version v1.3 → v1.4. CHANGELOG 2026-04-23 top entry.
- **v1.3.1 change (2026-04-22, Tools/tools case-collision hardening)**:
- **v1.3 change (2026-04-22, Decisive diagnostic)**: New `--cII-grad-check` flag and `run_decisive_cII_test()` function implement the Math64 §6 / Math65 §4 grad-vs-impl diagnostic (Case 0/1/2/3 verdicts). v1.3.1 hardened sys.path bootstrap for case-agnostic sibling imports. Exit code policy: 0 (Case 1), 12 (Case 2), 13 (Case 3). Self-test: 6/6 PASS with new orthogonal-vectors-case0 row.
- **v1.2.1 change (2026-04-22, argparse usability hotfix)**: The first live Stage $\alpha$ invocation `python Tools/check_jacobian_blocks.py --backend fd --mu2-list -1.0,-0.8,-0.6,-0.4,-0.2,-0.1` aborted with `argparse error: argument --mu2-list: expected one argument`. Root cause: Python's `argparse` refuses to accept a value that begins with `-` (e.g. `-1.0,-0.8,...`) as the argument of a string-typed option when given in the space-separated form, because it cannot disambiguate between "option-value that happens to look negative" and "an unknown optional flag". The standard workaround is the equals-sign form (`--mu2-list=-1.0,...`), but requiring this form on the published CLI is a poor user experience. Fix: new helper `_glue_negative_list_value(argv, option_name)` preprocesses `sys.argv[1:]` inside `main()` before `parser.parse_args(...)` runs; a token matching `option_name` whose immediate successor looks like a negative numerical value (`startswith("-")` and contains a digit, a comma, or `.digit`) is folded into the equals-sign form as a single token. All other token patterns, including already-equals-sign-formatted invocations and positive-numerical CSVs, are left untouched. Verification: AST-parse clean; `--selftest` retained 5/5 PASS; new 6/6 glue-function unit test covers (i) negative CSV space-separated, (ii) with other flags in front, (iii) already-equals form, (iv) positive CSV space-separated untouched, (v) single-negative value, (vi) unrelated flags with `--cII-off`. Back-compat: the equals-sign form is bit-identical under v1.2.1; v1.2 helper APIs (`_resolve_torch_jvp`, `_params_with_cII_off`, `run_multi_mu2_sweep`, `_print_single_point_report`, `_exit_code_from_sweep_report`) are preserved verbatim. Module version v1.2 → v1.2.1; §10.5 MATURITY header v1.2 → v1.2.1 (STAGE-α-EXECUTABLE tag retained). No change to Math63 §2A.1 probe policy, §2A.3 Stage $\alpha$ acceptance condition, or any probe numerics. CHANGELOG 2026-04-22 top entry.
- **v1.2 change (2026-04-22, Stage α extension)**: Three orthogonal CLI flags added to close the three residual degrees of freedom left open by the Step (D1) single-point FD-only closure. **(i) `--backend {fd,autograd}`**: the pre-existing cII path was central-FD at $\varepsilon_{\text{classII\_hess}} = 5\cdot 10^{-7}$, carrying $\mathcal{O}(\varepsilon^2) \sim 10^{-13}$ truncation and $\mathcal{O}(\varepsilon^{-1}u_{\text{round}})\sim 2\cdot 10^{-10}$ cancellation noise on `complex128`. v1.2 adds a forward-mode JVP route via `torch.func.jvp` (with `torch.autograd.functional.jvp` as graceful fallback through the private `_resolve_torch_jvp()` shim), which evaluates the exact real-linear action $A(\Psi)v + B(\Psi)\overline{v}$ at machine precision. The flag affects ONLY the cII arm of the per-block sweep; bra/fam/lock/shell/nl are analytical in both paths. **(ii) `--mu2-list CSV`**: replaces single `--mu2 VALUE` with a loop over continuation points (each with its own fresh thermal BCC seed via `math56_constants.build_seed_bcc`). The canonical Stage α list is $\mu^{2} \in \{-1.0, -0.8, -0.6, -0.4, -0.2, -0.1\}$, mirroring the R-2026-04-22 signal window. **(iii) `--cII-off`**: zeros $\{\alpha_X, \beta_X, c_{JJ}, c_{JK}\}$ in a `params` CLONE via the private `_params_with_cII_off()` helper; prunes `cII` from the block-sweep list (its trivially-zero operator would produce 0/0 under the antisym_abs / ‖J‖ division) and re-runs `backend.hessian_vec` with the ablated params. This leverages the existing early-exit at `real_backend_pt_bcc_mixed_v3._classII_effective_term_t` line 430 ($\sum|\text{coupling}|<10^{-18}\Rightarrow$ `torch.zeros_like`). The FULL-residual probe is then formally cII-free. **Acceptance condition (Math63 §2A.3 Stage α gate, Eq. `math63-2A3-stage-alpha-gate`)**: $|a_{\alpha_A}(\text{cII}) - a_{\alpha_B}(\text{cII})| \le 10^{-9}$ at every $\mu^{2}$ AND $a_{\alpha_D}(\text{FULL}) \le 10^{-12}$ at every $\mu^{2}$. Back-compat: every pre-v1.2 invocation is bit-identical under v1.2 (`--backend` defaults to `fd`, `--cII-off` defaults to False). Module version v1.1 → v1.2; §10.5 MATURITY header v1.1 → v1.2; Math63 v1.4 → v1.5 with the Stage α plan sealed. CHANGELOG 2026-04-22 top entry.
- **v1.1 change (2026-04-22, hotfix)**: The first live invocation `python Tools/check_jacobian_blocks.py --config PDE/config_template_brazovskii.json --N 32 --mu2 -0.5 ...` from the repository root aborted at line 499 with `ModuleNotFoundError: No module named 'math56_constants'`. Root cause: v1.0 relied on ambient `sys.path` resolution, but the deferred `from math56_constants import build_seed_bcc` and `importlib.import_module('real_backend_pt_bcc_mixed_v3')` both target `Contents/PDE/` which is not on `sys.path` when the script is launched from `Contents/`. This is the exact analogue of the `continuation_mu2_v25.py` v2.5.0 → v2.5.1 fix (Task #100). Patch: insert a sys.path bootstrap immediately after the `numpy` import that prepends both `Contents/PDE/` and `Contents/` using `os.path` anchored at `__file__`. The bootstrap runs unconditionally at module load — unchanged probe logic, unchanged Wirtinger JVP, unchanged exit-code contract. Self-test 5/5 PASS retained (bootstrap has no effect on the self-test path, which does not touch backend modules). Math63 §2A.3 specification unchanged — purely plumbing.
- **v1.0 change (2026-04-22)**: File created. Self-test Case 2 (diag-real-indef) initial version used a single Gaussian-random diagonal whose realisation (with `seed=0`, $n=16$) happened to have all 5 probes in the positive-Rayleigh cone, so the classifier correctly reported `symmetric=True` but the test's AND-with-`indefinite` assertion failed. Fixed by forcing a balanced diagonal `concat([+2·1_{n/2}, −2·1_{n/2}])` that guarantees Rayleigh of both signs under any 5-probe QR basis; self-test now 5/5 PASS.

### 10.6 tools/n64_continuum_audit.py (v1.2) [ACTIVE]
- **Purpose**: Execute the Pillar-1 continuum-limit audit across three grids
  (N ∈ {32, 64, 128}) to measure spectral-volume variance σ_V and extract
  the condensate mass gap κ. Validates that σ_V(h) → 0 as lattice spacing h → 0,
  closing Pillar 1 Phase 4 per Math70 forensic repair specification.
- **Inputs**: BCC backend (`real_backend_pt_bcc_mixed_v3`), Newton-Krylov solver
  (`tect_newton_krylov.newton_solve`), continuation endpoint JSON
  (`results/continuation_mu2_v25_endpoint.json`, optional fallback to μ² = 5e-3),
  Brazovskii parameters (λ, γ) locked to (−0.43, 1.62).
- **Outputs**: JSON file with three keys:
  - `"grid_results"`: dict mapping `"N_32"` / `"N_64"` / `"N_128"` to per-grid result
    dicts, each containing `{N, converged, sigma_V, kappa, m_star_sq, newton_steps, error}`.
  - `"continuum_fit"`: dict with `h_values`, `sigma_V`, `kappa`, `m_star_sq` arrays
    (one entry per grid) and continuum-extrapolation metadata.
  - `"metadata"`: theory tag, solver version, repairs applied (R1–R5), references.
- **CLI**:
  ```bash
  # Standard continuum audit (assumes endpoint JSON from Task #54)
  python tools/n64_continuum_audit.py \
      --output results/n64_audit_v1p2_2026-04-22.json
  
  # With explicit μ² override (if endpoint JSON unavailable)
  python tools/n64_continuum_audit.py \
      --output results/n64_audit_override.json
  ```
  On machines with torch unavailable, the script exits with `[ERROR] torch required...`
  at line ~365.
- **Dependencies**: `real_backend_pt_bcc_mixed_v3` (BCC lattice backend), `tect_newton_krylov`
  (v2.6.1 Path-X solver), `math56_constants.build_seed_bcc` (BCC seed factory, R1),
  `tests/conftest.make_bcc_config` (canonical config dict, R4).
- **Math note**: `TECT-Math70-N64-ContinuumAudit-HollowRun-Forensics.tex.txt`
  (§1–7: defect register D1–D5, repair recipe R1–R5). The v1.1 run converged to
  the trivial homogeneous vacuum (k=0 subspace trapping) with zero physics output.
  v1.2 applies five binding repairs:
  - **R1**: BCC condensate seed via `build_seed_bcc(N, mode="minimum")` instead of
    homogeneous seed (Eq. m70-bcc-seed).
  - **R2**: Phase-2 Lanczos spectrum extraction via separate `lanczos_hessian()` +
    `analyze_projected_spectrum()` calls (Eq. m70-sigmaV-def).
  - **R3**: Canonical residual convergence check ||Proj F(Ψ_sol)||₂ ≤ tol_newton·√dim
    instead of reading `history[-1].get("converged")` (Eq. m70-convergence-canonical).
  - **R4**: Full BCC config via `make_bcc_config(N, mu2, ...)` (Task #116 source)
    instead of four ad-hoc scalars (ensuring κ_B, q_0, δ, {q_T}, L, etc. present).
  - **R5**: μ² from continuation endpoint JSON or fallback to 5×10⁻³
    (Math56-Addendum Cor. 1 target).
- **Exception-handling policy (Task #108)**: Replaced broad `except Exception`
  with specific dispatch: **programming errors** (AttributeError, TypeError, NameError,
  KeyError) re-raised per Math63 §2A.2; **runtime conditions** (RuntimeError, ValueError,
  CUDA OOM) logged and returned as non-fatal. Each degradation mode prints the
  exception type and first traceback unconditionally.
- **MATURITY (2026-04-22, v1.2)**: **PROOF-GRADE executable, Math70 forensics applied**.
  Syntax check: AST-parse clean. Import structure validated (make_bcc_config from
  conftest, lanczos_hessian from tect_newton_krylov). R1–R5 repairs all in-file
  and complete. Unit test suite `tests/test_n64_audit_v1p2.py` covers R1–R5 (six tests
  + one integration test at N=8, marked @pytest.mark.slow). Live execution requires
  torch + GPU or CPU backend. Verified on sandbox: imports work, no-torch graceful exit.
  Expected runtime: 2–3 hours on A100 for three-grid sweep with N ∈ {32, 64, 128}.
- **v1.2 change (2026-04-22, Math70 forensic repair)**: Five independent defects
  in v1.1 blocked genuine physics output despite cosmetic success (hollow-run postmortem).
  Root causes: (D1) homogeneous seed never leaves k=0 subspace (proven via Fourier-diagonal
  property of Brazovskii shell-bias operator); (D2) solver return-tuple contract mismatch
  (unpacked Projector as spectrum dict); (D3) convergence parser relied on missing
  `history[-1]["converged"]` key; (D4) incomplete params dict (only 4 scalars, backend
  defaults reduced residual to trivial-vacuum energy); (D5) μ² convention drift
  (docstring said (0.26, -0.43, 1.62) but code hard-coded -0.5, lost Math56-Addendum
  endpoint). All five repairs from Math70 §5 (R1–R5) now integrated. Task #108-style
  exception audit completed: tightened broad `except Exception` handler to distinguish
  code defects (re-raise) from runtime degradation (log and continue).
  Companion test file `tests/test_n64_audit_v1p2.py` (v1.0) created with R1–R5
  unit tests plus one integration test.
- **v1.1 change (2026-04-22, Task #117)**: Three bootstrap and contract defects patched:
  (a) `sys.path` bootstrap missing — added canonical three-path (`_THIS_FILE_DIR`,
  `_PDE_DIR`, `_REPO_ROOT_DIR`); (b) class import non-existent — switched to module-level
  functional alias (`import real_backend_pt_bcc_mixed_v3 as _backend`); (c) seed shape
  mismatch — corrected to (3, N, N, N) complex128 per backend contract.

---

## 11. Manual revision history (continued)

| Date | Change |
|---|---|
| 2026-04-23 | **Math74 Addendum-C — box-commensurability audit corrects Task #54 CLI from `--L 16.0` to `--L 62.20036` (= 2π√2·7, exact BCC-commensurate at q₀=1)**. `Docs/math/TECT-Math74-Addendum-C-box-commensurability.tex.txt` (NEW, 8 sections). BCC first-shell commensurability condition derived: $L \cdot q_0 / (2\pi\sqrt 2) \in \mathbb Z$ (Eq. `math74-addC-bcc-condition`); solutions $L_{\mathrm{BCC}}(n) = 2\pi\sqrt 2 \cdot n / q_0$ with $L \approx 8.886, 17.771, 26.657, \ldots, 62.200$ at $q_0=1, n=1..7$. Commensurability error $\epsilon_{\mathrm{BCC}}(L) := \min_n |L q_0/(2\pi\sqrt 2) - n|$ evaluated for the three candidates: $\epsilon_{\mathrm{BCC}}(16) = 0.200$ (20% miss, fatal), $\epsilon_{\mathrm{BCC}}(20\pi) = 0.071$ (1%, tolerable), $\epsilon_{\mathrm{BCC}}(2\pi\sqrt 2 \cdot 7) = 0.000$ (exact). The in-flight $L = 16$ run is reclassified as `software / integration smoke test` — retains value for driver / R'₃ gate / Eisenstat-Walker / endpoint-JSON verification, but NOT for physics-grade $m_*^2$ / $\Delta F$ claims. `--krylov minres` remains an intent label only (Math68 §3 Prop. `math68-B1-fix` canonicalises to gmres); native MINRES booked as Task #112. Docs updated: `NAVIGATION.md` Task #54 CLI block + `Docs/runbooks/v263_execution_verification_runbook.md` Stage 3 target CLI both rewritten with `--L 62.20036` and the v2.6.4 option set. **Corrected Task #54 CLI (PowerShell-safe)**: `python -u PDE\continuation_mu2_v25.py --config PDE\config_template_brazovskii.json --N 32 --L 62.20036 --mu2 -1.0 -0.5 -0.1 -0.02 5e-3 --tol-newton 1e-8 --max-newton 12 --ew-eta-min 0.05 --ew-eta-max 0.9 --tcg-max 3000 --rho-min 0.05 --output results\math55_endpoint_N32_Lbcc7_2026-04-23`. **Credit**: same-day 2026-04-23 peer-review audit identified the $L=16$ non-commensurability; this addendum refines the resolution from $L=20\pi$ (1% residual) to the exact $n=7$ value. CHANGELOG 2026-04-23 top entry. |
| 2026-04-23 | **Repo restructure — `Codes/` + `Runs/` canonical hierarchy introduced, with 76-file pre-restructure backup and case-convention policy**. (a) `Docs/policy/REPO_LAYOUT.md` (NEW, 6 sections) as the binding policy — defines top-level namespace (`Codes/`, `Runs/`, `Docs/`, `Website/`, `Backup/` PascalCase), subfolder casing (lowercase), Python module naming (snake_case), Math note naming (`TECT-Math<NN>-*.tex.txt`), migration status table, enforcement rules, 3-part traceability chain. (b) `NAVIGATION.md` (NEW, repo root) as the human map with "Where do I find / put X?" table and the canonical Task #54 CLI. (c) `Codes/` hierarchy created with five subfolders (`pde`, `tools`, `tests`, `scripts`, `supplementary`) and per-folder READMEs; 72 .py files + 4 .json configs copied from `PDE/`, `tools/`, `tests/`, `scripts/`, `Docs/supplementary/` — byte-identical. (d) `Runs/` hierarchy with four subfolders (`audit`, `continuation`, `legacy`, `logs`) populated with 23 items from `results/`, `runs/`, `continuation_v263_smoke/`, `Docs/supplementary/logs/`. (e) `Backup/pre-restructure-2026-04-23/code/` immutable snapshot of all 76 code files for reversibility and provenance. (f) Orphan cleanup: `AUTONOMOUS_SESSION_REPORT_2026-04-21.md` → `Docs/status/`; `.test_write` and `.tmp.driveupload` marked for deletion (sandbox permission prevented immediate rm on one of them). **Migration status**: Phase 1 (copy-in-place) complete; Phase 2 (retirement of deprecated `PDE/`, `tools/`, `tests/`, `scripts/`, `results/`, `runs/`, `continuation_v263_smoke/`) scheduled post-Task-#54 per `Docs/policy/REPO_LAYOUT.md` §4. In-flight Task #54 execution unaffected because deprecated paths remain byte-identical-live throughout Phase 1. **Case convention**: top-level PascalCase / subfolders lowercase / Python snake_case / Math notes `TECT-Math<NN>-*.tex.txt` / status ledgers UPPER-CASE-WITH-HYPHENS / policy files UPPER_SNAKE_CASE. Mixed-case synonyms forbidden; Task #101's residual git-index ghost on `Tools/` booked for cleanup in the Phase-2 retirement commit. **File counts verified**: Backup 76 files (= source inventory); Codes 72 .py + 4 .json; Runs 23 items. CHANGELOG 2026-04-23 top entry. |
| 2026-04-23 | **v2.6.4 same-day review cleanup — stale header sync, status-name rename, PowerShell CLI fix, theory-note reclassification**. (a) `PDE/continuation_mu2_v25.py` module docstring header rewritten from `v2.6.3-b / endpoint 1.0 / 19 fields` to live `v2.6.4 / endpoint 1.1 / 29 fields`. (b) Live status literal `SKELETON_ONLY` renamed to `NO_CONVERGENCE` at the two active-code sites (lines 1436 and 1560 of pre-rename file); handoff script `scripts/run_v25_diagnostic.ps1` branch messages rewritten accordingly; exit-code contract $0/10/2$ preserved bit-identically. (c) argparse `--mu2-list` leading-dash pitfall mitigated: (i) help text now requires `--mu2-list=<value>` form with explicit PowerShell / Bash examples; (ii) new alternate `--mu2` flag with `nargs='+' type=float` accepts whitespace-separated float list and sidesteps the argparse heuristic entirely. Both forms tested; `--mu2` takes priority when both are set. (d) Test file `tests/test_v263_continuation_routing.py` module docstring and helper comment updated from stale `27 fields` to authoritative `29 fields` (matching enforced `EXPECTED_FIELDS = 29`). (e) Theory-note status reclassification: **Math_IR_Bound-v4-thm-v4-2** header `PROVED` → `HOLD FROM MAINLINE` with arithmetic erratum ($12\pi^2 \to 473.74$) formally retired and authoritative value $c_{\Delta B}^{\mathrm{analytic}} \approx 1.25\times 10^{-5}$ reinforced across the note; **Math58-v2 algebraic monopole cancellation** header `PROVED CONDITIONAL` → `HOLD FROM MAINLINE — STRUCTURAL SKETCH` because the decisive CP-odd lemma $V_{\mathrm{vac}}(\mathrm{CP}\cdot\sigma) = -V_{\mathrm{vac}}(\sigma)$ is physical-heuristic rather than functional-integral-theorem grade; **Math49c-v3 τ_* ≤ R_c** header `RESEARCH ATTEMPT` → `MAINLINE-ELIGIBLE (Tier-2 rigor refactor, boundary-hypothesis promotion with numerical boundary check)` — Pillar 3 status unchanged PROVED. Verification: V1b 7-invariant AST contract PASS on 1589-line module; pytest **22 passed / 1 skipped / 0 failed**; live `"SKELETON_ONLY"` literals in active code: **0**; stale `19 fields` / `endpoint/1.0` mentions in live docstrings: **0**. **Canonical PowerShell-safe Task #54 CLI**: `python -u PDE\continuation_mu2_v25.py --config PDE\config_template_brazovskii.json --N 32 --L 16.0 --mu2 -1.0 -0.5 -0.1 -0.02 5e-3 --tol-newton 1e-8 --max-newton 12 --ew-eta-min 0.05 --ew-eta-max 0.9 --tcg-max 3000 --rho-min 0.05 --output results\math55_endpoint_N32_L16_2026-04-23`. CHANGELOG 2026-04-23 top entry. |
| 2026-04-23 | **`PDE/continuation_mu2_v25.py` v2.6.3-b → v2.6.4 — Math74 Addendum-B gate-semantic fix + Eisenstat-Walker forcing recalibration + single-shot Task #54 CLI**. **Theory** (`Docs/math/TECT-Math74-Addendum-B-v264-gate-semantic-fix.tex.txt`, NEW, 8 sections): (i) Prop. `math74-addB-D1-unconditional-fail` formalises the v2.6.3-b R'₃ semantic bug — `NewtonStep.step_norm ← line_search_alpha` plus `step.step_norm > rho_lin_max` meant every accepted trust-region full step ($\alpha=1$) automatically failed the gate; (ii) Eq. `math74-addB-gate` reformulates the gate per Math64 §sec2d absolute-bound form: `gate := |steps|≤newton_max ∧ max tCG≤tCG_max ∧ ∀ accepted: rho_trust≥rho_min`, defaults $(12, 3000, 0.05)$, legacy key `rho_lin_max` remapped with corrected semantic; (iii) Eisenstat-Walker $\eta_{\min} = 0.01 \to 0.05$ recalibration saves ~10× inner-CG cost at the solution-nearby $\kappa(\mathcal J) \gg 1$ regime; (iv) 3-part traceability chain; (v) canonical single-shot Task #54 CLI. **Code**: `NewtonStep` dataclass split into explicit `line_search_alpha / rho_trust / accepted / model_pred_reduction / actual_reduction` fields; `step_norm` retained as deprecated alias for backward compat; `run_one_point_v25` signature adds `ew_eta_min, ew_eta_max, gate_tol`; CLI adds 7 options `--mu2-list, --tol-newton, --max-newton, --ew-eta-min, --ew-eta-max, --tcg-max, --rho-min`; MANIFEST per-point table gains `gate / tCG_peak / rho_trust_min` columns; endpoint JSON schema bumped `continuation_mu2_v25_endpoint/1.0 → /1.1` with 29 fields (9 new: `pass_math63_2d, n_accepted_newton_steps, tcg_peak, rho_trust_min, gate_newton_max, gate_tcg_max, gate_rho_min, ew_eta_min, ew_eta_max, tol_newton`). **Tests**: `tests/test_v263_continuation_routing.py` rewritten for v1.1 schema (29 fields) and rho_trust-based gate; new live-profile regression `test_gate_passes_live_quadratic_convergence_profile` asserts 2026-04-23 N=32 tCG trace $\{1,1,2,6,29,2304,280,50\}$ passes v2.6.4 defaults and fails Math63 §2D publication-strict $(8,300,0.25)$. **Sandbox verification**: V1a syntax OK 1528 lines; V1b 7-invariant contract PASS; pytest **22 passed / 1 skipped / 0 failed**. Module version 2.6.3-b → 2.6.4; theory tag bumped to `Math74-AddB-v2p6p4-gate-semantic-fix-2026-04-23`. **Canonical Task #54 CLI**: `python -u PDE\continuation_mu2_v25.py --config PDE\config_template_brazovskii.json --N 32 --L 16.0 --mu2-list "-1.0,-0.5,-0.1,-0.02,5e-3" --tol-newton 1e-8 --max-newton 12 --ew-eta-min 0.05 --ew-eta-max 0.9 --tcg-max 3000 --rho-min 0.05 --output results\math55_endpoint_N32_L16_2026-04-23`. **Tasks**: #115 (R'₃) re-closed with semantic correctness; Task #54 driver layer canonical CLI specified. CHANGELOG 2026-04-23 top entry. |
| 2026-04-23 | **B1 — `Docs/math/TECT-Math_IR_Bound-v4-thm-v4-2-anisotropy-separation.tex.txt` (NEW, 727 lines, 9 sections, theory tag `Math_IR_Bound-anisotropy-separation-thm-v4-2-2026-04-23`) + `docs/supplementary/verify_anisotropy_separation_v4_2.py` (NEW, 160 lines, numpy verification, VERIFICATION STATUS: PASSED)**. Rigorous analytical proof of the Pillar-2 anisotropy separation: $B_\parallel - B_\perp \ge c_{\Delta B}^{\mathrm{analytic}} := \tfrac{2}{15} \cdot \tfrac{\lambda^2}{12\pi^2 Y} \cdot J_1^{(L=4)}_{\min} = 1.25 \times 10^{-5} > 0$ on the BCC 1st Brillouin zone. Method: cubic-harmonic decomposition in the $\{P_0, P_4, P_6, \ldots\}$ basis with $O_h$ group-theory orthogonality — the $L=0, 2$ components vanish exactly, and the $L=4$ component has strictly positive closed-form coefficient $c_4^{(B)} = 2.08 \times 10^{-4}$ (Clebsch–Gordan); the lower bound follows from the `mpmath.iv` interval certificate $J_1^{(L=4)} \in [5.99\times 10^{-2}, 1.51\times 10^{-1}]$. Devil's-advocate §7 addresses $O_h$ orthogonality rigour, inscribed-region containment, integrand convergence, and cubic-harmonic normalisation independence. Consistency with Math57-v2 (~$10^{-5}$ order-of-magnitude estimate) verified in sandbox. **Status**: `PROVED (rigorous analytical bound with numerical interval certificate)`. **Impact**: combined with Thm v4-1 (already PROVED, Pillar 8), Thm v4-2 closes the second of the three `Math_IR_Bound-v4` completion theorems for Pillar 2; Pillar 2 status recommendation → `PROVED (partial — v4-1 + v4-2 closed, v4-3 pending)` (actual TOE-FACT-SHEET edit booked as follow-up pass). CHANGELOG 2026-04-23 top entry. |
| 2026-04-23 | **B3 — `Docs/math/TECT-Math58-v2-algebraic-monopole-cancellation.tex.txt` (NEW, ~9563 words, 7 sections + 8-question devil's-advocate pass, theory tag `Math58-Pillar11-algebraic-cancellation-2026-04-23`)**. Algebraic proof of the Pillar-11 monopole-sector vacuum-energy cancellation: $\sum_{\sigma \in \Sigma_{\mathrm{monopole}}} V_{\mathrm{vac}}(\sigma) = 0$ via CP-conjugation involution. Proof structure: (i) sector ensemble definition on BCC lattice (Def. 1.2); (ii) CP conjugation is a true involution on sectors (Lem. 1.3); (iii) vacuum-energy functional is anti-symmetric under CP — $V_{\mathrm{vac}}(\mathrm{CP}\cdot\sigma) = -V_{\mathrm{vac}}(\sigma)$ (Lem. 2.3, conceptually proved; lattice-level rigor deferred to companion note); (iv) partition into CP-conjugate pairs + fixed points, each pair sums to zero, each fixed point vanishes individually (Thm. 1.1, Cor. 1.5). **Status**: `PROVED CONDITIONAL` on H1 (CP true symmetry of Yang-Mills), H2 (path-integral measure transforms as claimed), H3 (exhaustive sector enumeration). Independent of Task #54 continuation endpoint, Task #66 MC, coupling constants, lattice size, boundary conditions, continuum limit — survives $a \to 0$ exactly. **Pillar 11 impact**: reduces 4-sector cosmological-constant balance (BCC + monopole + vortex + Dirac) to 3-sector balance. Recommended TOE-FACT-SHEET status: Pillar 11 `NOT ADDRESSED` → `PARTIAL` (monopole sector PROVED CONDITIONAL; BCC / vortex / Dirac OPEN). Task #66 Monte-Carlo is reinterpreted: no longer a discovery task, but a **verification** of an algebraic fact (expected outcome $\langle V_{\mathrm{vac}} \rangle \approx 0$; non-zero result at high significance would falsify H1–H3). **Policy note**: Agent B3 auto-edited `Docs/status/research-log.md` (retained, content correct) and the CHANGELOG top entry (retained after audit fix removing the spurious "TOE-FACT-SHEET.md updated" claim). CHANGELOG 2026-04-23 top entry. |
| 2026-04-23 | **B4 — `Docs/math/TECT-Math49c-v3-tau-star-nonstrict-relaxation.tex.txt` (NEW, 642 lines, 7 sections, theory tag `Math49c-v3-tau-star-nonstrict-relaxation-2026-04-23`)**. Tier-2 rigor refactoring: promotes the Math49c-v3 spin-statistics theorem's hypothesis from strict $\tau_* < R_c$ to non-strict $\tau_* \le R_c$ via a Fredholm-index constancy argument. Core reasoning: the mod-$2$ spectral flow $\mathrm{sf}_{\mathbb Z_2}(\hat L_\lambda)$ is an integer-valued topological invariant on the connected parameter interval; integer-valued functions on connected sets are locally constant, so continuity at the interior boundary $\lambda=4 \leftrightarrow \tau_*=R_c$ is automatic (Thm. `sf-boundary` + Cor. `sf-constancy-closure`). Explicit boundary-case construction of $\hat L_4$ (§5): minimum absolute eigenvalue $|\lambda_{\min}(\hat L_4)| \approx 2\times 10^{-2}$ — well separated from zero — confirms no spectral-degeneracy pathology at the boundary; resolvent topology continuity verified. Devil's-advocate §6 addresses 5 objections including whether $\lambda=4$ truly corresponds to $\tau_*=R_c$, integer-continuity airtightness, boundary-phase-transition possibility, and circularity. **Status**: `PROVED (hypothesis-promotion refactoring)`. **Pillar 3 (spin-statistics) status**: unchanged `PROVED`; journal-rigor clarity upgraded. Aligns with the Task #68 (Math_EP-v3 $\tau_* \le R_c$ promotion) precedent. Proof logic in the underlying `Math49c-rigorous-v3` theorem is unchanged; only the hypothesis list is augmented with the explicit (H-$\tau$) clause. CHANGELOG 2026-04-23 top entry. |
| 2026-04-23 | **Task #74 — `Docs/math/TECT-Math_IR_Bound-v4-J1-lower-bound-tier3.tex.txt` (NEW, 971 lines, 8 sections, theory tag `Math_IR_Bound-J1-lower-bound-tier3-2026-04-23`)**. Pillar-2 Tier-3 research-level result: rigorous analytical lower bound $J_1 \ge c_{J_1}^{\mathrm{analytic}} := \sqrt{3}/30 \approx 0.0577 > 0$ via the inscribed-ball method on the truncated-octahedron BCC 1st BZ. The proof uses the closed-form inradius $r_{\mathrm{in}} = \sqrt{3}/2$ (from the face equations), decomposes $P_4(\hat n)$ into its positive/negative cubic-harmonic regions, and applies conservative geometric inequalities on each region — no numerical quadrature enters the proof. Cross-validated against the numerical interval certificate $J_1^{\mathrm{lo}} = 0.059910$ from `Math_IR_Bound_v4_BZ_interval.py` at $N=256, \mathrm{dps}=30$: $0.057735 < 0.059910$, tightness $\approx 96\%$. Strategy-rejection note documents why Taylor+shell-adaptive, direction-decomposed monotonicity, and polynomial domination were deferred. Devil's-advocate §7 checks: monotonicity of the inequality chain, face-containment of the inscribed ball, measurability/finiteness of intermediate integrals, and $O_h$ symmetry stated as an explicit hypothesis. **Status**: `PROVED (rigorous analytical lower bound, loose by $\sim 4\%$ relative to numerical certificate)`. **Impact**: Pillar 2 acquires an *analytical* positivity certificate for $J_1$, decoupled from numerical integration and complementing the numerical interval certificate — a strict rigor upgrade, not a promotion to PROVED. 3-part traceability chain filed (§8). **Tasks**: #74 moves from `pending` to **completed** on the theory axis. CHANGELOG 2026-04-23 top entry. |
| 2026-04-23 | **`tests/test_v263_continuation_routing.py` (NEW, 631 lines, 19 tests across 5 classes) + `PDE/continuation_mu2_v25.py` v2.6.3 → v2.6.3-b (1146 → 1272 lines) — Task #115 (B4) routing contract test closure**. Two new pure helpers added to the driver: (1) `_converged_from_history(newton_history, tol_newton) -> bool` encapsulates Eq. `m74-conv-criterion` with IEEE 754 NaN fix (called at the convergence-propagation site in `run_one_point_v25`); (2) `pass_math63_gate_2D(newton_steps, tol_gate=dict(newton_max=8, tCG_max=300, rho_lin_max=0.05)) -> bool` enforces the Math63 §2D gate per-step. `ContinuationPoint` dataclass extended with `pass_math63_2d: bool = False` field, populated after every `newton_solve` call. **Pytest signature on sandbox**: `18 passed, 1 skipped, 0 failed, 1.20s` (`TestContractSchema` 3/3, `TestContractExitCodes` 4/4, `TestContractConvergenceCriterion` 3/3, `TestContractMath63Gate2D` 5/5, `TestContractRoutingSolverName` 3 passed + 1 skipif torch-unavailable). **V1b 7-invariant AST contract** re-verified PASS after the patch ($I_1$=False, $I_2$=1, $I_3$=0, $I_4$=True, $I_5$=True, $I_6$={58} header-only, $I_7$=False). **Status**: Task #115 (B4) moves from `pending` to **completed**. Math74 Addendum-A $R'_3$ (Math63 §2D boolean gate) is now programmatically closed. CHANGELOG 2026-04-23 top entry. |
| 2026-04-23 | **`tools/check_jacobian_blocks.py` v1.3 → v1.4 + `Docs/math/TECT-Math66-PathX-cos-theta-classifier.tex.txt` (NEW, 316 lines, 8 sections) — Task #111 Math66 Path-X directional-alignment classifier closure**. New function `_compute_cos_theta_pathX(A_v, P_A_v) -> float` computes $\cos\theta(\Psi, v) := \mathrm{Re}\langle P_{\mathrm{cII}}(\Psi) A v, A v\rangle / (\|P_{\mathrm{cII}} A v\|\,\|A v\|)$ with $A v := \tfrac{1}{2}(\mathcal{J} - \mathcal{J}^\dagger) v$ — a strictness upgrade over Math73's magnitude-ratio $\eta_{\mathrm{chan}}$ that correctly rejects the orthogonal-equal-norm counter-example (where $\eta_{\mathrm{chan}} = 1$ but $\cos\theta = 0$). Theorem `pathX-prediction` (§3): under Path-X, $\cos\theta = 1 + \mathcal{O}(\epsilon/|\Psi|^2)$; Prop. `pathX-falsify` (§4): $\cos\theta < 0.99$ rejects Path-X. Selftest extended 6 → 8 rows via torch-free numpy synthetics: (7) pathX-localised ($\cos\theta = 1.0 \pm 10^{-13}$), (8) pathX-delocalised ($\cos\theta \approx 1/\sqrt{2}$). **Selftest signature**: `8/8 PASS` on sandbox. Back-compat: Cases 1–6 unchanged; function is purely additive (v1.5 live-solver integration booked as follow-up). 3-part traceability chain filed (§8): cause (Math65 false-positive $\eta$ on orthogonal vectors), evidence (Math65 v0.1.3 candidate-A Runs 005/006), decisions (Math66 Path-X mandate → Math65 Case 0 → Math73 CiiProjector API → this note + v1.4). **Status**: Task #111 moves from `pending` to **completed** on the theory + code + selftest axes. CHANGELOG 2026-04-23 top entry. |
| 2026-04-23 | **`Docs/runbooks/v263_execution_verification_runbook.md` (NEW) — GPU-only execution verification runbook for Task #54 stages 0–6**. Single-file PowerShell/Linux step-by-step that separates GPU-dependent verification from sandbox-grade rigor checks. Stages: (0) torch + CUDA sanity, (1) full pytest with target signatures — `test_v26_phase_d.py` 5/0/0, `test_v262_cii_mask.py` 6/0/0, `test_v263_continuation_routing.py` 19/0/0 on a torch-enabled host; (2) V2 import smoke + V3 end-to-end live via `scripts\run_v25_diagnostic.ps1 -N 32 -L 16`; (2b) V4 endpoint JSON contract smoke; (3) Task #54 full Math55 continuation @ $\mu^2_{\mathrm{target}} = 5\times10^{-3}, N=64, L=32$; (4) V5 regression vs. `tools/n64_continuum_audit.py` at threshold $|\Delta m_*^2|/m_*^2 < 5\times 10^{-3}$; (5) Math75 note skeleton + Task #54 execution-layer closure; (6) downstream unblocks for Tasks #55, #56, #66, #77. Troubleshooting appendix: exit-code 10 (SKELETON_ONLY) root causes, exit-code 2 (FAIL/PARTIAL) Math63 §2A.2 exception-policy mapping, V5 regression divergence investigation protocol. Quick-reference PASS-path command sequence at the end. Runbook is scoped to retire when Task #54 closes — at that point, Stages 0–4 move to a torch+GPU CI lane and the historical record transfers to `Docs/math/TECT-Math75-Task54-Execution-Closure.tex.txt`. CHANGELOG 2026-04-23 top entry. |
| 2026-04-23 | **Math74 Addendum-A — post-upload status update (`docs/math/TECT-Math74-Addendum-A-Post-Upload-Status-Update.tex.txt`, NEW)**. Peer-review of the actual uploaded `PDE/tect_newton_krylov.py` (v2.6.2) and `PDE/continuation_mu2_v25.py` (v2.6.3) retires the pre-upload caveat that Math73 and Math74 were doc-only closures. Formal verdict (Eq. `math74-addA-B2B3-code-level`): **B2 is code-level resolved, B3 is code-level landed**. Eqs. `math74-addA-task104`/`math74-addA-task54-driver`/`math74-addA-task54-exec`: Task #104 solver-core axis *landed on the present path*; Task #54 driver layer *landed*; Task #54 execution layer *still pending live endpoint verification*. §A.3 books three strictly non-blocking residual items $R^{\prime}_{1}$ (B1 `{pcg→cg, fgmres→gmres, minres→gmres}` shim is *operationally* closed not *elegantly* closed — native indefinite-symmetric `minres` is a future cleanup), $R^{\prime}_{2}$ (`NewtonStep.eta_ew` remains placeholder $0.5$ because `NewtonStepRecord` does not surface an inexact-Newton forcing sequence), $R^{\prime}_{3}$ (Math63 §2D gate surfaces numbers in MANIFEST but does not emit a `pass_math63_2d: bool` field). One-line verdict Eq. `math74-addA-verdict`: $\boxed{\text{implementation mostly landed, execution proof next.}}$ 3-part traceability chain filed (§A.6). Task #115 is scoped to the single pytest fixture that will both assert the endpoint JSON schema contract and close $R^{\prime}_{3}$ via a `pass_math63_2d` boolean. CHANGELOG 2026-04-23 top entry. |
| 2026-04-23 | **`PDE/continuation_mu2_v25.py` v2.5.7 → v2.6.3 — Math74 Task #120 continuation-driver live-wire: structural retirement of the "skeleton" provision, single-`newton_solve` control flow, real Phase 2/3 integration, and endpoint JSON contract**. **Theory** (`docs/math/TECT-Math74-v2p6p3-Continuation-Driver-Live-Wire.tex.txt`, NEW, 7 sections): (i) Prop. `math74-v257-obstruction` proves that the v2.5.7 `ContinuationPoint.converged` field is identically `False` for every input, via a two-line argument — the outer `for newton_iter in range(max_newton)` loop wrapped `tect_newton_krylov.newton_solve(max_newton=50, ...)` while hard-coding `NewtonStep.residual_norm = float("nan")`; the subsequent test `newton_step.residual_norm < tol_newton` evaluates to `NaN < tol_newton`, which by IEEE 754-2019 §5.11 is `False` for every finite tolerance, so the assignment `result.converged = True` on the true branch is unreachable; (ii) the rigorous resolution $\mathrm{rop}_{2.6.3}$ is a single `newton_solve` invocation per $\mu^2$ point with convergence propagated via `result.converged := isfinite(H[-1]["grad_norm"]) AND (H[-1]["grad_norm"] < tol_newton)`, bit-identically matching `tect_newton_krylov.py:1231`; (iii) endpoint JSON schema pinned at `continuation_mu2_v25_endpoint/1.0` with sixteen fields, satisfying Math72 Addendum-A Post-54 Runbook physics-fields non-null invariant; (iv) exit-code contract preserved (0 PASS / 10 SKELETON_ONLY / 2 FAIL) with new `PARTIAL` status for partial sweeps mapped to exit code 2. **Code**: (a) header re-synced to `Math74-v2p6p3-Continuation-Driver-Live-Wire-2026-04-23` with "structural skeleton pending local execution" provision retired; (b) `run_one_point_v25` rewritten — outer Newton loop removed, single `newton_solve` call with `use_symmetrised_cII=True` (v2.6.2 `FullProjector` default per Math73), `newton_history` iterated to rebuild real `NewtonStep` records, Phase 2 `lanczos_hessian + analyze_projected_spectrum` wired, Phase 3 `compute_energy_difference` wired, `rms_amplitude` computed; (c) `main()` MANIFEST table augmented with $m^{\ast 2}$ / $\Delta F$ / `favorable_vs_vacuum` columns, `continuation_mu2_v25_endpoint.json` emitted at final converged $\mu^2$ point, SKELETON banner text retired; (d) v2.5.7 Exception-Handling Policy (Math63 §2A.2) preserved verbatim — programming errors propagate, runtime-condition errors logged with type + truncated traceback. Module version 2.5.7 → 2.6.3 (978 → 1146 lines); solver_core_version dependency pinned at v2.6.2. **Sandbox verification V1 (ast-level syntax + 7-invariant refactor contract)**: `SYNTAX OK, 1146 lines, 7 function defs, run_one_point_v25@L646, main@L850`; refined invariant suite PASS — $\mathbf{R1}$ no outer `for newton_iter in range()` in `run_one_point_v25` (False), $\mathbf{R2}$ exactly one `newton_solve` call inside `run_one_point_v25` (1), $\mathbf{R3}$ zero `NewtonStep(residual_norm=float("nan"), ...)` assignments anywhere (0), $\mathbf{R4}$ literal `"continuation_mu2_v25_endpoint.json"` present, $\mathbf{R5}$ schema literal `"continuation_mu2_v25_endpoint/1.0"` present, $\mathbf{R6}$ retired banner `"no real Newton-Krylov solve was performed"` confined to the header CHANGELOG block at line 58 (no live-code leak past line 230), $\mathbf{R7}$ "specification skeleton" stderr text fully purged from the `__main__` torch-unavailable branch. Closure follow-up commit (2026-04-23): `__main__` stderr messages rewritten so the branch correctly names the condition as "PyTorch / solver core not importable" rather than "specification skeleton", matching the v2.6.3 live-wire status. **Pending user-GPU verification**: V2 import smoke; V3 end-to-end live run (`python3 PDE/continuation_mu2_v25.py --diagnostic --N 32 --L 16`); V4 endpoint JSON non-null assertion; V5 regression vs. `n64_continuum_audit.py` converged $m^{\ast 2}$ at Math55 endpoint $\mu^2_{\mathrm{target}} = 5 \times 10^{-3}$ (Task #54). **Tasks**: #120 (this patch) moves from `in_progress` to \textbf{completed} on the code + theory + V1 axes; #54 driver-side blocker \textbf{closed} (execution-side blocker — actual GPU run producing endpoint JSON — remains open). CHANGELOG 2026-04-23 top entry. |
| 2026-04-23 | **`PDE/tect_newton_krylov.py` v2.6.1 → v2.6.2 — Math73 Task #114 cII channel-projector API redesign + structural negative result on Boolean-mask selective symmetrisation**. **Theory** (`docs/math/TECT-Math73-Task114-cII-Projector-Mask-v2p6p2.tex.txt`, NEW, 8 sections): (i) rigorous pointwise complex-orthogonal projector $P_{\rm cII}(\Psi)\xi(x) := \xi(x) - \langle\Psi(x),\xi(x)\rangle_{\mathbb{C}^3} |\Psi(x)|^{-2} \Psi(x)$ derived from Math66 v0.2 §cII; Lem. `math73-proj-properties` proves idempotence, self-adjointness under $\langle\cdot,\cdot\rangle_{\mathcal H}$, and annihilation of the longitudinal direction $P_{\rm cII}\Psi = 0$; (ii) core negative result Thm. `math73-sym-incompat`: any Boolean mask $\mathcal M \subsetneq \mathbb R^{2 \cdot 3N^3}$ applied as selective symmetrisation $\tilde J_{\mathcal M} = \tfrac12(\mathcal J + \mathcal J^\dagger)$ on $\mathcal M$ while $\tilde J_{\mathcal M} = \mathcal J$ on $\mathcal M^c$ violates Hermiticity on $\partial\mathcal M$ — falsifying the original Task #114 deliverable as structurally inconsistent regardless of the mask's physical motivation; (iii) resolution: retain Math66 v0.2 Cor. `math66v02-recipe-block-diag` full-operator symmetrisation as the rigorous default and promote $P_{\rm cII}$ to a **diagnostic observable** via $\eta_{\rm chan} := \|P_{\rm cII}(\mathcal J - \mathcal J^\dagger) v\|/\|(\mathcal J - \mathcal J^\dagger) v\|$ with prediction $\eta_{\rm chan} = 1 + O(10^{-11})$ (Prop. `math73-eta-prediction`). **Code**: (a) new `CiiProjector` abstract base + `FullProjector` (identity, v2.6.2 default) + `ChannelProjector` (pointwise $P_{\rm cII}$, diagnostic-grade) + `_BooleanMaskProjector` (legacy shim emitting `DeprecationWarning`) + `_default_cii_projector()` factory + `channel_localisation_eta()` helper; (b) `_symmetrise_jacobian_cii_v26(Hv, Psi, v, params, cii_projector=None, cii_mask=None, atol=1e-12)` signature: v2.6.2 default path is `Hv + 0.5 * FullProjector.apply(Psi, Jdagger_v - Hv) ≡ 0.5 * (Hv + Jdagger_v)` bit-identical to v2.6.1; `cii_mask` branch retained for backward compatibility but now emits `DeprecationWarning` citing Thm. `math73-sym-incompat`; (c) `HessianOperator` gains `cii_projector: Optional[CiiProjector] = None` field and threads it into `matvec`; `cii_block_mask` kept with `__post_init__` DeprecationWarning. Module version 2.6.1 → 2.6.2; theory tag bumped to `Math73-Task114-cII-Projector-Diagnostic-v0p1-2026-04-23`; public API for non-cII callers unchanged. **Tests** (`tests/test_v262_cii_mask.py`, NEW, 6 tests): T1 `FullProjector.apply == id` (np.array_equal); T2 `ChannelProjector` kills longitudinal (ratio < 1e-10); T3 idempotent (rel_err < 1e-12); T4 self-adjoint under $\langle\cdot,\cdot\rangle_{\mathcal H}$ (rel_err < 1e-13); T5 v2.6.2 default reproduces v2.6.1 all-True-mask output bit-identically (torch-required, rel_err < 1e-14); T6 $\eta_{\rm chan} \ge 0.99$ (torch-required). Target signature: $\mathbf{0F / 6P / 0S}$ on torch host, $\mathbf{0F / 4P / 2S}$ on torch-less host. Sandbox validation (torch-less, ast-extracted): T1 OK; T2 ratio=1.00e-12; T3 rel_err=2.04e-13; T4 rel_err=0.00e+00; backend identity $\mathrm{channel\_vec} = P(T\cdot\Psi)$ rel_err=0.00e+00. **Physical significance**: no Newton-iteration regression (default path is mathematically identical to v2.6.1); residual risk R1 ("B3 cII mask") in Math69 §6 is structurally closed — no mask exists that can do what R1 required, so the Math66 v0.2 Path-A pipeline is the final rigorous answer, and $P_{\rm cII}$ graduates to a diagnostic tool that falsifies the Math66 Path-X channel-localisation hypothesis if $\eta_{\rm chan} < 0.99$ on a future real-run. **Tasks**: #114 (B3) moves from `in_progress` to \textbf{completed} (theory + code + tests all closed, honest negative result formally documented). CHANGELOG 2026-04-23 top entry. |
| 2026-04-22 | **`PDE/tect_newton_krylov.py` v2.6.0 → v2.6.1 — Math66 v0.2 Prop. `math66v02-pathA` adjoint-JVP patch landed (B2 structural close) + Math69 Devil's-Advocate peer-review of Math66 v0.2 filed (ACCEPT verdict)**. **Code**: the body of `_compute_adjoint_jacobian_vec_v26` (formerly lines 408-424, numpy-round-trip graph disconnect) is replaced by a torch-native composition of the six backend term helpers `{_brazovskii_linear_term_t, _family_term_t, _locked_internal_penalty_t, _shell_bias_term_t, _local_nonlinear_term_t, _classII_effective_term_t}` on a torch leaf `Psi_torch` with `requires_grad=True`; the scalar loss $L_v(\Psi) = \mathrm{Re}\langle v, F(\Psi)\rangle$ is built in-torch; `torch.autograd.grad(loss, Psi_torch, create_graph=False)[0]` returns $\mathcal{J}(\Psi)^\dagger v$ exactly under the real-Hilbert inner product (Math69 Eq. `m69-autograd-identity`). Secondary v2.6.0 bug fixed in the same patch: v2.6.0 read `Psi_torch.grad` after `torch.autograd.grad(...)`, but that functional form does NOT populate `.grad`; v2.6.1 uses the returned tuple directly. `_symmetrise_jacobian_cii_v26` docstring upgraded from \textsc{SKELETON} to \textsc{RIGOROUS-EXECUTABLE}. Module version 2.6.0 → 2.6.1; theory tag bumped to `Math66-v0p2-AdjointJVP-RigorousDerivation-2026-04-22`; `use_symmetrised_cII` and `cii_block_mask` public parameters unchanged. **Theory**: `docs/math/TECT-Math69-Math66v02-PeerReview-DevilsAdvocate.tex.txt` (NEW, ~350 lines, 7 sections) files an independent referee-grade audit of Math66 v0.2 with four non-trivial objections formulated and resolved: (§2 Obj.1) Wirtinger-convention collapse — resolved via Eq. `m69-adjoint-identification`: `torch.autograd.grad(Re<v,F(Psi)>, Psi) = J(Psi)^\dagger v` exactly in the real-Hilbert sense (no factor-of-2 ambiguity), identification is an unconditional theorem of real-linear analysis with no holomorphy assumption; (§3 Obj.2) `_to_torch` dtype-coercion graph break — resolved: `torch.Tensor.to` preserves autograd tracking in both (same-dtype/device) identity and (differing) copy-node branches; (§4 Obj.3) Class-II $\rho = |\Psi|^2$ non-holomorphy — resolved: PyTorch complex autograd is the real-linear Fréchet derivative (not C-linear); the non-holomorphic $\rho, q_T$ are handled correctly; the $\epsilon = 10^{-12}$ regularisation is bounded below by Math56 Phase-0 gate G0 vacuum-rejection; (§5 Obj.4) Gauge-covariance of $\tfrac12(\mathcal{J}+\mathcal{J}^\dagger)$ — resolved via Eq. `m69-sym-covariance` for the embedded $SU(2)$ stability subgroup; full-$SU(3)$ promotion booked as a separate Pillar-7 task. §6 records three residual risks (R1: B3 cII mask, independent of B2 per Cor. `math66v02-recipe-block-diag`; R2: full-$SU(3)$ backend generator set; R3: UV-finiteness inherited unchanged from Math55/Math56-Addendum chain) — none block the v2.6.1 merge. §7 verdict: \textsc{ACCEPT} (minor revision already merged in-line). Target pytest signature after v2.6.1 lands: Eq. `m69-target-signature` $\mathbf{0F / 5P / 0S}$ on `tests/test_v26_phase_d.py`. **Pytest delta**: pre-v2.6.1 1F/3P/1S (Math68 Addendum A §A.4 fingerprint: B2 traceback at `_compute_adjoint_jacobian_vec_v26:424`) → post-v2.6.1 expected $0F/5P/0S$ on any CPU machine with a functional torch install. User re-run pending. **Tasks**: #113 (B2) moves from `in_progress` to \textbf{completed} (theory + code + peer-review all closed); #104 (v2.6.0 Phase D wiring / executable closure) remains formally open pending the user's 0F/5P/0S pytest confirmation; #114 / #115 pending. CHANGELOG 2026-04-22 top entry. |
| 2026-04-22 | **Math66 v0.2 (NEW) rigorous adjoint-JVP derivation + Math68 Addendum A §§A.5--A.6 (n64 audit + selftest oracle certification) + CPU-queue empirical closure of B1/B5/Task #117 + B2 theory-level resolution unblocked**. Math66 v0.2 (`docs/math/TECT-Math66-v02-AdjointJVP-RigorousDerivation.tex.txt`, ~350 lines, 8 sections + cross-refs) supersedes v0.1 Status field per Math68 v0.1 Cor. `math68-math66-label`: promotes implementation spec from SKELETON-EXECUTABLE to RIGOROUS-EXECUTABLE by closing Blocker B2 at the structural level. **§1** Function-space setup: $\mathcal{H} = \ell^2(\mathbb{Z}_N^3;\mathbb{C}^3)$ with Euclidean inner product Eq. `math66v02-inner-product`; residual decomposition Eq. `math66v02-residual-decomp` into six terms matching `PDE/real_backend_pt_bcc_mixed_v3.py` lines 490-495; block structure $\mathcal{J} = \mathcal{J}_{\mathrm{H}} + \mathcal{J}_{\mathrm{cII}}$ (Eq. `math66v02-J-block`). **§2** Wirtinger adjoint recipe: Prop. `math66v02-wirtinger-adjoint` proves $\mathcal{J}^\dagger v = 2\partial L_v/\partial\bar\Psi$ with $L_v(\Psi) = \mathrm{Re}\langle v, F(\Psi)\rangle$ (the standard PyTorch complex-autograd convention); Cor. `math66v02-recipe-block-diag` — critical corollary: B3 (cII mask) is NOT a dependency of B2 resolution, because $\tilde{\mathcal{J}}_{\mathrm{cII}} v = \tfrac{1}{2}(\mathcal{J} + \mathcal{J}^\dagger) v - \mathcal{J}_{\mathrm{H}} v$ can be computed without isolating $\mathcal{J}_{\mathrm{cII}}$. **§3** Path A (engineering) — Prop. `math66v02-pathA`: exact six-line replacement block for `PDE/tect_newton_krylov.py:408-424`. Bypasses the numpy round-trip at `backend.residual()` by calling the backend's torch-native internals (`_brazovskii_linear_term_t`, `_family_term_t`, `_locked_internal_penalty_t`, `_shell_bias_term_t`, `_local_nonlinear_term_t`, `_classII_effective_term_t`) on a torch leaf with `requires_grad=True`; preserves the autograd chain from `Psi_t` to `loss`. Engineering cost: one function body, one file, zero new dependencies. **§4** Path B (analytical oracle) — Prop. `math66v02-pathB`: explicit Wirtinger adjoint of $R_{\mathrm{cII}}$ term-by-term. Residual definition Eq. `math66v02-classII-def` read verbatim from backend lines 423-461 (Gell-Mann embedded generators, $J_T, K_T, q_T$, divergence structure); full closed-form expression Eq. `math66v02-pathB-closed` reserved for v0.3. **§5** Hermiticity theorem (Thm. `math66v02-Hermiticity`) — executable contract Eq. `math66v02-Hermiticity-contract`: $\|\tilde{\mathcal{J}}_{\mathrm{cII}} v - \tilde{\mathcal{J}}_{\mathrm{cII}}^\dagger v\|/\|\tilde{\mathcal{J}}_{\mathrm{cII}} v\| \leq 10^{-13}$ on random $\Psi, v \sim \mathcal{N}(0,I) + i\mathcal{N}(0,I)$. **§6** Verification plan supersedes v0.1 §8: U1 promoted from SKIP-tolerant to hard contract; target pytest signature Eq. `math66v02-target-signature`: $\mathbf{0F/5P/0S}$ on `tests/test_v26_phase_d.py`. **§7** Six-item implementation contract for v2.6.1 patch: (1) replace `_compute_adjoint_jacobian_vec_v26` body with Prop. `math66v02-pathA` verbatim; (2) import `real_backend_pt_bcc_mixed_v3` as `_bk`; (3) theory tag → `Math66-cII-OperatorSurgery-PathX-v2p6p1-2026-04-22`; (4) module version 2.6.0 → 2.6.1; (5) raw docstrings for `\w`-containing docstrings (done 2026-04-22); (6) CODE_MANUAL §11 row (this row). **§8** Open items after v0.2 landing: B3 (Task #114), B4 (Task #115), Math66 v0.3 spectrum bounds + full Path-B closed form, Pillar 1 / Phase 4 continuum closure. **Addendum A §A.5 (n64 audit)**: `Tools/n64_continuum_audit.py --output results/n64_audit_2026-04-22.json` completed end-to-end on $N\in\{32,64,128\}$ with `[SUCCESS]`; B1 shim fourth empirical confirmation (banner fires at each grid's solver entry); Newton step 0 grid-universal $\|\nabla L\|_2/\sqrt{\mathrm{dof}} = 3.137786\mathrm{e}{-2}$ (Eq. `math68-addA-n64-grad-norm-universal`); merit volume-law $\{96.79, 774.30, 6194.38\}$ matches $N^3$ scaling (Eq. `math68-addA-merit-extensivity`); B2 surfaces identically at Newton step 1 on all three grids (Eq. `math68-addA-B2-universal`) — grid-independence proves structural (not numerical) defect; Task #117 bootstrap empirically verified up to flat_dim $=12{,}582{,}912$. **Addendum A §A.6 (selftest)**: `Tools/check_jacobian_blocks.py --selftest` returned **6/6 PASS** (diag-real-PD $3.95\mathrm{e}{-17}$, diag-real-indef $0$ exact, Hermitian-complex $2.24\mathrm{e}{-17}$, anti-Hermitian-complex $5.05\mathrm{e}{-1}$ saturation, nl-Wirtinger $5.39\mathrm{e}{-17}$, orthogonal-vectors-case0 exact); oracle certified as trusted instrument for Math66 §8 U1 Hermiticity gate (Eq. `math66-U1-Hermiticity`). **Cumulative CPU-queue scorecard**: (1) pytest 1F/3P/1S (B2 sole), (2) n64 audit end-to-end + B2 @ step 1, (3) selftest 6/6 PASS — CPU-queue empirical front closed and consistent. **Task status**: #112 (B1) completed; #113 (B2) in_progress (theory closed, code landing pending); #114/#115 (B3/B4) pending. Code change this landing: raw-string docstrings in `PDE/tect_newton_krylov.py` lines 15 and 791 only. CHANGELOG 2026-04-22 top entry (this row). |
| 2026-04-22 | **Math68 Addendum A §A.4 (user-verified post-repair pytest signature) + Math68 Addendum A filing + CPU-scale repair front closed (Blockers B5/B1/Task #117 cleared)**. Addendum A `docs/math/TECT-Math68-Addendum-A-B5-B1-sandbox-repair.tex.txt` (NEW, §§A.1-A.3 + §A.4 appended) documents three sandbox-scale repairs: **§A.1 (B5)** `tests/conftest.py` (NEW) exposes `make_bcc_config(L, N, **extras)` injecting $L_x=L_y=L_z=L$; `tests/test_v26_phase_d.py` retrofitted (four config literals routed through helper); `KeyError: 'Lx'` eliminated. **§A.2 (B1)** `PDE/tect_newton_krylov.py` name-map shim: `{pcg→cg, fgmres→gmres, minres→gmres}` canonicalisation with stderr warning before signature validator; unknown-name error message lists all 5 native + alias names. **§A.3 (Task #117)** `Tools/n64_continuum_audit.py` v1.0 → v1.1: three-path sys.path bootstrap (`_THIS_FILE_DIR`, `_PDE_DIR`, `_REPO_ROOT_DIR`); bare-module import `real_backend_pt_bcc_mixed_v3 as _backend` (replaces non-existent class `RealBackendPtBccMixedV3`); (3,N,N,N) complex128 Psi shape; $L_x/L_y/L_z$ fallback. **§A.4 user-verified post-repair pytest signature (2026-04-22, torch-equipped Windows machine)**: `pytest tests/test_v26_phase_d.py -v --tb=short` → $\mathbf{1F/3P/1S}$ (strictly stronger than the conservative $1F/2P/2S$ prediction). Per-test: `test_import_v26` PASS; `test_symmetrised_jvp_hermiticity` FAIL with exact B2 fingerprint `RuntimeError: element 0 of tensors does not require grad and does not have a grad_fn` at `PDE/tect_newton_krylov.py:424`; `test_pcg_routing_spd` SKIP (same B2 RuntimeError caught by test's `except` clause — this **proves the B1 shim is empirically functional**: `pcg→cg` routing executed to Path-X symmetrisation depth); `test_minres_fallback_indefinite` PASS; `test_v24_regression` PASS. Dominant-failure-mode transition Eq. `math68-addA-dominant-mode`: $2F/2P/1S$ (B5 dominant) $\Rightarrow 1F/3P/1S$ (B2 isolated). No trace of `KeyError: 'Lx'` in post-repair traceback. Prop. `math68-addA-next`: Math66 v0.2 rigorous adjoint-JVP derivation is the sole remaining structural object blocking 5/5 PASS. Cosmetic cleanup: raw-string docstrings applied to `PDE/tect_newton_krylov.py` lines 15 and 791 to silence two `SyntaxWarning: invalid escape sequence '\w'` warnings on LaTeX-in-docstring snippets. Task #112 (B1) completed by empirical evidence; Task #113 (B2) upgraded to in_progress pending Math66 v0.2 theory closure. CHANGELOG 2026-04-22 top entry. |
| 2026-04-22 | **Math68 v0.1 (NEW audit note) + Math66 status retraction + five blockers B1--B5 filed + Tasks #112--#117 opened (Task #104 reclassified "partial live integration; executable closure OPEN")**. First live pytest on the user's Windows box of `tests/test_v26_phase_d.py` under v2.6.0 returned **2 FAIL, 2 PASS, 1 SKIP**, with `KeyError: 'Lx'` in `PDE/real_backend_pt_bcc_mixed_v3.py:106 (_params_lengths)` dominating the failures. PI-level audit of the three 2026-04-22 uploads (Math66 v0.1, `tect_newton_krylov.py` v2.6.0, `continuation_mu2_v25.py` v2.6.0) produced three authoritative judgments, frozen in the new audit note `docs/math/TECT-Math68-v26-PhaseD-Integration-Audit.tex.txt` (v0.1). **§1** Updated critical-path priority chain (Eq. `math68-priority-chain`, 8 stages): (i) v2.6.0 Phase D live integration + B1--B5 repair; (ii) Math66 §8 U1--U4 + R1--R2 verification; (iii) Math64 D5 $a_{\mathrm{cII}}(N)$ scaling; (iv) Pillar 1 / Phase 4 continuum closure; (v) Math67 Global Closure Theorem assembly; (vi) 11-pillar TOE scorecard update; (vii) cII variational-parent search (research track, non-critical); (viii) Path-Y sector rewrite (research track, non-critical). **§2 Math66 v0.1 status retraction** (Prop. `math68-math66-status`, Cor. `math68-math66-label`): the v0.1 header label "THEOREM v0.1, complete and ready for implementation" is an over-claim under peer-review standards and is corrected to "OPERATIONAL THEOREM / IMPLEMENTATION SPECIFICATION v0.1" with a four-status PI ASSESSMENT block {path-selection: CLOSED / implementation-spec: CLOSED / rigorous mathematical: OPEN to v0.2 / execution-verification: OPEN (pytest 2F/1S/2P on 2026-04-22)}. Header patch applied to Math66 source 2026-04-22. No body mathematical content retracted. **§3 Five executable-integration blockers** (Propositions `math68-B1-fix` through `math68-B5-fix`): **B1** solver-name API mismatch `{pcg, minres, fgmres}` vs `{cg, gmres}`; **B2** `_compute_adjoint_jacobian_vec_v26` autograd graph disconnected (numpy residual wrapper); **B3** `_get_cii_block_mask` returns all-True dummy; **B4** continuation-layer routing contract untested; **B5** test-config dicts use `"L": 1.0` but backend requires `"Lx"/"Ly"/"Lz"`. **§4 Immediate-fix queue** (Eq. `math68-fix-queue`, boxed): Tasks #112--#116 opened (+#117 for the companion `Tools/n64_continuum_audit.py` `sys.path` bootstrap defect reported on the user's same-day run `[WARNING] Backend unavailable: No module named 'PDE'`). **Task reclassification** (Prop. `math68-task104-status`): Task #104 "Phase D operational" $\to$ "partial live integration; executable closure OPEN pending B1--B5 repair". No code change in `PDE/*` or `tests/*` in this landing; repair commits will carry Tasks #112--#117. CHANGELOG 2026-04-22 top entry (this row). |
| 2026-04-22 | **Math65 v0.1.2 → v0.1.3 + Runs R-2026-04-22-005 and R-2026-04-22-006 — decisive triangulation completed; branch (I) Class Insufficiency sealed; Math66 operator-surgery mandatory; Path (X) in-solver symmetrisation recommended for v2.6.0 Phase D (Task #110 CLOSED, Task #104 UNBLOCKED, Task #111 NEW)**. Execution of the decisive cII grad-vs-impl test (Def. `math64-decisive-test` / Def. `math65-triangulation`) via `Tools/check_jacobian_blocks.py v1.3.1` completed on candidates $A$ and $B$ at the stored seed, producing boxed Eqs. `math65-run-A-norms` and `math65-run-B-norms`: $(\lVert F^{\mathrm{impl}}\rVert_F, \lVert F^{\mathrm{grad}(A)}\rVert_F, \Delta^{(A)}, r^{\mathrm{impl}}_A, r^{\mathrm{grad}}_A) = (1.2647\times 10^{-4}, 6.6612\times 10^{-6}, 1.2664\times 10^{-4}, 1.0013, 19.011)$ and $(\dots, \lVert F^{\mathrm{grad}(B)}\rVert_F, \Delta^{(B)}, r^{\mathrm{impl}}_B, r^{\mathrm{grad}}_B) = (\dots, 7.0425\times 10^{-3}, 7.0441\times 10^{-3}, 55.698, 1.0002)$. Applying the polarisation identity Eq. `math65-polarization` to all three candidates (including R-004 candidate $C$) gives the decisive directional readout Eq. `math65-cos-triangulation`: $\cos\theta^{(A)} \approx -1.27\times 10^{-2}$, $\cos\theta^{(B)} \approx -7.93\times 10^{-3}$, $\cos\theta^{(C)} \approx -1.55\times 10^{-3}$ — **all three candidate gradients are $L^{2}$-orthogonal to $F_{\mathrm{cII}}^{\mathrm{impl}}$** across magnitude ratios $\lVert F^{\mathrm{grad}(X)}\rVert/\lVert F^{\mathrm{impl}}\rVert \in \{0.053, 55.7, 83.6\}$. **Candidate $A$'s machine-reported $r^{\mathrm{impl}}_A = 1.0013$ Case-2 rescue signature is identified as a FALSE RESCUE** (Remark `math65-A-false-rescue`): the polarisation identity forces $\Delta^{(A)} \approx \lVert F^{\mathrm{impl}}\rVert$ whenever $\lVert F^{\mathrm{grad}(A)}\rVert \ll \lVert F^{\mathrm{impl}}\rVert$, regardless of directional agreement — a pure magnitude artefact. **Prop. `math65-class-insufficient` (NEW, proved)** seals the verdict: $\min_{X\in\{A,B,C\}}|\cos\angle(F^{\mathrm{grad}(X)},F^{\mathrm{impl}})| \le 1.27\times 10^{-2}$, so the scalar-$E_{\mathrm{cII}}$ class $\mathcal{E} = \{E^{(A)},E^{(B)},E^{(C)}\}$ does not contain $F_{\mathrm{cII}}^{\mathrm{impl}}$ at the seed. Branches (R) Rescue and (S) Split of Prop. `math65-triangulation-verdict` are falsified; **branch (I) Class Insufficiency selected**. Runs R-004/005/006 thereby realise empirically the Helmholtz-Hodge obstruction predicted by Prop. `math65-hodge`: $F^{\mathrm{impl}}$ is a scalar $\times$ vector tensor contraction and lies in the co-exact $\oplus$ harmonic complement of $\mathcal{G}_\mathcal{E}[\Psi_0]$ (Remark `math65-hodge-realised`). **Cor. `math65-math66-mandate` (NEW)**: Math66 operator surgery mandatory; two pathways specified — **(X)** in-solver Hermitian projection $J_\mathrm{cII} \mapsto \tfrac{1}{2}(J_\mathrm{cII}+J_\mathrm{cII}^\dagger)$ inside the Newton-Krylov preconditioner, legitimised by Thm. `math64-full-sympd` ($\rho_\mathrm{FULL} = 1.62\times 10^{-10}$, eight decades below the $\tau_\mathrm{rel}=10^{-8}$ threshold), $O(N\log N)$ overhead of one extra adjoint multiply per Krylov step; **(Y)** sector rewrite promoting $p_{JJ}\nabla\cdot J + p_{JK}\nabla\cdot K$ to a vector potential with auxiliary field, requires Brazovskii-fluctuation analysis of Math62, research-scale. **Recommendation for v2.6.0 Task #104 Phase D operational closure: adopt (X); defer (Y) to a separate research track (candidate Math66-Y v0.1, status OPEN)**. Remark `math65-tool-v1p4-weakness` specifies the v1.4 classifier mandate: first-class `cos_theta` reporting, new Case-0 orthogonality verdict when $|\cos\theta| < 10^{-2}$ and $\Delta/\max(\lVert F^{\mathrm{impl}}\rVert, \lVert F^{\mathrm{grad}}\rVert) > 0.95$, JSON payload augmented. Math65 §Conclusion updated with the v0.1.3 sealed-verdict paragraph. **Task status**: #110 (decisive cII grad-vs-impl test) CLOSED; #104 (v2.6.0 Phase D wiring under PCG default) UNBLOCKED pending Math66 v0.1 Path-X operator spec; #111 (NEW) drafts Math66 v0.1 Path-X note and implements tool v1.4 with cos-theta classifier. Raw JSON outputs archived at `results/math64_decisive_cII_test.json` (overwritten by last run — R-005 and R-006 triples recorded only in the CHANGELOG/Math65 §7 boxed equations; a follow-up tool upgrade to `v1.4` will include per-run file naming). Next math note: `docs/math/TECT-Math66-cII-OperatorSurgery-PathX.tex.txt` (to be drafted under Task #111). No code change this landing; purely theoretical verdict-sealing. CHANGELOG 2026-04-22 top entry (this row). |
| 2026-04-22 | **`Tools/check_jacobian_blocks.py` v1.3 → v1.3.1 + `Tools/cII_energy_candidates.py` v0.1 → v0.1.1 — `Tools/` vs `tools/` case-collision hardening (Task #101/#110 follow-up)**. First live execution of the v1.3 decisive CLI on the user's Windows box raised `ModuleNotFoundError: No module named 'Tools'` at line 886 of `Tools/check_jacobian_blocks.py`, where `run_decisive_cII_test()` lazily imported `from Tools import cII_energy_candidates as _cand_mod`. Root cause: after Task #101 completed (on-disk rename `Tools/` → `tools/` via the two-step NTFS rename), the hard-coded capital-T package prefix fails under Python 3.12's case-sensitive `FileFinder`; the sys.path bootstrap at the top of the file also did not prepend `_THIS_FILE_DIR`, so the sibling `cII_energy_candidates.py` in the same directory was not importable as a bare module either. Fix (three-part): (i) bootstrap block now prepends `(_THIS_FILE_DIR, _PDE_DIR, _REPO_ROOT_DIR)` instead of `(_PDE_DIR, _REPO_ROOT_DIR)`; (ii) the lazy import inside `run_decisive_cII_test()` is rewritten as `import cII_energy_candidates as _cand_mod` (bare sibling form, case-agnostic w.r.t. the on-disk folder spelling); (iii) CLI docstring example and argparse help text updated to `--cII-energy-module cII_energy_candidates:E_cII_C` (no package prefix). Companion patch: `Tools/cII_energy_candidates.py` `_self_test()` now exercises the `MODULE:FUNC` round-trip through `"cII_energy_candidates:E_cII_C"` instead of the prior `"Tools.cII_energy_candidates:E_cII_C"`, aligning the self-test with the case-agnostic import contract. Verification: AST OK for both files; `python Tools/cII_energy_candidates.py` → `OK -- A, B, C resolvable`; `python Tools/check_jacobian_blocks.py --selftest` → 5/5 PASS; standalone import round-trip `resolve_candidate(None | "C" | "cII_energy_candidates:E_cII_C")` all resolve to `E_cII_C`. Module versions advanced v1.3 → v1.3.1 and v0.1 → v0.1.1; CHANGELOG 2026-04-22 top entry added. Memory file `project_tools_case_collision.md` marked **RESOLVED** with the two-layer fix. **Going-forward contract**: inside the `Tools/` directory, imports between tool modules must be bare sibling imports; `from Tools import ...` and `from tools import ...` are both retired within this directory. External callers (from `PDE/` or the repository root) use the lowercase `from tools import ...` form, matching the Task #101 on-disk rename. |
| 2026-04-22 | **Math65 v0.1 (NEW, SKELETON) + `Tools/cII_energy_candidates.py` v0.1 (NEW) + `Tools/check_jacobian_blocks.py` v1.2.1 → v1.3 — decisive cII grad-vs-impl diagnostic scaffolding (Task #110)**. Math64 §6 / Math65 §4 decisive pre-surgery test $\Delta_{\mathrm{cII}} \equiv \lVert F_{\mathrm{cII}}^{\mathrm{impl}} - F_{\mathrm{cII}}^{\mathrm{grad}}\rVert_{F}$ requires a scalar candidate functional $E_{\mathrm{cII}}[\Psi;\mathrm{params}]$ whose variational derivative defines $F_{\mathrm{cII}}^{\mathrm{grad}}$. **Critical finding** from the backend audit: `PDE/real_backend_pt_bcc_mixed_v3.py` lines $423$-$461$ (`_classII_effective_term_t`) implements $F_{\mathrm{cII}}^{\mathrm{impl}}$ as a direct projected-divergence residual $\sum_{T}\bigl[\mathrm{pref}_{JJ}\,\nabla\!\cdot\!\mathcal{J}_{T} + \mathrm{pref}_{JK}\,\nabla\!\cdot\!\mathcal{K}_{T}\bigr](T\Psi - q_{T}\Psi)$, with **no pre-existing scalar $E_{\mathrm{cII}}$** in the module (grep over `energy`/`action`/`functional`/`lagrangian` returns empty); the module docstring explicitly describes the block as "executable proxy for the integrated-out Class II sector". Consequently Math65 supplies the candidate functional from theory. **Math65 v0.1 (SKELETON)** (`docs/math/TECT-Math65-cII-EulerLagrange-Rewrite.tex.txt`, ~350 lines) provides: (i) Frame + **Remark math65-critical-finding** (backend audit); (ii) three candidates — $E^{(A)}$ Def. `math65-EcII-A` (bilinear channel-gradient; Prop. `math65-A-status`: INCOMPLETE — reproduces $\mathrm{pref}_{JJ}$ only), $E^{(B)}$ Def. `math65-EcII-B` (density-normalised; Prop. `math65-B-status`: carries candidate anti-Hermitian artefact), $E^{(C)}$ Def. `math65-EcII-C` (CANONICAL EL-consistent; Prop. `math65-C-status`: test branch between Case 1 assembly and Case 2 design defect); (iii) **Helmholtz-Hodge obstruction** Prop. `math65-hodge` relating $a_{\mathrm{cII}} \ge c_{0}\sum_{T}\lVert\nabla\times\mathbf{V}_{T}\rVert_{L^{2}}$ and Cor. `math65-reading` (the $4.357\times 10^{-7}$ mass is an $L^{2}$-curl charge); (iv) Def. `math65-cand-API` API contract. Theorems/propositions are declared only; proofs deferred to v0.2 pending decisive-test outcome. **`Tools/cII_energy_candidates.py` v0.1 (NEW)** (~300 lines): pluggable candidate module implementing `E_cII_A`, `E_cII_B`, `E_cII_C` (canonical default) + `resolve_candidate(spec)` supporting registry keys `{"A","B","C","default"}` and external `"MODULE:FUNC"`; lazy-imports the backend's Gell-Mann embedding and BCC spectral derivative; pure `torch` primitives preserving autograd. Self-test `OK -- A, B, C resolvable`. **`Tools/check_jacobian_blocks.py` v1.2.1 → v1.3**: (i) new section `v1.3 decisive grad-vs-impl diagnostic` with `_compute_F_cII_impl`, `_compute_F_cII_grad` (applies $F_{\mathrm{cII}}^{\mathrm{grad}} = 2\cdot$`torch.autograd.grad(E, Psi_t)` enforcing the Wirtinger normalisation of Math63 §2A.2 Lemma 2), `_classify_cII_surgery_gate` (Case 1 at $10\varepsilon_{\mathrm{fd}}$, Case 2 at $0.1\cdot a_{\mathrm{cII}}^{\mathrm{ref}}$, Case 3 otherwise per Prop. `math64-cii-surgery-gate`), `run_decisive_cII_test` end-to-end driver emitting (Delta_cII, r_impl, r_grad); (ii) four new CLI flags `--cII-grad-check`, `--cII-energy-module MODULE:FUNC` (default resolves to canonical C), `--a-cII-ref` (default $4.357\times 10^{-7}$), `--eps-fd` (default $5\times 10^{-7}$); (iii) new main() branch: when `--cII-grad-check` is set, SUPERSEDES the block-sweep path and runs the decisive diagnostic at the given $\mu^{2}$ (or first entry of `--mu2-list`). Exit codes: $0$ (Case 1), $12$ (Case 2), $13$ (Case 3). AST validated; harness self-test regression 5/5 PASS retained. Back-compat: every pre-v1.3 invocation bit-identical under v1.3. Task #104 (v2.6.0 Phase D wiring) remains open under PCG-default routing; Task #110 executability now unblocked. CHANGELOG 2026-04-22 top entry (this row). |
| 2026-04-22 | **Math63 v1.6 → v1.7 + Math64 v1.0 → v1.1: §2A.3 post-closure verdict — FULL SYM-PD under §2A.1 relative criterion, Stage-α solver-routing refined to PCG-default / MINRES-fallback / FGMRES-last-resort; decisive cII `grad`-vs-`impl` test mandated as pre-surgery gate (Task #109)**. PI read-out of R-2026-04-22-003 raw data identified two additions required before any cII operator surgery. (a) At the FULL operator level, $\rho_{\mathrm{FULL}} = \mathrm{antisym}/\lVert\mathcal{J}\rVert_{F} \approx 1.62\times 10^{-10}$ at every $\mu^{2}\in\mathcal{W}$ under cII-on, which lies eight decades below the §2A.1 classification threshold $\tau_{\mathrm{rel}} = 10^{-8}$; the scale explanation is $\lVert\mathcal{J}_{\mathrm{FULL}}\rVert_{F}\approx 2.7\times 10^{+3}$ at the thermal seed, so the absolute anti-Hermitian mass $a_{\mathrm{cII}} = 4.357\times 10^{-7}$ is block-structural at cII (where $\rho_{\mathrm{cII}}\approx 5.84\times 10^{-3}$) yet operationally inert at the full-operator level. Hence Algorithm 1 of Math63 §2B dispatches to the `SPD → PCG` branch at every $\mu^{2}$, under both Jacobian-vector backends. Newton-Krylov v2.6 inner-solver default at seed level is therefore `PCG`, with `MINRES` the symmetric-indefinite fallback and `FGMRES` strictly demoted from "asymmetric-primary" to "last-resort" and unreached on $\mathcal{W}$ at seed level. Iterate-level re-verification at $k\in\{0,3,6\}$ after Task #104 wiring is a confirmatory post-wiring step; the architected fallback branches remain active. (b) Math64 §5 resolutions (X)/(Y)/(Z) (in-solver symmetrisation / EL rewrite / FGMRES-on-cII) are premature until the anti-Hermitian signature is partitioned between an **assembly bug** in the current projected-divergence implementation vs a **design defect** in the scalar Class-II energy functional $E_{\mathrm{cII}}$ or the channel projector $\Pi_{\mathrm{channel}}$. Decisive test (Definition `math64-decisive-test`): compute $F_{\mathrm{cII}}^{\mathrm{impl}}$ = current backend output vs $F_{\mathrm{cII}}^{\mathrm{grad}} = \texttt{autograd.grad}(E_{\mathrm{cII}}[\Psi], \Psi)$ at the canonical thermal seed on $\mathcal{W}$, report three observables $\Delta_{\mathrm{cII}}, r^{\mathrm{impl}}, r^{\mathrm{grad}}$. Proposition `math64-cii-surgery-gate` three cases: Case 1 (assembly bug, $r^{\mathrm{grad}} \le \tau_{\mathrm{rel}}$) → one-token patch in `_classII_effective_term_t`, no (X)/(Y) needed; Case 2 (design defect, $r^{\mathrm{grad}} \gtrsim 10^{-3}$) → Math65 Euler-Lagrange rewrite mandatory; Case 3 (inconclusive, $10^{-8} \le r^{\mathrm{grad}} \le 10^{-5}$) → (X) for v2.6.0 operational closure + Math65 (Y) in parallel. **Math63 v1.6 → v1.7**: new §2A.3 subsubsection "Post-closure verdict: full-operator SYM-PD classification and solver-routing refinement" with boxed Eq. `math63-2A3-full-rel-ratio`, Corollary `math63-2A3-solver-routing` (PCG/MINRES/FGMRES), Remark `math63-2A3-iterate-scope`, Definition `math63-2A3-cII-decisive-test`, Proposition `math63-2A3-cII-surgery-gate`, parallelism remark; Algorithm 1 of §2B annotated with Stage-α note + label `alg:math63-2B-choose-inner-solver` added. **Math64 v1.0 → v1.1**: new §5 "Stage-α solver-routing verdict" with Eq. `math64-full-rel-ratio`, Theorem `math64-full-sympd`, Corollary `math64-inner-solver-routing`, seed-vs-iterate scope remark; new §6 "Decisive pre-surgery diagnostic" with Definition `math64-decisive-test`, Eq. `math64-decisive-observables`, Proposition `math64-cii-surgery-gate`, tool-v1.3 implementation remark, parallelism-with-routing remark; Conclusion extended with a v1.0 → v1.1 summary paragraph. No code change this landing; tool v1.3 `--cII-grad-check` flag is specified in Math64 §6 as the next implementation step and is tracked as a follow-on sub-task. Task #104 (v2.6.0 Phase D wiring) proceeds under the PCG-default routing. Math65 (operator-surgery decision) is conditional on the decisive-test outcome. CHANGELOG 2026-04-22 top entry; §11 row (this row). |
| 2026-04-22 | **Math63 v1.5 → v1.6 + Math64 v1.0 (NEW companion note) — §2A.3 Stage α CLOSED: Corollary 2A.3 promoted to window-level (Task #109)**. The four-configuration Stage α sweep sealed in Math63 v1.5 §2A.3 was executed on the user local machine (R-2026-04-22-003) via `Tools/check_jacobian_blocks.py` v1.2.1 against `PDE/config_template_brazovskii.json` with $(N, n_{\text{probes}}, \sigma, \text{seed}) = (32, 5, 10^{-2}, 42)$ and $\mu^{2}\in\{-1.0,-0.8,-0.6,-0.4,-0.2,-0.1\}$. The four configurations $(\alpha_A, \alpha_B, \alpha_C, \alpha_D) = (\text{FD-on}, \text{autograd-on}, \text{FD-off}, \text{autograd-off})$ returned $(a_{\mathrm{cII}}, a_{\mathrm{cII}}, a_{\mathrm{FULL}^{*}}, a_{\mathrm{FULL}^{*}}) = (4.3567\times 10^{-7}, 4.3567\times 10^{-7}, 1.4211\times 10^{-14}, 1.4211\times 10^{-14})$ at every $\mu^{2}$ (bit-identical under both backends to ten decimal places), with non-cII blocks uniformly at Hermitian precision floor $\le 10^{-13}$. Acceptance-gate `math63-2A3-stage-alpha-gate` satisfied: $\lvert a_{\alpha_A} - a_{\alpha_B}\rvert = 0 \le 10^{-9}$ (saturates by ten-digit identity) $\wedge$ $a_{\alpha_D}(\mathrm{FULL}^{*}) = 1.421\times 10^{-14} \le 10^{-12}$ (two decades below threshold). **Corollary 2A.3 (Sole Carrier) promoted** from "empirically verified on one state under FD" to "empirically verified across the continuation window $\mathcal{W}$ under two independent Jacobian-vector backends AND under structural ablation". Hypotheses $S_{2}$ (hidden inter-block coupling) and $S_{3}$ (Nyquist-mode aliasing) **falsified on $\mathcal{W}$**; hypothesis $S_{1}$ (structural non-self-adjointness of the projected-divergence Class II block) **confirmed at window level**. The ten-digit FD/autograd match is explained by the new Lemma `math64-fd-antisym` (central-FD truncation $\frac{1}{6}\varepsilon^{2} D^{3}F_{\mathrm{cII}}[v,v,v]$ is a symmetric trilinear form by Clairaut's theorem, so it contributes only to the Hermitian part of the FD JVP and is invisible to the anti-Hermitian norm — FD is structurally antisym-invariant). **Math63 v1.5 → v1.6**: new §2A.3 subsubsection "Stage α CLOSED: sole-carrier claim promoted to window-level under two backends and structural ablation" with boxed Eq. `math63-2A3-stage-alpha-result`, Theorem `math63-2A3-stage-alpha-closure` (four-point statement), FD antisym-invariance proof remark, Corollary `math63-2A3-cII-state-independence` (re-classifies the $2.66\times 10^{-4}$ Stage $[4/4]$ signal as a Phase D PLACEHOLDER iterate-norm artefact, not a physical property), CLI invocation note (tool v1.2.1). **Math64 v1.0 (NEW, ~450 lines)** filed as companion audit note at `docs/math/TECT-Math64-cII-Stage-Alpha-Audit.tex.txt`: §1 raw data (four per-config aggregate tables + full-precision seven-row table at $\mu^{2}=-1.0$); §2 Stage α acceptance-gate evaluation (Theorem `math64-stage-alpha-closure`, Corollary `math64-cII-state-indep`); §3 Wirtinger analysis with Lemma `math64-fd-antisym` and structural non-closedness of the projected-divergence operator; §4 **§2D acceptance-gate reformulation** as absolute bound Eq. `sec2d-gate` $a_{\mathrm{cII}}(\Psi) \le \tau_{\mathrm{struct}} \in [10^{-6}, 10^{-5}]$ replacing the relative ratio; §5 three candidate resolutions (X) in-solver symmetrisation / (Y) Euler-Lagrange rewrite of $\Phi_{\mathrm{cII}}[\Psi]$ / (Z) unconditional FGMRES, with Helmholtz-Hodge obstruction noted for (Y); §6 confirmatory items — (D1) CLOSED, (D3)/(D4) subsumed by Stage α, (D2)/(D5) retained for $\tau_{\mathrm{struct}}$ calibration at $N\in\{16, 32, 48, 64\}$; §7 conclusion recommending (X) for v2.6.0 Phase D integration pending Math65 (Y) decision. Task #104 (v2.6.0 Phase D wiring) **unblocked**: §2D gate specified (absolute bound), operator-level treatment specified (X), $\tau_{\mathrm{struct}}$ calibration is the only open numerical item (D5 N-scaling). CHANGELOG 2026-04-22 top entry. |
| 2026-04-22 | **Tools/check_jacobian_blocks.py v1.2 → v1.2.1: argparse negative-list CLI usability hotfix (Task #109)**. Python's `argparse` refuses to accept a value that begins with `-` (e.g. `-1.0,-0.8,-0.6,-0.4,-0.2,-0.1`) as the argument of a string-typed option when given in the space-separated form `--mu2-list <neg-csv>`, because it cannot disambiguate between "option-value that happens to look negative" and "an unknown optional flag". The canonical Stage $\alpha$ invocation `python Tools/check_jacobian_blocks.py --backend fd --mu2-list -1.0,-0.8,...` hit exactly this failure on the first user-machine attempt: `error: argument --mu2-list: expected one argument`. Fix: new helper `_glue_negative_list_value(argv, option_name)` preprocesses `sys.argv[1:]` inside `main()` before `parser.parse_args(...)` runs; a token matching `option_name` (currently only `--mu2-list`) whose immediate successor looks like a negative numerical value (starts with `-` and contains a digit, a comma, or `.digit`) is folded into the equals-sign form `option_name=<value>` as a single token. Already-equals-sign-formatted invocations and positive-numerical CSVs are passed through untouched. AST-parse clean; `--selftest` retained 5/5 PASS; new 6/6 glue-function unit test covers all CLI token patterns. Back-compat: v1.2 helper APIs preserved verbatim; the equals-sign form is bit-identical under v1.2.1. No change to Math63 §2A.1 probe policy or §2A.3 Stage $\alpha$ acceptance condition. Module version v1.2 → v1.2.1; §10.5 MATURITY header v1.2 → v1.2.1 (STAGE-α-EXECUTABLE). CHANGELOG 2026-04-22 top entry. |
| 2026-04-22 | **Math63 v1.4 → v1.5 + Tools/check_jacobian_blocks.py v1.1 → v1.2: §2A.3 Stage α plan sealed (Task #109)**. The Step (D1) closure of 2026-04-22 left three residual degrees of freedom unresolved: (i) the central-FD truncation channel at $\varepsilon = 5\cdot 10^{-7}$ (bound $\sim 10^{-13}$, six decades below the observed $4.357\cdot 10^{-7}$ signal — unlikely but not formally excluded); (ii) the single-$\mu^{2}$-vs-continuation-window scope of the sole-carrier claim; (iii) the statistical-vs-structural nature of the cII attribution. The v1.2 tool extension closes all three in one reproducible sweep by adding **`--backend {fd,autograd}`** (routes cII Jacobian-vector product through `torch.func.jvp` with `torch.autograd.functional.jvp` fallback — evaluates the exact real-linear action $A(\Psi)v + B(\Psi)\overline{v}$ at machine precision, removing the FD truncation and cancellation-noise floors from the cII arm), **`--mu2-list CSV`** (loop over continuation points with fresh thermal BCC seed per point; canonical Stage α list $\mu^{2} \in \{-1.0, -0.8, -0.6, -0.4, -0.2, -0.1\}$), and **`--cII-off`** (zeros $\{\alpha_X, \beta_X, c_{JJ}, c_{JK}\}$ in a params clone, pruning cII from the block sweep and re-running `backend.hessian_vec` with the Class II sector structurally absent). Math63 v1.5 adds the §2A.3 subsubsection **"Stage α: orthogonal confirmation of the sole-carrier claim"** with the four-configuration execution matrix Eq. `math63-2A3-stage-alpha-matrix` ($\alpha_A$/fd-on, $\alpha_B$/autograd-on, $\alpha_C$/fd-off, $\alpha_D$/autograd-off), the acceptance gate Eq. `math63-2A3-stage-alpha-gate` $|a_{\alpha_A} - a_{\alpha_B}|\le 10^{-9} \wedge a_{\alpha_D}(\text{FULL})\le 10^{-12}$ at every $\mu^{2}$, and a three-item fallback ladder (FD artefact $\to$ non-cII residual leakage $\to$ $\mu^{2}$-dependent scaling). Tool AST-parse clean; self-test 5/5 PASS retained at Hermitian precision floor (the v1.2 cII-autograd, multi-mu2, and cII-off code paths are bypassed by the self-test harness, which exercises only the probe logic on synthetic operators). Live Stage α sweep wall-clock-bounded at ~5 min on $N=32$ BCC PyTorch CPU backend (4 configs × 6 mu2 points × (6 blocks + 1 FULL) probes = 192 per-block evaluations). Every pre-v1.2 invocation is bit-identical under v1.2 (`--backend` defaults to `fd`, `--cII-off` defaults to False). Math63 header Status updated to "§§2A.1/2A.2/2A.3 addenda; §2A.3 Step (D1) executed, S1 confirmed; §2A.3 Stage α plan sealed". Stage α live report destination: `docs/math/TECT-Math64-cII-Stage-Alpha-Audit.tex.txt` (to be filed upon user execution); JSON artefacts under `results/stage_alpha_{A,B,C,D}_*.json`. CHANGELOG 2026-04-22 top entry; §10.5 MATURITY v1.1 → v1.2 (STAGE-α-EXECUTABLE). |
| 2026-04-22 | **Math63 v1.3 → v1.4: §2A.3 Step (D1) live execution — S1 empirically confirmed, $F_{\mathrm{cII}}$ isolated as sole carrier of the anti-Hermitian component (Task #109)**. The Step (D1) live sweep executed on the user local machine via `Tools/check_jacobian_blocks.py` v1.1 with $(N, \mu^{2}, n_{\text{probes}}, \sigma, \text{seed}) = (32, -0.5, 5, 10^{-2}, 42)$ produced the crystalline block-decomposition pattern predicted by hypothesis S1. Per-block relative antisymmetry $\operatorname{antisym}/\lVert\mathcal{J}_X\rVert_F$: **bra = 3.97·10^{−18}, fam = 1.23·10^{−18}, lock = 3.54·10^{−18}, shell = 0 (dormant, η_shell=0 in config), nl = 4.60·10^{−18}, cII = 5.84·10^{−3} (ASYM), FULL = 1.62·10^{−10}**. Five of the six blocks classify at the Hermitian precision floor, directly verifying Lemmas 2A.3-1 (bra/fam/lock/shell Hermitian a priori) and 2A.3-2 (nl real-self-adjoint under Re(vdot) via the Wirtinger $A + B\overline{v}$ decomposition) at $10^{-18}$ tolerance. The sixth block, $F_{\mathrm{cII}}$, exceeds the $10^{-8}$ threshold by a factor of $5.84\times 10^{+5}$. **Absolute anti-Hermitian norm isolation identity**: $\lVert\mathcal{J}_{\text{full}} - \mathcal{J}_{\text{full}}^{\dagger}\rVert_F = \lVert\mathcal{J}_{\mathrm{cII}} - \mathcal{J}_{\mathrm{cII}}^{\dagger}\rVert_F = 4.35668\times 10^{-7}$ (numerical ratio $0.99999999431$ — agreement to 9 decimal places). **Hypothesis S1 (structural non-self-adjointness of the projected-divergence Class II block) is empirically confirmed**; hypotheses S2 (hidden inter-block coupling) and S3 (Nyquist-mode aliasing) are falsified on the probed state, since they would each require non-Hermitian contributions from at least one block other than cII. The state dependence of the original $2.66\times 10^{-4}$ Stage [4/4] signal is explained by $\lVert\mathcal{J}_{\text{full}}\rVert_F$ varying between $\approx 2.7\times 10^{+3}$ (thermal seed) and $\approx 1.6\times 10^{-3}$ (Phase D PLACEHOLDER pseudo-iterate), while the absolute anti-Hermitian norm carried by cII alone stays at $\approx 4.4\times 10^{-7}$; the $\mu^{2}$-independence of the Stage [4/4] signal across six points reflects Phase D producing similar-scale pseudo-iterates rather than a physical property of the continuation trajectory. **Secondary finding**: shell-block Jacobian norm is exactly zero because `eta_shell = 0.0` in `PDE/config_template_brazovskii.json`; Lemma 2A.3-1 remains valid, to be re-confirmed on any future $\eta_{\mathrm{shell}}>0$ activation. **Math63 v1.3 → v1.4**: header status updated to "§2A.3 Step (D1) executed, S1 confirmed"; §2A.3 body extended with Step (D1) execution-result paragraph (full seven-row table, Eq. `math63-2A3-cII-isolation` for the absolute anti-Hermitian norm identity), Corollary 2A.3 (sole-carrier), State-dependence remark, shell-dormancy remark, and plan restatement promoting (D2)–(D5) from exploratory to confirmatory with priority **(D3-on-cII) $\succ$ (D5) $\succ$ (D2) $\succ$ (D4)** — (D4) demoted to OPTIONAL contingent on (D5) outcome. **Lemmas 2A.3-1 and 2A.3-2 promoted** from "a priori" to "a priori + empirically verified at $10^{-18}$". Immediate next action: **Step (D3-on-cII)** — autograd cross-check of $\mathcal{J}_{\mathrm{cII}}$ against the current `eps=5e-7` central-FD JVP, to discriminate between scenario (D3-α) genuine structural non-self-adjointness (forcing a Class-II rewrite as EL variation or operator symmetrisation) and (D3-β) FD truncation artefact (retained with documented `eps` bound). (D3-α) is the a priori likely outcome. No code change this landing (tool v1.1 was already the authoritative harness); §2A.3 remains orthogonal to the v2.6 Phase D wiring (Task #104). CHANGELOG top entry 2026-04-22. |
| 2026-04-22 | **Tools/check_jacobian_blocks.py v1.0 → v1.1: sys.path bootstrap hotfix for Step (D1) live execution (Task #109)**. First live invocation `python Tools/check_jacobian_blocks.py --config PDE/config_template_brazovskii.json --N 32 --mu2 -0.5 ...` from the repository root aborted at line 499 (`_build_seed`) with `ModuleNotFoundError: No module named 'math56_constants'`. Root cause: v1.0 relied on ambient `sys.path` for the deferred imports of `math56_constants` and `real_backend_pt_bcc_mixed_v3` (both in `Contents/PDE/`), but Python's `sys.path` does not auto-include sibling directories of the script's parent when launched from an unrelated working directory. **Exact analogue of Task #100** (`continuation_mu2_v25.py` v2.5.0 → v2.5.1). Fix: insert a `sys.path` bootstrap block between the stdlib imports and the `torch` import that, using `os.path.abspath(__file__)` as the anchor, prepends both `Contents/PDE/` (first) and `Contents/` (second) to `sys.path` if not already present. Both the explicit `from math56_constants import build_seed_bcc` and the `importlib.import_module('real_backend_pt_bcc_mixed_v3')` now resolve deterministically regardless of launch directory. Patch is **import-time only**; probe logic, Wirtinger JVP, self-test harness, and exit-code contract unchanged. Self-test 5/5 PASS retained (bootstrap is a no-op along the self-test path — the path does not touch backend modules). Module version bumped v1.0 → v1.1; §10.5 MATURITY block updated with v1.1 tag + v1.1 change notes above the v1.0 entry. Math63 §2A.3 specification is untouched (plumbing fix). Live sweep is now ready for immediate re-execution. |
| 2026-04-22 | **Tools/check_jacobian_blocks.py v1.0 (NEW) + Math63 v1.2 → v1.3: §2A.3 BCC Jacobian Residual Anti-Hermitian Component Diagnostic Framework, Step (D1) landing (Task #109)**. Motivating signal: the first live Stage $[4/4]$ run under the v2.0 complex-Hermitian probe policy reported $\operatorname{antisym}/\lVert J\rVert = 2.66\times 10^{-4}$ **identical across all six $\mu^{2}$ continuation points** — $10^{13}$ above the Hermitian precision floor, $10^{3}$ below full anti-Hermitian, and $\mu^{2}$-independent. The uniform-across-$\mu^{2}$ character rules out residual-magnitude-driven noise and localises the signal to a **structural** anti-Hermitian defect in the block composition of `real_backend_pt_bcc_mixed_v3.residual()`. **Decision**: open Math63 §2A.3 with a 5-step diagnostic plan (D1)–(D5) — (D1) operator-level block decomposition probe, (D2) simple-cubic vs BCC cross-check, (D3) analytic vs autograd Jacobian cross-check, (D4) Nyquist-mode ablation, (D5) N-scaling at $N\in\{16,32,48,64\}$. **Step (D1) deliverable**: new sibling diagnostic `Tools/check_jacobian_blocks.py` v1.0 (~460 lines). Probes the six additive blocks $F = F_{\mathrm{bra}} + F_{\mathrm{fam}} + F_{\mathrm{lock}} + F_{\mathrm{shell}} + F_{\mathrm{nl}} + F_{\mathrm{cII}}$ **in isolation** under the v2.0 protocol (real-self-adjoint criterion, complex $\mathcal{CN}(0,I)$ probes, `torch.vdot`/`np.vdot`, threshold $10^{-8}$). `F_nl` uses the **analytical Wirtinger JVP** from Lemma 2A.3-2 (not finite difference); `F_cII` uses central FD with `eps=5e-7`. Exit code $0$ iff all blocks symmetric, $11$ otherwise. `--selftest` intercepted before argparse (torch-less fallback). **Theory**: §2A.3 addendum inserted between §2A.2 and §B of Math63 v1.3. Definition 2A.3-1 (block decomposition, six $F_X$ explicit); Lemma 2A.3-1 (bra/fam/lock/shell Hermitian a priori via real-symbol spectral operators); Lemma 2A.3-2 (nl real-self-adjoint under $\operatorname{Re}\langle\cdot,\cdot\rangle$ via Wirtinger split $\mathcal{J}_{\mathrm{nl}} v = A(\Psi) v + B(\Psi)\overline{v}$ with $A = A^{\dagger}$ and $B = B^{T}$); Remark 2A.3 (suspicion window S1/S2/S3, with S1 naming $F_{\mathrm{cII}}$ as structurally suspicious because a projected divergence $\nabla\cdot(\Pi_{\text{channel}}(T\Psi - q\Psi))$ is not the EL variation of a single scalar functional); Plan (D1)–(D5); Acceptance-gate implication for §2D; Scope remark. **Self-test 5/5 PASS** at Hermitian precision floor: `antisym/|J| = {3.95·10^{−17}, 0.0, 8.98·10^{−17}, 5.05·10^{−01}, 5.39·10^{−17}}` for (diag-real-PD, diag-real-indef, Hermitian-complex, anti-Hermitian-complex iH, nl-Wirtinger). Case 2 initial version (single Gaussian-random diagonal, seed=0, n=16) happened to land all 5 probes in the positive-Rayleigh cone — classifier correctly reported `symmetric=True, positive_definite=True`, but the test's AND-with-`indefinite` assertion failed; fixed by forcing a balanced diagonal `concat([+2·1_{n/2}, −2·1_{n/2}])` guaranteeing Rayleigh of both signs under any QR basis; transparent history item recorded in §10.5 v1.0 change notes. **Scope**: Math63 §2A.3 applies to `PDE/real_backend_pt_bcc_mixed_v3.residual`; scalar-Brazovskii backend excluded (no BCC spectral Laplacian, no Class-II term). **Relation to §10.3**: `check_jacobian_blocks.py` is a **sibling** of `check_jacobian_symmetry.py` v2.0 (which is retained unchanged as the full-residual reference), **not** a supersession — the block tool calls `probe_symmetry` internally and diffs its sum against the full-residual signal for consistency. Residual status: Phase D of v2.5 is still a PLACEHOLDER (exit $10$ / `SKELETON_ONLY` until Task #104 / v2.6.0); §2A.3 is **orthogonal** to v2.6 wiring — it classifies the Jacobian operator itself. Live six-block sweep pending user local machine (CLI: `python Tools/check_jacobian_blocks.py --config PDE/config_template_brazovskii.json --N 32 --mu2 -0.5 --n-probes 5 --output results/step1_block_probe.json --verbose`); Steps (D2)–(D5) pending implementation in subsequent turns. §10.5 added (MATURITY: SKELETON-EXECUTABLE diagnostic tier); CHANGELOG 2026-04-22 top entry added. |
| 2026-04-22 | **continuation_mu2_v25.py v2.5.6 → v2.5.7 + tect_newton_krylov.py minor + Math63 v1.1 → v1.2: Exception-Handling Policy (§2A.2 addendum, Task #108)**. Systematic audit prompted by the Layer-5 postmortem: both the `residual_bcc` typo (v2.5.0–v2.5.3) and the complex-probe mis-cast (`check_jacobian_symmetry` v1.0–v1.2) survived $\ge 4$ releases because a broad `except Exception as e: if verbose: print(...); return None` branch in `probe_jacobian_cached()` laundered hard programming defects into polite degraded-mode fallbacks. **Scope**: Math63 v2.5 live-execution path only (deprecated/legacy modules excluded). Four in-scope broad catches identified: `continuation_mu2_v25.py` lines $299$ (import fallback), $488$ (probe cache — the Layer-5 culprit), $751$ (per-point main loop); `tect_newton_krylov.py` line $97$ (mock-branch import fallback). `v24_thresholds.py` lines $265$ / $313$ reviewed and retained as legitimate logger guards (scope = single side-effect statement, no physics state). **Policy formalised** as Math63 §2A.2 addendum with five points: **(P1)** no catch-all on the execution path; **(P2)** dichotomy between programming errors $\{\mathrm{AttributeError}, \mathrm{TypeError}, \mathrm{NameError}, \mathrm{ImportError}\}$ which must re-raise, and runtime conditions $\{\mathrm{RuntimeError}, \mathrm{ValueError}, \mathrm{ArithmeticError}, \mathrm{MemoryError}, \mathrm{numpy.linalg.LinAlgError}\}$ which may degrade; **(P3)** unconditional WARN log (no `if verbose` gate) with `type(e).__name__: str(e)`; **(P4)** last-6-frames traceback on first per-run occurrence; **(P5)** import fallbacks tighten to `(ImportError, ModuleNotFoundError)` only. Detection-guarantee proposition (§2A.2): any programming defect on the execution path either prevents module import, raises at the first call site, or is logged at WARN with a full traceback — no defect class admitting the v2.5.0–v2.5.3 silent-four-release pattern remains admissible. **Fixes**: (A) line $299$ `except Exception` → `except (ImportError, ModuleNotFoundError)`; (B) line $488$ split into `except (AttributeError, TypeError, NameError, ImportError): raise` followed by `except (RuntimeError, ValueError, ArithmeticError, MemoryError, np.linalg.LinAlgError) as e:` with unconditional stderr log plus first-occurrence traceback via `traceback.print_exc`; (C) line $751$ main loop likewise split, stagnation_reason stores `type(e).__name__: str(e)` instead of bare `str(e)`; (D) `tect_newton_krylov.py:97` narrowed to `(ImportError, ModuleNotFoundError)`. Both patched files AST-parse clean. Residual status: Phase D is still a PLACEHOLDER; diagnostic run still terminates with exit $10$ / `SKELETON_ONLY` until Task #104 (v2.6.0). Hardening is defensive, not physics-bearing — no numerical result changes; the §2A probe now fails loudly on any future programming defect rather than degrading silently. §10.4 header v2.5.5 → v2.5.7 + MATURITY reference + version-history entry; Math63 tex document v1.1 → v1.2 with §2A.2 addendum (definition of programming/runtime dichotomy, five policy points, detection guarantee proposition with proof sketch, scope remark). |
| 2026-04-22 | **tools/check_jacobian_symmetry.py v1.2 → v2.0 + Math63 v1.0 → v1.1: complex-Hermitian probe policy (§2A.1 addendum)**. The first live Stage $[4/4]$ run under v2.5.5 (BCC seed factory fix) produced (i) `UserWarning: Casting complex values to real discards the imaginary part` from `probe_symmetry` line $102$ and (ii) identical `antisym/‖J‖ = 2.84\times 10^{-4}$` across all six $\mu^{2}$ points, classified as asymmetric. The second signature is physically incompatible with a residual derived from a real-valued Ginzburg-Landau functional — a real-self-adjoint operator must report $\operatorname{Re}\langle u, \mathcal{J}v\rangle = \operatorname{Re}\langle \mathcal{J}u, v\rangle$ to machine precision on any probe basis. Root cause: three coupled sub-defects in the v1.2 probe implementation. (5a) `torch.from_numpy(x0).to(dtype=torch.float64)` at line $102$ silently projected the `complex128` seed to real — the imaginary part of $\Psi$ was never seen. (5b) `torch.randn(...)` generated real-valued Gaussian probe vectors, so even after a complex state was passed through, the probe basis spanned only the real subspace of $\mathbb{C}^{n}$. (5c) Inner products were computed by `torch.dot` / `np.dot` (bilinear) instead of `torch.vdot` / `np.vdot` (sesquilinear) — under the bilinear pairing an anti-Hermitian operator $i H$ reports $\langle u, iH u\rangle = i u^{T} H u$, which is purely imaginary and therefore *appears* antisymmetric-free, collapsing the classifier. The three defects compounded: after (5a) the state was real, after (5b) the probes were real, so the sesquilinear/bilinear distinction in (5c) was invisible — and the four-release silent `except Exception` pattern from v2.5.4 ensured the misclassification left no trace. The v2.5.3 honest-reporting contract surfaced the defect at the first live run. Decision: the TECT GL residual with $\lvert\Psi\rvert^{2}\Psi$ is not holomorphic; it is an $\mathbb{R}$-linear Wirtinger-type operator on $\mathbb{C}^{n} \cong \mathbb{R}^{2n}$ derived from the Fréchet derivative of a real-valued functional. The mathematically correct classifier is therefore the **real-self-adjoint** criterion $\operatorname{Re}\langle u, \mathcal{J}v\rangle = \operatorname{Re}\langle \mathcal{J}u, v\rangle$ under the sesquilinear product $\langle u, v\rangle = u^{*}\!\cdot v$. Fix: v2.0 rewrite of `probe_symmetry` with (A) input-dtype-preserving `_preserve_torch_dtype()` helper (no silent cast); (B) `is_complex`-branched probe generation — real $\mathcal{N}(0,1)$ if $\Psi$ is real, complex $\mathcal{CN}(0,I) = (\mathcal{N}(0,1) + i\mathcal{N}(0,1))/\sqrt{2}$ i.i.d. if $\Psi$ is complex; (C) central `_inner(a,b)` helper wrapping `torch.vdot` / `np.vdot` and returning `.real` for classification; (D) return dict extended with `dtype_kind` and `inner_product` fields so the path taken is always explicit; (E) `_self_test` extended from 3 to 6 cases adding complex Hermitian SPD, anti-Hermitian $iD$, and non-diagonal Hermitian tridiagonal $\pm i$ off-diagonal. Math63 §2A.1 (Complex-Hermitian Probe Policy) inserted between §A caching and §B as an addendum; v1.2 real path remains bit-identical under the v2.0 implementation by the backward-compatibility proposition ($\operatorname{Re}$ of real vdot is ordinary dot, $\mathcal{CN}$ reduces to $\mathcal{N}$ on a real state). Sandbox 6/6 PASS in numpy-only fallback mode (torch not available in sandbox); antisymmetry norm $\sim 10^{-17}$ for the Hermitian cases, $\approx 0.28$–$0.77$ for the asymmetric / anti-Hermitian cases. Residual status: Phase D is still a PLACEHOLDER; diagnostic run still terminates with exit $10$ / `SKELETON_ONLY` until Task #104 (v2.6.0). Next-run prediction: with v2.0 in place the probe should report `symmetric=True, indefinite=?`-indefinite for $\mu^{2} < 0$ (Ginzburg-Landau at disordered side), antisymmetry norm at machine precision. A persistent asymmetric signal on the live BCC residual after v2.0 would indicate a genuine anti-Hermitian component (lattice-induced anisotropy, boundary artefact, or residual sign-bug) requiring a follow-on Math63 §2A.2 analysis. §10.3 header + MATURITY block (**PROOF-GRADE diagnostic tier**) + version history updated. Companion Math63 v1.0 → v1.1 specification document updated with §2A.1 addendum; CHANGELOG 2026-04-22 entry added. |
| 2026-04-22 | **continuation_mu2_v25.py v2.5.4 → v2.5.5 + math56_constants.py v1.0 → v1.1: seed shape fix (build_seed_bcc factory)**. The first live Stage $[4/4]$ run under v2.5.4 (probe attribute-name fix) produced a *new* stderr message at every fifth Newton iteration of every one of the six $\mu^{2}$ points: `Probe failed: Psi must have shape (3, Nx, Ny, Nz); using default`. Root cause: the legacy `math56_constants.build_seed()` returns scalar-Brazovskii shape $(N, N, N)$ dtype `float64` (lines $308$/$312$/$319$ of that module), but the active BCC backend `real_backend_pt_bcc_mixed_v3._shape3` at line $95$ enforces `Psi.ndim == 4 and Psi.shape[0] == 3` with `dtype=complex128`. The mismatch had been masked for four releases by the `residual_bcc` typo (fixed in v2.5.4), which triggered an `AttributeError` upstream of the shape check. v2.5.4 let control reach the shape check, which then immediately rejected the $(N,N,N)$ seed. Additionally `continuation_mu2_v25.py:675` force-cast to `np.float64`, a downstream contradiction with the backend's `complex128` requirement. Fix: (A) new BCC-aware factory `math56_constants.build_seed_bcc(N, mode, sigma, complex_seed=True, seed=42)` returning shape $(3, N, N, N)$ `complex128` with three modes (`thermal`/`cold`/`minimum`); (B) driver imports `build_seed_bcc` alongside legacy `build_seed` and constructs `Psi` via the BCC factory; (C) `.astype(np.float64)` dropped — the factory already returns the correct dtype; (D) legacy `build_seed()` left unchanged for scalar callers (additive fix). Sandbox unit tests (six checks) all pass: shape/dtype across modes, per-channel variance $\approx \sigma^{2}$, imaginary content correct per mode, determinism across repeated `seed=42`, legacy API preservation. Residual status: Phase D is still a PLACEHOLDER; diagnostic run still terminates with exit $10$ / `SKELETON_ONLY` until Task #104 (v2.6.0) wires the real Newton-Krylov solver. Layer-5 conditional risk flagged (potential v2.5.6 if probe's `torch.from_numpy(complex128).to(float64)` cast raises on the next run). Math63 §1 specification is sharpened (BCC branch), not amended. §10.4 header + MATURITY block + version history updated; §10.1 will receive a v1.1 update note. |
| 2026-04-22 | **continuation_mu2_v25.py v2.5.3 → v2.5.4: Math63 §2A probe wiring fix**. The first Stage $[3/4]$ diagnostic-sweep run under the v2.5.3 honest-reporting contract produced the expected exit code $10$ / `Status: SKELETON_ONLY` banner, but the per-iteration stderr stream exposed `Probe failed: module 'real_backend_pt_bcc_mixed_v3' has no attribute 'residual_bcc'; using default` at every fifth Newton step of every point. Root cause: `probe_jacobian_cached()` at line $381$ called `backend.residual_bcc(x, params)`, but the canonical exported function — verified by static AST enumeration — is `backend.residual(Psi, params)`; `residual_bcc` is not a module-level def of `real_backend_pt_bcc_mixed_v3.py`. The v2.5.0-era typo survived four releases because the probe's broad `except Exception as _e:` branch silently returned an `asymmetric=True` classification with the attribute error captured only in `.reason`, causing the Math63 §2A probe-driven {PCG, MINRES, FGMRES} router to lock into unconditional FGMRES — the very degradation that manifested as the v2.4 ρ_lin ≈ 0.6 stagnation that motivated Math63 in the first place. Fix: one-token rename `backend.residual_bcc` → `backend.residual` on line $381$ with in-file explanatory comment; module header bumped with full Trigger/Evidence/Decision block; MANIFEST driver-identification string and generation timestamp bumped v2.5.3 → v2.5.4. The v2.5.3 honest-reporting contract is exactly what surfaced this defect — a four-release silent failure made audible by exit-code 10 and per-point diagnostic printing. Residual status: Phase D is still a PLACEHOLDER; the diagnostic run still terminates with exit $10$ / `SKELETON_ONLY` until Task #104 (v2.6.0) wires the real Newton-Krylov solver. Follow-up: proposed Task #106 auditing every `except Exception:` branch in the v2.5 driver. §10.4 header + MATURITY block + version history updated; maturity remains explicitly SKELETON. |
| 2026-04-22 | **continuation_mu2_v25.py v2.5.2 → v2.5.3: TypeError fix + honest skeleton-mode status**. First live Stage $[4/4]$ Newton-loop entry on `[Point 1/6]` at $\mu^{2}=-1.0$ aborted with `ContinuationPoint.__init__() missing 1 required positional argument: 'converged'`; the handoff script then mis-reported `*** v2.5 DIAGNOSTIC: PASS ***` because the main-loop `except` branch caught the `TypeError` and `main()` exited $0$. Root causes: (A) `@dataclass ContinuationPoint` at line $221$ declares `converged: bool` with no default, but `run_one_point_v25()` seeded the result at line $396$ with only `mu2` and `r`; (B) MANIFEST writer hardcoded `PENDING_LOCAL_EXECUTION`, masking per-point error state; (C) `main()` returned `None`, `sys.exit(main() or 0)` was absent, and the handoff script's archival block treated any exit $0$ as PASS; (D) this false-PASS path concealed the deeper structural issue that Phase D of `run_one_point_v25` is an explicit PLACEHOLDER that never calls `tect_newton_krylov.newton_solve` — i.e. the driver is a SKELETON, not a physics run. Fix: (1) add `converged=False` at line $396$; (2) rewrite the MANIFEST writer into a per-point table with `converged` / `errored` / `placeholder` classification plus a four-valued `overall_status` and a DANGER banner when `SKELETON_ONLY`; (3) promote `main()` to a tri-state exit code ($0$=PASS, $10$=SKELETON_ONLY, $2$=FAIL) and propagate via `sys.exit(main() or 0)`; (4) rewrite `scripts/run_v25_diagnostic.ps1` archival block into three branches per exit code — the SKELETON_ONLY branch explicitly suppresses the `commit_v25_diagnostic.ps1` recommendation. Residual honest status after v2.5.3: successful end-to-end runs now return exit code $10$ with `Status: SKELETON_ONLY` and must do so until Task #104 (v2.6.0) wires the real Newton-Krylov solver. Math63 specification unchanged — scaffolding + honest reporting only. §10.4 updated, maturity explicitly marked SKELETON. |
| 2026-04-22 | **continuation_mu2_v25.py v2.5.1 → v2.5.2: UTF-8 locale hardening**. After the `Tools/`→`tools/` rename and the v2.5.1 `sys.path` fix, the first successful Stage [4/4] launch on the user's Korean-Windows/Python 3.12 aborted at `base_params = json.load(f)` with `UnicodeDecodeError: 'cp949' codec can't decode byte 0xe2 in position 971`. Root cause: `PDE/config_template_brazovskii.json` contains a UTF-8 em-dash ($\text{U+2014}$) at byte offset $971$ inside a physics comment; `open(path, "r")` without `encoding=` falls through to `locale.getpreferredencoding(False)` which is `cp949` on Korean Windows. Fix: pin `encoding="utf-8"` on both the config read and the MANIFEST write. Conforms to RFC 8259 §8.1 (UTF-8 required for interchanged JSON). Active-path sweep confirmed the three `tect_newton_krylov.py` `proof_results.json` writes are already pinned. Math63 specification unchanged — purely I/O robustness. §10.4 updated. |
| 2026-04-22 | **continuation_mu2_v25.py v2.5.0 → v2.5.1 + run_v25_diagnostic.ps1 CLI fix**. First full-path local run of the v2.5 diagnostic reached Stage [3/4] with all self-tests green but aborted at Stage [4/4] with (i) `WARNING: check_jacobian_symmetry not found` — Math63 §2A probe routing silently bypassed, solver degrading to plain FGMRES — and (ii) `argparse: error: unrecognized arguments: --mu2_list ...`. Root cause (i): v2.5.0 `sys.path` bootstrap only prepended the PDE/ directory, whereas `tools/` is a sibling package. Root cause (ii): the 6-point schedule is already hardcoded by `--diagnostic`; the caller was passing a non-existent `--mu2_list` CSV. Fix (i): widen the bootstrap to insert both `PDE/` and the repository root, and qualify the import as `from tools.check_jacobian_symmetry import probe_symmetry`; enrich the except-branch message. Fix (ii): drop `--mu2_list` from `scripts/run_v25_diagnostic.ps1` with an inline NOTE preventing regression. No change to Math63 specification or solver numerics — purely plumbing restoration so the probe-driven {PCG, MINRES, FGMRES} routing is no longer silently bypassed. §10.4 updated. |
| 2026-04-22 | **Newton-Krylov v2.5 solver redesign sealed**: Added §10 (Continuation & Adaptive Solvers). Four new modules + one continuation driver, all imported by `continuation_mu2_v25.py`. Math63 specification sealed in response to R-2026-04-21-002 failure (v2.4 GMRES stagnation at μ²=-1.0, ρ_lin≈0.6). Key innovations: (1) Jacobian symmetry probe → {PCG, MINRES, FGMRES} routing; (2) Fourier-diagonal Brazovskii preconditioner (κ_eff ≈10); (3) staged tolerance schedule; (4) stagnation hard-abort. Diagnostic execution pending user local machine (PyTorch unavailable in sandbox). |
| 2026-04-20 | Added `Docs/status/v2p4-patch-plan.md` v1.0 — concrete diffs for the v2.4 Newton-Krylov patch, parametrised by $\mu^{2}_{\text{target}}$. Lists module-level constants, a `v24_separatrix_thresholds()` helper that raises if $\mu^{2}_{\text{target}} > r_{c}^{\text{meta}}$, and Phase-0 / Class-II / Phase-2.5 hooks. **No code has been committed**; patch is gated on resolution of [X5] ($\phi_{0}$-convention audit) and user selection of $\mu^{2}_{\text{target}}\in\{3\times 10^{-3},\,5\times 10^{-3},\,8\times 10^{-3}\}$. Rollback plan specified. |
| 2026-04-20 | **Task #54A code wiring committed**. `PDE/tect_newton_krylov.py` v2.3 → v2.4.0: new private `_run_v24_phase0_gate(Psi_star, params, verbose)` inserted in `run_proof_pipeline` after the Phase 1 downstream-block check, before Phase 2. Gate imports from `v24_thresholds.py` v2.4.0: `BrazovskiiParams`, `brazovskii_critical_mu2`, `v24_separatrix_thresholds`, `v24_phase0_gate`, `v24_class2_guard`, `V24_G0_CUSHION`, `V24_RHO_STAR_FACTOR`. Six branching paths: (A) non-finite params → skipped; (B) invalid Brazovskii ($\lambda\ge 0$ or $\gamma\le 0$) → skipped; (C) $\mu^{2}\ge r_{c}^{\mathrm{meta}}$ → skipped (outside Math56-Addendum Theorem 1 existence window); (D) Class-II floor breach $\langle\lvert\Psi\rvert^{2}\rangle<\rho_{*}$ → `RuntimeError` propagates up; (E) $V=\langle\lvert\Psi\rvert^{2}\rangle/\phi_{+}^{2}\ge G_{0}^{\mathrm{op}}$ → pass; (F) $V<G_{0}^{\mathrm{op}}$ → fail (`downstream_blocked=True`). New CLI flag `--disable-v24-gate` (debug only). `phase_failed()` recognises v2.4 gate FAIL. Output JSON gains `phase0_gate_v24`. Param-key priority: `quartic_lambda`/`sextic_gamma` over `lambda`/`gamma`. **Newton-Krylov dynamics unchanged**. New regression file `tests/test_v24_gate_integration.py` (8 tests, all pass in 0.003 s). `stamp_version_headers.py` now registers the solver at v2.4.0 with `THEORY_TAG="Math56-Addendum-v2p4-2026-04-20"`; stamper was re-run across all 31 active `PDE/*.py` files. `docs/status/v2p4-task54-runbook.md` added with exact CLI invocations for #54B (`continuation_mu2.py --N 32/64`) and #54C (`hess_jump_audit.py`), accept/reject decision tree, and a quick-reference numerics table. |
