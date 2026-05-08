# TECT Update Policy

**Binding from**: 2026-04-15
**Status**: approved (Math39-Reorg era)
**Maintainer**: Jusang Lee (jtkor@outlook.com)

This document is the single, mechanical rulebook for propagating changes
across the TECT repository. Its purpose is to eliminate the need for
case-by-case instructions: when any listed **trigger** occurs, the
corresponding **targets** must be updated in the same commit (or the
next commit if a multi-step promotion is required). Nothing may be
skipped without an explicit entry in `CHANGELOG.md` explaining why.

Read this as a contract between the human maintainer and the AI
collaborator: the AI must apply these rules without being re-prompted.

---

## 0. Nomenclature

- **Theory tag** — `Math<NN>-<descriptor>-<YYYY-MM-DD>`. Global state
  of the theory. One tag = one annotated git tag on `main`.
- **Module version** — `<module>_v<N>.py` plus `Module version: vN.M`
  in the header block. `N` bumps on API / physics-signature change;
  `M` bumps on bug-fix within the same signature.
- **Result tag** — `R-<YYYY-MM-DD>-<seq>-<theory_tag>`. One per run.
- **Closure marker** — `✅ CLOSED` / `⚠ CONDITIONAL` / `⚠ GAP` in the
  Theory↔Code Sync Manifest. A discrepancy transitions `GAP → CONDITIONAL → CLOSED`
  and never regresses silently.

---

## 1. Trigger → Target Matrix

Rows are triggers. Columns collapse to: **what must change in the
same commit**. Items in *italic* are optional but recommended.

### 1.1 Theory-side triggers

| Trigger | Required targets |
|---|---|
| **A new Math-note is added or a Math-note is substantively rewritten** | 1. `docs/math/TECT-Math<NN>.tex.txt` (source) plus compiled PDF if present. 2. `docs/status/research-log.md` — one-line append under MASTER STATUS TABLE. 3. `Website/math/project-<roman>-*.html` — editorial summary updated if the note affects a currently-published claim. 4. `Website/math-notes.html` — table row added (raw index). 5. `Website/math/index.html` — summary card updated if project closure status changed. |
| **A theoretical claim transitions status** (e.g. `FRAMEWORK → PROVED`, or a discrepancy `GAP → CONDITIONAL → CLOSED`) | 1. `docs/status/TECT-Theory-Code-Sync.md` — §1 table row updated; §2 discrepancy block gets a `**[CLOSED YYYY-MM-DD]**` marker with resolution paragraph; §5 Sync Log appended. 2. `Website/math/project-<roman>-*.html` — status tag updated. 3. `Website/math-notes.html` + `Website/math/index.html` — status tag updated. 4. `Website/results.html` — if the claim affects a published numerical prediction. 5. `PDE/tect_version_manifest.py::THEORY_INVARIANTS_CLOSED` / `_OPEN` — move between the two lists. 6. `CHANGELOG.md` — entry under Theory subsection of the active theory tag. |
| **A new theory tag is minted** | 1. `CHANGELOG.md` — new top-level section `[<theory_tag>] — <date>` (Keep-a-Changelog). 2. `Website/changelog.html` — new `<div class="changelog-version">` block prepended. 3. `Website/timeline.html` — new `<li>` prepended to `<ul class="timeline">`. 4. `Website/data/timeline.json` — new entry prepended to `entries[]`. 5. `Website/data/version_index.json` — regenerate via `python tools/build_version_index.py`. 6. `PDE/tect_version_manifest.py::THEORY_VERSION` bumped. 7. `PDE/stamp_version_headers.py::THEORY_VERSION` bumped, then `python PDE/stamp_version_headers.py` run to re-stamp all active modules. 8. `Website/index.html`, `Website/theory.html` — headline theory tag updated. 9. `git tag -a <theory_tag> -m "<one-line summary>"` pushed per `docs/policy/GIT_TAG_POLICY.md`. 10. *Optional*: `docs/status/research-log.md` milestone append. |

### 1.2 Code-side triggers

| Trigger | Required targets |
|---|---|
| **Module API or physics signature changes** (bump `vN → v(N+1)`) | 1. Rename file: `<module>_v<N>.py → <module>_v<N+1>.py`. 2. Demote predecessor: `mv <old> PDE/deprecated/<old>_<YYYY-MM-DD>.py`. 3. `PDE/stamp_version_headers.py::MODULE_VERSIONS` — add new key, keep old key for the demoted file. 4. Run the stamper. 5. `docs/status/TECT-Theory-Code-Sync.md` §4 table — row updated; §5 Sync Log appended. 6. All live import strings, `.bat` / `.ps1` launchers, pipeline modules — renamed. 7. `Website/code.html` — row updated. 8. AST/import smoke-test must pass before commit. |
| **Bug-fix within same signature** (bump `vN.M → vN.(M+1)`) | 1. Header `Module version: vN.M` line bumped (stamper handles if `MODULE_VERSIONS` is edited). 2. `CHANGELOG.md` — Code subsection of the active theory tag. 3. `docs/status/TECT-Theory-Code-Sync.md` §5 Sync Log if the fix closes a discrepancy. |
| **Regime-affecting defaults change** (e.g. solver `quartic_lambda`, `sextic_gamma`) | 1. Hard-wire the new defaults in the module's `make_default_config` (or equivalent). 2. Provide a `--config` JSON overlay path for alternative regimes. 3. Echo the active regime at run start (banner). 4. `PDE/config_template_<regime>.json` — add or update. 5. Archive the previous regime's configs to `PDE/backup_<PREV_REGIME>_<YYYY-MM-DD>/` with a rollback README. 6. `PDE/tect_version_manifest.py::regime` field updated. 7. `CHANGELOG.md` + `Website/theory.html` + `Website/code.html`. |
| **A module is retired** | 1. Move to `PDE/deprecated/<name>_<YYYY-MM-DD>.py`. 2. Purge all live imports, `.bat` / `.ps1` launchers, pipeline modules. 3. `PDE/stamp_version_headers.py::MODULE_VERSIONS` — key retained for audit but commented `# deprecated`. 4. `docs/status/TECT-Theory-Code-Sync.md` §4. 5. `Website/code.html` — moved to deprecated table. |

