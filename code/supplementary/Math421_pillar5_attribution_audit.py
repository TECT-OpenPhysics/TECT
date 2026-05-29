#!/usr/bin/env python3
"""Math421 Pillar 5 attribution audit self-test."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUNS_DIR = REPO_ROOT / "Runs" / "math" / "Math421"
RUNS_DIR.mkdir(parents=True, exist_ok=True)
MATH_DIR = REPO_ROOT / "Docs" / "math"

results = []

# Assert 1: Math60-A is meta-consistency theorem (NOT chirality / AS-index substantive theorem)
math60a = (MATH_DIR / "TECT-Math60-A-Meta-Consistency.tex.txt").read_text(encoding="utf-8")[:3000]
is_meta = "meta-consistency" in math60a.lower() or "mutually compatible" in math60a.lower() or "hypothesis lists" in math60a.lower()
has_AS_or_chirality_theorem = "Atiyah-Singer" in math60a or "Fujikawa" in math60a or "chirality theorem" in math60a.lower()
results.append({"id": 1, "check": "Math60-A is meta-consistency (NOT chirality/AS-index theorem)",
    "expected": "is_meta True + has_AS_or_chirality_theorem False",
    "is_meta": is_meta, "has_AS_or_chirality": has_AS_or_chirality_theorem,
    "pass": is_meta and not has_AS_or_chirality_theorem})

# Assert 2: Substantive Pillar 5 anchor candidates exist
candidates = [
    "TECT-Math08.tex.txt", "TECT-Math09.tex.txt", "TECT-Math10.tex.txt", "TECT-Math18.tex.txt",
    "TECT-Math106-BCC-bundle-topology.tex.txt",
    "TECT-Math157-SO10-SM-anomaly-cancellation-rigorous-trace-method.tex.txt",
    "TECT-Math171-AddA-degree-arithmetic-correction.tex.txt",
    "TECT-Math76-Pillar5-SM-embedding.tex.txt",
    "TECT-Math105-Pillar5-PrecisionEW-Consistency.tex.txt",
    "TECT-Math166-Pillar4-subtask2-chiral-zero-modes-on-Math162-bundle.tex.txt",
]
existing = [f for f in candidates if (MATH_DIR / f).exists()]
results.append({"id": 2, "check": "Substantive Pillar 5 anchor candidates exist",
    "expected": ">= 8 of 10 candidates present",
    "n_existing": len(existing), "missing": [f for f in candidates if f not in existing],
    "pass": len(existing) >= 8})

# Assert 3: RETRACTED notes correctly identified
math148 = (MATH_DIR / "TECT-Math148-GAP3-Fujikawa-anomaly-explicit-calculation.tex.txt").read_text(encoding="utf-8")[:3000]
math148_retracted = "RETRACTED" in math148 or "RETRACTION" in math148 or "AUDIT-FLAGGED" in math148
math171 = (MATH_DIR / "TECT-Math171-Pillar4-subtask2-rigorous-AS-index.tex.txt").read_text(encoding="utf-8")[:3000]
math171_disputed = "DISPUTED" in math171 or "AUDIT-FLAGGED" in math171 or "incorrect" in math171.lower()
results.append({"id": 3, "check": "Math148 RETRACTED + Math171 DISPUTED correctly identified",
    "expected": "both flagged in headers",
    "math148_retracted": math148_retracted, "math171_disputed": math171_disputed,
    "pass": math148_retracted and math171_disputed})

# Assert 4: pillar_status.json Pillar 5 reflects Math421 downgrade or AddA promotion
ps = json.loads((REPO_ROOT / "Codes" / "config" / "pillar_status.json").read_text(encoding="utf-8"))
p5 = next((p for p in ps["pillars"] if p["n"] == 5), None)
p5_tier = p5.get("tier") if p5 else None
tier_updated = p5_tier in ["T4", "T6"]  # Either Math421 T4 pending or Math421-AddA T6 promoted
math421_meta = "_math421_pillar5_downgrade" in ps
results.append({"id": 4, "check": "pillar_status.json Pillar 5 reflects Math421 transition",
    "expected": "tier in [T4, T6] + meta block present",
    "p5_tier": p5_tier, "math421_meta_present": math421_meta,
    "pass": tier_updated and math421_meta})

total = len(results); passed = sum(1 for r in results if r["pass"])
artefact = {
    "theory_tag": "Math421-Pillar5-Deep-Dive-Attribution-Audit-2026-05-27",
    "honest_tier_verdict": "T4 STRONG EVIDENCE pending Math421-AddA bookkeeping cleanup (advanced to T6 PROVED CONDITIONAL on 5-hyp set post-AddA)",
    "audit_flagged_excluded": ["Math148 RETRACTED 2026-04-26", "Math171 DISPUTED 2026-04-27"],
    "substantive_anchors": existing,
    "n_checks": total, "n_passed": passed, "all_pass": passed == total, "checks": results,
}
(RUNS_DIR / "pillar5_attribution_audit.json").write_text(json.dumps(artefact, indent=2, ensure_ascii=False), encoding="utf-8")
for r in results:
    assert r["pass"], "Assert " + str(r["id"]) + " FAILED"
print("[Math421] " + str(passed) + "/" + str(total) + " asserts PASS")
print("[Math421] verdict: Pillar 5 T7 inherited UNSUBSTANTIATED; T4 pending → T6 PROVED COND on 5-hyp post-AddA")
sys.exit(0)
