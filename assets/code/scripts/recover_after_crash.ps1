# =====================================================================
# recover_after_crash.ps1 v1.0
# Windows PowerShell crash-recovery script for the TECT repo.
#
# Purpose: After a Claude Desktop crash, run ONE command from PowerShell
#          to:
#            1. Remove stale git lock files that WSL sandbox cannot rm
#            2. Verify all registered scripts have EOF sentinels
#            3. Verify HEAD / index integrity
#            4. Print recovery guidance if anything is broken
#
# Usage  : cd C:\Dev\TECT2\Contents
#          powershell -ExecutionPolicy Bypass -File Codes\scripts\recover_after_crash.ps1
#          [-WhatIf]   # dry-run, only report
#          [-Force]    # remove locks even if younger than 5 min
#
# Exit   : 0 clean; 1 issues found; 2 not in a repo
# =====================================================================

[CmdletBinding(SupportsShouldProcess)]
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "=== TECT crash-recovery v1.0 ===" -ForegroundColor Cyan
Write-Host ""

# -------------------- repo sanity --------------------
if (-not (Test-Path ".git" -PathType Container)) {
    Write-Host "  [FAIL] not in a git repo (no .git/)" -ForegroundColor Red
    exit 2
}

$issues = 0

# -------------------- (1) stale lock removal --------------------
Write-Host "-- stale-lock cleanup --"
$headRef = (Get-Content .git\HEAD -Raw).Trim()
$branchRef = $headRef -replace '^ref:\s+',''
$branchFile = ".git\$($branchRef -replace '/','\')"

$locks = @(
    ".git\index.lock",
    ".git\HEAD.lock",
    "$branchFile.lock"
)
foreach ($lock in $locks) {
    if (Test-Path $lock) {
        $item = Get-Item $lock -Force
        $ageMin = ((Get-Date) - $item.LastWriteTime).TotalMinutes
        if ($Force -or $ageMin -gt 5) {
            if ($PSCmdlet.ShouldProcess($lock, "Remove stale lock")) {
                try {
                    Remove-Item $lock -Force -ErrorAction Stop
                    Write-Host "  [OK]   removed $lock (age $([math]::Round($ageMin,1)) min)" -ForegroundColor Green
                } catch {
                    Write-Host "  [FAIL] could not remove $lock : $_" -ForegroundColor Red
                    $issues++
                }
            } else {
                Write-Host "  [DRY]  would remove $lock (age $([math]::Round($ageMin,1)) min)" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  [SKIP] $lock (age $([math]::Round($ageMin,1)) min <= 5 min; likely live)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [OK]   $lock (absent)"
    }
}

# -------------------- (2) script EOF-sentinel integrity --------------------
Write-Host ""
Write-Host "-- script integrity (EOF sentinels) --"
$registry = @(
    @{ Path = "Codes\scripts\sandbox_commit.sh";               Sentinel = "sandbox_commit_v2_0_eof_sentinel_DO_NOT_REMOVE" },
    @{ Path = "Codes\scripts\verify_scripts_integrity.sh";     Sentinel = "verify_scripts_integrity_v1_0_eof_sentinel_DO_NOT_REMOVE" },
    @{ Path = "Codes\scripts\preflight.sh";                    Sentinel = "preflight_v1_0_eof_sentinel_DO_NOT_REMOVE" }
)
foreach ($entry in $registry) {
    $p = $entry.Path
    $s = $entry.Sentinel
    if (-not (Test-Path $p)) {
        Write-Host "  [MISSING] $p" -ForegroundColor Red
        $issues++
        continue
    }
    $tail = Get-Content $p -Tail 5 -ErrorAction SilentlyContinue
    $pattern = "^# ${s}`$"
    if ($tail -match $pattern) {
        Write-Host "  [OK]      $p"
    } else {
        Write-Host "  [TRUNCAT] $p (missing EOF sentinel '$s')" -ForegroundColor Red
        Write-Host "            fix: git checkout HEAD -- $p" -ForegroundColor Yellow
        $issues++
    }
}

# -------------------- (3) HEAD integrity --------------------
Write-Host ""
Write-Host "-- HEAD integrity --"
try {
    $currentSha = (git rev-parse HEAD 2>$null).Trim()
    if ($currentSha -match '^[0-9a-f]{40}$') {
        Write-Host "  [OK]   HEAD -> $($currentSha.Substring(0,10))"
    } else {
        Write-Host "  [WARN] HEAD returned unexpected value: $currentSha" -ForegroundColor Yellow
        $issues++
    }

    # Check the diff HEAD vs HEAD~1 is not catastrophic (no accidental mass-delete)
    $diffCount = (git diff --name-status HEAD~1 HEAD 2>$null | Measure-Object).Count
    $deletedCount = ((git diff --name-status HEAD~1 HEAD 2>$null | Where-Object { $_ -match '^D\s' }) | Measure-Object).Count
    if ($deletedCount -gt 20) {
        Write-Host "  [WARN] HEAD commit has $deletedCount file deletions -- possibly a bad commit." -ForegroundColor Yellow
        Write-Host "         Inspect: git diff --name-status HEAD~1 HEAD | grep '^D'" -ForegroundColor Yellow
        Write-Host "         Recovery: git reset --mixed HEAD~1  (if bad)" -ForegroundColor Yellow
        $issues++
    } else {
        Write-Host "  [OK]   HEAD commit: $diffCount changes, $deletedCount deletions"
    }
} catch {
    Write-Host "  [FAIL] git command failed: $_" -ForegroundColor Red
    $issues++
}

# -------------------- summary --------------------
Write-Host ""
if ($issues -eq 0) {
    Write-Host "=== [OK] recovery complete -- repo is clean ===" -ForegroundColor Green
    exit 0
} else {
    Write-Host "=== [FAIL] $issues issue(s) found -- see Docs/policy/CRASH_RECOVERY.md ===" -ForegroundColor Red
    exit 1
}
