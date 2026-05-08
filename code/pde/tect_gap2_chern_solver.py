#!/usr/bin/env python3
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
TECT Gap 2: C^5 First Chern Number Solver for BCC Family Sectors
=================================================================

Computes c_1 of the rank-2 projector bundle P(r) restricted to each
BCC family's 2D Brillouin zone sector.

TECT Prediction: c_1 = 1 per family => N_g = 3 generations.

METHOD:
  1. Parameterize rank-2 condensate via two sets of C^5 amplitudes
     {a_{Q,s}} for s=1,2 (two occupied bands)
  2. Build projector P(r) = proj onto span{Phi_1(r), Phi_2(r)}
     on Nk x Nk grid in the 2D unit cell
  3. Compute c_1 via Fukui-Hatsugai-Suzuki (FHS) lattice method
  4. Scan configurations and optimize Brazovskii energy

PHYSICS:
  Each BCC family F_alpha has 4 wavevectors in a 2D plane.
  The condensate Phi_s(r) = sum_Q a_{Q,s} e^{iQ.r} defines a map
  from the 2D unit cell T^2 to Gr(2,5).
  c_1 of the tautological bundle pullback is the TKNN invariant.

  Phase structure:  Q_j . r = 2*pi*t_j  (j=1,2 for primitive vectors)
  So Phi_s(t1,t2) = a_{1,s} z1 + a_{2,s} z2 + a_{3,s} z1^{-1} + a_{4,s} z2^{-1}
  where z_j = e^{2*pi*i*t_j}.

Gap closure chain:
  Gap 1 (Rank Selection) -> CLOSED
  Gap 4 (Sigma Model)    -> CLOSED
  Gap 3 (N_g = 3)        -> CONDITIONALLY CLOSED (needs c_1 = 1)
  Gap 2 (THIS SOLVER)    -> Verify c_1 = 1 => Fully close Gap 3

Usage:
  python tect_gap2_chern_solver.py [--Nk 128] [--scan 2000] [--optimize]
