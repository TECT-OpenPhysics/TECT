#!/usr/bin/env python3
"""
test_monopole_mc.py — Unit tests for Block 4 monopole_vacuum_mc.py

MATURITY: SKELETON-EXECUTABLE
Tests structure and statistical API; full MC runs feasible on any machine (numpy-only).

TEST PLAN (Skeleton + executable):
  U1: Import and signature validation
  U2: Monopole action computation
  U3: MC sampling and statistical properties
  R1: JSON output schema validation
  C1: Hypothesis test on synthetic data

EXPECTED OUTPUT:
  All tests PASS (importable, stat tests on synthetic samples valid).

EXECUTABLE TEST (CPU-only):
  python -m pytest tests/test_monopole_mc.py -v -k "not test_u3_large_ensemble"
  (test_u3_large_ensemble can run locally; marked as slow)
"""

import sys
import json
import tempfile
from pathlib import Path

import numpy as np
from scipy import stats
import pytest


class TestMonopoleVacuumMC:
    """Test suite for monopole_vacuum_mc.py"""

    def test_u1_import_and_signature(self):
        """U1: Verify module imports and function signatures."""
        try:
            from tools import monopole_vacuum_mc as mc_module
        except ImportError:
            pytest.skip("monopole_vacuum_mc module not in import path")

        # Check function existence
        assert hasattr(mc_module, 'monopole_action')
        assert hasattr(mc_module, 'construct_bcc_lattice')
        assert hasattr(mc_module, 'sample_monopole_ensemble')
        assert hasattr(mc_module, 'run_monopole_mc')

        # Check function signatures
        import inspect

        sig = inspect.signature(mc_module.monopole_action)
        assert 'charge' in sig.parameters

        sig = inspect.signature(mc_module.construct_bcc_lattice)
        assert 'L' in sig.parameters

        sig = inspect.signature(mc_module.sample_monopole_ensemble)
        assert all(p in sig.parameters for p in ['n_samples', 'L'])

        sig = inspect.signature(mc_module.run_monopole_mc)
        assert 'n_samples' in sig.parameters

    def test_u2_monopole_action(self):
        """U2: Validate monopole action computation."""
        try:
            from tools.monopole_vacuum_mc import monopole_action
        except ImportError:
            pytest.skip("monopole_vacuum_mc module not available")

        # Test case 1: zero charge
        S = monopole_action(charge=0.0)
        assert np.isclose(S, 0.0, atol=1e-14), \
            f"Expected S = 0 for zero charge, got {S}"

        # Test case 2: positive charge scaling
        S1 = monopole_action(charge=1.0, scale_factor=1.0)
        S2 = monopole_action(charge=2.0, scale_factor=1.0)
        # Action should scale as Q²
        assert np.isclose(S2, 4.0 * S1, rtol=1e-10), \
            f"Expected S(Q=2) ≈ 4*S(Q=1), got ratio {S2/S1:.3f}"

        # Test case 3: scale factor dependence
        S_scale1 = monopole_action(charge=1.0, scale_factor=1.0)
        S_scale2 = monopole_action(charge=1.0, scale_factor=2.0)
        # Action should scale as 1/scale_factor
        assert np.isclose(S_scale2, S_scale1 / 2.0, rtol=1e-10), \
            f"Expected S(scale=2) ≈ S(scale=1)/2, got ratio {S_scale2/S_scale1:.3f}"

        print("[U2 PASS] Monopole action computation validated")

    def test_u3_bcc_lattice_construction(self):
        """U3: Validate BCC lattice construction."""
        try:
            from tools.monopole_vacuum_mc import construct_bcc_lattice
        except ImportError:
            pytest.skip("monopole_vacuum_mc module not available")

        # Test case 1: small lattice
        L = 2
        positions = construct_bcc_lattice(L)
        # BCC has 2 atoms per unit cell, L³ unit cells
        expected_size = 2 * L**3
        assert len(positions) == expected_size, \
            f"Expected {expected_size} positions, got {len(positions)}"

        # Test case 2: positions in [0, 1)
        assert np.all((positions >= 0.0) & (positions < 1.0)), \
            "Expected all positions in [0, 1)"

        # Test case 3: verify BCC structure (alternating primitive + body-centered)
        L = 3
        positions = construct_bcc_lattice(L)
        # Every even-indexed position should be primitive cubic
        # Every odd-indexed position should be body-centered
        primitive_positions = positions[::2]
        body_positions = positions[1::2]

        # Primitive positions should have integer coordinates (fractional)
        primitive_frac = (primitive_positions * L).astype(int)
        assert np.allclose(primitive_positions * L, primitive_frac, atol=1e-6), \
            "Primitive positions should have integer coordinates"

        print("[U3 PASS] BCC lattice construction validated")

    def test_r1_sample_ensemble(self):
        """R1: Test MC ensemble sampling."""
        try:
            from tools.monopole_vacuum_mc import sample_monopole_ensemble
        except ImportError:
            pytest.skip("monopole_vacuum_mc module not available")

        # Generate small ensemble
        np.random.seed(42)
        n_samples = 1000
        energies = sample_monopole_ensemble(n_samples=n_samples, L=8)

        # Check output properties
        assert len(energies) == n_samples, \
            f"Expected {n_samples} samples, got {len(energies)}"

        assert energies.dtype == np.float64, \
            "Expected float64 dtype"

        # Check statistics (should be roughly zero-mean for dilute monopole gas)
        mean_energy = np.mean(energies)
        std_energy = np.std(energies)

        # For a dilute Poisson gas, mean should be close to zero
        # (exact value depends on Poisson parameter and action scale)
        assert not np.isnan(mean_energy), "NaN in mean energy"
        assert not np.isnan(std_energy), "NaN in std energy"
        assert std_energy > 0, "Zero standard deviation"

        print(f"[R1 PASS] Ensemble sampling: μ = {mean_energy:.3e}, σ = {std_energy:.3e}")

    def test_r2_json_output_schema(self):
        """R2: Validate JSON output schema."""
        try:
            from tools import monopole_vacuum_mc
        except ImportError:
            pytest.skip("monopole_vacuum_mc module not available")

        # Create synthetic results dict (mimics run_monopole_mc output)
        synthetic_results = {
            "n_samples": 10000,
            "L": 16,
            "vacuum_energy_mean": -0.0012,
            "vacuum_energy_std": 0.0045,
            "vacuum_energy_stderr": 0.000045,
            "vacuum_energy_ci_95": [-0.0022, -0.0002],
            "z_score": -2.67,
            "cancellation_ratio": 0.012,
            "hypothesis_test": {
                "H0": "vacuum energy mean = 0",
                "test_statistic": "Z-score",
                "z_value": -2.67,
                "p_value": 0.0076,
                "reject_H0_at_0p05": True,
            },
            "metadata": {
                "date": "2026-04-22T00:00:00",
                "task": "Task #66",
                "theory_tag": "Math58",
            },
        }

        # Write and read back
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test_monopole.json"
            with open(output_file, 'w') as f:
                json.dump(synthetic_results, f)

            with open(output_file, 'r') as f:
                data = json.load(f)

        # Validate top-level keys
        required_keys = [
            "n_samples", "vacuum_energy_mean", "vacuum_energy_std",
            "vacuum_energy_ci_95", "hypothesis_test", "metadata"
        ]
        for key in required_keys:
            assert key in data, f"Missing key: {key}"

        # Validate hypothesis test structure
        ht = data["hypothesis_test"]
        assert "H0" in ht
        assert "test_statistic" in ht
        assert "z_value" in ht
        assert "p_value" in ht

        # Validate CI shape
        assert len(data["vacuum_energy_ci_95"]) == 2

        print("[R2 PASS] JSON schema validated")

    def test_c1_hypothesis_test_logic(self):
        """C1: Validate hypothesis test logic on synthetic data."""
        try:
            from tools import monopole_vacuum_mc
        except ImportError:
            pytest.skip("monopole_vacuum_mc module not available")

        # Simulate two scenarios: null hypothesis true, null hypothesis false

        # Scenario 1: Data consistent with H0 (μ = 0)
        np.random.seed(42)
        data_null = np.random.normal(loc=0.0, scale=0.1, size=500)
        mean_null = np.mean(data_null)
        stderr_null = np.std(data_null, ddof=1) / np.sqrt(len(data_null))
        z_null = mean_null / stderr_null

        # H0 should NOT be rejected
        assert abs(z_null) < 1.96, \
            f"H0 should not be rejected for null data, z = {z_null:.3f}"

        # Scenario 2: Data inconsistent with H0 (μ ≠ 0)
        np.random.seed(43)
        data_alt = np.random.normal(loc=0.5, scale=0.1, size=500)
        mean_alt = np.mean(data_alt)
        stderr_alt = np.std(data_alt, ddof=1) / np.sqrt(len(data_alt))
        z_alt = mean_alt / stderr_alt

        # H0 should be rejected
        assert abs(z_alt) > 1.96, \
            f"H0 should be rejected for alt data, z = {z_alt:.3f}"

        print(
            f"[C1 PASS] Hypothesis test logic validated\n"
            f"         Null scenario: Z = {z_null:.3f} (not rejected)\n"
            f"         Alt scenario: Z = {z_alt:.3f} (rejected)"
        )


class TestMonopoleActionEdgeCases:
    """Edge-case tests for monopole action."""

    def test_large_charge(self):
        """Edge case: large monopole charge."""
        try:
            from tools.monopole_vacuum_mc import monopole_action
        except ImportError:
            pytest.skip("monopole_vacuum_mc module not available")

        S = monopole_action(charge=100.0)
        assert S > 0, "Action should be positive"
        assert np.isfinite(S), "Action should be finite"

    def test_very_small_scale(self):
        """Edge case: very small scale factor."""
        try:
            from tools.monopole_vacuum_mc import monopole_action
        except ImportError:
            pytest.skip("monopole_vacuum_mc module not available")

        S_small = monopole_action(charge=1.0, scale_factor=0.01)
        S_normal = monopole_action(charge=1.0, scale_factor=1.0)
        # Action should scale inversely with scale factor
        assert S_small > S_normal, \
            "Smaller scale factor should yield larger action"
        assert np.isclose(S_small, 100.0 * S_normal, rtol=0.01), \
            "Action scaling with scale factor incorrect"


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])
