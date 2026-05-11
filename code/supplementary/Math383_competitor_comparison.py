#!/usr/bin/env python3
# =====================================================================
# Math383_competitor_comparison.py  v1.0 (2026-05-11)
#
# Numerical verification of Math383 §1-4 1-mode analytical claim:
#   F_BCC < F_FCC < F_HEX < F_lamellar
# at canonical TECT parameters (mu^2, lam, gam) = (-1, -0.43, +1.62)
# AND at Math82-AddH operating point mu^2 = +0.005.
#
# For each crystalline structure Lambda, generate the appropriate
# equal-amplitude seed, run Math376 v3 L-BFGS-B to convergence,
# extract F_converged, compare against BCC.
#
# Pre-registered PASS criterion: F_BCC < F_Lambda for all
# Lambda in {FCC, HEX, lamellar} at both operating points.
#
# Usage:
#   python -u Codes/supplementary/Math383_competitor_comparison.py \
#       --mu2 -1.0 --N 32 --converge-iters 1000 --eigs 30 \
#       --lattices BCC FCC HEX lamellar \
#       --out-dir Runs/math383
#
# Lattice wavevector definitions (all at shell |q| = q0):
#   BCC      6 cosines: (1,1,0)/sqrt(2), (1,-1,0)/sqrt(2),
#                       (1,0,1)/sqrt(2), (1,0,-1)/sqrt(2),
#                       (0,1,1)/sqrt(2), (0,1,-1)/sqrt(2)
#   FCC      4 cosines: (1,1,1)/sqrt(3), (1,1,-1)/sqrt(3),
#                       (1,-1,1)/sqrt(3), (-1,1,1)/sqrt(3)
#   HEX      3 cosines: (1, 0, 0), (-1/2, sqrt(3)/2, 0),
#                       (-1/2, -sqrt(3)/2, 0)  [in xy-plane]
#   lamellar 1 cosine:  (0, 0, 1)
#
# Per-cosine amplitude A_Lambda = sqrt(phi0^2(Lambda) / (N_modes/2))
# where phi0^2 satisfies the 1-mode quadratic:
#   gamma*K6*x^2 + lam*K4*x + mu^2/2 = 0,  x = phi0^2
#
# K_4, K_6 values (Math383 §2):
#   BCC:      K_4 = 1.0,   K_6 = 2.5
#   FCC:      K_4 = 1.5,   K_6 = 3.5
#   HEX:      K_4 = 2.0,   K_6 = 5.0
#   lamellar: K_4 = 3.0,   K_6 = 10.0
#
# Dependencies: numpy + scipy (sparse.linalg + optimize).
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

Q0_PHYSICAL: float = 0.6801747616
Y_LOCKED: float = 1.0
LAM_LOCKED: float = -0.43
GAM_LOCKED: float = +1.62
Z0_LOCKED: np.ndarray = np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0)

# Structure factors per Math383 §2
LATTICE_DATA = {
    "BCC":      {"n_modes": 6,  "K4": 1.0, "K6": 2.5},
    "FCC":      {"n_modes": 4,  "K4": 1.5, "K6": 3.5},
    "HEX":      {"n_modes": 3,  "K4": 2.0, "K6": 5.0},
    "lamellar": {"n_modes": 1,  "K4": 3.0, "K6": 10.0},
}


def import_math376(repo_root: Path):
    m376_path = repo_root / "Codes" / "supplementary" / "Math376_production_state_hessian.py"
    spec = importlib.util.spec_from_file_location("m376", str(m376_path))
    m376 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m376)
    return m376


