#!/usr/bin/env python3
# =====================================================================
# verify_website.py — Website completeness + correctness verifier.
#
# Binding from 2026-04-29 (CLAUDE.md §6.3.7). Run as the LAST step of
# every commit that touches Website/ files. Refuses to exit 0 if any
# of the following defects are detected:
#
#   1. JavaScript syntax errors in Website/data/*.js (Node-based parse,
#      with regex-based fallback when node is unavailable in sandbox).
#   2. Broken download links (href="assets/.../X" pointing to a file
#      not present in Website/assets/).
#   3. Missing HTML wrappers (every Website/data/<page>.js needs a
#      Website/<page>.html that loads it).
#   4. Stale manifest (Website/assets/manifest.json count != actual
#      Website/assets/ recursive file count).
#   5. Stale auto-generated pages (math-notes.js source count !=
#      Docs/math/TECT-Math*.tex.txt count, etc.).
#   6. Empty TECT_<NAME> object — common symptom of escape bugs that
#      break the JS string concatenation chain.
#
# Usage:
#   python -u Codes/tools/verify_website.py            # exits 1 on any defect
#   python -u Codes/tools/verify_website.py --json     # machine-readable
#   python -u Codes/tools/verify_website.py --warn-only  # warnings, no fail
#
# Author: Jusang Lee + collaboration (2026-04-29).
# =====================================================================

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
WEBSITE = ROOT / "Website"
ASSETS = WEBSITE / "assets"
DATA = WEBSITE / "data"
DOCS_MATH = ROOT / "Docs" / "math"

errors: list[str] = []
warnings: list[str] = []

