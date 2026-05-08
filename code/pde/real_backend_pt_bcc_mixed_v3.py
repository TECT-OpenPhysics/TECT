#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v3.1
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===

from __future__ import annotations

import math
from functools import lru_cache
from typing import Any, Dict, Tuple, Optional

import numpy as np
import torch

try:
    import intel_extension_for_pytorch as ipex
except ImportError:
    pass

# ============================================================
# Torch / NumPy bridge
# ============================================================

def _get_device(params: Dict[str, Any]) -> torch.device:
    dev = params.get("device", None)
    if dev is not None:
        return torch.device(str(dev))

    use_cuda = bool(params.get("use_cuda", True))
    if use_cuda and torch.cuda.is_available():
        return torch.device("cuda")

    use_xpu = bool(params.get("use_xpu", True))
    if use_xpu and hasattr(torch, "xpu") and torch.xpu.is_available():
        return torch.device("xpu")

    return torch.device("cpu")

def _get_cdtype(params: Dict[str, Any]):
    name = str(params.get("torch_complex_dtype", "complex128")).lower()
    if name in ("complex64", "c64"):
        return torch.complex64
    return torch.complex128


def _get_rdtype_from_complex(cdtype):
    return torch.float32 if cdtype == torch.complex64 else torch.float64


def _to_torch(arr: np.ndarray | torch.Tensor, params: Dict[str, Any], *, complex_required: bool = True) -> torch.Tensor:
    device = _get_device(params)
    cdtype = _get_cdtype(params)
    rdtype = _get_rdtype_from_complex(cdtype)

    if isinstance(arr, torch.Tensor):
        if complex_required and not torch.is_complex(arr):
            arr = arr.to(dtype=cdtype)
        elif (not complex_required) and torch.is_complex(arr):
            arr = arr.real.to(dtype=rdtype)
        elif (not complex_required):
            arr = arr.to(dtype=rdtype)
        else:
            arr = arr.to(dtype=cdtype)
        return arr.to(device=device)

    narr = np.asarray(arr)
    if complex_required:
        if not np.iscomplexobj(narr):
            narr = narr.astype(np.complex128)
        t = torch.from_numpy(narr)
        return t.to(device=device, dtype=cdtype)
    else:
        if np.iscomplexobj(narr):
            narr = np.asarray(narr.real)
        t = torch.from_numpy(np.asarray(narr))
        return t.to(device=device, dtype=rdtype)


def _to_numpy(t: torch.Tensor) -> np.ndarray:
    return t.detach().cpu().numpy()


def _shape3(Psi: np.ndarray | torch.Tensor) -> Tuple[int, int, int]:
    if Psi.ndim != 4 or Psi.shape[0] != 3:
        raise ValueError("Psi must have shape (3, Nx, Ny, Nz)")
    return int(Psi.shape[1]), int(Psi.shape[2]), int(Psi.shape[3])


def _shape3_scalar(f: np.ndarray | torch.Tensor) -> Tuple[int, int, int]:
    if f.ndim != 3:
        raise ValueError("Scalar field must have shape (Nx, Ny, Nz)")
    return int(f.shape[0]), int(f.shape[1]), int(f.shape[2])


def _params_lengths(params: Dict[str, Any]) -> Tuple[float, float, float]:
    return float(params["Lx"]), float(params["Ly"]), float(params["Lz"])


# ============================================================
# Cached k-grids
# ============================================================

