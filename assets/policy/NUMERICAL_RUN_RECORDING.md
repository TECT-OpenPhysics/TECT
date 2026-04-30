# Numerical-Run Recording Policy

**Binding from**: 2026-04-29
**Maintainer**: Jusang Lee (`jtkor@outlook.com`)
**Governed by**: `CLAUDE.md` §10 (records completeness), `CLAUDE.md` §10.6 NEW (helper-use binding rule), `Docs/status/INDEX.md` §1 (per-run provenance).

This document is the binding policy for **all** numerical-run drivers
in the TECT repository — PDE solvers, audit pipelines, supplementary
computations, scans, sweeps, Newton-Krylov, Bloch-linearisation,
spectral extraction, and any future addition. The goal is publication-
grade reproducibility by default: every numerical run leaves a
provenance trail that can survive terminal-log loss, hardware change,
and operator turnover.

---

## §1. Three-file canonical archive (binding)

Every `Runs/<class>/<run_id>/` directory MUST contain at minimum these
three files at run completion:

| File | Origin | Purpose |
|---|---|---|
| `run_diagnostics.json` | auto-emitted by `Codes/pde/record_run.py` (binding 2026-04-29) | full per-iteration time-series + provenance metadata |
| `RESULT.md` | populated from `Codes/pde/RESULT_TEMPLATE.md` (binding 2026-04-29) | human-readable §0–§10 standard report |
| `MANIFEST.md` *or* equivalent driver-specific summary | driver-emitted | aggregate gate verdict (PASS / NO_CONVERGENCE / FAIL / INVALID) |

Driver-specific outputs (`Psi_*.npy`, `eigenvalues.csv`, `flow_*.h5`,
etc.) are encouraged but not enforced by this policy.

---

## §2. Universal helper (binding 2026-04-29)

All TECT drivers MUST use `Codes/pde/record_run.RunRecorder` for
per-iteration recording. The 3-call API is:

```python
from Codes.pde.record_run import RunRecorder

rec = RunRecorder.start(
    output_dir=outdir,
    run_class="continuation",   # or "audit", "scan", "sweep", "supplementary"
    driver_name="my_driver.py",
    driver_version="vX.Y.Z",
    theory_tag="MathNN-...-YYYY-MM-DD",
    config={...},                # CLI args, hyperparameters
    constants_check=[...],       # driver-emitted Brazovskii lines (optional)
)

for step_idx, fields in iteration_loop:
    rec.record_step(point_idx=0, step_idx=step_idx, fields=fields)

rec.set_point_summary(point_idx=0, summary={"converged": True, "wall_time_s": 1234.5})

rec.finalize(
    overall_status="PASS",       # or NO_CONVERGENCE, PARTIAL, FAIL, INVALID
    summary={"n_converged": 1, "n_stalled": 0, "wall_time_s": 1234.5},
    emit_result_md_skeleton=True,
)
```

The helper is **defensive**: any persistence failure logs to stderr
and continues, preserving the host driver's exit-code contract. A
driver author should never have to wrap helper calls in `try/except`.

---

## §3. RESULT.md skeleton + operator completion

`record_run.RunRecorder.finalize()` emits a `RESULT.md` skeleton with
§0–§7 auto-populated from the recorder's state. Sections **§8–§10
require operator completion** before the run is publication-grade:

- **§6 Physical Interpretation** (CLAUDE.md §6.3.4 mandatory) — operator
  states ≥1 explicit quantitative sanity check.
- **§8 Cross-References** — atomic-write to `CHANGELOG.md`,
  `Docs/status/research-log.md`, `Docs/status/EVIDENCE-INDEX.md`, and
  (if retraction) `Docs/status/NEGATIVE-RESULTS.md`.
- **§9 Diagnosis & Next-Step Plan** — mandatory if outcome ≠ `PASS`.
- **§10 Sign-off** — operator note (≤200 words honest assessment).

If `RESULT.md` already exists (e.g., retroactively populated), the
helper writes `RESULT.auto-skeleton.md` as a sibling reference instead
of overwriting.

---

## §4. Per-driver-class minimum field set

Different driver classes track different per-iteration quantities.
The helper accepts free-form `fields` dicts; recommended minima:

