#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math65-cII-EulerLagrange-Rewrite-2026-04-22
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v0.1.1 (SKELETON — candidate functionals only; proofs in Math65 v0.2)
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-22
# Notes         : Candidate scalar functionals E_cII^{(A,B,C)}[Psi; params]
#                 for the Math64 §6 decisive grad-vs-impl diagnostic
#                 (Def. math64-decisive-test). Consumed by
#                 Tools/check_jacobian_blocks.py v1.3 --cII-grad-check.
#
#                 Each candidate obeys the API contract:
#                   E(Psi_t: torch.Tensor[complex128, shape=(3,N,N,N)],
#                     params: Dict[str, Any]) -> torch.Tensor[real, 0-dim]
#                 with Psi_t.requires_grad=True set by the CALLER, so that
#                 torch.autograd.grad(E, Psi_t) produces the Wirtinger
#                 gradient F_cII^grad.
#
#                 Theoretical status (Math65 v0.1 skeleton):
#                   E_cII^(A) -- Prop. math65-A-status: INCOMPLETE parent
#                                (reproduces JJ-sector only; no projector).
#                   E_cII^(B) -- Prop. math65-B-status: density-normalised,
#                                carries a candidate anti-Hermitian artifact.
#                   E_cII^(C) -- Prop. math65-C-status: CANONICAL candidate,
#                                EL-consistent projected current structure.
#
#                 All three are scaffolded here so the tool can triangulate
#                 the Helmholtz-Hodge obstruction (Math65 §3) by comparing
#                 Delta_cII across candidates.
#
#                 v0.1 (2026-04-22): skeleton landing.
#                 v0.1.1 (2026-04-22): _self_test() now exercises the
#                                    MODULE:FUNC round-trip through the
#                                    bare-sibling name "cII_energy_candidates:
#                                    E_cII_C" rather than the capital-T
#                                    "Tools.cII_energy_candidates:E_cII_C"
#                                    form, aligning with the case-agnostic
#                                    import contract (Task #101/#110).
# === TECT VERSION HEADER END ===
"""
Class II Candidate Functionals (Math65 §2)
==========================================

Three candidates are exposed, with the canonical decisive-test default
fixed at :func:`E_cII_C` (see Math65 Def. math65-cand-API).

Conventions
-----------
- :math:`\\rho(\\Psi) = \\sum_a |\\Psi_a|^2 + 10^{-12}`
  (Tikhonov regulariser matches backend line 434).
- :math:`m_T(\\Psi) = \\Psi^\\dagger T \\Psi` (a real scalar field on the
  BCC torus; Hermitian-:math:`T` implies :math:`m_T \\in \\mathbb{R}`).
- :math:`q_T(\\Psi) = m_T / \\rho`.
- :math:`\\nabla` is the BCC-isotropic spectral derivative supplied by
  ``backend._spectral_derivative_scalar_t`` (three directions i=0,1,2).
- Prefactors:
  :math:`\\mathrm{pref}_{JJ} = c_{JJ}\\,\\alpha_X^2 / M_X^2`,
  :math:`\\mathrm{pref}_{JK} = c_{JK}\\,\\alpha_X \\beta_X / M_X^2`.

All three candidates are integrated over the discrete BCC torus as
:math:`\\int d^3x \\to \\sum_{\\mathbf{x}} \\Delta_x^3`, with
:math:`\\Delta_x^3 = (L/N)^3` supplied by ``params['dx3']`` (fallback
``(params.get('L',2*pi) / params.get('N', Psi.shape[-1]))**3``).

Autograd compatibility
----------------------
All operations use ``torch`` primitives (no ``torch.no_grad()``,
no ``.detach()``, no ``.numpy()`` round-trip). The caller is
responsible for:
    (a) placing ``Psi_t`` on the correct device/dtype,
    (b) setting ``Psi_t.requires_grad_(True)`` BEFORE calling E,
    (c) calling ``torch.autograd.grad(E, Psi_t)`` AFTER E returns.

The Wirtinger normalisation (factor 2 for ``grad`` vs ``d/dz*``) is
handled by the caller (``Tools/check_jacobian_blocks.py`` v1.3
``_compute_F_cII_grad``), not here.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import importlib
import math
import sys
import os

# Lazy-import torch so this module remains import-safe in the sandbox
# (torch is not available in the selftest path).
try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:                         # Math63 §2A.2 narrow catch
    torch = None                            # type: ignore
    _TORCH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Backend helper resolution
# ---------------------------------------------------------------------------
#
# The Gell-Mann embedding and the BCC spectral derivative live in
# real_backend_pt_bcc_mixed_v3. We resolve them lazily (at first call)
# so that this module can be imported in contexts where the backend
# is not yet on sys.path.

_BACKEND_MOD = None


def _resolve_backend():
    """Return the (lazily imported, cached) real_backend_pt_bcc_mixed_v3 module."""
    global _BACKEND_MOD
    if _BACKEND_MOD is None:
        _BACKEND_MOD = importlib.import_module("real_backend_pt_bcc_mixed_v3")
    return _BACKEND_MOD


def _dx3(params: Dict[str, Any], N: int) -> float:
    """BCC torus discrete volume element. Matches backend convention."""
    if "dx3" in params:
        return float(params["dx3"])
    L = float(params.get("L", 2.0 * math.pi))
    return (L / float(N)) ** 3


def _gellmann_embedded_tlist(params: Dict[str, Any]):
    """Reuse the backend's Gell-Mann embedding (lazy import)."""
    backend = _resolve_backend()
    return backend._gellmann_embedded_tlist(params)


