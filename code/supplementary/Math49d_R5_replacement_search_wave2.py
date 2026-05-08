#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Math49d_R5_replacement_search_wave2.py
======================================

PR-1 wave-2 extension: census of M_lambda :=
    dim Hom_{G_SM}(C_{(1,1)_0}, S^lambda V)
over all partitions lambda with |lambda| in {20, 25} and at most 5
parts, completing the replacement-bundle search filed as
    Q-2026-04-20-PR1  (OPEN-QUESTIONS.md)
and promised at
    docs/math/TECT-Math49d-R5-replacement.tex.txt, line 325-331.

Wave-1 (this module's parent, Math49d_R5_replacement_search.py,
2026-04-20) established M_lambda <= 1 for every partition lambda
with |lambda| <= 15 (i.e. for k in {0,1,2,3}).

Wave-2 extends the enumeration to k in {4, 5}, i.e. to
|lambda| = 20 and |lambda| = 25.

Representation-theoretic identity (re-stated from wave-1):
    M_lambda  =  c^{lambda}_{(k,k,k), (k,k)}    with  |lambda| = 5 k
(only a single LR term contributes because k is determined by |lambda|).

Wave-2 question (falsification criterion for PR-1):
    Does there exist lambda in the wave-2 range with M_lambda >= 2
    (ideally M_lambda = 3, which would positively resolve the single-
    bundle version of Pillar 6)?

This script reuses the wave-1 LR kernel by importing the parent
module; no algorithmic changes are made, only the enumeration range
is widened.

Output
------
  1. Console log: full per-|lambda| multiplicity table, SU(5)
     dimension, and any flagged lambda with M_lambda >= 2.
  2. JSON report:
       Docs/supplementary/Math49d_R5_wave2_report.json
     with fields { wave: "2",
                   multiplicity_census: { "20": [...], "25": [...] },
                   sup_M: int,
                   lambda_of_sup: [...],
                   wave1_sup_M: 1 }.

Policy
------
Archived per UPDATE_POLICY.md section 13 (code-manual discipline).
Associated theory note:
    docs/math/TECT-Math49d-R5-replacement-wave2.tex.txt
Status:  PR-1 wave-2 census (Pillar 6 physical reopening closure).
Author:  TECT collaboration
Version: v1.0, 2026-04-21
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections import defaultdict
from typing import Dict, List, Tuple

# --- Import wave-1 LR machinery ---------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import Math49d_R5_replacement_search as wave1  # noqa: E402


# ---------------------------------------------------------------
# Wave-2 enumeration
# ---------------------------------------------------------------
def enumerate_wave2(
    k_list: Tuple[int, ...] = (4, 5),
    verbose: bool = True,
) -> Dict[int, List[Tuple[Tuple[int, ...], int, int]]]:
    """
    For each k in k_list, enumerate every partition lambda of 5*k
    with at most 5 parts, and return
        { 5*k : [ (lambda, M_lambda, dim_SU5(lambda)), ... ] }
    listing ALL partitions (including those with M_lambda = 0, for
    full provenance).
    """
    out: Dict[int, List[Tuple[Tuple[int, ...], int, int]]] = defaultdict(list)
    for k in k_list:
        n = 5 * k
        parts = wave1.partitions_of(n, max_parts=5)
        if verbose:
            print(f"  |lambda| = {n}  (k = {k}):  "
                  f"{len(parts)} partitions (<=5 parts)")
        t0 = time.time()
        for j, lam in enumerate(parts):
            m = wave1.multiplicity_trivial(lam, max_k=k)
            d = wave1.dim_su5_irrep(lam)
            out[n].append((lam, m, d))
            if verbose and (j + 1) % 25 == 0:
                print(f"    [{j + 1}/{len(parts)}] elapsed "
                      f"{time.time() - t0:.2f}s")
        if verbose:
            print(f"    done |lambda|={n} in {time.time() - t0:.2f}s")
    return out


