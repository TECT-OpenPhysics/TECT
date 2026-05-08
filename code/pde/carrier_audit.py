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
carrier_audit.py — Stage U3
============================
TECT carrier existence certificate:  ∃A : ℓ_{∥A} > η_threshold.

Physical background
-------------------
In TECT the condensate Ψ₀ couples to elementary excitations ("carriers")
through the projected velocity operator M_∥ = P*K_∥P*.  A carrier mode
z_A (a unit vector in the 3-component colour/family space) is said to be
*longitudinally active* if

    ℓ_{∥A} := |⟨u_∥ | P* | z_A⟩|  >  0

where u_∥ is the dominant eigenvector of M_∥|_{V*} (the longitudinal
transport eigenvector from Stage U2b).

The existence certificate asserts:

    ∃A ∈ {z₁, …, z_N} :  ℓ_{∥A} > η_carrier

This is the necessary condition for gauge-boson mass generation via the
condensate: a carrier must overlap non-trivially with the condensate's
longitudinal transport mode.

Three overlaps are reported per carrier:

    ℓ_{∥A}  = |⟨u_∥ | P* | z_A⟩|          longitudinal
    ℓ_{1A}  = |⟨u_1 | P* | z_A⟩|           first transverse
    ℓ_{2A}  = |⟨u_2 | P* | z_A⟩|           second transverse

where u_∥, u_1, u_2 are computed from DiracCoeffResult (Stage U2b).

API
---
- standard_carrier_basis(n_extra)  → (N, 3) complex128 candidate array
- carrier_overlaps_patch(pr, dr, carriers) → CarrierOverlaps namedtuple
- carrier_audit_patch(pr, dr, carriers, threshold) → CarrierAuditResult
- carrier_audit_all_patches(proj_results, dirac_results, carriers, threshold)
      → List[CarrierAuditResult]
- existence_certificate(audit_results, threshold) → CertificateResult
- carrier_audit_text_report(audit_results) → str
- carrier_audit_latex_table(audit_results) → str

Usage
-----
    from projector_spectral import condensate_projector_all
    from transport_extractor import (
        stiffness_tensor_full, dirac_coefficients_all_patches
    )
    from carrier_audit import (
        standard_carrier_basis, carrier_audit_all_patches,
        existence_certificate, carrier_audit_text_report,
    )

    carriers = standard_carrier_basis()       # (12, 3) default set
    audit    = carrier_audit_all_patches(proj_res, dirac_res, carriers)
    cert     = existence_certificate(audit, threshold=0.1)
    print("Certificate:", cert.exists, "  max ℓ_∥ =", cert.max_ell_par)
    print(carrier_audit_text_report(audit))
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


# ============================================================
# Standard carrier basis
# ============================================================

def standard_carrier_basis(n_extra: int = 0) -> np.ndarray:
    """
    Return a default set of candidate carrier vectors in the 3-component space.

    The default 12-element basis covers:
      - 3 Cartesian unit vectors  {e₀, e₁, e₂}
      - 3 face-diagonal vectors   {(e₀+e₁)/√2, (e₀+e₂)/√2, (e₁+e₂)/√2}
      - 3 anti-diagonal vectors   {(e₀−e₁)/√2, (e₀−e₂)/√2, (e₁−e₂)/√2}
      - 1 body-diagonal vector    {(e₀+e₁+e₂)/√3}
      - 2 complex off-diagonal    {(e₀+ie₁)/√2, (e₀+ie₂)/√2}

    Parameters
    ----------
    n_extra : int   extra random unit vectors to append (default 0)

    Returns
    -------
    carriers : (N, 3) complex128 ndarray  (N = 12 + n_extra)
    """
    basis = []

    # Cartesian
    for j in range(3):
        v = np.zeros(3, dtype=np.complex128)
        v[j] = 1.0
        basis.append(v)

    # Real face-diagonals
    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        v = np.zeros(3, dtype=np.complex128)
        v[i] = v[j] = 1.0 / np.sqrt(2.0)
        basis.append(v)

    # Real anti-diagonals
    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        v = np.zeros(3, dtype=np.complex128)
        v[i] =  1.0 / np.sqrt(2.0)
        v[j] = -1.0 / np.sqrt(2.0)
        basis.append(v)

    # Real body-diagonal
    v = np.ones(3, dtype=np.complex128) / np.sqrt(3.0)
    basis.append(v)

    # Complex off-diagonals (gauge-like)
    for (i, j) in [(0, 1), (0, 2)]:
        v = np.zeros(3, dtype=np.complex128)
        v[i] = 1.0 / np.sqrt(2.0)
        v[j] = 1j  / np.sqrt(2.0)
        basis.append(v)

    carriers = np.array(basis, dtype=np.complex128)  # (12, 3)

    if n_extra > 0:
        rng   = np.random.default_rng(0)
        extra = rng.standard_normal((n_extra, 3)) + 1j * rng.standard_normal((n_extra, 3))
        norms = np.linalg.norm(extra, axis=1, keepdims=True)
        extra /= np.maximum(norms, 1e-14)
        carriers = np.vstack([carriers, extra.astype(np.complex128)])

    return carriers


