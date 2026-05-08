#!/usr/bin/env python3
# =====================================================================
# build_v3_mirror.py — Math353-AddD theory-only mirror preview helper
# =====================================================================
#
# Purpose
# -------
# Read Codes/config/mirror.json (v3 schema) and emit Github_v3_preview/
# tree showing what the v3 cutover will mirror. NEVER touches Github/.
# Operator reviews Github_v3_preview/ before cutover (Math353-AddE).
#
# Pipeline
# --------
#   1. Load mirror.json v3 settings.
#   2. Walk Codes/, Docs/, Runs/, Website/ subset roots.
#   3. For each file:
#       (a) Apply directory_renames longest-prefix-first.
#       (b) If matched a rename: apply per-subtree allowlist
#           (keep_status_files / keep_manual_files / keep_run_dirs /
#            keep_supplementary_pattern / keep_policy_files).
#       (c) If no rename matched: prefix-match exclude_directories_local;
#           if matched, skip.
#       (d) Otherwise: mirror as-is at root level.
#       (e) Always check exclude_files_local for explicit per-file skip.
#   4. Mirror result to Github_v3_preview/<rewritten-path>.
#   5. Emit summary log: counts per category, total bytes, list of
#      excluded operational files.
#
# Invariants
# ----------
#   I1  Read-only over canonical tree (Codes/, Docs/, Runs/, Website/).
#   I2  Writes ONLY to Github_v3_preview/ + Docs/status/v3-mirror-preview.log.
#   I3  Idempotent: re-running produces the same Github_v3_preview/ tree.
#   I4  Never touches Github/ (the active v0 mirror).
#
# Usage
# -----
#   python -u Codes/scripts/build_v3_mirror.py
#   python -u Codes/scripts/build_v3_mirror.py --dry-run    # log only, no files
#   python -u Codes/scripts/build_v3_mirror.py --clean      # wipe preview first
#
# Author: Math353-AddD (2026-05-08).
# =====================================================================

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = REPO_ROOT / "Codes" / "config" / "mirror.json"
# Default target is Github_v3_preview/ for review; override via --target.
DEFAULT_PREVIEW_ROOT = REPO_ROOT / "Github_v3_preview"
LOG_PATH = REPO_ROOT / "Docs" / "status" / "v3-mirror-preview.log"

# Source roots to walk (in order; longest-prefix-first matching is applied
# per-file via the directory_renames table).
WALK_ROOTS = [
    "Codes/pde",
    "Codes/supplementary",
    "Docs/math",
    "Docs/papers",
    "Docs/manual",
    "Docs/status",
    "Docs/policy",
    "Runs",
    "Website",
]

# Always-mirror-at-root canonical files (CLAUDE.md §13 four-file list).
ROOT_CANONICAL_MIRROR = [
    "README.md",       # auto-generated; if absent at canonical root, skipped
    "CHANGELOG.md",
    "NAVIGATION.md",
    "tect-research.plugin",
]


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print(f"FAIL: {CONFIG_PATH} not found", file=sys.stderr)
        sys.exit(1)
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"FAIL: {CONFIG_PATH} parse error: {e}", file=sys.stderr)
        sys.exit(1)
    if int(cfg.get("schema_version", 0)) < 3:
        print(f"FAIL: mirror.json schema_version < 3 (got {cfg.get('schema_version')})", file=sys.stderr)
        sys.exit(1)
    return cfg


def apply_rename(rel_posix: str, rules: dict) -> str | None:
    """Apply directory_renames longest-prefix-first. Return new path or None."""
    sorted_keys = sorted(rules.keys(), key=lambda k: -len(k))
    for k in sorted_keys:
        bare = k.rstrip("/")
        prefix = bare + "/"
        if rel_posix == bare:
            return rules[k].rstrip("/")
        if rel_posix.startswith(prefix):
            tail = rel_posix[len(prefix):]
            new_prefix = rules[k].rstrip("/")
            return f"{new_prefix}/{tail}" if tail else new_prefix
    return None


def matches_dir_prefix(rel_posix: str, prefixes: list) -> bool:
    """True if rel_posix starts with any prefix in the list (slash-aware)."""
    for p in prefixes:
        bare = p.rstrip("/")
        if rel_posix == bare or rel_posix.startswith(bare + "/"):
            return True
    return False


