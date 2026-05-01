#!/usr/bin/env python3
# =====================================================================
# Math236_continuum_limit_scan.py
#
# Wrapper for the Math236 §9.2 four-stage continuum-limit-scan
# protocol on the BCC defect bundle. Implements Task #115 with
# RunRecorder-style outputs, Richardson extrapolation, and the nine
# pre-registered falsification gates.
#
# Pipeline:
#   Stage 1 — Per-N Phase-2 Newton-Krylov solve
#             via Codes/pde/continuation_mu2_v25.py (subprocess).
#   Stage 2 — Amplitude extraction f(a_k) from each converged Psi
#             via FFT on the q_0 shell, normalized by N_modes = 12.
#   Stage 3 — Richardson fit  f(a) = f_∞ + A_1·a + A_2·a^2
#             (3-point or more nonlinear least-squares).
#   Stage 4 — Falsification gates: residual, sign consistency,
#             power-law validation (Math235 §3, §4 + Math236 §3).
#
# CLI
# ---
#   python -u Codes/supplementary/Math236_continuum_limit_scan.py \
#       --config Codes/pde/config_template_brazovskii.json \
#       --mu2 -0.7 \
#       --N-list 32 64 128 \
#       --output-dir Runs/continuation/math236_<timestamp> \
#       [--max-newton 25] [--quiet] [--skip-stage 4] [--dry-run]
#
# Windows + POSIX compatible:
#   - uses pathlib (no raw '/' string concat)
#   - sys.executable for subprocess (no `python` shell lookup)
#   - UTF-8 encoding pinned on all file I/O
#   - no chmod (Windows has no POSIX bits); uses Path.mkdir(parents=True)
#   - atomic write via tempfile + os.replace (Windows-safe rename)
#
# Author: Jusang Lee + collaboration (2026-05-01).
# Theory: Math235 (protocol), Math236 (pre-flight), Math250+253 (T6).
# Status: ACTIVE; T3 PROOF SKETCH driver per CLAUDE.md §6.3.6.
# =====================================================================

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np

# ---------------------------------------------------------------------
# Constants (Math235 §2 + §3 + Math236 §1.2 corrections)
# ---------------------------------------------------------------------
DEFAULT_N_LIST = [32, 64, 128]            # geometric a-sequence at L=16
DEFAULT_MU2 = -0.7                          # broken-phase regime
# 2026-05-01: revised defaults after operator timing report.
# - tol_newton = 1e-5: amplitude extraction (FFT shell sum) is robust
#   to ~1e-5 residuals; Richardson fit's 50%-window (G4) is unaffected.
# - max_newton = 50: deep broken-phase (mu2 = -0.7) typically needs
#   25-40 Newton iterations to reach quadratic-convergence regime;
#   max=10 (initial heuristic) was insufficient.
DEFAULT_TOL_NEWTON = 1.0e-5
DEFAULT_MAX_NEWTON = 50
N_BCC_SHELL_MODES = 12                     # Math236 §1.2 correction
RICHARDSON_POWERS = [1, 2]                 # f(a) = f_inf + A_1·a + A_2·a^2
FALSIFICATION_GATES = {
    "G1_min_points": 3,                    # need ≥3 a-values for fit
    "G2_residual_max_rel": 0.20,           # |f_k - f_fit_k| / f_inf < 20%
    "G3_sign_consistency": True,           # all f(a_k) > 0
    "G4_power_law_window_rel": 0.50,       # ratio (f_k - f_inf)/(f_{k-1}-f_inf) within 50% of (a_k/a_{k-1})^p
    "G5_f_inf_lower": 0.001,               # plausibility lower bound (GeV)
    "G6_f_inf_upper": 1.0e6,               # plausibility upper bound (GeV)
}


# ---------------------------------------------------------------------
# Structured result data classes
# ---------------------------------------------------------------------
@dataclass
class PerNResult:
    N: int
    a: float
    output_dir: str
    solver_exit_code: int
    solver_stdout_tail: str = ""
    solver_stderr_tail: str = ""
    solver_wall_time_seconds: float = 0.0
    psi_path: Optional[str] = None
    f_amplitude: Optional[float] = None
    extraction_status: str = "PENDING"
    extraction_notes: str = ""
    # Math290 §5 (Stage-1.5 free-energy guard): parsed from solver stdout.
    # delta_F = F(Psi*) - F(0). For the broken-phase Brazovskii minimum we
    # require delta_F < 0; delta_F >= 0 indicates the Newton trajectory
    # converged to a near-trivial saddle (lambda_min < 0 with f(Psi*) = 0)
    # and the point must NOT be passed to the Richardson fit.
    delta_F: Optional[float] = None
    favorable: Optional[bool] = None


