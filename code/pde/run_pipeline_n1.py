#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v1.2
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
"""
run_pipeline_n1.py — TECT n*=1 WORKING pipeline on real Brazovskii data
================================================================================
STATUS:  n*=1 expectation-value extraction path (working / diagnostic).
         This is NOT the final theorem-strength certificate path.
         The final path requires:
           - n* > 1 multi-mode projector and Dirac extraction, OR
           - a rigorous proof that n*=1 expectation values are exact for the
             BCC first-shell ground state (currently an open conjecture).
         Results from this pipeline are physically meaningful and numerically
         validated, but carry the n*=1 truncation caveat.

Stages:
  0. Ψ₀ residual check (convergence sanity)
  1. U2  — Bloch linearization + spectral projector P* (n*=1)
  2. U2b — First-order Dirac coefficients (λ_∥, α, β) via expectation value
  3. U3  — Carrier audit (longitudinal + transverse certificate)
  4. U4  — Remote spectral gap audit (Level-1 linear + Level-2 numerical + Gate 1)
  5. Save — JSON summary + NPZ arrays

Usage:
  python run_pipeline_n1.py --input run_emerge_N64_s42
  python run_pipeline_n1.py --input bcc_compare/grid64_bcc --n_sample 30
  python run_pipeline_n1.py --input run_emerge_N64_s42 --output results_n1

Physical reference:
  λ_∥ = ⟨u*|M_∥|u*⟩  (longitudinal Dirac speed along G*)
  α   = ⟨u*|M_1|u*⟩  (transverse component 1)
  β   = ⟨u*|M_2|u*⟩  (transverse component 2)
  Gate 1: 𝔊₁ = Δ_bench − η_R > 0   (TECT-Math30)
  Gate 2: ∃A: ℓ_∥A > η_∥            (TECT-Math18, longitudinal carrier)
  Gate 3: ∃B: max(ℓ_IB,ℓ_JB) > η_T  (TECT-Math18, transverse carrier)
"""

import sys
import json
import math
import argparse
import traceback
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np

# ── Module imports ─────────────────────────────────────────────────────────────

sys.path.insert(0, str(Path(__file__).parent))

from transport_extractor import (
    full_stage_U2_pipeline,
    dirac_coefficients_all_patches,
    dirac_coeff_text_report,
)
from live_m_parallel import compute_live_m_parallel, write_summary as write_mpar_summary
from carrier_audit import (
    standard_carrier_basis,
    carrier_audit_all_patches,
    existence_certificate,
    carrier_audit_text_report,
    certificate_summary_latex,
    full_certificate_latex_block,
)
from remote_gap_audit import (
    full_remote_gap_audit,
    remote_gap_text_report,
    remote_gap_latex_block,
    eta_R_decomp_text_report,
    eta_R_decomp_latex_block,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def section(title: str, width: int = 72):
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)

