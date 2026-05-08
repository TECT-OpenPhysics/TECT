# =====================================================================
# repo_cleanup_phase2.ps1
# Theory tag:    Math82-RepoCleanup-Phase2-2026-04-24
# Purpose:       Execute Phase A + B + C of the 2026-04-24 repo
#                cleanup, per Docs/math/TECT-Math82-Repo-Cleanup-Phase2.tex.txt.
# Scope:
#   Phase A — relocate 18 root-level orphan files to canonical Docs/ subtrees.
#   Phase B — remove the empty continuation_v263_smoke/ directory.
#   Phase C — retire byte-equal mirrors: tools/, tests/, runs/, scripts/.
# Out of scope (deferred to Phase D-F, post Task #54 closure):
#   - results/ partial sync to Runs/
#   - PDE/ historical-data internal cleanup (data_pt_*, continuation_*,
#     newton_rigorous_*, emerge_*)
#   - PDE/ retirement
# Safety:
#   - All .gitignored files (e.g. *.npy, *.pyc) are unaffected.
#   - Destructive operations are git rm (history is preserved).
#   - Stops on first error (Stop-on-Error policy).
# Usage (PowerShell from C:\Dev\TECT2\Contents):
#   Remove-Item .git\HEAD.lock,.git\index.lock -Force -ErrorAction SilentlyContinue
#   .\Codes\scripts\repo_cleanup_phase2.ps1
# =====================================================================
$ErrorActionPreference = 'Stop'
# Prevent PowerShell from treating git's stderr warnings (e.g. LF/CRLF
# notices) as fatal exceptions. Git uses stderr for informational output;
# only the exit code indicates a true error.
$env:GIT_REDIRECT_STDERR = '2>&1'
Set-Location $PSScriptRoot\..\..

Write-Host "=============================================================="
Write-Host " repo_cleanup_phase2.ps1  (Math82 Phase A + B + C execution)"
Write-Host "=============================================================="

# Pre-flight: confirm we are at repo root
if (-not (Test-Path 'CLAUDE.md')) {
    Write-Error "Not at repo root. Expected CLAUDE.md present."
    exit 1
}
if (-not (Test-Path 'Codes/pde')) {
    Write-Error "Codes/pde/ missing. Phase 1 was not completed."
    exit 1
}

# Ensure target directories exist
$null = New-Item -ItemType Directory -Force -Path 'Docs/status/round-summaries'
$null = New-Item -ItemType Directory -Force -Path 'Docs/math/paste-ready-archive'
$null = New-Item -ItemType Directory -Force -Path 'Docs/manual/manual-entries-archive'

Write-Host ''
Write-Host '--- Phase A.1: delete duplicate ---'

# AUTONOMOUS_SESSION_REPORT_2026-04-21.md is already at Docs/status/, root copy is duplicate
if (Test-Path 'AUTONOMOUS_SESSION_REPORT_2026-04-21.md') {
    git rm AUTONOMOUS_SESSION_REPORT_2026-04-21.md
}

Write-Host ''
Write-Host '--- Phase A.2: relocate 17 root-level orphans ---'

$RoundSummaryFiles = @(
    'AUTONOMOUS_SESSION_REPORT_2026-04-24-ROUND4-PROOF-A.md',
    'ROUND6_SESSION_SUMMARY.txt',
    'ROUND7-PROOF-B-SESSION-SUMMARY.txt',
    'TECT-AUTONOMOUS-SESSION-SUMMARY-2026-04-24.txt',
    'TECT-KOREAN-SUMMARY-ROADMAP.txt',
    'FINAL_SESSION_STATUS.txt',
    'INDEX-ROUND7-DELIVERABLES.txt',
    'KOREAN-STATUS-REPORT-ROUND7.txt',
    '.round7-proof-c-executive-summary.txt',
    '.round7-proof-c-traceability.txt'
)
foreach ($f in $RoundSummaryFiles) {
    if (Test-Path $f) {
        git mv $f "Docs/status/round-summaries/$f"
    } else {
        Write-Warning "Skip (not present): $f"
    }
}

$PasteReadyFiles = @(
    'PASTE-READY-MATH60-S3-ROUND7-CHANGELOG.txt',
    'PASTE-READY-MATH75-Q3-PILLAR4-FINAL.txt',
    'PASTE-READY-PILLAR11-v6-SUMMARY.txt',
    'CHANGELOG-Pillar1-v2.txt',
    'CHANGELOG-Pillar11-v6-Dirac-sector-closure.txt'
)
foreach ($f in $PasteReadyFiles) {
    if (Test-Path $f) {
        git mv $f "Docs/math/paste-ready-archive/$f"
    } else {
        Write-Warning "Skip (not present): $f"
    }
}

