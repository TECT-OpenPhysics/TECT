# Stage 3 — External phenomenological qualification

Stage 3 is not a theorem but a **ledger discipline**. It encodes the requirement that internal mathematical closure (Stage 1 + Stage 2) is necessary but not sufficient for TOE qualification: the theory must also survive external falsification. Three sub-conditions must each be SEALED.

## Sub-condition scorecard (post Turn 5, 2026-04-24)

<table class="sm-table">
<thead><tr><th>Sub-condition</th><th>Content</th><th>Status</th><th>Source</th></tr></thead>
<tbody>
<tr>
<td>$S_3^{\rm (reproduce)}$</td>
<td>At least one independent reproduction of a Stage-1 or Stage-2 numerical certificate. Candidate targets: Math_IR_Bound-v4 Theorem v4-2 ($J_1 \in [+5.99\!\times\!10^{-2}, +1.51\!\times\!10^{-1}]$ at $N=256$); Math82-AddF Pillar 1 anchor ($m^{*2} = +4.247\!\times\!10^{-2}$ at $\mu^2 = +5\!\times\!10^{-3}$); Math49d-R5 wave-2 LR census; Math80-AddA+B Q6a 10-defect-moduli identity.</td>
<td><span class="tag tag-gap">OPEN</span></td>
<td>—</td>
</tr>
<tr>
<td>$S_3^{\rm (predict)}$</td>
<td>At least one prediction $\pi_j \in \mathcal{P}$ (Stage-2-E F-candidate) matched by experiment at pre-registered precision.</td>
<td><span class="tag tag-warn">GATED</span></td>
<td>Blocked on Stage-2-E SEALING + Pillar 4 Q2 numerical RGE</td>
</tr>
<tr>
<td>$S_3^{\rm (survive)}$</td>
<td>At least one prediction $\pi_k \in \mathcal{P}$ with experimental window open $\ge 1$ year without falsification.</td>
<td><span class="tag tag-warn">GATED</span></td>
<td>Blocked on $S_3^{\rm (predict)}$</td>
</tr>
</tbody>
</table>

## F-candidate experimental instrument inventory (Math60-Stage3)

The three pre-registered F-candidates from Stage-2-E, mapped to existing experimental data sources:

<table class="sm-table">
<thead>
<tr>
<th>F-candidate</th>
<th>Observable</th>
<th>Most direct test</th>
<th>Status</th>
<th>Distinguishing power</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>F1</strong></td>
<td>$R_{32} = \alpha_3(M_Z)/\alpha_2(M_Z) \approx 3.48 \pm 0.03$ (PDG 2024, $\sim 0.8\%$ precision)</td>
<td>LEP/SLD Z-pole + Tevatron + LHC fits, consolidated in PDG <em>Review of Particle Physics</em></td>
<td><span class="tag tag-warn">GATED</span> on Pillar 4 Q2 numerical RGE (Math75-Q2-AddA, queued)</td>
<td>Test of TECT-derived $R_{32}^{\rm TECT}$ vs experiment within $\pm 5\%$ tolerance band $[3.31, 3.65]$. Closest gate to SEALING (one Q2 numerical run away).</td>
</tr>
<tr>
<td><strong>F2</strong></td>
<td>$\Lambda_{\rm obs} \approx 1.1\!\times\!10^{-52}$ m$^{-2}$ (Planck 2018 + DESI 2024, $\sim 1\%$ on $\Omega_\Lambda$)</td>
<td>CMB + BAO + SNe Ia consortium analyses</td>
<td><span class="tag tag-partial">NEUTRAL</span></td>
<td>TECT prediction at LO: $\Lambda_{\rm TECT} = 0$ (Math58-v7). Sub-leading corrections uncomputed. Currently more of a consistency check than a forward prediction.</td>
</tr>
<tr>
<td><strong>F3</strong></td>
<td>Anisotropy at $O(a_{\rm BCC}^2)$ in flat-space dispersion — bounded by cryogenic cavity, atomic clocks, GZK cosmic-ray dispersion</td>
<td>Müller / Nagel cryogenic cavities ($\Delta c/c < 10^{-18}$); Pierre Auger photon dispersion ($\sim 10^{-23}$); Sr optical clocks ($10^{-19}$)</td>
<td><span class="tag tag-partial">CONSTRAINS</span></td>
<td><strong>Most distinguishing</strong> — SM has no built-in BCC anisotropy prediction. Existing isotropy bounds give $a_{\rm BCC} < 10^{-25}$ m. Genuine post-fit prediction once $a_{\rm BCC}$ is independently derived.</td>
</tr>
</tbody>
</table>

## Critical-path summary

| Sub-condition | Closest unblocking action | Estimated turns |
|---|---|---|
| $S_3^{\rm (reproduce)}$ | Independent recomputation of Math_IR_Bound-v4 Theorem v4-2 numerical certificate (mpmath.iv interval at $N=256$) | 1–2 |
| $S_3^{\rm (predict)}$ | Pillar 4 Q2 numerical RGE (Math75-Q2-AddA) → F1 ratio test | 1 |
| $S_3^{\rm (survive)}$ | $S_3^{\rm (predict)}$ + 1 calendar year wait | 1 + 1 yr |

**Operational status**: **0 / 3 SEALED** (was 0 / 3 throughout the project; F-candidate inventory now established, F1 closest to gate). Stage-3 SEALING begins as soon as Pillar 4 Q2 numerical run produces a quantitative $R_{32}^{\rm TECT}$ matched to PDG within tolerance.