# ============================================================
# Result containers
# ============================================================

@dataclass
class CarrierOverlaps:
    """
    Raw overlap values for one carrier z_A at one G*.

    Attributes
    ----------
    carrier_idx   : int
    z_A           : (3,) complex   candidate carrier unit vector
    Pz_A          : (3,) complex   P* z_A (condensate-projected carrier)
    ell_par       : float   |⟨u_∥ | P* | z_A⟩|
    ell_1         : float   |⟨u_1 | P* | z_A⟩|
    ell_2         : float   |⟨u_2 | P* | z_A⟩|
    total_overlap : float   ||P* z_A||   (total condensate overlap)
    """
    carrier_idx   : int
    z_A           : np.ndarray
    Pz_A          : np.ndarray
    ell_par       : float
    ell_1         : float
    ell_2         : float
    total_overlap : float


@dataclass
class CarrierAuditResult:
    """
    Full carrier audit output for a single G*.

    Attributes
    ----------
    patch_idx         : int
    G_unit            : (3,) float   ĝ
    n_carriers        : int
    overlaps          : list of CarrierOverlaps
    max_ell_par       : float    max over all carriers of ℓ_{∥A}
    best_carrier_idx  : int      index of best carrier for ℓ_{∥}
    threshold         : float    η_longitudinal
    certificate       : bool     max_ell_par > threshold  (longitudinal cert)
    u_par             : (3,)     longitudinal transport eigenvector
    u_1               : (3,)     first transverse transport eigenvector
    u_2               : (3,)     second transverse transport eigenvector
    max_ell_IJ        : float    max over carriers of max(ℓ_I, ℓ_J)   [transverse]
    best_carrier_IJ   : int      carrier achieving max_ell_IJ
    eta_transverse    : float    threshold for transverse certificate
    transverse_cert   : bool     max_ell_IJ > eta_transverse
    """
    patch_idx         : int
    G_unit            : np.ndarray
    n_carriers        : int
    overlaps          : List[CarrierOverlaps]
    max_ell_par       : float
    best_carrier_idx  : int
    threshold         : float
    certificate       : bool
    u_par             : np.ndarray
    u_1               : np.ndarray
    u_2               : np.ndarray
    max_ell_IJ        : float = 0.0
    best_carrier_IJ   : int   = -1
    eta_transverse    : float = 0.05
    transverse_cert   : bool  = False


@dataclass
class CertificateResult:
    """
    Global existence certificate for BOTH longitudinal and transverse conditions
    (TECT-Math18, §Full audit criterion):

        ∃A : ℓ_{∥A} > η_longitudinal     (longitudinal primitive seed)
        ∃B : max(ℓ_{IB}, ℓ_{JB}) > η_transverse  (transverse seed)

    Attributes
    ----------
    exists            : bool   ∃A: ℓ_{∥A} > η_longitudinal (longitudinal)
    max_ell_par       : float  global maximum ℓ_{∥A}
    best_patch_idx    : int    patch achieving max_ell_par
    best_carrier_idx  : int    carrier achieving max_ell_par
    threshold         : float  η_longitudinal
    per_patch         : list   max_ell_par per patch
    all_ell_par       : (Npatch, Ncarriers) float
    transverse_exists : bool   ∃B: max(ℓ_{IB}, ℓ_{JB}) > η_transverse
    max_ell_IJ        : float  global max of max(ℓ_I, ℓ_J)
    best_patch_IJ     : int    patch achieving max_ell_IJ
    best_carrier_IJ   : int    carrier achieving max_ell_IJ
    eta_transverse    : float  η_transverse threshold
    all_ell_1         : (Npatch, Ncarriers) float   ℓ_IB matrix
    all_ell_2         : (Npatch, Ncarriers) float   ℓ_JB matrix
    full_certificate  : bool   BOTH longitudinal and transverse pass
    """
    exists            : bool
    max_ell_par       : float
    best_patch_idx    : int
    best_carrier_idx  : int
    threshold         : float
    per_patch         : List[float]
    all_ell_par       : np.ndarray
    # --- transverse certificate (Module 11 upgrade, TECT-Math18) ---
    transverse_exists : bool  = False
    max_ell_IJ        : float = 0.0
    best_patch_IJ     : int   = -1
    best_carrier_IJ   : int   = -1
    eta_transverse    : float = 0.05
    all_ell_1         : np.ndarray = field(default_factory=lambda: np.zeros((1,1)))
    all_ell_2         : np.ndarray = field(default_factory=lambda: np.zeros((1,1)))
    full_certificate  : bool  = False


