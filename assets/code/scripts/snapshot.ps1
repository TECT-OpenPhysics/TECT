# =====================================================================
# snapshot.ps1 — TECT 8-step snapshot orchestrator
#
# Single-command orchestrator that brings all four TECT mirror trees
# (Docs/Codes canonical, Website/data, Website/assets, Github/) into a
# coherent state. Binding policy: Docs/policy/SNAPSHOT_POLICY.md
# (2026-05-01).
#
# PIPELINE
# --------
#   [1/8]  stamp     -> python -u Codes/pde/stamp_version_headers.py
#   [2/8]  generate  -> python -u Codes/tools/generate_website.py --all
#   [3/8]  verify    -> python -u Codes/tools/verify_website.py
#   [4/8]  manifest  -> python -u Codes/tools/generate_website.py --regenerate-manifest
#   [5/8]  commit    -> bash Codes/scripts/sandbox_commit.sh "<msg>" <files...>
#   [6/8]  curate    -> python -u Codes/tools/github_sync_curate.py
#   [7/8]  push      -> Codes/scripts/publish.ps1 -CredentialName tect-github
#   [8/8]  audit     -> python -u Codes/tools/check_review_cadence.py + summary
#
# Steps 6-7 are skipped under -SkipGitHub.
# Step 5 uses git porcelain output to discover the file list automatically;
# operator may supply additional files via -ExtraFiles.
#
# USAGE
# -----
#   # Full pipeline (canonical + Website + GitHub)
#   .\Codes\scripts\snapshot.ps1 -Message "Math296 + v2.6.7d patch"
#
#   # Local-only (no GitHub network calls)
#   .\Codes\scripts\snapshot.ps1 -Message "..." -SkipGitHub
#
#   # Dry-run (print what would happen, execute nothing)
#   .\Codes\scripts\snapshot.ps1 -Message "..." -DryRun
#
#   # Force-add files that auto-discovery may miss
#   .\Codes\scripts\snapshot.ps1 -Message "..." `
#       -ExtraFiles @("Runs/continuation/foo/MANIFEST.md", "...")
#
#   # Override credential name for the publish step (default tect-github)
#   .\Codes\scripts\snapshot.ps1 -Message "..." -CredentialName my-pat
#
# EXIT CODES
# ----------
#   0   OK (all requested steps PASS)
#   10  step 1 stamp failed
#   20  step 2 generate failed
#   30  step 3 verify failed
#   40  step 4 manifest failed
#   50  step 5 commit failed
#   60  step 6 curate failed
#   70  step 7 push failed
#   80  step 8 audit failed (warnings only; non-fatal)
#   90  precondition failed (no -Message, dirty Github, etc.)
#   99  generic failure
#
# Author: Jusang Lee + collaboration (2026-05-01).
# Companion policy: Docs/policy/SNAPSHOT_POLICY.md
# =====================================================================

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Message,

    # GitHub authentication: prefer -CredentialName (Windows Credential
    # Manager) over -Token (inline) for security. If neither is supplied
    # AND -SkipGitHub is NOT set, the run aborts at the precondition
    # check before any work happens.
    [string]$CredentialName = "tect-github",
    [string]$Token = "",

    [string[]]$ExtraFiles = @(),

    [switch]$SkipGitHub,
    [switch]$SkipManifest,    # advanced: skip step 4 if manifest is fresh
    [switch]$DryRun,
    [switch]$AllowEmpty       # allow snapshot with zero file changes (no-op refresh)
)

$ErrorActionPreference = 'Stop'
$startTime = Get-Date

# ---------------------------------------------------------------------
# 0. Locate repository root from the script's location.
# ---------------------------------------------------------------------
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $repoRoot

if ($DryRun) { $modeLabel = 'DRY-RUN' } else { $modeLabel = 'APPLY' }
$pipelineLabel = if ($SkipGitHub) { 'LOCAL (skip-github)' } else { 'FULL (canonical + Website + GitHub)' }

