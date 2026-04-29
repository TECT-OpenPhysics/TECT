# Stage 2 — Global Closure Theorem sub-components (Math60-A..E)

The five Stage-2 sub-theorems represent meta-level consistency conditions that no individual Stage-1 pillar can address. None is reducible to a Stage-1 closure: each carries its own hypothesis list $H_{A..E}$ and closure gate $G_{A..E}$. Recommended closure order (lowest cost first): **A → E → B → D → C**.

## Sub-component scorecard (post Turn 5, 2026-04-24)

<table class="sm-table">
<thead>
<tr>
<th>Sub-theorem</th>
<th>Name</th>
<th>Closure gate</th>
<th>Status</th>
<th>Mainline source</th>
<th>Open-Q tag / Task</th>
</tr>
</thead>
<tbody>
<tr>
<td>Math60-A</td>
<td>Meta-consistency of $\{H_i\}_{i=1}^{11}$ on a single background $\mathcal{M}_0$</td>
<td>Commutativity diagrams for each ordered pair $(i,j) \in \{1..11\}^2$ archived; 17/38/0/55 split (compatible / no-constraint / contradicting / total)</td>
<td><span class="tag tag-ok">SEALED</span></td>
<td>Math83-Math60-A-meta-consistency-audit (2026-04-24)</td>
<td>Q-2026-04-21-S2A — Task #81 CLOSED</td>
</tr>
<tr>
<td>Math60-B</td>
<td>Parameter compression $n_{\rm free}$ vs SM $n=19$</td>
<td>Explicit map $\Xi: \mathrm{A0} \to (\lambda, \gamma, Y, a_{\rm BCC}, \hbar)$ + reproduction of SM gauge sector + matter</td>
<td><span class="tag tag-ok">SEALED CONDITIONAL</span></td>
<td>Math60-Stage2-BDE Theorem `thm:parameter-compression`: 4 classical + 1 external $\hbar$, $\rho_{\rm compression} = 4.75\times$ (or 6.3× if $a_{\rm BCC}$ derivability holds)</td>
<td>Conditional on Pillar 4 Q2 + Pillar 6 Q6b/Q6d closure</td>
</tr>
<tr>
<td>Math60-C</td>
<td>Quantisation closure (canonical or path-integral)</td>
<td>Operator algebra $[\hat\Psi, \hat\Pi_\Psi] = i\hbar\,\delta$ + Pillar 1 mass gap + Pillar 4 gauge algebra + Pillar 11 $\Lambda$ cancellation extend to quantum sector</td>
<td><span class="tag tag-warn">OUTLINE</span></td>
<td>Math60-C-quantum-completion-outline: 3 quantum observables (QO1 zero-point Brazovskii energy; QO2 Casimir with form-factor suppression; QO3 anomalous noise spectrum at $\omega_{\rm shell}$); 3 compatibility checks (C1 mass gap, C2 gauge algebra, C3 $\Lambda$ cancellation) all preserved</td>
<td>Promoted from DEFERRED via Math79-AddB Cor. `cor:quantum-completion`. Full Stage-2-C SEALING deferred to a separate quantum-completion programme.</td>
</tr>
<tr>
<td>Math60-D</td>
<td>Observable map $\mathcal{O}: \text{params} \to \mathbb{R}^{n_{\rm obs}}$</td>
<td>$\mathrm{rank}(\partial \mathcal{O} / \partial p) = 5$ (full rank in 5-parameter direction space); local injectivity guarantees distinct TECT params produce distinct predictions</td>
<td><span class="tag tag-warn">OUTLINE</span></td>
<td>Math60-Stage2-BDE Theorem `thm:observable-map-injectivity`. Channels listed: $\alpha_{1,2,3}(M_Z)$, $m_e/m_\mu/m_\tau$, $m_W/m_Z$, $\Lambda_{\rm obs}$ — at least 9 dimensions.</td>
<td>$5\times 9$ Jacobian rank verification pending Pillar 4 Q2 + Pillar 6 Q6d numerical closure</td>
</tr>
<tr>
<td>Math60-E</td>
<td>Falsifiability package $\|\mathcal{P}\| \ge 3$</td>
<td>Three pre-registered predictions with written falsification thresholds</td>
<td><span class="tag tag-warn">OUTLINE</span></td>
<td>Math60-Stage2-BDE pre-registers F1/F2/F3 (see Stage 3 below for instrument inventory)</td>
<td>SEALING requires explicit numerical predictions for each F-candidate (gated on Pillar 4 Q2 for F1)</td>
</tr>
</tbody>
</table>

**Operational status**: 1 SEALED + 1 SEALED CONDITIONAL + 3 OUTLINE = **3 / 5 advanced** (was 1 / 5 prior to Turn 3-4 work). The remaining gap to fully SEALED is concentrated on a single numerical closure: Pillar 4 Q2 (Math75-Q2-AddA), which when executed unlocks B (unconditional), D (Jacobian-rank verification), and E (F1 quantitative prediction).
