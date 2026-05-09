#!/usr/bin/env python3
# =====================================================================
# Math371_BCC_param_sweep.py — sweep (mu^2, lambda) to find regime where
#                              BCC is local minimum + defect-free
#
# !!! AUDIT-FLAGGED INVALID (2026-05-09, see Math373) !!!
# Inherits Math369's toy free energy (sextic missing, gamma misinterpreted,
# mu^2 and quartic prefactor wrong). The 2D (mu^2, lambda) heatmap therefore
# scans the wrong Hamiltonian and the conclusion ``0/400 cells satisfy
# stability + defect-free => Mechanism (III) must be non-parameter''
# is NOT a property of canonical TECT. Do NOT cite. Corrected
# implementation queued as Math374. Canonical free energy:
# Codes/pde/real_backend_pt_bcc_mixed_v3.py (shell_free_energy).
# Retraction note: Docs/math/TECT-Math373-...RETRACTION...tex.txt
#
# Two questions to answer simultaneously:
#  Q1. In which (mu^2, lambda) region is the simplest 12-mode Hessian
#      positive-semidefinite (no negative eigenvalues)?
#  Q2. Within Q1's region, which parameter regime suppresses
#      Kibble-Zurek defect production below the cosmological threshold?
#
# Output: a 2D parameter map saved to JSON, plus an ASCII heatmap
# in the terminal showing where BCC closure is feasible.
#
# Math note linkage: Math371 (sweep) + Math373 (this script INVALID).
#
# Usage:
#     python -u Codes/supplementary/Math371_BCC_param_sweep.py
#     python -u Codes/supplementary/Math371_BCC_param_sweep.py --N-mu 25 --N-lam 20
#
# Runtime: ~5-10 seconds (analytic sweep; no PDE solving).
# Dependencies: numpy.
# =====================================================================
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def hessian_signature(mu2: float, lam: float, c4_BCC: float = 11.0/8.0,
                       n_modes: int = 12) -> dict:
    """Returns sign of all eigenvalues for the 12-mode equal-amp BCC Hessian.

    Returns dict with 'min_eig', 'max_eig', 'n_neg', 'is_local_min'.
    """
    if lam * c4_BCC == 0.0 or mu2 == 0.0:
        return {"min_eig": np.nan, "max_eig": np.nan, "n_neg": -1,
                 "is_local_min": False, "A0_squared": np.nan}
    A0_squared = abs(mu2) / abs(lam * c4_BCC)
    diag_val = mu2 + 3.0 * lam * c4_BCC * A0_squared
    off_diag = lam * c4_BCC * A0_squared
    H = np.full((n_modes, n_modes), off_diag)
    np.fill_diagonal(H, diag_val)
    eigs = np.linalg.eigvalsh(H)
    n_neg = int(np.sum(eigs < -1e-9))
    return {
        "min_eig": float(np.min(eigs)),
        "max_eig": float(np.max(eigs)),
        "n_neg": n_neg,
        "is_local_min": (n_neg == 0),
        "A0_squared": float(A0_squared),
    }


