# Pillar 10 phase-transition origin programme & ℏ derivation chain

**Status (post Math119-AddB / Math120, 2026-04-26)**: Pillar 10 has a two-tier structure.

## Tier 1 — Classical no-go (CLOSED-AS-NO-GO)

`Math79-AddB` proves rigorously that no purely classical derivation of $\hbar$ from the post-condensation Brazovskii PDE is possible.  Buckingham $\pi$-theorem on dimensionless combinations of $\{\lambda, \gamma Y^{-1/2}, \mu^2/Y, a_{\rm BCC}^{-1}q_0, \varepsilon\}$ rules out 8 attempted derivation routes.  $\hbar$ remains an external phenomenological parameter at the classical level — same epistemic status as Newton's $G$ in GR or Einstein's $\Lambda$ in cosmology.

## Tier 2 — Phase-transition origin programme (PROVED CONDITIONAL)

`Math98` opens a parallel research programme: $\hbar$ as a frozen-in adiabatic action invariant of the cosmic BCC condensation transition.  Premise set $\mathcal{P}_{\rm PT} = \mathcal{P}_{\rm class} \cup \{\rho_{\rm cond}, \tau_{\rm PT}, \eta_{\rm top}\}$ strictly enlarges $\mathcal{P}_{\rm class}$, so Math79-AddB classical no-go does not apply.

Four independent mathematical routes converge:

1. **Path (a) — Kibble–Zurek $\tau_{\rm PT}$** (Math98-AddA): mean-field Brazovskii $\nu = 1/2$, $z = 2$ → $\tau_{\rm PT} \sim a_{\rm BCC}/c$.
2. **Path (b) — Volovik shell-mode $\eta_{\rm norm}$** (Math98-AddB / AddH BdG): closed form via Brazovskii shell DOS; $\eta_{\rm norm} \in [0.24, 0.28]$.
3. **Path (c) — Berry curvature $\eta_{\rm top}$** (Math98-AddC / AddI Chern): integer Chern number $C_{\rm total} = 2$; $\eta_{\rm top} = 0.33 \pm 0.08$.
4. **Path (d) — Onsager–Machlup adiabatic invariant** (Math98-AddE): independent corroboration.

`Math110` integrates this with a CP² topology + spin-2 Einstein-Hilbert matching:

$$\hbar = \frac{c^3 \, a_{\rm BCC}^2}{16\pi G}, \qquad a_{\rm BCC} = 4\sqrt{\pi}\,\ell_P^{\rm TECT}.$$

## ℏ numerical evaluation (Math119)

**SI prediction tier (algebraic check)**: plugging the predicted $a_{\rm BCC}^{\rm SI} = 4\sqrt{\pi}\,\ell_P^{\rm SI} = 1.146 \times 10^{-34}$ m into the master formula yields $\hbar^{\rm TECT} = 1.054572 \times 10^{-34}$ J·s, matching CODATA exactly.  This is **algebraically tautological** ($\ell_P^{\rm SI}$ uses measured $\hbar$) and proves only Math110-AddI's internal consistency.

**Operating-point tier (TECT v2.4 natural units)**: $a_{\rm BCC}^{\rm TECT} = 2\pi/q_0 = 9.24$, predicted $4\sqrt{\pi} = 7.09$, giving $R_{F5}^{\rm op-pt} = 1.303$ — **30 % deviation** at the Gate F5 FAIL/MARGINAL boundary.

## 30 % deviation analysis (Math119-AddA RETRACTED → Math119-AddB)

`Math119-AddA` initially claimed RG running of $q_0(\mu^2)$ explained the deviation with a 0.1 % post-hoc fit.  This claim was **retracted** because in standard Brazovskii free energy $q_0$ is an input parameter of the kinetic term, not a fluctuating saddle-point quantity.  The retraction (CLAUDE.md §6.1 honest-scope discipline) preserves theoretical integrity.

`Math119-AddB` identifies three plausible physical interpretations:
- **(α) TECT natural units ≠ Planck units** — $\ell_P^{\rm TECT, op} = 1.303$ unit-conversion factor (most likely; not falsification);
- **(β) Math110-AddG $16\pi$ coefficient gauge-convention dependent** — TT vs de Donder vs synchronous;
- **(γ) Hartree-physical $G^{\rm TECT}(\mu^2)$ scale-dependent** — would imply asymptotic-safety quantum gravity structure.

## Math120 — 4-test discrimination protocol

`Math120` documents that naive 1-loop perturbation is **mathematically prohibited** in TECT's operating regime: $\lambda I_{\rm shell}/\mu^2 \sim 220 \gg 1$ (Brazovskii fluctuation-induced first-order regime).  Proper treatment requires Hartree self-consistent resummation $\mu^2_H = \mu^2_0 + \lambda I_{\rm shell}(\mu^2_H)$.

Four independent discrimination tests are pre-registered (CLAUDE.md §6.3.3):

| Test | Method | Discriminates |
|---|---|---|
| **D1** | Multi-scale length consistency ($a_{\rm BCC}$ vs $\xi$ vs $h_{\rm grid}$) | (α) uniform vs (γ) scale-dependent vs (β) one-scale |
| **D2** | Multi-$\mu^2$ scan of $R_{F5}(\mu^2)$ | **DEFINITIVE**: (α/β) constant vs (γ) $\mu^2$-trending |
| **D3** | Independent Math45/46c $G^{\rm TECT}$ extraction | (α/β) consistent vs (γ) factor 1.30 |
| **D4** | Math110-AddG re-derivation in TT/de-Donder/synchronous gauges | (β) gauge-dependent vs (α/γ) gauge-invariant |

If verdict is **(γ) Hartree-RG-shift**: TECT spontaneously implements **Weinberg's asymptotic-safety scenario** (Weinberg 1979; Reuter 1998+) — a major quantum-gravity research direction.

## Math82-H execution requirements (UPDATED post-Math119-AddB)

The numerical Layer 1 pipeline now requires **double extrapolation**:

- $N$-grids: 32, 64, 128 (continuum limit $h \to 0$).
- $\mu^2$ schedule: $5 \times 10^{-3}, 2 \times 10^{-3}, 5 \times 10^{-4}, 10^{-4}$ (approach critical $\mu^2_c = R_C^{\rm global} = 1.14 \times 10^{-2}$).
- Joint Richardson + critical-scaling extrapolation.

Output: $a_{\rm BCC}^{\rm crit, cont}$ in TECT natural units, plus the $R_{F5}(\mu^2)$ trend that discriminates (α/β/γ).

## Honest scope statement

The Pillar 10 phase-transition origin programme is **PROVED CONDITIONAL** on:
- (i) Math82-H continuum + multi-$\mu^2$ data (Task #115 + extended);
- (ii) Independent Math45/46c $G^{\rm TECT}$ and Math60-C-AddC $\hbar^{\rm TECT}$ extractions (Tasks #127, #129);
- (iii) Math120 discrimination protocol verdict.

Tier 1 classical no-go is unaffected and remains intact.  TECT operational classification: **UCFT + Partial TOE**, with full registered falsifiability pathway.
