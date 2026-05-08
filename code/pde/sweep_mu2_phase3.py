#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
sweep_mu2_phase3.py — μ² sweep driver for TECT Phase 3 criticality
===================================================================

Sweeps μ² from the current baseline (0.26) downward, running the Newton-Krylov
proof protocol (Phases 1-2-3) at each point.  Goal: identify μ²_crit where
ΔF = F[Ψ_BCC] − F[0] crosses zero (Phase 3 flips FAIL → PASS).

Each run prints ISO-8601 timestamps, per-Newton-step timing, and detects
hangs via activity watchdog (no stdout for N seconds → kill + HANG verdict).
"""
from __future__ import annotations

import argparse
import copy
import datetime
import json
import math
import os
import re
import select
import shutil
import signal
import subprocess
import sys
import textwrap
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════
# §1  Data classes
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class StepTiming:
    """Wall-clock timing for one Newton step."""
    step: int
    t_start: str                                # ISO-8601
    elapsed_sec: float
    grad_norm: float = float("nan")
    gmres_iters: int = 0


@dataclass
class PointResult:
    """Result for one μ² sweep point."""
    mu2: float
    r_computed: float                           # r = mu2 + Y*q0^4
    phase1_converged: bool = False
    downstream_blocked: bool = False
    m_star_sq: float = float("nan")
    stable: bool = False
    delta_F: float = float("nan")
    favorable_vs_vacuum: bool = False
    solver_exit_code: int = -1
    error: Optional[str] = None
    hang_detected: bool = False
    idle_seconds_at_kill: float = 0.0
    t_start: str = ""                           # ISO-8601
    t_end: str = ""                             # ISO-8601
    elapsed_sec: float = 0.0
    step_timings: List[StepTiming] = field(default_factory=list)
    last_newton_step: int = -1
    current_phase: str = ""


@dataclass
class SweepSummary:
    """Aggregate sweep results."""
    config_path: str
    N: int
    L: str
    q0: float
    Y: float
    Z: float
    lam: float
    gamma: float
    points: List[PointResult] = field(default_factory=list)
    sweep_start: str = ""
    sweep_end: str = ""
    total_elapsed_sec: float = 0.0


# ═══════════════════════════════════════════════════════════════════════
# §2  Config manipulation
# ═══════════════════════════════════════════════════════════════════════

_LOCKED_KEYS = ("quartic_lambda", "lambda", "sextic_gamma", "gamma",
                "Z", "Y", "q0")


def load_base_config(path: str) -> Dict[str, Any]:
    """Load and validate the base Brazovskii config."""
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    missing = [k for k in ("mu2", "r", "Y", "q0") if k not in cfg]
    if missing:
        raise KeyError(f"Base config missing required keys: {missing}")
    return cfg


def validate_config_drift(cfg: Dict[str, Any], original: Dict[str, Any]) -> None:
    """Assert that locked parameters haven't been mutated."""
    for key in _LOCKED_KEYS:
        if key in original and cfg.get(key) != original[key]:
            raise RuntimeError(
                f"Config drift detected: '{key}' changed from "
                f"{original[key]} to {cfg.get(key)}"
            )


def make_point_config(base: Dict[str, Any], mu2: float) -> Dict[str, Any]:
    """Create a config dict with updated μ² and r = μ² + Y q₀⁴."""
    cfg = copy.deepcopy(base)
    Y = float(cfg["Y"])
    q0 = float(cfg["q0"])
    r_new = mu2 + Y * q0**4
    cfg["mu2"] = mu2
    cfg["r"] = r_new
    return cfg


# ═══════════════════════════════════════════════════════════════════════
# §3  Single-point solver invocation
# ═══════════════════════════════════════════════════════════════════════

