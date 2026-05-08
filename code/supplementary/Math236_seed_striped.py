#!/usr/bin/env python3
# =====================================================================
# Math236_seed_striped.py
#
# Striped-seed synthesiser for Brazovskii Newton-Krylov warm-start
# (companion to Math236_continuum_limit_scan.py).
#
# Motivation (Math290 §5)
# -----------------------
# The first F-Pillar6 production run (Run id math236_20260430_172601Z,
# 39394 s wall time on N=16) converged to a near-trivial saddle:
#
#   F(Psi*) = +3.7533661358e-06     (vs. F(0) = 0)
#   Delta F = +3.75e-6 > 0          ("condensate NOT favorable")
#   lambda_min(Hessian|_{Psi*}) = -4.78e-01   (negative -> saddle)
#   Psi* shape = (3, 16, 16, 16)    (vector field, 3 components)
#
# At mu^2 = -0.7 the broken-phase Brazovskii minimum is expected to
# sit at f ~ O(1) with Psi(x) ~ A * cos(q_0 * n_hat . x), n_hat in S^2.
# The default (presumably symmetric / random) seed used by the v25
# driver does not reliably enter the broken-phase basin at coarse N.
# This script produces a deterministic striped Psi^{(0)} that can be
# passed via `--load-psi <path>` to continuation_mu2_v25.py.
#
# The seed is constructed in real space:
#
#   Psi^{(0)}_c(x) = A_0 * e_hat^c * cos(q_0 * n_hat . x)
#
# where:
#   - A_0 is a user-supplied amplitude (default 1.0 post-Math294-AddA;
#     was 0.5 pre-2026-05-01 — strengthened after the 2026-05-01
#     A_0=0.5 borderline-basin run that briefly entered the broken-phase
#     basin (F: +184.7 -> -171.7 at Newton step 3) but was ejected via
#     trust-region overshoot at step 4. Math294 Theorem 294.1 +
#     Proposition 294.3 lattice-corrected estimate puts basin-entry
#     threshold at A_0 ~ 0.5-0.7 on N=16; A_0=1.0 is robustly inside.)
#   - e_hat is a unit polarisation vector in component space (default
#     e_hat = (1, 0, 0))
#   - n_hat is a unit propagation direction in real space (default
#     n_hat = (1, 0, 0))
#   - q_0 is the Brazovskii peak wavenumber (read from config or CLI)
#
# The component-space dimensionality matches the v25 driver's expected
# field shape (3-component compression mode by default; can be set to
# 1 for scalar). The output .npy is dtype complex128 to match the v25
# driver's persistence format (Psi_final.npy is complex128).
#
# Usage
# -----
#   python -u Codes/supplementary/Math236_seed_striped.py \
#       --N 16 --L-box 16.0 --q0 0.6801747616 \
#       --A0 0.5 --n-comp 3 \
#       --output Runs/continuation/seed_striped_N16.npy
#
# Then plug it into the wrapper via:
#   python -u Codes/pde/continuation_mu2_v25.py \
#       --config <config> --N 16 --mu2 -0.7 \
#       --output <out> --max-newton 50 --tol-newton 1e-5 \
#       --load-psi Runs/continuation/seed_striped_N16.npy
#
# For a multi-N scan, generate one seed per N:
#   for N in 16 32 64; do
#     python -u Codes/supplementary/Math236_seed_striped.py \
#       --N $N --L-box 16.0 --q0 0.6801747616 \
#       --output Runs/continuation/seed_N${N}.npy
#   done
#
# Author: Jusang Lee (with collaboration), 2026-05-01.
# Status: Math290 §7 action item #3 deliverable.
# =====================================================================
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def synthesize_striped_seed(
    N: int,
    L_box: float,
    q0: float,
    A0: float = 1.0,
    n_comp: int = 3,
    polarisation: tuple[float, float, float] = (1.0, 0.0, 0.0),
    direction: tuple[float, float, float] = (1.0, 0.0, 0.0),
    dtype: np.dtype = np.complex128,
) -> np.ndarray:
    """Build a deterministic striped Psi^{(0)}.

    Returns an array of shape (n_comp, N, N, N) containing
        Psi^{(0)}_c(x) = A_0 * e_hat^c * cos(q_0 * n_hat . x)
    with e_hat = polarisation/|polarisation| and n_hat = direction/|direction|.

    The lattice is x_i = i * a, i = 0, ..., N-1, a = L_box / N, in each
    spatial axis. Periodic boundary conditions are not enforced explicitly
    (the cosine is naturally periodic in the box only when q_0 * L_box is
    an integer multiple of 2 pi; otherwise this is a near-mode seed and
    the Newton iteration is responsible for relaxing onto the discrete
    BCC primitive shell)."""
    if N <= 0:
        raise ValueError(f"N must be positive, got {N}")
    if n_comp <= 0:
        raise ValueError(f"n_comp must be positive, got {n_comp}")

    a_lat = L_box / N
    # Normalize polarisation in component space (truncate or zero-pad to
    # n_comp components).
    e = np.zeros(n_comp, dtype=np.float64)
    for i in range(min(len(polarisation), n_comp)):
        e[i] = float(polarisation[i])
    norm_e = np.linalg.norm(e)
    if norm_e == 0.0:
        raise ValueError("polarisation must be non-zero")
    e = e / norm_e

    # Normalize propagation direction in real space.
    nhat = np.array(direction, dtype=np.float64)
    if nhat.shape != (3,):
        raise ValueError(f"direction must be 3D, got shape {nhat.shape}")
    norm_n = np.linalg.norm(nhat)
    if norm_n == 0.0:
        raise ValueError("direction must be non-zero")
    nhat = nhat / norm_n

    # Real-space grid (i, j, k in {0, ..., N-1})
    idx = np.arange(N, dtype=np.float64) * a_lat
    X, Y, Z = np.meshgrid(idx, idx, idx, indexing="ij")
    phase = q0 * (nhat[0] * X + nhat[1] * Y + nhat[2] * Z)
    base = A0 * np.cos(phase)  # shape (N, N, N), real

    # Broadcast to (n_comp, N, N, N) with component-space polarisation.
    psi = e[:, None, None, None] * base[None, :, :, :]
    return psi.astype(dtype, copy=False)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Synthesize striped seed Psi^{(0)} for Brazovskii Newton-Krylov warm-start.")
    p.add_argument("--N", type=int, required=True,
                   help="Lattice points per dimension")
    p.add_argument("--L-box", type=float, required=True,
                   help="Periodic box length")
    p.add_argument("--q0", type=float, required=True,
                   help="Brazovskii peak wavenumber")
    p.add_argument("--A0", type=float, default=1.0,
                   help="Amplitude (default 1.0 post-Math294-AddA; "
                        "robust basin entry on N=16, mu^2=-0.7. Pre-2026-05-01 "
                        "default was 0.5 which is the borderline value per "
                        "Math294 Proposition 294.3.)")
    p.add_argument("--n-comp", type=int, default=3,
                   help="Number of field components (default 3 for vector)")
    p.add_argument("--polarisation", nargs=3, type=float, default=[1.0, 0.0, 0.0],
                   help="Component-space polarisation (default [1,0,0])")
    p.add_argument("--direction", nargs=3, type=float, default=[1.0, 0.0, 0.0],
                   help="Real-space propagation direction (default [1,0,0])")
    p.add_argument("--output", required=True,
                   help="Output .npy path")
    p.add_argument("--config", default=None,
                   help="Optional JSON config; if given, q0/L_box are read "
                        "from it (overrides --q0/--L-box)")
    p.add_argument("--quiet", action="store_true",
                   help="Suppress status output")
    args = p.parse_args()

    # Optional: pull q0 / L_box from config_template_brazovskii.json
    q0 = args.q0
    L_box = args.L_box
    if args.config is not None:
        cfg_path = Path(args.config)
        if not cfg_path.exists():
            print(f"FAIL: config not found: {cfg_path}", file=sys.stderr)
            return 1
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        if "q0" in cfg:
            q0 = float(cfg["q0"])
        elif "Brazovskii" in cfg and "q0" in cfg["Brazovskii"]:
            q0 = float(cfg["Brazovskii"]["q0"])
        if "L_box" in cfg:
            L_box = float(cfg["L_box"])
        elif "lattice" in cfg and "L_box" in cfg["lattice"]:
            L_box = float(cfg["lattice"]["L_box"])

    psi = synthesize_striped_seed(
        N=args.N, L_box=L_box, q0=q0, A0=args.A0,
        n_comp=args.n_comp,
        polarisation=tuple(args.polarisation),
        direction=tuple(args.direction),
    )

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(out_path), psi)

    if not args.quiet:
        a_lat = L_box / args.N
        print("=" * 64)
        print(" Math236_seed_striped — striped Psi^{(0)} synthesised")
        print("=" * 64)
        print(f"  shape       : {psi.shape}  (n_comp={args.n_comp}, N={args.N})")
        print(f"  dtype       : {psi.dtype}")
        print(f"  L_box       : {L_box}")
        print(f"  a_lattice   : {a_lat:.6f}")
        print(f"  q0          : {q0}")
        print(f"  q0 * a      : {q0*a_lat:.6f}  (target ~ 0.42 = 2*pi/15)")
        print(f"  A0          : {args.A0}")
        print(f"  polarisation: {args.polarisation}")
        print(f"  direction   : {args.direction}")
        print(f"  ||Psi||_L2  : {float(np.sqrt((np.abs(psi)**2).sum())):.6e}")
        print(f"  output      : {out_path}")
        print("=" * 64)
        print("Pass to v25 driver via:")
        print(f"  --load-psi {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
