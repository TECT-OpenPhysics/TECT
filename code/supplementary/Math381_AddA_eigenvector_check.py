#!/usr/bin/env python3
# =====================================================================
# Math381_AddA_eigenvector_check.py  v1.0 (2026-05-10)
#
# Math381 Pathway A: verify that the lowest 6 Hessian eigenvalues at
# a Math376/378/379/380 converged state correspond to the 6 expected
# Goldstone modes (3 translation + 3 rotation) by computing
# eigenvector overlap with the analytical Goldstone patterns.
#
# Theory:
#   For BCC condensate Psi*(r), the broken continuous symmetries are
#   3 translations (T_i) and 3 rotations (R_i). The Goldstone modes
#   are the corresponding generator action on the condensate:
#     translation: delta_T_i Psi* = grad_i Psi*(r)         (i = x, y, z)
#     rotation:    delta_R_i Psi* = (r x grad)_i Psi*(r)  (i = x, y, z)
#
#   On a finite cubic lattice, these are NOT exactly Hessian zero
#   modes (cubic point group breaks SO(3) and translation invariance);
#   they should be quasi-Goldstone modes with small mass O(h^2).
#
# Verification protocol:
#   1. Load converged state (single-channel real, (N,N,N))
#   2. Compute the 6 analytical Goldstone patterns via FFT-based
#      gradients
#   3. Gram-Schmidt orthonormalise to get a 6-dim Goldstone subspace
#   4. Compute the 6 lowest Hessian eigenvectors
#   5. Project each eigenvector onto the Goldstone subspace; report
#      total "energy" = sum of squared overlaps
#   6. PASS criterion: total overlap > 0.95 (each eigenvector almost
#      entirely in the Goldstone subspace)
#
# Usage:
#   python -u Codes/supplementary/Math381_AddA_eigenvector_check.py \
#       --state Runs/math379/math376_converged_N64_mu2_-1p0.npy \
#       --mu2 -1.0 --N 64 --L 124.40072
#
# Dependencies: numpy + scipy.sparse.linalg.
# =====================================================================
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

Q0_PHYSICAL: float = 0.6801747616
Y_LOCKED: float = 1.0
LAM_LOCKED: float = -0.43
GAM_LOCKED: float = +1.62
Z0_LOCKED: np.ndarray = np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0)


def import_math376(repo_root: Path):
    m376_path = repo_root / "Codes" / "supplementary" / "Math376_production_state_hessian.py"
    spec = importlib.util.spec_from_file_location("m376", str(m376_path))
    m376 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m376)
    return m376


def load_state(npy_path: Path) -> np.ndarray:
    arr = np.load(npy_path)
    if arr.ndim == 3 and np.isrealobj(arr):
        return arr.astype(np.float64)
    elif arr.ndim == 4 and arr.shape[0] == 3:
        if not np.iscomplexobj(arr):
            arr = arr.astype(np.complex128)
        return np.real(np.einsum("a,axyz->xyz", Z0_LOCKED, arr))
    else:
        raise ValueError("Unsupported shape {}".format(arr.shape))


def fft_gradient(Psi: np.ndarray, L: float) -> tuple:
    """Return (d/dx, d/dy, d/dz) of Psi via FFT."""
    N = Psi.shape[0]
    dx = L / N
    k1d = 2.0 * np.pi * np.fft.fftfreq(N, d=dx)
    KX, KY, KZ = np.meshgrid(k1d, k1d, k1d, indexing="ij")
    Psi_k = np.fft.fftn(Psi)
    dPsi_x = np.real(np.fft.ifftn(1j * KX * Psi_k))
    dPsi_y = np.real(np.fft.ifftn(1j * KY * Psi_k))
    dPsi_z = np.real(np.fft.ifftn(1j * KZ * Psi_k))
    return dPsi_x, dPsi_y, dPsi_z


def goldstone_translation_modes(Psi: np.ndarray, L: float) -> list:
    """3 translation Goldstone candidates: delta = grad_i Psi."""
    return list(fft_gradient(Psi, L))


def goldstone_rotation_modes(Psi: np.ndarray, L: float) -> list:
    """3 rotation Goldstone candidates: delta_i = (r x grad)_i Psi.

    Real-space: r is the position, grad is FFT-gradient.
    delta_x = y * d/dz Psi - z * d/dy Psi
    delta_y = z * d/dx Psi - x * d/dz Psi
    delta_z = x * d/dy Psi - y * d/dx Psi
    """
    N = Psi.shape[0]
    dx_grid = L / N
    x = np.arange(N) * dx_grid - 0.5 * L
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    dPsi_x, dPsi_y, dPsi_z = fft_gradient(Psi, L)
    delta_Rx = Y * dPsi_z - Z * dPsi_y
    delta_Ry = Z * dPsi_x - X * dPsi_z
    delta_Rz = X * dPsi_y - Y * dPsi_x
    return [delta_Rx, delta_Ry, delta_Rz]


