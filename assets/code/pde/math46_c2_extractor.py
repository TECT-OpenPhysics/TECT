#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v0.8
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
"""
math46_c2_extractor.py  v0.8  (2026-04-16)
(canonical name; v0.1 WITHDRAWN and deleted; _v2 suffix retired)
====================================================================
TECT Class-II (gravity) finite-audit extractor -- theorem-faithful
Math46c compliance, eighth revision.

v0.8 upgrade vs v0.7 (same day, polish round)
---------------------------------------------
(S) Z_h aggregate: comment said "p^2-weighted regression" but code
    used `np.mean`.  v0.8 implements the stated weighting:
        Z_h_fit = sum(p^2 * Z_h) / sum(p^2)
    over momenta where p^2 > 0 and Z_h is finite.  Momenta with
    p^2 = 0 (constant mode) are excluded from the mask.

v0.7 upgrades vs v0.6 (same day, peer-review round 3; one theorem fix + two fail-safes)
---------------------------------------------------------------------------------------
(A)  Basis-invariant H0 cross-sector mixing.
     v0.6 computed nu_{ss'} = ||H_{ss'}||_F / sqrt(||H_{ss}||_F ||H_{s's'}||_F)
     on the raw sector blocks.  This quantity is invariant only under a
     global probe-basis rescaling; under independent sector-wise
     rescalings (which do NOT change the physical eigenproblem
     H_{ss} v = lambda G_{ss} v) the ratio drifts.  v0.7 replaces it by
     the Gram-whitened diagnostic
         nu_tilde_{ss'} = ||Htilde_{ss'}||_F / sqrt(||Htilde_{ss}||_F ||Htilde_{s's'}||_F),
         Htilde_{ss'}   = G_{ss}^{-1/2} H_{ss'} G_{s's'}^{-1/2},
     which is invariant under independent sector rescalings and is the
     operationally correct H0 falsification quantity (Math46c Addendum
     v0.7 Prop.C2fail-H0).
(B)  load_backend() fail-closed on hessian_vec.
     The importlib-based loader now verifies that the imported module
     exposes the Math46c E5 symbol ``hessian_vec`` and raises
     AttributeError otherwise, eliminating a downstream opaque-error
     failure path.
(C)  CLI default output file renamed from math46_c2_audit_v0_5.json
     to math46_c2_audit_v0_7.json, tracking the module version.

v0.6 upgrades vs v0.5 (same day, peer-review round 2; three hot-fixes)
----------------------------------------------------------------------
(F1) `audit_T2()` singular-TT branch NameError fix.
     The early-return path for an empty TT sector referenced an
     undefined variable `mixing`; replaced by the correct emission
     of `mixing_G`, `mixing_H`, `max_H_mixing`, `pass_H0`.  This was
     an outright execution bug for any run where the TT block is
     rank-deficient.
(F2) S6 docstring / implementation alignment.
     The v0.5 header still referenced an "import-time cross-check"
     that the v0.5 code no longer performs.  The S6 paragraph now
     states explicitly that cross-checks live in the runtime audit
     layer (probe_consistency, P-B), not at module import.
(F3) probe_consistency_mode == probe_mode fail-safe.
     v0.5 silently marked the P-B check as trivially passing when
     the companion mode equalled the main mode, which defeats the
     purpose of an independent cross-check.  v0.6 flips this to an
     explicit failure with a warning record and
     `worst_probe_dev = inf`; operators must now pick genuinely
     distinct companion modes or disable P-B via the CLI flag.

v0.5 upgrades vs v0.4 (same day, peer-review Patch A + Patch B)
---------------------------------------------------------------
(P-A) Cross-sector H mixing audit (new H0 falsification mode).
      v0.4 only reported Gram mixing mu_{ss'} = ||G_{ss'}||_F / ...
      which is a kinematic diagnostic.  The dynamic-contamination
      quantity is
          nu_{ss'} = ||H_{ss'}||_F / sqrt(||H_{ss}||_F ||H_{s's'}||_F).
      v0.5 computes nu_{ss'} via `sector_mixing_H_ratios(H)` and
      emits an explicit `pass_H0 = (max nu <= audit_tol)`.  pass_C2
      now requires pass_H0 in addition to T1/T2/T3a.
(P-B) Fourier <-> spectral probe consistency check.
      The Fourier-periodic tangent of v0.4 is a strong torus
      regularisation of the exact affine generator but is not
      identical to the ramp generator.  v0.5 runs the T2 extractor
      under BOTH probe_mode='fourier' AND probe_mode='spectral' at
      every momentum, and reports
          delta_Z_probe = | Z_h^fourier - Z_h^spectral | / |Z_h^fourier|
      as a regression diagnostic.  `pass_probe_consistency` is
      emitted; pass_C2 requires it.  This is run unconditionally
      except when the user explicitly sets `probe_consistency=False`
      (e.g. when only one mode is available).

Reference: docs/math/TECT-Math46c.tex.txt
  Def. tangent        (affine deformation generator)
  Def. probe-basis    (symmetric-tensor polarisations TT / V / tr / L)
  Def. T1, T2, T3     (audit conditions)
  Prop. C2fail        (G1 / G2 / G3 falsification modes + H0 in v0.4)
  Thm. target         (Z_h = |Z|/2 on the Math40 locked vacuum)

v0.4 upgrades vs v0.3 (2026-04-16, same day)
--------------------------------------------
(S1) Fourier-periodic affine tangent.
     The v0.3 "spectral" probe used v_S(x) = S_{ij} x_j d_i psi, with
     x_j the centred ramp.  On the torus, x_j is not periodic, so the
     v0.3 path is not strictly a boundary-artefact-free periodic-lattice
     probe.  v0.4 replaces this by the Fourier-localised generator

        xi^i_{S, p_0}(x) = (L / 2 pi) * S^i_j * sin(2 pi x_j / L),

        v_{S, p_0}(x) = xi^i_{S, p_0}(x) * d_i psi(x),

     which is strictly periodic on the torus, Fourier-localised at
     |p| = 2 pi / L, and recovers S_{ij} x_j in the long-wavelength
     limit.  Math46c Prop.C2fail (G2) O(N^-2) convergence is now
     literally realised via |p_0|^2 ~ N^-2.

(S2) Default probe_mode = 'fourier'.
     'spectral' (v0.3 ramp) retained as O(N^-2) regression check;
     'trilinear' (v0.2 path) retained as legacy diagnostic only.

(S3) Sector-internal generalised eigenproblem.
     v0.3 applied a single 6x6 G^{-1/2} whitening and read off
     TT / V / tr / L blocks by index slicing.  This mixes sectors
     whenever G has off-diagonal entries.  v0.4 solves the generalised
     Hermitian eigenproblem H_ss v = lambda G_ss v within each
     O_h-irrep block separately, returning sector-faithful spectra.
     Cross-sector Gram coupling mu_{ss'} = ||G_{ss'}||_F /
     sqrt(||G_ss||_F ||G_{s's'}||_F) is reported as an independent
     diagnostic (new H0 falsification mode).

(S4) Polarisation universality (T3a), not species universality.
     v0.3 masked channels of the locked field and called the result
     "species universality."  Component-channel masking is NOT a
     clean Class-I/II/III identification.  v0.4 measures the
     polarisation equivalence within the TT doublet (TT1, TT2) and
     the V doublet (V1, V2) -- a legitimate O_h-isotropy statement
     extractable at the Math46c level.  True species universality
     belongs to the Math47 extractor (J1-J5).

(S5) Pass/fail booleans + signed audit margin.
     run() now reports pass_T1, pass_T2, pass_T3a, pass_C2 together
     with audit_margin = audit_tol - max(relative deviation).  No
     numbers are emitted without an audit verdict.

(S6) Affine sign convention.
     Module constant CONVENTION_AFFINE_SIGN = +1.0 locks the global
     convention psi(x) -> psi((I + eps S) x) (Math46c Def.tangent).
     The trilinear, spectral, and fourier paths are wired consistently.
     Cross-checks are performed in the runtime audit layer
     (probe_consistency, P-B), not at import time.

All other Math46c discipline preserved: actual solver package I/O,
actual backend hessian_vec, no scalar surrogate, no wrong-index
strain lift.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np


# ============================================================
#                 Convention locks
# ============================================================

CONVENTION_AFFINE_SIGN: float = +1.0
"""Global sign convention for the Math46c affine deformation.

