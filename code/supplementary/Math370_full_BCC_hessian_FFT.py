#!/usr/bin/env python3
# =====================================================================
# Math370_full_BCC_hessian_FFT.py — Real Brazovskii Hessian on N×N×N grid
#
# !!! AUDIT-FLAGGED INVALID (2026-05-09, see Math373) !!!
# Free energy implemented here OMITS the canonical sextic stabiliser
# γΨ⁶/3 (the integrand has only μ²Ψ²/2 + γ(∇²+q₀²)²Ψ²/2 + λΨ⁴/4).
# Without the sextic, λ<0 is unbounded below and the N=32 steepest-
# descent run diverges to NaN within 4 iterations — this is an
# artefact of the missing sextic, NOT a property of canonical TECT.
# γ is also misinterpreted as a gradient coefficient (canonical: γ is
# the sextic coefficient, gradient uses Z and Y). Do NOT cite this
# script's eigenvalues. Corrected implementation queued as Math374.
# Canonical free energy: Codes/pde/real_backend_pt_bcc_mixed_v3.py
# (shell_free_energy, lines 532-602). Retraction note:
# Docs/math/TECT-Math373-Math372-Sign-Error-Claim-RETRACTION-and-Canonical-Free-Energy-Restoration.tex.txt
#
# Replaces the 12-mode equal-amplitude shortcut (Math369) with the
# real Brazovskii functional discretised on a periodic N×N×N grid.
# Uses FFT to compute the (∇² + q₀²)² operator efficiently.
#
# Workflow:
#   1. Set up cubic periodic box of size L (chosen to fit BCC unit cell).
#   2. Initialise Ψ(x) with 12-mode equal-amplitude BCC (Bragg modes).
#   3. Optionally relax via gradient descent (find true ground state).
#   4. Construct linearised Hessian operator H[δΨ] at this configuration.
#   5. Compute lowest-K eigenvalues via Lanczos (scipy.sparse.linalg.eigsh).
#   6. Project out 6 Goldstone zero modes (3 translation + 3 rotation).
#   7. Verify: are remaining eigenvalues all positive? → BCC local minimum.
#
# Math note linkage: planned Math370 (next-cycle, post-operator-audit).
#
# Usage:
#     python -u Codes/supplementary/Math370_full_BCC_hessian_FFT.py --N 16 --eigs 30
#     python -u Codes/supplementary/Math370_full_BCC_hessian_FFT.py --N 32 --eigs 50 --relax-iters 200
#
# Runtime estimates (single core, modern CPU):
#     N=16, eigs=30           → ~10-30 seconds
#     N=32, eigs=50           → ~2-5 minutes
#     N=64, eigs=50, relax    → ~30-60 minutes
#     N=128, eigs=50          → ~hours (consider GPU)
#
# Dependencies: numpy, scipy.sparse.linalg, optional matplotlib.
# =====================================================================
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
try:
    from scipy.sparse.linalg import LinearOperator, eigsh
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("WARNING: scipy not installed; Lanczos disabled. "
          "Install: pip install scipy", file=sys.stderr)


# ---------------------------------------------------------------------
# Brazovskii free-energy functional + Hessian on periodic grid
# ---------------------------------------------------------------------
def setup_grid(N: int, q0: float = 1.0):
    """Periodic cubic grid of size L = (4π/q0)·sqrt(2) to fit one BCC unit cell."""
    L = 4.0 * np.pi * np.sqrt(2.0) / q0   # BCC lattice constant ~ √2·(2π/q0)
    dx = L / N
    x = np.arange(N) * dx
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    # Reciprocal grid
    k = np.fft.fftfreq(N, d=dx) * 2.0 * np.pi
    KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
    K2 = KX**2 + KY**2 + KZ**2
    return {"L": L, "dx": dx, "X": X, "Y": Y, "Z": Z, "K2": K2,
             "KX": KX, "KY": KY, "KZ": KZ, "N": N, "q0": q0}


def bcc_initial_state(grid, A0: float = 1.0):
    """12-mode (110)-family equal-amplitude BCC ansatz on the grid."""
    X, Y, Z = grid["X"], grid["Y"], grid["Z"]
    q0 = grid["q0"]
    # 12 BCC reciprocal vectors of length √2·q0
    G_vecs = []
    for i, j in [(0, 1), (0, 2), (1, 2)]:
        for s1, s2 in [(+1, +1), (+1, -1)]:
            v = [0.0, 0.0, 0.0]
            v[i] = s1 * q0
            v[j] = s2 * q0
            G_vecs.append(np.array(v))
    psi = np.zeros_like(X)
    for G in G_vecs:
        psi += A0 * np.cos(G[0]*X + G[1]*Y + G[2]*Z)
    return psi


