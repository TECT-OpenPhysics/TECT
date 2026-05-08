# RESULT.md — Per-Run Numerical-Result Standard Template

**Binding from**: 2026-04-29
**Scope**: every `Runs/<class>/<run_id>/` directory must contain `RESULT.md` populated from this template.
**Governed by**: `CLAUDE.md` §10 (records completeness), `Docs/status/INDEX.md` §1 (per-run provenance), `Docs/policy/UPDATE_POLICY.md` §7 (full-repo audit).
**Supersedes**: ad-hoc result reporting in `MANIFEST.md` only (which is now restricted to driver-emitted summary).

---

## §0. Run Identity

| Field | Value |
|---|---|
| **Run ID** | `<class>_<descriptor>_<date_or_seq>` (matches `Runs/<class>/<run_id>/` directory name) |
| **Run class** | `continuation` / `audit` / `seed` / `pretest` / `groundstate` / `coldstart` |
| **Date started (UTC)** | `YYYY-MM-DDTHH:MM:SSZ` |
| **Date ended (UTC)** | `YYYY-MM-DDTHH:MM:SSZ` |
| **Wall time (s)** | `<seconds>` |
| **Maintainer** | Jusang Lee (`jtkor@outlook.com`) |
| **Operator** | (who launched the run; usually identical to maintainer) |

---

## §1. Provenance

