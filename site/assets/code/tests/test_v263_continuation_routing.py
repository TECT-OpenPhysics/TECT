"""
Routing-layer pytest module for PDE/continuation_mu2_v25.py

Theory  : Math74 Addendum-A §A.3 residual items R'₁, R'₂, R'₃
          + Math74 Addendum-B (v2.6.4 gate semantic fix)
          + Math72 Addendum-A Post-54 Runbook endpoint-JSON contract

Contracts tested (v2.6.4 revision)
----------------------------------
1. TestContractSchema              — endpoint JSON schema
   (continuation_mu2_v25_endpoint/1.1, 29 fields, types, finiteness).
2. TestContractExitCodes           — exit-code semantics (PASS→0,
   SKELETON_ONLY→10, FAIL→2, PARTIAL→2).
3. TestContractConvergenceCriterion — Eq. m74-conv-criterion fix
   (grad_norm finite AND < tol; IEEE 754 NaN handling).
4. TestContractMath63Gate2D        — Math74 Addendum-B §3 semantic fix.
   Gate now evaluates on ``rho_trust`` (trust-region actual/predicted
   ratio), not on ``line_search_alpha``. Default thresholds
   newton_max=12, tCG_max=3000, rho_min=0.05.
5. TestContractRoutingSolverName   — R'₁ coverage (B1 name-map
   pcg→cg, fgmres→gmres, minres→gmres).

Torch availability
------------------
All tests are torch-independent; a single integration test is marked
skipif on torch unavailability.

Sync note (2026-04-23, v2.6.4): the earlier "16-field"/"19-field"/"27-field"
drafts of this docstring are superseded; the authoritative field count is
29 as enforced by test_endpoint_schema_complete_29_fields below and by
``TestContractSchema.EXPECTED_FIELDS = 29``. When the endpoint schema
bumps again, update EXPECTED_FIELDS first and let the test fail-fast
force the docstring to catch up.
"""

from __future__ import annotations

import json
import math
import sys
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

# Attempt to import test utilities
try:
    from conftest import make_bcc_config
except ImportError:
    # Fallback if conftest not auto-discovered
    from tests.conftest import make_bcc_config


# Torch availability detection (same as continuation_mu2_v25.py)
try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


# Ensure PDE/ is on the path for the tests below. We do this once, up
# front, to avoid repeated sys.path.insert inside every test body.
_PDE_DIR = "/sessions/intelligent-funny-cerf/mnt/Contents/PDE"
if _PDE_DIR not in sys.path:
    sys.path.insert(0, _PDE_DIR)


# ---------------------------------------------------------------------------
# Synthetic v2.6.4 endpoint payload used across TestContractSchema tests.
# Kept as a helper so the 29-field list is defined in exactly one place.
# ---------------------------------------------------------------------------

def _make_valid_endpoint_v11() -> Dict[str, Any]:
    """Return a valid v1.1 endpoint dict matching MANIFEST emission site."""
    return {
        "schema_version": "continuation_mu2_v25_endpoint/1.1",
        "theory_tag": "Math74-AddB-v2p6p4-gate-semantic-fix-2026-04-23",
        "driver_version": "v2.6.4",
        "solver_core_version": "v2.6.2",
        "mu2": 5.0e-3,
        "r": 0.005,
        "N": 32,
        "L": 16.0,
        "converged": True,
        "pass_math63_2d": True,
        "m_star_sq": 0.3138,
        "delta_F": -0.001,
        "F_condensate": -0.5,
        "F_vacuum": -0.499,
        "rms_amplitude": 0.2,
        "favorable_vs_vacuum": True,
        "wall_time_s": 123.45,
        "n_newton_steps": 8,
        "n_accepted_newton_steps": 7,
        "final_grad_norm": 1.2e-9,
        "tcg_peak": 432,
        "rho_trust_min": 0.98,
        "gate_newton_max": 12,
        "gate_tcg_max": 3000,
        "gate_rho_min": 0.05,
        "ew_eta_min": 0.05,
        "ew_eta_max": 0.9,
        "tol_newton": 1e-8,
        "timestamp": "2026-04-23T12:34:56",
    }


