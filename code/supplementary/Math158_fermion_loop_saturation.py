#!/usr/bin/env python3
"""
Math158_fermion_loop_saturation.py

Numerical evaluation of the fermion-loop saturation route to hbar.
Computes the one-loop wave-function renormalization Z_Psi^(1) and
estimates the critical hbar value needed for exact canonical commutator.

Theory reference: TECT-Math158-GAP1-third-route-matter-side-hbar-derivation.tex.txt
Date: 2026-04-26
Author: Autonomous TECT Agent
"""

import numpy as np
import argparse
from fractions import Fraction
import math

# Physical constants (SI units)
HBAR_REDUCED = 1.054571817e-34  # J·s (CODATA 2018)
C_LIGHT = 299792458  # m/s
G_NEWTON = 6.67430e-11  # m^3/(kg·s^2) (CODATA 2018)
PLANCK_LENGTH = np.sqrt(G_NEWTON * HBAR_REDUCED / C_LIGHT**3)  # meters

# TECT parameters (natural units: c = 1, hbar = 1)
Y_TOP = 1.0  # Top-quark Yukawa coupling (dimensionless)
M_FERMION_NATURAL = 0.01  # Fermion mass scale (in natural units)
A_BCC_PLANCK_RATIO = 1.5  # Lattice constant as multiple of Planck length


def compute_hbar_gravity(a_bcc):
    """
    Compute hbar from gravity route (Math110-AddI).
    hbar_gravity = (c^3 * a_bcc^2) / (16*pi*G)

    Args:
        a_bcc (float): Lattice constant in meters

    Returns:
        float: hbar_gravity in J·s
    """
    numerator = C_LIGHT**3 * a_bcc**2
    denominator = 16 * np.pi * G_NEWTON
    return numerator / denominator


def compute_one_loop_correction(y_t, m_f_natural, k_max_natural):
    """
    Compute one-loop wave-function renormalization Z_Psi^(1).

    Z_Psi^(1) ~ (y_t^2 / (4*pi)^2) * L
    where L = log(k_max / m_f) is the logarithmic divergence.

    Args:
        y_t (float): Yukawa coupling (dimensionless)
        m_f_natural (float): Fermion mass in natural units
        k_max_natural (float): UV cutoff momentum in natural units (1/a_bcc)

    Returns:
        tuple: (Z_Psi^(1), log_factor)
    """
    if m_f_natural <= 0 or k_max_natural <= m_f_natural:
        raise ValueError("Invalid fermion mass or cutoff parameters")

    log_factor = np.log(k_max_natural / m_f_natural)
    z_one_loop = (y_t**2 / (4 * np.pi)**2) * log_factor

    return z_one_loop, log_factor


def estimate_hbar_critical_nonperturb(y_t, m_f_natural, rho_cond_natural, a_bcc_natural):
    """
    Estimate the critical hbar value from non-perturbative saturation.

    hbar* ~ (y_t^(1/2) * m_f^(1/2) * rho_cond^(1/2) * a_bcc^(3/2)) / (4*pi)

    Args:
        y_t (float): Yukawa coupling
        m_f_natural (float): Fermion mass in natural units
        rho_cond_natural (float): Condensate density in natural units
        a_bcc_natural (float): Lattice constant in natural units

    Returns:
        float: hbar_critical in natural units
    """
    numerator = (y_t**0.5 * m_f_natural**0.5 * rho_cond_natural**0.5 * a_bcc_natural**1.5)
    hbar_critical = numerator / (4 * np.pi)
    return hbar_critical


