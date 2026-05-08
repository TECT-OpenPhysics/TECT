# SNAPSHOT_POLICY.md — TECT Repository Snapshot Discipline

**Binding from**: 2026-05-01
**Theory tag**: Math294-AddA-Snapshot-Discipline-2026-05-01
**Maintainer**: Jusang Lee (jtkor@outlook.com)
**Cross-references**: `CLAUDE.md` §3, §6.3.7, §13, §15.4 + `Docs/policy/UPDATE_POLICY.md` §10–§13 + `Docs/policy/WEBSITE_AUTO_SYNC.md` + `Docs/policy/GITHUB_SYNC_POLICY.md`

---

## 1. Motivation

TECT keeps four parallel mirror trees of every artefact:

| Tree | Role | Source-of-truth? |
|---|---|---|
| `Docs/`, `Codes/`, `CHANGELOG.md`, `Runs/` | Canonical source | YES |
| `Website/data/*.js`, `Website/data/_narrative/*.md`, `Website/*.html` | Public-site auto-generated content | NO (regenerated from canonical) |
| `Website/assets/math/`, `Website/assets/code/`, `Website/assets/runs/` | Public-site downloadable mirrors | NO (copied from canonical) |
| `Github/` | Public GitHub mirror (separate repo) | NO (curated from `Website/` + `Docs/` + `CHANGELOG.md`) |

A *snapshot* is the operation that brings all four trees into a coherent, mutually-consistent state at a single point in time. Without a defined snapshot discipline, the four trees drift, producing the documented failure modes catalogued in `POSTMORTEM_RECURRENCE_POLICY.md` (empty Results page, broken download links, stale manifest counts).

This policy makes snapshot a **single explicit operator action** with a fixed pipeline, fixed exit-code contract, and an audit-traceable record.

---

## 2. Definition of a snapshot

A snapshot is the atomic execution of the eight-step pipeline below. The snapshot is *complete* iff all eight steps return exit-code zero.

```
[1/8]  stamp     -> Codes/pde/stamp_version_headers.py
[2/8]  generate  -> Codes/tools/generate_website.py --all
[3/8]  verify    -> Codes/tools/verify_website.py
[4/8]  manifest  -> Codes/tools/generate_website.py --regenerate-manifest
[5/8]  commit    -> Codes/scripts/sandbox_commit.sh "<message>" <files...>
[6/8]  curate    -> Codes/tools/github_sync_curate.py        (optional --skip-github)
[7/8]  push      -> Codes/scripts/publish.ps1 -CredentialName tect-github  (optional --skip-github)
[8/8]  audit     -> Codes/tools/check_review_cadence.py + summary print
```

Steps 1–5 operate on the **canonical-and-Website** tier (always required). Steps 6–7 operate on the **GitHub-mirror** tier (optional via `-SkipGitHub` flag for local-only snapshots; required before any external publication or external claim about the public mirror).

---

## 3. When to snapshot

A snapshot MUST be executed in the following situations:

| Trigger | Rationale |
|---|---|
| End of any session that produced one or more new Math notes | §3 atomic-write rule extension to mirror trees |
| End of any session that modified `Codes/pde/*`, `Codes/tools/*`, `Codes/scripts/*`, or `Codes/supplementary/*` | Code change must propagate to Website mirror for download links |
| Before any external claim about the GitHub repository state | GitHub mirror must reflect the local canonical state |
| Before any tagged release (`Math<NN>` theory tag promoted to a git annotated tag) | Tag should pin a coherent snapshot, not a drifting state |
| At the request of the operator via the trigger phrases of §6 | Manual checkpoint |

A snapshot SHOULD be executed (but is not strictly required) in the following situations:

| Suggestion | Rationale |
|---|---|
| End of every working day | Daily checkpoint of progress |
| After every successful F-Pillar6 / F-GAP1 / F-GAP4 numerical run | Numerical result should be reflected in Website |
| Before a multi-turn autonomous agent dispatch | Clean baseline so the agent's work is auditable from a known state |

---

## 4. Atomic-commit-extension rule (binding extension of CLAUDE.md §3)

The §3 atomic-write rule of `CLAUDE.md` requires every accepted result to write simultaneously to (a) the pillar-level Math note, (b) `CHANGELOG.md`, (c) `Docs/status/TOE-FACT-SHEET.md`, (d) `Docs/status/EVIDENCE-INDEX.md`, and (e) a single git commit. This snapshot policy **extends** the atomic-write requirement to include the four mirror trees:

> Every accepted result MUST eventually flow through the snapshot pipeline so that all four mirror trees converge to a coherent state. The within-session §3 atomic-write covers the canonical tier only; the snapshot pipeline covers the Website + GitHub tiers.

A session is considered to be in **snapshot debt** if it produced canonical changes (Math notes, code edits, status row updates) but has not subsequently executed the snapshot pipeline. Snapshot debt accumulates across sessions and must be retired before any external claim about the public mirror.

---

## 5. The orchestrator script

**Path**: `Codes/scripts/snapshot.ps1`

