# TECT Negative Results Ledger

**Binding from**: 2026-04-15
**Maintainer**: Jusang Lee (jtkor@outlook.com)
**Governed by**: `docs/policy/UPDATE_POLICY.md` §9

This ledger preserves the *negative evidence* generated during TECT
research — failed hypotheses, retracted numerical results, and
abandoned approaches. Success is logged in `CHANGELOG.md` and
`docs/status/research-log.md`; this document is the parallel record
of what did **not** work, *why* it did not work, and what superseded
it.

Entries are append-only. Text is never redacted. Items may be
reopened if new evidence arrives, in which case a new entry is added
citing the reopened record — the original stays intact.

Schema: each entry is stamped `[F|R|D]-<YYYY-MM-DD>-<seq>` where
`F` = failed hypothesis, `R` = retracted result, `D` = dead-end
approach.

---

## R — Retracted results

### R-2026-04-30-Math242-c2-misquote-Pillar4-T6-rollback

**Date**: 2026-04-30 — Turn 16 (Math245 formal audit-rollback consolidation).
**Theory tag**: Math245 (`Docs/math/TECT-Math245-AuditRollback-Math242-c2-misquote-Pillar4-revert.tex.txt`)
**Type**: T0 REFUTED (Mechanism A of Pillar 4 sub-task 3 falsified); AUDIT-FLAGGED (Math243 cross-turn audit missed upstream failure).

**What was retracted**:
- **Math242 Theorem 3.1**: "Cubic-Sublattice Forcing of SO(10) → SU(5)×U(1)_χ Breaking". **Status claimed**: T6 PROVED CONDITIONAL. **Mechanisms**: (A) characteristic-class algebra forcing via $c_2(E)=1$; (B) cubic-equivariance O_h enforcement.
- **Pillar 4 sub-task 3**: Promoted from T3 PROOF SKETCH (Turn 13 pre-audit) to **T6 PROVED CONDITIONAL** (Turn 13 Math242 claim, Turn 14 Math243 audit PASS).

**Ground truth (verified by Math245)**:
- Math174 (`Docs/math/TECT-Math174-explicit-c2-second-Chern-number.tex.txt`, committed 2026-04-27) rigorously proves $c_2(E) = -40$ (splitting-principle calculation, §3.3–§4, verified arithmetic). This is NOT $c_2(E)=1$ as Math242 hypothesized.
- **Consequence**: Mechanism A's premise (topological constraint $c_2(E)=1$ achievable on canonical SO(10)→SU(5)×U(1)_χ branching on ℂℙ²) is **FALSE**. Mechanism A is **T0 REFUTED**.
- **Mechanism B alone** (cubic-equivariance) is structurally valid (T3 PROOF SKETCH) but insufficient to establish T6 (requires a valid geometric realisation).

**Root cause**: Math242 was written (Turn 13) **before** Math174 had completed its rigorous index calculation (committed 2026-04-27). Math242 **anticipated** that Math174 would deliver $c_2(E)=1$ as necessary to close Pillar 4 sub-task 2 (16 chiral zero modes). Instead, Math174 found $c_2(E)=-40$, falsifying the assumption.

**Secondary defect (audit-flagged)**: Math243 (Turn 14, commit `140039d`) issued **AUDIT PASS** on Math242 without verifying the cited value "$c_2(E)=1$" against Math174 on disk. This violates CLAUDE.md §6.3.2 (cross-turn audit must spot-check cited facts). **Math243 is AUDIT-FLAGGED** (not retracted; its local logic is sound, but the audit process was incomplete).

**Falsification evidence**:
- **Cause**: Math174 splitting-principle calculation (§3.3): $c_2(E) = (45 + 90 - 150 + 50 - 75)b^2 = -40b^2$.
- **Evidence**: Explicit arithmetic verification and four devil's-advocate objections (α–γ) in Math174 §6, all dismissed/mitigated. Falsification criterion (§7) confirms non-triviality of calculation.
- **Falsification criterion pre-register**: If SO(10) spinor weights / U(1)_χ charges / ℂℚ² integration are textbook-standard (they are, per Slansky tables + Georgi-Glashow), then $c_2(E)=-40$ is unconditional.

**Impact on Pillar 4 status**:
- **Sub-task 1** (SO(10) emergence, Math162): remains **T6 PROVED CONDITIONAL** (unaffected).
- **Sub-task 2** (16 chiral zero modes on canonical geometry): **FALSIFIED** (Math174 proves ind=56≠16).
- **Sub-task 3** (topological forcing): **reverted T6 → T3** (Mechanism A refuted; Mechanism B alone is T3 PROOF SKETCH).
- **Pillar 4 composite**: **T3 PROOF SKETCH** (atomic tier downgrade from T6 PROVED CONDITIONAL, Turn 13).

**Mitigation and recovery pathway** (per Math174 §8.2, Math244 §3, Math245 §8):
1. **Task #156** (NEW, Turn 17): Search alternative 4D Kähler base manifolds (Hirzebruch, K3, del Pezzo) or flat U(1)_χ structures for bundles with $c_2(E)=0$.
2. **Turn 18**: Cross-turn audit with mandatory CLAUDE.md §6.3.2.1 cited-fact spot-check.
3. **Decision gate** (2026-05-14): If no recovery geometry emerges, Pillar 4 demoted to OPEN-NEGATIVE REFINED.

**Operational lesson (CLAUDE.md amendment)**:
- **New binding rule** (CLAUDE.md §6.3.2.1): Every cross-turn audit must include a "Cited-Canonical-Fact Spot-Check" subsection. For each cited numerical result (e.g., $c_2(E)=1$, $\mu=-40$), read the source Math note from disk and verify the value. Discrepancy → AUDIT-FLAGGED (not AUDIT PASS).
- **Pattern identified**: This is the SECOND rollback in current programme (first: Math233 for Pillar 6, 2026-04-26). Both followed the pattern: agent over-claims (T6) → cross-turn audit misses upstream failure → deeper diagnostic catches it → formal rollback. Root cause: absence of mandatory spot-check in cross-turn audit protocol.

**Bidirectional cross-references**:
- Source of $c_2(E)=-40$: Math174 (2026-04-27, T7 PROVED splitting principle).
- Note containing misquote: Math242 (Turn 13, hypothesis H₁ line ~425, "Math174 $c_2(E)=1$").
- Audit that missed it: Math243 (Turn 14, §3.1 cites Math242 without verifying §3 hypothesis H₁).
- Diagnostic that caught it: Math244 (Turn 15, §2.2 identifies misquote, lines 80–87).
- Formal rollback: Math245 (Turn 16, consolidation note).

**Historical context**: The 2026-04-26 Math231→Math233 rollback (Pillar 6) and the current 2026-04-30 Math242→Math245 rollback (Pillar 4) together demonstrate that **cross-turn audits require independent source verification, not just local consistency checks**. CLAUDE.md §6.3.2 has been amended (§6.3.2.1) to enforce this.

**No status changes to other pillars**: Pillar 6 remains T4 STRONG EVIDENCE (independent of Pillar 4 status). All other pillars unchanged. Only Pillar 4 affected (T6 → T3).

---

### VOIDED-2026-04-29-Turn3-Agent-Working-Directory-Hallucination

**Date**: 2026-04-29 — Turn 3 dispatch.
**Type**: Agent operational defect (NOT a TECT theory defect). VOIDED entry.

**What happened**: The Turn 3 cross-turn audit agent (per CLAUDE.md §6.3.2) was dispatched to audit Math230 (committed in Turn 1, SHA `29dca265db`) and Math231 (committed in Turn 2, SHA `8af017acc7`). The agent's `ls Docs/math/TECT-Math23{0,1}*.tex.txt` returned empty, leading the agent to (incorrectly) report the notes as missing and write a false "AUDIT-FLAGGED — file-write-before-claim violation" entry here and a parallel false-flag note at `Docs/math/TECT-Math232-Turn3-Audit-Missing-Math230-Math231.tex.txt`.

**Ground truth (verified by dispatcher post-hoc)**:
- `Docs/math/TECT-Math230-Defect-Sector-One-Loop-Coupling-Verification.tex.txt` — exists (22667 bytes, 531 lines), committed at SHA `29dca265db`.
- `Docs/math/TECT-Math231-Pillar6-Higgs-Effective-Potential-Derivation.tex.txt` — exists (27329 bytes, 679 lines), committed at SHA `8af017acc7`.
- Both T6 PROVED CONDITIONAL claims are backed by canonical Math notes; CHANGELOG / TOE-FACT-SHEET / OPEN-QUESTIONS entries are consistent.

**Cause**: Agent working-directory mis-binding. Likely the agent invoked `ls` from a non-canonical path (its spawn-time cwd) rather than the canonical `C:\Dev\TECT2\Contents` (Linux mount `/sessions/admiring-gallant-goldberg/mnt/Contents`). No §15.2 file-write-before-claim violation occurred — the gate is intact.

**Action taken**: This entry voided (no canonical-status impact). The associated `Math232-Turn3-Audit-Missing-...` note has been replaced with a corrected audit. A post-mortem (`Docs/postmortem/2026-04-29-agent-cwd-hallucination.md`) records the operational lesson.

**No status changes**: Pillar 4 sub-task 2 remains T6 PROVED CONDITIONAL; Pillar 6 remains T6 PROVED CONDITIONAL; Tasks #169 and #170 remain CLOSED.

---

### AUDIT-2026-04-29-Math218-FailAsProof

**Date**: 2026-04-29 — FIFTH audit-rollback in the 2026-04-28 / 2026-04-29 cluster.
**Theory tag**: Math219 (`Docs/math/TECT-Math219-Audit-Rollback-Math216AddB-Math217-Math218.tex.txt`)
**Type**: Audit-correction / FAIL AS PROOF.

**Math218 FAIL AS PROOF — four quantitative defects**:

  Defect A (thermal-rate direction REVERSED): Math218 §3.3 wrote $\Gamma_{\rm ann}(T) = \Gamma_0 e^{-C_{\min}/T}$ and interpreted "cooling drives faster annihilation". Direct check: as $T\to 0$, $e^{-C_{\min}/T}\to 0$, so $\Gamma_{\rm ann}\to 0$ and $\tau_{\rm ann}\to\infty$. Cooling SLOWS thermal hopping, not accelerates. Physics interpretation OPPOSITE of correct.

  Defect B (exp[-10⁻¹⁴] ≈ 1, not ≪ 1): Math218 §4 estimated $p_{\rm defect}\sim e^{-N_e\cdot C_{\min}/T}\sim e^{-10^{-14}}$ and concluded $p_{\rm defect}\sim 10^{-14}$ "negligible". Direct check: $e^{-10^{-14}}\approx 1 - 10^{-14}\approx 1$. The numerical conclusion is REVERSED: defects are abundantly present, not negligible.

  Defect C (units mismatch): Math218 §4 divided $C_{\min}\sim 0.6$ "Brazovskii units" by $T_{\rm trans}\sim 10^{16}$ GeV directly. Brazovskii units are dimensionless or scaled to $a_{\rm BCC}, q_0$, not GeV-comparable. Without scale matching, the ratio is dimensionally meaningless.

  Defect D (Hubble scale wrong by 17 orders): Math218 §4 quoted $H\sim 10^{-3}$ GeV at $T_c\sim 10^{16}$ GeV. Standard Friedmann radiation-era: $H = 1.66\sqrt{g_*}T^2/M_{\rm Pl} \approx 7\times 10^{13}$ GeV at $T_c=10^{16}$ GeV with $g_*=O(100)$, $M_{\rm Pl}=2.4\times 10^{18}$ GeV. Math218's value is wrong by ~17 orders of magnitude.

**Affected status**:
- Math218: PROVED CONDITIONAL (claimed yesterday) → FAIL AS PROOF.
- $E_3'$ (Task #162): REOPENED. Cosmologically realised vacuum = global minimum has NOT been demonstrated.
- Math216-AddB and Math217 also DOWNGRADED (see sister AUDIT- entries below).
- Pillar 4 sub-task 2: composite condition set restored to {$E_{1,\chi 5}^{\rm sign}, E_2, E_2'_{\rm unresolved}, E_3, E_3'_{\rm unresolved}$}; the "all-five-conditional closed" claim of commit `8b82f49f1c` is RETRACTED.

