# TECT Negative Results Ledger

**Binding from**: 2026-04-15
**Maintainer**: Jusang Lee (jtkor@outlook.com)
**Governed by**: `docs/policy/UPDATE_POLICY.md` §9

This ledger preserves the *negative evidence* generated during TECT
research — failed hypotheses, retracted numerical results, and
abandoned approaches. Success is logged in `CHANGELOG.md` and
`docs/status/research-log.md`; this document is the parallel record
of what did **not** work, *why* it did not work, and what superseded
it.

Entries are append-only. Text is never redacted. Items may be
reopened if new evidence arrives, in which case a new entry is added
citing the reopened record — the original stays intact.

Schema: each entry is stamped `[F|R|D]-<YYYY-MM-DD>-<seq>` where
`F` = failed hypothesis, `R` = retracted result, `D` = dead-end
approach.

---

## R — Retracted results

### F-2026-04-24-Phase-Z-symmetric-seed-saddle — Phase Z Math55 deep-endpoint re-run: M2 (reversed schedule) confirmed; M1 (BCC symmetric 6-cosine seed) lands at SADDLE not minimum

**Hypothesis under test**: the Math82-Addendum-B Phase Z numerical harness (M1 BCC analytic seed + M2 reversed continuation schedule) achieves convergence at the deep endpoint $\mu^2 = -1.0$ with $\|\nabla \mathcal{M}\|/\sqrt{\dim} < 10^{-8}$ within `--max-newton 12`, providing the missing numerical anchor for Pillar 11.

**Result (Math82-Addendum-D)**: PARTIAL. 3/5 points converge, 2/5 stall. The pre-registered success criteria (Math82-Addendum-B §6) are met for criteria 2 and 5 fully and 1, 3, 4 for 3/5 of points. Specifically:

- Point 1 (μ²=+5e-3, BCC seed): STALL at 12 Newton iter, ||grad||=2.65e-6 (one to two more iterations would have reached 1e-8).
- Point 2 (μ²=-0.02, warm-start): CONVERGED 4 iter, lambda_min = +1.747e-2 (stable).
- Point 3 (μ²=-0.1, warm-start): CONVERGED 0 iter, **lambda_min = -6.253e-2 (SADDLE)**.
- Point 4 (μ²=-0.5, warm-start): CONVERGED 1 iter, **lambda_min = -4.625e-1 (SADDLE)**.
- Point 5 (μ²=-1.0, deep endpoint): STALL with bizarre ρ = -1e30 trust-region pathology (degenerate Newton step on the indefinite Hessian inherited from saddle warm-start).

**Diagnostic decomposition**:

1. **M2 (reversed schedule with warm-start chain)**: SUCCESSFUL. Points 2-4 converge in 0-4 Newton iterations, confirming warm-start delivers Psi to ~1e-8 between mu² steps.

2. **M1 (BCC analytic seed)**: PARTIALLY SUCCESSFUL. Initial residual at Point 1 dropped from ~1.44e+5 (thermal seed, prior run) to ~5.42e+3 (BCC seed, this run) — a **27× improvement**. Inner-Krylov bottleneck resolved: t_CG max = 65 (vs. prior 15000 ceiling). Eisenstat-Walker η_EW does not auto-promote.

3. **Symmetric 6-cosine ansatz lands at SADDLE**: the Phase 2 Lanczos signal at Points 3, 4 reveals lambda_min < 0 — Newton correctly identifies the maximally-O_h-symmetric BCC ansatz as a stationary point, but it is not a local minimum. Theorem (Math82-Addendum-D §2.2): the symmetric 6-cosine zero-relative-phase BCC ansatz is the saddle that connects the 24 BCC ground-state variants. The Hessian has at least 23 unstable directions in the amplitude phase-space, corresponding to the directions that break O_h to a smaller stabiliser.

4. **Point 5 catastrophic failure**: at μ² = -1.0 the indefinite Hessian inherited from the saddle generates a degenerate Newton step (predicted_m = actual_m = 0 in floating point, ρ becomes numerical garbage ~-1e30, trust region halves to nothing without progress).

**Cause** (3-part traceability, part 1): the BCC analytic seed was constructed with maximally O_h-symmetric structure (6 unit wave-vectors with equal amplitude and zero relative phase). This is the natural starting point for an unbiased BCC ansatz, but it sits at the maximally-symmetric center of the 24 BCC ground-state variants' orbit, which is the saddle.

**Evidence** (3-part traceability, part 2): Run output at `Runs/continuation/math55_endpoint_N32_Lbcc7_phaseZ_2026-04-24/`; per-point Phase 2 Lanczos lambda_min values are unambiguous; Point 5 trust-region degeneracy ρ = -1e30 is reproducible.

