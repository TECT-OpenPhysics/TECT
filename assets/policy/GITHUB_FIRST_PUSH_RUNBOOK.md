# GitHub-mediated tect.kr deployment — operator runbook

**Status**: BINDING from 2026-04-29
**Maintainer**: Jusang Lee (`jtkor@outlook.com`)
**Companion**: `Docs/policy/GITHUB_SYNC_POLICY.md`

This runbook is the canonical step-by-step that the operator follows
to push the curated `Github/` mirror to
`https://github.com/TECT-OpenPhysics/TECT` and to deploy that mirror
onto `tect.kr` via the cPanel Terminal of `hostingkr.com`. It
supersedes the ad-hoc command sequences scattered in chat after the
2026-04-29 GitHub-organisation handover.

The pipeline is a pure pull-model on the cPanel side. cPanel never
acts as the source of truth; it only `git pull`s from the public
GitHub repository and (optionally) rsyncs into `~/public_html/`.

---

## Section 1. Prerequisites (one-time)

1. Local Windows machine has `git` (Windows port) and `python` on
   `PATH`. Verify in PowerShell:
       git --version
       python --version
2. The public GitHub repository
   `https://github.com/TECT-OpenPhysics/TECT` exists and is empty
   (no commits yet) OR has only an initial README that the first
   push will overwrite.
3. A fine-grained GitHub Personal Access Token with `Contents:
   read & write` permission on the `TECT-OpenPhysics/TECT` repo.
   The token is held ONLY in the PowerShell environment, NEVER
   committed to disk inside the repository or pasted to chat.
4. `Codes/tools/github_sync_config.json` exists (gitignored) with
       "github_username":  "TECT-OpenPhysics"
       "github_repo":      "TECT"
       "remote_url":       "https://github.com/TECT-OpenPhysics/TECT.git"
       "auth.method":      "https-token"
       "auth.token_env_var": "GITHUB_TOKEN"
       "publish_branch":   "main"
       "dry_run_default":  true
5. cPanel Terminal access at hostingkr.com is available (the user
   has confirmed inbound SSH/FTP is blocked by the host but the
   in-cPanel Terminal works).

---

## Section 2. Layer-1 curate (offline, idempotent)

Run from Windows PowerShell:

    cd C:\Dev\TECT2\Contents
    python -u Codes\tools\verify_website.py
    python -u Codes\tools\github_sync_curate.py

Acceptance gates:
- `verify_website.py`: `errors: 0` (warnings tolerable; address
  before publication-grade citation).
- `github_sync_curate.py`: ends with line `OK: Github/ is in sync
  with Website/ (Layer-1 contract satisfied).`

The `Github/` working tree is now ready for Layer-2.

---

## Section 3. Layer-2 first push (network)

The token-URL injection in `cmd_push` (since 2026-04-29 commit
`8c4bda5...`) keeps the token out of `Github/.git/config`. The
token is read from `$env:GITHUB_TOKEN`, spliced into a one-shot
remote URL of the form `https://x-access-token:${TOKEN}@github.com/
TECT-OpenPhysics/TECT.git`, passed as a positional argument to
`git push`, and never echoed to stdout (the masked form is
displayed instead).

PowerShell sequence (single session, token alive only for this
shell):

    cd C:\Dev\TECT2\Contents

    # Set the token in the current session ONLY. Do NOT persist.
    $env:GITHUB_TOKEN = "<paste your fine-grained PAT here>"

    # 1) Status — no network, sanity check.
    python -u Codes\tools\github_sync_push.py status

    # 2) Initialise Github\.git and set the (token-free) https remote.
    python -u Codes\tools\github_sync_push.py init

    # 3) Commit the curated tree as a single initial public commit.
    python -u Codes\tools\github_sync_push.py commit --apply

    # 4) Push to origin/main using the token-URL splice.
    python -u Codes\tools\github_sync_push.py push --apply

    # 5) Drop the token from the shell.
    Remove-Item Env:\GITHUB_TOKEN

Expected output of step 4 ends with:
    OK: pushed to origin/main

The repository at `https://github.com/TECT-OpenPhysics/TECT` now
has its first commit visible publicly under the CC BY 4.0 licence.

---

## Section 4. cPanel side (initial clone + tect.kr wiring)

