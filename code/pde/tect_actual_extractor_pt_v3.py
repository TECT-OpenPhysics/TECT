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

import argparse
import importlib.util
import json
import math
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Callable, List

import numpy as np
import torch

try:
    import intel_extension_for_pytorch as ipex
except ImportError:
    pass

# ============================================================
# Utilities
# ============================================================

def eprint(*args: Any, **kwargs: Any) -> None:
    print(*args, file=sys.stderr, **kwargs)


def load_npy_required(path: Path, name: str) -> np.ndarray:
    f = path / name
    if not f.exists():
        raise FileNotFoundError(f"Required file not found: {f}")
    return np.load(f, allow_pickle=False)


def load_npy_optional(path: Path, name: str) -> Optional[np.ndarray]:
    f = path / name
    if not f.exists():
        return None
    return np.load(f, allow_pickle=False)


def load_config(path: Path) -> Dict[str, Any]:
    cfg_path = path / "config.json"
    if not cfg_path.exists():
        raise FileNotFoundError(f"Required config file not found: {cfg_path}")
    with open(cfg_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_metadata_optional(path: Path) -> Optional[Dict[str, Any]]:
    meta_path = path / "metadata.json"
    if not meta_path.exists():
        return None
    with open(meta_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def summarize_provenance(run_metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if run_metadata is None:
        return {
            "metadata_present": False,
            "emergence_claim_safe": None,
            "warning": "No metadata.json found in input package; initialization/back-end provenance could not be audited.",
        }

    lap_mode = str(run_metadata.get("laplacian_mode", "unknown"))
    init_mode = str(run_metadata.get("init_mode", "unknown"))
    safe = run_metadata.get("emergence_claim_safe", None)
    warning = None
    if safe is False:
        warning = (
            "This source run is NOT emergence-safe. Treat it as branch continuation / stabilization / validation "
            "unless independently justified otherwise."
        )
    return {
        "metadata_present": True,
        "backend_path": run_metadata.get("backend", None),
        "laplacian_mode": lap_mode,
        "init_mode": init_mode,
        "uses_noise": run_metadata.get("uses_noise", None),
        "uses_branch_seed": run_metadata.get("uses_branch_seed", None),
        "uses_external_init": run_metadata.get("uses_external_init", None),
        "uses_pure_random_init": run_metadata.get("uses_pure_random_init", None),
        "is_bcc_biased_backend": run_metadata.get("is_bcc_biased_backend", None),
        "emergence_claim_safe": safe,
        "methodology_note": run_metadata.get("methodology_note", None),
        "warning": warning,
    }


def load_backend_module(backend_path: Path):
    if not backend_path.exists():
        raise FileNotFoundError(f"Backend module not found: {backend_path}")
    spec = importlib.util.spec_from_file_location("tect_backend_pt", str(backend_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to load backend module from: {backend_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ensure_shape(arr: np.ndarray, shape: Tuple[int, ...], name: str) -> None:
    if arr.shape != shape:
        raise ValueError(f"{name} has shape {arr.shape}, expected {shape}")


def normalize_vector(v: np.ndarray, eps: float = 1e-14) -> np.ndarray:
    nrm = np.linalg.norm(v)
    if nrm < eps:
        raise ValueError("Cannot normalize near-zero vector.")
    return v / nrm


def P2(c: float) -> float:
    return 0.5 * (3.0 * c * c - 1.0)


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
    ]
    return all(hasattr(backend, name) for name in required)


def to_torch(arr: np.ndarray | torch.Tensor, backend: Any, params: Dict[str, Any], *, complex_required: bool = True) -> torch.Tensor:
    if backend_has_private_torch_api(backend):
        return backend._to_torch(arr, params, complex_required=complex_required)

    device = torch.device(str(params.get("device", "cpu")))
    cdtype_name = str(params.get("torch_complex_dtype", "complex128")).lower()
    cdtype = torch.complex64 if cdtype_name in ("complex64", "c64") else torch.complex128
    rdtype = torch.float32 if cdtype == torch.complex64 else torch.float64

    if isinstance(arr, torch.Tensor):
        if complex_required:
            return arr.to(device=device, dtype=cdtype)
        return arr.real.to(device=device, dtype=rdtype) if torch.is_complex(arr) else arr.to(device=device, dtype=rdtype)

    narr = np.asarray(arr)
    if complex_required:
        narr = narr.astype(np.complex128, copy=False)
        return torch.from_numpy(narr).to(device=device, dtype=cdtype)
    if np.iscomplexobj(narr):
        narr = np.asarray(narr.real)
    return torch.from_numpy(narr).to(device=device, dtype=rdtype)


def to_numpy(t: torch.Tensor, backend: Any) -> np.ndarray:
    if hasattr(backend, "_to_numpy"):
        return backend._to_numpy(t)
    return t.detach().cpu().numpy()


def get_device(backend: Any, params: Dict[str, Any]) -> torch.device:
    if hasattr(backend, "_get_device"):
        return backend._get_device(params)
    dev = params.get("device", None)
    if dev is not None:
        return torch.device(str(dev))
    use_cuda = bool(params.get("use_cuda", True))
    if use_cuda and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


# ============================================================
# k-grid / FFT helpers
# ============================================================

def build_torch_kgrid(Psi_t: torch.Tensor, backend: Any, params: Dict[str, Any]):
    if hasattr(backend, "_get_kgrid"):
        return backend._get_kgrid(params, Psi_t)

    if Psi_t.ndim != 4 or Psi_t.shape[0] != 3:
        raise ValueError("Psi must have shape (3, Nx, Ny, Nz)")
    Nx, Ny, Nz = int(Psi_t.shape[1]), int(Psi_t.shape[2]), int(Psi_t.shape[3])
    Lx, Ly, Lz = float(params["Lx"]), float(params["Ly"]), float(params["Lz"])
    device = get_device(backend, params)
    rdtype = torch.float32 if Psi_t.dtype == torch.complex64 else torch.float64

    kx = 2.0 * math.pi * torch.fft.fftfreq(Nx, d=Lx / Nx, device=device, dtype=rdtype)
    ky = 2.0 * math.pi * torch.fft.fftfreq(Ny, d=Ly / Ny, device=device, dtype=rdtype)
    kz = 2.0 * math.pi * torch.fft.fftfreq(Nz, d=Lz / Nz, device=device, dtype=rdtype)
    KX, KY, KZ = torch.meshgrid(kx, ky, kz, indexing="ij")
    K = torch.stack([KX, KY, KZ], dim=0)
    Kmag = torch.sqrt(torch.sum(K**2, dim=0))
    return kx, ky, kz, Kmag**2, (Kmag**2)**2, Kmag


def fft_field_t(Psi_t: torch.Tensor, backend: Any) -> torch.Tensor:
    if hasattr(backend, "_fft_field"):
        return backend._fft_field(Psi_t)
    return torch.fft.fftn(Psi_t, dim=(1, 2, 3))


def ifft_field_t(Psi_k: torch.Tensor, backend: Any) -> torch.Tensor:
    if hasattr(backend, "_ifft_field"):
        return backend._ifft_field(Psi_k)
    return torch.fft.ifftn(Psi_k, dim=(1, 2, 3))


# ============================================================
# Family projector
# ============================================================

def make_family_projector_t(
    backend: Any,
    params: Dict[str, Any],
    Pi_fam_matrix: Optional[np.ndarray],
) -> Callable[[torch.Tensor], torch.Tensor]:
    if hasattr(backend, "apply_family_projector"):
        def apply_family_projector_t(Psi_t: torch.Tensor) -> torch.Tensor:
            out_np = backend.apply_family_projector(to_numpy(Psi_t, backend), params)
            return to_torch(out_np, backend, params, complex_required=True)
        return apply_family_projector_t

    if Pi_fam_matrix is not None:
        P = to_torch(Pi_fam_matrix, backend, params, complex_required=True)

        def apply_family_projector_t(Psi_t: torch.Tensor) -> torch.Tensor:
            return torch.einsum("ab,bxyz->axyz", P, Psi_t)
        return apply_family_projector_t

    def identity(Psi_t: torch.Tensor) -> torch.Tensor:
        return Psi_t
    return identity


# ============================================================
# Harmonic extraction
# ============================================================

def nearest_axis_index_torch(axis: torch.Tensor, value: float, tol: float = 1e-8) -> int:
    idx = int(torch.argmin(torch.abs(axis - value)).detach().cpu().item())
    if abs(float(axis[idx].detach().cpu().item()) - value) > tol:
        raise ValueError(f"Could not match reciprocal value {value:.12e} on FFT axis within tol={tol}.")
    return idx


def reciprocal_index_from_vector_torch(
    G: np.ndarray,
    kx: torch.Tensor,
    ky: torch.Tensor,
    kz: torch.Tensor,
    tol: float = 1e-8,
) -> Tuple[int, int, int]:
    ix = nearest_axis_index_torch(kx, float(G[0]), tol=tol)
    iy = nearest_axis_index_torch(ky, float(G[1]), tol=tol)
    iz = nearest_axis_index_torch(kz, float(G[2]), tol=tol)
    return ix, iy, iz


def extract_shell_harmonics_t(
    Psi_t: torch.Tensor,
    G_list: np.ndarray,
    backend: Any,
    params: Dict[str, Any],
) -> Dict[Tuple[float, float, float], np.ndarray]:
    if G_list.ndim != 2 or G_list.shape[1] != 3:
        raise ValueError("G_list.npy must have shape (NG, 3).")
    kx, ky, kz, _, _, _ = build_torch_kgrid(Psi_t, backend, params)
    Psi_k = fft_field_t(Psi_t, backend) / np.prod(Psi_t.shape[1:])
    out: Dict[Tuple[float, float, float], np.ndarray] = {}
    for G in G_list:
        idx = reciprocal_index_from_vector_torch(G, kx, ky, kz)
        key = tuple(np.round(G.astype(float), 12))
        out[key] = np.array(to_numpy(Psi_k[:, idx[0], idx[1], idx[2]], backend), copy=True)
    return out


def load_orbit_fields_or_reconstruct_t(
    input_dir: Path,
    backend: Any,
    params: Dict[str, Any],
    Psi_corr_t: torch.Tensor,
    delta_corr: np.ndarray,
) -> Dict[str, torch.Tensor]:
    orbit: Dict[str, torch.Tensor] = {}
    labels = ["A", "E", "O"]
    files = {"A": "Phi_A.npy", "E": "Phi_E.npy", "O": "Phi_O.npy"}
    missing: List[str] = []

    Psi_shape = tuple(int(s) for s in Psi_corr_t.shape)
    for lab in labels:
        arr = load_npy_optional(input_dir, files[lab])
        if arr is None:
            missing.append(lab)
        else:
            ensure_shape(arr, Psi_shape, files[lab])
            orbit[lab] = to_torch(arr, backend, params, complex_required=True)

    if not missing:
        return orbit

    if not hasattr(backend, "branch_solver"):
        raise RuntimeError(f"Missing orbit fields {missing}, and backend.branch_solver(delta_vec, params) is not provided.")

    h = float(params.get("orbit_fd_step", 1e-4))
    for i, lab in enumerate(labels):
        if lab in orbit:
            continue
        d = np.zeros(3, dtype=float)
        d[i] = h
        Psi_p = backend.branch_solver(delta_corr + d, params)
        Psi_m = backend.branch_solver(delta_corr - d, params)
        ensure_shape(Psi_p, Psi_shape, "branch_solver(+)")
        ensure_shape(Psi_m, Psi_shape, "branch_solver(-)")
        orbit[lab] = to_torch((Psi_p - Psi_m) / (2.0 * h), backend, params, complex_required=True)

    return orbit


# ============================================================
# Patch projection
# ============================================================

def patch_mask_t(
    Psi_t: torch.Tensor,
    q0: float,
    hat_k_alpha: np.ndarray,
    dq: float,
    dtheta: float,
    backend: Any,
    params: Dict[str, Any],
) -> torch.Tensor:
    kx, ky, kz, _, _, Kmag = build_torch_kgrid(Psi_t, backend, params)
    KX, KY, KZ = torch.meshgrid(kx, ky, kz, indexing="ij")
    K = torch.stack([KX, KY, KZ], dim=0)
    kmag_ok = torch.abs(Kmag - q0) < dq
    Khat = K / (Kmag.unsqueeze(0) + 1e-14)
    hat_k = to_torch(np.asarray(hat_k_alpha, dtype=np.float64), backend, params, complex_required=False)
    cosang = torch.sum(Khat * hat_k[:, None, None, None], dim=0)
    ang_ok = torch.arccos(torch.clamp(cosang, -1.0, 1.0)) < dtheta
    return kmag_ok & ang_ok


def project_patch_t(Psi_t: torch.Tensor, mask_t: torch.Tensor, backend: Any) -> torch.Tensor:
    Psi_k = fft_field_t(Psi_t, backend)
    Psi_k = Psi_k * mask_t.unsqueeze(0)
    return ifft_field_t(Psi_k, backend)


# ============================================================
# Hessian-vector product
# ============================================================

def make_hessian_vec_t(backend: Any, params: Dict[str, Any]) -> Callable[[torch.Tensor, torch.Tensor], torch.Tensor]:
    if hasattr(backend, "hessian_vec"):
        def hessian_vec_t(Psi_t: torch.Tensor, v_t: torch.Tensor) -> torch.Tensor:
            out_np = backend.hessian_vec(to_numpy(Psi_t, backend), to_numpy(v_t, backend), params)
            return to_torch(out_np, backend, params, complex_required=True)
        return hessian_vec_t

    if not hasattr(backend, "residual"):
        raise RuntimeError("Backend must provide residual(Psi, params) if hessian_vec is absent.")

    eps_hess = float(params.get("eps_hess", 1e-6))

    def hessian_vec_t(Psi_t: torch.Tensor, v_t: torch.Tensor) -> torch.Tensor:
        Rp = backend.residual(to_numpy(Psi_t + eps_hess * v_t, backend), params)
        Rm = backend.residual(to_numpy(Psi_t - eps_hess * v_t, backend), params)
        return to_torch((Rp - Rm) / (2.0 * eps_hess), backend, params, complex_required=True)

    return hessian_vec_t


# ============================================================
# Torch-native patch low-mode extraction
# ============================================================

def complex_inner_t(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return torch.sum(torch.conj(a) * b)


def normalize_field_t(v_t: torch.Tensor) -> torch.Tensor:
    nrm = torch.sqrt(torch.real(complex_inner_t(v_t, v_t)) + 1e-18)
    return v_t / nrm


def orthogonalize_against_t(v_t: torch.Tensor, basis: List[torch.Tensor]) -> torch.Tensor:
    out = v_t
    for b in basis:
        coeff = complex_inner_t(b, out) / (complex_inner_t(b, b) + 1e-18)
        out = out - coeff * b
    return out


def extract_patch_mode_t(
    Psi_corr_t: torch.Tensor,
    patch_mask_alpha_t: torch.Tensor,
    apply_family_projector_t: Callable[[torch.Tensor], torch.Tensor],
    hessian_vec_t: Callable[[torch.Tensor, torch.Tensor], torch.Tensor],
    backend: Any,
    params: Dict[str, Any],
) -> Tuple[torch.Tensor, float, float]:
    """
    Matrix-free torch-native low-mode extraction.

    We minimize ||H v||^2 under ||v||=1 on the patch-projected space.
    This targets the smallest-magnitude eigenmode and remains GPU-friendly.
    """
    steps = int(params.get("pt_mode_steps", 120))
    lr = float(params.get("pt_mode_lr", 0.15))
    restarts = int(params.get("pt_mode_restarts", 2))
    strict_project_family = bool(params.get("project_family_in_eigensolve", False))

    def project_all(v_t: torch.Tensor) -> torch.Tensor:
        out = project_patch_t(v_t, patch_mask_alpha_t, backend)
        if strict_project_family:
            out = apply_family_projector_t(out)
        return out

    best = None
    best_obj = None
    basis: List[torch.Tensor] = []

    for _ in range(restarts):
        v = torch.randn_like(Psi_corr_t)
        v = project_all(v)
        v = orthogonalize_against_t(v, basis)
        v = normalize_field_t(v)

        for _it in range(steps):
            Hv = project_all(hessian_vec_t(Psi_corr_t, v))
            HHv = project_all(hessian_vec_t(Psi_corr_t, Hv))
            mu = torch.real(complex_inner_t(v, HHv))
            grad = HHv - mu * v
            v = v - lr * grad
            v = project_all(v)
            v = orthogonalize_against_t(v, basis)
            v = normalize_field_t(v)

        Hv = project_all(hessian_vec_t(Psi_corr_t, v))
        obj = float(torch.real(complex_inner_t(Hv, Hv)).detach().cpu().item())
        if best_obj is None or obj < best_obj:
            best_obj = obj
            best = v.detach().clone()

    if best is None:
        raise RuntimeError("Failed to extract patch mode.")

    chi = normalize_field_t(best)
    Hchi = project_all(hessian_vec_t(Psi_corr_t, chi))
    lam = complex_inner_t(chi, Hchi) / (complex_inner_t(chi, chi) + 1e-18)
    m2 = float(torch.real(lam).detach().cpu().item())

    chi_fam = apply_family_projector_t(chi)
    Nalpha = float(
        (torch.real(complex_inner_t(chi_fam, chi_fam)) / (torch.real(complex_inner_t(chi, chi)) + 1e-18))
        .detach()
        .cpu()
        .item()
    )
    return chi, m2, Nalpha


# ============================================================
# Quartic coefficient extraction
# ============================================================

def extract_galpha_from_energy_t(
    Psi_corr_t: torch.Tensor,
    chi_alpha_t: torch.Tensor,
    backend: Any,
    params: Dict[str, Any],
) -> float:
    if not hasattr(backend, "shell_free_energy"):
        raise RuntimeError("Backend must provide shell_free_energy(Psi, params).")

    h = float(params.get("h_quartic", 5e-4))

    def F(t: float) -> float:
        val = backend.shell_free_energy(to_numpy(Psi_corr_t + t * chi_alpha_t, backend), params)
        return float(np.real(val))

    Fm2 = F(-2.0 * h)
    Fm1 = F(-1.0 * h)
    F0 = F(0.0)
    Fp1 = F(1.0 * h)
    Fp2 = F(2.0 * h)

    fourth_deriv = (Fm2 - 4.0 * Fm1 + 6.0 * F0 - 4.0 * Fp1 + Fp2) / (h ** 4)
    g_alpha = fourth_deriv / 12.0
    return float(g_alpha)


# ============================================================
# Raw moments and observables
# ============================================================

def compute_raw_moments(
    hat_n: np.ndarray,
    patch_centers: np.ndarray,
    N_alpha: np.ndarray,
    m_alpha2: np.ndarray,
    g_alpha: np.ndarray,
) -> Tuple[float, float, float, float]:
    W0 = 0.0
    W2 = 0.0
    M2 = 0.0
    G4 = 0.0
    for hk, Nw, m2, g4 in zip(patch_centers, N_alpha, m_alpha2, g_alpha):
        hk = normalize_vector(np.asarray(hk, dtype=float))
        c = float(np.dot(hat_n, hk))
        W0 += float(Nw)
        W2 += float(Nw) * P2(c)
        M2 += float(Nw) * float(m2)
        G4 += float(Nw) * float(g4)
    return W0, W2, M2, G4


def compute_effective_observables(W0: float, W2: float, M2: float, G4: float) -> Dict[str, float]:
    if W0 <= 0.0:
        raise ValueError(f"W0 must be positive, got {W0}")

    _nan = float("nan")

    # Soft-fail: tachyonic or unstable phase (M2 ≤ 0 means the BCC shell is not
    # a genuine mass-generating condensate at this parameter point).  We do NOT
    # crash; instead we record phase_status and set derived quantities to NaN so
    # that the raw moments (W0, W2, M2, G4) and patchwise m_α² are still saved.
    if M2 <= 0.0:
        eps_lock = 3.0 * W2 / W0
        return {
            "phase_status": "tachyonic_or_unstable",
            "mstar2":    _nan,
            "mstar":     _nan,
            "geff":      G4 / W0,   # dimensionless coupling is still well-defined
            "eps_lock":  eps_lock,
            "Zcub":      _nan,      # involves M2^{3/2} → singular
        }

    mstar2 = M2 / W0
    mstar = math.sqrt(mstar2)
    geff = G4 / W0

    # NOTE (geometric identity): eps_lock = 3*W2/W0 is determined entirely by the
    # choice of patch_centers geometry and the family projector, NOT by the field Psi.
    # With the default 8-patch layout (2 polar + 6 equatorial) and identity family
    # projector (N_alpha=1 for all patches), W0=8 and W2=-1 are guaranteed by
    # construction, so eps_lock = 3*(-1)/8 = -3/8 identically for any converged field.
    # Do NOT interpret this as evidence of a dynamical or topological fixed point.
    eps_lock = 3.0 * W2 / W0

    Zcub = -(G4 ** 2 * W2) / (48.0 * math.pi * (W0 ** 1.5) * (M2 ** 1.5))
    return {
        "phase_status": "condensed",
        "mstar2":    mstar2,
        "mstar":     mstar,
        "geff":      geff,
        "eps_lock":  eps_lock,
        "Zcub":      Zcub,
    }


def compute_theory_mstar2(params: Dict[str, Any]) -> Dict[str, float]:
    """
    Closed-form m*^2 prediction from Math37 Addendum A (theory tag
    `Math37-AddA-2026-04-15`): BCC-constellation-normalized (K_4=1,
    K_6=5/2), with I_3=1/3 locked by cubic symmetry and the
    first-order Brazovskii lock phi0^2 = -4 lambda/(15 gamma).

        m*^2_TECT = [ 2 mu^2 + 12 lambda phi0^2 + 60 gamma phi0^4
                     + alpha^2 q0^2 / M_X^2 ] / ( |lambda| / 6 )

    Also emits R_patch = 45/16 (the extractor-vs-theory projection
    ratio for the legacy 8-patch layout), so callers can compute
    m*^2_num_corrected = R_patch * (M2 / W0) when comparing against
    the analytical value.

    Returns NaN fields if required parameters are missing.
    """
    _nan = float("nan")
    try:
        mu2    = float(params["mu2"])
        lam    = float(params["quartic_lambda"])
        gam    = float(params["sextic_gamma"])
    except Exception:
        return {
            "phi0_sq":                _nan,
            "phi0":                   _nan,
            "M_sq_bare":              _nan,
            "classII_contrib":        _nan,
            "lambda_parallel":        _nan,
            "mstar2_theory_analytic": _nan,
            "theory_tag":             "Math37-AddA-2026-04-15",
            "status":                 "missing_params",
        }

    # Constellation normalization constants (BCC first shell, 12 vectors)
    K4 = 1.0
    K6 = 2.5  # = 5/2

    # First-order Brazovskii lock for the reduced potential
    #   F(phi) = mu^2 phi^2 + lambda K4 phi^4 + gamma K6 phi^6
    # with K4=1, K6=5/2:  V(phi0)=V(0) & V'(phi0)=0  =>
    #   phi0^2 = -2 lambda / ( 3 K6 gamma ) = -4 lambda / (15 gamma)
    denom = 3.0 * K6 * gam
    phi0_sq = _nan if abs(denom) < 1e-30 else (-2.0 * lam / denom)
    phi0    = math.sqrt(phi0_sq) if (phi0_sq == phi0_sq and phi0_sq > 0) else _nan

    # Bare Hessian at phi0 (note 60 gamma = 30 K6 gamma with K6=5/2):
    #   M^2 = 2 mu^2 + 12 K4 lambda phi0^2 + 30 K6 gamma phi0^4
    if phi0_sq == phi0_sq:
        M_sq_bare = (2.0 * mu2
                     + 12.0 * K4 * lam * phi0_sq
                     + 30.0 * K6 * gam * (phi0_sq ** 2))
    else:
        M_sq_bare = _nan

    # Class II contribution: alpha^2 q0^2 / M_X^2
    alpha_X = float(params.get("alpha_X", 0.0))
    q0      = float(params.get("q0",      0.0))
    M_X     = float(params.get("M_X",     0.0))
    if M_X > 0.0:
        classII_contrib = (alpha_X ** 2) * (q0 ** 2) / (M_X ** 2)
    else:
        classII_contrib = 0.0

    # Longitudinal stiffness: lambda_parallel = |lambda| * I3 / 2; I3 = 1/3 locked
    I3 = float(params.get("I3_convention", 1.0 / 3.0))
    lambda_parallel = abs(lam) * I3 / 2.0

    if lambda_parallel > 0.0 and M_sq_bare == M_sq_bare:
        mstar2_theory = (M_sq_bare + classII_contrib) / lambda_parallel
    else:
        mstar2_theory = _nan

    # Extractor-convention factor for the legacy 8-patch layout
    # (2 polar + 6 equatorial):
    #   <|G.n|^2>_8 = (2*1 + 6*0.5)/8 = 5/8
    #   R_patch = (N_c / W_0) * (<|G.n|^2>_8 / I_3) = (12/8)*(5/8)/(1/3) = 45/16
    R_patch = 45.0 / 16.0

    return {
        "phi0_sq":                phi0_sq,
        "phi0":                   phi0,
        "M_sq_bare":              M_sq_bare,
        "classII_contrib":        classII_contrib,
        "lambda_parallel":        lambda_parallel,
        "I3_convention":          I3,
        "K4_constellation":       K4,
        "K6_constellation":       K6,
        "R_patch_8to12":          R_patch,
        "mstar2_theory_analytic": mstar2_theory,
        "theory_tag":             "Math37-AddA-2026-04-15",
        "status":                 "ok",
    }


# ============================================================
# Optional harmonic fast-sector extraction
# ============================================================

def maybe_extract_frozen_harmonics_pt(
    input_dir: Path,
    output_dir: Path,
    backend: Any,
    params: Dict[str, Any],
    Psi_corr_t: torch.Tensor,
    delta_corr: np.ndarray,
) -> None:
    G_list = load_npy_optional(input_dir, "G_list.npy")
    if G_list is None:
        print("[info] G_list.npy not found; skipping frozen harmonic extraction.")
        return

    barA_G = extract_shell_harmonics_t(Psi_corr_t, G_list, backend, params)
    orbit_t = load_orbit_fields_or_reconstruct_t(
        input_dir=input_dir,
        backend=backend,
        params=params,
        Psi_corr_t=Psi_corr_t,
        delta_corr=delta_corr,
    )
    orbit_harmonics = {
        lab: extract_shell_harmonics_t(orbit_t[lab], G_list, backend, params)
        for lab in ["A", "E", "O"]
    }

    G_keys = np.array(list(barA_G.keys()), dtype=float)
    barA_vals = np.stack([barA_G[tuple(k)] for k in G_keys], axis=0)
    BA_vals = np.stack([orbit_harmonics["A"][tuple(k)] for k in G_keys], axis=0)
    BE_vals = np.stack([orbit_harmonics["E"][tuple(k)] for k in G_keys], axis=0)
    BO_vals = np.stack([orbit_harmonics["O"][tuple(k)] for k in G_keys], axis=0)

    np.savez(
        output_dir / "frozen_harmonics_pt.npz",
        G_list=G_keys,
        barA_G=barA_vals,
        B_G_A=BA_vals,
        B_G_E=BE_vals,
        B_G_O=BO_vals,
    )
    print(f"[info] Saved frozen harmonics to: {output_dir / 'frozen_harmonics_pt.npz'}")

    if hasattr(backend, "compute_fast_sector_from_harmonics"):
        fast = backend.compute_fast_sector_from_harmonics(barA_G, orbit_harmonics, params)
        np.save(output_dir / "fast_sector_pt.npy", fast, allow_pickle=True)
        print(f"[info] Saved fast-sector data to: {output_dir / 'fast_sector_pt.npy'}")
    else:
        print("[info] backend.compute_fast_sector_from_harmonics not provided; skipped.")


# ============================================================
# Main extractor
# ============================================================

def full_actual_branch_extractor_pt(
    input_dir: Path,
    output_dir: Path,
    backend: Any,
    params: Dict[str, Any],
    run_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    provenance = summarize_provenance(run_metadata)

    Psi_corr = load_npy_required(input_dir, "Psi_corr.npy")
    hat_n = load_npy_required(input_dir, "hat_n.npy").astype(float)
    patch_centers = load_npy_required(input_dir, "patch_centers.npy").astype(float)
    Pi_fam_matrix = load_npy_optional(input_dir, "Pi_fam_matrix.npy")

    if Psi_corr.ndim != 4 or Psi_corr.shape[0] != 3:
        raise ValueError("Psi_corr.npy must have shape (3, Nx, Ny, Nz).")
    if hat_n.shape != (3,):
        raise ValueError("hat_n.npy must have shape (3,).")
    if patch_centers.ndim != 2 or patch_centers.shape[1] != 3:
        raise ValueError("patch_centers.npy must have shape (Npatch, 3).")

    hat_n = normalize_vector(hat_n)
    params["hat_n"] = hat_n.tolist()

    Psi_corr_t = to_torch(Psi_corr, backend, params, complex_required=True)
    device = get_device(backend, params)
    print(f"[info] extractor device: {device}")
    if provenance.get("metadata_present", False):
        print(f"[info] source laplacian_mode: {provenance.get('laplacian_mode')}")
        print(f"[info] source init_mode     : {provenance.get('init_mode')}")
        print(f"[info] emergence_claim_safe: {provenance.get('emergence_claim_safe')}")
        if provenance.get("warning"):
            print(f"[warning] {provenance['warning']}")
    else:
        print(f"[warning] {provenance.get('warning')}")

    q0 = float(params["q0"])
    dq_patch = float(params.get("dq_patch", 0.08 * q0))
    dtheta_patch = float(params.get("dtheta_patch", 0.35))
    delta_corr = np.asarray(params.get("delta_corr", [0.0096, -0.0288, 0.0096]), dtype=float)

    apply_family_projector_t = make_family_projector_t(backend, params, Pi_fam_matrix)
    hessian_vec_t = make_hessian_vec_t(backend, params)

    maybe_extract_frozen_harmonics_pt(
        input_dir=input_dir,
        output_dir=output_dir,
        backend=backend,
        params=params,
        Psi_corr_t=Psi_corr_t,
        delta_corr=delta_corr,
    )

    N_list: List[float] = []
    m2_list: List[float] = []
    g_list: List[float] = []

    for ia, hk in enumerate(patch_centers):
        hk = normalize_vector(np.asarray(hk, dtype=float))
        mask_t = patch_mask_t(
            Psi_t=Psi_corr_t,
            q0=q0,
            hat_k_alpha=hk,
            dq=dq_patch,
            dtheta=dtheta_patch,
            backend=backend,
            params=params,
        )

        chi_alpha_t, m2, Nalpha = extract_patch_mode_t(
            Psi_corr_t=Psi_corr_t,
            patch_mask_alpha_t=mask_t,
            apply_family_projector_t=apply_family_projector_t,
            hessian_vec_t=hessian_vec_t,
            backend=backend,
            params=params,
        )
        galpha = extract_galpha_from_energy_t(
            Psi_corr_t=Psi_corr_t,
            chi_alpha_t=chi_alpha_t,
            backend=backend,
            params=params,
        )

        N_list.append(Nalpha)
        m2_list.append(m2)
        g_list.append(galpha)

        print(
            f"[patch {ia:03d}] "
            f"N_alpha={Nalpha:.10e}, "
            f"m_alpha^2={m2:.10e}, "
            f"g_alpha={galpha:.10e}"
        )

    N_alpha = np.asarray(N_list, dtype=np.float64)
    m_alpha2 = np.asarray(m2_list, dtype=np.float64)
    g_alpha = np.asarray(g_list, dtype=np.float64)

    W0, W2, M2, G4 = compute_raw_moments(
        hat_n=hat_n,
        patch_centers=patch_centers,
        N_alpha=N_alpha,
        m_alpha2=m_alpha2,
        g_alpha=g_alpha,
    )
    obs = compute_effective_observables(W0=W0, W2=W2, M2=M2, G4=G4)

    # phase_status is a string — keep in Python dict but exclude from .npz
    phase_status: str = obs.pop("phase_status")

    # Math37-Step5 analytical companion (diagnostic only; see
    # TECT-Theory-Code-Sync.md for discrepancies D1–D4).
    theory_obs = compute_theory_mstar2(params)

    # results dict: raw arrays + moments + derived observables (NaN-valued if tachyonic)
    results = {
        "N_alpha":     N_alpha,
        "m_alpha2":    m_alpha2,
        "g_alpha":     g_alpha,
        "W0":          W0,
        "W2":          W2,
        "M2":          M2,
        "G4":          G4,
        **obs,
        "phase_status": phase_status,  # re-add as string for callers
        "theory":       theory_obs,    # Math37 Step 5 analytical prediction
    }

    # .npz: numeric arrays only (phase_status is a string; store in JSON instead)
    np.savez(
        output_dir / "actual_branch_results_pt.npz",
        N_alpha   = N_alpha,
        m_alpha2  = m_alpha2,
        g_alpha   = g_alpha,
        W0        = np.float64(W0),
        W2        = np.float64(W2),
        M2        = np.float64(M2),
        G4        = np.float64(G4),
        mstar2    = np.float64(obs["mstar2"]),
        mstar     = np.float64(obs["mstar"]),
        geff      = np.float64(obs["geff"]),
        eps_lock  = np.float64(obs["eps_lock"]),
        Zcub      = np.float64(obs["Zcub"]),
    )
    print(f"[info] Saved final results to: {output_dir / 'actual_branch_results_pt.npz'}")
    if phase_status != "condensed":
        print(f"[warn] phase_status = '{phase_status}'  (M2={M2:.6e} ≤ 0; "
              "mstar/mstar2/Zcub set to NaN in .npz)")

    # JSON helper: convert float NaN → null (NaN is not valid JSON)
    def _js(v: float):
        return None if (isinstance(v, float) and math.isnan(v)) else float(v)

    # Analytical↔numerical mismatch ratio (logged for audit; NOT a pass/fail).
    num = obs.get("mstar2", float("nan"))
    an  = theory_obs.get("mstar2_theory_analytic", float("nan"))
    R   = theory_obs.get("R_patch_8to12", float("nan"))
    if isinstance(num, float) and isinstance(an, float) and num == num and an == an and num > 0:
        ratio_raw = an / num
    else:
        ratio_raw = float("nan")
    if (isinstance(num, float) and isinstance(an, float) and isinstance(R, float)
            and num == num and an == an and R == R and num > 0 and R > 0):
        mstar2_num_corr = R * num
        ratio_corr = an / mstar2_num_corr
    else:
        mstar2_num_corr = float("nan")
        ratio_corr = float("nan")

    extraction_metadata = {
        "generator": "tect_actual_extractor_pt_v3.py",
        "theory_tag": "Math37-AddA-2026-04-15",
        "input_dir": str(input_dir),
        "backend_module": str(getattr(backend, "__file__", "<dynamic>")),
        "source_run_provenance": provenance,
        "phase_status": phase_status,
        "summary": {
            "W0":       float(W0),
            "W2":       float(W2),
            "M2":       float(M2),
            "G4":       float(G4),
            "mstar2":   _js(obs["mstar2"]),
            "mstar":    _js(obs["mstar"]),
            "geff":     _js(obs["geff"]),
            "eps_lock": _js(obs["eps_lock"]),
            "Zcub":     _js(obs["Zcub"]),
        },
        "theory_prediction": {k: _js(v) if isinstance(v, float) else v
                              for k, v in theory_obs.items()},
        "mstar2_analytic_over_numeric_ratio_raw":  _js(ratio_raw),
        "mstar2_num_corrected_R_patch":            _js(mstar2_num_corr),
        "mstar2_analytic_over_numeric_ratio_corr": _js(ratio_corr),
    }
    with open(output_dir / "extraction_metadata.json", "w", encoding="utf-8") as fh:
        json.dump(extraction_metadata, fh, indent=2)
    print(f"[info] Saved extraction metadata to: {output_dir / 'extraction_metadata.json'}")

    return results


# ============================================================
# CLI
# ============================================================

def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Torch-native TECT actual-branch extractor: Psi_corr -> raw moments -> effective observables"
    )
    p.add_argument("--input", required=True, type=str, help="Input directory containing .npy arrays and config.json")
    p.add_argument("--backend", required=True, type=str, help="Path to real_backend_pt.py / real_backend_pt_v2.py")
    p.add_argument("--output", default=None, type=str, help="Output directory. Default: same as input directory")
    return p


def main() -> None:
    parser = build_argparser()
    args = parser.parse_args()

    input_dir = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve() if args.output else input_dir
    backend_path = Path(args.backend).expanduser().resolve()

    try:
        if not input_dir.exists():
            raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

        params = load_config(input_dir)
        run_metadata = load_metadata_optional(input_dir)
        backend = load_backend_module(backend_path)

        if not hasattr(backend, "residual") and not hasattr(backend, "hessian_vec"):
            raise RuntimeError("Backend must provide at least one of: residual(Psi, params), hessian_vec(Psi, v, params)")
        if not hasattr(backend, "shell_free_energy"):
            raise RuntimeError("Backend must provide shell_free_energy(Psi, params)")

        print("=" * 72)
        print("TECT torch-native actual-branch extractor")
        print("=" * 72)
        print(f"Input directory : {input_dir}")
        print(f"Backend module  : {backend_path}")
        print(f"Output directory: {output_dir}")
        print("-" * 72)

        results = full_actual_branch_extractor_pt(
            input_dir=input_dir,
            output_dir=output_dir,
            backend=backend,
            params=params,
            run_metadata=run_metadata,
        )

        print("-" * 72)
        print("Final effective observables")
        print("-" * 72)
        print(f"W0               = {results['W0']:.16e}")
        print(f"W2               = {results['W2']:.16e}")
        print(f"M2               = {results['M2']:.16e}")
        print(f"G4               = {results['G4']:.16e}")
        print()
        _ps = results.get("phase_status", "condensed")
        print(f"phase_status     = {_ps}")
        if _ps == "tachyonic_or_unstable":
            print(f"m*^2             = NaN  [M2 <= 0: tachyonic / unstable phase]")
            print(f"m*               = NaN")
            print(f"g_eff            = {results['geff']:.16e}")
            print(f"epsilon_lock     = {results['eps_lock']:.16e}")
            print(f"Z_cub            = NaN")
            print()
            print("[WARN] Condensate is in a tachyonic or unstable phase at the")
            print("       current parameter point.  Raw moments (W0,W2,M2,G4) and")
            print("       patchwise m_α² are saved; mstar / Zcub are NaN.")
        else:
            print(f"m*^2             = {results['mstar2']:.16e}")
            print(f"m*               = {results['mstar']:.16e}")
            print(f"g_eff            = {results['geff']:.16e}")
            print(f"epsilon_lock     = {results['eps_lock']:.16e}")
            print(f"Z_cub            = {results['Zcub']:.16e}")
        print("=" * 72)

    except Exception as exc:
        eprint("=" * 72)
        eprint("ERROR: extraction failed")
        eprint("=" * 72)
        eprint(str(exc))
        eprint("-" * 72)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