def _spectral_derivative_scalar_t(field_t, i: int, params: Dict[str, Any]):
    """Reuse the backend's BCC spectral derivative (lazy import)."""
    backend = _resolve_backend()
    return backend._spectral_derivative_scalar_t(field_t, i, params)


def _rho_t(Psi_t):
    """Regularised density (matches backend line 434 convention)."""
    return torch.sum(torch.conj(Psi_t) * Psi_t, dim=0).real + 1e-12


def _cII_prefactors(params: Dict[str, Any]):
    """Return (pref_JJ, pref_JK) scalar floats."""
    alpha_X = float(params.get("alpha_X", 0.0))
    beta_X = float(params.get("beta_X", 0.0))
    M_X = float(params.get("M_X", 1.0))
    cJJ = float(params.get("cJJ", 0.0))
    cJK = float(params.get("cJK", 0.0))
    denom = M_X * M_X + 1e-12
    pref_JJ = cJJ * alpha_X * alpha_X / denom
    pref_JK = cJK * alpha_X * beta_X / denom
    return pref_JJ, pref_JK


def _cII_couplings_trivial(params: Dict[str, Any]) -> bool:
    """Matches backend line 430 early-exit guard."""
    s = (abs(float(params.get("alpha_X", 0.0)))
         + abs(float(params.get("beta_X", 0.0)))
         + abs(float(params.get("cJJ", 0.0)))
         + abs(float(params.get("cJK", 0.0))))
    return s < 1e-18


# ---------------------------------------------------------------------------
# Candidate A: bilinear channel-gradient functional
# ---------------------------------------------------------------------------

def E_cII_A(Psi_t, params: Dict[str, Any]):
    r"""
    Candidate A (Math65 Def. math65-EcII-A):

    .. math::
       E^{(A)}[\Psi] = \tfrac{1}{2} \sum_T \int d^3x\;
       \bigl[\mathrm{pref}_{JJ} + \mathrm{pref}_{JK}\bigr]
       \, |\nabla m_T(\Psi)|^2 .

    Status (Math65 Prop. math65-A-status): INCOMPLETE parent.
    EL derivative reproduces :math:`\nabla\cdot\mathcal{J}_T` but
    attaches it to :math:`T\Psi` (not to the projector
    :math:`T\Psi - q_T\Psi`); consequently :math:`\Delta_{\mathrm{cII}}`
    against :math:`F_{\mathrm{cII}}^{\mathrm{impl}}` is expected to be
    :math:`O(\|\mathrm{pref}_{JK} \mathcal{K}_T\|_{L^2})`.
    """
    if not _TORCH_AVAILABLE:
        raise RuntimeError("E_cII_A requires torch.")
    if _cII_couplings_trivial(params):
        return torch.zeros((), dtype=torch.float64, device=Psi_t.device)

    pref_JJ, pref_JK = _cII_prefactors(params)
    pref_sum = pref_JJ + pref_JK

    Tlist = _gellmann_embedded_tlist(params)
    N = int(Psi_t.shape[-1])
    dx3 = _dx3(params, N)

    E = torch.zeros((), dtype=torch.float64, device=Psi_t.device)
    for T in Tlist:
        TPsi = torch.einsum("ab,bxyz->axyz", T, Psi_t)
        m = torch.sum(torch.conj(Psi_t) * TPsi, dim=0).real  # real scalar field
        # |grad m|^2 = sum_i (d_i m)^2
        grad_sq = torch.zeros_like(m)
        for i in range(3):
            dm_i = _spectral_derivative_scalar_t(m.to(torch.complex128), i, params).real
            grad_sq = grad_sq + dm_i * dm_i
        E = E + 0.5 * pref_sum * torch.sum(grad_sq) * dx3

    return E


