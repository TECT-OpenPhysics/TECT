#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v1.0
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
"""
live_m_parallel.py
==================

Live longitudinal effective-mass extractor, closing discrepancy D5 of
TECT-Theory-Code-Sync.md (theory tag: Math37-AddA-2026-04-15).

The deprecated `paired_basis_extractor_v2.py` declared `m_parallel` as
an optional kwarg but never computed it, so every bcc_compare paired
summary reported `m_parallel: null`. This module supersedes that logic
by computing `m_parallel` directly and consistently from the live
extractor outputs:

  * per-patch   :  m_parallel[alpha]  = sqrt( M_evals[alpha][0]
                                              / lambda_par_stiff[alpha] )
  * per-pair    :  m_parallel^pair    = sqrt( 0.5 * ( m_parallel[+]^2
                                                   + m_parallel[-]^2 ) )
  * shell mean  :  m_parallel_shell   = < m_parallel[alpha] >
                                        weighted by N_alpha

where

  * M_evals[alpha][0]   — lowest Hessian eigenvalue at patch alpha
                          (from projector_spectral / transport_extractor)
  * lambda_par_stiff[a] — Gamma_|| second-order longitudinal stiffness
                          at patch alpha (from transport_extractor)

This is the numerical analogue of the Math37 AddA closed form
  m^{*2}_TECT = M^2 / lambda_parallel,
with  lambda_parallel  replaced by its per-patch stiffness
  Gamma_||(alpha)  and  M^2  replaced by the measured low eigenvalue.
The shell-mean of  m_parallel[alpha]  is directly comparable to the
theoretical prediction after the  R_patch  convention correction is
applied upstream (see `tect_actual_extractor_pt_v3.py::
compute_theory_mstar2`).

USAGE
-----

    from live_m_parallel import compute_live_m_parallel
    summary = compute_live_m_parallel(transport_results, patch_pairs,
                                       N_alpha=None)
    # summary['m_parallel_per_patch']  : list[float] length N_patch
    # summary['m_parallel_per_pair']   : list[dict]
    # summary['m_parallel_shell_mean'] : float
    # summary['m_parallel_shell_std']  : float
    # summary['theory_tag']            : 'Math37-AddA-2026-04-15'
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

THEORY_TAG = "Math37-AddA-2026-04-15"


def _safe_sqrt(x: float) -> float:
    if not (isinstance(x, (int, float)) and math.isfinite(x)):
        return float("nan")
    return math.sqrt(x) if x > 0.0 else float("nan")


def _lowest_real_eval(M_evals: Any) -> float:
    """Return the lowest real-part eigenvalue from transport_extractor's
    stored M_evals. Handles list, tuple, 1-D array, and complex arrays."""
    if M_evals is None:
        return float("nan")
    arr = np.asarray(M_evals).ravel()
    if arr.size == 0:
        return float("nan")
    re = np.real(arr.astype(np.complex128))
    return float(np.min(re))


def compute_per_patch(
    transport_results: Sequence[Any],
) -> List[Dict[str, float]]:
    """Per-patch m_parallel from transport_extractor output."""
    out: List[Dict[str, float]] = []
    for tr in transport_results:
        patch_idx = getattr(tr, "patch_idx", None)
        if patch_idx is None and isinstance(tr, dict):
            patch_idx = tr.get("patch_idx")

        lam_par = getattr(tr, "lambda_par_stiff", None)
        if lam_par is None and isinstance(tr, dict):
            lam_par = tr.get("lambda_par_stiff")
        lam_par = float(lam_par) if lam_par is not None else float("nan")

        M_ev = getattr(tr, "M_evals", None)
        if M_ev is None and isinstance(tr, dict):
            M_ev = tr.get("M_evals")
        M0 = _lowest_real_eval(M_ev)

        if math.isfinite(lam_par) and abs(lam_par) > 1e-30 and math.isfinite(M0):
            m_par_sq = M0 / lam_par
            m_par = _safe_sqrt(m_par_sq)
        else:
            m_par_sq = float("nan")
            m_par    = float("nan")

        out.append({
            "patch_idx":         int(patch_idx) if patch_idx is not None else -1,
            "M_low":             float(M0),
            "lambda_par_stiff":  float(lam_par),
            "m_parallel_sq":     float(m_par_sq),
            "m_parallel":        float(m_par),
        })
    return out


def compute_per_pair(
    per_patch: Sequence[Dict[str, float]],
    pairs: Iterable[Tuple[int, int]],
) -> List[Dict[str, float]]:
    """Average m_parallel^2 over antipodal patch pairs (G+, G-)."""
    by_idx = {p["patch_idx"]: p for p in per_patch}
    out: List[Dict[str, float]] = []
    for a, b in pairs:
        pa = by_idx.get(int(a))
        pb = by_idx.get(int(b))
        if pa is None or pb is None:
            continue
        m2a = pa.get("m_parallel_sq", float("nan"))
        m2b = pb.get("m_parallel_sq", float("nan"))
        if math.isfinite(m2a) and math.isfinite(m2b):
            m2_pair = 0.5 * (m2a + m2b)
            m_pair  = _safe_sqrt(m2_pair)
        else:
            m2_pair = float("nan")
            m_pair  = float("nan")
        out.append({
            "pair":           (int(a), int(b)),
            "m_parallel_sq":  float(m2_pair),
            "m_parallel":     float(m_pair),
        })
    return out


def compute_shell_mean(
    per_patch: Sequence[Dict[str, float]],
    N_alpha: Optional[Sequence[float]] = None,
) -> Tuple[float, float, float]:
    """Shell-weighted mean and std of m_parallel across patches.

    Returns (mean, std, W_sum). Uses N_alpha weights if provided, else
    uniform weights. Discards NaN entries from the aggregate but still
    counts their contribution to W_sum as zero (diagnostic)."""
    vals   = np.array([p["m_parallel"]    for p in per_patch], dtype=float)
    vals_sq= np.array([p["m_parallel_sq"] for p in per_patch], dtype=float)
    if N_alpha is None:
        w = np.ones_like(vals)
    else:
        w = np.asarray(N_alpha, dtype=float)
        if w.size != vals.size:
            w = np.ones_like(vals)
    mask = np.isfinite(vals) & np.isfinite(w)
    if not mask.any():
        return float("nan"), float("nan"), float(w.sum())
    w_eff = w[mask]
    v_eff = vals[mask]
    W = float(w_eff.sum())
    if W <= 0.0:
        return float("nan"), float("nan"), W
    mean = float(np.sum(w_eff * v_eff) / W)
    var  = float(np.sum(w_eff * (v_eff - mean) ** 2) / W)
    return mean, math.sqrt(max(var, 0.0)), float(w.sum())


def compute_live_m_parallel(
    transport_results: Sequence[Any],
    patch_pairs: Iterable[Tuple[int, int]],
    N_alpha: Optional[Sequence[float]] = None,
    theory_prediction: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Top-level D5 closure: emits per-patch, per-pair, and shell summaries."""
    per_patch = compute_per_patch(transport_results)
    per_pair  = compute_per_pair(per_patch, patch_pairs)
    mean, std, W = compute_shell_mean(per_patch, N_alpha)

    # Consistency check against theory (optional).
    analytic = None
    ratio    = float("nan")
    if theory_prediction is not None:
        analytic = theory_prediction.get("mstar2_theory_analytic")
        R_patch  = theory_prediction.get("R_patch_8to12")
        if (analytic is not None and math.isfinite(float(analytic))
                and math.isfinite(mean) and mean > 0):
            m_sq_shell = mean * mean
            if R_patch is not None and math.isfinite(float(R_patch)) and R_patch > 0:
                m_sq_shell_corr = float(R_patch) * m_sq_shell
            else:
                m_sq_shell_corr = m_sq_shell
            ratio = float(analytic) / m_sq_shell_corr if m_sq_shell_corr > 0 else float("nan")

    return {
        "theory_tag":             THEORY_TAG,
        "m_parallel_per_patch":   per_patch,
        "m_parallel_per_pair":    per_pair,
        "m_parallel_shell_mean":  float(mean),
        "m_parallel_shell_std":   float(std),
        "W_sum":                  float(W),
        "consistency_check": {
            "mstar2_theory_analytic":              analytic,
            "mstar2_numeric_shell_mean_sq":        float(mean * mean) if math.isfinite(mean) else float("nan"),
            "mstar2_analytic_over_numeric_corr":   ratio,
        },
    }


