#!/usr/bin/env python3
"""
Math167 Čech Cocycle Verification: g01 * g12 * g20 = I on triple overlap
================================================================================

This script numerically verifies the Čech cocycle identity on the triple overlap
$\mathcal{U}_0 \cap \mathcal{U}_1 \cap \mathcal{U}_2$ of $\mathbb{CP}^2$.

The transition functions are:
  g_01 = exp(i * arg(u_1) * T_3)   on U_0 cap U_1
  g_12 = exp(i * arg(v_2) * T_3)   on U_1 cap U_2
  g_02 = exp(i * arg(u_2) * T_3)   on U_0 cap U_2

And the cocycle condition is: g_01 * g_12 * g_20 = I

where g_20 = g_02^{-1}.

The phase relationship on the triple overlap is:
  arg(u_1) = -arg(v_1)
  arg(u_2) = arg(v_2) - arg(v_1)

So: arg(u_1) + arg(v_2) - arg(u_2) = -arg(v_1) + arg(v_2) - (arg(v_2) - arg(v_1)) = 0 (mod 2π)

This is verified numerically at sample points in the triple overlap.
"""

import numpy as np
from scipy.linalg import expm
import warnings
warnings.filterwarnings('ignore')

def arg(z):
    """Argument of complex number z (branch cut on negative real axis)."""
    return np.angle(z)

def SU5_cartan_T3():
    """
    Cartan generator T_3 of su(5).
    Diagonal matrix with eigenvalues (1, 1, -1, -1, 0) / sqrt(2).
    Chosen in fundamental 5-representation.
    """
    T3 = np.diag([1, 1, -1, -1, 0]) / np.sqrt(2)
    return T3

def transition_g01(u1):
    """g_01 = exp(i * arg(u1) * T3)"""
    T3 = SU5_cartan_T3()
    phase = arg(u1)
    return expm(1j * phase * T3)

def transition_g12(v2):
    """g_12 = exp(i * arg(v2) * T3)"""
    T3 = SU5_cartan_T3()
    phase = arg(v2)
    return expm(1j * phase * T3)

def transition_g02(u2):
    """g_02 = exp(i * arg(u2) * T3)"""
    T3 = SU5_cartan_T3()
    phase = arg(u2)
    return expm(1j * phase * T3)

def u1_from_v(v1, v2):
    """Coordinate transformation: u1 = 1 / v1, u2 = v2 / v1"""
    u1 = 1.0 / v1 if abs(v1) > 1e-15 else np.inf
    u2 = v2 / v1 if abs(v1) > 1e-15 else np.inf
    return u1, u2

def cocycle_product(u1, u2, v1, v2):
    """
    Compute g_01(u1) * g_12(v2) * g_20(u2) = g_01 * g_12 * g_02^{-1}

    Returns the product and its norm (should be close to 1 for identity).
    """
    g01 = transition_g01(u1)
    g12 = transition_g12(v2)
    g02 = transition_g02(u2)
    g02_inv = np.linalg.inv(g02)

    product = g01 @ g12 @ g02_inv

    return product

