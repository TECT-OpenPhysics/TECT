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
tect_version_manifest.py
========================

Stamp every PDE run / extractor output with a dual fingerprint:

    (theory_version, code_version)

so that downstream analysis can ALWAYS map a numerical result back to
the exact theoretical framework AND the exact code that produced it.

Usage (at the top of any run script):

    from tect_version_manifest import build_manifest, write_manifest

    manifest = build_manifest(
        theory_version="Math38-Brazovskii-2026-04-15",
        run_label="emergence_safe_seed17",
        params=params,
        extra={"driver": "tect_solver_pt_v3.py"},
    )
    write_manifest(output_dir, manifest)

The theory_version string SHOULD match the latest closed-form label in
TECT-Theory-Code-Sync.md.  If the theory changes, bump the label there
FIRST, then update any run scripts.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

# Canonical list of theoretical invariants currently treated as CLOSED
# (see TECT-Theory-Code-Sync.md for the mapping).  Keep in strict sync.
THEORY_INVARIANTS_CLOSED = {
    "BCC_ground_state_unique": True,             # Project I  (Math01–05)
    "U1_gauge_emergence":      True,             # Project II (Math06–09)
    "Weyl_Dirac_emergence":    True,             # Project III(Math10–14)
    "Gates_1_to_4_logic":      True,             # Project IV (Math15–24)
    "Rank2_stabilizer_GSM":    True,             # Paper I/III/IV
    "Rank2_anomaly_filter":    True,             # Paper III Prop 5.4
    "BCC_lock_first_order":    True,             # phi0^2 = -4 lambda/(15 gamma) after Addendum A
    "I3_cubic_symmetry":       True,             # Math37 Addendum A, Lemma (I3 = 1/3)
    "K4_K6_BCC_constellation": True,             # Math37 Addendum A (K4=1, K6=5/2)
    "Brazovskii_regime_locked":True,             # Math38 (lambda<0, gamma>0 sizeable; first-order lock)
    "mstar_closed_form":       "conditional",    # Math37 AddA + Math38 (constellation-locked Brazovskii; dynamical convergence pending)
}

# Formulas currently under numerical reconciliation (NOT yet closed).
THEORY_INVARIANTS_OPEN = {
    "mstar_analytic_value":            "pending_normalization",
    "mstar_numeric_value":             "extractor_dependent",
    "G_IJ_positive_definite":          "pending",
    "full_SU3xSU2xU1_from_C3_bundle":  "pending",
    "rank2_emergence_from_pure_noise": "in_progress",   # Step C running
}


def _try_git_sha(repo_root: Path) -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return out.decode("ascii").strip()
    except Exception:
        return None


def _fingerprint_files(paths: Iterable[Path]) -> Dict[str, str]:
    """SHA-256 of each listed source file (first 16 hex chars)."""
    out: Dict[str, str] = {}
    for p in paths:
        p = Path(p)
        if not p.is_file():
            out[str(p)] = "MISSING"
            continue
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 16), b""):
                h.update(chunk)
        out[str(p)] = h.hexdigest()[:16]
    return out


def build_manifest(
    theory_version: str,
    run_label: str,
    params: Optional[Dict[str, Any]] = None,
    source_files: Optional[Iterable[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    repo_root = Path(repo_root) if repo_root else Path(__file__).resolve().parent.parent
    if source_files is None:
        source_files = [
            repo_root / "PDE" / "tect_solver_pt_v3.py",
            repo_root / "PDE" / "real_backend_pt_bcc_mixed_v3.py",
            repo_root / "PDE" / "tect_actual_extractor_pt_v3.py",
            repo_root / "PDE" / "bloch_linearization.py",
        ]
    manifest = {
        "schema_version": "1.1",
        "theory_version": theory_version,
        "regime":         "Brazovskii" if "Brazovskii" in theory_version else ("GL" if "GL" in theory_version else "unspecified"),
        "run_label":      run_label,
        "timestamp_utc":  datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "host":           platform.node(),
        "platform":       platform.platform(),
        "python":         platform.python_version(),
        "code_git_sha":   _try_git_sha(repo_root),
        "code_fingerprint": _fingerprint_files(source_files),
        "theory_invariants_closed": THEORY_INVARIANTS_CLOSED,
        "theory_invariants_open":   THEORY_INVARIANTS_OPEN,
        "params": params or {},
        "extra":  extra  or {},
    }
    return manifest


def write_manifest(output_dir: os.PathLike, manifest: Dict[str, Any]) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "tect_version_manifest.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    return path


def read_manifest(result_dir: os.PathLike) -> Optional[Dict[str, Any]]:
    path = Path(result_dir) / "tect_version_manifest.json"
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    import sys
    label = sys.argv[1] if len(sys.argv) > 1 else "dry_run"
    m = build_manifest(
        theory_version="Math37-AddA-2026-04-15",
        run_label=label,
        params={"mu2": 0.26, "lambda": -0.43, "gamma": 1.62},
    )
    print(json.dumps(m, indent=2, sort_keys=True))