| Driver class | Recommended `fields` keys |
|---|---|
| Newton-Krylov (continuation, ground-state) | `grad_norm`, `merit`, `F_value`, `rho_trust`, `eta_forcing`, `krylov_iterations`, `step_alpha`, `trust_radius`, `accepted` |
| Bloch / band linearisation | `kpoint_index`, `eigenvalue`, `residual`, `wall_time` |
| Spectral / Hessian audit | `mode_index`, `eigenvalue`, `eigenvector_norm`, `iteration` |
| Scan / sweep | `scan_param`, `observable`, `wall_time`, `seed` |
| Integrator (RG flow, BZ-η, time-evolution) | `t`, `dt`, `state_norm`, `dt_accept`, `n_substep` |
| Supplementary (one-shot) | `iteration`, `intermediate_observable`, `final_observable` |

Any field is acceptable; the helper records whatever is passed.

---

## §5. Migration policy

Existing drivers that do not yet use the helper:

- **Tier 1 (active production drivers)** — must migrate within 1 month
  of policy date (2026-05-29 deadline). Examples: `continuation_mu2_v25.py`
  (already migrated to v2.6.7 native JSON; record_run.py compatible),
  `run_audit_pipeline.py`, `sweep_mu2_phase3.py`, `live_m_parallel.py`.
- **Tier 2 (semi-active)** — migrate when next edited. Examples:
  `bloch_linearization.py`, `phase4_manual_extrapolation.py`,
  `q18_commensurability_sweep.py`, `math46_c2_extractor.py`,
  `math46_c3_extractor.py`.
- **Tier 3 (one-shot supplementary)** — `Codes/supplementary/Math*.py` —
  migrate only if rerun. Past output is grandfathered with retroactive
  RESULT.md if it appears in `EVIDENCE-INDEX.md`.

Migration is a one-line import + 3 helper calls; the helper is
designed to be a drop-in addition, not a refactor.

---

## §6. Publication checklist

For any numerical result cited in a Math note, paper, or status row:

- ☐ `run_diagnostics.json` exists in the canonical run directory
- ☐ `RESULT.md` exists and §0–§7 populated (helper-emitted) + §6, §8–§10 operator-completed
- ☐ Theory tag / driver / git SHA recorded
- ☐ Brazovskii constants verification PASSED (if applicable)
- ☐ §6.3.4 quantitative sanity check explicit in §6
- ☐ Atomic-write performed (CHANGELOG + research-log + EVIDENCE-INDEX)
- ☐ Falsification gate pre-registered (CLAUDE.md §6.3.3) if applicable

A run that fails any of these checks is not publication-grade and may
not be cited as primary evidence.

---

## §7. Failure-mode handling

If `record_run.py` itself fails (import error, disk full, permission
denied), the host driver should:

1. Continue the numerical computation (helper failures are non-fatal).
2. Log the failure to stderr with `[record_run]` prefix.
3. At minimum, emit `MANIFEST.md` + `Psi_*.npy` (driver's own output) so
   the run can be retroactively reconstructed.

The helper itself wraps every persistence call in `try/except`; the
host driver should never see an exception from `RunRecorder` methods.

---

## §8. Records-completeness audit (CLAUDE.md §10.5)

The §7 full-repo audit (`UPDATE_POLICY.md` §7) checks every
`Runs/<class>/<run_id>/` directory for:

- presence of `run_diagnostics.json` (post-2026-04-29 runs only)
- presence of `RESULT.md` (post-2026-04-29 runs only)
- presence of corresponding `EVIDENCE-INDEX.md` row (if cited as primary
  evidence anywhere)

Missing artifacts are logged as audit defects and queued for
retroactive population in the next commit cycle.

---

## §9. Cross-references

- `Codes/pde/record_run.py` — universal helper module
- `Codes/pde/RESULT_TEMPLATE.md` — RESULT.md standard sections
- `CLAUDE.md` §10 — records completeness
- `CLAUDE.md` §10.6 — NEW 2026-04-29 binding helper-use rule
- `CLAUDE.md` §6.3.3 — numerical-result gate (cause/evidence/falsification)
- `CLAUDE.md` §6.3.4 — quantitative sanity-check requirement
- `Docs/status/INDEX.md` §1 — per-run provenance ledger
- `Docs/policy/UPDATE_POLICY.md` §7 — full-repo audit

---

End of NUMERICAL_RUN_RECORDING.md (binding from 2026-04-29).
