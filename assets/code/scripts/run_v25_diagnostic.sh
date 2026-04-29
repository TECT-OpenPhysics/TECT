#!/usr/bin/env bash
# ==============================================================================
# TECT v2.5 Newton-Krylov Diagnostic — Local Linux/macOS Handoff Script
# ==============================================================================
# Trigger : v2.4 continuation failure at mu^2=-1.0 (manifest R-2026-04-21-002)
# Evidence: PDE/continuation_N32_v2p4.log; GMRES saturates at tCG=15000.
# Decision: Execute Math63 v2.5 diagnostic sweep (6 points) locally.
# Math note: Docs/math/TECT-Math63-Solver-Redesign-v2.5.tex.txt
# ==============================================================================

set -euo pipefail
cd "$(dirname "$0")/.."

echo "============================================================"
echo " TECT v2.5 Newton-Krylov Diagnostic — 6-point sweep"
echo " Target acceptance: Newton <= 8 iter, tCG <= 300, rho_lin <= 0.05"
echo "============================================================"

echo
echo "[0/4] Python + PyTorch environment probe..."
python - <<'PY'
import sys, torch
print("Python:", sys.version.split()[0])
print("torch :", torch.__version__)
print("CUDA  :", torch.cuda.is_available())
PY

echo
echo "[1/4] Math56 constants consistency self-check..."
python -c "from PDE.math56_constants import assert_consistency; assert_consistency(); print('PASS: assert_consistency() OK')"

echo
echo "[2/4] BZ preconditioner + Jacobian symmetry-probe self-tests..."
python -m PDE.bz_preconditioner
python -m tools.check_jacobian_symmetry --selftest

outdir="runs/R-2026-04-22-001-newton-krylov-v25-diagnostic"
mkdir -p "$outdir"

echo
echo "[3/4] Launching 6-point diagnostic sweep..."
echo "      mu^2 in {-1.0, -0.8, -0.6, -0.4, -0.2, -0.1} at N=32"
echo "      Output dir: $outdir"

t0=$(date +%s)
python PDE/continuation_mu2_v25.py \
    --N 32 \
    --diagnostic \
    --mu2_list "-1.0,-0.8,-0.6,-0.4,-0.2,-0.1" \
    --output "$outdir" \
    --config PDE/config_template_brazovskii.json
exit_code=$?
wall=$(( $(date +%s) - t0 ))

echo
echo "[4/4] Diagnostic complete in ${wall} s (exit $exit_code)."

if [ $exit_code -eq 0 ]; then
    echo
    echo "*** v2.5 DIAGNOSTIC: PASS ***"
    echo "Populate $outdir/MANIFEST.md; then run: python tools/build_version_index.py"
    echo "Then commit: ./scripts/commit_v25_diagnostic.sh"
else
    echo
    echo "*** v2.5 DIAGNOSTIC: FAIL (exit $exit_code) ***"
    echo "File Q-2026-04-22-SolverFit in Docs/status/OPEN-QUESTIONS.md"
fi

exit $exit_code
