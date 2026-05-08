#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: unregistered
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
"""
backend_consistency_audit.py — Gradient / Hessian / Energy consistency test
===========================================================================

Purpose:  Identify the normalization factor between
          (1)  d/deps F[Psi + eps v]|_{eps=0}   (finite-difference energy gradient)
          (2)  Re <R[Psi], v>                    (inner product with residual)
          (3)  d/deps R[Psi + eps v]|_{eps=0}    (finite-difference Jacobian)
          (4)  H[Psi] v                          (backend hessian_vec)

If (1) and (2) differ by a constant factor, the trust-region ratio
rho = actual / predicted will be systematically wrong by that factor,
which is exactly the observed rho ≈ 0.126 ≈ 1/8 behaviour.

Usage:
    python PDE/backend_consistency_audit.py \
        --config PDE/config_template_brazovskii.json \
        --N 16 --L 10pi

Outputs a table of ratios.  The key diagnostic is:
    ratio_grad  =  <dF/deps>_{FD}  /  <R, v>_{code}
    ratio_hess  =  <dR/deps>_{FD}  /  <Hv>_{code}

If ratio_grad ≠ 1.0, the residual is NOT the gradient of shell_free_energy.
The trust-region solver assumes it is, so rho ≈ ratio_grad systematically.
"""

from __future__ import annotations
import argparse, json, math, sys, time
from pathlib import Path
from typing import Dict, Any

import numpy as np

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import real_backend_pt_bcc_mixed_v3 as backend

try:
    from tect_solver_pt_v3 import make_mock_branch_data
    _HAS_MOCK = True
except Exception:
    make_mock_branch_data = None
    _HAS_MOCK = False


# ── helpers ──────────────────────────────────────────────────────────

def parse_L(s: str) -> float:
    s = s.strip().lower()
    if s.endswith("pi"):
        c = s[:-2].strip()
        c = "1" if c == "" else c
        return float(c) * math.pi
    return float(s)


def complex_inner(A: np.ndarray, B: np.ndarray) -> complex:
    """Σ conj(A) * B  over all entries (Hermitian inner product)."""
    return np.sum(np.conj(A.ravel()) * B.ravel())


def real_L2(A: np.ndarray, B: np.ndarray) -> float:
    """Re Σ conj(A)*B = Σ Re(A)*Re(B) + Im(A)*Im(B)."""
    return float(np.real(complex_inner(A, B)))


def build_ansatz(N: int, L: float, params: Dict[str, Any]) -> np.ndarray:
    q0 = float(params["q0"])
    lam = float(params.get("quartic_lambda", params.get("lambda", -0.43)))
    gam = float(params.get("sextic_gamma", params.get("gamma", 1.62)))
    if _HAS_MOCK:
        hat_n = np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0)
        Psi_bcc, Psi_corr, _, _, _ = make_mock_branch_data(
            N=N, L=L, q0=q0, hat_n=hat_n,
            quartic_lambda=lam, sextic_gamma=gam,
        )
        return np.asarray(Psi_corr, dtype=np.complex128)
    # fallback: single-mode seed
    xs = np.linspace(0.0, L, N, endpoint=False)
    X, Y, Z = np.meshgrid(xs, xs, xs, indexing="ij")
    phase = q0 * (X + Y + Z) / math.sqrt(3.0)
    Psi = np.zeros((3, N, N, N), dtype=np.complex128)
    Psi[0] = 0.2 * np.cos(phase)
    return Psi


# ── tests ────────────────────────────────────────────────────────────