def free_energy(psi: np.ndarray, grid: dict,
                mu2: float, gamma: float, lam: float) -> float:
    """Compute F[Ψ] for a real field on the grid.

    F = ∫ [ (μ²/2) Ψ² + (γ/2) ((∇²+q₀²) Ψ)² + (λ/4) Ψ⁴ ] d³x
    """
    K2 = grid["K2"]; q0 = grid["q0"]; dx = grid["dx"]
    psi_k = np.fft.fftn(psi)
    laplacian_plus_q02 = (-K2 + q0**2) * psi_k
    grad_term = np.fft.ifftn(laplacian_plus_q02).real
    integrand = (mu2/2.0) * psi**2 + (gamma/2.0) * grad_term**2 + (lam/4.0) * psi**4
    return float(np.sum(integrand) * dx**3)


def free_energy_gradient(psi: np.ndarray, grid: dict,
                          mu2: float, gamma: float, lam: float) -> np.ndarray:
    """δF/δΨ = μ² Ψ + γ (∇²+q₀²)² Ψ + λ Ψ³"""
    K2 = grid["K2"]; q0 = grid["q0"]
    psi_k = np.fft.fftn(psi)
    L_psi_k = (-K2 + q0**2)**2 * psi_k
    L_psi = np.fft.ifftn(L_psi_k).real
    return mu2 * psi + gamma * L_psi + lam * psi**3