@lru_cache(maxsize=32)
def _kgrid_cached(
    Nx: int,
    Ny: int,
    Nz: int,
    Lx: float,
    Ly: float,
    Lz: float,
    device_str: str,
    dtype_str: str,
):
    """
    Cache of all spectral grids derived from (N, L, device, rdtype).
    Returns the public tuple ``(kx, ky, kz, k2, k4, kmag)`` for backward
    compatibility. The full (3D) ``KX, KY, KZ`` meshgrid tensors are
    cached separately and returned by ``_kmesh_cached`` so that hot-loop
    sites (``_grad_components_t``, ``_spectral_derivative_scalar_t``)
    do not allocate fresh ``(N, N, N)`` real tensors on every call.

    All entries of this cache are tied to a single (device, rdtype)
    pair; mixing devices or precisions therefore fills new cache rows
    rather than aliasing — this is intentional.
    """
    device = torch.device(device_str)
    rdtype = torch.float32 if dtype_str == "float32" else torch.float64

    kx = 2.0 * math.pi * torch.fft.fftfreq(Nx, d=Lx / Nx, device=device, dtype=rdtype)
    ky = 2.0 * math.pi * torch.fft.fftfreq(Ny, d=Ly / Ny, device=device, dtype=rdtype)
    kz = 2.0 * math.pi * torch.fft.fftfreq(Nz, d=Lz / Nz, device=device, dtype=rdtype)

    KX, KY, KZ = torch.meshgrid(kx, ky, kz, indexing="ij")
    k2 = KX**2 + KY**2 + KZ**2
    k4 = k2**2
    kmag = torch.sqrt(k2)
    return kx, ky, kz, k2, k4, kmag


@lru_cache(maxsize=32)
def _kmesh_cached(
    Nx: int,
    Ny: int,
    Nz: int,
    Lx: float,
    Ly: float,
    Lz: float,
    device_str: str,
    dtype_str: str,
):
    """
    Return the full 3D ``(KX, KY, KZ)`` meshgrid tensors. These are
    materialised once per ``(N, L, device, rdtype)`` cell and reused by
    every spectral-derivative evaluation. Memory cost: ``3 * Nx*Ny*Nz *
    sizeof(rdtype)`` bytes per cache entry (≈ 50 MB at N=128, float64),
    which is the same memory we previously allocated and freed once per
    RHS evaluation — i.e. the cache pays for itself after the first
    step and removes a ~150 MB/step allocation/free traffic from the
    inner loop.
    """
    device = torch.device(device_str)
    rdtype = torch.float32 if dtype_str == "float32" else torch.float64
    kx = 2.0 * math.pi * torch.fft.fftfreq(Nx, d=Lx / Nx, device=device, dtype=rdtype)
    ky = 2.0 * math.pi * torch.fft.fftfreq(Ny, d=Ly / Ny, device=device, dtype=rdtype)
    kz = 2.0 * math.pi * torch.fft.fftfreq(Nz, d=Lz / Nz, device=device, dtype=rdtype)
    KX, KY, KZ = torch.meshgrid(kx, ky, kz, indexing="ij")
    return KX, KY, KZ


def _get_kmesh(params: Dict[str, Any], Psi: np.ndarray | torch.Tensor):
    """Hot-path accessor — returns cached ``(KX, KY, KZ)`` 3D meshgrid."""
    Nx, Ny, Nz = _shape3(Psi)
    Lx, Ly, Lz = _params_lengths(params)
    device = _get_device(params)
    cdtype = _get_cdtype(params)
    rdtype = _get_rdtype_from_complex(cdtype)
    return _kmesh_cached(
        Nx, Ny, Nz, Lx, Ly, Lz,
        str(device),
        "float32" if rdtype == torch.float32 else "float64",
    )


def _get_kmesh_scalar(params: Dict[str, Any], f: np.ndarray | torch.Tensor):
    Nx, Ny, Nz = _shape3_scalar(f)
    Lx, Ly, Lz = _params_lengths(params)
    device = _get_device(params)
    cdtype = _get_cdtype(params)
    rdtype = _get_rdtype_from_complex(cdtype)
    return _kmesh_cached(
        Nx, Ny, Nz, Lx, Ly, Lz,
        str(device),
        "float32" if rdtype == torch.float32 else "float64",
    )


def _get_kgrid(params: Dict[str, Any], Psi: np.ndarray | torch.Tensor):
    Nx, Ny, Nz = _shape3(Psi)
    Lx, Ly, Lz = _params_lengths(params)
    device = _get_device(params)
    cdtype = _get_cdtype(params)
    rdtype = _get_rdtype_from_complex(cdtype)
    return _kgrid_cached(
        Nx, Ny, Nz, Lx, Ly, Lz,
        str(device),
        "float32" if rdtype == torch.float32 else "float64",
    )