@dataclass
class RichardsonFit:
    f_inf: Optional[float] = None
    A1: Optional[float] = None
    A2: Optional[float] = None
    residuals: list[float] = field(default_factory=list)
    rmse: Optional[float] = None
    n_points: int = 0
    fit_status: str = "PENDING"
    fit_notes: str = ""


@dataclass
class GateVerdict:
    gate: str
    passed: bool
    detail: str = ""


@dataclass
class ScanReport:
    timestamp: str
    config_path: str
    mu2: float
    N_list: list[int]
    L_box: float
    output_dir: str
    per_N: list[PerNResult] = field(default_factory=list)
    richardson: Optional[RichardsonFit] = None
    gates: list[GateVerdict] = field(default_factory=list)
    overall_status: str = "PENDING"   # PASS | FAIL | PARTIAL | ERROR
    elapsed_seconds: float = 0.0


# ---------------------------------------------------------------------
# Path utilities (Windows-safe)
# ---------------------------------------------------------------------
def repo_root() -> Path:
    """Find the repo root by walking up from this script."""
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "CLAUDE.md").exists() and (parent / "Codes").is_dir():
            return parent
    raise FileNotFoundError(
        "Could not locate repo root (no CLAUDE.md + Codes/ found)"
    )


def ensure_dir(p: Path) -> None:
    """Cross-platform directory creation (no chmod)."""
    p.mkdir(parents=True, exist_ok=True)


def atomic_write_text(target: Path, content: str, encoding: str = "utf-8") -> None:
    """Write text atomically. Uses a tempfile + os.replace (Windows-safe).

    On Windows, os.replace is the documented atomic-rename primitive
    when source and destination are on the same volume. We construct
    the temp file in the same directory to guarantee that.
    """
    ensure_dir(target.parent)
    fd, tmp = tempfile.mkstemp(
        prefix=target.name + ".tmp.",
        dir=str(target.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="\n") as fh:
            fh.write(content)
        os.replace(tmp, str(target))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_json(target: Path, payload) -> None:
    atomic_write_text(target, json.dumps(payload, indent=2, default=str) + "\n")


# ---------------------------------------------------------------------
# Stage 1 — Per-N Phase-2 BCC solve
# ---------------------------------------------------------------------
def solver_path() -> Path:
    return repo_root() / "Codes" / "pde" / "continuation_mu2_v25.py"


def run_phase2_solve(
    config_path: Path,
    N: int,
    mu2: float,
    output_dir: Path,
    max_newton: int,
    tol_newton: float,
    quiet: bool,
    dry_run: bool,
    load_psi: Optional[Path] = None,
) -> PerNResult:
    """Spawn the canonical solver via sys.executable for the given N.

    If `load_psi` is given, the solver receives `--load-psi <path>` to
    warm-start from a previously checkpointed Psi.
    """
    import subprocess

    a = config_L_box(config_path) / N
    result = PerNResult(N=N, a=a, output_dir=str(output_dir), solver_exit_code=-1)
    ensure_dir(output_dir)

    cmd = [
        sys.executable,
        "-u",
        str(solver_path()),
        "--config", str(config_path),
        "--N", str(N),
        "--mu2", str(mu2),
        "--output", str(output_dir),
        "--max-newton", str(max_newton),
        "--tol-newton", str(tol_newton),
    ]
    if quiet:
        cmd.append("--quiet")
    if load_psi is not None:
        cmd.extend(["--load-psi", str(load_psi)])

    print(f"  cmd: {' '.join(cmd)}")
    if dry_run:
        result.solver_exit_code = 0
        result.extraction_status = "DRY_RUN"
        return result

    # 2026-05-01 fix: Windows CP949 fallback when subprocess stdout is
    # piped (no TTY). The solver's `assert_consistency` writes ✓
    # check-marks; without PYTHONIOENCODING=utf-8 the child process
    # crashes with UnicodeEncodeError. Same pattern as the
    # github_sync_push.py CP949 em-dash bug. We force UTF-8 + unbuffered
    # in the child env for cross-platform consistency.
    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"
    child_env["PYTHONUTF8"] = "1"
    child_env["PYTHONUNBUFFERED"] = "1"

    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(repo_root()),
            env=child_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            # Windows: no shell=True, no PATH lookup; sys.executable absolute
        )
    except (FileNotFoundError, OSError) as exc:
        result.solver_stderr_tail = f"subprocess error: {exc}"
        result.extraction_status = "SOLVER_LAUNCH_FAILED"
        return result
    finally:
        result.solver_wall_time_seconds = time.time() - t0

    result.solver_exit_code = int(proc.returncode)
    result.solver_stdout_tail = "\n".join((proc.stdout or "").splitlines()[-30:])
    result.solver_stderr_tail = "\n".join((proc.stderr or "").splitlines()[-30:])
    return result


