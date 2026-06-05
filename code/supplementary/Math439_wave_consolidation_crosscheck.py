#!/usr/bin/env python3
"""Math439_wave_consolidation_crosscheck.py -- re-asserts every headline
number quoted in the Math439 consolidation note against the four primary
JSON artefacts of the Math435-438 wave (CLAUDE.md 6.3.8)."""
import json, math, os, sys
CLAIMS = []
def claim(name, expected, actual, tol=0.0):
    ok = abs(actual - expected) <= tol if tol else expected == actual
    CLAIMS.append(dict(name=name, expected=expected, actual=actual,
                       tol=tol, passed=bool(ok)))
    assert ok, f"FAIL {name}: {expected} vs {actual}"
def get(path):
    return json.load(open(path))

j435 = get("Runs/math/Math435/g6_corrected_cascade.json")
j436 = get("Runs/math/Math436/hex_exact_wick_bracket.json")
j437 = get("Runs/math/Math437/step5_class_closure.json")
j438 = get("Runs/math/Math438/g3prime_b_multishell_aniso.json")
def cl(j, name):
    for c in j["claims"]:
        if c["name"] == name: return c
    raise KeyError(name)

# Math435 (G6)
claim("435_all_pass", True, all(c.get("passed") for c in j435["claims"]))
claim("435_n_claims", 101, len(j435["claims"]))
rows = j435["corrected_sweep"]
# sweep rows: 17 corrected rows all path alpha unique root
n_alpha = sum(1 for r in rows
              if r.get("path") == "alpha" and r.get("n_roots") == 1)
claim("435_17_rows_alpha", 17, n_alpha)
# Math436 (G1''-3b-HEX)
claim("436_all_pass", True, all(c.get("passed") for c in j436["claims"]))
claim("436_n_claims", 49, len(j436["claims"]))
claim("436_exact_min", 9.532965760841716e-05,
      min(r["dF_exact_anchored"] for r in j436["rows"]
          if "dF_exact_anchored" in r), 1e-12)
claim("436_replica_min_math431", 9.486768603217552e-05,
      j436["metric_defect"]["replica_min"], 1e-12)
# Math437 (Step-5 layer)
claim("437_all_pass", True, all(c.get("passed") for c in j437["claims"]))
claim("437_n_claims", 78, len(j437["claims"]))
claim("437_dip_bound", 0.008520554698216732,  # = 9|u|^3/(64v^2) exact
      j437["constants"]["dip_bound"], 1e-12)
claim("437_Mc", 43.0/1620.0, j437["constants"]["Mc"], 1e-15)
d0 = cl(j437, "Delta0_RegionII")["recorded"]
claim("437_Delta0", 0.126465, d0, 5e-6)
claim("437_rR", 0.30452570866744433, j437["constants"]["r_R"], 5e-9)
# Math438 (G3'-b)
claim("438_all_pass", True, all(c.get("passed") for c in j438["claims"]))
claim("438_n_claims", 27, len(j438["claims"]))
claim("438_threeshell_min", 0.00019067826157433306,
      cl(j438, "threeshell_min")["recorded"]["dF"], 1e-15)
cm = cl(j438, "cross_moments_3shell")["recorded"]
claim("438_m31_211", 432.0, cm["m31_110x3_211"], 1e-9)
claim("438_m31_200", 144.0, cm["m31_110x3_200"], 1e-9)
n_neg = sum(1 for r in j438["rows_threeshell"] if r["dF"] is None or r["dF"] <= 0)
claim("438_zero_negatives", 0, n_neg)
claim("438_aniso_all_positive", True,
      all(r["dF"] > 0 for r in j438["rows_aniso"]))

out = dict(theory_tag="Math439", date="2026-06-04", claims=CLAIMS)
os.makedirs("Runs/math/Math439", exist_ok=True)
json.dump(out, open("Runs/math/Math439/wave_consolidation_crosscheck.json",
                    "w"), indent=1)
npass = sum(1 for c in CLAIMS if c["passed"])
print(f"crosscheck {npass}/{len(CLAIMS)}")
sys.exit(0)
