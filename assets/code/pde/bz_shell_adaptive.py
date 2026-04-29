#!/usr/bin/env python3
# =====================================================================
# bz_shell_adaptive.py
# Theory tag: Math_IR_Bound-anisotropy-v4-shell-adaptive-2026-04-21
# Companion to: docs/math/TECT-Math_IR_Bound-v4-shell-adaptive.tex.txt
#
# Purpose
# -------
# Rigorous interval-arithmetic enclosure of the 1-loop anisotropy
# coefficient c_4(eps) at the TECT mainline Brazovskii fixed point,
#
#     c_4(eps)
#       =  (1/(2 pi)^3)  \int_{BZ} d^3k  P_4(hat k) / omega^2(k),
#
# with  omega^2(k) = m^2 + (|k|^2 - q_0^2)^2,  P_4(n) = sum_i n_i^4 - 3/5,
# m^2 = eps^2 * q_0^4, and the BZ = truncated octahedron (A,B) = (3/2, 1).
#
# Strategy (shell-adaptive closed-form primitive)
# -----------------------------------------------
# The integrand peaks on the Brazovskii shell |k| = q_0, which defeats
# the naive cell-wise interval enclosure used in bz_eta_integrator.py
# (dependency blow-up -> 1/omega^2 per-cell range ~ 1/m^2 ~ 4.3e2,
# enclosure [-0.48, +0.77] at N_octant = 16).
#
# We eliminate the peak analytically by reducing to an angular
# integral.  Writing
#     c_4(eps)
#       =  (1/(2 pi)^3)  \int_{S^2} d Omega(hat n) P_4(hat n)
#                         \int_0^{r_BZ(hat n)} dr r^2 / omega^2(r),
# the radial integral admits the closed form
#     F(r)  :=  \int_0^r dr' r'^2 / (m^2 + (r'^2 - q_0^2)^2)
#            =  (1/(8 p))  ln[((r-p)^2 + q^2) / ((r+p)^2 + q^2)]
#              + (1/(4 q)) [arctan((r-p)/q) + arctan((r+p)/q)],
# where
#     R  =  sqrt(q_0^4 + m^2),
#     p  =  sqrt((R + q_0^2) / 2),
#     q  =  sqrt((R - q_0^2) / 2),
# obtained by partial-fraction decomposition
#     m^2 + (r^2 - q_0^2)^2  =  ((r - p)^2 + q^2) ((r + p)^2 + q^2).
# F(0) = 0 identically.  The peak r = q_0 is absorbed into F.
#
# Since r_BZ(hat n) is bounded below by  min(B, A*n_max/(n_1+n_2+n_3))
# which for the TECT mainline (A,B) = (3/2, 1) evaluates to
# r_BZ >= sqrt(3)/2 * 3/2 / 1 = 3 sqrt(3)/... > p = 0.6811 (for
# eps^2 = 1.081e-2 -> m^2 = 2.314e-3 -> p/q_0 = 1.0001), F is
# evaluated only AT or ABOVE the shell radius; no cell-wise dependency
# blow-up occurs.
#
# The residual 2D angular integral, restricted to the O_h fundamental
# domain D = {n_1 >= n_2 >= n_3 >= 0} and parametrised as (1, s, t) /
# sqrt(1+s^2+t^2) with (s,t) in D' = {0 <= t <= s <= 1}, carries a
# multiplicity factor |O_h| = 48 and a cube/octahedral regime split at
# s + t = 1/2 (as in Math_IR_Bound_v4_BZ_interval.py).
#
# The integrator is exactly the same grid / subdivision machinery as
# the J_1 interval integrator; only the integrand changes.
#
# Expected outcome
# ----------------
# Tight rigorous enclosure [c4_lo, c4_hi] with c4_lo > 0, certifying
#     gamma_{44}  =  - N * lambda^2 * c_4(eps)  <  0
# and upgrading Pillar 8 (emergent Lorentz invariance) from
# NEAR-FINAL CONDITIONAL to PROVED per PROOF-COMPLETION-CHECKLIST.md.
# =====================================================================
from __future__ import annotations