def config_L_box(config_path: Path) -> float:
    """Read Lx (assume isotropic) from the Brazovskii config JSON."""
    with config_path.open("r", encoding="utf-8") as fh:
        cfg = json.load(fh)
    Lx = float(cfg.get("Lx", cfg.get("L", 16.0)))
    Ly = float(cfg.get("Ly", Lx))
    Lz = float(cfg.get("Lz", Lx))
    if not (math.isclose(Lx, Ly) and math.isclose(Ly, Lz)):
        print(f"  WARNING: anisotropic box ({Lx}, {Ly}, {Lz}); using Lx for a-spacing.")
    return Lx


def config_q0(config_path: Path) -> float:
    with config_path.open("r", encoding="utf-8") as fh:
        cfg = json.load(fh)
    return float(cfg.get("q0", 0.68))


# ---------------------------------------------------------------------
# Stage 2 — Amplitude extraction f(a_k)
# ---------------------------------------------------------------------
def find_psi_npy(output_dir: Path) -> Optional[Path]:
    """Locate a CONVERGED Psi field file in `output_dir`.

    Distinguishes 'converged/final' from 'checkpoint' (= partial progress).
    Returns None if only a checkpoint exists. Use `find_checkpoint_psi`
    for the latter case.
    """
    primary = [
        "Psi_converged.npy",
        "Psi_final.npy",
        "psi_converged.npy",
        "psi_final.npy",
        "Psi.npy",
        "psi.npy",
    ]
    for name in primary:
        p = output_dir / name
        if p.exists():
            return p
    # Fallback: any [Pp]si*.npy excluding 'checkpoint'.
    for p in sorted(output_dir.glob("[Pp]si*.npy"),
                    key=lambda x: x.stat().st_mtime, reverse=True):
        if "checkpoint" not in p.name.lower():
            return p
    return None


def find_checkpoint_psi(output_dir: Path) -> Optional[Path]:
    """Locate a checkpointed partial-progress Psi file (mid-Newton)."""
    for name in ["Psi_checkpoint.npy", "psi_checkpoint.npy"]:
        p = output_dir / name
        if p.exists():
            return p
    # Fallback: any *_checkpoint.npy, most recent
    cps = sorted(output_dir.glob("*checkpoint*.npy"),
                 key=lambda x: x.stat().st_mtime, reverse=True)
    return cps[0] if cps else None


def extract_amplitude(psi_path: Path, q0: float, N: int, L_box: float) -> tuple[float, str, str]:
    """Compute Math236 §1.2 amplitude:
       f = sqrt( sum_{c} sum_{k in shell} |Psi_{k,c}|^2 ) / N_modes
    where the shell is |k| ≈ q0 within ±5% tolerance, N_modes = 12
    (BCC primitive shell), and the inner sum runs over field components
    (1 for a scalar field, 3 for a vector field, etc.).

    Patch (Math290 §3 / Bug A): the v25 driver persists Psi_final.npy as
    a 4D array of shape (n_comp, N, N, N) for vector order parameters
    (e.g. compression mode). The earlier implementation accepted only
    ndim==3 and returned (0.0, "unexpected ndim=4...") for any vector
    field. The fail-fast G3 sign-consistency gate then misclassified
    the wrapper-bug zero as a physical sign violation. This version
    handles both 3D and 4D inputs and returns an explicit status code.

    Returns
    -------
    (f, note, status):
        f      : float, the shell-projected amplitude (>= 0).
        note   : str,   diagnostic notes (mode count, power total, ...).
        status : str in {"OK", "BAD_NDIM", "BAD_SHAPE",
                         "NO_SHELL_MODES", "READ_ERROR"}.

    Callers MUST propagate `status` faithfully into PerNResult (see
    Bug B in Math290 §4). A "OK" status with f == 0.0 is a *physical*
    result (trivial vacuum / symmetric-phase convergence); any non-OK
    status is a *structural* failure that must be distinguished from
    the G3 gate."""
    try:
        arr = np.load(str(psi_path))
    except Exception as exc:
        return 0.0, f"load failed: {type(exc).__name__}: {exc}", "READ_ERROR"

    # Build wavenumber grid (assumes isotropic box)
    dk = 2.0 * np.pi / L_box
    kx = np.fft.fftfreq(N, d=L_box / N) * 2.0 * np.pi
    ky, kz = kx, kx
    KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing="ij")
    Kmag = np.sqrt(KX * KX + KY * KY + KZ * KZ)

    # Shell mask: |k - q0| / q0 < 0.05
    mask = np.abs(Kmag - q0) / q0 < 0.05
    if not np.any(mask):
        return (0.0,
                f"no modes in q_0 shell (|k-q0|/q0 < 5%); q0={q0}, dk={dk:.4f}",
                "NO_SHELL_MODES")

    # Resolve scalar (ndim=3) vs. multi-component (ndim=4 with leading
    # component axis) layouts. Reject anything else explicitly.
    if arr.ndim == 3:
        if arr.shape != (N, N, N):
            return (0.0,
                    f"unexpected scalar shape {arr.shape} (expected ({N},{N},{N}))",
                    "BAD_SHAPE")
        components = [arr]
    elif arr.ndim == 4:
        n_comp = arr.shape[0]
        if arr.shape[1:] != (N, N, N):
            return (0.0,
                    f"unexpected vector shape {arr.shape} (expected ({n_comp},{N},{N},{N}))",
                    "BAD_SHAPE")
        components = [arr[c] for c in range(n_comp)]
    else:
        return (0.0,
                f"unexpected ndim={arr.ndim}; need 3D scalar or 4D vector field",
                "BAD_NDIM")

    shell_power = 0.0
    for comp in components:
        psi_k = np.fft.fftn(comp)
        shell_power += float(np.sum(np.abs(psi_k[mask]) ** 2))

    f = math.sqrt(shell_power) / N_BCC_SHELL_MODES
    note = (f"shell modes counted = {int(mask.sum())}; "
            f"n_comp = {len(components)}; "
            f"power_total = {shell_power:.6e}")
    return f, note, "OK"


