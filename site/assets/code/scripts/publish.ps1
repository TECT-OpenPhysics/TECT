# =====================================================================
# publish.ps1 — single-command TECT publish pipeline
#
# Wraps the Layer-1 (curate) + Layer-2 (commit / push / meta) flow
# behind one PowerShell entry point so the operator runs ONE line per
# publication round instead of five.
#
# Pipeline (in order):
#   1. verify_website.py       (CLAUDE.md s6.3.7 binding)
#   2. github_sync_curate.py   (offline regeneration of Github/)
#   3. github_sync_push.py commit --apply
#   4. github_sync_push.py push --apply
#   5. github_sync_push.py meta --apply       (unless -SkipMeta)
#
# After each step the exit code is checked and the run aborts on the
# first failure (no partial publish). The GITHUB_TOKEN env var is
# always removed in a `finally` block, even on error or Ctrl-C.
#
# USAGE
# -----
#   # Token passed inline (one-shot session)
#   .\Codes\scripts\publish.ps1 -Token "<fine-grained PAT>"
#
#   # Token loaded from Windows Credential Manager (recommended)
#   #   First, register once:
#   #     cmdkey /generic:tect-github /user:jtkor /pass:<PAT>
#   .\Codes\scripts\publish.ps1 -CredentialName tect-github
#
#   # Skip the meta subcommand (faster, About/Topics/Releases not synced)
#   .\Codes\scripts\publish.ps1 -Token "<PAT>" -SkipMeta
#
#   # Skip releases only (About + Topics still sync, but no auto-tagging)
#   .\Codes\scripts\publish.ps1 -Token "<PAT>" -SkipReleases
#
#   # Dry-run: show what would happen without executing any step
#   .\Codes\scripts\publish.ps1 -Token "<PAT>" -DryRun
#
# EXIT CODES
# ----------
#   0   OK
#   10  verify_website.py failed
#   20  curate failed
#   30  commit failed
#   40  push failed
#   50  meta failed
#   90  precondition failed (no Github/.git, dirty mirror, etc.)
#   99  generic failure (uncaught exception)
#
# Author: Jusang Lee + collaboration (2026-04-29).
# =====================================================================

[CmdletBinding(DefaultParameterSetName = 'Inline')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'Inline')]
    [string]$Token,

    [Parameter(Mandatory = $true, ParameterSetName = 'Credential')]
    [string]$CredentialName,

    [switch]$SkipMeta,
    [switch]$SkipReleases,
    [switch]$DryRun,
    # -Force passes `--force-push --force-confirm` to the push subcommand.
    # Required after any `Remove-Item -Recurse -Force Github\.git` + re-init,
    # because the fresh local Github/.git history does not share commits
    # with the existing remote main; a fast-forward is impossible. The
    # 3-key safety gate (force_push:true in config + --force-push +
    # --force-confirm) is preserved; all three must agree.
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$startTime = Get-Date

# ---------------------------------------------------------------------
# 0. Locate repository root from the script's location.
# ---------------------------------------------------------------------
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $repoRoot

if ($DryRun) { $modeLabel = 'DRY-RUN' } else { $modeLabel = 'APPLY' }

Write-Host ('=' * 64) -ForegroundColor DarkCyan
Write-Host (' TECT publish pipeline -- Codes\scripts\publish.ps1')
Write-Host (' Repo root : ' + $repoRoot)
Write-Host (' Started   : ' + $startTime.ToString('yyyy-MM-dd HH:mm:ss zzz'))
Write-Host (' Mode      : ' + $modeLabel)
if ($SkipMeta)     { Write-Host ' Flag      : -SkipMeta'     -ForegroundColor Yellow }
if ($SkipReleases) { Write-Host ' Flag      : -SkipReleases' -ForegroundColor Yellow }
if ($Force)        { Write-Host ' Flag      : -Force (force-push enabled)' -ForegroundColor Yellow }
Write-Host ('=' * 64) -ForegroundColor DarkCyan

# ---------------------------------------------------------------------
# 1. Resolve token (inline OR Credential Manager).
# ---------------------------------------------------------------------
if ($PSCmdlet.ParameterSetName -eq 'Credential') {
    Write-Host "[token] Loading from Windows Credential Manager: $CredentialName" -ForegroundColor Cyan
    try {
        # Try the CredentialManager module first (Get-StoredCredential).
        if (Get-Command Get-StoredCredential -ErrorAction SilentlyContinue) {
            $cred = Get-StoredCredential -Target $CredentialName -ErrorAction Stop
            if ($null -eq $cred) {
                throw "Credential '$CredentialName' not found."
            }
            $Token = $cred.GetNetworkCredential().Password
        }
        else {
            # Fall back to cmdkey + native API. Less elegant but no module dep.
            Write-Host "  CredentialManager module absent; using cmdkey fallback." -ForegroundColor DarkYellow
            Write-Host "  (Install once: Install-Module -Name CredentialManager -Scope CurrentUser)" -ForegroundColor DarkYellow
            $cmdOut = & cmdkey /list:$CredentialName 2>&1
            if ($LASTEXITCODE -ne 0 -or $cmdOut -match 'NOT find any credentials') {
                throw "cmdkey could not locate credential '$CredentialName'."
            }
            throw "cmdkey can list but cannot retrieve passwords. Install CredentialManager module: Install-Module CredentialManager -Scope CurrentUser"
        }
    }
    catch {
        Write-Host "FAIL: $($_.Exception.Message)" -ForegroundColor Red
        exit 90
    }
    Write-Host "  OK -- token loaded ($(($Token.Length)) chars)." -ForegroundColor Green
}

