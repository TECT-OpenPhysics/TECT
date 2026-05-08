@echo off
:: ============================================================
:: TECT Full Gate Pipeline — Unified Runner
:: ============================================================
:: Run from: C:\Dev\TECT2\Contents\PDE\
::
:: This script runs ALL three TECT gate extractions in sequence:
::   1. Solver convergence check + checkpoint continuation
::   2. n*=1 pipeline (Gate 1 + within-patch Gate 2/3)
::   3. Intervalley v4 (cross-patch Gate 2/3 via 6×6 Hessian)
::   4. m* extractor (effective mass)
::
:: Prerequisites:
::   - run_finetune_bcc_ideal/ must exist with Psi_corr.npy
::   - Python 3.10+ with PyTorch
:: ============================================================

set RUN_DIR=run_finetune_bcc_ideal
set BACKEND=real_backend_pt_bcc_mixed_v3.py

echo ============================================================
echo  TECT Full Gate Pipeline
echo ============================================================
echo.

:: Step 0: Check solver status
echo [Step 0] Checking solver convergence...
python -c "
import numpy as np, os, sys
run = '%RUN_DIR%'
if not os.path.isdir(run):
    print(f'  ERROR: {run} not found. Run solver first.')
    sys.exit(1)
res = np.load(f'{run}/residual_history.npy')
en = np.load(f'{run}/energy_history.npy')
psi = np.load(f'{run}/Psi_corr.npy')
rms = float(np.sqrt((np.abs(psi)**2).mean()))

# Power spectrum check
N = psi.shape[-1]
fft = np.fft.fftn(psi[0])
nx = np.fft.fftfreq(N, 1.0/N).astype(int)
Nx,Ny,Nz = np.meshgrid(nx,nx,nx,indexing='ij')
n2 = Nx**2+Ny**2+Nz**2
power = np.abs(fft)**2
total = power.sum()
p2 = float(power[n2==2].sum()/total)
p3 = float(power[n2==3].sum()/total)

print(f'  Steps: {len(res)}')
print(f'  Residual final: {res[-1]:.4e}  (min: {res.min():.4e})')
print(f'  Energy final: {en[-1]:.6e}  ({\"NEGATIVE\" if en[-1]<0 else \"POSITIVE\"})')
print(f'  Psi rms: {rms:.4e}')
print(f'  BCC |n|^2=2: {p2*100:.1f}%%,  SC |n|^2=3: {p3*100:.1f}%%')
print()

if res[-1] > 1e-3:
    print('  WARNING: Residual > 1e-3. Consider running more steps.')
    print('  Recommended: continue from checkpoint with 20000 more steps')
    print()
    print('  python tect_solver_pt_v3.py ^')
    print(f'    --grid {N} --L 16.0 ^')
    print(f'    --backend {\"real_backend_pt_bcc_mixed_v3.py\"} ^')
    print(f'    --init {run}\\Psi_corr.npy ^')
    print(f'    --init-mode external ^')
    print(f'    --output {run}_continued ^')
    print('    --steps 20000 --dt 1e-3 --tol 1e-8 ^')
    print('    --device cpu --laplacian-mode mixed_bcc --seed 42')
    sys.exit(1)
elif en[-1] >= 0:
    print('  WARNING: Energy still positive. BCC condensate may not have formed.')
    print('  Continue solver or check parameters.')
    sys.exit(1)
else:
    print('  Solver converged. Proceeding with extraction.')
"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Solver check failed. Fix issues above before proceeding.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  [Step 1] n*=1 Pipeline (Gate 1 + within-patch Gate 2/3)
echo ============================================================
echo.
python run_pipeline_n1.py ^
    --input %RUN_DIR% ^
    --backend %BACKEND% ^
    --output %RUN_DIR%\pipeline_n1_out ^
    --dk_steps 2 ^
    --r_patch_frac 0.80 ^
    --n_sample 50 ^
    --rho_decomp 0.20