# ---------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------
def print_report(
    census: Dict[int, List[Tuple[Tuple[int, ...], int, int]]],
) -> Dict[str, object]:
    """Pretty-print the wave-2 table and build a JSON-ready summary."""
    summary: Dict[str, object] = {
        "wave": "2",
        "description": "PR-1 wave-2 Littlewood-Richardson census for "
                       "M_lambda = c^lambda_{(k,k,k),(k,k)} at |lambda| in {20,25}",
        "wave1_sup_M": 1,
        "multiplicity_census": {},
    }

    sup_M = 0
    sup_lambdas: List[Tuple[int, Tuple[int, ...], int]] = []

    for n in sorted(census.keys()):
        rows = sorted(census[n], key=lambda rec: (-rec[1], rec[0]))
        # Only list non-trivial (M > 0) in console for readability
        nonzero = [rec for rec in rows if rec[1] > 0]
        all_rows_json = [
            {"lambda": list(lam), "M": m, "dim_SU5": d}
            for (lam, m, d) in rows
        ]
        summary["multiplicity_census"][str(n)] = {
            "num_partitions_all": len(rows),
            "num_partitions_nonzero_M": len(nonzero),
            "entries": all_rows_json,
        }

        print()
        print(f"  === |lambda| = {n}  (k = {n // 5}) ===")
        print(f"    total partitions (<=5 parts): {len(rows)}")
        print(f"    partitions with M_lambda >= 1: {len(nonzero)}")
        if nonzero:
            print(f"    {'lambda':25s} {'M':>4s} {'dim_SU5':>12s}")
            for lam, m, d in nonzero:
                marker = "  <-- M>=2" if m >= 2 else ""
                print(f"    {str(lam):25s} {m:4d} {d:12d}{marker}")
        else:
            print("    (all M_lambda = 0)")

        # Track supremum
        for lam, m, d in rows:
            if m > sup_M:
                sup_M = m
                sup_lambdas = [(n, lam, d)]
            elif m == sup_M and m > 0:
                sup_lambdas.append((n, lam, d))

    summary["sup_M"] = sup_M
    summary["lambda_of_sup"] = [
        {"n": n, "lambda": list(lam), "dim_SU5": d}
        for (n, lam, d) in sup_lambdas
    ]

    print()
    print("=" * 72)
    print(f"  wave-2 supremum:  sup_lambda M_lambda = {sup_M}")
    if sup_M >= 2:
        print(f"  SUP >= 2 realised by:")
        for n, lam, d in sup_lambdas:
            print(f"    lambda = {lam}   |lambda|={n}, dim={d}")
    else:
        print(f"  SUP = 1; single-bundle Pillar 6 REMAINS FALSIFIED at |lambda|<=25.")
    print("=" * 72)

    return summary


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
def main() -> int:
    print("=" * 72)
    print("Math49d-R5 replacement-bundle search  [WAVE 2: |lambda| in {20, 25}]")
    print("=" * 72)
    print()
    print("-- re-running wave-1 sanity checks (LR engine) --")
    wave1.sanity_checks()
    print()

    print("-- wave-2 enumeration --")
    t0 = time.time()
    census = enumerate_wave2(k_list=(4, 5), verbose=True)
    total = time.time() - t0
    print(f"\n  total wave-2 enumeration time: {total:.2f}s")

    summary = print_report(census)
    summary["total_elapsed_s"] = round(total, 3)

    # Write JSON
    json_path = os.path.join(_THIS_DIR, "Math49d_R5_wave2_report.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    print(f"\n  JSON report written: {json_path}")

    # Exit status: 0 always (this is a census, not a pass/fail test),
    # but print a one-line verdict for the ledger.
    print()
    if summary["sup_M"] >= 3:
        verdict = ("VERDICT (wave-2): M_lambda = 3 realised --> "
                   "single-bundle Pillar 6 POSITIVELY RESOLVED.")
    elif summary["sup_M"] >= 2:
        verdict = (f"VERDICT (wave-2): sup M_lambda = {summary['sup_M']}; "
                   "single-bundle dim-3 still requires a direct sum.")
    else:
        verdict = ("VERDICT (wave-2): sup M_lambda = 1 on |lambda|<=25; "
                   "single-bundle Pillar 6 FALSIFIED through k<=5.")
    print(verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
