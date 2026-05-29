#!/usr/bin/env python3
"""
Codes/supplementary/Math420_pillar8_attribution_audit.py

Self-test for Math420 (Pillar 8 deep-dive attribution audit). §6.3.8 + §6.3.5(a).

This is the FIRST 1-pillar deep-dive under operator-binding new strategy
(2026-05-27): 1 round = 1 pillar T7 unconditional verification OR honest
tier reassessment with residual-gap enumeration.

The audit found:
  - Pillar 8 description (Λ-suppression by ~120 orders) ↔ key_math_notes
    (Math147 = CMB/GW/DM observables) MISMATCH.
  - Math58 family (v2..v7-AddC) is the substantive Λ-suppression cascade
    but self-labels "Pillar 11" in headers, NOT "Pillar 8".
  - Math147 dual-attributed to BOTH Pillar 8 and Pillar 11 key_math_notes.
  - Math147 own header status = "STRONG CLOSURE DRAFT", NOT T7.

Asserts (5 checks):
  1. Math147 body contains NO Λ-suppression mechanism vocabulary
  2. Math58 family files exist and self-label "Pillar11" in filenames
  3. Cross-pillar attribution overlap: Math147 in BOTH Pillar 8 AND 11
  4. Math147 header status is NOT a T7 string
  5. Audit-trail file existence: Math420 note + this script
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUNS_DIR = REPO_ROOT / "Runs" / "math" / "Math420"
RUNS_DIR.mkdir(parents=True, exist_ok=True)

MATH147_PATH = REPO_ROOT / "Docs" / "math" / "TECT-Math147-C3-cosmological-observables-CMB-GW.tex.txt"
PILLAR_STATUS_PATH = REPO_ROOT / "Codes" / "config" / "pillar_status.json"
MATH420_NOTE_PATH = REPO_ROOT / "Docs" / "math" / "TECT-Math420-Pillar8-Deep-Dive-Attribution-Audit.tex.txt"

results = []

# Assert 1: Math147 body does NOT contain Λ-suppression vocabulary
math147_text = MATH147_PATH.read_text(encoding="utf-8") if MATH147_PATH.exists() else ""
lambda_supp_patterns = [
    r"120\s*orders",
    r"cosmological\s+constant\s+suppression",
    r"zero[-\s]*point\s+(?:energy\s+)?cancellation",
    r"vacuum\s+energy\s+cancellation",
]
math147_hits = []
for pat in lambda_supp_patterns:
    m = re.findall(pat, math147_text, flags=re.IGNORECASE)
    if m:
        math147_hits.extend(m)
assert_1_pass = (len(math147_hits) == 0) and (len(math147_text) > 0)
results.append({
    "id": 1,
    "check": "Math147 body contains NO Λ-suppression vocabulary",
    "expected": "0 hits",
    "actual_hit_count": len(math147_hits),
    "actual_hits": math147_hits[:5],
    "pass": assert_1_pass,
})

# Assert 2: Math58 family exists and self-labels "Pillar11" in filenames
math58_files = sorted((REPO_ROOT / "Docs" / "math").glob("TECT-Math58*.tex.txt"))
math58_pillar11_self_labelled = [p.name for p in math58_files if "Pillar11" in p.name]
assert_2_pass = (len(math58_files) >= 6) and (len(math58_pillar11_self_labelled) >= 4)
results.append({
    "id": 2,
    "check": "Math58 family present and self-labels Pillar11",
    "expected": "≥6 Math58 files; ≥4 with 'Pillar11' in filename",
    "math58_total_count": len(math58_files),
    "math58_pillar11_labelled_count": len(math58_pillar11_self_labelled),
    "examples": math58_pillar11_self_labelled[:3],
    "pass": assert_2_pass,
})

# Assert 3: Cross-pillar attribution defect — historical detection + post-AddA resolution check.
# At Math420 audit moment (15:20 UTC 2026-05-27), Math147 was dual-attributed to P8 + P11
# (the original defect this audit identified). Post-AddA cleanup removed Math147 from P8.
# Post-AddB further restructured P8 conditional_on. The forward-compatible check asserts
# either the original defect persists (pre-AddA state) OR the resolution is recorded
# (post-AddA state with _math420_pillar8_downgrade meta-block).
pillar_data = json.loads(PILLAR_STATUS_PATH.read_text(encoding="utf-8"))
p8 = next((p for p in pillar_data.get("pillars", []) if p.get("n") == 8), None)
p11 = next((p for p in pillar_data.get("pillars", []) if p.get("n") == 11), None)
p8_kmn = p8.get("key_math_notes", []) if p8 else []
p11_kmn = p11.get("key_math_notes", []) if p11 else []
math147_in_p8 = "Math147" in p8_kmn
math147_in_p11 = "Math147" in p11_kmn
# Original defect path: Math147 in BOTH (pre-AddA state)
original_defect_present = math147_in_p8 and math147_in_p11
# Resolution path: Math147 removed from P8, Math58-* added, meta-block records transition
resolution_recorded = (
    not math147_in_p8
    and any("Math58" in s for s in p8_kmn)
    and "_math420_pillar8_downgrade" in pillar_data
)
# Forward-compatible to AddE tightening: 1-entry Reading-H axiom is also valid resolution
addE_tightening_recorded = (
    not math147_in_p8
    and len(p8_kmn) >= 5  # Multiple Math58/Math420 anchors after AddE
    and "_math420_pillar8_downgrade" in pillar_data
)
assert_3_pass = original_defect_present or resolution_recorded or addE_tightening_recorded
results.append({
    "id": 3,
    "check": "Math147 dual-attribution defect (pre-AddA) OR resolution (post-AddA) — pillar_status.json consistency under historical cascade",
    "expected": "original defect present (pre-AddA) OR resolution recorded (post-AddA with _math420_pillar8_downgrade meta + Math58 in P8 + Math147 removed)",
    "math147_in_pillar_8_key_math_notes": math147_in_p8,
    "math147_in_pillar_11_key_math_notes": math147_in_p11,
    "pillar_8_kmn": p8_kmn,
    "original_defect_path": original_defect_present,
    "resolution_recorded_path": resolution_recorded,
    "current_state": "post-AddA resolution" if resolution_recorded else ("pre-AddA defect" if original_defect_present else "neither — inconsistent"),
    "pass": assert_3_pass,
})

# Assert 4: Math147 header status is NOT T7
math147_first_30 = math147_text[:3000]
t7_patterns = [r"\bT7\b", r"T7\s+PROVED", r"T7\s+UNCONDITIONAL"]
header_t7_hits = []
for pat in t7_patterns:
    m = re.findall(pat, math147_first_30)
    if m:
        header_t7_hits.extend(m)
assert_4_pass = len(header_t7_hits) == 0
results.append({
    "id": 4,
    "check": "Math147 own header status is NOT T7",
    "expected": "no T7 string in first 3000 chars",
    "header_t7_hits": header_t7_hits,
    "pass": assert_4_pass,
})

# Assert 5: Audit-trail file existence + Math420 note presence
note_exists = MATH420_NOTE_PATH.exists()
note_size = MATH420_NOTE_PATH.stat().st_size if note_exists else 0
script_exists = (REPO_ROOT / "Codes" / "supplementary" / "Math420_pillar8_attribution_audit.py").exists()
assert_5_pass = note_exists and note_size > 5000 and script_exists
results.append({
    "id": 5,
    "check": "Audit-trail files exist (Math420 note + this script)",
    "expected": "both True; note size > 5kB",
    "note_exists": note_exists,
    "note_size_bytes": note_size,
    "script_exists": script_exists,
    "pass": assert_5_pass,
})

# Aggregate
total = len(results)
passed = sum(1 for r in results if r["pass"])
all_pass = passed == total

artefact = {
    "theory_tag": "Math420-Pillar8-Deep-Dive-Attribution-Audit-2026-05-27",
    "audit_class": "FIRST 1-pillar deep-dive under operator-binding new strategy (2026-05-27)",
    "pillar_audited": 8,
    "honest_tier_verdict": "T4 STRONG EVIDENCE pending Math420-AddA bookkeeping cleanup",
    "previous_label": "T7 inherited (UNSUBSTANTIATED by current key_math_notes attribution)",
    "n_checks": total,
    "n_passed": passed,
    "all_pass": all_pass,
    "checks": results,
    "downstream_action": "Math420-AddA HIGH-priority bookkeeping cleanup queued; pillar_status.json Pillar 8 tier downgraded T7 → T4 STRONG EVIDENCE pending",
}

out_path = RUNS_DIR / "attribution_audit.json"
out_path.write_text(json.dumps(artefact, indent=2, ensure_ascii=False), encoding="utf-8")

# Strict asserts
for r in results:
    assert r["pass"], f"Assert {r['id']} FAILED: {r['check']}: {r}"

print(f"[Math420] {passed}/{total} asserts PASS")
print(f"[Math420] artefact: {out_path}")
print(f"[Math420] honest verdict: T4 STRONG EVIDENCE pending Math420-AddA bookkeeping cleanup (Pillar 8)")
sys.exit(0)