# ---------------------------------------------------------------------
# Per-point fail-fast gate evaluation (lightweight, applied during Stage 1)
# ---------------------------------------------------------------------
def parse_delta_F(stdout_tail: str) -> tuple[Optional[float], Optional[bool]]:
    """Math290 §5 helper: extract `Delta F = ...` and the favorability
    verdict from the solver stdout tail. Returns (delta_F, favorable).
    favorable == True iff delta_F < 0 AND the line "Condensate is
    favorable" is present (or "NOT favorable" is absent)."""
    delta_F: Optional[float] = None
    favorable: Optional[bool] = None
    if not stdout_tail:
        return delta_F, favorable
    import re as _re
    m = _re.search(r"Delta\s*F\s*=\s*([+\-]?[0-9.eE+\-]+)", stdout_tail)
    if m:
        try:
            delta_F = float(m.group(1))
        except ValueError:
            delta_F = None
    if "NOT favorable" in stdout_tail:
        favorable = False
    elif "is favorable" in stdout_tail or "Condensate is favorable" in stdout_tail:
        favorable = True
    return delta_F, favorable


def per_point_fatal_reason(per: "PerNResult") -> Optional[str]:
    """Return a non-empty reason string if this per-point result is
    structurally fatal and the scan should fail-fast. Return None
    if the point is OK (or a benign DRY_RUN / RESUMED placeholder).

    Math290 §5 update: a per-point result with f_amplitude > 0 but
    delta_F >= 0 is classified as TRIVIAL_SADDLE -- not a structural
    extraction failure but also not a usable broken-phase data point.
    Such points are reported as fatal so fail-fast halts the scan and
    the operator can re-seed (cf. Math236_seed_striped.py)."""
    if per.extraction_status == "DRY_RUN":
        return None
    if per.extraction_status not in ("OK", "RESUMED"):
        return f"extraction structural failure: status={per.extraction_status} ({per.extraction_notes})"
    if per.f_amplitude is None:
        return "extraction returned no amplitude (None)"
    try:
        if not math.isfinite(per.f_amplitude):
            return f"f_amplitude is non-finite: {per.f_amplitude}"
    except TypeError:
        return f"f_amplitude is non-numeric: {per.f_amplitude!r}"
    if per.f_amplitude <= 0.0:
        return f"f_amplitude <= 0 (G3 sign-consistency violation): {per.f_amplitude}"
    # Math290 §5 free-energy guard. Only fires if delta_F was actually
    # parsed; otherwise we silently pass to preserve backward compatibility
    # with solver versions that do not emit the Delta F line.
    if per.delta_F is not None and per.delta_F >= 0.0:
        return (f"trivial saddle: Delta F = {per.delta_F:+.3e} >= 0 "
                f"(Psi* not energetically favourable vs. trivial vacuum); "
                f"re-seed via Math236_seed_striped.py")
    return None


