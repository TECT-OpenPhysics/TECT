#!/usr/bin/env python3
# =====================================================================
# bcc_analytic_seed.py
# Theory tag:  Math82-Addendum-B-Phase-Z-BCC-analytic-seed-2026-04-24
# Module version: v0.1
# Purpose:     Construct the BCC analytic seed for the Math55 deep-endpoint
#              continuation run, replacing the default thermal seed
#              (sigma ≈ 0.266) with the explicit 6-pair BCC-shell ansatz
#              that is much closer to the deep-mu^2 condensed equilibrium.
#
# Mathematical content:
#   The 12 first-shell BCC reciprocal-lattice vectors come in 6 ± pairs:
#       q_1 = (1, 1, 0)/sqrt(2)        q_2 = (1, -1, 0)/sqrt(2)
#       q_3 = (1, 0, 1)/sqrt(2)        q_4 = (1, 0, -1)/sqrt(2)
#       q_5 = (0, 1, 1)/sqrt(2)        q_6 = (0, 1, -1)/sqrt(2)
#   each scaled by the physical wavenumber Q0_PHYSICAL = 0.6801747616
#   (in lattice units a = 1).
#
#   The BCC analytic ansatz is
#       Psi_BCC(x) = A_BCC * sum_{j=1}^{6} cos(Q0 * q_j . x)
#   with amplitude
#       A_BCC = sqrt(|mu^2| / (15 * gamma))    (Brazovskii saddle-point)
#   For the locked-point (mu^2 = -1.0, gamma = 1.62) this gives
#       A_BCC ~ 0.203.
#
# Channel distribution:
#   The active backend (real_backend_pt_bcc_mixed_v3) expects shape
#   (3, N, N, N) complex128 representing three "family" channels. We
#   distribute the BCC scalar field across the three channels using the
#   locked direction z0 = (1, 1, 1)/sqrt(3) (matching the family-locking
#   convention). Imaginary parts are zero (BCC ground state is real).
#
# Usage (CLI):
#   python -u Codes/pde/bcc_analytic_seed.py \
#       --N 32 --L 62.20036 --mu2 -1.0 --gamma 1.62 \
#       --output Psi_BCC_N32_mu2_-1.npy
#
#   The output file is shape (3, N, N, N) complex128, ready to be loaded
#   into continuation_mu2_v25.py via the --load-psi flag.
#
# Math note: docs/math/TECT-Math82-Addendum-B-Phase-Z-BCC-analytic-seed-runbook.tex.txt
# =====================================================================

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Tuple

import numpy as np


# -- Physical constants (mirror of math56_constants.py values, kept local
#    to avoid PDE/ vs Codes/pde/ import-path coupling during Task #54
#    dual-tree window) -------------------------------------------------------
Q0_PHYSICAL: float = 0.6801747616
"""Physical BCC first-shell wavenumber in lattice units (a = 1)."""

LOCKED_FAMILY_DIRECTION: np.ndarray = np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0)
"""Locked z0 direction in the 3-family channel space."""


def bcc_primitive_wavevectors() -> np.ndarray:
    """Return the 6 independent BCC first-shell unit wave-vectors.

    Returns
    -------
    np.ndarray
        Shape (6, 3); each row is a unit vector q_j (|q_j| = 1).
        The 12 first-shell vectors are obtained as {±q_j}.
    """
    inv_sqrt2 = 1.0 / math.sqrt(2.0)
    q = np.array(
        [
            [+1, +1,  0],
            [+1, -1,  0],
            [+1,  0, +1],
            [+1,  0, -1],
            [ 0, +1, +1],
            [ 0, +1, -1],
        ],
        dtype=np.float64,
    ) * inv_sqrt2
    # Verify unit normalisation
    norms = np.linalg.norm(q, axis=1)
    assert np.allclose(norms, 1.0), f"BCC primitive q-vectors not unit: |q| = {norms}"
    return q