def gram_schmidt(vectors: list) -> list:
    """Gram-Schmidt orthonormalisation. Returns list of unit-norm
    vectors spanning the same subspace; degenerate vectors dropped."""
    out = []
    tol = 1e-10
    for v in vectors:
        v_flat = v.ravel().astype(np.float64)
        for u in out:
            v_flat = v_flat - np.dot(u, v_flat) * u
        nrm = np.linalg.norm(v_flat)
        if nrm > tol:
            out.append(v_flat / nrm)
    return out


def hessian_eigenvectors(Psi: np.ndarray, grid: dict, params: dict, n_eigs: int):
    """Compute lowest n_eigs eigenvectors of the Hessian via Lanczos."""
    from scipy.sparse.linalg import LinearOperator, eigsh
    N = grid["N"]
    size = N**3

    # Need access to Math376's hessian_apply
    # We pass it via closure
    from importlib import import_module
    repo_root = Path(__file__).resolve().parent.parent.parent
    m376 = import_math376(repo_root)

    def matvec(v):
        return m376.hessian_apply(v.reshape(N, N, N), Psi, grid, params).ravel()

    op = LinearOperator((size, size), matvec=matvec, dtype=np.float64)

    eigs, vecs = eigsh(op, k=n_eigs, which="SA", return_eigenvectors=True,
                        maxiter=5000, tol=1e-9)
    # eigs: (n_eigs,), vecs: (size, n_eigs)
    order = np.argsort(eigs)
    return eigs[order], vecs[:, order]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True,
                        help="path to converged .npy state")
    parser.add_argument("--mu2", type=float, default=-1.0)
    parser.add_argument("--lam", type=float, default=LAM_LOCKED)
    parser.add_argument("--gam", type=float, default=GAM_LOCKED)
    parser.add_argument("--Y", type=float, default=Y_LOCKED)
    parser.add_argument("--q0", type=float, default=Q0_PHYSICAL)
    parser.add_argument("--N", type=int, default=None)
    parser.add_argument("--L", type=float, default=None)
    parser.add_argument("--n-eigs", type=int, default=6,
                        help="number of low Hessian eigenvectors to project (default 6)")
    parser.add_argument("--out-dir", default="Runs/math381")
    parser.add_argument("--out-tag", default=None)
    args = parser.parse_args()

    state_path = Path(args.state)
    if not state_path.exists():
        print("ERROR: state not found: {}".format(state_path), file=sys.stderr)
        return 2

    print("=" * 76)
    print(" Math381-AddA: eigenvector overlap with Goldstone patterns")
    print("=" * 76)
    print(" State: {}".format(state_path))

    Psi = load_state(state_path)
    N = args.N if args.N is not None else Psi.shape[0]
    L = args.L if args.L is not None else 2.0 * (2.0 * math.pi / args.q0)

    if Psi.shape != (N, N, N):
        print("ERROR: state shape {} != ({},{},{})".format(Psi.shape, N, N, N),
              file=sys.stderr)
        return 2

    print(" Grid: {}^3 = {}, L = {:.4f}, dx = {:.4f}".format(
        N, N**3, L, L/N))
    print(" Locked params: mu^2 = {}, lam = {}, gam = {}".format(
        args.mu2, args.lam, args.gam))
    print(" <Psi> = {:+.4e}, <Psi^2> = {:.4e}".format(Psi.mean(), (Psi**2).mean()))

    # Step 1: build Goldstone candidates
    print("")
    print("[1/4] Computing 3 translation + 3 rotation Goldstone patterns ...")
    trans_modes = goldstone_translation_modes(Psi, L)
    rot_modes = goldstone_rotation_modes(Psi, L)
    all_goldstone = trans_modes + rot_modes
    norms = [np.linalg.norm(m.ravel()) for m in all_goldstone]
    labels = ["T_x", "T_y", "T_z", "R_x", "R_y", "R_z"]
    print("  Goldstone candidate L_2 norms:")
    for lbl, n_ in zip(labels, norms):
        print("    {} : {:.4e}".format(lbl, n_))

    # Step 2: Gram-Schmidt orthonormalise
    print("")
    print("[2/4] Gram-Schmidt orthonormalising Goldstone subspace ...")
    G = gram_schmidt(all_goldstone)
    print("  Effective Goldstone subspace dim = {} (started with 6)".format(len(G)))
    if len(G) < 6:
        print("  WARN: subspace dimension less than 6 — some Goldstones linearly dependent")

    # Step 3: compute lowest n_eigs Hessian eigenvectors
    print("")
    print("[3/4] Computing {} lowest Hessian eigenvectors (Lanczos) ...".format(args.n_eigs))
    grid = {"N": N, "L": L, "dx": L/N, "dV": (L/N)**3}
    k1d = 2.0 * np.pi * np.fft.fftfreq(N, d=L/N)
    KX, KY, KZ = np.meshgrid(k1d, k1d, k1d, indexing="ij")
    grid["K2"] = KX**2 + KY**2 + KZ**2

    params = {
        "r": args.mu2 + args.Y * args.q0**4,
        "Z": -2.0 * args.Y * args.q0**2,
        "Y": args.Y, "lam": args.lam, "gam": args.gam,
        "q0": args.q0, "mu2": args.mu2,
    }
    eigs, vecs = hessian_eigenvectors(Psi, grid, params, args.n_eigs)
    print("  Lowest {} eigenvalues: {}".format(args.n_eigs,
        ["{:+.4e}".format(e) for e in eigs]))

    # Step 4: project each eigenvector onto Goldstone subspace
    print("")
    print("[4/4] Projecting eigenvectors onto Goldstone subspace ...")

    # Build projection matrix M[j,k] = <eigvec_j | goldstone_k>
    n_v = vecs.shape[1]
    n_g = len(G)
    M = np.zeros((n_v, n_g))
    for j in range(n_v):
        v_j = vecs[:, j]
        # eigvec is already unit-norm from eigsh
        for k in range(n_g):
            M[j, k] = np.dot(v_j, G[k])

    # Total overlap = sum over Goldstone basis of squared projection
    overlaps = np.sum(M**2, axis=1)
    print("")
    print("  Eigenvector overlaps with 6-dim Goldstone subspace:")
    print("  ", " " * 10, "  ".join(["{:>9s}".format(lbl) for lbl in labels[:n_g]]),
          "   total")
    for j in range(n_v):
        row = "  lam_{:2d} = {:+.4e}".format(j+1, eigs[j])
        for k in range(n_g):
            row += "  {:+.4e}".format(M[j, k])
        row += "   {:.4f}".format(overlaps[j])
        print(row)

    print("")
    print("=== Verdict ===")
    n_confirmed = int(np.sum(overlaps > 0.95))
    print("  Eigenvectors with Goldstone overlap > 0.95 : {}/{}".format(n_confirmed, n_v))
    print("  Average overlap of lowest 6 : {:.4f}".format(np.mean(overlaps[:6])))
    print("  Min overlap (lowest 6)      : {:.4f}".format(np.min(overlaps[:6])))

    if n_confirmed >= 6:
        verdict = "PASS"
        print("\n  PASS: lowest 6 eigenvectors are confirmed Goldstone modes.")
        print("  Math378/379 PASS-WITH-FINITE-N-CAVEAT can be promoted to T6 PROVED.")
    elif n_confirmed >= 3:
        verdict = "PARTIAL-PASS"
        print("\n  PARTIAL-PASS: {} of 6 eigenvectors confirmed Goldstone.".format(n_confirmed))
        print("  Some near-zero modes may have non-Goldstone components (e.g.,")
        print("  cubic-grid breaks rotation Goldstones partially).")
    else:
        verdict = "FAIL"
        print("\n  FAIL: only {} of 6 eigenvectors confirmed Goldstone.".format(n_confirmed))
        print("  Near-zero modes are NOT primarily Goldstones — possible soft instability.")

    out_tag = args.out_tag or "addA_{}".format(state_path.stem)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "kind": "Math381-AddA-eigenvector-check",
        "generated": datetime.now(timezone.utc).isoformat(),
        "state_path": str(state_path),
        "params": params,
        "N": N, "L": L,
        "eigenvalues": [float(e) for e in eigs],
        "goldstone_subspace_dim": n_g,
        "overlap_matrix": M.tolist(),
        "total_overlaps": overlaps.tolist(),
        "n_confirmed_goldstone": n_confirmed,
        "verdict": verdict,
    }
    out_path = out_dir / "math381_{}.json".format(out_tag)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print("\nResult saved: {}".format(out_path))

    return 0 if verdict == "PASS" else (1 if verdict == "FAIL" else 3)


if __name__ == "__main__":
    sys.exit(main())
