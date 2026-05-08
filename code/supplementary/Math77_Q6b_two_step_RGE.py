#!/usr/bin/env python3
# =====================================================================
# Math77_Q6b_two_step_RGE.py
# Theory tag:  Math77-Q6b-Addendum-B-PS-two-step-RGE-2026-04-24
# Purpose:     Two-step RGE solver for the Pati-Salam intermediate
#              breaking SO(10) -> G_PS -> G_SM, with phenomenological
#              scan over BCC-defect Delta-b_i contributions to identify
#              whether ANY Delta-b_i combination achieves gauge-coupling
#              unification at a proton-decay-safe M_GUT.
#
# Following Math77-Q6b-Addendum-A (pure-SM 1-loop FALSIFIED):
#   (i) M_Z to M_PS: SM b-coefficients + BCC-defect Delta_b_{1,2,3}
#  (ii) Pati-Salam matching at M_PS:
#         alpha_{SU(3)_C}(M_PS)  = alpha_{SU(4)_C}(M_PS)
#         alpha_{U(1)_Y}(M_PS)   = (3/5)*alpha_{B-L} + (2/5)*alpha_{SU(2)_R}
#         (with B-L embedded in SU(4)_C)
# (iii) M_PS to M_GUT: Pati-Salam b-coefficients (textbook)
#                       SO(10) unification at M_GUT
#  (iv) Search M_PS over [10^9, 10^15] GeV
#   (v) Search Delta_b_i over discrete grid {-2,-1,0,+1,+2}^3
#  (vi) For each (M_PS, Delta_b), check unification quality + M_GUT bound
#
# Outputs:
#   - Math77_Q6b_two_step_RGE_results.json
#   - Console table: top-10 unification candidates by quality
# Math note: docs/math/TECT-Math77-Q6b-Addendum-B-PS-two-step-RGE.tex.txt
# =====================================================================

import math
import json
import itertools
from pathlib import Path

# ---------------- Initial conditions at M_Z (PDG 2024, GUT normalization) ----
M_Z         = 91.1876         # GeV
alpha_em_MZ = 1.0 / 127.952
sin2_thetaW = 0.23122
alpha_s_MZ  = 0.1184

cos2_thetaW = 1.0 - sin2_thetaW
alpha_1_inv_MZ = (3.0 / 5.0) * cos2_thetaW / alpha_em_MZ   # ~59.020
alpha_2_inv_MZ = sin2_thetaW / alpha_em_MZ                   # ~29.585
alpha_3_inv_MZ = 1.0 / alpha_s_MZ                            # ~8.446

# ---------------- 1-loop SM beta-function coefficients ----------------------
b_1_SM = +41.0 / 10.0    # U(1)_Y, GUT-normalized
b_2_SM = -19.0 / 6.0     # SU(2)_L
b_3_SM = -7.0            # SU(3)_C

# ---------------- 1-loop Pati-Salam beta-function coefficients --------------
# G_PS = SU(4)_C x SU(2)_L x SU(2)_R
# Matter content (one SM generation = 16 of SO(10) = (4, 2, 1) + (4-bar, 1, 2)):
#   (4, 2, 1): contributes T(4)_4 * 2(SU(2)_L) = (1/2)*2 = 1 to b_4,
#               and T(2)_2 * 4(SU(4)) = (1/2)*4 = 2 to b_{2L}
#   (4-bar, 1, 2): contributes T(4)_4 * 2(SU(2)_R) = 1 to b_4,
#               and T(2)_2 * 4(SU(4)) = 2 to b_{2R}
# Times 3 generations: per-gen contributions multiplied by 3.
# Plus Higgs sector: minimal Pati-Salam Higgs is (1,2,2) + (15,1,1) + (1,1,3) etc.
# We use the standard MINIMAL Pati-Salam beta functions from textbook:
b_4_PS  = -22.0/3.0 + (10.0/3.0) + (1.0/3.0)   # gauge + 3 gen fermions + Higgs
b_2L_PS = -22.0/3.0 + (10.0/3.0) + (2.0/3.0)
b_2R_PS = -22.0/3.0 + (10.0/3.0) + (2.0/3.0)
# Standard minimal Pati-Salam: b_4 = -7, b_2L = b_2R = -8/3 + small Higgs corr.
# Use canonical textbook values (Mohapatra & Pal, Massive Neutrinos, Eq. 5.84-86):
b_4_PS  = -7.0       # SU(4)_C
b_2L_PS = -3.0       # SU(2)_L (with std Higgs)
b_2R_PS = -3.0       # SU(2)_R (with std Higgs)