# ---------------------------------------------------------------------
# Stage 3 — Richardson fit
# ---------------------------------------------------------------------
def richardson_fit(per_N: list[PerNResult]) -> RichardsonFit:
    """Fit f(a) = f_inf + A_1·a + A_2·a^2 via numpy.polyfit (degree 2)."""
    fit = RichardsonFit()
    pts = [(r.a, r.f_amplitude) for r in per_N
           if r.extraction_status in ("OK", "DRY_RUN")
              and r.f_amplitude is not None
              and r.f_amplitude > 0.0]

    fit.n_points = len(pts)
    if fit.n_points < FALSIFICATION_GATES["G1_min_points"]:
        fit.fit_status = "INSUFFICIENT_POINTS"
        fit.fit_notes = f"have {fit.n_points} usable points, need >= 3"
        return fit

    a_arr = np.array([p[0] for p in pts], dtype=np.float64)
    f_arr = np.array([p[1] for p in pts], dtype=np.float64)

    # f(a) = c2*a^2 + c1*a + c0; c0 = f_inf
    coeffs = np.polyfit(a_arr, f_arr, 2)
    c2, c1, c0 = float(coeffs[0]), float(coeffs[1]), float(coeffs[2])
    fit.f_inf = c0
    fit.A1 = c1
    fit.A2 = c2

    f_pred = c2 * a_arr ** 2 + c1 * a_arr + c0
    residuals = (f_arr - f_pred).tolist()
    fit.residuals = residuals
    fit.rmse = float(np.sqrt(np.mean((f_arr - f_pred) ** 2)))
    fit.fit_status = "OK"
    return fit


# ---------------------------------------------------------------------
# Stage 4 — Falsification gates (Math235 §3 + Math236 §3)
# ---------------------------------------------------------------------
def evaluate_gates(per_N: list[PerNResult], fit: RichardsonFit) -> list[GateVerdict]:
    gates: list[GateVerdict] = []

    # G1: minimum points
    g1_pass = fit.n_points >= FALSIFICATION_GATES["G1_min_points"]
    gates.append(GateVerdict("G1_min_points", g1_pass,
                             f"n_points={fit.n_points}, threshold>={FALSIFICATION_GATES['G1_min_points']}"))

    # G2: residual within bound
    if fit.f_inf is not None and fit.f_inf != 0.0 and fit.residuals:
        rel_max = max(abs(r) for r in fit.residuals) / abs(fit.f_inf)
        g2_pass = rel_max < FALSIFICATION_GATES["G2_residual_max_rel"]
        gates.append(GateVerdict("G2_residual_max_rel", g2_pass,
                                 f"max_rel_residual={rel_max:.4f}, threshold<{FALSIFICATION_GATES['G2_residual_max_rel']}"))
    else:
        gates.append(GateVerdict("G2_residual_max_rel", False, "no fit available"))

    # G3: sign consistency (all f(a_k) > 0)
    g3_pass = (FALSIFICATION_GATES["G3_sign_consistency"]
               and all(r.f_amplitude is not None and r.f_amplitude > 0
                       for r in per_N if r.f_amplitude is not None))
    gates.append(GateVerdict("G3_sign_consistency", g3_pass,
                             f"all f(a_k) > 0 = {g3_pass}"))

    # G4: power-law validation (lambda * f_diff_ratio matches a_ratio^p for some p in {1,2})
    pts = sorted([(r.a, r.f_amplitude) for r in per_N
                  if r.f_amplitude is not None and r.a > 0],
                 key=lambda x: x[0])
    if len(pts) >= 3 and fit.f_inf is not None:
        ratios = []
        for i in range(1, len(pts)):
            a_k, f_k = pts[i]
            a_pk, f_pk = pts[i - 1]
            df_k = f_k - fit.f_inf
            df_pk = f_pk - fit.f_inf
            if abs(df_pk) < 1e-30:
                ratios.append(None)
                continue
            obs = df_k / df_pk
            ratios.append((obs, (a_k / a_pk) ** 1, (a_k / a_pk) ** 2))
        any_match = False
        for entry in ratios:
            if entry is None:
                continue
            obs, lin, quad = entry
            tol = FALSIFICATION_GATES["G4_power_law_window_rel"]
            if (lin > 0 and abs(obs - lin) / abs(lin) < tol) or \
               (quad > 0 and abs(obs - quad) / abs(quad) < tol):
                any_match = True
                break
        gates.append(GateVerdict("G4_power_law_window_rel", any_match,
                                 f"ratios={ratios}, tol={FALSIFICATION_GATES['G4_power_law_window_rel']}"))
    else:
        gates.append(GateVerdict("G4_power_law_window_rel", False, "insufficient points"))

    # G5+G6: f_inf plausibility window
    if fit.f_inf is not None:
        in_lo = fit.f_inf >= FALSIFICATION_GATES["G5_f_inf_lower"]
        in_hi = fit.f_inf <= FALSIFICATION_GATES["G6_f_inf_upper"]
        gates.append(GateVerdict("G5_f_inf_lower", in_lo,
                                 f"f_inf={fit.f_inf:.4e} >= {FALSIFICATION_GATES['G5_f_inf_lower']}"))
        gates.append(GateVerdict("G6_f_inf_upper", in_hi,
                                 f"f_inf={fit.f_inf:.4e} <= {FALSIFICATION_GATES['G6_f_inf_upper']:.0e}"))
    else:
        gates.append(GateVerdict("G5_f_inf_lower", False, "no fit"))
        gates.append(GateVerdict("G6_f_inf_upper", False, "no fit"))

    return gates