if ([string]::IsNullOrWhiteSpace($Token)) {
    Write-Host "FAIL: empty token." -ForegroundColor Red
    exit 90
}

# ---------------------------------------------------------------------
# 2. Pre-flight checks.
# ---------------------------------------------------------------------
Write-Host ""
Write-Host "[preflight] checking repository state ..." -ForegroundColor Cyan

if (-not (Test-Path 'Github\.git')) {
    Write-Host "FAIL: Github\.git is missing. Run github_sync_push.py init --apply first." -ForegroundColor Red
    exit 90
}

# Quick isolation re-check (defense in depth; the push.py guard does
# the same but at a later step).
$toplevel = (& git -C Github rev-parse --show-toplevel 2>$null).Trim()
$expected = (Resolve-Path '.\Github').Path -replace '\\', '/'
if ($toplevel -ne $expected) {
    Write-Host "FAIL: Github/ is not its own isolated git repo." -ForegroundColor Red
    Write-Host ("  --show-toplevel = $toplevel") -ForegroundColor Red
    Write-Host ("  expected        = $expected") -ForegroundColor Red
    Write-Host "  Run: Remove-Item -Recurse -Force Github\.git; python -u Codes\tools\github_sync_push.py init --apply" -ForegroundColor Red
    exit 90
}

Write-Host "  OK -- Github\.git isolated, working tree present." -ForegroundColor Green

# ---------------------------------------------------------------------
# 3. The pipeline. Token is exposed via $env:GITHUB_TOKEN ONLY between
#    the try-block entry and its `finally` cleanup.
# ---------------------------------------------------------------------
function Step($label, $cmd, $exitOnFail) {
    Write-Host ""
    Write-Host "[$label] $cmd" -ForegroundColor Cyan
    if ($DryRun) {
        Write-Host "  (DRY-RUN: not executed)" -ForegroundColor Yellow
        return
    }
    & cmd /c $cmd
    if ($LASTEXITCODE -ne 0) {
        throw "$label failed (exit $LASTEXITCODE)"
    }
}

try {
    # ---- Step 1: verify_website ----
    Step 'step 1/5 verify_website' 'python -u Codes\tools\verify_website.py' 10

    # ---- Step 2: curate ----
    Step 'step 2/5 curate' 'python -u Codes\tools\github_sync_curate.py' 20

    # Token enters the env namespace ONLY here, removed in `finally`.
    $env:GITHUB_TOKEN = $Token

    # ---- Step 3: commit ----
    Step 'step 3/5 commit' 'python -u Codes\tools\github_sync_push.py commit --apply' 30

    # ---- Step 4: push ----
    $pushCmd = 'python -u Codes\tools\github_sync_push.py push --apply'
    if ($Force) { $pushCmd += ' --force-push --force-confirm' }
    Step 'step 4/5 push' $pushCmd 40

    # ---- Step 5: meta ----
    if (-not $SkipMeta) {
        $metaCmd = 'python -u Codes\tools\github_sync_push.py meta --apply'
        if ($SkipReleases) { $metaCmd += ' --skip-releases' }
        Step 'step 5/5 meta' $metaCmd 50
    }
    else {
        Write-Host ""
        Write-Host "[step 5/5 meta] SKIPPED (-SkipMeta flag)." -ForegroundColor Yellow
    }

    $endTime = Get-Date
    $elapsed = $endTime - $startTime

    Write-Host ""
    Write-Host ('=' * 64) -ForegroundColor Green
    Write-Host (' OK: TECT publish pipeline complete.') -ForegroundColor Green
    Write-Host (' Elapsed : ' + ('{0:N1}' -f $elapsed.TotalSeconds) + ' seconds')
    Write-Host (' Live    : https://github.com/TECT-OpenPhysics/TECT')
    Write-Host (' Site    : https://tect.kr (refresh per cron / webhook latency)')
    Write-Host ('=' * 64) -ForegroundColor Green
    exit 0
}
catch {
    Write-Host ""
    Write-Host "FAIL: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Message -match 'verify_website')  { exit 10 }
    if ($_.Exception.Message -match 'curate')          { exit 20 }
    if ($_.Exception.Message -match 'commit')          { exit 30 }
    if ($_.Exception.Message -match 'push')            { exit 40 }
    if ($_.Exception.Message -match 'meta')            { exit 50 }
    exit 99
}
finally {
    # Always remove the token, even on error / Ctrl-C / uncaught throw.
    if (Test-Path Env:\GITHUB_TOKEN) {
        Remove-Item Env:\GITHUB_TOKEN -ErrorAction SilentlyContinue
    }
    # Defensive: explicitly null the param too so the value cannot
    # be retained by the calling shell.
    $Token = $null
}
