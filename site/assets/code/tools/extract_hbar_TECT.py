#!/usr/bin/env python3
"""
extract_hbar_TECT.py v1.0

Extract hbar_TECT (quantum of action in TECT natural units) from
INDEPENDENT measurements -- spectrum-integral routes that do NOT
reduce to rho_cond*a_BCC^3*c (which would trivialize R_F5).

CRITICAL DESIGN GOAL
---------------------
hbar_TECT must be extracted from a physical observable that is NOT
the cell-action invariant Math98-main is built from. Otherwise
R_F5 = 1 trivially.

Independent extraction routes (priority order)
----------------------------------------------
ROUTE I (cleanest): Math60-C-AddC noise spectrum integral.
    S_PsiPsi(omega, k) = (hbar c_T^2 / (2 omega_k)) delta(omega - omega_k) Theta(omega).
    Equal-time fluctuation: <|psi(k)|^2>_vac = hbar c_T^2/(2 omega_k).
    Integrate over BCC shell -> measured <|Psi|^2>_vac (dimensionless).
    From Math60-C-AddC numerical eval: <|Psi|^2>_vac/phi_0^2 ~ 4e-2.
    Therefore: hbar = (<|Psi|^2>_meas/phi_0^2) * 8 pi^2 sqrt(Y) / (c_T q_0^2 ln(4/eps^2))
    Inputs: <|Psi|^2>_vac measured, phi_0, c_T, Y, q_0, eps.

ROUTE II: Math60-C-AddA QO1 zero-point energy ratio.
    E_vac^(hbar) = kappa_vac * hbar  with kappa_vac = (2.3 +/- 0.3) x 10^-2.
    Measure E_vac classically (vacuum fluctuation field-theory integral)
    in TECT-natural units, then hbar = E_vac_measured / kappa_vac.
    Independent of a_BCC IF E_vac_measured uses normalized eigenmodes.

ROUTE III (FALLBACK -- TRIVIAL): Math98 main formula
    hbar = rho_cond * a_BCC^3 * tau_PT
    WARNING: trivializes R_F5 = 1.

Usage
-----
python Codes/tools/extract_hbar_TECT.py \
    --route I|II|III \
    --route-I-Psi2-vac <value>  --route-I-phi0 0.266 \
    --route-I-Y 1.0 --route-I-q0 0.6801747616 --route-I-eps 0.065 \
    --route-I-cT 1.0
    [or --route-II-Evac <value> [--route-II-kappa 0.023]]
    [or --route-III-rho_cond <v> --route-III-aBCC <v> --route-III-tauPT <v>]
    --output Runs/audit/hbar_tect_<date>.json
"""
import argparse
import json
import math
import sys
from pathlib import Path
from datetime import datetime, timezone


def route_I(Psi2_meas, phi0, Y, q0, eps, cT):
    """From Math60-C-AddC: <|Psi|^2>_vac = hbar c_T q_0^2 / (8 pi^2 sqrt(Y)) ln(4/eps^2)
    Solve for hbar:
       hbar = <|Psi|^2>_vac * 8 pi^2 sqrt(Y) / (c_T q_0^2 ln(4/eps^2))
    """
    if any(v is None for v in (Psi2_meas, phi0, Y, q0, eps, cT)):
        return None, "missing_inputs"
    if eps <= 0 or Y <= 0 or q0 <= 0 or cT <= 0:
        return None, "non_positive_input"
    log_term = math.log(4.0 / (eps * eps))
    if log_term <= 0:
        return None, "log_term_non_positive"
    hbar = (Psi2_meas * 8.0 * math.pi**2 * math.sqrt(Y)) / (cT * q0 * q0 * log_term)
    return hbar, "route_I_Math60-C-AddC_noise_spectrum"


def route_II(E_vac_meas, kappa_vac=0.023):
    """From Math60-C-AddA: hbar = E_vac / kappa_vac."""
    if E_vac_meas is None or kappa_vac is None or kappa_vac == 0:
        return None, "missing_inputs"
    return E_vac_meas / kappa_vac, f"route_II_Math60-C-AddA_zero_point_kappa={kappa_vac}"


