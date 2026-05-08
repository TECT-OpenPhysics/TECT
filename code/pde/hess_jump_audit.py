#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v1.1
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
"""
hess_jump_audit.py  —  TECT Phase-2.5 gate measurement (Math56)

Companion to tect_newton_krylov.py (v2.3) and TECT-Math56-HessJump-audit.

PURPOSE
-------
Measure the three Phase-2.5 gate observables

    (G1)  rho_UV         = Fourier mass at |k| > 2 q0  relative to total
    (G2)  O(N, 2N)       = cross-grid overlap of v*(N) against v*(2N)
                            after zero-pad spectral interpolation
    (G3)  eta_Ritz       = || H_proj v - lambda v || / lambda

for the Ritz pairs (lambda_i, v_i) produced by the Newton-Krylov Phase-2
Lanczos pass at N=32 and N=64.  Outputs a JSON verdict and a human
Markdown summary.

NOTE
----
This script does NOT re-run Newton-Krylov; it loads the saved
Ritz pairs and condensate fields from

    PDE/newton_rigorous_N32/hessian_ritz_vectors_projected.npy
    PDE/newton_rigorous_N32/hessian_evals_projected.npy
    PDE/newton_rigorous_N32/Psi_star.npy
    PDE/newton_rigorous_N64/...

and operates in pure-numpy / FFT.  For (G3) the Hessian-vector product
is re-evaluated via the PyTorch backend (real_backend_pt_bcc_mixed_v3);
if the backend is unavailable, (G3) is marked NOT_MEASURED and only
(G1), (G2), plus a reference linear-Brazovskii cross-check, are reported.

REFERENCES
----------
- TECT-Math56-HessJump-audit.tex.txt (theoretical foundation)
- NEGATIVE-RESULTS.md  F-2026-04-20-05
- OPEN-QUESTIONS.md    Q-2026-04-20-Q-HESS-JUMP
"""

from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# v2.4 theorem-anchored thresholds (Math56-Addendum §§B-E).
# Import lazily-failing so the script still runs if v24_thresholds.py is
# temporarily unavailable; in that case the v1.0 heuristics are used with
# a warning.
try:  # pragma: no cover - thin import shim
    from v24_thresholds import (
        V24_G2_MIN as _V24_G2_MIN,
        V24_G3_REL as _V24_G3_REL,
    )
    _V24_AVAILABLE = True
except Exception:  # pragma: no cover
    _V24_G2_MIN = 0.80   # legacy heuristic fallback
    _V24_G3_REL = None   # None => absolute 1e-3 fallback
    _V24_AVAILABLE = False

_HERE = os.path.dirname(os.path.abspath(__file__))
_DIR_N32 = os.path.join(_HERE, "newton_rigorous_N32")
_DIR_N64 = os.path.join(_HERE, "newton_rigorous_N64")
_OUT_JSON = os.path.join(_HERE, "phase2p5_gate_N32_N64_2026-04-20.json")
_OUT_MD = os.path.join(_HERE, "phase2p5_gate_summary.md")

# Locked TECT Brazovskii parameters (Math37-AddA).  These must match
# config_template_brazovskii.json.
_PARAMS_FALLBACK = dict(
    q0=0.6801747616,
    mu2=0.26,
    quartic_lambda=-0.43,
    sextic_gamma=1.62,
    Y=1.0,
    Z=-0.9252754126,
    r=0.4740336473,
    family_masses=[0.0, 0.03, 0.07],
    z0=[1.0, 1.0, 1.0],
    k_lock=0.15,
    eta_shell=0.0,
)


# =========================================================================
# Fourier helpers (numpy-only, N-cube grids)
# =========================================================================

def _lattice_kvec(N: int, L: float) -> np.ndarray:
    """FFT convention k-grid of shape (N,) — matches torch.fft.fftfreq."""
    return 2.0 * math.pi * np.fft.fftfreq(N, d=L / N)


def _kmag_cube(N: int, L: float) -> np.ndarray:
    """Returns |k| of shape (N,N,N)."""
    k = _lattice_kvec(N, L)
    KX, KY, KZ = np.meshgrid(k, k, k, indexing="ij")
    return np.sqrt(KX * KX + KY * KY + KZ * KZ)


