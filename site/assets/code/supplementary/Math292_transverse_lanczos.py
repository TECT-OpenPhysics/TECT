#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math292-transverse-Hessian-Lanczos-2026-05-02
# Regime        : Brazovskii BCC-broken phase (Pillar 6 / F-Pillar6 verdict workflow)
# Module version: v1.0
# Sync doc      : Docs/manual/CODE_MANUAL.md (entry pending after first run)
# Last synced   : 2026-05-02
# === TECT VERSION HEADER END ===
"""
Math292 transverse-Hessian Lanczos diagnostic.

Computes the smallest few eigenvalues of the symmetrised Hessian
``H = 0.5 * (J + J^T)`` of the Brazovskii free-energy functional at a
candidate critical point, restricted to the transverse complement of the
known zero-mode subspace (3 translation modes by default, optionally + global
phase).

Math292 G3 acceptance gate:
    lambda_min^transverse >= 0  (PSD on transverse complement)

A negative smallest eigenvalue indicates the candidate is a saddle (NOT a
local minimum), which is structurally distinct from the BCC ground state.

Usage:
    python Codes/supplementary/Math292_transverse_lanczos.py \
        --psi <path/to/Psi.npy> \
        --N 32 --mu2 -0.7 \
        [--config Codes/pde/config_template_brazovskii.json] \
        [--L 16] [--k-zero-modes 3] [--n-eig 5] \
        [--include-phase-mode] [--tol 1e-6]

Output:
    JSON sidecar at <psi>.lanczos.json with eigenvalues + verdict.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
from scipy.sparse.linalg import LinearOperator, eigsh, lobpcg
from scipy.sparse.linalg import ArpackNoConvergence

# Allow the supplementary script to import the canonical PDE backend +
# symmetrisation helpers from the parent Codes/pde/ package.
_THIS = Path(__file__).resolve()
_REPO_ROOT = _THIS.parent.parent.parent  # .../Contents
_PDE_DIR = _REPO_ROOT / "Codes" / "pde"
if str(_PDE_DIR) not in sys.path:
    sys.path.insert(0, str(_PDE_DIR))

import real_backend_pt_bcc_mixed_v3 as backend  # noqa: E402
from tect_newton_krylov import (  # noqa: E402
    flatten_complex_field,
    unflatten_complex_field,
    build_zero_mode_projector,
    _compute_adjoint_jacobian_vec_v26,
    parse_L,
)


# ---------------------------------------------------------------------------
# §1. Real-flat <-> complex-field bridge
# ---------------------------------------------------------------------------

def complex_field_to_real_flat(Psi_c: np.ndarray) -> np.ndarray:
    """(3,N,N,N) complex -> (2*3*N^3,) real (re/im concatenated)."""
    return flatten_complex_field(Psi_c).astype(np.float64, copy=False)


def real_flat_to_complex_field(x_r: np.ndarray, shape: Tuple[int, ...]) -> np.ndarray:
    """Inverse of complex_field_to_real_flat."""
    return unflatten_complex_field(x_r.astype(np.float64, copy=False), shape)


# ---------------------------------------------------------------------------
# §2. Hessian operator with symmetrisation + zero-mode projection
# ---------------------------------------------------------------------------

class TransverseHessianOperator:
    """
    LinearOperator that applies P * H_sym * P, where:

        H_sym = 0.5 * (J + J^T)            # explicit real-symmetrisation
        J(v)  = backend.hessian_vec(Psi, v, params)
        J^T(v) = _compute_adjoint_jacobian_vec_v26(Psi, v, params)
        P     = (I - V V^T)                 # zero-mode orthogonal projector
                  with V from build_zero_mode_projector

    The resulting operator is real-symmetric on R^{2*3*N^3} and supplies the
    spectrum required by Math292 G3.
    """

    def __init__(self, Psi: np.ndarray, params: Dict[str, Any], *,
                 include_phase_mode: bool = False,
                 verbose: bool = False) -> None:
        self.Psi = np.ascontiguousarray(Psi, dtype=np.complex128)
        self.params = params
        self.shape_field = self.Psi.shape
        self.flat_dim = 2 * self.Psi.size  # real (re,im)
        self.verbose = verbose

        self.zmp = build_zero_mode_projector(
            self.Psi, self.params,
            include_translations=True,
            include_global_phase=include_phase_mode,
        )
        self.n_zero_modes = self.zmp.n_basis

        if self.verbose:
            print(f"[Math292-Lanczos] flat_dim = {self.flat_dim}")
            print(f"[Math292-Lanczos] zero-mode basis size = {self.n_zero_modes}")

        self._call_count = 0

    @property
    def shape(self) -> Tuple[int, int]:
        return (self.flat_dim, self.flat_dim)

    @property
    def dtype(self) -> np.dtype:
        return np.dtype(np.float64)

    def _matvec_J(self, v_complex: np.ndarray) -> np.ndarray:
        return backend.hessian_vec(self.Psi, v_complex, self.params)

    def _matvec_JT(self, v_complex: np.ndarray) -> np.ndarray:
        return _compute_adjoint_jacobian_vec_v26(self.Psi, v_complex, self.params)

    def matvec(self, x_real: np.ndarray) -> np.ndarray:
        # Zero-mode project the input
        x_proj = self.zmp.project(x_real)
        v_c = real_flat_to_complex_field(x_proj, self.shape_field)

        # H_sym v = 0.5 * (J v + J^T v)
        Jv_c = self._matvec_J(v_c)
        JTv_c = self._matvec_JT(v_c)
        Hv_c = 0.5 * (Jv_c + JTv_c)

        y_real = complex_field_to_real_flat(Hv_c)
        # Zero-mode project the output
        y_proj = self.zmp.project(y_real)

        self._call_count += 1
        if self.verbose and self._call_count % 10 == 0:
            print(f"  [matvec count] {self._call_count}")
        return y_proj

    def to_linear_operator(self) -> LinearOperator:
        return LinearOperator(
            shape=self.shape,
            matvec=self.matvec,
            rmatvec=self.matvec,  # symmetric
            dtype=self.dtype,
        )


# ---------------------------------------------------------------------------
# §3. Asymmetry diagnostic (sanity check on user-facing report)
# ---------------------------------------------------------------------------

def estimate_asymmetry(op: TransverseHessianOperator,
                        n_probe: int = 3, seed: int = 0) -> float:
    """
    Return ||(J - J^T) v|| / (||J v|| + ||J^T v||) averaged over n_probe random
    test vectors. Should be close to machine epsilon for a properly Hermitian
    physical Hessian.
    """
    rng = np.random.default_rng(seed)
    flat_dim = op.flat_dim
    ratios: List[float] = []
    for _ in range(n_probe):
        x = rng.standard_normal(flat_dim).astype(np.float64)
        x = op.zmp.project(x)
        v_c = real_flat_to_complex_field(x, op.shape_field)
        Jv = op._matvec_J(v_c)
        JTv = op._matvec_JT(v_c)
        diff = Jv - JTv
        denom = float(np.linalg.norm(Jv)) + float(np.linalg.norm(JTv)) + 1e-300
        ratios.append(float(np.linalg.norm(diff)) / denom)
    return float(np.mean(ratios))


# ---------------------------------------------------------------------------
# §4. Driver
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(
        description="Math292 transverse-Hessian Lanczos diagnostic")
    p.add_argument("--psi", required=True,
                   help="Path to candidate Psi .npy file (shape (3,N,N,N), complex128)")
    p.add_argument("--config", default="Codes/pde/config_template_brazovskii.json",
                   help="Brazovskii backend config JSON (default: standard template)")
    p.add_argument("--N", type=int, required=True, help="Grid dimension")
    p.add_argument("--L", type=str, default="16",
                   help="Box size or 'Npi' notation (default 16)")
    p.add_argument("--mu2", type=float, required=True,
                   help="Brazovskii mass-squared mu^2 at which Hessian is evaluated")
    p.add_argument("--k-zero-modes", type=int, default=3,
                   help="Expected number of zero modes (3 = 3 translations; informational)")
    p.add_argument("--n-eig", type=int, default=5,
                   help="Number of smallest-algebraic eigenvalues to compute (default 5)")
    p.add_argument("--include-phase-mode", action="store_true",
                   help="Also project out global U(1) phase mode (typically NOT a TECT symmetry)")
    p.add_argument("--tol", type=float, default=1e-6,
                   help="ARPACK eigsh tolerance (default 1e-6)")
    p.add_argument("--maxiter", type=int, default=2000,
                   help="ARPACK eigsh maxiter (default 2000)")
    p.add_argument("--ncv", type=int, default=None,
                   help="ARPACK Lanczos vector count (default: auto = max(2*n_eig+1, 20))")
    p.add_argument("--solver", choices=["eigsh", "lobpcg", "eigsh-shift-invert"],
                   default="eigsh",
                   help="Eigensolver backend (default: eigsh ARPACK). "
                        "Use 'lobpcg' for densely clustered spectra near zero. "
                        "Use 'eigsh-shift-invert' with --sigma for spectrum near a target.")
    p.add_argument("--sigma", type=float, default=None,
                   help="Shift value for shift-invert mode (only with --solver eigsh-shift-invert). "
                        "Returns eigenvalues near sigma. For 'is the smallest eigenvalue >= 0?', "
                        "try --sigma -1e-3 to probe slightly-negative spectrum efficiently.")
    p.add_argument("--no-cuda", action="store_true",
                   help="Disable CUDA/XPU (use CPU torch backend)")
    p.add_argument("--asymmetry-probe", action="store_true",
                   help="Run 3-vector asymmetry sanity check before Lanczos")
    p.add_argument("--output", default=None,
                   help="JSON sidecar path (default: <psi>.lanczos.json next to psi)")
    p.add_argument("--verbose", action="store_true", help="Print matvec progress")
    args = p.parse_args()

    # ------------------------------------------------------------------
    # Load Psi
    # ------------------------------------------------------------------
    psi_path = Path(args.psi)
    if not psi_path.is_file():
        print(f"[FATAL] Psi file not found: {psi_path}", file=sys.stderr)
        return 2
    Psi = np.load(psi_path)
    if Psi.dtype != np.complex128:
        Psi = Psi.astype(np.complex128, copy=False)
    if Psi.shape != (3, args.N, args.N, args.N):
        print(f"[FATAL] Psi shape {Psi.shape} != expected (3,{args.N},{args.N},{args.N})",
              file=sys.stderr)
        return 2
    rms = float(np.sqrt(np.mean(np.abs(Psi) ** 2)))
    print(f"[load] Psi shape = {Psi.shape}, dtype = {Psi.dtype}, RMS|Psi| = {rms:.6e}")

    # ------------------------------------------------------------------
    # Build params dict (mirror continuation_mu2_v25 logic)
    # ------------------------------------------------------------------
    config_path = Path(args.config)
    if not config_path.is_file():
        config_path = _REPO_ROOT / args.config
    with open(config_path, "r", encoding="utf-8") as f:
        params = json.load(f)
    L = float(parse_L(args.L))
    Y = float(params.get("Y", 1.0))
    q0 = float(params["q0"])
    params["N"] = args.N; params["L"] = L
    params["Lx"] = L; params["Ly"] = L; params["Lz"] = L
    params["Nx"] = args.N; params["Ny"] = args.N; params["Nz"] = args.N
    # Brazovskii kinetic-locking convention (mirror v25 driver):
    # r = mu2 + Y * q0^4 ; Z = -2 Y q0^2 ; mu2 stored independently.
    params["mu2"] = float(args.mu2)
    params["r"] = float(args.mu2 + Y * (q0 ** 4))
    params["Z"] = float(-2.0 * Y * (q0 ** 2))
    params["Y"] = Y
    if args.no_cuda:
        params["use_cuda"] = False
        params["use_xpu"] = False
        params["device"] = "cpu"
    print(f"[params] mu2 = {params['mu2']:.6e}, r = {params['r']:.6e}, "
          f"Z = {params['Z']:.6e}, Y = {params['Y']:.4f}, L = {L:.6f}, N = {args.N}")

    # ------------------------------------------------------------------
    # Sanity: residual norm at Psi (how close to a critical point are we?)
    # ------------------------------------------------------------------
    R = backend.residual(Psi, params)
    res_norm = float(np.linalg.norm(R)) / math.sqrt(R.size)
    print(f"[sanity] ||R[Psi]||/sqrt(dof) = {res_norm:.6e}")

    # ------------------------------------------------------------------
    # Build Hessian operator
    # ------------------------------------------------------------------
    op = TransverseHessianOperator(
        Psi, params,
        include_phase_mode=args.include_phase_mode,
        verbose=args.verbose,
    )
    if op.n_zero_modes != args.k_zero_modes and not args.include_phase_mode:
        print(f"[warn] zero-mode basis size = {op.n_zero_modes} differs from "
              f"--k-zero-modes = {args.k_zero_modes} (informational only)")

    asym_ratio: float = float("nan")
    if args.asymmetry_probe:
        print("[asymmetry probe] running 3 random matvecs ...")
        asym_ratio = estimate_asymmetry(op, n_probe=3)
        print(f"[asymmetry probe] avg ||(J-J^T)v|| / (||Jv||+||J^Tv||) = {asym_ratio:.3e}")

    # ------------------------------------------------------------------
    # Lanczos: smallest algebraic eigenvalues of P H_sym P
    # ------------------------------------------------------------------
    LO = op.to_linear_operator()
    ncv = args.ncv if args.ncv is not None else max(2 * args.n_eig + 1, 20)
    print(f"[{args.solver}] which='SA', n_eig = {args.n_eig}, ncv = {ncv}, "
          f"tol = {args.tol:.1e}, maxiter = {args.maxiter}")

    eigvals: np.ndarray
    eigvecs: np.ndarray
    converged_full = True
    n_converged = 0
    t0 = time.time()
    try:
        if args.solver == "eigsh":
            eigvals, eigvecs = eigsh(
                LO, k=args.n_eig, which="SA",
                tol=args.tol, maxiter=args.maxiter, ncv=ncv,
                return_eigenvectors=True,
            )
            n_converged = int(eigvals.size)
        elif args.solver == "eigsh-shift-invert":
            if args.sigma is None:
                print("[FATAL] --sigma required for eigsh-shift-invert", file=sys.stderr)
                return 3
            print(f"[eigsh-shift-invert] sigma = {args.sigma:+.6e}, mode = 'normal'")
            eigvals, eigvecs = eigsh(
                LO, k=args.n_eig, sigma=args.sigma, which="LM",
                tol=args.tol, maxiter=args.maxiter, ncv=ncv,
                return_eigenvectors=True,
            )
            n_converged = int(eigvals.size)
        else:  # lobpcg
            rng = np.random.default_rng(0)
            X0 = rng.standard_normal((op.flat_dim, args.n_eig)).astype(np.float64)
            # Project initial guess off zero modes for cleaner convergence
            for j in range(args.n_eig):
                X0[:, j] = op.zmp.project(X0[:, j])
                X0[:, j] /= np.linalg.norm(X0[:, j]) + 1e-300
            print(f"[lobpcg] random initial subspace size = {args.n_eig}")
            eigvals, eigvecs = lobpcg(
                LO, X0, tol=args.tol, maxiter=args.maxiter,
                largest=False, verbosityLevel=1 if args.verbose else 0,
            )
            n_converged = int(eigvals.size)
    except ArpackNoConvergence as exc:
        # ARPACK partial-result salvage (key diagnostic for clustered spectra)
        eigvals = exc.eigenvalues
        eigvecs = exc.eigenvectors if exc.eigenvectors is not None else np.zeros((op.flat_dim, 0))
        n_converged = int(eigvals.size)
        converged_full = False
        print(f"[ARPACK PARTIAL] {n_converged}/{args.n_eig} eigenvalues converged "
              f"after {op._call_count} matvecs.", file=sys.stderr)
        print(f"[ARPACK PARTIAL] This usually indicates densely clustered spectrum "
              f"near the target (here: SA / smallest algebraic).", file=sys.stderr)
        if n_converged == 0:
            print(f"[FATAL] zero eigenvalues recovered; cannot diagnose", file=sys.stderr)
            return 3
    except Exception as exc:
        print(f"[FATAL] {args.solver} failed: {exc}", file=sys.stderr)
        return 3
    wall = time.time() - t0

    # Sort ascending (eigsh returns roughly sorted but enforce)
    if eigvals.size > 0:
        order = np.argsort(eigvals)
        eigvals = eigvals[order]
        if eigvecs.shape[1] > 0:
            eigvecs = eigvecs[:, order]

    print(f"[{args.solver}] {'DONE' if converged_full else 'PARTIAL'} "
          f"in {wall:.1f}s, total matvecs = {op._call_count}, "
          f"converged = {n_converged}/{args.n_eig}")
    for i, ev in enumerate(eigvals):
        # zero-mode contamination check on each eigenvector
        x = eigvecs[:, i]
        x_proj = op.zmp.project(x)
        residual_in_zmode = float(np.linalg.norm(x - x_proj))
        x_norm = float(np.linalg.norm(x))
        proj_ratio = residual_in_zmode / (x_norm + 1e-300)
        print(f"  lambda[{i}] = {ev:+.6e}   "
              f"(zero-mode contamination ratio = {proj_ratio:.2e})")

    # ------------------------------------------------------------------
    # Math292 G3 verdict
    # ------------------------------------------------------------------
    lambda_min = float(eigvals[0])
    eps_g3 = 1e-6  # numerical-zero tolerance per Math292 §G3
    if not converged_full:
        verdict = "INDETERMINATE"
        verdict_detail = (
            f"Eigensolver returned only {n_converged}/{args.n_eig} converged "
            f"eigenvalues after {op._call_count} matvecs. "
            f"Recovered partial smallest eigenvalues: {[f'{v:+.4e}' for v in eigvals.tolist()]}. "
            f"Non-convergence indicates densely clustered spectrum near target, "
            f"typically caused by additional zero modes (e.g. BCC orientation, "
            f"internal phase) beyond the projected {op.n_zero_modes}. "
            f"Math292 G3 cannot be definitively decided from this run; "
            f"recommend (i) re-run with --solver lobpcg or "
            f"--solver eigsh-shift-invert --sigma -1e-3, "
            f"(ii) extend zero-mode projector with rotation/phase modes, "
            f"OR (iii) converge Psi further (||R||/sqrt(dof) < 1e-5) before re-evaluating."
        )
    elif lambda_min >= -eps_g3:
        verdict = "PASS"
        verdict_detail = (
            f"lambda_min = {lambda_min:+.6e} >= -eps_g3 = {-eps_g3:.1e} : "
            f"transverse Hessian is PSD within numerical tolerance. "
            f"Candidate Psi is consistent with a local-minimum BCC ground state."
        )
    else:
        verdict = "FAIL"
        verdict_detail = (
            f"lambda_min = {lambda_min:+.6e} < -eps_g3 = {-eps_g3:.1e} : "
            f"transverse Hessian has NEGATIVE eigenvalue. "
            f"Candidate Psi is a SADDLE (Morse index >= 1), NOT a local "
            f"minimum. Math292 G3 acceptance gate FAILED."
        )
    print("\n=========== Math292 G3 verdict ===========")
    print(f"  {verdict}")
    print(f"  {verdict_detail}")
    print("==========================================\n")

    # ------------------------------------------------------------------
    # JSON sidecar
    # ------------------------------------------------------------------
    out_path = (Path(args.output) if args.output is not None
                else psi_path.with_suffix(psi_path.suffix + ".lanczos.json"))
    payload = {
        "schema": "math292-transverse-lanczos-v1.1",
        "psi_path": str(psi_path),
        "config_path": str(config_path),
        "N": args.N,
        "L": L,
        "mu2": params["mu2"],
        "r": params["r"],
        "Z": params["Z"],
        "Y": params["Y"],
        "q0": q0,
        "rms_psi": rms,
        "residual_norm_per_sqrt_dof": res_norm,
        "n_zero_modes": op.n_zero_modes,
        "include_phase_mode": bool(args.include_phase_mode),
        "asymmetry_ratio": asym_ratio,
        "solver": args.solver,
        "sigma": args.sigma,
        "converged_full": bool(converged_full),
        "n_converged": int(n_converged),
        "n_requested": int(args.n_eig),
        "eigenvalues": [float(v) for v in eigvals],
        "eigvec_zero_mode_contamination": [
            float(np.linalg.norm(eigvecs[:, i] - op.zmp.project(eigvecs[:, i]))
                  / (np.linalg.norm(eigvecs[:, i]) + 1e-300))
            for i in range(eigvals.size if eigvecs.shape[1] > 0 else 0)
        ],
        "lambda_min": lambda_min,
        "math292_g3_verdict": verdict,
        "math292_g3_detail": verdict_detail,
        "eigsh_tol": args.tol,
        "eigsh_maxiter": args.maxiter,
        "eigsh_ncv": ncv,
        "eigsh_n_matvecs": int(op._call_count),
        "eigsh_wall_seconds": float(wall),
        "theory_tag": "Math292-transverse-Hessian-Lanczos-v1.1-2026-05-02",
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"[output] sidecar written to {out_path}")

    if verdict == "PASS":
        return 0
    if verdict == "FAIL":
        return 1
    return 4  # INDETERMINATE


if __name__ == "__main__":
    sys.exit(main())