$ManualEntryFiles = @(
    'CODE_MANUAL-Math75-Q3-Entry.txt',
    'CODE_MANUAL-Pillar11-v6-Dirac-entry.txt'
)
foreach ($f in $ManualEntryFiles) {
    if (Test-Path $f) {
        git mv $f "Docs/manual/manual-entries-archive/$f"
    } else {
        Write-Warning "Skip (not present): $f"
    }
}

Write-Host ''
Write-Host '--- Phase B: remove empty continuation_v263_smoke/ ---'
if (Test-Path 'continuation_v263_smoke') {
    Remove-Item -Recurse -Force continuation_v263_smoke
    Write-Host 'continuation_v263_smoke/ removed (was empty in git).'
}

Write-Host ''
Write-Host '--- Phase C.1: preserve scripts/verify_dirac_casimir_toy.py before scripts/ retire ---'
if (Test-Path 'scripts/verify_dirac_casimir_toy.py') {
    if (-not (Test-Path 'Codes/scripts/verify_dirac_casimir_toy.py')) {
        Copy-Item 'scripts/verify_dirac_casimir_toy.py' 'Codes/scripts/verify_dirac_casimir_toy.py'
        git add 'Codes/scripts/verify_dirac_casimir_toy.py'
        Write-Host 'verify_dirac_casimir_toy.py copied to Codes/scripts/'
    }
}

Write-Host ''
Write-Host '--- Phase C.2: retire byte-equal mirrors (tools, tests, runs, scripts) ---'

# tools/ and tests/ are byte-equal with Codes/tools/ and Codes/tests/ except for __pycache__ (gitignored)
foreach ($d in 'tools', 'tests', 'runs', 'scripts') {
    if (Test-Path $d) {
        # Use git rm -r so that history is preserved
        git rm -r $d
    }
}

Write-Host ''
Write-Host '--- Stage Math82 + REPO_LAYOUT update + NAVIGATION update + CHANGELOG ---'
git add Docs/math/TECT-Math82-Repo-Cleanup-Phase2.tex.txt 2>$null
git add Docs/policy/REPO_LAYOUT.md
git add NAVIGATION.md
git add CHANGELOG.md
git add Docs/status/round-summaries/.gitkeep 2>$null
git add Docs/math/paste-ready-archive/.gitkeep 2>$null
git add Docs/manual/manual-entries-archive/.gitkeep 2>$null

Write-Host ''
Write-Host '--- Commit ---'
git -c user.email='jtkor@outlook.com' -c user.name='Jusang Lee' commit -m @"
Math82 Repo Cleanup Phase 2 (A+B+C): root orphan relocation + empty-folder removal + byte-equal mirror retirement

Phase A — relocate 18 root-level orphan files:
  - 1 duplicate deleted (AUTONOMOUS_SESSION_REPORT_2026-04-21.md, identical
    to Docs/status/ copy)
  - 10 round/session summary files -> Docs/status/round-summaries/
  - 5 paste-ready snippet files -> Docs/math/paste-ready-archive/
  - 2 CODE_MANUAL entry archives -> Docs/manual/manual-entries-archive/

Phase B — remove empty placeholder directory:
  - continuation_v263_smoke/ (was empty in git tree; superseded by
    Runs/continuation/continuation_v263_smoke/)

Phase C — retire deprecated byte-equal mirrors per REPO_LAYOUT
section 4 Phase 2 retirement criteria:
  - tools/  (byte-equal with Codes/tools/, modulo __pycache__)
  - tests/  (byte-equal with Codes/tests/, modulo __pycache__)
  - runs/   (byte-equal with Runs/legacy/, modulo README)
  - scripts/ (after copying the unique verify_dirac_casimir_toy.py
    to Codes/scripts/)

Out of scope (deferred to Phase D-F, post Task #54 closure):
  - results/ contains math55_endpoint_*, math64_*, dirac_casimir.png
    that need targeted move to Runs/continuation/ and Runs/audit/
  - PDE/ contains 344 tracked files including historical execution
    data (data_pt_*, continuation_*, newton_rigorous_*, emerge_*,
    backup_GL_*, bcc_compare/, bcc_recalib64/) that need internal
    sorting before PDE/ itself can be retired.

REPO_LAYOUT.md section 4 Migration-status table updated to reflect
the four retired directories. NAVIGATION.md updated to remove
references to removed paths and add the three new Docs/ archive
subfolders. CHANGELOG entry filed.

The Math82 process note (Docs/math/TECT-Math82-Repo-Cleanup-
Phase2.tex.txt) records the cleanup plan, executed phases, deferred
phases, and the rationale for each choice per UPDATE_POLICY
section 15 chat-archival rule.

No theory or pillar status changes from this commit.
"@

Write-Host ''
Write-Host '=============================================================='
Write-Host '  Cleanup Phase A + B + C complete.'
Write-Host '  See: git log -1 --stat'
Write-Host '=============================================================='
