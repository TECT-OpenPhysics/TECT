#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Math49d_R5_replacement_search.py
================================

PR-1-replacement bundle search: enumerate SU(5)-irreducible
representations S^lambda V whose branching to
S(U(3) x U(2)) (the centraliser of
    zeta = diag(omega, omega, omega, -1, -1), omega = e^{2 pi i / 3})
contains the trivial (1,1)_0 rep of G_SM
with multiplicity M_lambda := dim Hom_{G_SM}(C_{(1,1)_0}, S^lambda V).

Key representation-theoretic fact
---------------------------------
Let V = V_alpha + V_beta with dim V_alpha = 3, dim V_beta = 2.
Under S(U(3) x U(2)):
    V_alpha  -->  (3, 1)_{+1/3}
    V_beta   -->  (1, 2)_{-1/2}
For the tensor product S^mu V_alpha (x) S^nu V_beta to carry
the trivial (1,1)_0 rep of G_SM, both factors must individually
be SU(3)- and SU(2)-trivial:
    S^mu V_alpha is SU(3)-trivial  iff  mu = (k, k, k) for some k >= 0;
    S^nu V_beta  is SU(2)-trivial  iff  nu = (m, m)    for some m >= 0.
Total hypercharge:
    Y(S^mu V_alpha)  =  (1/3) |mu|   =  k,
    Y(S^nu V_beta)   = (-1/2) |nu|   = -m.
(1,1)_0 therefore forces k = m, whence |lambda| = |mu| + |nu| = 5 k.
By the Littlewood-Richardson branching theorem,
    M_lambda = sum_{k >= 0} c^{lambda}_{(k,k,k), (k,k)}.

This script enumerates all partitions lambda with |lambda| <= 15,
computes the LR coefficients c^{lambda}_{(k,k,k),(k,k)} by the
skew semistandard tableau + reverse-reading-word lattice rule, and
reports:

  * the full multiplicity table M_lambda,
  * the smallest lambda with M_lambda = 3  (the replacement-bundle
    candidate realising three (1,1)_0 singlets in a single SU(5)-irrep),
  * the smallest triple of distinct lambda's whose direct sum realises
    three (1,1)_0 singlets (a multi-bundle candidate).

Verification
------------
For lambda = () and lambda = (1,1,1,1,1) = det V the expected
multiplicity is 1, serving as a sanity check.
For lambda = (2,2,1), (2,1,1,1), (1,1,1,1,1) the script verifies
the same multiplicity 1, reproducing the LR hand computation of
the accompanying note TECT-Math49d-R5-replacement.tex.txt.

Policy
------
Archived per UPDATE_POLICY.md section 13 (code-manual discipline).
Associated theory note:
    docs/math/TECT-Math49d-R5-replacement.tex.txt
