# ==============================================================================
# TECT v2.5 Diagnostic Result — Commit Stamper
# ==============================================================================
# Trigger : Completion of v2.5 diagnostic (runs/R-2026-04-22-001-...).
# Evidence: R-2026-04-22-001/MANIFEST.md, per-point JSON outputs.
# Decision: Stamp the diagnostic result into git history with a signed,
#           traceable commit, tag the revision, and emit the SHA for
#           cross-reference from Math63 and CHANGELOG.
# Math note: Docs/math/TECT-Math63-Solver-Redesign-v2.5.tex.txt
# ==============================================================================

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot\..

if (-not (Test-Path .git)) { Write-Error "Run git_bootstrap.ps1 first."; exit 10 }

$outdir = "runs\R-2026-04-22-001-newton-krylov-v25-diagnostic"
if (-not (Test-Path $outdir)) { Write-Error "Diagnostic output dir missing: $outdir"; exit 11 }
if (-not (Test-Path "$outdir\MANIFEST.md")) { Write-Error "MANIFEST.md missing in $outdir"; exit 12 }

# Parse manifest status
$manifest = Get-Content "$outdir\MANIFEST.md" -Raw
if ($manifest -match "status:\s*PASS") {
    $status = "PASS"
    $tag = "v2p5-diagnostic-pass"
} elseif ($manifest -match "status:\s*FAIL") {
    $status = "FAIL"
    $tag = "v2p5-diagnostic-fail"
} else {
    Write-Error "MANIFEST.md does not contain status: PASS or status: FAIL"
    exit 13
}

# Stage artifacts
git add $outdir
git add CHANGELOG.md Docs/status/research-log.md 2>$null
git add website/data/history.js website/data/records.js 2>$null

# Construct commit message
$msg = @"
v2.5 diagnostic $status — R-2026-04-22-001

Trigger : Math63 v2.5 solver redesign reached acceptance stage.
Evidence: $outdir/MANIFEST.md (status=$status)
Decision: Stamp the result into git history; link R-tag bidirectionally
          to Math63, CHANGELOG, research-log, and the website ledgers.
Retires : v2.4 continuation_mu2.py (superseded by v2.5 on PASS; kept for
          comparison runs; tagged as deprecated in PDE/deprecated/ after
          follow-up commit once v2.5 is validated at N=64).
Math note: Docs/math/TECT-Math63-Solver-Redesign-v2.5.tex.txt
"@
git commit -m $msg

# Tag the milestone
git tag -a $tag -m "v2.5 diagnostic outcome: $status ($(Get-Date -Format yyyy-MM-dd))"

Write-Host "`nCommit SHA:"
$sha = git rev-parse HEAD
Write-Host "  $sha"
Write-Host "Tag: $tag"
Write-Host "`nNow update Math63 §4 and CHANGELOG with this SHA to seal the bidirectional link."