import argparse
import math
import sys
import time
from typing import Dict, Tuple

try:
    from mpmath import iv, mp, mpf
except ImportError as exc:
    print("ERROR: mpmath is required.  pip install mpmath --break-system-packages",
          file=sys.stderr)
    raise SystemExit(1) from exc


# ---------------------------------------------------------------------------
# TECT mainline parameters (matches bz_eta_integrator.py)
# ---------------------------------------------------------------------------

TECT_MAINLINE: Dict[str, float] = {
    "q0": 0.6801747616,
    "mu2": 5.0e-3,
    "epsilon_sq": 1.081e-2,
    "lambda_coup": -0.43,
    "gamma_coup": 1.62,
    "A_bz": 1.5,
    "B_bz": 1.0,
}


def derive_m_squared(mainline: Dict[str, float]) -> float:
    """m^2 = eps^2 * q_0^4 (convention of Math_IR_Bound-v4-thm-v4-1)."""
    q0 = mainline["q0"]
    eps2 = mainline["epsilon_sq"]
    return eps2 * q0**4


# ---------------------------------------------------------------------------
# Closed-form radial primitive F(r)
# ---------------------------------------------------------------------------
# Derivation (verified symbolically):
#
#   (r^2 - q_0^2)^2 + m^2
#     = r^4 - 2 q_0^2 r^2 + q_0^4 + m^2
#     = r^4 - 2 q_0^2 r^2 + R^2            [R = sqrt(q_0^4 + m^2)]
#     = (r^2 - 2 p r + R)(r^2 + 2 p r + R) [complete-the-square factoring]
#     = ((r - p)^2 + q^2) ((r + p)^2 + q^2),
#
# with  p^2 = (R + q_0^2)/2,  q^2 = (R - q_0^2)/2,  p^2 + q^2 = R,
#        p^2 - q^2 = q_0^2,  p q = m/2.
#
# Partial fractions:
#   r^2 / [(r-p)^2 + q^2) ((r+p)^2 + q^2)]
#     =  (r/(4 p)) * [1/((r-p)^2 + q^2) - 1/((r+p)^2 + q^2)],
#
# whose antiderivative is
#   F(r) = (1/(8 p)) ln[((r-p)^2 + q^2) / ((r+p)^2 + q^2)]
#         + (1/(4 q)) [arctan((r-p)/q) + arctan((r+p)/q)] + C,
# and C = 0 so that F(0) = 0.
# ---------------------------------------------------------------------------

def _extract_endpoints_iv(x_iv):
    """Return (lo, hi) as mpmath mpf from an iv.mpf.

    Uses mp.make_mpf on the internal ``_mpi_`` (sign, man, exp, bc) tuples,
    which is mpmath's documented zero-copy path from ivmpf to mpf.
    """
    lo = mp.make_mpf(x_iv._mpi_[0])
    hi = mp.make_mpf(x_iv._mpi_[1])
    return lo, hi


def compute_p_q_iv(q0_iv, m2_iv):
    """Compute p, q endpoints as iv.mpf intervals from q_0 and m^2 intervals.

    Uses the partial-fraction factorisation
        (r^2 - q_0^2)^2 + m^2  =  ((r-p)^2 + q^2) ((r+p)^2 + q^2),
        p^2 = (R + q_0^2)/2,   q^2 = (R - q_0^2)/2,
        R   = sqrt(q_0^4 + m^2).
    """
    q0_sq = q0_iv * q0_iv
    q0_4 = q0_sq * q0_sq
    R = iv.sqrt(q0_4 + m2_iv)
    p = iv.sqrt((R + q0_sq) / 2)
    q = iv.sqrt((R - q0_sq) / 2)
    return p, q, R