### 1.3 Result-side triggers

| Trigger | Required targets |
|---|---|
| **A production run is produced** (pipeline executes cleanly) | 1. Run directory contains `tect_version_manifest.json` (automatic). 2. `RESULT.md` in the run directory, filled per `PDE/RESULT_TEMPLATE.md`. 3. Result tag `R-<YYYY-MM-DD>-<seq>-<theory_tag>` stamped in the manifest. 4. If cited in any paper or on the Website: an entry under `Website/results.html`. |
| **A result is retracted or superseded** | 1. `RESULT.md` — `status: retracted`. 2. `docs/status/research-log.md` — one-line append with successor result-tag. 3. `Website/results.html` — row moved to "superseded" block. |

### 1.4 Website-side triggers

| Trigger | Required targets |
|---|---|
| **Any edit to any Website page** | The `<p class="timestamp">Last updated: YYYY-MM-DD</p>` line in that page's `<footer>` MUST be updated to today's date. No exceptions. |
| **Editorial summary revised** (`Website/math/project-*.html`) | 1. Per-page timestamp. 2. Raw-note link in Sources table must still resolve. 3. *Optional*: reviewer initials in a `<p class="muted">` line. |
| **Data files edited** (`Website/data/*.json`) | No timestamp rule applies (JSON carries its own `"generated"` field); but any consumer page that cites the JSON must be timestamp-bumped. |

### 1.5 Paper-side triggers

| Trigger | Required targets |
|---|---|
| **Paper draft revised** | 1. `docs/papers/.../<file>.tex` edited. 2. PDF rebuilt if compilation toolchain is available. 3. `Website/papers.html` — status tag updated if the paper moved between `IN PREPARATION / FRAMEWORK WRITTEN / PROP X COMPLETE / SUBMITTED / PUBLISHED`. |
| **Paper submitted or published** | 1. `Website/papers.html` — status + venue + date. 2. `Website/timeline.html` + `Website/data/timeline.json` — new entry under area `Paper`. 3. `docs/status/research-log.md` — milestone append. |

