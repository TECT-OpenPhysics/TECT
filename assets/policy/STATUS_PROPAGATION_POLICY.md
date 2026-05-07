# Status Propagation Policy

**Binding from**: 2026-05-07
**Maintainer**: Jusang Lee (`jtkor@outlook.com`)
**Governed by**: `CLAUDE.md` §2 (canonical-source hierarchy), §3 (atomic-write rule), §16 (snapshot discipline), this policy.
**Sister policies**: `WEBSITE_AUTO_SYNC.md` (per-page sync table), `SNAPSHOT_POLICY.md` (8-step orchestrator), `POSTMORTEM_RECURRENCE_POLICY.md` (pre-commit completeness).

This document defines how a single change to the canonical 11-Pillar Stage-1 scorecard (`Docs/status/TOE-FACT-SHEET.md` and its mirror `Website/data/status.js`) is propagated, in a single mechanical step, to every other artefact that displays or depends on Stage-1 status — website pages, README, paper-impact reports, and downstream new-paper assessment. It also defines the audit log that proves every propagation actually ran.

The rationale for this policy is the recurring failure mode observed across 2026-04 and 2026-05: a status change (e.g., Math348 BCC-uniqueness refutation, Math350 deep-regime saddle verdict) is correctly written to `TOE-FACT-SHEET.md` and `STATUS-HISTORY.md`, but the resulting tier downgrade is then NOT reflected in the index banner card, the theory.js Honest Limitations card, the papers.js dependency table, the README.md "Current state" snapshot, or the paper drafts that cite the affected pillar. Each of those is a manual edit that must be remembered. The present policy mechanises every one of those edits.

---

## §1. Single source of truth

The Stage-1 scoreboard in `Website/data/status.js` (the `11-Pillar scoreboard in canonical tiers` table inside the `window.TECT_STATUS` blocks array) is the **operational single source of truth** for the per-pillar T-tier (T0--T7). Every other artefact in the repository that displays a per-pillar tier (or a derivation thereof) is downstream of that table.

The chain of authority is:

```
pillar-level Math note            (CLAUDE.md §2 canonical evidence)
  -> Docs/status/TOE-FACT-SHEET.md  (canonical scorecard)
  -> Website/data/status.js          (operational SoT for propagation)
  -> all other downstream artefacts  (auto-derived, never hand-edited)
```

The chain MUST satisfy two invariants:

1. **Math-note > FACT-SHEET > status.js**: any conflict in tier label is a synchronisation defect. The Math note (cited in `STATUS-HISTORY.md`) overrides the FACT-SHEET; the FACT-SHEET overrides `status.js`. Repair direction is downward.
2. **status.js -> downstream**: any conflict between `status.js` and a downstream artefact (e.g., the index.js banner) is repaired by re-running `propagate_status.py`. The downstream artefact is never hand-edited inside an auto-propagation zone.

A pillar tier change therefore consists of three commits, in order: (i) Math-note write, (ii) `TOE-FACT-SHEET.md` + `STATUS-HISTORY.md` row update, (iii) `status.js` row update + `propagate_status.py` run. (i)+(ii) MAY be atomic; (iii) is typically run by the snapshot pipeline immediately after (i)+(ii).

---

## §2. Page-coverage matrix

`propagate_status.py` is responsible for keeping the following targets in sync with `status.js`. Each target carries an explicit anchor-marker zone (see §4) so that the auto-propagated content can be regenerated without disturbing the hand-curated surrounding text.

| Target | What is auto-propagated | Anchor zone tag |
|---|---|---|
| `Website/data/status_pillar_tiers.js` | machine-readable JSON payload (`window.TECT_STATUS_TIERS`) | entire file (`AUTO-GENERATED` header) |
| `Website/data/index.js` | "Latest state snapshot" card (Stage-1 scoreboard summary) + "Comparison vs other frameworks" TECT column | `<!-- PROP-AUTO:stage1-summary -->` and `<!-- PROP-AUTO:comparison-tect-col -->` |
| `Website/data/theory.js` | subtitle ("Partial TOE candidate" classification line) + Honest Limitations card per-pillar items | `<!-- PROP-AUTO:partial-toe-classification -->` and `<!-- PROP-AUTO:honest-limitations -->` |
| `Website/data/toe.js` | per-Stage Stage-1 pillar tier overlay (already implemented by `sync_toe_from_states.py`) | `<!-- PROP-AUTO:stage1-overlay -->` |
| `Website/data/papers.js` | per-paper Stage-1 dependency tier badges (derived from `papers_math_dependencies.js` + `status.js`) | `<!-- PROP-AUTO:papers-tier-badges -->` |
| `Website/data/history.js` | most recent Stage-1 tier-change ledger entries (top N rows, append-only mirror of `STATUS-HISTORY.md`) | `<!-- PROP-AUTO:status-history-recent -->` |
| `README.md` (repo root + Github mirror) | "Current state (YYYY-MM-DD)" section | `<!-- PROP-AUTO:readme-current-state -->` |
| `Docs/status/EVIDENCE-INDEX.md` | per-pillar tier column in §1 (claim → evidence map) | `<!-- PROP-AUTO:evidence-pillar-tiers -->` |

