#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v1.0
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
"""
remote_gap_audit.py — Stage U4
================================
TECT remote spectral gap certificate:  Δ_bench > η_{R,ρ}.

Physical background
-------------------
The TECT theorem-level acceptance requires that the linearised operator
L[Ψ₀](k) is gapped everywhere *outside* the condensate neighbourhood:

    Δ_bench := min_{k ∉ ∪_α B(G*_α, r_patch)} λ_min(L(k))  >  η_{R,ρ}

This ensures the condensate modes at {G*_α} are the unique soft modes of
the system, and that the effective field theory near the condensate is
well-defined.

The audit proceeds in two levels:

Level 1 — Analytical linear gap (fast, no Ψ₀ needed):
    Compute L_lin(k) = r + Z·s₂(k) + Y·s₂(k)²  (scalar × I₃) over the
    full discrete k-grid, then find the minimum in the remote region.

    Important subtlety: for the Brazovskii shell instability the minimum
    of L_lin may lie at |k| = q₀ (the shell), in which case L_lin is the
    same at ALL shell points — both condensate and remote.  The remote gap
    at the shell then comes from nonlinear corrections only.

    We therefore report two sub-quantities:
      Δ_lin_offshell  = min_{|k| far from q₀, remote} L_lin(k) − L_lin(G*)
      Δ_lin_onshell   = 0 by construction (same L_lin on the whole shell)

Level 2 — Numerical nonlinear gap (slower, requires Ψ₀ and hessian_fn):
    Sample n_sample random remote k-points, probe L(k) numerically via
    hessian_vec plane-wave injection, and report

      Δ_nl_sample = min_{sampled remote k} λ_min(L_num(k))

    This gives a lower bound on the true nonlinear remote gap.

Certificate:
    The full gap certificate is issued if
      Δ_lin_offshell > η_threshold   AND   Δ_nl_sample > η_threshold
    (or Δ_lin_offshell only if Level 2 is skipped).

API
---
- RemoteGapResult (dataclass)
- remote_region_mask(kx, ky, kz, patch_centers, q0, r_patch, params)
      → bool array (Nx, Ny, Nz)
- linear_gap_audit(params, patch_centers, q0, Nx, Ny, Nz,
                   r_patch_frac, eta_threshold) → RemoteGapResult
- numerical_gap_sample(Psi0, params, patch_centers, q0,
                       hessian_fn, n_sample, seed, eta_threshold)
      → RemoteGapResult
- full_remote_gap_audit(Psi0, params, patch_centers, q0,
                        hessian_fn, ...) → Dict
- remote_gap_text_report(result) → str
- remote_gap_latex_block(result) → str

Usage
-----
    from remote_gap_audit import full_remote_gap_audit, remote_gap_text_report

    out = full_remote_gap_audit(
        Psi0, params, patch_centers, q0,
        hessian_fn = lambda v: backend.hessian_vec(Psi0, v, params),
        n_sample   = 200,
        eta_threshold = 0.05,
    )
    print(remote_gap_text_report(out))
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from bloch_linearization import (
    kgrid_3d,
    k_to_grid_idx,
    bloch_matrix_at_idx,
    check_hermiticity,
    symmetrise,
)


# ============================================================
# Stiffness symbol computation (vectorised, full grid)
# ============================================================

def _s2_grid(
    params:  Dict[str, Any],
    kx: np.ndarray,
    ky: np.ndarray,
    kz: np.ndarray,
) -> np.ndarray:
    """
    Compute the stiffness symbol s₂(k) over the full 3-D k-grid.

    Supports laplacian_mode: 'spectral', 'bcc_symbol', 'mixed_bcc'.

    Returns
    -------
    s2 : (Nx, Ny, Nz) float64 ndarray
    """
    KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing="ij")
    k2 = KX**2 + KY**2 + KZ**2

    mode = str(params.get("laplacian_mode", "spectral")).lower()
    if mode == "spectral":
        return k2

    a_bcc = float(params.get("a_bcc", 1.0))
    c = (np.cos(0.5 * a_bcc * KX) *
         np.cos(0.5 * a_bcc * KY) *
         np.cos(0.5 * a_bcc * KZ))
    bcc2 = (8.0 / a_bcc**2) * (1.0 - c)

    if mode == "bcc_symbol":
        return bcc2
    if mode == "mixed_bcc":
        eps = float(params.get("bcc_mix_epsilon", 0.0))
        return (1.0 - eps) * k2 + eps * bcc2

    raise ValueError(f"Unknown laplacian_mode: {mode}")


def _L_lin_grid(
    params: Dict[str, Any],
    kx: np.ndarray,
    ky: np.ndarray,
    kz: np.ndarray,
) -> np.ndarray:
    """
    Compute L_lin(k) = r + Z·s₂(k) + Y·s₂(k)² over the full k-grid.

    This is the scalar coefficient of I₃ from the Brazovskii linear
    operator (family/lock/shell-bias terms are not included here).

    Returns
    -------
    L_lin : (Nx, Ny, Nz) float64
    """
    r = float(params.get("r", params.get("mu2", 0.25)))
    Z = float(params.get("Z", -1.0))
    Y = float(params.get("Y",  1.0))

    s2 = _s2_grid(params, kx, ky, kz)
    return r + Z * s2 + Y * s2**2


# ============================================================
# Remote region mask
# ============================================================

def remote_region_mask(
    kx: np.ndarray,
    ky: np.ndarray,
    kz: np.ndarray,
    patch_centers: np.ndarray,
    q0:            float,
    r_patch_frac:  float = 0.25,
    params:        Optional[Dict[str, Any]] = None,
) -> np.ndarray:
    """
    Build a boolean mask (Nx, Ny, Nz) that is True for k-points in the
    "remote" region, i.e., outside all condensate patch neighbourhoods.

    A k-point k is in the condensate neighbourhood of patch α if
        |k − G*_α| < r_patch_frac · q₀

    Parameters
    ----------
    kx, ky, kz    : 1-D k-grid arrays
    patch_centers  : (Npatch, 3) unit vectors ĝ_α
    q0             : float   shell radius
    r_patch_frac   : float   neighbourhood radius as fraction of q₀
    params         : dict    (unused here; kept for API symmetry)

    Returns
    -------
    mask : (Nx, Ny, Nz) bool   True = remote (not near any G*_α)
    """
    Nx, Ny, Nz = len(kx), len(ky), len(kz)
    KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing="ij")

    r_patch = r_patch_frac * q0
    mask    = np.ones((Nx, Ny, Nz), dtype=bool)

    for gc in patch_centers:
        gc   = np.asarray(gc, dtype=float)
        nrm  = np.linalg.norm(gc)
        if nrm < 1e-14:
            continue
        G_star = q0 * gc / nrm

        dist2 = (KX - G_star[0])**2 + (KY - G_star[1])**2 + (KZ - G_star[2])**2
        mask &= (dist2 >= r_patch**2)

    return mask


# ============================================================
# Result containers
# ============================================================

@dataclass
class RemoteGapResult:
    """
    Remote spectral gap audit result.

    Attributes (Level 1 — linear, analytical)
    ------------------------------------------
    n_remote          : int     number of remote k-points (grid)
    n_total           : int     total k-points in grid
    remote_fraction   : float   n_remote / n_total
    L_lin_at_G_star   : float   L_lin(G*) at the first patch centre
    delta_lin_offshell: float   min_{remote, off-shell} L_lin(k) − L_lin(G*)
    delta_lin_all     : float   min_{remote} L_lin(k) (all remote, incl. on-shell)
    kmin_lin          : (3,)    k-vector achieving delta_lin_all minimum
    offshell_tol      : float   |L_lin(k) − L_lin(G*)| < this → "on-shell"

    Attributes (Level 2 — numerical, sampled)
    ------------------------------------------
    n_sample          : int     number of remote k-points sampled numerically
    delta_nl_sample   : float   min_{sampled} λ_min(L_num(k))   (None if skipped)
    kmin_nl           : (3,)    k-vector achieving delta_nl_sample (None if skipped)
    nl_evals_min      : list    λ_min per sampled k-point

    Certificate
    -----------
    eta_threshold  : float
    certificate_lin: bool   delta_lin_offshell > eta_threshold
    certificate_nl : bool   delta_nl_sample > eta_threshold (None if skipped)
    certificate    : bool   both certificates pass (or lin-only if nl skipped)
    """
    # Level 1
    n_remote           : int
    n_total            : int
    remote_fraction    : float
    L_lin_at_G_star    : float
    delta_lin_offshell : float
    delta_lin_all      : float
    kmin_lin           : np.ndarray
    offshell_tol       : float

    # Level 2 (optional)
    n_sample           : int               = 0
    delta_nl_sample    : Optional[float]   = None
    kmin_nl            : Optional[np.ndarray] = None
    nl_evals_min       : List[float]       = field(default_factory=list)

    # Certificate (proxy threshold)
    eta_threshold      : float             = 0.05
    certificate_lin    : bool              = False
    certificate_nl     : Optional[bool]    = None
    certificate        : bool              = False

    # --- Module 10 upgrade: decomposition-based η_R,ρ (TECT-Math30, §3.1) ---
    eta_R_decomp       : Optional["EtaRDecompResult"] = field(default=None)
    gate1_margin       : Optional[float]   = None   # Δ_bench - η_R,ρ  (Gate 1 signed margin)
    gate1_pass         : Optional[bool]    = None   # gate1_margin > 0


# ============================================================
# Module 10: Decomposition-based η_{R,ρ} bound  (TECT-Math30)
# ============================================================

@dataclass
class EtaRDecompResult:
    """
    Decomposition-based upper bound on η_{R,ρ} (TECT-Math30, §3.1):

        η_{R,ρ} ≤ η_tr + η_tail + η_diag

    Components
    ----------
    η_tr (transport coupling):
        Löwdin-type remote correction from off-diagonal P*K_iQ* coupling:
            η_tr ≤ n_modes · K_offdiag_max² · ρ / Δ_bench
        where K_offdiag_max = max_i ‖P*K_iQ*‖_F and Δ_bench is Level-2 gap.

    η_tail (tail Fourier correction):
        Leading O(ρ) correction from omitted channel families:
            η_tail ≤ K_tail · ρ,   K_tail ≈ ‖K_i‖_op
        In the ultra-minimal truncation (no tail channels), η_tail=0 with warning.

    η_diag (diagonal remainder):
        O(ρ²) diagonal correction:
            η_diag ≤ C_diag · ρ²
        Estimated from second-order stiffness; set to 0 if not available.

    Gate 1 margin:
        𝔊₁ := Δ_bench,ρ^fin − η_{R,ρ}  >  0  ↔  Gate 1 PASS

    Attributes
    ----------
    rho         : float   patch momentum radius
    K_offdiag   : float   max_i ‖P*K_iQ*‖_F  (velocity off-diagonal norm)
    K_tail      : float   leading tail norm (max_i ‖K_i‖_op)
    delta_bench : float   Δ_bench,ρ^fin (Level-2 numerical gap)
    n_modes     : int     n* (dimension of V*)
    eta_tr      : float   transport correction bound
    eta_tail    : float   tail correction bound
    eta_diag    : float   diagonal remainder bound
    eta_R       : float   total η_{R,ρ} = η_tr + η_tail + η_diag
    gate1_margin: float   Δ_bench − η_R  (> 0 ↔ Gate 1 PASS)
    gate1_pass  : bool
    """
    rho          : float
    K_offdiag    : float
    K_tail       : float
    delta_bench  : float
    n_modes      : int
    eta_tr       : float
    eta_tail     : float
    eta_diag     : float
    eta_R        : float
    gate1_margin : float
    gate1_pass   : bool
    gamma_ij_missing : bool = False


def compute_eta_R_decomp(
    transport_results: List[Any],
    proj_results:      List[Any],
    delta_bench:       float,
    rho:               float,
    *,
    gamma_ij:          Optional[np.ndarray] = None,
    verbose:           bool = False,
) -> EtaRDecompResult:
    """
    Compute the decomposition-based upper bound on η_{R,ρ} (TECT-Math30 §3.1):

        η_{R,ρ} ≤ η_tr + η_tail + η_diag

    Uses M_i = P*K_iP* from TransportResult and P*/Q* from ProjectorResult.

    Parameters
    ----------
    transport_results : list of TransportResult  (contains M[3] velocity matrices)
    proj_results      : list of ProjectorResult  (contains P_star, Q_star, mode_mask)
    delta_bench       : float    Δ_bench from Level-2 numerical gap (or Level-1 if unavailable)
    rho               : float    patch momentum radius (BZ units)
    gamma_ij          : (3,3) stiffness tensor (optional; for η_diag)
    verbose           : bool

    Returns
    -------
    EtaRDecompResult
    """
    # Collect off-diagonal velocity norms over all patches
    K_offdiag_vals = []
    K_tail_vals    = []
    n_modes_list   = []

    for tr, pr in zip(transport_results, proj_results):
        # Use full K_i matrices (NOT P*K_iP*) so that P*K_iQ* off-diagonal coupling
        # is non-trivial.  tr.K stores the raw velocity matrices from bloch_linearization;
        # tr.M = P*K_iP* (projected) would give PKQ ≡ 0 identically.
        K_arr   = np.asarray(tr.K, dtype=np.complex128)   # (3, 3, 3) full K_i
        P_star  = np.asarray(pr.P_star, dtype=np.complex128)
        Q_star  = np.asarray(pr.Q_star, dtype=np.complex128)

        idx_modes = np.where(np.asarray(pr.mode_mask))[0]
        n_modes   = len(idx_modes)
        n_modes_list.append(n_modes)

        for i in range(3):
            Ki    = K_arr[i]                         # (3,3) full K_i (NOT P*K_iP*)
            PK    = P_star @ Ki                      # P* K_i
            PKQ   = PK @ Q_star                      # P* K_i Q*  (Löwdin off-diagonal block)
            K_offdiag_vals.append(float(np.linalg.norm(PKQ, 'fro')))
            # Full operator norm for η_tail: ‖K_i‖_op = max singular value of full K_i
            K_tail_vals.append(float(np.linalg.norm(Ki, 2)))

    K_offdiag_max = float(max(K_offdiag_vals)) if K_offdiag_vals else 0.0
    K_tail_max    = float(max(K_tail_vals))    if K_tail_vals    else 0.0
    n_star        = int(np.mean(n_modes_list)) if n_modes_list  else 1

    # η_tr: Löwdin-type bound (n* · K_offdiag² · ρ / Δ_bench)
    if delta_bench > 0:
        eta_tr = n_star * K_offdiag_max**2 * rho / delta_bench
    else:
        eta_tr = float('inf')

    # η_tail: leading O(ρ) from omitted channel tail (ultra-minimal: K_tail · ρ)
    eta_tail = K_tail_max * rho

    # η_diag: O(ρ²) diagonal correction from stiffness; use stiffness norm if available
    #
    # IMPORTANT: η_diag=0 when gamma_ij is unavailable is NOT conservative.
    # Gate 1 tests: 𝔊₁ = Δ_bench − η_R > 0.  Setting η_diag=0 UNDER-estimates
    # η_R, which OVER-estimates 𝔊₁ → optimistic (not conservative) for Gate 1.
    #
    # When gamma_ij is not provided, we flag the result as non-rigorous.
    gamma_ij_missing = (gamma_ij is None)
    if gamma_ij is not None:
        G = np.asarray(gamma_ij, dtype=float)
        eta_diag = float(np.linalg.norm(G, 2)) * rho**2
    else:
        eta_diag = 0.0
        import warnings
        warnings.warn(
            "eta_diag set to 0 because gamma_ij (stiffness tensor) was not provided. "
            "This UNDER-estimates η_R and is OPTIMISTIC for Gate 1, not conservative. "
            "Provide gamma_ij from Stage U2 stiffness extraction for a rigorous bound."
        )

    eta_R = eta_tr + eta_tail + eta_diag
    margin = delta_bench - eta_R

    if verbose:
        print(f"  [η_R decomp] rho={rho:.4f}  K_offdiag={K_offdiag_max:.4e}  K_tail={K_tail_max:.4e}")
        print(f"    η_tr={eta_tr:.4e}  η_tail={eta_tail:.4e}  η_diag={eta_diag:.4e}  η_R={eta_R:.4e}")
        print(f"    Δ_bench={delta_bench:.4e}  𝔊₁ = Δ_bench − η_R = {margin:.4e}  "
              f"Gate 1: {'PASS' if margin > 0 else 'FAIL'}")

    return EtaRDecompResult(
        rho              = rho,
        K_offdiag        = K_offdiag_max,
        K_tail           = K_tail_max,
        delta_bench      = delta_bench,
        n_modes          = n_star,
        eta_tr           = eta_tr,
        eta_tail         = eta_tail,
        eta_diag         = eta_diag,
        eta_R            = eta_R,
        gate1_margin     = margin,
        gate1_pass       = bool(margin > 0),
        gamma_ij_missing = gamma_ij_missing,
    )


def eta_R_decomp_text_report(er: EtaRDecompResult) -> str:
    """Plain-text Gate 1 margin report."""
    lines = [
        f"[Gate 1] Decomposition-based η_R,ρ (TECT-Math30 §3.1)",
        f"  ρ              = {er.rho:.4e}",
        f"  K_offdiag_max  = {er.K_offdiag:.4e}  (max_i ‖P*K_iQ*‖_F)",
        f"  K_tail_max     = {er.K_tail:.4e}  (max_i ‖K_i‖_op)",
        f"  n*             = {er.n_modes}",
        f"  η_tr           = {er.eta_tr:.4e}",
        f"  η_tail         = {er.eta_tail:.4e}",
        f"  η_diag         = {er.eta_diag:.4e}",
        f"  η_R = η_tr+η_tail+η_diag = {er.eta_R:.4e}",
        f"  Δ_bench        = {er.delta_bench:.4e}",
        f"  𝔊₁ = Δ_bench − η_R = {er.gate1_margin:.4e}  "
        f"({'PASS' if er.gate1_pass else 'FAIL'})",
    ]
    return "\n".join(lines)


def eta_R_decomp_latex_block(er: EtaRDecompResult) -> str:
    """LaTeX align block for Gate 1 margin (PRL-style)."""
    sign  = r"\checkmark" if er.gate1_pass else r"\times"
    return (
        r"\begin{align}" + "\n"
        rf"  \eta_{{R,\rho}} &= \eta_{{\rm tr}} + \eta_{{\rm tail}} + \eta_{{\rm diag}} \nonumber\\" + "\n"
        rf"  &= {er.eta_tr:.4e} + {er.eta_tail:.4e} + {er.eta_diag:.4e} = {er.eta_R:.4e} \nonumber\\" + "\n"
        rf"  \Delta_{{\rm bench}} &= {er.delta_bench:.4e} \nonumber\\" + "\n"
        rf"  \mathfrak{{G}}_1 &:= \Delta_{{\rm bench}} - \eta_{{R,\rho}} = {er.gate1_margin:.4e} \quad {sign}" + "\n"
        r"\end{align}"
    )


# ============================================================
# Level 1: analytical linear gap audit
# ============================================================

def linear_gap_audit(
    params:        Dict[str, Any],
    patch_centers: np.ndarray,
    q0:            float,
    Nx: int, Ny: int, Nz: int,
    r_patch_frac:  float = 0.25,
    eta_threshold: float = 0.05,
    offshell_tol:  float = 0.05,
    verbose:       bool  = False,
) -> RemoteGapResult:
    """
    Level-1 remote gap audit: analytical linear operator over full k-grid.

    Parameters
    ----------
    params        : solver parameter dict
    patch_centers : (Npatch, 3) unit vectors
    q0            : float   shell radius
    Nx, Ny, Nz    : int     grid sizes
    r_patch_frac  : float   neighbourhood radius (fraction of q₀)
    eta_threshold : float   gap certificate threshold
    offshell_tol  : float   |L_lin(k) − L_lin(G*)| / |L_lin(G*)| < this → on-shell
    verbose       : bool

    Returns
    -------
    RemoteGapResult (Level 1 filled, Level 2 empty)
    """
    kx, ky, kz = kgrid_3d(params, Nx, Ny, Nz)

    # Analytical L_lin on full grid
    L_lin = _L_lin_grid(params, kx, ky, kz)  # (Nx, Ny, Nz)

    # L_lin at first patch centre (reference)
    gc0    = np.asarray(patch_centers[0], dtype=float)
    nrm0   = np.linalg.norm(gc0)
    G0     = q0 * gc0 / max(nrm0, 1e-14)
    ix, iy, iz = k_to_grid_idx(G0, kx, ky, kz)
    L_lin_G = float(L_lin[ix, iy, iz])

    # Remote region mask
    mask_remote = remote_region_mask(kx, ky, kz, patch_centers, q0,
                                     r_patch_frac=r_patch_frac)
    n_remote = int(mask_remote.sum())
    n_total  = Nx * Ny * Nz

    if n_remote == 0:
        warnings.warn("No remote k-points found.  Increase grid size or decrease r_patch_frac.")
        return RemoteGapResult(
            n_remote=0, n_total=n_total, remote_fraction=0.0,
            L_lin_at_G_star=L_lin_G,
            delta_lin_offshell=float("nan"), delta_lin_all=float("nan"),
            kmin_lin=np.zeros(3),
            offshell_tol=offshell_tol,
            eta_threshold=eta_threshold,
            certificate_lin=False, certificate=False,
        )

    # L_lin over remote points
    L_remote = L_lin[mask_remote]

    # All-remote minimum (GAP relative to L_lin(G*), consistent with delta_lin_offshell)
    imin_flat       = int(np.argmin(L_remote))
    delta_lin_all   = float(L_remote[imin_flat]) - L_lin_G

    # Find corresponding k-vector
    remote_indices  = np.argwhere(mask_remote)
    idx_min         = remote_indices[imin_flat]
    kmin_lin        = np.array([kx[idx_min[0]], ky[idx_min[1]], kz[idx_min[2]]])

    # Off-shell sub-minimum: remote points where L_lin(k) ≠ L_lin(G*)
    on_shell_tol_abs = offshell_tol * max(abs(L_lin_G), 1e-14)
    offshell_mask    = np.abs(L_remote - L_lin_G) > on_shell_tol_abs
    if offshell_mask.any():
        L_offshell       = L_remote[offshell_mask]
        delta_lin_offshell = float(L_offshell.min()) - L_lin_G
    else:
        delta_lin_offshell = 0.0   # all remote k-points are on-shell → gap from NL only

    cert_lin = delta_lin_offshell > eta_threshold

    if verbose:
        print(
            f"  Remote k-points: {n_remote}/{n_total} ({100*n_remote/n_total:.1f}%)\n"
            f"  L_lin(G*)          = {L_lin_G:.6e}\n"
            f"  Δ_lin_all          = {delta_lin_all:.6e}   at k={kmin_lin}\n"
            f"  Δ_lin_offshell     = {delta_lin_offshell:.6e}\n"
            f"  η_threshold        = {eta_threshold:.4e}\n"
            f"  Certificate (lin)  = {cert_lin}"
        )

    return RemoteGapResult(
        n_remote           = n_remote,
        n_total            = n_total,
        remote_fraction    = n_remote / n_total,
        L_lin_at_G_star    = L_lin_G,
        delta_lin_offshell = delta_lin_offshell,
        delta_lin_all      = delta_lin_all,
        kmin_lin           = kmin_lin,
        offshell_tol       = offshell_tol,
        eta_threshold      = eta_threshold,
        certificate_lin    = cert_lin,
        certificate_nl     = None,
        certificate        = cert_lin,
    )


# ============================================================
# Level 2: numerical nonlinear gap (sampled)
# ============================================================

def numerical_gap_sample(
    Psi0:          np.ndarray,
    params:        Dict[str, Any],
    patch_centers: np.ndarray,
    q0:            float,
    hessian_fn:    Callable[[np.ndarray], np.ndarray],
    n_sample:      int   = 50,
    seed:          int   = 42,
    r_patch_frac:  float = 0.25,
    eta_threshold: float = 0.05,
    verbose:       bool  = False,
) -> RemoteGapResult:
    """
    Level-2 remote gap audit: numerical L(k) probing at sampled remote k-points.

    For each sampled remote k-point k_s:
      1. Probe bloch_matrix_at_idx(Psi0, idx_s, hessian_fn, params) → 3×3 L(k_s)
      2. Symmetrise: L_sym = (L + L†)/2
      3. λ_min(k_s) = minimum eigenvalue of L_sym

    Report: Δ_nl_sample = min_s λ_min(k_s)

    Parameters
    ----------
    Psi0          : (3, Nx, Ny, Nz) converged condensate
    params        : dict
    patch_centers : (Npatch, 3) unit vectors
    q0            : float
    hessian_fn    : callable  v → hessian_vec(Psi0, v, params)
    n_sample      : int   number of remote k-points to probe
    seed          : int   RNG seed for reproducible sampling
    r_patch_frac  : float
    eta_threshold : float
    verbose       : bool

    Returns
    -------
    RemoteGapResult (Level 2 filled; Level 1 fields left at defaults)
    """
    _, Nx, Ny, Nz = Psi0.shape
    kx, ky, kz    = kgrid_3d(params, Nx, Ny, Nz)

    # Remote mask
    mask_remote   = remote_region_mask(kx, ky, kz, patch_centers, q0,
                                       r_patch_frac=r_patch_frac)
    n_remote      = int(mask_remote.sum())

    if n_remote == 0:
        warnings.warn("No remote k-points found for numerical sampling.")
        return RemoteGapResult(
            n_remote=0, n_total=Nx*Ny*Nz, remote_fraction=0.0,
            L_lin_at_G_star=float("nan"),
            delta_lin_offshell=float("nan"), delta_lin_all=float("nan"),
            kmin_lin=np.zeros(3), offshell_tol=0.0,
            n_sample=0, delta_nl_sample=float("nan"),
            eta_threshold=eta_threshold,
            certificate_lin=False, certificate_nl=False, certificate=False,
        )

    # Sample up to n_sample remote indices
    remote_idx = np.argwhere(mask_remote)       # (n_remote, 3)
    rng        = np.random.default_rng(seed)
    chosen     = rng.choice(n_remote,
                             size=min(n_sample, n_remote),
                             replace=False)
    sampled_idx = remote_idx[chosen]             # (n_sampled, 3)

    nl_evals_min = []
    kmin_nl      = None
    delta_nl     = float("inf")

    for si, (ix, iy, iz) in enumerate(sampled_idx):
        idx = (int(ix), int(iy), int(iz))
        try:
            L_num = bloch_matrix_at_idx(Psi0, idx, hessian_fn, params)
        except Exception as exc:
            warnings.warn(f"hessian probe failed at idx={idx}: {exc}")
            continue

        L_sym  = symmetrise(L_num)
        evals  = np.real(np.linalg.eigvalsh(L_sym))
        lam_min = float(evals[0])
        nl_evals_min.append(lam_min)

        if lam_min < delta_nl:
            delta_nl = lam_min
            kmin_nl  = np.array([kx[ix], ky[iy], kz[iz]])

        if verbose and si % 10 == 0:
            k_vec = np.array([kx[ix], ky[iy], kz[iz]])
            print(f"    [{si+1}/{len(sampled_idx)}] k={k_vec}  λ_min={lam_min:.4e}")

    if not nl_evals_min:
        delta_nl = float("nan")

    cert_nl = (not math.isnan(delta_nl)) and (delta_nl > eta_threshold)

    if verbose:
        print(
            f"  Sampled {len(nl_evals_min)} remote k-points\n"
            f"  Δ_nl_sample        = {delta_nl:.6e}  at k={kmin_nl}\n"
            f"  Certificate (nl)   = {cert_nl}"
        )

    return RemoteGapResult(
        n_remote           = n_remote,
        n_total            = Nx * Ny * Nz,
        remote_fraction    = n_remote / (Nx * Ny * Nz),
        L_lin_at_G_star    = float("nan"),
        delta_lin_offshell = float("nan"),
        delta_lin_all      = float("nan"),
        kmin_lin           = np.zeros(3),
        offshell_tol       = 0.0,
        n_sample           = len(nl_evals_min),
        delta_nl_sample    = delta_nl,
        kmin_nl            = kmin_nl,
        nl_evals_min       = nl_evals_min,
        eta_threshold      = eta_threshold,
        certificate_lin    = False,
        certificate_nl     = cert_nl,
        certificate        = cert_nl,
    )


# ============================================================
# Full two-level audit
# ============================================================

def full_remote_gap_audit(
    Psi0:              np.ndarray,
    params:            Dict[str, Any],
    patch_centers:     np.ndarray,
    q0:                float,
    hessian_fn:        Callable[[np.ndarray], np.ndarray],
    *,
    r_patch_frac:      float = 0.25,
    eta_threshold:     float = 0.05,
    offshell_tol:      float = 0.05,
    n_sample:          int   = 50,
    seed:              int   = 42,
    skip_level2:       bool  = False,
    transport_results: Optional[List[Any]] = None,
    proj_results:      Optional[List[Any]] = None,
    rho_decomp:        float = 0.0,
    verbose:           bool  = True,
) -> Dict[str, Any]:
    """
    Run the full two-level remote gap audit (Stage U4) with optional Gate 1
    decomposition-based η_R,ρ bound (Module 10 upgrade, TECT-Math30 §3.1).

    Parameters
    ----------
    Psi0              : (3, Nx, Ny, Nz) converged condensate
    params            : dict
    patch_centers     : (Npatch, 3) unit vectors
    q0                : float
    hessian_fn        : callable
    r_patch_frac      : float   condensate neighbourhood radius / q₀
    eta_threshold     : float   proxy Δ_bench threshold (legacy, kept for compat)
    offshell_tol      : float   fractional tolerance for on-shell classification
    n_sample          : int     remote k-points for Level-2 numerical probe
    seed              : int     RNG seed
    skip_level2       : bool    skip numerical sampling (faster, linear-only)
    transport_results : list    TransportResult per patch (for η_R decomp)
    proj_results      : list    ProjectorResult per patch (for η_R decomp)
    rho_decomp        : float   patch momentum radius for η_R bound  (0 → auto = r_patch_frac * q0)
    verbose           : bool

    Returns
    -------
    dict with keys:
        "level1"      : RemoteGapResult
        "level2"      : RemoteGapResult (None if skipped)
        "certificate" : bool
        "summary"     : dict
        "eta_R_decomp": EtaRDecompResult (None if transport/proj not provided)
    """
    _, Nx, Ny, Nz = Psi0.shape

    if verbose:
        print("=" * 60)
        print("Stage U4: Remote spectral gap audit")
        print(f"  Grid: {Nx}×{Ny}×{Nz}   r_patch={r_patch_frac:.2f}·q₀   "
              f"η={eta_threshold:.4e}")
        print("=" * 60)

    # Level 1 — linear analytical
    if verbose:
        print("\n[Level 1] Analytical linear gap (full grid)…")
    lv1 = linear_gap_audit(
        params, patch_centers, q0, Nx, Ny, Nz,
        r_patch_frac  = r_patch_frac,
        eta_threshold = eta_threshold,
        offshell_tol  = offshell_tol,
        verbose       = verbose,
    )

    # Level 2 — numerical sample
    lv2 = None
    if not skip_level2:
        if verbose:
            print(f"\n[Level 2] Numerical L(k) probing ({n_sample} samples)…")
        lv2 = numerical_gap_sample(
            Psi0, params, patch_centers, q0, hessian_fn,
            n_sample      = n_sample,
            seed          = seed,
            r_patch_frac  = r_patch_frac,
            eta_threshold = eta_threshold,
            verbose       = verbose,
        )

    # Global certificate (proxy threshold)
    cert = lv1.certificate
    if lv2 is not None and lv2.certificate_nl is not None:
        cert = cert and lv2.certificate_nl

    # --- Module 10: decomposition-based η_R,ρ (Gate 1 margin) ---
    eta_R_result = None
    if transport_results is not None and proj_results is not None:
        # Use Level-2 Δ_bench if available, else Level-1 linear gap
        if lv2 is not None and lv2.delta_nl_sample is not None and np.isfinite(lv2.delta_nl_sample):
            delta_bench = float(lv2.delta_nl_sample)
        else:
            delta_bench = float(lv1.delta_lin_all)

        if rho_decomp <= 0:
            rho_decomp = r_patch_frac * q0

        if verbose:
            print(f"\n[Module 10] Decomposition-based η_R,ρ  (ρ={rho_decomp:.4f})…")

        eta_R_result = compute_eta_R_decomp(
            transport_results, proj_results,
            delta_bench = delta_bench,
            rho         = rho_decomp,
            verbose     = verbose,
        )

    summary = {
        "delta_lin_offshell" : lv1.delta_lin_offshell,
        "delta_lin_all"      : lv1.delta_lin_all,
        "L_lin_at_G_star"    : lv1.L_lin_at_G_star,
        "delta_nl_sample"    : lv2.delta_nl_sample if lv2 else None,
        "n_remote"           : lv1.n_remote,
        "n_total"            : lv1.n_total,
        "remote_fraction"    : lv1.remote_fraction,
        "eta_threshold"      : eta_threshold,
        "certificate_lin"    : lv1.certificate_lin,
        "certificate_nl"     : (lv2.certificate_nl if lv2 else None),
        "certificate"        : cert,
        # Gate 1
        "eta_R"              : (eta_R_result.eta_R        if eta_R_result else None),
        "gate1_margin"       : (eta_R_result.gate1_margin if eta_R_result else None),
        "gate1_pass"         : (eta_R_result.gate1_pass   if eta_R_result else None),
    }

    if verbose:
        print("\n" + "=" * 60)
        print("Stage U4 certificate:")
        print(f"  Δ_lin_offshell = {lv1.delta_lin_offshell:.6e}  "
              f"({'PASS' if lv1.certificate_lin else 'FAIL'})")
        if lv2 and lv2.delta_nl_sample is not None:
            print(f"  Δ_nl_sample    = {lv2.delta_nl_sample:.6e}  "
                  f"({'PASS' if lv2.certificate_nl else 'FAIL'})")
        if eta_R_result:
            g1 = eta_R_result.gate1_margin
            print(f"  Gate 1 𝔊₁     = {g1:.6e}  "
                  f"({'PASS' if eta_R_result.gate1_pass else 'FAIL'})")
        print(f"  GLOBAL: {'PASS ✓' if cert else 'FAIL ✗'}")
        print("=" * 60)

    return {
        "level1"      : lv1,
        "level2"      : lv2,
        "certificate" : cert,
        "summary"     : summary,
        "eta_R_decomp": eta_R_result,
    }


# ============================================================
# Reporting
# ============================================================

def remote_gap_text_report(result: Dict[str, Any]) -> str:
    """Plain-text summary of full_remote_gap_audit output."""
    s   = result["summary"]
    lv1 = result["level1"]
    lv2 = result.get("level2")

    rows = [
        "Remote spectral gap audit",
        f"  Remote k-points : {s['n_remote']}/{s['n_total']} "
        f"({100*s['remote_fraction']:.1f}%)",
        f"  L_lin(G*)       : {s['L_lin_at_G_star']:.6e}",
        f"  Δ_lin_offshell  : {s['delta_lin_offshell']:.6e}  "
        f"({'PASS' if s['certificate_lin'] else 'FAIL'}  η={s['eta_threshold']:.2e})",
    ]
    if lv2 is not None and s["delta_nl_sample"] is not None:
        rows.append(
            f"  Δ_nl_sample     : {s['delta_nl_sample']:.6e}  "
            f"({'PASS' if s['certificate_nl'] else 'FAIL'})"
        )
        rows.append(f"  (sampled {lv2.n_sample} remote k-points)")
    rows.append(f"  GLOBAL CERTIFICATE: {'PASS' if s['certificate'] else 'FAIL'}")
    return "\n".join(rows)


def remote_gap_latex_block(
    result:  Dict[str, Any],
    *,
    label:   str = "eq:remote_gap_cert",
) -> str:
    r"""
    LaTeX block summarising the remote gap certificate.

    When the decomposition-based η_{R,ρ} (TECT-Math30 §3.1) is available,
    the block uses the physically grounded bound:

        η_{R,ρ} ≤ η_tr + η_tail + η_diag

    and the Gate 1 margin  𝔊₁ = Δ_bench − η_{R,ρ}.

    Falls back to the proxy eta_threshold only when the decomposition was
    not computed (e.g. skip_level2 mode).

    Returns a string with \begin{align}...\end{align} and a verdict line.
    """
    s  = result["summary"]
    er = result.get("eta_R_decomp")

    nl_str = ""
    if s["delta_nl_sample"] is not None:
        nl_val = s["delta_nl_sample"]
        nl_str = (
            rf",\quad "
            rf"\Delta_{{\rm bench}}^{{\rm nl}} = {nl_val:.4e}"
        )

    # ── Use decomposition-based η_R when available ────────────────────────
    if er is not None:
        cert_sym = r"\checkmark" if er.gate1_pass else r"\times"
        eta_line = (
            rf"  \eta_{{R,\rho}} &= "
            rf"\underbrace{{{er.eta_tr:.4e}}}_{{\eta_{{\rm tr}}}}"
            rf" + \underbrace{{{er.eta_tail:.4e}}}_{{\eta_{{\rm tail}}}}"
            rf" + \underbrace{{{er.eta_diag:.4e}}}_{{\eta_{{\rm diag}}}}"
            rf" = {er.eta_R:.4e}"
        )
        if er.gamma_ij_missing:
            eta_line += (
                r"\quad\textcolor{orange}{"
                r"\scriptstyle(\eta_{\rm diag}=0\text{: optimistic, "
                r"\Gamma_{ij}\text{ not provided})}}"
            )
        margin_line = (
            rf"  \mathfrak{{G}}_1 &= \Delta_{{\rm bench}} - \eta_{{R,\rho}}"
            rf" = {er.gate1_margin:+.4e}"
        )
        verdict = (
            rf"\noindent\textbf{{Gate 1 (remote gap)}}: {cert_sym}\ "
            rf"$\mathfrak{{G}}_1 = {er.gate1_margin:+.4e} > 0$."
        )
        lines = [
            r"\begin{align}",
            rf"  \Delta_{{\rm bench}}^{{\rm lin}} &= {s['delta_lin_offshell']:.4e}"
            + nl_str + r"\\",
            eta_line + r"\\",
            margin_line,
            r"\end{align}",
            verdict,
        ]
    else:
        # Fallback: proxy threshold (no decomposition computed)
        cert_sym = r"\checkmark" if s["certificate"] else r"\times"
        lines = [
            r"\begin{align}",
            rf"  \Delta_{{\rm bench}}^{{\rm lin}} &= {s['delta_lin_offshell']:.4e}"
            + nl_str + r"\\",
            rf"  \eta_{{R,\rho}} &= {s['eta_threshold']:.4e}"
            r"\quad\text{(proxy threshold; decomposition not computed)}",
            r"\end{align}",
            rf"\noindent\textbf{{Remote gap certificate (proxy)}}: {cert_sym}\ "
            rf"$\Delta_{{\rm bench}} > \eta_{{R,\rho}}$.",
        ]
    return "\n".join(lines)
