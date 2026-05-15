# TECT Status History

**Binding from**: 2026-05-15
**Maintainer**: Jusang Lee (`jtkor@outlook.com`)
**Schema**: `tect-status-history-v1`

This is the canonical chronological record of every Pillar tier change in the TECT 11-pillar scoreboard, with reasons and supporting Math notes. Each entry corresponds to an explicit promotion, demotion, split, or rollback documented in `Codes/config/pillar_status.json` or `Docs/status/TOE-FACT-SHEET.md`.

The current tier scoreboard lives in `Codes/config/pillar_status.json` (machine-readable) and `Website/data/status.js` (display); this STATUS-HISTORY shows how the scoreboard reached its current state, so readers can audit the promotion/demotion history.

**Schema per entry**:
- **Date** (UTC): when the tier change was registered.
- **Pillar**: 1-11, plus split-axes (e.g., 11.A / 11.B).
- **Old tier → new tier**: explicit transition.
- **Reason**: short textual rationale.
- **Source Math note(s)**: archive references.
- **CHANGELOG ref**: matching CHANGELOG.md entry tag for full context.

---

## §1. 2026-05-15 cascade entries (today)

### 2026-05-15 — Pillar 11 SPLIT into 11.A (dominant DM) + 11.B (subdominant relic)
- **Pillar**: 11
- **Old tier**: T6 (Math402 era, pre-Math404 anchor)
- **New tier**: `T4|T2-split` (later `T4|T1-split` after Math409-AddD-AddC, see below)
- **Reason**: Math407-AddA Round-2 operator audit binding decision 1: single tier T6 was over-crediting Pillar 11 by absorbing Path III strength into a verdict about the historical dominant-DM hypothesis. Split into parallel claims:
  - **11.A** (dominant-DM claim, T2 initially): TECT KZ defects saturate Ω_DM via inflationary dilution. Conditional on G1, G2, G4.
  - **11.B** (subdominant-relic pathway, T4): TECT defects contribute f_def ∈ [10⁻⁵⁰, 10⁻³⁰]; bulk DM from ν_R via Math408 LRSM cascade.
- **Source Math notes**: Math407-AddA, Math409, Math409-AddA
- **CHANGELOG**: `Theory/Audit] Math407-AddA — Operator Round-2 adversarial audit ... 2026-05-15`

### 2026-05-15 — Pillar 11.A T2 → T1 OPEN downgrade (wall-DM REFUTED)
- **Pillar**: 11.A
- **Old tier**: T2 CONJECTURE
- **New tier**: T1 OPEN (effectively REFUTED)
- **Reason**: Math409-AddD-AddC quantitative evaluation of TECT-natural wall-DM bias mechanisms. Friedland-Murayama-Perelstein 2003 wall-DM CMB constraint exceeded by canonical factor 10^59.9. Three bias mechanisms (a) cubic-symmetry-breaking (T1, severe fine-tuning ε ~ 10⁻⁹³), (b) inflation dilution (T0, not a bias), (c) sector coupling (T2, requires g ~ 10⁻¹³·⁵). None reaches T3.
- **Source Math notes**: Math409-AddD-AddC, Math409-AddD
- **CHANGELOG**: `[Theory/Negative-Result] Math409-AddD-AddC — TECT-natural wall-DM bias mechanism: wall-DM REFUTED at factor 10^60 ... 2026-05-15`
- **OPEN-QUESTIONS**: Q-2026-05-15-Wall-DM-Bias-Mechanism CLOSED; Q-2026-05-15-Texture-DM-Alternative OPENED.

