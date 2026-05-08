"""
tests/test_v24_thresholds.py
============================

Unit tests for PDE/v24_thresholds.py.  No torch dependency, no GPU, no
disk I/O -- runs in milliseconds.

Run:
    python3 -m pytest tests/test_v24_thresholds.py -v
    # or, without pytest:
    python3 tests/test_v24_thresholds.py
"""

from __future__ import annotations

import math
import sys
import unittest

import numpy as np

# Import from project root.
sys.path.insert(0, __file__.rsplit("/", 2)[0])

from PDE.v24_thresholds import (  # noqa: E402
    BrazovskiiParams,
    V24_G0_CUSHION,
    V24_G2_MIN,
    V24_G3_REL,
    V24_MU2_TARGET_DEFAULT,
    V24_RHO_STAR_FACTOR,
    brazovskii_critical_mu2,
    v24_banner,
    v24_class2_guard,
    v24_phase0_gate,
    v24_phase0_statistic,
    v24_phase25_gate,
    v24_phase25_overlap,
    v24_phase25_residual_rel,
    v24_separatrix_thresholds,
)

LAM = -0.43
GAM = 1.62
P = BrazovskiiParams(lam=LAM, gam=GAM)


class TestCriticalScales(unittest.TestCase):
    """Math56-Addendum §1.  r_c^{global} = lam^2/(10 gam),
    r_c^{meta} = 2 lam^2/(15 gam)."""

    def test_critical_numerical_values(self) -> None:
        r_global, r_meta = brazovskii_critical_mu2(P)
        self.assertAlmostEqual(r_global, 0.011414, places=5)
        self.assertAlmostEqual(r_meta, 0.015218, places=5)
        # Ratio must be 3/4 exactly.
        self.assertAlmostEqual(r_global / r_meta, 0.75, places=10)

    def test_locked_above_meta(self) -> None:
        _, r_meta = brazovskii_critical_mu2(P)
        locked_mu2 = 0.26
        self.assertGreater(locked_mu2, r_meta)
        # 17x ratio, per Math56-Addendum Theorem 1.
        self.assertAlmostEqual(locked_mu2 / r_meta, 17.08, places=1)


class TestSeparatrixTable(unittest.TestCase):
    """Math56-Addendum Theorem 2 and numerical table."""

    def test_mu2_target_5e_3(self) -> None:
        """Recommended Option B.  Values SymPy-verified 2026-04-20."""
        s = v24_separatrix_thresholds(5.0e-3, P)
        self.assertAlmostEqual(s.phi_plus, 0.2538, places=4)
        self.assertAlmostEqual(s.phi_minus, 0.0799, places=4)
        self.assertAlmostEqual(s.alpha_sep, 0.3150, places=4)
        self.assertAlmostEqual(s.G0_raw, 0.6575, places=4)
        self.assertAlmostEqual(s.G0_op, 0.7075, places=4)
        self.assertAlmostEqual(s.rho_star, 6.44e-5, delta=1e-6)

    def test_mu2_target_3e_3_deeper(self) -> None:
        s = v24_separatrix_thresholds(3.0e-3, P)
        self.assertAlmostEqual(s.phi_plus, 0.2590, places=4)
        self.assertAlmostEqual(s.G0_op, 0.6671, places=4)

    def test_mu2_target_8e_3_shallow(self) -> None:
        s = v24_separatrix_thresholds(8.0e-3, P)
        self.assertAlmostEqual(s.G0_op, 0.7647, places=4)

    def test_mu2_at_r_global(self) -> None:
        r_global, _ = brazovskii_critical_mu2(P)
        s = v24_separatrix_thresholds(r_global, P)
        # At r_c^{global} we must recover phi_0 = sqrt(-lam/(5 gam)) = 0.23040.
        expected = math.sqrt(-LAM / (5.0 * GAM))
        self.assertAlmostEqual(s.phi_plus, expected, places=6)
        self.assertAlmostEqual(s.phi_plus, 0.2305, places=3)

    def test_locked_mu2_raises(self) -> None:
        """Math56-Addendum Theorem 1 + Corollary 1 precondition."""
        with self.assertRaises(ValueError) as ctx:
            v24_separatrix_thresholds(0.26, P)
        self.assertIn("r_c^meta", str(ctx.exception))


