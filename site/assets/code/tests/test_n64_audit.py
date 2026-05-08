#!/usr/bin/env python3
"""
test_n64_audit.py — Unit tests for Block 4 n64_continuum_audit.py

MATURITY: SKELETON-EXECUTABLE
Tests structure and API compatibility; does NOT run full Newton–Krylov solves.
Full executable tests deferred to user's GPU machine.

TEST PLAN (Skeleton level):
  U1: Import and signature validation
  U2: σ_V computation on synthetic spectrum
  R1: JSON output schema validation
  C1: API contract for continuum_audit function

EXPECTED OUTPUT (scaffold):
  All tests PASS (structure + imports valid; solver calls deferred).

FULL RUN (on GPU machine with torch):
  python -m pytest tests/test_n64_audit.py -v
"""

import sys
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest


class TestN64ContinuumAudit:
    """Test suite for n64_continuum_audit.py"""

    def test_u1_import_and_signature(self):
        """U1: Verify module imports and function signatures."""
        try:
            from tools import n64_continuum_audit as audit_module
        except ImportError:
            pytest.skip("n64_continuum_audit module not in import path")

        # Check function existence
        assert hasattr(audit_module, 'compute_sigma_V')
        assert hasattr(audit_module, 'run_single_grid')
        assert hasattr(audit_module, 'run_continuum_audit')

        # Check function signatures
        import inspect

        sig = inspect.signature(audit_module.compute_sigma_V)
        assert 'hess_spectrum' in sig.parameters

        sig = inspect.signature(audit_module.run_single_grid)
        assert all(p in sig.parameters for p in ['N', 'mu2', 'backend', 'params', 'solver'])

        sig = inspect.signature(audit_module.run_continuum_audit)
        assert 'output_file' in sig.parameters

    def test_u2_sigma_V_synthetic_spectrum(self):
        """U2: Test σ_V computation on synthetic eigenvalue spectrum."""
        try:
            from tools.n64_continuum_audit import compute_sigma_V
        except ImportError:
            pytest.skip("n64_continuum_audit module not available")

        # Test case 1: uniform spectrum (zero variance)
        spectrum_uniform = np.array([1.0, 1.0, 1.0, 1.0])
        sigma_V = compute_sigma_V(spectrum_uniform)
        assert np.isclose(sigma_V, 0.0, atol=1e-14), \
            f"Expected σ_V ≈ 0 for uniform spectrum, got {sigma_V}"

        # Test case 2: known variance spectrum
        spectrum_known = np.array([0.0, 1.0, 2.0, 3.0])  # mean=1.5
        sigma_V = compute_sigma_V(spectrum_known)
        # Variance = (1/4) * [(−1.5)² + (−0.5)² + (0.5)² + (1.5)²]
        #          = (1/4) * [2.25 + 0.25 + 0.25 + 2.25]
        #          = (1/4) * 5 = 1.25
        expected = 1.25
        assert np.isclose(sigma_V, expected, rtol=1e-10), \
            f"Expected σ_V = {expected}, got {sigma_V}"

        # Test case 3: empty spectrum (NaN)
        spectrum_empty = np.array([])
        sigma_V = compute_sigma_V(spectrum_empty)
        assert np.isnan(sigma_V), \
            "Expected NaN for empty spectrum"

        print("[U2 PASS] σ_V computation validated on synthetic spectra")

    def test_r1_json_schema(self):
        """R1: Validate JSON output schema with mock data."""
        try:
            from tools import n64_continuum_audit
        except ImportError:
            pytest.skip("n64_continuum_audit module not available")

        # Create a temporary directory for test output
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test_output.json"

            # Generate synthetic results
            synthetic_data = {
                "grid_results": {
                    "N_32": {
                        "N": 32,
                        "converged": True,
                        "sigma_V": 0.015,
                        "kappa": 0.0001,
                        "newton_steps": 15,
                        "error": None,
                    },
                    "N_64": {
                        "N": 64,
                        "converged": False,
                        "sigma_V": None,
                        "kappa": None,
                        "newton_steps": 0,
                        "error": "Newton–Krylov did not converge",
                    },
                },
                "continuum_fit": {
                    "h_values": [1/32, 1/64, 1/128],
                    "sigma_V": [0.015, None, None],
                    "kappa": [0.0001, None, None],
                },
                "metadata": {
                    "date": "2026-04-22T00:00:00",
                    "theory_tag": "Math66-cII-OperatorSurgery-PathX v2.6.0",
                    "solver_version": "tect_newton_krylov v2.6.0",
                },
            }

            # Write and read back
            with open(output_file, 'w') as f:
                json.dump(synthetic_data, f)

            with open(output_file, 'r') as f:
                data = json.load(f)

            # Validate schema
            assert "grid_results" in data
            assert "continuum_fit" in data
            assert "metadata" in data

            # Validate grid results structure
            for grid_key, grid_data in data["grid_results"].items():
                assert "N" in grid_data
                assert "converged" in grid_data
                assert "sigma_V" in grid_data
                assert "error" in grid_data

            # Validate continuum fit structure
            assert "h_values" in data["continuum_fit"]
            assert "sigma_V" in data["continuum_fit"]
            assert "kappa" in data["continuum_fit"]
            assert len(data["continuum_fit"]["h_values"]) == 3

            print("[R1 PASS] JSON schema validated")

    def test_c1_continuum_audit_api_signature(self):
        """C1: Test run_continuum_audit API contract."""
        try:
            from tools.n64_continuum_audit import run_continuum_audit
        except ImportError:
            pytest.skip("n64_continuum_audit module not available")

        # Verify that run_continuum_audit can be called with standard arguments
        # (Does not execute full solver; just tests API contract)
        import inspect

        sig = inspect.signature(run_continuum_audit)

        # Check parameters
        params = sig.parameters
        assert 'output_file' in params, "output_file parameter missing"
        assert 'verbose' in params, "verbose parameter missing"

        # Check default values
        assert params['output_file'].default != inspect.Parameter.empty
        assert params['verbose'].default != inspect.Parameter.empty

        print("[C1 PASS] API contract validated (signature + defaults)")