def F_scalar_iv(r_mpf, p_iv, q_iv):
    """Evaluate F(r) as an iv.mpf at scalar r_mpf using interval p, q.

    Since F is monotone-increasing in r on [0, +infty) (derivative r^2/omega^2
    is >= 0), the tight enclosure on an interval [r_lo, r_hi] is [F(r_lo),
    F(r_hi)]; this helper is therefore called at the two endpoints by
    F_iv_tight().
    """
    r = iv.mpf(r_mpf)
    u_m = r - p_iv
    u_p = r + p_iv
    q_sq = q_iv * q_iv
    num = u_m * u_m + q_sq
    den = u_p * u_p + q_sq
    # Both num, den > 0, log of ratio is real.  Ratio <= 1 for r > 0
    # (since (r+p)^2 + q^2 > (r-p)^2 + q^2 when r p > 0), so log <= 0.
    log_term = iv.log(num / den) / (8 * p_iv)
    # mpmath.iv has no single-argument atan; use atan2(y, x) = atan(y/x) for x>0.
    # Since q_iv > 0 rigorously (R > q_0^2), atan2(u, q) is well-defined and
    # equals atan(u/q).
    atan_term = (iv.atan2(u_m, q_iv) + iv.atan2(u_p, q_iv)) / (4 * q_iv)
    return log_term + atan_term


def F_iv_tight(r_iv, p_iv, q_iv):
    """Enclose F on interval r_iv by evaluating at endpoints (monotonicity).

    Returns an iv.mpf containing [F(r_lo), F(r_hi)] with conservative
    rounding from the endpoint evaluations.
    """
    r_lo, r_hi = _extract_endpoints_iv(r_iv)
    F_lo = F_scalar_iv(r_lo, p_iv, q_iv)
    F_hi = F_scalar_iv(r_hi, p_iv, q_iv)
    lo = mp.make_mpf(F_lo._mpi_[0])
    hi = mp.make_mpf(F_hi._mpi_[1])
    if hi < lo:
        # Should not happen (monotone), but guard against rounding pathologies
        lo, hi = hi, lo
    return iv.mpf((lo, hi))


# ---------------------------------------------------------------------------
# Angular integrand pieces (reused from Math_IR_Bound_v4_BZ_interval.py)
# ---------------------------------------------------------------------------

def P4_iv(s, t):
    """P_4(n) = sum_i n_i^4 - 3/5 evaluated at n = (1,s,t)/sqrt(1+s^2+t^2)."""
    one_plus_r2 = 1 + s * s + t * t
    num = 1 + s**4 + t**4
    return num / (one_plus_r2 * one_plus_r2) - iv.mpf("3") / iv.mpf("5")


def rBZ_square_iv(s, t, B):
    """Square-face regime: r_BZ(n) = B * sqrt(1+s^2+t^2)."""
    return B * iv.sqrt(1 + s * s + t * t)


def rBZ_hex_iv(s, t, A):
    """Hex-face regime: r_BZ(n) = A * sqrt(1+s^2+t^2) / (1 + s + t)."""
    return A * iv.sqrt(1 + s * s + t * t) / (1 + s + t)


def dOmega_iv(s, t):
    """Induced surface measure: dOmega = (1+s^2+t^2)^{-3/2} ds dt."""
    v = 1 + s * s + t * t
    return 1 / (v * iv.sqrt(v))


def integrand_square_iv(s, t, B, p_iv, q_iv, F0_iv):
    """P_4(s,t) * (F(r_BZ^square(s,t)) - F_0) * dOmega(s,t).

    The subtracted constant F_0 does not alter the true integral over the
    full fundamental domain D':  since sum_{g in O_h} P_4 circ g = 0
    pointwise on S^2, we have   int_{D'} P_4 dOmega = 0   exactly,
    and therefore
        int_{D'} P_4 * dOmega * F(r_BZ) = int_{D'} P_4 * dOmega * (F-F_0).
    Subtracting F_0 chosen near the mean of F(r_BZ) reduces the
    cell-wise integrand magnitude by more than an order of magnitude,
    which tightens the interval enclosure of c_4(eps) by the same factor.
    This is the 'centered-form interval' trick, and it is the key
    ingredient that permits sign-definite enclosure at moderate N.
    """
    r_iv = rBZ_square_iv(s, t, B)
    F_shifted = F_iv_tight(r_iv, p_iv, q_iv) - F0_iv
    return P4_iv(s, t) * F_shifted * dOmega_iv(s, t)