def test_gradient_consistency(
    Psi: np.ndarray, params: Dict[str, Any],
    n_probes: int = 5, eps_list=None,
) -> None:
    """
    Test 1:  Does  dF/dε = Re<R, v> ?

    Computes the directional derivative of shell_free_energy by central FD:
        dF_fd = [F(Ψ + εv) - F(Ψ - εv)] / (2ε)

    Compares against the code's residual inner product:
        dF_code = Re Σ conj(R(Ψ)) · v   (summed over all sites & components)

    The ratio dF_fd / dF_code reveals the missing normalization factor.
    """
    if eps_list is None:
        eps_list = [1e-4, 1e-5, 1e-6, 1e-7]

    R = np.asarray(backend.residual(Psi, params), dtype=np.complex128)
    rng = np.random.default_rng(42)

    print("\n" + "=" * 78)
    print("  TEST 1:  Gradient consistency   dF/dε  vs  Re<R, v>")
    print("=" * 78)
    print(f"  {'probe':>6s}  {'eps':>10s}  {'dF_fd':>14s}  {'<R,v>':>14s}"
          f"  {'ratio':>10s}  {'|ratio-1|':>10s}")
    print("-" * 78)

    ratios_best = []
    for ip in range(n_probes):
        v = rng.standard_normal(Psi.shape) + 1j * rng.standard_normal(Psi.shape)
        v = v / np.sqrt(np.sum(np.abs(v)**2))  # unit-norm direction

        Rv = real_L2(R, v)  # Re Σ conj(R)*v

        best_ratio = None
        best_eps = None
        for eps in eps_list:
            Fp = float(backend.shell_free_energy(Psi + eps * v, params))
            Fm = float(backend.shell_free_energy(Psi - eps * v, params))
            dF_fd = (Fp - Fm) / (2.0 * eps)

            ratio = dF_fd / Rv if abs(Rv) > 1e-30 else float("nan")
            dev = abs(ratio - 1.0) if np.isfinite(ratio) else float("inf")

            if best_ratio is None or (np.isfinite(ratio) and dev < abs(best_ratio - 1.0)):
                best_ratio = ratio
                best_eps = eps

            print(f"  {ip:6d}  {eps:10.1e}  {dF_fd:+14.8e}  {Rv:+14.8e}"
                  f"  {ratio:10.6f}  {dev:10.2e}")

        if best_ratio is not None and np.isfinite(best_ratio):
            ratios_best.append(best_ratio)

    if ratios_best:
        arr = np.array(ratios_best)
        print("-" * 78)
        print(f"  Best ratios:  mean = {np.mean(arr):.8f},"
              f"  std = {np.std(arr):.2e},  min = {np.min(arr):.8f},"
              f"  max = {np.max(arr):.8f}")
        print(f"\n  *** If ratio ≈ C ≠ 1.0, then  ∇F = C · R_code. ***")
        print(f"  *** The trust-region rho will be systematically ≈ C. ***")
    print()


def test_hessian_consistency(
    Psi: np.ndarray, params: Dict[str, Any],
    n_probes: int = 5, eps_list=None,
) -> None:
    """
    Test 2:  Does  dR/dε · v = H·v ?

    Computes the Jacobian-vector product of residual by central FD:
        JvFD = [R(Ψ + εv) - R(Ψ - εv)] / (2ε)

    Compares against the code's hessian_vec:
        Hv = backend.hessian_vec(Ψ, v, params)

    Reports ||JvFD - Hv|| / ||Hv|| and the best-fit scalar ratio.
    """
    if eps_list is None:
        eps_list = [1e-4, 1e-5, 1e-6, 1e-7]

    rng = np.random.default_rng(99)

    print("=" * 78)
    print("  TEST 2:  Hessian consistency   dR/dε·v  vs  Hv")
    print("=" * 78)
    print(f"  {'probe':>6s}  {'eps':>10s}  {'||JvFD||':>14s}  {'||Hv||':>14s}"
          f"  {'rel_err':>10s}  {'ratio':>10s}")
    print("-" * 78)

    ratios_best = []
    for ip in range(n_probes):
        v = rng.standard_normal(Psi.shape) + 1j * rng.standard_normal(Psi.shape)
        v = v / np.sqrt(np.sum(np.abs(v)**2))

        Hv = np.asarray(backend.hessian_vec(Psi, v, params), dtype=np.complex128)
        norm_Hv = np.sqrt(np.sum(np.abs(Hv)**2))

        for eps in eps_list:
            Rp = np.asarray(backend.residual(Psi + eps * v, params),
                            dtype=np.complex128)
            Rm = np.asarray(backend.residual(Psi - eps * v, params),
                            dtype=np.complex128)
            JvFD = (Rp - Rm) / (2.0 * eps)

            norm_Jv = np.sqrt(np.sum(np.abs(JvFD)**2))
            diff = np.sqrt(np.sum(np.abs(JvFD - Hv)**2))
            rel_err = diff / max(norm_Hv, 1e-30)

            # Best-fit scalar ratio: minimize ||JvFD - c*Hv||^2
            # c = Re<JvFD, Hv> / ||Hv||^2
            ratio = real_L2(JvFD, Hv) / max(norm_Hv**2, 1e-30)

            print(f"  {ip:6d}  {eps:10.1e}  {norm_Jv:14.8e}  {norm_Hv:14.8e}"
                  f"  {rel_err:10.2e}  {ratio:10.6f}")

        ratios_best.append(ratio)  # use smallest eps

    if ratios_best:
        arr = np.array(ratios_best)
        print("-" * 78)
        print(f"  Ratios:  mean = {np.mean(arr):.8f},"
              f"  std = {np.std(arr):.2e}")
        print(f"\n  *** If ratio ≈ 1.0, Hessian is self-consistent. ***")
        print(f"  *** If ratio ≈ C ≠ 1.0, hessian_vec = C · Jacobian(residual). ***")
    print()