def _get_kgrid_scalar(params: Dict[str, Any], f: np.ndarray | torch.Tensor):
    Nx, Ny, Nz = _shape3_scalar(f)
    Lx, Ly, Lz = _params_lengths(params)
    device = _get_device(params)
    cdtype = _get_cdtype(params)
    rdtype = _get_rdtype_from_complex(cdtype)
    return _kgrid_cached(
        Nx, Ny, Nz, Lx, Ly, Lz,
        str(device),
        "float32" if rdtype == torch.float32 else "float64",
    )


# ============================================================
# Spectral operators
# ============================================================

def _fft_field(Psi_t: torch.Tensor) -> torch.Tensor:
    return torch.fft.fftn(Psi_t, dim=(1, 2, 3))


def _ifft_field(Psi_k: torch.Tensor) -> torch.Tensor:
    return torch.fft.ifftn(Psi_k, dim=(1, 2, 3))


def _laplacian_t(Psi_t: torch.Tensor, params: Dict[str, Any]) -> torch.Tensor:
    s2, _, _ = _stiffness_symbols_t(params, Psi_t)
    Psi_k = _fft_field(Psi_t)
    return _ifft_field(-s2.unsqueeze(0) * Psi_k)


def _biharmonic_t(Psi_t: torch.Tensor, params: Dict[str, Any]) -> torch.Tensor:
    _, s4, _ = _stiffness_symbols_t(params, Psi_t)
    Psi_k = _fft_field(Psi_t)
    return _ifft_field(s4.unsqueeze(0) * Psi_k)


def _grad_components_t(Psi_t: torch.Tensor, params: Dict[str, Any]) -> torch.Tensor:
    """
    Return grad_i Psi with shape (3, 3, Nx, Ny, Nz): [i, comp, ...].

    Uses the cached 3-D meshgrid (``_get_kmesh``) — no per-call
    ``torch.meshgrid`` allocation. The intermediate
    ``1j * K[i].unsqueeze(0) * Psi_k`` is materialised inside
    ``_ifft_field``; that is the dominant memory event per axis and is
    unavoidable without rewriting the IFFT to take a generator.
    """
    K = _get_kmesh(params, Psi_t)  # cached (KX, KY, KZ)
    Psi_k = _fft_field(Psi_t)
    out = []
    for i in range(3):
        out.append(_ifft_field(1j * K[i].unsqueeze(0) * Psi_k))
    return torch.stack(out, dim=0)


def _spectral_derivative_scalar_t(f_t: torch.Tensor, axis: int, params: Dict[str, Any]) -> torch.Tensor:
    if f_t.ndim != 3:
        raise ValueError("Scalar field must have shape (Nx, Ny, Nz)")
    K = _get_kmesh_scalar(params, f_t)  # cached (KX, KY, KZ)
    fk = torch.fft.fftn(f_t, dim=(0, 1, 2))
    return torch.fft.ifftn(1j * K[axis] * fk, dim=(0, 1, 2))


def _bcc_positive_symbol_from_axes(kx: torch.Tensor, ky: torch.Tensor, kz: torch.Tensor, a_bcc: float) -> torch.Tensor:
    # 1-D ``kx, ky, kz`` arrive from ``_kgrid_cached``. Broadcast their
    # cosines directly without forming a fresh 3-D meshgrid: the product
    # ``cos(KX) * cos(KY) * cos(KZ)`` is identical algebraically and
    # avoids a ``3 * N**3`` real-tensor allocation per call.
    cx = torch.cos(0.5 * a_bcc * kx).reshape(-1, 1, 1)
    cy = torch.cos(0.5 * a_bcc * ky).reshape(1, -1, 1)
    cz = torch.cos(0.5 * a_bcc * kz).reshape(1, 1, -1)
    c = cx * cy * cz
    return (8.0 / (a_bcc ** 2)) * (1.0 - c)


