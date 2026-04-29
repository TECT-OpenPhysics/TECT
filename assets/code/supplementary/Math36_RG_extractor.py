#!/usr/bin/env python3
"""
Math36-Addendum-A: Multi-scale RG-extractor Pipeline for Pillar 4 Q2

This module implements the five-step numerical extraction algorithm to extract
running gauge couplings (g_c, g_E, g_O) from a BCC ground-state field as a
function of renormalisation scale Lambda.

The pipeline reduces Pillar 4 Q2 from theoretical proof to numerical execution.

Status: PROVED REDUCIBLE (theory complete; numerical execution pending)
Theory tag: Math36-Addendum-A-multi-scale-RG-extractor-2026-04-24
Module version: v1.0
"""

import numpy as np
import json
from dataclasses import dataclass
from typing import Tuple, List, Dict, Optional
from pathlib import Path
import warnings

__version__ = "1.0"
__theory_version__ = "Math36-Addendum-A-2026-04-24"


@dataclass
class ExtractionConfig:
    """Configuration for RG-extractor pipeline."""
    lambda_uv: float = 10.0  # UV scale (reciprocal lattice units)
    lambda_ir: float = 1.0   # IR scale
    n_scales: int = 15        # number of intermediate scales
    epsilon_fp: float = 0.05  # fixed-point tolerance (5%)
    fp_window_factor: float = 2.0  # IR window is [lambda_ir, lambda_ir * factor]
    q0: float = 1.0           # BCC reciprocal lattice vector magnitude
    c_mono: float = 0.1       # monotonicity tolerance coefficient


class SpectralFilter:
    """Step 1: Spectral filtering to isolate long-wavelength modes."""

    @staticmethod
    def filter_field(psi_real: np.ndarray, lambda_cutoff: float,
                     lattice_spacing: float = 1.0) -> np.ndarray:
        """
        Apply spectral filter to field at cutoff scale Lambda.

        Args:
            psi_real: real-space field (3D numpy array)
            lambda_cutoff: momentum cutoff scale
            lattice_spacing: BCC lattice spacing

        Returns:
            psi_filtered: filtered field in real space
        """
        # FFT to momentum space
        psi_hat = np.fft.fftn(psi_real)
        psi_hat_shifted = np.fft.fftshift(psi_hat)

        # Construct k-grid
        N = psi_real.shape[0]
        k_grid = np.fft.fftfreq(N, d=lattice_spacing)
        kx, ky, kz = np.meshgrid(k_grid, k_grid, k_grid, indexing='ij')
        kmag = np.sqrt(kx**2 + ky**2 + kz**2)

        # Indicator function: 1 if |k| < lambda_cutoff
        indicator = (kmag < lambda_cutoff).astype(float)

        # Apply filter
        psi_hat_filtered = psi_hat_shifted * indicator
        psi_hat_filtered = np.fft.ifftshift(psi_hat_filtered)

        # IFFT back to real space
        psi_filtered = np.fft.ifftn(psi_hat_filtered).real

        return psi_filtered


class RawMoments:
    """Step 2: Compute raw moments W_0, W_2, M_2, G_4 at scale Lambda."""

    @staticmethod
    def compute_moments(psi_filtered: np.ndarray,
                       lattice_spacing: float = 1.0) -> Dict[str, float]:
        """
        Compute raw moments for the filtered field.

        Args:
            psi_filtered: real-space filtered field
            lattice_spacing: lattice spacing

        Returns:
            moments: dict with keys 'W0', 'W2', 'M2', 'G4', 'meff2'
        """
        N = psi_filtered.size

        # W_0: norm squared
        psi_sq = psi_filtered**2
        W0 = np.mean(psi_sq)

        # W_2: quadratic-momentum moment
        psi_hat = np.fft.fftn(psi_filtered)
        psi_hat_mag2 = np.abs(psi_hat)**2
        k_grid = np.fft.fftfreq(psi_filtered.shape[0], d=lattice_spacing)
        kx, ky, kz = np.meshgrid(k_grid, k_grid, k_grid, indexing='ij')
        kmag2 = kx**2 + ky**2 + kz**2
        W2 = np.sum(kmag2 * psi_hat_mag2) / (N * W0) if W0 > 1e-15 else 0.0

        # Effective mass squared (inverse correlation length squared)
        meff2 = W2 / (W0 + 1e-15) if W0 > 1e-15 else 0.0

        # M_2: fourth moment (connected)
        deviation = psi_sq - W0
        M2 = np.mean(deviation**2)

        # G_4: fourth-point coupling
        G4 = np.mean(psi_filtered**4)

        return {
            'W0': float(W0),
            'W2': float(W2),
            'M2': float(M2),
            'G4': float(G4),
            'meff2': float(meff2),
        }