# ---------------------------------------------------------------------
# Check 1: JS syntax. We use a regex pre-screen; full parse via node if
# available. The regex catches the canonical escape bugs that bit us
# on 2026-04-29 (results.js empty).
# ---------------------------------------------------------------------
def check_js_syntax(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    # Bug pattern: '"<p>...<a href="assets/...' — embedded unescaped " in
    # an HTML attribute value INSIDE a "..." JS string. Look for `href="`
    # NOT preceded by backslash inside an unbalanced string.
    bad = re.findall(r'(?<!\\)href="(?!`)', text)
    # The "(?!`)" excludes template literals (rare in this project).
    if bad:
        # False-positive guard: only flag if the file is a TECT_<NAME> data
        # file (where everything sits inside JS strings).
        if path.name.endswith(".js") and re.search(r"window\.TECT_[A-Z_]+\s*=", text):
            errors.append(
                f"[js-syntax] {path.relative_to(ROOT)}: "
                f"found {len(bad)} unescaped `href=\"` patterns "
                f"(probable JS string-termination bug; see CLAUDE.md §6.3.7 lesson on results.js 2026-04-29)"
            )
    # Also: try node if available
    if subprocess.run(["which", "node"], capture_output=True).returncode == 0:
        result = subprocess.run(
            ["node", "--check", str(path)],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            errors.append(
                f"[js-syntax-node] {path.relative_to(ROOT)}: "
                f"node --check failed: {result.stderr.strip().splitlines()[0] if result.stderr.strip() else '?'}"
            )


# ---------------------------------------------------------------------
# Check 2: Broken download links.
# ---------------------------------------------------------------------
def check_download_links() -> None:
    """v0.2 (2026-04-29): scan only HTML-attribute href= patterns; skip
    matches that fall inside narrative body: "..." strings or inside
    backticked code spans (those are descriptive prose, not real links)."""
    href_re = re.compile(r'href=\\?"(assets/[^"\\]+)\\?"\s+download', re.IGNORECASE)
    href_plain = re.compile(r'href=\\?"(assets/[^"\\]+)\\?"', re.IGNORECASE)
    for js in sorted(DATA.glob("*.js")):
        text = js.read_text(encoding="utf-8", errors="replace")
        # Strip narrative body: "..." strings and `code spans` to suppress
        # prose-text false positives. body: lines in history.js contain
        # literal "<details>" and example href="assets/X" descriptions.
        text_clean = re.sub(r'body:\s*"(?:[^"\\]|\\.)*"', '', text)
        text_clean = re.sub(r'`[^`]+`', '', text_clean)
        all_refs = set(href_re.findall(text_clean)) | set(href_plain.findall(text_clean))
        for ref in all_refs:
            target = WEBSITE / ref
            if not target.exists():
                errors.append(
                    f"[broken-link] {js.name}: href=\"{ref}\" → {target.relative_to(ROOT)} not found"
                )


# ---------------------------------------------------------------------
# Check 3: HTML wrapper present for each data/*.js page.
# ---------------------------------------------------------------------
def check_html_wrappers() -> None:
    skip = {"site.js", "_archive", "_narrative", "version_index.json"}
    for js in sorted(DATA.glob("*.js")):
        if js.name in skip:
            continue
        # Map page name: page.js → page.html (special: math-notes.js → math-notes.html)
        page = js.stem  # e.g. "results"
        html = WEBSITE / f"{page}.html"
        if not html.exists():
            warnings.append(
                f"[no-html] {js.name}: Website/{page}.html missing (data file may be unreachable)"
            )


# ---------------------------------------------------------------------
# Check 4: manifest.json freshness.
# ---------------------------------------------------------------------
def check_manifest_freshness() -> None:
    mf = ASSETS / "manifest.json"
    if not mf.exists():
        errors.append("[manifest] Website/assets/manifest.json missing")
        return
    try:
        m = json.loads(mf.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"[manifest-parse] {exc}")
        return
    declared = m.get("count", -1)
    actual = sum(1 for p in ASSETS.rglob("*") if p.is_file() and p.name != "manifest.json")
    if declared != actual:
        errors.append(
            f"[manifest-stale] declared={declared} actual={actual} "
            f"(re-run: python Codes/tools/verify_website.py --regen-manifest)"
        )


# ---------------------------------------------------------------------
# Check 5: Auto-generated pages source-count freshness.
# ---------------------------------------------------------------------
def check_auto_freshness() -> None:
    # math-notes.js should mention Docs/math TECT-Math*.tex.txt count
    mn = DATA / "math-notes.js"
    if mn.exists():
        text = mn.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"Source:\s*Docs/math/TECT-Math\*\.tex\.txt\s*\((\d+)\s*files\)", text)
        if m:
            declared = int(m.group(1))
            actual = sum(1 for _ in DOCS_MATH.glob("TECT-Math*.tex.txt"))
            if declared != actual:
                errors.append(
                    f"[stale-mathnotes] math-notes.js declares {declared} TECT-Math*.tex.txt, "
                    f"Docs/math/ has {actual} (re-run: python Codes/tools/generate_website.py --math-notes)"
                )


# ---------------------------------------------------------------------
# Check 6: Empty TECT_<NAME> objects (escape bug symptom).
# ---------------------------------------------------------------------
_HANGUL_RE = re.compile(r"[ᄀ-ᇿ㄰-㆏가-힣]+")


def check_korean_text(strict: bool = False) -> None:
    """v0.3 (2026-04-29): English-only output policy enforcement.

    Source: ``Docs/policy/OUTPUT_LANGUAGE_POLICY.md`` (binding) +
    ``CLAUDE.md`` §5.1. Website tier (Website/data/*.js, narrative .md,
    Website/*.html) is enforced as ERROR (always). Docs/Codes/CHANGELOG
    tier is enforced as WARNING but only when ``strict=True``
    (--korean-strict flag) — the historical archive is large and slow
    to scan; the default-fast path runs only the Website-tier check.
    """
    # Tier 1 (ERROR): Website tier
    web_paths = []
    for p in DATA.rglob("*.js"):
        web_paths.append(p)
    narr = DATA / "_narrative"
    if narr.exists():
        for p in narr.rglob("*.md"):
            web_paths.append(p)
    for p in WEBSITE.glob("*.html"):
        web_paths.append(p)
    for fp in web_paths:
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        m = _HANGUL_RE.search(text)
        if m:
            line_no = text[: m.start()].count("\n") + 1
            sample = m.group(0)[:30]
            errors.append(
                f"[korean-text] {fp.relative_to(ROOT).as_posix()}:{line_no}: "
                f"Hangul detected (\"{sample}\") — Website tier is English-only "
                f"(Docs/policy/OUTPUT_LANGUAGE_POLICY.md)"
            )

    if not strict:
        return  # default-fast path: skip the heavy Docs/Codes scan

    # Tier 2 (WARN, strict mode): Docs/Codes/CHANGELOG tier (excluding archives)
    EXEMPT_PATTERNS = (
        "Website/assets/math/",  # historical Korean-summary archives
        "Docs/postmortem/2026-04-29-results-empty-and-notes-broken.md",  # verbatim trigger quote
        "Codes/tools/verify_website.py",  # this file's exempt list
        "Docs/policy/OUTPUT_LANGUAGE_POLICY.md",  # the policy lists Hangul ranges itself
        "Docs/policy/STATUS_NOMENCLATURE.md",  # legacy-label translation table
        "CLAUDE.md",  # references the policy
    )
    docs = ROOT / "Docs"
    codes = ROOT / "Codes"
    changelog = ROOT / "CHANGELOG.md"
    candidates = []
    if docs.exists():
        for ext in (".md", ".tex.txt", ".txt"):
            for p in docs.rglob("*" + ext):
                candidates.append(p)
    if codes.exists():
        for ext in (".py", ".sh", ".ps1", ".bat", ".md"):
            for p in codes.rglob("*" + ext):
                candidates.append(p)
    if changelog.exists():
        candidates.append(changelog)
    for fp in candidates:
        rel = fp.relative_to(ROOT).as_posix()
        if any(rel.startswith(pat) or rel == pat for pat in EXEMPT_PATTERNS):
            continue
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        m = _HANGUL_RE.search(text)
        if m:
            line_no = text[: m.start()].count("\n") + 1
            sample = m.group(0)[:30]
            warnings.append(
                f"[korean-text] {rel}:{line_no}: Hangul detected (\"{sample}\")"
            )


def check_details_summary() -> None:
    """v0.2 (2026-04-29): every <details> in Website/ tier MUST have a
    <summary> child element. Without <summary>, browsers (esp. ko-KR
    locale Chrome) render the disclosure widget with auto-translated
    label "세부정보", which is not English.
    """
    for js in sorted(DATA.glob("*.js")):
        try:
            text = js.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # Skip matches inside narrative body: "..." prose and `code spans`
        # — those are descriptions of the verifier itself, not real DOM.
        text_clean = re.sub(r'body:\s*"(?:[^"\\]|\\.)*"', '', text)
        text_clean = re.sub(r'`[^`]+`', '', text_clean)
        for m in re.finditer(r"<details[^>]*>", text_clean):
            after = text_clean[m.end() : m.end() + 80]
            if "<summary" not in after:
                line_no = text_clean[: m.start()].count("\n") + 1
                errors.append(
                    f"[details-no-summary] {js.name}:{line_no}: "
                    f"<details> without <summary> — browser ko-KR locale renders "
                    f"as \"\\uc138\\ubd80\\uc815\\ubcf4\" (auto-translated). Add <summary>...</summary>."
                )


def check_empty_tect_objects() -> None:
    """v0.2 (2026-04-29): the empty-blocks regex must skip matches inside
    narrative body: "..." prose, where literal text like 'blocks: []'
    appears as part of a bug-fix description."""
    for js in sorted(DATA.glob("*.js")):
        if js.name in ("site.js", "version_index.json"):
            continue
        text = js.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"window\.TECT_[A-Z_]+\s*=\s*(\{.*?\});?\s*$", text, re.DOTALL)
        if not m:
            warnings.append(f"[no-tect-object] {js.name}: no `window.TECT_<NAME> = {{...}}` found")
            continue
        body = m.group(1)
        body_clean = re.sub(r'body:\s*"(?:[^"\\]|\\.)*"', '', body)
        body_clean = re.sub(r'`[^`]+`', '', body_clean)
        # Heuristic: if blocks: [] is empty, the page is empty
        if re.search(r"blocks:\s*\[\s*\]", body_clean):
            errors.append(f"[empty-blocks] {js.name}: blocks: [] is empty (page will render nothing)")


