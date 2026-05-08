# Repository Restructure Roadmap (v2 — post-Math353-AddB closure)

**Status**: v2 binding from 2026-05-08 (Math353 + Math353-AddA + Math353-AddB)
**Maintainer**: Jusang Lee (`jtkor@outlook.com`)
**Governed by**: `CLAUDE.md` §13 (file-location discipline), `Docs/policy/REPO_LAYOUT.md` (canonical destination matrix), `STATUS_PROPAGATION_POLICY.md` (Phase A foundation), `MATH_NOTE_AND_PAPER_DISCIPLINE.md`.

This v2 supersedes the 2026-05-07 v1 lowercase-rename plan. The mirror-first design (Math353) replaced the local-rename approach: local tree retains `Codes/`, `Docs/`, `Runs/`, `Website/` naming; rename + content-path-rewrite happens at the `github_sync_curate.py` mirror boundary.

---

## §1. Phase A — COMPLETE (2026-05-07, Math352)

| Item | Artefact | Status |
|---|---|---|
| Status propagation policy | `Docs/policy/STATUS_PROPAGATION_POLICY.md` | binding |
| Math-note + paper discipline policy | `Docs/policy/MATH_NOTE_AND_PAPER_DISCIPLINE.md` | binding |
| `states.js` → `status.js` rename + redirect | site-wide | binding |
| `propagate_status.py` v1.0 | `Codes/tools/propagate_status.py` | working; idempotent |
| `paper_status_impact.py` v1.0 | `Codes/tools/paper_status_impact.py` | working |
| `paper_need_assessment.py` v1.0 | `Codes/tools/paper_need_assessment.py` | working |
| `status_history_tracker.py` v1.0 | `Codes/tools/status_history_tracker.py` | working |
| Externalised target list | `Codes/config/status_propagation_targets.json` | active |
| Snapshot pipeline integration | `Codes/scripts/snapshot.ps1` step 2.5b/c/d | wired |
| `verify_website.py` patch | sidecar + deprecation-stub recognition | applied |
| Audit log | `Docs/status/propagation-log.md` | active |
| Auto report | `Docs/status/paper-impact-report.md` | active |

---

## §2. Phase B-revised — COMPLETE/IN-FLIGHT/DEFERRED

### §2.1 Mirror-first plan (Math353 design, ACCEPTED 2026-05-07)

Per Math353 design principles:
1. Local single source of truth (`Codes/`, `Docs/`, `Runs/`, `Website/`) — zero local rename.
2. Single mapping table (`Codes/config/mirror.json` v2).
3. Idempotent mirror via `v0_compat_disable_renames` Boolean toggle.
4. Path rewriting at the publish boundary; `.md`/`.tex.txt`/`.js`/`.html` whitelist; `.py` excluded.
5. GitHub Pages serves `Github/site/` only.

The original lowercase-rename plan (v1 §2.1/§2.2/§2.3) is SUPERSEDED-BY-Math353 and retired. `Codes/scripts/migrate_to_lowercase_code.py` retired with header banner.

### §2.2 Phase B-revised work breakdown (Math353-AddA + AddB)

