#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the v2.6.2 CiiProjector API (Task #114, Math73).

Covers:
  T1 — FullProjector is the identity (numpy-only).
  T2 — ChannelProjector kills the longitudinal direction P Psi = 0 (numpy-only).
  T3 — ChannelProjector is idempotent: P^2 = P (numpy-only).
  T4 — ChannelProjector is self-adjoint on the real-Hilbert <,>_H (numpy-only).
  T5 — v2.6.2 default symmetrisation reproduces v2.6.1 output bit-identically
       (torch required; skipped otherwise).
  T6 — Channel-localisation diagnostic eta_chan >= 0.99 per Math73
       Prop. math73-eta-prediction (torch required; skipped otherwise).

Policy: this file lives under the v2.6.2 API contract of Math73 §5; any
regression failure here falsifies the diagnostic interpretation of
P_cII(Psi) or the backward-compatibility guarantee of FullProjector.

Target signature:  0 FAIL / 6 PASS / 0 SKIP   on a torch-enabled host.
                   0 FAIL / 4 PASS / 2 SKIP   on a torch-less host.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

# Ensure PDE and tests/ are importable.
_PDE_DIR = Path(__file__).resolve().parent.parent / "PDE"
if str(_PDE_DIR) not in sys.path:
    sys.path.insert(0, str(_PDE_DIR))
_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

try:
    from tect_newton_krylov import (
        CiiProjector,
        FullProjector,
        ChannelProjector,
        _BooleanMaskProjector,
        _default_cii_projector,
        _symmetrise_jacobian_cii_v26,
        _compute_adjoint_jacobian_vec_v26,
        channel_localisation_eta,
        flatten_complex_field,
        unflatten_complex_field,
        HessianOperator,
    )
    import real_backend_pt_bcc_mixed_v3 as backend  # noqa: F401
    _IMPORT_OK = True
    _IMPORT_ERROR = ""
except (ImportError, ModuleNotFoundError) as exc:  # pragma: no cover
    _IMPORT_OK = False
    _IMPORT_ERROR = str(exc)

try:
    import torch  # noqa: F401
    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False

# The conftest helper enforces Lx/Ly/Lz injection (Math68 §3 Blocker B5).
from conftest import make_bcc_config  # noqa: E402


# ---------------------------------------------------------------------------
# Utility builders — random Psi, v on a small lattice.
# ---------------------------------------------------------------------------


