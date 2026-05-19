#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Math409_AddH_compactness_audit.py
==================================

Corrective verification script for the Math409-AddH rollback (2026-05-18).

Audit-source: operator adversarial review identifying that Math409-AddH
mis-interpreted r_tex < r_Sch as "no horizon" — the correct GR reading
is "object compressed INSIDE its Schwarzschild radius = horizon present,
black-hole formation expected".

Compactness inequality (correct sign):
    r_tex > r_Sch(M_tex)     <=>     M_tex < (r_tex/2 ell_Pl) M_Pl
                              <=>     M_tex/M_Pl < r_tex/(2 ell_Pl)

If satisfied: no horizon, texture stable against BH collapse.
If violated: object inside Schwarzschild radius, BH forms, Hawking-
evaporates in t ~ (M/M_Pl)^3 t_Pl, FAST decay channel (a).

Per CLAUDE.md §6.3.8 (code+JSON archival of every Math note numerical
claim) + §6.3.4 (quantitative sanity check, sign-direction physics).

Verdict: texture-DM at current (r_tex, M_tex) values FAILS compactness
test by factor 26; classical GR REFUTES the configuration.

Output: Runs/math/Math409-AddH-compactness/cascade_verification.json

Self-test asserts (5):
  1. r_tex / r_Sch < 1 (texture inside Schwarzschild) -- audit fact
  2. Required compactness M_tex/M_Pl < r_tex/(2 ell_Pl) is VIOLATED
  3. Mass-reduction factor needed > 10 (significant rescue required)
  4. BH Hawking evaporation t_evap << tau_0 (channel (a) REFUTES)
  5. Verdict: T3 PROOF SKETCH (Math409-AddH) ROLLED BACK to T2 PROVISIONAL

Author: Jusang Lee + AI collaborator (2026-05-18, audit rollback)
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path

# Constants
M_PL_GEV  = 1.221e19
L_PL_M    = 1.616e-35
T_PL_S    = 5.391e-44
TAU_0_S   = 4.4e17

# Texture parameters (from Math409-AddD-AddD)
R_TEX_LPL  = 2.43
M_TEX_MPL  = 31.6

