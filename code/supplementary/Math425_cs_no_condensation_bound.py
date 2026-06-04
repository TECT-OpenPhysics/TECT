#!/usr/bin/env python3
"""Math425_cs_no_condensation_bound.py -- Cauchy-Schwarz no-condensation
theorem: numerical verification + adversarial probe (CLAUDE.md 6.3.8).

THEOREM (Math425): for the locked TECT canonical mean-field functional
(u = -0.86 < 0, v = +3.24 > 0, kernel >= r), ANY non-zero stationary field
configuration with finite cell-averaged moments requires
    u^2 <phi^4>^2 >= 4 kappa v <phi^2><phi^6>,  kappa >= r,
while Cauchy-Schwarz gives  J := <phi^4>^2/(<phi^2><phi^6>) <= 1.
Hence NO mean-field condensate of ANY form (any phases, amplitudes,
spectrum incl. multi-shell) exists whenever
    r > r* = u^2/(4v) = 0.0570679   <=>   mu^2 > mu^2* = -0.156966.
Canonical r = +0.2190336: margin 4 r v/u^2 = 3.83812 > 1.

Closes operator-audit gate G2 at the canonical point IN FULL and removes
the single-shell restriction (H2) at mean-field level for mu^2 > mu^2*.
The adversarial probe tries to push J above 1 over random + locally
optimised phase/amplitude patterns (single- and multi-shell); it must fail.
"""
import json, math, os, sys
import numpy as np

U, V, Q0 = -0.86, 3.24, 0.6801747616
R_CAN = 0.005 + Q0 ** 4
CLAIMS = []

def claim(name, expected, actual, tol):
    ok = abs(actual - expected) <= tol
    CLAIMS.append(dict(name=name, expected=expected, actual=actual,
                       tol=tol, passed=bool(ok)))
    assert ok, f"FAIL {name}: {expected} vs {actual}"

def claim_true(name, cond, detail=""):
    CLAIMS.append(dict(name=name, expected=True, actual=bool(cond),
                       tol=0, passed=bool(cond), detail=detail))
    assert cond, f"FAIL {name}: {detail}"

# ---- 1. threshold arithmetic ----
r_star = U * U / (4 * V)
mu2_star = r_star - Q0 ** 4
margin = 4 * R_CAN * V / (U * U)
claim("r_star_u2_over_4v", 0.0570679, r_star, 1e-6)
claim("mu2_star_boundary", -0.156966, mu2_star, 1e-5)
claim("canonical_margin_4rv_u2", 3.83812, margin, 1e-4)
claim_true("margin_exceeds_CS_bound", margin > 1.0, f"margin={margin}")

# ---- 2. lattice J-values (CS consistency of Math424-AddA enumeration) ----
LATT = dict(LAM=(1, 6, 20), HEX=(3, 90, 2040),
            FCC=(4, 216, 8000), BCC=(6, 540, 42240))
J_expect = dict(LAM=0.90000, HEX=0.66176, FCC=0.72900, BCC=0.57528)
for nm, (n, N4, N6) in LATT.items():
    J = N4 * N4 / (2 * n * N6)
    claim(f"J_{nm}", J_expect[nm], J, 1e-4)
    claim_true(f"J_{nm}_below_CS", J < 1.0)
claim("LAM_shortfall_equivalence", 4.2646,
      margin / (36 / 40.0), 1e-3)

# ---- 3. adversarial probe ----
SHELLS = {
    "HEX": [(2, 0, 0), (-1, 1, 0), (-1, -1, 0)],
    "BCC": [(1, 1, 0), (1, -1, 0), (1, 0, 1), (1, 0, -1), (0, 1, 1), (0, 1, -1)],
}
G = 32
ax = np.arange(G) * (2 * np.pi / G)
X, Yg, Z = np.meshgrid(ax, ax, ax, indexing="ij")

def J_of(vectors, amps, phases):
    phi = np.zeros_like(X)
    for (k, a, th) in zip(vectors, amps, phases):
        phi += a * np.cos(k[0] * X + k[1] * Yg + k[2] * Z + th)
    m2 = float(np.mean(phi ** 2)); m4 = float(np.mean(phi ** 4))
    m6 = float(np.mean(phi ** 6))
    return m4 * m4 / (m2 * m6) if m2 > 0 and m6 > 0 else 0.0

rng = np.random.default_rng(424)
sup_found = {}
for nm, vecs in SHELLS.items():
    best = J_of(vecs, np.ones(len(vecs)), np.zeros(len(vecs)))
    for trial in range(40):
        a = rng.uniform(0.2, 1.0, len(vecs))
        th = rng.uniform(0, 2 * np.pi, len(vecs))
        cur = J_of(vecs, a, th)
        for sweep in range(3):
            for j in range(len(vecs)):
                for d_th in (0.3, -0.3, 0.1, -0.1):
                    th2 = th.copy(); th2[j] += d_th
                    c2 = J_of(vecs, a, th2)
                    if c2 > cur:
                        th, cur = th2, c2
                for d_a in (1.2, 0.8):
                    a2 = a.copy(); a2[j] *= d_a
                    c2 = J_of(vecs, a2, th)
                    if c2 > cur:
                        a, cur = a2, c2
        best = max(best, cur)
    sup_found[nm] = best
    claim_true(f"adversarial_sup_J_{nm}_below_1", best <= 1.0 + 1e-9,
               f"sup_found={best:.6f}")

MS = [(1, 1, 0), (1, -1, 0), (0, 1, 1), (2, 0, 0), (0, 2, 0), (1, 1, 1)]
best_ms = 0.0
for trial in range(200):
    a = rng.uniform(0.0, 1.0, len(MS))
    th = rng.uniform(0, 2 * np.pi, len(MS))
    best_ms = max(best_ms, J_of(MS, a, th))
claim_true("adversarial_sup_J_multishell_below_1", best_ms <= 1.0 + 1e-9,
           f"sup={best_ms:.6f}")

# ---- 4. direct impossibility at canonical ----
for nm, s in sup_found.items():
    claim_true(f"no_condensate_{nm}_canonical",
               U * U * s < 4 * R_CAN * V,
               f"u^2 J={U*U*s:.4f} < 4rv={4*R_CAN*V:.4f}")

out = dict(theory_tag="Math425", date="2026-06-04",
           r_star=r_star, mu2_star=mu2_star, canonical_margin=margin,
           lattice_J={k: LATT[k][1] ** 2 / (2 * LATT[k][0] * LATT[k][2])
                      for k in LATT},
           adversarial_sup=sup_found, adversarial_sup_multishell=best_ms,
           claims=CLAIMS)
os.makedirs("Runs/math/Math425", exist_ok=True)
json.dump(out, open("Runs/math/Math425/cs_bound_verification.json", "w"),
          indent=1)
npass = sum(1 for c in CLAIMS if c["passed"])
print(f"r* = {r_star:.7f}  mu2* = {mu2_star:.6f}  margin = {margin:.5f}")
print("adversarial sup J:",
      {k: round(v, 5) for k, v in sup_found.items()},
      " multishell:", round(best_ms, 5))
print(f"claims: {npass}/{len(CLAIMS)} PASS")
sys.exit(0)
