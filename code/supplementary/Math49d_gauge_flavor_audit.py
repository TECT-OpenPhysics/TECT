#!/usr/bin/env python3
"""
Math49d_gauge_flavor_audit.py

Purpose
-------
Independent audit of the peer-review critique (GPT, 2026-04-20) against
Math49d-R3-rigorous-v2: the claim is that identifying the three
generations with Sym^2 V_beta creates a gauge-flavor mixing catastrophe
because Sym^2 V_beta transforms as an SU(2)_W triplet (Sym^2 of a
doublet = triplet), which by the Standard Model assumption must commute
with flavor.

This script *does not* re-derive the Lefschetz count (that is in
Math49d_equivariant_bott.py).  It isolates the purely representation-
theoretic sub-problem:

    Given V_5 = V_alpha (+) V_beta with
       V_alpha = fundamental of SU(3)_c  (dim 3, Y = -1/3)
       V_beta  = fundamental of SU(2)_W  (dim 2, Y = +1/2)
    decompose Sym^2 V_5 under

       G_SM = SU(3)_c x SU(2)_W x U(1)_Y

    and report which irreducible piece equals Sym^2 V_beta, its
    transformation under SU(2)_W, and its hypercharge.

The critique is confirmed if the Z_6-invariant piece (= Sym^2 V_beta)
is shown to be an SU(2)_W triplet with a SINGLE hypercharge value.
That is inconsistent with "three chiral families" because families
must be SU(2)_W-singlets from the flavor viewpoint (each generation
independently supplies a complete (3,2)_{1/6} quark doublet etc.).

Dependencies:  numpy, sympy (both standard).  No lattice / PDE inputs.
Status:        DIAGNOSTIC, single-shot.  2026-04-20.
Policy:        Archived per UPDATE_POLICY §13 (all proof code must be
               committed).
"""

from __future__ import annotations

import sys
from fractions import Fraction

import numpy as np  # noqa: F401 (reserved for future Clebsch-Gordan work)
import sympy as sp


# ---------------------------------------------------------------------
# Hypercharge convention
# ---------------------------------------------------------------------
#   GUT embedding SU(5) ⊃ SU(3)_c x SU(2)_W x U(1)_Y
#   The fundamental 5 of SU(5) splits as
#       5  =  (3, 1)_{-1/3}  ⊕  (1, 2)_{+1/2}
#   so
#       V_alpha = (3, 1)_{-1/3}   (the anti-down quark triplet)
#       V_beta  = (1, 2)_{+1/2}   (the lepton doublet slot)
#
#   NB:  the signs follow the "5̄ down" convention of Georgi-Glashow.
#   Nothing downstream depends on the overall sign, only on the RATIO
#   of Y's; we keep it consistent with the 5 → (3,1)_{-1/3} + (1,2)_{+1/2}
#   convention used in the Math49d-R3 manuscript.
#
Y_ALPHA = Fraction(-1, 3)
Y_BETA  = Fraction(+1, 2)


# ---------------------------------------------------------------------
# Symmetric-square decomposition
# ---------------------------------------------------------------------
def decompose_sym2_5():
    """
    Return the list of irreducible pieces of Sym^2 V_5 under G_SM,
    each given as a dict:
        dim  : dimension (integer)
        SU3  : dimension of the SU(3)_c rep
        SU2  : dimension of the SU(2)_W rep
        Y    : hypercharge (Fraction)
        origin: which block of Sym^2 (V_alpha + V_beta) it comes from
        Z6_invariant: True iff the Z_6 character omega^{2·q_alpha + 0·q_beta}
                      with q_alpha=1 for V_alpha and q_beta=0 for V_beta
                      equals 1 under the canonical zeta = diag(ω,ω,ω,-1,-1).
    """
    pieces = []

    # --- Sym^2 V_alpha ---
    # Sym^2 of (3, 1)_{-1/3}  =  (6, 1)_{-2/3}
    pieces.append({
        "name"   : "Sym^2 V_alpha",
        "SU3"    : 6,
        "SU2"    : 1,
        "Y"      : 2 * Y_ALPHA,
        "dim"    : 6,
        "origin" : "VaVa",
    })

    # --- V_alpha (x) V_beta ---
    # (3, 1)_{-1/3} ⊗ (1, 2)_{+1/2} = (3, 2)_{-1/3 + 1/2} = (3, 2)_{+1/6}
    pieces.append({
        "name"   : "V_alpha ⊗ V_beta",
        "SU3"    : 3,
        "SU2"    : 2,
        "Y"      : Y_ALPHA + Y_BETA,
        "dim"    : 6,
        "origin" : "VaVb",
    })

    # --- Sym^2 V_beta ---
    # Sym^2 of (1, 2)_{+1/2} = (1, 3)_{+1}
    pieces.append({
        "name"   : "Sym^2 V_beta",
        "SU3"    : 1,
        "SU2"    : 3,
        "Y"      : 2 * Y_BETA,
        "dim"    : 3,
        "origin" : "VbVb",
    })

    return pieces


