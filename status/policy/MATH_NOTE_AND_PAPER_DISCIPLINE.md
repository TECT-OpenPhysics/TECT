# Math-Note and Paper Discipline

**Binding from**: 2026-05-07
**Maintainer**: Jusang Lee (`jtkor@outlook.com`)
**Governed by**: `CLAUDE.md` §4 (chat-content auto-archival), §9 (manuscript discipline), `UPDATE_POLICY.md` §11 (manual-authorship rule), `STATUS_PROPAGATION_POLICY.md` §8 (new-paper assessment).
**Sister tools**: `Codes/tools/paper_status_impact.py`, `Codes/tools/paper_need_assessment.py`.

This document defines, mechanically, when a tier change in the canonical Stage-1 scoreboard (`Docs/status/TOE-FACT-SHEET.md` + `Website/data/status.js`) warrants the creation of a new paper, when an existing paper revision is sufficient, and when no paper-level action is required at all. It also restates the binding **manual-authorship rule** (`UPDATE_POLICY.md` §11) so the AI collaborator does not auto-draft paper prose even when a status change makes the omission feel mechanical.

The companion tool `paper_need_assessment.py` reads `STATUS-HISTORY.md` and emits an advisory section in `Docs/status/paper-impact-report.md`. Its recommendations are advisory only; they never block snapshot promotion (only `paper_status_impact.py` REVISION-REQUIRED flags can do that, per `STATUS_PROPAGATION_POLICY.md` §7.3).

---

## §1. Genres of paper output

TECT manuscripts under `Docs/papers/` are classified into four genres. The genre determines the rules below.

| Code | Genre | Typical journal style | Source folder |
|---|---|---|---|
| **MAIN** | Mainline pillar / closure paper | PRD article | `Docs/papers/papers/` |
| **AUX** | Auxiliary / mechanism / methodology paper | PRD article or supplement | `Docs/papers/auxiliary/` |
| **TI** | Top-impact / technical-correction paper | PRL Letter or PRL Comment | `Docs/papers/top_impact/` |
| **EPOCH** | Epoch retrospective | not externally publishable as primary research; archival | `Docs/papers/epochs/` |

A new paper is always one of these genres; the genre constrains the appropriate language tier and the publication target.

---

## §2. Trigger-to-action mapping

When a STATUS-HISTORY entry lands in the canonical ledger, the action below is recommended (NOT auto-executed). The operator decides; `paper_need_assessment.py` only emits the suggestion list.

| STATUS-HISTORY direction | Affected pillar tier change | Recommended action | Genre |
|---|---|---|---|
| **REFUTATION** ⬇⬇ | T6 / T7 -> T0 (counter-example) | **NEW_AUDIT_PAPER**: a Comment-style note that documents the counter-example and the retraction trail. Cites the offending Math note and the prior paper(s) that depended on the refuted claim. | TI (PRL Comment) |
| **REFUTATION** ⬇⬇ | T1–T4 -> T0 (falsification gate fired) | **NEW_NEGATIVE_RESULT_NOTE**: a short methodology paper documenting the falsification mechanism. | AUX |
| **DOWNGRADE** ⬇ | T7 -> T6 / T6 -> T4 / T5 -> T4 | **PAPER_REVISION_ONLY**: existing paper(s) absorb the downgrade via wording calibration. | n/a (revision) |
| **DOWNGRADE** ⬇ | T7 / T6 -> T3 or below | **NEW_AUDIT_PAPER** if the prior tier had been claimed in an externally circulated paper; else PAPER_REVISION_ONLY. | TI or revision |
| **UPGRADE** ⬆ | any pillar reaching T7 unconditional | **NEW_CONSOLIDATION_PAPER**: full closure paper consolidating the proof chain end-to-end. | MAIN |
| **UPGRADE** ⬆ | T1 / T2 -> T4 / T5 / T6 | **PAPER_REVISION_ONLY**: incorporate evidence into existing paper. Or NEW_AUX if the mechanism is novel and large enough. | revision (or AUX) |
| **WORDING** ↺ | scope / hypothesis-set narrowing | **PAPER_REVISION_ONLY**: wording calibration only. | revision |
| **SPLIT** ↪ | single tier -> regime-dependent sub-rows | **PAPER_REVISION_ONLY**: split the relevant section in any paper that asserted the previously unified tier. | revision |