def passes_subtree_allowlist(local_rel: str, mirror_rel: str, cfg: dict) -> tuple[bool, str]:
    """Apply per-subtree allowlists. Return (keep, reason)."""

    # Codes/pde -> code/pde/  (excluded if matches exclude_pde_pattern)
    if local_rel.startswith("Codes/pde/"):
        import re as _re_pde
        pat = cfg.get("exclude_pde_pattern", "")
        if pat:
            fname = Path(local_rel).name
            if _re_pde.search(pat, fname):
                return False, f"exclude_pde_pattern ({fname})"
        return True, "pde theory code"

    # Codes/supplementary -> code/  (filtered by keep_supplementary_pattern)
    if local_rel.startswith("Codes/supplementary/"):
        pat = cfg.get("keep_supplementary_pattern", "")
        if pat:
            fname = Path(local_rel).name
            if not re.match(pat, fname):
                return False, f"keep_supplementary_pattern mismatch ({fname})"
        return True, "supplementary Math*.py"

    # Docs/manual -> code/manual/  (filtered by keep_manual_files)
    if local_rel.startswith("Docs/manual/"):
        keep = set(cfg.get("keep_manual_files", []))
        # Subpath relative to Docs/manual/
        sub = local_rel[len("Docs/manual/"):]
        if "/" in sub or sub not in keep:
            return False, f"keep_manual_files filter ({sub})"
        return True, "manual whitelist"

    # Docs/status -> status/  (filtered by keep_status_files when strict)
    if local_rel.startswith("Docs/status/"):
        keep = set(cfg.get("keep_status_files", []))
        sub = local_rel[len("Docs/status/"):]
        if cfg.get("strict_status_whitelist", False):
            # Allow subpath only if first segment in keep list (exact filename)
            if "/" not in sub and sub in keep:
                return True, "status whitelist"
            return False, f"keep_status_files filter ({sub})"
        return True, "status (non-strict)"

    # Runs -> code/runs/  (filtered by keep_run_dirs)
    if local_rel.startswith("Runs/"):
        keep = cfg.get("keep_run_dirs", [])
        sub = local_rel[len("Runs/"):]
        import re as _re_b
        for k in keep:
            kbare = k.rstrip("/")
            if sub == kbare or sub.startswith(kbare + "/"):
                # Apply file-pattern filter within the kept run_dir
                fname = sub.split("/")[-1]
                excl_pat = cfg.get("exclude_run_files_pattern", "")
                if excl_pat and _re_b.search(excl_pat, fname):
                    return False, f"exclude_run_files_pattern ({fname})"
                keep_pat = cfg.get("keep_run_files_pattern", "")
                if keep_pat and not _re_b.search(keep_pat, fname):
                    return False, f"keep_run_files_pattern mismatch ({fname})"
                return True, f"keep_run_dirs ({kbare})"
        return False, f"keep_run_dirs filter ({sub})"

    # Docs/policy/ -> not in directory_renames; manually placed under status/policy/
    if local_rel.startswith("Docs/policy/"):
        keep = set(cfg.get("keep_policy_files", []))
        sub = local_rel[len("Docs/policy/"):]
        if "/" not in sub and sub in keep:
            return True, "policy whitelist (status/policy/)"
        return False, f"keep_policy_files filter ({sub})"

    # Docs/papers/<subdir>/  (filtered by keep_paper_subdirs + paper_flatten_pdf_only)
    if local_rel.startswith("Docs/papers/"):
        keep = set(cfg.get("keep_paper_subdirs", []))
        sub = local_rel[len("Docs/papers/"):]
        first_seg = sub.split("/")[0] if "/" in sub else sub
        if not ("/" in sub and first_seg in keep):
            return False, f"keep_paper_subdirs filter ({sub})"
        # Paper flatten: PDF-only at top level, other paper-internal files excluded
        if cfg.get("paper_flatten_pdf_only", False):
            if not local_rel.endswith(".pdf"):
                return False, f"paper_flatten_pdf_only (non-PDF: {Path(local_rel).name})"
        return True, f"keep_paper_subdirs ({first_seg})"

    # Docs/math, Website -> default: pass through
    return True, "default pass-through"


