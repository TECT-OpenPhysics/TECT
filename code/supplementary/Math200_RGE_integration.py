#!/usr/bin/env python3
"""
Math200_RGE_integration.py
Date: 2026-04-28
Purpose: Numerical integration of one-loop SM beta-functions for GAP-1 scale-coherence check.

TECT-Math200 computes the running of the effective Planck constant hbar(μ) under one-loop
RGE evolution from M_Z ≈ 91 GeV to M_X ≈ 2e16 GeV (GUT scale).

Usage:
    python Math200_RGE_integration.py

Output:
    - Table of gauge-coupling evolution (printed to stdout)
    - hbar drift calculation (printed to stdout)
    - Falsification-criterion verdict
    - (Optional) save results to JSON for later analysis
"""

import numpy as np
from scipy.integrate import solve_ivp
import json
from datetime import datetime

# ==============================================================================
# CONSTANTS & INITIAL CONDITIONS
# ==============================================================================

# Physical constants
M_Z = 91.2  # Z-boson mass (GeV)
M_X = 2e16  # GUT scale (GeV)

# PDG 2020 values at M_Z
alpha_inv_Z = 127.906  # α^{-1}(M_Z)
sin2_theta_W_Z = 0.23122  # sin²θ_W(M_Z)
alpha_s_Z = 0.1183  # α_s(M_Z)

# Extracted gauge couplings at M_Z (SM convention)
g1_Z = np.sqrt((5/3) * (1/alpha_inv_Z) / (1 - sin2_theta_W_Z)) * np.sqrt(1 / (4*np.pi))
g2_Z = np.sqrt((1/alpha_inv_Z) / sin2_theta_W_Z) * np.sqrt(1 / (4*np.pi))
g3_Z = np.sqrt(4*np.pi*alpha_s_Z)

# Top Yukawa coupling at M_Z (approximate)
y_t_Z = 1.0  # Renormalized top Yukawa

print("=" * 80)
print("TECT-Math200: GAP-1 RGE Scale-Coherence Numerical Integration")
print("=" * 80)
print()
print(f"Initial conditions at M_Z = {M_Z} GeV:")
print(f"  g_1(M_Z) = {g1_Z:.6f}")
print(f"  g_2(M_Z) = {g2_Z:.6f}")
print(f"  g_3(M_Z) = {g3_Z:.6f}")
print(f"  y_t(M_Z) = {y_t_Z:.6f}")
print()

# ==============================================================================
# ONE-LOOP BETA FUNCTIONS
# ==============================================================================

def beta_functions(mu, y):
    """
    One-loop SM beta-functions in MS-bar scheme.

    y[0] = g_1
    y[1] = g_2
    y[2] = g_3
    y[3] = y_t

    Returns dy/d(ln μ) for each coupling.
    """
    g1, g2, g3, yt = y

    # One-loop beta-function coefficients (Machacek-Vaughn 1983)
    # β_g = (g³ / 16π²) × b_g
    b_g1 = 41/6
    b_g2 = -19/6
    b_g3 = -7

    # Top Yukawa beta-function
    # β_yt = (y_t / 16π²) × [9*y_t² - (17/20)*g_1² - (9/4)*g_2² - 8*g_3²]

    dg1_d_lnmu = (g1**3 / (16*np.pi**2)) * b_g1
    dg2_d_lnmu = (g2**3 / (16*np.pi**2)) * b_g2
    dg3_d_lnmu = (g3**3 / (16*np.pi**2)) * b_g3
    dyt_d_lnmu = (yt / (16*np.pi**2)) * (9*yt**2 - (17/20)*g1**2 - (9/4)*g2**2 - 8*g3**2)

    return [dg1_d_lnmu, dg2_d_lnmu, dg3_d_lnmu, dyt_d_lnmu]

# ==============================================================================
# RGE INTEGRATION
# ==============================================================================

# Initial state vector
y0 = [g1_Z, g2_Z, g3_Z, y_t_Z]

# Log-spaced scales for evaluation
scales = np.logspace(np.log10(M_Z), np.log10(M_X), 100)

# Solve the RGE: dy/d(ln μ) = β(y)
# We integrate with respect to log(μ), so the independent variable is ln(μ)
ln_scales = np.log(scales)

# solve_ivp expects d(y)/d(t), so we set t = ln(μ)
sol = solve_ivp(
    beta_functions,
    [np.log(M_Z), np.log(M_X)],
    y0,
    t_eval=ln_scales,
    method='RK45',
    dense_output=False,
    max_step=1e-1,  # Control step size to avoid missing rapid transitions
    atol=1e-10,
    rtol=1e-9
)

# Extract results
g1_array = sol.y[0]
g2_array = sol.y[1]
g3_array = sol.y[2]
yt_array = sol.y[3]

# ==============================================================================
# HBAR EVOLUTION & FALSIFICATION CHECK
# ==============================================================================

