/**
 * @MANUAL_OVERRIDE — hand-curated; generate_website.py will skip this file.
 * index.js — Overview page: brief description + latest-state snapshot.
 * 2026-05-06 rev 5: emergent-BCC paragraph inserted; lattice vocabulary cleaned.
 */
window.TECT_INDEX = {
  title: "Topological Energy Condensate Theory",
  subtitle: "A candidate Theory of Everything built on an effectively two-axiom foundation (Math195): one physics axiom — a $\\mathbb Z_2$-symmetric continuum order parameter $\\Psi$ at the Brazovskii weak-crystallisation point — and one cosmological axiom (the cooling history $T(t)$). The BCC condensate emerges as the energetically selected ordered phase of that universality class; it is a derivation, not an assumption. Every law of physics in scope must follow as a mathematical or thermodynamic necessity from these two inputs.",
  lastUpdated: "2026-05-06",
  blocks: [
    {
      type: "card",
      title: "What is TECT?",
      blocks: [{ type: "html", content:
        "<p><strong>TECT</strong> proposes that the Standard Model, General Relativity, and the quantum and cosmological structure of nature all emerge as low-energy consequences of a single object: the order parameter $\\Psi$ of an emergent three-dimensional BCC topological condensate, governed by the Brazovskii free energy $\\mathcal F[\\Psi]$ on its first-order locked branch. Particles are defect excitations of the condensate, gauge fields are Berry connections on the emergent band structure, gravity is a long-wavelength elastic response, and quantum mechanics is the thermodynamic language of fluctuations around the locked vacuum.</p>" +
        "<p>The framework distinguishing claim is <strong>axiom minimality</strong>: after the Math195 reduction, two foundational axioms (one physics + one cosmological), against the much larger publicly stated input lists of SM, GR, GUT, String, LQG, and Wolfram Physics. The price of this minimalism is that essentially every empirical observation must be <em>derived</em> rather than postulated.</p>" +
        "<p>The BCC ordering itself is a <strong>derivation</strong>, not an assumption. TECT postulates only a $\\mathbb Z_2$-symmetric continuum field with a Brazovskii spectral minimum on the shell $|\\mathbf k|=q_0$; the BCC condensate emerges as the energetically selected ordered phase of that universality class — the first-order weak-crystallisation outcome that Brazovskii (1975) showed is the most generic instability of a symmetric continuum order parameter with a finite-momentum minimum. The Theory page makes this emergence explicit. The framework design principle is &quot;minimum assumption + maximally reasonable initial datum&quot;, never <em>ad hoc</em> fitting.</p>" +
        "<p>This site presents TECT <em>as it actually stands</em>. Proved parts are clearly marked as proved, conditional parts as conditional, retracted parts as retracted. Every status claim links to its evidence file in <code>Docs/math/</code> and every numerical result carries a unique $R$-tag tied to a code fingerprint. The append-only <a href=\"history.html\">History</a> page records every retraction.</p>"
      }]
    },
    {
      type: "card",
      title: "Latest state snapshot (2026-04-27)",
      blocks: [{ type: "html", content:
        "<p><strong>Headline</strong>: TECT remains a Partial TOE candidate. Classical sector strong; quantum-completion sector strengthening but not sealed. Pillar 4 sub-task 2 is now PROVED CONDITIONAL (Scenario B confirmed via Math191+Math192).</p>" +
        "<table class=\"sm-table\">" +
          "<thead><tr><th>Predicate</th><th>State</th><th>Critical task</th></tr></thead>" +
          "<tbody>" +
            "<tr><td>$S_1$ — eleven pillars</td><td><span class=\"tag tag-partial\">PARTIAL</span></td><td>Pillar 4 sub-tasks 1 + 2 PROVED CONDITIONAL; sub-task 3 STRONG DRAFT.</td></tr>" +
            "<tr><td>$S_2$ — Global Closure + 4 quantum gates</td><td><span class=\"tag tag-partial\">PARTIAL</span></td><td>GAP-2 + GAP-3 unconditional unblock once Pillar 4 sub-task 3 closes.</td></tr>" +
            "<tr><td>$S_3$ — external phenomenology</td><td><span class=\"tag tag-warn\">PROVISIONAL prediction</span></td><td>Math172 Kibble–Zurek GW $\\Omega_{\\rm GW}\\sim 10^{-15}$ at PTA, observable by SKA 2028–2030.</td></tr>" +
          "</tbody>" +
        "</table>" +
        "<p><strong>Most recent advances</strong>:</p>" +
        "<ul>" +
          "<li><code>Math157</code> — rigorous SO(10) $\\mathbf{16}$ anomaly cancellation via group-theoretic trace.</li>" +
          "<li><code>Math171-AddA</code> — corrected Hirzebruch–Riemann–Roch formula $\\mathrm{ind}(D_E^c) = 16 - \\mu$.</li>" +
          "<li><code>Math191 + Math192</code> — Pillar 4 sub-task 2 RESCUED via Scenario B.</li>" +
          "<li><code>Math194</code> — BCC uniqueness PROVED among 9 crystallographic competitors.</li>" +
          "<li><code>Math195</code> — A2 axiom-reduction theorem; effective TECT axiom count = 2.</li>" +
        "</ul>" +
        "<p>For the full quantum-theory proof-status table see <a href=\"status.html\">Status</a>.</p>"
      }]
    },
    {
      type: "card",
      title: "Comparison vs other candidate frameworks (compact)",
      blocks: [{ type: "html", content:
        "<p>One-glance positioning of TECT against three reference frameworks: the <strong>Standard Model (SM)</strong>, <strong>Superstring / M-theory</strong>, and <strong>Loop Quantum Gravity (LQG)</strong>. &quot;Predicts&quot; means the framework derives the listed item from its axioms rather than postulating it externally.</p>" +
        "<div class=\"cmp-scroll\"><table class=\"sm-table cmp-table\">" +
          "<thead><tr>" +
            "<th>Axis</th>" +
            "<th class=\"tect-col\">TECT</th>" +
            "<th>Standard Model</th>" +
            "<th>Superstring / M</th>" +
            "<th>Loop Quantum Gravity</th>" +
          "</tr></thead>" +
          "<tbody>" +
            "<tr>" +
              "<td>Foundational axioms</td>" +
              "<td class=\"tect-col\"><strong>2</strong> ($\\mathbb Z_2$-symmetric Brazovskii continuum + cooling history $T(t)$); BCC ordering derived; Math195</td>" +
              "<td>~26 parameters + chosen gauge group + 3 generations</td>" +
              "<td>5–10 (10/11-dim spacetime, branes, compactification, flux, SUSY, vacuum)</td>" +
              "<td>4–5 (spin-network kinematics, holonomy/flux algebra, dynamics, semiclassical limit)</td>" +
            "</tr>" +
            "<tr>" +
              "<td>Predicts SM gauge group</td>" +
              "<td class=\"tect-col\"><span class=\"tag tag-ok\">PROVED CONDITIONAL</span> — Math80-AddA + Math162 + Math191/192</td>" +
              "<td><span class=\"tag tag-gap\">No</span> — postulated</td>" +
              "<td><span class=\"tag tag-partial\">Landscape</span> — no unique selection</td>" +
              "<td><span class=\"tag tag-gap\">No</span> — gauge content imported</td>" +
            "</tr>" +
            "<tr>" +
              "<td>Predicts gravity</td>" +
              "<td class=\"tect-col\"><span class=\"tag tag-ok\">Yes</span> — emergent spin-2 graviton (Pillar 3 CLOSED@1-loop)</td>" +
              "<td><span class=\"tag tag-gap\">No</span></td>" +
              "<td><span class=\"tag tag-ok\">Yes</span> — closed-string graviton mode</td>" +
              "<td><span class=\"tag tag-ok\">Yes</span> — quantises GR by construction</td>" +
            "</tr>" +
            "<tr>" +
              "<td>Predicts $\\hbar$</td>" +
              "<td class=\"tect-col\"><span class=\"tag tag-warn\">CONDITIONAL</span> — $\\hbar = c^3 a_{\\rm BCC}^2/(16\\pi G)$ (Math110-AddI)</td>" +
              "<td><span class=\"tag tag-gap\">No</span></td>" +
              "<td><span class=\"tag tag-gap\">No</span></td>" +
              "<td><span class=\"tag tag-gap\">No</span></td>" +
            "</tr>" +
            "<tr>" +
              "<td>Predicts $\\Lambda$</td>" +
              "<td class=\"tect-col\"><span class=\"tag tag-warn\">CONDITIONAL</span> — Math58-v7 four-sector cancellation</td>" +
              "<td><span class=\"tag tag-gap\">No</span></td>" +
              "<td><span class=\"tag tag-gap\">No</span></td>" +
              "<td><span class=\"tag tag-gap\">No</span></td>" +
            "</tr>" +
            "<tr>" +
              "<td>Quantum-consistent</td>" +
              "<td class=\"tect-col\"><span class=\"tag tag-partial\">Partial</span> — anomaly cancellation conditional on Pillar 4</td>" +
              "<td><span class=\"tag tag-ok\">Yes</span></td>" +
              "<td><span class=\"tag tag-ok\">Yes</span> (perturbative)</td>" +
              "<td><span class=\"tag tag-partial\">Partial</span></td>" +
            "</tr>" +
            "<tr>" +
              "<td>Falsifiable predictions</td>" +
              "<td class=\"tect-col\"><span class=\"tag tag-warn\">3 pre-registered + KZ GW</span> (Math172)</td>" +
              "<td><span class=\"tag tag-ok\">Many</span></td>" +
              "<td><span class=\"tag tag-gap\">Few</span></td>" +
              "<td><span class=\"tag tag-gap\">Few</span></td>" +
            "</tr>" +
            "<tr>" +
              "<td>Empirical agreement</td>" +
              "<td class=\"tect-col\"><span class=\"tag tag-partial\">Partial</span> — classical sector agrees</td>" +
              "<td><span class=\"tag tag-ok\">Excellent</span> within scope</td>" +
              "<td><span class=\"tag tag-gap\">Untested</span></td>" +
              "<td><span class=\"tag tag-gap\">Untested</span></td>" +
            "</tr>" +
          "</tbody>" +
        "</table></div>" +
        "<p><em>Reading the table</em>: TECT distinguishing claim is parameter compression — the smallest published foundational input list among comparable candidates.</p>"
      }]
    }
  ]
};
