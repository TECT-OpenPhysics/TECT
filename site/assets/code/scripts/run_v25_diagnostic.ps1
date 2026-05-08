# ==============================================================================
# TECT v2.5 Newton-Krylov Diagnostic — Local Windows/PowerShell Handoff Script
# ==============================================================================
# Trigger : v2.4 continuation failure at mu^2=-1.0 (manifest R-2026-04-21-002)
#           Sandbox cannot install PyTorch (D-2026-04-21-001 environmental blocker).
# Evidence: PDE/continuation_N32_v2p4.log; inner GMRES saturates at tCG=15000.
# Decision: Execute Math63 v2.5 diagnostic sweep locally (6 points: mu^2 in
#           {-1.0, -0.8, -0.6, -0.4, -0.2, -0.1}) on user's machine where the
#           existing Python/PyTorch environment is functional.
# Math note: Docs/math/TECT-Math63-Solver-Redesign-v2.5.tex.txt
# ==============================================================================

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot\..

# Banner
Write-Host "============================================================"
Write-Host " TECT v2.5 Newton-Krylov Diagnostic — 6-point sweep"
Write-Host " Target acceptance: Newton <= 8 iter, tCG <= 300, rho_lin <= 0.05"
Write-Host "============================================================"

# --- Stage 0 :: Environment probe ----------------------------------------------
Write-Host "`n[0/4] Python + PyTorch environment probe..."
try {
    $pyinfo = python -c "import sys, torch; print('Python:', sys.version.split()[0]); print('torch:', torch.__version__); print('CUDA:', torch.cuda.is_available())"
    Write-Host $pyinfo
} catch {
    Write-Error "PyTorch not found. Activate the venv used for v2.4 runs, then retry."
    exit 1
}

# --- Stage 1 :: Constants self-check -------------------------------------------
Write-Host "`n[1/4] Math56 constants consistency self-check..."
python -c "from PDE.math56_constants import assert_consistency; assert_consistency(); print('PASS: assert_consistency() OK')"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Math56 constants inconsistent — HALT. Run theory-currency audit before retrying."
    exit 2
}

# --- Stage 2 :: Preconditioner & symmetry-probe self-tests ---------------------
Write-Host "`n[2/4] BZ preconditioner self-test..."
python -m PDE.bz_preconditioner
if ($LASTEXITCODE -ne 0) { Write-Error "bz_preconditioner self-test FAILED."; exit 3 }

Write-Host "`n    Jacobian symmetry-probe self-test..."
# NOTE 2026-04-22: We invoke the file directly rather than via `python -m
# tools.xxx`. Background: on the user's Windows / Python 3.12 env the call
# `python -m tools.check_jacobian_symmetry` raised `ModuleNotFoundError: No
# module named 'tools'` even after `tools/__init__.py` was added, while the
# sibling `python -m PDE.xxx` worked. The file-path form is immune to
# whatever is suppressing `tools/` from sys.path resolution (case-insensitive
# FS collision with CPython's `Tools/` directory is the leading hypothesis).
python tools/check_jacobian_symmetry.py --selftest
if ($LASTEXITCODE -ne 0) { Write-Error "check_jacobian_symmetry self-test FAILED."; exit 4 }

# --- Stage 3 :: Diagnostic continuation ----------------------------------------
$outdir = "runs/R-2026-04-22-001-newton-krylov-v25-diagnostic"
New-Item -ItemType Directory -Force -Path $outdir | Out-Null

Write-Host "`n[3/4] Launching 6-point diagnostic sweep..."
Write-Host "      mu^2 in {-1.0, -0.8, -0.6, -0.4, -0.2, -0.1} at N=32"
Write-Host "      Output dir: $outdir"

# NOTE 2026-04-22: we do NOT pass `--mu2_list` — it was never part of the
# continuation_mu2_v25.py CLI. The `--diagnostic` flag is self-sufficient: it
# hardcodes exactly the 6-point schedule {-1.0, -0.8, -0.6, -0.4, -0.2, -0.1}
# at continuation_mu2_v25.py line ~504. Passing `--mu2_list` raised
# `argparse: error: unrecognized arguments` and aborted Stage [4/4]
# (exit code 2) on the first local run at 2026-04-22. Removal restores the
# caller/callee CLI contract specified in Math63 §7.
$t0 = Get-Date
python PDE/continuation_mu2_v25.py `
    --N 32 `
    --diagnostic `
    --output $outdir `
    --config PDE/config_template_brazovskii.json
$exit = $LASTEXITCODE
$wall = (Get-Date) - $t0

Write-Host "`n[4/4] Diagnostic complete in $($wall.TotalSeconds) s (exit $exit)."

# --- Results archival ----------------------------------------------------------
# v2.5.3 / v2.6.4: main() in continuation_mu2_v25.py returns a tri-state
# exit code. The numeric contract is preserved bit-identically across
# renames; v2.6.4 renames the status string for exit 10 from
# `SKELETON_ONLY` to `NO_CONVERGENCE` for semantic accuracy (the driver
# is no longer a skeleton as of v2.6.3).
#
#   0  -> PASS            : every scheduled μ² point converged under the
#                           Math63 §2D / Math64 §sec2d acceptance gate.
#   10 -> NO_CONVERGENCE  : run completed without raising, but no point
#                           reached tol_newton. v2.6.4 reserves this for
#                           (a) solver-core unavailable (torch / backend
#                           / GPU not importable) or (b) genuine physical
#                           non-convergence on every scheduled μ².
#                           v2.6.3-b's `SKELETON_ONLY` wording is retired;
#                           the driver has not been a skeleton since
#                           Math74 v2.6.3 landed.
#   other -> FAIL         : at least one point raised, or overall_status
#                           was UNKNOWN.
if ($exit -eq 0) {
    Write-Host "`n*** v2.6.4 DIAGNOSTIC: PASS ***"
    Write-Host "All scheduled points converged under the Math63 §2D /"
    Write-Host "Math64 §sec2d acceptance gate (v2.6.4 calibration)."
    Write-Host "Populate $outdir\MANIFEST.md narrative if any additional"
    Write-Host "physics interpretation is desired, then:"
    Write-Host "  python tools/build_version_index.py"
    Write-Host "  .\scripts\commit_v25_diagnostic.ps1"
} elseif ($exit -eq 10) {
    Write-Warning "*** v2.6.4 DIAGNOSTIC: NO_CONVERGENCE (exit 10) ***"
    Write-Warning "No scheduled μ² point converged under the Math63 §2D /"
    Write-Warning "Math64 §sec2d gate. Possible causes:"
    Write-Warning "  (a) PyTorch / tect_newton_krylov solver-core not"
    Write-Warning "      importable on this host;"
    Write-Warning "  (b) GPU out-of-memory or backend compile failure;"
    Write-Warning "  (c) genuine physical non-convergence on every μ²."
    Write-Warning "Open $outdir\MANIFEST.md for the per-point table (v2.6.4"
    Write-Warning "now includes ``gate / tCG_peak / rho_trust_min`` columns)."
    Write-Warning "Do NOT run commit_v25_diagnostic.ps1 on a NO_CONVERGENCE run."
} else {
    Write-Warning "*** v2.6.4 DIAGNOSTIC: FAIL (exit $exit) ***"
    Write-Warning "At least one continuation point errored. Inspect"
    Write-Warning "  $outdir\MANIFEST.md for the per-point table."
    Write-Warning "Open question Q-2026-04-22-SolverFit should be filed in"
    Write-Warning "  Docs/status/OPEN-QUESTIONS.md if the error reproduces."
}

exit $exit
