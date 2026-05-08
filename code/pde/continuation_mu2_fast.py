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
TECT mu^2 continuation solver (fast + stable patch, v1.1)
=========================================================

Main upgrades over v1.0
-----------------------
1. Stability:
   - NaN-safe Phase-3 flip tracking
   - safer triviality test (absolute + relative RMS)
   - stronger --psi0 shape validation
   - GMRES-only default recommendation
2. Speed:
   - optional Phase-2 skipping / cadence
   - adaptive mu^2 step size
   - secant predictor from the last two successful branch points
   - local secant/bisection refinement after Delta F sign flip

Default philosophy:
- Track branch fast: Newton + Phase 3 at most points
- Run Phase 2 only occasionally
- Refine the critical mu^2 only after a bracket is found
"""

import argparse
import json
import math
import os
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Imports from the TECT solver
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tect_newton_krylov import (  # type: ignore
    newton_solve,
    build_bcc_ansatz,
    compute_energy_difference,
    lanczos_hessian,
    analyze_projected_spectrum,
    parse_L,
)
import real_backend_pt_bcc_mixed_v3 as backend  # noqa: F401  # side effects / backend registration


def kinetic_coefficients(mu2: float, Y: float, q0: float) -> Tuple[float, float]:
    """Return (r, Z) for omega(k) = r + Z k^2 + Y k^4 with shell minimum mu2."""
    r = mu2 + Y * q0**4
    Z = -2.0 * Y * q0**2
    return r, Z


def override_params(params: Dict[str, Any], mu2: float, Y: float, q0: float) -> Dict[str, Any]:
    p = dict(params)
    r, Z = kinetic_coefficients(mu2, Y, q0)
    p["mu2"] = mu2
    p["r"] = r
    p["Z"] = Z
    return p


def safe_isfinite(x: Any) -> bool:
    try:
        return bool(np.isfinite(x))
    except Exception:
        return False


def rms_amplitude(Psi: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.abs(Psi) ** 2)))


def validate_psi_shape(Psi: np.ndarray, N: int) -> Tuple[bool, str]:
    """Conservative shape validation.

    The original code assumed shape[1] == N, which is too weak. Here we accept
    arrays whose last three axes or axes 1:4 match (N, N, N), which covers the
    common (C, Nx, Ny, Nz) layout.
    """
    if not isinstance(Psi, np.ndarray):
        return False, "not a numpy array"
    if Psi.ndim < 4:
        return False, f"ndim={Psi.ndim} < 4"
    if Psi.shape[-3:] == (N, N, N):
        return True, "ok"
    if Psi.ndim >= 4 and Psi.shape[1:4] == (N, N, N):
        return True, "ok"
    return False, f"shape={Psi.shape} incompatible with requested N={N}"


def secant_predictor(
    mu_target: float,
    history: Sequence[Tuple[float, np.ndarray]],
) -> Optional[np.ndarray]:
    """Linear predictor from the last two successful nontrivial points."""
    if len(history) < 2:
        return None
    mu_prev, Psi_prev = history[-2]
    mu_last, Psi_last = history[-1]
    denom = mu_last - mu_prev
    if abs(denom) < 1e-14:
        return None
    alpha = (mu_target - mu_last) / denom
    return Psi_last + alpha * (Psi_last - Psi_prev)


def classify_trivial(
    Psi_star: np.ndarray,
    seed_rms: float,
    *,
    abs_threshold: float,
    rel_threshold: float,
) -> Tuple[bool, float]:
    """Triviality test using absolute and relative RMS thresholds."""
    rms_amp = rms_amplitude(Psi_star)
    rel = rms_amp / max(seed_rms, 1e-30)
    is_trivial = (rms_amp < abs_threshold) or (rel < rel_threshold)
    return is_trivial, rms_amp


def should_run_phase2(
    point_index: int,
    prev_valid_delta_F: Optional[float],
    *,
    phase2_cadence: int,
    near_flip_threshold: float,
) -> bool:
    if point_index == 0:
        return True
    if phase2_cadence > 0 and (point_index % phase2_cadence == 0):
        return True
    if prev_valid_delta_F is not None and safe_isfinite(prev_valid_delta_F):
        if abs(prev_valid_delta_F) <= near_flip_threshold:
            return True
    return False


def choose_point_tol(
    *,
    auto_two_stage_tol: bool,
    legacy_tol: float,
    tol_fast: float,
    tol_final: float,
    do_phase2: bool,
    prev_valid_delta_F: Optional[float],
    final_near_df: float,
    current_step: float,
    step_min: float,
) -> float:
    """Choose Newton tolerance automatically.

    Philosophy:
    - use tol_fast for cheap branch tracking
    - upgrade to tol_final near interesting/critical regions
    """
    if not auto_two_stage_tol:
        return float(legacy_tol)
    if do_phase2:
        return float(tol_final)
    if prev_valid_delta_F is not None and safe_isfinite(prev_valid_delta_F):
        if abs(float(prev_valid_delta_F)) <= float(final_near_df):
            return float(tol_final)
    if current_step <= max(1.01 * float(step_min), 2.0 * float(step_min)):
        return float(tol_final)
    return float(tol_fast)


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
    do_phase2: bool = True,
    trivial_abs: float = 1e-8,
    trivial_rel: float = 1e-3,
) -> Tuple[Dict[str, Any], np.ndarray]:
    """Run Newton solve + optional Phase 2 + Phase 3 at one mu2 value."""
    mu2 = float(params["mu2"])
    r = float(params["r"])
    seed_rms = rms_amplitude(Psi0)

    t0 = time.time()
    Psi_star, hist, projector = newton_solve(
        Psi0,
        params,
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
    grad_norm = float(last.get("grad_norm", float("nan")))
    final_F = float(last.get("F", float("nan")))
    converged = bool(safe_isfinite(grad_norm) and grad_norm < tol)

    m_star_sq = float("nan")
    if converged and do_phase2:
        try:
            evals, _ = lanczos_hessian(
                Psi_star,
                params,
                projector=projector,
                n_eigs=6,
                krylov_dim=30,
                verbose=verbose,
            )
            p2 = analyze_projected_spectrum(evals)
            m_star_sq = float(p2.m_star_sq)
        except Exception as e:  # pragma: no cover - runtime backend dependent
            if verbose:
                print(f"  [Phase 2 error] {e}")

    delta_F = float("nan")
    F_condensate = float("nan")
    F_vacuum = float("nan")
    favorable = False
    if converged:
        try:
            p3 = compute_energy_difference(Psi_star, params, verbose=verbose)
            delta_F = float(p3.delta_F)
            F_condensate = float(p3.F_condensate)
            F_vacuum = float(p3.F_vacuum)
            favorable = bool(p3.favorable_vs_vacuum)
        except Exception as e:  # pragma: no cover - runtime backend dependent
            if verbose:
                print(f"  [Phase 3 error] {e}")

    is_trivial, rms_amp = classify_trivial(
        Psi_star,
        seed_rms,
        abs_threshold=trivial_abs,
        rel_threshold=trivial_rel,
    )

    result = {
        "mu2": mu2,
        "r": r,
        "converged": converged,
        "steps": len(hist),
        "final_grad_norm": grad_norm,
        "final_F": final_F,
        "seed_rms_amplitude": seed_rms,
        "rms_amplitude": rms_amp,
        "rms_ratio_to_seed": rms_amp / max(seed_rms, 1e-30),
        "is_trivial": is_trivial,
        "m_star_sq": m_star_sq,
        "delta_F": delta_F,
        "F_condensate": F_condensate,
        "F_vacuum": F_vacuum,
        "favorable_vs_vacuum": favorable,
        "phase2_executed": bool(converged and do_phase2),
        "wall_time_s": dt_newton,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    return result, Psi_star


def interpolate_seed(Psi_lo: np.ndarray, Psi_hi: np.ndarray, t: float) -> np.ndarray:
    t = float(np.clip(t, 0.0, 1.0))
    return (1.0 - t) * Psi_lo + t * Psi_hi


def refine_critical_mu2(
    *,
    mu_lo: float,
    mu_hi: float,
    deltaF_lo: float,
    deltaF_hi: float,
    Psi_lo: np.ndarray,
    Psi_hi: np.ndarray,
    base_params: Dict[str, Any],
    Y: float,
    q0: float,
    tol: float,
    max_newton: int,
    krylov: str,
    gmres_restart: int,
    trivial_abs: float,
    trivial_rel: float,
    refine_max_iter: int,
    refine_tol_mu2: float,
    verbose: bool,
) -> Tuple[float, List[Dict[str, Any]]]:
    """Local secant/bisection refinement of Delta F = 0 after a bracket is found."""
    records: List[Dict[str, Any]] = []
    lo_mu, hi_mu = float(mu_lo), float(mu_hi)
    lo_dF, hi_dF = float(deltaF_lo), float(deltaF_hi)
    lo_Psi, hi_Psi = np.array(Psi_lo, copy=True), np.array(Psi_hi, copy=True)

    for _ in range(refine_max_iter):
        width = hi_mu - lo_mu
        if abs(width) <= refine_tol_mu2:
            break

        if safe_isfinite(lo_dF) and safe_isfinite(hi_dF) and abs(hi_dF - lo_dF) > 1e-14:
            mu_mid = hi_mu - hi_dF * (hi_mu - lo_mu) / (hi_dF - lo_dF)
            if not (lo_mu < mu_mid < hi_mu):
                mu_mid = 0.5 * (lo_mu + hi_mu)
        else:
            mu_mid = 0.5 * (lo_mu + hi_mu)

        t = (mu_mid - lo_mu) / max(hi_mu - lo_mu, 1e-30)
        Psi_seed = interpolate_seed(lo_Psi, hi_Psi, t)
        params_mid = override_params(base_params, mu_mid, Y, q0)
        result_mid, Psi_mid = run_one_point(
            Psi_seed,
            params_mid,
            tol=tol,
            max_newton=max_newton,
            krylov=krylov,
            gmres_restart=gmres_restart,
            ew=True,
            verbose=verbose,
            do_phase2=False,
            trivial_abs=trivial_abs,
            trivial_rel=trivial_rel,
        )
        records.append(result_mid)

        dF_mid = result_mid["delta_F"]
        if not (result_mid["converged"] and (not result_mid["is_trivial"]) and safe_isfinite(dF_mid)):
            mu_mid = 0.5 * (lo_mu + hi_mu)
            t = (mu_mid - lo_mu) / max(hi_mu - lo_mu, 1e-30)
            Psi_seed = interpolate_seed(lo_Psi, hi_Psi, t)
            params_mid = override_params(base_params, mu_mid, Y, q0)
            result_mid, Psi_mid = run_one_point(
                Psi_seed,
                params_mid,
                tol=tol,
                max_newton=max_newton,
                krylov=krylov,
                gmres_restart=gmres_restart,
                ew=True,
                verbose=verbose,
                do_phase2=False,
                trivial_abs=trivial_abs,
                trivial_rel=trivial_rel,
            )
            records.append(result_mid)
            dF_mid = result_mid["delta_F"]
            if not (result_mid["converged"] and (not result_mid["is_trivial"]) and safe_isfinite(dF_mid)):
                break

        if dF_mid < 0.0:
            lo_mu, lo_dF, lo_Psi = mu_mid, dF_mid, Psi_mid
        else:
            hi_mu, hi_dF, hi_Psi = mu_mid, dF_mid, Psi_mid

    if safe_isfinite(lo_dF) and safe_isfinite(hi_dF) and abs(hi_dF - lo_dF) > 1e-14:
        mu_crit = lo_mu + (hi_mu - lo_mu) * (-lo_dF) / (hi_dF - lo_dF)
    else:
        mu_crit = 0.5 * (lo_mu + hi_mu)
    return float(mu_crit), records


def format_result_line(point_number: int, result: Dict[str, Any]) -> str:
    phase2_tag = "P2" if result["phase2_executed"] else "--"
    delta_F = result["delta_F"]
    m_star_sq = result["m_star_sq"]
    return (
        f"{point_number:>3} {result['mu2']:>10.5f} {result['r']:>10.6f} "
        f"{'Y' if result['converged'] else 'N':>5} "
        f"{result['steps']:>5} "
        f"{result['rms_amplitude']:>12.6e} "
        f"{result['rms_ratio_to_seed']:>10.3e} "
        f"{'TRIV' if result['is_trivial'] else 'BCC':>8} "
        f"{m_star_sq:>12.6e} "
        f"{delta_F:>14.6e} "
        f"{'PASS' if result['favorable_vs_vacuum'] else 'FAIL':>5} "
        f"{phase2_tag:>4} "
        f"{result['wall_time_s']:>7.1f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TECT mu^2 continuation method (fast + stable)"
    )
    parser.add_argument("--config", required=True, help="Path to Brazovskii config JSON")
    parser.add_argument("--N", type=int, default=16, help="Grid dimension (default: 16)")
    parser.add_argument("--L", type=str, default="16", help="Box size, supports 'Npi' notation")
    parser.add_argument("--mu2-start", type=float, default=-1.0)
    parser.add_argument("--mu2-end", type=float, default=0.30)
    parser.add_argument("--mu2-step", type=float, default=0.05)
    parser.add_argument("--mu2-step-min", type=float, default=0.005)
    parser.add_argument("--mu2-step-max", type=float, default=None)
    parser.add_argument("--tol", type=float, default=1e-6,
                        help="Legacy single Newton tolerance (used when auto-two-stage-tol is OFF)")
    parser.add_argument("--auto-two-stage-tol", action="store_true",
                        help="Automatically use tol-fast for branch tracking and tol-final near critical/diagnostic points")
    parser.add_argument("--tol-fast", type=float, default=1e-5,
                        help="Fast Newton tolerance for routine tracking points (default: 1e-5)")
    parser.add_argument("--tol-final", type=float, default=1e-6,
                        help="Stricter Newton tolerance for near-critical/final points (default: 1e-6)")
    parser.add_argument("--tol-final-near-df", type=float, default=5e-3,
                        help="Use tol-final when previous valid |Delta F| is below this threshold (default: 5e-3)")
    parser.add_argument("--max-newton", type=int, default=50)
    parser.add_argument("--psi0", type=str, default=None)
    parser.add_argument("--outdir", type=str, default=None)
    parser.add_argument("--krylov", type=str, default="gmres", choices=["gmres", "cg"])
    parser.add_argument("--gmres-restart", type=int, default=50)
    parser.add_argument("--save-every", type=int, default=1)
    parser.add_argument("--quiet", action="store_true")

    # Speed / stability knobs
    parser.add_argument("--phase2-cadence", type=int, default=5,
                        help="Run Phase 2 every N accepted branch points (0=disable except first point)")
    parser.add_argument("--phase2-near-df", type=float, default=1e-2,
                        help="Force Phase 2 when previous valid |Delta F| is below this threshold")
    parser.add_argument("--trivial-rms-abs", type=float, default=1e-8)
    parser.add_argument("--trivial-rms-rel", type=float, default=1e-3)
    parser.add_argument("--adaptive-step", action="store_true",
                        help="Enable adaptive step sizing (recommended)")
    parser.add_argument("--step-grow", type=float, default=1.35)
    parser.add_argument("--step-shrink", type=float, default=0.5)
    parser.add_argument("--fast-step-threshold", type=int, default=5,
                        help="Grow step when Newton steps <= this")
    parser.add_argument("--slow-step-threshold", type=int, default=12,
                        help="Shrink step when Newton steps >= this")
    parser.add_argument("--refine-on-flip", action="store_true",
                        help="Refine critical mu2 after Delta F sign flip is bracketed")
    parser.add_argument("--refine-max-iter", type=int, default=8)
    parser.add_argument("--refine-tol-mu2", type=float, default=1e-3)
    parser.add_argument("--max-points", type=int, default=10000)

    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        base_params = json.load(f)

    N = args.N
    L = float(parse_L(args.L))
    Y = float(base_params.get("Y", 1.0))
    q0 = float(base_params["q0"])
    outdir = args.outdir or f"continuation_fast_stable_N{N}"
    os.makedirs(outdir, exist_ok=True)

    if args.krylov == "cg":
        print("*** WARNING: CG is kept for compatibility, but GMRES is strongly recommended for stability.")

    base_params["N"] = N
    base_params["L"] = L
    base_params["Lx"] = L
    base_params["Ly"] = L
    base_params["Lz"] = L
    base_params["Nx"] = N
    base_params["Ny"] = N
    base_params["Nz"] = N

    mu2_start = float(args.mu2_start)
    mu2_end = float(args.mu2_end)
    step0 = float(args.mu2_step)
    step_min = float(args.mu2_step_min)
    step_max = float(args.mu2_step_max) if args.mu2_step_max is not None else float(max(step0, step_min))
    current_step = step0

    r_start, _ = kinetic_coefficients(mu2_start, Y, q0)
    r_end, _ = kinetic_coefficients(mu2_end, Y, q0)
    Yq04 = Y * q0**4

    print("=" * 88)
    print("  TECT mu^2 Continuation Method (fast + stable patch)")
    print("=" * 88)
    print(f"  Config         : {args.config}")
    print(f"  Grid           : N={N}, L={L:.4f}")
    print(f"  Y={Y}, q0={q0:.10f}, Y*q0^4={Yq04:.10f}")
    print(f"  mu2 range      : [{mu2_start:.4f}, {mu2_end:.4f}]  initial step={step0:.4f}")
    print(f"  step bounds    : [{step_min:.4f}, {step_max:.4f}]")
    print(f"  r(start)       : {r_start:.10f} {'< 0 (GOOD)' if r_start < 0 else '> 0 (WARNING)'}")
    print(f"  r(end)         : {r_end:.10f}")
    if args.auto_two_stage_tol:
        print(f"  Newton tol     : auto two-stage (fast={args.tol_fast:.1e}, final={args.tol_final:.1e})")
        print(f"  Finalize near  : |Delta F| <= {args.tol_final_near_df:.1e} or Phase2/near-min-step")
    else:
        print(f"  Newton tol     : {args.tol:.1e}")
    print(f"  Max Newton     : {args.max_newton}")
    print(f"  Krylov         : {args.krylov.upper()}")
    print(f"  Phase2 cadence : {args.phase2_cadence}")
    print(f"  Adaptive step  : {'ON' if args.adaptive_step else 'OFF'}")
    print(f"  Refine on flip : {'ON' if args.refine_on_flip else 'OFF'}")
    print(f"  Outdir         : {outdir}")
    if args.psi0:
        print(f"  Initial Psi    : {args.psi0}")
    print()

    if r_start > 0 and args.psi0 is None:
        print("*** WARNING: r(start) > 0 and no external seed was provided.")
        print("*** Consider a more negative mu2_start or provide --psi0.")
        print()

    if args.psi0 is not None:
        print(f"  Loading initial Psi from: {args.psi0}")
        loaded = np.load(args.psi0)
        ok, msg = validate_psi_shape(loaded, N)
        if ok:
            Psi_current = loaded
        else:
            print(f"  *** Invalid Psi shape ({msg}). Falling back to BCC ansatz.")
            params0 = override_params(base_params, mu2_start, Y, q0)
            Psi_current = build_bcc_ansatz(N, L, params0)
    else:
        print("  Building BCC ansatz as initial seed...")
        params0 = override_params(base_params, mu2_start, Y, q0)
        Psi_current = build_bcc_ansatz(N, L, params0)

    print(f"  Initial RMS amplitude: {rms_amplitude(Psi_current):.6e}")
    print()

    all_results: List[Dict[str, Any]] = []
    refined_points: List[Dict[str, Any]] = []
    successful_history: List[Tuple[float, np.ndarray]] = []
    critical_mu2: Optional[float] = None
    prev_valid_delta_F: Optional[float] = None
    prev_valid_mu2: Optional[float] = None
    prev_valid_Psi: Optional[np.ndarray] = None

    log_path = os.path.join(outdir, "continuation_log.txt")
    json_path = os.path.join(outdir, "continuation_results.json")

    header = (
        f"{'#':>3} {'mu2':>10} {'r':>10} {'conv':>5} {'steps':>5} "
        f"{'RMS_amp':>12} {'RMS/seed':>10} {'branch':>8} {'m*^2':>12} "
        f"{'Delta_F':>14} {'fav':>5} {'P2':>4} {'time_s':>7}"
    )

    point_counter = 0
    current_mu2 = mu2_start
    t_total = time.time()

    with open(log_path, "w", encoding="utf-8") as logf:
        logf.write(header + "\n")
        logf.write("-" * len(header) + "\n")
        logf.flush()
        print(header)
        print("-" * len(header))

        while current_mu2 <= mu2_end + 1e-12 and point_counter < args.max_points:
            point_counter += 1
            params_i = override_params(base_params, current_mu2, Y, q0)

            predictor = secant_predictor(current_mu2, successful_history)
            Psi_seed = predictor if predictor is not None else Psi_current

            do_phase2 = should_run_phase2(
                len(successful_history),
                prev_valid_delta_F,
                phase2_cadence=args.phase2_cadence,
                near_flip_threshold=args.phase2_near_df,
            )

            point_tol = choose_point_tol(
                auto_two_stage_tol=args.auto_two_stage_tol,
                legacy_tol=args.tol,
                tol_fast=args.tol_fast,
                tol_final=args.tol_final,
                do_phase2=do_phase2,
                prev_valid_delta_F=prev_valid_delta_F,
                final_near_df=args.tol_final_near_df,
                current_step=current_step,
                step_min=step_min,
            )

            print(f"\n{'=' * 88}")
            print(
                f"  Point {point_counter}: mu2={current_mu2:.5f}, r={params_i['r']:.10f}, "
                f"step={current_step:.5f}, predictor={'YES' if predictor is not None else 'NO'}, "
                f"Phase2={'YES' if do_phase2 else 'NO'}, tol={point_tol:.1e}"
            )
            print(f"{'=' * 88}")


            result, Psi_star = run_one_point(
                Psi_seed,
                params_i,
                tol=point_tol,
                max_newton=args.max_newton,
                krylov=args.krylov,
                gmres_restart=args.gmres_restart,
                ew=True,
                verbose=not args.quiet,
                do_phase2=do_phase2,
                trivial_abs=args.trivial_rms_abs,
                trivial_rel=args.trivial_rms_rel,
            )

            result["newton_tol_used"] = float(point_tol)
            line = format_result_line(point_counter, result)
            print(f"\n  >> {line}")
            logf.write(line + "\n")
            logf.flush()
            all_results.append(result)

            is_branch_success = bool(result["converged"] and (not result["is_trivial"]))
            dF = result["delta_F"]
            valid_dF = bool(is_branch_success and safe_isfinite(dF))

            # Flip detection (NaN-safe)
            if (
                prev_valid_delta_F is not None
                and prev_valid_mu2 is not None
                and prev_valid_Psi is not None
                and valid_dF
                and prev_valid_delta_F < 0.0 <= dF
            ):
                if abs(dF - prev_valid_delta_F) > 1e-14:
                    critical_mu2 = prev_valid_mu2 + (current_mu2 - prev_valid_mu2) * (-prev_valid_delta_F) / (dF - prev_valid_delta_F)
                else:
                    critical_mu2 = 0.5 * (prev_valid_mu2 + current_mu2)
                print(
                    f"\n  *** PHASE 3 FLIP bracketed between mu2={prev_valid_mu2:.5f} and mu2={current_mu2:.5f}"
                )
                print(f"  *** Initial mu2_crit estimate = {critical_mu2:.6f}")

                if args.refine_on_flip:
                    mu_refined, refine_records = refine_critical_mu2(
                        mu_lo=prev_valid_mu2,
                        mu_hi=current_mu2,
                        deltaF_lo=prev_valid_delta_F,
                        deltaF_hi=dF,
                        Psi_lo=prev_valid_Psi,
                        Psi_hi=Psi_star,
                        base_params=base_params,
                        Y=Y,
                        q0=q0,
                        tol=(args.tol_final if args.auto_two_stage_tol else args.tol),
                        max_newton=args.max_newton,
                        krylov=args.krylov,
                        gmres_restart=args.gmres_restart,
                        trivial_abs=args.trivial_rms_abs,
                        trivial_rel=args.trivial_rms_rel,
                        refine_max_iter=args.refine_max_iter,
                        refine_tol_mu2=args.refine_tol_mu2,
                        verbose=not args.quiet,
                    )
                    critical_mu2 = mu_refined
                    refined_points.extend(refine_records)
                    print(f"  *** Refined mu2_crit = {critical_mu2:.6f}")

            if valid_dF:
                prev_valid_delta_F = float(dF)
                prev_valid_mu2 = current_mu2
                prev_valid_Psi = np.array(Psi_star, copy=True)

            if is_branch_success:
                Psi_current = Psi_star
                successful_history.append((current_mu2, np.array(Psi_star, copy=True)))

                if args.adaptive_step:
                    near_flip = valid_dF and abs(dF) <= args.phase2_near_df
                    if near_flip or result["steps"] >= args.slow_step_threshold:
                        current_step = max(step_min, current_step * args.step_shrink)
                    elif result["steps"] <= args.fast_step_threshold:
                        current_step = min(step_max, current_step * args.step_grow)

                current_mu2 = current_mu2 + current_step
            else:
                if args.adaptive_step and successful_history and current_step > step_min * (1.0 + 1e-12):
                    current_step = max(step_min, current_step * args.step_shrink)
                    last_good_mu2 = successful_history[-1][0]
                    current_mu2 = last_good_mu2 + current_step
                    print(
                        f"  *** Failed/trivial point. Shrinking step and retrying from last good point: "
                        f"new step={current_step:.5f}, next mu2={current_mu2:.5f}"
                    )
                else:
                    print("  *** Failed/trivial point and no further safe shrink possible. Advancing.")
                    current_mu2 = current_mu2 + current_step

            if (point_counter % args.save_every == 0) or (point_counter == 1):
                mu2_tag = f"mu2_{result['mu2']:+.5f}".replace("+", "p").replace("-", "m").replace(".", "")
                npy_path = os.path.join(outdir, f"Psi_star_{mu2_tag}.npy")
                np.save(npy_path, Psi_star)

            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(
                    {
                        "config": args.config,
                        "N": N,
                        "L": L,
                        "Y": Y,
                        "q0": q0,
                        "mu2_start": mu2_start,
                        "mu2_end": mu2_end,
                        "mu2_step_initial": step0,
                        "mu2_step_min": step_min,
                        "mu2_step_max": step_max,
                        "tol": args.tol,
                        "auto_two_stage_tol": args.auto_two_stage_tol,
                        "tol_fast": args.tol_fast,
                        "tol_final": args.tol_final,
                        "tol_final_near_df": args.tol_final_near_df,
                        "critical_mu2": critical_mu2,
                        "points": all_results,
                        "refined_points": refined_points,
                    },
                    jf,
                    indent=2,
                    allow_nan=True,
                )

            if len(all_results) >= 3:
                last3 = all_results[-3:]
                if all((not r["converged"]) or r["is_trivial"] for r in last3) and current_step <= step_min * (1.0 + 1e-12):
                    print("\n  *** 3 consecutive failed/trivial points at minimum step. Branch likely lost. Stopping.")
                    break

        dt_total = time.time() - t_total

    print(f"\n{'=' * 88}")
    print(f"  Continuation complete: {len(all_results)} points in {dt_total:.1f}s")
    print(f"{'=' * 88}")

    bcc_points = [r for r in all_results if r["converged"] and (not r["is_trivial"])]
    triv_points = [r for r in all_results if r["is_trivial"]]
    fav_points = [r for r in bcc_points if r["favorable_vs_vacuum"]]

    print(f"  BCC solutions found  : {len(bcc_points)}/{len(all_results)}")
    print(f"  Trivial solutions    : {len(triv_points)}/{len(all_results)}")
    print(f"  Favorable (DeltaF<0) : {len(fav_points)}/{len(bcc_points) if bcc_points else 0}")
    if critical_mu2 is not None:
        print(f"  Estimated mu2_crit   : {critical_mu2:.6f}")
    elif len(fav_points) == len(bcc_points) and len(bcc_points) > 0:
        print("  All BCC points favorable -- mu2_crit > mu2_end")
    elif len(fav_points) == 0 and len(bcc_points) > 0:
        print("  No favorable BCC points -- mu2_crit < mu2_start or branch is never favorable")

    print(f"\n  Results saved to: {outdir}/")
    print(f"    {json_path}")
    print(f"    {log_path}")

    with open(log_path, "a", encoding="utf-8") as logf_final:
        logf_final.write(f"\n# Total time: {dt_total:.1f}s\n")
        if critical_mu2 is not None:
            logf_final.write(f"# Estimated mu2_crit: {critical_mu2:.6f}\n")


if __name__ == "__main__":
    main()
