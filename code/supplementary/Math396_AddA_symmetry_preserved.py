#!/usr/bin/env python3
# =====================================================================
# Math396_AddA_symmetry_preserved.py  v1.0 (2026-05-11)
#
# Path Z PROPER: symmetry-preserving lattice solver.
#
# Operator directive (2026-05-11):
#   "Path Z 부터 견고하게 정리하자."
#   Math383 §6 numerical FAIL likely an L-BFGS-B manifold-drift
#   artefact, NOT a refutation of BCC global-min in single-mode SMA.
#   This script restricts optimisation to the LATTICE MANIFOLD by
#   construction, with no ability to drift off into mixed structures.
#
# Method
# ------
# For each lattice  Lambda in {BCC, FCC, HEX, lamellar}:
#   (1) Identify first-shell wavevectors {q_j}, j=1..n_modes.
#   (2) Variables: per-mode amplitudes (A_1, ..., A_{n_modes}).
#   (3) Field on the N^3 grid:
#         Psi(r) = sum_j A_j * cos(q_j . r)
#       The field is restricted to the lattice's first shell --
#       it CANNOT drift into modes off the lattice manifold.
#   (4) F(A) = free_energy_canonical(Psi(A))
#       evaluated by direct N^3 quadrature via Math376 v3.
#   (5) Gradient with respect to amplitudes (chain rule):
#         dF/dA_j = sum_x (delta F / delta Psi(x)) * cos(q_j . x) * dx
#       where (delta F / delta Psi) comes from
#       free_energy_gradient(Psi).  IMPORTANT: free_energy_gradient
#       returns dV * (functional derivative), so we MUST divide by dV
#       BEFORE multiplying by cos and summing -- otherwise we get a
#       double-dV. The cleanest form is:
#         dF/dA_j = sum_x grad_disc(x) * cos(q_j . x)
#       where grad_disc = free_energy_gradient(Psi) (already has dV
#       inside it as a discrete-sum gradient).
#   (6) L-BFGS-B in n_modes-dim amplitude space (n=6/4/3/1), starting
#       from the analytical SMA equal-amplitude seed (Math383 §1-4).
#   (7) Independence of starting point: also run from a perturbed
#       (non-equal) seed to test whether L-BFGS-B prefers a
#       symmetry-broken minimum on the lattice manifold.
#
# Pre-registered analytical hierarchy (Math383 §1-4, single-mode SMA):
#   F/V(BCC) < F/V(FCC) < F/V(HEX) < F/V(lamellar)
#   driven by structure factors:
#     BCC      K_4=1.0,  K_6=2.5
#     FCC      K_4=1.5,  K_6=3.5
#     HEX      K_4=2.0,  K_6=5.0
#     lamellar K_4=3.0,  K_6=10.0
#   (smaller K_4^2/K_6 -> deeper minimum at fixed mu^2, lam<0, gam>0)
#
# Pre-registered PASS / FAIL criterion (CLAUDE.md §6.3.3):
#   PASS at operating point mu^2 if  F_BCC/V < F_Lambda/V  for all
#   Lambda in {FCC, HEX, lamellar}.
#   FAIL otherwise.
#
# Operating points:
#   mu^2 = -1.0      (post-melt, near-saddle / deep minimum regime)
#   mu^2 = +0.005    (Brazovskii-window, Math82-AddH operating point)
#
# Falsification gate
# ------------------
# If symmetry-preserving SMA at mu^2=-1 produces F_BCC/V > F_lamellar/V,
# this would refute Math383 §1-4 analytics in their own SMA setting,
# which would be a P4-fundamental crisis.  If symmetry-preserving SMA
# REPRODUCES the analytical hierarchy, then Math383 §6 was indeed an
# unconstrained-L-BFGS-B drift artefact, and the question of which
# lattice is the actual TRUE global minimum (multi-shell, off-shell,
# etc.) is a separate, follow-on question.
#
# Usage:
#   python -u Codes/supplementary/Math396_AddA_symmetry_preserved.py \
#       --mu2 -1.0 --N 32 --max-iters 2000 \
#       --out-dir Runs/math396
# =====================================================================
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# Locked TECT canonical parameters (Math60-A..E series, Math82-AddH).
Q0_PHYSICAL: float = 0.6801747616
Y_LOCKED:    float = 1.0
LAM_LOCKED:  float = -0.43
GAM_LOCKED:  float = +1.62
Z0_LOCKED:   np.ndarray = np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0)

