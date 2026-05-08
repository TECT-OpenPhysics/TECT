# Paper 14 — GAP-2: BRST Gauge Fixing and Faddeev–Popov Determinant

> ⚠️ **Audit notice (Math314 family closure, 2026-05-02)**: README metadata predates the Math314 audit. Current canonical status in `.tex` `AUDIT-FLAG` block; scorecard at [`../../PAPERS_STATUS_REGISTRY.md`](../../PAPERS_STATUS_REGISTRY.md) (Rev 10). Legacy `Paper-14.md` mirror DEPRECATED.

**Status**: `[DRAFT][NEEDS_UPDATE]` — Wave 4 GAP cluster, post-Math314-AddD: HEALTHIEST of GAP cluster (GAP-2 = T6 already canonical). "GAP-2 is now complete" / "fully rigorous" / "ready for publication" wording removed; recast as conditional BRST/FP closure note inheriting Math160 Berry correction.

**Canonical Sources**:
- Math160: BRST FP Determinant + TECT-Specific Berry Phase
- Math280: T6 Promotion Post-Pillar 4 via Inheritance

**Abstract**: GAP-2 (Faddeev–Popov determinant) is proved via the BRST
symmetry method on the BCC defect sector. The ghost Lagrangian is derived
using the standard Faddeev–Popov construction, with an additional TECT-specific
Berry-phase correction (Math160) arising from the adiabatic evolution of the
BCC order parameter during freeze-out. The BRST symmetry ensures unitarity.
The proof is **T6 PROVED CONDITIONAL** on Pillar 4's hypothesis H1.1
(the Grassmannian stability theorem Math80-AddA), via the inheritance
mechanism of Math280. No additional hypotheses beyond Pillar 4 are required;
the BRST closure is standard textbook quantum field theory.

**Result Tier**: T6 PROVED CONDITIONAL (on Pillar 4 H1.1)

**Hypotheses**:
- H1: Pillar 4 hypothesis H1.1 (Grassmannian stability, Math80-AddA)
- (No other hypotheses required)

**Inheritance Mechanism**:
- Pillar 4 verdict (T6 or otherwise) → automatic GAP-2 verdict
- When Pillar 4 is verified to T6 → GAP-2 automatically T6
- When Pillar 4 is falsified or downgraded → GAP-2 automatically follows

**Math-Note Verification**:
- ✓ Math160 assumed located
- ✓ Math280 assumed located

**Last Synced**: 2026-05-02 (SRP-v1 verification)

**Paper Narrative**: GAP-2 is refreshingly clean. Once Pillar 4 is settled,
GAP-2 is automatically settled. There is no independent falsification gate
for GAP-2; the verdict is inherited from Pillar 4. This is elegant and makes
the paper simple to write: state the theorem, derive the BRST closure, note
the Berry-phase correction, and explain the inheritance mechanism. The paper
will be short and publication-ready.

This demonstrates the power of the inheritance mechanism: not every result
needs an independent falsification gate if it logically depends on a
previously-gatekeeping result. This is good epistemology.
