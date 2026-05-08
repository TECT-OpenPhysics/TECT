#!/usr/bin/env python3
"""
compute_aBCC_continuum.py v1.1 (FIXED)

Richardson extrapolation of a_BCC(N) -> a_BCC^cont in PHYSICAL units.

Fix vs v1.0 (CRITICAL): box length L is now read from MANIFEST and
used to convert FFT lattice frequency to physical wave-vector.
v1.0 returned lattice-unit a_BCC which is dimensionally wrong for
Gate F5 evaluation.

Convention
----------
For a real-space grid with N points along each axis and physical box L:
    dx = L / N  (lattice spacing)
    k_phys[n] = 2*pi * n / L   for n = -N/2, ..., N/2-1
    np.fft.fftfreq(N) returns n/N, so k_phys = fftfreq(N) * (2*pi*N/L)
                                                = fftfreq(N) * 2*pi / dx
For BCC primitive (110) reciprocal vector: |Q_110| = 2*pi*sqrt(2) / a_BCC
  => a_BCC = 2*pi*sqrt(2) / |k_peak_phys|
Substituting k_peak_phys = (k_peak_lattice_index) * 2*pi / L:
  => a_BCC = L * sqrt(2) / k_peak_index_normalised
where k_peak_index_normalised = (n_peak_x^2 + n_peak_y^2 + n_peak_z^2)^(1/2)
(integer-index norm of the FFT bin where the peak resides).

Usage
-----
python Codes/tools/compute_aBCC_continuum.py \
    --runs Runs/.../N32_extended Runs/.../N64 Runs/.../N128 \
    --output Runs/audit/aBCC_continuum_<date>.json
    [--q0 0.6801747616]
    [--shell-width 0.15]   # fractional width around q0 for peak masking
    [--verbose]

Each run dir must contain Psi_final.npy and a MANIFEST.md / .json with
keys 'N' and 'L' (or grid + box_length).
"""
import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

try:
    import numpy as np
except ImportError:
    print("FATAL: numpy required", file=sys.stderr); sys.exit(2)


def parse_manifest(run_dir):
    md = {}
    for cand in ['MANIFEST.json', 'manifest.json', 'MANIFEST.md', 'manifest.md']:
        p = run_dir / cand
        if not p.exists():
            continue
        try:
            text = p.read_text()
            if p.suffix == '.json':
                md = json.loads(text)
            else:
                # Parse "key: value" or "key = value" lines
                for line in text.splitlines():
                    m = re.match(r'\s*([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*(\S.*?)\s*$', line)
                    if m:
                        md[m.group(1).lower()] = m.group(2)
        except Exception as e:
            print(f"  [WARN] manifest parse {p}: {e}", file=sys.stderr)
        break
    return md


def get_N_L(run_dir, psi_path, md):
    """Extract grid size N and physical box length L from manifest or psi file."""
    N, L = None, None
    for k_n in ('N', 'n', 'grid', 'lattice_size'):
        if k_n in md:
            try:
                v = md[k_n]
                if isinstance(v, str):
                    v = re.sub(r'\^.*$', '', v)  # strip "^3"
                N = int(float(v)); break
            except (ValueError, TypeError):
                continue
    for k_l in ('L', 'l', 'L_box', 'box_length', 'physical_length'):
        if k_l in md:
            try:
                L = float(md[k_l]); break
            except (ValueError, TypeError):
                continue
    if N is None and psi_path.exists():
        try:
            arr = np.load(psi_path, mmap_mode='r')
            N = int(arr.shape[-1])
        except Exception:
            pass
    return N, L


def extract_aBCC_physical(psi_path, N, L, q0_physical, shell_width=0.15, verbose=False):
    """Find FFT peak in BCC shell around q0 and convert to physical a_BCC."""
    if not psi_path.exists():
        return None, "psi_missing", None
    if N is None or L is None:
        return None, f"missing_N_or_L (N={N}, L={L})", None
    try:
        psi = np.load(psi_path)
    except Exception as e:
        return None, f"load_error:{e}", None

    # Build power spectrum
    if psi.ndim == 4:
        rho = np.sum(np.abs(psi)**2, axis=0)
    else:
        rho = np.abs(psi)**2

    if rho.shape != (N, N, N):
        return None, f"shape_mismatch (got {rho.shape}, expected ({N},{N},{N}))", None

    rho_hat = np.fft.fftn(rho)
    P = np.abs(rho_hat)**2

    # Build PHYSICAL k-magnitude grid: k_phys = 2*pi/L * (integer index in -N/2..N/2-1)
    n_arr = np.fft.fftfreq(N) * N  # gives integer indices
    NX, NY, NZ = np.meshgrid(n_arr, n_arr, n_arr, indexing='ij')
    n_norm = np.sqrt(NX**2 + NY**2 + NZ**2)
    k_phys = (2 * np.pi / L) * n_norm

    # Mask: only consider modes within shell_width of q0
    shell_lo = q0_physical * (1 - shell_width)
    shell_hi = q0_physical * (1 + shell_width)
    mask = (k_phys >= shell_lo) & (k_phys <= shell_hi)
    if not np.any(mask):
        # Fallback: any non-zero k
        mask = k_phys > q0_physical * 0.3
    P_masked = np.where(mask, P, 0.0)

    flat_idx = int(np.argmax(P_masked))
    k_peak_phys = float(k_phys.flat[flat_idx])
    n_peak = float(n_norm.flat[flat_idx])

    if k_peak_phys <= 0:
        return None, "zero_peak", None

    # BCC primitive: |Q_110| = 2*pi*sqrt(2)/a_BCC  =>  a_BCC = 2*pi*sqrt(2)/k_peak_phys
    a_BCC_phys = 2 * np.pi * np.sqrt(2) / k_peak_phys

    if verbose:
        print(f"  N={N}, L={L:.6f}: n_peak={n_peak:.3f}, k_peak_phys={k_peak_phys:.6f}, "
              f"q0={q0_physical:.6f}, a_BCC_phys={a_BCC_phys:.6f}")
    return a_BCC_phys, "fft_peak_physical", {
        'k_peak_phys': k_peak_phys,
        'n_peak_index_norm': n_peak,
        'shell_lo': shell_lo,
        'shell_hi': shell_hi,
    }