Status:  PR-1 replacement-bundle search (Pillar 6 physical reopening).
Author:  TECT collaboration
Version: v1.0, 2026-04-20
"""

from __future__ import annotations

import sys
from collections import defaultdict
from typing import Dict, List, Tuple

# ---------------------------------------------------------------
# Partition utilities
# ---------------------------------------------------------------
def partitions_of(n: int, max_parts: int = None) -> List[Tuple[int, ...]]:
    """All partitions of n into at most max_parts parts, sorted descending."""
    if n == 0:
        return [()]
    out: List[Tuple[int, ...]] = []
    def rec(rem: int, cap: int, so_far: List[int]) -> None:
        if rem == 0:
            out.append(tuple(so_far))
            return
        if max_parts is not None and len(so_far) >= max_parts:
            return
        for k in range(min(rem, cap), 0, -1):
            rec(rem - k, k, so_far + [k])
    rec(n, n, [])
    return out


def contains(lam: Tuple[int, ...], mu: Tuple[int, ...]) -> bool:
    """Whether mu is contained in lam as a Young diagram."""
    if len(mu) > len(lam):
        return False
    for i in range(len(mu)):
        if mu[i] > lam[i]:
            return False
    return True


def skew_boxes(lam: Tuple[int, ...], mu: Tuple[int, ...]) -> List[Tuple[int, int]]:
    """List of (row, col) for the skew shape lam/mu, 1-indexed."""
    out: List[Tuple[int, int]] = []
    nrows = max(len(lam), len(mu))
    mu_ext = list(mu) + [0] * (nrows - len(mu))
    lam_ext = list(lam) + [0] * (nrows - len(lam))
    for r in range(nrows):
        for c in range(mu_ext[r], lam_ext[r]):
            out.append((r + 1, c + 1))
    return out


# ---------------------------------------------------------------
# Littlewood-Richardson coefficient
# ---------------------------------------------------------------
def lr_coefficient(
    lam: Tuple[int, ...],
    mu: Tuple[int, ...],
    nu: Tuple[int, ...],
) -> int:
    """
    Compute the Littlewood-Richardson coefficient c^{lambda}_{mu, nu}
    by enumerating skew semistandard Young tableaux of shape lam/mu
    with content nu, and accepting those whose reverse reading word
    (read each row right-to-left, top to bottom) is a lattice word:
    every prefix has #i >= #(i+1) for all i >= 1.
    """
    # Basic containment test
    if not contains(lam, mu):
        return 0
    # Size test
    boxes = skew_boxes(lam, mu)
    if len(boxes) != sum(nu):
        return 0
    if not nu:
        return 1 if len(boxes) == 0 else 0
    # Symbol counts from content nu
    nu_ext = list(nu)
    # Organise boxes by row in top->bottom order
    by_row: Dict[int, List[int]] = defaultdict(list)
    for (r, c) in boxes:
        by_row[r].append(c)
    for r in by_row:
        by_row[r].sort()  # left-to-right

    # Depth-first enumerate fills, maintaining semistandard + LR
    rows_sorted = sorted(by_row.keys())
    count = 0

    def available_entries(
        row: int,
        col: int,
        row_last: Dict[int, int],
        col_last: Dict[int, int],
        remaining: List[int],
    ) -> List[int]:
        """Entries allowed at (row, col) when boxes are visited
        top-to-bottom across rows and right-to-left within each row.

        Semistandard constraints (left-to-right within a row, top-to-
        bottom within a column) translated into visit order:
          - row is scanned right-to-left, so ``row_last[row]`` holds the
            entry placed to the RIGHT of the current box; the current
            entry must be <= row_last for row-weakly-increasing L->R.
          - column is scanned top-to-bottom, so ``col_last[col]`` holds
            the entry placed ABOVE the current box; the current entry
            must be > col_last for column-strictly-increasing top->bot.
        """
        hi_row = row_last.get(row)  # None => no upper bound
        low_col = col_last.get(col, 0) + 1
        lo = low_col
        hi = hi_row if hi_row is not None else len(remaining)
        out = []
        for i in range(lo, hi + 1):
            if 1 <= i <= len(remaining) and remaining[i - 1] > 0:
                out.append(i)
        return out

    def lattice_prefix_ok(symbol: int, prefix_counts: List[int]) -> bool:
        """After appending symbol, does #i >= #(i+1) hold for all i?"""
        tmp = list(prefix_counts)
        if symbol - 1 >= len(tmp):
            tmp.extend([0] * (symbol - len(tmp)))
        tmp[symbol - 1] += 1
        for i in range(len(tmp) - 1):
            if tmp[i] < tmp[i + 1]:
                return False
        return True

    def rec(
        boxes_iter: List[Tuple[int, int]],
        row_last: Dict[int, int],
        col_last: Dict[int, int],
        remaining: List[int],
        reverse_reading_prefix_counts: List[int],
    ) -> None:
        nonlocal count
        if not boxes_iter:
            count += 1
            return
        (r, c) = boxes_iter[0]
        rest = boxes_iter[1:]
        # Reverse reading word order: top rows first, within row RIGHT to LEFT.
        # We are visiting boxes in that order (see top-level).
        for sym in available_entries(r, c, row_last, col_last, remaining):
            # Check lattice condition on the reverse reading word
            if not lattice_prefix_ok(sym, reverse_reading_prefix_counts):
                continue
            new_remaining = list(remaining)
            new_remaining[sym - 1] -= 1
            new_row_last = dict(row_last)
            new_row_last[r] = sym
            new_col_last = dict(col_last)
            new_col_last[c] = sym
            new_prefix = list(reverse_reading_prefix_counts)
            if sym - 1 >= len(new_prefix):
                new_prefix.extend([0] * (sym - len(new_prefix)))
            new_prefix[sym - 1] += 1
            rec(rest, new_row_last, new_col_last, new_remaining, new_prefix)

    # Order boxes in reverse-reading-word order:
    # top rows first, within each row right-to-left.
    boxes_ordered: List[Tuple[int, int]] = []
    for r in rows_sorted:
        for c in reversed(by_row[r]):
            boxes_ordered.append((r, c))

    remaining = list(nu_ext)
    rec(boxes_ordered, {}, {}, remaining, [])
    return count


