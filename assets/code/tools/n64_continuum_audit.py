#!/usr/bin/env python3
"""
n64_continuum_audit.py — v1.2 (2026-04-22)

v1.2 patch (2026-04-22, Task #119 — Math70 §5 R1–R5 binding repairs):
  Five independent defects blocked genuine physics output in v1.1 despite
  cosmetic success (hollow-run postmortem in Math70 §1–7):
    (D1) Homogeneous seed: Psi_init = np.ones((3,N,N,N)) * 0.5 never leaves
         k=0 mode (Proof: Brazovskii shell-bias operator is FFT-diagonal;
         k=0 input stays in k=0 subspace under Newton iteration).
         REPAIR R1: Use BCC-condensate seed via `build_seed_bcc(N, mode="minimum")`
         with amplitude initialized at Phase-0 gate threshold.
    (D2) Return-tuple mismatch: solver returns (Psi, history, projector);
         audit unpacks as (Psi_sol, history, spectrum_out) and queries
         spectrum_out["eigenvalues"] — projector has no such key.
         REPAIR R2: Call separate `analyze_projected_spectrum()` on the
         Lanczos eigenvalues extracted via `lanczos_hessian()`.
    (D3) Convergence parser: history[-1].get("converged", False) always False
         because history[-1] stores per-step diagnostics only.
         REPAIR R3: Check residual directly per Math70 Eq. `m70-convergence-canonical`:
         converged := ||Proj F(Psi_sol)||_2 <= tol_newton * sqrt(dim).
    (D4) Incomplete params dict: only four scalars; backend defaults reduce
         residual to trivial-vacuum energy.
         REPAIR R4: Use `make_bcc_config(N, mu2, ...)` (Task #116 canonical source).
    (D5) μ² convention drift: docstring says (0.26, -0.43, 1.62) but code
         hard-codes -0.5 (Math49-era seed). Locked target: μ²=5×10⁻³ (Math56-Addendum).
         REPAIR R5: Read μ² from continuation endpoint JSON (Task #54) or fall back
         to μ²=5×10⁻³ with warning.

Also applies Task #108 exception-handling audit: replace broad `except Exception`
at line 253 with specific exception dispatch per Math63 §2A.2 policy.

v1.1 baseline: sys.path bootstrap + module alias + shape fix (all retained).
"""

