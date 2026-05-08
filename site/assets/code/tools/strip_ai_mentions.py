#!/usr/bin/env python3
# =====================================================================
# strip_ai_mentions.py v1.0
#
# Sweep public-facing Website/ content (data/*.js + selected assets/*.md
# rendered into pages) and remove or rephrase AI-tool mentions
# unsuitable for a formal physics website:
#
#   - "Anthropic Claude (Opus|Sonnet)? \d.\d?" -> remove sentence containing it
#   - "Claude" (standalone, NOT in CLAUDE.md filename) -> remove or rephrase
#   - "Anthropic" -> remove
#   - "GPT-?\d?" -> remove
#   - "LLM" / "large language model" -> remove
#   - "AI (assistant|agent|collaborator|reviewer)" -> "research collaborator"
#   - "autonomous research/agent" -> "research"
#   - "autonomous-turn" / "Round R\d+" / "N-turn" / "30-turn" /
#     "turn R?\d+" -> "research session"
#
# Sentences that become trivially short are dropped entirely.
# Each change is logged so the operator can audit.
#
# CLI:
#   python -u Codes/tools/strip_ai_mentions.py            # apply
#   python -u Codes/tools/strip_ai_mentions.py --check    # dry-run
#   python -u Codes/tools/strip_ai_mentions.py --scope=data    # only data/*.js
# =====================================================================
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WEBSITE   = REPO_ROOT / "Website"

def _glob_data() -> List[Path]:
    """Every Website/data/*.js + Website/data/_narrative/*.md (excluding
    _archive which is historical auto-snapshots)."""
    out = []
    data_root = WEBSITE / "data"
    for p in sorted(data_root.glob("*.js")):
        out.append(p.relative_to(WEBSITE))
    for p in sorted((data_root / "_narrative").glob("*.md")):
        out.append(p.relative_to(WEBSITE))
    return out


def _glob_assets() -> List[Path]:
    """Public-facing narrative + selected assets (NOT the full mirrored
    canonical Docs; those carry their own provenance and remain
    untouched at sweep level)."""
    out = []
    asset_narr = WEBSITE / "assets" / "_narrative"
    for p in sorted(asset_narr.glob("*.md")):
        out.append(p.relative_to(WEBSITE))
    return out


SCOPE_DATA   = []   # filled lazily in main() to allow lazy WEBSITE resolution
SCOPE_ASSETS = []

# Replacement rules: (pattern, replacement, label)
# Order matters — multi-word patterns first.
RULES: List[Tuple[re.Pattern, str, str]] = [
    # Compound AI-tool phrases first
    (re.compile(r'\bAnthropic\s+Claude(?:\s+Opus)?(?:\s+\d+(?:\.\d+)?)?'),
     '', 'Anthropic Claude X'),
    (re.compile(r'\bClaude\s+(?:Opus|Sonnet|Haiku)\s+\d+(?:\.\d+)?'),
     '', 'Claude Opus N'),
    (re.compile(r'\bAI\s+(?:assistant|agent|collaborator|reviewer)\b',
                re.IGNORECASE), 'research collaborator', 'AI X'),
    (re.compile(r'\bAnthropic\b'), '', 'Anthropic'),
    (re.compile(r'\bClaude\b'), '', 'Claude'),
    (re.compile(r'\bGPT[- ]?\d?\b'), '', 'GPT'),
    (re.compile(r'\bLLM(?:s)?\b'), 'computational tool', 'LLM'),
    (re.compile(r'\blarge\s+language\s+model(?:s)?\b', re.IGNORECASE),
     'computational tool', 'large language model'),
    # Autonomous-research / agent / turn
    (re.compile(r'\bautonomous[- ]research\b', re.IGNORECASE),
     'research', 'autonomous-research'),
    (re.compile(r'\bautonomous[- ]agent(?:s)?\b', re.IGNORECASE),
     'research session', 'autonomous-agent'),
    (re.compile(r'\bautonomous[- ]turn(?:s)?\b', re.IGNORECASE),
     'research session', 'autonomous-turn'),
    (re.compile(r'\b30[- ]turn\b'), 'research-session', '30-turn'),
    (re.compile(r'\b\d+[- ]turn(?:s)?\b'), 'research-session', 'N-turn'),
    (re.compile(r'\bRounds?\s+R?\d+(?:[-–]R?\d+)?\b'),
     'research session', 'Round N'),
    (re.compile(r'\bturn\s+R?\d+\b'), 'research session', 'turn N'),
]


def apply_rules(text: str, verbose: bool = False) -> Tuple[str, dict]:
    """Apply all rules; return new text and per-rule hit counts."""
    counts = {}
    for pat, repl, label in RULES:
        new_text, n = pat.subn(repl, text)
        if n > 0:
            counts[label] = counts.get(label, 0) + n
            text = new_text
    # Cleanup leftover artefacts: doubled commas / spaces / punctuation
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'\s+([.,;:])', r'\1', text)
    text = re.sub(r'([.,;:])\s*([.,;:])', r'\1', text)
    text = re.sub(r'\(\s*\)', '', text)        # empty parens
    text = re.sub(r'\[\s*\]', '', text)        # empty brackets
    text = re.sub(r'\s+\n', '\n', text)        # trailing whitespace
    return text, counts


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true', help='dry-run')
    p.add_argument('--scope', choices=['all', 'data', 'assets'], default='all',
                   help='which files to sweep (default: all)')
    p.add_argument('-v', '--verbose', action='store_true')
    args = p.parse_args()

    targets = []
    if args.scope in ('all', 'data'):   targets.extend(_glob_data())
    if args.scope in ('all', 'assets'): targets.extend(_glob_assets())
    print(f' TECT strip-ai-mentions v1.0 (scope={args.scope}, '
          f'{len(targets)} files)')

    grand_total = {}
    files_changed = 0
    for rel in targets:
        path = WEBSITE / rel
        if not path.exists():
            if args.verbose:
                print(f'  [skip-missing] {rel}')
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except OSError as exc:
            print(f'  [ERROR read] {rel}: {exc}', file=sys.stderr)
            continue
        new_text, counts = apply_rules(text, verbose=args.verbose)
        if not counts:
            if args.verbose:
                print(f'  [clean]   {rel}')
            continue
        action = '[dry-run]' if args.check else '[patched] '
        print(f'  {action} {rel}: {counts}')
        for k, v in counts.items():
            grand_total[k] = grand_total.get(k, 0) + v
        if not args.check:
            try:
                path.write_text(new_text, encoding='utf-8')
                files_changed += 1
            except OSError as exc:
                print(f'  [ERROR write] {rel}: {exc}', file=sys.stderr)

    print(f'\n[strip-ai] grand total: {grand_total}')
    print(f'[strip-ai] files changed: {files_changed}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
