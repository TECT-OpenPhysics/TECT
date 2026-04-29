# TECT Evidence Index

**Binding from**: 2026-04-15
**Purpose**: single-entry-point claim → evidence map, to support
reviewer Q&A without cross-file search.

Each row maps a claim / numerical fact / design choice to its
primary and secondary evidence paths. Secondary rows cite related
failure entries and runtime provenance so that the full reasoning
trail is visible in one place.

Canonical sources: `docs/math/`, `docs/papers/`, `docs/status/`,
`PDE/`. This file is a navigation layer; it contains no original
claims of its own.

**Discoverability discipline**: every row in §1–§3 must carry a
**Last reviewed** date; rows older than 60 days without re-review
are flagged by the `§7 full-repo audit` as stale. Rows in §4–§6
are structural and exempt from staleness.

**Rot rule**: when a file cited here is moved, renamed, or deleted,
the row must be updated in the same commit. A broken `code` path
in this file is a policy violation (UPDATE_POLICY §10.2).

---

## 1. Foundational claims

| Claim | Primary evidence | Secondary / history |
|---|---|---|
| **Math61 Stage-2-E pre-registration** (3 predictions sealed) | `docs/math/TECT-Math61-Falsifiability-Prereg.tex.txt` v1.0 (2026-04-21); SHA-256 anchor `b65cac59...` | `docs/runs/R-2026-04-21-001-*` (Task #85 completion); $G_E=\texttt{TRUE}$ |
| Math61 Prediction $P_1$: Cubic anisotropy $\|\kappa^{(c)}\|$ | Derives from Math57-v2 Theorem thm:main-v2 (one-loop RG bound $7\times 10^{-4}$, anisotropy $\Delta\eta^{\mathrm{KE}}$); conversion to light speed via Full_PDE_Pauli §4.2. Central: $3.5\times 10^{-4}$; CI: $[1.5\times 10^{-4}, 5.5\times 10^{-4}]$; fail $>10^{-3}$. Observable: Lorentz tests (cavity QED, VLBI, GRB). | One-loop only (higher-loop pending); matches SME anisotropy bounds; unfa\lsifiable at current expt precision. |
| Math61 Prediction $P_2$: EP violation $\|\eta_{\mathrm{EP}}\|$ | Derives from Math\_EP-rigorous-v3.1 Theorem thm:EP-violation-suppression; conditional on graviton mass $m_h$. Central: $5\times 10^{-13}$; CI: $[2\times 10^{-13}, 8\times 10^{-13}]$; fail $>10^{-10}$. Observable: Eötvös balance (Su et al. 2018), MICROSCOPE (Touboul et al. 2017). | Scaffolding-level conditional (external $m_h$); current expt bounds $\sim 10^{-15}$ already constraining. |
| Math61 Prediction $P_3$: Graviton normalisation $Z_h$ | Derives from Math41/45/46c (Pillar 3 graviton emergence) + pending Math55 Phase-2 continuum limit (Task #54). Predicted envelope: $Z_h \in [0.575, 0.875]$; fail $Z_h < 0.2 \vee Z_h > 1.2$. Observable: GW dispersion (LIGO/Virgo), CMB tensor modes (future). | Not yet measured (Task #54 blocked); label "predicted envelope pending measurement". |
| BCC ground-state uniqueness | `docs/math/TECT-Math01.tex.txt`–`Math05.tex.txt`; `PDE/tect_c5_bcc_stability.py` | `Website/math/project-I-bcc-uniqueness.html` |
| Loop-count hierarchy $N_\mathrm{BCC}=6 > N_\mathrm{FCC}=2 > N_\mathrm{SC}=0$ | `docs/math/TECT-Math03.tex.txt` | Sync Manifest §1 T1 |
| Emergent $U(1)$ gauge structure | `docs/math/TECT-Math06.tex.txt`–`Math09.tex.txt`; `PDE/projector_spectral.py` | `Website/math/project-II-emergent-u1.html` |
| Dirac node: $\det H_D(0)=0$ | `docs/math/TECT-Math10.tex.txt`–`Math12.tex.txt`; `PDE/bloch_linearization.py` L137–141 | `Website/math/project-III-weyl-dirac.html` |
| Rank-2 uniqueness ($G_{\mathrm{SM}}$ stabilizer) | `docs/papers/TECT_Paper_III_RankSelection.tex` Prop 5.4; `PDE/tect_rank_selection_v4.py` | Paper IV (standalone statement) |
| Brazovskii regime (inverse-superconductor) | `docs/math/TECT-Math38.tex.txt` | `NEGATIVE-RESULTS.md` F-2026-04-15-01; Sync Log row 4 |
| Chern class $c_1(\mathrm{T}S^{2}) = 2$ (transverse phonon bundle) | `docs/math/TECT-Math07.tex.txt`; `PDE/projector_spectral.py` | Math08 obstruction; `Website/math/project-II-emergent-u1.html` |
| $U(1)$ bundle obstruction on $S^{2}$ — global section impossible | `docs/supplementary/TECT-U1_Gauge_Supplementary.tex.txt` | Math08; Math-U1 §2 |
| Clifford $\mathrm{Cl}(3)$ closure at the Dirac node | `docs/math/TECT-Math18.tex.txt` (+ Math19–Math20) | $\Gamma^{i}=\tau^{1}\!\otimes\!\sigma_{i}$, $\tau^{3}\!\otimes\!\mathbb{I}$ |
| Opposite-valley pairing + valley $\mathbb{Z}_{2}^{V}$ mass protection | `docs/math/TECT-Math11.tex.txt`–`Math14.tex.txt` | Witness theorem (Math10, Math12) |
| Emergent $SU(2)$ gauge via Route B (gauge-covariant Pauli channel) | `docs/supplementary/TECT-Pauli_Supplementary.tex.txt`; `docs/math/TECT-Math09.tex.txt` | Supersedes Route A (D-2026-04-15-06) |
| Emergent Lorentz $SO(3,1)$ via acoustic Cauchy relation | `docs/supplementary/TECT-Lorentz_Supplementary.tex.txt`; `docs/math/TECT-Math06.tex.txt` | $C_{44} = (C_{11}-C_{12})/2 + O(A^{4})$ |
| Heavy-mediator elimination identity (Class II) | `docs/math/TECT-Math15.tex.txt` L570–654; `docs/math/TECT-Math37.tex.txt` § UV | $\lambda_{\parallel} = \alpha_{X}^{2} q_{0}^{2}/(3 M_{X}^{2})$ |
| Four-class BCC pair-kernel exhaustiveness | `docs/math/TECT-Math31.tex.txt` | F-2026-04-15-04 rules out 3-parameter $(u,v,\kappa)$ |
| Witness-theorem framework (Dirac / mass-protection) | `docs/math/TECT-Math10.tex.txt`, `Math12.tex.txt`, `Math17.tex.txt` | Finite-audit reformulation in Math15 |
| Finite-audit reformulation of the carrier program | `docs/math/TECT-Math15.tex.txt` | Feeds Gate 1–4 certificate (Q-2026-04-15-02) |
| CKM toy model $|V_{us}| \approx 0.228$ | `docs/math/TECT-Math21.tex.txt` (+ Math22–Math23) | Full-precision CKM open (Q-2026-04-15-15) |
| Canonical locked basis — $3\times3$ minimum $S_{\min}$ | `docs/math/TECT-Math35.tex.txt` | Source-integrals $I_{\theta}$, $I_{\theta'^{3}}$ in Math34 |
| Three-generation fermion spectrum (Pillar 6) — **FALSIFIED-ANSATZ** (2026-04-20 v2) | `docs/math/TECT-Math49-rigorous-v2.tex.txt`; `docs/supplementary/Math49_hrr_v3.py`; `docs/supplementary/Math49_hrr_v3_output.txt` | Bott equivariant localisation with exact sympy arithmetic rules out $\chi=3$ for all integer $(a,b)$; refinements R1/R3/R4 open |
| Triangle-anomaly argument (Pillar 7 anomaly) — **PROVED@per-generation** (2026-04-20 v2) | `docs/math/TECT-Math49b-rigorous-v2.tex.txt` | All six coefficients $SU(3)^3, SU(2)^3, U(1)_Y^3, SU(3)^2 U(1), SU(2)^2 U(1), \text{Grav}^2 U(1)$ vanish via Abelian-leg reduction Lemma |
| Fermionic statistics (Pillar 7 spin-stat.) — **PROVED** (2026-04-20 v2) | `docs/math/TECT-Math49c-rigorous-v2.tex.txt` | FR theorem on $SO(3)/O$; order-4-in-$O$ lifts to order-8 in $2O$; $(\tilde R^{(100)}_{\pi/2})^4 = -\mathbb{1}$ explicit |
| Equivalence principle (Pillar 9) — **PROVED** (scalar + Dirac) (2026-04-20 v2) | `docs/math/TECT-Math_EP-rigorous-v2.tex.txt` | Dynamical $m_I = m_G$ via Belinfante–Rosenfeld improvement $T^{\text{imp},\mu\nu} = T^{\text{Hilb},\mu\nu}$; exponential-decay hypothesis for Dirac zero mode |
| Lorentz anisotropy bound (Pillars 2, 8) — **OUTLINE** (2026-04-20 v2) | `docs/math/TECT-Math_IR_Bound-rigorous-v2.tex.txt` | Correct $\mathcal{O}^{(c)}_4$; Gaussian $[g] = -3 < 0$ IR-irrelevant; Brazovskii $d_{\text{eff}} = 4$ outline; full Callan–Symanzik + numerical BZ integrals pending v3 |

## 2. Locked invariants

| Invariant | Value | Primary evidence | Correction history |
|---|---|---|---|
| $(\mu^{2},\lambda,\gamma)$ | $(0.26,\,-0.43,\,1.62)$ | Math38 three-eq matching; `PDE/config_template_brazovskii.json`; solver v3.1 defaults L207–209 | Pre-Math38 used $(0.25,\,+0.35,\,0.05)$ GL triple → F-2026-04-15-01; D-2026-04-15-01 records fit-as-derivation dead end |
| $\phi_0^{2}$ | $-4\lambda/(15\gamma) \approx 0.07078$ | Math37 AddA §A.2; extractor L619–625 | Previously $-2\lambda/(3\gamma)$ → F-2026-04-15-02 |
| $K_4$ | $1$ | Math37 AddA; extractor L616 | — |
| $K_6$ | $5/2$ | Math37 AddA §A.1; extractor L617 | Hessian coefficient $30\gamma\phi_0^4 \to 60\gamma\phi_0^4$ corrected at AddA |
| $I_3$ | $1/3$ | Math37 AddA §A.1 ($O_h$ invariance); extractor L646 | Previously un-fixed → F-2026-04-15-03 |
| $R_\mathrm{patch}$ | $45/16 \approx 2.81$ | Math37 AddA; extractor L654 onward | Compatibility shim for legacy 8-patch; see D-2026-04-15-03 |
| $m^{*2}_{\mathrm{TECT}}$ | $\approx 9.005$ | Math37 AddA closure; extractor L629–650 | Replaces retired $m^{*}=0.3138$ → R-2026-04-15-01 |
| $c_{1}(\mathrm{T}S^{2})$ | $2$ | Math07 transverse-phonon bundle integral | — |
| $N_{\mathrm{BCC}}$ (ground-state loop count) | $6$ | Math03 Theorem 3.2 | $N_{\mathrm{FCC}}=2$, $N_{\mathrm{SC}}=0$ |
| Acoustic Cauchy relation | $C_{44} = (C_{11}-C_{12})/2 + O(A^{4})$ | Math-Lorentz Supp §2; Math06 | Leading-order anisotropy suppressed by BCC $O_{h}$ |
| Kernel-rank deficit $\Delta_{\mathrm{ker}}$ | $32976$ | Math31 Theorem 2.3 | Disproves three-parameter pair kernel → F-2026-04-15-04 |
| Source integrals $I_{\theta}$, $I_{\theta'^{3}}$ | $-\sqrt{3}\pi\theta_{0}\kappa/16$; $-3\sqrt{3}\pi\theta_{0}^{3}\kappa^{3}/256$ | Math34 closed-form seed-profile overlaps | Feeds Math35 canonical basis |
| Finite extraction $\Delta_{00}$ | Math22 closed form | Math22 §3; Math23 Hessian projection | — |
| **Pillar 6 Q6a: 10-defect-moduli dimension identity (THEOREM 2026-04-24)** | `docs/math/TECT-Math80-Addendum-A-Q6a-10-moduli-theorem.tex.txt` (Lie-algebraic closure, Strategies 2+3 combined); `docs/math/TECT-Math80-Addendum-B-Q6a-equivariance-theorem.tex.txt` (topological closure, principal-fibration equivariance) | Proved BOTH Lie-algebraically and topologically. Lie-algebraic: $\dim(\mathfrak{g}_{\mathrm{PS}}/\mathfrak{g}_{\mathrm{SM}}) + \dim \mathfrak{u}(1)_{B-L} = 9 + 1 = 10 = \dim \mathbf{10}_{\mathrm{vec}}$. Topological: $\pi_1(M_{\mathrm{BCC}}) \mathrel{/\mkern-3mu/} \mathrm{SO}(10) \cong \mathbf{10}_{\mathrm{vec}}$ via principal $T^{11}$-fibration + equivariant lifting + per-charge-class dimension analysis. Both routes agree on $9 + 1$ decomposition and $G_{\mathrm{SM}}$-equivariant sub-content. Closes Q-2026-04-24-P6-Q6a-equivariance (Task #91). | Last reviewed: 2026-04-24 &nbsp;\|&nbsp; Review by: 2026-05-24 |

### 2.1 Boundary physical inputs (non-derived)

These three numerical inputs enter the mass-squared closure through
the Class-II contribution $\alpha_X^{2}\,q_0^{2}/M_X^{2}$ but are
*not* derived invariants in the §2 sense. Their provenance was
audited on 2026-04-15.

| Input | Runtime value | Primary evidence | Status | Last reviewed: 2026-04-15 &nbsp;\|&nbsp; Review by: 2026-06-15 |
|---|---|---|---|---|
| $q_0$ (Brazovskii shell) | $0.6801747616$ | Theory: `docs/math/TECT-Math01.tex.txt` L50, L210 (microscopic origin); protocol: `docs/math/TECT-Math38.tex.txt` (shell-mean measurement); runtime: `PDE/config_template_brazovskii.json` L9; code: `PDE/tect_actual_extractor_pt_v3.py` L638 | **Measured post-hoc** — extractor shell-mean wavenumber; measurement protocol is documented. | (Last reviewed: 2026-04-15 \| Review by: 2026-06-15) |
| $M_X$ (Class-II mediator mass) | $2.0$ | Theory: `docs/math/TECT-Math37.tex.txt` L40, L54, L77–79, L131, L200 (UV action); `docs/math/TECT-Math15.tex.txt` L570–591, L1027 (heavy-mediator elimination); runtime: `PDE/config_template_brazovskii.json` L37; code: `PDE/tect_actual_extractor_pt_v3.py` L639 | **Free parameter** — no first-principles RG / matching derivation of the numerical value. Open: Q-2026-04-15-06. | (Last reviewed: 2026-04-15 \| Review by: 2026-06-15) |
| $\alpha_X$ (Class-II coupling) | $0.3$ | Theory: `docs/math/TECT-Math37.tex.txt` L41, L77, L131, L200 (coupling in UV action); `docs/math/TECT-Math15.tex.txt` L590–591, L654, L1027 (shell-projected role); runtime: `PDE/config_template_brazovskii.json` L35; code: `PDE/tect_actual_extractor_pt_v3.py` L637, L641 | **Free parameter** — no microscopic derivation of the numerical value. Open: Q-2026-04-15-07. | (Last reviewed: 2026-04-15 \| Review by: 2026-06-15) |

> **Reviewer note**: the Class-II contribution
> $\alpha_X^{2}\,q_0^{2}/M_X^{2}$ therefore mixes one measured
> quantity with two phenomenological inputs. The $m^{*2}_\mathrm{TECT}
> \approx 9.005$ closure in §2 is conditional on these two free
> parameters; a first-principles derivation is tracked as an open
> question, not a closed claim.

## 3. Code design choices

| Design decision | Primary evidence | Related negative-result |
|---|---|---|
| Solver defaults hard-wired to Brazovskii (not runtime-overridable without `--config`) | `PDE/tect_solver_pt_v3.py` v3.1 L207–209; banner L747–753 | R-2026-04-15-02 (silent-GL bug this fix prevents) |
| `live_m_parallel.py` computes $m_\parallel$ live, no `None` default | `PDE/live_m_parallel.py` v1.0; Stage U2c in `run_pipeline_n1.py` | D-2026-04-15-02 (`m_parallel = None` pattern) |
| 12-constellation patch layout is canonical; 8-patch is legacy-only | Math37 AddA; extractor L615 | D-2026-04-15-03 |
| Module naming: `<module>_v<N>.py`; `_FINAL` forbidden | `docs/status/TECT-Theory-Code-Sync.md` §4 | `PDE/deprecated/` |

## 4. Infrastructure & governance

| Artefact | Primary evidence |
|---|---|
| Theory ↔ Code mapping | `docs/status/TECT-Theory-Code-Sync.md` |
| Update rulebook (trigger → target) | `docs/policy/UPDATE_POLICY.md` §1–§6 |
| Full-repo audit procedure | `docs/policy/UPDATE_POLICY.md` §7 |
| Negative-result discipline | `docs/policy/UPDATE_POLICY.md` §9; `docs/status/NEGATIVE-RESULTS.md` |
| Open questions discipline | `docs/policy/UPDATE_POLICY.md` §10; `docs/status/OPEN-QUESTIONS.md` |
| Evidence index (this file) | `docs/status/EVIDENCE-INDEX.md` |
| Git tag policy | `docs/policy/GIT_TAG_POLICY.md` |
| Per-run provenance | `PDE/tect_version_manifest.py`; `PDE/RESULT_TEMPLATE.md` |
| Version registries | `PDE/stamp_version_headers.py::MODULE_VERSIONS`; `Website/data/version_index.json`; `Website/data/timeline.json` |

## 4b. Reverse index — by file path

For questions of the form "what claims does file X support?", search
the forward rows above; the canonical reverse mapping is:

| Primary file | Supports (§.row) |
|---|---|
| `docs/math/TECT-Math01.tex.txt`–`Math05.tex.txt` | §1 BCC uniqueness, loop-count hierarchy |
| `docs/math/TECT-Math06.tex.txt`–`Math09.tex.txt` | §1 emergent $U(1)$ |
| `docs/math/TECT-Math10.tex.txt`–`Math14.tex.txt` | §1 Dirac node $\det H_D(0)=0$ |
| `docs/math/TECT-Math37.tex.txt` (+ AddA) | §2 $K_4$, $K_6$, $I_3$, $R_\mathrm{patch}$, $\phi_0^2$, $m^{*2}_\mathrm{TECT}$ |
| `docs/math/TECT-Math38.tex.txt` | §1 Brazovskii regime; §2 $(\mu^2,\lambda,\gamma)$; §2.1 $q_0$ measurement protocol |
| `docs/math/TECT-Math15.tex.txt` | §2.1 Class-II mediator formalism ($M_X$, $\alpha_X$) |
| `docs/math/TECT-Math37.tex.txt` (UV §1–§2) | §2.1 $M_X$, $\alpha_X$ defining action |
| `docs/papers/TECT_Paper_III_RankSelection.tex` | §1 rank-2 uniqueness (Prop 5.4) |
| `PDE/tect_solver_pt_v3.py` v3.1 | §3 solver Brazovskii defaults + banner |
| `PDE/tect_actual_extractor_pt_v3.py` v3.1 | §2 $\phi_0^2$, $K_4$, $K_6$, $I_3$, $m^{*2}_\mathrm{TECT}$ (L615–650) |
| `PDE/live_m_parallel.py` v1.0 | §3 live $m_\parallel$ computation |
| `PDE/config_template_brazovskii.json` | §2 $(\mu^2,\lambda,\gamma)$ locked triple (runtime) |
| `PDE/tect_c5_bcc_stability.py` | §1 BCC ground-state uniqueness |
| `PDE/projector_spectral.py` + `PDE/dirac_index_bcc.py` | §1 emergent $U(1)$ |
| `PDE/bloch_linearization.py` L137–141 | §1 Dirac node |
| `PDE/tect_rank_selection_v4.py` | §1 rank-2 uniqueness (numerical production) |
| `docs/math/TECT-Math06.tex.txt` | §1 emergent Lorentz (partial — see Q-2026-04-15-10); §2 Cauchy relation |
| `docs/math/TECT-Math07.tex.txt` | §1 $c_{1}(\mathrm{T}S^{2})=2$; §2 Chern number |
| `docs/math/TECT-Math10.tex.txt`–`Math17.tex.txt` | §1 witness-theorem framework; finite-audit reformulation |
| `docs/math/TECT-Math18.tex.txt`–`Math20.tex.txt` | §1 Clifford Cl(3) closure |
| `docs/math/TECT-Math21.tex.txt`–`Math23.tex.txt` | §1 CKM toy ($|V_{us}|\approx 0.228$); §2 $\Delta_{00}$ |
| `docs/math/TECT-Math24.tex.txt` | Q-2026-04-15-11 ($Z_{\mathrm{pol}}^{(T)}$ loop weight) |
| `docs/math/TECT-Math25.tex.txt`–`Math30.tex.txt` | Q-2026-04-15-14/15 (CKM convergence + precision fit) |
| `docs/math/TECT-Math26.tex.txt` | Q-2026-04-15-12/13 (C2 gravity + C3 gauge) |
| `docs/math/TECT-Math31.tex.txt` | §1 four-class kernel; §2 $\Delta_{\mathrm{ker}}=32976$; F-2026-04-15-04 |
| `docs/math/TECT-Math32.tex.txt`–`Math33.tex.txt` | F-2026-04-15-05; D-2026-04-15-05 |
| `docs/math/TECT-Math34.tex.txt` | §2 $I_{\theta}$, $I_{\theta'^{3}}$ |
| `docs/math/TECT-Math35.tex.txt` | §1 canonical locked basis $S_{\min}$; Q-2026-04-15-17 |
| `docs/supplementary/TECT-Pauli_Supplementary.tex.txt` | §1 Route B emergent $SU(2)$; D-2026-04-15-06 (Route A) |
| `docs/supplementary/TECT-Lorentz_Supplementary.tex.txt` | §1 Lorentz emergence; §2 Cauchy relation |
| `docs/supplementary/TECT-Nija_Tensor_Supplementary.tex.txt` | Nijenhuis tensor obstruction (integrability) |
| `docs/supplementary/TECT-U1_Gauge_Supplementary.tex.txt` | §1 $U(1)$ bundle obstruction on $S^{2}$ |

## 4c. Automation

| Tool | Role |
|---|---|
| `tools/check_review_cadence.py` | Scans §1–§3 `Last reviewed` / `Review by` dates and `OPEN-QUESTIONS.md` `## Active`. Returns non-zero under `--check` when any row is OVERDUE or missing a required date field. Invoked by §7 audit Layer 3. |
| `tools/build_version_index.py` | Regenerates `Website/data/version_index.json`; `--check` exits non-zero on drift. |
| `PDE/stamp_version_headers.py` | Re-stamps `__version__` / `__theory_version__` across live `PDE/*.py`. |

## 5. Reviewer Q&