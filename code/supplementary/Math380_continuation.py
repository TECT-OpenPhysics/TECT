#!/usr/bin/env python3
# =====================================================================
# Math380_continuation.py  v1.0 (2026-05-10)
#
# Math381 audit-driven CLI rewrite of the operator's session script
# math380_v3_continuation.py. Implements continuation-based BCC-state
# tracking from a deep-mu^2 converged state up through arbitrary mu^2
# values, with Math376 v3 L-BFGS-B at each step and a unified verdict
# at the final point.
#
# Replaces (and supersedes) the operator-session one-off
# math380_v3_continuation.py with:
#   - CLI argparse for all parameters
#   - Pluggable solver (l-bfgs-b default, NK or none for comparison)
#   - Reuses Math376's verdict logic instead of duplicating it
#   - Auto-detection of input state shape ((N,N,N) real OR (3,N,N,N) complex)
#   - JSON output annotation with "reduced_model" warning per Math381
#
# Pre-registered verdicts identical to Math376 v3 (CLAUDE.md 6.3.3
# canonical strict-criterion); see Math381 calibration for the
# operator-binding interpretation.
#
# Usage:
#   python -u Codes/supplementary/Math380_continuation.py \
#       --start-state Runs/math376/math376_converged_l_bfgs_b_Psi_BCC_N32_phaseZ.npy \
#       --mu2-steps -1.0 -0.5 -0.1 -0.01 0.005 \
#       --eigs 50 --converge-iters 3000 --f-tol 1e-7 \
#       --out-dir Runs/math380 --out-tag continuation_to_+0p005
#
# Dependencies: numpy + scipy (sparse.linalg + optimize).
# =====================================================================
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# --- Locked canonical defaults (same as Math376 v3) ---
Q0_PHYSICAL: float = 0.6801747616
Y_LOCKED: float = 1.0
LAM_LOCKED: float = -0.43
GAM_LOCKED: float = +1.62
Z0_LOCKED: np.ndarray = np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0)


def import_math376(repo_root: Path):
    """Dynamic import of Math376 v3 module to reuse its solvers + verdict."""
    m376_path = repo_root / "Codes" / "supplementary" / "Math376_production_state_hessian.py"
    if not m376_path.exists():
        raise FileNotFoundError(f"Math376 module not found at {m376_path}")
    spec = importlib.util.spec_from_file_location("m376", str(m376_path))
    m376 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m376)
    return m376