def site_subtree_filter(local_rel: str, cfg: dict) -> tuple[bool, str]:
    """Extra filter for Website/* before site/ rename is applied."""
    site_excl_dirs = cfg.get("site_exclude_dirs_local", [])
    site_excl_files = cfg.get("site_exclude_files_local", [])
    if local_rel in site_excl_files:
        return False, f"site_exclude_files_local ({Path(local_rel).name})"
    if matches_dir_prefix(local_rel, site_excl_dirs):
        return False, "site_exclude_dirs_local"
    return True, ""


def walk_and_classify(cfg: dict) -> dict:
    """Walk source roots; classify each file as MIRROR or SKIP with reason."""
    rules = cfg.get("directory_renames", {}).get("rules", {})
    excl_dirs = cfg.get("exclude_directories_local", [])
    excl_files = set(cfg.get("exclude_files_local", []))

    classification = {
        "mirror": [],   # list[(local_rel, mirror_rel, bytes)]
        "skip":   [],   # list[(local_rel, reason)]
    }

    # Map Docs/policy/ -> status/policy/ explicitly (no directory_rename rule)
    # This is handled in the policy branch of passes_subtree_allowlist below.

    for walk_root in WALK_ROOTS:
        root_dir = REPO_ROOT / walk_root
        if not root_dir.exists():
            continue
        for fp in root_dir.rglob("*"):
            if not fp.is_file():
                continue
            try:
                local_rel = fp.relative_to(REPO_ROOT).as_posix()
            except ValueError:
                continue

            # 0) explicit per-file exclusion
            if local_rel in excl_files:
                classification["skip"].append((local_rel, "exclude_files_local"))
                continue

            # 1a) site-only filter (Website/* only)
            if local_rel.startswith("Website/"):
                ok, why = site_subtree_filter(local_rel, cfg)
                if not ok:
                    classification["skip"].append((local_rel, why))
                    continue

            # 1) per-subtree allowlist (manual / status / runs / supplementary / policy)
            mirror_rel_pre = local_rel  # placeholder, computed below
            ok_allow, allow_reason = passes_subtree_allowlist(local_rel, mirror_rel_pre, cfg)
            if not ok_allow:
                classification["skip"].append((local_rel, allow_reason))
                continue

            # 2) directory_renames longest-prefix-first
            renamed = apply_rename(local_rel, rules)

            # 2.5) Paper flatten: paper/<subdir>/<paper-id>/<paper-id>.pdf -> paper/<paper-id>.pdf
            if (renamed and renamed.startswith("paper/") and
                cfg.get("paper_flatten_pdf_only", False) and
                local_rel.endswith(".pdf")):
                # Extract just the PDF filename and put it at paper/ top level
                pdf_name = Path(renamed).name
                renamed = f"paper/{pdf_name}"

            # 3) Docs/policy/ -> manually map to status/policy/<file>
            if renamed is None and local_rel.startswith("Docs/policy/"):
                sub = local_rel[len("Docs/policy/"):]
                renamed = f"{cfg.get('policy_target_subdir', 'status/policy/').rstrip('/')}/{sub}"

            # 4) if no rename, check exclude_directories_local
            if renamed is None:
                if matches_dir_prefix(local_rel, excl_dirs):
                    classification["skip"].append((local_rel, "exclude_directories_local"))
                    continue
                # Default: mirror as-is at root
                renamed = local_rel

            try:
                size = fp.stat().st_size
            except OSError:
                size = -1
            classification["mirror"].append((local_rel, renamed, size))

    return classification