echo.
echo ============================================================
echo  [Step 2] Intervalley v4 (cross-patch Gate 2/3 via 6x6 Hessian)
echo ============================================================
echo.
python intervalley_extractor_v4.py ^
    --input %RUN_DIR% ^
    --backend %BACKEND% ^
    --output %RUN_DIR%\intervalley_v4_out ^
    --dk-steps 1 ^
    --eta-par 0.01 ^
    --eta-trans 0.01

echo.
echo ============================================================
echo  [Step 3] m* Extractor (effective mass)
echo ============================================================
echo.
python tect_actual_extractor_pt_v3.py ^
    --input %RUN_DIR% ^
    --backend %BACKEND% ^
    --output %RUN_DIR%\mstar_out

echo.
echo ============================================================
echo  [Step 4] Final Summary
echo ============================================================
echo.
python -c "
import json, os, numpy as np

run = '%RUN_DIR%'
print('=' * 72)
print('TECT COMPREHENSIVE GATE SUMMARY')
print('=' * 72)
print()

# n*=1 results
n1_path = os.path.join(run, 'pipeline_n1_out', 'pipeline_n1_summary.json')
if os.path.exists(n1_path):
    with open(n1_path) as f:
        n1 = json.load(f)
    gs = n1.get('gate_summary', {})
    print('[n*=1 Pipeline]')
    print(f'  Gate 1 (spectral gap):      {\"PASS\" if gs.get(\"Gate1_pass\") else \"FAIL\"}')
    print(f'  Gate 2 (within-patch long):  {\"PASS\" if gs.get(\"Gate2_pass\") else \"FAIL\"}')
    print(f'  Gate 3 (within-patch trans): {\"PASS\" if gs.get(\"Gate3_pass\") else \"FAIL\"}')
    d = n1.get('stage_U2b_dirac', {})
    print(f'  lambda_par mean: {d.get(\"lambda_par_mean\", \"N/A\")}')
else:
    print('[n*=1 Pipeline] NOT RUN')

print()

# Intervalley v4 results
v4_path = os.path.join(run, 'intervalley_v4_out', 'intervalley_v4_summary.json')
if os.path.exists(v4_path):
    with open(v4_path) as f:
        v4 = json.load(f)
    print('[Intervalley v4]')
    max_lp = max(r['ell_cross_par'] for r in v4) if v4 else 0
    max_l1 = max(r['ell_cross_1'] for r in v4) if v4 else 0
    max_l2 = max(r['ell_cross_2'] for r in v4) if v4 else 0
    max_lt = max(max_l1, max_l2)
    g2 = any(r['gate2_pass'] for r in v4)
    g3 = any(r['gate3_pass'] for r in v4)
    print(f'  Gate 2 (cross-patch long):   {\"PASS\" if g2 else \"FAIL\"}  (ell_par = {max_lp:.4e})')
    print(f'  Gate 3 (cross-patch trans):  {\"PASS\" if g3 else \"FAIL\"}  (ell_trans = {max_lt:.4e})')
    m_vals = [r['m_scalar'] for r in v4]
    print(f'  m_scalar mean:               {np.mean(m_vals):.4e}')
    m2_vals = [r['m2_diag_par'] for r in v4]
    print(f'  m2_diag(par) mean:           {np.mean(m2_vals):.4e}')
else:
    print('[Intervalley v4] NOT RUN')

print()

# m* results
ms_path = os.path.join(run, 'mstar_out', 'extraction_metadata.json')
if os.path.exists(ms_path):
    with open(ms_path) as f:
        ms = json.load(f)
    s = ms.get('summary', {})
    print('[m* Extractor]')
    print(f'  phase_status: {ms.get(\"phase_status\", \"N/A\")}')
    print(f'  M2 = {s.get(\"M2\", \"N/A\")}')
    print(f'  m* = {s.get(\"mstar\", \"N/A\")}')
    print(f'  m*^2 = {s.get(\"mstar2\", \"N/A\")}')
    print(f'  g_eff = {s.get(\"geff\", \"N/A\")}')
else:
    print('[m* Extractor] NOT RUN')

print()
print('=' * 72)
print('TARGET: m* = 0.3138')
print('=' * 72)
"

echo.
pause
