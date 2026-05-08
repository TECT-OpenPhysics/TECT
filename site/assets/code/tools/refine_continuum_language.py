#!/usr/bin/env python3
# =====================================================================
# refine_continuum_language.py v1.0
#
# Sweep public-facing Website/ content (data/*.js + data/_narrative/*.md
# + assets/_narrative/*.md) and rephrase residual "lattice"/"sublattice"
# vocabulary that risks giving readers the false impression that TECT
# *assumes* a discrete lattice or BCC structure.
#
# TECT's actual framing:
#   - high-energy Z-symmetric continuum field
#   - Brazovskii-class weak-crystallisation first-order transition
#   - emergent BCC condensate as the energetically selected ordered phase
#
# Filenames (e.g. TECT-Math242-...-Sublattice-Ladder.tex.txt) are NOT
# touched — they are part of the historical canonical record. Only
# narrative text that surrounds or echoes such filenames is rephrased.
#
# CLI:
#   python -u Codes/tools/refine_continuum_language.py            # apply
#   python -u Codes/tools/refine_continuum_language.py --check    # dry-run
# =====================================================================
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WEBSITE   = REPO_ROOT / "Website"


def _glob_targets() -> List[Path]:
    out = []
    data = WEBSITE / "data"
    for p in sorted(data.glob("*.js")):
        out.append(p)
    for p in sorted((data / "_narrative").glob("*.md")):
        out.append(p)
    asset_narr = WEBSITE / "assets" / "_narrative"
    if asset_narr.exists():
        for p in sorted(asset_narr.glob("*.md")):
            out.append(p)
    return out


# Replacement rules: (compiled regex, replacement, label).
# Order matters: more specific phrases first.
RULES: List[Tuple[re.Pattern, str, str]] = [
    # ----- Class A: TECT-internal "BCC lattice" -> "BCC condensate" -----
    (re.compile(r'\bBCC[- ]lattice structure\b', re.IGNORECASE),
     'BCC condensate ordering', 'BCC lattice structure'),
    (re.compile(r'\bBCC[- ]lattice spacing\b', re.IGNORECASE),
     'BCC condensate modulation length', 'BCC lattice spacing'),
    (re.compile(r'\bBCC[- ]lattice\b', re.IGNORECASE),
     'BCC condensate', 'BCC lattice'),
    (re.compile(r'\bBCC reciprocal[- ]lattice\b', re.IGNORECASE),
     'BCC reciprocal-vector', 'BCC reciprocal-lattice'),

    # ----- Class A continued: TECT-internal narrative ----------
    (re.compile(r'\bMagnetic lattice\b'),
     'Magnetic ordering', 'Magnetic lattice'),
    (re.compile(r'\bkinematic lattice dynamics\b', re.IGNORECASE),
     'kinematic condensate dynamics', 'kinematic lattice dynamics'),
    (re.compile(r'\bprimitive lattice inputs\b', re.IGNORECASE),
     'primitive condensate inputs', 'primitive lattice inputs'),
    (re.compile(r'\bshell-adaptive BCC lattice\b', re.IGNORECASE),
     'shell-adaptive BCC reciprocal grid', 'shell-adaptive BCC lattice'),
    (re.compile(r'\bfinite[- ]lattice\b', re.IGNORECASE),
     'finite-discretisation', 'finite-lattice'),

    # ----- Class A continued: numerical / supplementary references -----
    (re.compile(r'\bsupplementary lattice script\b', re.IGNORECASE),
     'supplementary discretisation script', 'supplementary lattice script'),
    (re.compile(r'\blattice[- ]corrected\b', re.IGNORECASE),
     'discretisation-corrected', 'lattice-corrected'),
    (re.compile(r'\blattice[- ]spacing\b', re.IGNORECASE),
     'modulation length', 'lattice-spacing'),

    # ----- Class C: "Q2 lattice" audit context (lattice = UV-regulator) -----
    # Math58-v7-AddA Q2 originally read "lattice scheme-dependence DISMISSED";
    # rephrase as "alternate-regulator scheme-dependence DISMISSED" so the
    # casual reader does not infer that TECT itself uses a lattice.
    (re.compile(r'\bQ2 lattice\b'),
     'Q2 alternate-regulator (UV-cutoff) scheme', 'Q2 lattice'),
    (re.compile(r'\blattice scheme[- ]dependence\b', re.IGNORECASE),
     'UV-regulator scheme dependence', 'lattice scheme-dependence'),
    (re.compile(r'\bdim[- ]reg and lattice\b', re.IGNORECASE),
     'dimensional and alternate-regulator', 'dim-reg and lattice'),

    # ----- Class C: Sr lattice clocks -> Sr optical clocks -----
    # "Sr optical lattice clocks" is the textbook term, but the lone word
    # "lattice" can be confusing in a TECT context. "Sr optical clocks"
    # is unambiguous experimentally and removes the conflation.
    (re.compile(r'\bSr lattice clocks\b'),
     'Sr optical clocks', 'Sr lattice clocks'),

    # ----- Class A continued: sublattice (TECT internal narrative) -----
    # Filenames containing "Sublattice" are NOT touched; the regex below
    # excludes file-extension-bearing tokens via a negative-lookahead.
    (re.compile(r'\bsub-?lattice\b(?![-A-Za-z0-9_]*\.tex)', re.IGNORECASE),
     'sub-condensate', 'sublattice'),
]


# Cleanup pass after substitution
def _post_cleanup(text: str) -> str:
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r' +([.,;:])', r'\1', text)
    return text


def apply_rules(text: str) -> Tuple[str, dict]:
    counts = {}
    for pat, repl, label in RULES:
        new_text, n = pat.subn(repl, text)
        if n > 0:
            counts[label] = counts.get(label, 0) + n
            text = new_text
    text = _post_cleanup(text)
    return text, counts


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true', help='dry-run')
    p.add_argument('-v', '--verbose', action='store_true')
    args = p.parse_args()

    targets = _glob_targets()
    print(f' TECT refine-continuum-language v1.0 ({len(targets)} files)')

    grand_total = {}
    files_changed = 0
    for path in targets:
        rel = path.relative_to(WEBSITE)
        try:
            text = path.read_text(encoding='utf-8')
        except OSError as exc:
            print(f'  [ERROR read] {rel}: {exc}', file=sys.stderr)
            continue
        new_text, counts = apply_rules(text)
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

    print(f'\n[refine-continuum] grand total: {grand_total}')
    print(f'[refine-continuum] files changed: {files_changed}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
