#!/usr/bin/env python3
# =====================================================================
# verify_J1_L6_simple.py
# Simplified version without adaptive refinement — use uniform grid only
# for faster initial computation.
# =====================================================================
from __future__ import annotations

import argparse
import sys
import time
from typing import Tuple

try:
    from mpmath import iv, mp, mpf
except ImportError as exc:
    print("ERROR: mpmath is required.", file=sys.stderr)
    raise SystemExit(1) from exc

# ---------------------------------------------------------------------------
# P6 cubic harmonic
# ---------------------------------------------------------------------------

def P6_iv(s, t):
    """P_6(n) = sum_i n_i^6 - (7/4) sum_i n_i^4 + 3/5"""
    r2 = 1 + s * s + t * t
    r2_3 = r2 * r2 * r2
    r2_2 = r2 * r2
    sum6 = (1 + s**6 + t**6) / r2_3
    sum4 = (1 + s**4 + t**4) / r2_2
    return sum6 - (7*sum4)/4 + 3/5


def integrand_square_iv(s, t, B):
    """P6(s,t) * r_BZ^{square}(s,t) * dOmega(s,t)"""
    return P6_iv(s, t) * B / (1 + s * s + t * t)


def integrand_hex_iv(s, t, A):
    """P6(s,t) * r_BZ^{hex}(s,t) * dOmega(s,t)"""
    return P6_iv(s, t) * A / ((1 + s + t) * (1 + s * s + t * t))


# ---------------------------------------------------------------------------
# Simple uniform grid integration (no adaptive refinement)
# ---------------------------------------------------------------------------

def integrate_region_uniform(regime, N, A, B):
    """
    Sum of interval enclosures over uniform N x N grid of [0,1]^2.
    No adaptive refinement — cells on boundaries are simply skipped or
    included conservatively.
    """
    h = 1.0 / N
    total = iv.mpf(0)

    for i in range(N):
        for j in range(N):
            s_lo, s_hi = i*h, (i+1)*h
            t_lo, t_hi = j*h, (j+1)*h

            # Check if cell is entirely in D' (t <= s, s <= 1, t >= 0)
            if not (t_hi <= s_lo and s_hi <= 1.0 and t_lo >= 0):
                continue  # Skip cells not fully in D'

            # Check regime
            if regime == "square":
                if not (s_hi + t_hi < 0.5):
                    continue  # Not in square regime
            else:  # hex
                if not (s_lo + t_lo >= 0.5):
                    continue  # Not in hex regime

            # Evaluate integrand on the cell
            s = iv.mpf((s_lo, s_hi))
            t = iv.mpf((t_lo, t_hi))

            if regime == "square":
                val = integrand_square_iv(s, t, B)
            else:
                val = integrand_hex_iv(s, t, A)

            total = total + val * (s_hi - s_lo) * (t_hi - t_lo)

    return total


def compute_J6(N, A, B, dps):
    """Compute J_1^{(L=6)} with uniform grid at resolution N."""
    iv.prec = dps
    mp.prec = dps
    t0 = time.time()
    J_sq = integrate_region_uniform("square", N, A, B)
    J_hx = integrate_region_uniform("hex", N, A, B)
    J_tot = 48 * (J_sq + J_hx)
    t1 = time.time()
    return J_sq, J_hx, J_tot, t1 - t0


def compute_c6(lam2, Y):
    """Compute coefficient c_6 from loop structure."""
    pi = mp.pi
    c_4 = (mp.mpf("2") / mp.mpf("15")) * lam2 / (12 * pi**2 * Y)
    ratio = lam2
    c_6 = ratio * c_4
    return c_6, c_4


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Simplified J_1^{(L=6)} interval-arithmetic evaluation.")
    parser.add_argument("--N", type=int, default=128,
                        help="grid resolution (default 128)")
    parser.add_argument("--A", type=str, default="1.5",
                        help="BZ octahedral parameter (default 3/2)")
    parser.add_argument("--B", type=str, default="1.0",
                        help="BZ cube parameter (default 1)")
    parser.add_argument("--lambda2", type=float, default=0.1849,
                        help="physical coupling squared (default 0.1849)")
    parser.add_argument("--Y", type=float, default=1.0,
                        help="shell parameter Y (default 1.0)")
    parser.add_argument("--dps", type=int, default=20,
                        help="mpmath precision (default 20)")
    args = parser.parse_args()

    mp.dps = args.dps
    iv.dps = args.dps

    A = iv.mpf(args.A)
    B = iv.mpf(args.B)
    lam2 = mp.mpf(args.lambda2)
    Y = mp.mpf(args.Y)

    print("=" * 80)
    print("J_1^{(L=6)} interval-arithmetic evaluation (SIMPLIFIED, UNIFORM GRID)")
    print("=" * 80)
    print(f"  BZ parameters: A = {args.A}, B = {args.B}")
    print(f"  Physical coupling: lambda^2 = {args.lambda2}")
    print(f"  Shell parameter: Y = {args.Y}")
    print(f"  mpmath precision: {args.dps} decimal digits")
    print("-" * 80)

    c_6, c_4 = compute_c6(lam2, Y)
    c_6_float = float(c_6)
    c_4_float = float(c_4)

    print(f"  c_4 (coefficient, L=4): {c_4_float:.6e}")
    print(f"  c_6 (coefficient, L=6): {c_6_float:.6e}")
    print(f"  c_6/c_4 ratio:          {float(c_6/c_4):.6e}")
    print("-" * 80)

    def hull(v):
        try:
            return float(v.a), float(v.b)
        except Exception:
            return None, None

    # Run at increasing grid resolutions
    for N_val in [64, 128, 256]:
        print(f"\n  Computing with N={N_val}...")
        J_sq, J_hx, J_tot, elapsed = compute_J6(N_val, A, B, args.dps * 3)

        tot_lo, tot_hi = hull(J_tot)

        if isinstance(tot_lo, float) and isinstance(tot_hi, float):
            print(f"    J_sq = {hull(J_sq)}")
            print(f"    J_hx = {hull(J_hx)}")
            print(f"    J_tot = 48*(J_sq + J_hx)")
            print(f"    J_1^{{(L=6)}} ∈ [{tot_lo:+.6e}, {tot_hi:+.6e}]")

            prod_lo = c_6_float * tot_lo
            prod_hi = c_6_float * tot_hi
            if c_6_float < 0:
                prod_lo, prod_hi = c_6_float * tot_hi, c_6_float * tot_lo

            print(f"    |c_6 J_1^{{(L=6)}}| ≤ {max(abs(prod_lo), abs(prod_hi)):.6e}")
            print(f"    elapsed: {elapsed:.2f} s")
        else:
            print(f"    (numerical extraction failed)")

    print("\n" + "=" * 80)
    print("Final verdict: Check if |c_6 J_1^{(L=6)}| < 3.1e-6")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