Targets are listed in `Codes/config/status_propagation_targets.json` (NOT hard-coded inside `propagate_status.py`). Adding a new target is a config-only change.

Pages NOT in this list are auto-generated from other sources (per `WEBSITE_AUTO_SYNC.md` §1) or do not display Stage-1 tier information; they are out of scope for `propagate_status.py`.

### §2.1 Out-of-scope manual narrative

Hand-written narrative in `Website/data/_narrative/*.md` and inside Math notes / paper drafts is OUT OF SCOPE for automatic rewriting. Promotional adjectives ("rigorous", "established", "candidate", etc.) inside narrative are checked by `paper_status_impact.py` (§7) which emits warnings but never modifies prose. Narrative repair is a manual edit performed by the operator.

---

## §3. Direction of propagation

`propagate_status.py` runs in one direction only: `status.js -> targets`. It never modifies `status.js`, `TOE-FACT-SHEET.md`, `STATUS-HISTORY.md`, or any Math note. If the pillar tier in `status.js` is wrong, the operator hand-edits `status.js` (and the upstream Math note and FACT-SHEET); `propagate_status.py` then propagates the fix.

Reverse-flow tools (`status_history_tracker.py` §6) DETECT inconsistency between `TOE-FACT-SHEET.md` and `STATUS-HISTORY.md`, but they never auto-repair upstream. They emit a stub entry or a diff for the operator to commit.

---

## §4. Anchor-marker convention

Each auto-propagation zone is bounded by HTML/JS comment markers of the form:

```
<!-- PROP-AUTO:<zone-tag> START
     generator: Codes/tools/propagate_status.py
     do-not-edit-between-markers
     last-regenerated: YYYY-MM-DDTHH:MM:SSZ
-->
... auto-generated content ...
<!-- PROP-AUTO:<zone-tag> END -->
```

For JavaScript data files (`Website/data/*.js`), the markers are inserted as `/* ... */` block comments around the auto-generated string fragment.

For Markdown targets (`README.md`, `EVIDENCE-INDEX.md`), the markers are HTML comments that survive Markdown rendering.

`propagate_status.py` regenerates **only** the content between the markers; everything outside is preserved verbatim. Hand-edits between markers will be silently overwritten on the next run.

If a target file does NOT yet contain the anchor markers, `propagate_status.py --init` inserts them at a documented insertion point (specified per target in the config JSON) and emits a diff for operator review before any content is written.

---

## §5. Operating modes

`propagate_status.py` supports four CLI modes:

| Mode | Behaviour |
|---|---|
| `--check` | dry-run; parse `status.js`, render every target's auto-zone, compare against current file content, print unified diff per target. Exit 0 if no diffs; exit 1 if at least one target is out of sync. |
| (default) | parse `status.js`, render every target's auto-zone, write the updated content (only between anchor markers). Exit 0 on success, 2 on I/O error. |
| `--init` | for any target whose auto-zone is missing, insert the anchor markers at the documented insertion point. Used once per new target. Exit 0 on success. |
| `--targets <name1> <name2> ...` | restrict propagation to a subset of targets (all four modes accept this). Useful for incremental fixes. |

`--check` is the mode invoked by the snapshot pipeline pre-commit gate (§8) and by `verify_website.py` (`POSTMORTEM_RECURRENCE_POLICY.md` §3). A non-zero `--check` exit blocks snapshot promotion.

---

## §6. Audit log

Every `propagate_status.py` execution (in any mode except `--check`) appends one line to `Docs/status/propagation-log.md` of the form:

