#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v1.0
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
"""
projector_spectral.py — Stage U2, Module 2
===========================================
TECT spectral projector: construct P* from near-zero eigenmodes of L(G*).

Physical background
-------------------
At the ordering wavevector G* the linearised operator L(G*) has one (or more)
small eigenvalues corresponding to the condensate modes—modes that cost zero
(or near-zero) quadratic energy at the Brazovskii instability.  These modes
span the "condensate subspace" V*.

The spectral projector onto V* is

    P* = Σ_{j ∈ V*} |u_j⟩⟨u_j|

where {u_j} are the normalised eigenvectors of L(G*) for eigenvalues within
*tol* of the minimum eigenvalue.

This module also provides:
  - Carrier overlap diagnostics (ℓ_{∥A}, ℓ_{IA}, ℓ_{JA})
  - Existence certificate: ∃A : ℓ_{∥A} ≠ 0
  - Projector orthonormality verification

API
---
- condensate_projector(L, n_modes, tol) → ProjectorResult namedtuple
- condensate_projector_all(bloch_results, ...) → list of ProjectorResult
- carrier_overlaps(P_star, z_A, G_star, direction) → (ell_par, ell_I, ell_J)
- carrier_existence_certificate(overlap_results) → (exists, max_overlap)
- projector_report(results) → str (LaTeX table fragment)

Definitions
-----------
The condensate projector P* acts on the 3-component colour/family space.
z_A denotes the unit vector of a candidate carrier mode in that space.

Carrier overlaps (notation from TECT architecture document §U3):
    ℓ_{∥A} = |⟨u_∥ | P* | z_A⟩|   longitudinal carrier overlap
    ℓ_{IA} = |⟨u_I | P* | z_A⟩|   first transverse carrier overlap
    ℓ_{JA} = |⟨u_J | P* | z_A⟩|   second transverse carrier overlap

where u_∥ is the eigenvector of P*L(G*+δk)P* for motion along G*, and
u_I, u_J are the two transverse eigenvectors.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# scipy is optional (used for null_space only); fall back to numpy where possible
try:
    import scipy.linalg as _scipy_linalg
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


# ============================================================
# Result container
# ============================================================

@dataclass
class ProjectorResult:
    """
    Container for spectral projector output at a single G*.

    Attributes
    ----------
    patch_idx   : int
    G_star      : (3,) float   continuous ordering wavevector
    G_grid      : (3,) float   snapped grid wavevector
    eigenvalues : (3,) float   all eigenvalues of Hermitised L (ascending)
    eigenvectors: (3,3) complex128  columns = eigenvectors of Hermitised L
    n_modes     : int          number of modes included in V* (condensate subspace)
    mode_mask   : (3,) bool    which eigenvalues are in V*
    P_star      : (3,3) complex128  projector onto V*
    Q_star      : (3,3) complex128  complementary projector I − P*
    gap         : float        spectral gap: min(eig outside V*) − max(eig inside V*)
    L_sym       : (3,3) complex128  symmetrised input matrix (L+L†)/2
    is_hermitian: bool         whether |L − L†|/|L| < hermitian_tol
    herm_dev    : float        relative Hermitian deviation
    """
    patch_idx   : int
    G_star      : np.ndarray
    G_grid      : np.ndarray
    eigenvalues : np.ndarray
    eigenvectors: np.ndarray
    n_modes     : int
    mode_mask   : np.ndarray
    P_star      : np.ndarray
    Q_star      : np.ndarray
    gap         : float
    L_sym       : np.ndarray
    is_hermitian: bool
    herm_dev    : float


# ============================================================
# Core projector construction
# ============================================================

def condensate_projector(
    L: np.ndarray,
    *,
    n_modes: int = 1,
    tol: Optional[float] = None,
    tol_gap_fraction: float = 0.1,
    hermitian_tol: float = 1e-6,
    patch_idx: int = 0,
    G_star: Optional[np.ndarray] = None,
    G_grid: Optional[np.ndarray] = None,
) -> ProjectorResult:
    """
    Construct the spectral projector P* from the near-zero eigenmodes of L.

    The function symmetrises L before diagonalisation:
        L_sym = (L + L†) / 2

    Mode selection strategy:
    - If *tol* is given explicitly: include all modes with eigenvalue within
      *tol* of the smallest eigenvalue.
    - If *tol* is None: include the *n_modes* modes with smallest eigenvalue.
      Additionally warn if the spectral gap (min excluded eigenvalue minus
      max included eigenvalue) is smaller than *tol_gap_fraction* times the
      spread of all eigenvalues.

    Parameters
    ----------
    L               : (3,3) complex128   Bloch matrix at G*
    n_modes         : int                number of condensate modes (default 1)
    tol             : float or None      absolute eigenvalue tolerance for V*
    tol_gap_fraction: float              gap warning threshold (as fraction of spread)
    hermitian_tol   : float              threshold for Hermitian check
    patch_idx       : int                patch label (for reporting)
    G_star          : (3,) optional      continuous G* (metadata)
    G_grid          : (3,) optional      snapped G* (metadata)

    Returns
    -------
    ProjectorResult
    """
    L = np.asarray(L, dtype=np.complex128)
    if L.shape != (3, 3):
        raise ValueError(f"L must be 3×3; got {L.shape}")

    # Hermiticity check
    diff  = L - L.conj().T
    nrm_L = max(np.linalg.norm(L), 1e-14)
    hdev  = float(np.linalg.norm(diff)) / nrm_L
    is_herm = hdev < hermitian_tol
    if not is_herm:
        warnings.warn(
            f"Patch {patch_idx}: L is not Hermitian (relative deviation = {hdev:.3e}). "
            "This may indicate a non-converged Ψ₀ or numerical probe error.  "
            "Proceeding with (L+L†)/2."
        )

    L_sym = 0.5 * (L + L.conj().T)
    # numpy.linalg.eigh is sufficient for small (3×3) Hermitian matrices
    evals, evecs = np.linalg.eigh(L_sym)   # ascending order, columns = eigenvectors

    evals = np.real(evals).astype(float)       # should be real for Hermitian input

    # Mode selection
    if tol is not None:
        mode_mask = (evals - evals[0]) <= tol
    else:
        # Include exactly n_modes smallest eigenvalues
        mode_mask = np.zeros(3, dtype=bool)
        mode_mask[:n_modes] = True

    n_selected = int(np.sum(mode_mask))

    # Spectral gap
    evals_in  = evals[mode_mask]
    evals_out = evals[~mode_mask]
    if len(evals_out) > 0 and len(evals_in) > 0:
        gap = float(evals_out.min() - evals_in.max())
    else:
        gap = 0.0

    spread = float(evals[-1] - evals[0]) if evals[-1] > evals[0] else 1.0
    if gap < tol_gap_fraction * spread and len(evals_out) > 0:
        warnings.warn(
            f"Patch {patch_idx}: spectral gap = {gap:.3e} is less than "
            f"{tol_gap_fraction*100:.0f}%% of eigenvalue spread ({spread:.3e}).  "
            "Mode selection may be ambiguous.  Consider increasing n_modes or "
            "using tol-based selection."
        )

    # Build P* = Σ_j |u_j><u_j|
    U_star = evecs[:, mode_mask]               # (3, n_selected)
    P_star = U_star @ U_star.conj().T          # (3, 3)
    Q_star = np.eye(3, dtype=np.complex128) - P_star

    return ProjectorResult(
        patch_idx    = patch_idx,
        G_star       = np.asarray(G_star if G_star is not None else np.zeros(3)),
        G_grid       = np.asarray(G_grid if G_grid is not None else np.zeros(3)),
        eigenvalues  = evals,
        eigenvectors = evecs,
        n_modes      = n_selected,
        mode_mask    = mode_mask,
        P_star       = P_star,
        Q_star       = Q_star,
        gap          = gap,
        L_sym        = L_sym,
        is_hermitian = is_herm,
        herm_dev     = hdev,
    )


def condensate_projector_all(
    bloch_results: List[Dict],
    *,
    n_modes: int = 1,
    tol: Optional[float] = None,
    tol_gap_fraction: float = 0.1,
    hermitian_tol: float = 1e-6,
    verbose: bool = False,
) -> List[ProjectorResult]:
    """
    Apply condensate_projector() to every patch in the output of
    bloch_matrices_all_patches().

    Parameters
    ----------
    bloch_results : list of dicts from bloch_linearization.bloch_matrices_all_patches()
    n_modes, tol, tol_gap_fraction, hermitian_tol : forwarded to condensate_projector()
    verbose       : print per-patch summary

    Returns
    -------
    list of ProjectorResult (one per patch)
    """
    proj_results = []
    for entry in bloch_results:
        pr = condensate_projector(
            entry["L"],
            n_modes          = n_modes,
            tol              = tol,
            tol_gap_fraction = tol_gap_fraction,
            hermitian_tol    = hermitian_tol,
            patch_idx        = entry["patch_idx"],
            G_star           = entry.get("G_star"),
            G_grid           = entry.get("G_grid"),
        )
        proj_results.append(pr)
        if verbose:
            print(
                f"  Patch {pr.patch_idx}: "
                f"eig={pr.eigenvalues}  n_modes={pr.n_modes}  "
                f"gap={pr.gap:.4e}  herm_dev={pr.herm_dev:.2e}"
            )
    return proj_results


# ============================================================
# Orthonormality and positivity verification
# ============================================================

def verify_projector(pr: ProjectorResult, tol: float = 1e-10) -> Dict[str, Any]:
    """
    Run basic algebraic sanity checks on P*.

    Checks
    ------
    1. Idempotency:   ||P*² − P*||_F < tol
    2. Hermiticity:   ||P* − P*†||_F < tol
    3. Positivity:    all eigenvalues of P* ≥ −tol
    4. Rank:          tr(P*) ≈ n_modes
    5. Orthogonality: P*·Q* = 0 (up to tol)

    Returns
    -------
    dict with keys: 'idempotent', 'hermitian', 'positive', 'rank_ok',
                    'orthogonal', 'all_pass', and numerical deviations.
    """
    P = pr.P_star
    Q = pr.Q_star

    idem_dev   = float(np.linalg.norm(P @ P - P))
    herm_dev   = float(np.linalg.norm(P - P.conj().T))
    evals_P    = np.real(np.linalg.eigvalsh(P))
    pos_ok     = bool(evals_P.min() >= -tol)
    rank_dev   = abs(float(np.real(np.trace(P))) - pr.n_modes)
    orth_dev   = float(np.linalg.norm(P @ Q))

    all_pass = (
        idem_dev < tol and
        herm_dev < tol and
        pos_ok and
        rank_dev < tol and
        orth_dev < tol
    )

    return {
        "idempotent"   : idem_dev < tol,
        "hermitian"    : herm_dev < tol,
        "positive"     : pos_ok,
        "rank_ok"      : rank_dev < tol,
        "orthogonal"   : orth_dev < tol,
        "all_pass"     : all_pass,
        "idem_dev"     : idem_dev,
        "herm_dev"     : herm_dev,
        "min_eval_P"   : float(evals_P.min()),
        "rank_dev"     : rank_dev,
        "orth_dev"     : orth_dev,
    }


# ============================================================
# Carrier overlaps (Stage U3 preparation)
# ============================================================

def carrier_overlaps(
    pr: ProjectorResult,
    z_A: np.ndarray,
    *,
    u_par: Optional[np.ndarray] = None,
    u_I: Optional[np.ndarray] = None,
    u_J: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """
    Compute carrier overlaps ℓ_{∥A}, ℓ_{IA}, ℓ_{JA} for a candidate
    carrier mode z_A in the 3-component colour/family space.

    Parameters
    ----------
    pr    : ProjectorResult at G*
    z_A   : (3,) complex   candidate carrier unit vector
    u_par : (3,) complex   longitudinal eigenvector (default: first mode of P*)
    u_I   : (3,) complex   first transverse (default: from P* eigenvectors)
    u_J   : (3,) complex   second transverse (default: from P* eigenvectors)

    Returns
    -------
    dict with keys: 'ell_par', 'ell_I', 'ell_J', 'total_overlap'

    Notes
    -----
    The "transport eigenvectors" u_∥, u_I, u_J are determined by the
    projected velocity matrix M_∥ = P*K_∥P*.  Until transport_extractor.py
    has been run, the user may pass the eigenvectors of P* itself as proxies.
    """
    z_A = np.asarray(z_A, dtype=np.complex128).ravel()
    nrm = np.linalg.norm(z_A)
    if nrm < 1e-14:
        raise ValueError("Carrier vector z_A is zero.")
    z_A = z_A / nrm

    P = pr.P_star

    # Default transport eigenvectors: use P* eigenvectors
    # (overridden once M_i is computed in transport_extractor)
    if u_par is None:
        idx_modes = np.where(pr.mode_mask)[0]
        u_par = pr.eigenvectors[:, idx_modes[0]]
    if u_I is None:
        idx_modes = np.where(pr.mode_mask)[0]
        u_I = pr.eigenvectors[:, idx_modes[min(1, len(idx_modes) - 1)]]
    if u_J is None:
        # Use orthogonal complement via SVD (scipy.null_space fallback)
        if _HAS_SCIPY:
            ns = _scipy_linalg.null_space(pr.P_star)
        else:
            # Manual null space via SVD for 3×3
            U, S, Vt = np.linalg.svd(pr.P_star)
            null_mask = S < 1e-10
            ns = Vt[null_mask].T.conj()
        if ns.ndim == 2 and ns.shape[1] > 0:
            u_J = ns[:, 0]
        else:
            u_J = np.zeros(3, dtype=np.complex128)

    Pz  = P @ z_A
    ell_par = float(abs(np.dot(np.conj(u_par), Pz)))
    ell_I   = float(abs(np.dot(np.conj(np.asarray(u_I, dtype=np.complex128)), Pz)))
    ell_J   = float(abs(np.dot(np.conj(np.asarray(u_J, dtype=np.complex128)), Pz)))

    total = float(np.linalg.norm(Pz))

    return {
        "ell_par"       : ell_par,
        "ell_I"         : ell_I,
        "ell_J"         : ell_J,
        "total_overlap" : total,
    }


def carrier_existence_certificate(
    overlap_list: List[Dict[str, float]],
    threshold: float = 0.1,
) -> Dict[str, Any]:
    """
    Stage U3 existence certificate: ∃A such that ℓ_{∥A} > threshold.

    Parameters
    ----------
    overlap_list : list of dicts from carrier_overlaps() over multiple A
    threshold    : float   minimum overlap to certify existence

    Returns
    -------
    dict with keys:
        'exists'       : bool   ∃A with ℓ_{∥A} > threshold
        'max_ell_par'  : float  maximum ℓ_{∥A} over all A
        'best_A_idx'   : int    index of best carrier
        'all_ell_par'  : list   ℓ_{∥A} for all A
    """
    ells = [d["ell_par"] for d in overlap_list]
    best = int(np.argmax(ells))
    return {
        "exists"      : ells[best] > threshold,
        "max_ell_par" : float(ells[best]),
        "best_A_idx"  : best,
        "all_ell_par" : ells,
    }


# ============================================================
# Reporting
# ============================================================

def projector_summary_table(
    proj_results: List[ProjectorResult],
    *,
    label: str = "",
) -> str:
    """
    Generate a LaTeX fragment summarising the spectral projector results
    across all patches.

    Returns a string with \\begin{tabular}...\\end{tabular}.
    """
    lines = [
        r"\begin{tabular}{cccccc}",
        r"\hline",
        r"Patch & $|\mathbf{G}^*|$ & $\lambda_{\min}$ "
        r"& $\lambda_2$ & Gap & $\delta_{\rm herm}$ \\",
        r"\hline",
    ]
    for pr in proj_results:
        kmag = float(np.linalg.norm(pr.G_grid))
        e0   = float(pr.eigenvalues[0])
        e1   = float(pr.eigenvalues[1])
        lines.append(
            f"  {pr.patch_idx} & {kmag:.4f} & {e0:.4e} "
            f"& {e1:.4e} & {pr.gap:.4e} & {pr.herm_dev:.2e} \\\\"
        )
    lines += [r"\hline", r"\end{tabular}"]
    if label:
        lines.insert(0, f"% {label}")
    return "\n".join(lines)


def projector_text_report(proj_results: List[ProjectorResult]) -> str:
    """Plain-text summary for terminal output."""
    rows = [
        f"{'Patch':>5}  {'|G_grid|':>9}  {'λ_min':>12}  {'λ_2':>12}  "
        f"{'gap':>12}  {'n*':>4}  {'herm_dev':>10}"
    ]
    rows.append("-" * 75)
    for pr in proj_results:
        kmag = float(np.linalg.norm(pr.G_grid))
        rows.append(
            f"{pr.patch_idx:>5}  {kmag:>9.4f}  {pr.eigenvalues[0]:>12.4e}  "
            f"{pr.eigenvalues[1]:>12.4e}  {pr.gap:>12.4e}  "
            f"{pr.n_modes:>4}  {pr.herm_dev:>10.2e}"
        )
    return "\n".join(rows)