def emit_summary_log(cfg: dict, cls: dict) -> str:
    """Emit a human-readable summary log to LOG_PATH and return as string."""
    lines = []
    lines.append("# v3 mirror preview")
    lines.append(f"# Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"# active_v3_publish: {cfg.get('active_v3_publish', False)}")
    lines.append("")

    n_mirror = len(cls["mirror"])
    n_skip = len(cls["skip"])
    total_bytes = sum(b for _, _, b in cls["mirror"] if b > 0)
    lines.append(f"## Summary")
    lines.append(f"  Mirrored : {n_mirror} files, {total_bytes / 1024 / 1024:.2f} MB")
    lines.append(f"  Skipped  : {n_skip} files (operational / out-of-scope)")
    lines.append("")

    # Group mirror entries by top-level rewritten dir
    bins: dict[str, list] = {}
    for local, mirror, size in cls["mirror"]:
        top = mirror.split("/")[0] if "/" in mirror else "(root)"
        bins.setdefault(top, []).append((local, mirror, size))
    lines.append("## Mirror tree by top-level dir")
    for top in sorted(bins.keys()):
        sub = bins[top]
        sub_bytes = sum(b for _, _, b in sub if b > 0)
        lines.append(f"  {top}/ : {len(sub)} files, {sub_bytes / 1024:.1f} KB")
    lines.append("")

    # Group skip reasons
    skip_bins: dict[str, int] = {}
    for _, reason in cls["skip"]:
        skip_bins[reason] = skip_bins.get(reason, 0) + 1
    lines.append("## Skip reasons (count)")
    for reason in sorted(skip_bins.keys()):
        lines.append(f"  [{skip_bins[reason]:>5}] {reason}")
    lines.append("")

    # Sample of skipped files (first 30)
    lines.append("## Sample skipped (first 30)")
    for local, reason in cls["skip"][:30]:
        lines.append(f"  - {local}  ({reason})")
    lines.append("")

    # Sample of mirrored files per top-level dir (first 10 each)
    lines.append("## Sample mirrored (first 10 per top-level)")
    for top in sorted(bins.keys()):
        lines.append(f"### {top}/")
        for local, mirror, size in bins[top][:10]:
            lines.append(f"  - {local} -> {mirror}  ({size} bytes)")
        if len(bins[top]) > 10:
            lines.append(f"  ... ({len(bins[top]) - 10} more)")
        lines.append("")

    out = "\n".join(lines)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(out, encoding="utf-8")
    return out


def materialise_to_target(cls: dict, target_root: Path, clean: bool = False, preserve_dotgit: bool = True) -> int:
    """Copy mirror entries to target_root/. Return file count.

    If clean=True, wipes target_root first (preserving .git/ when preserve_dotgit=True).
    """
    if clean and target_root.exists():
        for child in target_root.iterdir():
            if preserve_dotgit and child.name == ".git":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    target_root.mkdir(parents=True, exist_ok=True)

    n = 0
    for local, mirror, _size in cls["mirror"]:
        src = REPO_ROOT / local
        dst = target_root / mirror
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dst)
            n += 1
        except OSError:
            pass
    return n


# Backward-compat alias
def materialise_preview(cls: dict, clean: bool) -> int:
    return materialise_to_target(cls, DEFAULT_PREVIEW_ROOT, clean=clean)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true",
                   help="emit summary log only; do not write target/")
    p.add_argument("--clean", action="store_true",
                   help="wipe target/ first (preserves .git/)")
    p.add_argument("--target", type=str, default="",
                   help="override target dir (default: Github_v3_preview/). Use 'Github' for cutover.")
    args = p.parse_args()
    target_root = Path(args.target).resolve() if args.target else DEFAULT_PREVIEW_ROOT

    cfg = load_config()
    print(f"build_v3_mirror.py — schema v{cfg.get('schema_version')}")
    print(f"  Repo root         : {REPO_ROOT}")
    rel_t = target_root.relative_to(REPO_ROOT) if target_root.is_relative_to(REPO_ROOT) else target_root
    print(f"  Preview target    : {rel_t}/")
    print(f"  Active v3 publish : {cfg.get('active_v3_publish', False)} (governs github_sync_curate; helper runs regardless)")
    print()

    print("Walking source roots and classifying ...")
    cls = walk_and_classify(cfg)
    print(f"  mirror : {len(cls['mirror'])}  skip : {len(cls['skip'])}")
    print()

    summary = emit_summary_log(cfg, cls)
    print(f"Summary log: {LOG_PATH.relative_to(REPO_ROOT)}")
    print()

    if args.dry_run:
        print(f"DRY-RUN: no files written to {target_root.relative_to(REPO_ROOT) if target_root.is_relative_to(REPO_ROOT) else target_root}/")
    else:
        n = materialise_to_target(cls, target_root, clean=args.clean)
        rel = target_root.relative_to(REPO_ROOT) if target_root.is_relative_to(REPO_ROOT) else target_root
        print(f"Materialised: {n} files into {rel}/")

    print()
    print("Top-level summary lines:")
    for ln in summary.split("\n")[:10]:
        print(f"  {ln}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
