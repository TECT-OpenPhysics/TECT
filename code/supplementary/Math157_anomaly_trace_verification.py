"""
Math157 anomaly trace verification.

Computes the six perturbative gauge anomaly coefficients of the SM gauge
group G_SM = SU(3)_C x SU(2)_L x U(1)_Y on a single SO(10) spinor multiplet
\\mathbf{16}, using exact rational (fractions.Fraction) arithmetic. Verifies
the rigorous closure claim of Math157 §2.

Theory tag: Math157-SO10-SM-anomaly-cancellation-rigorous-trace-method-2026-04-26
Author: Jusang Lee (jtkor@outlook.com)

Usage:
    python3 Math157_anomaly_trace_verification.py

Falsification criterion: any non-zero coefficient invalidates the rigorous
closure claim of Math157 §2 and refers GAP 3 back to OPEN status. Exact
zeros are required (rational arithmetic, no floating-point tolerance).
"""
from fractions import Fraction as F


# Single SO(10) 16: SM-basis fermion content (Y_SM hypercharges).
#
# Schema: (label, Y_SM, total_components, SU(3)_rep, SU(2)_rep)
# All Weyl fermions in left-handed convention (RH SM particles -> conjugate).
fields = [
    ('Q',  F(1, 6),  6, 'fund_3', 'fund_2'),   # quark doublet, 3 colour x 2 weak
    ('uc', F(-2, 3), 3, 'anti_3', 'sing_2'),   # u^c (LH conjugate of RH up)
    ('dc', F(1, 3),  3, 'anti_3', 'sing_2'),   # d^c
    ('L',  F(-1, 2), 2, 'sing_3', 'fund_2'),   # lepton doublet
    ('ec', F(1, 1),  1, 'sing_3', 'sing_2'),   # e^c
    ('N',  F(0, 1),  1, 'sing_3', 'sing_2'),   # right-handed neutrino (singlet)
]


def A3(rep3):
    """Cubic SU(3) Dynkin index: A(3)=+1, A(3bar)=-1, A(1)=0."""
    return {'fund_3': 1, 'anti_3': -1, 'sing_3': 0}[rep3]


def T3(rep3):
    """SU(3) (quadratic) Dynkin index: T(fund)=T(antifund)=1/2."""
    return F(1, 2) if rep3 in ('fund_3', 'anti_3') else F(0, 1)


def T2(rep2):
    """SU(2) Dynkin index: T(2)=1/2."""
    return F(1, 2) if rep2 == 'fund_2' else F(0, 1)


def n3(rep3):
    """SU(3) multiplicity (dim of SU(3) rep)."""
    return 3 if rep3 in ('fund_3', 'anti_3') else 1


def n2(rep2):
    """SU(2) multiplicity (dim of SU(2) rep)."""
    return 2 if rep2 == 'fund_2' else 1


def compute_anomalies():
    """Return the six anomaly coefficients on a single 16 as exact rationals."""
    A_333 = sum(A3(r3) * n2(r2) for (_, _, _, r3, r2) in fields)
    A_222 = F(0, 1)  # SU(2) admits no symmetric d^abc
    A_33Y = sum(T3(r3) * n2(r2) * Y for (_, Y, _, r3, r2) in fields)
    A_22Y = sum(T2(r2) * n3(r3) * Y for (_, Y, _, r3, r2) in fields)
    A_YYY = sum(n * Y ** 3 for (_, Y, n, _, _) in fields)
    A_grY = sum(n * Y for (_, Y, n, _, _) in fields)
    return {
        'SU(3)^3':           A_333,
        'SU(2)^3':           A_222,
        'SU(3)^2 U(1)_Y':    A_33Y,
        'SU(2)^2 U(1)_Y':    A_22Y,
        'U(1)_Y^3':          A_YYY,
        'grav^2 U(1)_Y':     A_grY,
    }


def main():
    print('=' * 72)
    print('Math157 anomaly trace verification (single SO(10) 16, exact rationals)')
    print('=' * 72)
    A = compute_anomalies()
    for label, val in A.items():
        flag = 'PASS' if val == 0 else 'FAIL'
        print(f'  [{flag}]  A({label:<18}) = {val}')
    print('-' * 72)
    all_zero = all(v == 0 for v in A.values())
    if all_zero:
        print('VERDICT: all six anomaly coefficients vanish identically.')
        print('        Math157 §2 rigorous-closure claim VERIFIED.')
        return 0
    else:
        print('VERDICT: at least one coefficient is non-zero.')
        print('        Math157 §2 rigorous-closure claim FAILED.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