Math46c Def.tangent defines v_S(x) := d/d eps psi((I + eps S) x)|_0.
CONVENTION_AFFINE_SIGN = +1.0 corresponds to psi -> psi((I + eps S) x);
any override must be reflected in the theory note.  The trilinear
legacy path and the Fourier / spectral analytic paths all respect
this sign.
"""

assert CONVENTION_AFFINE_SIGN in (+1.0, -1.0), "Affine sign must be +/- 1."


# ============================================================
#                 Data structures
# ============================================================

@dataclass(frozen=True)
class SolverPackage:
    root: Path
    psi_lock: np.ndarray
    config: Dict[str, Any]
    metadata: Dict[str, Any]
    hat_n: Optional[np.ndarray]
    G_list: Optional[np.ndarray]


@dataclass(frozen=True)
class C2AuditConfig:
    package_root: Path
    backend_path: Path
    momenta: Tuple[Tuple[int, int, int], ...]
    fd_eps: float = 1e-5
    projector_tol: float = 1e-10
    probe_mode: str = "fourier"  # v0.4 default; 'spectral' (ramp) and 'trilinear' retained.
    audit_tol: float = 1e-2
    target_Z_h: float = 0.5       # Math46c Thm.target with locked |Z|=1
    probe_consistency: bool = True       # P-B: fourier vs spectral Z_h cross-check
    probe_consistency_mode: str = "spectral"  # the companion mode to compare against


# ============================================================
#                 E1 / backend loading (unchanged)
# ============================================================

def load_solver_package(root: Path) -> SolverPackage:
    root = root.expanduser().resolve()
    psi_lock = np.load(root / "Psi_corr.npy").astype(np.complex128, copy=False)
    config = json.loads((root / "config.json").read_text(encoding="utf-8"))
    metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))

    hat_n = None
    if (root / "hat_n.npy").exists():
        hat_n = np.load(root / "hat_n.npy").astype(np.float64, copy=False)

    G_list = None
    if (root / "G_list.npy").exists():
        G_list = np.load(root / "G_list.npy").astype(np.float64, copy=False)

    if psi_lock.ndim != 4:
        raise ValueError(f"Psi_corr.npy must have ndim=4, got shape={psi_lock.shape}")

    return SolverPackage(
        root=root,
        psi_lock=psi_lock,
        config=config,
        metadata=metadata,
        hat_n=hat_n,
        G_list=G_list,
    )


def load_backend(path: Path):
    """v0.7 Patch B -- fail-closed backend loader.

    Imports the backend module from ``path`` and verifies that the required
    ``hessian_vec`` symbol is present before returning.  Previously any
    import-only check deferred the failure to the first matvec call with
    an opaque AttributeError; the extractor now raises immediately.
    """
    path = path.expanduser().resolve()
    spec = importlib.util.spec_from_file_location("tect_backend_actual", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load backend module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tect_backend_actual"] = mod
    spec.loader.exec_module(mod)
    if not hasattr(mod, "hessian_vec"):
        raise AttributeError(
            f"Backend {path.name} lacks required symbol 'hessian_vec' "
            f"(Math46c E5 contract)."
        )
    return mod


class ActualBackendAdapter:
    def __init__(self, backend_module, config: Dict[str, Any]):
        self.backend = backend_module
        self.config = dict(config)

    def residual(self, psi: np.ndarray) -> np.ndarray:
        return np.asarray(self.backend.residual(psi, self.config), dtype=np.complex128)

    def hessian_vec(self, psi: np.ndarray, v: np.ndarray) -> np.ndarray:
        return np.asarray(self.backend.hessian_vec(psi, v, self.config),
                          dtype=np.complex128)


# ============================================================
#                 Primitive helpers
# ============================================================

def inner(a: np.ndarray, b: np.ndarray) -> complex:
    return np.vdot(a.ravel(), b.ravel())


def make_xyz_grid(N: int, L: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.linspace(-L / 2.0, L / 2.0, N, endpoint=False, dtype=np.float64)
    return np.meshgrid(x, x, x, indexing="ij")


def normalize(v: np.ndarray, eps: float = 1e-14) -> np.ndarray:
    n = np.linalg.norm(v)
    if n < eps:
        raise ValueError("Cannot normalize near-zero vector.")
    return v / n


def spectral_grad(psi: np.ndarray, L: float) -> np.ndarray:
    if psi.ndim != 4:
        raise ValueError(f"psi must have shape (C,N,N,N), got {psi.shape}")
    k = np.fft.fftfreq(psi.shape[1], d=L / psi.shape[1]) * (2.0 * np.pi)
    KX, KY, KZ = np.meshgrid(k, k, k, indexing="ij")
    psi_k = np.fft.fftn(psi, axes=(1, 2, 3))
    out = []
    for K in (KX, KY, KZ):
        out.append(np.fft.ifftn(1j * K[None, ...] * psi_k, axes=(1, 2, 3)))
    return np.stack(out, axis=0)


def bloch_modulate(field: np.ndarray, pvec: Tuple[int, int, int], L: float) -> np.ndarray:
    _, N, _, _ = field.shape
    X, Y, Z = make_xyz_grid(N, L)
    dk = 2.0 * np.pi / L
    p = dk * np.asarray(pvec, dtype=np.float64)
    phase = np.exp(1j * (p[0] * X + p[1] * Y + p[2] * Z))
    return field * phase[None, ...]


def fft_bin_to_pvec(pvec: Tuple[int, int, int], L: float) -> np.ndarray:
    dk = 2.0 * np.pi / L
    return dk * np.asarray(pvec, dtype=np.float64)


def orthonormal_triad_from_p(p: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    phat = normalize(np.asarray(p, dtype=np.float64))
    trial = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    if abs(np.dot(trial, phat)) > 0.8:
        trial = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    e1 = normalize(trial - np.dot(trial, phat) * phat)
    e2 = normalize(np.cross(phat, e1))
    return phat, e1, e2


def symmetric_tensor_basis(p: np.ndarray) -> Dict[str, np.ndarray]:
    """Math46c Def.probe-basis: six symmetric 3x3 polarisation tensors.

    Organised by O_h-irrep sectors (TT / V / tr / L); returned in the
    canonical probe order TT1, TT2, V1, V2, tr, L.  The TT and V
    sectors are 2-dimensional; tr and L are 1-dimensional.
    """
    phat, e1, e2 = orthonormal_triad_from_p(p)
    I = np.eye(3, dtype=np.float64)
    return {
        "TT1": (np.outer(e1, e1) - np.outer(e2, e2)) / np.sqrt(2.0),
        "TT2": (np.outer(e1, e2) + np.outer(e2, e1)) / np.sqrt(2.0),
        "V1":  (np.outer(phat, e1) + np.outer(e1, phat)) / np.sqrt(2.0),
        "V2":  (np.outer(phat, e2) + np.outer(e2, phat)) / np.sqrt(2.0),
        "tr":  I / np.sqrt(3.0),
        "L":   np.sqrt(3.0 / 2.0) * (np.outer(phat, phat) - I / 3.0),
    }


# Irrep partition of the canonical probe order (v0.4 S3).
PROBE_ORDER: Tuple[str, ...] = ("TT1", "TT2", "V1", "V2", "tr", "L")
SECTOR_BLOCKS: Dict[str, Tuple[int, ...]] = {
    "TT": (0, 1),
    "V":  (2, 3),
    "tr": (4,),
    "L":  (5,),
}


# ============================================================
#     Trilinear resample (legacy v0.2) -- retained for regression
# ============================================================

def _periodic_linear_sample_scalar(f: np.ndarray, x_idx: np.ndarray, y_idx: np.ndarray, z_idx: np.ndarray) -> np.ndarray:
    N = f.shape[0]
    x0 = np.floor(x_idx).astype(np.int64) % N
    y0 = np.floor(y_idx).astype(np.int64) % N
    z0 = np.floor(z_idx).astype(np.int64) % N
    x1 = (x0 + 1) % N
    y1 = (y0 + 1) % N
    z1 = (z0 + 1) % N
    tx = x_idx - np.floor(x_idx)
    ty = y_idx - np.floor(y_idx)
    tz = z_idx - np.floor(z_idx)

    c000 = f[x0, y0, z0]; c001 = f[x0, y0, z1]
    c010 = f[x0, y1, z0]; c011 = f[x0, y1, z1]
    c100 = f[x1, y0, z0]; c101 = f[x1, y0, z1]
    c110 = f[x1, y1, z0]; c111 = f[x1, y1, z1]
    c00 = c000 * (1 - tx) + c100 * tx
    c01 = c001 * (1 - tx) + c101 * tx
    c10 = c010 * (1 - tx) + c110 * tx
    c11 = c011 * (1 - tx) + c111 * tx
    c0 = c00 * (1 - ty) + c10 * ty
    c1 = c01 * (1 - ty) + c11 * ty
    return c0 * (1 - tz) + c1 * tz


def resample_affine(psi: np.ndarray, A: np.ndarray, L: float) -> np.ndarray:
    _, N, _, _ = psi.shape
    X, Y, Z = make_xyz_grid(N, L)
    Xp = A[0, 0] * X + A[0, 1] * Y + A[0, 2] * Z
    Yp = A[1, 0] * X + A[1, 1] * Y + A[1, 2] * Z
    Zp = A[2, 0] * X + A[2, 1] * Y + A[2, 2] * Z
    dx = L / N
    x_idx = (Xp + L / 2.0) / dx
    y_idx = (Yp + L / 2.0) / dx
    z_idx = (Zp + L / 2.0) / dx
    out = np.empty_like(psi)
    for c in range(psi.shape[0]):
        out[c] = _periodic_linear_sample_scalar(psi[c], x_idx, y_idx, z_idx)
    return out


def affine_deformation_tangent_trilinear(psi_lock: np.ndarray, S: np.ndarray,
                                         L: float, eps: float = 1e-5) -> np.ndarray:
    """Legacy v0.2 path: symmetric FD of trilinearly-resampled fields.

    Carries O(dx) interpolation error plus an O(1) torus-wrap boundary
    artefact; fails Math46c Prop.C2fail (G2) O(N^-2) in general.
    Retained for regression diagnostics ONLY.  Sign convention:
    CONVENTION_AFFINE_SIGN * eps S in the + direction.
    """
    eps_eff = CONVENTION_AFFINE_SIGN * eps
    I = np.eye(3, dtype=np.float64)
    psi_p = resample_affine(psi_lock, I + eps_eff * S, L)
    psi_m = resample_affine(psi_lock, I - eps_eff * S, L)
    return (psi_p - psi_m) / (2.0 * eps)


# ============================================================
#     Spectral ramp tangent (v0.3, retained as O(N^-2) diagnostic)
# ============================================================

def affine_deformation_tangent_spectral(psi_lock: np.ndarray, S: np.ndarray,
                                        L: float) -> np.ndarray:
    """v0.3 path: v_S(x) = S_{ij} x_j d_i psi with ramp x_j.

    Machine-precision at the grid points but x_j is NOT strictly
    periodic.  In v0.4 this is demoted to an O(N^-2) regression
    diagnostic; not the canonical probe.
    """
    if psi_lock.ndim != 4:
        raise ValueError(f"psi_lock must have shape (C,N,N,N), got {psi_lock.shape}")
    _, N, _, _ = psi_lock.shape
    X, Y, Z = make_xyz_grid(N, L)
    coords = np.stack([X, Y, Z], axis=0)  # (3,N,N,N)
    grad_psi = spectral_grad(psi_lock, L)  # (3, C, N, N, N)
    Sx = np.tensordot(S, coords, axes=([1], [0]))  # S_{ij} x_j
    v = np.einsum("ixyz,icxyz->cxyz", Sx, grad_psi)
    return (CONVENTION_AFFINE_SIGN * v).astype(np.complex128, copy=False)


# ============================================================
#     Fourier-periodic tangent (v0.4 canonical, S1)
# ============================================================

def affine_deformation_tangent_fourier(psi_lock: np.ndarray, S: np.ndarray,
                                       L: float) -> np.ndarray:
    """Math46c Def.tangent realised via the Fourier-localised generator.

    xi^i_{S, p_0}(x) = (L / 2 pi) * S^i_j * sin(2 pi x_j / L),
    v_{S, p_0}(x)    = xi^i_{S, p_0}(x) * d_i psi(x).

    xi is strictly periodic on T^3 (sin is periodic), Fourier-localised
    at the two lowest lattice momenta +/- 2 pi / L per Cartesian axis,
    and recovers S_{ij} x_j in the long-wavelength limit (small
    2 pi x_j / L).  The C2 coefficient read at this |p_0| satisfies
        Z_h(p_0) = Z_h^cont + alpha * p_0^2 + O(p_0^4),
    i.e.\\ Math46c (G2) O(N^-2) via |p_0|^2 ~ N^-2 at fixed physical L.
    """
    if psi_lock.ndim != 4:
        raise ValueError(f"psi_lock must have shape (C,N,N,N), got {psi_lock.shape}")
    _, N, _, _ = psi_lock.shape
    X, Y, Z = make_xyz_grid(N, L)
    coords = np.stack([X, Y, Z], axis=0)  # (3, N, N, N)
    k0 = 2.0 * np.pi / L
    amp = L / (2.0 * np.pi)
    xi_scalar = amp * np.sin(k0 * coords)        # (3, N, N, N)  -- xi[j]
    grad_psi = spectral_grad(psi_lock, L)        # (3, C, N, N, N) -- partial_i psi
    xi_i = np.tensordot(S, xi_scalar, axes=([1], [0]))  # S_{ij} xi_scalar[j]
    v = np.einsum("ixyz,icxyz->cxyz", xi_i, grad_psi)
    return (CONVENTION_AFFINE_SIGN * v).astype(np.complex128, copy=False)


def affine_deformation_tangent(
    psi_lock: np.ndarray,
    S: np.ndarray,
    L: float,
    eps: float = 1e-5,
    mode: str = "fourier",
) -> np.ndarray:
    if mode == "fourier":
        return affine_deformation_tangent_fourier(psi_lock, S, L)
    elif mode == "spectral":
        return affine_deformation_tangent_spectral(psi_lock, S, L)
    elif mode == "trilinear":
        return affine_deformation_tangent_trilinear(psi_lock, S, L, eps=eps)
    else:
        raise ValueError(
            f"Unknown probe_mode {mode!r}; expected 'fourier' (v0.4 default), "
            "'spectral' (v0.3 ramp, O(N^-2) diagnostic), or 'trilinear' (v0.2 legacy)."
        )


# ============================================================
#     Projected Hessian + sector-internal eigenproblems (S3)
# ============================================================

def projected_hessian(psi_lock: np.ndarray, probes: List[np.ndarray],
                      backend: ActualBackendAdapter) -> Tuple[np.ndarray, np.ndarray]:
    m = len(probes)
    G = np.zeros((m, m), dtype=np.complex128)
    H = np.zeros((m, m), dtype=np.complex128)
    Hprobes = [backend.hessian_vec(psi_lock, q) for q in probes]
    for i in range(m):
        for j in range(m):
            G[i, j] = inner(probes[i], probes[j])
            H[i, j] = inner(probes[i], Hprobes[j])
    return G, H


def _hermitianise(M: np.ndarray) -> np.ndarray:
    return 0.5 * (M + M.conj().T)


def _block(M: np.ndarray, rows: Tuple[int, ...], cols: Tuple[int, ...]) -> np.ndarray:
    return M[np.ix_(rows, cols)]


def sector_generalised_eigs(
    G: np.ndarray,
    H: np.ndarray,
    tol: float = 1e-12,
) -> Dict[str, Dict[str, Any]]:
    """Solve H_ss v = lambda G_ss v within each O_h-irrep sector.

    Returns a dict {sector_name: {evals, G_block, H_block}}.  No full
    6x6 whitening is performed; each sector is treated independently so
    that index slicing cannot leak cross-sector coupling into the
    reported spectrum.
    """
    Gh = _hermitianise(G)
    Hh = _hermitianise(H)
    out: Dict[str, Dict[str, Any]] = {}
    for s, idx in SECTOR_BLOCKS.items():
        G_ss = _block(Gh, idx, idx)
        H_ss = _block(Hh, idx, idx)
        G_ss = _hermitianise(G_ss)
        H_ss = _hermitianise(H_ss)
        # Generalised eigenproblem: need G_ss^{-1/2} H_ss G_ss^{-1/2}.
        ew, U = np.linalg.eigh(G_ss)
        keep = ew > tol * max(1.0, float(ew.max().real))
        if not np.any(keep):
            out[s] = {"evals": np.array([]), "G_block": G_ss, "H_block": H_ss,
                      "dim": 0, "singular": True}
            continue
        ew_keep = ew[keep]
        U_keep = U[:, keep]
        Gm12 = U_keep @ np.diag(ew_keep ** (-0.5)) @ U_keep.conj().T
        H_std = Gm12 @ H_ss @ Gm12
        evals = np.linalg.eigvalsh(_hermitianise(H_std))
        out[s] = {"evals": evals, "G_block": G_ss, "H_block": H_ss,
                  "dim": int(evals.size), "singular": False}
    return out


def _mixing_ratios(M: np.ndarray) -> Dict[Tuple[str, str], float]:
    """Common kernel:  ratio_{ss'} = ||M_{ss'}||_F / sqrt(||M_ss||_F ||M_{s's'}||_F)."""
    Mh = _hermitianise(M)
    names = list(SECTOR_BLOCKS.keys())
    ratios: Dict[Tuple[str, str], float] = {}
    norms: Dict[str, float] = {}
    for s, idx in SECTOR_BLOCKS.items():
        norms[s] = float(np.linalg.norm(_block(Mh, idx, idx)))
    for i, s in enumerate(names):
        for s_ in names[i + 1:]:
            idx_s = SECTOR_BLOCKS[s]
            idx_sp = SECTOR_BLOCKS[s_]
            num = float(np.linalg.norm(_block(Mh, idx_s, idx_sp)))
            den = math.sqrt(max(norms[s] * norms[s_], 1e-60))
            ratios[(s, s_)] = num / den if den > 0 else float("inf")
    return ratios


def sector_mixing_ratios(G: np.ndarray) -> Dict[Tuple[str, str], float]:
    """Gram mixing: mu_{ss'} = ||G_{ss'}||_F / sqrt(||G_ss||_F ||G_{s's'}||_F).

    Kinematic diagnostic for the probe basis itself; bounded in [0, 1].
    """
    return _mixing_ratios(G)


def _inv_sqrt_block(G_block: np.ndarray, tol: float = 1e-12) -> np.ndarray | None:
    """Pseudo-inverse square root of a Hermitian positive-semidefinite block.

    Returns None if the block has no eigenvalues above the relative tolerance
    (i.e. the sector Gram block is effectively singular, in which case the
    caller must treat the sector as unresolved).
    """
    G_block = _hermitianise(G_block)
    ew, U = np.linalg.eigh(G_block)
    keep = ew > tol * max(1.0, float(np.real(ew.max())))
    if not np.any(keep):
        return None
    ew_keep = ew[keep]
    U_keep = U[:, keep]
    return U_keep @ np.diag(ew_keep ** (-0.5)) @ U_keep.conj().T


def sector_mixing_H_ratios(
    G: np.ndarray,
    H: np.ndarray,
    tol: float = 1e-12,
) -> Dict[Tuple[str, str], float]:
    """v0.7 Patch A -- basis-invariant H0 falsification mode.

    Gram-whitened cross-sector mixing.  Let
        \tilde H_{ss'} := G_{ss}^{-1/2} H_{ss'} G_{s's'}^{-1/2},
    defined on the generalised-eigenbasis of the same decomposition used
    in `sector_generalised_eigs`.  The returned diagnostic is
        \nu_{ss'} = || \tilde H_{ss'} ||_F
                   / sqrt( || \tilde H_{ss} ||_F * || \tilde H_{s's'} ||_F ),
    which is invariant under independent rescalings of the probe basis in
    each sector (Prop.C2fail-H0, Math46c Addendum v0.7) -- the raw v0.5
    formula \|H_{ss'}\|_F / sqrt(\|H_{ss}\|_F \|H_{s's'}\|_F) was only
    basis-invariant under global probe-basis rescaling.
    """
    Gh = _hermitianise(G)
    Hh = _hermitianise(H)

    Gm12: Dict[str, np.ndarray | None] = {}
    Hdiag_norm: Dict[str, float] = {}

    for s, idx in SECTOR_BLOCKS.items():
        G_ss = _block(Gh, idx, idx)
        H_ss = _block(Hh, idx, idx)
        Gm12_s = _inv_sqrt_block(G_ss, tol=tol)
        Gm12[s] = Gm12_s
        if Gm12_s is None:
            Hdiag_norm[s] = 0.0
            continue
        Htilde_ss = Gm12_s @ H_ss @ Gm12_s
        Hdiag_norm[s] = float(np.linalg.norm(Htilde_ss))

    names = list(SECTOR_BLOCKS.keys())
    ratios: Dict[Tuple[str, str], float] = {}

    for i, s in enumerate(names):
        for s_ in names[i + 1:]:
            if Gm12[s] is None or Gm12[s_] is None:
                ratios[(s, s_)] = float("inf")
                continue

            idx_s = SECTOR_BLOCKS[s]
            idx_sp = SECTOR_BLOCKS[s_]
            H_ssp = _block(Hh, idx_s, idx_sp)

            Htilde_ssp = Gm12[s] @ H_ssp @ Gm12[s_]
            num = float(np.linalg.norm(Htilde_ssp))
            den = math.sqrt(max(Hdiag_norm[s] * Hdiag_norm[s_], 1e-60))
            ratios[(s, s_)] = num / den if den > 0 else float("inf")

    return ratios


# ============================================================
#                 Extractor class
# ============================================================

class C2ExtractorV2:
    def __init__(self, pkg: SolverPackage, backend: ActualBackendAdapter,
                 cfg: C2AuditConfig):
        self.pkg = pkg
        self.backend = backend
        self.cfg = cfg
        self.psi_lock = np.asarray(pkg.psi_lock, dtype=np.complex128)
        if self.psi_lock.shape[0] != 3:
            raise ValueError(
                f"Expected locked field shape (3,N,N,N), got {self.psi_lock.shape}"
            )
        self.N = self.psi_lock.shape[1]
        self.L = float(pkg.config.get("Lx", pkg.config.get("L", 16.0)))
        self.translation_tangents = spectral_grad(self.psi_lock, self.L)

    # --- displacement (T1) probes ---
    def displacement_probes(self, pvec: Tuple[int, int, int]) -> List[np.ndarray]:
        return [bloch_modulate(self.translation_tangents[i], pvec, self.L)
                for i in range(3)]

    # --- tensor probe basis (T2 / T3a) ---
    def tensor_probe_basis(self, pvec: Tuple[int, int, int]) -> Dict[str, np.ndarray]:
        p = fft_bin_to_pvec(pvec, self.L)
        basis = symmetric_tensor_basis(p)
        out: Dict[str, np.ndarray] = {}
        for name, S in basis.items():
            Q = affine_deformation_tangent(
                self.psi_lock, S=S, L=self.L, eps=self.cfg.fd_eps,
                mode=self.cfg.probe_mode,
            )
            out[name] = bloch_modulate(Q, pvec, self.L)
        return out

    # --- T1 (translation-isotropy) ---
    def audit_T1(self, pvec: Tuple[int, int, int]) -> Dict[str, Any]:
        probes = self.displacement_probes(pvec)
        G, H = projected_hessian(self.psi_lock, probes, self.backend)
        Gh = _hermitianise(G)
        Hh = _hermitianise(H)
        ew, U = np.linalg.eigh(Gh)
        keep = ew > self.cfg.projector_tol * max(1.0, float(ew.max().real))
        Gm12 = U[:, keep] @ np.diag(ew[keep] ** (-0.5)) @ U[:, keep].conj().T
        H_std = Gm12 @ Hh @ Gm12
        evals = np.linalg.eigvalsh(_hermitianise(H_std)).real
        if evals.size == 0:
            return {"pass": False, "evals": [], "iso_dev": float("inf")}
        mean = float(np.mean(evals))
        iso_dev = float(np.max(np.abs(evals - mean)) / max(abs(mean), 1e-30))
        return {
            "evals": evals.tolist(),
            "mean": mean,
            "iso_dev": iso_dev,
            "pass": bool(iso_dev <= self.cfg.audit_tol),
        }

    # --- T2 (TT-principal + Z_h target) ---
    def audit_T2(self, pvec: Tuple[int, int, int]) -> Dict[str, Any]:
        p = fft_bin_to_pvec(pvec, self.L)
        p2 = float(np.dot(p, p))
        probes_dict = self.tensor_probe_basis(pvec)
        probes = [probes_dict[k] for k in PROBE_ORDER]
        G, H = projected_hessian(self.psi_lock, probes, self.backend)
        sector = sector_generalised_eigs(G, H, tol=self.cfg.projector_tol)
        mixing_G = sector_mixing_ratios(G)
        mixing_H = sector_mixing_H_ratios(G, H, tol=self.cfg.projector_tol)
        max_nu = max(mixing_H.values()) if mixing_H else 0.0
        pass_H0 = bool(max_nu <= self.cfg.audit_tol)

        # TT is the graviton sector.
        tt_evals = np.asarray(sector["TT"]["evals"], dtype=np.float64).real
        if tt_evals.size == 0:
            return {
                "pass": False,
                "reason": "TT sector singular",
                "sectors": sector,
                "mixing_G": {f"{a}-{b}": v for (a, b), v in mixing_G.items()},
                "mixing_H": {f"{a}-{b}": v for (a, b), v in mixing_H.items()},
                "max_H_mixing": max_nu,
                "pass_H0": pass_H0,
            }
        tt_min = float(np.min(tt_evals))
        Z_h = float(tt_min / max(p2, 1e-30))
        dev_Z = abs(Z_h - self.cfg.target_Z_h) / max(abs(self.cfg.target_Z_h), 1e-30)

        # TT must be the most-bound (smallest) sector among {TT, V, tr, L}.
        sector_mins: Dict[str, float] = {}
        for s in SECTOR_BLOCKS:
            ev = np.asarray(sector[s]["evals"], dtype=np.float64).real
            sector_mins[s] = float(np.min(ev)) if ev.size else float("inf")
        tt_is_principal = bool(tt_min <= min(
            sector_mins[s] for s in ("V", "tr", "L")
        ))

        return {
            "p2": p2,
            "Z_h": Z_h,
            "target_Z_h": self.cfg.target_Z_h,
            "dev_Z": dev_Z,
            "tt_evals": tt_evals.tolist(),
            "sector_mins": sector_mins,
            "tt_is_principal": tt_is_principal,
            "mixing_G": {f"{a}-{b}": v for (a, b), v in mixing_G.items()},
            "mixing_H": {f"{a}-{b}": v for (a, b), v in mixing_H.items()},
            "max_H_mixing": max_nu,
            "pass_H0": pass_H0,
            "pass": bool((dev_Z <= self.cfg.audit_tol)
                         and tt_is_principal and pass_H0),
        }

    # --- T3a (polarisation universality; S4) ---
    def audit_T3a(self, pvec: Tuple[int, int, int]) -> Dict[str, Any]:
        probes_dict = self.tensor_probe_basis(pvec)
        probes = [probes_dict[k] for k in PROBE_ORDER]
        G, H = projected_hessian(self.psi_lock, probes, self.backend)
        sector = sector_generalised_eigs(G, H, tol=self.cfg.projector_tol)
        tt = np.asarray(sector["TT"]["evals"], dtype=np.float64).real
        vv = np.asarray(sector["V"]["evals"], dtype=np.float64).real

        def rel_spread(x: np.ndarray) -> float:
            if x.size < 2:
                return 0.0
            mu = float(np.mean(x))
            return float(np.max(np.abs(x - mu)) / max(abs(mu), 1e-30))

        tt_spread = rel_spread(tt)
        v_spread = rel_spread(vv)
        return {
            "tt_evals": tt.tolist(),
            "v_evals": vv.tolist(),
            "tt_polar_dev": tt_spread,
            "v_polar_dev": v_spread,
            "max_polar_dev": max(tt_spread, v_spread),
            "pass": bool(max(tt_spread, v_spread) <= self.cfg.audit_tol),
        }

    def audit_momentum(self, pvec: Tuple[int, int, int]) -> Dict[str, Any]:
        t1 = self.audit_T1(pvec)
        t2 = self.audit_T2(pvec)
        t3a = self.audit_T3a(pvec)
        return {"pvec": list(pvec), "T1": t1, "T2": t2, "T3a": t3a}

    # --- T2 with an arbitrary probe_mode override (P-B support) ---
    def _audit_T2_with_mode(self, pvec: Tuple[int, int, int],
                            probe_mode_override: str) -> Dict[str, Any]:
        saved = self.cfg.probe_mode
        object.__setattr__(self.cfg, "probe_mode", probe_mode_override)
        try:
            out = self.audit_T2(pvec)
        finally:
            object.__setattr__(self.cfg, "probe_mode", saved)
        return out

    def run(self) -> Dict[str, Any]:
        per_momentum = [self.audit_momentum(pvec) for pvec in self.cfg.momenta]

        # -------- P-B: fourier <-> spectral Z_h cross-check --------
        probe_consistency_report: List[Dict[str, Any]] = []
        pass_probe_consistency = True
        worst_probe_dev = 0.0
        if self.cfg.probe_consistency:
            companion = self.cfg.probe_consistency_mode
            if companion == self.cfg.probe_mode:
                # Fail-safe: trivially equal probe modes do NOT constitute an
                # independent cross-check.  Emit an explicit warning and mark
                # the audit as failed rather than silently passing.
                probe_consistency_report.append({
                    "warning": (
                        "probe_consistency_mode equals probe_mode; "
                        "no independent cross-check performed."
                    ),
                    "probe_mode": self.cfg.probe_mode,
                    "companion_mode": companion,
                })
                pass_probe_consistency = False
                worst_probe_dev = float("inf")
            else:
                for pvec in self.cfg.momenta:
                    t2_alt = self._audit_T2_with_mode(pvec, companion)
                    Z_main = next(m["T2"].get("Z_h", float("nan"))
                                  for m in per_momentum
                                  if tuple(m["pvec"]) == tuple(pvec))
                    Z_alt = t2_alt.get("Z_h", float("nan"))
                    if (np.isfinite(Z_main) and np.isfinite(Z_alt)
                            and abs(Z_main) > 1e-30):
                        dev = abs(Z_main - Z_alt) / abs(Z_main)
                    else:
                        dev = float("inf")
                    probe_consistency_report.append({
                        "pvec": list(pvec),
                        "Z_main": float(Z_main),
                        "Z_companion": float(Z_alt),
                        "delta_Z_probe": float(dev),
                        "companion_mode": companion,
                    })
                    if dev > worst_probe_dev:
                        worst_probe_dev = dev
                pass_probe_consistency = bool(
                    worst_probe_dev <= self.cfg.audit_tol
                )

        # Aggregate: Z_h fit via p^2-weighted mean across momenta.
        # Z_h(p) = lambda_min(p) / p^2 is constant in the continuum limit;
        # weighting by p^2 suppresses contributions from near-zero momenta
        # where lattice discretisation errors are largest.
        p2   = np.array([m["T2"].get("p2",  np.nan) for m in per_momentum], dtype=np.float64)
        Z_hs = np.array([m["T2"].get("Z_h", np.nan) for m in per_momentum], dtype=np.float64)
        good = np.isfinite(p2) & np.isfinite(Z_hs) & (p2 > 0.0)
        if np.any(good):
            w = p2[good]
            Z_h_fit = float(np.sum(w * Z_hs[good]) / np.sum(w))
        else:
            Z_h_fit = float("nan")

        # Pass/fail aggregation (S5 + P-A + P-B).
        pass_T1  = all(m["T1"]["pass"] for m in per_momentum)
        pass_T2  = all(m["T2"]["pass"] for m in per_momentum)
        pass_T3a = all(m["T3a"]["pass"] for m in per_momentum)
        pass_H0  = all(m["T2"].get("pass_H0", False) for m in per_momentum)
        pass_C2  = bool(pass_T1 and pass_T2 and pass_T3a
                        and pass_H0 and pass_probe_consistency)

        worst_iso = max((m["T1"].get("iso_dev", 0.0) or 0.0)
                        for m in per_momentum) if per_momentum else 0.0
        worst_Z = max((m["T2"].get("dev_Z", 0.0) or 0.0)
                      for m in per_momentum) if per_momentum else 0.0
        worst_polar = max((m["T3a"].get("max_polar_dev", 0.0) or 0.0)
                          for m in per_momentum) if per_momentum else 0.0
        worst_nu = max((m["T2"].get("max_H_mixing", 0.0) or 0.0)
                       for m in per_momentum) if per_momentum else 0.0
        worst = max(worst_iso, worst_Z, worst_polar, worst_nu, worst_probe_dev)
        audit_margin = float(self.cfg.audit_tol - worst)

        return {
            "package_root": str(self.pkg.root),
            "backend": str(self.cfg.backend_path),
            "N": self.N,
            "L": self.L,
            "probe_mode": self.cfg.probe_mode,
            "momenta": [list(p) for p in self.cfg.momenta],
            "per_momentum": per_momentum,
            "aggregate": {
                "Z_h_fit": Z_h_fit,
                "target_Z_h": self.cfg.target_Z_h,
                "worst_iso_dev": worst_iso,
                "worst_Z_dev": worst_Z,
                "worst_polar_dev": worst_polar,
                "worst_H_mixing": worst_nu,
                "worst_probe_dev": worst_probe_dev,
            },
            "probe_consistency": {
                "enabled": bool(self.cfg.probe_consistency),
                "companion_mode": self.cfg.probe_consistency_mode,
                "per_momentum": probe_consistency_report,
                "worst_delta_Z": worst_probe_dev,
                "pass_probe_consistency": pass_probe_consistency,
            },
            "audit": {
                "audit_tol": self.cfg.audit_tol,
                "audit_margin": audit_margin,
                "pass_T1":  pass_T1,
                "pass_T2":  pass_T2,
                "pass_T3a": pass_T3a,
                "pass_H0":  pass_H0,
                "pass_probe_consistency": pass_probe_consistency,
                "pass_C2":  pass_C2,
            },
            "compliance": {
                "convention_affine_sign": CONVENTION_AFFINE_SIGN,
                "uses_actual_backend_hessian": True,
                "uses_solver_package": True,
                "uses_direct_tensor_probes": True,
                "sector_internal_generalised_eig": True,
                "fourier_periodic_tangent": self.cfg.probe_mode == "fourier",
                "polarisation_universality_T3a": True,
                "H_mixing_audit_H0": True,                       # P-A
                "probe_consistency_cross_check": bool(self.cfg.probe_consistency),  # P-B
                "passfail_emitted": True,
            },
        }


# ============================================================
#                 CLI
# ============================================================

def parse_momenta(vals: Iterable[str]) -> Tuple[Tuple[int, int, int], ...]:
    out = []
    for s in vals:
        parts = tuple(int(x) for x in s.split(","))
        if len(parts) != 3:
            raise ValueError(f"Invalid momentum triplet: {s}")
        out.append(parts)
    return tuple(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--package-root", required=True)
    ap.add_argument("--backend", required=True)
    ap.add_argument("--momenta", nargs="+", required=True,
                    help="FFT-bin triplets like 1,0,0 1,1,0 2,0,0")
    ap.add_argument("--fd-eps", type=float, default=1e-5,
                    help="FD step for the legacy trilinear probe.")
    ap.add_argument("--projector-tol", type=float, default=1e-10)
    ap.add_argument("--probe-mode",
                    choices=("fourier", "spectral", "trilinear"),
                    default="fourier",
                    help="Affine tangent realisation: fourier (v0.4 default, "
                         "periodic on torus), spectral (v0.3 ramp, non-periodic "
                         "diagnostic), or trilinear (v0.2 legacy).")
    ap.add_argument("--audit-tol", type=float, default=1e-2)
    ap.add_argument("--target-Zh", type=float, default=0.5,
                    help="Math46c Thm.target; |Z|/2 = 0.5 with the locked triple.")
    ap.add_argument("--no-probe-consistency", action="store_true",
                    help="Disable the P-B fourier<->companion Z_h cross-check.")
    ap.add_argument("--probe-consistency-mode",
                    choices=("spectral", "trilinear", "fourier"),
                    default="spectral",
                    help="Companion probe_mode for the P-B consistency check.")
    ap.add_argument("--out", default="math46_c2_audit_v0_7.json")
    args = ap.parse_args()

    pkg = load_solver_package(Path(args.package_root))
    backend_mod = load_backend(Path(args.backend))
    backend = ActualBackendAdapter(backend_mod, pkg.config)

    cfg = C2AuditConfig(
        package_root=Path(args.package_root).expanduser().resolve(),
        backend_path=Path(args.backend).expanduser().resolve(),
        momenta=parse_momenta(args.momenta),
        fd_eps=float(args.fd_eps),
        projector_tol=float(args.projector_tol),
        probe_mode=str(args.probe_mode),
        audit_tol=float(args.audit_tol),
        target_Z_h=float(args.target_Zh),
        probe_consistency=not bool(args.no_probe_consistency),
        probe_consistency_mode=str(args.probe_consistency_mode),
    )

    ext = C2ExtractorV2(pkg, backend, cfg)
    result = ext.run()

    out_path = Path(args.out).expanduser().resolve()
    out_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
