#!/usr/bin/env python3
# =====================================================================
# emit_Sh_psi.py v1.0
#
# Generates a Math348-family two-latitude hexagon Psi.npy in the
# (3, N, N, N) complex128 format expected by
# Math292_transverse_lanczos.py.
#
# The Math348 prismatic counter-example to BCC mean-field uniqueness
# has 12 unit vectors u_m, m=0..5, plus their antipodes:
#   u_m = (sqrt(1-h^2) cos(m*pi/3), sqrt(1-h^2) sin(m*pi/3), h)
# This generator builds a vector-valued order parameter Psi whose
# c-th component is the sum over the 12 wavevectors q0 * u_m of
# u_m^c * exp(i q0 u_m . x), then rescales to match a target RMS|Psi|
# (default 0.408, matching the operator-supplied BCC reference seed
# math236_A1p0_seeded_N32_resumed/Psi_best_F.npy).
#
# CLI:
#   python -u Codes/supplementary/emit_Sh_psi.py \
#       --N 32 --L 16.0 --h 0.3 --q0 0.6801747616 \
#       --target-rms 0.408 \
#       --output Runs/continuation/Sh_h0p3_N32_psi.npy
# =====================================================================
from __future__ import annotations
import argparse
import numpy as np
from pathlib import Path


def Sh_unit_vectors(h: float) -> np.ndarray:
    """Return the 12 antipodal unit vectors of the Math348 family at
    height h in (0, 1)."""
    a = np.sqrt(1.0 - h * h)
    upper = np.array(
        [[a * np.cos(m * np.pi / 3), a * np.sin(m * np.pi / 3), h]
         for m in range(6)],
        dtype=np.float64,
    )
    return np.vstack([upper, -upper])  # shape (12, 3)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--N", type=int, default=32,
                   help="grid resolution (default 32)")
    p.add_argument("--L", type=float, default=16.0,
                   help="box length (default 16.0)")
    p.add_argument("--h", type=float, default=0.3,
                   help="Math348 latitude parameter h in (0,1) (default 0.3)")
    p.add_argument("--q0", type=float, default=0.6801747616,
                   help="canonical Brazovskii lock momentum (default 0.6802)")
    p.add_argument("--target-rms", type=float, default=0.408,
                   help="rescale to this RMS|Psi| (default 0.408 = BCC ref)")
    p.add_argument("--output", required=True,
                   help="output .npy path")
    args = p.parse_args()

    N = args.N
    L = args.L
    q0 = args.q0
    h = args.h

    if not (0.0 < h < 1.0):
        raise SystemExit(f"[FATAL] h={h} must lie in the open interval (0,1)")

    # Spatial grid (periodic, lattice spacing L/N)
    xs = np.linspace(0.0, L, N, endpoint=False)
    X, Y, Z = np.meshgrid(xs, xs, xs, indexing="ij")
    pos = np.stack([X, Y, Z], axis=-1)  # shape (N, N, N, 3)

    # Math348 wavevectors
    units = Sh_unit_vectors(h)        # (12, 3)
    kvecs = q0 * units                # (12, 3)

    # Vector-valued Psi: c-th component = sum_m u_m^c * exp(i k_m . x)
    Psi = np.zeros((3, N, N, N), dtype=np.complex128)
    for m in range(12):
        k = kvecs[m]
        u = units[m]
        phase = np.einsum("ijkc,c->ijk", pos, k)  # (N,N,N)
        wave = np.exp(1j * phase)
        for c in range(3):
            Psi[c] += u[c] * wave

    # Rescale to target RMS|Psi|
    cur_rms = float(np.sqrt(np.mean(np.abs(Psi) ** 2)))
    if cur_rms <= 0.0:
        raise SystemExit("[FATAL] generated Psi has zero RMS; check inputs")
    Psi *= args.target_rms / cur_rms
    final_rms = float(np.sqrt(np.mean(np.abs(Psi) ** 2)))

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.save(out, Psi)

    print(f"  wrote {out}")
    print(f"  shape = {Psi.shape}  dtype = {Psi.dtype}")
    print(f"  RMS|Psi| = {final_rms:.6e} (target {args.target_rms})")
    print(f"  N = {N}  L = {L}  h = {h}  q0 = {q0}")
    print(f"  source: Math348 two-latitude hexagon, 12 wavevectors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
