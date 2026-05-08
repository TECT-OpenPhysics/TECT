#!/usr/bin/env python3
"""
Math174_c2_via_slansky.py
Explicit computation of the second Chern number c_2(E) for the SO(10) spinor
matter bundle on CP^2 via weight enumeration and the splitting principle.

Theory: TECT-Math174
Date: 2026-04-27
Status: SUPPLEMENTARY CODE FOR RIGOROUS COMPUTATION

Computation logic:
1. Enumerate all 16 weights of the SO(10) spinor representation.
2. Classify them by SU(5) representation (10, 5̄, 1) and U(1)_χ charge.
3. Apply the splitting principle: c_2(E) = ∑_{i<j} x_i x_j where x_i are Chern roots.
4. For a direct sum E = E_10 ⊕ E_5̄ ⊕ E_1, use c_2(E) = c_2(E_10) + c_2(E_5̄) +
   c_2(E_1) + c_1(E_10)·c_1(E_5̄) + c_1(E_10)·c_1(E_1) + c_1(E_5̄)·c_1(E_1).
5. Express in terms of the U(1)_χ degree b ∈ H^2(CP^2).
6. Integrate over CP^2 with ∫ b^2 = 1 (hyperplane class normalisation).
"""

import itertools
import numpy as np
from fractions import Fraction
from typing import List, Tuple, Dict, Set

# ============================================================================
# PART 1: SO(10) SPINOR REPRESENTATION AND WEIGHT ENUMERATION
# ============================================================================

def enumerate_so10_spinor_weights() -> List[Tuple[int, int, int, int, int]]:
    """
    Enumerate all 16 weights of the SO(10) positive-chirality spinor (𝟏𝟔).

    In the standard basis where SO(10) Cartan generators are diagonal with
    eigenvalues (e_1, e_2, e_3, e_4, e_5), the 16 weights are:
        (ε_1/2, ε_2/2, ε_3/2, ε_4/2, ε_5/2)
    where ε_i ∈ {+1, -1} and ∏ε_i = +1 (even number of minus signs).

    Returns:
        List of 16 weight tuples, each (ε_1, ε_2, ε_3, ε_4, ε_5).
    """
    weights = []
    for signs in itertools.product([1, -1], repeat=5):
        # Check if the product is +1 (even parity)
        if np.prod(signs) == 1:
            weights.append(signs)

    assert len(weights) == 16, f"Expected 16 weights, got {len(weights)}"
    return weights


def classify_weights_by_u1_charge(weights: List[Tuple[int, ...]]) -> Dict[int, List[Tuple[int, ...]]]:
    """
    Classify SO(10) spinor weights by U(1)_χ charge under SO(10)→SU(5)×U(1)_χ.

    Standard convention (Georgi-Glashow):
    - Weights with (ε_1, ε_2, ε_3, ε_4, ε_5) map to (ε_1, ε_2, ε_3, ε_4) under
      the maximal embedding SU(5) ⊂ SO(10).
    - The U(1)_χ charge is determined by the ε_5 and the parity of earlier signs.

    For the standard branching 𝟏𝟔 → 𝟏𝟎(q=+1) ⊕ 𝟓̄(q=-3) ⊕ 𝟏(q=+5):
      - 10 weights with q=+1 (antisymmetric rank-2 tensors of SU(5))
      - 5 weights with q=-3 (antifundamental of SU(5))
      - 1 weight with q=+5 (singlet)

    Returns:
        Dictionary {charge: [weights with that charge]}.
    """
    # Standard Slansky table charge assignment for SO(10) → SU(5) × U(1)_χ
    # The spinor 𝟏𝟔 branches as:
    #   𝟏𝟔 → 𝟏𝟎(+1) ⊕ 𝟓̄(-3) ⊕ 𝟏(+5)

    charged_weights = {}

    for weight in weights:
        # Determine charge from the weight pattern.
        # For the standard branching, weights are classified as:
        # - All five ε_i = +1: singlet with q=+5
        # - All five ε_i = -1: impossible (product = -1)
        # - Four ε_i = +1, one = -1: one of the 5 antifundamental states, q=-3
        # - Two ε_i = +1, two = -1 (and one more): the 10 antisymmetric tensors, q=+1

        num_plus = sum(1 for e in weight if e == 1)
        num_minus = 5 - num_plus

        # Charge assignment (from Slansky table or standard GUT convention):
        if num_plus == 5:  # All +1
            charge = 5
        elif num_plus == 3:  # Three +1, two -1 (equivalently, two -1)
            charge = -3
        elif num_plus == 1:  # One +1, four -1 (equivalently, four -1)
            # Actually, let me reconsider: num_plus = 1 means one +1 and four -1,
            # which has product -1 (odd parity), so this should not appear.
            # Let me recount...
            raise ValueError(f"Weight {weight} has odd parity, should not appear in spinor!")
        else:  # num_plus == 2 (two +1, three -1) — product = -1, invalid
            # OR num_plus == 4 (four +1, one -1) — product = -1, invalid
            # OR num_plus == 0 (zero +1, five -1) — product = -1, invalid
            # OR num_plus == 3 (three +1, two -1) — product = +1, valid ✓
            # OR num_plus == 1 (one +1, four -1) — product = -1, invalid
            raise ValueError(f"Weight {weight} has odd parity (num_plus={num_plus}), invalid!")

        # Correct logic: we have (num_plus = k, num_minus = 5-k) with product = (-1)^(5-k).
        # For product = +1, we need 5-k to be even, i.e., k ∈ {1, 3, 5}.

        # Standard charge assignment:
        if num_plus == 5:
            charge = 5  # 𝟏 singlet
        elif num_plus == 3:
            charge = -3  # 𝟓̄ antifundamental (5 such weights)
        elif num_plus == 1:
            charge = 1  # 𝟏𝟎 antisymmetric tensor (10 such weights)
        else:
            raise ValueError(f"Unexpected parity: num_plus={num_plus}")

        if charge not in charged_weights:
            charged_weights[charge] = []
        charged_weights[charge].append(weight)

    return charged_weights


