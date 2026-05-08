# TECT Status Nomenclature — Standard 8-Tier Schema

**Binding from**: 2026-04-29
**Maintainer**: Jusang Lee (`jtkor@outlook.com`)
**Governed by**: this policy + `CLAUDE.md` §7 (Pillar status semantics).
**Supersedes**: all prior ad-hoc status labels (PARTIAL-ADVANCED, NEAR-CLOSURE, STRONG CLOSURE DRAFT, SCAFFOLD, NOT ADDRESSED, etc.). Existing notes are grandfathered with mandatory mapping per §3 below.

This document is the **single source of truth** for proof-progress labels in TECT. Every Math note, status row, paper draft, website page, and changelog entry MUST use one of the eight canonical tiers defined here. Any other phrase ("essentially proved", "almost closed", "at theorem level", "conjecturally established", "near closure", etc.) is forbidden — it must be replaced by the closest tier in this table.

---

## §1. The eight canonical tiers (T0–T7)

The schema is a hybrid of standard mathematical-physics nomenclature (theorem / lemma / conjecture / open) and standard particle-physics nomenclature (rigorously proved / established / strong evidence / conjectured / open / refuted). The labels are chosen to map cleanly onto referee phrases used in **Physical Review Letters / Reviews of Modern Physics / Annual Review** and onto theorem-environment language in **Annals of Mathematics / Communications in Mathematical Physics**.

| Tier | Canonical label | Definition | Standard physics phrase | Standard math phrase |
|---|---|---|---|---|
| **T7** | **PROVED** | Unconditional mathematical theorem. All hypotheses are textbook-standard (no TECT-specific physical input remaining). | "rigorously proved" / "established unconditionally" | "Theorem" |
| **T6** | **PROVED CONDITIONAL** | Theorem under an explicit, named hypothesis set $H_1, \dots, H_n$. Each $H_i$ is either textbook-standard or pre-registered as a separately tracked open question. | "established conditional on $H$" / "proved modulo $H$" | "Theorem (conditional on $H$)" |
| **T5** | **CLOSED@N-LOOP** | Theorem established at perturbative order $N$ (typically one-loop). Higher-loop closure pending. The order $N$ MUST be stated explicitly. | "established at $N$-loop order" / "proved perturbatively to $\mathcal O(g^{2N})$" | "Theorem (perturbative, order $N$)" |
| **T4** | **STRONG EVIDENCE** | Multi-line independent evidence (analytical + numerical + audit), but no rigorous theorem. The argument structure is correct; what is missing is a self-contained closed-form proof. | "strong evidence supports" / "compelling but non-rigorous" | "Lemma sketch with corroborating analysis" |
| **T3** | **PROOF SKETCH** | Main logic and key steps are written; technical details (regulator, normalisation, edge case) are explicitly marked OPEN. Convertible to T6 by closing the marked gaps. | "we sketch a proof" / "outline of the argument" | "Proof sketch (technical gaps marked)" |
| **T2** | **CONJECTURE** | Explicit hypothesis with partial evidence. No proof attempted or attempted proof failed. Pre-registered falsification gate required (CLAUDE.md §6.3.3). | "we conjecture" / "tentative claim" | "Conjecture" |
| **T1** | **OPEN** | Unaddressed in TECT, or in active research with no partial result yet. | "remains open" / "not yet addressed" | "Open problem" |
| **T0** | **REFUTED** | Explicit counter-example, falsification by audit, or pre-registered falsification gate firing. The claim is **withdrawn** from the canonical record and entered into `Docs/status/NEGATIVE-RESULTS.md` with an `R-` or `F-` tag. | "refuted by" / "falsified" | "Counter-example" / "negative result" |

**Tier ordering**: T7 > T6 > T5 > T4 > T3 > T2 > T1, and T0 is parallel (not on the proof axis but on the rejection axis). A status promotion from T2 to T6 must pass through T3, T4, T5 unless the proof is genuinely a one-shot textbook-style argument that lands directly at T6.

---

## §2. Mandatory side-channels per tier

Each tier carries binding requirements:

| Tier | Required artefacts |
|---|---|
| **T7** | Theorem statement + complete proof in a Math note + §6.3.1 devil's-advocate self-test PASSED + §6.3.4 quantitative sanity check (if numerical claim) + §6.3.5(a) self-adversarial review + reviewer audit pass + atomic-commit (CLAUDE.md §3) |
| **T6** | All of T7 PLUS: explicit hypothesis set $\{H_1, \ldots, H_n\}$ in the theorem statement; each $H_i$ flagged as either "textbook" or "open question with separate tracking entry" in `Docs/status/OPEN-QUESTIONS.md` |
| **T5** | All of T6 PLUS: explicit perturbative order $N$ in the label (`CLOSED@1-LOOP`, `CLOSED@2-LOOP`, etc.); higher-order audit gate pre-registered |
| **T4** | Multi-line evidence summary in the Math note; explicit list of remaining gaps; promotion path to T6 clearly stated |
| **T3** | Marked gap list in the Math note (`OPEN GAP α: ...`, `OPEN GAP β: ...`); each gap with a separately tracked task in OPEN-QUESTIONS.md |
| **T2** | Pre-registered falsification gate in OPEN-QUESTIONS.md (CLAUDE.md §6.3.3 binding) |
| **T1** | Entry in OPEN-QUESTIONS.md with statement, owner, expected closure path |
| **T0** | Entry in NEGATIVE-RESULTS.md with `R-` or `F-` tag; canonical-record retraction; bidirectional link from any prior Math note that asserted the (now refuted) claim |

---

## §3. Mapping from legacy ad-hoc labels

Existing TECT documents use heterogeneous labels. The following mapping is binding for translation:

| Legacy label (forbidden going forward) | Canonical tier |
|---|---|
| `PROVED` (no qualifier) | **T7** |
| `PROVED UNCONDITIONAL` | **T7** |
| `PROVED CONDITIONAL` | **T6** |
| `PROVED with caveat` | **T6** |
| `CLOSED@1-loop` | **T5** (with `N=1`) |
| `CLOSED@1-LOOP` | **T5** |
| `PARTIAL-ADVANCED` | **T4** (if multi-line evidence) or **T3** (if just sketch) |
| `STRONG CLOSURE DRAFT` | **T4** |
| `STRONG DRAFT` | **T3** or **T4** depending on completeness of sketch |
| `PARTIAL ACCEPT` | **T3** (the partial part is accepted, residual gaps remain) |
| `NEAR-CLOSURE` | **T3** or **T4** depending on rigour |
| `STRUCTURAL DRAFT` | **T3** |
| `SCAFFOLD` | **T2** (framework exists; uniqueness/existence absent → conjecture-level) |
| `OUTLINE` | **T2** or **T3** depending on whether main steps are written |
| `CONDITIONAL CONJECTURE` | **T2** |
| `OPEN-NEGATIVE REFINED` | **T0** with explicit no-go cited (the refinement = updated rejection evidence) |
| `OPEN-NEGATIVE` | **T0** |
| `NOT ADDRESSED` | **T1** |
| `AUDIT-FLAGGED` | **T0** if claim withdrawn; **T3** if claim downgraded but salvageable |
| `FAIL AS PROOF` | **T0** if claim withdrawn from canonical record |
| `RETRACTED` | **T0** |
| `FALSIFIED` | **T0** |

When updating an existing note, replace the legacy label with the canonical tier in-place; cite this policy file in the `Status:` line.

---

## §4. Application examples (post-2026-04-29 canonical)

### Pillar 4 sub-task 2 (flat-Cartan ground-state forcing)

**Canonical statement** (using T6):

> **T6 PROVED CONDITIONAL on Lemmas A, B + standard physical-principle inputs (E2, E3).**
>
> Hypotheses: (H1 = Lemma A, microscopic positive curvature stiffness $\kappa_\chi, \kappa_5 > 0$); (H2 = Lemma B, relative no-negative-offset bound $\Delta\Gamma_{\rm rest} \geq -\epsilon\,\mathcal F_{\rm top}$ with $\epsilon < 1$); (H3 = E2 no external topological flux, standard physical setup); (H4 = E3 global energy minimisation, thermodynamic principle).

The mathematical skeleton (Hodge + Yang-Mills + Chern-Weil + composition) is **T7 PROVED** in Math222. The conditional set status:

| Component | Tier | Source |
|---|---|---|
| Math222 skeleton | **T7** | Math222 v1.1 |
| H1 = Lemma A | **T6** (sign-positivity), **T3** for full proportionality | Math221-AddB/C |
| H2 = Lemma B | **T3** | Math220-AddA/B (constant-bound theorem partial) |
| H3 = E2 | **T6** (textbook setup) | Math214 |
| H4 = E3 | **T6** (thermodynamic) | Math214 |

