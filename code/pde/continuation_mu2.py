#!/usr/bin/env python3
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v1.1
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
"""
TECT  mu^2 continuation solver  (v1.0)
=======================================
Strategy:
  1. Start from a very negative mu2 where r = mu2 + Y*q0^4 < 0,
     so the trivial vacuum Psi=0 is an unstable saddle point.
     The Newton solver MUST leave it and find the BCC branch.
  2. Use the converged Psi* as the initial condition for the
     next mu2 (slightly higher).
  3. March mu2 upward, tracking the nontrivial BCC branch,
     until Phase 3 flips (Delta F > 0) or mu2 reaches mu2_max.

Key advantage over sweep_mu2_phase3.py:
  - In-process (no subprocess overhead per point)
  - Psi carried in memory between steps (no disk I/O per step)
  - Much faster at N=16: ~30-60s per continuation step

Usage:
  python continuation_mu2.py --config config_template_brazovskii.json \
      --N 16 --L 16 \
      --mu2-start -1.0 --mu2-end 0.30 --mu2-step 0.05 \
      --tol 1e-6

  For finer resolution near the critical point:
  python continuation_mu2.py --config config_template_brazovskii.json \
      --N 16 --L 16 \
      --mu2-start -0.20 --mu2-end 0.10 --mu2-step 0.01 \
      --psi0 continuation_N16/Psi_star_mu2_m0.2000.npy \
      --tol 1e-6
"""

import argparse
import json
import math
import os
import sys
import time
from dataclasses import asdict
from typing import Dict, Any, Optional

import numpy as np

# ---------------------------------------------------------------------------
# Imports from the TECT solver
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tect_newton_krylov import (
    newton_solve,
    build_bcc_ansatz,
    compute_energy_difference,
    build_zero_mode_projector,
    lanczos_hessian,
    analyze_projected_spectrum,
    parse_L,
)
import real_backend_pt_bcc_mixed_v3 as backend

# v2.4 theorem-anchored thresholds (Math56-Addendum §§A-E).  Imported
# lazily so continuation keeps working if the module is missing.
try:
    from v24_thresholds import (
        BrazovskiiParams,
        brazovskii_critical_mu2,
        v24_banner,
    )
    _V24_AVAILABLE = True
except Exception:  # pragma: no cover
    _V24_AVAILABLE = False


def _v24_precheck_mu2_end(mu2_end: float, lam: float, gam: float) -> None:
    """Refuse to start continuation if mu2_end exceeds r_c^meta.

    Rationale: Math56-Addendum Theorem 1 proves there is no real BCC
    extremum for mu^2 > r_c^meta.  A continuation that terminates at such
    a mu^2 can only converge to the trivial vacuum -- exactly the failure
    mode that produced the 2026-04-20 retraction.
    """
    if not _V24_AVAILABLE:
        return
    try:
        p = BrazovskiiParams(lam=lam, gam=gam)
    except ValueError:
        return
    r_global, r_meta = brazovskii_critical_mu2(p)
    if mu2_end > r_meta:
        raise RuntimeError(
            f"[v2.4 precheck] mu2_end={mu2_end:.4e} exceeds r_c^meta="
            f"{r_meta:.4e} (= 2 lam^2/(15 gam)).  No BCC extremum exists "
            "beyond this edge; the continuation would terminate in the "
            "trivial vacuum.  Lower mu2_end (recommended 5e-3; see "
            "Docs/status/v2p4-patch-plan.md §2.2)."
        )
    if mu2_end > r_global:
        print(
            f"  *** v2.4 WARNING: mu2_end={mu2_end:.4e} > r_c^global="
            f"{r_global:.4e}.  The terminal BCC branch is only METASTABLE "
            "(F-margin negative).  Phase-3 Delta F will be positive; this "
            "is acceptable for existence checks but not for ground-state "
            "certification.  Lower mu2_end below r_c^global for a globally "
            "stable endpoint."
        )


