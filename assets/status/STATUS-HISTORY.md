# TECT Status History — Append-Only Ledger of Pillar Tier Changes

**Binding from**: 2026-05-07
**Purpose**: Single chronological ledger of every change to the canonical 11-Pillar status scorecard (`Docs/status/TOE-FACT-SHEET.md`). Each entry records the date, the pillar(s) affected, the tier transition (T0–T7), the canonical Math note(s) responsible, the R-tag if applicable, and a one-line rationale. Append-only: never edit past entries.

**Direction convention**:
- ⬆ **UPGRADE**: tier improvement (e.g., T4 → T6).
- ⬇ **DOWNGRADE**: tier regression (e.g., T6 → T4).
- ⬇⬇ **REFUTATION**: explicit T0 REFUTED (counter-example or numerical falsification).
- ↺ **WORDING**: scope or wording revision; tier label unchanged but operational meaning narrowed/widened.
- ↪ **SPLIT**: single pillar tier split into regime-dependent sub-rows (rare).

**Source-of-truth contract** (CLAUDE.md §2):
- The pillar-level Math note (cited in each entry) is the canonical evidence.
- This ledger is a navigation/audit layer; in case of conflict, the pillar-level note overrides this ledger.
- Entries are written in the same atomic commit as the underlying Math note (CLAUDE.md §3).

**Operational rule**: any change to the Stage-1 scorecard rows in `TOE-FACT-SHEET.md` MUST produce a corresponding entry here. Verified by `Codes/tools/status_history_tracker.py` (planned; see `Docs/policy/STATUS_PROPAGATION_POLICY.md`).

---

## 2026-05-07 — Math348 + Math350 + Math349-AddA: BCC-uniqueness refuted, deep-regime BCC saddle confirmed

### Entry 2026-05-07-03 ↪ SPLIT — Pillar 1 (BCC ground state)

**Pillar**: 1 — BCC ground state.
**Transition**: single tier `T6 PROVED CONDITIONAL` (homogeneous) → regime-split:
- Shallow positive $\mu^2$ ($+5\times 10^{-3}$, Math82-AddD anchor): **T4 STRONG EVIDENCE** retained.
- Deep negative $\mu^2$ ($-0.7$, Math350 verdict): **T0 REFUTED** (saddle of Morse index $\ge 5$).
- Regime-transition $\mu^2_*$: **T1 OPEN** (location currently unknown, $\mu^2_* \in (-0.7, +5\times 10^{-3})$).
- True deep-regime ground state: **T1 OPEN** (mainline target M5).

**Canonical evidence**:
- `Docs/math/TECT-Math350-Math292-G3-N32-DeepRegime-Saddle.tex.txt` (5 LOBPCG eigenvalues all negative, $|\lambda_{\min}|=0.237$, zero-mode contamination $\le 4\times 10^{-14}$, asymmetry probe $1.24\times 10^{-5}$).
- `Docs/math/TECT-Math82-AddD.tex.txt` (shallow-regime stability anchor, retained).
- `Docs/math/TECT-Math349-AddA-User-Audit-Acknowledgment-and-Math350-Reprioritisation.tex.txt` (Mechanism re-prioritisation, M5 added).

**R-tag**: `R-2026-05-07-Math350-DeepRegime-BCC-Saddle`.

**Rationale**: Math292 G3 transverse-Hessian acceptance gate, executed via LOBPCG at $N=32$, $\mu^2 = -0.7$, returns five negative eigenvalues with zero-mode contamination $\le 4\times 10^{-14}$. The configuration produced by the operator-supplied continuation seed (`math236_A1p0_seeded_N32_resumed/Psi_best_F.npy`) is therefore a saddle, not a local minimum, in the deep regime. Math82-AddD's shallow-regime BCC stability is unaffected. Pillar 1 must therefore carry a regime-dependent label rather than a homogeneous one.

---

### Entry 2026-05-07-02 ⬇⬇ REFUTATION — BCC mean-field uniqueness clause (Math320 / Math339 / Math347 chain)

**Pillar**: 1 (BCC ground state) — uniqueness clause.
**Transition**: claimed **T6 PROVED CONDITIONAL** ("BCC is the unique mean-field $\Lambda$-maximiser among antipodal 12-stars") → **T0 REFUTED**.
**Upper bound $\Lambda \le 540$**: previously claimed at T6, returns to **T1 OPEN** (empirically supported by $5 \times 10^3$ random scan but no rigorous proof; previous "proof" used $r(v) \in \{2,4\}$ which is now known false).

**Canonical evidence**:
- `Docs/math/TECT-Math348-TwoLatitudeHexagon-CounterExample-L1-and-BCC-Uniqueness-Refuted.tex.txt` (explicit construction: for $S_h = \{u_0,\dots,u_5,-u_0,\dots,-u_5\}$ with $u_m = (\sqrt{1-h^2}\cos(m\pi/3), \sqrt{1-h^2}\sin(m\pi/3), h)$ and $v = (0,0,2h)$, $r_{S_h}(v) = 6$ for every $h \in (0,1)$, and $\Lambda(S_h) = 540 = \Lambda(S_{\rm BCC})$).
- `Docs/math/TECT-Math349-Math348-Cascading-Impact-Analysis.tex.txt` (per-pillar impact mapping).

**R-tag**: `R-2026-05-07-Math339-BCC-Uniqueness-Refuted`.

