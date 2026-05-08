# =====================================================================
# repo_cleanup_phase_e_f.ps1
# Theory tag:    Math82-Addendum-C-Phase-E-F-PDE-retirement-2026-04-24
# Purpose:       Phase E + F of the 2026-04-24 repo cleanup. Retire PDE/
#                entirely after the Phase Z continuation run is launched.
# Companion:     Docs/math/TECT-Math82-Addendum-C-Phase-E-F-PDE-retirement.tex.txt
# Scope:
#   E.1  Move PDE/ policy docs        -> Docs/policy/
#   E.2  Move PDE/ .bat scripts       -> Codes/scripts/
#   E.3  Move PDE/ Phase_1 .txt       -> Runs/legacy/
#   E.4  Move PDE/ historical data subtrees -> Runs/historical/<name>/
#   E.5  Move PDE/deprecated/         -> Backup/pre-PDE-retirement-2026-04-24/PDE_deprecated/
#   E.6  Remove untracked PDE/__pycache__ and PDE/Psi_*.npy
#   F.1  git rm PDE/*.py and PDE/*.json (byte-equal with Codes/pde/)
#   F.2  Remove now-empty PDE/
#
# Safety:
#   - The Phase Z run uses Codes\pde\continuation_mu2_v25.py, NOT PDE/.
#     Therefore retiring PDE/ during the run is safe.
#   - $env:GIT_REDIRECT_STDERR='2>&1' prevents PowerShell from treating
#     git's normal stderr warnings as fatal.
#   - All operations preserve git history via git mv / git rm.
# Usage (PowerShell from C:\Dev\TECT2\Contents):
#   Remove-Item .git\HEAD.lock,.git\index.lock -Force -ErrorAction SilentlyContinue
#   .\Codes\scripts\repo_cleanup_phase_e_f.ps1
# =====================================================================
$ErrorActionPreference = 'Stop'
$env:GIT_REDIRECT_STDERR = '2>&1'
Set-Location $PSScriptRoot\..\..

Write-Host "=============================================================="
Write-Host " repo_cleanup_phase_e_f.ps1  (Math82-Addendum-C Phase E + F)"
Write-Host "=============================================================="

# Pre-flight
if (-not (Test-Path 'CLAUDE.md')) {
    Write-Error "Not at repo root. Expected CLAUDE.md present."; exit 1
}
if (-not (Test-Path 'Codes/pde/continuation_mu2_v25.py')) {
    Write-Error "Codes/pde/continuation_mu2_v25.py missing - canonical mirror not in place."
    exit 1
}
if (-not (Test-Path 'PDE')) {
    Write-Host "PDE/ already absent. Nothing to do."
    exit 0
}

# Ensure target directories exist
$null = New-Item -ItemType Directory -Force -Path 'Runs/historical'
$null = New-Item -ItemType Directory -Force -Path 'Runs/legacy'
$null = New-Item -ItemType Directory -Force -Path 'Backup/pre-PDE-retirement-2026-04-24'

# ---------------- Phase E.1: policy docs -> Docs/policy/ ----------------
Write-Host ''
Write-Host '--- E.1: policy docs PDE/ -> Docs/policy/ ---'
$policyDocs = @(
    'PDE/RECORDS_CUTOFF.md',
    'PDE/RESULT_TEMPLATE.md',
    'PDE/RETRO_MANIFEST_NOTE.md'
)
foreach ($f in $policyDocs) {
    if (Test-Path $f) {
        git mv $f 'Docs/policy/'
    } else {
        Write-Warning "Skip (not present): $f"
    }
}

# ---------------- Phase E.2: .bat -> Codes/scripts/ ----------------
Write-Host ''
Write-Host '--- E.2: .bat scripts PDE/ -> Codes/scripts/ ---'
$batScripts = Get-ChildItem 'PDE/*.bat' -ErrorAction SilentlyContinue
foreach ($f in $batScripts) {
    git mv $f.FullName "Codes/scripts/$($f.Name)"
}

# ---------------- Phase E.3: Phase_1 result -> Runs/legacy/ ----------------
Write-Host ''
Write-Host '--- E.3: Phase_1 result txt -> Runs/legacy/ ---'
if (Test-Path 'PDE/Phase_1_grid64_emergence_result.txt') {
    git mv 'PDE/Phase_1_grid64_emergence_result.txt' 'Runs/legacy/Phase_1_grid64_emergence_result.txt'
}