def _js(v):
    """float → JSON-safe (NaN/Inf → None)."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return float(v) if isinstance(v, (float, np.floating)) else v


# ── Stage 0: Residual check ────────────────────────────────────────────────────

def check_residual(backend, Psi0: np.ndarray, params: dict) -> dict:
    """
    Evaluate ‖F[Ψ₀]‖ (Euler-Lagrange residual).
    A converged condensate should have ‖res‖_∞ < 1e-4 (publication: < 1e-6).
    """
    if not hasattr(backend, "residual"):
        print("[Stage 0] backend.residual not available — skipping convergence check.")
        return {"available": False}

    res = backend.residual(Psi0, params)
    inf_norm = float(np.max(np.abs(res)))
    l2_norm  = float(np.linalg.norm(res))
    rel_norm = l2_norm / max(float(np.linalg.norm(Psi0)), 1e-30)

    converged_pub   = inf_norm < 1e-6   # publication-quality
    converged_basic = inf_norm < 1e-3   # working threshold

    print(f"  ‖residual‖_∞  = {inf_norm:.6e}  "
          f"{'[pub OK]' if converged_pub else '[WARN: not pub-quality]' if converged_basic else '[FAIL: not converged]'}")
    print(f"  ‖residual‖_2  = {l2_norm:.6e}")
    print(f"  ‖residual‖_2 / ‖Ψ₀‖_2 = {rel_norm:.6e}")

    return {
        "available":       True,
        "inf_norm":        inf_norm,
        "l2_norm":         l2_norm,
        "rel_norm":        rel_norm,
        "converged_pub":   converged_pub,
        "converged_basic": converged_basic,
    }


# ── Stage 1-2: U2 + U2b ────────────────────────────────────────────────────────

def run_u2_u2b(
    Psi0: np.ndarray,
    patch_centers: np.ndarray,
    q0: float,
    hessian_fn,
    params: dict,
    *,
    n_modes: int = 1,
    dk_steps: int = 2,
    fd_order: int = 4,
    include_lowdin: bool = True,
    verbose: bool = True,
) -> dict:
    """
    U2: Bloch linearization → K_i, L(G*), P*
    U2b: Dirac coefficient extraction (λ_∥, α, β)
    Returns u2 dict with keys: transport, projector, stiffness_summary
    """
    u2 = full_stage_U2_pipeline(
        Psi0, patch_centers, q0, hessian_fn, params,
        n_modes       = n_modes,
        dk_steps      = dk_steps,
        fd_order      = fd_order,
        include_lowdin= include_lowdin,
        verbose       = verbose,
    )
    dirac = dirac_coefficients_all_patches(
        u2["transport"], u2["projector"], verbose=verbose
    )
    print()
    print(dirac_coeff_text_report(dirac))
    u2["dirac"] = dirac

    # ── Stage U2c (D5 closure, theory tag Math37-AddA-2026-04-15) ──
    # Live longitudinal-mass extractor. Computes m_parallel per patch,
    # per antipodal pair, and shell-mean, replacing the null-returning
    # deprecated/paired_basis_extractor_v2.py branch.
    try:
        pairs = _antipodal_patch_pairs(patch_centers)
        N_alpha = params.get("N_alpha") if isinstance(params, dict) else None
        theory_pred = _theory_mstar2_for_params(params)
        u2["m_parallel_live"] = compute_live_m_parallel(
            u2["transport"], pairs,
            N_alpha=N_alpha,
            theory_prediction=theory_pred,
        )
        if verbose:
            m_mean = u2["m_parallel_live"]["m_parallel_shell_mean"]
            m_std  = u2["m_parallel_live"]["m_parallel_shell_std"]
            print(f"[U2c] m_parallel (shell mean) = {m_mean:.6e}  ± {m_std:.3e}")
            cc = u2["m_parallel_live"]["consistency_check"]
            r  = cc.get("mstar2_analytic_over_numeric_corr")
            if r is not None:
                print(f"[U2c] analytic/numeric (R_patch-corrected) = {r}")
    except Exception as exc:
        eprint(f"[U2c] live_m_parallel failed: {exc}")
        u2["m_parallel_live"] = {"error": str(exc),
                                 "theory_tag": "Math37-AddA-2026-04-15"}

    return u2


# ── D5 helpers (Math37-AddA-2026-04-15) ───────────────────────────────────────

def _antipodal_patch_pairs(patch_centers) -> list:
    """Find (+G, -G) antipodal patch index pairs from patch_centers.
    Returns a list of (i, j) integer tuples, i < j."""
    centers = np.asarray(patch_centers, dtype=float)
    n = centers.shape[0]
    pairs = []
    used = set()
    for i in range(n):
        if i in used:
            continue
        ni = float(np.linalg.norm(centers[i]))
        if ni < 1e-12:
            continue
        for j in range(i + 1, n):
            if j in used:
                continue
            nj = float(np.linalg.norm(centers[j]))
            if nj < 1e-12:
                continue
            cos = float(np.dot(centers[i], centers[j]) / (ni * nj))
            if cos < -0.995:            # antipodal
                pairs.append((i, j))
                used.add(i); used.add(j)
                break
    return pairs


def _theory_mstar2_for_params(params: dict) -> dict:
    """Import extractor's analytical predictor on demand (avoid hard dep)."""
    try:
        from tect_actual_extractor_pt_v3 import compute_theory_mstar2
        return compute_theory_mstar2(params)
    except Exception:
        return {}


# ── Stage 3: U3 Carrier audit ──────────────────────────────────────────────────