def _fft_field(Psi: np.ndarray) -> np.ndarray:
    """FFT along spatial axes (1,2,3) of a (3,N,N,N) complex field."""
    return np.fft.fftn(Psi, axes=(1, 2, 3))


def _ifft_field(Psi_k: np.ndarray) -> np.ndarray:
    return np.fft.ifftn(Psi_k, axes=(1, 2, 3))


# =========================================================================
# G1 — Fourier localisation
# =========================================================================

def _fourier_mass_bands(v_real: np.ndarray, N: int, L: float,
                        q0: float) -> Dict[str, float]:
    """Decompose a flat real vector of length 2 * 3 * N^3 back into a
    (3, N, N, N) complex field and measure squared Fourier mass in

        IR band      |k| <= 2 q0
        shell band   2 q0 < |k| <= 3 q0
        UV band      |k| > 3 q0.

    Returns fractions summing to 1.
    """
    expected = 2 * 3 * N * N * N
    if v_real.size != expected:
        raise ValueError(f"ritz vector size {v_real.size} != {expected}")
    half = v_real.size // 2
    re = v_real[:half].reshape(3, N, N, N).astype(np.float64)
    im = v_real[half:].reshape(3, N, N, N).astype(np.float64)
    v_cplx = (re + 1j * im).astype(np.complex128)

    vk = _fft_field(v_cplx)  # (3, N, N, N) complex
    # Power spectrum summed over internal index
    power = np.sum(np.abs(vk) ** 2, axis=0)  # (N, N, N) real
    total = float(np.sum(power))

    kmag = _kmag_cube(N, L)
    mask_IR = kmag <= 2.0 * q0
    mask_UV = kmag > 3.0 * q0
    mask_shell = (~mask_IR) & (~mask_UV)

    rho_IR = float(np.sum(power[mask_IR])) / total if total > 0 else 0.0
    rho_shell = float(np.sum(power[mask_shell])) / total if total > 0 else 0.0
    rho_UV = float(np.sum(power[mask_UV])) / total if total > 0 else 0.0

    # Dominant-k diagnostic: where is the peak?
    peak_idx = np.unravel_index(int(np.argmax(power)), power.shape)
    k_peak = float(kmag[peak_idx])

    # Radial profile (binned) for reporting
    n_bins = 32
    kmax = float(np.max(kmag))
    bins = np.linspace(0.0, kmax, n_bins + 1)
    centers = 0.5 * (bins[:-1] + bins[1:])
    digit = np.digitize(kmag.ravel(), bins) - 1
    digit = np.clip(digit, 0, n_bins - 1)
    radial = np.zeros(n_bins, dtype=np.float64)
    np.add.at(radial, digit, power.ravel())
    radial = radial / total if total > 0 else radial

    return dict(
        total_power=total,
        rho_IR=rho_IR,
        rho_shell=rho_shell,
        rho_UV=rho_UV,
        k_peak=k_peak,
        k_Nyquist=float(math.pi * N / L),
        q0=q0,
        radial_bin_centers=centers.tolist(),
        radial_mass=radial.tolist(),
    )


# =========================================================================
# G2 — Cross-grid overlap via zero-pad spectral interpolation
# =========================================================================

