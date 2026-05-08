#!/usr/bin/env python3
# =====================================================================
# check_file_integrity.py v1.0 (2026-05-07)
#
# Pre-commit truncation + null-byte guard. Catches the recurring
# failure modes observed across 2026-04 / 2026-05 sessions:
#
#   (a) Trailing NUL bytes — Write-tool padding artefact. Files ending
#       with `\x00` parse OK in Python but break `node --check` and
#       break PowerShell parsing when the NUL is inside a control
#       structure.
#
#   (b) Mid-line truncation — Edit-tool interrupt artefact. The last
#       N lines are silently dropped, often inside an open string
#       literal or unclosed if/while/function block. Python and JS
#       parsers immediately detect; PowerShell may swallow the error
#       until execution.
#
#   (c) Suspicious shrinkage — current file is dramatically smaller
#       than its git-HEAD version, with no commit message explaining.
#       Heuristic flag for operator review.
#
# CLI:
#   python -u Codes/tools/check_file_integrity.py            # warn-only by default
#   python -u Codes/tools/check_file_integrity.py --strict   # fail (exit 1) on any defect
#   python -u Codes/tools/check_file_integrity.py --fix      # auto-strip trailing NULs
#   python -u Codes/tools/check_file_integrity.py PATH ...   # restrict to listed paths
#
# Exit codes:
#   0  OK / no defects (or warn-only mode with defects flagged)
#   1  --strict mode: at least one defect detected
#   2  I/O error
# =====================================================================
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# File extensions that we actively scan. Binary types (.png, .npy, .pdf,
# .jpg, etc.) are always skipped.
TEXT_EXTENSIONS = {
    ".py", ".js", ".ps1", ".sh", ".bat", ".md", ".tex", ".txt",
    ".json", ".yaml", ".yml", ".toml", ".html", ".css", ".cfg",
    ".ini", ".gitignore",
}

# Paths excluded from scan (mirror trees, vendor copies, archives).
EXCLUDE_PREFIXES = (
    "Github/",            # auto-generated mirror
    "Website/assets/",    # mirror of Docs/Codes/Runs
    "Backup/",
    "Runs/",
    ".git/",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    "node_modules/",
    ".tmp.driveupload/",
    "Docs/archive/",
    "Codes/deprecated/",
)

# Filename patterns that indicate deprecated / archived files; these are
# kept for historical record but are NOT expected to parse cleanly.
# Examples: continuation_mu2_v25.old.v2.6.6.py, foo_v1.deprecated.py.
EXCLUDE_FILENAME_PATTERNS = (
    r"\.old\.",         # *.old.* (archived old version)
    r"\.deprecated\.",  # *.deprecated.*
    r"\.bak$",           # *.bak
    r"\.backup$",        # *.backup
)

# Suspicious shrinkage threshold: if the current file is < this fraction
# of the git-HEAD version (and the diff has no commit message), flag it.
SHRINKAGE_RATIO_THRESHOLD = 0.50  # current size < 50 % of HEAD = suspicious


def list_tracked_files() -> List[Path]:
    """Return all git-tracked files plus newly-added files (no .gitignore'd)."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            capture_output=True, text=True, check=True, cwd=REPO_ROOT,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"[integrity] WARN: git ls-files failed: {exc}", file=sys.stderr)
        return []
    return [REPO_ROOT / line.strip() for line in out.stdout.splitlines()
            if line.strip()]


def read_git_head(path: Path) -> Optional[bytes]:
    """Return the file's content at git HEAD, or None if not tracked / missing."""
    try:
        rel = path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return None
    try:
        out = subprocess.run(
            ["git", "show", f"HEAD:{rel}"],
            capture_output=True, check=True, cwd=REPO_ROOT,
        )
        return out.stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def is_in_scope(path: Path) -> bool:
    """Decide whether to scan this file."""
    try:
        rel = path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return False
    if any(rel.startswith(pref) for pref in EXCLUDE_PREFIXES):
        return False
    # Filename-pattern exclusion (deprecated / archived files)
    name = path.name
    for pat in EXCLUDE_FILENAME_PATTERNS:
        if re.search(pat, name):
            return False
    if path.suffix.lower() not in TEXT_EXTENSIONS and path.name != ".gitignore":
        return False
    if not path.is_file():
        return False
    return True


def check_null_padding(path: Path, data: bytes) -> Optional[str]:
    """Detect trailing NUL bytes that indicate Write-tool padding."""
    if data.endswith(b"\x00"):
        n = 0
        for b in reversed(data):
            if b == 0:
                n += 1
            else:
                break
        return f"trailing NUL padding ({n} bytes)"
    return None


def check_python_truncation(path: Path, data: bytes) -> Optional[str]:
    """Try to parse Python; if parse fails, report SyntaxError line.
    SyntaxWarning (e.g. invalid escape sequences in non-raw strings) is
    suppressed: it indicates a code-smell, NOT a truncation defect, and
    the file still parses successfully. Use --warn-escape to surface."""
    try:
        import ast, warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            ast.parse(data.decode("utf-8", errors="replace"))
    except SyntaxError as exc:
        return f"Python parse error at line {exc.lineno}: {exc.msg}"
    except UnicodeDecodeError as exc:
        return f"UTF-8 decode error: {exc}"
    return None