| Step | Description | Status |
|---|---|---|
| B-α | `mirror.json` v2 schema | DONE 2026-05-07 (Math353 ACCEPTED) |
| B-β | `github_sync_curate.py` v2 framework (additive, default v0 behaviour) | DONE 2026-05-07 |
| B-γ | dry-run validation (golden-file diff) | DONE 2026-05-07 (preview log: `Docs/status/mirror-rewrite-preview.log`) |
| B-ι | Snapshot pipeline self-fixes (CMD limit, UTF-8 BOM, LF, mount-translation, auto-config bootstrap, multi-source remote, PS-version safety) | DONE 2026-05-08 (Math353-AddA r1–r7) |
| B-κ | Root orphan cleanup: TECT_*.png → `Website/assets/branding/`; `/Backup/`, `/outputs/`, `/code/` gitignored; `site.js` PNG references rewritten | DONE 2026-05-08 (Math353-AddB) |
| B-λ | `Codes/pde/*.old.*.py` retire (operator-side `git rm` per PowerShell handoff) | OPERATOR-ACTION 2026-05-08 (banner + handoff list provided) |
| B-μ | `mirror.json::exclude_from_mirror.active_v1_0` activated with 3 internal-ops policy files | DONE 2026-05-08 (Math353-AddB) |
| B-η | `migrate_to_lowercase_code.py` removal | OPERATOR-ACTION (sandbox unable to delete; rm command provided) |
| B-ζ | Root `site/` v0 scaffold removal | OPERATOR-ACTION (sandbox unable to delete; rmdir command provided) |
| B-θ | This v2 ROADMAP rewrite | DONE 2026-05-08 (Math353-AddB; this file) |
| B-ε | `verify_website.py` v1.1 path-resolution check (rewritten paths resolve in mirror tree) | DEFERRED to dedicated session |
| B-δ | Cutover trial (`v0_compat_disable_renames: false`, full snapshot validation) | DEFERRED to dedicated session |

### §2.3 Cutover gate (B-δ, DEFERRED)

Flipping `mirror.json::v0_compat_disable_renames` to `false` requires:
1. Operator review of `Docs/status/mirror-rewrite-preview.log` (2,635 files, 5,526 rewrites already previewed in Math353-AddA r0).
2. One full snapshot pass with `v0_compat=true` retained (production-grade idempotency confirmation).
3. Explicit operator authorisation in chat.
4. B-ε `verify_website.py` v1.1 extension landed first (defensive: ensures rewritten paths actually resolve).

Until B-δ ships, the public mirror surface is unchanged from v1.

---

## §3. Phase C-revised — IN-FLIGHT/OPERATOR-ACTION

| Step | Description | Status |
|---|---|---|
| C-α | GitHub Pages activation (Settings → Pages → folder=`Github/site/` post-cutover, OR root `Github/` pre-cutover) | OPERATOR-ACTION (web UI; deferred per operator directive 2026-05-08 to a later session) |
| C-β | `Github/README.md` auto-generated by `github_sync_curate.py::render_readme()` from canonical sources every snapshot. Operator only edits canonical sources (TOE-FACT-SHEET, Math notes, CHANGELOG); template change requires `render_readme()` edit (CLAUDE.md §9 still applies to template-edit prose). Original Math353-AddA "operator authors" framing CORRECTED 2026-05-08 (Math353-AddC). | AUTO-MANAGED |
| C-γ | BCC narrative softening sweep via `sweep_rules.json` rules; apply to `Website/data/_narrative/*.md` and HTML | DEFERRED to dedicated session |
| C-δ | GitHub metadata (description + topics + homepage) auto-synced by `github_sync_push.py::cmd_meta()` invoked at snapshot step 7/8 (`publish.ps1 step 5/5`). Operator PAT must carry `Metadata:RW` + `Administration:W` (fine-grained) or `repo` (classic) scope. CORRECTED 2026-05-08 (Math353-AddC). | AUTO-MANAGED |
| C-ε | Per-page provenance footer (`Mirrored from Contents/Website/<source>; canonical: <git-sha>`) auto-emitted by `generate_website.py` | DEFERRED to dedicated session |

---

## §4. Operator handoff — sandbox-restricted operations

The 2026-05-08 Math353-AddB session was unable to perform the following operations from the sandbox (NTFS mount permission). The operator must execute these on Windows PowerShell:

### §4.1 File deletions