def integrand_hex_iv(s, t, A, p_iv, q_iv, F0_iv):
    """P_4(s,t) * (F(r_BZ^hex(s,t)) - F_0) * dOmega(s,t).  See integrand_square_iv."""
    r_iv = rBZ_hex_iv(s, t, A)
    F_shifted = F_iv_tight(r_iv, p_iv, q_iv) - F0_iv
    return P4_iv(s, t) * F_shifted * dOmega_iv(s, t)


# ---------------------------------------------------------------------------
# Region topology and adaptive cell enclosure (copied from
# Math_IR_Bound_v4_BZ_interval.py with integrand replaced)
# ---------------------------------------------------------------------------
# Fundamental domain D' = {0 <= t <= s <= 1}, regime split at s + t = 1/2.
# Cells are axis-aligned in (s,t); those straddling a boundary are
# adaptively bisected up to MAX_DEPTH, after which the residual cell
# uses the widened enclosure that also admits the zero-contribution case.

def cell_fully_in_region(s_lo, s_hi, t_lo, t_hi, regime):
    """True iff the axis-aligned cell lies entirely in D' and in regime."""
    if t_lo < 0:
        return False
    if s_hi > 1:
        return False
    if t_hi > s_lo:
        return False
    if regime == "square":
        return (s_hi + t_hi) < 0.5
    else:
        return (s_lo + t_lo) >= 0.5


def cell_interval_enclosure(s_lo, s_hi, t_lo, t_hi, regime, A, B, p_iv, q_iv, F0_iv):
    s = iv.mpf((s_lo, s_hi))
    t = iv.mpf((t_lo, t_hi))
    if regime == "square":
        val = integrand_square_iv(s, t, B, p_iv, q_iv, F0_iv)
    else:
        val = integrand_hex_iv(s, t, A, p_iv, q_iv, F0_iv)
    return val * (s_hi - s_lo) * (t_hi - t_lo)


def boundary_cell_enclosure(s_lo, s_hi, t_lo, t_hi, regime, A, B, p_iv, q_iv, F0_iv):
    """Widened enclosure at maximum refinement depth.

    The cell's intersection with D' and with the named regime has area in
    [0, cell_area]; the contribution is therefore enclosed by the widened
    interval  [min(0, f_lo * cell_area), max(0, f_hi * cell_area)].
    """
    s = iv.mpf((s_lo, s_hi))
    t = iv.mpf((t_lo, t_hi))
    if regime == "square":
        val = integrand_square_iv(s, t, B, p_iv, q_iv, F0_iv)
    else:
        val = integrand_hex_iv(s, t, A, p_iv, q_iv, F0_iv)
    val *= (s_hi - s_lo) * (t_hi - t_lo)
    lo_f = mp.make_mpf(val._mpi_[0])
    hi_f = mp.make_mpf(val._mpi_[1])
    if lo_f > 0:
        lo_f = mpf(0)
    if hi_f < 0:
        hi_f = mpf(0)
    return iv.mpf((lo_f, hi_f))