def lattice_wavevectors(name: str, q0: float) -> np.ndarray:
    """Return (n_modes, 3) array of wavevectors at shell |q|=q0."""
    if name == "BCC":
        inv_sqrt2 = 1.0 / math.sqrt(2.0)
        qhat = np.array([
            [+1, +1, 0], [+1, -1, 0],
            [+1, 0, +1], [+1, 0, -1],
            [0, +1, +1], [0, +1, -1],
        ], dtype=np.float64) * inv_sqrt2
    elif name == "FCC":
        inv_sqrt3 = 1.0 / math.sqrt(3.0)
        qhat = np.array([
            [+1, +1, +1], [+1, +1, -1],
            [+1, -1, +1], [-1, +1, +1],
        ], dtype=np.float64) * inv_sqrt3
    elif name == "HEX":
        sqrt3_2 = math.sqrt(3.0) / 2.0
        qhat = np.array([
            [1.0, 0.0, 0.0],
            [-0.5,  sqrt3_2, 0.0],
            [-0.5, -sqrt3_2, 0.0],
        ], dtype=np.float64)
    elif name == "lamellar":
        qhat = np.array([[0.0, 0.0, 1.0]], dtype=np.float64)
    else:
        raise ValueError(f"unknown lattice: {name}")
    return q0 * qhat


def deep_amplitude_for_lattice(name: str, mu2: float,
                                lam: float = LAM_LOCKED,
                                gam: float = GAM_LOCKED) -> float:
    """Per-cosine amplitude A from full 1-mode quadratic at given lattice.

    a*x^2 + b*x + c = 0,  x = phi_0^2 = <Psi^2>
    a = gam * K6, b = lam * K4, c = mu^2/2
    A = sqrt(phi_0^2 / (n_modes/2))  (to match Psi = A * sum cos(q_j r))
    """
    data = LATTICE_DATA[name]
    a = gam * data["K6"]
    b = lam * data["K4"]
    c = 0.5 * mu2
    disc = b**2 - 4.0 * a * c
    if disc <= 0:
        return 0.05 * math.sqrt(abs(mu2) + 0.01)
    x_pos = (-b + math.sqrt(disc)) / (2.0 * a)
    if x_pos <= 0:
        return 0.05 * math.sqrt(abs(mu2) + 0.01)
    # phi_0^2 = (n_modes/2) * A^2  =>  A = sqrt(phi_0^2 / (n_modes/2))
    n_modes = data["n_modes"]
    return math.sqrt(x_pos / (n_modes / 2.0))


def construct_seed(name: str, N: int, L: float, A: float, q0: float) -> np.ndarray:
    """Build single-channel real (N,N,N) seed for the named lattice."""
    qvecs = lattice_wavevectors(name, q0)
    dx = L / N
    x = np.arange(N) * dx
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    Psi = np.zeros((N, N, N))
    for q in qvecs:
        Psi += A * np.cos(q[0]*X + q[1]*Y + q[2]*Z)
    return Psi


