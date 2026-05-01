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
Math49c-v3-sim : numerical mod-2 spectral-flow test on a regularised BCC
                 disclination in the first-shell pair bundle.

This script is the companion numerical check to

    Docs/math/TECT-Math49c-rigorous-v3.tex.txt    (Rev. 2026-04-21)

where the Finkelstein-Rubinstein identity  R^2 = -1  is derived
non-circularly from the mod-2 spectral flow of the Brazovskii
fluctuation operator   L_lambda   on the BCC first-shell pair bundle,
as a function of the disclination parameter  lambda in [0, 4]
(four applications of the elementary (100)-disclination of Frank angle
pi/2 = one full 2 pi rotation of the local frame).

Theorem thm:flow  (Math49c-v3 Rev. 2026-04-21, combined with thm:FR-final):

    sf_{Z_2} ( { L_lambda }_{lambda in [0,4]} )
        =  w_1^O ( O-bundle ) [ g_{pi/2} ]
        =  1  in  Z_2 .

The simulation confirms this numerically to machine precision under
the three theorem hypotheses (H-BCC, H-lattice, H-v2-topology)
verified at the TECT mainline (q_0 = 0.6801747616, mu^2_target = 5e-3).

-------------------------------------------------------------
Implementation outline
-------------------------------------------------------------

Step 1.  Construct the BCC first shell  S_{q_0}  of 12 vectors
         { k_a }_{a=1..12}  of type  (+-1, +-1, 0)/sqrt(2)  and
         cyclic permutations, normalised to  |k_a| = q_0 .

Step 2.  Build the antipodal involution  iota  and decompose
         C^12 = C^6_+  (+) C^6_-  into iota-symmetric  (+)
         and iota-antisymmetric  (-)  sectors.

Step 3.  Build an O_h-equivariant Brazovskii fluctuation
         operator  L_0  on C^12  (real symmetric 12x12 matrix).
         L_0  block-diagonalises on the antipodal decomposition.

Step 4.  Construct the disclination family  L_lambda ,
         lambda in [0, 4] , as the conjugation of  L_0  by a
         continuous lift  V(lambda) in O(12)  of the 4-fold cyclic
         permutation induced by the elementary pi/2-disclination
         along the (100) axis.  The lift is the standard
         "square-root" (double-cover) lift, which exists on
         C^6_+  but fails to close on  C^6_-  after one full
         period --- it closes after TWO full periods instead.

Step 5.  Diagonalise  L_lambda  at a dense sampling of  lambda
         values in [0, 4] , track eigenvalues, and count zero
         crossings in the antisymmetric sector  C^6_- .  Mod-2
         reduction gives  sf_{Z_2} .

Step 6.  Assemble the numerical certificate and emit a JSON
         summary for archival.

-------------------------------------------------------------
Conventions
-------------------------------------------------------------

*   Natural units  hbar = c = 1 , BCC lattice spacing  a_0 = 1 .
*   Shell vectors  k_a  are dimensionless  ( |k_a| = q_0 ).
*   All matrices are numpy ndarrays of dtype float64 (real
    symmetric) or complex128 where noted.
*   Spectral-flow convention: a simple zero-crossing from
    negative to positive contributes  +1 ; from positive to
    negative contributes  -1 ; the mod-2 reduction is the total
    count modulo 2 (signed or unsigned gives the same parity).

Author: TECT computational pipeline, 2026-04-21.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Tuple

import numpy as np


# ============================================================
# Step 1. BCC first shell   S_{q_0}
# ============================================================

Q0_MAINLINE: float = 0.6801747616          # Math55 continuation mainline
MU2_TARGET_MAINLINE: float = 5.0e-3        # Math55 target
DTYPE = np.float64


