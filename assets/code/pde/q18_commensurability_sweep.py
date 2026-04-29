#!/usr/bin/env python3
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
q18_commensurability_sweep.py
-----------------------------
Q-2026-04-15-18 falsification protocol driver.

Sweeps the Patch-A Brazovskii solver across three grid resolutions
(fixed dk product N*dk = 2*pi*N/L preserved) and reports, for each
run, the triple

    k_min  = sqrt(-Z/(2Y))                   # kinetic minimiser
    q0_cfg = params["q0"] from config        # shell radius written at runtime
    q0_meas = argmax_k  |Psi(k)|^2 radial    # post-hoc measured peak
    |G|_1st = sqrt(2) * dk                   # BCC first-shell magnitude

Pre-registered falsification: if across {(32,10pi), (64,20pi),
(128,40pi)} the measured q0 fails to approach k_min=1.0 monotonically
(within one radial bin dk), the current (Z,Y,L) parameter choice is
falsified as a continuum-limit realisation of the Brazovskii shell.

Run:
    python PDE/q18_commensurability_sweep.py \
        --solver PDE/tect_solver_pt_v3.py \
        --backend PDE/real_backend_pt_bcc_mixed_v3.py \
        --config  PDE/config_template_brazovskii.json \
        --outdir  runs/q18_sweep_2026-04-15 \
        --steps   1500 \
        --device  auto

