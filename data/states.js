/**
 * @MANUAL_OVERRIDE — hand-curated; generate_website.py will skip this file.
 * states.js — TECT TOE qualification states.
 *
 * 2026-04-26: created as part of the website restructure (rev 3).
 * 2026-04-27: added "Quantum theory proof status" card.
 *
 * 2026-04-28 rev 4 (hand-curated): per user directive,
 *   - page title narrowed from "States & comparison" to "States"; subtitle
 *     drops the framework-comparison framing.
 *   - Stage-2 and "Quantum theory proof status" cards merged into a
 *     single Stage-2 card carrying the full four-gate table, Pillar-4
 *     sub-task decomposition, bifurcation-resolution path, audit-discipline
 *     scorecard, and closing verdict.
 *   - "Side-by-side comparison vs other frameworks" card trimmed to
 *     TECT vs SM, Superstring/M, LQG only (the multi-framework comparison
 *     now lives on Overview); table uses the .cmp-table responsive class.
 */
window.TECT_STATES = {
  title: "States",
  subtitle: "Three-stage TOE qualification predicate $\\mathrm{TOE}:=S_1\\wedge S_2\\wedge S_3$ — current state of the eleven emergence pillars (Stage-1), the Global Closure plus four quantum-consistency gates (Stage-2), and the external phenomenological qualification (Stage-3).",
  lastUpdated: "2026-04-28",

  blocks: [
    {
      type: "card",
      title: "TECT-Status-Tier (T0–T7) — canonical 8-tier nomenclature (binding from 2026-04-29)",
      blocks: [{
        type: "html",
        content:
          "<p>Every TECT proof-progress claim — in Math notes, papers, status rows, and on this website — uses one of the eight canonical tiers below. The schema is a hybrid of standard mathematical-physics nomenclature (theorem / conjecture / open) and standard particle-physics nomenclature (rigorously proved / established / strong evidence / refuted). Legacy labels (PARTIAL-ADVANCED, NEAR-CLOSURE, STRONG CLOSURE DRAFT, etc.) are mapped to T-tiers per <code>Docs/policy/STATUS_NOMENCLATURE.md</code> §3.</p>" +
          "<table class=\"status-tier\"><thead><tr><th>Tier</th><th>Label</th><th>Definition</th><th>Standard physics phrase</th><th>Standard math phrase</th></tr></thead><tbody>" +
          "<tr><td><strong>T7</strong></td><td><strong>PROVED</strong></td><td>Unconditional mathematical theorem; all hypotheses textbook-standard.</td><td>\"rigorously proved\"</td><td>Theorem</td></tr>" +
          "<tr><td><strong>T6</strong></td><td><strong>PROVED CONDITIONAL</strong></td><td>Theorem under explicit named hypothesis set $H_1, \\ldots, H_n$, each either textbook or separately tracked.</td><td>\"established conditional on $H$\"</td><td>Theorem (conditional)</td></tr>" +
          "<tr><td><strong>T5</strong></td><td><strong>CLOSED@N-LOOP</strong></td><td>Established at perturbative order $N$ (typically 1-loop). Order $N$ stated explicitly.</td><td>\"established at $N$-loop\"</td><td>Theorem (perturbative, order $N$)</td></tr>" +
          "<tr><td><strong>T4</strong></td><td><strong>STRONG EVIDENCE</strong></td><td>Multi-line analytical+numerical+audit evidence; no rigorous theorem yet.</td><td>\"strong evidence supports\"</td><td>Lemma sketch with corroboration</td></tr>" +
          "<tr><td><strong>T3</strong></td><td><strong>PROOF SKETCH</strong></td><td>Main logic written, technical gaps marked OPEN. Convertible to T6 by closing gaps.</td><td>\"we sketch a proof\"</td><td>Proof sketch (gaps marked)</td></tr>" +
          "<tr><td><strong>T2</strong></td><td><strong>CONJECTURE</strong></td><td>Explicit hypothesis with partial evidence; falsification gate pre-registered.</td><td>\"we conjecture\"</td><td>Conjecture</td></tr>" +
          "<tr><td><strong>T1</strong></td><td><strong>OPEN</strong></td><td>Unaddressed in TECT, or in active research with no partial result yet.</td><td>\"remains open\"</td><td>Open problem</td></tr>" +
          "<tr><td><strong>T0</strong></td><td><strong>REFUTED</strong></td><td>Explicit counter-example, falsification, or audit-rollback. Claim withdrawn from canonical record.</td><td>\"refuted by\"</td><td>Counter-example / negative result</td></tr>" +
          "</tbody></table>" +
          "<p><strong>Promotion path</strong>: T1 → T2 → T3 → T4 → T5 → T6 → T7. T0 is parallel (rejection axis). A T2→T6 promotion must pass through T3, T4, T5 unless the proof is genuinely a one-shot textbook argument that lands directly at T6.</p>" +
          "<p><strong>Per-tier required artefacts</strong>: T7 requires complete proof + §6.3.1 devil's-advocate + §6.3.4 quantitative sanity check + §6.3.5(a) self-adversarial review + reviewer audit pass + atomic-commit; T6 adds explicit hypothesis set; T5 adds explicit perturbative order; T4 requires multi-line evidence summary + remaining-gap list; T3 requires marked gap list + tracked tasks; T2 requires pre-registered falsification gate (CLAUDE.md §6.3.3 binding); T1 requires OPEN-QUESTIONS.md entry; T0 requires NEGATIVE-RESULTS.md entry with R- or F- tag.</p>" +
          "<p><strong>Source policy</strong>: <code>Docs/policy/STATUS_NOMENCLATURE.md</code> (binding from 2026-04-29). Cross-references: CLAUDE.md §7 (Pillar status semantics, updated), §6.3.1 / §6.3.3 / §6.3.5 (audit gates), <code>Docs/status/TOE-FACT-SHEET.md</code> (scoreboard), <code>Docs/status/NEGATIVE-RESULTS.md</code> (T0), <code>Docs/status/OPEN-QUESTIONS.md</code> (T1/T2/T3).</p>"
      }]
    },
    {
      type: "card",
      title: "11-Pillar scoreboard in canonical tiers (post-2026-04-29 migration)",
      blocks: [{
        type: "html",
        content:
          "<p>Each of the 11 emergence pillars carries a canonical T-tier. Aggregate <em>S<sub>1</sub></em> qualification is the conjunction of all pillar tiers.</p>" +
          "<table class=\"pillar-tier\"><thead><tr><th>Pillar</th><th>Subject</th><th>Canonical tier</th><th>Conditional inputs (if T6)</th></tr></thead><tbody>" +
          "<tr><td>1</td><td>BCC condensate uniqueness</td><td><strong>T6</strong></td><td>Math60-Stage 1 hypothesis list</td></tr>" +
          "<tr><td>2</td><td>Lorentz invariance + emergent metric</td><td><strong>T6</strong></td><td>matter-coupling hierarchy</td></tr>" +
          "<tr><td>3</td><td>Diffeomorphism invariance</td><td><strong>T5 (N=1)</strong></td><td>1-loop closure; higher-loop pending</td></tr>" +
          "<tr><td>4</td><td>Gauge group emergence (sub-task 1: SO(10) bundle, 2: flat-Cartan forcing, 3: SO(10)→G<sub>SM</sub>)</td><td><strong>T4</strong> aggregate (sub-task 1: T6, 2: T6 conditional on Lemmas A+B, 3: T6 conditional on Pillar 6)</td><td>Lemmas A, B + Pillar 6 Higgs mechanism</td></tr>" +
          "<tr><td>5</td><td>Standard-model fermion content</td><td><strong>T7</strong></td><td>—</td></tr>" +
          "<tr><td>6</td><td>GUT unification (SO(10))</td><td><strong>T4</strong></td><td>Higgs scalar potential closure (Task #170)</td></tr>" +
          "<tr><td>7</td><td>Spin-statistics</td><td><strong>T7</strong></td><td>—</td></tr>" +
          "<tr><td>8</td><td>Equivalence principle</td><td><strong>T7</strong></td><td>—</td></tr>" +
          "<tr><td>9</td><td>Geodesic motion</td><td><strong>T7</strong></td><td>—</td></tr>" +
          "<tr><td>10</td><td>Quantum completion (ℏ emergence)</td><td><strong>T0</strong> (classical no-go) + <strong>T2</strong> (phase-transition origin)</td><td>Pre-registered F1–F3 (Math98)</td></tr>" +
          "<tr><td>11</td><td>Cosmological observables</td><td><strong>T4</strong></td><td>numerical BCC solution (Task #115)</td></tr>" +
          "</tbody></table>" +
          "<p><em>Aggregate S<sub>1</sub></em>: 4 × T7 (Pillars 5, 7, 8, 9) + 2 × T6 (Pillars 1, 2) + 1 × T5 (Pillar 3) + 3 × T4 (Pillars 4, 6, 11) + 1 × T0+T2 (Pillar 10). Until all 11 pillars reach ≥ T6, S<sub>1</sub> qualification is <strong>partial</strong>.</p>"
      }]
    },
    {
      type: "card",
      title: "Active flat-Cartan forcing chain — per-Math222-component tiers",
      blocks: [{
        type: "html",
        content:
          "<table class=\"forcing-chain\"><thead><tr><th>Component</th><th>Tier</th><th>Source</th><th>Promotion path</th></tr></thead><tbody>" +
          "<tr><td>Math222 mathematical skeleton (Hodge + Yang-Mills + Chern-Weil + composition)</td><td><strong>T7</strong></td><td>Math222 v1.1 (textbook composition only)</td><td>—</td></tr>" +
          "<tr><td>Lemma A (microscopic positive curvature stiffness $\\kappa_\\chi, \\kappa_5 > 0$)</td><td><strong>T6 sign-only / T3 full</strong></td><td>Math221-AddB sign-positivity, Math221-AddC charge table + non-trivial action</td><td>Task #168 (audit-clean trace-stiffness proportionality)</td></tr>" +
          "<tr><td>Lemma B (relative no-negative-offset $\\Delta\\Gamma_{\\rm rest} \\geq -\\epsilon\\,\\mathcal F_{\\rm top}$, $\\epsilon < 1$)</td><td><strong>T3</strong></td><td>Math220-AddA structural repair, Math220-AddB ε ≈ 0.2 marginal</td><td>Task #169 ($\\kappa_{\\min} > C_m + C_d$ analytically)</td></tr>" +
          "<tr><td>E<sub>3</sub>' cosmological realisation</td><td><strong>T2</strong></td><td>Math218-AddA conditional conjecture (Mechanism I / II)</td><td>Task #162-R (Mechanism I or II)</td></tr>" +
          "</tbody></table>" +
          "<p><strong>Composite Pillar 4 sub-task 2 status</strong>: <strong>T6 conditional on (Lemma A, Lemma B, E<sub>2</sub>, E<sub>3</sub>, E<sub>3</sub>')</strong>. Mathematical skeleton is T7; conditional set is T2/T3/T6 across components.</p>"
      }]
    },
    {
      type: "card",
      title: "GAP-1/2/3/4 quantum-completion qualification ($S_2$)",
      blocks: [{
        type: "html",
        content:
          "<table class=\"gap-tier\"><thead><tr><th>GAP</th><th>Subject</th><th>Tier</th><th>Source</th></tr></thead><tbody>" +
          "<tr><td>GAP-1</td><td>ℏ emergence (canonical commutator from fermion-loop saturation)</td><td><strong>T6 (weak)</strong></td><td>Math158 + Math163 boson-loop subdominance + Math227 second-order audit + Math200-AddC ℏ_TECT non-running</td></tr>" +
          "<tr><td>GAP-2</td><td>BRST quantisation (FP determinant + Berry-phase signature)</td><td><strong>T6 conditional on Pillar 4</strong> (BRST framework) + <strong>T0</strong> (Berry-phase TECT-specific signature)</td><td>Math160 §II BRST PROVED CONDITIONAL; Math226 Berry-phase REFUTED ($\\pi_1 = \\{e\\}$)</td></tr>" +
          "<tr><td>GAP-3</td><td>Anomaly cancellation (SO(10) trace method on $\\mathbf{16}$)</td><td><strong>T6 conditional on Pillar 4</strong></td><td>Math157 numerical-verified anomaly trace</td></tr>" +
          "<tr><td>GAP-4</td><td>Cosmological observables (Kibble-Zurek defect spectrum)</td><td><strong>T2</strong> (rescoped from inflationary, falsified)</td><td>Math159 rescope; Math151 inflationary branch REFUTED (T0)</td></tr>" +
          "</tbody></table>" +
          "<p><strong>Aggregate $S_2$</strong>: partial (T2 component blocks unconditional sealing). Pillar 4 sub-task 2/3 is the unique critical blocker.</p>"
      }]
    },
    {
      type: "card",
      title: "Legacy-label translation (read-only reference for older Math notes)",
      blocks: [{
        type: "html",
        content:
          "<p>Math notes written before 2026-04-29 use legacy labels. The translation table below is binding for any audit / review of older notes:</p>" +
          "<table class=\"legacy-translate\"><thead><tr><th>Legacy label</th><th>Canonical tier</th></tr></thead><tbody>" +
          "<tr><td><code>PROVED</code> (no qualifier) / <code>PROVED UNCONDITIONAL</code></td><td>T7</td></tr>" +
          "<tr><td><code>PROVED CONDITIONAL</code> / <code>PROVED with caveat</code></td><td>T6</td></tr>" +
          "<tr><td><code>CLOSED@1-loop</code> / <code>CLOSED@1-LOOP</code></td><td>T5 (N=1)</td></tr>" +
          "<tr><td><code>PARTIAL-ADVANCED</code> (multi-line evidence)</td><td>T4</td></tr>" +
          "<tr><td><code>PARTIAL-ADVANCED</code> (just sketch)</td><td>T3</td></tr>" +
          "<tr><td><code>STRONG CLOSURE DRAFT</code> / <code>STRONG DRAFT</code></td><td>T3 or T4</td></tr>" +
          "<tr><td><code>PARTIAL ACCEPT</code></td><td>T3</td></tr>" +
          "<tr><td><code>NEAR-CLOSURE</code></td><td>T3 or T4</td></tr>" +
          "<tr><td><code>STRUCTURAL DRAFT</code></td><td>T3</td></tr>" +
          "<tr><td><code>SCAFFOLD</code></td><td>T2</td></tr>" +
          "<tr><td><code>OUTLINE</code></td><td>T2 or T3</td></tr>" +
          "<tr><td><code>CONDITIONAL CONJECTURE</code></td><td>T2</td></tr>" +
          "<tr><td><code>OPEN-NEGATIVE REFINED</code></td><td>T0 (with explicit no-go cited)</td></tr>" +
          "<tr><td><code>NOT ADDRESSED</code></td><td>T1</td></tr>" +
          "<tr><td><code>AUDIT-FLAGGED</code></td><td>T0 if withdrawn; T3 if salvageable</td></tr>" +
          "<tr><td><code>FAIL AS PROOF</code> / <code>RETRACTED</code> / <code>FALSIFIED</code></td><td>T0</td></tr>" +
          "</tbody></table>" +
          "<p><strong>Forbidden phrases going forward</strong>: \"essentially proved\", \"almost closed\", \"at theorem level\", \"conjecturally established\", \"near closure\". Use exact T-tier labels only.</p>"
      }]
    },
    {
      type: "card",
      title: "TOE qualification predicate (Math60 specification)",
      blocks: [{
        type: "html",
        content:
          "<p>TECT's TOE qualification is a conjunction of three predicates introduced in <code>Docs/math/TECT-Math60-TOE-Global-Closure-Spec.tex.txt</code>:</p>" +
          "<p>$$\\mathrm{TOE}\\;:=\\;S_{1}\\;\\wedge\\;S_{2}\\;\\wedge\\;S_{3}.$$</p>" +
          "<ul>" +
            "<li><strong>$S_1$</strong> — theorem-level closure of all eleven emergence pillars individually.</li>" +
            "<li><strong>$S_2$</strong> — Global Closure Theorem (Math60-A through Math60-E) plus the four quantum-consistency gates GAP-1 ($\\hbar$ matching), GAP-2 (BRST), GAP-3 (anomaly), GAP-4 (observables).</li>" +
            "<li><strong>$S_3$</strong> — external phenomenological qualification (one reproduction, one matched prediction, one $\\geq 1$-year survival window).</li>" +
          "</ul>" +
          "<p><strong>Status snapshot (2026-04-28, post-R8):</strong></p>" +
          "<table class=\"sm-table\">" +
            "<thead><tr><th>Predicate</th><th>Status</th><th>Driving evidence / blocker</th></tr></thead>" +
            "<tbody>" +
            "<tr><td>$S_1$</td><td><span class=\"tag tag-partial\">PARTIAL</span></td>" +
                "<td>4 PROVED unconditional (Pillars 5, 7, 8, 9) + 2 PROVED CONDITIONAL (1, 2) + 1 CLOSED@1-loop (3) + 3 PARTIAL-ADVANCED (4, 6, 10) + 1 NEAR-CLOSURE (11). Pillar 4 sub-tasks 1 + 2 PROVED CONDITIONAL (Math162+167, Math191+192).</td></tr>" +
            "<tr><td>$S_2$</td><td><span class=\"tag tag-partial\">PARTIAL</span></td>" +
                "<td>Five Math60 sub-theorems SEALED. GAP-1 PROVED CONDITIONAL (weak); GAP-2 PROVED CONDITIONAL on Pillar 4 + OUTLINE (signature); GAP-3 PROVED CONDITIONAL on Pillar 4; GAP-4 RESCOPED to KZ branch with PROVISIONAL prediction (Math172).</td></tr>" +
            "<tr><td>$S_3$</td><td><span class=\"tag tag-warn\">PROVISIONAL prediction (Math172)</span></td>" +
                "<td>0 / 3 sub-conditions sealed; Math172 elevates $S_3^{\\rm (predict)}$ to PROVISIONAL via Kibble–Zurek GW prediction observable by SKA / IPTA-2 (2028–2030).</td></tr>" +
            "</tbody>" +
          "</table>"
      }]
    },

    {
      type: "card",
      title: "Stage-1 — eleven emergence pillars",
      blocks: [{
        type: "html",
        content:
          "<p>Each pillar fixes one piece of empirical physics that an axiomatic candidate must reproduce. The aggregate scorecard reflects the post-R8 state.</p>" +
          "<table class=\"sm-table\">" +
            "<thead><tr><th>Status</th><th>Count</th><th>Pillars</th></tr></thead>" +
            "<tbody>" +
            "<tr><td><span class=\"tag tag-ok\">PROVED unconditional</span></td><td>4</td><td>5 (chirality), 7 (quantum consistency / per-generation), 8 (Lorentz invariance), 9 (equivalence principle)</td></tr>" +
            "<tr><td><span class=\"tag tag-ok\">PROVED CONDITIONAL</span></td><td>2</td><td>1 (mass; single-mode caveat), 2 (inertia; H-suppression hypothesis)</td></tr>" +
            "<tr><td><span class=\"tag tag-ok\">CLOSED@1-loop</span></td><td>1</td><td>3 (gravity)</td></tr>" +
            "<tr><td><span class=\"tag tag-partial\">PARTIAL-ADVANCED</span></td><td>3</td><td>4 (gauge interactions; sub-tasks 1+2 PROVED CONDITIONAL, sub-task 3 STRONG DRAFT), 6 (generations / SM embedding), 10 ($\\hbar$ origin)</td></tr>" +
            "<tr><td><span class=\"tag tag-warn\">NEAR-CLOSURE</span></td><td>1</td><td>11 (cosmological constant $\\Lambda$)</td></tr>" +
            "</tbody>" +
          "</table>" +
          "<p><em>Pillar 10 demotion (2026-04-26)</em>: Math149 GAP-1 closure was PROVED but Math156 §3.1 demonstrated that Routes A and B share an elastic-modulus input; demoted to PROVED CONDITIONAL (weak); Math163 substantiated this via the boson-loop subdominance ratio.</p>" +
          "<p><em>Pillar 4 sub-task 2 RESCUED (post-R8)</em>: Math191 establishes $c_1(\\mathrm{U}(1)_\\chi) = 0$; Math192 establishes $c_2(E_{\\rm SU(5)}) = 0$. Scenario B confirmed; $\\mathrm{ind}(D_E^c) = 16$ matches the SO(10) $\\mathbf{16}$ exactly.</p>"
      }]
    },

    {
      type: "card",
      title: "Stage-2 — Global Closure + four quantum-consistency gates",
      blocks: [{
        type: "html",
        content:
          "<p>Stage-2 ($S_2$) demands theorem-level closure of the five Math60 sub-theorems plus four explicit quantum-consistency gates. Five Math60 sub-theorems are SEALED (A meta-consistency, B parameter-compression conditional, C-AddD all three quantum observables in closed form, D observable-map global injectivity, E falsifiability package). The post-Math156 audit added four quantum-consistency gates (GAP-1 to GAP-4) that must be discharged before $S_2$ is unconditionally sealed. The post-30-turn (R1–R8, Math162–196) state is summarised below.</p>" +
          "<p>The quantum-completion sector of TECT — the set of conditions that must hold for the framework to be a genuine quantum field theory rather than a classical UCFT — is decomposed into the four gates and a single critical bottleneck (Pillar 4 $\\mathrm{SO}(10)+\\mathbf{16}$ emergence).</p>" +
          "<table class=\"sm-table\">" +
            "<thead><tr><th>Gate</th><th>Sub-claim</th><th>Status</th><th>Anchor result</th><th>Open task</th></tr></thead>" +
            "<tbody>" +
            "<tr><td><strong>GAP-1</strong></td><td>$\\hbar_{\\rm Fock} = \\hbar_{\\rm gravity}$ via independent matter-side route</td>" +
              "<td><span class=\"tag tag-ok\">PROVED CONDITIONAL (weak)</span> at $M_Z$; <span class=\"tag tag-warn\">scale-coherence under RGE OPEN</span></td>" +
              "<td>Math163 fermion-loop saturation: $R_{\\rm boson/fermion}\\approx 0.12$ via $y_t^2\\gg g_{\\rm EW}^2$; Math196 KZ rate from Friedmann coupling. <em>Math200 (2026-04-28, AUDIT-FLAGGED STRONG DRAFT)</em>: 1-loop SM RGE proxy $\\hbar_{\\rm proxy}(\\mu)\\propto g_1^2 g_2 g_3$ drifts $\\approx 19\\%$ over $[M_Z, M_X]$; the proxy itself is audit-flagged (functional form of $\\hbar_{\\rm TECT}(\\mu)$ undefined; $g_i(\\mu)$ sign/normalisation candidate-defect). Math200 falsifies the proxy, NOT GAP-1.</td>" +
              "<td>Tasks #147 (2-loop RGE), #148 ($\\hbar_{\\rm TECT}$ matching functional, HIGHEST PRIORITY), #149 (proxy sensitivity scan)</td></tr>" +
            "<tr><td><strong>GAP-2</strong></td><td>BRST gauge-fixing / Faddeev–Popov determinant</td>" +
              "<td><span class=\"tag tag-warn\">PROVED CONDITIONAL on Pillar 4</span> (formula); <span class=\"tag tag-warn\">OUTLINE</span> (signature)</td>" +
              "<td>Math160 FP-determinant computed; Math164 proves $\\pi_1(M_{\\rm BCC})=\\{e\\}$ so the standard Berry-phase signature is empty</td>" +
              "<td>Q-2026-04-26-Math164-Higher-form-Berry-topology (#138)</td></tr>" +
            "<tr><td><strong>GAP-3</strong></td><td>SM gauge anomaly cancellation</td>" +
              "<td><span class=\"tag tag-ok\">PROVED CONDITIONAL on Pillar 4</span></td>" +
              "<td>Math157 group-theoretic trace on a single $\\mathrm{SO}(10)$ $\\mathbf{16}$: six anomaly coefficients exact zero, numerically verified</td>" +
              "<td>Pillar 4 sub-task 3 closure</td></tr>" +
            "<tr><td><strong>GAP-4</strong></td><td>Cosmological observable comparison</td>" +
              "<td><span class=\"tag tag-warn\">RESCOPED + PROVISIONAL prediction</span></td>" +
              "<td>Math159 retracts Math151 inflationary $n_s$ as category error; Math172 produces BBN-scenario $\\Omega_{\\rm GW}\\approx 5\\!\\times\\!10^{-15}$ at PTA band, observable by SKA / IPTA-2 (2028–2030)</td>" +
              "<td>Q-2026-04-26-Math168-defect-mass-refinement (#144)</td></tr>" +
            "</tbody>" +
          "</table>" +
          "<p><strong>Critical bottleneck — Pillar 4 $\\mathrm{SO}(10)+\\mathbf{16}$ emergence</strong>. Three of the four gates (GAP-2 formula, GAP-3, GAP-4 indirectly) are conditional on the Pillar-4 emergence being closed at the matter-content level. The 30-turn programme decomposed Pillar 4 sub-task 2 into a mechanically reducible bifurcation, then post-R8 (Math191+192) RESCUED Scenario B.</p>" +
          "<table class=\"sm-table\">" +
            "<thead><tr><th>Pillar 4 sub-task</th><th>Status</th><th>Anchor</th></tr></thead>" +
            "<tbody>" +
            "<tr><td>1 — Fibre-bundle foundation ($\\mathbb{CP}^2$ base, $\\mathrm{SO}(10)/\\mathrm{SU}(5)$ fibre, $c_1=1$)</td>" +
              "<td><span class=\"tag tag-ok\">PROVED CONDITIONAL</span></td>" +
              "<td>Math162 + Math167 (three-patch Čech closure)</td></tr>" +
            "<tr><td>2 — Chiral fermion zero-mode count $\\mathrm{ind}(D_E^c) = 16$</td>" +
              "<td><span class=\"tag tag-ok\">PROVED CONDITIONAL</span></td>" +
              "<td>Math171-AddA: $\\mathrm{ind} = 16 - \\mu$ via canonical complex spin-c (Hirzebruch–Riemann–Roch). Math191+Math192 establish $c_1(\\mathrm{U}(1)_\\chi)=0$ and $c_2(E_{\\rm SU(5)})=0$ → Scenario B → $\\mathrm{ind}=16$.</td></tr>" +
            "<tr><td>3 — Symmetry-breaking chain to $G_{\\rm SM}$</td>" +
              "<td><span class=\"tag tag-warn\">STRONG CLOSURE DRAFT</span></td>" +
              "<td>Math175 algebraic chain $\\mathrm{SO}(10)\\to\\mathrm{SU}(5)\\times\\mathrm{U}(1)_\\chi\\to\\mathrm{SU}(5)\\to G_{\\rm SM}$; BCC geometric origins phenomenological</td></tr>" +
            "</tbody>" +
          "</table>" +
          "<p><strong>Bifurcation-resolution history</strong>: the sub-task 2 bifurcation reduced to two integer-valued tasks, both now closed in Scenario B.</p>" +
          "<ul>" +
            "<li><strong>Task #149b</strong> — determine the $\\mathrm{U}(1)_\\chi$ transition function $\\chi_{ij}$ in the Math162 atlas. <em>Resolved</em>: Math191 → $c_1(\\mathrm{U}(1)_\\chi) = 0$.</li>" +
            "<li><strong>Task #150</strong> — compute the $\\mathrm{SU}(5)$ instanton number $c_2(E_{\\rm SU(5)})$. <em>Resolved</em>: Math192 → $c_2(E_{\\rm SU(5)}) = 0$.</li>" +
          "</ul>" +
          "<p>With both integers zero, <strong>Scenario B</strong> is confirmed; sub-task 2 is PROVED CONDITIONAL on sub-task 3; GAP-2 + GAP-3 unconditional closures unblock once sub-task 3 promotes from STRONG CLOSURE DRAFT to PROVED.</p>" +
          "<p><strong>30-turn audit-discipline scorecard</strong> (CLAUDE.md §6.3.2 cross-turn audit hop):</p>" +
          "<table class=\"sm-table\">" +
            "<thead><tr><th>Round</th><th>Audit verdict</th><th>Catch / miss</th></tr></thead>" +
            "<tbody>" +
            "<tr><td>R1 (Math165)</td><td>ACCEPT WITH MINOR REVISIONS</td><td>Caught Math160 Berry-signature triviality on simply-connected $M_{\\rm BCC}$</td></tr>" +
            "<tr><td>R2 (Math169)</td><td>DOWNGRADE Math166 + DOWNGRADE Math168</td><td>Caught Math166 &quot;index by ansatz&quot; pattern</td></tr>" +
            "<tr><td>R3 (Math173)</td><td>ACCEPT (audit MISSED)</td><td>Failed to catch Math171 §3.3 degree-arithmetic error; recovered via Math171-AddA</td></tr>" +
            "<tr><td>R4 (Math177)</td><td>ACCEPT WITH MAJOR REVISIONS</td><td>Caught Math174 Scenario-A vs Scenario-B bifurcation</td></tr>" +
            "<tr><td>R5 (Math184)</td><td>DOWNGRADE Math181</td><td>Caught Math181 simply-connected-vs-Chern-class conflation</td></tr>" +
            "<tr><td>R6 (dispatcher)</td><td>HONEST UNDER-SPECIFICATION VERDICT</td><td>Math185 identified the genuine atlas gap</td></tr>" +
            "</tbody>" +
          "</table>" +
          "<p><strong>Net 30-turn position (post-R8)</strong>: substantial structural advance with one Stage-1 status promotion (Pillar 4 sub-task 2 → PROVED CONDITIONAL, Scenario B). The audit discipline is mature: 5 catches in 6 rounds, 1 miss recovered at the dispatcher level.</p>" +
          "<p><em>Honest verdict (Math156 §4 + Math190 §6 + Math193 §5)</em>: TECT remains a <strong>Partial TOE candidate</strong>. Its classical sector is strong. Its quantum-completion sector has one weak-but-substantiated proof (GAP-1), one open higher-form-topology question (GAP-2 signature), one closure pending Pillar 4 sub-task 3 (GAP-3 unconditional), and one PROVISIONAL prediction in the Kibble–Zurek branch (GAP-4).</p>"
      }]
    },

    {
      type: "card",
      title: "Stage-3 — external phenomenological qualification",
      blocks: [{
        type: "html",
        content:
          "<p>Stage-3 is a ledger discipline rather than a theorem. Three sub-conditions must each seal:</p>" +
          "<table class=\"sm-table\">" +
            "<thead><tr><th>Sub-condition</th><th>Content</th><th>Status</th></tr></thead>" +
            "<tbody>" +
            "<tr><td>$S_3^{\\rm (reproduce)}$</td><td>Independent reproduction of one Stage-1 / Stage-2 numerical certificate</td><td><span class=\"tag tag-gap\">OPEN</span></td></tr>" +
            "<tr><td>$S_3^{\\rm (predict)}$</td><td>One pre-registered prediction matched to experiment within tolerance</td><td><span class=\"tag tag-warn\">PROVISIONAL via Math172 Kibble–Zurek GW prediction</span> ($\\Omega_{\\rm GW}\\sim 10^{-15}$ at PTA band, observable by SKA 2028–2030)</td></tr>" +
            "<tr><td>$S_3^{\\rm (survive)}$</td><td>One prediction window open $\\geq 1$ year without falsification</td><td><span class=\"tag tag-warn\">GATED</span> on $S_3^{\\rm (predict)}$ sealing</td></tr>" +
            "</tbody>" +
          "</table>" +
          "<p>The TECT cosmology branch was rescoped from inflationary slow-roll (Math151, retracted as a category error in Math159) to Kibble–Zurek quench-driven (Math172). The closest sealing pathway is now the BBN-scenario stochastic GW background prediction, observable by the next-generation pulsar-timing arrays.</p>"
      }]
    },

    {
      type: "card",
      title: "Side-by-side comparison vs other frameworks (compact)",
      blocks: [{
        type: "html",
        content:
          "<p>Compact comparison of TECT against three reference frameworks: the <strong>Standard Model (SM)</strong>, <strong>Superstring / M-theory</strong>, and <strong>Loop Quantum Gravity (LQG)</strong>. The same compact table also appears on the <a href=\"index.html\">Overview</a> page. Status reflects the publicly stated state of each programme as of 2026 spring; entries for non-TECT frameworks are summary-grade and meant for orientation, not adjudication.</p>" +
          "<div class=\"cmp-scroll\"><table class=\"sm-table cmp-table\">" +
            "<thead><tr>" +
              "<th>Axis</th>" +
              "<th class=\"tect-col\">TECT</th>" +
              "<th>Standard Model</th>" +
              "<th>Superstring / M</th>" +
              "<th>Loop Quantum Gravity</th>" +
            "</tr></thead>" +
            "<tbody>" +
            "<tr><td>Foundational axioms</td>" +
                "<td class=\"tect-col\"><strong>2</strong> (A0 BCC condensate with TDGL kinetics; A1 cosmological cooling history $T(t)$); Math195</td>" +
                "<td>~26 parameters + chosen gauge group + 3 generations</td>" +
                "<td>5–10 (10/11-dim spacetime, branes, compactification, flux, SUSY, vacuum)</td>" +
                "<td>4–5 (spin-network kinematics, holonomy/flux algebra, dynamics, semiclassical limit)</td></tr>" +
            "<tr><td>Predicts SM gauge group</td>" +
                "<td class=\"tect-col\"><span class=\"tag tag-ok\">PROVED CONDITIONAL</span> — Math80-AddA + Math162 + Math191/192: $\\mathrm{Stab}_{\\mathrm{SU}(5)}\\,\\mathrm{Gr}(2,5)=G_{\\rm SM}$</td>" +
                "<td><span class=\"tag tag-gap\">No</span> — gauge group postulated</td>" +
                "<td><span class=\"tag tag-partial\">Partial</span> — landscape of vacua</td>" +
                "<td><span class=\"tag tag-gap\">No</span> — gauge content imported</td></tr>" +
            "<tr><td>Predicts gravity</td>" +
                "<td class=\"tect-col\"><span class=\"tag tag-ok\">Yes</span> — emergent spin-2 graviton at 1-loop (Pillar 3 CLOSED@1-loop)</td>" +
                "<td><span class=\"tag tag-gap\">No</span></td>" +
                "<td><span class=\"tag tag-ok\">Yes</span> — closed-string graviton mode</td>" +
                "<td><span class=\"tag tag-ok\">Yes</span> — quantises GR by construction</td></tr>" +
            "<tr><td>Predicts $\\hbar$</td>" +
                "<td class=\"tect-col\"><span class=\"tag tag-warn\">CONDITIONAL (weak)</span> — Math110-AddI: $\\hbar=c^3 a_{\\rm BCC}^2/(16\\pi G)$</td>" +
                "<td><span class=\"tag tag-gap\">No</span> — input constant</td>" +
                "<td><span class=\"tag tag-gap\">No</span></td>" +
                "<td><span class=\"tag tag-gap\">No</span></td></tr>" +
            "<tr><td>Predicts cosmological constant</td>" +
                "<td class=\"tect-col\"><span class=\"tag tag-warn\">PROVED CONDITIONAL</span> — Math58-v7 four-sector cancellation chain (Pillar 11 NEAR-CLOSURE)</td>" +
                "<td><span class=\"tag tag-gap\">No</span></td>" +
                "<td><span class=\"tag tag-gap\">No</span> — landscape predictability</td>" +
                "<td><span class=\"tag tag-gap\">No</span></td></tr>" +
            "<tr><td>Quantum-consistent</td>" +
                "<td class=\"tect-col\"><span class=\"tag tag-partial\">Partial</span> — anomaly cancellation conditional on Pillar 4; BRST FP determinant computed</td>" +
                "<td><span class=\"tag tag-ok\">Yes</span> — by construction</td>" +
                "<td><span class=\"tag tag-ok\">Yes</span> (perturbative)</td>" +
                "<td><span class=\"tag tag-partial\">Partial</span> — kinematics yes, dynamics open</td></tr>" +
            "<tr><td>Falsifiable predictions</td>" +
                "<td class=\"tect-col\"><span class=\"tag tag-warn\">3 pre-registered + Kibble–Zurek GW (Math172)</span></td>" +
                "<td><span class=\"tag tag-ok\">Many</span></td>" +
                "<td><span class=\"tag tag-gap\">Few</span> — energies inaccessible</td>" +
                "<td><span class=\"tag tag-gap\">Few</span> — kinematic mostly</td></tr>" +
            "<tr><td>Empirical agreement (current)</td>" +
                "<td class=\"tect-col\"><span class=\"tag tag-partial\">Partial</span> — classical sector agrees; cosmology rescoped to Kibble–Zurek with PROVISIONAL GW prediction</td>" +
                "<td><span class=\"tag tag-ok\">Excellent</span> within scope</td>" +
                "<td><span class=\"tag tag-gap\">Untested</span></td>" +
                "<td><span class=\"tag tag-gap\">Untested</span></td></tr>" +
            "</tbody>" +
          "</table></div>" +
          "<p><em>Reading the table</em>: TECT's distinguishing claim is axiom-level parameter compression — fewer foundational inputs than the listed alternatives — purchased at the cost of an active Pillar-4 sub-task 3 closure path and an open quantum-consistency closure path.</p>"
      }]
    }
  ]
};