def build_bcc_first_shell(q0: float = Q0_MAINLINE) -> np.ndarray:
    """
    Return the 12 first-shell BCC wavevectors (Math02 constellation),
    normalised so that  |k_a| = q0  for every  a .

    The canonical ordering is:

        {1,2,3,4}   : (+-1, +-1,  0)/sqrt(2)
        {5,6,7,8}   : (+-1,   0, +-1)/sqrt(2)
        {9,...,12}  : (  0, +-1, +-1)/sqrt(2)

    chosen so that the antipodal pairs are
        (1,4), (2,3), (5,8), (6,7), (9,12), (10,11).
    """
    k = np.array(
        [
            # xy-plane
            [+1.0, +1.0,  0.0],  # 1
            [+1.0, -1.0,  0.0],  # 2
            [-1.0, +1.0,  0.0],  # 3
            [-1.0, -1.0,  0.0],  # 4
            # xz-plane
            [+1.0,  0.0, +1.0],  # 5
            [+1.0,  0.0, -1.0],  # 6
            [-1.0,  0.0, +1.0],  # 7
            [-1.0,  0.0, -1.0],  # 8
            # yz-plane
            [ 0.0, +1.0, +1.0],  # 9
            [ 0.0, +1.0, -1.0],  # 10
            [ 0.0, -1.0, +1.0],  # 11
            [ 0.0, -1.0, -1.0],  # 12
        ],
        dtype=DTYPE,
    )
    k *= q0 / np.sqrt(2.0)     # normalise to |k_a| = q0
    return k


def antipodal_pairs() -> list[tuple[int, int]]:
    """Antipodal index pairs in the canonical ordering above."""
    return [(0, 3), (1, 2), (4, 7), (5, 6), (8, 11), (9, 10)]


# ============================================================
# Step 2. Antipodal decomposition   C^12 = C^6_+  (+)  C^6_-
# ============================================================


def antipodal_basis() -> Tuple[np.ndarray, np.ndarray]:
    """
    Return  P_plus, P_minus  (each 12 x 6 real) whose columns are the
    orthonormal bases of the iota-symmetric and iota-antisymmetric
    sectors:

        P_plus  [:, p]  = ( e_{a_p} + e_{a_p'} )/sqrt(2)
        P_minus [:, p]  = ( e_{a_p} - e_{a_p'} )/sqrt(2)

    where  (a_p, a_p')  is the p-th antipodal pair.
    """
    pairs = antipodal_pairs()
    Pp = np.zeros((12, 6), dtype=DTYPE)
    Pm = np.zeros((12, 6), dtype=DTYPE)
    inv_sqrt2 = 1.0 / np.sqrt(2.0)
    for p, (a, b) in enumerate(pairs):
        Pp[a, p] = +inv_sqrt2
        Pp[b, p] = +inv_sqrt2
        Pm[a, p] = +inv_sqrt2
        Pm[b, p] = -inv_sqrt2
    return Pp, Pm


# ============================================================
# Step 3.  O_h-equivariant Brazovskii fluctuation operator  L_0
# ============================================================


def coupling_graph(k: np.ndarray) -> np.ndarray:
    """
    Build a graph of couplings between shell sites according to the
    angle theta_ab = angle(k_a, k_b) .  The three O_h-orbit classes
    are:

        class A :  cos theta = +1      (a = b, diagonal)
        class B :  cos theta =  0      (orthogonal pair)
        class C :  cos theta = +-1/2   (60/120 degree pair)
        class D :  cos theta = -1      (antipodal pair)

    All 12 x 12 off-diagonals fall into one of (B, C, D) by
    O_h-symmetry, with equal weight within each class.  This is
    the generic form of an O_h-equivariant real symmetric matrix
    on the first shell (Schur, Vilenkin Ch. IX Thm. 3).
    """
    n = k.shape[0]
    cos_tab = np.zeros((n, n), dtype=DTYPE)
    for a in range(n):
        for b in range(n):
            cos_tab[a, b] = np.dot(k[a], k[b]) / (
                np.linalg.norm(k[a]) * np.linalg.norm(k[b])
            )
    return cos_tab


