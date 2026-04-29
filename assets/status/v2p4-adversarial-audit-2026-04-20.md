# v2.4 Code Adversarial Audit (2026-04-20)

**Auditor role.** Hostile peer reviewer for *Physical Review D / PRL*.
**Scope.** Everything delivered under the v2.4 patch set:
`PDE/v24_thresholds.py`, `tests/test_v24_thresholds.py`,
`Docs/supplementary/v24_threshold_sympy_check.py`,
the `hess_jump_audit.py` v1.0 → v1.1 diff,
the `continuation_mu2.py` v1.0 → v1.1 diff,
`Docs/math/TECT-Math56-Addendum.tex.txt`, and
`Docs/status/v2p4-patch-plan.md`.
**Reference.** Math56-Addendum Theorems 1–5, plus open items X1–X5
in `Docs/status/OPEN-QUESTIONS.md`.
**Verdict summary.** Accept with minor revision — five residual
concerns, none blocking the first continuation run; three are
already tracked as open questions. Two should be added to the
register.

---

## Audit protocol

For every claim I consider:
1. *Theorem-to-code faithfulness* — does the Python expression match
   the symbolic formula, to the digit?
2. *Dimensional and symmetry consistency* — does the code preserve
   what the theorem assumed?
3. *Numerical edge cases* — degenerate denominators, FP cancellation,
   sign-flip near the theorem's precondition boundary.
4. *Regression surface* — does the patch silently change the
   behaviour of existing callers?
5. *Uncovered residual risks* — what the theorem does *not* bound.

Each issue is tagged `[H]` high, `[M]` medium, `[L]` low.

---

## 1. Theorem-to-code faithfulness

### 1.1 Critical scales — `brazovskii_critical_mu2`
```python
r_global = lam * lam / (10.0 * gam)
r_meta   = 2.0 * lam * lam / (15.0 * gam)
```

**Addendum Eq. (1.3)**: $r_c^{\text{global}} = \lambda^2/(10\gamma)$.
**Addendum Eq. (1.4)**: $r_c^{\text{meta}} = 2\lambda^2/(15\gamma)$.

- Numerical check at $(\lambda,\gamma)=(-0.43,1.62)$:
  code returns `(0.011413580..., 0.015218107...)`; SymPy returns
  `Rational(0.43**2,10*1.62) = 0.011413...`. **Match.**
- Ratio: `r_global/r_meta = 3/4` — SymPy scenario C confirms.
  Unit-test `test_critical_numerical_values` asserts this to ten
  decimals. **Pass.**

No issue.

### 1.2 Separatrix roots — `v24_separatrix_thresholds`
```python
R = 4*lam**2 - 30*gam*mu2_target
x_plus  = (-2*lam + sqrt(R)) / (15*gam)
x_minus = (-2*lam - sqrt(R)) / (15*gam)
```

**Addendum Theorem 2**: the quadratic
$15\gamma\, x^2 + 4\lambda\, x + \mu^2 = 0$ (from
$\partial_x \mathcal F / (2x) = 0$, with $x=\phi^2$) has roots
$x_{\pm} = (-2\lambda \pm \sqrt{4\lambda^2 - 30\gamma\mu^2})/(15\gamma)$.

- With $\lambda<0$ and $\mu^2\ll 1$, $-2\lambda>0$ and $\sqrt R
  \leq 2|\lambda|$, so both roots are non-negative. **Sign-safe.**
- Near $\mu^2 \to r_c^{\text{meta}}$ the discriminant vanishes and
  $x_-$ can round negative by $O(10^{-18})$. The code clamps
  `if x_minus < 0.0: x_minus = 0.0`. **Safe.**

**[L-1] Residual concern — no symbolic check inside the
  production module.** The SymPy audit is archived but not wired
  into the import path. If someone later edits `R = 4*lam**2 -
  30*gam*mu2_target` to the apparently equivalent `R =
  4*lam**2 + 30*gam*(-mu2_target)`, no unit test catches the sign
  slip until `test_mu2_target_5e_3` fails five places downstream.
  **Suggested fix.** Add a one-line SymPy round-trip to
  `tests/test_v24_thresholds.py` so the production formula is
  compared against `sympy.solve` each run. Non-blocking; nice to
  have.

### 1.3 $G_0$ — `G0_raw, G0_op`
```python
alpha_sep = phi_minus / phi_plus
G0_raw    = 0.5 * (1.0 + alpha_sep)
G0_op     = G0_raw + cushion                    # cushion = 0.05
```

