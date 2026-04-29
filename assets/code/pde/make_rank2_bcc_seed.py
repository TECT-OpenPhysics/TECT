# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v1.0
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
"""
make_rank2_bcc_seed.py
======================
Generate BCC-condensate initial conditions with EXACT rank-2 internal structure
for TECT Brazovskii gradient-flow simulations.

Physics
-------
The Brazovskii free energy on the BCC first shell has a saddle point at the
rank-1 "democratic" state (all 12 modes share one internal direction).  The
true minimum is the rank-2 state where each BCC family F_alpha points in a
distinct 2D subspace of the n_internal-dimensional order-parameter space.

This script constructs three classes of rank-2 initial conditions:

  Mode A – "family-split":
    Each of the 3 BCC families is assigned a different linear combination of
    two internal basis vectors (v1, v2), so the 12x3 amplitude matrix has
    exactly rank 2 by construction.

  Mode B – "chiral":
    Family amplitudes involve a complex relative phase exp(2pi i alpha/3),
    exploiting the Z3-symmetry of the BCC triplet coupling.

  Mode C – "random-SVD-projected":
    Draw fully random complex amplitudes, then SVD-project to the top-2
    singular values.  Repeat for N_seeds seeds.

All modes apply the physical reality condition a_{-Q} = conj(a_Q) before
IFFT-ing to real space, ensuring Psi(r) is real-valued.

Usage
-----
  python make_rank2_bcc_seed.py [--grid 64] [--L 16.0] [--n-int 3]
                                 [--amplitude 0.25] [--mode A|B|C|all]
                                 [--n-seeds 8] [--out-dir .]

Output
------
  Psi_rank2_<mode>_seed<k>.npy  -- shape (n_internal, grid, grid, grid), complex128
  rank2_seed_manifest.txt       -- SVD singular-value confirmation for each file
"""

import argparse
import numpy as np
import os
import sys

# ─── BCC geometry ────────────────────────────────────────────────────────────

def bcc_first_shell(L, grid):
    """
    Return 12 BCC first-shell wavevectors at |k| = q0 = pi*sqrt(2)/a,
    where a = L/grid.

    BCC first-shell in reciprocal space: permutations of (+/-1, +/-1, 0) * 2pi/a.
    Family F_alpha: vectors with alpha-th component == 0.
      F0 (kx=0): 4 vectors
      F1 (ky=0): 4 vectors
      F2 (kz=0): 4 vectors
    """
    a = L / grid
    dk = 2 * np.pi / L          # reciprocal lattice spacing

    # All (pm1, pm1, 0) permutations in reciprocal-lattice units
    raw = []
    for i in range(3):
        for s1 in [+1, -1]:
            for s2 in [+1, -1]:
                v = [0, 0, 0]
                # Place zeros at axis i, signs at the other two
                axes = [j for j in range(3) if j != i]
                v[axes[0]] = s1
                v[axes[1]] = s2
                v[i] = 0
                raw.append((tuple(v), i))   # (vector, family_index)

    # Convert to physical k-vectors and remove duplicates (direction, not sign)
    seen = set()
    Q_list   = []      # physical k-vector, shape (12, 3)
    fam_list = []      # family index in {0, 1, 2}
    for v, fam in raw:
        key = v
        if key not in seen:
            seen.add(key)
            Q_list.append(np.array(v, dtype=float) * dk)
            fam_list.append(fam)

    Q_list   = np.array(Q_list)    # (12, 3)
    fam_list = np.array(fam_list)  # (12,)
    q0 = np.linalg.norm(Q_list[0])
    return Q_list, fam_list, q0


def find_pairs(Q_list, tol=1e-8):
    """
    Return list of (i, j) pairs such that Q_list[i] + Q_list[j] ≈ 0.
    The BCC first shell is closed under negation, so every Q has a -Q partner.
    """
    N = len(Q_list)
    used = [False] * N
    pairs = []
    for i in range(N):
        if used[i]:
            continue
        for j in range(i+1, N):
            if used[j]:
                continue
            if np.linalg.norm(Q_list[i] + Q_list[j]) < tol:
                pairs.append((i, j))
                used[i] = True
                used[j] = True
                break
    return pairs   # 6 pairs for the 12 BCC first-shell vectors


