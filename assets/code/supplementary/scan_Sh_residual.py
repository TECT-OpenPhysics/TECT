#!/usr/bin/env python3
# =====================================================================
# scan_Sh_residual.py v1.0
#
# Option 3 helper: scan multiple Sh psi variants (polarisation x
# amplitude) and report Brazovskii residual ||R[Psi]||/sqrt(dof) for
# each, identifying the variant closest to a Brazovskii fixed point.
# Uses the same backend.residual() as Math292_transverse_lanczos.py
# so results are directly comparable.
#
# CLI:
#   python -u Codes/supplementary/scan_Sh_residual.py \
#       --N 32 --L 16.0 --h 0.3 --q0 0.6801747616 \
#       --mu2 -0.7
# =====================================================================
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "Codes" / "pde"))


def Sh_units(h: float) -> np.ndarray:
    a = np.sqrt(1.0 - h * h)
    upper = np.array(
        [[a * np.cos(m * np.pi / 3), a * np.sin(m * np.pi / 3), h]
         for m in range(6)],
        dtype=np.float64,
    )
    return np.vstack([upper, -upper])  # (12, 3)


def build_grid(N: int, L: float):
    xs = np.linspace(0.0, L, N, endpoint=False)
    X, Y, Z = np.meshgrid(xs, xs, xs, indexing="ij")
    return np.stack([X, Y, Z], axis=-1)  # (N, N, N, 3)


def make_psi(units: np.ndarray, q0: float, pos: np.ndarray,
             N: int, polarisation: str, A: float) -> np.ndarray:
    """Build (3, N, N, N) complex Psi with chosen polarisation rule.

    polarisation:
      'parallel'  -- Psi^c[m] proportional to u_m^c (current default)
      'transverse-z' -- polarisation perpendicular to k, projected toward z
      'scalar-c0' -- only component 0 nonzero (scalar Sh)
      'scalar-iso' -- equal weight on all 3 components, scalar field
    """
    Psi = np.zeros((3, N, N, N), dtype=np.complex128)
    z_axis = np.array([0.0, 0.0, 1.0])
    for m in range(12):
        k = q0 * units[m]
        u = units[m]
        phase = np.einsum("ijkc,c->ijk", pos, k)
        wave = np.exp(1j * phase)

        if polarisation == "parallel":
            eps = u
        elif polarisation == "transverse-z":
            # project z_axis perpendicular to k_hat
            k_hat = u / max(np.linalg.norm(u), 1e-12)
            eps = z_axis - np.dot(z_axis, k_hat) * k_hat
            n = np.linalg.norm(eps)
            eps = eps / n if n > 1e-12 else np.array([1.0, 0.0, 0.0])
        elif polarisation == "scalar-c0":
            eps = np.array([1.0, 0.0, 0.0])
        elif polarisation == "scalar-iso":
            eps = np.array([1.0, 1.0, 1.0]) / np.sqrt(3.0)
        else:
            raise ValueError(f"unknown polarisation: {polarisation}")

        for c in range(3):
            Psi[c] += eps[c] * wave

    # rescale so RMS|Psi| == A
    cur = float(np.sqrt(np.mean(np.abs(Psi) ** 2)))
    if cur > 0:
        Psi *= A / cur
    return Psi


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--N", type=int, default=32)
    p.add_argument("--L", type=float, default=16.0)
    p.add_argument("--h", type=float, default=0.3)
    p.add_argument("--q0", type=float, default=0.6801747616)
    p.add_argument("--mu2", type=float, default=-0.7)
    p.add_argument("--config", default="Codes/pde/config_template_brazovskii.json")
    p.add_argument("--amplitudes", type=float, nargs="+",
                   default=[0.05, 0.1, 0.2, 0.408, 0.6, 1.0])
    p.add_argument("--polarisations", nargs="+",
                   default=["parallel", "transverse-z", "scalar-c0", "scalar-iso"])
    p.add_argument("--save-best", action="store_true",
                   help="save the best (lowest-residual) Psi to .npy")
    p.add_argument("--output-dir", default="Runs/continuation/Sh_scan")
    args = p.parse_args()

    # ---- import backend ----
    config_path = Path(args.config)
    if not config_path.is_file():
        config_path = REPO_ROOT / args.config
    with open(config_path, "r", encoding="utf-8") as f:
        params = json.load(f)
    backend_name = params.get("backend", "real_backend_pt_bcc_mixed_v3")
    backend = __import__(backend_name)

    L = args.L
    Y = float(params.get("Y", 1.0))
    q0 = float(params.get("q0", args.q0))
    params["N"] = args.N; params["L"] = L
    params["Lx"] = L; params["Ly"] = L; params["Lz"] = L
    params["Nx"] = args.N; params["Ny"] = args.N; params["Nz"] = args.N
    params["mu2"] = float(args.mu2)
    params["r"] = float(args.mu2 + Y * (q0 ** 4))
    params["Z"] = float(-2.0 * Y * (q0 ** 2))
    params["Y"] = Y

    # ---- scan ----
    units = Sh_units(args.h)
    pos = build_grid(args.N, L)

    print(f" scan_Sh_residual v1.0")
    print(f" N={args.N}, L={L}, h={args.h}, mu2={args.mu2}, q0={q0}")
    print(f" backend = {backend_name}")
    print(f" {'polarisation':<16} {'A':>8} {'RMS':>10} {'||R||/sqrt(dof)':>20}")
    print(" " + "-" * 60)

    best = None
    rows = []
    for pol in args.polarisations:
        for A in args.amplitudes:
            try:
                Psi = make_psi(units, q0, pos, args.N, pol, A)
                rms = float(np.sqrt(np.mean(np.abs(Psi) ** 2)))
                R = np.asarray(backend.residual(Psi, params),
                               dtype=np.complex128)
                res_norm = float(np.linalg.norm(R) / np.sqrt(Psi.size))
                rows.append((pol, A, rms, res_norm, Psi))
                print(f" {pol:<16} {A:>8.4f} {rms:>10.4e} {res_norm:>20.4e}")
                if best is None or res_norm < best[3]:
                    best = (pol, A, rms, res_norm, Psi)
            except Exception as exc:
                print(f" {pol:<16} {A:>8.4f}   FAIL: {type(exc).__name__}: {exc}")

    print()
    if best is not None:
        bp, bA, brms, bres, bPsi = best
        print(f" BEST: polarisation={bp}, A={bA:.4f}, RMS={brms:.4e}, "
              f"||R||/sqrt(dof)={bres:.4e}")
        print(f" (BCC reference for comparison: ||R||/sqrt(dof) = 9.99e-03)")

        if args.save_best:
            outdir = REPO_ROOT / args.output_dir
            outdir.mkdir(parents=True, exist_ok=True)
            tag = f"h{args.h:.2f}".replace(".", "p")
            outname = f"Sh_{tag}_N{args.N}_pol-{bp}_A{bA:.3f}.npy".replace(
                ".", "p", 2
            ).replace("ppy", ".npy")
            outpath = outdir / outname
            np.save(outpath, bPsi)
            print(f" SAVED best Psi -> {outpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