# ============================================================
# Core computation
# ============================================================

def _transport_frame_vectors(dr: Any) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extract (u_par, u_1, u_2) from a DiracCoeffResult.

    u_par is the dominant longitudinal condensate eigenvector.
    u_1, u_2 are two unit vectors spanning the complement of u_par within V*
    (or from e1, e2 if n_modes=1).
    """
    u_par = np.asarray(dr.u_par, dtype=np.complex128)
    u_par = u_par / max(np.linalg.norm(u_par), 1e-14)

    # Build u_1 orthogonal to u_par in ℂ³
    # Use e1 as hint: project out u_par component
    e1 = np.asarray(dr.e1, dtype=np.complex128)
    proj = np.dot(np.conj(u_par), e1) * u_par
    u_1_raw = e1 - proj
    nrm = np.linalg.norm(u_1_raw)
    if nrm < 1e-10:
        # e1 is parallel to u_par — use e2 instead
        e2 = np.asarray(dr.e2, dtype=np.complex128)
        proj2 = np.dot(np.conj(u_par), e2) * u_par
        u_1_raw = e2 - proj2
        nrm = np.linalg.norm(u_1_raw)
    u_1 = u_1_raw / max(nrm, 1e-14)

    # u_2 orthogonal to both u_par and u_1
    u_2_raw = np.cross(np.conj(u_par), np.conj(u_1))
    nrm2 = np.linalg.norm(u_2_raw)
    if nrm2 < 1e-10:
        u_2 = np.zeros(3, dtype=np.complex128)
        u_2[2] = 1.0
    else:
        u_2 = u_2_raw.astype(np.complex128) / nrm2

    return u_par, u_1, u_2


def carrier_overlaps_patch(
    pr: Any,
    dr: Any,
    carriers: np.ndarray,
) -> List[CarrierOverlaps]:
    """
    Compute (ℓ_{∥A}, ℓ_{1A}, ℓ_{2A}) for every candidate carrier z_A.

    Parameters
    ----------
    pr       : ProjectorResult   (contains P_star)
    dr       : DiracCoeffResult  (contains u_par)
    carriers : (N_A, 3) complex  candidate carrier vectors

    Returns
    -------
    list of CarrierOverlaps, one per carrier
    """
    P      = np.asarray(pr.P_star, dtype=np.complex128)
    u_par, u_1, u_2 = _transport_frame_vectors(dr)

    results = []
    for A, z_raw in enumerate(carriers):
        z_A = np.asarray(z_raw, dtype=np.complex128).ravel()
        nrm = np.linalg.norm(z_A)
        if nrm < 1e-14:
            warnings.warn(f"Carrier {A} is zero vector; skipping.")
            continue
        z_A = z_A / nrm

        Pz  = P @ z_A

        ell_par = float(abs(np.dot(np.conj(u_par), Pz)))
        ell_1   = float(abs(np.dot(np.conj(u_1),   Pz)))
        ell_2   = float(abs(np.dot(np.conj(u_2),   Pz)))
        total   = float(np.linalg.norm(Pz))

        results.append(CarrierOverlaps(
            carrier_idx   = A,
            z_A           = z_A,
            Pz_A          = Pz,
            ell_par       = ell_par,
            ell_1         = ell_1,
            ell_2         = ell_2,
            total_overlap = total,
        ))

    return results


def carrier_audit_patch(
    pr: Any,
    dr: Any,
    carriers: np.ndarray,
    threshold: float = 0.1,
    eta_transverse: float = None,
) -> CarrierAuditResult:
    """
    Run the full carrier audit for a single G*.

    Parameters
    ----------
    pr              : ProjectorResult
    dr              : DiracCoeffResult
    carriers        : (N_A, 3) complex   candidate carrier vectors
    threshold       : float              η_∥ for longitudinal certificate
    eta_transverse  : float or None      η_T for transverse certificate
                      (default None → use separate default 0.05, NOT threshold)

    Returns
    -------
    CarrierAuditResult
    """
    if eta_transverse is None:
        eta_transverse = 0.05   # TECT default: η_T ≠ η_∥ in general

    overlaps = carrier_overlaps_patch(pr, dr, carriers)

    ells_par = [ov.ell_par for ov in overlaps]
    if not ells_par:
        raise RuntimeError("No valid carriers found (all zero?).")

    best_idx     = int(np.argmax(ells_par))
    max_ell_par  = float(ells_par[best_idx])

    # Transverse overlaps: max(ℓ_I, ℓ_J) per carrier
    ells_IJ   = [max(ov.ell_1, ov.ell_2) for ov in overlaps]
    best_IJ   = int(np.argmax(ells_IJ))
    max_IJ    = float(ells_IJ[best_IJ])

    u_par, u_1, u_2 = _transport_frame_vectors(dr)

    return CarrierAuditResult(
        patch_idx        = pr.patch_idx,
        G_unit           = np.asarray(dr.G_unit, dtype=float),
        n_carriers       = len(overlaps),
        overlaps         = overlaps,
        max_ell_par      = max_ell_par,
        best_carrier_idx = best_idx,
        threshold        = threshold,
        certificate      = max_ell_par > threshold,
        u_par            = u_par,
        u_1              = u_1,
        u_2              = u_2,
        max_ell_IJ       = max_IJ,
        best_carrier_IJ  = best_IJ,
        eta_transverse   = eta_transverse,
        transverse_cert  = max_IJ > eta_transverse,
    )


def carrier_audit_all_patches(
    proj_results:  List[Any],
    dirac_results: List[Any],
    carriers:      np.ndarray,
    threshold:     float = 0.1,
    eta_transverse: float = None,
    *,
    verbose: bool = False,
) -> List[CarrierAuditResult]:
    """
    Run carrier_audit_patch() for every patch.

    Parameters
    ----------
    proj_results   : list of ProjectorResult
    dirac_results  : list of DiracCoeffResult
    carriers       : (N_A, 3) complex
    threshold      : float       η_∥ for longitudinal
    eta_transverse : float       η_T for transverse (default None → 0.05)
    verbose        : bool

    Returns
    -------
    list of CarrierAuditResult
    """
    if len(proj_results) != len(dirac_results):
        raise ValueError("proj_results and dirac_results must have equal length")

    if verbose:
        eta_t_display = eta_transverse if eta_transverse is not None else 0.05
        print(f"\n[Stage U3] Carrier audit — {len(carriers)} candidates, "
              f"η_∥ = {threshold}, η_T = {eta_t_display}")

    results = []
    for pr, dr in zip(proj_results, dirac_results):
        ar = carrier_audit_patch(pr, dr, carriers, threshold,
                                 eta_transverse=eta_transverse)
        results.append(ar)
        if verbose:
            stat = "PASS" if ar.certificate else "FAIL"
            print(f"  Patch {ar.patch_idx} [{stat}]: "
                  f"max ℓ_∥ = {ar.max_ell_par:.4f}  "
                  f"(carrier {ar.best_carrier_idx})")

    return results


# ============================================================
# Global existence certificate
# ============================================================

def existence_certificate(
    audit_results:  List[CarrierAuditResult],
    threshold:      float = 0.1,
    eta_transverse: float = 0.05,
) -> CertificateResult:
    """
    Aggregate patch-level audits into global certificate for BOTH conditions
    (TECT-Math18, §Full audit criterion, eq. (5.5)):

        ∃A : ℓ_{∥A} > η_longitudinal     (longitudinal primitive seed)
        ∃B : max(ℓ_{IB}, ℓ_{JB}) > η_transverse  (transverse seed)

    Parameters
    ----------
    audit_results  : list of CarrierAuditResult
    threshold      : float   η_longitudinal  (default 0.1)
    eta_transverse : float   η_transverse    (default 0.05; usually smaller)

    Returns
    -------
    CertificateResult  (includes both longitudinal and transverse certificates)
    """
    if not audit_results:
        raise ValueError("audit_results is empty.")

    n_patches  = len(audit_results)
    n_carriers = audit_results[0].n_carriers

    # Build (Npatch, Ncarrier) matrices for all three overlap channels
    all_ell_par = np.zeros((n_patches, n_carriers), dtype=float)
    all_ell_1   = np.zeros((n_patches, n_carriers), dtype=float)
    all_ell_2   = np.zeros((n_patches, n_carriers), dtype=float)
    per_patch   = []

    for pi, ar in enumerate(audit_results):
        for ov in ar.overlaps:
            a = ov.carrier_idx
            all_ell_par[pi, a] = ov.ell_par
            all_ell_1[pi, a]   = ov.ell_1
            all_ell_2[pi, a]   = ov.ell_2
        per_patch.append(ar.max_ell_par)

    # --- Longitudinal certificate ---
    global_max    = float(all_ell_par.max())
    best_flat     = int(all_ell_par.argmax())
    best_patch    = int(best_flat // n_carriers)
    best_carrier  = int(best_flat %  n_carriers)

    # --- Transverse certificate ---
    # Criterion: ∃B: max(ℓ_IB, ℓ_JB) > η_transverse
    all_ell_IJ    = np.maximum(all_ell_1, all_ell_2)   # (Npatch, Ncarrier)
    IJ_max        = float(all_ell_IJ.max())
    best_flat_IJ  = int(all_ell_IJ.argmax())
    best_patch_IJ = int(best_flat_IJ // n_carriers)
    best_carr_IJ  = int(best_flat_IJ %  n_carriers)
    transverse_ok = IJ_max > eta_transverse

    full_cert = (global_max > threshold) and transverse_ok

    return CertificateResult(
        exists            = global_max > threshold,
        max_ell_par       = global_max,
        best_patch_idx    = best_patch,
        best_carrier_idx  = best_carrier,
        threshold         = threshold,
        per_patch         = per_patch,
        all_ell_par       = all_ell_par,
        transverse_exists = transverse_ok,
        max_ell_IJ        = IJ_max,
        best_patch_IJ     = best_patch_IJ,
        best_carrier_IJ   = best_carr_IJ,
        eta_transverse    = eta_transverse,
        all_ell_1         = all_ell_1,
        all_ell_2         = all_ell_2,
        full_certificate  = full_cert,
    )


# ============================================================
# Reporting
# ============================================================

def carrier_audit_text_report(
    audit_results: List[CarrierAuditResult],
    top_n: int = 3,
) -> str:
    """
    Plain-text summary: top-*top_n* carriers per patch by ℓ_{∥A}.
    """
    rows = []
    for ar in audit_results:
        rows.append(
            f"Patch {ar.patch_idx}  |G_unit|=({ar.G_unit[0]:.3f},{ar.G_unit[1]:.3f},{ar.G_unit[2]:.3f})  "
            f"certificate={'PASS' if ar.certificate else 'FAIL'}  η={ar.threshold}"
        )
        rows.append(f"  {'A':>4}  {'ℓ_∥':>10}  {'ℓ_1':>10}  {'ℓ_2':>10}  {'total':>10}")
        rows.append("  " + "-" * 46)
        sorted_ovs = sorted(ar.overlaps, key=lambda x: x.ell_par, reverse=True)
        for ov in sorted_ovs[:top_n]:
            rows.append(
                f"  {ov.carrier_idx:>4}  {ov.ell_par:>10.4f}  "
                f"{ov.ell_1:>10.4f}  {ov.ell_2:>10.4f}  "
                f"{ov.total_overlap:>10.4f}"
            )
    return "\n".join(rows)


def carrier_audit_latex_table(
    audit_results: List[CarrierAuditResult],
    *,
    label:   str = "tab:carrier_audit",
    caption: str = "TECT Stage U3: carrier overlap audit results.",
    top_n:   int = 3,
) -> str:
    """LaTeX table of the top-*top_n* carriers per patch."""
    lines = [
        r"\begin{table}[h]",
        r"\centering",
        r"\caption{" + caption + r"}",
        r"\label{" + label + r"}",
        r"\begin{tabular}{cccccc}",
        r"\hline\hline",
        r"Patch & Carrier $A$ & $\ell_{\parallel A}$ "
        r"& $\ell_{1A}$ & $\ell_{2A}$ & Certificate \\",
        r"\hline",
    ]
    for ar in audit_results:
        sorted_ovs = sorted(ar.overlaps, key=lambda x: x.ell_par, reverse=True)
        cert_str = r"\checkmark" if ar.certificate else r"$\times$"
        for rank, ov in enumerate(sorted_ovs[:top_n]):
            patch_col = str(ar.patch_idx) if rank == 0 else ""
            cert_col  = cert_str if rank == 0 else ""
            lines.append(
                f"  {patch_col} & {ov.carrier_idx} "
                f"& {ov.ell_par:.4f} & {ov.ell_1:.4f} & {ov.ell_2:.4f} "
                f"& {cert_col} \\\\"
            )
        if len(sorted_ovs) > top_n:
            lines.append(r"  \multicolumn{6}{c}{\ldots} \\")
        lines.append(r"  \hline")

    lines += [r"\hline", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines)


def certificate_summary_latex(cert: CertificateResult) -> str:
    """
    Two-line LaTeX carrier existence certificate statement.

    Reports both conditions of TECT-Math18 §Full audit criterion:
        (1) ∃A: ℓ_{∥A} > η_longitudinal
        (2) ∃B: max(ℓ_IB, ℓ_JB) > η_transverse
    """
    long_sym  = r"\checkmark" if cert.exists else r"$\times$"
    tran_sym  = r"\checkmark" if cert.transverse_exists else r"$\times$"
    full_sym  = r"\checkmark" if cert.full_certificate  else r"$\times$"

    long_line = (
        rf"\noindent\textbf{{Carrier cert. (longitudinal)}}: "
        rf"{long_sym}\ "
        rf"$\exists A:\,\ell_{{\parallel A}} = {cert.max_ell_par:.4f} > \eta_{{\parallel}} = {cert.threshold}$"
        rf"\ (patch {cert.best_patch_idx}, carrier {cert.best_carrier_idx})."
    )
    tran_line = (
        rf"\noindent\textbf{{Carrier cert. (transverse)}}: "
        rf"{tran_sym}\ "
        rf"$\exists B:\,\max(\ell_{{IB}},\ell_{{JB}}) = {cert.max_ell_IJ:.4f} > \eta_{{T}} = {cert.eta_transverse}$"
        rf"\ (patch {cert.best_patch_IJ}, carrier {cert.best_carrier_IJ})."
    )
    full_line = (
        rf"\noindent\textbf{{Full carrier certificate}}: "
        rf"{full_sym}\ "
        rf"$[\exists A:\ell_{{\parallel A}}\neq 0]\ \wedge\ [\exists B:(\ell_{{IB}},\ell_{{JB}})\neq(0,0)]$."
    )
    return "\n".join([long_line, tran_line, full_line])


def full_certificate_latex_block(cert: CertificateResult) -> str:
    """
    Full LaTeX align block reporting the Gate 2-3 carrier acceptance criterion.

    Follows TECT-Math18 notation:
        ∃A: ℓ_{∥A} ≠ 0   (Gate 2: longitudinal primitive seed)
        ∃B: (ℓ_{IB}, ℓ_{JB}) ≠ (0,0)  (Gate 3: transverse seed)
    """
    long_cert  = r"\checkmark" if cert.exists           else r"\times"
    tran_cert  = r"\checkmark" if cert.transverse_exists else r"\times"
    full_cert  = r"\checkmark" if cert.full_certificate  else r"\times"

    return (
        r"\begin{align}" + "\n"
        rf"  &\text{{Gate 2 (longitudinal): }}\exists A:\,\ell_{{\parallel A}} = {cert.max_ell_par:.4f} > \eta_{{\parallel}} = {cert.threshold} "
        rf"\quad {long_cert} \\" + "\n"
        rf"  &\text{{Gate 3 (transverse): }}\exists B:\,\max(\ell_{{IB}},\ell_{{JB}}) = {cert.max_ell_IJ:.4f} > \eta_{{T}} = {cert.eta_transverse} "
        rf"\quad {tran_cert} \\" + "\n"
        rf"  &\text{{Full carrier certificate: }} {full_cert}" + "\n"
        r"\end{align}"
    )