def run_u3(
    u2: dict,
    *,
    threshold: float    = 0.10,
    eta_transverse: float = 0.05,
    verbose: bool = True,
) -> dict:
    """
    U3: Carrier overlap audit + existence certificate (Gates 2 & 3).
    Returns dict with audit, cert.
    """
    carriers = standard_carrier_basis()
    audit = carrier_audit_all_patches(
        u2["projector"], u2["dirac"], carriers,
        threshold      = threshold,
        eta_transverse = eta_transverse,
        verbose        = verbose,
    )
    cert = existence_certificate(
        audit,
        threshold      = threshold,
        eta_transverse = eta_transverse,
    )

    print()
    print(carrier_audit_text_report(audit))
    print()
    print(certificate_summary_latex(cert))
    print()
    print(full_certificate_latex_block(cert))

    return {"audit": audit, "cert": cert}


# ── Stage 4: U4 Remote gap audit ───────────────────────────────────────────────

def run_u4(
    Psi0: np.ndarray,
    params: dict,
    patch_centers: np.ndarray,
    q0: float,
    hessian_fn,
    u2: dict,
    *,
    r_patch_frac: float  = 0.25,
    eta_threshold: float = 0.01,
    n_sample: int        = 50,
    seed: int            = 42,
    rho_decomp: float    = 0.20,
    skip_level2: bool    = False,
    verbose: bool        = True,
) -> dict:
    """
    U4: Remote spectral gap audit.
    Level-1: analytical linear gap (full grid)
    Level-2: numerical L(k) sampling (n_sample remote k-points)
    Gate 1:  decomposition-based η_R bound
    """
    result = full_remote_gap_audit(
        Psi0, params, patch_centers, q0, hessian_fn,
        r_patch_frac      = r_patch_frac,
        eta_threshold     = eta_threshold,
        n_sample          = n_sample,
        seed              = seed,
        skip_level2       = skip_level2,
        transport_results = u2["transport"],
        proj_results      = u2["projector"],
        rho_decomp        = rho_decomp,
        verbose           = verbose,
    )

    print()
    print(remote_gap_text_report(result))
    print()
    print(remote_gap_latex_block(result))

    er = result.get("eta_R_decomp")
    if er is not None:
        print()
        print(eta_R_decomp_text_report(er))
        print()
        print(eta_R_decomp_latex_block(er))

    return result


# ── Stage 5: Save results ──────────────────────────────────────────────────────

