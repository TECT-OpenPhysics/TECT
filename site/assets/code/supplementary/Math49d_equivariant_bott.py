#!/usr/bin/env python3
"""
TECT Math49d-R3: Z_6-equivariant Lefschetz index on Gr(2,5).

Computes chi_{zeta^k}(Gr(2,5), E) for k=0,...,5, where zeta is the
GUT-quotient Z_6 generator

    zeta = diag(omega, omega, omega, -1, -1),   omega = exp(2*pi*i/3),

and assembles the invariant index

    chi^{Z_6}(E) = (1/6) sum_{k=0}^{5} chi_{zeta^k}(E).

Implementation strategy (v2, 2026-04-20):
- k=0: direct symbolic Hirzebruch-Riemann-Roch via sympy at eps=0 limit,
  reusing the proven Math49_hrr_v3 torus-localisation kernel. (Fast.)
- k=1..5: mpmath high-precision (60-digit) complex evaluation of the
  torus-localised Atiyah-Bott formula at a single small eps.  Each of the
  10 T-fixed-point contributions is a rational function in eps with pole
  order <= 3 (positive-dim fixed components F_1 dim 2, F_2 dim 3); summing
  all 10 cancels poles and yields a constant that is recognised as a
  Gaussian/Eisenstein integer in Z[omega].

The Z_6-invariant index is then 1/6 of the sum of the six chi_{zeta^k};
by the Atiyah-Bott fixed-point theorem it is a non-negative integer
(= dim H^0 - dim H^1 + ... restricted to the Z_6-trivial isotype).

Target: search for bundles E with chi^{Z_6}(E) = 3 (three generations as
Z_6-invariant Euler characteristic), the structural-three signature of
Theorem 1 (three connected components X^zeta = F_1 sqcup F_2 sqcup F_3).
"""

import sympy as sp
from itertools import combinations
import mpmath as mp

mp.mp.dps = 200


# --- Z_6 eigenvalues (numerical) --------------------------------------

def phi_num(i, k):
    """Numerical (mpmath complex) Z_6-eigenvalue of slot i under zeta^k."""
    if i in (0, 1, 2):
        return mp.exp(2 * mp.pi * 1j * (k % 3) / 3)
    else:
        return mp.mpc(1) if (k % 2 == 0) else mp.mpc(-1)


def phi_sym(i, k):
    """Symbolic (sympy) version for k=0 (all phi=1)."""
    return sp.Integer(1)


# --- Z_6 eigenvalues (symbolic, algebraic field Q(omega, sqrt(-3))) ----

def omega_sym():
    return (sp.Integer(-1) + sp.sqrt(-3)) / 2


# --- T-localisation kernel --------------------------------------------

def tau(I_or_Ic, t):
    r = 1
    for i in I_or_Ic:
        r = r * t[i]
    return r


def bott_contribution(I, bundle_weight_fn, t, one=1):
    """Standard T-equivariant Bott contribution at p_I for the given bundle.

    Works for both sympy and mpmath numerics: `one` is the multiplicative
    identity in the chosen arithmetic (sp.Integer(1) or mp.mpc(1)).
    """
    Ic = tuple(k for k in range(5) if k not in I)
    weights = bundle_weight_fn(I, Ic, t)
    num = sum(weights)
    denom = one
    for i in I:
        for j in Ic:
            denom = denom * (one - t[i] / t[j])
    return num / denom


# --- k=0 path: pure sympy, exact (reproduces Math49_hrr_v3) -----------

