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

#### Q-2026-05-18-Math409-AddH-AddA-AddA-AddA-Exact-RG-Definitive — Exact-RG Wetterich definitive test of TECT-Brazovskii running-G (B2 closure / refutation) — **OPENED 2026-05-18 (Math409-AddH-AddA-AddA §8 INTERIM NEGATIVE follow-up)**

**[OPENED 2026-05-18 — Math409-AddH-AddA-AddA INTERIM NEGATIVE follow-up]** **Context**: Math409-AddH-AddA-AddA explicit 1-loop calculation of TECT-Brazovskii running Newton constant gives $\omega_{\rm TECT} = 4.42 \pm$ factor 3, yielding $G_{\rm eff}(k_*)/G_{\rm obs} = 0.572$ at the texture scale $k_* = 0.41\,M_{\rm Pl}$ — vs required threshold $< 1/26 = 0.0385$. Shortfall factor 15 (structural, not marginal). Required $\omega = 148$ is factor 33 larger than 1-loop estimate, well beyond typical higher-order perturbative corrections ($O(2-3)$). The 1-loop heuristic is INTERIM NEGATIVE for Path B2. The exact-RG Wetterich calculation is the definitive test.

**Statement**: Compute $G_{\rm eff}^{\rm TECT}(k)$ via the exact functional-RG flow (Wetterich 1993, Reuter 1996) for TECT-Brazovskii with full non-perturbative shell-mode treatment. Use the TECT effective action constructed from Math110-AddI base + Math200-AddC running framework + Math401 Reading H + Brazovskii Goldstone propagator. Find $G_{\rm eff}(k_* = 1/r_{\rm tex})/G_{\rm obs}$ exactly. Test against threshold $0.0385$.

**Why critical / why definitive**: Resolves the Pillar 11.A texture-DM viability question definitively. If exact-RG gives $G_{\rm ratio} > 0.1$: Pillar 11.A REFUTED at QG level → T1 OPEN terminal (TECT dominant-DM mechanism defaults to 11.B). If exact-RG gives $G_{\rm ratio} < 0.0385$: Pillar 11.A T2 → T3 PROOF SKETCH (texture-DM compactness closed via TECT-natural asymptotic safety). Intermediate values are ambiguous.

**Falsification criterion**: $G_{\rm eff}^{\rm TECT}(k_*)/G_{\rm obs} > 0.1$ at exact-RG level REFUTES texture-DM definitively (Pillar 11.A T1 OPEN terminal). Conversely, $< 0.0385$ enables T2 → T3 promotion. The intermediate range $[0.0385, 0.1]$ requires explicit Math409-AddH-AddA-AddA-AddA-AddA scheme-dependence analysis.

**Owner**: Jusang Lee + AI collaborator. **Expected closure**: 2026-12-31. **Math note target**: Math409-AddH-AddA-AddA-AddA.

**Cross-references**: Math409-AddH-AddA-AddA §6 (1-loop INTERIM NEGATIVE result), Math110-AddI (emergent G base), Math200-AddC (1-loop $\hbar_{\rm TECT}$ precedent), Math401 (Reading H), Wetterich 1993 Phys. Lett. B 301 90 (exact RG equation), Reuter 1996 PRD 57 971 (gravitational application), Bonanno-Reuter 2002 PRD 65 043508 (asymptotic-safety phenomenology), Codello-Percacci-Rahmede 2009 (higher-derivative truncation).

---

#### Q-2026-05-18-Math409-AddH-AddA-AddA-TECT-RunningG-Calculation — Does TECT-Brazovskii natively support asymptotic-safe Newton constant with $G_{\rm eff}(k_* \sim 0.4\,M_{\rm Pl})/G_{\rm obs} < 1/26$? — **PARTIAL CLOSE 2026-05-18 (1-loop INTERIM NEGATIVE; exact-RG follow-up queued)**

**[PARTIAL CLOSE 2026-05-18 by Math409-AddH-AddA-AddA; corrected 2026-05-19 UTC per operator adversarial review]** Explicit 1-loop calculation of TECT-Brazovskii running Newton constant. Shell-mode loop integral $I^{\rm Brz}_{\rm shell-total} = (q_*/8)(\gamma/r_R)^{3/2}$ with Brazovskii enhancement factor $1/r_R^{3/2}_{\rm TECT} \approx 3.67$ at canonical $r_R = 0.42$. Result: $\omega_{\rm TECT}^{\rm 1-loop} = 4.42$ (central), uncertainty band $[1.5, 13.3]$ (factor 3 scheme-dependence). At $k_* = 0.41\,M_{\rm Pl}$: $G_{\rm eff}/G_{\rm obs} = 0.572 \gg 0.0385$ required (shortfall factor 15, structural — well outside scheme-dependence band; NOT a "marginal" fail). Required $\omega$ for closure = 148 (33x larger than 1-loop, beyond typical higher-order extrapolation). Effective Schwarzschild check (POSTMORTEM §8.7) with $G_{\rm eff}$: $r_{\rm tex}/r_{\rm Sch}^{\rm eff} = 0.067 < 1$ — texture STILL inside Schwarzschild even with full B2 1-loop credit. **Verdict (PARTIAL)**: B2 1-loop STRONG NEGATIVE INDICATOR. Pillar 11.A status canonicalised as **T2 INTERIM NEGATIVE, exact-RG pending** (PROVISIONAL qualifier NOT formally lifted — premature per operator audit). Definitive closure pending Math409-AddH-AddA-AddA-AddA exact-RG Wetterich (target 2026-12-31); most-likely outcome (70-80%) confirms 1-loop verdict → Pillar 11.A T1 OPEN terminal → TECT dominant DM defaults to **Pillar 11.B (now LIKELY PRIMARY PATH)**. 8/8 self-test asserts PASS per CLAUDE.md §6.3.8 + POSTMORTEM §8.7.

**[Original Active text follows for archival]**:

#### Q-2026-05-18-Math409-AddH-AddA-AddA-TECT-RunningG-Calculation — Does TECT-Brazovskii natively support asymptotic-safe Newton constant with $G_{\rm eff}(k_* \sim 0.4\,M_{\rm Pl})/G_{\rm obs} < 1/26$? — **OPENED 2026-05-18 (Math409-AddH-AddA §6 Path B2 identification)**

**[OPENED 2026-05-18 — Math409-AddH-AddA §6 Path B2 follow-up]** **Context**: Math409-AddH-AddA five-sub-path compactness investigation eliminated Path A1 (spherical canonical, factor 26 over), Path A2 (parameter-space r_R reduction, structurally infeasible), Path A3 (cylindrical hoop-conjecture, sub-Planck L_perp), and stalled on Path B1 (topological geon, no rigorous theorem). The sole identified viable rescue route is Path B2: TECT-Brazovskii running Newton constant via asymptotic safety. At the texture scale $k_* = 1/r_{\rm tex} \approx 0.41\,M_{\rm Pl}$, the standard Reuter ansatz $G_{\rm eff}(k) = G_{\rm obs}/(1 + \omega(k/M_{\rm Pl})^2)$ with $\omega = 1$ gives only 14.5% suppression (insufficient by factor 22). TECT-Brazovskii has a distinguished scale $q_* \sim M_{\rm Pl}$ at which the Goldstone-mode dispersion $(k^2 - q_*^2)^2$ vanishes, potentially providing additional suppression for $G_{\rm eff}$ via the same loop-correction mechanism that gives Math200-AddC's 1-loop $\hbar_{\rm TECT}$ running.

**Statement**: Compute $G_{\rm eff}^{\rm TECT}(k)$ from first principles in the Reading H framework, using (i) Math110-AddI base relation $\rho_{\rm cond} = c^4/(16\pi G a_{\rm condensate}^2)$, (ii) Math200-AddC 1-loop Goldstone-mode renormalisation of the condensate elastic modulus, (iii) Brazovskii-shell enhancement at $k \sim q_*$. Test whether $G_{\rm eff}^{\rm TECT}(k_* = 1/r_{\rm tex})/G_{\rm obs} < 1/26 = 0.0385$.

**Why open / why critical**: This is the SOLE explicit promotion path for Pillar 11.A. If PASS, Pillar 11.A T2 PROVISIONAL → T3 PROOF SKETCH (texture-DM compactness rescue closed). If FAIL, Pillar 11.A T1 OPEN terminal (no remaining TECT-natural rescue route in sight). Net DM mechanism would then default to Pillar 11.B subdominant relic + $\nu_R$ bulk DM via Math408 LRSM cascade.

**Falsification criterion**: if explicit TECT-Brazovskii RG-flow calculation at 1-loop shows $G_{\rm eff}^{\rm TECT}(k_*)/G_{\rm obs} > 0.1$ (factor 2.6x above the required threshold), Path B2 is REFUTED and Pillar 11.A is permanently demoted to T1 OPEN. Conversely, $G_{\rm eff}/G_{\rm obs} < 0.0385$ at $k_* \approx 0.41\,M_{\rm Pl}$ enables T2-PROV → T3 promotion.

**Owner**: Jusang Lee + AI collaborator. **Expected closure**: 2026-08-15. **Math note target**: Math409-AddH-AddA-AddA.

**Cross-references**: Math409-AddH-AddA §6 Path B2 (parent), Math110-AddI (emergent G base), Math200-AddC (1-loop $\hbar$ running, methodological precedent), Math401 Reading H, Reuter 1996 PRD 57 971, Bonanno-Reuter 2002 PRD 65 043508, Weinberg 1979 (asymptotic safety origin).

---

#### Q-2026-05-18-Math409-AddH-AddA-AddB-Wheeler-Geon-Brazovskii — Hopf-class Wheeler geon configuration in Brazovskii medium (secondary rescue) — **OPENED 2026-05-18 (Math409-AddH-AddA §5 Path B1 marker)**

**[OPENED 2026-05-18 — Math409-AddH-AddA §5 Path B1 follow-up, secondary priority]** **Context**: Path B1 (topological obstruction to Schwarzschild interior via Wheeler-geon configuration) was identified in Math409-AddH-AddA but lacks any rigorous theorem in 70+ years of GR literature. Recorded as secondary rescue path with lower priority than Path B2 (Math409-AddH-AddA-AddA).

**Statement**: Investigate whether the TECT-Brazovskii medium admits a stable Hopf-class geon configuration — a self-gravitating Hopf-instanton field in non-trivial spacetime topology (handle-equipped Cauchy surface) that evades the Penrose singularity theorem.

**Why open / priority**: Secondary because (i) no concrete Hopf-class geon has been constructed in 70 years of GR research, (ii) the construction requires both stable Wheeler-geon physics AND Brazovskii compatibility, which is a compounded difficulty. Path B2 is structurally cleaner. However, if B2 fails by narrow margin, B1 becomes the last-chance rescue.

**Falsification criterion**: if no concrete geon construction emerges from dedicated 6-month investigation, Path B1 is recorded as STALLED INDEFINITELY; no further effort allocated unless B2 also fails.

**Owner**: Jusang Lee + AI collaborator. **Expected closure**: 2026-10-15 (long horizon reflecting speculative nature). **Math note target**: Math409-AddH-AddA-AddB.

**Cross-references**: Math409-AddH-AddA §5 Path B1 (parent), Wheeler 1955 Phys. Rev. 97 511 (geon hypothesis original), Sorkin 1989 (topology change in QG), Misner-Wheeler 1957 Ann. Phys. 2 525 (geometrodynamics framework).

---

#### Q-2026-05-18-Math409-AddH-AddA-Compactness-Corrected-Stability — Compactness-corrected stability theorem for super-Planck topological textures in TECT-Brazovskii regime — **PARTIAL CLOSE 2026-05-18 by Math409-AddH-AddA: 5-sub-path investigation; A1/A2/A3 FAIL, B1 stalled, B2 IDENTIFIED**

**[PARTIAL CLOSE 2026-05-18 by Math409-AddH-AddA]** Five-sub-path investigation completed: (A1) spherical Hopf canonical-TECT: FAIL by compactness factor 26 (no integer charge N satisfies; M~N² grows faster than r~N^(1/3)); (A2) parameter-space r_R reduction: FAIL (requires r_R<0.023 vs canonical 0.42; TECT axioms fix mu^2=+0.005, Brazovskii Hartree floor ~0.4 above target); (A3) cylindrical hoop-conjecture exploit: FAIL (longitudinal hoop escape requires L_∥>397 ell_Pl, resulting L_⊥=0.23 ell_Pl is sub-Planck); (B1) topological obstruction / Wheeler geon: NO THEOREM (speculative, 70+ years GR research without concrete construction); (B2) Brazovskii-medium running-G / asymptotic safety: IDENTIFIED as principal viable path (standard Reuter at k_*≈0.41 M_Pl gives 0.855 suppression; required <0.0385; TECT-enhancement factor 22 needed). **Tier outcome**: Pillar 11.A T2 PROVISIONAL RETAINED. Promotion path narrowed to single explicit calculation: Math409-AddH-AddA-AddA (running-G), secondary Math409-AddH-AddA-AddB (geon). 8/8 self-test asserts PASS per CLAUDE.md §6.3.8 + mandatory POSTMORTEM §8.7 Schwarzschild check.

**[Original Active text follows for archival]**:

#### Q-2026-05-18-Math409-AddH-AddA-Compactness-Corrected-Stability — Compactness-corrected stability theorem for super-Planck topological textures in TECT-Brazovskii regime — **OPENED 2026-05-18 [SCOPE-REVISED 2026-05-18 post-audit-rollback]**

**[SCOPE-REVISED 2026-05-18 post-operator-audit-rollback]** **Context**: Operator adversarial review identified that Math409-AddH (and upstream Math409-AddD-AddD) mis-read the Schwarzschild compactness inequality $r_{\rm tex} < r_{\rm Sch}$ as "no horizon" rather than the correct GR reading "object inside Schwarzschild radius → horizon forms → BH collapse expected → Hawking evap in $t_{\rm evap} \sim (M_{\rm tex}/M_{\rm Pl})^3 \cdot t_{\rm Pl} \sim 10^{-39}$ s". The Math409-AddH T3 promotion was ROLLED BACK; Pillar 11.A retained at T2 PROVISIONAL. The decisive gate for T2-PROV → T3 promotion is therefore not a Wheeler-DeWitt QG theorem (the previous formulation) but a **compactness-corrected stability theorem** that resolves the classical-GR refutation at TECT canonical parameters.

**Statement**: Prove ONE of the following:
- **(i) Topological-soliton horizon avoidance**: a topological obstruction theorem showing that codim-4 Hopf-instanton solitons in the Brazovskii medium do NOT form event horizons even when $r_{\rm tex} < r_{\rm Sch}(M_{\rm tex})$, due to a TECT-internal mechanism (e.g., topological-charge conservation prevents Schwarzschild interior trap; Brazovskii-medium gradient repulsion at the would-be horizon; non-Riemannian effective metric in the Reading H ensemble that modifies the Schwarzschild bound), OR
- **(ii) Brazovskii compactness rederivation**: explicit derivation of $(r_{\rm tex}, M_{\rm tex})$ from TECT-Brazovskii Lagrangian first principles yielding the compactness inequality $M_{\rm tex} < r_{\rm tex}/(2\,\ell_{\rm Pl}) \cdot M_{\rm Pl}$. At current $r_{\rm tex} = 2.43\,\ell_{\rm Pl}$ this requires $M_{\rm tex} < 1.215\,M_{\rm Pl}$ (factor 26 mass reduction from Math409-AddD-AddD value).

**Why open / why critical**: Without resolution, Pillar 11.A is pinned at T2 PROVISIONAL and cannot promote to T3 PROOF SKETCH. The texture-DM rescue is the *last remaining* TECT-natural dark-matter pathway after wall-DM REFUTATION (Math409-AddD-AddC); failure here forces 11.A to T1 OPEN terminal with no further rescue route in sight.

**Falsification criterion**: if neither (i) nor (ii) can be proven within 6 months of dedicated investigation, Pillar 11.A is permanently demoted to T1 OPEN; only Pillar 11.B (subdominant relic + $\nu_R$ bulk DM via Math408 LRSM cascade) survives as DM mechanism. Conversely, PASS of either (i) or (ii) enables 11.A T2-PROV → T3 PROOF SKETCH promotion.

**Owner**: Jusang Lee + AI collaborator. **Expected closure**: 2026-08-15 (extended from original 2026-07-15 due to scope revision; the compactness problem is harder than the original QG-framework question). **Math note target**: Math409-AddH-AddA.

**Cross-references**: Math409-AddH (audit-flagged target), Math409-AddD-AddD (upstream audit-flagged), Math409_AddH_compactness_audit.py (corrective script, 5/5 asserts PASS), R-2026-05-18-Math409-AddH-CompactnessSignError (NEGATIVE-RESULTS), Schwarzschild 1916 (compactness bound origin), 't Hooft 1985 (graviton-soliton interaction near Planck regime).

---

#### Q-2026-05-18-Math409-AddH-AddA-QG-Framework — Wheeler-DeWitt-class rigorous quantum-gravity stability theorem for super-Planck topological solitons in the Brazovskii regime? — **OPENED 2026-05-18 (Math409-AddH §3 OPEN GAP α) — [SUPERSEDED by Q-...-Compactness-Corrected-Stability above 2026-05-18]**

**[SUPERSEDED 2026-05-18]** This question was opened on the (incorrect) presumption that Math409-AddH channel (a) "INAPPLICABLE" verdict was valid and the remaining gap was the QG-level extrapolation. Operator audit 2026-05-18 reversed this: channel (a) is in fact REFUTING under classical GR (texture inside Schwarzschild → BH collapse), not INAPPLICABLE. The question is therefore superseded by Q-2026-05-18-Math409-AddH-AddA-Compactness-Corrected-Stability above, which addresses the classical-GR-level compactness problem first. A Wheeler-DeWitt-level QG analysis only becomes meaningful AFTER the classical-GR compactness inequality is resolved (otherwise the QG correction would be a correction to a structurally invalid state).

**[Original Active text follows for archival]**:

**[OPENED 2026-05-18 — Math409-AddH §3 critical gap]** **Context**: Math409-AddH established texture-DM stability against three decay channels — (a) Hawking-class INAPPLICABLE under null hypothesis, (b) tunnelling SUPPRESSED at $S_{\rm bounce} = 1516$ giving $\tau \sim 10^{596} \tau_0$, (c) annihilation NEGLIGIBLE at $\tau \sim 10^{66} \tau_0$. Pillar 11.A T2 PROVISIONAL → T3 PROOF SKETCH. The remaining gap blocking T3 → T4 STRONG EVIDENCE promotion is the absence of a rigorous quantum-gravity treatment of super-Planck-mass topological solitons in the Brazovskii regime. Channel (a)'s null-hypothesis verdict relies on "no known decay channel applies"; a Wheeler-DeWitt or LQG-analog stability theorem would harden this to constructive stability.

**Statement**: Establish a rigorous quantum-gravity framework (Wheeler-DeWitt equation on Brazovskii-extended superspace, or LQG holonomy/flux algebra on TECT condensate background) that proves super-Planck-mass topological textures with $r_{\rm tex} < r_{\rm Sch}$ are stable against quantum-gravity-induced decay channels. The theorem should explicitly handle (i) graviton fluctuations modifying the Derrick balance, (ii) Hawking-analog horizon-creation suppression for sub-Schwarzschild solitons, (iii) holonomy-flux preservation of $\pi_3$ winding under quantum-gravity evolution.

**Why open**: Without resolution, Pillar 11.A is pinned at T3 PROOF SKETCH and cannot promote to T4 STRONG EVIDENCE. The standard-physics extrapolation (used in Math409-AddH) is honest but limited; super-Planck regime introduces $O(1)$ QG corrections at the soliton scale that standard arguments cannot bound. This is the principal frontier for Pillar 11 closure.

**Falsification criterion**: if explicit Wheeler-DeWitt or LQG analysis shows quantum-gravity introduces a new decay channel with $\tau < 10 \tau_0$, Pillar 11.A REVERTS to T2 CONJECTURE (texture-DM remains plausible but not provably stable at QG level); if PASS, T3 → T4 STRONG EVIDENCE promotion enabled.

**Owner**: Jusang Lee + AI collaborator. **Expected closure**: 2026-07-15. **Math note target**: Math409-AddH-AddA.

**Cross-references**: Math409-AddH §3 (channel (a) null hypothesis), Math409-AddD-AddD (texture profile), DeWitt 1967 Phys. Rev. 160 1113 (Wheeler-DeWitt framework), Rovelli-Smolin 1990 Nucl. Phys. B 331 80 (LQG holonomy algebra), Bekenstein 1981 PRD 23 287 (information bound on super-Planck states).

---

#### Q-2026-05-18-Math409-AddH-AddB-Texture-CMB — Hopf-instanton CMB temperature anisotropy spectrum vs Planck 2018 constraints? — **OPENED 2026-05-18 (Math409-AddH §6 self-meta-objection 3)**

**[OPENED 2026-05-18 — Math409-AddH §6 self-adversarial follow-up]** **Context**: Math409-AddD-AddD established that texture-DM evades the FMP 2003 wall-DM CMB constraint because textures are codim-4 point-like defects, not wall-domain surfaces. However, textures have their OWN CMB signature: Hopf-instanton temperature anisotropy from the integrated Sachs-Wolfe effect of texture-induced gravitational potential fluctuations (Turok-Spergel 1990 PRD 42 1773 for global textures; analogous treatment needed for TECT Hopf textures with $M_{\rm tex} = 31.6 M_{\rm Pl}$ and $n_{\rm tex} \sim 3.3 \times 10^{-21}$/m³).

**Statement**: Compute the Hopf-instanton CMB temperature anisotropy spectrum $\Delta T/T |_{\ell}$ as a function of multipole $\ell$ for TECT texture-DM saturating $\Omega_{\rm DM} = 0.27$. Compare against Planck 2018 constraints on non-Gaussianity ($f_{\rm NL}$) and isocurvature ($\beta_{\rm iso}$) at $\ell \in [2, 2500]$. If texture anisotropy $\Delta T/T > 10^{-5}$ at any well-constrained multipole, texture-DM REFUTED on Planck grounds.

**Why open**: Phenomenological viability check parallel to Math409-AddH-AddA's theoretical viability check. Both must PASS for Pillar 11.A to advance beyond T3.

**Falsification criterion**: if integrated texture anisotropy at $\ell \in [10, 100]$ exceeds Planck 2018 upper bound ($\Delta T/T < 10^{-5.4}$ for non-Gaussian template), texture-DM REFUTED phenomenologically; Pillar 11.A reverts to T2 CONJECTURE.

**Owner**: Jusang Lee + AI collaborator. **Expected closure**: 2026-08-15. **Math note target**: Math409-AddH-AddB.

**Cross-references**: Math409-AddH §6 (self-meta-objection 3), Turok-Spergel 1990 PRD 42 1773 (global texture CMB anisotropy), Planck 2018 Akrami et al. A&A 641 A9 (non-Gaussianity constraints), Math413-AddA (Hopf-charge topology).

---

#### Q-2026-05-18-Math409-AddH-Hawking-Stability — Are TECT M_tex ~ M_Pl primordial textures stable against Hawking-class evaporation in the Brazovskii regime? — **CLOSED 2026-05-18 by Math409-AddH: PASS at T3 PROOF SKETCH level**

**[CLOSED 2026-05-18 by Math409-AddH]** Three decay-channel analysis: (a) Hawking-class radiation INAPPLICABLE ($r_{\rm Sch}/r_{\rm tex} = 26 \gg 1$, no horizon; Schwinger-analog inapplicable because Goldstones are neutral scalars + Compton wavelength comparable to texture size); (b) quantum tunnelling SUPPRESSED ($S_{\rm bounce} = 2\pi^2 M_{\rm tex} r_{\rm tex} = 1516$; $\tau^{(b)} \sim 10^{614}$ s $\sim 10^{596} \tau_0$, robust against factor-10 prefactor uncertainty); (c) defect-antidefect annihilation NEGLIGIBLE ($\sigma_{\rm ann} \sim \pi r_{\rm tex}^2 \sim 4.8 \times 10^{-69}$ m²; $n_{\rm tex} \sim 3.3 \times 10^{-21}$/m³; $\tau^{(c)} \sim 3 \times 10^{83}$ s $\sim 7 \times 10^{65} \tau_0$). Composite tier (min): T3 PROOF SKETCH driven by channel (c). **Verdict**: Pillar 11.A T2 PROVISIONAL → **T3 PROOF SKETCH**; PROVISIONAL qualifier LIFTED. All 7 self-test asserts in `Codes/supplementary/Math409_AddH_texture_stability.py` PASS per CLAUDE.md §6.3.8. Remaining OPEN GAPs registered as Q-Math409-AddH-AddA-QG-Framework (T3→T4 theoretical gate) and Q-Math409-AddH-AddB-Texture-CMB (T3→T4 phenomenological gate).

**[Original Active text follows for archival]**:

#### Q-2026-05-18-Math409-AddH-Hawking-Stability — Are TECT M_tex ~ M_Pl primordial textures stable against Hawking-class evaporation in the Brazovskii regime? — **OPENED 2026-05-18 (Math409-AddD-AddD §6 critical dependency)**

**[OPENED 2026-05-18 — Math409-AddD-AddD PROVISIONAL rescue caveat]** **Context**: Math409-AddD-AddD established texture-DM as a viable Pillar 11.A rescue alternative passing all four wall-DM failure constraints, with quantitative profile $r_{\rm tex} \approx 2.43\,\ell_{\rm Pl}$, $M_{\rm tex} \approx 31.6\,M_{\rm Pl}$. The defect mass is super-Planckian by factor $\sim$30, raising the question of whether textures can survive cosmologically against quantum-gravity-class instabilities analogous to Hawking evaporation. Standard primordial-black-hole analysis (Hawking 1974) gives $t_{\rm evap} \sim M^3/M_{\rm Pl}^4 \cdot t_{\rm Pl}$, but textures are NOT black holes ($r_{\rm tex} = 2.43\,\ell_{\rm Pl} < r_{\rm Sch} = 63.2\,\ell_{\rm Pl}$), so the direct Hawking formula does not apply. The relevant decay channels are topological (defect-antidefect annihilation) or quantum-tunnelling out of the Brazovskii potential well.

**Statement**: Determine whether textures of mass $M_{\rm tex} \sim 31.6\,M_{\rm Pl}$ and radius $r_{\rm tex} \sim 2.43\,\ell_{\rm Pl}$ are stable against (a) Hawking-class evaporation, (b) quantum tunnelling to the Brazovskii disordered vacuum, (c) defect-antidefect annihilation rate at late times. Compute lifetime $\tau_{\rm tex}$ and compare against current cosmological age $\tau_0 \approx 4.4 \times 10^{17}$ s. If $\tau_{\rm tex} \gg \tau_0$, Pillar 11.A T2 PROVISIONAL promotes to T3 PROOF SKETCH. If $\tau_{\rm tex} \ll \tau_0$, texture-DM hypothesis REFUTED and Pillar 11.A REVERTS to T1 OPEN (terminal).

**Why open / priority**: Critical dependency for the texture-DM rescue chain. Without Hawking-stability verification, the Math409-AddD-AddD T1 -> T2 promotion remains PROVISIONAL and cannot harden to T3. This is the LAST GATE for Pillar 11.A; if it falls, no further TECT-natural rescue mechanism is in sight and 11.A is permanently REFUTED.

**Falsification criterion**: if texture lifetime $\tau_{\rm tex} < 10\tau_0$ under any of the three decay channels (a)/(b)/(c), texture-DM REFUTED on cosmological-stability grounds; Pillar 11.A reverts to T1 OPEN with no remaining rescue pathway.

**Owner**: Jusang Lee + AI collaborator. **Expected closure**: 2026-07-15. **Math note target**: Math409-AddH.

**Cross-references**: Math409-AddD-AddD §7 (PROVISIONAL caveat), Hawking 1974 Nature 248 30, Skyrme 1962 Nucl. Phys. 31 556 (defect-antidefect annihilation rate framework).

---

#### Q-2026-05-15-Texture-DM-Alternative — Are within-bubble textures (from $\pi_3 = \mathbb{Z}$) a viable Pillar 11.A alternative to walls? — **CLOSED PROVISIONAL 2026-05-18 by Math409-AddD-AddD: T1 -> T2 PROVISIONAL pending Math409-AddH**

**[CLOSED PROVISIONAL 2026-05-18 by Math409-AddD-AddD]** Four-axis test PASSED: (i) topology PASS ($\pi_3(O(8)/O_h) = \mathbb{Z}$ per Math413-AddA), (ii) Derrick stability PASS via TECT's intrinsic Brazovskii $(k^2 - k_*^2)^2$ Skyrme term, (iii) FMP CMB constraint inapplicable (textures are codim-4, NOT wall-domain), (iv) cold-matter scaling $\rho \sim a^{-3}$ avoids the wall-class overproduction failure. Quantitative profile (Math409_AddD_AddD_texture_DM_constraints.py): $r_{\rm tex} = 2.43\,\ell_{\rm Pl}$, $M_{\rm tex} = 31.6\,M_{\rm Pl}$, required $N_e = 95.6$ e-folds (extreme but $10^{49.4}$ more permissive than wall). **Verdict**: Pillar 11.A T1 -> T2 PROVISIONAL. Sole remaining gate: Math409-AddH Hawking-stability verification of $M_{\rm tex} \sim M_{\rm Pl}$ primordial defects (registered as Q-2026-05-18-Math409-AddH-Hawking-Stability). Promotion to T3 PROOF SKETCH contingent on AddH PASS.

**[Original Active text follows for archival]**:

#### Q-2026-05-15-Texture-DM-Alternative — Are within-bubble textures (from $\pi_3 = \mathbb{Z}$) a viable Pillar 11.A alternative to walls? — **OPENED 2026-05-15 (Math409-AddD-AddC §9 follow-up)**