def amplitude_BCC_brazovskii(mu2: float, gamma: float = 1.62) -> float:
    """Brazovskii saddle-point amplitude for the deep-BCC condensate.

    Per peak (one of the 6 cosines), the equilibrium amplitude that
    minimises the Brazovskii free energy at locked (mu^2, lambda, gamma)
    is approximately
        A_BCC = sqrt(|mu^2| / (15 * gamma))
    in the cold-condensed limit |mu^2| >> R_C.

    For mu^2 = -1.0, gamma = 1.62: A_BCC ~ 0.203.
    """
    if mu2 >= 0:
        # In the metastable / pre-condensation regime use a smaller seed
        # amplitude to avoid over-shooting.
        return 0.05 * math.sqrt(abs(mu2) + 0.01)
    return math.sqrt(abs(mu2) / (15.0 * gamma))


SUBSET_4COSINE_INDICES: tuple = (0, 2, 4, 5)
"""For mode='subset_4cosine', use these 4 of the 6 BCC primitive vectors.
Indices into bcc_primitive_wavevectors() output: q_1, q_3, q_5, q_6.
This breaks O_h to a D_4-like subgroup, producing an elongated BCC
variant rather than the maximally-symmetric saddle (Math82-Addendum-D
Theorem `thm:saddle`)."""


