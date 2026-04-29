#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math65-cII-EulerLagrange-Rewrite-2026-04-22 /
#                 Math64-cII-Stage-Alpha-Audit-2026-04-22 §6 /
#                 Math63-Solver-Redesign-v2p5-2026-04-22 §2A.3
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v1.4
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-23
# Notes         : Operator-level Jacobian decomposition probe + pre-surgery
#                 decisive F_cII^grad vs F_cII^impl diagnostic (Math64 §6
#                 Def. math64-decisive-test / Math65 §4 Def. math65-cand-API).
#                 Math66 Path-X mandate classifier. Sibling to
#                 tools/check_jacobian_symmetry.py (v2.0).
#
#                 v1.0 (2026-04-22): Skeleton-executable sandbox landing.
#                 v1.1 (2026-04-22): sys.path bootstrap hotfix (Task #100
#                                    parity).
#                 v1.2 (2026-04-22): Math63 §2A.3 Stage α extension —
#                                    (i) --backend {fd,autograd} cII JVP
#                                    routing; (ii) --mu2-list CSV driver;
#                                    (iii) --cII-off structural ablation.
#                 v1.2.1 (2026-04-22): argparse usability hotfix for
#                                    negative-leading-number CSV values.
#                 v1.3 (2026-04-22): Decisive diagnostic (Task #110) —
#                                    (i) --cII-grad-check flag running the
#                                    Math64 §6 / Math65 §4 grad-vs-impl
#                                    comparison F_cII^grad = 2 * d E_cII /
#                                    d Psi* (Wirtinger), classifying the
#                                    outcome per Prop. math64-cii-surgery-
#                                    gate (Case 1 assembly / Case 2 design
#                                    / Case 3 inconclusive).
#                                    (ii) --cII-energy-module MODULE:FUNC
#                                    pluggable E_cII override; default
#                                    resolves to cII_energy_candidates:E_cII_C
#                                    (canonical Math65 candidate; bare sibling
#                                    import — case-agnostic w.r.t. the on-disk
#                                    folder name Tools/ vs tools/).
#                 v1.3.1 (2026-04-22): Tools/tools case-collision hardening
#                                    (Task #101/#110 follow-up). sys.path
#                                    bootstrap now prepends _THIS_FILE_DIR so
#                                    that sibling tool modules are importable
#                                    directly. The lazy import inside
#                                    run_decisive_cII_test() is rewritten as
#                                    `import cII_energy_candidates` (no
#                                    capital-T package prefix). CLI example
#                                    and argparse help text updated to match.
#                                    (iii) Emits (Delta_cII, r_impl, r_grad)
#                                    triple per Eq. math64-decisive-
#                                    observables into the JSON report under
#                                    key "cII_grad_check".
#                                    NOT automatically triggered in the
#                                    default block-sweep path (to keep the
#                                    Stage α re-runs identical bit-for-bit);
#                                    must be enabled with --cII-grad-check.
#                 v1.4 (2026-04-23, Task #111): Math66 Path-X
#                                    cos-theta channel-localisation diagnostic.
#                                    New function _compute_cos_theta_pathX(A_v,
#                                    P_A_v) computes the cosine of the angle
#                                    between anti-Hermitian Jacobian residue
#                                    A v = (J - J†)v/2 and its channel projection
#                                    P_cII(A v), measuring directional alignment
#                                    rather than just magnitude (stricter than
#                                    Math73 eta_chan). Two new self-test rows
#                                    (Cases 7--8): pathX-localised-synthetic
#                                    (cos_theta = 1.0 ± 1e-13) and pathX-
#                                    delocalised-synthetic (cos_theta ≈ 0.707).
#                                    Self-test now 8/8 PASS. Math note: docs/
#                                    math/TECT-Math66-PathX-cos-theta-
#                                    classifier.tex.txt (NEW, 8 sections).
# === TECT VERSION HEADER END ===
"""
Jacobian Block-Decomposition Probe (Math63 §2A.3 Step 1)
========================================================

Purpose
-------
The v2.0 probe in tools/check_jacobian_symmetry.py classifies the FULL
TECT residual Jacobian

    F(Psi) = F_bra(Psi) + F_fam(Psi) + F_lock(Psi) + F_shell(Psi)
           + F_nl(Psi)  + F_cII(Psi),

where the six additive pieces correspond to the Brazovskii linear term
(r - Z Delta + Y Delta^2), the diagonal family mass matrix, the rank-1
internal-lock penalty, the k-space shell-bias penalty (eta_shell (|k|-q0)^2),
the local quartic+sextic nonlinearity (lambda |Psi|^2 Psi + gamma |Psi|^4 Psi),
and the Class II effective projected-hydrodynamic term, respectively.

The v2.5.7 diagnostic on N=32 reports a persistent real-self-adjoint defect

    max_{i<j} |Re<u_i, J u_j> - Re<u_j, J u_i>| / ||J||_F  =  2.66e-04

identical across all six continuation points mu^2 ∈ {-1.0, ..., -0.1}.
The mu^2-independence rules out F_fam (diagonal real) and the mu^2*Psi
term of F_bra as possible sources. The remaining candidates are all
mu^2-independent at the operator level.

The present tool applies the Math63 §2A.1 probe INDIVIDUALLY to each block's
Jacobian by routing a matrix-vector product through PyTorch autograd on a
block-restricted residual wrapper, and reports per-block
(antisym_norm, antisym_norm / ||J_block||_F, Rayleigh range).
The block whose relative antisymmetry exceeds the 1e-8 Math63 threshold
while the others remain at machine-precision Hermitian floor is the
source of the full-residual defect.

Theoretical prediction (Math63 §2A.3 Lemma 1):
    For each block B in {bra, fam, lock, shell, nl}, J_B is real-self-
    adjoint by construction (direct verification in §2A.3.1 of the note).
    For block B = cII, no such proof is available a priori; the block is
    implemented via a finite-difference gradient of a functional that is
    real-valued but whose Euler-Lagrange derivative is projected by a
    non-orthogonal 'channel' projector (T Psi - q Psi).

Thus the tool's expected output is:
    antisym_rel[bra, fam, lock, shell, nl] = O(1e-13..1e-15)
    antisym_rel[cII]                        = O(1e-04)  if Class II is ON
or, if Class II is OFF (all couplings zero) and the signal persists, the
Hermiticity of one of {bra, fam, lock, shell, nl} must be reexamined.

CLI
---
    # Single-point probe, FD cII backend (v1.1 behaviour):
    python Tools/check_jacobian_blocks.py \
        --config PDE/config_template_brazovskii.json \
        --N 32 --mu2 -0.5 \
        --n-probes 5 \
        --output results/step1_block_probe.json

    # Stage α (v1.2) Math63 §2A.3 parallel sweep:
    python Tools/check_jacobian_blocks.py \
        --config PDE/config_template_brazovskii.json \
        --N 32 \
        --mu2-list "-1.0,-0.8,-0.6,-0.4,-0.2,-0.1" \
        --backend autograd \
        --n-probes 5 \
        --output results/step1_sweep_autograd.json --verbose

    # cII-ablation probe (couplings zeroed):
    python Tools/check_jacobian_blocks.py \
        --config PDE/config_template_brazovskii.json \
        --N 32 --mu2 -0.5 --cII-off \
        --output results/step1_cIIoff_probe.json

    # Harness self-test (no backend needed):
    python Tools/check_jacobian_blocks.py --selftest

    # v1.3 decisive grad-vs-impl diagnostic (Math64 §6 / Math65 §4):
    #   --cII-energy-module accepts either "<module>:<func>" or a registry
    #   short-key (e.g. "C"). The module is resolved via a bare sibling
    #   import, so it is case-agnostic w.r.t. Tools/ vs tools/ on disk.
    python Tools/check_jacobian_blocks.py \
        --config PDE/config_template_brazovskii.json \
        --N 32 --mu2 -0.5 \
        --cII-grad-check \
        --cII-energy-module cII_energy_candidates:E_cII_C \
        --output results/math64_decisive_cII_test.json --verbose

The --selftest mode does NOT require an imported PDE backend; it exercises
the block-probe harness on synthetic analytically-controlled operators.

Status
------
MATURITY (v1.3.1, 2026-04-22): STAGE-α-CLOSED + DECISIVE-TEST-EXECUTABLE.
v1.0 / v1.1 / v1.2 / v1.2.1 covered the harness + bootstrap + autograd
cII JVP + multi-μ² + cII-off + argparse hotfix. v1.3 adds the Math64 §6
decisive grad-vs-impl diagnostic: given a scalar candidate functional
E_cII[Psi; params] (default: canonical Math65 candidate C), the tool
computes F_cII^grad = 2 * d E_cII / d Psi* via torch.autograd.grad,
compares it to the backend's F_cII^impl = _classII_effective_term_t,
and emits the triple (Delta_cII, r_impl, r_grad) of
Eq. math64-decisive-observables. The classification implements
Prop. math64-cii-surgery-gate:
    Case 1 (Delta_cII <= 10 * eps_fd)          -> assembly inconsistency
                                                    (local rewrite)
    Case 2 (Delta_cII ~ a_cII)                 -> design defect (no
                                                    variational parent in
                                                    the candidate's
                                                    structural class)
    Case 3 (intermediate, inconclusive)        -> try next candidate or
                                                    escalate to Math66
The canonical Math65 candidate C is shipped in
Tools/cII_energy_candidates.py; the --cII-energy-module
MODULE:FUNC flag permits user override to the A/B candidates or to
externally authored candidates for Math66 surgery triangulation.

References
----------
    docs/math/TECT-Math63-Solver-Redesign-v2.5.tex.txt §2A.3 (Step 1).
    docs/math/TECT-Math64-cII-Stage-Alpha-Audit.tex.txt §6 (decisive).
    docs/math/TECT-Math65-cII-EulerLagrange-Rewrite.tex.txt §4 (API).
    Tools/cII_energy_candidates.py          (Math65 E_cII candidates).
    tools/check_jacobian_symmetry.py v2.0   (Math63 §2A.1 policy).
    PDE/real_backend_pt_bcc_mixed_v3.py     (residual / hessian_vec).
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# sys.path bootstrap (Math63 §2A.2 compliance, mirrors continuation_mu2_v25
# v2.5.1 fix / Task #100). Without this, `python Tools/check_jacobian_blocks.py`
# invoked from the repository root raises ModuleNotFoundError on
# `math56_constants` (lives in Contents/PDE/) and on
# `real_backend_pt_bcc_mixed_v3` (likewise in Contents/PDE/).
# Inserting BOTH the PDE/ sibling directory AND the repository root makes
# `from math56_constants import build_seed_bcc` and
# `importlib.import_module('real_backend_pt_bcc_mixed_v3')` resolve
# deterministically, while leaving the caller's sys.path unmutated except
# for these two well-defined prepends.
# ---------------------------------------------------------------------------
_THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))  # .../Contents/Tools (or tools)
_REPO_ROOT_DIR = os.path.dirname(_THIS_FILE_DIR)             # .../Contents
_PDE_DIR       = os.path.join(_REPO_ROOT_DIR, "PDE")
# Note (Task #101 / #110 case-collision fix, 2026-04-22): _THIS_FILE_DIR is
# prepended so that sibling tool modules (e.g. cII_energy_candidates) can be
# imported as BARE modules without a capitalised `Tools.` package prefix.
# Python 3.12 FileFinder is case-sensitive, whereas Windows NTFS is
# case-insensitive, so hard-coding the package casing (either `Tools` or
# `tools`) is fragile. Bare sibling imports sidestep the entire problem.
for _p in (_THIS_FILE_DIR, _PDE_DIR, _REPO_ROOT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:                         # Math63 §2A.2 (narrow import catch)
    torch = None                            # type: ignore
    _TORCH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Block registry
# ---------------------------------------------------------------------------
#
# Each entry maps a human-readable block name to a pair of constructors
# that, given the live `backend` module (real_backend_pt_bcc_mixed_v3) and
# the current params dict, build:
#
#   residual_fn(Psi)          -> np.ndarray                (for FD fallback)
#   jv_fn(Psi, v)             -> np.ndarray                (analytic mat-vec)
#
# jv_fn is the PREFERRED path (avoids FD truncation error entirely). The
# FD path is retained for cII where an analytic jv is unavailable and for
# cross-validation.


BLOCK_NAMES = ["bra", "fam", "lock", "shell", "nl", "cII"]


def _build_block_residuals(backend, params: Dict[str, Any]) -> Dict[str, Callable]:
    """
    Return {block_name: residual_fn(Psi)} for each of the six additive
    pieces of real_backend_pt_bcc_mixed_v3.residual. Each residual_fn is
    fully self-contained in the sense that it returns a numpy.complex128
    array of the same shape as Psi.

    NB: we access the private `_xxx_t(Psi_t, params)` helpers of the
    backend module. This is diagnostic-tier code and is explicitly
    documented in Math63 §2A.3 as exempt from the "public API only"
    discipline that governs solver code.
    """
    if not _TORCH_AVAILABLE:
        raise RuntimeError(
            "Block probe requires torch (backend helpers are torch-only). "
            "Run on the user local machine, not the sandbox."
        )

    # Reach into the backend's private helpers. These names are pinned in
    # real_backend_pt_bcc_mixed_v3.py v3.1 and CODE_MANUAL §10.1 v3.1.
    _to_torch = getattr(backend, "_to_torch")
    _to_numpy = getattr(backend, "_to_numpy")
    _bra_t = getattr(backend, "_brazovskii_linear_term_t")
    _fam_t = getattr(backend, "_family_term_t")
    _lock_t = getattr(backend, "_locked_internal_penalty_t")
    _shell_t = getattr(backend, "_shell_bias_term_t")
    _nl_t = getattr(backend, "_local_nonlinear_term_t")
    _cII_t = getattr(backend, "_classII_effective_term_t")

    def _wrap(fn_t):
        def fn(Psi: np.ndarray) -> np.ndarray:
            Psi_t = _to_torch(Psi, params, complex_required=True)
            return _to_numpy(fn_t(Psi_t, params)).astype(np.complex128, copy=False)
        return fn

    return {
        "bra":   _wrap(_bra_t),
        "fam":   _wrap(_fam_t),
        "lock":  _wrap(_lock_t),
        "shell": _wrap(_shell_t),
        "nl":    _wrap(_nl_t),
        "cII":   _wrap(_cII_t),
    }


def _resolve_torch_jvp():
    """
    Return a callable `_torch_jvp(fn, primals, tangents) -> (fn(primals), J·v)`
    using `torch.func.jvp` if available (PyTorch >= 2.0 recommended API), else
    falling back to the still-supported `torch.autograd.functional.jvp`.

    Both functions evaluate

        lim_{t -> 0} ( fn(primals + t * tangents) - fn(primals) ) / t

    which, for a real-linear (but generally non-holomorphic) operator
    F(Psi) = A(Psi) + B(Psi̅), equals  A v + B v̄ — exactly the real-linear
    Jacobian action tested by the Math63 §2A.1 probe under the Re<·,·>
    inner product. Neither routine requires Psi to be "holomorphic-
    differentiable"; they operate on the underlying real/imag pair.

    The shim is built once and cached via closure so that a single
    `_build_block_jvp` call does not re-import per probe.
    """
    # Preferred: functional (forward-mode) JVP.
    try:
        from torch.func import jvp as _jvp_func   # type: ignore
        def _call(fn, primals, tangents):
            return _jvp_func(fn, primals, tangents)
        return _call, "torch.func.jvp"
    except Exception:
        pass
    # Fallback: double-backward JVP.
    try:
        from torch.autograd.functional import jvp as _jvp_auto   # type: ignore
        def _call(fn, primals, tangents):
            # Signature is jvp(func, inputs, v=None, create_graph=False,
            # strict=False) -> (output, jvp). Matches our needs.
            return _jvp_auto(fn, primals, v=tangents, strict=False)
        return _call, "torch.autograd.functional.jvp"
    except Exception:
        pass
    return None, None


def _build_block_jvp(
    backend,
    params: Dict[str, Any],
    cII_backend: str = "fd",
) -> Dict[str, Callable]:
    """
    Return {block_name: jv_fn(Psi, v) -> np.ndarray} where jv_fn is the
    real-linear Jacobian-vector product of the block-restricted residual.

    For linear blocks (bra, fam, lock, shell) the Jacobian-vector product
    is simply the block residual applied to `v` (Psi-independent).

    For `nl` (quartic + sextic), the analytic form matches
    real_backend_pt_bcc_mixed_v3.hessian_vec lines 517-521:

        dnl_v = lam   * (rho   * v + delta_rho * Psi)
              + gamma * (rho^2 * v + 2 * rho * delta_rho * Psi),

    with delta_rho = 2 * Re< Psi, v > pointwise, which is real-self-adjoint
    under the Re<·,·> inner product (Math63 §2A.3 Lemma 2).

    For `cII` two backends are provided:

        cII_backend="fd" (v1.1 default):
            Central-finite-difference on the block residual with
            eps_classII_hess matching backend.hessian_vec (default 5e-7).
            Carries O(eps^2) truncation and O(1/eps) cancellation noise
            (net ~1e-10 on complex128 at eps=5e-7).

        cII_backend="autograd" (v1.2 addition):
            Forward-mode JVP via torch.func.jvp (with a fallback to
            torch.autograd.functional.jvp), which evaluates the exact
            real-linear action A v + B v̄ at machine precision on
            complex128, removing the FD truncation floor entirely.
            This is the reference path for the Math63 §2A.3 Stage α
            isolation experiment: if the anti-Hermitian signal
            |Re<u,J_cII v> - Re<v,J_cII u>| survives the FD → autograd
            change at the ~4.4e-7 level, the signal is OPERATOR-
            STRUCTURAL and not an FD aliasing artifact.

    Returns numpy.complex128 arrays.
    """
    if not _TORCH_AVAILABLE:
        raise RuntimeError("Block probe requires torch (backend helpers are torch-only).")

    if cII_backend not in ("fd", "autograd"):
        raise ValueError(f"cII_backend must be 'fd' or 'autograd'; got {cII_backend!r}")

    _to_torch = getattr(backend, "_to_torch")
    _to_numpy = getattr(backend, "_to_numpy")
    _bra_t = getattr(backend, "_brazovskii_linear_term_t")
    _fam_t = getattr(backend, "_family_term_t")
    _lock_t = getattr(backend, "_locked_internal_penalty_t")
    _shell_t = getattr(backend, "_shell_bias_term_t")
    _rho_t = getattr(backend, "_rho_t")
    _cII_t = getattr(backend, "_classII_effective_term_t")

    def _linear_jv(fn_t):
        def jv(Psi: np.ndarray, v: np.ndarray) -> np.ndarray:
            v_t = _to_torch(v, params, complex_required=True)
            return _to_numpy(fn_t(v_t, params)).astype(np.complex128, copy=False)
        return jv

    def _nl_jv(Psi: np.ndarray, v: np.ndarray) -> np.ndarray:
        lam = float(params.get("quartic_lambda", params.get("lambda", 0.40)))
        gamma = float(params.get("sextic_gamma", params.get("gamma", 0.0)))
        Psi_t = _to_torch(Psi, params, complex_required=True)
        v_t = _to_torch(v, params, complex_required=True)
        rho = _rho_t(Psi_t)
        delta_rho = 2.0 * torch.real(torch.sum(torch.conj(Psi_t) * v_t, dim=0))
        dq = lam * (rho.unsqueeze(0) * v_t + delta_rho.unsqueeze(0) * Psi_t)
        ds = gamma * ((rho ** 2).unsqueeze(0) * v_t
                      + 2.0 * rho.unsqueeze(0) * delta_rho.unsqueeze(0) * Psi_t)
        return _to_numpy(dq + ds).astype(np.complex128, copy=False)

    def _cII_jv_fd(Psi: np.ndarray, v: np.ndarray) -> np.ndarray:
        eps = float(params.get("eps_classII_hess", 5e-7))
        Psi_t = _to_torch(Psi, params, complex_required=True)
        v_t = _to_torch(v, params, complex_required=True)
        fp = _cII_t(Psi_t + eps * v_t, params)
        fm = _cII_t(Psi_t - eps * v_t, params)
        return _to_numpy((fp - fm) / (2.0 * eps)).astype(np.complex128, copy=False)

    _torch_jvp, _torch_jvp_name = _resolve_torch_jvp()

    def _cII_jv_autograd(Psi: np.ndarray, v: np.ndarray) -> np.ndarray:
        if _torch_jvp is None:
            raise RuntimeError(
                "cII_backend='autograd' requires either torch.func.jvp (>= "
                "PyTorch 2.0) or torch.autograd.functional.jvp; neither was "
                "importable. Fall back to cII_backend='fd' or upgrade torch."
            )
        Psi_t = _to_torch(Psi, params, complex_required=True)
        v_t = _to_torch(v, params, complex_required=True)
        # torch.func.jvp does NOT require requires_grad=True on primals; it
        # builds its own graph for the tangent. torch.autograd.functional
        # .jvp also internally handles this. Detach defensively to avoid
        # accumulating grad into the user's Psi tensor.
        Psi_t = Psi_t.detach()
        v_t = v_t.detach()

        def _f(x: "torch.Tensor") -> "torch.Tensor":
            return _cII_t(x, params)

        _, Jv_t = _torch_jvp(_f, (Psi_t,), (v_t,))
        return _to_numpy(Jv_t).astype(np.complex128, copy=False)

    _cII_jv = _cII_jv_fd if cII_backend == "fd" else _cII_jv_autograd

    return {
        "bra":   _linear_jv(_bra_t),
        "fam":   _linear_jv(_fam_t),
        "lock":  _linear_jv(_lock_t),
        "shell": _linear_jv(_shell_t),
        "nl":    _nl_jv,
        "cII":   _cII_jv,
    }


# ---------------------------------------------------------------------------
# Block-level probe (Math63 §2A.1 Re(vdot) policy, applied per block)
# ---------------------------------------------------------------------------

def probe_block_symmetry(
    jv_fn: Callable[[np.ndarray, np.ndarray], np.ndarray],
    Psi: np.ndarray,
    n_probes: int = 5,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Apply the Math63 §2A.1 real-self-adjoint probe to a block-restricted
    Jacobian provided as a mat-vec `jv_fn(Psi, v) -> J_B v`.

    Inner product: < a, b > := np.vdot(a, b) (sesquilinear on C^n).
    Real self-adjointness: Re< u, J v > = Re< J u, v >.

    Returns a dict with keys:
        antisym_abs     : max_{i<j} |Re<u_i, J u_j> - Re<u_j, J u_i>|
        antisym_rel     : antisym_abs / ||J||_F-estimate
        rayleigh_min    : min_i  Re<u_i, J u_i>
        rayleigh_max    : max_i  Re<u_i, J u_i>
        jacobian_norm   : max_i  ||J u_i||_2      (estimate of ||J||_F/sqrt(n_probes))
        n_probes        : n_probes
        classification  : {symmetric, indefinite, asymmetric}
    """
    if n_probes not in (3, 5, 7):
        raise ValueError(f"n_probes must be 3, 5, or 7; got {n_probes}")

    is_complex = bool(np.issubdtype(Psi.dtype, np.complexfloating))
    rng = np.random.default_rng(seed=seed)

    shape = Psi.shape
    n_total = int(np.prod(shape))

    if is_complex:
        re = rng.standard_normal((n_total, n_probes))
        im = rng.standard_normal((n_total, n_probes))
        M = ((re + 1j * im) / math.sqrt(2.0)).astype(Psi.dtype, copy=False)
    else:
        M = rng.standard_normal((n_total, n_probes)).astype(Psi.dtype, copy=False)

    Q, _ = np.linalg.qr(M)
    probes = [Q[:, i].reshape(shape).astype(Psi.dtype, copy=False) for i in range(n_probes)]

    # J u_i
    jus: List[np.ndarray] = []
    jnorm_est = 0.0
    for u in probes:
        ju = jv_fn(Psi, u)
        jus.append(np.asarray(ju, dtype=Psi.dtype))
        jnorm_est = max(jnorm_est, float(np.linalg.norm(ju.ravel())))

    def _inner(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.real(np.vdot(a.ravel(), b.ravel())))

    # Rayleigh
    rayleigh = [_inner(probes[i], jus[i]) for i in range(n_probes)]

    # Off-diagonal antisymmetry
    antisym_vals: List[float] = []
    for i in range(n_probes):
        for j in range(i + 1, n_probes):
            a_ij = _inner(probes[i], jus[j])
            a_ji = _inner(probes[j], jus[i])
            antisym_vals.append(abs(a_ij - a_ji))

    max_antisym = max(antisym_vals) if antisym_vals else 0.0
    antisym_rel = max_antisym / (jnorm_est + 1e-16)

    threshold = 1e-8
    is_symmetric = antisym_rel < threshold
    rayleigh_min = min(rayleigh)
    rayleigh_max = max(rayleigh)
    is_positive = rayleigh_min > 0.0

    return {
        "antisym_abs": float(max_antisym),
        "antisym_rel": float(antisym_rel),
        "rayleigh_min": float(rayleigh_min),
        "rayleigh_max": float(rayleigh_max),
        "rayleigh_samples": [float(r) for r in rayleigh],
        "jacobian_norm": float(jnorm_est),
        "n_probes": int(n_probes),
        "threshold": float(threshold),
        "symmetric": bool(is_symmetric),
        "positive_definite": bool(is_symmetric and is_positive),
        "indefinite": bool(is_symmetric and (not is_positive)),
        "asymmetric": bool(not is_symmetric),
        "dtype_kind": "complex" if is_complex else "real",
        "inner_product": "Re(vdot)" if is_complex else "real-dot",
    }