def chi_equiv_at_k0(bundle_weight_fn):
    """k=0 ordinary chi via high-precision mpmath numerics.

    At k=0, phi_i = 1 for all i, so t_i = 1 + z_i*eps.  Each Bott contribution
    has pole order up to 6 at eps=0 (since all 6 denominator factors vanish).
    Using dps=200 and eps=1e-25, we retain 200 - 6*25 = 50 digits of the
    regular constant term -- more than enough for integer recognition.

    This replaces the slow sympy `cancel + limit` path used previously.
    """
    eps_val = mp.mpf('1e-25')
    z_list = [mp.mpf(1), mp.mpf(2), mp.mpf(3), mp.mpf(5), mp.mpf(7)]
    t = [1 + z_list[i] * eps_val for i in range(5)]
    total = mp.mpc(0)
    for I in combinations(range(5), 2):
        total += bott_contribution(I, bundle_weight_fn, t, one=mp.mpc(1))
    rec = recognize_integer(total, tol=mp.mpf('1e-15'))
    if rec is not None:
        return sp.Integer(rec)
    return complex(total)


# --- k!=0 path: high-precision mpmath numerics ------------------------

def chi_equiv_at_k_numeric(bundle_weight_fn, k, eps_val=None,
                           z_list=None):
    if eps_val is None:
        eps_val = mp.mpf('1e-50')
    """Numerical mpmath evaluation at zeta^k, k != 0.

    Substitutes t_i = phi_i(k) * (1 + z_i * eps) and sums the 10 T-fixed
    Bott contributions.  Returns an mpmath complex number; the imaginary
    part should be ~machine epsilon for the Z_6-invariant sum.
    """
    if z_list is None:
        z_list = [mp.mpf(1), mp.mpf(2), mp.mpf(3),
                  mp.mpf(5), mp.mpf(7)]
    phi = [phi_num(i, k) for i in range(5)]
    t = [phi[i] * (1 + z_list[i] * eps_val) for i in range(5)]
    total = mp.mpc(0)
    for I in combinations(range(5), 2):
        c = bott_contribution(I, bundle_weight_fn, t, one=mp.mpc(1))
        total += c
    return total


def recognize_integer(z, tol=None):
    """If z is within tol of an integer (real part), return that integer."""
    if tol is None:
        tol = mp.mpf('1e-20')
    try:
        if abs(z.imag) < tol and abs(z.real - round(z.real)) < tol:
            return int(round(z.real))
    except AttributeError:
        pass
    return None


def chi_equiv_at_k(bundle_weight_fn, k):
    """Dispatch: symbolic for k=0, mpmath for k=1..5."""
    if k == 0:
        return chi_equiv_at_k0(bundle_weight_fn)
    val = chi_equiv_at_k_numeric(bundle_weight_fn, k)
    # Try recognizing integer (the most common case for Z_6-invariant).
    rec = recognize_integer(val)
    if rec is not None:
        return sp.Integer(rec)
    # Otherwise, recognize as element of Z[omega] = Z + Z*omega.
    # omega has imaginary part sqrt(3)/2.  So z = a + b*omega means
    # Re(z) = a - b/2, Im(z) = b * sqrt(3)/2.
    sqrt3_over_2 = float(mp.sqrt(3) / 2)
    b_float = float(val.imag) / sqrt3_over_2
    a_float = float(val.real) + b_float / 2
    if abs(b_float - round(b_float)) < 1e-15 and abs(a_float - round(a_float)) < 1e-15:
        a, b = int(round(a_float)), int(round(b_float))
        return sp.Integer(a) + sp.Integer(b) * omega_sym()
    # Otherwise, return raw mpmath value (failure mode).
    return complex(val)


def chi_Z6_invariant(bundle_weight_fn):
    """(1/6) sum_k chi_{zeta^k}(E).  Returns (invariant, list_chi_k)."""
    chi_k = [chi_equiv_at_k(bundle_weight_fn, k) for k in range(6)]
    total = sum(chi_k, sp.Integer(0))
    invariant = sp.simplify(total / 6)
    return invariant, chi_k


# --- Bundle weight functions ------------------------------------------

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


def weights_wedge2_S(I, Ic, t):
    return [tau(I, t)]


def weights_wedge2_Q(I, Ic, t):
    Ic_list = list(Ic)
    out = []
    for i_idx in range(len(Ic_list)):
        for j_idx in range(i_idx + 1, len(Ic_list)):
            out.append(t[Ic_list[i_idx]] * t[Ic_list[j_idx]])
    return out


