#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v4.0
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
"""
intervalley_extractor_v4.py — TECT cross-patch intervalley Gate WITNESS extractor
==================================================================================

PURPOSE
-------
Compute cross-patch Gates 2 & 3 WITNESS quantities via the 6×6 intervalley
Hessian block for each antipodal BCC wavevector pair (G_+, G_-).

STATUS: strong Gate-witness extractor (NOT the final projector-based coefficient
        extractor).  The exact (λ_∥, α, β) extraction via Pauli-trace formulas
        is implemented in transport_extractor.py (U2b-final module).

This extractor:

  (a)  Uses the full (z₀, χ₁, χ₂) ⊗ (G₊, G₋) = 6×6 basis,
       capturing both longitudinal AND transverse carrier physics.
  (b)  Computes FIRST derivatives ∂H/∂p_i  →  velocity / transport operators.
  (c)  Computes SECOND derivatives ∂²H/∂p_i∂p_j  →  effective-mass (stiffness) tensor.
  (d)  Extracts cross-patch WITNESS quantities (ℓ_∥^cross, ℓ_I^cross, m_scalar)
       that provide necessary conditions for Gate passage.

NOTE: The quantities ℓ_∥^cross = |Ũ_∥[0,0]| and ℓ_I^cross = |Ũ_I[0,0]| are
      lowest-eigenvector cross-elements, NOT the final theorem-level Pauli-trace
      coefficients (λ_∥, α, β).  Use transport_extractor.py U2b-final for
      the exact projector-based extraction P*K_iP* → Pauli trace.

THEORY
------
At a BCC ordering wavevector G_A with |G_A| = q₀, the linearised Hessian
of the Brazovskii functional around the condensate Ψ₀ has block structure

    H₀(G₊, G₋)  =  ⎡ E₊   B₀ ⎤     ∈ ℂ^{6×6}
                     ⎣ B₀†  E₋ ⎦

where E± ∈ ℂ^{3×3} are the intra-valley blocks and B₀ ∈ ℂ^{3×3} is the
inter-valley coupling.  The 3-dimensional internal basis at each valley is
(z₀, χ₁, χ₂) where z₀ is the condensate polarisation direction and χ₁, χ₂
span the transverse (family) plane.

The first derivative of H₀ with respect to carrier momentum p:

    ∂H/∂p_i  =  ⎡ ∂E₊/∂p_i   ∂B₀/∂p_i ⎤
                 ⎣ (∂B₀/∂p_i)† ∂E₋/∂p_i ⎦

yields the velocity/transport operators.  Projected along the BCC valley
direction n̂ = G₊/|G₊| and two transverse directions e₁, e₂:

    V_∥  = n̂_i (∂H/∂p_i)        longitudinal velocity operator
    V_I  = (e_I)_i (∂H/∂p_i)    transverse velocity operators (I = 1,2)

The second derivative:

    Γ_{ij} = ∂²H / ∂p_i ∂p_j   →   mass / stiffness tensor

GATE DEFINITIONS (TECT-Math18/Math30)
-------------------------------------
Let u*₊ be the lowest eigenvector of E₊, and u*₋ that of E₋.

  Gate 2 (longitudinal carrier):
      ℓ_∥^{cross} = |⟨u*₊ | V_∥^{off} | u*₋⟩|
      where V_∥^{off} = [∂H/∂p_∥]_{0:3, 3:6}   (off-diagonal block)
      PASS if  ∃ pair :  ℓ_∥^{cross} > η_∥

  Gate 3 (transverse carrier):
      ℓ_I^{cross} = |⟨u*₊ | V_I^{off} | u*₋⟩|    (I = 1, 2)
      PASS if  ∃ pair, I :  ℓ_I^{cross} > η_T

  Mass scalar (intervalley):
      m_scalar = |½ Tr(B̃₀)|   where  B̃₀ = U₊† B₀ U₋

  Effective mass (stiffness):
      m²_eff = ⟨u*₊ | Γ_∥∥^{diag} | u*₊⟩   (on-shell mass from second derivative)

BACKEND INTERFACE
-----------------
Requires a backend module that provides:
    hessian_vec(Psi: ndarray, v: ndarray, params: dict) -> ndarray
        The Fréchet derivative of the Euler-Lagrange residual at Psi,
        applied to direction v.  Shape: (3, Nx, Ny, Nz) complex128.

AUTHORS
-------
TECT Research Team — v4 cross-patch Gate WITNESS extractor, aligned with TECT-Math18/Math30.
  NOTE: This module provides gate witnesses (ℓ_∥^cross, ℓ_I^cross), NOT the
        final projector-based Pauli-trace coefficients (λ_∥, α, β).
        For exact Dirac coefficients, see transport_extractor.py (U2b-final).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np


# ============================================================
# Pauli matrices (2×2)
# ============================================================

SIGMA0 = np.eye(2, dtype=np.complex128)
SIGMA1 = np.array([[0, 1], [1, 0]], dtype=np.complex128)
SIGMA2 = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
SIGMA3 = np.array([[1, 0], [0, -1]], dtype=np.complex128)


# ============================================================
# Data containers
# ============================================================

@dataclass
class PairResult:
    """Complete extraction for one antipodal pair (G₊, G₋)."""
    pair_label: str
    patch_plus: int
    patch_minus: int
    G_plus: List[float]
    G_minus: List[float]
    snap_err_plus: float
    snap_err_minus: float

    # Spectral data
    evals_plus: List[float]            # eigenvalues of E₊ (3 values)
    evals_minus: List[float]           # eigenvalues of E₋ (3 values)
    gap_plus: float                    # E₊[1] - E₊[0] intra-valley gap
    gap_minus: float                   # E₋[1] - E₋[0] intra-valley gap

    # Intervalley coupling
    delta00: complex                   # ⟨η₊|B₀|η₋⟩  overlap
    m_scalar: float                    # |½ Tr(B̃₀)|  intervalley mass
    r_mass: float                      # residual: ‖B̃₀ − m·I‖ / ‖B̃₀‖

    # First-derivative transport (velocity operators)
    ell_cross_par: float               # |Ũ_∥[0,0]|  longitudinal cross-patch
    ell_cross_1: float                 # |Ũ_1[0,0]|  transverse-1 cross-patch
    ell_cross_2: float                 # |Ũ_2[0,0]|  transverse-2 cross-patch
    u_parallel_sigma3: float           # ½ Re Tr(σ₃ Ũ_∥)  splitting diagnostic

    # Pauli decomposition (supplementary)
    c_E: float                         # even chirality
    c_O: float                         # odd chirality

    # Second-derivative stiffness (mass tensor)
    m2_diag_par: float                 # ⟨η₊|Γ̃_∥∥|η₊⟩  longitudinal mass²
    m2_diag_1: float                   # ⟨η₊|Γ̃_11|η₊⟩  transverse-1 mass²
    m2_diag_2: float                   # ⟨η₊|Γ̃_22|η₊⟩  transverse-2 mass²
    m2_cross_par: float                # ⟨η₊|Γ̃_∥∥^{off}|η₋⟩  cross stiffness

    # Gate verdicts (per-pair)
    gate2_pass: bool
    gate3_pass: bool


# ============================================================
# Geometry utilities
# ============================================================

def load_backend(path: str):
    """Load backend module from .py path."""
    p = Path(path).resolve()
    spec = importlib.util.spec_from_file_location(p.stem, str(p))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load backend from {p}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_run_dir(run_dir: Path):
    """Load Ψ₀, config, patch_centers from a solver run directory."""
    psi_path = run_dir / "Psi_corr.npy"
    if not psi_path.exists():
        psi_path = run_dir / "Psi_final.npy"
    if not psi_path.exists():
        raise FileNotFoundError(f"No Psi_corr.npy or Psi_final.npy in {run_dir}")

    psi0 = np.load(psi_path).astype(np.complex128)
    with open(run_dir / "config.json", "r", encoding="utf-8") as f:
        params = json.load(f)
    patch_centers = np.load(run_dir / "patch_centers.npy").astype(np.float64)
    return psi0, params, patch_centers


def grid_kvectors(N: int, L: float) -> np.ndarray:
    """1D k-space grid matching numpy FFT convention."""
    dx = L / N
    return 2.0 * np.pi * np.fft.fftfreq(N, d=dx)


def snap_to_grid(k_target: np.ndarray, k1d: np.ndarray) -> Tuple[np.ndarray, float]:
    """Snap a 3D k-vector to the nearest grid point; return snapped vec + rel error."""
    idx = [int(np.argmin(np.abs(k1d - k_target[d]))) for d in range(3)]
    snapped = np.array([k1d[idx[0]], k1d[idx[1]], k1d[idx[2]]])
    denom = max(float(np.linalg.norm(k_target)), 1e-15)
    return snapped, float(np.linalg.norm(snapped - k_target) / denom)


def find_antipodal_pairs(patch_centers: np.ndarray, tol: float = 0.3) -> List[Tuple[int, int]]:
    """Find antipodal pairs (G, -G) from patch_centers."""
    n = len(patch_centers)
    used = set()
    pairs = []
    for i in range(n):
        if i in used:
            continue
        target = -patch_centers[i]
        best_j, best_d = None, np.inf
        for j in range(i + 1, n):
            if j in used:
                continue
            d = float(np.linalg.norm(patch_centers[j] - target))
            if d < best_d:
                best_d, best_j = d, j
        if best_j is not None and best_d < tol:
            used.update([i, best_j])
            pairs.append((i, best_j))
    return pairs


def frame_from_G(Gp: np.ndarray, Gm: np.ndarray):
    """Build orthonormal frame (n̂, e₁, e₂) from the valley separation direction."""
    g = Gp - Gm
    n = g / max(np.linalg.norm(g), 1e-15)
    trial = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    e1 = trial - np.dot(trial, n) * n
    e1 /= max(np.linalg.norm(e1), 1e-15)
    e2 = np.cross(n, e1)
    e2 /= max(np.linalg.norm(e2), 1e-15)
    return n, e1, e2


# ============================================================
# Internal basis construction
# ============================================================

def internal_frame_from_condensate(psi0: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build orthonormal internal frame (z₀, χ₁, χ₂) from condensate Ψ₀.

    z₀ = leading eigenvector of the polarisation density matrix
         ρ_{ab} = ⟨Ψ_a Ψ_b*⟩ / ⟨|Ψ|²⟩

    χ₁, χ₂ = Gram-Schmidt completion in the plane ⊥ z₀.
    """
    # Compute polarisation density matrix
    nrm = np.sqrt(np.sum(np.abs(psi0) ** 2, axis=0))
    valid = nrm > 1e-14
    z = np.zeros_like(psi0, dtype=np.complex128)
    z[:, valid] = psi0[:, valid] / nrm[valid]

    rho = np.zeros((3, 3), dtype=np.complex128)
    for a in range(3):
        for b in range(3):
            rho[a, b] = np.mean(z[a] * np.conj(z[b]))

    evals, evecs = np.linalg.eigh(rho)
    z0 = evecs[:, np.argmax(evals)]
    z0 /= max(np.linalg.norm(z0), 1e-15)

    # Deterministic Gram-Schmidt: choose canonical seed vectors
    # For z0 ≈ (1,1,1)/√3, this gives χ₁ ∝ (2,-1,-1), χ₂ ∝ (0,1,-1)
    seed1 = np.array([1.0, 0.0, 0.0], dtype=np.complex128)
    if abs(np.vdot(z0, seed1)) > 0.9:
        seed1 = np.array([0.0, 1.0, 0.0], dtype=np.complex128)
    chi1 = seed1 - z0 * np.vdot(z0, seed1)
    chi1 /= max(np.linalg.norm(chi1), 1e-15)

    seed2 = np.array([0.0, 0.0, 1.0], dtype=np.complex128)
    if abs(np.vdot(z0, seed2)) > 0.9 or abs(np.vdot(chi1, seed2)) > 0.9:
        seed2 = np.array([0.0, 1.0, 0.0], dtype=np.complex128)
    chi2 = seed2 - z0 * np.vdot(z0, seed2) - chi1 * np.vdot(chi1, seed2)
    chi2 /= max(np.linalg.norm(chi2), 1e-15)

    # Verify orthonormality
    assert abs(np.vdot(z0, chi1)) < 1e-12, "z0 and chi1 not orthogonal"
    assert abs(np.vdot(z0, chi2)) < 1e-12, "z0 and chi2 not orthogonal"
    assert abs(np.vdot(chi1, chi2)) < 1e-12, "chi1 and chi2 not orthogonal"
    assert abs(np.linalg.norm(z0) - 1) < 1e-12
    assert abs(np.linalg.norm(chi1) - 1) < 1e-12
    assert abs(np.linalg.norm(chi2) - 1) < 1e-12

    return z0, chi1, chi2