class DirectionalDecomposition:
    """Step 3: Decompose G_4 along BCC first-shell directions."""

    # BCC first-shell direction orbits (normalised)
    CUBE_DIRECTIONS = np.array([
        [1, 1, 1], [1, 1, -1], [1, -1, 1], [1, -1, -1],
        [-1, 1, 1], [-1, 1, -1], [-1, -1, 1], [-1, -1, -1]
    ], dtype=float) / np.sqrt(3)

    EDGE_DIRECTIONS = np.array([
        [1, 0, 0], [-1, 0, 0],
        [0, 1, 0], [0, -1, 0],
        [0, 0, 1], [0, 0, -1]
    ], dtype=float)

    OCTAHEDRON_DIRECTIONS = np.array([
        [1, 1, 0], [1, -1, 0], [-1, 1, 0], [-1, -1, 0],
        [1, 0, 1], [1, 0, -1], [-1, 0, 1], [-1, 0, -1],
        [0, 1, 1], [0, 1, -1], [0, -1, 1], [0, -1, -1]
    ], dtype=float) / np.sqrt(2)

    @staticmethod
    def directional_coupling_amplitude(psi_filtered: np.ndarray,
                                       direction: np.ndarray,
                                       q0: float,
                                       lattice_spacing: float = 1.0) -> float:
        """
        Extract the Fourier amplitude along a specified direction.

        Args:
            psi_filtered: real-space field
            direction: BCC direction (normalised)
            q0: BCC reciprocal lattice vector magnitude
            lattice_spacing: lattice spacing

        Returns:
            amplitude: |F_direction|^2 where F is the Fourier amplitude along direction
        """
        N = psi_filtered.shape[0]
        phase_shift = q0 * np.dot(direction, np.array([
            np.arange(N).reshape(-1, 1, 1),
            np.arange(N).reshape(1, -1, 1),
            np.arange(N).reshape(1, 1, -1)
        ])) * (2 * np.pi / N)

        # Compute directional Fourier amplitude: sum_x psi(x)^2 * exp(i q0 hat_n · x)
        phase = np.exp(1j * phase_shift)
        amplitude_complex = np.sum(psi_filtered**2 * np.sum(phase, axis=0))
        amplitude = np.abs(amplitude_complex)**2

        return float(amplitude / N**2)

    @classmethod
    def decompose(cls, psi_filtered: np.ndarray, q0: float = 1.0,
                  lattice_spacing: float = 1.0) -> Dict[str, float]:
        """
        Decompose four-point coupling onto BCC first-shell orbits.

        Args:
            psi_filtered: real-space field
            q0: BCC reciprocal lattice vector magnitude
            lattice_spacing: lattice spacing

        Returns:
            couplings: dict with keys 'g_c', 'g_E', 'g_O'
        """
        # Cube orbit average
        g_c_list = []
        for direction in cls.CUBE_DIRECTIONS:
            amp = cls.directional_coupling_amplitude(psi_filtered, direction, q0, lattice_spacing)
            g_c_list.append(amp)
        g_c = np.mean(g_c_list) if g_c_list else 0.0

        # Edge orbit average
        g_E_list = []
        for direction in cls.EDGE_DIRECTIONS:
            amp = cls.directional_coupling_amplitude(psi_filtered, direction, q0, lattice_spacing)
            g_E_list.append(amp)
        g_E = np.mean(g_E_list) if g_E_list else 0.0

        # Octahedron orbit average
        g_O_list = []
        for direction in cls.OCTAHEDRON_DIRECTIONS:
            amp = cls.directional_coupling_amplitude(psi_filtered, direction, q0, lattice_spacing)
            g_O_list.append(amp)
        g_O = np.mean(g_O_list) if g_O_list else 0.0

        return {
            'g_c': float(g_c),
            'g_E': float(g_E),
            'g_O': float(g_O),
        }