```
| YYYY-MM-DD HH:MM:SS UTC | targets-touched=<N> | targets-changed=<M> | status.js-sha=<7-char-hash> | invocation=<argv> |
```

The log file is append-only. Each entry's `<7-char-hash>` is the first 7 characters of `sha256(status.js content)` at the moment of the run; this lets the operator (or a forensic reviewer) tie any past propagation to the exact upstream source state.

The log is checked into git but is NOT inside `.gitignore`-able territory: it is the auditable evidence that propagation actually ran when the snapshot pipeline says it did.

---

## §7. Paper-impact gate

`paper_status_impact.py` (Codes/tools/) is the companion tool that detects which paper drafts under `Docs/papers/{papers,auxiliary,top_impact,epochs}/*` are affected by a Stage-1 tier change.

### §7.1 Inputs

- `Docs/status/STATUS-HISTORY.md` — top N most recent entries (default N = 5; configurable via `--since YYYY-MM-DD`).
- `Website/data/papers_math_dependencies.js` (auto-generated by `extract_paper_dependencies.py`) — paper -> Math note dependency map.
- `Website/data/status.js` — current pillar tiers.

### §7.2 Output

`Docs/status/paper-impact-report.md` (auto-overwritten on every run):

```markdown
# Paper Status Impact Report

Generated: <UTC timestamp>
States.js sha: <7-char hash>
Recent STATUS-HISTORY entries audited: <N>

## Affected papers (REVISION REQUIRED)

For each recent STATUS-HISTORY entry that downgrades or refutes a pillar tier:

### <Status-history entry tag>: <one-line summary>

| Paper | Reason | Recommended action |
|---|---|---|
| `Paper-XX` | cites Math-note in refuted pillar / has wording stronger than current tier | revise §X / abstract / theorem statement |
```

The report includes ONLY revisions whose mechanism is mechanical (cited Math-note refuted, tier label inside paper exceeds current canonical tier). Promotional-adjective audits are advisory and listed separately in a `## Advisory (manual review)` section.

### §7.3 Pre-snapshot blocking gate

By default, a non-empty "REVISION REQUIRED" section blocks snapshot promotion (snapshot.ps1 step [2.5]). The operator can override via `snapshot.ps1 -GrandfatherPaperImpact` (with the rationale recorded in the snapshot-log entry). Advisory items NEVER block.

### §7.4 No automatic prose rewriting

`paper_status_impact.py` ONLY emits a report; it never modifies any `.tex` file. Paper prose rewriting is binding-manual (CLAUDE.md §9 / UPDATE_POLICY §11). The operator chooses to revise, retract, grandfather, or accept the impact for each affected paper.

---

## §8. New-paper assessment

`paper_need_assessment.py` (Codes/tools/) is the third tool in the propagation chain. It evaluates each recent STATUS-HISTORY entry against the policy rules in `Docs/policy/MATH_NOTE_AND_PAPER_DISCIPLINE.md` §3 (new-paper trigger table) and produces a recommendation list.

The tool emits a `## Suggested new papers` section appended to `paper-impact-report.md`. Recommendations are always advisory; they NEVER block snapshot promotion. The operator decides whether to act on a recommendation.

Categories of recommendation:

- **NEW_AUDIT_PAPER**: triggered by T6/T7 -> T0 refutations (e.g., Math348 BCC-uniqueness refutation -> "An audit of the candidate global-12-star optimality argument"). Appropriate genre: PRL Comment style.
- **NEW_CONSOLIDATION_PAPER**: triggered by T1/T2 -> T7 unconditional promotions (e.g., Pillar 5 chirality full closure -> "Emergent fermion chirality in the BCC topological condensate"). Appropriate genre: full PRD article.
- **NEW_NEGATIVE_RESULT_NOTE**: triggered by F-tag falsification gates firing without an existing paper to retract (e.g., Math350 deep-regime saddle verdict -> "BCC condensate at deep negative chemical potential: a saddle-point report").
- **PAPER_REVISION_ONLY**: triggered by intermediate transitions (e.g., T2 -> T4) that are absorbed by an existing paper revision rather than a new manuscript.
- **NONE**: tier change too small or already covered by existing draft; no new paper warranted.

The decision rules are codified in `MATH_NOTE_AND_PAPER_DISCIPLINE.md` §3 and may evolve; the present policy is the binding interface contract.

---