# Structure factors per Math383 §2 (Leibler 1980 normalisation).
LATTICE_DATA = {
    "BCC":      {"n_modes": 6,  "K4": 1.0, "K6": 2.5},
    "FCC":      {"n_modes": 4,  "K4": 1.5, "K6": 3.5},
    "HEX":      {"n_modes": 3,  "K4": 2.0, "K6": 5.0},
    "lamellar": {"n_modes": 1,  "K4": 3.0, "K6": 10.0},
}


# ---------------------------------------------------------------------
# Math376 import
# ---------------------------------------------------------------------
def import_math376(repo_root: Path):
    p = repo_root / "Codes" / "supplementary" / "Math376_production_state_hessian.py"
    spec = importlib.util.spec_from_file_location("m376", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------
# Lattice wavevectors (first shell only, |q|=q0)
# ---------------------------------------------------------------------
def lattice_wavevectors(name: str, q0: float) -> np.ndarray:
    """Return (n_modes, 3) array of independent wavevectors at shell |q|=q0.

    Independent here means we do NOT include both +q and -q for a real
    cosine -- one cos(q.r) per mode is sufficient.
    """
    if name == "BCC":
        inv_sqrt2 = 1.0 / math.sqrt(2.0)
        qhat = np.array([
            [+1, +1,  0], [+1, -1,  0],
            [+1,  0, +1], [+1,  0, -1],
            [ 0, +1, +1], [ 0, +1, -1],
        ], dtype=np.float64) * inv_sqrt2
    elif name == "FCC":
        inv_sqrt3 = 1.0 / math.sqrt(3.0)
        qhat = np.array([
            [+1, +1, +1], [+1, +1, -1],
            [+1, -1, +1], [-1, +1, +1],
        ], dtype=np.float64) * inv_sqrt3
    elif name == "HEX":
        s32 = math.sqrt(3.0) / 2.0
        qhat = np.array([
            [ 1.0,  0.0, 0.0],
            [-0.5,  s32, 0.0],
            [-0.5, -s32, 0.0],
        ], dtype=np.float64)
    elif name == "lamellar":
        qhat = np.array([[0.0, 0.0, 1.0]], dtype=np.float64)
    else:
        raise ValueError(f"unknown lattice: {name}")
    return q0 * qhat


# ---------------------------------------------------------------------
# Field-amplitude utilities
# ---------------------------------------------------------------------
def build_field(amps: np.ndarray, qvecs: np.ndarray, N: int, L: float) -> np.ndarray:
    """Construct Psi(r) = sum_j amps[j] * cos(q_j . r) on the (N,N,N) grid."""
    dx = L / N
    x = np.arange(N) * dx
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    Psi = np.zeros((N, N, N), dtype=np.float64)
    for j, q in enumerate(qvecs):
        Psi += amps[j] * np.cos(q[0]*X + q[1]*Y + q[2]*Z)
    return Psi


def cos_basis_grid(qvecs: np.ndarray, N: int, L: float) -> np.ndarray:
    """Pre-compute (n_modes, N, N, N) array of cos(q_j . r) basis fields."""
    dx = L / N
    x = np.arange(N) * dx
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    n = qvecs.shape[0]
    basis = np.zeros((n, N, N, N), dtype=np.float64)
    for j, q in enumerate(qvecs):
        basis[j] = np.cos(q[0]*X + q[1]*Y + q[2]*Z)
    return basis


def amplitude_gradient(Psi: np.ndarray, basis: np.ndarray, m376, grid, params) -> np.ndarray:
    """Return (n_modes,) gradient dF/dA_j by chain rule.

    free_energy_gradient(Psi) = dV * (delta F / delta Psi(x)) -- i.e., the
    gradient of the discrete-sum F w.r.t. the field-vector entries.
    For F as a function of amplitudes A_j with Psi = sum_j A_j * basis_j,
        dF/dA_j = sum_x (dF/dPsi(x)) * basis_j(x)
    where dF/dPsi(x) is the discrete-sum gradient (already has dV).
    Hence dF/dA_j = sum over the spatial grid of the elementwise product.
    """
    grad_disc = m376.free_energy_gradient(Psi, grid, params)  # shape (N,N,N)
    n = basis.shape[0]
    g = np.zeros(n, dtype=np.float64)
    for j in range(n):
        g[j] = float(np.sum(grad_disc * basis[j]))
    return g


# ---------------------------------------------------------------------
# Analytical SMA seed (equal-amplitude phi_0^2 from 1-mode quadratic)
# ---------------------------------------------------------------------
def deep_amplitude_for_lattice(name: str, mu2: float,
                                lam: float = LAM_LOCKED,
                                gam: float = GAM_LOCKED) -> float:
    """Per-cosine amplitude A in equal-amplitude SMA.

    1-mode quadratic in x = phi_0^2 = <Psi^2>:
        gam*K_6 * x^2 + lam*K_4 * x + mu^2/2 = 0
    Take positive real root. Then
        phi_0^2 = (n_modes / 2) * A^2  =>  A = sqrt(phi_0^2 / (n_modes/2))
    """
    data = LATTICE_DATA[name]
    a = gam * data["K6"]
    b = lam * data["K4"]
    c = 0.5 * mu2
    disc = b*b - 4.0*a*c
    if disc <= 0:
        return 0.05 * math.sqrt(abs(mu2) + 0.01)
    x_pos = (-b + math.sqrt(disc)) / (2.0*a)
    if x_pos <= 0:
        return 0.05 * math.sqrt(abs(mu2) + 0.01)
    n_modes = data["n_modes"]
    return math.sqrt(x_pos / (n_modes / 2.0))


# ---------------------------------------------------------------------
# Per-lattice constrained optimisation
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# Pure-numpy backtracking gradient descent (sandbox fallback / no-scipy)
# ---------------------------------------------------------------------
def _numpy_minimize_armijo(F_value, F_grad, x0, max_iters: int,
                            gtol: float = 1e-9, ftol: float = 1e-13,
                            verbose: bool = True, callback=None):
    """Backtracking Armijo line search on amplitude space.

    Used when scipy.optimize is unavailable.  Sufficient for n <= 6 dim.
    Returns dict mimicking scipy's OptimizeResult subset.
    """
    x = np.array(x0, dtype=np.float64).copy()
    F = F_value(x)
    g = F_grad(x)
    success = False
    msg = "max_iters reached"
    last_F = F
    for it in range(max_iters):
        gn = float(np.linalg.norm(g))
        if gn < gtol:
            success = True
            msg = "|grad| < gtol"
            break
        # Steepest descent direction (good enough at n<=6)
        d = -g
        # Armijo line search
        alpha = 1.0
        c1 = 1e-4
        F0 = F
        gd = float(np.dot(g, d))  # should be negative
        for _ in range(50):
            x_try = x + alpha * d
            F_try = F_value(x_try)
            if F_try <= F0 + c1 * alpha * gd:
                break
            alpha *= 0.5
        else:
            msg = "line search failed"
            break
        x = x_try
        F = F_try
        g = F_grad(x)
        if callback is not None:
            callback(x)
        if abs(F - last_F) < ftol * max(abs(F0), 1.0):
            success = True
            msg = "F change < ftol"
            break
        last_F = F
    class _Res:
        pass
    res = _Res()
    res.x = x
    res.fun = F
    res.success = success
    res.message = msg
    res.nit = it + 1
    return res


def run_lattice_constrained(name: str, mu2: float, N: int, L: float,
                              max_iters: int, m376,
                              perturb_seed: bool = False,
                              perturb_strength: float = 0.05,
                              rng_seed: int = 12345,
                              verbose: bool = True):
    """Run amplitude-space L-BFGS-B for one lattice. Returns dict of results."""
    try:
        from scipy.optimize import minimize
        _have_scipy = True
    except ImportError:
        _have_scipy = False
        if verbose:
            print("  [WARN] scipy.optimize unavailable -- using pure-numpy "
                  "backtracking-Armijo fallback.")

    data = LATTICE_DATA[name]
    n_modes = data["n_modes"]
    qvecs = lattice_wavevectors(name, Q0_PHYSICAL)
    A_eq = deep_amplitude_for_lattice(name, mu2)
    amps0 = np.full(n_modes, A_eq, dtype=np.float64)
    if perturb_seed and n_modes > 1:
        rng = np.random.default_rng(rng_seed)
        eps = perturb_strength * abs(A_eq) * rng.standard_normal(n_modes)
        amps0 = amps0 + eps  # perturb to break exact equal-amplitude symmetry

    grid = m376.setup_kspace(N, L)
    params = {
        "r":  mu2 + Y_LOCKED * Q0_PHYSICAL**4,
        "Z": -2.0 * Y_LOCKED * Q0_PHYSICAL**2,
        "Y":  Y_LOCKED, "lam": LAM_LOCKED, "gam": GAM_LOCKED,
        "q0": Q0_PHYSICAL, "mu2": mu2,
    }

    basis = cos_basis_grid(qvecs, N, L)

    iter_count = [0]
    F_history = []

    def F_value(amps_flat):
        Psi = build_field(amps_flat, qvecs, N, L)
        return m376.free_energy_canonical(Psi, grid, params)

    def F_grad(amps_flat):
        Psi = build_field(amps_flat, qvecs, N, L)
        return amplitude_gradient(Psi, basis, m376, grid, params)

    def callback(amps_flat):
        iter_count[0] += 1
        F = F_value(amps_flat)
        F_history.append(F)
        if verbose and (iter_count[0] % 5 == 0 or iter_count[0] <= 3):
            g = F_grad(amps_flat)
            gn = float(np.linalg.norm(g))
            print(f"    iter {iter_count[0]:4d}: F = {F:+.6e}, "
                  f"|grad|_A = {gn:.4e}, A_max = {np.max(np.abs(amps_flat)):.4f}")

    Psi_seed = build_field(amps0, qvecs, N, L)
    F_seed = m376.free_energy_canonical(Psi_seed, grid, params)
    psi2_seed = float((Psi_seed**2).mean())
    if verbose:
        print(f"  Seed amps: {[f'{a:+.4f}' for a in amps0]}")
        print(f"  Seed: F={F_seed:+.4e}, <Psi^2>={psi2_seed:.4e}")

    if _have_scipy:
        res = minimize(
            F_value, amps0,
            jac=F_grad,
            method="L-BFGS-B",
            callback=callback,
            options={"maxiter": max_iters, "gtol": 1e-9,
                     "ftol": 1e-15, "disp": False},
        )
    else:
        res = _numpy_minimize_armijo(F_value, F_grad, amps0, max_iters,
                                       gtol=1e-9, ftol=1e-13,
                                       verbose=verbose, callback=callback)

    amps_final = np.array(res.x, dtype=np.float64)
    Psi_final = build_field(amps_final, qvecs, N, L)
    F_final = m376.free_energy_canonical(Psi_final, grid, params)
    g_final = amplitude_gradient(Psi_final, basis, m376, grid, params)
    gnorm_amp = float(np.linalg.norm(g_final))
    psi2_final = float((Psi_final**2).mean())
    a_mean = float(np.mean(amps_final))
    a_std = float(np.std(amps_final))
    a_rel_std = a_std / max(abs(a_mean), 1e-30)

    if verbose:
        print(f"  Final amps: {[f'{a:+.4f}' for a in amps_final]}")
        print(f"  L-BFGS-B status: success={res.success}, message={res.message}")
        print(f"  Final F = {F_final:+.6e}, F/V = {F_final/L**3:+.6e}")
        print(f"  |grad|_A (amplitude space) = {gnorm_amp:.4e}")
        print(f"  amp mean={a_mean:+.4e}, std={a_std:.4e}, rel std={a_rel_std:.4e}")

    return {
        "lattice": name,
        "n_modes": n_modes,
        "K4": data["K4"], "K6": data["K6"],
        "perturb_seed": perturb_seed,
        "amps_seed": [float(a) for a in amps0],
        "amps_final": [float(a) for a in amps_final],
        "F_seed": float(F_seed),
        "F_converged": float(F_final),
        "F_per_V": float(F_final / L**3),
        "grad_amp_norm": gnorm_amp,
        "amp_mean": a_mean,
        "amp_std": a_std,
        "amp_rel_std": a_rel_std,
        "psi2_mean_seed": psi2_seed,
        "psi2_mean_final": psi2_final,
        "lbfgs_success": bool(res.success),
        "lbfgs_message": str(res.message),
        "n_iterations": int(iter_count[0]),
    }


# ---------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mu2", type=float, default=-1.0)
    parser.add_argument("--N", type=int, default=32)
    parser.add_argument("--L", type=float, default=62.20036)
    parser.add_argument("--max-iters", type=int, default=2000)
    parser.add_argument("--lattices", nargs="+",
                        default=["BCC", "FCC", "HEX", "lamellar"],
                        choices=list(LATTICE_DATA.keys()))
    parser.add_argument("--perturb-seed", action="store_true",
                        help="Perturb starting amps off equal-amplitude axis "
                             "to test for symmetry-breaking minima.")
    parser.add_argument("--perturb-strength", type=float, default=0.05)
    parser.add_argument("--out-dir", default="Runs/math396")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    m376 = import_math376(repo_root)

    print("=" * 76)
    print(" Math396-AddA -- symmetry-preserving SMA solver (Path Z proper)")
    print("=" * 76)
    print(f" Operating point: mu^2 = {args.mu2}, N = {args.N}, L = {args.L}")
    print(f" Lattices: {args.lattices}")
    print(f" Perturb seed: {args.perturb_seed} (strength {args.perturb_strength})")
    print(f" Locked params: lam={LAM_LOCKED}, gam={GAM_LOCKED}, "
          f"Y={Y_LOCKED}, q0={Q0_PHYSICAL}")

    results = {}
    for name in args.lattices:
        print()
        print("=" * 60)
        print(f" Lattice: {name}  (n_modes={LATTICE_DATA[name]['n_modes']}, "
              f"K4={LATTICE_DATA[name]['K4']}, K6={LATTICE_DATA[name]['K6']})")
        print("=" * 60)
        results[name] = run_lattice_constrained(
            name, args.mu2, args.N, args.L, args.max_iters, m376,
            perturb_seed=args.perturb_seed,
            perturb_strength=args.perturb_strength)

    # ----- Analytical SMA prediction (Math383 §1-4) for cross-check -----
    print()
    print("=" * 76)
    print(" ANALYTICAL SMA prediction (Math383 §1-4) at mu^2 = {}".format(args.mu2))
    print(" 1-mode quadratic: gam*K_6 * x^2 + lam*K_4 * x + mu^2/2 = 0,  x = phi_0^2")
    print(" F/V = (mu^2/2) x + (lam/2) K_4 x^2 + (gam/3) K_6 x^3")
    print("=" * 76)
    print(f"  {'Lattice':<10} {'phi_0^2 (x*)':>14} {'F/V (analytic)':>16}")
    analytic_FV = {}
    for name in args.lattices:
        d = LATTICE_DATA[name]
        a = GAM_LOCKED * d["K6"]
        b = LAM_LOCKED * d["K4"]
        c = 0.5 * args.mu2
        disc = b*b - 4.0*a*c
        if disc <= 0:
            analytic_FV[name] = float("nan")
            print(f"  {name:<10} {'NaN':>14} {'(no real root)':>16}")
            continue
        x = (-b + math.sqrt(disc)) / (2.0 * a)
        FV = (args.mu2/2.0)*x + (LAM_LOCKED/2.0)*d["K4"]*x*x + (GAM_LOCKED/3.0)*d["K6"]*x**3
        analytic_FV[name] = FV
        print(f"  {name:<10} {x:>+14.4e} {FV:>+16.6e}")

    print()
    print("=" * 76)
    print(f" SUMMARY: F_per_V comparison (symmetry-preserving SMA), mu^2 = {args.mu2}")
    print("=" * 76)
    print(f"  {'Lattice':<10} {'F_converged':>14} {'F/V':>14} "
          f"{'<Psi^2>':>12} {'|grad|_A':>10} {'a_rel_std':>10}")
    for name in args.lattices:
        r = results[name]
        print(f"  {name:<10} {r['F_converged']:>+14.4e} {r['F_per_V']:>+14.4e} "
              f"{r['psi2_mean_final']:>12.4e} {r['grad_amp_norm']:>10.2e} "
              f"{r['amp_rel_std']:>10.2e}")

    if "BCC" in results:
        F_BCC = results["BCC"]["F_per_V"]
        all_pass = True
        for name in args.lattices:
            if name == "BCC":
                continue
            F_other = results[name]["F_per_V"]
            ok = (F_BCC < F_other)
            print(f"  F_BCC ({F_BCC:+.4e}) < F_{name} ({F_other:+.4e}) ? {ok}")
            if not ok:
                all_pass = False
        if all_pass:
            print("\n  PRE-REGISTERED VERDICT: PASS -- F_BCC global min in SMA")
            verdict = "PASS"
        else:
            print("\n  PRE-REGISTERED VERDICT: FAIL -- competitor deeper in SMA")
            verdict = "FAIL"
    else:
        verdict = "INDETERMINATE-NO-BCC"

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = {
        "kind": "Math396-AddA-symmetry-preserved-SMA-v1.0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "operating_point": {"mu2": args.mu2, "N": args.N, "L": args.L,
                             "lam": LAM_LOCKED, "gam": GAM_LOCKED,
                             "Y": Y_LOCKED, "q0": Q0_PHYSICAL},
        "lattices_tested": args.lattices,
        "perturb_seed": args.perturb_seed,
        "perturb_strength": args.perturb_strength,
        "results_per_lattice": results,
        "verdict": verdict,
    }
    out_path = out_dir / (
        f"math396_AddA_symmetry_mu2_{args.mu2:+.4f}_N{args.N}"
        f"{'_perturb' if args.perturb_seed else ''}.json"
    )
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\n  Result saved: {out_path}")

    # Exit codes: 0=PASS, 1=FAIL, 3=INDETERMINATE
    return 0 if verdict == "PASS" else (1 if verdict == "FAIL" else 3)


if __name__ == "__main__":
    sys.exit(main())
