#!/usr/bin/env python3
# =====================================================================
# publish_papers.py v1.1 - sweep Docs/papers/**/Paper-*.pdf into
# Github/assets/papers/<category>/<stem>.pdf and emit
# Website/data/papers_pdf_index.js with per-paper tier + title.
# =====================================================================
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT  = Path(__file__).resolve().parent.parent.parent
DOCS_PAPERS = REPO_ROOT / "Docs" / "papers"
# Two mirror targets (PDFs must exist in BOTH for local + GitHub use):
#   1) Website/assets/papers/  - served by the local site (file:// or
#      a simple HTTP server) and by GitHub Pages (when Website is
#      published as the Pages source).
#   2) Github/assets/papers/   - mirrored into the public GitHub repo
#      via the github_sync_curate.py + publish.ps1 chain.
WEBSITE    = REPO_ROOT / "Website"
TARGET_WEBSITE = WEBSITE / "assets" / "papers"
TARGET_GITHUB  = REPO_ROOT / "Github" / "assets" / "papers"
TARGETS    = [TARGET_WEBSITE, TARGET_GITHUB]
INDEX_JS   = WEBSITE / "data" / "papers_pdf_index.js"
PUBLIC_BASE_URL = "assets/papers"

CATEGORIES: List[Tuple[str, str, str, str]] = [
    ("papers",     "papers",      "Paper-*",     "Paper-*"),
    ("auxiliary",  "auxiliary",   "Auxiliary-*", "Auxiliary-*"),
    ("top_impact", "top_impact",  "Paper-TI-*",  "Paper-TI-*"),
    ("epochs",     "epochs",      "Epoch-*",     "Epoch-*"),
]

CATEGORY_META: Dict[str, Dict[str, str]] = {
    "papers": {
        "label": "Pillar papers",
        "subtitle": "Wave 1-7 main proof papers, one per pillar / GAP-track."
    },
    "auxiliary": {
        "label": "Auxiliary notes",
        "subtitle": "Background and methodology notes."
    },
    "top_impact": {
        "label": "Top-impact papers",
        "subtitle": "Algebraic-geometry foundation papers."
    },
    "epochs": {
        "label": "Epoch retrospectives",
        "subtitle": "Chronological audit-cycle records."
    },
}

# ---- Tier extraction (T0-T7) ---------------------------------------
TIER_OVERRIDE: Dict[str, str] = {
    'Paper-00':     'T6', 'Paper-01':     'T6', 'Paper-02':     'T6',
    'Paper-03':     'T5', 'Paper-04':     'T6', 'Paper-05':     'T7',
    'Paper-06':     'T4', 'Paper-07':     'T2', 'Paper-07-ext': 'T6',
    'Paper-08':     'T4', 'Paper-09':     'T4', 'Paper-10':     'T4',
    'Paper-11':     'T4', 'Paper-12':     'T3', 'Paper-13':     'T4',
    'Paper-14':     'T6', 'Paper-15':     'T6', 'Paper-16':     'T3',
    'Auxiliary-01': 'T2', 'Auxiliary-02': 'T4',
    'Paper-TI-1':   'T7', 'Paper-TI-2':   'T4',
    'Paper-TI-3':   'T6', 'Paper-TI-4':   'T7',
    'Epoch-01':     'T4', 'Epoch-02':     'T4', 'Epoch-03':     'T2',
    'Epoch-04':     'T3', 'Epoch-05':     'T3', 'Epoch-06':     'T3',
    'Epoch-07':     'T4', 'Epoch-08':     'T4', 'Epoch-09':     'T4',
    'Epoch-10':     'T6', 'Epoch-11':     'T3', 'Epoch-12':     'T7',
}


def extract_tier(tex_path: Path, stem: str) -> str:
    if stem in TIER_OVERRIDE:
        return TIER_OVERRIDE[stem]
    return '?'


def extract_title(tex_path: Path) -> str:
    try:
        text = tex_path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return tex_path.stem
    m = re.search(r'\\title\{', text)
    if not m:
        return tex_path.stem
    start = m.end()
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        c = text[i]
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: break
        i += 1
    raw = text[start:i]
    raw = re.sub(r'\\\\\s*', ' ', raw)
    raw = re.sub(r'\\normalsize\{[^{}]*\}', '', raw)
    raw = re.sub(r'\\textit\{[^{}]*\}', '', raw)
    raw = re.sub(r'\\\\?[a-zA-Z]+\{', '', raw)
    raw = raw.replace('}', '').replace('~', ' ')
    raw = ' '.join(raw.split())
    return raw or tex_path.stem


def discover_papers(verbose: bool = False):
    results = []
    missing = []
    from fnmatch import fnmatch
    for key, subdir, dir_glob, stem_glob in CATEGORIES:
        cat_root = DOCS_PAPERS / subdir
        if not cat_root.is_dir():
            continue
        for d in sorted(cat_root.iterdir()):
            if not d.is_dir() or d.name.startswith("_"):
                continue
            if not fnmatch(d.name, dir_glob):
                continue
            for tex in sorted(d.glob(f"{stem_glob}.tex")):
                stem = tex.stem
                pdf  = d / f"{stem}.pdf"
                if pdf.is_file():
                    results.append((key, pdf, d, stem))
                else:
                    missing.append(tex)
    if missing:
        print(f"[publish-papers] WARN: {len(missing)} .tex without matching .pdf")
    return results