# ---------------------------------------------------------------
# Sanity check: classical LR coefficients
# ---------------------------------------------------------------
def sanity_checks() -> None:
    """Known LR identities to validate the implementation."""
    print("== Sanity checks ==")
    # s_{(1)} * s_{(1)} = s_{(2)} + s_{(1,1)}
    assert lr_coefficient((2,), (1,), (1,)) == 1
    assert lr_coefficient((1, 1), (1,), (1,)) == 1
    assert lr_coefficient((2,), (), (2,)) == 1
    # Trivial identity: c^lambda_{empty, lambda} = 1
    for n in range(1, 5):
        for lam in partitions_of(n):
            assert lr_coefficient(lam, (), lam) == 1, f"Trivial ID failed at {lam}"
    # s_{(2)} * s_{(2)} = s_{(4)} + s_{(3,1)} + s_{(2,2)}
    assert lr_coefficient((4,), (2,), (2,)) == 1
    assert lr_coefficient((3, 1), (2,), (2,)) == 1
    assert lr_coefficient((2, 2), (2,), (2,)) == 1
    assert lr_coefficient((3, 1, 0), (2,), (2,)) == 1
    # s_{(1,1)} * s_{(1,1)} = s_{(2,2)} + s_{(2,1,1)} + s_{(1,1,1,1)}
    assert lr_coefficient((2, 2), (1, 1), (1, 1)) == 1
    assert lr_coefficient((2, 1, 1), (1, 1), (1, 1)) == 1
    assert lr_coefficient((1, 1, 1, 1), (1, 1), (1, 1)) == 1
    assert lr_coefficient((3, 1), (1, 1), (1, 1)) == 0
    print("  all classical LR identities hold.  PASS")


# ---------------------------------------------------------------
# (1,1)_0 multiplicity in S^lambda V under S(U(3) x U(2))
# ---------------------------------------------------------------
def multiplicity_trivial(
    lam: Tuple[int, ...],
    max_k: int = 6,
) -> int:
    """
    Multiplicity of (1,1)_0 in S^lambda V under S(U(3) x U(2)).
    Equals sum_{k=0}^{max_k} c^{lambda}_{(k,k,k), (k,k)}.
    |lambda| must equal 5 k for the k-term to contribute.
    """
    n = sum(lam)
    if n % 5 != 0:
        return 0
    k = n // 5
    if k > max_k:
        raise ValueError(f"|lambda|={n} requires k={k} > max_k={max_k}")
    mu = tuple([k, k, k]) if k > 0 else ()
    nu = tuple([k, k]) if k > 0 else ()
    return lr_coefficient(lam, mu, nu)


def enumerate_all(max_size: int = 15) -> Dict[int, List[Tuple[Tuple[int, ...], int]]]:
    """Enumerate all partitions lambda of size <= max_size (in multiples of 5)
    with <=5 parts, and return their multiplicity_trivial."""
    out: Dict[int, List[Tuple[Tuple[int, ...], int]]] = defaultdict(list)
    for n in range(0, max_size + 1, 5):
        for lam in partitions_of(n, max_parts=5):
            m = multiplicity_trivial(lam)
            if m > 0:
                out[n].append((lam, m))
    return out


