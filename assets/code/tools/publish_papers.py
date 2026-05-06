#!/usr/bin/env python3
# =====================================================================
# publish_papers.py — Layer 1.5 of the publish pipeline (offline).
#
# Sweeps every Paper-NN.pdf produced by the LaTeX build and copies it
# into the public mirror Github/assets/papers/ under category-aware
# subfolders, then regenerates Website/data/papers_pdf_index.js so that
# the website's Papers page can render download links automatically.
#
# Source layout (input):
#   Docs/papers/papers/Paper-NN-*/Paper-NN.pdf       (Wave 1-7 main)
#   Docs/papers/auxiliary/Auxiliary-NN-*/Auxiliary-NN.pdf
#   Docs/papers/top_impact/Paper-TI-N-*/Paper-TI-N.pdf
#   Docs/papers/epochs/Epoch-NN-*/Epoch-NN.pdf       (chronological)
#
# Mirror layout (output):
#   Github/assets/papers/papers/Paper-NN.pdf
#   Github/assets/papers/auxiliary/Auxiliary-NN.pdf
#   Github/assets/papers/top_impact/Paper-TI-N.pdf
#   Github/assets/papers/epochs/Epoch-NN.pdf
#
# Index generated:
#   Website/data/papers_pdf_index.js  (window.TECT_PAPERS_PDF_INDEX = {...})
#
# Invariants (mirror github_sync_curate.py)
#   I1  No network. This step is fully offline.
#   I2  Idempotent. Re-running with the same inputs produces the same
#       output (mtime-checked; only changed PDFs are re-copied).
#   I3  Never touches Github/.git/.
#   I4  English-only output.
#
# CLI
#   python -u Codes/tools/publish_papers.py            # build + index
#   python -u Codes/tools/publish_papers.py --check    # dry-run
#   python -u Codes/tools/publish_papers.py --clean    # wipe target first
#   python -u Codes/tools/publish_papers.py -v         # verbose deltas
#
# Exit codes
#   0   OK
#   1   one or more PDFs missing where the .tex source exists
#   2   I/O error during copy
#   3   index write failed
# =====================================================================
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT  = Path(__file__).resolve().parent.parent.parent
DOCS_PAPERS = REPO_ROOT / "Docs" / "papers"
TARGET     = REPO_ROOT / "Github" / "assets" / "papers"
WEBSITE    = REPO_ROOT / "Website"
INDEX_JS   = WEBSITE / "data" / "papers_pdf_index.js"
PUBLIC_BASE_URL = "assets/papers"   # relative to Github/ root (matches site layout)

# ---------------------------------------------------------------------
# Category configuration
# ---------------------------------------------------------------------
CATEGORIES: List[Tuple[str, str, str, str]] = [
    # (key, source_subdir, dirname_glob, stem_glob)
    ("papers",     "papers",      "Paper-*",     "Paper-*"),
    ("auxiliary",  "auxiliary",   "Auxiliary-*", "Auxiliary-*"),
    ("top_impact", "top_impact",  "Paper-TI-*",  "Paper-TI-*"),
    ("epochs",     "epochs",      "Epoch-*",     "Epoch-*"),
]

# Category metadata for the website index
CATEGORY_META: Dict[str, Dict[str, str]] = {
    "papers": {
        "label": "Pillar papers",
        "subtitle": "Wave 1-7 main proof papers, one per pillar / GAP-track."
    },
    "auxiliary": {
        "label": "Auxiliary notes",
        "subtitle": "Background and methodology notes (Brazovskii universality, numerical solver)."
    },
    "top_impact": {
        "label": "Top-impact papers",
        "subtitle": "Algebraic-geometry foundation papers (HRR index, BCC uniqueness, A2 reclassification, CP^2 cohomology)."
    },
    "epochs": {
        "label": "Epoch retrospectives",
        "subtitle": "Chronological audit-cycle records (Math01-Math209 archive)."
    },
}


