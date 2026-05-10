#!/usr/bin/env python3
# =====================================================================
# Math376_production_state_hessian.py  v3 (2026-05-09)
#
# v3 change: ADD --solver option {l-bfgs-b, newton-krylov, none}.
# Default switched to 'l-bfgs-b' because Math377 diagnosed NK as
# saddle-prone for this problem class (NK minimises |grad F|^2 which
# does not distinguish minima from saddles; Armijo line search on
# residual norm allows F to INCREASE during a Newton step).
# L-BFGS-B minimises F directly with line search ensuring F decrease,
# so it preserves the deep BCC basin from which the seed starts.
#
# Pre-registered verdicts unchanged from v2.
#
# Usage:
#   # Default L-BFGS-B
#   python -u Codes/supplementary/Math376_production_state_hessian.py \
#       --state Runs/seeds/Psi_BCC_N32_phaseZ.npy --eigs 50
#
#   # Legacy NK (if requested for comparison)
#   python -u Codes/supplementary/Math376_production_state_hessian.py \
#       --state ... --solver newton-krylov --eigs 50
#
#   # Hessian-only on already-converged state (Pathway B v1 mode)
#   python -u Codes/supplementary/Math376_production_state_hessian.py \
#       --state ... --solver none --eigs 50
#
# Dependencies: numpy + scipy (sparse.linalg + optimize).
# =====================================================================
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

Q0_PHYSICAL: float = 0.6801747616
Y_LOCKED: float = 1.0
LAM_LOCKED: float = -0.43
GAM_LOCKED: float = +1.62
Z0_LOCKED: np.ndarray = np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0)


def setup_kspace(N: int, L: float):
    dx = L / N
    k1d = 2.0 * np.pi * np.fft.fftfreq(N, d=dx)
    KX, KY, KZ = np.meshgrid(k1d, k1d, k1d, indexing="ij")
    K2 = KX**2 + KY**2 + KZ**2
    return {"N": N, "L": L, "dx": dx, "dV": dx**3, "K2": K2}


def load_production_state(npy_path: Path):
    arr = np.load(npy_path)
    if arr.ndim == 3 and np.isrealobj(arr):
        Psi_real = arr.astype(np.float64)
    elif arr.ndim == 4 and arr.shape[0] == 3:
        if not np.iscomplexobj(arr):
            arr = arr.astype(np.complex128)
        Psi_real = np.real(np.einsum("a,axyz->xyz", Z0_LOCKED, arr))
    else:
        raise ValueError(
            "Unsupported .npy shape {}; expected (N,N,N) real or "
            "(3,N,N,N) complex128".format(arr.shape))
    meta_path = npy_path.with_suffix(npy_path.suffix + ".meta.json")
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    return Psi_real, meta


def free_energy_canonical(Psi, grid, params):
    r = params["r"]; Z = params["Z"]; Y = params["Y"]
    lam = params["lam"]; gam = params["gam"]
    K2 = grid["K2"]
    Psi_k = np.fft.fftn(Psi)
    grad_sq = (K2 * np.abs(Psi_k)**2).sum() / Psi.size
    lap_sq = ((K2**2) * np.abs(Psi_k)**2).sum() / Psi.size
    F_quad = 0.5 * r * np.sum(Psi**2)
    F_grad = 0.5 * Z * grad_sq
    F_bi = 0.5 * Y * lap_sq
    F_q4 = 0.5 * lam * np.sum(Psi**4)
    F_q6 = (gam / 3.0) * np.sum(Psi**6)
    return float(grid["dV"] * (F_quad + F_grad + F_bi + F_q4 + F_q6))


def free_energy_gradient(Psi, grid, params):
    """delta F / delta Psi(x); gradient of free_energy_canonical w.r.t. Psi."""
    r = params["r"]; Z = params["Z"]; Y = params["Y"]
    lam = params["lam"]; gam = params["gam"]
    K2 = grid["K2"]
    Psi_k = np.fft.fftn(Psi)
    lap_Psi = np.real(np.fft.ifftn(-K2 * Psi_k))
    lap2_Psi = np.real(np.fft.ifftn((K2**2) * Psi_k))
    # Multiply by dV to be the gradient of the discrete-sum F
    return grid["dV"] * (r * Psi - Z * lap_Psi + Y * lap2_Psi
                         + 2.0 * lam * Psi**3 + 2.0 * gam * Psi**5)