### 2026-05-15 — Pillar 6 Pathway B closure attempt (Math408)
- **Pillar**: 6
- **Old tier**: T4 STRONG EVIDENCE (post-Math407 ROLLBACK)
- **New tier**: T4 ⊕ T3 ⊕ T2 (composite)
- **Reason**: Math408 explicit O_h character decomposition refutes Math406's literal SO(4) adjoint identification at the cubic algebraic level. The 6-band decomposes as A_1g ⊕ E_g ⊕ T_2g (only one 3-dim irrep, where SO(4) adjoint requires two). Adds T3 PROOF SKETCH (Stueckelberg dynamical bridge candidate) + T2 CONJECTURE (SO(4) emergence via Brazovskii fluctuation-induced isotropy). 4 falsification gates F1-F4 pre-registered. NO T5/T6 promotion claimed.
- **Source Math notes**: Math408
- **CHANGELOG**: `[Theory] Math408 — Pillar 6 Pathway B closure attempt ... 2026-05-15`

---

## §2. 2026-05-12 entries (Math404 anchor era)

### 2026-05-12 — Pillar 6 T5 → T4 ROLLBACK
- **Pillar**: 6
- **Old tier**: T5 CLOSED@Pathway-B-structural (Math406 promotion)
- **New tier**: T4 STRONG EVIDENCE (rollback)
- **Reason**: Operator Round-1 hostile review of Math406 found three concrete objections: (i) eigenvalue degeneracy (1+2+2+1) used as proxy for representation decomposition without explicit O_h eigenvector test; (ii) scalar-Hessian-to-gauge-adjoint dynamical bridge missing; (iii) Math403 SM-spectroscopic mismatch not resolved. All three accepted as binding.
- **Source Math notes**: Math407 (rollback record), Math406 (target)
- **CHANGELOG**: `Adversarial-audit ROLLBACK: Pillar 6 T5→T4 ... 2026-05-12`

### 2026-05-12 — Math404 Planck anchor (no tier change, structural baseline)
- **Pillar**: 9 (T7 unchanged) + supporting all
- **Reason**: TECT canonical scale identified as Planck scale within O(1) factor (1 TECT energy unit = 1.30 M_Pl c²). Sets physical units for Pillar 6/10/11 closure programmes. NOT a tier promotion but a structural calibration enabling subsequent quantitative claims.
- **Source Math notes**: Math404
- **CHANGELOG**: `[Theory] Math404 — TECT canonical scale identification via Pillar 9 (Newton G) anchoring ... 2026-05-12`

### 2026-05-12 — Math402 → PRE-ANCHOR EXPLORATORY reclassification
- **Pillar**: 11
- **Reason**: Math402's Kibble-Zurek defect dilution analysis was based on N_e ≈ 45 e-folds with 10^58 excess (pre-Math404 GUT-scale assumption). Math404 anchor deepens excess to 10^114 requiring N_e ≈ 88. Math402's quantitative N_e ≈ 45 closure window reclassified as EXPLORATORY; framework valid but values obsolete.
- **Source Math notes**: Math407 (reclassification), Math402 (target), Math409 (post-anchor recalc)

---

## §3. 2026-05-11 entries (Reading H adoption)

### 2026-05-11 — Pillar 4 sub-task 2 reformulation under Reading H
- **Pillar**: 4
- **Old tier**: T2 CONJECTURE (pre-Math400 era)
- **New tier**: T6 PROVED CONDITIONAL on Reading H + Lemmas A, B, E_3'
- **Reason**: Math401 operator binding consensus: canonical TECT vacuum interpretation shifted from "BCC = thermodynamic vacuum" (pre-Math400) to "Reading H ensemble vacuum + BCC stable cosmologically-relevant fluctuation channel" (post-Math400-AddE/AddF). Math400-AddE Path α confirmed; Math400-AddF BCC channel stable.
- **Source Math notes**: Math401, Math400-AddE, Math400-AddF
- **CHANGELOG**: `[Theory] Math401 — Archive operator's binding consensus statement on Reading H adoption ... 2026-05-11`

---

## §4. 2026-05-09 and earlier (pre-Reading-H era)

Earlier tier transitions (Math353-Math400 era) are documented in CHANGELOG.md and individual Math notes; they predate the introduction of this STATUS-HISTORY canonical-archive practice. Future cleanup pass may retroactively populate them as `§5. Historical (pre-2026-05-09)` if archival demand arises.

---

## §5. Cross-references