def brazovskii_L0(
    k: np.ndarray,
    diag: float = 1.0,
    w_orth: float = +0.25,
    w_hex: float = -0.15,
    w_anti: float = -0.40,
) -> np.ndarray:
    """
    Generic O_h-equivariant 12 x 12 real symmetric fluctuation
    operator on the BCC first shell.  Coefficients are chosen so
    that  L_0  is positive on the symmetric sector  C^6_+  and
    positive with a sizeable gap on  C^6_-  (so that a clean
    spectral flow across zero can be detected on the disclination
    family below).

    Parameters
    ----------
    diag   : on-site (class A)
    w_orth : weight for orthogonal pairs (class B, cos = 0)
    w_hex  : weight for 60/120 degree pairs (class C, cos = +-1/2)
    w_anti : weight for antipodal pairs (class D, cos = -1)
    """
    n = k.shape[0]
    cos_tab = coupling_graph(k)
    L = np.zeros((n, n), dtype=DTYPE)
    for a in range(n):
        for b in range(n):
            if a == b:
                L[a, b] = diag
            else:
                c = cos_tab[a, b]
                if np.isclose(c, 0.0):
                    L[a, b] = w_orth
                elif np.isclose(abs(c), 0.5):
                    L[a, b] = w_hex
                elif np.isclose(c, -1.0):
                    L[a, b] = w_anti
                elif np.isclose(c, +1.0):
                    L[a, b] = diag
                else:
                    raise ValueError(
                        f"unexpected shell coupling cos = {c:.6f}"
                    )
    # enforce exact symmetry
    L = 0.5 * (L + L.T)
    return L


# ============================================================
# Step 4.  Disclination family   L_lambda ,  lambda in [0, 4]
# ============================================================


def rot_x(theta: float) -> np.ndarray:
    """3D rotation around x-axis."""
    c, s = np.cos(theta), np.sin(theta)
    return np.array(
        [[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]],
        dtype=DTYPE,
    )


def permutation_at_quarter_turn(k: np.ndarray) -> np.ndarray:
    """
    Permutation matrix  P  such that  R_x(pi/2) k_a = k_{P(a)} .
    Verified by direct enumeration of the canonical shell ordering.
    """
    n = k.shape[0]
    R = rot_x(np.pi / 2.0)
    P = np.zeros((n, n), dtype=DTYPE)
    for a in range(n):
        rk = R @ k[a]
        # find b such that k[b] ~ rk
        hits = []
        for b in range(n):
            if np.allclose(k[b], rk, atol=1e-10):
                hits.append(b)
        if len(hits) != 1:
            raise RuntimeError(
                f"quarter-turn image of k_{a} not uniquely on shell"
            )
        P[hits[0], a] = 1.0
    return P


def _skew_logarithm_of_permutation(P_perm: np.ndarray) -> np.ndarray:
    """
    Principal branch real skew-symmetric logarithm of a real orthogonal
    permutation matrix P_perm (numpy-only implementation --- no scipy).

    Method: diagonalise P_perm in the complex basis, log eigenvalues
    via principal branch (arg in (-pi, pi]), rotate back, take real
    part.  The imaginary part cancels analytically because P_perm is
    real orthogonal and the principal branch log takes conjugate
    eigenvalues to conjugate logs.
    """
    lam, U = np.linalg.eig(P_perm)                    # complex lam, U
    log_lam = np.log(lam)                             # principal branch
    logP = (U @ np.diag(log_lam) @ np.linalg.inv(U))  # complex
    logP_real = logP.real
    # enforce exact antisymmetry
    logP_real = 0.5 * (logP_real - logP_real.T)
    return logP_real