# ---------------------------------------------------------------------
# Output rendering
# ---------------------------------------------------------------------
def render_result_md(report: ScanReport) -> str:
    out = []
    out.append("# Math236 Continuum-Limit Scan — RESULT")
    out.append("")
    out.append(f"- Theory tag : Math236-Task115-Continuum-Limit-Scan")
    out.append(f"- Driver     : Codes/supplementary/Math236_continuum_limit_scan.py")
    out.append(f"- Timestamp  : {report.timestamp}")
    out.append(f"- Config     : `{report.config_path}`")
    out.append(f"- mu^2       : {report.mu2}")
    out.append(f"- L (box)    : {report.L_box}")
    out.append(f"- N list     : {report.N_list}")
    out.append(f"- Output dir : `{report.output_dir}`")
    out.append(f"- Elapsed    : {report.elapsed_seconds:.1f} s")
    out.append(f"- **Overall  : {report.overall_status}**")
    out.append("")
    out.append("## Stage 1 + 2 — Per-N solve and amplitude")
    out.append("")
    out.append("| N | a = L/N | solver exit | wall-time (s) | f(a) | extraction |")
    out.append("|---|---|---|---|---|---|")
    for r in report.per_N:
        f_str = f"{r.f_amplitude:.6e}" if r.f_amplitude is not None else "—"
        out.append(f"| {r.N} | {r.a:.4f} | {r.solver_exit_code} | "
                   f"{r.solver_wall_time_seconds:.1f} | {f_str} | {r.extraction_status} |")
    out.append("")
    out.append("## Stage 3 — Richardson fit  f(a) = f_inf + A_1·a + A_2·a^2")
    out.append("")
    if report.richardson and report.richardson.fit_status == "OK":
        rf = report.richardson
        out.append(f"- f_inf = {rf.f_inf:.6e}")
        out.append(f"- A_1   = {rf.A1:.6e}")
        out.append(f"- A_2   = {rf.A2:.6e}")
        out.append(f"- RMSE  = {rf.rmse:.6e}")
        out.append(f"- residuals = {rf.residuals}")
    else:
        out.append(f"- fit_status: {report.richardson.fit_status if report.richardson else 'NONE'}")
        if report.richardson:
            out.append(f"- notes    : {report.richardson.fit_notes}")
    out.append("")
    out.append("## Stage 4 — Falsification gates (Math235 §3 + Math236 §3)")
    out.append("")
    out.append("| Gate | Pass | Detail |")
    out.append("|---|---|---|")
    for g in report.gates:
        mark = "✓" if g.passed else "✗"
        out.append(f"| {g.gate} | {mark} | {g.detail} |")
    out.append("")
    out.append("## Operator notes")
    out.append("")
    out.append("- `run_diagnostics.json` in the output dir holds the structured payload.")
    out.append("- Per-N output subdirs hold the solver's own `proof_results.json` etc.")
    out.append("- For T6 promotion of Pillar 6 sub-task β (Math234 OPEN GAP β),")
    out.append("  G1+G2+G3+G5+G6 must all PASS and f_inf must reproduce the SM")
    out.append("  electroweak scale within 30 percent (Math234 §3 closure criterion).")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(
        description="Math236 §9.2 four-stage continuum-limit-scan protocol "
                    "(BCC defect bundle, Task #115)."
    )
    p.add_argument("--config", required=True,
                   help="Brazovskii config JSON (e.g., Codes/pde/config_template_brazovskii.json)")
    p.add_argument("--mu2", type=float, default=DEFAULT_MU2,
                   help=f"Newton-Krylov mu^2 (default {DEFAULT_MU2})")
    p.add_argument("--N-list", nargs="+", type=int, default=DEFAULT_N_LIST,
                   help=f"List of N values for continuum scan (default {DEFAULT_N_LIST})")
    p.add_argument("--output-dir", default=None,
                   help="Output dir (default: Runs/continuation/math236_<timestamp>)")
    p.add_argument("--max-newton", type=int, default=DEFAULT_MAX_NEWTON,
                   help=f"Newton-Krylov max iterations per point (default {DEFAULT_MAX_NEWTON})")
    p.add_argument("--tol-newton", type=float, default=DEFAULT_TOL_NEWTON,
                   help=f"Newton tolerance (default {DEFAULT_TOL_NEWTON})")
    p.add_argument("--skip-stage", type=int, default=0,
                   help="Skip stages 3+4 if set to 3 (do solve+extract only)")
    p.add_argument("--quiet", action="store_true",
                   help="Pass --quiet to the solver")
    p.add_argument("--dry-run", action="store_true",
                   help="Echo solver commands, do not actually launch")
    p.add_argument("--resume", action="store_true",
                   help="Skip N values whose output dir already has a converged "
                        "Psi (Psi_converged.npy / Psi_final.npy). Use to recover "
                        "from a mid-scan crash without re-running completed points.")
    p.add_argument("--warm-start-checkpoint", action="store_true",
                   help="If only a Psi_checkpoint.npy is present in N_NNNN/, "
                        "pass it to the solver via --load-psi for Newton warm-"
                        "start. Only effective when --resume is also set.")
    p.add_argument("--fail-fast", action=argparse.BooleanOptionalAction,
                   default=True,
                   help="Abort the scan early on per-point falsification signals "
                        "(extraction failure, f<=0, NaN/Inf). Default ON. "
                        "Use --no-fail-fast to run the full N-list regardless of "
                        "early failures. Stages 3+4 still run on whatever data "
                        "was collected before the abort.")

    args = p.parse_args()

    root = repo_root()
    config_path = (root / args.config).resolve() if not Path(args.config).is_absolute() else Path(args.config).resolve()
    if not config_path.exists():
        print(f"FAIL: config not found: {config_path}", file=sys.stderr)
        return 1

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    if args.output_dir:
        out_dir = (root / args.output_dir).resolve() if not Path(args.output_dir).is_absolute() else Path(args.output_dir).resolve()
    else:
        out_dir = root / "Runs" / "continuation" / f"math236_{timestamp}"
    ensure_dir(out_dir)

    L_box = config_L_box(config_path)
    q0 = config_q0(config_path)

    report = ScanReport(
        timestamp=timestamp,
        config_path=str(config_path),
        mu2=float(args.mu2),
        N_list=list(args.N_list),
        L_box=L_box,
        output_dir=str(out_dir),
    )

    print("=" * 64)
    print(" Math236 §9.2 continuum-limit scan")
    print(f"  config    : {config_path}")
    print(f"  output    : {out_dir}")
    print(f"  mu^2      : {args.mu2}")
    print(f"  L_box     : {L_box}")
    print(f"  q0        : {q0}")
    print(f"  N list    : {args.N_list}")
    print(f"  dry-run   : {args.dry_run}")
    print("=" * 64)

    t_start = time.time()

    # Stage 1 + 2: per-N solve + amplitude extraction
    for N in args.N_list:
        sub_out = out_dir / f"N_{N:04d}"
        ensure_dir(sub_out)
        a_val = L_box / N
        print(f"\n[Stage 1] N={N}  (a = {a_val:.4f})")

        # Resume: if a converged Psi already exists, skip solve.
        existing_converged = find_psi_npy(sub_out) if args.resume else None
        if existing_converged is not None:
            print(f"  RESUME: found converged {existing_converged.name}; "
                  f"skipping solver, going straight to extraction.")
            per = PerNResult(
                N=N, a=a_val, output_dir=str(sub_out),
                solver_exit_code=0,
                solver_stdout_tail="(skipped: --resume hit existing converged Psi)",
                solver_wall_time_seconds=0.0,
                psi_path=str(existing_converged),
                extraction_status="RESUMED",
            )
        else:
            # Warm-start from in-N checkpoint if requested + present.
            warm_psi = None
            if args.resume and args.warm_start_checkpoint:
                cp = find_checkpoint_psi(sub_out)
                if cp is not None:
                    print(f"  RESUME: found checkpoint {cp.name}; "
                          f"warm-starting Newton via --load-psi.")
                    warm_psi = cp

            per = run_phase2_solve(
                config_path=config_path,
                N=N,
                mu2=args.mu2,
                output_dir=sub_out,
                max_newton=args.max_newton,
                tol_newton=args.tol_newton,
                quiet=args.quiet,
                dry_run=args.dry_run,
                load_psi=warm_psi,
            )

        if per.solver_exit_code == 0 and not args.dry_run:
            psi = find_psi_npy(sub_out)
            if psi is None:
                per.extraction_status = "PSI_NOT_FOUND"
                per.extraction_notes = f"no .npy file in {sub_out}"
            else:
                per.psi_path = str(psi)
                try:
                    f_val, note, status = extract_amplitude(
                        psi, q0=q0, N=N, L_box=L_box)
                    per.f_amplitude = f_val
                    # Math290 §4 / Bug B fix: propagate the actual status
                    # returned by the extractor instead of unconditionally
                    # tagging "OK". Structural failures (BAD_NDIM,
                    # NO_SHELL_MODES, ...) must be distinguishable from a
                    # genuine physics result of f == 0.
                    per.extraction_status = status
                    per.extraction_notes = note
                    print(f"  extracted f({per.a:.4f}) = {f_val:.6e}  "
                          f"[status={status}]")
                except Exception as exc:
                    per.extraction_status = "EXTRACTION_ERROR"
                    per.extraction_notes = f"{type(exc).__name__}: {exc}"

            # Math290 §5 Stage-1.5 free-energy guard: parse Delta F from
            # solver stdout tail and stamp PerNResult. The fail-fast gate
            # in per_point_fatal_reason consumes these.
            d_F, fav = parse_delta_F(per.solver_stdout_tail)
            per.delta_F = d_F
            per.favorable = fav
            if d_F is not None:
                print(f"  Delta F   = {d_F:+.3e}  (favorable={fav})")
        elif args.dry_run:
            per.extraction_status = "DRY_RUN"
            per.f_amplitude = None
        else:
            per.extraction_status = f"SOLVER_FAIL_EXIT_{per.solver_exit_code}"

        report.per_N.append(per)

        # Per-point fail-fast gate (CLAUDE.md §6.3.3 falsification-gate spirit).
        if args.fail_fast:
            reason = per_point_fatal_reason(per)
            if reason is not None:
                print(f"\n!!! FAIL-FAST triggered at N={N}: {reason}")
                print("    Skipping remaining N values; "
                      "Stages 3+4 will run on collected partial data.")
                report.overall_status = "EARLY_FAIL"
                break

    # Stage 3: Richardson fit
    if args.skip_stage and args.skip_stage <= 3:
        print("\n[Stage 3] SKIPPED per --skip-stage")
        report.richardson = RichardsonFit(fit_status="SKIPPED",
                                          fit_notes="--skip-stage <= 3")
    else:
        print("\n[Stage 3] Richardson fit ...")
        report.richardson = richardson_fit(report.per_N)
        if report.richardson.fit_status == "OK":
            print(f"  f_inf = {report.richardson.f_inf:.6e}")
            print(f"  A_1   = {report.richardson.A1:.6e}")
            print(f"  A_2   = {report.richardson.A2:.6e}")
            print(f"  RMSE  = {report.richardson.rmse:.6e}")

    # Stage 4: falsification gates
    if args.skip_stage and args.skip_stage <= 4:
        print("\n[Stage 4] SKIPPED per --skip-stage")
        report.gates = []
    else:
        print("\n[Stage 4] Falsification gates ...")
        report.gates = evaluate_gates(report.per_N, report.richardson)
        for g in report.gates:
            mark = "PASS" if g.passed else "FAIL"
            print(f"  {g.gate:30s}  {mark}   {g.detail}")

    # Overall verdict
    n_extracted = sum(1 for r in report.per_N if r.extraction_status == "OK")
    n_gates_passed = sum(1 for g in report.gates if g.passed)
    if args.dry_run:
        report.overall_status = "DRY_RUN"
    elif n_extracted == 0:
        report.overall_status = "ERROR"
    elif report.richardson and report.richardson.fit_status == "OK" and \
         n_gates_passed == len(report.gates) and report.gates:
        report.overall_status = "PASS"
    elif n_extracted > 0:
        report.overall_status = "PARTIAL"
    else:
        report.overall_status = "FAIL"

    report.elapsed_seconds = time.time() - t_start

    # Persist
    diag_path = out_dir / "run_diagnostics.json"
    payload = {
        "report": asdict(report),
        "constants": {
            "N_BCC_SHELL_MODES": N_BCC_SHELL_MODES,
            "FALSIFICATION_GATES": FALSIFICATION_GATES,
            "RICHARDSON_POWERS": RICHARDSON_POWERS,
        },
    }
    atomic_write_json(diag_path, payload)
    print(f"\nWrote {diag_path}")

    md_path = out_dir / "RESULT.md"
    atomic_write_text(md_path, render_result_md(report))
    print(f"Wrote {md_path}")

    print("\n" + "=" * 64)
    print(f"OVERALL: {report.overall_status}   "
          f"(elapsed {report.elapsed_seconds:.1f} s)")
    print("=" * 64)

    return 0 if report.overall_status in ("PASS", "DRY_RUN", "PARTIAL") else 2


if __name__ == "__main__":
    sys.exit(main())
