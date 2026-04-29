#!/usr/bin/env python3
"""
compute_RF5.py v1.0

Math110 Gate F5 verification.
Computes R_F5 = a_BCC^cont / (4 * sqrt(pi) * ell_P^TECT)
where ell_P^TECT must be derived INDEPENDENTLY of a_BCC
to make R_F5 a non-trivial consistency check.

Per Math110-AddI Theorem F5:
  ell_P^2 = G_TECT * hbar_TECT / c_TECT^3
where:
  - G_TECT comes from Pillar 3 graviton-emergence (Math45/46c)
  - hbar_TECT comes from Math60-C QO1 zero-point energy
  - c_TECT comes from Math57-AddA shell-mode speed (= c by Pillar 2)

Pre-registered Gate F5 (CLAUDE.md sec 6.3.3):
  PASS: |R_F5 - 1| <= 0.1
  MARGINAL: 0.1 < |R_F5 - 1| <= 0.3
  FAIL: |R_F5 - 1| > 0.3

Usage
-----
python Codes/tools/compute_RF5.py \
    --aBCC-continuum Runs/audit/aBCC_continuum_*.json \
    --G-tect-source Runs/audit/G_tect_from_Math45.json \
    --hbar-tect-source Runs/audit/hbar_tect_from_Math60-C.json \
    [--c-tect 1.0]   # default natural units
    --output Runs/audit/RF5_verdict_<date>.json
    [--verbose]

Sources of independently-measured constants:
  1. G_TECT: from Math45/Math46c gravitational coupling extraction.
     File should be JSON with key "G_TECT_natural_units" (numerical).
     If file unavailable, falls back to placeholder via --G-placeholder.
  2. hbar_TECT: from Math60-C QO1 closed form
     E_vac^(hbar) = (2.3 +/- 0.3) * 10^-2 * hbar
     => hbar_TECT = E_vac_measured / 0.023
  3. c_TECT: default 1.0 (TECT natural units, Math57-AddA Lorentz emergence).

Output (JSON):
  {
    "timestamp": "...",
    "inputs": {
      "a_BCC_cont": ..., "sigma_a": ...,
      "G_TECT": ..., "G_source": "...",
      "hbar_TECT": ..., "hbar_source": "...",
      "c_TECT": ...
    },
    "derived": {
      "ell_P_TECT": ...,
      "sigma_ell_P": ...,
      "expected_a_BCC": 4*sqrt(pi)*ell_P_TECT,
    },
    "R_F5": {
      "value": ..., "sigma": ...,
      "deviation_from_1": ...,
      "verdict": "PASS|MARGINAL|FAIL",
      "gate_pass_threshold": 0.1
    },
    "pillar10_status_action": "PROVED CONDITIONAL upgrade ready" | "FAIL diagnostic"
  }
"""
import argparse
import json
import math
import sys
import glob
from pathlib import Path
from datetime import datetime, timezone


def load_json_glob(pattern):
    """Resolve glob and load most recent JSON file."""
    files = sorted(glob.glob(pattern))
    if not files:
        return None, None
    latest = files[-1]
    try:
        with open(latest) as f:
            return json.load(f), latest
    except Exception as e:
        print(f"  [WARN] could not parse {latest}: {e}", file=sys.stderr)
        return None, latest


def extract_aBCC_continuum(json_data):
    """Extract a_BCC_cont and uncertainty from compute_aBCC_continuum output."""
    if not json_data:
        return None, None
    cont = json_data.get('continuum', {})
    a = cont.get('a_BCC_cont')
    sigma = cont.get('uncertainty', 0.0)
    return a, sigma


def extract_G_TECT(json_data, default=None):
    """Extract G_TECT from Math45/Math46c output."""
    if not json_data:
        return default, "fallback_placeholder"
    for key in ['G_TECT_natural_units', 'G_TECT', 'G', 'newton_constant']:
        if key in json_data:
            return json_data[key], f"key:{key}"
    return default, "fallback_placeholder"


