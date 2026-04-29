# =====================================================================
# repo_cleanup_phase3_d.ps1
# Theory tag:    Math82-Addendum-A-Phase-D-results-propagation-2026-04-24
# Purpose:       Execute Phase D of the 2026-04-24 repo cleanup:
#                propagate results/ tracked content to Runs/ canonical
#                subtree and retire results/ + clean Phase-C leftover
#                empty/untracked directories.
# Companion:     Docs/math/TECT-Math82-Addendum-A-Phase-D-results-propagation.tex.txt
# Scope:
#   D.1  Create Runs/audit/ if missing.
#   D.2  Move 11 tracked files from results/ to Runs/audit/ (.png, .json, .txt).
#   D.3  Remove untracked / empty subfolders from results/ (math55_endpoint_*).
#   D.4  Retire results/ via git rm -r.
#   D.5  Remove Phase-C leftover empty dirs: tools/, tests/, scripts/, runs/.
# Out of scope (Phase E + F, post Task #54 closure):
#   - PDE/ historical-data internal sorting.
#   - PDE/ retirement.
# Safety:
#   - All operations under git tracking; history preserved via git mv / git rm.
#   - Empty / untracked dirs are removed via Remove-Item.
#   - $env:GIT_REDIRECT_STDERR='2>&1' prevents PowerShell from treating
#     git's normal LF/CRLF stderr warnings as fatal exceptions.
# Usage (PowerShell from C:\Dev\TECT2\Contents):
#   Remove-Item .git\HEAD.lock,.git\index.lock -Force -ErrorAction SilentlyContinue
#   .\Codes\scripts\repo_cleanup_phase3_d.ps1
# =====================================================================
$ErrorActionPreference = 'Stop'
$env:GIT_REDIRECT_STDERR = '2>&1'
Set-Location $PSScriptRoot\..\..

Write-Host "=============================================================="
Write-Host " repo_cleanup_phase3_d.ps1  (Math82-Addendum-A Phase D execution)"
Write-Host "=============================================================="

if (-not (Test-Path 'CLAUDE.md')) {
    Write-Error "Not at repo root. Expected CLAUDE.md present."
    exit 1
}

# --- D.1: Create Runs/audit/ if missing ---
Write-Host ''
Write-Host '--- D.1: ensure Runs/audit/ exists ---'
$null = New-Item -ItemType Directory -Force -Path 'Runs/audit'

# --- D.2: Move 11 tracked files from results/ to Runs/audit/ ---
Write-Host ''
Write-Host '--- D.2: relocate 11 tracked files from results/ to Runs/audit/ ---'
$ResultsFiles = @(
    'dirac_casimir_verification.png',
    'math64_decisive_cII_test.json',
    'math64_decisive_cII_test_A.json',
    'math64_decisive_cII_test_B.json',
    'n64_audit_2026-04-22.json',
    'stage_alpha_archive_sha256.txt',
    'stage_alpha_A_fd_on.json',
    'stage_alpha_B_autograd_on.json',
    'stage_alpha_C_fd_off.json',
    'stage_alpha_D_autograd_off.json',
    'step1_block_probe.json'
)
foreach ($f in $ResultsFiles) {
    if (Test-Path "results/$f") {
        git mv "results/$f" "Runs/audit/$f"
    } else {
        Write-Warning "Skip (not present): results/$f"
    }
}

# --- D.3: Remove untracked / empty subfolders from results/ ---
Write-Host ''
Write-Host '--- D.3: remove untracked / empty subfolders from results/ ---'
$ResultsSubfolders = @(
    'results/math55_endpoint_N32_L16_2026-04-23',
    'results/math55_endpoint_N32_Lbcc7_2026-04-23'
)
foreach ($d in $ResultsSubfolders) {
    if (Test-Path $d) {
        Remove-Item -Recurse -Force $d
    }
}

