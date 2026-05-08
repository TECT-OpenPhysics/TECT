# =====================================================================
# run_math92_numerical_checklist.ps1
# Theory tag : Math92 §8 numerical-execution trigger checklist runbook
# Date       : 2026-04-24
# Maintainer : Jusang Lee (jtkor@outlook.com)
#
# PURPOSE
#   Single PowerShell script grouping the 5 GPU/CPU runs that unlock
#   Pillar 4 / Pillar 6 / Pillar 11 / Stage-2-B / Stage-2-D / Stage-3-F1
#   per Math92 §8. Sections are independent — run any subset.
#
# USAGE (from C:\Dev\TECT2\Contents in PowerShell):
#     powershell -ExecutionPolicy Bypass -File Codes\scripts\run_math92_numerical_checklist.ps1 -Run pretest
#     powershell -ExecutionPolicy Bypass -File Codes\scripts\run_math92_numerical_checklist.ps1 -Run proper
#     powershell -ExecutionPolicy Bypass -File Codes\scripts\run_math92_numerical_checklist.ps1 -Run extractor
#     powershell -ExecutionPolicy Bypass -File Codes\scripts\run_math92_numerical_checklist.ps1 -Run rge
#     powershell -ExecutionPolicy Bypass -File Codes\scripts\run_math92_numerical_checklist.ps1 -Run lambda
#     powershell -ExecutionPolicy Bypass -File Codes\scripts\run_math92_numerical_checklist.ps1 -Run all
#
# COSTS (approximate, local GPU)
#     pretest   : 4 runs   ~10 min     workflow validation only
#     proper    : 56 runs  ~3-6 hours  Math82-I DECISIVE branch-existence test
#     extractor : N runs   ~1 min/run  per-branch fixed-point check (after proper)
#     rge       : 1 run    ~2-4 hours  Pillar 4 Q2 numerical RGE
#     lambda    : 1 run    ~1 min      Pillar 11 Q5 4-sector audit
#
# OUTPUT DIRECTORIES (all under Runs/continuation/ or Runs/audit/)
# =====================================================================