# ---------------- RGE solver primitives ---------------------------------
def alpha_inv_at_scale(alpha_inv_0, b, mu_0, mu_target):
    """1-loop RGE: alpha^-1(mu) = alpha^-1(mu_0) - (b/2pi) * ln(mu/mu_0)."""
    return alpha_inv_0 - (b / (2.0 * math.pi)) * math.log(mu_target / mu_0)

def step1_run(M_PS, delta_b):
    """Run SM couplings from M_Z to M_PS with optional BCC-defect Delta b_i."""
    db_1, db_2, db_3 = delta_b
    a1 = alpha_inv_at_scale(alpha_1_inv_MZ, b_1_SM + db_1, M_Z, M_PS)
    a2 = alpha_inv_at_scale(alpha_2_inv_MZ, b_2_SM + db_2, M_Z, M_PS)
    a3 = alpha_inv_at_scale(alpha_3_inv_MZ, b_3_SM + db_3, M_Z, M_PS)
    return a1, a2, a3

def pati_salam_matching(a1_at_PS, a2_at_PS, a3_at_PS):
    """Match at M_PS:
       alpha_4^-1 = alpha_3^-1 (SU(3)_C subset of SU(4)_C)
       alpha_{2L}^-1 = alpha_2^-1 (continuous through PS scale)
       alpha_{2R}^-1: derived from a1 and a4 via:
         (3/5)*alpha_{B-L}^-1 + (2/5)*alpha_{2R}^-1 = alpha_1^-1
         alpha_{B-L}^-1 = alpha_4^-1 (B-L embeds in SU(4)_C)
       So: alpha_{2R}^-1 = (5/2)*(alpha_1^-1 - (3/5)*alpha_4^-1)
                         = (5/2)*alpha_1^-1 - (3/2)*alpha_4^-1
    """
    a4_at_PS  = a3_at_PS              # SU(3)_C subset of SU(4)_C
    a2L_at_PS = a2_at_PS              # SU(2)_L unchanged
    a2R_at_PS = (5.0/2.0)*a1_at_PS - (3.0/2.0)*a4_at_PS
    return a4_at_PS, a2L_at_PS, a2R_at_PS

def step2_run(a4_at_PS, a2L_at_PS, a2R_at_PS, M_PS, M_GUT):
    """Run Pati-Salam couplings from M_PS to M_GUT."""
    a4  = alpha_inv_at_scale(a4_at_PS,  b_4_PS,  M_PS, M_GUT)
    a2L = alpha_inv_at_scale(a2L_at_PS, b_2L_PS, M_PS, M_GUT)
    a2R = alpha_inv_at_scale(a2R_at_PS, b_2R_PS, M_PS, M_GUT)
    return a4, a2L, a2R

