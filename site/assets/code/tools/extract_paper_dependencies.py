#!/usr/bin/env python3
# =====================================================================
# extract_paper_dependencies.py v1.0 — Paper <-> Math-note dependency mapper.
#
# Sweeps every paper TeX under Docs/papers/{papers,auxiliary,top_impact,
# epochs}/ and extracts:
#   (a) the "% Canonical archive: ..." header line(s) — the curated
#       authoritative dependency list maintained by the paper author;
#   (b) every \cite{Math...} body reference — empirical dependency
#       evidence;
#   (c) every "MathNN" / "MathNN-AddX" mention in body prose.
#
# Outputs:
#   Docs/status/PAPER-MATH-DEPENDENCIES.md   (forward + reverse maps)
#   Website/data/papers_math_dependencies.js (window.TECT_PAPERS_DEPS)
#
# Validation: every cited Math note must exist as
#   Docs/math/TECT-Math<NN>*.tex.txt
# Missing notes cause exit 1 (override with --no-fail).
#
# CLI:
#   python -u Codes/tools/extract_paper_dependencies.py
#   python -u Codes/tools/extract_paper_dependencies.py --check       # dry-run
#   python -u Codes/tools/extract_paper_dependencies.py -v            # verbose
#   python -u Codes/tools/extract_paper_dependencies.py --no-fail     # don't exit 1
# =====================================================================
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple

REPO_ROOT  = Path(__file__).resolve().parent.parent.parent
DOCS_PAPERS = REPO_ROOT / "Docs" / "papers"
DOCS_MATH   = REPO_ROOT / "Docs" / "math"
WEBSITE     = REPO_ROOT / "Website"
OUT_MD      = REPO_ROOT / "Docs" / "status" / "PAPER-MATH-DEPENDENCIES.md"
OUT_JS      = WEBSITE / "data" / "papers_math_dependencies.js"

CATEGORIES: List[Tuple[str, str, str, str]] = [
    ("papers",     "papers",      "Paper-*",     "Paper-*"),
    ("auxiliary",  "auxiliary",   "Auxiliary-*", "Auxiliary-*"),
    ("top_impact", "top_impact",  "Paper-TI-*",  "Paper-TI-*"),
    ("epochs",     "epochs",      "Epoch-*",     "Epoch-*"),
]

# Regex: MathNN / MathNN-AddX / MathNN-vN / MathNNvN / MathNNAddF, etc.
# Liberal match (canonical AND dash-less variants) bounded to a true
# word boundary; placeholders like "Math3xx" still excluded because
# the suffix must start with `Add[A-Z]`, `v\d`, or `-[A-Z]`.
MATH_TOKEN = re.compile(
    r'\bMath\d+'                                          # MathNN
    r'(?:-?(?:Add[A-Z]\w*|v\d+|[A-Z][A-Za-z0-9]*))*'      # suffix(es), dash optional
    r'(?=[^A-Za-z\d-]|$)'                                 # bound to non-word-non-dash
)


def _normalise_to_index_key(tok: str) -> str:
    """Convert 'Math01v2' / 'Math82AddF' into 'Math01-v2' / 'Math82-AddF'
    so we can look them up against the on-disk filenames (which use
    dashed canonical form)."""
    # Insert a dash before 'Add[A-Z]' or 'v\d'
    out = re.sub(r'(?<=\d)(Add[A-Z]\w*)', r'-\1', tok)
    out = re.sub(r'(?<=\d)(v\d+)', r'-\1', out)
    return out


def index_math_notes() -> Dict[str, Path]:
    idx: Dict[str, Path] = {}
    for f in sorted(DOCS_MATH.glob("TECT-Math*.tex.txt")):
        m = re.match(r'TECT-(Math\d+(?:-(?:Add[A-Za-z]+|v\d+))?)', f.name)
        key = m.group(1) if m else None
        if not key:
            m2 = re.match(r'TECT-(Math\d+)', f.name)
            if m2:
                key = m2.group(1)
            else:
                continue
        idx[key] = f
        bare = re.match(r'(Math\d+)', key).group(1)
        idx.setdefault(bare, f)
    return idx


def parse_paper_header(tex_path: Path) -> List[str]:
    lines = tex_path.read_text(encoding='utf-8', errors='replace').splitlines()
    collected: List[str] = []
    in_archive = False
    for line in lines:
        if line.startswith('%'):
            stripped = line.lstrip('%').strip()
            if re.match(r'Canonical (archive|sources?):', stripped, re.IGNORECASE):
                in_archive = True
                rest = re.sub(r'^Canonical (?:archive|sources?):\s*', '',
                              stripped, count=1, flags=re.IGNORECASE)
                collected.extend(MATH_TOKEN.findall(rest))
            elif in_archive and re.match(r'^\s+', line[1:]):
                collected.extend(MATH_TOKEN.findall(stripped))
            else:
                in_archive = False
        else:
            in_archive = False
    return collected


