#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stamp_version_headers.py
========================

Prepend (or refresh) a unified TECT version-header block on every .py
file in the PDE/ tree. Idempotent: if the marker block already exists,
it is replaced with the current one.

Run via:

    python3 stamp_version_headers.py

Targets:  PDE/*.py and PDE/**/*.py EXCLUDING
  - stamp_version_headers.py   (this file)
  - deprecated/                (do not modify legacy)
  - backup_GL_*                (archival)
  - __pycache__/

Re-run after any theory-tag bump to refresh every file in sync.
"""
from __future__ import annotations

import io
import os
import re
from datetime import date
from pathlib import Path

# ---------------------------------------------------------
# Canonical header values — bump when theory/regime changes.
# ---------------------------------------------------------
THEORY_TAG   = "Math56-Addendum-v2p4-2026-04-20"
REGIME       = "Brazovskii (lambda<0, gamma>0 sizeable)"
SYNC_DOC     = "/Contents/docs/status/TECT-Theory-Code-Sync.md"
LAST_SYNCED  = "2026-04-20"

HEADER_MARK_BEGIN = "# === TECT VERSION HEADER BEGIN ==="
HEADER_MARK_END   = "# === TECT VERSION HEADER END ==="

# Per-file module-interface version. Bump when the module's public API or
# physics-relevant signature changes; this is independent of THEORY_TAG.
MODULE_VERSIONS = {
    # core PDE solver / backend / extractor (renamed 2026-04-15: dropped _FINAL)
    "tect_solver_pt_v3.py":              "v3.2",   # +sparse xyz grid; phase-cache branch/orbit assembly (Math39 opt A/B)
    "real_backend_pt_bcc_mixed_v3.py":   "v3.1",   # +lru-cached KX/KY/KZ meshgrid; 1D-broadcast BCC symbol (Math39 opt C)
    "tect_actual_extractor_pt_v3.py":    "v3.1",   # +R_patch +compute_theory_mstar2 (Math37 AddA)
    # pipeline orchestrator + Stage U2 modules
    "run_pipeline_n1.py":                "v1.2",   # +Stage U2c (live_m_parallel)
    "transport_extractor.py":            "v2.0",   # U2b-final
    "bloch_linearization.py":            "v1.1",
    "projector_spectral.py":             "v1.0",
    "intervalley_extractor_v4.py":       "v4.0",
    "dirac_index_bcc.py":                "v1.0",
    "live_m_parallel.py":                "v1.0",   # new 2026-04-15 (D5 closure)
    # audit / utility
    "carrier_audit.py":                  "v1.0",
    "remote_gap_audit.py":               "v1.0",
    "tect_version_manifest.py":          "v1.1",   # schema 1.1 +regime
    # standalone proof scripts
    "tect_c5_bcc_stability.py":          "v1.0",
    "tect_gap2_chern_solver.py":         "v1.0",
    "make_rank2_bcc_seed.py":            "v1.0",
    "rank2_check.py":                    "v1.0",
    # rank-selection (Paper III Prop 5.4 production = v4)
    "tect_rank_selection_v4.py":         "v4.0",
    # Math46 finite-audit extractors (canonical paths; v0.1 WITHDRAWN, superseded)
    "math46_c2_extractor.py":            "v0.8",       # v0.8 polish: Z_h aggregate changed from np.mean to p^2-weighted mean (comment said "p^2-weighted regression" but code was unweighted); supersedes v0.7
    "math46_c3_extractor.py":            "v0.7",       # v0.7: (R4) pass_T6_final = pass_T6 AND pass_frame_nonzero injected into CLI audit payload, (R5) _SmokeBackend.hessian_vec corrected to full-field (C,N,N,N) contract; supersedes v0.6
    # finite-audit pipeline orchestrator
    "run_audit_pipeline.py":             "v1.0",       # v1.0: Stages 1-5 pipeline; solver->config_patch->C2->C3->summary; --resume idempotent; --only-summary for progress checks
    # v2.4 theorem-anchored gates (Math56-Addendum, 2026-04-20)
    "v24_thresholds.py":                 "v2.4.0",     # NEW: theorem-anchored Phase-0/2.5 gates + class-II floor; 22/22 unit tests (tests/test_v24_thresholds.py); audit [H-1] fail-closed on non-positive lambda_Ritz (v2p4-adversarial-audit-2026-04-20)
    "continuation_mu2.py":               "v1.1",       # v1.1: imports brazovskii_critical_mu2 + v24 thresholds; refuses mu2 above r_c^meta per Math56-Addendum Theorem 1
    "hess_jump_audit.py":                "v1.1",       # v1.1: imports V24_G2_MIN / V24_G3_REL from v24_thresholds; Phase-2.5 (G2, G3) anchored to Math56-Addendum Theorems 4-5
    "tect_newton_krylov.py":             "v2.4.0",     # v2.4 (2026-04-20): v24 Phase-0 gate + Class-II floor wired between Phase 1 and Phase 2 via _run_v24_phase0_gate; --disable-v24-gate debug flag; phase_failed() recognises v2.4 gate FAIL; Math56-Addendum Theorem 2 + Corollary 1 enforcement
}

def build_header(module_version: str = "n/a") -> str:
    return (
        f"{HEADER_MARK_BEGIN}\n"
        f"# Theory tag    : {THEORY_TAG}\n"
        f"# Regime        : {REGIME}\n"
        f"# Module version: {module_version}\n"
        f"# Sync doc      : {SYNC_DOC}\n"
        f"# Last synced   : {LAST_SYNCED}\n"
        f"# Notes         : Code is version-locked to the above theory tag.\n"
        f"#                 The module-version field tracks the file's own API\n"
        f"#                 generation (filename = <module>_v<N>.py); the theory\n"
        f"#                 tag is global. Re-run PDE/stamp_version_headers.py\n"
        f"#                 after any tag bump or version-table edit.\n"
        f"{HEADER_MARK_END}\n"
    )

HEADER_RE = re.compile(
    re.escape(HEADER_MARK_BEGIN) + r".*?" + re.escape(HEADER_MARK_END) + r"\n?",
    flags=re.DOTALL,
)

EXCLUDE_DIRS = {"deprecated", "__pycache__"}
EXCLUDE_PREFIXES = ("backup_GL_",)
EXCLUDE_FILES = {"stamp_version_headers.py"}

def should_skip(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
        if any(part.startswith(pre) for pre in EXCLUDE_PREFIXES):
            return True
    return path.name in EXCLUDE_FILES

def split_preamble(text: str):
    """Return (preamble, body) where preamble = shebang + encoding lines,
    which must stay at top of file. At most 2 lines."""
    lines = text.splitlines(keepends=True)
    keep = []
    for line in lines[:2]:
        stripped = line.lstrip()
        if stripped.startswith("#!") or "coding:" in stripped or "coding=" in stripped:
            keep.append(line)
        else:
            break
    rest = "".join(lines[len(keep):])
    return "".join(keep), rest

def stamp_file(path: Path) -> str:
    """Return one of: 'new', 'refreshed', 'unchanged'."""
    text = path.read_text(encoding="utf-8")
    preamble, body = split_preamble(text)

    module_version = MODULE_VERSIONS.get(path.name, "unregistered")
    header_block = build_header(module_version)
    existing = HEADER_RE.search(body)
    if existing is not None:
        new_body = HEADER_RE.sub(header_block, body, count=1)
        if new_body == body:
            return "unchanged"
        status = "refreshed"
    else:
        new_body = header_block + body
        status = "new"

    new_text = preamble + new_body
    # Some files on the mount occasionally raise a transient PermissionError
    # on the first open. Retry with a brief mode toggle before giving up.
    try:
        path.write_text(new_text, encoding="utf-8")
    except PermissionError:
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        path.write_text(new_text, encoding="utf-8")
    return status

def main() -> None:
    root = Path(__file__).resolve().parent
    files = sorted(root.rglob("*.py"))
    counts = {"new": 0, "refreshed": 0, "unchanged": 0, "skipped": 0}
    for fp in files:
        rel = fp.relative_to(root)
        if should_skip(rel):
            counts["skipped"] += 1
            continue
        status = stamp_file(fp)
        counts[status] += 1
        print(f"  [{status:>9}]  {rel}")
    print()
    print(f"Theory tag : {THEORY_TAG}")
    print(f"Regime     : {REGIME}")
    print(f"Results    : {counts}")

if __name__ == "__main__":
    main()