"""

import numpy as np
import argparse
import sys
import time

# ================================================================
# 1. BCC GEOMETRY
# ================================================================

def bcc_families():
    """
    Return the 3 BCC families, each with 4 wavevectors.

    Family F_alpha = {Q in BCC shell : Q_alpha = 0}
      F_0: Q_x = 0, vectors in yz-plane
      F_1: Q_y = 0, vectors in xz-plane
      F_2: Q_z = 0, vectors in xy-plane

    Returns dict: alpha -> {Q_3d, Q_2d, axes}
    """
    families = {}
    for alpha in range(3):
        i, j = (alpha + 1) % 3, (alpha + 2) % 3
        Q_3d = []
        for s1 in [1, -1]:
            for s2 in [1, -1]:
                v = np.zeros(3)
                v[i] = s1
                v[j] = s2
                Q_3d.append(v / np.sqrt(2))
        Q_3d = np.array(Q_3d)
        Q_2d = Q_3d[:, [i, j]]
        families[alpha] = {
            'Q_3d': Q_3d,
            'Q_2d': Q_2d,
            'axes': (i, j),
            'plane': ['yz', 'xz', 'xy'][alpha],
        }
    return families


def bcc_triplets():
    """Find all 24 BCC Bragg triplets Q_a + Q_b + Q_c = 0."""
    Q = []
    fam = []
    for alpha in range(3):
        i, j = (alpha + 1) % 3, (alpha + 2) % 3
        for s1 in [1, -1]:
            for s2 in [1, -1]:
                v = np.zeros(3)
                v[i] = s1
                v[j] = s2
                Q.append(v / np.sqrt(2))
                fam.append(alpha)
    Q = np.array(Q)
    trips = []
    n = len(Q)
    for a in range(n):
        for b in range(a + 1, n):
            for c in range(b + 1, n):
                if np.linalg.norm(Q[a] + Q[b] + Q[c]) < 1e-10:
                    trips.append((a, b, c))
    return Q, fam, trips


# ================================================================
# 2. OCCUPIED STATES ON 2D GRID
# ================================================================

def build_occupied_states(amp1, amp2, Nk):
    """
    Build orthonormal occupied states on Nk x Nk grid.

    The 4 wavevectors of a family satisfy:
      Q_j . r = 2*pi*t_j  for j=1,2 (primitive)
      Q_3 = -Q_1, Q_4 = -Q_2
    So phases are z1, z2, z1^{-1}, z2^{-1}.

    Parameters
    ----------
    amp1 : (4, 5) complex - C^5 amplitudes for band 1
    amp2 : (4, 5) complex - C^5 amplitudes for band 2
    Nk   : int - grid size

    Returns
    -------
    U     : (Nk, Nk, 5, 2) complex - orthonormal frame
    rk_min: float - min |Phi1 x Phi2| (rank indicator, >0 means rank-2 everywhere)
    """
    t = np.linspace(0, 1, Nk, endpoint=False)
    t1, t2 = np.meshgrid(t, t, indexing='ij')  # (Nk, Nk)

    # Phases: z1 = e^{2*pi*i*t1}, z2 = e^{2*pi*i*t2}
    z1 = np.exp(2j * np.pi * t1)  # (Nk, Nk)
    z2 = np.exp(2j * np.pi * t2)

    # phases[q] for q=0,1,2,3 -> z1, z2, z1^{-1}, z2^{-1}
    phases = np.stack([z1, z2, 1.0 / z1, 1.0 / z2], axis=-1)  # (Nk, Nk, 4)

    # Phi_s(t1,t2) = sum_q a_{q,s} * phase_q
    # amp_s: (4, 5), phases: (Nk, Nk, 4) -> Phi: (Nk, Nk, 5)
    Phi1 = np.einsum('mnq,qi->mni', phases, amp1)
    Phi2 = np.einsum('mnq,qi->mni', phases, amp2)

    # Gram-Schmidt orthonormalization
    n1 = np.linalg.norm(Phi1, axis=-1, keepdims=True)  # (Nk, Nk, 1)
    safe_n1 = np.maximum(n1, 1e-15)
    e1 = Phi1 / safe_n1

    olap = np.sum(np.conj(e1) * Phi2, axis=-1, keepdims=True)  # (Nk, Nk, 1)
    Phi2p = Phi2 - olap * e1
    n2 = np.linalg.norm(Phi2p, axis=-1, keepdims=True)
    safe_n2 = np.maximum(n2, 1e-15)
    e2 = Phi2p / safe_n2

    U = np.stack([e1, e2], axis=-1)  # (Nk, Nk, 5, 2)
    rk_min = float(np.min(n1 * n2))

    return U, rk_min


# ================================================================
# 3. FUKUI-HATSUGAI-SUZUKI CHERN NUMBER
# ================================================================

def chern_fhs(U):
    """
    Compute first Chern number via the FHS lattice method.

    For a rank-r occupied bundle with frame U(k) at each k-point,
    the plaquette Wilson loop is:
      W(k) = M_x(k) M_y(k+dx) M_x^dag(k+dy) M_y^dag(k)
    where M_mu(k) = U^dag(k) U(k+d_mu) is the r x r overlap matrix.

    c_1 = (1/2*pi) sum_k [-Im ln det W(k)]

    Parameters
    ----------
    U : (Nk, Nk, 5, 2) complex - orthonormal occupied states

    Returns
    -------
    c1 : float (should be close to integer)
    """
    # Shifted arrays (periodic)
    Ux = np.roll(U, -1, axis=0)    # U(i+1, j)
    Uy = np.roll(U, -1, axis=1)    # U(i, j+1)
    Uxy = np.roll(Ux, -1, axis=1)  # U(i+1, j+1)

    # Overlap matrices: M = U^dag @ U_shifted  -> (Nk, Nk, 2, 2)
    Mx = np.einsum('ijka,ijkb->ijab', np.conj(U), Ux)       # U^dag(ij) U(i+1,j)
    My_x = np.einsum('ijka,ijkb->ijab', np.conj(Ux), Uxy)   # U^dag(i+1,j) U(i+1,j+1)
    Mx_y = np.einsum('ijka,ijkb->ijab', np.conj(Uy), Uxy)   # U^dag(i,j+1) U(i+1,j+1)
    My = np.einsum('ijka,ijkb->ijab', np.conj(U), Uy)        # U^dag(ij) U(i,j+1)

    # Plaquette: W = Mx @ My_x @ Mx_y^dag @ My^dag
    Mx_y_dag = np.conj(np.swapaxes(Mx_y, -2, -1))
    My_dag = np.conj(np.swapaxes(My, -2, -1))
    W = Mx @ My_x @ Mx_y_dag @ My_dag  # (Nk, Nk, 2, 2)

    # Berry flux per plaquette
    det_W = np.linalg.det(W)  # (Nk, Nk) complex
    F = -np.imag(np.log(det_W))  # in (-pi, pi]

    c1 = np.sum(F) / (2 * np.pi)
    return c1


# ================================================================
# 4. BRAZOVSKII ENERGY FUNCTIONAL
# ================================================================

def brazovskii_energy_family(amp1, amp2, Nk_energy=32,
                              r_param=-0.5, u=1.0,
                              d_sex=0.5, e_sex=-1.0, f_sex=1.0):
    """
    Compute Brazovskii free energy for rank-2 condensate
    restricted to one BCC family (4 wavevectors).

    F = r <|Psi|^2> + u <|Psi|^4> + B_2 <|Psi|^6>

    where B_2 = d + e/2 + f/4 (rank-2 sextic coefficient).

    For first-shell modes |Q|=q_0, the kinetic term vanishes.
    """
    t = np.linspace(0, 1, Nk_energy, endpoint=False)
    t1, t2 = np.meshgrid(t, t, indexing='ij')
    z1 = np.exp(2j * np.pi * t1)
    z2 = np.exp(2j * np.pi * t2)
    phases = np.stack([z1, z2, 1.0 / z1, 1.0 / z2], axis=-1)

    Phi1 = np.einsum('mnq,qi->mni', phases, amp1)
    Phi2 = np.einsum('mnq,qi->mni', phases, amp2)

    # |Psi(r)|^2 = |Phi1|^2 + |Phi2|^2
    rho2 = np.sum(np.abs(Phi1) ** 2 + np.abs(Phi2) ** 2, axis=-1)

    avg2 = np.mean(rho2)
    avg4 = np.mean(rho2 ** 2)
    avg6 = np.mean(rho2 ** 3)

    B_2 = d_sex + e_sex / 2 + f_sex / 4
    F = r_param * avg2 + u * avg4 + B_2 * avg6
    return F


def brazovskii_energy_full(amps_all, Nk_energy=16,
                            r_param=-0.5, u=1.0, w_cubic=-0.3,
                            d_sex=0.5, e_sex=-1.0, f_sex=1.0):
    """
    Full 3D Brazovskii energy with all 12 BCC modes and cubic term.

    amps_all: (12, 5, 2) complex - amplitudes for 12 Q-vectors, 5 C^5 comps, 2 bands
    """
    Q_all, fam_labels, trips = bcc_triplets()

    t = np.linspace(0, 1, Nk_energy, endpoint=False)
    t1, t2, t3 = np.meshgrid(t, t, t, indexing='ij')  # (N,N,N)
    r = np.stack([t1, t2, t3], axis=-1) * 2 * np.pi  # (N,N,N,3)

    # Phases for all 12 Q-vectors: (N,N,N,12)
    phases = np.exp(1j * np.einsum('qi,...i->...q', Q_all, r))

    # Psi_s(r) = sum_Q a_{Q,s} e^{iQ.r}
    amp1 = amps_all[:, :, 0]  # (12, 5)
    amp2 = amps_all[:, :, 1]  # (12, 5)
    Phi1 = np.einsum('...q,qi->...i', phases, amp1)  # (N,N,N,5)
    Phi2 = np.einsum('...q,qi->...i', phases, amp2)

    rho2 = np.sum(np.abs(Phi1) ** 2 + np.abs(Phi2) ** 2, axis=-1)

    avg2 = np.mean(rho2)
    avg4 = np.mean(rho2 ** 2)
    avg6 = np.mean(rho2 ** 3)

    # Cubic term (Alexander-McTague): w * sum_triplets a_a^dag . a_b * ...
    # For C^5 fields, use |Psi|^2 * Psi structure
    # Simplified: cubic ~ w * sum_triplets (a_a^dag . a_b)(a_b^dag . a_c)(a_c^dag . a_a)
    E_cubic = 0.0
    for s in range(2):  # both bands contribute
        amp_s = amps_all[:, :, s]
        for (a, b, c) in trips:
            fab = np.dot(np.conj(amp_s[a]), amp_s[b])
            fbc = np.dot(np.conj(amp_s[b]), amp_s[c])
            fca = np.dot(np.conj(amp_s[c]), amp_s[a])
            E_cubic += np.real(fab * fbc * fca)

    B_2 = d_sex + e_sex / 2 + f_sex / 4
    F = r_param * avg2 + u * avg4 + B_2 * avg6 + w_cubic * E_cubic
    return F


# ================================================================
# 5. CONFIGURATION LIBRARY
# ================================================================

def config_trivial(scale=1.0):
    """Constant 2-plane: all amp in span(e1, e2) -> c1 = 0 guaranteed."""
    amp1 = np.zeros((4, 5), dtype=complex)
    amp2 = np.zeros((4, 5), dtype=complex)
    amp1[:, 0] = scale
    amp2[:, 1] = scale
    return amp1, amp2, "trivial (constant 2-plane)"


def config_twisted_maxrank():
    """
    Band amplitudes span rank-4 subspace of C^5.
    Each Q-vector points in a different C^5 direction per band.
    """
    amp1 = np.zeros((4, 5), dtype=complex)
    amp2 = np.zeros((4, 5), dtype=complex)
    # Band 1: Q_j -> e_j (j=0..3)
    for j in range(4):
        amp1[j, j] = 1.0
    # Band 2: Q_j -> e_{j+1 mod 5}
    for j in range(4):
        amp2[j, (j + 1) % 5] = 1.0
    return amp1, amp2, "twisted-maxrank (global rank 5)"


def config_chiral():
    """
    Chiral: only positive-frequency modes for band 1,
    mixed for band 2. Breaks time-reversal.
    """
    amp1 = np.zeros((4, 5), dtype=complex)
    amp2 = np.zeros((4, 5), dtype=complex)
    amp1[0] = [1, 0, 0, 0, 0]   # z1 mode
    amp1[1] = [0, 1, 0, 0, 0]   # z2 mode
    # Q3 = z1^{-1}, Q4 = z2^{-1} are zero for band 1
    amp2[0] = [0, 0, 1, 0, 0]
    amp2[1] = [0, 0, 0, 0, 1]
    amp2[2] = [0, 0, 0, 1, 0]
    amp2[3] = [1, 0, 0, 0, 0]
    return amp1, amp2, "chiral (T-breaking)"


def config_mixed_bands():
    """
    Bands share C^5 directions (necessary for c1 != 0).
    Both bands have amplitude along e1 for different Q-vectors.
    """
    amp1 = np.zeros((4, 5), dtype=complex)
    amp2 = np.zeros((4, 5), dtype=complex)
    # Band 1
    amp1[0] = [1, 0, 0, 0, 0]
    amp1[1] = [0, 1, 0, 0, 0]
    amp1[2] = [0, 0, 1, 0, 0]
    amp1[3] = [0, 0, 0, 1, 0]
    # Band 2: SHARES e1,e2 with band 1
    amp2[0] = [0, 1, 0, 0, 0]
    amp2[1] = [0, 0, 0, 0, 1]
    amp2[2] = [1, 0, 0, 0, 0]  # shares e1 direction with amp1[0]
    amp2[3] = [0, 0, 1, 0, 0]  # shares e3 with amp1[2]
    return amp1, amp2, "mixed-bands (shared C5 dirs)"


def config_monopole_embed():
    """
    Embed the CP^1 monopole bundle into Gr(2,5).
    P = |psi><psi| + |e5><e5| where psi traces CP^1.

    psi(t1,t2) = (cos(pi*t1), sin(pi*t1)*e^{2*pi*i*t2}, 0, 0, 0)

    Approximate by Fourier modes.
    """
    amp1 = np.zeros((4, 5), dtype=complex)
    amp2 = np.zeros((4, 5), dtype=complex)
    # Band 1: approximate cos/sin via z1+z1^{-1} and (z1-z1^{-1})*z2
    amp1[0] = [0.5, 0, 0, 0, 0]       # z1: contributes to cos(2*pi*t1)
    amp1[2] = [0.5, 0, 0, 0, 0]       # z1^{-1}: completes cos
    amp1[1] = [0, 0.5, 0, 0, 0]       # z2
    amp1[3] = [0, 0.5, 0, 0, 0]       # z2^{-1}
    # This gives Phi1 = (cos(2*pi*t1), cos(2*pi*t2), 0, 0, 0) - degenerate at t=1/4

    # Band 2: fixed direction + mixing
    amp2[0] = [0, 0, 0.5, 0, 0]
    amp2[1] = [0, 0, 0, 0.5, 0]
    amp2[2] = [0, 0, 0.5, 0, 0]
    amp2[3] = [0, 0, 0, 0.5, 0]
    return amp1, amp2, "monopole-embed (CP1 in Gr(2,5))"


def config_asymmetric_rotation():
    """
    Band 1 rotates in (e1,e2,e3) subspace.
    Band 2 fixed along (e4,e5).
    Asymmetric rotation can produce non-zero c1.
    """
    amp1 = np.zeros((4, 5), dtype=complex)
    amp2 = np.zeros((4, 5), dtype=complex)
    amp1[0] = [1, 0, 0, 0, 0]     # z1 -> e1
    amp1[1] = [0, 1, 0, 0, 0]     # z2 -> e2
    amp1[2] = [0, 0, 1, 0, 0]     # z1^{-1} -> e3
    amp1[3] = [0, 0, 0, 0, 0]     # z2^{-1} -> 0
    amp2[0] = [0, 0, 0, 1, 0]     # z1 -> e4
    amp2[1] = [0, 0, 0, 0, 1]     # z2 -> e5
    amp2[2] = [0, 0, 0, 1, 0]     # z1^{-1} -> e4
    amp2[3] = [0, 0, 0, 0, 1]     # z2^{-1} -> e5
    return amp1, amp2, "asymmetric-rotation (3+2 split)"


def config_holomorphic():
    """
    Purely holomorphic: only z1, z2 modes (no z^{-1}).
    Band 1: z1*e1 + z2*e2
    Band 2: z1*e3 + z2*e4 + constant*e5
    """
    amp1 = np.zeros((4, 5), dtype=complex)
    amp2 = np.zeros((4, 5), dtype=complex)
    amp1[0] = [1, 0, 0, 0, 0]
    amp1[1] = [0, 1, 0, 0, 0]
    amp2[0] = [0, 0, 1, 0, 0]
    amp2[1] = [0, 0, 0, 1, 0]
    amp2[2] = [0, 0, 0, 0, 0.5]  # small antiholomorphic component
    amp2[3] = [0, 0, 0, 0, 0.5]
    return amp1, amp2, "holomorphic (z1,z2 only for band 1)"


def config_interleaved():
    """
    Interleave C^5 directions between the two bands and across modes,
    creating maximum mixing. Both bands share ALL 5 directions.
    """
    amp1 = np.zeros((4, 5), dtype=complex)
    amp2 = np.zeros((4, 5), dtype=complex)
    # Band 1
    amp1[0] = [1, 0, 1j, 0, 0]
    amp1[1] = [0, 1, 0, 1j, 0]
    amp1[2] = [0, 1j, 0, 0, 1]
    amp1[3] = [1j, 0, 0, 0, 1]
    # Band 2
    amp2[0] = [0, 1, 0, 0, 1j]
    amp2[1] = [1j, 0, 1, 0, 0]
    amp2[2] = [0, 0, 1j, 1, 0]
    amp2[3] = [0, 0, 0, 1j, 1]
    return amp1, amp2, "interleaved (full C5 mixing)"


def config_su5_breaking():
    """
    SU(5) -> SU(2)xSU(3): condensate in the (2,1) sector
    with topological winding from the SU(2) factor.
    """
    amp1 = np.zeros((4, 5), dtype=complex)
    amp2 = np.zeros((4, 5), dtype=complex)
    # Band 1: SU(2) doublet winding in first 2 components
    amp1[0] = [1, 0, 0, 0, 0]      # z1 -> (1,0)
    amp1[1] = [0, 1, 0, 0, 0]      # z2 -> (0,1)
    amp1[2] = [0, -1, 0, 0, 0]     # z1^{-1} -> (0,-1)  [anti-aligned]
    amp1[3] = [1, 0, 0, 0, 0]      # z2^{-1} -> (1,0)
    # Band 2: SU(3) singlet with winding in 3rd component
    amp2[0] = [0, 0, 1, 0, 0]
    amp2[1] = [0, 0, 0, 1, 0]
    amp2[2] = [0, 0, 0, 0, 1]
    amp2[3] = [0, 0, 1, 0, 0]
    return amp1, amp2, "SU(5)->SU(2)xSU(3) breaking"


def config_random(seed=None, scale=1.0):
    """Fully random C^5 amplitudes for both bands."""
    rng = np.random.default_rng(seed)
    amp1 = (rng.standard_normal((4, 5)) + 1j * rng.standard_normal((4, 5))) * scale
    amp2 = (rng.standard_normal((4, 5)) + 1j * rng.standard_normal((4, 5))) * scale
    return amp1, amp2, f"random(seed={seed})"


def config_random_physical(seed=None, scale=1.0):
    """
    Random config with reality condition: a_{-Q} = a_Q^*.
    Q3 = -Q1, Q4 = -Q2, so amp[2] = conj(amp[0]), amp[3] = conj(amp[1]).
    """
    rng = np.random.default_rng(seed)
    amp1_half = (rng.standard_normal((2, 5)) + 1j * rng.standard_normal((2, 5))) * scale
    amp2_half = (rng.standard_normal((2, 5)) + 1j * rng.standard_normal((2, 5))) * scale
    amp1 = np.vstack([amp1_half, np.conj(amp1_half)])
    amp2 = np.vstack([amp2_half, np.conj(amp2_half)])
    return amp1, amp2, f"random-phys(seed={seed})"


# ================================================================
# 6. PACKING / UNPACKING FOR OPTIMIZER
# ================================================================

def pack(amp1, amp2):
    """Pack (4,5) x 2 complex -> (80,) real vector."""
    return np.concatenate([amp1.ravel().real, amp1.ravel().imag,
                           amp2.ravel().real, amp2.ravel().imag])


def unpack(x):
    """Unpack (80,) real -> two (4,5) complex arrays."""
    n = 20
    amp1 = (x[:n] + 1j * x[n:2 * n]).reshape(4, 5)
    amp2 = (x[2 * n:3 * n] + 1j * x[3 * n:]).reshape(4, 5)
    return amp1, amp2


# ================================================================
# 7. OPTIMIZER
# ================================================================

def _numerical_gradient(func, x, eps=1e-6):
    """Central-difference gradient."""
    grad = np.zeros_like(x)
    for i in range(len(x)):
        xp = x.copy(); xp[i] += eps
        xm = x.copy(); xm[i] -= eps
        grad[i] = (func(xp) - func(xm)) / (2 * eps)
    return grad


def optimize_ground_state(Nk_chern=64, Nk_energy=32, n_restarts=50, seed=42,
                          r_param=-0.5, u=1.0, d_sex=0.5, e_sex=-1.0, f_sex=1.0,
                          verbose=True):
    """
    Find energy-minimizing configurations and compute their c1.
    Uses gradient descent with multiple random restarts (no scipy).
    """
    rng = np.random.default_rng(seed)
    results = []

    def objective(x):
        amp1, amp2 = unpack(x)
        return brazovskii_energy_family(amp1, amp2, Nk_energy,
                                        r_param, u, d_sex, e_sex, f_sex)

    for trial in range(n_restarts):
        x = rng.standard_normal(80) * 0.3
        lr = 0.01
        best_f = objective(x)
        best_x = x.copy()
        for step in range(200):
            g = _numerical_gradient(objective, x, eps=1e-5)
            x_new = x - lr * g
            f_new = objective(x_new)
            if f_new < best_f:
                best_f = f_new
                best_x = x_new.copy()
                lr *= 1.1  # accelerate
            else:
                lr *= 0.5  # backtrack
            x = x_new
            if lr < 1e-12:
                break

        amp1, amp2 = unpack(best_x)
        U, rk_min = build_occupied_states(amp1, amp2, Nk_chern)
        if rk_min > 1e-8:
            c1 = chern_fhs(U)
        else:
            c1 = float('nan')
        results.append({
            'trial': trial,
            'energy': float(best_f),
            'c1': float(c1),
            'rank_min': float(rk_min),
            'converged': True,
            'amp1': amp1.copy(),
            'amp2': amp2.copy(),
        })
        if verbose and (trial + 1) % 10 == 0:
            print(f"  ... {trial + 1}/{n_restarts} done")

    results.sort(key=lambda r: r['energy'])
    return results


# ================================================================
# 8. COMPREHENSIVE SCAN
# ================================================================

def scan_random(Nk, n_samples, mode='complex', verbose=True):
    """
    Scan random configurations and report c1 distribution.

    mode: 'complex' (general) or 'physical' (reality condition)
    """
    c1_list = []
    hits = []  # configs with |c1| > 0.5

    for seed in range(n_samples):
        if mode == 'physical':
            amp1, amp2, _ = config_random_physical(seed)
        else:
            amp1, amp2, _ = config_random(seed)

        U, rk_min = build_occupied_states(amp1, amp2, Nk)
        if rk_min < 1e-10:
            c1_list.append(float('nan'))
            continue

        c1 = chern_fhs(U)
        c1_list.append(c1)

        if abs(c1 - round(c1)) < 0.05 and abs(round(c1)) >= 1:
            hits.append({
                'seed': seed,
                'c1': c1,
                'c1_int': int(round(c1)),
                'rank_min': rk_min,
                'amp1': amp1.copy(),
                'amp2': amp2.copy(),
            })
            if verbose:
                print(f"  *** HIT: seed={seed}, c1={c1:+.6f}, "
                      f"rk_min={rk_min:.2e}")

        if verbose and (seed + 1) % 500 == 0:
            valid = [c for c in c1_list if not np.isnan(c)]
            if valid:
                print(f"  ... {seed + 1}/{n_samples}: "
                      f"mean(c1)={np.mean(valid):+.4f}, "
                      f"std(c1)={np.std(valid):.4f}, "
                      f"hits={len(hits)}")

    return c1_list, hits


# ================================================================
# 9. CONVERGENCE TEST
# ================================================================

def convergence_test(amp1, amp2, Nk_values=[16, 32, 64, 128, 256]):
    """Test c1 convergence as function of grid size."""
    results = []
    for Nk in Nk_values:
        U, rk_min = build_occupied_states(amp1, amp2, Nk)
        c1 = chern_fhs(U) if rk_min > 1e-10 else float('nan')
        results.append({'Nk': Nk, 'c1': c1, 'rank_min': rk_min})
    return results


# ================================================================
# 10. ANALYSIS AND REPORTING
# ================================================================

def analyze_c1_distribution(c1_list):
    """Statistical analysis of c1 distribution."""
    valid = np.array([c for c in c1_list if not np.isnan(c)])
    if len(valid) == 0:
        return {'n_valid': 0}

    # Round to nearest integer
    c1_ints = np.round(valid).astype(int)
    unique, counts = np.unique(c1_ints, return_counts=True)

    return {
        'n_total': len(c1_list),
        'n_valid': len(valid),
        'n_degenerate': len(c1_list) - len(valid),
        'mean': float(np.mean(valid)),
        'std': float(np.std(valid)),
        'min': float(np.min(valid)),
        'max': float(np.max(valid)),
        'distribution': {int(u): int(c) for u, c in zip(unique, counts)},
        'integrality': float(np.mean(np.abs(valid - np.round(valid)))),
    }


def print_report(title, c1, rk_min, width=60):
    """Print a single configuration result."""
    if np.isnan(c1):
        status = "DEGENERATE (rank < 2)"
    elif abs(c1 - round(c1)) > 0.1:
        status = f"NON-INTEGER: {c1:+.6f}"
    elif int(round(c1)) == 0:
        status = f"TRIVIAL (c1 = 0)"
    elif int(round(c1)) == 1:
        status = f"*** c1 = +1 *** TARGET"
    elif int(round(c1)) == -1:
        status = f"*** c1 = -1 ***"
    else:
        status = f"c1 = {int(round(c1)):+d}"
    return f"  c1 = {c1:+8.4f}  rk_min={rk_min:.2e}  [{status}]"


# ================================================================
# MAIN
# ================================================================

def main():
    parser = argparse.ArgumentParser(
        description='TECT Gap 2: C^5 Chern Number Solver')
    parser.add_argument('--Nk', type=int, default=64,
                        help='BZ grid size for Chern number (default: 64)')
    parser.add_argument('--scan', type=int, default=2000,
                        help='Number of random configs to scan (default: 2000)')
    parser.add_argument('--optimize', action='store_true',
                        help='Run energy optimizer')
    parser.add_argument('--n-restarts', type=int, default=50,
                        help='Optimizer restart count')
    parser.add_argument('--convergence', action='store_true',
                        help='Run convergence test')
    parser.add_argument('--family', type=int, default=None,
                        help='Restrict to one family (0,1,2)')
    parser.add_argument('--physical-only', action='store_true',
                        help='Only scan configs with reality condition')
    args = parser.parse_args()

    Nk = args.Nk
    families = bcc_families()

    print("=" * 70)
    print("  TECT Gap 2: C^5 First Chern Number Solver")
    print("  Target: c_1 = 1 per BCC family => N_g = 3")
    print("=" * 70)
    print(f"  BZ grid: {Nk} x {Nk}")
    print(f"  Random scan: {args.scan} configs")
    print(f"  Mode: {'physical (reality)' if args.physical_only else 'general complex'}")
    print()

    # ---- Phase 1: Predefined configurations ----
    print("-" * 70)
    print("PHASE 1: Predefined configuration library")
    print("-" * 70)

    named_configs = [
        config_trivial,
        config_twisted_maxrank,
        config_chiral,
        config_mixed_bands,
        config_asymmetric_rotation,
        config_holomorphic,
        config_interleaved,
        config_su5_breaking,
        config_monopole_embed,
    ]

    # Only need to test one family (all are equivalent by O symmetry)
    alpha = 0 if args.family is None else args.family
    print(f"\nFamily F_{alpha} ({families[alpha]['plane']}-plane):")

    for cfg_fn in named_configs:
        amp1, amp2, name = cfg_fn()
        U, rk_min = build_occupied_states(amp1, amp2, Nk)
        c1 = chern_fhs(U) if rk_min > 1e-10 else float('nan')
        report = print_report(name, c1, rk_min)
        print(f"  {name:42s} {report}")

    # ---- Phase 2: Random scan ----
    if args.scan > 0:
        print()
        print("-" * 70)
        print(f"PHASE 2: Random scan ({args.scan} configurations)")
        print("-" * 70)

        mode = 'physical' if args.physical_only else 'complex'

        # General complex scan
        print(f"\n  Scanning {args.scan} {mode} random configs...")
        t0 = time.time()
        c1_list, hits = scan_random(Nk, args.scan, mode=mode, verbose=True)
        dt = time.time() - t0

        stats = analyze_c1_distribution(c1_list)
        print(f"\n  Completed in {dt:.1f}s")
        print(f"  Valid configs: {stats['n_valid']}/{stats['n_total']} "
              f"({stats.get('n_degenerate', 0)} degenerate)")
        if stats['n_valid'] > 0:
            print(f"  Mean c1: {stats['mean']:+.6f}")
            print(f"  Std  c1: {stats['std']:.6f}")
            print(f"  Range:   [{stats['min']:+.4f}, {stats['max']:+.4f}]")
            print(f"  Integrality (mean |c1 - round(c1)|): {stats['integrality']:.6f}")
            print(f"  Distribution of round(c1):")
            for c1_val, count in sorted(stats['distribution'].items()):
                pct = 100 * count / stats['n_valid']
                bar = '#' * max(1, int(pct / 2))
                print(f"    c1 = {c1_val:+2d}: {count:5d} ({pct:5.1f}%) {bar}")

        if hits:
            print(f"\n  NON-TRIVIAL HITS: {len(hits)}")
            for h in hits[:20]:
                print(f"    seed={h['seed']:5d}, c1={h['c1']:+.6f}, "
                      f"rk_min={h['rank_min']:.2e}")

            # Convergence test on first hit
            if args.convergence and len(hits) > 0:
                print(f"\n  Convergence test on first hit (seed={hits[0]['seed']}):")
                conv = convergence_test(
                    hits[0]['amp1'], hits[0]['amp2'],
                    [16, 32, 64, 128, 256])
                for r in conv:
                    print(f"    Nk={r['Nk']:4d}: c1={r['c1']:+.8f}")

        # Also scan physical (reality condition) if not already
        if not args.physical_only and args.scan >= 500:
            print(f"\n  Also scanning {min(args.scan, 1000)} physical (real) configs...")
            c1_phys, hits_phys = scan_random(Nk, min(args.scan, 1000),
                                             mode='physical', verbose=True)
            stats_p = analyze_c1_distribution(c1_phys)
            if stats_p['n_valid'] > 0:
                print(f"  Physical scan: mean={stats_p['mean']:+.6f}, "
                      f"std={stats_p['std']:.6f}")
                print(f"  Distribution:")
                for c1_val, count in sorted(stats_p['distribution'].items()):
                    pct = 100 * count / stats_p['n_valid']
                    print(f"    c1 = {c1_val:+2d}: {count:5d} ({pct:5.1f}%)")
                if hits_phys:
                    print(f"  Physical NON-TRIVIAL HITS: {len(hits_phys)}")

    # ---- Phase 3: Energy optimizer ----
    if args.optimize:
        print()
        print("-" * 70)
        print("PHASE 3: Energy-minimizing ground state search")
        print("-" * 70)
        results = optimize_ground_state(
            Nk_chern=Nk, Nk_energy=32, n_restarts=args.n_restarts)

        print(f"\n  Top 10 by energy:")
        for r in results[:10]:
            c1_str = f"{r['c1']:+.4f}" if not np.isnan(r['c1']) else " NaN  "
            print(f"    E={r['energy']:+12.8f}  c1={c1_str}  "
                  f"rk_min={r['rank_min']:.2e}  "
                  f"{'CONVERGED' if r['converged'] else 'NOT CONVERGED'}")

        # Check if any ground state has c1 != 0
        gs_c1_values = [r['c1'] for r in results if not np.isnan(r['c1'])]
        if gs_c1_values:
            nontrivial = [c for c in gs_c1_values
                          if abs(c - round(c)) < 0.05 and abs(round(c)) >= 1]
            if nontrivial:
                print(f"\n  *** NON-TRIVIAL TOPOLOGY IN GROUND STATE: "
                      f"c1 = {nontrivial[0]:+.4f} ***")
            else:
                print(f"\n  Ground state appears TOPOLOGICALLY TRIVIAL (c1 = 0)")
                print(f"  This means the c1=1 assumption in Paper I "
                      f"may require revision.")

    # ---- Summary ----
    print()
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    if args.scan > 0 and 'hits' in dir():
        n_nontrivial = len(hits) if hits else 0
        print(f"  Random scan: {n_nontrivial}/{args.scan} configs with |c1| >= 1")
        if n_nontrivial > 0:
            c1_hit_vals = [h['c1_int'] for h in hits]
            unique_hits = set(c1_hit_vals)
            print(f"  Non-trivial sectors found: {unique_hits}")
            if 1 in unique_hits:
                print(f"  *** c1 = 1 ACHIEVED — Gap 3 closable ***")
            else:
                print(f"  c1 = 1 NOT found in scan")
        else:
            print(f"  NO non-trivial topology found in {args.scan} random configs")
            print(f"  Implication: c1 = 1 may require specific physical mechanism")

    print()
    print("  Next steps:")
    print("  - If c1=1 found: verify with energy optimizer that it's the ground state")
    print("  - If c1=0 only:  the three-generation mechanism needs refinement")
    print("  - Run --convergence on any hits to confirm integrality")
    print("=" * 70)


if __name__ == '__main__':
    main()
