@echo off
:: TECT BCC Solver — Checkpoint Diagnostics & Continuation
:: Run from: C:\Dev\TECT2\Contents\PDE\
:: Purpose: Check run_finetune_bcc_ideal status, then continue if needed

echo ============================================================
echo  TECT BCC Solver — Checkpoint Status
echo ============================================================
echo.

:: Step 1: Diagnose current run
python -c "
import numpy as np, os, sys

run1 = 'run_finetune_bcc_ideal'
run2 = 'run_finetune_bcc_ideal_2'

for run in [run1, run2]:
    print(f'=== {run} ===')
    if not os.path.isdir(run):
        print('  NOT FOUND (not run yet)')
        continue

    res_path = os.path.join(run, 'residual_history.npy')
    en_path  = os.path.join(run, 'energy_history.npy')
    psi_path = os.path.join(run, 'Psi_corr.npy')

    if not os.path.exists(res_path):
        print('  residual_history.npy not found')
        continue

    res = np.load(res_path)
    en  = np.load(en_path)
    psi = np.load(psi_path)
    rms = float(np.sqrt((np.abs(psi)**2).mean()))

    print(f'  Steps: {len(res)}')
    print(f'  Residual: final={res[-1]:.4e}, min={res.min():.4e} @ step {res.argmin()}')
    print(f'  Energy:   final={en[-1]:.6e} ({'NEGATIVE=CONDENSED' if en[-1]<0 else 'POSITIVE=DISORDERED'})')
    print(f'  Psi rms:  {rms:.4e}')

    # Power spectrum
    N = psi.shape[-1]
    fft = np.fft.fftn(psi[0])
    nx = np.fft.fftfreq(N, 1.0/N).astype(int)
    Nx,Ny,Nz = np.meshgrid(nx,nx,nx,indexing='ij')
    n2 = Nx**2+Ny**2+Nz**2
    power = np.abs(fft)**2
    total = power.sum()
    p2 = float(power[n2==2].sum()/total)
    p3 = float(power[n2==3].sum()/total)
    print(f'  BCC |n|^2=2: {p2*100:.1f}%,  SC |n|^2=3: {p3*100:.1f}%')
    if p2 > 0.5:
        print('  ** BCC ORDERING CONFIRMED **')
    elif p3 > 0.5:
        print('  ** WARNING: SC/FCC ordering dominates (wrong vacuum) **')
    print()
"

:: Step 2: Decision tree
echo.
echo ============================================================
echo  CONTINUATION COMMANDS (copy and run as needed)
echo ============================================================
echo.
echo [A] If run_finetune_bcc_ideal is done AND energy negative:
echo     Run extractor on it:
echo     python tect_actual_extractor_pt_v3.py --run-dir run_finetune_bcc_ideal --field-key Psi_corr
echo.
echo [B] If run_finetune_bcc_ideal is still running / not enough steps:
echo     Continue from checkpoint (20000 more steps):
echo.
echo     python tect_solver_pt_v3.py ^
echo       --grid 64 --L 16.0 ^
echo       --backend real_backend_pt_bcc_mixed_v3.py ^
echo       --init run_finetune_bcc_ideal\Psi_corr.npy ^
echo       --init-mode external ^
echo       --output run_finetune_bcc_ideal_2 ^
echo       --steps 20000 --dt 1e-3 --tol 1e-8 ^
echo       --device cpu --laplacian-mode mixed_bcc --seed 42
echo.
echo [C] If BCC ordering fails (p2 less than 50 percent after 20000 steps):
echo     Try with smaller dt=5e-4 and longer run:
echo.
echo     python tect_solver_pt_v3.py ^
echo       --grid 64 --L 16.0 ^
echo       --backend real_backend_pt_bcc_mixed_v3.py ^
echo       --init Psi_BCC_A025_seed.npy ^
echo       --init-mode external ^
echo       --output run_finetune_bcc_slowdt ^
echo       --steps 30000 --dt 5e-4 --tol 1e-8 ^
echo       --device cpu --laplacian-mode mixed_bcc --seed 42
echo.
echo ============================================================
echo  AFTER SUCCESSFUL CONVERGENCE: Run extractor
echo ============================================================
echo.
echo     python tect_actual_extractor_pt_v3.py ^
echo       --run-dir [CONVERGED_RUN_DIR] --field-key Psi_corr
echo.
echo     Then check: M2 > 0, m_parallel > 0
echo     Compare with target: m* = 0.3138
echo.
pause
