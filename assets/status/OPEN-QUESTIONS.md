# TECT Open Questions Ledger

**Binding from**: 2026-04-15
**Governed by**: `docs/policy/UPDATE_POLICY.md` §10
**Sister files**: `CHANGELOG.md` (proved), `NEGATIVE-RESULTS.md` (failed), this file (open).

Append-only ledger of currently-open theoretical conjectures and
numerical frontiers. An item is closed by either (a) proof → migrate
to `CHANGELOG.md` + `research-log.md` under a theory tag, or
(b) disproof → migrate to `NEGATIVE-RESULTS.md` as an `F` / `R` /
`D` entry. Closure removes the item from the active section of this
file but preserves the entry under `## Archive` with its resolution.

## Schema

Each entry carries **seven fields**:

1. **Tag** `Q-<YYYY-MM-DD>-<seq>`
2. **Statement** — the open claim in formal language, with LaTeX.
3. **Predicted by** — Math-note + section reference.
4. **Why open** — what evidence is missing.
5. **Falsification criterion** (strongly recommended) — a pre-registered numerical or logical test whose failure forces the item into `NEGATIVE-RESULTS.md`.
6. **Owner** — the module / note responsible for closure.
7. **Last reviewed** / **Review by** — calendar dates governing cadence. Default cadence is 30 days; longer cadences must be justified in the entry.

An entry missing any field is incomplete and must be fixed before
the next commit touching this file.

## Status transitions

```
  ACTIVE ──proof──▶ Archive (cites theory tag + CHANGELOG section)
         ──disproof─▶ Archive (cites NEGATIVE-RESULTS F-/R-/D- tag)
         ──reformulated─▶ new ACTIVE entry (old goes to Archive
                           citing the replacement)
```

A reformulation is not a closure; the superseded entry must be
archived with the replacement's tag, and the replacement gains an
"Origin" line citing the original.

## Review cadence

- The table of contents of the `## Active` section is scanned at
  every `§7 full-repo audit` (UPDATE_POLICY.md).
- An item whose `Review by` date has passed without update is
  flagged in the audit report as **overdue**. Overdue items do
  not automatically close but become a priority in the next work
  session.
- A 30-day default cadence applies unless the entry carries an
  explicit longer `Review by` window (e.g. for items awaiting a
  single long numerical run).

---

## Active

### Q-2026-04-24-P11-symmetry-broken-seed — Symmetry-broken BCC seed for Math55 deep-endpoint convergence — [OPEN 2026-04-24, paired with Math82-Addendum-D PARTIAL Phase Z verdict]

- **Stage**: 1, Pillar 11 ($\Lambda$ cosmological constant) numerical-anchor sub-task. Mainline note: `Docs/math/TECT-Math82-Addendum-D-Phase-Z-result-PARTIAL.tex.txt`.
- **Origin**: Math82-Addendum-D (2026-04-24) Phase Z run revealed that the maximally-symmetric 6-cosine BCC analytic seed is a SADDLE point of the Brazovskii functional, not a local minimum. Phase 2 Lanczos signal: $\lambda_{\min}(\mu^2 = -0.1) = -0.063$ and $\lambda_{\min}(\mu^2 = -0.5) = -0.463$ at warm-started Newton-converged $\Psi^*$. The 23 unstable Hessian directions correspond to symmetry-breaking directions toward the 24 distinct BCC ground-state variants.
- **Statement**: construct a SYMMETRY-BROKEN BCC analytic seed inside the basin of one of the 24 BCC ground-state variants (Math82-Addendum-D §4 options) and re-run the continuation, achieving 5/5 converged points with $\lambda_{\min} > 0$ at all interior points (true BCC minimum, not saddle).
- **Why open**: symmetric seed produces saddle (proved Math82-Addendum-D Theorem `thm:saddle`); deep-endpoint $\mu^2 = -1.0$ fails catastrophically due to indefinite Hessian inherited from saddle warm-start; Math55 deep-endpoint anchor for Pillar 11 still pending.
- **Falsification criterion (pre-registered)**: any of the following:
  1. No symmetry-broken BCC ansatz converges to a stable minimum at $\mu^2 = -1.0$ within `--max-newton 12`.
  2. Even with symmetry-broken seed, $\lambda_{\min}(\mu^2 = -1.0) < 0$ persists.
  3. The natural Brazovskii ground state at $\mu^2 = -1.0$ is genuinely a saddle of the discretised functional (would indicate a fundamental discretisation bias in the $N=32$ BCC commensurate box).
  Either outcome demands re-evaluation of the BCC condensate existence claim at the discrete level.
- **Method (4 options enumerated in Math82-Addendum-D §4)**:
  1. Option A: 4-cosine subset (e.g., $\{\mathbf{q}_1, \mathbf{q}_3, \mathbf{q}_5, \mathbf{q}_6\}$) — elongated BCC variant, breaks $O_h$ to subgroup of order $\le 8$.
  2. Option B: random phase shifts $\theta_j \in [0, 2\pi)$ on each wave-vector — generic $O_h$ breaking.
  3. Option C: perturb symmetric seed along the Phase 2 Lanczos lowest negative eigenvector — directional descent into nearest minimum.
  4. Option D (orthogonal): insert intermediate $\mu^2$ values $\{-0.7, -0.85\}$ between Point 4 ($\mu^2 = -0.5$) and Point 5 ($\mu^2 = -1.0$).
- **Recommendation**: combine Option A (clean symmetry-broken seed) with Option D (smaller $\mu^2$ steps near deep endpoint).
- **Owner**: TECT collaboration (Pillar 11 numerical-anchor sub-task). Primary executor: extend `Codes/pde/bcc_analytic_seed.py` with `--mode subset_4cosine` etc.; create Math82-Addendum-E follow-up note.
- **Task**: assigned `#93 — Symmetry-broken BCC seed for Math55 deep-endpoint`.
- **Closure consequence**: success → Pillar 11 receives missing deep-endpoint numerical anchor; status can advance from `NEAR-CLOSURE` toward closure (independently requires Math58-v6 Dirac-sector tightening = Math58-v7 separate pending).
- **Last reviewed**: 2026-04-24.
- **Review by**: 2026-05-24.

---

### Q-2026-04-24-P6-Q6b-PS-two-step — Pati-Salam two-step RGE with TECT BCC-defect $\beta$-function content — [OPEN 2026-04-24, paired with Math77-Q6b-Addendum-A FALSIFICATION of pure-SM-1-loop baseline]

- **Stage**: 1, Pillar 6 (Generations / SM embedding) Q6b sub-task. Mainline note: `Docs/math/TECT-Math77-Q6b-Addendum-A-RGE-extraction.tex.txt`.
- **Origin**: Math77-Q6b-Addendum-A (2026-04-24) FALSIFIES the pure-SM 1-loop unification baseline: pairwise meeting scales span ~4 orders of magnitude, $M_{\mathrm{GUT}}^{\mathrm{geom}} \approx 6.4\times 10^{14}$ GeV is below the proton-decay safety threshold. The Q6b conjecture as-stated ("$M_{\mathrm{GUT}} \sim 10^{16}$ GeV from gauge unification") is salvageable only via TECT-natural Pati-Salam intermediate breaking with explicit BCC-defect $\beta$-function content.
- **Statement**: Construct the Pati-Salam two-step RGE
$$M_Z \xrightarrow{\text{SM + BCC-defect content}} M_{\mathrm{PS}} \xrightarrow{G_{\mathrm{PS}} = \mathrm{SU}(4)_C \times \mathrm{SU}(2)_L \times \mathrm{SU}(2)_R\text{ + BCC-defect content}} M_{\mathrm{GUT}}$$
and find $(M_{\mathrm{PS}}, M_{\mathrm{GUT}})$ such that all three SM gauge couplings $\alpha_1, \alpha_2, \alpha_3$ align at $M_{\mathrm{GUT}}$ AND $M_{\mathrm{GUT}}$ exceeds the Super-K proton-decay safety threshold $\sim 4 \times 10^{15}$ GeV.
- **Why open**: pure-SM baseline established (Math77-Q6b-Addendum-A). The Pati-Salam $\beta$-function coefficients $(b_4, b_{2L}, b_{2R})$ above $M_{\mathrm{PS}}$ are textbook; the BCC-defect contribution to the SM $\beta$-functions $(b_1, b_2, b_3)$ between $M_Z$ and $M_{\mathrm{PS}}$ requires explicit derivation from the BCC defect-state spectrum (this is the TECT-specific ingredient).
- **Required ingredients (pre-registered)**:
  1. Choose $M_{\mathrm{PS}}$ as a function of TECT parameters (BCC lattice spacing, $\mu^2_{\mathrm{target}}$, condensate amplitude).
  2. Compute BCC-defect $\Delta b_i$ contributions to $(b_1, b_2, b_3)$ between $M_Z$ and $M_{\mathrm{PS}}$.
  3. Compute $\Delta b$ contributions to $(b_4, b_{2L}, b_{2R})$ between $M_{\mathrm{PS}}$ and $M_{\mathrm{GUT}}$.
  4. Solve coupled RGE for $(M_{\mathrm{PS}}, M_{\mathrm{GUT}}, \alpha_{\mathrm{GUT}})$.
  5. Cross-check against $\tau_p > 1.6 \times 10^{34}$ yr.
- **Falsification criterion (pre-registered)**:
  1. No $(M_{\mathrm{PS}}, M_{\mathrm{GUT}})$ exists making all three SM couplings align.
  2. The required BCC-defect $\Delta b_i$ are physically unreasonable (e.g. $|\Delta b_i| > 10$).
  3. Even with alignment, $M_{\mathrm{GUT}} < 10^{15}$ GeV (proton-decay violation).
  Either outcome confirms Q6b conjecture is fundamentally false in TECT and Pillar 6 Q6b sub-task pivots to a different mechanism.
- **Method**: extend `Codes/supplementary/Math77_Q6b_RGE_integration.py` to handle two-step running; add BCC-defect spectrum module derived from TECT first-shell amplitude content.
- **Owner**: TECT collaboration (Pillar 6 Q6b-2). Primary executor: theorem + numerical follow-up (Math77-Q6b-Addendum-B candidate).
- **Task**: assigned `#92 — Q6b Pati-Salam two-step RGE with BCC-defect content`.
- **Closure consequence**: Q6b fully closed → Pillar 6 closure pending Q6a-equivariance + Q6c + Q6d.
- **Last reviewed**: 2026-04-24.
- **Review by**: 2026-05-24.

---

### Q-2026-04-24-P6-Q6a-equivariance — BCC defect-bundle equivariance with the $\mathrm{SO}(10)$-vector representation — [**RESOLVED-THEOREM 2026-04-24** — paired with Math80-Addendum-A and Math80-Addendum-B]

**Resolution (2026-04-24, same day as Addendum-A)**: Math80-Addendum-B (Topological Realisation, 2026-04-24) proves the equivariant $\mathrm{SO}(10)$ action on $\pi_1(M_{\mathrm{BCC}})$ with orbit space $\mathbf{10}_{\mathrm{vec}}$ via principal $T^{11}$-fibration analysis, per-charge-class moduli decomposition, and cross-check against Addendum-A. **Q6a is FULLY CLOSED at THEOREM level** (both Lie-algebraic and topological halves proved). Closure evidence: `Docs/math/TECT-Math80-Addendum-A-Q6a-10-moduli-theorem.tex.txt` + `Docs/math/TECT-Math80-Addendum-B-Q6a-equivariance-theorem.tex.txt`.

