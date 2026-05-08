#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Math49d_BWB_Zomega_exact.py
===========================

Independent symbolic verification of TECT-Math49d-R4-BWB-exact
(remediations PR-2 and PR-3 of the 2026-04-20 peer-review response).

What this script verifies
-------------------------
1.  The Borel-Weil-Bott concentration weight check:
        mu + rho = (6, 3, 2, 1, 0)  is strictly decreasing
    so H^q(Gr(2,5), Sym^2 Q) = 0 for all q > 0 and
    H^0(Gr(2,5), Sym^2 Q) ~= Sym^2 V  (dim 15).

2.  The exact Z[omega] closed form for the zeta^k-traces on Sym^2 V:
        chi_{zeta^k} = 6 omega^{2k} + 6 (-1)^k omega^k + 3       (eq. 8)
    and, equivalently, the six explicit integers
        (15, -3 - 12 omega, -3, 3, -3, -3 - 12 omega^2)          (eq. 5)
    with omega^3 = 1, 1 + omega + omega^2 = 0.

3.  The exact Z[omega] sum and quotient:
        sum_{k=0}^{5} chi_{zeta^k} = 18
        chi^{Z_6} = sum / 6        = 3   (in Z, after dividing out omega terms)

All arithmetic is performed symbolically using SymPy's cyclotomic
polynomial ring.  No floating-point arithmetic is used.  The script
exits non-zero if any check fails.

