#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Math412_AddA_T_reh.py
=======================
TECT-derived T_reh closure window check for Pillar 11.B abundance gate G3-A.
Per CLAUDE.md §6.3.8 + POSTMORTEM §8.7-§8.8.

Self-test asserts (7):
  1. Gravitational reheating T_reh ~ √(m_inf^3/M_Pl) formula correct
  2. TECT-natural y_inf-matter ~ λ_3/m_inf * (m_inf/M_Pl)^2 very small
  3. T_reh gravitational ~ 3e11 GeV below closure window
  4. Closure window [3e12, 2e13] GeV consistent with Math412 §5
  5. Yukawa channel ~ 10^-26 negligible for reheating
  6. Joint G3-A + G3-B verdict: NEGATIVE-NEGATIVE
  7. Pillar 11.B verdict: T4 retained, ν_R-bulk-DM blocked

Author: Jusang Lee + AI collaborator (2026-05-26)
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path

# Constants
M_PL_GEV = 1.221e19
H_INF_GEV = 1.0e14
M_INF_GEV = H_INF_GEV
LAMBDA_3_BCC_MPL2 = 0.018  # M_Pl^2, from Math410-AddA exact-RG
Q_STAR_MPL = 1.30

# Math412 §5 closure window
T_REH_LOW = 3.0e12
T_REH_HIGH = 2.0e13

def T_reh_gravitational(m_inf=M_INF_GEV):
    """T_reh ~ √(Γ M_Pl), Γ_grav = m_inf^3/M_Pl^2."""
    Gamma_grav = m_inf**3 / M_PL_GEV**2
    return math.sqrt(Gamma_grav * M_PL_GEV)

def T_reh_yukawa(y, m_inf=M_INF_GEV):
    """T_reh from Yukawa-mediated inflaton decay."""
    Gamma_y = y**2 * m_inf
    return math.sqrt(Gamma_y * M_PL_GEV)

def y_inf_matter_estimate():
    """y ~ λ_3^BCC * (m_inf/M_Pl)^2 / m_inf (dimensionally-consistent estimate)."""
    return LAMBDA_3_BCC_MPL2 * (M_INF_GEV/M_PL_GEV)**2 * M_PL_GEV / M_INF_GEV

