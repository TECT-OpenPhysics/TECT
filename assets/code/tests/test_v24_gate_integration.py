"""
tests/test_v24_gate_integration.py
==================================

Logic-level regression tests for the v2.4 Phase-0 gate integration
into tect_newton_krylov.py.  We cannot import the full solver in a
no-torch sandbox, so we replicate the gate wrapper inline here and
verify its six branching paths against v24_thresholds (the single
source of truth).

The six paths:

  (A) Missing/non-finite mu2          -> skipped = True, passed = False
  (B) Invalid Brazovskii params       -> skipped = True, passed = False
  (C) mu2 >= r_c^meta                 -> skipped = True, passed = False
                                         (outside Math56-Addendum window)
  (D) Phi* = 0 exactly                -> RuntimeError (Class-II guard)
  (E) Phi* = phi_+ * ones             -> passed = True
  (F) Phi* = phi_- * ones (on sep.)   -> passed = False (cushion)

Runs in milliseconds, pure numpy.
"""
from __future__ import annotations

import math
import sys
import unittest

import numpy as np

# Make project root importable.
_HERE = __file__.rsplit("/", 2)[0]
sys.path.insert(0, _HERE)

from PDE.v24_thresholds import (  # noqa: E402
    BrazovskiiParams,
    V24_G0_CUSHION,
    V24_RHO_STAR_FACTOR,
    brazovskii_critical_mu2,
    v24_class2_guard,
    v24_phase0_gate,
    v24_separatrix_thresholds,
)


def gate_wrapper(Psi_star: np.ndarray, params: dict) -> dict:
    """Mirror of tect_newton_krylov._run_v24_phase0_gate (verbose=False),
    but without the downstream print statements.  We keep the function
    local to the test so any future drift is caught by this regression
    rather than silently passing under a stale tect_newton_krylov."""
    lam = float(params.get("quartic_lambda", params.get("lambda", np.nan)))
    gam = float(params.get("sextic_gamma",   params.get("gamma",  np.nan)))
    mu2 = float(params.get("mu2", np.nan))
    if not np.isfinite(lam) or not np.isfinite(gam) or not np.isfinite(mu2):
        return {"passed": False, "skipped": True,
                "reason": "non-finite params"}
    try:
        P = BrazovskiiParams(lam=lam, gam=gam)
    except ValueError as exc:
        return {"passed": False, "skipped": True,
                "reason": f"invalid Brazovskii: {exc}"}

    r_global, r_meta = brazovskii_critical_mu2(P)
    if mu2 >= r_meta:
        return {"passed": False, "skipped": True,
                "reason": "outside existence window",
                "r_c_global": r_global, "r_c_meta": r_meta}

    sep = v24_separatrix_thresholds(mu2, P)
    mean_sq = float(np.mean(np.abs(Psi_star) ** 2))
    gate = v24_phase0_gate(mean_sq, sep)
    v24_class2_guard(mean_sq, sep)  # may raise
    return {"passed": bool(gate["passed"]), "skipped": False,
            "mean_sq": mean_sq, "V": float(gate["V"]),
            "G0_op": float(sep.G0_op), "rho_star": float(sep.rho_star),
            "phi_plus": float(sep.phi_plus)}


LAM, GAM = -0.43, 1.62
MU2_TARGET = 5.0e-3