# ---------------------------------------------------------------------------
# Top-level sweep
# ---------------------------------------------------------------------------

_CII_COUPLING_KEYS: Tuple[str, ...] = ("alpha_X", "beta_X", "cJJ", "cJK")


def _params_with_cII_off(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a shallow copy of `params` with all four Class II couplings
    {alpha_X, beta_X, cJJ, cJK} forced to 0.0. This is the structural
    kill-switch consistent with real_backend_pt_bcc_mixed_v3
    ._classII_effective_term_t line 430 early-exit: once the sum of
    absolute couplings drops below 1e-18, the Class II term returns
    torch.zeros_like(Psi_t) identically, which is exactly
    real-self-adjoint (trivially) under Re<·,·>.
    """
    out = dict(params)
    for k in _CII_COUPLING_KEYS:
        out[k] = 0.0
    return out


def run_block_sweep(
    backend,
    params: Dict[str, Any],
    Psi: np.ndarray,
    n_probes: int = 5,
    seed: int = 42,
    blocks: Optional[List[str]] = None,
    verbose: bool = False,
    cII_backend: str = "fd",
    cII_off: bool = False,
) -> Dict[str, Any]:
    """
    Apply probe_block_symmetry to each of the requested blocks (default:
    all six) at the given iterate Psi and return a combined report.

    Parameters
    ----------
    cII_backend : {"fd", "autograd"}
        Routing for the cII Jacobian-vector product (see
        _build_block_jvp). Has NO effect on the bra/fam/lock/shell/nl
        blocks (which are always analytical) and NO effect on the
        FULL-residual probe (which routes through backend.hessian_vec
        unconditionally; that path's own cII handling is central-FD
        and is therefore subject to the same O(eps^2) truncation floor
        as cII_backend='fd'). The cII arm's value of antisym_abs in
        Math63 §2A.3 Step (D3) is compared across backends to confirm
        that the 4.357e-7 anti-Hermitian signal is STRUCTURAL (equal in
        both backends up to machine noise) rather than FD-induced.

    cII_off : bool
        If True, ablate the Class II sector by zeroing its couplings
        {alpha_X, beta_X, cJJ, cJK} in a params clone for BOTH the
        per-block path (in which case the cII block is pruned from the
        requested list, since probing the identically-zero operator
        is a trivial 0/0 report) AND the FULL-residual path (which
        re-runs backend.hessian_vec on the cII-disabled params). The
        expected outcome if hypothesis S1 (Math63 §2A.3) holds is
        antisym_abs(FULL | cII_off) drops from 4.357e-7 to ~1e-13,
        confirming cII as the sole anti-Hermitian carrier.

    The full-residual probe (for cross-check) is ALSO run — when
    cII_off=False its antisym_abs must reproduce the cII block's
    antisym_abs up to the cross-block real-cancellation noise floor
    (Math63 §2A.3 Corollary: sole carrier). When cII_off=True the
    full-residual antisym_abs must collapse to the machine-precision
    Hermitian floor.
    """
    if blocks is None:
        blocks = list(BLOCK_NAMES)

    effective_params = _params_with_cII_off(params) if cII_off else params

    # When cII is structurally off, do not re-probe the trivially-zero cII
    # block; its antisym would be 0/0, which the report format cannot
    # represent cleanly.
    effective_blocks = [b for b in blocks if not (cII_off and b == "cII")]

    jvp_fns = _build_block_jvp(backend, effective_params, cII_backend=cII_backend)

    per_block: Dict[str, Any] = {}
    t0 = time.time()
    for name in effective_blocks:
        if verbose:
            print(f"[block={name}] probing ...", file=sys.stderr)
        t_block = time.time()
        rep = probe_block_symmetry(jvp_fns[name], Psi, n_probes=n_probes, seed=seed)
        rep["wall_s"] = float(time.time() - t_block)
        rep["cII_backend_applied"] = cII_backend if name == "cII" else "n/a"
        per_block[name] = rep

    # Full-residual reference (via backend.hessian_vec)
    hessian_vec = getattr(backend, "hessian_vec")

    def _full_jv(Psi_arr: np.ndarray, v_arr: np.ndarray) -> np.ndarray:
        return hessian_vec(Psi_arr, v_arr, effective_params)

    if verbose:
        tag = "FULL (cII-off)" if cII_off else "FULL"
        print(f"[block={tag}] probing (via backend.hessian_vec) ...", file=sys.stderr)
    t_full = time.time()
    full_rep = probe_block_symmetry(_full_jv, Psi, n_probes=n_probes, seed=seed)
    full_rep["wall_s"] = float(time.time() - t_full)
    full_rep["cII_off_applied"] = bool(cII_off)

    mu2_val = effective_params.get("mu2", params.get("mu2", None))

    return {
        "per_block": per_block,
        "full": full_rep,
        "shape": list(Psi.shape),
        "dtype": str(Psi.dtype),
        "n_probes": int(n_probes),
        "seed": int(seed),
        "mu2": (float(mu2_val) if mu2_val is not None else None),
        "cII_backend": cII_backend,
        "cII_off": bool(cII_off),
        "blocks_requested": list(blocks),
        "blocks_probed": list(effective_blocks),
        "wall_s_total": float(time.time() - t0),
        "math_note": "Math63 §2A.3 Step 1 / Stage α",
        "tool_version": "check_jacobian_blocks v1.3.1",
    }


def run_multi_mu2_sweep(
    backend,
    params: Dict[str, Any],
    N: int,
    mu2_list: List[float],
    sigma: float = 0.01,
    n_probes: int = 5,
    seed: int = 42,
    blocks: Optional[List[str]] = None,
    verbose: bool = False,
    cII_backend: str = "fd",
    cII_off: bool = False,
    seed_builder: Optional[Callable[[int, Dict[str, Any], float], np.ndarray]] = None,
) -> Dict[str, Any]:
    """
    Math63 §2A.3 Stage α: loop `run_block_sweep` over a user-supplied
    list of continuation points mu2 ∈ {mu2_1, ..., mu2_K} using a FRESH
    thermal BCC seed at each point (the seed is recomputed per mu2 via
    `seed_builder`, defaulting to math56_constants.build_seed_bcc). This
    mirrors the mu2-independence audit of tools/check_jacobian_symmetry
    v2.0 that produced the 2.66e-4 signature originally, and will now
    confirm (or falsify) whether the FD → autograd cII route is
    mu2-independent as predicted by Math63 §2A.3 Corollary (sole carrier).

    Returns a dict with keys:
        "sweep"        : list of per-mu2 run_block_sweep reports.
        "N"            : grid dimension.
        "mu2_list"     : the list as supplied.
        "cII_backend"  : routing tag.
        "cII_off"      : ablation tag.
        "tool_version" : "check_jacobian_blocks v1.2".
    """
    if seed_builder is None:
        seed_builder = _build_seed

    sweep: List[Dict[str, Any]] = []
    for mu2 in mu2_list:
        params_local = dict(params)
        params_local["mu2"] = float(mu2)
        Psi = seed_builder(N, params_local, sigma)
        if verbose:
            print(
                f"\n[sweep] mu2={float(mu2):+.6e}  N={N}  cII_backend={cII_backend}"
                f"  cII_off={cII_off}",
                file=sys.stderr,
            )
        rep = run_block_sweep(
            backend=backend,
            params=params_local,
            Psi=Psi,
            n_probes=n_probes,
            seed=seed,
            blocks=blocks,
            verbose=verbose,
            cII_backend=cII_backend,
            cII_off=cII_off,
        )
        sweep.append(rep)

    return {
        "sweep": sweep,
        "N": int(N),
        "mu2_list": [float(x) for x in mu2_list],
        "n_probes": int(n_probes),
        "seed": int(seed),
        "cII_backend": cII_backend,
        "cII_off": bool(cII_off),
        "math_note": "Math63 §2A.3 Stage α (multi-mu2 sweep)",
        "tool_version": "check_jacobian_blocks v1.3.1",
    }


# ---------------------------------------------------------------------------
# v1.3 decisive grad-vs-impl diagnostic (Math64 §6 / Math65 §4)
# ---------------------------------------------------------------------------
#
# Given a scalar candidate functional E_cII[Psi; params], compute
#
#     F_cII^grad(Psi) = 2 * d E_cII / d Psi*   (Wirtinger; Math63 §2A.2 Lem. 2)
#     F_cII^impl(Psi) = backend._classII_effective_term_t(Psi; params)
#
# and emit (Delta_cII, r_impl, r_grad) per Math64 §6 Eq. math64-decisive-
# observables. Classification per Prop. math64-cii-surgery-gate.
#
# The implementation computes the Wirtinger gradient via autograd on the
# REAL and IMAGINARY parts of Psi, reconstituted as
#
#     d E / d Psi* = 0.5 * (d E / d Psi_R + i d E / d Psi_I)
#
# which is the standard complex-autograd identity; torch.autograd.grad
# on a real scalar w.r.t. a complex tensor natively returns the
# conjugate-Wirtinger derivative (d E / d Psi*), so the factor-of-2 is
# the only adjustment needed to match backend residual conventions.

def _compute_F_cII_impl(backend, Psi: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
    """Wrap backend._classII_effective_term_t to return numpy.complex128."""
    if not _TORCH_AVAILABLE:
        raise RuntimeError("Decisive test requires torch.")
    _to_torch = getattr(backend, "_to_torch")
    _to_numpy = getattr(backend, "_to_numpy")
    _cII_t = getattr(backend, "_classII_effective_term_t")
    Psi_t = _to_torch(Psi, params, complex_required=True)
    with torch.no_grad():
        F_impl_t = _cII_t(Psi_t, params)
    return _to_numpy(F_impl_t).astype(np.complex128, copy=False)


def _compute_F_cII_grad(
    candidate_fn: Callable,
    backend,
    Psi: np.ndarray,
    params: Dict[str, Any],
) -> np.ndarray:
    """
    Evaluate the candidate functional E_cII and return the Wirtinger gradient

        F_cII^grad = 2 * d E_cII / d Psi*

    PyTorch convention: torch.autograd.grad on a real scalar L w.r.t. a
    complex tensor z returns  conj(dL/dz) = dL/dz*  (per PyTorch
    complex-autograd spec, mirrored in backend.hessian_vec's use of
    autograd). The factor of 2 promotes the Wirtinger conjugate derivative
    to the full real-linear residual component, matching
    Math63 §2A.2 Lemma 2 and the F_bra / F_nl block conventions of the
    backend.
    """
    if not _TORCH_AVAILABLE:
        raise RuntimeError("Decisive test requires torch.")
    _to_torch = getattr(backend, "_to_torch")
    _to_numpy = getattr(backend, "_to_numpy")

    Psi_t = _to_torch(Psi, params, complex_required=True)
    Psi_t = Psi_t.detach().clone().requires_grad_(True)

    E = candidate_fn(Psi_t, params)
    if not isinstance(E, torch.Tensor) or E.dim() != 0:
        raise ValueError(
            f"Candidate E_cII must return a 0-dim torch.Tensor (real scalar); "
            f"got {type(E).__name__} with shape {getattr(E, 'shape', 'n/a')}."
        )
    if E.is_complex():
        # The functional must be real; if the caller supplied a complex E,
        # take the real part but warn in the report (caller checks).
        E = E.real

    grad_t, = torch.autograd.grad(E, Psi_t, create_graph=False, retain_graph=False)
    # grad_t = dE/dPsi* (conjugate Wirtinger). Promote by factor 2 to
    # match the residual convention of F_bra / F_nl.
    F_grad_t = 2.0 * grad_t
    return _to_numpy(F_grad_t).astype(np.complex128, copy=False)


def _norm_F(F: np.ndarray) -> float:
    """Frobenius norm on the flat view."""
    return float(np.linalg.norm(F.ravel()))


def _compute_cos_theta(F_impl: np.ndarray, F_grad: np.ndarray) -> float:
    """
    Compute the cosine of the angle between F_impl and F_grad via the
    polarisation identity (Math65 Eq. math65-polarization):

        Delta^2 = ||F_impl||^2 + ||F_grad||^2 - 2 Re<F_impl, F_grad>

    Rearranged:
        Re<F_impl, F_grad> = (||F_impl||^2 + ||F_grad||^2 - Delta^2) / 2

    Then: cos_theta = Re<F_impl, F_grad> / (||F_impl|| ||F_grad||)

    Returns NaN if either norm is zero.
    """
    F_impl_flat = F_impl.ravel()
    F_grad_flat = F_grad.ravel()

    # Compute norms
    norm_impl = np.linalg.norm(F_impl_flat)
    norm_grad = np.linalg.norm(F_grad_flat)

    if norm_impl < 1e-30 or norm_grad < 1e-30:
        return np.nan

    # Compute inner product (real part)
    inner_product = np.real(np.dot(np.conj(F_impl_flat), F_grad_flat))

    cos_theta = inner_product / (norm_impl * norm_grad)
    return float(cos_theta)


def _compute_cos_theta_pathX(
    A_v: np.ndarray,
    P_A_v: np.ndarray,
) -> float:
    """
    Compute the cos-theta Path-X channel-localisation classifier (Math66 Path-X diagnostic).

    The observable is defined as:
        cos_theta_pathX := Re<P_cII(A v), A v> / (||P_cII(A v)|| ||A v||)

    where:
      - A v = (J - J^dagger) v is the anti-Hermitian Jacobian residue,
      - P_cII is the channel projector (Math73 Def. 1),
      - the prediction (Path-X hypothesis) is cos_theta_pathX ≈ 1.

    This is a stricter classifier than the magnitude-ratio eta_chan of Math73,
    because it directly tests the *directional* alignment, not just the
    magnitude of the channel projection. Per Math65 Rem. math65-tool-v1p4-weakness
    and Math66 Path-X mandate: if cos_theta_pathX < 0.99 on random-seed (Psi, v),
    then Path-X is falsified.

    Parameters
    ----------
    A_v : ndarray
        Anti-Hermitian Jacobian residue A v = (J - J^dagger) v, shape (3, N, N, N).
    P_A_v : ndarray
        Channel-projected residue P_cII(A v), shape (3, N, N, N).

    Returns
    -------
    cos_theta : float
        Cosine of the angle between P_A_v and A_v. Returns NaN if either
        norm is zero.
    """
    A_v_flat = A_v.ravel()
    P_A_v_flat = P_A_v.ravel()

    norm_A_v = np.linalg.norm(A_v_flat)
    norm_P_A_v = np.linalg.norm(P_A_v_flat)

    if norm_A_v < 1e-30 or norm_P_A_v < 1e-30:
        return np.nan

    # Real inner product via Hermitian pairing
    inner_product = np.real(np.dot(np.conj(P_A_v_flat), A_v_flat))

    cos_theta = inner_product / (norm_P_A_v * norm_A_v)
    return float(cos_theta)


def _classify_cII_surgery_gate(
    delta_cII: float,
    r_impl: float,
    r_grad: float,
    a_cII_ref: float,
    eps_fd: float = 5e-7,
    cos_theta: Optional[float] = None,
    F_impl_norm: Optional[float] = None,
    F_grad_norm: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Apply Math64 §6 Prop. math64-cii-surgery-gate with Math65 v0.1.3
    branch (I) Class Insufficiency verdict logic (Path-X mandate).

    v1.4 enhancement (2026-04-22): Add Case 0 (directional orthogonality)
    per Math65 Rem. math65-tool-v1p4-weakness. Case 0 is triggered when:
        |cos_theta| < 1e-2  AND
        Delta_cII / max(||F_impl||, ||F_grad||) > 0.95

    This pre-filters the false-rescue signature of candidate A (v1.3.1 issue).

    Acceptance thresholds:
        Case 0 trigger:   |cos_theta| < 1e-2 AND magnitude_ratio > 0.95
                          (directional orthogonality despite scalar similarity)
        Case 1 trigger:   Delta_cII <= 10 * eps_fd
        Case 2 trigger:   Delta_cII >= 0.1 * a_cII_ref
        Case 3 otherwise.
    """
    thr_case1 = 10.0 * eps_fd
    thr_case2 = 0.1 * max(a_cII_ref, 1e-20)
    thr_orthogonal = 1e-2  # cos_theta threshold for Case 0
    thr_magnitude = 0.95   # ratio threshold for Case 0

    # Compute magnitude ratio if not supplied
    if F_impl_norm is None or F_grad_norm is None:
        magnitude_ratio = None
    else:
        denom = max(F_impl_norm, F_grad_norm)
        magnitude_ratio = delta_cII / denom if denom > 1e-30 else None

    # Case 0: directional orthogonality (v1.4 mandate)
    if (cos_theta is not None and
        magnitude_ratio is not None and
        abs(cos_theta) < thr_orthogonal and
        magnitude_ratio > thr_magnitude):
        verdict = "Case 0 — directional orthogonality (candidate outside variational class)"
        case = 0
        action = ("Candidate gradient is L2-orthogonal to F_cII^impl "
                  "(|cos_theta| < 1e-2). This rules out the candidate as "
                  "a variational parent regardless of magnitude ratios. "
                  "Per Math65 v0.1.3 Prop. math65-class-insufficient, if all "
                  "three candidates (A, B, C) show Case 0, branch (I) Class "
                  "Insufficiency is sealed and Math66 operator surgery "
                  "(Path-X in-solver Hermitian projection) is mandatory.")
        exit_code = 0
    # Case 1: assembly consistency
    elif delta_cII <= thr_case1:
        verdict = "Case 1 — assembly consistency (Delta_cII at FD floor)"
        case = 1
        action = ("Proceed with local assembly rewrite; candidate functional "
                  "is the Euler-Lagrange parent of F_cII^impl up to finite-"
                  "difference truncation.")
        exit_code = 1
    # Case 2: design defect
    elif delta_cII >= thr_case2:
        verdict = "Case 2 — design defect (Delta_cII comparable to a_cII)"
        case = 2
        action = ("Candidate functional cannot be the variational parent; "
                  "escalate to Math66 (in-solver symmetrisation OR "
                  "sector rewrite). Solver routing per Math63 Cor. "
                  "math63-2A3-solver-routing (PCG default) remains valid.")
        exit_code = 2
    # Case 3: inconclusive
    else:
        verdict = "Case 3 — inconclusive (try next candidate / tighten eps_fd)"
        case = 3
        action = ("Rerun with Math65 candidate B, then A, for triangulation. "
                  "If all three return Case 3, commission ad-hoc "
                  "bilinear-plus-projector search in Math65 v0.2.")
        exit_code = 3

    result = {
        "case": int(case),
        "verdict": verdict,
        "threshold_case1": float(thr_case1),
        "threshold_case2": float(thr_case2),
        "eps_fd_used": float(eps_fd),
        "a_cII_reference": float(a_cII_ref),
        "recommended_action": action,
        "exit_code": int(exit_code),
    }

    # Add v1.4 fields
    if cos_theta is not None:
        result["cos_theta"] = float(cos_theta)
    if magnitude_ratio is not None:
        result["magnitude_ratio"] = float(magnitude_ratio)
    if cos_theta is not None:
        result["threshold_orthogonal"] = float(thr_orthogonal)
    if magnitude_ratio is not None:
        result["threshold_magnitude"] = float(thr_magnitude)

    return result


def run_decisive_cII_test(
    backend,
    params: Dict[str, Any],
    Psi: np.ndarray,
    candidate_spec: Optional[str] = None,
    a_cII_ref: float = 4.357e-7,
    eps_fd: float = 5e-7,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Math64 §6 / Math65 §4 decisive grad-vs-impl diagnostic.

    Returns a dict with the v1.3 schema:
        {
          "candidate_spec"     : the resolved candidate name/spec,
          "F_impl_norm"        : ||F_cII^impl||_F,
          "F_grad_norm"        : ||F_cII^grad||_F,
          "delta_cII"          : ||F_cII^impl - F_cII^grad||_F,
          "r_impl"             : delta_cII / F_impl_norm,
          "r_grad"             : delta_cII / F_grad_norm,
          "classification"     : output of _classify_cII_surgery_gate,
          "math_note"          : reference citation,
          "tool_version"       : "check_jacobian_blocks v1.3",
        }
    """
    # Lazy import to avoid a torch dependency in selftest.
    # Case-agnostic sibling import (Task #101/#110 fix): the sys.path bootstrap
    # above prepends _THIS_FILE_DIR, so this bare import resolves regardless of
    # whether the on-disk folder is spelt `Tools/` or `tools/`.
    import cII_energy_candidates as _cand_mod   # type: ignore
    candidate_fn = _cand_mod.resolve_candidate(candidate_spec)
    resolved_name = getattr(candidate_fn, "__qualname__", str(candidate_fn))

    if verbose:
        print(f"[cII-grad-check] candidate = {candidate_spec!r}  "
              f"resolved -> {resolved_name}", file=sys.stderr)

    F_impl = _compute_F_cII_impl(backend, Psi, params)
    F_grad = _compute_F_cII_grad(candidate_fn, backend, Psi, params)

    F_impl_norm = _norm_F(F_impl)
    F_grad_norm = _norm_F(F_grad)
    delta = _norm_F(F_impl - F_grad)
    r_impl = delta / max(F_impl_norm, 1e-30)
    r_grad = delta / max(F_grad_norm, 1e-30)

    # v1.4: Compute cos_theta via polarisation identity (Math65 Eq. polarization)
    cos_theta = _compute_cos_theta(F_impl, F_grad)

    classification = _classify_cII_surgery_gate(
        delta_cII=delta,
        r_impl=r_impl,
        r_grad=r_grad,
        a_cII_ref=a_cII_ref,
        eps_fd=eps_fd,
        cos_theta=cos_theta,
        F_impl_norm=F_impl_norm,
        F_grad_norm=F_grad_norm,
    )

    if verbose:
        print(f"[cII-grad-check] ||F_impl||_F = {F_impl_norm:.4e}", file=sys.stderr)
        print(f"[cII-grad-check] ||F_grad||_F = {F_grad_norm:.4e}", file=sys.stderr)
        print(f"[cII-grad-check] Delta_cII    = {delta:.4e}", file=sys.stderr)
        print(f"[cII-grad-check] r_impl       = {r_impl:.4e}", file=sys.stderr)
        print(f"[cII-grad-check] r_grad       = {r_grad:.4e}", file=sys.stderr)
        if not np.isnan(cos_theta):
            print(f"[cII-grad-check] cos_theta    = {cos_theta:.4e}", file=sys.stderr)
        print(f"[cII-grad-check] verdict      = {classification['verdict']}",
              file=sys.stderr)

    return {
        "candidate_spec": candidate_spec,
        "candidate_resolved": resolved_name,
        "F_impl_norm": F_impl_norm,
        "F_grad_norm": F_grad_norm,
        "delta_cII": delta,
        "r_impl": r_impl,
        "r_grad": r_grad,
        "cos_theta": float(cos_theta) if not np.isnan(cos_theta) else None,
        "classification": classification,
        "shape": list(Psi.shape),
        "dtype": str(Psi.dtype),
        "mu2": float(params.get("mu2")) if params.get("mu2") is not None else None,
        "math_note": ("Math64 §6 Def. math64-decisive-test / Math65 §4 "
                      "Def. math65-cand-API / Math66 Path-X mandate"),
        "tool_version": "check_jacobian_blocks v1.4",
    }


# ---------------------------------------------------------------------------
# Self-test (five synthetic blocks, no torch required)
# ---------------------------------------------------------------------------

def _self_test() -> int:
    """
    Exercise `probe_block_symmetry` on five analytically-controlled
    synthetic operators that mirror the structural patterns of the TECT
    blocks. Also test the v1.4 cos_theta classifier on an orthogonal-gradient
    synthetic case. Test the Path-X cos-theta channel-localisation classifier
    (v1.4 Math66 Path-X diagnostic) on two synthetic cases:
      (7) pathX-localised: A v is fully channel-projected by construction
      (8) pathX-delocalised: A v has both channel and non-channel components
    Returns 0 on full pass, 1 otherwise.

    Cases (symmetry tests):
      (1) Diagonal real positive (mirrors fam with positive masses)        -> symmetric PD
      (2) Diagonal real with mixed sign (mirrors bra at mu^2 < 0)          -> symmetric indefinite
      (3) Random Hermitian complex (mirrors lock = k_lock (I - P0))        -> symmetric (indefinite generally)
      (4) Anti-Hermitian complex diagonal i*D                              -> asymmetric
      (5) Wirtinger-style nl block  J v = 2|c|^2 v + c^2 v*                -> symmetric under Re(vdot)
      (6) v1.4 Case-0 orthogonality: two orthogonal vectors, test _compute_cos_theta
      (7) Math66 Path-X: pathX-localised-synthetic (channel-projected by construction)
      (8) Math66 Path-X: pathX-delocalised-synthetic (both channel and non-channel parts)
    """
    import numpy as _np
    rng = _np.random.default_rng(seed=0)
    n = 16
    passed = 0
    total = 8

    # Case 1: diagonal real PD
    D1 = _np.diag(_np.abs(rng.standard_normal(n)) + 0.1).astype(_np.float64)
    Psi1 = rng.standard_normal(n).astype(_np.float64)
    r1 = probe_block_symmetry(lambda _Psi, v: D1 @ v, Psi1, n_probes=5)
    ok1 = r1["symmetric"] and r1["positive_definite"]
    passed += int(ok1)

    # Case 2: diagonal real indefinite (force both signs large — random
    # Gaussian diagonals can produce probes that happen to avoid the
    # negative subspace; cf. self-test v1.0 report 2026-04-22).
    d = _np.concatenate([_np.ones(n // 2) * 2.0, -_np.ones(n // 2) * 2.0])
    D2 = _np.diag(d).astype(_np.float64)
    Psi2 = rng.standard_normal(n).astype(_np.float64)
    r2 = probe_block_symmetry(lambda _Psi, v: D2 @ v, Psi2, n_probes=5)
    ok2 = r2["symmetric"] and r2["indefinite"]
    passed += int(ok2)

    # Case 3: random Hermitian complex
    A = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    H = 0.5 * (A + A.conj().T)
    Psi3 = (rng.standard_normal(n) + 1j * rng.standard_normal(n)).astype(_np.complex128)
    r3 = probe_block_symmetry(lambda _Psi, v: H @ v, Psi3, n_probes=5)
    ok3 = r3["symmetric"]
    passed += int(ok3)

    # Case 4: anti-Hermitian complex diagonal
    iD = _np.diag(1j * rng.standard_normal(n)).astype(_np.complex128)
    Psi4 = (rng.standard_normal(n) + 1j * rng.standard_normal(n)).astype(_np.complex128)
    r4 = probe_block_symmetry(lambda _Psi, v: iD @ v, Psi4, n_probes=5)
    ok4 = r4["asymmetric"]
    passed += int(ok4)

    # Case 5: Wirtinger nl-block J v = 2 |c|^2 v + c^2 conj(v), with c complex.
    # This is real-self-adjoint under Re< u, J v >.
    c = (rng.standard_normal(n) + 1j * rng.standard_normal(n)).astype(_np.complex128)
    rho = _np.abs(c) ** 2

    def nl_jv(_Psi, v):
        return 2.0 * rho * v + (c ** 2) * _np.conj(v)

    Psi5 = c.copy()
    r5 = probe_block_symmetry(nl_jv, Psi5, n_probes=5)
    ok5 = r5["symmetric"]
    passed += int(ok5)

    # Case 6 (v1.4): Test _compute_cos_theta on two orthogonal synthetic vectors
    # Construct F_impl = (1, 0, 0, ..., 0) and F_grad = (0, 1, 0, ..., 0) which
    # are orthogonal; cos_theta should be ~0. Then check that classification
    # emits Case 0 when Delta / max(norms) > 0.95 (which it will, since
    # Delta ≈ sqrt(2) and max(norms) = 1).
    F_impl_orth = _np.zeros(n, dtype=_np.complex128)
    F_impl_orth[0] = 1.0
    F_grad_orth = _np.zeros(n, dtype=_np.complex128)
    F_grad_orth[1] = 1.0

    cos_theta_orth = _compute_cos_theta(F_impl_orth, F_grad_orth)
    ok6_costheta = abs(cos_theta_orth) < 1e-10  # Should be ~0

    # Now test the classification logic with Case 0 thresholds
    F_impl_norm_orth = _np.linalg.norm(F_impl_orth)
    F_grad_norm_orth = _np.linalg.norm(F_grad_orth)
    delta_orth = _np.linalg.norm(F_impl_orth - F_grad_orth)
    magnitude_ratio_orth = delta_orth / max(F_impl_norm_orth, F_grad_norm_orth)

    class_result_orth = _classify_cII_surgery_gate(
        delta_cII=delta_orth,
        r_impl=1.0,  # dummy
        r_grad=1.0,  # dummy
        a_cII_ref=1e-7,  # dummy reference
        eps_fd=5e-7,
        cos_theta=cos_theta_orth,
        F_impl_norm=F_impl_norm_orth,
        F_grad_norm=F_grad_norm_orth,
    )
    ok6_case0 = class_result_orth["case"] == 0
    ok6 = ok6_costheta and ok6_case0
    passed += int(ok6)

    # Case 7 (v1.4 Path-X): pathX-localised-synthetic
    # Construct A_v = (1, 0, 0, ..., 0) (complex vector in C^n)
    # and P_A_v = A_v (already channel-projected by construction).
    # cos_theta_pathX should be 1.0 ± 1e-13 (machine precision).
    A_v_loc = _np.zeros(n, dtype=_np.complex128)
    A_v_loc[0] = 1.0 + 0.0j
    P_A_v_loc = A_v_loc.copy()  # By construction, already "projected"

    cos_theta_loc = _compute_cos_theta_pathX(A_v_loc, P_A_v_loc)
    ok7 = abs(cos_theta_loc - 1.0) < 1e-13  # Should be 1.0 ± machine epsilon
    passed += int(ok7)

    # Case 8 (v1.4 Path-X): pathX-delocalised-synthetic
    # Construct A_v with both "channel" and "non-channel" components:
    # A_v = [1, 0, ..., 0] + i*[0, 1, 0, ..., 0]  (complex vector in C^n)
    # P_A_v = projection that keeps only the first component
    # = [1, 0, ..., 0] (magnitude_ratio ≈ 1/sqrt(2) ≈ 0.707)
    # Then cos_theta should be close to 0.707, < 0.99.
    A_v_deloc = _np.zeros(n, dtype=_np.complex128)
    A_v_deloc[0] = 1.0 + 0.0j
    A_v_deloc[1] = 0.0 + 1.0j  # Orthogonal component
    P_A_v_deloc = _np.zeros(n, dtype=_np.complex128)
    P_A_v_deloc[0] = 1.0 + 0.0j  # Only keep first component

    cos_theta_deloc = _compute_cos_theta_pathX(A_v_deloc, P_A_v_deloc)
    ok8 = cos_theta_deloc < 0.99 and cos_theta_deloc > 0.69  # Within range (approx 1/sqrt(2))
    passed += int(ok8)

    labels = ["diag-real-PD", "diag-real-indef", "Hermitian-complex",
              "anti-Hermitian-complex", "nl-Wirtinger", "orthogonal-vectors-case0",
              "pathX-localised-synthetic", "pathX-delocalised-synthetic"]
    results = [ok1, ok2, ok3, ok4, ok5, ok6, ok7, ok8]
    reports = [r1, r2, r3, r4, r5, None, None, None]  # Cases 6, 7, 8 have no block_symmetry report
    for i, (label, ok, rep) in enumerate(zip(labels, results, reports)):
        status = "PASS" if ok else "FAIL"
        if rep is not None:
            print(f"[self-test] {label:28s} {status}  "
                  f"antisym/|J| = {rep['antisym_rel']:.3e}  "
                  f"Rayleigh range = [{rep['rayleigh_min']:+.3e}, {rep['rayleigh_max']:+.3e}]")
        elif i == 5:
            # Case 6: report cos_theta and classification verdict for orthogonal-vectors-case0
            print(f"[self-test] {label:28s} {status}  "
                  f"cos_theta = {cos_theta_orth:.3e}  "
                  f"mag_ratio = {magnitude_ratio_orth:.3e}  "
                  f"verdict = {class_result_orth['verdict']}")
        elif i == 6:
            # Case 7: pathX-localised-synthetic
            print(f"[self-test] {label:28s} {status}  "
                  f"cos_theta_pathX = {cos_theta_loc:.3e}  "
                  f"expected = 1.0  "
                  f"error = {abs(cos_theta_loc - 1.0):.3e}")
        elif i == 7:
            # Case 8: pathX-delocalised-synthetic
            print(f"[self-test] {label:28s} {status}  "
                  f"cos_theta_pathX = {cos_theta_deloc:.3e}  "
                  f"expected < 0.99  "
                  f"magnitude_ratio ~ 0.707")

    print(f"[self-test] {passed}/{total} PASS")
    return 0 if passed == total else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _build_seed(N: int, params: Dict[str, Any], sigma: float = 0.01) -> np.ndarray:
    """Construct a complex128 BCC seed via math56_constants.build_seed_bcc."""
    # Defer the import: self-test path must not require the TECT package.
    from math56_constants import build_seed_bcc  # type: ignore
    return build_seed_bcc(N=N, mode="thermal", sigma=sigma, complex_seed=True, seed=42)


def _glue_negative_list_value(argv: List[str], option_name: str) -> List[str]:
    """
    Preprocess argv to fold ``--opt <neg-csv>`` into ``--opt=<neg-csv>``.

    Python's ``argparse`` refuses to accept a value that begins with ``-``
    (e.g. ``-1.0,-0.8,-0.6,...``) as the argument of a string-typed option
    when given in the space-separated form, because argparse cannot
    disambiguate between "option-value that happens to look negative" and
    "an unknown optional flag". The standard workaround is the equals-sign
    form (``--opt=-1.0,...``). This helper transparently promotes the
    space-separated form to the equals form BEFORE argparse sees it, so
    both invocation styles succeed. Only a token matching ``option_name``
    whose following token looks like a negative CSV (starts with ``-``,
    contains ``,`` or a digit) is rewritten; untouched otherwise.

    This is a purely cosmetic CLI-ergonomics fix; no semantic change to
    the probe policy (Math63 §2A.1 Re<u,Jv>=Re<Ju,v>).
    """
    out: List[str] = []
    i = 0
    n = len(argv)
    while i < n:
        tok = argv[i]
        if tok == option_name and (i + 1) < n:
            nxt = argv[i + 1]
            # Trigger only when the following token looks like a value
            # that argparse would misread as a flag: starts with '-' and
            # is not itself a known long option (i.e. contains a comma or
            # a digit after the leading '-').
            if nxt.startswith("-") and len(nxt) > 1 and (
                "," in nxt or nxt[1].isdigit() or (nxt[1] == "." and len(nxt) > 2 and nxt[2].isdigit())
            ):
                out.append(f"{option_name}={nxt}")
                i += 2
                continue
        out.append(tok)
        i += 1
    return out


def _print_single_point_report(report: Dict[str, Any], blocks: List[str]) -> None:
    """Pretty-print one run_block_sweep report to stderr (Stage α row format)."""
    mu2 = report.get("mu2", None)
    cII_bk = report.get("cII_backend", "fd")
    cII_off = report.get("cII_off", False)
    header = (f"\n===== Math63 §2A.3 block-decomposition probe  "
              f"mu2={('{:+.6e}'.format(mu2) if mu2 is not None else 'n/a')}  "
              f"cII_backend={cII_bk}  cII_off={cII_off}  =====")
    print(header, file=sys.stderr)
    print(f"  {'block':6s}  {'antisym_abs':>14s}  {'antisym/||J||':>14s}  "
          f"{'||J||':>12s}  {'Rayleigh':>22s}  {'class':>10s}", file=sys.stderr)

    blocks_probed = report.get("blocks_probed", blocks)
    for name in blocks_probed:
        r = report["per_block"][name]
        cls = ("SYM-PD" if r["positive_definite"]
               else ("SYM-IND" if r["indefinite"] else "ASYM"))
        print(f"  {name:6s}  {r['antisym_abs']:14.4e}  {r['antisym_rel']:14.4e}  "
              f"{r['jacobian_norm']:12.4e}  "
              f"[{r['rayleigh_min']:+.3e},{r['rayleigh_max']:+.3e}]  {cls:>10s}",
              file=sys.stderr)
    r = report["full"]
    cls = ("SYM-PD" if r["positive_definite"]
           else ("SYM-IND" if r["indefinite"] else "ASYM"))
    full_label = "FULL*" if cII_off else "FULL"
    print(f"  {full_label:6s}  {r['antisym_abs']:14.4e}  {r['antisym_rel']:14.4e}  "
          f"{r['jacobian_norm']:12.4e}  "
          f"[{r['rayleigh_min']:+.3e},{r['rayleigh_max']:+.3e}]  {cls:>10s}",
          file=sys.stderr)


def _exit_code_from_sweep_report(report: Dict[str, Any], blocks: List[str]) -> int:
    """0 iff every probed block AND the FULL residual pass the 1e-8 Hermitian gate."""
    probed = report.get("blocks_probed", blocks)
    all_symmetric = all(report["per_block"][b]["symmetric"] for b in probed)
    all_symmetric = all_symmetric and report["full"]["symmetric"]
    return 0 if all_symmetric else 11


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Math63 §2A.3 Stage α: block-decomposition Jacobian probe")
    parser.add_argument("--config", type=str, default=None,
                        help="backend config JSON (mirrors continuation_mu2_v25 schema)")
    parser.add_argument("--N", type=int, default=32, help="grid dimension")
    parser.add_argument("--mu2", type=float, default=-0.5,
                        help="current continuation point; overrides config['mu2'] if given")
    parser.add_argument("--mu2-list", type=str, default=None,
                        help="comma-separated list of mu2 points (e.g. '-1.0,-0.8,-0.6,"
                             "-0.4,-0.2,-0.1'); when present, supersedes --mu2 and "
                             "triggers the Stage α multi-point driver")
    parser.add_argument("--n-probes", type=int, default=5, choices=[3, 5, 7])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sigma", type=float, default=0.01, help="seed noise scale")
    parser.add_argument("--blocks", type=str, default=",".join(BLOCK_NAMES),
                        help="comma-separated subset of {bra,fam,lock,shell,nl,cII}")
    parser.add_argument("--backend", type=str, default="fd",
                        choices=["fd", "autograd"],
                        help="cII Jacobian-vector product backend: "
                             "'fd' = central-finite-difference (v1.1 default, O(5e-7) "
                             "truncation floor), 'autograd' = forward-mode JVP via "
                             "torch.func.jvp (machine-precision, Math63 §2A.3 Stage α "
                             "reference path)")
    parser.add_argument("--cII-off", action="store_true",
                        help="ablate the Class II sector by zeroing {alpha_X, beta_X, "
                             "cJJ, cJK} in a params clone; prunes cII from the block "
                             "sweep and re-runs the FULL-residual probe with cII "
                             "structurally absent (Math63 §2A.3 hypothesis S1 test)")
    parser.add_argument("--cII-grad-check", action="store_true",
                        help="run the Math64 §6 / Math65 §4 decisive grad-vs-impl "
                             "diagnostic: compute F_cII^grad = 2 d E_cII/d Psi* via "
                             "torch.autograd.grad and compare to F_cII^impl; emit "
                             "(Delta_cII, r_impl, r_grad) triple and classify per "
                             "Prop. math64-cii-surgery-gate. When set, this "
                             "SUPERSEDES the block-sweep path.")
    parser.add_argument("--cII-energy-module", type=str, default=None,
                        help="plugin spec for E_cII candidate, one of "
                             "{'A','B','C','default'} (registry lookup) or "
                             "'MODULE:FUNC' (external). Defaults to canonical "
                             "Math65 candidate C.")
    parser.add_argument("--a-cII-ref", type=float, default=4.357e-7,
                        help="reference |F_cII^impl - F_cII^impl^T|_F at seed "
                             "(Math64 Theorem math64-full-sympd, Stage α closure). "
                             "Used to set the Case-2 threshold in the surgery gate.")
    parser.add_argument("--eps-fd", type=float, default=5e-7,
                        help="finite-difference epsilon used for the Case-1 "
                             "assembly-consistency threshold.")
    parser.add_argument("--output", type=str, default=None, help="JSON report path")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--selftest", action="store_true")

    # Intercept --selftest before argparse (matches v2.0 convention)
    if argv is None:
        argv = sys.argv[1:]
    if "--selftest" in argv:
        return _self_test()

    # v1.2.1 argparse usability hotfix: argparse rejects a value that starts
    # with '-' (e.g. '-1.0,-0.8,...') when passed to a string-typed option
    # via the space-separated form, interpreting it as an unknown flag.
    # Glue '--mu2-list <neg-csv>' into '--mu2-list=<neg-csv>' so BOTH
    # invocation forms succeed. The equals-sign form is unaffected because
    # it is already a single token.
    argv = _glue_negative_list_value(argv, "--mu2-list")

    args = parser.parse_args(argv)
    if args.selftest:
        return _self_test()

    if not _TORCH_AVAILABLE:
        print("ERROR: torch not available; live block sweep cannot run in this process.",
              file=sys.stderr)
        return 3

    if args.config is None:
        print("ERROR: --config <path> is required for live sweep.", file=sys.stderr)
        return 2

    params = _load_config(args.config)
    # Note: mu2 is only written into params when the single-point path is
    # taken. For the multi-mu2 path, run_multi_mu2_sweep writes each mu2
    # into its own params clone per iteration.

    blocks = [b.strip() for b in args.blocks.split(",") if b.strip()]
    for b in blocks:
        if b not in BLOCK_NAMES:
            print(f"ERROR: unknown block '{b}'; valid: {BLOCK_NAMES}", file=sys.stderr)
            return 2

    backend = importlib.import_module("real_backend_pt_bcc_mixed_v3")

    # ---------------------------------------------------------------
    # v1.3 decisive grad-vs-impl driver (Math64 §6 / Math65 §4).
    # When enabled, this path SUPERSEDES the block-sweep output and
    # emits the decisive diagnostic only. Runs at the --mu2 point
    # (or the first entry of --mu2-list if both are given).
    # ---------------------------------------------------------------
    if args.cII_grad_check:
        mu2_target = args.mu2
        if args.mu2_list is not None:
            try:
                mu2_parsed = [float(x.strip()) for x in args.mu2_list.split(",")
                              if x.strip()]
                if mu2_parsed:
                    mu2_target = mu2_parsed[0]
            except ValueError:
                print(f"ERROR: --mu2-list parse error: {args.mu2_list!r}",
                      file=sys.stderr)
                return 2
        params["mu2"] = float(mu2_target)
        Psi = _build_seed(args.N, params, sigma=args.sigma)

        print("\n===== Math64 §6 / Math65 §4 decisive grad-vs-impl diagnostic =====",
              file=sys.stderr)
        print(f"  N={args.N}  mu2={mu2_target:+.6e}  "
              f"candidate={args.cII_energy_module or 'default (C)'}  "
              f"a_cII_ref={args.a_cII_ref:.3e}  eps_fd={args.eps_fd:.3e}",
              file=sys.stderr)

        decisive = run_decisive_cII_test(
            backend=backend,
            params=params,
            Psi=Psi,
            candidate_spec=args.cII_energy_module,
            a_cII_ref=args.a_cII_ref,
            eps_fd=args.eps_fd,
            verbose=args.verbose,
        )

        # Pretty-print verdict block
        cls = decisive["classification"]
        print("", file=sys.stderr)
        print(f"  ||F_impl||_F = {decisive['F_impl_norm']:.6e}", file=sys.stderr)
        print(f"  ||F_grad||_F = {decisive['F_grad_norm']:.6e}", file=sys.stderr)
        print(f"  Delta_cII    = {decisive['delta_cII']:.6e}", file=sys.stderr)
        print(f"  r_impl       = {decisive['r_impl']:.6e}", file=sys.stderr)
        print(f"  r_grad       = {decisive['r_grad']:.6e}", file=sys.stderr)
        print(f"  thr(Case 1)  = {cls['threshold_case1']:.3e}", file=sys.stderr)
        print(f"  thr(Case 2)  = {cls['threshold_case2']:.3e}", file=sys.stderr)
        print(f"  verdict      = {cls['verdict']}", file=sys.stderr)
        print(f"  action       = {cls['recommended_action']}", file=sys.stderr)

        if args.output:
            os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as fh:
                json.dump({"cII_grad_check": decisive}, fh, indent=2)
            print(f"  wrote: {args.output}", file=sys.stderr)

        # Exit code: 0 iff Case 1 (assembly consistency closed).
        return 0 if cls["case"] == 1 else (12 if cls["case"] == 2 else 13)

    # ---------------------------------------------------------------
    # Multi-mu2 driver (Stage α path)
    # ---------------------------------------------------------------
    if args.mu2_list is not None:
        try:
            mu2_list = [float(x.strip()) for x in args.mu2_list.split(",") if x.strip()]
        except ValueError:
            print(f"ERROR: --mu2-list must be a comma-separated list of floats; "
                  f"got {args.mu2_list!r}", file=sys.stderr)
            return 2
        if not mu2_list:
            print("ERROR: --mu2-list produced an empty list after parsing.", file=sys.stderr)
            return 2

        multi_report = run_multi_mu2_sweep(
            backend=backend,
            params=params,
            N=args.N,
            mu2_list=mu2_list,
            sigma=args.sigma,
            n_probes=args.n_probes,
            seed=args.seed,
            blocks=blocks,
            verbose=args.verbose,
            cII_backend=args.backend,
            cII_off=args.cII_off,
        )

        # Pretty-print per-point summaries + aggregate
        print("\n===== Math63 §2A.3 Stage α multi-mu2 sweep =====", file=sys.stderr)
        print(f"  N={args.N}  n_probes={args.n_probes}  seed={args.seed}  "
              f"cII_backend={args.backend}  cII_off={args.cII_off}  "
              f"K_mu2={len(mu2_list)}", file=sys.stderr)
        for rep in multi_report["sweep"]:
            _print_single_point_report(rep, blocks)
        # Stage α aggregate table
        print("\n[aggregate] antisym_abs per mu2 (one row per point):", file=sys.stderr)
        probed_any = multi_report["sweep"][0].get("blocks_probed", blocks)
        hdr = "  " + "mu2".rjust(14) + "  " + "  ".join(
            [b.rjust(10) for b in probed_any] + ["FULL".rjust(10)]
        )
        print(hdr, file=sys.stderr)
        for rep in multi_report["sweep"]:
            row = [f"  {rep['mu2']:+.6e}"]
            for b in probed_any:
                row.append(f"{rep['per_block'][b]['antisym_abs']:10.3e}")
            row.append(f"{rep['full']['antisym_abs']:10.3e}")
            print("  ".join(row), file=sys.stderr)

        if args.output:
            os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as fh:
                json.dump(multi_report, fh, indent=2)
            print(f"  wrote: {args.output}", file=sys.stderr)

        # Exit code: 0 iff EVERY point in the sweep passes the Hermitian gate.
        codes = [_exit_code_from_sweep_report(rep, blocks) for rep in multi_report["sweep"]]
        return 0 if all(c == 0 for c in codes) else 11

    # ---------------------------------------------------------------
    # Single-mu2 driver (v1.1 path, preserved for backward compat)
    # ---------------------------------------------------------------
    params["mu2"] = args.mu2
    Psi = _build_seed(args.N, params, sigma=args.sigma)

    report = run_block_sweep(
        backend=backend,
        params=params,
        Psi=Psi,
        n_probes=args.n_probes,
        seed=args.seed,
        blocks=blocks,
        verbose=args.verbose,
        cII_backend=args.backend,
        cII_off=args.cII_off,
    )

    _print_single_point_report(report, blocks)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print(f"  wrote: {args.output}", file=sys.stderr)

    return _exit_code_from_sweep_report(report, blocks)


if __name__ == "__main__":
    sys.exit(main())