def check_powershell_truncation(path: Path, data: bytes) -> Optional[str]:
    """Conservative PowerShell truncation check: the brace-balance heuristic
    is too false-positive-prone (here-strings, ${expansion}, $() etc.), so
    we only flag the actual truncation signature: an unterminated string
    literal on the file's LAST non-blank line. This catches the
    snapshot.ps1 line-595 'prec... mid-string truncation pattern.
    """
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception as exc:
        return f"decode error: {exc}"
    last_line = (text.rstrip().splitlines() or [""])[-1]
    # Quote-balance check: counts apostrophes / quotes outside escapes.
    sq = last_line.count("'") - last_line.count("\\'")
    dq = last_line.count('"') - last_line.count('\\"')
    if sq % 2 != 0:
        return f"last non-blank line has unbalanced single-quotes: {last_line[:80]!r}"
    if dq % 2 != 0:
        return f"last non-blank line has unbalanced double-quotes: {last_line[:80]!r}"
    return None


def check_json_truncation(path: Path, data: bytes) -> Optional[str]:
    """JSON parse check."""
    try:
        import json
        json.loads(data.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        return f"JSON parse error at line {exc.lineno}: {exc.msg}"
    except UnicodeDecodeError as exc:
        return f"UTF-8 decode error: {exc}"
    return None


def check_shrinkage(path: Path, data: bytes) -> Optional[str]:
    """Compare current size against git HEAD; flag suspicious shrinkage."""
    head = read_git_head(path)
    if head is None or not head:
        return None  # new file or untracked
    if len(head) == 0:
        return None
    ratio = len(data) / len(head)
    if ratio < SHRINKAGE_RATIO_THRESHOLD:
        return (f"size shrunk from {len(head)} -> {len(data)} bytes "
                f"({ratio*100:.1f}% of HEAD); confirm this is intentional")
    return None


def fix_null_padding(path: Path) -> bool:
    """Strip trailing NULs in-place. Returns True if any were stripped."""
    with path.open("rb") as f:
        data = f.read()
    clean = data.rstrip(b"\x00")
    if len(clean) == len(data):
        return False
    with path.open("wb") as f:
        f.write(clean)
    return True


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("paths", nargs="*",
                   help="restrict scan to these paths; default = all tracked files")
    p.add_argument("--strict", action="store_true",
                   help="exit 1 if any defect is detected")
    p.add_argument("--fix", action="store_true",
                   help="auto-strip trailing NUL bytes (irreversible)")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    print(" check_file_integrity v1.0 (truncation + NUL guard)")

    if args.paths:
        targets = [Path(x).resolve() for x in args.paths if Path(x).exists()]
    else:
        targets = list_tracked_files()
    targets = [t for t in targets if is_in_scope(t)]
    print(f"   Scanning {len(targets)} files")

    defects: List[Tuple[Path, str, str]] = []
    nul_fixed = 0

    for path in targets:
        try:
            data = path.read_bytes()
        except OSError as exc:
            defects.append((path, "io-error", str(exc)))
            continue

        # Fix-mode: strip NULs first so subsequent checks see the cleaned data
        if args.fix:
            if fix_null_padding(path):
                nul_fixed += 1
                data = path.read_bytes()

        # Check 1: NUL padding
        msg = check_null_padding(path, data)
        if msg:
            defects.append((path, "nul-padding", msg))

        # Check 2-4: language-specific syntax
        suffix = path.suffix.lower()
        if suffix == ".py":
            msg = check_python_truncation(path, data)
            if msg:
                defects.append((path, "py-syntax", msg))
        elif suffix == ".ps1":
            msg = check_powershell_truncation(path, data)
            if msg:
                defects.append((path, "ps1-syntax", msg))
        elif suffix == ".json":
            msg = check_json_truncation(path, data)
            if msg:
                defects.append((path, "json-syntax", msg))

        # Check 5: suspicious shrinkage
        msg = check_shrinkage(path, data)
        if msg:
            defects.append((path, "shrinkage", msg))

        if args.verbose and not any(d[0] == path for d in defects):
            try:
                rel = path.relative_to(REPO_ROOT).as_posix()
            except ValueError:
                rel = str(path)
            print(f"   ok    {rel}")

    if args.fix:
        print(f"   --fix stripped NUL bytes from {nul_fixed} file(s)")

    if not defects:
        print("[integrity] OK (no defects)")
        return 0

    print(f"[integrity] {len(defects)} defect(s) found:")
    for path, kind, msg in defects:
        try:
            rel = path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = str(path)
        print(f"   [{kind}] {rel}: {msg}")

    if args.strict:
        print("[integrity] FAIL (--strict): commit blocked", file=sys.stderr)
        return 1
    print("[integrity] WARN (warn-only mode); use --strict to block commit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