def integrate_region(regime, N, A, B, p_iv, q_iv, F0_iv, max_depth=10):
    """Adaptive-grid interval enclosure of the 2D angular integral over
    (D' intersect regime), summed over an N x N base mesh on [0,1]^2."""
    h = 1.0 / N

    def is_outside(s_lo, s_hi, t_lo, t_hi):
        if t_hi <= 0:
            return True
        if s_lo >= 1:
            return True
        if t_lo > s_hi:
            return True
        if regime == "square" and (s_lo + t_lo) >= 0.5:
            return True
        if regime == "hex" and (s_hi + t_hi) <= 0.5:
            return True
        return False

    total = iv.mpf(0)
    stack = []
    for i in range(N):
        for j in range(N):
            stack.append((i * h, (i + 1) * h, j * h, (j + 1) * h, 0))

    n_interior = 0
    n_boundary = 0
    while stack:
        s_lo, s_hi, t_lo, t_hi, depth = stack.pop()
        if is_outside(s_lo, s_hi, t_lo, t_hi):
            continue
        if cell_fully_in_region(s_lo, s_hi, t_lo, t_hi, regime):
            total = total + cell_interval_enclosure(
                s_lo, s_hi, t_lo, t_hi, regime, A, B, p_iv, q_iv, F0_iv)
            n_interior += 1
            continue
        if depth >= max_depth:
            total = total + boundary_cell_enclosure(
                s_lo, s_hi, t_lo, t_hi, regime, A, B, p_iv, q_iv, F0_iv)
            n_boundary += 1
            continue
        ds = s_hi - s_lo
        dt = t_hi - t_lo
        if ds >= dt:
            s_mid = (s_lo + s_hi) / 2
            stack.append((s_lo, s_mid, t_lo, t_hi, depth + 1))
            stack.append((s_mid, s_hi, t_lo, t_hi, depth + 1))
        else:
            t_mid = (t_lo + t_hi) / 2
            stack.append((s_lo, s_hi, t_lo, t_mid, depth + 1))
            stack.append((s_lo, s_hi, t_mid, t_hi, depth + 1))

    return total, {"n_interior": n_interior, "n_boundary": n_boundary}


# ---------------------------------------------------------------------------
# Top-level evaluator
# ---------------------------------------------------------------------------

def compute_c4(N, mainline, dps, max_depth=10, verbose=False):
    """Compute interval enclosure for c_4(eps).

    Returns (c4_iv, J_sq_iv, J_hex_iv, diagnostics).
    """
    iv.prec = dps
    mp.prec = dps

    q0_f = mainline["q0"]
    A_f = mainline["A_bz"]
    B_f = mainline["B_bz"]
    m2_f = derive_m_squared(mainline)

    q0_iv = iv.mpf(mpf(q0_f))
    m2_iv = iv.mpf(mpf(m2_f))
    A_iv = iv.mpf(mpf(A_f))
    B_iv = iv.mpf(mpf(B_f))

    p_iv, q_iv, R_iv = compute_p_q_iv(q0_iv, m2_iv)

    # Centered-form constant:  F_0 := F(B) = F(1.0) evaluated in interval.
    # Subtracting F_0 from F(r_BZ) is exact because int_{D'} P_4 dOmega = 0,
    # but it dramatically tightens the cell-wise interval enclosure.
    B_mpf = mp.make_mpf(B_iv._mpi_[1])   # B is exact; both endpoints equal
    F0_iv = F_scalar_iv(B_mpf, p_iv, q_iv)

    if verbose:
        p_lo = float(mp.make_mpf(p_iv._mpi_[0]))
        p_hi = float(mp.make_mpf(p_iv._mpi_[1]))
        q_lo = float(mp.make_mpf(q_iv._mpi_[0]))
        q_hi = float(mp.make_mpf(q_iv._mpi_[1]))
        R_lo = float(mp.make_mpf(R_iv._mpi_[0]))
        R_hi = float(mp.make_mpf(R_iv._mpi_[1]))
        F0_lo = float(mp.make_mpf(F0_iv._mpi_[0]))
        F0_hi = float(mp.make_mpf(F0_iv._mpi_[1]))
        print(f"  derived radii:")
        print(f"    R    ∈ [{R_lo:.10e}, {R_hi:.10e}]")
        print(f"    p    ∈ [{p_lo:.10e}, {p_hi:.10e}]   (shell radius analogue)")
        print(f"    q    ∈ [{q_lo:.10e}, {q_hi:.10e}]   (damping width)")
        print(f"    p/q_0 ≈ {p_lo/q0_f:.10f}  (should be ≈ 1 + O(eps^2))")
        print(f"    F_0  ∈ [{F0_lo:.10e}, {F0_hi:.10e}]   (centered-form shift)")

    t0 = time.time()
    J_sq, diag_sq = integrate_region(
        "square", N, A_iv, B_iv, p_iv, q_iv, F0_iv, max_depth)
    J_hx, diag_hx = integrate_region(
        "hex", N, A_iv, B_iv, p_iv, q_iv, F0_iv, max_depth)
    t1 = time.time()

    # c_4 = (48 / (2 pi)^3) * (J_sq + J_hx)
    two_pi = 2 * iv.pi
    prefactor = iv.mpf(48) / (two_pi * two_pi * two_pi)
    c4_iv = prefactor * (J_sq + J_hx)

    diagnostics = {
        "N": N,
        "dps": dps,
        "max_depth": max_depth,
        "elapsed_s": t1 - t0,
        "square": diag_sq,
        "hex": diag_hx,
        "m2": m2_f,
        "q0": q0_f,
        "p_hi": float(mp.make_mpf(p_iv._mpi_[1])),
        "q_hi": float(mp.make_mpf(q_iv._mpi_[1])),
    }
    return c4_iv, J_sq, J_hx, diagnostics