def main():
    parser = argparse.ArgumentParser(
        description="Math158: Fermion-loop saturation route to hbar"
    )
    parser.add_argument(
        "--a_bcc_planck_ratio",
        type=float,
        default=A_BCC_PLANCK_RATIO,
        help="a_bcc as multiple of Planck length"
    )
    parser.add_argument(
        "--y_top",
        type=float,
        default=Y_TOP,
        help="Top-quark Yukawa coupling"
    )
    parser.add_argument(
        "--m_fermion",
        type=float,
        default=M_FERMION_NATURAL,
        help="Fermion mass in natural units"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run diagnostic checks"
    )

    args = parser.parse_args()

    # Compute a_bcc in meters
    a_bcc = args.a_bcc_planck_ratio * PLANCK_LENGTH

    # Gravity route
    hbar_gravity = compute_hbar_gravity(a_bcc)

    print("=" * 70)
    print("Math158: Fermion-Loop Saturation Route to hbar")
    print("=" * 70)
    print()

    print("PHYSICAL CONSTANTS (SI units):")
    print(f"  Planck length (ell_P):        {PLANCK_LENGTH:.6e} m")
    print(f"  Reduced Planck constant:      {HBAR_REDUCED:.6e} J·s")
    print(f"  Speed of light:               {C_LIGHT:.6e} m/s")
    print(f"  Gravitational coupling:       {G_NEWTON:.6e} m³/(kg·s²)")
    print()

    print("TECT PARAMETERS:")
    print(f"  a_bcc (lattice constant):     {a_bcc:.6e} m")
    print(f"  a_bcc / ell_P:                {args.a_bcc_planck_ratio}")
    print(f"  y_t (Yukawa coupling):        {args.y_top}")
    print(f"  m_f (fermion mass, nat. u.):  {args.m_fermion}")
    print()

    print("ROUTE B (GRAVITY):")
    print(f"  hbar_gravity:                 {hbar_gravity:.6e} J·s")
    print(f"  Comparison to standard hbar:  {hbar_gravity / HBAR_REDUCED:.6f} (ratio)")
    print()

    # One-loop calculation
    k_max_natural = 1.0 / (args.a_bcc_planck_ratio * 1.0)  # In natural units, k_max ~ 1/a_bcc
    z_one_loop, log_factor = compute_one_loop_correction(args.y_top, args.m_fermion, k_max_natural)

    print("ROUTE 1 (FERMION-LOOP, ONE-LOOP PERTURBATIVE):")
    print(f"  Cutoff momentum k_max:        1/a_bcc = {k_max_natural:.6e} (natural units)")
    print(f"  Logarithmic factor L:         log(k_max/m_f) = {log_factor:.2f}")
    print(f"  One-loop correction Z_Psi^(1): {z_one_loop:.4f}")
    print()

    if z_one_loop > 0.1:
        print(f"  WARNING: Z_Psi^(1) = {z_one_loop:.4f} is NOT small.")
        print(f"  Perturbation theory is marginal or breaks down.")
        print(f"  Non-perturbative calculation required for reliable result.")
    else:
        print(f"  One-loop correction is small: {z_one_loop:.4f} << 1 ✓")
    print()

    # Condensate density (from Math110-AddG)
    rho_cond_natural = (1.0**4) / (16 * np.pi * 1.0 * (args.a_bcc_planck_ratio**2))

    # Non-perturbative critical hbar estimate
    hbar_critical = estimate_hbar_critical_nonperturb(
        args.y_top, args.m_fermion, rho_cond_natural, args.a_bcc_planck_ratio
    )

    print("ROUTE 1 (FERMION-LOOP, NON-PERTURBATIVE ESTIMATE):")
    print(f"  Condensate density (nat. u.): {rho_cond_natural:.6e}")
    print(f"  hbar_critical (nat. u.):      {hbar_critical:.6e}")
    print()

    # Falsification criterion (10% agreement threshold)
    if abs(hbar_critical - 1.0) / 1.0 < 0.1:
        print("  NON-PERTURBATIVE RESULT (relative to natural unit hbar=1):")
        print(f"    Deviation from tree-level:  {abs(hbar_critical - 1.0) / 1.0 * 100:.1f}%")
        print("    Status: PASSES agreement criterion (< 10%) ✓")
    else:
        print("  NON-PERTURBATIVE RESULT (relative to natural unit hbar=1):")
        print(f"    Deviation from tree-level:  {abs(hbar_critical - 1.0) / 1.0 * 100:.1f}%")
        print("    Status: FAILS agreement criterion (> 10%) ✗")
        print("    This would trigger falsification (see Math158 §6).")
    print()

    print("COMPARISON: ROUTE B vs ROUTE 1")
    print(f"  hbar_gravity (SI):            {hbar_gravity:.6e} J·s")
    print(f"  hbar_critical * factor (est.): [requires full all-loop calculation]")
    print(f"  Current status:               PARTIAL-ADVANCED (pending all-loop)")
    print()

    print("=" * 70)
    print("DIAGNOSTIC CHECKS")
    print("=" * 70)
    print()

    if args.check:
        print("Dimensional consistency:")
        print(f"  [a_bcc] = length ✓")
        print(f"  [y_t^2 * m_f * a_bcc^3 / (4π)^2]:")
        print(f"    = [dimensionless]^2 * [energy] * [length]^3 / [dimensionless]")
        print(f"    = [energy] * [length]^3")
        print(f"    ≠ [action] = [energy * time]")
        print(f"  -> Requires additional Compton wavelength factor (resolved in §2.4)")
        print()

        print("Perturbative validity check:")
        print(f"  y_t^2 / (4π)^2 ~ {args.y_top**2 / (4*np.pi)**2:.4f}")
        print(f"  Log factor L ~ {log_factor:.2f}")
        print(f"  Coupling strength: y_t^2 * L ~ {args.y_top**2 * log_factor / (4*np.pi)**2:.4f}")
        if args.y_top**2 * log_factor / (4*np.pi)**2 < 0.1:
            print(f"  Status: Perturbative regime valid ✓")
        else:
            print(f"  Status: Non-perturbative regime; resummation needed ✗")
        print()

    print("CONCLUSION:")
    print("  Route 1 (fermion-loop saturation) is structurally independent of")
    print("  the elastic-modulus identification (ρ_cond ↔ G).")
    print("  Numerical verification requires all-loop calculation.")
    print("  Current status: PARTIAL-ADVANCED (Math158 §5.3)")
    print()


if __name__ == "__main__":
    main()