# ============================================================
# Plane-wave basis states
# ============================================================

def make_plane_wave(
    kvec: np.ndarray,
    chi: np.ndarray,
    X: np.ndarray, Y: np.ndarray, Z: np.ndarray,
    dV: float,
) -> np.ndarray:
    """
    Normalised plane-wave state |k, χ⟩ = N · χ_a · e^{ik·x}

    Shape: (3, Nx, Ny, Nz) complex128.
    Inner product: ⟨a|b⟩ = Σ_x a*(x)·b(x) · dV
    """
    phase = np.exp(1j * (kvec[0] * X + kvec[1] * Y + kvec[2] * Z))
    state = chi[:, None, None, None] * phase[None, :, :, :]
    norm2 = float(np.real(np.sum(np.conj(state) * state)) * dV)
    return state / max(np.sqrt(norm2), 1e-15)


def inner(a: np.ndarray, b: np.ndarray, dV: float) -> complex:
    """Hermitian inner product ⟨a|b⟩ = Σ a*(x)·b(x) dV."""
    return complex(np.sum(np.conj(a) * b) * dV)


# ============================================================
# Core: build the 6×6 Hessian block at momentum shift p
# ============================================================

def hessian_block_6x6(
    backend,
    psi0: np.ndarray,
    params: dict,
    Gp: np.ndarray,
    Gm: np.ndarray,
    z0: np.ndarray,
    chi1: np.ndarray,
    chi2: np.ndarray,
    pvec: np.ndarray,
    X: np.ndarray, Y: np.ndarray, Z: np.ndarray,
    dV: float,
) -> np.ndarray:
    """
    Build the 6×6 Hessian matrix H(G₊+p, G₋+p) in the basis:
        |0⟩ = |G₊+p, z₀⟩     |3⟩ = |G₋+p, z₀⟩
        |1⟩ = |G₊+p, χ₁⟩     |4⟩ = |G₋+p, χ₁⟩
        |2⟩ = |G₊+p, χ₂⟩     |5⟩ = |G₋+p, χ₂⟩

    Returns: Hermitian 6×6 matrix.
    """
    internal = [z0, chi1, chi2]
    basis = []
    for kvec in [Gp + pvec, Gm + pvec]:
        for chi in internal:
            basis.append(make_plane_wave(kvec, chi, X, Y, Z, dV))

    # Apply Hessian to each basis vector
    Hbasis = []
    for b in basis:
        hv = backend.hessian_vec(psi0, b, params)
        Hbasis.append(np.asarray(hv, dtype=np.complex128))

    # Build matrix
    M = np.zeros((6, 6), dtype=np.complex128)
    for a in range(6):
        for b in range(6):
            M[a, b] = inner(basis[a], Hbasis[b], dV)

    # Enforce Hermiticity
    return 0.5 * (M + M.conj().T)