def _copy_to_target(target: Path, pdfs, clean: bool, dry_run: bool,
                     verbose: bool, label: str):
    """Copy + orphan-cleanup for a single mirror target."""
    counts = {"added": 0, "updated": 0, "unchanged": 0, "removed": 0, "errors": 0}
    if clean and target.exists() and not dry_run:
        shutil.rmtree(target)
    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)
    expected = set()
    for cat, src_pdf, src_dir, stem in pdfs:
        dest_dir = target / cat
        dest = dest_dir / f"{stem}.pdf"
        expected.add(dest.resolve())
        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
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
            print(f"  [{label}/{action:9s}] {cat:<11s} {stem}.pdf"
                  f" ({src_pdf.stat().st_size//1024} KB)")
        if action != "unchanged":
            try:
                if not dry_run:
                    shutil.copy2(src_pdf, dest)
            except OSError as exc:
                print(f"  [ERROR copy] {src_pdf}: {exc}", file=sys.stderr)
                counts["errors"] += 1
                continue
        counts[action] += 1
    if target.exists():
        for existing in target.rglob("*.pdf"):
            if existing.resolve() not in expected:
                if verbose:
                    print(f"  [{label}/orphan] {existing.relative_to(target)}")
                if not dry_run:
                    try:
                        existing.unlink()
                    except OSError as exc:
                        print(f"  [ERROR rm]  {existing}: {exc}", file=sys.stderr)
                        counts["errors"] += 1
                        continue
                counts["removed"] += 1
    return counts


def copy_pdfs(pdfs, clean=False, dry_run=False, verbose=False):
    """Mirror PDFs to BOTH Website/assets/papers/ AND Github/assets/papers/."""
    total = {"added": 0, "updated": 0, "unchanged": 0, "removed": 0, "errors": 0}
    for target, label in [(TARGET_WEBSITE, "web"), (TARGET_GITHUB, "git")]:
        c = _copy_to_target(target, pdfs, clean=clean, dry_run=dry_run,
                            verbose=verbose, label=label)
        for k, v in c.items():
            total[k] += v
    return total


def write_index_js(pdfs, dry_run=False):
    by_cat = {k: [] for k, *_ in CATEGORIES}
    for cat, src_pdf, src_dir, stem in pdfs:
        tex_path = src_dir / f"{stem}.tex"
        title = extract_title(tex_path)
        tier  = extract_tier(tex_path, stem)
        rel   = f"{PUBLIC_BASE_URL}/{cat}/{stem}.pdf"
        bytes_size = src_pdf.stat().st_size
        by_cat[cat].append({
            "stem": stem, "title": title, "tier": tier, "category": cat,
            "url": rel, "bytes": bytes_size, "kb": round(bytes_size/1024, 1),
        })
    payload = {
        "schema":     "tect-papers-pdf-index-v1.1",
        "generated":  datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "publicBase": PUBLIC_BASE_URL,
        "categories": [
            {"key": k, "label": CATEGORY_META[k]["label"],
             "subtitle": CATEGORY_META[k]["subtitle"], "papers": by_cat[k]}
            for k, *_ in CATEGORIES
        ],
        "totalPapers": sum(len(v) for v in by_cat.values()),
        "totalBytes":  sum(p["bytes"] for v in by_cat.values() for p in v),
    }
    body = (
        "/* AUTO-GENERATED by Codes/tools/publish_papers.py - DO NOT EDIT. */\n"
        "/* Source: Docs/papers/                                            */\n"
        "/* Mirror: Github/assets/papers/                                   */\n"
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


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    p.add_argument("--clean", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()
    print(" TECT publish-papers v1.2 (dual-mirror: Website + Github)")
    print(f" Source : {DOCS_PAPERS.relative_to(REPO_ROOT)}")
    print(f" Mirror1: {TARGET_WEBSITE.relative_to(REPO_ROOT)}  (local site / GitHub Pages)")
    print(f" Mirror2: {TARGET_GITHUB.relative_to(REPO_ROOT)}   (public GitHub mirror)")
    pdfs = discover_papers(verbose=args.verbose)
    if not pdfs:
        return 1
    print(f"[publish-papers] discovered {len(pdfs)} PDFs")
    counts = copy_pdfs(pdfs, clean=args.clean, dry_run=args.check, verbose=args.verbose)
    print(f"[publish-papers] copy: added={counts['added']} "
          f"updated={counts['updated']} unchanged={counts['unchanged']} "
          f"removed={counts['removed']} errors={counts['errors']}")
    if counts["errors"] > 0:
        return 2
    if not write_index_js(pdfs, dry_run=args.check):
        return 3
    print("[publish-papers] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