def hessian_apply(delta, Psi, grid, params):
    """Hessian-vector product (without the dV prefactor; matches Math374)."""
    r = params["r"]; Z = params["Z"]; Y = params["Y"]
    lam = params["lam"]; gam = params["gam"]
    K2 = grid["K2"]
    delta_k = np.fft.fftn(delta)
    lap_delta = np.real(np.fft.ifftn(-K2 * delta_k))
    lap2_delta = np.real(np.fft.ifftn((K2**2) * delta_k))
    return (r * delta - Z * lap_delta + Y * lap2_delta
            + 6.0 * lam * (Psi**2) * delta
            + 10.0 * gam * (Psi**4) * delta)


def converge_lbfgsb(Psi, grid, params, max_iters, f_tol, verbose=True):
    """L-BFGS-B energy minimisation. Returns converged Psi (real, shape (N,N,N)).

    Minimises F[Psi] directly with line search ensuring F decrease.
    Unlike Newton-Krylov on |grad F|^2, this solver CANNOT escape the
    starting basin to a saddle of higher energy (Math377 lesson).
    """
    try:
        from scipy.optimize import minimize
    except ImportError:
        raise RuntimeError("scipy.optimize required; install via 'pip install scipy --user'")

    N = grid["N"]
    sqrtV = math.sqrt(Psi.size)
    iter_count = [0]
    best_state = {"Psi": Psi.copy(), "F": free_energy_canonical(Psi, grid, params),
                  "gnorm": float("inf"), "iter": -1}

    def F_value(x):
        return free_energy_canonical(x.reshape(N, N, N), grid, params)

    def F_grad(x):
        return free_energy_gradient(x.reshape(N, N, N), grid, params).ravel()

    def callback(xk):
        iter_count[0] += 1
        gnorm = math.sqrt(np.sum(F_grad(xk)**2)) / sqrtV
        F = F_value(xk)
        if F < best_state["F"]:
            best_state["F"] = F
            best_state["gnorm"] = gnorm
            best_state["Psi"] = xk.copy()
            best_state["iter"] = iter_count[0]
        if verbose and (iter_count[0] % 10 == 0 or iter_count[0] <= 5):
            print("    LBFGSB iter {:4d}: F = {:+.6e}, |grad F|/sqrt(V) = {:.4e}".format(
                iter_count[0], F, gnorm))

    if verbose:
        print("    L-BFGS-B: max_iters = {}, f_tol = {:.0e} (gradient inf-norm)".format(
            max_iters, f_tol))
    t0 = time.time()
    # gtol in L-BFGS-B is |grad|_inf; we want |grad|_2/sqrt(V) < f_tol,
    # so set gtol to f_tol * something. Use sqrt(V)*f_tol as a generous proxy.
    res = minimize(
        F_value, Psi.ravel(),
        jac=F_grad,
        method="L-BFGS-B",
        callback=callback,
        options={"maxiter": max_iters, "gtol": f_tol, "ftol": 1e-15,
                 "disp": False},
    )
    elapsed = time.time() - t0
    Psi_final = res.x.reshape(N, N, N)
    F_final = F_value(res.x)
    g_final = F_grad(res.x)
    gnorm_final = math.sqrt(np.sum(g_final**2)) / sqrtV
    if F_final < best_state["F"]:
        best_state["F"] = F_final
        best_state["gnorm"] = gnorm_final
        best_state["Psi"] = res.x.copy()
        best_state["iter"] = iter_count[0]
    if verbose:
        print("    L-BFGS-B: success = {}, message = {}".format(res.success, res.message))
        print("    L-BFGS-B: final F = {:+.6e}, |grad F|/sqrt(V) = {:.4e} ({:.1f} s)".format(
            F_final, gnorm_final, elapsed))
        print("    Best-so-far: F = {:+.6e}, |grad F|/sqrt(V) = {:.4e} (iter {})".format(
            best_state["F"], best_state["gnorm"], best_state["iter"]))
    # Always return best-so-far (it's <= res.x by construction)
    return best_state["Psi"].reshape(N, N, N), best_state["F"], best_state["gnorm"]