def kz_defect_density(mu2: float, lam: float, q0: float = 1.0,
                       tau_Q: float = 1.0) -> float:
    """Estimate Kibble-Zurek topological defect density."""
    gamma = 1.62
    xi_squared = 1.0 / max(abs(gamma * q0**2 + mu2), 1e-6)
    xi = np.sqrt(xi_squared)
    xi_hat = xi * tau_Q ** 0.26
    n_defect = xi_hat ** (-3)
    return float(n_defect)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mu2-range", nargs=2, type=float,
                        default=[-1.5, -0.05])
    parser.add_argument("--lam-range", nargs=2, type=float,
                        default=[-1.0, 1.0])
    parser.add_argument("--N-mu", type=int, default=20)
    parser.add_argument("--N-lam", type=int, default=20)
    parser.add_argument("--defect-threshold", type=float, default=1e-3,
                        help="cosmologically allowed n_defect (heuristic)")
    parser.add_argument("--out-dir", default="Runs/math371",
                        help="output directory")
    args = parser.parse_args()

    print("=" * 72)
    print(" Math371 (mu^2, lambda) parameter sweep -- BCC stability + defect map")
    print(" !!! AUDIT-FLAGGED INVALID per Math373 -- toy free energy !!!")
    print("=" * 72)
    print(f" mu^2 range: {args.mu2_range[0]} to {args.mu2_range[1]} ({args.N_mu} pts)")
    print(f" lam  range: {args.lam_range[0]} to {args.lam_range[1]} ({args.N_lam} pts)")

    mu2_grid = np.linspace(*args.mu2_range, args.N_mu)
    lam_grid = np.linspace(*args.lam_range, args.N_lam)

    is_local_min = np.zeros((args.N_mu, args.N_lam), dtype=int)
    n_defect_map = np.zeros((args.N_mu, args.N_lam))
    pillar4_feasible = np.zeros((args.N_mu, args.N_lam), dtype=int)

    for i, mu2 in enumerate(mu2_grid):
        for j, lam in enumerate(lam_grid):
            sig = hessian_signature(float(mu2), float(lam))
            is_local_min[i, j] = 1 if sig["is_local_min"] else 0
            n_d = kz_defect_density(float(mu2), float(lam))
            n_defect_map[i, j] = n_d
            if sig["is_local_min"] and n_d < args.defect_threshold:
                pillar4_feasible[i, j] = 1

    print(f"\n=== Stability map (rows: mu^2 descending, cols: lam ascending) ===")
    print(f"   X = BCC local-min + defect-free  <-  PILLAR 4 CLOSURE FEASIBLE")
    print(f"   M = BCC local-min only (defects too high)")
    print(f"   D = defect-free only (BCC NOT local-min)")
    print(f"   . = neither")
    print()
    print("       lam:  " + "".join(f"{l:+5.2f}" for l in lam_grid[::max(1,args.N_lam//12)]))
    print("           " + "-" * (5 * len(lam_grid[::max(1,args.N_lam//12)])))
    for i, mu2 in enumerate(mu2_grid[::-1]):
        row_idx = args.N_mu - 1 - i
        marks = []
        for j, lam in enumerate(lam_grid):
            if pillar4_feasible[row_idx, j]:
                marks.append('X')
            elif is_local_min[row_idx, j]:
                marks.append('M')
            elif n_defect_map[row_idx, j] < args.defect_threshold:
                marks.append('D')
            else:
                marks.append('.')
        print(f"  mu^2={mu2:+5.2f}: " + "".join(marks))

    n_local_min = int(np.sum(is_local_min))
    n_feasible  = int(np.sum(pillar4_feasible))
    total       = args.N_mu * args.N_lam
    print(f"\n=== Sweep summary ===")
    print(f"  BCC local-min cells:   {n_local_min}/{total} ({100*n_local_min/total:.1f}%)")
    print(f"  Pillar 4 feasible:     {n_feasible}/{total} ({100*n_feasible/total:.1f}%)")

    if n_feasible == 0:
        print(f"\n[X] NO PARAMETER REGIME satisfies both stability AND defect-free.")
        print(f"    (NOTE: this conclusion is INVALID per Math373 -- toy free energy")
        print(f"     used here omits the canonical sextic stabiliser; result tells us")
        print(f"     nothing about the canonical TECT theory. See Math374 for the")
        print(f"     corrected sweep.)")
    else:
        print(f"\n[OK] {n_feasible} feasible (mu^2, lambda) cells found.")
        feasible_indices = np.argwhere(pillar4_feasible == 1)
        center_idx = feasible_indices[len(feasible_indices) // 2]
        ci, cj = int(center_idx[0]), int(center_idx[1])
        print(f"  Sample feasible point: mu^2={mu2_grid[ci]:+.3f}, lambda={lam_grid[cj]:+.3f}")
        print(f"    n_defect = {n_defect_map[ci, cj]:.3e}, A0^2 = "
              f"{hessian_signature(float(mu2_grid[ci]), float(lam_grid[cj]))['A0_squared']:.4f}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "kind": "Math371-param-sweep",
        "audit_status": "INVALID per Math373 (toy free energy)",
        "generated": datetime.now(timezone.utc).isoformat(),
        "parameters": {
            "mu2_range": args.mu2_range, "lam_range": args.lam_range,
            "N_mu": args.N_mu, "N_lam": args.N_lam,
            "defect_threshold": args.defect_threshold,
        },
        "mu2_grid": mu2_grid.tolist(),
        "lam_grid": lam_grid.tolist(),
        "is_local_min": is_local_min.tolist(),
        "n_defect_map": n_defect_map.tolist(),
        "pillar4_feasible": pillar4_feasible.tolist(),
        "summary": {
            "n_local_min": n_local_min,
            "n_feasible": n_feasible,
            "total": total,
        },
    }
    out_path = out_dir / "math371_sweep.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nResult saved: {out_path}")

    return 0 if n_feasible > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
