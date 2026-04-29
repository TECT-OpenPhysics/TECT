"""
build_version_index.py
----------------------
Auto-generate Website/data/version_index.json from the canonical sources:

  1. CHANGELOG.md                       -- current theory_tag, regime, changelog_versions[]
  2. PDE/stamp_version_headers.py       -- MODULE_VERSIONS dict (module -> vN.M)
  3. docs/status/TECT-Theory-Code-Sync.md -- open/closed discrepancies
  4. docs/math/TECT-Math*.tex.txt       -- math note inventory

Run:
    python tools/build_version_index.py            # writes Website/data/version_index.json
    python tools/build_version_index.py --check    # exits non-zero if the file on disk is stale

This script is deliberately dependency-free (stdlib only) so it can run in CI
or as a pre-commit hook without a virtualenv.

Author: TECT project, 2026-04-15.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
STAMPER = ROOT / "PDE" / "stamp_version_headers.py"
SYNC_DOC = ROOT / "docs" / "status" / "TECT-Theory-Code-Sync.md"
MATH_DIR = ROOT / "docs" / "math"
OUT = ROOT / "Website" / "data" / "version_index.json"

THEORY_TAG_RE = re.compile(r"`(Math\d+-[A-Za-z0-9\-]+-\d{4}-\d{2}-\d{2})`")
REGIME_RE = re.compile(r"\*\*regime\*\*\s*[:=]\s*([A-Za-z\-]+)", re.I)
VERSION_HDR_RE = re.compile(r"^##\s+[`\[](Math\d+[a-z]?-[^\]`]+)[`\]].*?(\d{4}-\d{2}-\d{2})", re.M)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def current_theory_tag(changelog: str) -> str:
    m = VERSION_HDR_RE.search(changelog)
    if not m:
        raise RuntimeError("No Math-tag version header found in CHANGELOG.md")
    return m.group(1)


def parse_changelog_versions(changelog: str) -> list[dict]:
    out = []
    for m in VERSION_HDR_RE.finditer(changelog):
        out.append({"tag": m.group(1), "date": m.group(2)})
    return out


def parse_module_versions(stamper: str) -> dict[str, str]:
    """Extract the MODULE_VERSIONS dict via AST without importing the file."""
    try:
        tree = ast.parse(stamper)
    except SyntaxError:
        return {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "MODULE_VERSIONS":
                    if isinstance(node.value, ast.Dict):
                        return {
                            ast.literal_eval(k): ast.literal_eval(v)
                            for k, v in zip(node.value.keys, node.value.values)
                        }
    return {}


def parse_discrepancies(sync_doc: str) -> dict[str, list[str]]:
    """Return {'closed': [...], 'open': [...]}; crude but sufficient."""
    closed, open_ = [], []
    for line in sync_doc.splitlines():
        m = re.match(r"\s*[-*]\s*\*\*(D\d+)\*\*", line)
        if not m:
            continue
        did = m.group(1)
        low = line.lower()
        if "closed" in low or "\u2713" in line or "✅" in line:
            closed.append(did)
        elif "open" in low or "pending" in low:
            open_.append(did)
    return {"closed": sorted(set(closed)), "open": sorted(set(open_))}


def math_note_inventory() -> list[dict]:
    out = []
    if not MATH_DIR.exists():
        return out
    for p in sorted(MATH_DIR.glob("TECT-Math*.tex.txt")):
        out.append({"id": p.stem.replace(".tex", ""), "path": str(p.relative_to(ROOT))})
    return out


def build_index() -> dict:
    changelog = read(CHANGELOG)
    stamper = read(STAMPER)
    sync_doc = read(SYNC_DOC)

    theory_tag = current_theory_tag(changelog)
    # Regime is the most recent Math-tag that names one. Infrastructure-only
    # tags (e.g. Math39-Reorg) inherit the physics-locked regime from the
    # previous entry in CHANGELOG.md.
    regime = "Unknown"
    for tag in [theory_tag] + [v["tag"] for v in parse_changelog_versions(changelog)]:
        if "Brazovskii" in tag:
            regime = "Brazovskii"; break
        if "GL" in tag or "Ginzburg" in tag:
            regime = "Ginzburg-Landau"; break

    index = {
        "_schema": "tect-version-index/1.1",
        "_generator": "tools/build_version_index.py",
        "_generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "current": {"theory_tag": theory_tag, "regime": regime},
        "modules": [
            {"file": f, "module_version": v} for f, v in sorted(parse_module_versions(stamper).items())
        ],
        "discrepancies": parse_discrepancies(sync_doc),
        "changelog_versions": parse_changelog_versions(changelog),
        "math_notes": math_note_inventory(),
    }
    return index


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="exit 1 if on-disk file is stale")
    args = ap.parse_args()

    new = build_index()
    new_text = json.dumps(new, indent=2, ensure_ascii=False)

    if args.check:
        if not OUT.exists():
            print(f"STALE: {OUT} does not exist", file=sys.stderr)
            return 1
        old_text = OUT.read_text(encoding="utf-8")
        # compare ignoring the timestamp field
        def strip_ts(s: str) -> str:
            return re.sub(r'"_generated_utc":\s*"[^"]+"', '"_generated_utc": ""', s)
        if strip_ts(new_text).rstrip() != strip_ts(old_text).rstrip():
            print(f"STALE: {OUT} is out of sync with source", file=sys.stderr)
            return 1
        print(f"OK: {OUT} is in sync")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(new_text + "\n", encoding="utf-8")
    print(f"wrote {OUT}  [theory_tag={new['current']['theory_tag']}, modules={len(new['modules'])}, math_notes={len(new['math_notes'])}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