def test_energy_model_ratio(
    Psi: np.ndarray, params: Dict[str, Any],
    n_probes: int = 5,
) -> None:
    """
    Test 3:  Direct trust-region ratio simulation.

    Takes a small steepest-descent step s = -ε·R and computes:
        actual = F(Ψ) - F(Ψ + s)
        pred   = -<R, s> - 0.5 <s, H·s>     (quadratic model)
        rho    = actual / pred

    This directly reproduces the rho ≈ 0.126 observed in the solver.
    """
    R = np.asarray(backend.residual(Psi, params), dtype=np.complex128)
    F0 = float(backend.shell_free_energy(Psi, params))
    norm_R = np.sqrt(np.sum(np.abs(R)**2))

    print("=" * 78)
    print("  TEST 3:  Direct rho simulation  (steepest-descent micro-step)")
    print("=" * 78)
    print(f"  F(Ψ)      = {F0:+.10e}")
    print(f"  ||R||     = {norm_R:.10e}")
    print()
    print(f"  {'eps':>10s}  {'actual':>14s}  {'pred_linear':>14s}"
          f"  {'pred_quad':>14s}  {'rho_lin':>10s}  {'rho_quad':>10s}")
    print("-" * 78)

    for eps in [1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8]:
        s = -eps * R  # steepest descent step (complex)

        # Actual energy change
        Psi_new = Psi + s
        F_new = float(backend.shell_free_energy(Psi_new, params))
        actual = F0 - F_new

        # Predicted (linear part): -Re<R, s> = eps * ||R||^2
        pred_linear = eps * norm_R**2

        # Predicted (full quadratic): -Re<R,s> - 0.5*Re<s, Hs>
        Hs = np.asarray(backend.hessian_vec(Psi, s, params), dtype=np.complex128)
        pred_quad = eps * norm_R**2 - 0.5 * real_L2(s, Hs)

        rho_lin = actual / pred_linear if abs(pred_linear) > 1e-30 else float("nan")
        rho_quad = actual / pred_quad if abs(pred_quad) > 1e-30 else float("nan")

        print(f"  {eps:10.1e}  {actual:+14.8e}  {pred_linear:+14.8e}"
              f"  {pred_quad:+14.8e}  {rho_lin:10.6f}  {rho_quad:10.6f}")

    print("-" * 78)
    print(f"\n  *** rho_lin = actual / (ε||R||²).  If constant ≈ 0.126, ***")
    print(f"  *** this is the exact factor mismatch.  ***")
    print(f"  *** Expected from dV analysis: dV = (L/N)³ = "
          f"{(float(params.get('L', params.get('Lx', 16.0))) / Psi.shape[1])**3:.8f} ***")
    print()