**Decision chain** (3-part traceability, part 3): (a) M2 (reversed schedule) confirmed working — adopt as standard practice. (b) M1 (BCC symmetric 6-cosine seed) confirmed as initial-residual-reducer but not as ground-state seeker — must be combined with symmetry breaking. (c) New sub-task `Q-2026-04-24-P11-symmetry-broken-seed` (Task #93) opened: construct symmetry-broken BCC seed (4-cosine subset, or random phase shifts, or Lanczos-eigenvector perturbation) for Math82-Addendum-E re-run. (d) Pillar 11 status REMAINS at NEAR-CLOSURE; the symmetric-seed saddle finding is a positive physical result.

**Positive findings (independent of the failure)**:

- Theorem `thm:saddle` (Math82-Addendum-D §2.2): the maximally-symmetric 6-cosine BCC ansatz is a saddle point of the Brazovskii functional. This is a real physical result that constrains the structure of the BCC ground-state manifold.
- The 24 BCC ground-state variants are now an explicit object whose O_h-orbit determines the Hessian instability count.
- M2 (reversed schedule) is production-validated.
- M1 inner-Krylov resolution is production-validated (no more 15000-ceiling saturation).

**Re-promotion criteria for Pillar 11 deep-endpoint anchor**:
- Math82-Addendum-E re-run achieves 5/5 converged with lambda_min > 0 at all interior points (true BCC minimum, not saddle).
- This separately requires Math58-v6 Dirac-sector tightening (Math58-v7 = independent pending work).

**Result tag**: `F-2026-04-24-Phase-Z-symmetric-seed-saddle`. **Math notes**: `TECT-Math82-Addendum-B-Phase-Z-BCC-analytic-seed-runbook.tex.txt` (run plan), `TECT-Math82-Addendum-D-Phase-Z-result-PARTIAL.tex.txt` (this verdict). **Resolves**: nothing (opens follow-up `Q-2026-04-24-P11-symmetry-broken-seed`).

---

### F-2026-04-24-R5-FirstIteration — Pillar 10 R5 residual-matching audit (first iteration) fails pre-registered failure criterion

**Hypothesis under test (R5)**: a single dimensionless completion parameter $\chi_* := \hbar/(m_e c\,a_{\mathrm{BCC}})$ is consistently inferred from four independent residual mismatches between exact classical TECT predictions and observed physics:
$$\bigl\{\,\delta\Lambda,\;\;\delta F_{\mathrm{Casimir}}(d=1\,\mu\mathrm{m}),\;\;\delta\lambda_{\mathrm{Compton}},\;\;\delta a_e\,\bigr\}.$$

**Result (numerical extraction, `Codes/supplementary/Math79_R5_chi_star_extraction.py`)**: Two independent calibration conventions (Compton-anchored with $\chi_*^{(\mathrm{Comp})}=1$; electron-energy-anchored with $E_{\mathrm{BCC}}^{\mathrm{phys}} = m_e c^2$) yield consistent ratio values
$$
\rho_\Lambda \approx 3.4\times 10^{-44}, \quad \rho_{\mathrm{Cas}} \approx -8.7\times 10^{-7}, \quad \rho_{g{-}2} \approx +8.0\times 10^{+7}.
$$
None of these lies in the pre-registered success window $[0.5, 2.0]$, and all three lie outside the conservative failure window $[0.1, 10]$. Math79 §7 Theorem on R5 failure is satisfied at the dimensional-ansatz level.

**Diagnostic interpretation (three failure modes)**:
1. *$\Lambda$ channel ($\rho \approx 10^{-44}$)*: cosmological constant residual is 44 orders smaller than a Compton-anchored universal scale would predict. This quantitatively reproduces the standard cosmological-constant problem (60–120 orders mismatch in QFT vacuum-energy estimates) and indicates that $\Lambda$ residual physics belongs to a different universality class than electron-scale physics.
2. *Casimir channel ($\rho \approx -10^{-7}$ with sign mismatch)*: classical-TECT defect-mediated stiffness is not the dominant boundary-energy mechanism; the sign error reflects the dimensional ansatz's failure to encode the attractive boundary condition.
3. *$g{-}2$ channel ($\rho \approx +10^{+7}$)*: QED loop structure providing the Schwinger $\alpha/(2\pi)$ term is fundamentally larger than a naive classical defect-vertex estimate.

The three failure modes go in three different directions ($\Lambda$ too small, Casimir too small with wrong sign, $g{-}2$ too large), so no rescaling, no choice of $a_{\mathrm{BCC}}^{\mathrm{phys}}$, and no choice of $Y_{\mathrm{SI}}$ can simultaneously bring them to unity.

**Cause** (3-part traceability, part 1): R5 framework was designed to provide a binary verdict on the existence of a single universal completion scale; the dimensional-ansatz first iteration was the simplest possible test. The pre-registered failure outcome is itself a meaningful scientific result, not a procedural error.

**Evidence** (3-part traceability, part 2): `Math79_R5_chi_star_results.json` (first-iteration scan output); `Docs/math/TECT-Math79-Addendum-A-R5-first-iteration-FAILURE.tex.txt` (formal write-up with derivation, calibration tables, and diagnostic interpretation).

**Decision chain** (3-part traceability, part 3): (a) `Q-2026-04-24-P10-R5-residual-matching` resolved-negative in OPEN-QUESTIONS. (b) Pillar 10 status REMAINS at OPEN-NEGATIVE REFINED (no change — the failure reinforces the existing classification). (c) The honest scope statement is preserved: TECT is a UCFT with $\hbar$ external. (d) A refined-$C_i$ second iteration (Math79-Addendum-B) is theoretically possible but de-prioritised given the 44-order gap on $\Lambda$.

**Result tag**: `F-2026-04-24-R5-FirstIteration`. **Math note**: `TECT-Math79-Pillar10-R5-residual-matching-framework.tex.txt` + `Math79-Addendum-A-R5-first-iteration-FAILURE.tex.txt`. **Resolves**: `Q-2026-04-24-P10-R5-residual-matching`.

---

### R-2026-04-24-RoundOverclaim — Three Round 9 (2026-04-24) pillar-closure declarations retracted by reviewer audit

**Retracted claims**:
1. **Pillar 4 = `UNCONDITIONAL PROVED`** (Round 9 final scorecard).
2. **Pillar 6 = `FULL CLOSURE`** (Round 9 final scorecard, on the strength of `Math77-Q6c-Q6d-closure`).
3. **Pillar 11 = `FULLY PROVED (4/4 sectors)`** (Round 9 final scorecard, on the strength of `Math58-v6-Pillar11-Dirac-sector-closure` plus the v2/v3/v4/v5 chain).

**Audit verdicts (2026-04-24)**:

1. *Pillar 4* ⇒ **PARTIAL-ADVANCED**. Q2 (RG-flow derivation) self-classifies as `PARTIAL WITH CONCRETE RG EVIDENCE`; Q3 closes the local moment-map and reduced-dimension-$24$ statements but the identification with the $G_{\mathrm{SM}}$ gauge-field phase space is still conjectural. Full numerical RG integration to the exact $G_{\mathrm{SM}}$ IR fixed point and the $\omega_{\mathrm{red}}$ global Poincaré-form matching are pending. Closure also requires anomaly-matching integration with the matter sector.

2. *Pillar 6* ⇒ **PARTIAL-ADVANCED**. The Math77 base note (`Math77-Pillar6-GUT-embedding`) and the Q6a/Q6b note (`Math77-Q6a-Q6b-closure`) both classify Pillar 6 as PARTIAL-ADVANCED. The Q6c/Q6d note (`Math77-Q6c-Q6d-closure`) declares `Pillar 6 FULL CLOSURE` while simultaneously labelling Q6c and Q6d themselves as PARTIAL-ADVANCED with deferred numerics — internal status-semantics conflict. The 10-defect-moduli count in Q6a is reclassified as conjecture in the same session notes. The argument *"Q6c, Q6d are PARTIAL-ADVANCED, therefore Pillar 6 is fully closed"* is not accepted.

3. *Pillar 11* ⇒ **NEAR-CLOSURE / not yet final archive theorem**. Mainline acceptance: `Math58-v2`, `Math58-v3`, `Math58-v4-sublemma-closure` (supersedes the earlier v4-partial; vortex sector closed unconditionally), and `Math58-v5` (BCC sector $\Delta\Lambda_{\rm BCC}=0$, with wording softened to honestly describe a renormalization-convention vanishing rather than a pure symmetry theorem). Held: `Math58-v6` (Dirac sector) is a STRONG CLOSURE DRAFT for two reasons. (i) **Internal status-sync defect**: the total $\Lambda_{\rm cosmo}$ summation inside v6 still labels the vortex sector as `partial` and writes "*once the vortex-sector sub-lemmas are closed*", although `Math58-v4-sublemma-closure` (in the same upload bundle) already closes those sub-lemmas. (ii) **Renormalization-convention vs symmetry**: the Dirac-sector vanishing rests on the chain "UV zero-point integral is a contact term $\propto V$; absorbed by vacuum renormalization in a periodic box; finite fermionic energy is a chemical-potential shift; the finite part is zero for $\Lambda$ by definition". This is plausible but is a renormalization-convention statement, not a symmetry-driven cancellation theorem of the same evidentiary class as the monopole CP and vortex CP sectors.

**Cause** (3-part traceability, part 1): The 2026-04-24 autonomous Round 9 closed pillar sectors faster than the underlying evidence supported, in part because the round summary (Math78-RESEARCH-SESSION-SUMMARY) was written ahead of the pillar-level theorem notes and then propagated backward into the changelog without an audit step.

**Evidence** (3-part traceability, part 2): The 2026-04-24 reviewer audit identified internal status-sync defects in Math58-v6 (Dirac-sector wording inconsistent with sibling notes), Math77-Q6c-Q6d (declares closure while underlying components remain partial), and Math78 (synthesis table internally classifies Pillar 5 both as FULL CLOSURE and PARTIAL-ADV in different sub-files; Stage-2 meta-consistency uses obsolete pillar mapping).

**Decision chain** (3-part traceability, part 3): (a) The pillar-level theorem notes are preserved unchanged. (b) Explicit `% [AUDIT-STATUS 2026-04-24]` banners are inserted in the over-claiming files (`Math58-v6`, `Math_IR_Bound-v4-PC-3A-L6-closure-attempt`, `Math_IR_Bound-v4-thm-v4-2-H-suppression-closure`, `Math78-Stage2-Meta-Consistency-Round9`, `Math78-TOE-Global-Closure-Synthesis`) and a confirming MAINLINE banner in `Math_IR_Bound-v4-thm-v4-2-final-formalization`. (c) `TOE-FACT-SHEET` Stage-1 scorecard rewritten with the audit-verified statuses. (d) The original Round 9 CHANGELOG entry is preserved per append-only discipline but tagged `[Audit-superseded 2026-04-24]`. (e) A canonical-source hierarchy is fixed: pillar-level theorem note > round summary > global synthesis draft. (f) SRP-v1 (Session Resumption Protocol) is added to `UPDATE_POLICY.md` §14 to prevent future status drift across session boundaries.

**Stage-3 consequence**: The Round 8 advance from `0/3 MISSING` to `1.5/3 PARTIAL-ADVANCED`, which depended in part on `$\pi_2$ FALSIFIED by Pillar 11 closure`, is provisionally rolled back to `≤ 1/3 PARTIAL-ADVANCED`. Task #87 (Math61 amendment) is REOPENED.

**Re-promotion criteria**:
- Pillar 4 ⇒ UNCONDITIONAL PROVED requires: full numerical RG integration showing the $G_{\rm SM}$ IR fixed point + global $\omega_{\rm red}$ Poincaré matching + anomaly-matching integration.
- Pillar 6 ⇒ FULL CLOSURE requires: completion of Q6a (10-moduli enumeration as theorem, not conjecture), Q6b (numerical RGE), Q6c (formal SO(10) uniqueness theorem), Q6d (Yukawa/flavor emergence). This is the recommended Round 10 mainline.
- Pillar 11 ⇒ FULLY PROVED requires: Math58-v6 status-sync repair against `Math58-v4-sublemma-closure`, AND tightening of the Dirac vanishing argument from a renormalization-convention statement to either a symmetry theorem or an explicit-convention closure with the convention stated.

**Result tag**: `R-2026-04-24-RoundOverclaim`. **Audit-rollback CHANGELOG entry**: `[Audit Rollback — 2026-04-24]`.

---

## F — Failed hypotheses

### F-2026-04-21-R5W2 — Single-Schur-functor Pillar-6 strategy falsified through $|\lambda|\le 25$ ($k\le 5$)

**Hypothesis under test**: there exists a single partition $\lambda$ with $|\lambda|=5k$, $\ell(\lambda)\le 5$ for which
$$
M^{\lambda}\;:=\;\dim\mathrm{Hom}_{G_{\rm SM}}\!\bigl(\mathbb{C}_{(\mathbf{1},\mathbf{1})_{0}},\;S^{\lambda}V\bigr)
\;=\;c^{\lambda}_{(k,k,k),(k,k)}\;\ge\;2
$$
(ideally $=3$, which would positively resolve the single-bundle version of Pillar 6 — three generations realised by one $SU(5)$-irrep). The hypothesis was left open at wave-1 (Math49d-R5 v1.0, 2026-04-20) where the exhaustive enumeration for $k\le 3$ ($|\lambda|\le 15$) gave $\sup M^\lambda=1$.

**Result**: wave-2 (Math49d-R5-wave2 v1.0, 2026-04-21) extends the enumeration to $k\in\{4,5\}$, i.e.\ $|\lambda|\in\{20,25\}$. Out of all $192$ partitions of $20$ and $377$ partitions of $25$ with at most $5$ parts, exactly $15$ and $21$ respectively realise $M^{\lambda}=1$; all remaining partitions satisfy $M^{\lambda}=0$. In particular,
$$
\sup_{\lambda\vdash 20,\;\ell\le 5} M^{\lambda}\;=\;\sup_{\lambda\vdash 25,\;\ell\le 5} M^{\lambda}\;=\;1.
$$
Combined with wave-1: $\sup_{|\lambda|\le 25,\;\ell\le 5} M^{\lambda}=1$. The falsification criterion registered in `Q-2026-04-20-PR1` is therefore **met** at search depth $k\le 5$.

**Structural observation** (not part of the falsification, but recorded for future analytic work): the count of $M=1$ partitions at fixed $|\lambda|=5k$ is $\binom{k+2}{2}$ ($=15$ at $k=4$, $=21$ at $k=5$); every realiser satisfies $\lambda_{3}=k$ exactly. A closed-form proof of $M^{\lambda}\le 1$ for all $k$ would permanently close the question beyond the census range.

**Evidence artefacts**:
- `Docs/math/TECT-Math49d-R5-replacement-wave2.tex.txt` (v1.0, md5 `1ee8f075`), Theorem `thm:wave2` and Table I.
- `Docs/supplementary/Math49d_R5_replacement_search_wave2.py` (v1.0, md5 `8541621b`); runtime $0.05\,{\rm s}$.
- `Docs/supplementary/Math49d_R5_wave2_report.json` (md5 `8665629c`) — full census.
- `Docs/supplementary/logs/Math49d_R5_wave2_run.log` — audit log.

**Supersedes** (in the sense of closing the question, not of replacing content): the wave-1 note Math49d-R5 v1.0 which left $k\in\{4,5\}$ open.

**Operative replacement (wave-1, unchanged)**: minimal multi-bundle realisation $E_{\min}=\mathcal{O}\oplus\det V\oplus S^{(2,1,1,1)}V$, total rank $7$; each summand independently carries $M^{\lambda}=1$.

**Pillar 6 impact**: SCAFFOLD at the physical layer is **retained** (not downgraded). The geometric three-count $\chi^{\mathbb{Z}_6}(\mathrm{Gr}(2,5),\mathrm{Sym}^{2}Q)=3$ from Math49d-R3 retains its PROVED status on the arithmetic layer. Next step for physical closure: either (i) prove $M^{\lambda}\le 1$ for all $k$ (closed form), or (ii) compute the twisted Dirac chirality index on $E_{\min}$ under the BCC disclination connection; or (iii) pivot to a partial-flag variety per `Q-2026-04-20-R4`.

**Result tag**: `F-2026-04-21-R5W2`.  **Associated OPEN-QUESTIONS archive entry**: `Q-2026-04-20-PR1` (RESOLVED 2026-04-21 later).

---

### F-2026-04-20-05 — Newton-Krylov projected-Lanczos eigenvalue exhibits a $\times 17$ jump between $N=32$ and $N=64$; clean continuum extrapolation is falsified

**Hypothesis under test**: the sequence $\{m^{*2}_{\text{num}}(N)\}_{N\in\{32,64,128\}}$ obeys the leading-order lattice-spacing expansion
$$
m^{*2}_{\text{num}}(N) \;=\; m^{*2}_{0} \;+\; c\,h(N)^{2} \;+\; \mathcal{O}(h^{4}), \qquad h(N) = 2\pi L/N,
$$
permitting a two-point linear fit in $h^{2}$ to extract $m^{*2}_{0}$ (Phase 4 of the Newton-Krylov proof protocol, Math51–53).

**Result**: `verdict: "falsified at the two-grid level: magnitude jump incompatible with h^2 scaling"`. Numerical values:
- $N=32$, $h_{32}^{2} = (2\pi\cdot 20\pi/32)^{2} \approx 15.42$, $m^{*2}_{32} = 3.1485$.
- $N=64$, $h_{64}^{2} = (2\pi\cdot 20\pi/64)^{2} \approx 3.855$, $m^{*2}_{64} = 54.07$.

The naïve linear fit would predict $c = (m^{*2}_{32} - m^{*2}_{64})/(h_{32}^{2} - h_{64}^{2}) = (3.1485 - 54.07)/(15.42 - 3.855) \approx -4.40$ and $m^{*2}_{0} = 54.07 - c\cdot h_{64}^{2} = 54.07 - (-4.40)(3.855) \approx 71.0$, which is absurd: (i) it contradicts the analytic prediction $m^{*2}_{\text{analytic}} = 9.005$ by nearly an order of magnitude in the wrong direction, (ii) a negative slope $c<0$ combined with the $N=32$ value yields $m^{*2}_{0} > m^{*2}_{64}$, violating any physically sensible "finer grid approaches continuum from below" or "from above" monotonicity prior.

**Root cause — three candidate explanations (ranked by prior plausibility)**

1. **Eigenvector-family migration**. The projected Lanczos at $N=32$ plausibly locks onto the physical longitudinal gap mode; at $N=64$ the finer grid resolves additional UV shell modes whose projected Hessian eigenvalue dominates the first Lanczos eigenvector. **Test**: dump the top-8 Lanczos eigenpairs at both grids and compute the overlap matrix of leading eigenvectors restricted to the common BZ shells. If the $N=32$ leading eigenvector overlaps with the $N=64$ eigenvector rank $\geq 4$, eigenvector-family migration is confirmed.
2. **Merit/projector normalisation latent $N$-dependence**. The projected Hessian carries an implicit $(dx)^{3}$ volume factor through the $L^{2}$ inner product. If the merit function $m = \tfrac{1}{2}\|R_{\mathrm{proj}}\|^{2}$ or the tangent-space projector $P_\perp$ inherits a counting-vs-integrating convention in the shell-mask sum that has not been absorbed, the eigenvalue scales with $N$. **Test**: audit `tect_newton_krylov.py` — in particular the projector construction around the BCC shell mask, and the Lanczos matrix–vector product — for any sum-over-modes that should have been rescaled by $V_{\text{box}}/N_{\text{dof}}$.
3. **Accidental $N=32$ near-degeneracy**. The coarser grid produced an artificial level crossing; $N=64$ is closer to the true continuum. This is the only prior under which the extrapolation is *allowed* to be steep, but requires the eigenvector-overlap test in (1) to come back clean.

**Result tag**: `R-2026-04-20-02-newton-krylov-N64-2026-04-20`. **Run command**: `python tect_newton_krylov.py --config config_template_brazovskii.json --N 64 --L 20pi --phases 123 --tol 1e-6`. **Locked parameters**: $(\mu^{2}, \lambda, \gamma) = (0.26, -0.43, 1.62)$.

**Superseded by**: `Math56-HessJump-audit-2026-04-20` (2026-04-20).  The three candidate explanations above (eigenvector-family migration, projector normalisation, accidental near-degeneracy) were **all refuted by direct measurement** via `PDE/hess_jump_audit.py`. The Phase-2.5 audit (Fourier-band localisation $\rho_{\mathrm{UV}}$, cross-grid zero-pad overlap, Ritz residual) established the true root cause: at both grids the Newton-Krylov solver terminated on the **trivial vacuum** $\Psi^{\ast}\approx 0$ (RMS$|\Psi^{\ast}|/\varphi_{0} = 3.43\times 10^{-6}$ at $N=32$ and $2.64\times 10^{-6}$ at $N=64$, where $\varphi_{0} = \sqrt{-4\lambda/(15\gamma)} = 0.266$), so the reported "$m^{*2}$" values $3.1485$ and $54.07$ are **not** BCC-condensate projected-Hessian eigenvalues — they are artefacts of the Class-II effective term's $\rho^{-1}$ singularity at $\Psi\to 0$ (the guarded quotient $q_{\alpha} = m_{\alpha}/(\rho + 10^{-12})$ becomes ill-conditioned at $\rho\sim 10^{-10}$). See `Docs/math/TECT-Math56-HessJump-audit.tex.txt` §5 for the full empirical dossier; resolution key `MATH55_CONTINUATION_REQUIRED`.

**What remains PASSED despite this F**: (i) Phase 1 existence at $N=64$ is PASS ($\|\nabla\| / \sqrt{\mathrm{dof}} = 1.55\times 10^{-7}$, 10 Newton steps), **but converges to the trivial vacuum**, not to the BCC minimum; (ii) the Newton-Krylov v2.3 solver infrastructure itself is validated at 1.57 M degrees of freedom, with the caveat that it requires a Math55 continuation path to guarantee escape from the $\Psi = 0$ basin; (iii) the mode count $n_{\mathrm{neg}} = 0$ is retained only as a statement about the spectrum *at the point reached*, not as evidence for BCC stability.

**Phase 3 (vacuum favorability) at $N=64$**: the reported $\Delta F = +9.38\times 10^{-10} > 0$ is now understood to be $F[\Psi^{\ast}]-F[0] \approx 0$ with sign set by Class-II and shell-bias cross-terms at the trivial vacuum; it is **not** a thermodynamic comparison against the BCC condensate. This entry remains FAIL and is subsumed by the same root-cause correction above. No new $F$ entry is opened for Phase 3.

**Remediation path**: protocol v2.4 = (G0) Phase-0 vacuum-escape gate RMS$|\Psi^{\ast}|/\varphi_{0} \geq 0.3$; (G1) Fourier-band localisation $\rho_{\mathrm{UV}} < 0.1$; (G2) cross-grid zero-pad overlap $\mathcal{O} \geq 0.8$; (G3) Ritz residual $\eta < 10^{-3}$; **plus** Class-II guarded quotient with $\rho_{\mathrm{cut}} \sim 10^{-3}\varphi_{0}^{2}$. Entry point: Math55 continuation sweep from $\mu^{2}_{0} = -1$ (condensed basin) to the locked value $\mu^{2}=0.26$, producing a genuine BCC $\Psi^{\ast}$ at $N=32$ and $N=64$ for a legitimate Phase-2 comparison.

---

### F-2026-04-16-01 — Q18 commensurability sweep (2026-04-15 vintage) was infrastructurally falsified by a kinetic/seed mismatch, not by physics

**Hypothesis under test**: `Q-2026-04-15-18` — in the Brazovskii-locked
regime with `q0 = 0.6801747616`, the measured radial peak
`q0_meas = argmax_k |Ψ(k)|²` should converge monotonically to `q0`
(equivalently to `k_min = √(-Z/(2Y))`) as the continuum limit is
approached via the three-grid sweep
`(N, L) ∈ {(32, 10π), (64, 20π), (128, 40π)}`.

**Result**: `verdict: "falsified: q0_meas does not track k_min within
one bin at finest grid"` — but for a reason unrelated to physics.

**Root cause — config-kinetic inconsistency**: The config
`PDE/config_template_brazovskii.json` carried `(Z, Y) = (-1.0, 0.5)`,
which gives kinetic minimum `k_min = √(-Z/(2Y)) = 1.000`, while the
same config declared `q0 = 0.6801747616`. The backend
`real_backend_pt_bcc_mixed_v3.py::_brazovskii_linear_term_t` uses
`(r, Z, Y)` literally, and `q0` enters only through `bcc_seed` init
(and `_shell_bias_term_t`, which was disabled with `eta_shell = 0`).
The solver therefore tried to evolve a seed placed at `k = 0.6802`
under a kinetic that pulls toward `k = 1.000`.

**Evidence (three-grid `--skip-solve` post-hoc measurement,
audit_run 2026-04-16)**:

| N   | dk    | q0_meas | q0_meas/dk | q0_meas·L | status         |
|-----|-------|---------|------------|-----------|----------------|
| 32  | 0.200 | 0.5196  | 2.598      | 16.32     | not a shell    |
| 64  | 0.100 | 0.2598  | 2.598      | 16.32     | not a shell    |
| 128 | 0.050 | 0.1299  | 2.598      | 16.32     | not a shell    |

The dimensionless ratio `q0_meas / dk = 3√3/2 = 2.598…` is **identical
across all three grids**, i.e. `q0_meas ∝ 1/L`. The peak is at a
fixed box-relative index, not at a physical wavevector, which falsifies
any interpretation as a Brazovskii shell. The `err_in_bins_of_dk`
metric **worsens** with N (−2.4 → −7.4 → −17.4), confirming divergence
from the kinetic minimum rather than convergence to it.

Solver residual signatures confirm non-convergence:
- N=32: final residual 2.75e-2, energy −16.88 (frustrated transient,
  residual reverses from 2.46e-2 to 2.75e-2 over steps 900→1499);
- N=64: final residual 5.32e-4, energy −7.80e-3 (near-trivial uniform);
- N=128: final residual 1.89e-4 (reverses from 1.50e-4 to 1.89e-4
  over steps 900→1499), energy −1.24e-3 (near-trivial).

**Superseded by**: config fix `[config-kinetic-fix-v2-2026-04-16]` —
full Math38 coefficient closure.

**v1 fix** (same date): set `(Z, Y) = (−0.9252754126, 1.0)` to enforce
`k_min = q0`. However, v1 left `r = mu2 = 0.26`, which gives
`omega(q0) = r − Z²/(4Y) = 0.046` — effective shell mass 5.65× too low.
This would corrupt the condensate amplitude and break locked-triple
self-consistency even though the shell *position* was correct.

**v2 fix** (same date): additionally set `r = mu2 + Y q0^4 = 0.4740336473`.
Now `omega(q0) = mu2 = 0.26` exactly, and the full dispersion
`omega(k) = r + Z k² + Y k⁴` matches `Y(k² − q0²)² + mu2` at every
order. Tag: `config-kinetic-fix-v2-2026-04-16`.

**Propagation**:
- Config patched: `PDE/config_template_brazovskii.json`
  `(r, Z, Y) = (0.4740336473, −0.9252754126, 1.0)`.
- Code-manual entry updated: `docs/manual/CODE_MANUAL.md` §2 now
  carries the full three-coefficient binding relation.
- `UPDATE_POLICY.md` §13 gate: any future config change touching
  `r, Z, Y, q0, mu2` must satisfy `Z = −2Yq0²` **and** `r = mu2 + Yq0⁴`,
  or carry an explicit NEGATIVE-RESULT `R` entry explaining the deviation.
- Q-2026-04-15-18 remains **open** pending re-run against the v2-patched
  config; the 2026-04-15-vintage sweep output is archived at
  `PDE/runs/q18_sweep_2026-04-15/` with this note attached.

---

### F-2026-04-15-01 — Ginzburg–Landau critical-surface regime for TECT

- **Original claim** (pre-Math38): TECT's condensate lives on the
  Ginzburg–Landau critical surface with `(r, λ, γ) ≈ (0.25, +0.35,
  0.05)`, i.e. $\lambda > 0$ and $\gamma$ small.
- **Evidence of failure**: Under this regime the analytic Math37
  prediction and the numerical extractor outputs diverged by a
  factor of roughly $32\times$ that could not be closed by any
  normalisation or patch-layout correction.
- **Root cause**: TECT is the **inverse-superconductor** — the
  topological condensate lies on the Brazovskii first-order locked
  branch ($\lambda < 0$, $\gamma > 0$ sizeable), not on a GL
  critical surface. The GL regime was a sign-and-magnitude error in
  the continuation-schedule fit that set the original locked
  parameters.
- **Superseded by**: `Math38-Brazovskii-2026-04-15`, which
  self-consistently reproduces $(\mu^{2}, \lambda, \gamma) = (0.26,\,
  -0.43,\, 1.62)$ from the three-equation matching $\mathcal{F}(\phi_{0}) = \mathcal{F}(0)$,
  $\mathcal{F}'(\phi_{0}) = 0$, $\mathcal{F}''(\phi_{0}) = \mathcal{M}^{2}_{\mathrm{meas}}$.
- **Archive**: `PDE/backup_GL_2026-04-15/configs/` contains the 32
  GL-regime config files + rollback `README.md`. Do not use in
  production runs.

### F-2026-04-15-02 — Uncorrected first-order lock $\phi_0^{2} = -2\lambda/(3\gamma)$

- **Original claim** (pre-Math37 AddA): $\phi_0^{2} = -2\lambda/(3\gamma)$,
  giving $\phi_0^{2} = 0.17695$ at the locked parameters.
- **Evidence of failure**: The derivation implicitly assumed the
  simple-cubic constellation normalisation ($K_4 = K_6 = 1$). Under
  the correct BCC 12-vector constellation sums $K_4 = 1$, $K_6 = 5/2$,
  the Hessian coefficient on the $\gamma\phi_0^{4}$ term is
  $30 K_6 \gamma = 60\gamma$, not $30\gamma$.
- **Superseded by**: Math37 Addendum A, $\phi_0^{2} = -4\lambda/(15\gamma) \approx 0.07078$.
- **Code locus of correction**: `PDE/tect_actual_extractor_pt_v3.py`
  L619–625, using $\mathrm{denom} = 3 K_6 \gamma$.

### F-2026-04-15-03 — Angular constant $I_3$ left un-fixed between `1/3` and `1`

- **Original state** (pre-Math37 AddA): Math37 §5.5 carried two
  candidate values for $I_3$ — the angular average $1/3$ and the
  constellation average $1$ — without resolution. Numerical code
  used neither explicitly; the effective longitudinal stiffness was
  the bare BCC Laplacian symbol.
- **Evidence of failure**: Ambiguity propagated into $\lambda_\parallel$
  and polluted the $m^{*2}$ closure.
- **Superseded by**: Math37 Addendum A §A.1 proves $I_3 = 1/3$
  *uniquely* from $O_h$ invariance of the BCC constellation. No
  further calibration freedom.
- **Code locus of correction**: `PDE/tect_actual_extractor_pt_v3.py`
  L646 locks `I3 = 1/3`.

### F-2026-04-15-04 — Three-parameter $(u,v,\kappa)$ BCC pair-kernel ansatz

- **Original claim** (pre-Math31): The BCC first-shell pair kernel $K_{ij}$
  can be exhaustively parametrised by the three scalars $(u,v,\kappa)$
  corresponding to $A_{1g}$, $E_{g}$, $T_{2g}$ moments of the 12-vector
  constellation.
- **Evidence of failure**: Math31 Theorem 2.3 — the residual kernel-rank
  deficit $\Delta_{\mathrm{ker}} \approx 32976$ shows that the
  three-parameter ansatz is structurally insufficient; the four-class
  decomposition is mandatory.
- **Superseded by**: Four-class BCC pair-kernel decomposition (Math31),
  which closes the rank deficit and becomes the canonical kernel
  representation entering Math32–Math35.
- **Archive**: Math31 §2–§3 retains the three-parameter calculation as
  pedagogical counter-example.

### F-2026-04-15-05 — $A/E$-symmetric coarse model for the flavor sector

- **Original claim** (Math32, Math33 early drafts): The flavor Gram
  matrix can be captured by an $A/E$-symmetric coarse model (two shell
  parameters, one off-diagonal coupling).
- **Evidence of failure**: The coarse model fails to reproduce the
  $T_{2g}$ mixing block and leaves a residual $O(1)$ mismatch in the
  Gram minors along the locked line.
- **Superseded by**: Full four-class kernel + canonical locked basis
  (Math35), which introduces the $3\times3$ $S_{\min}$ minimum.
- **Archive**: Math32 §4, Math33 §2 retained as working-note trace.

### F-2026-04-15-06 — Scalar Bragg mass $B_{0}$ as a physical mass channel

- **Original claim** (pre-Math12): A scalar Bragg mass $B_{0}$ could
  open at the Dirac node, giving a parity-preserving mass term.
- **Evidence of failure**: Math12 witness theorem — opposite-valley
  pairing plus the valley $\mathbb{Z}_{2}^{V}$ symmetry forbids the
  scalar Bragg channel; only the parity-odd Dirac mass is admissible
  and it is protected.
- **Superseded by**: Witness theorem (Math12 §2–§3); mass protection
  via $U(1)_{V}$ / $\mathbb{Z}_{2}^{V}$.

### F-2026-04-15-07 — Toy positive-sign local potential ansatz

- **Original claim** (Math26 exploratory §1): A local potential
  $V(\phi) = +\tfrac{\lambda}{4}\phi^{4} + \ldots$ with $\lambda>0$
  could host the TECT condensate.
- **Evidence of failure**: Math26 §2 — positive-sign local quartic
  gives only the trivial vacuum; the Brazovskii lock requires
  $\lambda<0$ stabilised by $\gamma\phi^{6}$ at sixth order.
- **Superseded by**: Brazovskii regime lock (Math38, F-2026-04-15-01
  resolution).
- **Lesson preserved**: Local-potential positivity is incompatible
  with topological-condensate existence. Negative quartic + positive
  sextic is the minimal stabilising triple.

---

## R — Retracted numerical results

### R-2026-04-15-01 — Legacy target $m^{*} = 0.3138$

- **Provenance**: Appeared in `PDE/check_and_continue_finetune.bat`
  line 102 as a benchmark comment. Not derived from any Math-note
  or Paper; not computed by any pipeline stage.
- **Status**: Retired as an unverified legacy artefact at the
  Math37 m\*-provenance audit (2026-04-15). No theoretical
  traceability. Must not be cited as a prediction or target in
  any paper, talk, or website page.
- **Current analogue**: The well-traced analytic prediction is
  $m^{*2}_{\mathrm{TECT}} \approx 9.005$ (Math37 AddA at the
  Brazovskii-locked parameters), i.e. $m^{*} \approx 3.00$ — one
  order of magnitude above the retired benchmark.

### R-2026-04-15-02 — v3.0 solver run with seed=17 (silent GL regime)

- **Run context**: User executed `tect_solver_pt_FINAL.py` (pre-rename)
  and `tect_solver_pt_v3.py` v3.0 on seeds 17 / 23 / 41 / 73.
  Seed 17 completed with residual $= 2.88 \times 10^{-5}$, energy
  $= -2.65 \times 10^{-5}$; seeds 23/41/73 failed with
  `FileNotFoundError`.
- **Evidence of failure**: Residual and energy magnitudes are
  consistent with GL pre-convergence, not Brazovskii locked-branch
  convergence. Diagnostic: the v3.0 rename was cosmetic only —
  `make_default_config` retained hard-wired $\lambda = +0.35$,
  $\gamma = 0.05$, $r = 0.25$, and there was no `--config` CLI
  flag to inject the Brazovskii triple.
- **Verdict**: Every v3.0 run executed on a file named for the
  Brazovskii regime was in fact a GL run. All v3.0 result tags
  of form `R-<date>-<seq>-Math38-Brazovskii-...` that predate
  Patch A are retracted.
- **Superseded by**: Solver Patch A (`tect_solver_pt_v3.py` v3.1):
  hard-wired Brazovskii defaults at L207/209, `--config` JSON
  overlay at L642/677–681, regime banner echo at L747–753.
- **Status**: Re-run pending on user machine once stale
  `__pycache__/*FINAL*.pyc` is purged.

---

## D — Dead-end approaches and blockers

### D-2026-04-21-001 — Task #54 Math55 continuation blocked: PyTorch environment unavailable

**Attempted action**: Execute `continuation_mu2_fast.py` v1.1 Newton-Krylov continuation from $\mu^2=0.26$ to $\mu^2_{\rm target}=5\times 10^{-3}$ on grid $N=32$, followed by (if successful) $N=64$ run.

**Blocker**: Missing PyTorch dependency. The computational backend `real_backend_pt_bcc_mixed_v3.py` (line 23) imports `torch`. Installation via `pip install torch --break-system-packages --no-cache-dir` failed with OOM (Exit code 143, process killed mid-install).

**Environment**: /sessions/intelligent-funny-cerf/mnt/Contents, filesystem 238GB (200GB used, 38GB avail); pip cache cleared; Python 3.10.

**Root cause analysis**:
1. PyTorch wheel build/download is memory-intensive (~2GB in typical CI).
2. Current session environment may have per-process or per-user memory limits.
3. Pre-built wheels for this platform/Python combination may be unavailable or require compilation.

**Impact**:
- **Task #54**: BLOCKED (no numerical result; cannot execute continuation).
- **Task #55 X6**: BLOCKED (depends on Task #54 Phase-2 spectral eigenvalues for $\sigma_V(N)$ scaling).
- **Pillar 1 closure**: BLOCKED (requires Math55 Phase-2 projected-Lanczos data).
- **Math61 prediction P3 measurement**: BLOCKED (pending Task #54 continuum limit for $Z_h$).

**Workarounds attempted**:
1. `pip install torch --no-cache-dir`: OOM → killed.
2. Checked for pre-installed PyTorch: not found.
3. Examined if pure-NumPy backend is available: `real_backend_pt_bcc_mixed_v3.py` is torch-only (no fallback).

**Recommended remediation**:
1. Retry continuation in a session with larger memory allocation or a dedicated GPU node.
2. Consider implementing a lightweight NumPy-only backend (would require `real_backend_pt_bcc_mixed_v3.py` rewrite, ~days of work).
3. Pre-compile PyTorch wheels in a build session and cache locally.

**Not a theoretical blocker**: The continuation mathematics (Math55, Math56, Math56-Addendum) is sound. The failure is purely environmental. Once PyTorch is available, continuation will execute without code changes.

**Evidence artefacts**:
- Session attempt log: `/sessions/intelligent-funny-cerf/mnt/Contents/runs/R-2026-04-21-001-newton-krylov-v2p4-FAILURE.md` (manifest).
- Attempted config: `/sessions/intelligent-funny-cerf/mnt/Contents/PDE/config_mu2_target_5e3.json`.
- Attempted command line: (recorded in FAILURE manifest).

---

## D — Dead-end approaches (archived)

### D-2026-04-15-01 — Continuation-schedule fit as first-principles parameter derivation

- **Approach**: The original `(μ², λ, γ) = (0.26, -0.43, 1.62)`
  triple cited throughout Math01–36 was obtained from a
  continuation-schedule fit, i.e. a numerical annealing that
  stabilised a working point, then read the parameters off the
  endpoint.
- **Why abandoned**: The fit produced correct numerics by accident
  — there was no derivation from RG flow, 1-loop matching, or any
  first-principles scheme. The identity of the *regime* itself
  (Brazovskii vs GL) was ambiguous in the original notes, which is
  what allowed F-2026-04-15-01 to persist.
- **Superseded by**: Math38 path-α (theory-first) derivation: the
  three-equation matching system reproduces the same triple
  self-consistently from the Brazovskii effective potential at the
  measured curvature $\mathcal{M}^{2}_{\mathrm{meas}}$, with $K_6 = 5/2$.
- **Lesson preserved**: Numerical coincidence is not theoretical
  derivation. Future parameter locks must provide a matching
  condition *and* the regime classification *before* being accepted.

### D-2026-04-15-02 — `paired_basis_extractor_v2.py` with `m_parallel = None` default

- **Approach**: `m_parallel` was declared as an optional kwarg
  defaulting to `None` and propagated unchanged through all
  callers. `bcc_compare/grid64_bcc/` scans never passed it, so every
  paired-basis summary reported `null`.
- **Why abandoned**: Silent null-propagation hid the absence of a
  live computation. D5 stayed open for weeks because the numerical
  output *looked* present but was structurally empty.
- **Superseded by**: `PDE/live_m_parallel.py` (v1.0, 2026-04-15),
  wired into `run_pipeline_n1.py` as Stage U2c. Computes per-patch
  / per-antipodal-pair / shell-mean $m_\parallel$ directly from
  `transport_extractor` outputs; emits `live_m_parallel_summary.json`.
- **Original file** is retained under `PDE/deprecated/paired_basis_extractor_v2.py`
  for audit only — no live imports.
- **Lesson preserved**: Optional kwargs that stand in for
  computations are a structural anti-pattern. Every physics
  observable must be either computed live or raise — never default
  to `None`.

### D-2026-04-15-03 — 8-patch axis-aligned extractor layout as the canonical convention

- **Approach**: The first-generation extractor hard-wired 8 patches
  (2 polar + 6 equatorial) with $N_\alpha = 1$, giving $W_0 = 8$,
  $W_2 = -1$, $\varepsilon_\mathrm{lock} = -3/8$.
- **Why abandoned**: The BCC first-shell constellation has $|S_\mathrm{BCC}| = 12$
  star vectors. The 8-patch layout drops 4 of the 12 vectors, so
  the patch-moment normalisation is inconsistent with any
  constellation-symmetric average. This contributed a factor of
  $12/8 = 1.5$ in $m^{*}$ (≈ $2.25\times$ in $m^{*2}$) to the
  pre-Math38 mismatch.
- **Superseded by**: Math37 AddA introduces projection factor
  $R_\mathrm{patch} = 45/16 \approx 2.81$ that post-hoc corrects
  legacy 8-patch outputs. New work must use the 12-constellation
  layout at source; `R_\mathrm{patch}` is a compatibility shim,
  not the target of future extractors.
- **Lesson preserved**: The patch layout is a **physics choice**,
  not a discretisation convenience. Drop-in axis-aligned grids
  violate constellation symmetry.

### D-2026-04-15-04 — Naive small-$p$ perturbation without norm-uniform bounds

- **Approach** (Math24 §1 exploratory): Expand Hessian eigenvalues
  in small momentum $p$ without tracking norm-uniform bounds on the
  remainder.
- **Why abandoned**: The bare small-$p$ expansion does not control
  $Z_{\mathrm{pol}}^{(T)}$ loop weight corrections; Math24 §3 shows
  the leading bound is not norm-uniform.
- **Superseded by**: Norm-uniform estimate programme (Math24 §4 onward);
  $Z_{\mathrm{pol}}^{(T)}$ itself tracked as Q-2026-04-15-11.
- **Lesson preserved**: Perturbative expansion in a compact
  parameter must be accompanied by a uniform-in-$p$ remainder bound
  before being admitted as an analytic identity.

### D-2026-04-15-05 — Two-shell-parameter linear map for flavor Gram

- **Approach** (Math32 §3 exploratory): Reduce the flavor Gram matrix
  computation to a two-shell-parameter linear map, assuming the
  $T_{2g}$ block is captured by a single off-diagonal entry.
- **Why abandoned**: Math33 shows the two-parameter map is
  rank-deficient on the locked line — it fails to produce positive
  $\det G$ at interior points, matching F-2026-04-15-05.
- **Superseded by**: Full four-class kernel + $S_{\min}$ canonical
  basis (Math35).
- **Lesson preserved**: Dimensional reductions of the Gram matrix
  before establishing full-rank at a single reference point produce
  false closures.

### D-2026-04-15-06 — Pauli Route A (non-gauge-covariant $SU(2)$ embedding)

- **Approach** (pre-Pauli Supp): Embed the Pauli channel directly
  at the fibre level without gauge-covariantising the transverse
  phonon derivatives.
- **Why abandoned**: Route A breaks $SU(2)$-covariance under
  rotations of the phonon frame; the resulting connection is not
  the Levi-Civita of the emergent metric and fails the Nijenhuis
  integrability test (Nija_Tensor supp).
- **Superseded by**: Pauli Supplementary Route B — gauge-covariant
  $SU(2)$ emergence on the transverse-phonon bundle with
  Levi-Civita connection on $TS^{2}$.
- **Lesson preserved**: Gauge structures emergent on a curved
  internal space must be constructed covariantly on the bundle, not
  at a single reference fibre.

### D-2026-04-20-02 — Naive direct-sum three-generation ansatz $E_L(a,b) = S\otimes(\det Q)^a \oplus Q\otimes(\det S)^b$ on $\text{Gr}(2,5)$ rigorously FALSIFIED ($\chi = 3$ not realised for any integer $(a,b)$) — first falsification-grade computation in the TECT ledger

- **Hypothesis under test**: The three-generation count of the Standard Model arises from the Hirzebruch–Riemann–Roch index $\chi(\text{Gr}(2,5), E_L) = 3$, where $E_L$ is the direct-sum bundle $S \otimes (\det Q)^a \oplus Q \otimes (\det S)^b$ with $S$ the tautological rank-2 subbundle, $Q$ the rank-3 quotient bundle, and $(a,b)\in\mathbb{Z}^2$ tunable twist parameters. This ansatz was the original Math49 target (both scaffold and first rigorous rewrite) for Pillar 6 (three-generation fermion count).
- **Why the question was asked**: The branching rule $\mathbf{5} = (\mathbf{3},\mathbf{1})_{-1/3} \oplus (\mathbf{1},\mathbf{2})_{1/2}$ under $G_{\text{SM}} \subset SU(5)$ suggests that the fundamental SM representation assembles naturally from tautological-plus-quotient bundles on $\text{Gr}(2,5)$. The direct-sum $E_L(a,b)$ was the most economical such construction.
- **Result — FALSIFIED-ANSATZ**: `Math49-rigorous-v2` computes $\chi(E_L(a,b))$ exactly via Bott equivariant localisation in sympy rational arithmetic for all $(a,b) \in [-8, 8]^2 \cap \mathbb{Z}^2$. Corollary 1 establishes direct-sum additivity $\chi(E_L(a,b)) = \chi_S(a) + \chi_Q(b)$, which extends the scan to all integers via the two univariate sequences $\chi_S(a), \chi_Q(b)$. Theorem 2:
$$\chi(E_L(a,b)) = 3 \quad \text{has no solution for } (a,b) \in \mathbb{Z}^2.$$
Explicit ranges on $[-8,8]$:
$$\{\chi_S(a)\}_{a=-8}^{8} \cap [0, 10^4] = \{0, 5, 40, 175, 560, 1470, 3360, 6930\},$$
$$\{\chi_Q(b)\}_{b=-8}^{8} \cap [0, 10^4] = \{0, 5, 10, 45, 75, 210, 315, 700, 1890, 4410, 9240\}.$$
The minimum positive value in either image is 5, so no non-negative combination equals 3. (Negative values on the image sets are accommodated by Serre duality but likewise never sum to 3.)

**Evidence (rigorous)**:
- **Sanity suite (Prop. 1 of Math49-v2)**. Five Weyl-dimension-formula validations against the SL(5) Borel–Weil–Bott theorem:

  | $d$ | $\chi(\mathcal{O}(d)) = s_{d,d}(1^5)$ | Bott-localisation (sympy) | Match |
  |-----|----------------------------------------|---------------------------|-------|
  | $-1$ | 0 | 0 | ✓ |
  | 0 | 1 | 1 | ✓ |
  | 1 | 10 | 10 | ✓ |
  | 2 | 50 | 50 | ✓ |
  | 3 | 175 | 175 | ✓ |

  This confirms that the sympy kernel (with symbolic $t_i = 1 + z_i \varepsilon$ pole-cancellation expansion; $z = (1,2,3,5,7)$) computes $\chi$ correctly.

- **Main scan (Theorem 1 of Math49-v2)**. $\chi(E_L(a,b))$ tabulated on $[-3,3]^2$; no cell contains the value 3. Extended scan via additivity on $[-8,8]^2$: no solution.

**Root cause — a combinatorial / arithmetic obstruction**: The direct-sum structure factorises the global Euler characteristic into two independent SL(5) Weyl-dimension sequences, neither of which contains 3 in its image. Specifically,
$$\chi_S(a) = (\text{dim of an irrep of } SL(5) \text{ of highest weight determined by } a), \quad \chi_Q(b) = \text{idem}.$$
The smallest positive SL(5) irreducible-representation dimensions accessible through these twists are 5, 10, 40, 45, 175, … The integer 3 is never an SL(5) irrep dimension. Hence no direct-sum realisation of the ansatz can yield $\chi = 3$.

**Superseded by**: Three refinement paths, tracked as `Q-2026-04-20-R1`, `Q-2026-04-20-R3`, `Q-2026-04-20-R4` in `OPEN-QUESTIONS.md`:
- **R1**: replace direct sum with an irreducible Schur-functor image $\mathbb{S}^\lambda(S\oplus Q)$; the resulting $\chi$ is no longer a sum of SL(5) dimensions and may include 3.
- **R3** (HIGHEST PRIORITY): compute the $\mathbb{Z}_6$-equivariant Lefschetz index; the three-generation count would emerge as the count of $\mathbb{Z}_6$-fixed points on $\text{Gr}(2,5)$, mirroring Heterotic orbifold constructions.
- **R4**: replace $\text{Gr}(2,5)$ with the partial flag $\mathrm{Fl}(2,3;5)$ (fallback if R3 fails).

- **R2 RULED OUT**: discrete quotient of $\text{Gr}(2,5)$ cannot deliver three copies because $\pi_1(\text{Gr}(2,5)) = 1$; no non-trivial cover exists.

**Lesson preserved**: The fact that a target integer (three, in this case) is inaccessible through a direct-sum construction is itself useful information — it concentrates refinement effort on genuinely inhomogeneous bundles (Schur-functor, equivariant, partial-flag) rather than infinite parameter tuning. The additivity observation $\chi(E_L(a,b)) = \chi_S(a) + \chi_Q(b)$ reduces an infinite $(a,b)$-scan to two univariate scans, making the falsification rigorous and exhaustive. Falsification of a *structural* ansatz — not merely of a numerical value — is the cleanest form of negative result a topological approach can generate.

**Discipline significance**: This is the first *rigorous falsification* in the TECT ledger. The preceding `F-` and `D-` entries record failed numerical fits or abandoned approaches; Math49-v2 records the exhaustive refutation of a mathematically well-posed conjecture using exact arithmetic. The TECT update policy (`docs/policy/UPDATE_POLICY.md` §11, §13) is hereby strengthened: **Pillar closures will henceforth require computed, not asserted, index/character/dimension values**. Any future Math-note asserting a topological count must either (i) enumerate the relevant cohomology/index symbolically or (ii) provide a fixed-point localisation calculation analogous to `Math49_hrr_v3.py`.

**Addendum 2026-04-20 (independent-channel corroboration)** — The $\mathbb{Z}_6$-equivariant Lefschetz scan of the same direct-sum bundle family,
$$\chi^{\mathbb{Z}_6}(E_L(a,b)) \;\text{ on }\; (a,b) \in [-3,3]^2 \;\subset\; \mathbb{Z}^2,$$
computed by the independent multiprecision kernel `Math49d_equivariant_bott.py` (dps=200, eps=1e-50, 10-point $T$-localisation on three $\zeta$-fixed components), yields the image set
$$\mathrm{image}\,\chi^{\mathbb{Z}_6}(E_L(\cdot,\cdot))\big|_{[-3,3]^2} = \{0, 8, 42, 50, 62, 104, 203, 211, 265\}.$$
No entry equals $3$. The $\mathbb{Z}_6$-refined direct-sum ansatz is therefore falsified on a completely disjoint logical channel (equivariant trace vs.\ ordinary HRR integral), with all six character traces $\chi_{\zeta^k}$ computed separately and summed as $\tfrac{1}{6}\sum_k \chi_{\zeta^k}$. This second-channel falsification **strengthens** D-2026-04-20-02 to a double-root ruling: the failure of the direct-sum ansatz is not an artefact of the ordinary index but a genuine structural obstruction.

**Successor (positive)**: The structural three-ness emerges from an *irreducible* bundle under the same $\mathbb{Z}_6$ refinement, not from a direct sum. `Math49d-R3-rigorous-v2` (2026-04-20) proves $\chi^{\mathbb{Z}_6}(\mathrm{Sym}^2 Q) = 3$, with the three coming from the dimension of $\mathrm{Sym}^2 V_\beta$ = the $\mathbb{Z}_6$-invariant isotype inside the $\mathbf{15}$ of SU(5). See Q-2026-04-20-R3 archive entry.

**Artefacts preserved**:
- `docs/math/TECT-Math49-rigorous-v2.tex.txt` — full PRL-style derivation with sanity suite + main theorem + additivity corollary + falsification corollary + refinement enumeration.
- `docs/supplementary/Math49_hrr_v3.py` — sympy Bott-localisation kernel (exact Rational arithmetic).
- `docs/supplementary/Math49_hrr_v3_output.txt` — execution log with all sanity checks and the $[-3,3]^2$ / $[-8,8]$ scan outputs.

---

### D-2026-04-20-01 — Five Math notes (Math49, Math49b, Math49c, Math_EP, Math_IR_Bound) initially labelled PROVED/CLOSED/ANALYTICALLY BOUNDED without sufficient rigour

- **Approach (2026-04-20)**: A same-day autonomous closure sprint
  produced five PRL-formatted Math notes targeting Pillars 2, 6, 7,
  8, 9 of the TOE fact-sheet. These were logged in `CHANGELOG.md`,
  `research-log.md`, `TOE-FACT-SHEET.md`, `EVIDENCE-INDEX.md` and
  `OPEN-QUESTIONS.md` as theorem-level closures.
- **Why flagged**: A strict devil's-advocate review performed on the
  same day identified technical defects in four of the five notes:

  1. **Math49** — real dimension of $\text{Gr}(2,5)$ stated as 6 rather
     than the correct $\dim_\mathbb{R} = 12$ (complex-dim 6); Â-genus
     conflated with Euler characteristic in Eq.(20); instanton number
     $k = 1$ asserted without derivation; the final
     arithmetic step "$2 + 1 = 3$" conflated bundle rank with the
     topological index.
  2. **Math49b** — Eq.(19) U(1)_Y³ sum included only $Q_L$ and $L_L$,
     omitting $u_R, d_R, e_R$ and the Weyl multiplicities
     $(6,3,3,2,1)$; the correct per-generation sum
     $6(1/6)^3 + 3(-2/3)^3 + 3(1/3)^3 + 2(-1/2)^3 + 1(1)^3 = 0$
     was not written out. SU(2)³ vanishing reason inverted — should
     invoke $d^{abc} = 0$ in $\mathfrak{su}(2)$, not "including $e_R$".
  3. **Math49c** — structurally close to complete, but missing the
     lemma identifying the BCC disclination charge with the generator
     of $\pi_1(\text{SO}(3)/G_{\text{pt}})$; point group $O_h$ vs.\ $O$
     not clearly distinguished.
  4. **Math_EP** — proof is tautological: all three stress tensors
     $T^W$, $T^{\text{def}}$, $T^{\text{grav}}$ are defined as
     $(2/\sqrt{-g})\,\delta S/\delta g^{\mu\nu}$ of the same action,
     so their coincidence is a definitional identity, not a physical
     WEP statement. Eq.(24) contains a "this gives a sign flip"
     mid-proof comment indicating the derivation was not finalised.
     A genuine WEP proof requires dynamical definitions of $m_I$ and
     $m_G$ and a theorem identifying them.
  5. **Math_IR_Bound** — Eq.(3) chose a quadrupole spin-2 operator
     $(\partial_i \partial_j \Psi)^2 - \tfrac{1}{3}(\nabla^2\Psi)^2$
     rather than the cubic-$O_h$ invariant
     $\sum_i (\partial_i \Psi)^4 - \tfrac{1}{3}(\sum_i(\partial_i\Psi)^2)^2$.
     The canonical dimension was misstated; the one-loop anomalous
     dimension $\eta = +0.02$ was asserted without a diagrammatic
     calculation; the SME bound $c_{\mu\nu} \lesssim 10^{-70}$ was
     quoted from literature rather than derived from a BCC
     Brillouin-zone integral.

- **Discipline corollary**: The `UPDATE_POLICY.md` memory rule
  "never label prototype work as rigorous / proof-grade" was violated
  by the initial closure labelling. Same-day downgrade restored
  discipline: `TOE-FACT-SHEET.md` summary scorecard now reads
  "1 PROVED, 1 CLOSED@1-loop, 2 PARTIAL, 4 SCAFFOLD, 1 OPEN, 2 NOT
  ADDRESSED", and the five reopened items sit in `OPEN-QUESTIONS.md`
  as Q-2026-04-20-ZZ-A through Q-2026-04-20-ZZ-E.
- **Superseded by**: Forthcoming rigorous rewrites
  `TECT-Math49-rigorous.tex.txt`, `TECT-Math49b-rigorous.tex.txt`,
  `TECT-Math49c-rigorous.tex.txt`, `TECT-Math_EP-rigorous.tex.txt`,
  `TECT-Math_IR_Bound-rigorous.tex.txt`, each to be subjected to a
  second devil's-advocate pass before any closure label is
  reinstated.
- **Lesson preserved**: Producing a PRL-formatted LaTeX note whose
  statement matches a closure target is not evidence of closure.
  An independent pass — ideally an adversarial one — must check
  dimensions, arithmetic, operator choice, and the
  definition-vs.-derivation distinction before any pillar label is
  promoted from SCAFFOLD.

---

## Governance

- **Append-only**. No entry is ever edited in place. Corrections,
  if needed, are added as a new entry referencing the original.
- **Cross-referenced**. Every `F` / `R` / `D` entry cites the
  superseding theory tag, code version, or replacement entry. A
  dangling entry with no successor is itself a flag that the
  project owes a theoretical or numerical response.
- **Mirrored at milestones**. When a new theory tag is minted, the
  associated `CHANGELOG.md` section includes a `### Retracted /
  dead-end` subsection listing any `F` / `R` / `D` entries
  attributed to that tag, linking here.
- **Canonical**. This file is the single source of truth for
  failure provenance. Public-facing failure narratives on the
  Website (when published) must link back here.

---

### F-2026-04-20-03 — Math49d-R3-rigorous-v2 physical identification FALSIFIED: the unique $\mathbb{Z}_6$-invariant piece of $\mathrm{Sym}^2 V_5$ is a Georgi–Machacek-like electroweak Higgs triplet $(1,3)_{+1}$, not three chiral fermion families

**Hypothesis under test (Math49d-R3-rigorous-v2, 2026-04-20)**: that the
three-dimensional $\mathbb{Z}_6$-invariant sub-representation
$\mathrm{Sym}^2 V_\beta \subset \mathrm{Sym}^2 V_5$ — arising as the
unique isotype with $\zeta$-character $+1$ — furnishes the three chiral
families of the Standard Model, realising Pillar 6 at the
geometric-count level.

**External critique (GPT peer review, 2026-04-20)**: $V_\beta$ is
identified as the electroweak doublet slot in the GUT decomposition
$V_5 = V_\alpha \oplus V_\beta$ with $V_\alpha = (3,1)_{-1/3}$ and
$V_\beta = (1,2)_{+1/2}$. Therefore $\mathrm{Sym}^2 V_\beta$ transforms
as $\mathrm{Sym}^2 (\text{doublet of }SU(2)_W)$, which is the
**triplet** $(1,3)_{+1}$. Identifying flavour families with a
gauge-triplet multiplet forces the three families to carry distinct
$SU(2)_W$ quantum numbers, violating the Standard-Model axiom that
flavour rotations commute with the gauge group.

**Independent confirmation (TECT internal audit,
`Docs/supplementary/Math49d_gauge_flavor_audit.py`, 2026-04-20)**:
$$
\mathrm{Sym}^2 V_5 = (6,1)_{-2/3} \;\opl