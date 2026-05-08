# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v2.4.0
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
"""
PDE/v24_thresholds.py
=====================

Theorem-anchored v2.4 Phase-0 / Phase-2.5 gate thresholds and the
class-II Newton-step guard for the TECT Newton-Krylov proof protocol.

All public symbols here correspond 1:1 to the derivations in

    Docs/math/TECT-Math56-Addendum.tex.txt

with section references printed in-docstring.  Do not hard-code any
threshold value elsewhere in PDE/ or tools/ -- import from this module
instead.  The SymPy audit script
Docs/supplementary/v24_threshold_sympy_check.py regenerates the
numerical tables and can be run before any code change.

Version: v2.4.0  (2026-04-20)
Depends on: numpy; torch (only inside torch-aware helpers, lazily imported).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, Tuple

import numpy as np

__all__ = [
    "V24_MU2_TARGET_DEFAULT",
    "V24_G0_CUSHION",
    "V24_G2_MIN",
    "V24_G3_REL",
    "V24_NEWTON_TOL",
    "V24_RHO_STAR_FACTOR",
    "BrazovskiiParams",
    "SeparatrixReport",
    "brazovskii_critical_mu2",
    "v24_separatrix_thresholds",
    "v24_recommended_rho_star",
    "v24_phase0_statistic",
    "v24_phase0_gate",
    "v24_class2_guard",
    "v24_phase25_overlap",
    "v24_phase25_residual_rel",
    "v24_phase25_gate",
    "v24_banner",
]


# ---------------------------------------------------------------------------
# Constants (all derived, not heuristic; see Math56-Addendum §G summary)
# ---------------------------------------------------------------------------

#: Recommended continuation end-point mu^2.  Corollary 1 of Math56-Addendum
#: guarantees existence of a BCC extremum at mu^2 < r_c^{global}.  The
#: recommended 5e-3 sits at 0.44 * r_c^{global} (λ=-0.43, γ=1.62).
V24_MU2_TARGET_DEFAULT: float = 5.0e-3

#: Finite-N cushion added on top of the raw separatrix threshold.  Phenomenological;
#: 5% absorbs projector-loss + RMS fluctuation at N=32 (O(1/N) contribution).
V24_G0_CUSHION: float = 5.0e-2

#: Minimum cross-grid Ritz-eigenvector overlap.  Theorem 4 (Rayleigh-Ritz
#: perturbation): 0.90 corresponds to 20% fractional eigenvector error budget.
V24_G2_MIN: float = 0.90

#: Relative Saad bound constant.  Theorem 5: ||r|| <= V24_G3_REL * lam_Ritz
#: at 1% relative precision (diagonal-dominant case).
V24_G3_REL: float = 1.0e-1

#: Default Newton residual tolerance used for rho_* dimensional bookkeeping.
V24_NEWTON_TOL: float = 1.0e-9

#: Fraction of phi_+^2 at which the class-II abort fires (Theorem 3).  At
#: mu^2_target=5e-3, V24_RHO_STAR_FACTOR * phi_+^2 = 6.44e-5.
V24_RHO_STAR_FACTOR: float = 1.0e-3


# ---------------------------------------------------------------------------
# Reduced potential and critical scales (§1 of Math56-Addendum)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BrazovskiiParams:
    """Reduced BCC-moment potential parameters.

    F(phi) = mu2 * phi^2 + lam * phi^4 + (5/2) * gam * phi^6

    with K_4 = 1, K_6 = 5/2 (Leibler-Wickham BCC first-shell enumeration;
    Math37-AddA §A.2: N_4^{BCC}=144, N_6^{BCC}=4320).
    """

    lam: float
    gam: float
    K6: float = 5.0 / 2.0  # retained so unit tests can override

    def __post_init__(self) -> None:
        if self.gam <= 0:
            raise ValueError("BrazovskiiParams requires gam > 0 (Brazovskii regime).")
        if self.lam >= 0:
            raise ValueError("BrazovskiiParams requires lam < 0 (attractive quartic).")


def brazovskii_critical_mu2(p: BrazovskiiParams) -> Tuple[float, float]:
    """Return (r_c^global, r_c^meta) = (lam^2 / (10 gam), 2 lam^2 / (15 gam)).

    Math56-Addendum eqs. (1.3)-(1.4): r_c^{global} is the first-order
    transition, r_c^{meta} is the metastability edge (above which the
    potential has no non-trivial real extremum).
    """
    r_global = p.lam * p.lam / (10.0 * p.gam)
    r_meta = 2.0 * p.lam * p.lam / (15.0 * p.gam)
    return r_global, r_meta


# ---------------------------------------------------------------------------
# Separatrix / Phase-0 threshold (§B, Theorem 2)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SeparatrixReport:
    mu2_target: float
    phi_plus: float
    phi_minus: float
    alpha_sep: float
    G0_raw: float
    G0_op: float
    phi_plus_sq: float
    rho_star: float
    r_c_global: float
    r_c_meta: float

    def as_dict(self) -> Dict[str, float]:
        return asdict(self)


def v24_separatrix_thresholds(
    mu2_target: float,
    p: BrazovskiiParams,
    cushion: float = V24_G0_CUSHION,
    rho_star_factor: float = V24_RHO_STAR_FACTOR,
) -> SeparatrixReport:
    """Compute (phi_+, phi_-, alpha_sep, G0) from Theorem 2 and rho_* from Theorem 3.

    Raises
    ------
    ValueError
        If mu2_target > r_c^meta (no real BCC extremum exists).  This is
        the Math56-Addendum Corollary 1 precondition; the function refuses
        to return otherwise-meaningless thresholds.
    """
    r_global, r_meta = brazovskii_critical_mu2(p)

    R = 4.0 * p.lam * p.lam - 30.0 * p.gam * mu2_target
    if R < 0.0:
        raise ValueError(
            "v2.4 precondition failed: "
            f"mu2_target={mu2_target:.4e} > r_c^meta={r_meta:.4e} "
            f"(2*lam^2/(15*gam)). "
            "No real BCC extremum exists; refuse to start continuation."
        )

    sqrtR = math.sqrt(R)
    x_plus = (-2.0 * p.lam + sqrtR) / (15.0 * p.gam)
    x_minus = (-2.0 * p.lam - sqrtR) / (15.0 * p.gam)

    # x_minus can round negative by O(1e-18) near r_meta; clamp.
    if x_minus < 0.0:
        x_minus = 0.0

    phi_plus = math.sqrt(x_plus)
    phi_minus = math.sqrt(x_minus)
    alpha_sep = phi_minus / phi_plus if phi_plus > 0 else 0.0

    G0_raw = 0.5 * (1.0 + alpha_sep)
    G0_op = G0_raw + cushion

    rho_star = rho_star_factor * x_plus

    return SeparatrixReport(
        mu2_target=mu2_target,
        phi_plus=phi_plus,
        phi_minus=phi_minus,
        alpha_sep=alpha_sep,
        G0_raw=G0_raw,
        G0_op=G0_op,
        phi_plus_sq=x_plus,
        rho_star=rho_star,
        r_c_global=r_global,
        r_c_meta=r_meta,
    )


def v24_recommended_rho_star(mu2_target: float, p: BrazovskiiParams) -> float:
    """Standalone accessor.  Equivalent to v24_separatrix_thresholds(...).rho_star."""
    return v24_separatrix_thresholds(mu2_target, p).rho_star


# ---------------------------------------------------------------------------
# Phase-0 gate (vacuum escape)
# ---------------------------------------------------------------------------

def v24_phase0_statistic(
    psi_abs_sq_mean: float,
    phi_plus: float,
) -> float:
    """Return V = ||Psi||_RMS / phi_+ given an already-computed <|Psi|^2>.

    Passing in the mean (rather than the tensor) keeps this helper
    framework-agnostic; torch callers should pass
    ``(psi.abs()**2).mean().item()``.
    """
    if phi_plus <= 0:
        raise ValueError("phi_plus must be positive.")
    rms = math.sqrt(max(psi_abs_sq_mean, 0.0))
    return rms / phi_plus


def v24_phase0_gate(
    psi_abs_sq_mean: float,
    separatrix: SeparatrixReport,
    logger: Optional[Any] = None,
) -> Dict[str, Any]:
    """Enforce Theorem 2 (vacuum-escape past the Brazovskii separatrix).

    Parameters
    ----------
    psi_abs_sq_mean : float
        Lattice mean of |Psi|^2 at the candidate solver state.
    separatrix : SeparatrixReport
        Output of ``v24_separatrix_thresholds``.
    logger : optional
        Object with ``.info(str)``; e.g. a ``logging.Logger`` or any
        duck-typed shim.  If ``None``, nothing is logged.

    Returns
    -------
    dict with V, G0_op, passed, margin.  Caller is responsible for
    abort semantics; this function does not raise.
    """
    V = v24_phase0_statistic(psi_abs_sq_mean, separatrix.phi_plus)
    passed = V >= separatrix.G0_op
    margin = V - separatrix.G0_op
    if logger is not None:
        try:
            logger.info(
                "[v2.4 Phase-0] V = ||Psi||_RMS / phi_+ = "
                f"{V:.4f}  G0_op = {separatrix.G0_op:.4f}  "
                f"{'PASS' if passed else 'FAIL'}  (margin {margin:+.4f})"
            )
        except Exception:  # never let logging break the solver
            pass
    return {
        "V": V,
        "G0_op": separatrix.G0_op,
        "passed": passed,
        "margin": margin,
        "phi_plus": separatrix.phi_plus,
    }


# ---------------------------------------------------------------------------
# Class-II abort guard (Theorem 3)
# ---------------------------------------------------------------------------

def v24_class2_guard(
    rho_min_value: float,
    separatrix: SeparatrixReport,
    logger: Optional[Any] = None,
) -> None:
    """Raise if rho has dropped below the theorem-anchored abort floor.

    Parameters
    ----------
    rho_min_value : float
        Lattice min of rho at the current Newton iterate (torch callers
        should pass ``rho.min().item()``).
    separatrix : SeparatrixReport
        Supplies ``rho_star`` derived in Theorem 3.

    Raises
    ------
    RuntimeError
        If ``rho_min_value < separatrix.rho_star``.  Caller must either
        halve the step and retry (continuation) or abort with a diagnostic
        (Newton-Krylov at fixed mu^2).
    """
    if rho_min_value < separatrix.rho_star:
        msg = (
            f"[v2.4 Class-II abort] min(rho) = {rho_min_value:.4e} "
            f"< rho_* = {separatrix.rho_star:.4e} "
            f"(= {V24_RHO_STAR_FACTOR:.0e} * phi_+^2). "
            "Solver is drifting into the regularised-quotient singularity; "
            "halve continuation step or pick a deeper mu^2_target."
        )
        if logger is not None:
            try:
                logger.warning(msg)
            except Exception:
                pass
        raise RuntimeError(msg)


# ---------------------------------------------------------------------------
# Phase-2.5 gate: G2 cross-grid overlap (Theorem 4), G3 Saad residual (Theorem 5)
# ---------------------------------------------------------------------------

def v24_phase25_overlap(
    v_interp_N_to_2N: np.ndarray,
    v_2N: np.ndarray,
) -> float:
    """Return |<I_N^{2N} v_N | v_2N>| between unit-norm vectors.

    Both inputs must already be unit-normalised on the 2N grid; the caller
    is responsible for the zero-pad spectral interpolation
    (``Docs/math/TECT-Math56-Addendum.tex.txt`` §D).  Works with complex
    or real arrays.
    """
    a = np.asarray(v_interp_N_to_2N)
    b = np.asarray(v_2N)
    if a.shape != b.shape:
        raise ValueError(f"Shape mismatch: {a.shape} vs {b.shape}")
    inner = np.vdot(a, b)
    return float(np.abs(inner))


def v24_phase25_residual_rel(
    residual_norm: float,
    lam_ritz: float,
) -> Tuple[float, float]:
    """Return (bound, ratio) with bound = V24_G3_REL * |lam_ritz|.

    The Saad bound is interpreted as a *relative* bound; see Theorem 5.
    """
    if not math.isfinite(lam_ritz):
        raise ValueError("lam_ritz must be finite.")
    bound = V24_G3_REL * abs(lam_ritz)
    ratio = residual_norm / max(bound, 1e-300)
    return bound, ratio


def v24_phase25_gate(
    v_interp_N_to_2N: np.ndarray,
    v_2N: np.ndarray,
    lam_ritz: float,
    residual_norm: float,
    lam_small_floor: float = 1e-12,
) -> Dict[str, Any]:
    """Enforce G2 (cross-grid overlap) and G3 (Saad relative residual).

    Parameters
    ----------
    lam_small_floor : float
        Guards the edge case where ``lam_ritz`` is numerically zero or
        negative; in that case the G3 gate fails unconditionally since
        no meaningful relative bound can be formed.
    """
    overlap = v24_phase25_overlap(v_interp_N_to_2N, v_2N)
    g2_pass = overlap >= V24_G2_MIN

    if abs(lam_ritz) < lam_small_floor or lam_ritz <= 0.0:
        # Theorem 5 requires a strictly positive Ritz eigenvalue (mass-gap
        # interpretation).  A negative eigenvalue is an instability, NOT a
        # spectral gap, and must never certify as "admissible" even if the
        # residual is small.  Fail closed.
        g3_pass = False
        bound = 0.0
        ratio = float("inf")
    else:
        bound, ratio = v24_phase25_residual_rel(residual_norm, lam_ritz)
        g3_pass = residual_norm <= bound

    return {
        "G2_overlap": overlap,
        "G2_min": V24_G2_MIN,
        "G2_pass": bool(g2_pass),
        "G3_residual": residual_norm,
        "G3_bound_rel": bound,
        "G3_ratio": ratio,
        "G3_pass": bool(g3_pass),
        "overall_pass": bool(g2_pass and g3_pass),
    }


# ---------------------------------------------------------------------------
# Banner / diagnostic printer
# ---------------------------------------------------------------------------

def v24_banner(
    mu2_target: float = V24_MU2_TARGET_DEFAULT,
    lam: float = -0.43,
    gam: float = 1.62,
) -> str:
    """Return a multi-line banner tabulating the current v2.4 thresholds.

    Solver / continuation drivers should print this once at startup.
    """
    p = BrazovskiiParams(lam=lam, gam=gam)
    sep = v24_separatrix_thresholds(mu2_target, p)
    lines = [
        "=" * 72,
        "  TECT Newton-Krylov v2.4 (theorem-anchored thresholds)",
        "  Reference: Docs/math/TECT-Math56-Addendum.tex.txt",
        "=" * 72,
        f"  Brazovskii: lam={lam:+.4f}, gam={gam:+.4f}, K_6=5/2",
        f"  r_c^global = lam^2/(10 gam)     = {sep.r_c_global:.6f}",
        f"  r_c^meta   = 2 lam^2/(15 gam)   = {sep.r_c_meta:.6f}",
        f"  mu^2_target                     = {mu2_target:.4e}",
        "  --- Phase-0 separatrix (Theorem 2) ---",
        f"  phi_+                           = {sep.phi_plus:.4f}",
        f"  phi_-                           = {sep.phi_minus:.4f}",
        f"  alpha_sep = phi_-/phi_+         = {sep.alpha_sep:.4f}",
        f"  G0_raw    = (1+alpha_sep)/2     = {sep.G0_raw:.4f}",
        f"  G0_op     = G0_raw + cushion    = {sep.G0_op:.4f}  (cushion={V24_G0_CUSHION:.3f})",
        "  --- Class-II abort (Theorem 3) ---",
        f"  rho_*     = {V24_RHO_STAR_FACTOR:.0e} * phi_+^2   = {sep.rho_star:.3e}",
        "  --- Phase-2.5 gate (Theorems 4, 5) ---",
        f"  G2_min    (cross-grid overlap)  = {V24_G2_MIN:.4f}",
        f"  G3_rel    (||r|| / lam_ritz)    = {V24_G3_REL:.4e}  (relative)",
        "=" * 72,
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module self-test (run: python -m PDE.v24_thresholds)
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    print(v24_banner())
    # Sanity: locked-parameter precondition must fail.
    try:
        v24_separatrix_thresholds(0.26, BrazovskiiParams(lam=-0.43, gam=1.62))
    except ValueError as exc:
        print(f"\n[self-test] locked mu^2=0.26 correctly rejected: {exc}")
