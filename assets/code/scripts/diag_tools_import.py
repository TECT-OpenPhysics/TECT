"""
One-shot diagnostic: why can/can't Python find the `tools/` package?

Purpose: 2026-04-22 — on the user's Windows / Python 3.12 environment,
`python -m tools.check_jacobian_symmetry` fails with
`ModuleNotFoundError: No module named 'tools'`, while `python -m PDE.xxx`
succeeds in the same shell. This script prints exactly what Python sees
so the cause (sys.path omission / case collision / file-visibility /
PYTHONSAFEPATH) can be pinpointed.

Usage: python scripts/diag_tools_import.py
"""
from __future__ import annotations

import os
import sys


def main() -> int:
    print("=" * 70)
    print("Tools-import diagnostic")
    print("=" * 70)

    print(f"Python executable : {sys.executable}")
    print(f"Python version    : {sys.version.split()[0]}")
    print(f"cwd               : {os.getcwd()}")
    print(f"PYTHONSAFEPATH    : {os.environ.get('PYTHONSAFEPATH', '(unset)')}")
    print(f"PYTHONPATH        : {os.environ.get('PYTHONPATH', '(unset)')}")

    print("\nsys.path (ordered):")
    for i, p in enumerate(sys.path):
        print(f"  [{i}] {p!r}")

    print("\nFilesystem view from cwd:")
    for name in ("tools", "PDE"):
        full = os.path.abspath(name)
        exists = os.path.isdir(name)
        print(f"  {name}/ → exists={exists}, abspath={full}")
        if exists:
            listing = os.listdir(name)
            print(f"    listdir → {listing[:6]}{'...' if len(listing) > 6 else ''}")
            init = os.path.join(name, "__init__.py")
            print(f"    __init__.py present: {os.path.isfile(init)}")
            if os.path.isfile(init):
                try:
                    sz = os.path.getsize(init)
                    print(f"    __init__.py size: {sz} bytes")
                except OSError as e:
                    print(f"    __init__.py size: READ ERROR ({e})")

    print("\nImport attempts:")
    for name in ("tools", "PDE"):
        try:
            mod = __import__(name)
            origin = getattr(mod, "__file__", "(namespace package)")
            path = getattr(mod, "__path__", None)
            print(f"  import {name}  →  OK, __file__={origin}, __path__={path}")
        except Exception as e:
            print(f"  import {name}  →  FAIL: {type(e).__name__}: {e}")

    # Also try the submodule we actually care about
    print("\nSubmodule import attempt:")
    try:
        from tools import check_jacobian_symmetry as cjs
        print(f"  from tools import check_jacobian_symmetry  →  OK")
        print(f"    module file: {cjs.__file__}")
    except Exception as e:
        print(f"  from tools import check_jacobian_symmetry  →  FAIL: "
              f"{type(e).__name__}: {e}")

    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