**Tagging rationale (AUDIT- vs R-)**: AUDIT- chosen because the Kibble-Zurek + TDGL approach itself remains a valid research direction; only this specific document execution is FAIL AS PROOF. Math218-AddA repair is queued (Task #162-R, highest priority).

**Methodology lesson (FIFTH audit-rollback in 2-day cluster)**: Math219 §5 proposes §6.3.1 methodological extension — every Math note with numerical claims must include independent numerical sanity checks (Hubble dimensional, exponential-magnitude, distribution-product well-definedness). The §6 self-test in Math218 was insufficiently rigorous — it did NOT catch the four quantitative defects via mere structural objections. Future Math notes must apply quantitative cross-checks.

**Sister rollbacks in cluster** (5 total, 2 days):
- Math208 (2026-04-28 late+5): Math203-207 rollback.
- Math213 (2026-04-28 late+8): Math211 FALSIFIED, Math212 DEMOTED.
- Math215-AddA (2026-04-28 late+11): Math215 §2 Step 5 STRUCTURAL CONJECTURE.
- Math216-AddA (2026-04-29): Math216 factor-of-2 + shell measure + rep matching.
- **Math219 (2026-04-29, this entry)**: Math216-AddB AUDIT-FLAGGED (3 defects), Math217 STRONG DRAFT (3 defects), Math218 FAIL AS PROOF (4 defects).

---

### AUDIT-2026-04-29-Math216-AddB-AuditFlagged

**Date**: 2026-04-29.
**Theory tag**: Math219 §1.
**Type**: Audit-correction / AUDIT-FLAGGED.

**Math216-AddB AUDIT-FLAGGED — three structural defects**:
(A) $\delta(|k|-q_0)^2$ undefined as a Schwartz distribution; smeared shell projector + ε-renormalisation required for legitimate one-loop polarization tensor.
(B) Euclidean integral coefficient error: $\int dk/(2\pi)/(k^2+M^2)^2 = 1/(4M^3)$ NOT $1/(4\pi M^3)$. $\alpha_{\rm match} = 1/(8\pi^4 q_0)$ wrong by factor of $\pi$.
(C) $\zeta_\Psi = \mathbf{16}$ identification CIRCULAR. Math162 zero-mode count is post-selected fermion sector, not BCC fast-mode rep; Math166-A's $b=0$ assumption is logically circular relative to $c_1=0$ forcing.

**What survives**: $E_{1,\chi 5}^{\rm sign}$ (sign-positivity), conditional on $U(1)_\chi \times SU(5)$ acting non-trivially on BCC shell modes.

**What is needed**: non-circular proof that $\mathrm{Tr}_{\Psi_{\rm shell}}(T^a T^b) = \alpha_{\rm rep} \mathrm{Tr}_{\mathbf{16}}(T^a T^b)$ with $\alpha_{\rm rep} > 0$, derived directly from microscopic BCC condensate Brazovskii structure.

---

### AUDIT-2026-04-29-Math217-AuditFlagged-OneLoopStrongDraft

**Date**: 2026-04-29.
**Theory tag**: Math219 §2.
**Type**: Audit-correction / AUDIT-FLAGGED, STRONG DRAFT.

**Math217 AUDIT-FLAGGED — three structural defects**:
(A) Schwinger proper-time positivity gives convergence/regularity of one-loop fermion determinant but NOT the spectral comparison $\Delta\mathcal F_{\rm matter}^{(1)}[c_1,c_2] \geq 0$. A separate spectral-comparison theorem (heat-kernel $a_2$ analysis or Lifshitz-type bound) is required.
(B) Defect-sector strict equality $\mathcal F_{\rm defect}[c_1,c_2] = \mathcal F_{\rm defect}[0,0]$ is too strong; in non-trivial bundles, charged condensate gradient energy is generally $\geq 0$, not equal. Requires gradient-energy comparison theorem.
(C) Two-loop dismissal as $O(\alpha^2)$ suppressed and positive is not rigorous; sign of higher-order effective-action terms is scheme/diagram-class dependent.

**What is needed (Task #161-R)**: $\Delta\Gamma_{\rm eff}[A] \geq -\epsilon \mathcal F_{\rm top}[A]$, $0 \leq \epsilon < 1$, across all $U(1)_\chi \times SU(5)$ topological sectors.

---

### AUDIT-2026-04-28-Math213-Math211-FALSIFIED-Math212-demoted

**Date**: 2026-04-28 (late+8) — THIRD audit-rollback of 2026-04-28.
**Theory tag**: Math213 (`Docs/math/TECT-Math213-Audit-Rollback-Math211-Math212.tex.txt`)
**Type**: Audit-correction / honest-scope event.

**Math211 FALSIFIED**: Two critical errors.

  Error I (real-slice preservation): Math211 §1(B), §2 Step 4 claimed U(1)_χ rotation at θ breaks reality except θ ∈ {0, π}. Direct calculation: for $q_- = q_+^*$, $(q'_+)^* = (e^{2iθ} q_+)^* = e^{-2iθ} q_- = q'_-$ for ALL θ. Real slice preserved by FULL continuous U(1)_χ. Math211 conflated 'preserve real slice' with 'fix individual vectors pointwise or up to sign'.

  Error II (Z_2-reduction vs 2ℤ): Math211 §2 Step 7 claimed Z_2-structure-group reduction implies $c_1 \in 2\mathbb Z$. Correct: on simply-connected CP² (no torsion), Z_2-reduction implies $c_1 = 0$ (flat/torsion bundle), NOT $c_1 \in 2\mathbb Z$. The 2ℤ-classification corresponds to "line bundle has square root", a different condition.

**Math212 DEMOTED**: index-selection valid; forcing claim withdrawn. The mathematical content (ind = 16 + 40b²; ind = 16 ⟹ b = 0 uniquely) is RETAINED. The Pillar 4 sub-task 2 unconditional promotion is WITHDRAWN — Math212 establishes a SELECTION result (consistency with SM-empirical input), not a FORCING result (TECT microscopics ⟹ b = 0). The SM 16-fermion requirement is empirical input; Math212 + this empirical input gives b = 0 conditional. Additionally, c_2(E_{SU(5)}) = 0 forcing is separate and not addressed by Math212.

**Affected status**: Pillar 4 sub-task 2 REVERTS to PROVED CONDITIONAL on canonical realisation (post-R8 baseline). Math191/Math192 c_1=0, c_2=0 remain canonical-realisation choices, not forced by TECT microscopics.

**Methodology lesson** (THIRD audit-rollback today): §6.3 extension proposed — distinguish (m) selection theorem vs forcing theorem, (n) subspace preservation vs pointwise fixity, (o) structure-group reduction (gives flat/torsion bundles) vs Chern-class divisibility (gives 2ℤ classes).

**Tagging rationale (AUDIT- vs R-)**: AUDIT- chosen because Math212's mathematical content (the index formula and integer equation) is RETAINED as a valid consistency-selection theorem; only the unconditional-promotion CLAIM is withdrawn. Math211 partial constructions (10_vec = 5+5̄ decomposition) are RETAINED as canonical-source; only the forcing CONCLUSION is withdrawn. Neither note is fully retracted; both have valid mathematical content within proper scope.


### R-2026-04-28-Math209-Math203-c1-Forcing-Falsified

**Date**: 2026-04-28 (late+2)
**Theory tag**: Math209 (`Docs/math/TECT-Math209-RR1b-bundle-lift-type-Type-B-confirmed.tex.txt`)
**Type**: Retracted theoretical claim (with positive substantive replacement: Type B verdict).

**Claim under test**: Math203's central theorem — σ_I-equivariance of the U(1)_χ bundle on Math162 CP² forces $c_1(U(1)_\chi) = 0$ unconditionally.

**Result**: FALSIFIED by direct computation from Math162's explicit transition function.

Math162 §3.2 gives the explicit transition $g_{01}(u_1, u_2) = \exp(i \arg(u_1) T_3)$. Restricting to the Cartan-T_3 U(1) subbundle gives $h_{01} = e^{i\arg(u_1)}$. Under Math207's σ_I([u]) = [ū], we have $\sigma_I^* h_{01} = e^{-i\arg(u_1)} = h_{01}^{-1} = \bar h_{01}$. This is Type B (Real / anti-linear) equivariance $L \cong \sigma_I^* \bar L$, NOT Type A complex-linear $L \cong \sigma_I^* L$. Under Type B, the equation $c_1(L) = \sigma_I^*(-c_1(L)) = c_1(L)$ is a tautology, NOT a constraint. The Math162 explicit $c_1 = 1$ (per its §4.2) directly demonstrates this: Real-equivariant U(1) bundles can have any integer $c_1$.

**Why Math203 was wrong**: Math203 §2 Step 2 wrote "σ_I^*L ≅ L" as a hypothesis treating "I-equivariant by construction" as complex-linear equivariance. The actual equivariance type from explicit Math162 transitions is Real / anti-linear, which does not constrain $c_1$.

**Affected results**:
  - Math203 (Lemma L2): c_1(U(1)_χ) = 0 from σ_I-equivariance FALSIFIED.
  - Math205 (synthesis L1+L2+L3): FALSIFIED at L2 component.
  - Math207 RR1a portion (base involution antiholomorphism): UNAFFECTED — that result is correct; only the implicit "complex-linear lift" jump was wrong.
  - Math191/192 (c_1=0, c_2=0 claims): REVERT to CHOICE (Scenario B canonical realisation), as reviewer originally maintained.

**Pillar 4 sub-task 2 status**: UNCHANGED at "PROVED CONDITIONAL on canonical realisation" (post-R8 baseline). The Math202-209 cluster identified the forcing question, attempted multiple repair routes, and ultimately confirmed the reviewer's original position: the realisation is a CHOICE, not forced by σ_I-equivariance.

**Reviewer position vindicated**: The 2026-04-28 reviewer audit verdict — "Math191/192 establish c_1=0 and c_2=0 only on the canonical flat-Cartan realisation; the realisation is a CHOICE, not a forcing" — is now confirmed by direct computation from Math162.

**Paths forward** (queued, not executed):
  - M1: Direct BCC microscopic c_1(U(1)_χ) computation (no equivariance argument).
  - M2: Anomaly-cancellation requirement forcing c_1=0.
  - M3: Higher-form symmetry / generalised global symmetries.
  - M4: Acceptance of flat-Cartan as phenomenological choice.

**Methodology lesson**: §6.3 self-tests must explicitly check (a) line-bundle equivariance type (complex-linear vs Real) at the level of EXPLICIT transition functions, not just abstract symmetry arguments. CLAUDE.md §6.3 extension proposed.


### AUDIT-2026-04-28-Math208-Cluster-Rollback

**Date**: 2026-04-28 (late reviewer audit; SECOND audit-rollback of the day)
**Theory tag**: Math208 (`Docs/math/TECT-Math208-Audit-Rollback-Math203-207-cluster.tex.txt`)
**Type**: Audit-correction / honest-scope event (CLAUDE.md §6.1).

**Affected notes** (this commit):
  - Math203 (Lemma L2): PROVED unconditional → AUDIT-FLAGGED.
  - Math204 (Lemma L3): PROVED CONDITIONAL → AUDIT-FLAGGED STRONG DRAFT.
  - Math205 (synthesis): PROVED CONDITIONAL on RR2 → SYNTHESIS DRAFT only.
  - Math207 (RR1 closure): PROVED unconditional → AUDIT-FLAGGED.
  - Math200-AddA y_t portion: AUDIT-FLAGGED (g_1 sign correction RETAINED).
  - Math200-AddB ℏ_A=ℏ_B equality: AUDIT-FLAGGED (proxy-void conclusion RETAINED).

**Critical issues identified by reviewer**:
  I. Math203 / Math207: equivariance-type confusion. The c_1=0 argument requires complex-linear equivariance σ_I*L ≅ L; the natural equivariance for an antiholomorphic involution is the Real structure σ_I* L̄ ≅ L. Concrete counterexample: O(1) → CP² has standard real structure with c_1 = h ≠ 0.
  II. Math204: π_3(SU(5)) → π_3(SO(10)) multiplication coefficient (claimed Dynkin index = 1) unverified for the chiral 16-spinor embedding. Standard "complexification" embeddings give multiplication ×2, yielding π_3(coset) = Z_2 ≠ 0.
  III. Math204: Pontrjagin-Chern sign inconsistent between §1 statement and §3 proof.
  IV. Math200-AddA: y_t β-function "9 y_t²" with PDG initial conditions is likely a calculation error, not a convention difference. Correct (9/2 y_t²) gives no Landau pole below M_Planck.
  V. Math200-AddB: Route B formula ℏ_B = ρ_cond a_BCC³ c_T has dimension [J·m/s], not [J·s] = ℏ. Dimensional repair required.

**Honest verdict**: The Math202-Math207 cluster's "decomposition into bookkeeping items (RR1, RR2)" framing was OVER-OPTIMISTIC. RR1 and RR2 are NOT bookkeeping; they encapsulate genuine mathematical claims that have themselves been audit-flagged. The ESCALATED conditional set is {RR1', RR2', RR3', RR4', RR5'} (Tasks #150-revised, #151-revised, #152, #153, #154).

**Pillar 4 sub-task 2 status**: REVERTS to post-R8 baseline ("PROVED CONDITIONAL on canonical realisation"). The verbal label is unchanged; the supporting evidence cluster (Math202-Math207) is audit-flagged pending resolution of the five RR' questions.

**Methodology lesson**: The §6.3 self-tests of Math203/204/205/207 did NOT systematically check (a) line-bundle equivariance type, (b) homotopy-map multiplication coefficients, or (c) sign normalisations. A CLAUDE.md §6.3 extension is proposed to require these checks for any future line-bundle / homotopy / characteristic-class arguments.

**Tagging rationale (R- vs AUDIT-)**: AUDIT- chosen because:
  - The g_1 sign correction (Math200-AddA part 1) is RETAINED — it IS valid.
  - The proxy-void conclusion (Math200-AddB main) is RETAINED — it IS valid.
  - The Math202 base lemma is RETAINED — it IS valid.
  - Only specific load-bearing claims within the cluster are audit-flagged; not the entire cluster's contribution.

**Open follow-ups**: Tasks #150-revised, #151-revised, #152, #153, #154 (see OPEN-QUESTIONS.md).


### AUDIT-2026-04-28-Math200-Proxy-Defect (downgrade of overreach R-tag from earlier today)

**Date**: 2026-04-28
**Theory tag**: Math200 (R9–R14 autonomous session)
**Type**: Negative numerical result (pre-registered falsification gate fired)
**Location**: `Docs/math/TECT-Math200-GAP1-RGE-scale-coherence.tex.txt` v1.0; supplementary `Codes/supplementary/Math200_RGE_integration.py`

**Claim under test**: The Math149 / Math163 GAP-1 PROVED-CONDITIONAL (weak) verdict — fermion-loop saturation $R_{\rm boson/fermion}\approx 0.12$ at $M_Z$ — survives RGE evolution from $M_Z$ to the GUT scale $M_X \sim 10^{16}$ GeV in the sense that the running $\hbar(\mu)$ defined via $\hbar(\mu) \propto g_1(\mu)^2 g_2(\mu) g_3(\mu)$ (SO(10)-motivated functional form) drifts by less than 10% across the range.

**Pre-registered F-gate** (CLAUDE.md §6.3.3): fail if $|\Delta\hbar/\hbar| \geq 0.10$ at any $\mu \in [M_Z, M_X]$.

**Result**: Numerical RK4 integration of one-loop SM $\beta$-functions yields a 1-loop proxy drift $|\Delta\hbar_{\rm proxy}(10^{12}\,{\rm GeV})| \approx 0.15$ and end-to-end drift $\approx 19\%$ on the assumed proxy $\hbar_{\rm proxy}(\mu)\propto g_1^2 g_2 g_3$. **However**, the 2026-04-28 reviewer audit identifies that this verdict is OVERREACH: (i) the proxy functional form is asserted not derived; (ii) the $g_i(\mu)$ table appears to violate sign expectations from $b_1=41/10>0$ (so $g_1$ should *increase* with $\mu$, but the supplementary code's output table shows decrease — sign / normalisation defect candidate); (iii) the document conflates three distinct matching steps (SM running, GUT matching, TECT $\hbar$ matching). The F-gate therefore fires **on the proxy, not on GAP-1**.

**Honest verdict (post-reviewer audit)**: Math200 establishes that **the chosen 1-loop proxy fails the 10\% band**, not that GAP-1 fails. GAP-1 remains PROVED CONDITIONAL (weak); the RGE scale-coherence question is OPEN, not falsified. Math200 is recorded as an AUDIT-FLAGGED STRONG DRAFT and retained as a warning note, not as a GAP-1 falsification theorem. Status of TOE-FACT-SHEET §S2 GAP-1 row is corrected accordingly (proxy failure annotated, not GAP-1 failure).

**Supersedes / relates to**:
- Math149 (GAP-1 tree-level matching) — UNAFFECTED at $\mu = M_Z$.
- Math163 (boson-loop subdominance ratio) — UNAFFECTED at $\mu = M_Z$.
- Math200 §4 (mitigation discussion) — open.

**Reviewer's prioritised fix list (2026-04-28 audit)**:
  1. Re-derive the analytic 1-loop solution $1/g_i^2(\mu)=1/g_i^2(\mu_0)-(b_i/8\pi^2)\ln(\mu/\mu_0)$ and verify the sign of $g_1(\mu)$ direction in Math200's numerical table.
  2. Confirm the $g_1$ normalisation convention used (SM hypercharge $g'$ vs $\mathrm{SU}(5)$/GUT-normalised $g_1=\sqrt{5/3}\,g'$).
  3. Verify the $y_t$ beta coefficient: SM one-loop convention is $\beta_{y_t}\supset(9/2) y_t^3/(16\pi^2)$, not $9 y_t^3/(16\pi^2)$; document and reconcile.
  4. Derive the matching functional $\hbar_{\rm TECT}(\mu)=\mathcal F_\hbar(g_i(\mu),y_t(\mu),\lambda_H(\mu),a_{\rm BCC}(\mu),G(\mu))$ from TECT first principles before any further drift comparison.
  5. Proxy sensitivity scan: parametrise $\hbar_{\rm proxy}(\mu)\propto g_1^a g_2^b g_3^c y_t^d$ and quantify the falsification verdict's dependence on $(a,b,c,d)$.
  6. Only after items 1–5 discharge, proceed to two-loop RGE + threshold matching (Task #147).

**Open tasks**: Task #147 (two-loop SM RGE), Task #148 ($\hbar_{\rm TECT}$ matching functional derivation; HIGHEST PRIORITY among GAP-1 closure tasks per this audit), Task #149 (proxy sensitivity scan).

### R-2026-04-27-Math181-Scenario-B-Rescue-Unproven — Math181 "three independent paths" do not prove U(1)_χ flatness; Scenario B rescue claim DOWNGRADED to unproven conjecture

**Hypothesis under test**: Math181 claims Task #147 bifurcation is resolved via three independent derivation routes (Paths α, β, γ), each proving that the U(1)_χ holonomy on the Math162 bundle is FLAT (b = c_1(U(1)_χ) = 0), hence Scenario B is correct and μ = 0.

**Result**: DOWNGRADED-NOT-RETRACTED-BUT-UNPROVEN. The Math184 cross-turn audit (CLAUDE.md §6.3.2) identifies critical logical gaps in all three paths that prevent closure:
  - **Path α**: Proves that the BCC order parameter carries zero U(1)_χ charge (⟨T_χ⟩ = 0) but conflates this with zero Berry connection. Zero expectation value ≠ zero connection 1-form. Category error identical to the flaw caught in Math164/165 audit (π₁=0 does not imply trivial Chern classes).
  - **Path β**: Correctly proves 1-cycle holonomy is trivial (using π₁(CP²)=0 and commutativity [T_χ, su(5)]=0). However, trivial 1-cycle holonomy does NOT rule out non-zero first Chern class c_1 ∈ H²(CP²;ℤ). The Chern obstruction lives in the second cohomology, not the first homotopy group.
  - **Path γ**: Argues that uniform U(1)_χ charge across the 24-fold ground-state manifold M_BCC implies zero Berry connection on the moduli space. But (i) uniform charge ≠ zero connection (same error as Path α), and (ii) the moduli M_BCC and the base CP² are different manifolds; the argument does not transfer.

**Cause** (1): Math181 attempts to prove c_1(U(1)_χ) = 0 by computing properties of the BCC order parameter (charge, stabilizer, symmetry), rather than directly computing the connection and curvature on the CP² base. The paths conflate zero eigenvalues / charges / stabilizer properties with zero connection form and curvature — a recurring confusion in bundle theory when quantum-information language is mixed with differential-geometric language.

**Evidence** (2):
  - `Docs/math/TECT-Math181-Pillar4-U1chi-holonomy-from-BCC-microscopics.tex.txt` (all three paths, §§2–4).
  - `Docs/math/TECT-Math184-Round-R5-cross-turn-audit-of-Math181-182-183.tex.txt` (detailed objections α–δ, §§1–4).
  - Math164/165 audit record (canonical precedent for the π₁ vs H² confusion).

**Decision chain** (3): (a) Math181 status DEMOTED from PRIMARY DELIVERABLE / RESCUED (Scenario B proven) to STRONG CLOSURE DRAFT / UNPROVEN (Scenario B still open). (b) Task #147 (Q-2026-04-27-Pillar4-U1chi-topology) is **NOT discharged**; the bifurcation remains genuinely open. (c) Pillar 4 sub-task 2 is DEMOTED from "RESCUED" back to BIFURCATED-CONDITIONAL. (d) New tasks opened: Q-2026-04-27-Math181-Rigorous-C1-Computation (Task #149, explicit c_1 via curvature integral on CP²), Q-2026-04-27-Math162-SU5-Instanton-Status (Task #150, determine c_2(SU(5))), Q-2026-04-27-Alternative-Scenario-B-Proof (Task #151, alternative geometric realisation). (e) **Critical-path impact**: The unique blocker for Pillar 4 sub-task 2 remains unresolved. GAP-2 and GAP-3 remain PROVED CONDITIONAL on Pillar-4 closure, with no clear path to unconditional $S_1 ∧ S_2$ sealing until the U(1)_χ topology is genuinely determined. (f) The backup analyses Math182 and Math183 (referenced in the dispatch brief) were not produced, leaving the rescue narrative incomplete and speculative.

**Successor records**: `Docs/math/TECT-Math184-Round-R5-cross-turn-audit-of-Math181-182-183.tex.txt` (full audit); Tasks #149–151 (follow-ups).

---

### R-2026-04-27-Math162-Bundle-SO10-Spinor-Index — Pillar 4 sub-task 2 falsified: canonical SU(5) branching does not yield 16 chiral zero modes

**Hypothesis under test**: Math162 § (Pillar 4 sub-task 1, foundation) constructs an associated bundle E over CP² with fibre SO(10)/SU(5) and first Chern class c_1=1. Math166 then claims ind(D_E^c)=16 (the SO(10) spinor dimension), and Math171-AddA provides the corrected formula ind(D_E^c) = 16 - μ where μ = ∫_{CP^2} c_2(E). For the target index of 16, we require μ = 0 exactly.

**Result**: FALSIFIED. Math174 (R4-A autonomous computation) rigorously computes μ via the splitting principle using explicit SO(10) spinor weight enumeration and SU(5) branching with standard U(1)_χ charges (+1 for **10**, -3 for **5̄**, +5 for **1**). The calculation yields:
  - c_2(E) = -40 b² (where b = c_1(U(1)_χ) ∈ H²(CP²))
  - μ = ∫_{CP^2} c_2(E) = -40 (with the hyperplane normalisation ∫ b² = 1)
  - ind(D_E^c) = 16 - (-40) = 56 ≠ 16

**Cause** (1): The canonical SU(5) branching of the SO(10) **16** spinor, when realised as an associated bundle on CP² with topologically non-trivial U(1)_χ structure (degree b = H), unavoidably carries a large negative second Chern number due to the charge structure: 10 weights at q=+1 and 5 weights at q=-3 combine (via c_2 = Σ_{i<j} q_i q_j b²) to give -40b². There is no computational error; the issue is structural.

**Evidence** (2): 
  - `Docs/math/TECT-Math174-explicit-c2-second-Chern-number.tex.txt` (full derivation with weight enumeration and splitting-principle calculation, §§ 1–4).
  - `Codes/supplementary/Math174_c2_via_slansky.py` (executable verification: enumerates 16 weights, classifies by U(1)_χ charge, computes Σ c_2 term-by-term).
  - Math171-AddA §3 (confirmed Hirzebruch–Riemann–Roch formula ind(D_E^c) = 16 - μ for canonical complex spin-c on Kähler manifold).

**Decision chain** (3): (a) Pillar 4 sub-task 2 status DEMOTED from PARTIAL-ADVANCED → **REQUIRES REVISION / FALSIFIED**. (b) The geometric realisation (Math162 on CP² with standard SU(5) branching) is incompatible with the target 16 chiral zero modes. (c) Alternatives to be explored: (i) different base manifold (K3, Hirzebruch surface, del Pezzo, etc.) where c_2(E) = 0 might be achievable; (ii) flat U(1)_χ structure (c_1 = 0) instead of topological; (iii) alternative weight assignment or representation (e.g., different maximal subalgebra embedding); (iv) orbifold / stacked geometry. (d) New task Q-2026-04-27-Pillar4-Alternative-Realisation opened. (e) **Cross-coupling with GAP-3**: Math157's anomaly-cancellation result (PROVED) is independent of the geometric realisation; it depends only on group theory of SO(10). Hence Math157 and GAP-3 remain **PROVED CONDITIONAL on existence of a 𝟏𝟔 in some realisation**, not specifically on Math162. The conditional is still binding, but the specific bundle structure is ruled out. (f) Honest scope: if no alternative realisation closes Pillar 4 sub-task 2, then Pillar 4 remains PARTIAL-ADVANCED (foundation OK, matter-embedding falsified), and consequently $S_1 ∧ S_2$ cannot be unconditionally sealed, keeping TECT at **Partial TOE candidate** status.

**Successor records**: `Docs/math/TECT-Math174-explicit-c2-second-Chern-number.tex.txt`; Q-2026-04-27-Pillar4-Alternative-Realisation (new open task).

---

### R-2026-04-26-Math151-InflationaryBranch — Math151 mapping of Brazovskii $\epsilon_s$ to slow-roll $\epsilon$ is a category error; inflationary cosmology branch retracted in favour of Kibble–Zurek

**Hypothesis under test**: Math151 (GAP-4 observables) reports $n_s^{\rm TECT}\approx 0.913$ vs $n_s^{\rm obs}=0.9649\pm 0.0042$ for the cosmological scalar spectral index, treating the BCC phase transition as a slow-roll inflationary epoch with TECT-derived slow-roll parameter $\epsilon=\epsilon_s=2/23$.

**Result**: RETRACTED. Math159 §3 demonstrates that the Brazovskii critical exponent $\epsilon_s=2/23$ (a non-locality / shell-spectral-density quantity) is dimensionally and ontologically incommensurable with the slow-roll parameter $\epsilon=-\dot H/H^2$ (a Hubble-rate logarithmic derivative). Substituting $\epsilon_s$ into the slow-roll formula $n_s=1-6\epsilon+2\eta$ is a category error. Math161 §3 (cross-turn audit) confirms the dimensional analysis and additionally notes that the implied tensor-to-scalar ratio $r\approx 16\epsilon_s\approx 1.4$ is independently falsified by the observational bound $r<0.06$ (Planck/BICEP/Keck 2021).

**Cause** (1): autonomous pre-Math156 work imported a slow-roll formula without checking that the TECT cosmology branch is in the slow-roll regime. The BCC first-order locked branch (axiom A0) is by construction first-order, hence quench-dominated rather than slow-roll.

**Evidence** (2): `Docs/math/TECT-Math159-GAP4-ns-rescue-or-rescope.tex.txt` §3 + `Docs/math/TECT-Math161-Round-W1-cross-turn-audit-of-Math158-159-160.tex.txt` §3.

**Decision chain** (3): (a) Math151's $n_s$ prediction is RETRACTED as a category error. (b) The TECT cosmology branch is rescoped to **Kibble–Zurek quench-driven** (Math146/147 + Math98 phase-transition origin). (c) New observable suite: defect-density spectrum, GW background from defect annihilation, post-condensation matter power spectrum. (d) The previous "FAIL at $\geq 5\sigma$" verdict on $n_s$ is replaced by "$n_s$ is not a TECT observable on the Kibble–Zurek branch." (e) Stage-3 sub-condition $S_3^{\rm (predict)}$ is now gated on Q-2026-04-26-GAP4-Kibble-Zurek-defect-spectrum (Task #135) instead of on $n_s$. (f) Stage-3 still OPEN; the inflationary branch is closed-as-rescoped, not closed-as-passing.

**Successor records**: `Docs/math/TECT-Math159-GAP4-ns-rescue-or-rescope.tex.txt` (rescope), Q-2026-04-26-GAP4-Kibble-Zurek-defect-spectrum (open).

---

### R-2026-04-26-Math160-FPSignError — Math160 supplementary lattice script produced spurious all-negative eigenvalues from a Laplacian sign-convention error; corrected at audit

**Hypothesis under test**: `Codes/supplementary/Math160_fp_det_numerical.py` numerically verifies Math160's claim that the BRST Faddeev–Popov determinant is non-zero and finite on a representative BCC patch.

**Result**: PARTIAL-FAILURE-CORRECTED. The first run of the script reported $\lambda_{\min}=-12.69$, all-negative eigenvalues, and a spurious "FAIL: Degenerate eigenvalue suggests Gribov obstruction" verdict, plus a downstream `TypeError` in the zeta-function regulariser. The Math161 cross-turn audit traced the failure to a sign-convention bug: the helper `lattice_laplacian()` returns the discrete $\Delta$ operator (diagonal $-6/a^2$, eigenvalues in $[-12/a^2,0]$), but the FP operator must be $-\Delta+V_{\rm bg}$, not $\Delta+V_{\rm bg}$. Replacing `M_FP = L + V_bg` with `M_FP = -L + V_bg` (sign-corrected 2026-04-26) restores positivity and yields $\det\mathcal M_{\rm FP}\approx 9.13\times 10^{17}$ on the $N=16$ patch, with $\Gamma_{\rm Berry}=2\pi$ and $\exp[i\Gamma_{\rm Berry}]=1+0i$.

**Cause** (1): autonomous Math160 dispatch produced a numerical script whose internal sign convention did not match its analytic claim. The §6.3.1 self-test in Math160 did not exercise the script, so the failure was caught only at the §6.3.2 cross-turn audit hop.

**Evidence** (2): pre-fix script run output (all-negative eigenvalues + downstream TypeError) and post-fix script run output ($\det\neq 0$, finite). Both reproduced at audit.

**Decision chain** (3): (a) Sign correction applied to `Codes/supplementary/Math160_fp_det_numerical.py` line ~108 (`M_FP = L + V_bg` $\to$ `M_FP = -L + V_bg`) with audit-status comment. (b) Math160 §III gains an audit-recommended caveat noting the sign-correction. (c) Math160 status remains PROVED CONDITIONAL on Pillar-4 SO(10)+$\mathbf{16}$ emergence; no upstream theorem is invalidated. (d) The Berry-phase = $2\pi$ result on the representative patch triggers the new open task Q-2026-04-26-Math160-Berry-phase-non-triviality (Task #134) — existence of the Berry-phase factor is established but non-triviality on physically relevant configurations is not. (e) Lesson recorded: §6.3.1 self-tests must include script execution, not merely text inspection, when supplementary numerics are claimed.

**Successor records**: corrected script `Codes/supplementary/Math160_fp_det_numerical.py` v1.1; Q-2026-04-26-Math160-Berry-phase-non-triviality.

---

### R-2026-04-27-Math173-AuditMissDegreeError — Math173 R3 cross-turn audit ACCEPTED Math171 despite a degree-arithmetic error in §3.3

**Hypothesis under test**: Math173 §2 audit verdict on Math171 (R3-A Pillar 4 sub-task 2 rigorous Atiyah–Singer index re-derivation) was "ACCEPT WITH MINOR REVISIONS". The audit's own Objections α, β, γ were all DISMISSED.

**Result**: PARTIAL-RETRACTED on the Math173 §2 verdict. Direct hand-derivation by the dispatcher on commit-review revealed a degree-arithmetic error in Math171 §3.3 line 177–178: the constant `16` (rank of $E$, a degree-$0$ form on $\mathbb{CP}^2$) was incorrectly combined with $-2H^2$ (a degree-$4$ form) inside the integral, yielding $\int[16 - c_2 - 2H^2] = \int[14H^2 - c_2]$ — but the constant cannot be promoted to a $4$-form for integration. The correct degree-$4$ part of the integrand is $-c_2 - 2H^2$ (without the $16$), and under the canonical complex spin-c structure (the physically admissible choice on the non-spin Kähler manifold $\mathbb{CP}^2$), $\mathrm{ind}(D_E^c) = \chi(E) = 16 - \mu$ (not $14 - \mu$ as Math171 claimed). The audit's Objection β-DISMISSED ("$c_1=0$ correctly simplifies the formula") missed the actual error in the degree arithmetic.

**Cause** (1): the audit was specifically prompted (in the dispatch instructions) to hand-check the $\hat A\wedge\mathrm{ch}(E)$ derivation step-by-step, with the dispatcher providing the explicit hand-computation showing $-c_2 - 2H^2$. The audit agent appears to have treated the prompt's hand-derivation as a sanity check rather than an explicit comparison target, and did not flag the discrepancy with Math171's stated $14H^2 - c_2$.

**Evidence** (2): `Docs/math/TECT-Math171-AddA-degree-arithmetic-correction.tex.txt` (full corrected derivation including spin-c structure analysis); `Docs/math/TECT-Math171-Pillar4-subtask2-rigorous-AS-index.tex.txt` line 177–178 (the buggy lines); `Docs/math/TECT-Math173-Round-R3-cross-turn-audit-of-Math171-157AddD-172.tex.txt` §2 (the audit that missed it).

**Decision chain** (3): (a) Math171 status DEMOTED STRONG CLOSURE DRAFT $\to$ DISPUTED via the AUDIT-FLAGGED banner. (b) Math171-AddA written as the canonical correction record, with the corrected formula $\mathrm{ind}(D_E^c) = 16 - \mu$ and the corrected target $\mu = 0$ (not $-2$). (c) Math173 audit-pass on Math171 is partially retracted via this record; the Math157-AddD and Math172 verdicts of Math173 stand. (d) The R4-A task (compute $c_2(E)$) is updated to use the corrected formula and to test against $\mu = 0$ rather than $\mu = -2$. (e) Lesson recorded: when the dispatcher hand-derives a key formula in the audit prompt, the audit MUST report explicit agreement or disagreement with that hand-derivation, not silently accept the audited file's version.

**Successor records**: `Docs/math/TECT-Math171-AddA-degree-arithmetic-correction.tex.txt`; updated R4-A task brief (Q-2026-04-26-Math166-rigorous-AS-index Task #142 carries the corrected gate).

---

### R-2026-04-26-Math166-IndexByAnsatz — Math166 Atiyah-Singer index value of 16 was asserted by ansatz, not derived from first principles

**Hypothesis under test**: Math166 §2 claims $\mathrm{ind}(D_E)=16$ for the twisted Dirac operator on the Math162 BCC defect bundle ($\mathrm{CP}^2$ base, $\mathrm{SO}(10)/\mathrm{SU}(5)$ fibre, $c_1=1$), with decomposition $\mathbf{16}=\mathbf{10}+\overline{\mathbf{5}}+\mathbf{1}$ matching the Georgi-Glashow branching exactly.

**Result**: PARTIAL-RETRACTED. Math169 §2 audit Objection α is UPHELD: the index value of 16 was identified as the SO(10) spinor dimension target and the Atiyah-Singer formula was inverted to recover that target, rather than evaluated from first principles using $\mathrm{ind}(D_E)=\int_{\mathrm{CP}^2}\hat A(T\mathrm{CP}^2)\wedge\mathrm{ch}(E)$ with the explicit $\hat A(T\mathrm{CP}^2)=1+(1/24)c_2(T\mathrm{CP}^2)$ and the actual rank of the bundle $E$. The bundle-rank assumption is unverified — is the twisted Dirac acting on rank-5 fundamental of SU(5)? rank-21 fibre? rank-24 adjoint? Each gives a different index. Until the rank is fixed and the integral is evaluated forward (not backward), the 16-mode count is not established.

**Cause** (1): autonomous-agent over-claim pattern. Identifying that 16 is the right answer (SO(10) spinor dim, matching Math157 fermion content) led the agent to construct an argument that yielded 16, rather than computing the index honestly and seeing what number emerges.

**Evidence** (2): `Docs/math/TECT-Math169-Round-R2-cross-turn-audit-of-Math166-167-168.tex.txt` §2; the AUDIT-FLAGGED banner now in Math166's header.

**Decision chain** (3): (a) Math166 status DEMOTED PARTIAL-ADVANCED → PARTIAL. (b) Math162 status (Pillar 4 sub-task 1) REMAINS PROVED CONDITIONAL via Math167's three-patch closure — the foundation is intact; only the matter-content sub-task 2 is in question. (c) Open task `Q-2026-04-26-Math166-rigorous-AS-index` (Task #142) records the rigorous re-derivation requirement: compute $\hat A(T\mathrm{CP}^2)\wedge\mathrm{ch}(E)$ explicitly with $c_2(T\mathrm{CP}^2)=3$, $\mathrm{ch}(E)=r+c_1+(c_1^2-2c_2)/2+\ldots$, and verify the degree-4 integral over $\mathrm{CP}^2$. (d) The number 16 is plausible but unproven; the rigorous derivation may confirm it or yield a different number that requires a different bundle / fibre choice.

**Successor records**: `Docs/math/TECT-Math169-Round-R2-cross-turn-audit-of-Math166-167-168.tex.txt`; Q-2026-04-26-Math166-rigorous-AS-index (Task #142).

---

### R-2026-04-26-Math160-BerrySignatureTrivial — Math160 TECT-specific Berry-phase signature is empty on the simply-connected BCC moduli space

**Hypothesis under test**: Math160 §III claims the Berry-phase prefactor $\exp[i\Gamma_{\rm Berry}[\Psi]]$ on the BRST FP determinant is the TECT-specific signature distinguishing TECT from flat-spacetime Yang–Mills. Math161 §4 audit upheld that non-triviality on physically relevant configurations had not been established and required further work.

**Result**: NEGATIVE on the non-triviality leg of the signature claim. Math164 (R1-C autonomous research) proves $\pi_1(M_{\rm BCC})=\{e\}$ for the BCC condensate moduli space $M_{\rm BCC}=(T^{11}\times O_h)/\sim$ — orbifold singular strata are codimension $\geq 2$ and do not contribute non-contractible loops. By Stokes' theorem, $\Gamma_{\rm Berry}=\oint_\gamma\mathcal A=\int_D d\mathcal A=0\pmod{2\pi}$ on every closed loop bounding a disk in the simply-connected base. Numerical verification (`Codes/supplementary/Math164_berry_phase_winding.py`) on three loop families (cyclic permutation, global rotation, relative rotation) returns $\Gamma_{\rm Berry}\approx 0$ to machine precision. Math165 §5 cross-coupling check additionally verifies that the non-zero Chern class $c_1=1$ on the CP² base (Math162) is fully consistent with $\pi_1$-trivial moduli space — cohomology ($H^2$) vs homotopy ($\pi_1$) — and that the two together imply the prefactor $\exp[i\Gamma_{\rm Berry}]$ evaluates to unity on every physically realised loop.

**Cause** (1): Math160 was authored under the unstated assumption that the BCC moduli space supports non-trivial monodromy. The simple-connectedness of $M_{\rm BCC}$ was not checked. Math161 §4 audit flagged the gap; Math164 closed it in the negative.

**Evidence** (2): `Docs/math/TECT-Math164-Berry-phase-non-triviality-construction.tex.txt` (topological proof + numerical verification); `Docs/math/TECT-Math165-Round-R1-cross-turn-audit-of-Math162-163-164.tex.txt` §5 (cross-coupling consistency check).

**Decision chain** (3): (a) Math160 §III TECT-specific signature claim is **DEMOTED from PROVED CONDITIONAL to OUTLINE** (per Math165 §6 recommended revision applied). (b) Math160's formula-level FP-determinant calculation of §II remains PROVED CONDITIONAL on Pillar 4 — the demote affects only the signature interpretation, not the determinant existence/finiteness. (c) Open task `Q-2026-04-26-Math164-Higher-form-Berry-topology` records that a genuine TECT-specific signature would require a higher-form symmetry, a Chern–Simons term, or coupling to the Math80-AddB $\mathrm{Gr}(2,5)$ stratification. (d) GAP-2 status remains PROVED CONDITIONAL on Pillar 4 (the conditional is informative via the formula-level result; the signature-vs-flat-Yang–Mills distinction is now an open question rather than an established theorem).

**Successor records**: `Docs/math/TECT-Math164-Berry-phase-non-triviality-construction.tex.txt`; Q-2026-04-26-Math164-Higher-form-Berry-topology.

---

### R-2026-04-26-Math148-FalsePositive — Math148 chiral-anomaly closure is a false positive; replaced by Math157 rigorous trace method

**Hypothesis under test**: the Math148 (Round V1) component-by-component Fujikawa sum closes GAP 3 (chiral gauge anomaly cancellation) for TECT's emergent SM-like fermion content, with apparent non-zero individual coefficients ($\mathcal A_{YYY}=-2$, $\mathcal A_{YY2}=1/3$, $\mathcal A_{222}=1$) cancelled either by Higgs-scalar contributions or by SO(10) embedding fallback.

**Result**: RETRACTED. (a) Scalars cannot cancel chiral gauge anomalies — Adler–Bardeen theorem fixes the gauge anomaly as a one-loop, fermion-only contribution; Wess–Zumino consistency forbids scalar contributions. (b) The SO(10) trivial-$d^{abc}$ property is a property of the SO(10) gauge anomaly (representation-independent zero), but does not by itself certify any particular low-energy hypercharge assignment in the SU(3)×SU(2)×U(1) basis. The non-zero Math148 numbers therefore reflect a misassigned $Y$-charge or mis-counted chirality, not a physical anomaly that scalars/SO(10) somehow cancel.

**Cause** (3-part traceability, part 1): component-by-component Fujikawa sum was used in place of the standard representation-theoretic trace method. Cancellation patterns in the SM hypercharge assignment require the GUT-normalised $Y_{\rm GUT} = \sqrt{3/5}\,Y_{\rm SM}$ together with the correct Georgi–Glashow embedding of the 16 spinor; mis-stating either invalidates the component sum.

**Evidence** (3-part traceability, part 2): `Docs/math/TECT-Math156-Round-V1-V5-comprehensive-audit-verdict.tex.txt` §3.2 documents the logical error; the Math148 file now carries an AUDIT-FLAGGED retraction banner.

**Decision chain** (3-part traceability, part 3): (a) Math148 superseded by `Docs/math/TECT-Math157-SO10-SM-anomaly-cancellation-rigorous-trace-method.tex.txt`, which computes the six SM anomaly coefficients via representation traces and obtains zero identically (numerically verified by `Codes/supplementary/Math157_anomaly_trace_verification.py` using exact rationals). (b) GAP-3 status revised: was claimed CLOSED in Math148 → demoted to OPEN by Math156 → re-upgraded to PROVED CONDITIONAL on Pillar-4 SO(10)+16 emergence by Math157. (c) Future autonomous rounds: any anomaly claim from a component sum must be re-derived by the trace method before being admitted as evidence (lesson recorded in Math156 §8).

**Successor records**: `Docs/math/TECT-Math157-SO10-SM-anomaly-cancellation-rigorous-trace-method.tex.txt` (rigorous replacement); `Codes/supplementary/Math157_anomaly_trace_verification.py` (numerical verification).

---

### R-2026-04-26-Math149-RouteIndependence — Math149 ℏ-matching two routes are not independent; structural tautology not a cross-check

**Hypothesis under test**: the Math149 (Round V2) two-route derivation $\hbar_{\rm Fock} = \hbar_{\rm gravity}$ provides an independent cross-check that closes GAP 1 (Planck constant matching) at the PROVED level.

**Result**: DEMOTED to PROVED CONDITIONAL (weak). Route A computes $\hbar_{\rm Fock} \sim \rho_{\rm cond}\, c\, a_{\rm BCC}^3$; Route B uses the Planck closure $a_{\rm BCC}^2 = 16\pi G\,\hbar/c^3$ together with the elastic-modulus identification $\rho_{\rm cond} \sim c^4/(16\pi G\, a_{\rm BCC}^2)$ established in Math110-AddG. Substituting Route B's $\rho_{\rm cond}$ into Route A yields $\hbar_{\rm Fock} = c^5 a_{\rm BCC}/(16\pi G)$, which is algebraically identical to Route B's relation modulo a single $a_{\rm BCC}$ inversion. The two routes therefore share a common elastic-modulus input and the agreement is structurally tautological rather than an independent cross-check.

**Cause** (1): the Math149 derivation reused the same $\rho_{\rm cond} \leftrightarrow G$ identification on both sides without flagging it as a shared input.

**Evidence** (2): `Docs/math/TECT-Math156-Round-V1-V5-comprehensive-audit-verdict.tex.txt` §3.1; Math149 file carries a DEMOTION banner.

**Decision chain** (3): GAP-1 demoted from PROVED to PROVED CONDITIONAL (weak); a third matter-side route (e.g. fermion-loop computation, or matrix-element saturation of the canonical commutator at the BCC scale) is required for unconditional closure. Open task: `Q-2026-04-26-GAP1-third-route` in OPEN-QUESTIONS.

---

### R-2026-04-26-Math150-AuditMiss — Math150 V1-V2 cross-turn audit failed to catch the Math148 false positive and Math149 route non-independence

**Hypothesis under test**: Math150 (Round V3 second-order audit per CLAUDE.md §6.3.2) provides an effective cross-turn validation of Math148 (V1) and Math149 (V2), with verdict "ACCEPT" certifying both.

**Result**: RETRACTED. The §6.3.2 audit hop missed both substantive errors (Math148 component-sum mistake; Math149 shared elastic-modulus input). Subsequent V4–V8 rounds expanded on the defective basis, culminating in Math155's overstated "internally rigorous and unobstructed" verdict.

**Cause** (1): the V3 audit examined surface coherence (notation, internal consistency) but did not re-derive the substantive results by an independent method.

**Evidence** (2): `Docs/math/TECT-Math156-Round-V1-V5-comprehensive-audit-verdict.tex.txt` §8 records the second-order failure pattern.

**Decision chain** (3): the §6.3.2 procedure is strengthened: cross-turn audits must re-derive numerical claims by an independent method (e.g. group-theoretic trace where the upstream used component sums) before issuing "ACCEPT". Math150 superseded by Math156.

---

### R-2026-04-26-Math155-Optimistic-Bias — Math155 "internally rigorous and unobstructed" synthesis is over-claim

**Hypothesis under test**: Math155 (Round V8 final synthesis) certifies that TECT's quantum completion is "internally rigorous and unobstructed" with all four GAPs closed.

**Result**: RETRACTED. The honest verdict (Math156 §4) is: GAP 1 PROVED CONDITIONAL (weak), GAP 2 OUTLINE, GAP 3 PROVED CONDITIONAL on Pillar-4 emergence (after Math157), GAP 4 FAIL (current cosmology branch). TECT is a Partial TOE candidate; it is not yet a quantum-consistent theory in the unconditional sense.

**Cause** (1): Math155 inherited the Math148/Math149 over-claims and amplified them through a synthesis verdict that was not independently audited.

**Evidence** (2): `Docs/math/TECT-Math156-Round-V1-V5-comprehensive-audit-verdict.tex.txt` §2 demotion table + §4 replacement verdict.

**Decision chain** (3): synthesis verdicts must not exceed the weakest constituent. Future synthesis notes will state explicitly the lower bound across constituent claims and flag inherited conditionals.

---

### F-2026-04-24-Phase-Z-symmetric-seed-saddle — Phase Z Math55 deep-endpoint re-run: M2 (reversed schedule) confirmed; M1 (BCC symmetric 6-cosine seed) lands at SADDLE not minimum

**Hypothesis under test**: the Math82-Addendum-B Phase Z numerical harness (M1 BCC analytic seed + M2 reversed continuation schedule) achieves convergence at the deep endpoint $\mu^2 = -1.0$ with $\|\nabla \mathcal{M}\|/\sqrt{\dim} < 10^{-8}$ within `--max-newton 12`, providing the missing numerical anchor for Pillar 11.

**Result (Math82-Addendum-D)**: PARTIAL. 3/5 points converge, 2/5 stall. The pre-registered success criteria (Math82-Addendum-B §6) are met for criteria 2 and 5 fully and 1, 3, 4 for 3/5 of points. Specifically:

- Point 1 (μ²=+5e-3, BCC seed): STALL at 12 Newton iter, ||grad||=2.65e-6 (one to two more iterations would have reached 1e-8).
- Point 2 (μ²=-0.02, warm-start): CONVERGED 4 iter, lambda_min = +1.747e-2 (stable).
- Point 3 (μ²=-0.1, warm-start): CONVERGED 0 iter, **lambda_min = -6.253e-2 (SADDLE)**.
- Point 4 (μ²=-0.5, warm-start): CONVERGED 1 iter, **lambda_min = -4.625e-1 (SADDLE)**.
- Point 5 (μ²=-1.0, deep endpoint): STALL with bizarre ρ = -1e30 trust-region pathology (degenerate Newton step on the indefinite Hessian inherited from saddle warm-start).

**Diagnostic decomposition**:

1. **M2 (reversed schedule with warm-start chain)**: SUCCESSFUL. Points 2-4 converge in 0-4 Newton iterations, confirming warm-start delivers Psi to ~1e-8 between mu² steps.

2. **M1 (BCC analytic seed)**: PARTIALLY SUCCESSFUL. Initial residual at Point 1 dropped from ~1.44e+5 (thermal seed, prior run) to ~5.42e+3 (BCC seed, this run) — a **27× improvement**. Inner-Krylov bottleneck resolved: t_CG max = 65 (vs. prior 15000 ceiling). Eisenstat-Walker η_EW does not auto-promote.

3. **Symmetric 6-cosine ansatz lands at SADDLE**: the Phase 2 Lanczos signal at Points 3, 4 reveals lambda_min < 0 — Newton correctly identifies the maximally-O_h-symmetric BCC ansatz as a stationary point, but it is not a local minimum. Theorem (Math82-Addendum-D §2.2): the symmetric 6-cosine zero-relative-phase BCC ansatz is the saddle that connects the 24 BCC ground-state variants. The Hessian has at least 23 unstable directions in the amplitude phase-space, corresponding to the directions that break O_h to a smaller stabiliser.

4. **Point 5 catastrophic failure**: at μ² = -1.0 the indefinite Hessian inherited from the saddle generates a degenerate Newton step (predicted_m = actual_m = 0 in floating point, ρ becomes numerical garbage ~-1e30, trust region halves to nothing without progress).

**Cause** (3-part traceability, part 1): the BCC analytic seed was constructed with maximally O_h-symmetric structure (6 unit wave-vectors with equal amplitude and zero relative phase). This is the natural starting point for an unbiased BCC ansatz, but it sits at the maximally-symmetric center of the 24 BCC ground-state variants' orbit, which is the saddle.

**Evidence** (3-part traceability, part 2): Run output at `Runs/continuation/math55_endpoint_N32_Lbcc7_phaseZ_2026-04-24/`; per-point Phase 2 Lanczos lambda_min values are unambiguous; Point 5 trust-region degeneracy ρ = -1e30 is reproducible.

**Decision chain** (3-part traceability, part 3): (a) M2 (reversed schedule) confirmed working — adopt as standard practice. (b) M1 (BCC symmetric 6-cosine seed) confirmed as initial-residual-reducer but not as ground-state seeker — must be combined with symmetry breaking. (c) New sub-task `Q-2026-04-24-P11-symmetry-broken-seed` (Task #93) opened: construct symmetry-broken BCC seed (4-cosine subset, or random phase shifts, or Lanczos-eigenvector perturbation) for Math82-Addendum-E re-run. (d) Pillar 11 status REMAINS at NEAR-CLOSURE; the symmetric-seed saddle finding is a positive physical result.

**Positive findings (independent of the failure)**:

- Theorem `thm:saddle` (Math82-Addendum-D §2.2): the maximally-symmetric 6-cosine BCC ansatz is a saddle point of the Brazovskii functional. This is a real physical result that constrains the structure of the BCC ground-state manifold.
- The 24 BCC ground-state variants are now an explicit object whose O_h-orbit determines the Hessian instability count.
- M2 (reversed schedule) is production-validated.
- M1 inner-Krylov resolution is production-validated (no more 15000-ceiling saturation).

**Re-promotion criteria for Pillar 11 deep-endpoint anchor**:
- Math82-Addendum-E re-run achieves 5/5 converged with lambda_min > 0 at all interior points (true BCC minimum, not saddle).
- This separately requires Math58-v6 Dirac-sector tightening (Math58-v7 = independent pending work).

**Result tag**: `F-2026-04-24-Phase-Z-symmetric-seed-saddle`. **Math notes**: `TECT-Math82-Addendum-B-Phase-Z-BCC-analytic-seed-runbook.tex.txt` (run plan), `TECT-Math82-Addendum-D-Phase-Z-result-PARTIAL.tex.txt` (this verdict). **Resolves**: nothing (opens follow-up `Q-2026-04-24-P11-symmetry-broken-seed`).

---

### F-2026-04-24-R5-FirstIteration — Pillar 10 R5 residual-matching audit (first iteration) fails pre-registered failure criterion

**Hypothesis under test (R5)**: a single dimensionless completion parameter $\chi_* := \hbar/(m_e c\,a_{\mathrm{BCC}})$ is consistently inferred from four independent residual mismatches between exact classical TECT predictions and observed physics:
$$\bigl\{\,\delta\Lambda,\;\;\delta F_{\mathrm{Casimir}}(d=1\,\mu\mathrm{m}),\;\;\delta\lambda_{\mathrm{Compton}},\;\;\delta a_e\,\bigr\}.$$

**Result (numerical extraction, `Codes/supplementary/Math79_R5_chi_star_extraction.py`)**: Two independent calibration conventions (Compton-anchored with $\chi_*^{(\mathrm{Comp})}=1$; electron-energy-anchored with $E_{\mathrm{BCC}}^{\mathrm{phys}} = m_e c^2$) yield consistent ratio values
$$
\rho_\Lambda \approx 3.4\times 10^{-44}, \quad \rho_{\mathrm{Cas}} \approx -8.7\times 10^{-7}, \quad \rho_{g{-}2} \approx +8.0\times 10^{+7}.
$$
None of these lies in the pre-registered success window $[0.5, 2.0]$, and all three lie outside the conservative failure window $[0.1, 10]$. Math79 §7 Theorem on R5 failure is satisfied at the dimensional-ansatz level.

**Diagnostic interpretation (three failure modes)**:
1. *$\Lambda$ channel ($\rho \approx 10^{-44}$)*: cosmological constant residual is 44 orders smaller than a Compton-anchored universal scale would predict. This quantitatively reproduces the standard cosmological-constant problem (60–120 orders mismatch in QFT vacuum-energy estimates) and indicates that $\Lambda$ residual physics belongs to a different universality class than electron-scale physics.
2. *Casimir channel ($\rho \approx -10^{-7}$ with sign mismatch)*: classical-TECT defect-mediated stiffness is not the dominant boundary-energy mechanism; the sign error reflects the dimensional ansatz's failure to encode the attractive boundary condition.
3. *$g{-}2$ channel ($\rho \approx +10^{+7}$)*: QED loop structure providing the Schwinger $\alpha/(2\pi)$ term is fundamentally larger than a naive classical defect-vertex estimate.

The three failure modes go in three different directions ($\Lambda$ too small, Casimir too small with wrong sign, $g{-}2$ too large), so no rescaling, no choice of $a_{\mathrm{BCC}}^{\mathrm{phys}}$, and no choice of $Y_{\mathrm{SI}}$ can simultaneously bring them to unity.

**Cause** (3-part traceability, part 1): R5 framework was designed to provide a binary verdict on the existence of a single universal completion scale; the dimensional-ansatz first iteration was the simplest possible test. The pre-registered failure outcome is itself a meaningful scientific result, not a procedural error.

**Evidence** (3-part traceability, part 2): `Math79_R5_chi_star_results.json` (first-iteration scan output); `Docs/math/TECT-Math79-Addendum-A-R5-first-iteration-FAILURE.tex.txt` (formal write-up with derivation, calibration tables, and diagnostic interpretation).

**Decision chain** (3-part traceability, part 3): (a) `Q-2026-04-24-P10-R5-residual-matching` resolved-negative in OPEN-QUESTIONS. (b) Pillar 10 status REMAINS at OPEN-NEGATIVE REFINED (no change — the failure reinforces the existing classification). (c) The honest scope statement is preserved: TECT is a UCFT with $\hbar$ external. (d) A refined-$C_i$ second iteration (Math79-Addendum-B) is theoretically possible but de-prioritised given the 44-order gap on $\Lambda$.

**Result tag**: `F-2026-04-24-R5-FirstIteration`. **Math note**: `TECT-Math79-Pillar10-R5-residual-matching-framework.tex.txt` + `Math79-Addendum-A-R5-first-iteration-FAILURE.tex.txt`. **Resolves**: `Q-2026-04-24-P10-R5-residual-matching`.

---

### R-2026-04-24-RoundOverclaim — Three Round 9 (2026-04-24) pillar-closure declarations retracted by reviewer audit

**Retracted claims**:
1. **Pillar 4 = `UNCONDITIONAL PROVED`** (Round 9 final scorecard).
2. **Pillar 6 = `FULL CLOSURE`** (Round 9 final scorecard, on the strength of `Math77-Q6c-Q6d-closure`).
3. **Pillar 11 = `FULLY PROVED (4/4 sectors)`** (Round 9 final scorecard, on the strength of `Math58-v6-Pillar11-Dirac-sector-closure` plus the v2/v3/v4/v5 chain).

**Audit verdicts (2026-04-24)**:

1. *Pillar 4* ⇒ **PARTIAL-ADVANCED**. Q2 (RG-flow derivation) self-classifies as `PARTIAL WITH CONCRETE RG EVIDENCE`; Q3 closes the local moment-map and reduced-dimension-$24$ statements but the identification with the $G_{\mathrm{SM}}$ gauge-field phase space is still conjectural. Full numerical RG integration to the exact $G_{\mathrm{SM}}$ IR fixed point and the $\omega_{\mathrm{red}}$ global Poincaré-form matching are pending. Closure also requires anomaly-matching integration with the matter sector.

2. *Pillar 6* ⇒ **PARTIAL-ADVANCED**. The Math77 base note (`Math77-Pillar6-GUT-embedding`) and the Q6a/Q6b note (`Math77-Q6a-Q6b-closure`) both classify Pillar 6 as PARTIAL-ADVANCED. The Q6c/Q6d note (`Math77-Q6c-Q6d-closure`) declares `Pillar 6 FULL CLOSURE` while simultaneously labelling Q6c and Q6d themselves as PARTIAL-ADVANCED with deferred numerics — internal status-semantics conflict. The 10-defect-moduli count in Q6a is reclassified as conjecture in the same session notes. The argument *"Q6c, Q6d are PARTIAL-ADVANCED, therefore Pillar 6 is fully closed"* is not accepted.

3. *Pillar 11* ⇒ **NEAR-CLOSURE / not yet final archive theorem**. Mainline acceptance: `Math58-v2`, `Math58-v3`, `Math58-v4-sublemma-closure` (supersedes the earlier v4-partial; vortex sector closed unconditionally), and `Math58-v5` (BCC sector $\Delta\Lambda_{\rm BCC}=0$, with wording softened to honestly describe a renormalization-convention vanishing rather than a pure symmetry theorem). Held: `Math58-v6` (Dirac sector) is a STRONG CLOSURE DRAFT for two reasons. (i) **Internal status-sync defect**: the total $\Lambda_{\rm cosmo}$ summation inside v6 still labels the vortex sector as `partial` and writes "*once the vortex-sector sub-lemmas are closed*", although `Math58-v4-sublemma-closure` (in the same upload bundle) already closes those sub-lemmas. (ii) **Renormalization-convention vs symmetry**: the Dirac-sector vanishing rests on the chain "UV zero-point integral is a contact term $\propto V$; absorbed by vacuum renormalization in a periodic box; finite fermionic energy is a chemical-potential shift; the finite part is zero for $\Lambda$ by definition". This is plausible but is a renormalization-convention statement, not a symmetry-driven cancellation theorem of the same evidentiary class as the monopole CP and vortex CP sectors.

**Cause** (3-part traceability, part 1): The 2026-04-24 autonomous Round 9 closed pillar sectors faster than the underlying evidence supported, in part because the round summary (Math78-RESEARCH-SESSION-SUMMARY) was written ahead of the pillar-level theorem notes and then propagated backward into the changelog without an audit step.

**Evidence** (3-part traceability, part 2): The 2026-04-24 reviewer audit identified internal status-sync defects in Math58-v6 (Dirac-sector wording inconsistent with sibling notes), Math77-Q6c-Q6d (declares closure while underlying components remain partial), and Math78 (synthesis table internally classifies Pillar 5 both as FULL CLOSURE and PARTIAL-ADV in different sub-files; Stage-2 meta-consistency uses obsolete pillar mapping).

**Decision chain** (3-part traceability, part 3): (a) The pillar-level theorem notes are preserved unchanged. (b) Explicit `% [AUDIT-STATUS 2026-04-24]` banners are inserted in the over-claiming files (`Math58-v6`, `Math_IR_Bound-v4-PC-3A-L6-closure-attempt`, `Math_IR_Bound-v4-thm-v4-2-H-suppression-closure`, `Math78-Stage2-Meta-Consistency-Round9`, `Math78-TOE-Global-Closure-Synthesis`) and a confirming MAINLINE banner in `Math_IR_Bound-v4-thm-v4-2-final-formalization`. (c) `TOE-FACT-SHEET` Stage-1 scorecard rewritten with the audit-verified statuses. (d) The original Round 9 CHANGELOG entry is preserved per append-only discipline but tagged `[Audit-superseded 2026-04-24]`. (e) A canonical-source hierarchy is fixed: pillar-level theorem note > round summary > global synthesis draft. (f) SRP-v1 (Session Resumption Protocol) is added to `UPDATE_POLICY.md` §14 to prevent future status drift across session boundaries.

**Stage-3 consequence**: The Round 8 advance from `0/3 MISSING` to `1.5/3 PARTIAL-ADVANCED`, which depended in part on `$\pi_2$ FALSIFIED by Pillar 11 closure`, is provisionally rolled back to `≤ 1/3 PARTIAL-ADVANCED`. Task #87 (Math61 amendment) is REOPENED.

**Re-promotion criteria**:
- Pillar 4 ⇒ UNCONDITIONAL PROVED requires: full numerical RG integration showing the $G_{\rm SM}$ IR fixed point + global $\omega_{\rm red}$ Poincaré matching + anomaly-matching integration.
- Pillar 6 ⇒ FULL CLOSURE requires: completion of Q6a (10-moduli enumeration as theorem, not conjecture), Q6b (numerical RGE), Q6c (formal SO(10) uniqueness theorem), Q6d (Yukawa/flavor emergence). This is the recommended Round 10 mainline.
- Pillar 11 ⇒ FULLY PROVED requires: Math58-v6 status-sync repair against `Math58-v4-sublemma-closure`, AND tightening of the Dirac vanishing argument from a renormalization-convention statement to either a symmetry theorem or an explicit-convention closure with the convention stated.

**Result tag**: `R-2026-04-24-RoundOverclaim`. **Audit-rollback CHANGELOG entry**: `[Audit Rollback — 2026-04-24]`.

---

## F — Failed hypotheses

### F-2026-04-21-R5W2 — Single-Schur-functor Pillar-6 strategy falsified through $|\lambda|\le 25$ ($k\le 5$)

**Hypothesis under test**: there exists a single partition $\lambda$ with $|\lambda|=5k$, $\ell(\lambda)\le 5$ for which
$$
M^{\lambda}\;:=\;\dim\mathrm{Hom}_{G_{\rm SM}}\!\bigl(\mathbb{C}_{(\mathbf{1},\mathbf{1})_{0}},\;S^{\lambda}V\bigr)
\;=\;c^{\lambda}_{(k,k,k),(k,k)}\;\ge\;2
$$
(ideally $=3$, which would positively resolve the single-bundle version of Pillar 6 — three generations realised by one $SU(5)$-irrep). The hypothesis was left open at wave-1 (Math49d-R5 v1.0, 2026-04-20) where the exhaustive enumeration for $k\le 3$ ($|\lambda|\le 15$) gave $\sup M^\lambda=1$.

**Result**: wave-2 (Math49d-R5-wave2 v1.0, 2026-04-21) extends the enumeration to $k\in\{4,5\}$, i.e.\ $|\lambda|\in\{20,25\}$. Out of all $192$ partitions of $20$ and $377$ partitions of $25$ with at most $5$ parts, exactly $15$ and $21$ respectively realise $M^{\lambda}=1$; all remaining partitions satisfy $M^{\lambda}=0$. In particular,
$$
\sup_{\lambda\vdash 20,\;\ell\le 5} M^{\lambda}\;=\;\sup_{\lambda\vdash 25,\;\ell\le 5} M^{\lambda}\;=\;1.
$$
Combined with wave-1: $\sup_{|\lambda|\le 25,\;\ell\le 5} M^{\lambda}=1$. The falsification criterion registered in `Q-2026-04-20-PR1` is therefore **met** at search depth $k\le 5$.

**Structural observation** (not part of the falsification, but recorded for future analytic work): the count of $M=1$ partitions at fixed $|\lambda|=5k$ is $\binom{k+2}{2}$ ($=15$ at $k=4$, $=21$ at $k=5$); every realiser satisfies $\lambda_{3}=k$ exactly. A closed-form proof of $M^{\lambda}\le 1$ for all $k$ would permanently close the question beyond the census range.

**Evidence artefacts**:
- `Docs/math/TECT-Math49d-R5-replacement-wave2.tex.txt` (v1.0, md5 `1ee8f075`), Theorem `thm:wave2` and Table I.
- `Docs/supplementary/Math49d_R5_replacement_search_wave2.py` (v1.0, md5 `8541621b`); runtime $0.05\,{\rm s}$.
- `Docs/supplementary/Math49d_R5_wave2_report.json` (md5 `8665629c`) — full census.
- `Docs/supplementary/logs/Math49d_R5_wave2_run.log` — audit log.

**Supersedes** (in the sense of closing the question, not of replacing content): the wave-1 note Math49d-R5 v1.0 which left $k\in\{4,5\}$ open.

**Operative replacement (wave-1, unchanged)**: minimal multi-bundle realisation $E_{\min}=\mathcal{O}\oplus\det V\oplus S^{(2,1,1,1)}V$, total rank $7$; each summand independently carries $M^{\lambda}=1$.

**Pillar 6 impact**: SCAFFOLD at the physical layer is **retained** (not downgraded). The geometric three-count $\chi^{\mathbb{Z}_6}(\mathrm{Gr}(2,5),\mathrm{Sym}^{2}Q)=3$ from Math49d-R3 retains its PROVED status on the arithmetic layer. Next step for physical closure: either (i) prove $M^{\lambda}\le 1$ for all $k$ (closed form), or (ii) compute the twisted Dirac chirality index on $E_{\min}$ under the BCC disclination connection; or (iii) pivot to a partial-flag variety per `Q-2026-04-20-R4`.

**Result tag**: `F-2026-04-21-R5W2`.  **Associated OPEN-QUESTIONS archive entry**: `Q-2026-04-20-PR1` (RESOLVED 2026-04-21 later).

---

### F-2026-04-20-05 — Newton-Krylov projected-Lanczos eigenvalue exhibits a $\times 17$ jump between $N=32$ and $N=64$; clean continuum extrapolation is falsified

**Hypothesis under test**: the sequence $\{m^{*2}_{\text{num}}(N)\}_{N\in\{32,64,128\}}$ obeys the leading-order lattice-spacing expansion
$$
m^{*2}_{\text{num}}(N) \;=\; m^{*2}_{0} \;+\; c\,h(N)^{2} \;+\; \mathcal{O}(h^{4}), \qquad h(N) = 2\pi L/N,
$$
permitting a two-point linear fit in $h^{2}$ to extract $m^{*2}_{0}$ (Phase 4 of the Newton-Krylov proof protocol, Math51–53).

**Result**: `verdict: "falsified at the two-grid level: magnitude jump incompatible with h^2 scaling"`. Numerical values:
- $N=32$, $h_{32}^{2} = (2\pi\cdot 20\pi/32)^{2} \approx 15.42$, $m^{*2}_{32} = 3.1485$.
- $N=64$, $h_{64}^{2} = (2\pi\cdot 20\pi/64)^{2} \approx 3.855$, $m^{*2}_{64} = 54.07$.

The naïve linear fit would predict $c = (m^{*2}_{32} - m^{*2}_{64})/(h_{32}^{2} - h_{64}^{2}) = (3.1485 - 54.07)/(15.42 - 3.855) \approx -4.40$ and $m^{*2}_{0} = 54.07 - c\cdot h_{64}^{2} = 54.07 - (-4.40)(3.855) \approx 71.0$, which is absurd: (i) it contradicts the analytic prediction $m^{*2}_{\text{analytic}} = 9.005$ by nearly an order of magnitude in the wrong direction, (ii) a negative slope $c<0$ combined with the $N=32$ value yields $m^{*2}_{0} > m^{*2}_{64}$, violating any physically sensible "finer grid approaches continuum from below" or "from above" monotonicity prior.

**Root cause — three candidate explanations (ranked by prior plausibility)**

1. **Eigenvector-family migration**. The projected Lanczos at $N=32$ plausibly locks onto the physical longitudinal gap mode; at $N=64$ the finer grid resolves additional UV shell modes whose projected Hessian eigenvalue dominates the first Lanczos eigenvector. **Test**: dump the top-8 Lanczos eigenpairs at both grids and compute the overlap matrix of leading eigenvectors restricted to the common BZ shells. If the $N=32$ leading eigenvector overlaps with the $N=64$ eigenvector rank $\geq 4$, eigenvector-family migration is confirmed.
2. **Merit/projector normalisation latent $N$-dependence**. The projected Hessian carries an implicit $(dx)^{3}$ volume factor through the $L^{2}$ inner product. If the merit function $m = \tfrac{1}{2}\|R_{\mathrm{proj}}\|^{2}$ or the tangent-space projector $P_\perp$ inherits a counting-vs-integrating convention in the shell-mask sum that has not been absorbed, the eigenvalue scales with $N$. **Test**: audit `tect_newton_krylov.py` — in particular the projector construction around the BCC shell mask, and the Lanczos matrix–vector product — for any sum-over-modes that should have been rescaled by $V_{\text{box}}/N_{\text{dof}}$.
3. **Accidental $N=32$ near-degeneracy**. The coarser grid produced an artificial level crossing; $N=64$ is closer to the true continuum. This is the only prior under which the extrapolation is *allowed* to be steep, but requires the eigenvector-overlap test in (1) to come back clean.

**Result tag**: `R-2026-04-20-02-newton-krylov-N64-2026-04-20`. **Run command**: `python tect_newton_krylov.py --config config_template_brazovskii.json --N 64 --L 20pi --phases 123 --tol 1e-6`. **Locked parameters**: $(\mu^{2}, \lambda, \gamma) = (0.26, -0.43, 1.62)$.

**Superseded by**: `Math56-HessJump-audit-2026-04-20` (2026-04-20).  The three candidate explanations above (eigenvector-family migration, projector normalisation, accidental near-degeneracy) were **all refuted by direct measurement** via `PDE/hess_jump_audit.py`. The Phase-2.5 audit (Fourier-band localisation $\rho_{\mathrm{UV}}$, cross-grid zero-pad overlap, Ritz residual) established the true root cause: at both grids the Newton-Krylov solver terminated on the **trivial vacuum** $\Psi^{\ast}\approx 0$ (RMS$|\Psi^{\ast}|/\varphi_{0} = 3.43\times 10^{-6}$ at $N=32$ and $2.64\times 10^{-6}$ at $N=64$, where $\varphi_{0} = \sqrt{-4\lambda/(15\gamma)} = 0.266$), so the reported "$m^{*2}$" values $3.1485$ and $54.07$ are **not** BCC-condensate projected-Hessian eigenvalues — they are artefacts of the Class-II effective term's $\rho^{-1}$ singularity at $\Psi\to 0$ (the guarded quotient $q_{\alpha} = m_{\alpha}/(\rho + 10^{-12})$ becomes ill-conditioned at $\rho\sim 10^{-10}$). See `Docs/math/TECT-Math56-HessJump-audit.tex.txt` §5 for the full empirical dossier; resolution key `MATH55_CONTINUATION_REQUIRED`.

**What remains PASSED despite this F**: (i) Phase 1 existence at $N=64$ is PASS ($\|\nabla\| / \sqrt{\mathrm{dof}} = 1.55\times 10^{-7}$, 10 Newton steps), **but converges to the trivial vacuum**, not to the BCC minimum; (ii) the Newton-Krylov v2.3 solver infrastructure itself is validated at 1.57 M degrees of freedom, with the caveat that it requires a Math55 continuation path to guarantee escape from the $\Psi = 0$ basin; (iii) the mode count $n_{\mathrm{neg}} = 0$ is retained only as a statement about the spectrum *at the point reached*, not as evidence for BCC stability.

**Phase 3 (vacuum favorability) at $N=64$**: the reported $\Delta F = +9.38\times 10^{-10} > 0$ is now understood to be $F[\Psi^{\ast}]-F[0] \approx 0$ with sign set by Class-II and shell-bias cross-terms at the trivial vacuum; it is **not** a thermodynamic comparison against the BCC condensate. This entry remains FAIL and is subsumed by the same root-cause correction above. No new $F$ entry is opened for Phase 3.

**Remediation path**: protocol v2.4 = (G0) Phase-0 vacuum-escape gate RMS$|\Psi^{\ast}|/\varphi_{0} \geq 0.3$; (G1) Fourier-band localisation $\rho_{\mathrm{UV}} < 0.1$; (G2) cross-grid zero-pad overlap $\mathcal{O} \geq 0.8$; (G3) Ritz residual $\eta < 10^{-3}$; **plus** Class-II guarded quotient with $\rho_{\mathrm{cut}} \sim 10^{-3}\varphi_{0}^{2}$. Entry point: Math55 continuation sweep from $\mu^{2}_{0} = -1$ (condensed basin) to the locked value $\mu^{2}=0.26$, producing a genuine BCC $\Psi^{\ast}$ at $N=32$ and $N=64$ for a legitimate Phase-2 comparison.

---

### F-2026-04-16-01 — Q18 commensurability sweep (2026-04-15 vintage) was infrastructurally falsified by a kinetic/seed mismatch, not by physics

**Hypothesis under test**: `Q-2026-04-15-18` — in the Brazovskii-locked
regime with `q0 = 0.6801747616`, the measured radial peak
`q0_meas = argmax_k |Ψ(k)|²` should converge monotonically to `q0`
(equivalently to `k_min = √(-Z/(2Y))`) as the continuum limit is
approached via the three-grid sweep
`(N, L) ∈ {(32, 10π), (64, 20π), (128, 40π)}`.

**Result**: `verdict: "falsified: q0_meas does not track k_min within
one bin at finest grid"` — but for a reason unrelated to physics.

**Root cause — config-kinetic inconsistency**: The config
`PDE/config_template_brazovskii.json` carried `(Z, Y) = (-1.0, 0.5)`,
which gives kinetic minimum `k_min = √(-Z/(2Y)) = 1.000`, while the
same config declared `q0 = 0.6801747616`. The backend
`real_backend_pt_bcc_mixed_v3.py::_brazovskii_linear_term_t` uses
`(r, Z, Y)` literally, and `q0` enters only through `bcc_seed` init
(and `_shell_bias_term_t`, which was disabled with `eta_shell = 0`).
The solver therefore tried to evolve a seed placed at `k = 0.6802`
under a kinetic that pulls toward `k = 1.000`.

**Evidence (three-grid `--skip-solve` post-hoc measurement,
audit_run 2026-04-16)**:

| N   | dk    | q0_meas | q0_meas/dk | q0_meas·L | status         |
|-----|-------|---------|------------|-----------|----------------|
| 32  | 0.200 | 0.5196  | 2.598      | 16.32     | not a shell    |
| 64  | 0.100 | 0.2598  | 2.598      | 16.32     | not a shell    |
| 128 | 0.050 | 0.1299  | 2.598      | 16.32     | not a shell    |

The dimensionless ratio `q0_meas / dk = 3√3/2 = 2.598…` is **identical
across all three grids**, i.e. `q0_meas ∝ 1/L`. The peak is at a
fixed box-relative index, not at a physical wavevector, which falsifies
any interpretation as a Brazovskii shell. The `err_in_bins_of_dk`
metric **worsens** with N (−2.4 → −7.4 → −17.4), confirming divergence
from the kinetic minimum rather than convergence to it.

Solver residual signatures confirm non-convergence:
- N=32: final residual 2.75e-2, energy −16.88 (frustrated transient,
  residual reverses from 2.46e-2 to 2.75e-2 over steps 900→1499);
- N=64: final residual 5.32e-4, energy −7.80e-3 (near-trivial uniform);
- N=128: final residual 1.89e-4 (reverses from 1.50e-4 to 1.89e-4
  over steps 900→1499), energy −1.24e-3 (near-trivial).

**Superseded by**: config fix `[config-kinetic-fix-v2-2026-04-16]` —
full Math38 coefficient closure.

**v1 fix** (same date): set `(Z, Y) = (−0.9252754126, 1.0)` to enforce
`k_min = q0`. However, v1 left `r = mu2 = 0.26`, which gives
`omega(q0) = r − Z²/(4Y) = 0.046` — effective shell mass 5.65× too low.
This would corrupt the condensate amplitude and break locked-triple
self-consistency even though the shell *position* was correct.

**v2 fix** (same date): additionally set `r = mu2 + Y q0^4 = 0.4740336473`.
Now `omega(q0) = mu2 = 0.26` exactly, and the full dispersion
`omega(k) = r + Z k² + Y k⁴` matches `Y(k² − q0²)² + mu2` at every
order. Tag: `config-kinetic-fix-v2-2026-04-16`.

**Propagation**:
- Config patched: `PDE/config_template_brazovskii.json`
  `(r, Z, Y) = (0.4740336473, −0.9252754126, 1.0)`.
- Code-manual entry updated: `docs/manual/CODE_MANUAL.md` §2 now
  carries the full three-coefficient binding relation.
- `UPDATE_POLICY.md` §13 gate: any future config change touching
  `r, Z, Y, q0, mu2` must satisfy `Z = −2Yq0²` **and** `r = mu2 + Yq0⁴`,
  or carry an explicit NEGATIVE-RESULT `R` entry explaining the deviation.
- Q-2026-04-15-18 remains **open** pending re-run against the v2-patched
  config; the 2026-04-15-vintage sweep output is archived at
  `PDE/runs/q18_sweep_2026-04-15/` with this note attached.

---

### F-2026-04-15-01 — Ginzburg–Landau critical-surface regime for TECT

- **Original claim** (pre-Math38): TECT's condensate lives on the
  Ginzburg–Landau critical surface with `(r, λ, γ) ≈ (0.25, +0.35,
  0.05)`, i.e. $\lambda > 0$ and $\gamma$ small.
- **Evidence of failure**: Under this regime the analytic Math37
  prediction and the numerical extractor outputs diverged by a
  factor of roughly $32\times$ that could not be closed by any
  normalisation or patch-layout correction.
- **Root cause**: TECT is the **inverse-superconductor** — the
  topological condensate lies on the Brazovskii first-order locked
  branch ($\lambda < 0$, $\gamma > 0$ sizeable), not on a GL
  critical surface. The GL regime was a sign-and-magnitude error in
  the continuation-schedule fit that set the original locked
  parameters.
- **Superseded by**: `Math38-Brazovskii-2026-04-15`, which
  self-consistently reproduces $(\mu^{2}, \lambda, \gamma) = (0.26,\,
  -0.43,\, 1.62)$ from the three-equation matching $\mathcal{F}(\phi_{0}) = \mathcal{F}(0)$,
  $\mathcal{F}'(\phi_{0}) = 0$, $\mathcal{F}''(\phi_{0}) = \mathcal{M}^{2}_{\mathrm{meas}}$.
- **Archive**: `PDE/backup_GL_2026-04-15/configs/` contains the 32
  GL-regime config files + rollback `README.md`. Do not use in
  production runs.

### F-2026-04-15-02 — Uncorrected first-order lock $\phi_0^{2} = -2\lambda/(3\gamma)$

- **Original claim** (pre-Math37 AddA): $\phi_0^{2} = -2\lambda/(3\gamma)$,
  giving $\phi_0^{2} = 0.17695$ at the locked parameters.
- **Evidence of failure**: The derivation implicitly assumed the
  simple-cubic constellation normalisation ($K_4 = K_6 = 1$). Under
  the correct BCC 12-vector constellation sums $K_4 = 1$, $K_6 = 5/2$,
  the Hessian coefficient on the $\gamma\phi_0^{4}$ term is
  $30 K_6 \gamma = 60\gamma$, not $30\gamma$.
- **Superseded by**: Math37 Addendum A, $\phi_0^{2} = -4\lambda/(15\gamma) \approx 0.07078$.
- **Code locus of correction**: `PDE/tect_actual_extractor_pt_v3.py`
  L619–625, using $\mathrm{denom} = 3 K_6 \gamma$.

### F-2026-04-15-03 — Angular constant $I_3$ left un-fixed between `1/3` and `1`

- **Original state** (pre-Math37 AddA): Math37 §5.5 carried two
  candidate values for $I_3$ — the angular average $1/3$ and the
  constellation average $1$ — without resolution. Numerical code
  used neither explicitly; the effective longitudinal stiffness was
  the bare BCC Laplacian symbol.
- **Evidence of failure**: Ambiguity propagated into $\lambda_\parallel$
  and polluted the $m^{*2}$ closure.
- **Superseded by**: Math37 Addendum A §A.1 proves $I_3 = 1/3$
  *uniquely* from $O_h$ invariance of the BCC constellation. No
  further calibration freedom.
- **Code locus of correction**: `PDE/tect_actual_extractor_pt_v3.py`
  L646 locks `I3 = 1/3`.

### F-2026-04-15-04 — Three-parameter $(u,v,\kappa)$ BCC pair-kernel ansatz

- **Original claim** (pre-Math31): The BCC first-shell pair kernel $K_{ij}$
  can be exhaustively parametrised by the three scalars $(u,v,\kappa)$
  corresponding to $A_{1g}$, $E_{g}$, $T_{2g}$ moments of the 12-vector
  constellation.
- **Evidence of failure**: Math31 Theorem 2.3 — the residual kernel-rank
  deficit $\Delta_{\mathrm{ker}} \approx 32976$ shows that the
  three-parameter ansatz is structurally insufficient; the four-class
  decomposition is mandatory.
- **Superseded by**: Four-class BCC pair-kernel decomposition (Math31),
  which closes the rank deficit and becomes the canonical kernel
  representation entering Math32–Math35.
- **Archive**: Math31 §2–§3 retains the three-parameter calculation as
  pedagogical counter-example.

### F-2026-04-15-05 — $A/E$-symmetric coarse model for the flavor sector

- **Original claim** (Math32, Math33 early drafts): The flavor Gram
  matrix can be captured by an $A/E$-symmetric coarse model (two shell
  parameters, one off-diagonal coupling).
- **Evidence of failure**: The coarse model fails to reproduce the
  $T_{2g}$ mixing block and leaves a residual $O(1)$ mismatch in the
  Gram minors along the locked line.
- **Superseded by**: Full four-class kernel + canonical locked basis
  (Math35), which introduces the $3\times3$ $S_{\min}$ minimum.
- **Archive**: Math32 §4, Math33 §2 retained as working-note trace.

### F-2026-04-15-06 — Scalar Bragg mass $B_{0}$ as a physical mass channel

- **Original claim** (pre-Math12): A scalar Bragg mass $B_{0}$ could
  open at the Dirac node, giving a parity-preserving mass term.
- **Evidence of failure**: Math12 witness theorem — opposite-valley
  pairing plus the valley $\mathbb{Z}_{2}^{V}$ symmetry forbids the
  scalar Bragg channel; only the parity-odd Dirac mass is admissible
  and it is protected.
- **Superseded by**: Witness theorem (Math12 §2–§3); mass protection
  via $U(1)_{V}$ / $\mathbb{Z}_{2}^{V}$.

### F-2026-04-15-07 — Toy positive-sign local potential ansatz

- **Original claim** (Math26 exploratory §1): A local potential
  $V(\phi) = +\tfrac{\lambda}{4}\phi^{4} + \ldots$ with $\lambda>0$
  could host the TECT condensate.
- **Evidence of failure**: Math26 §2 — positive-sign local quartic
  gives only the trivial vacuum; the Brazovskii lock requires
  $\lambda<0$ stabilised by $\gamma\phi^{6}$ at sixth order.
- **Superseded by**: Brazovskii regime lock (Math38, F-2026-04-15-01
  resolution).
- **Lesson preserved**: Local-potential positivity is incompatible
  with topological-condensate existence. Negative quartic + positive
  sextic is the minimal stabilising triple.

---

## R — Retracted numerical results

### R-2026-04-15-01 — Legacy target $m^{*} = 0.3138$

- **Provenance**: Appeared in `PDE/check_and_continue_finetune.bat`
  line 102 as a benchmark comment. Not derived from any Math-note
  or Paper; not computed by any pipeline stage.
- **Status**: Retired as an unverified legacy artefact at the
  Math37 m\*-provenance audit (2026-04-15). No theoretical
  traceability. Must not be cited as a prediction or target in
  any paper, talk, or website page.
- **Current analogue**: The well-traced analytic prediction is
  $m^{*2}_{\mathrm{TECT}} \approx 9.005$ (Math37 AddA at the
  Brazovskii-locked parameters), i.e. $m^{*} \approx 3.00$ — one
  order of magnitude above the retired benchmark.

### R-2026-04-15-02 — v3.0 solver run with seed=17 (silent GL regime)

- **Run context**: User executed `tect_solver_pt_FINAL.py` (pre-rename)
  and `tect_solver_pt_v3.py` v3.0 on seeds 17 / 23 / 41 / 73.
  Seed 17 completed with residual $= 2.88 \times 10^{-5}$, energy
  $= -2.65 \times 10^{-5}$; seeds 23/41/73 failed with
  `FileNotFoundError`.
- **Evidence of failure**: Residual and energy magnitudes are
  consistent with GL pre-convergence, not Brazovskii locked-branch
  convergence. Diagnostic: the v3.0 rename was cosmetic only —
  `make_default_config` retained hard-wired $\lambda = +0.35$,
  $\gamma = 0.05$, $r = 0.25$, and there was no `--config` CLI
  flag to inject the Brazovskii triple.
- **Verdict**: Every v3.0 run executed on a file named for the
  Brazovskii regime was in fact a GL run. All v3.0 result tags
  of form `R-<date>-<seq>-Math38-Brazovskii-...` that predate
  Patch A are retracted.
- **Superseded by**: Solver Patch A (`tect_solver_pt_v3.py` v3.1):
  hard-wired Brazovskii defaults at L207/209, `--config` JSON
  overlay at L642/677–681, regime banner echo at L747–753.
- **Status**: Re-run pending on user machine once stale
  `__pycache__/*FINAL*.pyc` is purged.

---

## D — Dead-end approaches and blockers

### D-2026-04-21-001 — Task #54 Math55 continuation blocked: PyTorch environment unavailable

**Attempted action**: Execute `continuation_mu2_fast.py` v1.1 Newton-Krylov continuation from $\mu^2=0.26$ to $\mu^2_{\rm target}=5\times 10^{-3}$ on grid $N=32$, followed by (if successful) $N=64$ run.

**Blocker**: Missing PyTorch dependency. The computational backend `real_backend_pt_bcc_mixed_v3.py` (line 23) imports `torch`. Installation via `pip install torch --break-system-packages --no-cache-dir` failed with OOM (Exit code 143, process killed mid-install).

**Environment**: /sessions/intelligent-funny-cerf/mnt/Contents, filesystem 238GB (200GB used, 38GB avail); pip cache cleared; Python 3.10.

**Root cause analysis**:
1. PyTorch wheel build/download is memory-intensive (~2GB in typical CI).
2. Current session environment may have per-process or per-user memory limits.
3. Pre-built wheels for this platform/Python combination may be unavailable or require compilation.

**Impact**:
- **Task #54**: BLOCKED (no numerical result; cannot execute continuation).
- **Task #55 X6**: BLOCKED (depends on Task #54 Phase-2 spectral eigenvalues for $\sigma_V(N)$ scaling).
- **Pillar 1 closure**: BLOCKED (requires Math55 Phase-2 projected-Lanczos data).
- **Math61 prediction P3 measurement**: BLOCKED (pending Task #54 continuum limit for $Z_h$).

**Workarounds attempted**:
1. `pip install torch --no-cache-dir`: OOM → killed.
2. Checked for pre-installed PyTorch: not found.
3. Examined if pure-NumPy backend is available: `real_backend_pt_bcc_mixed_v3.py` is torch-only (no fallback).

**Recommended remediation**:
1. Retry continuation in a session with larger memory allocation or a dedicated GPU node.
2. Consider implementing a lightweight NumPy-only backend (would require `real_backend_pt_bcc_mixed_v3.py` rewrite, ~days of work).
3. Pre-compile PyTorch wheels in a build session and cache locally.

**Not a theoretical blocker**: The continuation mathematics (Math55, Math56, Math56-Addendum) is sound. The failure is purely environmental. Once PyTorch is available, continuation will execute without code changes.

**Evidence artefacts**:
- Session attempt log: `/sessions/intelligent-funny-cerf/mnt/Contents/runs/R-2026-04-21-001-newton-krylov-v2p4-FAILURE.md` (manifest).
- Attempted config: `/sessions/intelligent-funny-cerf/mnt/Contents/PDE/config_mu2_target_5e3.json`.
- Attempted command line: (recorded in FAILURE manifest).

---

## D — Dead-end approaches (archived)

### D-2026-04-15-01 — Continuation-schedule fit as first-principles parameter derivation

- **Approach**: The original `(μ², λ, γ) = (0.26, -0.43, 1.62)`
  triple cited throughout Math01–36 was obtained from a
  continuation-schedule fit, i.e. a numerical annealing that
  stabilised a working point, then read the parameters off the
  endpoint.
- **Why abandoned**: The fit produced correct numerics by accident
  — there was no derivation from RG flow, 1-loop matching, or any
  first-principles scheme. The identity of the *regime* itself
  (Brazovskii vs GL) was ambiguous in the original notes, which is
  what allowed F-2026-04-15-01 to persist.
- **Superseded by**: Math38 path-α (theory-first) derivation: the
  three-equation matching system reproduces the same triple
  self-consistently from the Brazovskii effective potential at the
  measured curvature $\mathcal{M}^{2}_{\mathrm{meas}}$, with $K_6 = 5/2$.
- **Lesson preserved**: Numerical coincidence is not theoretical
  derivation. Future parameter locks must provide a matching
  condition *and* the regime classification *before* being accepted.

### D-2026-04-15-02 — `paired_basis_extractor_v2.py` with `m_parallel = None` default

- **Approach**: `m_parallel` was declared as an optional kwarg
  defaulting to `None` and propagated unchanged through all
  callers. `bcc_compare/grid64_bcc/` scans never passed it, so every
  paired-basis summary reported `null`.
- **Why abandoned**: Silent null-propagation hid the absence of a
  live computation. D5 stayed open for weeks because the numerical
  output *looked* present but was structurally empty.
- **Superseded by**: `PDE/live_m_parallel.py` (v1.0, 2026-04-15),
  wired into `run_pipeline_n1.py` as Stage U2c. Computes per-patch
  / per-antipodal-pair / shell-mean $m_\parallel$ directly from
  `transport_extractor` outputs; emits `live_m_parallel_summary.json`.
- **Original file** is retained under `PDE/deprecated/paired_basis_extractor_v2.py`
  for audit only — no live imports.
- **Lesson preserved**: Optional kwargs that stand in for
  computations are a structural anti-pattern. Every physics
  observable must be either computed live or raise — never default
  to `None`.

### D-2026-04-15-03 — 8-patch axis-aligned extractor layout as the canonical convention

- **Approach**: The first-generation extractor hard-wired 8 patches
  (2 polar + 6 equatorial) with $N_\alpha = 1$, giving $W_0 = 8$,
  $W_2 = -1$, $\varepsilon_\mathrm{lock} = -3/8$.
- **Why abandoned**: The BCC first-shell constellation has $|S_\mathrm{BCC}| = 12$
  star vectors. The 8-patch layout drops 4 of the 12 vectors, so
  the patch-moment normalisation is inconsistent with any
  constellation-symmetric average. This contributed a factor of
  $12/8 = 1.5$ in $m^{*}$ (≈ $2.25\times$ in $m^{*2}$) to the
  pre-Math38 mismatch.
- **Superseded by**: Math37 AddA introduces projection factor
  $R_\mathrm{patch} = 45/16 \approx 2.81$ that post-hoc corrects
  legacy 8-patch outputs. New work must use the 12-constellation
  layout at source; `R_\mathrm{patch}` is a compatibility shim,
  not the target of future extractors.
- **Lesson preserved**: The patch layout is a **physics choice**,
  not a discretisation convenience. Drop-in axis-aligned grids
  violate constellation symmetry.

### D-2026-04-15-04 — Naive small-$p$ perturbation without norm-uniform bounds

- **Approach** (Math24 §1 exploratory): Expand Hessian eigenvalues
  in small momentum $p$ without tracking norm-uniform bounds on the
  remainder.
- **Why abandoned**: The bare small-$p$ expansion does not control
  $Z_{\mathrm{pol}}^{(T)}$ loop weight corrections; Math24 §3 shows
  the leading bound is not norm-uniform.
- **Superseded by**: Norm-uniform estimate programme (Math24 §4 onward);
  $Z_{\mathrm{pol}}^{(T)}$ itself tracked as Q-2026-04-15-11.
- **Lesson preserved**: Perturbative expansion in a compact
  parameter must be accompanied by a uniform-in-$p$ remainder bound
  before being admitted as an analytic identity.

### D-2026-04-15-05 — Two-shell-parameter linear map for flavor Gram

- **Approach** (Math32 §3 exploratory): Reduce the flavor Gram matrix
  computation to a two-shell-parameter linear map, assuming the
  $T_{2g}$ block is captured by a single off-diagonal entry.
- **Why abandoned**: Math33 shows the two-parameter map is
  rank-deficient on the locked line — it fails to produce positive
  $\det G$ at interior points, matching F-2026-04-15-05.
- **Superseded by**: Full four-class kernel + $S_{\min}$ canonical
  basis (Math35).
- **Lesson preserved**: Dimensional reductions of the Gram matrix
  before establishing full-rank at a single reference point produce
  false closures.

### D-2026-04-15-06 — Pauli Route A (non-gauge-covariant $SU(2)$ embedding)

- **Approach** (pre-Pauli Supp): Embed the Pauli channel directly
  at the fibre level without gauge-covariantising the transverse
  phonon derivatives.
- **Why abandoned**: Route A breaks $SU(2)$-covariance under
  rotations of the phonon frame; the resulting connection is not
  the Levi-Civita of the emergent metric and fails the Nijenhuis
  integrability test (Nija_Tensor supp).
- **Superseded by**: Pauli Supplementary Route B — gauge-covariant
  $SU(2)$ emergence on the transverse-phonon bundle with
  Levi-Civita connection on $TS^{2}$.
- **Lesson preserved**: Gauge structures emergent on a curved
  internal space must be constructed covariantly on the bundle, not
  at a single reference fibre.

### D-2026-04-20-02 — Naive direct-sum three-generation ansatz $E_L(a,b) = S\otimes(\det Q)^a \oplus Q\otimes(\det S)^b$ on $\text{Gr}(2,5)$ rigorously FALSIFIED ($\chi = 3$ not realised for any integer $(a,b)$) — first falsification-grade computation in the TECT ledger

- **Hypothesis under test**: The three-generation count of the Standard Model arises from the Hirzebruch–Riemann–Roch index $\chi(\text{Gr}(2,5), E_L) = 3$, where $E_L$ is the direct-sum bundle $S \otimes (\det Q)^a \oplus Q \otimes (\det S)^b$ with $S$ the tautological rank-2 subbundle, $Q$ the rank-3 quotient bundle, and $(a,b)\in\mathbb{Z}^2$ tunable twist parameters. This ansatz was the original Math49 target (both scaffold and first rigorous rewrite) for Pillar 6 (three-generation fermion count).
- **Why the question was asked**: The branching rule $\mathbf{5} = (\mathbf{3},\mathbf{1})_{-1/3} \oplus (\mathbf{1},\mathbf{2})_{1/2}$ under $G_{\text{SM}} \subset SU(5)$ suggests that the fundamental SM representation assembles naturally from tautological-plus-quotient bundles on $\text{Gr}(2,5)$. The direct-sum $E_L(a,b)$ was the most economical such construction.
- **Result — FALSIFIED-ANSATZ**: `Math49-rigorous-v2` computes $\chi(E_L(a,b))$ exactly via Bott equivariant localisation in sympy rational arithmetic for all $(a,b) \in [-8, 8]^2 \cap \mathbb{Z}^2$. Corollary 1 establishes direct-sum additivity $\chi(E_L(a,b)) = \chi_S(a) + \chi_Q(b)$, which extends the scan to all integers via the two univariate sequences $\chi_S(a), \chi_Q(b)$. Theorem 2:
$$\chi(E_L(a,b)) = 3 \quad \text{has no solution for } (a,b) \in \mathbb{Z}^2.$$
Explicit ranges on $[-8,8]$:
$$\{\chi_S(a)\}_{a=-8}^{8} \cap [0, 10^4] = \{0, 5, 40, 175, 560, 1470, 3360, 6930\},$$
$$\{\chi_Q(b)\}_{b=-8}^{8} \cap [0, 10^4] = \{0, 5, 10, 45, 75, 210, 315, 700, 1890, 4410, 9240\}.$$
The minimum positive value in either image is 5, so no non-negative combination equals 3. (Negative values on the image sets are accommodated by Serre duality but likewise never sum to 3.)

**Evidence (rigorous)**:
- **Sanity suite (Prop. 1 of Math49-v2)**. Five Weyl-dimension-formula validations against the SL(5) Borel–Weil–Bott theorem:

  | $d$ | $\chi(\mathcal{O}(d)) = s_{d,d}(1^5)$ | Bott-localisation (sympy) | Match |
  |-----|----------------------------------------|---------------------------|-------|
  | $-1$ | 0 | 0 | ✓ |
  | 0 | 1 | 1 | ✓ |
  | 1 | 10 | 10 | ✓ |
  | 2 | 50 | 50 | ✓ |
  | 3 | 175 | 175 | ✓ |

  This confirms that the sympy kernel (with symbolic $t_i = 1 + z_i \varepsilon$ pole-cancellation expansion; $z = (1,2,3,5,7)$) computes $\chi$ correctly.

- **Main scan (Theorem 1 of Math49-v2)**. $\chi(E_L(a,b))$ tabulated on $[-3,3]^2$; no cell contains the value 3. Extended scan via additivity on $[-8,8]^2$: no solution.

**Root cause — a combinatorial / arithmetic obstruction**: The direct-sum structure factorises the global Euler characteristic into two independent SL(5) Weyl-dimension sequences, neither of which contains 3 in its image. Specifically,
$$\chi_S(a) = (\text{dim of an irrep of } SL(5) \text{ of highest weight determined by } a), \quad \chi_Q(b) = \text{idem}.$$
The smallest positive SL(5) irreducible-representation dimensions accessible through these twists are 5, 10, 40, 45, 175, … The integer 3 is never an SL(5) irrep dimension. Hence no direct-sum realisation of the ansatz can yield $\chi = 3$.

**Superseded by**: Three refinement paths, tracked as `Q-2026-04-20-R1`, `Q-2026-04-20-R3`, `Q-2026-04-20-R4` in `OPEN-QUESTIONS.md`:
- **R1**: replace direct sum with an irreducible Schur-functor image $\mathbb{S}^\lambda(S\oplus Q)$; the resulting $\chi$ is no longer a sum of SL(5) dimensions and may include 3.
- **R3** (HIGHEST PRIORITY): compute the $\mathbb{Z}_6$-equivariant Lefschetz index; the three-generation count would emerge as the count of $\mathbb{Z}_6$-fixed points on $\text{Gr}(2,5)$, mirroring Heterotic orbifold constructions.
- **R4**: replace $\text{Gr}(2,5)$ with the partial flag $\mathrm{Fl}(2,3;5)$ (fallback if R3 fails).

- **R2 RULED OUT**: discrete quotient of $\text{Gr}(2,5)$ cannot deliver three copies because $\pi_1(\text{Gr}(2,5)) = 1$; no non-trivial cover exists.

**Lesson preserved**: The fact that a target integer (three, in this case) is inaccessible through a direct-sum construction is itself useful information — it concentrates refinement effort on genuinely inhomogeneous bundles (Schur-functor, equivariant, partial-flag) rather than infinite parameter tuning. The additivity observation $\chi(E_L(a,b)) = \chi_S(a) + \chi_Q(b)$ reduces an infinite $(a,b)$-scan to two univariate scans, making the falsification rigorous and exhaustive. Falsification of a *structural* ansatz — not merely of a numerical value — is the cleanest form of negative result a topological approach can generate.

**Discipline significance**: This is the first *rigorous falsification* in the TECT ledger. The preceding `F-` and `D-` entries record failed numerical fits or abandoned approaches; Math49-v2 records the exhaustive refutation of a mathematically well-posed conjecture using exact arithmetic. The TECT update policy (`docs/policy/UPDATE_POLICY.md` §11, §13) is hereby strengthened: **Pillar closures will henceforth require computed, not asserted, index/character/dimension values**. Any future Math-note asserting a topological count must either (i) enumerate the relevant cohomology/index symbolically or (ii) provide a fixed-point localisation calculation analogous to `Math49_hrr_v3.py`.

**Addendum 2026-04-20 (independent-channel corroboration)** — The $\mathbb{Z}_6$-equivariant Lefschetz scan of the same direct-sum bundle family,
$$\chi^{\mathbb{Z}_6}(E_L(a,b)) \;\text{ on }\; (a,b) \in [-3,3]^2 \;\subset\; \mathbb{Z}^2,$$
computed by the independent multiprecision kernel `Math49d_equivariant_bott.py` (dps=200, eps=1e-50, 10-point $T$-localisation on three $\zeta$-fixed components), yields the image set
$$\mathrm{image}\,\chi^{\mathbb{Z}_6}(E_L(\cdot,\cdot))\big|_{[-3,3]^2} = \{0, 8, 42, 50, 62, 104, 203, 211, 265\}.$$
No entry equals $3$. The $\mathbb{Z}_6$-refined direct-sum ansatz is therefore falsified on a completely disjoint logical channel (equivariant trace vs.\ ordinary HRR integral), with all six character traces $\chi_{\zeta^k}$ computed separately and summed as $\tfrac{1}{6}\sum_k \chi_{\zeta^k}$. This second-channel falsification **strengthens** D-2026-04-20-02 to a double-root ruling: the failure of the direct-sum ansatz is not an artefact of the ordinary index but a genuine structural obstruction.

**Successor (positive)**: The structural three-ness emerges from an *irreducible* bundle under the same $\mathbb{Z}_6$ refinement, not from a direct sum. `Math49d-R3-rigorous-v2` (2026-04-20) proves $\chi^{\mathbb{Z}_6}(\mathrm{Sym}^2 Q) = 3$, with the three coming from the dimension of $\mathrm{Sym}^2 V_\beta$ = the $\mathbb{Z}_6$-invariant isotype inside the $\mathbf{15}$ of SU(5). See Q-2026-04-20-R3 archive entry.

**Artefacts preserved**:
- `docs/math/TECT-Math49-rigorous-v2.tex.txt` — full PRL-style derivation with sanity suite + main theorem + additivity corollary + falsification corollary + refinement enumeration.
- `docs/supplementary/Math49_hrr_v3.py` — sympy Bott-localisation kernel (exact Rational arithmetic).
- `docs/supplementary/Math49_hrr_v3_output.txt` — execution log with all sanity checks and the $[-3,3]^2$ / $[-8,8]$ scan outputs.

---

### D-2026-04-20-01 — Five Math notes (Math49, Math49b, Math49c, Math_EP, Math_IR_Bound) initially labelled PROVED/CLOSED/ANALYTICALLY BOUNDED without sufficient rigour

- **Approach (2026-04-20)**: A same-day autonomous closure sprint
  produced five PRL-formatted Math notes targeting Pillars 2, 6, 7,
  8, 9 of the TOE fact-sheet. These were logged in `CHANGELOG.md`,
  `research-log.md`, `TOE-FACT-SHEET.md`, `EVIDENCE-INDEX.md` and
  `OPEN-QUESTIONS.md` as theorem-level closures.
- **Why flagged**: A strict devil's-advocate review performed on the
  same day identified technical defects in four of the five notes:

  1. **Math49** — real dimension of $\text{Gr}(2,5)$ stated as 6 rather
     than the correct $\dim_\mathbb{R} = 12$ (complex-dim 6); Â-genus
     conflated with Euler characteristic in Eq.(20); instanton number
     $k = 1$ asserted without derivation; the final
     arithmetic step "$2 + 1 = 3$" conflated bundle rank with the
     topological index.
  2. **Math49b** — Eq.(19) U(1)_Y³ sum included only $Q_L$ and $L_L$,
     omitting $u_R, d_R, e_R$ and the Weyl multiplicities
     $(6,3,3,2,1)$; the correct per-generation sum
     $6(1/6)^3 + 3(-2/3)^3 + 3(1/3)^3 + 2(-1/2)^3 + 1(1)^3 = 0$
     was not written out. SU(2)³ vanishing reason inverted — should
     invoke $d^{abc} = 0$ in $\mathfrak{su}(2)$, not "including $e_R$".
  3. **Math49c** — structurally close to complete, but missing the
     lemma identifying the BCC disclination charge with the generator
     of $\pi_1(\text{SO}(3)/G_{\text{pt}})$; point group $O_h$ vs.\ $O$
     not clearly distinguished.
  4. **Math_EP** — proof is tautological: all three stress tensors
     $T^W$, $T^{\text{def}}$, $T^{\text{grav}}$ are defined as
     $(2/\sqrt{-g})\,\delta S/\delta g^{\mu\nu}$ of the same action,
     so their coincidence is a definitional identity, not a physical
     WEP statement. Eq.(24) contains a "this gives a sign flip"
     mid-proof comment indicating the derivation was not finalised.
     A genuine WEP proof requires dynamical definitions of $m_I$ and
     $m_G$ and a theorem identifying them.
  5. **Math_IR_Bound** — Eq.(3) chose a quadrupole spin-2 operator
     $(\partial_i \partial_j \Psi)^2 - \tfrac{1}{3}(\nabla^2\Psi)^2$
     rather than the cubic-$O_h$ invariant
     $\sum_i (\partial_i \Psi)^4 - \tfrac{1}{3}(\sum_i(\partial_i\Psi)^2)^2$.
     The canonical dimension was misstated; the one-loop anomalous
     dimension $\eta = +0.02$ was asserted without a diagrammatic
     calculation; the SME bound $c_{\mu\nu} \lesssim 10^{-70}$ was
     quoted from literature rather than derived from a BCC
     Brillouin-zone integral.

- **Discipline corollary**: The `UPDATE_POLICY.md` memory rule
  "never label prototype work as rigorous / proof-grade" was violated
  by the initial closure labelling. Same-day downgrade restored
  discipline: `TOE-FACT-SHEET.md` summary scorecard now reads
  "1 PROVED, 1 CLOSED@1-loop, 2 PARTIAL, 4 SCAFFOLD, 1 OPEN, 2 NOT
  ADDRESSED", and the five reopened items sit in `OPEN-QUESTIONS.md`
  as Q-2026-04-20-ZZ-A through Q-2026-04-20-ZZ-E.
- **Superseded by**: Forthcoming rigorous rewrites
  `TECT-Math49-rigorous.tex.txt`, `TECT-Math49b-rigorous.tex.txt`,
  `TECT-Math49c-rigorous.tex.txt`, `TECT-Math_EP-rigorous.tex.txt`,
  `TECT-Math_IR_Bound-rigorous.tex.txt`, each to be subjected to a
  second devil's-advocate pass before any closure label is
  reinstated.
- **Lesson preserved**: Producing a PRL-formatted LaTeX note whose
  statement matches a closure target is not evidence of closure.
  An independent pass — ideally an adversarial one — must check
  dimensions, arithmetic, operator choice, and the
  definition-vs.-derivation distinction before any pillar label is
  promoted from SCAFFOLD.

---

## Governance

- **Append-only**. No entry is ever edited in place. Corrections,
  if needed, are added as a new entry referencing the original.
- **Cross-referenced**. Every `F` / `R` / `D` entry cites the
  superseding theory tag, code version, or replacement entry. A
  dangling entry with no successor is itself a flag that the
  project owes a theoretical or numerical response.
- **Mirrored at milestones**. When a new theory tag is minted, the
  associated `CHANGELOG.md` section includes a `### Retracted /
  dead-end` subsection listing any `F` / `R` / `D` entries
  attributed to that tag, linking here.
- **Canonical**. This file is the single source of truth for
  failure provenance. Public-facing failure narratives on the
  Website (when published) must link back here.

---

### F-2026-04-20-03 — Math49d-R3-rigorous-v2 physical identification FALSIFIED: the unique $\mathbb{Z}_6$-invariant piece of $\mathrm{Sym}^2 V_5$ is a Georgi–Machacek-like electroweak Higgs triplet $(1,3)_{+1}$, not three chiral fermion families

**Hypothesis under test (Math49d-R3-rigorous-v2, 2026-04-20)**: that the
three-dimensional $\mathbb{Z}_6$-invariant sub-representation
$\mathrm{Sym}^2 V_\beta \subset \mathrm{Sym}^2 V_5$ — arising as the
unique isotype with $\zeta$-character $+1$ — furnishes the three chiral
families of the Standard Model, realising Pillar 6 at the
geometric-count level.

**External critique (GPT peer review, 2026-04-20)**: $V_\beta$ is
identified as the electroweak doublet slot in the GUT decomposition
$V_5 = V_\alpha \oplus V_\beta$ with $V_\alpha = (3,1)_{-1/3}$ and
$V_\beta = (1,2)_{+1/2}$. Therefore $\mathrm{Sym}^2 V_\beta$ transforms
as $\mathrm{Sym}^2 (\text{doublet of }SU(2)_W)$, which is the
**triplet** $(1,3)_{+1}$. Identifying flavour families with a
gauge-triplet multiplet forces the three families to carry distinct
$SU(2)_W$ quantum numbers, violating the Standard-Model axiom that
flavour rotations commute with the gauge group.

**Independent confirmation (TECT internal audit,
`Docs/supplementary/Math49d_gauge_flavor_audit.py`, 2026-04-20)**:
$$
\mathrm{Sym}^2 V_5 = (6,1)_{-2/3} \;\oplus\; (3,2)_{+1/6} \;\oplus\; (1,3)_{+1},
$$
with $\mathbb{Z}_6$-characters
$(\omega^{2},\, -\omega,\, 1)$ under
$\zeta = \mathrm{diag}(\omega,\omega,\omega,-1,-1)$, $\omega = e^{2\pi i/3}$.
Only the last isotype is $\mathbb{Z}_6$-invariant, and it is
$(1,3)_{+1}$ — identical in quantum numbers to the
Georgi–Machacek Higgs triplet $\chi$. This is not a family index.

**Verdict**: the **geometric** count $\chi^{\mathbb{Z}_6}(\mathrm{Gr}(2,5),
\mathrm{Sym}^2 Q) = 3$ survives as a valid cohomological assertion, but
its **physical** interpretation as the three SM generations is
categorically falsified. The number "3" is the internal dimension of a
single weak-triplet scalar multiplet, not a generation count.

**Consequences**:
1. Math49d-R3-rigorous-v2 is downgraded from *R3 geometric three-count
   closure of Pillar 6* to *R3 geometric candidate, physical
   identification RETRACTED*. The title must be rewritten.
2. TOE-FACT-SHEET Pillar 6 returns to `SCAFFOLD` status. Any public
   banner reading "three generations proved" must be withdrawn.
3. The search for the fermionic generation count requires a
   **different bundle** — one whose $\mathbb{Z}_6$-invariant isotype
   supplies an $SU(2)_W$-singlet flavour index (e.g., a spinor bundle
   realising Dirac zero modes on the BCC disclination network with the
   Atiyah–Singer index restricted to a family-diagonal sub-lattice),
   not the symmetric square of the tautological quotient.
4. The $\mathbb{Z}_6$-invariant $(1,3)_{+1}$ multiplet is itself
   physically interesting: it has the quantum numbers of a Georgi–
   Machacek Higgs triplet and would, if realised in the TECT IR
   spectrum, predict a doubly-charged scalar at the BCC gap scale.
   This is logged as a new open direction
   (`Q-2026-04-20-Q-GM-TRIPLET`), not a SM family count.
5. The planned Math49e Yukawa extractor is suspended until a
   physically-correct bundle is identified.

**Supersession / replacement**: `Math49d-R3-rigorous-v3` (pending),
which must (i) identify a bundle whose $\mathbb{Z}_6$-invariant isotype
is $SU(2)_W$-singlet, (ii) supply a Borel–Weil–Bott cohomology
concentration lemma (currently absent from v2, per GPT item "problem
2"), (iii) replace high-precision `mpmath` recognition by exact
symbolic arithmetic in $\mathbb{Z}[\omega]$ (GPT item "problem 1"), and
(iv) fix the broken `eqref{eq:zeta_def}` cross-reference in the v2
manuscript (GPT item "problem 4").

**Status**: Falsified (physical identification) / partially retained
(cohomological count) as of 2026-04-20. Ledgers updated; website
downgrade in progress.

---

### F-2026-04-20-04 — Math_IR_Bound-rigorous-v2 directional-dimension averaging $\langle[\partial_i]\rangle = (2\mu + \mu^2)/3$ is a soft hand-wave, not a rigorous RG bound

**Hypothesis under test**: the Brazovskii-locked effective action for
the emergent Lorentz sector admits a uniform bound
$\Delta_{\mathrm{op}} \geq d_{\mathrm{eff}}=4$ under scale composition
by averaging the transverse and longitudinal scaling dimensions of the
cubic operator $O_h$.

**Critique (GPT peer review, 2026-04-20)**: tensor-operator scaling
dimensions are not averages. Proper RG analysis must decompose $O_h$
into irreducible $O_h$-cubic sectors (perpendicular, parallel, mixed),
compute the dimension of each separately, and take the **minimum**
(most IR-relevant), not the mean, to bound relevance. The
averaging identity $\langle[\partial_i]\rangle = (2\mu + \mu^2)/3$ is
not a theorem.

**Verdict**: Lemma 2 of Math_IR_Bound-rigorous-v2 is demoted to a
heuristic estimate. The claim "$\Delta \geq 4$" is not yet proved under
the stated derivation.

**Replacement**: `Math_IR_Bound-rigorous-v3` (Task #34, #39), which
must perform the full $O_h$-cubic decomposition and also supply the
quantitative 1-loop anomalous dimension $\eta^{(c)}$ that v2 deferred.

---

### R-2026-04-20-01 — Math49c-rigorous-v2 spin-statistics argument retracted as circular (v3 replacement already in tree)

**Hypothesis under test**: Theorem 2 of Math49c-rigorous-v2 derives
fermion statistics of BCC disclinations by invoking the fact that
"the Dirac zero mode has spin $1/2$, so under $2\pi$ rotation it
acquires a sign, hence by Finkelstein–Rubinstein the configuration is
fermionic".

**Critique (GPT peer review, 2026-04-20)**: assuming the zero mode is
"spin-$1/2$" is assuming the conclusion. TOE-grade derivation must
start from the bosonic TECT order parameter $\Psi$ and derive the
$2\pi$ sign from its topology alone.

**Verdict**: the v2 theorem as written is tautological and is
retracted.

**Replacement**: `TECT-Math49c-rigorous-v3.tex.txt` (already in tree,
2026-04-20), which routes the derivation through the first-shell BCC
pair bundle $\mathcal{O} \to \Pi$ and a mod-2 spectral-flow index,
avoiding any fermionic input. The v3 manuscript carries its own DA log
`N_DA1…N_DA4`. One open numerical item (O1) remains: a PDE-lattice
mod-2 spectral-flow cross-check, scheduled as `Math49c-v3-sim`.