- `Codes/config/pillar_status.json` — current canonical tier scoreboard (machine-readable).
- `Website/data/status.js` — display version of the scoreboard.
- `CHANGELOG.md` — full chronological record of every change (theory + code + infrastructure).
- `Docs/status/TOE-FACT-SHEET.md` — Stage-1 11-pillar narrative summary.
- `Docs/status/OPEN-QUESTIONS.md` — Active falsification gates and resolution status.
- `Docs/status/NEGATIVE-RESULTS.md` — refutations and audit-rollback records.

---

## §6. How to add a new entry (binding workflow + 3-layer automation)

When a Pillar tier changes (promotion, demotion, split, rollback), the change MUST be recorded in this file in the SAME COMMIT as the corresponding pillar_status.json + Math note + CHANGELOG entry (per CLAUDE.md §3 atomic-write rule).

### §6.1 Recommended: one-line CLI (NEW 2026-05-15)

The fastest path is the `tect tier-change` subcommand which auto-appends the entry to this file:

```powershell
.\Codes\scripts\tect.ps1 tier-change `
    -Pillar 11.A `
    -OldTier T2 -NewTier T1 `
    -Description "wall-DM REFUTED" `
    -Reason "Math409-AddD-AddC: TECT walls violate FMP 2003 by 10^59.9 factor; three bias mechanisms inadequate" `
    -SourceNotes "Math409-AddD-AddC, Math409-AddD" `
    -ChangelogRef "[Theory/Negative-Result] Math409-AddD-AddC ... 2026-05-15" `
    -OpenQuestions "Q-2026-05-15-Wall-DM-Bias-Mechanism CLOSED; Q-2026-05-15-Texture-DM-Alternative OPENED" `
    -ApplyToPillarStatus
```

This invokes `Codes/scripts/log_tier_change.py` which:
1. Validates tier syntax (T0..T7, split syntax `T4|T2`).
2. Builds the entry per §6.3 schema.
3. Auto-appends under today's section (creates new §N if needed).
4. (optional) Updates `pillar_status.json` tier field via `--apply-to-pillar-status`.

### §6.2 Auto-detection watchdog (NEW 2026-05-15)

`Codes/scripts/detect_tier_change.py` runs as snapshot.ps1 step 0.7 BEFORE every commit. It diffs current pillar_status.json against git HEAD and warns (non-fatal) if any tier changes are NOT yet logged in this file. Run manually anytime:

```bash
python3 Codes/scripts/detect_tier_change.py            # warning-only
python3 Codes/scripts/detect_tier_change.py --strict   # exit 1 if drift
```

### §6.3 Manual fallback (entry schema)

If neither the CLI helper nor the watchdog is available, the manual entry format is:

```
### YYYY-MM-DD — Pillar N <description>
- **Date**: YYYY-MM-DD
- **Pillar**: N (or N.X if split)
- **Old tier**: <T-tier>
- **New tier**: <T-tier>
- **Reason**: <one-paragraph rationale>
- **Source Math notes**: <list>
- **CHANGELOG**: <matching entry tag>
- **OPEN-QUESTIONS** (optional): <Q-IDs CLOSED/OPENED>
```

### §6.4 Auto-conversion to website

The `Codes/tools/generate_status_history.py` script (auto-invoked by snapshot.ps1 step 2.7) converts this Markdown into `Website/data/status-history.js` for browser display. The script runs on every snapshot, so the website is always in sync.

### §6.5 Three-layer defence summary

| Layer | Tool | Behaviour |
|---|---|---|
| 1 (write) | `log_tier_change.py` + `tect tier-change` | One-line CLI to append entries |
| 2 (detect) | `detect_tier_change.py` + snapshot.ps1 step 0.7 | Pre-snapshot warning if pillar_status.json changed without STATUS-HISTORY entry |
| 3 (sync) | `generate_status_history.py` + snapshot.ps1 step 2.7 | Auto-rebuild Website/data/status-history.js |

---

End of STATUS-HISTORY.md (binding from 2026-05-15).
