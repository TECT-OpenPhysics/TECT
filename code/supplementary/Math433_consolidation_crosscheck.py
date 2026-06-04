#!/usr/bin/env python3
"""Math433_consolidation_crosscheck.py -- CLAUDE.md 6.3.8 verification for the
Math433 Final Consolidation note: every headline number quoted in the
consolidation is re-asserted against the PRIMARY per-gate JSON artefacts
(Math428/429/430/431/432). No new physics is computed; this script certifies
that the consolidation quotes its sources verbatim and that the chain-level
consistency facts (shared r_R, M_R; margin/drift separations) hold.
Exit 0 iff all asserts pass.
"""
import json, os, sys

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

def load(p): return json.load(open(p))
def cl(d, name):
    for c in d["claims"]:
        if c.get("name") == name: return c
    raise KeyError(name)

d428 = load("Runs/math/Math428/g1doubleprime_bloch_logdet.json")
d429 = load("Runs/math/Math429/g1pp1prime_inhomwick.json")
d430 = load("Runs/math/Math430/g1pp2_surface_convergence.json")
d431 = load("Runs/math/Math431/g1pp3_lam_hex_fcc.json")
d432 = load("Runs/math/Math432/g3prime_multishell_ensemble.json")

# ---- chain-level consistency: one operating point across all gates ----
rRs = [d428["r_R"], d429["r_R"], d430["r_R"], d431["r_R"], d432["r_R"]]
MRs = [d428["M_R"], d429["M_R"], d430["M_R"], d431["M_R"], d432["M_R"]]
claim_true("chain_rR_identical", max(rRs)-min(rRs) < 1e-12, f"{rRs}")
claim_true("chain_MR_identical", max(MRs)-min(MRs) < 1e-12, f"{MRs}")
claim("chain_rR_value", 0.3045, rRs[0], 5e-4)

# ---- G1''-0 (Math428 v1.1) ----
claim("g1pp0_anchored_min_calibrated", 7.260e-4,
      cl(d428,"G1pp0_anchored_min_calibrated")["actual"], 1e-6)
claim("g1pp0_anchored_min_worstcase", 6.727e-4,
      cl(d428,"G1pp0_anchored_min_worstcase")["actual"], 1e-6)

# ---- G1''-1' (Math429 v1.1) ----
claim("g1pp1p_min_inbasis", 4.582e-3, d429["min_inbasis"], 1e-5)
claim("g1pp1p_min_anchored", 7.691e-3, d429["min_anchored"], 1e-5)
claim_true("g1pp1p_M_minima_interior",
           not cl(d429,"anchored_min_on_M_boundary")["actual"],
           "anchored min not on M boundary")

# ---- G1''-2 (Math430) ----
sm = cl(d430,"surface_min_anchored")["recorded"]
claim("g1pp2_surface_min", 1.91e-4, sm["dF"], 2e-6)
claim("g1pp2_negatives", 0, cl(d430,"surface_negative_points")["recorded"], 0)
cv = d430["convergence"]["A0.01_M1.0"]
drift430 = abs(cv["c20"]["dF_anchored"] - cv["c12"]["dF_anchored"])
claim_true("g1pp2_argmin_machine_converged", drift430 < 1e-5,
           f"drift {drift430:.2e}")

# ---- G1''-3 (Math431) ----
claim("g1pp3_LAM_min", 3.170e-5, cl(d431,"LAM_estimator_min_rho1")["actual"], 5e-8)
claim("g1pp3_HEX_min", 9.487e-5, cl(d431,"HEX_estimator_min_rho1")["actual"], 5e-8)
claim("g1pp3_FCC_min", 1.2622e-4, cl(d431,"FCC_estimator_min_rho1")["actual"], 5e-8)
claim("g1pp3_FCC_exactWick_min", 5.2335e-4,
      cl(d431,"FCC_exactWick_min_anchored")["recorded"]["dF"], 1e-6)

# ---- G3' (Math432) ----
zm = cl(d432,"zoom_min_anchored")["recorded"]
claim("g3p_zoom_min", 2.302e-4, zm["dF"], 1e-6)
claim("g3p_negatives", 0, cl(d432,"surface_negative_points")["recorded"], 0)
claim("g3p_m31", 144.0, d432["m31"], 1e-6)
claim("g3p_K2_Math426_K0", 0.219034, d432["K2"], 1e-5)
key432 = [k for k in d432["convergence"] if k.startswith("A10.01_A20.0049")][0]
cv432 = d432["convergence"][key432]
drift432 = abs(cv432["c20"]["dF_anchored"] - cv432["c12"]["dF_anchored"])
claim_true("g3p_argmin_drift_lt_1em6", drift432 < 1e-6, f"{drift432:.2e}")
claim_true("g3p_margin_drift_separation_100x",
           zm["dF"] / max(drift432, 1e-12) > 100,
           f"margin {zm['dF']:.2e} vs drift {drift432:.2e}")

# ---- weakest-link audit fact: LAM margin is the chain minimum ----
chain_mins = dict(
    g1pp0=cl(d428,"G1pp0_anchored_min_worstcase")["actual"],
    g1pp1p=d429["min_anchored"],
    g1pp2=sm["dF"], g3p=zm["dF"],
    g1pp3_LAM=cl(d431,"LAM_estimator_min_rho1")["actual"],
    g1pp3_HEX=cl(d431,"HEX_estimator_min_rho1")["actual"],
    g1pp3_FCC=cl(d431,"FCC_estimator_min_rho1")["actual"])
weakest = min(chain_mins, key=chain_mins.get)
claim_true("weakest_link_is_LAM", weakest == "g1pp3_LAM", f"{chain_mins}")
claim_true("all_chain_minima_positive", all(v > 0 for v in chain_mins.values()),
           f"{chain_mins}")

out = dict(theory_tag="Math433", date="2026-06-04", chain_minima=chain_mins,
           weakest_link=weakest, drift430=drift430, drift432=drift432,
           claims=CLAIMS)
os.makedirs("Runs/math/Math433", exist_ok=True)
json.dump(out, open("Runs/math/Math433/consolidation_crosscheck.json","w"),
          indent=1)
npass = sum(1 for c in CLAIMS if c.get("passed"))
print(f"chain minima: {chain_mins}")
print(f"weakest link: {weakest} = {chain_mins[weakest]:+.3e}")
print(f"claims {npass}/{len(CLAIMS)} PASS")
sys.exit(0)
