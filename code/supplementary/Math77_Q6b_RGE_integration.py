#!/usr/bin/env python3
# =====================================================================
# Math77_Q6b_RGE_integration.py
# Theory tag:  Math77-Q6b-Addendum-A-RGE-numerical-extraction-2026-04-24
# Purpose:     1-loop Standard Model RGE numerical integration of the
#              three gauge couplings alpha_1, alpha_2, alpha_3 from M_Z
#              up to M_Planck, with explicit unification-scale and
#              proton-decay-bound assessment.
#
# This script implements the standard textbook 1-loop SM RGE without
# assumptions of supersymmetry or other BSM content. The output is the
# honest numerical answer: "does the pure SM unify at one scale?"
# (Answer: no, it gives three pairwise meeting points spanning ~4
# orders of magnitude.)
#
# The TECT Q6b context: Math77-Q6a-Q6b-closure conjectures that the
# Pati-Salam two-step breaking SO(10) -> SU(4)_C x SU(2)_L x SU(2)_R
# -> G_SM with an intermediate scale ~10^11-10^12 GeV could fix the
# unification, with the BCC condensate providing the necessary
# intermediate matter content. This script does NOT prove that
# conjecture; it establishes the BASELINE that the conjecture must
# improve upon.
#
# Outputs:
#   - Math77_Q6b_RGE_integration_results.json  (structured)
#   - Console table of pairwise meeting scales
# Inputs:      none (PDG 2024 SM gauge coupling values hard-coded)
# Math note:   Docs/math/TECT-Math77-Q6b-Addendum-A-RGE-extraction.tex.txt
# =====================================================================

import math
import json
from pathlib import Path

# ---------------- Initial conditions at M_Z (PDG 2024 / 2025) ----------------
# All gauge couplings in GUT normalization (g_1 = sqrt(5/3) * g_Y).
# alpha_em(M_Z) and sin^2(theta_W) are MS-bar values.
M_Z         = 91.1876        # GeV
alpha_em_MZ = 1.0 / 127.952  # MS-bar at M_Z
sin2_thetaW = 0.23122
alpha_s_MZ  = 0.1184         # alpha_3(M_Z), PDG world average

cos2_thetaW = 1.0 - sin2_thetaW

# Convert to GUT-normalized inverse couplings at M_Z:
alpha_1_inv_MZ = (3.0 / 5.0) * cos2_thetaW / alpha_em_MZ
alpha_2_inv_MZ = sin2_thetaW / alpha_em_MZ
alpha_3_inv_MZ = 1.0 / alpha_s_MZ

# ---------------- 1-loop SM beta-function coefficients ----------------
# d alpha_i^{-1} / d ln(mu) = - b_i / (2 pi)
b_1 = +41.0 / 10.0    # U(1)_Y, GUT-normalized
b_2 = -19.0 / 6.0     # SU(2)_L
b_3 = -7.0            # SU(3)_C

# ---------------- 1-loop RGE solution ----------------
def alpha_inv(i, mu):
    """alpha_i^{-1}(mu) at 1-loop, mu in GeV."""
    if i == 1:
        return alpha_1_inv_MZ - (b_1 / (2.0 * math.pi)) * math.log(mu / M_Z)
    elif i == 2:
        return alpha_2_inv_MZ - (b_2 / (2.0 * math.pi)) * math.log(mu / M_Z)
    elif i == 3:
        return alpha_3_inv_MZ - (b_3 / (2.0 * math.pi)) * math.log(mu / M_Z)

def find_meeting_scale(i, j):
    """Solve alpha_i^{-1}(mu) = alpha_j^{-1}(mu) for mu, in GeV."""
    if i == 1 and j == 2:
        a0 = alpha_1_inv_MZ - alpha_2_inv_MZ
        slope = (b_1 - b_2) / (2.0 * math.pi)
    elif i == 1 and j == 3:
        a0 = alpha_1_inv_MZ - alpha_3_inv_MZ
        slope = (b_1 - b_3) / (2.0 * math.pi)
    elif i == 2 and j == 3:
        a0 = alpha_2_inv_MZ - alpha_3_inv_MZ
        slope = (b_2 - b_3) / (2.0 * math.pi)
    # alpha_i^{-1} - alpha_j^{-1} = a0 - slope * ln(mu/MZ) = 0
    if slope == 0:
        return None
    log_ratio = a0 / slope
    return M_Z * math.exp(log_ratio)

# ---------------- Compute pairwise meeting scales ----------------
M_12 = find_meeting_scale(1, 2)
M_13 = find_meeting_scale(1, 3)
M_23 = find_meeting_scale(2, 3)

# Coupling at each meeting
alpha_at_M12 = 1.0 / alpha_inv(1, M_12)
alpha_at_M13 = 1.0 / alpha_inv(1, M_13)
alpha_at_M23 = 1.0 / alpha_inv(2, M_23)