> **Manual-authorship rule (binding).** Any creation, substantive
> revision, or rewording of prose inside `docs/papers/*.tex`,
> `docs/papers/supplementary/*`, public-facing blog posts, abstracts,
> or press-style articles MUST be performed **only when the user
> issues an explicit, unambiguous manual instruction** (e.g. "write
> Section II", "draft the abstract for Paper III", "rewrite this
> paragraph"). The AI collaborator does not auto-generate, auto-draft,
> or pre-emptively rewrite paper prose — even when a closure or
> theory-tag bump would make such prose technically useful. Automatic
> propagation under §1.1–§1.4 is restricted to registries, status
> ledgers, sync manifests, changelog entries, and Website status tags;
> paper prose is explicitly out of scope. Editorial touches to
> `docs/papers/*.tex` that are strictly mechanical (e.g. fixing a
> broken `\cite` key after a Math-note rename, updating a version
> number in a preamble comment) are permitted under §1.2 code-side
> triggers and must be flagged in the commit message as a mechanical
> touch, not a prose edit.

---

## 2. Ordering rule (must-pre-must)

Some targets depend on others. Honour this order inside a single
commit to avoid transient inconsistency:

1. **Source-of-truth first**: `docs/math/`, `PDE/*.py`, raw `.tex`.
2. **Registries second**: `PDE/stamp_version_headers.py::MODULE_VERSIONS`,
   `PDE/tect_version_manifest.py::THEORY_VERSION` / `THEORY_INVARIANTS_*`.
3. **Run the stampers**: `python PDE/stamp_version_headers.py`.
4. **Changelogs third**: `CHANGELOG.md`, `docs/status/TECT-Theory-Code-Sync.md`,
   `docs/status/research-log.md`.
5. **Data artefacts fourth**: `python tools/build_version_index.py`,
   manually prepend to `Website/data/timeline.json`.
6. **Website views last**: `Website/*.html` (headline, page-specific content,
   footer timestamp), `Website/math/*.html`.
7. **Git tag last**: `git tag -a <theory_tag>` only after all of the above
   are committed. Tags are immutable per `GIT_TAG_POLICY.md`.

---

## 3. Closure discipline (for discrepancies and conjectures)

A discrepancy in `docs/status/TECT-Theory-Code-Sync.md` §2 does **not**
close silently. The transition `GAP → CONDITIONAL → CLOSED` requires:

1. A `**[CLOSED YYYY-MM-DD]**` marker inside the discrepancy block.
2. A one-paragraph **Resolution** note citing (a) the code locus
   (file + line range) and (b) the theory reference (Math-note + §/eq).
3. The original text preserved under `Legacy text preserved below:` —
   no redaction. History stays auditable.
4. §5 Sync Log row appended.
5. The §1 status column updated in the same commit.

A conjecture in any Math-note is treated the same way: once proved, the
text gains a `\textbf{Proved (YYYY-MM-DD).}` block; the original
conjecture statement remains visible.

---

## 4. Acceptance gates

Before any commit that touches more than one of the targets above:

1. **AST / import smoke-test** on all renamed or re-stamped `.py` files:
   `python -c "import ast; [ast.parse(open(f).read()) for f in <list>]"`.
2. **Version-index drift check**: `python tools/build_version_index.py --check`
   must exit 0.
3. **Website link check** (spot): no broken `href` to `docs/math/` or
   `docs/papers/` in `Website/math/project-*.html`.
4. **Regime banner echo** on any solver run: first three lines of stdout
   must contain `regime : Brazovskii` (or the currently-locked regime).

Failed gates block the commit; the fix is a new commit, never `--amend`
on a pushed branch.

---

## 5. AI collaborator directive

The AI collaborator SHALL:

- Read this document at the start of any session in which file edits
  are anticipated.
- Apply §1–§4 without being asked on a per-target basis.
- When a user request spans a trigger category, enumerate the
  mandated targets in a short plan before editing.
- When a target cannot be updated (permissions, missing file, tooling
  absent), flag it explicitly in the response rather than silently
  skipping.
- Treat this policy as binding until a `docs/policy/UPDATE_POLICY.md`
  revision is merged; the policy file itself is versioned through
  normal `CHANGELOG.md` entries.

---

## 7. Full-repo audit & refresh procedure

When the user asks for a **full-state check** ("전체 상태를 확인하고 최신으로
갱신해줘", "bring the whole repo up to date", "sync everything"), the
following seven-layer procedure MUST be executed in order. Each layer
is a strict prerequisite for the next; skipping a layer invalidates
the downstream ones.

### Layer 0 — Inventory snapshot (read-only, no edits)

Goal: establish the current state before touching anything.

1. `git status -s` and `git log -n 20 --oneline` — working-tree +
   recent history.
2. `git tag --list "Math*" --sort=-v:refname | head -20` — active
   theory tags.
3. Read the **top of** each of:
   - `CHANGELOG.md` (latest theory-tag section)
   - `docs/status/TECT-Theory-Code-Sync.md` (§1 table + §2 open
     discrepancy list + §5 last Sync Log row)
   - `docs/status/research-log.md` (last MASTER STATUS TABLE block)
   - `PDE/tect_version_manifest.py` (`THEORY_VERSION`,
     `THEORY_INVARIANTS_CLOSED`, `_OPEN`)
   - `PDE/stamp_version_headers.py` (`THEORY_VERSION`,
     `MODULE_VERSIONS`)
   - `Website/data/version_index.json` (`theory_tag` field)
   - `Website/data/timeline.json` (most recent `entries[0]`)
4. Record the snapshot date (today's YYYY-MM-DD) as `AUDIT_DATE`.

### Layer 1 — Theory layer (source of all downstream truth)

Order within the layer:

1. **`docs/math/`** — every `TECT-Math<NN>.tex.txt` that has changed
   since the previous Sync Log row. For each: check whether a closure
   marker (`\textbf{Proved (YYYY-MM-DD).}`) was added or an open
   conjecture was resolved.
2. **`docs/papers/`** — every `.tex` that has changed. Check paper
   status (`IN PREPARATION / FRAMEWORK WRITTEN / PROP X COMPLETE /
   SUBMITTED / PUBLISHED`).
3. **`docs/supplementary/`** — PDE-Blueprint or related.
4. Classify the delta: (a) no change → skip to Layer 2; (b) new claim
   / status transition → record it for Layer 3 propagation; (c) new
   theory tag warranted → flag for Layer 6.

### Layer 2 — Code layer

Order within the layer:

1. **`PDE/*.py` live-core modules** — scan headers for `Module
   version: vN.M` lines. Cross-check against
   `PDE/stamp_version_headers.py::MODULE_VERSIONS`. Any mismatch is a
   stamper-drift bug; fix by editing the dict and running
   `python PDE/stamp_version_headers.py`.
2. **`PDE/config_template_*.json`** — confirm the Brazovskii template
   defaults match the `THEORY_INVARIANTS_CLOSED` locked triple.
3. **`PDE/deprecated/`** — no live imports into this directory.
   Verify with `grep -rn "from deprecated" PDE/` (must return empty).
4. **AST / import smoke-test** on the live-core set:
   `python -c "import ast; [ast.parse(open(f).read()) for f in <live modules>]"`
5. **Regime banner check**: run the solver in dry-run mode or inspect
   the `_regime` block in `tect_solver_pt_v3.py`; confirm defaults
   match the active theory tag's regime.

### Layer 3 — Sync manifest layer

Update `docs/status/TECT-Theory-Code-Sync.md`:

1. §1 table — every row whose implementation reference changed in
   Layer 2 gets its `Primary code locus` column updated (file + line
   range). Status column updated per Layer 1 findings.
2. §2 discrepancy list — any discrepancy resolved in Layer 1 or
   Layer 2 gets a `**[CLOSED YYYY-MM-DD]**` marker + resolution
   paragraph + legacy text preserved. Any new discrepancy discovered
   during Layer 0–2 is added here with status `⚠ GAP`.
3. §4 active-codebase inventory — reconciled against Layer 2 scan.
4. §5 Sync Log — one row appended, describing the audit delta.
   Format: `| AUDIT_DATE | <prev tag> (unchanged) or <prev> → <new> | <delta summary> |`.

### Layer 4 — Registry + data-artefact layer

1. **`PDE/tect_version_manifest.py`** — `THEORY_VERSION`,
   `THEORY_INVARIANTS_CLOSED`, `_OPEN` reconciled against the updated
   sync manifest.
2. **`PDE/stamp_version_headers.py`** — `THEORY_VERSION` bumped if a
   new theory tag was minted. Run the stamper.
3. **`Website/data/version_index.json`** — regenerate via
   `python tools/build_version_index.py`. Then run
   `python tools/build_version_index.py --check` (must exit 0).
4. **`Website/data/timeline.json`** — if a new theory tag was minted,
   prepend a new entry to `entries[]`. Otherwise the audit is a
   no-op at this layer.

### Layer 5 — Changelog layer

1. **`CHANGELOG.md`** — if any substantive change occurred in Layers
   1–4, either append to the current theory-tag section (minor) or
   create a new top-level section (major / new theory tag).
2. **`docs/status/research-log.md`** — one-line append describing
   the audit, even for no-op audits (empty rows are still audit trail).

### Layer 6 — Website layer

Order within the layer:

1. **Headline pages** — `Website/index.html`, `Website/theory.html`:
   theory-tag banner + locked invariants table.
2. **Content pages** — `Website/code.html`, `Website/results.html`,
   `Website/math-notes.html`, `Website/math/index.html`,
   `Website/math/project-*.html`, `Website/papers.html`: status
   tags, tables, anything referencing a claim updated in Layer 3.
3. **Log pages** — `Website/changelog.html`, `Website/timeline.html`:
   one new block per Layer 5 entry.
4. **Every page touched in this layer** — footer
   `<p class="timestamp">Last updated: AUDIT_DATE</p>` updated.
   If a page was not content-edited, its timestamp stays at its
   previous value (do not mass-bump timestamps on no-op pages —
   timestamps must reflect real edits).

### Layer 7 — Git-tag + close-out layer

1. If a new theory tag was minted:
   `git tag -a <theory_tag> -m "<one-line summary>"` per
   `docs/policy/GIT_TAG_POLICY.md`.
2. Commit all changes in **one logical commit per layer** (or a
   single atomic commit if the audit is small). Never amend a pushed
   tag commit.
3. Produce a **final audit report** citing:
   - Every target updated (grouped by layer).
   - Every target skipped, with justification.
   - Every gate (AST / version-index `--check` / link check /
     regime banner) passed or failed.

### Layer dependencies (enforcement)

```
Layer 0  (snapshot)
   ↓
Layer 1  (docs/math, docs/papers)
   ↓
Layer 2  (PDE/*.py, config templates)
   ↓
Layer 3  (Sync manifest §1/§2/§4/§5)
   ↓
Layer 4  (manifest py + stamper + version_index + timeline.json)
   ↓
Layer 5  (CHANGELOG.md + research-log.md)
   ↓
Layer 6  (Website/* + per-page timestamps)
   ↓
Layer 7  (git tag + final audit report)
```

**Never update Layer N before Layer N-1 is confirmed consistent.**
If a later layer exposes an inconsistency in an earlier layer,
return to that earlier layer and re-audit — do not patch only the
downstream manifestation.

### No-miss checklist (AI collaborator must run before returning)

```
[ ] Layer 0: snapshot recorded (git state + top-of-file reads).
[ ] Layer 1: docs/math + docs/papers audited; deltas classified.
[ ] Layer 2: MODULE_VERSIONS ↔ headers consistent; stamper run if
    dict changed; AST smoke-test passed; regime banner defaults
    match theory tag.
[ ] Layer 3: Sync manifest §1/§2/§4 updated; §5 row appended with
    AUDIT_DATE.
[ ] Layer 4: tect_version_manifest.py + stamp_version_headers.py
    THEORY_VERSION reconciled; version_index.json regenerated;
    --check passed; timeline.json entry added iff new theory tag.
[ ] Layer 5: CHANGELOG.md entry added iff substantive delta;
    research-log.md one-line append.
[ ] Layer 6: Website headline / content / log pages updated;
    per-page footer timestamp bumped ONLY for pages actually edited
    in this audit.
[ ] Layer 7: git tag created iff new theory tag; final audit report
    enumerates updates + skips + gate results.
```

A full-state refresh is **not complete** until every box above is
ticked, explicitly, in the AI collaborator's return message.

---

## 9. Failure / negative-result discipline

Success is logged in `CHANGELOG.md`, `docs/status/research-log.md`,
`Website/changelog.html`, `Website/timeline.html`. Failure is logged
in **`docs/status/NEGATIVE-RESULTS.md`**, which is append-only and
never redacted.

### 9.1 When an entry is required

An entry in `docs/status/NEGATIVE-RESULTS.md` MUST be opened when any
of the following occur. The entry is written in the same commit that
supersedes the failure.

| Event | Entry type | Tag format |
|---|---|---|
| A theoretical claim is disproved or corrected by a later derivation | `F` — failed hypothesis | `F-<YYYY-MM-DD>-<seq>` |
| A numerical result is withdrawn or invalidated (bug, regime mismatch, provenance audit) | `R` — retracted result | `R-<YYYY-MM-DD>-<seq>` |
| An approach, convention, or coding pattern is abandoned as structurally defective | `D` — dead-end approach | `D-<YYYY-MM-DD>-<seq>` |

### 9.2 Required fields

Every entry must carry: **Original claim / context**, **Evidence of
failure**, **Root cause**, **Superseded by** (theory tag, code
version, or replacement entry), and where applicable **Archive
location** (deprecated file path, backup config directory, retracted
run directory). A one-line **Lesson preserved** is strongly
recommended for `D` entries.

### 9.3 Append-only rule

No entry is ever edited in place. If new evidence reopens an item, a
new entry is appended that cites the reopened entry by tag. The
original stays intact for audit.

### 9.4 Propagation

- **`CHANGELOG.md`**: for any theory tag that produces a failure
  entry, that tag's section gains a `### Retracted / dead-end`
  subsection enumerating the tags and linking to
  `docs/status/NEGATIVE-RESULTS.md`.
- **`docs/status/TECT-Theory-Code-Sync.md`**: if the failure closes
  a discrepancy, the §2 resolution paragraph cites the negative-
  result tag; the legacy text block already preserves the failed
  statement.
- **`PDE/` archives**: retracted runs, deprecated modules, or
  archived config sets (e.g. `backup_GL_2026-04-15/`) retain their
  physical artefacts; the negative-result entry points to them.
- **Website**: failure provenance is *not* surfaced on public-
  facing editorial pages by default (public pages carry final, proved
  statements). If a failure narrative is published (e.g. in a paper's
  errata section), the public text must link back to this ledger.

### 9.5 Audit integration

Layer 5 of the §7 full-repo audit procedure is extended: if Layer 1
or Layer 2 reveals a retracted claim / invalidated result / abandoned
approach that is not yet recorded, an entry in
`docs/status/NEGATIVE-RESULTS.md` MUST be opened **before** Layer 5
changelog updates are considered complete. The final audit report
must enumerate any negative-result tags created during the audit.

The `§7 no-miss checklist` line for Layer 5 is now:

```
[ ] Layer 5: CHANGELOG.md entry added iff substantive delta;
    research-log.md one-line append; NEGATIVE-RESULTS.md entry
    added for every F/R/D event discovered during this audit,
    with Retracted/dead-end subsection back-linked from the
    current theory-tag CHANGELOG section.
```

---

## 10. Records completeness & queryability

Three sister ledgers plus an index guarantee that every claim has a
traceable trail and every reviewer question has a single
entry-point.

### 10.1 The four-ledger model

| File | Records | Append-only? |
|---|---|---|
| `CHANGELOG.md` + `docs/status/research-log.md` + `Website/data/timeline.json` | Proved claims / released code / milestones | Yes |
| `docs/status/NEGATIVE-RESULTS.md` | Failed hypotheses (F), retracted results (R), dead-end approaches (D) | Yes (per §9) |
| `docs/status/OPEN-QUESTIONS.md` | Active open conjectures / numerical frontiers (Q-) | Active + Archive sections |
| `docs/status/EVIDENCE-INDEX.md` | Claim → evidence map (no original claims) | Live index (rows added; rot fixes allowed) |

An item moves Q → CHANGELOG upon proof, or Q → NEGATIVE-RESULTS
upon disproof. The `EVIDENCE-INDEX.md` is kept current with every
new locked invariant, retraction, or closure.

### 10.2 When to touch each ledger (additions to §1)

| Event | New targets (on top of §1) |
|---|---|
| A new open conjecture is stated in a Math-note | Append `Q-<YYYY-MM-DD>-<seq>` to `OPEN-QUESTIONS.md` under `## Active`. |
| An open conjecture is proved | Append to `CHANGELOG.md` under active theory tag; move the `Q-` entry to `## Archive` with the successor theory-tag cite; add/update a row in `EVIDENCE-INDEX.md` §1 or §2. |
| An open conjecture is disproved | Open a `F-` entry in `NEGATIVE-RESULTS.md`; move the `Q-` entry to `## Archive` citing the `F-` tag; update `EVIDENCE-INDEX.md` if the claim had a pre-existing row. |
| A new locked invariant is produced | New row in `EVIDENCE-INDEX.md` §2 with primary evidence + correction history; if it replaces an old value, the old value gains a cross-link to the relevant `F-` entry. |
| A code file is moved/renamed/demoted | Update every row in `EVIDENCE-INDEX.md` that cites the old path (no stale paths allowed). |

### 10.3 Records cutoff (replaces retroactive-manifest plan)

The formal start of the TECT record system is **2026-04-15**. All
artefacts dated before this cutoff are treated as pre-cutoff
historical material: archived for audit, **not cited as evidence**
in any paper, website page, or theory statement. Canonical doctrine
is `PDE/RECORDS_CUTOFF.md`.

No retroactive manifests are written. The earlier plan
(`PDE/RETRO_MANIFEST_NOTE.md`, proposing
`schema_version: "1.0-retro"`) is withdrawn; the stub file is
preserved as a marker under the append-only rule.

Pre-cutoff material may still be used for forensic analysis,
pedagogy (when a pre-cutoff failure is recorded in
`NEGATIVE-RESULTS.md`), or as motivation for a post-cutoff
derivation — but the post-cutoff derivation is the evidence, never
the pre-cutoff artefact.

### 10.3a Review cadence (drift prevention)

To prevent silent staleness of the Open / Index ledgers, the
following cadences apply:

| Ledger | Rows / entries | Cadence |
|---|---|---|
| `OPEN-QUESTIONS.md` | `## Active` entries | 30 days default; entries requiring longer windows must justify the window in the entry itself (60-day / 90-day supported) |
| `EVIDENCE-INDEX.md` | §1–§3 rows (foundational claims / locked invariants / code design choices) | 60 days |
| `EVIDENCE-INDEX.md` | §4–§6 rows (infrastructure & reviewer quick-links) | exempt — structural |
| `NEGATIVE-RESULTS.md` | all entries | exempt — append-only historical |
| `CHANGELOG.md` / `research-log.md` | all entries | exempt — append-only historical |
| Website per-page footer timestamps | all pages | updated only on real content edits — do NOT mass-bump on audit |

**Enforcement**: the `§7 full-repo audit` Layer 3 is extended to
scan `Last reviewed` fields across OPEN-QUESTIONS and
EVIDENCE-INDEX; any entry past its cadence window is marked
**overdue** in the audit report. Overdue entries do not close
automatically but become priority work items.

### 10.3b Single entry point — `docs/status/INDEX.md`

`docs/status/INDEX.md` is the canonical single entry point to the
entire record system. All other ledgers link back to it; it links
to them. An external reviewer or the AI collaborator may start
here and reach any record within two clicks.

### 10.4 Audit Layer 5 extension

The §7 no-miss checklist Layer 5 line becomes:

```
[ ] Layer 5: CHANGELOG.md entry added iff substantive delta;
    research-log.md one-line append; NEGATIVE-RESULTS.md entry
    added for every F/R/D event discovered during this audit;
    OPEN-QUESTIONS.md entries added/moved for every new / proved
    / disproved open conjecture; EVIDENCE-INDEX.md rows added or
    repaired for every new locked invariant, retraction, or path
    change.
```

### 10.5 Queryability contract

At any point, the AI collaborator (or any reviewer following the
index) must be able to answer the following seven question types
by consulting at most three files:

1. **"Why this value / sign / regime?"** → `EVIDENCE-INDEX.md` row → primary evidence file.
2. **"Has this ever been retracted or disproved?"** → `NEGATIVE-RESULTS.md` search.
3. **"What is currently open / unproven?"** → `OPEN-QUESTIONS.md` §Active + Sync Manifest §2.
4. **"Provenance of this run / result?"** → run dir's `tect_version_manifest.json` + `RESULT.md`; pre-2026-04-15 runs fall under `PDE/RETRO_MANIFEST_NOTE.md`.
5. **"Which code version implements which claim?"** → Sync Manifest §1.
6. **"When and why did this change?"** → `CHANGELOG.md` + Sync Manifest §5 Sync Log.
7. **"Where does the old file live now?"** → `CHANGELOG.md` Math39-Reorg entry + `git log --follow`.

Failure to satisfy the contract on any of the seven is a policy
violation and must be repaired in the next commit.

---

## 11. Manuscript authorship doctrine

Papers, articles, and externally-published prose are the one class of
artefact where automation is *intentionally disabled*. The reasoning:

1. **Prose commits claims in durable form.** Once a sentence is
   written in a paper and published, it is quoted, cited, and held
   against the theory. A mis-phrased statement ("we prove" where we
   have only "we conjecture") is not correctable by a later
   changelog entry.
2. **The AI lacks the editorial signal.** Ledger updates can be
   automated because each target has a rule-governed, schema-valid
   form. Prose cannot — emphasis, pacing, and rhetorical framing are
   user judgement.
3. **Separation of concerns.** Automation handles state tracking
   (what is true, what failed, what is open). Manual authorship
   handles narrative (how we say it in public).

### 11.1 Scope
The manual-only rule applies to:
- `docs/papers/*.tex` and `docs/papers/**/*.tex`.
- `docs/papers/supplementary/**/*` prose files.
- Any future `Website/blog/`, `Website/press/`, or equivalent
  externally-styled prose.
- Any document Claude or another assistant is asked to produce that
  is styled as "paper", "manuscript", "abstract", "blog post",
  "press release", "article".

The rule does NOT apply to:
- Math notes (`docs/math/*.tex.txt`) — these are internal working
  notes and are permitted under §1.1.
- Changelog / sync manifest / research-log / negative-results /
  open-questions / evidence-index prose. These are schema-bound and
  automatable under §1.
- Website editorial pages (`theory.html`, `code.html`, `results.html`,
  `math-notes.html`, `records.html`, etc.) — these are derivative
  summaries of already-committed claims and are permitted under §1.4.
- Docstring / comment edits in `PDE/*.py`.

### 11.2 Required user instruction form
To unblock paper-prose authorship, the user's instruction must be
explicit, at minimum naming either (i) the paper or section by
identifier, or (ii) a specific paragraph / figure caption / equation
environment to be drafted. Vague instructions ("update the paper",
"make it sound better") must be refused with a request for
specificity.

### 11.3 Forbidden auto-behaviours
Even when a closure (§3) or theory-tag bump (§1.1) occurs, the AI:
- MUST NOT add a new `\section`, `\subsection`, paragraph, or
  equation to a paper `.tex` file.
- MUST NOT reword an existing sentence in a paper `.tex` file.
- MUST NOT produce a standalone draft titled "Paper N Section X"
  unless explicitly instructed.
- MAY flag in the return message: "Paper III §II currently cites
  m*=0.3138; after R-2026-04-15-01, this sentence needs manual
  revision." This is a *flag*, not an edit.

### 11.4 Enforcement
Violations of §11 are tracked as `D-` (dead-end / discipline)
entries in `NEGATIVE-RESULTS.md` — the pattern "AI silently edited
paper prose" is itself a recorded mistake to avoid.

### 11.5 Papers catalogue admission rule (binding from 2026-04-28)

The `Website/data/papers.js` index — which serves as the public
"Papers (complete proof catalogue)" page — is governed by a
strict ADMISSION RULE that complements the manual-authorship rule
above:

**Admission criteria.** A research item (Math note, derivation,
result, claim) may be listed in `papers.js` if AND ONLY IF it has
cleared **all three** of:

  (i)   its CLAUDE.md §6.3 devil's-advocate self-test;
  (ii)  any reviewer audit dispatched against it (with VALID/UPHELD
        objections resolved or with status downgraded to honest scope);
  (iii) any cross-turn §6.3.2 second-order audit affecting it.

**Forbidden inclusions.** The following content classes MUST NOT
appear in `papers.js`:

  - In-progress proofs / OUTLINE-status notes whose §6.3 self-test
    has not been performed.
  - AUDIT-FLAGGED notes (any note carrying an `AUDIT-STATUS BANNER`).
  - FALSIFIED claims (notes whose central theorem has been disproved).
  - Conjectural research programmes (status `CONJECTURAL` or
    `PARTIAL` with significant residual hypothesis weight).
  - Status downgrades pending in NEGATIVE-RESULTS.md.

**Promotion / retraction discipline.** When a research item
PROMOTES from in-progress / audit-flagged → fully verified, it is
admitted to the catalogue in the SAME atomic-write commit that
records the promotion (per §3 atomic-write rule + §15 chat-archival).
Conversely, if a previously-admitted item is RETRACTED by a later
audit, it is REMOVED from the catalogue and migrated to
`NEGATIVE-RESULTS.md` in the same commit. The catalogue therefore
presents a SNAPSHOT of currently-validated TECT research, with full
audit traceability via `EVIDENCE-INDEX.md` and `NEGATIVE-RESULTS.md`.

**Scope of the rule.** Applies to:
  - `Website/data/papers.js` — the seventeen pillar-grade papers,
    auxiliary entries, top-impact verified-proof table, and
    chronological catalogue cards.
  - Any future Papers-page derivatives.

Does NOT apply to:
  - `Docs/status/EVIDENCE-INDEX.md` — that is a navigation index of
    ALL claims (verified, conditional, retracted alike) with explicit
    status flags.
  - `Docs/status/NEGATIVE-RESULTS.md` — that is the dedicated home of
    retracted / audit-flagged content.
  - `Docs/status/OPEN-QUESTIONS.md` — active work tracking.
  - Math notes themselves (each carries its own status banner and is
    preserved as a permanent historical record).

**Honest-scope companion (§6.1) requirement.** When a status
downgrade fires, the PROMOTION audit-trail in `EVIDENCE-INDEX.md`
must record the demotion in the same commit as the `papers.js`
removal; the demotion-side entry in `NEGATIVE-RESULTS.md` must
include explicit (cause, evidence/failure log, decision chain) per
§9. This guarantees that no claim ever silently disappears from
the public Papers catalogue.

**Examples of correct application** (post-Math209, 2026-04-28):

  - The Math202-205 cluster ATTEMPTED to establish flat-Cartan
    forcing for Pillar 4 sub-task 2. Math208 audit-flagged Math203/
    204/205. Math209 confirmed Math203 c_1=0 conclusion FALSIFIED.
    Result: these notes are NOT listed in `papers.js`; they are
    instead recorded in `NEGATIVE-RESULTS.md` (R-2026-04-28-Math209-
    Math203-c1-Forcing-Falsified). The Pillar 4 paper (Paper 4) in
    `papers.js` cites the post-R8 baseline (Math162+Math167 +
    Math191/192 canonical realisation), NOT the Math202-205 cluster.

  - Math200 main note + Math200-AddA y_t portion + Math200-AddB ℏ_B
    portion are AUDIT-FLAGGED. Result: NOT listed in `papers.js`
    catalogue. Math200-AddA's g_1 sign correction (the verified part)
    + Math200-AddB's proxy-paradigm-void main conclusion (the verified
    part) ARE listed. Mixed-status notes are split at the paragraph
    level, with audit-flagged parts excluded.

  - Math202 v1.1 cleared the reviewer's three minor revisions.
    Result: LISTED in `papers.js` Top-impact verified proofs (#10).

### 11.6 Enforcement of §11.5

Violations of §11.5 (e.g., listing an audit-flagged note in
`papers.js` without resolving its conditional, or failing to remove
a retracted note) are tracked as `D-` (dead-end / discipline)
entries in `NEGATIVE-RESULTS.md`. The 2026-04-28 reviewer audit's
identification of the over-optimistic Math202-207 inclusion in the
roadmap is the canonical exemplar of the failure mode this rule
prevents.

---

## 12. Automation tooling

The records system is only as good as its ability to detect drift.
This section enumerates the automated tools that enforce the policy
without requiring per-commit human review.

### 12.1 `tools/build_version_index.py`
Regenerates `Website/data/version_index.json` from
`PDE/tect_version_manifest.py`. The `--check` flag exits non-zero if
regeneration would change the file (i.e. the committed index is
stale). Gate: §4 acceptance gates, §7 audit Layer 4.

### 12.2 `tools/check_review_cadence.py` (added 2026-04-15)
Scans `Last reviewed` / `Review by` date fields in:
- `docs/status/OPEN-QUESTIONS.md` `## Active` section
- `docs/status/EVIDENCE-INDEX.md` §1, §2, §3 rows (60-day cadence
  per §10.3a)

Computes days-overdue against today's date; prints a report grouped
by ledger and severity (UPCOMING ≤ 7 days, OVERDUE > 0 days past
`Review by`). The `--check` flag exits non-zero if any entry is
overdue, intended for use in §7 audit Layer 3 and pre-commit
validation. The tool is stdlib-only (no third-party dependencies)
and treats missing fields as policy violations.

### 12.3 `PDE/stamp_version_headers.py`
Re-stamps `__version__` / `__theory_version__` headers across all
live `PDE/*.py` files from `MODULE_VERSIONS` + `THEORY_VERSION`.
Gate: §2 ordering rule step 3; §1.1 and §1.2 require re-run on any
triggered change.

### 12.4 Invocation from §7 audit
The §7 Layer 3 audit procedure is extended to invoke
`tools/check_review_cadence.py --check` and surface its report in
the no-miss checklist. A non-zero exit code is treated as a policy
deviation that must be explained (overdue entries either reviewed
during the audit, or flagged as priority work with a justification).

### 12.5 Tool ownership rule
Every automation tool listed here must be:
- Stdlib-only where possible (no build-time dependency bloat).
- Documented in its own module docstring.
- Invokable both as a library (`import` + function call) and as a
  CLI (`python -m tools.<name>` or `python tools/<name>.py`).
- Referenced from `docs/status/INDEX.md` under the "Automation"
  subsection.

---

## 13. Code manual discipline

**Binding from**: 2026-04-16.
**Canonical file**: `docs/manual/CODE_MANUAL.md`.

Every Python module under `PDE/` (and any future `tools/` module
exposed to the operator) MUST have a user-manual entry in
`docs/manual/CODE_MANUAL.md`. In-file docstrings remain the low-level
reference; the manual is the operator-level reference that the human
maintainer and the AI collaborator consult first.

### 13.1 Mandatory schema per module

```
### filename.py  (vX.Y)  [ACTIVE|UTILITY|DIAGNOSTIC|SUPERSEDED|EXPERIMENTAL]
- Purpose     : one-sentence physics / compute goal.
- Inputs      : files and/or CLI args.
- Outputs     : files and/or return values.
- CLI         : minimal copy-pasteable invocation.
- Dependencies: upstream reads / downstream callers.
- Math note   : TECT-Math<NN> mapping.
```

### 13.2 Trigger → target rules (additive to §1)

| Trigger | Required targets (same commit) |
|---|---|
| New module added to `PDE/` | Manual entry in correct section + `MODULE_VERSIONS` bump + `version_index.json` + `CHANGELOG.md` |
| Existing module version bumped | Manual entry updated (version + any changed CLI / outputs) + `MODULE_VERSIONS` + `version_index.json` + `CHANGELOG.md` |
| CLI flag added / removed / renamed | Manual CLI line updated + any quick-start workflow that uses it |
| Module retired / replaced | Status flipped to `[SUPERSEDED]`, replacement named, kept in manual (never deleted) |

### 13.3 Acceptance gate

A commit that touches `PDE/*.py` or `tools/*.py` without a corresponding
`docs/manual/CODE_MANUAL.md` edit fails the §4 acceptance gate and MUST
NOT be tagged. `run_audit_pipeline.py` and any future orchestrators
are also subject to this rule because they are user-facing entry points.

### 13.4 Quick-start workflows

`CODE_MANUAL.md §1` hosts the operator quick-start invocations.
Whenever a new user-facing orchestrator or a workflow-critical change
lands, a quick-start block MUST be added or updated there in the same commit.

### 13.5 AI directive

The AI collaborator must:
1. Before editing or creating any `PDE/*.py`, open `CODE_MANUAL.md` and
   identify the entry to be updated.
2. In the same response that modifies code, write the manual entry edit.
3. Refuse to advance to the next task until the manual reflects the change.

---

## 14. Session Resumption Protocol (SRP-v1)

**Binding from**: 2026-04-24.
**Purpose**: Prevent the cross-session status drift that produced the
2026-04-24 audit-rollback (`R-2026-04-24-RoundOverclaim`). New sessions
must start from the canonical mainline, not from in-memory recollection
of a previous session.

### 14.1 Mandatory read-only prelude

Every new TECT session MUST execute the following reads, in this exact
order, before any computation, math note edit, or code change:

1. `Docs/status/INDEX.md`                          — entry-point ledger map
2. `Docs/status/TOE-FACT-SHEET.md`                  — canonical 11-pillar status (binding)
3. `Docs/status/research-log.md` (last entry)       — most recent live result
4. `CHANGELOG.md` (top entry)                       — last theory tag
5. `Docs/status/OPEN-QUESTIONS.md` (Active section) — what is currently open
6. `Docs/status/NEGATIVE-RESULTS.md` (top entry)    — what has been retracted
7. `Docs/policy/UPDATE_POLICY.md` §1–§7             — trigger → target rulebook

### 14.2 SRP status line

After the prelude, the session emits exactly one Korean status line of
the form:

```
[SRP-OK] Pillars n_PROVED/n_COND/n_PARTIAL/n_OPEN  Last theory tag: <Math NN-…>.
```

Counts are taken directly from the `TOE-FACT-SHEET.md` Stage-1 scorecard.
This single line is the contract that the session has read the canonical
state and is operating from it.

### 14.3 Canonical-source hierarchy (binding)

A pillar-status claim in a higher-tier document never overrides the
corresponding pillar-level theorem note:

$$
\boxed{\text{pillar-level theorem note} \;\succ\; \text{round summary} \;\succ\; \text{global synthesis draft.}}
$$

If a higher tier is ahead of a pillar-level theorem note, that is a
synchronization defect, not a status upgrade. The acceptance gate is
the pillar-level note.

### 14.4 Atomic-write rule

Every accepted result writes simultaneously to:

1. the pillar-level theorem note (or a new one),
2. `CHANGELOG.md` (one entry per theory tag),
3. `Docs/status/TOE-FACT-SHEET.md` (status row),
4. `Docs/status/EVIDENCE-INDEX.md` (claim → evidence row),
5. a single `git commit` stamping all of the above.

A partial write is a §4 acceptance-gate failure and must be rolled back
in the next commit.

### 14.5 Round-summary discipline

A "round summary" (e.g.\ Math78-RESEARCH-SESSION-SUMMARY style) MAY be
emitted at the end of a multi-result session, but its pillar-status
claims MUST NOT precede the corresponding pillar-level theorem-note
edits. If a round summary is produced before any theorem-note write,
its status claims default to "AS YET UNVERIFIED, audit pending" and the
TOE-FACT-SHEET MUST NOT be updated from it directly.

### 14.6 AI directive

The AI collaborator must:
1. Execute §14.1 before any computation in a new session.
2. Emit the §14.2 status line as the first paragraph of the first
   non-trivial response.
3. When a higher-tier document conflicts with a pillar-level theorem
   note, treat the higher tier as defective and trigger a
   synchronization commit, not a status upgrade.
4. Refuse to declare a pillar promotion (`SCAFFOLD → PROVED`,
   `PARTIAL → FULL CLOSURE`, etc.) without simultaneously executing the
   §14.4 atomic-write rule.

---

## 15. Chat-content auto-archival rule

**Binding from**: 2026-04-24.
**Purpose**: prevent the leak diagnosed in user feedback 2026-04-24:
substantive LaTeX blocks shown in chat without being archived to a
canonical Math note. The chat is a transient view; only the on-disk
note is the canonical record.

### 15.1 Trigger

Any of the following in an AI response constitutes a §15 trigger:

- A LaTeX `\section` / `\subsection` / `\boxed{}` / theorem / lemma /
  proposition block.
- A multi-line derivation, proof sketch, or strategy framework.
- A status verdict (PROVED / FAILED / RETRACTED / etc.) on a pillar
  or sub-task.
- A numerical-extraction result with $\rho$, $\chi$, $\delta$, or
  ratio values.
- A diagnosis of a code or process defect with proposed mitigations.
- A "honest scope statement" or "binding boxed conclusion".

### 15.2 Required action

For each §15 trigger, the AI MUST in the same response:

1. Identify the appropriate archive target per §4.1 of `CLAUDE.md`.
2. Write the content to that target (new Math note, addendum, or
   ledger entry — never chat-only).
3. Reference the on-disk archive path in chat with a `computer://`
   link.
4. Include the archive write in the same git commit as the response
   (atomic-write rule §14.4).

### 15.3 Theory-tag numbering

The Math-note sequence is monotonic. The current next-available tag
is recorded in the latest commit of `CHANGELOG.md`. AI collaborators
MUST verify the current next-tag before creating a new Math note to
avoid collisions.

### 15.4 Retroactive archival

If a previous session left chat-only content un-archived, the next
session begins by retroactively archiving that content as
`Docs/math/TECT-MathNN-Session-<YYYY-MM-DD>-<topic>-decisions.tex.txt`.
This is a §4 acceptance-gate item; new substantive work cannot begin
until the retroactive archival is committed.

### 15.5 What this rule explicitly forbids

- Producing a `\boxed{}` or theorem-style LaTeX in chat without
  writing it to a Math note.
- Producing a "next-step recommendation" or strategy framework as a
  chat-only block.
- Producing audit verdicts as chat-only content; they MUST land in
  `NEGATIVE-RESULTS.md` AND a Math-note addendum.
- Relying on the user to copy-paste paste-ready content into a file.

### 15.6 What this rule explicitly allows

- Brief Korean conversational summaries (§5 of `CLAUDE.md`).
- One-line status updates and decision-point questions to the user.
- Inline math in conversational paragraphs (e.g., $\hbar$, $q_0$,
  $\rho_\Lambda$) used for natural-language reference, not as theorem
  statements.
- Pre-implementation strategy discussion that does not yet have a
  fixed conclusion.

### 15.7 The session-end audit

At the end of each substantive session, the AI must verify:

1. Every `\boxed{}` displayed in chat is on disk.
2. Every
