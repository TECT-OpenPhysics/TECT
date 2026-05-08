#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v2.0
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
"""
transport_extractor.py — Stage U2, Module 3
============================================
TECT transport-coefficient extraction: K_i, M_i = P*K_iP*, (λ_∥, α, β).

Physical background
-------------------
The Bloch-operator velocity matrix at G* is

    K_i^{ab}(G*) = ∂L_{ab}(k)/∂k_i |_{k=G*}       (3×3 complex)

Projected onto the condensate subspace V* (dimension n* ≤ 3):

    M_i = P* K_i P*     (3×3, but rank ≤ n*)

The eigenvalues of M_i give group velocities along k_i.  For the Brazovskii
condensate at the shell instability |G*| = q₀, the first-order velocities
typically vanish by the shell symmetry (the condensate sits at a local maximum
of the dispersion projected onto V*).  The physically relevant quantities are
then the second-order stiffness coefficients:

    Eff. stiffness tensor at G*:
    Γ_{ij} = P* [∂²L/∂k_i∂k_j]|_{G*} P*   +  (Löwdin second-order correction)

Decomposed into longitudinal (∥) and transverse (⊥) directions relative to
the ordering vector ĝ = G*/|G*|:

    λ_∥  = Γ_{ĝ·ĝ}      longitudinal stiffness
    α    = Γ_{e₁·e₁}    first transverse stiffness
    β    = Γ_{e₂·e₂}    second transverse stiffness

where e₁, e₂ are two unit vectors orthogonal to ĝ (and to each other).

Implementation
--------------
We compute Γ_{ij} by a second finite-difference in k (4th-order Richardson)
applied to the full L matrix, then project.  For efficiency, the Löwdin
second-order correction is evaluated perturbatively:

    Löwdin_{ij} = −Σ_{m ∉ V*}
                   [P*K_iQ*|u_m⟩⟨u_m|Q*K_jP* + P*K_jQ*|u_m⟩⟨u_m|Q*K_iP*]
                   / (E_m − E_0)

where E_m = eigenvalues of L outside V* and E_0 = mean eigenvalue inside V*.

API
---
- TransportResult (dataclass)
- second_derivative_bloch(Psi0, idx, i, j, hessian_fn, params, ...) → 3×3
- stiffness_tensor_full(bloch_results, proj_results, Psi0,
                        hessian_fn, params, ...) → list of TransportResult
- extract_lambda_alpha_beta(Gamma_ij_dict, G_unit) → (lambda_par, alpha, beta)
- lowdin_correction(K_i, K_j, pr, energy_scale) → 3×3
- transport_latex_table(transport_results) → str
- transport_text_report(transport_results) → str
- full_stage_U2_pipeline(Psi0, patch_centers, q0, hessian_fn, params, ...) → dict
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import importlib
from pathlib import Path

import numpy as np

from bloch_linearization import (
    bloch_matrix_at_idx,
    bloch_derivative_numerical,
    bloch_derivative_linear,
    bloch_matrices_all_patches,
    kgrid_3d,
    k_to_grid_idx,
    _shifted_idx,
    symmetrise,
    check_hermiticity,
)
from projector_spectral import (
    ProjectorResult,
    condensate_projector,
    condensate_projector_all,
    verify_projector,
)


# ============================================================
# Result container
# ============================================================

@dataclass
class TransportResult:
    """
    Full transport-coefficient extraction output for a single G*.

    Attributes
    ----------
    patch_idx         : int
    G_star            : (3,) float   continuous G*
    G_grid            : (3,) float   snapped G*
    G_unit            : (3,) float   unit vector ĝ = G_grid/|G_grid|
    M                 : (3, 3, 3)    M_i = P*K_iP*  for i=0,1,2 (first-order velocity)
    Gamma             : (3, 3, 3)    Γ_{ij} = second-order projected stiffness (no Löwdin)
    Gamma_lowdin      : (3, 3, 3)    Γ_{ij} + Löwdin correction
    lambda_par_stiff  : float   longitudinal second-order stiffness Γ_{∥∥}
    alpha_stiff       : float   first transverse second-order stiffness Γ_{11}
    beta_stiff        : float   second transverse second-order stiffness Γ_{22}
    e1                : (3,) float   first transverse direction
    e2                : (3,) float   second transverse direction
    M_evals           : (3, 3)       eigenvalues of M_i for i=0,1,2
    gap               : float        spectral gap of L at G*
    K                 : (3, 3, 3)    K_i matrices (from bloch_results)
    K_lin             : (3, 3, 3)    analytical linear K_i (reference)
    n_modes           : int          condensate subspace dimension

    Note on naming
    --------------
    The quantities ``lambda_par_stiff``, ``alpha_stiff``, ``beta_stiff`` are
    *second-order stiffness coefficients*, not the first-order Dirac-symbol
    coefficients (λ_∥, α, β) that appear in the TECT theorem-level reduced
    action.  They are defined as frame-projected traces of Γ_{ij} (with
    Löwdin correction) and characterise the curvature of the condensate
    dispersion near G*.  The true first-order Dirac coefficients require a
    separate Stage-U2b extraction step (eigenvalues of P*K_iP* along the
    appropriate symmetry-breaking directions).
    """
    patch_idx        : int
    G_star           : np.ndarray
    G_grid           : np.ndarray
    G_unit           : np.ndarray
    M                : np.ndarray          # (3, 3, 3)  P*K_iP*
    Gamma            : np.ndarray          # (3, 3) scalar stiffness matrix in frame
    Gamma_lowdin     : np.ndarray          # (3, 3) + Löwdin correction
    lambda_par_stiff : float               # Γ_∥∥  second-order stiffness along G*
    alpha_stiff      : float               # Γ_⊥⊥  first transverse stiffness
    beta_stiff       : float               # Γ_⊥⊥' second transverse stiffness
    e1               : np.ndarray
    e2               : np.ndarray
    M_evals          : np.ndarray          # (3, 3)
    gap              : float
    K                : np.ndarray          # (3, 3, 3) from bloch_results["K"]
    K_lin            : np.ndarray          # (3, 3, 3)
    n_modes          : int

# ============================================================
# Util
# ============================================================

def load_backend_module(backend_arg: str):
    p = Path(backend_arg)
    if p.suffix == ".py" or p.exists():
        p = p.expanduser().resolve()
        spec = importlib.util.spec_from_file_location("tect_backend_dynamic", str(p))
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load backend module from: {p}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    return importlib.import_module(backend_arg)

# ============================================================
# Second finite difference in k for Γ_{ij} = P*∂²L/∂k_i∂k_j P*
# ============================================================

def second_derivative_bloch(
    Psi0: np.ndarray,
    idx: Tuple[int, int, int],
    i: int,
    j: int,
    hessian_fn: Callable[[np.ndarray], np.ndarray],
    params: Dict[str, Any],
    *,
    n_steps: int = 2,
    order: int = 4,
    verbose: bool = False,
) -> np.ndarray:
    """
    Compute ∂²L(k)/∂k_i∂k_j |_{k=G*} as a 3×3 matrix by finite differences.

    Mixed partial (i ≠ j): cross derivative using 4-point formula:
        ∂²L/∂k_i∂k_j ≈
          [L(+i+j) − L(+i−j) − L(−i+j) + L(−i−j)] / (4 δk_i δk_j)

    Diagonal (i == j): second derivative using 5-point formula:
        ∂²L/∂k_i² ≈
          [−L(+2i) + 16L(+i) − 30L(0) + 16L(−i) − L(−2i)] / (12 δk_i²)
        (O(δk⁴) accuracy)

    Parameters
    ----------
    Psi0     : (3, Nx, Ny, Nz) converged condensate
    idx      : (ix, iy, iz)   grid index of G*
    i, j     : int            0=x,1=y,2=z
    hessian_fn : callable
    params   : dict
    n_steps  : int            number of grid steps for offset (default 2 for 4th-order)
    order    : int            finite difference order (2 or 4)
    verbose  : bool

    Returns
    -------
    d2L_didj : (3,3) complex128 ndarray
    """
    _, Nx, Ny, Nz = Psi0.shape
    shape = (Nx, Ny, Nz)

    Ldirs = [float(params["Lx"]), float(params["Ly"]), float(params["Lz"])]
    dk_i  = 2.0 * math.pi / Ldirs[i]   # physical grid step in direction i
    dk_j  = 2.0 * math.pi / Ldirs[j]   # physical grid step in direction j

    step = 1 if order == 2 else 1   # we use step=1 for one-grid-step shifts

    if i == j:
        # Diagonal: ∂²L/∂k_i²
        idx_p2 = _shifted_idx(idx, i, +2, shape)
        idx_p1 = _shifted_idx(idx, i, +1, shape)
        idx_m1 = _shifted_idx(idx, i, -1, shape)
        idx_m2 = _shifted_idx(idx, i, -2, shape)

        L_p2 = bloch_matrix_at_idx(Psi0, idx_p2, hessian_fn, params)
        L_p1 = bloch_matrix_at_idx(Psi0, idx_p1, hessian_fn, params)
        L_0  = bloch_matrix_at_idx(Psi0, idx,    hessian_fn, params)
        L_m1 = bloch_matrix_at_idx(Psi0, idx_m1, hessian_fn, params)
        L_m2 = bloch_matrix_at_idx(Psi0, idx_m2, hessian_fn, params)

        if order >= 4:
            d2L = (-L_p2 + 16.0 * L_p1 - 30.0 * L_0 + 16.0 * L_m1 - L_m2) / (12.0 * dk_i**2)
        else:
            d2L = (L_p1 - 2.0 * L_0 + L_m1) / dk_i**2

    else:
        # Mixed: ∂²L/∂k_i∂k_j — 4-point cross difference
        def _shift(di, dj):
            ix2 = _shifted_idx(idx, i, di, shape)
            ix3 = _shifted_idx(ix2, j, dj, shape)
            return bloch_matrix_at_idx(Psi0, ix3, hessian_fn, params)

        L_pp = _shift(+1, +1)
        L_pm = _shift(+1, -1)
        L_mp = _shift(-1, +1)
        L_mm = _shift(-1, -1)

        d2L = (L_pp - L_pm - L_mp + L_mm) / (4.0 * dk_i * dk_j)

    if verbose:
        print(f"  d²L/dk_{i}dk_{j} max|elem| = {np.abs(d2L).max():.4e}")

    return d2L


# ============================================================
# Löwdin second-order correction
# ============================================================

def lowdin_correction(
    K_i: np.ndarray,
    K_j: np.ndarray,
    pr: ProjectorResult,
    energy_scale: Optional[float] = None,
) -> np.ndarray:
    """
    Compute the Löwdin second-order perturbative correction to Γ_{ij}:

        Δ_{ij}^Löwdin = −(P*K_i Q*) (Q*K_j P*) / ΔE
                        −(P*K_j Q*) (Q*K_i P*) / ΔE

    where ΔE = E_out_avg − E_in_avg is the mean gap between outside and
    inside modes.

    Parameters
    ----------
    K_i, K_j     : (3,3) complex128   velocity matrices at G*
    pr            : ProjectorResult
    energy_scale  : float or None
        If None, use the spectral gap of pr.  If zero or negative, return 0.

    Returns
    -------
    Delta_ij : (3,3) complex128  Löwdin correction matrix (rank ≤ n*)
    """
    P = pr.P_star
    Q = pr.Q_star

    # Determine energy denominator
    if energy_scale is None:
        energy_scale = pr.gap

    if abs(energy_scale) < 1e-14:
        warnings.warn(
            f"Patch {pr.patch_idx}: Löwdin denominator is zero (gap={pr.gap:.3e}).  "
            "Returning zero correction."
        )
        return np.zeros((3, 3), dtype=np.complex128)

    if energy_scale < 0.0:
        warnings.warn(
            f"Patch {pr.patch_idx}: Negative energy_scale={energy_scale:.3e}.  "
            "Löwdin correction may be unphysical."
        )

    K_i = np.asarray(K_i, dtype=np.complex128)
    K_j = np.asarray(K_j, dtype=np.complex128)

    # P* K_i Q* and P* K_j Q*
    PK_i_Q = P @ K_i @ Q
    PK_j_Q = P @ K_j @ Q
    QK_i_P = Q @ K_i @ P
    QK_j_P = Q @ K_j @ P

    # Löwdin: −(PK_iQ)(QK_jP)/ΔE − (PK_jQ)(QK_iP)/ΔE
    Delta = -(PK_i_Q @ QK_j_P + PK_j_Q @ QK_i_P) / energy_scale
    return Delta


# ============================================================
# Full Γ tensor computation
# ============================================================

def stiffness_tensor_full(
    bloch_results: List[Dict],
    proj_results: List[ProjectorResult],
    Psi0: np.ndarray,
    hessian_fn: Callable[[np.ndarray], np.ndarray],
    params: Dict[str, Any],
    *,
    fd_order: int = 4,
    include_lowdin: bool = True,
    verbose: bool = False,
) -> List[TransportResult]:
    """
    Compute the full stiffness tensor Γ_{ij} and transport coefficients
    (λ_∥, α, β) for all patches.

    Parameters
    ----------
    bloch_results : list of dicts from bloch_linearization.bloch_matrices_all_patches()
    proj_results  : list of ProjectorResult from projector_spectral.condensate_projector_all()
    Psi0          : (3, Nx, Ny, Nz) converged condensate
    hessian_fn    : callable
    params        : dict
    fd_order      : int    finite-difference order for second derivative (2 or 4)
    include_lowdin: bool   include Löwdin second-order correction
    verbose       : bool

    Returns
    -------
    list of TransportResult (one per patch)
    """
    if len(bloch_results) != len(proj_results):
        raise ValueError("bloch_results and proj_results must have equal length")

    results = []

    for br, pr in zip(bloch_results, proj_results):
        alpha_idx = br["patch_idx"]
        idx = br["grid_idx"]
        G_grid = np.asarray(br["G_grid"], dtype=float)
        G_star = np.asarray(br["G_star"], dtype=float)

        # Unit vector
        nrm = np.linalg.norm(G_grid)
        if nrm < 1e-14:
            warnings.warn(f"Patch {alpha_idx}: G_grid is zero; skipping transport.")
            continue
        G_unit = G_grid / nrm

        if verbose:
            print(f"\nPatch {alpha_idx}: G*={G_grid}  |G*|={nrm:.4f}")

        P = pr.P_star
        K_arr  = np.asarray(br.get("K",     np.zeros((3, 3, 3), dtype=np.complex128)))
        K_lin_arr = np.asarray(br.get("K_lin", np.zeros((3, 3, 3), dtype=np.complex128)))

        # ---- M_i = P* K_i P* ----
        M_arr = np.zeros((3, 3, 3), dtype=np.complex128)
        M_evals = np.zeros((3, 3), dtype=float)
        for i in range(3):
            M_arr[i] = P @ K_arr[i] @ P
            M_evals[i] = np.real(np.linalg.eigvalsh(symmetrise(M_arr[i])))

        # ---- Second-order stiffness Γ_{ij} ----
        Gamma_arr  = np.zeros((3, 3, 3, 3), dtype=np.complex128)  # Gamma[i,j] = 3×3 matrix
        Gamma_lowdin_arr = np.zeros((3, 3, 3, 3), dtype=np.complex128)

        for i in range(3):
            for j in range(i, 3):   # upper triangle (matrix is symmetric in i,j)
                d2L = second_derivative_bloch(
                    Psi0, idx, i, j, hessian_fn, params,
                    order=fd_order, verbose=verbose,
                )
                Gamma_ij = P @ d2L @ P
                Gamma_arr[i, j] = Gamma_ij
                Gamma_arr[j, i] = Gamma_ij   # symmetry

                if include_lowdin:
                    low = lowdin_correction(K_arr[i], K_arr[j], pr)
                    Gamma_lowdin_arr[i, j] = Gamma_ij + low
                    Gamma_lowdin_arr[j, i] = Gamma_lowdin_arr[i, j]
                else:
                    Gamma_lowdin_arr[i, j] = Gamma_ij
                    Gamma_lowdin_arr[j, i] = Gamma_ij

        # ---- Extract second-order stiffness scalars from Γ along ĝ, e₁, e₂ ----
        # Build orthonormal frame {ĝ, e₁, e₂}
        e1, e2 = _orthonormal_pair(G_unit)

        # NOTE: these are Γ_∥∥, Γ_11, Γ_22 (second-order stiffnesses),
        # NOT the first-order Dirac-symbol coefficients (λ_∥, α, β).
        lam_par_s, alpha_s, beta_s = extract_lambda_alpha_beta(
            Gamma_lowdin_arr if include_lowdin else Gamma_arr,
            G_unit, e1, e2,
        )

        if verbose:
            print(f"  Γ_∥∥(stiff) = {lam_par_s:.6e}  "
                  f"Γ_11(stiff) = {alpha_s:.6e}  Γ_22(stiff) = {beta_s:.6e}")

        # Project (3,3,3,3) Gamma to (3,3) scalar stiffness matrix in frame
        frame = np.array([G_unit, e1, e2])          # (3 directions, 3 components)
        Gamma_scalar         = _project_gamma_scalar(Gamma_arr,         frame)
        Gamma_lowdin_scalar  = _project_gamma_scalar(Gamma_lowdin_arr,  frame)

        results.append(TransportResult(
            patch_idx        = alpha_idx,
            G_star           = G_star,
            G_grid           = G_grid,
            G_unit           = G_unit,
            M                = M_arr,
            Gamma            = Gamma_scalar,
            Gamma_lowdin     = Gamma_lowdin_scalar,
            lambda_par_stiff = lam_par_s,
            alpha_stiff      = alpha_s,
            beta_stiff       = beta_s,
            e1               = e1,
            e2               = e2,
            M_evals          = M_evals,
            gap              = pr.gap,
            K                = K_arr,
            K_lin            = K_lin_arr,
            n_modes          = pr.n_modes,
        ))

    return results


# ============================================================
# Helper: orthonormal frame and Γ projection
# ============================================================

def _orthonormal_pair(
    g_unit: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Given a unit vector ĝ, return two orthonormal vectors e₁, e₂
    such that {ĝ, e₁, e₂} forms a right-handed orthonormal frame.
    """
    g = np.asarray(g_unit, dtype=float)
    g = g / np.linalg.norm(g)

    # Pick a reference vector not parallel to g
    if abs(g[0]) < abs(g[1]):
        ref = np.array([1.0, 0.0, 0.0])
    else:
        ref = np.array([0.0, 1.0, 0.0])

    e1 = ref - np.dot(ref, g) * g
    nrm = np.linalg.norm(e1)
    if nrm < 1e-14:
        e1 = np.array([0.0, 0.0, 1.0])
    else:
        e1 /= nrm

    e2 = np.cross(g, e1)
    e2 /= np.linalg.norm(e2)
    return e1, e2


