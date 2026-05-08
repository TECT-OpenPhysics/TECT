// AUTO-GENERATED v0.3 page 9/9 — 2026-05-08 07:32 UTC
window.TECT_HISTORY_PAGE_009 = {
  title: "History (page 9 of 9)",
  subtitle: "Chronological CHANGELOG mirror — auto-generated.",
  lastUpdated: "2026-05-08 (auto)",
  pagination: {"page": 9, "total": 9, "newer": "history-page-008.html", "older": null, "archiveIndex": "history-archive-index.html"},
  blocks: [
    { type: "html", content: "<div class=\"pagination-nav\"><a href=\"history-page-008.html\">&larr; Newer</a> &middot; Page 9 / 9 &middot; <a href=\"history-archive-index.html\">archive index</a></div>" },
    { type: "timeline", items: [
        {
          date: "2026-04-22",
          title: "[tools namespace-package fix + check_jacobian_symmetry --selftest — v2.5 diagnostic stage [3/4] unblocked]",
          body: "**Trigger**: Second local run of `scripts/run_v25_diagnostic.ps1` (commit `badd11d`, after the v1.2 BZ-preconditioner patch): stage [2/4] passes cleanly, stage [3/4] fails with `ModuleNotFoundError: No module named 'tools'` on `python -m tools.check_jacobian_symmetry --selftest`, even though the sibling call `python -m PDE.bz_preconditioner` in the same stage succeeds."
        },
        {
          date: "2026-04-22",
          title: "[bz_preconditioner scaling self-test — two-step correction to an upper-bound-only regression check]",
          body: "**Trigger (v1.1)**: First local diagnostic run (R-2026-04-22-001 launch, commit `badd11d`) failed the O(N log N) scaling assertion at step [2/4] of `scripts/run_v25_diagnostic.ps1`."
        },
        {
          date: "2026-04-22",
          title: "[Theory-currency audit on v2.5 solver bundle — 2 pre-existing assertion defects repaired; MU2_TARGET/Q0_PHYSICAL surfaced as explicit constants]",
          body: "**Trigger**: Standing rule `feedback_tect_theory_currency.md` — every new solver bundle must be audited against the current authoritative theory stack before production use. The v2.5 Math63 solver was scheduled for its first diagnostic run."
        },
        {
          date: "2026-04-22",
          title: "[Newton-Krylov v2.5 solver redesign (Math63) sealed; diagnostic pending local execution]",
          body: "**Trigger**: Failure manifest R-2026-04-21-002 (v2.4 continuation failure at μ²=-1.0) — inner GMRES saturates at tCG=15000 for Newton iter ≥5, ρ_lin≈0.6, η_EW locks at 0.5. Root cause: unpreconditioned GMRES cannot resolve Brazovskii ill-conditioning (κ≈1000 at shell |**k**|=q₀)."
        },
        {
          date: "2026-04-21",
          title: "[Math61 Stage-2-E falsifiability pre-registration sealed; Task #54 PyTorch blocker]",
          body: "**Trigger**: Autonomous two-objective session (user directive, Korean, 2026-04-21): (Objective 1) seal Math61 pre-registration for Stage-2-E $G_E$ gate closure; (Objective 2) execute Math55 continuation Task #54 to $\\mu^2_{\\rm target}=5\\times 10^{-3}$."
        }
      ]
    },
    { type: "html", content: "<div class=\"pagination-nav\"><a href=\"history-page-008.html\">&larr; Newer</a> &middot; Page 9 / 9 &middot; <a href=\"history-archive-index.html\">archive index</a></div>" }
  ]
};