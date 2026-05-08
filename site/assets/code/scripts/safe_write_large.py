#!/usr/bin/env python3
"""
safe_write_large.py — Robust large-file writer for Cowork mode.

Background
----------
The Cowork mode Write tool exhibits intermittent truncation when writing
large content (typically > 15 KB) to mounted paths. The Windows-side view
sees the full content; the bash-side mount sees the file truncated mid-line
at variable positions (observed truncations at lines 117, 190, 1665, etc.
during 2026-04-26..27 website-restructure work).

The truncation is platform-level (Cowork desktop ↔ bash sandbox file
sync race condition), not a defect in our code. We cannot fix the
underlying cause from our codebase.

This helper provides a reliable workaround pattern: write a target file
by first composing it in pieces under outputs/ (each piece < 10 KB so
truncation is unlikely), then concatenating into the target via bash.

Usage
-----
1. Author your full content as multiple chunks (each < 10 KB):

       chunk1 = "..."  # first ~5KB
       chunk2 = "..."  # next ~5KB
       ...

2. Write each chunk to outputs/ via the Write tool (each is small enough
   to land safely):

       Write outputs/chunk_01.txt with chunk1
       Write outputs/chunk_02.txt with chunk2
       ...

3. Invoke this script from bash:

       python3 Codes/scripts/safe_write_large.py \\
           --target Website/data/some_file.js \\
           --inputs /sessions/.../mnt/outputs/chunk_*.txt

   It concatenates the chunks in lexicographic order, writes the target,
   and verifies the byte count.

Alternative — direct bash heredoc
---------------------------------
For shell-friendly content (no special chars), `cat << 'EOF' > target`
in bash is also reliable. This script handles arbitrary content
including JS template-strings, escape sequences, and unicode.

CLAUDE.md / REPO_LAYOUT integration
-----------------------------------
This pattern is canonical for any file > 15 KB destined for a mounted
path. See CLAUDE.md §13 (file-location discipline) and the
`Website/data/*.js` rev-3..rev-7 development notes for prior incidents.
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", required=True, type=Path,
                        help="Final destination path for the concatenated content.")
    parser.add_argument("--inputs", required=True, nargs='+', type=Path,
                        help="Chunk files to concatenate (in the order given).")
    parser.add_argument("--separator", default="",
                        help="Optional separator string inserted between chunks (default: empty).")
    parser.add_argument("--verify-syntax", choices=["js", "python", "json", "none"], default="none",
                        help="Optional syntax check after writing.")
    args = parser.parse_args()

    # 1. Validate inputs
    for p in args.inputs:
        if not p.exists():
            print(f"[FAIL] missing chunk: {p}", file=sys.stderr)
            sys.exit(2)

    # 2. Concatenate
    parts = []
    total_bytes = 0
    for p in args.inputs:
        chunk = p.read_text(encoding="utf-8")
        parts.append(chunk)
        total_bytes += len(chunk.encode("utf-8"))
        print(f"  [chunk] {p.name}: {len(chunk):>8} chars, {len(chunk.encode('utf-8')):>8} bytes")

    content = args.separator.join(parts)

    # 3. Write target
    args.target.parent.mkdir(parents=True, exist_ok=True)
    args.target.write_text(content, encoding="utf-8", newline="\n")
    written = args.target.stat().st_size
    expected = len(content.encode("utf-8"))
    print(f"  [target] {args.target}: {written} bytes (expected {expected})")

    if written != expected:
        print(f"[FAIL] byte-count mismatch: wrote {written}, expected {expected}", file=sys.stderr)
        sys.exit(3)

    # 4. Optional syntax verification
    if args.verify_syntax == "js":
        import subprocess
        r = subprocess.run(["node", "--check", str(args.target)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[FAIL] node --check failed:\n{r.stderr}", file=sys.stderr)
            sys.exit(4)
        print("  [verify-syntax js] OK")
    elif args.verify_syntax == "python":
        import ast
        try:
            ast.parse(content)
            print("  [verify-syntax python] OK")
        except SyntaxError as e:
            print(f"[FAIL] python syntax: line {e.lineno}: {e.msg}", file=sys.stderr)
            sys.exit(4)
    elif args.verify_syntax == "json":
        import json
        try:
            json.loads(content)
            print("  [verify-syntax json] OK")
        except json.JSONDecodeError as e:
            print(f"[FAIL] json: {e}", file=sys.stderr)
            sys.exit(4)

    print(f"[OK] {args.target.name}: {written} bytes assembled from {len(args.inputs)} chunks")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
