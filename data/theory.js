/**
 * @MANUAL_OVERRIDE — hand-curated; generate_website.py will skip this file.
 * theory.js — Theory page: minimal-axiom philosophy + framework outline.
 * 2026-05-06 rev 6: Locked-Parameters card removed (moved to states.js
 * detail); Brazovskii-emergence background card expanded with the
 * universality argument; final "Honest limitations + ongoing closure
 * work" card added with hyperlinks to the Math notes that address each
 * weakness.
 */
window.TECT_THEORY = {
  title: "Theory",
  subtitle: "TECT is a candidate Theory of Everything built on the smallest possible set of foundational axioms — two. After the Math195 reduction, the prior three-axiom list collapses to one physics axiom (A0: a $\\mathbb Z_2$-symmetric continuum order parameter $\\Psi$ governed by the Brazovskii free energy with TDGL relaxational dynamics) and one cosmological axiom (A1: the cooling history $T(t)$). The BCC condensate is not assumed; it is the energetically selected ordered phase of the Brazovskii weak-crystallisation transition, and emerges as a derivation. Every law of physics in TECT scope must follow as a mathematical or thermodynamic necessity from these two inputs.",
  lastUpdated: "2026-05-06",
  blocks: [
    {
      type: "card",
      title: "Why TECT? — the minimal-axiom philosophy",
      blocks: [{ type: "html", content:
        "<p>Modern physics is a confederation of frameworks, each with its own foundational inputs: the Standard Model takes a gauge group and roughly 26 parameters as given; General Relativity takes the equivalence principle and Einstein–Hilbert action as given; GUT candidates take a unifying group as given; string theory takes 10/11-dimensional spacetime, branes, and a compactification scheme as given. The combined input list is large, and most items are postulated rather than derived.</p>" +
        "<p>TECT working hypothesis is that this combined input list is not minimal. It posits that the underlying structure of reality is a single object — a $\\mathbb Z_2$-symmetric continuum order parameter $\\Psi$ at the Brazovskii weak-crystallisation point — and that the framework reproducing the empirical content of the SM, GR, and the cosmological sector ought to require only the smallest set of axioms needed to specify that object plus its cosmological history. After the Math195 axiom-reduction theorem, the current TECT list is <strong>two axioms</strong>:</p>" +
        "<ol>" +
          "<li><strong>A0 — Brazovskii continuum order parameter (physics axiom).</strong> Physical reality is the order parameter $\\Psi:\\mathbb R^3\\to\\mathbb C$ of a $\\mathbb Z_2$-symmetric continuum field whose free energy is the Brazovskii functional $$\\mathcal F[\\Psi]=\\int d^3x\\Big[\\tfrac12\\mu^2|\\Psi|^2+\\tfrac{\\gamma}{2}\\big((\\nabla^2+q_0^2)\\Psi\\big)^2+\\tfrac{\\lambda}{4}|\\Psi|^4\\Big],$$ with locked parameters $(\\mu^2,\\lambda,\\gamma)$ and finite-momentum spectral minimum at $|\\mathbf k|=q_0$, evolving by the universal Halperin–Hohenberg Model-A relaxational dynamics. The TDGL kinetics is <em>not</em> an additional postulate — it is the canonical relaxational law for any non-conserved order parameter, derived in Math195 §3.1. The BCC ordering of the condensate is a derivation from this functional, not an input — see the next two cards.</li>" +
          "<li><strong>A1 — cosmological cooling history (cosmological axiom).</strong> The condensate inherits a monotonic temperature schedule $T(t)$ from a pre-condensation phase, with $T(t)\\to\\infty$ as $t\\to 0^+$ and $T(t)\\to T_{\\rm now}$ as $t\\to t_{\\rm now}$. Math195 §3.2 shows that the Kibble–Zurek-relevant content of the prior &quot;ultra-high-energy initial state&quot; axiom is fixed by the local cooling rate $\\dot T/T$ at the BCC condensation transition; the remainder is a universal Cauchy boundary that requires no separate physical postulate.</li>" +
        "</ol>" +
        "<p>Two axioms is the same structural count as Einstein GR and strictly fewer than the publicly stated input lists of the SM, GUT-class extensions, string theory, or Loop Quantum Gravity. The price of this minimalism is that everything else — gauge group, gravitational action, fermion content, generation count, $\\hbar$, the cosmological constant — must be <em>derived</em>.</p>"
      }]
    },

    {
      type: "card",
      title: "Theoretical background — why the Brazovskii functional is the unique long-wavelength fixed point",
      blocks: [{ type: "html", content:
        "<p>The single most important step in evaluating TECT is understanding that the Brazovskii free energy is not a chosen Lagrangian. It is the unique infrared fixed point of a class of microscopic systems characterised by <em>two competing length scales</em>, and TECT inherits it from a renormalisation-group argument that has been written down independently in at least four physical contexts.</p>" +
        "<p><strong>1. The two-scale frustration.</strong> Consider any continuum order parameter whose effective free-energy density contains a kinetic term that prefers smoothness ($+|\\nabla\\Psi|^2$) and a competing nonlocal interaction (Coulomb-like, dipolar, or fluctuation-induced) that disfavours the homogeneous mode. Long-wavelength fluctuations cost gradient energy; very short wavelengths cost interaction energy. The two penalties balance at a finite wavevector $|\\mathbf k|=q_0\\neq 0$, and any analytic infrared expansion around that minimum produces $$\\mathcal F_{\\rm IR}[\\Psi]\\;\\supset\\;\\tfrac{\\gamma}{2}\\big((\\nabla^2+q_0^2)\\Psi\\big)^2,$$ the Brazovskii (or Swift–Hohenberg) gradient kernel. This kernel is universal: every microscopic Hamiltonian whose dispersion has a single non-degenerate minimum at $|\\mathbf k|=q_0$ produces it after coarse-graining.</p>" +
        "<p><strong>2. Where this functional has been derived from microscopics.</strong> The same Brazovskii / Swift–Hohenberg structure appears, with different physical origins for $q_0$, in:</p>" +
        "<ul>" +
          "<li><em>Rayleigh–Bénard convection</em> (Swift &amp; Hohenberg, <em>Phys. Rev. A</em> <strong>15</strong> 319 (1977)) — $q_0$ is the inverse cell height; derivation from the Boussinesq equations.</li>" +
          "<li><em>Block copolymer microphase separation</em> (Leibler, <em>Macromolecules</em> <strong>13</strong> 1602 (1980); Fredrickson &amp; Helfand, <em>J. Chem. Phys.</em> <strong>87</strong> 697 (1987)) — $q_0$ is set by the polymer statistical segment length; derivation from RPA on the Edwards Hamiltonian.</li>" +
          "<li><em>FFLO / Larkin–Ovchinnikov modulated superconductors</em> (Fulde &amp; Ferrell, <em>Phys. Rev.</em> <strong>135</strong> A550 (1964); Larkin &amp; Ovchinnikov, <em>JETP</em> <strong>20</strong> 762 (1965)) — $q_0$ is set by the Zeeman splitting; derivation from the BCS gap equation in a Pauli-limiting field.</li>" +
          "<li><em>Density-wave instabilities in correlated electron systems</em> (Brazovskii, <em>Sov. Phys. JETP</em> <strong>41</strong> 85 (1975); Hohenberg &amp; Swift, <em>Phys. Rev. E</em> <strong>52</strong> 1828 (1995)) — $q_0$ is set by Fermi-surface nesting; derivation from RPA on the Hubbard-class Hamiltonian.</li>" +
        "</ul>" +
        "<p>In each case the microscopic theory differs, but the long-wavelength theory is the <em>same</em> Brazovskii functional. This is universality in the precise renormalisation-group sense: the microscopic identity of $\\Psi$ is irrelevant to its long-wavelength dynamics once the dispersion has the single-minimum structure.</p>" +
        "<p><strong>3. What TECT adds.</strong> TECT proposes that this universality class also describes the most fundamental level of the physical vacuum. The two competing length scales are then identified with two intrinsic scales of the relativistic vacuum itself — a microscopic UV scale (whose nature is left open at the foundational level, in keeping with axiom minimality) and the BCC modulation length $a_{\\rm BCC}=2\\pi/q_0$. The ground state is the energetically selected ordered phase, which by the analytic Landau-cubic-invariant calculation (next card) is BCC.</p>" +
        "<p><strong>4. Why this is &quot;maximally reasonable&quot; rather than ad hoc.</strong> A genuinely ad hoc theory would specify the microscopic Hamiltonian and reverse-engineer a long-wavelength theory matching observation. TECT does the opposite: it specifies only the universality class — the equivalence class of microscopic theories sharing a finite-momentum spectral minimum — and argues that the correct macroscopic theory must be in that class on universality grounds. The same argument that turns the Hubbard model and the Edwards model and the BCS gap equation into the same Brazovskii functional in their respective contexts is the argument TECT applies to the relativistic vacuum. The minimality is not in the number of microscopic ingredients (which is left underspecified) but in the number of <em>relevant operators</em>, which is two ($\\mu^2,\\lambda$) plus one geometric scale ($q_0$).</p>" +
        "<p><strong>5. Falsifiability of the universality claim.</strong> If the underlying vacuum had two non-degenerate spectral minima, or none, or a continuous-degeneracy ring rather than a sphere, the long-wavelength theory would NOT reduce to Brazovskii, and the BCC ordering derivation would fail. The pre-registered F3 anisotropy test (cosmic isotropy bounds vs the BCC modulation length) is the experimental probe of this universality assumption.</p>"
      }]
    },

    {
      type: "card",
      title: "Origin of the BCC condensate — emergence, not assumption",
      blocks: [{ type: "html", content:
        "<p>Given the Brazovskii functional from the previous card, the BCC ordering is not selected by hand — it is the energetically forced consequence of the Landau cubic invariant, and the selection is rigorous within the single-shell single-mode approximation.</p>" +
        "<p><strong>1. High-temperature precursor.</strong> Above $T_c$ the order parameter sits in a homogeneous, $\\mathbb Z_2$-symmetric (and rotation-invariant) phase $\\langle\\Psi\\rangle=0$. There is no preferred direction, no preferred wavelength, and no broken symmetry. This is the cleanest possible high-energy initial datum.</p>" +
        "<p><strong>2. Brazovskii weak-crystallisation instability.</strong> As $T$ drops past $T_c$, the symmetric phase becomes unstable to <em>any</em> superposition of plane waves with $|\\mathbf k|=q_0$. The triply-degenerate momentum-shell instability — together with the fluctuation-induced cubic coupling that Brazovskii (1975) showed restabilises the transition into a first-order locked branch — is the universal mechanism for weak crystallisation.</p>" +
        "<p><strong>3. Selection of the BCC ordering.</strong> Among the discrete subsets of the momentum shell that produce a real, periodic order parameter, the one minimising the Landau free energy is the set of $12$ momenta whose convex hull is the BCC reciprocal Wigner–Seitz cell. This is the Brazovskii / Hohenberg–Swift selection rule, recovered analytically in <a href=\"papers.html\">Paper-TI-2</a> / Math248: among all single-shell crystallographic candidates compatible with the Landau cubic invariant, BCC minimises $\\mathcal F$. The result is robust against admixture of competing orderings (FCC, simple cubic, lamellar, hexagonal) within the single-shell single-mode approximation; the rigorous global-minimum proof beyond that approximation is tracked in Paper-TI-2 §6 (STRONG-EVIDENCE).</p>" +
        "<p><strong>4. Continuum throughout.</strong> No discrete spacetime, no fixed lattice, no spatial cut-off is introduced. The condensate inherits a periodic ground-state modulation of wavelength $a_{\\rm BCC}=2\\pi/q_0$ from the spontaneously broken translation symmetry, in exact analogy with the smectic-A phase of liquid crystals or the LOFF modulated superconductor. All field equations remain continuum partial differential equations on $\\mathbb R^3$.</p>"
      }]
    },

    {
      type: "card",
      title: "Structural advantages claimed by TECT",
      blocks: [{ type: "html", content:
        "<ul>" +
          "<li><strong>Parameter compression.</strong> The Standard Model takes ~19 free parameters in its core sector plus matter content; TECT condenses them onto 4 classical Brazovskii inputs $(\\mu^2,\\lambda,\\gamma,a_{\\rm BCC})$ + 1 external $\\hbar$. At the axiom level (Math195) the count is 2 vs SM much larger axiomatic input.</li>" +
          "<li><strong>SM gauge group from topology, not by fiat.</strong> Math80-AddA derives $\\mathrm{Stab}_{\\mathrm{SU}(5)}\\,\\mathrm{Gr}(2,5)=G_{\\rm SM}$ from the BCC primitive geometry; the gauge group is a consequence of the order manifold, not an input.</li>" +
          "<li><strong>Gravity as an emergent spin-2 elastic mode.</strong> Pillar 3 (gravity) is CLOSED@1-loop. The graviton is the transverse-traceless elastic mode of the BCC condensate, with $\\kappa_G^2=Y q_0^2$ tying Newton constant to the condensate elastic stiffness.</li>" +
          "<li><strong>Falsifiable from the start.</strong> Three F-candidates (F1 $R_{32}$, F2 $\\Lambda$, F3 BCC anisotropy) are pre-registered with explicit thresholds; the Math172 Kibble–Zurek GW prediction $\\Omega_{\\rm GW}\\sim 10^{-15}$ at PTA band (observable by SKA / IPTA-2 2028–2030) is the first PROVISIONAL Stage-3 prediction.</li>" +
          "<li><strong>Universality, not fitting.</strong> The Brazovskii functional and the BCC selection are both universality-class statements (see prior card and Paper-TI-2), inherited from the same renormalisation-group argument that governs Rayleigh–Bénard, block copolymers, and FFLO superconductors.</li>" +
        "</ul>"
      }]
    },

    {
      type: "card",
      title: "Honest limitations and ongoing closure work",
      blocks: [{ type: "html", content:
        "<p>TECT is a candidate Theory of Everything in active development; it is not a finished theory. Three limitations are load-bearing and disclosed transparently here. For each, the corresponding ongoing-closure work is hyperlinked to the relevant Math note or paper.</p>" +
        "<h3>Limitation 1 — the $\\hbar$ derivation route is not yet independent</h3>" +
        "<p>The foundational identification $$\\hbar\\;=\\;\\frac{c^3 a_{\\rm BCC}^2}{16\\pi G}$$ ties Planck constant to the BCC modulation length and the Newton constant. This is a single derivation route, anchored in the elastic-modulus identification of <a href=\"math-notes.html\">Math110-AddI</a>; an independent matter-side route has not yet been written down. <a href=\"math-notes.html\">Math156</a> §3.1 demoted Pillar 10 from PROVED to PROVED CONDITIONAL (weak) on this ground. Closure work in progress: <a href=\"math-notes.html\">Math163</a> (matter-side stress-tensor route), <a href=\"math-notes.html\">Math196</a> (Berry-curvature route), and <a href=\"states.html\">Pillar 10 status row on the States page</a>.</p>" +
        "<h3>Limitation 2 — Pillar 4 sub-task 3 is in STRONG DRAFT, not unconditional closure</h3>" +
        "<p>The proof that the SM gauge group emerges with the correct three generations is closed at sub-tasks 1 and 2 (PROVED CONDITIONAL via <a href=\"math-notes.html\">Math162</a>+Math167 and <a href=\"math-notes.html\">Math191</a>+<a href=\"math-notes.html\">Math192</a>). Sub-task 3 (residual cohomology integral on the order manifold) remains in the STRONG DRAFT state. Closure work in progress: documented under the active sub-task 3 entry on the <a href=\"states.html\">States page</a> and the open-question registry behind it. GAP-2 and GAP-3 of the quantum gates auto-resolve once sub-task 3 closes.</p>" +
        "<h3>Limitation 3 — the high-energy precursor is postulated, not derived from a deeper layer</h3>" +
        "<p>The $\\mathbb Z_2$-symmetric continuum field at the Brazovskii spectral minimum (axiom A0) is the cleanest possible initial datum we know how to write, but it is still a postulate. TECT does not currently derive A0 from a more fundamental layer; the framework's claim is universality of the long-wavelength theory (the prior &quot;Theoretical background&quot; card), not derivation from nothing. The honest scope of the framework is &quot;Unified Classical Field Theory / Partial TOE&quot; (CLAUDE.md §8 operational classification, post-2026-04-24 audit). Whether A0 admits a deeper derivation remains an open programme; <a href=\"math-notes.html\">Math195</a> reduced the prior three-axiom list to two, which is the best current result on this front.</p>" +
        "<p>The site's <a href=\"toe.html\">TOE page</a> tracks progress against TOE-completion goals; the <a href=\"history.html\">History page</a> records every retraction and audit event in append-only form. No claim on this site is presented as more closed than the underlying Math note actually establishes.</p>"
      }]
    }
  ]
};
