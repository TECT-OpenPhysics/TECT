#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
r"""
tect_newton_krylov.py  —  Trust-region Newton-Krylov solver (v2.6)
==================================================================

A rigor-oriented matrix-free Newton-Krylov solver for the TECT Brazovskii
shell free-energy functional.

v2.6 (Math66, 2026-04-22) — Class-II in-solver Hermitian projection (Path-X)
integrated into Hessian-vector product via symmetrised cII block. New parameter
`use_symmetrised_cII` (default True) enables $\widetilde{\mathcal{J}}_\mathrm{cII}
:= \frac{1}{2}(J_\mathrm{cII} + J_\mathrm{cII}^\dagger)$ per Math66 §2–§6.

v2.4 (Math56-Addendum, 2026-04-20) — theorem-anchored Phase-0 gate G0
and Class-II Newton-step floor rho_* inserted between Phase 1 and
Phase 2.  See Math56-Addendum §§A-E for the derivations; every
threshold is imported from PDE/v24_thresholds.py (single source of
truth, 22/22 unit tests in tests/test_v24_thresholds.py, SymPy audit
in Docs/supplementary/v24_threshold_sympy_check.py).

The v2.4 gate is a DEFENSIVE check: it does not modify the Newton
dynamics; it only refuses to certify Phases 2/3/4 on a converged
Psi* that has collapsed to the trivial vacuum.  The underlying
continuation must drive (mu2, lambda, gamma) into the Math56-Addendum
Theorem-1 existence window (mu2 <= r_c^meta = 2 lambda^2 / (15 gamma)
= 1.5218e-2 at locked couplings) for a meaningful G0 check; the
recommended target is mu2 = 5e-3 (Option B, Math56-Addendum Corollary 1).

Key design choices vs. the v1.0 prototype:

1. Inner Newton solve defaults to restarted GMRES (handles non-symmetric
   Jacobian from Class II numerical differentiation). Steihaug-Toint CG
   available as fallback (--krylov cg). Trust-region merit m = ½||R||²
   replaces shell_free_energy for acceptance ratio.
2. Hessian spectral audit is performed in a projected subspace with
   explicit zero-mode removal (translations, optionally global phase),
   so m*^2 is the first positive projected eigenvalue, not blindly evals[1].
3. Phase 3 is interpreted correctly: Delta F < 0 proves favorability
   against the trivial vacuum only — NOT global optimality among all
   competing branches.
4. Phase 4 is actually implemented: grid-convergence audit across
   user-specified N values with h^2 extrapolation.
5. v2.4 Phase-0 gate G0 = V(Psi*) / G0_op and Class-II floor rho_*
   refuse to enter Phase 2 on a converged Psi* that is numerically
   indistinguishable from the trivial vacuum.

Known limitations (honest):
  - Zero-mode projector is built once from Psi_0 and not rebuilt per
    Newton step. Near convergence this is accurate; at early steps the
    projected gradient norm is approximate. The trust-region mechanism
    provides robustness regardless.
  - Class II sector in the backend uses numerical hessian_vec (central
    difference), introducing ~1% asymmetry in the Jacobian (Test 6).
    GMRES (default) handles this; CG assumes symmetry.
  - Phase 3 compares only against Psi=0. Other competing branches
    (lamellar, cylindrical) are not checked.

Required backend interface
--------------------------
    residual(Psi, params)          -> ndarray, shape (3,N,N,N), complex128
    hessian_vec(Psi, v, params)    -> ndarray, shape (3,N,N,N), complex128
    shell_free_energy(Psi, params) -> float
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import warnings
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

# ── Ensure local PDE directory is importable ───────────────────────────
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import real_backend_pt_bcc_mixed_v3 as backend

try:
    from tect_solver_pt_v3 import make_mock_branch_data  # type: ignore
    _HAS_MOCK_BRANCH = True
except (ImportError, ModuleNotFoundError):
    # v2.5.7 (Math63 §2A.2 Exception-Handling Policy): only missing-module
    # conditions are swallowed here. A SyntaxError / NameError / TypeError
    # raised from inside tect_solver_pt_v3 is a programming defect and must
    # propagate rather than silently suppress mock-branch functionality.
    make_mock_branch_data = None  # type: ignore
    _HAS_MOCK_BRANCH = False

# ── v2.4 theorem-anchored gates (Math56-Addendum §§A-E) ───────────────
# The Phase-0 separatrix gate G0 and the Class-II Newton-step floor
# rho_* are imported from v24_thresholds.py, the single source of truth
# for Math56-Addendum derived numerical thresholds.  Do NOT hard-code
# G0_op, phi_+, rho_*, G2_min, or G3_rel anywhere else in this file --
# call into v24_thresholds so the SymPy audit
# (Docs/supplementary/v24_threshold_sympy_check.py) remains the
# authoritative cross-check before any code change.
from v24_thresholds import (  # type: ignore
    BrazovskiiParams,
    V24_G0_CUSHION,
    V24_MU2_TARGET_DEFAULT,
    V24_RHO_STAR_FACTOR,
    brazovskii_critical_mu2,
    v24_class2_guard,
    v24_phase0_gate,
    v24_phase0_statistic,
    v24_separatrix_thresholds,
)


# ===========================================================================
# §0  Low-level real-representation helpers
# ===========================================================================

def flatten_complex_field(Psi: np.ndarray) -> np.ndarray:
    """Convert complex field to a real vector [Re(block) | Im(block)].

    Parameters
    ----------
    Psi : ndarray, complex128, arbitrary shape

    Returns
    -------
    x : ndarray, float64, shape (2 * Psi.size,)
    """
    arr = np.asarray(Psi, dtype=np.complex128).ravel()
    return np.concatenate([arr.real, arr.imag]).astype(np.float64, copy=False)


def unflatten_complex_field(x: np.ndarray, shape: Tuple[int, ...]) -> np.ndarray:
    """Inverse of flatten_complex_field."""
    x = np.asarray(x, dtype=np.float64)
    half = x.size // 2
    return (x[:half] + 1j * x[half:]).reshape(shape)


def real_inner(a: np.ndarray, b: np.ndarray) -> float:
    """Euclidean inner product in the real representation."""
    return float(np.dot(np.asarray(a, dtype=np.float64),
                        np.asarray(b, dtype=np.float64)))


def real_norm(a: np.ndarray) -> float:
    return math.sqrt(max(real_inner(a, a), 0.0))


def field_real_norm(Psi: np.ndarray) -> float:
    return real_norm(flatten_complex_field(Psi))


def gram_schmidt_columns(vectors: Sequence[np.ndarray],
                          *, tol: float = 1e-14) -> np.ndarray:
    """Return an orthonormal row-stacked basis from a sequence of real vectors."""
    basis: List[np.ndarray] = []
    for v in vectors:
        w = np.array(v, dtype=np.float64, copy=True)
        n0 = real_norm(w)
        if n0 < tol:
            continue
        for q in basis:
            w -= real_inner(q, w) * q
        nw = real_norm(w)
        if nw < tol:
            continue
        basis.append(w / nw)
    if not basis:
        return np.zeros((0, 0), dtype=np.float64)
    return np.vstack(basis)


# ===========================================================================
# §1  BCC ansatz construction
# ===========================================================================

def _minimal_fallback_shell_seed(N: int, L: float,
                                  params: Dict[str, Any]) -> np.ndarray:
    """Fallback initial guess if make_mock_branch_data is unavailable.

    This places a single-plane-wave shell seed at q0 along [1,1,1].
    It is NOT the full corrected branch — only a symmetry-compatible
    starting point so that the solver remains executable.
    """
    q0 = float(params["q0"])
    xs = np.linspace(0.0, L, N, endpoint=False)
    X, Y, Z = np.meshgrid(xs, xs, xs, indexing="ij")
    phase = q0 * (X + Y + Z) / math.sqrt(3.0)

    Psi = np.zeros((3, N, N, N), dtype=np.complex128)
    amp = float(params.get("seed_amplitude", 0.1))
    profile = amp * np.cos(phase)
    Psi[0] = profile
    return Psi


def build_bcc_ansatz(N: int, L: float, params: Dict[str, Any]) -> np.ndarray:
    """Construct the theory-predicted BCC condensate at amplitude phi_0.

    Uses make_mock_branch_data (v3.3) which computes
    phi_0 = sqrt(-4*lambda/(15*gamma)) from the config.
    Falls back to minimal shell seed if the import is unavailable.
    """
    q0 = float(params["q0"])
    lam = float(params.get("quartic_lambda", params.get("lambda", -0.43)))
    gam = float(params.get("sextic_gamma", params.get("gamma", 1.62)))

    if _HAS_MOCK_BRANCH:
        hat_n = np.array([1.0, 1.0, 1.0], dtype=np.float64) / math.sqrt(3.0)
        Psi_bcc, Psi_corr, _, _, _ = make_mock_branch_data(
            N=N, L=L, q0=q0, hat_n=hat_n,
            quartic_lambda=lam, sextic_gamma=gam,
        )
        return np.asarray(Psi_corr, dtype=np.complex128)

    print("  [WARNING] make_mock_branch_data not available; using minimal fallback seed.")
    return _minimal_fallback_shell_seed(N, L, params)


# ===========================================================================
# §2  Zero-mode projector
# ===========================================================================

@dataclass
class ZeroModeProjector:
    """Orthogonal projector removing known symmetry zero modes.

    The basis matrix has shape (n_basis, flat_dim) with orthonormal rows.
    project(x) = x - V^T (V x) removes the component in the zero-mode subspace.
    """
    basis: np.ndarray  # shape (n_basis, flat_dim)

    @property
    def n_basis(self) -> int:
        return int(self.basis.shape[0]) if self.basis.size else 0

    @property
    def flat_dim(self) -> int:
        if self.basis.size:
            return int(self.basis.shape[1])
        return 0

    def project(self, x: np.ndarray) -> np.ndarray:
        if self.n_basis == 0:
            return np.asarray(x, dtype=np.float64)
        coeff = self.basis @ np.asarray(x, dtype=np.float64)
        return np.asarray(x, dtype=np.float64) - self.basis.T @ coeff

    def project_field(self, Psi: np.ndarray) -> np.ndarray:
        x = flatten_complex_field(Psi)
        return unflatten_complex_field(self.project(x), Psi.shape)


def _field_derivative_modes(Psi: np.ndarray, L: float) -> List[np.ndarray]:
    """Translation zero modes via central differences on the periodic grid.

    For a stationary point Psi*, the three translation modes
    dPsi/dx_i are exact null vectors of the Hessian (by translation symmetry).
    """
    N = Psi.shape[1]
    dx = float(L) / float(N)
    modes: List[np.ndarray] = []
    for axis in (1, 2, 3):
        dPsi = (np.roll(Psi, -1, axis=axis)
                - np.roll(Psi, 1, axis=axis)) / (2.0 * dx)
        modes.append(flatten_complex_field(dPsi))
    return modes


def build_zero_mode_projector(
    Psi: np.ndarray,
    params: Dict[str, Any],
    *,
    include_translations: bool = True,
    include_global_phase: bool = False,
    extra_modes: Optional[Sequence[np.ndarray]] = None,
    tol: float = 1e-14,
) -> ZeroModeProjector:
    """Build an orthogonal projector removing known symmetry zero modes.

    Parameters
    ----------
    include_translations : bool
        Remove the 3 translation modes dPsi/dx_i. Almost always True.
    include_global_phase : bool
        Remove the global U(1) phase mode i*Psi. This is NOT always
        a genuine symmetry of the TECT backend (family splitting breaks
        it), so it is disabled by default.
    """
    vectors: List[np.ndarray] = []
    L = float(params.get("L", params.get("Lx", 1.0)))

    if include_translations:
        vectors.extend(_field_derivative_modes(Psi, L=L))
    if include_global_phase:
        vectors.append(flatten_complex_field(1j * Psi))
    if extra_modes:
        vectors.extend(np.asarray(v, dtype=np.float64) for v in extra_modes)

    if not vectors:
        return ZeroModeProjector(
            basis=np.zeros((0, 2 * Psi.size), dtype=np.float64))

    basis = gram_schmidt_columns(vectors, tol=tol)
    if basis.size == 0:
        basis = np.zeros((0, 2 * Psi.size), dtype=np.float64)
    return ZeroModeProjector(basis=basis)


# ===========================================================================
# §2A  v2.6 Path-X symmetrised cII helpers (Math66 §2–§6)
# ===========================================================================
# The following functions implement the in-solver Hermitian projection
# of the Class-II (cII) block Jacobian per Math66 Path-X.

def _get_cii_block_mask(Psi_shape: Tuple[int, ...],
                         atol: float = 1e-12) -> np.ndarray:
    r"""
    [DEPRECATED in v2.6.2 — retained for v2.6.0/v2.6.1 backward compatibility.]

    v2.6.2 (Math73 Thm. math73-sym-incompat): applying any Boolean mask
    strictly finer than all-True to the v2.6.1 selective-symmetrisation
    formula breaks the Math66 v0.2 Hermiticity contract.  The correct
    replacement is the `CiiProjector` API below; see `FullProjector`
    (default, identity, bit-identical to v2.6.1) and `ChannelProjector`
    (pointwise complex-orthogonal, diagnostic-only).

    This legacy helper still returns the v2.6.1 all-True mask and is
    consulted only by the deprecation-shim path of
    `_symmetrise_jacobian_cii_v26`.
    """
    total_size = 2 * int(np.prod(Psi_shape))
    return np.ones(total_size, dtype=bool)


# ---------------------------------------------------------------------------
# v2.6.2 CiiProjector API (Math73 §5)
# ---------------------------------------------------------------------------
# Per Math73 Thm. math73-sym-incompat, the Boolean-mask-selective
# symmetrisation of v2.6.0/v2.6.1 destroys Hermiticity for any mask
# strictly finer than all-True.  The v2.6.2 resolution promotes
# P_cII(Psi) to a first-class API object and keeps the default
# (FullProjector = identity) bit-identical to v2.6.1.  ChannelProjector
# is exposed for diagnostic use only — see `channel_localisation_eta`.


class CiiProjector:
    r"""
    Abstract base for pointwise linear operators on
    $\mathcal{H} = \ell^2(\mathbb{Z}_N^3; \mathbb{C}^3)$ used to quantify
    or restrict the cII-channel subspace.

    All concrete subclasses must implement `apply(Psi, xi)` which
    returns $P(\Psi)[\xi]$ with the same `(3, N, N, N)` shape as `xi`.
    """

    def apply(self, Psi: np.ndarray, xi: np.ndarray) -> np.ndarray:
        raise NotImplementedError("CiiProjector is abstract")


class FullProjector(CiiProjector):
    r"""
    Identity projector: $P_{\mathrm{Full}}(\Psi)\,\xi = \xi$.

    This is the default for v2.6.2 `_symmetrise_jacobian_cii_v26` and
    makes the v2.6.2 symmetrised output bit-identical to v2.6.1.

    Math73 Cor. math73-M-eq-I: among diagonal Boolean masks, $M = I$ is
    the unique Hermiticity-preserving choice under the anti-Hermitian
    structure quantified in Math64.
    """

    def apply(self, Psi: np.ndarray, xi: np.ndarray) -> np.ndarray:
        return xi


class ChannelProjector(CiiProjector):
    r"""
    Pointwise complex-orthogonal cII channel projector per Math73 Def. 1:

    .. math::

       [P_{\mathrm{cII}}(\Psi)\,\xi](x)
       = \xi(x) - \frac{\langle \Psi(x), \xi(x)\rangle_{\mathbb{C}^3}}
                       {|\Psi(x)|^2 + \epsilon}\,\Psi(x).

    Properties (Math73 Lem. math73-proj-properties):
    (a) $P^2 = P$ (idempotent),
    (b) $P^\dagger = P$ (self-adjoint on $\mathcal{H}$),
    (c) $P\Psi = 0$ up to the $\epsilon$-regularisation,
    (d) $\mathrm{channel}_T(\Psi) = P(T\Psi)$ exactly (backend identity
        at real_backend_pt_bcc_mixed_v3.py:458).

    WARNING: Using this projector in the Boolean-mask-selective path of
    `_symmetrise_jacobian_cii_v26` violates Hermiticity per Math73 Thm.
    math73-sym-incompat.  This class is DIAGNOSTIC ONLY; intended for
    the channel-localisation observable `channel_localisation_eta` and
    for any future work that replaces Path-X symmetrisation with a
    variationally-correct projection.
    """

    def __init__(self, eps: float = 1e-12) -> None:
        self.eps = float(eps)

    def apply(self, Psi: np.ndarray, xi: np.ndarray) -> np.ndarray:
        Psi = np.asarray(Psi, dtype=np.complex128)
        xi = np.asarray(xi, dtype=np.complex128)
        # rho(x) = sum_a |Psi_a(x)|^2 + eps   (shape (N, N, N))
        rho = (np.conj(Psi) * Psi).sum(axis=0).real + self.eps
        # <Psi, xi>_C3(x) = sum_a conj(Psi_a) * xi_a   (shape (N, N, N))
        inner = (np.conj(Psi) * xi).sum(axis=0)
        # Broadcast across the internal index.
        coeff = (inner / rho)[np.newaxis, ...]
        return xi - coeff * Psi


class _BooleanMaskProjector(CiiProjector):
    """
    Internal adapter: wraps a legacy Boolean mask (v2.6.0/v2.6.1 API) as
    a `CiiProjector`.  Used only when a caller passes the deprecated
    `cii_mask` argument to `_symmetrise_jacobian_cii_v26`.

    Honest status: this adapter preserves the v2.6.1 formula exactly and
    therefore INHERITS the Math73 Thm. math73-sym-incompat obstruction
    for any mask strictly finer than all-True.  A DeprecationWarning is
    raised at the call site.
    """

    def __init__(self, mask: np.ndarray, field_shape: Tuple[int, ...]) -> None:
        self.mask = np.asarray(mask, dtype=bool)
        self.field_shape = tuple(field_shape)

    def apply(self, Psi: np.ndarray, xi: np.ndarray) -> np.ndarray:
        xi_flat = flatten_complex_field(xi)
        out = np.zeros_like(xi_flat)
        out[self.mask] = xi_flat[self.mask]
        return unflatten_complex_field(out, self.field_shape)


def _default_cii_projector() -> CiiProjector:
    """Factory for the default v2.6.2 projector (FullProjector).

    Returned object's `apply` is the identity; using it in
    `_symmetrise_jacobian_cii_v26` reproduces v2.6.1 output exactly.
    """
    return FullProjector()


def channel_localisation_eta(Psi: np.ndarray,
                              v: np.ndarray,
                              params: Dict[str, Any],
                              *,
                              projector: Optional[CiiProjector] = None,
                              ) -> float:
    r"""
    Compute the channel-localisation diagnostic $\eta_{\mathrm{chan}}$
    (Math73 Def. math73-eta-chan):

    .. math::

       \eta_{\mathrm{chan}}(\Psi, v) :=
         \frac{\|P_{\mathrm{cII}}(\Psi)\,(\mathcal{J} - \mathcal{J}^\dagger)\,v\|_{\mathcal{H}}}
              {\|(\mathcal{J} - \mathcal{J}^\dagger)\,v\|_{\mathcal{H}}}.

    Under the Math66 Path-X hypothesis (cII is the unique source of
    anti-Hermitian Jacobian content), Math73 Prop.
    math73-eta-prediction predicts
    $\eta_{\mathrm{chan}} = 1 + \mathcal{O}(10^{-11})$.

    A measured value below $0.99$ would falsify Path-X and mandate
    re-opening Math65 branch (S).

    Parameters
    ----------
    Psi : ndarray, complex128, shape (3, N, N, N)
        Field at which the Jacobian is evaluated.
    v : ndarray, complex128, shape (3, N, N, N)
        Random direction.  Caller should normalise $\|v\|_{\mathcal{H}} = 1$
        for clean comparison with the predicted value.
    params : dict
        Backend parameter dict.
    projector : Optional[CiiProjector]
        Defaults to `ChannelProjector()` for this diagnostic.

    Returns
    -------
    eta_chan : float
        Ratio in [0, 1].
    """
    if projector is None:
        projector = ChannelProjector()
    # Forward JVP: J v = backend.hessian_vec(Psi, v, params)  (complex128)
    Jv = backend.hessian_vec(Psi, v, params)
    # Adjoint JVP via Math66 v0.2 Path-A.
    Jdag_v = _compute_adjoint_jacobian_vec_v26(Psi, v, params)
    # Anti-Hermitian action  A v = (J - J^dag) v   (with A = J_antiH).
    A_v = np.asarray(Jv, dtype=np.complex128) - np.asarray(Jdag_v, dtype=np.complex128)
    # Projected onto channel subspace.
    PA_v = projector.apply(Psi, A_v)
    num = real_norm(flatten_complex_field(PA_v))
    den = real_norm(flatten_complex_field(A_v))
    if den <= 1e-300:
        return 0.0
    return float(num / den)


def _compute_adjoint_jacobian_vec_v26(Psi: np.ndarray,
                                       v: np.ndarray,
                                       params: Dict[str, Any]) -> np.ndarray:
    r"""
    Compute the adjoint (real-Hilbert conjugate) Jacobian-vector product
    $\mathcal{J}(\Psi)^\dagger v$ via torch.autograd on a graph-connected
    torch-native residual.

    Real-Hilbert adjoint identity (Math66 v0.2 Thm. math66v02-Hermiticity):
        $\langle \mathcal{J}^\dagger v, w \rangle_{\mathbb{R}}
         = \langle v, \mathcal{J} w \rangle_{\mathbb{R}}$,
    with $\langle a, b\rangle_{\mathbb{R}} := \operatorname{Re}\sum_i \bar a_i b_i$.
    Under PyTorch's conjugate-Wirtinger grad convention, the return of
    ``torch.autograd.grad(Re<v, F(Psi)>, Psi)`` at a leaf $\Psi_\text{torch}$
    with $\texttt{requires\_grad=True}$ equals exactly $\mathcal{J}^\dagger v$.

    v2.6.1 (Math66 v0.2 Prop. math66v02-pathA) — B2 structural fix
    -------------------------------------------------------------
    The v2.6.0 implementation routed through ``backend.residual(Psi, params)``
    which terminates with ``_to_numpy(out)``; the returned ndarray has no
    ``grad_fn`` and the subsequent ``torch.from_numpy(F_Psi)`` sealed the
    graph disconnect. ``torch.autograd.grad(loss, Psi_torch)`` then raised
    ``RuntimeError: element 0 of tensors does not require grad and does not
    have a grad_fn`` (Math68 §3 B2, per 2026-04-22 pytest / n64-audit).
    v2.6.1 replicates ``backend.residual`` inline from the six torch-native
    helpers (``_brazovskii_linear_term_t``, ``_family_term_t``,
    ``_locked_internal_penalty_t``, ``_shell_bias_term_t``,
    ``_local_nonlinear_term_t``, ``_classII_effective_term_t``) on a torch
    leaf ``Psi_torch``, preserving the autograd chain to the leaf.

    Parameters
    ----------
    Psi : ndarray, complex128, shape (3, N, N, N)
        Current field iterate.
    v : ndarray, complex128, shape (3, N, N, N)
        Direction vector.
    params : dict
        PDE parameters (routed to the torch-native backend helpers).

    Returns
    -------
    Jdagger_v : ndarray, complex128, shape (3, N, N, N)
        Adjoint Jacobian-vector product $\mathcal{J}^\dagger v$.
    """
    try:
        import torch
        _HAS_TORCH = True
    except ImportError:
        _HAS_TORCH = False

    if not _HAS_TORCH:
        raise NotImplementedError(
            "v2.6 adjoint computation requires torch. "
            "This must be run on a machine with PyTorch installed."
        )

    # ------------------------------------------------------------------
    # Math66 v0.2 Path A — graph-connected adjoint JVP (B2 structural fix)
    # ------------------------------------------------------------------
    device = backend._get_device(params)
    cdtype = backend._get_cdtype(params)

    Psi_np = np.ascontiguousarray(np.asarray(Psi, dtype=np.complex128))
    v_np = np.ascontiguousarray(np.asarray(v, dtype=np.complex128))

    # Torch leaf with autograd tracking enabled.
    Psi_torch = torch.from_numpy(Psi_np).to(dtype=cdtype, device=device)
    Psi_torch.requires_grad_(True)
    v_torch = torch.from_numpy(v_np).to(dtype=cdtype, device=device)

    # Torch-native composition of backend.residual():
    #     F(Psi) = lin + fam + lock + shell + nl + classII
    # Identical to the six terms summed inside backend.residual (line 478
    # of real_backend_pt_bcc_mixed_v3.py), but without the trailing
    # _to_numpy cast that severs the autograd chain in v2.6.0.
    F_lin = backend._brazovskii_linear_term_t(Psi_torch, params)
    F_fam = backend._family_term_t(Psi_torch, params)
    F_lock = backend._locked_internal_penalty_t(Psi_torch, params)
    F_shell = backend._shell_bias_term_t(Psi_torch, params)
    F_nl = backend._local_nonlinear_term_t(Psi_torch, params)
    F_classII = backend._classII_effective_term_t(Psi_torch, params)
    F_Psi_torch = F_lin + F_fam + F_lock + F_shell + F_nl + F_classII

    # Real-Hilbert pairing L(Psi) := Re <v, F(Psi)>_C.
    # Under PyTorch's conjugate-Wirtinger convention, dL/d(conj Psi) is
    # returned as the tensor grad, and this tensor coincides with the
    # real-Hilbert adjoint action (J^dag v). See Math66 v0.2 §2, §5.
    loss = torch.real(torch.sum(torch.conj(v_torch) * F_Psi_torch))

    # Autograd-computed J^dag v. We do NOT rely on Psi_torch.grad
    # (which is not populated by torch.autograd.grad); the tuple return
    # is authoritative.
    grad_out = torch.autograd.grad(loss, Psi_torch, create_graph=False)[0]

    # Bring result back to host numpy in complex128.
    Jdagger_v = grad_out.detach().to(device="cpu").numpy()
    return np.asarray(Jdagger_v, dtype=np.complex128)


def _symmetrise_jacobian_cii_v26(Hv: np.ndarray,
                                  Psi: np.ndarray,
                                  v_direction: np.ndarray,
                                  params: Dict[str, Any],
                                  cii_projector: Optional[CiiProjector] = None,
                                  cii_mask: Optional[np.ndarray] = None,
                                  atol: float = 1e-12) -> np.ndarray:
    r"""
    Apply the Math66 v0.2 Path-X Hermitian symmetrisation
    $\widetilde{\mathcal{J}} v := \tfrac{1}{2}(\mathcal{J} v + \mathcal{J}^\dagger v)$.

    The adjoint term $\mathcal{J}^\dagger v$ is delivered by the Math66
    v0.2 Path-A autograd recipe (Prop. math66v02-pathA) — graph-connected
    and torch-native (v2.6.1+).

    v2.6.2 API (Math73 §5)
    ----------------------
    The new first-class parameter is ``cii_projector: Optional[CiiProjector]``.

    - ``cii_projector=None`` (default) instantiates a :class:`FullProjector`,
      which reproduces v2.6.1 output bit-for-bit: every index is
      symmetrised, which is the unique Hermiticity-preserving choice
      under a diagonal projector (Math73 Cor. math73-M-eq-I).
    - ``cii_projector=FullProjector()`` is equivalent to the default.
    - ``cii_projector=ChannelProjector()`` is DIAGNOSTIC ONLY and
      violates Hermiticity under this helper's formula per Math73 Thm.
      math73-sym-incompat; use :func:`channel_localisation_eta` instead.

    v2.6.0/v2.6.1 backward compatibility
    ------------------------------------
    ``cii_mask: Optional[np.ndarray]`` is DEPRECATED but accepted for
    backward compatibility.  If a non-None ``cii_mask`` is supplied
    (whether ``cii_projector`` is None or not) a
    :class:`DeprecationWarning` is emitted, and the mask is consulted
    via an internal :class:`_BooleanMaskProjector` adapter that
    preserves the v2.6.1 semantics.  This path INHERITS the Math73 Thm.
    math73-sym-incompat obstruction: it is Hermiticity-preserving only
    for the all-True mask.

    Parameters
    ----------
    Hv : ndarray, complex128
        Forward Jacobian-vector product $\mathcal{J} v$ (from
        ``backend.hessian_vec``).
    Psi : ndarray, complex128, shape (3, N, N, N)
        Current iterate.
    v_direction : ndarray, complex128, shape (3, N, N, N)
        Direction for the JVP.
    params : dict
        PDE parameters (routed to the torch-native backend helpers for
        the adjoint JVP).
    cii_projector : Optional[CiiProjector]
        v2.6.2 API.  Defaults to :class:`FullProjector`.
    cii_mask : Optional[np.ndarray]
        DEPRECATED (v2.6.0/v2.6.1 API).  Retained for backward compat.
    atol : float
        Tolerance (unused; retained for API stability).

    Returns
    -------
    Hv_symmetrised : ndarray, complex128, shape == Hv.shape
        Symmetrised Jacobian-vector product.
    """
    # Compute adjoint JVP (Math66 v0.2 Path-A; torch required).
    Jdagger_v = _compute_adjoint_jacobian_vec_v26(Psi, v_direction, params)

    # Legacy mask path (deprecated): translate to a BooleanMaskProjector,
    # emit a DeprecationWarning, and use the v2.6.1 Boolean-selective
    # formula for backward-compatible output.
    if cii_mask is not None:
        warnings.warn(
            "Parameter `cii_mask` is deprecated as of v2.6.2 "
            "(Math73 Thm. math73-sym-incompat). "
            "Use `cii_projector: Optional[CiiProjector]` instead. "
            "A non-None mask strictly finer than all-True breaks "
            "Hermiticity; see Math73 Thm. math73-sym-incompat.",
            DeprecationWarning,
            stacklevel=2,
        )
        Hv_flat = flatten_complex_field(Hv)
        Jdagger_v_flat = flatten_complex_field(Jdagger_v)
        mask = np.asarray(cii_mask, dtype=bool)
        Hv_sym = Hv_flat.copy()
        Hv_sym[mask] = 0.5 * (Hv_flat[mask] + Jdagger_v_flat[mask])
        return unflatten_complex_field(Hv_sym, Hv.shape)

    # v2.6.2 API: default to FullProjector (identity → full-operator
    # symmetrisation, which is the unique Hermiticity-preserving
    # choice per Math73 Cor. math73-M-eq-I).
    if cii_projector is None:
        cii_projector = _default_cii_projector()

    # ------------------------------------------------------------------
    # Symmetrisation formula in projector form (Math73 §5):
    #   Hv_sym = Hv + (1/2) * P(Psi)[Jdag_v - Hv].
    # For P = I  (FullProjector):
    #     Hv_sym = Hv + (1/2)(Jdag_v - Hv) = (1/2)(Hv + Jdag_v)
    #     ≡ v2.6.1 full-True output, exactly.
    # For P = 0  (no-op projector):
    #     Hv_sym = Hv (unsymmetrised; NOT Hermitian).
    # Exposing intermediate projectors (e.g. ChannelProjector) is for
    # research / diagnostic use only — see Math73 Thm. math73-sym-incompat.
    # ------------------------------------------------------------------
    Hv_np = np.asarray(Hv, dtype=np.complex128)
    Jdag_np = np.asarray(Jdagger_v, dtype=np.complex128)
    correction = cii_projector.apply(Psi, Jdag_np - Hv_np)
    return Hv_np + 0.5 * correction


# ===========================================================================
# §3  Matrix-free projected Hessian operator
# ===========================================================================

@dataclass
class HessianOperator:
    """Wrapper providing projected Hessian-vector product P H P.

    The projection ensures that the Krylov subspace stays orthogonal
    to the known zero-mode directions.

    v2.6 enhancement: Optional Path-X in-solver Hermitian projection of
    the cII block via use_symmetrised_cII=True. See Math66 §2–§6.

    v2.6.2 enhancement (Math73 §5): `cii_projector: Optional[CiiProjector]`
    replaces `cii_block_mask: Optional[np.ndarray]`.  The legacy field is
    retained for backward compatibility and emits a DeprecationWarning
    when set to a non-None value.  The default (`None`) instantiates a
    :class:`FullProjector` whose matvec output is bit-identical to v2.6.1.
    """
    Psi: np.ndarray
    params: Dict[str, Any]
    projector: Optional[ZeroModeProjector] = None
    use_symmetrised_cII: bool = True                    # v2.6 Path-X (Math66)
    cii_projector: Optional[CiiProjector] = None        # v2.6.2 (Math73)
    cii_block_mask: Optional[np.ndarray] = None         # DEPRECATED in v2.6.2

    def __post_init__(self) -> None:
        if self.cii_block_mask is not None:
            warnings.warn(
                "`HessianOperator.cii_block_mask` is deprecated as of "
                "v2.6.2 (Math73 Thm. math73-sym-incompat). Use "
                "`cii_projector: Optional[CiiProjector]` instead. "
                "The legacy mask is still honoured for backward compat "
                "but may produce a non-Hermitian operator for any mask "
                "strictly finer than all-True.",
                DeprecationWarning,
                stacklevel=2,
            )

    @property
    def shape(self) -> Tuple[int, int]:
        dim = 2 * int(np.prod(self.Psi.shape))
        return (dim, dim)

    def matvec(self, x: np.ndarray) -> np.ndarray:
        shape = self.Psi.shape
        x = np.asarray(x, dtype=np.float64)
        if self.projector is not None:
            x = self.projector.project(x)
        v = unflatten_complex_field(x, shape)
        Hv = backend.hessian_vec(self.Psi, v, self.params)

        # v2.6 Path-X: Apply in-solver Hermitian projection on cII block
        if self.use_symmetrised_cII:
            try:
                Hv = _symmetrise_jacobian_cii_v26(
                    Hv, self.Psi, v, self.params,
                    cii_projector=self.cii_projector,
                    cii_mask=self.cii_block_mask,
                )
            except NotImplementedError as e:
                # If torch is not available, issue a warning and continue
                # with the unsymmetrised Jacobian (graceful degradation).
                print(f"[HessianOperator] v2.6 symmetrisation skipped: {e}",
                      file=sys.stderr)
                pass

        y = flatten_complex_field(Hv)
        if self.projector is not None:
            y = self.projector.project(y)
        return y


# ===========================================================================
# §4  Trust-region truncated CG (Steihaug-Toint)
# ===========================================================================

@dataclass
class TruncatedCGInfo:
    converged: bool
    iterations: int
    residual_norm: float
    hit_boundary: bool
    negative_curvature: bool
    predicted_reduction: float


def _tau_to_boundary(s: np.ndarray, p: np.ndarray, radius: float) -> float:
    """Return tau >= 0 such that ||s + tau p|| = radius.

    Since s is inside the trust region (||s|| < radius), the quadratic
    ||s + tau p||^2 = radius^2 has exactly one positive root.
    """
    a = real_inner(p, p)
    b = 2.0 * real_inner(s, p)
    c = real_inner(s, s) - radius * radius
    disc = max(b * b - 4.0 * a * c, 0.0)
    sqrt_disc = math.sqrt(disc)
    tau1 = (-b + sqrt_disc) / (2.0 * a)
    tau2 = (-b - sqrt_disc) / (2.0 * a)
    # One root is positive, one negative (since c < 0 when s is interior).
    candidates = [t for t in (tau1, tau2) if t >= 0.0]
    if not candidates:
        return 0.0
    return max(candidates)


def truncated_cg_solve(
    operator: HessianOperator,
    g: np.ndarray,
    *,
    radius: float,
    max_iter: int = 300,
    tol_rel: float = 1e-3,
    tol_abs: float = 1e-12,
    curvature_tol: float = 1e-14,
) -> Tuple[np.ndarray, TruncatedCGInfo]:
    """Approximately minimize  q(s) = g^T s + 1/2 s^T H s  with ||s|| <= radius.

    This is the Steihaug-Toint truncated CG method. Unlike plain CG, it
    correctly handles indefinite Hessians by detecting negative curvature
    directions and stepping to the trust-region boundary along them.
    """
    g = np.asarray(g, dtype=np.float64)
    dim = g.size
    s = np.zeros(dim, dtype=np.float64)
    r = g.copy()
    p = -r.copy()

    g_norm = real_norm(g)
    target = max(tol_abs, tol_rel * g_norm)

    if g_norm < target:
        info = TruncatedCGInfo(
            converged=True, iterations=0, residual_norm=g_norm,
            hit_boundary=False, negative_curvature=False,
            predicted_reduction=0.0,
        )
        return s, info

    negative_curvature = False
    hit_boundary = False
    residual_norm = g_norm

    for k in range(max_iter):
        Hp = operator.matvec(p)
        pHp = real_inner(p, Hp)

        # Negative or zero curvature → go to trust-region boundary
        if pHp <= curvature_tol:
            tau = _tau_to_boundary(s, p, radius)
            s = s + tau * p
            negative_curvature = True
            hit_boundary = True
            residual_norm = real_norm(r)
            break

        rr = real_inner(r, r)
        alpha = rr / pHp
        s_trial = s + alpha * p

        # Step exceeds trust region → truncate to boundary
        if real_norm(s_trial) >= radius:
            tau = _tau_to_boundary(s, p, radius)
            s = s + tau * p
            hit_boundary = True
            residual_norm = real_norm(r)
            break

        s = s_trial
        r_new = r + alpha * Hp
        residual_norm = real_norm(r_new)
        if residual_norm < target:
            r = r_new
            break

        beta = real_inner(r_new, r_new) / max(rr, 1e-300)
        p = -r_new + beta * p
        r = r_new
    else:
        k = max_iter

    # Compute predicted reduction: -q(s) = -(g^T s + 1/2 s^T H s)
    Hs = operator.matvec(s)
    predicted_reduction = -real_inner(g, s) - 0.5 * real_inner(s, Hs)
    predicted_reduction = max(predicted_reduction, 0.0)

    info = TruncatedCGInfo(
        converged=(residual_norm < target) and (not negative_curvature),
        iterations=k + 1 if max_iter > 0 else 0,
        residual_norm=residual_norm,
        hit_boundary=hit_boundary,
        negative_curvature=negative_curvature,
        predicted_reduction=predicted_reduction,
    )
    return s, info


# ===========================================================================
# §4b  GMRES inner solve (handles non-symmetric Jacobian)
# ===========================================================================

def gmres_trust_region_solve(
    operator: HessianOperator,
    g: np.ndarray,
    radius: float,
    max_iter: int = 300,
    tol_rel: float = 5e-4,
    restart: int = 50,
) -> Tuple[np.ndarray, TruncatedCGInfo]:
    """Restarted GMRES inner solve for J·s = -g with trust-region clipping.

    Unlike Steihaug-Toint CG, GMRES does not require operator symmetry.
    This is critical when the Jacobian J = DR has non-symmetric components
    (e.g. Class II sector with numerical Fréchet derivative).

    Trust-region enforcement: if the GMRES solution exceeds the radius,
    it is scaled to the boundary.  This is geometrically suboptimal
    compared to Steihaug-Toint boundary tracking, but the merit-based
    trust-region in newton_solve provides robust acceptance/rejection.

    Parameters
    ----------
    restart : int
        GMRES restart parameter (Krylov basis size before restart).
        Memory: O(restart × dim).  Default 50 is conservative.
    """
    from scipy.sparse.linalg import LinearOperator as SpLinOp
    from scipy.sparse.linalg import gmres as sp_gmres

    n = len(g)
    ng = real_norm(g)

    if ng < 1e-30:
        return np.zeros_like(g), TruncatedCGInfo(
            converged=True, iterations=0, residual_norm=0.0,
            hit_boundary=False, negative_curvature=False,
            predicted_reduction=0.0,
        )

    A = SpLinOp((n, n), matvec=operator.matvec, dtype=np.float64)

    # Track iterations via callback
    _iter_count = [0]

    def _callback(pr_norm):
        _iter_count[0] += 1

    # scipy ≥ 1.12 renamed tol → rtol; detect at runtime
    import inspect
    _gmres_sig = inspect.signature(sp_gmres)
    _tol_key = 'rtol' if 'rtol' in _gmres_sig.parameters else 'tol'

    # v2.6.6 (2026-04-26) -- map cumulative-iter semantics to SciPy's
    # restart-cycle semantics: SciPy GMRES treats `maxiter` as the number
    # of restart cycles, so effective cumulative inner iter is
    # maxiter * restart. The CLI option --tcg-max in continuation_mu2_v25
    # carries cumulative-iter semantics (matches the callback-counted
    # tCG reported in the Newton log), so divide by restart here. Prior
    # to v2.6.6 the wrapper passed `maxiter=max_iter` directly, producing
    # an effective cap of max_iter * restart (e.g. core default 300 * 50
    # = 15000 cumulative iter visible in the v2.6.4 logs).
    _restart = min(restart, n)
    _scipy_maxiter = max(1, max_iter // max(1, _restart))
    s, exit_code = sp_gmres(
        A, -g.astype(np.float64),
        **{_tol_key: tol_rel}, atol=0.0,
        maxiter=_scipy_maxiter,
        restart=_restart,
        callback=_callback, callback_type='pr_norm',
    )
    s = np.asarray(s, dtype=np.float64)

    # ── Trust-region clipping ──
    norm_s = real_norm(s)
    hit_boundary = (norm_s > radius)
    if hit_boundary:
        s = (radius / norm_s) * s

    residual_norm = real_norm(operator.matvec(s) + g)

    info = TruncatedCGInfo(
        converged=(exit_code == 0),
        iterations=_iter_count[0],
        residual_norm=residual_norm,
        hit_boundary=hit_boundary,
        negative_curvature=False,      # not applicable for GMRES
        predicted_reduction=0.0,       # computed in newton_solve (v2.2+)
    )
    return s, info


# ===========================================================================
# §5  Trust-region Newton iteration (Phase 1 — Existence)
# ===========================================================================

@dataclass
class NewtonStepRecord:
    step: int
    F: float
    merit: float          # v2.2: m = ½||R_proj||²  (trust-region merit)
    grad_norm: float
    trust_radius: float
    model_pred_reduction: float   # predicted reduction in merit
    actual_reduction: float       # actual reduction in merit
    rho: float
    accepted: bool
    tCG_iterations: int
    tCG_residual: float
    negative_curvature: bool
    line_search_alpha: float
    time_s: float


def newton_solve(
    Psi0: np.ndarray,
    params: Dict[str, Any],
    *,
    max_newton: int = 50,
    tol_newton: float = 1e-10,
    trust_radius_init: Optional[float] = None,
    trust_radius_max: Optional[float] = None,
    krylov_method: str = 'gmres',
    tcg_max_iter: int = 300,
    tcg_tol_rel: float = 5e-4,
    gmres_restart: int = 50,
    armijo_c1: float = 1e-4,
    max_backtrack: int = 12,
    eisenstat_walker: bool = True,
    ew_eta_max: float = 0.9,
    ew_eta_min: float = 0.01,
    ew_gamma: float = 0.9,
    ew_alpha: float = 2.0,
    include_translation_zero_modes: bool = True,
    include_global_phase_zero_mode: bool = False,
    use_symmetrised_cII: bool = True,  # v2.6 Path-X (Math66)
    cii_block_mask: Optional[np.ndarray] = None,  # v2.6 optional cII block mask
    checkpoint_callback: Optional[Callable[[np.ndarray, int, Dict[str, Any]], None]] = None,
    verbose: bool = True,
) -> Tuple[np.ndarray, List[Dict[str, Any]], ZeroModeProjector]:
    r"""Trust-region Newton-Krylov solve for residual(Psi) = 0.

    Convergence criterion: projected ||R_proj|| / sqrt(dof_eff) < tol_newton.

    v2.6 changes (Math66, 2026-04-22)
    -----------
    - In-solver Hermitian projection on Class-II (cII) block via Path-X:
      $\widetilde{\mathcal{J}}_\mathrm{cII} := \frac{1}{2}(J_\mathrm{cII} + J_\mathrm{cII}^\dagger)$.
    - New parameter use_symmetrised_cII (default True) enables/disables Path-X.
    - Optional cii_block_mask allows fine-grained control (default None = full domain).
    - Graceful degradation: if torch unavailable, continues with unsymmetrised J.

    v2.3 changes
    -------------
    - Eisenstat-Walker Choice 2 forcing terms for adaptive inner-solve
      tolerance.  Prevents GMRES iteration-count explosion near convergence.

    v2.2 changes
    -------------
    - Merit function m = ½||R_proj||² replaces shell_free_energy for the
      trust-region ratio and Armijo line search.
    - GMRES inner solve (default) replaces CG because the Jacobian J=DR
      is non-symmetric (~1% asymmetry from Class II numerical Fréchet
      derivative).  CG is still available via krylov_method='cg'.

    Parameters
    ----------
    krylov_method : {'gmres', 'cg'}
        Inner Krylov solver.  'gmres' (default) handles non-symmetric J.
        'cg' (Steihaug-Toint) requires approximately symmetric J.
    gmres_restart : int
        GMRES restart parameter (ignored if krylov_method='cg').
    eisenstat_walker : bool
        If True (default), use Eisenstat-Walker Choice 2 to adapt the
        inner Krylov tolerance each Newton step.  If False, use fixed
        ``tcg_tol_rel`` at every step.
    ew_eta_max : float
        Maximum forcing term (loose tolerance for early steps).
    ew_eta_min : float
        Minimum forcing term (prevents over-solving near convergence).
    ew_gamma, ew_alpha : float
        EW Choice 2 parameters: eta_k = gamma * (||R_k||/||R_{k-1}||)^alpha.
    use_symmetrised_cII : bool
        If True (default, v2.6), apply Path-X in-solver Hermitian projection.
        See Math66 §2–§6. Requires torch; gracefully degrades if unavailable.
    cii_block_mask : ndarray, optional
        Boolean mask (shape = flat_dim,) selecting cII block indices.
        If None (default), apply symmetrisation to entire domain (skeleton).

    Returns
    -------
    Psi_star : converged (or best) field
    history  : per-step diagnostics as list of dicts
    projector : the zero-mode projector used
    """
    # -----------------------------------------------------------------
    # Task #112 (Math68 §3 Blocker B1 repair) — solver-name API shim.
    #
    # `continuation_mu2_v25.select_krylov_solver()` returns names from the
    # Math63 v1.7 / Math64 v1.1 routing vocabulary {"pcg", "minres", "fgmres"};
    # this function historically accepted only {"gmres", "cg"}.  Without the
    # shim, the Phase D live call raised `ValueError` before any Krylov work
    # was dispatched.  Per Prop. `math68-B1-fix` the temporary canonicalisation
    # map is
    #     pcg     -> cg      (SPD path; CG IS the preconditioned branch here)
    #     fgmres  -> gmres   (non-flexible GMRES is the available asymmetric
    #                          solver; flexible-GMRES promotion is tracked in
    #                          Task #112 permanent-fix sub-item)
    #     minres  -> gmres   (temporary; native MINRES dispatch is the
    #                          permanent fix, tracked in Task #112)
    # The shim emits a stderr warning the first time a non-native name is
    # received so that the downstream solver choice remains auditable.
    _KRYLOV_ALIAS_MAP = {'pcg': 'cg', 'fgmres': 'gmres', 'minres': 'gmres'}
    _KRYLOV_NATIVE = ('gmres', 'cg')
    _krylov_requested = krylov_method
    if krylov_method in _KRYLOV_ALIAS_MAP:
        krylov_method = _KRYLOV_ALIAS_MAP[krylov_method]
        import sys as _sys
        _sys.stderr.write(
            f"[tect_newton_krylov v2.6 B1-shim] krylov_method="
            f"{_krylov_requested!r} canonicalised to {krylov_method!r} "
            f"(Math68 §3 Prop. math68-B1-fix; native MINRES is Task #112)\n"
        )
    if krylov_method not in _KRYLOV_NATIVE:
        raise ValueError(
            f"krylov_method must be one of "
            f"{_KRYLOV_NATIVE + tuple(_KRYLOV_ALIAS_MAP.keys())!r}, "
            f"got {_krylov_requested!r}"
        )
    Psi = np.array(Psi0, dtype=np.complex128, copy=True)
    flat_dim = 2 * int(np.prod(Psi.shape))

    projector = build_zero_mode_projector(
        Psi, params,
        include_translations=include_translation_zero_modes,
        include_global_phase=include_global_phase_zero_mode,
    )
    dof_eff = float(max(flat_dim - projector.n_basis, 1))

    if trust_radius_init is None:
        trust_radius = max(1e-3, 0.25 * field_real_norm(Psi))
    else:
        trust_radius = float(trust_radius_init)
    if trust_radius_max is None:
        trust_radius_max = max(1.0, 10.0 * trust_radius)
    else:
        trust_radius_max = float(trust_radius_max)

    history: List[Dict[str, Any]] = []

    if verbose:
        print("=" * 72)
        print("  TECT trust-region Newton-Krylov solver -- Phase 1 (Existence)")
        print("=" * 72)
        print(f"  grid = {Psi.shape[1]}^3")
        print(f"  flat_dim = {flat_dim}")
        print(f"  projector zero-modes = {projector.n_basis}")
        print(f"  effective dof = {dof_eff:.0f}")
        print(f"  tol_newton = {tol_newton:.1e}")
        print(f"  krylov = {krylov_method.upper()}"
              f"  (restart={gmres_restart})" * (krylov_method == 'gmres'))
        print(f"  merit = (1/2)||R_proj||^2  (v2.2)")
        if use_symmetrised_cII:
            print(f"  v2.6 Path-X: cII Hermitian symmetrisation ON (Math66)")
        if eisenstat_walker:
            print(f"  Eisenstat-Walker: ON  "
                  f"(gamma={ew_gamma}, alpha={ew_alpha}, "
                  f"eta in [{ew_eta_min}, {ew_eta_max}])")
        else:
            print(f"  Eisenstat-Walker: OFF  (fixed tol_rel={tcg_tol_rel:.1e})")
        print()

    converged = False

    # ── Eisenstat-Walker state (v2.3) ──
    prev_grad_norm: Optional[float] = None
    prev_eta: float = ew_eta_max
    current_eta: float = ew_eta_max if eisenstat_walker else tcg_tol_rel

    # ── v2.6.6 (2026-04-26): per-step checkpoint callback ──
    # If the caller supplies `checkpoint_callback`, it is invoked after
    # every Newton step's history.append, with arguments (Psi, step,
    # step_record_dict). The callback is the persistence hook used by
    # continuation_mu2_v25.run_one_point_v25 to save Psi to disk between
    # steps so that a Ctrl-C produces a recoverable warm-start state.
    # Caller-side exception handling (KeyboardInterrupt, MemoryError) is
    # responsible for the final clean-up; this hook only provides the
    # incremental snapshots.

    for step in range(max_newton):
        t0 = time.perf_counter()

        F_old = float(backend.shell_free_energy(Psi, params))
        R = np.asarray(backend.residual(Psi, params), dtype=np.complex128)
        g = flatten_complex_field(R)
        g_proj = projector.project(g)
        grad_norm = real_norm(g_proj) / math.sqrt(dof_eff)
        m_old = 0.5 * real_inner(g_proj, g_proj)

        if verbose:
            print(
                f"  Newton {step:3d} | ||grad||/√dof = {grad_norm:.6e}"
                f" | merit = {m_old:+.10e} | F = {F_old:+.10e}"
                f" | Delta = {trust_radius:.3e}"
            )

        # ── Math82-AddG3 vacuum-floor guard (Task #116, 2026-04-24) ──
        # If ||F||/sqrt(N) is at the FP roundoff floor, the iterate is
        # the numerical trivial vacuum: declare convergence-as-vacuum
        # rather than chasing zero past where it can be measured.
        # Threshold derivation: ||F|| ≥ c_floor * sqrt(N) * eps_mach for any
        # genuine non-trivial Brazovskii equilibrium (Math82-AddG3 §3
        # bound). c_floor=100 gives 2-order separation from the present
        # Phase-Z merit floor of ~1e-10. See TECT-Math82-Addendum-G3.
        F_norm_total = real_norm(g_proj)
        _c_floor = 100.0
        _eps_mach64 = 1.1e-16
        _vac_floor = _c_floor * math.sqrt(dof_eff) * _eps_mach64
        if F_norm_total < _vac_floor:
            elapsed = time.perf_counter() - t0
            history.append(asdict(NewtonStepRecord(
                step=step, F=F_old, merit=m_old,
                grad_norm=grad_norm,
                trust_radius=trust_radius,
                model_pred_reduction=0.0, actual_reduction=0.0,
                rho=1.0, accepted=True,
                tCG_iterations=0, tCG_residual=0.0,
                negative_curvature=False, line_search_alpha=0.0,
                time_s=elapsed,
            )))
            converged = True
            if verbose:
                print(f"  >>> Converged at step {step} "
                      f"(numerical_vacuum guard: ||F_proj||={F_norm_total:.3e} "
                      f"< vac_floor={_vac_floor:.3e})")
            break

        # ── Convergence check (sole criterion: projected gradient norm) ──
        if grad_norm < tol_newton:
            elapsed = time.perf_counter() - t0
            history.append(asdict(NewtonStepRecord(
                step=step, F=F_old, merit=m_old,
                grad_norm=grad_norm,
                trust_radius=trust_radius,
                model_pred_reduction=0.0, actual_reduction=0.0,
                rho=1.0, accepted=True,
                tCG_iterations=0, tCG_residual=0.0,
                negative_curvature=False, line_search_alpha=0.0,
                time_s=elapsed,
            )))
            converged = True
            if verbose:
                print(f"\n  >>> Converged at step {step}.")
            break

        # ── Eisenstat-Walker forcing term (v2.3) ──
        if eisenstat_walker and prev_grad_norm is not None and prev_grad_norm > 0:
            ratio = grad_norm / prev_grad_norm
            eta_raw = ew_gamma * ratio ** ew_alpha
            # Safeguard: prevent too-rapid decrease (EW Choice 2)
            eta_safeguard = ew_gamma * prev_eta ** ew_alpha
            current_eta = max(eta_raw, eta_safeguard)
            current_eta = max(ew_eta_min, min(ew_eta_max, current_eta))
        elif eisenstat_walker:
            current_eta = ew_eta_max  # first step: loose tolerance
        # else: current_eta remains tcg_tol_rel (fixed)

        # ── Inner Krylov solve (CG or GMRES) ──
        H = HessianOperator(Psi=Psi, params=params, projector=projector,
                           use_symmetrised_cII=use_symmetrised_cII,
                           cii_block_mask=cii_block_mask)
        if krylov_method == 'cg':
            step_vec, info = truncated_cg_solve(
                H, g_proj, radius=trust_radius,
                max_iter=tcg_max_iter, tol_rel=current_eta,
            )
        else:  # gmres
            step_vec, info = gmres_trust_region_solve(
                H, g_proj, radius=trust_radius,
                max_iter=tcg_max_iter, tol_rel=current_eta,
                restart=gmres_restart,
            )

        # ── Compute Hessian·step for merit-function trust-region ──
        #    v2.2: merit m = ½||R_proj||² replaces shell_free_energy
        #    because backend_consistency_audit proved R ≠ ∇F.
        #    The (R, H=J) pair IS self-consistent (Test 2: ratio=1.0).
        Hs = H.matvec(step_vec)
        directional_m = real_inner(g_proj, Hs)   # dm/dα at α=0

        # ── Descent check on merit: require dm/dα < 0 ──
        if directional_m >= 0.0:
            ng = real_norm(g_proj)
            if ng > 0.0:
                step_vec = -(trust_radius / ng) * g_proj
            else:
                step_vec = np.zeros_like(g_proj)
            info.negative_curvature = True
            info.hit_boundary = True
            Hs = H.matvec(step_vec)
            directional_m = real_inner(g_proj, Hs)

        Hs_norm_sq = real_inner(Hs, Hs)
        dPsi = unflatten_complex_field(step_vec, Psi.shape)

        # ── Backtracking line search (Armijo on merit m = ½||R_proj||²) ──
        alpha = 1.0
        m_trial = m_old
        accepted = False
        for _ in range(max_backtrack):
            Psi_trial = Psi + alpha * dPsi
            R_trial = np.asarray(backend.residual(Psi_trial, params),
                                 dtype=np.complex128)
            g_trial_proj = projector.project(
                flatten_complex_field(R_trial))
            m_trial = 0.5 * real_inner(g_trial_proj, g_trial_proj)
            if m_trial <= m_old + armijo_c1 * alpha * directional_m:
                accepted = True
                break
            alpha *= 0.5

        # ── Last fallback: small steepest-descent step ──
        if not accepted:
            ng = real_norm(g_proj)
            if ng > 0.0:
                fallback_radius = min(trust_radius,
                                      max(1e-12, 0.1 * trust_radius))
                fallback = -(fallback_radius / ng) * g_proj
                dPsi = unflatten_complex_field(fallback, Psi.shape)
                step_vec = fallback
                Hs = H.matvec(step_vec)
                directional_m = real_inner(g_proj, Hs)
                Hs_norm_sq = real_inner(Hs, Hs)
                alpha = 1.0
                for _ in range(max_backtrack):
                    Psi_trial = Psi + alpha * dPsi
                    R_trial = np.asarray(
                        backend.residual(Psi_trial, params),
                        dtype=np.complex128)
                    g_trial_proj = projector.project(
                        flatten_complex_field(R_trial))
                    m_trial = 0.5 * real_inner(
                        g_trial_proj, g_trial_proj)
                    if m_trial <= (m_old
                                   + armijo_c1 * alpha * directional_m):
                        accepted = True
                        break
                    alpha *= 0.5

        # ── Merit-based predicted reduction ──
        #    From linear model R(Ψ+αs) ≈ R + α J s:
        #    m_model(α) = ½||g + α Hs||²
        #    Δm_pred = m_old - m_model = -α Re<g,Hs> - ½ α² ||Hs||²
        predicted = max(-alpha * directional_m
                        - 0.5 * alpha ** 2 * Hs_norm_sq, 0.0)

        # ── Trust-region radius update (merit-based) ──
        if accepted:
            Psi_new = Psi + alpha * dPsi
            actual_reduction = m_old - m_trial
            rho = actual_reduction / predicted if predicted > 0.0 else 0.0

            if rho < 0.25:
                trust_radius = max(1e-12, 0.25 * trust_radius)
            elif rho > 0.75 and info.hit_boundary:
                trust_radius = min(trust_radius_max, 2.0 * trust_radius)

            Psi = Psi_new
        else:
            actual_reduction = 0.0
            rho = -1.0e30  # finite sentinel (avoids JSON serialization crash)
            trust_radius = max(1e-12, 0.25 * trust_radius)

        elapsed = time.perf_counter() - t0
        history.append(asdict(NewtonStepRecord(
            step=step, F=F_old, merit=m_old,
            grad_norm=grad_norm,
            trust_radius=trust_radius,
            model_pred_reduction=predicted,
            actual_reduction=actual_reduction,
            rho=rho, accepted=accepted,
            tCG_iterations=info.iterations,
            tCG_residual=info.residual_norm,
            negative_curvature=info.negative_curvature,
            line_search_alpha=alpha,
            time_s=elapsed,
        )))

        # ── v2.6.6 per-step checkpoint hook ──
        # Persist Psi *immediately* after the new step is committed, so
        # a Ctrl-C between Newton iterations leaves disk in a consistent
        # warm-start state. Callback errors are swallowed (best-effort
        # checkpointing must never crash the Newton loop itself).
        if checkpoint_callback is not None:
            try:
                checkpoint_callback(Psi, step, history[-1])
            except (OSError, IOError, RuntimeError, ValueError) as _ckpt_err:
                if verbose:
                    print(
                        f"      [checkpoint WARNING] {type(_ckpt_err).__name__}: {_ckpt_err}",
                        file=sys.stderr,
                    )

        # ── Update Eisenstat-Walker state for next step ──
        prev_grad_norm = grad_norm
        prev_eta = current_eta

        if verbose:
            tag = "ACCEPT" if accepted else "REJECT"
            eta_str = f" | η = {current_eta:.3e}" if eisenstat_walker else ""
            print(
                f"      -> {tag} | pred_m = {predicted:.3e}"
                f" | actual_m = {actual_reduction:.3e} | ρ = {rho:.3f}"
                f" | α = {alpha:.2e} | tCG = {info.iterations}{eta_str}"
            )

    if not converged and verbose:
        print(f"\n  >>> Did not converge within {max_newton} Newton steps.")

    return Psi, history, projector


# ===========================================================================
# §6  Lanczos on the projected Hessian (Phase 2 — Stability)
# ===========================================================================

@dataclass
class Phase2Result:
    eigenvalues: List[float]
    n_negative: int
    n_near_zero: int
    lambda_min: float
    lambda_gap: float
    m_star_sq: float
    stable: bool


def lanczos_hessian(
    Psi: np.ndarray,
    params: Dict[str, Any],
    *,
    projector: Optional[ZeroModeProjector] = None,
    n_eigs: int = 20,
    krylov_dim: Optional[int] = None,
    max_iter: int = 300,
    rng_seed: int = 12345,
    reorthogonalize_every: int = 5,
    verbose: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """Projected Lanczos iteration for the Hessian spectrum at Psi.

    The Lanczos start vector is seeded deterministically (rng_seed)
    for run-to-run reproducibility.

    Note (v2.6): lanczos_hessian currently uses default HessianOperator
    (unsymmetrised Jacobian). Phase 2 stability analysis does not yet
    use the Path-X cII symmetrisation. This is acceptable because Phase 2
    only audits the spectrum; the symmetrised Jacobian is used only in
    Phase 1 Newton-Krylov iteration (newton_solve).

    Returns
    -------
    evals : ndarray, ascending Ritz eigenvalues of the projected Hessian
    ritz_vecs : ndarray, corresponding Ritz vectors (flattened)
    """
    # v2.6: instantiate with default (unsymmetrised) HessianOperator
    H = HessianOperator(Psi=Psi, params=params, projector=projector,
                       use_symmetrised_cII=False)
    flat_dim = H.shape[0]
    if krylov_dim is None:
        krylov_dim = min(max_iter, max(3 * n_eigs, n_eigs + 8), flat_dim)
    else:
        krylov_dim = min(int(krylov_dim), max_iter, flat_dim)

    rng = np.random.default_rng(rng_seed)
    v = rng.standard_normal(flat_dim)
    if projector is not None:
        v = projector.project(v)
    nv = real_norm(v)
    if nv < 1e-14:
        raise RuntimeError(
            "Projected random start vector vanished; "
            "enlarge subspace or revise zero-mode basis.")
    v /= nv

    V = np.zeros((krylov_dim, flat_dim), dtype=np.float64)
    alpha_arr = np.zeros(krylov_dim, dtype=np.float64)
    beta_arr = np.zeros(krylov_dim, dtype=np.float64)

    V[0] = v
    w = H.matvec(v)
    alpha_arr[0] = real_inner(v, w)
    w = w - alpha_arr[0] * v
    if projector is not None:
        w = projector.project(w)

    k_eff = krylov_dim
    for j in range(1, krylov_dim):
        beta_j = real_norm(w)
        if beta_j < 1e-14:
            k_eff = j
            break
        beta_arr[j] = beta_j
        v_prev = V[j - 1]
        v = w / beta_j
        V[j] = v

        w = H.matvec(v) - beta_j * v_prev
        alpha_arr[j] = real_inner(v, w)
        w = w - alpha_arr[j] * v
        if projector is not None:
            w = projector.project(w)

        # Partial reorthogonalisation
        if reorthogonalize_every > 0 and (j % reorthogonalize_every == 0):
            for jj in range(j + 1):
                w -= real_inner(V[jj], w) * V[jj]

    T = (np.diag(alpha_arr[:k_eff])
         + np.diag(beta_arr[1:k_eff], 1)
         + np.diag(beta_arr[1:k_eff], -1))
    evals, evecs_T = np.linalg.eigh(T)
    n_ret = min(n_eigs, k_eff)
    ritz_vecs = evecs_T[:, :n_ret].T @ V[:k_eff]

    if verbose:
        print("\n" + "=" * 72)
        print("  TECT Lanczos -- Phase 2 (Projected Hessian spectrum)")
        print("=" * 72)
        print(f"  Krylov dimension = {k_eff}")
        print(f"  returning lowest {n_ret} Ritz values")
        for i in range(n_ret):
            print(f"    lambda_{i} = {evals[i]:+.10e}")

    return evals[:n_ret], ritz_vecs[:n_ret]


def analyze_projected_spectrum(
    evals: np.ndarray,
    *,
    zero_tol: float = 1e-8,
    neg_tol: float = 1e-8,
) -> Phase2Result:
    """Interpret the projected Hessian spectrum.

    m*^2 is the first projected eigenvalue strictly above zero_tol.
    This is NOT evals[1] — the projector already removed translation modes,
    so there should be no near-zero eigenvalues in the projected spectrum.
    """
    evals = np.asarray(evals, dtype=np.float64)
    n_negative = int(np.sum(evals < -neg_tol))
    n_near_zero = int(np.sum(np.abs(evals) <= zero_tol))
    lambda_min = float(evals[0]) if evals.size else float("nan")

    positive = evals[evals > zero_tol]
    if positive.size > 0:
        lambda_gap = float(positive[0])
        m_star_sq = float(positive[0])
    else:
        lambda_gap = float("nan")
        m_star_sq = float("nan")

    stable = n_negative == 0 and np.isfinite(m_star_sq)
    return Phase2Result(
        eigenvalues=evals.tolist(),
        n_negative=n_negative,
        n_near_zero=n_near_zero,
        lambda_min=lambda_min,
        lambda_gap=lambda_gap,
        m_star_sq=m_star_sq,
        stable=stable,
    )


# ===========================================================================
# §7  Energetic favorability against the trivial vacuum (Phase 3)
# ===========================================================================

@dataclass
class Phase3Result:
    F_condensate: float
    F_vacuum: float
    delta_F: float
    favorable_vs_vacuum: bool


def compute_energy_difference(
    Psi_star: np.ndarray,
    params: Dict[str, Any],
    *,
    verbose: bool = True,
) -> Phase3Result:
    """Compute Delta F = F(Psi*) - F(0).

    Interpretation (exact scope, no more):
    Delta F < 0 proves that the stationary condensate Psi* is energetically
    favored over the trivial vacuum Psi = 0. It does NOT prove global
    optimality among all competing nontrivial branches (lamellar, cylindrical,
    etc.). Such branch comparison would require separate Phase 1 runs on
    each candidate.
    """
    F_condensate = float(backend.shell_free_energy(Psi_star, params))
    Psi_zero = np.zeros_like(Psi_star)
    F_vacuum = float(backend.shell_free_energy(Psi_zero, params))
    delta_F = F_condensate - F_vacuum

    result = Phase3Result(
        F_condensate=F_condensate,
        F_vacuum=F_vacuum,
        delta_F=delta_F,
        favorable_vs_vacuum=(delta_F < 0.0),
    )

    if verbose:
        print("\n" + "=" * 72)
        print("  TECT Energy comparison -- Phase 3 (Vacuum favorability)")
        print("=" * 72)
        print(f"  F(Psi*) = {F_condensate:+.10e}")
        print(f"  F(0)    = {F_vacuum:+.10e}")
        print(f"  Delta F = {delta_F:+.10e}")
        if delta_F < 0.0:
            print("  >>> Condensate is favorable versus the trivial vacuum.")
        else:
            print("  >>> Condensate is NOT favorable versus the trivial vacuum.")

    return result


# ===========================================================================
# §8  Continuum / grid-convergence audit (Phase 4)
# ===========================================================================

@dataclass
class Phase4Result:
    Ns: List[int]
    hs: List[float]
    phase1_converged_flags: List[bool]
    m_star_sq_values: List[float]
    delta_F_values: List[float]
    stable_flags: List[bool]
    favorable_vs_vacuum_flags: List[bool]
    continuum_intercept_m_star_sq: float
    fit_slope: float
    max_relative_fit_residual: float
    passed: bool


def run_continuum_audit(
    Ns: Sequence[int],
    L: float,
    params: Dict[str, Any],
    *,
    outdir: Optional[str] = None,
    tol_newton: float = 1e-10,
    max_newton: int = 50,
    krylov_method: str = 'gmres',
    gmres_restart: int = 50,
    eisenstat_walker: bool = True,
    ew_eta_max: float = 0.9,
    ew_eta_min: float = 0.01,
    verbose: bool = True,
) -> Phase4Result:
    """Run Phases 1-3 across several grid sizes and fit m*^2(h) = m0 + c h^2.

    This is the continuum-limit extrapolation. If the fit intercept m0 > 0
    and all individual runs pass Phases 1-3, the continuum limit is declared
    consistent.
    """
    if len(Ns) < 2:
        raise ValueError("Phase 4 requires at least two grid sizes.")

    hs: List[float] = []
    phase1_flags: List[bool] = []
    mvals: List[float] = []
    deltas: List[float] = []
    stable_flags: List[bool] = []
    favorable_flags: List[bool] = []

    if verbose:
        print("\n" + "=" * 72)
        print("  Phase 4 (Continuum / grid-convergence audit)")
        print("=" * 72)
        print("  Running nested Phases 1-3 across N = "
              + ", ".join(str(n) for n in Ns))

    for N in Ns:
        sub_outdir = None
        if outdir is not None:
            sub_outdir = os.path.join(outdir, f"continuum_N{N}")
        res = run_proof_pipeline(
            N=N, L=L, params=dict(params),
            phases="123",
            outdir=sub_outdir,
            verbose=verbose,
            tol_newton=tol_newton,
            max_newton=max_newton,
            krylov_method=krylov_method,
            gmres_restart=gmres_restart,
            eisenstat_walker=eisenstat_walker,
            ew_eta_max=ew_eta_max,
            ew_eta_min=ew_eta_min,
        )
        h = float(L) / float(N)
        hs.append(h)
        p1 = res.get("phase1", {})
        p2 = res.get("phase2", {})
        p3 = res.get("phase3", {})
        phase1_flags.append(bool(p1.get("converged", False)))
        mvals.append(float(p2.get("m_star_sq", float("nan"))))
        deltas.append(float(p3.get("delta_F", float("nan"))))
        stable_flags.append(bool(p2.get("stable", False)))
        favorable_flags.append(bool(p3.get("favorable_vs_vacuum", False)))

    # Linear fit: m*^2(h^2) = m0 + slope * h^2
    hs_arr = np.asarray(hs, dtype=np.float64)
    x = hs_arr * hs_arr
    y = np.asarray(mvals, dtype=np.float64)
    mask = np.isfinite(y)
    if np.sum(mask) < 2:
        m0, slope, max_rel_resid = float("nan"), float("nan"), float("nan")
        passed = False
    else:
        coeff = np.polyfit(x[mask], y[mask], deg=1)
        slope = float(coeff[0])
        m0 = float(coeff[1])
        y_fit = slope * x[mask] + m0
        denom = np.maximum(np.abs(y[mask]), 1e-14)
        max_rel_resid = float(np.max(np.abs((y[mask] - y_fit) / denom)))
        passed = (
            all(phase1_flags)
            and all(stable_flags)
            and all(favorable_flags)
            and math.isfinite(m0)
            and (m0 > 0.0)
            and (max_rel_resid < 0.2)
        )

    result = Phase4Result(
        Ns=list(map(int, Ns)), hs=hs,
        phase1_converged_flags=phase1_flags,
        m_star_sq_values=mvals, delta_F_values=deltas,
        stable_flags=stable_flags,
        favorable_vs_vacuum_flags=favorable_flags,
        continuum_intercept_m_star_sq=m0,
        fit_slope=slope,
        max_relative_fit_residual=max_rel_resid,
        passed=passed,
    )

    if verbose:
        print("\n  Continuum audit summary")
        for N_i, h, p1c, m2, dF, st, fav in zip(
                Ns, hs, phase1_flags, mvals, deltas,
                stable_flags, favorable_flags):
            print(
                f"    N={N_i:4d} | h={h:.4e} | P1={p1c}"
                f" | m*^2={m2:+.8e}"
                f" | DeltaF={dF:+.8e} | stable={st} | fav={fav}"
            )
        print(f"  fitted m*^2(h->0) = {m0:+.8e}")
        print(f"  fit slope         = {slope:+.8e}")
        print(f"  max rel residual  = {max_rel_resid:.3e}")
        print(f"  continuum pass    = {passed}")

    return result


# ===========================================================================
# §9  Full proof pipeline
# ===========================================================================

def sanitize_for_json(obj: Any) -> Any:
    """Recursively sanitize a nested dict/list for strict JSON.

    Python's json.dump default hook is NOT called for float NaN/Inf
    because float is a native JSON type.  This function walks the
    entire tree and replaces non-finite floats with string sentinels.
    """
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())
    if isinstance(obj, (np.floating, float)):
        x = float(obj)
        if math.isnan(x):
            return "NaN"
        if math.isinf(x):
            return "Inf" if x > 0 else "-Inf"
        return x
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    return obj


def _run_v24_phase0_gate(
    Psi_star: np.ndarray,
    params: Dict[str, Any],
    verbose: bool = True,
) -> Dict[str, Any]:
    """v2.4 Phase-0 gate + Class-II floor (Math56-Addendum §§A-E).

    Operates on the CONVERGED Psi* from Phase 1.  Returns a dict with
    keys ``passed`` (bool), ``V`` (float, normalised amplitude^2 statistic),
    ``G0_op`` (float, operating threshold), ``rho_star`` (float, floor),
    ``skipped`` (bool, True iff mu2 lies above r_c^meta -- i.e. outside
    the Math56-Addendum existence window), ``reason`` (str), and the
    derived ``BrazovskiiParams`` for downstream reporting.

    The gate NEVER raises on a physical failure; it reports ``passed =
    False`` so the caller can set ``downstream_blocked`` cleanly.  The
    only exception is the Class-II guard: if ``||Psi*||_RMS^2 < rho_*``
    the backend Hessian_vec would suffer a numerical 1/rho divergence,
    so ``v24_class2_guard`` raises RuntimeError and we propagate it
    upwards as a hard failure.
    """
    lam = float(params.get("quartic_lambda", params.get("lambda", np.nan)))
    gam = float(params.get("sextic_gamma",   params.get("gamma",  np.nan)))
    mu2 = float(params.get("mu2", np.nan))
    if not np.isfinite(lam) or not np.isfinite(gam) or not np.isfinite(mu2):
        return {
            "passed": False,
            "skipped": True,
            "reason": ("v2.4 gate skipped: params['mu2'], 'lambda', "
                       "or 'gamma' is missing or non-finite."),
        }

    try:
        P = BrazovskiiParams(lam=lam, gam=gam)
    except ValueError as exc:
        return {
            "passed": False,
            "skipped": True,
            "reason": f"v2.4 gate skipped: invalid Brazovskii params ({exc}).",
        }

    r_global, r_meta = brazovskii_critical_mu2(P)
    if mu2 >= r_meta:
        # Outside the Math56-Addendum existence window: T1 of Theorem 1
        # fails, there is no real BCC local extremum at these parameters.
        # The gate is vacuous; refuse to certify but do not crash.
        msg = (f"v2.4 gate SKIPPED: mu2 = {mu2:.4e} >= r_c^meta = {r_meta:.4e}. "
               f"Outside Math56-Addendum existence window "
               f"(Theorem 1, Corollary 1).  Run a Math55 continuation to "
               f"mu2 < r_c^meta before expecting a BCC Psi*.")
        if verbose:
            print(f"  [v2.4 Phase-0] {msg}")
        return {
            "passed": False,
            "skipped": True,
            "reason": msg,
            "mu2": mu2,
            "r_c_global": float(r_global),
            "r_c_meta":   float(r_meta),
        }

    sep = v24_separatrix_thresholds(mu2, P)
    mean_sq = float(np.mean(np.abs(Psi_star) ** 2))
    gate = v24_phase0_gate(mean_sq, sep)

    # Class-II floor: hard-fail if Psi* has numerically collapsed to
    # the trivial vacuum, in which case Hessian_vec is ill-defined.
    v24_class2_guard(mean_sq, sep)

    phi0_sq = float(sep.phi_plus ** 2)
    out = {
        "passed": bool(gate["passed"]),
        "skipped": False,
        "mu2": float(mu2),
        "r_c_global": float(r_global),
        "r_c_meta":   float(r_meta),
        "phi_plus":  float(sep.phi_plus),
        "phi_minus": float(sep.phi_minus),
        "alpha_sep": float(sep.alpha_sep),
        "G0_raw":    float(sep.G0_raw),
        "G0_op":     float(sep.G0_op),
        "G0_cushion": float(V24_G0_CUSHION),
        "rho_star":  float(sep.rho_star),
        "rho_star_factor": float(V24_RHO_STAR_FACTOR),
        "mean_sq_Psi_star": float(mean_sq),
        "V_statistic":  float(gate["V"]),
        "reason": (
            f"V = {gate['V']:.4f} "
            f"{'>=' if gate['passed'] else '<'} G0_op = {sep.G0_op:.4f} "
            f"(cushion delta = {V24_G0_CUSHION:.3f} above alpha_sep = "
            f"{sep.alpha_sep:.4f})."
        ),
    }
    if verbose:
        tag = "PASS" if out["passed"] else "FAIL"
        print(f"  [v2.4 Phase-0 gate]  mu2={mu2:.4e}  "
              f"phi_+={sep.phi_plus:.4f}  rho_*={sep.rho_star:.2e}")
        print(f"  [v2.4 Phase-0 gate]  V(Psi*)={gate['V']:.4f}  "
              f"G0_op={sep.G0_op:.4f}  -> {tag}")
    return out


def run_proof_pipeline(
    N: int,
    L: float,
    params: Dict[str, Any],
    *,
    phases: str = "1234",
    outdir: Optional[str] = None,
    verbose: bool = True,
    tol_newton: float = 1e-10,
    max_newton: int = 50,
    krylov_method: str = 'gmres',
    gmres_restart: int = 50,
    eisenstat_walker: bool = True,
    ew_eta_max: float = 0.9,
    ew_eta_min: float = 0.01,
    include_translation_zero_modes: bool = True,
    include_global_phase_zero_mode: bool = False,
    continuum_Ns: Optional[Sequence[int]] = None,
    rng_seed: int = 12345,
    v24_gate_enabled: bool = True,
) -> Dict[str, Any]:
    """Execute selected phases of the TECT proof protocol.

    Returns a JSON-serializable results dictionary.
    """
    params = dict(params)
    results: Dict[str, Any] = {
        "N": int(N),
        "L": float(L),
        "theory_tag": params.get("theory_tag", "unknown"),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "phases": phases,
    }

    if outdir is not None:
        os.makedirs(outdir, exist_ok=True)

    # Ensure grid params are set for the backend.
    params.setdefault("N", N)
    params.setdefault("L", L)
    params.setdefault("Lx", L)
    params.setdefault("Ly", L)
    params.setdefault("Lz", L)
    params.setdefault("Nx", N)
    params.setdefault("Ny", N)
    params.setdefault("Nz", N)

    Psi_star: Optional[np.ndarray] = None
    projector: Optional[ZeroModeProjector] = None

    # ── Phase 1: existence ──────────────────────────────────────
    if "1" in phases:
        Psi0 = build_bcc_ansatz(N, L, params)
        if verbose:
            amp_rms = float(np.sqrt(np.mean(np.abs(Psi0) ** 2)))
            print(f"\n  [ansatz] RMS amplitude = {amp_rms:.6e}")

        Psi_star, newton_hist, projector = newton_solve(
            Psi0, params,
            max_newton=max_newton,
            tol_newton=tol_newton,
            krylov_method=krylov_method,
            gmres_restart=gmres_restart,
            eisenstat_walker=eisenstat_walker,
            ew_eta_max=ew_eta_max,
            ew_eta_min=ew_eta_min,
            include_translation_zero_modes=include_translation_zero_modes,
            include_global_phase_zero_mode=include_global_phase_zero_mode,
            verbose=verbose,
        )
        last = newton_hist[-1]
        converged = bool(last["grad_norm"] < tol_newton)
        results["phase1"] = {
            "converged": converged,
            "final_projected_grad_norm": float(last["grad_norm"]),
            "final_F": float(last["F"]),
            "steps": int(len(newton_hist)),
            "projector_zero_modes": int(
                projector.n_basis if projector is not None else 0),
            "history": newton_hist,
        }

        if outdir is not None:
            np.save(os.path.join(outdir, "Psi_star.npy"), Psi_star)
            np.save(os.path.join(outdir, "Psi_ansatz.npy"), Psi0)

    # ── Downstream gate: Phase 1 failure blocks Phases 2/3/4 ──
    #    A non-stationary branch cannot be meaningfully audited
    #    for stability, energetics, or continuum behavior.
    if "1" in phases and not results.get("phase1", {}).get(
            "converged", False):
        downstream_needed = any(p in phases for p in "234")
        if downstream_needed:
            results["downstream_blocked"] = True
            results["downstream_reason"] = (
                "Phase 1 did not converge; Phases 2/3/4 are invalid "
                "on a non-stationary branch."
            )
            if verbose:
                print("\n  >>> Phase 1 FAILED -- downstream phases blocked.")
            if outdir is not None:
                safe_results = sanitize_for_json(results)
                with open(os.path.join(outdir, "proof_results.json"),
                          "w", encoding="utf-8") as f:
                    json.dump(safe_results, f, indent=2, allow_nan=False)
            return results

    # ── v2.4 Phase-0 gate (Math56-Addendum Theorem 2 + Corollary 1) ──
    #    Applied only if Phase 1 converged.  Refuses to enter Phases
    #    2/3/4 on a trivial-vacuum Psi*.  Skipped silently if mu2 lies
    #    above the Math56-Addendum existence window (r_c^meta), in
    #    which case a Math55 continuation to mu2 <= r_c^meta is
    #    required before the gate is physically meaningful.
    if "1" in phases and v24_gate_enabled and Psi_star is not None and (
            results.get("phase1", {}).get("converged", False)):
        try:
            phase0 = _run_v24_phase0_gate(Psi_star, params, verbose=verbose)
        except RuntimeError as exc:
            # Class-II floor breach: Psi* has collapsed; Hessian_vec
            # would diverge.  Propagate as a hard downstream block.
            phase0 = {
                "passed": False,
                "skipped": False,
                "class2_floor_breach": True,
                "reason": str(exc),
            }
        results["phase0_gate_v24"] = phase0

        if (not phase0.get("passed", False)
                and not phase0.get("skipped", False)):
            downstream_needed = any(p in phases for p in "234")
            if downstream_needed:
                results["downstream_blocked"] = True
                results["downstream_reason"] = (
                    "v2.4 Phase-0 gate FAILED on converged Psi*: "
                    + phase0.get("reason", "unknown")
                    + "  Phases 2/3/4 are invalid on a trivial-vacuum "
                      "branch (Math56-Addendum §§A-E)."
                )
                if verbose:
                    print("\n  >>> v2.4 Phase-0 gate FAILED -- "
                          "downstream phases blocked.")
                if outdir is not None:
                    safe_results = sanitize_for_json(results)
                    with open(os.path.join(outdir, "proof_results.json"),
                              "w", encoding="utf-8") as f:
                        json.dump(safe_results, f, indent=2,
                                  allow_nan=False)
                return results

    # ── Phase 2: stability ──────────────────────────────────────
    if "2" in phases:
        if Psi_star is None:
            if (outdir is not None
                    and os.path.isfile(os.path.join(outdir, "Psi_star.npy"))):
                Psi_star = np.load(os.path.join(outdir, "Psi_star.npy"))
            else:
                raise RuntimeError(
                    "Phase 2 requires Phase 1 output Psi_star.")
        if projector is None:
            projector = build_zero_mode_projector(
                Psi_star, params,
                include_translations=include_translation_zero_modes,
                include_global_phase=include_global_phase_zero_mode,
            )

        evals, evecs = lanczos_hessian(
            Psi_star, params,
            projector=projector,
            rng_seed=rng_seed,
            verbose=verbose,
        )
        phase2 = analyze_projected_spectrum(evals)
        results["phase2"] = asdict(phase2)

        if phase2.n_near_zero > 0:
            results["phase2_warning"] = (
                f"Projected spectrum still contains {phase2.n_near_zero} "
                f"near-zero mode(s); projector or backend symmetry "
                f"handling may be incomplete."
            )
            if verbose:
                print(f"  [WARNING] {results['phase2_warning']}")

        if outdir is not None:
            np.save(os.path.join(outdir, "hessian_evals_projected.npy"),
                    evals)
            np.save(os.path.join(outdir, "hessian_ritz_vectors_projected.npy"),
                    evecs)

    # ── Phase 3: energetics vs vacuum ───────────────────────────
    if "3" in phases:
        if Psi_star is None:
            if (outdir is not None
                    and os.path.isfile(os.path.join(outdir, "Psi_star.npy"))):
                Psi_star = np.load(os.path.join(outdir, "Psi_star.npy"))
            else:
                raise RuntimeError(
                    "Phase 3 requires Phase 1 output Psi_star.")
        phase3 = compute_energy_difference(Psi_star, params, verbose=verbose)
        results["phase3"] = asdict(phase3)

    # ── Phase 4: continuum audit ────────────────────────────────
    if "4" in phases:
        Ns_list = (list(continuum_Ns) if continuum_Ns is not None
                   else [32, 64, 128])
        phase4 = run_continuum_audit(
            Ns=Ns_list, L=L, params=params,
            outdir=(os.path.join(outdir, "continuum")
                    if outdir is not None else None),
            tol_newton=tol_newton,
            max_newton=max_newton,
            krylov_method=krylov_method,
            gmres_restart=gmres_restart,
            eisenstat_walker=eisenstat_walker,
            ew_eta_max=ew_eta_max,
            ew_eta_min=ew_eta_min,
            verbose=verbose,
        )
        results["phase4"] = asdict(phase4)

    # ── Save ────────────────────────────────────────────────────
    if outdir is not None:
        safe_results = sanitize_for_json(results)
        with open(os.path.join(outdir, "proof_results.json"),
                  "w", encoding="utf-8") as f:
            json.dump(safe_results, f, indent=2, allow_nan=False)
        if verbose:
            print(f"\n  Results saved to {outdir}/proof_results.json")

    # ── Summary ─────────────────────────────────────────────────
    if verbose:
        print("\n" + "=" * 72)
        print("  PROOF PROTOCOL SUMMARY")
        print("=" * 72)
        if results.get("downstream_blocked", False):
            print(f"  DOWNSTREAM BLOCKED: "
                  f"{results.get('downstream_reason', 'unknown')}")
        if "phase1" in results:
            p1 = results["phase1"]
            status = "PASS" if p1["converged"] else "FAIL"
            print(
                f"  Phase 1 (Existence):    {status}"
                f"  projected ||grad|| = "
                f"{p1['final_projected_grad_norm']:.2e}"
            )
        if "phase0_gate_v24" in results:
            p0 = results["phase0_gate_v24"]
            if p0.get("skipped", False):
                print(f"  Phase 0 gate (v2.4):    SKIP  "
                      f"({p0.get('reason','')[:50]}...)")
            else:
                status = "PASS" if p0.get("passed", False) else "FAIL"
                v = p0.get("V_statistic", float("nan"))
                g = p0.get("G0_op", float("nan"))
                print(
                    f"  Phase 0 gate (v2.4):    {status}"
                    f"  V = {v:.4f}, G0_op = {g:.4f} "
                    f"(Math56-Addendum Thm. 2+Cor. 1)"
                )
        if "phase2" in results:
            p2 = results["phase2"]
            status = "PASS" if p2["stable"] else "FAIL"
            print(
                f"  Phase 2 (Stability):    {status}"
                f"  m*^2 = {p2['m_star_sq']:.6e}, n_neg = {p2['n_negative']}"
            )
        if "phase3" in results:
            p3 = results["phase3"]
            status = "PASS" if p3["favorable_vs_vacuum"] else "FAIL"
            print(
                f"  Phase 3 (Energetics):   {status}"
                f"  Delta F = {p3['delta_F']:+.6e}"
            )
        if "phase4" in results:
            p4 = results["phase4"]
            status = "PASS" if p4["passed"] else "FAIL"
            print(
                f"  Phase 4 (Continuum):    {status}"
                f"  m*^2(h->0) = "
                f"{p4['continuum_intercept_m_star_sq']:+.6e}"
            )
        print("=" * 72)

    return results


# ===========================================================================
# §10  CLI
# ===========================================================================

def parse_L(s: str) -> float:
    """Parse L from string, supporting 'Npi' notation (e.g. '10pi')."""
    s = s.strip().lower()
    if s.endswith("pi"):
        coeff = s[:-2].strip()
        coeff = "1" if coeff == "" else coeff
        return float(coeff) * math.pi
    return float(s)


def parse_int_list(s: str) -> List[int]:
    vals = [item.strip() for item in s.split(",") if item.strip()]
    if not vals:
        raise ValueError("Empty integer list.")
    return [int(v) for v in vals]


def phase_failed(phases: str, results: Dict[str, Any]) -> bool:
    """Check if ANY requested phase failed. Used for exit code.

    Also returns True if downstream phases were blocked by Phase 1
    failure OR the v2.4 Phase-0 gate (Math56-Addendum Thm. 2 + Cor. 1).
    """
    if results.get("downstream_blocked", False):
        return True
    # v2.4 gate: a non-skipped FAIL is a hard failure even if the
    # downstream_blocked sentinel has not been set (e.g. when phases
    # were restricted to "1" so Phases 2/3/4 were not requested).
    p0 = results.get("phase0_gate_v24")
    if p0 is not None and not p0.get("skipped", False) and not p0.get(
            "passed", False):
        return True
    if ("1" in phases
            and not results.get("phase1", {}).get("converged", False)):
        return True
    if ("2" in phases
            and not results.get("phase2", {}).get("stable", False)):
        return True
    if ("3" in phases
            and not results.get("phase3", {}).get("favorable_vs_vacuum",
                                                   False)):
        return True
    if ("4" in phases
            and not results.get("phase4", {}).get("passed", False)):
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TECT trust-region Newton-Krylov solver "
                    "-- rigorous proof protocol",
    )
    parser.add_argument("--config", required=True,
                        help="Path to Brazovskii config JSON")
    parser.add_argument("--N", type=int, default=64,
                        help="Grid dimension (default: 64)")
    parser.add_argument("--L", type=str, default="20pi",
                        help="Box size, supports 'Npi' notation")
    parser.add_argument("--outdir", type=str, default=None,
                        help="Output directory")
    parser.add_argument("--phases", type=str, default="1234",
                        help="Which phases to run, e.g. '1234'")
    parser.add_argument("--tol", type=float, default=1e-10,
                        help="Projected Newton convergence tolerance")
    parser.add_argument("--max-newton", type=int, default=50,
                        help="Maximum Newton iterations")
    parser.add_argument("--continuum-Ns", type=str, default="32,64,128",
                        help="Comma-separated N values for Phase 4")
    parser.add_argument("--rng-seed", type=int, default=12345,
                        help="Random seed for Lanczos start vector")
    parser.add_argument("--include-global-phase-zero-mode",
                        action="store_true",
                        help="Project out i*Psi in Phase 2")
    parser.add_argument("--krylov", type=str, default="gmres",
                        choices=["gmres", "cg"],
                        help="Inner Krylov solver (default: gmres)")
    parser.add_argument("--gmres-restart", type=int, default=50,
                        help="GMRES restart parameter (default: 50)")
    parser.add_argument("--no-eisenstat-walker", action="store_true",
                        help="Disable Eisenstat-Walker adaptive forcing "
                             "(use fixed tol_rel=5e-4)")
    parser.add_argument("--ew-eta-max", type=float, default=0.9,
                        help="EW max forcing term (default: 0.9)")
    parser.add_argument("--ew-eta-min", type=float, default=0.01,
                        help="EW min forcing term (default: 0.01)")
    parser.add_argument("--disable-v24-gate", action="store_true",
                        help="(debug only) Skip the v2.4 Phase-0 gate "
                             "(G0 + Class-II floor, Math56-Addendum "
                             "Theorem 2 + Corollary 1).  Phases 2/3/4 "
                             "will run on whatever Psi* Phase 1 produced, "
                             "including the trivial vacuum -- any results "
                             "must NOT be cited.")

    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        params = json.load(f)

    N = int(args.N)
    L = float(parse_L(args.L))
    outdir = args.outdir or f"newton_rigorous_N{N}"
    continuum_Ns = parse_int_list(args.continuum_Ns)

    print("=" * 72)
    print("  TECT Trust-Region Newton-Krylov Proof Protocol")
    print("=" * 72)
    print(f"  Config        : {args.config}")
    print(f"  Grid          : N={N}, L={L:.6f}")
    print(f"  Phases        : {args.phases}")
    print(f"  Outdir        : {outdir}")
    print(f"  Newton tol    : {args.tol:.1e}")
    print(f"  Max Newton    : {args.max_newton}")
    print(f"  Continuum Ns  : {continuum_Ns}")
    print(f"  Krylov        : {args.krylov.upper()}"
          f"  (restart={args.gmres_restart})" * (args.krylov == 'gmres'))
    ew_on = not args.no_eisenstat_walker
    print(f"  Eisenstat-Walker: {'ON' if ew_on else 'OFF'}"
          + (f"  (eta in [{args.ew_eta_min}, {args.ew_eta_max}])" if ew_on else ""))
    print(f"  RNG seed      : {args.rng_seed}")
    print()

    results = run_proof_pipeline(
        N=N, L=L, params=params,
        phases=args.phases,
        outdir=outdir,
        verbose=True,
        tol_newton=args.tol,
        max_newton=args.max_newton,
        krylov_method=args.krylov,
        gmres_restart=args.gmres_restart,
        eisenstat_walker=ew_on,
        ew_eta_max=args.ew_eta_max,
        ew_eta_min=args.ew_eta_min,
        include_translation_zero_modes=True,
        include_global_phase_zero_mode=bool(
            args.include_global_phase_zero_mode),
        continuum_Ns=continuum_Ns,
        rng_seed=args.rng_seed,
        v24_gate_enabled=(not bool(args.disable_v24_gate)),
    )

    sys.exit(1 if phase_failed(args.phases, results) else 0)


if __name__ == "__main__":
    main()