def fit_richardson(N_arr, a_arr, sigma_arr=None):
    x = 1.0 / np.array(N_arr, dtype=float)**2
    y = np.array(a_arr, dtype=float)
    w = np.ones_like(y) if sigma_arr is None else 1.0 / np.array(sigma_arr, dtype=float)**2
    X = np.vstack([np.ones_like(x), x]).T
    XTW = X.T * w[None, :]
    M = XTW @ X
    M_inv = np.linalg.inv(M)
    beta = M_inv @ (XTW @ y)
    a_cont, alpha = float(beta[0]), float(beta[1])
    sigma_a_cont = float(np.sqrt(M_inv[0, 0])) if sigma_arr is not None else 0.0
    sigma_alpha = float(np.sqrt(M_inv[1, 1])) if sigma_arr is not None else 0.0
    resid = y - X @ beta
    chi2 = float((resid * w * resid).sum())
    dof = max(len(y) - 2, 1)
    return {
        'a_cont': a_cont, 'alpha': alpha,
        'sigma_a_cont': sigma_a_cont, 'sigma_alpha': sigma_alpha,
        'chi2': chi2, 'chi2_per_dof': chi2 / dof, 'n_points': len(y),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--runs', nargs='+', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--q0', type=float, default=0.6801747616)
    p.add_argument('--shell-width', type=float, default=0.15)
    p.add_argument('--verbose', action='store_true')
    args = p.parse_args()

    print(f"=== compute_aBCC_continuum v1.1 (PHYSICAL units, L-aware) ===")
    print(f"  q0_physical = {args.q0}, shell_width = {args.shell_width}")

    per_grid = []
    for rd in args.runs:
        run_dir = Path(rd)
        if not run_dir.exists():
            print(f"  [SKIP] {rd} (not found)", file=sys.stderr); continue
        md = parse_manifest(run_dir)
        psi_path = run_dir / 'Psi_final.npy'
        N, L = get_N_L(run_dir, psi_path, md)
        a_BCC, src, dbg = extract_aBCC_physical(psi_path, N, L, args.q0, args.shell_width, args.verbose)
        if a_BCC is None:
            print(f"  [WARN] {rd}: extraction failed ({src})", file=sys.stderr); continue
        sigma = a_BCC / max(N * N, 4)
        entry = {'run_dir': str(run_dir), 'N': int(N), 'L': float(L),
                 'a_BCC_physical': float(a_BCC), 'uncertainty': float(sigma),
                 'source': src, 'debug': dbg}
        per_grid.append(entry)
        print(f"  N={N}, L={L:.4f}: a_BCC_phys = {a_BCC:.6f} (sigma={sigma:.2e}) [{src}]")

    if len(per_grid) < 2:
        print(f"FATAL: need >=2 grids, got {len(per_grid)}", file=sys.stderr); sys.exit(3)

    per_grid.sort(key=lambda d: d['N'])
    fit = fit_richardson(
        [d['N'] for d in per_grid],
        [d['a_BCC_physical'] for d in per_grid],
        [d['uncertainty'] for d in per_grid])
    a_cont, alpha = fit['a_cont'], fit['alpha']
    g1 = len(per_grid) >= 2
    g2 = fit['chi2_per_dof'] < 5.0
    g3 = abs(alpha / a_cont) < 0.5 if a_cont != 0 else False
    quality = 'PASS' if (g1 and g2 and g3) else ('MARGINAL' if g1 and (g2 or g3) else 'FAIL')

    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'tool': 'compute_aBCC_continuum.py v1.1',
        'units': 'physical (L from manifest, k_phys = 2*pi/L * n_index)',
        'q0_physical': args.q0,
        'shell_width': args.shell_width,
        'n_grids': len(per_grid),
        'per_grid': per_grid,
        'continuum': {
            'a_BCC_cont_physical': a_cont,
            'uncertainty': fit['sigma_a_cont'],
            'alpha_coeff': alpha, 'sigma_alpha': fit['sigma_alpha'],
            'chi2': fit['chi2'], 'chi2_per_dof': fit['chi2_per_dof'],
            'fit_quality': quality,
            'gates': {'G1': g1, 'G2_chi2': g2, 'G3_small_correction': g3},
        },
        'gate_F5_input': {
            'a_BCC_cont_physical': a_cont,
            'sigma': fit['sigma_a_cont'],
            'ready_for_RF5_evaluation': quality in ('PASS', 'MARGINAL'),
        },
    }
    out_path = Path(args.output); out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2))

    print(f"\n=== Continuum (PHYSICAL units) ===")
    print(f"  a_BCC^cont = {a_cont:.6f} +/- {fit['sigma_a_cont']:.2e}")
    print(f"  alpha (1/N^2 coef) = {alpha:.6f}")
    print(f"  chi^2/dof = {fit['chi2_per_dof']:.3f}, quality={quality}")
    print(f"  Output: {out_path}")
    sys.exit(0 if quality == 'PASS' else 1)


if __name__ == '__main__':
    main()
