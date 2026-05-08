#!/usr/bin/env python3
# =====================================================================
# Math79_R5_chi_star_extraction.py
# Theory tag:  Math79-Pillar10-R5-Residual-Matching-Framework-2026-04-24
# Purpose:     First-iteration numerical extraction of chi_star^(i) for
#              the four canonical R5 residual channels.
# Inputs:      None (constants hard-coded; no observational data file).
# Outputs:     Math79_R5_chi_star_results.json + console table.
# Dependencies: numpy (stdlib + numpy only).
# Math note:   docs/math/TECT-Math79-Pillar10-R5-residual-matching-framework.tex.txt
#
# IMPORTANT: This is a FIRST-ITERATION extraction. C_i are taken from the
# leading dimensional form of Math79 sections 4-6. A rigorous extraction
# would derive C_i from explicit Brazovskii defect-mediated calculations.
# However, the dimensional form already suffices to test the
# pre-registered success criterion (Math79 section 7 Theorem on R5).
#
# The dimensional ambiguity is encoded in two free parameters:
#   a_BCC_phys  — the physical lattice spacing in meters
#   E_BCC_phys  — the natural BCC energy scale in joules
# We scan over plausible values and report chi_star^(i) and the ratios
# rho_Lambda, rho_Cas, rho_g-2 versus chi_star^(Comp) (calibration).
# =====================================================================

import math
import json
import numpy as np
from pathlib import Path

# ---------------- Physical constants (SI, observational) ----------------
hbar_obs   = 1.054571817e-34         # J s
h_obs      = 2.0 * math.pi * hbar_obs # J s
c          = 2.99792458e8            # m/s
e_charge   = 1.602176634e-19         # C
eps0       = 8.8541878128e-12        # F/m
m_e        = 9.1093837015e-31        # kg
G_N        = 6.67430e-11             # m^3 kg^-1 s^-2 (gravitational; not used in C_i)

# Coupling combination e^2/(4 pi eps0) [J m]
e2_4pieps = e_charge**2 / (4.0 * math.pi * eps0)

# ---------------- Observational anchor values ----------------
# Compton wavelength of electron (full, not reduced)
lambda_C = h_obs / (m_e * c)         # m, ~2.4263e-12

# Cosmological constant (Planck 2018 LCDM)
Lambda_obs = 1.1056e-52              # m^-2

# Casimir force per area at d = 1 micron (parallel plates)
d_Cas = 1.0e-6                       # m
F_per_A_Cas_obs = -math.pi**2 * hbar_obs * c / (240.0 * d_Cas**4)  # Pa = J/m^3

# Electron g-factor anomaly
a_e_obs = 1.15965218073e-3

# ---------------- TECT classical inputs (lattice-natural units) ----------------
q0_lat    = 0.6801747616             # BCC geometric value, dimensionless (lattice)
a_BCC_lat = 2.0 * math.pi / q0_lat   # ~9.24, dimensionless (lattice)
Y_lat     = 1.62                     # Brazovskii Y, dimensionless (lattice)
lam_lat   = -0.43                    # Brazovskii lambda
mu2_lat   = 5.0e-3                   # Brazovskii mu^2 (target operating point)

# ---------------- Channel coefficient functions ----------------
# Math79 dimensional ansatz:
#   R5-A: C_Lambda  ~ Y_SI / a_BCC_phys^2          [m^-2]
#   R5-B: C_Cas(d)  ~ Y_SI * (q0_phys)^2 / d^2     [J/m^3]   with q0_phys = q0_lat/a_BCC_phys
#   R5-C: C_Comp    = a_BCC_phys                    [m]
#   R5-D: C_a_e     = (1/2pi) * e^2/(4pi eps0) / (Y_SI * (q0_phys)^2 * a_BCC_phys^2)  [dimensionless]
#
# Y_SI dimensional analysis: Brazovskii free-energy density f has units J/m^3,
# the gradient term Y * (nabla^2 + q0^2)^2 psi^2 has [Y] * [psi]^2 / m^4,
# with psi dimensionless this gives [Y] = (J/m^3) * m^4 = J*m.
# Lattice-to-SI: Y_SI = Y_lat * E_BCC_phys * a_BCC_phys (per lattice convention).
# We treat Y_SI as an independent parameter for the audit.

def chi_star_compton(a_BCC_phys):
    """R5-C calibration channel: chi_star^(Comp) = lambda_C / a_BCC_phys."""
    return lambda_C / a_BCC_phys

def chi_star_lambda(a_BCC_phys, Y_SI):
    """R5-A: chi_star^(Lambda) = Lambda_obs * a_BCC_phys^2 / Y_SI."""
    C_Lambda = Y_SI / a_BCC_phys**2
    return Lambda_obs / C_Lambda