def construct_bcc_analytic_seed(
    N: int,
    L: float,
    mu2: float = -1.0,
    gamma: float = 1.62,
    A_BCC_override: float = None,
    z0: np.ndarray = None,
    return_metadata: bool = False,
    mode: str = "bcc_analytic",
    phase_seed: int = 42,
) -> np.ndarray:
    """Build the BCC analytic seed Psi(x) of shape (3, N, N, N) complex128.

    Parameters
    ----------
    N : int
        Grid dimension (cube N x N x N).
    L : float
        Physical box length. Convention: x_i in [0, L) on a periodic
        lattice with N points per axis.
    mu2 : float
        Brazovskii mass parameter (target operating point, default -1.0).
    gamma : float
        Brazovskii cubic coupling (locked, default 1.62).
    A_BCC_override : float, optional
        Override the saddle-point amplitude. If None, use
        amplitude_BCC_brazovskii(mu2, gamma).
    z0 : np.ndarray, optional
        Locked family direction (length-3). If None, use
        LOCKED_FAMILY_DIRECTION = (1, 1, 1)/sqrt(3).
    return_metadata : bool
        If True, also return a dict of construction parameters.

    Returns
    -------
    Psi : np.ndarray
        Shape (3, N, N, N), dtype complex128.
    metadata : dict (only if return_metadata=True)
        {N, L, mu2, gamma, A_BCC, Q0, z0, q_vectors, theory_tag}.
    """
    if z0 is None:
        z0 = LOCKED_FAMILY_DIRECTION
    z0 = np.asarray(z0, dtype=np.complex128)
    z0 = z0 / np.linalg.norm(z0)
    assert z0.shape == (3,), f"z0 must be length 3; got shape {z0.shape}"

    if A_BCC_override is None:
        A_BCC = amplitude_BCC_brazovskii(mu2, gamma)
    else:
        A_BCC = float(A_BCC_override)

    # Spatial grid (periodic): x_i = i * (L/N) for i in 0..N-1
    dx = L / N
    coords_1d = np.arange(N, dtype=np.float64) * dx     # (N,)
    X, Y, Z = np.meshgrid(coords_1d, coords_1d, coords_1d, indexing="ij")  # each (N, N, N)

    # Build the scalar BCC field on the spatial grid.
    # Math82-Addendum-E (2026-04-24) adds three new modes that break
    # the O_h symmetry of the default 6-cosine ansatz, putting the seed
    # inside the basin of one of the 24 BCC ground-state variants
    # rather than at the maximally-symmetric saddle.
    qvecs_unit = bcc_primitive_wavevectors()              # (6, 3)
    qvecs = qvecs_unit * Q0_PHYSICAL                       # (6, 3), scaled
    Psi_scalar = np.zeros((N, N, N), dtype=np.float64)

    if mode == "bcc_analytic":
        # Default: maximally-O_h-symmetric 6-cosine ansatz.
        # WARNING: Math82-Addendum-D shows this is a SADDLE, not a minimum.
        for j in range(qvecs.shape[0]):
            qx, qy, qz = qvecs[j]
            phase = qx * X + qy * Y + qz * Z
            Psi_scalar += np.cos(phase)

    elif mode == "subset_4cosine":
        # Math82-Addendum-E Option A: use 4 of 6 wave-vectors, breaking
        # O_h to a D_4-like subgroup. Default indices = (0, 2, 4, 5)
        # = {q_1, q_3, q_5, q_6}, an elongated BCC variant.
        idx = SUBSET_4COSINE_INDICES
        for j in idx:
            qx, qy, qz = qvecs[j]
            phase = qx * X + qy * Y + qz * Z
            Psi_scalar += np.cos(phase)
        # Re-normalise so RMS amplitude is comparable to symmetric seed
        # (4 cosines instead of 6 → multiply by sqrt(6/4) = sqrt(1.5))
        Psi_scalar *= math.sqrt(6.0 / len(idx))

    elif mode in ("phase_random", "full_12cosine_random_phase"):
        # Math82-Addendum-E Option B: 6 cosines but each with random
        # phase shift theta_j in [0, 2pi). Generic O_h breaking.
        rng = np.random.default_rng(seed=phase_seed)
        thetas = rng.uniform(0, 2.0 * math.pi, size=qvecs.shape[0])
        for j in range(qvecs.shape[0]):
            qx, qy, qz = qvecs[j]
            phase = qx * X + qy * Y + qz * Z + thetas[j]
            Psi_scalar += np.cos(phase)

    elif mode == "subset_4cosine_random_phase":
        # Math82-Addendum-E hybrid: 4-cosine subset AND random phases.
        # Maximally symmetry-broken; safest option for BCC minimum search.
        idx = SUBSET_4COSINE_INDICES
        rng = np.random.default_rng(seed=phase_seed)
        thetas = rng.uniform(0, 2.0 * math.pi, size=len(idx))
        for k, j in enumerate(idx):
            qx, qy, qz = qvecs[j]
            phase = qx * X + qy * Y + qz * Z + thetas[k]
            Psi_scalar += np.cos(phase)
        Psi_scalar *= math.sqrt(6.0 / len(idx))

    else:
        raise ValueError(
            f"Unrecognised mode '{mode}'; must be one of: "
            "'bcc_analytic' (default symmetric 6-cosine, SADDLE warning), "
            "'subset_4cosine' (Math82-Addendum-E Option A), "
            "'phase_random' (Math82-Addendum-E Option B), "
            "'subset_4cosine_random_phase' (Math82-Addendum-E hybrid)."
        )

    Psi_scalar *= A_BCC

    # Distribute across the 3-channel family direction
    # Psi[a, x] = z0[a] * Psi_scalar(x), so that the family-projector
    # P0 = z0 z0^* maps Psi -> Psi (locked-direction seed).
    Psi = np.zeros((3, N, N, N), dtype=np.complex128)
    for a in range(3):
        Psi[a] = z0[a] * Psi_scalar.astype(np.complex128, copy=False)

    if return_metadata:
        meta = {
            "theory_tag": "Math82-Addendum-E-Phase-Z-symmetry-broken-seed-2026-04-24" if mode != "bcc_analytic" else "Math82-Addendum-B-Phase-Z-BCC-analytic-seed-2026-04-24",
            "module_version": "v0.2",
            "mode": mode,
            "phase_seed": phase_seed if mode in ("phase_random", "full_12cosine_random_phase", "subset_4cosine_random_phase") else None,
            "subset_indices": list(SUBSET_4COSINE_INDICES) if mode in ("subset_4cosine", "subset_4cosine_random_phase") else None,
            "N": N,
            "L": L,
            "mu2": mu2,
            "gamma": gamma,
            "A_BCC": A_BCC,
            "Q0_PHYSICAL": Q0_PHYSICAL,
            "z0_real": z0.real.tolist(),
            "z0_imag": z0.imag.tolist(),
            "q_vectors_unit": bcc_primitive_wavevectors().tolist(),
            "shape": list(Psi.shape),
            "dtype": str(Psi.dtype),
            "rms_amplitude": float(np.sqrt(np.mean(np.abs(Psi) ** 2))),
            "max_abs": float(np.max(np.abs(Psi))),
        }
        return Psi, meta
    return Psi


