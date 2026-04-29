# TECT Proof-Completion Checklist

**Binding from**: 2026-04-21 (rev. 2026-04-21 late)
**Source**: GPT peer-review 2026-04-21, adopted as project-wide standard in commit of
`Math_IR_Bound-v4-BZ-integrator + GPT peer-review integration`; revised following
`Math_IR_Bound-v4-shell-adaptive` closure (2026-04-21 late).
**Scope**: Every theorem or pillar claim in the TECT theoretical framework
whose status is tracked in `docs/status/TOE-FACT-SHEET.md` or any pillar ledger.
**Maintainer**: Jusang Lee (jtkor@outlook.com)

This document fixes the classification criteria used across TECT ledgers.
It is the canonical mapping from **proof state** to **status label**.

---

## 1. The four closure criteria

Each proof of a TECT claim is evaluated along four orthogonal axes:

1. **Logical closure (LC)** — every logical step in the proof chain is
   explicit. No tacit invocation of off-stack axioms. All hypotheses
   promoted to explicit labels (H-*) and separately verifiable.

2. **Sign / bound closure (SB)** — the final quantitative output
   (sign of an invariant, direction of an inequality, numerical bound)
   is established rigorously. For sign-definite claims this means
   either (a) a rigorous interval enclosure excluding zero, or
   (b) an analytic proof of sign with no unquantified remainder.
   For numerical-magnitude claims, the enclosure width must be
   smaller than the claimed result.

3. **Current-mainline alignment (CM)** — the computation is performed
   at the current TECT mainline parameters
   $(q_0, \mu^2, \lambda, \gamma)$ as recorded in the most recent
   `PDE/continuation_N<NN>_v<VV>.log`, not at stale anchors.
   Any re-baselining of the mainline invalidates CM for all dependent
   claims and forces re-computation.

4. **Reproducibility (RP)** — a deterministic computation exists
   (`PDE/*.py` or `tools/*.py`) that reproduces every numerical result
   in the proof to bit-level (for symbolic) or to documented
   floating-point tolerance (for numerical). Script md5 and input
   parameters are recorded in `docs/manual/CODE_MANUAL.md`.

---

## 2. Status-label mapping

| LC | SB | CM | RP | Label |
|----|----|----|----|-------|
| ✓  | ✓  | ✓  | ✓  | **PROVED** |
| ✓  | ✓* | ✓  | ✓  | **NEAR-FINAL CONDITIONAL** (SB via numerical convergence, interval enclosure pending) |
| ✓  | —  | ✓  | ✓  | **CONDITIONAL** (one or more H-hypothesis not yet independently verified) |
| —  | —  | ✓  | ✓  | **PARTIAL** (key intermediate lemma missing) |
| —  | —  | —  | —  | **SCAFFOLD** (architecture exists, closure pending data) |
| —  | —  | —  | —  | **NOT ADDRESSED** (no proof attempt) |

The label **PROVED** requires all four criteria ✓.

The distinction between **NEAR-FINAL CONDITIONAL** and **PROVED** is
whether the sign/bound is established via (a) rigorous interval
certificate (→ PROVED) or (b) numerical grid-convergence only
(→ NEAR-FINAL CONDITIONAL). The latter is considered "operationally
closed but formally pending" under TECT editorial policy.

The distinction between **CONDITIONAL** and **NEAR-FINAL CONDITIONAL**
is whether the outstanding gap is (a) an unverified theoretical
hypothesis (→ CONDITIONAL) or (b) a technical rigor upgrade from
numerical to interval arithmetic (→ NEAR-FINAL CONDITIONAL).

---

## 3. Application to the 11-pillar scorecard

The current status of each pillar per this checklist, as of 2026-04-21 (late):