# ─── Amplitude constructors ───────────────────────────────────────────────────

def amp_family_split(Q_list, fam_list, n_int, amplitude, rng):
    """
    Mode A: assign each BCC family a distinct column subspace of ℂ^n_int.

    All modes in family alpha share: a_Q = sigma_Q * (cos(theta_alpha) v1 + sin(theta_alpha) v2)
    with theta_0=0, theta_1=2pi/3, theta_2=4pi/3.
    v1, v2 are random orthonormal vectors in ℂ^n_int.
    sigma_Q = amplitude (same for all Q within a family, ±sign for +/-Q pair).
    """
    # Two random orthonormal internal vectors
    raw1 = rng.standard_normal(n_int) + 1j * rng.standard_normal(n_int)
    v1 = raw1 / np.linalg.norm(raw1)
    raw2 = rng.standard_normal(n_int) + 1j * rng.standard_normal(n_int)
    raw2 -= np.dot(np.conj(v1), raw2) * v1   # Gram-Schmidt
    v2 = raw2 / np.linalg.norm(raw2)

    thetas = [0.0, 2*np.pi/3, 4*np.pi/3]
    A = np.zeros((len(Q_list), n_int), dtype=complex)

    pairs = find_pairs(Q_list)
    pair_map = {}
    for (i, j) in pairs:
        pair_map[i] = j
        pair_map[j] = i

    for idx, (Q, fam) in enumerate(zip(Q_list, fam_list)):
        th = thetas[fam]
        direction = np.cos(th) * v1 + np.sin(th) * v2
        direction /= np.linalg.norm(direction)
        # Determine if this is the "positive" member of the pair
        j = pair_map[idx]
        if idx < j:        # positive partner
            A[idx] = amplitude * direction
        else:              # negative partner: reality condition
            A[idx] = np.conj(A[j])

    return A


def amp_chiral(Q_list, fam_list, n_int, amplitude, rng, phi=2*np.pi/3):
    """
    Mode B: BCC triplet-locking with Z3 phase.

    Each family alpha carries a complex phase exp(i alpha phi):
      a_Q = amplitude * exp(i alpha phi) * v    for Q in F_alpha
    Reality condition: a_{-Q} = conj(a_Q).

    This maps to the BCC cubic term ∫ Ψ^3:
      Σ_alpha exp(i phi_alpha) ~ Σ_alpha exp(i 2pi alpha/3) = 0 (for phi=2pi/3)
    So phi=2pi/3 DECOUPLES the families from the cubic term — phi ≠ 2pi/3 gives
    the maximum coupling.  Use phi = pi/3 for maximum triplet locking.
    """
    raw1 = rng.standard_normal(n_int) + 1j * rng.standard_normal(n_int)
    v1 = raw1 / np.linalg.norm(raw1)
    raw2 = rng.standard_normal(n_int) + 1j * rng.standard_normal(n_int)
    raw2 -= np.dot(np.conj(v1), raw2) * v1
    v2 = raw2 / np.linalg.norm(raw2)

    A = np.zeros((len(Q_list), n_int), dtype=complex)
    pairs = find_pairs(Q_list)
    pair_map = {i: j for (i, j) in pairs}
    pair_map.update({j: i for (i, j) in pairs})

    for idx, (Q, fam) in enumerate(zip(Q_list, fam_list)):
        j = pair_map[idx]
        if idx < j:
            phase = np.exp(1j * fam * phi)
            direction = v1 + 1j * v2 * np.sin(fam * np.pi / 2)
            direction /= np.linalg.norm(direction)
            A[idx] = amplitude * phase * direction
        else:
            A[idx] = np.conj(A[j])

    return A