# ============================================================
# Finite differences: first and second derivatives
# ============================================================

def fd_first_4th(fm2, fm1, fp1, fp2, h: float):
    """4th-order centred first derivative."""
    return (fm2 - 8.0 * fm1 + 8.0 * fp1 - fp2) / (12.0 * h)


def fd_second_4th(fm2, fm1, f0, fp1, fp2, h: float):
    """4th-order centred second derivative: f''(x) = (-f_{-2} + 16f_{-1} - 30f_0 + 16f_{+1} - f_{+2}) / (12h²)."""
    return (-fm2 + 16.0 * fm1 - 30.0 * f0 + 16.0 * fp1 - fp2) / (12.0 * h**2)


# ============================================================
# Full extraction for one antipodal pair
# ============================================================

def extract_pair(
    backend,
    psi0: np.ndarray,
    params: dict,
    Gp: np.ndarray,
    Gm: np.ndarray,
    z0: np.ndarray,
    chi1: np.ndarray,
    chi2: np.ndarray,
    X: np.ndarray, Y: np.ndarray, Z: np.ndarray,
    dV: float,
    dk_steps: int = 1,
    L: float = 16.0,
    eta_par: float = 0.01,
    eta_trans: float = 0.01,
) -> Tuple[PairResult, dict]:
    """
    Full Gate 2 & 3 extraction for one (G₊, G₋) pair.

    Returns: (PairResult, arrays_dict)
    """
    h = dk_steps * (2.0 * np.pi / L)
    unit = [np.array([1, 0, 0], dtype=float),
            np.array([0, 1, 0], dtype=float),
            np.array([0, 0, 1], dtype=float)]

    def H(p):
        return hessian_block_6x6(backend, psi0, params, Gp, Gm,
                                 z0, chi1, chi2, p, X, Y, Z, dV)

    # ---- H₀ at p = 0 ----
    H0 = H(np.zeros(3))

    # ---- First derivatives ∂H/∂p_i via 4th-order FD ----
    dH = []
    for i in range(3):
        e = unit[i]
        Hm2 = H(-2 * h * e)
        Hm1 = H(-1 * h * e)
        Hp1 = H(+1 * h * e)
        Hp2 = H(+2 * h * e)
        dHi = fd_first_4th(Hm2, Hm1, Hp1, Hp2, h)
        dH.append(0.5 * (dHi + dHi.conj().T))  # enforce Hermiticity
    dH = np.array(dH)  # shape (3, 6, 6)

    # ---- Second derivatives ∂²H/∂p_i∂p_j via 4th-order FD ----
    d2H = np.zeros((3, 3, 6, 6), dtype=np.complex128)
    for i in range(3):
        e = unit[i]
        Hm2 = H(-2 * h * e)
        Hm1 = H(-1 * h * e)
        Hp1 = H(+1 * h * e)
        Hp2 = H(+2 * h * e)
        d2Hii = fd_second_4th(Hm2, Hm1, H0, Hp1, Hp2, h)
        d2H[i, i] = 0.5 * (d2Hii + d2Hii.conj().T)

    # Cross terms ∂²H/∂p_i∂p_j (i≠j) via mixed FD
    for i in range(3):
        for j in range(i + 1, 3):
            ei, ej = unit[i], unit[j]
            Hpp = H(+h * ei + h * ej)
            Hpm = H(+h * ei - h * ej)
            Hmp = H(-h * ei + h * ej)
            Hmm = H(-h * ei - h * ej)
            d2Hij = (Hpp - Hpm - Hmp + Hmm) / (4.0 * h**2)
            d2Hij = 0.5 * (d2Hij + d2Hij.conj().T)
            d2H[i, j] = d2Hij
            d2H[j, i] = d2Hij

    # ---- Spatial frame ----
    nvec, e1vec, e2vec = frame_from_G(Gp, Gm)

    # ---- Block decomposition of H₀ ----
    # E₊ = H₀[0:3, 0:3],  E₋ = H₀[3:6, 3:6],  B₀ = H₀[0:3, 3:6]
    Eplus = H0[:3, :3]
    Eminus = H0[3:, 3:]
    B0 = H0[:3, 3:]

    # Diagonalise E₊ and E₋
    evalsp, evecsp = np.linalg.eigh(Eplus)
    evalsm, evecsm = np.linalg.eigh(Eminus)

    # Lowest eigenvectors (the carrier modes)
    eta_p = evecsp[:, 0]  # lowest of E₊
    eta_m = evecsm[:, 0]  # lowest of E₋

    # Rotation matrices for eigenframe
    Up = evecsp   # columns = eigenvectors of E₊
    Um = evecsm   # columns = eigenvectors of E₋

    gap_p = float(evalsp[1] - evalsp[0])
    gap_m = float(evalsm[1] - evalsm[0])

    # ---- Intervalley coupling B̃₀ = U₊† B₀ U₋ ----
    B0_tilde = Up.conj().T @ B0 @ Um
    delta00 = complex(B0_tilde[0, 0])
    mass_scalar = abs(0.5 * np.trace(B0_tilde))
    denom_mass = max(float(np.linalg.norm(B0_tilde, ord='fro')), 1e-30)
    r_mass = float(np.linalg.norm(B0_tilde - 0.5 * np.trace(B0_tilde) * np.eye(3), ord='fro') / denom_mass)

    # ---- First-derivative transport operators ----
    # Project along spatial directions
    V_par = nvec[0] * dH[0] + nvec[1] * dH[1] + nvec[2] * dH[2]
    V_1 = e1vec[0] * dH[0] + e1vec[1] * dH[1] + e1vec[2] * dH[2]
    V_2 = e2vec[0] * dH[0] + e2vec[1] * dH[1] + e2vec[2] * dH[2]

    # Extract off-diagonal blocks (inter-valley transport)
    Vpar_off = V_par[:3, 3:]
    V1_off = V_1[:3, 3:]
    V2_off = V_2[:3, 3:]

    # Rotate to eigenframe: Ũ = U₊† · V^{off} · U₋
    Upar_tilde = Up.conj().T @ Vpar_off @ Um
    U1_tilde = Up.conj().T @ V1_off @ Um
    U2_tilde = Up.conj().T @ V2_off @ Um

    # ---- GATE 2: Cross-patch longitudinal carrier ----
    # ℓ_∥^{cross} = |Ũ_∥[0,0]| = |⟨η₊|V_∥^{off}|η₋⟩|
    ell_cross_par = abs(Upar_tilde[0, 0])

    # ---- GATE 3: Cross-patch transverse carrier ----
    # ℓ_I^{cross} = |Ũ_I[0,0]| = |⟨η₊|V_I^{off}|η₋⟩|
    ell_cross_1 = abs(U1_tilde[0, 0])
    ell_cross_2 = abs(U2_tilde[0, 0])

    # ---- Supplementary: σ₃ splitting (diagnostic) ----
    u_par_s3 = float(np.real(0.5 * np.trace(SIGMA3 @ Upar_tilde[:2, :2])))

    # ---- Supplementary: Pauli c_E, c_O (chirality) ----
    # These use the 2×2 transverse sub-block of Ũ
    U1t_22 = U1_tilde[1:3, 1:3]   # chi1/chi2 subblock
    U2t_22 = U2_tilde[1:3, 1:3]
    c_E = float(np.real(0.25 * np.trace(SIGMA1 @ U1t_22 + SIGMA2 @ U2t_22)))
    c_O = float(np.real(0.25 * np.trace(SIGMA2 @ U1t_22 - SIGMA1 @ U2t_22)))

    # ---- Second-derivative: stiffness tensor projected ----
    # Γ̃_∥∥ = n̂_i n̂_j d²H/dp_i dp_j  (6×6 → eigenframe)
    Gamma_par = np.zeros((6, 6), dtype=np.complex128)
    Gamma_1 = np.zeros((6, 6), dtype=np.complex128)
    Gamma_2 = np.zeros((6, 6), dtype=np.complex128)
    for i in range(3):
        for j in range(3):
            Gamma_par += nvec[i] * nvec[j] * d2H[i, j]
            Gamma_1 += e1vec[i] * e1vec[j] * d2H[i, j]
            Gamma_2 += e2vec[i] * e2vec[j] * d2H[i, j]

    # On-diagonal block (G₊ sector) in eigenframe: U₊† Γ[:3,:3] U₊
    Gpar_diag_ef = Up.conj().T @ Gamma_par[:3, :3] @ Up
    G1_diag_ef = Up.conj().T @ Gamma_1[:3, :3] @ Up
    G2_diag_ef = Up.conj().T @ Gamma_2[:3, :3] @ Up

    m2_diag_par = float(np.real(Gpar_diag_ef[0, 0]))
    m2_diag_1 = float(np.real(G1_diag_ef[0, 0]))
    m2_diag_2 = float(np.real(G2_diag_ef[0, 0]))

    # Off-diagonal block stiffness: U₊† Γ[:3,3:] U₋
    Gpar_cross_ef = Up.conj().T @ Gamma_par[:3, 3:] @ Um
    m2_cross_par = float(abs(Gpar_cross_ef[0, 0]))

    # ---- Gate verdicts ----
    gate2 = ell_cross_par > eta_par
    gate3 = ell_cross_1 > eta_trans or ell_cross_2 > eta_trans

    result = PairResult(
        pair_label="", patch_plus=0, patch_minus=0,
        G_plus=[], G_minus=[],
        snap_err_plus=0.0, snap_err_minus=0.0,
        evals_plus=[float(e) for e in evalsp],
        evals_minus=[float(e) for e in evalsm],
        gap_plus=gap_p, gap_minus=gap_m,
        delta00=delta00, m_scalar=mass_scalar, r_mass=r_mass,
        ell_cross_par=ell_cross_par,
        ell_cross_1=ell_cross_1,
        ell_cross_2=ell_cross_2,
        u_parallel_sigma3=u_par_s3,
        c_E=c_E, c_O=c_O,
        m2_diag_par=m2_diag_par,
        m2_diag_1=m2_diag_1,
        m2_diag_2=m2_diag_2,
        m2_cross_par=m2_cross_par,
        gate2_pass=gate2,
        gate3_pass=gate3,
    )

    arrays = {
        "H0": H0,
        "Eplus": Eplus, "Eminus": Eminus, "B0": B0,
        "B0_tilde": B0_tilde,
        "Upar_tilde": Upar_tilde,
        "U1_tilde": U1_tilde,
        "U2_tilde": U2_tilde,
        "eta_plus": eta_p,
        "eta_minus": eta_m,
        "Gamma_par_diag_ef": Gpar_diag_ef,
    }

    return result, arrays