def discover_papers(verbose: bool = False) -> List[Tuple[str, Path, Path, str]]:
    """
    Returns: list of (category, src_pdf, src_dir, stem)
    Skips directories without a matching PDF; warns if .tex exists but PDF missing.
    """
    results: List[Tuple[str, Path, Path, str]] = []
    missing: List[Path] = []
    for key, subdir, dir_glob, stem_glob in CATEGORIES:
        cat_root = DOCS_PAPERS / subdir
        if not cat_root.is_dir():
            continue
        for d in sorted(cat_root.iterdir()):
            if not d.is_dir() or d.name.startswith("_"):
                continue
            from fnmatch import fnmatch
            if not fnmatch(d.name, dir_glob):
                continue
            # Find the canonical .tex / .pdf stem inside this dir
            for tex in sorted(d.glob(f"{stem_glob}.tex")):
                stem = tex.stem
                pdf  = d / f"{stem}.pdf"
                if pdf.is_file():
                    results.append((key, pdf, d, stem))
                else:
                    missing.append(tex)
                    if verbose:
                        print(f"  [missing PDF] {tex.relative_to(REPO_ROOT)}")
    if missing:
        print(f"[publish-papers] WARN: {len(missing)} .tex without matching .pdf "
              f"(run build-all-papers first)")
    return results


def copy_pdfs(pdfs: List[Tuple[str, Path, Path, str]],
              clean: bool = False, dry_run: bool = False,
              verbose: bool = False) -> Dict[str, int]:
    """Copy PDFs into Github/assets/papers/<category>/<stem>.pdf with mtime
    preservation; only re-copies if source is newer or destination missing."""
    counts = {"added": 0, "updated": 0, "unchanged": 0, "removed": 0, "errors": 0}
    if clean and TARGET.exists() and not dry_run:
        # Wipe but preserve .git (none here) — just remove the whole tree
        shutil.rmtree(TARGET)
    if not dry_run:
        TARGET.mkdir(parents=True, exist_ok=True)

    # Track expected destinations to detect orphans
    expected_dests = set()
    for cat, src_pdf, src_dir, stem in pdfs:
        dest_dir = TARGET / cat
        dest = dest_dir / f"{stem}.pdf"
        expected_dests.add(dest.resolve())
        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
        # Decide action
        if not dest.exists():
            action = "added"
        else:
            src_mtime  = src_pdf.stat().st_mtime
            dest_mtime = dest.stat().st_mtime
            src_size   = src_pdf.stat().st_size
            dest_size  = dest.stat().st_size
            if src_mtime > dest_mtime + 1.0 or src_size != dest_size:
                action = "updated"
            else:
                action = "unchanged"
        if verbose or action != "unchanged":
            print(f"  [{action:9s}] {cat:<11s} {stem}.pdf"
                  f" ({src_pdf.stat().st_size//1024} KB)")
        if action != "unchanged":
            try:
                if not dry_run:
                    shutil.copy2(src_pdf, dest)
            except OSError as exc:
                print(f"  [ERROR copy] {src_pdf} -> {dest}: {exc}",
                      file=sys.stderr)
                counts["errors"] += 1
                continue
        counts[action] += 1

    # Detect orphans (existing PDFs in TARGET that no longer have a source)
    if TARGET.exists():
        for existing in TARGET.rglob("*.pdf"):
            if existing.resolve() not in expected_dests:
                if verbose:
                    print(f"  [orphan]    {existing.relative_to(TARGET)}")
                if not dry_run:
                    try:
                        existing.unlink()
                    except OSError as exc:
                        print(f"  [ERROR rm]  {existing}: {exc}", file=sys.stderr)
                        counts["errors"] += 1
                        continue
                counts["removed"] += 1
    return counts


