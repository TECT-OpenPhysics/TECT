#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v1.0
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
"""
run_audit_pipeline.py  v1.0  (2026-04-16)
=========================================

TECT Math44 / Math45 / Math46 Finite-Audit Orchestration Script.

Theory targets (Math44 / Math45):
    C3 (gauge):   c_W* = 1/(96 pi^2),  c_B* = 1/(64 pi^2)   [pass_T6_final]
    C2 (gravity): Z_h  = |Z|/2 = 0.5                         [pass_C2]

Pipeline stages
---------------
Stage 1 — Brazovskii solver at N in {32, 64, 128}
          Locked triple (mu^2, lambda, gamma) = (0.26, -0.43, +1.62)
          Init: bcc_seed (converges directly to locked BCC state)

Stage 2 — Config / metadata patch
          Injects physical_L = Lx into config.json (required by C3 extractor)
          Injects doublet_channels = [0, 1] into metadata.json
          (SU(2) generators T1/T2/T3 act on components 0 and 1)

Stage 3 — C2 extractor (math46_c2_extractor.py v0.8)
          Gravity sector: T1 (isotropy), T2 (Z_h -> 0.5), T3a (polarisation)
          Momenta: (1,0,0), (0,1,0), (0,0,1)   [IR probes, |p| << q0]

Stage 4 — C3 extractor (math46_c3_extractor.py v0.7)
          Gauge sector: T6 (c_W*, c_B*)   [allow_surrogate=True]
          Han-Avron-Saad Tr log, n_samples=32, lanczos_steps=48

Stage 5 — Combined summary -> PDE/outputs/audit_summary.json

Usage
-----
  # Background run (returns immediately; logs to outputs/audit_pipeline.log):
  nohup python3 PDE/run_audit_pipeline.py > /dev/null 2>&1 &

  # Foreground with live output (logs + prints):
  python3 PDE/run_audit_pipeline.py

  # Resume — skip stages whose output files already exist:
  python3 PDE/run_audit_pipeline.py --resume

  # Quick test on N=32 only:
  python3 PDE/run_audit_pipeline.py --grids 32 --resume

  # Only regenerate summary from existing JSON files:
  python3 PDE/run_audit_pipeline.py --only-summary

  # Check current progress / results at any time:
  python3 PDE/run_audit_pipeline.py --only-summary

Outputs
-------
  PDE/outputs/solver_N32/          locked package (Psi_corr.npy + config.json + metadata.json + ...)
  PDE/outputs/solver_N64/
  PDE/outputs/solver_N128/
  PDE/outputs/c2_audit_N32.json    C2 extractor audit result
  PDE/outputs/c2_audit_N64.json
  PDE/outputs/c2_audit_N128.json
  PDE/outputs/c3_audit_N32.json    C3 extractor audit result
  PDE/outputs/c3_audit_N64.json
  PDE/outputs/c3_audit_N128.json
  PDE/outputs/audit_summary.json   Combined pass/fail summary (human + machine readable)
  PDE/outputs/audit_pipeline.log   Timestamped per-stage log
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# =============================================================================
# Directory layout
# =============================================================================

PDE_DIR   = Path(__file__).resolve().parent
OUTPUTS   = PDE_DIR / "outputs"

SOLVER_PY = PDE_DIR / "tect_solver_pt_v3.py"
BACKEND   = PDE_DIR / "real_backend_pt_bcc_mixed_v3.py"
C2_EXT_PY = PDE_DIR / "math46_c2_extractor.py"
C3_EXT_PY = PDE_DIR / "math46_c3_extractor.py"


# =============================================================================
# Physical / numerical parameters
# =============================================================================

# EW doublet: SU(2) generators T1/T2/T3 in real_backend_pt_bcc_mixed_v3.py
# act on the (0,1) block of the 3-component field.  Channel 2 is the singlet.
DOUBLET_CHANNELS: list[int] = [0, 1]

# Per-grid solver configuration.
# Steps are scaled to give residual < 1e-8 on each grid.
# seed=1234 matches the default in tect_solver_pt_v3 for reproducibility.
SOLVER_CFG: dict[int, dict] = {
    32:  {"L": 16.0, "steps": 2000,  "seed": 1234},
    64:  {"L": 16.0, "steps": 4000,  "seed": 1234},
    128: {"L": 16.0, "steps": 8000,  "seed": 1234},
}

# C2 extractor: three axis-aligned IR momentum modes (|p| = 2pi/L << q0).
# These probe T1 (isotropy), T2 (Z_h), T3a (polarisation universality).
C2_MOMENTA: list[str] = ["1,0,0", "0,1,0", "0,0,1"]

# C3 extractor: Hutchinson-Lanczos parameters.
# n_samples=32 and lanczos_steps=48 give ~1% statistical uncertainty
# at N=32; increase for production-grade runs.
C3_N_SAMPLES:   int   = 32
C3_LANCZOS:     int   = 48
C3_AUDIT_TOL:   float = 1.0e-2

# Hard timeout per subprocess stage (seconds).
STAGE_TIMEOUT: int = 7200  # 2 hours; N=128 solver may need this


# =============================================================================
# Logging
# =============================================================================

def _setup_logging(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("audit_pipeline")
    if logger.handlers:
        return logger  # already configured (re-entrant guard)
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    return logger


# =============================================================================
# Progress tracking
# =============================================================================

def _load_progress(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_progress(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


# =============================================================================
# Stage runner
# =============================================================================

def _run_stage(
    cmd: list[str | Path],
    label: str,
    log: logging.Logger,
    sentinel: Path,
    resume: bool,
    progress: dict,
    progress_path: Path,
) -> bool:
    """Execute a subprocess stage.

    Returns True on success (or if sentinel already exists and resume=True).
    Writes progress to ``progress_path`` after each stage.
    """
    key = label.replace(" ", "_")

    if resume and sentinel.exists():
        log.info(f"SKIP   [{label}]  (sentinel exists: {sentinel.name})")
        progress[key] = "skipped"
        _save_progress(progress_path, progress)
        return True

    log.info(f"START  [{label}]")
    log.info(f"CMD    {' '.join(str(c) for c in cmd)}")
    t0 = time.monotonic()

    try:
        proc = subprocess.run(
            [str(c) for c in cmd],
            cwd=str(PDE_DIR),
            timeout=STAGE_TIMEOUT,
        )
        elapsed = time.monotonic() - t0
        if proc.returncode != 0:
            log.error(
                f"FAIL   [{label}]  returncode={proc.returncode}"
                f"  elapsed={elapsed:.1f}s"
            )
            progress[key] = f"failed (rc={proc.returncode})"
            _save_progress(progress_path, progress)
            return False
        log.info(f"DONE   [{label}]  elapsed={elapsed:.1f}s")
        progress[key] = f"done ({elapsed:.1f}s)"
        _save_progress(progress_path, progress)
        return True

    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - t0
        log.error(f"TIMEOUT [{label}]  (>{STAGE_TIMEOUT}s elapsed={elapsed:.1f}s)")
        progress[key] = "timeout"
        _save_progress(progress_path, progress)
        return False

    except Exception as exc:
        elapsed = time.monotonic() - t0
        log.error(f"ERROR  [{label}]  {exc}  elapsed={elapsed:.1f}s")
        progress[key] = f"error: {exc}"
        _save_progress(progress_path, progress)
        return False


# =============================================================================
# Stage 2: config + metadata patch
# =============================================================================

def _patch_package(solver_dir: Path, N: int, log: logging.Logger) -> bool:
    """Inject missing keys required by the extractors.

    C3 extractor needs:
      config["physical_L"]       (reads Lx from solver config)
      metadata["doublet_channels"]

    C2 extractor reads Lx directly — no patch needed.
    """
    config_path   = solver_dir / "config.json"
    metadata_path = solver_dir / "metadata.json"

    for p in (config_path, metadata_path):
        if not p.exists():
            log.error(f"PATCH  missing file: {p}")
            return False

    changed = False

    # --- config.json ---------------------------------------------------------
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if "physical_L" not in config:
        L = float(config.get("Lx", SOLVER_CFG[N]["L"]))
        config["physical_L"] = L
        changed = True
        log.info(f"PATCH  config.json: injected physical_L={L}")
    if changed:
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        changed = False

    # --- metadata.json -------------------------------------------------------
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if "doublet_channels" not in metadata:
        metadata["doublet_channels"] = DOUBLET_CHANNELS
        changed = True
        log.info(f"PATCH  metadata.json: injected doublet_channels={DOUBLET_CHANNELS}")
    if changed:
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return True


# =============================================================================
# Stage 5: summary
# =============================================================================

def _make_summary(grids: list[int], log: logging.Logger) -> dict:
    summary: dict = {
        "_schema":       "tect-audit-summary/1.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "theory_tags": {
            "c2": "Math46c-c2-extractor-v0.8-2026-04-16",
            "c3": "Math46b-c3-extractor-v0.7-2026-04-16",
        },
        "targets": {
            "Z_h":     0.5,
            "cW_star": "1/(96*pi^2)",
            "cB_star": "1/(64*pi^2)",
        },
        "grids": grids,
        "c2":     {},
        "c3":     {},
        "verdict": {},
    }

    import math
    TARGET_CW = 1.0 / (96.0 * math.pi**2)
    TARGET_CB = 1.0 / (64.0 * math.pi**2)

    for N in grids:
        c2_path = OUTPUTS / f"c2_audit_N{N}.json"
        c3_path = OUTPUTS / f"c3_audit_N{N}.json"

        # ---- C2 ----
        if c2_path.exists():
            c2 = json.loads(c2_path.read_text(encoding="utf-8"))
            agg   = c2.get("aggregate", {})
            audit = c2.get("audit", {})
            summary["c2"][N] = {
                "pass_T1":       audit.get("pass_T1"),
                "pass_T2":       audit.get("pass_T2"),
                "pass_T3a":      audit.get("pass_T3a"),
                "pass_H0":       audit.get("pass_H0"),
                "pass_C2":       audit.get("pass_C2"),
                "Z_h_fit":       agg.get("Z_h_fit"),
                "worst_iso_dev": agg.get("worst_iso_dev"),
                "worst_Z_dev":   agg.get("worst_Z_dev"),
                "audit_margin":  audit.get("audit_margin"),
            }
        else:
            summary["c2"][N] = {"status": "missing", "pass_C2": False}

        # ---- C3 ----
        if c3_path.exists():
            c3   = json.loads(c3_path.read_text(encoding="utf-8"))
            aud3 = c3.get("audit", {})
            comp = c3.get("compliance", {})
            cW_avg = aud3.get("cW_avg")
            cB     = aud3.get("cB")
            summary["c3"][N] = {
                "cW_T1":              aud3.get("cW_T1"),
                "cW_T2":              aud3.get("cW_T2"),
                "cB":                 cB,
                "cW_avg":             cW_avg,
                "cW_target":          TARGET_CW,
                "cB_target":          TARGET_CB,
                "cW_rel_err":         (abs(cW_avg - TARGET_CW) / TARGET_CW
                                       if cW_avg is not None else None),
                "cB_rel_err":         (abs(cB - TARGET_CB) / TARGET_CB
                                       if cB is not None else None),
                "pass_F1":            aud3.get("pass_F1"),
                "pass_F2":            aud3.get("pass_F2"),
                "pass_F3":            aud3.get("pass_F3"),
                "pass_positivity":    aud3.get("pass_positivity"),
                "pass_T6":            aud3.get("pass_T6"),
                "pass_frame_nonzero": aud3.get("pass_frame_nonzero"),
                "pass_T6_final":      aud3.get("pass_T6_final"),
                "uses_surrogate":     comp.get("uses_surrogate_M1M2"),
                "audit_margin":       aud3.get("audit_margin"),
            }
        else:
            summary["c3"][N] = {"status": "missing", "pass_T6_final": False}

        # ---- per-grid verdict ----
        c2_pass = bool(summary["c2"].get(N, {}).get("pass_C2", False))
        c3_pass = bool(summary["c3"].get(N, {}).get("pass_T6_final", False))
        summary["verdict"][N] = {
            "pass_C2":       c2_pass,
            "pass_T6_final": c3_pass,
            "pass_all":      c2_pass and c3_pass,
        }

    # ---- overall verdict ----
    all_grids_pass = all(
        summary["verdict"].get(N, {}).get("pass_all", False)
        for N in grids
    )
    # "pending" if some results are still missing
    any_missing = any(
        "missing" in str(summary["c2"].get(N, {}).get("status", ""))
        or "missing" in str(summary["c3"].get(N, {}).get("status", ""))
        for N in grids
    )
    summary["overall_pass"]    = all_grids_pass
    summary["overall_pending"] = any_missing

    return summary


def _print_summary_table(summary: dict, log: logging.Logger) -> None:
    log.info("")
    log.info("  ══════ TECT FINITE AUDIT SUMMARY ══════")
    log.info(f"  Generated: {summary.get('generated_utc', 'n/a')}")
    log.info("")
    log.info("  C2 (gravity sector) — target Z_h = 0.5")
    log.info("  ┌──────┬─────────┬─────────┬──────────┬─────────┬─────────────┐")
    log.info("  │  N   │ pass_T1 │ pass_T2 │ pass_T3a │ pass_C2 │   Z_h_fit   │")
    log.info("  ├──────┼─────────┼─────────┼──────────┼─────────┼─────────────┤")
    for N in sorted(summary.get("grids", [])):
        c2 = summary.get("c2", {}).get(N, {})
        def _b(v): return ("  ✓   " if v else "  ✗   ") if v is not None else "  ?   "
        Zh = c2.get("Z_h_fit")
        Zh_s = f"{Zh:+.5f}" if Zh is not None else "   n/a  "
        log.info(
            f"  │ {N:4d} │{_b(c2.get('pass_T1'))}  │{_b(c2.get('pass_T2'))}  │"
            f"{_b(c2.get('pass_T3a'))}   │{_b(c2.get('pass_C2'))}  │  {Zh_s}   │"
        )
    log.info("  └──────┴─────────┴─────────┴──────────┴─────────┴─────────────┘")
    log.info("")

    import math
    TARGET_CW = 1.0 / (96.0 * math.pi**2)
    TARGET_CB = 1.0 / (64.0 * math.pi**2)
    log.info(f"  C3 (gauge sector) — c_W* = {TARGET_CW:.6e}, c_B* = {TARGET_CB:.6e}")
    log.info("  ┌──────┬─────────────┬─────────────┬─────────────┬──────────────┐")
    log.info("  │  N   │   cW_avg    │     cB      │   pass_T6   │ pass_T6_final│")
    log.info("  ├──────┼─────────────┼─────────────┼─────────────┼──────────────┤")
    for N in sorted(summary.get("grids", [])):
        c3 = summary.get("c3", {}).get(N, {})
        cW  = c3.get("cW_avg")
        cB  = c3.get("cB")
        p6  = c3.get("pass_T6")
        p6f = c3.get("pass_T6_final")
        cW_s  = f"{cW:.6e}" if cW  is not None else "     n/a   "
        cB_s  = f"{cB:.6e}" if cB  is not None else "     n/a   "
        def _b(v): return "  ✓  " if v else ("  ✗  " if v is not None else "  ? ")
        log.info(
            f"  │ {N:4d} │ {cW_s} │ {cB_s} │{_b(p6)}      │{_b(p6f)}       │"
        )
    log.info("  └──────┴─────────────┴─────────────┴─────────────┴──────────────┘")
    log.info("")

    overall = summary.get("overall_pass", False)
    pending = summary.get("overall_pending", True)
    if pending:
        log.info("  Overall: PENDING (some grids not yet computed)")
    else:
        verdict = "PASS ✓  — Math44 Thm.cWcB + Math45 Thm.C2_Einstein confirmed" \
                  if overall else "FAIL ✗  — at least one audit test did not converge"
        log.info(f"  Overall: {verdict}")
    log.info("")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    ap = argparse.ArgumentParser(
        description="TECT Math44/45/46 finite-audit pipeline  v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--grids", type=int, nargs="+", default=[32, 64, 128],
        choices=[32, 64, 128],
        help="Grid sizes to run (default: 32 64 128)",
    )
    ap.add_argument(
        "--resume", action="store_true",
        help="Skip stages whose sentinel output files already exist",
    )
    ap.add_argument(
        "--only-summary", action="store_true",
        help="Regenerate audit_summary.json from existing JSON files; "
             "do not run any computation",
    )
    ap.add_argument(
        "--solver-steps", type=int, default=None,
        help="Override solver step counts for all grids (useful for quick tests)",
    )
    ap.add_argument(
        "--c3-n-samples", type=int, default=C3_N_SAMPLES,
        help=f"Hutchinson samples for C3 extractor (default: {C3_N_SAMPLES})",
    )
    ap.add_argument(
        "--c3-lanczos", type=int, default=C3_LANCZOS,
        help=f"Lanczos steps for C3 extractor (default: {C3_LANCZOS})",
    )
    args = ap.parse_args()

    grids = sorted(set(args.grids))

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    log = _setup_logging(OUTPUTS / "audit_pipeline.log")
    progress_path = OUTPUTS / "audit_progress.json"
    progress = _load_progress(progress_path)

    python = sys.executable

    t_pipeline_start = time.monotonic()
    log.info("═" * 72)
    log.info("TECT finite-audit pipeline  v1.0  (2026-04-16)")
    log.info(f"grids={grids}  resume={args.resume}  only_summary={args.only_summary}")
    log.info(f"python={python}")
    log.info("═" * 72)

    if args.only_summary:
        summary = _make_summary(grids, log)
        _print_summary_table(summary, log)
        out = OUTPUTS / "audit_summary.json"
        out.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
        log.info(f"Summary written → {out}")
        return

    for N in grids:
        solver_dir = OUTPUTS / f"solver_N{N}"
        psi_corr   = solver_dir / "Psi_corr.npy"
        c2_out     = OUTPUTS / f"c2_audit_N{N}.json"
        c3_out     = OUTPUTS / f"c3_audit_N{N}.json"

        sp = SOLVER_CFG[N].copy()
        if args.solver_steps is not None:
            sp["steps"] = args.solver_steps

        log.info("─" * 72)
        log.info(f"GRID  N={N}   L={sp['L']}   solver_steps={sp['steps']}")
        log.info("─" * 72)

        # ── Stage 1: Brazovskii solver ────────────────────────────────────────
        ok = _run_stage(
            cmd=[
                python, SOLVER_PY,
                "--grid",          str(N),
                "--L",             str(sp["L"]),
                "--output",        str(solver_dir),
                "--backend",       str(BACKEND),
                "--steps",         str(sp["steps"]),
                "--tol",           "1e-8",
                "--laplacian-mode","spectral",
                "--init-mode",     "bcc_seed",
                "--seed",          str(sp["seed"]),
                "--device",        "auto",
            ],
            label=f"solver N={N}",
            log=log,
            sentinel=psi_corr,
            resume=args.resume,
            progress=progress,
            progress_path=progress_path,
        )
        if not ok:
            log.error(f"  Solver failed for N={N}; skipping extractors.")
            continue

        # ── Stage 2: config + metadata patch ──────────────────────────────────
        if not _patch_package(solver_dir, N, log):
            log.error(f"  Config patch failed for N={N}; skipping extractors.")
            continue

        # ── Stage 3: C2 extractor (gravity sector) ────────────────────────────
        _run_stage(
            cmd=[
                python, C2_EXT_PY,
                "--package-root",          str(solver_dir),
                "--backend",               str(BACKEND),
                "--momenta",               *C2_MOMENTA,
                "--probe-mode",            "fourier",
                "--probe-consistency-mode","spectral",
                "--audit-tol",             "0.01",
                "--target-Zh",             "0.5",
                "--out",                   str(c2_out),
            ],
            label=f"C2 extractor N={N}",
            log=log,
            sentinel=c2_out,
            resume=args.resume,
            progress=progress,
            progress_path=progress_path,
        )

        # ── Stage 4: C3 extractor (gauge sector) ──────────────────────────────
        _run_stage(
            cmd=[
                python, C3_EXT_PY,
                "--package-root",       str(solver_dir),
                "--backend",            str(BACKEND),
                "--n-samples",          str(args.c3_n_samples),
                "--lanczos-steps",      str(args.c3_lanczos),
                "--audit-tol",          str(C3_AUDIT_TOL),
                "--allow-surrogate",           # kinetic-Laplacian M1/M2 surrogate
                "--out",                str(c3_out),
            ],
            label=f"C3 extractor N={N}",
            log=log,
            sentinel=c3_out,
            resume=args.resume,
            progress=progress,
            progress_path=progress_path,
        )

    # ── Stage 5: Summary ──────────────────────────────────────────────────────
    log.info("─" * 72)
    log.info("SUMMARY")
    log.info("─" * 72)
    summary = _make_summary(grids, log)
    _print_summary_table(summary, log)
    out = OUTPUTS / "audit_summary.json"
    out.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    log.info(f"Summary written → {out}")

    elapsed_total = time.monotonic() - t_pipeline_start
    log.info(f"Pipeline complete  total_elapsed={elapsed_total:.1f}s")
    log.info("═" * 72)


if __name__ == "__main__":
    main()