class TestPhase0Gate(unittest.TestCase):

    def setUp(self) -> None:
        self.sep = v24_separatrix_thresholds(5.0e-3, P)

    def test_trivial_vacuum_fails(self) -> None:
        # ||Psi||_RMS = 1e-6, phi_+ = 0.2538 => V = 3.94e-6
        mean_sq = (1.0e-6) ** 2
        out = v24_phase0_gate(mean_sq, self.sep)
        self.assertFalse(out["passed"])
        self.assertLess(out["V"], 1e-5)

    def test_at_bcc_minimum_passes(self) -> None:
        # ||Psi||_RMS = phi_+ => V = 1.0
        mean_sq = self.sep.phi_plus ** 2
        out = v24_phase0_gate(mean_sq, self.sep)
        self.assertTrue(out["passed"])
        self.assertAlmostEqual(out["V"], 1.0, places=6)

    def test_on_separatrix_fails_with_cushion(self) -> None:
        # V = alpha_sep (0.315) < G0_op (0.708)
        mean_sq = (self.sep.phi_minus) ** 2
        out = v24_phase0_gate(mean_sq, self.sep)
        self.assertFalse(out["passed"])


class TestClass2Guard(unittest.TestCase):

    def setUp(self) -> None:
        self.sep = v24_separatrix_thresholds(5.0e-3, P)

    def test_above_floor_passes_silently(self) -> None:
        # Should not raise.
        v24_class2_guard(1.0, self.sep)

    def test_below_floor_raises(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            v24_class2_guard(1.0e-10, self.sep)
        self.assertIn("Class-II", str(ctx.exception))
        self.assertIn("rho_*", str(ctx.exception))


class TestPhase25Gate(unittest.TestCase):

    def test_G2_perfect_overlap_passes(self) -> None:
        v = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        overlap = v24_phase25_overlap(v, v)
        self.assertAlmostEqual(overlap, 1.0, places=8)

    def test_G2_orthogonal_fails(self) -> None:
        a = np.array([1.0, 0.0], dtype=np.float64)
        b = np.array([0.0, 1.0], dtype=np.float64)
        self.assertAlmostEqual(v24_phase25_overlap(a, b), 0.0, places=8)

    def test_G2_at_threshold(self) -> None:
        # Two unit vectors with overlap exactly 0.9.
        theta = math.acos(V24_G2_MIN)
        a = np.array([1.0, 0.0], dtype=np.float64)
        b = np.array([math.cos(theta), math.sin(theta)], dtype=np.float64)
        overlap = v24_phase25_overlap(a, b)
        self.assertAlmostEqual(overlap, V24_G2_MIN, places=8)

    def test_G3_relative_bound(self) -> None:
        bound, ratio = v24_phase25_residual_rel(residual_norm=0.05, lam_ritz=1.0)
        self.assertAlmostEqual(bound, 0.1, places=8)
        self.assertAlmostEqual(ratio, 0.5, places=8)

    def test_G3_fails_on_zero_lam(self) -> None:
        v = np.array([1.0, 0.0])
        res = v24_phase25_gate(v, v, lam_ritz=0.0, residual_norm=1e-6)
        self.assertFalse(res["G3_pass"])
        self.assertFalse(res["overall_pass"])

    def test_G3_fails_on_negative_lam(self) -> None:
        """v2p4-adversarial-audit-2026-04-20 [H-1]:  a negative Ritz
        eigenvalue is an instability, not a spectral gap, and must
        never certify G3 even with a small residual."""
        v = np.array([1.0, 0.0])
        res = v24_phase25_gate(v, v, lam_ritz=-0.5, residual_norm=1e-8)
        self.assertFalse(res["G3_pass"])
        self.assertFalse(res["overall_pass"])

    def test_full_gate_pass(self) -> None:
        v = np.array([1.0, 0.0])
        res = v24_phase25_gate(
            v, v, lam_ritz=0.02, residual_norm=0.001  # ratio = 0.5
        )
        self.assertTrue(res["G2_pass"])
        self.assertTrue(res["G3_pass"])
        self.assertTrue(res["overall_pass"])


class TestBanner(unittest.TestCase):
    def test_banner_contains_key_tags(self) -> None:
        txt = v24_banner(mu2_target=V24_MU2_TARGET_DEFAULT)
        for key in ("r_c^global", "r_c^meta", "phi_+", "G0_op", "rho_*",
                    "G2_min", "G3_rel", "Math56-Addendum"):
            self.assertIn(key, txt)


class TestInvariantParams(unittest.TestCase):
    def test_rejects_positive_lam(self) -> None:
        with self.assertRaises(ValueError):
            BrazovskiiParams(lam=+0.1, gam=1.0)

    def test_rejects_nonpositive_gam(self) -> None:
        with self.assertRaises(ValueError):
            BrazovskiiParams(lam=-0.1, gam=0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
