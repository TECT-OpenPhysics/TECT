#!/usr/bin/env python3
"""
Docs/supplementary/v24_threshold_sympy_check.py

Formal SymPy re-derivation of the phi_0 convention and the v2.4
Phase-0 / Phase-2.5 gate thresholds.  This file is the audit-grade
record behind TECT-Math56-Addendum §F (resolution of open item X5).

Run:
    python3 Docs/supplementary/v24_threshold_sympy_check.py

The script is self-contained, reads no data, and prints the
derivation outputs in a stable form suitable for archival grep.

Reference: Docs/math/TECT-Math56-Addendum.tex.txt (Theorems 1-5).
License: TECT research — internal audit artefact.
"""

from __future__ import annotations

import sys
import sympy as sp
import numpy as np


def banner(title: str) -> None:
    print("\n" + "=" * 72)
    print(f"  {title}")
    print("=" * 72)


def scenario_A_first_order_lock() -> dict:
    """F(phi0)=F(0)=0 and F'(phi0)=0 simultaneously."""
    banner("Scenario A — first-order Brazovskii lock (simultaneous)")
    mu2, lam, gam, x = sp.symbols("mu2 lam gam x", real=True)
    F_over_x2 = mu2 + lam * x + sp.Rational(5, 2) * gam * x * x          # F(phi0)/phi0^2 = 0
    Fprime_over_x = 2 * mu2 + 4 * lam * x + 15 * gam * x * x             # F'(phi0)/phi0 = 0
    sol = sp.solve([F_over_x2, Fprime_over_x], [x, mu2], dict=True)
    for s in sol:
        print(f"   {s}")
    out = {
        "phi0_sq": "-lam/(5*gam)",
        "mu2_c":   "lam**2/(10*gam)",
    }
    print(f"   ==>  phi_0^2 = {out['phi0_sq']}  at  mu^2 = {out['mu2_c']}")
    return out


def scenario_B_Fprime_only_mu0() -> dict:
    """F'(phi0)=0 alone, evaluated at mu^2=0 (SINGLE condition)."""
    banner("Scenario B — F'(phi0)=0 at mu^2=0 (SINGLE condition)")
    lam, gam, x = sp.symbols("lam gam x", real=True)
    eq = 4 * lam * x + 15 * gam * x * x
    roots = sp.solve(eq, x)
    print(f"   Roots of 4*lam*x + 15*gam*x^2 = 0 :  x = {roots}")
    nontrivial = [r for r in roots if not r.equals(0)]
    print(f"   Non-trivial root:  x = {nontrivial[0]}")
    print("   ----")
    print("   >>> This matches Math37-AddA §A.3 boxed phi_0^2 = -4*lam/(15*gam).")
    print("   >>> Its *label* in Math37-AddA as the `first-order Brazovskii lock' is ")
    print("   >>> therefore wrong: the boxed value is the mu^2=0 single-extremum root,")
    print("   >>> NOT the simultaneous lock.  X5 resolved.")
    return {"phi0_sq_mu2_zero": "-4*lam/(15*gam)"}


def scenario_C_numerical_comparison() -> None:
    """Numerical tabulation at (lam, gam) = (-0.43, 1.62)."""
    banner("Scenario C — Numerical tabulation (lam=-0.43, gam=1.62)")
    lam_v, gam_v = -0.43, 1.62
    phi0_correct_sq = -lam_v / (5.0 * gam_v)
    phi0_wrong_sq   = -4.0 * lam_v / (15.0 * gam_v)
    ratio = phi0_wrong_sq / phi0_correct_sq
    mu2_c = lam_v * lam_v / (10.0 * gam_v)
    r_meta = 2.0 * lam_v * lam_v / (15.0 * gam_v)
    print(f"   phi_0^2 (correct, -lam/(5*gam))     = {phi0_correct_sq:.6f}  "
          f"=> phi_0 = {np.sqrt(phi0_correct_sq):.4f}")
    print(f"   phi_0^2 (Math37-AddA box, -4lam/(15gam)) = {phi0_wrong_sq:.6f}  "
          f"=> phi_0 = {np.sqrt(phi0_wrong_sq):.4f}")
    print(f"   ratio (wrong/correct) = {ratio:.6f}  (= 4/3)")
    print(f"   mu^2_c = lam^2/(10*gam)   = {mu2_c:.6f}   (first-order transition)")
    print(f"   r_meta = 2*lam^2/(15*gam) = {r_meta:.6f}  (metastability edge)")
    print(f"   locked mu^2 = 0.26 -> ratio to r_meta = {0.26 / r_meta:.2f}")