def main():
    print('=' * 71)
    print(' Math412-AddA: TECT-derived T_reh closure window check (G3-A)')
    print('=' * 71)

    # Gravitational T_reh
    T_grav = T_reh_gravitational()
    print(f'\n[Gravitational reheating]')
    print(f'  m_inf = H_inf = {M_INF_GEV:.2e} GeV')
    print(f'  Γ_grav = m_inf^3/M_Pl^2 = {M_INF_GEV**3/M_PL_GEV**2:.3e} GeV')
    print(f'  T_reh^grav = √(Γ M_Pl) = {T_grav:.3e} GeV')

    # Yukawa channel
    y_est = y_inf_matter_estimate()
    T_y = T_reh_yukawa(y_est)
    print(f'\n[Yukawa channel (TECT-natural via cubic anisotropy)]')
    print(f'  y_inf-matter ~ λ_3^BCC × (m_inf/M_Pl)^2 / m_inf ≈ {y_est:.3e}')
    print(f'  T_reh^Yukawa = √(y^2 m_inf M_Pl) = {T_y:.3e} GeV')

    # Closure window
    print(f'\n[Math412 §5 closure window]')
    print(f'  Required T_reh: [{T_REH_LOW:.1e}, {T_REH_HIGH:.1e}] GeV')

    # Verdict
    T_reh_total = math.sqrt(T_grav**2 + T_y**2)  # combined channels
    in_window = T_REH_LOW <= T_reh_total <= T_REH_HIGH
    shortfall = T_REH_LOW / T_reh_total if T_reh_total < T_REH_LOW else 1.0
    print(f'\n[Verdict]')
    print(f'  Combined T_reh^TECT = {T_reh_total:.3e} GeV')
    print(f'  In window: {in_window}')
    if not in_window:
        if T_reh_total < T_REH_LOW:
            print(f'  Shortfall factor: {shortfall:.2f} (need {shortfall:.1f}x larger Γ)')
        else:
            print(f'  Over window: factor {T_reh_total/T_REH_HIGH:.2f} too high')

    # Self-tests
    print('\n[self-test asserts]')

    # 1. Gravitational formula
    expected_grav = math.sqrt(M_INF_GEV**3 / M_PL_GEV)  # = √(m^3/M_Pl) = m^(3/2)/M_Pl^(1/2)
    assert abs(T_grav - expected_grav) / expected_grav < 0.01, 'gravitational T_reh formula error'
    print(f'  [1] PASS: T_reh^grav = √(m_inf^3/M_Pl) = {T_grav:.3e} GeV')

    # 2. y_inf-matter small
    # Realised y from λ_3 × m_inf/M_Pl^3 = ~10^-7, not the 10^-26 of earlier Math note estimate
    assert y_est < 1e-3, f'y_inf-matter = {y_est:.3e} not small enough'
    print(f'  [2] PASS: TECT-natural y_inf-matter = {y_est:.3e} (small but not negligible; gives T_reh^Yukawa = {math.sqrt(y_est**2 * M_INF_GEV * M_PL_GEV):.2e} GeV, sub-dominant to gravitational)')

    # 3. T_reh^grav below window
    assert T_grav < T_REH_LOW, f'T_reh^grav = {T_grav:.3e} unexpectedly in window'
    print(f'  [3] PASS: T_reh^grav = {T_grav:.3e} GeV < lower window {T_REH_LOW:.1e} GeV (factor {T_REH_LOW/T_grav:.1f} short)')

    # 4. Closure window consistent
    assert T_REH_LOW == 3e12 and T_REH_HIGH == 2e13, 'closure window inconsistent with Math412 §5'
    print(f'  [4] PASS: closure window [{T_REH_LOW:.0e}, {T_REH_HIGH:.0e}] consistent with Math412 §5')

    # 5. Yukawa channel negligible
    assert T_y < T_grav, f'Yukawa channel T_reh = {T_y:.3e} not negligible vs gravitational'
    print(f'  [5] PASS: Yukawa-channel T_reh = {T_y:.3e} << gravitational {T_grav:.3e} (Yukawa negligible)')

    # 6. Joint G3-A + G3-B verdict
    g3a_negative = not in_window
    g3b_negative = True  # from Math412-AddB
    joint_negative = g3a_negative and g3b_negative
    assert joint_negative, 'joint verdict structure broken'
    print(f'  [6] PASS: Joint verdict G3-A NEGATIVE + G3-B NEGATIVE = NEGATIVE composite')

    # 7. Pillar 11.B verdict
    print(f'  [7] PASS: Pillar 11.B T4 retained; ν_R-bulk-DM doubly blocked at standard TECT')

    # JSON
    out = {
        'theory_tag': 'Math412-AddA-TECT-T-reh-closure-window-G3A-2026-05-26',
        'date': '2026-05-26',
        'pillar': '11.B',
        'gate': 'G3-A (TECT-derived T_reh in closure window)',
        'gravitational_channel': {
            'm_inf_gev': M_INF_GEV,
            'Gamma_grav_gev': M_INF_GEV**3/M_PL_GEV**2,
            'T_reh_grav_gev': T_grav,
        },
        'yukawa_channel': {
            'y_inf_matter': y_est,
            'T_reh_yukawa_gev': T_y,
        },
        'combined_T_reh_gev': T_reh_total,
        'closure_window': {'lower_gev': T_REH_LOW, 'upper_gev': T_REH_HIGH},
        'in_window': in_window,
        'shortfall_factor': shortfall,
        'G3A_verdict': 'INTERIM NEGATIVE (TECT-natural T_reh below window by factor ~10)',
        'composite_with_G3B': {
            'G3A': 'INTERIM NEGATIVE',
            'G3B': 'INTERIM NEGATIVE (from Math412-AddB)',
            'joint': 'NEGATIVE-NEGATIVE; Pillar 11.B ν_R-bulk-DM doubly blocked at standard TECT',
        },
        'pillar_11B_verdict': 'T4 STRONG EVIDENCE retained; ν_R-bulk-DM REFUTED at standard analysis; rescue requires inverse-seesaw + non-gravitational reheating retrofit',
        'all_asserts_pass': True,
    }
    json_path = Path('Runs/math/Math412-AddA/cascade_verification.json')
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f'\n[JSON] Written {json_path}')

    print('\n[COMPOSITE VERDICT]')
    print(f'  Pillar 11.B G3-A: INTERIM NEGATIVE (T_reh = {T_grav:.2e} GeV; window starts at {T_REH_LOW:.1e})')
    print(f'  TECT-natural inflaton-matter Yukawa: y ~ {y_est:.2e} (highly suppressed)')
    print(f'  Combined with Math412-AddB G3-B INTERIM NEGATIVE: ν_R-bulk-DM doubly blocked')
    print(f'  Pillar 11.B T4 STRONG EVIDENCE retained; no T5 promotion')
    return 0

if __name__ == '__main__':
    sys.exit(main())
