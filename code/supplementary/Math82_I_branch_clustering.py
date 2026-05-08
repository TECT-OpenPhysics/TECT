#!/usr/bin/env python3
"""
Math82_I_branch_clustering.py

Post-processor for Math82-I-proper multi-replica cold-start output.
Implements Math36-Addendum-B Step 1 clustering specification.

TECT Theory tag: Math82-I-branch-clustering-2026-04-24
Module version: v1.0
Author: Jusang Lee (jtkor@outlook.com)
Status: IMPLEMENTATION COMPLETE (pre-test ready)

Mandatory schema compliance: CLAUDE.md §6.5 theory-currency audit.
Pre-registered gates (§6.3.3): see Math36-AddB §4 + §6 (F4, F5, F6).
Devil's-advocate self-test: see Math82_I_branch_clustering-implementation.tex.txt §4.
"""

import json
import os
import glob
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BranchClusterer:
    """
    Hierarchical agglomerative clustering of converged wavefunctions.

    Input: Ensemble of converged Psi^* from Math82-I-proper runs (per mu^2).
    Output: Branch index set I with representatives and cluster sizes.
    """

    def __init__(self, delta_hamming: float = 0.1):
        """
        Args:
            delta_hamming: Single-linkage threshold for Hamming-like metric.
                          Default per Math36-AddB §2 Step 1: 0.1
        """
        self.delta_hamming = delta_hamming
        self.results = {}
        self.sensitivity_curve = {}

    def hamming_like_distance(self, psi1: np.ndarray, psi2: np.ndarray) -> float:
        """
        Compute Hamming-like distance per Math36-AddB §2 Step 1.

        d^(k,k') = ||Psi^*,(k) - Psi^*,(k')||_2 / (1/2) * (||Psi^*,(k)||_2 + ||Psi^*,(k')||_2)

        This is a relative L2 distance (normalization-insensitive).

        Args:
            psi1, psi2: 1D condensate wavefunction arrays (flattened to N^3)

        Returns:
            Dimensionless distance in [0, 2]
        """
        diff_norm = np.linalg.norm(psi1 - psi2)
        avg_norm = 0.5 * (np.linalg.norm(psi1) + np.linalg.norm(psi2))

        if avg_norm < 1e-15:
            # Both near-zero: vacuum collapse
            return 0.0

        return diff_norm / avg_norm

    def pairwise_distances(self, psi_ensemble: List[np.ndarray]) -> np.ndarray:
        """
        Compute full K x K distance matrix for ensemble of K replicas.

        Args:
            psi_ensemble: List of K Psi^* arrays (each shape (N^3,) or (N, N, N))

        Returns:
            K x K symmetric distance matrix
        """
        K = len(psi_ensemble)
        D = np.zeros((K, K))

        for i in range(K):
            for j in range(i+1, K):
                psi1 = psi_ensemble[i].flatten()
                psi2 = psi_ensemble[j].flatten()
                d = self.hamming_like_distance(psi1, psi2)
                D[i, j] = d
                D[j, i] = d

        return D

    def single_linkage_clustering(self, D: np.ndarray, threshold: float) -> Tuple[List[List[int]], List[int]]:
        """
        Hierarchical agglomerative clustering with single linkage.

        Args:
            D: K x K distance matrix
            threshold: Merge clusters if min(d_i,j) < threshold

        Returns:
            (clusters, representatives)
            - clusters: List of lists of replica indices
            - representatives: One index per cluster (first replica in cluster)
        """
        K = D.shape[0]
        clusters = [[i] for i in range(K)]  # Start: each replica is its own cluster

        while True:
            # Find closest pair of clusters
            min_dist = np.inf
            merge_i, merge_j = -1, -1

            for i in range(len(clusters)):
                for j in range(i+1, len(clusters)):
                    # Single linkage: min distance between any two members
                    for idx_i in clusters[i]:
                        for idx_j in clusters[j]:
                            if D[idx_i, idx_j] < min_dist:
                                min_dist = D[idx_i, idx_j]
                                merge_i, merge_j = i, j

            if min_dist >= threshold:
                break

            # Merge clusters merge_i and merge_j
            clusters[merge_i].extend(clusters[merge_j])
            del clusters[merge_j]

        representatives = [cluster[0] for cluster in clusters]
        return clusters, representatives

    def classify_converged_replicas(self, psi_list: List[np.ndarray],
                                    convergence_flags: List[bool],
                                    mu2: float) -> Tuple[List[np.ndarray], List[int]]:
        """
        Filter out non-converged replicas per Math36-AddB §2 Step 0.

        Args:
            psi_list: Raw Psi arrays from all replicas
            convergence_flags: Boolean for each replica (converged or not)
            mu2: Control parameter (for logging)

        Returns:
            (converged_psi_list, original_indices_of_converged)
        """
        converged_psi = []
        converged_idx = []

        for idx, (psi, converged) in enumerate(zip(psi_list, convergence_flags)):
            if converged:
                converged_psi.append(psi)
                converged_idx.append(idx)

        if not converged_psi:
            logger.warning(f"μ²={mu2}: no converged replicas (NEWTON_FAILURE)")

        return converged_psi, converged_idx

    def cluster_per_mu2(self, mu2: float, psi_ensemble: List[np.ndarray],
                        convergence_flags: List[bool]) -> Dict:
        """
        Cluster all replicas for a single μ² value.

        Args:
            mu2: Control parameter
            psi_ensemble: List of K raw Psi arrays from all replicas
            convergence_flags: List of K boolean convergence indicators

        Returns:
            {
                'mu2': float,
                'n_replicas_total': int,
                'n_converged': int,
                'n_branches': int,
                'branches': [{'replica_indices': [...],
                             'representative_index': int,
                             'cluster_size': int}],
                'sensitivity_curve': {threshold: n_branches, ...}
            }
        """
        # Step 0: Filter converged replicas
        converged_psi, converged_idx = self.classify_converged_replicas(
            psi_ensemble, convergence_flags, mu2)

        if not converged_psi:
            return {
                'mu2': mu2,
                'n_replicas_total': len(psi_ensemble),
                'n_converged': 0,
                'status': 'NEWTON_FAILURE',
                'n_branches': 0,
                'branches': []
            }

        # Step 1: Compute pairwise distances
        D = self.pairwise_distances(converged_psi)

        # Main clustering at nominal threshold
        clusters, representatives = self.single_linkage_clustering(D, self.delta_hamming)

        # Sensitivity test: vary threshold
        sensitivity = {}
        for delta in np.linspace(0.05, 0.2, 16):
            _, reps = self.single_linkage_clustering(D, delta)
            sensitivity[float(delta)] = len(reps)

        # Build output structure
        branches = []
        for cluster, rep_idx_in_cluster in zip(clusters, representatives):
            # Map back to original replica indices
            original_indices = [converged_idx[i] for i in cluster]
            rep_original_idx = converged_idx[rep_idx_in_cluster]

            branches.append({
                'replica_indices': original_indices,
                'representative_index': rep_original_idx,
                'cluster_size': len(cluster)
            })

        return {
            'mu2': mu2,
            'n_replicas_total': len(psi_ensemble),
            'n_converged': len(converged_psi),
            'n_branches': len(clusters),
            'status': 'CLUSTERED',
            'branches': branches,
            'sensitivity_curve': sensitivity
        }

    def process_run_directory(self, run_dir: str) -> Dict:
        """
        Read Math82-I-proper output from run directory and cluster all μ² points.

        Expected directory structure:
            Runs/continuation/math82i_proper_mu2_<value>_r<replica>/
                MANIFEST.md (with output filenames and convergence status)
                psi_final_*.npy (converged wavefunction)

        Args:
            run_dir: Path to root Runs/continuation/ directory containing math82i_proper_* subdirs

        Returns:
            {
                'timestamp': ISO8601,
                'run_directory': str,
                'mu2_results': [cluster_result_per_mu2],
                'summary': {'n_mu2_values': ..., 'total_replicas': ..., ...}
            }
        """
        run_path = Path(run_dir)
        all_results = []

        # Find all math82i_proper_mu2_*_r*/ directories
        pattern = str(run_path / "math82i_proper_mu2_*_r*")
        run_subdirs = glob.glob(pattern)

        if not run_subdirs:
            logger.error(f"No math82i_proper_* directories found in {run_dir}")
            return None

        logger.info(f"Found {len(run_subdirs)} replica directories")

        # Group by μ² value
        mu2_groups = {}
        for subdir in run_subdirs:
            # Parse directory name: math82i_proper_mu2_<value>_r<replica>
            basename = os.path.basename(subdir)
            parts = basename.split('_')

            # Extract mu2 value (handle +/- signs and scientific notation)
            mu2_str = None
            for i, part in enumerate(parts):
                if part == 'mu2' and i+1 < len(parts):
                    # Concatenate until we find _r<digit>
                    mu2_parts = []
                    for j in range(i+1, len(parts)):
                        if parts[j].startswith('r') and parts[j][1:].isdigit():
                            break
                        mu2_parts.append(parts[j])
                    mu2_str = '_'.join(mu2_parts)
                    break

            try:
                mu2_val = float(mu2_str.replace('_', '').replace('m', '-'))
            except (ValueError, AttributeError):
                logger.warning(f"Could not parse μ² from {basename}, skipping")
                continue

            if mu2_val not in mu2_groups:
                mu2_groups[mu2_val] = []
            mu2_groups[mu2_val].append(subdir)

        logger.info(f"Grouped into {len(mu2_groups)} unique μ² values")

        # Process each μ² group
        for mu2_val in sorted(mu2_groups.keys()):
            subdirs = mu2_groups[mu2_val]
            psi_ensemble = []
            convergence_flags = []

            for subdir in subdirs:
                # Read MANIFEST.md for convergence status
                manifest_file = os.path.join(subdir, 'MANIFEST.md')
                converged = self._read_convergence_status(manifest_file)
                convergence_flags.append(converged)

                # Read psi_final_*.npy
                psi_file = self._find_psi_file(subdir)
                if psi_file is None:
                    logger.warning(f"No psi output found in {subdir}")
                    psi_ensemble.append(np.zeros(32768))  # Placeholder vacuum
                else:
                    psi = np.load(psi_file)
                    psi_ensemble.append(psi.flatten() if psi.ndim > 1 else psi)

            # Cluster this μ² group
            result = self.cluster_per_mu2(mu2_val, psi_ensemble, convergence_flags)
            all_results.append(result)

        # Compile summary
        summary = {
            'n_mu2_values': len(mu2_groups),
            'total_replicas': sum(len(v) for v in mu2_groups.values()),
            'total_converged': sum(r['n_converged'] for r in all_results),
            'total_branches_found': sum(r.get('n_branches', 0) for r in all_results if r.get('status') == 'CLUSTERED')
        }

        return {
            'timestamp': datetime.now().isoformat(),
            'run_directory': str(run_path),
            'mu2_results': all_results,
            'summary': summary,
            'clustering_threshold': self.delta_hamming
        }

    def _read_convergence_status(self, manifest_file: str) -> bool:
        """
        Extract convergence status from MANIFEST.md.

        Returns: True if Newton converged, False otherwise.
        """
        if not os.path.exists(manifest_file):
            return False

        try:
            with open(manifest_file, 'r') as f:
                content = f.read()
                # Look for 'converged: true' or 'CONVERGED'
                return 'converged: true' in content.lower() or 'CONVERGED' in content
        except Exception as e:
            logger.warning(f"Could not read {manifest_file}: {e}")
            return False

    def _find_psi_file(self, subdir: str) -> Optional[str]:
        """
        Locate psi_final_*.npy or equivalent output file.
        """
        patterns = [
            os.path.join(subdir, 'psi_final_*.npy'),
            os.path.join(subdir, 'psi_*.npy'),
            os.path.join(subdir, '*_psi.npy')
        ]

        for pattern in patterns:
            matches = glob.glob(pattern)
            if matches:
                return matches[0]

        return None