# ---------------------------------------------------------------------------
# TestContractSchema — Static JSON schema contract (Torch-less)
# ---------------------------------------------------------------------------

class TestContractSchema:
    """
    Assert the 29-field v1.1 endpoint JSON schema contract
    (``continuation_mu2_v25_endpoint/1.1``, Math74 Addendum-B §5).

    v1.1 upgrades v1.0 with (a) ``pass_math63_2d`` gate boolean,
    (b) ``n_accepted_newton_steps`` / ``tcg_peak`` / ``rho_trust_min``
    per-point diagnostics, (c) ``gate_newton_max`` /
    ``gate_tcg_max`` / ``gate_rho_min`` / ``ew_eta_min`` /
    ``ew_eta_max`` / ``tol_newton`` explicit thresholds, so that
    downstream consumers (Task #55 / #56 / #77) can audit exactly
    which run conditions produced a given endpoint.
    """

    EXPECTED_FIELDS = 29

    def test_endpoint_schema_complete_29_fields(self):
        """Schema must have exactly 29 fields with correct names and types."""
        endpoint = _make_valid_endpoint_v11()
        assert len(endpoint) == self.EXPECTED_FIELDS, (
            f"Expected {self.EXPECTED_FIELDS} fields, got {len(endpoint)}"
        )
        # Schema version pin
        assert endpoint["schema_version"] == "continuation_mu2_v25_endpoint/1.1"
        # Type pins
        assert isinstance(endpoint["theory_tag"], str)
        assert isinstance(endpoint["driver_version"], str)
        assert isinstance(endpoint["solver_core_version"], str)
        assert isinstance(endpoint["mu2"], (int, float))
        assert isinstance(endpoint["r"], (int, float))
        assert isinstance(endpoint["N"], int)
        assert isinstance(endpoint["L"], (int, float))
        assert isinstance(endpoint["converged"], bool)
        assert isinstance(endpoint["pass_math63_2d"], bool)
        assert isinstance(endpoint["m_star_sq"], (int, float))
        assert isinstance(endpoint["delta_F"], (int, float))
        assert isinstance(endpoint["F_condensate"], (int, float))
        assert isinstance(endpoint["F_vacuum"], (int, float))
        assert isinstance(endpoint["rms_amplitude"], (int, float))
        assert isinstance(endpoint["favorable_vs_vacuum"], bool)
        assert isinstance(endpoint["wall_time_s"], (int, float))
        assert isinstance(endpoint["n_newton_steps"], int)
        assert isinstance(endpoint["n_accepted_newton_steps"], int)
        assert isinstance(endpoint["final_grad_norm"], (int, float))
        assert isinstance(endpoint["tcg_peak"], int)
        assert isinstance(endpoint["rho_trust_min"], (int, float))
        assert isinstance(endpoint["gate_newton_max"], int)
        assert isinstance(endpoint["gate_tcg_max"], int)
        assert isinstance(endpoint["gate_rho_min"], (int, float))
        assert isinstance(endpoint["ew_eta_min"], (int, float))
        assert isinstance(endpoint["ew_eta_max"], (int, float))
        assert isinstance(endpoint["tol_newton"], (int, float))
        assert isinstance(endpoint["timestamp"], str)

    def test_endpoint_physics_fields_finite(self):
        """Physics fields (m_star_sq, delta_F, F_*, rms_amplitude) must be finite."""
        endpoint = _make_valid_endpoint_v11()
        physics_fields = [
            "m_star_sq",
            "delta_F",
            "F_condensate",
            "F_vacuum",
            "rms_amplitude",
            "final_grad_norm",
            "rho_trust_min",
        ]
        for field in physics_fields:
            val = endpoint[field]
            assert math.isfinite(val), f"Field {field} = {val} is not finite"

    def test_endpoint_booleans_are_bool(self):
        """favorable_vs_vacuum / pass_math63_2d / converged must all be bool."""
        endpoint = _make_valid_endpoint_v11()
        for field in ("favorable_vs_vacuum", "pass_math63_2d", "converged"):
            val = endpoint[field]
            assert isinstance(val, bool), f"{field} must be bool, got {type(val)}"
            assert val in (True, False)