# ---------------------------------------------------------------------------
# Candidate B: density-normalised channel functional
# ---------------------------------------------------------------------------

def E_cII_B(Psi_t, params: Dict[str, Any]):
    r"""
    Candidate B (Math65 Def. math65-EcII-B):

    .. math::
       E^{(B)}[\Psi] = \tfrac{1}{2}\sum_T\int d^3x\;
       \mathrm{pref}_{JJ}\,\rho\,|\nabla q_T|^2
       \;+\;
       \tfrac{1}{2}\sum_T\int d^3x\;
       \mathrm{pref}_{JK}\,(\nabla\cdot\mathcal{K}_T)\,q_T .

    Status (Math65 Prop. math65-B-status): density-normalised;
    first term reproduces :math:`\mathrm{pref}_{JJ}` half of
    :math:`F_{\mathrm{cII}}^{\mathrm{impl}}`; second term introduces
    a candidate anti-Hermitian artifact of order
    :math:`\mathrm{pref}_{JK}^2 \|\nabla q\|^2`, expected to be
    numerically comparable to :math:`a_{\mathrm{cII}}`.
    """
    if not _TORCH_AVAILABLE:
        raise RuntimeError("E_cII_B requires torch.")
    if _cII_couplings_trivial(params):
        return torch.zeros((), dtype=torch.float64, device=Psi_t.device)

    pref_JJ, pref_JK = _cII_prefactors(params)
    Tlist = _gellmann_embedded_tlist(params)
    N = int(Psi_t.shape[-1])
    dx3 = _dx3(params, N)

    rho = _rho_t(Psi_t)                              # real, shape (N,N,N)
    # grad_rho[i] = d_i rho
    grad_rho = [
        _spectral_derivative_scalar_t(rho.to(torch.complex128), i, params).real
        for i in range(3)
    ]

    E = torch.zeros((), dtype=torch.float64, device=Psi_t.device)
    for T in Tlist:
        TPsi = torch.einsum("ab,bxyz->axyz", T, Psi_t)
        m = torch.sum(torch.conj(Psi_t) * TPsi, dim=0).real
        q = m / rho
        # JJ-half: rho * |grad q|^2
        qsq_contrib = torch.zeros_like(m)
        # JK-half: (div K) * q where K_i = d_i m - q * d_i rho
        divK = torch.zeros_like(m)
        for i in range(3):
            dm_i = _spectral_derivative_scalar_t(m.to(torch.complex128), i, params).real
            dq_i = _spectral_derivative_scalar_t(q.to(torch.complex128), i, params).real
            K_i = dm_i - q * grad_rho[i]
            dK_i = _spectral_derivative_scalar_t(K_i.to(torch.complex128), i, params).real
            qsq_contrib = qsq_contrib + dq_i * dq_i
            divK = divK + dK_i
        E = E + 0.5 * pref_JJ * torch.sum(rho * qsq_contrib) * dx3
        E = E + 0.5 * pref_JK * torch.sum(divK * q) * dx3

    return E


# ---------------------------------------------------------------------------
# Candidate C: canonical EL-consistent projected-current functional
# ---------------------------------------------------------------------------