class FlowReconstruction:
    """Step 4: Assemble RG flow trajectory at multiple scales."""

    @staticmethod
    def reconstruct_flow(psi_real: np.ndarray, config: ExtractionConfig,
                        lattice_spacing: float = 1.0) -> List[Dict]:
        """
        Reconstruct RG flow by executing Steps 1-3 at multiple scales.

        Args:
            psi_real: BCC ground-state field (3D array)
            config: ExtractionConfig with scale parameters
            lattice_spacing: lattice spacing

        Returns:
            flow: list of dicts with keys 'lambda', 'g_c', 'g_E', 'g_O', 'W0', 'W2', 'M2', 'G4', 'meff2'
        """
        # Generate scale sequence: geometric progression from lambda_UV down to lambda_IR
        r = (config.lambda_ir / config.lambda_uv)**(1.0 / config.n_scales)
        scales = [config.lambda_uv * (r**j) for j in range(config.n_scales + 1)]

        flow = []
        for lam in scales:
            # Step 1: spectral filter
            psi_filtered = SpectralFilter.filter_field(psi_real, lam, lattice_spacing)

            # Step 2: raw moments
            moments = RawMoments.compute_moments(psi_filtered, lattice_spacing)

            # Step 3: directional decomposition
            couplings = DirectionalDecomposition.decompose(psi_filtered, config.q0, lattice_spacing)

            # Assemble result
            entry = {
                'lambda': float(lam),
                **moments,
                **couplings,
            }
            flow.append(entry)

        return flow