def _random_field(N: int, *, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    real = rng.standard_normal(size=(3, N, N, N))
    imag = rng.standard_normal(size=(3, N, N, N))
    return np.asarray(real + 1j * imag, dtype=np.complex128)


def _real_hilbert_inner(u: np.ndarray, v: np.ndarray) -> float:
    r"""<u, v>_H := Re sum_{x,a} conj(u_a(x)) v_a(x)  (no dV factor, cf. test scope)."""
    return float(np.real(np.sum(np.conj(u) * v)))


# ===========================================================================
# T1 — FullProjector is the exact identity (numpy-only)
# ===========================================================================


def test_full_projector_is_identity() -> None:
    if not _IMPORT_OK:
        pytest.fail(f"PDE imports failed: {_IMPORT_ERROR}")
    Psi = _random_field(N=4, seed=1)
    xi = _random_field(N=4, seed=2)
    proj = FullProjector()
    out = proj.apply(Psi, xi)
    # Exact byte-wise equality; identity must not perturb.
    assert out.shape == xi.shape
    assert np.array_equal(out, xi), "FullProjector.apply must be the identity"


# ===========================================================================
# T2 — ChannelProjector annihilates the longitudinal direction
# ===========================================================================


def test_channel_projector_kills_longitudinal() -> None:
    if not _IMPORT_OK:
        pytest.fail(f"PDE imports failed: {_IMPORT_ERROR}")
    Psi = _random_field(N=4, seed=3)
    # Guarantee |Psi(x)|^2 >= 1 by rescaling pointwise (avoids the eps
    # regularisation regime where P Psi is only O(eps)).
    rho = (np.conj(Psi) * Psi).sum(axis=0).real
    scale = np.sqrt(1.0 / np.maximum(rho, 1e-12))
    Psi = Psi * scale[np.newaxis, ...]
    proj = ChannelProjector(eps=1e-12)
    out = proj.apply(Psi, Psi)
    # |P Psi|^2 / |Psi|^2 should be O(eps / |Psi|^2) <= 1e-11.
    num = float(np.linalg.norm(out))
    den = float(np.linalg.norm(Psi))
    ratio = num / max(den, 1e-300)
    assert ratio < 1e-10, (
        f"ChannelProjector should kill the longitudinal direction; "
        f"measured ratio {ratio:.3e} violates Math73 Lem. "
        f"math73-proj-properties (c)."
    )


# ===========================================================================
# T3 — ChannelProjector is idempotent: P^2 = P
# ===========================================================================


def test_channel_projector_idempotent() -> None:
    if not _IMPORT_OK:
        pytest.fail(f"PDE imports failed: {_IMPORT_ERROR}")
    Psi = _random_field(N=4, seed=4)
    xi = _random_field(N=4, seed=5)
    proj = ChannelProjector(eps=1e-12)
    P_xi = proj.apply(Psi, xi)
    P2_xi = proj.apply(Psi, P_xi)
    # P^2 xi == P xi up to O(eps / |Psi|^2) regularisation.
    diff = float(np.linalg.norm(P2_xi - P_xi))
    norm = float(np.linalg.norm(P_xi))
    rel = diff / max(norm, 1e-300)
    assert rel < 1e-12, (
        f"ChannelProjector idempotence violated: rel_err={rel:.3e}; "
        f"Math73 Lem. math73-proj-properties (a) broken."
    )


# ===========================================================================
# T4 — ChannelProjector is self-adjoint: <u, P v>_H = <P u, v>_H
# ===========================================================================


def test_channel_projector_self_adjoint() -> None:
    if not _IMPORT_OK:
        pytest.fail(f"PDE imports failed: {_IMPORT_ERROR}")
    Psi = _random_field(N=4, seed=6)
    u = _random_field(N=4, seed=7)
    v = _random_field(N=4, seed=8)
    proj = ChannelProjector(eps=1e-12)
    lhs = _real_hilbert_inner(u, proj.apply(Psi, v))
    rhs = _real_hilbert_inner(proj.apply(Psi, u), v)
    # Absolute tolerance scaled by the natural size of the inner product.
    scale = max(abs(lhs), abs(rhs), 1.0)
    diff = abs(lhs - rhs) / scale
    assert diff < 1e-13, (
        f"ChannelProjector self-adjointness violated: "
        f"|<u,Pv>-<Pu,v>|/scale={diff:.3e}; "
        f"Math73 Lem. math73-proj-properties (b) broken."
    )


# ===========================================================================
# T5 — v2.6.2 default symmetrisation reproduces v2.6.1 output bit-identically
# ===========================================================================


@pytest.mark.skipif(not _HAS_TORCH,
                    reason="torch required for adjoint JVP comparison")
@pytest.mark.skipif(not _IMPORT_OK,
                    reason="PDE imports failed")
def test_v262_default_reproduces_v261() -> None:
    """
    With the v2.6.2 default (FullProjector), the symmetrised output
    must agree with the v2.6.1 (Boolean all-True mask) output to
    machine precision — this is the backward-compatibility guarantee
    of Math73 §5.
    """
    config = make_bcc_config(L=1.0, N=8, mu2=-0.5, lam=-1.0, gamma=0.8)
    N = config["N"]
    Psi = _random_field(N=N, seed=11)
    v = _random_field(N=N, seed=12)

    Hv = backend.hessian_vec(Psi, v, config)

    # v2.6.2 default (FullProjector) — new API.
    Hv_v262 = _symmetrise_jacobian_cii_v26(Hv, Psi, v, config)

    # v2.6.1 emulation — legacy Boolean all-True mask via deprecation shim.
    all_true = np.ones(2 * int(np.prod(Psi.shape)), dtype=bool)
    with pytest.warns(DeprecationWarning):
        Hv_v261 = _symmetrise_jacobian_cii_v26(
            Hv, Psi, v, config, cii_mask=all_true)

    diff = float(np.linalg.norm(Hv_v262 - Hv_v261))
    norm = float(np.linalg.norm(Hv_v262))
    rel = diff / max(norm, 1e-300)
    assert rel < 1e-14, (
        f"v2.6.2 FullProjector must reproduce v2.6.1 all-True mask "
        f"output to machine precision; measured rel_err={rel:.3e}."
    )


# ===========================================================================
# T6 — Channel-localisation eta_chan >= 0.99 (Math73 Prop. math73-eta-prediction)
# ===========================================================================


@pytest.mark.skipif(not _HAS_TORCH,
                    reason="torch required for adjoint JVP computation")
@pytest.mark.skipif(not _IMPORT_OK,
                    reason="PDE imports failed")
def test_channel_localisation_of_antiherm() -> None:
    """
    The channel-localisation diagnostic eta_chan := ||P_cII (J - J^dag) v||
    / ||(J - J^dag) v|| verifies that the anti-Hermitian content of the
    full Jacobian is concentrated in the channel subspace, as required
    by the Math66 Path-X legitimacy argument (Math73 Prop.
    math73-eta-prediction: eta_chan = 1 + O(1e-11)).
    """
    config = make_bcc_config(L=1.0, N=8, mu2=-0.5, lam=-1.0, gamma=0.8)
    N = config["N"]
    Psi = _random_field(N=N, seed=21)
    v = _random_field(N=N, seed=22)
    # Normalise v for a clean comparison with the predicted value.
    v = v / max(float(np.linalg.norm(v)), 1e-300)

    eta = channel_localisation_eta(Psi, v, config)
    assert eta >= 0.99, (
        f"Channel-localisation diagnostic eta_chan={eta:.4f} < 0.99; "
        f"this falsifies the Math66 Path-X hypothesis (Math73 Prop. "
        f"math73-eta-prediction) and mandates re-opening Math65 branch (S)."
    )