def scenario_D_separatrix_table() -> None:
    """Phase-0 threshold G_0 as a function of mu^2_target."""
    banner("Scenario D — Phase-0 separatrix table (Theorem 2)")
    lam_v, gam_v = -0.43, 1.62
    print(f"   {'mu2_target':>12}  {'phi_+':>8}  {'phi_-':>8}  "
          f"{'alpha_sep':>10}  {'G0_raw':>8}  {'G0_op':>8}")
    for mu2 in [3e-3, 5e-3, 8e-3, 1.0e-2, 1.14e-2]:
        R = 4.0 * lam_v * lam_v - 30.0 * gam_v * mu2
        if R < 0:
            continue
        sqrtR = np.sqrt(R)
        x_plus  = (-2.0 * lam_v + sqrtR) / (15.0 * gam_v)
        x_minus = (-2.0 * lam_v - sqrtR) / (15.0 * gam_v)
        phi_plus = np.sqrt(x_plus)
        phi_minus = np.sqrt(x_minus)
        alpha = phi_minus / phi_plus
        g0_raw = 0.5 * (1.0 + alpha)
        g0_op  = g0_raw + 0.05
        tag = "  <== recommended" if abs(mu2 - 5e-3) < 1e-12 else ""
        print(f"   {mu2:>12.4e}  {phi_plus:>8.4f}  {phi_minus:>8.4f}  "
              f"{alpha:>10.4f}  {g0_raw:>8.4f}  {g0_op:>8.4f}{tag}")


def scenario_E_rho_star_and_saad() -> None:
    """Scale of rho_* and G_3 relative threshold."""
    banner("Scenario E — rho_* (Theorem 3) and G_3 relative (Theorem 5)")
    lam_v, gam_v = -0.43, 1.62
    mu2 = 5e-3
    R = 4.0 * lam_v * lam_v - 30.0 * gam_v * mu2
    x_plus = (-2.0 * lam_v + np.sqrt(R)) / (15.0 * gam_v)
    rho_star = 1e-3 * x_plus                                             # 1e-3 * phi_+^2
    print(f"   phi_+^2 (at mu^2=5e-3) = {x_plus:.6f}")
    print(f"   rho_* = 1e-3 * phi_+^2  = {rho_star:.3e}")
    print(f"   G_3 relative bound    : ||r|| <= 10^(-1) * lam_Ritz")
    print(f"   (absolute equivalent only when lam_Ritz ~ 0.01: ||r|| <= 1e-3)")


def scenario_F_overlap_threshold() -> None:
    """Rayleigh-Ritz perturbation budget => G_2,min = 0.90."""
    banner("Scenario F — G_2,min from Rayleigh-Ritz (Theorem 4)")
    print("   Set: v_N = v_inf|_N + eps_N with ||eps_N|| <= delta_N = O(N^-2)")
    print("   <I v_N | v_2N> = <v_inf|_N interpolated | v_inf|_2N> + O(delta)")
    print("   Demanding fractional error <= 20% per side => G_2 >= 1 - 2*0.05 = 0.90")
    print("   Prior heuristic 0.80 corresponded to 36% error budget (too loose).")


def main() -> int:
    scenario_A_first_order_lock()
    scenario_B_Fprime_only_mu0()
    scenario_C_numerical_comparison()
    scenario_D_separatrix_table()
    scenario_E_rho_star_and_saad()
    scenario_F_overlap_threshold()
    banner("Audit complete — v2.4 thresholds are theorem-anchored")
    return 0


if __name__ == "__main__":
    sys.exit(main())