# ---------------------------------------------------------------------
# Optional helpers
# ---------------------------------------------------------------------
def regen_manifest() -> int:
    """Regenerate Website/assets/manifest.json from actual file tree."""
    import datetime as _dt
    manifest = {
        "generated_utc": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema": "tect-asset-manifest-v1",
        "files": [],
    }
    for root, dirs, files in os.walk(ASSETS):
        for fn in sorted(files):
            if fn == "manifest.json":
                continue
            p = Path(root) / fn
            rel = p.relative_to(ASSETS).as_posix()
            manifest["files"].append({
                "path": rel,
                "bytes": p.stat().st_size,
                "mtime_utc": _dt.datetime.utcfromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
    manifest["count"] = len(manifest["files"])
    manifest["total_bytes"] = sum(f["bytes"] for f in manifest["files"])
    (ASSETS / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest["count"]


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--warn-only", action="store_true", help="exit 0 even on errors")
    parser.add_argument("--regen-manifest", action="store_true",
                        help="regenerate Website/assets/manifest.json from actual tree")
    parser.add_argument("--korean-strict", action="store_true",
                        help="also scan Docs/, Codes/, CHANGELOG.md for Hangul (slow)")
    args = parser.parse_args()

    if args.regen_manifest:
        n = regen_manifest()
        print(f"[regen] manifest.json: {n} files")

    print("=" * 60)
    print(" Website verifier (CLAUDE.md §6.3.7)")
    print("=" * 60)

    # Run checks
    print("[1/8] JS syntax …")
    for js in sorted(DATA.glob("*.js")):
        check_js_syntax(js)
    print("[2/8] Download links …")
    check_download_links()
    print("[3/8] HTML wrappers …")
    check_html_wrappers()
    print("[4/8] Manifest freshness …")
    check_manifest_freshness()
    print("[5/8] Auto-page source counts …")
    check_auto_freshness()
    print("[6/8] Empty TECT_<NAME> blocks …")
    check_empty_tect_objects()
    print("[7/8] Korean text (English-only policy, OUTPUT_LANGUAGE_POLICY.md) …")
    check_korean_text(strict=args.korean_strict)
    print("[8/8] <details>/<summary> pairing (ko-KR auto-translate guard) …")
    check_details_summary()

    print()
    print(f"errors:   {len(errors)}")
    print(f"warnings: {len(warnings)}")

    if args.json:
        print(json.dumps({"errors": errors, "warnings": warnings}, indent=2, ensure_ascii=False))
    else:
        for e in errors:
            print(f"  ERR  {e}")
        for w in warnings:
            print(f"  warn {w}")

    if errors and not args.warn_only:
        print()
        print("FAIL: website verification failed. Fix the errors above before commit.")
        return 1
    print()
    print("OK: website verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
