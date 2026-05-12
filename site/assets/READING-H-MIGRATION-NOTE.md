# Reading H Migration Note — Historical Archive Notice

**Effective from**: 2026-05-11 (Math401 binding consensus)
**Scope**: every file under `Website/assets/math/` and `Website/assets/policy/`
**Authority**: `Docs/math/TECT-Math401-Operator-Consensus-Reading-H-Adoption-and-Current-State-Summary.tex.txt`

---

## What changed

On **2026-05-11**, the operator-led foundation-first audit cascade
(Math399 → Math400 → Math400-AddA → AddB → AddC → AddD → AddE → AddF → Math401)
reformulated the canonical TECT vacuum interpretation:

| | Pre-2026-05-11 | Post-2026-05-11 (Reading H) |
|---|---|---|
| Canonical vacuum | "BCC condensate is the thermodynamic vacuum" | Brazovskii fluctuation-stabilised disordered phase ($\langle\Psi\rangle = 0$, $\langle\Psi^2\rangle \neq 0$) |
| BCC role | Ground state of the broken-symmetry phase | Cosmologically-relevant **stable fluctuation channel** within the disordered ensemble vacuum |
| Pillar 4 sub-task 2 status | T3 PROOF SKETCH (Math395) | **T6 PROVED CONDITIONAL on Reading H** (Math400-AddE/AddF/Math401) |
| Goldstone interpretation | Exact broken-symmetry Goldstones | Quasi-Goldstones (small-mass shell modes at $|\mathbf q| = q_0$) |
| Lattice-spacing $a_{\rm BCC}$ | BCC crystal lattice constant | Condensation length scale $a_{\rm condensate} = 2\pi/q_0$ (numerical value unchanged) |

The Math82-AddH BCC NUMERICAL data is RETAINED. The Math110-AddG/H/I Newton-$G$ derivation is RETAINED with the lexical update $a_{\rm BCC} \to a_{\rm condensate}$ (numerical value identical). The Brazovskii framework is RETAINED (Math400-AddE Path α confirmed). Only the INTERPRETIVE language changes.

---

## Why archive notes are not edited

Math notes archived on or before **2026-05-10** were written under the pre-Math400 "BCC vacuum" interpretation. They reflect TECT thinking at their respective dates and serve as the audit trail of how the framework arrived at the current state. Editing them would falsify the historical record (CLAUDE.md §17 public-mirror policy + READING-H-MIGRATION-CHECKLIST §2.5).

This banner is the canonical replacement for individual archive-note edits. Readers of any pre-Math399 archive note should cross-reference Math401 (canonical interpretation statement) and READING-H-MIGRATION-CHECKLIST.md (per-surface migration status).

---

## Pre-Math400 archive notes with significant interpretive content

The following Math notes (pre-Math399, archived under pre-Math400 BCC vacuum interpretation) are the most-impactful for Reading H migration. Each carries claims that have been re-interpreted (NOT retracted) under Reading H:

### Vacuum-interpretation foundational
- `Math82-AddH` — "BCC condensation at canonical $\mu^2 = +0.005$" (production simulation): NUMERICAL data retained as BCC-channel realisation; INTERPRETATION as "thermodynamic vacuum" is reformulated as "stable fluctuation channel" per Math401.
- `Math174` — $c_2(E) = -40$ on canonical $\mathbb{CP}^2$ (T7 PROVED unconditional): mathematical statement intact; downstream physical interpretation under Reading H is via gauge-bundle structure on the fluctuation-channel manifold.
- `Math191`, `Math192` — Pillar 4 sub-task 2 "Scenario B" rescue: superseded by Math400-AddE/AddF Reading H reformulation. The Scenario B framing is no longer the canonical pathway; the Reading H pathway is.
- `Math194` — "BCC uniqueness PROVED among 9 crystallographic competitors": superseded by Math400-AddE one-loop Brazovskii self-consistency, which establishes Reading H emergent vacuum independent of crystallographic enumeration.
- `Math195` — A2 axiom-reduction theorem (effective TECT axiom count = 2): UNAFFECTED by Reading H (axiom count is independent of vacuum interpretation).

