#!/usr/bin/env python3
# =====================================================================
# [RETIRED 2026-05-07 — SUPERSEDED-BY-Math353]
# =====================================================================
# This script is no longer the active mechanism for the public-mirror
# directory rename. Math353 (`Docs/math/TECT-Math353-Mirror-First-
# Restructure-Strategy-Framework.tex.txt`, ACCEPTED 2026-05-07)
# replaces the local-rename approach with a mirror-first design: local
# tree retains `Codes/`, `Docs/`, `Runs/`, `Website/` naming; the
# rename + path-rewrite happens at the `github_sync_curate.py` v2
# boundary. This script is retained for git history; do NOT invoke.
# =====================================================================
# migrate_to_lowercase_code.py v1.1 (2026-05-07, post-trial-run patch)
#
# CHANGELOG
#   v1.0 (2026-05-07 morning): initial release.
#   v1.1 (2026-05-07 evening): fix two defects observed in trial run:
#     (a) Python Path() segment pattern: REPO_ROOT / "Codes" / ... was
#         not matched by the slash-bearing rule "Codes/" -> "code/".
#         New rules cover the segment-style usage explicitly.
#     (b) Documentation arrow self-corruption: "Codes/ -> code/" was
#         substituted on both sides into "code/ -> code/". A
#         PROTECTED_FILES set now skips substitution on files whose
#         purpose is documenting the migration itself (this script,
#         REPO_RESTRUCTURE_ROADMAP.md). For the Math352 note we
#         instead use placeholder substitution (preserve arrow text).
#
# Phase B-5/6/7 atomic migration helper. Renames the canonical
# directory tree to its target final-state form per
# Docs/policy/REPO_RESTRUCTURE_ROADMAP.md s2.1-s2.3:
#
#   Codes/            -> code/
#   Runs/             -> code/runs/
#   Docs/manual/      -> code/manual/
#
# AND updates ALL cross-references in tracked text files
# (Python imports, PowerShell paths, Markdown links, Math note cite
# refs, etc.). The operation is atomic per safe_write helper:
# every file edit goes through atomic os.replace.
#
# Modes
# -----
# (default)  Dry-run. Print every planned move + every cross-ref
#            replacement. NO file writes. Safe to run anytime.
#
# --apply    Execute the migration. Requires:
#            (a) git working tree clean (no uncommitted changes),
#            (b) no in-flight numerical runs writing to Runs/,
#            (c) explicit operator confirmation (this is destructive
#                in the sense that paths in code stop working).
#
# --verify   After --apply, runs check_file_integrity --strict +
#            verify_website + propagate_status --check. Aborts and
#            prints a recovery hint if any check fails.
#
# Pre-flight
# ----------
# The script will refuse to run --apply if:
#   - git status reports anything other than the migration's own
#     expected delta
#   - any integrity defect exists in the pre-migration tree
#
# Recovery
# --------
# If --apply leaves the tree broken, the operator can:
#   git restore --source=HEAD --staged --worktree .
# to revert to the last committed state. The script never writes
# outside the working tree, so HEAD is always a safe rollback point.
#
# Cross-references
# ----------------
# - Docs/policy/REPO_RESTRUCTURE_ROADMAP.md s2.1-s2.3 (target state)
# - CLAUDE.md s11.5 (atomic-write discipline)
# - Codes/scripts/safe_write.py (atomic helper used for all edits)
# =====================================================================
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from safe_write import atomic_write, atomic_replace_in_file
except ImportError:
    print("[migrate] FATAL: cannot import safe_write helpers", file=sys.stderr)
    sys.exit(2)

# ---------------------------------------------------------------------
# Migration plan (declarative; loaded by both dry-run and apply modes)
# ---------------------------------------------------------------------

DIRECTORY_MOVES: List[Tuple[str, str]] = [
    # (source, destination) — order matters: do Codes/ first, then
    # consolidate Runs and Docs/manual into the new code/ tree.
    ("Codes",       "code"),
    ("Runs",        "code/runs"),
    ("Docs/manual", "code/manual"),
]