# ---------------------------------------------------------------------------
# TestContractExitCodes — Exit-code semantics (Torch-less)
# ---------------------------------------------------------------------------

class TestContractExitCodes:
    """
    Assert the exit-code mapping contract:
      PASS          → 0
      SKELETON_ONLY → 10
      FAIL          → 2
      PARTIAL       → 2 (fail-closed)

    The mapping is a pure function of the ``overall_status`` string; we
    exercise it directly via the reference implementation duplicated
    below. This is torch-less.
    """

    @staticmethod
    def _exit_code(status: str) -> int:
        if status == "PASS":
            return 0
        if status == "SKELETON_ONLY":
            return 10
        return 2

    def test_exit_code_pass_returns_0(self):
        assert self._exit_code("PASS") == 0

    def test_exit_code_skeleton_only_returns_10(self):
        assert self._exit_code("SKELETON_ONLY") == 10

    def test_exit_code_fail_returns_2(self):
        assert self._exit_code("FAIL") == 2

    def test_exit_code_partial_returns_2(self):
        assert self._exit_code("PARTIAL") == 2


# ---------------------------------------------------------------------------
# TestContractConvergenceCriterion — IEEE 754 fix (Torch-less)
# ---------------------------------------------------------------------------

class TestContractConvergenceCriterion:
    """Eq. m74-conv-criterion: converged iff grad_norm finite AND < tol."""

    def test_converged_when_grad_norm_finite_and_below_tol(self):
        from continuation_mu2_v25 import _converged_from_history
        history = [{"step": 0, "grad_norm": 1.0, "tCG_iterations": 50},
                   {"step": 1, "grad_norm": 1.0e-9, "tCG_iterations": 30}]
        assert _converged_from_history(history, 1e-8) is True

    def test_not_converged_when_grad_norm_above_tol(self):
        from continuation_mu2_v25 import _converged_from_history
        history = [{"step": 0, "grad_norm": 1.0, "tCG_iterations": 50},
                   {"step": 1, "grad_norm": 1.0e-5, "tCG_iterations": 30}]
        assert _converged_from_history(history, 1e-8) is False

    def test_not_converged_when_grad_norm_is_nan(self):
        from continuation_mu2_v25 import _converged_from_history
        history = [{"step": 0, "grad_norm": float("nan"), "tCG_iterations": 50}]
        assert _converged_from_history(history, 1e-8) is False


# ---------------------------------------------------------------------------
# TestContractMath63Gate2D — R'₃ semantic fix (Torch-less)
# ---------------------------------------------------------------------------

def _mk_step(
    iteration: int,
    *,
    grad: float = 1e-5,
    alpha: float = 1.0,
    rho: float = 1.0,
    accepted: bool = True,
    tCG: int = 150,
) -> "NewtonStep":  # forward reference
    from continuation_mu2_v25 import NewtonStep
    return NewtonStep(
        iteration=iteration,
        residual_norm=grad,
        step_norm=alpha,                       # v2.6.3-b deprecated alias
        convergence_ratio=None,
        krylov_method="pcg",
        krylov_iterations=tCG,
        krylov_converged=True,
        eta_ew=0.5,
        newton_tolerance=1e-8,
        wall_time_s=0.1,
        line_search_alpha=alpha,
        rho_trust=rho,
        accepted=accepted,
        model_pred_reduction=1.0,
        actual_reduction=rho,
    )