The mapping is intentionally conservative: it favours revisions over new papers when the existing manuscript can carry the corrected claim. New papers are reserved for (a) refutations that genuinely need a Comment-style retraction, (b) full theorem-level closures that warrant a self-contained article, and (c) novel mechanism notes too large to fold into existing drafts.

---

## §3. Decision rule for the operator

When `paper_need_assessment.py` emits a recommendation, the operator chooses:

1. **Accept (NEW)**: open a new file under the appropriate `Docs/papers/{papers,auxiliary,top_impact,epochs}/` subfolder and start drafting. The AI collaborator MUST NOT auto-draft prose; the operator either drafts manually or invokes the AI explicitly with the `tect-research:tect-latex-paper` skill (`CLAUDE.md` §9).
2. **Accept (REVISION)**: edit the existing paper(s) flagged by `paper_status_impact.py` REVISION-REQUIRED and re-run snapshot.
3. **Defer**: add the recommendation to `OPEN-QUESTIONS.md` with an explicit `Q-` tag and a target review date.
4. **Reject**: record a one-line rationale in `paper-impact-report.md` (manual annotation between propagation runs) explaining why the recommendation was not actionable. The next run of `paper_need_assessment.py` will re-emit if the underlying STATUS-HISTORY entry is still in window.

No automatic paper drafting; no automatic acceptance. Section §2 is a guide, not a workflow.

---

## §4. Manual-authorship rule (re-statement, binding)

Per `UPDATE_POLICY.md` §11 and `CLAUDE.md` §9: the AI collaborator does NOT auto-generate, auto-draft, or pre-emptively rewrite paper prose. This rule is binding even when a status change makes paper revision feel mechanical. The operator issues an explicit instruction (e.g., "rewrite Auxiliary-02 abstract", "draft Math-note section for Paper-XX") before any prose work begins.

Mechanical edits to paper sources permitted under this discipline:

- Fixing a `\cite{}` key after a Math-note rename (per `UPDATE_POLICY.md` §1.5 paper-side trigger).
- Updating the `% Canonical archive:` header to add a newly-cited Math note.
- Inserting `[NEEDS_UPDATE]` or `AUDIT-FLAG` banners above `\documentclass` in response to a `paper_status_impact.py` REVISION-REQUIRED finding.

Anything beyond these mechanical touches requires explicit operator instruction.

---

## §5. Naming conventions for new papers

When a new paper IS created (per §3 step 1), the following naming conventions apply:

| Genre | Path | Stem prefix | Example |
|---|---|---|---|
| MAIN | `Docs/papers/papers/Paper-NN-<descriptor>/Paper-NN.tex` | `Paper-NN` | `Paper-17-Pillar-4-SubTask-3-Closure` |
| AUX | `Docs/papers/auxiliary/Auxiliary-NN-<descriptor>/Auxiliary-NN.tex` | `Auxiliary-NN` | `Auxiliary-03-Newton-Krylov-v2` |
| TI | `Docs/papers/top_impact/Paper-TI-NN-<descriptor>/Paper-TI-NN.tex` | `Paper-TI-NN` | `Paper-TI-5-BCC-Uniqueness-Refutation-Comment` |
| EPOCH | `Docs/papers/epochs/Epoch-NN-<descriptor>/Epoch-NN.tex` | `Epoch-NN` | `Epoch-13-2026-Q2-Retrospective` |

`NN` is the next free integer in that genre. `paper_need_assessment.py` does NOT pre-allocate the number; the operator chooses on creation.

---

## §6. Cross-references

- `Docs/policy/STATUS_PROPAGATION_POLICY.md` §7--§8 (paper-impact gate, new-paper assessment)
- `Docs/policy/UPDATE_POLICY.md` §1.5 (paper-side triggers), §11 (manual-authorship rule)
- `CLAUDE.md` §4 (chat-content auto-archival), §9 (manuscript discipline)
- `Codes/tools/paper_status_impact.py` (revision detection)
- `Codes/tools/paper_need_assessment.py` (new-paper recommendation)
- `Codes/tools/extract_paper_dependencies.py` (paper -> Math-note map source)
- `Docs/papers/PAPERS_STATUS_REGISTRY.md` (paper roster + per-paper status)
- `Docs/status/paper-impact-report.md` (auto-generated; output of paper-impact + need-assessment)

End of MATH_NOTE_AND_PAPER_DISCIPLINE.md (binding from 2026-05-07).