def chi_star_casimir(a_BCC_phys, Y_SI, d=d_Cas):
    """R5-B: chi_star^(Cas) = (F/A) / [Y_SI * q0_phys^2 / d^2]."""
    q0_phys = q0_lat / a_BCC_phys
    C_Cas = Y_SI * q0_phys**2 / d**2
    return F_per_A_Cas_obs / C_Cas

def chi_star_g2(a_BCC_phys, Y_SI):
    """R5-D: chi_star^(g-2) = a_e_obs / C_a_e."""
    q0_phys = q0_lat / a_BCC_phys
    C_ae = (1.0 / (2.0 * math.pi)) * e2_4pieps / (Y_SI * q0_phys**2 * a_BCC_phys**2)
    return a_e_obs / C_ae

# ---------------- Audit ----------------
print("=" * 78)
print("TECT Math79 — Pillar 10 R5 chi_star extraction (first iteration)")
print("=" * 78)
print(f"  Compton wavelength (full):  lambda_C = {lambda_C:.6e} m")
print(f"  Lambda_obs:                 {Lambda_obs:.6e} m^-2")
print(f"  Casimir at d=1 um:          F/A = {F_per_A_Cas_obs:.6e} Pa")
print(f"  Electron a_e (g-2)/2:       {a_e_obs:.6e}")
print(f"  q0_lattice:                 {q0_lat:.6f}")
print(f"  a_BCC_lattice = 2pi/q0:     {a_BCC_lat:.6f}")
print()

# Scan over plausible a_BCC_phys values (1 fm to 10 nm)
a_grid = np.logspace(-15, -8, 71)

# For Y_SI we need an independent estimate. Per Math79 lattice convention,
# Y_SI ~ Y_lat * E_BCC_phys * a_BCC_phys with E_BCC_phys an unknown energy scale.
# We use the calibration trick: choose E_BCC_phys such that chi_star^(Comp) = 1
# at the chosen a_BCC_phys (i.e. a_BCC_phys = lambda_C). This fixes E_BCC_phys
# only implicitly. For each a_BCC_phys we instead test multiple Y_SI values.

# Calibration option 1: chi_star^(Comp) = 1  =>  a_BCC_phys = lambda_C.
print("=" * 78)
print("Calibration option 1: chi_star^(Comp) = 1  =>  a_BCC_phys = lambda_C")
print("=" * 78)
a_calib_1 = lambda_C
# At this a, scan Y_SI to see if any value yields rho ~ 1 across other channels
print(f"  a_BCC_phys = {a_calib_1:.6e} m  (= lambda_C)")
print()
print(f"  Scanning Y_SI from 1e-50 to 1e10 J*m to test rho_Lambda alignment...")
Y_grid = np.logspace(-50, 10, 121)
best_Y = None
best_resid = float('inf')
for Y_SI in Y_grid:
    cC = chi_star_compton(a_calib_1)
    cL = chi_star_lambda(a_calib_1, Y_SI)
    rho_L = abs(cL / cC)
    resid = abs(math.log10(rho_L)) if rho_L > 0 else float('inf')
    if resid < best_resid:
        best_resid = resid
        best_Y = Y_SI

print(f"  Best Y_SI for rho_Lambda ~ 1: Y_SI = {best_Y:.3e} J*m")
print(f"    chi_C = {chi_star_compton(a_calib_1):.6e}")
print(f"    chi_L = {chi_star_lambda(a_calib_1, best_Y):.6e}  (rho_L = {chi_star_lambda(a_calib_1, best_Y)/chi_star_compton(a_calib_1):.6e})")
print(f"    chi_K = {chi_star_casimir(a_calib_1, best_Y):.6e}  (rho_K = {chi_star_casimir(a_calib_1, best_Y)/chi_star_compton(a_calib_1):.6e})")
print(f"    chi_g = {chi_star_g2(a_calib_1, best_Y):.6e}  (rho_g = {chi_star_g2(a_calib_1, best_Y)/chi_star_compton(a_calib_1):.6e})")
print()