# --- D.4: results/ now empty; remove ---
Write-Host ''
Write-Host '--- D.4: remove now-empty results/ ---'
if (Test-Path 'results') {
    $remaining = Get-ChildItem -Path 'results' -Force -ErrorAction SilentlyContinue
    if ($null -eq $remaining -or $remaining.Count -eq 0) {
        Remove-Item -Recurse -Force 'results'
        Write-Host 'results/ removed (now empty after D.2 + D.3).'
    } else {
        Write-Warning "results/ not empty after D.2 + D.3 — manual review:"
        $remaining | ForEach-Object { Write-Warning "  $_" }
    }
}

# --- D.5: Phase-C leftover empty / untracked dirs ---
Write-Host ''
Write-Host '--- D.5: clean Phase-C leftover empty/untracked directories ---'

# tools/__pycache__ — untracked compiled bytecode
if (Test-Path 'tools') {
    Remove-Item -Recurse -Force 'tools'
    Write-Host 'tools/ removed (only __pycache__ remained).'
}

# tests/__pycache__ — untracked compiled bytecode
if (Test-Path 'tests') {
    Remove-Item -Recurse -Force 'tests'
    Write-Host 'tests/ removed (only __pycache__ remained).'
}

# scripts/ — empty after Phase C
if (Test-Path 'scripts') {
    Remove-Item -Recurse -Force 'scripts'
    Write-Host 'scripts/ removed (was empty after Phase C).'
}

# runs/ — empty subfolders after Phase C tracked-file removal
if (Test-Path 'runs') {
    Remove-Item -Recurse -Force 'runs'
    Write-Host 'runs/ removed (only empty subfolders remained after Phase C).'
}

# --- Stage + commit ---
Write-Host ''
Write-Host '--- Stage Math82-Addendum-A + REPO_LAYOUT update + NAVIGATION update + CHANGELOG ---'
git add Docs/math/TECT-Math82-Addendum-A-Phase-D-results-propagation.tex.txt
git add Docs/policy/REPO_LAYOUT.md
git add NAVIGATION.md
git add CHANGELOG.md
git add Codes/scripts/repo_cleanup_phase3_d.ps1

Write-Host ''
Write-Host '--- Commit ---'
git -c user.email='jtkor@outlook.com' -c user.name='Jusang Lee' commit -m @"
Math82 Addendum A Phase D: results/ propagation to Runs/audit/ + Phase-C leftover cleanup

Phase D moves 11 tracked files from results/ to canonical Runs/audit/:
  dirac_casimir_verification.png
  math64_decisive_cII_test{,_A,_B}.json (3)
  n64_audit_2026-04-22.json
  stage_alpha_archive_sha256.txt
  stage_alpha_{A_fd_on,B_autograd_on,C_fd_off,D_autograd_off}.json (4)
  step1_block_probe.json

Empty / untracked subfolders removed from results/:
  results/math55_endpoint_N32_L16_2026-04-23/
  results/math55_endpoint_N32_Lbcc7_2026-04-23/
(These held .npy / .json runtime outputs that are gitignored.)

results/ is now empty and removed.

Phase-C leftover untracked / empty directories also removed:
  tools/__pycache__   (Python bytecode, gitignored)
  tests/__pycache__   (Python bytecode, gitignored)
  scripts/            (became empty after Phase C)
  runs/               (only empty subfolders remained after Phase C
                       tracked-file removal)

After this commit, the only remaining deprecated path is PDE/, which
remains live for Task #54. PDE/ retirement is Phase E + F, scheduled
for post-Task-#54 closure.

REPO_LAYOUT.md migration table updated. NAVIGATION.md quick-map
updated. CHANGELOG entry filed.

No theory or pillar status changes. Structural-discipline commit only.
"@

Write-Host ''
Write-Host '=============================================================='
Write-Host '  Phase D complete. PDE/ remains as the only deprecated path.'
Write-Host '  See: git log -1 --stat'
Write-Host '=============================================================='