Policy
------
Archived per UPDATE_POLICY.md section 13 (code-manual discipline)
and the 2026-04-20 user directive ("proof code is saved permanently,
no inline shell").  Associated theory note:
    docs/math/TECT-Math49d-R4-BWB-exact.tex.txt
Peer-review response reference:
    docs/math/TECT-PeerReview-Response-2026-04-20.tex.txt
Status:  PR-2 and PR-3 closure verification.
Author:  TECT collaboration
Version: v1.0, 2026-04-20
"""

from __future__ import annotations

import sys
from typing import List

try:
    import sympy as sp
except Exception as exc:  # pragma: no cover
    print("[FATAL] sympy is required:", exc)
    sys.exit(2)


# ---------------------------------------------------------------
# Utility: simplify in Z[omega] via omega^2 + omega + 1 = 0
# ---------------------------------------------------------------
def z_omega_normal_form(expr: sp.Expr, omega: sp.Symbol) -> sp.Expr:
    """Reduce a polynomial in omega modulo (omega^2 + omega + 1)."""
    # Expand, then divmod by minimal polynomial.
    poly = sp.Poly(sp.expand(expr), omega)
    min_poly = sp.Poly(omega**2 + omega + 1, omega)
    _, rem = sp.div(poly, min_poly, domain=sp.ZZ)
    return sp.expand(rem.as_expr())


def eq_z_omega(a: sp.Expr, b: sp.Expr, omega: sp.Symbol) -> bool:
    """Equality test in Z[omega]."""
    return sp.simplify(
        z_omega_normal_form(a - b, omega)
    ) == 0


# ---------------------------------------------------------------
# 1.  BWB concentration weight check
# ---------------------------------------------------------------
def check_bwb_concentration() -> None:
    """
    Bundle: Sym^2 Q on Gr(2,5).
        alpha = (0, 0)        S-side weight
        beta  = (2, 0, 0)     Q-side weight
    Weyman convention places the Q-weight first:
        mu = (beta | alpha) = (2, 0, 0, 0, 0)
        rho = (n-1, ..., 0)  = (4, 3, 2, 1, 0)
        mu + rho = (6, 3, 2, 1, 0)
    If strictly decreasing, cohomology is concentrated in degree 0
    and H^0 = Schur_{mu}(V) = Sym^2 V.
    """
    print("== Check 1: BWB concentration ==")
    alpha = (0, 0)
    beta = (2, 0, 0)
    mu = tuple(list(beta) + list(alpha))
    rho = (4, 3, 2, 1, 0)
    mu_plus_rho = tuple(a + b for a, b in zip(mu, rho))
    strictly_decreasing = all(
        mu_plus_rho[i] > mu_plus_rho[i + 1]
        for i in range(len(mu_plus_rho) - 1)
    )
    print(f"  mu          = {mu}")
    print(f"  rho         = {rho}")
    print(f"  mu + rho    = {mu_plus_rho}")
    print(f"  strictly decreasing? {strictly_decreasing}")
    assert mu_plus_rho == (6, 3, 2, 1, 0), "BWB weight mismatch"
    assert strictly_decreasing, (
        "BWB concentration fails: mu + rho is not strictly decreasing"
    )
    # Partition of H^0: mu (already non-decreasing fix), dim = multinomial
    # For Sym^2 of a 5-dim space, dim = binomial(5+1, 2) = 15
    dim_H0 = sp.binomial(5 + 1, 2)
    assert dim_H0 == 15, "dim Sym^2 V mismatch"
    print(f"  => H^q = 0 for q > 0; dim H^0 = {dim_H0}  (PASS)")


# ---------------------------------------------------------------
# 2.  Closed-form zeta^k-trace:
#         chi_k = 6 omega^{2k} + 6 (-1)^k omega^k + 3
#               = 6 omega^{2k} + 6 (-omega)^k + 3
# ---------------------------------------------------------------
def check_closed_form_traces(omega: sp.Symbol) -> List[sp.Expr]:
    """
    Verify the six zeta^k-traces by *two* independent routes:

        (A) The closed form
                chi_k = 6 omega^{2k} + 6 (-1)^k omega^k + 3
                      = 6 omega^{2k} + 6 (-omega)^k       + 3
            derived in Lemma (Exact zeta^k-traces) of Math49d-R4
            by the decomposition
                Sym^2 V = Sym^2 V_alpha  (+)  V_alpha (x) V_beta  (+)  Sym^2 V_beta
            with (dim, zeta-eigenvalue) = (6, omega^2), (6, -omega), (3, 1).

        (B) A direct explicit-matrix trace over Sym^2(C^5) with
            zeta = diag(omega, omega, omega, -1, -1), computed
            entirely in the polynomial ring Z[omega].
    """
    print("== Check 2: zeta^k-trace closed form ==")
    chis = []
    for k in range(6):
        # Middle block V_alpha (x) V_beta has zeta-eigenvalue -omega,
        # so zeta^k acts by (-omega)^k = (-1)^k * omega^k.
        raw = 6 * omega ** (2 * k) + 6 * ((-1) ** k) * omega ** k + 3
        chis.append(z_omega_normal_form(raw, omega))

    # Target table (eq. 5 of Math49d-R4)
    target = [
        sp.Integer(15),
        sp.Integer(-3) - 12 * omega,
        sp.Integer(-3),
        sp.Integer(3),
        sp.Integer(-3),
        sp.Integer(-3) - 12 * omega ** 2,
    ]
    target = [z_omega_normal_form(t, omega) for t in target]

    for k, (c, t) in enumerate(zip(chis, target)):
        ok = eq_z_omega(c, t, omega)
        print(f"  chi_{{zeta^{k}}} = {c}    target = {t}   {'OK' if ok else 'FAIL'}")
        assert ok, f"Closed-form trace mismatch at k={k}"

    print("  (A) closed form verified.")

    # -------- Independent route (B): direct matrix trace --------
    # Build zeta as a 5x5 diagonal, lift to Sym^2 (C^5) (dim 15),
    # and compute the trace symbolically in Z[omega].
    print("  (B) independent matrix trace cross-check:")
    eigvals = [omega, omega, omega, sp.Integer(-1), sp.Integer(-1)]
    # Sym^2-basis: e_i * e_j for i <= j; eigenvalue = eig_i * eig_j
    mat_traces = []
    for k in range(6):
        trace = sp.Integer(0)
        for i in range(5):
            for j in range(i, 5):  # i <= j for Sym^2 basis
                trace += (eigvals[i] ** k) * (eigvals[j] ** k)
        trace = z_omega_normal_form(trace, omega)
        mat_traces.append(trace)
        ok = eq_z_omega(trace, chis[k], omega)
        print(
            f"    k={k}: Sym^2 matrix trace = {trace}  "
            f"{'OK' if ok else 'FAIL'}"
        )
        assert ok, f"Direct trace mismatch at k={k}"
    print("  PASS")
    return chis


# ---------------------------------------------------------------
# 3.  Z_6 sum and quotient:  sum = 18, chi^{Z_6} = 3
# ---------------------------------------------------------------
def check_sum_and_quotient(
    omega: sp.Symbol, chis: List[sp.Expr]
) -> None:
    print("== Check 3: Z_6 sum and quotient ==")
    total = sum(chis)
    total_norm = z_omega_normal_form(total, omega)
    print(f"  sum_k chi_{{zeta^k}} = {total_norm}")
    assert eq_z_omega(total_norm, sp.Integer(18), omega), (
        f"Sum mismatch: expected 18, got {total_norm}"
    )
    # Quotient by |Z_6| = 6
    quotient = sp.Rational(1, 6) * total_norm
    quotient_norm = z_omega_normal_form(quotient, omega)
    print(f"  chi^{{Z_6}} = sum / 6 = {quotient_norm}")
    assert eq_z_omega(quotient_norm, sp.Integer(3), omega), (
        f"Quotient mismatch: expected 3, got {quotient_norm}"
    )
    # Integer-valuedness: no omega remaining
    assert quotient_norm == sp.Integer(3), (
        "chi^{Z_6} has residual omega dependence; failed to land in Z"
    )
    print("  PASS: chi^{Z_6} = 3 in Z (subset of Z[omega])")


# ---------------------------------------------------------------
# 4.  Invariant-subspace dimension via closed form (sanity)
# ---------------------------------------------------------------
def check_invariant_dim(omega: sp.Symbol) -> None:
    """
    chi^{Z_6} = dim (Sym^2 V)^{Z_6}, and by the decomposition used in
    Math49d-R4, the unique Z_6-invariant isotype is Sym^2 V_beta with
    dim 3.  Verify the arithmetic match explicitly.
    """
    print("== Check 4: invariant-subspace dimension ==")
    # Sym^2 V_beta has dim 3 (beta eigenvalue -1, so eigenvalue on Sym^2 V_beta is 1)
    dim_sym2_v_beta = sp.Integer(3)
    # Burnside average
    eigenvalues = [omega, omega, omega, sp.Integer(-1), sp.Integer(-1)]
    sym2_eigs = []
    for i in range(5):
        for j in range(i, 5):
            sym2_eigs.append(eigenvalues[i] * eigenvalues[j])
    # Count how many of sym2_eigs satisfy g = 1 after Burnside averaging,
    # using the identity dim (V)^G = (1/|G|) sum_{g in G} tr_V(g)
    invariant_count = sp.Integer(0)
    for k in range(6):
        tr_k = sum(z_omega_normal_form(e ** k, omega) for e in sym2_eigs)
        invariant_count += z_omega_normal_form(tr_k, omega)
    invariant_count = sp.Rational(1, 6) * invariant_count
    invariant_count = z_omega_normal_form(invariant_count, omega)
    print(f"  Burnside average dim = {invariant_count}")
    assert eq_z_omega(invariant_count, dim_sym2_v_beta, omega), (
        "Invariant-dim mismatch"
    )
    print("  PASS: dim (Sym^2 V)^{Z_6} = 3, matches chi^{Z_6}")


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
def main() -> int:
    print("=" * 66)
    print("Math49d-R4 exact arithmetic verification (PR-2 + PR-3)")
    print("=" * 66)
    omega = sp.Symbol("omega")
    try:
        check_bwb_concentration()
        print()
        chis = check_closed_form_traces(omega)
        print()
        check_sum_and_quotient(omega, chis)
        print()
        check_invariant_dim(omega)
    except AssertionError as err:
        print()
        print(f"[FAIL] {err}")
        return 1
    print()
    print("=" * 66)
    print("ALL CHECKS PASSED")
    print("  PR-2 (BWB concentration):   CLOSED")
    print("  PR-3 (exact Z[omega] sum):  CLOSED")
    print("  (Physical identification of Pillar 6 remains retracted;")
    print("   this script certifies the mathematical layer only.)")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    sys.exit(main())