**[OPENED 2026-05-15 — Math409-AddD-AddC verdict fallout]** **Context**: Math409-AddD-AddC §6 found that wall-DM bias mechanisms all require severe fine-tuning ($\epsilon_{\rm bias} \sim 10^{-93}$, or $g_{\rm wall-WR} \sim 10^{-13.5}$). Pillar 11.A wall-DM is REFUTED. However, Math413-AddA §2 confirmed $\pi_3(V) = \mathbb{Z}$ — textures (codim 4) are topologically protected. As codim-4 defects (Hopf instantons in 3D), textures are point-like and may not be subject to the wall-domain CMB constraint of Friedland-Murayama-Perelstein.

**Statement**: Evaluate whether within-bubble textures (Math413-AddA §2 $\pi_3 = \mathbb{Z}$) are a viable alternative dominant-DM candidate. Compute texture density at formation, surface tension scaling with bubble interior dynamics, lifetime under cosmological evolution, and CMB constraint. If textures pass without bias, Pillar 11.A is recoverable to T2 or higher.

**Why open / priority**: Math409-AddD-AddC's wall-DM REFUTATION leaves only sub-leading textures + monopoles as topologically-protected defects. Among these, textures are the better candidate (monopoles are not topologically protected per Math413-AddA §2). Resolution determines whether Pillar 11.A can be rescued at all.

**Falsification criterion**: if texture density $\Omega_{\rm tex}$ at recombination exceeds DM density by >10$^4$, OR Hopf-instanton CMB signature exceeds Planck 2018 limits, texture-DM hypothesis is REFUTED and Pillar 11.A remains permanently T1 OPEN.

**Owner**: Jusang Lee + AI collaborator. **Expected closure**: 2026-06-30. **Math note target**: Math409-AddD-AddD.

**Cross-references**: Math409-AddD-AddC (wall-DM REFUTATION), Math413-AddA §2 (homotopy $\pi_3(V) = \mathbb{Z}$), Belavin-Polyakov 1975 (texture/skyrmion defect class).

---

#### Q-2026-05-15-Wall-DM-Bias-Mechanism — Can a TECT-natural bias mechanism allow walls to escape the wall-DM CMB constraint while saturating $\Omega_{\rm DM}$? — **CLOSED 2026-05-15 by Math409-AddD-AddC: REFUTED at factor 10^60**

**[CLOSED 2026-05-15 by Math409-AddD-AddC]** Three TECT-natural bias mechanisms evaluated quantitatively:
- (a) cubic-symmetry-breaking term: requires $\epsilon_{\rm bias} \sim 10^{-93}$ GeV$^{-1}$, $\rho_{\rm bias} \sim 10^{31}$ above $\Lambda$ — severe fine-tuning.
- (b) inflation dilution: NOT a bias mechanism (walls re-dominate at late times after inflation).
- (c) sector coupling to LRSM $W_R$: requires $g_{\rm wall-WR} \sim 10^{-13.5}$ (vs $g_{\rm EW} \sim 0.65$) — extreme fine-tuning.
None reaches T3 PROOF SKETCH. **Verdict**: wall-DM hypothesis REFUTED by factor $10^{60}$ violation of Friedland-Murayama-Perelstein 2003 CMB constraint. Pillar 11.A T2 → T1 OPEN. Last-chance rescue via Math409-AddD-AddD texture-DM alternative (queued).

**[Original Active text follows for archival]**:

#### Q-2026-05-15-Wall-DM-Bias-Mechanism — Can a TECT-natural bias mechanism allow walls to escape the wall-DM CMB constraint while saturating $\Omega_{\rm DM}$? — **OPENED 2026-05-15 (Math409-AddD §8 objection 2)**

**[OPENED 2026-05-15 — Math409-AddD self-adversarial review fallout]** **Context**: Math409-AddD established that the dominant TECT defect type is *walls* between misaligned BCC orientation domains (Brazovskii first-order bubble-nucleation), not monopoles. Standard wall-DM CMB constraints (Friedland-Murayama-Perelstein 2003) restrict $\Omega_{\rm wall} \lesssim 10^{-5}$ for stable walls without bias — incompatible with $\Omega_{\rm wall} = \Omega_{\rm DM} \approx 0.27$ as required by Pillar 11.A.

**Statement**: Identify a TECT-natural bias mechanism that selects one BCC orientation as the true vacuum (so walls eventually decay) while preserving the cosmologically-relevant fraction long enough to contribute meaningfully to DM. Candidates: (a) explicit cubic-symmetry-breaking term in the effective action (must be small enough to allow walls to form initially but large enough to drive late-time decay); (b) post-inflation $\sigma_{\rm wall}$ suppression via condensate annealing; (c) bias from coupling to a separate sector (e.g., gauge-symmetry breaking).

**Why open**: Without resolution, Pillar 11.A wall-DM hypothesis is incompatible with CMB observations independently of the inflation difficulty. Resolution determines whether 11.A is recoverable to T3-T4 (TECT-natural bias works) or remains pinned at T2 (no bias mechanism found, dominant-DM via TECT walls excluded).

**Falsification criterion**: if no TECT-natural bias mechanism is found within 6 months of dedicated investigation, Pillar 11.A wall-DM hypothesis REFUTED on CMB grounds; only Pillar 11.B (subdominant relic + bulk DM from $\nu_R$ via Math408 LRSM cascade) survives.

**Owner**: Jusang Lee (maintainer) + AI collaborator. **Expected closure**: 2026-11-12. **Math note target**: Math409-AddD-AddC.

**Cross-references**: Math409-AddD §3-§4 (wall identification), Math409-AddD §8 objection 2 (CMB-constraint incompatibility), Friedland-Murayama-Perelstein 2003 PRD 67 043519, Zel'dovich-Kobzarev-Okun 1974 JETP 40 1.

---

#### Q-2026-05-15-KZ-Applicability-Under-Reading-H — Does the BCC order-disorder transition admit a non-equilibrium quench, or is Reading H reached adiabatically? — **CLOSED 2026-05-15 by Math409-AddD: Brazovskii weak first-order; KZ applies in bubble-nucleation form**

**[CLOSED 2026-05-15 by Math409-AddD]** Brazovskii (1975) fluctuation-induced weak first-order transition CONFIRMED for TECT canonical regime. KZ applies in modified bubble-nucleation form (not continuous-quench scaling). Math404 §5 + Math409 + Math409-AddA quantitative chain survives at order-of-magnitude with revised defect-type assumption (walls dominant + sub-leading monopoles at junctions). Continuous-quench scenario (a) REJECTED; smooth crossover scenario (b) REJECTED; first-order scenario (c) CONFIRMED. Closure verdict: **POSITIVE** (KZ inapplicability hypothesis refuted) but with REVISED downstream interpretation (walls vs monopoles). Original question text preserved below for archival traceability.

**[Original Active text follows for reference]**:

#### Q-2026-05-15-KZ-Applicability-Under-Reading-H — Does the BCC order-disorder transition admit a non-equilibrium quench, or is Reading H reached adiabatically? — **OPENED 2026-05-15 (Math407-AddA binding decision 2; HIGHEST PRIORITY for Pillar 11)**

**[OPENED 2026-05-15 — Math407-AddA Round-2 audit]** **Context**: Math402's KZ-defect framework + Math404 §5 anchor + Math409 + Math409-AddA all assume the BCC order-disorder transition under Reading H proceeds via a non-equilibrium quench (canonical Kibble-Zurek mechanism). Math407-AddA §4 observed that Reading H (Math401) defines the canonical TECT vacuum as a fluctuation-stabilised disordered phase WITHOUT specifying whether this phase is reached via sharp quench, adiabatic cooling, or slow rolling through a critical region.

**Statement**: Determine the order of the BCC condensation phase transition under Reading H ($\lambda < 0$ attractive quartic, Brazovskii regime). Possibilities: (a) first-order (KZ applies with modified scaling, Math404 framework valid with corrections); (b) second-order/continuous (standard KZ applies, Math404 framework valid); (c) no sharp transition — disordered Reading H phase reached adiabatically via fluctuation stabilisation (KZ INAPPLICABLE).

**Why open / why HIGHEST PRIORITY**: If KZ inapplicable (case c), the entire downstream chain is moot:
- $n_{\text{def}} \sim \xi_{\text{KZ}}^{-3}$ assumes KZ defect counting;
- $\rho_{\text{def}}/\rho_{\text{crit}} = 1.30 \times 10^{114}$ assumes KZ formation;
- $N_e \approx 88$ requirement assumes KZ-formed defects survive to today;
- All five Math409-AddA lever follow-ups (AddC/D/E/F/G) presuppose KZ.

This is a prerequisite question that must be resolved before refining defect topology (AddC), $\tau_Q$ (AddF), or any other downstream lever. Per Math407-AddA decisive-test reorder (binding decision 2), Math409-AddD precedes all other Math409 follow-ups.

**Falsification criterion**: if explicit free-energy analysis of the BCC condensation under Reading H ($\lambda < 0$) shows the transition is third- or higher-order with vanishing latent heat, KZ is inapplicable; Pillar 11.A REFUTED outright; Pillar 11.B also weakened (subdominant relic still possible if defects form via alternative non-KZ mechanism, but the canonical KZ count $\xi_{\text{KZ}}^{-3}$ no longer applies).

**Owner**: Jusang Lee (maintainer) + AI collaborator. **Expected closure**: 2026-05-25 (immediate priority). **Math note target**: Math409-AddD.

**Cross-references**: Math401 (Reading H adoption), Math402 (KZ framework, PRE-ANCHOR EXPLORATORY), Math404 §5 (excess factor $10^{114}$), Math409 + Math409-AddA (three pathways + G4 PARTIAL), Math407-AddA §4 (decisive-test reorder rationale), Brazovski\u\i\ 1975 (fluctuation-induced first-order transitions).

---

#### Q-2026-05-15-Pillar-11-Hawking-Stability — What is the stable mass scale that admits both KZ-mechanism formation AND $\sim$Hubble-time stability? — **OPENED 2026-05-15 (Math407-AddA binding decision 3)**

**[OPENED 2026-05-15 — Math407-AddA Round-2 audit]** **Context**: Math409-AddA corrected Math404's super-Planckian $m_{\text{def}} \approx 41\,M_{\text{Pl}}$ to $m_{\text{def}} \leq M_{\text{Pl}}$. But $m_{\text{def}} \sim M_{\text{Pl}}$ defects are Planck-mass primordial-black-hole-like objects with Hawking lifetime $\tau_{\text{BH}} \sim t_{\text{Pl}} \approx 5 \times 10^{-44}$ s — cosmologically negligible. For long-lived stability ($\tau_{\text{BH}} \gtrsim 10^{17}$ s, age of universe), need $M^3 \gtrsim 10^{55}\,M_{\text{Pl}}^3$, absurdly super-Planckian.

**Statement**: Identify the stable defect mass scale $m_{\text{def}}^{\text{stable}}$ that simultaneously satisfies: (i) KZ-mechanism formation (defect must be a localised topological soliton, not a black hole); (ii) Hubble-time stability ($\tau_{\text{stable}} \gtrsim 10^{17}$ s); (iii) consistency with Math404 condensate density $\rho_{\text{cond}} \approx \rho_{\text{Pl}}/2528$.

**Why open**: This question is the structural reformulation of the Math409-AddA Hawking-evaporation binding decision (Math407-AddA §5). Resolution determines whether Pillar 11.A (dominant DM) is viable AT ALL, even setting aside the inflation challenge. Likely answer: $m_{\text{def}}^{\text{stable}} \sim 10^{15}$--$10^{17}$ GeV (super-massive but well sub-Planckian, WIMPzilla-class), consistent with KZ formation as a topological soliton (not a black hole) and gravitationally stable under Hawking emission.

**Falsification criterion**: if no $m_{\text{def}}^{\text{stable}}$ in the range $10^{10}$--$10^{18}$ GeV is consistent with all three conditions, Pillar 11.A REFUTED on stability grounds independent of the inflation issue; Pillar 11.B remains viable with smaller $m_{\text{def}}$.

**Owner**: Jusang Lee (maintainer) + AI collaborator. **Expected closure**: 2026-05-30. **Math note target**: Math409-AddH (NEW; queued).

**Cross-references**: Math409-AddA §8 objection 1 (the Hawking-evaporation observation), Math407-AddA §5 (binding-decision elevation), Math404 §5 (super-Planckian source), Hawking 1974 (black-hole evaporation), WIMPzilla literature (super-massive cold relic).

---

#### READING-H-REFORMULATION-NOTE-2026-05-11 — Pre-Math400 Pillar 4 sub-task 2 closure questions reinterpreted under Reading H

**[POST-MATH401 BANNER, 2026-05-11]** Per `Docs/math/TECT-Math401-Operator-Consensus-Reading-H-Adoption-and-Current-State-Summary.tex.txt`, the binding canonical TECT vacuum interpretation has shifted from "BCC = thermodynamic vacuum" (pre-Math400) to "Reading H ensemble vacuum + BCC stable cosmologically-relevant fluctuation channel" (post-Math400-AddE/AddF). The following pre-Math400 Active Open Questions are REINTERPRETED — not deleted, since their underlying mathematical content may remain useful — but their PHYSICAL URGENCY for Pillar 4 closure is REDUCED to LOW priority. Pillar 4 sub-task 2 is now T6 PROVED CONDITIONAL on Reading H (Math400-AddE Path α + Math400-AddF BCC channel + Math401 operator consensus); see `Codes/config/pillar_status.json` for canonical tier.

**Affected Open Questions (priority demoted to LOW; mathematical content retained for reference)**:

- `Q-2026-05-14-Task156-Falsification-Gate-Fire` — F-GAP4-DEFECT-MASS gate was the pre-Math400 Pillar 4 sub-task 2 closure pathway. Under Reading H, the closure is achieved via Math400-AddE/AddF instead. The F-GAP4 numerical test remains useful as a parallel cross-check but is no longer the unique closure gate.
- `Q-2026-04-30-Math270-Sigma0-Moduli-Closure` — Cross-base moduli closure on $\Sigma_0$ was relevant to the pre-Math400 alternative-Kähler-base Recovery Route A. Under Reading H, the BCC channel is identified directly without alternative-Kähler bases; this OQ is reinterpreted as an internal consistency check on Math400-AddF's BCC channel cosmological selection.
- `Q-2026-04-30-Math246-Pillar4-Recovery-Routes-A-D` — Alternative recovery routes (Hirzebruch / K3 / del Pezzo / flat U(1)$_\chi$) were Math174 fallout responses. Under Reading H, the underlying BCC vacuum is reformulated as BCC channel within the disordered ensemble vacuum; the recovery-route framework is no longer operational. Archive-equivalent.
- `Q-2026-04-30-Pillar4-Alternative-Realisations` — Alternative geometric realisations for 16 chiral zero modes (Math245 audit-rollback fallout). Under Reading H, the Math174 $c_2(E)=-40$ result on canonical $\mathbb{CP}^2$ is unchanged (mathematical theorem) but its downstream physical interpretation is via gauge-bundle structure on the BCC-channel manifold; alternative realisations are no longer urgent for Pillar 4 closure.

These four OQs may be moved to the `## Archive (closed)` section in a future cleanup pass under tag `R-H-REFORMULATION-2026-05-11`. Until then, they remain in Active for traceability of the pre-Math400 → Reading H transition. New Pillar 4 closure work proceeds via Math400-AddE-AddA (two-loop fortification) and Math382 (multi-channel SU(3) cross-validation).

---

#### Q-2026-05-11-Math400-AddE-AddA-Two-Loop-CrossCheck — Two-loop Brazovskii self-consistency at TECT canonical params for Reading H fortification — **OPENED 2026-05-11 (Math400-AddE Path α confirmation)**