# ---------------------------------------------------------------------
# Helper: extract paper title from .tex (\title{...}) for index rendering
# ---------------------------------------------------------------------
def extract_title(tex_path: Path) -> str:
    """Best-effort extract of \\title{...} (handling multi-line + \\\\ marks)."""
    try:
        text = tex_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return tex_path.stem
    import re
    m = re.search(r'\\title\{', text)
    if not m:
        return tex_path.stem
    # Walk from the opening { matching nesting depth to extract content
    start = m.end()
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        c = text[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                break
        i += 1
    raw = text[start:i]
    # Strip LaTeX line breaks and \normalsize{...} / \textit{...} junk
    raw = re.sub(r'\\\\\s*', ' ', raw)
    raw = re.sub(r'\\normalsize\{[^{}]*\}', '', raw)
    raw = re.sub(r'\\textit\{[^{}]*\}', '', raw)
    raw = re.sub(r'\\\\?[a-zA-Z]+\{', '', raw)   # drop other macros
    raw = raw.replace('}', '').replace('~', ' ')
    raw = ' '.join(raw.split())
    return raw or tex_path.stem


# ---------------------------------------------------------------------
# Index file generator
# ---------------------------------------------------------------------
def write_index_js(pdfs: List[Tuple[str, Path, Path, str]], dry_run: bool = False) -> bool:
    """Emit Website/data/papers_pdf_index.js with the structured index."""
    by_cat: Dict[str, List[Dict[str, object]]] = {k: [] for k, *_ in CATEGORIES}
    for cat, src_pdf, src_dir, stem in pdfs:
        title = extract_title(src_dir / f"{stem}.tex")
        rel = f"{PUBLIC_BASE_URL}/{cat}/{stem}.pdf"
        bytes_size = src_pdf.stat().st_size
        by_cat[cat].append({
            "stem":     stem,
            "title":    title,
            "category": cat,
            "url":      rel,
            "bytes":    bytes_size,
            "kb":       round(bytes_size / 1024, 1),
        })

    payload: Dict[str, object] = {
        "schema":      "tect-papers-pdf-index-v1",
        "generated":   datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "publicBase":  PUBLIC_BASE_URL,
        "categories":  [
            {
                "key":      key,
                "label":    CATEGORY_META[key]["label"],
                "subtitle": CATEGORY_META[key]["subtitle"],
                "papers":   by_cat[key],
            }
            for key, *_ in CATEGORIES
        ],
        "totalPapers": sum(len(v) for v in by_cat.values()),
        "totalBytes":  sum(p["bytes"] for v in by_cat.values() for p in v),
    }

    body = (
        "/* AUTO-GENERATED by Codes/tools/publish_papers.py — DO NOT EDIT. */\n"
        "/* Source: Docs/papers/{papers,auxiliary,top_impact,epochs}/      */\n"
        "/* Mirror: Github/assets/papers/<category>/<stem>.pdf             */\n"
        "window.TECT_PAPERS_PDF_INDEX = "
        + json.dumps(payload, indent=2, ensure_ascii=False)
        + ";\n"
    )

    if dry_run:
        print(f"  [dry-run] would write {INDEX_JS} ({len(body)} bytes)")
        return True
    try:
        INDEX_JS.parent.mkdir(parents=True, exist_ok=True)
        INDEX_JS.write_text(body, encoding="utf-8")
        print(f"  [index]   wrote {INDEX_JS.relative_to(REPO_ROOT)}"
              f" ({payload['totalPapers']} papers, "
              f"{payload['totalBytes']//1024} KB total)")
        return True
    except OSError as exc:
        print(f"  [ERROR]   index write: {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true",
                   help="dry-run: list deltas but do not write")
    p.add_argument("--clean", action="store_true",
                   help="wipe Github/assets/papers/ before rebuilding")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="list per-file actions")
    args = p.parse_args()

    print(" TECT publish-papers — sweep PDFs into Github/assets/papers/")
    print(" Source: Docs/papers/{papers,auxiliary,top_impact,epochs}/")
    print(f" Target: {TARGET.relative_to(REPO_ROOT)}")
    if args.check:
        print(" Mode: --check (dry-run)")

    pdfs = discover_papers(verbose=args.verbose)
    if not pdfs:
        print("[publish-papers] no PDFs found. Run build-all-papers first.")
        return 1
    print(f"[publish-papers] discovered {len(pdfs)} PDFs across "
          f"{len(set(c for c,*_ in pdfs))} categories")

    counts = copy_pdfs(pdfs, clean=args.clean, dry_run=args.check,
                       verbose=args.verbose)
    print(f"[publish-papers] copy summary: "
          f"added={counts['added']} updated={counts['updated']} "
          f"unchanged={counts['unchanged']} removed={counts['removed']} "
          f"errors={counts['errors']}")
    if counts["errors"] > 0:
        return 2

    if not write_index_js(pdfs, dry_run=args.check):
        return 3

    print("[publish-papers] OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