def main():
    """
    Command-line entry point for Math82_I_branch_clustering.py.

    Usage:
        python Math82_I_branch_clustering.py --run-dir Runs/continuation \
                                              --threshold 0.1 \
                                              --output Runs/audit/clustering_result.json
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Post-processor for Math82-I multi-replica cold-start clustering"
    )
    parser.add_argument('--run-dir', type=str, default='Runs/continuation',
                        help='Root directory containing math82i_proper_* subdirectories')
    parser.add_argument('--threshold', type=float, default=0.1,
                        help='Hamming-like distance threshold (Math36-AddB §2)')
    parser.add_argument('--output', type=str,
                        default=None,
                        help='Output JSON file (default: Runs/audit/math82i_branch_clustering_<date>.json)')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Initialize clusterer
    clusterer = BranchClusterer(delta_hamming=args.threshold)

    # Process run directory
    logger.info(f"Processing Math82-I-proper output from {args.run_dir}")
    result = clusterer.process_run_directory(args.run_dir)

    if result is None:
        logger.error("Clustering failed: no valid input found")
        return 1

    # Write output
    output_file = args.output
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'Runs/audit/math82i_branch_clustering_{timestamp}.json'

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Clustering complete. Output written to: {output_file}")

    # Print summary
    summary = result['summary']
    logger.info(f"Summary: {summary['n_mu2_values']} μ² values, "
                f"{summary['total_replicas']} total replicas, "
                f"{summary['total_converged']} converged, "
                f"{summary['total_branches_found']} branches found")

    return 0


if __name__ == '__main__':
    exit(main())