**Original statement (now proved):**
- **Stage**: 1, Pillar 6 (Generations / SM embedding) Q6a sub-task.
- **Origin**: Math80-Addendum-A (2026-04-24) closed the Lie-algebraic half via Strategy 2 + 3 combined ($\dim \mathfrak{g}_{\mathrm{PS}}/\mathfrak{g}_{\mathrm{SM}} + \dim U(1)_{B-L} = 9 + 1 = 10 = \dim \mathbf{10}_{\mathrm{vec}}$). The topological-equivariance half was recorded here and is now closed by Addendum-B.
- **Statement (PROVED)**: The BCC ground-state manifold $M_{\mathrm{BCC}}$ admits a $\pi_1$-equivariant action of $\mathrm{SO}(10)$ whose orbit space is exactly the $\mathbf{10}_{\mathrm{vec}}$ representation identified in Math80-Addendum-A, realising the higher-charge defect-bundle moduli under the standard BCC defect topology.
- **Proof method**: Principal $T^{11}$-fibration on $M_{\mathrm{BCC}}$ + equivariant lifting of $\mathrm{SO}(10)$ action + per-charge-class moduli analysis + dimension matching + cross-check against Math80-Addendum-A.
- **Closure consequence**: Q6a fully closed ✓. Pillar 6 remains PARTIAL-ADVANCED because Q6b, Q6c, Q6d are still open.
- **Resolved by**: Task #91 (2026-04-24, combined Addendum-A + Addendum-B).
- **Ledger update**: Moved from Active to Archive.

---

### Q-2026-04-24-P10-R5-residual-matching — Universal completion-scale extraction via residual matching between exact classical TECT and observed physics — [RESOLVED-NEGATIVE 2026-04-24, R5 first-iteration FAILS pre-registered failure criterion]

**Resolution (2026-04-24, same day)**: First-iteration numerical extraction (`Codes/supplementary/Math79_R5_chi_star_extraction.py`) yields
$$
\rho_\Lambda \approx 3.4\times 10^{-44}, \quad \rho_{\mathrm{Cas}} \approx -8.7\times 10^{-7}, \quad \rho_{g{-}2} \approx +8.0\times 10^{+7},
$$
all far outside both the success window $[0.5, 2.0]$ and the conservative failure window $[0.1, 10]$. Pre-registered failure criterion (Math79 §7 Theorem on R5 failure) triggered. **Pillar 10 = OPEN-NEGATIVE REFINED is REINFORCED.** Three failure modes diagnostically informative: $\Lambda$ residual ~44 orders too small (consistent with the standard cosmological-constant problem; $\Lambda$ physics is in a different universality class than electron-Compton); Casimir residual ~7 orders too small with opposite sign (dimensional ansatz under-models boundary-condition physics); $g{-}2$ residual ~7 orders too large (QED loop structure exceeds naive defect-vertex estimate). Recorded in `Docs/math/TECT-Math79-Addendum-A-R5-first-iteration-FAILURE.tex.txt`. Refined-$C_i$ second iteration (Math79-Addendum-B) is theoretically possible but the 44-order gap on $\Lambda$ makes universality recovery considered unlikely. Q closed by negative verdict.

#### [Original framework statement (OPEN 2026-04-24, archived after same-day resolution)]


- **Stage**: 1, Pillar 10 ($\hbar$ origin) supplementary route. Framework note: `Docs/math/TECT-Math79-Pillar10-R5-residual-matching-framework.tex.txt`.
- **Origin**: User suggestion 2026-04-24 (R4 dimensional-monomial-enumeration form), reframed in the same session into the present R5 residual-matching form per reviewer feedback. The R5 reformulation drops the unrealistic "derive $\hbar$ from nothing" ambition and asks instead whether a single external completion scale explains multiple residuals.
- **Statement**: Define the dimensionless completion parameter
$$
\chi_* \;:=\; \frac{\hbar}{S_{\mathrm{BCC}}^{(e)}}, \qquad S_{\mathrm{BCC}}^{(e)} := m_e\,c\,a_{\mathrm{BCC}}.
$$
For each admissible residual channel $i$, with classical TECT prediction $Q_i^{\mathrm{TECT,cl}}$ and observation $Q_i^{\mathrm{obs}}$, define
$$
\delta Q_i := Q_i^{\mathrm{obs}} - Q_i^{\mathrm{TECT,cl}}, \qquad \chi_*^{(i)} := \delta Q_i / C_i,
$$
where $C_i$ is the classical-TECT coefficient (no $\hbar$). Test whether $\chi_*^{(i)}$ is approximately the same constant across the four canonical channels:
$$
\bigl\{\,\delta\Lambda,\;\;\delta F_{\mathrm{Casimir}},\;\;\delta\lambda_{\mathrm{Compton}},\;\;\delta a_e\,\bigr\}.
$$
- **Predicted by**: `TECT-Math79-Pillar10-R5-residual-matching-framework.tex.txt` (this commit).
- **Why open**: framework fixed; numerical extraction of $\chi_*^{(\Lambda)}, \chi_*^{(\mathrm{Cas})}, \chi_*^{(\mathrm{Comp})}, \chi_*^{(g{-}2)}$ pending. Supplementary script `Docs/supplementary/Math79_R5_chi_star_extraction.py` to be produced.
- **Pre-registered success criterion** (from Math79 §7 Theorem on R5 success):
$$
\rho_\Lambda := \chi_*^{(\Lambda)}/\chi_*^{(\mathrm{Comp})} \in [0.5,\,2.0], \quad \rho_{\mathrm{Cas}} := \chi_*^{(\mathrm{Cas})}/\chi_*^{(\mathrm{Comp})} \in [0.5,\,2.0], \quad \rho_{g{-}2} := \chi_*^{(g{-}2)}/\chi_*^{(\mathrm{Comp})} \in [0.5,\,2.0],
$$
with $\chi_*^{(\mathrm{Cas})}(d)$ furthermore $d$-independent across $d \in [10\,\mathrm{nm}, 10\,\mu\mathrm{m}]$.
- **Pre-registered failure criterion** (from Math79 §7 Theorem on R5 failure): at least one of $\rho_\Lambda, \rho_{\mathrm{Cas}}, \rho_{g{-}2}$ differs from unity by a factor of $10$ or more, OR $\chi_*^{(\mathrm{Cas})}(d)$ exhibits a power-law $d$-dependence. Either outcome reinforces `Pillar 10 = OPEN-NEGATIVE REFINED` (even phenomenological universality fails).
- **Honest scope statement** (binding):
$$
\boxed{\text{TECT does not derive }\hbar\text{ from pure classical first principles.}}
$$
$$
\boxed{\text{R5 only audits whether one external completion scale controls the gap between exact classical TECT and observed physics.}}
$$
- **Method**: (a) compute each $C_i$ from classical TECT alone (Math79 §§4–6); (b) extract $\chi_*^{(i)}$ for each channel using current best observational values; (c) test the four pre-registered ratios; (d) for R5-B, test $d$-independence over the experimental range.
- **Non-circularity audit**: every $C_i$ must be traced back to TECT-classical inputs $\{a_{\mathrm{BCC}}, q_0, \mu^2, \lambda, \gamma, Y, c, e, \varepsilon_0, \rho_{\mathrm{BCC}}\}$ — the fine-structure constant $\alpha = e^2/(4\pi\varepsilon_0\hbar c)$ must NOT appear inside any $C_i$.
- **Owner**: TECT collaboration (Pillar 10 supplementary). Primary executor: focused subagent / supplementary script.
- **Task**: assigned `#90 — Math79 R5 numerical extraction`.
- **Last reviewed**: 2026-04-24.
- **Review by**: 2026-05-24 (30-day cadence).
- **Supersession status of prior R4 entry**: the dimensional-monomial enumeration form of R4 (`Q-2026-04-24-P10-R4-BCC-stiffness-cosmic-wave`) is reframed by this entry. The R4 falsification routes (numerical / circularity) are absorbed as edge cases of the R5 non-circularity audit. R4 is closed-as-reframed; the original R4 entry is archived below for historical record.