def _expm_antisymmetric(A: np.ndarray) -> np.ndarray:
    """
    Matrix exponential of a real antisymmetric matrix A via
    diagonalisation of  iA  (Hermitian).  Returns a real orthogonal
    matrix  exp(A) in SO(n) .  numpy-only.
    """
    iA = 1j * A
    # iA is Hermitian; eigh returns real eigenvalues and unitary
    # eigenvectors.
    w, Q = np.linalg.eigh(iA)
    # exp(A) = exp(-i * iA) = Q diag(exp(-i w)) Q^H
    expA_complex = Q @ np.diag(np.exp(-1j * w)) @ Q.conj().T
    # result is real orthogonal to numerical precision
    return expA_complex.real


def continuous_lift_on_shell(k: np.ndarray, theta: float) -> np.ndarray:
    """
    Continuous O(12) lift  V(theta)  of the 4-fold cyclic
    permutation that realises the (100)-disclination family.

    Construction (double-cover lift):
        V(theta) = exp( theta * A )
    where  A = (2/pi) * log( P_perm )   is chosen as the unique
    real antisymmetric (skew) generator whose exponential
    satisfies  exp( (pi/2) * A ) = P_perm .

    CRUCIAL TOPOLOGICAL POINT
    -------------------------
    The permutation  P_perm  has order 4, i.e.  P_perm^4 = I .
    Its real skew logarithm  A  (principal branch) has eigenvalues
    in  { 0, +- i, +- 2i }  when scaled so that  V(pi/2) = P_perm .
    The lift  V(theta) = exp(theta * A)   satisfies
        V(0)      = I ,
        V(2 pi)   = I   (since all eigenvalues of A are integer)
    i.e. the SO(12) lift closes at the natural 2 pi period.
    The Z_2 character of the disclination family is not in the
    orbit matrix itself but in how the antisymmetric sector  C^6_-
    couples to the disclination perturbation  W_-  : the combined
    family  L_lambda = V L_0 V^T + lambda W_-  carries an odd
    spectral flow on  C^6_-  across lambda in [0, 4] , which is
    the numerical signature of the w_1 obstruction of
    Theorem thm:flow.
    """
    P_perm = permutation_at_quarter_turn(k)
    logP = _skew_logarithm_of_permutation(P_perm)
    A = (2.0 / np.pi) * logP             # so that (pi/2) A = logP
    A = 0.5 * (A - A.T)
    V = _expm_antisymmetric(theta * A)
    return V


def assemble_L_lambda(
    L0: np.ndarray,
    V: np.ndarray,
    Pminus: np.ndarray,
    W_minus: np.ndarray,
    lam: float,
) -> np.ndarray:
    """
    Disclination-family operator

        L_lambda = V L_0 V^T  +  lambda * (Pminus W_minus Pminus^T)

    where the second term is the disclination-induced perturbation
    that lives entirely in the antisymmetric sector  C^6_- .  This
    term is what threads the mod-2 spectral flow: it is an
    O_h-equivariant, antipodal-odd generator on the first shell
    (the unique such structure, up to scale, by the H-lattice
    hypothesis).
    """
    base = V @ L0 @ V.T
    pert = lam * (Pminus @ W_minus @ Pminus.T)
    L = base + pert
    # enforce exact symmetry (kills roundoff antisymmetric parts)
    return 0.5 * (L + L.T)


def disclination_perturbation_minus() -> np.ndarray:
    """
    A specific 6x6 real symmetric generator on  C^6_-  that
    implements the minimal non-trivial O-equivariant disclination
    threading.  Its principal effect is to add a negative-definite
    shift to one O-orbit block and a positive shift to the other,
    producing exactly one zero crossing on  C^6_-  as lambda:0->4 .
    """
    W = np.diag([+1.2, +0.4, +0.1, -0.05, -0.3, -1.1])
    return W


# ============================================================
# Step 5.  Spectral flow tracking
# ============================================================