def converge_newton_krylov(Psi, grid, params, max_iters, f_tol,
                            inner_maxiter=20, verbose=True):
    """Newton-Krylov on the gradient field. Legacy v2 path; saddle-prone.

    See Math377 for diagnosis. Kept for comparison studies only.
    """
    try:
        from scipy.optimize import newton_krylov, NoConvergence
    except ImportError:
        raise RuntimeError("scipy.optimize required; install via 'pip install scipy --user'")

    N = grid["N"]
    sqrtV = math.sqrt(Psi.size)
    iter_count = [0]
    best_state = {"Psi": Psi.copy(), "gnorm": float("inf"), "iter": -1,
                  "F": free_energy_canonical(Psi, grid, params)}

    def F_residual(Psi_flat):
        g = free_energy_gradient(Psi_flat.reshape(N, N, N), grid, params)
        return g.ravel()

    def callback(Psi_flat, F_value):
        iter_count[0] += 1
        gnorm = math.sqrt(np.sum(F_value**2)) / sqrtV
        F = free_energy_canonical(Psi_flat.reshape(N, N, N), grid, params)
        if gnorm < best_state["gnorm"]:
            best_state["Psi"] = Psi_flat.copy()
            best_state["gnorm"] = gnorm
            best_state["F"] = F
            best_state["iter"] = iter_count[0]
        if verbose and (iter_count[0] % 5 == 0 or iter_count[0] <= 5):
            print("    NK iter {:3d}: F = {:+.6e}, |grad F|/sqrt(V) = {:.4e}".format(
                iter_count[0], F, gnorm))

    if verbose:
        print("    Newton-Krylov (LEGACY, saddle-prone per Math377):")
        print("      max_iters = {}, f_tol = {:.0e}, inner_maxiter = {}".format(
            max_iters, f_tol, inner_maxiter))
    t0 = time.time()
    try:
        sol = newton_krylov(
            F_residual, Psi.ravel(), method="lgmres",
            f_tol=f_tol * sqrtV, maxiter=max_iters,
            inner_maxiter=inner_maxiter, line_search="armijo",
            callback=callback, verbose=False,
        )
        Psi_conv = sol.reshape(N, N, N)
        elapsed = time.time() - t0
        F_final = free_energy_canonical(Psi_conv, grid, params)
        g_final = free_energy_gradient(Psi_conv, grid, params)
        gnorm_final = math.sqrt(np.sum(g_final**2)) / sqrtV
        if verbose:
            print("    NK: converged in {} iters ({:.1f} s)".format(iter_count[0], elapsed))
        return Psi_conv, F_final, gnorm_final
    except NoConvergence:
        if verbose:
            print("    NK: NO CONVERGENCE; using best-so-far at iter {}".format(best_state["iter"]))
        return best_state["Psi"].reshape(N, N, N), best_state["F"], best_state["gnorm"]
    except Exception as exc:
        if verbose:
            print("    NK: FAILED ({}); using best-so-far".format(exc))
        return best_state["Psi"].reshape(N, N, N), best_state["F"], best_state["gnorm"]


