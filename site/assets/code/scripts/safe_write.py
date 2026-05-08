#!/usr/bin/env python3
# =====================================================================
# safe_write.py — atomic file-write helper that bypasses Edit/Write
# tool truncation issues observed across 2026-04 / 2026-05 sessions.
#
# Root cause being addressed
# --------------------------
# The Edit and Write tools used by AI collaborators perform a
# non-atomic write: an OS-level `write()` call that, when interrupted
# (by a system-reminder mid-stream, by the harness flushing too early,
# by encoding hiccups), leaves the file in a half-written state. The
# observed failure modes are:
#
#   (a) Trailing NUL bytes (Write-tool padding artefact).
#   (b) Mid-line truncation that drops the last N lines of the file
#       (Edit-tool interrupt artefact).
#   (c) String-literal terminated mid-quote (PowerShell line-595
#       'prec... pattern).
#
# The fix is to write to a temp file in the same directory, fsync it,
# then atomically rename. POSIX `os.replace()` and Windows `MoveFileEx`
# (which Python wraps via os.replace) are both atomic — the rename
# either fully succeeds (file is the new content) or fully fails
# (file is unchanged). There is no half-written intermediate state
# observable by another reader.
#
# Usage from Bash (replaces Edit/Write for non-trivial files):
# ------------------------------------------------------------
#   python3 Codes/scripts/safe_write.py PATH < content_via_stdin
#
#   # Or use Python heredoc directly (preferred for AI collaborators):
#   python3 <<'EOF'
#   from Codes.scripts.safe_write import atomic_write
#   atomic_write('Codes/tools/foo.py', '''<full file content>''')
#   EOF
#
# Usage as a library (preferred when AI generates content):
# ---------------------------------------------------------
#   import sys
#   sys.path.insert(0, 'Codes/scripts')
#   from safe_write import atomic_write, atomic_replace_in_file
#   atomic_write(path, content)
#   atomic_replace_in_file(path, old_substr, new_substr)
#
# CLI:
#   python3 Codes/scripts/safe_write.py PATH                 # read content from stdin
#   python3 Codes/scripts/safe_write.py PATH --content STR   # inline content (small)
#   python3 Codes/scripts/safe_write.py PATH --replace OLD NEW  # in-place replace
#   python3 Codes/scripts/safe_write.py --verify PATH        # NUL/truncation sanity check
#
# Exit codes:
#   0  OK
#   1  verification failed (file has NUL padding or syntax error)
#   2  I/O error
# =====================================================================
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional


def atomic_write(path: str | os.PathLike, content: str,
                  encoding: str = "utf-8") -> None:
    """Write `content` to `path` atomically. The function:
       1. Encodes content to bytes.
       2. Strips any trailing NUL bytes (defensive against caller bugs).
       3. Writes to a temp file in the SAME directory (same filesystem).
       4. fsyncs the temp file's content + directory.
       5. Atomically replaces `path` with the temp file via os.replace.
    If the function returns successfully, `path` contains exactly the
    bytes of `content`. If it raises, `path` is unchanged.
    """
    path = Path(path)
    data = content.encode(encoding)
    # Strip trailing NULs defensively
    data = data.rstrip(b"\x00")

    parent = path.parent if path.parent != Path("") else Path(".")
    parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file in the same directory (same filesystem -> atomic rename)
    fd, tmp_path = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp",
                                     dir=str(parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass  # some filesystems do not support fsync
        # Atomic replace
        os.replace(tmp_path, path)
    except Exception:
        # Clean up temp file on any failure; original file unchanged
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def atomic_replace_in_file(path: str | os.PathLike, old: str, new: str,
                            count: int = -1, encoding: str = "utf-8") -> int:
    """Read `path`, replace `old` with `new` (up to `count` times; -1 = all),
    and atomic-write back. Returns the number of replacements performed.
    Raises if `old` is not found at least once."""
    path = Path(path)
    text = path.read_text(encoding=encoding)
    if old not in text:
        raise ValueError(f"old_string not found in {path}")
    if count < 0:
        new_text = text.replace(old, new)
        n = text.count(old)
    else:
        new_text = text.replace(old, new, count)
        n = min(text.count(old), count)
    atomic_write(path, new_text, encoding=encoding)
    return n


def verify(path: str | os.PathLike) -> Optional[str]:
    """Sanity-check a file. Returns None if OK, an error message otherwise."""
    path = Path(path)
    if not path.exists():
        return f"file does not exist: {path}"
    data = path.read_bytes()
    if data.endswith(b"\x00"):
        n = 0
        for b in reversed(data):
            if b == 0:
                n += 1
            else:
                break
        return f"trailing NUL padding: {n} bytes"
    suffix = path.suffix.lower()
    if suffix == ".py":
        try:
            import ast
            ast.parse(data.decode("utf-8", errors="replace"))
        except SyntaxError as exc:
            return f"Python parse error at line {exc.lineno}: {exc.msg}"
    elif suffix == ".json":
        try:
            import json
            json.loads(data.decode("utf-8", errors="replace"))
        except Exception as exc:
            return f"JSON parse error: {exc}"
    return None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", help="target file path")
    p.add_argument("--content", help="inline content; if absent, read from stdin")
    p.add_argument("--replace", nargs=2, metavar=("OLD", "NEW"),
                   help="in-place text replacement instead of full write")
    p.add_argument("--verify", action="store_true",
                   help="sanity-check the file (NUL / parse) and exit")
    p.add_argument("--encoding", default="utf-8")
    args = p.parse_args()

    if args.verify:
        msg = verify(args.path)
        if msg:
            print(f"FAIL [{args.path}]: {msg}", file=sys.stderr)
            return 1
        print(f"OK [{args.path}] no defects")
        return 0

    try:
        if args.replace:
            old, new = args.replace
            n = atomic_replace_in_file(args.path, old, new, encoding=args.encoding)
            print(f"OK replaced {n} occurrence(s) in {args.path}")
        else:
            content = args.content if args.content is not None else sys.stdin.read()
            atomic_write(args.path, content, encoding=args.encoding)
            print(f"OK wrote {len(content)} chars to {args.path}")
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    # Post-write verification
    msg = verify(args.path)
    if msg:
        print(f"WARN post-write verify: {msg}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