## §9. Snapshot pipeline integration (Step [2.5])

The 8-step `snapshot.ps1` orchestrator (`SNAPSHOT_POLICY.md` §5) gains a new pre-commit step **[2.5] Status propagation**:

1. `python -u Codes/tools/propagate_status.py --check` — exit 0 required.
2. If non-zero: run `python -u Codes/tools/propagate_status.py` (apply mode), then re-run `--check`. Still non-zero -> abort snapshot.
3. `python -u Codes/tools/paper_status_impact.py --since <last-snapshot-date>` — if "REVISION REQUIRED" section is non-empty AND `-GrandfatherPaperImpact` is not set -> abort snapshot.
4. `python -u Codes/tools/paper_need_assessment.py --since <last-snapshot-date>` — advisory only; output appended to report; never blocks.
5. `python -u Codes/tools/status_history_tracker.py --check` — verify `STATUS-HISTORY.md` is in sync with `TOE-FACT-SHEET.md` Stage-1 deltas since the last snapshot. Non-zero -> abort.

Step [2.5] runs after `verify_website.py` (Step [2]) and before the atomic-commit (Step [3]). Its outputs are committed in the same atomic-commit if `propagate_status.py` produced any changes.

---

## §10. Failure-mode taxonomy and recovery

| Symptom | Cause | Recovery |
|---|---|---|
| `--check` reports diff but no Math-note / FACT-SHEET change in flight | hand-edit drift inside an auto-zone | run apply mode; commit |
| `--check` reports diff, FACT-SHEET row updated, `status.js` row NOT updated | (i) of §1 forgotten | hand-edit `status.js`, then apply |
| paper-impact "REVISION REQUIRED" non-empty, snapshot blocked | a paper draft cites a refuted Math-note | revise paper / `[NEEDS_UPDATE]` flag / `-GrandfatherPaperImpact` |
| `propagation-log.md` last entry > 30 days but `status.js` mtime is recent | snapshot debt accumulation | run `propagate_status.py` + snapshot |
| `--init` mode reports unknown insertion point | new target without config entry | edit `status_propagation_targets.json` first |

---

## §11. Recurrence-protection guarantees

The combination of §1--§10 protects against the four canonical failure modes observed in 2026-04 and 2026-05:

1. **Math348-style refutation that doesn't reach the website**: §2 requires every public-facing page to have an anchor zone; §9 step 1 + 2 fail snapshot if any zone is stale.
2. **Math350-style regime split that doesn't reach paper drafts**: §7 reads STATUS-HISTORY directly and cross-checks paper dependency maps; §9 step 3 blocks snapshot until either revised or grandfathered.
3. **`status.js` updated but `toe.js` overlay stale**: subsumed by §2 and §9; the existing `sync_toe_from_states.py` becomes one renderer inside `propagate_status.py`.
4. **README "Current state" section years out of date**: §2 explicit target; §9 step 1+2 keep it pinned to the current `status.js`.

The auditable evidence that the policy operated as intended is the per-snapshot entry in `propagation-log.md` (§6) plus the matching `snapshot-log.md` entry (`SNAPSHOT_POLICY.md` §7).

---

## §12. Cross-references

- `CLAUDE.md` §2 (canonical-source hierarchy), §3 (atomic-write rule), §16 (snapshot discipline).
- `Docs/policy/SNAPSHOT_POLICY.md` (8-step orchestrator).
- `Docs/policy/WEBSITE_AUTO_SYNC.md` (per-page sync table).
- `Docs/policy/POSTMORTEM_RECURRENCE_POLICY.md` (pre-commit completeness).
- `Docs/policy/MATH_NOTE_AND_PAPER_DISCIPLINE.md` (new-paper trigger table; A20).
- `Docs/policy/STATUS_NOMENCLATURE.md` (T0--T7 canonical tiers).
- `Docs/status/STATUS-HISTORY.md` (append-only tier-change ledger).
- `Codes/tools/propagate_status.py` (this policy's main implementation).
- `Codes/tools/paper_status_impact.py` (companion).
- `Codes/tools/paper_need_assessment.py` (companion).
- `Codes/tools/status_history_tracker.py` (FACT-SHEET <-> STATUS-HISTORY consistency check).
- `Codes/config/status_propagation_targets.json` (target list, externalised).

End of STATUS_PROPAGATION_POLICY.md (binding from 2026-05-07).