def find_unification(M_PS, delta_b):
    """For given (M_PS, Delta b), find M_GUT where SU(4)_C, SU(2)_L, SU(2)_R unify.
    Returns (M_GUT, alpha_GUT_inv, unification_rms_relative).
    """
    # Step 1: M_Z -> M_PS (SM + BCC-defect)
    a1_PS, a2_PS, a3_PS = step1_run(M_PS, delta_b)
    # Pati-Salam matching at M_PS
    a4_PS, a2L_PS, a2R_PS = pati_salam_matching(a1_PS, a2_PS, a3_PS)
    # Step 2: find M_GUT where the three PS couplings meet
    # Try pairwise meeting + check the third
    # alpha_4^-1(mu) = alpha_4_PS - (b_4/2pi)*ln(mu/M_PS)
    # alpha_{2L}^-1(mu) = alpha_2L_PS - (b_2L/2pi)*ln(mu/M_PS)
    # alpha_{2R}^-1(mu) = alpha_2R_PS - (b_2R/2pi)*ln(mu/M_PS)

    # 4 == 2L:
    if b_4_PS != b_2L_PS:
        log_M_GUT_4_2L = (a4_PS - a2L_PS) / ((b_4_PS - b_2L_PS) / (2*math.pi)) + math.log(M_PS)
        M_GUT_4_2L = math.exp(log_M_GUT_4_2L)
    else:
        M_GUT_4_2L = float('nan')
    # 4 == 2R:
    if b_4_PS != b_2R_PS:
        log_M_GUT_4_2R = (a4_PS - a2R_PS) / ((b_4_PS - b_2R_PS) / (2*math.pi)) + math.log(M_PS)
        M_GUT_4_2R = math.exp(log_M_GUT_4_2R)
    else:
        M_GUT_4_2R = float('nan')
    # 2L == 2R:
    if b_2L_PS != b_2R_PS:
        log_M_GUT_2L_2R = (a2L_PS - a2R_PS) / ((b_2L_PS - b_2R_PS) / (2*math.pi)) + math.log(M_PS)
        M_GUT_2L_2R = math.exp(log_M_GUT_2L_2R)
    else:
        # b_2L == b_2R (textbook minimal Pati-Salam):
        # 2L and 2R never meet unless they start equal.
        # Use geometric mean of 4-2L and 4-2R as M_GUT proxy.
        M_GUT_2L_2R = float('nan')

    # Use M_GUT = geometric mean of valid pairwise meetings
    valid_M = [m for m in (M_GUT_4_2L, M_GUT_4_2R, M_GUT_2L_2R) if not math.isnan(m) and m > M_PS]
    if not valid_M:
        return float('nan'), float('nan'), float('inf')
    if len(valid_M) > 1:
        # log-mean
        log_M_GUT = sum(math.log(m) for m in valid_M) / len(valid_M)
        M_GUT = math.exp(log_M_GUT)
    else:
        M_GUT = valid_M[0]

    # Couplings at M_GUT
    a4_GUT, a2L_GUT, a2R_GUT = step2_run(a4_PS, a2L_PS, a2R_PS, M_PS, M_GUT)

    # Unification quality: RMS of (alpha_i^-1 - mean) / mean
    mean_inv = (a4_GUT + a2L_GUT + a2R_GUT) / 3.0
    if mean_inv <= 0:
        return M_GUT, mean_inv, float('inf')
    rms = math.sqrt(((a4_GUT - mean_inv)**2 + (a2L_GUT - mean_inv)**2 + (a2R_GUT - mean_inv)**2) / 3.0)
    rms_rel = rms / abs(mean_inv)

    return M_GUT, mean_inv, rms_rel


# ---------------- Search ----------------------------------------------
M_PS_grid = [10**x for x in [9, 9.5, 10, 10.5, 11, 11.5, 12, 12.5, 13, 13.5, 14, 14.5, 15]]  # GeV
delta_b_range = list(range(-2, 3))  # -2, -1, 0, +1, +2
PROTON_DECAY_MIN_M_GUT = 4.0e15  # GeV (Super-K bound, rough)

# Phenomenological scan: try all (Delta b_1, Delta b_2, Delta b_3) on the grid
all_results = []
for db_1 in delta_b_range:
    for db_2 in delta_b_range:
        for db_3 in delta_b_range:
            for M_PS in M_PS_grid:
                M_GUT, alpha_GUT_inv, rms_rel = find_unification(M_PS, (db_1, db_2, db_3))
                if math.isnan(M_GUT) or math.isinf(rms_rel):
                    continue
                if M_GUT < M_PS:
                    continue
                all_results.append({
                    "delta_b": (db_1, db_2, db_3),
                    "M_PS": M_PS,
                    "M_GUT": M_GUT,
                    "alpha_GUT_inv": alpha_GUT_inv,
                    "rms_rel": rms_rel,
                    "M_GUT_safe": M_GUT >= PROTON_DECAY_MIN_M_GUT,
                })

# Sort by unification quality (smaller rms_rel = better)
all_results.sort(key=lambda r: r["rms_rel"])
top_unif = [r for r in all_results if r["rms_rel"] < 0.10]      # <10% spread
top_safe = [r for r in top_unif if r["M_GUT_safe"]]              # also proton-decay safe

print("=" * 80)
print(" Math77-Q6b two-step RGE scan results")
print("=" * 80)
print(f"  M_PS grid: {len(M_PS_grid)} values from 1e9 to 1e15 GeV")
print(f"  Delta_b grid: {len(delta_b_range)}^3 = {len(delta_b_range)**3} combinations")
print(f"  Total scan points: {len(M_PS_grid) * len(delta_b_range)**3}")
print(f"  Valid unification candidates: {len(all_results)}")
print(f"  With unification RMS < 10%: {len(top_unif)}")
print(f"  Also proton-decay safe (M_GUT >= 4e15 GeV): {len(top_safe)}")
print()

print("=" * 80)
print(" Top-10 unification candidates by quality")
print("=" * 80)
print(f"  {'rank':>4} {'Delta b_1,2,3':>14} {'M_PS':>10} {'M_GUT':>10} {'1/alpha_GUT':>11} {'rms%':>6} {'safe?':>5}")
for i, r in enumerate(all_results[:10], 1):
    print(f"  {i:>4} {str(r['delta_b']):>14} {r['M_PS']:>10.2e} {r['M_GUT']:>10.2e} {r['alpha_GUT_inv']:>11.2f} {r['rms_rel']*100:>6.2f} {str(r['M_GUT_safe']):>5}")