# ============================================================
# Full pipeline for all pairs
# ============================================================

def run_all_pairs(
    backend,
    psi0: np.ndarray,
    params: dict,
    patch_centers: np.ndarray,
    *,
    dk_steps: int = 1,
    eta_par: float = 0.01,
    eta_trans: float = 0.01,
) -> Tuple[List[PairResult], List[dict]]:
    """Run extraction on all antipodal pairs."""
    N = psi0.shape[1]
    L = float(params.get("L", params.get("Lx", 16.0)))
    k1d = grid_kvectors(N, L)

    # Spatial grid for plane-wave construction
    x = np.linspace(0, L, N, endpoint=False)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    dV = (L / N) ** 3

    # Internal frame
    z0, chi1, chi2 = internal_frame_from_condensate(psi0)
    print(f"  z₀ = [{z0[0]:.4f}, {z0[1]:.4f}, {z0[2]:.4f}]")
    print(f"  χ₁ = [{chi1[0]:.4f}, {chi1[1]:.4f}, {chi1[2]:.4f}]")
    print(f"  χ₂ = [{chi2[0]:.4f}, {chi2[1]:.4f}, {chi2[2]:.4f}]")

    pairs = find_antipodal_pairs(patch_centers)
    if not pairs:
        raise RuntimeError("No antipodal pairs found.")
    print(f"  Found {len(pairs)} antipodal pair(s)")

    results = []
    all_arrays = []

    for idx, (i, j) in enumerate(pairs):
        Gp_target = patch_centers[i]
        Gm_target = patch_centers[j]
        Gp_grid, err_p = snap_to_grid(Gp_target, k1d)
        Gm_grid, err_m = snap_to_grid(Gm_target, k1d)

        print(f"\n  --- Pair {idx}: patches {i}<->{j} ---")
        print(f"  G₊ = [{Gp_grid[0]:.4f}, {Gp_grid[1]:.4f}, {Gp_grid[2]:.4f}]  (snap err {err_p:.4f})")
        print(f"  G₋ = [{Gm_grid[0]:.4f}, {Gm_grid[1]:.4f}, {Gm_grid[2]:.4f}]  (snap err {err_m:.4f})")

        res, arrs = extract_pair(
            backend, psi0, params,
            Gp_grid, Gm_grid,
            z0, chi1, chi2,
            X, Y, Z, dV,
            dk_steps=dk_steps, L=L,
            eta_par=eta_par, eta_trans=eta_trans,
        )

        # Fill metadata
        res.pair_label = f"{i}<->{j}"
        res.patch_plus = i
        res.patch_minus = j
        res.G_plus = [float(x) for x in Gp_grid]
        res.G_minus = [float(x) for x in Gm_grid]
        res.snap_err_plus = err_p
        res.snap_err_minus = err_m

        results.append(res)
        all_arrays.append(arrs)

        # Report
        g2 = "PASS" if res.gate2_pass else "FAIL"
        g3 = "PASS" if res.gate3_pass else "FAIL"
        print(f"  E₊ eigenvalues: {res.evals_plus[0]:.4e}, {res.evals_plus[1]:.4e}, {res.evals_plus[2]:.4e}")
        print(f"  Gap(E₊) = {res.gap_plus:.4e},  Gap(E₋) = {res.gap_minus:.4e}")
        print(f"  |Δ₀₀| = {abs(res.delta00):.4e},  m_scalar = {res.m_scalar:.4e}")
        print(f"  ℓ_∥^cross = {res.ell_cross_par:.6e}   [Gate 2: {g2}]")
        print(f"  ℓ_1^cross = {res.ell_cross_1:.6e}")
        print(f"  ℓ_2^cross = {res.ell_cross_2:.6e}   [Gate 3: {g3}]")
        print(f"  m²_diag(∥) = {res.m2_diag_par:.4e},  m²_diag(⊥1) = {res.m2_diag_1:.4e}")
        print(f"  c_E = {res.c_E:.4e},  c_O = {res.c_O:.4e}")

    return results, all_arrays


