#!/usr/bin/env python3
"""
HRR chi(Gr(2,5), E_L(a,b)) via Bott equivariant localisation —
EXACT sympy Laurent-series expansion around t=1 (t_i = 1 + z_i*eps).

Rationale for previous failures:
--------------------------------
(i) A subagent's Schubert-basis script returned chi(a,b) = 0 for all (a,b)
    on the false grounds that "sigma_3^2 does not appear in Chern-class
    monomials of codim 6". This is wrong: Pieri gives sigma_3 * sigma_3 =
    sigma_{(3,3)}, and int(sigma_{(3,3)}) = 1.
(ii) A direct floating-point Bott evaluation at t = exp(eps*z) failed
    because each summand has a pole of order 6 at eps=0; the cancellations
    among 10 fixed points are exact in symbolic arithmetic but lose all
    precision in float arithmetic (spurious 1e24-scale values).

Current strategy:
-----------------
Use t_i = 1 + z_i*eps with z = (1, 2, 3, 5, 7) (distinct rationals),
expand each Bott contribution in sympy exact arithmetic as a Laurent
series in eps to order eps^0, sum the 10 contributions (the negative
powers of eps cancel), and read off the eps^0 coefficient. This
coefficient is chi (independent of the choice of z after cancellation,
a built-in consistency check of the method).

Bundle under test:
  E_L(a, b) = S ⊗ (det Q)^a  ⊕  Q ⊗ (det S)^b
  with E_L|p_I = sum_{i in I} t_i * tau_{I^c}^a
              + sum_{j in I^c} t_j * tau_I^b
"""

import sympy as sp
from itertools import combinations


def tau(I, t):
    r = sp.Integer(1)
    for i in I:
        r *= t[i]
    return r


def bott_contribution(I, bundle_weight_fn, t):
    Ic = tuple(k for k in range(5) if k not in I)
    weights = bundle_weight_fn(I, Ic, t)
    num = sum(weights)
    denom = sp.Integer(1)
    for i in I:
        for j in Ic:
            denom *= (sp.Integer(1) - t[i] / t[j])
    return num / denom


def chi_via_bott(bundle_weight_fn):
    """Compute chi by symbolic Laurent expansion in eps."""
    eps = sp.Symbol('eps')
    # Distinct small positive rationals (rationally independent for our
    # polynomial purposes: z_i - z_j != 0 for i != j).
    z = [sp.Rational(1), sp.Rational(2), sp.Rational(3),
         sp.Rational(5), sp.Rational(7)]
    t = [1 + z[i] * eps for i in range(5)]

    total = sp.Integer(0)
    for I in combinations(range(5), 2):
        total += bott_contribution(I, bundle_weight_fn, t)

    # Combine into single rational function over eps, then simplify.
    combined = sp.together(total)
    # cancel common factors; chi(a,b) is a polynomial in eps (indeed
    # a constant, independent of z) after all fixed-point poles cancel.
    simplified = sp.cancel(combined)
    # Substitute eps -> 0 to extract the constant term.
    return sp.simplify(simplified.subs(eps, 0))


def weights_O(d):
    def fn(I, Ic, t):
        return [tau(Ic, t) ** d]
    return fn


def weights_S(I, Ic, t):
    return [t[i] for i in I]


def weights_Q(I, Ic, t):
    return [t[j] for j in Ic]


def weights_EL(a, b):
    def fn(I, Ic, t):
        tauI = tau(I, t)
        tauIc = tau(Ic, t)
        out = []
        for i in I:
            out.append(t[i] * tauIc ** a)
        for j in Ic:
            out.append(t[j] * tauI ** b)
        return out
    return fn


def main():
    print("=" * 72)
    print("HRR chi(Gr(2,5), .) via Bott equivariant localisation (sympy exact)")
    print("=" * 72)

    print("\n[Sanity checks]")
    # chi(O(d)) on Gr(2,5) = dim H^0(O(d)) = s_{d,d}(1^5) = dim SL(5) rep
    #   with Young diagram (d,d) = (d+1)(d+2)^2(d+3)^2(d+4)/12
    # (Weyl dim formula for SL_n and the Schur functor s_{d^k}(1^n).)
    # Quick hand values:
    #   d = 0: 1
    #   d = 1: 10  (C(5,2), Pluecker dim)
    #   d = 2: 1*3*4^2*5^2*6/(1*2*3*4*4*5) =
    #          formula dim = prod_{1<=i<j<=5}(lambda_i - lambda_j + j - i)/(j-i)
    # Let me just compute and compare.
    for d in range(-1, 4):
        val = chi_via_bott(weights_O(d))
        print(f"  chi(O({d:+d}))  =  {val}")

    val_S = chi_via_bott(weights_S)
    val_Q = chi_via_bott(weights_Q)
    print(f"  chi(S)      =  {val_S}")
    print(f"  chi(Q)      =  {val_Q}")
    print(f"  chi(S) + chi(Q) = {val_S + val_Q}   [expected 5 = chi(O^5)]")

    print("\n" + "=" * 72)
    print("MAIN TABLE:  chi(E_L(a,b)) = chi(S ⊗ L^a ⊕ Q ⊗ M^b)")
    print("  L = det Q,  M = det S;   a, b in [-3, +3]")
    print("=" * 72)

    hdr = "       " + " ".join(f"a={a:+d}".rjust(7) for a in range(-3, 4))
    print(hdr)
    print("      " + "-" * (8 * 7))
    chi_table = {}
    for b in range(-3, 4):
        row = f" b={b:+d} |"
        for a in range(-3, 4):
            val = chi_via_bott(weights_EL(a, b))
            chi_table[(a, b)] = val
            row += f" {str(val).rjust(6)} "
        print(row)

    print("\n" + "=" * 72)
    print("All (a, b) yielding chi = 3:")
    print("=" * 72)
    hits3 = [(a, b) for (a, b), v in chi_table.items() if v == 3]
    if hits3:
        for ab in hits3:
            print(f"  (a, b) = {ab}")
    else:
        print("  [none in the scanned range]")

    print("\nAll chi values that occur:")
    vals = sorted(set(chi_table.values()), key=lambda x: (abs(sp.Integer(x) if sp.simplify(x).is_integer else 0), x))
    for v in sorted(set(chi_table.values()), key=lambda x: int(x) if x.is_integer else 0):
        pairs = [(a, b) for (a, b), c in chi_table.items() if c == v]
        print(f"  chi = {v}:  {pairs}")


if __name__ == "__main__":
    main()
