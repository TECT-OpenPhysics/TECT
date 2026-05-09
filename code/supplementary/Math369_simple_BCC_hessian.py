#!/usr/bin/env python3
# =====================================================================
# Math369_simple_BCC_hessian.py — 12-mode equal-amplitude BCC Hessian
#
# !!! AUDIT-FLAGGED INVALID (2026-05-09, see Math373) !!!
# Toy free energy used here OMITS the canonical sextic stabiliser γΨ⁶/3,
# MISINTERPRETS γ as a gradient coefficient (γ is sextic in canonical),
# uses μ²=-0.7 instead of canonical operating point +0.26, and uses
# (λ/4)Ψ⁴ instead of canonical (λ/2)Ψ⁴. Eigenvalues below tell us
# nothing about the canonical TECT theory. Do NOT cite as evidence
# for or against Math358. Corrected implementation queued as Math374.
# Canonical free energy: Codes/pde/real_backend_pt_bcc_mixed_v3.py
# (shell_free_energy, lines 532-602). Retraction note:
# Docs/math/TECT-Math373-Math372-Sign-Error-Claim-RETRACTION-and-Canonical-Free-Energy-Restoration.tex.txt
#
# Reproduces the simplest Brazovskii-BCC stability check executed in
# Math369 §3 (operator audit acceptance, 2026-05-09).
#
# Purpose: confirm / refute Math358's "BCC = local minimum" claim
#          using the simplest 12-mode equal-amplitude approximation.
#
# Result (this script): 12 NEGATIVE eigenvalues at locked parameters
#                       (μ²=-0.7, λ=-0.43) — does NOT support local-minimum
#                       claim. Either model is wrong, or Math358 was wrong,
#                       or BCC is metastable in this regime.
#
# Math note linkage: Docs/math/TECT-Math369-Operator-Audit-Acceptance-and-Actual-Lanczos.tex.txt
#
# Usage:
#     python -u Codes/supplementary/Math369_simple_BCC_hessian.py
#     python -u Codes/supplementary/Math369_simple_BCC_hessian.py --json out.json
#
# Runtime: < 1 second.
# Dependencies: numpy.
# =====================================================================
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

import numpy as np