def test_cocycle_on_triple_overlap():
    """
    Sample points in the triple overlap U_0 ∩ U_1 ∩ U_2 and verify cocycle.
    """
    print("=" * 80)
    print("Math167 Čech Cocycle Verification")
    print("=" * 80)
    print()

    # Sample points on the triple overlap
    # We parametrize by (v1, v2) in U_1 cap U_2, avoiding singularities

    n_samples = 20
    errors = []

    print(f"Testing {n_samples} sample points in U_0 ∩ U_1 ∩ U_2:\n")
    print(f"{'Point':<8} {'|v1|':<12} {'|v2|':<12} {'Phase(g01*g12*g20)':<20} {'||g01*g12*g20 - I||':<20}")
    print("-" * 80)

    for i in range(n_samples):
        # Parametrize by random phases and radii (avoiding singularities)
        r1 = 0.3 + 0.5 * np.random.rand()  # |v1|
        phi1 = 2 * np.pi * np.random.rand()
        v1 = r1 * np.exp(1j * phi1)

        r2 = 0.3 + 0.5 * np.random.rand()  # |v2|
        phi2 = 2 * np.pi * np.random.rand()
        v2 = r2 * np.exp(1j * phi2)

        # Compute U_0 coordinates from V coordinates
        u1, u2 = u1_from_v(v1, v2)

        if np.isinf(u1) or np.isinf(u2):
            continue

        # Compute cocycle product
        cocycle = cocycle_product(u1, u2, v1, v2)

        # Identity matrix for comparison
        identity = np.eye(5)

        # Error: ||cocycle - I||_F (Frobenius norm)
        error = np.linalg.norm(cocycle - identity, 'fro')
        errors.append(error)

        # Extract a phase from the product (trace argument for diagonal part)
        trace_cocycle = np.trace(cocycle)
        phase_prod = arg(trace_cocycle)

        print(f"{i+1:<8} {abs(v1):<12.6f} {abs(v2):<12.6f} {phase_prod:<20.10f} {error:<20.2e}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    errors = np.array(errors)
    max_error = np.max(errors)
    mean_error = np.mean(errors)

    print(f"Maximum ||g01*g12*g20 - I||:  {max_error:.4e}")
    print(f"Mean ||g01*g12*g20 - I||:     {mean_error:.4e}")
    print(f"Standard deviation:            {np.std(errors):.4e}")
    print()

    tolerance = 1e-10
    if max_error < tolerance:
        print(f"✓ COCYCLE CLOSES: All errors < {tolerance}")
        print("  The Čech cocycle condition g_01 * g_12 * g_20 = I is verified to machine precision.")
        return True
    else:
        print(f"✗ COCYCLE DOES NOT CLOSE: Max error {max_error:.4e} > {tolerance}")
        print("  Possible issue with coordinate transformations or phase definitions.")
        return False

def test_phase_relationship():
    """
    Verify the phase relationship: arg(u1) + arg(v2) - arg(u2) = 0 (mod 2π)
    """
    print()
    print("=" * 80)
    print("Phase Relationship Verification")
    print("=" * 80)
    print()

    n_samples = 20
    phase_errors = []

    print(f"Testing phase closure: arg(u1) + arg(v2) - arg(u2) ≡ 0 (mod 2π)\n")
    print(f"{'Point':<8} {'arg(u1)':<15} {'arg(v2)':<15} {'arg(u2)':<15} {'Sum (mod 2π)':<20}")
    print("-" * 80)

    for i in range(n_samples):
        # Random parameters
        r1 = 0.3 + 0.5 * np.random.rand()
        phi1 = 2 * np.pi * np.random.rand()
        v1 = r1 * np.exp(1j * phi1)

        r2 = 0.3 + 0.5 * np.random.rand()
        phi2 = 2 * np.pi * np.random.rand()
        v2 = r2 * np.exp(1j * phi2)

        # Compute u coordinates
        u1 = 1.0 / v1 if abs(v1) > 1e-15 else np.inf
        u2 = v2 / v1 if abs(v1) > 1e-15 else np.inf

        if np.isinf(u1) or np.isinf(u2):
            continue

        arg_u1 = arg(u1)
        arg_v2 = arg(v2)
        arg_u2 = arg(u2)

        phase_sum = (arg_u1 + arg_v2 - arg_u2) % (2 * np.pi)
        if phase_sum > np.pi:
            phase_sum -= 2 * np.pi  # Wrap to [-π, π]

        phase_errors.append(abs(phase_sum))

        print(f"{i+1:<8} {arg_u1:<15.10f} {arg_v2:<15.10f} {arg_u2:<15.10f} {phase_sum:<20.2e}")

    print()
    phase_errors = np.array(phase_errors)
    max_phase_error = np.max(phase_errors)

    print(f"Maximum phase error: {max_phase_error:.4e} rad")
    print()

    if max_phase_error < 1e-10:
        print("✓ PHASE RELATIONSHIP VERIFIED: arg(u1) + arg(v2) - arg(u2) ≡ 0 (mod 2π)")
        return True
    else:
        print(f"✗ PHASE RELATIONSHIP ERROR: Max {max_phase_error:.4e} rad")
        return False

if __name__ == "__main__":
    cocycle_ok = test_cocycle_on_triple_overlap()
    phase_ok = test_phase_relationship()

    print()
    print("=" * 80)
    if cocycle_ok and phase_ok:
        print("OVERALL RESULT: ✓ ALL TESTS PASSED")
        print("The three-patch Čech cocycle closes correctly.")
    else:
        print("OVERALL RESULT: ✗ SOME TESTS FAILED")
        print("Review the phase definitions or coordinate transformations.")
    print("=" * 80)