#### [Archived — R4 reframed into R5, 2026-04-24]
The original R4 entry asked whether $\hbar = \mathcal{F}(a, \omega'(q_0), H_0, c)$ could be matched by dimensional enumeration. This was correct in spirit but methodologically too narrow: dimensional matching alone does not constitute a physically meaningful derivation, and the natural cleanest statement of the problem (per reviewer audit) is the residual-matching form R5 above. R4's two falsification rules are subsumed by R5's pre-registered success/failure criteria.

---

### Q-2026-04-21-S2A — Math60-A meta-consistency of the 11-pillar hypothesis lists on a single background model $\mathcal{M}_0$ — [OPEN 2026-04-21]

- **Stage**: 2 (Global Closure Theorem sub-component A). Parent specification: `Docs/math/TECT-Math60-TOE-Global-Closure-Spec.tex.txt`.
- **Statement**: Prove that the hypothesis lists $\{H_i\}_{i=1}^{11}$ of the eleven Stage-1 pillars are mutually compatible in the sense that there exists a single background model $\mathcal{M}_0 = \bigl(\mathcal{F}[\Psi];\ (\mu^2,\lambda,\gamma,q_0);\ O_h\text{-lattice}\bigr)$ in which every $H_i$ is simultaneously satisfied. The compatibility set to check: (a) uniform kinetic convention $\omega(k)=r+Zk^2+Yk^4$ across all pillars; (b) continuum-limit compatibility of every pillar that uses the lattice; (c) the gauge group used in pillar $i$ does not contradict the stabilizer chain $\mathrm{Stab}_{SU(5)}\,\mathrm{Gr}(2,5)=G_{\mathrm{SM}}$ used in pillar $j$ for any pair $(i,j)$; (d) a single order-parameter scale $\varphi_0$ such that the Pillar-1 mass gate $\mathrm{RMS}|\Psi|/\varphi_0\ge 0.3$ is consistent with the Pillar-9 weak-field expansion $\varepsilon^2\ll 1$.
- **Predicted by**: Math60 §Math60-A (Theorem + Hypothesis $H_A$ + gate $G_A$).
- **Why open**: not attempted. The compatibility check is diagnostic — all Stage-1 pillars currently use the same Brazovskii locked point, the same kinetic convention (enforced at runtime by `_check_kinetic_convention`), and the same BCC lattice, so the conjecture is that the answer is affirmative. However, no diagram-by-diagram audit has been filed.
- **Falsification criterion**: any ordered pair $(i,j)$ for which $H_i$ and $H_j$ cannot be satisfied on the same $\mathcal{M}_0$ (e.g.\ $H_i$ requires $q_0=0.3138$ while $H_j$ requires $q_0=0.6802$) falsifies Math60-A. The Math57-v2 re-baseline (Task #67) demonstrates the type of repair needed when such a mismatch is found.
- **Owner**: TECT collaboration (meta-structural).
- **Task**: #81.
- **Last reviewed**: 2026-04-21.
- **Review by**: 2026-06-21.

---

### Q-2026-04-21-S2B — Math60-B parameter compression $n_{\mathrm{free}}\le 1$ from axiom A0 — [OPEN 2026-04-21]

- **Stage**: 2 (Global Closure Theorem sub-component B). Parent: Math60.
- **Statement**: Construct an explicit map $\Xi:\mathrm{A0}\to(\mu^2,\lambda,\gamma,M_X,\alpha_X)$ that reduces the count of externally-imposed free parameters to $n_{\mathrm{free}}\le 1$. Partial closure at $n_{\mathrm{free}}=1$ is acceptable if the single residual parameter is a dimensionless ratio whose value is predicted by a further sub-programme.
- **Subsumes**: `Q-2026-04-15-04` (RG derivation of $(\mu^2,\lambda,\gamma)$), `Q-2026-04-15-06` ($M_X$ origin), `Q-2026-04-15-07` ($\alpha_X$ origin).
- **Why open**: three boundary inputs — $q_0$ (measured), $M_X=2.0$ (free), $\alpha_X=0.3$ (free) — plus the Brazovskii triplet $(\mu^2,\lambda,\gamma)$ are currently matched to numerical BCC observables rather than derived. A first-principles derivation from A0 + a single RG fixed-point condition is missing.
- **Falsification criterion**: exhibit a fifth independent Stage-1 numerical observable whose predicted value under any candidate $\Xi$ deviates from measurement by more than $10\sigma$.
- **Owner**: TECT collaboration.
- **Task**: #82.
- **Last reviewed**: 2026-04-21.
- **Review by**: 2026-07-21.

---

### Q-2026-04-21-S2C — Math60-C quantization closure (measure or algebraic-QFT) — [OPEN 2026-04-21]

- **Stage**: 2 (Global Closure Theorem sub-component C). Parent: Math60. Subsumes Pillar 10 ($\hbar$-origin).
- **Statement**: Construct a quantization $(\mathscr{H},\mathcal{O},U_t)$ of the BCC condensate theory with non-trivial vacuum, such that the emergent Minkowski Poincar\'e group acts by bounded unitaries $U_t$ on $\mathscr{H}$. Closure requires: (a) a positive measure on the continuum-limit field configurations; (b) reflection positivity or Wightman positivity in the emergent Minkowski sector; (c) a mass gap $m^*>0$ (to be supplied by Pillar 1 after the v2.4 Math55 continuation closes); (d) compatibility with a Stage-1 Pillar-10 statement $\hbar=\hbar(\mathrm{A0})$.
- **Why open**: not attempted. Currently Pillar 10 is marked `OPEN-NEGATIVE` in the Stage-1 scoreboard (Math59 higher-form obstruction as conjecture, four routes closed). The Stage-2 Math60-C slot unifies the quantization construction and the $\hbar$-origin question into a single theorem.
- **Falsification criterion**: failure of Osterwalder–Schrader reflection positivity on any candidate continuum measure; non-existence of a unitary Poincar\'e representation on any candidate $\mathscr{H}$.
- **Owner**: TECT collaboration.
- **Task**: #83.
- **Last reviewed**: 2026-04-21.
- **Review by**: 2026-10-21.

---

### Q-2026-04-21-S2D — Math60-D phenomenology closure / observable map $\Phi$ in SI units — [OPEN 2026-04-21]

- **Stage**: 2 (Global Closure Theorem sub-component D). Parent: Math60.
- **Statement**: Build an explicit map $\Phi:\{\text{TECT invariants}\}\to\{\text{SM/GR observables in SI units}\}$ such that each of the charged-lepton masses, $G_N$, $\alpha_{\mathrm{em}}$, $\alpha_s$, and the CKM/PMNS entries is either (i) the image under $\Phi$ of a TECT invariant, or (ii) explicitly flagged as an external input with a written justification. Required sub-items: (a) C2 graviton normalisation extractor ($Z_h\to 1/2$) run on a v2.4-certified BCC condensate; (b) C3 gauge coupling extractor run; (c) a Yukawa extractor once the Pillar-6 replacement bundle is identified; (d) a fixed $q_0$-in-$\mathrm{fm}^{-1}$ setting so that $m^*$ at the Brazovskii-locked parameters maps to MeV.
- **Why open**: the C2 and C3 extractors exist but have not been run on a certified BCC condensate; the Yukawa extractor requires Pillar-6 replacement-bundle closure (currently falsified through $k\le 5$ by `F-2026-04-21-R5W2`); no unit-conversion factor has been fixed.
- **Falsification criterion**: any charged-lepton mass ratio predicted by $\Phi$ deviating from PDG by more than $10\sigma$ at the pre-registered precision.
- **Owner**: TECT collaboration.
- **Task**: #84.
- **Last reviewed**: 2026-04-21.
- **Review by**: 2026-08-21.

---

### Q-2026-04-21-S2E — Math60-E falsifiability package ($|\mathcal{P}|\ge 3$ pre-registered predictions) — [OPEN 2026-04-21]

- **Stage**: 2 (Global Closure Theorem sub-component E). Parent: Math60.
- **Statement**: Pre-register a falsifiability package $\mathcal{P}=\{\pi_1,\ldots,\pi_k\}$ with $k\ge 3$, each $\pi_j$ (i) computed from Stage-1 content alone, (ii) not imposed as theory input, (iii) testable at current or near-future precision, with a written falsification threshold. Current candidates:
  - $\pi_1$: Lorentz-violation parameter $|\kappa^{(c)}|\lesssim 10^{-38}$ (Pillar 8, Math_IR_Bound-v4).
  - $\pi_2$: Equivalence-principle parameter $|\eta_{\mathrm{EP}}|\lesssim 10^{-15}$ (Pillar 9, Math_EP-v3.1).
  - $\pi_3$: graviton normalisation $Z_h\to 1/2$ and TT-purity of the emergent $h_{\mu\nu}$ mode (Pillar 3, Math41/45/46c).
  - $\pi_4$ (pending): $\Lambda$ near-cancellation fraction (Pillar 11, Math58 + Math59).
- **Why open**: all candidate $\pi_j$ already exist as internal Stage-1 outputs, but none is pre-registered with an explicit experimental falsification threshold and a matching Open-Question entry carrying a dated review window.
- **Falsification criterion**: any $\pi_j$ measured to violate its threshold at the stated confidence level falsifies that $\pi_j$ and, if the package cardinality drops below 3, falsifies Math60-E.
- **Owner**: TECT collaboration.
- **Task**: #85.
- **Last reviewed**: 2026-04-21.
- **Review by**: 2026-06-21.

---

### Q-2026-04-21-S3 — Stage-3 phenomenological TOE qualification ledger — [OPEN 2026-04-21]

- **Stage**: 3 (external phenomenological qualification). Parent: Math60 §Stage 3.
- **Statement**: Open and maintain an external-qualification ledger $S_3 = S_3^{(\mathrm{reproduce})}\wedge S_3^{(\mathrm{predict})}\wedge S_3^{(\mathrm{survive})}$.
  - $S_3^{(\mathrm{reproduce})}$: at least one independent reproduction of a Stage-1/Stage-2 numerical certificate (candidate targets: Theorem-v4-2 $J_1$ interval at $N=256$; Math56 trivial-vacuum audit; Math49d-R5 wave-2 LR census).
  - $S_3^{(\mathrm{predict})}$: at least one $\pi_j\in\mathcal{P}$ (from Stage-2-E) matched by experiment at its pre-registered precision.
  - $S_3^{(\mathrm{survive})}$: at least one $\pi_k\in\mathcal{P}$ with experimental window open for $\ge 1$ year without falsification.
- **Why open**: blocked upstream by Stage-2-E (no pre-registered package yet). Stage-3 activity begins only after Stage-2-E produces a pre-registered package.
- **Falsification criterion**: any $\pi_k$ falsified during its open window invalidates $S_3^{(\mathrm{survive})}$ for that $\pi_k$; closure still requires at least one surviving $\pi$.
- **Owner**: TECT collaboration (external-facing).
- **Task**: #86.
- **Last reviewed**: 2026-04-21.
- **Review by**: 2026-10-21.

---

### Q-2026-04-20-X5 — [RESOLVED 2026-04-20] $\phi_0$-convention discrepancy between Math37-AddA §A.3 and Math56-Addendum §F

- **Statement**: Math37-AddA §A.3 boxes the first-order BCC amplitude as
  $\phi_{0,\,\text{corr}}^{2} = -4\lambda/(15\gamma)$ (numerical value $0.0708$
  at $(\lambda,\gamma)=(-0.43,1.62)$, giving $\phi_0=0.266$). A direct
  re-derivation from the simultaneous conditions
  $\mathcal{F}(\phi_0)=\mathcal{F}(0)=0$ and $\mathcal{F}'(\phi_0)=0$ on the
  reduced potential $\mathcal{F}(\phi) = \mu^2\phi^2 + \lambda\phi^4 + (5/2)\gamma\phi^6$
  (Math56-Addendum eqs.~(i)–(ii), §F) yields
  $\phi_0^2 = -\lambda/(5\gamma)$, numerically $0.0531$, giving $\phi_0=0.2305$.
  The two differ by a factor $4/3$ in $\phi_0^2$ ($\approx 1.154$ in $\phi_0$).
- **Predicted by**: Math56-Addendum §F (re-derivation); Math37-AddA §A.3
  (boxed formula).
- **Why open**: both algebraic paths use the same reduced potential and both
  claim Brazovskii first-order locking, but produce different answers. Either
  (a) an algebraic slip is present in Math37-AddA §A.3 between eq.~(5708) and
  the boxed eq.~(5711), or (b) the two derivations correspond to different
  locking conditions (e.g. $\mathcal{F}''(\phi_0)=0$ vs
  $\mathcal{F}'(\phi_0)=\mathcal{F}(\phi_0)=0$), in which case the Math37-AddA
  label is mis-stated.
- **Falsification criterion**: Symbolic re-derivation in SymPy from
  $\mathcal{F}$ as written in Math37-AddA eq.~(5701–5706). If SymPy returns
  $\phi_0^2=-\lambda/(5\gamma)$, Math37-AddA §A.3 must be patched to the
  smaller value. If it returns $-4\lambda/(15\gamma)$, Math56-Addendum §F
  must be patched and the derivation explained.
- **Owner**: Math37-AddA §A.3 authors; Math56-Addendum §F as challenger.
- **Impact if the corrected value is $\phi_0=0.2305$**: The $\mathcal{M}^2_{\text{corr}}$
  number in Math37-AddA eq.~(5737) is recomputed; $m^{*2}_{\text{analytic,corr}}$
  drops from $9.005$. The v2.4 code patch (Docs/status/v2p4-patch-plan.md §3)
  must use the re-derived value.
- **Resolution (2026-04-20)**: SymPy audit
  (`Docs/supplementary/v24_threshold_sympy_check.py`, scenarios A–C)
  confirms that the simultaneous first-order-lock conditions
  $\mathcal{F}(\phi_0)=0$ and $\mathcal{F}'(\phi_0)=0$ yield
  $\phi_0^2=-\lambda/(5\gamma)=0.0531$ at
  $\mu^2_c=\lambda^2/(10\gamma)=0.01141$, whereas the single
  condition $\mathcal{F}'(\phi)=0$ evaluated at $\mu^2=0$ yields
  the Math37-AddA §A.3 boxed value $\phi_0^2=-4\lambda/(15\gamma)=0.0708$.
  The Math37-AddA §A.3 *label* ("first-order Brazovskii lock")
  is therefore wrong: the boxed value corresponds to the $\mu^2=0$
  single-extremum root, not the simultaneous lock. Math56-Addendum
  §F and every v2.4 threshold use $\phi_0^2=-\lambda/(5\gamma)$.
- **Follow-up**: Math37-AddA §A.3 requires an erratum (non-blocking
  for v2.4); the numerical $\mathcal{M}^2_{\text{corr}}$ in
  Math37-AddA eq.~(5737) is recomputed in Math56-Addendum §B.
- **Last reviewed**: 2026-04-20 | **Resolved at**: 2026-04-20.

---

### Q-2026-04-20-X6 — [OPEN 2026-04-20] Quantify the Phase-0 cushion $\delta$ from measured RMS fluctuation

- **Statement**: Math56-Addendum Theorem 2 sets the Phase-0 threshold
  as $G_0^{\text{op}} = \tfrac12(1+\alpha_{\text{sep}}) + \delta$
  with $\delta=0.05$. The cushion is justified verbally as absorbing
  the $O(1/N)$ RMS fluctuation of $\|\Psi\|_{\mathrm{RMS}}/\varphi_+$
  at $N=32$, but no quantitative bound exists. A converged Math55
  continuation endpoint at $\mu^2_{\text{target}}=5\times 10^{-3}$
  will provide the missing variance statistic.
- **Predicted by**: v2p4 adversarial audit 2026-04-20 §1.3 ([M-1]).
- **Why open**: the threshold currently over- or under-fits the
  finite-grid budget with no data-driven anchor.
- **Falsification criterion**: measure
  $\sigma_V \equiv \sqrt{\langle V^2\rangle-\langle V\rangle^2}$ on
  a converged BCC Math55 endpoint at $N\in\{32,64,128\}$; if
  $\sigma_V(N{=}32)/\langle V\rangle > 0.10$ the 5% cushion is
  insufficient and must be raised to
  $\delta = 2\sigma_V(N{=}32)/\langle V\rangle$.
- **Owner**: `PDE/v24_thresholds.py` (constant `V24_G0_CUSHION`) and
  Math56-Addendum §B.
- **Impact**: tightens (or loosens) the operational Phase-0 gate;
  data-driven rather than heuristic.
- **Last reviewed**: 2026-04-20 | **Review by**: after first Math55
  $N=32$ continuation endpoint (target 2026-05-04).

---

### Q-2026-04-20-X7 — [OPEN 2026-04-20] First-principles derivation of the Class-II abort factor $\kappa$

- **Statement**: Math56-Addendum Theorem 3 sets
  $\rho_* = \kappa\,\varphi_+^2$ with $\kappa = 10^{-3}$. The factor
  absorbs both the Newton residual tolerance and the cell volume
  $\Delta x^3 = (L/N)^3$, but is asserted dimensionally rather than
  derived. The v2.4 code hard-codes it as `V24_RHO_STAR_FACTOR`.
- **Predicted by**: v2p4 adversarial audit 2026-04-20 §1.4 ([M-2]).
- **Why open**: the abort floor is traceable to solver settings
  (`tol_newton`, $N$, $L$) in principle but not in the current
  theorem statement.
- **Falsification criterion**: derive
  $\kappa \equiv f(\text{tol}_{\text{Newton}},\Delta x^3,\varphi_+^2)$
  so that the product $\rho_* = \kappa\varphi_+^2$ is the largest
  value for which the regularised Class-II quotient
  $q_\alpha = m_\alpha/(\rho+\epsilon)$ does not amplify the
  Newton-step residual beyond $10\times$ its input. If the derivation
  yields $\kappa\neq 10^{-3}$ by more than a factor 3, update
  `V24_RHO_STAR_FACTOR`.
- **Owner**: `PDE/v24_thresholds.py` and Math56-Addendum §C.
- **Impact**: makes the Class-II floor a function of solver
  configuration rather than a fixed constant; closes the remaining
  dimensional-analysis gap in Theorem 3.
- **Last reviewed**: 2026-04-20 | **Review by**: before any published
  $m^{*2}$ value (target 2026-05-11).

---

### Q-2026-04-20-Q-HESS-JUMP — [RESOLVED 2026-04-20] Projected-Lanczos eigenvalue exhibits a $\times 17$ jump between $N=32$ and $N=64$ in the Newton-Krylov Phase-2 pipeline

- **Resolution** (2026-04-20): Resolved via Math56 wavenumber-stratified decomposition + empirical audit (`PDE/hess_jump_audit.py`). The three-candidate hypothesis (eigenvector-family migration / projector normalisation / accidental N=32 near-degeneracy) was **all three refuted by direct measurement**. The actual root cause is:
  (i) **Trivial-vacuum collapse on both grids**: $\|\Psi^*\|_{\text{RMS}}/\phi_0 = 3.43\times 10^{-6}$ at N=32 and $2.64\times 10^{-6}$ at N=64 (six orders of magnitude below the BCC seed $\phi_0 = 0.266$).
  (ii) **Class-II backend singularity**: the quotient $q_\alpha = m_\alpha/(\rho + 10^{-12})$ in `_classII_effective_term_t` is ill-conditioned when $\rho \sim 10^{-10}$, injecting spurious order-$N$-dependent eigenvalues into the Hessian.
- **Resolution key**: `MATH55_CONTINUATION_REQUIRED` (see Math56 Remark~\ref{rem:v2p4}).
- **Both N=32 and N=64 Phase-2 values are retracted**; Pillar 1 demoted to SCAFFOLD.
- **Next steps** (tracked as implementation items under Math56 §7): (1) patch `_classII_effective_term_t` with a guarded quotient; (2) insert Phase-0 gate G0 (`RMS|Psi|/phi_0 >= 0.3`); (3) re-run via Math55 continuation from $\mu^2=-1$; (4) apply Phase-2.5 gate (G1+G2+G3) to the valid BCC solutions at two grids.
- **Evidence**: `phase2p5_gate_N32_N64_2026-04-20.json`, `phase2p5_gate_summary.md`, Math56-HessJump-audit §5.
- **Closed at**: 2026-04-20.

---

### Q-2026-04-20-Q-HESS-JUMP-ORIGINAL-TEXT — (archival, retained for audit trail)

- **Statement**: the two-grid Phase-2 data
  $\{m^{*2}_{\text{num}}(N)\}_{N\in\{32,64\}} = \{3.1485, 54.07\}$
  is *not* compatible with the leading-order continuum expansion
  $m^{*2}(h^{2}) = m^{*2}_{0} + c\,h^{2} + \mathcal{O}(h^{4})$ in the
  lattice spacing $h(N) = 2\pi L/N$. Either the first projected
  Lanczos eigenvector migrates to a different mode family between the
  two grids, or the merit/projector carries a latent $N$-dependence
  that has not been absorbed, or the $N=32$ value is an accidental
  near-degeneracy lifted by the finer grid. Which of the three?
- **Predicted by**: Newton-Krylov proof protocol (Math51–53) and the
  Phase-4 linear extrapolation template. The $N=32$ Phase-2 result was
  logged on 2026-04-16; the $N=64$ result that broke the extrapolation
  was logged on 2026-04-20 (result tag
  `R-2026-04-20-02-newton-krylov-N64-2026-04-20`; failure entry
  `F-2026-04-20-05`).
- **Why open**: only two grids exist; the test that distinguishes
  among the three explanations (eigenvector-family migration,
  projector normalisation, accidental degeneracy) requires an
  eigenvector-overlap audit that has not been run. Phase 4 is
  therefore BLOCKED.
- **Falsification criterion**: dump the top-8 Lanczos eigenpairs at
  both $N=32$ and $N=64$; restrict each eigenvector to the common BZ
  shell set; compute the overlap matrix
  $O_{ij} = \langle \psi_{i}^{(32)} | P_{\text{common}} | \psi_{j}^{(64)} \rangle$.
  (a) If $|O_{11}|^{2} \gtrsim 0.9$: the leading eigenvectors are a
  common family and the jump is either a projector artifact
  (explanation 2) or an accidental $N=32$ near-degeneracy
  (explanation 3); run the projector-audit test. (b) If the $N=32$
  leading eigenvector matches $\psi_{j}^{(64)}$ for some $j\geq 2$
  with $|O_{1j}|^{2}\gtrsim 0.9$: eigenvector-family migration
  (explanation 1) is confirmed, and the physical $m^{*2}_{\text{long}}$
  should be read from row $j$ of the $N=64$ spectrum rather than
  row 1. (c) If no eigenvector in either grid has overlap
  $\gtrsim 0.5$ with any eigenvector of the other: the finer grid
  has altered the eigenstructure so substantially that the two-grid
  protocol is unfit for purpose and an $N=128$ seed-continuation run
  from $N=64$ is required.
- **Owner**: `PDE/tect_newton_krylov.py` (Lanczos diagnostics) +
  `Docs/math/TECT-Math51–53-series` (Newton-Krylov proof protocol).
- **Last reviewed**: 2026-04-20.
- **Review by**: 2026-05-04 (14 days — the short cadence reflects
  that the continuum limit of Pillar 1 is blocked on this item).

---

### Q-2026-04-20-Q-GM-TRIPLET — Does the $(\mathbf{1},\mathbf{3})_{+1}$ weak-triplet isotype realise a physical Higgs-triplet in the TECT IR spectrum?

- **Statement**: The unique $\mathbb{Z}_6$-invariant isotype of
  $\mathrm{Sym}^2 V_5$ carries the SM quantum numbers of a Georgi–
  Machacek triplet $\chi = (\chi^{++}, \chi^{+}, \chi^{0})$. Is this
  multiplet physically realised as a scalar excitation in the TECT
  IR spectrum, with mass set by the BCC gap $\sim q_0^{-1}$, and
  what is its doubly-charged phenomenological signature?
- **Predicted by**: by-product of F-2026-04-20-03 analysis;
  `Math49d_gauge_flavor_audit.py`.
- **Why open**: the isotype is a geometric consequence of
  $\chi^{\mathbb{Z}_6}(\mathrm{Sym}^2 Q) = 3$; whether it corresponds
  to a propagating IR mode or to a pure constraint multiplet has
  not been tested. Distinct from Q-2026-04-20-PR1 (which concerns
  flavour count, not this secondary prediction).
- **Falsification criterion**: a converged $N=64$ BCC solution
  (Newton-Krylov v2.3) whose projected spectrum shows no resonance
  with the Z₂-centre $\zeta$-symmetric quantum numbers within
  $[0.1, 10]\cdot q_0$ falsifies the IR-realisation of this
  multiplet.
- **Owner**: Math56 (pending; Higgs-triplet extractor).
- **Last reviewed**: 2026-04-20 &nbsp;|&nbsp; **Review by**: 2026-06-20 (60-day, exploratory).

### Q-2026-04-15-01 — Step C numerical convergence to $m^{*2}_{\mathrm{num,corr}} \to 9.0 \pm \delta$

- **Statement**: Under the Brazovskii-locked config $(\mu^{2},\lambda,\gamma) = (0.26, -0.43, 1.62)$
  with $K_4 = 1$, $K_6 = 5/2$, $I_3 = 1/3$, $R_{\mathrm{patch}} = 45/16$, the
  numerical extractor output $m^{*2}_{\mathrm{num,corr}}$ after Step C
  convergence must match the analytic prediction $m^{*2}_{\mathrm{TECT}} \approx 9.005$
  within acceptance band $[1.8,\,45.0]$.
- **Predicted by**: Math37 Addendum A § closure; Math38 three-equation matching.
- **Why open**: Solver Patch A (v3.1) landed 2026-04-15; no production
  Brazovskii-regime run has been archived with manifest yet. User's
  first post-patch run pending.
- **Falsification criterion**: Persistent $\geq 5\times$ shortfall after
  converged Step C reverts to the GL hypothesis (re-opening
  F-2026-04-15-01). This is a hard, pre-registered test.
- **Next action**: Run `tect_solver_pt_v3.py --config PDE/config_template_brazovskii.json`
  on seeds 17/23/41/73; verify regime banner; extract `mstar2_analytic_over_numeric_corr`
  from `live_m_parallel_summary.json`.
- **Owner**: `PDE/tect_solver_pt_v3.py` v3.1, `PDE/live_m_parallel.py` v1.0.
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-05-15 (30-day default).

### Q-2026-04-15-02 — Gate 1–4 coefficient certificate (Project IV)

- **Statement**: The Gates 1–4 carrier audit (Math15–24) has its
  logic proved but the *quantitative coefficient bounds* required
  for certificate-grade closure remain numerical estimates. A
  closed-form interval or a rigorously bounded numerical certificate
  is required before Project IV moves from ⚠ LOGIC PROVED to ✅
  PROVED.
- **Current state**: `PDE/carrier_audit.py` v1.0 computes the four
  gate quantities. Symbolic tight bounds are missing.
- **Strategy**: Either (a) analytic bound via $O_h$-symmetric
  inequalities on the 12-vector star, or (b) interval arithmetic
  wrapping the existing numerical audit.
- **Owner**: `PDE/carrier_audit.py` v1.0; Math15–24.
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-06-15 (60-day; awaits analytic work).

### Q-2026-04-15-03 — Flavor Gram matrix $G_{IJ}$ positive-definiteness (Project V)

- **Statement**: The framework for the flavor sector (Math25–30)
  derives the Gram matrix $G_{IJ}$ governing family mixing but has
  not proved $G_{IJ} \succ 0$ across the full locked parameter
  region.
- **Why open**: A counter-example at any interior point of the
  locked region would invalidate the SM+GR IR limit derivation.
- **Strategy**: Compute $\det G$ and the leading principal minors
  symbolically at the locked triple, then extend by continuity
  arguments to a neighbourhood.
- **Owner**: Math29–30; no dedicated code module yet.
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-06-15 (60-day).

### Q-2026-04-15-04 — First-principles derivation of the locked triple $(\mu^{2},\lambda,\gamma)$ from RG flow   [PARTIAL 2026-04-15 → Math40]

- **Partial-closure note**: The sibling kinetic pair $(Z,Y)$, which
  governs the Brazovskii shell position $q_{0}=k_{\min}$ and was
  implicitly part of the "locked parameters" remit, is now sealed by
  `Math40-RG-kinetic-2026-04-15` (`docs/math/TECT-Math40.tex.txt` Thm 1):
  $Y\,q_{0}^{2}/|Z|=1/2$ as a universal one-loop Wilsonian identity.
  The original triple $(\mu^{2},\lambda,\gamma)$ remains open.
- **Statement**: Math38 reproduces $(\mu^{2}, \lambda, \gamma) = (0.26, -0.43, 1.62)$
  self-consistently from the three-equation Brazovskii matching,
  which is a theoretical derivation relative to the measured
  curvature $\mathcal{M}^{2}_{\mathrm{meas}}$. A fully first-principles
  derivation from RG flow / 1-loop matching, *independent* of
  numerical curvature input, is the ambition.
- **Why open**: Math38 is a consistency check, not an RG derivation.
  The locked triple passes the sanity test but is not yet *derived*
  in the strong sense.
- **Relation to D-2026-04-15-01**: That dead-end entry records the
  earlier continuation-schedule fit; Q-…-04 is the positive version
  of the same ambition — do it properly.
- **Owner**: Math38 follow-up note (not yet drafted).
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-07-15 (90-day; long-horizon analytic).

### Q-2026-04-15-05 — Continuum limit of the spectral BCC Laplacian

- **Statement**: The extractor uses the bare BCC Laplacian symbol
  $(8/a^{2})(1 - \cos(a k_x / 2) \cos(a k_y / 2) \cos(a k_z / 2))$.
  The continuum limit $a \to 0$ of observables at the Brazovskii
  fixed point must be shown to exist and to give the locked
  analytic predictions, independent of lattice artefacts at finite
  $a$.
- **Why open**: Lattice-artefact attack is standard in peer review.
  A convergence-of-observables plot vs grid spacing $a$ is the
  expected evidence; a bound on $O(a^2)$ corrections from the cubic
  symmetry of the BCC lattice is the strong version.
- **Owner**: `PDE/tect_solver_pt_v3.py` v3.1 (grid-spacing sweep driver to be added).
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-06-15 (60-day).

### Q-2026-04-15-06 — Microscopic origin of the Class-II mediator mass $M_X$   [CLOSED 2026-04-16 → Math43]

- **Last reviewed**: 2026-04-16 &nbsp;|&nbsp; **Review by**: 2026-06-16 (60-day; closed-pending-two-loop).
- **Closure note (2026-04-16)**: Math43 Thm `closure` proves
  $\Lambda/\mu_{B}=e$ from Wilson-step uniqueness and PMS coincidence
  at $\ell^{\star}=1$. The one-parameter freedom of Math42 is removed
  at one-loop leading log. $M_{X}=2.0$ is now fully determined by
  $(\mu^{2},\lambda,\gamma)$ and BCC geometry, conditional only on
  two-loop stability and the Q-18 commensurability verdict.

### Q-2026-04-15-06-LEGACY — Microscopic origin of the Class-II mediator mass $M_X$   [PARTIAL 2026-04-15 → Math42, OPEN — superseded by Math43]

- **Partial-closure note (revised after review 2026-04-15)**: Math42
  Thm 1 reduces $(M_{X},\alpha_{X})$ from **free parameters** to a
  **one-parameter matched family** indexed by $\log(\Lambda/\mu_{B})$.
  Obtaining the runtime value $M_{X}=2.0$ requires the additional
  prescription $\Lambda/\mu_{B}=e$, which Math42 itself flags as
  the sole remaining phenomenological commitment. This question
  therefore **remains open** until the natural matching choice is
  derived (Math43 target).
- **Statement**: The Class-II UV action
  $\mathcal{L}_{\mathrm{UV}}^{(II)} = \tfrac{M_X^{2}}{2}\,X_i^{a}X_i^{a} + \alpha\,X_i^{a} J_i^{a}[\Psi] + \cdots$
  (Math37 L40–L41; Math15 L570–L591) introduces a heavy-mediator mass
  scale $M_X$. The runtime configuration uses $M_X = 2.0$ in
  `PDE/config_template_brazovskii.json` L37, but no first-principles
  RG, matching, or dimensional-analysis argument pins this value.
- **Predicted by**: Math37 § UV (structural form); value not predicted.
- **Why open**: $M_X$ enters the final closure
  $m^{*2}_{\mathrm{TECT}} \leftarrow \alpha_X^{2}q_0^{2}/M_X^{2}$ as a
  free parameter. Under peer review the claim "we predict
  $m^{*2} \approx 9.005$" is conditional on an un-derived input.
- **Falsification criterion**: Either (i) a derivation from UV physics
  or RG-flow matching fixes $M_X$ to a value consistent with the
  locked closure, or (ii) sensitivity analysis shows
  $m^{*2}_{\mathrm{TECT}}$ is stable under $M_X$ variation in the
  acceptance band $[1.8,\,45.0]$, demoting $M_X$ from parameter to
  physically uninformative knob.
- **Next action**: Draft a Math-follow-up note on heavy-mediator
  elimination tying $M_X$ to either (a) the BCC microscopic lattice
  scale, (b) an auxiliary short-distance cutoff, or (c) a matching
  condition to the emergent-$U(1)$ gauge coupling.
- **Owner**: `docs/math/` (new Math-4x note); `docs/papers/TECT_Paper_III`.
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-07-15 (90-day; long-horizon analytic).

### Q-2026-04-15-07 — First-principles determination of the Class-II coupling $\alpha_X$   [CLOSED 2026-04-16 → Math43]

- **Last reviewed**: 2026-04-16 &nbsp;|&nbsp; **Review by**: 2026-06-16 (60-day; closed-pending-two-loop).
- **Closure note (2026-04-16)**: See Q-2026-04-15-06 closure; same
  Math43 Thm `closure` removes the one-parameter freedom of Math42
  for $\alpha_{X}=0.3$ at one-loop leading log. Conditional only on
  two-loop stability.

### Q-2026-04-15-07-LEGACY — First-principles determination of the Class-II coupling $\alpha_X$   [PARTIAL 2026-04-15 → Math42, OPEN — superseded by Math43]

- **Partial-closure note (revised after review 2026-04-15)**: Same
  Math42 Thm 1 reduces the two parameters to one matched family;
  the dimensionless ratio $\tilde{\alpha}=\alpha_{X}q_{0}/M_{X}$ is
  the physical combination. Full closure requires derivation of the
  natural matching choice $\Lambda/\mu_{B}=e$, which is **not** yet
  proven. This question **remains open**.
- **Statement**: The Class-II coupling $\alpha_X$ (Math37 L41; Math15
  L590–L654) sets the strength of the $X_i^{a} J_i^{a}$ interaction
  and, after heavy-mediator elimination, yields
  $\lambda_{\parallel} = \alpha_X^{2}\,q_0^{2}/(3 M_X^{2})$. The
  runtime value $\alpha_X = 0.3$ in
  `PDE/config_template_brazovskii.json` L35 is phenomenological.
- **Predicted by**: Math37 § UV (structural form); value not predicted.
- **Why open**: The same conditional-closure argument as Q-…-06:
  $\alpha_X$ enters the analytic prediction but carries no microscopic
  derivation or anomalous-dimension bound.
- **Falsification criterion**: A matching of $\alpha_X$ to either the
  emergent-$U(1)$ gauge coupling or a RG-flow IR fixed-point value,
  OR a demonstration that the locked closure is invariant under
  $\alpha_X$ rescaling with $M_X$ in the physical ratio
  $\alpha_X/M_X$.
- **Next action**: Same follow-up Math note as Q-…-06; investigate
  whether only the dimensionless combination
  $\tilde\alpha \equiv \alpha_X\,q_0/M_X$ enters physical predictions,
  which would collapse the two free parameters into one.
- **Owner**: `docs/math/` (new Math-4x note); `docs/papers/TECT_Paper_III`.
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-07-15 (90-day; long-horizon analytic).

### Q-2026-04-15-08 — Math04 Conjecture A: fixed-size $N=12$ optimality

- **Statement**: Among all Bravais lattices with first-shell
  coordination number fixed at $N=12$, the BCC first-shell
  constellation uniquely minimises the effective energy functional
  $\mathcal{E}[S]$ (Math04 §3).
- **Predicted by**: Math04 Conjecture A.
- **Why open**: Proved for cubic sublattices (SC / BCC / FCC) by
  direct constellation sum; general-Bravais proof requires a
  variational argument over the full Bravais moduli space.
- **Falsification criterion**: A single non-cubic Bravais lattice
  with $N=12$ first-shell coordination and $\mathcal{E} <
  \mathcal{E}_{\mathrm{BCC}}$.
- **Owner**: Math04 follow-up; Project I.
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-07-15 (90-day).

### Q-2026-04-15-09 — Math04 Conjecture B: Bravais first-shell optimality (non-cubic)

- **Statement**: For non-cubic Bravais lattices, the first-shell
  constellation minimises $\mathcal{E}[S]$ within its symmetry class.
- **Predicted by**: Math04 Conjecture B.
- **Why open**: Companion to Q-…-08 with lifted $N$ constraint;
  requires a symmetry-class-by-symmetry-class variational analysis.
- **Owner**: Math04 follow-up.
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-07-15 (90-day).

### Q-2026-04-15-10 — Math06 Lorentz-emergence rigor (partial claim)

- **Statement**: The acoustic Cauchy relation $C_{44} = (C_{11} -
  C_{12})/2$ emerges to leading order in the amplitude $A$; the
  $O(A^{4})$ correction is bounded but the full
  anisotropy-suppression proof over the Brazovskii-locked
  parameter region is partial in Math06.
- **Predicted by**: Math06 §4; Math-Lorentz Supplementary §2.
- **Why open**: The current derivation controls the linearised
  elasticity tensor but not the higher-amplitude corrections
  uniformly.
- **Falsification criterion**: A point in the locked region where
  $|C_{44} - (C_{11}-C_{12})/2| / C_{44} > $ acceptance threshold.
- **Owner**: Math06 + Math-Lorentz supplementary follow-up.
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-06-15 (60-day).

### Q-2026-04-15-11 — Math24 $Z_{\mathrm{pol}}^{(T)}$ transverse loop weight

- **Statement**: The transverse-polarisation loop renormalisation
  $Z_{\mathrm{pol}}^{(T)}$ (Math24) requires a norm-uniform estimate
  over the Brazovskii shell.
- **Predicted by**: Math24 §4.
- **Why open**: D-2026-04-15-04 records the failed small-$p$
  approach; the norm-uniform replacement is drafted but not closed.
- **Owner**: Math24 follow-up.
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-06-15 (60-day).

### Q-2026-04-15-12 — Math26 C2 (gravity) unconditional derivation   [CLOSED 2026-04-16 → Math45, pending Math46 finite audit]

- **Last reviewed**: 2026-04-16 &nbsp;|&nbsp; **Review by**: 2026-06-16 (60-day; closed-pending-audit).
- **Closure note (2026-04-16)**: Math45 delivers the theorem-level
  chain `shell fluctuations → u(x) → ε_ij → h^{TT} → Einstein kinetic
  → κ_G universal`. Thm `C2_Einstein` gives
  $\kappa_{G}^{-2}=Y q_{0}^{2}=|Z|/2$; Thm `C2_univ` establishes
  species-independence. Remaining work: three finite numerical tests
  (T1 purity, T2 Einstein normalisation, T3 universality) at the 1%
  level (Thm `C2_actual_audit`) — targeted by Math46 extractor.

### Q-2026-04-15-12-LEGACY — Math26 C2 unconditional derivation   [PARTIAL 2026-04-15 → Math41, OPEN — superseded by Math45]

- **Partial-closure note (revised after review 2026-04-15)**:
  Math41-EW+gravity-candidate Prop 1 supplies a rank-2 BCC bilinear
  $h_{\mu\nu}$ with a **linearised Einstein-Hilbert kinetic candidate**
  and a normalisation $G_{N}^{-1}=5|\lambda|\phi_{0}^{2}q_{0}^{4}/(2\pi)$
  at the Brazovskii locked point. The **emergent-graviton theorem
  is not established**: residual items (g1) spin-2 projector
  separation, (g2) scalar/vector-graviton contamination removal,
  (g3) linearised-diffeomorphism redundancy, (g4) universal
  matter coupling (equivalence principle) are open. Math41 §4.
- **Statement**: The C2 pathway — emergent linearised gravity on
  the BCC condensate — is derived conditionally in Math26; an
  unconditional derivation from the BCC elasticity tensor at the
  Brazovskii fixed point is open.
- **Predicted by**: Math26 §3.
- **Owner**: Math26 follow-up; Project VI.
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-07-15 (90-day).

### Q-2026-04-15-13 — Math26 C3 (gauge) unconditional derivation   [CLOSED 2026-04-16 → Math44, pending Math46 extractor audit]

- **Last reviewed**: 2026-04-16 &nbsp;|&nbsp; **Review by**: 2026-06-16 (60-day; closed-pending-audit).
- **Closure note (2026-04-16)**: Math44 delivers the theorem-level
  chain `global algebra → local U(2)_{EW} frame F(x) → A_μ = -iF†∂_μF
  → D_μ → YM kinetic` with computable positive coefficients
  $c_{W}=1/(96\pi^{2})$, $c_{B}=1/(64\pi^{2})$ (Thm `cWcB`). Canonical
  $g^{2}=24\pi^{2}$, $g'^{2}=16\pi^{2}$ at the matching scale. RG
  running to $m_{Z}$ and the extractor for $F(x)$ from the locked
  Hessian remain (Math46).

### Q-2026-04-15-13-LEGACY — Math26 C3 unconditional derivation   [PARTIAL 2026-04-15 → Math41, OPEN — superseded by Math44]

- **Partial-closure note (revised after review 2026-04-15)**:
  Math41-EW+gravity-candidate Prop 2 establishes a **global internal
  $\mathfrak{su}(2)\oplus\mathfrak{u}(1)$ algebra** on the valley
  doublet $\Psi_{D}$ from the Math31 four-class exhaustiveness, with
  a tree-level coupling ratio $\sin^{2}\theta_{W}|_{\mathrm{tree}}=1/4$
  **contingent on the existence of a local gauge extension**. The
  emergent-gauge-theory theorem is not established: residual items
  (e1) local connection field, (e2) Yang-Mills kinetic term,
  (e3) chiral matter coupling (Math17 witness modules),
  (e4) $\sin^{2}\theta_{W}$ RG running to $M_{Z}$,
  (e5) colour $SU(3)_{C}$ three-valley extension, are open.
  Math41 §4.
- **Statement**: The C3 pathway — full SM gauge emergence — is
  derived conditionally on the $SU(2)$ Route B and the flavor Gram
  matrix. An unconditional derivation awaits closure of Q-02, Q-03,
  and the $SU(3)$ channel (not yet opened).
- **Predicted by**: Math26 §4.
- **Owner**: Math26 follow-up; Project IV–V.
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-07-15 (90-day).

### Q-2026-04-15-14 — Math29 CKM convergence theorem

- **Statement**: The Math21 toy-model CKM derivation ($|V_{us}|
  \approx 0.228$) converges to the full three-family CKM matrix in
  the locked-basis limit (Math29 conjecture).
- **Predicted by**: Math29 §2.
- **Why open**: Requires Q-2026-04-15-03 (Gram positivity) + a
  continuity argument along the locked line.
- **Owner**: Math29 follow-up.
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-07-15 (90-day).

### Q-2026-04-15-15 — Math25 precision-level CKM fit including CP

- **Statement**: A real-symmetric Gram matrix cannot reproduce the
  CP-violating phase of the measured CKM matrix to experimental
  precision; a Hermitian extension (complex off-diagonal entries) is
  required.
- **Predicted by**: Math25 §4.
- **Why open**: The microscopic origin of the complex phase from
  the BCC condensate + heavy-mediator sector is not yet identified.
- **Owner**: Math25 + Math29 follow-up.
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-07-15 (90-day).

### Q-2026-04-15-16 — Math17 longitudinal primitive odd singlet $\theta'^{3}\sigma_{3}$

- **Statement**: The primitive odd-singlet source $\theta'^{3}\sigma_{3}$
  produced by Math17 witness-theorem formalism must be verified as
  non-degenerate in the full TECT action (not only the truncated
  witness model).
- **Predicted by**: Math17 §3.
- **Owner**: Math17 follow-up; Math35 canonical-basis check.
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-06-15 (60-day).

### Q-2026-04-15-17 — Math35 $(m_{\parallel} u_{\parallel})_{\mathrm{corr}}$ numerical value

- **Statement**: The corrected $(m_{\parallel} u_{\parallel})_{\mathrm{corr}}$
  invariant derived in Math35 from the canonical $3\times 3$ $S_{\min}$
  basis requires a production-grade numerical evaluation at the
  Brazovskii-locked parameters.
- **Predicted by**: Math35 §5.
- **Why open**: Depends on closure of Q-2026-04-15-01 (Step C
  convergence) to supply the numerical $u_{\parallel}$ input.
- **Owner**: `PDE/live_m_parallel.py`; Math35.
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-06-15 (60-day).

### Q-2026-04-15-18 — $q_{0}$ / $k_{\min}$ / $|G|$ commensurability

- **Statement**: Three theoretically-linked wavevector scales disagree
  numerically at the Brazovskii-locked parameter set. Let
  $k_{\min}\equiv\sqrt{-Z/(2Y)}$ denote the minimiser of the quadratic
  kinetic symbol $F_{\mathrm{quad}}(k)=r+Zk^{2}+Yk^{4}$ with $(Z,Y)=(-1,0.5)$,
  giving $k_{\min}=1.0$. Let $q_{0}=0.6801747616$ denote the value
  written in `PDE/config_template_brazovskii.json` (inherited from the
  Math01/Math38 post-hoc shell-mean extraction on a
  $(N,L)=(32,10\pi)$ grid with $dk=2\pi/L\approx 0.3927$, i.e.\
  $q_{0}\approx\sqrt{3}\,dk$, consistent with the $(1,1,1)$
  body-diagonal shell). Let $|G|=\sqrt{2}\,dk\approx 0.5554$ denote
  the first-shell magnitude produced by
  `make_bcc_shell_G_list` (the twelve $(\pm1,\pm1,0)$-type vectors).
  The three numbers $\{k_{\min}, q_{0}, |G|\}$ are not equal and not
  commensurate with any single discrete cubic shell.
- **Predicted by**: Brazovskii effective kinetic (Math05/Math07
  derivation of $Z,Y$); BCC shell geometry (Math13);
  `config_template_brazovskii.json` (runtime).
- **Why open**: The solver, the extractor, and the shell-list all
  carry a different notion of "where the condensate sits." Until
  reconciled, any production run that couples FFT kinetics to a
  BCC-shell projector may mis-weight the active modes.
- **Falsification criterion**: A Patch-A-class production run at
  $(N,L)=(32,10\pi)$ whose post-hoc extractor reports $q_{0}$
  agreeing with either $k_{\min}=1.0$ or $|G|=\sqrt{2}\,dk$ to
  within one radial bin. Persistent disagreement across
  $\{32, 48, 64\}^{3}$ falsifies the current commensurability
  assumption and forces either (a) a continuum-limit renormalisation
  of $(Z,Y)$ or (b) a regridding with $L$ chosen so that
  $k_{\min}$ coincides with a BCC first-shell magnitude.
- **Owner**: `PDE/tect_solver_pt_v3.py` (kinetic),
  `PDE/real_backend_pt_bcc_mixed_v3.py` (projector),
  `config_template_brazovskii.json` (runtime), Math05/Math07/Math13.
- **Last reviewed**: 2026-04-15 &nbsp;|&nbsp; **Review by**: 2026-05-15 (30-day).

### Q-2026-04-20-XX — Yukawa mass hierarchy and flavor-diagonal lepton/quark masses

- **Statement**: The three-generation structure is topologically fixed (Math49, Thm gen_count: $\dim H_L = 3$), but the mass splittings within each family (e.g., $m_e \ll m_\mu \ll m_\tau$, $m_d \ll m_s \ll m_b$) are not yet derived. These arise from overlaps of condensate wavefunctions at scales $\lesssim \Delta$ (shell width) and require analysis of the full non-local Dirac/Yukawa profile.
- **Predicted by**: Math49 — topological index fixes dimension but NOT mass splitting.
- **Why open**: Condensate wavefunction profile at sub-shell scales not yet extracted from solver output.
- **Strategy**: Post-process converged Newton-Krylov solution to extract generational-overlap integrals governing mass ratios.
- **Owner**: New extractor (C6, not yet drafted); Math49 follow-up.
- **Last reviewed**: 2026-04-20 &nbsp;|&nbsp; **Review by**: 2026-06-20 (60-day; awaits numerical audit infrastructure).

### Q-2026-04-20-YY — Numerical verification of Lorentz-violation SME coefficients from converged BCC condensate

- **Statement**: Math_IR_Bound proves analytically that cubic anisotropy is suppressed by $(k/|G^*|)^{2+\eta}$ and predicts SME coefficients $c_{\mu\nu} \lesssim 10^{-70}$ at observable scales. This bound must be numerically verified by extracting actual SME coefficients from the converged N=64/128 Newton-Krylov solution.
- **Predicted by**: Math_IR_Bound, Prop SME_bound.
- **Why open**: Requires converged solver output and dispersion-relation isotropy analysis.
- **Strategy**: C7 extractor (not yet drafted) computes $\omega(\mathbf{k})$ for multiple momentum directions; fits to SME parametrisation; compares to RG prediction.
- **Owner**: New extractor (C7); Math_IR_Bound follow-up.
- **Last reviewed**: 2026-04-20 &nbsp;|&nbsp; **Review by**: 2026-07-20 (90-day; depends on Phase 4 continuum audit).

### Q-2026-04-20-ZZ-A — Rigorous index-theoretic proof of $\dim(H_L) = 3$ on $\text{Gr}(2,5)/G_{\text{SM}}$   [RESOLVED NEGATIVE 2026-04-20 → FALSIFIED-ANSATZ; SEE Q-2026-04-20-R3]

- **Closure outcome (2026-04-20)**: `Math49-rigorous-v2` computes $\chi(\text{Gr}(2,5), E_L(a,b))$ exactly via Bott equivariant localisation in sympy rational arithmetic. Five Weyl-dim-formula sanity checks pass ($\chi(\mathcal{O}(d)) = 0,1,10,50,175$ for $d=-1,\dots,3$). Direct-sum additivity $\chi(E_L(a,b))=\chi_S(a)+\chi_Q(b)$ verified. Theorem 2: $\chi \neq 3$ for every $(a,b)\in\mathbb{Z}^2$; minimum positive Euler characteristic is 5. Logged as `D-2026-04-20-02` in `NEGATIVE-RESULTS.md`.
- **Implication**: The naive direct-sum ansatz is refuted. Pillar 6 closure via this route is ruled out. Three refinement paths open: R1 Schur-functor irreducible subbundle; R3 $\mathbb{Z}_6$-equivariant Lefschetz index; R4 partial flag $\mathrm{Fl}(2,3;5)$. R2 (discrete quotient) ruled out by $\pi_1(\text{Gr}(2,5))=1$.
- **Successor**: See Q-2026-04-20-R3 (highest priority), Q-2026-04-20-R1, Q-2026-04-20-R4 below.

### Q-2026-04-20-ZZ-B — Rigorous triangle-anomaly proof with full 15-Weyl enumeration   [CLOSED 2026-04-20 → Math49b-rigorous-v2]

- **Closure outcome (2026-04-20)**: `Math49b-rigorous-v2` proves vanishing of all six triangle anomaly coefficients per SM generation with the abelian-leg reduction $\mathrm{Tr}(T^a\{T^b, Y\}) = 2 Y T(R_H)\delta^{ab}$ (via $[T^a, Y]=0$). Explicit sums: $U(1)_Y^3$: $6(1/6)^3 + 3(-2/3)^3 + 3(1/3)^3 + 2(-1/2)^3 + 1(1)^3 = 0$; $SU(2)^3$: $d^{abc}=0$ identically; $SU(3)^3$: fundamental $+$ two antifundamentals $\Rightarrow A(R)=1-2=-1 \Rightarrow$ cancellation with $Q_L$. Archived in `CHANGELOG.md §[Math49-Math_EP-v2-feedback-loop-2026-04-20]`.
- **Cross-family comment**: Per-generation cancellation proved; three-family universality of hypercharge assignments (Q-2026-04-20-YK below) remains open.

### Q-2026-04-20-ZZ-C — Lemma: BCC disclination topological charge $\equiv$ generator of $\pi_1(\text{SO}(3)/G_{\text{pt}})$   [CLOSED 2026-04-20 → Math49c-rigorous-v2]

- **Closure outcome (2026-04-20)**: `Math49c-rigorous-v2` establishes $\pi_1(\text{SO}(3)/O) = 2O$ (binary octahedral group) with point-group choice $G_{\text{pt}} = O_h$ (full BCC symmetry); the rotation-only projection to $O$ is the physically relevant orientation-defect group. Lemma 2 (structure of $O$): $|O|=24$ with conjugacy-class table. Lemma 3: the $\pi/2$ rotation around $\langle 100 \rangle$, $R^{(100)}_{\pi/2}\in O$, lifts to $\tilde R^{(100)}_{\pi/2}\in 2O$ satisfying $(\tilde R^{(100)}_{\pi/2})^4 = \exp(-i\pi\sigma_1) = -\mathbb{1}$. Finkelstein–Rubinstein theorem then gives exchange monodromy $R^2 = -\mathbb{1}$ for spin-$1/2$ Dirac zero modes on disclination cores. Archived in `CHANGELOG.md §[Math49-Math_EP-v2-feedback-loop-2026-04-20]`.

### Q-2026-04-20-ZZ-D — Dynamical proof that $m_I = m_G$ from the BCC defect–geodesic limit   [CLOSED 2026-04-20 → Math_EP-rigorous-v2 scalar + Dirac]

- **Closure outcome (2026-04-20)**: `Math_EP-rigorous-v2` proves $m_I = m_G$ for (i) scalar collective modes and (ii) Dirac zero modes with exponential spatial decay $|\psi_0(\vec x)| \leq C e^{-\kappa|\vec x|}$, $\psi_0 \in L^2(\mathbb{R}^3)$. The crux is the Belinfante–Rosenfeld improvement theorem $T^{\text{imp},\mu\nu} = T^{\text{Hilb},\mu\nu}$ with spin density $S^{\rho\mu\nu} = (i/4)\bar\psi\{\gamma^\rho, \Sigma^{\mu\nu}\}\psi$, together with Lemma 1: $\int d^3x\,\Delta T^{00} = 0$ (surface term vanishes by the normalisability hypothesis). Pass-3 patch P3-04 made the exponential-decay hypothesis explicit in the main theorem statement. Archived in `CHANGELOG.md §[Math49-Math_EP-v2-feedback-loop-2026-04-20]`.
- **Residual open item (sub-question)**: Full tensor-excitation WEP (graviton sector) awaits the emergent-graviton theorem (Q-2026-04-15-12-LEGACY + Math46 C2 audit).

### Q-2026-04-20-ZZ-E — Rigorous Wilsonian RG bound for BCC cubic anisotropy with 1-loop $\eta$   [PARTIAL 2026-04-20 → Math_IR_Bound-rigorous-v2, OUTLINE]

- **Partial-closure note (2026-04-20)**: `Math_IR_Bound-rigorous-v2` installs the correct $O_h$-invariant operator $\mathcal{O}^{(c)}_4 = \sum_i(\partial_i\Psi)^4 - \tfrac{1}{3}(\sum_i(\partial_i\Psi)^2)^2$ and proves the Gaussian-level result: $[\mathcal{O}^{(c)}_4] = 6$, $[g] = -3$, IR-irrelevant. Section 4 establishes anisotropic Brazovskii scaling $[\delta k_\perp] = \mu$, $[\delta k_\parallel] = \mu^2$ with $d_{\text{eff}} = 4$ on the shell $|\vec k|=q_0$. Pass-3 patch P3-06/08 relabelled the 1-loop anomalous-dimension claim as OUTLINE (previously asserted without derivation). **Full Callan–Symanzik RG at the Brazovskii FP + numerical BZ integrals for $\eta^{(c)}$ → v3**. See Q-2026-04-20-v3-IR below.

### Q-2026-04-20-R1 — Schur-functor irreducible subbundle refinement of the three-generation index (Pillar 6, refinement R1)

- **Origin**: Opened 2026-04-20 as refinement path after Q-2026-04-20-ZZ-A FALSIFIED-ANSATZ.
- **Statement**: Replace the direct-sum ansatz $E_L(a,b) = S \otimes (\det Q)^a \oplus Q\otimes(\det S)^b$ with an irreducible Schur-functor image $E_L = \mathbb{S}^{(\lambda_1, \lambda_2)}(S \oplus Q)$ for small partitions $\lambda$ selected by the $G_{\text{SM}}$-branching of $\mathbf{5}$. Compute $\chi(\mathbb{S}^\lambda(S\oplus Q))$ via Bott localisation and scan for $\chi = 3$.
- **Strategy**: Direct extension of the `Math49_hrr_v3.py` sympy localisation kernel; Schur functor $\mathbb{S}^\lambda$ acts on weights by symmetriser/antisymmetriser projection, yielding a rational function of the $t_i$ whose localisation integral is tractable.
- **Why open**: A single Schur diagram might reproduce $\chi = 3$ where the direct sum failed; the phenomenologically natural choices are $\lambda = (1,1)$ (exterior square — dim 10) and $\lambda = (2)$ (symmetric square — dim 15), both compatible with SM-multiplet count per generation.
- **Owner**: `TECT-Math49d-R1-Schur.tex.txt` (future).
- **Last reviewed**: 2026-04-20 &nbsp;|&nbsp; **Review by**: 2026-05-20 (30-day).

### Q-2026-04-20-R3 — $\mathbb{Z}_6$-equivariant Lefschetz-index refinement of the three-generation count (Pillar 6, refinement R3)   [CLOSED 2026-04-20 — PROVED@GEOMETRIC; see archive]

- **Status**: CLOSED. See `## Archive` Q-2026-04-20-R3 entry below.
- **Summary**: $\chi^{\mathbb{Z}_6}(\mathrm{Gr}(2,5),\mathrm{Sym}^2 Q)=3$ proved (Math49d-R3-rigorous-v2.tex.txt, Theorem 1 of Math49d-R3-rigorous-v1.tex.txt); representation-theoretic meaning $3=\dim\mathrm{Sym}^2 V_\beta$ proved. Physical identification of the three $\mathrm{Sym}^2 V_\beta$ basis vectors with SM families remains open in Q-2026-04-20-YK and Math55.

### Q-2026-04-20-R4 — Partial flag $\mathrm{Fl}(2,3;5)$ alternative index route (Pillar 6, refinement R4)

- **Origin**: Opened 2026-04-20 as refinement path after Q-2026-04-20-ZZ-A FALSIFIED-ANSATZ.
- **Statement**: Replace $\text{Gr}(2,5)$ (parameter space of $SU(2)\subset SU(5)$ embeddings) with the full partial flag $\mathrm{Fl}(2,3;5)$ (parameter space of nested $SU(2) \subset SU(2)\times SU(3) \subset SU(5)$ embeddings). Compute the HRR index of a phenomenologically motivated bundle on $\mathrm{Fl}(2,3;5)$; scan for $\chi = 3$.
- **Why open**: The partial flag carries both the $SU(2)_W$ and $SU(3)_C$ subgroup data simultaneously and may be the more natural moduli space for the SM branching — at the cost of a 10-dim Calabi–Yau-adjacent target (dim $\mathrm{Fl}(2,3;5) = 2\cdot 3 + 2 = 8$-complex).
- **Strategy**: Extend `Math49_hrr_v3.py` Bott kernel to multi-step flag fixed-point combinatorics; use Bruhat cell decomposition for fixed-point enumeration.
- **Owner**: `TECT-Math49d-R4-flag.tex.txt` (future; fallback if R3 fails).
- **Last reviewed**: 2026-04-20 &nbsp;|&nbsp; **Review by**: 2026-06-20 (60-day; contingent on R3 outcome).

### Q-2026-04-20-v3-IR — Full Callan–Symanzik RG at Brazovskii FP with numerical BZ integrals for $\eta^{(c)}$

- **Origin**: Opened 2026-04-20 as v3 continuation of Q-2026-04-20-ZZ-E (closed at OUTLINE).
- **Statement**: At the Brazovskii anisotropic fixed point with scaling $[\delta k_\perp] = \mu$, $[\delta k_\parallel] = \mu^2$, $d_{\text{eff}} = 4$, compute the one-loop anomalous dimension $\eta^{(c)}$ of the cubic-$O_h$ operator $\mathcal{O}^{(c)}_4$ via explicit Brillouin-zone integrals $\int_{\text{BZ}} d^3k\, G(k)\, K_i^4$ where $K_i$ is the cubic-anisotropy vertex and $G(k) = 1/(r + Zk^2 + Yk^4)$ is the Brazovskii propagator evaluated on the BCC Brillouin zone. Derive the SME Lorentz-violation coefficient $c_{\mu\nu}$ from the resulting anomalous-dimension flow over the RG interval $[\mu_{\text{UV}}, \mu_{\text{IR}}]$.
- **Why open**: Math_IR_Bound-v2 establishes the Gaussian canonical dimension rigorously but defers the 1-loop correction as OUTLINE. Without the numerical BZ integral, the $10^{-70}$ SME bound remains quoted rather than derived.
- **Falsification criterion**: If $\eta^{(c)}$ computed from the BZ integral has the wrong sign to preserve IR-irrelevance, or the integrated suppression factor falls below current experimental SME bounds ($c_{\mu\nu} \lesssim 10^{-17}$ from atomic clocks), Pillar 2/8 closure via this route is ruled out.
- **Strategy**: (i) symbolic reduction of the 1-loop vertex correction via $O_h$-symmetry projectors; (ii) numerical BZ integration on a cubic $k$-grid with $\geq 256^3$ sampling; (iii) RG flow integration from BCC UV scale to atomic-clock IR scale.
- **Owner**: `TECT-Math_IR_Bound-rigorous-v3.tex.txt` + new BZ-integrator module in `PDE/`.
- **Last reviewed**: 2026-04-20 &nbsp;|&nbsp; **Review by**: 2026-06-20 (60-day).

### Q-2026-04-20-YK — Three-family universality of hypercharge assignments and the Yukawa mass hierarchy

- **Origin**: Opened 2026-04-20 as residual question after Q-2026-04-20-ZZ-B closure@per-generation.
- **Statement**: Math49b-v2 proves triangle-anomaly cancellation per SM generation, with hypercharges $(Q_L, u_R, d_R, L_L, e_R)$ assumed identical across the three generations. The three-family universality (same hypercharge spectrum on each copy of $H_L$) is a structural input, not yet derived. Additionally, the *within-family* mass splittings $m_e \ll m_\mu \ll m_\tau$ are not produced by the per-family anomaly proof.
- **Why open**: A full three-generation index derivation (R3 refinement, Q-2026-04-20-R3) should produce universality as a corollary of the $\mathbb{Z}_6$-equivariant structure. Mass hierarchy requires a separate Yukawa-overlap calculation (see Q-2026-04-20-XX).
- **Strategy**: Derive universality from R3 equivariant branching; derive hierarchy from numerical overlap integrals of the three $H_L$ fibres on the BCC condensate profile.
- **Owner**: Math49d (R3 implementation); Math49e (Yukawa overlap).
- **Last reviewed**: 2026-04-20 &nbsp;|&nbsp; **Review by**: 2026-06-20 (60-day).

---

### Q-2026-04-21-CG-ZeroT — Zero-temperature rigorous limit of the 3-dimensional monopole Coulomb-gas free energy

- **Origin**: Opened 2026-04-21 as a named hypothesis (**H-CoulombGas-ZeroT**) of Math58-v2 skeleton (`TECT-Math58-v2-Pillar11-CosmConst-skeleton.tex.txt`, Prop.\ mono-sign).
- **Statement**: Show that the $T\to 0^{+}$ variational minimum of the 3-dimensional Coulomb-gas free-energy density $f_{\mathrm{CG}}(n_{\mathrm{pair}}) = T\,n_{\mathrm{pair}}\ln(n_{\mathrm{pair}}a^{3}) - \alpha_s(q_0)\,n_{\mathrm{pair}}\ln(r_{\mathrm{typ}}/a) + O(n_{\mathrm{pair}}^{2})$ exists, lies in the dilute-pair regime $n_{\mathrm{pair}}^{\star}\,a^{3} \ll 1$, and satisfies $f_{\mathrm{CG}}(n_{\mathrm{pair}}^{\star}) < 0$ whenever $\alpha_s(q_0) > 0$.
- **Predicted by**: Math58-v2 skeleton Prop.\ mono-sign (sketch-level proof); requires lattice-UV-regularised treatment for rigour.
- **Why open**: the $T\to 0^{+}$ limit of the entropic log term is singular; a standard statistical-mechanics argument (e.g.\ Fröhlich–Spencer renormalisation-group for 2D/3D Coulomb gases) is invoked implicitly. A rigorous lattice-UV regularised proof is required to convert the skeleton's Prop. to a Theorem.
- **Falsification criterion**: a numerical scan of $f_{\mathrm{CG}}(n_{\mathrm{pair}})$ over $n_{\mathrm{pair}}\,a^{3} \in [10^{-6}, 10^{-1}]$ at $T/\alpha_s(q_0) = 10^{-3}$ that fails to produce a negative-valued interior minimum would falsify **H-CoulombGas-ZeroT** and force Prop.\ mono-sign to be either discarded or replaced by a weaker inequality.
- **Owner**: Math58-v2 (Pillar 11).
- **Last reviewed**: 2026-04-21 &nbsp;|&nbsp; **Review by**: 2026-07-21 (90-day; defers until Task #54 endpoint drives the Math58-v2 instantiation).

---

### Q-2026-04-21-CALLIAS — Callias-type index for vortex/BCC pairing in the TECT condensate

- **Origin**: Opened 2026-04-21 as a named hypothesis (**H-Callias**) of Math58-v2 skeleton, Prop.\ vortex-sign.
- **Statement**: Establish the Callias-type index pairing $\mathrm{ind}_{\mathrm{C}}(v)$ between a smooth vortex configuration $v$ and the Brazovskii scalar background $\Psi$ that renders the vortex-sector contribution $\rho_{\mathrm{vortex}}$ negative on a positive-measure subset of the vortex configuration space $\mathcal{V}$.
- **Predicted by**: Math58-v2 skeleton Prop.\ vortex-sign (conditional statement; bound $|\rho_{\mathrm{vortex}}| \leq \varphi_0^{4}$ unconditional).
- **Why open**: The sign of $\rho_{\mathrm{vortex}}$ depends on a topological pairing that has not been derived from first principles within TECT. Without explicit construction, only the bound survives.
- **Falsification criterion**: an explicit construction of the Callias operator acting on vortex line + BCC scalar with a non-trivial index, together with a positive-measure subset of $\mathcal{V}$ over which the binding dominates the line tension. If no such construction is achievable, Prop.\ vortex-sign must be demoted to the bound-only form.
- **Owner**: Math58-v2 (Pillar 11).
- **Last reviewed**: 2026-04-21 &nbsp;|&nbsp; **Review by**: 2026-07-21 (90-day).

---

### Q-2026-04-21-YUKAWA-TECT — TECT-native fermion-mass mechanism in place of Yukawa-to-BCC

- **Origin**: Opened 2026-04-21 as a named hypothesis (**H-Yukawa**) of Math58-v2 skeleton, §6.
- **Statement**: Replace the schematic $m_f = y_f\,\phi_+^{\star}\,\varphi_0$ ansatz of §6 with the TECT-native mass formula for chiral fermions localised on BCC-disclination Dirac zero modes (Pillar 5). Re-derive Cor.\ dirac-scale using the topological $m_f \sim \varphi_0\,e^{-1/g}$ (or equivalent) scaling and verify that $(a_{\mathrm{Dirac}}, b_{\mathrm{Dirac}}) = (4, 0)$ is preserved.
- **Predicted by**: Math58-v2 skeleton §6 (Coleman-Weinberg block, flagged as order-of-magnitude placeholder).
- **Why open**: The Yukawa ansatz is not TECT-native. A consistent instantiation of Math58-v2 requires the Pillar-5 topological-zero-mode mass formula to supersede this placeholder.
- **Falsification criterion**: substitute the Pillar-5 mass formula into \eqref{eq:rho-dirac-CW}. If the resulting $\rho_{\mathrm{Dirac}}$ no longer factorises as $c\cdot\varphi_0^{4}$ (with $c$ a slowly-varying log function) or exhibits scale that violates Lemma dim-fact, the Coleman-Weinberg block must be removed from Thm.\ scale-closure and Pillar-11 closure is weakened.
- **Owner**: Math58-v2 (Pillar 11), dependent on Pillar-5 mass formula.
- **Last reviewed**: 2026-04-21 &nbsp;|&nbsp; **Review by**: 2026-07-21 (90-day).

---

## Archive (closed)

### Q-2026-04-20-PR1 — [RESOLVED 2026-04-21 later] Replacement bundle for Pillar 6 after Math49d-R3-v2 physical retraction

- **Statement** (original): identify a $\mathbb{Z}_6$-equivariant
  holomorphic bundle $E\to\mathrm{Gr}(2,5)$ whose $\mathbb{Z}_6$-invariant
  section space has complex dimension three and transforms as an
  $SU(2)_W$-singlet under $SU(3)_c\times SU(2)_W\times U(1)_Y\hookrightarrow SU(5)$.
- **Predicted by**: Math49d-R3-rigorous-v2 (retracted 2026-04-20,
  F-2026-04-20-03) + replacement plan in
  `TECT-PeerReview-Response-2026-04-20.tex.txt` §3.
- **Resolution (2026-04-21 later; tag `F-2026-04-21-R5W2`)**:
  wave-1 (Math49d-R5 v1.0, 2026-04-20) established
  $\sup_{|\lambda|\le 15,\;\ell(\lambda)\le 5} M^\lambda = 1$;
  wave-2 (Math49d-R5 wave-2 v1.0, 2026-04-21; see
  `Docs/math/TECT-Math49d-R5-replacement-wave2.tex.txt` and
  `Docs/supplementary/Math49d_R5_replacement_search_wave2.py` md5
  `8541621b`) extends the exhaustive LR census to $|\lambda|\in\{20,25\}$
  (all $192+377=569$ partitions with $\ell(\lambda)\le 5$) and yields
  $\sup_{\lambda\vdash 20} M^\lambda = \sup_{\lambda\vdash 25} M^\lambda = 1$,
  with exactly $15$ and $21$ partitions respectively realising
  $M^\lambda=1$. Combined with wave-1,
  $\sup_{|\lambda|\le 25,\;\ell(\lambda)\le 5} M^\lambda=1$, which
  falsifies the single-Schur-functor strategy through the full
  $k\le 5$ window.
- **Falsification-criterion verdict**: met. The single-bundle version
  of the $\mathrm{Gr}(2,5)$ approach is retired at the stated search
  depth; the minimal multi-bundle realisation
  $E_{\min}=\mathcal{O}\oplus\det V\oplus S^{(2,1,1,1)}V$ (total rank $7$)
  from wave-1 remains the operative direct-sum candidate.
- **Consequence for Pillar 6**: status unchanged (SCAFFOLD at the
  physical layer); the wave-2 result tightens but does not upgrade
  the scorecard. Next step: either prove $M^\lambda\le 1$ for all $k$
  (closed form), or compute the twisted Dirac chirality index on
  $E_{\min}$ under the BCC disclination connection.
- **Theory tag**: `Math49d-R5-wave2, 2026-04-21`.
  CHANGELOG.md top entry (2026-04-21 later).
  NEGATIVE-RESULTS.md: `F-2026-04-21-R5W2`.
- **Last reviewed**: 2026-04-21 &nbsp;|&nbsp; **Resolved at**: 2026-04-21 (later).

---

### Q-2026-04-21-IV-shell-adaptive — [RESOLVED 2026-04-21 late] Shell-adaptive interval-arithmetic certificate for $c_4(\epsilon)>0$

- **Statement** (original): A rigorous interval enclosure
  $c_4(\epsilon)\in[c_4^{\rm lo},c_4^{\rm hi}]$ with $c_4^{\rm lo}>0$
  is required to upgrade Pillar 8 from NEAR-FINAL CONDITIONAL to
  PROVED per the Proof-Completion Checklist.
- **Predicted by**: `docs/math/TECT-Math_IR_Bound-v4-BZ-integrator.tex.txt`
  §3.2; Proof-Completion Checklist Sign/Bound-closure criterion for Pillar 8.
- **Resolution (2026-04-21 late)**: closed by
  `docs/math/TECT-Math_IR_Bound-v4-shell-adaptive.tex.txt` and
  `PDE/bz_shell_adaptive.py` (v1.0, md5 `ada51b4b`). The shell-peak
  wrap was eliminated not by hybrid shell-band+off-shell subdivision
  (the originally proposed falsification pathway) but by an
  *analytically stronger* route: closed-form radial primitive
  $F(r) = \tfrac{1}{8p}\ln\!\big[((r-p)^2+q^2)/((r+p)^2+q^2)\big]
       + \tfrac{1}{4q}\big[\arctan((r-p)/q)+\arctan((r+p)/q)\big]$
  obtained by real partial-fraction factorization
  $m^2+(r^2-q_0^2)^2=[(r-p)^2+q^2]\,[(r+p)^2+q^2]$ with
  $p=\sqrt{(R+q_0^2)/2}$, $q=\sqrt{(R-q_0^2)/2}$, $R=\sqrt{q_0^4+m^2}$.
  Comb