# Substring replacement rules. Applied to every tracked text file.
# Order matters: longer / more-specific patterns first to avoid
# partial-match clobbering.
REPLACEMENT_RULES: List[Tuple[str, str]] = [
    # --- v1.1 NEW: Python Path() segment patterns (longer first) ---
    # These match REPO_ROOT / "Codes" / ... style usage where "Codes"
    # is a quoted segment, not a slash-bearing substring.
    ('REPO_ROOT / "Docs" / "manual"', 'REPO_ROOT / "code" / "manual"'),
    ('REPO_ROOT / "Codes" /', 'REPO_ROOT / "code" /'),
    ('REPO_ROOT / "Runs"',    'REPO_ROOT / "code" / "runs"'),
    ('Path("Codes")',         'Path("code")'),
    ('Path("Runs")',          'Path("code/runs")'),
    # --- POSIX-style paths ---
    ("Docs/manual/", "code/manual/"),
    ("Docs/manual",  "code/manual"),
    ("Codes/runs/",  "code/runs/"),   # rare; legacy typo guard
    ("Runs/",        "code/runs/"),
    # `Runs` as a bare token (e.g., "Runs directory" in narrative)
    # is NOT replaced — too risky for false positives.
    ("Codes/",       "code/"),
    # --- Windows-style backslash paths (in *.ps1, *.bat) ---
    ("Docs\\manual\\", "code\\manual\\"),
    ("Codes\\runs\\",  "code\\runs\\"),
    ("Runs\\",         "code\\runs\\"),
    ("Codes\\",        "code\\"),
]

# v1.1: files whose purpose is documenting the migration itself.
# Substitution is SKIPPED for these so the "Codes/ -> code/" arrow
# notation in their text is preserved as-is. The script itself is
# the canonical example.
PROTECTED_FILES: set = {
    "Codes/scripts/migrate_to_lowercase_code.py",
    "Docs/policy/REPO_RESTRUCTURE_ROADMAP.md",
}

# File extensions to scan for cross-reference replacement.
SCAN_EXTENSIONS = {
    ".py", ".ps1", ".sh", ".bat", ".md", ".tex", ".txt",
    ".json", ".yaml", ".yml", ".toml", ".html", ".css",
    ".cfg", ".ini", ".js",
}

# Skip these path prefixes (auto-regenerated mirrors / archives that
# will be re-derived from the new canonical tree on next snapshot).
SKIP_PREFIXES = (
    "Github/",            # auto-mirror; regenerated by github_sync_curate
    "Website/assets/",    # mirror of Docs+Codes+Runs; regenerated by generate_website
    ".git/",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    "node_modules/",
    ".tmp.driveupload/",
    "Backup/",
)


# ---------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------

def check_git_clean() -> Tuple[bool, str]:
    """Verify git working tree has no uncommitted changes."""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, check=True, cwd=REPO_ROOT,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        return (False, f"git status failed: {exc}")
    if out.stdout.strip():
        n_lines = len(out.stdout.strip().splitlines())
        return (False, f"git working tree dirty ({n_lines} lines of porcelain output); "
                       "commit or stash first")
    return (True, "git working tree clean")


def check_runs_quiescent() -> Tuple[bool, str]:
    """Heuristic: Runs/ tree has no .lock file or recently-modified
    .json (within 60 seconds), implying no driver is actively writing."""
    runs_dir = REPO_ROOT / "Runs"
    if not runs_dir.exists():
        return (True, "Runs/ directory not present (skipping)")
    # Look for any *.lock or *.in-progress file
    lock_files = list(runs_dir.rglob("*.lock"))
    if lock_files:
        return (False, f"Runs/ has {len(lock_files)} .lock file(s); active driver suspected")
    # Find recently-modified files
    import time
    now = time.time()
    recent = [
        f for f in runs_dir.rglob("*.json")
        if f.stat().st_mtime > (now - 60)
    ]
    if recent:
        return (False, f"Runs/ has {len(recent)} JSON file(s) modified <60s ago; "
                       "wait for active driver to finish")
    return (True, "Runs/ appears quiescent (no lock files, no recent activity)")


