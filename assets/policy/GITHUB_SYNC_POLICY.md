# GitHub-publish Sync Policy

**Binding from**: 2026-04-29
**Maintainer**: Jusang Lee (`jtkor@outlook.com`)
**Cross-references**: `CLAUDE.md` §5.1 (Output-language policy), `Docs/policy/OUTPUT_LANGUAGE_POLICY.md`, `Codes/tools/github_sync_curate.py`, `Codes/tools/github_sync_push.py`, `Codes/tools/github_sync_config.template.json`.

---

## §1. Why this policy exists

The canonical TECT repository at `C:\Dev\TECT2\Contents\` is the single source of truth for theory, code, numerical runs, and policy. A subset of that content needs to be visible on GitHub: the public website (browsable via GitHub Pages), curated Math notes, code mirrors, and policy summaries. This policy defines a two-layer pipeline that keeps publication discipline separate from authoring discipline.

The two layers are:

1. **Layer 1 — Curate (offline, deterministic)**. `Codes/tools/github_sync_curate.py` reads `Website/` (and a small set of other canonical sources) and writes a self-contained mirror into `Github/`. No network. No git. Deterministic and idempotent.
2. **Layer 2 — Push (network, credentialed)**. `Codes/tools/github_sync_push.py` takes the curated `Github/` working tree, manages git state inside it, and pushes to a remote public repository. Requires `Codes/tools/github_sync_config.json` (gitignored).

The two layers are decoupled so that:

- Curation can be tested locally without any GitHub account (current state of the project).
- Credentials and network calls are isolated to Layer 2; a curate-layer bug cannot leak credentials.
- Each layer has a single responsibility, so failures are easy to diagnose.

## §2. The `Github/` folder contract

The `Github/` folder at the root of the canonical repository is the working tree of a *separate*, public GitHub repository. It is **gitignored from the main repo** (see `.gitignore`) so the two repositories' git state does not collide.

Layout produced by `github_sync_curate.py`:

| Path | Type | Generator |
|---|---|---|
| `Github/README.md` | auto-generated | `render_readme()` |
| `Github/CITATION.cff` | auto-generated | `render_citation_cff()` |
| `Github/LICENSE` | placeholder, hand-editable | `render_license_placeholder()` (only on first run; subsequent runs leave it alone) |
| `Github/.gitignore` | auto-generated | `render_gitignore_for_target()` |
| `Github/.nojekyll` | auto-generated empty file | `render_nojekyll()` (instructs GitHub Pages to skip Jekyll so `data/_archive/` etc. are served verbatim) |
| `Github/docs/KEY_RESULTS.md` | auto-generated | `render_key_results()` |
| `Github/docs/NAVIGATION.md` | auto-generated | `render_navigation()` |
| `Github/docs/POLICIES_INDEX.md` | auto-generated | `render_policies_index()` |
| `Github/{index,theory,states,papers,toe,results,history,records,math-notes,code,code-old,history-page-002..007,history-archive-index}.html` | verbatim copy | `copy_website_tree()` |
| `Github/data/**` | verbatim copy of `Website/data/` | `copy_website_tree()` |
| `Github/assets/**` | verbatim copy of `Website/assets/` | `copy_website_tree()` |

Auto-generated files carry an explicit sentinel header (`<!-- AUTO-GENERATED -->` for markdown, `# AUTO-GENERATED` for YAML / `.cff`). Hand-editing them is supported but the next curate run will overwrite the changes.

Files NOT generated and NOT touched by `curate`:

- Anything inside `Github/.git/` — owned exclusively by Layer 2.
- `Github/LICENSE` after first creation — once you commit to a license, the curate step won't disturb it.

## §3. Workflow

Operator workflow once everything is configured:

```bash
# 0. Update canonical website state
python -u Codes/tools/generate_website.py --all

# 1. Verify (CLAUDE.md §6.3.7 mandatory)
python -u Codes/tools/verify_website.py

# 2. Curate (Layer 1)
python -u Codes/tools/github_sync_curate.py            # idempotent rebuild
# Optional flags:
#   --check     : dry-run; print deltas only
#   --clean     : wipe Github/ (preserving .git/) before rebuilding
#   -v          : list per-file additions/modifications/removals

# 3. Push (Layer 2)
# First time:
python -u Codes/tools/github_sync_push.py status      # confirm config + tree
python -u Codes/tools/github_sync_push.py init --apply
python -u Codes/tools/github_sync_push.py commit --apply
python -u Codes/tools/github_sync_push.py push --apply

# Subsequent runs (after edits to canonical repo):
python -u Codes/tools/github_sync_push.py sync --apply
```

The `sync` subcommand chains `status -> commit -> push`. Without `--apply` (and with `dry_run_default: true` in config), every step is non-destructive.

## §4. Credentials

`Codes/tools/github_sync_config.json` is the only file the push layer reads for credentials. It is **gitignored** from the canonical repo.

Setup:

```bash
cp Codes/tools/github_sync_config.template.json Codes/tools/github_sync_config.json
# Edit github_sync_config.json:
#   - github_username, github_repo, remote_url
#   - auth.method  ("ssh" recommended; "https-token" requires a PAT)
#   - commit_author.name + email
```

Authentication methods:

- **`ssh`** (recommended): operator has set up an SSH key with GitHub. The remote URL is `git@github.com:USERNAME/REPO.git`. No tokens stored anywhere.
- **`https-token`**: operator has a Personal Access Token (PAT) in environment variable `GITHUB_TOKEN` (or whatever `auth.token_env_var` says). The push layer never prints the token; git's credential helper reads it from the environment.
- **`none`**: no authentication configured. Push layer refuses to network, but other subcommands still work (status, init).

## §5. Safety gates

The push layer enforces several guard rails:

| Gate | Default | How to bypass | Purpose |
|---|---|---|---|
| `dry_run_default` | `true` | pass `--apply` to a subcommand, OR set `dry_run_default: false` in config | Prevent accidental write/network on first runs. |
| `force_push` | `false` | both `force_push: true` in config AND `--force-confirm` flag AND `--force-push` flag | Prevent destruction of remote history. We use `--force-with-lease`, never plain `--force`. |
| Credentials masking | always on | (cannot be disabled) | Status output and stderr are passed through `_mask_token()`; tokens look like `ghp_****`. |
| `Github/.git` invariant | always preserved | (cannot be bypassed by curate) | Curate never touches `.git/`. Push layer is the sole owner. |
| English-only | enforced via verifier | `verify_website.py --korean-strict` | The website tier is English-only by `Docs/policy/OUTPUT_LANGUAGE_POLICY.md`; since `Github/` is a copy of `Website/` the same constraint holds. |

## §6. What goes into the public mirror — and what does not

**Included** (publicly readable):

- The entire `Website/` tree (HTML pages + data + assets including all Math notes, code mirror, manifest).
- A curated `README.md`, `CITATION.cff`, and `docs/{KEY_RESULTS,NAVIGATION,POLICIES_INDEX}.md`.
- A placeholder `LICENSE` until the maintainer decides on a final license.

**Excluded** (canonical repo only):

- `Runs/` — raw numerical run output (some runs are 50+ GB; the public site already exposes their summary cards via `data/results.js` + `assets/runs/<run_id>/MANIFEST.md`).
- `Docs/postmortem/` — internal incident reports.
- `Docs/status/round-summaries/.round*/` — internal round-summary archives.
- `Codes/tools/github_sync_config.json` — credentials.
- `Github/` itself in the canonical repo's git state (excluded via `.gitignore`).

If a piece of content needs to move from the "excluded" column to "included," the curate step adds an explicit copy rule, NOT a wholesale `Docs/`-tree mirror. We curate; we do not dump.

## §7. Failure modes and recovery

| Failure | Recovery |
|---|---|
| Curate produces malformed `README.md` | The `README.md` includes a sentinel; rerun curate after fixing the generator. |
| `Github/` gets out of sync with `Website/` | Run `github_sync_curate.py --clean` to wipe and rebuild. |
| `github_sync_config.json` accidentally committed to canonical repo | `git rm --cached Codes/tools/github_sync_config.json` + rotate the leaked credentials. The `.gitignore` line should prevent this; if it slipped through, treat as a security incident. |
| Push fails with auth error | Re-check `auth.method` and the corresponding environment variable / SSH key. Run `git ls-remote $remote_url` manually inside `Github/` to test. |
| Force-push gate triggered accidentally | Drop `--force-push` from CLI; if a real history rewrite is needed, set `force_push: true` in config + pass both `--force-push --force-confirm`. |
| Curate step hangs or crashes | Always safe — curate makes no destructive changes outside `Github/`. Worst case: `rm -rf Github/` and rerun. |

## §8. When to run

The curate step SHOULD run after every commit that touches:

- `Website/` (any subtree)
- `Codes/tools/generate_website.py` or `verify_website.py`
- `Docs/policy/` (because `POLICIES_INDEX.md` is auto-extracted)
- `CHANGELOG.md` (because `README.md` shows the top entries)

For now, this is a manual operator step — running `github_sync_curate.py` is the operator's responsibility. A future enhancement would be a git pre-push hook on the canonical repo that runs curate automatically.

## §9. Cross-references

- `Codes/tools/github_sync_curate.py` — Layer 1 implementation.
- `Codes/tools/github_sync_push.py` — Layer 2 implementation.
- `Codes/tools/github_sync_config.template.json` — credentials template (committed).
- `.gitignore` — excludes `Github/` and `github_sync_config.json` from canonical repo tracking.
- `CLAUDE.md` §5.1 — Output-language policy (English-only, applies to mirror).
- `Docs/policy/OUTPUT_LANGUAGE_POLICY.md` — full schema.
- `Docs/policy/POSTMORTEM_RECURRENCE_POLICY.md` — every leaked-credential incident must add a post-mortem.

---

End of GITHUB_SYNC_POLICY.md (binding from 2026-04-29).