def write_summary(output_dir: Path, summary: Dict[str, Any]) -> Path:
    """Serialize to `live_m_parallel_summary.json`. Converts tuples to
    lists and NaNs to null so the result is valid JSON."""
    def _clean(x: Any) -> Any:
        if isinstance(x, float):
            return None if not math.isfinite(x) else x
        if isinstance(x, tuple):
            return [_clean(v) for v in x]
        if isinstance(x, list):
            return [_clean(v) for v in x]
        if isinstance(x, dict):
            return {k: _clean(v) for k, v in x.items()}
        return x

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "live_m_parallel_summary.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(_clean(summary), f, indent=2)
    return path


if __name__ == "__main__":
    # Dry-run self-test with synthetic data.
    class _Dummy:
        def __init__(self, idx, lam, evs):
            self.patch_idx = idx
            self.lambda_par_stiff = lam
            self.M_evals = evs

    results = [
        _Dummy(0, 0.07167, [0.28, 1.1, 1.4]),
        _Dummy(1, 0.07167, [0.28, 1.0, 1.5]),
        _Dummy(2, 0.07170, [0.27, 1.1, 1.6]),
        _Dummy(3, 0.07170, [0.29, 1.0, 1.5]),
    ]
    pairs = [(0, 1), (2, 3)]
    theory = {"mstar2_theory_analytic": 9.005, "R_patch_8to12": 45.0 / 16.0}
    out = compute_live_m_parallel(results, pairs, theory_prediction=theory)
    print(json.dumps({
        "shell_mean_m_parallel":   out["m_parallel_shell_mean"],
        "shell_std":               out["m_parallel_shell_std"],
        "consistency_check":       out["consistency_check"],
        "theory_tag":              out["theory_tag"],
    }, indent=2))
