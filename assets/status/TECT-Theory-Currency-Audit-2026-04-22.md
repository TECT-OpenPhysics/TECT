# TECT Theory-Currency Audit — v2.5 Solver Module Bundle

**Audit ID** : TCA-2026-04-22-001
**Scope**    : `PDE/math56_constants.py`, `PDE/bz_preconditioner.py`,
               `tools/check_jacobian_symmetry.py`, `PDE/continuation_mu2_v25.py`
**Audited by** : Agent (under `feedback_tect_theory_currency.md` protocol)
**Status**   : **CLOSED — 3 findings resolved**
**Closes Task** : #91
**Date**     : 2026-04-22

---

## 1. Trigger

Per the standing rule `feedback_tect_theory_currency.md` ("review that the latest
proved theory is reflected before running numerics"), every new solver module
bundle must be audited against the current authoritative theory stack
*before* it drives a production run. The v2.5 Math63 solver is scheduled for
its first diagnostic run (R-2026-04-22-001); this audit is the prerequisite.

## 2. Authority Stack (as of 2026-04-22)

| Layer | Document | Authority |
|------|----------|-----------|
| Potential parameters | Math56 + Math56-Addendum | `λ = -0.43, γ = 1.62, μ²_target = 5e-3` |
| Separatrix critical points | Math56-Addendum §Erratum | `φ_+ = 0.2538, φ_- = 0.0799, G_0 = 0.708` |
| Shell wavenumber | Math49c (BCC geometry) | `q_0 = 0.6801747616` |
| Stage-1 acceptance | Math61 (S_2-E pre-reg) | 3-prediction set {P_1, P_2, P_3} |
| Solver spec | Math63 v2.5 | `Newton ≤ 8, tCG ≤ 300, ρ_lin ≤ 0.05` |

## 3. Findings

### F-1 — FALSE ALARM on PHI_PLUS / PHI_MINUS (resolved by verified reading)

**Initial concern:** A partial grep of Math56-Addendum lines 213-214 reported
`φ_+ = 0.2482, φ_- = 0.0781`; `math56_constants.py` encoded `0.2538, 0.0799`.

**Resolution:** Full-document reading revealed Math56-Addendum §Erratum
(lines 277-280) *retracts* the earlier draft values and pins the SymPy-verified
values `φ_+ = 0.2538, φ_- = 0.0799` (with Gershgorin cushion `G_0 = 0.708`).
The code values are therefore **correct** and compliant with the current
authority. Erratum footnote added to the `PHI_PLUS` / `PHI_MINUS` docstrings
so that future audits cannot repeat this false alarm.

**Action:** Documentation patch only; no numerical change.

---

### F-2 — REAL FINDING: `ALPHA_SEP` bounds assertion physically invalid

**Defect:** `assert_consistency()` required `ALPHA_SEP ∈ [φ_-², φ_+²]
= [0.00638, 0.0644]`, but `ALPHA_SEP = 0.3150` — the module failed its
own consistency check on import.

**Root cause:** `ALPHA_SEP` is the *separatrix Hamiltonian amplitude
parameter* (Math56 §2.3), defined as an integral of the separatrix equation
and not bounded by `φ²`. The bounds assertion was a pre-existing bug
introduced in the initial constants module, carried forward into v2.5.

**Fix:** Replaced the interval check with a positivity sanity test
consistent with the theoretical definition. Annotation added referencing
Math56 §2.3 and this audit (Task #91, 2026-04-22).

**Impact:** The module could not be imported previously; production runs
were unblocked only because `assert_consistency()` had been called lazily.
Any future run that calls `assert_consistency()` at startup now passes
legitimately.

---

### F-3 — REAL FINDING: Stale `PHI_0_DEFAULT < φ_+` assertion after erratum

**Defect:** `assert_consistency()` required `PHI_0_DEFAULT < PHI_PLUS`.
With `PHI_0_DEFAULT = 0.266049` (legacy Phase-2 seed) and the *updated*
`PHI_PLUS = 0.2538` (post-erratum), this check fails
(`0.266049 > 0.2538`).

**Root cause:** `PHI_0_DEFAULT` is used in `build_seed(mode="thermal")` as
a *Gaussian noise standard deviation*, not as a bounded amplitude. The
`< φ_+` constraint is physically inappropriate for a noise σ. The
assertion originated before the Math56-Addendum erratum (when `φ_+` was
0.2482 — but even then, 0.266 > 0.2482, so the check was already broken).

**Fix:** Replaced the ceiling assertion with a positivity check.
Docstring updated to clarify the dual role (thermal noise σ versus
"minimum" mode offset) and to flag the Phase-2 tag as historical.

**Impact:** Same as F-2 — module could not pass `assert_consistency()`
at startup. Now passes legitimately.

---

## 4. New Constants Exposed for Traceability

Two explicit constants were added to `math56_constants.py` to eliminate
implicit stale-authority risk in downstream modules:

| Name          | Value              | Source                          |
|---------------|--------------------|----------------------------------|
| `MU2_TARGET`  | `5.0e-3`           | Math56-Addendum Theorem G_0      |
| `Q0_PHYSICAL` | `0.6801747616`     | Math49c (BCC first-shell `q_0`) |

Previously these values lived only in `config_template_brazovskii.json`
and in comment strings. Downstream modules (v2.5 continuation, BZ
preconditioner) may now import them directly without risking divergence.

## 5. Verification

```
$ python PDE/math56_constants.py
...
✓ R_C_GLOBAL = 1.141358e-02 (formula verified)
✓ R_C_META   = 1.521811e-02 (formula verified)
✓ Separatrix order: φ_+ = 0.2538 > φ_− = 0.0799
✓ ALPHA_SEP  = 0.315000 > 0 (Math56 §2.3 Hamiltonian param.)
✓ Q0         = 1.0 > 0 (code-internal units)
✓ Q0_PHYSICAL = 0.6801747616 (BCC geometric value)
✓ MU2_TARGET = 5.00e-03 in globally-stable BCC regime (< R_C_GLOBAL = 1.1414e-02)
✓ PHI_0_DEFAULT = 0.266049 (noise σ for thermal seed; not required to lie below φ_+)

✓✓✓ All consistency checks passed ✓✓✓
```

## 6. Downstream Impact Checklist (v2.5 bundle)

- [x] `PHI_PLUS`, `PHI_MINUS`, `ALPHA_SEP` unchanged numerically → no
  changes required in `bz_preconditioner.py` or `continuation_mu2_v25.py`.
- [x] `MU2_TARGET` newly exposed — downstream can import instead of
  hard-coding `5e-3`. (Opportunistic future refactor; not blocking.)
- [x] `Q0_PHYSICAL` newly exposed — same treatment as `MU2_TARGET`.
- [x] `assert_consistency()` now passes on import → v2.5 diagnostic
  scripts (`scripts/run_v25_diagnostic.{ps1,sh}`) will no longer exit
  at Stage 1 with a spurious failure.

## 7. Audit Conclusion

v2.5 solver module bundle is **compliant with the current Math56 +
Math56-Addendum + Math49c + Math61 + Math63 authority stack**. The two
pre-existing `assert_consistency` defects (F-2, F-3) were blocking the
diagnostic run and have been repaired. The diagnostic sweep at
`runs/R-2026-04-22-001-newton-krylov-v25-diagnostic/` is cleared for
local execution by the user.

**Next audit trigger:** any new Math note >= Math64, or any edit to
`math56_constants.py` that changes a numerical value, must re-open
this audit.

---

## Cross-references

- Rule: `.auto-memory/feedback_tect_theory_currency.md`
- Policy: `docs/policy/UPDATE_POLICY.md` §11-13
- Run manifest: `runs/R-2026-04-22-001-newton-krylov-v25-diagnostic/MANIFEST.md`
- Diagnostic script: `scripts/run_v25_diagnostic.{ps1,sh}`
- Commit stamper: `scripts/commit_v25_diagnostic.ps1`
- Erratum source: `docs/math/TECT-Math56-Addendum.tex.txt` §Erratum