# ---------------- Unification quality assessment ----------------
# Geometric mean of the three pairwise meeting scales:
M_GUT_geom = (M_12 * M_13 * M_23) ** (1.0 / 3.0)

# Logarithmic spread (orders of magnitude between min and max meeting):
log_spread = math.log10(max(M_12, M_13, M_23) / min(M_12, M_13, M_23))

# At M_GUT_geom, what are the three couplings?
alpha_1_at_geom_inv = alpha_inv(1, M_GUT_geom)
alpha_2_at_geom_inv = alpha_inv(2, M_GUT_geom)
alpha_3_at_geom_inv = alpha_inv(3, M_GUT_geom)

# RMS deviation of alpha_i^{-1} from their mean at M_GUT_geom:
mean_inv = (alpha_1_at_geom_inv + alpha_2_at_geom_inv + alpha_3_at_geom_inv) / 3.0
unification_rms = math.sqrt(
    ((alpha_1_at_geom_inv - mean_inv)**2 +
     (alpha_2_at_geom_inv - mean_inv)**2 +
     (alpha_3_at_geom_inv - mean_inv)**2) / 3.0
)
unification_relative_rms = unification_rms / mean_inv

# ---------------- Proton-decay bound (gauge-mediated tree-level) ----------------
# Tree-level proton decay rate ~ alpha_GUT^2 m_p^5 / M_X^4.
# Super-K bound: tau_p > 1.6e34 yr (p -> e+ pi^0 channel, 2024).
# Threshold: M_X >= 4 * 10^15 GeV (very rough).
TAU_P_OBS_LOWER_BOUND_yr = 1.6e34      # Super-K
M_X_threshold_for_bound = 4.0e15       # GeV, very rough

# At M_GUT_geom, M_X ~ M_GUT_geom (gauge boson mass). Test whether each
# of the three meeting scales is above the threshold.
M_X_safe_M12 = M_12 >= M_X_threshold_for_bound
M_X_safe_M13 = M_13 >= M_X_threshold_for_bound
M_X_safe_M23 = M_23 >= M_X_threshold_for_bound
M_X_safe_geom = M_GUT_geom >= M_X_threshold_for_bound

# ---------------- Output ----------------
print("=" * 72)
print(" Math77-Q6b 1-loop SM RGE numerical extraction")
print("=" * 72)
print(f"  Initial conditions at M_Z = {M_Z} GeV (GUT normalization):")
print(f"    alpha_1^-1(M_Z) = {alpha_1_inv_MZ:.4f}")
print(f"    alpha_2^-1(M_Z) = {alpha_2_inv_MZ:.4f}")
print(f"    alpha_3^-1(M_Z) = {alpha_3_inv_MZ:.4f}")
print(f"  1-loop b-coefficients: b_1 = {b_1:+.4f}, b_2 = {b_2:+.4f}, b_3 = {b_3:+.4f}")
print()
print("  Pairwise meeting scales (1-loop pure SM, no BSM content):")
print(f"    M_12 (alpha_1 = alpha_2) = {M_12:.3e} GeV   alpha = {alpha_at_M12:.5f} (1/alpha = {1/alpha_at_M12:.2f})")
print(f"    M_13 (alpha_1 = alpha_3) = {M_13:.3e} GeV   alpha = {alpha_at_M13:.5f} (1/alpha = {1/alpha_at_M13:.2f})")
print(f"    M_23 (alpha_2 = alpha_3) = {M_23:.3e} GeV   alpha = {alpha_at_M23:.5f} (1/alpha = {1/alpha_at_M23:.2f})")
print()
print(f"  Geometric mean: M_GUT_geom = {M_GUT_geom:.3e} GeV")
print(f"  Logarithmic spread (max/min): {log_spread:.2f} orders of magnitude")
print(f"  Couplings at M_GUT_geom:")
print(f"    alpha_1^-1 = {alpha_1_at_geom_inv:.4f}")
print(f"    alpha_2^-1 = {alpha_2_at_geom_inv:.4f}")
print(f"    alpha_3^-1 = {alpha_3_at_geom_inv:.4f}")
print(f"    Mean       = {mean_inv:.4f}")
print(f"    RMS deviation = {unification_rms:.4f} ({100*unification_relative_rms:.2f}% of mean)")
print()
print(f"  Proton-decay safety check (Super-K bound tau_p > {TAU_P_OBS_LOWER_BOUND_yr:.1e} yr):")
print(f"    Threshold M_X >= {M_X_threshold_for_bound:.1e} GeV (rough)")
print(f"    M_12 safe? {M_X_safe_M12}")
print(f"    M_13 safe? {M_X_safe_M13}")
print(f"    M_23 safe? {M_X_safe_M23}")
print(f"    M_GUT_geom safe? {M_X_safe_geom}")
print()