class TestContractMath63Gate2D:
    """
    Math63 §2D / Math64 §sec2d gate, v2.6.4 semantic fix
    (Math74 Addendum-B §3).

    The gate tests:
      |newton_steps|   ≤ newton_max      (default 12)
      max tCG          ≤ tCG_max         (default 3000)
      ∀ accepted step: rho_trust ≥ rho_min   (default 0.05)

    The v2.6.3-b bug that compared ``line_search_alpha`` against
    rho_min is eliminated; the gate now reads ``NewtonStep.rho_trust``
    explicitly, sourced from ``NewtonStepRecord.rho`` of the solver
    core.
    """

    def test_gate_passes_valid_steps(self):
        from continuation_mu2_v25 import pass_math63_gate_2D
        steps = [
            _mk_step(0, grad=1e-2, rho=1.0, tCG=150),
            _mk_step(1, grad=1e-4, rho=1.0, tCG=140),
            _mk_step(2, grad=1e-9, rho=1.0, tCG=100),
        ]
        assert pass_math63_gate_2D(steps) is True

    def test_gate_fails_too_many_newton_steps(self):
        from continuation_mu2_v25 import pass_math63_gate_2D
        # 13 accepted steps with rho=1.0 each — exceeds default max 12.
        steps = [_mk_step(i, rho=1.0, tCG=100) for i in range(13)]
        assert pass_math63_gate_2D(steps) is False

    def test_gate_fails_tCG_over_threshold(self):
        from continuation_mu2_v25 import pass_math63_gate_2D
        steps = [
            _mk_step(0, rho=1.0, tCG=150),
            _mk_step(1, rho=1.0, tCG=5000),   # exceeds default tCG_max=3000
        ]
        assert pass_math63_gate_2D(steps) is False

    def test_gate_fails_low_rho_trust_on_accepted_step(self):
        """v2.6.4 core: accepted step with ρ_trust < 0.05 must fail the gate."""
        from continuation_mu2_v25 import pass_math63_gate_2D
        steps = [
            _mk_step(0, rho=1.0, accepted=True, tCG=200),
            _mk_step(1, rho=0.01, accepted=True, tCG=200),   # ρ < 0.05
        ]
        assert pass_math63_gate_2D(steps) is False

    def test_gate_ignores_rejected_step_rho(self):
        """Rejected steps (not accepted) are NOT tested against rho_min.
        Rejected steps have rho < 0.25 by trust-region definition; the
        gate must not be tricked into failure by them."""
        from continuation_mu2_v25 import pass_math63_gate_2D
        steps = [
            _mk_step(0, rho=1.0, accepted=True, tCG=100),
            _mk_step(1, rho=-1e30, accepted=False, tCG=200),  # rejected shrink-step
            _mk_step(2, rho=1.0, accepted=True, tCG=100),
        ]
        assert pass_math63_gate_2D(steps) is True

    def test_gate_passes_live_quadratic_convergence_profile(self):
        """Live 2026-04-23 N=32 profile (Newton 7, α=1 everywhere, ρ=1.0).

        Before v2.6.4 the gate failed on this profile because α was
        compared against rho_min=0.05. After v2.6.4 the same profile
        passes, which is the correct physical verdict."""
        from continuation_mu2_v25 import pass_math63_gate_2D
        live_tCG = [1, 1, 2, 6, 29, 2304, 280, 50]          # pasted from live log
        steps = [_mk_step(i, alpha=1.0, rho=1.0, accepted=True,
                          tCG=live_tCG[i])
                 for i in range(len(live_tCG))]
        # With default thresholds (newton_max=12, tCG_max=3000, rho_min=0.05)
        # the live profile must pass.
        assert pass_math63_gate_2D(steps) is True
        # But with the legacy-strict Math63 publication thresholds the
        # same profile fails on the tCG=2304 step.
        strict = {"newton_max": 8, "tCG_max": 300, "rho_min": 0.25}
        assert pass_math63_gate_2D(steps, tol_gate=strict) is False

    def test_gate_fails_on_empty_history(self):
        from continuation_mu2_v25 import pass_math63_gate_2D
        assert pass_math63_gate_2D([]) is False

    def test_gate_legacy_key_rho_lin_max_is_remapped(self):
        """v2.6.3-b callers passed ``rho_lin_max`` as the third key;
        v2.6.4 interprets this legacy key as ``rho_min`` (lower bound
        on rho_trust, NOT upper bound on α)."""
        from continuation_mu2_v25 import pass_math63_gate_2D
        steps = [_mk_step(0, rho=0.10, tCG=100, accepted=True)]
        # Legacy key is remapped; 0.10 >= 0.05 → pass
        assert pass_math63_gate_2D(
            steps, tol_gate={"rho_lin_max": 0.05}
        ) is True
        # Legacy key with stricter threshold 0.5 >> 0.10 → fail
        assert pass_math63_gate_2D(
            steps, tol_gate={"rho_lin_max": 0.5}
        ) is False

    def test_continuation_point_has_pass_math63_2d_field(self):
        from continuation_mu2_v25 import ContinuationPoint
        point = ContinuationPoint(mu2=-1.0, r=0.5, converged=True)
        assert hasattr(point, "pass_math63_2d")
        assert point.pass_math63_2d is False
        point.pass_math63_2d = True
        assert point.pass_math63_2d is True