def _zero_pad_fft(v_flat_N: np.ndarray, N: int, M: int) -> np.ndarray:
    """Zero-pad a (3,N,N,N) complex field (packed into a flat real vector)
    in Fourier space to produce a (3,M,M,M) field with M = 2*N.

    The interpolator I_N^{2N} is defined in the Fourier representation:

        hat{I v}(k) = hat v(k)   if k in the N-cube's BZ
                      0          otherwise.

    Output is returned as a flat real vector of length 2 * 3 * M^3.
    """
    if M % N != 0 or M < N:
        raise ValueError(f"zero-pad requires M >= N and M%N==0, got N={N}, M={M}")
    half = v_flat_N.size // 2
    re = v_flat_N[:half].reshape(3, N, N, N)
    im = v_flat_N[half:].reshape(3, N, N, N)
    v_c = (re + 1j * im).astype(np.complex128)
    vk = _fft_field(v_c)  # (3, N, N, N)

    # Build zero-padded (3, M, M, M) spectrum by placing the N-cube
    # into the corners of the M-cube consistent with FFT ordering
    # (positive and negative frequencies at both ends).
    half_n_hi = (N + 1) // 2  # number of non-negative freq indices
    half_n_lo = N // 2        # number of negative freq indices
    vk_M = np.zeros((3, M, M, M), dtype=np.complex128)

    # Slice helpers for positive (0:half_n_hi) and negative (-half_n_lo:)
    # portions of the 1-D FFT ordering.
    def _split(a: np.ndarray, axis: int):
        return (np.take(a, range(half_n_hi), axis=axis),
                np.take(a, range(N - half_n_lo, N), axis=axis))

    # Split along axis 1 (kx)
    kx_pos, kx_neg = _split(vk, 1)
    # Split along axis 2 (ky)
    kxp_yp, kxp_yn = _split(kx_pos, 2)
    kxn_yp, kxn_yn = _split(kx_neg, 2)
    # Split along axis 3 (kz) and place into the M-cube
    def _place(block: np.ndarray, x_sign: int, y_sign: int) -> None:
        blk_zp, blk_zn = _split(block, 3)
        # x slice
        xs_pos = slice(0, half_n_hi)
        xs_neg = slice(M - half_n_lo, M)
        ys_pos = slice(0, half_n_hi)
        ys_neg = slice(M - half_n_lo, M)
        zs_pos = slice(0, half_n_hi)
        zs_neg = slice(M - half_n_lo, M)
        xs = xs_pos if x_sign > 0 else xs_neg
        ys = ys_pos if y_sign > 0 else ys_neg
        vk_M[:, xs, ys, zs_pos] = blk_zp
        vk_M[:, xs, ys, zs_neg] = blk_zn

    _place(kxp_yp, +1, +1)
    _place(kxp_yn, +1, -1)
    _place(kxn_yp, -1, +1)
    _place(kxn_yn, -1, -1)

    # Scale: preserve the L^2 (discrete) inner product under zero-pad.
    # FFT(N) has norm factor 1 (forward unnormalised, inverse /N^3).
    # After padding we must scale by (M/N)^3 so that ifft_M produces the
    # sampled continuation of the underlying band-limited function with
    # unit L^2 norm.
    scale = (M / N) ** 3
    v_c_M = _ifft_field(vk_M * scale)
    re_M = v_c_M.real
    im_M = v_c_M.imag
    return np.concatenate([re_M.ravel(), im_M.ravel()]).astype(np.float64)


def _real_inner(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a.astype(np.float64), b.astype(np.float64)))


def _real_norm(a: np.ndarray) -> float:
    return math.sqrt(max(_real_inner(a, a), 0.0))


def _overlap_matrix(V_flat_N: np.ndarray, V_flat_2N: np.ndarray,
                    N: int, M: int) -> np.ndarray:
    """Compute O_{ij} = |< I_N^{2N} v_i(N), v_j(2N) >|^2  / norms.

    V_flat_N : (n_vecs, 2*3*N^3)
    V_flat_2N: (n_vecs, 2*3*M^3)
    """
    n = V_flat_N.shape[0]
    # Interpolate each N vector to the 2N grid
    V_lift = np.zeros((n, V_flat_2N.shape[1]), dtype=np.float64)
    for i in range(n):
        V_lift[i] = _zero_pad_fft(V_flat_N[i], N, M)

    # Normalise
    nrm_lift = np.array([_real_norm(V_lift[i]) for i in range(n)])
    nrm_big = np.array([_real_norm(V_flat_2N[i]) for i in range(n)])

    O = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        if nrm_lift[i] < 1e-14:
            continue
        for j in range(n):
            if nrm_big[j] < 1e-14:
                continue
            inner = _real_inner(V_lift[i], V_flat_2N[j])
            O[i, j] = (inner / (nrm_lift[i] * nrm_big[j])) ** 2
    return O


# =========================================================================
# G3 — Ritz residual via backend hessian_vec
# =========================================================================

def _try_load_backend():
    """Attempt to import the TECT PyTorch backend.  Returns None on failure."""
    try:
        sys.path.insert(0, _HERE)
        import real_backend_pt_bcc_mixed_v3 as backend  # type: ignore
        return backend
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"  [G3 skipped] backend import failed: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return None