def lowest_eigenvalues(Psi, grid, params, n_eigs):
    N = grid["N"]; size = N**3
    try:
        from scipy.sparse.linalg import LinearOperator, eigsh
    except ImportError:
        raise RuntimeError("scipy.sparse.linalg required; install via 'pip install scipy --user'")

    def matvec(v):
        return hessian_apply(v.reshape(N, N, N), Psi, grid, params).ravel()

    op = LinearOperator((size, size), matvec=matvec, dtype=np.float64)
    try:
        eigs = eigsh(op, k=n_eigs, which="SA", return_eigenvectors=False,
                     maxiter=5000, tol=1e-9)
        return np.sort(eigs)
    except Exception as e1:
        print("  SA mode failed ({}); trying shift-invert sigma=-0.001".format(e1))
        try:
            eigs = eigsh(op, k=n_eigs, sigma=-0.001, which="LM",
                         return_eigenvectors=False, maxiter=5000, tol=1e-7)
            return np.sort(eigs)
        except Exception as e2:
            raise RuntimeError("both Lanczos modes failed: SA={}; SI={}".format(e1, e2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True)
    parser.add_argument("--mu2", type=float, default=None)
    parser.add_argument("--lam", type=float, default=LAM_LOCKED)
    parser.add_argument("--gam", type=float, default=GAM_LOCKED)
    parser.add_argument("--Y", type=float, default=Y_LOCKED)
    parser.add_argument("--q0", type=float, default=Q0_PHYSICAL)
    parser.add_argument("--L", type=float, default=None)
    parser.add_argument("--eigs", type=int, default=50)
    parser.add_argument("--solver", choices=["l-bfgs-b", "newton-krylov", "none"],
                        default="l-bfgs-b",
                        help="energy-minimization solver (default: l-bfgs-b; "
                             "newton-krylov is legacy v2; none = Hessian-only at loaded state)")
    parser.add_argument("--converge-iters", type=int, default=500,
                        help="max optimizer outer iters")
    parser.add_argument("--f-tol", type=float, default=1e-6,
                        help="target |grad F|/sqrt(V) tolerance")
    parser.add_argument("--inner-maxiter", type=int, default=20,
                        help="LGMRES inner iters (NK only)")
    parser.add_argument("--save-converged", action="store_true",
                        help="save the converged state as .npy for reuse")
    parser.add_argument("--out-dir", default="Runs/math376")
    parser.add_argument("--out-tag", default=None)
    args = parser.parse_args()

    state_path = Path(args.state)
    if not state_path.exists():
        print("ERROR: state file not found: {}".format(state_path), file=sys.stderr)
        return 2

    print("=" * 76)
    print(" Math376 production-state Hessian (v3 with L-BFGS-B + NK + none solvers)")
    print("=" * 76)
    print(" State file: {}".format(state_path))

    Psi, meta = load_production_state(state_path)
    N = Psi.shape[0]
    if Psi.shape != (N, N, N):
        print("ERROR: post-projection field shape {} not cubic".format(Psi.shape), file=sys.stderr)
        return 2

    mu2 = args.mu2 if args.mu2 is not None else meta.get("mu2", -0.5)
    L = args.L if args.L is not None else meta.get("L", 2.0 * (2*math.pi/args.q0))

    r_eff = mu2 + args.Y * args.q0**4
    Z_eff = -2.0 * args.Y * args.q0**2
    params = {"r": r_eff, "Z": Z_eff, "Y": args.Y,
              "lam": args.lam, "gam": args.gam, "q0": args.q0, "mu2": mu2}

    grid = setup_kspace(N, L)
    print(" Grid: {}^3 = {} points, L = {:.4f}, dx = {:.4f}".format(
        N, N**3, L, grid['dx']))
    print(" Canonical params:")
    print("   mu2 = {:+.6f}     lam = {:+.6f}     gam = {:+.6f}".format(mu2, args.lam, args.gam))
    print("   Y   = {:+.6f}   Z   = {:+.6f}   r   = {:+.6f}".format(args.Y, Z_eff, r_eff))
    print(" Loaded field statistics:")
    print("   <Psi>   = {:+.6e}".format(Psi.mean()))
    print("   <Psi^2> = {:.6e}".format((Psi**2).mean()))
    print("   max|Psi|= {:.6e}".format(np.abs(Psi).max()))
    print(" Solver: {}".format(args.solver))

    print("")
    print("[1/4] Initial state energy + stationarity ...")
    F0 = free_energy_canonical(Psi, grid, params)
    g0 = free_energy_gradient(Psi, grid, params)
    gnorm0 = math.sqrt(np.sum(g0**2) / Psi.size)
    print("   F[Psi_init]              = {:+.6e}".format(F0))
    print("   |grad F|/sqrt(V) initial = {:.4e}".format(gnorm0))

    Psi_for_hessian = Psi
    if args.solver == "none" or args.converge_iters == 0:
        print("")
        print("[2/4] (skipped solver; --solver=none or --converge-iters=0)")
        F_final = F0; gnorm_final = gnorm0
    else:
        print("")
        print("[2/4] Running solver = {} ({} max iters, f_tol = {:.0e}) ...".format(
            args.solver, args.converge_iters, args.f_tol))
        if args.solver == "l-bfgs-b":
            Psi_for_hessian, F_final, gnorm_final = converge_lbfgsb(
                Psi, grid, params, args.converge_iters, args.f_tol, verbose=True)
        elif args.solver == "newton-krylov":
            Psi_for_hessian, F_final, gnorm_final = converge_newton_krylov(
                Psi, grid, params, args.converge_iters, args.f_tol,
                args.inner_maxiter, verbose=True)
        else:
            raise ValueError("unknown solver: {}".format(args.solver))
        print("   Post-solver: F = {:+.6e}, |grad F|/sqrt(V) = {:.4e}".format(F_final, gnorm_final))
        print("   Post-solver: <Psi^2> = {:.6e}, max|Psi| = {:.6e}".format(
            (Psi_for_hessian**2).mean(), np.abs(Psi_for_hessian).max()))
        if F_final > F0 + 1e-9:
            print("   WARNING: F INCREASED from {:+.6e} to {:+.6e} (solver escaped basin!)".format(F0, F_final))

    print("")
    print("[3/4] Stationarity certificate at the configuration used for Hessian:")
    print("   F                      = {:+.6e}".format(F_final))
    print("   |grad F|/sqrt(V)       = {:.4e}".format(gnorm_final))
    if gnorm_final < args.f_tol:
        print("   STATIONARITY: PASS (|grad F|/sqrt(V) < f_tol)")
        stationary = True
    elif gnorm_final < 1e-3:
        print("   STATIONARITY: ACCEPTABLE (|grad F|/sqrt(V) < 1e-3)")
        stationary = True
    elif gnorm_final < 1e-1:
        print("   STATIONARITY: MARGINAL (|grad F|/sqrt(V) in [1e-3, 1e-1])")
        stationary = False
    else:
        print("   STATIONARITY: FAIL (|grad F|/sqrt(V) > 1e-1)")
        stationary = False

    print("")
    print("[4/4] Computing {} lowest Hessian eigenvalues (Lanczos) ...".format(args.eigs))
    try:
        eigs = lowest_eigenvalues(Psi_for_hessian, grid, params, args.eigs)
    except Exception as exc:
        print("")
        print("  ERROR: eigenvalue extraction failed: {}".format(exc))
        return 2

    lam_top = float(np.max(np.abs(eigs)))
    tol_zero = 1e-6 * lam_top
    tol_significant_neg = 1e-3 * lam_top

    print("")
    print("   Lowest {} eigenvalues:".format(args.eigs))
    for i, e in enumerate(eigs):
        if e < -tol_significant_neg: tag = "  <- NEGATIVE (significant)"
        elif abs(e) < tol_zero:      tag = "  <- Goldstone-zero candidate"
        elif e < 0:                   tag = "  <- near-zero negative"
        else:                          tag = ""
        print("     lam_{:3d} = {:+.6e}{}".format(i+1, e, tag))

    n_neg = int(np.sum(eigs < -tol_significant_neg))
    n_near_zero = int(np.sum(np.abs(eigs) < tol_zero))
    n_pos = int(np.sum(eigs > tol_zero))

    print("")
    print("   Classification (tol_zero = 1e-6 * |lam_top| = {:.2e}):".format(tol_zero))
    print("     significant-negative ( < -1e-3*|lam_top| ) : {}".format(n_neg))
    print("     near-zero (Goldstone)                       : {}".format(n_near_zero))
    print("     positive                                    : {}".format(n_pos))

    print("")
    print("=== PRE-REGISTERED VERDICT (CLAUDE.md 6.3.3) ===")
    if not stationary:
        verdict = "INDETERMINATE-NOT-STATIONARY"
        print("  INDETERMINATE: configuration not stationary "
              "(|grad F|/sqrt(V) = {:.2e}).".format(gnorm_final))
        print("  Increase --converge-iters or relax --f-tol.")
    elif n_neg == 0 and n_near_zero >= 3:
        verdict = "PASS"
        print("  PASS: BCC IS a local minimum of canonical Brazovskii F.")
        print("        ({} Goldstone modes + 0 significant negatives at converged state)".format(n_near_zero))
        print("  Math82-AddH BCC stability claim is NUMERICALLY CONFIRMED at this operating point.")
    elif n_neg > 0:
        verdict = "FAIL"
        print("  FAIL: {} eigenvalue(s) below -1e-3*|lam_top| at converged state.".format(n_neg))
        print("  This REFUTES Math82-AddH BCC stability claim at this operating point.")
        print("  Pillar 1 status would revert from T6 to T4 STRONG EVIDENCE.")
    else:
        verdict = "INDETERMINATE-FEW-GOLDSTONES"
        print("  INDETERMINATE: stationary, no significant negatives, but only "
              "{} Goldstone candidates (need >= 3).".format(n_near_zero))

    out_tag = args.out_tag or "{}_{}".format(args.solver.replace("-","_"), state_path.stem)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.save_converged and stationary:
        npy_out = out_dir / "math376_converged_{}.npy".format(out_tag)
        np.save(npy_out, Psi_for_hessian)
        print("  Converged state saved: {}".format(npy_out))
    result = {
        "kind": "Math376-production-state-hessian-v3",
        "generated": datetime.now(timezone.utc).isoformat(),
        "state_path": str(state_path),
        "state_meta": meta,
        "params": params,
        "N": N, "L": L,
        "solver": args.solver,
        "converge_iters_max": args.converge_iters,
        "f_tol_target": args.f_tol,
        "F_initial": F0,
        "grad_norm_initial": gnorm0,
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
    out_path = out_dir / "math376_v3_{}.json".format(out_tag)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print("")
    print("  Result saved: {}".format(out_path))

    return 0 if verdict == "PASS" else (1 if verdict == "FAIL" else 3)


if __name__ == "__main__":
    sys.exit(main())