| Pillar | Claim | LC | SB | CM | RP | Label | Notes |
|--------|-------|----|----|----|----|-------|-------|
| 1 | Brazovskii gap | ✓ | ✓ | ✓ | ✓ | PROVED | Math10-14, Math52-53 |
| 2 | Locked-phase effective-action positivity | ✓ | ✓ | ✓ | ✓ | PROVED | Math57-v2 (re-baselined) |
| 3 | Dimensional reduction $S^3 \to \mathbb{R}$ | ✓ | — | ✓ | ✓ | CONDITIONAL | Math50-addendum, 1-loop only |
| 4 | Three-generation structure | ✓ | ✓ | ✓ | ✓ | PROVED | Math49 / Math49d-R5 |
| 5 | Anomaly cancellation | ✓ | ✓ | ✓ | ✓ | PROVED | Math49b-v3 + Witten SU(2) |
| 6 | Spin-statistics | ✓ | ✓ | ✓ | ✓ | PROVED | Math49c-v3 / Math-SpinStat |
| 7 | Equivalence principle | ✓ | — | ✓ | ✓ | CONDITIONAL | Math_EP-v3 (MPD-suppression) |
| 8 | Emergent Lorentz invariance | ✓ | ✓ | ✓ | ✓ | PROVED | Math_IR_Bound-v4 chain: $J_1>0$ PROVED (v4-2 interval), $c_4(\epsilon)>0$ PROVED (v4-shell-adaptive, rigorous mpmath.iv enclosure $c_4\in[+1.402\!\times\!10^{-3},\,+2.368\!\times\!10^{-3}]$ at $N=64$, $\mathrm{dps}=40$); BZ volume formula patched v1.0 $\to$ v2.0 (Irwin-Hall CDF) |
| 9 | Mass gap via condensate | ✓ | — | ✓ | ✓ | CONDITIONAL | Math37 / Math55 |
| 10 | Gravitational sector | — | — | — | — | SCAFFOLD | Math58/59, coupling open |
| 11 | Cosmological constant | — | — | — | — | NOT ADDRESSED | Math58-v2 skeleton only; instantiation pending Task #54 |

**Summary**: 6 PROVED, 0 NEAR-FINAL CONDITIONAL, 3 CONDITIONAL, 1 SCAFFOLD, 1 NOT ADDRESSED.

This scorecard supersedes all prior status tables. Any pillar
reclassification must be documented in a CHANGELOG entry tagged
`[Proof-Completion-Checklist update]`.

---

## 4. Enforcement

1. Every theorem or pillar claim in a TECT Math note (`docs/math/TECT-MathNN*.tex.txt`)
   must carry an explicit status label from §2 in its abstract or
   Remark block.

2. Any mismatch between the claim's in-text label and the scorecard
   of §3 is a HOLD-worthy defect. The note must be patched to match
   the scorecard, or the scorecard must be updated via a new CHANGELOG
   entry.

3. Every new numerical computation under `PDE/*.py` or `tools/*.py`
   must document, in `docs/manual/CODE_MANUAL.md`, which of the four
   criteria (LC / SB / CM / RP) it advances for which pillar.

4. The distinction between "independent proof" and "companion PASS
   check" is load-bearing. A numerical simulation that merely
   reproduces the output of an analytic theorem under its hypotheses
   is a companion PASS check (supports RP); it does not advance
   LC, SB, or CM. Labelling of simulation results must reflect this
   distinction.

---

## 5. History

- **2026-04-21** (this document, v1.0): checklist adopted from GPT
  peer-review 2026-04-21. Pillar 8 reclassified from prior mixed
  PROVED/NEAR-FINAL labelling to uniform NEAR-FINAL CONDITIONAL
  pending shell-adaptive interval certificate. Math49c-v3-sim
  reclassified as companion PASS check.
- **2026-04-21 (late)** (v1.1): Pillar 8 upgraded
  **NEAR-FINAL CONDITIONAL** $\to$ **PROVED** via
  `Math_IR_Bound-v4-shell-adaptive` (rigorous mpmath.iv enclosure of the
  1-loop anisotropy coefficient at Brazovskii FP,
  $c_4(\epsilon)\in[+1.402\!\times\!10^{-3},\,+2.368\!\times\!10^{-3}]>0$ at
  $N_{\rm octant}=64$, $\mathrm{dps}=40$; half-width
  $4.83\!\times\!10^{-4}$ sign-definite). Closed-form radial primitive
  $F(r)$ derived via partial-fraction factorization
  $m^2+(r^2-q_0^2)^2 = [(r-p)^2+q^2]\,[(r+p)^2+q^2]$ with
  $p=\sqrt{(R+q_0^2)/2}$, $q=\sqrt{(R-q_0^2)/2}$,
  $R=\sqrt{q_0^4+m^2}$, combined with $O_h$-fundamental-domain
  $(s,t)$ reduction and centered-form identity $\int_{D'} P_4\,d\Omega=0$
  to cancel the cancellation-dominated wrap. Companion
  patch: `truncated_octahedron_volume()` rewritten from the
  narrow-validity cube-minus-corner-tetrahedra formula
  (V$_{\rm BZ}=7/2$, valid only for $2B\le A\le 3B$) to the
  Irwin-Hall CDF piecewise form valid on all $A/B\ge 0$;
  mainline ($A=3/2$, $B=1$, $s=3/2\in[1,2]$) value corrected to
  $V_{\rm BZ}=4$, matching the numerical mask count.
  Pillar-count summary updated 5/1/3/1/1 $\to$ 6/0/3/1/1
  (PROVED / NEAR-FINAL / CONDITIONAL / SCAFFOLD / NOT ADDRESSED).