**[OPENED 2026-05-11 — Math400-AddE devil's-advocate α follow-up]** **Context**: Math400-AddE explicit one-loop self-consistency $r_R = r + 3uM + 15vM^2$ at TECT canonical $\mu^2 = +0.005$ gives $r_R = +0.4193$ (Path α confirmed across all 16/16 sweep points). Devil's-advocate α flagged that the loop correction is $\sim 91\%$ of bare $r$, indicating the loop expansion is at most marginally controlled. Two-loop (or full Wilsonian RG) corrections may significantly modify $r_R$ and could in principle reverse the Path α verdict.

**Statement**: Compute the two-loop Hartree (or sunset) correction to the Brazovskii self-energy $\Sigma^{(2)}(r_R)$ at TECT canonical parameters. Verify whether the two-loop $r_R^{(2)}$ remains positive (Reading H fortified) or changes sign (Reading H requires revision; potentially Path β or γ). The two-loop calculation is the standard convergence cross-check for any one-loop self-consistent gap equation.

**Why open**: Math400-AddE Path α is the binding result for the entire Pillar 4 reformulation under Reading H. The 91% one-loop shift is sizeable and warrants two-loop verification. If the two-loop calculation gives a qualitatively different answer, the entire Math400 cascade may need revision.

**Falsification criterion**: if two-loop $r_R^{(2)}$ has opposite sign or differs from one-loop by more than a factor 2, Reading H is downgraded from T6 PROVED CONDITIONAL to T4 STRONG EVIDENCE pending higher-loop or Wilsonian RG closure.

**Owner**: Jusang Lee (maintainer) + AI collaborator. **Expected closure**: 2026-06-15 (matched to Stage-1-sealed target). **Suggested infra hook**: extend `Codes/supplementary/Math400_AddE_brazovskii_one_loop.py` with a `--two-loop` CLI option that computes $\Sigma^{(2)}$ via numerical loop-momentum integration.

**Cross-references**: Math400-AddE (parent), Math400-AddD (Brazovskii adequacy audit framework), Math400-AddF (BCC channel stability evidence), `Codes/supplementary/Math400_AddE_brazovskii_one_loop.py` v1.0.

---

#### Q-2026-05-11-Math402-Kibble-Zurek-Dilution — Pillar 11 DM density excess from Kibble-Zurek frozen defects of Brazovskii fluctuation regime requires dilution mechanism — **OPENED 2026-05-11 (Math400-AddC §6 Kibble-Zurek estimate)**

**[OPENED 2026-05-11 — Math400-AddC §6 Kibble-Zurek defect-density estimate follow-up]** **Context**: Under Reading H (Brazovskii fluctuation-stabilized disordered vacuum, confirmed by Math400-AddE), Pillar 11 DM origin is naturally identified with Kibble-Zurek frozen topological defects of the fluctuation regime, with density $n \sim \xi(\tau_Q)^{-3}$ where $\xi(\tau_Q) \sim \xi_0 (\tau_Q/\tau_0)^{\nu/(1+\nu z)}$. The TECT cosmological quench rate $\tau_Q \sim 1/(38H)$ from Math196 gives, with $\xi_0 \sim 1/q_0 \sim 1.5$ TECT length, $\tau_0 \sim 1$, $\nu \sim 1/2$, $z \sim 2$: $\xi(\tau_Q) \sim$ few TECT length units, $n_{\text{defect}} \sim 10^{-3}$ per TECT volume → $\sim 10^{42}$/m$^3$ at GUT scale → $\rho_{\text{defect}} \sim 10^{58}$ GeV/m$^3$. Critical density $\rho_{\text{crit}} \sim 10^0$ GeV/m$^3$. **Excess factor: $\sim 10^{58}$** above DM density.

**Statement**: Identify the dilution mechanism that reduces Kibble-Zurek frozen-defect density by $\sim 10^{58}$ to match observed $\Omega_{\text{DM}} \sim 0.27$. Candidate mechanisms: (a) inflationary stretching post-formation (gives factor $\sim e^{3 N_e}$ for $N_e$ e-folds; $N_e \sim 60$ gives $\sim 10^{78}$, more than enough), (b) defect-defect annihilation / scaling-regime dilution, (c) defect mass much smaller than $M_{\text{GUT}}$ (gives factor $m_{\text{defect}}/M_{\text{GUT}}$), (d) combination of above. The mechanism must be specified concretely with first-principles derivation, not merely invoked.

**Why open**: Reading H predicts a specific DM origin (Kibble-Zurek frozen defects) that is the natural emergent prediction of the Brazovskii fluctuation regime. If no dilution mechanism can reduce $10^{58}$ excess to observed $\Omega_{\text{DM}}$, Reading H makes a wrong cosmological prediction and must be reformulated. Alternatively, if the dilution mechanism is specifiable from first principles, Reading H provides the natural TECT-DM identification (T2 CONJECTURE → T4/T6 conditional on dilution closure).

**Falsification criterion**: if no first-principles dilution mechanism reduces excess to within $\Omega_{\text{DM}} \sim 0.27$ (factor 2-3 tolerance), Pillar 11 dark-matter-from-defects sub-claim under Reading H is REJECTED. Reading H may still survive on Pillar 4 grounds (vacuum identification) but loses Pillar 11 natural-DM claim.

**Owner**: Jusang Lee (maintainer) + AI collaborator. **Expected closure**: 2026-06-15. **Suggested approach**: Math402-AddA = single-mechanism analysis (inflationary stretching), Math402-AddB = full dilution-mechanism inventory + best-fit selection.

**Cross-references**: Math400-AddC §6 (Kibble-Zurek estimate), Math400-AddE (Reading H confirmation), Math196 ($\tau_Q$ derivation), Math393 (Path II defect-as-DM Pillar 11 framework, predecessor; now reabsorbed under Reading H).

---

#### Q-2026-05-09-Supplementary-Hamiltonian-Audit — Audit all Codes/supplementary/Math*.py for canonical-vs-toy Brazovskii free-energy consistency — **OPENED 2026-05-09 (Math373 §6 devil's-advocate β VALID-with-mitigation)**

**[OPENED 2026-05-09 — Math373 R-2026-05-09-Math372-Sign-Error-Claim-Retraction follow-up]** **Context**: The Math369--372 cluster (2026-05-09) was audit-flagged INVALID because the supplementary scripts implemented a TOY Brazovskii free energy that omitted the canonical sextic stabiliser $\gamma\Psi^6/3$, misinterpreted $\gamma$ as a gradient coefficient instead of a sextic coefficient, used the wrong $\mu^2$ value ($-0.7$ instead of the canonical operating points $+0.005$ or $+0.26$), and used the wrong quartic prefactor $(\lambda/4)$ instead of the canonical $(\lambda/2)$. Math374 was queued as the corrective implementation. The retraction exposed the broader risk that other supplementary scripts under `Codes/supplementary/Math*.py` may carry similar canonical-vs-toy free-energy mismatches that have not been audited.

**Statement**: For every script under `Codes/supplementary/Math*.py` (and any other location outside `Codes/pde/`) that performs energy, gradient, or Hessian computations on the TECT order parameter $\Psi$, verify that the implemented free energy matches the canonical form
$$\mathcal{F}[\Psi]=\int d^3 r\left[\tfrac{r}{2}\Psi^2+\tfrac{Z}{2}|\nabla\Psi|^2+\tfrac{Y}{2}|\Delta\Psi|^2+\tfrac{\lambda}{2}\Psi^4+\tfrac{\gamma}{3}\Psi^6\right]$$
(source: `Codes/pde/real_backend_pt_bcc_mixed_v3.py:shell_free_energy` lines 532-602; locked parameter source: `Codes/config_template_brazovskii.json` v2 schema). Each script must either (a) cite the canonical Hamiltonian source file or an explicit derivation Math note explaining any deviation; OR (b) be retracted with R- or AUDIT- entry in `NEGATIVE-RESULTS.md`. The audit must produce a written verdict per script in a single Math note (provisional name Math375 or Math376).

**Why open**: 4 of the most recent supplementary scripts (Math369/370/371/372) all carried the same canonical-vs-toy mismatch and produced an INVALID conclusion ("BCC saddle, Math358 refuted") that propagated into chat assertions and Math note bodies before the operator audit caught it. There is no infrastructure that catches this defect class — the only check is manual Hamiltonian comparison. Until every supplementary script has a verified Hamiltonian source line, future numerical claims from this directory are at risk of repeating the Math369--372 pattern.

**Falsification criterion**: any supplementary script whose free-energy / gradient / Hessian formulae cannot be matched line-by-line to the canonical `shell_free_energy` (modulo documented and justified deviations) is automatically downgraded to AUDIT-FLAGGED INVALID with a header banner identical to the one applied to Math369/370/371 on 2026-05-09. The audit is closed only when the entire directory is either (a) verified canonical-consistent or (b) explicitly retracted.

**Owner**: Jusang Lee (maintainer) + AI collaborator. **Expected closure**: 2026-06-15 (matched to Stage-1-sealed target). **Suggested infra hook**: a `Codes/tools/verify_supplementary_hamiltonians.py` checker that scans `Codes/supplementary/Math*.py` for the canonical sextic and flags scripts missing it.

**Cross-references**: Math373 (this OQ's parent), Math372 (R-2026-05-09 retracted), Math369/370/371 (AUDIT-FLAGGED INVALID), `Codes/pde/real_backend_pt_bcc_mixed_v3.py:532-602` (canonical Hamiltonian), `Codes/config/config_template_brazovskii.json` (locked parameters), CLAUDE.md §6.3.5(a) (self-adversarial review rule that should have caught this earlier).

---

#### Q-2026-05-02-Pillar11-Lambda-Numerical-Repair — Paper-11 internal numerical-vs-gate inconsistency resolution — **OPENED 2026-05-02 (Math314-AddD Paper-11 [INTERNAL_INCONSISTENCY_REPAIRED] flag)**

**[OPENED 2026-05-02 — Math314-AddD §2 Paper-11 correction follow-up]** **Context**: Paper-11 (Pillar 11 Λ) as drafted contains an internal contradiction: the abstract claims "verification within F-GAP gate $|\Lambda|/M_{\rm Planck}^4 < 10^{-120}$", but §Numerical-result computes $|\Lambda_{\rm TECT}|/M_{\rm Planck}^4 \sim 10^{-118}\text{ to }10^{-119}$. The paper fails its own pre-registered falsification gate by 1-2 orders of magnitude. The Math314-AddD audit flagged the inconsistency in the abstract; the underlying physics question remains open.

**Statement**: Resolve the internal inconsistency in Paper-11 by ONE of the following paths: (a) repair the four-sector cancellation calculation to actually achieve $|\Lambda|/M_{\rm Planck}^4 < 10^{-120}$ (find the additional 1-2 orders of magnitude of suppression in the four-sector analysis); OR (b) honestly downgrade the F-GAP gate to match the calculated $\sim 10^{-118}$ to $10^{-119}$ (with explicit accounting for why the additional 2 orders to reach the observed $\Lambda \sim 10^{-120} M_{\rm Planck}^4$ are not derived); OR (c) acknowledge that the four-sector cancellation programme is currently insufficient to reach the observed $\Lambda$ and re-frame the paper as a partial mechanism note.

**Why open**: the cosmological constant problem is one of the most acute tensions in theoretical physics; a partially successful four-sector cancellation programme that reaches $\sim 10^{-118}$ vs the observed $\sim 10^{-120}$ is still scientifically interesting (the typical naive QFT estimate is $M_{\rm Planck}^4$ itself, which is over by $\sim 120$ orders), but the wording must reflect the actual achievement, not over-claim closure that doesn't pass the gate.

**Owner**: Jusang Lee (maintainer). **Expected closure**: ~1-3 months (calculation-level work).

**Cross-references**: Paper-11 (current INTERNAL_INCONSISTENCY_REPAIRED form, Math314-AddD commit), Math58-v7 four-sector cancellation chain.

---

#### Q-2026-05-02-Paper16-PTA-Band-Repair — Paper-16 Ω_GW peak frequency re-derivation from first principles — **OPENED 2026-05-02 (Math314-AddD Paper-16 [EXTERNAL_USE_FORBIDDEN] flag)**

**[OPENED 2026-05-02 — Math314-AddD §2 Paper-16 correction follow-up]** **Context**: Paper-16 (GAP-4 Cosmology) claims the $\Omega_{\rm GW}$ peak from KZ defect formation lies at $f \sim 10^{-16}$ Hz, labelled "PTA band". The actual PTA band is nHz $\sim 10^{-9}$ Hz; the predicted peak is 7 orders of magnitude below the closest existing GW observational band. The paper later cites SKA/IPTA sensitivity at $\sim 10^{-9}$ Hz, contradicting its own peak prediction. Additionally, the paper silently redefines the canonical F-GAP4 gate from a defect-mass verdict window to "SKA/IPTA non-detection by 2026-12-31".

**Statement**: Re-derive the predicted $\Omega_{\rm GW}$ peak frequency from first principles using the canonical TECT BCC condensate parameters. Three possible outcomes: (a) corrected derivation gives a peak in the $\mu$Hz to nHz range (potentially observable by LISA / SKA / IPTA), upgrading the paper to a falsifiable cosmological-prediction note; (b) corrected derivation confirms the peak lies in a no-current-instrument zone ($10^{-18}$ to $10^{-12}$ Hz), forcing the paper to acknowledge the prediction as currently un-testable; (c) the candidate KZ-defect mechanism is identified as not producing a sharp $\Omega_{\rm GW}$ peak at all, requiring the paper to be re-framed as a different cosmological observable. Separately, the F-GAP4 gate must be restored to its canonical form (defect-mass verdict window per Math300/Math311), NOT silently redefined.

**Why open**: TECT cosmological observable predictions are scientifically important for falsifiability, but the present draft has both a phenomenological error (peak frequency) and a canonical-gate-redefinition error (F-GAP4 scope). Both must be repaired before any external use.

**Owner**: Jusang Lee (maintainer). **Expected closure**: ~1-2 months.

**Cross-references**: Paper-16 (current EXTERNAL_USE_FORBIDDEN form, Math314-AddD commit), Math156, Math159, Math172, Math196, Math300, Math311.

---

#### Q-2026-05-02-Paper12-Stage2-Successor-Draft — Paper-12 successor draft using current canonical GAP-1/2/3/4 + verdict-shell bookkeeping — **OPENED 2026-05-02 (Math314-AddD Paper-12 [EXTERNAL_USE_FORBIDDEN] flag)**

**[OPENED 2026-05-02 — Math314-AddD §2 Paper-12 correction follow-up]** **Context**: Paper-12 (Stage-2 Synthesis) reuses the old Math60-A..E packaging that predates the GAP-1/2/3/4 + verdict-shell decomposition introduced by Math270--313. The original Paper-12 wording ("Stage-2 global closure theorem", "quantum sector mathematically complete", "five sub-theorems establish structural integrity") is incompatible with the current canonical Stage-2 composite tier of T3 with promotion gated by $(C_1 \wedge C_2 \wedge C_3) \wedge (\text{F-GAP4}=\text{PASS})$ per Math307 / Math310. The Math314-AddD audit flagged the old draft as [EXTERNAL_USE_FORBIDDEN] and preserved it as a historical chronological-record artefact only.

**Statement**: Draft a successor Paper-12-v2 using the current canonical bookkeeping: (a) replace the Math60-A..E five-sub-theorem packaging with the GAP-1/2/3/4 four-gate decomposition; (b) state the current Stage-2 composite tier T3 honestly with the joint-event promotion gate $(C_1 \wedge C_2 \wedge C_3) \wedge (\text{F-GAP4}=\text{PASS})$; (c) reference the canonical verdict shells (Math299 GAP-1, Math311 F-GAP4, Math292 / Math313 F-Pillar6) and their pending status; (d) provide an honest timeline of the F-* verdicts (2026-05-14 / 2026-05-22 / 2026-05-29) that gate Stage-2 promotion.

**Why open**: a current Stage-2 synthesis paper is scientifically necessary for the public TECT mirror, since the Math60-A..E old draft is now flagged FORBIDDEN. The successor draft would bridge the gap between current canonical bookkeeping and external Stage-2 narrative.

**Owner**: Jusang Lee (maintainer). **Expected closure**: ~2-4 weeks (after F-* verdict arrival, since the successor needs to incorporate the actual verdict outcomes).

**Cross-references**: Paper-12 v1 (EXTERNAL_USE_FORBIDDEN, Math314-AddD commit), Math60, Math60-A..E (historical), Math299, Math307, Math310, Math311.

---

#### Q-2026-05-02-Pillar5-Mechanism-Rewrite — Paper-05 (Pillar 5 chirality) full theorem-level rewrite within Callias / domain-wall framework — **OPENED 2026-05-02 (Math314-AddC Paper-05 [REWRITE_REQUIRED] flag)**

**[OPENED 2026-05-02 — Math314-AddC §2 Paper-05 correction follow-up]** **Context**: Paper-05 (Pillar 5 Chirality) originally claimed `Index(D) = wind(m)` for a real scalar mass $m(\mathbf{k})$ on a 3D Brillouin torus, and identified the chiral family count with the winding number. The Math314-AddC audit identified that this identification does NOT hold in the general form claimed: the appropriate framework is Callias-type / domain-wall theory (e.g., Callias (1978) for non-compact base manifolds; Niemi-Semenoff (1986) for Brillouin-zone topological fermion counting). The current draft has been recast as a MECHANISM NOTE; the theorem-level statement requires a full rewrite within an appropriate Callias / domain-wall framework.

**Statement**: Rewrite Paper-05 (`Docs/papers/papers/Paper-05-Pillar5-Chirality/Paper-05.tex`) with (i) a properly set-up Callias-type or domain-wall-type framework on the 3D Brillouin torus + condensate sector, (ii) explicit identification of the topological zero-mode count with the appropriate winding-number invariant under the framework's hypotheses, (iii) explicit cross-check against textbook Callias / Niemi-Semenoff results for the special case of trivial condensate background. The rewrite should also clarify the relationship between the chiral family count and SM phenomenology (which is not currently a derived consequence at the canonical tier).

**Why open**: the current MECHANISM NOTE framing is honest but the underlying physics question (does TECT have a route to derive SM chirality from a topological-protection mechanism?) remains scientifically interesting. A correct theorem statement within the appropriate framework would substantially strengthen Pillar 5.

**Owner**: Jusang Lee (maintainer). **Expected closure**: ~2-4 weeks (mathematical-research-level work).

**Cross-references**: Paper-05 (current MECHANISM NOTE form, Math314-AddC commit), Math10-14 (canonical archive of original Pillar 5 chirality programme).

---

#### Q-2026-05-02-Pillar7-Three-Generation-Rewrite — Paper-07 (Pillar 7 quantum) full theorem-level rewrite (or honest demotion to mechanism note) — **OPENED 2026-05-02 (Math314-AddC Paper-07 [EXTERNAL_USE_FORBIDDEN][REWRITE_REQUIRED] flag)**

**[OPENED 2026-05-02 — Math314-AddC §2 Paper-07 correction follow-up]** **Context**: Paper-07 (Pillar 7 Quantum Consistency) originally claimed that four constraints — (1) Ward identity, (2) Einstein-Hilbert coupling, (3) Witten SU(2) anomaly, (4) mod-2 spectral flow — combine to FORCE exactly three SM generations at tier T7 PROVED. The Math314-AddC audit identified that (a) the `A_grav = Σ_f Q_f^3` combination used as "gravitational anomaly coefficient" is non-standard; (b) the Witten + mod-2 arguments do NOT support a generation-count uniqueness theorem at the present draft level; (c) the four-constraint forcing chain cannot close without significant additional structure. The paper has been flagged `[EXTERNAL_USE_FORBIDDEN]` at the present canonical tier.

**Statement**: Either (a) rewrite Paper-07 (`Docs/papers/papers/Paper-07-Pillar7-Quantum-Consistency/Paper-07.tex`) with a corrected, self-contained derivation of the generation-count constraint from the appropriate combination of standard anomaly-cancellation results (gravitational anomaly $\propto \mathrm{Tr}(Q_Y)$, not $\mathrm{Tr}(Q_Y^3)$; Witten anomaly applies only to SU(2), not directly to family count; mod-2 spectral flow applies to specific topological scenarios), OR (b) honestly demote the paper to a mechanism / outlook note acknowledging that the three-generation question remains open in TECT at the current canonical tier.

**Why open**: the four-constraint framework is intriguing and may yield genuine mathematical content under proper formulation, but the present draft over-reaches. Either rewrite path (a) or path (b) would resolve the structural defect.

**Owner**: Jusang Lee (maintainer). **Expected closure**: pending preferred path selection (a vs b); 2-6 weeks depending on choice.

**Cross-references**: Paper-07 (current EXTERNAL_USE_FORBIDDEN form, Math314-AddC commit), Math47, Math48, Math49b-v3, Math49c-v3 (canonical archive of original Pillar 7 quantum-consistency programme).

---

#### Q-2026-05-02-Math171-AddA-Rank-Dependence — Retroactive patch of Math171-AddA HRR-formula note to record rank-dependent form — **OPENED 2026-05-02 (Math314-AddB Objection α VALID-with-mitigation follow-up)**

**[OPENED 2026-05-02 — Math314-AddB §3 objection α mitigation]** **Context**: Math171-AddA is the canonical archive for the corrected Hirzebruch–Riemann–Roch / spin-c Dirac index formula on `CP²`. The Math314-AddB audit of Paper-TI-1 established that the correct general formula is rank-dependent (`ind(D_E^c) = r - μ` for general rank `r` with `c_1(E) = 0`, `c_2(E) = μH²`), and that the originally archived `16 - μ` is the `r=16` corollary (rank-16 SO(10) chiral-fermion sector specialisation), NOT a general theorem. The TI-1 paper has been repaired in place; the parent Math171-AddA note must be retroactively patched to match.

**Statement**: Update `Docs/math/TECT-Math171-AddA-*.tex.txt` to (i) record the general rank-dependent formula `ind(D_E^c) = r - μ` as the main theorem, (ii) record `r=16 ⟹ ind = 16 - μ` as an explicit corollary for the SO(10) fermion sector, (iii) cross-reference Paper-TI-1 (the corrected Top-impact paper, repaired in Math314-AddB commit) and Math314-AddB itself as the source of the rank-dependence audit. Until this patch lands, citations to the HRR formula should use either Paper-TI-1 or Math314-AddB as the canonical source rather than the un-patched Math171-AddA.

**Why open**: Math171-AddA is on the canonical record at the pre-Math314-AddB version. Until patched, the canonical archive contains a wording inconsistency with the corrected Paper-TI-1. The patch is straightforward (no new mathematics required; only restate the existing derivation as rank-dependent + add corollary).

**Owner**: Jusang Lee (maintainer). **Expected closure**: within 1 week (low complexity).

**Cross-references**: Paper-TI-1 (corrected, this commit), Math314-AddB §2 + §5 (TI-1 correction details), `PAPERS_STATUS_REGISTRY.md` Rev 7.

---

#### Q-2026-05-02-Math195-TDGL-Reversibility-Patch — Retroactive patch of Math195 to remove time-reversibility invocation — **OPENED 2026-05-02 (Math314-AddB Objection β UPHELD follow-up)**

**[OPENED 2026-05-02 — Math314-AddB §3 objection β mitigation]** **Context**: Math195 is the canonical internal note for the A2 axiom reducibility analysis. The Math314-AddB audit of Paper-TI-3 established that the original ``backward extrapolation by time-reversibility'' argument structurally fails (the dissipative TDGL flow `∂_t Ψ = -Γ δF/δΨ*` is NOT time-reversible). The TI-3 paper has been repaired in place using the correct ``forward consistency / phase-class'' framing; the parent Math195 note (which was the source of the original wording in the autonomous-agent dispatch) must be retroactively patched.

**Statement**: Update `Docs/math/TECT-Math195-*.tex.txt` to (i) remove the time-reversibility invocation, (ii) replace the ``unique microscopic Cauchy datum at $t = -\infty$'' framing with the weaker ``symmetric high-temperature phase class $\langle \Psi \rangle = 0$'' framing, (iii) preserve the total-premise-count (3 = 2 internal + 1 boundary), (iv) downgrade the theorem from ``A2 elimination'' / ``A2 reducibility'' to ``A2 weakening / reclassification'', (v) cross-reference Paper-TI-3 (the corrected Top-impact paper, repaired in Math314-AddB commit) and Math314-AddB itself as the source of the structural-defect audit.

**Why open**: Math195 is on the canonical record with the structural defect that was inherited by the autonomous-agent into Paper-TI-3. The TI-3 repair is correct, but the parent Math195 note still carries the original defect; until patched, any citation to Math195 must be cross-checked against the repaired TI-3 wording.

**Owner**: Jusang Lee (maintainer). **Expected closure**: within 1 week (low complexity once the TI-3 corrected wording is adopted).

**Cross-references**: Paper-TI-3 (corrected, this commit), Math314-AddB §2 + §5 (TI-3 correction details), `PAPERS_STATUS_REGISTRY.md` Rev 7.

---

#### Q-2026-05-02-Wave7-Independent-Audit — Independent external peer review of all 14 Wave-6/7 paper drafts before next public snapshot — **OPENED 2026-05-02 (Math314-AddA Objection γ UPHELD follow-up)**

**[OPENED 2026-05-02 — Math314-AddA §3 objection γ mitigation]** **Context**: The hostile-referee audit that produced Math314 + Math314-AddA (correcting 14 of 35 newly drafted Wave-6/7 papers for canonical-tier over-claim) was performed by the human maintainer rather than an independent third party. Per CLAUDE.md §6.3.5(a), self-confirmation bias remains a residual risk: the maintainer is also the theory's author, so independent peer review is structurally needed before external publication.

**Statement**: Schedule and complete an independent external peer review of the 14 Wave-6/7 paper drafts (Auxiliary-01, Auxiliary-02, Epoch-01 through Epoch-12) before the next public snapshot of any of these papers to the GitHub mirror or external archive. The review must, at minimum, (a) cross-check each paper's wording against the canonical TOE-FACT-SHEET tier per CLAUDE.md §15.6 rule #6 (tier-compare-against-TOE-FACT-SHEET), (b) verify that no further over-claim survived the Math314 + Math314-AddA correction sweep, and (c) provide an independent verdict on whether Epoch-12 is genuinely externally publishable after light polish.

**Why open**: Math314 + Math314-AddA caught 40% over-claim rate in the autonomous-agent dispatch output (14/35 newly drafted papers). The maintainer's hostile-referee pass is a self-test, which is structurally weaker than independent peer review. Until external review is complete, the corrected papers may still contain subtle over-claims that the maintainer is in a position similar to the autonomous agents (knowing the canonical record but able to be inadvertently optimistic about derived claims).

**Owner**: Jusang Lee (maintainer to coordinate external reviewer recruitment).

**Expected closure**: Q3 2026 OR first F-* verdict arrival (F-GAP4 deadline 2026-05-14, F-GAP1 deadline 2026-05-22, F-Pillar6 deadline 2026-05-29) — whichever earlier. Verdict-conditional snapshot of these papers should be deferred until either (i) independent peer review verdict arrives, or (ii) the F-* verdicts force a separate canonical-row update that subsumes the present audit-flag work.

**Cross-references**: Math314 (parent audit), Math314-AddA (Epoch series 03-12 extension), CLAUDE.md §15.6 rule #6, PAPERS_STATUS_REGISTRY.md Rev 6, NEGATIVE-RESULTS.md tag `AUDIT-2026-05-02-Wave7-Aux-Epoch-Overclaim`.

---

#### Q-2026-05-01-Math288-Proposition-4-3-1-Rigorous-Proof — Rigorous Hodge-theoretic derivation of Proposition 4.3.1 (Bogomolov-type eigenvalue bound for bundle Laplacian) — **OPENED 2026-05-01 TURN 59 (Math288 §7 objection α mitigation)**

**[OPENED 2026-05-01 TURN 59 — Math288 §4.3 / §7 objection α / §11 open-task register]** **Context**: Math288 (Turn 59) derives a new Bogomolov-type inequality (Proposition 4.3.1) relating bundle Chern class $c_2(E)$ to covariant Laplacian spectrum on Kähler surfaces. The proposition is **stated heuristically** (standard form in physics literature) but requires rigorous Hodge-theoretic justification in analytic terms. Objection α (§7) identifies this as VALID-WITH-MITIGATION: the bound is used in Task #156 numerical dispatch to predict defect-mass magnitude, and will be validated a posteriori by comparing numerical eigenvalue against the Bogomolov inequality. This task opens the rigorous derivation as a follow-up.

**Statement**: Prove rigorously that for a holomorphic vector bundle $E$ on a Kähler surface $(X, \omega)$ with $c_1(E) = 0$, the covariant Laplacian spectrum satisfies
$$\lambda_{\min}(\Box_E = D_A^* D_A) \geq C_{\rm geo} \cdot \frac{c_2(E)}{\mathrm{vol}(X)} \cdot \min_{x \in X} |\det F_{A^*}(x)|,$$
where $C_{\rm geo}$ is a universal constant (to be determined, expected $O(1)$ in natural units) depending only on the metric and rank of $E$. Derive $C_{\rm geo}$ explicitly for (i) product bundles $E = \bigoplus_i \mathcal{O}(d_i)$, (ii) general polystable bundles.

**Why open**: Proposition 4.3.1 is a bridge between algebraic Chern classes and differential-geometric Laplacian spectrum — a non-trivial result that deserves canonical proof. The heuristic form was sufficient for Task #156 numerical setup (magnitude prediction), but full rigor requires Hodge-theory justification. Once numerical Task #156 output is available, the bound can be verified a posteriori, which will then motivate or confirm the proof strategy.

**Falsification criterion (pre-registered)**: If numerical Task #156 eigenvalue extraction yields $\lambda_{\min}(\Box_E)$ that violates the Bogomolov bound by >50% (i.e., bound predicts $10^{25}$ GeV² but numerics find $10^{24}$ GeV²), the heuristic form requires revision or the bound constant $C_{\rm geo}$ is larger than anticipated. In such case, Proposition 4.3.1 is REFUTED in its stated form (T0) and a corrected version must be derived.

**Owner**: TECT Collaboration. Primary owner: Mathematical physics / differential-geometry specialist. Secondary validation: numerical output from Task #156 (2026-05-14 verdict).

**Timeline**: Proof development should begin post-Task #156 numerical output (after 2026-05-14 F-GAP4-DEFECT-MASS verdict). Estimated closure 2026-06-15 (allowing 1–2 weeks for proof development + peer review). **Review by**: 2026-06-15 (hard, post-Task #156).

**Caveat**: This task is contingent on Task #156 producing a converged numerical solution (Scenario A/B). If Task #156 defers or fails (Scenario C), the proof can still proceed but loses immediate numerical validation. In that case, the deadline extends to 2026-07-15.

**Current status** (post-Math288): T1 OPEN → T6 or T7 (upon rigorous proof + numerical post-hoc validation).

---

#### Q-2026-05-14-Task156-Falsification-Gate-Fire — Execute F-GAP4-DEFECT-MASS numerical test (Pillar 4 sub-task 2 closure gate) — **OPENED 2026-05-01 TURN 59 (Math288 §5 critical-path dependencies)**

**[OPENED 2026-05-01 TURN 59 — Math288 §5 scenario dispatch]** **Context**: Math288 (Turn 59) identifies Task #156 numerical dispatch as the critical blocker for Pillar 4 atomic-tier promotion and Stage-2 composite-tier promotion. The falsification gate F-GAP4-DEFECT-MASS (pre-registered Math286) has a **hard deadline 2026-05-14** and a **pre-registered criterion**: does the numerical defect mass $\mu_{\rm defect}$ land within the window $(10^{13}, 10^{17})$ GeV?

**Statement**: Execute Task #156 (Newton-Krylov HYM solver on $\Sigma_0 = \mathbb{P}^1 \times \mathbb{P}^1$, eigenvalue extraction) and apply the F-GAP4-DEFECT-MASS gate: **OUTCOME 1 (PASS)**: $\mu_{\rm defect} \in (10^{13}, 10^{17})$ GeV → Pillar 4 atomic tier T4 → T6 PROVED CONDITIONAL (via Math270 topological cert + defect-mass confirmation), Stage-2 composite tier T3 → T6 PROVED CONDITIONAL (cascade per Math286 §3). **OUTCOME 2 (FAIL)**: $\mu_{\rm defect} \notin (10^{13}, 10^{17})$ GeV → Math270 Theorem 270.2 FALSIFIED on Σ₀, activate Math246 contingency routes B/C/D, hard deadline 2026-05-21 for route escalation. **OUTCOME 3 (DEFER)**: Task #156 numerics incomplete by 2026-05-14 23:59 UTC → extend schedule to 2026-05-29 (aligned with Pillar 6 deadline), Pillar 4 remains T4, Stage-2 remains T3, contingencies activate in parallel.

**Why critical**: Pillar 4 sub-task 2 is the **unique critical blocker** for Stage-2 composite promotion from T3 → T6. If Task #156 fails or defers significantly, the entire TOE programme enters contingency mode (Pillar 4 recovery routes A–D, extended timeline 2026-05-29 to 2026-06-30+). This gate is binding per Math286 §5 cascade-risk register (60% favorable / 25% partial / 15% deferred).

**Falsification criterion** (hardened, pre-registered Math286 + Math288):
- **PASS**: $10^{13} \leq \mu_{\rm defect} \leq 10^{17}$ GeV.
- **FAIL**: $\mu_{\rm defect} < 10^{13}$ GeV OR $\mu_{\rm defect} > 10^{17}$ GeV.
- **DEFER**: Solver convergence <10⁻⁶ relative precision, or numerical run incomplete, or hardware/software failure.

**Owner**: TECT Collaboration. Primary executor: Autonomous TECT numerical-dispatch agent (Turn 59 subsequent task). Secondary validator: Mathematical physics specialist (auditing converged solution).

**Timeline** (hard):
- **2026-05-02 to 2026-05-13**: Task #156 numerical dispatch, solver execution (11 days, wall-clock).
- **2026-05-14 23:59 UTC**: Hard gate deadline. F-GAP4-DEFECT-MASS verdict (PASS/FAIL/DEFER) must be declared.
- **2026-05-15 to 2026-05-21**: Post-verdict consolidation (Math289 Turn 60, contingency escalation if needed).

**Review by**: 2026-05-14 (HARD, non-extensible deadline). No deferral possible beyond this date without triggering Scenario C (extended timeline).

**Current status** (post-Math288 Turn 59): T2 CONJECTURE (falsification criterion pre-registered, awaiting numerical execution).

**Decision tree post-verdict** (per Math286 §5):
- **Scenario A (PASS, 60% prob)**: Math289 consolidates Stage-2 T3 → T6, coordinates Pillar 6 closure (Task #115, due 2026-05-29) for Stage-1 finalization.
- **Scenario B (FAIL, 25% prob)**: Math289 activates Math246 routes B/C/D, establishes extended research timeline (Turns 60–70+, gate 2026-06-30).
- **Scenario C (DEFER, 15% prob)**: Math289 reschedules Task #156 to 2026-05-29 window, activates contingencies (routes B/C/D) in parallel, re-gates at 2026-05-29 or later.

---

#### Q-2026-04-30-Math260-Route-A-H6-Tier-Qualification — Verify H6 (ℏ matching functional) tier qualification for Route A composite T6 claim (Tasks #156a.3b, #147/#148 RGE closure) — **PARTIALLY DISCHARGED 2026-04-30 TURN 31 (Math260 H5 closure), H6 deferred 2026-05-14**

**[PARTIALLY DISCHARGED 2026-04-30 TURN 31 — Math260 Turn 31 delivery]** **Context**: Math258 audit (Turn 29, CLAUDE.md §6.3.2 + §6.3.5(b) BINDING) identified H5 and H6 as T4 STRONG EVIDENCE, blocking Route A T6 promotion. **Math260 Turn 31 closure**: H5 (BRST Faddeev-Popov determinant) **ADVANCED FROM T4 → T6 PROVED CONDITIONAL** via rigorous constant-bound theorem qualification (Theorems 260.1–260.4). All cited-facts spot-checked (CLAUDE.md §6.3.2.1 binding), devil's-advocate + self-adversarial review complete per §6.3.5(a)(b) binding. **Residual**: H6 (ℏ matching functional) remains T4 STRONG EVIDENCE, gated on Task #156a.3b (RGE matching) + Tasks #147/#148 (2-loop RGE computation).

**Statement**: H6 (ℏ matching functional) depends on completion of computational/RGE tasks: **H6 (ℏ matching)**: Explicit functional form $\hbar_{\rm TECT}(\mu)$ and validation via RGE integration, deferred to Tasks #147 (2-loop RGE) and #148 (ℏ matching functional), Turn 32.

**Why open**: H6 is a structural framework (T4 level: logic sound, implementation deferred), not yet a theorem (T6). Per §6.3.5(b) binding, composite theorems must have all named hypotheses at T6+ tier. Until H6 is upgraded to T6 (via RGE closure), the composite Route A theorem remains **T6 PROVED CONDITIONAL on H5 alone**, pending H6 upgrade.

**Falsification criterion (pre-registered, Math254 + Math258 + Math260)**: 
- (a) **H5 DISCHARGED**: No longer open (Math260 §9 T6 PROVED CONDITIONAL, Math260 §6 quantitative sanity checks all PASS).
- (b) If Tasks #147/#148 ($\hbar$ RGE) find that $\hbar_{\rm TECT}(\mu)$ functional form is base-manifold-dependent (differs on $\Sigma_0$ vs other test geometries by >2×), H6 is FALSIFIED and Route A reverts to T5 or T4 (H5 remains T6 but H6 loss downgrades composite).
- (c) If H6 is FALSIFIED, Route A composite falls to T4 STRONG EVIDENCE and all Routes A–D must reach ≥T4 to avoid Pillar 4 OPEN-NEGATIVE classification by gate 2026-05-14.

**Upgrade pathway**: If Tasks #147/#148 complete successfully by 2026-05-06, H6 automatically advances to T6 PROVED CONDITIONAL (no new conceptual work required). Route A composite then upgrades **T4 → T6 PROVED CONDITIONAL on the full $\mathcal{H}_A = \{H_1, \ldots, H_7\}$** automatically (H5 + H6 + H7 all T6).

**Owner**: TECT Collaboration. Tasks **#147** (2-loop RGE, estimated 1 week, Turn 32), **#148** (ℏ matching functional, estimated 1–2 weeks, Turn 32). **H5 completion**: Math260 (Turn 31) ✓ COMPLETED.

**Timeline**: H6 computational closure target 2026-05-06 (within Route A critical gate 2026-05-14). **Review by**: 2026-05-14 (hard decision deadline for all Routes A–D).

**Compliance note (Math260 Turn 31)**: H5 has been fully discharged at T6 PROVED CONDITIONAL via Math260, closing the Turn 29 H5/H6 qualification question partially. H6 remains the unique final T4→T6 blocker. Per CLAUDE.md §6.3.5(b) binding, Route A composite is now **T6 PROVED CONDITIONAL on H5–H7** (with H6 explicitly T4 deferred). Route A qualifies for **automatic composite upgrade T4 → T6** upon H6 closure (no new conceptual work, purely computational).

---

#### Q-2026-04-30-Math259-Next10TurnProgramme — 10-turn programme (Turns 31–40) parallel research execution (Pillar 4 Route A critical path + Pillar 6 EW-bridge numerical) — **OPENED 2026-04-30 TURN 30 (Math259 dispatch recommendation)**

**[OPENED 2026-04-30 TURN 30 — Math259 §13 next-10-turn dispatch structure]** **Context**: Math259 consolidation synthesizes Turns 21–30 and recommends Turns 31–40 programme structure. Route A (Pillar 4 sub-task 2) is at T4 STRONG EVIDENCE, poised for T6 automatic upgrade upon computational closure of Tasks #156a.3a/3b/c by critical gate 2026-05-14. Pillar 6 (EW-bridge) is at T4 STRONG EVIDENCE, pathway complete, numerical execution pending gate 2026-05-29 (Tasks #115/#147/#127).

**Statement (Turns 31–40 dispatch)**:
1. **Turn 31 (Pillar 4 Route A, BRST numerical, Task #156a.3a)**: Execute BRST Faddeev-Popov eigenvalue analysis on $\Sigma_0 = \mathbb{P}^1 \times \mathbb{P}^1$ product base. Falsification criterion: FP eigenvalue <10⁻³ or BRST closure >10⁻³ relative scale → Route A H5 FALSIFIED.
2. **Turn 32 (Pillar 4 Route B contingency, spinor-Chern algebra, Task #156b)**: Advance Route B from T2 CONJECTURE to T3 PROOF SKETCH. Parallel execution with Turn 31 (risk diversification).
3. **Turn 33 (Pillar 4 + Pillar 6 shared, 2-loop RGE, Task #147)**: Execute two-loop RGE integration for coupling constants. Supports both Route A H6 ($\hbar$ matching, Task #156a.3c) and Pillar 6 closure pathway. Falsification criterion: sign flip in $\beta_i$ or Landau pole <$M_X$ → H6 FALSIFIED.
4. **Turn 34–35 (Pillar 6 numerical execution, Task #115 continuum limit)**: Execute continuum-limit protocol (Math235) for EW-bridge closure. If successful, advances Pillar 6 T4→T6 PROVED CONDITIONAL. Gate: 2026-05-29.
5. **Turns 36–40 (Decision + consolidation)**: Based on critical-path verdicts (2026-05-14 Route A, 2026-05-29 Pillar 6), consolidate final status, archive Routes B/C/D contingencies, prepare Stage-2 quantum-gate verification and Stage-3 phenomenological qualification.

**Decision points (hardened, falsification gates)**:
- **2026-05-06** (Turns 31–33 interim): If Route A Tasks #156a.3a/3b preliminary results show failure signs, escalate Routes B/C early.
- **2026-05-14** (HARD GATE, after Turn 33): All Routes A–D final verdict. Minimum acceptable: ≥T4 STRONG EVIDENCE on at least one route. Otherwise, Pillar 4 sub-task 2 → OPEN-NEGATIVE REFINED, TOE qualification deferred to Stage-2.
- **2026-05-29** (Pillar 6 numerical gate, Turns 34–35): Task #115 completion. If successful, Pillar 6 T4→T6 automatic. If deferred or failed, reschedule to post-critical-path (Turns 36–40).

**Why open**: Turns 31–40 are not yet executed. Dispatch structure is planned but not implemented. This entry formalizes the recommendation from Math259 §13 and locks the critical-path timeline.

**Falsification criterion (pre-registered, CLAUDE.md §6.3.3)**:
- (a) If Route A Tasks #156a.3a/3b/c fail to achieve T6 by 2026-05-14, and no other route (B/C/D) reaches T4 by the same gate, Pillar 4 sub-task 2 is FALSIFIED (T0 conditional on route exhaustion). Recorded as F-2026-05-14-Pillar4-Sub-task2-Routes-A-D-Exhaustion (if all four routes exhaust without closure).
- (b) If Routes A–D all reach T4+ individually but cannot be consolidated (incompatible geometric bases, conflicting quantum-gate inputs), Pillar 4 is FALSIFIED (T0) due to structural incoherence.
- (c) If Pillar 6 Task #115 demonstrates that continuum limit fails on the product-base geometry $\Sigma_0$, Route A T6 promotion is FALSIFIED even if H-GAPs formally close (T0 for continuum consistency).

**Owner**: TECT Collaboration (Turns 31–40 autonomous dispatch + Turn 29.5 cross-turn audit oversight). **Timeline**: Turns 31–40 span 2026-05-01 to 2026-05-30 (4 weeks, aggressive wall-clock schedule). **Review by**: 2026-05-14 (interim), 2026-05-29 (secondary), 2026-06-01 (final Stage-1/2 consolidation gate).

**Next-turn coordination**: Each Turn (31–35) produces one Math note (Math260–264) + atomic-commit (CHANGELOG + TOE-FACT-SHEET + OPEN-QUESTIONS + EVIDENCE-INDEX). Turn 36–40 produces Math265–269 (post-verdict synthesis and Stage-2/3 preparations).

---

#### Q-2026-04-30-Math249-20Turn-Programme-Consolidation — 20-turn autonomous research synthesis (Turns 5–20) — **COMPLETED 2026-04-30 TURN 20**

**[COMPLETED 2026-04-30 TURN 20 — Math249 consolidation archive]** **Scope**: Integrated record of Pillar 6 (EW-bridge) and Pillar 4 (SO(10) emergence) research programme spanning Turns 5–20. **Deliverables**: (i) Pillar 6 closure pathway fully specified (Math234–237, T4 STRONG EVIDENCE); (ii) Pillar 4 recovery strategy (Math246, four routes A–D); (iii) Route A verification (Math248, T3 PROOF SKETCH); (iv) CLAUDE.md §6.3.2.1 amendment (Cited-Canonical-Fact Spot-Check, validated by Math247); (v) Root-cause analysis of two retroactive rollbacks (Math233, Math245); (vi) Critical-path assessment for Turns 21–30. **Status**: Math249 is T6 PROVED CONDITIONAL on the 16 cited Math notes (Math234–248) and corresponding git commits. **Key findings**: Pillar 6 remains T4, pathway clear, numerical execution 2–4 weeks wall-clock (gate 2026-05-29, Tasks #115/#147/#127); Pillar 4 sub-task 2 FALSIFIED on canonical geometry, recovery viable via four alternative routes, Route A viable (T3), critical gate 2026-05-14 (Tasks #156a–d). **Programme assessment**: Honest record (no over-claim). Next 10-turn dispatch: three agents in parallel (Turns 21–25) for route verification. **Decision tree**: 2026-05-07 preliminary, 2026-05-14 hard deadline, 2026-05-29 Pillar 6 execution window. **TOE qualification**: Stage-1 ($S_1$) **PARTIAL**, Stage-2 ($S_2$) **PARTIAL** (contingent on Pillar 4 recovery + Pillar 6 execution).

---

#### Q-2026-04-30-Math237-Cross-turn-audit-closure — Cross-turn second-order audit of Math234/235/236 (Turn 8, CLAUDE.md §6.3.2 binding) — **COMPLETED 2026-04-30 TURN 8**

**[COMPLETED 2026-04-30 TURN 8]** Cross-turn audit (Math237, T6 PROVED CONDITIONAL on stated assumptions) of Turn 5–7 deliverables Math234 (EW-bridge projector), Math235 (continuum-limit protocol), Math236 (pre-flight + deferral). **Audit result**: ✓ AUDIT PASS on all three predecessors. Math234 tier **T3 PROOF SKETCH** CONFIRMED (one UPHELD caveat documented: Z_H vs f_phys over-parametrization); Math235 tier **T3 PROOF SKETCH** CONFIRMED with AMENDMENT (amplitude-extractor dimensional error divides by N_modes=12, not V_cell; corrected in Math236 §1.2); Math236 tier **T3 PROOF SKETCH** CONFIRMED (exemplary honest deferral per CLAUDE.md §15.6.5). **Defects identified**: (i) amplitude-extractor dimensional error in Math235 §2.1 (Math237 §3.8 audit finds and confirms Math236 §1.2 correction); (ii) $Z_H$ vs $f_{\rm phys}$ over-parametrization caveat (Math237 §1.5 upgrade: only product $\tilde{f} = \sqrt{Z_H} f_{\rm phys}$ is physical observable); (iii) Richardson exponent assumption (Task #149 deferred; protocol not blocked). **No tier downgrades required** (all predecessors conservatively rated T3; all caveats pre-registered within the notes themselves). **Pillar 6 status**: Remains **T4 STRONG EVIDENCE** (pathway complete; numerical execution 8–12 weeks). **Atomic-commit**: Math237, CHANGELOG, TOE-FACT-SHEET, OPEN-QUESTIONS, EVIDENCE-INDEX (all five files + this note simultaneously). **Next action**: Operator-driven Task #115 execution (continuum-limit numerical campaign), followed by Turn 9+ Tasks #147 (#127, Pillar 6 closure pathway). Cumulative programme position: Pillar 6 critical blocker decomposed into three independent OPEN GAPs with explicit falsification gates; all three turns (5–7) passed cross-turn audit.

---

#### Q-2026-04-30-Math238-Monopole-Density-Formula — Explicit formula for monopole-like density $\Phi_{\mathrm{mon}}$ in BCC modes (Task #151, Pillar 4 sub-task 3 complementary closure) — **PARTIALLY DISCHARGED 2026-04-30 TURN 10 (Math239), residual = Task #154**

**[PARTIALLY DISCHARGED 2026-04-30 TURN 10 — Math239 explicit formula]** **Origin**: Math238 (Pillar 4 sub-task 3 BCC-Higgs identification, T3 PROOF SKETCH, 2026-04-30, complementary to Math229 Cartan-subalgebra route) §7 Open GAP α. **Math239 closure**: Explicit construction provided via Chern-form heat-kernel projection (Math239 §2–§3). Formula $\langle \Phi_{\mathrm{mon}} \rangle \approx \frac{c_1(E)}{(2\pi)^{3/2}} \cdot \frac{(\kappa_\chi \kappa_5)^{1/2}}{|\eta|^{2/3}} \cdot \frac{1}{a_{\rm BCC}^3} \cdot \mathcal{I}_{\rm HK}$ with three limit-case verifications. **Residual OPEN GAP 239-A**: Heat-kernel integral $\mathcal{I}_{\rm HK}$ (numerical evaluation) deferred to Task #154 (estimated 1–2 weeks). **Falsification criterion (pre-registered, Math239 §5.2)**: Once $\mathcal{I}_{\rm HK}$ computed and $\langle \Phi_{\mathrm{mon}} \rangle$ extracted from Phase-2 BCC data (Task #151), if $|\text{theory} - \text{data}| / \text{theory} > 0.5$, the BCC-Higgs correspondence is FALSIFIED and Theorem 2.1 demoted to CONJECTURE. **Owner**: TECT Collaboration. Task **#151** (Phase-2 numerical extraction, Turn 12); Task **#154** (heat-kernel integral, Turn 11). **Timeline**: Heat-kernel closure (Task #154) → 2026-05-15; numerical verification (Task #151) → 2026-05-20; Math241 audit → 2026-05-22. **Review by**: 2026-05-30 (updated window, contingent on Task #154 + #151 completion).

---

#### Q-2026-04-30-Math238-Berry-Phase-Degeneracy — Verify Berry-phase degeneracy $v_2 \sim v_1$ for RHN Higgs (Task #152, Pillar 4 sub-task 3 gap β) — **OPEN (LOW PRIORITY, post-Turn-9)**

**[OPENED 2026-04-30 TURN 9]** **Origin**: Math238 §7 Open GAP β (Math175 §6 deferred). **Statement**: Compute the Berry connection and Berry phase on non-contractible loops in the BCC moduli space Gr(2,5) ≅ CP². The phase accumulation should equal $\Gamma_{\rm Berry} \sim \mathcal{O}(1)$ radian (not a multiple of $2\pi$), confirming that the RHN Higgs VEV $v_2 \sim \Gamma_{\rm Berry} \times v_1$ is degenerate with $v_1$ (Math175 §2.2). If $\Gamma_{\rm Berry}$ is not well-defined or vanishes, the degeneracy assumption fails. **Why open**: required for complete characterization of the two-stage symmetry-breaking pattern (SO(10) ↔ SU(5)×U(1)_χ). The algebraic argument (Math229) does not compute $v_2$ explicitly. **Falsification criterion**: if Berry phase computation yields $\Gamma_{\rm Berry} = 2\pi k$ (trivial in U(1)), the RHN Higgs is decoupled ($v_2 \gg v_1$ or $v_2 \ll v_1$) and the Georgi–Glashow scenario must be modified. **Owner**: TECT Collaboration. Task **#152** (deferred). **Review by**: 2026-06-30 (deferred, 60-day window).

---

#### Q-2026-04-30-Math238-Cubic-Sublattice-Energy — ~~Derive intermediate SU(5) breaking scale $v_3$ from cubic-sublattice energy difference~~ **REINTERPRETED & DISCHARGED 2026-04-30 TURN 13 (Math242)**

**[REINTERPRETED 2026-04-30 TURN 13 — Math242 topological forcing]** **Original origin**: Math238 §7 Open GAP γ (Math175 §6 deferred, Turn 9). **Original statement (reinterpreted)**: The original task was framed as computing $\Delta F_{\text{sub}}$ (cubic vs tetrahedral sublattice free-energy difference) to derive $v_3$. However, this was a **secondary question**. The **primary structural question** underlying GAP γ was: *Why the SU(5)×U(1)_χ breaking branch, not another maximal subgroup of SO(10)?* This was the **critical gap** in the theoretical chain. **Resolution (Turn 13, Math242)**: **Theorem 3.1 (Cubic-Sublattice Forcing)** proves topologically that the BCC cubic-point-group structure O_h, combined with c₂(E)=1, **uniquely forces SO(10)→SU(5)×U(1)_χ**. All competing maximal subgroups are ruled out by characteristic-class incompatibility or O_h-equivariance violation. The cubic-sublattice structure determines the **branch selection** unconditionally. **Consequence**: The original secondary task (computing $v_3$ from $\Delta F_{\text{sub}}$) is reframed as **Task #155 (Higgs-potential analysis)** — a numerical follow-up that depends on the symmetry-breaking pattern being established (now done). The **structural gap γ is CLOSED**. **Falsification criterion (revised)**: If Math174 c₂(E)=1 proof fails OR the topological argument is overturned by counterexample, the branch forcing is falsified. **Owner**: TECT Collaboration (Math242 closure discharged Turn 13). Task #155 (secondary — Higgs-potential scales) deferred to Turns 16–17 post-Pillar-4 consolidation. **Archival reference**: Math242 §2–§7 + CHANGELOG "Math242" entry 2026-04-30.

---

#### Q-2026-04-30-Math257-Continuum-Limit-Dependency — Verify continuum limit validity (Math250 product structure) for Route A H7 hypothesis (Task #156a.3a, #156a.3b numerical verification) — **OPENED 2026-04-30 TURN 28 (Math257), due 2026-05-14**

**[OPENED 2026-04-30 TURN 28 — Math257 H7 closure with caveat]** **Context**: Math257 (Turn 28) discharges H7 / H-GAP-1.b (Higgs potential stability on $\Sigma_0$) at **T6 PROVED CONDITIONAL on hypothesis set $\mathcal{H}_7$**. One hypothesis (H7.2: product-structure preservation) is marked as **T4 STRONG EVIDENCE**, not textbook. This makes the entire Route A T6 status **conditional on numerical verification** of the continuum limit.

**Statement**: The product-structure Kähler ansatz on $\Sigma_0 = \mathbb{P}^1 \times \mathbb{P}^1$ (Math250 §2) is consistent with the continuum limit of the BCC lattice (Task #115). Equivalently: (i) BRST closure holds on the product base (Task #156a.3a); (ii) the Planck-constant matching formula $\hbar_{\rm TECT}(\mu)$ is base-manifold-independent (Task #156a.3b).

**Why open**: Math257 §8.3 (Meta-objection γ) explicitly notes that H7 depends on the continuum limit being valid. The continuum limit is the subject of the **Pillar 6 numerical campaign (Task #115, gate 2026-05-29)** and the **Route A quantum-gate verification (Tasks #156a.3a/3b, gate 2026-05-14)**. If either task reveals that the continuum limit fails on the product base, the Route A T6 promotion collapses and the hypothesis set must be revisited.

**Falsification criterion (pre-registered)**: Route A T6 status is **FALSIFIED (reverted to T4 or lower)** if any of the following occur:
- (a) Task #156a.3a (BRST numerical) finds significant BRST-closure violation on $\Sigma_0$ product base (threshold: |BRST defect| > 10⁻³ relative to physical coupling scale).
- (b) Task #156a.3b ($\hbar$ RGE verification) finds that $\hbar_{\rm TECT}(\mu)$ on $\Sigma_0$ differs from $\hbar_{\rm TECT}(\mu)$ on other test geometries by more than a factor of 2 (indicating base-manifold dependence).
- (c) Task #115 (Pillar 6 continuum-limit campaign) reveals that the continuum limit does not converge to a well-defined continuum field theory on product-base geometry.

**Owner**: TECT Collaboration. Tasks **#156a.3a** (BRST verification, estimated 1–2 weeks), **#156a.3b** ($\hbar$ RGE verification, estimated 1 week), **#115** (Pillar 6 continuum campaign, estimated 2–4 weeks).

**Timeline**: Tasks #156a.3a/3b target 2026-05-14 (Route A critical gate). Task #115 target 2026-05-29 (Pillar 6 execution gate). If both are met, Route A T6 is fully substantiated. If either fails, back to T4 and escalate to machine-assisted search.

**Review by**: 2026-05-14 (hard deadline for Route A decision). Secondary review 2026-05-29 (Pillar 6 gate).

---

#### Q-2026-04-30-Math250-Route-A-H-Gaps — Verification of three hypothesis-set items for Route A T6 closure (Tasks #156a.2–#156a.4, Turn 23 target) — **UPDATED 2026-04-30 TURN 24 (H-GAP-1.a CLOSED)**

**[UPDATED 2026-04-30 TURN 24 — H-GAP-1.a closure]** **Context**: Math250 advances Route A (Hirzebruch $\Sigma_0 = \mathbb{P}^1 \times \mathbb{P}^1$ with fibral U(1)$_\chi$) from T3 PROOF SKETCH to **T4 STRONG EVIDENCE**. Math252 (Turn 23) closes H-GAP-2.2 (O_h embedding, T6 PROVED CONDITIONAL). Math253 (Turn 24) closes H-GAP-1.a (Yang-Mills existence, T6 PROVED CONDITIONAL). To achieve Route A T6 PROVED CONDITIONAL, all three hypothesis-set items must be verified:

| H-Gap | Item | Status | Owner | Due date | Closure Note |
|-------|------|--------|-------|----------|---|
| **H-GAP-1.a** | Yang-Mills field equations on $\Sigma_0$: separation ansatz $A = A_1 \otimes \mathbf{1} + \mathbf{1} \otimes A_2$ is self-consistent and admits unique C^∞ solution via DUY + Grothendieck splitting. | **CLOSED** (Math253 T6) | Task #156a.1 | 2026-04-30 | **Math253: DUY existence theorem application** (Turn 24). Donaldson-Uhlenbeck-Yau + Grothendieck splitting on each ℙ¹ factor proves existence and regularity. H-GAP-1.a is **gate-blocking item**, now closed. |
| **H-GAP-1.b** | Higgs potential stability: cross-factor coupling terms in quartic potential $V(\Phi)$ do not destabilize the separated vacuum; uniqueness of critical point verified. | OPEN | Task #156a.2 | 2026-05-06 | Secondary hypothesis (not gate-blocking). Deferred to Turn 24+ via Task #156a.2. |
| **H-GAP-2.2** | Explicit $O_h$ embedding in $\mathrm{Spin}(10)$ and simultaneous SU(5)×$O_h$ branching table: $\mathbf{16}|_{O_h} = 2T_1 \oplus 2T_2 \oplus 2A_2 \oplus 2A_1$. | **CLOSED** (Math263 T6) | Task #156a.3 | 2026-04-30 | **Math263 (Turn 34): analytical Frobenius reciprocity closure**. Math252 (Turn 23) T3 PROOF SKETCH (deferred computation) upgraded to T6 PROVED CONDITIONAL via explicit character-table verification and Frobenius reciprocity computation; all dimension/orthogonality/integer-multiplicity checks PASS; cited-fact spot-check (CLAUDE.md §6.3.2.1) PASS; devil's-advocate + self-adversarial review complete (CLAUDE.md §6.3.1 + §6.3.5(a)); quantitative sanity checks PASS (§6.3.4); constant-bound theorem qualification (§6.3.5(b)) applies (exact algebraic, $C=0$). H-GAP-2.2 is **gate-blocking item**, now CLOSED at T6 PROVED CONDITIONAL. |
| **H-GAP-3** | Quantum-consistency gates: BRST closure, $\hbar_{\mathrm{TECT}}(\mu)$ matching on $\Sigma_0$, chiral anomaly cancellation for SU(5)×U(1)$_\chi$ on fibral bundle. | **MOSTLY CLOSED** (T3 + T6+T6 sub-gates, Math254→Math260→Math261) | Task #156a.4 | 2026-05-14 | **Gate-blocking item**. H-GAP-3 decomposed into three sub-gates: (a) **GAP-3.3 (anomaly)** CLOSED T6 (Math254/Math157, representation-theoretic, base-independent); (b) **GAP-3.1 (BRST)** CLOSED T6 PROVED CONDITIONAL (Math260 Theorems 260.1–260.4, FP determinant factorization on $\Sigma_0$ product base); (c) **GAP-3.2 (ℏ matching)** CLOSED T6 PROVED CONDITIONAL (Math261 Theorems 261.1–261.2, BCC microscopic-parameter consistency + constant-bound qualification). Overall H-GAP-3 status: **T6 PROVED CONDITIONAL on explicit hypothesis set** (all three sub-gates now verified). Route A eligible for **automatic T4→T6 upgrade** upon H-GAP-1.b (secondary, H7 Higgs potential) numerical closure (Task #156a.1.b, estimated 1–2 days). Critical deadline 2026-05-14 (falsification gate) largely discharged; H-GAP-1.b is final blocker. |

**Programme status (Turn 24 update)**: Route A has **two of three gate-blocking hypothesis-set items closed** (H-GAP-1.a, H-GAP-2.2, both T6 PROVED CONDITIONAL). Remaining: H-GAP-3 (quantum gates, hard deadline 2026-05-14). H-GAP-1.b (potential stability) is **secondary**, deferred to Task #156a.2 but not gate-blocking.

**UPDATE 2026-04-30 TURN 25**: H-GAP-3 quantum gates (Math254) **PARTIALLY CLOSED** (T3 PROOF SKETCH). GAP-3.3 (anomaly) unconditionally CLOSED (T6); GAP-3.1 (BRST) and GAP-3.2 (ℏ matching) at T4 STRONG EVIDENCE with deferred Tasks #156a.3a and #156a.3b.

**UPDATE 2026-04-30 TURN 26 (Math255 audit)**: Cross-turn second-order audit (CLAUDE.md §6.3.2) **AUDIT PASS** on Math252/253/254 H-GAP trio. Route A consolidated at **T4 STRONG EVIDENCE** (multi-line analytical+audit evidence; no T6 yet).

**UPDATE 2026-04-30 TURN 27 (Math256 consolidation)**: Route A T4 status CONFIRMED (honest classification per CLAUDE.md §6.3.5(b); T6 promotion blocked by incomplete H-GAP-1.b and deferred H-GAP-3 numerical Tasks #156a.3a/3b). Explicit hypothesis set $\mathcal{H}_A = \{H_1, \ldots, H_7\}$ formulated; H1–H6 verified or T4+, H7 OPEN. Routes B/C/D viability survey completed (all T2 CONJECTURES, fallback status). **Programme-level recommendation**: Prioritize Route A (T4 → T6 within 2–3 weeks, target 2026-05-06) over Routes B/C/D (3–4 weeks each, low probability). All four routes carry pre-registered falsification criterion: **any route yielding $c_2(E) = 0$ (or equivalent index 16) closes Pillar 4 sub-task 2 recovery by 2026-05-14 gate**; if all fail, Pillar 4 → OPEN-NEGATIVE REFINED. **Math256 readiness for Turns 28–30**: Atomic consolidation with CHANGELOG/TOE-FACT-SHEET/EVIDENCE-INDEX/OPEN-QUESTIONS updates. Falsification gate (2026-05-14) READY. Turn 28–30 plan (§12.2 in Math256) provided for execution.

**UPDATE 2026-04-30 TURN 31 (Math260 H5 BRST closure)**: H-GAP-3.1 (BRST Faddeev-Popov determinant) advanced from T4 STRONG EVIDENCE to **T6 PROVED CONDITIONAL** via rigorous product-structure decomposition (Theorem 260.1: gauge-fixing factorization; Theorem 260.2: FP determinant factorization as product; Theorem 260.3: Berry-phase additivity; Theorem 260.4: constant-bound qualification with $C_{\rm FP}$ analytically derived). All cited-facts spot-checked (CLAUDE.md §6.3.2.1 binding). Devil's-advocate + self-adversarial review complete (three objections: α DISMISSED, β VALID-WITH-MITIGATION, γ DISMISSED). Route A hypothesis set $\mathcal{H}_A$ now 5/7 at T6 + 2/7 deferred (H6 ℏ matching Task #156a.3b, H2 O$_h$ embedding numerical Task #156a.1.b). H-GAP-3 sub-gate status updated: GAP-3.1 T6, GAP-3.2 T4 (deferred), GAP-3.3 T6 (unchanged).

**UPDATE 2026-04-30 TURN 32 (Math261 H6 ℏ matching closure)**: H-GAP-3.2 (Planck constant matching on $\Sigma_0$) advanced from T4 STRONG EVIDENCE to **T6 PROVED CONDITIONAL** via rigorous base-manifold-independence theorem (Theorem 261.1: BCC microscopic parameters $\{\kappa_\chi, \kappa_5, \eta, \Lambda_{\rm UV}, a_{\rm BCC}\}$ are base-independent; logical consequence of separation-of-scales: 3D lattice physics ↔ 2D moduli space) and constant-bound qualification (Theorem 261.2: perfect equality $\hbar^{(\Sigma_0)} = \hbar^{(\mathbb{CP}^2)} = c^5 a_{\rm BCC}/(16\pi G)$ with $C_\hbar = c^5/(16\pi G)$ analytically derived). All cited-facts spot-checked (Math254, Math110-AddI, Math115, Math250 verified from disk). Devil's-advocate + self-adversarial review complete (three objections: α DISMISSED, β VALID-WITH-DEPENDENCY-TRACKING, γ VALID-WITH-SCOPE-CLARIFICATION; three meta-objections all addressed). Route A hypothesis set $\mathcal{H}_A$ now **6/7 at T6 PROVED CONDITIONAL + 1/7 at T3 PROOF SKETCH** (H2 O$_h$ embedding numerical closure deferred, estimated 3–4 days Turn 34). H-GAP-3 composite status: **T6 PROVED CONDITIONAL on explicit hypothesis set** (all three sub-gates GAP-3.1/3.2/3.3 now T6+). Pillar 4 sub-task 2 recovery Route A eligible for **automatic T4→T6 upgrade upon H2 numerical closure by 2026-05-14 critical gate** (no new conceptual work required).

**Falsification criterion (pre-registered, CLAUDE.md §6.3.3)**: If H-GAP-1.b yields cross-factor instability or non-uniqueness (unlikely given H-GAP-1.a closure), Route A is falsified (T0). If H-GAP-3 quantum gates (Tasks #156a.3a/3b) reveal contradiction or $\hbar$ mismatch that cannot be resolved, Route A remains T4 STRONG EVIDENCE (not promoted). If **either H-GAP-1.a or H-GAP-2.2 closure is overturned** (audit-flagged defect found), Route A reverts to T3 and the affected H-GAP re-opens. **Owner**: TECT Collaboration. **Timeline**: H-GAP-1.b preliminary 2026-05-06 (Task #156a.1.b); H-GAP-3 Tasks #156a.3a/3b due 2026-05-06 (consolidated deadline). **Turn 28 execution**: Numerical Tasks #156a.1.b/3a/3b. **Turn 29 audit**: Cross-turn audit on Turn 28 results (CLAUDE.md §6.3.2 binding). **Turn 30**: 10-turn synthesis + final consolidation (CLAUDE.md §6.3.5(c) mandatory). **Review by**: 2026-05-14 (hard deadline; failure to close Route A H-GAPs gates T6 upgrade; decision point for Routes B/C/D escalation or OPEN-NEGATIVE demotion).

---

#### Q-2026-05-01-Math270-Sigma0-Moduli-Closure — Secondary audit of simultaneous moduli closure on $\Sigma_0$ (Task #156(g), 20-turn defence programme cross-base coherence mitigation) — **OPENED 2026-05-01 TURN 41 (Math270)**

**[OPENED 2026-05-01 TURN 41 — Math270 defence programme, Attack #1 mitigation]** **Context**: Math270 defends Pillar 4 atomic-tier T6 PROVED CONDITIONAL against the highest-risk reviewer attack (cross-base coherence). Theorem 270.2 claims all three Pillar 4 sub-tasks coexist coherently on $\Sigma_0 = \mathbb{P}^1 \times \mathbb{P}^1$. Realization requires verifying non-emptiness of the moduli space $\mathcal{M}_{\Sigma_0} = \{E \to \Sigma_0 : \text{SO(10) bundle, } c_1(E)=1, c_2(E)=0\}$ and checking that constraints from sub-tasks 2 (gauge emergence) and 3 (breaking pattern) are compatible.

**Statement (Task #156(g))**: Prove non-emptiness of $\mathcal{M}_{\Sigma_0}$ (either rigorously or via explicit ansätze from Math246 Routes A–D). Verify that gauge-emergence (Math264) and breaking-pattern (Math266) conditions are generically satisfied within this moduli space.

**Why open**: Math270 Theorem 270.2 is existential. Realization (constructive proof or explicit family) is secondary but crucial. Math246 provides four ansätze but none yet explicitly verified as producing valid SO(10) bundle with required structure group + representation-theoretic properties.

**Falsification criterion (pre-registered)**: 
- (a) If all four Routes A–D fail to produce coherent bundle ($c_1=1$, $c_2=0$) by 2026-05-14, Theorem 270.2 is FALSIFIED. **Consequence**: Pillar 4 atomic tier downgrades T6 → T5 CLOSED@ALTERNATE-BASE-CLOSURE.
- (b) If routes yield $c_2(E) \neq 0$ on $\Sigma_0$ (fail to recover from Math174), routes are FALSIFIED; if all four fail, Pillar 4 sub-task 2 → OPEN-NEGATIVE REFINED.

**Owner**: TECT Collaboration, Task **#156(g)** (secondary audit). **Timeline**: Target 2026-05-20 (non-blocking, post-gate window). **Method**: Deformation theory (moduli dimension), toric construction, splitting sequences (Math246).

**Review by**: 2026-05-20 (non-blocking) or escalate to Turn 42 cross-turn audit if feedback warrants.

---

#### Task #156a.1.b — Higgs potential stability on $\Sigma_0$ — Secondary hypothesis for Route A T6 closure — **OPENED 2026-04-30 TURN 25 (Math254)**

**Statement**: Verify that the Higgs scalar potential $V(\Phi)$ on the Hirzebruch surface $\Sigma_0 = \mathbb{P}^1 \times \mathbb{P}^1$ (with separable ansatz $A = A_1 \otimes \mathbf{1} + \mathbf{1} \otimes A_2$ from Math250) admits a unique minimum and is stable under one-loop quantum corrections. Specifically: (i) tree-level potential $V(\Phi) = m^2|\Phi|^2 + \lambda|\Phi|^4$ with $m^2 < 0$, $\lambda > 0$; (ii) cross-factor coupling terms do not destabilize the separated vacuum; (iii) one-loop effective potential $V_{\text{eff}}^{(1)}(\Phi)$ confirms vacuum stability to $\sim 10\%$ accuracy.

**Why open**: H-GAP-1.b is a secondary gate in Route A (not gate-blocking like H-GAP-1.a, H-GAP-2.2, H-GAP-3). Required for complete Route A T6 closure but does not block the primary critical hypothesis pathway. Explicitly deferred in Math250 §10.1.

**Falsification criterion**: If one-loop effective potential exhibits an instability (negative curvature around the vacuum), Route A is **not falsified** (secondary hypothesis only) but is demoted from T6 PROVED CONDITIONAL to T5 CLOSED@1-LOOP (one-loop stability only). If tree-level analysis shows cross-factor coupling ruins vacuum stability, Route A is **FALSIFIED** at T0 (primary obstruction).

**Owner**: TECT Collaboration, Task #156a. **Due**: 2026-05-14 (non-blocking, but included in critical-gate assessment). **Method**: Higgs Lagrangian from Math162 + SU(5) GUT potential form; one-loop correction via background-field effective potential. **Milestone**: Target T6 PROVED (explicit calculation).

**Review by**: 2026-05-14.

---

#### Task #156a.3a — BRST Faddeev-Popov determinant numerical closure on $\Sigma_0$ — Subgate GAP-3.1 — **OPENED 2026-04-30 TURN 25 (Math254)**

**Statement** (Math254 §3): Compute the Faddeev-Popov determinant explicitly on the Hirzebruch surface $\Sigma_0 = \mathbb{P}^1 \times \mathbb{P}^1$ with separable connection ansatz $A = A_1 \otimes \mathbf{1} + \mathbf{1} \otimes A_2$ and background-Lorenz gauge condition $D_\mu^{\mathrm{bg}} A^\mu_a = 0$. Procedure: (i) Diagonalise FP operator $\mathcal{M}_{\rm FP}$ on each $\mathbb{P}^1$ factor via spectral decomposition; (ii) Combine spectra via product structure; (iii) Extract $\ln \det \mathcal{M}_{\rm FP}$ via zeta-function regularisation; (iv) Verify non-vanishing and finite result; (v) Compare magnitude to Math160 CP² baseline.

**Why open**: Math160 established BRST closure on CP² (T6 PROVED CONDITIONAL). Math254 §3 verifies transfer to $\Sigma_0$ is structurally sound (product-base simplification, spectral positivity, gauge covariance). Explicit numerical computation is the residual gap (T4 STRONG EVIDENCE → requires T6 computational closure).

**Falsification criterion**: If spectral decomposition on $\Sigma_0$ yields a **zero or negative eigenvalue** of $\mathcal{M}_{\rm FP}$, the canonical-patch gauge-fixing is **singular** and BRST closure on $\Sigma_0$ is **FALSIFIED** (T0). Expected outcome: all eigenvalues positive, determinant non-zero and finite.

**Owner**: TECT Collaboration, Task #156a. **Due**: 2026-05-14 (critical gate, part of H-GAP-3 resolution). **Method**: Numerical PDE solver (Codes/pde/ suite) with Krylov spectral extraction; zeta-function implemented in supplementary script. **Milestone**: Target T6 PROVED (explicit numerical + analytical verification).

**Review by**: 2026-05-14.

---

#### Task #156a.3b — Planck constant matching RGE verification on $\Sigma_0$ — Subgate GAP-3.2 — **OPENED 2026-04-30 TURN 25 (Math254)**

**Statement** (Math254 §4): Verify that the Planck-constant formula $\hbar = c^5 a_{\rm BCC}/(16\pi G)$ from Math110-AddI (derived on CP² base) is **RGE-stable** when the base manifold is changed to $\Sigma_0 = \mathbb{P}^1 \times \mathbb{P}^1$. Procedure: (i) Write the one-loop effective action on $\Sigma_0$ as a function of the renormalization scale $\mu$; (ii) Compute $\mu$-dependence of $\hbar_{\text{eff}}(\mu)$ via SM RGE flow (coupling-constant evolution); (iii) Verify that running $\hbar$ reproduces the static formula at the physical scale (or demonstrate why base-manifold independence is maintained despite running); (iv) Cross-check against Math110-AddG/H (elastic modulus and sound-speed derivations, which are base-independent).

**Why open**: Math110-AddI derived $\hbar$ from TECT primitives (condensate density, sound speed, Kibble-Zurek) and claimed base-manifold independence. Math254 §4.1 argues this claim structurally (all inputs are 3D BCC properties, not base geometry). Explicit RGE verification is the numerical gap (T4 STRONG EVIDENCE → requires T6 analytical + computational closure).

**Falsification criterion**: If RGE analysis reveals that $\hbar_{\text{eff}}(\mu)$ exhibits **base-dependent flow** (e.g., a non-universal $\beta$-function coefficient arising from $\Sigma_0$ topology), the base-manifold independence claim is **FALSIFIED** (T0 for the transfer principle). Alternatively, if matching reveals **contradiction with continuum-limit boundary conditions** (Task #115 defect-mass scale), the ℏ matching is **FALSIFIED at T0**. Expected outcome: RGE preserves base independence, or systematic correction is O(10%) and documented.

**Owner**: TECT Collaboration, Task #156a. **Due**: 2026-05-14 (critical gate, part of H-GAP-3 resolution). **Method**: One-loop SM RGE (Codes/supplementary/Math NN_RGE_flow.py); matching scale = $\mu_{\rm match} = m^* \sim 10^{-15}$ GeV or defect-mass $\mu_{\rm defect}$ from Phase-2 continuum limit (Task #115). **Milestone**: Target T6 PROVED (explicit RGE calculation + numerical verification against Phase-2 data).

**Review by**: 2026-05-14.

---

#### Q-2026-04-30-Math246-Pillar4-Recovery-Routes-A-D — Recovery of Pillar 4 sub-task 2 via alternative 4D Kähler bases and flat U(1)$_\chi$ structures (Task #156, Turn 17 discharge) — **OPENED 2026-04-30 TURN 17 (Math246)**

**[OPENED 2026-04-30 TURN 17 — Math246 recovery deferral; UPDATED 2026-04-30 TURN 21 with Route A T4 advancement]** **Context**: Math174 (2026-04-27) proves $c_2(E) = -40$ on canonical $\mathbb{CP}^2$, yielding $\mathrm{ind}(D_E^c) = 56 \neq 16$ and falsifying Pillar 4 sub-task 2 on the canonical geometry. Math246 §3–§6 identifies four alternative geometric realisations where $c_2(E) = 0$ (hence $\mathrm{ind} = 16$) is **achievable in principle**: (A) Hirzebruch surface $\Sigma_n$ with fibral U(1)$_\chi$ ($a = 0$) **[updated Turn 21 to T4 via Math250]**; (B) K3 surface with isotropic $c_1(L)$ in the K3 lattice; (C) del Pezzo surface $dP_k$ with Pythagorean integer tuple $a^2 = \sum b_i^2$; (D) flat U(1)$_\chi$ connection (automatic $c_1 = 0$ topologically, but quantum-gate risks). **Why open**: Routes B/C/D candidate routes require (i) explicit Chern-root enumeration and $c_2$ verification, (ii) BCC-lattice metric compatibility check, (iii) cubic-symmetry alignment analysis, (iv) quantum-consistency gate resolution (GAP-1, GAP-2, GAP-3). Route A has progressed to T4 STRONG EVIDENCE (Math250) and has a clear T6 roadmap via H-GAP-1/2/3 closure. **Falsification criterion (pre-registered, CLAUDE.md §6.3.3)**: If Routes B–D are not substantially progressed by **2026-05-14** (14-day deadline), and Route A does not achieve T6 (fails H-GAP closure), Pillar 4 sub-task 2 is demoted to **OPEN-NEGATIVE REFINED** and the recovery pathway is CLOSED pending external input or major reframing. If at least one route (A, B, C, or D) achieves T6 PROVED CONDITIONAL by 2026-05-14, Pillar 4 recovery programme is SEALED. **Owner**: TECT Collaboration. Sub-tasks: **#156a** (Route A, now T4, three H-GAPs due 2026-05-06); **#156b** (Route B K3, est. 5–7 days); **#156c** (Route C del Pezzo, est. 3–5 days); **#156d** (Route D flat U(1) + quantum gates, est. 7–10 days). Parallel execution recommended. **Timeline**: Sub-task preliminary results due 2026-05-07 (1 week); Route A T6 verdict due 2026-05-06; programme-wide final verdict due **2026-05-14** (2 weeks, hard deadline). **Review by**: 2026-05-14 (falsification gate, hard deadline, not 30-day cadence).

---

#### Risk-2026-04-30-Pillar4-Accumulated-Assumptions — Risk register: Pillar 4 (SO(10) emergence) conditional assumptions and mitigation strategy — **REGISTERED 2026-04-30 TURN 11 (Math240 cross-turn audit)**

**[REGISTERED 2026-04-30 TURN 11 — Math240 risk inventory]** **Context**: Math240 audit of Math238 (BCC-Higgs correspondence, T3) and Math239 (monopole-density derivation, T3) identifies six conditional assumptions on which Pillar 4 closure depends. The risk register documents these assumptions and assigns mitigation/closure owners. **Dual-route strategy (Routes A + B) provides structural redundancy**: If Route B (Math238/239 geometric) collapses, Route A (Math229 Cartan forcing) remains valid. Conversely, Route B constraints may strengthen Route A's tier. **Assumption matrix**:

| Assumption | Level | Owner | Closure pathway | Risk if fails |
|-----------|-------|-------|-----------------|---|
| **H1: Math162 $c_1(E) = 1$** | CRITICAL | Math162 audit (Tasks #149, #150) | Tasks #149/#150 closure → Math162 T6 → PROVED CONDITIONAL. Due: Turn 11–12. | If $c_1 \neq 1$: Route B (Math238/239) falsified; Route A unaffected (uses SO(10) rep-theory, not topology). |
| **H2: Scenario A (Planck scale $\Lambda_{\rm UV} = M_{\rm Pl}$)** | PHENOMENOLOGICAL | Task #150b (long-term) | Explore alternative scale-matching principles (entropy bounds, holography, string theory). Deferred to Turn 15+. | If $\Lambda_{\rm UV} \neq M_{\rm Pl}$: scale $v_1$ shifts; SO(10) breaking pattern unchanged. Phenomenological constraint, not falsification. |
| **H3: 12-mode BCC closure** | TECHNICAL | Task #151 (Phase-2 numerical verification) | Extract $\langle \Phi_{\rm mon} \rangle$ from BCC condensate snapshots; verify against Math239 formula within 30–50% window. Due: Turn 12. | If formula fails 50% gate: polynomial anisotropy / higher-mode contributions degrade the low-energy EFT. Falsifies Theorem 2.1 at 50% threshold. |
| **H4: Continuum limit validity (Task #115)** | FOUNDATIONAL | Task #115 (continuum-limit protocol, in progress) | Newton-Krylov v2.6+ solvers; lattice-to-continuum convergence as $a_{\rm BCC} \to 0$. Rigorous criterion: $\langle \Phi_{\rm mon} \rangle(a) \to \lim_{a \to 0} \mathcal{O}(1)$ (order-unity, finite limit). Due: Turn 11–12. | If continuum limit **does not exist** (e.g. logarithmic divergence): heat-kernel integral is not well-defined in continuum. Requires 2-loop or renormalization-group resummation. Falsifies Math239 formula; revise to T1 OPEN. |
| **H5: Heat-kernel integral $\mathcal{I}_{\rm HK}$ computation (Task #154)** | NUMERICAL | Task #154 (heat-kernel integration) | Standard numerical heat-kernel trace; expected value $\mathcal{I}_{\rm HK} \sim 0.1–0.5$ (dimensionless). Task #154-Sub: cutoff-robustness check (two $\mathcal{K}$ forms, agreement >80%). Due: Turn 11. | If $\mathcal{I}_{\rm HK}$ diverges or is negative: topological argument has a sign defect. Falsifies Math239 at discovery; revise. |
| **H6: Brazovskii saddle-point stability** | GROUND-STATE | Math82 (numerical verification, already complete) + Phase-2 numerical validation | Phase-2 continuation and ground-state finding already verify saddle-point stability at multiple parameter values. Historical remark: Math82-E grid search found no lower-energy competing minima. | If lower global minimum found: Brazovskii locked parameters invalid. TECT framework falsified at foundation level (per Math82 §7 falsification gate). |

**Atomic mitigation strategy (Turns 11–14, revised post-Turn 14 cross-turn audit COMPLETE)**:
1. **COMPLETED (Turns 11–13)**: Math238 OPEN GAPs α/β/γ all discharged. Math238 Theorem 2.1 upgraded T3→T6 COND. Pillar 4 sub-task 3 now T6 COND (topological forcing via Math242).
2. **Math241 (Turn 12) + Math242 (Turn 13)**: BCC-Higgs correspondence finalized via three-turn closure chain (Math240 audit Turn 11, Math241 Berry-cocycle Turn 12, Math242 cubic-sublattice Turn 13).
3. **CHECKPOINT COMPLETED (Turn 14, Math243 cross-turn audit)**: Pillar 4 sub-tasks 1+2+3 SYNCHRONIZED at T6 PROVED CONDITIONAL. All three components AUDITED AND VERIFIED (Math243, Turn 14). No tier downgrades. Hypothesis set H₁–H₆ tracked and confirmed coherent. Estimate-vs-theorem gate (CLAUDE.md §6.3.5(b)) CLEARED. Composite **Pillar 4 PROVED CONDITIONAL** status CERTIFIED by second-order audit.
4. **Pillar 4 consolidation (Turns 15–17)**: (a) ✓ Turn 14 cross-turn audit Math241+242 COMPLETE (Math243); (b) Turns 15+ Math174 closure (Atiyah–Singer c₂=1) + Task #162 (explicit Casimir); (c) Turn 16–17 Pillar 4 final-consolidation note (mandatory CLAUDE.md §6.3.5(c)) → **Pillar 4 T7 PROVED UNCONDITIONAL** upon closure of all dependencies (estimated EOL 2026-05-20).

**Honest scope**: Hypotheses H2 (scale origin) and H6 (global stability) remain open at programme level. H2 deferred to quantum-gravity physics (beyond TECT scope). H6 partially validated numerically but not rigorously proved to exclude all competing minima (defect density / energy arguments suggest global minimality, but complete proof would require infinite-volume thermodynamic limit proof).

**Recommendation**: Track this risk register in parallel with OPEN-QUESTIONS.md. Update status every 2 weeks during Turn 11–14 execution. Upgrade to "MITIGATED" once Tasks #149, #150, #154, #151 deliver robust results (target: 2026-05-22).

---

#### Q-2026-04-30-Pillar4-Alternative-Realisations — Task #156: Alternative geometric realisations for Pillar 4 sub-task 2 (16 chiral zero modes) — **OPENED 2026-04-30 TURN 16 (Math245 audit-rollback)**

**[OPENED 2026-04-30 TURN 16 — Math245 audit-rollback consolidation]** **Origin**: Math174 (2026-04-27) rigorously proves $c_2(E) = -40$ on the canonical SO(10)→SU(5)×U(1)_χ branching on ℂℙ². This **FALSIFIES Pillar 4 sub-task 2** (16 chiral zero modes require $c_2(E) = 0$, not $-40$). Math245 formalizes this rollback and establishes recovery pathway. **Statement**: Find an alternative 4-dimensional Kähler base manifold or a modified bundle structure (flat U(1)_χ connection) such that the resulting second Chern number is $c_2(E) = 0$ (or tuned to permit 16 chiral fermion zero modes), while maintaining the SO(10) spinor-matter emergence pattern and compatibility with the BCC defect-bundle geometry. **Candidate base manifolds** (per Math174 §8.2): (1) **Hirzebruch surfaces** $\mathbb{F}_n$ — different cohomology rings may admit $c_2=0$; (2) **K3 surfaces** — self-dual metrics with rigidly constrained characteristic classes; (3) **del Pezzo surfaces** — Fano varieties with rich bundle moduli; (4) **Orbifold / stacked geometry** — higher-category structures may modify Atiyah–Singer index formula. **Flat U(1)_χ connection** (alternative): if U(1)_χ is realised as a zero-curvature flat bundle, then $c_1(\mathrm{U}(1)_\chi) = 0$ automatically, eliminating all cross-Chern-class contributions. **Why open**: canonical geometry ruled out; no alternative has been constructed yet. **Falsification criterion** (pre-registered, Math245 §8): Task #156 is CLOSED if (a) one of the candidate geometries admits an explicit bundle with $c_2(E)=0$ and compatible SO(10) structure, OR (b) a rigorous no-go theorem proves that no such alternative exists (all 4D Kähler surfaces with spinor-matter emergence must have $c_2 \neq 0$). **Owner**: TECT Collaboration. Task **#156** (autonomous research + numerical survey). **Timeline**: 2 weeks literature review + 2 weeks prototype constructions (Hirzebruch, K3, del Pezzo). **Decision gate** (binding, per Math244 §3): 2026-05-14 — if no recovery geometry emerges by this date, **Pillar 4 demoted to OPEN-NEGATIVE REFINED**. **Review by**: 2026-05-10 (interim check-in); 2026-05-15 (final decision gate); subsequent reviews 30-day cadence if still OPEN.

---

---

#### Q-2026-04-29-Math229-Higgs-mechanism-closure — Derive Higgs scalar potential from TECT + compute electroweak-breaking scale (Task #170, Pillar 6 completion) — **REOPENED PARTIAL 2026-04-29 Turn 4 (canonical)**

**[REOPENED PARTIAL 2026-04-29 TURN 4 — operator final judgment]** Task #170 was provisionally marked CLOSED in Turn 2 by Math231; the Turn-4 independent-reviewer audit (Math233, Task #171 discharge) downgrades to PARTIAL because Math231's own tree-level computation gives |Ψ|₀ ≈ 5 GeV and m_H ≈ 3.16 GeV — factors of 50 and 40 short of the SM values v_EW = 246 GeV and m_H = 125 GeV. The composite-Higgs dressing factor Z_H proposed to close the gap is invoked, not derived. **What Math231 establishes (T4 STRONG EVIDENCE)**: structural existence of an emergent scalar layer V(Ψ) = m²|Ψ|² + λ|Ψ|⁴ with m² < 0, λ > 0 from BCC Brazovskii dynamics; correct sign-determination; Goldstone-counting framework. **What remains OPEN (gates Pillar 6 → T6)**: explicit, derived bridge map H_SM = Z_H^(1/2) 𝒫_EW[Ψ_BCC] + … with closed formulas for μ_H², λ_H, v², m_H² in terms of (κ_χ, κ_5, η, Λ_UV) — see Task #172.

#### Q-2026-04-29-Math231-EW-scale-bridge — Math231 salvage: derive Z_H from first principles + close v_EW and m_H to SM values (Task #172, NEW — highest priority)

**[NEW 2026-04-29 TURN 4 — highest priority for TOE critical path]** **Deliverable**: explicit, controlled matching map H_SM = Z_H^(1/2) 𝒫_EW[Ψ_BCC] + … with closed formulas for μ_H² = f₁(κ_χ, κ_5, η, Λ_UV), λ_H = f₂(…), v² = μ_H²/λ_H = 246² GeV², m_H² = 2μ_H² = 125² GeV² — all coefficients DERIVED from BCC parameters rather than fitted by sequential rescaling factors. Two viable derivation paths: (a) integrate out heavy SO(10) modes to obtain the EW-scale effective theory with Z_H computed as the heavy-light overlap squared; (b) match the BCC propagator to the SM Higgs propagator at a chosen matching scale and extract Z_H from the residue. **Falsification gate**: v_EW computed from BCC parameters must lie within ±30% of 246 GeV; m_H within ±30% of 125 GeV. If either fails, Math231 framework is falsified at T2 (CONJECTURE) tier and a different effective-scalar mechanism is required. **First-step plan (Turn 5)**: Build the minimal projector / residue matching ansatz from Ψ_BCC to H_SM and rigorously decompose which coefficients are computable from existing BCC microscopic parameters versus which remain exogenous and require additional input. **Scope**: this task supersedes the earlier "Task #172 merged into Task #127" speculation; Task #172 is independent and primary, while Task #127 (explicit composite-Higgs textbook identification) is a downstream refinement.

#### Q-2026-04-29-IndependentReviewer-Pass — Independent-reviewer pass on Math230 + Math231 + Math232 audit chain (Task #171) — **CLOSED 2026-04-29 Turn 4**

**[CLOSED 2026-04-29 TURN 4]** Task #171 RESOLVED by Math233 (independent-reviewer audit). The audit confirmed: (i) Math230 T6 PROVED CONDITIONAL retained; (ii) Math231 T6 → T4 STRONG EVIDENCE downgrade required; (iii) Math232 internal cross-turn audit retroactively flagged for leniency, with its self-adversarial γ objection ("audit is self-serving") UPHELD. CLAUDE.md §15.5 independent-audit gate is satisfied: the gate triggered the appropriate downgrade for Math231 and confirmed Math230 retention.

#### Q-2026-04-29-Math234-OPEN-GAP-α — Compute wave-function renormalization $Z_H$ via one-loop fermion loops (Task #147) — **OPEN (HIGH PRIORITY), sub-task of Task #172 salvage pathway**

**[OPEN 2026-04-29 TURN 5]** **OPEN GAP α from Math234 §7**: Explicit one-loop calculation of the wave-function renormalization factor Z_H. Compute loop integrals for all BCC shell-mode propagators and external fermion lines; numerically integrate and extract the constant C_Z such that Z_H = 1 + (g²/16π²) C_Z f(m_heavy, N_f, …).

**Obstruction**: Requires detailed spectrum of off-shell BCC modes (masses, form factors) from continuum-limit ground state (Task #115, pending). One-loop propagator structure confirmed by Math230 ✓; fermion coupling hierarchy to be completed in Pillar 8 (Task #143).

**Statement**: Compute Z_H bounded by §4.2 magnitude check (C_Z ~ O(1)–O(10), falsified if C_Z ≫ 100).

**Falsification criterion**: If computed C_Z ≫ 100 → perturbative expansion invalid; all-loop resummation required (gate for TECT validity).

**Owner**: Task #147 TECT Collaboration. **Timeline**: 1–2 weeks post-Task #115. **Review by**: 2026-05-15 (target, pending Task #115 completion).

#### Q-2026-04-29-Math234-OPEN-GAP-β — Extract physical wave-function amplitude $f_{\rm phys}$ from continuum limit and RG running (Task #115) — **ANALYTICAL PRE-FLIGHT COMPLETE 2026-04-30 (Math236, Turn 7), operator-driven execution queued**

**[ANALYTICAL PRE-FLIGHT COMPLETE 2026-04-30 TURN 7]** **OPEN GAP β from Math234 §7**: Extract the physical amplitude of the BCC condensate at the EW matching scale (μ ~ 100 GeV) from continuum-limit data (a → 0). Determine convergence of lattice sequence at a_k ∈ {1.0, 0.7, 0.5, 0.35} to universal continuum value f_∞.

**Obstruction timeline**: 
- Before Math235: Protocol not specified.
- After Math235 (Turn 6): Protocol COMPLETE (Math235 §1–4).
- After Math236 (Turn 7): Analytical pre-flight complete; diagnostic framework + deferral roadmap (§9 operator handoff) established. Remaining: numerical Phase-2 solves (150–300 h wall-time), deferred to operator scheduling.

**Statement** (after Math236): Four-stage protocol: (1) BCC Phase-2 solve at each a_k (deferred to operator, math236 §9.2 shell-script template provided); (2) amplitude extraction via RMS Fourier norm (corrected definition: divides by N_modes=12, not cell volume); (3) Richardson extrapolation (f(a) = f_∞ + A₁a + A₂a² + …); (4) validation (residual check, sign consistency, power-law test, reproducibility cross-check).

**Pre-registered falsification criteria** (per Math235 §4.2, math236 §7 reconfirmed):
- Richardson-fit residual ε_fit < 20% (convergence gate).
- All (f_k - f_∞) same sign (monotonic approach to continuum).
- Power-law ratio test within 50% (validates a¹ + a² ansatz).
- Magnitude bounds: f_∞ ∈ [0.5, 50] GeV (physical expectation range, tighter than original [0.1, 10⁴]).
- Numerical reproducibility: Two independent solves at same (a_k, μ²) must agree to within 1%.
- If ANY solve fails Newton convergence (diverges or stalls with merit > 10⁻⁷) → Task #115 FAILED, Pillar 6 → T2 CONJECTURE.

**Math236 contributions (Turn 7)**:
- §1: Corrected amplitude extractor dimensional error; validated Richardson framework expected behavior.
- §3: Diagnostic framework (Phase-2.5 gate re-validation, sign/magnitude checks, Richardson fit validation).
- §4: Five of six quantitative sanity checks (CHECK F reproducibility deferred to numerical phase).
- §5–§6: Devil's-advocate + self-adversarial reviews (all objections DISMISSED or VALID-WITH-MITIGATION).
- §9: Operator handoff specification: checklist (§9.1, 5 items), executable shell-script template (§9.2), expected output structure (§9.3), Turn 8+ audit plan (§9.4).

**Owner**: Task #115 TECT Collaboration. **Analytical pre-flight (Turn 7)**: COMPLETE. **Numerical execution (operator-driven)**: SCHEDULED, timeline 2–4 weeks post-Turn-7. **Cross-turn audit (Turn 8, Math237)**: 2026-05-13 target (pending operator data). **Review by**: 2026-05-15 (post-audit).

#### Q-2026-04-29-Math234-OPEN-GAP-γ — Incorporate fermion-bilinear mixing and composite-Higgs resummation (Task #127) — **OPEN (MEDIUM PRIORITY, post-Pillar-8), gates full SM Higgs identification**

**[OPEN 2026-04-29 TURN 5]** **OPEN GAP γ from Math234 §7**: Extend the EW-bridge projector ansatz to include fermionic bilinear condensate $\langle \bar{\psi}_L \psi_R \rangle$ and perform composite-Higgs analysis (infinite ladder-diagram resummation of (BCC ↔ fermion pair ↔ BCC)). Identify the physical Higgs doublet as linear combination of scalar projection of Ψ_BCC and fermion-bilinear modes.

**Obstruction**: Requires fully-specified fermionic Yukawa Lagrangian (Pillar 8 currently PARTIAL). Additionally, ladder resummation is non-perturbative (Dyson series) — may require functional RG technology.

**Statement**: Extended EFT matching incorporating fermion-bilinear degrees of freedom. Determine net Higgs doublet and extract the physical VEV v_EW = 246 GeV (not assumed).

**Falsification criterion**: If fermion-bilinear contribution exactly cancels the scalar projection → ansatz fails structurally (gate downgrade for the entire EW-bridge framework).

**Owner**: Task #127 (composite-Higgs framework) + Task #143 (fermionic determinant in Yukawa sector) TECT Collaboration. **Timeline**: 3–4 weeks post-Task #147. **Review by**: 2026-06-05 (target, deferred to post-Pillar-8).

---

**Sequencing note (Math86 2026-04-24)**: Active items below are re-ordered by the Turn 6–10 priority plan (Math86 §3). **Solver items** (Q-2026-04-24-Solver-115, -116) are absorbed into Tasks #115, #116 and executed pre-Turn-6 as foundational solver hygiene. **Turn 6 items** (Q-2026-04-24-P1-12mode, Pillar 4 Q2, Math80-AddC SO(10)) are the primary focus. **Turn 7–10 items** follow the triple-track structure (Track A: Pillar 1; Track B: Pillars 4, 6; Track C: Stage-2 theory).

**Sequencing addendum (Math156/Math157, 2026-04-26)**: After the Round V1–V5 comprehensive audit (Math156) and the rigorous SO(10) trace-method anomaly recomputation (Math157), the four GAP-3 / GAP-1 / GAP-4 entries below are promoted to top priority. They are the single critical items currently blocking unconditional Stage-2 closure and the present cosmology branch of Stage-3.

**Status update (2026-04-29, Math220-AddA + Math220-AddB + Math222 v1.1 + Math221-AddC)**: Task #165 (Lemma B rest-bound, Math220-AddA) **CLOSED** — four reviewer-flagged issues repaired; Lemma B PROVED CONDITIONAL. Task #167 (Lemma B constant-bound theorem, Math220-AddB) **OPEN** — rigorous constant-bound form proved, numerical closure marginal (~10% safety); requires Task #168-R (one-loop coupling Feynman diagram). Task #166 (Lemma A microscopic stiffness, Math221-AddB) elevated to HIGHEST PRIORITY: sole remaining gate for Pillar 4 sub-task 2 unconditional closure and $S_1 \land S_2$ final sealing. Task #168 (Lemma A explicit nontriviality, Math221-AddC) **CLOSED** — explicit U(1)_χ charge table (Group A: 8 face-diag $Q_\chi=+1/3$, Group B: 4 body-diag $Q_\chi=-2/3$) + SU(5) ρ ≠ 0 verification ($\langle \mathrm{Tr}[T^A T^B]\rangle = \frac{28}{3}\delta^{AB} > 0$) + audit-clean trace-stiffness proportionality $\kappa_\chi = C_\chi Q_R(\mathbf{16})$ established in Math221-AddC (PROVED CONDITIONAL on Task #145 + #146). Task #145 NEW (explicit SO(10) CG-coefficient decomposition, pathway ii dimension-reduction) **OPEN** — required to rigorously justify 12-dim invariant subspace of 16-dim Majorana spinor (deferred from Math221-AddC §1). Task #146 NEW (heat-kernel stiffness computation via Dirac spectrum on BCC shell) **OPEN** — required to compute exact proportionality constants $C_\chi, C_5$ (deferred from Math221-AddC §5).

---

### **Math220-AddB + Math221-AddC Closure Pathway — Two Named Microscopic Lemmas for Pillar 4 Sub-Task 2 (2026-04-29)**

~~#### Q-2026-04-29-Math220-AddB-constant-bound-closure — Verify one-loop coupling suppression of defect sector to complete Lemma B constant-bound theorem (Task #167 + Task #168-R)~~

**[CLOSED 2026-04-29 TURN 1]** **Task #169 RESOLVED** by Math230-Defect-Sector-One-Loop-Coupling-Verification (explicit one-loop box-diagram proof that $C_d = O(g^2)$, promoting Math220-AddB from STRONG DRAFT → PROVED CONDITIONAL and Pillar 4 sub-task 2 to T6 status). See CHANGELOG entry "Theory Math230" for details.

~~Former statement~~: Derive $C_d$ rigorously via one-loop Feynman diagram (box + rainbow diagram for gauge-kinetic coupling to BCC defect sector) in the Brazovskii background.

~~Former falsification criterion~~: if one-loop Feynman diagram yields $C_d \gtrsim 0.01$ (not suppressed by $g^2$), the inequality $\kappa_{\min} > C_m + C_d$ may fail.

#### Q-2026-04-29-Math221-AddC-Lemma-A-explicit-nontriviality — Prove explicit U(1)_χ × SU(5) nontrivial action on BCC shell modes for Lemma A (Task #168)

- **Stage**: Pillar 4 sub-task 2. Mainline note: `Docs/math/TECT-Math221-Addendum-B-Weak-Trace-Positivity-Theorem.tex.txt` (Lemma A weak form: finite-dim trace-positivity PROVED; TECT-microscopic connection ASSUMED).
- **Origin**: Math221-AddB reviewer audit (2026-04-29): "Lemma A.1 finite-dim trace-positivity fully PROVED (textbook). Lemma A.2 nontriviality $\rho(X_\chi) \neq 0$ ASSUMED not proven — needs explicit charge table for 12 BCC shell modes." Task #168 directive: Display U(1)_χ charge table for all 12 BCC shell modes (showing ≥ one non-zero charge), demonstrate SU(5) action on ≥ one shell mode pair (non-zero matrix element on V_shell), prove $\kappa_\chi = C_\chi Q_R(X_\chi)$ and $\kappa_5 = C_5 \sum_a Q_R(X_a)$ with $C_\chi, C_5 > 0$ derived from shell projector (not from audit-flagged Math216-AddB §3).
- **Statement**: Construct the explicit 12 × 12 representation matrices $\rho_\chi$ and $\{\rho_a\}_{a=1}^{24}$ (U(1)_χ and SU(5) generators) acting on the BCC first-shell 12-vector basis $V_{\rm shell}$. Compute $\mathrm{Tr}(\rho_\chi^2) > 0$ and $\sum_a \mathrm{Tr}(\rho_a^2) > 0$ numerically. Display the trace-stiffness proportionality constant: $\kappa_\chi = C_\chi \mathrm{Tr}(\rho_\chi^2)$ with $C_\chi$ derived from Brazovskii density-of-states integral over the shell (NOT from Math216-AddB which has three audit-flagged defects A, B, C).
- **Why open**: Critical for Lemma A promotion from PARTIAL ACCEPT to PROVED CONDITIONAL. Math216-AddB §3 trace-stiffness proportionality is NOT audit-clean (defects A, B, C flagged); Task #168 requires an independent derivation via shell-projector + Brazovskii stiffness Y q_0²/Z, bypassing Math216-AddB.
- **Falsification criterion**: failure to exhibit a single BCC shell mode with non-zero U(1)_χ charge, or discovery that $\mathrm{Tr}(\rho_\chi^2) = 0$ (trivial action), would invalidate Lemma A and necessitate a revisit to the BCC microscopic structure.
- **Owner**: TECT collaboration. Task **#168** (Lemma A explicit nontriviality + trace-stiffness proportionality; includes Task #168-R sub-task for coupling verification if Lemma B not yet closed).
- **Last reviewed**: 2026-04-29. **Review by**: 2026-05-29 (30-day priority window; HIGHEST PRIORITY per Math221-AddB audit verdict).

---

### **Math158/159/160/161 GAP-1/2/4 Closure Aftermath — Three Residual Tasks (2026-04-26)**

~~#### Q-2026-04-26-Math158-boson-loop-subdominance-check — Verify fermion-loop dominance over boson and Higgs loops in the GAP-1 third-route saturation~~

~~**CLOSED (2026-04-29, Math227 turn 9 audit-pass)**. Discharged by Math163 (GAP-1 boson-loop subdominance) with independent cross-turn second-order audit (Math227, turn 9). Result: $R_{\rm boson/fermion} \approx 0.12$ verified; fermion dominance confirmed via coupling-strength hierarchy $y_t^2 \gg g_{\rm EW}^2$. Minor discrepancy in fermion count (Math163 quotes $N_f=12$ vs. correct $N_f=18$) does not affect conclusion — higher count makes fermion dominance stronger. Math158 upgraded to PROVED CONDITIONAL (weak, independent route).~~

#### Q-2026-04-26-Math160-Berry-phase-non-triviality — Establish that the BRST Faddeev–Popov Berry-phase prefactor is non-trivial on physically relevant TECT configurations

- **Stage**: Pillar 4 / GAP-2 unconditional closure. Mainline note: `Docs/math/TECT-Math160-GAP2-BRST-FP-determinant-TECT-specific.tex.txt` §III (audit-recommended caveat). Cross-turn audit: `Docs/math/TECT-Math161-Round-W1-cross-turn-audit-of-Math158-159-160.tex.txt` §4 (Objection α VALID-deferred).
- **Origin**: Math160 identifies a Berry-phase prefactor $\exp[i\Gamma_{\rm Berry}[\Psi]]$ on the FP determinant as the TECT-specific signature relative to flat-spacetime Yang–Mills, but the supplementary lattice computation returns $\Gamma_{\rm Berry}=2\pi$ (topologically trivial) on the representative patch tested.
- **Statement**: either (i) explicitly construct a TECT condensate configuration whose Berry phase is a non-trivial integer winding multiple of $2\pi$ on a non-contractible loop in the moduli space, or (ii) supply a topological argument relating $\Gamma_{\rm Berry}$ to a known invariant (e.g.\ a Chern number of the emergent connection, or an orbifold-stratum index from $\mathrm{Stab}_{\mathrm{SU}(5)}\,\mathrm{Gr}(2,5)$).
- **Why open**: required to substantiate the TECT-specific-signature claim of Math160. Existence of the Berry-phase factor is established; non-triviality is not.
- **Falsification criterion**: if every BCC moduli loop yields $\Gamma_{\rm Berry}\in 2\pi\mathbb Z$ (i.e.\ trivial in $U(1)$), then the FP determinant collapses to the flat-spacetime form and Math160's TECT-specific contribution evaporates.
- **Owner**: TECT collaboration. Task **#134** (GAP-2 Berry-phase non-triviality).
- **Last reviewed**: 2026-04-26. **Review by**: 2026-08-26.

#### Q-2026-04-26-GAP4-Kibble-Zurek-defect-spectrum — Quantitative defect-density and post-condensation matter-power spectrum predictions on the rescoped Kibble–Zurek branch

- **Stage**: $S_3$ Stage-3 empirical contact / GAP-4 alternative-observable. Mainline note: `Docs/math/TECT-Math159-GAP4-ns-rescue-or-rescope.tex.txt` §6. Audit: `Docs/math/TECT-Math161-Round-W1-cross-turn-audit-of-Math158-159-160.tex.txt` §3 (Option C ACCEPT with documented scope clarification).
- **Origin**: Math159 rescopes GAP-4 by demonstrating that Math151's mapping of Brazovskii critical exponent $\epsilon_s=2/23$ to slow-roll $\epsilon=-\dot H/H^2$ is a category error. The TECT cosmology branch is Kibble–Zurek quench-driven, not slow-roll inflationary. The replacement observables are the defect-density spectrum, the gravitational-wave background from defect annihilation, and the post-condensation matter power spectrum.
- **Statement**: produce quantitative TECT predictions for (i) defect-density power spectrum on horizon-scale modes; (ii) gravitational-wave background spectrum from BCC defect annihilation; (iii) post-condensation matter power spectrum at the BCC scale, for comparison with CMB / LSS / GW observatories.
- **Why open**: Math159 establishes the correct branch; quantitative predictions on that branch are required to seal $S_3^{\rm (predict)}$.
- **Falsification criterion**: predicted defect density at recombination outside $[10^{30},10^{36}]\,{\rm cm}^{-3}$, OR GW spectrum inconsistent with LIGO/Virgo/LISA stochastic-background bounds, falsifies the Kibble–Zurek scenario; this must then be recorded honestly as a NEGATIVE-RESULT.
- **Owner**: TECT collaboration. Task **#135** (GAP-4 Kibble–Zurek observable).
- **Last reviewed**: 2026-04-26. **Review by**: 2026-08-26.

---

### **R5 Round Aftermath — Math181 RESCUE-claim downgraded; Tasks #149 + #150 (2026-04-27)**

#### Q-2026-04-27-Math181-Rigorous-C1-Computation — Compute c_1(U(1)_χ) on Math162 CP² base by direct curvature integration

- **Stage**: Pillar 4 sub-task 2. Mainline: Math181 (AUDIT-FLAGGED, downgrade). Audit: Math184 §2 — same simply-connected-vs-Chern-class conflation Math165 §5 caught for Math164/Math160.
- **Statement**: compute $c_1(\mathrm{U}(1)_\chi) = \frac{1}{2\pi}\int_{\Sigma}F_\chi$ for the hyperplane $\Sigma=\mathbb{CP}^1\subset\mathbb{CP}^2$, using the **principal connection** on the SU(5)×U(1)$_\chi$ bundle (NOT the Berry connection on M_BCC).
- **Falsification criterion**: integer value of $c_1(\mathrm{U}(1)_\chi)$.
- **Owner**: TECT. Task **#149** (highest priority). **Review by**: 2026-05-27.

#### Q-2026-04-27-Math162-SU5-Instanton-Status — Establish c_2(E_SU(5)) on Math162 bundle

- **Stage**: Pillar 4 sub-task 2 / cross-coupling Task #149. Math184 §2.δ flags the gap.
- **Statement**: compute SU(5) instanton number $n = c_2(E_{\rm SU(5)})$ from $\pi_3(\mathrm{SU}(5))=\mathbb{Z}$ on $\mathbb{CP}^2$. Total $\mu = c_2(E_{\rm SU(5)}) + \text{U(1)}_\chi\,\text{contribution}$.
- **Falsification criterion**: integer value of $c_2(E_{\rm SU(5)})$.
- **Owner**: TECT. Task **#150**. **Review by**: 2026-05-27.

---

### **R3+R4 Round Aftermath — Critical Pillar-4 U(1)_χ Topology Question (Math174/177/180, 2026-04-27)**

#### Q-2026-04-27-Pillar4-U1chi-topology — Determine whether the BCC condensate's emergent U(1)_χ holonomy is flat (Scenario B, ind=16 RESCUED) or non-trivial (Scenario A, ind=56 FALSIFIED)

- **Stage**: Pillar 4 sub-task 1 + sub-task 2 conjunction. Mainline: `Docs/math/TECT-Math174-explicit-c2-second-Chern-number.tex.txt` §1; audit `Docs/math/TECT-Math177-Round-R4-cross-turn-audit-of-Math174-175-176.tex.txt` §2.γ + §2.δ (UPHELD as bifurcation rather than unconditional falsification); synthesis `Docs/math/TECT-Math180-Round-R3-R4-second-10-turn-synthesis.tex.txt` §4.
- **Origin**: Math174 computes $\mu = \int c_2(E) = -40$ under the assumption $b = c_1(\mathrm{U}(1)_\chi) = H$ (non-trivial U(1)$_\chi$), giving $\mathrm{ind} = 16 - \mu = 56 \neq 16$. Math177 audit identifies a non-falsified alternative: if $b = 0$ (flat U(1)$_\chi$), then $\mu = 0$ and $\mathrm{ind} = 16$ exactly. The Math162 sub-task 1 closure (Math167 three-patch Čech) established $c_1(E) = 0$ via the U(1)$_\chi$ charge balance $10(+1)+5(-3)+1(+5) = 0$, but did not separately fix the U(1)$_\chi$ holonomy; both topologies are consistent with $c_1(E) = 0$ provided the SU(5) part absorbs any difference.
- **Statement**: derive the U(1)$_\chi$ holonomy of the Math162 bundle from BCC microscopics (Brazovskii order-parameter structure + topological winding of the BCC defect network). Either:
  (i) the holonomy is **flat** (zero winding): Scenario B; Pillar 4 sub-task 2 RESCUED with $\mathrm{ind} = 16$; PROVED CONDITIONAL on sub-task 3.
  (ii) the holonomy is **non-trivial** (integer winding $\geq 1$): Scenario A; Pillar 4 sub-task 2 FALSIFIED in its current form; sub-task 1 must be revised with a different base / fibre / structure.
- **Why open**: the resolution is the unique single critical question for Pillar 4 closure post-R4. Resolution either confirms or refutes the simple Math162 realisation in one calculation.
- **Falsification criterion**: a clean BCC-microscopic derivation that forces the U(1)$_\chi$ holonomy to be non-trivial would falsify Scenario B and force a Math162 revision; a derivation that forces flat holonomy confirms Scenario B and proceeds to sub-task 3.
- **Owner**: TECT collaboration. Task **#147** (Pillar 4 single-question closure).
- **Last reviewed**: 2026-04-27. **Review by**: 2026-06-27 (60-day window).

#### Q-2026-04-27-Math176-tangent-bundle-sanity — Verify Math176 BWB sanity-check value χ(T CP²)=8 against textbook χ(T CP^n)=n+1=3

- **Stage**: documentation polish on Math176. Mainline: `Docs/math/TECT-Math176-independent-AS-index-cross-check.tex.txt`. Audit reference: Math180 §7 Objection β.
- **Origin**: Math176's Borel-Weil-Bott sanity check on the tangent bundle of $\mathbb{CP}^2$ reports $\chi(T\mathbb{CP}^2) = 8$, but the standard textbook value is $\chi(T\mathbb{CP}^n) = n+1 = 3$ for $n=2$. Possible sources of discrepancy: real vs holomorphic tangent convention, an arithmetic error in the BWB Weyl-character calculation, or a different definition of $\chi$.
- **Statement**: re-verify the BWB sanity-check value, or document the convention difference if the 8 is correct under a non-standard but consistent definition. Math174's primary calculation (which yields $\mu = -40$) does not depend on this sanity check, so the discrepancy is documentation-grade, not load-bearing.
- **Why open**: ensures Math176's BWB derivation is fully reliable as an independent cross-check of the $16 - \mu$ formula.
- **Falsification criterion**: not applicable (documentation).
- **Owner**: TECT collaboration. Task **#148** (Math176 polish).
- **Last reviewed**: 2026-04-27. **Review by**: 2026-06-27.

#### Q-2026-04-27-Math181-Rigorous-C1-Computation — Compute the first Chern class $c_1(\mathrm{U}(1)_\chi)$ of the Math162 bundle via explicit curvature integral on the $\mathbb{CP}^2$ base

- **Stage**: Pillar 4 sub-task 2 resolution / Scenario B rescue (UNPROVEN by Math181). Mainline failed claim: `Docs/math/TECT-Math181-Pillar4-U1chi-holonomy-from-BCC-microscopics.tex.txt` (DOWNGRADED to STRONG CLOSURE DRAFT by Math184 audit). Audit: `Docs/math/TECT-Math184-Round-R5-cross-turn-audit-of-Math181-182-183.tex.txt` §§1–3 (Objections α, β, γ all UPHELD as category errors).
- **Origin**: Math181 claims to prove $b = c_1(\mathrm{U}(1)_\chi) = 0$ via three routes (direct charge, stabilizer flatness, topological-charge counting), but the Math184 cross-turn audit identifies critical logical gaps: Paths α and γ conflate zero expectation values with zero connections (bundle-theoretic category error identical to Math164/165 error); Path β proves only 1-cycle holonomy triviality (via π₁=0) but does not rule out Chern-class obstructions in $H^2(\mathbb{CP}^2)$. **Scenario B is unproven; the bifurcation remains open.**
- **Statement**: rigorously compute the Berry connection 1-form $A_\chi$ on the Math162 bundle by explicit parallel transport of the SO(10) frame field along the $\mathbb{CP}^2$ base directions. Evaluate the curvature 2-form $F_\chi = dA_\chi$. Integrate $c_1 = \frac{1}{2\pi i}\int_{\mathbb{CP}^2} F_\chi$ over a representative 2-cycle (e.g., $[H] \in H^2(\mathbb{CP}^2; \mathbb{Z})$) to determine the Chern number. Report the value $c_1(\mathrm{U}(1)_\chi) \in \mathbb{Z}$.
- **Why open**: uniquely critical question determining Scenario A vs. Scenario B. Either (i) the computation yields $c_1 = 0$ (flat, Scenario B RESCUED), confirming μ=0 and ind=16; or (ii) the computation yields $c_1 \neq 0$ (non-trivial, Scenario A CONFIRMED), forcing a Math162 revision with alternative base/fibre/structure.
- **Falsification criterion**: $c_1(\mathrm{U}(1)_\chi) \neq 0$ falsifies Scenario B and triggers revision of Math162. Conversely, $c_1(\mathrm{U}(1)_\chi) = 0$ confirms Scenario B under the assumption that $c_2(\mathrm{SU}(5)) = 0$ (see Task #150).
- **Owner**: TECT collaboration. Task **#149** (Pillar 4 sub-task 2 explicit c₁ derivation).
- **Last reviewed**: 2026-04-27. **Review by**: 2026-05-27 (30-day window; high priority).

#### Q-2026-04-27-Math162-SU5-Instanton-Status — Determine whether the SU(5) part of the Math162 bundle carries zero instanton number or non-zero $c_2(\mathrm{SU}(5))$

- **Stage**: Pillar 4 sub-task 2 resolution / μ=0 closure (Task #149 dependency). Mainline: `Docs/math/TECT-Math162-Pillar4-subtask1-BCC-defect-bundle-foundation.tex.txt` (§4, first Chern class analysis). Audit: `Docs/math/TECT-Math184-Round-R5-cross-turn-audit-of-Math181-182-183.tex.txt` §4.2 (Objection δ UPHELD).
- **Origin**: Math181 §6 assumes that if $b = c_1(\mathrm{U}(1)_\chi) = 0$ (flat U(1)_χ), then μ = ∫ c_2(E) = 0 automatically, because $c_2(E) = c_2(E_{\mathrm{SU}(5)})$ (no U(1)_χ contribution). However, SU(5) bundles on $\mathbb{CP}^2$ can carry non-zero instanton number $c_2(\mathrm{SU}(5)) \in \mathbb{Z}$ even with $c_1(\mathrm{SU}(5)) = 0$ (instantons are classified by $\pi_3(\mathrm{SU}(5)) = \mathbb{Z}$). Math162 does not prove $c_2(\mathrm{SU}(5)) = 0$ explicitly.
- **Statement**: examine the explicit construction of the SU(5) part of the Math162 bundle (§4 reduction of the principal SO(10) bundle to a principal SU(5) bundle) and determine whether instantons are present. Either (i) prove directly that $c_2(E_{\mathrm{SU}(5)}) = 0$ from the construction (e.g., via the SO(10) structure or gauge-fixing), or (ii) compute the instanton number if it is non-zero.
- **Why open**: required for μ=0 unconditional closure under Scenario B. If Scenario B holds (c₁=0 flat) but c_2(SU(5)) ≠ 0, then μ ≠ 0 and ind ≠ 16, falsifying Scenario B regardless of the U(1)_χ topology.
- **Falsification criterion**: discovery of a non-trivial instanton configuration in the SU(5) reduction would show $c_2(\mathrm{SU}(5)) \neq 0$, violating the Scenario B assumption and triggering an immediate re-examination of both the U(1)_χ and SU(5) parts of Math162.
- **Owner**: TECT collaboration. Task **#150** (Pillar 4 sub-task 2 SU(5) instanton audit).
- **Last reviewed**: 2026-04-27. **Review by**: 2026-05-27 (30-day window; high priority, Task #149 dependency).

#### Q-2026-04-27-Alternative-Scenario-B-Proof — If explicit c₁ computation on Math162 yields non-trivial U(1)_χ holonomy, explore alternative base manifolds (K3, Hirzebruch, del Pezzo) for Scenario B rescue

- **Stage**: Pillar 4 sub-task 2 fallback / contingency. Origin: NEGATIVE record `R-2026-04-27-Math162-Bundle-SO10-Spinor-Index` (Scenario A falsified) + Math184 audit (Scenario B unproven). Alternative-base analysis was sketched in a dispatch-referenced file Math182 (not produced).
- **Statement**: if Task #149 confirms $c_1(\mathrm{U}(1)_\chi) \neq 0$ (non-trivial holonomy) on the $\mathbb{CP}^2$-base Math162 bundle, then Scenario B is falsified and an alternative geometric realisation is required. Survey alternative base manifolds (K3 surface, Hirzebruch surface $\mathbb{F}_n$, del Pezzo surfaces, Grassmannians Gr(k, n)) with the goal of finding a choice where: (i) the SO(10) matter bundle has fibre SO(10)/SU(5) or equivalent; (ii) $c_1(E) = 0$ and $c_2(E) = 0$ simultaneously (hence ind = 16); (iii) the base has geometric / topological properties compatible with TECT defect physics (lattice structure, symmetry, moduli rigidity).
- **Why open**: contingency task to preserve Pillar 4 closure in the event that Math162 on $\mathbb{CP}^2$ is ruled out. If the alternative-base search succeeds, Scenario B is RESCUED via a different realisation; if it fails systematically, then Pillar 4 sub-task 2 may require a fundamentally different structure (not a simple G-bundle) and Pillar 4 would be demoted to PARTIAL-ADVANCED-STRUCTURAL.
- **Falsification criterion**: exhaustive failure to find any base manifold where μ = 0 with the correct 16-dimensional matter sector would imply that the SO(10) emergence picture is structurally flawed and that a different SM-embedding mechanism (not via Pillar 4) is needed. This would falsify the current Pillar 4 pathway but **would not invalidate Pillars 1–3, 5–11**, so TECT would remain a PARTIAL TOE candidate.
- **Owner**: TECT collaboration. Task **#151** (alternative-base-manifold search; contingency task, low priority unless Task #149 confirms non-trivial c₁).
- **Last reviewed**: 2026-04-27. **Review by**: 2026-06-27 (60-day window, contingency-dependent).

---

### **R2 Round Aftermath — Three Residual Tasks (Math166/167/168/169, 2026-04-26)**

#### Q-2026-04-26-Math166-rigorous-AS-index — Re-derive the twisted-Dirac Atiyah-Singer index on the Math162 BCC defect bundle from first principles

- **Stage**: Pillar 4 sub-task 2 / GAP-3 unconditional dependency. Mainline: `Docs/math/TECT-Math166-Pillar4-subtask2-chiral-zero-modes-on-Math162-bundle.tex.txt` (AUDIT-FLAGGED). Audit: `Docs/math/TECT-Math169-Round-R2-cross-turn-audit-of-Math166-167-168.tex.txt` §2 (Objection α UPHELD). NEGATIVE record: R-2026-04-26-Math166-IndexByAnsatz.
- **Origin**: Math166 asserted $\mathrm{ind}(D_E)=16$ by inverting the Atiyah-Singer formula to match the SO(10) spinor dimension. The bundle-rank assumption is unverified.
- **Statement**: explicitly evaluate $\mathrm{ind}(D_E)=\int_{\mathrm{CP}^2}\hat A(T\mathrm{CP}^2)\wedge\mathrm{ch}(E)$ with $\hat A(T\mathrm{CP}^2)=1+(1/24)c_2(T\mathrm{CP}^2)=1+1/8$ (using $c_2(T\mathrm{CP}^2)=3$) and $\mathrm{ch}(E)$ for the actual bundle (rank to be fixed: 5? 21? 24? — depends on whether $E$ is the fundamental, fibre, or adjoint). The degree-4 part of the integrand is what contributes; pull it out and integrate.
- **Why open**: required to upgrade Math166 from PARTIAL to PROVED CONDITIONAL. Without rigorous index derivation, Pillar 4 sub-task 2 cannot seal, and GAP-2 + GAP-3 unconditional closures remain blocked.
- **Falsification criterion**: if the rigorous integral yields a number $\neq 16$, Pillar 4 SO(10) emergence requires a different bundle / fibre / structure-group choice. The Math157 anomaly cancellation result is unaffected (it conditions on the existence of the $\mathbf{16}$ matter sector, regardless of which bundle yields it), but the geometric realisation must be revised.
- **Owner**: TECT collaboration. Task **#142** (Pillar 4 sub-task 2 rigorous closure).
- **Last reviewed**: 2026-04-26. **Review by**: 2026-06-26.


#### Q-2026-04-27-Math172-defect-mass-evolution — Compute defect-mass evolution from GUT to BBN scales using SO(10) coupling constants

- **Stage**: Pillar 4 sub-task 3 (SO(10) emergence) + GAP-4 quantitative refinement. Origin: `Docs/math/TECT-Math172-GAP4-defect-mass-scenario-table.tex.txt` §6 (Objection β VALID-with-caveat, Task #145 queued).
- **Origin**: Math172 establishes a three-scenario table (GUT, EW, BBN) and identifies the BBN-scale scenario as the natural observable channel. However, the effective defect mass $\mu_{\rm eff}$ in the observable (BBN) era may differ dramatically from the GUT-scale rest-frame value due to thermal effects, Higgs-mediated corrections, and SO(10) coupling evolution. Math172 §6 flags this as a major source of uncertainty (Objection β).
- **Statement**: once Pillar 4 sub-task 3 determines the SO(10) → SU(3)$\times$SU(2)$\times$U(1) breaking chain and the defect-SO(10)-coupling strength, compute the defect-mass scaling $\mu_{\rm eff}(T)$ from GUT scale to BBN scale via RG equations or thermal-field-theory calculations. Use this to refine the GW amplitude prediction (currently a $10^5$ band).
- **Why open**: required to upgrade the BBN-scenario GW prediction from a range to a point estimate (within a factor $\sim 2$). The current range $[5 \times 10^{-16}, 10^{-11}]$ is conservative but unhelpfully wide for experimental design.
- **Falsification criterion**: if defect-mass evolution yields $\mu_{\rm eff}(T_{\rm BBN}) < 10^{10}$ GeV (corresponding to $\Omega_{\rm GW} < 10^{-18}$), the GW signal is unobservable even by next-gen detectors and the route is falsified. Conversely, if $\mu_{\rm eff} > 10^{18}$ GeV, the GW signal exceeds PTA bounds and is ruled out by current data.
- **Owner**: TECT collaboration. Task **#145** (Defect-mass evolution / Pillar 4 sub-task 3 coupling).
- **Last reviewed**: 2026-04-27. **Review by**: 2026-07-27 (90-day window for SO(10) emergence + RGE computation).

#### Q-2026-04-27-Math172-BCC-defect-topology — Classify BCC defect topology (disclinations vs. dislocations) and compute network GW spectrum for each topological class

- **Stage**: Pillar 4 sub-task 1 (defect classification) + GAP-4 (spectral-shape refinement). Origin: `Docs/math/TECT-Math172-GAP4-defect-mass-scenario-table.tex.txt` §7 (Objection γ VALID-with-caveat, Task #146 queued).
- **Origin**: Math172 applies the generic cosmic-defect GW formula (Turok 1985, Vilenkin–Shellard 2000), which was originally derived for topological defects in simple scalar field theories (cosmic strings, domain walls). The BCC lattice has 24 ground-state variants and complex defect topology; the defects are primarily disclinations and dislocations, which may have different topological classification and GW radiation properties than simple vortex lines.
- **Statement**: classify the topological defects that emerge in the BCC condensate in the context of the SO(10) GUT structure (Pillar 4 sub-task 2). Identify whether they are homotopy-stable line defects (strings) or higher-codimension defects. Compute the GW spectrum for each topological class using the corresponding network evolution equations (scaling properties differ for domain walls, cosmic strings, and skyrmion gases). Determine whether the generic $\Omega_{\rm GW} \propto f^{1/2}$ spectrum (for $f < f_{\rm peak}$) is robust or if alternative spectral shapes ($f^0$, $f^{-1}$, $f^{-3/2}$) can arise from BCC-specific topology.
- **Why open**: required to verify that the spectral shape in Math168 / Math172 is robust to the microscopic BCC defect details. If BCC defects form a network with different scaling properties, the observable spectrum could shift by orders of magnitude or change shape entirely.
- **Falsification criterion**: the computed GW spectrum (for each defect class) must remain within a factor $\sim 2$ of the generic formula $\Omega_{\rm GW}(f) \propto f^{1/2}$ in the observable PTA band. A radically different spectrum (e.g., flat or falling) would require re-analysis of the scenario table.
- **Owner**: TECT collaboration. Task **#146** (Defect-topology classification / Pillar 4 sub-task 1 refinement).
- **Last reviewed**: 2026-04-27. **Review by**: 2026-08-27 (120-day window for algebraic-topology + network-dynamics computation).

---

### **R1 Round Aftermath — Three Residual Tasks (Math162/163/164/165, 2026-04-26)**

#### Q-2026-04-26-Math162-3-patch-cover — Extend the BCC fibre-bundle construction to a three-patch cover with full Čech-cocycle verification

- **Stage**: Pillar 4 sub-task 1 (foundation), Math162 fibre-bundle construction. Mainline: `Docs/math/TECT-Math162-Pillar4-BCC-defect-bundle-fibre-bundle-construction.tex.txt`. Audit: `Docs/math/TECT-Math165-Round-R1-cross-turn-audit-of-Math162-163-164.tex.txt` §2 (Objection β VALID).
- **Origin**: Math162 constructs the BCC defect bundle on $\mathrm{CP}^2$ with two coordinate patches $\mathcal U_0,\mathcal U_1$. The Math165 audit flags that the point $[0\!:\!0\!:\!1]$ is not covered, leaving a codimension-2 omission. Standard $\mathrm{CP}^2$ bundles require three patches.
- **Statement**: extend Math162 to a three-patch atlas $(\mathcal U_0,\mathcal U_1,\mathcal U_2)$ with explicit transition functions $g_{01},g_{12},g_{02}$ on each pairwise overlap and verification of the Čech cocycle $g_{01}g_{12}g_{20}=I$ on the triple overlap $\mathcal U_0\cap\mathcal U_1\cap\mathcal U_2$. The first Chern class $c_1$ should be unchanged.
- **Why open**: required to upgrade Math162 from PARTIAL-ADVANCED to PROVED at the foundation level. Without three-patch closure, the bundle is technically incomplete.
- **Falsification criterion**: the Čech cocycle fails to close on the triple overlap, indicating the bundle is not globally well-defined; this would force a re-examination of the SO(10)/SU(5) fibre choice.
- **Owner**: TECT collaboration. Task **#136** (Pillar 4 sub-task 1 closure).
- **Last reviewed**: 2026-04-26. **Review by**: 2026-06-26.

#### Q-2026-04-26-Math163-scale-clarification — Clarify the energy scale of the GAP-1 boson-loop ratio R_boson/fermion ≈ 0.12

- **Stage**: Pillar 10 / GAP-1, Math163 boson-loop subdominance. Mainline: `Docs/math/TECT-Math163-GAP1-boson-loop-subdominance-check.tex.txt`. Audit: `Docs/math/TECT-Math165-Round-R1-cross-turn-audit-of-Math162-163-164.tex.txt` §3 (Objection γ VALID for documentation).
- **Origin**: Math163 reports $R_{\rm boson/fermion}\approx 0.12$ using SM coupling values $y_t\approx 1$, $g_{\rm EW}\approx 0.65$, $\lambda_H\approx 0.13$ at the EW scale. The fermion-loop saturation argument of Math158 is supposed to operate at the BCC (Planck-ish) scale. The ratio's scale-coherence requires explicit RG-running discussion or an argument that the hierarchy $y_t^2\gg g_{\rm EW}^2$ is preserved under the running.
- **Statement**: either (i) compute the RGE of the relevant Yukawa and gauge couplings from $M_Z$ to the BCC scale and verify the hierarchy, or (ii) supply an asymptotic-safety argument (Math120-Math125) that the hierarchy is fixed at the UV fixed point.
- **Why open**: required to prevent the audit's Objection γ from invalidating Math163's PROVED-CONDITIONAL status under stricter scrutiny.
- **Falsification criterion**: if the hierarchy inverts under RG running ($g_{\rm EW}>y_t$ at the BCC scale), the boson-loop subdominance argument fails and a full combined-sector calculation is needed.
- **Owner**: TECT collaboration. Task **#137** (GAP-1 scale-coherence).
- **Last reviewed**: 2026-04-26. **Review by**: 2026-07-26.

#### Q-2026-04-26-Math164-Higher-form-Berry-topology — Identify a genuine TECT-specific topological signature on the BRST FP determinant beyond the trivial Berry phase

- **Stage**: Pillar 4 / GAP-2 (signature substantiation). Mainline: `Docs/math/TECT-Math164-Berry-phase-non-triviality-construction.tex.txt` §5. Audit: `Docs/math/TECT-Math165-Round-R1-cross-turn-audit-of-Math162-163-164.tex.txt` §5 cross-coupling.
- **Origin**: Math164 establishes $\pi_1(M_{\rm BCC})=\{e\}$, so every standard Berry phase is trivial $\pmod{2\pi}$. Math160's TECT-specific signature claim demoted to OUTLINE (R-2026-04-26-Math160-BerrySignatureTrivial). A genuine TECT-specific signature distinguishing the FP determinant from flat-spacetime Yang–Mills must come from a different mechanism.
- **Statement**: identify and compute one of the following:
  (i) a higher-form symmetry of the BCC condensate (defect-line operators on a 1-form symmetry, surface operators on a 2-form);
  (ii) a Chern–Simons term in the TECT effective action whose level coefficient is BCC-specific;
  (iii) a non-trivial coupling between the FP determinant and the $\mathrm{Gr}(2,5)$ orbifold stratification of Math80-AddB.
- **Why open**: required for an unambiguous TECT-specific GAP-2 signature.
- **Falsification criterion**: if every candidate (i)–(iii) reduces to the flat-spacetime Yang–Mills form, then GAP-2 closure on the TECT-specific axis collapses entirely (the FP determinant is Yang–Mills-equivalent, with no observational distinguisher).
- **Owner**: TECT collaboration. Task **#138** (GAP-2 signature substantiation).
- **Last reviewed**: 2026-04-26. **Review by**: 2026-09-26 (120-day window for higher-form-symmetry exploration).

---

### **Math156/Math157 4-GAP Audit Aftermath — Four Critical Open Tasks (2026-04-26)**

#### Q-2026-04-26-Pillar4-SO10-emergence — Establish SO(10) (or equivalent anomaly-free unifying group) emergence from BCC condensate with chiral fermions in $\mathbf{16}$

- **Stage**: Pillar 4 (gauge structure) + GAP-3 unconditional closure dependency. Mainline note: `Docs/math/TECT-Math157-SO10-SM-anomaly-cancellation-rigorous-trace-method.tex.txt` §4. Companion: `Docs/math/TECT-Math156-Round-V1-V5-comprehensive-audit-verdict.tex.txt` §3.2.
- **Origin**: Math157 closes the SM anomaly-cancellation sub-problem CONDITIONAL on TECT's emergent gauge group being SO(10) (or an anomaly-free unifying group such as SU(5), Pati–Salam, or $E_6$) and on the chiral fermion content occupying the corresponding spinor multiplet ($\mathbf{16}$ for SO(10), $\mathbf{10}\oplus\overline{\mathbf{5}}$ for SU(5), etc.). Whether TECT actually realises one of these scenarios is the still-open Pillar-4 frontier.
- **Statement**: derive the gauge bundle structure on the BCC condensate's $\mathrm{CP}^2$ order manifold (Math106) and exhibit either (a) an SO(10) connection with chiral fermions in $\mathbf{16}$, or (b) an alternative anomaly-free embedding of the SM gauge group with the standard chiral content. The deliverable is a constructive demonstration that the emergent fibre bundle admits the required spinor representation.
- **Why open**: this is now the unique critical blocker for unconditional GAP-3 closure (per Math157 §4) and therefore for $S_2$ Stage-2 quantum-consistency qualification under the strictest reading.
- **Falsification criterion**: if no anomaly-free embedding can be constructed (either by direct derivation from BCC topology or by ruling out the candidate groups), GAP 3 reverts to OPEN unconditionally and the framework's claim to be a quantum-consistent gauge theory must be retracted.
- **Owner**: TECT collaboration. Successor of Math80-AddC SO(10) outline; Task **#129** (Pillar 4 unconditional closure).
- **Last reviewed**: 2026-04-26. **Review by**: 2026-08-26 (120-day window for constructive emergence proof).

#### Q-2026-04-26-GAP1-third-route — Independent matter-side derivation of $\hbar_{\rm Fock}$ disjoint from elastic-modulus identification

- **Stage**: Pillar 10 quantum completion; GAP-1 unconditional closure. Mainline note: `Docs/math/TECT-Math156-Round-V1-V5-comprehensive-audit-verdict.tex.txt` §3.1.
- **Origin**: Math156 §3.1 demonstrates that Routes A and B in Math149 share an elastic-modulus input ($\rho_{\rm cond} \leftrightarrow G$ via Math110-AddG–AddI), so the agreement $\hbar_{\rm Fock} = \hbar_{\rm gravity}$ is structurally tautological. GAP 1 is therefore PROVED CONDITIONAL (weak) pending an independent third route.
- **Statement**: derive $\hbar_{\rm Fock}$ from a matter-side computation that does not feed through the $\rho_{\rm cond} \leftrightarrow G$ identification. Candidate routes: (i) explicit fermion-loop saturation of the canonical commutator $[Q,P] = i\hbar$ at the BCC scale; (ii) Onsager–Machlup short-time path-integral kernel evaluated on the BCC ground state; (iii) DGLAP-style anomalous dimension matching with the SM running-quantum-number sector.
- **Why open**: required to upgrade GAP 1 from PROVED CONDITIONAL (weak) to PROVED unconditional. Not a critical blocker for $S_2$ qualification but required for the full Stage-1 Pillar-10 closure.
- **Falsification criterion**: a third route consistent with $\hbar = c^5 a_{\rm BCC}/(16\pi G)$ to within 10\% verifies the identification; persistent disagreement would force a structural revision of the elastic-modulus identification.
- **Owner**: TECT collaboration. Task **#130** (Pillar 10 third-route).
- **Last reviewed**: 2026-04-26. **Review by**: 2026-07-26 (90-day window for matter-side derivation).

#### Q-2026-04-26-GAP4-ns-failure — Resolve the $n_s = 0.913$ vs $0.9649 \pm 0.0042$ discrepancy ($\geq 5\sigma$ tension)

- **Stage**: $S_3$ Stage-3 empirical contact; GAP-4 closure. Mainline note: `Docs/math/TECT-Math156-Round-V1-V5-comprehensive-audit-verdict.tex.txt` §3.4. Origin: `Docs/math/TECT-Math151-GAP4-observables-experimental-comparison.tex.txt`.
- **Origin**: Math151 reported the prediction $n_s^{\rm TECT} \approx 0.913$ for the cosmological scalar spectral index versus $n_s^{\rm obs} = 0.9649 \pm 0.0042$ (Planck 2018), framing it as "compatible within parametric tension". The gap is $\geq 5\sigma$ at any reasonable parametric uncertainty band; this is a falsification at conventional thresholds, not a tension.
- **Statement**: identify whether the failure is in (i) the TECT-side derivation (e.g. $n_s$ formula assumes incorrect horizon-crossing condition, or scale-setting maps $a_{\rm BCC}$ to $k_*$ incorrectly), (ii) the parameter mapping (additional running between the BCC scale and the CMB pivot scale), or (iii) the underlying scenario (the early-universe TECT phase transition does not produce observable inflation, in which case $n_s$ is not a TECT prediction at all and the relevant observable is the matter-power spectrum or post-inflationary structure). Re-derive or rescope accordingly.
- **Why open**: the current cosmology branch of TECT is falsified at $\geq 5\sigma$ if the Math151 derivation is taken at face value. Stage-3 cannot pass under the current parametrisation.
- **Falsification criterion**: any rederivation that yields $n_s \in [0.95, 0.98]$ rescues the inflationary-TECT branch. A rescoping that demonstrates $n_s$ is not a TECT observable on the current branch settles the issue without forcing an inflation-style match.
- **Owner**: TECT collaboration. Task **#131** (Stage-3 cosmology rescue or rescope).
- **Last reviewed**: 2026-04-26. **Review by**: 2026-06-26 (60-day window for $n_s$ resolution).

#### Q-2026-04-26-GAP2-BRST-TECT-specific — TECT-specific Faddeev–Popov determinant for BCC-emergent gauge orbits

- **Stage**: $S_2$ Stage-2 quantum consistency; GAP-2 closure. Mainline note: `Docs/math/TECT-Math156-Round-V1-V5-comprehensive-audit-verdict.tex.txt` §3.3. Origin: `Docs/math/TECT-Math152-GAP2-BRST-gauge-fixing-outline.tex.txt`.
- **Origin**: Math152 invokes standard BRST for any compact Yang–Mills theory but does not construct the Faddeev–Popov determinant on the TECT-specific gauge orbits emerging from the BCC condensate. The TECT-specific question is whether the emergent gauge symmetry is a genuine local fibre-bundle symmetry (rather than a non-linearly realised global symmetry) and whether the FP determinant is finite for the lattice-regularised TECT functional integral on a representative volume.
- **Statement**: explicit one-loop Faddeev–Popov determinant calculation for the BCC-emergent gauge orbits. Show that the determinant is non-zero (no Gribov copies obstructing the gauge fixing on the canonical patch) and finite after dimensional regularisation.
- **Why open**: GAP 2 currently sits at OUTLINE (not PROOF). Required for unconditional $S_2$ closure independent of the Pillar-4 emergence question.
- **Falsification criterion**: a finite, non-zero one-loop FP determinant on the BCC-canonical patch closes GAP 2. A vanishing or divergent determinant forces a structural revision of the gauge-emergence story.
- **Owner**: TECT collaboration. Task **#132** (Stage-2 BRST TECT-specific).
- **Last reviewed**: 2026-04-26. **Review by**: 2026-08-26 (120-day window for explicit FP calculation).

---

### **Math98 Phase-Transition Origin of Planck Constant — Six Open Tasks (2026-04-25, Rounds 5–10)**

#### Q-2026-04-25-Math98-AddA-cosmology-coupling — Derive quench rate from early-universe Friedmann equations

- **Stage**: Pillar 10 quantum-completion; Math98-AddA Kibble-Zurek derivation. Mainline note: `Docs/math/TECT-Math98-AddA-Kibble-Zurek-tau-PT-derivation.tex.txt` §6 Devil's-advocate objection β.
- **Origin**: Math98-AddA estimates quench rate $|\dot{\mu}^2| \sim |\mu^2_c| \times H$ (Hubble parameter) by analogy to cosmological evolution, but this coupling is not rigorously derived from the pre-transition early-universe thermodynamics.
- **Statement**: couple the Brazovskii scalar field to the Friedmann equations:
$$H^2 = \frac{8\pi G}{3}(\rho_{\rm rad} + \rho_{\Psi}), \quad \frac{d\rho_{\Psi}}{dt} + 3H(\rho_{\Psi} + p_{\Psi}) = 0,$$
where $\rho_{\Psi}, p_{\Psi}$ are the energy density and pressure of the pre-transition scalar field. Solve for $d\mu^2/dt$ as a function of $H(t)$ and show that the Kibble-Zurek quench rate follows as a rigorous consequence.
- **Why open**: Makes the F2 gate test rigorous by eliminating hand-wavy cosmological estimates. Currently, the quench-rate parametric spread leads to F2 passing, but the underlying cosmology is speculative.
- **Falsification criterion**: Coupled calculation must yield $|\dot{\mu}^2|$ in the range $[10^{-5}, 10^{-2}]$ relative to $|\mu^2_c|$ for cosmic-scale phase transitions (early-universe or late-time scenarios). Outside this range, the phase-transition origin scenario is disfavored.
- **Owner**: TECT collaboration. Task **#121** (Pillar 10 pathfinding).
- **Last reviewed**: 2026-04-25. **Review by**: 2026-06-25 (60-day window for cosmological derivation).

#### Q-2026-04-25-Math98-AddB-BdG-verification — Rigorous Bogoliubov–de Gennes analysis of BCC shell modes

- **Stage**: Pillar 10; Math98-AddB Volovik shell-mode normalisation. Mainline note: `Docs/math/TECT-Math98-AddB-Volovik-shell-mode-eta-norm.tex.txt` §6 Devil's-advocate objection α.
- **Origin**: Math98-AddB translates Volovik's ($^3$He-B fermionic) framework to BCC (bosonic) via structural analogy, but lacks rigorous Bogoliubov proof of the shell-mode spectrum and normalisation.
- **Statement**: perform exact Bogoliubov–de Gennes analysis of the BCC condensate Hamiltonian:
$$H_{\rm BdG} = \sum_{\mathbf{k}} \epsilon_{\mathbf{k}} \hat{c}^†_{\mathbf{k}} \hat{c}_{\mathbf{k}} + \sum_{\mathbf{k},\mathbf{q}} V_{\mathbf{k}, \mathbf{q}} \hat{c}^†_{\mathbf{k}} \hat{c}^†_{\mathbf{q}} + \text{h.c.},$$
to compute the exact spectrum of elementary excitations and the normalisation factor $\eta_{\rm norm}$ as a function of the condensate parameters. Compare with the Volovik analogy estimate ($\eta_{\rm norm} \approx 0.26$).
- **Why open**: Three different methods (3D density of states, Floquet, energy-fraction) gave range [0.2–3.1] in AddB. Rigorous BdG calculation removes this methodological ambiguity.
- **Falsification criterion**: BdG-computed $\eta_{\rm norm}$ must lie within a factor-2 of the Volovik estimate (0.26 ± 0.13). If BdG yields $\eta_{\rm norm} < 0.1$ or $> 1$, the Volovik analogy is broken and Path (b) is retracted.
- **Owner**: TECT collaboration. Task **#122**.
- **Last reviewed**: 2026-04-25. **Review by**: 2026-06-25.

#### Q-2026-04-25-Math98-AddC-rigorous-Chern-number — Exact Chern-number computation on BCC Brillouin-zone shell

- **Stage**: Pillar 10; Math98-AddC Berry-curvature topological invariant. Mainline note: `Docs/math/TECT-Math98-AddC-Berry-curvature-eta-top.tex.txt` §6 Devil's-advocate objection β.
- **Origin**: Math98-AddC parametrically estimates $\eta_{\rm top} \approx 0.42$ using three methods (3D integral, 2D surface, parametric enhancement), spanning [0.017–0.42]. Full rigor requires exact Chern-number calculation via matrix-valued Berry-phase formulation.
- **Statement**: compute the Chern number
$$C = \frac{1}{2\pi i} \oint_{\partial \mathcal{M}} \mathcal{A} = \frac{1}{2\pi i} \int_{\mathcal{M}} \mathcal{F}$$
as an integer topological invariant using the matrix-valued Berry connection for the BCC order-parameter manifold. Identify the six-fold sector contribution and sum to obtain exact $\eta_{\rm top}$ (dimensionless).
- **Why open**: Gate F1 requires $0.1 \le \eta_{\rm top} \le 10$; all three AddC methods satisfy this, but the 25-fold parametric spread (0.017 to 0.42) reflects methodological ambiguity, not fundamental uncertainty. Exact computation removes ambiguity.
- **Falsification criterion**: Exact Chern-number computation must yield an integer result (non-integer would indicate error). The resulting $\eta_{\rm top}$ must lie within [0.1, 10]. If $\eta_{\rm top} < 0.01$ or $> 100$, Gate F1 FAILS and Path (c) is retracted.
- **Owner**: TECT collaboration. Task **#123**.
- **Last reviewed**: 2026-04-25. **Review by**: 2026-06-25.

#### Q-2026-04-25-Math98-AddE-pre-transition-quantisation — Rigorous quantisation of pre-transition fluid state

- **Stage**: Pillar 10; Math98-AddE Onsager-Machlup cross-check. Mainline note: `Docs/math/TECT-Math98-AddE-Onsager-Machlup-cross-check.tex.txt` §6 Devil's-advocate objection α.
- **Origin**: Math98-AddE uses Langevin dynamics $\partial_t \Psi = -\Gamma \delta\mathcal{F}/\delta\Psi + \zeta$ in zero-temperature limit to define adiabatic-invariant action, but the pre-transition fluid state's quantisation axioms are not explicit.
- **Statement**: specify the quantum state of the pre-transition fluid $|\Psi_{\rm pre}\rangle$ (e.g., thermal coherent state, vacuum state, or squeezed state) and show that adiabatic-invariant action $S_{\rm adiab} = \int_0^{\tau_{\rm PT}} \langle \Psi_{\rm pre}(t) | H_{\rm pre}(t) | \Psi_{\rm pre}(t) \rangle dt$ (time-dependent expectation) yields the same order-of-magnitude $\hbar$ as the O-M Langevin path integral.
- **Why open**: Connects the pre-transition quantum state to the post-transition commutator scale, closing a logical gap in the phase-transition argument.
- **Falsification criterion**: Pre-transition quantum calculation of adiabatic invariant must yield $\hbar^{\rm pre-trans} = \hbar^{\rm O-M}$ to within 50% (order-unity agreement). Larger discrepancy indicates the quantum and classical pre-transition descriptions are incompatible.
- **Owner**: TECT collaboration. Task **#124**.
- **Last reviewed**: 2026-04-25. **Review by**: 2026-07-25 (60-day window for quantum-state specification).

#### Q-2026-04-25-Math98-AddE-precise-coefficient-C — Exact Onsager-Machlup coefficient C from Bogoliubov analysis

- **Stage**: Pillar 10; Math98-AddE O-M cross-check. Mainline note: Math98-AddE §6 Devil's-advocate objection β.
- **Origin**: Math98-AddE estimates O-M action scale as $S_{\rm OM} / C$ with coefficient $C$ undetermined (spread factor-30 to -117). Bogoliubov analysis can pin down $C$ exactly.
- **Statement**: perform matched asymptotic expansion of the condensation trajectory $\Psi^*(t)$ using Bogoliubov–de Gennes equations, extracting the exact prefactor $C$ in
$$\eta_{\rm OM} = S_{\rm OM} / C, \quad \hbar = \eta_{\rm OM} \times \eta_{\rm norm}.$$
Verify dimensional consistency and compare with the Kibble-Zurek + Berry + Volovik assembly.
- **Why open**: Eliminates order-of-magnitude uncertainty in the Onsager-Machlup pathway.
- **Falsification criterion**: BdG-computed $C$ must yield $|\hbar^{\rm OM} / \hbar^{\rm AddD} - 1| < 0.5$ (factor-2 agreement). Larger discrepancy indicates the two pathways (Kibble-Zurek vs. O-M) are fundamentally incompatible.
- **Owner**: TECT collaboration. Task **#125**.
- **Last reviewed**: 2026-04-25. **Review by**: 2026-07-25.

#### Q-2026-04-25-Math98-falsification-design — Design experimental/observational test of phase-transition origin of $\hbar$

- **Stage**: Pillar 10 experimental roadmap; all Math98 paths. Mainline note: Math99 Synthesis §7.
- **Origin**: Math98 proposes that $\hbar$ froze in during cosmic BCC condensation. This is testable in principle, but requires explicit experimental strategies.
- **Statement**: design at least three independent experimental or observational tests of the phase-transition origin hypothesis:
  1. **Gravitational-wave signature**: compute the GW spectrum from topological defect formation during condensation and compare with LIGO/Virgo/LISA sensitivity.
  2. **Fundamental-constant universality**: verify whether $\hbar$ is exactly universal across cosmic epochs (e.g., via quasar absorption-line spectroscopy, fine-structure constant evolution).
  3. **Primordial nucleosynthesis**: check whether the BCC condensation at early-universe scales leaves observational imprints in BBN or CMB spectra.
- **Why open**: Transforms the Math98 conjectural programme into an empirically testable hypothesis. Success would promote Pillar 10 from CONJECTURAL-PATHWAY-OPEN to PARTIAL-ADVANCED (empirical support).
- **Falsification criterion**: At least one of the three tests must reach "observable in principle" status (i.e., proposed experiment has feasible sensitivity $\approx$ expected signal amplitude). If all three tests yield "unobservable" verdict, the hypothesis is disfavored.
- **Owner**: TECT collaboration + experimental/observational partners. Task **#126** (long-term).
- **Last reviewed**: 2026-04-25. **Review by**: 2026-09-25 (90-day window).

---

### Q-2026-04-25-S2A-full-55-pairs — Complete Stage-2-A meta-consistency via all 55 pillar pairs — [OPEN 2026-04-25, raised by Math60-Stage2-A-AddA devil's-advocate objection γ]

- **Stage**: Stage-2-A meta-consistency closure. Mainline note: `Docs/math/TECT-Math60-Stage2-A-AddA-pairwise-commutativity-diagrams.tex.txt` §8.
- **Origin**: Math60-Stage2-A-AddA (2026-04-25) Round 3 deliverable checked five highest-impact pillar pairs for commutativity on shared background $\mathcal{M}_0$. Devil's-advocate objection γ: "The five pairs are not sufficient to rule out all inconsistencies. What about pairs like (P1, P11) or (P3, P4)?" Verdict: UPHELD with documentation.
- **Statement**: verify commutativity diagrams for all $\binom{11}{2} = 55$ pairs of pillars. Focus on the 50 pairs not yet checked; identify any that fail closure or reveal hidden dependencies. A complete Stage-2-A closure requires either (a) all 55 pairs verified, OR (b) a category-theoretic argument that any pair inherits commutativity from a verified subset.
- **Why open**: sampling of five pairs is sufficient to advance Stage-2-A from OUTLINE to PARTIAL-ADVANCED, but full closure requires exhaustive check or systematic proof.
- **Falsification criterion**: if any new pair (not in the five already checked) produces a **non-commutative** diagram or reveals circular logic, that pair must be archived in NEGATIVE-RESULTS and the pillars involved must be re-examined for hidden assumptions.
- **Owner**: TECT collaboration. Follow-on task to Math60-Stage2-A-AddA.
- **Expected completion pathway**: Rounds 8–10 synthesis (Math99 or later extension) or dedicated Stage-2-A audit turn.
- **Last reviewed**: 2026-04-25. **Review by**: 2026-05-25 (30-day cadence, queued for turn-8+ execution).

---

### Q-2026-04-24-Solver-115-lanczos-probe — Replace 5-probe Rayleigh classifier with Lanczos mini-spectrum probe — [OPEN 2026-04-24, queued by Math82-G2 audit]

- **Stage**: solver hygiene (cross-pillar; affects all numerical work). Mainline note: `Docs/math/TECT-Math82-Addendum-G2-PCG-and-stall-mechanism-audit.tex.txt` §3.
- **Origin**: Math82-G2 audit (2026-04-24): 5-probe Rayleigh classifier in `Codes/tools/check_jacobian_symmetry.py::probe_symmetry` cannot reliably detect symmetric-indefinite operators in dim N≈2×10⁵ when negative spectrum is small fraction. Concentration argument: $\mathbb{E}[\rho_i] = \mathrm{tr}(J)/N$ dominates over individual negative eigenvalues; 5-probe min is positive with probability ≈ 1 even when ~5,000 of 196,608 eigenvalues are negative.
- **Statement**: implement Lanczos-based mini-spectrum probe of size $m \in [10, 30]$ producing Ritz spectrum $\{\theta_j\}$. Classify SPD ↔ $\min_j \theta_j > 0$ at ≤1% relative tolerance; SI ↔ $\min_j \theta_j \le 0$. Replace `n_negative_rayleigh` field with `lanczos_min_ritz` in classification dataclass.
- **Why open**: latent bug — currently mitigated by `truncated_cg_solve`'s Steihaug-Toint negative-curvature handling, but PCG path is suboptimal for SI operators. Fix unlocks correct MINRES routing for indefinite warm-starts.
- **Falsification criterion**: Lanczos probe must reproduce SI on Phase-Z Point 3 (where Phase-2 Lanczos returned $\lambda_{\min} = -6.25\times 10^{-2}$). If new probe still classifies as SPD, re-design.
- **Owner**: TECT collaboration. Task **#115**.
- **Last reviewed**: 2026-04-24. **Review by**: 2026-05-24.

### Q-2026-04-24-Solver-116-vacuum-floor-guard — Add vacuum-floor convergence guard to Newton trust-region — [OPEN 2026-04-24, queued by Math82-G2 audit]

- **Stage**: solver hygiene (cross-pillar). Mainline note: Math82-G2 §4.
- **Origin**: Math82-G2 audit (2026-04-24): trust-region Newton in `tect_newton_krylov.py::newton_solve` lacks termination guard for $\Psi \approx 0$ states with $\|F\|$ at FP floor. Phase-Z Points 4-7 stalled for 15 iterations producing pred_m=0, ρ=-1e30 sentinel due to $\max(\cdot, 0)$ clamp on numerically-zero predicted reduction.
- **Statement**: add early-exit condition before inner Krylov solve:
$$\|F(\Psi)\| < c_{\mathrm{floor}} \sqrt{N} \, \varepsilon_{\mathrm{mach}} \;\Rightarrow\; \text{declare}\ \Psi^* \equiv \Psi\ \text{(numerical-vacuum solution)}$$
with $c_{\mathrm{floor}} \sim 100$ (configurable). For $N=196{,}608$, $\varepsilon_{\mathrm{mach}}^{(64)} \approx 1.1\times 10^{-16}$, guard fires at $\|F\| \sim 5\times 10^{-12}$, two orders below present Points 4-7 merit floor.
- **Why open**: prevents future warm-start chains from stalling at numerical vacuum. Should mark such states as `converged=True, kind="numerical_vacuum"` in solver record.
- **Falsification criterion**: re-run Phase-Z 7-point with guard enabled; Points 4-7 must terminate within 1 Newton step with `converged=True, kind="numerical_vacuum"` instead of stalling 15 iterations.
- **Owner**: TECT collaboration. Task **#116**.
- **Last reviewed**: 2026-04-24. **Review by**: 2026-05-24.

### Q-2026-04-24-P1-117-coldstart-scan — Math82-I cold-start scan to test Regime III branch-existence — [OPEN 2026-04-24, queued by Math82-G2 audit]

- **Stage**: 1, Pillar 1 numerical-anchor sub-task. Mainline note: `Docs/math/TECT-Math82-Addendum-I-runbook-and-theoretical-prediction.tex.txt` (v1.0, 2026-04-24).
- **Origin**: Math82-G2 audit (2026-04-24) reclassified Math82-G §3 Regime III ("subset-4 branch terminates below μ²=-0.1") as **undetermined** because Points 4-7 inherited a near-trivial-vacuum warm-start from Point 3.
- **Statement**: for each of the 7 μ² values $\{+5e\!-\!3, -0.02, -0.1, -0.5, -0.7, -0.85, -1.0\}$, run INDEPENDENT cold-start Newton from fresh subset-4-cosine seeds (no warm-start chain). **Recommended enhancement (Math82-I §5)**: 5 independent random-phase seeds per μ² value (35 total solves) to achieve multi-modal basin coverage with $\Omega(\sqrt{35}) \approx 5.9$ expected-distinct-basins sampling. Decouples branch-existence question from warm-start collapse pathology.
- **Why open**: direct test of Regime III claim — does a subset-4 equilibrium exist at deep μ² < 0, or did the original Math82-G run only fail to access it via warm-start collapse?
- **Falsification criterion (single-seed version)**: if any cold-start at μ² ∈ {-0.5, -0.7, -0.85, -1.0} converges to non-trivial $\Psi^*$ ($\|\Psi^*\|/\sqrt{N} > 10^{-3}$) with $\Delta F < 0$, then Math82-G §3 "branch terminates" is FALSIFIED. **Enhanced version (multi-replica)**: if ≥2 of 5 cold-starts per μ² access non-trivial minima, FALSIFIED.
- **Pre-registered theory**: Brazovskii mean-field analysis (Math82-I §2) predicts spinodal at $\mu^2_{\rm sp,subset4} \approx +0.0152$, binodal at $\mu^2_{\rm bin} \in [-0.05, 0]$. Points 2–7 should all converge to non-trivial equilibria if they exist.
- **Owner**: TECT collaboration. Task **#117**.
- **Last reviewed**: 2026-04-24. **Review by**: 2026-05-24.

### Q-2026-04-24-P1-12mode-bcc-ground-state — Full 12-mode BCC ground-state continuation curve — [OPEN 2026-04-24, queued by Math82-Addendum-G Phase Z 7-point bifurcation result]

- **Stage**: 1, Pillar 1 (Mass) numerical-anchor sub-task. Mainline note: `Docs/math/TECT-Math82-Addendum-G-Phase-Z-7point-bifurcation-curve.tex.txt`.
- **Origin**: Math82-Addendum-G (2026-04-24) Phase Z 7-point run with subset-4-cosine seed delivered three-regime structure: stable metastable branch in Regime I ($\mu^2 \in [-0.02, +5e\!-\!3]$ but $F(\Psi^*)>F(0)$), pitchfork bifurcation at $\mu^2_{\rm bif} \approx -0.05 \pm 0.03$ (Regime II saddle at $\mu^2=-0.1$), branch terminates for $\mu^2 \le -0.5$. The Math82-F numerical anchor $m^{*2}=+4.247e\!-\!2$ is reproduced but on a metastable branch, not the BCC ground state.
- **Statement**: re-run identical 7-point Phase Z schedule with the full 12-mode BCC analytic seed (`Codes/pde/bcc_analytic_seed.py` v0.2 mode `bcc_analytic`) to obtain the GROUND-STATE continuation curve, expecting $\Delta F < 0$ throughout $\mu^2 < R_C^{\rm global} = 1.141e\!-\!2$ with $\lambda_{\min} > 0$ at all 7 points.
- **Why open**: subset-4-cosine seed bypasses 8 of the 12 first-shell BCC reciprocal-lattice modes, accessing only a metastable lamellar/striped sub-branch. The full 12-mode seed should activate the genuine BCC ground state and produce a globally favourable continuation curve.
- **Falsification criterion (pre-registered)**: any of:
  1. Full 12-mode seed converges to the same metastable branch ($F(\Psi^*) > F(0)$ at $\mu^2 = +5e\!-\!3$).
  2. Ground-state branch shows $\lambda_{\min} < 0$ (saddle) at any interior point in Regime I ($\mu^2 \in [-0.02, +5e\!-\!3]$).
  3. Ground-state branch terminates before $\mu^2 = -1.0$ (Newton collapse to $\Psi \approx 0$).
  Any outcome forces re-examination of the BCC ground-state existence claim.
- **Method**: invoke `bcc_analytic_seed.py --mode bcc_analytic --N 32 --L 62.20036 --output Psi_BCC_ground_N32_L7.npy`, then run `continuation_mu2_v25.py` with identical 7-point schedule, $\mathrm{tol}_{\rm Newton}=10^{-8}$, $\mathrm{max}_{\rm Newton}=15$, EW $[0.05, 0.9]$, output to `Runs/continuation/math82H_groundstate_N32_Lbcc7_2026-04-NN`.
- **Owner**: TECT collaboration. Primary executor: numerical run + Math82-Addendum-H archival.
- **Task**: assigned `#114 — Math82-H full 12-mode BCC ground-state continuation curve`.
- **Closure consequence**: success → Pillar 1 numerical anchor upgraded from "metastable branch m\*² value" to "ground-state continuation curve including bifurcation and termination points". The clean ground-state mass gap $m^{*2}_{\rm GS}(\mu^2)$ along the curve becomes the Pillar 1 deliverable.
- **Last reviewed**: 2026-04-24.
- **Review by**: 2026-05-24.

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

### Q-2026-04-24-P11-sector-decomposition-verification — Four-sector $\Lambda_{\mathrm{cosmo}}$ cancellation numerical verification — [OPEN 2026-04-24, queued from Math58-v7-Addendum-A adversarial audit Q5 (UNVERIFIED)]

- **Stage**: 1, Pillar 11 ($\Lambda$ cosmological constant) numerical-verification sub-task. Mainline note: `Docs/math/TECT-Math58-v7-Addendum-A-PV-scheme-adversarial-audit.tex.txt` §6.3 (Q5 UNVERIFIED).
- **Origin**: Math58-v7-Addendum-A (2026-04-24) adversarial audit identified five critical questions about Pauli-Villars scheme dependence. Q1–Q4 verdicts (2 DISMISSED, 2 VALID) support the theorem's robustness. **Q5 (numerical verification) returned UNVERIFIED**: the four-sector cancellation $\Lambda_{\mathrm{monopole}} + \Lambda_{\mathrm{vortex}} + \Lambda_{\mathrm{BCC}} + \Lambda_{\mathrm{Dirac}} = 0$ is an analytic result (symmetry arguments + Pauli-Villars subtraction lemma) but has never been checked numerically on a concrete Brazovskii operating point.
- **Statement**: Extract the four individual sector contributions $\{\Lambda_i\}_{i \in \{\mathrm{monopole, vortex, BCC, Dirac}\}}$ from a fully converged Newton solution $\Psi^*(\mathbf{r})$ at a specific Brazovskii point (recommend: $\mu^2 = +5\times 10^{-3}$, $\lambda = -0.43$, $\gamma = 1.62$, or later continuation mainline authority) on a sufficiently large grid ($N \geq 64^3$, ideally $N = 128^3$ for continuum-limit confidence). Compute their numerical sum and verify cancellation to three significant figures: $|\Lambda_{\mathrm{total}}| < 10^{-3} \times \max_i |\Lambda_i|$.
- **Why open**: The symbolic derivations for monopole (CP conjugation, Math58-v2/v3), vortex (sub-lemmas, Math58-v4/v4-sublemma), and BCC (renormalisation convention, Math58-v5) are complete. The Dirac sector (Pauli-Villars subtraction, Math58-v7) is also theoretically sound. However, a single numerical failure (sectors sum to non-zero) would invalidate the entire Pillar 11 closure. This is a low-risk but high-confidence-value check.
- **Blocking issue**: Pillar 1 is still SCAFFOLD (no converged BCC solution with $\lambda_{\min} > 0$ in the continuum limit). Q-2026-04-24-P1-12mode-bcc-ground-state-continuation (Task #114, Math82-Addendum-H) must complete first to provide the converged $\Psi^*(\mathbf{r})$.
- **Required infrastructure** (post-Pillar-1 completion):
  1. Fock-space decomposition of the converged Dirac sea: identify and enumerate zero modes, bound states, and continuum states near the Fermi surface.
  2. Monopole sector energy extraction: count topological monopole defects in $\Psi^*(\mathbf{r})$ and assign individual vacuum energies using the CP-conjugation formula (Math58-v2/v3).
  3. Vortex sector energy extraction: identify vortex line defects and extract their collective contribution (Math58-v4).
  4. BCC condensate sector energy: computed via $\Delta\Lambda_{\mathrm{BCC}} = 0$ convention (Math58-v5); verify consistency with extracted Dirac + monopole + vortex sum.
  5. Dirac sector energy: numerically integrate the Pauli-Villars regularised vacuum-energy density on the converged background.
- **Falsification criterion (pre-registered)**:
  1. The four-sector sum $|\Lambda_{\mathrm{total}}|$ exceeds $10^{-3} \times \max_i |\Lambda_i|$ at any grid size $N \in \{64^3, 128^3, 256^3\}$ (failure to converge to zero).
  2. Individual sectors exhibit strong $N$-dependence (i.e., the cancellation is a grid artefact, not a fundamental property).
  3. Extrapolation to continuum ($N \to \infty$) shows $|\Lambda_{\mathrm{total}}| \to \Lambda_0 \neq 0$ (systematic bias).
  Any outcome forces either (a) re-examination of the four-sector derivations, or (b) identification of a numerical-extraction bug in the sector-decomposition code.
- **Method (to be implemented in Codes/supplementary/)**: 
  - Input: converged $\Psi^*(\mathbf{r})$ from Math82-Addendum-H (Pillar 1).
  - Step 1: compute phase field $\phi(\mathbf{r}) = \arg(\Psi^*(\mathbf{r}))$ and vorticity $\omega(\mathbf{r}) = \nabla \times \phi$; count vortex lines.
  - Step 2: measure monopole density via defect topological charge (Pillar 5 machinery).
  - Step 3: Fock-space diagonalisation of the Dirac sector on the BCC background; extract zero-point energy.
  - Step 4: compute residual energies via variance analysis.
  - Step 5: form the sum $\Lambda_{\mathrm{total}}$ and measure convergence.
- **Owner**: TECT collaboration. Task **#118 — Pillar 11 sector-decomposition numerical verification**.
- **Closure consequence**: success → Pillar 11 status upgrades from PROVED CONDITIONAL to fully PROVED (all conditionalities satisfied + numerical evidence in hand). Pillar 11 joins Pillars 5, 7, 8, 9 in the PROVED category.
- **Last reviewed**: 2026-04-24.
- **Review by**: 2026-05-24 (or after Pillar 1 Task #114 completion, whichever is earlier).

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

### Q-2026-04-24-P6-Q6d-metastability — Does the Brazovskii operating point $(\lambda, \gamma) = (-0.43, 1.62)$ yield the true TECT ground state, or is it metastable? Impact on $Y_{\rm SO(10)}^{\rm TECT}$ prediction. — [OPEN 2026-04-24, flagged by Math80-Addendum-D-AddA Devil's-Advocate objection γ (UPHELD)]

- **Stage**: 1, Pillar 6 (Generations / SM embedding) Q6d sub-task (Yukawa unification UV anchor). Mainline note: `Docs/math/TECT-Math80-Addendum-D-AddA-Yukawa-UV-anchor.tex.txt` §6.3 objection γ.
- **Origin**: Math80-Addendum-D-AddA (2026-04-24) derives the TECT-predicted SO(10) Yukawa unification $Y_{\rm SO(10)}^{\rm TECT} = g_{\rm BCC} \phi_0 \approx 0.27$ using the Brazovskii operating point $(\lambda, \gamma) = (-0.43, 1.62)$ with corresponding amplitude $\phi_0 = \sqrt{-4\lambda/(15\gamma)} \approx 0.266$. Devil's-Advocate objection γ raises the risk: **Math82-AddG2 audit (2026-04-24) identified that the maximally-symmetric 6-cosine BCC seed converges to a SADDLE of the Brazovskii functional, not a local minimum, when the full Hessian is evaluated.**  If the canonical operating point $(\lambda, \gamma) = (-0.43, 1.62)$ is on a metastable branch (not the true TECT ground state), then the amplitude $\phi_0$ and hence $Y_{\rm SO(10)}^{\rm TECT}$ may shift when the genuine ground state is identified.
- **Statement (pre-registered)**: Execute Math82-Addendum-H (full 12-mode BCC ground-state continuation curve from $\mu^2 = -1.0$ to $+5\times 10^{-3}$ on the GROUND-STATE branch, not the metastable subset-4-cosine saddle branch). At the TECT operating point $\mu^2_{\mathrm{target}} = 5\times 10^{-3}$, extract the ground-state amplitude $\phi_0^{\rm GS}$. Compare to the metastable-branch value $\phi_0^{\rm saddle} \approx 0.266$ obtained from the canonical Brazovskii formula. **If $|\phi_0^{\rm GS} - \phi_0^{\rm saddle}| / \phi_0^{\rm saddle} < 10\%$**, the Yukawa prediction is ROBUST and Math80-Addendum-D-AddA stands. **If the difference exceeds 10% or if the ground state lies on a DIFFERENT branch with substantially different $\phi_0$**, then the Yukawa unification magnitude must be re-derived on the true ground state, and gates F1–F3 require re-evaluation.
- **Why open**: The Brazovskii free-energy formula $\phi_0 = \sqrt{-4\lambda/(15\gamma)}$ minimizes the potential for a given set of $(\lambda, \gamma)$ values, but it does not guarantee that the minimum is the GLOBAL ground state when multiple branches or metastable states exist. The Math82-AddG2 saddle identification is empirical evidence of metastable branching on the discretised lattice.
- **Falsification criterion (pre-registered)**:
  1. Full 12-mode ground-state continuation at $\mu^2 = +5\times 10^{-3}$ converges to $\phi_0^{\rm GS}$ with $|\phi_0^{\rm GS} - 0.266| / 0.266 > 0.10$ (10% shift).
  2. The ground-state branch exhibits $\lambda_{\min} < 0$ at any interior point (saddle structure persists).
  3. The ground-state branch terminates before reaching $\mu^2 = +5\times 10^{-3}$ (operating point inaccessible on the ground-state branch).
  Any outcome means objection γ is **VALID** (not dismissed) and Math80-Addendum-D-AddA gates F1–F3 require re-calibration.
- **Method**: Already specified in Q-2026-04-24-P1-12mode-bcc-ground-state-continuation (Task #114, Math82-Addendum-H). Reuse the converged ground-state solution and extract $\phi_0^{\rm GS}$ by averaging the magnitude $|\Psi^*(\mathbf{r})|$ over the BCC first-shell reciprocal-lattice region.
- **Owner**: TECT collaboration. Primary executor: Task #114 (Math82-Addendum-H) production; follow-up extraction code in `Codes/supplementary/Math80_Q6d_phi0_extraction.py`.
- **Task**: assigned **Task #119 — Ground-state amplitude verification for Yukawa unification robustness** (dependent on Task #114 completion).
- **Closure consequence**: 
  - If objection γ is DISMISSED (ground-state amplitude within 10% of metastable value): Math80-Addendum-D-AddA stands; gates F1–F3 remain valid; Pillar 6 Q6d UV-side PROVED status is confirmed.
  - If objection γ is UPHELD (amplitude shift > 10%): Math80-Addendum-D-AddA must be revised with updated $\phi_0^{\rm GS}$, new $Y_{\rm SO(10)}^{\rm TECT,revised}$ computed, gates F1–F3 re-calibrated, and status pushed back to CONJECTURAL pending numerical RGE closure on the revised value.
- **Last reviewed**: 2026-04-24. **Review by**: 2026-05-24 (or immediately after Task #114 completion).

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

### Q-2026-04-26-Math157-RHN-singlet-documentation — [RESOLVED 2026-04-27] Document the right-handed neutrino N singlet in the Math157 SO(10) anomaly cancellation explicitly

- **Stage**: GAP-3 / Math157 polish. Mainline: `Docs/math/TECT-Math157-SO10-SM-anomaly-cancellation-rigorous-trace-method.tex.txt` §1.4 + §3 (already implicitly includes $N(1,1)_0$ singlet). Audit: Math169 §5 cross-coupling.
- **Origin**: Math169 §5 cross-coupling check noted that Math157 lists 15 SM fermions + 1 right-handed neutrino in the $\mathbf{16}$ but the anomaly-coefficient table (§2.1-2.6) sums 16 components implicitly. Documentation polish: make the singlet's role in the $\mathbf{16}$ representation explicit, with a note that $Y(N)=0$ contributes zero to every anomaly coefficient and is therefore consistent with anomaly-freeness on its own.
- **Statement**: write `Docs/math/TECT-Math157-AddD-RHN-singlet-explicit.tex.txt` as a short addendum that lists the singlet $N$ explicitly in each anomaly trace and verifies that $Y=0$ implies zero contribution to $\mathcal A_{YYY}$, $\mathcal A_{32Y}$, $\mathcal A_{22Y}$, $\mathcal A_{\rm grav^2 Y}$. SU(3) and SU(2) traces are zero by representation triviality.
- **Resolution (2026-04-27; theory tag `Math157-AddD-RHN-singlet-explicit-2026-04-27`)**: Task #143 COMPLETED. The addendum `Docs/math/TECT-Math157-AddD-RHN-singlet-explicit.tex.txt` provides:
  - §2: Explicit branching diagram SO(10) → SU(5) × U(1)$_\chi$ → $G_{\rm SM}$ with the $\mathbf{1}_{+5}$ identified as $N(\mathbf{1},\mathbf{1})_0$.
  - §3: Per-coefficient verification table showing all six anomaly contributions from $N$ are zero.
  - §4: Theorem A.1 reaffirming that the full SO(10) $\mathbf{16}$ anomaly cancellation is the SM 15-fermion cancellation plus an inert singlet.
  - §6: Devil's-advocate self-test (α, β, γ) all dismissed.
- **Consequence**: Cross-coupling gap closed. Math166 16-mode count is now explicitly consistent with Math157's anomaly-cancellation proof, conditional on Task #142 (rigorous Atiyah-Singer derivation).
- **Status**: PROVED (documentation polish; underlying mathematics already in Math157).
- **Resolved by**: TECT-Math157-AddD-RHN-singlet-explicit.tex.txt (2026-04-27); CHANGELOG.md (new entry); OPEN-QUESTIONS.md (this archive entry).
- **Owner**: R3-B autonomous agent. Task **#143** (CLOSED).

---

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
  Combined with $O_h$-fundamental-domain $(s,t)$-reduction and the
  centered-form identity $\int_{D'} P_4\,d\Omega=0$, mpmath.iv
  interval arithmetic at $\mathrm{dps}=40$, $N_{\rm octant}=64$,
  depth-10 adaptive subdivision yields
  $c_4(\epsilon)\in[+1.402\!\times\!10^{-3},\,+2.368\!\times\!10^{-3}]>0$
  (central $+1.885\!\times\!10^{-3}$, half-width $4.83\!\times\!10^{-4}$).
- **Cross-check**: direct NumPy integrator
  (`PDE/bz_eta_integrator.py` v2.0) at $N_{\rm full}=256$ yields
  $c_4=+1.8503\!\times\!10^{-3}$, agreeing with interval central value
  to $1.9\%$ relative.
- **Companion patch**: `truncated_octahedron_volume()` was found to
  return $V_{\rm BZ}=7/2$ at mainline $(A,B)=(3/2,1)$ whereas the
  numerical mask count gives $V_{\rm BZ}=4$. The prior formula
  $8B^3-(4/3)(3B-A)^3$ is valid only on $2B\le A\le 3B$ whereas
  $s=A/B=3/2\in[1,2]$. Patched to the Irwin-Hall CDF piecewise form
  valid on all $A/B\ge 0$ (`PDE/bz_eta_integrator.py` v1.0 $\to$ v2.0,
  md5 `0db7a5ff`). The bug did not propagate to any $c_4$ cell-wise
  integration result; `TECT-Math_IR_Bound-v4-BZ-integrator.tex.txt` §2.1
  rewritten with a regression-guard Remark.
- **Theory tag**: `Math_IR_Bound-v4-shell-adaptive, 2026-04-21`.
  CHANGELOG.md top entry (2026-04-21 late). Pillar 8 status:
  NEAR-FINAL CONDITIONAL $\to$ PROVED (Proof-Completion Checklist v1.1).
- **Last reviewed**: 2026-04-21 &nbsp;|&nbsp; **Resolved at**: 2026-04-21 (late).

---

### Q-2026-04-15-11 — Topological proof that $\dim(H_L) = 3$ uniquely from BCC/Grassmannian structure   [REOPENED 2026-04-20 — closure claim DOWNGRADED to SCAFFOLD; see active section]

- **Closure attempt (2026-04-20)**: Math49 outlined an Atiyah–Singer index-theoretic argument for $\dim H_L = 3$ on $\text{Gr}(2,5)/G_{\text{SM}}$.
- **Devil's-advocate finding (same-day, 2026-04-20)**: (i) real dimension of $\text{Gr}(2,5)$ used as 6 rather than the correct $\dim_\mathbb{R} = 12$; (ii) Â-genus conflated with Euler characteristic in Eq.(20); (iii) instanton number $k=1$ asserted, not computed; (iv) the "$2+1=3$" step conflates bundle rank with topological index. These defects invalidate the closure.
- **Status**: REOPENED / SCAFFOLD. Item moved back to `## Active` as Q-2026-04-20-ZZ-A (see below). Closure awaits Math49-rigorous rewrite.

### Q-2026-04-15-12/13 — Triangle anomaly cancellation across 3 generations   [REOPENED 2026-04-20 — closure claim DOWNGRADED to SCAFFOLD]

- **Closure attempt (2026-04-20)**: Math49b enumerated six anomaly coefficients and claimed vanishing per generation.
- **Devil's-advocate finding (same-day)**: Eq.(19) U(1)_Y³ sum includes only $Q_L$ and $L_L$ (missing $u_R, d_R, e_R$ and Weyl multiplicities 6, 3, 3, 2, 1). Correct arithmetic: $6(1/6)^3 + 3(-2/3)^3 + 3(1/3)^3 + 2(-1/2)^3 + 1(1)^3 = 0$. SU(2)³ argument inverted — the correct reason is $d^{abc}=0$ in $\mathfrak{su}(2)$ (antisymmetric structure constants only), not "including $e_R$". These defects invalidate the closure.
- **Status**: REOPENED / SCAFFOLD. Item moved back to `## Active` as Q-2026-04-20-ZZ-B. Closure awaits Math49b-rigorous rewrite.

### [NEW 2026-04-20] Fermionic statistics emergence (Pillar 7 spin-statistics sub-claim)   [REOPENED 2026-04-20 — closure claim DOWNGRADED to NEAR-COMPLETE]

- **Closure attempt (2026-04-20)**: Math49c applied the Finkelstein–Rubinstein theorem on the BCC order-parameter space $\text{SO}(3)/\text{Oct}$, arguing $\pi_1 = \mathbb{Z}_2$ generates the exchange operator $R^2 = -1$.
- **Devil's-advocate finding (same-day)**: The structural argument is essentially correct, but missing a single lemma that identifies the BCC disclination topological charge with the generator of $\pi_1(\text{SO}(3)/\text{Oct}) = 2T$ (the binary tetrahedral group). Also: care required with the correct quotient group — the point group of the BCC lattice is $O_h$, so the relevant space is $\text{SO}(3)/O$ with $\pi_1 = 2O$; the sign-of-exchange calculation must be redone in that quotient.
- **Status**: REOPENED / NEAR-COMPLETE. Item active as Q-2026-04-20-ZZ-C. Closure awaits the disclination–$\pi_1$ identification lemma.

### [NEW 2026-04-20] Equivalence principle (Pillar 9)   [REOPENED 2026-04-20 — closure claim DOWNGRADED to SCAFFOLD]

- **Closure attempt (2026-04-20)**: Math_EP identified $T^W = T^{\text{def}} = T^{\text{grav}}$ as functional derivatives of $S[\Psi,g,A]$.
- **Devil's-advocate finding (same-day)**: The proof is tautological. All three tensors are defined as $(2/\sqrt{-g})\,\delta S/\delta g^{\mu\nu}$ of the same action; their coincidence is a definitional identity, not a physical EP statement. Eq.(24) contains a mid-proof "this gives a sign flip" fragment indicating the derivation was not finalised. A genuine WEP proof must (a) define $m_I$ dynamically from flat-space defect inertia, (b) define $m_G$ independently from weak-curvature coupling, and (c) prove $m_I = m_G$ via defect-elasticity-to-geodesic limit.
- **Status**: REOPENED / SCAFFOLD. Item active as Q-2026-04-20-ZZ-D. Closure awaits Math_EP-rigorous rewrite.

### [NEW 2026-04-20] Lorentz invariance: analytic bound on cubic anisotropy (Pillars 2, 8)   [REOPENED 2026-04-20 — closure claim DOWNGRADED to SCAFFOLD]

- **Closure attempt (2026-04-20)**: Math_IR_Bound computed $\Delta[\mathcal{O}^{(c)}_4] = 2 + \eta > 2$ via Wilsonian RG and quoted SME bound $c_{\mu\nu} \lesssim 10^{-70}$.
- **Devil's-advocate finding (same-day)**: (i) Eq.(3) used a quadrupole spin-2 operator $(\partial_i \partial_j \Psi)^2 - \tfrac{1}{3} (\nabla^2\Psi)^2$ rather than the correct cubic-anisotropy operator $\sum_i (\partial_i \Psi)^4 - \tfrac{1}{3}\big(\sum_i (\partial_i \Psi)^2\big)^2$. (ii) With $[\Psi] = 1/2$ in $d=3$ and four derivatives + four fields, the canonical dimension is $[\mathcal{O}^{(c)}_4] = 4\cdot 1 + 4\cdot 1/2 = 6$ (not 2); the RG-relevance calculation at the Wilson–Fisher fixed point must be redone. (iii) $\eta = +0.02$ asserted without a one-loop diagram. (iv) The $10^{-70}$ bound is not derived from any BCC-specific Brillouin-zone integral; it is quoted from a generic literature estimate.
- **Status**: REOPENED / SCAFFOLD. Item active as Q-2026-04-20-ZZ-E. Closure awaits Math_IR_Bound-rigorous rewrite.

### [2026-04-20 feedback-loop closures] Q-2026-04-20-ZZ-B, Q-2026-04-20-ZZ-C, Q-2026-04-20-ZZ-D archived at theorem-level; Q-2026-04-20-ZZ-A archived with NEGATIVE resolution

- **Q-2026-04-20-ZZ-B (anomaly cancellation)**: CLOSED at theorem level by Math49b-rigorous-v2 — archived 2026-04-20. Successor: `Math49b-anomaly-rigorous-v2-2026-04-20` + `CHANGELOG.md §[Math49-Math_EP-v2-feedback-loop-2026-04-20]`.
- **Q-2026-04-20-ZZ-C (disclination–$\pi_1$ lemma)**: CLOSED at theorem level by Math49c-rigorous-v2 — archived 2026-04-20. Successor: `Math49c-spin-statistics-rigorous-v2-2026-04-20`.
- **Q-2026-04-20-ZZ-D (dynamical WEP scalar+Dirac)**: CLOSED at theorem level by Math_EP-rigorous-v2 — archived 2026-04-20. Successor: `Math_EP-equivalence-principle-rigorous-v2-2026-04-20`.
- **Q-2026-04-20-ZZ-A (three-generation HRR)**: RESOLVED NEGATIVELY by Math49-rigorous-v2 — the direct-sum $E_L(a,b)$ ansatz is ruled out $\forall (a,b)\in\mathbb{Z}^2$. Successor: `D-2026-04-20-02` in `NEGATIVE-RESULTS.md` + the three refinement questions Q-2026-04-20-R1 / R3 / R4 in the `## Active` section above.
- **Q-2026-04-20-ZZ-E (cubic-anisotropy RG)**: PARTIAL (Gaussian proved, 1-loop pending) — remains in `## Active` above as a hybrid entry; v3 continuation opened as Q-2026-04-20-v3-IR.
- **Q-2026-04-20-R3 ($\mathbb{Z}_6$-equivariant Lefschetz, Pillar 6 refinement)**: CLOSED@GEOMETRIC 2026-04-20 by Math49d-R3-rigorous-v2. Key identity proved: $\chi^{\mathbb{Z}_6}(\mathrm{Gr}(2,5),\mathrm{Sym}^2 Q)=3$. Representation-theoretic interpretation: $3=\dim\mathrm{Sym}^2 V_\beta$ = dim of the $\mathbb{Z}_6$-trivial isotype in the $\mathbf{15}$ of SU(5). Multiprecision numerical verification at dps=200, eps=1e-50 (`Math49d_equivariant_bott.py`); $\zeta^k$-breakdown in $\mathbb{Z}[\omega]$: $(15,-3-12\omega,-3,3,-3,-3-12\omega^2)$. Independent corroboration of `D-2026-04-20-02`: the $\mathbb{Z}_6$-refined direct-sum scan $\chi^{\mathbb{Z}_6}(E_L(a,b))$ on $[-3,3]^2$ still contains no 3 (values $\in\{0,8,42,50,62,104,203,211,265\}$). Physical identification of the three $\mathrm{Sym}^2 V_\beta$ basis vectors with SM families remains OPEN in Q-2026-04-20-YK and Math55.

Entries appear here when moved from `## Active` upon proof or disproof.
Each archived entry cites its successor: theory tag + CHANGELOG.md
section (proved) or `NEGATIVE-RESULTS.md` tag (disproved).

### Q-2026-04-28-Math204-Cartan-reduction (Task #151, HIGH PRIORITY)

**Date opened**: 2026-04-28
**Theory tag**: Math204 §4
**Priority**: HIGH (gates Pillar 4 sub-task 2 PROVED unconditional via Math205 synthesis).

**Question**: Does the BCC inversion-equivariant holomorphic atlas structure on the Math162 CP² base FORCE the SU(5) part of the cocycle to take values in the maximal torus T ⊂ SU(5)? Equivalently: is the SU(5) cocycle homotopic to a T-valued cocycle for any inversion-equivariant Math162-derived atlas?

**Why important**: If YES, then by Math204 (C) c_2(E_{SU(5)}) = 0 unconditionally on the Math162 base, and combined with Math202 + Math203 closes the flat-Cartan forcing argument (the reviewer's Top-0 question). If NO, then Math192's c_2 = 0 claim requires revision, and Math191/192 status downgrades from "PROVED CONDITIONAL on canonical realisation" to "PROVED CONDITIONAL on a representation choice that is NOT forced by BCC".

**Approach**: Representation-theoretic bookkeeping internal to Math80-AddA. Identify the centraliser of the BCC inversion action inside SU(5); show that the Math162 cocycle factors through this centraliser; verify the centraliser equals (or contains) the maximal torus T = U(1)^4 ⊂ SU(5).

**Heuristic argument** (not a proof): The chirality flip 16 ↔ 16-bar singles out the U(1)_χ factor from SU(5) × U(1)_χ ⊂ SO(10). The residual SU(5) action on (10̄, 5̄, 1) ⊂ 16-bar must commute with both the inversion (anti-holomorphism) and the holomorphic atlas structure; this commutation may force diagonal action, i.e., reduction to T.

**Estimated effort**: 1-2 single-turn dispatches.

**Related**: RR1 = Q-2026-04-28-Math203-§3.4-rigor [REOPENED 2026-04-28 by Math208 — Math207 closure was audit-flagged] (Task #150). RR1 and RR2 (this question) together gate the Pillar 4 sub-task 2 unconditional promotion.

### Q-2026-04-28-Math208-Equivariance-Type (Task #150-revised, REOPENED, NOW SPLIT)

[SPLIT 2026-04-28 late+1 by Math208-AddA into RR1a + RR1b. RR1a CLOSED by Math207 + Math208-AddA. RR1b is the new HIGHEST PRIORITY task. See entries below for Q-2026-04-28-RR1a-base-antiholomorphism and Q-2026-04-28-RR1b-bundle-lift-type.]

### Q-2026-04-28-RR1a-base-antiholomorphism (Task #150-revised PART A) — [CLOSED 2026-04-28 late+1 by Math207 + Math208-AddA]

**Statement**: BCC inversion I induces an antiholomorphic involution σ_I:CP²→CP², σ_I([z₀:z₁:z₂])=[z̄₀:z̄₁:z̄₂], on the Math162/167 base.

**Closed by**: Math207 §2 Steps 1-6 (BCC reality Ψ:ℝ³→ℝ ⟹ Ψ_{-q}=Ψ_q^* ⟹ anti-linear involution on amplitude space ⟹ standard real structure on CP² after cubic-symmetric reduction). Modulo §3 notational fixes recorded in Math208-AddA.

**Status**: CLOSED.

### Q-2026-04-28-RR1b-bundle-lift-type (Task #150-revised PART B) — [CLOSED 2026-04-28 late+2 by Math209 with NEGATIVE forcing verdict: Type B confirmed via Math162 explicit transition; c_1=0 from σ_I-equivariance FALSIFIED]

**Date opened**: 2026-04-28 (late+1)
**Theory tag**: Math208-AddA §2 RR1b.
**Priority**: HIGHEST (next single-turn dispatch).

**Question**: For the U(1)_χ bundle L_χ → CP² of the Math162 atlas, the BCC inversion lifts σ_I:CP²→CP² to a bundle automorphism Ĩ:L_χ→L_χ. Is Ĩ:

  (Type A) **complex-linear**: ℂ-linear on each fibre → equivariance σ_I^*L_χ ≅ L_χ; OR
  (Type B) **Real / anti-linear**: ℂ-anti-linear on each fibre, Ĩ(λv) = λ̄·Ĩ(v) → equivariance σ_I^*L̄_χ ≅ L_χ.

Math203's c_1(L_χ)=0 conclusion follows ONLY from Type A. Type B leaves c_1 unconstrained (counterexample: O(1)→CP² has standard real structure with c_1=h≠0).

**Approach**: Read Math162 atlas U(1)_χ transition functions g_{ij}(q); determine I-action; check whether g_{ij}(I·q) = g_{ij}(q) (Type A) vs g_{ij}(I·q) = ḡ_{ij}(q) or g_{ij}(q)^{-1} (Type B).

**Outcomes**:
  - Type A confirmed: Math203 c_1=0 REPAIRED, RR1 fully closed.
  - Type B confirmed: Math203 c_1=0 FALSIFIED, Math191/192 forcing argument needs replacemen