def compute_hessian(mu2: float, gamma: float, lam: float,
                    q0: float = 1.0, n_modes: int = 12,
                    c4_BCC: float = 11.0/8.0) -> dict:
    """
    Construct the simplest 12-mode equal-amplitude BCC Hessian and
    diagonalise. Returns dict of result fields.

    Parameters
    ----------
    mu2, gamma, lam : Brazovskii free-energy coefficients (Math82 locked).
    q0 : characteristic wavenumber (sets the BCC lattice scale).
    n_modes : 12 = (110)-family Bragg modes (6 ± pairs).
    c4_BCC : BCC quartic coefficient in equal-amp ansatz (Brazovskii 1975 → 11/8).

    Returns
    -------
    dict with 'A0_squared', 'eigenvalues' (list), 'classification', 'verdict'.
    """
    # Equal-amp BCC stationary point: A0² = -μ²/(λ·c4)
    if lam * c4_BCC == 0.0 or mu2 == 0.0:
        raise ValueError("Cannot compute A0 with zero μ² or λ")
    A0_squared = abs(mu2) / abs(lam * c4_BCC)

    # Hessian (n×n in real-amplitude basis at the BCC fixed point)
    diag_val = mu2 + 3.0 * lam * c4_BCC * A0_squared
    off_diag = lam * c4_BCC * A0_squared
    H = np.full((n_modes, n_modes), off_diag)
    np.fill_diagonal(H, diag_val)

    eigs = np.linalg.eigvalsh(H)

    n_zero = int(np.sum(np.abs(eigs) < 1e-9))
    n_neg  = int(np.sum(eigs < -1e-9))
    n_pos  = int(np.sum(eigs > 1e-9))

    if n_neg == 0:
        verdict = "BCC local-minimum verified (simplest model)"
    elif n_pos == 0:
        verdict = "BCC FULL SADDLE (all directions destabilising)"
    else:
        verdict = f"MIXED: {n_neg} negative, {n_pos} positive — saddle of index {n_neg}"

    return {
        "parameters": {
            "mu2": mu2, "gamma": gamma, "lambda": lam, "q0": q0,
            "n_modes": n_modes, "c4_BCC": c4_BCC,
        },
        "A0_squared": float(A0_squared),
        "A0": float(np.sqrt(A0_squared)),
        "diagonal_value": float(diag_val),
        "off_diagonal_value": float(off_diag),
        "eigenvalues": [float(e) for e in eigs],
        "n_zero_modes": n_zero,
        "n_negative_modes": n_neg,
        "n_positive_modes": n_pos,
        "verdict": verdict,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mu2", type=float, default=-0.7,
                        help="Brazovskii μ² (locked, Math82 default -0.7)")
    parser.add_argument("--gamma", type=float, default=1.62,
                        help="γ coefficient (locked, default 1.62)")
    parser.add_argument("--lam", type=float, default=-0.43,
                        help="λ coefficient (locked, default -0.43)")
    parser.add_argument("--q0", type=float, default=1.0)
    parser.add_argument("--n-modes", type=int, default=12)
    parser.add_argument("--c4-bcc", type=float, default=11.0/8.0)
    parser.add_argument("--json", default="",
                        help="path to write JSON result (e.g. Runs/math369/result.json)")
    parser.add_argument("--sweep-mu2", action="store_true",
                        help="parameter sweep over μ² ∈ [-1.5, -0.05]")
    args = parser.parse_args()

    print("=" * 70)
    print(" Math369 simple BCC Hessian eigenvalue computation")
    print(f" (operator-audit confirmation, 2026-05-09)")
    print("=" * 70)

    if args.sweep_mu2:
        print(f"\nParameter sweep over μ² (locked γ={args.gamma}, λ={args.lam})")
        print(f"{'μ²':>8s}  {'A0²':>10s}  {'min(λ)':>14s}  {'max(λ)':>14s}  {'verdict':>40s}")
        print("-" * 90)
        results = []
        for mu2 in np.linspace(-1.5, -0.05, 30):
            r = compute_hessian(float(mu2), args.gamma, args.lam,
                                 args.q0, args.n_modes, args.c4_bcc)
            min_e = min(r["eigenvalues"])
            max_e = max(r["eigenvalues"])
            short_v = r["verdict"][:38]
            print(f"{mu2:8.4f}  {r['A0_squared']:10.4f}  {min_e:+14.4e}  {max_e:+14.4e}  {short_v:>40s}")
            results.append({"mu2": float(mu2), **r})
        if args.json:
            with open(args.json, "w") as f:
                json.dump({
                    "kind": "Math369-sweep-mu2",
                    "generated": datetime.now(timezone.utc).isoformat(),
                    "results": results,
                }, f, indent=2)
            print(f"\nSweep result saved: {args.json}")
        return 0

    # Single point computation
    r = compute_hessian(args.mu2, args.gamma, args.lam,
                        args.q0, args.n_modes, args.c4_bcc)

    print(f"\nLocked parameters:")
    for k, v in r["parameters"].items():
        print(f"  {k}: {v}")
    print(f"\nEqual-amplitude BCC stationary point: A0² = {r['A0_squared']:.6f}, "
          f"A0 = {r['A0']:.6f}")
    print(f"\nHessian construction:")
    print(f"  diagonal:     {r['diagonal_value']:+.6e}")
    print(f"  off-diagonal: {r['off_diagonal_value']:+.6e}")

    print(f"\nALL {len(r['eigenvalues'])} eigenvalues (sorted ascending):")
    for i, e in enumerate(r["eigenvalues"]):
        if abs(e) < 1e-9:
            tag = "  ← Goldstone (zero)"
        elif e < 0:
            tag = "  ← NEGATIVE (instability!)"
        else:
            tag = ""
        print(f"  λ_{i+1:2d} = {e:+.6e}{tag}")

    print(f"\nClassification: {r['n_zero_modes']} zero, "
          f"{r['n_negative_modes']} negative, {r['n_positive_modes']} positive")
    print(f"\nVerdict: {r['verdict']}")

    if args.json:
        with open(args.json, "w") as f:
            json.dump({
                "kind": "Math369-single-point",
                "generated": datetime.now(timezone.utc).isoformat(),
                "result": r,
            }, f, indent=2)
        print(f"\nResult saved: {args.json}")

    # Exit code: 0 if BCC is local minimum, 1 otherwise
    return 0 if r["n_negative_modes"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