# ---------------------------------------------------------------------
# Z_6 invariance check
# ---------------------------------------------------------------------
def z6_character(origin: str) -> complex:
    """
    Under zeta = diag(ω, ω, ω, -1, -1) with ω = exp(2πi/3), ω^3 = 1,
    a bilinear block V_i ⊗ V_j gets character z_i · z_j where z_alpha = ω
    and z_beta = -1.  A symmetric piece inherits the same factor.
    """
    z_alpha = sp.exp(2 * sp.pi * sp.I / 3)
    z_beta  = sp.Integer(-1)
    table = {"VaVa": z_alpha**2, "VaVb": z_alpha * z_beta, "VbVb": z_beta**2}
    return sp.simplify(table[origin])


# ---------------------------------------------------------------------
# Main audit
# ---------------------------------------------------------------------
def main() -> int:
    print("============================================================")
    print("Math49d-R3 gauge–flavor audit (GPT peer-review check)")
    print("2026-04-20")
    print("============================================================\n")

    pieces = decompose_sym2_5()

    # Total dimension must equal dim Sym^2 C^5 = 15.
    total_dim = sum(p["dim"] for p in pieces)
    assert total_dim == 15, f"dim mismatch: {total_dim} != 15"

    print(f"{'piece':<22}{'SU(3)':>6}{'SU(2)':>7}{'Y':>8}"
          f"{'dim':>6}{'Z6 char':>14}{'Z6 invariant':>16}")
    print("-" * 80)

    for p in pieces:
        char = z6_character(p["origin"])
        invariant = (sp.simplify(char - 1) == 0)
        print(f"{p['name']:<22}"
              f"{p['SU3']:>6}"
              f"{p['SU2']:>7}"
              f"{str(p['Y']):>8}"
              f"{p['dim']:>6}"
              f"{str(char):>14}"
              f"{str(bool(invariant)):>16}")

    print()

    # --- Audit verdict ---
    print("VERDICT")
    print("-------")
    invariant_pieces = [
        p for p in pieces
        if sp.simplify(z6_character(p['origin']) - 1) == 0
    ]
    assert len(invariant_pieces) == 1
    inv = invariant_pieces[0]

    print(f"Unique Z_6-invariant isotype in Sym^2 V_5: {inv['name']}")
    print(f"  SU(3)_c : {inv['SU3']}  (color singlet: "
          f"{inv['SU3'] == 1})")
    print(f"  SU(2)_W : {inv['SU2']}  (weak triplet : "
          f"{inv['SU2'] == 3})")
    print(f"  U(1)_Y  : Y = {inv['Y']}")
    print(f"  dim     : {inv['dim']}")
    print()

    if inv['SU2'] == 3:
        print("CRITICAL — The Z_6-invariant piece is an SU(2)_W triplet.")
        print("If the three generations are identified with its three")
        print("basis vectors, they do not form an SU(2)_W-singlet family")
        print("index; equivalently, the flavor rotation U(3)_f does not")
        print("commute with SU(2)_W.  The GPT critique of Math49d-R3 is")
        print("CONFIRMED: the count '3' is the internal SU(2)_W-triplet")
        print("dimension of a single (1,3)_{+1} multiplet, not a family")
        print("count.  This is inconsistent with the Standard Model's")
        print("gauge/flavor commutation and falsifies the physical")
        print("identification in Math49d-R3-rigorous-v2.")
        print()
        print("Recognised SM content of (1,3)_{+1} with Y=+1: identical")
        print("quantum numbers to the Georgi-Machacek Higgs triplet")
        print("field, NOT to a family of chiral fermions.")
        return 0  # the audit itself ran correctly; the theory is falsified

    print("NOT CRITICAL — Z_6-invariant piece is an SU(2)_W singlet;")
    print("the gauge-flavor commutation is not immediately violated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
