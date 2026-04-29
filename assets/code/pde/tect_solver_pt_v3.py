#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v3.2
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===

"""
tect_solver_pt.py  [TECT-NPY-v2-final]
---------------------------------------

PyTorch-accelerated pseudospectral IMEX gradient-flow solver for the TECT
working branch. Compatible with real_backend_pt_bcc_mixed.py and any backend
exposing the standard private torch API (_stiffness_symbols_t, etc.).

Honest scope
------------
This is NOT the unique final complete TECT UV solver.
It is the current executable working branch:
    Brazovskii core (spectral / bcc_symbol / mixed_bcc Laplacian)
  + family splitting (diagonal mass matrix in internal space)
  + internal locking (projector penalty)
  + optional shell bias (eta_shell)
  + executable proxy for integrated-out Class II sector

Bug fixes vs. previous version
--------------------------------
  Bug#1 [HIGH]  : IMEX linear_denominator_t now uses _stiffness_symbols_t(s2, s4)
                  instead of raw k^2/k^4.  In mixed_bcc mode the old code caused the
                  IMEX fixed point to differ from the true zero of R[Psi].
  Bug#2 [MEDIUM]: shell_bias removed from explicit_rest_t (private API path).
                  It was double-counted: once in the denominator, once in the
                  explicit part.  (eta_shell=0 default means zero impact on past runs.)

Export format
-------------
Writes a complete TECT extractor package (format: TECT-NPY-v2-final):
  Psi_init.npy         initial field before gradient flow
  noise_init.npy       noise vector (only if solver-generated noise present)
  Psi_corr.npy         converged / final field
  Psi_BCC.npy          BCC seed reference (for comparison)
  Phi_A.npy, Phi_E.npy, Phi_O.npy   orbit tangent fields
  hat_n.npy            reference axis
  patch_centers.npy    8 patch directions in k-space
  G_list.npy           BCC shell reciprocal vectors
  Pi_fam_matrix.npy    family projector
  config.json          all physical and numerical parameters
  metadata.json        full provenance including emergence_claim_safe flag
  residual_history.npy per-step RMS residual
  energy_history.npy   per-step free energy
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import torch

try:
    import intel_extension_for_pytorch as ipex
except ImportError:
    pass

# ============================================================
# Backend loader
# ============================================================

def load_module(module_path: Path):
    spec = importlib.util.spec_from_file_location("tect_real_backend_pt", str(module_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from: {module_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ============================================================
# Generic utilities
# ============================================================

def normalize(v: np.ndarray, eps: float = 1e-14) -> np.ndarray:
    v = np.asarray(v, dtype=np.float64)
    n = np.linalg.norm(v)
    if n < eps:
        raise ValueError("Cannot normalize near-zero vector.")
    return v / n


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def make_xyz_grid(N: int, L: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Return (X, Y, Z) broadcasting views of shape (N,1,1), (1,N,1), (1,1,N).
    Algebraically identical to ``np.meshgrid(x, x, x, indexing='ij')``
    inside any broadcast expression (e.g. ``hat_n[0]*X + hat_n[1]*Y +
    hat_n[2]*Z``), but stores ``3*N*8`` bytes rather than ``3*N**3*8``
    bytes (≈ 150 MB → 3 KB at N=128). Callers that previously stacked
    ``np.stack([X, Y, Z], axis=0)`` must instead form scalar phases as
    ``vec[0]*X + vec[1]*Y + vec[2]*Z`` (broadcast sum). The
    ``make_xyz_grid_dense`` helper is provided for the rare case in which
    a materialized ``(N, N, N)`` tensor is genuinely required.
    """
    x = np.linspace(-L / 2.0, L / 2.0, N, endpoint=False, dtype=np.float64)
    X = x.reshape(N, 1, 1)
    Y = x.reshape(1, N, 1)
    Z = x.reshape(1, 1, N)
    return X, Y, Z