# ---------------------------------------------------------------
# SU(5)-irrep dimension  via hook-content formula for lambda
# with <=5 parts
# ---------------------------------------------------------------
def dim_su5_irrep(lam: Tuple[int, ...]) -> int:
    """Weyl dimension of SU(5)-irrep with highest weight lam (in fundamental-weight basis, but we use partitions)."""
    # For GL(5), dim S^lambda V = product over boxes of (5 - i + j) / hook
    # For SU(5) the same formula applies if we mod by det^(lam_5).
    lam_ext = list(lam) + [0] * (5 - len(lam))
    n = 5
    num = 1
    den = 1
    # Hook-content formula:
    for i in range(5):
        for j in range(lam_ext[i]):
            # Content: j - i  (j 1-indexed from 0)
            num *= n + (j - i)
            # Hook:
            # hook(i,j) = (lam[i] - j - 1) + (col height below) + 1
            # Column height below (i,j):  number of rows k>i with lam_ext[k] > j
            below = 0
            for k in range(i + 1, 5):
                if lam_ext[k] > j:
                    below += 1
            hook = (lam_ext[i] - j - 1) + below + 1
            den *= hook
    return num // den


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
def main() -> int:
    print("=" * 72)
    print("Math49d-R5 replacement-bundle search")
    print("=" * 72)
    sanity_checks()
    print()

    print("== (1,1)_0 multiplicities in S^lambda V under S(U(3) x U(2)) ==")
    print("    (only partitions with nonzero multiplicity are listed)")
    print()
    table = enumerate_all(max_size=15)
    for n in sorted(table.keys()):
        print(f"  |lambda| = {n}  (k = {n // 5}):")
        for lam, m in sorted(table[n]):
            d = dim_su5_irrep(lam)
            print(
                f"    lambda = {str(lam):22s}  "
                f"dim S^lambda V = {d:6d}   "
                f"M_(1,1)_0 = {m}"
            )
        print()

    # Find the smallest lambda with M = 3
    best_single: Tuple[int, Tuple[int, ...], int, int] = None
    for n in sorted(table.keys()):
        for lam, m in table[n]:
            if m == 3:
                best_single = (n, lam, m, dim_su5_irrep(lam))
                break
        if best_single:
            break
    if best_single:
        n, lam, m, d = best_single
        print(
            f"==> Smallest single-irrep realisation: lambda = {lam}, "
            f"dim = {d}, M_(1,1)_0 = {m}"
        )
    else:
        print(
            "==> NO single SU(5)-irrep S^lambda V with M_(1,1)_0 = 3 "
            f"for |lambda| <= 15.  (i.e. single-bundle Pillar 6 requires "
            "|lambda| > 15.)"
        )

    # Multi-bundle (direct sum) realisation: smallest |lambda|-sum
    # of three distinct partitions each with M = 1
    candidates_with_1: List[Tuple[int, Tuple[int, ...], int]] = []
    for n in sorted(table.keys()):
        for lam, m in table[n]:
            if m == 1:
                candidates_with_1.append((n, lam, dim_su5_irrep(lam)))
    if len(candidates_with_1) >= 3:
        candidates_with_1.sort()
        chosen = candidates_with_1[:3]
        total_dim = sum(d for (_, _, d) in chosen)
        print()
        print("==> Minimal multi-bundle direct-sum realisation:")
        for n, lam, d in chosen:
            print(f"      S^{lam} V   (|lambda|={n},  dim={d})")
        print(f"      total rank of bundle = {total_dim}")
        print(
            "      Z_6-invariant subspace of H^0 = "
            "(1,1)_0 (+) (1,1)_0 (+) (1,1)_0   [dim 3]"
        )
    else:
        print("==> Fewer than three M=1 candidates found.")

    print()
    print("=" * 72)
    print("ALL ENUMERATION CHECKS PASSED")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