**Rationale**: User-supplied two-latitude hexagon family $\{S_h\}_{h \in (0,1)}$ achieves $\Lambda(S_h) = 540$ with multiplicity distribution $(n_1, n_2, n_4, n_6) = (12, 30, 12, 2)$, structurally distinct from BCC's $(12, 24, 18, 0)$. Three consecutive closure attempts (Math320, Math339, Math347) had implicitly assumed $r(v) \le 4$ for all generic off-diagonal $v$, which is false on $S_h$ at $v = (0,0,2h)$. Both the uniqueness clause and the upper-bound proof are refuted; only the empirical bound (numerical scans $\le 540$) survives.

---

### Entry 2026-05-07-01 ↺ WORDING — Math349 Mechanism 4 + cosmic-isotropy argument downgrade

**Pillar**: 1, 4, 5, 6, 8, 10, 11 (all pillars depending on BCC topology) — operational hypothesis explicitly added.
**Transition**: tier labels unchanged; the implicit hypothesis "BCC is selected by mean-field $\Lambda$-maximisation" is replaced by the explicit hypothesis "BCC is retained as a working hypothesis on grounds of TECT-internal consistency until a Mechanism 1–3 result establishes selection".

**Canonical evidence**:
- `Docs/math/TECT-Math349-AddA-User-Audit-Acknowledgment-and-Math350-Reprioritisation.tex.txt`.

**Rationale**: User audit of Math349 correctly identified two over-statements: (i) "Mechanism 4 (topological consistency) selects BCC" was a self-consistency placeholder, not a derivation; (ii) "cosmic isotropy excludes $S_h$" required uncomputed RG flow analysis and is therefore F3-programme motivation, not exclusion theorem. AddA explicitly relabels both.

---

## Format reference (for future entries)

```
### Entry YYYY-MM-DD-NN <direction-arrow> — Pillar X (short pillar name)

**Pillar**: <pillar number and short name>
**Transition**: <old tier> → <new tier> (or split / wording).

**Canonical evidence**:
- `Docs/math/TECT-MathNN-<descriptor>.tex.txt` (one-line description).
- `Docs/math/TECT-MathNN-AddX-<descriptor>.tex.txt` (one-line description).

**R-tag**: `R-YYYY-MM-DD-<descriptor>` (if applicable; only for retractions / refutations).

**Rationale**: One-paragraph plain-English explanation of why the change occurred and what evidence justifies it. Sufficient for a reader to understand the change without consulting the underlying notes.

---
```

## Operational guidance

- **Direction arrow choice**:
  - ⬆ for any tier improvement (T1→T2, T3→T4, T4→T6, etc.).
  - ⬇ for any tier regression that is not a full refutation (T6→T4, etc.).
  - ⬇⬇ for explicit T0 REFUTED (counter-example, numerical falsification, etc.).
  - ↺ for wording / scope / hypothesis-set changes that do not move the tier label.
  - ↪ for regime-dependent splits (one row → multiple sub-rows).

- **Numbering within a date**: `YYYY-MM-DD-NN` where NN starts at 01 for the first entry that day. Multiple entries on the same date are written in chronological order of finalisation.

- **R-tag policy** (CLAUDE.md §15.8): R-tags are required for ⬇⬇ REFUTATION entries; recommended but optional for ⬇ DOWNGRADE; not used for ⬆ UPGRADE or ↺ WORDING.

- **Atomic commit rule** (CLAUDE.md §3): every entry here MUST be committed in the same `git commit` as the underlying Math note(s) and the corresponding `TOE-FACT-SHEET.md` row update.

- **Backward-compatibility** (CLAUDE.md §11): the legacy `CHANGELOG.md` continues to be the omnibus change log; `STATUS-HISTORY.md` is the focused subset for tier changes only. The two are reconciled by the snapshot pipeline ([5] commit step).

## 2026-05-07 (afternoon) — Math351 Phase 0 closure: Sh raw-ansatz non-comparable

### Entry 2026-05-07-04 ↺ WORDING — Pillar 1 deep-regime ground state

**Pillar**: 1 — BCC ground state (deep-regime row).
**Transition**: previously OPEN with M5 priority; refined OPEN with explicit hypothesis "Sh and BCC have different natural box lengths" added as M5b companion task.

**Canonical evidence**:
- `Docs/math/TECT-Math351-Sh-Raw-Ansatz-Lanczos-Phase0-Closure.tex.txt` (3 LOBPCG runs + 4-step (N,L) residual scan; raw ansatz cannot reach BCC residual at any tested combination; eigenvalues ≈ μ² in linear-regime confirms triviality of small-A Hessian).

**R-tag**: `R-2026-05-07-Math351-Sh-Raw-Ansatz-Non-Comparable`.

**Rationale**: Three LOBPCG diagnostic runs (BCC continuation residual 0.01 vs Sh raw ansatz residuals 65 and 0.35) plus 24-variant (N, L, polarisation, A) residual scan establish that no raw Sh ansatz reaches BCC-continuation residual at any tested combination. Smallest achievable raw residual is 0.345 at (N=16, L=18.47, A=0.05), which corresponds to a small-amplitude linear regime where Hessian eigenvalues collapse to bare μ² = -0.7 (no information about saddle/min classification). The Sh family's natural axial period (≈ 15.4) differs from BCC's natural period (≈ 9.24), establishing a substantive physical difference that propagates into the Math110-AddI ℏ formula. Phase 0 closed; M5 (Newton-Krylov continuation of Sh seed) is the only path to quantitative comparison.

---