param(
    [ValidateSet("pretest", "proper", "extractor", "rge", "lambda", "all")]
    [string]$Run = "pretest"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
Set-Location $RepoRoot
Write-Host "Repo root: $RepoRoot" -ForegroundColor Cyan
Write-Host "Run mode : $Run"            -ForegroundColor Cyan

# ---------------------------------------------------------------------
# 1. Math82-I PRETEST  (4 runs, subset-4 random phase, ~10 minutes)
# ---------------------------------------------------------------------
function Run-Pretest {
    Write-Host "`n=== [1] Math82-I-pretest (4 runs, subset-4 random phase) ===" -ForegroundColor Magenta
    $datestamp = Get-Date -Format "yyyy-MM-dd"
    foreach ($mu2 in @("-0.1", "-0.7")) {
        foreach ($r in 1..2) {
            $seedFile = "Runs\seeds\Psi_subset4_rand_r${r}.npy"
            $outDir   = "Runs\continuation\math82I_pretest_mu2_${mu2}_r${r}_${datestamp}"
            Write-Host "`n  -> mu2=$mu2 replica=$r"
            python -u Codes\pde\bcc_analytic_seed.py `
                --mode subset_4cosine_random_phase --N 32 --L 62.20036 `
                --phase-seed $r --output $seedFile
            python -u Codes\pde\continuation_mu2_v25.py `
                --config Codes\pde\config_template_brazovskii.json `
                --N 32 --L 62.20036 --mu2 $mu2 `
                --tol-newton 1e-7 --max-newton 20 --tcg-max 3000 `
                --load-psi $seedFile `
                --output $outDir
        }
    }
    Write-Host "`n[1] Pretest complete. Inspect Runs\continuation\math82I_pretest_*." -ForegroundColor Green
}

# ---------------------------------------------------------------------
# 2. Math82-I PROPER  (56 runs, full-12 random phase, ~3-6 hours)
# ---------------------------------------------------------------------
function Run-Proper {
    Write-Host "`n=== [2] Math82-I-proper (56 runs, full-12 random phase) ===" -ForegroundColor Magenta
    Write-Host "    EXPECTED RUNTIME: 3-6 hours. Cancellable mid-stream (each run is independent)." -ForegroundColor Yellow
    $datestamp = Get-Date -Format "yyyy-MM-dd"
    foreach ($mu2 in @("5e-3", "-0.02", "-0.1", "-0.5", "-0.7", "-0.85", "-1.0")) {
        foreach ($r in 1..8) {
            $seedFile = "Runs\seeds\Psi_full12_rand_r${r}.npy"
            $outDir   = "Runs\continuation\math82I_proper_mu2_${mu2}_r${r}_${datestamp}"
            Write-Host "`n  -> mu2=$mu2 replica=$r/8"
            python -u Codes\pde\bcc_analytic_seed.py `
                --mode full_12cosine_random_phase --N 32 --L 62.20036 `
                --phase-seed $r --output $seedFile
            python -u Codes\pde\continuation_mu2_v25.py `
                --config Codes\pde\config_template_brazovskii.json `
                --N 32 --L 62.20036 --mu2 $mu2 `
                --tol-newton 1e-7 --max-newton 20 --tcg-max 3000 `
                --load-psi $seedFile `
                --output $outDir
        }
    }
    Write-Host "`n[2] Math82-I-proper complete. Run Math82_I_coldstart_analysis.py + branch-clustering next." -ForegroundColor Green
}

# ---------------------------------------------------------------------
# 3. Math36-extractor  (per-branch RG flow extraction, ~1 min/run)
# ---------------------------------------------------------------------
function Run-Extractor {
    Write-Host "`n=== [3] Math36-extractor (per-branch RG flow) ===" -ForegroundColor Magenta
    Write-Host "    REQUIRES: at least one converged Psi_star.npy (from Math82-H or Math82-I-proper)" -ForegroundColor Yellow
    $datestamp = Get-Date -Format "yyyy-MM-dd"
    # Default: extract from Math82-H Point 1 (always-converged metastable Psi*)
    $defaultPsi = "Runs\continuation\math82H_groundstate_N32_Lbcc7_2026-04-24\Psi_star_point1.npy"
    if (Test-Path $defaultPsi) {
        Write-Host "  -> extracting from Math82-H Point 1 metastable Psi*"
        python -u Codes\supplementary\Math36_RG_extractor.py `
            --input $defaultPsi `
            --output "Runs\audit\math36_extractor_point1_${datestamp}.json"
    } else {
        Write-Host "  WARNING: $defaultPsi not found; manually edit -input to a converged .npy" -ForegroundColor Yellow
    }
    Write-Host "`n[3] Extractor complete. Inspect JSON for fixed-point classification." -ForegroundColor Green
}

# ---------------------------------------------------------------------
# 4. Math75-Q2-AddA RGE solver  (alpha_i(M_Z) numerical, ~2-4 hours)
# ---------------------------------------------------------------------
function Run-Rge {
    Write-Host "`n=== [4] Math75-Q2-AddA RGE solver (Pillar 4 Q2 numerical) ===" -ForegroundColor Magenta
    Write-Host "    EXPECTED RUNTIME: 2-4 hours; output: alpha_i(M_Z) at PDG +/- 5%" -ForegroundColor Yellow
    python -u Codes\supplementary\Math75_Q2_RG_integration.py --integrate --report
    Write-Host "`n[4] RGE solver complete. Check report JSON for status flag (PROVED/PARTIAL/FALSIFIED)." -ForegroundColor Green
}

# ---------------------------------------------------------------------
# 5. Math58-v7-AddB lambda-cancellation audit  (Pillar 11 Q5, ~1 min)
# ---------------------------------------------------------------------
function Run-Lambda {
    Write-Host "`n=== [5] Math58-v7-AddB lambda-cancellation 4-sector audit ===" -ForegroundColor Magenta
    python -u Codes\supplementary\Math58_v7_lambda_cancellation_audit.py
    Write-Host "`n[5] Lambda audit complete. Inspect output for total cancellation gate." -ForegroundColor Green
}

# ---------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------
switch ($Run) {
    "pretest"   { Run-Pretest }
    "proper"    { Run-Proper }
    "extractor" { Run-Extractor }
    "rge"       { Run-Rge }
    "lambda"    { Run-Lambda }
    "all" {
        Run-Pretest
        Run-Proper
        Run-Extractor
        Run-Rge
        Run-Lambda
    }
}

Write-Host "`nAll requested runs complete." -ForegroundColor Cyan