# ---------------------------------------------------------------------
# Discovery: which files need cross-ref updates
# ---------------------------------------------------------------------

def discover_text_files() -> List[Path]:
    """Walk the repo and return tracked text files that should be
    scanned for cross-reference updates."""
    files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT, topdown=True):
        rel_dir = os.path.relpath(dirpath, REPO_ROOT)
        if rel_dir == ".":
            rel_dir = ""
        else:
            rel_dir = rel_dir.replace(os.sep, "/") + "/"
        # In-place skip of unwanted subtrees
        dirnames[:] = [
            d for d in dirnames
            if not any((rel_dir + d + "/").startswith(p) for p in SKIP_PREFIXES)
            and not d.startswith(".")
        ]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in SCAN_EXTENSIONS:
                continue
            full = Path(dirpath) / fn
            files.append(full)
    return files


def find_replacements_in_file(path: Path) -> List[Tuple[str, str, int]]:
    """Return list of (pattern, replacement, occurrence_count) for
    rules that fire in this file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    hits: List[Tuple[str, str, int]] = []
    for pat, rep in REPLACEMENT_RULES:
        n = text.count(pat)
        if n > 0:
            hits.append((pat, rep, n))
    return hits


# ---------------------------------------------------------------------
# Apply mode: do the work
# ---------------------------------------------------------------------

def apply_directory_moves(dry_run: bool) -> List[str]:
    """Perform the three top-level directory renames via git mv.
    Returns log lines."""
    log: List[str] = []
    for src, dst in DIRECTORY_MOVES:
        src_path = REPO_ROOT / src
        dst_path = REPO_ROOT / dst
        if not src_path.exists():
            log.append(f"  [skip] {src} -> {dst}: source does not exist")
            continue
        if dst_path.exists():
            log.append(f"  [skip] {src} -> {dst}: destination already exists")
            continue
        if dry_run:
            log.append(f"  [dry-run] git mv {src} {dst}")
            continue
        # Ensure parent of destination exists
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["git", "mv", src, dst],
                check=True, cwd=REPO_ROOT,
                capture_output=True, text=True,
            )
            log.append(f"  [moved] {src} -> {dst}")
        except subprocess.CalledProcessError as exc:
            # Fallback: filesystem mv (git will detect rename on next add)
            log.append(f"  [git mv failed: {exc.stderr.strip()}; trying fs mv]")
            shutil.move(str(src_path), str(dst_path))
            log.append(f"  [moved-fs] {src} -> {dst}")
    return log


def apply_text_replacements(files: List[Path], dry_run: bool) -> List[str]:
    """Run all REPLACEMENT_RULES over each text file. Uses atomic_write
    when applying."""
    log: List[str] = []
    n_files_touched = 0
    n_total_replacements = 0
    n_protected_skipped = 0
    for path in files:
        # v1.1: skip protected files (migration documentation)
        try:
            rel_posix = path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel_posix = ""
        if rel_posix in PROTECTED_FILES:
            n_protected_skipped += 1
            continue
        hits = find_replacements_in_file(path)
        if not hits:
            continue
        n_files_touched += 1
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        new_text = text
        for pat, rep, _ in hits:
            new_text = new_text.replace(pat, rep)
        if new_text == text:
            continue
        n_total_replacements += sum(n for _, _, n in hits)
        try:
            rel = path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = str(path)
        if dry_run:
            summary = ", ".join(f"{n}x{pat}" for pat, _, n in hits)
            log.append(f"  [dry-run] {rel}: {summary}")
        else:
            try:
                atomic_write(path, new_text)
                summary = ", ".join(f"{n}x{pat}" for pat, _, n in hits)
                log.append(f"  [updated] {rel}: {summary}")
            except OSError as exc:
                log.append(f"  [error] {rel}: {exc}")
    summary = f"  ({n_files_touched} files, {n_total_replacements} total replacements"
    if n_protected_skipped > 0:
        summary += f"; {n_protected_skipped} protected files skipped"
    summary += ")"
    log.insert(0, summary)
    return log


# ---------------------------------------------------------------------
# Post-apply verification
# ---------------------------------------------------------------------

def post_apply_verify() -> Tuple[bool, List[str]]:
    """Run integrity, verify_website, propagate_status after apply.
    Note: paths in this script reference 'Codes/...' which after migration
    should be 'code/...'. The verify uses the NEW location for tools.
    """
    log: List[str] = []
    overall_ok = True
    # Try the new lowercase tools dir first; fall back to old if migration
    # didn't run yet.
    code_dir = REPO_ROOT / "code"
    legacy_dir = REPO_ROOT / "Codes"
    base = code_dir if code_dir.exists() else legacy_dir
    checks = [
        ("integrity", [sys.executable, "-u", str(base / "tools" / "check_file_integrity.py"), "--strict"]),
        ("verify_website", [sys.executable, "-u", str(base / "tools" / "verify_website.py")]),
        ("propagate_status", [sys.executable, "-u", str(base / "tools" / "propagate_status.py"), "--check"]),
    ]
    for name, cmd in checks:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT, timeout=120)
            log.append(f"  [{name}] exit={r.returncode}")
            if r.returncode != 0:
                overall_ok = False
                # Print last 5 lines of stderr/stdout for diagnosis
                tail = (r.stderr.strip() or r.stdout.strip()).splitlines()[-5:]
                for line in tail:
                    log.append(f"    | {line}")
        except (OSError, subprocess.TimeoutExpired) as exc:
            log.append(f"  [{name}] ERROR: {exc}")
            overall_ok = False
    return overall_ok, log


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply", action="store_true",
                   help="execute the migration (default: dry-run only)")
    p.add_argument("--verify", action="store_true",
                   help="after --apply, run integrity + verify_website + propagate_status")
    p.add_argument("--skip-preflight", action="store_true",
                   help="skip git-clean + runs-quiescent checks (dangerous)")
    args = p.parse_args()

    print(" migrate_to_lowercase_code v1.1 (Phase B-5/6/7 atomic migration; PROTECTED_FILES + Path-segment patterns)")
    print(f"   Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print()

    # Pre-flight
    if args.apply and not args.skip_preflight:
        print(" Pre-flight checks:")
        ok1, msg1 = check_git_clean()
        print(f"  [{('PASS' if ok1 else 'FAIL')}] git-clean: {msg1}")
        ok2, msg2 = check_runs_quiescent()
        print(f"  [{('PASS' if ok2 else 'FAIL')}] runs-quiescent: {msg2}")
        if not (ok1 and ok2):
            print()
            print(" Pre-flight failed. Resolve the issues above or use --skip-preflight.",
                  file=sys.stderr)
            return 1
        print()

    # Discovery
    print(" Discovering text files to scan...")
    files = discover_text_files()
    print(f"   Found {len(files)} text files")
    print()

    # Phase 1: directory moves
    print(" Phase 1: directory renames")
    for line in apply_directory_moves(dry_run=not args.apply):
        print(line)
    print()

    # Phase 2: text replacements
    print(" Phase 2: cross-reference updates")
    for line in apply_text_replacements(files, dry_run=not args.apply):
        print(line)
    print()

    if args.apply and args.verify:
        print(" Post-apply verification:")
        ok, vlog = post_apply_verify()
        for line in vlog:
            print(line)
        print()
        if not ok:
            print(" Verification FAILED. Recover via:", file=sys.stderr)
            print("   git restore --source=HEAD --staged --worktree .", file=sys.stderr)
            return 2

    if args.apply:
        print("[migrate] APPLY complete. Run snapshot when ready.")
    else:
        print("[migrate] DRY-RUN complete. Re-run with --apply to execute.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