def kinetic_coefficients(mu2: float, Y: float, q0: float):
    """Compute kinetic convention coefficients from mu2.

    Returns (r, Z) consistent with the Brazovskii dispersion:
        omega(k) = r + Z*k^2 + Y*k^4
    where omega(q0) = mu2 (shell minimum).
    """
    r = mu2 + Y * q0**4
    Z = -2.0 * Y * q0**2
    return r, Z


def override_params(params: Dict[str, Any], mu2: float,
                    Y: float, q0: float) -> Dict[str, Any]:
    """Create a copy of params with mu2/r/Z overridden."""
    p = dict(params)
    r, Z = kinetic_coefficients(mu2, Y, q0)
    p["mu2"] = mu2
    p["r"] = r
    p["Z"] = Z
    return p


def run_one_point(
    Psi0: np.ndarray,
    params: Dict[str, Any],
    *,
    tol: float = 1e-6,
    max_newton: int = 50,
    krylov: str = "gmres",
    gmres_restart: int = 50,
    ew: bool = True,
    verbose: bool = True,
):
    """Run Newton solve + Phase 2 + Phase 3 at one mu2 value.

    Returns dict with all results + converged Psi_star.
    """
    mu2 = params["mu2"]
    r = params["r"]

    t0 = time.time()
    Psi_star, hist, projector = newton_solve(
        Psi0, params,
        max_newton=max_newton,
        tol_newton=tol,
        krylov_method=krylov,
        gmres_restart=gmres_restart,
        eisenstat_walker=ew,
        ew_eta_min=0.01,
        ew_eta_max=0.9,
        include_translation_zero_modes=True,
        include_global_phase_zero_mode=False,
        verbose=verbose,
    )
    dt_newton = time.time() - t0

    last = hist[-1]
    converged = bool(last["grad_norm"] < tol)

    # Phase 2: spectral gap via Lanczos
    m_star_sq = float("nan")
    if converged:
        try:
            evals, _ = lanczos_hessian(
                Psi_star, params,
                projector=projector,
                n_eigs=6,
                krylov_dim=30,
                verbose=verbose,
            )
            p2 = analyze_projected_spectrum(evals)
            m_star_sq = p2.m_star_sq
        except Exception as e:
            if verbose:
                print(f"  [Phase 2 error] {e}")

    # Phase 3: Delta F
    delta_F = float("nan")
    F_condensate = float("nan")
    F_vacuum = float("nan")
    favorable = False
    if converged:
        try:
            p3 = compute_energy_difference(Psi_star, params, verbose=verbose)
            delta_F = p3.delta_F
            F_condensate = p3.F_condensate
            F_vacuum = p3.F_vacuum
            favorable = p3.favorable_vs_vacuum
        except Exception as e:
            if verbose:
                print(f"  [Phase 3 error] {e}")

    # Check if solution is trivial (|Psi| ~ 0)
    rms_amp = float(np.sqrt(np.mean(np.abs(Psi_star)**2)))
    is_trivial = (rms_amp < 1e-6)

    result = {
        "mu2": mu2,
        "r": r,
        "converged": converged,
        "steps": len(hist),
        "final_grad_norm": float(last["grad_norm"]),
        "final_F": float(last["F"]),
        "rms_amplitude": rms_amp,
        "is_trivial": is_trivial,
        "m_star_sq": m_star_sq,
        "delta_F": delta_F,
        "F_condensate": F_condensate,
        "F_vacuum": F_vacuum,
        "favorable_vs_vacuum": favorable,
        "wall_time_s": dt_newton,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    return result, Psi_star


def main():
    parser = argparse.ArgumentParser(
        description="TECT mu^2 continuation method -- "
                    "track the BCC branch from r<0 upward"
    )
    parser.add_argument("--config", required=True,
                        help="Path to Brazovskii config JSON")
    parser.add_argument("--N", type=int, default=16,
                        help="Grid dimension (default: 16)")
    parser.add_argument("--L", type=str, default="16",
                        help="Box size, supports 'Npi' notation (default: 16)")
    parser.add_argument("--mu2-start", type=float, default=-1.0,
                        help="Starting mu2 (should give r<0) (default: -1.0)")
    parser.add_argument("--mu2-end", type=float, default=0.30,
                        help="Ending mu2 (default: 0.30)")
    parser.add_argument("--mu2-step", type=float, default=0.05,
                        help="mu2 step size (default: 0.05)")
    parser.add_argument("--tol", type=float, default=1e-6,
                        help="Newton convergence tolerance (default: 1e-6)")
    parser.add_argument("--max-newton", type=int, default=50,
                        help="Max Newton iterations per point (default: 50)")
    parser.add_argument("--psi0", type=str, default=None,
                        help="Path to initial Psi .npy file "
                             "(overrides BCC ansatz seed)")
    parser.add_argument("--outdir", type=str, default=None,
                        help="Output directory (default: continuation_N{N})")
    parser.add_argument("--krylov", type=str, default="gmres",
                        choices=["gmres", "cg"],
                        help="Inner Krylov solver (default: gmres)")
    parser.add_argument("--gmres-restart", type=int, default=50,
                        help="GMRES restart parameter (default: 50)")
    parser.add_argument("--save-every", type=int, default=1,
                        help="Save Psi_star.npy every N points (default: 1)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress per-step solver output")

    args = parser.parse_args()

    # Load config
    with open(args.config, "r", encoding="utf-8") as f:
        base_params = json.load(f)

    N = args.N
    L = float(parse_L(args.L))
    Y = float(base_params.get("Y", 1.0))
    q0 = float(base_params["q0"])
    outdir = args.outdir or f"continuation_N{N}"
    os.makedirs(outdir, exist_ok=True)

    # Ensure grid params
    base_params["N"] = N
    base_params["L"] = L
    base_params["Lx"] = L
    base_params["Ly"] = L
    base_params["Lz"] = L
    base_params["Nx"] = N
    base_params["Ny"] = N
    base_params["Nz"] = N

    # Build mu2 schedule
    mu2_start = args.mu2_start
    mu2_end = args.mu2_end
    mu2_step = args.mu2_step
    n_points = int(round((mu2_end - mu2_start) / mu2_step)) + 1
    mu2_schedule = [mu2_start + i * mu2_step for i in range(n_points)]

    # v2.4 precheck (Math56-Addendum Theorem 1).  Raises if mu2_end is
    # beyond r_c^meta; warns if between r_c^global and r_c^meta.
    _v24_precheck_mu2_end(
        mu2_end=mu2_end,
        lam=float(base_params.get("quartic_lambda", -0.43)),
        gam=float(base_params.get("sextic_gamma", 1.62)),
    )

    # Verify starting point has r < 0
    r_start, _ = kinetic_coefficients(mu2_start, Y, q0)
    r_end, _ = kinetic_coefficients(mu2_end, Y, q0)
    Yq04 = Y * q0**4

    print("=" * 72)
    print("  TECT mu^2 Continuation Method")
    print("=" * 72)
    if _V24_AVAILABLE:
        try:
            print(v24_banner(
                mu2_target=mu2_end,
                lam=float(base_params.get("quartic_lambda", -0.43)),
                gam=float(base_params.get("sextic_gamma", 1.62)),
            ))
        except Exception as exc:  # non-fatal: banner is diagnostic only
            print(f"  [v2.4 banner skipped] {type(exc).__name__}: {exc}")
    print(f"  Config       : {args.config}")
    print(f"  Grid         : N={N}, L={L:.4f}")
    print(f"  Y={Y}, q0={q0:.10f}, Y*q0^4={Yq04:.10f}")
    print(f"  mu2 range    : [{mu2_start:.4f}, {mu2_end:.4f}]"
          f"  step={mu2_step:.4f}  ({n_points} points)")
    print(f"  r(start)     : {r_start:.10f}"
          f"  {'< 0 (unstable vacuum, GOOD)' if r_start < 0 else '> 0 (WARNING: vacuum stable!)'}")
    print(f"  r(end)       : {r_end:.10f}")
    print(f"  Newton tol   : {args.tol:.1e}")
    print(f"  Max Newton   : {args.max_newton}")
    print(f"  Krylov       : {args.krylov.upper()}")
    print(f"  Outdir       : {outdir}")
    print(f"  Save Psi     : every {args.save_every} points")
    if args.psi0:
        print(f"  Initial Psi  : {args.psi0}")
    print()

    if r_start > 0 and args.psi0 is None:
        print("  *** WARNING: r(start) > 0. The trivial vacuum is stable.")
        print("  *** The solver may converge to Psi=0 (useless).")
        print("  *** Consider using a more negative mu2_start,")
        print("  *** or provide --psi0 from a previously converged run.")
        print()

    # Initial condition
    if args.psi0 is not None:
        print(f"  Loading initial Psi from: {args.psi0}")
        Psi_current = np.load(args.psi0)
        if Psi_current.shape[1] != N:
            print(f"  *** Shape mismatch: Psi has N={Psi_current.shape[1]}"
                  f" but requested N={N}. Falling back to BCC ansatz.")
            params0 = override_params(base_params, mu2_start, Y, q0)
            Psi_current = build_bcc_ansatz(N, L, params0)
    else:
        print("  Building BCC ansatz as initial seed...")
        params0 = override_params(base_params, mu2_start, Y, q0)
        Psi_current = build_bcc_ansatz(N, L, params0)

    rms0 = float(np.sqrt(np.mean(np.abs(Psi_current)**2)))
    print(f"  Initial RMS amplitude: {rms0:.6e}")
    print()

    # Results accumulator
    all_results = []
    critical_mu2 = None
    prev_delta_F = None

    # Summary log file
    log_path = os.path.join(outdir, "continuation_log.txt")
    json_path = os.path.join(outdir, "continuation_results.json")

    with open(log_path, "w", encoding="utf-8") as logf:
        header = (f"{'#':>3} {'mu2':>8} {'r':>10} {'conv':>5} "
                  f"{'steps':>5} {'RMS_amp':>12} {'trivial':>8} "
                  f"{'m*^2':>12} {'Delta_F':>14} {'fav':>5} "
                  f"{'time_s':>7}")
        logf.write(header + "\n")
        logf.write("-" * len(header) + "\n")
        logf.flush()
        print(header)
        print("-" * len(header))

        t_total = time.time()

        for idx, mu2 in enumerate(mu2_schedule):
            params_i = override_params(base_params, mu2, Y, q0)

            print(f"\n{'='*72}")
            print(f"  Point {idx+1}/{n_points}: mu2={mu2:.4f}, "
                  f"r={params_i['r']:.10f}")
            print(f"{'='*72}")

            result, Psi_star = run_one_point(
                Psi_current, params_i,
                tol=args.tol,
                max_newton=args.max_newton,
                krylov=args.krylov,
                gmres_restart=args.gmres_restart,
                verbose=not args.quiet,
            )

            # Summary line
            line = (
                f"{idx+1:>3} {mu2:>8.4f} {result['r']:>10.6f} "
                f"{'Y' if result['converged'] else 'N':>5} "
                f"{result['steps']:>5} "
                f"{result['rms_amplitude']:>12.6e} "
                f"{'TRIV' if result['is_trivial'] else 'BCC':>8} "
                f"{result['m_star_sq']:>12.6e} "
                f"{result['delta_F']:>14.6e} "
                f"{'PASS' if result['favorable_vs_vacuum'] else 'FAIL':>5} "
                f"{result['wall_time_s']:>7.1f}"
            )
            print(f"\n  >> {line}")
            logf.write(line + "\n")
            logf.flush()

            all_results.append(result)

            # Detect Phase 3 flip
            if (prev_delta_F is not None
                    and not result['is_trivial']
                    and prev_delta_F < 0 and result['delta_F'] >= 0):
                # Crossed from favorable to unfavorable
                critical_mu2 = mu2 - mu2_step * (
                    result['delta_F'] / (result['delta_F'] - prev_delta_F))
                print(f"\n  *** PHASE 3 FLIP detected between "
                      f"mu2={mu2-mu2_step:.4f} and mu2={mu2:.4f}")
                print(f"  *** Estimated mu2_crit = {critical_mu2:.6f} "
                      f"(linear interpolation)")

            if not result['is_trivial']:
                prev_delta_F = result['delta_F']

            # Chain: use converged Psi as seed for next step
            if result['converged'] and not result['is_trivial']:
                Psi_current = Psi_star
            else:
                # If solver failed or found trivial, keep previous Psi
                print("  *** Solver found trivial/diverged. "
                      "Keeping previous Psi as seed.")

            # Save Psi_star
            if (idx + 1) % args.save_every == 0 or idx == 0:
                mu2_tag = f"mu2_{mu2:+.4f}".replace("+", "p").replace("-", "m").replace(".", "")
                npy_path = os.path.join(outdir, f"Psi_star_{mu2_tag}.npy")
                np.save(npy_path, Psi_star)

            # Incremental JSON save
            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump({
                    "config": args.config,
                    "N": N, "L": L, "Y": Y, "q0": q0,
                    "mu2_start": mu2_start, "mu2_end": mu2_end,
                    "mu2_step": mu2_step,
                    "tol": args.tol,
                    "critical_mu2": critical_mu2,
                    "points": all_results,
                }, jf, indent=2, allow_nan=True)

            # Early termination: if BCC branch lost (trivial for 3 consecutive)
            if len(all_results) >= 3:
                last3 = all_results[-3:]
                if all(r["is_trivial"] for r in last3):
                    print("\n  *** 3 consecutive trivial solutions. "
                          "BCC branch likely lost. Stopping.")
                    break

        dt_total = time.time() - t_total

        print(f"\n{'='*72}")
        print(f"  Continuation complete: {len(all_results)} points "
              f"in {dt_total:.1f}s")
        print(f"{'='*72}")

        # Summary
        bcc_points = [r for r in all_results if not r['is_trivial']]
        triv_points = [r for r in all_results if r['is_trivial']]
        fav_points = [r for r in bcc_points if r['favorable_vs_vacuum']]

        print(f"  BCC solutions found  : {len(bcc_points)}/{len(all_results)}")
        print(f"  Trivial solutions    : {len(triv_points)}/{len(all_results)}")
        print(f"  Favorable (DeltaF<0) : {len(fav_points)}/{len(bcc_points)}")

        if critical_mu2 is not None:
            print(f"  Estimated mu2_crit   : {critical_mu2:.6f}")
        elif len(fav_points) > 0 and len(fav_points) < len(bcc_points):
            # Try to find the crossing
            for i in range(1, len(bcc_points)):
                if (bcc_points[i-1]['delta_F'] < 0
                        and bcc_points[i]['delta_F'] >= 0):
                    dF0 = bcc_points[i-1]['delta_F']
                    dF1 = bcc_points[i]['delta_F']
                    mu0 = bcc_points[i-1]['mu2']
                    mu1 = bcc_points[i]['mu2']
                    critical_mu2 = mu0 + (mu1 - mu0) * (-dF0) / (dF1 - dF0)
                    print(f"  Estimated mu2_crit   : {critical_mu2:.6f}")
                    break
        elif len(fav_points) == len(bcc_points) and len(bcc_points) > 0:
            print("  All BCC points favorable -- mu2_crit > mu2_end")
            print("  Extend the range with higher mu2_end.")
        elif len(fav_points) == 0 and len(bcc_points) > 0:
            print("  No favorable points -- mu2_crit < mu2_start")
            print("  (or BCC branch is never favorable in this regime)")

        print(f"\n  Results saved to: {outdir}/")
        print(f"    {json_path}")
        print(f"    {log_path}")
        print()

    logf_final = open(log_path, "a", encoding="utf-8")
    logf_final.write(f"\n# Total time: {dt_total:.1f}s\n")
    if critical_mu2 is not None:
        logf_final.write(f"# Estimated mu2_crit: {critical_mu2:.6f}\n")
    logf_final.close()


if __name__ == "__main__":
    main()