### Pillar 4 sub-task 2 closure programme (pre-Math400)
- `Math220-AddB` — Lemma B sign theorem: T6 retained under Reading H with explicit conditional.
- `Math221-AddC` — Lemma A regularity: T6 retained under Reading H with explicit conditional.
- `Math218-AddA` — Lemma E$_3'$: pre-Math400 framing as Pillar 4 blocker is REFORMULATED as Pillar 11 Kibble-Zurek defect-density question (Math402 queued).
- `Math265-Math268` — Pillar 4 atomic-tier T3 → T6 promotion via Math229/238/246: superseded by Math400-AddE/AddF + Math401 reformulation.
- `Math354-Math395` — Pillar 4 closure cascade (Lemma A audit, $E_3'$ four-RG audit, Path I/II/III): superseded by Math400-AddE Path α verdict. Notes remain valid as conditional theorems ("IF BCC vacuum THEN ...") but their physical applicability evaporates.

### Lattice / structure-factor (pre-Math400)
- `Math348` — mean-field non-uniqueness ($\Lambda(S_h) = 540$ on prismatic 12-stars): superseded by Math400-AddE Reading H emergent vacuum (no need for crystallographic mean-field selection).
- `Math349`, `Math350` — regime-dependent stability + cascading-impact: deep-regime "saddle" framing reformulated under Math400-AddE (the operating regime is the Brazovskii fluctuation regime; no transition out of it within tested $\mu^2$ window).
- `Math383` — BCC global-min vs FCC/HEX/lamellar competitor comparison: §3-4 arithmetic REFUTED by Math399; §1 formula and §2 K-table partially REFUTED by Math399 + Math400 §3 first-principles re-derivation; §6 numerical retained as fluctuation-channel snapshot.

### Goldstone interpretation (pre-Math400)
- `Math378`, `Math379` — continuum-limit Goldstone scaling at N=16/32/64: numerical data retained; interpretation as exact Goldstones reformulated as quasi-Goldstones under Reading H (Math403 queued for full reinterpretation).
- `Math381-AddA`, `Math381-AddB` — Goldstone eigenvector overlap = 0 + N=128 plateau: data retained; reinterpretation as quasi-Goldstone band structure under Reading H.

### $a_{\rm BCC}$ direct formulae (pre-Math400)
- `Math110-AddB` — $a_{\rm BCC}$-Planck numerical framework: numerical value retained; lexical $a_{\rm BCC} \to a_{\rm condensate}$ under Reading H.
- `Math110-AddG/H/I` — Newton-$G$ derivation $\rho_{\rm cond} = c^4/(16\pi G a_{\rm BCC}^2)$: mathematics retained; lexical update only.

---

## How to read pre-Math400 archive notes under Reading H

When reading any pre-Math399 archive note:

1. **NUMERICAL content**: take at face value (data is data; the simulations were run, the values are correct).
2. **MATHEMATICAL theorems**: take at face value (theorems remain theorems; e.g., Math174's $c_2(E) = -40$ is true regardless of vacuum interpretation).
3. **INTERPRETIVE claims about "BCC vacuum" or "BCC ground state"**: silently substitute "BCC fluctuation channel within Brazovskii fluctuation-stabilised disordered vacuum" per Reading H.
4. **CLAIMS conditional on the BCC vacuum being the thermodynamic ground state**: now re-interpret as conditional on the BCC channel being the cosmologically-selected stable fluctuation channel.
5. **CLAIMS about exact Goldstones**: re-interpret as quasi-Goldstones (small-mass, not zero-mass).
6. **For canonical current interpretation**: defer to Math401, Math400-AddE, Math400-AddF.

---

## Files that are explicitly UPDATED under Reading H (not archives)

The following Tier 1 files have been updated to reflect Reading H. If you find any contradiction between these and an archived note, the Tier 1 file is binding:

- `Codes/config/pillar_status.json` (canonical pillar tier database; 11-pillar Reading H lexical sweep applied 2026-05-11)
- `Docs/status/TOE-FACT-SHEET.md` (Pillar 4 banner under Reading H)
- `Docs/status/EVIDENCE-INDEX.md` (Math400-AddE evidence row)
- `Docs/status/OPEN-QUESTIONS.md` (Math400-AddE-AddA + Math402 active entries)
- `Docs/status/NEGATIVE-RESULTS.md` (R-2026-05-11 retractions)
- `README.md` (snapshot + recent advances + scoreboard under Reading H)
- `Website/data/index.js` (Overview narrative under Reading H)
- `Website/data/theory.js` (Limitations 2 + 4 under Reading H)
- `Website/data/results.js` (Pillar 1 regime-split + scoreboard under Reading H)
- `Docs/wiki-seed/Pillar-1.md`, `Pillar-4.md`, `Pillar-9.md`, etc. (auto-generated from `pillar_status.json`)

---

## Cross-references

- `Docs/math/TECT-Math401-Operator-Consensus-Reading-H-Adoption-and-Current-State-Summary.tex.txt` — binding canonical interpretation statement
- `Docs/policy/READING-H-MIGRATION-CHECKLIST.md` — per-surface cleanup status
- `CHANGELOG.md` (top entries) — Math399-Math401 cascade record
- CLAUDE.md §17 (public-mirror policy), §20 (8-axis co-stabilisation)

---

*This banner is canonical. Do not edit individual pre-Math399 archive notes; reference this banner instead.*