def _stiffness_symbols_t(params: Dict[str, Any], Psi: np.ndarray | torch.Tensor):
    kx, ky, kz, k2, _, kmag = _get_kgrid(params, Psi)
    mode = str(params.get("laplacian_mode", "spectral")).lower()
    if mode == "spectral":
        s2 = k2
    else:
        a_bcc = float(params.get("a_bcc", 1.0))
        if a_bcc <= 0.0:
            raise ValueError("params['a_bcc'] must be positive")
        bcc2 = _bcc_positive_symbol_from_axes(kx, ky, kz, a_bcc)
        if mode == "bcc_symbol":
            s2 = bcc2
        elif mode == "mixed_bcc":
            eps = float(params.get("bcc_mix_epsilon", 0.0))
            s2 = (1.0 - eps) * k2 + eps * bcc2
        else:
            raise ValueError(f"Unknown laplacian_mode: {mode}")
    s4 = s2 ** 2
    return s2, s4, kmag


# ============================================================
# Internal utilities
# ============================================================

def _rho_t(Psi_t: torch.Tensor) -> torch.Tensor:
    return torch.sum(torch.abs(Psi_t) ** 2, dim=0)


def _family_matrix_t(params: Dict[str, Any]) -> torch.Tensor:
    fam = np.asarray(params.get("family_masses", [0.0, 0.0, 0.0]), dtype=float)
    if fam.shape != (3,):
        raise ValueError("params['family_masses'] must be a length-3 list")
    return _to_torch(np.diag(fam.astype(np.complex128)), params, complex_required=True)


def _projector_P0_t(params: Dict[str, Any]) -> torch.Tensor:
    z0 = np.asarray(params.get("z0", [1.0, 1.0, 1.0]), dtype=np.complex128)
    nrm = np.linalg.norm(z0)
    if nrm < 1e-14:
        raise ValueError("params['z0'] must be nonzero")
    z0 = z0 / nrm
    P0 = np.outer(z0, np.conj(z0))
    return _to_torch(P0, params, complex_required=True)


def _locked_internal_penalty_t(Psi_t: torch.Tensor, params: Dict[str, Any]) -> torch.Tensor:
    k_lock = float(params.get("k_lock", 0.15))
    if abs(k_lock) < 1e-18:
        return torch.zeros_like(Psi_t)
    P0 = _projector_P0_t(params)
    I = torch.eye(3, device=Psi_t.device, dtype=Psi_t.dtype)
    return k_lock * torch.einsum("ab,bxyz->axyz", (I - P0), Psi_t)


def _family_term_t(Psi_t: torch.Tensor, params: Dict[str, Any]) -> torch.Tensor:
    M = _family_matrix_t(params)
    return torch.einsum("ab,bxyz->axyz", M, Psi_t)


def _shell_bias_term_t(Psi_t: torch.Tensor, params: Dict[str, Any]) -> torch.Tensor:
    eta_shell = float(params.get("eta_shell", 0.0))
    if abs(eta_shell) < 1e-18:
        return torch.zeros_like(Psi_t)
    _, _, _, _, _, kmag = _get_kgrid(params, Psi_t)
    q0 = float(params["q0"])
    Psi_k = _fft_field(Psi_t)
    penal = (kmag - q0).unsqueeze(0) ** 2 * Psi_k
    return _ifft_field(eta_shell * penal)


_KINETIC_CONVENTION_CHECKED = False


def _check_kinetic_convention(params: Dict[str, Any]) -> None:
    """One-shot consistency gate: verify (r, Z, Y) match Math38 Brazovskii
    expansion of Y(k^2 - q0^2)^2 + mu2.  Fires once per process; raises
    ValueError on mismatch so misconfigured runs fail loudly at launch."""
    global _KINETIC_CONVENTION_CHECKED
    if _KINETIC_CONVENTION_CHECKED:
        return
    _KINETIC_CONVENTION_CHECKED = True
    q0 = float(params.get("q0", 0.0))
    if q0 == 0.0:
        return  # q0 not set → skip (non-Brazovskii mode)
    mu2 = float(params.get("mu2", 0.26))
    r = float(params.get("r", params.get("mu2", 0.26)))
    Z = float(params.get("Z", -1.0))
    Y = float(params.get("Y", 1.0))
    Z_expect = -2.0 * Y * q0 ** 2
    r_expect = mu2 + Y * q0 ** 4
    tol = 1e-6
    errs = []
    if abs(Z - Z_expect) > tol:
        errs.append(f"Z={Z} but -2*Y*q0^2={Z_expect:.10f} (delta={Z - Z_expect:.2e})")
    if abs(r - r_expect) > tol:
        errs.append(f"r={r} but mu2+Y*q0^4={r_expect:.10f} (delta={r - r_expect:.2e})")
    if errs:
        raise ValueError(
            "[TECT kinetic convention gate] Config (r,Z,Y) inconsistent with "
            f"Math38 Brazovskii form Y(k^2-q0^2)^2+mu2:\n  " + "\n  ".join(errs)
            + "\n  See docs/manual/CODE_MANUAL.md §2 kinetic convention box."
        )


