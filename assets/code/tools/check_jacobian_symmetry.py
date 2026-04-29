#!/usr/bin/env python3
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math63-Solver-Redesign-v2p5-2026-04-22
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v2.0
# Sync doc      : /Contents/Docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-22
# Notes         : Jacobian symmetry classification tool for v2.5 adaptive solver.
#                 v2.0: complex-Hermitian probe policy (Math63 §2A.1 addendum).
# === TECT VERSION HEADER END ===
"""
Jacobian Symmetry Classification Tool (v2.0)
============================================

Diagnostic tool for Newton-Krylov v2.5 to classify the Jacobian (Hessian) at a
given iterate as SPD, symmetric-indefinite, or asymmetric, in either real or
complex Hilbert space.

Trigger/Evidence/Decision (v1.2 → v2.0, 2026-04-22, Math63 §2A.1 addendum):
- Trigger (v2.0): run_v25_diagnostic 2026-04-22 (R-2026-04-22-001) emitted
            `UserWarning: Casting complex values to real discards the
            imaginary part` at line 102 of v1.2, with `antisym=2.84e-04`
            identical across all six μ² probe points — a cast artifact,
            not a Jacobian observable.
- Evidence (v2.0): Three coupled defects in v1.2 broke Math63 §2A
            classification for complex128 BCC-channel operators:
            (5a) silent `torch.from_numpy(complex128).to(float64)` casting,
            (5b) real-valued probe generation regardless of operator dtype,
            (5c) bilinear `torch.dot` / `np.dot` instead of sesquilinear
                 `torch.vdot` / `np.vdot`.
- Decision (v2.0): Preserve input dtype end-to-end. Branch on complex dtype:
            generate complex-Gaussian probes, compute the real inner product
            Re⟨u, Jv⟩ = Re(u^H J v) via `vdot`, and classify using the
            Math63 §2A.1 real-self-adjoint criterion (works for both
            complex-Hermitian and Wirtinger-type ℝ-self-adjoint operators,
            which covers the TECT GL residual with |Ψ|²Ψ nonlinearity).

Reference: see `docs/mathematical-notes/TECT-Math63-Solver-Redesign-v2.5.tex.txt`
           §2A and §2A.1 (addendum).
"""

import argparse
import json
import math
import sys
from typing import Callable, Dict, Any, List, Tuple, Optional, Union

import numpy as np

try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_complex_array(x) -> bool:
    """True iff x carries a complex dtype (torch.Tensor or numpy.ndarray)."""
    if _TORCH_AVAILABLE and isinstance(x, torch.Tensor):
        return bool(x.is_complex())
    return bool(np.issubdtype(np.asarray(x).dtype, np.complexfloating))