def route_III(rho_cond, a_BCC, tau_PT):
    """Fallback Math98 main. WARNING: trivializes F5."""
    if any(v is None for v in (rho_cond, a_BCC, tau_PT)):
        return None, "missing_inputs"
    return rho_cond * a_BCC**3 * tau_PT, "route_III_Math98_TRIVIAL_for_F5"


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--route', choices=['I', 'II', 'III'], required=True)
    # Route I
    p.add_argument('--route-I-Psi2-vac', type=float, default=None,
                   help='<|Psi|^2>_vac measured (Math60-C-AddC integrated noise)')
    p.add_argument('--route-I-phi0', type=float, default=0.266049)
    p.add_argument('--route-I-Y', type=float, default=1.0)
    p.add_argument('--route-I-q0', type=float, default=0.6801747616)
    p.add_argument('--route-I-eps', type=float, default=0.065,
                   help='Brazovskii shell-mass parameter (Math57-AddA)')
    p.add_argument('--route-I-cT', type=float, default=1.0)
    # Route II
    p.add_argument('--route-II-Evac', type=float, default=None,
                   help='Vacuum energy measured (TECT natural units)')
    p.add_argument('--route-II-kappa', type=float, default=0.023,
                   help='kappa_vac coefficient (Math60-C-AddA: 2.3e-2)')
    # Route III (TRIVIAL fallback)
    p.add_argument('--route-III-rho_cond', type=float, default=None)
    p.add_argument('--route-III-aBCC', type=float, default=None)
    p.add_argument('--route-III-tauPT', type=float, default=None)

    p.add_argument('--output', required=True)
    p.add_argument('--verbose', action='store_true')
    args = p.parse_args()

    print(f"=== extract_hbar_TECT v1.0 (route {args.route}) ===")
    hbar, label = None, None
    independent = False
    meta = {}

    if args.route == 'I':
        hbar, label = route_I(args.route_I_Psi2_vac, args.route_I_phi0, args.route_I_Y,
                              args.route_I_q0, args.route_I_eps, args.route_I_cT)
        independent = True
        meta = {
            'Psi2_vac_meas': args.route_I_Psi2_vac,
            'phi0': args.route_I_phi0, 'Y': args.route_I_Y,
            'q0': args.route_I_q0, 'eps': args.route_I_eps, 'cT': args.route_I_cT,
        }
    elif args.route == 'II':
        hbar, label = route_II(args.route_II_Evac, args.route_II_kappa)
        independent = True
        meta = {'E_vac_meas': args.route_II_Evac, 'kappa_vac': args.route_II_kappa}
    else:  # III
        hbar, label = route_III(args.route_III_rho_cond, args.route_III_aBCC, args.route_III_tauPT)
        independent = False  # CRITICAL: trivializes
        meta = {
            'rho_cond': args.route_III_rho_cond,
            'aBCC': args.route_III_aBCC,
            'tau_PT': args.route_III_tauPT,
            'WARNING': 'route III uses a_BCC; R_F5 will be trivially 1',
        }

    if hbar is None:
        print(f"FATAL: extraction failed: {label}", file=sys.stderr); sys.exit(2)

    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'tool': 'extract_hbar_TECT.py v1.0',
        'extraction_route': args.route,
        'route_label': label,
        'independent_of_aBCC': independent,
        'inputs': meta,
        'hbar_TECT': hbar,
    }
    out_path = Path(args.output); out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2))

    print(f"  hbar_TECT = {hbar:.6e}  ({label})")
    print(f"  independent_of_aBCC = {independent}")
    if not independent:
        print(f"  WARNING: route III trivializes F5.", file=sys.stderr)
    print(f"  Output: {out_path}")
    sys.exit(0 if independent else 4)


if __name__ == '__main__':
    main()