def make_xyz_grid_dense(N: int, L: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Materialized (N,N,N) coordinate tensors for sites that genuinely
    need them. Use ``make_xyz_grid`` (sparse views) wherever broadcast
    arithmetic suffices — that is the common case."""
    x = np.linspace(-L / 2.0, L / 2.0, N, endpoint=False, dtype=np.float64)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    return X, Y, Z


def make_default_hat_n() -> np.ndarray:
    return normalize(np.array([1.0, 1.0, 1.0], dtype=np.float64))


def make_default_patch_centers(hat_n: np.ndarray) -> np.ndarray:
    hat_n = normalize(hat_n)
    trial = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    if abs(np.dot(trial, hat_n)) > 0.8:
        trial = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    e1 = normalize(trial - np.dot(trial, hat_n) * hat_n)
    e2 = normalize(np.cross(hat_n, e1))
    raw = np.array(
        [
            hat_n,
            -hat_n,
            e1,
            -e1,
            e2,
            -e2,
            normalize(e1 + e2),
            normalize(-(e1 + e2)),
        ],
        dtype=np.float64,
    )
    return raw


def make_bcc_shell_G_list(N: int, L: float, q0: Optional[float] = None) -> np.ndarray:
    dk = 2.0 * np.pi / L
    if q0 is None:
        q0 = dk * math.sqrt(2.0)
    m = max(1, int(round(q0 / (dk * math.sqrt(2.0)))))
    dirs = np.array(
        [
            [1, 1, 0],
            [1, -1, 0],
            [-1, 1, 0],
            [-1, -1, 0],
            [1, 0, 1],
            [1, 0, -1],
            [-1, 0, 1],
            [-1, 0, -1],
            [0, 1, 1],
            [0, 1, -1],
            [0, -1, 1],
            [0, -1, -1],
        ],
        dtype=np.float64,
    )
    return dirs * (m * dk)


def make_default_family_projector() -> np.ndarray:
    return np.eye(3, dtype=np.complex128)


def make_default_config(N: int, L: float, q0: Optional[float], hat_n: np.ndarray) -> Dict[str, Any]:
    dk = 2.0 * np.pi / L
    if q0 is None:
        q0 = dk * math.sqrt(2.0)

    if N == 32:
        dq_patch = 4.0 * dk
        dtheta_patch = 1.20
    elif N == 64:
        dq_patch = 3.0 * dk
        dtheta_patch = 0.90
    elif N == 128:
        dq_patch = 2.0 * dk
        dtheta_patch = 0.70
    else:
        raise ValueError("Supported grids are exactly 32, 64, 128.")

    return {
        "Lx": float(L),
        "Ly": float(L),
        "Lz": float(L),
        "q0": float(q0),
        "dq_patch": float(dq_patch),
        "dtheta_patch": float(dtheta_patch),
        "eps_hess": 1e-6,
        "h_quartic": 1e-3,
        "num_eigs": 4,
        "project_family_in_eigensolve": False,
        "delta_corr": [0.0096, -0.0288, 0.0096],
        "orbit_fd_step": 1e-4,
        # ---- Brazovskii-locked defaults (Math38-Brazovskii-2026-04-15) -----
        # Previous GL defaults (r=0.25, lambda=+0.35, gamma=0.05) are now
        # archived under PDE/backup_GL_2026-04-15/. Override via --config
        # path if a different regime is required for a particular run.
        "r":              0.26,
        "mu2":            0.26,
        "Z": -1.0,
        "Y": 0.5,
        "quartic_lambda": -0.43,
        "lambda":         -0.43,
        "sextic_gamma":    1.62,
        "gamma":           1.62,
        "I3_convention":   0.3333333333,
        "K4_BCC":          1.0,
        "K6_BCC":          2.5,
        "family_masses": [0.0, 0.03, 0.07],
        "family_projector": [1.0, 1.0, 1.0],
        "z0": [1.0, 1.0, 1.0],
        "k_lock": 0.15,
        "eta_shell": 0.0,
        "alpha_X": 0.3,
        "beta_X": 0.25,
        "M_X": 2.0,
        "cJJ": 0.2,
        "cJK": 0.1,
        "cKK": 0.15,
        "eps_classII_hess": 5e-7,
        "hat_n": hat_n.tolist(),
        "fast_scale": 1.0,
        "solver_dt": 5e-3,
        "solver_steps": 2000,
        "solver_save_every": 100,
        "solver_tol": 1e-8,
        "export_format_version": "TECT-NPY-v1",
    }


# ============================================================
# Mock seed / orbit fields
# ============================================================

def make_mock_branch_data(N: int, L: float, q0: Optional[float], hat_n: np.ndarray,
                          quartic_lambda: Optional[float] = None,
                          sextic_gamma: Optional[float] = None):
    """Generate BCC-symmetric seed field on the q0-shell.

    If quartic_lambda and sextic_gamma are provided, the seed amplitude is
    set to the Brazovskii theory prediction:
        phi0 = sqrt(-4 lambda / (15 gamma))       (Math37-AddA)
    Otherwise falls back to the legacy hardcoded amplitudes (0.22/0.15/0.10).
    """
    X, Y, Z = make_xyz_grid(N, L)  # sparse broadcasting views
    if q0 is None:
        q0 = (2.0 * np.pi / L) * math.sqrt(2.0)

    hat_n = normalize(hat_n)
    trial = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    if abs(np.dot(trial, hat_n)) > 0.8:
        trial = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    e1 = normalize(trial - np.dot(trial, hat_n) * hat_n)
    e2 = normalize(np.cross(hat_n, e1))

    # Direct broadcast sum — equivalent to q0 * tensordot(vec, R) but
    # avoids materialising the (3, N, N, N) coordinate stack.
    phase_n  = q0 * (hat_n[0] * X + hat_n[1] * Y + hat_n[2] * Z)
    phase_e1 = q0 * (e1[0]    * X + e1[1]    * Y + e1[2]    * Z)
    phase_e2 = q0 * (e2[0]    * X + e2[1]    * Y + e2[2]    * Z)

    z0 = np.array([1.0, 1.0, 1.0], dtype=np.complex128)
    z0 = z0 / np.linalg.norm(z0)

    # ── Seed amplitude ──────────────────────────────────────────
    # Brazovskii first-order lock (Math37-AddA, Math38):
    #   phi0 = sqrt(-4 lambda / (15 gamma))
    # For lambda < 0, gamma > 0 this is real and positive.
    # The dominant ±hat_n arms carry amplitude phi0; the four
    # equatorial arms carry phi0 * 0.45 (secondary modulation).
    if quartic_lambda is not None and sextic_gamma is not None:
        lam = float(quartic_lambda)
        gam = float(sextic_gamma)
        if lam >= 0 or gam <= 0:
            raise ValueError(
                f"Brazovskii seed requires lambda<0, gamma>0; got "
                f"lambda={lam}, gamma={gam}"
            )
        phi0 = math.sqrt(-4.0 * lam / (15.0 * gam))
        a_main = phi0           # dominant ±hat_n arm
        a_conj = phi0 * 0.68    # conjugate arm (slightly weaker)
        a_eq   = phi0 * 0.45    # equatorial arms
        print(f"[seed] Brazovskii phi0 = {phi0:.6f}  "
              f"(lambda={lam}, gamma={gam})")
    else:
        # Legacy hardcoded amplitudes (pre-Math37)
        a_main = 0.22
        a_conj = 0.15
        a_eq   = 0.10
        print(f"[seed] Legacy amplitudes: {a_main}/{a_conj}/{a_eq}")

    # Phase cache: each np.exp call is O(N**3) on the dense (N,N,N) phase
    # array, so we evaluate each unique exponential exactly once and reuse
    # both ±k branches. Family loop becomes a single broadcast assignment.
    e_pn = np.exp(1j * phase_n);  e_mn = np.conj(e_pn)
    e_p1 = np.exp(1j * phase_e1); e_m1 = np.conj(e_p1)
    e_p2 = np.exp(1j * phase_e2); e_m2 = np.conj(e_p2)
    # BCC star-arm linear combination:
    psi_pattern = (
        a_main * e_pn
        + a_conj * e_mn
        + a_eq * (e_p1 + e_m1 + e_p2 + e_m2)
    )  # shape (N, N, N)

    amps = np.array([1.0, 0.9, 1.1], dtype=np.float64)
    psi0 = amps[:, None, None, None] * psi_pattern[None, :, :, :]   # (3,N,N,N)
    psi_bcc = psi0 * z0[:, None, None, None]

    Phi_A = np.zeros_like(psi_bcc)
    Phi_E = np.zeros_like(psi_bcc)
    Phi_O = np.zeros_like(psi_bcc)

    modA = np.cos(phase_n) + 0.35 * np.cos(phase_e1 + phase_e2)
    modE = np.cos(phase_e1) - np.cos(phase_e2)
    modO = np.sin(phase_e1) + 0.7 * np.sin(phase_e2)

    vA = normalize(np.array([1.0, -1.0, 0.5], dtype=np.float64)).astype(np.complex128)
    vE = normalize(np.array([1.0, 0.0, -1.0], dtype=np.float64)).astype(np.complex128)
    vO = normalize(np.array([0.5, 1.0, -1.0], dtype=np.float64)).astype(np.complex128)

    for a in range(3):
        Phi_A[a] = (0.06 + 0.01 * a) * modA * vA[a]
        Phi_E[a] = (0.07 + 0.01 * a) * modE * vE[a]
        Phi_O[a] = 1j * (0.05 + 0.01 * a) * modO * vO[a]

    delta = np.array([0.0096, -0.0288, 0.0096], dtype=np.float64)
    Psi_corr0 = psi_bcc + delta[0] * Phi_A + delta[1] * Phi_E + delta[2] * Phi_O

    i0 = (N // 2, N // 2, N // 2)
    ref = Psi_corr0[0, i0[0], i0[1], i0[2]]
    phase_fix = np.exp(-1j * np.angle(ref))
    Psi_corr0 *= phase_fix
    psi_bcc *= phase_fix
    Phi_A *= phase_fix
    Phi_E *= phase_fix
    Phi_O *= phase_fix

    return psi_bcc, Psi_corr0, Phi_A, Phi_E, Phi_O


# ============================================================
# Torch backend adapters
# ============================================================

def backend_has_private_torch_api(backend: Any) -> bool:
    required = [
        "_to_torch",
        "_to_numpy",
        "_get_device",
        "_get_cdtype",
        "_get_kgrid",
        "_fft_field",
        "_ifft_field",
        "_brazovskii_linear_term_t",
        "_family_term_t",
        "_locked_internal_penalty_t",
        "_shell_bias_term_t",
        "_local_nonlinear_term_t",
        "_classII_effective_term_t",
    ]
    return all(hasattr(backend, name) for name in required)


def to_torch_state(Psi: np.ndarray | torch.Tensor, backend: Any, params: Dict[str, Any]) -> torch.Tensor:
    if backend_has_private_torch_api(backend):
        return backend._to_torch(Psi, params, complex_required=True)
    device = torch.device(str(params.get("device", "cpu")))
    dtype = torch.complex128 if str(params.get("torch_complex_dtype", "complex128")).lower() != "complex64" else torch.complex64
    if isinstance(Psi, torch.Tensor):
        return Psi.to(device=device, dtype=dtype)
    return torch.as_tensor(Psi, device=device, dtype=dtype)


def to_numpy_state(Psi_t: torch.Tensor, backend: Any) -> np.ndarray:
    if hasattr(backend, "_to_numpy"):
        return backend._to_numpy(Psi_t).astype(np.complex128, copy=False)
    return Psi_t.detach().cpu().numpy().astype(np.complex128, copy=False)


def _get_stiffness_diag(Psi_t: torch.Tensor, backend: Any, params: Dict[str, Any]):
    """
    FIX(Bug#1): Return the spectral symbol (s2, s4, kmag) that MATCHES the backend's
    actual Brazovskii operator, including mixed_bcc / bcc_symbol modes.
    Previously, linear_denominator_t and linear_diag_term_t used raw k^2/k^4 from
    _get_kgrid, causing a fixed-point mismatch in IMEX when laplacian_mode != 'spectral'.
    Now we call _stiffness_symbols_t when available; this makes the IMEX implicit part
    exactly match the linear operator in the residual.
    """
    if hasattr(backend, "_stiffness_symbols_t"):
        s2, s4, kmag = backend._stiffness_symbols_t(params, Psi_t)
    else:
        # fallback: spectral mode (k^2) — correct when laplacian_mode == 'spectral'
        _, _, _, s2, s4, kmag = backend._get_kgrid(params, Psi_t)
    return s2, s4, kmag


def linear_denominator_t(Psi_t: torch.Tensor, backend: Any, params: Dict[str, Any], dt: float) -> torch.Tensor:
    # FIX(Bug#1): use actual stiffness symbols (s2, s2^2), not raw k^2, k^4
    s2, s4, kmag = _get_stiffness_diag(Psi_t, backend, params)
    r = float(params.get("r", params.get("mu2", 0.25)))
    Z = float(params.get("Z", -1.0))
    Y = float(params.get("Y", 1.0))
    eta_shell = float(params.get("eta_shell", 0.0))
    q0 = float(params.get("q0", 0.0))
    diag = r + Z * s2 + Y * s4 + eta_shell * (kmag - q0) ** 2
    return 1.0 + dt * diag.unsqueeze(0)


def linear_diag_term_t(Psi_t: torch.Tensor, backend: Any, params: Dict[str, Any]) -> torch.Tensor:
    # FIX(Bug#1): use actual stiffness symbols (s2, s2^2), not raw k^2, k^4
    s2, s4, kmag = _get_stiffness_diag(Psi_t, backend, params)
    r = float(params.get("r", params.get("mu2", 0.25)))
    Z = float(params.get("Z", -1.0))
    Y = float(params.get("Y", 1.0))
    eta_shell = float(params.get("eta_shell", 0.0))
    q0 = float(params.get("q0", 0.0))
    diag = r + Z * s2 + Y * s4 + eta_shell * (kmag - q0) ** 2
    Psi_k = backend._fft_field(Psi_t)
    return backend._ifft_field(diag.unsqueeze(0) * Psi_k)


def residual_t(Psi_t: torch.Tensor, backend: Any, params: Dict[str, Any]) -> torch.Tensor:
    if backend_has_private_torch_api(backend):
        lin = backend._brazovskii_linear_term_t(Psi_t, params)
        fam = backend._family_term_t(Psi_t, params)
        lock = backend._locked_internal_penalty_t(Psi_t, params)
        shell = backend._shell_bias_term_t(Psi_t, params)
        nl = backend._local_nonlinear_term_t(Psi_t, params)
        classII = backend._classII_effective_term_t(Psi_t, params)
        return lin + fam + lock + shell + nl + classII
    res_np = backend.residual(to_numpy_state(Psi_t, backend), params)
    return to_torch_state(res_np, backend, params)


def explicit_rest_t(Psi_t: torch.Tensor, backend: Any, params: Dict[str, Any]) -> torch.Tensor:
    """
    Explicit (nonlinear + nondiagonal linear) part of the IMEX splitting.

    FIX(Bug#2): shell_bias term is NOT included here.
    shell_bias is a quadratic-diagonal term (eta*(|k|-q0)^2 * Psi_k) that belongs
    entirely in the implicit denominator (linear_denominator_t).  Including it here
    AND in the denominator counted it twice, so the IMEX fixed point satisfied
    (L + 2*shell)*Psi + N = 0 instead of the true R = (L + shell)*Psi + N = 0.
    With eta_shell=0 (default) the error was zero, but the structural bug is removed.
    """
    if backend_has_private_torch_api(backend):
        fam     = backend._family_term_t(Psi_t, params)
        lock    = backend._locked_internal_penalty_t(Psi_t, params)
        # shell_bias deliberately omitted — handled implicitly in linear_denominator_t
        nl      = backend._local_nonlinear_term_t(Psi_t, params)
        classII = backend._classII_effective_term_t(Psi_t, params)
        return fam + lock + nl + classII
    # Fallback: compute true residual minus full implicit diagonal (including shell)
    return residual_t(Psi_t, backend, params) - linear_diag_term_t(Psi_t, backend, params)


def gradient_flow_step_t(Psi_t: torch.Tensor, backend: Any, params: Dict[str, Any], dt: float) -> torch.Tensor:
    if backend_has_private_torch_api(backend):
        denom = linear_denominator_t(Psi_t, backend, params, dt)
        rest = explicit_rest_t(Psi_t, backend, params)
        Psi_k = backend._fft_field(Psi_t)
        rest_k = backend._fft_field(rest)
        return backend._ifft_field((Psi_k - dt * rest_k) / denom)
    # fallback: explicit Euler through public API
    res = residual_t(Psi_t, backend, params)
    return Psi_t - dt * res


def shell_energy_t(Psi_t: torch.Tensor, backend: Any, params: Dict[str, Any]) -> float:
    return float(backend.shell_free_energy(to_numpy_state(Psi_t, backend), params))


def reconstruct_orbit_tangents(Psi_corr: np.ndarray, hat_n: np.ndarray, q0: float, L: float):
    N = Psi_corr.shape[1]
    X, Y, Z = make_xyz_grid(N, L)  # sparse broadcasting views

    hat_n = normalize(hat_n)
    trial = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    if abs(np.dot(trial, hat_n)) > 0.8:
        trial = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    e1 = normalize(trial - np.dot(trial, hat_n) * hat_n)
    e2 = normalize(np.cross(hat_n, e1))

    # Direct broadcast (avoids the (3, N, N, N) coordinate stack).
    phase_n  = q0 * (hat_n[0] * X + hat_n[1] * Y + hat_n[2] * Z)
    phase_e1 = q0 * (e1[0]    * X + e1[1]    * Y + e1[2]    * Z)
    phase_e2 = q0 * (e2[0]    * X + e2[1]    * Y + e2[2]    * Z)

    amp = np.sqrt(np.sum(np.abs(Psi_corr) ** 2, axis=0)) + 1e-14
    z = Psi_corr / amp[None, ...]

    modA = np.cos(phase_n)
    modE = np.cos(phase_e1) - np.cos(phase_e2)
    modO = np.sin(phase_e1) + np.sin(phase_e2)

    Phi_A = 0.08 * modA[None, ...] * z
    Phi_E = 0.08 * modE[None, ...] * z
    Phi_O = 1j * 0.08 * modO[None, ...] * z

    return (
        np.asarray(Phi_A, dtype=np.complex128),
        np.asarray(Phi_E, dtype=np.complex128),
        np.asarray(Phi_O, dtype=np.complex128),
    )


# ============================================================
# Initialization provenance helpers
# ============================================================

def determine_init_mode(args: argparse.Namespace) -> str:
    if getattr(args, "init_mode", None):
        return str(args.init_mode)
    if getattr(args, "init", None):
        return "external"
    return "seed_plus_noise"


def build_initial_state(
    *,
    args: argparse.Namespace,
    N: int,
    Psi_BCC_seed: np.ndarray,
    Psi_corr_seed: np.ndarray,
) -> Tuple[np.ndarray, Optional[np.ndarray], Dict[str, Any]]:
    init_mode = determine_init_mode(args)
    noise_scale = float(getattr(args, "noise_scale", 0.0))
    noise_kind = str(getattr(args, "noise_kind", "complex_gaussian")).lower()

    if init_mode == "external":
        if args.init is None:
            raise ValueError("init_mode='external' requires --init <file>. ")
        Psi0 = np.load(args.init, allow_pickle=False).astype(np.complex128)
        if Psi0.shape != (3, N, N, N):
            raise ValueError(f"Initial field has shape {Psi0.shape}, expected (3,{N},{N},{N})")
        noise = None
        resolved_noise_kind = "none"
        uses_noise = False
        uses_branch_seed = False
    elif init_mode == "pure_noise":
        if noise_kind == "none" or noise_scale <= 0.0:
            raise ValueError("init_mode='pure_noise' requires noise_kind != 'none' and noise_scale > 0.")
        if noise_kind != "complex_gaussian":
            raise ValueError(f"Unsupported noise_kind: {noise_kind}")
        noise = (np.random.randn(3, N, N, N) + 1j * np.random.randn(3, N, N, N)) * noise_scale
        Psi0 = noise.astype(np.complex128)
        resolved_noise_kind = noise_kind
        uses_noise = True
        uses_branch_seed = False
    elif init_mode == "seed_plus_noise":
        if noise_kind == "none" or noise_scale <= 0.0:
            raise ValueError("init_mode='seed_plus_noise' requires noise_kind != 'none' and noise_scale > 0.")
        if noise_kind != "complex_gaussian":
            raise ValueError(f"Unsupported noise_kind: {noise_kind}")
        noise = (np.random.randn(3, N, N, N) + 1j * np.random.randn(3, N, N, N)) * noise_scale
        Psi0 = Psi_corr_seed + noise.astype(np.complex128)
        resolved_noise_kind = noise_kind
        uses_noise = True
        uses_branch_seed = True
    elif init_mode == "corr_seed":
        Psi0 = np.array(Psi_corr_seed, dtype=np.complex128, copy=True)
        noise = None
        resolved_noise_kind = "none"
        uses_noise = False
        uses_branch_seed = True
    elif init_mode == "bcc_seed":
        Psi0 = np.array(Psi_BCC_seed, dtype=np.complex128, copy=True)
        noise = None
        resolved_noise_kind = "none"
        uses_noise = False
        uses_branch_seed = True
    else:
        raise ValueError(f"Unknown init_mode: {init_mode}")

    info = {
        "init_mode": init_mode,
        "init_file": str(Path(args.init).expanduser().resolve()) if args.init is not None else None,
        "noise_kind": resolved_noise_kind,
        "noise_scale": float(noise_scale if uses_noise else 0.0),
        "uses_noise": bool(uses_noise),
        "uses_branch_seed": bool(uses_branch_seed),
        "uses_external_init": bool(init_mode == "external"),
        "uses_pure_random_init": bool(init_mode == "pure_noise"),
        "noise_generated_by_solver": bool(uses_noise and init_mode in {"pure_noise", "seed_plus_noise"}),
    }

    if noise is not None:
        abs_noise = np.abs(noise)
        info["noise_l2"] = float(np.sqrt(np.mean(abs_noise ** 2)))
        info["noise_linf"] = float(np.max(abs_noise))
    else:
        info["noise_l2"] = 0.0
        info["noise_linf"] = 0.0

    return np.asarray(Psi0, dtype=np.complex128), (None if noise is None else np.asarray(noise, dtype=np.complex128)), info


def make_methodology_note(*, laplacian_mode: str, init_mode: str, emergence_claim_safe: bool) -> str:
    if emergence_claim_safe:
        return (
            "This run uses laplacian_mode='spectral' with init_mode='pure_noise'; "
            "it is compatible with an unbiased emergence-style interpretation, subject to the usual numerical caveats."
        )
    if init_mode in {"seed_plus_noise", "corr_seed", "bcc_seed", "external"}:
        return (
            "This run is not an unbiased emergence test. It uses a seeded or externally supplied branch-style initialization "
            "and should be interpreted as branch continuation / stabilization / validation numerics."
        )
    if laplacian_mode in {"bcc_symbol", "mixed_bcc"}:
        return (
            "This run uses a BCC-sensitive stiffness backend and should not be cited as standalone evidence of spontaneous "
            "BCC emergence from isotropic spectral dynamics."
        )
    return (
        "This run is not flagged as emergence-safe. Consult init_mode and laplacian_mode before using it as evidence for "
        "spontaneous structure selection claims."
    )


# ============================================================
# Export writer
# ============================================================

def write_package(
    output_dir: Path,
    Psi_init: np.ndarray,
    noise_init: Optional[np.ndarray],
    Psi_corr: np.ndarray,
    Psi_BCC: np.ndarray,
    Phi_A: np.ndarray,
    Phi_E: np.ndarray,
    Phi_O: np.ndarray,
    hat_n: np.ndarray,
    patch_centers: np.ndarray,
    G_list: np.ndarray,
    Pi_fam_matrix: np.ndarray,
    config: Dict[str, Any],
    residual_history: np.ndarray,
    energy_history: np.ndarray,
    metadata: Dict[str, Any],
) -> None:
    ensure_dir(output_dir)
    np.save(output_dir / "Psi_init.npy", np.asarray(Psi_init, dtype=np.complex128))
    if noise_init is not None:
        np.save(output_dir / "noise_init.npy", np.asarray(noise_init, dtype=np.complex128))
    np.save(output_dir / "Psi_corr.npy", np.asarray(Psi_corr, dtype=np.complex128))
    np.save(output_dir / "Psi_BCC.npy", np.asarray(Psi_BCC, dtype=np.complex128))
    np.save(output_dir / "Phi_A.npy", np.asarray(Phi_A, dtype=np.complex128))
    np.save(output_dir / "Phi_E.npy", np.asarray(Phi_E, dtype=np.complex128))
    np.save(output_dir / "Phi_O.npy", np.asarray(Phi_O, dtype=np.complex128))
    np.save(output_dir / "hat_n.npy", np.asarray(hat_n, dtype=np.float64))
    np.save(output_dir / "patch_centers.npy", np.asarray(patch_centers, dtype=np.float64))
    np.save(output_dir / "G_list.npy", np.asarray(G_list, dtype=np.float64))
    np.save(output_dir / "Pi_fam_matrix.npy", np.asarray(Pi_fam_matrix, dtype=np.complex128))
    np.save(output_dir / "residual_history.npy", np.asarray(residual_history, dtype=np.float64))
    np.save(output_dir / "energy_history.npy", np.asarray(energy_history, dtype=np.float64))

    with open(output_dir / "config.json", "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)
    with open(output_dir / "metadata.json", "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)


# ============================================================
# CLI
# ============================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="PyTorch-accelerated TECT working-branch pseudospectral solver with extractor-format export."
    )
    p.add_argument("--grid", type=int, choices=[32, 64, 128], required=True)
    p.add_argument("--L", type=float, default=16.0)
    p.add_argument("--output", type=str, required=True)
    p.add_argument("--steps", type=int, default=2000)
    p.add_argument("--dt", type=float, default=5e-3)
    p.add_argument("--save-every", type=int, default=100)
    p.add_argument("--tol", type=float, default=1e-8)
    p.add_argument("--backend", type=str, required=True)
    p.add_argument("--config", type=str, default=None,
                   help="Path to a JSON config (e.g. PDE/config_template_brazovskii.json). "
                        "Keys present in the JSON override the built-in defaults. "
                        "Omit to run with the Brazovskii-locked defaults hard-coded in make_default_config().")
    p.add_argument("--init", type=str, default=None, help="Optional initial Psi field (.npy), shape (3,N,N,N).")
    p.add_argument("--q0", type=float, default=None, help="Optional shell radius override.")
    p.add_argument("--seed", type=int, default=1234)
    p.add_argument("--device", type=str, default="auto", help="auto / cpu / cuda")
    p.add_argument("--torch-complex-dtype", type=str, default="complex128", choices=["complex64", "complex128"])
    p.add_argument("--laplacian-mode", type=str, default="spectral", choices=["spectral", "bcc_symbol", "mixed_bcc"])
    p.add_argument("--a-bcc", type=float, default=1.0)
    p.add_argument("--bcc-mix-epsilon", type=float, default=0.0)
    p.add_argument("--init-mode", type=str, default=None, choices=["external", "pure_noise", "seed_plus_noise", "corr_seed", "bcc_seed"],
                   help="Initialization provenance mode. Default: external if --init is supplied, otherwise seed_plus_noise for backward compatibility.")
    p.add_argument("--noise-scale", type=float, default=2e-3, help="Complex Gaussian noise amplitude for pure_noise / seed_plus_noise modes.")
    p.add_argument("--noise-kind", type=str, default="complex_gaussian", choices=["complex_gaussian", "none"],
                   help="Noise model used by solver-generated initialization.")
    return p


def main() -> None:
    args = build_parser().parse_args()
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    N = int(args.grid)
    L = float(args.L)
    output_dir = Path(args.output).expanduser().resolve()
    backend_path = Path(args.backend).expanduser().resolve()

    backend = load_module(backend_path)

    hat_n = make_default_hat_n()
    config = make_default_config(N=N, L=L, q0=args.q0, hat_n=hat_n)

    # --- Optional JSON config overlay (Brazovskii regime template, etc.) ----
    if args.config is not None:
        cfg_path = Path(args.config).expanduser().resolve()
        if not cfg_path.exists():
            raise FileNotFoundError(f"--config file not found: {cfg_path}")
        with open(cfg_path, "r", encoding="utf-8") as fh:
            overlay = json.load(fh)
        # Strip comment keys (underscore-prefixed) for safety
        overlay = {k: v for k, v in overlay.items() if not k.startswith("_")}
        config.update(overlay)
        config["_config_source"] = str(cfg_path)

    config["solver_dt"] = float(args.dt)
    config["solver_steps"] = int(args.steps)
    config["solver_save_every"] = int(args.save_every)
    config["solver_tol"] = float(args.tol)
    config["torch_complex_dtype"] = str(args.torch_complex_dtype)
    config["laplacian_mode"] = str(args.laplacian_mode)
    config["a_bcc"] = float(args.a_bcc)
    config["bcc_mix_epsilon"] = float(args.bcc_mix_epsilon)
    config["init_mode"] = determine_init_mode(args)
    config["noise_scale"] = float(args.noise_scale)
    config["noise_kind"] = str(args.noise_kind)

    if args.device == "auto":
        config["use_cuda"] = True
    else:
        config["device"] = str(args.device)
        config["use_cuda"] = str(args.device).lower() == "cuda"

    # Align with backend device choice if available
    if hasattr(backend, "_get_device"):
        actual_device = backend._get_device(config)
    else:
        actual_device = torch.device("cuda" if config.get("use_cuda", True) and torch.cuda.is_available() else "cpu")

    q0 = float(config["q0"])
    patch_centers = make_default_patch_centers(hat_n)
    G_list = make_bcc_shell_G_list(N=N, L=L, q0=q0)
    Pi_fam_matrix = make_default_family_projector()

    Psi_BCC_seed, Psi_corr_seed, _, _, _ = make_mock_branch_data(
        N=N, L=L, q0=q0, hat_n=hat_n,
        quartic_lambda=config.get("quartic_lambda"),
        sextic_gamma=config.get("sextic_gamma"),
    )

    Psi0, noise_init, init_info = build_initial_state(
        args=args,
        N=N,
        Psi_BCC_seed=Psi_BCC_seed,
        Psi_corr_seed=Psi_corr_seed,
    )

    Psi_t = to_torch_state(Psi0, backend, config)

    residual_history = []
    energy_history = []

    print("=" * 72)
    print("TECT torch working-branch solver")
    print("=" * 72)
    print(f"grid        : {N}^3")
    print(f"L           : {L}")
    print(f"q0          : {q0:.16e}")
    print(f"steps       : {args.steps}")
    print(f"dt          : {args.dt}")
    print(f"backend     : {backend_path}")
    print(f"device      : {actual_device}")
    print(f"dtype       : {config['torch_complex_dtype']}")
    print(f"output      : {output_dir}")
    print(f"lap_mode    : {config['laplacian_mode']}")
    print(f"a_bcc       : {config['a_bcc']}")
    print(f"bcc_mix_eps : {config['bcc_mix_epsilon']}")
    _lam   = float(config.get("quartic_lambda", config.get("lambda", float('nan'))))
    _gam   = float(config.get("sextic_gamma",   config.get("gamma",  float('nan'))))
    _r     = float(config.get("r", config.get("mu2", float('nan'))))
    _regime = ("Brazovskii" if (_lam < 0 and _gam > 0.5) else
               ("Ginzburg-Landau" if (_lam > 0 and _gam < 0.5) else "Unknown"))
    print(f"config src  : {config.get('_config_source', '<built-in Brazovskii defaults>')}")
    print(f"regime      : {_regime}   (r/mu2={_r:+.3f}, lambda={_lam:+.3f}, gamma={_gam:+.3f})")
    print(f"init_mode   : {init_info['init_mode']}")
    print(f"noise_kind  : {init_info['noise_kind']}")
    print(f"noise_scale : {init_info['noise_scale']}")
    print("-" * 72)

    steps_completed = 0
    for it in range(args.steps):
        res_t = residual_t(Psi_t, backend, config)
        res_norm = float(torch.sqrt(torch.mean(torch.abs(res_t) ** 2)).detach().cpu().item())
        energy = float(shell_energy_t(Psi_t, backend, config))

        residual_history.append(res_norm)
        energy_history.append(energy)
        steps_completed = it + 1

        if (it % args.save_every == 0) or (it == args.steps - 1):
            print(f"[step {it:06d}] residual={res_norm:.8e}  energy={energy:.8e}")

        if res_norm < args.tol:
            print(f"[converged] step={it}, residual={res_norm:.8e} < tol={args.tol:.8e}")
            break

        Psi_t = gradient_flow_step_t(Psi_t, backend, config, args.dt)

    Psi_corr = to_numpy_state(Psi_t, backend)
    Phi_A, Phi_E, Phi_O = reconstruct_orbit_tangents(Psi_corr, hat_n, q0, L)

    laplacian_mode = str(config["laplacian_mode"]).lower()
    bcc_mix_epsilon = float(config.get("bcc_mix_epsilon", 0.0))
    is_bcc_biased_backend = (laplacian_mode == "bcc_symbol") or (laplacian_mode == "mixed_bcc" and bcc_mix_epsilon > 0.0)
    emergence_claim_safe = (laplacian_mode == "spectral") and bool(init_info["uses_pure_random_init"])

    metadata = {
        "generator": "tect_solver_pt_v3.py",
        "backend": str(backend_path),
        "grid": N,
        "L": L,
        "q0": q0,
        "steps_requested": int(args.steps),
        "steps_completed": int(steps_completed),
        "dt": float(args.dt),
        "tol": float(args.tol),
        "device": str(actual_device),
        "torch_complex_dtype": str(config["torch_complex_dtype"]),
        "laplacian_mode": laplacian_mode,
        "a_bcc": float(config.get("a_bcc", 1.0)),
        "bcc_mix_epsilon": bcc_mix_epsilon,
        "is_bcc_biased_backend": bool(is_bcc_biased_backend),
        "init_mode": init_info["init_mode"],
        "init_file": init_info["init_file"],
        "noise_kind": init_info["noise_kind"],
        "noise_scale": init_info["noise_scale"],
        "noise_generated_by_solver": bool(init_info["noise_generated_by_solver"]),
        "uses_noise": bool(init_info["uses_noise"]),
        "uses_branch_seed": bool(init_info["uses_branch_seed"]),
        "uses_external_init": bool(init_info["uses_external_init"]),
        "uses_pure_random_init": bool(init_info["uses_pure_random_init"]),
        "noise_l2": float(init_info["noise_l2"]),
        "noise_linf": float(init_info["noise_linf"]),
        "residual_final": float(residual_history[-1]),
        "energy_final": float(energy_history[-1]),
        "emergence_claim_safe": bool(emergence_claim_safe),
        "description": "Torch-accelerated executable working-branch solver with explicit initialization/noise provenance.",
        "methodology_note": make_methodology_note(laplacian_mode=laplacian_mode, init_mode=init_info["init_mode"], emergence_claim_safe=bool(emergence_claim_safe)),
        "format": "TECT-NPY-v2-final",
        "bugfixes": ["Bug#1:IMEX-stiffness-mismatch", "Bug#2:shell-bias-double-count"],
    }

    if not metadata["emergence_claim_safe"]:
        print("[methodology] This run is NOT emergence-safe. See metadata.json for init/back-end provenance.")

    write_package(
        output_dir=output_dir,
        Psi_init=Psi0,
        noise_init=noise_init,
        Psi_corr=Psi_corr,
        Psi_BCC=Psi_BCC_seed,
        Phi_A=Phi_A,
        Phi_E=Phi_E,
        Phi_O=Phi_O,
        hat_n=hat_n,
        patch_centers=patch_centers,
        G_list=G_list,
        Pi_fam_matrix=Pi_fam_matrix,
        config=config,
        residual_history=np.asarray(residual_history, dtype=np.float64),
        energy_history=np.asarray(energy_history, dtype=np.float64),
        metadata=metadata,
    )

    print("-" * 72)
    print("Export completed.")
    print(f"final residual : {residual_history[-1]:.16e}")
    print(f"final energy   : {energy_history[-1]:.16e}")
    print("=" * 72)


if __name__ == "__main__":
    main()