### Pillar 4 sub-task 3 (SO(10) → G$_{\rm SM}$ breaking pattern)

**T6 PROVED CONDITIONAL** on Lemmas A, B + Pillar 6 Higgs mechanism (Math229).

### GAP-2 TECT-specific Berry-phase signature

**T0 REFUTED** by Math226 ($\pi_1(M_{\rm BCC}) = \{e\}$ proof, all loops contractible). Withdrawn from canonical record; `R-2026-04-29-Math226-BerryPhaseFalsified` in NEGATIVE-RESULTS.md. The BRST Faddeev–Popov framework (Math160 §II) survives as **T6**.

### Math218-AddA E$_3'$ cosmological realisation

**T2 CONJECTURE** with Mechanism I or Mechanism II as falsification path.

---

## §5. Stage-1 / Stage-2 / Stage-3 scoreboard re-labelling

The `TOE-FACT-SHEET.md` 11-pillar scoreboard MUST use only T0–T7 labels going forward. The previous label set (PROVED / PROVED CONDITIONAL / CLOSED@1-loop / PARTIAL-ADVANCED / OPEN-NEGATIVE REFINED / NEAR-CLOSURE) is to be migrated in the next §3 atomic-write commit:

**Migration table for current scoreboard (2026-04-29 baseline)**:

| Pillar | Legacy label | Canonical tier |
|---|---|---|
| 1 | PROVED CONDITIONAL | **T6** |
| 2 | PROVED CONDITIONAL | **T6** |
| 3 | CLOSED@1-loop | **T5** (N=1) |
| 4 | PARTIAL-ADVANCED | **T4** (sub-task 1, 2, 3 each have their own tier; aggregate is T4) |
| 5 | PROVED | **T7** |
| 6 | PARTIAL-ADVANCED | **T4** (Math77 unification + Higgs mechanism open) |
| 7 | PROVED | **T7** |
| 8 | PROVED | **T7** |
| 9 | PROVED | **T7** |
| 10 | OPEN-NEGATIVE REFINED | **T0** (classical no-go) + **T2** (phase-transition origin programme) |
| 11 | NEAR-CLOSURE | **T4** |

---

## §6. Website mandatory display

The `Website/status.html` (rendered from `Website/data/status.js`) MUST display:

1. **The 8-tier definition table** (this §1 above) at the top of the page.
2. **Per-pillar status** with explicit T-tier label (no legacy labels).
3. **Per-Lemma status** for active Math222 forcing chain.
4. **Per-GAP status** (GAP-1/2/3/4) for $S_2$ qualification.
5. **A legend block** mapping legacy labels to current tiers (for readers consulting older Math notes).

---

## §7. Failure mode

A Math note, paper draft, or status row that uses a non-canonical label (or any of the legacy labels in §3 without an explicit translation) is **AUDIT-FLAGGED on first review** and CANNOT contribute to a status promotion. Migration of legacy text is a §3 atomic-write item — when an author touches a legacy-labelled section, they MUST re-label to T0–T7 in the same commit.

The reviewer (or self-adversarial review per CLAUDE.md §6.3.5(a)) MUST flag any non-canonical label as an audit defect.

---

## §8. Cross-references

- `CLAUDE.md` §7 — Pillar status semantics (updated to point to this policy)
- `CLAUDE.md` §6.3.1 — devil's-advocate self-test (T7/T6/T5 promotion gate)
- `CLAUDE.md` §6.3.3 — numerical-result gate (T2 falsification pre-registration)
- `CLAUDE.md` §6.3.5 — self-adversarial review + estimate-vs-theorem (T6 vs T4 boundary)
- `Docs/status/TOE-FACT-SHEET.md` — pillar scoreboard (to be re-labelled per §5)
- `Docs/status/NEGATIVE-RESULTS.md` — T0 entries
- `Docs/status/OPEN-QUESTIONS.md` — T1, T2, T3 entries with separate tracking
- `Website/data/status.js` — website mandatory display per §6
- `Docs/policy/UPDATE_POLICY.md` — atomic-write rule for label migration

---

End of STATUS_NOMENCLATURE.md (binding from 2026-04-29).