def save_results(
    output_dir: Path,
    *,
    residual_info: dict,
    u2: dict,
    u3: dict,
    u4: dict,
    r_patch_frac: float,
    eta_threshold: float,
    params: dict,
    run_dir: Path,
    n_modes: int,
    rho_decomp: float,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    dirac    = u2["dirac"]
    cert     = u3["cert"]
    s        = u4["summary"]
    er       = u4.get("eta_R_decomp")

    # ── Patchwise arrays ──
    lambda_par = np.array([dc.lambda_par for dc in dirac])
    alpha      = np.array([dc.alpha      for dc in dirac])
    beta       = np.array([dc.beta       for dc in dirac])
    is_phys    = np.array([dc.is_physical for dc in dirac])
    extr_meth  = [dc.extraction_method   for dc in dirac]

    np.savez(
        output_dir / "pipeline_n1_arrays.npz",
        lambda_par  = lambda_par,
        alpha       = alpha,
        beta        = beta,
        is_physical = is_phys,
        patch_centers = np.array([tr.G_grid for tr in u2["transport"]]),
    )

    # ── JSON summary ──
    summary = {
        "timestamp":    datetime.now().isoformat(timespec="seconds"),
        "input_dir":    str(run_dir),
        "n_modes":        n_modes,
        "rho_decomp":     rho_decomp,
        "r_patch_frac":   r_patch_frac,
        "eta_threshold":  eta_threshold,

        "stage0_residual": {
            k: (_js(v) if not isinstance(v, bool) else v)
            for k, v in residual_info.items()
        },

        "stage_U2b_dirac": {
            "patches": [
                {
                    "patch":            dc.patch_idx,
                    "lambda_par":       _js(dc.lambda_par),
                    "alpha":            _js(dc.alpha),
                    "beta":             _js(dc.beta),
                    "lambda_par_imag":  _js(dc.lambda_par_imag),
                    "is_physical":      dc.is_physical,
                    "extraction_method": extr_meth[i],
                }
                for i, dc in enumerate(dirac)
            ],
            "lambda_par_mean":  _js(float(np.mean(lambda_par))),
            "lambda_par_std":   _js(float(np.std(lambda_par))),
            "alpha_mean":       _js(float(np.mean(alpha))),
            "beta_mean":        _js(float(np.mean(beta))),
        },

        "stage_U3_carrier": {
            "exists":            cert.exists,
            "transverse_exists": cert.transverse_exists,
            "full_certificate":  cert.full_certificate,
            "max_ell_par":       _js(cert.max_ell_par),
            "max_ell_IJ":        _js(cert.max_ell_IJ),
            "threshold":         _js(cert.threshold),
            "eta_transverse":    _js(cert.eta_transverse),
            "best_patch_long":   cert.best_patch_idx,
            "best_carrier_long": cert.best_carrier_idx,
            "best_patch_trans":  cert.best_patch_IJ,
            "best_carrier_trans": cert.best_carrier_IJ,
        },

        "stage_U4_gap": {
            "delta_lin_offshell": _js(s["delta_lin_offshell"]),
            "delta_lin_all":      _js(s["delta_lin_all"]),
            "delta_nl_sample":    _js(s["delta_nl_sample"]),
            "certificate_lin":    s.get("certificate_lin"),
            "certificate_nl":     s.get("certificate_nl"),
            "certificate":        s.get("certificate"),
            "n_remote":           s.get("n_remote"),
            "remote_fraction":    _js(s.get("remote_fraction")),
        },

        "gate1": {
            "eta_R":        _js(er.eta_R        if er else None),
            "eta_tr":       _js(er.eta_tr       if er else None),
            "eta_tail":     _js(er.eta_tail     if er else None),
            "eta_diag":     _js(er.eta_diag     if er else None),
            "delta_bench":  _js(er.delta_bench  if er else None),
            "gate1_margin": _js(er.gate1_margin if er else None),
            "gate1_pass":   (er.gate1_pass      if er else None),
            "K_offdiag":    _js(er.K_offdiag    if er else None),
            "K_tail":       _js(er.K_tail       if er else None),
        },

        "gate_summary": {
            "Gate1_pass": (er.gate1_pass if er else None),
            "Gate2_pass": cert.exists,
            "Gate3_pass": cert.transverse_exists,
            "Full_pass":  cert.full_certificate and (er.gate1_pass if er else False),
        },

        # D5 closure, theory tag Math37-AddA-2026-04-15.
        "m_parallel_live": u2.get("m_parallel_live"),
    }

    with open(output_dir / "pipeline_n1_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)

    # Standalone D5 summary (matches deprecated paired_basis_summary.json shape).
    mpar = u2.get("m_parallel_live")
    if isinstance(mpar, dict) and "m_parallel_shell_mean" in mpar:
        try:
            write_mpar_summary(output_dir, mpar)
            print(f"[save] {output_dir / 'live_m_parallel_summary.json'}")
        except Exception as _exc:
            eprint(f"[save] live_m_parallel_summary.json: {_exc}")

    print(f"\n[save] {output_dir / 'pipeline_n1_arrays.npz'}")
    print(f"[save] {output_dir / 'pipeline_n1_summary.json'}")


# ── Final gate summary printout ────────────────────────────────────────────────

def print_gate_summary(u2: dict, u3: dict, u4: dict) -> None:
    dirac = u2["dirac"]
    cert  = u3["cert"]
    er    = u4.get("eta_R_decomp")
    s     = u4["summary"]

    lambda_par_vals = [dc.lambda_par for dc in dirac]
    lam_mean = np.mean(lambda_par_vals)
    lam_std  = np.std(lambda_par_vals)

    gate1 = er.gate1_pass   if er else None
    gate2 = cert.exists
    gate3 = cert.transverse_exists
    full  = cert.full_certificate and (gate1 is True)

    print()
    print("╔" + "═"*70 + "╗")
    print("║  TECT GATE CERTIFICATE SUMMARY (n*=1, working pipeline)" + " "*13 + "║")
    print("╠" + "═"*70 + "╣")
    print(f"║  λ_∥ (mean ± std)  =  {lam_mean:+.6e}  ±  {lam_std:.2e}" + " "*20 + "║")
    print(f"║  α (mean)          =  {np.mean([dc.alpha for dc in dirac]):+.4e}" + " "*35 + "║")
    print(f"║  β (mean)          =  {np.mean([dc.beta  for dc in dirac]):+.4e}" + " "*35 + "║")
    print("╠" + "═"*70 + "╣")

    def gate_line(name, passed, detail=""):
        mark = "✅ PASS" if passed is True else ("❌ FAIL" if passed is False else "⚠  N/A ")
        line = f"║  {name:<10}  {mark}  {detail}"
        print(line + " " * max(0, 71 - len(line)) + "║")

    gate_line(
        "Gate 1",
        gate1,
        f"𝔊₁ = {er.gate1_margin:+.4e}" if er else "η_R not computed",
    )
    gate_line(
        "Gate 2",
        gate2,
        f"ℓ_∥ = {cert.max_ell_par:.4f} > {cert.threshold}",
    )
    gate_line(
        "Gate 3",
        gate3,
        f"ℓ_IJ = {cert.max_ell_IJ:.4f} > {cert.eta_transverse}",
    )
    print("╠" + "═"*70 + "╣")
    gate_line("GLOBAL", full, "Gates 1+2+3 all pass" if full else "see details above")
    print("╚" + "═"*70 + "╝")

    # LaTeX one-liner for the paper
    g1s = r"\checkmark" if gate1 is True else r"\times"
    g2s = r"\checkmark" if gate2        else r"\times"
    g3s = r"\checkmark" if gate3        else r"\times"
    print()
    print("LaTeX gate block:")
    print(r"\begin{align}")
    print(rf"  &\text{{Gate 1 (remote gap):}}\quad "
          rf"\mathfrak{{G}}_1 = {er.gate1_margin:+.4e} > 0 \quad {g1s} \\" if er else
          rf"  &\text{{Gate 1 (remote gap):}}\quad \text{{not computed}} \\")
    print(rf"  &\text{{Gate 2 (longitudinal carrier):}}\quad "
          rf"\ell_{{\parallel A}} = {cert.max_ell_par:.4f} > \eta_{{\parallel}} = {cert.threshold} \quad {g2s} \\")
    print(rf"  &\text{{Gate 3 (transverse carrier):}}\quad "
          rf"\max(\ell_{{IB}},\ell_{{JB}}) = {cert.max_ell_IJ:.4f} > \eta_T = {cert.eta_transverse} \quad {g3s}")
    print(r"\end{align}")


# ── CLI ────────────────────────────────────────────────────────────────────────

def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="TECT n*=1 WORKING pipeline (not final theorem path): "
                    "U2 → U2b → U3 → U4 on real Ψ₀"
    )
    p.add_argument("--input",   required=True,  type=str,
                   help="Input directory (contains Psi_corr.npy, config.json, patch_centers.npy)")
    p.add_argument("--backend", default="real_backend_pt_bcc_mixed_v3.py", type=str,
                   help="Backend module path (default: real_backend_pt_bcc_mixed_v3.py)")
    p.add_argument("--output",  default=None,   type=str,
                   help="Output directory (default: <input>/pipeline_n1_out)")
    p.add_argument("--n_sample", default=50, type=int,
                   help="Level-2 numerical gap sample count (default: 50)")
    p.add_argument("--rho_decomp", default=0.20, type=float,
                   help="ρ for η_R decomposition (default: 0.20)")
    p.add_argument("--seed",    default=42,  type=int,
                   help="RNG seed for Level-2 k-sampling (default: 42)")
    p.add_argument("--fd_order", default=4, type=int, choices=[2, 4],
                   help="FD order for K_i computation (default: 4)")
    p.add_argument("--dk_steps", default=2, type=int,
                   help="Richardson dk steps for FD (default: 2)")
    p.add_argument("--threshold", default=0.10, type=float,
                   help="Carrier longitudinal threshold η_∥ (default: 0.10)")
    p.add_argument("--eta_transverse", default=0.05, type=float,
                   help="Carrier transverse threshold η_T (default: 0.05)")
    p.add_argument("--r_patch_frac", default=0.80, type=float,
                   help="Patch exclusion radius as fraction of q0 (default: 0.80). "
                        "Remote mask excludes |k − G*_α| < r_patch_frac * q0. "
                        "Too small (e.g. 0.25) → remote mask covers nearly the whole "
                        "grid on N=64 BCC, inflating η_R artificially.")
    p.add_argument("--skip_level2", action="store_true",
                   help="Skip Level-2 numerical gap sampling (faster, no Gate 1)")
    p.add_argument("--quiet", action="store_true",
                   help="Suppress verbose stage output")
    return p


def main() -> None:
    parser = build_argparser()
    args   = parser.parse_args()

    run_dir    = Path(args.input).expanduser().resolve()
    backend_path = Path(args.backend).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve() if args.output \
                 else run_dir / "pipeline_n1_out"
    verbose    = not args.quiet

    # ── Load data ──────────────────────────────────────────────────────────────
    section("Loading data")
    if not run_dir.exists():
        eprint(f"ERROR: input directory not found: {run_dir}")
        sys.exit(1)

    params        = json.load(open(run_dir / "config.json", encoding="utf-8"))
    Psi0          = np.load(run_dir / "Psi_corr.npy")
    patch_centers = np.load(run_dir / "patch_centers.npy")
    q0            = float(params["q0"])

    print(f"  Input dir   : {run_dir}")
    print(f"  Output dir  : {output_dir}")
    print(f"  Ψ₀ shape    : {Psi0.shape}")
    print(f"  q₀          : {q0:.6f}")
    print(f"  N patches   : {len(patch_centers)}")
    print(f"  n_modes     : 1  (n*=1 expectation-value path)")
    print(f"  fd_order    : {args.fd_order}   dk_steps: {args.dk_steps}")
    print(f"  ρ_decomp    : {args.rho_decomp}")
    print(f"  r_patch_frac: {args.r_patch_frac}  (patch exclusion radius = {args.r_patch_frac * q0:.4f})")

    # ── Load backend ───────────────────────────────────────────────────────────
    import importlib.util
    spec = importlib.util.spec_from_file_location("_backend", backend_path)
    backend = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backend)
    hessian_fn = lambda v: backend.hessian_vec(Psi0, v, params)

    # ── Stage 0: Residual ──────────────────────────────────────────────────────
    section("Stage 0: Ψ₀ convergence check")
    residual_info = check_residual(backend, Psi0, params)

    if residual_info.get("available") and not residual_info.get("converged_basic"):
        print()
        print("  [WARN] Ψ₀ residual > 1e-3.  Results may be unreliable.")
        print("  Consider running the solver longer before re-running this pipeline.")

    # ── Stage 1-2: U2 + U2b ───────────────────────────────────────────────────
    section("Stage U2 + U2b: Bloch extraction + Dirac coefficients (n*=1)")
    u2 = run_u2_u2b(
        Psi0, patch_centers, q0, hessian_fn, params,
        n_modes       = 1,
        dk_steps      = args.dk_steps,
        fd_order      = args.fd_order,
        include_lowdin= True,
        verbose       = verbose,
    )

    # ── Stage 3: U3 ────────────────────────────────────────────────────────────
    section("Stage U3: Carrier audit (Gates 2 & 3)")
    u3 = run_u3(
        u2,
        threshold     = args.threshold,
        eta_transverse= args.eta_transverse,
        verbose       = verbose,
    )

    # ── Stage 4: U4 ────────────────────────────────────────────────────────────
    section("Stage U4: Remote spectral gap audit (Gate 1)")
    u4 = run_u4(
        Psi0, params, patch_centers, q0, hessian_fn, u2,
        r_patch_frac  = args.r_patch_frac,
        eta_threshold = 0.01,
        n_sample      = args.n_sample,
        seed          = args.seed,
        rho_decomp    = args.rho_decomp,
        skip_level2   = args.skip_level2,
        verbose       = verbose,
    )

    # ── Stage 5: Save ──────────────────────────────────────────────────────────
    section("Stage 5: Saving results")
    save_results(
        output_dir,
        residual_info = residual_info,
        u2            = u2,
        u3            = u3,
        u4            = u4,
        params        = params,
        run_dir       = run_dir,
        n_modes       = 1,
        rho_decomp    = args.rho_decomp,
        r_patch_frac  = args.r_patch_frac,
        eta_threshold = 0.01,
    )

    # ── Final gate summary ─────────────────────────────────────────────────────
    section("TECT Gate Certificate")
    print_gate_summary(u2, u3, u4)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        eprint("\n" + "=" * 72)
        eprint("PIPELINE ERROR")
        eprint("=" * 72)
        eprint(str(exc))
        traceback.print_exc()
        sys.exit(1)