def amp_random_svd(Q_list, n_int, amplitude, rng, rank=2):
    """
    Mode C: random amplitudes projected to top-<rank> singular values.

    1. Draw A_raw ~ CN(0, sigma) for all (Q, s) pairs
    2. Apply reality condition: a_{-Q} = conj(a_Q)
    3. SVD: A = U Σ V†
    4. Truncate: A_rank2 = U[:, :rank] * Σ[:rank] * V†[:rank, :]
    5. Rescale so ||A||_F = amplitude * sqrt(12)

    Note: this gives GLOBAL rank-2 but per-family rank may exceed 2 because
    the left singular vectors are complex (violating the Gr_R constraint).
    For physically correct per-family rank-2 (Prop 5.3 Step 1), use Mode D.
    """
    pairs = find_pairs(Q_list)
    pair_map = {i: j for (i, j) in pairs}
    pair_map.update({j: i for (i, j) in pairs})

    A = np.zeros((len(Q_list), n_int), dtype=complex)
    for i, j in pairs:
        raw = rng.standard_normal(n_int) + 1j * rng.standard_normal(n_int)
        raw /= np.linalg.norm(raw)
        A[i] = raw
        A[j] = np.conj(raw)   # reality condition

    # SVD-project to rank 2
    U, s, Vh = np.linalg.svd(A, full_matrices=False)
    s_trunc = np.zeros_like(s)
    s_trunc[:rank] = s[:rank]
    A_trunc = U * s_trunc[None, :] @ Vh

    # Rescale
    frob = np.linalg.norm(A_trunc, 'fro')
    target_frob = amplitude * np.sqrt(len(Q_list))
    A_trunc *= (target_frob / frob)

    return A_trunc


def amp_real_plane(Q_list, fam_list, n_int, amplitude, rng):
    """
    Mode D: Real Grassmannian Gr_R(2, n_int) construction.

    Physics basis (Proposition 5.3 Step 1, TECT Paper I):
      Reality condition a_{-Q} = conj(a_Q) + global rank-2 constraint
      forces the occupied 2-plane E into Gr_R(2, n_int) [real Grassmannian].
      This means the basis vectors {u1, u2} spanning E must be REAL.
      Complex mode amplitudes (alpha_j, beta_j) are allowed per half-shell mode.

    Construction:
      1. Draw REAL orthonormal 2-plane {u1, u2} ⊂ R^n_int via QR
      2. For each half-shell mode j: a_j = alpha_j * u1 + beta_j * u2
         with complex scalars alpha_j, beta_j ~ CN(0,1)
      3. Partner mode: a_{-j} = conj(a_j)   (exact reality condition)

    Properties:
      - Global SVD rank = 2  (all modes in same real 2-plane E)
      - Per-family SVD rank = 2  (complex scalars generically independent)
      - c_1(E) = 0  (E is real → Gr_R)
      - Reality condition: exact by construction
    """
    pairs = find_pairs(Q_list)
    pair_map = {i: j for (i, j) in pairs}
    pair_map.update({j: i for (i, j) in pairs})

    # Real orthonormal 2-plane {u1, u2} in R^n_int
    U_rand, _ = np.linalg.qr(rng.standard_normal((n_int, 2)))
    u1 = U_rand[:, 0].astype(complex)   # keep complex dtype for arithmetic
    u2 = U_rand[:, 1].astype(complex)

    A = np.zeros((len(Q_list), n_int), dtype=complex)
    for i, j in pairs:
        # Complex scalars for half-shell mode i
        alpha = rng.standard_normal() + 1j * rng.standard_normal()
        beta  = rng.standard_normal() + 1j * rng.standard_normal()
        a_i = alpha * u1 + beta * u2
        A[i] = a_i
        A[j] = np.conj(a_i)    # exact reality condition: a_{-Q} = a_Q^*

    # Rescale: ||A||_F = amplitude * sqrt(12)
    frob = np.linalg.norm(A, 'fro')
    target_frob = amplitude * np.sqrt(len(Q_list))
    A *= (target_frob / frob)

    return A


# ─── Real-space field constructor ─────────────────────────────────────────────