class FixedPointCheck:
    """Step 5: Verify fixed-point condition in IR limit."""

    @staticmethod
    def detect_fixed_point(flow: List[Dict], config: ExtractionConfig) -> Dict:
        """
        Detect fixed point by checking convergence in IR window.

        Args:
            flow: RG flow trajectory (from FlowReconstruction)
            config: ExtractionConfig with fixed-point parameters

        Returns:
            result: dict with keys:
                - 'fixed_point_exists': bool
                - 'g_c_fp', 'g_E_fp', 'g_O_fp': fixed-point values
                - 'variance_c', 'variance_E', 'variance_O': variances in IR window
                - 'ir_window': [lambda_start, lambda_end]
                - 'falsification_F1_pass': bool
                - 'falsification_F2_pass': bool
                - 'falsification_F3_pass': bool
                - 'coupling_ratios': {'R_c_E': g_c/g_E, 'R_E_O': g_E/g_O}
        """
        lambda_ir = config.lambda_ir
        ir_window_end = lambda_ir * config.fp_window_factor

        # Extract points in IR window
        ir_points = [pt for pt in flow if lambda_ir <= pt['lambda'] <= ir_window_end]

        if len(ir_points) < 3:
            warnings.warn(f"Only {len(ir_points)} points in IR window; fixed-point detection unreliable.")

        g_c_vals = np.array([pt['g_c'] for pt in ir_points])
        g_E_vals = np.array([pt['g_E'] for pt in ir_points])
        g_O_vals = np.array([pt['g_O'] for pt in ir_points])

        # Compute variances
        var_c = float(np.var(g_c_vals)) if len(g_c_vals) > 0 else 0.0
        var_E = float(np.var(g_E_vals)) if len(g_E_vals) > 0 else 0.0
        var_O = float(np.var(g_O_vals)) if len(g_O_vals) > 0 else 0.0

        # Fixed-point values (mean in IR window)
        g_c_fp = float(np.mean(g_c_vals)) if len(g_c_vals) > 0 else 0.0
        g_E_fp = float(np.mean(g_E_vals)) if len(g_E_vals) > 0 else 0.0
        g_O_fp = float(np.mean(g_O_vals)) if len(g_O_vals) > 0 else 0.0

        # Falsification F1: variance test
        max_var = max(var_c, var_E, var_O)
        max_g = max(g_c_fp, g_E_fp, g_O_fp) if max(g_c_fp, g_E_fp, g_O_fp) > 0 else 1.0
        f1_ratio = max_var / (max_g**2) if max_g**2 > 0 else float('inf')
        f1_pass = f1_ratio < 0.05

        # Falsification F2: coupling ratios (test against SM expectations)
        # Expected: alpha_3:alpha_2:alpha_1 ~ 0.118:0.034:0.010
        # So g_c:g_E:g_O should scale similarly (within factor of 2-6)
        ratio_c_E = g_c_fp / (g_E_fp + 1e-15)
        ratio_E_O = g_E_fp / (g_O_fp + 1e-15)
        f2_pass = (2.5 <= ratio_c_E <= 4.5) and (2.0 <= ratio_E_O <= 6.0)

        # Falsification F3: monotonicity
        # Compute slopes d(g)/d(log Lambda) and check they don't oscillate
        lambdas = np.array([pt['lambda'] for pt in flow])
        log_lambdas = np.log(lambdas)

        slopes_c = np.gradient(g_c_vals, np.log(lambdas[len(flow)-len(ir_points):]))
        slopes_E = np.gradient(g_E_vals, np.log(lambdas[len(flow)-len(ir_points):]))
        slopes_O = np.gradient(g_O_vals, np.log(lambdas[len(flow)-len(ir_points):]))

        # Check for oscillation (no sign changes in slope)
        f3_pass = True
        for slopes in [slopes_c, slopes_E, slopes_O]:
            if len(slopes) > 1:
                sign_changes = np.sum(np.diff(np.sign(slopes + 1e-15)) != 0)
                if sign_changes > 1:
                    f3_pass = False

        return {
            'fixed_point_exists': f1_pass,
            'g_c_fp': g_c_fp,
            'g_E_fp': g_E_fp,
            'g_O_fp': g_O_fp,
            'variance_c': var_c,
            'variance_E': var_E,
            'variance_O': var_O,
            'ir_window': [float(lambda_ir), float(ir_window_end)],
            'falsification_F1_pass': f1_pass,
            'falsification_F2_pass': f2_pass,
            'falsification_F3_pass': f3_pass,
            'coupling_ratios': {
                'R_c_E': ratio_c_E,
                'R_E_O': ratio_E_O,
            },
        }