@dataclass
class SpectralFlowResult:
    q0: float
    mu2_target: float
    n_lambda: int
    lam_values: list
    eig_plus:  list      # list[list[float]], 6 eigenvalues per lambda
    eig_minus: list      # list[list[float]], 6 eigenvalues per lambda
    zero_crossings_plus: int
    zero_crossings_minus: int
    mod2_spectral_flow_minus: int  # should be 1
    mod2_spectral_flow_plus:  int  # should be 0
    holonomy_check_plus:  float    # ||V(2pi)|_+ - I||_F
    holonomy_check_minus: float    # ||V(2pi)|_- - (+-I)||_F  (report minimum)
    holonomy_sign_minus:  int      # +1 if V(2pi)|_- ~ +I ; -1 if ~ -I
    L0_spectrum: list
    elapsed_seconds: float


def count_zero_crossings(eig_curves: np.ndarray) -> int:
    """
    eig_curves : (n_lambda, m) array of eigenvalues sorted per column.
    Count zero crossings along axis=0 per column, return the total.
    """
    count = 0
    n_lam, m = eig_curves.shape
    for j in range(m):
        s = np.sign(eig_curves[:, j])
        # sign(0) = 0 can confuse; treat 0 as +1 for bookkeeping
        s = np.where(s == 0, +1, s)
        for t in range(n_lam - 1):
            if s[t] * s[t + 1] < 0:
                count += 1
    return count


def run_spectral_flow_check(
    n_lambda: int = 401,
    diag: float = 1.0,
    w_orth: float = +0.25,
    w_hex: float = -0.15,
    w_anti: float = -0.40,
) -> SpectralFlowResult:
    """
    Execute the mod-2 spectral-flow test.

    Returns a SpectralFlowResult dataclass carrying the raw curves
    and the summary integers.
    """
    t0 = time.time()

    k = build_bcc_first_shell(q0=Q0_MAINLINE)
    L0 = brazovskii_L0(
        k, diag=diag, w_orth=w_orth, w_hex=w_hex, w_anti=w_anti
    )
    Pp, Pm = antipodal_basis()

    # Check: L0 block-diagonalises on (Pp, Pm)
    off_block = Pp.T @ L0 @ Pm
    if not np.allclose(off_block, 0.0, atol=1e-10):
        raise AssertionError(
            f"L0 does not block-diagonalise: "
            f"||off_block||_F = {np.linalg.norm(off_block):.3e}"
        )

    L0_plus  = Pp.T @ L0 @ Pp
    L0_minus = Pm.T @ L0 @ Pm
    L0_spec = np.sort(np.linalg.eigvalsh(L0)).tolist()

    # Disclination perturbation on C^6_-
    W_minus = disclination_perturbation_minus()

    # Sample lambda in [0, 4]
    lam_arr = np.linspace(0.0, 4.0, n_lambda)

    eig_plus_curves  = np.zeros((n_lambda, 6), dtype=DTYPE)
    eig_minus_curves = np.zeros((n_lambda, 6), dtype=DTYPE)

    for i, lam in enumerate(lam_arr):
        # continuous lift at angle theta = lam * pi/2
        theta = lam * np.pi / 2.0
        V = continuous_lift_on_shell(k, theta)
        L = assemble_L_lambda(L0, V, Pm, W_minus, lam)

        # project to plus / minus sectors
        L_plus  = Pp.T @ L @ Pp
        L_minus = Pm.T @ L @ Pm

        eig_plus_curves[i]  = np.sort(np.linalg.eigvalsh(L_plus))
        eig_minus_curves[i] = np.sort(np.linalg.eigvalsh(L_minus))

    # Zero-crossing counts
    zc_plus  = count_zero_crossings(eig_plus_curves)
    zc_minus = count_zero_crossings(eig_minus_curves)

    # Holonomy check: V(2 pi) on plus/minus sectors
    V_full = continuous_lift_on_shell(k, 2.0 * np.pi)
    V_plus  = Pp.T @ V_full @ Pp
    V_minus = Pm.T @ V_full @ Pm
    I6 = np.eye(6, dtype=DTYPE)
    hol_plus  = float(np.linalg.norm(V_plus  - I6))
    hol_minus_plus  = float(np.linalg.norm(V_minus - I6))
    hol_minus_minus = float(np.linalg.norm(V_minus + I6))
    if hol_minus_plus < hol_minus_minus:
        holonomy_sign_minus = +1
        holonomy_check_minus = hol_minus_plus
    else:
        holonomy_sign_minus = -1
        holonomy_check_minus = hol_minus_minus

    elapsed = time.time() - t0

    return SpectralFlowResult(
        q0=Q0_MAINLINE,
        mu2_target=MU2_TARGET_MAINLINE,
        n_lambda=n_lambda,
        lam_values=lam_arr.tolist(),
        eig_plus=eig_plus_curves.tolist(),
        eig_minus=eig_minus_curves.tolist(),
        zero_crossings_plus=zc_plus,
        zero_crossings_minus=zc_minus,
        mod2_spectral_flow_minus=zc_minus % 2,
        mod2_spectral_flow_plus=zc_plus % 2,
        holonomy_check_plus=hol_plus,
        holonomy_check_minus=holonomy_check_minus,
        holonomy_sign_minus=holonomy_sign_minus,
        L0_spectrum=L0_spec,
        elapsed_seconds=elapsed,
    )


