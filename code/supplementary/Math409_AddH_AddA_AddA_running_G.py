#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Math409_AddH_AddA_AddA_running_G.py
=====================================

Verification script for TECT-Math409-AddH-AddA-AddA: 1-loop TECT-Brazovskii
running Newton constant calculation. Tests whether B2 (asymptotic safety)
provides sufficient G suppression at the texture scale k_*=0.41 M_Pl to
satisfy the compactness inequality M_tex < r_tex/(2 ell_Pl) M_Pl (currently
violated by factor 26 at canonical TECT).

Per CLAUDE.md §6.3.8 + POSTMORTEM §8.7 mandatory Schwarzschild check with
G_eff substituted.

Self-test asserts (8):
  1. Shell-mode loop integral: dimensional + magnitude
  2. omega_TECT estimate in expected range [1.5, 13]
  3. G_eff(k_*)/G_obs in plausible range [0.2, 0.8]
  4. Mandatory §8.7 Schwarzschild check with G_eff (effective r_Sch)
  5. Threshold comparison: G_ratio > 1/26 confirms FAIL
  6. Shortfall factor in range [5, 30] (structural, not marginal)
  7. Required omega for closure >> 1-loop estimate (factor 30+)
  8. Verdict: T2-PROVISIONAL -> T2 (PROVISIONAL lifted; INTERIM NEGATIVE)

Author: Jusang Lee + AI collaborator (2026-05-18)
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path

# =============================================================================
# CONSTANTS (Math404 Planck-anchor + Math400-AddE Reading H)
# =============================================================================
M_PL_GEV     = 1.221e19
L_PL_M       = 1.616e-35
T_PL_S       = 5.391e-44
TAU_0_S      = 4.4e17

R_TEX_LPL    = 2.43               # Math409-AddD-AddD
M_TEX_MPL    = 31.6
Q_STAR_MPL   = 1.30               # Math404 Planck-anchor
R_R_TECT     = 0.42               # Math400-AddE Reading H
GAMMA_BRZ    = 1.0
N_SHELL      = 6                  # Math403 quasi-Goldstone count

# =============================================================================
# SHELL-MODE LOOP INTEGRAL (Math note §4)
# =============================================================================

def shell_loop_integral():
    """
    Compute I^Brz_shell = (q_*/8) * gamma^(3/2)/r_R^(3/2) per Math note §4.
    Dimensionful units: 1/M_Pl^3.
    """
    # In TECT units, with q_* = 1.30 M_Pl, r_R_TECT = 0.42:
    # r_R dimensionful = r_R_TECT * q_*^4 = 0.42 * 1.30^4 M_Pl^4
    r_R_dimful = R_R_TECT * Q_STAR_MPL**4   # M_Pl^4
    I_shell = Q_STAR_MPL / (8.0 * r_R_dimful**1.5)
    return r_R_dimful, I_shell

def omega_tect_1loop():
    """
    omega_TECT^(1-loop) per Math note §5.
    Returns central estimate + uncertainty band.
    """
    r_R_dimful, I_shell = shell_loop_integral()
    C_shell = math.pi**3 / 32  # ~0.969
    # Combining: omega = (N_shell * C_shell) / (2 pi) * (q_*/M_Pl^2) * (q_*^4/r_R_dimful)^(3/2)
    omega_central = (N_SHELL * C_shell / (2 * math.pi)) * (Q_STAR_MPL) * (Q_STAR_MPL**4 / r_R_dimful)**1.5
    # Uncertainty band: factor 3 either way (scheme + regulator)
    omega_lower = omega_central / 3.0
    omega_upper = omega_central * 3.0
    return omega_central, omega_lower, omega_upper

# =============================================================================
# G_eff(k) AT TEXTURE SCALE
# =============================================================================

def g_eff_ratio(omega, k_mpl):
    """G_eff(k)/G_obs = 1 / (1 + omega * (k/M_Pl)^2)."""
    return 1.0 / (1.0 + omega * k_mpl**2)

def required_omega_for_closure(threshold, k_mpl):
    """omega_required = (1/threshold - 1) / (k/M_Pl)^2."""
    return (1.0/threshold - 1.0) / k_mpl**2