# ============================================================================
# CLI entry point
# ============================================================================
def _cli() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Construct the BCC analytic seed for the Math55 deep-endpoint "
            "continuation run. Output is a single .npy file of shape "
            "(3, N, N, N) complex128 ready for --load-psi in "
            "continuation_mu2_v25.py."
        )
    )
    parser.add_argument("--N", type=int, default=32, help="Grid dimension (default 32)")
    parser.add_argument(
        "--L", type=float, default=62.20036,
        help="Box length (default 62.20036, BCC-commensurate L_BCC^(7))"
    )
    parser.add_argument(
        "--mu2", type=float, default=-1.0,
        help="Brazovskii mu^2 target (used to estimate amplitude; default -1.0)"
    )
    parser.add_argument(
        "--gamma", type=float, default=1.62,
        help="Brazovskii gamma (locked at 1.62; default 1.62)"
    )
    parser.add_argument(
        "--A-BCC", dest="A_BCC", type=float, default=None,
        help="Override saddle-point amplitude (default: derive from mu^2 and gamma)"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output .npy path (default: Psi_BCC_N{N}_mu2_{mu2}.npy)"
    )
    parser.add_argument(
        "--metadata-output", type=str, default=None,
        help="Output JSON metadata path (default: <output>.meta.json)"
    )
    parser.add_argument(
        "--mode", type=str, default="bcc_analytic",
        choices=["bcc_analytic", "subset_4cosine", "phase_random", "full_12cosine_random_phase", "subset_4cosine_random_phase"],
        help="Seed construction mode (Math82-Addendum-E v0.2 added 3 symmetry-broken modes). "
             "Default 'bcc_analytic' = symmetric 6-cosine (SADDLE per Math82-Addendum-D); "
             "'subset_4cosine' = Option A (4 of 6 cosines, elongated BCC variant); "
             "'phase_random' = Option B (6 cosines + random phases); "
             "'subset_4cosine_random_phase' = hybrid (most symmetry-broken)."
    )
    parser.add_argument(
        "--phase-seed", dest="phase_seed", type=int, default=42,
        help="RNG seed for random phases (modes phase_random and subset_4cosine_random_phase only). "
             "Default 42, deterministic."
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress diagnostic output"
    )
    args = parser.parse_args()

    Psi, meta = construct_bcc_analytic_seed(
        N=args.N,
        L=args.L,
        mu2=args.mu2,
        gamma=args.gamma,
        A_BCC_override=args.A_BCC,
        return_metadata=True,
        mode=args.mode,
        phase_seed=args.phase_seed,
    )

    out_path = (
        args.output if args.output is not None
        else f"Psi_BCC_N{args.N}_mu2_{args.mu2}.npy"
    )
    meta_path = (
        args.metadata_output if args.metadata_output is not None
        else f"{out_path}.meta.json"
    )

    np.save(out_path, Psi)
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    if not args.quiet:
        print("=" * 70)
        print(" BCC analytic seed constructed")
        print("=" * 70)
        print(f"  mode         = {args.mode}")
        if args.mode in ("phase_random", "full_12cosine_random_phase", "subset_4cosine_random_phase"):
            print(f"  phase_seed   = {args.phase_seed}")
        if args.mode in ("subset_4cosine", "subset_4cosine_random_phase"):
            print(f"  subset_idx   = {SUBSET_4COSINE_INDICES} (4 of 6 BCC primitives)")
        print(f"  N            = {args.N}")
        print(f"  L            = {args.L} (lattice units)")
        print(f"  mu^2         = {args.mu2}")
        print(f"  gamma        = {args.gamma}")
        print(f"  Q0_PHYSICAL  = {Q0_PHYSICAL}")
        print(f"  A_BCC        = {meta['A_BCC']:.6f}  ({'override' if args.A_BCC else 'saddle-point'})")
        print(f"  shape        = {meta['shape']}")
        print(f"  dtype        = {meta['dtype']}")
        print(f"  RMS|Psi|     = {meta['rms_amplitude']:.6e}")
        print(f"  max|Psi|     = {meta['max_abs']:.6e}")
        print()
        print(f"  Saved to:        {out_path}")
        print(f"  Metadata saved:  {meta_path}")


if __name__ == "__main__":
    _cli()
