"""
record_run.py — Universal numerical-run recording helper for TECT.

Binding from 2026-04-29 (CLAUDE.md §10.6 NEW). Every TECT driver (PDE
solver, audit pipeline, supplementary computation, scan, sweep) MUST
use this helper to emit a uniform reproducibility-grade record per run.

Records:
  - <output_dir>/run_diagnostics.json  — full per-iteration time-series
                                          + provenance (driver, theory
                                          tag, hardware, seeds, gates)
  - <output_dir>/RESULT.md             — §0–§7 skeleton auto-populated
                                          from `Codes/pde/RESULT_TEMPLATE.md`;
                                          operator completes §8–§10

Driver-agnostic: works for any iterative numerical procedure that has
a notion of "step" with named diagnostic fields. Replaces ad-hoc
per-driver JSON emission.

Usage pattern (3-call API):

    from Codes.pde.record_run import RunRecorder

    rec = RunRecorder.start(
        output_dir="Runs/<class>/<run_id>/",
        run_class="continuation",
        driver_name="continuation_mu2_v25.py",
        driver_version="v2.6.7",
        theory_tag="Math74-AddB-v2p6p4-gate-semantic-fix-2026-04-23",
        config={"N": 32, "L": 62.20036, "mu2": -0.7, ...},
    )

    for step_idx, step_data in enumerate(newton_iter):
        rec.record_step(point_idx=0, step_idx=step_idx, fields=step_data)

    rec.finalize(
        overall_status="NO_CONVERGENCE",
        summary={"n_converged": 0, "n_stalled": 1, "wall_time_s": ...},
    )

The `fields` dict for `record_step` is free-form; recommended keys for
Newton-Krylov drivers:
  grad_norm, merit, F_value, rho_trust, eta_forcing,
  krylov_iterations, step_alpha, trust_radius, accepted

For other driver classes (audit, scan, sweep, integrator), use whatever
fields are natural; record_run.py does not enforce a schema beyond the
provenance + outcome metadata.

The helper is defensive: any persistence failure logs a warning to
stderr but does NOT raise, preserving the host driver's exit-code
contract. This is the same defensive policy as
continuation_mu2_v25.py v2.6.7.

Governed by:
  - CLAUDE.md §10  (records completeness)
  - CLAUDE.md §10.6  (NEW 2026-04-29 — binding helper-use rule)
  - Codes/pde/RESULT_TEMPLATE.md  (RESULT.md standard sections)

Author: Jusang Lee + collaboration (2026-04-29).
"""

from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


__version__ = "1.0.0"


def _safe_git_sha(repo_root: Optional[str] = None) -> str:
    """Best-effort HEAD SHA capture; returns 'unknown' on any failure."""
    try:
        cmd = ["git", "rev-parse", "HEAD"]
        cwd = repo_root or os.getcwd()
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def _hardware_summary() -> Dict[str, str]:
    info: Dict[str, str] = {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "python": sys.version.split()[0],
    }
    # PyTorch / CUDA capture is optional and never fatal.
    try:
        import torch  # type: ignore

        info["torch"] = torch.__version__
        if torch.cuda.is_available():
            info["cuda"] = torch.version.cuda or "unknown"
            info["gpu"] = torch.cuda.get_device_name(0)
        else:
            info["cuda"] = "n/a"
            info["gpu"] = "cpu-only"
    except Exception:
        info["torch"] = "n/a"
    try:
        import numpy as np  # type: ignore

        info["numpy"] = np.__version__
    except Exception:
        info["numpy"] = "n/a"
    return info