```powershell
# Phase B-λ: retire superseded Codes/pde files
git tag -a code-v2.6.6-continuation-mu2 HEAD -m "Archive: continuation_mu2_v25.old.v2.6.6.py before retirement (Math353-AddB B-λ 2026-05-08)"
git rm Codes/pde/continuation_mu2_v25.old.v2.6.6.py

git tag -a code-v24-thresholds HEAD -m "Archive: v24_thresholds.py before retirement (Math353-AddB B-λ 2026-05-08)"
git rm Codes/pde/v24_thresholds.py

# Phase B-η: remove migrate_to_lowercase_code.py (banner already inserted)
git tag -a migrate-to-lowercase-code-v1.1 HEAD -m "Archive: migrate_to_lowercase_code.py v1.1 before final removal (Math353-AddB B-η 2026-05-08; SUPERSEDED-BY-Math353 mirror-first plan)"
git rm Codes/scripts/migrate_to_lowercase_code.py

# Phase B-ζ: remove root site/ v0 scaffold (Github/site/ is the canonical post-cutover serve root)
git rm site/.nojekyll site/README.md
Remove-Item -Recurse -Force site
```

### §4.2 Snapshot

After the above deletions:

```powershell
# Atomic commit of B-λ + B-η + B-ζ deletions plus AddB working-tree state
git add -A
git -c user.email="jtkor@outlook.com" -c user.name="Jusang Lee" commit -m "Math353-AddB: Phase B-κ root orphan cleanup (TECT_*.png → branding/; /Backup,/outputs,/code gitignored) + B-λ git-tag retire of Codes/pde superseded files + B-η migrate_to_lowercase_code.py final removal + B-ζ root site/ scaffold removal + B-μ mirror.json exclude active_v1_0 activation + B-θ REPO_RESTRUCTURE_ROADMAP.md v2 rewrite"

# Snapshot (using r7 patches: -Token + -RemoteUrl no longer needed since github_sync_config.json now exists)
.\Codes\scripts\snapshot.ps1 -Token "<your-PAT>" -Message "Math353-AddB: Phase B inventory cleanup + ROADMAP v2 + Phase C handoff"
```

### §4.3 Phase C operator-only items

| Item | Action |
|---|---|
| C-α | Open `https://github.com/TECT-OpenPhysics/TECT/settings/pages`. Set Source: "Deploy from a branch" → Branch: `main` → Folder: `/` (pre-cutover) or `/Github/site/` (post-B-δ). Save. |
| C-β | Author root `README.md` per Math353-AddA §"C-β scope" 7-section specification. AI cannot pre-draft this prose (CLAUDE.md §9). |
| C-δ | Open `https://github.com/TECT-OpenPhysics/TECT` repo → Edit description + topics. Suggested: description `"Topological Energy Condensate Theory (TECT): a candidate Theory of Everything built on a two-axiom Brazovskii-universality foundation"`; topics `theory-of-everything, physics, brazovskii, topological-condensate, gauge-theory, general-relativity, lattice-gauge-theory, peer-reviewable-pre-print`. |

---

## §5. Cross-references

- `CLAUDE.md` §13 — file-location discipline
- `Docs/policy/REPO_LAYOUT.md` — canonical destination matrix
- `Docs/policy/STATUS_PROPAGATION_POLICY.md` — Phase A foundation
- `Docs/policy/MATH_NOTE_AND_PAPER_DISCIPLINE.md` — paper-impact + new-paper rules
- `Docs/policy/SNAPSHOT_POLICY.md` — 8-step snapshot orchestrator policy
- `Docs/math/TECT-Math353-Mirror-First-Restructure-Strategy-Framework.tex.txt` — design framework
- `Docs/math/TECT-Math353-AddA-Snapshot-v2.1-Fix-and-Phase-B-C-Inventory.tex.txt` — pipeline self-fix r1–r7 + inventory
- `Docs/math/TECT-Math353-AddB-Phase-B-Implementation-Report.tex.txt` — this round's implementation report
- `Codes/config/mirror.json` — v2 schema, v0_compat toggle, exclude_from_mirror.active_v1_0 (Math353-AddB B-μ activated)
- `Codes/config/sweep_rules.json` — C-γ narrative-softening rules (v0 scaffold)

End of REPO_RESTRUCTURE_ROADMAP.md v2 (binding from 2026-05-08).