# ---------------- Phase E.4: historical data subtrees -> Runs/historical/ ----
Write-Host ''
Write-Host '--- E.4: historical data subtrees PDE/<dir>/ -> Runs/historical/<dir>/ ---'
$historicalDirs = @(
    'PDE/backup_GL_2026-04-15',
    'PDE/bcc_compare',
    'PDE/bcc_recalib64',
    'PDE/continuation_N16',
    'PDE/continuation_N32_v2p4',
    'PDE/continuation_fast_stable_N16',
    'PDE/data_pt_64_quick',
    'PDE/emerge_N64_mixed_s17',
    'PDE/newton_rigorous_N32',
    'PDE/newton_rigorous_N64',
    'PDE/newton_rigorous_N128',
    'PDE/newton_test_N32',
    'PDE/rank2_D0_1em4',
    'PDE/run_emerge_N64_s42',
    'PDE/run_emerge_N64_s42_extract',
    'PDE/run_emerge_N64_s42_long',
    'PDE/run_emerge_N64_s42_long_extract_soft',
    'PDE/run_finetune_bcc_ideal',
    'PDE/runs',
    'PDE/scan_1em3',
    'PDE/scan_1em4',
    'PDE/scan_2em4',
    'PDE/scan_5em4',
    'PDE/smoke_mixedbcc',
    'PDE/smoke_mixedbcc_extract',
    'PDE/smoke_purenoise',
    'PDE/smoke_purenoise_extract',
    'PDE/smoke_seeded',
    'PDE/smoke_seeded_extract',
    'PDE/sweep_mu2_results',
    'PDE/validation_runs',
    'PDE/validation_runs_tuned'
)
foreach ($d in $historicalDirs) {
    if (Test-Path $d) {
        $name = Split-Path -Leaf $d
        $dest = "Runs/historical/$name"
        if (Test-Path $dest) {
            Write-Warning "Destination already exists, skipping: $dest"
            continue
        }
        # Try git mv first; if directory has no tracked content, fall back to plain Move-Item
        $tracked = (git ls-files $d 2>$null | Measure-Object -Line).Lines
        if ($tracked -gt 0) {
            git mv $d $dest
        } else {
            Move-Item -Force $d $dest
        }
    }
}

# ---------------- Phase E.5: PDE/deprecated/ -> Backup/ ----------------
Write-Host ''
Write-Host '--- E.5: PDE/deprecated/ -> Backup/pre-PDE-retirement-2026-04-24/PDE_deprecated/ ---'
if (Test-Path 'PDE/deprecated') {
    $tracked = (git ls-files 'PDE/deprecated' 2>$null | Measure-Object -Line).Lines
    if ($tracked -gt 0) {
        git mv 'PDE/deprecated' 'Backup/pre-PDE-retirement-2026-04-24/PDE_deprecated'
    } else {
        Move-Item -Force 'PDE/deprecated' 'Backup/pre-PDE-retirement-2026-04-24/PDE_deprecated'
    }
}

# ---------------- Phase E.6: untracked PDE/__pycache__ + PDE/Psi_*.npy ----------------
Write-Host ''
Write-Host '--- E.6: remove untracked PDE/__pycache__ and PDE/Psi_*.npy ---'
if (Test-Path 'PDE/__pycache__') {
    Remove-Item -Recurse -Force 'PDE/__pycache__'
    Write-Host '  PDE/__pycache__/ removed.'
}
$npyFiles = Get-ChildItem 'PDE/*.npy' -ErrorAction SilentlyContinue
foreach ($f in $npyFiles) {
    Remove-Item -Force $f.FullName
}
if ($npyFiles.Count -gt 0) {
    Write-Host "  $($npyFiles.Count) .npy seed files removed."
}

# ---------------- Phase F.1: git rm PDE/*.py and PDE/*.json ----------------
Write-Host ''
Write-Host '--- F.1: git rm PDE/*.py and PDE/*.json (byte-equal mirrors with Codes/pde/) ---'
$pyFiles = Get-ChildItem 'PDE/*.py' -ErrorAction SilentlyContinue
foreach ($f in $pyFiles) {
    git rm $f.FullName
}
$jsonFiles = Get-ChildItem 'PDE/*.json' -ErrorAction SilentlyContinue
foreach ($f in $jsonFiles) {
    git rm $f.FullName
}

