#!/usr/bin/env python3
"""
extract_G_TECT.py v1.0

Extract G_TECT (Newton's constant in TECT natural units) from
INDEPENDENT measurements -- specifically, the graviton-emergence
sector (Pillar 3, Math45 / Math46c).

CRITICAL DESIGN GOAL
---------------------
G_TECT must be measured WITHOUT using a_BCC, otherwise R_F5 becomes
trivially 1 (Math110-AddG matching loop is closed by construction).

Independent extraction routes (in priority order)
-------------------------------------------------
ROUTE A (cleanest): Math46c graviton-emergence simulation produces
    Z_h continuum-limit eta_TT propagator residue.  Newton's constant
    follows from:
        S_EH^(2)|_TT = (c^3/(64*pi*G)) * Integral [ (d h)^2 ]
    Matching to TECT-measured Z_h:
        G_TECT = c^3 / (64 * pi * Z_h_measured * eta_TT_pole)
    Inputs: Z_h (continuum-limit), eta_TT_pole_residue.

ROUTE B: From Math45 graviton dispersion measurement
    Stress-tensor 2-point function gives <T_munu T_rhosigma>(k) ~
    1/(G k^4) at low k. Fit <TT>(k) at small k to extract G_TECT.

ROUTE C (FALLBACK -- TRIVIAL): Math110-AddG self-consistent matching
        G_TECT = c^4 / (16*pi*rho_cond*a_BCC^2)
    WARNING: using this makes R_F5 = 1 trivially. Only use as
    consistency cross-check, not as F5 evidence.

Usage
-----
python Codes/tools/extract_G_TECT.py \
    --route A|B|C \
    --route-A-input <Z_h.json>     # for route A
    --route-A-eta-TT-pole <value>
    --route-B-input <TT_2pt.json>  # for route B
    --route-C-input <rho_cond.json> --route-C-aBCC <value>  # FALLBACK
    --c-tect 1.0
    --output Runs/audit/G_tect_<date>.json

Output JSON keys (compatible with compute_RF5.py):
    G_TECT_natural_units: float
    extraction_route: "A|B|C"
    independent_of_aBCC: true|false  (CRITICAL: must be true for non-trivial F5)
"""
import argparse
import json
import math
import sys
from pathlib import Path
from datetime import datetime, timezone


def route_A(z_h, eta_tt_pole, c_tect):
    """G = c^3 / (64*pi*Z_h*eta_TT_pole). Independent of a_BCC."""
    if z_h is None or eta_tt_pole is None or eta_tt_pole == 0:
        return None, "missing_inputs"
    G = c_tect**3 / (64 * math.pi * z_h * eta_tt_pole)
    return G, "route_A_Math46c_Zh_emergence"


def route_B(TT_residue_at_low_k, c_tect):
    """G = c^4 / TT_residue (with appropriate normalization).
    Math45 stress-tensor 2-point at k -> 0:
        <T_munu T_munu>(k) -> A / (G * k^4) + ...
    Therefore G = A / TT_residue.
    Coefficient A depends on TECT normalization conventions
    (typically A = c^4/(16*pi) or similar; document explicitly).
    """
    if TT_residue_at_low_k is None or TT_residue_at_low_k == 0:
        return None, "missing_inputs"
    A = c_tect**4 / (16 * math.pi)  # leading-order normalization, Math45 §3
    G = A / TT_residue_at_low_k
    return G, "route_B_Math45_TT_propagator"


def route_C(rho_cond, a_BCC, c_tect):
    """Fallback: Math110-AddG self-consistent. WARNING: trivializes F5."""
    if rho_cond is None or a_BCC is None or a_BCC == 0:
        return None, "missing_inputs"
    G = c_tect**4 / (16 * math.pi * rho_cond * a_BCC**2)
    return G, "route_C_Math110_AddG_TRIVIAL_for_F5"


