// AUTO-GENERATED v0.3 page 8/8 — 2026-05-01 23:27 UTC
window.TECT_HISTORY_PAGE_008 = {
  title: "History (page 8 of 8)",
  subtitle: "Chronological CHANGELOG mirror — auto-generated.",
  lastUpdated: "2026-05-01 (auto)",
  pagination: {"page": 8, "total": 8, "newer": "history-page-007.html", "older": null, "archiveIndex": "history-archive-index.html"},
  blocks: [
    { type: "html", content: "<div class=\"pagination-nav\"><a href=\"history-page-007.html\">&larr; Newer</a> &middot; Page 8 / 8 &middot; <a href=\"history-archive-index.html\">archive index</a></div>" },
    { type: "timeline", items: [
        {
          date: "2026-04-22",
          title: "[continuation_mu2_v25 TypeError fix + honest skeleton-mode status (v2.5.3)]",
          body: "**Trigger**: With the $\\texttt{Tools/}\\to\\texttt{tools/}$ rename (v2.5.1 plumbing) and the UTF-8 pin (v2.5.2) in place, Stage $[4/4]$ of `run_v25_diagnostic.ps1` finally reached the Newton loop. `[Point 1/6]$ $\\mu^{2}=-1.000000\\mathrm{e}{+00}$ aborted immediately with `ERROR: ContinuationPoint.__init__() missing 1 required positional argument: 'converged'` and the handoff script then mis-reported `*** v2.5 DIAGNOSTIC: PASS ***` because Python exited $0$. A run with *zero* real Newton steps thus looked indistinguishable from a fully-converged 6-point sweep."
        },
        {
          date: "2026-04-22",
          title: "[continuation_mu2_v25 UTF-8 locale hardening (v2.5.2)]",
          body: "**Trigger**: After the user-side `Tools/` → `tools/` rename landed, the v2.5.1 diagnostic finally reached Stage [4/4] and the 6-point sweep actually started. The Math56 constants self-check passed; however `python PDE/continuation_mu2_v25.py` then aborted with `UnicodeDecodeError: 'cp949' codec can't decode byte 0xe2 in position 971: illegal multibyte sequence` at `base_params = json.load(f)`."
        },
        {
          date: "2026-04-22",
          title: "[Root-cause resolution: `tools/` ↔ `Tools/` case collision on Windows/Python 3.12]",
          body: "**Trigger**: While static-smoke-testing the v2.5.1 `sys.path` fix, the in-sandbox import `from tools.check_jacobian_symmetry import probe_symmetry` *still* failed with `ModuleNotFoundError`, even though both `tools/` and `tools/__init__.py` were confirmed on disk. Escalated to root-cause investigation."
        },
        {
          date: "2026-04-22",
          title: "[continuation_mu2_v25 symmetry-probe import fix + run_v25_diagnostic.ps1 CLI contract (v2.5.1)]",
          body: "**Trigger**: First full-path local run of `scripts/run_v25_diagnostic.ps1` (after the v1.2 BZ-preconditioner and v1.2 self-test patches) reached Stage [3/4] with all three self-tests green, but Stage [4/4] aborted at `python PDE/continuation_mu2_v25.py ...` with exit code $2$ and two distinct defects: 1. `WARNING: check_jacobian_symmetry not found.` — Math63 §2A symmetry-probe-driven solver routing was silently bypassed, degrading v2.5 to a plain FGMRES solver (specification deviation). 2. `continuation_mu2_v25.py: error: unrecognized arguments: --mu2_list -1.0,-0.8,-0.6,-0.4,-0.2,-0.1` — caller/callee CLI contract mismatch."
        },
        {
          date: "2026-04-22",
          title: "[check_jacobian_symmetry _self_test backend-coherence correction (v1.2)]",
          body: "**Trigger**: First run of the v1.1 self-test via `python tools\\check_jacobian_symmetry.py --selftest` raised `TypeError: unsupported operand type(s) for @: 'numpy.ndarray' and 'Tensor'` at Case 1."
        },
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
    { type: "html", content: "<div class=\"pagination-nav\"><a href=\"history-page-007.html\">&larr; Newer</a> &middot; Page 8 / 8 &middot; <a href=\"history-archive-index.html\">archive index</a></div>" }
  ]
};