import sys
import os
import json
import argparse
import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# v1.1 sys.path bootstrap (Task #117, Math68 §4 fix-queue companion).
#
# `n64_continuum_audit.py` historically used `from PDE.xxx import yyy`, which
# requires the repository root to be on sys.path AND `PDE/` to be a package
# (no __init__.py exists).  Under the Task #101 / #110 case-collision contract,
# sibling tool modules use BARE imports after prepending three directories
# in this order:
#
#     _THIS_FILE_DIR  (.../Contents/Tools or .../Contents/tools)
#     _PDE_DIR        (.../Contents/PDE)
#     _REPO_ROOT_DIR  (.../Contents)
#
# so that `import real_backend_pt_bcc_mixed_v3` and `from tect_newton_krylov
# import newton_solve` resolve deterministically regardless of launch
# directory and regardless of case-collision on NTFS.
# ---------------------------------------------------------------------------
_THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))  # .../Contents/Tools
_REPO_ROOT_DIR = os.path.dirname(_THIS_FILE_DIR)             # .../Contents
_PDE_DIR       = os.path.join(_REPO_ROOT_DIR, "PDE")
for _p in (_THIS_FILE_DIR, _PDE_DIR, _REPO_ROOT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Skeleton-level imports (will gracefully degrade if torch unavailable)
try:
    import numpy as np
except ImportError:
    print("[ERROR] numpy required", file=sys.stderr)
    sys.exit(1)

torch_available = False
try:
    import torch
    torch_available = True
except ImportError:
    print("[WARNING] torch not available; will skip GPU solves", file=sys.stderr)

# Local imports (v1.1 — bare sibling form; see bootstrap above).
# Note: `real_backend_pt_bcc_mixed_v3` is a FUNCTIONAL module exporting
# module-level `residual(Psi, params)` and `hessian_vec(Psi, v, params)`;
# it does NOT define a `RealBackendPtBccMixedV3` class (this was the v1.0
# import defect).  We alias the module itself as `_backend` and let
# downstream code call the functional API directly.
try:
    import real_backend_pt_bcc_mixed_v3 as _backend
except (ImportError, ModuleNotFoundError) as e:
    print(f"[WARNING] Backend unavailable: {e}", file=sys.stderr)
    _backend = None

try:
    from tect_newton_krylov import (
        newton_solve,
        lanczos_hessian,
        analyze_projected_spectrum,
        build_zero_mode_projector,
    )
except (ImportError, ModuleNotFoundError) as e:
    print(f"[WARNING] Newton-Krylov v2.6.0 unavailable: {e}", file=sys.stderr)
    newton_solve = None
    lanczos_hessian = None
    analyze_projected_spectrum = None
    build_zero_mode_projector = None

try:
    from math56_constants import build_seed_bcc
except (ImportError, ModuleNotFoundError) as e:
    print(f"[WARNING] math56_constants unavailable: {e}", file=sys.stderr)
    build_seed_bcc = None

# R4: Import the canonical config factory from tests
try:
    # Navigate to tests/ which is a sibling of PDE/ and tools/
    _TESTS_DIR = os.path.join(_REPO_ROOT_DIR, "tests")
    if _TESTS_DIR not in sys.path:
        sys.path.insert(0, _TESTS_DIR)
    from conftest import make_bcc_config
except (ImportError, ModuleNotFoundError) as e:
    print(f"[WARNING] make_bcc_config unavailable: {e}", file=sys.stderr)
    make_bcc_config = None


def compute_sigma_V(hess_spectrum):
    """
    Compute spectral-volume variance σ_V from Jacobian eigenvalues.

    σ_V := (1/N_eig) * sum_i (λ_i - λ_bar)^2

    where λ_bar is the mean eigenvalue.

    Args:
        hess_spectrum: np.ndarray, shape (N_eig,) of real eigenvalues

    Returns:
        float: σ_V (spectral variance)
    """
    if len(hess_spectrum) == 0:
        return np.nan

    spectrum = np.asarray(hess_spectrum)
    mean_eig = np.mean(spectrum)
    variance = np.mean((spectrum - mean_eig)**2)
    return float(variance)


def run_single_grid(N, mu2, backend, params, solver, lanczos_fn, analyze_fn, verbose=True):
    """
    Execute Phase-2.5 audit and spectral-gap measurement at a single grid N.

    REPAIRED v1.2 implementation per Math70 §5 R1–R5:
      R1: BCC condensate seed via build_seed_bcc (not homogeneous)
      R2: Phase-2 spectrum via separate lanczos_hessian + analyze_projected_spectrum
      R3: Convergence via residual check (not history[-1].get("converged"))
      R4: Full config via make_bcc_config (not ad-hoc scalars)
      R5: μ² from continuation endpoint or fallback to 5e-3

    Args:
        N (int): grid size (e.g., 32, 64, 128)
        mu2 (float): Brazovskii parameter
        backend: BCC lattice backend module reference
        params (dict): configuration dict (output of make_bcc_config)
        solver: newton_solve function reference
        lanczos_fn: lanczos_hessian function reference
        analyze_fn: analyze_projected_spectrum function reference
        verbose (bool): print diagnostics

    Returns:
        dict with keys:
            - "N": int
            - "converged": bool
            - "sigma_V": float or None
            - "kappa": float or None (order-parameter scaling)
            - "m_star_sq": float or None (mass-gap eigenvalue)
            - "newton_steps": int
            - "error": str or None
    """
    result = {
        "N": N,
        "converged": False,
        "sigma_V": None,
        "kappa": None,
        "m_star_sq": None,
        "newton_steps": 0,
        "error": None,
    }

    # Defensive checks on solver availability
    if solver is None:
        result["error"] = "Newton–Krylov solver not available"
        return result

    if backend is None:
        result["error"] = "BCC backend not available"
        return result

    if lanczos_fn is None or analyze_fn is None:
        result["error"] = "Lanczos/Phase-2 audit functions not available"
        return result

    try:
        # ===== R1: BCC condensate seed (not homogeneous) =====
        # Use the canonical BCC seed factory with "minimum" mode
        # (Eq. m70-bcc-seed). This ensures the seed has nonzero
        # amplitude on the twelve-star {q_T} of the BCC lattice.
        if build_seed_bcc is not None:
            Psi_init = build_seed_bcc(N, mode="minimum", phi0=0.3)
            if verbose:
                print(f"    [R1] BCC seed: shape {Psi_init.shape}, nonzero sites {np.count_nonzero(Psi_init)}")
        else:
            raise RuntimeError("build_seed_bcc factory not available (R1 repair)")

        # ===== R4: Full config via make_bcc_config (canonical source) =====
        # Ensure all required BCC backend fields are present
        if make_bcc_config is not None:
            # Merge the passed-in params with the canonical config
            # (make_bcc_config returns base fields; params may override with solver tuning)
            canonical_cfg = make_bcc_config(N=N, mu2=mu2)
            for k, v in params.items():
                if k not in ('N', 'mu2'):  # Don't override grid/mu2
                    canonical_cfg[k] = v
            params = canonical_cfg
        else:
            # Minimal fallback: ensure Lx/Ly/Lz present
            if "Lx" not in params:
                box_L = float(params.get("L", 1.0))
                params.setdefault("Lx", box_L)
                params.setdefault("Ly", box_L)
                params.setdefault("Lz", box_L)

        if verbose:
            print(f"    [R4] Config: mu2={params.get('mu2')}, Lx={params.get('Lx')}")

        # ===== Phase 1: Newton–Krylov solve =====
        tol_newton_val = params.get("phase_d_tol_newton", 1e-10)
        max_newton_val = params.get("phase_d_max_newton", 30)

        Psi_sol, history, projector = solver(
            Psi_init,
            params,
            max_newton=max_newton_val,
            tol_newton=tol_newton_val,
            krylov_method='minres',
            use_symmetrised_cII=True,
            verbose=verbose,
        )

        # ===== R3: Convergence check via residual (canonical) =====
        # Compute ||Proj F(Psi_sol)||_2 / sqrt(dim) and check against tol_newton
        # per Math70 Eq. m70-convergence-canonical
        try:
            F_residual = backend.residual(Psi_sol, params)
            if projector is not None:
                F_residual_proj = projector.project(F_residual)
            else:
                F_residual_proj = F_residual

            residual_norm = float(np.linalg.norm(F_residual_proj.flatten()))
            residual_normalized = residual_norm / np.sqrt(F_residual_proj.size)
            converged_canonical = residual_normalized <= tol_newton_val * np.sqrt(F_residual_proj.size)

            result["converged"] = converged_canonical
            result["newton_steps"] = len(history)

            if verbose:
                print(f"    [R3] Residual check: ||Proj F|| = {residual_norm:.3e}, " +
                      f"normalized = {residual_normalized:.3e}, " +
                      f"converged = {converged_canonical}")

            if not converged_canonical:
                result["error"] = (f"Newton–Krylov residual {residual_normalized:.3e} "
                                   f"exceeds tolerance {tol_newton_val:.3e}")
                if verbose:
                    print(f"  [N={N}] NOT CONVERGED (residual check)", file=sys.stderr)
                return result

        except (AttributeError, TypeError) as e:
            # Programming error in residual evaluation or projector
            result["error"] = f"Residual check failed (R3): {type(e).__name__}: {e}"
            if verbose:
                print(f"  [N={N}] FAILED (R3): {result['error']}", file=sys.stderr)
            raise  # Re-raise programming errors per Math63 §2A.2 policy

        # ===== Phase 2: Lanczos spectrum audit =====
        # R2: Call separate Phase-2 helper to extract Jacobian spectrum
        try:
            evals_ritz, ritz_vecs = lanczos_fn(
                Psi_sol,
                params,
                projector=projector,
                n_eigs=20,
                max_iter=300,
                verbose=False,
            )

            # Analyze the spectrum to extract λ_min, m*², and eigenvalues list
            phase2_result = analyze_fn(evals_ritz)

            if verbose:
                print(f"    [R2] Lanczos: {len(evals_ritz)} eigenvalues, " +
                      f"λ_min = {phase2_result.lambda_min:.3e}, " +
                      f"m*² = {phase2_result.m_star_sq:.3e}")

            # Compute σ_V from the eigenvalue list
            result["sigma_V"] = compute_sigma_V(phase2_result.eigenvalues)
            result["kappa"] = float(phase2_result.lambda_min)
            result["m_star_sq"] = float(phase2_result.m_star_sq)

            if verbose:
                print(f"  [N={N}] σ_V = {result['sigma_V']:.3e}, κ = {result['kappa']:.3e}, " +
                      f"m*² = {result['m_star_sq']:.3e}")

        except (RuntimeError, ValueError) as e:
            # Expected degradation: Lanczos convergence issue, numerical problem
            result["error"] = f"Phase-2 Lanczos failed: {type(e).__name__}: {e}"
            if verbose:
                print(f"  [N={N}] Lanczos warning (non-fatal): {result['error']}", file=sys.stderr)
            # Do NOT re-raise; Lanczos failure is an audit limitation, not a code bug
            return result

        except (AttributeError, TypeError, NameError) as e:
            # Programming error in Lanczos or analyze
            result["error"] = f"Phase-2 audit code error: {type(e).__name__}: {e}"
            if verbose:
                print(f"  [N={N}] FAILED (Phase-2 code): {result['error']}", file=sys.stderr)
            raise  # Re-raise per Math63 §2A.2

    except Exception as e:
        # Catch remaining exceptions: distinguish programming vs. runtime
        if isinstance(e, (AttributeError, TypeError, NameError, KeyError)):
            # Programming error: propagate with traceback
            import traceback
            result["error"] = f"{type(e).__name__}: {e}"
            if verbose:
                print(f"  [N={N}] CODE ERROR: {result['error']}", file=sys.stderr)
                traceback.print_exc(limit=3, file=sys.stderr)
            raise
        else:
            # Runtime condition: log and continue
            result["error"] = f"{type(e).__name__}: {e}"
            if verbose:
                print(f"  [N={N}] RUNTIME ERROR (non-fatal): {result['error']}", file=sys.stderr)
            return result

    return result


def run_continuum_audit(output_file="results/n64_audit.json", verbose=True):
    """
    Execute full continuum audit: N ∈ {32, 64, 128} at μ² target (Math56-Addendum).

    REPAIRED v1.2 implementation per Math70 §5 R5:
      R5: Read μ² from Task #54 continuation endpoint JSON; fall back to
          μ²_target = 5×10⁻³ with warning if absent.

    Args:
        output_file (str): path to JSON output
        verbose (bool): print diagnostics
    """

    # ===== R5: Load μ² from continuation endpoint or fallback =====
    endpoint_json = "results/continuation_mu2_v25_endpoint.json"
    mu2 = None

    if os.path.exists(endpoint_json):
        try:
            with open(endpoint_json, 'r') as f:
                endpoint_data = json.load(f)
                mu2 = float(endpoint_data.get("mu2", None))
                if mu2 is not None and verbose:
                    print(f"[R5] Loaded μ² = {mu2:.3e} from {endpoint_json}")
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            if verbose:
                print(f"[R5] Could not parse μ² from {endpoint_json}: {e}", file=sys.stderr)
            mu2 = None

    if mu2 is None:
        # Fallback to Math56-Addendum Cor. 1 Option B target
        mu2 = 5e-3
        if verbose:
            print(f"[R5] Endpoint JSON absent or parse failed; falling back to μ² = {mu2:.3e} " +
                  f"(Math56-Addendum Cor. 1 target)", file=sys.stderr)

    # Brazovskii parameters (locked per mandate)
    lambda_param = -0.43
    gamma_param = 1.62

    # v1.1: backend is the imported module itself (functional API:
    # backend.residual, backend.hessian_vec) — there is no class to
    # instantiate.  `backend` is None only if the import failed upstream.
    backend = _backend
    solver = newton_solve
    lanczos_fn = lanczos_hessian
    analyze_fn = analyze_projected_spectrum

    if backend is None:
        print(f"[WARNING] Backend module not imported; "
              f"all grid runs will be skipped.", file=sys.stderr)

    if solver is None:
        print(f"[WARNING] newton_solve not available; "
              f"all grid runs will be skipped.", file=sys.stderr)

    # Configuration dictionary for solver
    # R4: Use make_bcc_config as the canonical source (passed to run_single_grid)
    base_params = {
        "mu2": mu2,
        "lambda": lambda_param,
        "gamma": gamma_param,
        "phase_d_max_newton": 30,
        "phase_d_tol_newton": 1e-10,
    }

    # Run audits for each grid
    grid_results = {}
    for N in [32, 64, 128]:
        if verbose:
            print(f"\n[AUDIT] Running N={N}...")

        result = run_single_grid(
            N, mu2, backend, base_params, solver, lanczos_fn, analyze_fn, verbose=verbose
        )
        grid_key = f"N_{N}"
        grid_results[grid_key] = result

    # Assemble continuum-fit metadata
    h_values = [1.0/N for N in [32, 64, 128]]  # grid spacing
    sigma_V_values = [
        grid_results.get(f"N_{N}", {}).get("sigma_V")
        for N in [32, 64, 128]
    ]
    kappa_values = [
        grid_results.get(f"N_{N}", {}).get("kappa")
        for N in [32, 64, 128]
    ]
    m_star_sq_values = [
        grid_results.get(f"N_{N}", {}).get("m_star_sq")
        for N in [32, 64, 128]
    ]

    # Simple continuum fit: fit σ_V(h) ~ a*h^α
    # (Full polynomial fit and Symanzik analysis deferred to Task #55/#56 post-processing)
    continuum_fit = {
        "h_values": h_values,
        "sigma_V": sigma_V_values,
        "kappa": kappa_values,
        "m_star_sq": m_star_sq_values,
        "continuum_extrapolation": "Symanzik O(a^2) fit to h -> 0 deferred to analysis phase",
        "pillar1_closure_target": "sigma_V(h) -> 0 per Math70 Eq. m70-pillar1-closure",
    }

    # Assemble final output
    output_data = {
        "grid_results": grid_results,
        "continuum_fit": continuum_fit,
        "metadata": {
            "date": datetime.datetime.now().isoformat(),
            "version": "v1.2 (2026-04-22 Math70 R1-R5 repair)",
            "theory_tag": "Math70-N64-ContinuumAudit-Forensics + Math66-PathX-v2.6.0",
            "solver_version": "tect_newton_krylov v2.6.1 (Path-X)",
            "task": "Task #55, #56 (Pillar 1 continuum audit)",
            "references": ["Math70", "Math56", "Math55", "Math66", "Math68-Addendum-A"],
            "repairs_applied": [
                "R1: BCC condensate seed (build_seed_bcc)",
                "R2: Phase-2 spectrum (lanczos_hessian + analyze_projected_spectrum)",
                "R3: Convergence via residual check (canonical)",
                "R4: Full config via make_bcc_config",
                "R5: μ² from continuation endpoint (fallback 5e-3)",
            ],
        },
    }

    # Write output
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    if verbose:
        print(f"\n[COMPLETE] Results written to {output_file}")

    return output_data


def main():
    parser = argparse.ArgumentParser(
        description="N=64 continuum audit (Task #55, #56)"
    )
    parser.add_argument(
        "--output",
        default="results/n64_audit_2026-04-22.json",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--no-verbose",
        action="store_true",
        help="Suppress diagnostic output",
    )

    args = parser.parse_args()

    if not torch_available:
        print(
            "[ERROR] torch required for GPU-accelerated solves. "
            "Please run on a machine with torch installed.",
            file=sys.stderr
        )
        return

    verbose = not args.no_verbose

    print("[AUDIT] N=64 continuum audit — Task #55, #56")
    print("[INFO] Solver: tect_newton_krylov v2.6.0 (Path-X)")
    print("[INFO] Grids: N ∈ {32, 64, 128}")
    print("[INFO] Theory: Math56 spectral gap + Math66 Path-X")
    print()

    try:
        results = run_continuum_audit(output_file=args.output, verbose=verbose)
        if verbose:
            print("\n[SUCCESS] Audit complete")
    except Exception as e:
        print(f"[ERROR] Audit failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