def _preserve_torch_dtype(x_np: np.ndarray) -> "torch.dtype":
    """Map numpy dtype to the natural torch dtype, preserving complex kind."""
    if np.issubdtype(x_np.dtype, np.complexfloating):
        return torch.complex128 if x_np.dtype == np.complex128 else torch.complex64
    if np.issubdtype(x_np.dtype, np.floating):
        return torch.float64 if x_np.dtype == np.float64 else torch.float32
    return torch.float64


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def probe_symmetry(
    residual_fn: Callable,
    x0: Union[np.ndarray, "torch.Tensor"],
    n_probes: int = 5,
    eps: float = 1e-6,
    dtype: Optional[Any] = None,
    device: str = "cpu",
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Classify Jacobian J = ∂F/∂x at x0 via finite-difference probes.

    Protocol (Math63 §2A + §2A.1):
    - Generate n_probes random orthonormal vectors {u_i} in the ambient
      space (complex Gaussian if dtype is complex, real Gaussian otherwise).
    - Compute w_i = J u_i via central FD: w_i = [F(x0+ε u_i) − F(x0−ε u_i)] / (2ε).
    - Rayleigh samples: ρ_i := Re⟨u_i, J u_i⟩ (real-valued).
    - Off-diagonal antisymmetry: α_{ij} := |Re⟨u_i, J u_j⟩ − Re⟨u_j, J u_i⟩|.

    The real-self-adjoint condition Re⟨u, Jv⟩ = Re⟨Ju, v⟩ (∀ u, v) classifies:
    - SPD                    ⇔ α_{ij}/‖J‖ < 1e-8  and  min ρ_i > 0    → PCG
    - Symmetric-indefinite   ⇔ α_{ij}/‖J‖ < 1e-8  and  min ρ_i ≤ 0    → MINRES
    - Asymmetric             ⇔ α_{ij}/‖J‖ ≥ 1e-8                        → FGMRES

    For real operators this reduces to the Math63 §2A probe (vdot = dot in ℝ).
    For complex Wirtinger-type operators (TECT GL residual), Re⟨·,·⟩ is the
    natural ℝ-inner product on ℂⁿ ≅ ℝ²ⁿ, under which the TECT Jacobian is
    self-adjoint whenever F is the gradient of a real potential.

    Args:
        residual_fn: callable(x) -> F (returns residual as tensor or array).
        x0: current iterate (torch.Tensor or numpy.ndarray), real or complex.
        n_probes: number of random vectors (3, 5, or 7; default 5).
        eps: finite-difference step size (default 1e-6).
        dtype: target dtype; default preserves x0.dtype (including complex).
        device: 'cpu' or 'cuda' if torch available.
        verbose: if True, print probe details.

    Returns:
        dict with Math63 §2A classification fields plus:
        - 'dtype_kind': 'real' or 'complex'.
        - 'inner_product': 'real-dot' (real case) or 'Re(vdot)' (complex case).
    """

    if n_probes not in (3, 5, 7):
        raise ValueError(f"n_probes must be 3, 5, or 7; got {n_probes}")

    # -----------------------------------------------------------------
    # Select backend and preserve dtype (no silent complex→real cast).
    # -----------------------------------------------------------------
    use_torch = isinstance(x0, torch.Tensor) if _TORCH_AVAILABLE else False
    if use_torch:
        x_torch = x0
        if dtype is None:
            dtype = x0.dtype
        if device is None:
            device = x0.device
    else:
        if _TORCH_AVAILABLE:
            x_np_in = np.asarray(x0)
            target_dtype = dtype if dtype is not None else _preserve_torch_dtype(x_np_in)
            x_torch = torch.from_numpy(x_np_in).to(device=device, dtype=target_dtype)
            use_torch = True
        else:
            x_np = np.asarray(x0)
            use_torch = False

    if use_torch:
        is_complex = bool(x_torch.is_complex())
    else:
        is_complex = bool(np.issubdtype(x_np.dtype, np.complexfloating))

    # -----------------------------------------------------------------
    # Generate n_probes random orthonormal vectors in the ambient field.
    # -----------------------------------------------------------------
    if use_torch:
        gen = torch.Generator(device=device)
        gen.manual_seed(42)
        n_total = x_torch.numel()
        if is_complex:
            # Complex Gaussian: CN(0, 1) = (N(0,1) + i N(0,1))/sqrt(2)
            re = torch.randn(n_total, n_probes, generator=gen, device=device, dtype=torch.float64)
            im = torch.randn(n_total, n_probes, generator=gen, device=device, dtype=torch.float64)
            M = torch.complex(re, im) / math.sqrt(2.0)
            M = M.to(x_torch.dtype)
        else:
            M = torch.randn(n_total, n_probes, generator=gen, device=device, dtype=x_torch.dtype)
        Q, _ = torch.linalg.qr(M)
        probes = [Q[:, i].reshape(x_torch.shape).to(dtype=x_torch.dtype) for i in range(n_probes)]
    else:
        rng = np.random.default_rng(seed=42)
        n_total = x_np.size
        if is_complex:
            re = rng.standard_normal((n_total, n_probes))
            im = rng.standard_normal((n_total, n_probes))
            M = ((re + 1j * im) / math.sqrt(2.0)).astype(x_np.dtype, copy=False)
        else:
            M = rng.standard_normal((n_total, n_probes)).astype(x_np.dtype, copy=False)
        Q, _ = np.linalg.qr(M)
        probes = [Q[:, i].reshape(x_np.shape) for i in range(n_probes)]

    if verbose:
        ipname = "Re(vdot)" if is_complex else "real-dot"
        print(f"Probing Jacobian symmetry with {n_probes} {('complex' if is_complex else 'real')}-Gaussian probes  (inner product: {ipname})")

    # -----------------------------------------------------------------
    # Inner-product and norm helpers — always return real Python floats.
    # -----------------------------------------------------------------
    def _inner(a, b) -> float:
        """Return Re⟨a, b⟩ = Re(a* · b) in the ambient field (vdot-based)."""
        if use_torch:
            v = torch.vdot(a.flatten(), b.flatten())
            if v.is_complex():
                return float(v.real.item())
            return float(v.item())
        else:
            v = np.vdot(a.flatten(), b.flatten())
            return float(np.real(v))

    def _norm(a) -> float:
        if use_torch:
            return float(torch.linalg.norm(a).item())
        return float(np.linalg.norm(a))

    # -----------------------------------------------------------------
    # Evaluate J u_i via central finite differences.
    # -----------------------------------------------------------------
    jacobian_probes = []
    for i, u in enumerate(probes):
        if use_torch:
            f_plus = residual_fn(x_torch + eps * u)
            f_minus = residual_fn(x_torch - eps * u)
            if isinstance(f_plus, np.ndarray):
                f_plus = torch.from_numpy(f_plus).to(device=device, dtype=x_torch.dtype)
            elif isinstance(f_plus, (float, int)):
                f_plus = torch.tensor(f_plus, dtype=x_torch.dtype, device=device)
            if isinstance(f_minus, np.ndarray):
                f_minus = torch.from_numpy(f_minus).to(device=device, dtype=x_torch.dtype)
            elif isinstance(f_minus, (float, int)):
                f_minus = torch.tensor(f_minus, dtype=x_torch.dtype, device=device)
            ju = (f_plus - f_minus) / (2.0 * eps)
        else:
            f_plus = np.asarray(residual_fn(x_np + eps * u))
            f_minus = np.asarray(residual_fn(x_np - eps * u))
            ju = (f_plus - f_minus) / (2.0 * eps)

        jacobian_probes.append(ju)
        if verbose:
            print(f"  Probe {i}: ‖J(u_{i})‖ = {_norm(ju):.6e}")

    # -----------------------------------------------------------------
    # Rayleigh quotients ρ_i = Re⟨u_i, J u_i⟩.
    # -----------------------------------------------------------------
    rayleigh_samples: List[float] = []
    jacobian_norm_estimate = 0.0
    for i, (u, ju) in enumerate(zip(probes, jacobian_probes)):
        rho = _inner(u, ju)
        rayleigh_samples.append(rho)
        jacobian_norm_estimate = max(jacobian_norm_estimate, _norm(ju))
        if verbose:
            print(f"  Rayleigh {i}: Re⟨u_{i}, J(u_{i})⟩ = {rho:.6e}")

    # -----------------------------------------------------------------
    # Off-diagonal antisymmetry α_{ij} = |Re⟨u_i, J u_j⟩ − Re⟨u_j, J u_i⟩|.
    # -----------------------------------------------------------------
    antisym_norms: List[float] = []
    for i in range(n_probes):
        for j in range(i + 1, n_probes):
            term1 = _inner(probes[i], jacobian_probes[j])   # Re⟨u_i, J u_j⟩
            term2 = _inner(probes[j], jacobian_probes[i])   # Re⟨u_j, J u_i⟩
            antisym = abs(term1 - term2)
            antisym_norms.append(antisym)
            if verbose:
                print(f"  Antisym ({i},{j}): |Re⟨u_{i},J u_{j}⟩ − Re⟨u_{j},J u_{i}⟩| = {antisym:.6e}")

    max_antisym = max(antisym_norms) if antisym_norms else 0.0
    antisym_norm_rel = max_antisym / (jacobian_norm_estimate + 1e-16)

    # -----------------------------------------------------------------
    # Classification (Math63 §2A thresholds, applied in real inner product).
    # -----------------------------------------------------------------
    rayleigh_min = min(rayleigh_samples)
    rayleigh_max = max(rayleigh_samples)
    n_negative = sum(1 for r in rayleigh_samples if r < 0)

    accept_spd_threshold = 1e-8
    is_symmetric = antisym_norm_rel < accept_spd_threshold
    is_positive_definite = rayleigh_min > 0
    is_indefinite = is_symmetric and not is_positive_definite
    is_asymmetric = not is_symmetric

    if verbose:
        print("\nSummary:")
        print(f"  dtype_kind       : {'complex' if is_complex else 'real'}")
        print(f"  ‖J‖ (estimate)   : {jacobian_norm_estimate:.6e}")
        print(f"  max antisymmetry : {max_antisym:.6e}")
        print(f"  antisym / ‖J‖    : {antisym_norm_rel:.6e} (threshold {accept_spd_threshold:.6e})")
        print(f"  Rayleigh range   : [{rayleigh_min:.6e}, {rayleigh_max:.6e}]")
        print(f"  # negative Rayl. : {n_negative}/{n_probes}")
        print("\n  Classification:")
        print(f"    Symmetric     : {is_symmetric}")
        print(f"    SPD           : {is_positive_definite}")
        print(f"    Indefinite    : {is_indefinite}")
        print(f"    Asymmetric    : {is_asymmetric}")

    return {
        "symmetric": bool(is_symmetric),
        "indefinite": bool(is_indefinite),
        "asymmetric": bool(is_asymmetric),
        "rayleigh_samples": rayleigh_samples,
        "antisymmetry_norm": float(max_antisym),
        "antisymmetry_norm_relative": float(antisym_norm_rel),
        "rayleigh_min": float(rayleigh_min),
        "rayleigh_max": float(rayleigh_max),
        "jacobian_norm": float(jacobian_norm_estimate),
        "n_negative_rayleigh": int(n_negative),
        "probe_labels": list(range(n_probes)),
        "accept_spd_threshold": float(accept_spd_threshold),
        "dtype_kind": "complex" if is_complex else "real",
        "inner_product": "Re(vdot)" if is_complex else "real-dot",
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _self_test() -> int:
    """
    Internal self-test for the Jacobian-symmetry classifier.

    v1.x covered: SPD / symmetric-indefinite / asymmetric in the real field.
    v2.0 adds: complex-Hermitian SPD / complex anti-Hermitian / complex
    non-diagonal Hermitian (off-diagonal i) — exercising Math63 §2A.1.

    Returns 0 on full pass, 1 on any mismatch.
    """
    import numpy as _np

    print("=" * 70)
    print("check_jacobian_symmetry — Self-Test (v2.0)")
    print("=" * 70)

    if _TORCH_AVAILABLE:
        backend = "torch"

        def _asmatrix_real(arr_np):
            return torch.as_tensor(arr_np, dtype=torch.float64)

        def _asmatrix_complex(arr_np):
            return torch.as_tensor(arr_np, dtype=torch.complex128)

        def _zeros_real(n):
            return torch.zeros(n, dtype=torch.float64)

        def _zeros_complex(n):
            return torch.zeros(n, dtype=torch.complex128)
    else:
        backend = "numpy"

        def _asmatrix_real(arr_np):
            return _np.asarray(arr_np, dtype=_np.float64)

        def _asmatrix_complex(arr_np):
            return _np.asarray(arr_np, dtype=_np.complex128)

        def _zeros_real(n):
            return _np.zeros(n, dtype=_np.float64)

        def _zeros_complex(n):
            return _np.zeros(n, dtype=_np.complex128)

    print(f"Backend selected: {backend}  (torch available: {_TORCH_AVAILABLE})")

    n = 8
    failures = []

    # ==================== REAL CASES (v1.x coverage) ====================

    # --- Case 1: SPD diagonal -----------------------------------------------
    x0r = _zeros_real(n)
    D_spd = _asmatrix_real(_np.diag(_np.arange(1.0, n + 1.0)))

    def res_spd(x):
        return D_spd @ x

    print("\nCase 1: Real SPD diagonal  (D = diag(1, 2, ..., n))")
    r1 = probe_symmetry(res_spd, x0r, n_probes=5, eps=1e-6, verbose=False)
    ok1 = (r1["symmetric"] and not r1["indefinite"]
           and not r1["asymmetric"] and r1["n_negative_rayleigh"] == 0
           and r1["dtype_kind"] == "real")
    print(f"  kind={r1['dtype_kind']}, symmetric={r1['symmetric']}, "
          f"indefinite={r1['indefinite']}, asymmetric={r1['asymmetric']}, "
          f"n_neg_rayleigh={r1['n_negative_rayleigh']}")
    print(f"  antisym/‖J‖ = {r1['antisymmetry_norm_relative']:.3e}  "
          f"→ {'PASS' if ok1 else 'FAIL'}")
    if not ok1:
        failures.append("Case 1 (real SPD): classification mismatch")

    # --- Case 2: Symmetric-indefinite ---------------------------------------
    D_ind = _asmatrix_real(_np.diag([1.0, -1.0, 2.0, -2.0, 3.0, -3.0, 4.0, -4.0]))

    def res_ind(x):
        return D_ind @ x

    print("\nCase 2: Real symmetric-indefinite  (eigenvalues ±1, ±2, ±3, ±4)")
    r2 = probe_symmetry(res_ind, x0r, n_probes=5, eps=1e-6, verbose=False)
    ok2 = (r2["symmetric"] and r2["indefinite"]
           and not r2["asymmetric"] and r2["n_negative_rayleigh"] > 0)
    print(f"  symmetric={r2['symmetric']}, indefinite={r2['indefinite']}, "
          f"asymmetric={r2['asymmetric']}, n_neg_rayleigh={r2['n_negative_rayleigh']}")
    print(f"  antisym/‖J‖ = {r2['antisymmetry_norm_relative']:.3e}  "
          f"→ {'PASS' if ok2 else 'FAIL'}")
    if not ok2:
        failures.append("Case 2 (real indefinite): classification mismatch")

    # --- Case 3: Asymmetric (skew + diagonal) -------------------------------
    A_base = _np.diag(_np.arange(1.0, n + 1.0)).copy()
    skew = _np.zeros((n, n))
    for i in range(n - 1):
        skew[i, i + 1] = 2.0
        skew[i + 1, i] = -2.0
    A_asym = _asmatrix_real(A_base + skew)

    def res_asym(x):
        return A_asym @ x

    print("\nCase 3: Real asymmetric  (diag(1..n) + tridiagonal skew ±2)")
    r3 = probe_symmetry(res_asym, x0r, n_probes=5, eps=1e-6, verbose=False)
    ok3 = (not r3["symmetric"]) and r3["asymmetric"]
    print(f"  symmetric={r3['symmetric']}, indefinite={r3['indefinite']}, "
          f"asymmetric={r3['asymmetric']}")
    print(f"  antisym/‖J‖ = {r3['antisymmetry_norm_relative']:.3e}  "
          f"→ {'PASS' if ok3 else 'FAIL'}")
    if not ok3:
        failures.append("Case 3 (real asymmetric): classification mismatch")

    # ==================== COMPLEX CASES (v2.0) ==========================

    x0c = _zeros_complex(n)

    # --- Case 4: Complex Hermitian SPD (diagonal real positive) ------------
    H_diag = _np.diag(_np.arange(1.0, n + 1.0)).astype(_np.complex128)
    H_spd_c = _asmatrix_complex(H_diag)

    def res_herm_spd(x):
        return H_spd_c @ x

    print("\nCase 4: Complex Hermitian SPD  (diag(1..n) in complex128)")
    r4 = probe_symmetry(res_herm_spd, x0c, n_probes=5, eps=1e-6, verbose=False)
    ok4 = (r4["symmetric"] and not r4["indefinite"]
           and not r4["asymmetric"] and r4["n_negative_rayleigh"] == 0
           and r4["dtype_kind"] == "complex")
    print(f"  kind={r4['dtype_kind']}, symmetric={r4['symmetric']}, "
          f"indefinite={r4['indefinite']}, asymmetric={r4['asymmetric']}, "
          f"n_neg_rayleigh={r4['n_negative_rayleigh']}, "
          f"inner_product={r4['inner_product']}")
    print(f"  antisym/‖J‖ = {r4['antisymmetry_norm_relative']:.3e}, "
          f"Rayleigh range = [{r4['rayleigh_min']:.3e}, {r4['rayleigh_max']:.3e}]  "
          f"→ {'PASS' if ok4 else 'FAIL'}")
    if not ok4:
        failures.append("Case 4 (complex Hermitian SPD): classification mismatch")

    # --- Case 5: Complex anti-Hermitian  (A = i * diag(1..n)) --------------
    A_anti = _asmatrix_complex(1j * _np.diag(_np.arange(1.0, n + 1.0)))

    def res_anti_herm(x):
        return A_anti @ x

    print("\nCase 5: Complex anti-Hermitian  (A = i · diag(1..n))")
    r5 = probe_symmetry(res_anti_herm, x0c, n_probes=5, eps=1e-6, verbose=False)
    # Expected: Re⟨u, Au⟩ = Re(i·Σk|u_k|²) = 0 ⇒ rayleigh ≈ 0
    # And α_{ij} = 2|Im⟨u_i, diag u_j⟩| generically nonzero ⇒ asymmetric=True.
    ok5 = ((not r5["symmetric"]) and r5["asymmetric"]
           and r5["dtype_kind"] == "complex"
           and abs(r5["rayleigh_max"]) < 1e-6 and abs(r5["rayleigh_min"]) < 1e-6)
    print(f"  kind={r5['dtype_kind']}, symmetric={r5['symmetric']}, "
          f"indefinite={r5['indefinite']}, asymmetric={r5['asymmetric']}")
    print(f"  antisym/‖J‖ = {r5['antisymmetry_norm_relative']:.3e}, "
          f"Rayleigh range = [{r5['rayleigh_min']:.3e}, {r5['rayleigh_max']:.3e}]  "
          f"→ {'PASS' if ok5 else 'FAIL'}")
    if not ok5:
        failures.append("Case 5 (complex anti-Hermitian): classification mismatch")

    # --- Case 6: Complex non-diagonal Hermitian with imaginary off-diag ----
    # H_{kk} = k+1 (diag), H_{k,k+1} = -i, H_{k+1,k} = +i; n = 8.
    H6 = _np.diag(_np.arange(1.0, n + 1.0) + 1.0).astype(_np.complex128)
    for k in range(n - 1):
        H6[k, k + 1] = -1j
        H6[k + 1, k] = +1j
    H6_c = _asmatrix_complex(H6)

    def res_herm_tridiag(x):
        return H6_c @ x

    print("\nCase 6: Complex non-diagonal Hermitian  (tridiagonal ±i off-diag)")
    r6 = probe_symmetry(res_herm_tridiag, x0c, n_probes=5, eps=1e-6, verbose=False)
    # Matrix is diagonally dominant (|H_kk| ≥ 2 > 2·|off-diag| = 2·1; strict
    # Gershgorin SPD since each diag = k+1 ≥ 2 and row-sum-off-diag ≤ 2).
    # Wait: row 0 has diag=2, off-diag |−i|=1 ⇒ Gershgorin disk [1,3] ⊂ (0,∞)
    # Row k (1≤k≤n−2) has diag=k+2, off-diags two of magnitude 1 ⇒ disk [k,k+4].
    # All disks ⊂ (0,∞) ⇒ all eigenvalues > 0 ⇒ SPD.
    ok6 = (r6["symmetric"] and not r6["indefinite"]
           and not r6["asymmetric"] and r6["n_negative_rayleigh"] == 0
           and r6["dtype_kind"] == "complex")
    print(f"  kind={r6['dtype_kind']}, symmetric={r6['symmetric']}, "
          f"indefinite={r6['indefinite']}, asymmetric={r6['asymmetric']}, "
          f"n_neg_rayleigh={r6['n_negative_rayleigh']}")
    print(f"  antisym/‖J‖ = {r6['antisymmetry_norm_relative']:.3e}, "
          f"Rayleigh range = [{r6['rayleigh_min']:.3e}, {r6['rayleigh_max']:.3e}]  "
          f"→ {'PASS' if ok6 else 'FAIL'}")
    if not ok6:
        failures.append("Case 6 (complex non-diag Hermitian): classification mismatch")

    print("\n" + "=" * 70)
    if not failures:
        print("✓ All 6 classification cases passed!  (3 real + 3 complex)")
        print("=" * 70)
        return 0
    else:
        print("✗ Self-test FAILED:")
        for f in failures:
            print(f"    - {f}")
        print("=" * 70)
        return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """CLI interface for Jacobian symmetry check."""
    # Intercept --selftest *before* argparse: in self-test mode the
    # --residual-fn/--x0 required arguments must not be enforced.
    if "--selftest" in sys.argv[1:]:
        sys.exit(_self_test())

    parser = argparse.ArgumentParser(
        description="Classify Jacobian symmetry via finite-difference probes (real/complex)."
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run internal self-test on 6 synthetic Jacobians "
             "(3 real: SPD / indefinite / asymmetric; "
             "3 complex: Hermitian-SPD / anti-Hermitian / non-diagonal Hermitian).",
    )
    parser.add_argument(
        "--residual-fn",
        type=str,
        required=True,
        help='Residual function as "module:function" (e.g., "real_backend_pt_bcc_mixed_v3:residual")',
    )
    parser.add_argument(
        "--x0",
        type=str,
        required=True,
        help="Path to current iterate (φ*.npy or φ*.pt)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config JSON (optional; needed if residual_fn requires it)",
    )
    parser.add_argument(
        "--n-probes",
        type=int,
        default=5,
        choices=[3, 5, 7],
        help="Number of random probe vectors (default 5)",
    )
    parser.add_argument(
        "--eps",
        type=float,
        default=1e-6,
        help="Finite-difference step size (default 1e-6)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed probe output",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file (default: print to stdout)",
    )

    args = parser.parse_args()

    # Load config if provided
    params = {}
    if args.config:
        with open(args.config, "r") as f:
            params = json.load(f)

    # Load residual function
    module_name, func_name = args.residual_fn.split(":")
    try:
        module = __import__(module_name)
        residual_fn = getattr(module, func_name)
    except (ImportError, AttributeError) as e:
        print(f"Error loading {args.residual_fn}: {e}", file=sys.stderr)
        sys.exit(1)

    # Load iterate
    if args.x0.endswith(".npy"):
        x0 = np.load(args.x0)
    elif args.x0.endswith(".pt"):
        if not _TORCH_AVAILABLE:
            print("PyTorch required for .pt files", file=sys.stderr)
            sys.exit(1)
        x0 = torch.load(args.x0)
    else:
        print(f"Unrecognized file format: {args.x0}", file=sys.stderr)
        sys.exit(1)

    # Create residual function wrapper (if config needed)
    def residual_with_config(x):
        return residual_fn(x, params)

    # Run probe
    result = probe_symmetry(
        residual_fn=residual_with_config,
        x0=x0,
        n_probes=args.n_probes,
        eps=args.eps,
        verbose=args.verbose,
    )

    # Output
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Results written to {args.output}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