**Single-line invocation** (full pipeline including GitHub; requires token):
```powershell
.\Codes\scripts\snapshot.ps1 -Message "<one-line snapshot summary>"
```

**Local-only invocation** (skip steps 6–7, **no GitHub token required**):
```powershell
.\Codes\scripts\snapshot.ps1 -Message "<...>" -SkipGitHub
```

**Dry-run** (print what would happen, execute nothing):
```powershell
.\Codes\scripts\snapshot.ps1 -Message "<...>" -DryRun
```

**Force-add specific files** (when sandbox_commit.sh's auto-discovery misses something):
```powershell
.\Codes\scripts\snapshot.ps1 -Message "<...>" -ExtraFiles @("path1", "path2")
```

### 5.1 GitHub authentication

When the full pipeline (steps 6–7) is requested, the orchestrator must locate a GitHub fine-grained PAT. Three resolution paths in priority order:

| Priority | Source | Operator action | Lifetime |
|---|---|---|---|
| 1 | Inline `-Token` parameter | Pass `-Token "<PAT>"` on each invocation | one-shot, never persisted |
| 2 | Windows Credential Manager (default name `tect-github`) | One-time setup: `cmdkey /generic:tect-github /user:<USERNAME> /pass:<PAT>` | until revoked / re-registered |
| 3 | Custom credential name | Pass `-CredentialName <name>` and pre-register it | until revoked |

**The orchestrator pre-flight (step 0) checks for at least one available authentication source** before any work happens. If none is available AND `-SkipGitHub` is not set, the orchestrator aborts at exit code 90 with explicit operator guidance:
```
FAIL [precondition]: GitHub publish requested but no token available.
  Options:
    (a) Re-run with -SkipGitHub for a local-only snapshot.
    (b) Pass token inline: .\snapshot.ps1 -Message "..." -Token "<PAT>"
    (c) Register credential once: cmdkey /generic:tect-github /user:<USERNAME> /pass:<PAT>
```

### 5.2 No-token path

A snapshot with `-SkipGitHub` runs steps 1–5 + 8 (skips curate at step 6 AND push at step 7). This is a fully valid snapshot under this policy: it brings the canonical and Website tiers into a coherent state, atomic-commits to the local git repo, and leaves the GitHub mirror untouched. When the operator later acquires/configures a token, a follow-up `snapshot.ps1` invocation **without** `-SkipGitHub` will catch up the GitHub mirror with whatever local state has accumulated.

**Snapshot debt distinction**: a `-SkipGitHub` snapshot retires the *local* snapshot debt (canonical → Website → local commit) but leaves *GitHub publish debt* outstanding. The next full snapshot retires both.

The script is `param`-driven, with `[CmdletBinding()]` attributes for tab-completion. It mirrors the design pattern of the existing `Codes/scripts/publish.ps1` (which it consumes in step 7).

**Exit-code contract**:

| Code | Meaning |
|---|---|
| 0 | All requested steps PASS |
| 10 | Step 1 (stamp) failed |
| 20 | Step 2 (generate) failed |
| 30 | Step 3 (verify) failed |
| 40 | Step 4 (manifest) failed |
| 50 | Step 5 (commit) failed |
| 60 | Step 6 (curate) failed |
| 70 | Step 7 (push) failed |
| 80 | Step 8 (audit) failed (warnings only; no rollback) |
| 90 | Pre-condition failed (no -Message, dirty state, etc.) |
| 99 | Generic failure (uncaught exception) |

---

## 6. Trigger phrases for AI collaborator

When the operator types one of the following phrases (Korean conversational layer), the AI collaborator MUST recognise it as a snapshot request and execute the §5 orchestrator. The AI MUST NOT silently fall through to per-file edits.

**Full snapshot (canonical + Website + GitHub)**:
- "스냅샷 진행해" / "스냅샷 진행" / "스냅샷"
- "현재 상태 스냅샷"
- "전체 업데이트" (when followed by no specific target)
- "publish snapshot" / "publish snapshot now"

**Local-only snapshot (canonical + Website, no GitHub)**:
- "로컬 스냅샷"
- "스냅샷 (로컬만)" / "스냅샷 로컬만"
- "local snapshot"

**Dry-run**:
- "스냅샷 dry-run" / "스냅샷 미리보기"
- "snapshot dry-run"

After recognising the trigger, the AI:
1. Confirms the exact `-Message` to be used (operator may supply explicit message; otherwise propose one based on session changes).
2. Issues the corresponding PowerShell invocation as a code block for the operator to execute.
3. Awaits the snapshot script output before declaring the session complete.
4. On any non-zero exit code, helps the operator diagnose and fix the failed step before re-running.
5. On success, emits the §7 closing summary and (if requested) returns to mainline work.

---

## 7. Snapshot closing summary (binding format)

Every successful snapshot MUST be followed by an AI-generated closing summary in the conversational layer:

```
[SNAPSHOT-OK] <YYYY-MM-DDThh:mm:ss>
- Steps PASSED: 1/8 stamp, 2/8 generate, 3/8 verify, 4/8 manifest,
  5/8 commit (commit hash <abbrev>), 6/8 curate, 7/8 push (remote <commit>),
  8/8 audit (warnings: <N>)
- Files in commit: <count>
- Math notes added/modified: <list>
- Code modules touched: <list>
- Status row deltas: <none|...>
- GitHub commit URL: <url> (if pushed)
- Next mainline step: <one-line>
```

The closing summary is also written to `Docs/status/snapshot-log.md` (append-only) by the snapshot script itself; the AI summary in chat is a courtesy display.

---

## 8. Failure handling

| Step | Failure mode | Recovery |
|---|---|---|
| 1 stamp | version-stamp inconsistency | manually edit version header; retry |
| 2 generate | generator AssertionError | usually a Math-note format defect; check filename / header; retry |
| 3 verify | hard error in verify_website.py | post-mortem per `POSTMORTEM_RECURRENCE_POLICY.md` §3, then retry |
| 4 manifest | file count mismatch | re-run with `--regenerate-manifest` flag once; if still fails, debug |
| 5 commit | sandbox_commit.sh refused (forbidden pattern) | move offending file to canonical destination per REPO_LAYOUT.md §6; retry |
| 6 curate | Github mirror dirty | `git -C Github status`; resolve; retry |
| 7 push | network / credentials / 403 | check token validity, credential cache; retry |
| 8 audit | overdue review-cadence rows | non-blocking; address in next session |

A snapshot that fails at step N is considered **partially executed**. The operator MUST NOT make external claims about the snapshot's state until the failed step is resolved and a re-run reaches exit-code 0.

---

## 9. Coexistence with sandbox_commit.sh and publish.ps1

The snapshot orchestrator does NOT replace the existing per-step scripts; it consumes them. Each step is a clean delegation:

| Step | Delegated to | Lives where |
|---|---|---|
| 1 stamp | `python -u Codes/pde/stamp_version_headers.py` | `Codes/pde/stamp_version_headers.py` |
| 2 generate | `python -u Codes/tools/generate_website.py --all` | `Codes/tools/generate_website.py` |
| 3 verify | `python -u Codes/tools/verify_website.py` | `Codes/tools/verify_website.py` |
| 4 manifest | `python -u Codes/tools/generate_website.py --regenerate-manifest` | `Codes/tools/generate_website.py` |
| 5 commit | `bash Codes/scripts/sandbox_commit.sh "<msg>" <files...>` | `Codes/scripts/sandbox_commit.sh` |
| 6 curate | `python -u Codes/tools/github_sync_curate.py` | `Codes/tools/github_sync_curate.py` |
| 7 push | `Codes/scripts/publish.ps1 -CredentialName tect-github` | `Codes/scripts/publish.ps1` |
| 8 audit | `python -u Codes/tools/check_review_cadence.py` | `Codes/tools/check_review_cadence.py` |

This means the operator can still invoke any sub-step manually for diagnosis; the orchestrator is a convenience for the common case.

---

## 10. Per-step idempotency

Every step in the pipeline is idempotent:
- Re-running with no source changes produces no diff.
- Re-running after a partial failure produces the correct state.
- Re-running on a fully-snapshotted state is a no-op (still exits 0).

This means a snapshot can be safely re-attempted without risk of double-applying.

---

## 11. Snapshot vs. theory-tag promotion

A snapshot is a *coherent state checkpoint*. A theory-tag promotion is a *named milestone*. The two are independent:

- A snapshot may be taken at any time; theory tags are promoted only when a Math note advances tier.
- Every theory-tag promotion SHOULD be followed by a snapshot (to ensure the public mirror reflects the new tag).
- A snapshot may be taken without any theory-tag change (e.g., after wrapper bug-fixes that do not change tier).

The `CHANGELOG.md` records both: theory-tag promotions become explicit `[Theory] Math<NN>` entries, snapshots are implicit (recorded in `Docs/status/snapshot-log.md`).

---

## 12. Snapshot-log file (binding from 2026-05-01)

**Path**: `Docs/status/snapshot-log.md` (append-only)

**Format per entry**:
```
## YYYY-MM-DDThh:mm:ss UTC — <commit-hash-abbrev> — <message>
- Steps: 1/8 stamp ✓, 2/8 generate ✓, ..., 8/8 audit ✓ (warnings: N)
- Files in commit: <count>
- Math notes added/modified: <list>
- GitHub commit URL: <url>
- Operator: <name@email>
```

The snapshot orchestrator writes this entry on successful completion. On partial failure, it writes a separate entry tagged `[PARTIAL]` documenting which step failed and at what timestamp.

---

## 13. Migration notes (2026-05-01)

This policy is binding from 2026-05-01. The retroactive snapshot for the Math290–296 + Math294-AddA + v2.6.7c/d code changes of 2026-05-01 is the inaugural snapshot under this policy.

Pre-2026-05-01 sessions did not follow this discipline; the four mirror trees may carry historical drift. The first invocation of `snapshot.ps1` will surface and resolve any such drift via the verify_website.py + curate steps. Operators should not be alarmed if the first snapshot produces a larger-than-usual commit; this is the migration commit.

---

**End of SNAPSHOT_POLICY.md.**