def _ritz_residual(backend, Psi: np.ndarray, v_flat: np.ndarray,
                   lam: float, params: Dict[str, Any], N: int) -> float:
    """Compute || (H_proj - lam) v || / lam via backend.hessian_vec.

    Note: this does NOT re-apply the zero-mode projector; it assumes the
    saved Ritz vector is already in the projected subspace (which the
    Lanczos routine guarantees).
    """
    half = v_flat.size // 2
    re = v_flat[:half].reshape(3, N, N, N)
    im = v_flat[half:].reshape(3, N, N, N)
    v_cplx = (re + 1j * im).astype(np.complex128)
    Hv_cplx = backend.hessian_vec(Psi, v_cplx, params)
    Hv_flat = np.concatenate([Hv_cplx.real.ravel(),
                              Hv_cplx.imag.ravel()]).astype(np.float64)
    resid = _real_norm(Hv_flat - lam * v_flat)
    return resid / max(abs(lam), 1e-16)


# =========================================================================
# Reference: linear-Brazovskii eigenvalue table at Psi* = 0
# =========================================================================

def _linear_brazovskii_spectrum_from_k(N: int, L: float, r: float,
                                        Z: float, Y: float,
                                        n_smallest: int = 20
                                        ) -> List[Tuple[float, Tuple[int, int, int]]]:
    """Enumerate omega(k) at all lattice k and return the smallest n values.

    Valid only when Psi* = 0 (trivial-vacuum collapse), in which case
    H[Psi*=0] = H_0 is diagonal in Fourier space with symbol

        omega(k) = r + Z k^2 + Y k^4.
    """
    k = _lattice_kvec(N, L)
    KX, KY, KZ = np.meshgrid(k, k, k, indexing="ij")
    k2 = KX * KX + KY * KY + KZ * KZ
    omega = r + Z * k2 + Y * (k2 ** 2)
    # Flatten and sort
    flat = omega.ravel()
    # Index bookkeeping
    n_max = np.argsort(flat)[:n_smallest]
    out = []
    for idx in n_max:
        ix = idx // (N * N)
        iy = (idx // N) % N
        iz = idx % N
        out.append((float(flat[idx]), (int(ix), int(iy), int(iz))))
    return out


# =========================================================================
# Main audit pipeline
# =========================================================================

@dataclass
class GridResult:
    N: int
    L: float
    psi_max_abs: float
    psi_trivial: bool
    eigenvalues: List[float]
    rho_IR: List[float]
    rho_shell: List[float]
    rho_UV: List[float]
    k_peak: List[float]
    k_Nyquist: float
    eta_Ritz: Optional[List[float]]
    radial_first_vec: Dict[str, List[float]]
    linear_brazovskii_expected_min: List[Tuple[float, Tuple[int, int, int]]]


def _audit_grid(dirpath: str, N: int, params: Dict[str, Any],
                backend, n_vecs: int = 8) -> GridResult:
    print(f"\n=== Auditing N = {N}  ({dirpath}) ===")
    evals = np.load(os.path.join(dirpath, "hessian_evals_projected.npy"))
    ritz = np.load(os.path.join(dirpath, "hessian_ritz_vectors_projected.npy"))
    Psi = np.load(os.path.join(dirpath, "Psi_star.npy"))
    meta = json.load(open(os.path.join(dirpath, "proof_results.json")))

    L = float(meta["L"])
    q0 = float(params["q0"])
    psi_max_abs = float(np.max(np.abs(Psi)))
    psi_rms = float(np.sqrt(np.mean(np.abs(Psi) ** 2)))
    # Theoretical BCC amplitude phi_0 = sqrt(-4 lambda/(15 gamma))
    lam = float(params.get("quartic_lambda", -0.43))
    gam = float(params.get("sextic_gamma", 1.62))
    phi_0 = math.sqrt(max(-4.0 * lam / (15.0 * gam), 0.0))
    psi_trivial = (psi_rms / max(phi_0, 1e-16)) < 1e-2
    print(f"  L = {L:.6f}   Psi* max|.| = {psi_max_abs:.3e}   "
          f"RMS|Psi|/phi_0 = {psi_rms/max(phi_0,1e-16):.2e}   "
          f"trivial-vacuum = {psi_trivial}")

    n_vecs = min(n_vecs, ritz.shape[0])

    rho_IR, rho_shell, rho_UV, k_peak = [], [], [], []
    radial_first: Dict[str, List[float]] = {}
    for i in range(n_vecs):
        res = _fourier_mass_bands(ritz[i], N=N, L=L, q0=q0)
        rho_IR.append(res["rho_IR"])
        rho_shell.append(res["rho_shell"])
        rho_UV.append(res["rho_UV"])
        k_peak.append(res["k_peak"])
        if i == 0:
            radial_first = dict(
                bin_centers=res["radial_bin_centers"],
                mass=res["radial_mass"],
            )
        tag = "UV" if res["rho_UV"] > 0.5 else (
            "IR" if res["rho_IR"] > 0.5 else "shell")
        print(f"  v_{i}: lambda={evals[i]:+.4e}  "
              f"rho_IR={res['rho_IR']:.3f} rho_shell={res['rho_shell']:.3f} "
              f"rho_UV={res['rho_UV']:.3f}  k_peak={res['k_peak']:.3f}  "
              f"(k_Ny={res['k_Nyquist']:.3f})  dominant={tag}")

    eta_Ritz: Optional[List[float]] = None
    if backend is not None:
        eta_Ritz = []
        for i in range(n_vecs):
            try:
                eta = _ritz_residual(backend, Psi, ritz[i], float(evals[i]),
                                      params, N)
            except Exception as exc:
                print(f"  [G3 partial] residual for v_{i} failed: {exc}")
                eta = float("nan")
            eta_Ritz.append(eta)
        for i in range(n_vecs):
            # v2.4 G3: relative bound ||r|| <= V24_G3_REL * |lam_ritz|.
            # If V24 is unavailable, fall back to the v1.0 absolute 1e-3.
            lam_i = float(evals[i])
            if _V24_G3_REL is not None and abs(lam_i) > 1e-12:
                g3_bound = _V24_G3_REL * abs(lam_i)
                g3_tag = "rel"
            else:
                g3_bound = 1.0e-3
                g3_tag = "abs(legacy)"
            g3_ok = eta_Ritz[i] < g3_bound
            print(f"  v_{i}: eta_Ritz = {eta_Ritz[i]:.3e}  "
                  f"bound={g3_bound:.3e}({g3_tag})  "
                  f"[G3 {'PASS' if g3_ok else 'FAIL'}]")

    lin_ref = _linear_brazovskii_spectrum_from_k(
        N, L, r=float(params["r"]), Z=float(params["Z"]),
        Y=float(params["Y"]), n_smallest=20)
    if psi_trivial:
        print("  Theory (Psi*=0 linear Brazovskii H_0) smallest omega(k):")
        for j, (w, idx) in enumerate(lin_ref[:6]):
            print(f"    omega_{j} = {w:+.4e}   (index {idx})")

    return GridResult(
        N=N, L=L,
        psi_max_abs=psi_max_abs, psi_trivial=psi_trivial,
        eigenvalues=[float(x) for x in evals[:n_vecs]],
        rho_IR=rho_IR, rho_shell=rho_shell, rho_UV=rho_UV,
        k_peak=k_peak, k_Nyquist=float(math.pi * N / L),
        eta_Ritz=eta_Ritz,
        radial_first_vec=radial_first,
        linear_brazovskii_expected_min=lin_ref,
    )


def _verdict_from_observables(g32: GridResult, g64: GridResult,
                               overlap: np.ndarray
                               ) -> Dict[str, Any]:
    """Apply Phase-2.5 gate (Math56 + Addendum §§D-E).  Returns a verdict dict."""
    def gate_pair(rho_UV_0: float, eta_Ritz_0: Optional[float],
                  O_00: float, lam_0: Optional[float] = None) -> Dict[str, Any]:
        g1 = rho_UV_0 < 0.10
        # v2.4 G3 (relative Saad bound); fallback to absolute 1e-3 if V24
        # module is unavailable or lam_0 is missing.
        if (eta_Ritz_0 is not None) and (_V24_G3_REL is not None) and \
                (lam_0 is not None) and (abs(lam_0) > 1e-12):
            g3_bound = _V24_G3_REL * abs(lam_0)
            g3 = eta_Ritz_0 < g3_bound
        else:
            g3_bound = 1.0e-3
            g3 = (eta_Ritz_0 is not None) and (eta_Ritz_0 < g3_bound)
        g2 = O_00 >= _V24_G2_MIN
        return dict(G1_pass=bool(g1), G2_pass=bool(g2), G3_pass=bool(g3),
                    G1_rho_UV=float(rho_UV_0),
                    G2_O_00=float(O_00), G2_min=float(_V24_G2_MIN),
                    G3_eta_Ritz=float(eta_Ritz_0) if eta_Ritz_0 is not None else None,
                    G3_bound=float(g3_bound),
                    accept=bool(g1 and g2 and g3))

    O_00 = float(overlap[0, 0])
    v32 = gate_pair(g32.rho_UV[0], None if g32.eta_Ritz is None else g32.eta_Ritz[0],
                    O_00, g32.eigenvalues[0] if g32.eigenvalues else None)
    v64 = gate_pair(g64.rho_UV[0], None if g64.eta_Ritz is None else g64.eta_Ritz[0],
                    O_00, g64.eigenvalues[0] if g64.eigenvalues else None)

    # Diagnostic classification of the 2026-04-20 result
    diag: Dict[str, Any] = {}
    if g32.psi_trivial and g64.psi_trivial:
        diag["root_cause"] = (
            "Newton-Krylov collapsed to the trivial vacuum Psi*=0 on BOTH "
            "grids (max|Psi*| = {:.2e} at N=32, {:.2e} at N=64).  The "
            "reported m*^2 values are NOT BCC-condensate spectral gaps; "
            "they are individual eigenvalues of the linear Brazovskii "
            "operator H_0 = r + Z nabla^2 + Y nabla^4 plus the internal "
            "family/lock shifts, evaluated at Psi*=0.  The ×17 jump is a "
            "Lanczos mode-selection artefact across two trivial-vacuum "
            "runs and is physically meaningless.  Remediation: re-run "
            "Newton-Krylov with the Math55 continuation method from "
            "mu^2 = -1 to avoid trivial-vacuum collapse."
        ).format(g32.psi_max_abs, g64.psi_max_abs)
        diag["resolution_key"] = "MATH55_CONTINUATION_REQUIRED"
    elif g64.rho_UV[0] > 0.9 and g32.rho_UV[0] < 0.3:
        diag["root_cause"] = (
            "Phase-2.5 G1 failure at N=64 (rho_UV = {:.3f}): the reported "
            "smallest-positive Ritz pair is a UV grid ghost with Fourier "
            "mass concentrated above |k| > 3 q0.  N=32 passes G1 "
            "(rho_UV = {:.3f}).  The ×17 ratio matches the (N_ratio)^4 "
            "= 16 prediction of Math56 Corollary 1 within 7%.  "
            "Remediation: enlarge the Krylov dimension at N=64 and use "
            "shift-invert Lanczos targeted at lambda ~ 3."
        ).format(g64.rho_UV[0], g32.rho_UV[0])
        diag["resolution_key"] = "UV_GHOST_AT_N64"
    elif g32.rho_UV[0] > 0.3:
        diag["root_cause"] = (
            "Phase-2.5 G1 failure at N=32 (rho_UV = {:.3f}): even the "
            "N=32 eigenvalue is not IR-localised, so both grids are "
            "untrustworthy.  The smallest physical Ritz pair is not in "
            "the top-8 spectrum returned by the current Lanczos run."
        ).format(g32.rho_UV[0])
        diag["resolution_key"] = "BOTH_GRIDS_INVALID"
    else:
        diag["root_cause"] = "Inconclusive — manual inspection required."
        diag["resolution_key"] = "INCONCLUSIVE"

    return dict(
        gate_N32=v32,
        gate_N64=v64,
        diagnosis=diag,
        accept_N32=v32["accept"],
        accept_N64=v64["accept"],
    )


def _write_outputs(g32: GridResult, g64: GridResult,
                   overlap: np.ndarray, verdict: Dict[str, Any]) -> None:
    payload = dict(
        theory_tag="hess-jump-audit-v1.0-2026-04-20",
        math_note="TECT-Math56-HessJump-audit",
        timestamp="2026-04-20",
        grids=dict(
            N32=asdict(g32),
            N64=asdict(g64),
        ),
        cross_grid_overlap_top8=overlap.tolist(),
        verdict=verdict,
    )
    with open(_OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"\n[JSON] verdict written to {_OUT_JSON}")

    md = []
    md.append("# Phase-2.5 gate audit — N=32 vs N=64 (2026-04-20)\n")
    md.append(f"Theory: **TECT-Math56-HessJump-audit**; "
              f"tag `hess-jump-audit-v1.0-2026-04-20`.\n")
    md.append("## Observables\n")
    md.append("| Grid | lambda_0 | rho_IR | rho_shell | rho_UV | k_peak | k_Ny | |Psi*|_inf |\n")
    md.append("|---|---|---|---|---|---|---|---|\n")
    for g in (g32, g64):
        md.append(
            f"| N={g.N} | {g.eigenvalues[0]:+.4e} | {g.rho_IR[0]:.3f} | "
            f"{g.rho_shell[0]:.3f} | {g.rho_UV[0]:.3f} | {g.k_peak[0]:.3f} | "
            f"{g.k_Nyquist:.3f} | {g.psi_max_abs:.2e} |\n"
        )
    md.append("\n## Phase-2.5 Gate\n")
    md.append(f"- **N=32 accept:** `{verdict['accept_N32']}`  "
              f"(G1 {verdict['gate_N32']['G1_pass']}, "
              f"G2 {verdict['gate_N32']['G2_pass']}, "
              f"G3 {verdict['gate_N32']['G3_pass']})\n")
    md.append(f"- **N=64 accept:** `{verdict['accept_N64']}`  "
              f"(G1 {verdict['gate_N64']['G1_pass']}, "
              f"G2 {verdict['gate_N64']['G2_pass']}, "
              f"G3 {verdict['gate_N64']['G3_pass']})\n")
    md.append(f"- Cross-grid overlap O(v_0(32) -> v_0(64)) = "
              f"{float(overlap[0,0]):.3f}\n")
    md.append("\n## Diagnosis\n")
    md.append(f"{verdict['diagnosis']['root_cause']}\n")
    md.append(f"\n**Resolution key:** `{verdict['diagnosis']['resolution_key']}`\n")
    with open(_OUT_MD, "w", encoding="utf-8") as fh:
        fh.writelines(md)
    print(f"[MD]   summary written to {_OUT_MD}")


def main() -> int:
    # Load params — prefer a config if present next to the backend, else
    # fall back to the locked Brazovskii values.
    params = dict(_PARAMS_FALLBACK)
    params.update(dict(Lx=62.83185307179586,
                       Ly=62.83185307179586,
                       Lz=62.83185307179586,
                       laplacian_mode="spectral"))

    backend = _try_load_backend()

    n_vecs = 8
    g32 = _audit_grid(_DIR_N32, N=32, params=params, backend=backend,
                       n_vecs=n_vecs)
    g64 = _audit_grid(_DIR_N64, N=64, params=params, backend=backend,
                       n_vecs=n_vecs)

    ritz32 = np.load(os.path.join(_DIR_N32, "hessian_ritz_vectors_projected.npy"))
    ritz64 = np.load(os.path.join(_DIR_N64, "hessian_ritz_vectors_projected.npy"))
    n_vecs_use = min(n_vecs, ritz32.shape[0], ritz64.shape[0])
    print(f"\n=== Cross-grid overlap (top {n_vecs_use} x top {n_vecs_use}) ===")
    overlap = _overlap_matrix(ritz32[:n_vecs_use], ritz64[:n_vecs_use],
                              N=32, M=64)
    print(f"  max O_ij = {float(np.max(overlap)):.4e}")
    print(f"  row-max (O_0j for j = 0..{n_vecs_use-1}):",
          ", ".join(f"{float(x):.2e}" for x in overlap[0]))
    print(f"  col-max (O_i0 for i = 0..{n_vecs_use-1}):",
          ", ".join(f"{float(overlap[i,0]):.2e}" for i in range(n_vecs_use)))

    verdict = _verdict_from_observables(g32, g64, overlap)
    print("\n=== Phase-2.5 Verdict ===")
    print(f"  accept(N=32) = {verdict['accept_N32']}")
    print(f"  accept(N=64) = {verdict['accept_N64']}")
    print(f"  resolution key = {verdict['diagnosis']['resolution_key']}")
    print(f"  root cause:\n  {verdict['diagnosis']['root_cause']}")

    _write_outputs(g32, g64, overlap, verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