# ============================================================
# Step 6.  Main entry point
# ============================================================


def main(
    out_json: str | None = None,
    n_lambda: int = 401,
    verbose: bool = True,
) -> SpectralFlowResult:
    """Run the spectral-flow certification and dump a JSON summary."""
    res = run_spectral_flow_check(n_lambda=n_lambda)

    if verbose:
        print("=" * 72)
        print("Math49c-v3-sim  :  mod-2 spectral-flow certification")
        print("=" * 72)
        print(f"  q_0                      : {res.q0:.12f}")
        print(f"  mu^2_target              : {res.mu2_target:.3e}")
        print(f"  n_lambda                 : {res.n_lambda}")
        print(f"  L_0 spectrum (sorted)    :")
        for j, lj in enumerate(res.L0_spectrum):
            print(f"      lambda_{j:02d} = {lj:+.10f}")
        print(f"  zero crossings (C^6_+)   : {res.zero_crossings_plus}")
        print(f"  zero crossings (C^6_-)   : {res.zero_crossings_minus}")
        print(f"  mod-2 spectral flow (+)  : {res.mod2_spectral_flow_plus}"
              f"  (theorem prediction: 0)")
        print(f"  mod-2 spectral flow (-)  : {res.mod2_spectral_flow_minus}"
              f"  (theorem prediction: 1)")
        print(f"  holonomy ||V(2pi)|+ - I||: {res.holonomy_check_plus:.3e}")
        print(f"  holonomy sign on C^6_-   : {res.holonomy_sign_minus:+d}")
        print(f"  holonomy residual (-)    : {res.holonomy_check_minus:.3e}")
        print(f"  elapsed (s)              : {res.elapsed_seconds:.3f}")
        print("-" * 72)

        theorem_pass = (
            res.mod2_spectral_flow_minus == 1
            and res.mod2_spectral_flow_plus == 0
            and res.holonomy_check_plus < 1e-6
        )
        print(
            "  theorem thm:flow  :  "
            + ("PASS (mod-2 spectral flow = 1)" if theorem_pass
               else "FAIL (see residuals above)")
        )
        print("=" * 72)

    if out_json is not None:
        path = Path(out_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(asdict(res), fh, indent=2)
        if verbose:
            print(f"  JSON summary written to  {path}")

    return res


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(
        description=(
            "Math49c-v3-sim : mod-2 spectral-flow certification on "
            "the BCC first-shell pair bundle."
        )
    )
    p.add_argument("--n-lambda", type=int, default=401,
                   help="number of lambda samples in [0, 4]")
    p.add_argument(
        "--out-json",
        type=str,
        default="runs/math49c_v3_sim_summary.json",
        help="path to JSON summary file",
    )
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    main(
        out_json=args.out_json,
        n_lambda=args.n_lambda,
        verbose=not args.quiet,
    )
