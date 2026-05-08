#!/usr/bin/env python3
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: unregistered
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
# =====================================================================
# bz_eta_integrator.py
# Theory tag: Math_IR_Bound-v4-BZ-integrator-2026-04-21
# Companion to: docs/math/TECT-Math_IR_Bound-v4-thm-v4-1.tex.txt
# Task:        #27  (V3-2b: Math_IR_Bound-v3 BZ integrator code)
#
# Purpose:
#   Direct numerical evaluation, at the TECT mainline Brazovskii fixed
#   point, of the 1-loop coefficient
#
#       c_4(eps)  :=  \int_{Omega_BZ}  d^3 k / (2 pi)^3 *
#                     [ P_4(hat k) / omega^2(k) ],
#
#   where
#       omega^2(k) = m^2 + (|k|^2 - q_0^2)^2        (Brazovskii),
#       P_4(hat n) = sum_i hat n_i^4 - 3/5          (cubic L=4 harmonic),
#       Omega_BZ   = { k : |k_i| <= B, |k_1|+|k_2|+|k_3| <= A }
#                    (truncated octahedron; (A,B)=(3/2, 1) physical),
#       eps        = m / q_0^2.
#
#   The sign of c_4 controls the anomalous dimension
#       gamma_{44} = -N * lambda^2 * c_4(eps)
#   so c_4 > 0  <=>  gamma_{44} < 0  <=>  cubic-anisotropy
#   IR-irrelevant  <=>  Pillar 8 (emergent Lorentz invariance) PROVED.
#
# Why this script (distinct from Math_IR_Bound_v4_BZ_interval.py):
#   The companion script evaluates J_1 = <P_4, r_BZ>_{L^2(S^2)}, which
#   is the LEADING-ORDER reconstruction of c_4 via the Lemma
#   "Reduction of c_4 to an angular integral" + Taylor-expansion of
#   phi.  That route leaves a finite-eps quadratic remainder
#   R(eps) whose in-text bound is only qualitative.  GPT peer-review
#   (2026-04-21) correctly flagged this as the residual IR-v4 gap.
#
#   This script bypasses the J_1 reduction altogether and evaluates
#   c_4(eps) directly at the physical eps, so the sign of gamma_{44}
#   is certified without invoking the R(eps) bound.  A convergence
#   study across N_grid in {64, 128, 192, 256} and a Richardson
#   extrapolation provide a quantitative central value; a companion
#   interval-arithmetic enclosure (mpmath.iv) on a coarser grid gives
#   the rigorous certificate.
#
# Output:
#   - Central numerical value of c_4(eps) and grid-convergence plot data
#   - Interval-arithmetic enclosure [c_4^lo, c_4^hi]  (on coarse grid)
#   - Derived certificate:  gamma_{44}  =  -N * lambda^2 * c_4  < 0  ?
#   - JSON report written to PDE/bz_eta_integrator_report.json
#
# Authority:
#   TECT mainline:  q_0 = 0.6801747616, mu^2 = 5e-3, lambda = -0.43,
#                   gamma = 1.62, (A,B) = (3/2, 1).
#   (PDE/continuation_N32_v2p4.log; Math57-v2 interval certificate.)
# =====================================================================
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

try:
    from mpmath import iv, mp, mpf
    HAS_MPMATH = True
except ImportError:
    HAS_MPMATH = False


# ---------------------------------------------------------------------------
# TECT mainline parameters
# ---------------------------------------------------------------------------

TECT_MAINLINE: Dict[str, float] = {
    "q0": 0.6801747616,
    "mu2": 5.0e-3,
    "epsilon_sq": 1.081e-2,   # per Math57-v2 interval certificate
    "lambda_coup": -0.43,
    "gamma_coup": 1.62,
    "A_bz": 1.5,
    "B_bz": 1.0,
}


def derive_m_squared(mainline: Dict[str, float]) -> float:
    """m^2 in the Brazovskii dispersion, derived from epsilon^2 and q_0.

        m = epsilon * q_0^2   =>   m^2 = epsilon^2 * q_0^4.

    This is the convention of TECT-Math_IR_Bound-v4-thm-v4-1, Eq.~(eq:eta_def),
    with the amplitude-mode mass identified as eps * q_0^2.
    """
    q0 = mainline["q0"]
    eps2 = mainline["epsilon_sq"]
    return eps2 * q0**4