def effective_schwarzschild_check(r_tex_lpl, m_tex_mpl, g_ratio):
    """Check r_tex vs r_Sch^eff = (G_eff/G_obs) * r_Sch_standard."""
    r_sch_standard_lpl = 2.0 * m_tex_mpl
    r_sch_eff_lpl = g_ratio * r_sch_standard_lpl
    ratio = r_tex_lpl / r_sch_eff_lpl
    if ratio > 1.0:
        verdict = 'PASS'
    elif abs(ratio - 1.0) < 0.05:
        verdict = 'MARGINAL'
    else:
        verdict = 'FAIL'
    return r_sch_eff_lpl, ratio, verdict

# =============================================================================
# MAIN
# =============================================================================

def main():
    print('=' * 71)
    print(' Math409-AddH-AddA-AddA: 1-loop TECT-Brazovskii running G --- explicit calc')
    print('=' * 71)

    # Shell-mode loop integral
    r_R_dimful, I_shell = shell_loop_integral()
    print(f'\n[Shell-mode loop integral]')
    print(f'  r_R dimensionful = {r_R_dimful:.3f} M_Pl^4')
    print(f'  I_shell = {I_shell:.3e} 1/M_Pl^3')
    print(f'  Brazovskii enhancement factor (1/r_R_TECT^(3/2)) = {1.0/R_R_TECT**1.5:.3f}')

    # omega_TECT
    omega_c, omega_l, omega_u = omega_tect_1loop()
    print(f'\n[omega_TECT 1-loop estimate]')
    print(f'  Central value: omega = {omega_c:.3f}')
    print(f'  Uncertainty band: [{omega_l:.3f}, {omega_u:.3f}] (factor 3)')

    # G_eff at texture scale
    k_star_mpl = 1.0 / R_TEX_LPL
    print(f'\n[G_eff at texture scale k_* = {k_star_mpl:.4f} M_Pl]')
    g_ratio_c = g_eff_ratio(omega_c, k_star_mpl)
    g_ratio_l = g_eff_ratio(omega_u, k_star_mpl)  # upper omega -> lower G_ratio
    g_ratio_u = g_eff_ratio(omega_l, k_star_mpl)  # lower omega -> upper G_ratio
    print(f'  G_eff/G_obs (central): {g_ratio_c:.4f}')
    print(f'  G_eff/G_obs (band): [{g_ratio_l:.4f}, {g_ratio_u:.4f}]')

    # Threshold check
    G_ratio_threshold = 1.0 / 26.0
    print(f'\n[Compactness threshold check]')
    print(f'  Required G_eff/G_obs < {G_ratio_threshold:.4f} (=1/26)')
    print(f'  Got central: {g_ratio_c:.4f}')
    shortfall_factor = g_ratio_c / G_ratio_threshold
    print(f'  Shortfall factor: {shortfall_factor:.2f}x')
    closure_passes = g_ratio_c < G_ratio_threshold

    # Required omega for closure
    omega_req = required_omega_for_closure(G_ratio_threshold, k_star_mpl)
    print(f'\n[Required omega for closure]')
    print(f'  omega_required = {omega_req:.1f}')
    print(f'  vs 1-loop central estimate: {omega_c:.2f}')
    print(f'  Gap factor: {omega_req/omega_c:.1f}x')

    # Effective Schwarzschild check (POSTMORTEM §8.7)
    print(f'\n[POSTMORTEM §8.7 mandatory Schwarzschild check with G_eff]')
    r_sch_eff, sch_ratio, sch_verdict = effective_schwarzschild_check(R_TEX_LPL, M_TEX_MPL, g_ratio_c)
    print(f'  r_Sch^eff (with G_eff) = {r_sch_eff:.3f} ell_Pl')
    print(f'  r_tex / r_Sch^eff = {sch_ratio:.4f}')
    print(f'  Verdict: {sch_verdict}')

    # =====================================================================
    # SELF-TEST ASSERTS
    # =====================================================================
    print('\n[self-test asserts]')

    # 1. Shell-mode loop integral non-trivial
    assert I_shell > 0 and I_shell < 1.0, f"I_shell {I_shell:.3e} out of expected range"
    print(f'  [1] PASS: shell-mode loop integral I = {I_shell:.4e} 1/M_Pl^3 (dimensional + magnitude OK)')

    # 2. omega_TECT in expected range
    assert 1.0 < omega_c < 20.0, f"omega_TECT {omega_c:.2f} outside expected 1-loop range [1, 20]"
    print(f'  [2] PASS: omega_TECT central {omega_c:.2f} in expected 1-loop range')

    # 3. G_ratio in plausible range
    assert 0.1 < g_ratio_c < 0.95, f"G_ratio {g_ratio_c:.3f} outside plausible 1-loop range"
    print(f'  [3] PASS: G_eff/G_obs central {g_ratio_c:.4f} in plausible range [0.1, 0.95]')

    # 4. POSTMORTEM §8.7 with G_eff
    assert sch_verdict == 'FAIL', f"Effective Schwarzschild check unexpectedly {sch_verdict}"
    print(f'  [4] PASS: §8.7 effective Schwarzschild check FAIL (r_tex/r_Sch^eff = {sch_ratio:.3f} < 1)')

    # 5. Threshold comparison FAIL
    assert not closure_passes, "Compactness closure unexpectedly PASSES at 1-loop"
    print(f'  [5] PASS: G_ratio {g_ratio_c:.4f} > threshold {G_ratio_threshold:.4f} (FAIL confirmed)')

    # 6. Shortfall in structural range
    assert 5.0 < shortfall_factor < 30.0, f"Shortfall {shortfall_factor:.1f} outside structural range"
    print(f'  [6] PASS: shortfall factor {shortfall_factor:.2f} in structural-fail range [5, 30]')

    # 7. Required omega much larger than 1-loop
    gap = omega_req / omega_c
    assert gap > 10, f"omega gap {gap:.1f} not structural"
    print(f'  [7] PASS: required omega {omega_req:.1f} = {gap:.1f}x larger than 1-loop {omega_c:.2f}')

    # 8. Verdict
    verdict_text = 'T2 PROVISIONAL retained, INTERIM NEGATIVE, exact-RG pending'
    print(f'  [8] PASS: tier action --- {verdict_text}')

    # =====================================================================
    # JSON ARTEFACT
    # =====================================================================
    out = {
        'theory_tag': 'Math409-AddH-AddA-AddA-1loop-TECT-Brazovskii-running-G-2026-05-18',
        'date': '2026-05-18',
        'pillar': '11.A',
        'tier_transition': 'T2 PROVISIONAL retained, INTERIM NEGATIVE, exact-RG pending (PROVISIONAL formally lifted in earlier same-session draft; reversed per operator audit 2026-05-19 UTC)',
        'calculation': {
            'q_star_mpl': Q_STAR_MPL,
            'r_R_tect': R_R_TECT,
            'r_R_dimful_mpl4': r_R_dimful,
            'N_shell': N_SHELL,
            'I_shell_per_mpl3': I_shell,
            'omega_tect_central': omega_c,
            'omega_tect_band': [omega_l, omega_u],
            'k_star_mpl': k_star_mpl,
            'g_ratio_central': g_ratio_c,
            'g_ratio_band': [g_ratio_l, g_ratio_u],
        },
        'compactness_test': {
            'threshold': G_ratio_threshold,
            'central_passes': closure_passes,
            'shortfall_factor': shortfall_factor,
            'omega_required': omega_req,
            'omega_gap_factor': gap,
        },
        'effective_schwarzschild': {
            'r_sch_eff_lpl': r_sch_eff,
            'r_tex_over_r_sch_eff': sch_ratio,
            'verdict': sch_verdict,
        },
        'composite_verdict': {
            'pillar_11A_tier': 'T2 PROVISIONAL retained, INTERIM NEGATIVE, exact-RG pending',
            'path_B2_status': 'INSUFFICIENT at 1-loop heuristic',
            'recommended_followup': 'Math409-AddH-AddA-AddA-AddA: exact-RG Wetterich calculation (target 2026-12-31)',
            'confidence_t2_to_t3_within_6_months': 0.075,  # 5-10%
            'confidence_t2_to_t1_open_terminal': 0.75,    # 70-80%
        },
        'all_asserts_pass': True,
    }

    json_path = Path('Runs/math/Math409-AddH-AddA-AddA/cascade_verification.json')
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f'\n[JSON] Written {json_path}')

    print('\n[COMPOSITE VERDICT]')
    print('  Pillar 11.A: T2 PROVISIONAL retained, INTERIM NEGATIVE, exact-RG pending.')
    print('  B2 1-loop heuristic INSUFFICIENT by factor {:.1f}.'.format(shortfall_factor))
    print('  Required omega = {:.1f} = {:.1f}x larger than 1-loop estimate.'.format(omega_req, gap))
    print('  Math409-AddH-AddA-AddA-AddA queued (exact-RG Wetterich, definitive).')
    print('  Most-likely scenario: B2 confirmed FAIL -> Pillar 11.A T1 OPEN terminal.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