def _brazovskii_linear_term_t(Psi_t: torch.Tensor, params: Dict[str, Any]) -> torch.Tensor:
    r = float(params.get("r", params.get("mu2", 0.26)))
    Z = float(params.get("Z", -1.0))
    Y = float(params.get("Y", 1.0))
    return r * Psi_t - Z * _laplacian_t(Psi_t, params) + Y * _biharmonic_t(Psi_t, params)


def _local_nonlinear_term_t(Psi_t: torch.Tensor, params: Dict[str, Any]) -> torch.Tensor:
    lam = float(params.get("quartic_lambda", params.get("lambda", 0.40)))
    gamma = float(params.get("sextic_gamma", params.get("gamma", 0.0)))
    rho = _rho_t(Psi_t)
    return lam * rho.unsqueeze(0) * Psi_t + gamma * (rho ** 2).unsqueeze(0) * Psi_t


def _gellmann_embedded_tlist(params: Dict[str, Any]):
    T1 = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]], dtype=np.complex128)
    T2 = np.array([[0, -1j, 0], [1j, 0, 0], [0, 0, 0]], dtype=np.complex128)
    T3 = np.array([[1, 0, 0], [0, -1, 0], [0, 0, 0]], dtype=np.complex128)
    return [_to_torch(T1, params, complex_required=True),
            _to_torch(T2, params, complex_required=True),
            _to_torch(T3, params, complex_required=True)]


def _classII_effective_term_t(Psi_t: torch.Tensor, params: Dict[str, Any]) -> torch.Tensor:
    alpha_X = float(params.get("alpha_X", 0.0))
    beta_X = float(params.get("beta_X", 0.0))
    M_X = float(params.get("M_X", 1.0))
    cJJ = float(params.get("cJJ", 0.0))
    cJK = float(params.get("cJK", 0.0))

    if (abs(alpha_X) + abs(beta_X) + abs(cJJ) + abs(cJK)) < 1e-18:
        return torch.zeros_like(Psi_t)

    Tlist = _gellmann_embedded_tlist(params)
    rho = _rho_t(Psi_t) + 1e-12
    gradPsi = _grad_components_t(Psi_t, params)  # (i, comp, ...)
    gradrho = 2.0 * torch.real(torch.sum(torch.conj(Psi_t).unsqueeze(0) * gradPsi, dim=1))  # (i, ...)

    out = torch.zeros_like(Psi_t)
    prefJJ = cJJ * (alpha_X**2) / (M_X**2 + 1e-12)
    prefJK = cJK * (alpha_X * beta_X) / (M_X**2 + 1e-12)

    for T in Tlist:
        TPsi = torch.einsum("ab,bxyz->axyz", T, Psi_t)
        m = torch.sum(torch.conj(Psi_t) * TPsi, dim=0)
        q = m / rho

        gradm = torch.sum(torch.conj(gradPsi) * TPsi.unsqueeze(0), dim=1) + torch.sum(
            torch.conj(Psi_t).unsqueeze(0) * torch.einsum("ab,ibxyz->iaxyz", T, gradPsi), dim=1
        )
        K = gradm - q.unsqueeze(0) * gradrho

        divJ = torch.zeros_like(m)
        divK = torch.zeros_like(m)
        for i in range(3):
            divJ = divJ + _spectral_derivative_scalar_t(gradm[i], i, params)
            divK = divK + _spectral_derivative_scalar_t(K[i], i, params)

        channel_vec = TPsi - q.unsqueeze(0) * Psi_t
        out = out + prefJJ * divJ.unsqueeze(0) * channel_vec + prefJK * divK.unsqueeze(0) * channel_vec

    return out