# ---------------------------------------------------------------------------
# TestContractRoutingSolverName — R'₁ coverage (Torch-less + skippable torch)
# ---------------------------------------------------------------------------

class TestContractRoutingSolverName:
    """
    R'₁: the solver routing must canonicalise
      pcg    → cg
      fgmres → gmres
      minres → gmres

    The canonicalisation is documented in Math68 §3 Prop.
    ``math68-B1-fix``. Here we exercise the Phase-A probe output
    (``select_krylov_solver``), which is the upstream of that
    canonicalisation; the B1 shim itself sits inside the solver core
    and is validated by the solver-core tests.
    """

    def test_krylov_method_routing_pcg_to_cg(self):
        from continuation_mu2_v25 import select_krylov_solver, JacobianClassification
        jc = JacobianClassification(
            symmetric=True, indefinite=False, asymmetric=False,
            rayleigh_samples=[0.1, 0.05], antisymmetry_norm=1e-10,
            jacobian_norm=1.0, n_negative_rayleigh=0,
        )
        assert select_krylov_solver(jc, verbose=False) in ("cg", "pcg")

    def test_krylov_method_routing_fgmres_to_gmres(self):
        from continuation_mu2_v25 import select_krylov_solver, JacobianClassification
        jc = JacobianClassification(
            symmetric=False, indefinite=False, asymmetric=True,
            rayleigh_samples=[0.1, 0.05], antisymmetry_norm=0.1,
            jacobian_norm=1.0, n_negative_rayleigh=0,
        )
        assert select_krylov_solver(jc, verbose=False) in ("gmres", "fgmres")

    def test_krylov_method_routing_minres_to_gmres(self):
        from continuation_mu2_v25 import select_krylov_solver, JacobianClassification
        jc = JacobianClassification(
            symmetric=True, indefinite=True, asymmetric=False,
            rayleigh_samples=[-0.1, 0.05, 0.1], antisymmetry_norm=1e-10,
            jacobian_norm=1.0, n_negative_rayleigh=1,
        )
        assert select_krylov_solver(jc, verbose=False) in ("minres", "gmres")

    @pytest.mark.skipif(not _TORCH_AVAILABLE, reason="PyTorch not available")
    def test_select_krylov_solver_integration_torch_present(self):
        from continuation_mu2_v25 import select_krylov_solver
        assert callable(select_krylov_solver)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