Author: TECT project, 2026-04-15.
Theory tag: Math39-Reorg-2026-04-15.
"""
from __future__ import annotations
import argparse
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np


# ---------- grid sweep (N, L) with preserved N/L so dk halves per step ----------
SWEEP = [
    # (N,  L,         label)
    (32,  10 * math.pi, "N32_L10pi"),
    (64,  20 * math.pi, "N64_L20pi"),
    (128, 40 * math.pi, "N128_L40pi"),
]


def run_solver(solver: Path, backend: Path, config: Path, N: int, L: float,
               out: Path, steps: int, device: str, seed: int) -> int:
    out.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, str(solver),
        "--grid", str(N),
        "--L", f"{L:.12f}",
        "--output", str(out),
        "--steps", str(steps),
        "--dt", "3e-3",
        "--save-every", str(max(steps // 5, 50)),
        "--backend", str(backend),
        "--config", str(config),
        "--seed", str(seed),
        "--device", device,
        "--laplacian-mode", "spectral",
        "--init-mode", "bcc_seed",
    ]
    print(f"[driver] spawning solver for {out.name}:\n  {' '.join(cmd)}", flush=True)
    t0 = time.time()
    rc = subprocess.call(cmd)
    print(f"[driver] solver rc={rc}  wall={time.time()-t0:.1f}s", flush=True)
    return rc


def load_final_psi(rundir: Path) -> np.ndarray:
    """
    Locate the converged field written by tect_solver_pt_v3.
    Search order (v1.1):
      1. Psi_corr.npy           (tect_solver_pt_v3.py, v3.x)   -- canonical
      2. emerge_*.npy (latest)  (legacy TECT-NPY-v1)
      3. final_Psi.npy          (legacy working branch)
    """
    if (rundir / "Psi_corr.npy").exists():
        return np.load(rundir / "Psi_corr.npy")
    finals = sorted(rundir.glob("emerge_*.npy"))
    if finals:
        return np.load(finals[-1])
    if (rundir / "final_Psi.npy").exists():
        return np.load(rundir / "final_Psi.npy")
    raise FileNotFoundError(f"no Psi field in {rundir}")


def measure_q0(Psi: np.ndarray, L: float) -> tuple[float, float, np.ndarray, np.ndarray]:
    """
    Radial power spectrum of |Psi|^2 summed over internal index.
    Returns (q0_meas, dk, k_centers, S_radial).
    Psi shape: (C, N, N, N) complex, with C in {1,2,3}.
    """
    if Psi.ndim == 3:
        Psi = Psi[None, ...]
    C, N = Psi.shape[0], Psi.shape[1]
    dk = 2.0 * math.pi / L
    # FFT per component and coherently sum |Psi_k|^2
    S = np.zeros((N, N, N), dtype=np.float64)
    for c in range(C):
        Pk = np.fft.fftn(Psi[c], norm="ortho")
        S += np.abs(Pk) ** 2
    # radial binning
    kx = np.fft.fftfreq(N, d=1.0 / N) * dk  # note: fftfreq returns cycles/sample => scale
    # Correct: fftfreq(N, d=L/N) gives cycles/length; *2pi => rad/length
    kx = 2.0 * math.pi * np.fft.fftfreq(N, d=L / N)
    KX, KY, KZ = np.meshgrid(kx, kx, kx, indexing="ij")
    Kmag = np.sqrt(KX ** 2 + KY ** 2 + KZ ** 2)
    nb = N // 2
    bins = np.linspace(0.0, Kmag.max() + 1e-12, nb + 1)
    centers = 0.5 * (bins[:-1] + bins[1:])
    idx = np.digitize(Kmag, bins) - 1
    S_rad = np.zeros(nb)
    C_rad = np.zeros(nb)
    flat_S = S.ravel(); flat_i = idx.ravel()
    for val, b in zip(flat_S, flat_i):
        if 0 <= b < nb:
            S_rad[b] += val
            C_rad[b] += 1.0
    # drop k=0 bin; take shell-mean so peak is an intensive quantity
    S_mean = np.where(C_rad > 0, S_rad / np.maximum(C_rad, 1.0), 0.0)
    S_mean[0] = 0.0
    q0_meas = float(centers[int(np.argmax(S_mean))])
    return q0_meas, dk, centers, S_mean


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solver",  required=True)
    ap.add_argument("--backend", required=True)
    ap.add_argument("--config",  required=True)
    ap.add_argument("--outdir",  required=True)
    ap.add_argument("--steps",   type=int, default=1500)
    ap.add_argument("--device",  default="auto")
    ap.add_argument("--seed",    type=int, default=17)
    ap.add_argument("--skip-solve", action="store_true",
                    help="Skip solver spawn; only re-measure q0 from existing "
                         "Psi_corr.npy in each <outdir>/<label>/ directory.")
    args = ap.parse_args()

    solver  = Path(args.solver).resolve()
    backend = Path(args.backend).resolve()
    config  = Path(args.config).resolve()
    outdir  = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    # Pull (Z,Y,q0_cfg) once from the config for reference.
    cfg = json.loads(config.read_text(encoding="utf-8"))
    Z = float(cfg.get("Z", -1.0)); Y = float(cfg.get("Y", 0.5))
    q0_cfg = float(cfg.get("q0", float("nan")))
    k_min = math.sqrt(-Z / (2.0 * Y))  # kinetic minimiser

    rows = []
    for (N, L, label) in SWEEP:
        run_out = outdir / label
        if args.skip_solve:
            print(f"[driver] --skip-solve: using existing {run_out}")
        else:
            rc = run_solver(solver, backend, config, N, L, run_out,
                            args.steps, args.device, args.seed)
            if rc != 0:
                print(f"[driver] solver failed on {label}; skipping measurement.")
                rows.append({"label": label, "N": N, "L": L, "status": "solver_fail"})
                continue

        try:
            Psi = load_final_psi(run_out)
        except FileNotFoundError as e:
            print(f"[driver] {e}")
            rows.append({"label": label, "N": N, "L": L, "status": "no_output"})
            continue

        q0_meas, dk, centers, S_rad = measure_q0(Psi, L)
        G1 = math.sqrt(2.0) * dk
        err_kmin = q0_meas - k_min
        rows.append({
            "label":     label,
            "N":         N,
            "L":         L,
            "dk":        dk,
            "k_min":     k_min,
            "q0_cfg":    q0_cfg,
            "q0_meas":   q0_meas,
            "G1_norm":   G1,
            "err_q0_minus_kmin":        err_kmin,
            "err_in_bins_of_dk":        err_kmin / dk,
            "q0_meas_nearest_shell_n":  round((q0_meas / dk) ** 2),
            "status":    "ok",
        })

        # dump shell mean for later plotting
        np.savez(run_out / "q18_radial_spectrum.npz",
                 centers=centers, S_rad=S_rad, dk=dk, q0_meas=q0_meas)

    # summary
    summary = {
        "_schema":    "tect-q18-sweep/1.0",
        "theory_tag": "Math39-Reorg-2026-04-15",
        "open_q":     "Q-2026-04-15-18",
        "Z":          Z, "Y": Y, "k_min": k_min, "q0_cfg": q0_cfg,
        "rows":       rows,
        "verdict":    _verdict(rows, k_min),
    }
    (outdir / "q18_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("\n=== Q-18 sweep summary ===")
    print(json.dumps(summary, indent=2))
    return 0


def _verdict(rows: list[dict], k_min: float) -> str:
    ok = [r for r in rows if r.get("status") == "ok"]
    if len(ok) < 2:
        return "insufficient_data"
    errs = [abs(r["err_in_bins_of_dk"]) for r in ok]
    monotone_shrink = all(errs[i + 1] <= errs[i] + 1e-9 for i in range(len(errs) - 1))
    within_one_bin_at_finest = errs[-1] <= 1.0
    if monotone_shrink and within_one_bin_at_finest:
        return "convergent_to_k_min: Q18 tentatively resolved in favour of k_min"
    if within_one_bin_at_finest and not monotone_shrink:
        return "non_monotone_but_close: inspect radial spectra manually"
    return "falsified: q0_meas does not track k_min within one bin at finest grid"


if __name__ == "__main__":
    sys.exit(main())
