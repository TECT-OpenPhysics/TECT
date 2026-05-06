# Stage 3 — External Phenomenological Qualification

TECT's internal theorem framework ($S_1$ and $S_2$) is a **classical field theory** (Math145–147). Stage 3 closes the final TOE qualification gap by requiring independent external validation: reproduction of a numerical certificate, pre-registered prediction matched by experiment, and surviving falsification window.

## Qualification Predicate

$$S_3:= S_3^{(\mathrm{reproduce})}\;\wedge\;S_3^{(\mathrm{predict})}\;\wedge\;S_3^{(\mathrm{survive})}$$

| Sub-condition | Definition | Current Status |
|---|---|---|
| **Reproduce** | Independent re-execution of a Stage-1 or Stage-2 numerical certificate | OPEN (experimental instruments inventoried 2026-04-24) |
| **Predict** | At least one pre-registered falsification candidate ($F_j$) matched by experiment at its pre-registered precision | OPEN (F1 closest to gate) |
| **Survive** | At least one prediction has survived falsification window $\ge$ 1 year without exclusion | OPEN (pre-register start date required) |

## Falsification Candidates (F1–F3)

Three independent predictions, each arising from Stage-1/2 content:

### F1: Gauge-coupling ratio at electroweak scale
- **Prediction**: $R_{32} = \alpha_3(M_Z) / \alpha_2(M_Z)$ computed from Pillar 4 RGE evolution
- **Current status**: GATED on Pillar 4 Q2 numerical RGE integration (Task #92)
- **Experimental tolerance**: $\pm 5\%$ (TECT); SM data within $\pm 0.8\%$ (PDG 2024)
- **Falsification threshold**: If $|R_{32}^{\rm TECT} - R_{32}^{\rm exp}| > 0.05$, reject TECT GUT sector
- **Closest to gate**: 1 Pillar-4 RGE run away

### F2: Equivalence principle violation ($\eta_{\rm EP}$)
- **Prediction**: Dipole moment from TECT BCC anisotropy (suppressed classically, $O(\hbar)$ at quantum level)
- **Current status**: NEUTRAL (LO TECT prediction = 0; higher-order loops uncomputed)
- **Experimental tolerance**: $\pm [2\times 10^{-13}, 8\times 10^{-13}]$ (MICROSCOPE/Eötvös)
- **Falsification gate**: F2 becomes active once Pillar 10 (quantum $\hbar$ origin) moves from CLOSED-AS-NO-GO to a quantum-completion framework

### F3: Cosmic anisotropy from BCC condensate ordering
- **Prediction**: Anisotropy coupling $O(a_{\rm BCC}^2)$ breaks isotropy at ultra-high precision
- **Current status**: CONSTRAINED (existing experiments: cryogenic cavity $< 10^{-25}$ m, atomic clocks, cosmic-ray dispersion)
- **Falsification threshold**: BCC condensate modulation length $a_{\rm BCC}$ must be below current bounds or show new directional dependence
- **Distinction**: SM has no anisotropy prediction; F3 is a genuinely distinguishing test

**Canonical reference**: `Docs/math/TECT-Math60-Stage3-experiment-inventory.tex.txt` (2026-04-24 audit)

## Scope Extension: Cosmological TOE ($S_{\rm IV}$)

**NEW 2026-04-26**: A formal cosmological extension (Branch B) has been registered and advanced to STRONG CLOSURE DRAFT. This adds:

- **Pre-transition phase** ($\mathcal{P}_{\rm pre}$): ultra-high-energy isotropic fluid at $T \gg T_c$ (Math145)
- **Kibble-Zurek mechanism**: Topological defect formation during cosmological quench (Math146)
- **CMB/GW/DM observables**: Falsification gates tied to Planck, LIGO-Virgo-KAGRA, LISA (Math147)
- **Cosmological constant**: Latent-heat contribution ($\sim 10^{-120} M_{\rm Pl}^4$, subdominant to observed $\Lambda_{\rm obs}$)

**Scope $S_{\rm IV}$ status**: PROGRAMME REGISTERED → STRONG CLOSURE DRAFT.