In cPanel Terminal (hostingkr.com session):

    # Pick a working location OUTSIDE the document root.
    cd ~
    git clone https://github.com/TECT-OpenPhysics/TECT.git tectweb
    cd tectweb
    git log --oneline -3

The `~/tectweb/` directory now mirrors the GitHub repository.
Two deployment options to surface it under `tect.kr`:

### 4.A. Symlink (preferred when cPanel allows symlinks)

    # Back up any existing public_html/tect.kr first.
    mv ~/public_html/tect.kr ~/public_html/tect.kr.bak.$(date +%Y%m%d)

    # Replace the document root with a symlink to the git working tree.
    ln -s ~/tectweb ~/public_html/tect.kr

    # Verify Apache follows symlinks.
    ls -ld ~/public_html/tect.kr

If symlinks are disallowed, use rsync (4.B).

### 4.B. rsync into the document root (universal)

    rsync -av --delete --exclude='.git' \
        ~/tectweb/ ~/public_html/tect.kr/

    # Sanity check.
    head -1 ~/public_html/tect.kr/index.html

After either 4.A or 4.B, browsing `https://tect.kr/` should serve
`index.html` from the mirror.

---

## Section 5. Refresh cycle (after every Layer-1+2 publish)

Local Windows PowerShell:

    cd C:\Dev\TECT2\Contents
    python -u Codes\tools\verify_website.py
    python -u Codes\tools\github_sync_curate.py
    $env:GITHUB_TOKEN = "<token>"
    python -u Codes\tools\github_sync_push.py commit --apply
    python -u Codes\tools\github_sync_push.py push --apply
    Remove-Item Env:\GITHUB_TOKEN

cPanel Terminal:

    cd ~/tectweb && git pull --ff-only

    # If 4.B rsync mode (skip if 4.A symlink mode is used).
    rsync -av --delete --exclude='.git' \
        ~/tectweb/ ~/public_html/tect.kr/

---

## Section 6. Optional cron automation on cPanel

If the operator wants `tect.kr` to auto-refresh every N minutes
without manual intervention, add a cPanel Cron Job:

    Frequency: */15 * * * *   (every 15 min — adjust as needed)
    Command  : cd ~/tectweb && /usr/bin/git pull --ff-only --quiet \
               && rsync -a --delete --exclude='.git' \
                  ~/tectweb/ ~/public_html/tect.kr/

For symlink mode (Section 4.A), drop the rsync clause; only
`git pull` is needed.

Acceptance: after operator pushes a new commit on the local side
the cron-driven `git pull` reflects it on `tect.kr` within the
cron interval.

---

## Section 7. Failure-mode quick reference

| Failure | Likely cause | Resolution |
|---|---|---|
| `push` exits with `403` and `Permission denied` | PAT lacks `Contents: write` on `TECT-OpenPhysics/TECT` | Regenerate PAT with correct resource owner = `TECT-OpenPhysics`, scope `Contents: read & write`. |
| `push` exits with `auth.method = https-token but $GITHUB_TOKEN is not set` | Env var not set in current PowerShell shell | `$env:GITHUB_TOKEN = "..."` before the push subcommand. |
| `push` exits with `https-token auth requires remote_url to start with https://` | Config still has `git@github.com:...` SSH URL | Edit `github_sync_config.json` `remote_url` to the `https://` form. |
| cPanel `git clone` reports `Could not resolve host: github.com` | Outbound DNS blocked | Use the cPanel-provided git proxy (rare) or change to https with explicit IP fallback. |
| `tect.kr` serves an old version after `git pull` | Browser cache or rsync skipped | Hard-refresh; verify rsync line was actually executed; check Apache `ExpiresActive` in `.htaccess`. |
| Commit message in chat references token | Token leaked in operator message | Revoke the token in GitHub settings IMMEDIATELY; generate a new one; never paste in chat or in tracked files. |

---

## Section 8. Cross-references

- `Docs/policy/GITHUB_SYNC_POLICY.md` — full Layer-1+2 architecture.
- `Codes/tools/github_sync_curate.py` — Layer-1 source of truth.
- `Codes/tools/github_sync_push.py` — Layer-2 source of truth.
- `Codes/tools/templates/LICENSE-CC-BY-4.0.txt` — verbatim CC BY 4.0
  legal code (downloaded once, hand-edit forbidden).
- `CLAUDE.md` s5.1 — output-language policy (English-only for tracked
  artefacts; the public mirror inherits the rule).