@dataclass
class RunRecorder:
    """Driver-agnostic numerical-run recorder.

    Single instance per run. Emits run_diagnostics.json (full per-step
    time-series) and RESULT.md skeleton (template-derived) at finalise
    time. Designed to be a drop-in import for any TECT driver.
    """

    output_dir: str
    run_class: str
    driver_name: str
    driver_version: str
    theory_tag: str
    config: Dict[str, Any] = field(default_factory=dict)
    run_id: str = ""
    timestamp_start: str = ""
    git_sha: str = ""
    hardware: Dict[str, str] = field(default_factory=dict)
    points: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    constants_check: Optional[List[str]] = None  # driver-emitted Brazovskii lines

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @classmethod
    def start(
        cls,
        output_dir: str,
        run_class: str,
        driver_name: str,
        driver_version: str,
        theory_tag: str,
        config: Optional[Dict[str, Any]] = None,
        constants_check: Optional[List[str]] = None,
    ) -> "RunRecorder":
        """Initialise a recorder, capturing provenance immediately."""
        os.makedirs(output_dir, exist_ok=True)
        run_id = os.path.basename(os.path.normpath(output_dir))
        rec = cls(
            output_dir=output_dir,
            run_class=run_class,
            driver_name=driver_name,
            driver_version=driver_version,
            theory_tag=theory_tag,
            config=config or {},
            run_id=run_id,
            timestamp_start=time.strftime("%Y-%m-%dT%H:%M:%S"),
            git_sha=_safe_git_sha(),
            hardware=_hardware_summary(),
            constants_check=constants_check,
        )
        # Emit a stub run_diagnostics.json immediately so the run is
        # detectable in case of a hard crash before finalise().
        rec._persist_diagnostics(overall_status="STARTED", summary={})
        return rec

    def record_step(
        self,
        point_idx: int,
        step_idx: int,
        fields: Dict[str, Any],
    ) -> None:
        """Append a single iteration record under (point_idx, step_idx).

        `fields` is free-form; whatever the driver tracks per iteration.
        """
        try:
            point = self.points.setdefault(
                point_idx,
                {
                    "index": int(point_idx),
                    "steps": [],
                    "step_count": 0,
                },
            )
            entry: Dict[str, Any] = {"step": int(step_idx)}
            entry.update({k: _coerce_jsonable(v) for k, v in fields.items()})
            point["steps"].append(entry)
            point["step_count"] = len(point["steps"])
        except Exception as exc:
            print(
                f"[record_run] record_step({point_idx},{step_idx}) "
                f"failed (non-fatal): {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )

    def set_point_summary(self, point_idx: int, summary: Dict[str, Any]) -> None:
        """Attach point-level summary fields (mu2, converged, wall_time, ...)."""
        try:
            point = self.points.setdefault(
                point_idx, {"index": int(point_idx), "steps": [], "step_count": 0}
            )
            point.update({k: _coerce_jsonable(v) for k, v in summary.items()})
        except Exception as exc:
            print(
                f"[record_run] set_point_summary({point_idx}) "
                f"failed (non-fatal): {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )

    def finalize(
        self,
        overall_status: str,
        summary: Optional[Dict[str, Any]] = None,
        emit_result_md_skeleton: bool = True,
    ) -> None:
        """Emit run_diagnostics.json + RESULT.md skeleton (if requested)."""
        try:
            self._persist_diagnostics(overall_status, summary or {})
        except Exception as exc:
            print(
                f"[record_run] finalize.diagnostics failed (non-fatal): "
                f"{type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
        if emit_result_md_skeleton:
            try:
                self._emit_result_skeleton(overall_status, summary or {})
            except Exception as exc:
                print(
                    f"[record_run] finalize.result_md failed (non-fatal): "
                    f"{type(exc).__name__}: {exc}",
                    file=sys.stderr,
                )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _persist_diagnostics(
        self, overall_status: str, summary: Dict[str, Any]
    ) -> None:
        path = os.path.join(self.output_dir, "run_diagnostics.json")
        payload = {
            "schema_version": __version__,
            "run_id": self.run_id,
            "run_class": self.run_class,
            "driver": self.driver_name,
            "driver_version": self.driver_version,
            "theory_tag": self.theory_tag,
            "git_sha": self.git_sha,
            "hardware": self.hardware,
            "config": self.config,
            "constants_check": self.constants_check or [],
            "timestamp_start": self.timestamp_start,
            "timestamp_end": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "overall_status": overall_status,
            "summary": {k: _coerce_jsonable(v) for k, v in summary.items()},
            "points": [self.points[k] for k in sorted(self.points.keys())],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False, default=str)

    def _emit_result_skeleton(
        self, overall_status: str, summary: Dict[str, Any]
    ) -> None:
        """Emit a §0–§7 RESULT.md skeleton; §8–§10 left for operator.

        If RESULT.md already exists in the directory, append a
        ".auto-skeleton.md" sibling instead of overwriting; this lets
        retroactively-populated RESULTs (e.g. math82H_v266d) survive.
        """
        target = os.path.join(self.output_dir, "RESULT.md")
        skeleton_target = (
            target if not os.path.exists(target)
            else os.path.join(self.output_dir, "RESULT.auto-skeleton.md")
        )

        config_lines = "\n".join(
            f"- `{k}`: `{v}`" for k, v in self.config.items()
        ) or "(none recorded)"

        constants_block = (
            "\n".join(self.constants_check)
            if self.constants_check
            else "(driver did not pass constants_check; if Brazovskii driver, this is a defect)"
        )

        # Convergence-table snippet (first 5 + last 3 steps per point;
        # full series lives in run_diagnostics.json)
        conv_blocks: List[str] = []
        for pidx in sorted(self.points.keys()):
            pt = self.points[pidx]
            steps = pt.get("steps", [])
            if not steps:
                continue
            head = steps[: min(5, len(steps))]
            tail = steps[max(5, len(steps) - 3):] if len(steps) > 5 else []
            keys = sorted({k for s in head + tail for k in s.keys()})
            cols = " | ".join(keys)
            sep = " | ".join(["---"] * len(keys))
            rows: List[str] = []
            for s in head:
                rows.append(" | ".join(str(s.get(k, "")) for k in keys))
            if tail:
                rows.append(" | ".join(["…"] * len(keys)))
                for s in tail:
                    rows.append(" | ".join(str(s.get(k, "")) for k in keys))
            conv_blocks.append(
                f"\n#### Point {pidx}\n\n| {cols} |\n| {sep} |\n"
                + "\n".join(f"| {r} |" for r in rows)
                + "\n"
            )
        convergence_table = "\n".join(conv_blocks) or "(no per-step records)"

        body = f"""# RESULT.md — {self.run_id}

(Auto-generated skeleton from `Codes/pde/record_run.py` v{__version__}.
Operator MUST review and complete §8–§10. Full per-iteration
diagnostics in `run_diagnostics.json`.)

## §0. Run Identity

| Field | Value |
|---|---|
| Run ID | `{self.run_id}` |
| Run class | `{self.run_class}` |
| Started (UTC) | `{self.timestamp_start}` |
| Ended (UTC) | `{time.strftime("%Y-%m-%dT%H:%M:%S")}` |
| Wall time (s) | `{summary.get("wall_time_s", "?")}` |
| Maintainer | Jusang Lee (`jtkor@outlook.com`) |
| Operator | (please fill) |

## §1. Provenance

| Field | Value |
|---|---|
| Driver path | `{self.driver_name}` |
| Driver version | `{self.driver_version}` |
| Theory tag | `{self.theory_tag}` |
| Git commit SHA | `{self.git_sha}` |
| Host | `{self.hardware.get("hostname", "?")}` |
| Platform | `{self.hardware.get("platform", "?")}` |
| Python / NumPy / Torch / CUDA | `{self.hardware.get("python", "?")}` / `{self.hardware.get("numpy", "?")}` / `{self.hardware.get("torch", "?")}` / `{self.hardware.get("cuda", "?")}` |
| GPU | `{self.hardware.get("gpu", "?")}` |

## §2. Configuration

{config_lines}

(Full provenance in `run_diagnostics.json`.)

## §3. Brazovskii / TECT Constants Verification

```text
{constants_block}
```

## §4. Per-Iteration Convergence Table (head/tail; full series in run_diagnostics.json)

{convergence_table}

## §5. Outcome Status

`{overall_status}`

Summary: {summary or "(none)"}

## §6. Physical Interpretation (CLAUDE.md §6.3.4 mandatory — operator must complete)

(Operator: state ≥1 explicit quantitative sanity check from the §6.3.4
binding 8-class table. Required even for `PASS` outcomes.)

## §7. Files Persisted

- `run_diagnostics.json` — full per-iteration time-series + provenance
- `RESULT.md` — this file
- (driver may also emit `MANIFEST.md`, `Psi_*.npy`, etc.)

## §8. Cross-References (atomic-write per CLAUDE.md §3 — operator must complete)

- ☐ `CHANGELOG.md` entry
- ☐ `Docs/status/research-log.md` dated entry
- ☐ `Docs/status/EVIDENCE-INDEX.md` row
- ☐ `Docs/status/NEGATIVE-RESULTS.md` (only if outcome retracts a prior claim)

## §9. Diagnosis & Next-Step Plan (mandatory if NOT `PASS`)

(Operator: complete per `Codes/pde/RESULT_TEMPLATE.md` §9.)

## §10. Sign-off (operator must complete)

(Operator: complete per `Codes/pde/RESULT_TEMPLATE.md` §10.)
"""

        with open(skeleton_target, "w", encoding="utf-8") as f:
            f.write(body)


def _coerce_jsonable(v: Any) -> Any:
    """Coerce non-trivially-jsonable values (numpy scalars, etc.) to str."""
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, (list, tuple)):
        return [_coerce_jsonable(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _coerce_jsonable(x) for k, x in v.items()}
    # numpy / torch scalars
    try:
        return float(v)
    except Exception:
        pass
    try:
        return int(v)
    except Exception:
        pass
    return str(v)