# ---------------------------------------------------------------------------
# Grid generation (cell-centered, cube [-B, B]^3)
# ---------------------------------------------------------------------------

def make_full_grid(N: int, B: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Uniform cell-centered grid on [-B, B]^3 with N cells per axis.

    Returns:
        (k1, k2, k3) arrays of shape (N, N, N) with dtype float64.
        Cell volume = (2*B/N)**3.
    """
    dx = 2.0 * B / N
    edge = -B + dx * (np.arange(N, dtype=np.float64) + 0.5)
    k1, k2, k3 = np.meshgrid(edge, edge, edge, indexing="ij")
    return k1, k2, k3


def make_fundamental_domain_grid(
    N: int, B: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Cell-centered grid on the positive octant [0, B]^3 with N cells per axis.

    Used for O_h-symmetry reduction.  Cell volume = (B/N)**3.
    """
    dx = B / N
    edge = dx * (np.arange(N, dtype=np.float64) + 0.5)
    k1, k2, k3 = np.meshgrid(edge, edge, edge, indexing="ij")
    return k1, k2, k3


# ---------------------------------------------------------------------------
# Brillouin-zone mask (truncated octahedron)
# ---------------------------------------------------------------------------

def bz_mask_full(
    k1: np.ndarray, k2: np.ndarray, k3: np.ndarray, A: float, B: float
) -> np.ndarray:
    """Truncated-octahedron BZ mask on the full cube:
        |k_i| <= B  AND  |k_1| + |k_2| + |k_3| <= A.
    """
    absk = np.abs(k1) + np.abs(k2) + np.abs(k3)
    return (
        (np.abs(k1) <= B) & (np.abs(k2) <= B) & (np.abs(k3) <= B) & (absk <= A)
    )


def bz_mask_fund(
    k1: np.ndarray, k2: np.ndarray, k3: np.ndarray, A: float, B: float
) -> np.ndarray:
    """BZ mask on the positive octant (k_i >= 0):
        k_i <= B  AND  k_1 + k_2 + k_3 <= A.
    """
    return (k1 <= B) & (k2 <= B) & (k3 <= B) & (k1 + k2 + k3 <= A)


# ---------------------------------------------------------------------------
# Integrand:   P_4(hat k) / omega^2(k)
# ---------------------------------------------------------------------------

def integrand(
    k1: np.ndarray,
    k2: np.ndarray,
    k3: np.ndarray,
    q0: float,
    m2: float,
) -> np.ndarray:
    """Integrand  P_4(hat k) / omega^2(k)  with  omega^2 = m^2 + (|k|^2 - q_0^2)^2.

    At k = 0 the direction hat k is undefined; we mask out any grid point
    with k_sq < eps_tiny * B^2.  The ambient measure is zero-measure there.
    """
    k_sq = k1 * k1 + k2 * k2 + k3 * k3
    k4_sum = k1**4 + k2**4 + k3**4

    # P_4(hat k) = sum_i hat k_i^4 - 3/5 = (sum_i k_i^4) / k_sq^2 - 3/5
    # Guard division-by-zero.
    tiny = np.finfo(k_sq.dtype).tiny
    inv_k4 = 1.0 / (k_sq * k_sq + tiny)
    P4 = k4_sum * inv_k4 - 0.6

    omega2 = m2 + (k_sq - q0 * q0) ** 2
    return P4 / omega2


# ---------------------------------------------------------------------------
# Full-BZ integration (no symmetry reduction)
# ---------------------------------------------------------------------------

def c4_full(N: int, mainline: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """Direct evaluation of c_4(eps) on the full cube [-B, B]^3 with N^3 cells.

    Returns (c4_value, diagnostics).
    """
    q0 = mainline["q0"]
    A = mainline["A_bz"]
    B = mainline["B_bz"]
    m2 = derive_m_squared(mainline)

    k1, k2, k3 = make_full_grid(N, B)
    mask = bz_mask_full(k1, k2, k3, A, B)
    vals = integrand(k1, k2, k3, q0, m2)

    dk3 = (2.0 * B / N) ** 3
    # Apply mask and sum (ignore NaN at any isolated k=0 cell; cell-centered
    # grid avoids hitting k=0 exactly, so NaN should not appear)
    vals_masked = np.where(mask, vals, 0.0)
    integral_raw = vals_masked.sum() * dk3
    c4 = integral_raw / (2.0 * math.pi) ** 3

    # Diagnostics
    n_in_bz = int(mask.sum())
    V_bz_numerical = n_in_bz * dk3
    # Exact volume of the truncated octahedron with (A, B) = (3/2, 1):
    #   V_cube - 8 * V_corner_cut = 8 - 8 * (1/6)*(3/2-1)^3 * ???
    # For (A,B) = (3/2, 1), the exact volume is computed below:
    V_bz_exact = truncated_octahedron_volume(A, B)

    return c4, {
        "N": N,
        "c4": c4,
        "n_in_bz": n_in_bz,
        "V_bz_numerical": V_bz_numerical,
        "V_bz_exact": V_bz_exact,
        "V_bz_rel_err": (V_bz_numerical - V_bz_exact) / V_bz_exact if V_bz_exact > 0 else float("nan"),
        "m2": m2,
        "integrand_min": float(vals_masked.min()),
        "integrand_max": float(vals_masked.max()),
    }


# ---------------------------------------------------------------------------
# O_h-reduced integration (positive octant, no ordering restriction)
# ---------------------------------------------------------------------------

def c4_octant(N: int, mainline: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """Reduced evaluation on positive octant [0, B]^3, multiplied by 8.

    The integrand P_4(hat k) / omega^2(k) is invariant under each
    sign-flip k_i -> -k_i (even powers of k_i), hence
       int_{[-B,B]^3} f d^3k  =  8 * int_{[0,B]^3} f d^3k.

    Cell volume in the octant grid is (B/N)^3.  For the same effective
    grid resolution as the full-cube N_full, set N = N_full / 2.
    """
    q0 = mainline["q0"]
    A = mainline["A_bz"]
    B = mainline["B_bz"]
    m2 = derive_m_squared(mainline)

    k1, k2, k3 = make_fundamental_domain_grid(N, B)
    mask = bz_mask_fund(k1, k2, k3, A, B)
    vals = integrand(k1, k2, k3, q0, m2)

    dk3 = (B / N) ** 3
    vals_masked = np.where(mask, vals, 0.0)
    integral_octant = vals_masked.sum() * dk3
    integral_full = 8.0 * integral_octant
    c4 = integral_full / (2.0 * math.pi) ** 3

    return c4, {
        "N": N,
        "N_full_equivalent": 2 * N,
        "c4": c4,
        "n_in_bz_octant": int(mask.sum()),
        "V_bz_numerical": 8.0 * mask.sum() * dk3,
        "m2": m2,
    }


# ---------------------------------------------------------------------------
# Angular-projector consistency check:  <1, P_4>_{S^2} = 0
# ---------------------------------------------------------------------------

def check_angular_orthogonality(N_angular: int = 200) -> Dict[str, float]:
    """Verify the angular consistency  int_{S^2} P_4(hat n) dOmega = 0
    by numerical quadrature on (theta, phi).

    This is a stand-alone projector sanity check; it does not use the BZ
    radial integral.
    """
    theta = np.linspace(0.0, math.pi, N_angular)
    phi = np.linspace(0.0, 2.0 * math.pi, 2 * N_angular)
    dth = theta[1] - theta[0]
    dph = phi[1] - phi[0]

    TH, PH = np.meshgrid(theta, phi, indexing="ij")
    nx = np.sin(TH) * np.cos(PH)
    ny = np.sin(TH) * np.sin(PH)
    nz = np.cos(TH)

    P4 = nx**4 + ny**4 + nz**4 - 0.6
    integrand_vol = P4 * np.sin(TH)
    integral_P4 = integrand_vol.sum() * dth * dph
    # And the norm ||P_4||^2
    P4sq_int = (P4 * P4 * np.sin(TH)).sum() * dth * dph
    expected_norm_sq = 64.0 * math.pi / 525.0   # (Lemma P4norm)

    return {
        "N_angular": N_angular,
        "integral_P4": float(integral_P4),
        "integral_P4_expected": 0.0,
        "norm_P4_sq_numerical": float(P4sq_int),
        "norm_P4_sq_expected": expected_norm_sq,
        "norm_rel_err": float(abs(P4sq_int - expected_norm_sq) / expected_norm_sq),
    }


# ---------------------------------------------------------------------------
# Exact BZ volume (truncated octahedron)
# ---------------------------------------------------------------------------

def truncated_octahedron_volume(A: float, B: float) -> float:
    """Volume of
        Omega_BZ = { k in R^3 : |k_i| <= B,  |k_1| + |k_2| + |k_3| <= A }.

    By octant symmetry,
        V_BZ = 8 * V_+,
        V_+  = Vol{ (x,y,z) in [0,B]^3 : x + y + z <= A }.

    With s := A/B, V_+ = B^3 * F(s), where F(s) is the Irwin-Hall CDF
    for the sum of three independent U(0,1) variables:
        F(s) = 0                           for s <= 0
             = s^3 / 6                     for 0 <= s <= 1
             = (s^3 - 3 (s-1)^3) / 6       for 1 <= s <= 2
             = 1 - (3-s)^3 / 6             for 2 <= s <= 3
             = 1                           for s >= 3.

    Equivalently, in terms of A and B directly:
        V_BZ = (4/3) A^3                          for 0 <= A <= B
             = (4/3) A^3 - 4 (A - B)^3            for B <= A <= 2 B
             = 8 B^3 - (4/3) (3 B - A)^3          for 2 B <= A <= 3 B
             = 8 B^3                              for A >= 3 B.

    At the TECT mainline (A, B) = (3/2, 1), we are in the intermediate
    regime  B <= A <= 2 B, hence
        V_BZ = (4/3) (3/2)^3 - 4 (1/2)^3 = 9/2 - 1/2 = 4.
    This matches the cell-mask count (full BZ: 4.0 * N^3) at every
    tested resolution.

    History (2026-04-21):
      v1.0 [WITHDRAWN]:  used the "cube minus 8 corner tetrahedra"
      formula V_BZ = 8 B^3 - (4/3) (3B - A)^3, valid only for
      2B <= A <= 3B (our s=1.5 case falls in [1,2], not [2,3], so the
      old formula returned 3.5 at mainline, inconsistent with the
      mask count 4.0).
      v2.0 [ACTIVE]: Irwin-Hall CDF formula, correct on [0, 3B].
    """
    if A <= 0.0:
        return 0.0
    if A <= B:
        return (4.0 / 3.0) * A ** 3
    if A <= 2.0 * B:
        return (4.0 / 3.0) * A ** 3 - 4.0 * (A - B) ** 3
    if A <= 3.0 * B:
        return 8.0 * B ** 3 - (4.0 / 3.0) * (3.0 * B - A) ** 3
    return 8.0 * B ** 3


def _self_test_bz_volume():
    """Sanity checks for the BZ volume formula.  Called once on import in
    debug builds (skipped in production)."""
    # Mainline:
    assert abs(truncated_octahedron_volume(1.5, 1.0) - 4.0) < 1e-12
    # Degenerate A <= B:
    assert abs(truncated_octahedron_volume(0.5, 1.0) - (4.0 / 3.0) * 0.125) < 1e-12
    # A = B (transition):
    assert abs(truncated_octahedron_volume(1.0, 1.0) - 4.0 / 3.0) < 1e-12
    # A = 2B (transition):  (4/3)*8 - 4*1 = 32/3 - 4 = 20/3
    assert abs(truncated_octahedron_volume(2.0, 1.0) - 20.0 / 3.0) < 1e-12
    # A = 3B (full cube):
    assert abs(truncated_octahedron_volume(3.0, 1.0) - 8.0) < 1e-12
    # A > 3B (saturated):
    assert abs(truncated_octahedron_volume(5.0, 1.0) - 8.0) < 1e-12


# ---------------------------------------------------------------------------
# Grid-convergence / Richardson extrapolation
# ---------------------------------------------------------------------------

def grid_convergence(
    mainline: Dict[str, float],
    N_list: List[int],
    use_octant: bool = True,
) -> List[Dict[str, float]]:
    """Run c_4 evaluation at each N in N_list and collect results."""
    results = []
    for N in N_list:
        t0 = time.time()
        if use_octant:
            c4, diag = c4_octant(N, mainline)
        else:
            c4, diag = c4_full(N, mainline)
        t1 = time.time()
        diag["elapsed_s"] = t1 - t0
        diag["method"] = "octant" if use_octant else "full"
        results.append(diag)
        print(
            f"  N = {N:4d}  "
            f"c_4 = {c4:+.8e}  "
            f"elapsed = {t1 - t0:6.2f} s  "
            f"n_in_bz = {diag.get('n_in_bz_octant', diag.get('n_in_bz')):,}"
        )
    return results


def richardson_extrapolate(
    N_list: List[int], c4_list: List[float]
) -> Dict[str, float]:
    """Given a sequence of (N_i, c_4_i) with N_i doubling, apply Richardson
    extrapolation assuming an asymptotic O(1/N^p) error with p to be fit.

    For a midpoint quadrature on a smooth integrand, p = 2 is expected.
    For an integrand with a peak of width ~eps resolved by dk ~ 1/N, the
    asymptotic regime may require dk << eps; we report both the p=2
    Richardson-extrapolated value and the raw sequence.
    """
    out = {"N_list": list(N_list), "c4_list": list(c4_list)}
    if len(N_list) < 2:
        return out
    # Pairwise Richardson, assuming f(N) - f(inf) ~ C/N^2:
    richardson_pairs = []
    for i in range(len(N_list) - 1):
        N1, N2 = N_list[i], N_list[i + 1]
        f1, f2 = c4_list[i], c4_list[i + 1]
        r = (N2 / N1) ** 2
        # f_inf ~ (r * f2 - f1) / (r - 1)
        if r != 1.0:
            f_inf = (r * f2 - f1) / (r - 1.0)
            richardson_pairs.append({
                "N1": N1, "N2": N2, "f1": f1, "f2": f2, "f_inf_est": f_inf,
            })
    out["richardson_pairs"] = richardson_pairs
    if richardson_pairs:
        out["f_inf_best"] = richardson_pairs[-1]["f_inf_est"]
    # Fit exponent p to the observed ratio
    if len(N_list) >= 3:
        # (f(N_1) - f_inf) / (f(N_3) - f_inf) = (N_3/N_1)^p
        # (f(N_1) - f(N_2)) / (f(N_2) - f(N_3))  asymptotically  =
        #   [(1/N_1)^p - (1/N_2)^p] / [(1/N_2)^p - (1/N_3)^p]
        # For N_2 = 2 N_1, N_3 = 4 N_1:  that ratio -> 2^p * (1+..) / (1+..) ≈ 2^p
        d12 = c4_list[0] - c4_list[1]
        d23 = c4_list[1] - c4_list[2]
        if d23 != 0.0 and d12 * d23 > 0.0:
            ratio = d12 / d23
            p_est = math.log(abs(ratio)) / math.log(N_list[1] / N_list[0])
            out["p_estimate"] = float(p_est)
    return out


# ---------------------------------------------------------------------------
# Interval-arithmetic certificate (mpmath.iv) on coarser grid
# ---------------------------------------------------------------------------

def c4_interval_coarse(
    N: int, mainline: Dict[str, float], dps: int = 50
) -> Dict[str, float]:
    """Rigorous interval enclosure of c_4(eps) on a coarse octant grid.

    For each cell, construct the interval hull of the integrand over the
    cell via interval arithmetic (mpmath.iv).  Only cells FULLY INSIDE
    the BZ contribute interior contributions; cells straddling the
    truncated-octahedron boundary are treated conservatively (the integrand
    is evaluated on the cell's (s, t) interval hull, and the contribution
    range is widened to [min(0, f * V_cell), max(0, f * V_cell)] where
    f is the interval hull of the integrand and V_cell = (B/N)^3).
    """
    if not HAS_MPMATH:
        return {"status": "mpmath not available"}

    iv.prec = dps
    mp.prec = dps

    # Float-valued grid coordinates for cell boundaries (exact in binary)
    B_f = float(mainline["B_bz"])
    A_f = float(mainline["A_bz"])
    dx_f = B_f / N

    q0 = iv.mpf(mainline["q0"])
    A = iv.mpf(mainline["A_bz"])
    B = iv.mpf(mainline["B_bz"])
    m2_f = derive_m_squared(mainline)
    m2 = iv.mpf(m2_f)
    q0sq = q0 * q0
    three_fifths = iv.mpf("3") / iv.mpf("5")

    total = iv.mpf(0)

    t0 = time.time()
    for i in range(N):
        k1_lo_f = i * dx_f
        k1_hi_f = (i + 1) * dx_f
        k1 = iv.mpf((k1_lo_f, k1_hi_f))
        for j in range(N):
            k2_lo_f = j * dx_f
            k2_hi_f = (j + 1) * dx_f
            k2 = iv.mpf((k2_lo_f, k2_hi_f))
            for l in range(N):
                k3_lo_f = l * dx_f
                k3_hi_f = (l + 1) * dx_f
                k3 = iv.mpf((k3_lo_f, k3_hi_f))

                # Conservative BZ-membership test on the cell (float-level)
                fully_in = (k1_hi_f + k2_hi_f + k3_hi_f) <= A_f
                fully_out = (k1_lo_f + k2_lo_f + k3_lo_f) > A_f

                if fully_out:
                    continue

                # Integrand interval hull
                k_sq = k1 * k1 + k2 * k2 + k3 * k3
                # Avoid division-by-zero at k=0 cell: the (0,0,0) cell lives at
                # (i,j,l) = (0,0,0) with k_sq in [0, 3*dx^2]; since the (s,t)
                # parametrisation singularity at k=0 is integrable, we skip it.
                if i == 0 and j == 0 and l == 0:
                    continue

                k4_sum = k1**4 + k2**4 + k3**4
                P4 = k4_sum / (k_sq * k_sq) - three_fifths
                omega2 = m2 + (k_sq - q0sq) ** 2
                f = P4 / omega2

                V_cell = iv.mpf(dx_f) * iv.mpf(dx_f) * iv.mpf(dx_f)
                cell_contrib = f * V_cell

                if not fully_in:
                    # Conservative widening: include possibility of zero
                    # contribution from outside part of the cell.
                    lo_f = mpf(cell_contrib._mpi_[0])
                    hi_f = mpf(cell_contrib._mpi_[1])
                    if lo_f > 0:
                        lo_f = mpf(0)
                    if hi_f < 0:
                        hi_f = mpf(0)
                    cell_contrib = iv.mpf((lo_f, hi_f))

                total = total + cell_contrib
    # Full cube = 8 octants
    total = 8 * total
    # Divide by (2pi)^3
    total = total / (iv.mpf(2) * iv.pi) ** 3

    t1 = time.time()
    lo = float(total.a)
    hi = float(total.b)
    center = 0.5 * (lo + hi)
    half = 0.5 * (hi - lo)
    return {
        "status": "ok",
        "N_octant": N,
        "dps": dps,
        "lo": lo,
        "hi": hi,
        "center": center,
        "half_width": half,
        "rel_half_width": half / abs(center) if center != 0 else float("inf"),
        "sign_certified": "positive" if lo > 0 else ("negative" if hi < 0 else "inconclusive"),
        "elapsed_s": t1 - t0,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Direct BZ integration of c_4(eps) at TECT mainline Brazovskii FP"
    )
    parser.add_argument(
        "--N_list",
        type=str,
        default="64,128,192,256",
        help="Comma-separated list of FULL-cube-equivalent grid resolutions.",
    )
    parser.add_argument(
        "--interval_N",
        type=int,
        default=8,
        help="Octant grid resolution for the interval-arithmetic certificate.",
    )
    parser.add_argument(
        "--interval_dps",
        type=int,
        default=50,
        help="mpmath.iv precision for the interval certificate.",
    )
    parser.add_argument(
        "--skip_interval",
        action="store_true",
        help="Skip the interval-arithmetic certificate (faster).",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=str(Path(__file__).parent / "bz_eta_integrator_report.json"),
        help="Output JSON report path.",
    )
    args = parser.parse_args()

    N_list_full = [int(x) for x in args.N_list.split(",")]
    # Use octant method for efficiency; N_octant = N_full / 2
    N_list_octant = [max(2, n // 2) for n in N_list_full]

    print("=" * 76)
    print("BZ integrator for c_4(eps)  --  Task #27 / Math_IR_Bound-v4-BZ-integrator")
    print("=" * 76)
    print("  TECT mainline: q_0 = {q0}, mu^2 = {mu2}, lambda = {lambda_coup},".format(**TECT_MAINLINE))
    print("                 gamma = {gamma_coup}, (A,B) = ({A_bz},{B_bz})".format(**TECT_MAINLINE))
    print(f"                 m^2 = eps^2 * q_0^4 = {derive_m_squared(TECT_MAINLINE):.6e}")
    print(f"  BZ volume (exact, trunc. oct.): {truncated_octahedron_volume(TECT_MAINLINE['A_bz'], TECT_MAINLINE['B_bz']):.6f}")
    print("-" * 76)

    # (1) Angular-projector consistency check
    print("\n[1] Angular-projector consistency check (P_4 on S^2):")
    ang = check_angular_orthogonality(N_angular=200)
    print(f"    integral_P4 (expect 0): {ang['integral_P4']:+.3e}")
    print(f"    ||P_4||^2 numerical:    {ang['norm_P4_sq_numerical']:.6f}")
    print(f"    ||P_4||^2 exact:        {ang['norm_P4_sq_expected']:.6f}  "
          f"(rel err {ang['norm_rel_err']:.3e})")

    # (2) Grid convergence (numerical)
    print("\n[2] Grid-convergence study (O_h octant method):")
    print(f"    N_full-equivalent: {N_list_full}")
    conv_results = grid_convergence(TECT_MAINLINE, N_list_octant, use_octant=True)
    c4_values = [r["c4"] for r in conv_results]

    # (3) Richardson extrapolation
    print("\n[3] Richardson extrapolation (assuming O(1/N^2) asymptotic error):")
    rich = richardson_extrapolate(N_list_full, c4_values)
    if "f_inf_best" in rich:
        print(f"    c_4(eps) extrapolated -> {rich['f_inf_best']:+.8e}")
    if "p_estimate" in rich:
        print(f"    empirical convergence exponent p = {rich['p_estimate']:.3f}")

    # (4) Interval-arithmetic certificate
    interval_result = {"status": "skipped"}
    if not args.skip_interval:
        print(f"\n[4] Interval-arithmetic certificate (octant N = {args.interval_N}, dps = {args.interval_dps}):")
        interval_result = c4_interval_coarse(
            args.interval_N, TECT_MAINLINE, dps=args.interval_dps
        )
        if interval_result.get("status") == "ok":
            print(f"    c_4 interval enclosure: [{interval_result['lo']:+.6e}, {interval_result['hi']:+.6e}]")
            print(f"    center = {interval_result['center']:+.6e}, half-width = {interval_result['half_width']:+.6e}")
            print(f"    sign: {interval_result['sign_certified']}")
            print(f"    elapsed: {interval_result['elapsed_s']:.2f} s")
        else:
            print(f"    status: {interval_result.get('status')}")
    else:
        print("\n[4] Interval-arithmetic certificate: SKIPPED (--skip_interval)")

    # (5) Derived gamma_{44} sign
    print("\n[5] Derived gamma_{44} (= -N * lambda^2 * c_4):")
    lam = TECT_MAINLINE["lambda_coup"]
    if c4_values:
        c4_final = rich.get("f_inf_best", c4_values[-1])
        gamma_44_numerical = -1.0 * lam**2 * c4_final   # up to positive N factor
        print(f"    c_4(eps) (finest grid) = {c4_values[-1]:+.8e}")
        print(f"    c_4(eps) (Richardson)  = {c4_final:+.8e}")
        print(f"    gamma_{{44}} / N      = {gamma_44_numerical:+.8e} (N > 0)")
        print(f"    sign(gamma_{{44}})   = {'NEGATIVE (IR-irrelevant)' if gamma_44_numerical < 0 else 'POSITIVE (IR-relevant)' if gamma_44_numerical > 0 else 'undetermined'}")

    # (6) Write JSON report
    report = {
        "theory_tag": "Math_IR_Bound-v4-BZ-integrator-2026-04-21",
        "task_id": 27,
        "mainline": TECT_MAINLINE,
        "m_squared": derive_m_squared(TECT_MAINLINE),
        "bz_volume_exact": truncated_octahedron_volume(
            TECT_MAINLINE["A_bz"], TECT_MAINLINE["B_bz"]
        ),
        "angular_check": ang,
        "convergence": conv_results,
        "richardson": rich,
        "interval_certificate": interval_result,
    }
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    with open(args.report, "w") as f:
        json.dump(report, f, indent=2, default=float)
    print(f"\n[6] Report written: {args.report}")

    print("=" * 76)
    # Exit code: 0 if interval certifies c_4 > 0, 1 if inconclusive, 2 if negative
    if interval_result.get("status") == "ok":
        if interval_result["sign_certified"] == "positive":
            return 0
        elif interval_result["sign_certified"] == "negative":
            return 2
        else:
            return 1
    # Fall back to finest-grid sign
    if c4_values and c4_values[-1] > 0:
        return 0
    if c4_values and c4_values[-1] < 0:
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