def main():
    print('=' * 71)
    print(' Math409-AddH COMPACTNESS AUDIT (operator-driven rollback, 2026-05-18)')
    print('=' * 71)

    # Compactness inequality
    r_sch_lpl     = 2.0 * M_TEX_MPL   # 2 (M/M_Pl) ell_Pl
    r_ratio       = R_TEX_LPL / r_sch_lpl
    m_max_compact = R_TEX_LPL / 2.0   # max M/M_Pl for compactness PASS
    m_reduction   = M_TEX_MPL / m_max_compact

    # Hawking evaporation timescale (if classical BH forms)
    t_evap_s      = (M_TEX_MPL)**3 * T_PL_S      # ~ (M/M_Pl)^3 t_Pl

    print()
    print('[Compactness inequality]')
    print(f'  r_tex          = {R_TEX_LPL:.3f} ell_Pl')
    print(f'  r_Sch(M_tex)   = {r_sch_lpl:.3f} ell_Pl')
    print(f'  r_tex / r_Sch  = {r_ratio:.4f}  ({"<" if r_ratio < 1 else ">="} 1)')
    print(f'  -> texture lies {"INSIDE" if r_ratio < 1 else "OUTSIDE"} its Schwarzschild radius')

    print()
    print('[Required mass for compactness PASS]')
    print(f'  M_tex < (r_tex/2 ell_Pl) M_Pl  =>  M_tex < {m_max_compact:.4f} M_Pl')
    print(f'  Actual M_tex                   =  {M_TEX_MPL:.2f} M_Pl')
    print(f'  Required reduction factor      =  {m_reduction:.2f}x')

    compactness_pass = M_TEX_MPL < m_max_compact

    print()
    print('[If classical BH forms (which it must under standard GR)]')
    print(f'  Hawking evaporation t_evap = (M/M_Pl)^3 * t_Pl')
    print(f'                              = {M_TEX_MPL:.1f}^3 * {T_PL_S:.2e} s')
    print(f'                              = {t_evap_s:.2e} s')
    print(f'  t_evap / tau_0              = {t_evap_s/TAU_0_S:.2e}')
    if t_evap_s < TAU_0_S:
        print('  --> EVAPORATES IN <<< cosmological timescale')
        print('  --> texture-DM REFUTED at classical GR + Hawking level')

    print()
    print('[Verdict]')
    if compactness_pass:
        verdict = 'Compactness PASS -- texture-DM viable (no BH collapse)'
        tier_action = 'maintain T3 PROOF SKETCH'
    else:
        verdict = 'Compactness FAIL -- texture-DM not GR-stable at current params'
        tier_action = (
            'ROLLBACK: Math409-AddH T2 PROVISIONAL -> T3 promotion is REVERSED. '
            'Pillar 11.A retained at T2 PROVISIONAL pending Math409-AddH-AddA '
            'compactness-corrected stability theorem.'
        )
    print(f'  {verdict}')
    print(f'  Action: {tier_action}')

    # Self-test asserts
    print()
    print('[self-test asserts]')
    assert r_ratio < 1.0, f"r_tex/r_Sch = {r_ratio:.3f} >= 1 (compactness already satisfied; rollback unnecessary)"
    print(f'  [1] PASS: r_tex/r_Sch = {r_ratio:.4f} < 1 (texture inside Schwarzschild, GR audit fact)')

    assert not compactness_pass, "Compactness inequality already satisfied -- audit moot"
    print(f'  [2] PASS: M_tex = {M_TEX_MPL:.2f} M_Pl > compactness bound {m_max_compact:.4f} M_Pl (VIOLATED, factor {m_reduction:.1f} over)')

    assert m_reduction > 10, f"Reduction factor {m_reduction:.2f} <= 10 -- rescue is minor, not structural"
    print(f'  [3] PASS: mass-reduction factor = {m_reduction:.2f}x > 10 (structural failure, not marginal)')

    assert t_evap_s < TAU_0_S, f"t_evap {t_evap_s:.2e} >= tau_0 {TAU_0_S:.2e} -- Hawking channel not decisive"
    print(f'  [4] PASS: t_evap = {t_evap_s:.2e} s << tau_0 = {TAU_0_S:.2e} s (factor 10^{math.log10(TAU_0_S/t_evap_s):.0f})')

    expected_action = 'ROLLBACK'
    assert expected_action in tier_action, f"Tier action does not contain '{expected_action}'"
    print(f'  [5] PASS: verdict = ROLLBACK Math409-AddH T3 promotion -> retain T2 PROVISIONAL')

    # JSON artefact
    out = {
        'theory_tag': 'Math409-AddH-compactness-audit-rollback-2026-05-18',
        'date': '2026-05-18',
        'audit_source': 'operator adversarial review (correct GR sign-direction)',
        'pillar': '11.A',
        'tier_transition': 'T3 PROOF SKETCH (Math409-AddH proposed) -> T2 PROVISIONAL (retained after rollback)',
        'rollback_reason': 'Math409-AddH mis-read r_tex < r_Sch as no-horizon; correct GR reading: texture compressed inside Schwarzschild = BH formation expected. Channel (a) is therefore NOT INAPPLICABLE but REFUTING (BH + Hawking evap in 1e-39 s).',
        'compactness': {
            'r_tex_lpl': R_TEX_LPL,
            'r_Sch_lpl': r_sch_lpl,
            'r_tex_over_r_Sch': r_ratio,
            'm_max_for_compactness_PASS_mpl': m_max_compact,
            'actual_m_tex_mpl': M_TEX_MPL,
            'reduction_factor_required': m_reduction,
            'compactness_PASS': compactness_pass,
        },
        'hawking_if_bh_forms': {
            't_evap_s': t_evap_s,
            't_evap_over_tau_0': t_evap_s / TAU_0_S,
            'channel_a_verdict': 'REFUTING (not INAPPLICABLE)',
        },
        'decisive_test_for_math409_addh_adda': {
            'test_form_1': 'M_tex < (r_tex / 2 ell_Pl) M_Pl  [classical GR compactness]',
            'current_violation_factor': m_reduction,
            'test_form_2': 'OR: TECT-internal QG theorem showing topological soliton avoids horizon despite r_tex < r_Sch',
        },
        'verdict': verdict,
        'tier_action': tier_action,
        'all_asserts_pass': True,
    }

    json_path = Path('Runs/math/Math409-AddH-compactness/cascade_verification.json')
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f'\n[JSON] Written {json_path}')

    print('\n[FINAL VERDICT] ROLLBACK CONFIRMED')
    print('  Pillar 11.A: T3 PROOF SKETCH -> T2 PROVISIONAL (retained)')
    print('  Math409-AddH AUDIT-FLAGGED for compactness sign-direction error')
    print('  Math409-AddD-AddD AUDIT-FLAGGED for same upstream error')
    print('  Math409-AddH-AddA scope REVISED: compactness-corrected stability theorem')
    return 0

if __name__ == '__main__':
    sys.exit(main())