# ============================================================
# Summary and certification
# ============================================================

def print_certificate(results: List[PairResult], eta_par: float, eta_trans: float) -> None:
    """Print the final TECT gate certificate."""
    max_ell_par = max(r.ell_cross_par for r in results)
    max_ell_1 = max(r.ell_cross_1 for r in results)
    max_ell_2 = max(r.ell_cross_2 for r in results)
    max_ell_trans = max(max_ell_1, max_ell_2)

    gate2 = max_ell_par > eta_par
    gate3 = max_ell_trans > eta_trans
    any_g2 = any(r.gate2_pass for r in results)
    any_g3 = any(r.gate3_pass for r in results)

    # Mean stiffness
    m2_vals = [r.m2_diag_par for r in results]
    m2_mean = np.mean(m2_vals) if m2_vals else float('nan')

    print()
    print("╔" + "═" * 70 + "╗")
    print("║  TECT INTERVALLEY GATE CERTIFICATE (v4)                            ║")
    print("╠" + "═" * 70 + "╣")
    print(f"║  Pairs analysed      : {len(results):>4d}" + " " * 42 + "║")
    print(f"║  max ℓ_∥^cross       : {max_ell_par:>14.6e}" + " " * 28 + "║")
    print(f"║  max ℓ_⊥^cross       : {max_ell_trans:>14.6e}" + " " * 28 + "║")
    print(f"║  mean m²_diag(∥)     : {m2_mean:>14.6e}" + " " * 28 + "║")
    print("╠" + "═" * 70 + "╣")

    def gate_line(name, passed, detail=""):
        mark = "✅ PASS" if passed else "❌ FAIL"
        line = f"║  {name:<12s}  {mark}  {detail}"
        print(line + " " * max(0, 71 - len(line)) + "║")

    gate_line("Gate 2", any_g2, f"ℓ_∥ = {max_ell_par:.6e} > η_∥ = {eta_par}")
    gate_line("Gate 3", any_g3, f"ℓ_⊥ = {max_ell_trans:.6e} > η_T = {eta_trans}")
    gate_line("Cross-patch", any_g2 and any_g3, "Both Gates 2+3" if any_g2 and any_g3 else "")
    print("╚" + "═" * 70 + "╝")

    # LaTeX block
    g2s = r"\checkmark" if any_g2 else r"\times"
    g3s = r"\checkmark" if any_g3 else r"\times"
    print()
    print(r"\begin{align}")
    print(rf"  &\text{{Gate 2 (cross-patch longitudinal):}}\quad "
          rf"\ell_{{\parallel}}^{{\mathrm{{cross}}}} = {max_ell_par:.4e} "
          rf"\ {'>' if any_g2 else r'\leq'}\ \eta_{{\parallel}} = {eta_par} "
          rf"\quad {g2s} \\")
    print(rf"  &\text{{Gate 3 (cross-patch transverse):}}\quad "
          rf"\ell_{{\perp}}^{{\mathrm{{cross}}}} = {max_ell_trans:.4e} "
          rf"\ {'>' if any_g3 else r'\leq'}\ \eta_T = {eta_trans} "
          rf"\quad {g3s}")
    print(r"\end{align}")