# ============================================================================
# PART 2: CHERN CLASS COMPUTATION VIA SPLITTING PRINCIPLE
# ============================================================================

def compute_c2_via_charges(charged_weights: Dict[int, List]) -> Tuple[float, Dict[str, float]]:
    """
    Compute c_2(E) = ∫ c_2(E) using the splitting principle.

    For E = E_10 ⊕ E_5̄ ⊕ E_1 where all roots within each subbundle have the
    same U(1)_χ charge q:
      - c_1(E_k) = n_k · q_k · b  (where n_k is the rank and q_k is the common charge)
      - c_2(E_k) = C(n_k, 2) · q_k^2 · b^2  (binomial coefficient)

    Cross terms:
      c_1(E_i) · c_1(E_j) = n_i · q_i · n_j · q_j · b^2

    Total:
      c_2(E) = [∑_k C(n_k, 2) · q_k^2 + ∑_{i<j} n_i · q_i · n_j · q_j] · b^2

    With ∫_{CP^2} b^2 = 1 (hyperplane class), we get μ = ∫ c_2(E).

    Returns:
        (μ, details_dict) where μ is the integral and details_dict contains
        intermediate calculations.
    """

    # Unpack charges and counts
    charges_counts = {q: len(weights) for q, weights in charged_weights.items()}

    print("=" * 70)
    print("CHARGE CLASSIFICATION")
    print("=" * 70)
    for charge, count in sorted(charges_counts.items(), reverse=True):
        print(f"  q = {charge:+2d}: {count:2d} weights")

    # Assign representation labels for clarity
    rep_names = {1: "𝟏𝟎 (rank 10)", -3: "𝟓̄ (rank 5)", 5: "𝟏 (rank 1)"}

    # Validate counts
    expected_counts = {1: 10, -3: 5, 5: 1}
    for charge, expected_count in expected_counts.items():
        actual_count = charges_counts.get(charge, 0)
        if actual_count != expected_count:
            raise ValueError(
                f"Charge q={charge}: expected {expected_count} weights, got {actual_count}"
            )

    details = {}

    # ---- Part A: Diagonal terms c_2(E_k) = C(rank, 2) · q_k^2 · b^2 ----

    print("\n" + "=" * 70)
    print("PART A: DIAGONAL CHERN CLASS TERMS")
    print("=" * 70)

    diagonal_sum = 0
    for charge in [1, -3, 5]:
        rank = charges_counts[charge]
        c2_coeff = (rank * (rank - 1)) // 2 * (charge ** 2)
        diagonal_sum += c2_coeff
        print(
            f"  {rep_names[charge]:16s}: "
            f"C({rank}, 2) × ({charge:+2d})^2 = {rank*(rank-1)//2:2d} × {charge**2:3d} = {c2_coeff:+5d}"
        )

    details["diagonal_sum"] = diagonal_sum
    print(f"\n  Sum of diagonal terms: {diagonal_sum}")

    # ---- Part B: Cross terms c_1(E_i) · c_1(E_j) = n_i·q_i · n_j·q_j · b^2 ----

    print("\n" + "=" * 70)
    print("PART B: CROSS TERMS (FIRST CHERN PRODUCTS)")
    print("=" * 70)

    charges_list = sorted(charges_counts.keys(), reverse=True)
    cross_sum = 0

    for i, charge_i in enumerate(charges_list):
        for charge_j in charges_list[i + 1:]:
            rank_i = charges_counts[charge_i]
            rank_j = charges_counts[charge_j]
            cross_coeff = rank_i * charge_i * rank_j * charge_j
            cross_sum += cross_coeff
            print(
                f"  {rep_names[charge_i]} × {rep_names[charge_j]}: "
                f"{rank_i} × ({charge_i:+2d}) × {rank_j} × ({charge_j:+2d}) = {cross_coeff:+6d}"
            )

    details["cross_sum"] = cross_sum
    print(f"\n  Sum of cross terms: {cross_sum}")

    # ---- Total ----

    print("\n" + "=" * 70)
    print("TOTAL c_2(E)")
    print("=" * 70)

    total_coeff = diagonal_sum + cross_sum
    print(f"\n  c_2(E) = ({diagonal_sum:+6d} + {cross_sum:+6d}) × b^2")
    print(f"         = {total_coeff:+6d} × b^2")

    # With ∫ b^2 = 1 on CP^2:
    mu = float(total_coeff)

    print(f"\n  ∫_{{CP^2}} c_2(E) = {total_coeff:+6d} × ∫_{{CP^2}} b^2")
    print(f"                   = {total_coeff:+6d} × 1")
    print(f"                   = {mu:+6.1f}")

    details["total_coeff"] = total_coeff
    details["mu"] = mu

    return mu, details