def build_psi(A, Q_list, grid, L, n_int):
    """
    Construct Ψ_s(r) = sum_Q A[Q, s] * exp(i Q·r) in real space.

    Uses discrete FFT: place amplitudes at the nearest k-grid point,
    then IFFT.  Returns complex128 array of shape (n_int, grid, grid, grid).
    """
    Ng = grid
    dk = 2 * np.pi / L
    Psi_k = np.zeros((n_int, Ng, Ng, Ng), dtype=complex)

    for qi, Q in enumerate(Q_list):
        # Map Q to integer indices
        nx = int(round(Q[0] / dk)) % Ng
        ny = int(round(Q[1] / dk)) % Ng
        nz = int(round(Q[2] / dk)) % Ng
        Psi_k[:, nx, ny, nz] += A[qi]   # shape (n_int,)

    # IFFT (numpy convention: forward FFT has exp(-i k r), so IFFT gives exp(+i k r))
    Psi_r = np.fft.ifftn(Psi_k, axes=(1, 2, 3)) * (Ng**3)
    return Psi_r   # shape (n_int, Ng, Ng, Ng), complex128


# ─── Verification ─────────────────────────────────────────────────────────────

def verify_amplitude_matrix(A, label=""):
    """
    Print SVD diagnostics for the 12×n_int amplitude matrix.
    Returns the effective rank (number of singular values > 1e-6 * sigma_max).
    """
    U, s, Vh = np.linalg.svd(A, full_matrices=False)
    rank = np.sum(s > 1e-6 * s[0])
    print(f"  [{label}] SVD singular values: {s[:5]}")
    print(f"  [{label}] Effective rank: {rank}")
    # Check reality condition
    Q_list_local = None  # (used only for printing, not critical)
    return rank, s


def verify_reality_condition(A, Q_list, tol=1e-10):
    """Check that A[-Q] = conj(A[Q]) for all pairs."""
    pairs = find_pairs(Q_list)
    max_err = 0.0
    for (i, j) in pairs:
        err = np.max(np.abs(A[i] - np.conj(A[j])))
        max_err = max(max_err, err)
    ok = max_err < tol
    print(f"  Reality condition max error: {max_err:.2e}  {'✓' if ok else '✗ FAIL'}")
    return ok


def verify_psi_real(Psi_r, tol=1e-10):
    """Check that Psi_r is real-valued (imaginary part should vanish)."""
    max_imag = np.max(np.abs(Psi_r.imag))
    ok = max_imag < tol
    print(f"  max|Im(Psi)| = {max_imag:.2e}  {'✓' if ok else '✗ FAIL (not real!)'}")
    return ok


def check_bcc_shell_power(Psi_r, Q_list, grid, L):
    """Compute fraction of spectral power in BCC first shell."""
    Psi_k = np.fft.fftn(Psi_r, axes=(1, 2, 3)) / (grid**3)
    dk = 2 * np.pi / L
    total_power = np.sum(np.abs(Psi_k)**2)
    bcc_power = 0.0
    for Q in Q_list:
        nx = int(round(Q[0]/dk)) % grid
        ny = int(round(Q[1]/dk)) % grid
        nz = int(round(Q[2]/dk)) % grid
        bcc_power += np.sum(np.abs(Psi_k[:, nx, ny, nz])**2)
    frac = bcc_power / total_power if total_power > 0 else 0.0
    print(f"  BCC shell spectral power fraction: {frac:.4f}")
    return frac


