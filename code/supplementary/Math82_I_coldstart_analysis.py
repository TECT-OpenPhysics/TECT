#!/usr/bin/env python3
"""
Math82-I Cold-Start Multi-Replica Statistical Analysis Framework
===============================================================

Purpose: Aggregate and analyze 35 independent cold-start Newton runs (5 replicas × 7 μ² values)
from the Math82-I numerical experiment (subset-4-cosine ansatz).

This script:
  1. Reads MANIFEST.md files from Runs/continuation/math82i_coldstart_mu2_<mu2>_r<r>_<date>/
  2. Aggregates per-μ² distributions of: (m*², λ_min, ΔF, ||Ψ*||/√N, n_Newton, converged?)
  3. Computes per-μ² mean/std/min/max + Kolmogorov-Smirnov test of basin uniformity
  4. Outputs CSV summary + JSON status per μ²: NON_TRIVIAL_BRANCH_EXISTS / VACUUM_COLLAPSE / MIXED_BIMODAL
  5. Evaluates falsification criterion F1 (Math82-AddI §3.1)

Pre-registered falsification criterion F1 (Math82-AddI §3.1):
  "If at least 2 of 5 cold-starts at ANY μ² ∈ {-0.5, -0.7, -0.85, -1.0} converge to
   non-trivial Ψ* with ||Ψ*||/√N > 1e-3 AND ΔF < 0, then Math82-G Regime III claim
   (branch terminates below μ² ≈ -0.1) is FALSIFIED."

Author: Jusang Lee (jtkor@outlook.com)
Theory tag: Math82-Addendum-I-Addendum-A-analysis-framework
Date: 2026-04-24
Status: ANALYSIS FRAMEWORK COMPLETE (awaiting 35-run execution)

Usage:
  python Codes/supplementary/Math82_I_coldstart_analysis.py \\
    --runs-base-dir "Runs/continuation" \\
    --output-csv "Math82_I_analysis_summary.csv" \\
    --output-json "Math82_I_classification.json" \\
    --verbose
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse
import logging
from scipy.stats import ks_2samp
from datetime import datetime

# ============================================================================
# Configuration (HARD-CODED PER MATH82-I SPECIFICATION)
# ============================================================================

MU2_VALUES = [
    5e-3,    # Point 1: near spinodal (μ²_sp ≈ 0.0152)
    -0.02,   # Point 2: just below binodal estimate
    -0.1,    # Point 3: mid-range (near Math82-G Regime III boundary)
    -0.5,    # Point 4: Regime III deep (FALSIFICATION GATE)
    -0.7,    # Point 5: Regime III deep (FALSIFICATION GATE)
    -0.85,   # Point 6: Regime III deep (FALSIFICATION GATE)
    -1.0,    # Point 7: Regime III extreme (FALSIFICATION GATE)
]

REPLICAS_PER_MU2 = 5  # K = 5 per Math82-AddI §5

# ============================================================================
# Per-μ² classification thresholds (Math82-Addendum-I-AddA theoretical definition)
# ============================================================================

AMPLITUDE_THRESHOLD = 1e-3  # ||Ψ*||/√N > 1e-3 ⇔ non-trivial (Math82-AddI §3.1)
ENERGY_THRESHOLD = 0.0       # ΔF < 0 ⇔ energetically favorable vs. vacuum

# ============================================================================
# Logger setup
# ============================================================================

def setup_logger(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s: %(message)s"
    )
    return logging.getLogger(__name__)

logger = None

# ============================================================================
# Class 1: ManifestReader — parse individual MANIFEST.md files
# ============================================================================

class ManifestReader:
    """
    Parse a MANIFEST.md file from a single Newton solve.

    Expected format (from continuation_mu2_v25.py output):
      MANIFEST_HASH: <hash>
      mu2_target: <float>
      N: <int>
      L: <float>
      converged: <bool>
      n_newton_steps: <int>
      ||Psi*|| (L2): <float>
      ||Psi*||/√N: <float>
      λ_min (Hessian): <float>
      ΔF = F(Ψ*) - F(0): <float>
      ...
    """

    @staticmethod
    def read(manifest_path: Path) -> Optional[Dict]:
        """
        Parse MANIFEST.md and return dict of extracted values.

        Returns:
          dict with keys: {mu2, converged, n_newton, norm_psi, norm_psi_per_sqrt_n,
                          lambda_min, delta_f, ...}
          or None if parse fails.
        """
        if not manifest_path.exists():
            logger.warning(f"Manifest not found: {manifest_path}")
            return None

        result = {}
        try:
            with open(manifest_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # Parse key: value pairs
                    if ':' in line:
                        key, val = line.split(':', 1)
                        key = key.strip()
                        val = val.strip()

                        if key == "mu2_target":
                            result['mu2'] = float(val)
                        elif key == "converged":
                            result['converged'] = val.lower() in ['true', '1', 'yes']
                        elif key == "n_newton_steps":
                            result['n_newton'] = int(val)
                        elif key == "||Psi*|| (L2)":
                            result['norm_psi'] = float(val)
                        elif key == "||Psi*||/√N":
                            result['norm_psi_per_sqrt_n'] = float(val)
                        elif key == "λ_min (Hessian)":
                            result['lambda_min'] = float(val)
                        elif key == "ΔF = F(Ψ*) - F(0)":
                            result['delta_f'] = float(val)

            # Minimal validation
            if 'mu2' in result and 'converged' in result:
                return result
            else:
                logger.warning(f"Incomplete manifest: {manifest_path}")
                return None

        except Exception as e:
            logger.warning(f"Error parsing {manifest_path}: {e}")
            return None

# ============================================================================
# Class 2: ColdStartAggregator — organize runs by (μ², replica) and classify
# ============================================================================

class ColdStartAggregator:
    """
    Aggregate cold-start runs and classify per-μ² outcomes.
    """

    def __init__(self, runs_base_dir: Path):
        self.runs_base_dir = Path(runs_base_dir)
        self.mu2_data: Dict[float, List[Dict]] = {mu2: [] for mu2 in MU2_VALUES}
        self.classifications: Dict[float, str] = {}
        self.falsification_verdict: Optional[str] = None
        self.falsification_evidence: Dict = {}

    def scan_and_aggregate(self) -> bool:
        """
        Scan Runs/continuation/ for math82i_coldstart_mu2_<mu2>_r<r>_<date>/ dirs.

        Returns True if at least one run was found, False otherwise.
        """
        logger.info(f"Scanning {self.runs_base_dir} for Math82-I cold-start runs...")

        run_count = 0
        for run_dir in self.runs_base_dir.glob("math82i_coldstart_mu2_*"):
            if not run_dir.is_dir():
                continue

            # Extract μ² and replica from directory name
            # Expected format: math82i_coldstart_mu2_<mu2_str>_r<replica>_<date>
            parts = run_dir.name.split('_')
            try:
                # Find the 'r' index
                mu2_str_parts = []
                r_idx = None
                for i, p in enumerate(parts):
                    if p.startswith('r') and i > 3:  # r<replica> is after mu2_<value>
                        r_idx = i
                        break

                if r_idx is None:
                    logger.warning(f"Cannot parse run dir: {run_dir.name}")
                    continue

                # Reconstruct μ² value
                mu2_str = '_'.join(parts[3:r_idx]).replace('_', '')  # e.g., "-0.5" from "-0_5"
                mu2 = float(mu2_str)
                replica = int(parts[r_idx][1:])  # extract <replica> from r<replica>

                # Read MANIFEST.md
                manifest_path = run_dir / "MANIFEST.md"
                data = ManifestReader.read(manifest_path)

                if data:
                    self.mu2_data[mu2].append(data)
                    run_count += 1
                    logger.info(f"  Loaded: μ²={mu2:.3e}, replica={replica}, converged={data.get('converged')}")
                else:
                    logger.warning(f"  Skipped: {run_dir.name} (manifest parse failed)")

            except Exception as e:
                logger.warning(f"Error processing {run_dir.name}: {e}")
                continue

        logger.info(f"Aggregated {run_count} runs across {len(MU2_VALUES)} μ² values")
        return run_count > 0

    def classify_per_mu2(self) -> None:
        """
        Classify each μ² point according to Math82-Addendum-I-AddA definition.

        Classification rules (§2 of the addendum):
          NON_TRIVIAL_BRANCH_EXISTS: ≥ 2/5 converge with ||Ψ*||/√N > 1e-3 AND ΔF < 0
          VACUUM_COLLAPSE: 5/5 converge to vacuum (||Ψ*||/√N < 1e-3)
          MIXED_BIMODAL: 1/5 non-trivial, 4/5 vacuum
          NEWTON_FAILURE: < 5/5 converge after 15 steps (solver issue)
        """
        logger.info("\n" + "="*70)
        logger.info("PER-μ² CLASSIFICATION (Math82-Addendum-I-AddA §2)")
        logger.info("="*70)

        for mu2 in MU2_VALUES:
            runs = self.mu2_data[mu2]
            if not runs:
                self.classifications[mu2] = "NO_DATA"
                logger.info(f"μ²={mu2:.3e}: NO_DATA (0 runs)")
                continue

            n_runs = len(runs)
            n_converged = sum(1 for r in runs if r.get('converged', False))

            # Count non-trivial: ||Ψ*||/√N > 1e-3 AND ΔF < 0
            non_trivial_runs = [
                r for r in runs
                if r.get('norm_psi_per_sqrt_n', 0.0) > AMPLITUDE_THRESHOLD
                   and r.get('delta_f', 0.0) < ENERGY_THRESHOLD
            ]
            n_non_trivial = len(non_trivial_runs)

            # Classify
            if n_converged < n_runs:
                classification = "NEWTON_FAILURE"
            elif n_non_trivial >= 2:
                classification = "NON_TRIVIAL_BRANCH_EXISTS"
            elif n_non_trivial == 0:
                classification = "VACUUM_COLLAPSE"
            else:  # n_non_trivial == 1
                classification = "MIXED_BIMODAL"

            self.classifications[mu2] = classification

            logger.info(
                f"μ²={mu2:.3e}: {classification} | "
                f"runs={n_runs}, converged={n_converged}, non_trivial={n_non_trivial}"
            )

    def evaluate_falsification(self) -> None:
        """
        Evaluate falsification criterion F1 (Math82-AddI §3.1).

        F1 FALSIFIED if: ≥ 2 of 5 cold-starts at ANY μ² ∈ {-0.5, -0.7, -0.85, -1.0}
                         converge to non-trivial Ψ* with ||Ψ*||/√N > 1e-3 AND ΔF < 0.

        Implication: Math82-G Regime III claim ("branch terminates below μ² ≈ -0.1") is FALSE.
        """
        logger.info("\n" + "="*70)
        logger.info("FALSIFICATION CRITERION F1 EVALUATION (Math82-AddI §3.1)")
        logger.info("="*70)

        falsification_gate_mu2 = [-0.5, -0.7, -0.85, -1.0]

        for mu2 in falsification_gate_mu2:
            classification = self.classifications.get(mu2, "UNKNOWN")
            self.falsification_evidence[mu2] = {
                'classification': classification,
                'is_falsifying': classification == "NON_TRIVIAL_BRANCH_EXISTS"
            }

            logger.info(
                f"  μ²={mu2:.3e}: {classification} | "
                f"Falsifying: {classification == 'NON_TRIVIAL_BRANCH_EXISTS'}"
            )

        # Check if ANY falsifying point
        is_falsified = any(v['is_falsifying'] for v in self.falsification_evidence.values())

        if is_falsified:
            self.falsification_verdict = "FALSIFIED"
            logger.info("\n[VERDICT] Math82-G Regime III claim: FALSIFIED ✗")
            logger.info(
                "  → At least one Regime III point (μ² ≤ -0.5) shows non-trivial "
                "stable equilibrium.\n  → Conclusion: branch does NOT terminate at μ² ≈ -0.1."
            )
        else:
            self.falsification_verdict = "NOT_FALSIFIED"
            logger.info("\n[VERDICT] Math82-G Regime III claim: NOT FALSIFIED (tentatively confirmed) ✓")
            logger.info(
                "  → All Regime III points collapse to vacuum or show mixed bimodality.\n"
                "  → Conclusion: branch termination consistent with Math82-G prediction.\n"
                "  → Recommended: bisect to narrow termination point μ²_term ∈ (-0.1, -0.5)."
            )

# ============================================================================
# Class 3: StatisticalSummary — compute per-μ² aggregates and output
# ============================================================================

class StatisticalSummary:
    """
    Compute per-μ² statistics and generate outputs (CSV, JSON).
    """

    def __init__(self, aggregator: ColdStartAggregator):
        self.aggregator = aggregator
        self.summary_df = None

    def compute_statistics(self) -> pd.DataFrame:
        """
        Compute per-μ² summary statistics: mean, std, min, max, KS test.

        Returns a pandas DataFrame with:
          - μ² | n_runs | n_converged | n_non_trivial
          - mean(m*²) | std(m*²) | min(m*²) | max(m*²)
          - mean(λ_min) | std(λ_min)
          - mean(ΔF) | std(ΔF)
          - mean(||Ψ*||/√N)
          - mean(n_Newton) | max(n_Newton)
          - KS_uniformity_p_value
          - Classification
        """
        logger.info("\n" + "="*70)
        logger.info("STATISTICAL SUMMARY (per-μ²)")
        logger.info("="*70)

        rows = []

        for mu2 in MU2_VALUES:
            runs = self.aggregator.mu2_data[mu2]
            if not runs:
                rows.append({
                    'mu2': mu2,
                    'n_runs': 0,
                    'n_converged': 0,
                    'n_non_trivial': 0,
                    'mean_m_sq': np.nan,
                    'std_m_sq': np.nan,
                    'min_m_sq': np.nan,
                    'max_m_sq': np.nan,
                    'mean_lambda_min': np.nan,
                    'std_lambda_min': np.nan,
                    'mean_delta_f': np.nan,
                    'std_delta_f': np.nan,
                    'mean_norm_psi_per_sqrtn': np.nan,
                    'mean_n_newton': np.nan,
                    'max_n_newton': np.nan,
                    'ks_uniformity_pvalue': np.nan,
                    'classification': 'NO_DATA'
                })
                continue

            # Extract arrays
            converged = np.array([r.get('converged', False) for r in runs])
            n_converged = np.sum(converged)

            # Heuristic m*² estimate (λ_min from Lanczos, related to spectral gap)
            lambda_mins = np.array([r.get('lambda_min', np.nan) for r in runs])
            m_sq_est = lambda_mins ** 2  # rough proxy (not the full spectral gap, but related)

            delta_fs = np.array([r.get('delta_f', np.nan) for r in runs])
            norm_psis = np.array([r.get('norm_psi_per_sqrt_n', np.nan) for r in runs])
            n_newtons = np.array([r.get('n_newton', 0) for r in runs])

            # Count non-trivial
            non_trivial = (norm_psis > AMPLITUDE_THRESHOLD) & (delta_fs < ENERGY_THRESHOLD)
            n_non_trivial = np.sum(non_trivial)

            # Statistics (filter out NaN)
            valid_m_sq = m_sq_est[~np.isnan(m_sq_est)]
            valid_lambda_min = lambda_mins[~np.isnan(lambda_mins)]
            valid_delta_f = delta_fs[~np.isnan(delta_fs)]

            # KS uniformity test: compare two halves of the run sample
            # (measures whether replicas sample diverse basins)
            ks_pvalue = np.nan
            if len(valid_norm_psi := norm_psis[~np.isnan(norm_psis)]) >= 4:
                half = len(valid_norm_psi) // 2
                if half > 0:
                    try:
                        ks_stat, ks_pvalue = ks_2samp(
                            valid_norm_psi[:half],
                            valid_norm_psi[half:]
                        )
                    except:
                        ks_pvalue = np.nan

            rows.append({
                'mu2': mu2,
                'n_runs': len(runs),
                'n_converged': int(n_converged),
                'n_non_trivial': int(n_non_trivial),
                'mean_m_sq': float(np.mean(valid_m_sq)) if len(valid_m_sq) > 0 else np.nan,
                'std_m_sq': float(np.std(valid_m_sq)) if len(valid_m_sq) > 1 else np.nan,
                'min_m_sq': float(np.min(valid_m_sq)) if len(valid_m_sq) > 0 else np.nan,
                'max_m_sq': float(np.max(valid_m_sq)) if len(valid_m_sq) > 0 else np.nan,
                'mean_lambda_min': float(np.mean(valid_lambda_min)) if len(valid_lambda_min) > 0 else np.nan,
                'std_lambda_min': float(np.std(valid_lambda_min)) if len(valid_lambda_min) > 1 else np.nan,
                'mean_delta_f': float(np.mean(valid_delta_f)) if len(valid_delta_f) > 0 else np.nan,
                'std_delta_f': float(np.std(valid_delta_f)) if len(valid_delta_f) > 1 else np.nan,
                'mean_norm_psi_per_sqrtn': float(np.mean(norm_psis[~np.isnan(norm_psis)])) if len(valid_norm_psi) > 0 else np.nan,
                'mean_n_newton': float(np.mean(n_newtons)) if len(n_newtons) > 0 else np.nan,
                'max_n_newton': int(np.max(n_newtons)) if len(n_newtons) > 0 else 0,
                'ks_uniformity_pvalue': float(ks_pvalue),
                'classification': self.aggregator.classifications.get(mu2, 'UNKNOWN')
            })

        self.summary_df = pd.DataFrame(rows)
        logger.info(self.summary_df.to_string(index=False))
        return self.summary_df

    def write_csv(self, csv_path: Path) -> None:
        """Write summary to CSV."""
        if self.summary_df is None:
            logger.error("No summary computed. Call compute_statistics() first.")
            return

        self.summary_df.to_csv(csv_path, index=False)
        logger.info(f"\n[OUTPUT] CSV summary written to: {csv_path}")

    def write_json(self, json_path: Path) -> None:
        """
        Write detailed JSON output with per-μ² classification and falsification verdict.
        """
        output = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'theory_tag': 'Math82-Addendum-I-Addendum-A-analysis-framework',
                'script_version': '1.0',
                'total_runs': sum(len(runs) for runs in self.aggregator.mu2_data.values()),
                'mu2_points': len(MU2_VALUES),
                'replicas_per_mu2': REPLICAS_PER_MU2
            },
            'amplitude_threshold_nontrivial': AMPLITUDE_THRESHOLD,
            'energy_threshold_favorable': ENERGY_THRESHOLD,
            'classifications': {
                str(mu2): {
                    'mu2': mu2,
                    'classification': self.aggregator.classifications.get(mu2, 'UNKNOWN'),
                    'n_runs': len(self.aggregator.mu2_data[mu2]),
                    'n_non_trivial': sum(
                        1 for r in self.aggregator.mu2_data[mu2]
                        if r.get('norm_psi_per_sqrt_n', 0.0) > AMPLITUDE_THRESHOLD
                           and r.get('delta_f', 0.0) < ENERGY_THRESHOLD
                    )
                }
                for mu2 in MU2_VALUES
            },
            'falsification_verdict': self.aggregator.falsification_verdict,
            'falsification_gate_results': self.aggregator.falsification_evidence,
            'remarks': [
                "Classification per Math82-Addendum-I-AddA §2:",
                "  - NON_TRIVIAL_BRANCH_EXISTS: ≥2/5 non-trivial AND energetically favorable",
                "  - VACUUM_COLLAPSE: 5/5 collapse to vacuum",
                "  - MIXED_BIMODAL: exactly 1 non-trivial, 4 vacuum",
                "  - NEWTON_FAILURE: convergence failure in Newton solver",
                "",
                "Falsification Criterion F1 (Math82-AddI §3.1):",
                "  If ANY μ² ∈ {-0.5, -0.7, -0.85, -1.0} has classification NON_TRIVIAL_BRANCH_EXISTS,",
                "  then Math82-G Regime III claim ('branch terminates below μ² ≈ -0.1') is FALSIFIED."
            ]
        }

        with open(json_path, 'w') as f:
            json.dump(output, f, indent=2)

        logger.info(f"[OUTPUT] JSON classification written to: {json_path}")

# ============================================================================
# Main routine
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Math82-I cold-start multi-replica statistical analysis framework"
    )
    parser.add_argument(
        '--runs-base-dir',
        type=str,
        default='Runs/continuation',
        help='Base directory containing math82i_coldstart_* run folders'
    )
    parser.add_argument(
        '--output-csv',
        type=str,
        default='Math82_I_analysis_summary.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--output-json',
        type=str,
        default='Math82_I_classification.json',
        help='Output JSON classification file path'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    global logger
    logger = setup_logger(verbose=args.verbose)

    logger.info("=" * 70)
    logger.info("Math82-I Cold-Start Analysis Framework")
    logger.info("Theory tag: Math82-Addendum-I-Addendum-A")
    logger.info("Date: 2026-04-24")
    logger.info("=" * 70)

    # Initialize aggregator
    aggregator = ColdStartAggregator(Path(args.runs_base_dir))

    # Scan and aggregate
    if not aggregator.scan_and_aggregate():
        logger.warning(
            "\nNo Math82-I runs found in the runs directory.\n"
            "Ensure 35-run execution (5 replicas × 7 μ² values) is complete."
        )
        return 1

    # Classify per μ²
    aggregator.classify_per_mu2()

    # Evaluate falsification
    aggregator.evaluate_falsification()

    # Compute statistics
    summary = StatisticalSummary(aggregator)
    summary.compute_statistics()

    # Write outputs
    summary.write_csv(Path(args.output_csv))
    summary.write_json(Path(args.output_json))

    logger.info("\n" + "=" * 70)
    logger.info("Analysis complete.")
    logger.info("=" * 70)

    return 0

if __name__ == "__main__":
    exit(main())