**Addendum Theorem 2**:
$G_0^{\text{raw}} = \tfrac12(1+\alpha_{\text{sep}})$;
$G_0^{\text{op}} = G_0^{\text{raw}} + \delta$ with $\delta = 0.05$
absorbing the $O(1/N)$ RMS fluctuation (Appendix B of the Addendum).

- At $\mu^2=5\times 10^{-3}$: SymPy gives
  $\alpha_{\text{sep}} = 0.3150$, $G_0^{\text{raw}}=0.6575$,
  $G_0^{\text{op}}=0.7075$. Unit test
  `test_mu2_target_5e_3` asserts `G0_op=0.7075` to four places.
  **Match.**

**[M-1] The cushion is still phenomenological.** The Addendum
  justifies $\delta=0.05$ verbally ("absorbs O(1/N) fluctuation
  at N=32"). For the PRD draft this needs a quantitative tie:
  either a measured fluctuation amplitude from a converged
  Math55 continuation run, or a variance bound of the form
  $\langle (\|\Psi\|_{\mathrm{RMS}}/\varphi_+)^2\rangle - 1 \leq
  C/N^2$ with an explicit $C$. The code is fine; the *theorem*
  is missing a number. Track as **X6 (new open question)**.

### 1.4 $\rho_*$ — `rho_star = rho_star_factor * x_plus`

**Addendum Theorem 3**: $\rho_* = \kappa\,\varphi_+^2$ with
$\kappa=10^{-3}$. Code reads `rho_star = V24_RHO_STAR_FACTOR *
x_plus`, where `x_plus = phi_+^2`. **Match.**

- At $\mu^2=5\times 10^{-3}$: $\rho_* = 6.44\times 10^{-5}$.
  SymPy scenario E and unit test `test_mu2_target_5e_3`
  (`rho_star=6.44e-5`, `delta=1e-6`) agree. **Match.**

**[M-2] $\kappa = 10^{-3}$ is still a dimensional guess.** The
  Addendum derives its scale (energy density $\sim \mu^2
  \varphi_+^2$, thus $\rho\geq\kappa\mu^2\varphi_+^2/\mu^2$), but
  the factor $\kappa$ absorbs both the lattice cell volume and
  the regularisation tolerance of the Class-II step. Ideally
  $\kappa$ is computed from the Newton-step tolerance and the
  cell volume, not asserted. Track as **X7 (new open question)**.

### 1.5 $G_{2,\min}$ and $G_{3,\text{rel}}$

**Addendum Theorem 4**: $G_{2,\min}\geq 1-2\,\delta_N/\|v\| \geq
0.90$ at 20% per-side error budget ($\delta_N=O(N^{-2})$).
**Addendum Theorem 5**: $\|r\| \leq 10^{-1}\,\lambda_{\text{Ritz}}$.

Constants hard-coded to `V24_G2_MIN=0.90`, `V24_G3_REL=1e-1`.
**Match by inspection.** The bound itself relies on:
(i) the interpolation $I_N^{2N}$ being norm-preserving
(verified in `hess_jump_audit.py:_zero_pad_fft` to ratio $1.0000$
on smooth fields); (ii) the Ritz eigenvalue being the ground-state
mode. Both hold in the intended call context.

**[L-2] `v24_phase25_gate` does not enforce the eigenvector
  normalisation.** The doctring says "both inputs must already be
  unit-normalised", but nothing in the code checks `|v|=1`. A
  caller that passes an un-normalised vector silently inflates
  the overlap score and may pass G2 when it should fail.
  **Fix.** Add an assertion
  `abs(np.linalg.norm(a)-1) < 1e-6` inside
  `v24_phase25_overlap`. Five-line change.

---

## 2. Invariance and symmetry

- **Lorentz.** Not at issue here — the reduced BCC moment potential
  $\mathcal F(\phi)=\mu^2\phi^2+\lambda\phi^4+\tfrac52\gamma\phi^6$
  is a spatial zero-mode average, so it is automatically a scalar
  under the SO(3) internal symmetry of the BCC first shell. The
  SO(1,3) question is the one Math_IR_Bound must answer, not this
  module.
- **Gauge.** Not at issue: $\Psi$ is treated as a real scalar
  doublet; no gauge covariance is invoked.
- **Topological.** The thresholds here do not change the Chern
  class of the BCC condensate; they gate *admissibility*, not
  topology. **Safe.**
- **Parameter-domain invariance.** `BrazovskiiParams.__post_init__`
  rejects $\gamma\leq 0$ and $\lambda\geq 0$, so the
  attractive-quartic + confining-sextic regime is enforced at
  construction. **Good.**

---

## 3. Numerical edge cases

### 3.1 Locked-parameter rejection
Call path: `v24_separatrix_thresholds(0.26, p)` with the locked
$\mu^2=0.26$. Discriminant is
$R = 4(0.43)^2 - 30(1.62)(0.26) = 0.7396 - 12.636 < 0$,
so the code raises `ValueError` *before* attempting $\sqrt R$.
Unit test `test_locked_mu2_raises` confirms. **Safe.** The module
self-test (`__main__`) also exercises this path and prints a
friendly message. **Good.**

### 3.2 $\rho_{\min} \to 0^+$
`v24_class2_guard(1e-10, sep)` raises — unit test
`test_below_floor_raises` confirms. The diagnostic message names
$\rho_*$, the factor, and the suggested remediation
("halve continuation step or pick a deeper mu^2_target").
**Good.**

### 3.3 $\lambda_{\text{Ritz}} \to 0$ and $\lambda_{\text{Ritz}}<0$

```python
if abs(lam_ritz) < lam_small_floor:          # 1e-12
    g3_pass = False; bound = 0.0; ratio = inf
else:
    bound = V24_G3_REL * abs(lam_ritz)
    g3_pass = residual_norm <= bound
```

- Zero: explicit fail. `test_G3_fails_on_zero_lam` confirms.
- Negative $\lambda_{\text{Ritz}}$: `abs(lam_ritz)` is used, so
  the bound remains positive, but a *negative* Ritz eigenvalue
  is itself physically pathological (indicates an instability,
  not a mass gap). The gate currently admits a negative
  eigenvalue as long as $\|r\| \leq 0.1|\lambda|$.

**[H-1] Sign of $\lambda_{\text{Ritz}}$ is not gated.** The
Addendum Theorem 5 is stated for $\lambda>0$ (mass-gap
interpretation). A negative eigenvalue that passes G3 would
falsely certify an instability as a clean spectral gap.
**Fix.** In `v24_phase25_gate`, add
`g3_pass = g3_pass and (lam_ritz > 0)`. One-line change; the
unit test file should also add a `test_G3_fails_on_negative_lam`.
This is the only issue in the audit I would label `[H]`.

### 3.4 FP cancellation in `R = 4*lam**2 - 30*gam*mu2_target`
For $\mu^2\to r_c^{\text{meta}}$ the two terms are equal to ten
figures and $R\to 0$ with relative precision $\sim 10^{-15}$.
The code does not rewrite this as `R = 30*gam*(r_meta-mu2)`
which would be condition-number optimal, but for the target
regime $\mu^2\in[10^{-3},10^{-2}]$ we are nowhere near the
cancellation boundary. **Not a real issue at the operating
point; flag for future awareness.**

### 3.5 Empty Ritz-vector payload
`v24_phase25_overlap(np.zeros(0), np.zeros(0))` executes
`np.vdot([],[]) = 0.0` silently. That propagates as
`g2_pass=False` which is the correct behaviour, but the caller
gets no explicit diagnostic. Low risk; the calling convention
(audit script) always passes length-$N^3$ arrays.

---

## 4. Regression surface — behaviour of existing callers

### 4.1 `continuation_mu2.py` v1.0 → v1.1
- Adds a precondition raise and a banner print. If
  `v24_thresholds.py` is absent, `_V24_AVAILABLE=False`, the
  precheck is a no-op, and the banner block is skipped.
  **v1.0 behaviour preserved under import failure.**
- The raise triggers *only* at `mu2_end > r_c^{\text{meta}}`.
  Any pre-existing script pointing at $\mu^2_{\text{end}}=0.26$
  will now abort rather than run to a silent trivial-vacuum
  collapse. **This is the intended operational enforcement of
  the 2026-04-20 retraction; it is a behaviour change, but the
  old behaviour was the bug.**
- CLI defaults (`--mu2-end = 0.30`) are *still* in the argparse
  table. **[M-3] Fix:** update the argparse default to `0.005`
  so a bare `python3 PDE/continuation_mu2.py --config ...` run
  does not immediately trip the new guard. This is cosmetic
  but it affects operator muscle-memory. Suggested for the
  v1.2 bump.

### 4.2 `hess_jump_audit.py` v1.0 → v1.1
- G2: tightened from 0.80 to 0.90. A Phase-2.5 record that
  formerly passed with $O_{00}\in[0.80,0.90)$ will now fail.
  **Intended.** None of the currently-archived Phase-2.5
  records were in that band (the 2026-04-20 run had
  $O_{00}=1.26\times 10^{-4}$, failing at either threshold).
- G3: relative bound replaces absolute $10^{-3}$.
  - At small $\lambda_0 \ll 10^{-2}$ the new bound is *tighter*:
    a record that passed G3 at $\|r\|=5\times 10^{-4}$ with
    $\lambda_0=10^{-3}$ now fails (bound $=10^{-4}$).
  - At $\lambda_0\sim 0.1$ the new bound is *looser*: a record
    with $\|r\|=5\times 10^{-3}$ now passes (bound $=10^{-2}$).
  - This is Theorem 5's intended semantics; absolute bounds
    incorrectly penalised large-gap modes and under-penalised
    near-zero modes.
- **Backward fallback** (`_V24_G3_REL is None`) preserves v1.0
  behaviour when the module is missing. **Safe.**

### 4.3 `tect_newton_krylov.py`
- Not touched in this patch. When v2.4 lands on the solver,
  two integration points are required:
  (i) wire `v24_phase0_gate` on the converged $\Psi^*$ before
  Phase-2 spectral extraction;
  (ii) wire `v24_class2_guard` on `rho.min().item()` inside
  each inner Newton step.
- Both are enumerated in `Docs/status/v2p4-patch-plan.md §3`;
  not yet in code. **Tracked.**

---

## 5. Uncovered residual risks

### 5.1 X1 (continuation path smoothness)
The Math56-Addendum gates guarantee *admissibility at a single
$\mu^2_{\text{target}}$*; they do not guarantee that the
continuation path itself remains on a single branch. A
Math55-style snake-back at an unresolved cusp could still
produce a trivial-vacuum endpoint even though each individual
step passes the Class-II guard. The plan mentions a step-size
cap (`mu2_step $\leq$ 0.01`) as a safeguard, but this cap is
**not yet enforced in code**.
**Status.** Open question X1; tracked in v2p4-patch-plan §4.
No change in v1.1.

### 5.2 X3 (sextic mode-dependence)
Leibler–Wickham reduction yields $K_6=5/2$ under the
first-shell-only BCC ansatz. Away from the exact first-shell
($q=q_0$) the effective sextic coefficient acquires a
mode-dependent correction of order $1.6$ at $\mu^2=5\times
10^{-3}$ (Math37-AddA §A.4). The Addendum quotes $K_6=5/2$
exactly; any $\sim 2\times$ error in $K_6$ rescales
$r_c^{\text{meta}}$ and $r_c^{\text{global}}$ by the same
factor. The recommended $\mu^2_{\text{target}}=5\times 10^{-3}$
sits at $0.44\,r_c^{\text{global}}$, so even a $2\times$ downward
shift in $K_6$ (which would move $r_c^{\text{global}}\to
0.0057$) leaves the target admissible with margin. **Not
currently blocking but to be revisited before the published
$\mu^{*2}$ is reported.** Open question X3.

### 5.3 X4 / X5
X4 (effective-theory convergence under the moment truncation):
open. X5 (the Math37-AddA §A.3 mis-labeling): **resolved by
the SymPy audit**, documented in the erratum line of the
CODE_MANUAL, and non-blocking for v2.4. Math37-AddA §A.3
requires an erratum in its own manuscript, tracked separately.

### 5.4 `K6=5/2` hard-coding
`BrazovskiiParams.K6=5/2` is *exposed* as a field but the module
itself never reads it — every formula uses the literal constant
$5/2$ implicitly (via `30*gam*mu2` = $15\gamma\cdot 2\mu^2$
= $2K_6\gamma\cdot 3\mu^2$ after the usual manipulations, and
the quartic coefficient in the discriminant is
$4\lambda^2$, not involving $K_6$).

**[M-4] `K6` is currently a cosmetic field.** Either remove it
or thread it through `brazovskii_critical_mu2` and
`v24_separatrix_thresholds` so the invariant test file can
verify what happens when Math37-AddA §A.4 ever recommends a
different value. Non-blocking but misleading. Suggested for
v2.4.1.

### 5.5 Math56-Addendum §B numerical erratum traceability
The first draft of the Addendum printed $\varphi_+=0.2482$,
$\varphi_-=0.0781$, $G_0=0.657$ at $\mu^2=5\times 10^{-3}$; these
were traced to a scratch-calculation that reused a 2-digit
$\sqrt R$ instead of the 6-digit value. Corrected values:
$\varphi_+=0.2538$, $\varphi_-=0.0799$, $G_0^{\text{op}}=0.7075$.
`tests/test_v24_thresholds.py::test_mu2_target_5e_3` asserts the
corrected values; the SymPy script emits them at four digits for
archival grep. **Full traceability established.** The erratum
line has been added to the Addendum §F and to CODE_MANUAL
revision history.

---

## 6. Verdict

**Overall.** The v2.4 code faithfully implements the five theorems
of Math56-Addendum to the precision stated. All 21 unit tests
pass; the SymPy audit regenerates the numerical tables
consistently; locked-parameter calls are refused at both the
`v24_thresholds.py` ValueError layer and the `continuation_mu2.py`
RuntimeError layer; Class-II abort raises. The code is
defensively structured (lazy imports, graceful fallbacks, no
`assert` used for runtime invariants) and is drop-in for the
existing solver pipeline.

**Blocking.** None.

**High-priority fix (one line).**
- **[H-1]** `v24_phase25_gate`: add $\lambda_{\text{Ritz}}>0$ to
  the G3 pass condition so a negative-eigenvalue instability
  cannot silently certify.

**Medium-priority follow-ups.**
- **[M-1]** Put a quantitative bound on the $G_0$ cushion
  $\delta=0.05$ once the first Math55 continuation run produces
  $N=32$ RMS-fluctuation statistics (open X6).
- **[M-2]** Derive $\kappa=10^{-3}$ in the $\rho_*$ formula from
  the Newton tolerance + cell volume instead of asserting it
  (open X7).
- **[M-3]** Update `continuation_mu2.py` argparse default
  `--mu2-end` from `0.30` to `5e-3` so the CLI reflects the v2.4
  regime of validity.
- **[M-4]** Either remove the cosmetic `K6` field from
  `BrazovskiiParams` or thread it through the discriminant
  formulas.

**Low-priority hardening.**
- **[L-1]** Add a SymPy round-trip in the unit-test file so the
  symbolic formula is checked against the code on every run.
- **[L-2]** Enforce unit-norm inputs to
  `v24_phase25_overlap`.

**Accept with minor revision.** Proceed with the Math55
continuation run at $\mu^2_{\text{target}}=5\times 10^{-3}$ on
$N=32$; apply `[H-1]` before the first Phase-2 report; schedule
`[M-*]` items against the v2.4.1 bump.

---

## 7. Open-question register updates

The following entries should be added to
`Docs/status/OPEN-QUESTIONS.md` (schema: Q-<date>-<tag>):

- **Q-2026-04-20-X6** — Quantify the $G_0$ cushion. What is the
  measured RMS-fluctuation amplitude
  $\sigma_V = \sqrt{\langle V^2\rangle - \langle V\rangle^2}$
  at $N=32, 64, 128$ for a converged BCC Math55 endpoint?
  Falsification criterion: $\sigma_V(N=32)/\langle V\rangle >
  0.10$ would invalidate the 5% cushion. Impact: tightens (or
  loosens) $G_0^{\text{op}}$ on a data-driven basis.
- **Q-2026-04-20-X7** — Derive $\kappa$ from first principles.
  Express $\rho_*$ as $\kappa(\text{Newton\_tol},
  \Delta x^3, \varphi_+^2)$ and close Theorem 3. Impact: makes
  the Class-II floor traceable to solver settings rather than a
  dimensional ansatz.

---

## 8. Audit sign-off

| Check | Status |
|---|---|
| Theorem-to-code faithfulness | PASS (modulo [H-1]) |
| Dimensional / symmetry consistency | PASS |
| Numerical edge cases | PASS (modulo [H-1]) |
| Regression surface | PASS (modulo [M-3] cosmetic) |
| Unit-test coverage (21/21) | PASS |
| SymPy audit regeneration | PASS |
| Backward compatibility under missing v24 module | PASS |
| Documentation traceability (Addendum, erratum, patch plan) | PASS |

**Auditor recommendation.** Apply [H-1] (one line + one unit
test) before commit; register X6, X7; then proceed to the
Math55 continuation run.