# ─── Main ─────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--grid',      type=int,   default=64)
    p.add_argument('--L',         type=float, default=16.0)
    p.add_argument('--n-int',     type=int,   default=3,
                   help='Number of internal (order-parameter) components')
    p.add_argument('--amplitude', type=float, default=0.25,
                   help='RMS amplitude A of BCC modes (≈ |n|^(1/2) in TECT units)')
    p.add_argument('--mode',      type=str,   default='D',
                   choices=['A', 'B', 'C', 'D', 'all'],
                   help='D = real-plane (Gr_R, physically correct per-family rank-2)')
    p.add_argument('--n-seeds',   type=int,   default=4,
                   help='Number of random seeds for mode C')
    p.add_argument('--out-dir',   type=str,   default='.',
                   help='Output directory for .npy files')
    p.add_argument('--seed',      type=int,   default=42,
                   help='Base random seed')
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    Q_list, fam_list, q0 = bcc_first_shell(args.L, args.grid)
    print(f"BCC first shell: {len(Q_list)} vectors at |Q| = {q0:.6f}")
    print(f"Families: {dict(zip(*np.unique(fam_list, return_counts=True)))}")
    print(f"Grid: {args.grid}^3,  L={args.L},  n_int={args.n_int},  A={args.amplitude}")
    print()

    manifest_path = os.path.join(args.out_dir, 'rank2_seed_manifest.txt')
    manifest_lines = [
        "rank2_seed_manifest.txt",
        f"grid={args.grid}, L={args.L}, n_int={args.n_int}, amplitude={args.amplitude}",
        "="*70,
    ]

    def save_seed(Psi_r, A, mode_tag, seed_idx):
        fname = f"Psi_rank2_{mode_tag}_seed{seed_idx}.npy"
        fpath = os.path.join(args.out_dir, fname)
        # Save as real array (imaginary part should be ~machine-eps)
        np.save(fpath, Psi_r.real)
        print(f"  Saved: {fpath}  (shape {Psi_r.shape}, max|Ψ|={np.max(np.abs(Psi_r)):.4f})")
        rank, s = verify_amplitude_matrix(A, label=mode_tag)
        real_ok = verify_psi_real(Psi_r)
        bcc_ok  = check_bcc_shell_power(Psi_r, Q_list, args.grid, args.L)
        reality = verify_reality_condition(A, Q_list)
        manifest_lines.append(
            f"{fname}  rank={rank}  "
            f"s=[{', '.join(f'{x:.3e}' for x in s[:4])}]  "
            f"max|Im|={np.max(np.abs(Psi_r.imag)):.1e}  "
            f"BCC_frac={bcc_ok:.4f}"
        )
        print()
        return rank

    rng_base = np.random.default_rng(args.seed)

    # ── Mode A: family-split ──────────────────────────────────────────────────
    if args.mode in ('A', 'all'):
        print("=== Mode A: Family-Split (3 families → 2D internal subspace) ===")
        for k in range(4):
            rng = np.random.default_rng(args.seed + k * 1000)
            A = amp_family_split(Q_list, fam_list, args.n_int, args.amplitude, rng)
            Psi_r = build_psi(A, Q_list, args.grid, args.L, args.n_int)
            save_seed(Psi_r, A, 'A', k)

    # ── Mode B: chiral Z3 ─────────────────────────────────────────────────────
    if args.mode in ('B', 'all'):
        print("=== Mode B: Chiral Z3-phase (triplet-locked) ===")
        for k, phi in enumerate([np.pi/6, np.pi/4, np.pi/3, np.pi/2]):
            rng = np.random.default_rng(args.seed + k * 2000)
            A = amp_chiral(Q_list, fam_list, args.n_int, args.amplitude, rng, phi=phi)
            Psi_r = build_psi(A, Q_list, args.grid, args.L, args.n_int)
            save_seed(Psi_r, A, f'B_phi{int(phi*180/np.pi):03d}', k)

    # ── Mode C: random SVD-projected ─────────────────────────────────────────
    if args.mode in ('C', 'all'):
        print(f"=== Mode C: Random SVD-projected (rank-2, {args.n_seeds} seeds) ===")
        for k in range(args.n_seeds):
            rng = np.random.default_rng(args.seed + k * 3000 + 7)
            A = amp_random_svd(Q_list, args.n_int, args.amplitude, rng, rank=2)
            Psi_r = build_psi(A, Q_list, args.grid, args.L, args.n_int)
            save_seed(Psi_r, A, 'C', k)

    # ── Mode D: real Grassmannian (physically correct) ────────────────────────
    if args.mode in ('D', 'all'):
        print(f"=== Mode D: Real Gr_R(2,n_int) — per-family rank-2 ({args.n_seeds} seeds) ===")
        print("    [Prop 5.3 Step 1: reality condition forces c_1=0, real 2-plane]")
        for k in range(args.n_seeds):
            rng = np.random.default_rng(args.seed + k * 4000 + 13)
            A = amp_real_plane(Q_list, fam_list, args.n_int, args.amplitude, rng)
            Psi_r = build_psi(A, Q_list, args.grid, args.L, args.n_int)
            save_seed(Psi_r, A, 'D', k)

    # Write manifest
    with open(manifest_path, 'w') as f:
        f.write('\n'.join(manifest_lines) + '\n')
    print(f"Manifest written: {manifest_path}")


if __name__ == '__main__':
    main()
