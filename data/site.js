/**
 * @MANUAL_OVERRIDE — hand-curated; generate_website.py will skip this file.
 * site.js — Shared site-level data (brand, navigation, footer).
 * Loaded by every page before the renderer.
 */
window.TECT_SITE = {
  brand: {
    name: "TECT",
    sub:  "Topological Energy Condensate Theory"
  },

  /**
   * banners — site-wide top/bottom banner slots.
   * Set html to "" or null to disable a slot.
   * Change once here → reflected on every page.
   *
   * 2026-04-26: bottom slot carries the Open Physics Independent Research
   * tag and the non-commercial copyright line, applied site-wide.
   */
  banners: {
    top:    "",
    bottom: "<div class=\"site-license wrap\">" +
              "<p class=\"site-license-line\"><strong>Open Physics Independent Research</strong></p>" +
              "<p class=\"site-license-line muted\">" +
                "© 2024–2026 Jusang Lee. The TECT framework, theorem notes, code, and " +
                "site content are released under the " +
                "<a href=\"https://creativecommons.org/licenses/by-nc-sa/4.0/\" rel=\"license noopener\" target=\"_blank\">" +
                "Creative Commons Attribution–NonCommercial–ShareAlike 4.0 International (CC&nbsp;BY-NC-SA&nbsp;4.0)" +
                "</a> licence. Commercial use is not permitted." +
              "</p>" +
            "</div>"
  },

  /*
   * Navigation order (2026-04-26 publish-readiness revision, rev 3 — user directive):
   *
   *   Overview → Theory → States → Papers → TOE → Notes → Code → Results → History
   *
   * Reader flow:
   *   • Overview — public-facing entry, brief description + latest snapshot.
   *   • Theory   — minimal-axiom philosophy, full goal, detailed framework.
   *   • States   — S1/S2/S3 qualification predicates + comparison vs other theories.
   *   • Papers   — one per Pillar + cosmic-origin proof, with TOE/GUT/SM/QCT/GR tags.
   *   • TOE      — what TECT has achieved vs other TOE candidates + remaining goals.
   *   • Notes    — proof-level Math notes (Math01..Math157).
   *   • Code     — implementation modules.
   *   • Results  — numerical run outputs.
   *   • History  — chronological timeline + status-ledger pointers (Records absorbed).
   *
   * Change rev 2 → rev 3 (2026-04-26):
   *   • Inserted States between Theory and Papers (carries S1/S2/S3 +
   *     comparison table previously in Theory; Causal Set Theory excluded).
   *   • Moved Papers to position after States and before TOE.
   *   • Records merged into History (records.html keeps a redirect note).
   *   • Theory page slimmed to minimal-axiom philosophy + advantages.
   *   • TOE page repurposed to comparison + remaining goals.
   *   • Site-wide footer banner with non-commercial CC BY-NC-SA 4.0 added.
   */
  nav: [
    { id: "index",      label: "Overview", href: "index.html" },
    { id: "theory",     label: "Theory",   href: "theory.html" },
    { id: "states",     label: "States",   href: "states.html" },
    { id: "papers",     label: "Papers",   href: "papers.html" },
    { id: "toe",        label: "TOE",      href: "toe.html" },
    { id: "math-notes", label: "Notes",    href: "math-notes.html" },
    { id: "code",       label: "Code",     href: "code.html" },
    { id: "results",    label: "Results",  href: "results.html" },
    { id: "history",    label: "History",  href: "history.html" }
  ]
};