# ============================================================
# Public backend API
# ============================================================

def apply_family_projector(Psi: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
    Psi_t = _to_torch(Psi, params, complex_required=True)
    weights = np.asarray(params.get("family_projector", [1.0, 1.0, 1.0]), dtype=float)
    if weights.shape != (3,):
        raise ValueError("params['family_projector'] must be length 3")
    P = _to_torch(np.diag(weights.astype(np.complex128)), params, complex_required=True)
    out = torch.einsum("ab,bxyz->axyz", P, Psi_t)
    return _to_numpy(out).astype(np.complex128, copy=False)


def residual(Psi: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
    """
    PyTorch-accelerated executable current working-branch residual.

    Honest scope:
    - This is NOT the unique final complete TECT PDE.
    - It is the current executable working branch:
        Brazovskii core + family splitting + internal locking + optional shell bias
        + executable proxy for the integrated-out Class II sector.
    """
    _check_kinetic_convention(params)
    Psi_t = _to_torch(Psi, params, complex_required=True)
    lin = _brazovskii_linear_term_t(Psi_t, params)
    fam = _family_term_t(Psi_t, params)
    lock = _locked_internal_penalty_t(Psi_t, params)
    shell_bias = _shell_bias_term_t(Psi_t, params)
    nl = _local_nonlinear_term_t(Psi_t, params)
    classII = _classII_effective_term_t(Psi_t, params)
    out = lin + fam + lock + shell_bias + nl + classII
    return _to_numpy(out).astype(np.complex128, copy=False)


def hessian_vec(Psi: np.ndarray, v: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
    """
    PyTorch-accelerated Fréchet derivative of the executable working-branch residual.

    Linear and local nonlinear terms are differentiated analytically.
    The Class II proxy is differentiated numerically.
    """
    Psi_t = _to_torch(Psi, params, complex_required=True)
    v_t = _to_torch(v, params, complex_required=True)

    lin_v = _brazovskii_linear_term_t(v_t, params)
    fam_v = _family_term_t(v_t, params)
    lock_v = _locked_internal_penalty_t(v_t, params)
    shell_v = _shell_bias_term_t(v_t, params)

    lam = float(params.get("quartic_lambda", params.get("lambda", 0.40)))
    gamma = float(params.get("sextic_gamma", params.get("gamma", 0.0)))
    rho = _rho_t(Psi_t)
    delta_rho = 2.0 * torch.real(torch.sum(torch.conj(Psi_t) * v_t, dim=0))

    dquartic = lam * (rho.unsqueeze(0) * v_t + delta_rho.unsqueeze(0) * Psi_t)
    dsextic = gamma * ((rho**2).unsqueeze(0) * v_t + 2.0 * rho.unsqueeze(0) * delta_rho.unsqueeze(0) * Psi_t)

    eps = float(params.get("eps_classII_hess", 5e-7))
    classII_p = _classII_effective_term_t(Psi_t + eps * v_t, params)
    classII_m = _classII_effective_term_t(Psi_t - eps * v_t, params)
    dclassII = (classII_p - classII_m) / (2.0 * eps)

    out = lin_v + fam_v + lock_v + shell_v + dquartic + dsextic + dclassII
    return _to_numpy(out).astype(np.complex128, copy=False)


def shell_free_energy(Psi: np.ndarray, params: Dict[str, Any]) -> float:
    """
    PyTorch-accelerated real shell free energy consistent with the executable working branch.
    """
    Psi_t = _to_torch(Psi, params, complex_required=True)
    Nx, Ny, Nz = _shape3(Psi_t)
    Lx, Ly, Lz = _params_lengths(params)
    dV = (Lx / Nx) * (Ly / Ny) * (Lz / Nz)

    r = float(params.get("r", params.get("mu2", 0.26)))
    Z = float(params.get("Z", -1.0))
    Y = float(params.get("Y", 1.0))
    lam = float(params.get("quartic_lambda", params.get("lambda", 0.40)))
    gamma = float(params.get("sextic_gamma", params.get("gamma", 0.0)))
    eta_shell = float(params.get("eta_shell", 0.0))
    q0 = float(params.get("q0", 0.0))

    rho = _rho_t(Psi_t)
    gradPsi = _grad_components_t(Psi_t, params)
    lapPsi = _laplacian_t(Psi_t, params)

    F_quad = 0.5 * r * torch.sum(rho)           # FIX(Bug#3): was missing r factor; correct: (r/2)*integral(|Psi|^2)
    F_grad = 0.5 * Z * torch.sum(torch.abs(gradPsi) ** 2)
    F_bi = 0.5 * Y * torch.sum(torch.abs(lapPsi) ** 2)

    MfamPsi = _family_term_t(Psi_t, params)
    F_fam = 0.5 * torch.sum(torch.real(torch.sum(torch.conj(Psi_t) * MfamPsi, dim=0)))

    lockPsi = _locked_internal_penalty_t(Psi_t, params)
    k_lock = float(params.get("k_lock", 0.15))
    F_lock = torch.zeros((), device=Psi_t.device, dtype=torch.real(Psi_t).dtype)
    if abs(k_lock) > 1e-18:
        F_lock = 0.5 / k_lock * torch.sum(torch.real(torch.sum(torch.conj(lockPsi) * lockPsi, dim=0)))

    F_shell = torch.zeros((), device=Psi_t.device, dtype=torch.real(Psi_t).dtype)
    if abs(eta_shell) > 1e-18:
        _, _, _, _, _, kmag = _get_kgrid(params, Psi_t)
        Psi_k = _fft_field(Psi_t)
        penal = (kmag - q0).unsqueeze(0) * Psi_k
        F_shell = 0.5 * eta_shell * torch.sum(torch.abs(penal) ** 2) / np.prod(Psi_t.shape[1:])

    F_q4 = 0.5 * lam * torch.sum(rho ** 2)
    F_q6 = (gamma / 3.0) * torch.sum(rho ** 3)

    alpha_X = float(params.get("alpha_X", 0.0))
    beta_X = float(params.get("beta_X", 0.0))
    M_X = float(params.get("M_X", 1.0))
    cJJ = float(params.get("cJJ", 0.0))
    cKK = float(params.get("cKK", 0.0))

    F_classII = torch.zeros((), device=Psi_t.device, dtype=torch.real(Psi_t).dtype)
    if (abs(alpha_X) + abs(beta_X) + abs(cJJ) + abs(cKK)) > 1e-18:
        Tlist = _gellmann_embedded_tlist(params)
        rho_safe = rho + 1e-12
        gradrho = 2.0 * torch.real(torch.sum(torch.conj(Psi_t).unsqueeze(0) * gradPsi, dim=1))
        prefJJ = cJJ * (alpha_X**2) / (M_X**2 + 1e-12)
        prefKK = cKK * (beta_X**2) / (M_X**2 + 1e-12)

        for T in Tlist:
            TPsi = torch.einsum("ab,bxyz->axyz", T, Psi_t)
            m = torch.sum(torch.conj(Psi_t) * TPsi, dim=0)
            q = m / rho_safe
            gradm = torch.sum(torch.conj(gradPsi) * TPsi.unsqueeze(0), dim=1) + torch.sum(
                torch.conj(Psi_t).unsqueeze(0) * torch.einsum("ab,ibxyz->iaxyz", T, gradPsi), dim=1
            )
            K = gradm - q.unsqueeze(0) * gradrho
            F_classII = F_classII + 0.5 * prefJJ * torch.sum(torch.abs(gradm) ** 2)
            F_classII = F_classII + 0.5 * prefKK * torch.sum(torch.abs(K) ** 2)

    F_total = dV * (F_quad + F_grad + F_bi + F_fam + F_lock + F_q4 + F_q6 + F_classII) + F_shell
    return float(torch.real(F_total).detach().cpu().item())


def branch_solver(delta_vec: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
    required = ["Psi_base", "Phi_A", "Phi_E", "Phi_O"]
    if not all(k in params for k in required):
        raise NotImplementedError(
            "branch_solver requires params['Psi_base'], params['Phi_A'], params['Phi_E'], params['Phi_O']."
        )
    d = np.asarray(delta_vec, dtype=float)
    Psi_base = np.asarray(params["Psi_base"], dtype=np.complex128)
    Phi_A = np.asarray(params["Phi_A"], dtype=np.complex128)
    Phi_E = np.asarray(params["Phi_E"], dtype=np.complex128)
    Phi_O = np.asarray(params["Phi_O"], dtype=np.complex128)
    return Psi_base + d[0] * Phi_A + d[1] * Phi_E + d[2] * Phi_O


def compute_fast_sector_from_harmonics(
    barA_G: Dict[Tuple[float, float, float], np.ndarray],
    orbit_harmonics: Dict[str, Dict[Tuple[float, float, float], np.ndarray]],
    params: Dict[str, Any],
):
    """
    Torch-accelerated harmonic-level finite evaluator for the fast six-row sector.
    Output format matches real_backend.py.
    """
    labels = ["A", "E", "O"]
    hat_n = np.asarray(params.get("hat_n", [1.0, 0.0, 0.0]), dtype=float)
    hat_n = hat_n / (np.linalg.norm(hat_n) + 1e-14)
    fast_scale = float(params.get("fast_scale", 1.0))

    device = _get_device(params)
    cdtype = _get_cdtype(params)

    Gkeys = sorted(barA_G.keys())
    if len(Gkeys) == 0:
        raise ValueError("barA_G is empty")

    S = {}
    Mdiag = {}
    for lab in labels:
        S_lab = torch.zeros((), device=device, dtype=cdtype)
        M_lab = torch.zeros((), device=device, dtype=torch.float64 if cdtype == torch.complex128 else torch.float32)
        for Gk in Gkeys:
            A = _to_torch(barA_G[Gk], params, complex_required=True)
            B = _to_torch(orbit_harmonics[lab][Gk], params, complex_required=True)
            S_lab = S_lab + torch.vdot(A, B)
            M_lab = M_lab + torch.real(torch.vdot(B, B))
        S[lab] = S_lab
        Mdiag[lab] = M_lab

    H = torch.zeros((3, 3), device=device, dtype=torch.float64 if cdtype == torch.complex128 else torch.float32)
    for i, li in enumerate(labels):
        for j, lj in enumerate(labels):
            Hij = torch.real(torch.conj(S[li]) * S[lj]) + (Mdiag[li] if i == j else 0.0)
            H[i, j] = fast_scale * Hij
    H = 0.5 * (H + H.T)

    CE = torch.zeros((), device=device, dtype=cdtype)
    CO = torch.zeros((), device=device, dtype=cdtype)
    hat_n_t = _to_torch(hat_n, params, complex_required=False)
    for Gk in Gkeys:
        G = _to_torch(np.asarray(Gk, dtype=float), params, complex_required=False)
        nproj = torch.dot(hat_n_t, G)
        A = _to_torch(barA_G[Gk], params, complex_required=True)
        BE = _to_torch(orbit_harmonics["E"][Gk], params, complex_required=True)
        BO = _to_torch(orbit_harmonics["O"][Gk], params, complex_required=True)
        CE = CE + nproj * torch.vdot(A, BE)
        CO = CO + nproj * torch.vdot(A, BO)

    out = {
        "H2_fast": _to_numpy(H),
        "A_E": float(torch.real(CE).detach().cpu().item()),
        "B_E": float(torch.imag(CE).detach().cpu().item()),
        "A_O": float(torch.real(CO).detach().cpu().item()),
        "B_O": float(torch.imag(CO).detach().cpu().item()),
        "overlaps": {k: complex(_to_numpy(v)) for k, v in S.items()},
        "norms": {k: float(v.detach().cpu().item()) for k, v in Mdiag.items()},
        "device": str(device),
        "torch_complex_dtype": str(cdtype),
    }
    return out