# Define hbar running: hbar(μ) ∝ g_1(μ)² × g_2(μ) × g_3(μ)
# (This is motivated by SO(10) structure; exact power law depends on Pillar 4)

hbar_at_scale = g1_array**2 * g2_array * g3_array  # Proportional to hbar(μ)
hbar_Z = hbar_at_scale[0]  # Value at M_Z
hbar_relative_shift = (hbar_at_scale - hbar_Z) / hbar_Z  # Fractional shift

# Pre-registered falsification criterion
falsification_threshold = 0.10
max_shift = np.max(np.abs(hbar_relative_shift))
falsified = max_shift >= falsification_threshold

# ==============================================================================
# OUTPUT TABLES
# ==============================================================================

print()
print("Table 1: Gauge-coupling evolution (selected scales)")
print("-" * 80)
print(f"{'Scale (GeV)':>15} | {'g_1(μ)':>10} | {'g_2(μ)':>10} | {'g_3(μ)':>10} | {'g_3/g_1':>10}")
print("-" * 80)

# Select output scales for table
output_scales_idx = []
target_scales = [1e2, 1e3, 1e4, 1e5, 1e6, 1e9, 1e12, 1e15, 1e16]
for target in target_scales:
    idx = np.argmin(np.abs(scales - target))
    output_scales_idx.append(idx)

for idx in output_scales_idx:
    scale = scales[idx]
    g1_val = g1_array[idx]
    g2_val = g2_array[idx]
    g3_val = g3_array[idx]
    ratio = g3_val / g1_val if g1_val != 0 else np.nan
    print(f"{scale:15.2e} | {g1_val:10.6f} | {g2_val:10.6f} | {g3_val:10.6f} | {ratio:10.6f}")

print("-" * 80)
print()

print("Table 2: Hbar running and scale-coherence check")
print("-" * 80)
print(f"{'Scale (GeV)':>15} | {'Δhbar / hbar':>15} | {'Falsified?':>12}")
print("-" * 80)

for idx in output_scales_idx:
    scale = scales[idx]
    shift = hbar_relative_shift[idx]
    is_falsified = "YES" if abs(shift) >= falsification_threshold else "NO"
    print(f"{scale:15.2e} | {shift:15.6f} | {is_falsified:>12}")

print("-" * 80)
print()

# ==============================================================================
# VERDICT
# ==============================================================================

print("FALSIFICATION CRITERION RESULT")
print("=" * 80)
print(f"Pre-registered threshold: |Δhbar / hbar| < {falsification_threshold}")
print(f"Maximum observed shift: {max_shift:.6f}")
print(f"Status: {'FALSIFIED (GAP-1 scale-coherence FAILS)' if falsified else 'PASSED'}")
print()

if falsified:
    print("WARNING: One-loop RGE predicts Δhbar > 10% over the evolution range.")
    print("Mitigation required:")
    print("  1. Two-loop β-functions may reduce the shift.")
    print("  2. Intermediate thresholds may introduce compensating jumps.")
    print("  3. GUT-scale matching may enforce consistency.")
    print("  → Task #147: Compute two-loop RGE for full assessment.")
else:
    print("SUCCESS: One-loop RGE indicates Δhbar < 10% across the evolution range.")
    print("GAP-1 scale-coherence PASSED to one-loop accuracy.")

print()

# ==============================================================================
# SAVE RESULTS TO JSON
# ==============================================================================

results = {
    "timestamp": datetime.now().isoformat(),
    "analysis": "TECT-Math200 GAP-1 RGE scale-coherence (one-loop)",
    "initial_conditions": {
        "M_Z_GeV": M_Z,
        "g1_Z": float(g1_Z),
        "g2_Z": float(g2_Z),
        "g3_Z": float(g3_Z),
        "y_t_Z": float(y_t_Z)
    },
    "evolution": {
        "M_X_GeV": float(M_X),
        "num_points": len(scales),
        "scales": scales.tolist(),
        "g1_values": g1_array.tolist(),
        "g2_values": g2_array.tolist(),
        "g3_values": g3_array.tolist(),
        "yt_values": yt_array.tolist(),
        "hbar_relative_shift": hbar_relative_shift.tolist()
    },
    "falsification": {
        "threshold": falsification_threshold,
        "max_observed_shift": float(max_shift),
        "falsified": bool(falsified),
        "criterion_text": "If |Δhbar / hbar| ≥ 0.10 at any scale in [M_Z, M_X], then GAP-1 FAILS"
    },
    "verdict": "FALSIFIED (one-loop)" if falsified else "PASSED (one-loop)"
}

# Save to file (filename convention for runs)
output_filename = f"Math200_RGE_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(output_filename, 'w') as f:
    json.dump(results, f, indent=2)

print(f"Results saved to: {output_filename}")
print()

# ==============================================================================
# END OF SCRIPT
# ==============================================================================
