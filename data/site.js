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

  banners: {
    top:    "",
    bottom: "<div class=\"site-license wrap\">" +
              "<div class=\"footer-profile\">" +
                "<img src=\"assets/TECT_Profile_S.png\" alt=\"TECT\" loading=\"lazy\">" +
              "</div>" +
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
  ],

  github: {
    url:   "https://github.com/TECT-OpenPhysics/TECT",
    label: "TECT on GitHub"
  },

  hero: {
    src:  "assets/TECT_Covers.png",
    alt:  "TECT - Topological Energy Condensate Theory",
    href: "index.html"
  },

  profile: {
    src: "assets/TECT_Profile_S.png",
    alt: "TECT"
  }
};
