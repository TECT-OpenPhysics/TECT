#!/usr/bin/env python3
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: unregistered
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
"""
phase4_manual_extrapolation.py
------------------------------
Manual Phase 4 continuum-limit extrapolation from individual
Phase 1-3 runs at N = 32, 64, 128.

Usage:
    python phase4_manual_extrapolation.py

Expects:
    newton_rigorous_N32/proof_results.json
    newton_rigorous_N64/proof_results.json
    newton_rigorous_N128/proof_results.json

Performs:
    Linear fit  m*²(h²) = m₀ + c · h²
    where h = L / N  (lattice spacing)

    If m₀ > 0 and all grids pass Phases 1-3, the continuum
    limit is declared consistent.
"""

import json
import os
import sys
import numpy as np

# ── Configuration ──────────────────────────────────────────
L = 20.0 * np.pi  # 62.831853...
Ns = [32, 64, 128]
result_dirs = [f"newton_rigorous_N{N}" for N in Ns]

# ── Collect results ────────────────────────────────────────
print("=" * 70)
print("  Phase 4: Manual Continuum-Limit Extrapolation")
print("=" * 70)
print(f"  L = {L:.6f}")
print(f"  Grids: N = {Ns}")
print()

data = []
all_pass = True

for N, rdir in zip(Ns, result_dirs):
    path = os.path.join(rdir, "proof_results.json")
    if not os.path.isfile(path):
        print(f"  [MISSING] {path}")
        print(f"           Run Phase 1-3 at N={N} first.")
        all_pass = False
        continue

    with open(path, "r", encoding="utf-8") as f:
        res = json.load(f)

    p1 = res.get("phase1", {})
    p2 = res.get("phase2", {})
    p3 = res.get("phase3", {})

    converged = p1.get("converged", False)
    m_star_sq = p2.get("m_star_sq", float("nan"))
    stable = p2.get("stable", False)
    delta_F = p3.get("delta_F", float("nan"))
    favorable = p3.get("favorable_vs_vacuum", False)

    h = L / N
    pass_all = converged and stable and favorable

    status = "PASS" if pass_all else "FAIL"
    if not pass_all:
        all_pass = False

    print(f"  N={N:4d}  h={h:.4f}  h²={h**2:.4f}")
    print(f"    Phase 1 (existence):     {'PASS' if converged else 'FAIL'}")
    print(f"    Phase 2 (stability):     {'PASS' if stable else 'FAIL'}"
          f"   m*² = {m_star_sq:.6e}")
    print(f"    Phase 3 (favorability):  {'PASS' if favorable else 'FAIL'}"
          f"   ΔF = {delta_F:.6e}")
    print(f"    Overall: {status}")
    print()

    data.append({
        "N": N, "h": h, "h2": h ** 2,
        "m_star_sq": m_star_sq,
        "delta_F": delta_F,
        "pass": pass_all,
    })

if len(data) < 2:
    print("  Not enough data for extrapolation. Need at least 2 grids.")
    sys.exit(1)

# ── Linear fit: m*²(h²) = m₀ + c · h² ────────────────────
x = np.array([d["h2"] for d in data])
y = np.array([d["m_star_sq"] for d in data])
mask = np.isfinite(y)

if np.sum(mask) < 2:
    print("  Not enough finite m*² values for fit.")
    sys.exit(1)

coeffs = np.polyfit(x[mask], y[mask], deg=1)
c_slope = coeffs[0]
m0 = coeffs[1]

# Fit quality
y_fit = c_slope * x[mask] + m0
residuals = y[mask] - y_fit
max_rel_resid = float(np.max(np.abs(residuals / y[mask])))
r_squared = 1.0 - np.sum(residuals ** 2) / np.sum((y[mask] - np.mean(y[mask])) ** 2)

print("=" * 70)
print("  Continuum-Limit Extrapolation: m*²(h²) = m₀ + c · h²")
print("=" * 70)
print()
print(f"  {'N':>6s}  {'h²':>12s}  {'m*² (measured)':>16s}  {'m*² (fit)':>16s}  {'residual':>12s}")
print(f"  {'─'*6}  {'─'*12}  {'─'*16}  {'─'*16}  {'─'*12}")
for i, d in enumerate(data):
    if mask[i]:
        fit_val = c_slope * d["h2"] + m0
        res_val = d["m_star_sq"] - fit_val
        print(f"  {d['N']:6d}  {d['h2']:12.4f}  {d['m_star_sq']:16.6e}  {fit_val:16.6e}  {res_val:12.2e}")
print()
print(f"  m₀ (continuum limit) = {m0:.6e}")
print(f"  c  (lattice artifact) = {c_slope:.6e}")
print(f"  R² = {r_squared:.6f}")
print(f"  max |residual/m*²|   = {max_rel_resid:.2e}")
print()

# ── Verdict ────────────────────────────────────────────────
verdict_m0 = m0 > 0
verdict_fit = max_rel_resid < 0.1  # 10% threshold
verdict_all_pass = all_pass

print("=" * 70)
print("  VERDICT")
print("=" * 70)
print(f"  m₀ > 0?                 {'YES' if verdict_m0 else 'NO'}"
      f"   (m₀ = {m0:.6e})")
print(f"  Linear fit quality?     {'GOOD' if verdict_fit else 'POOR'}"
      f"   (max rel resid = {max_rel_resid:.2e})")
print(f"  All grids pass Ph1-3?   {'YES' if verdict_all_pass else 'NO'}")
print()

if verdict_m0 and verdict_fit and verdict_all_pass:
    print("  ★ CONTINUUM LIMIT: PASS")
    print("    The BCC condensate mass gap m*² > 0 survives")
    print("    the continuum limit (h → 0) extrapolation.")
else:
    reasons = []
    if not verdict_m0:
        reasons.append("m₀ ≤ 0 (mass gap vanishes in continuum)")
    if not verdict_fit:
        reasons.append("poor linear fit (higher-order lattice artifacts?)")
    if not verdict_all_pass:
        reasons.append("not all grids passed Phases 1-3")
    print("  ✗ CONTINUUM LIMIT: FAIL")
    for r in reasons:
        print(f"    - {r}")

print("=" * 70)

# ── Save summary ───────────────────────────────────────────
summary = {
    "L": float(L),
    "grids": [d["N"] for d in data],
    "h_values": [d["h"] for d in data],
    "m_star_sq_values": [d["m_star_sq"] for d in data],
    "delta_F_values": [d["delta_F"] for d in data],
    "all_grids_pass": all_pass,
    "fit": {
        "m0_continuum": float(m0),
        "c_slope": float(c_slope),
        "R_squared": float(r_squared),
        "max_rel_residual": float(max_rel_resid),
    },
    "continuum_pass": bool(verdict_m0 and verdict_fit and verdict_all_pass),
}

outpath = "phase4_continuum_summary.json"
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, allow_nan=False)
print(f"\n  Summary saved to {outpath}")
