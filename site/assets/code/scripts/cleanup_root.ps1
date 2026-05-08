# =====================================================================
# cleanup_root.ps1 — purge stray autonomous-research files from the
#                    Contents/ repository root.
#
# CONTEXT
#   The Cowork sandbox cannot delete files on the Windows-mount due to
#   NTFS ACL restrictions. This script runs natively in PowerShell on
#   the user's machine and removes the well-known classes of stray files
#   created by autonomous research agents that did not yet know about the
#   canonical layout (Codes/scripts/sandbox_commit.sh, Runs/seeds/, etc.).
#
# USAGE (from Contents/ root in PowerShell):
#     pwsh Codes\scripts\cleanup_root.ps1
#     # or:    powershell -ExecutionPolicy Bypass -File Codes\scripts\cleanup_root.ps1
#
# SAFETY
#   - Dry-run by default: prints what WOULD be removed; no deletion.
#   - Pass `-Apply` to actually delete files.
#   - Files matching the patterns below are SAFE TO DELETE:
#       commit_*.sh        (stray agent commit helpers)
#       commit_*.py        (stray agent commit helpers)
#       do_commit*.sh      (stray agent commit helpers)
#       run_commit*.sh     (stray agent commit helpers)
#       run_q6d_commit.sh  (Turn-2 Q6d commit attempt)
#       temp_commit_*.sh   (stray temp commit helpers)
#       temp_q6d_commit.sh (Turn-2 Q6d temp helper)
#       q6d_commit_msg.txt (orphan commit message)
#       COMMIT_MANIFEST_*.txt (orphan manifest)
#       .commit_message_temp.txt
#       .q6d_commit_trigger
#   - Numerical seed files (Psi_BCC_*.npy + .meta.json) are MOVED to
#     Runs/seeds/ if not already present, then deleted from root.
#
# Future agents must NOT create files at repo root; see
# `Docs/policy/REPO_LAYOUT.md` §6 (Where new files go) and CLAUDE.md §13.
# =====================================================================

param(
    [switch]$Apply
)

$RepoRoot = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
Push-Location $RepoRoot
Write-Host "Repo root: $RepoRoot" -ForegroundColor Cyan

$strayPatterns = @(
    # broad nets (any commit-helper / commit-message at root):
    "*commit*.sh",
    "*commit*.py",
    "*commit*.bat",
    "*_commit_msg.txt",
    "*_commit_*.txt",
    "COMMIT_MANIFEST_*.txt",
    "COMMIT_*.txt",
    ".commit_message_temp.txt",
    ".*_commit_trigger",
    ".*_commit_msg",
    # explicit historical patterns (defense-in-depth):
    "direct_*.sh",
    "do_commit*.sh",
    "run_commit*.sh",
    "run_q6d_commit.sh",
    "temp_commit_*.sh",
    "temp_q6d_commit.sh",
    "q6d_commit_msg.txt"
)

$seedPatterns = @(
    "Psi_BCC_*.npy",
    "Psi_BCC_*.npy.meta.json"
)

# Step 1 — list strays
Write-Host "`n--- Stray commit helpers / orphan messages ---" -ForegroundColor Yellow
$strays = @()
foreach ($p in $strayPatterns) {
    $strays += Get-ChildItem -Force -File -ErrorAction SilentlyContinue -Filter $p
}
if ($strays.Count -eq 0) {
    Write-Host "  (none found)" -ForegroundColor Green
} else {
    foreach ($f in $strays) { Write-Host "  $($f.Name) ($($f.Length) bytes)" }
}

# Step 2 — list seeds + relocate
Write-Host "`n--- Numerical seed files (move to Runs\seeds\) ---" -ForegroundColor Yellow
$seedsDir = Join-Path $RepoRoot "Runs\seeds"
if (-not (Test-Path $seedsDir)) {
    if ($Apply) { New-Item -ItemType Directory -Force -Path $seedsDir | Out-Null }
    Write-Host "  Runs\seeds\ will be created"
}
$seeds = @()
foreach ($p in $seedPatterns) {
    $seeds += Get-ChildItem -Force -File -ErrorAction SilentlyContinue -Filter $p
}
if ($seeds.Count -eq 0) {
    Write-Host "  (none found)" -ForegroundColor Green
} else {
    foreach ($f in $seeds) {
        $dst = Join-Path $seedsDir $f.Name
        if (Test-Path $dst) {
            Write-Host "  $($f.Name) -> already in Runs\seeds\; will delete root copy"
        } else {
            Write-Host "  $($f.Name) -> MOVE to Runs\seeds\"
        }
    }
}

# Step 3 — apply or dry-run
if (-not $Apply) {
    Write-Host "`n[DRY-RUN] No files were modified." -ForegroundColor Yellow
    Write-Host "Run with -Apply to actually delete / move files:" -ForegroundColor Yellow
    Write-Host "  pwsh Codes\scripts\cleanup_root.ps1 -Apply" -ForegroundColor Yellow
    Pop-Location
    exit 0
}

Write-Host "`n--- Applying ---" -ForegroundColor Magenta
foreach ($f in $strays) {
    try {
        Remove-Item -Force -LiteralPath $f.FullName
        Write-Host "  deleted: $($f.Name)" -ForegroundColor Green
    } catch {
        Write-Host "  FAILED:  $($f.Name) - $_" -ForegroundColor Red
    }
}
foreach ($f in $seeds) {
    $dst = Join-Path $seedsDir $f.Name
    try {
        if (-not (Test-Path $dst)) {
            Move-Item -Force -LiteralPath $f.FullName -Destination $dst
            Write-Host "  moved:   $($f.Name) -> Runs\seeds\" -ForegroundColor Green
        } else {
            Remove-Item -Force -LiteralPath $f.FullName
            Write-Host "  removed root copy of $($f.Name) (Runs\seeds\ already has it)" -ForegroundColor Green
        }
    } catch {
        Write-Host "  FAILED:  $($f.Name) - $_" -ForegroundColor Red
    }
}

# Step 4 — git untrack (not delete from history; just remove from index)
Write-Host "`n--- git rm --cached for tracked seeds ---" -ForegroundColor Yellow
$tracked = git ls-files | Where-Object { $_ -match '^Psi_BCC_' }
if ($tracked) {
    foreach ($t in $tracked) {
        & git rm --cached $t 2>&1 | Out-Host
    }
    Write-Host "  (tracked seeds untracked; commit the .gitignore-respecting state separately)"
} else {
    Write-Host "  (no tracked seeds)" -ForegroundColor Green
}

Write-Host "`nCleanup complete. Repo root should now match Docs\policy\REPO_LAYOUT.md sec 1." -ForegroundColor Cyan
Pop-Location