# ---------------- Phase F.2: PDE/ should now be empty; remove ----------------
Write-Host ''
Write-Host '--- F.2: remove now-empty PDE/ ---'
if (Test-Path 'PDE') {
    $remaining = Get-ChildItem 'PDE' -Force -ErrorAction SilentlyContinue
    if ($null -eq $remaining -or $remaining.Count -eq 0) {
        Remove-Item -Recurse -Force 'PDE'
        Write-Host '  PDE/ removed (now empty after E.1-F.1).'
    } else {
        Write-Warning "PDE/ not empty after cleanup. Manual review needed:"
        $remaining | ForEach-Object { Write-Warning "  $($_.FullName)" }
        Write-Warning "Aborting commit step. Investigate and remove leftovers manually."
        exit 1
    }
}

# ---------------- Stage + commit ----------------
Write-Host ''
Write-Host '--- Stage Math82-Addendum-C + REPO_LAYOUT update + NAVIGATION update + CHANGELOG ---'
git add Docs/math/TECT-Math82-Addendum-C-Phase-E-F-PDE-retirement.tex.txt
git add Docs/policy/REPO_LAYOUT.md
git add NAVIGATION.md
git add CHANGELOG.md
git add Codes/scripts/repo_cleanup_phase_e_f.ps1

Write-Host ''
Write-Host '--- Commit ---'
git -c user.email='jtkor@outlook.com' -c user.name='Jusang Lee' commit -m @"
Math82-Addendum-C Phase E + F: PDE/ retirement complete

Phase E.1: policy docs PDE/ -> Docs/policy/
  RECORDS_CUTOFF.md, RESULT_TEMPLATE.md, RETRO_MANIFEST_NOTE.md

Phase E.2: .bat scripts PDE/ -> Codes/scripts/
  check_and_continue_finetune.bat (and any others present)

Phase E.3: Phase_1 result txt -> Runs/legacy/
  Phase_1_grid64_emergence_result.txt

Phase E.4: historical execution data subtrees PDE/<dir>/ -> Runs/historical/<dir>/
  32 subdirs: backup_GL_2026-04-15, bcc_compare, bcc_recalib64,
  continuation_N16, continuation_N32_v2p4, continuation_fast_stable_N16,
  data_pt_64_quick, emerge_N64_mixed_s17, newton_rigorous_N{32,64,128},
  newton_test_N32, rank2_D0_1em4, run_emerge_N64_s42 + _extract +
  _long + _long_extract_soft, run_finetune_bcc_ideal, runs,
  scan_1em3/4/2em4/5em4, smoke_mixedbcc + _extract, smoke_purenoise +
  _extract, smoke_seeded + _extract, sweep_mu2_results, validation_runs,
  validation_runs_tuned.

Phase E.5: PDE/deprecated/ -> Backup/pre-PDE-retirement-2026-04-24/PDE_deprecated/
  ~55 deprecated files preserved as immutable archive.

Phase E.6: untracked content removed
  PDE/__pycache__/ (Python bytecode, gitignored)
  PDE/Psi_*.npy (~11 untracked seed files, gitignored)

Phase F.1: git rm PDE/*.py and PDE/*.json
  38 .py + 4 .json byte-equal mirrors with Codes/pde/ removed from
  index. History preserved via git rm.

Phase F.2: PDE/ removed (now empty).

Result: only the canonical top-level layout per REPO_LAYOUT.md §1
remains. PDE/ is fully retired. All in-flight Phase Z continuation
runs use Codes/pde/continuation_mu2_v25.py and were unaffected by
this commit.

REPO_LAYOUT.md §1 + §4 migration table updated. NAVIGATION.md
quick-map updated. CHANGELOG entry filed. Math82-Addendum-C
process note records the full execution log and traceability.

No theory or pillar status changes. Structural-discipline commit only.
"@

Write-Host ''
Write-Host '=============================================================='
Write-Host '  Phase E + F complete. PDE/ fully retired.'
Write-Host '  Repo root now matches the canonical REPO_LAYOUT.md §1 layout.'
Write-Host '  See: git log -1 --stat'
Write-Host '=============================================================='