Write-Host ('=' * 72) -ForegroundColor DarkCyan
Write-Host ' TECT snapshot orchestrator -- Codes\scripts\snapshot.ps1'
Write-Host (' Repo root  : ' + $repoRoot)
Write-Host (' Started    : ' + $startTime.ToString('yyyy-MM-ddTHH:mm:ss zzz'))
Write-Host (' Mode       : ' + $modeLabel)
Write-Host (' Pipeline   : ' + $pipelineLabel)
Write-Host (' Message    : ' + $Message)
if ($ExtraFiles.Count -gt 0) {
    Write-Host (' ExtraFiles : ' + ($ExtraFiles -join ', '))
}
Write-Host ('=' * 72) -ForegroundColor DarkCyan

# ---------------------------------------------------------------------
# Pre-flight: validate -Message is non-trivial.
# ---------------------------------------------------------------------
if ([string]::IsNullOrWhiteSpace($Message) -or $Message.Length -lt 5) {
    Write-Host "FAIL [precondition]: -Message must be non-empty and >=5 chars." -ForegroundColor Red
    exit 90
}

# ---------------------------------------------------------------------
# Pre-flight: if GitHub publish is requested, ensure either -Token or
# a Windows Credential Manager entry is available. This prevents the
# pipeline from running steps 1-6 only to fail at step 7 with a token
# error.
# ---------------------------------------------------------------------
if (-not $SkipGitHub) {
    $hasInlineToken = -not [string]::IsNullOrWhiteSpace($Token)
    $hasCredential = $false
    $hasEnvToken = $false

    # 2026-05-01 fix: auto-detect $env:GITHUB_TOKEN as a third
    # authentication source. If the operator pre-set the env var
    # (`$env:GITHUB_TOKEN = "ghp_..."`) we lift it into the -Token
    # parameter so publish.ps1 receives it via the canonical path.
    # This eliminates the need for the operator to choose between
    # inline -Token and pre-set env var (the env var path is the
    # standard GitHub CLI convention).
    if (-not $hasInlineToken) {
        if (-not [string]::IsNullOrWhiteSpace($env:GITHUB_TOKEN)) {
            $Token = $env:GITHUB_TOKEN
            $hasInlineToken = $true
            $hasEnvToken = $true
            Write-Host '[preflight] $env:GITHUB_TOKEN detected; promoted to -Token' -ForegroundColor DarkGray
        }
    }

    if (-not $hasInlineToken) {
        # Best-effort check: does Get-StoredCredential find the named entry?
        if (Get-Command Get-StoredCredential -ErrorAction SilentlyContinue) {
            try {
                $cred = Get-StoredCredential -Target $CredentialName -ErrorAction Stop
                if ($null -ne $cred) { $hasCredential = $true }
            } catch {}
        } else {
            # Fall back to cmdkey listing (works even without the
            # CredentialManager PowerShell module). We probe by attempting
            # the lookup and inspecting the output for the credential's
            # `Target:` line, which is locale-independent.
            $cmdOut = & cmdkey /list:$CredentialName 2>&1
            if ($LASTEXITCODE -eq 0 -and ($cmdOut -join "`n") -match "Target:.*$CredentialName") {
                $hasCredential = $true
            }
        }
    }
    if (-not ($hasInlineToken -or $hasCredential)) {
        Write-Host "FAIL [precondition]: GitHub publish requested but no token available." -ForegroundColor Red
        Write-Host "  config target  : github_sync_config.json -> remote_url" -ForegroundColor DarkGray
        Write-Host "  expected       : a GitHub PAT for TECT-OpenPhysics/TECT (Contents:RW)" -ForegroundColor DarkGray
        Write-Host "  Options:" -ForegroundColor Yellow
        Write-Host "    (a) Re-run with -SkipGitHub for a local-only snapshot." -ForegroundColor Yellow
        Write-Host "    (b) Pass token inline: .\snapshot.ps1 -Message ""..."" -Token ""<PAT>""" -ForegroundColor Yellow
        Write-Host ("    (c) Set env var: " + '$env:GITHUB_TOKEN = "<PAT>"' + " then re-run.") -ForegroundColor Yellow
        Write-Host "    (d) Register credential once: cmdkey /generic:$CredentialName /user:TECT-OpenPhysics /pass:<PAT>" -ForegroundColor Yellow
        Write-Host "        Then snapshot.ps1 will pick it up automatically (current default name: $CredentialName)." -ForegroundColor Yellow
        Write-Host "    (e) Use GitHub CLI: gh auth login (then snapshot inherits via git credential helper)." -ForegroundColor Yellow
        exit 90
    }
}