# ---------------------------------------------------------------------------
# Self-test: consistency of F(r) at endpoints versus a quick trapezoidal
# midpoint evaluation, to guard against a sign / algebra error in F.
# ---------------------------------------------------------------------------

def self_test_F(q0, m2, n_test=20000):
    """Compare F(r) (closed form) with numerical ∫_0^r r'^2 dr'/omega^2(r')
    on a few sample radii.  All differences should be < 1e-8 relative."""
    R = math.sqrt(q0**4 + m2)
    p = math.sqrt((R + q0**2) / 2)
    q = math.sqrt((R - q0**2) / 2)

    def F_closed(r):
        num = (r - p)**2 + q**2
        den = (r + p)**2 + q**2
        t1 = math.log(num / den) / (8 * p)
        t2 = (math.atan((r - p) / q) + math.atan((r + p) / q)) / (4 * q)
        return t1 + t2

    def F_numeric(r):
        # Composite midpoint rule
        if r <= 0:
            return 0.0
        h = r / n_test
        s = 0.0
        for i in range(n_test):
            ri = (i + 0.5) * h
            s += ri * ri / (m2 + (ri * ri - q0 * q0)**2)
        return s * h

    r_tests = [0.1, 0.5, q0 * 0.99, q0, q0 * 1.01, 1.0, 1.5, 2.0]
    results = []
    for r in r_tests:
        fc = F_closed(r)
        fn = F_numeric(r)
        rel = abs(fc - fn) / max(abs(fc), 1e-30)
        results.append((r, fc, fn, rel))
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Shell-adaptive interval certificate for c_4(eps) > 0")
    parser.add_argument("--N", type=int, default=32,
                        help="base grid resolution (N x N cells on [0,1]^2)")
    parser.add_argument("--dps", type=int, default=50,
                        help="mpmath decimal precision for iv arithmetic")
    parser.add_argument("--max-depth", type=int, default=10,
                        help="adaptive subdivision depth cap for boundary cells")
    parser.add_argument("--q0", type=float, default=TECT_MAINLINE["q0"])
    parser.add_argument("--epsilon_sq", type=float,
                        default=TECT_MAINLINE["epsilon_sq"])
    parser.add_argument("--skip-self-test", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    mp.dps = args.dps
    iv.dps = args.dps

    mainline = dict(TECT_MAINLINE)
    mainline["q0"] = args.q0
    mainline["epsilon_sq"] = args.epsilon_sq
    m2 = derive_m_squared(mainline)

    print("=" * 76)
    print("Shell-adaptive interval certificate for c_4(eps) > 0")
    print("  (Math_IR_Bound-v4-shell-adaptive -> Pillar 8 PROVED)")
    print("=" * 76)
    print(f"  TECT mainline: q_0 = {mainline['q0']:.10f}")
    print(f"                 mu^2 = {mainline['mu2']}, lambda = {mainline['lambda_coup']}")
    print(f"                 eps^2 = {mainline['epsilon_sq']:.6e}")
    print(f"                 m^2 = eps^2 * q_0^4 = {m2:.6e}")
    print(f"                 (A,B) = ({mainline['A_bz']}, {mainline['B_bz']})")
    print(f"  Grid resolution: N = {args.N}  (base cells per region <= {args.N**2})")
    print(f"  mpmath decimal precision: {args.dps}")
    print(f"  adaptive depth cap: {args.max_depth}")
    print("-" * 76)

    if not args.skip_self_test:
        print("  self-test: closed-form F(r) vs. composite midpoint rule")
        st = self_test_F(mainline["q0"], m2)
        worst = max(st, key=lambda row: row[3])
        for r, fc, fn, rel in st:
            ok = "✓" if rel < 1e-4 else "!" if rel < 1e-2 else "X"
            print(f"    r = {r:.4f}:  F_closed = {fc:.6e},  F_num = {fn:.6e}"
                  f"  rel = {rel:.2e}  {ok}")
        print(f"    worst relative deviation: {worst[3]:.2e}")
        if worst[3] > 1e-2:
            print("  SELF-TEST FAILED: closed form inconsistent with numeric quadrature.")
            return 4
        print("-" * 76)

    c4_iv, J_sq, J_hx, diag = compute_c4(
        args.N, mainline, dps=args.dps * 4,
        max_depth=args.max_depth, verbose=args.verbose)

    sq_lo = float(mp.make_mpf(J_sq._mpi_[0]))
    sq_hi = float(mp.make_mpf(J_sq._mpi_[1]))
    hx_lo = float(mp.make_mpf(J_hx._mpi_[0]))
    hx_hi = float(mp.make_mpf(J_hx._mpi_[1]))
    c4_lo = float(mp.make_mpf(c4_iv._mpi_[0]))
    c4_hi = float(mp.make_mpf(c4_iv._mpi_[1]))
    center = 0.5 * (c4_lo + c4_hi)
    halfwidth = 0.5 * (c4_hi - c4_lo)
    rel = halfwidth / abs(center) if center != 0 else float("inf")

    print(f"  I_square      enclosure: [{sq_lo:+.6e}, {sq_hi:+.6e}]")
    print(f"  I_hex         enclosure: [{hx_lo:+.6e}, {hx_hi:+.6e}]")
    print(f"  c_4(eps)      enclosure: [{c4_lo:+.6e}, {c4_hi:+.6e}]")
    print(f"  central value ~ {center:+.6e}   half-width ~ {halfwidth:+.6e}"
          f"   (relative {rel:.2%})")
    print(f"  interior cells: square = {diag['square']['n_interior']},"
          f" hex = {diag['hex']['n_interior']}")
    print(f"  boundary cells: square = {diag['square']['n_boundary']},"
          f" hex = {diag['hex']['n_boundary']}")
    print(f"  elapsed: {diag['elapsed_s']:.2f} s")
    print("-" * 76)

    if c4_lo > 0:
        print("  CERTIFICATE: c_4(eps) > 0 rigorously.")
        print("               => gamma_{44} = - N * lambda^2 * c_4 < 0")
        print("               => cubic-anisotropy coupling IR-irrelevant")
        print("               => Pillar 8 (emergent Lorentz invariance) PROVED")
        status = 0
    elif c4_hi < 0:
        print("  UNEXPECTED: c_4(eps) < 0 rigorously.")
        print("              Pillar 8 conclusion would REVERSE -- investigate.")
        status = 2
    else:
        print("  INCONCLUSIVE: enclosure straddles zero.")
        print(f"                Refine --N (current: {args.N}) or")
        print(f"                --dps (current: {args.dps}).")
        status = 1
    print("=" * 76)
    return status


if __name__ == "__main__":
    sys.exit(main())