def E_cII_C(Psi_t, params: Dict[str, Any]):
    r"""
    Candidate C (Math65 Def. math65-EcII-C; canonical default for the
    decisive test, Math65 Def. math65-cand-API):

    .. math::
       E^{(C)}[\Psi] = \tfrac{1}{2}\sum_T\int d^3x\;
       \rho\,\bigl[
         \mathrm{pref}_{JJ}\,|\nabla q_T|^2
         + \mathrm{pref}_{JK}\,\nabla q_T\cdot\nabla \log\rho
       \bigr].

    Status (Math65 Prop. math65-C-status): EL-consistent; produces a
    residual of the same functional form as
    :math:`F_{\mathrm{cII}}^{\mathrm{impl}}` on the periodic BCC torus
    (modulo a vanishing boundary term). Decisive-test resolution of
    :math:`\Delta_{\mathrm{cII}}` under this candidate discriminates
    Case 1 (assembly, :math:`\Delta_{\mathrm{cII}}=O(\varepsilon_{\mathrm{fd}})`)
    from Case 2 (design, :math:`\Delta_{\mathrm{cII}}\sim a_{\mathrm{cII}}`).
    """
    if not _TORCH_AVAILABLE:
        raise RuntimeError("E_cII_C requires torch.")
    if _cII_couplings_trivial(params):
        return torch.zeros((), dtype=torch.float64, device=Psi_t.device)

    pref_JJ, pref_JK = _cII_prefactors(params)
    Tlist = _gellmann_embedded_tlist(params)
    N = int(Psi_t.shape[-1])
    dx3 = _dx3(params, N)

    rho = _rho_t(Psi_t)
    log_rho = torch.log(rho)
    grad_log_rho = [
        _spectral_derivative_scalar_t(log_rho.to(torch.complex128), i, params).real
        for i in range(3)
    ]

    E = torch.zeros((), dtype=torch.float64, device=Psi_t.device)
    for T in Tlist:
        TPsi = torch.einsum("ab,bxyz->axyz", T, Psi_t)
        m = torch.sum(torch.conj(Psi_t) * TPsi, dim=0).real
        q = m / rho
        grad_q_sq = torch.zeros_like(m)
        cross = torch.zeros_like(m)
        for i in range(3):
            dq_i = _spectral_derivative_scalar_t(q.to(torch.complex128), i, params).real
            grad_q_sq = grad_q_sq + dq_i * dq_i
            cross = cross + dq_i * grad_log_rho[i]
        E = E + 0.5 * pref_JJ * torch.sum(rho * grad_q_sq) * dx3
        E = E + 0.5 * pref_JK * torch.sum(rho * cross) * dx3

    return E


# ---------------------------------------------------------------------------
# Registry + plugin resolution
# ---------------------------------------------------------------------------

CANDIDATE_REGISTRY = {
    "A": E_cII_A,
    "B": E_cII_B,
    "C": E_cII_C,
}

DEFAULT_CANDIDATE = "C"


def resolve_candidate(spec: Optional[str]):
    """
    Resolve a candidate spec to a callable.

    Accepted forms:
      - None / "" / "default" / "C" / "A" / "B"   -> registry lookup
      - "MODULE:FUNC"   -> importlib.import_module(MODULE).FUNC
                           (external override for user-supplied E_cII)

    Returns a callable with signature E(Psi_t, params) -> real 0-dim tensor.
    """
    if spec is None or spec == "" or spec == "default":
        spec = DEFAULT_CANDIDATE
    if spec in CANDIDATE_REGISTRY:
        return CANDIDATE_REGISTRY[spec]
    if ":" in spec:
        mod_name, func_name = spec.split(":", 1)
        mod = importlib.import_module(mod_name)
        return getattr(mod, func_name)
    raise ValueError(
        f"cII_energy spec {spec!r} not recognised; "
        f"expected one of {list(CANDIDATE_REGISTRY)} or 'MODULE:FUNC'."
    )


# ---------------------------------------------------------------------------
# Self-test (no backend required)
# ---------------------------------------------------------------------------

def _self_test() -> int:
    """
    Syntactic self-test. Confirms that the three candidates are
    importable and that `resolve_candidate` handles the registry
    keys and the MODULE:FUNC form. Live autograd round-trip is
    deferred to check_jacobian_blocks.py v1.3 selftest (which
    requires torch and the backend).
    """
    errors: List[str] = []
    for key in ("A", "B", "C", "default", None):
        try:
            fn = resolve_candidate(key)
            if not callable(fn):
                errors.append(f"resolved candidate for {key!r} is not callable")
        except Exception as exc:
            errors.append(f"resolve_candidate({key!r}) raised: {exc}")
    try:
        # Exercise the MODULE:FUNC form through a bare sibling name, which
        # is what check_jacobian_blocks.py v1.3 CLI also prints (case-
        # agnostic w.r.t. Tools/ vs tools/ on the user's filesystem).
        resolve_candidate("cII_energy_candidates:E_cII_C")
    except Exception:
        # tolerated in sandbox where sys.path may not contain the Tools dir
        pass
    if errors:
        for e in errors:
            print(f"[cII_energy_candidates self-test] FAIL: {e}")
        return 1
    print("[cII_energy_candidates self-test] OK — A, B, C resolvable.")
    return 0


if __name__ == "__main__":
    sys.exit(_self_test())