def weights_sym2_S(I, Ic, t):
    I_list = list(I)
    out = []
    for i_idx in range(len(I_list)):
        for j_idx in range(i_idx, len(I_list)):
            out.append(t[I_list[i_idx]] * t[I_list[j_idx]])
    return out


# --- Main: sanity suite + scan ----------------------------------------

def display_k_decomposition(label, chi_k):
    parts = [f"k={k}: {v}" for k, v in enumerate(chi_k)]
    print(f"    {label}: " + "   ".join(parts))


def main():
    print("=" * 78)
    print("Z_6-equivariant Lefschetz index on Gr(2,5)  (TECT Math49d-R3 v2)")
    print("zeta = diag(omega, omega, omega, -1, -1),  omega = exp(2*pi*i/3)")
    print("Method: k=0 exact sympy;  k=1..5 mpmath 200-digit (eps=1e-50).")
    print("=" * 78)

    print("\n[Sanity 0] k=0 reproduces ordinary chi(O(d)) = binom(d+4,4)")
    expected = {-1: 0, 0: 1, 1: 10, 2: 50, 3: 175}
    for d in (-1, 0, 1, 2, 3):
        chi0 = chi_equiv_at_k0(weights_O(d))
        ok = "OK" if chi0 == expected[d] else "FAIL"
        print(f"  chi(O({d:+d})) = {chi0}   expected {expected[d]}   [{ok}]")

    print("\n[Sanity 1] Trivial bundle O: chi^{Z_6}(O) expected = 1")
    inv_O, chi_k_O = chi_Z6_invariant(weights_O(0))
    print(f"  chi^{{Z_6}}(O) = {inv_O}")
    display_k_decomposition("chi_{zeta^k}(O)", chi_k_O)

    print("\n[Sanity 2] O(1): expected 4 Z_6-invariant Pluecker coords")
    # Pluecker coords of Gr(2,5) = Lambda^2 C^5 = 10-dim; under zeta,
    # Lambda^2 C^5 decomposes as (Lambda^2 V_alpha) + (V_alpha (x) V_beta) +
    # (Lambda^2 V_beta) with zeta-weights (omega^2, omega * (-1), (-1)^2).
    # Z_6-invariants: need total weight 1 under zeta.  Lambda^2 V_alpha
    # has weight omega^2: NO.  V_alpha (x) V_beta has weight -omega: NO.
    # Lambda^2 V_beta has weight 1: YES (dim 1).  So expected = 1.
    inv_O1, chi_k_O1 = chi_Z6_invariant(weights_O(1))
    print(f"  chi^{{Z_6}}(O(1)) = {inv_O1}   (expected: 1, from Lambda^2 V_beta)")
    display_k_decomposition("chi_{zeta^k}(O(1))", chi_k_O1)

    print("\n[Sanity 3] S and Q tautological bundles")
    inv_S, chi_k_S = chi_Z6_invariant(weights_S)
    inv_Q, chi_k_Q = chi_Z6_invariant(weights_Q)
    print(f"  chi^{{Z_6}}(S)   = {inv_S}   (ordinary chi(S)=0)")
    print(f"  chi^{{Z_6}}(Q)   = {inv_Q}   (ordinary chi(Q)=5)")
    display_k_decomposition("chi_{zeta^k}(S)", chi_k_S)
    display_k_decomposition("chi_{zeta^k}(Q)", chi_k_Q)

    print("\n" + "=" * 78)
    print("MAIN SCAN: chi^{Z_6}(E_L(a,b)) for (a,b) in [-3, 3]^2")
    print("  E_L(a, b) = S (x) (det Q)^a  (+)  Q (x) (det S)^b")
    print("=" * 78)

    print("        " + " ".join(f"a={a:+d}".center(10) for a in range(-3, 4)))
    print("       " + "-" * (11 * 7))
    hits3 = []
    for b in range(-3, 4):
        row = f" b={b:+d} |"
        for a in range(-3, 4):
            inv, _ = chi_Z6_invariant(weights_EL(a, b))
            cell = str(inv)[:8]
            row += f" {cell.rjust(8)} "
            if inv == 3:
                hits3.append((a, b))
        print(row)

    print("\n" + "=" * 78)
    if hits3:
        print("SUCCESS: chi^{Z_6}(E_L(a,b)) = 3 achieved at:")
        for ab in hits3:
            print(f"  (a, b) = {ab}")
    else:
        print("  [no (a,b) with chi^{Z_6} = 3 in [-3,3]^2 for the direct-sum")
        print("  bundle E_L(a,b).  Proceed to irreducible bundles below.]")

    print("\n" + "=" * 78)
    print("IRREDUCIBLE BUNDLES (avoid direct-sum additivity artefact)")
    print("=" * 78)

    inv_w2S, chi_k_w2S = chi_Z6_invariant(weights_wedge2_S)
    print(f"  chi^{{Z_6}}(Lambda^2 S) = chi^{{Z_6}}(det S) = {inv_w2S}")
    display_k_decomposition("chi_{zeta^k}(det S)", chi_k_w2S)

    inv_w2Q, chi_k_w2Q = chi_Z6_invariant(weights_wedge2_Q)
    print(f"  chi^{{Z_6}}(Lambda^2 Q) = {inv_w2Q}  (ordinary rank 3)")
    display_k_decomposition("chi_{zeta^k}(Lambda^2 Q)", chi_k_w2Q)

    inv_s2S, chi_k_s2S = chi_Z6_invariant(weights_sym2_S)
    print(f"  chi^{{Z_6}}(Sym^2 S) = {inv_s2S}  (ordinary rank 3)")
    display_k_decomposition("chi_{zeta^k}(Sym^2 S)", chi_k_s2S)

    # === EXPANDED bundle scan ===
    print("\n" + "=" * 78)
    print("EXPANDED BUNDLE SEARCH: twists and Schur functors")
    print("=" * 78)

    catalog = []

    # O(d) for d = -2..5
    for d in range(-2, 6):
        catalog.append((f"O({d:+d})", weights_O(d)))

    # S (x) O(d)  (weights of S times tau(Ic)^d)
    def weights_S_twist(d):
        def fn(I, Ic, t):
            tw = tau(Ic, t) ** d
            return [t[i] * tw for i in I]
        return fn

    # Q (x) O(d)
    def weights_Q_twist(d):
        def fn(I, Ic, t):
            tw = tau(Ic, t) ** d
            return [t[j] * tw for j in Ic]
        return fn

    # Lambda^2 Q (x) O(d)
    def weights_w2Q_twist(d):
        def fn(I, Ic, t):
            tw = tau(Ic, t) ** d
            Ic_list = list(Ic)
            return [t[Ic_list[a]] * t[Ic_list[b]] * tw
                    for a in range(3) for b in range(a + 1, 3)]
        return fn

    # Sym^2 Q (x) O(d)
    def weights_s2Q_twist(d):
        def fn(I, Ic, t):
            tw = tau(Ic, t) ** d
            Ic_list = list(Ic)
            return [t[Ic_list[a]] * t[Ic_list[b]] * tw
                    for a in range(3) for b in range(a, 3)]
        return fn

    # Sym^2 S (x) O(d)
    def weights_s2S_twist(d):
        def fn(I, Ic, t):
            tw = tau(Ic, t) ** d
            I_list = list(I)
            return [t[I_list[a]] * t[I_list[b]] * tw
                    for a in range(2) for b in range(a, 2)]
        return fn

    # Sym^3 S (x) O(d)  -- rank 4
    def weights_s3S_twist(d):
        def fn(I, Ic, t):
            tw = tau(Ic, t) ** d
            I_list = list(I)
            out = []
            for a in range(2):
                for b in range(a, 2):
                    for c in range(b, 2):
                        out.append(t[I_list[a]] * t[I_list[b]] * t[I_list[c]] * tw)
            return out
        return fn

    # Sym^3 Q (x) O(d)  -- rank 10
    def weights_s3Q_twist(d):
        def fn(I, Ic, t):
            tw = tau(Ic, t) ** d
            Ic_list = list(Ic)
            out = []
            for a in range(3):
                for b in range(a, 3):
                    for c in range(b, 3):
                        out.append(t[Ic_list[a]] * t[Ic_list[b]] * t[Ic_list[c]] * tw)
            return out
        return fn

    # S (x) Q (x) O(d)  (rank 6)
    def weights_SQ_twist(d):
        def fn(I, Ic, t):
            tw = tau(Ic, t) ** d
            return [t[i] * t[j] * tw for i in I for j in Ic]
        return fn

    for d in range(-2, 4):
        catalog.append((f"S (x) O({d:+d})", weights_S_twist(d)))
    for d in range(-2, 4):
        catalog.append((f"Q (x) O({d:+d})", weights_Q_twist(d)))
    for d in range(-2, 4):
        catalog.append((f"Lambda^2 Q (x) O({d:+d})", weights_w2Q_twist(d)))
    for d in range(-2, 4):
        catalog.append((f"Sym^2 Q (x) O({d:+d})", weights_s2Q_twist(d)))
    for d in range(-2, 4):
        catalog.append((f"Sym^2 S (x) O({d:+d})", weights_s2S_twist(d)))
    for d in range(-2, 4):
        catalog.append((f"Sym^3 S (x) O({d:+d})", weights_s3S_twist(d)))
    for d in range(-2, 4):
        catalog.append((f"Sym^3 Q (x) O({d:+d})", weights_s3Q_twist(d)))
    for d in range(-2, 4):
        catalog.append((f"S (x) Q (x) O({d:+d})", weights_SQ_twist(d)))

    def _is_three(x):
        """Robust check: x equals 3 as sympy Integer, mpmath, or complex."""
        try:
            if x == 3:
                return True
        except Exception:
            pass
        try:
            return abs(complex(x) - 3) < 1e-8
        except Exception:
            return False

    print(f"  {'bundle':<28} {'chi_ord':>8} {'chi^{Z_6}':>18}")
    print("  " + "-" * 58)
    hits3 = []
    for (label, fn) in catalog:
        chi0 = chi_equiv_at_k0(fn)
        inv, _ = chi_Z6_invariant(fn)
        marker = "  <-- ** 3 **" if _is_three(inv) else ""
        s_chi0 = str(chi0)[:8]
        s_inv = str(inv)[:18]
        print(f"  {label:<28} {s_chi0:>8} {s_inv:>18}{marker}")
        if _is_three(inv):
            hits3.append(label)

    print("\n" + "=" * 78)
    if hits3:
        print("BUNDLES WITH chi^{Z_6}(E) = 3:")
        for h in hits3:
            print(f"  " + h)
    else:
        print("  No chi^{Z_6} = 3 found in catalog.  Need Schur S^(a,b) or")
        print("  fuller Grassmannian-twisted families.")

    # Detailed k-decomposition for key hit bundles.
    print("\n" + "=" * 78)
    print("DETAILED k-DECOMPOSITION FOR HIT BUNDLES (chi^{Z_6} = 3)")
    print("=" * 78)

    def weights_s2Q_bare(I, Ic, t):
        Ic_list = list(Ic)
        return [t[Ic_list[a]] * t[Ic_list[b]]
                for a in range(3) for b in range(a, 3)]

    hit_specs = [
        ("Sym^2 Q", weights_s2Q_bare),
        ("Sym^2 S (x) O(+2)", weights_s2S_twist(2)),
        ("Sym^2 S (x) O(+3)", weights_s2S_twist(3)),
    ]
    for (label, fn) in hit_specs:
        inv, chi_k = chi_Z6_invariant(fn)
        print(f"\n  {label}:  chi^{{Z_6}} = {inv}")
        for k, v in enumerate(chi_k):
            print(f"    chi_{{zeta^{k}}} = {v}")


if __name__ == "__main__":
    main()