def load_json_value(path, *keys):
    if not path:
        return None
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [WARN] cannot load {path}: {e}", file=sys.stderr)
        return None
    for k in keys:
        if k in data:
            return data[k]
        # nested support
        for v in data.values():
            if isinstance(v, dict) and k in v:
                return v[k]
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--route', choices=['A', 'B', 'C'], required=True)
    p.add_argument('--route-A-input', help='JSON with Z_h continuum value')
    p.add_argument('--route-A-eta-TT-pole', type=float, default=None,
                   help='eta_TT_pole_residue (Math46c §4)')
    p.add_argument('--route-B-input', help='JSON with TT_residue_at_low_k')
    p.add_argument('--route-C-input', help='JSON with rho_cond')
    p.add_argument('--route-C-aBCC', type=float, default=None)
    p.add_argument('--c-tect', type=float, default=1.0)
    p.add_argument('--output', required=True)
    p.add_argument('--verbose', action='store_true')
    args = p.parse_args()

    print(f"=== extract_G_TECT v1.0 (route {args.route}) ===")
    G, route_label = None, None
    independent_of_aBCC = False

    if args.route == 'A':
        z_h = load_json_value(args.route_A_input, 'Z_h', 'Z_h_continuum', 'Z_h_extrapolated')
        eta_pole = args.route_A_eta_TT_pole
        if eta_pole is None:
            eta_pole = load_json_value(args.route_A_input, 'eta_TT_pole', 'eta_TT_pole_residue')
        if z_h is None or eta_pole is None:
            print(f"FATAL: route A requires Z_h and eta_TT_pole", file=sys.stderr)
            print(f"  Z_h source: {args.route_A_input} -> {z_h}", file=sys.stderr)
            print(f"  eta_TT_pole: {eta_pole}", file=sys.stderr)
            sys.exit(2)
        G, route_label = route_A(z_h, eta_pole, args.c_tect)
        independent_of_aBCC = True
        meta = {'route': 'A', 'Z_h': z_h, 'eta_TT_pole': eta_pole}
    elif args.route == 'B':
        TT_residue = load_json_value(args.route_B_input,
                                     'TT_residue_at_low_k', 'TT_2pt_residue', 'stress_propagator_residue')
        if TT_residue is None:
            print(f"FATAL: route B requires TT_residue_at_low_k", file=sys.stderr); sys.exit(2)
        G, route_label = route_B(TT_residue, args.c_tect)
        independent_of_aBCC = True
        meta = {'route': 'B', 'TT_residue': TT_residue}
    else:  # C
        rho_cond = load_json_value(args.route_C_input, 'rho_cond', 'rho_cond_natural_units')
        a_BCC = args.route_C_aBCC
        if rho_cond is None or a_BCC is None:
            print(f"FATAL: route C requires rho_cond and aBCC", file=sys.stderr); sys.exit(2)
        G, route_label = route_C(rho_cond, a_BCC, args.c_tect)
        independent_of_aBCC = False  # CRITICAL: trivializes F5
        meta = {'route': 'C_TRIVIAL', 'rho_cond': rho_cond, 'a_BCC': a_BCC,
                'WARNING': 'route C uses a_BCC; R_F5 will be trivially 1'}

    if G is None:
        print(f"FATAL: extraction failed: {route_label}", file=sys.stderr); sys.exit(3)

    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'tool': 'extract_G_TECT.py v1.0',
        'extraction_route': args.route,
        'route_label': route_label,
        'independent_of_aBCC': independent_of_aBCC,
        'c_TECT': args.c_tect,
        'inputs': meta,
        'G_TECT_natural_units': G,
    }
    out_path = Path(args.output); out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2))

    print(f"  G_TECT = {G:.6e}  ({route_label})")
    print(f"  independent_of_aBCC = {independent_of_aBCC}")
    if not independent_of_aBCC:
        print(f"  WARNING: this G makes R_F5 trivially equal to 1.", file=sys.stderr)
        print(f"           Use route A or B for non-trivial F5 evaluation.", file=sys.stderr)
    print(f"  Output: {out_path}")
    sys.exit(0 if independent_of_aBCC else 4)


if __name__ == '__main__':
    main()