def parse_paper_body(tex_path: Path) -> Set[str]:
    text = tex_path.read_text(encoding='utf-8', errors='replace')
    body_lines = [
        line for line in text.splitlines()
        if not line.lstrip().startswith('%')
    ]
    body = '\n'.join(body_lines)
    return set(MATH_TOKEN.findall(body))


def discover_papers() -> List[Tuple[str, Path, str]]:
    out: List[Tuple[str, Path, str]] = []
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
                out.append((key, tex, tex.stem))
    return out


def normalise_token(tok: str) -> str:
    return tok.strip().rstrip('.,;:)')


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true', help='dry-run')
    p.add_argument('-v', '--verbose', action='store_true')
    p.add_argument('--no-fail', action='store_true',
                   help='do not exit 1 on missing Math notes')
    args = p.parse_args()

    print(' TECT extract-paper-dependencies — paper <-> Math-note mapper')
    print(f' Source: {DOCS_PAPERS.relative_to(REPO_ROOT)}')
    print(f' Math index: {DOCS_MATH.relative_to(REPO_ROOT)}')

    math_idx = index_math_notes()
    print(f'[deps] indexed {len(math_idx)} Math-note keys '
          f'({len(set(math_idx.values()))} files)')

    papers = discover_papers()
    if not papers:
        print('[deps] no papers discovered; aborting.', file=sys.stderr)
        return 2
    print(f'[deps] discovered {len(papers)} papers across '
          f'{len(set(c for c,*_ in papers))} categories')

    fwd: Dict[str, Dict[str, object]] = {}
    rev: Dict[str, List[str]] = defaultdict(list)
    missing_global: Set[Tuple[str, str]] = set()

    for cat, tex, stem in papers:
        header_tokens_raw = [normalise_token(t) for t in parse_paper_header(tex)]
        body_tokens_raw   = {normalise_token(t) for t in parse_paper_body(tex)}
        # Map every token to its dashed canonical form for index lookup
        header_tokens = [_normalise_to_index_key(t) for t in header_tokens_raw]
        body_tokens   = {_normalise_to_index_key(t) for t in body_tokens_raw}
        all_tokens    = set(header_tokens) | body_tokens
        existing      = sorted(t for t in all_tokens if t in math_idx)
        missing       = sorted(
            t for t in all_tokens
            if t not in math_idx
            and re.match(r'Math\d+', t).group(0) not in math_idx
        )
        for t in missing:
            missing_global.add((stem, t))
        fwd[stem] = {
            'category':       cat,
            'tex_path':       str(tex.relative_to(REPO_ROOT)),
            'header_tokens':  sorted(set(header_tokens)),
            'body_tokens':    sorted(body_tokens),
            'all_existing':   existing,
            'all_missing':    missing,
            'count_header':   len(set(header_tokens)),
            'count_body':     len(body_tokens),
            'count_total':    len(existing),
        }
        for t in existing:
            rev[t].append(stem)
        if args.verbose:
            print(f'  [{cat:<11s}] {stem:<22s} '
                  f'header={len(set(header_tokens)):2d} '
                  f'body={len(body_tokens):2d} '
                  f'total={len(existing):2d}'
                  + (f'  MISSING={len(missing)}' if missing else ''))

    total_header = sum(p['count_header'] for p in fwd.values())
    total_body   = sum(p['count_body'] for p in fwd.values())
    total_uniq   = len(rev)
    print(f'[deps] coverage: {total_uniq} unique Math notes cited '
          f'across {len(fwd)} papers')
    print(f'[deps] total header refs={total_header}, body refs={total_body}')

    if missing_global:
        print(f'[deps] WARNING: {len(missing_global)} missing Math-note refs:',
              file=sys.stderr)
        for stem, key in sorted(missing_global):
            print(f'    {stem} -> {key}', file=sys.stderr)

    # Markdown
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    md_lines: List[str] = []
    md_lines.append('<!-- AUTO-GENERATED by Codes/tools/extract_paper_dependencies.py - DO NOT EDIT. -->')
    md_lines.append('# Paper <-> Math-note Dependency Map')
    md_lines.append('')
    md_lines.append(f'**Generated**: `{now}`')
    md_lines.append('')
    md_lines.append(f'**Coverage**: {len(fwd)} papers -> {total_uniq} unique Math notes.')
    md_lines.append('')
    if missing_global:
        md_lines.append(f'**WARNINGS**: {len(missing_global)} cited Math notes are not present on disk:')
        md_lines.append('')
        md_lines.append('| Paper | Missing Math note |')
        md_lines.append('|---|---|')
        for stem, key in sorted(missing_global):
            md_lines.append(f'| `{stem}` | `{key}` |')
        md_lines.append('')

    md_lines.append('## 1. Forward map (paper -> cited Math notes)')
    md_lines.append('')
    md_lines.append('Header = curated `% Canonical archive:` list (authoritative).')
    md_lines.append('Body = empirical `\\cite{Math...}` and prose references.')
    md_lines.append('')
    by_cat: Dict[str, List[str]] = defaultdict(list)
    for stem in sorted(fwd):
        by_cat[fwd[stem]['category']].append(stem)
    for cat in ('papers', 'auxiliary', 'top_impact', 'epochs'):
        if cat not in by_cat:
            continue
        md_lines.append(f'### {cat}')
        md_lines.append('')
        md_lines.append('| Stem | Header refs | Body refs | Total existing | Cited Math notes |')
        md_lines.append('|---|---:|---:|---:|---|')
        for stem in by_cat[cat]:
            row = fwd[stem]
            cite_str = ', '.join(f'`{t}`' for t in row['all_existing']) or '_(none)_'
            md_lines.append(
                f"| `{stem}` | {row['count_header']} | {row['count_body']} "
                f"| {row['count_total']} | {cite_str} |"
            )
        md_lines.append('')

    md_lines.append('## 2. Reverse map (Math note -> papers that cite it)')
    md_lines.append('')
    md_lines.append('| Math note | # papers | Cited in |')
    md_lines.append('|---|---:|---|')
    for key in sorted(rev,
                      key=lambda k: (-len(rev[k]),
                                     int(re.match(r'Math(\d+)', k).group(1)))):
        cite_str = ', '.join(f'`{s}`' for s in sorted(rev[key]))
        md_lines.append(f'| `{key}` | {len(rev[key])} | {cite_str} |')
    md_lines.append('')
    md_md = '\n'.join(md_lines) + '\n'

    payload: Dict[str, object] = {
        'schema':    'tect-papers-math-deps-v1',
        'generated': now,
        'papers':    [
            {
                'stem':         stem,
                'category':     row['category'],
                'tex_path':     row['tex_path'],
                'header_count': row['count_header'],
                'body_count':   row['count_body'],
                'total':        row['count_total'],
                'cited_math':   row['all_existing'],
                'missing':      row['all_missing'],
            }
            for stem, row in sorted(fwd.items())
        ],
        'notes':     [
            {
                'key':    key,
                'count':  len(rev[key]),
                'papers': sorted(rev[key]),
            }
            for key in sorted(rev,
                              key=lambda k: (-len(rev[k]),
                                             int(re.match(r'Math(\d+)', k).group(1))))
        ],
        'totals':    {
            'papers':       len(fwd),
            'unique_notes': total_uniq,
            'header_refs':  total_header,
            'body_refs':    total_body,
            'missing':      len(missing_global),
        },
    }
    js_body = (
        '/* AUTO-GENERATED by Codes/tools/extract_paper_dependencies.py - DO NOT EDIT. */\n'
        '/* Source: Docs/papers/{papers,auxiliary,top_impact,epochs}/*.tex            */\n'
        'window.TECT_PAPERS_DEPS = '
        + json.dumps(payload, indent=2, ensure_ascii=False)
        + ';\n'
    )

    if args.check:
        print(f'  [dry-run] would write {OUT_MD} ({len(md_md)} bytes)')
        print(f'  [dry-run] would write {OUT_JS} ({len(js_body)} bytes)')
    else:
        try:
            OUT_MD.write_text(md_md, encoding='utf-8')
            print(f'  [md]   wrote {OUT_MD.relative_to(REPO_ROOT)} '
                  f'({len(md_md)//1024} KB)')
            OUT_JS.parent.mkdir(parents=True, exist_ok=True)
            OUT_JS.write_text(js_body, encoding='utf-8')
            print(f'  [js]   wrote {OUT_JS.relative_to(REPO_ROOT)} '
                  f'({len(js_body)//1024} KB)')
        except OSError as exc:
            print(f'[deps] ERROR: I/O failure: {exc}', file=sys.stderr)
            return 2

    if missing_global and not args.no_fail:
        print(f'[deps] FAIL: {len(missing_global)} missing references; '
              f'use --no-fail to allow.', file=sys.stderr)
        return 1
    print('[deps] OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