def test_wirtinger_factor(
    Psi: np.ndarray, params: Dict[str, Any],
) -> None:
    """
    Test 4:  Wirtinger factor test.

    For a real functional F[Ψ,Ψ*], the gradient in real coordinates is:
        ∂F/∂(Re Ψ) = 2 Re(δF/δΨ*)
        ∂F/∂(Im Ψ) = 2 Im(δF/δΨ*)

    If R = δF/δΨ*, then flatten(R) = [Re(R), Im(R)] and the real gradient
    is 2 * flatten(R).  This test checks whether the factor 2 is present.
    """
    print("=" * 78)
    print("  TEST 4:  Wirtinger / real-gradient factor")
    print("=" * 78)

    F0 = float(backend.shell_free_energy(Psi, params))
    R = np.asarray(backend.residual(Psi, params), dtype=np.complex128)

    # Test with pure-real and pure-imaginary perturbations
    rng = np.random.default_rng(77)
    eps = 1e-6

    # Pure real perturbation
    v_real = rng.standard_normal(Psi.shape)
    v_real = v_real / np.sqrt(np.sum(v_real**2))

    Fp = float(backend.shell_free_energy(Psi + eps * v_real, params))
    Fm = float(backend.shell_free_energy(Psi - eps * v_real, params))
    dF_real_fd = (Fp - Fm) / (2.0 * eps)

    # Code predicts: Re(Σ conj(R) * v_real) = Σ Re(R) * v_real
    dF_code = float(np.sum(np.real(R) * v_real))

    ratio_real = dF_real_fd / dF_code if abs(dF_code) > 1e-30 else float("nan")

    # Pure imaginary perturbation
    v_imag = 1j * rng.standard_normal(Psi.shape)
    v_imag = v_imag / np.sqrt(np.sum(np.abs(v_imag)**2))

    Fp = float(backend.shell_free_energy(Psi + eps * v_imag, params))
    Fm = float(backend.shell_free_energy(Psi - eps * v_imag, params))
    dF_imag_fd = (Fp - Fm) / (2.0 * eps)

    # Code predicts: Re(Σ conj(R) * v_imag) = Σ Im(R) * Im(v_imag)
    dF_code_imag = float(np.sum(np.imag(R) * np.imag(v_imag)))

    ratio_imag = dF_imag_fd / dF_code_imag if abs(dF_code_imag) > 1e-30 else float("nan")

    print(f"  Pure-real  perturbation:  dF_fd = {dF_real_fd:+.10e},"
          f"  <R,v>_code = {dF_code:+.10e},  ratio = {ratio_real:.8f}")
    print(f"  Pure-imag  perturbation:  dF_fd = {dF_imag_fd:+.10e},"
          f"  <R,v>_code = {dF_code_imag:+.10e},  ratio = {ratio_imag:.8f}")
    print()
    print(f"  *** If ratio ≈ dV = (L/N)³, the Wirtinger factor is absorbed in dV. ***")
    print(f"  *** If ratio ≈ 2·dV, there is an extra Wirtinger factor of 2.       ***")
    print()


def test_component_decomposition(
    Psi: np.ndarray, params: Dict[str, Any],
) -> None:
    """
    Test 5:  Decompose the gradient ratio by backend component.

    Separately tests the linear (kinetic) part vs nonlinear part
    by using near-zero amplitude field (linear dominated) and
    larger amplitude (nonlinear significant).
    """
    print("=" * 78)
    print("  TEST 5:  Component decomposition  (linear vs nonlinear)")
    print("=" * 78)

    eps = 1e-6
    rng = np.random.default_rng(55)
    v = rng.standard_normal(Psi.shape) + 1j * rng.standard_normal(Psi.shape)
    v = v / np.sqrt(np.sum(np.abs(v)**2))

    for scale_label, scale in [("tiny (1e-6)", 1e-6), ("small (1e-3)", 1e-3),
                                ("config φ₀", 1.0)]:
        Psi_scaled = scale * Psi if scale != 1.0 else Psi.copy()
        R = np.asarray(backend.residual(Psi_scaled, params), dtype=np.complex128)
        F0 = float(backend.shell_free_energy(Psi_scaled, params))
        Fp = float(backend.shell_free_energy(Psi_scaled + eps * v, params))
        Fm = float(backend.shell_free_energy(Psi_scaled - eps * v, params))
        dF_fd = (Fp - Fm) / (2.0 * eps)
        Rv = real_L2(R, v)
        ratio = dF_fd / Rv if abs(Rv) > 1e-30 else float("nan")

        print(f"  amplitude = {scale_label:20s}  ||Ψ||_rms = "
              f"{np.sqrt(np.mean(np.abs(Psi_scaled)**2)):.4e}  "
              f"dF_fd/Rv = {ratio:.8f}")

    print()
    print("  *** If ratio changes with amplitude, bilinear and nonlinear")
    print("      have DIFFERENT normalization factors. ***")
    print()


