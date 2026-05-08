#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conftest.py — shared pytest fixtures for TECT test suite.

Created: 2026-04-22 (Task #116 — Math68 §3 Blocker B5 repair).

Purpose
-------
`PDE/real_backend_pt_bcc_mixed_v3._params_lengths` (line 106) requires
`Lx`, `Ly`, `Lz` keys in the params dict.  Pre-2026-04-22 tests supplied
only `"L": 1.0`, which reliably raised `KeyError: 'Lx'` before any
Krylov dispatch or Hermitian check could execute (2 FAIL / 1 SKIP on
the 2026-04-22 live pytest run of `tests/test_v26_phase_d.py`).

This module exposes `make_bcc_config(L, N, **extras)` as the single
canonical helper for assembling an isotropic BCC config dict with
`Lx = Ly = Lz = L`.  All new tests MUST use this helper; legacy tests
should be retrofitted in the next pass.

The fixture `bcc_config` wraps the helper for pytest-style injection.

Policy (Math68 §3 Prop. math68-B5-fix)
--------------------------------------
Any test that instantiates a BCC backend config dict and does NOT use
`make_bcc_config` (or inject equivalent `Lx/Ly/Lz` keys) is in violation
of the Blocker B5 repair contract.
"""

from __future__ import annotations

from typing import Any, Dict

import pytest


def make_bcc_config(
    L: float = 1.0,
    N: int = 8,
    *,
    mu2: float = -0.5,
    lam: float = -1.0,
    gamma: float = 0.8,
    **extras: Any,
) -> Dict[str, Any]:
    """
    Assemble an isotropic BCC config dict with ``Lx = Ly = Lz = L``.

    Parameters
    ----------
    L : float
        Isotropic box length (same value written to Lx, Ly, Lz, and a
        convenience ``L`` alias for code paths that still read it).
    N : int
        Lattice size per axis.
    mu2, lam, gamma : float
        Physical parameters.  Defaults chosen to match the 2026-04-22
        test_v26_phase_d.py conventions.
    **extras : any
        Additional keys merged last (caller overrides).

    Returns
    -------
    dict
        Config dict with Lx, Ly, Lz, L, N, mu2, lambda, gamma keys,
        plus any extras.  Shadows any backend-required keys via
        merge-order.
    """
    cfg: Dict[str, Any] = {
        "Lx": float(L),
        "Ly": float(L),
        "Lz": float(L),
        "L": float(L),  # retained for legacy code paths
        "N": int(N),
        "lambda": float(lam),
        "gamma": float(gamma),
        "mu2": float(mu2),
    }
    cfg.update(extras)
    return cfg


@pytest.fixture
def bcc_config():
    """Pytest fixture form of ``make_bcc_config`` (default args)."""
    return make_bcc_config()