def load_state_with_projection(npy_path: Path) -> np.ndarray:
    """Load a state .npy; auto-detect shape and reduce to single-channel real.

    Supports:
      - (N, N, N) real float64: returned as-is
      - (3, N, N, N) complex128 production format: project onto z0=(1,1,1)/sqrt(3)
    """
    arr = np.load(npy_path)
    if arr.ndim == 3 and np.isrealobj(arr):
        return arr.astype(np.float64)
    elif arr.ndim == 4 and arr.shape[0] == 3:
        if not np.iscomplexobj(arr):
            arr = arr.astype(np.complex128)
        return np.real(np.einsum("a,axyz->xyz", Z0_LOCKED, arr))
    else:
        raise ValueError(
            "Unsupported .npy shape {}; expected (N,N,N) real or "
            "(3,N,N,N) complex128".format(arr.shape))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-state", required=True,
                        help="path to starting .npy state (deep-mu^2 converged)")
    parser.add_argument("--mu2-steps", type=float, nargs="+", required=True,
                        help="sequence of mu^2 values for continuation steps")
    parser.add_argument("--N", type=int, default=None,
                        help="grid size N (default: inferred from start-state shape)")
    parser.add_argument("--L", type=float, default=62.20036,
                        help="box length L (default: 62.20036, N=32 BCC unit cell)")
    parser.add_argument("--lam", type=float, default=LAM_LOCKED)
    parser.add_argument("--gam", type=float, default=GAM_LOCKED)
    parser.add_argument("--Y", type=float, default=Y_LOCKED)
    parser.add_argument("--q0", type=float, default=Q0_PHYSICAL)
    parser.add_argument("--eigs", type=int, default=50)
    parser.add_argument("--solver", choices=["l-bfgs-b", "newton-krylov"],
                        default="l-bfgs-b",
                        help="energy-minimization solver per step")
    parser.add_argument("--converge-iters", type=int, default=3000)
    parser.add_argument("--f-tol", type=float, default=1e-7)
    parser.add_argument("--inner-maxiter", type=int, default=20)
    parser.add_argument("--out-dir", default="Runs/math380")
    parser.add_argument("--out-tag", default=None)
    args = parser.parse_args()

    # Repo root = ../../ from this script
    repo_root = Path(__file__).resolve().parent.parent.parent
    m376 = import_math376(repo_root)

    state_path = Path(args.start_state)
    if not state_path.exists():
        print("ERROR: start state not found: {}".format(state_path), file=sys.stderr)
        return 2

    print("=" * 76)
    print(" Math380 continuation (CLI v1.0; supersedes math380_v3_continuation.py)")
    print("=" * 76)
    print(" Start state: {}".format(state_path))

    psi = load_state_with_projection(state_path)
    N = args.N if args.N is not None else psi.shape[0]
    if psi.shape != (N, N, N):
        print("ERROR: post-projection shape {} not (N,N,N) cubic".format(psi.shape),
              file=sys.stderr)
        return 2

    print(" Grid: {}^3 = {} points".format(N, N**3))
    print(" Box L = {:.4f}, dx = {:.4f}".format(args.L, args.L / N))
    print(" Solver: {}".format(args.solver))
    print(" Continuation: {} steps from mu^2 = {} to {}".format(
        len(args.mu2_steps), args.mu2_steps[0], args.mu2_steps[-1]))
    print(" Locked: lam = {}, gam = {}, Y = {}, q0 = {}".format(
        args.lam, args.gam, args.Y, args.q0))

    # Trajectory tracking
    trajectory = []

    for step_idx, mu2 in enumerate(args.mu2_steps):
        print("")
        print("=" * 60)
        print("Step {}/{}: mu^2 = {}".format(step_idx + 1, len(args.mu2_steps), mu2))
        print("=" * 60)

        grid = m376.setup_kspace(N, args.L)
        params = {
            "r": mu2 + args.Y * args.q0**4,
            "Z": -2.0 * args.Y * args.q0**2,
            "Y": args.Y, "lam": args.lam, "gam": args.gam,
            "q0": args.q0, "mu2": mu2,
        }

        F_pre = m376.free_energy_canonical(psi, grid, params)
        g_pre = m376.free_energy_gradient(psi, grid, params)
        gnorm_pre = float(np.sqrt(np.sum(g_pre**2) / psi.size))
        print("  Pre-step:  F = {:+.6e}, |grad|/sqrt(V) = {:.4e}".format(F_pre, gnorm_pre))

        if args.solver == "l-bfgs-b":
            psi_new, F_post, gnorm_post = m376.converge_lbfgsb(
                psi, grid, params,
                max_iters=args.converge_iters, f_tol=args.f_tol, verbose=False)
        elif args.solver == "newton-krylov":
            psi_new, F_post, gnorm_post = m376.converge_newton_krylov(
                psi, grid, params,
                max_iters=args.converge_iters, f_tol=args.f_tol,
                inner_maxiter=args.inner_maxiter, verbose=False)
        else:
            raise ValueError("unknown solver: {}".format(args.solver))

        print("  Post-step: F = {:+.6e}, |grad|/sqrt(V) = {:.4e}".format(F_post, gnorm_post))
        print("  <Psi^2> = {:.6e}, max|Psi| = {:.4f}".format(
            (psi_new**2).mean(), np.abs(psi_new).max()))

        trajectory.append({
            "step": step_idx + 1,
            "mu2": mu2,
            "F_pre": F_pre, "gnorm_pre": gnorm_pre,
            "F_post": F_post, "gnorm_post": gnorm_post,
            "psi2_mean": float((psi_new**2).mean()),
            "max_abs_psi": float(np.abs(psi_new).max()),
        })
        psi = psi_new

    # ---- Final Hessian extraction at last mu^2 ----
    final_mu2 = args.mu2_steps[-1]
    print("")
    print("=" * 60)
    print("Final Hessian extraction at mu^2 = {}".format(final_mu2))
    print("=" * 60)

    grid = m376.setup_kspace(N, args.L)
    params = {
        "r": final_mu2 + args.Y * args.q0**4,
        "Z": -2.0 * args.Y * args.q0**2,
        "Y": args.Y, "lam": args.lam, "gam": args.gam,
        "q0": args.q0, "mu2": final_mu2,
    }

    print("Computing {} lowest Hessian eigenvalues (Lanczos)...".format(args.eigs))
    eigs = m376.lowest_eigenvalues(psi, grid, params, args.eigs)

    lam_top = float(np.max(np.abs(eigs)))
    tol_zero = 1e-6 * lam_top
    tol_significant_neg = 1e-3 * lam_top

    print("")
    print("Lowest {} eigenvalues:".format(args.eigs))
    for i, e in enumerate(eigs):
        if e < -tol_significant_neg:
            tag = "  <- NEGATIVE (significant)"
        elif abs(e) < tol_zero:
            tag = "  <- Goldstone-zero candidate"
        elif e < 0:
            tag = "  <- near-zero negative (Goldstone noise?)"
        else:
            tag = ""
        print("  lam_{:3d} = {:+.6e}{}".format(i+1, e, tag))

    n_neg = int(np.sum(eigs < -tol_significant_neg))
    n_near_zero = int(np.sum(np.abs(eigs) < tol_zero))
    n_pos = int(np.sum(eigs > tol_zero))

    F_final = trajectory[-1]["F_post"]
    gnorm_final = trajectory[-1]["gnorm_post"]
    stationary = gnorm_final < 1e-3

    print("")
    print("Classification (tol_zero = 1e-6 * |lam_top| = {:.2e}):".format(tol_zero))
    print("  significant-negative ( < -1e-3*|lam_top| ) : {}".format(n_neg))
    print("  near-zero (Goldstone)                       : {}".format(n_near_zero))
    print("  positive                                    : {}".format(n_pos))

    print("")
    print("=== PRE-REGISTERED VERDICT (CLAUDE.md 6.3.3; Math381 calibration applies) ===")
    if not stationary:
        verdict = "INDETERMINATE-NOT-STATIONARY"
        print("  INDETERMINATE: |grad F|/sqrt(V) = {:.2e} > 1e-3".format(gnorm_final))
    elif n_neg == 0 and n_near_zero >= 3:
        verdict = "PASS"
        print("  PASS: BCC IS local minimum at mu^2 = {}.".format(final_mu2))
    elif n_neg > 0:
        verdict = "FAIL"
        print("  FAIL: {} significant-negative eigenvalue(s).".format(n_neg))
    else:
        verdict = "INDETERMINATE-FEW-GOLDSTONES"
        print("  INDETERMINATE: stationary; only {} Goldstone candidates (need >= 3)".format(n_near_zero))
        print("  (Math381 calibration: 6-fold near-zero cluster at lambda << gap may be physical Goldstones with finite-N shift.)")

    # ---- Output ----
    out_tag = args.out_tag or "continuation_{}".format(state_path.stem)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    npy_out = out_dir / "math380_{}_final_state.npy".format(out_tag)
    np.save(npy_out, psi)
    print("\nFinal state saved: {}".format(npy_out))

    result = {
        "kind": "Math380-continuation-CLI-v1.0",
        "reduced_model": True,
        "reduced_model_note": "Inherits Math376 z0-projection + canonical free energy; family/lock/classII penalties NOT included; Math381 calibration applies",
        "generated": datetime.now(timezone.utc).isoformat(),
        "start_state": str(state_path),
        "mu2_steps": args.mu2_steps,
        "N": N, "L": args.L,
        "params_locked": {"lam": args.lam, "gam": args.gam,
                          "Y": args.Y, "q0": args.q0},
        "solver": args.solver,
        "converge_iters_max": args.converge_iters,
        "f_tol_target": args.f_tol,
        "trajectory": trajectory,
        "F_final": F_final,
        "grad_norm_final": gnorm_final,
        "stationary": stationary,
        "eigenvalues": [float(e) for e in eigs],
        "n_significant_neg": n_neg,
        "n_near_zero_goldstone": n_near_zero,
        "n_pos": n_pos,
        "tol_zero": tol_zero,
        "tol_significant_neg": tol_significant_neg,
        "lam_top": lam_top,
        "verdict": verdict,
    }
    json_out = out_dir / "math380_{}_result.json".format(out_tag)
    with open(json_out, "w") as f:
        json.dump(result, f, indent=2)
    print("Result saved: {}".format(json_out))

    return 0 if verdict == "PASS" else (1 if verdict == "FAIL" else 3)


if __name__ == "__main__":
    sys.exit(main())