print()
print("=" * 80)
print(" Top-10 candidates that are ALSO proton-decay safe")
print("=" * 80)
if top_safe:
    print(f"  {'rank':>4} {'Delta b_1,2,3':>14} {'M_PS':>10} {'M_GUT':>10} {'1/alpha_GUT':>11} {'rms%':>6}")
    for i, r in enumerate(top_safe[:10], 1):
        print(f"  {i:>4} {str(r['delta_b']):>14} {r['M_PS']:>10.2e} {r['M_GUT']:>10.2e} {r['alpha_GUT_inv']:>11.2f} {r['rms_rel']*100:>6.2f}")
else:
    print("  (none)")

print()
print("=" * 80)
print(" Verdict")
print("=" * 80)

if len(top_safe) > 0:
    best_safe = top_safe[0]
    verdict = "SUCCESS"
    print(f"  SUCCESS: {len(top_safe)} (Delta_b, M_PS) combinations achieve")
    print(f"  unification at proton-decay-safe M_GUT.")
    print(f"  Best: Delta_b = {best_safe['delta_b']}, M_PS = {best_safe['M_PS']:.2e} GeV,")
    print(f"        M_GUT = {best_safe['M_GUT']:.2e} GeV, alpha_GUT^-1 = {best_safe['alpha_GUT_inv']:.2f},")
    print(f"        unification RMS = {best_safe['rms_rel']*100:.2f}%.")
elif len(top_unif) > 0:
    best_unif = top_unif[0]
    verdict = "PARTIAL"
    print(f"  PARTIAL: {len(top_unif)} combinations achieve unification (<10% RMS),")
    print(f"  but none satisfies the proton-decay safety bound (M_GUT >= 4e15 GeV).")
    print(f"  Best (unification only): Delta_b = {best_unif['delta_b']}, M_PS = {best_unif['M_PS']:.2e} GeV,")
    print(f"        M_GUT = {best_unif['M_GUT']:.2e} GeV (BELOW PROTON-DECAY THRESHOLD).")
else:
    verdict = "FAILURE"
    print("  FAILURE: no (Delta_b, M_PS) combination on the scanned grid")
    print("  achieves unification with <10% RMS spread.")
    if all_results:
        best = all_results[0]
        print(f"  Best (poor): Delta_b = {best['delta_b']}, M_PS = {best['M_PS']:.2e},")
        print(f"        M_GUT = {best['M_GUT']:.2e}, RMS = {best['rms_rel']*100:.2f}%.")

# Save full result
out_path = Path(__file__).parent / "Math77_Q6b_two_step_RGE_results.json"
out = {
    "theory_tag": "Math77-Q6b-Addendum-B-PS-two-step-RGE-2026-04-24",
    "framework": "1-loop SM (with BCC-defect Delta_b_i) M_Z -> M_PS, then 1-loop minimal Pati-Salam M_PS -> M_GUT, with PS matching at M_PS",
    "initial_conditions_at_MZ": {
        "M_Z_GeV": M_Z,
        "alpha_1_inv": alpha_1_inv_MZ,
        "alpha_2_inv": alpha_2_inv_MZ,
        "alpha_3_inv": alpha_3_inv_MZ,
    },
    "SM_beta_coefficients": {"b_1": b_1_SM, "b_2": b_2_SM, "b_3": b_3_SM},
    "PS_beta_coefficients": {"b_4": b_4_PS, "b_2L": b_2L_PS, "b_2R": b_2R_PS},
    "scan_parameters": {
        "M_PS_grid_GeV": M_PS_grid,
        "delta_b_grid": list(delta_b_range),
        "proton_decay_min_M_GUT_GeV": PROTON_DECAY_MIN_M_GUT,
    },
    "summary": {
        "total_scan_points": len(M_PS_grid) * len(delta_b_range)**3,
        "valid_candidates": len(all_results),
        "good_unification_count": len(top_unif),
        "good_and_safe_count": len(top_safe),
        "verdict": verdict,
    },
    "top_10_by_quality": all_results[:10],
    "top_10_safe": top_safe[:10],
}
with open(out_path, "w") as f:
    json.dump(out, f, indent=2)
print(f"\n  Results saved to: {out_path}")