def extract_lambda_alpha_beta(
    Gamma: np.ndarray,
    G_unit: np.ndarray,
    e1: np.ndarray,
    e2: np.ndarray,
) -> Tuple[float, float, float]:
    """
    Extract (λ_∥, α, β) from the stiffness tensor projected onto the
    frame {ĝ, e₁, e₂}.

    Gamma has shape (3, 3, 3, 3) where Gamma[i, j] is the 3×3 projected
    stiffness matrix in component space.  We further project onto the
    condensate direction by taking the real part of the trace.

    λ_∥ = Re tr(Gamma[∥, ∥]) / n*
    α   = Re tr(Gamma[e₁, e₁]) / n*
    β   = Re tr(Gamma[e₂, e₂]) / n*

    where [a, b] means the component (3×3 matrix) Γ_{a,b} = Σ_{ij} a_i Γ_{ij} b_j.
    """
    # Gamma[i, j] is a 3×3 matrix; we contract with frame directions
    def project_frame(n_vec: np.ndarray, m_vec: np.ndarray) -> float:
        """Compute Re tr[Σ_{ij} n_i Γ_{ij} m_j]."""
        total = np.zeros((3, 3), dtype=np.complex128)
        for i in range(3):
            for j in range(3):
                total += n_vec[i] * m_vec[j] * Gamma[i, j]
        return float(np.real(np.trace(total)))

    lam_par = project_frame(G_unit, G_unit)
    alpha   = project_frame(e1, e1)
    beta    = project_frame(e2, e2)
    return lam_par, alpha, beta


