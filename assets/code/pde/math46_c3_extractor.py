#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v0.7
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
"""
math46_c3_extractor.py  v0.7  (2026-04-16)
==========================================

v0.7 peer-review patches (same day) -- two closure fixes on top of v0.6:
    (R4) `pass_T6_final` added to CLI payload.  `pass_T6` reported the
         spectral-numeric result only; a doublet node (pass_frame_nonzero
         = False) could yield pass_T6 = True while the Householder lift
         was silently fictitious.  v0.7 computes
             pass_T6_final = pass_T6 AND pass_frame_nonzero
         and injects it (together with pass_frame_nonzero) into the
         `audit` block so the single top-level field is unambiguous.
    (R5) `_SmokeBackend.hessian_vec` full-field contract.  The smoke
         backend previously read `N = v.shape[0]`, assuming (N,N,N,2)
         doublet-shape input; `ActualBackendAdapter.hessian_vec_full`
         passes (C,N,N,N) full-field tensors, so the smoke test was
         inconsistent with the adapter contract.  Fixed: the backend
         now unpacks `(_C, N, _, _) = v_full.shape` and transposes the
         FFT axes and the K2 broadcast axis accordingly.

v0.6 peer-review patches (retained) -- three completeness fixes on top of v0.5:
    (R1) `compliance["fail_closed_E4"]` semantics.  v0.5 always emitted
         True even for runs that fell back to the surrogate under
         `allow_surrogate=True`; v0.6 computes
         `fail_closed_E4 = (not uses_surrogate_M1M2)`, so the payload
         is self-consistent.
    (R2) CLI description + default output filename are promoted to v0.6
         (previously still advertised v0.4).
    (R3) Frame-singularity audit.  `FrameData` gains `min_norm` and
         `pass_frame_nonzero`; `frame_lift` reports the smallest
         on-site doublet magnitude and flags pass/fail against the
         1e-10 floor.  The doublet-node regime (where the Householder
         lift is silently stabilised by `eps_floor`) is now explicit.
         The CLI emits `frame_audit` in the output JSON.

v0.5 peer-review patches (retained) -- three accuracy fixes on top of v0.4:
    (Q1) Lanczos Tr log normalisation.  The Han-Avron-Saad single-seed
         estimator of <v0, log(A) v0> carries prefactor |v0|^2, NOT the
         ambient dimension n_dim.  Because the seed vector is already
         projected onto the Brazovskii shell (shell_mask), using n_dim
         systematically biased the shell-restricted trace log by the
         shell fill-fraction.  v0.5 replaces `n_dim * log_contrib`
         by `v0_norm2 * log_contrib`.
    (Q2) Delta S_eff symmetric-difference error propagation.  With
         DeltaS_sym = (S_+ + S_- - 2 S_0) / 2, the independent-error
         variance is Var = (sigma_+^2 + sigma_-^2 + 4 sigma_0^2)/4.
         v0.4 used coefficient 2 on sigma_0^2, under-weighting the
         zero-field Tr log noise; v0.5 uses 4.
    (Q3) Backend `covariant_coupling_vec` shape-normalisation guard.
         The v0.4 native-backend branch assumed the backend returned
         doublet-shape (N,N,N,2); real backends are likely to expose a
         full-field-shape (C,N,N,N) interface.  v0.5 accepts either,
         restricting full-shape returns to the doublet via the existing
         embed/restrict helpers, and raises on any other shape.

v0.4 peer-review patches (retained) -- three hard-closures on top of v0.3:
    (P1) Full-field / doublet-shape adapter.  Actual backends expect
         psi_full of shape (C, N, N, N); the doublet probe is (N, N, N, 2).
         `ActualBackendAdapter.hessian_vec_doublet` embeds / restricts via
         the metadata-declared channels, eliminating the silent shape
         mismatch that v0.3 depended on.
    (P2) Fail-closed covariant coupling.  `perturbed_hessian_vec_factory`
         no longer silently falls back to the kinetic-Laplacian surrogate.
         If neither an explicit `covariant_coupling_vec` nor a backend
         method of the same name is available, the factory raises unless
         the caller sets `allow_surrogate=True`.
    (P3) Production CLI + actual-backend loader.  `load_backend()` +
         argparse front-end turn the module into a directly runnable
         extractor against a real run directory.  The synthetic smoke
         harness is demoted to `_smoke_test()` and no longer runs by
         default.

Math46b probe-mode extractor of the Yang-Mills coefficients c_W, c_B.
Theorem target (Math44 Thm.cWcB):

    c_W* = 1 / (96 * pi^2)
    c_B* = 1 / (64 * pi^2)

E1-E7 interface (Math46b Prop.extract):
    E1  load_locked_package   — read actual solver .npy + JSON
    E2  project_doublet       — hard-locked to metadata['doublet_channels']
    E3  frame_lift            — Householder-completed U(2) frame + det-phase winding
    E4  perturbed_operator    — TORUS-EXACT Fourier-space covariant-derivative
                                perturbation of L_full at O(eps) and O(eps^2);
                                replaces the v0.2 non-periodic Wilson-line primitive
    E5  compute_Seff_delta    — Hutchinson-Lanczos Tr log on Brazovskii shell,
                                symmetrised over eps -> +-eps, with explicit
                                positivity audit (pass_positivity,
                                negative_ritz_count, no silent flooring)
    E6  extract_cWcB          — Cor.extract with symmetrised Delta S
    E7  audit_T6              — F1/F2/F3 + positivity carried through

v0.3 closes the four residual defects of v0.2:

    (D1) Doublet identification is no longer provisional.  Metadata must supply
         `doublet_channels`; a missing field raises a hard error.
    (D2) Frame extraction is renamed `frame_lift` (no polar R returned); the
         construction is now presented honestly as a U(2) frame completion, not
         a polar decomposition.  det_phase is preserved and augmented with a
         lattice `phase_winding` diagnostic.
    (D3) The gauge probe no longer uses a straight-line primitive I(x) that
         cannot be made globally periodic on T^3.  Instead the probe is
         implemented as a Fourier-space covariant-derivative perturbation of
         the full Hessian:
             L(eps) = L_full + eps * M_1[a] + eps^2 * M_2[a]
         with a_mu(x) = eps_mu cos(q.x) strictly periodic.  Delta S_eff is
         extracted from the symmetrised Tr log difference at O(eps^2).
    (D4) The Tr log estimator no longer silently floors non-positive Ritz
         values.  pass_positivity and negative_ritz_count are explicit audit
         outputs; pass_T6 requires pass_positivity.

Honest scope-limits carried forward:
 - Single-generator plane-wave probes only (sufficient for Cor.extract).
 - Backend adapter must expose `hessian_vec(psi, v, config)` for L_full, and
   optionally `covariant_coupling_vec(psi, v, probe, order)` for M_1, M_2.
   A default implementation of the covariant-coupling operators is provided
   for backends that expose only the kinetic Laplacian block.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Tuple

import numpy as np

# ----------------------------------------------------------------------
# Module-level constants (locked).
# ----------------------------------------------------------------------
TARGET_CW = 1.0 / (96.0 * math.pi * math.pi)
TARGET_CB = 1.0 / (64.0 * math.pi * math.pi)
DEFAULT_AUDIT_TOL = 1.0e-2

# Pauli generators on the doublet (SU(2)_W: sigma_i / 2, U(1)_Y: (1/2) I).
_SIGMA_1 = 0.5 * np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
_SIGMA_2 = 0.5 * np.array([[0.0, -1j], [1j, 0.0]], dtype=np.complex128)
_HYPER_Y = 0.5 * np.eye(2, dtype=np.complex128)

GENERATORS: dict[str, np.ndarray] = {
    "T1": _SIGMA_1,
    "T2": _SIGMA_2,
    "Y":  _HYPER_Y,
}

# ======================================================================
# E1. load_locked_package
# ======================================================================
@dataclass
class LockedPackage:
    psi_full: np.ndarray            # (n_channels, N, N, N) complex
    config:   dict[str, Any]
    metadata: dict[str, Any]
    path:     Path

    @property
    def N(self) -> int:
        return int(self.psi_full.shape[-1])

    @property
    def L(self) -> float:
        return float(self.config["physical_L"])

    @property
    def doublet_channels(self) -> Tuple[int, int]:
        """Math46b E2 requires metadata['doublet_channels'].

        v0.3 fail-closed contract: a missing or malformed field raises.
        """
        dc = self.metadata.get("doublet_channels")
        if dc is None:
            raise ValueError(
                "Math46b E2: metadata['doublet_channels'] missing.  "
                "c3-extractor v0.3 refuses to fall back to a provisional "
                "channel pair; the solver package must declare the "
                "electroweak doublet storage convention."
            )
        if not (isinstance(dc, (list, tuple)) and len(dc) == 2):
            raise ValueError(
                f"metadata['doublet_channels'] must be a 2-tuple, got {dc!r}"
            )
        c0, c1 = int(dc[0]), int(dc[1])
        n = int(self.psi_full.shape[0])
        if not (0 <= c0 < n and 0 <= c1 < n and c0 != c1):
            raise ValueError(
                f"doublet_channels={dc} incompatible with psi_full of "
                f"channel-count {n}."
            )
        return (c0, c1)


def load_locked_package(root: str | Path) -> LockedPackage:
    root = Path(root)
    psi_full = np.load(root / "Psi_corr.npy")
    with open(root / "config.json", "r", encoding="utf-8") as fh:
        config = json.load(fh)
    with open(root / "metadata.json", "r", encoding="utf-8") as fh:
        metadata = json.load(fh)
    return LockedPackage(
        psi_full=psi_full.astype(np.complex128, copy=False),
        config=config,
        metadata=metadata,
        path=root,
    )


# ======================================================================
# E2. project_doublet
# ======================================================================
def project_doublet(pkg: LockedPackage,
                    doublet_projector: Callable[[np.ndarray, LockedPackage], np.ndarray] | None = None,
                    ) -> np.ndarray:
    """Return Psi_D of shape (N, N, N, 2), complex.

    Default path: channel pair taken from metadata (E2 fail-closed).
    Custom path: user supplies a callable for non-trivial Class-III projections.
    """
    if doublet_projector is not None:
        psi_D = doublet_projector(pkg.psi_full, pkg)
    else:
        c0, c1 = pkg.doublet_channels
        psi_D = np.stack([pkg.psi_full[c0], pkg.psi_full[c1]], axis=-1)
    if psi_D.ndim != 4 or psi_D.shape[-1] != 2:
        raise ValueError(
            f"project_doublet returned shape {psi_D.shape}; expected (N,N,N,2)."
        )
    return psi_D.astype(np.complex128, copy=False)


# ======================================================================
# E2b. full-field / doublet adapter  (v0.4 Patch 1)
# ======================================================================
def embed_doublet(pkg: LockedPackage, psi_D: np.ndarray) -> np.ndarray:
    """Embed a doublet-shaped field (N,N,N,2) back into full-field layout.

    Non-doublet channels are zeroed.  This is the correct tangent-space
    embedding for `backend.hessian_vec` when the electroweak probe acts
    only on the declared doublet channels.
    """
    if psi_D.ndim != 4 or psi_D.shape[-1] != 2:
        raise ValueError(f"embed_doublet: expected (N,N,N,2), got {psi_D.shape}")
    c0, c1 = pkg.doublet_channels
    out = np.zeros_like(pkg.psi_full, dtype=np.complex128)
    out[c0] = psi_D[..., 0]
    out[c1] = psi_D[..., 1]
    return out


def restrict_full_to_doublet(pkg: LockedPackage, v_full: np.ndarray) -> np.ndarray:
    """Restrict a full-field vector back to the declared doublet channels."""
    if v_full.shape != pkg.psi_full.shape:
        raise ValueError(
            f"restrict_full_to_doublet: expected full shape {pkg.psi_full.shape}, "
            f"got {v_full.shape}"
        )
    c0, c1 = pkg.doublet_channels
    return np.stack([v_full[c0], v_full[c1]], axis=-1).astype(np.complex128, copy=False)


class ActualBackendAdapter:
    """Doublet-aware wrapper around an actual solver backend module.

    `backend_module.hessian_vec(psi_full, v_full, config)` must exist.
    Optionally, `backend_module.covariant_coupling_vec(psi_full, v_D, probe, order)`
    exposes M_1 / M_2 at the native backend level; if absent, the v0.4
    fail-closed policy refuses the extraction unless the caller explicitly
    opts into the kinetic surrogate.
    """

    def __init__(self, backend_module: Any, pkg: LockedPackage) -> None:
        if not hasattr(backend_module, "hessian_vec"):
            raise AttributeError(
                "Backend module lacks required symbol 'hessian_vec'"
            )
        self.backend = backend_module
        self.pkg = pkg
        self.config = dict(pkg.config)

    def hessian_vec_full(self, v_full: np.ndarray) -> np.ndarray:
        return np.asarray(
            self.backend.hessian_vec(self.pkg.psi_full, v_full, self.config),
            dtype=np.complex128,
        )

    def hessian_vec_doublet(self, v_D: np.ndarray) -> np.ndarray:
        """Apply the actual full Hessian to a doublet probe via embed / restrict."""
        v_full = embed_doublet(self.pkg, v_D)
        Hv_full = self.hessian_vec_full(v_full)
        return restrict_full_to_doublet(self.pkg, Hv_full)


# ======================================================================
# E3. frame_lift  (v0.3: renamed from polar_frame; no polar R returned)
# ======================================================================
@dataclass
class FrameData:
    F0:                np.ndarray     # (N,N,N,2,2) complex unitary
    det_phase:         np.ndarray     # (N,N,N)    complex, |det_phase|=1
    norm:              np.ndarray     # (N,N,N)    real, |psi_D|
    phase_winding:     dict[str, int] # integer winding of arg(det F0) per axis
    # v0.6 Patch R3 -- frame-singularity audit.  `min_norm` is the
    # smallest on-site doublet magnitude; `pass_frame_nonzero` is True
    # iff `min_norm` exceeds the hard floor below which the Householder
    # lift is geometrically meaningless (the doublet has a node).
    min_norm:          float
    pass_frame_nonzero: bool


def _integer_winding_1d(phase: np.ndarray) -> int:
    """Integer winding of a unit-modulus complex sequence along a periodic axis.

    Sums the unwrapped phase difference around the periodic loop and rounds
    to the nearest integer multiple of 2 pi.
    """
    arg = np.angle(phase)
    diff = np.diff(np.concatenate([arg, arg[:1]]))
    diff = np.angle(np.exp(1j * diff))  # wrap into (-pi, pi]
    return int(round(float(np.sum(diff)) / (2.0 * math.pi)))


def frame_lift(psi_D: np.ndarray, eps_floor: float = 1.0e-14) -> FrameData:
    """Construct a per-site U(2) frame F0 whose first column is psi_D / |psi_D|.

    v0.3 docstring policy: this is a *frame completion*, not a polar
    decomposition.  The second column is the Householder-orthogonal complement
    v = (-conj(b), conj(a))/norm with (a,b) = first column.  The phase of
    det(F0) encodes the residual U(1)_em direction and is returned as the
    `det_phase` array.  Integer winding of arg(det F0) along the three lattice
    axes is returned for topology diagnostics.
    """
    if psi_D.ndim != 4 or psi_D.shape[-1] != 2:
        raise ValueError(f"frame_lift: expected shape (N,N,N,2), got {psi_D.shape}")

    norm = np.linalg.norm(psi_D, axis=-1)
    norm_safe = np.maximum(norm, eps_floor)
    u = psi_D / norm_safe[..., None]

    a = u[..., 0]
    b = u[..., 1]
    v = np.stack([-np.conj(b), np.conj(a)], axis=-1)
    F0 = np.stack([u, v], axis=-1)   # (N,N,N,2,2)

    det_F0 = F0[..., 0, 0] * F0[..., 1, 1] - F0[..., 0, 1] * F0[..., 1, 0]
    det_phase = det_F0 / np.maximum(np.abs(det_F0), eps_floor)

    phase_winding = {
        "x": _integer_winding_1d(det_phase[:, 0, 0]),
        "y": _integer_winding_1d(det_phase[0, :, 0]),
        "z": _integer_winding_1d(det_phase[0, 0, :]),
    }

    # v0.6 Patch R3 -- audit the minimum on-site doublet magnitude.  A
    # near-zero |psi_D| signals a doublet node at which the Householder
    # frame lift is silently regularised by eps_floor; this is a quiet
    # numerical risk that the caller must be able to flag.
    min_norm = float(np.min(norm))
    pass_frame_nonzero = bool(min_norm > 1.0e-10)

    return FrameData(
        F0=F0,
        det_phase=det_phase,
        norm=norm,
        phase_winding=phase_winding,
        min_norm=min_norm,
        pass_frame_nonzero=pass_frame_nonzero,
    )


# ======================================================================
# E4. Torus-exact perturbed operator  (v0.3: covariant-derivative formulation)
# ======================================================================
@dataclass
class PlaneWaveProbe:
    q:        np.ndarray      # (3,) float -- lattice momentum 2 pi n / L
    epsilon:  np.ndarray      # (3,) float -- polarisation amplitude (transverse: eps . q = 0)
    gen_name: str             # one of "T1","T2","Y"
    use_cos:  bool = True     # a_mu(x) = epsilon_mu cos(q.x) (else sin)

    @property
    def generator(self) -> np.ndarray:
        return GENERATORS[self.gen_name]

    @property
    def q2(self) -> float:
        return float(np.dot(self.q, self.q))


def _probe_field(probe: PlaneWaveProbe, N: int, L: float) -> np.ndarray:
    """Return a_mu(x) evaluated on the lattice: shape (3, N, N, N), real."""
    ax = np.arange(N) * (L / N)
    X = np.meshgrid(ax, ax, ax, indexing="ij")
    phase = probe.q[0] * X[0] + probe.q[1] * X[1] + probe.q[2] * X[2]
    envelope = np.cos(phase) if probe.use_cos else np.sin(phase)
    a = np.empty((3, N, N, N), dtype=np.float64)
    for mu in range(3):
        a[mu] = probe.epsilon[mu] * envelope
    return a


def _default_covariant_coupling_vec(pkg: LockedPackage,
                                    v: np.ndarray,
                                    probe: PlaneWaveProbe,
                                    order: int,
                                    ) -> np.ndarray:
    """Default M_1 / M_2 action for a kinetic-Laplacian backend.

    Covariant-Laplacian expansion:
        (D_mu)^2 = partial^2 + i eps { a_mu, partial_mu } T + eps^2 a_mu a^mu T^2.
    Hence
        M_1 v = 2i * a_mu * T * partial_mu v  +  i * (partial_mu a_mu) * T * v
        M_2 v = (a_mu a^mu) * T^2 * v
    v has shape (N, N, N, 2).  All operations are FFT-based, so periodicity on
    T^3 is manifest.
    """
    N = pkg.N
    L = pkg.L
    a_field = _probe_field(probe, N, L)    # (3, N, N, N)
    T = probe.generator                    # (2, 2)

    if order == 1:
        k = 2.0 * np.pi * np.fft.fftfreq(N, d=L / N)
        km_doublet = [k[:, None, None, None],
                      k[None, :, None, None],
                      k[None, None, :, None]]
        km_scalar = [k[:, None, None], k[None, :, None], k[None, None, :]]
        v_k = np.fft.fftn(v, axes=(0, 1, 2))
        grad = [np.fft.ifftn(1j * km_doublet[mu] * v_k, axes=(0, 1, 2))
                for mu in range(3)]

        div_a_k = np.zeros((N, N, N), dtype=np.complex128)
        for mu in range(3):
            div_a_k += 1j * km_scalar[mu] * np.fft.fftn(a_field[mu], axes=(0, 1, 2))
        div_a = np.fft.ifftn(div_a_k, axes=(0, 1, 2)).real

        Tv = v @ T.T
        result = np.zeros_like(v, dtype=np.complex128)
        for mu in range(3):
            Tgrad_mu = grad[mu] @ T.T
            result += 2j * a_field[mu][..., None] * Tgrad_mu
        result += 1j * div_a[..., None] * Tv
        return result

    if order == 2:
        a2 = np.sum(a_field * a_field, axis=0)
        T2v = v @ (T @ T).T
        return a2[..., None] * T2v

    raise ValueError(f"covariant_coupling order must be 1 or 2, got {order!r}")


def perturbed_hessian_vec_factory(
    pkg: LockedPackage,
    backend: ActualBackendAdapter,
    probe: PlaneWaveProbe,
    covariant_coupling_vec: Callable[..., np.ndarray] | None = None,
    allow_surrogate: bool = False,
) -> Tuple[Callable[[np.ndarray, float], np.ndarray], bool]:
    """Return `(matvec, used_surrogate)` for L(eps) on the doublet subspace.

        L(eps) v_D = H_full(v_D) + eps * M_1[a] v_D + eps^2 * M_2[a] v_D

    Resolution order for the covariant coupling (v0.4 fail-closed policy):
      1. `covariant_coupling_vec` passed explicitly by the caller.
      2. `backend.backend.covariant_coupling_vec(psi_full, v_D, probe, order)`.
      3. Kinetic-Laplacian surrogate -- ONLY if `allow_surrogate=True`;
         otherwise a RuntimeError is raised.
    """
    used_surrogate = False

    if covariant_coupling_vec is not None:
        def cc(v_D: np.ndarray, order: int) -> np.ndarray:
            return covariant_coupling_vec(pkg, v_D, probe, order)
    elif hasattr(backend.backend, "covariant_coupling_vec"):
        cc_native = backend.backend.covariant_coupling_vec
        def cc(v_D: np.ndarray, order: int) -> np.ndarray:
            # Shape-normalisation guard: backend authors may return either
            # the doublet-shape (N,N,N,2) -- matching the extractor probe
            # space -- or the full-field shape (C,N,N,N) -- matching the
            # natural domain of the ambient Hessian.  Both are physically
            # correct; we restrict to doublet in the latter case so the
            # downstream shape contract in `matvec` is honoured.
            raw = np.asarray(
                cc_native(pkg.psi_full, v_D, probe, order),
                dtype=np.complex128,
            )
            if raw.shape == v_D.shape:
                return raw
            if raw.shape == pkg.psi_full.shape:
                return restrict_full_to_doublet(pkg, raw)
            raise ValueError(
                f"backend.covariant_coupling_vec returned shape {raw.shape}; "
                f"expected either doublet shape {v_D.shape} or full shape "
                f"{pkg.psi_full.shape}."
            )
    elif allow_surrogate:
        used_surrogate = True
        def cc(v_D: np.ndarray, order: int) -> np.ndarray:
            return _default_covariant_coupling_vec(pkg, v_D, probe, order)
    else:
        raise RuntimeError(
            "Math46b E4 fail-closed: backend lacks covariant_coupling_vec "
            "and no explicit covariant_coupling_vec override was supplied. "
            "Refusing to use the kinetic surrogate silently.  Either (a) "
            "implement covariant_coupling_vec on the backend, (b) pass one "
            "explicitly to run_extractor, or (c) pass allow_surrogate=True "
            "if a regression-only estimate is acceptable."
        )

    def matvec(v_D: np.ndarray, eps: float) -> np.ndarray:
        if v_D.ndim != 4 or v_D.shape[-1] != 2:
            raise ValueError(f"E4 matvec expects (N,N,N,2), got {v_D.shape}")
        base = backend.hessian_vec_doublet(v_D)
        if eps == 0.0:
            return base
        M1 = cc(v_D, 1)
        M2 = cc(v_D, 2)
        if M1.shape != v_D.shape or M2.shape != v_D.shape:
            raise ValueError(
                f"E4 covariant operator shape mismatch: "
                f"M1 {M1.shape}, M2 {M2.shape}, expected {v_D.shape}"
            )
        return base + eps * M1 + (eps * eps) * M2

    return matvec, used_surrogate


# ======================================================================
# E5. Brazovskii-shell restricted Tr log  (Hutchinson + Lanczos)
# ======================================================================
def brazovskii_shell_mask(N: int, L: float, q0: float, delta: float) -> np.ndarray:
    """FFT-space indicator 1{ | |k| - q0 | <= delta } on an (N,N,N) grid."""
    k = 2.0 * np.pi * np.fft.fftfreq(N, d=L / N)
    KX, KY, KZ = np.meshgrid(k, k, k, indexing="ij")
    K = np.sqrt(KX * KX + KY * KY + KZ * KZ)
    return (np.abs(K - q0) <= delta).astype(np.float64)


def project_onto_shell(v: np.ndarray, shell_mask: np.ndarray) -> np.ndarray:
    """Project (N,N,N,2) doublet field onto Brazovskii shell in Fourier space."""
    v_k = np.fft.fftn(v, axes=(0, 1, 2))
    v_k *= shell_mask[..., None]
    return np.fft.ifftn(v_k, axes=(0, 1, 2))


@dataclass
class LanczosLogResult:
    log_estimate:        float
    negative_ritz_count: int
    min_ritz:            float
    max_ritz:            float


def _lanczos_log_from_matvec(matvec: Callable[[np.ndarray], np.ndarray],
                             v0: np.ndarray,
                             m: int,
                             positivity_tol: float = 1.0e-12,
                             ) -> LanczosLogResult:
    """m-step Lanczos with Han-Avron-Saad Ritz log estimator.

    Non-positive Ritz values are NOT floored.  Their count is reported so the
    audit layer can declare pass_positivity = False.
    """
    shape = v0.shape
    # Han-Avron-Saad estimator of <v0, log(A) v0> for a single Rademacher
    # seed.  The prefactor is |v0|^2 = <v0, v0>, NOT n_dim: the seed has
    # already been projected onto the Brazovskii shell (shell_mask), so
    # E[v0 v0^H] = P_shell, not I_n.  Using n_dim here biases the
    # shell-restricted trace log by the fill-fraction factor.
    v0_norm2 = float(np.vdot(v0.ravel(), v0.ravel()).real)
    norm_v = math.sqrt(v0_norm2)
    if norm_v == 0.0:
        raise ValueError("Lanczos seed vector has zero norm.")
    q_prev = np.zeros_like(v0)
    q_cur  = v0 / norm_v

    alphas = np.zeros(m, dtype=np.float64)
    betas  = np.zeros(m - 1, dtype=np.float64)
    j_end = m
    for j in range(m):
        w = matvec(q_cur)
        if j > 0:
            w = w - betas[j - 1] * q_prev
        alpha = float(np.real(np.vdot(q_cur.ravel(), w.ravel())))
        alphas[j] = alpha
        w = w - alpha * q_cur
        w = w - float(np.real(np.vdot(q_prev.ravel(), w.ravel()))) * q_prev
        w = w - float(np.real(np.vdot(q_cur.ravel(),  w.ravel()))) * q_cur
        if j < m - 1:
            beta = float(np.linalg.norm(w.ravel()))
            betas[j] = beta
            if beta < 1.0e-14:
                j_end = j + 1
                break
            q_prev = q_cur
            q_cur  = w / beta

    a_use = alphas[:j_end]
    b_use = betas[: max(j_end - 1, 0)]
    T = np.diag(a_use)
    if b_use.size > 0:
        T += np.diag(b_use, k=1) + np.diag(b_use, k=-1)
    ritz, U = np.linalg.eigh(T)
    e1_sq = (U[0, :]) ** 2
    neg = int(np.sum(ritz <= positivity_tol))
    safe_mask = ritz > positivity_tol
    log_contrib = float(np.sum(e1_sq[safe_mask] * np.log(ritz[safe_mask])))
    log_estimate = v0_norm2 * log_contrib

    return LanczosLogResult(
        log_estimate=log_estimate,
        negative_ritz_count=neg,
        min_ritz=float(ritz.min()),
        max_ritz=float(ritz.max()),
    )


@dataclass
class TrLogEstimate:
    mean:                float
    std:                 float
    negative_ritz_total: int
    pass_positivity:     bool


def hutchinson_tr_log_shell(matvec_L: Callable[[np.ndarray], np.ndarray],
                            shape: Tuple[int, ...],
                            shell_mask: np.ndarray,
                            n_samples: int,
                            lanczos_steps: int,
                            rng: np.random.Generator,
                            ) -> TrLogEstimate:
    """Complex-Rademacher Hutchinson estimator of Tr log restricted to the shell.

    Final scaling:  (1/2) * mean_over_samples  (the one-loop prefactor).
    """
    samples = []
    neg_total = 0
    for _ in range(n_samples):
        r_real = rng.choice([-1.0, +1.0], size=shape)
        r_imag = rng.choice([-1.0, +1.0], size=shape)
        z = (r_real + 1j * r_imag) / math.sqrt(2.0)
        z = project_onto_shell(z, shell_mask)

        def matvec_proj(v: np.ndarray) -> np.ndarray:
            return project_onto_shell(matvec_L(project_onto_shell(v, shell_mask)), shell_mask)

        res = _lanczos_log_from_matvec(matvec_proj, z, lanczos_steps)
        samples.append(res.log_estimate)
        neg_total += res.negative_ritz_count
    arr = np.asarray(samples, dtype=np.float64)
    mean = 0.5 * float(arr.mean())
    std  = 0.5 * float(arr.std(ddof=1) / math.sqrt(max(n_samples, 1))) if n_samples > 1 else 0.0
    return TrLogEstimate(
        mean=mean,
        std=std,
        negative_ritz_total=neg_total,
        pass_positivity=(neg_total == 0),
    )


# ======================================================================
# E5/E6. Symmetrised Delta S_eff at +-eps and c_W / c_B extraction
# ======================================================================
@dataclass
class DeltaSeffResult:
    delta_S_plus:      float
    delta_S_minus:     float
    delta_S_symmetric: float   # ( DS(+eps) + DS(-eps) ) / 2
    delta_S_std:       float
    neg_ritz_total:    int
    pass_positivity:   bool


def compute_Seff_delta(matvec_factory: Callable[[np.ndarray, float], np.ndarray],
                       shape: Tuple[int, ...],
                       shell_mask: np.ndarray,
                       eps: float,
                       n_samples: int,
                       lanczos_steps: int,
                       rng: np.random.Generator,
                       ) -> DeltaSeffResult:
    """Return symmetrised Delta S_eff(eps) = (1/2) [ DS(+eps) + DS(-eps) ].

    Symmetrisation cancels any residual O(eps) numerical drift and enforces the
    gauge-invariance condition that the physical response is even in eps.
    """
    def mk(e: float) -> Callable[[np.ndarray], np.ndarray]:
        return lambda v: matvec_factory(v, e)

    est_plus  = hutchinson_tr_log_shell(mk(+eps), shape, shell_mask,
                                        n_samples, lanczos_steps, rng)
    est_zero  = hutchinson_tr_log_shell(mk(0.0),  shape, shell_mask,
                                        n_samples, lanczos_steps, rng)
    est_minus = hutchinson_tr_log_shell(mk(-eps), shape, shell_mask,
                                        n_samples, lanczos_steps, rng)

    dS_plus  = est_plus.mean  - est_zero.mean
    dS_minus = est_minus.mean - est_zero.mean
    dS_sym   = 0.5 * (dS_plus + dS_minus)
    # DeltaS_sym = (S_+ + S_- - 2 S_0) / 2.  For independent estimators:
    #   Var(DeltaS_sym) = (sigma_+^2 + sigma_-^2 + 4 sigma_0^2) / 4.
    # (v0.4 used a 2*sigma_0^2 coefficient, which under-weighted S_0.)
    dS_std = 0.5 * math.sqrt(
        est_plus.std ** 2
        + est_minus.std ** 2
        + 4.0 * est_zero.std ** 2
    )
    neg_total = (est_plus.negative_ritz_total
                 + est_minus.negative_ritz_total
                 + est_zero.negative_ritz_total)

    return DeltaSeffResult(
        delta_S_plus=dS_plus,
        delta_S_minus=dS_minus,
        delta_S_symmetric=dS_sym,
        delta_S_std=dS_std,
        neg_ritz_total=neg_total,
        pass_positivity=(neg_total == 0),
    )


def extract_coefficient(delta_S: float, V: float, eps: float, q2: float) -> float:
    """Cor.extract:  coeff = 2 * Delta S / ( V * eps^2 * q^2 )."""
    denom = max(V * eps * eps * q2, 1.0e-30)
    return 2.0 * delta_S / denom


# ======================================================================
# E7. audit_T6
# ======================================================================
@dataclass
class AuditT6:
    cW_T1:           float
    cW_T2:           float
    cB:              float
    cW_avg:          float
    cW_target:       float
    cB_target:       float
    isotropy_defect: float
    pass_F1:         bool
    pass_F2:         bool
    pass_F3:         bool
    pass_positivity: bool
    pass_T6:         bool
    audit_margin:    float


def audit_T6(cW_T1: float, cW_T2: float, cB: float,
             pass_positivity: bool,
             tol: float = DEFAULT_AUDIT_TOL) -> AuditT6:
    cW_avg = 0.5 * (cW_T1 + cW_T2)
    err_F1 = abs(cW_avg - TARGET_CW) / TARGET_CW
    err_F2 = abs(cB     - TARGET_CB) / TARGET_CB
    iso    = abs(cW_T1 - cW_T2) / max(abs(cW_avg), 1.0e-30)

    pass_F1 = err_F1 <= tol
    pass_F2 = err_F2 <= tol
    pass_F3 = iso    <= tol
    pass_T6 = bool(pass_F1 and pass_F2 and pass_F3 and pass_positivity)
    margin  = float(tol - max(err_F1, err_F2, iso))

    return AuditT6(
        cW_T1=cW_T1, cW_T2=cW_T2, cB=cB,
        cW_avg=cW_avg,
        cW_target=TARGET_CW, cB_target=TARGET_CB,
        isotropy_defect=iso,
        pass_F1=pass_F1, pass_F2=pass_F2, pass_F3=pass_F3,
        pass_positivity=pass_positivity,
        pass_T6=pass_T6,
        audit_margin=margin,
    )


# ======================================================================
# Top-level driver
# ======================================================================
@dataclass
class ExtractorConfig:
    eps:                float = 1.0e-5
    shell_delta_factor: float = 0.25
    n_samples:          int   = 32
    lanczos_steps:      int   = 48
    audit_tol:          float = DEFAULT_AUDIT_TOL
    seed:               int   = 20260416


def canonical_transverse_probes(L: float) -> Tuple[PlaneWaveProbe,
                                                    PlaneWaveProbe,
                                                    PlaneWaveProbe]:
    """Three canonical transverse probes with eps . q = 0 for every generator."""
    k0 = 2.0 * math.pi / L
    qX = np.array([k0, 0.0, 0.0])
    qY = np.array([0.0, k0, 0.0])
    qZ = np.array([0.0, 0.0, k0])
    eX = np.array([1.0, 0.0, 0.0])
    eY = np.array([0.0, 1.0, 0.0])
    eZ = np.array([0.0, 0.0, 1.0])
    probe_T1 = PlaneWaveProbe(q=qY, epsilon=eX, gen_name="T1")
    probe_T2 = PlaneWaveProbe(q=qZ, epsilon=eY, gen_name="T2")
    probe_Y  = PlaneWaveProbe(q=qX, epsilon=eZ, gen_name="Y")
    return probe_T1, probe_T2, probe_Y


def run_extractor(pkg: LockedPackage,
                  backend: ActualBackendAdapter,
                  cfg: ExtractorConfig | None = None,
                  covariant_coupling_vec: Callable[..., np.ndarray] | None = None,
                  doublet_projector: Callable[[np.ndarray, LockedPackage], np.ndarray] | None = None,
                  allow_surrogate: bool = False,
                  ) -> dict[str, Any]:
    """Execute the full Math46b E1-E7 pipeline and return a results dict."""
    if cfg is None:
        cfg = ExtractorConfig()
    rng = np.random.default_rng(cfg.seed)

    psi_D = project_doublet(pkg, doublet_projector)
    frame = frame_lift(psi_D)

    q0 = float(pkg.config.get("q0", pkg.config.get("q_star", 1.0)))
    shell_delta = cfg.shell_delta_factor * q0
    shell_mask  = brazovskii_shell_mask(pkg.N, pkg.L, q0, shell_delta)

    probe_T1, probe_T2, probe_Y = canonical_transverse_probes(pkg.L)
    V     = pkg.L ** 3
    shape = (pkg.N, pkg.N, pkg.N, 2)    # doublet subspace only

    used_surrogate_flags: list[bool] = []

    def run_probe(probe: PlaneWaveProbe) -> Tuple[float, DeltaSeffResult]:
        matvec, used_surr = perturbed_hessian_vec_factory(
            pkg, backend, probe,
            covariant_coupling_vec=covariant_coupling_vec,
            allow_surrogate=allow_surrogate,
        )
        used_surrogate_flags.append(used_surr)
        ds = compute_Seff_delta(matvec, shape, shell_mask,
                                cfg.eps, cfg.n_samples, cfg.lanczos_steps, rng)
        coeff = extract_coefficient(ds.delta_S_symmetric, V, cfg.eps, probe.q2)
        return coeff, ds

    cW_T1, dsT1 = run_probe(probe_T1)
    cW_T2, dsT2 = run_probe(probe_T2)
    cB,    dsY  = run_probe(probe_Y)

    pos = dsT1.pass_positivity and dsT2.pass_positivity and dsY.pass_positivity
    audit = audit_T6(cW_T1, cW_T2, cB, pass_positivity=pos, tol=cfg.audit_tol)

    # v0.6 Patch R1 -- correct compliance semantics.
    # A run is Math46b-E4 fail-closed iff no probe fell back to the
    # kinetic-Laplacian surrogate M_1 ~ partial, M_2 ~ 0; the v0.5
    # payload always set this to True, which misreported
    # allow_surrogate=True runs.
    uses_surrogate  = bool(any(used_surrogate_flags))
    fail_closed_E4  = bool(not uses_surrogate)

    return {
        "audit":       audit,
        "frame":       frame,
        "delta_S_T1":  dsT1,
        "delta_S_T2":  dsT2,
        "delta_S_Y":   dsY,
        "shell_q0":    q0,
        "shell_delta": shell_delta,
        "config":      cfg,
        "compliance": {
            "fail_closed_E4":      fail_closed_E4,
            "uses_surrogate_M1M2": uses_surrogate,
            "doublet_channels":    list(pkg.doublet_channels),
        },
    }


# ----------------------------------------------------------------------
# Minimal self-check on a synthetic backend (no real solver required).
# ----------------------------------------------------------------------
class _SmokeBackend:
    """Kinetic Laplacian only: L_full psi = ( -partial^2 + mass^2 ) psi.

    v0.7 contract: `hessian_vec(psi_full, v_full, config)` receives and
    returns full-field arrays of shape (C, N, N, N), matching the actual
    backend interface expected by `ActualBackendAdapter.hessian_vec_full`.
    The v0.6 version assumed shape (N, N, N, 2) on the first spatial axis,
    which was inconsistent with the adapter embed/restrict cycle.
    """
    def __init__(self, mass_sq: float = 1.0):
        self.mass_sq = mass_sq

    def hessian_vec(self, psi_full: np.ndarray, v_full: np.ndarray, config: dict) -> np.ndarray:
        # v_full shape: (C, N, N, N)
        _C, N, _, _ = v_full.shape
        L = float(config["physical_L"])
        k = 2.0 * np.pi * np.fft.fftfreq(N, d=L / N)
        KX, KY, KZ = np.meshgrid(k, k, k, indexing="ij")
        K2 = (KX * KX + KY * KY + KZ * KZ)[None, ...]   # (1,N,N,N) — broadcast over C
        v_k = np.fft.fftn(v_full, axes=(1, 2, 3))
        Hv_k = (K2 + self.mass_sq) * v_k
        return np.fft.ifftn(Hv_k, axes=(1, 2, 3))


def _smoke_test() -> None:
    """Synthetic smoke run (free-Laplacian backend) -- no real package required.

    Exercises the end-to-end pipeline, including the fail-closed policy via
    allow_surrogate=True.  Never invoked by the production CLI.
    """
    N = 8
    L = 2.0 * math.pi
    rng0 = np.random.default_rng(0)
    psi_full = rng0.standard_normal((3, N, N, N)).astype(np.complex128) \
             + 1j * rng0.standard_normal((3, N, N, N))
    metadata = {"doublet_channels": [1, 2]}
    config   = {"physical_L": L, "q0": 1.0}
    pkg = LockedPackage(psi_full=psi_full, config=config, metadata=metadata, path=Path("."))
    backend = ActualBackendAdapter(_SmokeBackend(mass_sq=0.5), pkg)
    cfg = ExtractorConfig(n_samples=2, lanczos_steps=8)
    out = run_extractor(pkg, backend=backend, cfg=cfg, allow_surrogate=True)
    a = out["audit"]
    print(f"smoke: cW_T1={a.cW_T1:+.3e}  cW_T2={a.cW_T2:+.3e}  "
          f"cB={a.cB:+.3e}  pass_pos={a.pass_positivity}  "
          f"pass_T6={a.pass_T6}  surrogate={out['compliance']['uses_surrogate_M1M2']}")


# ======================================================================
# Production CLI  (v0.4 Patch 3)
# ======================================================================
def load_backend(path: str | Path) -> Any:
    import importlib.util
    import sys
    p = Path(path).expanduser().resolve()
    spec = importlib.util.spec_from_file_location("tect_backend_actual", str(p))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load backend from {p}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tect_backend_actual"] = mod
    spec.loader.exec_module(mod)
    if not hasattr(mod, "hessian_vec"):
        raise AttributeError(f"Backend {p.name} lacks required symbol 'hessian_vec'")
    return mod


def _audit_to_jsonable(audit: AuditT6) -> dict:
    return {
        "cW_T1":           audit.cW_T1,
        "cW_T2":           audit.cW_T2,
        "cB":              audit.cB,
        "cW_avg":          audit.cW_avg,
        "cW_target":       audit.cW_target,
        "cB_target":       audit.cB_target,
        "isotropy_defect": audit.isotropy_defect,
        "pass_F1":         audit.pass_F1,
        "pass_F2":         audit.pass_F2,
        "pass_F3":         audit.pass_F3,
        "pass_positivity": audit.pass_positivity,
        "pass_T6":         audit.pass_T6,
        "audit_margin":    audit.audit_margin,
    }


def _dS_to_jsonable(ds: DeltaSeffResult) -> dict:
    return {
        "delta_S_plus":      ds.delta_S_plus,
        "delta_S_minus":     ds.delta_S_minus,
        "delta_S_symmetric": ds.delta_S_symmetric,
        "delta_S_std":       ds.delta_S_std,
        "neg_ritz_total":    ds.neg_ritz_total,
        "pass_positivity":   ds.pass_positivity,
    }


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(
        description="Math46b E1-E7 C3 extractor (c_W, c_B) -- v0.6 production."
    )
    ap.add_argument("--package-root", required=True)
    ap.add_argument("--backend",      required=True)
    ap.add_argument("--eps",                type=float, default=1.0e-5)
    ap.add_argument("--shell-delta-factor", type=float, default=0.25)
    ap.add_argument("--n-samples",          type=int,   default=32)
    ap.add_argument("--lanczos-steps",      type=int,   default=48)
    ap.add_argument("--audit-tol",          type=float, default=1.0e-2)
    ap.add_argument("--seed",               type=int,   default=20260416)
    ap.add_argument("--allow-surrogate", action="store_true",
                    help="Permit the kinetic-Laplacian surrogate for M_1, M_2 "
                         "when the backend does not expose covariant_coupling_vec. "
                         "Disabled by default (fail-closed).")
    ap.add_argument("--out", default="math46_c3_audit_v0_6.json")
    args = ap.parse_args()

    pkg         = load_locked_package(args.package_root)
    backend_mod = load_backend(args.backend)
    backend     = ActualBackendAdapter(backend_mod, pkg)

    cfg = ExtractorConfig(
        eps=float(args.eps),
        shell_delta_factor=float(args.shell_delta_factor),
        n_samples=int(args.n_samples),
        lanczos_steps=int(args.lanczos_steps),
        audit_tol=float(args.audit_tol),
        seed=int(args.seed),
    )

    result = run_extractor(
        pkg=pkg,
        backend=backend,
        cfg=cfg,
        covariant_coupling_vec=None,
        allow_surrogate=bool(args.allow_surrogate),
    )

    # Render result dataclasses to JSON-serialisable form.
    # v0.7 Patch R4 -- gate the final pass on frame-singularity audit.
    # `pass_T6` reports the spectral-numeric audit only.  `pass_T6_final`
    # further requires the frame to be geometrically non-singular at every
    # lattice site; a doublet node invalidates the Householder lift and
    # silently corrupts the extracted c_W, c_B even when pass_T6 is True.
    audit_json = _audit_to_jsonable(result["audit"])
    frame_ok   = bool(result["frame"].pass_frame_nonzero)
    audit_json["pass_frame_nonzero"] = frame_ok
    audit_json["pass_T6_final"]      = bool(audit_json["pass_T6"] and frame_ok)

    payload = {
        "package_root":   str(Path(args.package_root).expanduser().resolve()),
        "backend":        str(Path(args.backend).expanduser().resolve()),
        "N":              pkg.N,
        "L":              pkg.L,
        "shell_q0":       result["shell_q0"],
        "shell_delta":    result["shell_delta"],
        "audit":          audit_json,
        "delta_S_T1":     _dS_to_jsonable(result["delta_S_T1"]),
        "delta_S_T2":     _dS_to_jsonable(result["delta_S_T2"]),
        "delta_S_Y":      _dS_to_jsonable(result["delta_S_Y"]),
        "phase_winding":  result["frame"].phase_winding,
        "frame_audit": {
            "min_norm":            result["frame"].min_norm,
            "pass_frame_nonzero":  result["frame"].pass_frame_nonzero,
        },
        "compliance":     result["compliance"],
        "config": {
            "eps":                cfg.eps,
            "shell_delta_factor": cfg.shell_delta_factor,
            "n_samples":          cfg.n_samples,
            "lanczos_steps":      cfg.lanczos_steps,
            "audit_tol":          cfg.audit_tol,
            "seed":               cfg.seed,
        },
    }

    out_path = Path(args.out).expanduser().resolve()
    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