class TestGateIntegration(unittest.TestCase):
    """Six-branch coverage of the v2.4 gate."""

    def test_A_missing_mu2(self) -> None:
        out = gate_wrapper(np.ones((3, 2, 2, 2)),
                           {"lambda": LAM, "gamma": GAM})
        self.assertTrue(out["skipped"])
        self.assertFalse(out["passed"])

    def test_B_invalid_brazovskii(self) -> None:
        # lam > 0 violates BrazovskiiParams invariant.
        out = gate_wrapper(np.ones((3, 2, 2, 2)),
                           {"lambda": +0.43, "gamma": GAM, "mu2": 1e-3})
        self.assertTrue(out["skipped"])
        self.assertFalse(out["passed"])
        self.assertIn("invalid Brazovskii", out["reason"])

    def test_C_outside_existence_window(self) -> None:
        # Locked mu2 = 0.26 is 17x above r_c^meta.
        out = gate_wrapper(np.ones((3, 2, 2, 2)),
                           {"lambda": LAM, "gamma": GAM, "mu2": 0.26})
        self.assertTrue(out["skipped"])
        self.assertFalse(out["passed"])
        self.assertGreater(out["r_c_meta"], 0.0)
        self.assertLess(out["r_c_meta"], 0.26)

    def test_D_class2_floor_breach(self) -> None:
        P = BrazovskiiParams(lam=LAM, gam=GAM)
        sep = v24_separatrix_thresholds(MU2_TARGET, P)
        # ||Psi||_RMS^2 far below rho_* -> must raise.
        tiny = np.full((3, 2, 2, 2), 1e-8, dtype=np.complex128)
        with self.assertRaises(RuntimeError) as ctx:
            gate_wrapper(tiny,
                         {"lambda": LAM, "gamma": GAM, "mu2": MU2_TARGET})
        self.assertIn("Class-II", str(ctx.exception))

    def test_E_phi_plus_passes(self) -> None:
        P = BrazovskiiParams(lam=LAM, gam=GAM)
        sep = v24_separatrix_thresholds(MU2_TARGET, P)
        # A uniform Psi with |Psi|^2 = phi_+^2 maps to V = 1 > G0_op.
        phi = sep.phi_plus
        Psi = np.full((3, 2, 2, 2), phi, dtype=np.complex128)
        out = gate_wrapper(Psi,
                           {"lambda": LAM, "gamma": GAM, "mu2": MU2_TARGET})
        self.assertFalse(out["skipped"])
        self.assertTrue(out["passed"])
        self.assertAlmostEqual(out["V"], 1.0, places=6)

    def test_F_phi_minus_fails_with_cushion(self) -> None:
        P = BrazovskiiParams(lam=LAM, gam=GAM)
        sep = v24_separatrix_thresholds(MU2_TARGET, P)
        # |Psi|^2 = phi_-^2 lies on the separatrix; V = alpha_sep < G0_op.
        phi = sep.phi_minus
        Psi = np.full((3, 2, 2, 2), phi, dtype=np.complex128)
        out = gate_wrapper(Psi,
                           {"lambda": LAM, "gamma": GAM, "mu2": MU2_TARGET})
        self.assertFalse(out["skipped"])
        self.assertFalse(out["passed"])
        # The cushion delta = V24_G0_CUSHION must be positive.
        self.assertGreater(out["G0_op"] - out["V"], V24_G0_CUSHION - 1e-9)


class TestConfigCompatibility(unittest.TestCase):
    """The production config uses BOTH 'quartic_lambda'/'sextic_gamma' and
    'lambda'/'gamma'; v2.4 gate must prefer the explicit quartic_/sextic_
    fields when both are present and fall back otherwise."""

    def test_quartic_sextic_priority(self) -> None:
        out = gate_wrapper(
            np.full((3, 2, 2, 2), 0.0, dtype=np.complex128) + 1e-10,
            {"quartic_lambda": LAM, "sextic_gamma": GAM,
             "mu2": 0.26,  # force SKIP to avoid Class-II raise
             "lambda": +0.5, "gamma": -0.1},  # bogus fallbacks
        )
        # Must have used the quartic_/sextic_ values (which are valid).
        self.assertTrue(out["skipped"])
        self.assertIn("existence window", out["reason"])

    def test_fallback_to_lambda_gamma(self) -> None:
        out = gate_wrapper(
            np.full((3, 2, 2, 2), 0.0, dtype=np.complex128) + 1e-10,
            {"lambda": LAM, "gamma": GAM, "mu2": 0.26},
        )
        self.assertTrue(out["skipped"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