class RGExtractorPipeline:
    """Main 5-step RG-extractor pipeline."""

    def __init__(self, config: Optional[ExtractionConfig] = None):
        """
        Initialise the pipeline.

        Args:
            config: ExtractionConfig (uses defaults if None)
        """
        self.config = config if config is not None else ExtractionConfig()

    def execute(self, psi_real: np.ndarray,
               lattice_spacing: float = 1.0) -> Dict:
        """
        Execute the complete 5-step RG-extractor pipeline.

        Args:
            psi_real: BCC ground-state field (3D real-space array)
            lattice_spacing: lattice spacing (default 1.0)

        Returns:
            result: dict with keys:
                - 'flow': RG flow trajectory (list of dicts)
                - 'fixed_point': fixed-point analysis result
                - 'config': configuration used
                - 'summary': human-readable summary string
        """
        # Step 4: Flow reconstruction (encompasses Steps 1-3)
        flow = FlowReconstruction.reconstruct_flow(psi_real, self.config, lattice_spacing)

        # Step 5: Fixed-point detection
        fixed_point = FixedPointCheck.detect_fixed_point(flow, self.config)

        # Generate summary
        summary = self._generate_summary(flow, fixed_point)

        return {
            'flow': flow,
            'fixed_point': fixed_point,
            'config': {
                'lambda_uv': self.config.lambda_uv,
                'lambda_ir': self.config.lambda_ir,
                'n_scales': self.config.n_scales,
                'epsilon_fp': self.config.epsilon_fp,
            },
            'summary': summary,
        }

    @staticmethod
    def _generate_summary(flow: List[Dict], fixed_point: Dict) -> str:
        """Generate a human-readable summary."""
        summary = []
        summary.append("=== RG-Extractor Pipeline Summary ===")
        summary.append(f"Scales evaluated: {len(flow)}")
        summary.append(f"UV scale: {flow[0]['lambda']:.4e}, IR scale: {flow[-1]['lambda']:.4e}")
        summary.append("")
        summary.append(f"Fixed-point (g_c, g_E, g_O): ({fixed_point['g_c_fp']:.6e}, {fixed_point['g_E_fp']:.6e}, {fixed_point['g_O_fp']:.6e})")
        summary.append(f"Variances: ({fixed_point['variance_c']:.6e}, {fixed_point['variance_E']:.6e}, {fixed_point['variance_O']:.6e})")
        summary.append(f"Coupling ratios (g_c/g_E, g_E/g_O): ({fixed_point['coupling_ratios']['R_c_E']:.3f}, {fixed_point['coupling_ratios']['R_E_O']:.3f})")
        summary.append("")
        summary.append("Falsification tests:")
        summary.append(f"  F1 (fixed-point existence): {'PASS' if fixed_point['falsification_F1_pass'] else 'FAIL'}")
        summary.append(f"  F2 (SM coupling ratios):    {'PASS' if fixed_point['falsification_F2_pass'] else 'FAIL'}")
        summary.append(f"  F3 (monotonicity):          {'PASS' if fixed_point['falsification_F3_pass'] else 'FAIL'}")
        summary.append("")
        if fixed_point['fixed_point_exists'] and fixed_point['falsification_F1_pass'] and fixed_point['falsification_F2_pass'] and fixed_point['falsification_F3_pass']:
            summary.append("VERDICT: All falsification gates PASS. Q2 gauge-emergence hypothesis is numerically supported.")
        else:
            summary.append("VERDICT: Some falsification gates FAIL. Extraction method or physics assumptions require revision.")

        return "\n".join(summary)


# =========================================================================
# Main entry point for testing / execution
# =========================================================================

def main():
    """
    Minimal test harness: create a synthetic BCC-like field and extract RG flow.
    """
    print("Math36-Addendum-A RG-Extractor Pipeline v1.0")
    print("=" * 60)
    print()

    # Create synthetic test field: 3D cosine (simplified BCC representation)
    N = 32  # lattice size
    x = np.arange(N, dtype=float)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')

    # Synthetic BCC ground state: sum of cosines along first-shell directions
    psi_synthetic = (
        np.cos(2*np.pi*X/N) * np.cos(2*np.pi*Y/N) * np.cos(2*np.pi*Z/N) +  # cube
        np.cos(2*np.pi*X/N) + np.cos(2*np.pi*Y/N) + np.cos(2*np.pi*Z/N)     # edges
    )
    psi_synthetic = np.abs(psi_synthetic)  # ensure positivity
    psi_synthetic /= np.linalg.norm(psi_synthetic)  # normalise

    # Run pipeline
    config = ExtractionConfig(
        lambda_uv=10.0,
        lambda_ir=1.0,
        n_scales=15,
        q0=2*np.pi  # BCC reciprocal lattice scale
    )

    pipeline = RGExtractorPipeline(config)
    result = pipeline.execute(psi_synthetic, lattice_spacing=1.0)

    # Print results
    print(result['summary'])
    print()
    print("First 5 flow points:")
    for i, pt in enumerate(result['flow'][:5]):
        print(f"  Lambda={pt['lambda']:.4e}: g_c={pt['g_c']:.4e}, g_E={pt['g_E']:.4e}, g_O={pt['g_O']:.4e}")

    # Save result to JSON
    output_file = Path("Math36_extractor_result.json")
    with open(output_file, 'w') as f:
        # Convert numpy arrays and floats for JSON serialization
        json_result = {
            'flow': result['flow'],
            'fixed_point': result['fixed_point'],
            'config': result['config'],
            'summary': result['summary'],
        }
        json.dump(json_result, f, indent=2)

    print()
    print(f"Result saved to: {output_file}")


if __name__ == "__main__":
    main()
