// AUTO-GENERATED v0.3 page 9/9 — 2026-05-08 16:34 UTC
window.TECT_HISTORY = {
  title: "History (page 9 of 9)",
  subtitle: "Chronological CHANGELOG mirror — auto-generated.",
  lastUpdated: "2026-05-08 (auto)",
  pagination: {"page": 9, "total": 9, "newer": null, "older": "history/page-008.html", "archiveIndex": "history-archive-index.html"},
  blocks: [
    { type: "html", content: "<div class=\"pagination-nav\">Page 9 / 9 &middot; <a href=\"history/page-008.html\">Older &rarr;</a></div>" },
    { type: "timeline", items: [
        {
          date: "2026-05-08",
          title: "[Infrastructure + Policy] Math353-AddG: v3 mirror tightening pass (paste-ready/.pdf/pde-init/site-assets-subdirs eliminated)",
          body: "**Root cause analysis**: - (1) `Docs/math/paste-ready-archive/` was in exclude_directories_local but apply_rename matched longest-prefix `Docs/math` first → renamed → never reached exclude check. Logic gap. - (2) `Docs/math/*.pdf` had no filter; passes_subtree_allowlist default-passed everything in note/. - (3) exclude_pde_pattern lacked __init__, .json, RESULT_TEMPLATE.md. - (4) `site_exclude_dirs_local` was missing `Website/assets/{code, code-old, manual, runs, policy, status, docs}/` (only had math, papers, Website/math)."
        },
        {
          date: "2026-05-08",
          title: "[Infrastructure + Policy] Math353-AddF: v3 mirror cleanup (pde operational + paper flatten + site/assets minimisation + auto-docs disabled)",
          body: "**Cleanups applied** (mirror.json v3.5): - (a) `exclude_pde_pattern`: regex matching audit/check/run_/pipeline/version/manual_extrapolation/parallel/sweep operational scripts in Codes/pde/. 11 operational files excluded; theory PDE solvers (continuation_mu2*, bz_*, tect_*, math46/49/56_*, projector_*, dirac_index_bcc, intervalley_extractor, etc.) pass through. - (b) `v3_disable_auto_docs=true`: github_sync_curate.py v3 mode skips Github/docs/{KEY_RESULTS,NAVIGATION,POLICIES_INDEX}.md generation. _v3_prune expected set updated. - (c) `Docs/math/paste-ready-archive/` added to exclude_directories_local. note/paste-ready-archive subdir not mirrored. - (d) `paper_flatten_pdf_only=true`: Docs/papers/<subdir>/<paper-id>/<paper-id>.pdf → paper/<paper-id>.pdf (top-level flatten). All non-PDF paper-internal files (.tex, .bib, figures) excluded. - (e) site/assets/ exclusions extended: `Website/assets/{status, docs}/` directory exclusions; `Website/assets/{CHANGELOG, CLAUDE, NAVIGATION}.md` + `TECT_*.png` file exclusions. site/assets/{code, code-old, manual, runs, policy, math, papers}/ already excluded (prior commits). - Also: `Docs/papers/{PAPERS_STATUS_REGISTRY, PAPERS_TRACK_PLAN}.md` exclu"
        },
        {
          date: "2026-05-08",
          title: "[Infrastructure + Policy] Math353-AddD r3 + AddE: v3 mirror policy + cutover (theory-only mirror activated)",
          body: "**Theory tags**: `Math353-AddD-Theory-Only-Mirror-Restructure-2026-05-08`, `Math353-AddE-v3-Cutover-2026-05-08` **Trigger**: operator directive 2026-05-08 (5 clarifications): root structure (note/paper/code/status/site); code/ = pde+supplementary+manual; site/math + assets duplicates removed; Old papers + operational MDs excluded; runs/ disabled (Math notes embed key results inline)."
        },
        {
          date: "2026-05-08",
          title: "[Infrastructure + Policy] Math353-AddC: B-ε path-resolution check + C-γ narrative sweep + C-β/δ documentation correction",
          body: "**Theory tag**: `Math353-AddC-Phase-B-Epsilon-and-C-Gamma-Plus-Documentation-Correction-2026-05-08` **Type**: Implementation report addendum (CLAUDE.md §4.3). **Trigger**: operator's directive 2026-05-08 post-AddB snapshot completion: GitHub Pages activation deferred; README + metadata are auto-managed (operator confirmed PAT permissions); the rest of the planned work to be processed."
        },
        {
          date: "2026-05-08",
          title: "[Infrastructure + Policy] Math353-AddB: Phase B inventory cleanup (B-κ + B-μ + B-θ DONE; B-λ + B-η + B-ζ operator-handoff)",
          body: "**Theory tag**: `Math353-AddB-Phase-B-Implementation-Report-2026-05-08` **Type**: Implementation report addendum (CLAUDE.md §4.3). **Trigger**: operator's directive 2026-05-08 to \"automatically progress through Phase C\" after Math353-AddA r1-r7 snapshot pipeline first successful 8/8 completion."
        }
      ]
    },
    { type: "html", content: "<div class=\"pagination-nav\">Page 9 / 9 &middot; <a href=\"history/page-008.html\">Older &rarr;</a></div>" }
  ]
};