def run_one_lattice(name: str, mu2: float, N: int, L: float,
                     converge_iters: int, eigs: int, m376):
    """Generate seed, run L-BFGS-B, extract Hessian eigenvalues."""
    A = deep_amplitude_for_lattice(name, mu2)
    Psi_seed = construct_seed(name, N, L, A, Q0_PHYSICAL)

    grid = m376.setup_kspace(N, L)
    params = {
        "r": mu2 + Y_LOCKED * Q0_PHYSICAL**4,
        "Z": -2.0 * Y_LOCKED * Q0_PHYSICAL**2,
        "Y": Y_LOCKED, "lam": LAM_LOCKED, "gam": GAM_LOCKED,
        "q0": Q0_PHYSICAL, "mu2": mu2,
    }

    F_seed = m376.free_energy_canonical(Psi_seed, grid, params)
    print(f"  Seed: A={A:.4f}, F_seed={F_seed:+.4e}, <Psi^2>={(Psi_seed**2).mean():.4e}")

    Psi_conv, F_conv, gnorm_conv = m376.converge_lbfgsb(
        Psi_seed, grid, params, max_iters=converge_iters, f_tol=1e-7, verbose=False)

    print(f"  Post-LBFGSB: F={F_conv:+.4e}, |grad|/sqrt(V)={gnorm_conv:.4e}")
    print(f"               <Psi^2>={(Psi_conv**2).mean():.4e}, max|Psi|={np.abs(Psi_conv).max():.4f}")

    eigs_arr = m376.lowest_eigenvalues(Psi_conv, grid, params, eigs)
    print(f"  lowest 6 eigs: {[f'{e:+.4e}' for e in eigs_arr[:6]]}")

    return {
        "lattice": name,
        "n_modes": LATTICE_DATA[name]["n_modes"],
        "K4": LATTICE_DATA[name]["K4"],
        "K6": LATTICE_DATA[name]["K6"],
        "A_seed": A,
        "F_seed": F_seed,
        "F_converged": F_conv,
        "F_per_V": F_conv / (L**3),
        "grad_norm_final": gnorm_conv,
        "psi2_mean": float((Psi_conv**2).mean()),
        "max_abs_psi": float(np.abs(Psi_conv).max()),
        "eigs_lowest_6": [float(e) for e in eigs_arr[:6]],
        "n_significant_neg": int(np.sum(eigs_arr < -1e-3 * float(np.max(np.abs(eigs_arr))))),
        "n_pos": int(np.sum(eigs_arr > 1e-6 * float(np.max(np.abs(eigs_arr))))),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mu2", type=float, default=-1.0)
    parser.add_argument("--N", type=int, default=32)
    parser.add_argument("--L", type=float, default=62.20036)
    parser.add_argument("--converge-iters", type=int, default=1000)
    parser.add_argument("--eigs", type=int, default=30)
    parser.add_argument("--lattices", nargs="+",
                        default=["BCC", "FCC", "HEX", "lamellar"],
                        choices=list(LATTICE_DATA.keys()))
    parser.add_argument("--out-dir", default="Runs/math383")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    m376 = import_math376(repo_root)

    print("=" * 76)
    print(" Math383 §6 -- BCC vs competitors numerical verification")
    print("=" * 76)
    print(f" Operating point: mu^2 = {args.mu2}, N = {args.N}, L = {args.L}")
    print(f" Lattices: {args.lattices}")
    print(f" Locked params: lam={LAM_LOCKED}, gam={GAM_LOCKED}, Y={Y_LOCKED}, q0={Q0_PHYSICAL}")
    print(f" Solver: L-BFGS-B, max_iters={args.converge_iters}, f_tol=1e-7")

    results = {}
    for name in args.lattices:
        print()
        print("=" * 60)
        print(f" Lattice: {name}  (n_modes={LATTICE_DATA[name]['n_modes']}, "
              f"K4={LATTICE_DATA[name]['K4']}, K6={LATTICE_DATA[name]['K6']})")
        print("=" * 60)
        results[name] = run_one_lattice(name, args.mu2, args.N, args.L,
                                          args.converge_iters, args.eigs, m376)

    print()
    print("=" * 76)
    print(" SUMMARY: F_per_V comparison at mu^2 = {}".format(args.mu2))
    print("=" * 76)
    print(f"  {'Lattice':<10} {'F_converged':>14} {'F/V':>14} {'<Psi^2>':>12} {'|grad|':>10} {'n_neg':>6}")
    for name in args.lattices:
        r = results[name]
        print(f"  {name:<10} {r['F_converged']:>+14.4e} {r['F_per_V']:>+14.4e} "
              f"{r['psi2_mean']:>12.4e} {r['grad_norm_final']:>10.2e} {r['n_significant_neg']:>6d}")

    # Pre-registered verdict
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
            print(f"\n  PRE-REGISTERED VERDICT: PASS — F_BCC is global minimum among tested competitors")
            verdict = "PASS"
        else:
            print(f"\n  PRE-REGISTERED VERDICT: FAIL — at least one competitor has F < F_BCC")
            verdict = "FAIL"
    else:
        verdict = "INDETERMINATE-NO-BCC"

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = {
        "kind": "Math383-competitor-comparison-v1.0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "operating_point": {"mu2": args.mu2, "N": args.N, "L": args.L,
                            "lam": LAM_LOCKED, "gam": GAM_LOCKED,
                            "Y": Y_LOCKED, "q0": Q0_PHYSICAL},
        "lattices_tested": args.lattices,
        "results_per_lattice": results,
        "verdict": verdict,
    }
    out_path = out_dir / f"math383_competitors_mu2_{args.mu2:+.4f}_N{args.N}.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n  Result saved: {out_path}")

    return 0 if verdict == "PASS" else (1 if verdict == "FAIL" else 3)


if __name__ == "__main__":
    sys.exit(main())