def _now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _fmt_elapsed(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


# ── Regex patterns for parsing solver live output ───────────────
_RE_NEWTON_STEP = re.compile(
    r"Step\s+(\d+).*\|\|grad\|\|\s*=\s*([0-9.eE+\-]+)", re.IGNORECASE)
_RE_GMRES_ITERS = re.compile(
    r"tCG\s*=\s*(\d+)", re.IGNORECASE)
_RE_PHASE_HEADER = re.compile(
    r"Phase\s+(\d)", re.IGNORECASE)


def _get_cpu_time(pid: int) -> Optional[float]:
    """Read cumulative CPU time (user + system) for a process.

    Strategy:
      1. /proc/<pid>/stat  (Linux)
      2. psutil             (cross-platform, pip install psutil)
      3. None               (watchdog degrades to stdout-only)

    Returns seconds, or None if unavailable.
    """
    # ── Linux: /proc/pid/stat (no dependencies) ─────────────────
    try:
        with open(f"/proc/{pid}/stat", "r") as f:
            parts = f.read().split()
        utime = int(parts[13])
        stime = int(parts[14])
        ticks_per_sec = os.sysconf("SC_CLK_TCK")
        return (utime + stime) / ticks_per_sec
    except (FileNotFoundError, IndexError, OSError, ValueError, AttributeError):
        pass

    # ── Cross-platform: psutil ──────────────────────────────────
    try:
        import psutil  # type: ignore
        p = psutil.Process(pid)
        t = p.cpu_times()
        return t.user + t.system
    except Exception:
        pass

    return None


# Flag: is CPU monitoring available on this platform?
_CPU_MONITOR_AVAILABLE: Optional[bool] = None


def _check_cpu_monitor(pid: int) -> bool:
    """Test once whether CPU time can be read for the given pid."""
    global _CPU_MONITOR_AVAILABLE
    if _CPU_MONITOR_AVAILABLE is None:
        _CPU_MONITOR_AVAILABLE = _get_cpu_time(pid) is not None
        if not _CPU_MONITOR_AVAILABLE:
            print("  ⚠ CPU monitoring unavailable (no /proc, no psutil).")
            print("    Watchdog will use stdout silence only.  "
                  "Install psutil for CPU-based hang detection:", flush=True)
            print("      pip install psutil", flush=True)
    return _CPU_MONITOR_AVAILABLE


def _read_lines_with_cpu_watchdog(
    proc: subprocess.Popen,
    cpu_idle_limit: float,
    heartbeat_interval: float,
    stdout_fallback_limit: float = 3600.0,
) -> Tuple[List[str], bool, float]:
    """Read stdout lines from proc with CPU-based hang detection.

    Primary: HANG = process CPU time hasn't advanced for cpu_idle_limit sec.
    Fallback (no /proc, no psutil — e.g. Windows without psutil):
        HANG = no stdout for stdout_fallback_limit sec (default 3600 = 1 hr).
        This is deliberately generous because GMRES can be silent for long.

    During long silent stretches, prints a heartbeat line every
    heartbeat_interval seconds showing elapsed time and CPU usage.

    Returns (lines, hang_detected, idle_at_kill).
    """
    lines: List[str] = []
    hang = False
    idle_at_kill = 0.0

    last_stdout_time = time.monotonic()
    last_heartbeat_time = time.monotonic()
    wall_t0 = time.monotonic()

    # CPU tracking state
    has_cpu = _check_cpu_monitor(proc.pid)
    last_cpu_time = _get_cpu_time(proc.pid) if has_cpu else None
    last_cpu_check_time = time.monotonic()
    last_cpu_advance_time = time.monotonic()

    # ── Windows compatibility: select() doesn't work on pipes ───
    # Use a polling loop with non-blocking readline via threading
    if sys.platform == "win32":
        import threading
        import queue as _queue

        line_queue: _queue.Queue = _queue.Queue()

        def _reader():
            try:
                for ln in iter(proc.stdout.readline, ""):
                    line_queue.put(ln)
            except ValueError:
                pass
            line_queue.put(None)  # sentinel

        thr = threading.Thread(target=_reader, daemon=True)
        thr.start()

        while True:
            now = time.monotonic()
            try:
                line = line_queue.get(timeout=5.0)
            except _queue.Empty:
                line = None

            if line is None and not line_queue.empty():
                continue
            if line is None and proc.poll() is not None:
                break
            if line is not None and line == "":
                break

            if line is not None:
                last_stdout_time = now
                lines.append(line)
                sys.stdout.write(line)
                sys.stdout.flush()

            now = time.monotonic()

            # CPU check
            if has_cpu and now - last_cpu_check_time >= 10.0:
                last_cpu_check_time = now
                cur_cpu = _get_cpu_time(proc.pid)
                if cur_cpu is not None and last_cpu_time is not None:
                    if cur_cpu > last_cpu_time + 0.05:
                        last_cpu_advance_time = now
                        last_cpu_time = cur_cpu
                    else:
                        if now - last_cpu_advance_time >= cpu_idle_limit:
                            hang = True
                            idle_at_kill = now - last_cpu_advance_time
                            try:
                                proc.kill()
                            except OSError:
                                pass
                            break
                elif cur_cpu is not None:
                    last_cpu_time = cur_cpu
                    last_cpu_advance_time = now

            # stdout fallback (when no CPU monitoring)
            if not has_cpu:
                stdout_silence = now - last_stdout_time
                if stdout_silence >= stdout_fallback_limit:
                    hang = True
                    idle_at_kill = stdout_silence
                    try:
                        proc.kill()
                    except OSError:
                        pass
                    break

            # heartbeat
            stdout_silence = now - last_stdout_time
            if stdout_silence > 60.0 and (now - last_heartbeat_time) >= heartbeat_interval:
                last_heartbeat_time = now
                elapsed_wall = now - wall_t0
                cpu_now = _get_cpu_time(proc.pid) if has_cpu else None
                cpu_str = (f"CPU={cpu_now:.1f}s" if cpu_now is not None
                           else "CPU=n/a")
                print(f"  ♥ heartbeat  wall={_fmt_elapsed(elapsed_wall)}  "
                      f"silent={stdout_silence:.0f}s  {cpu_str}  "
                      f"(still computing...)", flush=True)

            if line is None and proc.poll() is not None:
                break

        return lines, hang, idle_at_kill

    # ── POSIX path: select() works on pipes ─────────────────────
    fd = proc.stdout.fileno()

    while True:
        ready, _, _ = select.select([fd], [], [], 5.0)
        now = time.monotonic()

        if ready:
            line = proc.stdout.readline()
            if line == "":
                break
            last_stdout_time = now
            lines.append(line)
            sys.stdout.write(line)
            sys.stdout.flush()
        else:
            if proc.poll() is not None:
                for tail in proc.stdout:
                    lines.append(tail)
                    sys.stdout.write(tail)
                sys.stdout.flush()
                break

        # ── CPU activity check (every 10s) ──────────────────────
        if has_cpu and now - last_cpu_check_time >= 10.0:
            last_cpu_check_time = now
            cur_cpu = _get_cpu_time(proc.pid)

            if cur_cpu is not None and last_cpu_time is not None:
                if cur_cpu > last_cpu_time + 0.05:
                    last_cpu_advance_time = now
                    last_cpu_time = cur_cpu
                else:
                    cpu_frozen_sec = now - last_cpu_advance_time
                    if cpu_frozen_sec >= cpu_idle_limit:
                        hang = True
                        idle_at_kill = cpu_frozen_sec
                        try:
                            proc.kill()
                        except OSError:
                            pass
                        break
            elif cur_cpu is not None:
                last_cpu_time = cur_cpu
                last_cpu_advance_time = now

        # ── stdout fallback (when no CPU monitoring) ────────────
        if not has_cpu:
            stdout_silence = now - last_stdout_time
            if stdout_silence >= stdout_fallback_limit:
                hang = True
                idle_at_kill = stdout_silence
                try:
                    proc.kill()
                except OSError:
                    pass
                break

        # ── heartbeat during long silence ───────────────────────
        stdout_silence = now - last_stdout_time
        if stdout_silence > 60.0 and (now - last_heartbeat_time) >= heartbeat_interval:
            last_heartbeat_time = now
            elapsed_wall = now - wall_t0
            cpu_now = _get_cpu_time(proc.pid) if has_cpu else None
            cpu_str = (f"CPU={cpu_now:.1f}s" if cpu_now is not None
                       else "CPU=n/a")
            print(f"  ♥ heartbeat  wall={_fmt_elapsed(elapsed_wall)}  "
                  f"silent={stdout_silence:.0f}s  {cpu_str}  "
                  f"(still computing...)", flush=True)

    return lines, hang, idle_at_kill


def _parse_step_timings(
    lines: List[str],
) -> Tuple[List[StepTiming], int, str]:
    """Parse Newton step numbers, grad norms, GMRES iters from live output.

    Returns (step_timings, last_step, current_phase).
    """
    timings: List[StepTiming] = []
    step_start_time = time.monotonic()  # will be approximate
    last_step = -1
    current_phase = ""
    pending_gmres = 0

    for line in lines:
        # detect phase changes
        pm = _RE_PHASE_HEADER.search(line)
        if pm:
            current_phase = f"Phase {pm.group(1)}"

        # detect Newton steps
        sm = _RE_NEWTON_STEP.search(line)
        if sm:
            step_num = int(sm.group(1))
            grad_norm = float(sm.group(2))

            now = time.monotonic()
            elapsed = now - step_start_time if timings else 0.0

            timings.append(StepTiming(
                step=step_num,
                t_start=_now_iso(),
                elapsed_sec=round(elapsed, 1),
                grad_norm=grad_norm,
                gmres_iters=pending_gmres,
            ))
            step_start_time = now
            last_step = step_num
            pending_gmres = 0

        # detect GMRES iterations
        gm = _RE_GMRES_ITERS.search(line)
        if gm:
            pending_gmres = int(gm.group(1))

    return timings, last_step, current_phase


def run_single_point(
    mu2: float,
    base_config: Dict[str, Any],
    solver_script: str,
    N: int,
    L: str,
    outdir_root: str,
    phases: str = "123",
    cpu_idle_limit: float = 120.0,
    heartbeat_interval: float = 120.0,
    extra_args: Optional[List[str]] = None,
) -> PointResult:
    """Run the Newton-Krylov solver for one μ² value.

    CPU-based watchdog: if the process's CPU time stops advancing for
    `cpu_idle_limit` seconds (default 120 = 2 min), it is killed as HANG.
    stdout silence alone is NOT a hang indicator — GMRES inner solves
    can run 30+ min without printing.  Heartbeat lines are printed every
    `heartbeat_interval` seconds during silent stretches.
    """

    Y = float(base_config["Y"])
    q0 = float(base_config["q0"])
    r_new = mu2 + Y * q0**4

    result = PointResult(mu2=mu2, r_computed=r_new)

    # ── write per-point config ──────────────────────────────────
    point_dir = os.path.join(outdir_root, f"mu2_{mu2:.6f}")
    os.makedirs(point_dir, exist_ok=True)

    cfg = make_point_config(base_config, mu2)
    validate_config_drift(cfg, base_config)

    cfg_path = os.path.join(point_dir, "config.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    # ── build command ───────────────────────────────────────────
    cmd = [
        sys.executable, solver_script,
        "--config", cfg_path,
        "--N", str(N),
        "--L", L,
        "--phases", phases,
        "--outdir", point_dir,
    ]
    if extra_args:
        cmd.extend(extra_args)

    # ── run with activity watchdog ──────────────────────────────
    result.t_start = _now_iso()
    t0 = datetime.datetime.now()

    print(f"\n{'─'*72}")
    print(f"  μ² = {mu2:.6f}   |   r = {r_new:.10f}")
    print(f"  START  {result.t_start}")
    print(f"  CPU idle limit: {cpu_idle_limit:.0f}s "
          f"(hang if CPU frozen > {cpu_idle_limit:.0f}s)")
    print(f"  heartbeat: every {heartbeat_interval:.0f}s during silence")
    print(f"  cmd: {' '.join(cmd)}")
    print(f"{'─'*72}", flush=True)

    try:
        # Force unbuffered stdout in the child Python process.
        # Without this, pipe-connected Python uses full buffering
        # and solver output is invisible until process exits.
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,    # merge stderr into stdout
            text=True,
            bufsize=1,                   # line-buffered
            env=env,
        )

        lines, hang, idle_at_kill = _read_lines_with_cpu_watchdog(
            proc, cpu_idle_limit, heartbeat_interval)

        proc.wait()  # collect exit code
        result.solver_exit_code = proc.returncode

        if hang:
            result.hang_detected = True
            result.idle_seconds_at_kill = idle_at_kill
            result.error = (
                f"HANG detected: no output for {idle_at_kill:.0f}s "
                f"(limit {idle_limit:.0f}s) — process killed"
            )

        # ── parse Newton step timings from captured lines ───────
        timings, last_step, cur_phase = _parse_step_timings(lines)
        result.step_timings = timings
        result.last_newton_step = last_step
        result.current_phase = cur_phase

    except Exception as e:
        result.error = str(e)
        result.solver_exit_code = -1

    t1 = datetime.datetime.now()
    result.t_end = _now_iso()
    result.elapsed_sec = (t1 - t0).total_seconds()

    # ── timing summary ──────────────────────────────────────────
    print(f"\n  END    {result.t_end}")
    print(f"  ELAPSED  {_fmt_elapsed(result.elapsed_sec)}  "
          f"({result.elapsed_sec:.1f} s)")

    if result.hang_detected:
        print(f"  ⚠ HANG  idle {result.idle_seconds_at_kill:.0f}s "
              f"at Newton step {result.last_newton_step}, "
              f"{result.current_phase}")

    if result.step_timings:
        print(f"  Newton steps completed: {len(result.step_timings)}")
        for st in result.step_timings:
            gm_str = f", GMRES={st.gmres_iters}" if st.gmres_iters else ""
            print(f"    step {st.step:3d}: "
                  f"{st.elapsed_sec:8.1f}s  "
                  f"||grad||={st.grad_norm:.2e}{gm_str}")

    # ── parse proof_results.json ────────────────────────────────
    results_path = os.path.join(point_dir, "proof_results.json")
    if os.path.isfile(results_path):
        try:
            with open(results_path, "r", encoding="utf-8") as f:
                res = json.load(f)

            # downstream blocked?
            if res.get("downstream_blocked", False):
                result.downstream_blocked = True
                if result.error is None:
                    result.error = res.get("downstream_reason", "blocked")
                print(f"  >>> DOWNSTREAM BLOCKED: "
                      f"{res.get('downstream_reason', '')}")

            # Phase 1
            p1 = res.get("phase1", {})
            result.phase1_converged = bool(p1.get("converged", False))

            # Phase 2
            p2 = res.get("phase2", {})
            result.m_star_sq = float(p2.get("m_star_sq", float("nan")))
            result.stable = bool(p2.get("stable", False))

            # Phase 3
            p3 = res.get("phase3", {})
            result.delta_F = float(p3.get("delta_F", float("nan")))
            result.favorable_vs_vacuum = bool(
                p3.get("favorable_vs_vacuum", False))

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            if result.error is None:
                result.error = f"JSON parse error: {e}"
    else:
        if result.error is None:
            result.error = "proof_results.json not found"

    # ── one-line verdict ────────────────────────────────────────
    p1_tag = "PASS" if result.phase1_converged else "FAIL"
    p2_tag = "PASS" if result.stable else "FAIL"
    p3_tag = "PASS" if result.favorable_vs_vacuum else "FAIL"
    if result.hang_detected:
        verdict = f"HANG at step {result.last_newton_step} ({result.current_phase})"
    elif result.downstream_blocked:
        verdict = f"P1={p1_tag}  P2=BLOCKED  P3=BLOCKED"
    else:
        verdict = (f"P1={p1_tag}  P2={p2_tag}  P3={p3_tag}  "
                   f"ΔF={result.delta_F:+.6e}")

    print(f"  VERDICT: {verdict}")
    print(f"{'─'*72}\n", flush=True)

    return result


# ═══════════════════════════════════════════════════════════════════════
# §4  Full sweep
# ═══════════════════════════════════════════════════════════════════════

DEFAULT_MU2_POINTS = [
    0.20, 0.15, 0.10, 0.05, 0.03,
    0.02, 0.015, 0.012, 0.010, 0.005,
]


def run_sweep(
    config_path: str,
    solver_script: str,
    N: int = 32,
    L: str = "20pi",
    mu2_values: Optional[List[float]] = None,
    outdir: str = "sweep_mu2_results",
    phases: str = "123",
    clean_stale: bool = True,
    cpu_idle_limit: float = 120.0,
    heartbeat_interval: float = 120.0,
    extra_args: Optional[List[str]] = None,
) -> SweepSummary:
    """Execute the full μ² sweep."""

    if mu2_values is None:
        mu2_values = list(DEFAULT_MU2_POINTS)

    base_config = load_base_config(config_path)

    summary = SweepSummary(
        config_path=config_path,
        N=N,
        L=L,
        q0=float(base_config["q0"]),
        Y=float(base_config["Y"]),
        Z=float(base_config["Z"]),
        lam=float(base_config.get("lambda", base_config.get("quartic_lambda", 0))),
        gamma=float(base_config.get("gamma", base_config.get("sextic_gamma", 0))),
    )

    # ── clean stale output dirs ─────────────────────────────────
    if clean_stale and os.path.isdir(outdir):
        for name in os.listdir(outdir):
            sub = os.path.join(outdir, name)
            if os.path.isdir(sub) and name.startswith("mu2_"):
                shutil.rmtree(sub, ignore_errors=True)

    os.makedirs(outdir, exist_ok=True)

    # ── header ──────────────────────────────────────────────────
    summary.sweep_start = _now_iso()
    sweep_t0 = datetime.datetime.now()

    print("=" * 72)
    print("  TECT μ² SWEEP — Phase 3 Criticality Search")
    print("=" * 72)
    print(f"  Config        : {config_path}")
    print(f"  Grid          : N={N}, L={L}")
    print(f"  Phases        : {phases}")
    print(f"  Output        : {outdir}")
    print(f"  Sweep points  : {len(mu2_values)}")
    print(f"  μ² values     : {mu2_values}")
    print(f"  Locked: q₀={summary.q0:.10f}, Y={summary.Y}, "
          f"Z={summary.Z:.10f}")
    print(f"  Locked: λ={summary.lam}, γ={summary.gamma}")
    print(f"  CPU idle limit: {cpu_idle_limit:.0f}s "
          f"(hang if CPU frozen > {cpu_idle_limit:.0f}s)")
    print(f"  Heartbeat     : every {heartbeat_interval:.0f}s during silence")
    print(f"  Sweep start   : {summary.sweep_start}")
    print("=" * 72, flush=True)

    # ── sweep loop ──────────────────────────────────────────────
    for i, mu2 in enumerate(mu2_values):
        print(f"\n{'▶'*3}  Point {i+1}/{len(mu2_values)}  "
              f"μ² = {mu2:.6f}  {'◀'*3}")

        pt = run_single_point(
            mu2=mu2,
            base_config=base_config,
            solver_script=solver_script,
            N=N, L=L,
            outdir_root=outdir,
            phases=phases,
            cpu_idle_limit=cpu_idle_limit,
            heartbeat_interval=heartbeat_interval,
            extra_args=extra_args,
        )
        summary.points.append(pt)

        # ── incremental save after every point ──────────────────
        _save_summary(summary, outdir)

    # ── finalize ────────────────────────────────────────────────
    sweep_t1 = datetime.datetime.now()
    summary.sweep_end = _now_iso()
    summary.total_elapsed_sec = (sweep_t1 - sweep_t0).total_seconds()

    _save_summary(summary, outdir)

    # ── final table ─────────────────────────────────────────────
    _print_final_table(summary)

    return summary


# ═══════════════════════════════════════════════════════════════════════
# §5  Output
# ═══════════════════════════════════════════════════════════════════════

def _sanitize_for_json(obj: Any) -> Any:
    """Recursively replace NaN/Inf with null for strict JSON."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(v) for v in obj]
    return obj


def _save_summary(summary: SweepSummary, outdir: str) -> None:
    """Save sweep results as JSON + human-readable TXT."""

    # ── JSON ────────────────────────────────────────────────────
    data = {
        "config_path": summary.config_path,
        "N": summary.N, "L": summary.L,
        "locked": {
            "q0": summary.q0, "Y": summary.Y, "Z": summary.Z,
            "lambda": summary.lam, "gamma": summary.gamma,
        },
        "sweep_start": summary.sweep_start,
        "sweep_end": summary.sweep_end,
        "total_elapsed_sec": summary.total_elapsed_sec,
        "points": [_sanitize_for_json(asdict(p)) for p in summary.points],
    }
    json_path = os.path.join(outdir, "sweep_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, allow_nan=False)

    # ── TXT table ───────────────────────────────────────────────
    txt_path = os.path.join(outdir, "sweep_summary.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("TECT μ² Sweep — Phase 3 Criticality\n")
        f.write(f"Config: {summary.config_path}\n")
        f.write(f"Grid: N={summary.N}, L={summary.L}\n")
        f.write(f"Locked: q₀={summary.q0:.10f}, Y={summary.Y}, "
                f"Z={summary.Z:.10f}\n")
        f.write(f"Locked: λ={summary.lam}, γ={summary.gamma}\n")
        f.write(f"Sweep: {summary.sweep_start} → {summary.sweep_end}\n")
        f.write(f"Total elapsed: "
                f"{_fmt_elapsed(summary.total_elapsed_sec)}\n\n")

        hdr = (f"{'μ²':>10s}  {'r':>14s}  {'P1':>4s}  {'P2':>4s}  "
               f"{'P3':>4s}  {'m*²':>12s}  {'ΔF':>14s}  "
               f"{'elapsed':>10s}  {'start':>20s}  {'end':>20s}")
        f.write(hdr + "\n")
        f.write("─" * len(hdr) + "\n")

        for p in summary.points:
            if p.hang_detected:
                p1, p2, p3 = "HANG", "—", "—"
            elif p.downstream_blocked:
                p1 = "PASS" if p.phase1_converged else "FAIL"
                p2, p3 = "—", "—"
            else:
                p1 = "PASS" if p.phase1_converged else "FAIL"
                p2 = "PASS" if p.stable else "FAIL"
                p3 = "PASS" if p.favorable_vs_vacuum else "FAIL"

            m_str = (f"{p.m_star_sq:.6e}" if math.isfinite(p.m_star_sq)
                     else "—")
            df_str = (f"{p.delta_F:+.6e}" if math.isfinite(p.delta_F)
                      else "—")
            el_str = _fmt_elapsed(p.elapsed_sec)

            f.write(f"{p.mu2:10.6f}  {p.r_computed:14.10f}  "
                    f"{p1:>4s}  {p2:>4s}  {p3:>4s}  "
                    f"{m_str:>12s}  {df_str:>14s}  "
                    f"{el_str:>10s}  {p.t_start:>20s}  {p.t_end:>20s}\n")

            # per-step detail (indented)
            if p.step_timings:
                for st in p.step_timings:
                    f.write(f"{'':>12s}step {st.step:3d}: "
                            f"{st.elapsed_sec:8.1f}s  "
                            f"||grad||={st.grad_norm:.2e}"
                            f"{f'  GMRES={st.gmres_iters}' if st.gmres_iters else ''}\n")
            if p.hang_detected:
                f.write(f"{'':>12s}⚠ HANG: no output for "
                        f"{p.idle_seconds_at_kill:.0f}s at step "
                        f"{p.last_newton_step}\n")

        # ── critical point estimate ─────────────────────────────
        f.write("\n")
        _write_critical_estimate(f, summary.points)


def _write_critical_estimate(f, points: List[PointResult]) -> None:
    """Estimate μ²_crit by linear interpolation of ΔF sign change."""
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        if (math.isfinite(a.delta_F) and math.isfinite(b.delta_F)
                and a.delta_F * b.delta_F < 0):
            # linear interpolation
            frac = a.delta_F / (a.delta_F - b.delta_F)
            mu2_crit = a.mu2 + frac * (b.mu2 - a.mu2)
            f.write(f"Phase 3 sign change between μ²={a.mu2:.6f} "
                    f"(ΔF={a.delta_F:+.4e}) and μ²={b.mu2:.6f} "
                    f"(ΔF={b.delta_F:+.4e})\n")
            f.write(f"Linear interpolation → μ²_crit ≈ {mu2_crit:.6f}\n")
            return

    f.write("No Phase 3 sign change detected in this sweep range.\n")
    # report trend
    valid = [p for p in points
             if math.isfinite(p.delta_F) and not p.downstream_blocked]
    if len(valid) >= 2:
        if valid[-1].delta_F < valid[0].delta_F:
            f.write("Trend: ΔF decreasing — extend sweep to lower μ².\n")
        else:
            f.write("Trend: ΔF not decreasing — check physics.\n")


def _print_final_table(summary: SweepSummary) -> None:
    """Print the final sweep summary table to stdout."""
    print("\n" + "=" * 72)
    print("  SWEEP COMPLETE")
    print("=" * 72)
    print(f"  Total elapsed: {_fmt_elapsed(summary.total_elapsed_sec)}  "
          f"({summary.total_elapsed_sec:.1f} s)")
    print()

    print(f"  {'μ²':>10s}  {'P1':>4s}  {'P2':>4s}  {'P3':>4s}  "
          f"{'m*²':>12s}  {'ΔF':>14s}  {'elapsed':>10s}")
    print(f"  {'─'*10}  {'─'*4}  {'─'*4}  {'─'*4}  "
          f"{'─'*12}  {'─'*14}  {'─'*10}")

    for p in summary.points:
        if p.hang_detected:
            p1, p2, p3 = "HANG", "—", "—"
        elif p.downstream_blocked:
            p1 = "PASS" if p.phase1_converged else "FAIL"
            p2, p3 = "—", "—"
        else:
            p1 = "PASS" if p.phase1_converged else "FAIL"
            p2 = "PASS" if p.stable else "FAIL"
            p3 = "PASS" if p.favorable_vs_vacuum else "FAIL"
        m_str = (f"{p.m_star_sq:.6e}" if math.isfinite(p.m_star_sq)
                 else "—")
        df_str = (f"{p.delta_F:+.6e}" if math.isfinite(p.delta_F)
                  else "—")
        el_str = _fmt_elapsed(p.elapsed_sec)
        note = " ⚠HANG" if p.hang_detected else ""
        print(f"  {p.mu2:10.6f}  {p1:>4s}  {p2:>4s}  {p3:>4s}  "
              f"{m_str:>12s}  {df_str:>14s}  {el_str:>10s}{note}")

    print("=" * 72)
    print(f"  Results saved: {os.path.join('sweep_mu2_results', 'sweep_summary.txt')}")
    print(f"                 {os.path.join('sweep_mu2_results', 'sweep_results.json')}")
    print("=" * 72, flush=True)


# ═══════════════════════════════════════════════════════════════════════
# §6  CLI
# ═══════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="TECT μ² sweep — find Phase 3 critical point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Example:
              python sweep_mu2_phase3.py \\
                --config config_template_brazovskii.json \\
                --N 32 --L 20pi \\
                --mu2 0.20,0.15,0.10,0.05,0.03,0.02,0.015,0.012,0.010,0.005
        """),
    )
    parser.add_argument("--config", required=True,
                        help="Path to base Brazovskii config JSON")
    parser.add_argument("--solver", type=str, default="tect_newton_krylov.py",
                        help="Path to solver script (default: tect_newton_krylov.py)")
    parser.add_argument("--N", type=int, default=32,
                        help="Grid dimension (default: 32)")
    parser.add_argument("--L", type=str, default="20pi",
                        help="Box size (default: 20pi)")
    parser.add_argument("--mu2", type=str, default=None,
                        help="Comma-separated μ² values (default: 10 built-in points)")
    parser.add_argument("--outdir", type=str, default="sweep_mu2_results",
                        help="Output directory (default: sweep_mu2_results)")
    parser.add_argument("--phases", type=str, default="123",
                        help="Solver phases to run (default: 123)")
    parser.add_argument("--cpu-idle", type=float, default=120.0,
                        help="CPU watchdog: kill if process CPU time stops "
                             "advancing for this many seconds (default: 120 "
                             "= 2 min). stdout silence alone is NOT a hang. "
                             "Set 0 to disable watchdog.")
    parser.add_argument("--heartbeat", type=float, default=120.0,
                        help="Print heartbeat line every N seconds during "
                             "long silent stretches (default: 120 = 2 min)")
    parser.add_argument("--no-clean", action="store_true",
                        help="Don't clean stale per-point directories")
    parser.add_argument("--solver-args", type=str, default="",
                        help="Extra args forwarded to solver (quoted string)")

    args = parser.parse_args()

    # ── parse μ² list ───────────────────────────────────────────
    if args.mu2:
        mu2_values = [float(x.strip()) for x in args.mu2.split(",")
                      if x.strip()]
    else:
        mu2_values = None  # use defaults

    # ── parse extra solver args ─────────────────────────────────
    extra = args.solver_args.split() if args.solver_args.strip() else None

    # ── watchdog limits (0 = disable → effectively infinite) ────
    cpu_idle = args.cpu_idle if args.cpu_idle > 0 else 1e9
    heartbeat = args.heartbeat if args.heartbeat > 0 else 1e9

    # ── run ─────────────────────────────────────────────────────
    run_sweep(
        config_path=args.config,
        solver_script=args.solver,
        N=args.N,
        L=args.L,
        mu2_values=mu2_values,
        outdir=args.outdir,
        phases=args.phases,
        clean_stale=not args.no_clean,
        cpu_idle_limit=cpu_idle,
        heartbeat_interval=heartbeat,
        extra_args=extra,
    )


if __name__ == "__main__":
    main()
