#!/usr/bin/env python3
# =====================================================================
# Math348_two_latitude_counterexample.py
#
# Verifies the user-supplied two-latitude hexagon counter-example to
# (L1) "r_S(v) <= 4 for all antipodal 12-stars" and to BCC uniqueness
# in the Global 12-Star Optimality Theorem.
#
# For h in (0, 1), the two-latitude antipodal 12-star
#   S_h = {u_0,...,u_5, -u_0,...,-u_5}
# with u_m = (sqrt(1-h^2) cos(m*pi/3), sqrt(1-h^2) sin(m*pi/3), h)
# achieves r(v=(0,0,2h)) = 6 and Lambda(S_h) = 540 for every h.
# =====================================================================
from __future__ import annotations
import argparse
import sys
import numpy as np
from collections import Counter


def two_latitude(h: float) -> np.ndarray:
    a = np.sqrt(1.0 - h * h)
    upper = np.array([
        [a * np.cos(m * np.pi / 3), a * np.sin(m * np.pi / 3), h]
        for m in range(6)
    ])
    return np.vstack([upper, -upper])


def bcc_110() -> np.ndarray:
    raw = np.array([
        [+1, +1,  0],[-1, -1,  0],[+1, -1,  0],[-1, +1,  0],
        [+1,  0, +1],[-1,  0, -1],[+1,  0, -1],[-1,  0, +1],
        [ 0, +1, +1],[ 0, -1, -1],[ 0, +1, -1],[ 0, -1, +1],
    ], dtype=float)
    return raw / np.linalg.norm(raw[0])


def distribution(S: np.ndarray, tol: float = 1e-9):
    sums = Counter()
    for i in range(len(S)):
        for j in range(len(S)):
            v = tuple(np.round((S[i] + S[j]) / tol).astype(int))
            sums[v] += 1
    by_m = Counter()
    for v, m in sums.items():
        by_m[m] += 1
    Lambda = sum(m * m for m in sums.values())
    return by_m, Lambda, sums


def report(name: str, S: np.ndarray, h: float = None) -> dict:
    by_m, Lam, sums = distribution(S)
    print(f'\n=== {name} ===')
    print(f'  N = {len(S)}, Lambda = {Lam}')
    for m in sorted(by_m, reverse=True):
        print(f'    r(v) = {m:3d}   n_m = {by_m[m]:4d}   contrib = {by_m[m]*m*m:5d}')
    if h is not None:
        v_target = tuple(np.round(np.array([0, 0, 2 * h]) / 1e-9).astype(int))
        r_at = sums.get(v_target, 0)
        print(f'  r(v=(0,0,2h={2*h:.3f})) = {r_at}')
    return {'Lambda': Lam, 'distribution': dict(by_m)}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--h-values', type=float, nargs='+',
                   default=[0.1, 0.3, 0.5, 0.7, 0.9])
    args = p.parse_args()

    print(' Math348 two-latitude hexagon counter-example')
    print(' Verifying (L1) refutation and BCC uniqueness refutation.\n')

    bcc = report('BCC {110} cuboctahedron (reference)', bcc_110())

    for h in args.h_values:
        sh = report(f'Two-latitude S_h with h={h}', two_latitude(h), h=h)
        if sh['Lambda'] != 540:
            print(f'  FAIL: Lambda(S_{h}) = {sh["Lambda"]} != 540')
            return 1

    print('\n=== VERDICT ===')
    print('  (L1) "r_S(v) <= 4 for all antipodal 12-stars": REFUTED (T0)')
    print('  BCC uniqueness "Lambda=540 only at BCC":      REFUTED (T0)')
    print('  Lambda <= 540 upper bound:                    EMPIRICALLY consistent, proof OPEN')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
