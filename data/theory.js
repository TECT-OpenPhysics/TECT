/**
 * @MANUAL_OVERRIDE — hand-curated; generate_website.py will skip this file.
 * theory.js — Theory page: minimal-axiom philosophy + framework outline.
 *
 * 2026-04-26 rev 3 (hand-curated): Stage-1/2/3 status detail moved to states.js;
 *   per-pillar achievement scorecard + remaining-goals view moved to toe.js;
 *   cross-framework comparison moved to states.js / index.js.
 *
 * 2026-04-28 rev 4 (hand-curated): per user directive, the axiom list
 * is restated in the post-Math195 two-axiom form:
 *   A0 — BCC topological condensate with Brazovskii free energy and
 *        TDGL relaxational dynamics (the prior A1 is absorbed as the
 *        universal Halperin–Hohenberg Model-A kinetics canonically
 *        attached to any Brazovskii order parameter).
 *   A1 — cosmological cooling history T(t) (the prior A2 is reduced
 *        to its KZ-relevant content via Math195; the remainder is a
 *        universal Cauchy boundary).
 * The "Where to go next" navigation card is removed.
 */
window.TECT_THEORY = {
  title: "Theory",
  subtitle: "TECT is a candidate Theory of Everything built on the smallest possible set of foundational axioms — two. After the Math195 reduction, the prior three-axiom list collapses to one physics axiom (A0: the Brazovskii BCC topological condensate with TDGL relaxational dynamics) and one cosmological axiom (A1: the cooling history $T(t)$). Every law of physics in TECT's scope must follow as a mathematical or thermodynamic necessity from these two inputs, with no external symmetry imposed and no hand-tuned parameters beyond those locked by the Brazovskii free energy.",
  lastUpdated: "2026-04-28",

  blocks: [
    {
      type: "card",
      title: "Why TECT? — the minimal-axiom philosophy",
      blocks: [{
        type: "html",
        content:
          "<p>Modern physics is a confederation of frameworks, each with its own foundational inputs: the Standard Model takes a gauge group and roughly 26 parameters as given; General Relativity takes the equivalence principle and Einstein–Hilbert action as given; GUT candidates take a unifying group as given; string theory takes 10/11-dimensional spacetime, branes, and a compactification scheme as given. The combined input list is large, and most items are postulated rather than derived.</p>" +
          "<p>TECT's working hypothesis is that this combined input list is not minimal. It posits that the underlying structure of reality is a single object — a 3-D BCC topological condensate — and that the framework reproducing the empirical content of the SM, GR, and the cosmological sector ought to require only the smallest set of axioms needed to specify that object plus its cosmological history. After the Math195 axiom-reduction theorem, the current TECT list is <strong>two axioms</strong>:</p>" +
          "<ol>" +
            "<li><strong>A0 — BCC topological condensate (physics axiom).</strong> Physical reality is the order parameter $\\Psi:\\mathbb R^3\\to\\mathbb C$ of a three-dimensional body-centred-cubic topological condensate, governed by the Brazovskii free energy " +
              "$$\\mathcal F[\\Psi]=\\int d^3x\\Big[\\tfrac12\\mu^2|\\Psi|^2+\\tfrac{\\gamma}{2}\\big((\\nabla^2+q_0^2)\\Psi\\big)^2+\\tfrac{\\lambda}{4}|\\Psi|^4\\Big]$$ " +
              "with locked parameters $(\\mu^2,\\lambda,\\gamma)$ and BCC reciprocal-lattice momentum $q_0$, evolving by the universal Halperin–Hohenberg Model-A relaxational dynamics " +
              "$$\\partial_t\\Psi=-\\frac{\\delta\\mathcal F}{\\delta\\Psi^*}+\\eta,\\qquad \\langle\\eta(x,t)\\eta^*(x',t')\\rangle=2k_BT\\,\\delta^{(3)}(x-x')\\delta(t-t').$$ " +
              "Note: the time-dependent Ginzburg–Landau (TDGL) kinetics that appeared as a separate axiom in the previous restatement is <em>not</em> an additional postulate — it is the canonical relaxational law for any non-conserved Brazovskii order parameter, derived in Math195 §3.1 from H-theorem + locality + the absence of conserved currents on $\\Psi$. We therefore bundle it into A0.</li>" +
            "<li><strong>A1 — cosmological cooling history (cosmological axiom).</strong> The condensate inherits a monotonic temperature schedule $T(t)$ from a pre-condensation phase, with $T(t)\\to\\infty$ as $t\\to 0^+$ and $T(t)\\to T_{\\rm now}$ as $t\\to t_{\\rm now}$. Math195 §3.2 shows that the Kibble–Zurek-relevant content of the prior &quot;ultra-high-energy initial state&quot; axiom is fixed by the local cooling rate $\\dot T/T$ at the BCC condensation transition; the remainder is a universal Cauchy boundary that requires no separate physical postulate. This axiom plays the same structural role as the cosmological boundary condition in Einstein GR.</li>" +
          "</ol>" +
          "<p>Two axioms is the same structural count as Einstein GR (one geometric postulate + one cosmological boundary condition) and strictly fewer than the publicly stated input lists of the Standard Model, GUT-class extensions, string theory, or Loop Quantum Gravity. The States page makes the side-by-side comparison explicit. The price of this minimalism is that everything else — gauge group, gravitational action, fermion content, generation count, $\\hbar$, the cosmological constant — must be <em>derived</em>, and the derivation must survive both internal mathematical consistency and external empirical contact. Roughly half of those derivations are now in PROVED territory; the rest are explicitly tracked as open problems on the TOE page.</p>"
      }]
    },

    {
      type: "card",
      title: "Structural advantages claimed by TECT",
      blocks: [{
        type: "html",
        content:
          "<ul>" +
            "<li><strong>Parameter compression.</strong> The Standard Model takes ~19 free parameters in its core sector plus matter content; TECT condenses them onto 4 classical Brazovskii inputs $(\\mu^2,\\lambda,\\gamma,a_{\\rm BCC})$ + 1 external $\\hbar$, a compression ratio of $4.75\\times$ (or $6.3\\times$ if $a_{\\rm BCC}$ derivability holds). At the axiom level (Math195) the count is 2 vs SM's much larger axiomatic input. Stage-2-B captures this formally.</li>" +
            "<li><strong>SM gauge group from topology, not by fiat.</strong> Math80-AddA derives $\\mathrm{Stab}_{\\mathrm{SU}(5)}\\,\\mathrm{Gr}(2,5)=G_{\\rm SM}$ at theorem level from the BCC primitive geometry; the gauge group is a consequence of the order manifold rather than an input. Pillar 4 (gauge interactions) sub-tasks 1 and 2 are now PROVED CONDITIONAL (Math162+Math167 and Math191+Math192).</li>" +
            "<li><strong>Gravity as an emergent spin-2 elastic mode.</strong> Pillar 3 (gravity) is CLOSED@1-loop. The graviton is the transverse-traceless elastic mode of the BCC condensate, with $\\kappa_G^2=Y q_0^2$ tying Newton's constant to the condensate's elastic stiffness.</li>" +
            "<li><strong>Falsifiable from the start.</strong> Three F-candidates (F1 $R_{32}$, F2 $\\Lambda$, F3 BCC anisotropy) are pre-registered with explicit thresholds. The Math172 Kibble–Zurek GW prediction $\\Omega_{\\rm GW}\\sim 10^{-15}$ at PTA band (observable by SKA / IPTA-2 2028–2030) is the first PROVISIONAL Stage-3 prediction.</li>" +
            "<li><strong>One scope-limit, transparently disclosed.</strong> $\\hbar$ has not yet been derived from a route independent of the elastic-modulus identification; Math156 §3.1 demoted Pillar 10 from PROVED to PROVED CONDITIONAL (weak) for this reason. A matter-side third route is the explicit critical task.</li>" +
          "</ul>"
      }]
    },

    {
      type: "card",
      title: "Brazovskii regime — TECT is the inverse superconductor",
      blocks: [{
        type: "html",
        content:
          "<p>Where a Ginzburg–Landau superconductor condenses through a second-order instability at $r=0$ with $\\lambda>0$, TECT condenses on the <strong>Brazovskii first-order locked branch</strong> with</p>" +
          "<p>$$\\lambda<0,\\qquad \\gamma>0\\text{ sizeable},\\qquad \\phi_0^2=-\\tfrac{4\\lambda}{15\\gamma}$$</p>" +
          "<p>restabilised by fluctuation-induced cubic coupling near a shell $|\\mathbf k|=q_0$. The order parameter acquires its finite amplitude discontinuously at the locked branch; this discontinuity is what supplies the topological structure that downstream pillars exploit.</p>"
      }]
    },

    {
      type: "card",
      title: "Locked parameters (current operating point)",
      blocks: [{
        type: "html",
        content:
          "<table>" +
            "<thead><tr><th>Quantity</th><th>Value</th><th>Origin</th></tr></thead>" +
            "<tbody>" +
              "<tr><td>$\\mu^2$</td><td>$5\\times 10^{-3}$</td><td>v2.4 continuation target (post-2026-04-21)</td></tr>" +
              "<tr><td>$\\lambda$</td><td>$-0.43$</td><td>Brazovskii lock equation (Math38)</td></tr>" +
              "<tr><td>$\\gamma$</td><td>$1.62$</td><td>Brazovskii three-equation matching</td></tr>" +
              "<tr><td>$q_0^{\\mathrm{phys}}$</td><td>$0.6801747616$</td><td>BCC reciprocal-lattice geometric value</td></tr>" +
              "<tr><td>$L_{\\mathrm{BCC}}^{(7)}$</td><td>$2\\pi\\sqrt{2}\\cdot 7\\approx 62.20036$</td><td>BCC-commensurate box length (Math74-AddC)</td></tr>" +
              "<tr><td>$R_C^{\\mathrm{global}}$</td><td>$1.141358\\times 10^{-2}$</td><td>Brazovskii Maxwell-equal-area threshold (Math56)</td></tr>" +
            "</tbody>" +
          "</table>" +
          "<p>First clean Pillar-1 numerical anchor (Math82-Addendum-F, 2026-04-24): $m^{*2}_{\\rm num}(N=32,\\;L=L_{\\rm BCC}^{(7)},\\;\\mu^2=+5\\times 10^{-3})=+4.247\\times 10^{-2}$ at a true local minimum ($\\lambda_{\\min}>0$), 14 Newton iterations.</p>"
      }]
    }
  ]
};