# ============================================================
# Save
# ============================================================

def save_outputs(
    output_dir: Path,
    results: List[PairResult],
    all_arrays: List[dict],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # JSON summary (serialisable)
    summary = []
    for r in results:
        d = {
            "pair_label": r.pair_label,
            "patch_plus": r.patch_plus,
            "patch_minus": r.patch_minus,
            "G_plus": r.G_plus,
            "G_minus": r.G_minus,
            "snap_err_plus": r.snap_err_plus,
            "snap_err_minus": r.snap_err_minus,
            "evals_plus": r.evals_plus,
            "evals_minus": r.evals_minus,
            "gap_plus": r.gap_plus,
            "gap_minus": r.gap_minus,
            "delta00_abs": abs(r.delta00),
            "m_scalar": r.m_scalar,
            "r_mass": r.r_mass,
            "ell_cross_par": r.ell_cross_par,
            "ell_cross_1": r.ell_cross_1,
            "ell_cross_2": r.ell_cross_2,
            "u_parallel_sigma3": r.u_parallel_sigma3,
            "c_E": r.c_E,
            "c_O": r.c_O,
            "m2_diag_par": r.m2_diag_par,
            "m2_diag_1": r.m2_diag_1,
            "m2_diag_2": r.m2_diag_2,
            "m2_cross_par": r.m2_cross_par,
            "gate2_pass": r.gate2_pass,
            "gate3_pass": r.gate3_pass,
        }
        summary.append(d)

    with open(output_dir / "intervalley_v4_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # NPZ arrays
    npz = {}
    for idx, arrs in enumerate(all_arrays):
        for k, v in arrs.items():
            npz[f"pair{idx}_{k}"] = np.asarray(v)
    np.savez_compressed(output_dir / "intervalley_v4_arrays.npz", **npz)

    print(f"\n[save] {output_dir / 'intervalley_v4_summary.json'}")
    print(f"[save] {output_dir / 'intervalley_v4_arrays.npz'}")


# ============================================================
# CLI
# ============================================================

def main():
    p = argparse.ArgumentParser(
        description="TECT intervalley extractor v4: cross-patch Gate 2+3 WITNESS via 6×6 Hessian block"
    )
    p.add_argument("--input", required=True, help="Run directory")
    p.add_argument("--backend", required=True, help="Backend .py path")
    p.add_argument("--output", default=None, help="Output directory")
    p.add_argument("--dk-steps", type=int, default=1,
                   help="FD step in grid units (default: 1, recommended for N=64)")
    p.add_argument("--eta-par", type=float, default=0.01,
                   help="Gate 2 threshold η_∥ (default: 0.01)")
    p.add_argument("--eta-trans", type=float, default=0.01,
                   help="Gate 3 threshold η_T (default: 0.01)")
    args = p.parse_args()

    run_dir = Path(args.input).resolve()
    output_dir = Path(args.output).resolve() if args.output else run_dir / "intervalley_v4_out"

    print("=" * 72)
    print("TECT Intervalley Extractor v4")
    print("Cross-patch Gate 2+3 WITNESS via 6×6 Hessian block")
    print("=" * 72)

    psi0, params, patch_centers = load_run_dir(run_dir)
    backend = load_backend(args.backend)

    if not hasattr(backend, "hessian_vec"):
        raise RuntimeError("Backend must provide hessian_vec(Psi, v, params)")

    print(f"  Input     : {run_dir}")
    print(f"  Backend   : {args.backend}")
    print(f"  Output    : {output_dir}")
    print(f"  Grid      : {psi0.shape[1]}")
    print(f"  q₀        : {params.get('q0', 'N/A')}")
    print(f"  dk_steps  : {args.dk_steps}")
    print(f"  η_∥       : {args.eta_par}")
    print(f"  η_T       : {args.eta_trans}")
    print()
    print("Building internal frame from condensate...")

    results, all_arrays = run_all_pairs(
        backend, psi0, params, patch_centers,
        dk_steps=args.dk_steps,
        eta_par=args.eta_par,
        eta_trans=args.eta_trans,
    )

    print_certificate(results, args.eta_par, args.eta_trans)
    save_outputs(output_dir, results, all_arrays)

    print("\n" + "=" * 72)
    print("Done.")
    print("=" * 72)


if __name__ == "__main__":
    main()