# ---------------------------------------------------------------------
# Helper: run a step, print prefix, abort on non-zero exit.
# ---------------------------------------------------------------------
function Invoke-Step($num, $label, $cmd, $exitCode) {
    Write-Host ""
    Write-Host ("[{0}/8] {1}" -f $num, $label) -ForegroundColor Cyan
    Write-Host ("       $cmd") -ForegroundColor DarkGray
    if ($DryRun) {
        Write-Host "       (DRY-RUN: not executed)" -ForegroundColor Yellow
        return
    }
    & cmd /c $cmd
    if ($LASTEXITCODE -ne 0) {
        Write-Host ("FAIL [{0}/8 {1}]: exit {2}" -f $num, $label, $LASTEXITCODE) -ForegroundColor Red
        throw "snapshot step $num/$label failed (exit $LASTEXITCODE)"
    }
    Write-Host ("       OK [{0}/8]" -f $num) -ForegroundColor Green
}

# ---------------------------------------------------------------------
# Wrapper: track per-step result for the closing summary.
# ---------------------------------------------------------------------
$stepResults = @{}
$commitHash = $null
$githubCommitUrl = $null
$auditWarnings = 0

try {
    # ---- Step 0.5 / 8: file-integrity guard (NUL padding + truncation) ----
    # NOTE (2026-05-07): catches the recurring failure modes documented
    # in Math352 (Write-tool NUL padding, Edit-tool mid-line truncation).
    # Runs --strict so any defect aborts the snapshot before commit.
    # Repair via: python -u Codes/tools/check_file_integrity.py --fix
    Invoke-Step 1 'integrity-check' 'python -u Codes\tools\check_file_integrity.py --strict' 5
    $stepResults['integrity-check'] = 'PASS'

    # ---- Step 1 / 8: stamp version headers ---------------------------
    Invoke-Step 1 'stamp' 'python -u Codes\pde\stamp_version_headers.py' 10
    $stepResults['stamp'] = 'PASS'

    # ---- Step 2 / 8: regenerate Website/data + Website/assets --------
    # NOTE (2026-05-01 fix): use --publish (= --all + --copy-assets) so the
    # asset-copy plan (Docs/Codes/Runs -> Website/assets/) actually runs.
    # The bare --all only regenerates data/*.js; without copy-assets the
    # download links in math-notes.js / code.js / results.js point to
    # files that do not exist in Website/assets/, and verify_website.py
    # fails at the [broken-link] check (this was the inaugural-snapshot
    # failure mode at 2026-05-01T18:32 -- 46 broken-link errors).
    Invoke-Step 2 'generate' 'python -u Codes\tools\generate_website.py --publish' 20
    $stepResults['generate'] = 'PASS'

    # ---- Step 2.4 / 8: sync-toe-from-status -------------------------
    # NOTE (2026-05-07, post-rename): Status page (status.js, hand-curated;
    # renamed from states.js) is the single source of truth for the
    # 11-pillar canonical T-tier scoreboard. TOE page (toe.js, hand-curated)
    # carried 6-Stage narrative which drifted from Status. This step parses
    # the pillar-tier table from status.js and emits status_pillar_tiers.js
    # + injects an auto-derived overlay into toe.html so the TOE page
    # always shows live Status data.
    Invoke-Step 2 'sync-toe-from-status' 'python -u Codes\tools\sync_toe_from_status.py' 20
    $stepResults['sync-toe-from-status'] = 'PASS'

    # ---- Step 2.5a / 8: extract-paper-dependencies ------------------
    # NOTE (2026-05-06): scans every paper TeX for `% Canonical archive:`
    # header tokens + body \cite{Math...} references, validates against
    # Docs/math/, emits Docs/status/PAPER-MATH-DEPENDENCIES.md (forward +
    # reverse map) AND Website/data/papers_math_dependencies.js
    # (window.TECT_PAPERS_DEPS) so papers-deps.html can render the
    # paper <-> Math-note dependency matrix. Exit 1 on missing-Math-note
    # gates the snapshot pipeline (use --no-fail to override).
    Invoke-Step 2 'extract-deps' 'python -u Codes\tools\extract_paper_dependencies.py' 20
    $stepResults['extract-deps'] = 'PASS'

    # ---- Step 2.5b / 8: propagate-status ----------------------------
    # NOTE (2026-05-07): propagates the canonical 11-pillar Stage-1
    # scoreboard from Website/data/status.js to status_pillar_tiers.js
    # (whole-file regen, parallel to the older sync_toe_from_status step
    # which still runs to inject the toe.html overlay) and to the
    # PROP-AUTO marker zones in EVIDENCE-INDEX.md. Governed by
    # Docs/policy/STATUS_PROPAGATION_POLICY.md (binding 2026-05-07).
    # Idempotent: timestamp-aware compare reports no-drift on reruns.
    Invoke-Step 2 'propagate-status' 'python -u Codes\tools\propagate_status.py' 20
    $stepResults['propagate-status'] = 'PASS'

    # ---- Step 2.5c / 8: paper-status-impact -------------------------
    # NOTE (2026-05-07): cross-references recent STATUS-HISTORY.md
    # entries against the paper -> Math-note dependency map and emits
    # Docs/status/paper-impact-report.md flagging any paper whose
    # cited Math notes have been refuted or downgraded. Default mode
    # (no --check) writes the report unconditionally; the report is
    # always advisory unless an operator wires --check elsewhere.
    Invoke-Step 2 'paper-status-impact' 'python -u Codes\tools\paper_status_impact.py' 20
    $stepResults['paper-status-impact'] = 'PASS'

    # ---- Step 2.5d / 8: paper-need-assessment -----------------------
    # NOTE (2026-05-07): emits a "Suggested new papers" section appended
    # to paper-impact-report.md per MATH_NOTE_AND_PAPER_DISCIPLINE.md §2.
    # Recommendations are always advisory and never block the snapshot.
    # The AI collaborator does NOT auto-draft any paper prose
    # (CLAUDE.md §9 binding); the operator decides each recommendation.
    Invoke-Step 2 'paper-need-assessment' 'python -u Codes\tools\paper_need_assessment.py' 20
    $stepResults['paper-need-assessment'] = 'PASS'

    # ---- Step 2.6 / 8: website-freshness audit ---------------------
    Invoke-Step 2 'audit-website-freshness' 'python -u Codes\tools\audit_website_freshness.py' 20
    $stepResults['audit-website-freshness'] = 'PASS'

    # ---- Step 2.5b / 8: publish-papers (PDF sweep + index.js) -------
    # NOTE (2026-05-06): copies Docs/papers/**/Paper-*.pdf into
    # Github/assets/papers/<category>/<stem>.pdf and emits
    # Website/data/papers_pdf_index.js so papers-pdf.html can render
    # download links.
    Invoke-Step 2 'publish-papers' 'python -u Codes\tools\publish_papers.py' 20
    $stepResults['publish-papers'] = 'PASS'

    # ---- Step 3 / 8: verify Website state ----------------------------
    Invoke-Step 3 'verify' 'python -u Codes\tools\verify_website.py' 30
    $stepResults['verify'] = 'PASS'

    # ---- Step 4 / 8: regenerate canonical manifest --------------------
    # NOTE (2026-05-01 fix): the canonical manifest schema (with `count`,
    # `total_bytes`, schema string `tect-asset-manifest-v1`) is owned by
    # verify_website.py --regen-manifest, NOT by generate_website.py.
    # The latter's copy_assets() writes a different (legacy) schema that
    # lacks the `count` field, causing check_manifest_freshness() to
    # read declared=-1 (default) and flag manifest-stale.
    # Pre-fix this step called the non-existent
    # `generate_website.py --regenerate-manifest` flag.
    if ($SkipManifest) {
        Write-Host ""
        Write-Host '[4/8] manifest SKIPPED (-SkipManifest)' -ForegroundColor Yellow
        $stepResults['manifest'] = 'SKIP'
    } else {
        Invoke-Step 4 'manifest' 'python -u Codes\tools\verify_website.py --regen-manifest' 40
        $stepResults['manifest'] = 'PASS'
    }

    # ---- Step 5 / 8: atomic-commit canonical changes -----------------
    Write-Host ""
    Write-Host '[5/8] commit' -ForegroundColor Cyan

    # Discover modified + untracked files via git porcelain output.
    # Filter to files that the snapshot policy considers part of the
    # canonical tier (Docs/, Codes/, CHANGELOG.md, Runs/, top-level).
    # Forbidden patterns are filtered out by sandbox_commit.sh itself.
    if ($DryRun) {
        Write-Host '       (DRY-RUN: not executed)' -ForegroundColor Yellow
        $stepResults['commit'] = 'DRY-RUN'
    } else {
        $porcelain = & git status --porcelain
        $changedFiles = @()
        foreach ($line in $porcelain) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            # porcelain format: "XY filename" where XY are 2-char status codes
            $statusCode = $line.Substring(0, 2)
            $rawPath = $line.Substring(3).Trim()
            # Skip deleted-only entries (sandbox_commit handles them)
            if ($statusCode -eq 'D ' -or $statusCode -eq ' D') { continue }
            # Strip surrounding quotes that git adds for paths with spaces
            if ($rawPath.StartsWith('"') -and $rawPath.EndsWith('"')) {
                $rawPath = $rawPath.Substring(1, $rawPath.Length - 2)
            }
            # Normalise to forward slashes (sandbox_commit expects them)
            $rawPath = $rawPath -replace '\\', '/'
            $changedFiles += $rawPath
        }

        # Add operator-supplied -ExtraFiles
        foreach ($ef in $ExtraFiles) {
            $efNorm = $ef -replace '\\', '/'
            if ($changedFiles -notcontains $efNorm) {
                $changedFiles += $efNorm
            }
        }

        # ── v2.6.7d (2026-05-01) forbidden-pattern pre-filter ──
        # sandbox_commit.sh refuses files matching the REPO_LAYOUT §13
        # forbidden patterns (orphan commit-helpers, top-level Psi npy,
        # top-level .tex.txt). Pre-filtering them HERE means snapshot
        # completes with the legitimate changes; the offending files
        # remain on disk untracked and the operator is told to run
        # cleanup_root.ps1 -Apply to delete them. Without pre-filter,
        # sandbox_commit.sh exits with code 8 and the entire snapshot
        # aborts at step 5/8 (the failure mode observed at the inaugural
        # snapshot 2026-05-01T21:?? for 9 commit-helpers + 7 orphan
        # instruction files dating back to the autonomous-research era).
        $forbiddenAtRootPatterns = @(
            # sandbox_commit.sh §50-63 set:
            '*commit*.sh', '*commit*.py', '*commit*.bat',
            'direct_*.sh', 'do_commit*.sh', 'run_commit*.sh', 'run_*_commit.sh',
            'temp_commit_*.sh', 'temp_*_commit.sh',
            '*_commit_msg.txt', '*_commit_*.txt',
            'COMMIT_MANIFEST_*.txt', 'COMMIT_*.txt',
            '.commit_message_temp.txt', '.*_commit_trigger', '.*_commit_msg',
            'Psi_BCC_*.npy', '*.npy', '*.npz',
            '*.tex.txt',
            # Extended set (cleanup_root.ps1 + observed orphans):
            'COMMIT_*.sh', 'commit-msg-*.txt',
            'ROUND-*.txt', 'ROUND*_COMMIT_MSG.txt', 'ROUND*_COMMIT_*.txt',
            'TURN-*.txt', 'TURN*_COMMIT_*.txt',
            'MATH*_DEPLOYMENT_*.txt',
            'temp_*_commit.txt',
            'CLAUDE.md.full', 'CLAUDE.md.recovery',
            '*_commit_message.txt',
            '.commit_msg_*.txt',
            'commit_msg_*.txt',
            '*COMMIT*INSTRUCTIONS.txt',
            '*SESSION_SUMMARY*.txt',
            '*STRATEGIC_PLAN*.txt'
        )
        $skippedForbidden = @()
        $filteredFiles = @()
        foreach ($f in $changedFiles) {
            $isFileAtRoot = (-not $f.Contains('/')) -or $f.EndsWith('/')
            $isDirectory = $f.EndsWith('/')
            if ($isFileAtRoot -and -not $isDirectory) {
                # Apply forbidden-pattern check
                $isForbidden = $false
                foreach ($pat in $forbiddenAtRootPatterns) {
                    if ($f -like $pat) {
                        $isForbidden = $true
                        break
                    }
                }
                if ($isForbidden) {
                    $skippedForbidden += $f
                    continue
                }
            }
            $filteredFiles += $f
        }
        if ($skippedForbidden.Count -gt 0) {
            Write-Host ''
            Write-Host ("       WARN: " + $skippedForbidden.Count +
                       " file(s) at root match REPO_LAYOUT §13 forbidden patterns; " +
                       "filtered from this snapshot:") -ForegroundColor Yellow
            foreach ($f in $skippedForbidden) {
                Write-Host ('         - ' + $f) -ForegroundColor Yellow
            }
            Write-Host '       To delete them, run:' -ForegroundColor Yellow
            Write-Host '         pwsh Codes\scripts\cleanup_root.ps1 -Apply' -ForegroundColor Yellow
            Write-Host '       (current snapshot proceeds with legitimate changes only)' -ForegroundColor Yellow
            $changedFiles = $filteredFiles
        }

        if ($changedFiles.Count -eq 0) {
            if ($AllowEmpty) {
                Write-Host '       no changes detected; -AllowEmpty in effect; commit step is a no-op.' -ForegroundColor Yellow
                $stepResults['commit'] = 'NO-OP'
            } else {
                Write-Host '       FAIL: no changes detected. Use -AllowEmpty to snapshot with no commit.' -ForegroundColor Red
                throw 'commit step has nothing to commit (use -AllowEmpty to override)'
            }
        } else {
            Write-Host ('       discovered ' + $changedFiles.Count + ' changed file(s):') -ForegroundColor DarkGray
            foreach ($f in $changedFiles) { Write-Host ('         ' + $f) -ForegroundColor DarkGray }

            # Build the bash command. sandbox_commit.sh expects:
            #   sandbox_commit.sh "<message>" <file1> <file2> ...
            $bashFiles = ($changedFiles | ForEach-Object { '"' + $_ + '"' }) -join ' '
            $msgEsc = $Message -replace '"', '\"'
            $bashCmd = "bash Codes/scripts/sandbox_commit.sh `"$msgEsc`" $bashFiles"
            Write-Host ('       $ ' + $bashCmd) -ForegroundColor DarkGray
            & cmd /c $bashCmd
            if ($LASTEXITCODE -ne 0) {
                Write-Host ('FAIL [5/8 commit]: exit ' + $LASTEXITCODE) -ForegroundColor Red
                throw "commit step failed (exit $LASTEXITCODE)"
            }
            $commitHash = (& git rev-parse --short HEAD).Trim()
            Write-Host ('       OK [5/8] commit ' + $commitHash) -ForegroundColor Green
            $stepResults['commit'] = "PASS ($commitHash)"
        }
    }

    # ---- Step 6 / 8: curate Github mirror ----------------------------
    if ($SkipGitHub) {
        Write-Host ""
        Write-Host '[6/8] curate SKIPPED (-SkipGitHub)' -ForegroundColor Yellow
        $stepResults['curate'] = 'SKIP'
    } else {
        Invoke-Step 6 'curate' 'python -u Codes\tools\github_sync_curate.py' 60
        $stepResults['curate'] = 'PASS'
    }

    # ---- Step 7 / 8: publish to GitHub remote -----------------------
    if ($SkipGitHub) {
        Write-Host ""
        Write-Host '[7/8] push SKIPPED (-SkipGitHub)' -ForegroundColor Yellow
        $stepResults['push'] = 'SKIP'
    } else {
        # Prefer inline -Token (operator-supplied this run) over registered
        # credential (longer-lived). Either is acceptable per the §preflight
        # check above.
        # 2026-05-01 fix: use direct named arguments instead of @publishArgs
        # splatting. PowerShell sometimes mis-routes splatted parameters
        # when the target script uses ParameterSetName attributes (publish.ps1
        # has 'Inline' / 'Credential' parameter sets, and the splat-bind
        # path can fail to select the correct set, raising
        # "Cannot find a positional parameter that accepts the argument
        # '-CredentialName'." (observed at the inaugural snapshot
        # 2026-05-01T21:18). Direct named-arg invocation avoids the
        # ambiguity.
        $usingToken = -not [string]::IsNullOrWhiteSpace($Token)
        if ($usingToken) {
            $publishMethod = "inline -Token"
        } else {
            $publishMethod = "credential '$CredentialName'"
        }
        Write-Host ""
        Write-Host '[7/8] push' -ForegroundColor Cyan
        Write-Host ("       method: $publishMethod") -ForegroundColor DarkGray
        # Do NOT print the token value to the host. Show only the method.
        if ($DryRun) {
            Write-Host '       (DRY-RUN: publish.ps1 -DryRun delegated)' -ForegroundColor Yellow
        }
        if ($usingToken) {
            if ($DryRun) {
                & .\Codes\scripts\publish.ps1 -Token $Token -DryRun
            } else {
                & .\Codes\scripts\publish.ps1 -Token $Token
            }
        } else {
            if ($DryRun) {
                & .\Codes\scripts\publish.ps1 -CredentialName $CredentialName -DryRun
            } else {
                & .\Codes\scripts\publish.ps1 -CredentialName $CredentialName
            }
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Host ('FAIL [7/8 push]: publish.ps1 exit ' + $LASTEXITCODE) -ForegroundColor Red
            throw "push step failed (publish.ps1 exit $LASTEXITCODE)"
        }
        # Best-effort: read the most recent github commit hash for the URL
        try {
            $githubHash = (& git -C Github rev-parse HEAD).Trim()
            if ($githubHash) {
                $githubCommitUrl = "https://github.com/TECT-OpenPhysics/TECT/commit/$githubHash"
            }
        } catch {}
        Write-Host '       OK [7/8] push' -ForegroundColor Green
        $stepResults['push'] = if ($githubCommitUrl) { "PASS ($githubCommitUrl)" } else { "PASS" }
    }

    # ---- Step 8 / 8: review-cadence audit ----------------------------
    Write-Host ""
    Write-Host '[8/8] audit' -ForegroundColor Cyan
    if ($DryRun) {
        Write-Host '       (DRY-RUN: not executed)' -ForegroundColor Yellow
        $stepResults['audit'] = 'DRY-RUN'
    } else {
        & cmd /c 'python -u Codes\tools\check_review_cadence.py --check'
        # check_review_cadence returns 0 = clean, non-zero = warnings.
        # Snapshot policy: warnings are non-fatal but tracked.
        if ($LASTEXITCODE -ne 0) {
            $auditWarnings = $LASTEXITCODE
            Write-Host ('       WARN [8/8 audit]: check_review_cadence reported ' +
                       $auditWarnings + ' warning(s) (non-fatal)') -ForegroundColor Yellow
            $stepResults['audit'] = "WARN ($auditWarnings)"
        } else {
            Write-Host '       OK [8/8] audit (clean)' -ForegroundColor Green
            $stepResults['audit'] = 'PASS (clean)'
        }
    }

    # ---- Closing summary + snapshot-log entry ------------------------
    $endTime = Get-Date
    $elapsed = $endTime - $startTime
    $tsUtc = $endTime.ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss')

    Write-Host ""
    Write-Host ('=' * 72) -ForegroundColor Green
    Write-Host (" [SNAPSHOT-OK] $tsUtc UTC") -ForegroundColor Green
    foreach ($k in @('stamp','generate','verify','manifest','commit','curate','push','audit')) {
        if ($stepResults.ContainsKey($k)) {
            Write-Host ("   - {0,-9} {1}" -f $k, $stepResults[$k])
        }
    }
    Write-Host (" Elapsed   : {0:N1} seconds" -f $elapsed.TotalSeconds)
    if ($commitHash) { Write-Host " Commit    : $commitHash" -ForegroundColor Green }
    if ($githubCommitUrl) { Write-Host " GitHub URL: $githubCommitUrl" -ForegroundColor Green }
    Write-Host ('=' * 72) -ForegroundColor Green

    # Append to snapshot-log.md (idempotent: even on dry-run, we record)
    if (-not $DryRun) {
        $snapshotLogPath = Join-Path $repoRoot 'Docs\status\snapshot-log.md'
        $snapshotLogDir = Split-Path -Parent $snapshotLogPath
        if (-not (Test-Path $snapshotLogDir)) { New-Item -ItemType Directory -Path $snapshotLogDir -Force | Out-Null }
        if (-not (Test-Path $snapshotLogPath)) {
            "# TECT Snapshot Log`r`n`r`n**Binding from**: 2026-05-01 per Docs/policy/SNAPSHOT_POLICY.md §12.`r`nAppend-only. Latest snapshot at top.`r`n`r`n---`r`n" |
                Set-Content -Path $snapshotLogPath -Encoding UTF8
        }
        $logEntry = @()
        $logEntry += "## $tsUtc UTC -- $commitHash -- $Message"
        foreach ($k in @('stamp','generate','verify','manifest','commit','curate','push','audit')) {
            if ($stepResults.ContainsKey($k)) {
                $logEntry += "- $k : $($stepResults[$k])"
            }
        }
        $logEntry += "- Elapsed: $([math]::Round($elapsed.TotalSeconds,1)) s"
        if ($githubCommitUrl) { $logEntry += "- GitHub: $githubCommitUrl" }
        $logEntry += ""
        $logEntry += "---"
        $logEntry += ""
        $existing = Get-Content -Path $snapshotLogPath -Raw -Encoding UTF8
        # Insert new entry after the header block (after '---' line)
        $marker = "`r`n---`r`n"
        $idx = $existing.IndexOf($marker)
        if ($idx -ge 0) {
            $head = $existing.Substring(0, $idx + $marker.Length)
            $tail = $existing.Substring($idx + $marker.Length)
            $newEntry = ($logEntry -join "`r`n") + "`r`n"
            ($head + $newEntry + $tail) | Set-Content -Path $snapshotLogPath -Encoding UTF8
        } else {
            ($logEntry -join "`r`n") + "`r`n" | Add-Content -Path $snapshotLogPath -Encoding UTF8
        }
        Write-Host (" snapshot-log.md updated") -ForegroundColor DarkGray
    }

    exit 0
}
catch {
    Write-Host ""
    Write-Host ("FAIL: " + $_.Exception.Message) -ForegroundColor Red
    if ($_.Exception.Message -match 'stamp')    { exit 10 }
    if ($_.Exception.Message -match 'generate') { exit 20 }
    if ($_.Exception.Message -match 'verify')   { exit 30 }
    if ($_.Exception.Message -match 'manifest') { exit 40 }
    if ($_.Exception.Message -match 'commit')   { exit 50 }
    if ($_.Exception.Message -match 'curate')   { exit 60 }
    if ($_.Exception.Message -match 'push')     { exit 70 }
    if ($_.Exception.Message -match 'integrity-check') { exit 5 }
    if ($_.Exception.Message -match 'audit')    { exit 80 }
    if ($_.Exception.Message -match 'precondition') { exit 90 }
    if ($_.Exception.Message -match 'propagate')    { exit 95 }
    if ($_.Exception.Message -match 'paper-status') { exit 96 }
    if ($_.Exception.Message -match 'paper-need')   { exit 97 }
    exit 99
}
