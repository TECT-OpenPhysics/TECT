**Honest-status assessment.** Every measured quantity below carries an explicit confidence label (TECT-Status-Tier T0–T7, defined on the [States](states.html) page) and a result-tag traceable to a code fingerprint and run manifest. Retracted results live in the append-only `Docs/status/NEGATIVE-RESULTS.md` ledger and are **not** removed from this page.

---

### Tier-organised summary

#### T7 PROVED (unconditional theorem)

| Item | Result | Source |
|---|---|---|
| Math222 mathematical skeleton | flat-Cartan ground-state forcing under (H1) $\kappa_\chi,\kappa_5>0$ + (H2) $\Delta\Gamma_{\rm rest}\geq -\epsilon\,\mathcal F_{\rm top}$, $\epsilon<1$ | Math222 v1.1 (2026-04-29) |

#### T6 PROVED CONDITIONAL

| Item | Result | Conditional inputs | Source |
|---|---|---|---|
| Pillar 1 ($m^{*2}_{\rm num}$) | $+4.247\times 10^{-2}$ at $\mu^2=+5\times 10^{-3}$, $N=32$, local minimum confirmed ($\lambda_{\min}>0$); 14 Newton iters; $\|\nabla L\|/\sqrt{\dim}=6.11\times 10^{-9}$ | Math60-Stage 1 hypothesis list | Math82-AddF (2026-04-24) |
| Pillar 11 ($\Lambda_{\rm cosmo}$) | 4-sector cancellation $\Lambda_{\rm monopole}+\Lambda_{\rm vortex}+\Lambda_{\rm BCC}+\Lambda_{\rm Dirac}=0$ | Pauli-Villars + BCC condensate-energy convention | Math58-v7 (2026-04-24) |
| Lemma A — sign-only | $\kappa_\chi,\kappa_5>0$ via trace-positivity | non-trivial gauge action on shell | Math221-AddB/C (2026-04-29) |

#### T4 STRONG EVIDENCE

| Item | Result | Source |
|---|---|---|
| Pillar 6 ($M_{\rm GUT}$, Pati–Salam minimal $\Delta b=(0,0,0)$) | $6.36\times 10^{16}$ GeV at $\alpha_{\rm GUT}^{-1}=46.52$, RMS 0.20%, 349/1625 configs at $M_{\rm GUT}\geq 4\times 10^{15}$ GeV | Math77-Q6b-AddB (2026-04-24) |

#### T3 PROOF SKETCH (gaps marked)

| Item | Marked gap | Source |
|---|---|---|
| Lemma A — full proportionality | audit-clean trace-stiffness proof independent of Math216-AddB | Math221-AddC + Task #168 |
| Lemma B (rest-bound) | $\kappa_{\min}>C_m+C_d$ analytical; current $\epsilon\approx 0.216$ marginal | Math220-AddA / AddB + Task #169 |

#### T2 CONJECTURE (falsification gate pre-registered)

| Item | Conjecture | Falsification path | Source |
|---|---|---|---|
| Pillar 10 (phase-transition origin) | $\hbar$ from BCC condensation | F1–F3 numerical gates | Math98 (2026-04-25) |
| $E_3'$ (cosmologically realised vacuum) | Mechanism I (suppressed Kibble–Zurek) OR Mechanism II (catalysed annihilation) | Task #162-R | Math218-AddA (2026-04-29) |

#### T1 OPEN

| Item | Status | Owner |
|---|---|---|
| Phase-Z deep-endpoint at $\mu^2<0$ | bifurcation interval $(-0.1, +5\times 10^{-3})$ identified; symmetry-broken-seed re-run pending | Math82-AddE (next GPU run) |

#### T0 REFUTED

| Item | What was withdrawn | Source |
|---|---|---|
| Pillar 10 R5 first iteration | $\rho_\Lambda\approx 3.4\times 10^{-44}$, $\rho_{\rm Cas}\approx -8.7\times 10^{-7}$, $\rho_{g-2}\approx +8\times 10^{+7}$ — three failure modes diverge | Math79-AddA (2026-04-24) |
| Pillar 10 classical no-go | 8 independent failed routes (Math59 + Math59-v3 + R5) | Math79-AddB |
| GAP-2 Berry-phase TECT-specific signature | $\pi_1(M_{\rm BCC})=\{e\}$, all loops contractible | Math226 (2026-04-29) |

---

### Active deep-quench run (Math82-H phase 2)

| Run | $\mu^2$ | Result | Wall | Status |
|---|---|---|---|---|
| `math82H_phase2_v266d` | $-0.7$ | $\|\nabla\|/\sqrt{\dim}=2.45\times 10^{-8}$ at step 24 (target $10^{-8}$) | 53.9 h | NO_CONVERGENCE — plateau (3 saturated gates: tCG=30 000, $\eta\to 0.86$, $\Delta=63.5$); warm-restart Plan A queued |

CLI command + downloadable artefacts: see the per-run card on this page.

---

### Reading guide

- **TECT-Status-Tier (T0–T7)** definitions, per-tier mandatory artefacts, and forbidden-phrase list: [States](states.html).
- **Per-run CLI commands + download links**: per-run cards above (click a Run ID in the summary table to expand).
- **Full append-only retraction ledger**: [Records](records.html).
- **Older code versions** (re-run any past numerical result with the matching driver version): [Codebase → Older Versions](code-old.html).