def extract_hbar_TECT(json_data, default=None):
    """Extract hbar_TECT from Math60-C QO1 output.
    Math60-C-AddA: E_vac^(hbar) = (2.3 +/- 0.3) x 10^-2 * hbar
    => hbar = E_vac / 0.023
    """
    if not json_data:
        return default, "fallback_placeholder"
    for key in ['hbar_TECT', 'hbar']:
        if key in json_data:
            return json_data[key], f"key:{key}"
    if 'E_vac' in json_data:
        try:
            E_vac = float(json_data['E_vac'])
            kappa = json_data.get('kappa_vac', 0.023)
            return E_vac / kappa, "derived:E_vac/0.023"
        except (ValueError, ZeroDivisionError):
            pass
    return default, "fallback_placeholder"


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--aBCC-continuum', required=True,
                   help='JSON output from compute_aBCC_continuum.py (glob accepted)')
    p.add_argument('--G-tect-source', default=None,
                   help='JSON file with G_TECT (key: G_TECT_natural_units)')
    p.add_argument('--hbar-tect-source', default=None,
                   help='JSON file with hbar_TECT or E_vac for derivation')
    p.add_argument('--c-tect', type=float, default=1.0,
                   help='Speed of light in TECT natural units (default 1.0 by Pillar 2)')
    p.add_argument('--G-placeholder', type=float, default=None,
                   help='Override G_TECT (use only when source not available)')
    p.add_argument('--hbar-placeholder', type=float, default=None,
                   help='Override hbar_TECT (use only when source not available)')
    p.add_argument('--output', required=True)
    p.add_argument('--pass-threshold', type=float, default=0.1)
    p.add_argument('--marginal-threshold', type=float, default=0.3)
    p.add_argument('--verbose', action='store_true')
    args = p.parse_args()

    print(f"=== compute_RF5 v1.0 ===")
    print(f"  Math110 Gate F5 verification")
    print(f"  R_F5 := a_BCC^cont / (4*sqrt(pi) * ell_P^TECT)")
    print()

    # Load a_BCC^cont
    a_BCC_data, a_path = load_json_glob(args.aBCC_continuum)
    if a_BCC_data is None:
        print(f"FATAL: cannot load aBCC_continuum from {args.aBCC_continuum}", file=sys.stderr)
        sys.exit(2)
    a_BCC_cont, sigma_a = extract_aBCC_continuum(a_BCC_data)
    if a_BCC_cont is None:
        print(f"FATAL: a_BCC_cont not found in {a_path}", file=sys.stderr)
        sys.exit(3)
    print(f"  [INPUT] a_BCC^cont = {a_BCC_cont:.6f} (sigma={sigma_a:.2e}) from {a_path}")

    # Load G_TECT
    G_TECT, G_source = None, "missing"
    if args.G_tect_source:
        G_data, G_path = load_json_glob(args.G_tect_source)
        G_TECT, G_source = extract_G_TECT(G_data, args.G_placeholder)
        if G_path: G_source = f"{G_path}:{G_source}"
    elif args.G_placeholder is not None:
        G_TECT, G_source = args.G_placeholder, "CLI_placeholder"
    if G_TECT is None:
        print(f"FATAL: G_TECT unavailable. Provide --G-tect-source or --G-placeholder", file=sys.stderr)
        print(f"       Math110-AddG analytical formula: G = c^4 / (16*pi*rho_cond*a_BCC^2)", file=sys.stderr)
        print(f"       Pillar 3 (Math45/46c) gravity-emergence run produces independent G_TECT", file=sys.stderr)
        sys.exit(4)
    print(f"  [INPUT] G_TECT = {G_TECT:.6e} ({G_source})")

    # Load hbar_TECT
    hbar_TECT, hbar_source = None, "missing"
    if args.hbar_tect_source:
        hbar_data, hbar_path = load_json_glob(args.hbar_tect_source)
        hbar_TECT, hbar_source = extract_hbar_TECT(hbar_data, args.hbar_placeholder)
        if hbar_path: hbar_source = f"{hbar_path}:{hbar_source}"
    elif args.hbar_placeholder is not None:
        hbar_TECT, hbar_source = args.hbar_placeholder, "CLI_placeholder"
    if hbar_TECT is None:
        print(f"FATAL: hbar_TECT unavailable. Provide --hbar-tect-source or --hbar-placeholder", file=sys.stderr)
        print(f"       Math60-C-AddA: E_vac^(hbar) = (2.3 +/- 0.3) x 10^-2 * hbar", file=sys.stderr)
        sys.exit(5)
    print(f"  [INPUT] hbar_TECT = {hbar_TECT:.6e} ({hbar_source})")

    c_TECT = args.c_tect
    print(f"  [INPUT] c_TECT = {c_TECT:.6f} (Pillar 2 default)")

    # Derive ell_P^TECT
    ell_P_TECT_squared = G_TECT * hbar_TECT / (c_TECT**3)
    if ell_P_TECT_squared <= 0:
        print(f"FATAL: ell_P^2 = {ell_P_TECT_squared} (non-positive)", file=sys.stderr)
        sys.exit(6)
    ell_P_TECT = math.sqrt(ell_P_TECT_squared)
    expected_a_BCC = 4 * math.sqrt(math.pi) * ell_P_TECT

    # Compute R_F5
    R_F5 = a_BCC_cont / expected_a_BCC
    deviation = abs(R_F5 - 1.0)

    # Verdict
    if deviation <= args.pass_threshold:
        verdict = "PASS"
        action = "PROVED CONDITIONAL upgrade ready -- Pillar 10 phase-transition origin numerical closure achieved"
    elif deviation <= args.marginal_threshold:
        verdict = "MARGINAL"
        action = "MARGINAL -- review Math82-H continuum extrapolation accuracy + Math45 G_TECT precision"
    else:
        verdict = "FAIL"
        action = "FAIL -- run Math110-AddE sec 6 contingency protocols (4-step diagnostic)"

    # Uncertainty propagation (rough)
    rel_sigma_a = (sigma_a / a_BCC_cont) if a_BCC_cont != 0 else 0.0
    sigma_R_F5 = R_F5 * rel_sigma_a

    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'tool': 'compute_RF5.py v1.0',
        'inputs': {
            'a_BCC_cont': a_BCC_cont,
            'sigma_a_BCC_cont': sigma_a,
            'a_BCC_source': str(a_path),
            'G_TECT': G_TECT,
            'G_source': G_source,
            'hbar_TECT': hbar_TECT,
            'hbar_source': hbar_source,
            'c_TECT': c_TECT,
        },
        'derived': {
            'ell_P_TECT_squared': ell_P_TECT_squared,
            'ell_P_TECT': ell_P_TECT,
            'expected_a_BCC_eq_4sqrt_pi_ell_P': expected_a_BCC,
        },
        'R_F5': {
            'value': R_F5,
            'sigma': sigma_R_F5,
            'deviation_from_1': deviation,
            'pass_threshold': args.pass_threshold,
            'marginal_threshold': args.marginal_threshold,
            'verdict': verdict,
        },
        'pillar10_status_action': action,
        'theorem_reference': 'Math110-AddI Theorem F5; Math113 Final Closure',
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)

    print()
    print(f"=== Math110 Gate F5 verdict ===")
    print(f"  ell_P^TECT     = {ell_P_TECT:.6e}")
    print(f"  expected a_BCC = 4*sqrt(pi)*ell_P = {expected_a_BCC:.6f}")
    print(f"  measured a_BCC = {a_BCC_cont:.6f}")
    print(f"  R_F5           = {R_F5:.6f} +/- {sigma_R_F5:.2e}")
    print(f"  |R_F5 - 1|     = {deviation:.6f}  (threshold {args.pass_threshold})")
    print(f"  ==>  Verdict: {verdict}")
    print(f"  Output: {out_path}")
    print(f"  Action: {action}")
    sys.exit(0 if verdict == 'PASS' else (1 if verdict == 'MARGINAL' else 2))


if __name__ == '__main__':
    main()