# ---------------- Verdict ----------------
print("=" * 72)
print(" Verdict")
print("=" * 72)

if log_spread < 0.5:
    verdict = "TIGHT_UNIFICATION"
    verdict_text = "Pure SM 1-loop achieves tight unification (within factor 3)."
elif log_spread < 1.5:
    verdict = "APPROXIMATE_UNIFICATION"
    verdict_text = "Pure SM 1-loop achieves approximate unification (~1 order of magnitude spread)."
else:
    verdict = "NO_UNIFICATION"
    verdict_text = ("Pure SM 1-loop does NOT unify cleanly: pairwise meeting "
                    f"scales span {log_spread:.2f} orders of magnitude.")

print(f"  {verdict}: {verdict_text}")
if M_X_safe_geom:
    print("  Geometric-mean GUT scale satisfies proton-decay bound.")
else:
    print(f"  WARNING: M_GUT_geom = {M_GUT_geom:.3e} GeV may be below the proton-decay safety threshold.")

print()
print("  Implication for TECT Q6b:")
print("  Pure SM 1-loop running gives three different pairwise meeting scales")
print(f"  ({M_12:.2e}, {M_13:.2e}, {M_23:.2e} GeV) — consistent with the well-known")
print("  SM-without-SUSY non-unification result. TECT's Q6b conjecture")
print("  requires intermediate-scale new physics (Pati-Salam two-step breaking")
print("  with BCC defect content) to bring all three couplings together.")
print("  This script ESTABLISHES THE BASELINE; the TECT conjecture must")
print("  IMPROVE on this baseline by reducing log_spread.")
print()

# ---------------- JSON output ----------------
out = {
    "theory_tag": "Math77-Q6b-Addendum-A-RGE-numerical-extraction-2026-04-24",
    "framework": "1-loop SM gauge-coupling RGE (GUT-normalized U(1)_Y)",
    "initial_conditions_at_MZ": {
        "M_Z_GeV": M_Z,
        "alpha_em_MZ": alpha_em_MZ,
        "sin2_thetaW": sin2_thetaW,
        "alpha_s_MZ": alpha_s_MZ,
        "alpha_1_inv": alpha_1_inv_MZ,
        "alpha_2_inv": alpha_2_inv_MZ,
        "alpha_3_inv": alpha_3_inv_MZ,
    },
    "1loop_beta_coefficients": {
        "b_1": b_1,
        "b_2": b_2,
        "b_3": b_3,
    },
    "pairwise_meeting_scales_GeV": {
        "M_12_alpha1_eq_alpha2": M_12,
        "M_13_alpha1_eq_alpha3": M_13,
        "M_23_alpha2_eq_alpha3": M_23,
    },
    "couplings_at_meeting": {
        "alpha_at_M12": alpha_at_M12,
        "alpha_at_M13": alpha_at_M13,
        "alpha_at_M23": alpha_at_M23,
    },
    "unification_quality": {
        "M_GUT_geometric_mean_GeV": M_GUT_geom,
        "log10_spread_max_over_min": log_spread,
        "alpha_1_inv_at_M_GUT_geom": alpha_1_at_geom_inv,
        "alpha_2_inv_at_M_GUT_geom": alpha_2_at_geom_inv,
        "alpha_3_inv_at_M_GUT_geom": alpha_3_at_geom_inv,
        "mean_alpha_inv": mean_inv,
        "rms_deviation": unification_rms,
        "rms_deviation_relative_to_mean": unification_relative_rms,
    },
    "proton_decay_bound": {
        "Super_K_tau_p_lower_bound_yr": TAU_P_OBS_LOWER_BOUND_yr,
        "rough_M_X_threshold_GeV": M_X_threshold_for_bound,
        "M_12_safe": M_X_safe_M12,
        "M_13_safe": M_X_safe_M13,
        "M_23_safe": M_X_safe_M23,
        "M_GUT_geom_safe": M_X_safe_geom,
    },
    "verdict": {
        "code": verdict,
        "text": verdict_text,
    },
    "TECT_implication": (
        "Pure SM 1-loop running gives three different pairwise meeting "
        "scales spanning ~{:.1f} orders of magnitude, consistent with the "
        "well-known SM-without-SUSY non-unification. TECT Q6b conjecture "
        "requires intermediate-scale new physics (Pati-Salam two-step "
        "breaking with BCC defect content) to achieve unification. This "
        "script ESTABLISHES THE BASELINE; the Q6b conjecture must improve "
        "on this baseline.".format(log_spread)
    ),
}
out_path = Path(__file__).parent / "Math77_Q6b_RGE_integration_results.json"
with open(out_path, "w") as f:
    json.dump(out, f, indent=2)
print(f"  Results saved to: {out_path}")