# ============================================================================
# PART 3: ATIYAH-SINGER INDEX
# ============================================================================

def compute_index(mu: float) -> Tuple[float, bool]:
    """
    Compute the Atiyah-Singer index from the corrected formula (Math171-AddA):
        ind(D_E^c) = 16 - μ

    where μ = ∫ c_2(E) is the second Chern number.

    Returns:
        (index, is_correct) where is_correct is True iff index == 16.
    """
    index = 16 - mu
    is_correct = (index == 16)

    print("\n" + "=" * 70)
    print("ATIYAH-SINGER INDEX (Math171-AddA FORMULA)")
    print("=" * 70)
    print(f"\n  Formula: ind(D_E^c) = 16 - μ")
    print(f"  μ = {mu:+6.1f}")
    print(f"  ind(D_E^c) = 16 - ({mu:+6.1f}) = {index:+6.1f}")
    print(f"\n  Target: ind = 16 (SO(10) spinor dimension)")
    print(f"  Status: {'✓ PASS' if is_correct else '✗ FAIL'}")

    if not is_correct:
        print(f"\n  ** FALSIFICATION **")
        print(f"  The Math162 bundle does NOT produce 16 chiral zero modes.")
        print(f"  Actual index: {index:+6.1f} ≠ 16")

    return index, is_correct


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Full computation pipeline:
    1. Enumerate SO(10) spinor weights.
    2. Classify by U(1)_χ charge.
    3. Compute c_2(E) via splitting principle.
    4. Compute Atiyah-Singer index.
    5. Compare with target (16).
    """

    print("\n" + "=" * 70)
    print("TECT-Math174: Explicit Second Chern Number Computation")
    print("=" * 70)
    print("\nTask: Compute μ = ∫_{CP^2} c_2(E) for the SO(10) spinor matter bundle")
    print("      and verify whether μ = 0 (required for 16 chiral zero modes).")

    # Step 1: Enumerate weights
    print("\n" + "=" * 70)
    print("STEP 1: SO(10) SPINOR WEIGHT ENUMERATION")
    print("=" * 70)
    weights = enumerate_so10_spinor_weights()
    print(f"\nEnumerated {len(weights)} weights of SO(10) 𝟏𝟔:")
    for i, w in enumerate(weights, 1):
        print(f"  {i:2d}. {w}")

    # Step 2: Classify by charge
    print("\n" + "=" * 70)
    print("STEP 2: CLASSIFICATION BY U(1)_χ CHARGE")
    print("=" * 70)
    charged_weights = classify_weights_by_u1_charge(weights)

    for charge in sorted(charged_weights.keys(), reverse=True):
        print(f"\nCharge q = {charge:+2d}:")
        for w in charged_weights[charge]:
            print(f"  {w}")

    # Step 3: Compute c_2(E)
    mu, details = compute_c2_via_charges(charged_weights)

    # Step 4: Compute index
    index, is_correct = compute_index(mu)

    # Final summary
    print("\n" + "=" * 70)
    print("FINAL VERDICT")
    print("=" * 70)
    print(f"\nSecond Chern number:  μ = {details['total_coeff']:+6d}")
    print(f"Atiyah-Singer index:  ind(D_E^c) = {index:+6.1f}")
    print(f"Target:               ind = 16")
    print(f"\nResult: {'PASS ✓' if is_correct else 'FAIL ✗ — FALSIFIED'}")

    if not is_correct:
        print(f"\n** PILLAR 4 SUB-TASK 2 IS FALSIFIED **")
        print(f"The Math162 bundle with canonical SU(5) branching")
        print(f"does NOT produce 16 chiral zero modes.")
        print(f"\nExpected:  μ = 0,  ind = 16")
        print(f"Obtained:  μ = {details['total_coeff']:+6d},  ind = {index:+6.1f}")
        print(f"\nRevision required: alternative bundle structure needed.")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