def _project_gamma_scalar(
    Gamma: np.ndarray,
    frame: np.ndarray,
) -> np.ndarray:
    """
    Contract (3, 3, 3, 3) Γ tensor with the frame {ĝ, e₁, e₂} to produce
    a (3, 3) real matrix of scalar stiffness components Γ_{AB} = ê_A^i Γ_{ij}^{tr} ê_B^j.

    Gamma[i, j] is a 3×3 matrix; output[A, B] = Re tr(Σ_{ij} frame[A,i] Γ[i,j] frame[B,j]).
    """
    out = np.zeros((3, 3), dtype=float)
    for A in range(3):
        for B in range(3):
            acc = np.zeros((3, 3), dtype=np.complex128)
            for i in range(3):
                for j in range(3):
                    acc += frame[A, i] * frame[B, j] * Gamma[i, j]
            out[A, B] = float(np.real(np.trace(acc)))
    return out


# ============================================================
# Full Stage U2 pipeline (convenience wrapper)
# ============================================================

def full_stage_U2_pipeline(
    Psi0: np.ndarray,
    patch_centers: np.ndarray,
    q0: float,
    hessian_fn: Callable[[np.ndarray], np.ndarray],
    params: Dict[str, Any],
    *,
    n_modes: int = 1,
    tol: Optional[float] = None,
    dk_steps: int = 2,
    fd_order: int = 4,
    include_lowdin: bool = True,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Run the complete Stage U2 extraction pipeline:

        L(k) → P*K_iP* → (λ_∥, α, β)

    Steps
    -----
    1. bloch_matrices_all_patches : compute L(G*_α) and K_i(G*_α) for all patches
    2. condensate_projector_all   : build P*_α from near-zero modes of L(G*_α)
    3. stiffness_tensor_full      : compute Γ_{ij}, Löwdin correction, extract (λ_∥, α, β)
    4. Collect and report results

    Parameters
    ----------
    Psi0          : (3, Nx, Ny, Nz) converged condensate
    patch_centers : (Npatch, 3) unit vectors ĝ_α (from patch_centers.npy)
    q0            : float   ordering wavevector radius
    hessian_fn    : callable  v → hessian_vec(Psi0, v, params)  (backend API)
    params        : dict    solver parameters
    n_modes       : int     number of condensate modes per patch
    tol           : float   eigenvalue tolerance for mode selection (None = use n_modes)
    dk_steps      : int     Richardson steps for K_i computation
    fd_order      : int     2 or 4  (finite-difference order)
    include_lowdin: bool    include second-order Löwdin correction to Γ
    verbose       : bool

    Returns
    -------
    dict with keys:
        "bloch"     : list of dicts from bloch_matrices_all_patches()
        "projector" : list of ProjectorResult
        "transport" : list of TransportResult
        "summary"   : dict  (mean λ_∥, α, β, gap, hermiticity stats)
    """
    if verbose:
        print("=" * 60)
        print("Stage U2: Bloch-operator extraction")
        print(f"  Ψ₀ shape: {Psi0.shape}")
        print(f"  N_patches: {patch_centers.shape[0]}")
        print(f"  q₀ = {q0:.6f}")
        print(f"  fd_order = {fd_order}  dk_steps = {dk_steps}")
        print("=" * 60)

    # --- Step 1: Bloch matrices ---
    if verbose:
        print("\n[Step 1] Computing Bloch matrices L(G*) and K_i(G*)...")
    bloch_res = bloch_matrices_all_patches(
        Psi0, patch_centers, q0, hessian_fn, params,
        dk_steps=dk_steps, fd_order=fd_order,
        compute_K=True, verbose=verbose,
    )

    # --- Step 2: Spectral projectors ---
    if verbose:
        print("\n[Step 2] Building spectral projectors P*...")
    proj_res = condensate_projector_all(
        bloch_res,
        n_modes=n_modes,
        tol=tol,
        verbose=verbose,
    )

    # Verify projectors
    if verbose:
        for pr in proj_res:
            chk = verify_projector(pr)
            status = "OK" if chk["all_pass"] else "WARN"
            print(f"  Patch {pr.patch_idx} [{status}]: "
                  f"idem={chk['idem_dev']:.2e} herm={chk['herm_dev']:.2e} "
                  f"rank={pr.n_modes}")

    # --- Step 3: Transport coefficients ---
    if verbose:
        print("\n[Step 3] Computing Γ_{ij} and extracting (λ_∥, α, β)...")
    transport_res = stiffness_tensor_full(
        bloch_res, proj_res, Psi0, hessian_fn, params,
        fd_order=fd_order,
        include_lowdin=include_lowdin,
        verbose=verbose,
    )

    # --- Step 4: Summary statistics ---
    # Use renamed stiff fields
    lam_pars = [tr.lambda_par_stiff for tr in transport_res]
    alphas   = [tr.alpha_stiff      for tr in transport_res]
    betas    = [tr.beta_stiff       for tr in transport_res]
    gaps     = [tr.gap              for tr in transport_res]
    hdevs    = [pr.herm_dev         for pr in proj_res]

    summary = {
        "n_patches"              : len(transport_res),
        # second-order stiffness quantities (Γ_∥∥, Γ_11, Γ_22)
        "lambda_par_stiff_mean"  : float(np.mean(lam_pars)) if lam_pars else float("nan"),
        "lambda_par_stiff_std"   : float(np.std(lam_pars))  if lam_pars else float("nan"),
        "alpha_stiff_mean"       : float(np.mean(alphas))   if alphas   else float("nan"),
        "alpha_stiff_std"        : float(np.std(alphas))    if alphas   else float("nan"),
        "beta_stiff_mean"        : float(np.mean(betas))    if betas    else float("nan"),
        "beta_stiff_std"         : float(np.std(betas))     if betas    else float("nan"),
        "gap_min"                : float(np.min(gaps))      if gaps     else float("nan"),
        "gap_mean"               : float(np.mean(gaps))     if gaps     else float("nan"),
        "herm_dev_max"           : float(np.max(hdevs))     if hdevs    else float("nan"),
    }

    if verbose:
        print("\n" + "=" * 60)
        print("Stage U2 summary (second-order stiffness, not theorem-level Dirac coefficients):")
        print(f"  Γ_∥∥  = {summary['lambda_par_stiff_mean']:.6e}  ± {summary['lambda_par_stiff_std']:.2e}")
        print(f"  Γ_11  = {summary['alpha_stiff_mean']:.6e}  ± {summary['alpha_stiff_std']:.2e}")
        print(f"  Γ_22  = {summary['beta_stiff_mean']:.6e}  ± {summary['beta_stiff_std']:.2e}")
        print(f"  spectral gap (min) = {summary['gap_min']:.4e}")
        print(f"  max Hermitian deviation = {summary['herm_dev_max']:.2e}")
        print("=" * 60)

    return {
        "bloch"     : bloch_res,
        "projector" : proj_res,
        "transport" : transport_res,
        "summary"   : summary,
    }


# ============================================================
# Stage U2b: true first-order Dirac-symbol coefficient extractor
# ============================================================

@dataclass
class DiracCoeffResult:
    """
    True first-order Dirac-symbol coefficients at a single G*.

    Physical meaning
    ----------------
    The TECT reduced action near G* has the form

        A₁(p) = λ_∥ p_∥ σ₃ + α(p₁σ₁ + p₂σ₂) + β(−p₂σ₁ + p₁σ₂)

    where p = k − G* is the momentum deviation.  The coefficients (λ_∥, α, β)
    are the expectation values of the projected velocity matrices M_n̂ = P*K_n̂P*
    with respect to the dominant condensate mode u*:

        λ_∥ = Re⟨u*|P*(Σᵢ ĝᵢ Kᵢ)P*|u*⟩
        α   = Re⟨u*|P*(Σᵢ e₁ᵢ Kᵢ)P*|u*⟩
        β   = Re⟨u*|P*(Σᵢ e₂ᵢ Kᵢ)P*|u*⟩

    These are DISTINCT from the second-order stiffness Γ_∥∥, Γ₁₁, Γ₂₂ computed
    in TransportResult.

    Attributes
    ----------
    patch_idx      : int
    G_unit         : (3,) float   ĝ = G_grid / |G_grid|
    e1, e2         : (3,) float   transverse frame directions
    lambda_par     : float   first-order longitudinal coefficient (theorem target)
    alpha          : float   first-order first transverse coefficient
    beta           : float   first-order second transverse coefficient
    lambda_par_imag: float   imaginary part of ⟨u*|M_par|u*⟩ (should be ~0)
    alpha_imag     : float   imaginary part of α
    beta_imag      : float   imaginary part of β
    u_par          : (3,)    dominant condensate mode (longitudinal eigenvector)
    M_par          : (3,3)   P*(Σᵢ ĝᵢ Kᵢ)P*   longitudinal velocity matrix
    M_1            : (3,3)   P*(Σᵢ e₁ᵢ Kᵢ)P*
    M_2            : (3,3)   P*(Σᵢ e₂ᵢ Kᵢ)P*
    M_par_evals    : (n*,)   eigenvalues of M_par projected to V*
    n_modes        : int
    is_physical    : bool    True if |imag/real| < imaginary_tol for all coefficients
    """
    patch_idx      : int
    G_unit         : np.ndarray
    e1             : np.ndarray
    e2             : np.ndarray
    lambda_par     : float
    alpha          : float
    beta           : float
    lambda_par_imag: float
    alpha_imag     : float
    beta_imag      : float
    u_par          : np.ndarray
    M_par          : np.ndarray
    M_1            : np.ndarray
    M_2            : np.ndarray
    M_par_evals    : np.ndarray
    n_modes        : int
    is_physical    : bool
    # --- U2b-final (Pauli 2×2 block) ---
    pauli_decomp   : Optional["PauliDecomp2x2Result"] = field(default=None)
    extraction_method: str = field(default="expectation_value")


# ============================================================
# U2b-final: Pauli decomposition on the 2×2 doubled low-slot
# ============================================================

@dataclass
class PauliDecomp2x2Result:
    """
    Full 2×2 Pauli decomposition of the low-slot projected velocity block.

    For a doubled low-slot (n*=2), the theorem (TECT-Math21, §Shell Projection)
    asserts the Pauli ansatz:

        M_∥ = λ_∥ σ₃
        M₁  = α σ₁ + β σ₂
        M₂  = α σ₂ − β σ₁

    Extraction is exact via Pauli traces:

        λ_∥ = (1/2) Re Tr(σ₃ M_∥|_{V*})
        α   = (1/4) Re Tr(σ₁ M₁|_{V*} + σ₂ M₂|_{V*})
        β   = (1/4) Re Tr(σ₂ M₁|_{V*} − σ₁ M₂|_{V*})

    Residual norms measure how well the Pauli ansatz is satisfied:

        res_par = ‖M_∥|_{V*} − λ_∥ σ₃‖_F / max(‖M_∥|_{V*}‖_F, 1e-14)
        res_1   = ‖M₁|_{V*}  − α σ₁ − β σ₂‖_F / max(‖M₁|_{V*}‖_F, 1e-14)
        res_2   = ‖M₂|_{V*}  − α σ₂ + β σ₁‖_F / max(‖M₂|_{V*}‖_F, 1e-14)

    Attributes
    ----------
    patch_idx     : int
    M_par_small   : (2,2) complex  M_∥ restricted to V*
    M_1_small     : (2,2) complex  M₁ restricted to V*
    M_2_small     : (2,2) complex  M₂ restricted to V*
    lambda_par    : float   (1/2) Re Tr(σ₃ M_∥|_{V*})
    alpha         : float   (1/4) Re Tr(σ₁ M₁|_{V*} + σ₂ M₂|_{V*})
    beta          : float   (1/4) Re Tr(σ₂ M₁|_{V*} − σ₁ M₂|_{V*})
    lambda_par_imag: float  imaginary part of Pauli extraction (should be ≈0)
    alpha_imag    : float
    beta_imag     : float
    res_par       : float   Frobenius residual for M_∥ = λ_∥ σ₃ ansatz
    res_1         : float   Frobenius residual for M₁ = α σ₁ + β σ₂ ansatz
    res_2         : float   Frobenius residual for M₂ = α σ₂ − β σ₁ ansatz
    pauli_ansatz_ok: bool   True if all residuals < residual_tol
    n_modes       : int     must be 2
    """
    patch_idx     : int
    M_par_small   : np.ndarray      # (2,2) complex
    M_1_small     : np.ndarray      # (2,2) complex
    M_2_small     : np.ndarray      # (2,2) complex
    lambda_par    : float
    alpha         : float
    beta          : float
    lambda_par_imag: float
    alpha_imag    : float
    beta_imag     : float
    res_par       : float
    res_1         : float
    res_2         : float
    pauli_ansatz_ok: bool
    n_modes       : int = 2


# --- Pauli matrices (constant, lazy-initialised) ---
_SIGMA1 = np.array([[0, 1], [1, 0]],   dtype=np.complex128)
_SIGMA2 = np.array([[0,-1j],[1j,0]],   dtype=np.complex128)
_SIGMA3 = np.array([[1, 0], [0,-1]],   dtype=np.complex128)


def _pauli_trace_extract(
    M_par_s: np.ndarray,
    M_1_s:   np.ndarray,
    M_2_s:   np.ndarray,
) -> Tuple[complex, complex, complex]:
    """
    Exact Pauli projector-trace formulas (TECT-Math21, §Coefficient Extraction):

        λ_∥ = (1/2) Tr(σ₃ M_∥)
        α   = (1/4) Tr(σ₁ M₁ + σ₂ M₂)
        β   = (1/4) Tr(σ₂ M₁ − σ₁ M₂)

    All matrices are assumed to be 2×2.  Returns complex scalars; the calling
    routine inspects real and imaginary parts separately.
    """
    lam_c = 0.5  * np.trace(_SIGMA3 @ M_par_s)
    alp_c = 0.25 * np.trace(_SIGMA1 @ M_1_s + _SIGMA2 @ M_2_s)
    bet_c = 0.25 * np.trace(_SIGMA2 @ M_1_s - _SIGMA1 @ M_2_s)
    return complex(lam_c), complex(alp_c), complex(bet_c)


def _frobenius_residual(M: np.ndarray, M_approx: np.ndarray) -> float:
    """‖M − M_approx‖_F / max(‖M‖_F, 1e-14)."""
    diff = M - M_approx
    norm_M = max(np.linalg.norm(M, 'fro'), 1e-14)
    return float(np.linalg.norm(diff, 'fro') / norm_M)


def pauli_dirac_2x2(
    tr: "TransportResult",
    pr: "ProjectorResult",
    *,
    imaginary_tol: float = 1e-3,
    residual_tol:  float = 1e-4,
    verbose:       bool  = False,
) -> PauliDecomp2x2Result:
    """
    U2b-final: extract (λ_∥, α, β) from the 2×2 doubled low-slot block.

    Implements the exact Pauli-trace formulas of TECT-Math21 §Shell Projection:

        M_∥|_{V*} = U*† M_∥ U*     (2×2 in the V* basis)

    Then:
        λ_∥ = (1/2) Re Tr(σ₃ M_∥|_{V*})
        α   = (1/4) Re Tr(σ₁ M₁|_{V*} + σ₂ M₂|_{V*})
        β   = (1/4) Re Tr(σ₂ M₁|_{V*} − σ₁ M₂|_{V*})

    Residual verification checks whether the Pauli ansatz
        M_∥|_{V*} ≈ λ_∥ σ₃,   M₁|_{V*} ≈ α σ₁ + β σ₂,   M₂|_{V*} ≈ α σ₂ − β σ₁
    is satisfied to within `residual_tol` in Frobenius norm.

    Parameters
    ----------
    tr            : TransportResult  (contains M[3], G_unit, e1, e2)
    pr            : ProjectorResult  (contains P_star, eigenvectors, mode_mask)
    imaginary_tol : float   warn if |Im/Re| > this for extracted complex scalar
    residual_tol  : float   warn if Frobenius residual of Pauli ansatz > this
    verbose       : bool

    Raises
    ------
    ValueError  if n* ≠ 2 (this function is specific to the doubled low-slot)

    Returns
    -------
    PauliDecomp2x2Result
    """
    idx_modes = np.where(pr.mode_mask)[0]
    n_star    = len(idx_modes)
    if n_star != 2:
        raise ValueError(
            f"pauli_dirac_2x2 requires n*=2 (doubled low-slot); got n*={n_star}."
            "  Use first_order_dirac_coefficients() for n*=1."
        )

    M_arr  = np.asarray(tr.M,     dtype=np.complex128)  # (3, 3, 3)
    G_unit = np.asarray(tr.G_unit, dtype=float)
    e1     = np.asarray(tr.e1,     dtype=float)
    e2     = np.asarray(tr.e2,     dtype=float)

    # 1. Frame-projected full-space matrices
    M_par_full = sum(G_unit[i] * M_arr[i] for i in range(3))  # (3,3)
    M_1_full   = sum(e1[i]     * M_arr[i] for i in range(3))
    M_2_full   = sum(e2[i]     * M_arr[i] for i in range(3))

    # 2. Restrict to 2-dimensional V* via U* = [u₀, u₁]
    U_star = pr.eigenvectors[:, idx_modes]   # (3, 2)
    M_par_s = U_star.conj().T @ M_par_full @ U_star   # (2,2)
    M_1_s   = U_star.conj().T @ M_1_full   @ U_star
    M_2_s   = U_star.conj().T @ M_2_full   @ U_star

    # 3. Pauli trace extraction (exact, from TECT-Math21 §Coefficient Extraction)
    lam_c, alp_c, bet_c = _pauli_trace_extract(M_par_s, M_1_s, M_2_s)

    # 4. Residual verification (Pauli ansatz quality)
    M_par_ansatz = lam_c.real * _SIGMA3
    M_1_ansatz   = alp_c.real * _SIGMA1 + bet_c.real * _SIGMA2
    M_2_ansatz   = alp_c.real * _SIGMA2 - bet_c.real * _SIGMA1

    res_par = _frobenius_residual(M_par_s, M_par_ansatz)
    res_1   = _frobenius_residual(M_1_s,   M_1_ansatz)
    res_2   = _frobenius_residual(M_2_s,   M_2_ansatz)
    pauli_ansatz_ok = all(r < residual_tol for r in [res_par, res_1, res_2])

    if not pauli_ansatz_ok:
        warnings.warn(
            f"Patch {tr.patch_idx}: Pauli ansatz residuals ({res_par:.2e}, "
            f"{res_1:.2e}, {res_2:.2e}) exceed tol={residual_tol:.1e}.  "
            "Locked Pauli selection rule may not hold at this condensate."
        )

    # 5. Imaginary-part check
    _ref = max(abs(lam_c), 1e-14)
    def _ir(c: complex) -> float:
        return abs(c.imag) / max(abs(c.real), _ref * 1e-6, 1e-30)
    lam_ir, alp_ir, bet_ir = _ir(lam_c), _ir(alp_c), _ir(bet_c)
    is_physical = all(r < imaginary_tol for r in [lam_ir, alp_ir, bet_ir])

    if not is_physical:
        warnings.warn(
            f"Patch {tr.patch_idx}: Pauli extraction imaginary parts large "
            f"(|Im/Re| λ_∥={lam_ir:.2e}, α={alp_ir:.2e}, β={bet_ir:.2e})."
        )

    if verbose:
        print(
            f"  [Pauli 2×2] Patch {tr.patch_idx}: "
            f"λ_∥={lam_c.real:.6e}(+{lam_c.imag:.1e}i)  "
            f"α={alp_c.real:.6e}  β={bet_c.real:.6e}  "
            f"res=({res_par:.2e},{res_1:.2e},{res_2:.2e})"
            f"  {'OK' if pauli_ansatz_ok else 'WARN'}"
        )

    return PauliDecomp2x2Result(
        patch_idx       = tr.patch_idx,
        M_par_small     = np.asarray(M_par_s, dtype=np.complex128),
        M_1_small       = np.asarray(M_1_s,   dtype=np.complex128),
        M_2_small       = np.asarray(M_2_s,   dtype=np.complex128),
        lambda_par      = float(lam_c.real),
        alpha           = float(alp_c.real),
        beta            = float(bet_c.real),
        lambda_par_imag = float(lam_c.imag),
        alpha_imag      = float(alp_c.imag),
        beta_imag       = float(bet_c.imag),
        res_par         = res_par,
        res_1           = res_1,
        res_2           = res_2,
        pauli_ansatz_ok = pauli_ansatz_ok,
        n_modes         = 2,
    )


def pauli_dirac_all_patches(
    transport_results: List["TransportResult"],
    proj_results:      List["ProjectorResult"],
    *,
    imaginary_tol: float = 1e-3,
    residual_tol:  float = 1e-4,
    verbose:       bool  = False,
) -> List[PauliDecomp2x2Result]:
    """
    Run pauli_dirac_2x2() over all patches.  Patches with n*≠2 raise ValueError.

    Returns list of PauliDecomp2x2Result, one per patch.
    """
    if len(transport_results) != len(proj_results):
        raise ValueError("transport_results and proj_results must have equal length")
    if verbose:
        print("\n[Stage U2b-final] Pauli 2×2 block decomposition")
    results = []
    for tr, pr in zip(transport_results, proj_results):
        pd2 = pauli_dirac_2x2(tr, pr,
                               imaginary_tol=imaginary_tol,
                               residual_tol=residual_tol,
                               verbose=verbose)
        results.append(pd2)
    return results


def pauli_decomp_text_report(pd_results: List[PauliDecomp2x2Result]) -> str:
    """Plain-text table: Pauli-trace (λ_∥, α, β) with Frobenius residuals."""
    hdr = (
        f"{'Patch':>5}  {'λ_∥':>14}  {'α':>14}  {'β':>14}  "
        f"{'res_∥':>8}  {'res_1':>8}  {'res_2':>8}  {'Pauli':>6}"
    )
    rows = [hdr, "-" * 84]
    for pd in pd_results:
        rows.append(
            f"{pd.patch_idx:>5}  {pd.lambda_par:>14.6e}  "
            f"{pd.alpha:>14.6e}  {pd.beta:>14.6e}  "
            f"{pd.res_par:>8.2e}  {pd.res_1:>8.2e}  {pd.res_2:>8.2e}  "
            f"{'OK' if pd.pauli_ansatz_ok else 'WARN':>6}"
        )
    return "\n".join(rows)


def pauli_decomp_latex_table(
    pd_results: List[PauliDecomp2x2Result],
    *,
    label:   str = "tab:pauli_coeffs",
    caption: str = (
        r"TECT Stage U2b-final: Pauli-trace extraction "
        r"$(\lambda_\parallel, \alpha, \beta)$ from the doubled low-slot "
        r"$2\times2$ block.  Columns $r_\parallel, r_1, r_2$ are "
        r"Frobenius residuals of the Pauli ansatz."
    ),
) -> str:
    """LaTeX table for PRL-style paper."""
    lines = [
        r"\begin{table}[h]",
        r"\centering",
        r"\caption{" + caption + r"}",
        r"\label{" + label + r"}",
        r"\begin{tabular}{ccccccc}",
        r"\hline\hline",
        (r"Patch & $\lambda_\parallel$ & $\alpha$ & $\beta$ & "
         r"$r_\parallel$ & $r_1$ & $r_2$ \\"),
        r"\hline",
    ]
    for pd in pd_results:
        lines.append(
            f"  {pd.patch_idx} & {pd.lambda_par:.4e} & "
            f"{pd.alpha:.4e} & {pd.beta:.4e} & "
            f"{pd.res_par:.2e} & {pd.res_1:.2e} & {pd.res_2:.2e} \\\\"
        )
    lines += [r"\hline\hline", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines)


def first_order_dirac_coefficients(
    tr: "TransportResult",
    pr: "ProjectorResult",
    *,
    imaginary_tol: float = 1e-3,
    verbose: bool = False,
) -> DiracCoeffResult:
    """
    Extract true first-order Dirac-symbol coefficients (λ_∥, α, β) from the
    already-computed M_i = P*K_iP* matrices stored in TransportResult.

    Algorithm
    ---------
    1. Build frame-projected velocity matrices:
           M_par = Σᵢ ĝᵢ · M[i]      (longitudinal, 3×3)
           M_1   = Σᵢ e₁ᵢ · M[i]    (first transverse)
           M_2   = Σᵢ e₂ᵢ · M[i]    (second transverse)

    2. Restrict M_par to the condensate subspace V* (dimension n*):
           M_par|_{V*} = U*† M_par U*    (n* × n*)
       where U* = [u_j] columns = condensate eigenvectors from ProjectorResult.

    3. For n* = 1 (standard case):
           λ_∥ = Re⟨u*|M_par|u*⟩
           α   = Re⟨u*|M_1|u*⟩
           β   = Re⟨u*|M_2|u*⟩
           u_par = u*

    4. For n* > 1:
       Eigendecompose M_par|_{V*}, select eigenvector with largest |eigenvalue|.
       Use this as u_par; project M_1, M_2 along u_par.

    Parameters
    ----------
    tr             : TransportResult (contains M, G_unit, e1, e2)
    pr             : ProjectorResult (contains P_star, eigenvectors, mode_mask)
    imaginary_tol  : float   warn if |Im/Re| > this for any coefficient
    verbose        : bool

    Returns
    -------
    DiracCoeffResult
    """
    M_arr  = np.asarray(tr.M,     dtype=np.complex128)  # (3, 3, 3)
    G_unit = np.asarray(tr.G_unit, dtype=float)
    e1     = np.asarray(tr.e1,     dtype=float)
    e2     = np.asarray(tr.e2,     dtype=float)

    # --- Step 1: frame-projected velocity matrices ---
    M_par = sum(G_unit[i] * M_arr[i] for i in range(3))  # (3,3)
    M_1   = sum(e1[i]     * M_arr[i] for i in range(3))
    M_2   = sum(e2[i]     * M_arr[i] for i in range(3))

    # --- Step 2: condensate basis ---
    idx_modes = np.where(pr.mode_mask)[0]
    U_star    = pr.eigenvectors[:, idx_modes]   # (3, n*)
    n_star    = len(idx_modes)

    # --- Step 3/4: extract coefficients ---
    _pauli_result: Optional[PauliDecomp2x2Result] = None
    _extr_method  = "expectation_value"

    if n_star == 1:
        u_par = U_star[:, 0]                          # (3,)
        lam_c  = complex(u_par.conj() @ M_par @ u_par)
        alp_c  = complex(u_par.conj() @ M_1   @ u_par)
        bet_c  = complex(u_par.conj() @ M_2   @ u_par)
        M_par_evals = np.array([lam_c.real])

    elif n_star == 2:
        # --- U2b-final: exact Pauli-trace extraction on the 2×2 block ---
        _pauli_result = pauli_dirac_2x2(
            tr, pr, imaginary_tol=imaginary_tol, verbose=verbose
        )
        _extr_method = "pauli_2x2"
        lam_c = complex(_pauli_result.lambda_par, _pauli_result.lambda_par_imag)
        alp_c = complex(_pauli_result.alpha,      _pauli_result.alpha_imag)
        bet_c = complex(_pauli_result.beta,        _pauli_result.beta_imag)
        # u_par = σ₃ dominant eigenvector (upper basis state of V*)
        # Convention: σ₃ eigenvalue +1 → u_par = U* @ [1,0]
        M_par_s = U_star.conj().T @ M_par @ U_star          # (2,2)
        M_sym   = 0.5 * (M_par_s + M_par_s.conj().T)
        evals_p, evecs_p = np.linalg.eigh(M_sym)
        best = int(np.argmax(np.abs(evals_p)))
        u_par  = U_star @ evecs_p[:, best]               # (3,) in full basis
        M_par_evals = evals_p.real

    else:
        # n* > 2: eigendecompose-and-project fallback (warns, not Pauli-exact)
        warnings.warn(
            f"Patch {tr.patch_idx}: n*={n_star} > 2.  Using dominant-eigenmode "
            "expectation value; Pauli 2×2 ansatz not applicable."
        )
        M_par_small = U_star.conj().T @ M_par @ U_star      # (n*, n*)
        M_sym       = 0.5 * (M_par_small + M_par_small.conj().T)
        evals_p, evecs_p = np.linalg.eigh(M_sym)
        best   = int(np.argmax(np.abs(evals_p)))
        v_best = evecs_p[:, best]
        u_par  = U_star @ v_best
        M_1_small = U_star.conj().T @ M_1 @ U_star
        M_2_small = U_star.conj().T @ M_2 @ U_star
        lam_c = complex(v_best.conj() @ M_par_small @ v_best)
        alp_c = complex(v_best.conj() @ M_1_small   @ v_best)
        bet_c = complex(v_best.conj() @ M_2_small   @ v_best)
        M_par_evals = evals_p.real

    # Imaginary-part check
    # Use |λ_∥| as global reference scale so that α, β with Re≈0 (physically correct
    # zero by isotropy) are not falsely flagged when |Im| is also at machine precision.
    _ref_scale = max(abs(lam_c), 1e-14)

    def _imag_ratio(c: complex) -> float:
        # Denominator: local |Re| OR 1e-6·λ_ref (prevents 1/0 for structurally-zero coefficients)
        return abs(c.imag) / max(abs(c.real), _ref_scale * 1e-6, 1e-30)

    lam_ir = _imag_ratio(lam_c)
    alp_ir = _imag_ratio(alp_c)
    bet_ir = _imag_ratio(bet_c)
    is_physical = all(r < imaginary_tol for r in [lam_ir, alp_ir, bet_ir])

    if not is_physical:
        import warnings as _w
        _w.warn(
            f"Patch {tr.patch_idx}: large imaginary parts in Dirac coefficients "
            f"(|Im/Re| λ_∥={lam_ir:.2e}, α={alp_ir:.2e}, β={bet_ir:.2e}).  "
            "Non-Hermitian L or insufficient convergence of Ψ₀ suspected."
        )

    if verbose:
        print(
            f"  Patch {tr.patch_idx}: λ_∥ = {lam_c.real:.6e} (+{lam_c.imag:.2e}i)  "
            f"α = {alp_c.real:.6e} (+{alp_c.imag:.2e}i)  "
            f"β = {bet_c.real:.6e} (+{bet_c.imag:.2e}i)"
        )

    return DiracCoeffResult(
        patch_idx          = tr.patch_idx,
        G_unit             = G_unit,
        e1                 = e1,
        e2                 = e2,
        lambda_par         = float(lam_c.real),
        alpha              = float(alp_c.real),
        beta               = float(bet_c.real),
        lambda_par_imag    = float(lam_c.imag),
        alpha_imag         = float(alp_c.imag),
        beta_imag          = float(bet_c.imag),
        u_par              = u_par,
        M_par              = np.asarray(M_par, dtype=np.complex128),
        M_1                = np.asarray(M_1,   dtype=np.complex128),
        M_2                = np.asarray(M_2,   dtype=np.complex128),
        M_par_evals        = M_par_evals,
        n_modes            = n_star,
        is_physical        = is_physical,
        pauli_decomp       = _pauli_result,
        extraction_method  = _extr_method,
    )


def dirac_coefficients_all_patches(
    transport_results: List["TransportResult"],
    proj_results: List["ProjectorResult"],
    *,
    imaginary_tol: float = 1e-3,
    verbose: bool = False,
) -> List[DiracCoeffResult]:
    """
    Run first_order_dirac_coefficients() for every patch.

    Parameters
    ----------
    transport_results : output of stiffness_tensor_full()
    proj_results      : output of condensate_projector_all()
    imaginary_tol     : float
    verbose           : bool

    Returns
    -------
    list of DiracCoeffResult, one per patch
    """
    if len(transport_results) != len(proj_results):
        raise ValueError("transport_results and proj_results must have equal length")

    if verbose:
        print("\n[Stage U2b] First-order Dirac-symbol coefficient extraction")

    results = []
    for tr, pr in zip(transport_results, proj_results):
        dr = first_order_dirac_coefficients(tr, pr,
                                            imaginary_tol=imaginary_tol,
                                            verbose=verbose)
        results.append(dr)

    return results


def dirac_coeff_text_report(dirac_results: List[DiracCoeffResult]) -> str:
    """Plain-text table of true first-order Dirac coefficients."""
    rows = [
        f"{'Patch':>5}  {'λ_∥':>16}  {'α':>16}  {'β':>16}  "
        f"{'|Im/Re|_λ':>10}  {'phys':>5}"
    ]
    rows.append("-" * 75)
    for dr in dirac_results:
        lam_ir = abs(dr.lambda_par_imag) / max(abs(dr.lambda_par), 1e-30)
        rows.append(
            f"{dr.patch_idx:>5}  {dr.lambda_par:>16.6e}  "
            f"{dr.alpha:>16.6e}  {dr.beta:>16.6e}  "
            f"{lam_ir:>10.2e}  {'OK' if dr.is_physical else 'WARN':>5}"
        )
    return "\n".join(rows)


def dirac_coeff_latex_table(
    dirac_results: List[DiracCoeffResult],
    *,
    label:   str = "tab:dirac_coeffs",
    caption: str = "TECT Stage U2b: first-order Dirac-symbol coefficients.",
) -> str:
    """LaTeX table of (λ_∥, α, β) per patch."""
    lines = [
        r"\begin{table}[h]",
        r"\centering",
        r"\caption{" + caption + r"}",
        r"\label{" + label + r"}",
        r"\begin{tabular}{cccc}",
        r"\hline\hline",
        r"Patch & $\lambda_\parallel$ & $\alpha$ & $\beta$ \\",
        r"\hline",
    ]
    for dr in dirac_results:
        lines.append(
            f"  {dr.patch_idx} & {dr.lambda_par:.4e} "
            f"& {dr.alpha:.4e} & {dr.beta:.4e} \\\\"
        )
    lines += [r"\hline\hline", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines)


# ============================================================
# Reporting
# ============================================================

def transport_text_report(transport_results: List[TransportResult]) -> str:
    """Plain-text summary table for terminal output.

    Columns are second-order stiffness quantities (Γ_∥∥, Γ_11, Γ_22),
    not the theorem-level first-order Dirac coefficients.
    """
    rows = [
        f"{'Patch':>5}  {'|G*|':>8}  {'Γ_∥∥(stiff)':>16}  "
        f"{'Γ_11(stiff)':>16}  {'Γ_22(stiff)':>16}  {'gap':>10}  {'n*':>3}"
    ]
    rows.append("-" * 82)
    for tr in transport_results:
        kmag = float(np.linalg.norm(tr.G_grid))
        rows.append(
            f"{tr.patch_idx:>5}  {kmag:>8.4f}  "
            f"{tr.lambda_par_stiff:>16.6e}  "
            f"{tr.alpha_stiff:>16.6e}  {tr.beta_stiff:>16.6e}  "
            f"{tr.gap:>10.4e}  {tr.n_modes:>3}"
        )
    return "\n".join(rows)


def transport_latex_table(
    transport_results: List[TransportResult],
    *,
    label: str = "tab:transport",
    caption: str = "TECT Stage U2 transport coefficients.",
) -> str:
    """
    Generate a complete LaTeX table of (λ_∥, α, β) results.

    Returns a string containing \\begin{table}...\\end{table}.
    """
    lines = [
        r"\begin{table}[h]",
        r"\centering",
        r"\caption{" + caption + r"}",
        r"\label{" + label + r"}",
        r"\begin{tabular}{cccccc}",
        r"\hline\hline",
        r"Patch & $|\mathbf{G}^*|$ & $\Gamma_{\parallel\parallel}$ "
        r"& $\Gamma_{11}$ & $\Gamma_{22}$ & Gap \\",
        r"& & (2nd-order stiffness) & & & \\",
        r"\hline",
    ]
    for tr in transport_results:
        kmag = float(np.linalg.norm(tr.G_grid))
        lines.append(
            f"  {tr.patch_idx} & {kmag:.4f} "
            f"& {tr.lambda_par_stiff:.4e} & {tr.alpha_stiff:.4e} & {tr.beta_stiff:.4e} "
            f"& {tr.gap:.4e} \\\\"
        )
    lines += [
        r"\hline\hline",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines)


# ============================================================
# Command-line entry point
# ============================================================

def main():
    """
    CLI wrapper: load Ψ₀ and patch data from a TECT solver output directory
    and run the full Stage U2 pipeline.

    Usage
    -----
        python transport_extractor.py <output_dir> [--backend <backend_module>]
                                       [--n-modes N] [--fd-order 2|4] [--verbose]

    The output_dir must contain:
        Psi_final.npy       converged field  (3, Nx, Ny, Nz)
        params.json         solver parameters
        patch_centers.npy   patch centre unit vectors (Npatch, 3)

    Results are printed to stdout.  Add --save to write JSON + LaTeX files.
    """
    import argparse
    import json
    import sys
    import os

    parser = argparse.ArgumentParser(description="TECT Stage U2: transport extraction")
    parser.add_argument("output_dir",  type=str,  help="Solver output directory")
    parser.add_argument("--backend",   type=str,  default="real_backend_pt_bcc_mixed_v3",
                        help="Backend module name")
    parser.add_argument("--n-modes",   type=int,  default=1)
    parser.add_argument("--fd-order",  type=int,  default=4, choices=[2, 4])
    parser.add_argument("--dk-steps",  type=int,  default=2)
    parser.add_argument("--no-lowdin", action="store_true")
    parser.add_argument("--save",      action="store_true", help="Save results to output_dir")
    parser.add_argument("--verbose",   action="store_true")
    args = parser.parse_args()

    out_dir = args.output_dir

    # --- Load Ψ₀: accept Psi_corr.npy (current solver export) or Psi_final.npy ---
    psi_candidates = ["Psi_corr.npy", "Psi_final.npy"]
    Psi0 = None
    for psi_name in psi_candidates:
        psi_path = os.path.join(out_dir, psi_name)
        if os.path.exists(psi_path):
            Psi0 = np.load(psi_path)
            print(f"Loaded field from: {psi_path}  shape={Psi0.shape}")
            break
    if Psi0 is None:
        raise FileNotFoundError(
            f"No field file found in {out_dir}.  "
            f"Expected one of: {psi_candidates}"
        )

    # --- Load params: accept config.json (current solver) or params.json ---
    cfg_candidates = ["config.json", "params.json"]
    params = None
    for cfg_name in cfg_candidates:
        cfg_path = os.path.join(out_dir, cfg_name)
        if os.path.exists(cfg_path):
            with open(cfg_path) as f:
                params = json.load(f)
            print(f"Loaded params from: {cfg_path}")
            break
    if params is None:
        raise FileNotFoundError(
            f"No parameter file found in {out_dir}.  "
            f"Expected one of: {cfg_candidates}"
        )

    # --- Load patch centres ---
    patch_path = os.path.join(out_dir, "patch_centers.npy")
    if not os.path.exists(patch_path):
        raise FileNotFoundError(f"patch_centers.npy not found in {out_dir}")
    patch_centers = np.load(patch_path)
    q0 = float(params["q0"])

    # Load backend
    sys.path.insert(0, out_dir)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    backend = load_backend_module(args.backend)

    Psi0_ref = Psi0.copy()
    hessian_fn = lambda v: backend.hessian_vec(Psi0_ref, v, params)

    # Run pipeline
    pipeline_out = full_stage_U2_pipeline(
        Psi0, patch_centers, q0, hessian_fn, params,
        n_modes        = args.n_modes,
        dk_steps       = args.dk_steps,
        fd_order       = args.fd_order,
        include_lowdin = not args.no_lowdin,
        verbose        = args.verbose,
    )

    # Print reports
    print("\n" + transport_text_report(pipeline_out["transport"]))
    print("\n" + transport_latex_table(pipeline_out["transport"]))

    # U2b: first-order Dirac coefficients
    dirac_res = dirac_coefficients_all_patches(
        pipeline_out["transport"],
        pipeline_out["projector"],
        verbose=args.verbose,
    )
    print("\n" + dirac_coeff_text_report(dirac_res))
    print("\n" + dirac_coeff_latex_table(dirac_res))

    if args.save:
        import json as jmod
        summary = pipeline_out["summary"]
        summary_path = os.path.join(out_dir, "stage_U2_summary.json")
        table_path   = os.path.join(out_dir, "stage_U2_stiffness_table.tex")
        dirac_path   = os.path.join(out_dir, "stage_U2b_dirac_table.tex")
        with open(summary_path, "w") as f:
            jmod.dump(summary, f, indent=2)
        with open(table_path, "w") as f:
            f.write(transport_latex_table(pipeline_out["transport"]))
        with open(dirac_path, "w") as f:
            f.write(dirac_coeff_latex_table(dirac_res))
        print(f"\nResults saved to:\n  {summary_path}\n  {table_path}\n  {dirac_path}")


if __name__ == "__main__":
    main()