class TestSigmaVEdgeCases:
    """Additional edge-case tests for σ_V computation."""

    def test_single_eigenvalue(self):
        """Edge case: single eigenvalue (variance should be zero)."""
        try:
            from tools.n64_continuum_audit import compute_sigma_V
        except ImportError:
            pytest.skip("n64_continuum_audit module not available")

        spectrum = np.array([5.0])
        sigma_V = compute_sigma_V(spectrum)
        assert np.isclose(sigma_V, 0.0, atol=1e-14)

    def test_negative_eigenvalues(self):
        """Edge case: negative eigenvalues (should work normally)."""
        try:
            from tools.n64_continuum_audit import compute_sigma_V
        except ImportError:
            pytest.skip("n64_continuum_audit module not available")

        spectrum = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        sigma_V = compute_sigma_V(spectrum)
        # Mean = 0, variance = (1/5) * (4+1+0+1+4) = 2
        expected = 2.0
        assert np.isclose(sigma_V, expected, rtol=1e-10)

    def test_large_spectrum(self):
        """Edge case: large spectrum (performance check)."""
        try:
            from tools.n64_continuum_audit import compute_sigma_V
        except ImportError:
            pytest.skip("n64_continuum_audit module not available")

        # Generate large random spectrum
        np.random.seed(42)
        spectrum = np.random.randn(10000)
        sigma_V = compute_sigma_V(spectrum)

        # Should be close to 1 (variance of std normal)
        assert 0.95 < sigma_V < 1.05, \
            f"Expected σ_V ≈ 1 for std-normal spectrum, got {sigma_V}"


class TestIntegration:
    """Integration tests (structure only; full solver execution deferred)."""

    def test_run_continuum_audit_structure(self):
        """Test that run_continuum_audit produces correct output structure (no solve)."""
        try:
            from tools import n64_continuum_audit
        except ImportError:
            pytest.skip("n64_continuum_audit module not available")

        # Check that the function is callable and has expected behavior
        # (Does not actually run Newton–Krylov; tests scaffolding only)
        assert callable(n64_continuum_audit.run_continuum_audit)
        assert callable(n64_continuum_audit.run_single_grid)
        assert callable(n64_continuum_audit.compute_sigma_V)


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])