| Field | Value |
|---|---|
| **Driver path** | `Codes/pde/<driver>.py` |
| **Driver version** | (from driver's `__version__` or top-of-file header) |
| **Theory tag** | `Math<NN>-<descriptor>-<YYYY-MM-DD>` |
| **Git commit SHA** | (HEAD SHA when run was started) |
| **Module versions** | (paste-ready `MODULE_VERSIONS` snapshot or pointer to `tect_version_manifest.json`) |
| **Hardware** | `<CPU/GPU model + OS>` |
| **Python / PyTorch / CUDA** | `<py X.Y / torch X.Y / cuda X.Y>` |
| **Random seed** | `<seed value or "none">` |

---

## §2. Configuration

Paste the full command-line invocation (PowerShell or bash):

```text
python -u Codes\pde\<driver>.py `
    --config <config>.json `
    ...
```

Critical hyperparameters (one row per relevant option):

| Parameter | Value | Notes |
|---|---|---|
| `--N` | grid size | $N^3$ DoF |
| `--L` | box size (lattice units) | physical interpretation |
| `--mu2` | μ² target(s) | sequential or single-jump |
| `--tol-newton` | Newton tolerance on `||grad||/√dof` | gate criterion |
| `--max-newton` | max Newton steps | gate criterion |
| `--tcg-max` | inner Krylov budget | gate criterion |
| `--krylov-method` | linear-solver choice | `auto`/`gmres`/`fgmres`/... |
| `--load-psi` | initial seed `Psi_*.npy` | provenance trace |
| (other) | (other) | (other) |

---

## §3. Brazovskii / TECT Constants Verification

(Driver auto-prints these; copy verbatim from stdout):

```text
✓ R_C_GLOBAL = ...
✓ R_C_META   = ...
✓ Separatrix order: φ_+ > φ_−
✓ ALPHA_SEP  = ...
✓ Q0         = 1.0 (code-internal)
✓ Q0_PHYSICAL = 0.6801747616
✓ MU2_TARGET = ... (within globally-stable BCC regime)
✓✓✓ All consistency checks passed ✓✓✓
```

If any check FAILS, **the run is invalid and RESULT.md status MUST be `INVALID — constants check failed`**.

---

## §4. Newton-Krylov Convergence Table

Per μ² point, summarise (one row per Newton step OR aggregate if N≥40):

| Step | μ² | `‖grad‖/√dof` | merit | F-value | ρ_trust | η_forcing | tCG | α step | Δ trust | Accepted? |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | ... | ... | ... | ... | ... | ... | ... | ... | ... | ✓/✗ |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

**Aggregate diagnostics** (per μ² point):
- `tCG_peak` = max inner-Krylov iterations across steps
- `ρ_trust_min` = min trust-region acceptance ratio across accepted steps
- `eta_min, eta_max` = forcing-term range observed
- Plateau / divergence step (if any) = step number where convergence rate broke

---

## §5. Outcome Status

Choose ONE of (matches driver's `overall_status`):

- ☐ **PASS** — all μ² points reached `tol_newton` on `‖grad‖/√dof`. Result fully converged.
- ☐ **NO_CONVERGENCE** — every point completed Phase D without converging. Diagnose plateau OR runtime issue.
- ☐ **PARTIAL** — some points converged, some stalled.
- ☐ **FAIL** — exception raised during run.
- ☐ **INVALID** — constants check failed (§3); ignore all numerical results.

**Honest status text** (one paragraph): describe what the run actually shows. Do NOT over-claim. If `NO_CONVERGENCE`, document plateau pattern (which step, which gate hit, what η/Δ trajectory shows).

---

## §6. Physical Interpretation (CLAUDE.md §6.3.4 mandatory)

Per CLAUDE.md §6.3.4, every numerical claim must include ≥1 quantitative sanity check from the binding table:

- ☐ **Dimensional**: confirm both sides of every reported equation have identical dimensions.
- ☐ **Magnitude**: substitute canonical values; verify result agrees with textbook estimate within an order of magnitude.
- ☐ **Limit-case**: check the formula reduces to a known limit (e.g., $\mu^2 \to 0$, $T \to \infty$).
- ☐ **Exponential-magnitude**: if $e^{-x}$ appears, evaluate $x \gg 1 / \sim 1 / \ll 1$ and verify sign of conclusion.
- ☐ **Sign-direction physics**: temperature dependence, rate direction, etc.
- ☐ **Conservation**: charge / energy / topological-invariant.
- ☐ **Numerical reproducibility**: textbook reference for any quoted coefficient.

State ≥1 explicit check carried out in the run text.

---

## §7. Files Persisted

(driver auto-emits these; verify presence)

| File | Purpose |
|---|---|
| `MANIFEST.md` | driver-emitted aggregate summary (per-point table + gate values) |
| `newton_history.json` | per-Newton-step time-series (driver v2.6.7+, 2026-04-29) |
| `Psi_final.npy` | final iterate for warm-restart of subsequent runs |
| `Psi_checkpoint.npy` | last-accepted iterate snapshot |
| `RESULT.md` | this file |

If a file is missing, mark `MISSING` and explain why.

---

## §8. Cross-References (binding)

Update the following ledgers in the same commit as RESULT.md (CLAUDE.md §3 atomic-write):

- ☐ `CHANGELOG.md` — top-level entry under the relevant theory tag.
- ☐ `Docs/status/research-log.md` — dated entry summarising outcome.
- ☐ `Docs/status/EVIDENCE-INDEX.md` — claim → evidence row pointing to this `RESULT.md`.
- ☐ `Docs/status/NEGATIVE-RESULTS.md` — only if outcome is `NO_CONVERGENCE` or `FAIL` and the run retracts a prior claim.

---

## §9. Diagnosis & Next-Step Plan (mandatory if NOT `PASS`)

If the outcome is anything other than `PASS`, this section is binding:

- **Diagnosis**: what physical / numerical / runtime cause underlies the non-PASS outcome?
- **Warm-restart strategy**: which seed (path to `Psi_final.npy`) + which hyperparameter changes (max-newton, tcg-max, krylov-method, μ² staircase) should be tried next?
- **Falsification criterion**: what subsequent observation would invalidate the current TECT claim that the run was meant to support?
- **Anticipated wall time**: order-of-magnitude estimate for the warm-restart run.

---

## §10. Sign-off

| Item | Status |
|---|---|
| Driver constants check | ☐ PASS / ☐ FAIL |
| Convergence gate | ☐ PASS / ☐ FAIL |
| §6.3.4 quantitative sanity check | ☐ PASS / ☐ FAIL |
| Atomic-write ledger update | ☐ DONE / ☐ PENDING |
| RESULT.md complete | ☐ YES |

**Signed (maintainer note)**: (free-text honest assessment; can be the same person who launched the run; ≤200 words)

---

End of RESULT.md template. Last revised 2026-04-29.