# Calibration option 2: choose Y_SI from Brazovskii lattice convention
# Y_SI = Y_lat * E_BCC_phys * a_BCC_phys
# Pick E_BCC_phys = m_e c^2 (electron rest-energy) as natural energy scale
# (since R5-C calibration anchors on electron). Then:
#   Y_SI = Y_lat * m_e c^2 * a_BCC_phys
print("=" * 78)
print("Calibration option 2: Y_SI = Y_lat * m_e c^2 * a_BCC_phys (electron-anchored)")
print("=" * 78)
E_BCC_phys = m_e * c**2  # 8.187e-14 J = 511 keV
print(f"  E_BCC_phys = m_e c^2 = {E_BCC_phys:.3e} J")
print()
print(f"  {'a_BCC [m]':>14}  {'chi_C':>12}  {'chi_L':>12}  {'chi_K':>12}  {'chi_g':>12}  {'rho_L':>12}  {'rho_K':>12}  {'rho_g':>12}")
print("  " + "-" * 124)
results_opt2 = []
for a in a_grid:
    Y_SI = Y_lat * E_BCC_phys * a
    cC = chi_star_compton(a)
    cL = chi_star_lambda(a, Y_SI)
    cK = chi_star_casimir(a, Y_SI)
    cg = chi_star_g2(a, Y_SI)
    rho_L = cL / cC if cC != 0 else float('nan')
    rho_K = cK / cC if cC != 0 else float('nan')
    rho_g = cg / cC if cC != 0 else float('nan')
    results_opt2.append({"a_BCC_m": a, "chi_C": cC, "chi_L": cL, "chi_K": cK, "chi_g": cg,
                          "rho_L": rho_L, "rho_K": rho_K, "rho_g": rho_g})
    if a in [a_grid[0], a_grid[10], a_grid[20], a_grid[35], a_grid[50], a_grid[60], a_grid[-1]]:
        print(f"  {a:>14.3e}  {cC:>12.3e}  {cL:>12.3e}  {cK:>12.3e}  {cg:>12.3e}  {rho_L:>12.3e}  {rho_K:>12.3e}  {rho_g:>12.3e}")

# Find a where rho_L is closest to 1
best = min(results_opt2, key=lambda r: abs(math.log10(abs(r["rho_L"]) + 1e-300)))
print()
print(f"  Best a_BCC_phys for rho_L ~ 1:  a = {best['a_BCC_m']:.3e} m")
print(f"    rho_L = {best['rho_L']:.3e}, rho_K = {best['rho_K']:.3e}, rho_g = {best['rho_g']:.3e}")

# Find a where ALL three rho are minimized in joint sense
def joint_resid(r):
    parts = []
    for key in ("rho_L", "rho_K", "rho_g"):
        v = abs(r[key])
        if v > 0:
            parts.append(abs(math.log10(v)))
        else:
            parts.append(float('inf'))
    return sum(parts)
best_joint = min(results_opt2, key=joint_resid)
print(f"  Best a_BCC_phys for joint rho ~ 1 (sum of |log10 rho|):  a = {best_joint['a_BCC_m']:.3e} m")
print(f"    rho_L = {best_joint['rho_L']:.3e}, rho_K = {best_joint['rho_K']:.3e}, rho_g = {best_joint['rho_g']:.3e}")

print()
print("=" * 78)
print("R5 success criterion (Math79 section 7):")
print("  rho_Lambda, rho_Cas, rho_g-2 ALL in [0.5, 2.0] simultaneously.")
print("=" * 78)

success = (
    abs(best_joint["rho_L"] - 1.0) < 1.0 and
    abs(best_joint["rho_K"] - 1.0) < 1.0 and
    abs(best_joint["rho_g"] - 1.0) < 1.0 and
    0.5 <= best_joint["rho_L"] <= 2.0 and
    0.5 <= best_joint["rho_K"] <= 2.0 and
    0.5 <= best_joint["rho_g"] <= 2.0
)

failure_factor10 = (
    abs(math.log10(abs(best_joint["rho_L"]) + 1e-300)) > 1.0 or
    abs(math.log10(abs(best_joint["rho_K"]) + 1e-300)) > 1.0 or
    abs(math.log10(abs(best_joint["rho_g"]) + 1e-300)) > 1.0
)

print()
if success:
    print("  >>> R5 SUCCESS: phenomenological universality CONFIRMED.")
elif failure_factor10:
    print("  >>> R5 FAILURE (factor-10 criterion): even phenomenological universality FAILS.")
    print("       Pillar 10 = OPEN-NEGATIVE REFINED is REINFORCED.")
else:
    print("  >>> R5 INCONCLUSIVE: ratios within [0.1, 10] but outside [0.5, 2].")
    print("       Refinement of C_i (beyond dimensional ansatz) required.")

# Save
out_path = Path(__file__).parent / "Math79_R5_chi_star_results.json"
out = {
    "framework_note": "TECT-Math79-Pillar10-R5-residual-matching-framework.tex.txt",
    "iteration": "first-iteration dimensional ansatz",
    "calibration_option_1": {
        "description": "chi_star^(Comp) = 1 => a_BCC_phys = lambda_C",
        "a_BCC_phys_m": a_calib_1,
        "best_Y_SI_J_m": best_Y,
    },
    "calibration_option_2": {
        "description": "Y_SI = Y_lat * m_e c^2 * a_BCC_phys (electron-anchored)",
        "scan": results_opt2,
        "best_for_rho_Lambda": best,
        "best_for_joint_rho": best_joint,
    },
    "success_criterion_pre_registered": "rho_Lambda, rho_Cas, rho_g-2 all in [0.5, 2.0]",
    "verdict": "SUCCESS" if success else ("FAILURE_factor10" if failure_factor10 else "INCONCLUSIVE"),
}
with open(out_path, "w") as f:
    json.dump(out, f, indent=2)
print()
print(f"  Results saved to: {out_path}")