def test_jacobian_symmetry(
    Psi: np.ndarray, params: Dict[str, Any],
    n_probes: int = 8,
) -> None:
    """
    Test 6:  Jacobian symmetry   Re<u, Jv>  vs  Re<v, Ju>.

    The CG solver requires J = DR to be symmetric.  For a variational
    problem (R = ∇F), J = ∇²F is automatically symmetric.  But if the
    residual deviates from ∇F (as Test 1 proved), J might not be symmetric.

    This test checks:  Re<u, H[v]> vs Re<v, H[u]>  for random (u, v).
    If |Re<u,Jv> - Re<v,Ju>| / max(|Re<u,Jv>|, |Re<v,Ju>|) ~ 0,
    the Jacobian is symmetric and CG is safe.
    """
    print("=" * 78)
    print("  TEST 6:  Jacobian symmetry   Re<u, Jv>  vs  Re<v, Ju>")
    print("=" * 78)
    print("   probe         Re<u,Jv>          Re<v,Ju>       rel_asym")
    print("-" * 78)

    rng = np.random.default_rng(66)
    max_asym = 0.0
    for k in range(n_probes):
        u = rng.standard_normal(Psi.shape) + 1j * rng.standard_normal(Psi.shape)
        v = rng.standard_normal(Psi.shape) + 1j * rng.standard_normal(Psi.shape)
        u = u / np.sqrt(np.sum(np.abs(u)**2))
        v = v / np.sqrt(np.sum(np.abs(v)**2))

        Jv = np.asarray(backend.hessian_vec(Psi, v, params),
                        dtype=np.complex128)
        Ju = np.asarray(backend.hessian_vec(Psi, u, params),
                        dtype=np.complex128)

        uJv = real_L2(u, Jv)
        vJu = real_L2(v, Ju)

        denom = max(abs(uJv), abs(vJu), 1e-300)
        rel_asym = abs(uJv - vJu) / denom

        max_asym = max(max_asym, rel_asym)

        print(f"   {k:5d}   {uJv:+.10e}   {vJu:+.10e}   {rel_asym:.3e}")

    print("-" * 78)
    print(f"  Max relative asymmetry = {max_asym:.3e}")
    print()
    if max_asym < 1e-6:
        print("  *** J is symmetric to machine precision.  CG is safe. ***")
    elif max_asym < 1e-2:
        print("  *** J is approximately symmetric.  CG is acceptable,")
        print("      but GMRES would be more robust. ***")
    else:
        print("  *** J is NOT symmetric.  CG may fail or give wrong directions.")
        print("      Switch to GMRES for the inner Krylov solve. ***")
    print()


# ── main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Backend gradient/Hessian/energy consistency audit")
    parser.add_argument("--config", required=True)
    parser.add_argument("--N", type=int, default=16)
    parser.add_argument("--L", type=str, default="10pi")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        params = json.load(f)

    N = args.N
    L = parse_L(args.L)
    params["N"] = N
    params["L"] = L
    params["Lx"] = L
    params["Ly"] = L
    params["Lz"] = L
    params["Nx"] = N
    params["Ny"] = N
    params["Nz"] = N

    dV = (L / N) ** 3

    print("=" * 78)
    print("  TECT Backend Consistency Audit")
    print("=" * 78)
    print(f"  Config    : {args.config}")
    print(f"  Grid      : N={N}, L={L:.6f}")
    print(f"  dV = (L/N)³ = {dV:.10f}")
    print(f"  2·dV      = {2*dV:.10f}")
    print(f"  1/8       = {1/8:.10f}")
    print()

    Psi = build_ansatz(N, L, params)
    rms = np.sqrt(np.mean(np.abs(Psi)**2))
    print(f"  Ansatz RMS = {rms:.6e}")

    t0 = time.perf_counter()
    test_gradient_consistency(Psi, params)
    test_hessian_consistency(Psi, params)
    test_energy_model_ratio(Psi, params)
    test_wirtinger_factor(Psi, params)
    test_component_decomposition(Psi, params)
    test_jacobian_symmetry(Psi, params)
    elapsed = time.perf_counter() - t0

    print(f"  Total audit time: {elapsed:.1f}s")
    print()
    print("=" * 78)
    print("  ACTION ITEMS")
    print("=" * 78)
    print("  1. If Test 1 ratio ≈ C ≠ 1:  residual ≠ ∇(shell_free_energy).")
    print("     Fix: switch merit from F to ½||R||² (DONE in v2.2).")
    print("  2. If Test 2 ratio ≈ 1:  hessian_vec IS the Jacobian of residual.")
    print("     The gradient/Hessian pair is self-consistent (good).")
    print("  3. If Test 5 ratio varies with amplitude:  bilinear/nonlinear")
    print("     have different factors → cannot fix with a single constant.")
    print("  4. If Test 6 asymmetry < 1e-6:  J is symmetric, CG is valid.")
    print("     If asymmetry > 0.01:  switch CG → GMRES.")
    print("=" * 78)


if __name__ == "__main__":
    main()