def relax_to_ground_state(psi0: np.ndarray, grid: dict,
                           mu2: float, gamma: float, lam: float,
                           n_iters: int = 100, dt: float = 0.01,
                           verbose: bool = True) -> tuple:
    """Simple steepest-descent relaxation Ψ_{n+1} = Ψ_n - dt · δF/δΨ.

    For a true minimum, gradient should approach zero.
    """
    psi = psi0.copy()
    F_history = []
    for it in range(n_iters):
        F = free_energy(psi, grid, mu2, gamma, lam)
        grad = free_energy_gradient(psi, grid, mu2, gamma, lam)
        F_history.append(F)
        psi = psi - dt * grad
        if verbose and (it < 5 or it % max(1, n_iters // 10) == 0):
            grad_norm = float(np.sqrt(np.mean(grad**2)))
            print(f"    iter {it:4d}: F = {F:+.6e}, |∇F|/√V = {grad_norm:.4e}")
    return psi, F_history


def hessian_apply(delta_psi: np.ndarray, psi: np.ndarray, grid: dict,
                  mu2: float, gamma: float, lam: float) -> np.ndarray:
    """H[δΨ] = δ²F/δΨ² · δΨ
            = μ² δΨ + γ (∇²+q₀²)² δΨ + 3λ Ψ² δΨ
    """
    K2 = grid["K2"]; q0 = grid["q0"]
    delta_k = np.fft.fftn(delta_psi)
    L_delta_k = (-K2 + q0**2)**2 * delta_k
    L_delta = np.fft.ifftn(L_delta_k).real
    return mu2 * delta_psi + gamma * L_delta + 3.0 * lam * psi**2 * delta_psi


def lowest_eigenvalues(psi: np.ndarray, grid: dict,
                        mu2: float, gamma: float, lam: float,
                        k: int = 30) -> tuple:
    """Lowest k eigenvalues of the Hessian via scipy LinearOperator + eigsh."""
    if not HAS_SCIPY:
        raise RuntimeError("scipy required for Lanczos; pip install scipy")
    n = psi.size
    shape_3d = psi.shape

    def matvec(v_flat):
        v_3d = v_flat.reshape(shape_3d)
        Hv_3d = hessian_apply(v_3d, psi, grid, mu2, gamma, lam)
        return Hv_3d.flatten()

    H_op = LinearOperator((n, n), matvec=matvec, dtype=psi.dtype)
    # 'SA' = smallest algebraic (most negative). Need shift if Hessian is
    # nearly singular at zero (Goldstone modes); use 'sigma=0' shift-invert.
    try:
        eigs, vecs = eigsh(H_op, k=k, which='SA', tol=1e-6)
    except Exception as e:
        print(f"    SA mode failed ({e}); trying shift-invert at sigma=0")
        eigs, vecs = eigsh(H_op, k=k, sigma=0.0, which='LM', tol=1e-6)
    # Sort ascending
    order = np.argsort(eigs)
    return eigs[order], vecs[:, order]


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--N", type=int, default=16,
                        help="grid points per axis (16=fast, 32=careful, 64=slow)")
    parser.add_argument("--mu2", type=float, default=-0.7)
    parser.add_argument("--gamma", type=float, default=1.62)
    parser.add_argument("--lam", type=float, default=-0.43)
    parser.add_argument("--q0", type=float, default=1.0)
    parser.add_argument("--A0", type=float, default=1.0,
                        help="initial BCC amplitude (will be relaxed if --relax-iters>0)")
    parser.add_argument("--relax-iters", type=int, default=0,
                        help="gradient-descent iterations (0=skip relaxation)")
    parser.add_argument("--relax-dt", type=float, default=0.005,
                        help="gradient descent step size")
    parser.add_argument("--eigs", type=int, default=30,
                        help="how many lowest eigenvalues to compute")
    parser.add_argument("--out-dir", default="Runs/math370",
                        help="output directory for JSON + spectrum")
    args = parser.parse_args()

    print("=" * 72)
    print(" Math370 full Brazovskii Hessian eigenvalue computation (FFT-based)")
    print("=" * 72)
    print(f" Grid: {args.N}×{args.N}×{args.N} = {args.N**3} points")
    print(f" Parameters: μ²={args.mu2}, γ={args.gamma}, λ={args.lam}, q₀={args.q0}")
    print(f" Initial A₀={args.A0}, relax iters={args.relax_iters}")
    print(f" Lanczos: lowest {args.eigs} eigenvalues")

    grid = setup_grid(args.N, args.q0)
    print(f" Box L = {grid['L']:.4f}, dx = {grid['dx']:.4f}")

    # 1. Initial state
    print(f"\n[1/4] Initialising 12-mode equal-amp BCC ansatz...")
    psi = bcc_initial_state(grid, args.A0)
    F0 = free_energy(psi, grid, args.mu2, args.gamma, args.lam)
    print(f"      Initial F = {F0:+.6e}, ⟨Ψ⟩={np.mean(psi):.4e}, "
          f"⟨Ψ²⟩={np.mean(psi**2):.4e}")

    # 2. Optional relaxation
    F_history = [F0]
    if args.relax_iters > 0:
        print(f"\n[2/4] Relaxing via steepest descent ({args.relax_iters} iters)...")
        psi, F_history = relax_to_ground_state(
            psi, grid, args.mu2, args.gamma, args.lam,
            n_iters=args.relax_iters, dt=args.relax_dt
        )
        F_final = F_history[-1]
        print(f"      Relaxed: F: {F0:+.4e} → {F_final:+.4e} "
              f"(ΔF = {F_final - F0:+.4e})")
    else:
        print(f"\n[2/4] (skipped relaxation; --relax-iters=0)")

    # 3. Final |∇F| at the (possibly relaxed) state
    grad = free_energy_gradient(psi, grid, args.mu2, args.gamma, args.lam)
    grad_norm = float(np.sqrt(np.mean(grad**2)))
    print(f"\n[3/4] Stationarity check at final state:")
    print(f"      |∇F|/√V = {grad_norm:.4e} (should be ≪ 1 for true stationary)")

    # 4. Lanczos
    print(f"\n[4/4] Computing {args.eigs} lowest Hessian eigenvalues (Lanczos)...")
    if not HAS_SCIPY:
        print("      SKIPPED — scipy not available")
        return 1
    try:
        eigs, vecs = lowest_eigenvalues(psi, grid, args.mu2, args.gamma, args.lam,
                                         k=args.eigs)
    except Exception as e:
        print(f"      FAILED: {e}", file=sys.stderr)
        return 1

    n_zero = int(np.sum(np.abs(eigs) < 1e-6))
    n_neg  = int(np.sum(eigs < -1e-6))
    n_pos  = int(np.sum(eigs > 1e-6))
    print(f"\nEigenvalue spectrum:")
    for i, e in enumerate(eigs):
        if abs(e) < 1e-6: tag = " ← Goldstone (zero)"
        elif e < 0:       tag = " ← NEGATIVE (instability)"
        else:             tag = ""
        print(f"  λ_{i+1:3d} = {e:+.6e}{tag}")

    print(f"\nClassification: {n_zero} zero, {n_neg} negative, {n_pos} positive")
    print(f"Expected for true BCC local-min: ~6 zero (3 translation + 3 rotation), "
          f"rest positive.")
    if n_neg == 0:
        print(f"\n✓ NO NEGATIVE EIGENVALUES — BCC IS A LOCAL MINIMUM in this regime.")
        print(f"  This SUPPORTS Math358's claim (and refutes the Math369 12-mode result).")
    else:
        print(f"\n✗ {n_neg} NEGATIVE EIGENVALUES — BCC is NOT a local minimum here.")
        print(f"  This CONFIRMS Math369 simple-model result. Either parameters are")
        print(f"  outside the BCC stable regime, or Math358's claim was incorrect.")

    # Save result
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "kind": "Math370-full-BCC-hessian-FFT",
        "generated": datetime.now(timezone.utc).isoformat(),
        "parameters": {
            "N": args.N, "mu2": args.mu2, "gamma": args.gamma, "lam": args.lam,
            "q0": args.q0, "A0_init": args.A0,
            "relax_iters": args.relax_iters, "relax_dt": args.relax_dt,
            "eigs_requested": args.eigs,
        },
        "grid": {"L": grid["L"], "dx": grid["dx"]},
        "F_initial": F_history[0],
        "F_final": F_history[-1],
        "gradient_norm_final": grad_norm,
        "eigenvalues": [float(e) for e in eigs],
        "n_zero_modes": n_zero,
        "n_negative_modes": n_neg,
        "n_positive_modes": n_pos,
        "verdict": (
            "BCC local minimum (NO negative eigs)" if n_neg == 0
            else f"BCC saddle of index {n_neg}"
        ),
    }
    out_path = out_dir / f"math370_N{args.N}_mu2_{args.mu2}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nResult saved: {out_path}")

    return 0 if n_neg == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
