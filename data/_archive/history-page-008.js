// AUTO-GENERATED v0.3 page 8/8 — 2026-05-06 09:20 UTC
window.TECT_HISTORY_PAGE_008 = {
  title: "History (page 8 of 8)",
  subtitle: "Chronological CHANGELOG mirror — auto-generated.",
  lastUpdated: "2026-05-06 (auto)",
  pagination: {"page": 8, "total": 8, "newer": "history-page-007.html", "older": null, "archiveIndex": "history-archive-index.html"},
  blocks: [
    { type: "html", content: "<div class=\"pagination-nav\"><a href=\"history-page-007.html\">&larr; Newer</a> &middot; Page 8 / 8 &middot; <a href=\"history-archive-index.html\">archive index</a></div>" },
    { type: "timeline", items: [
        {
          date: "2026-04-22",
          title: "[check_jacobian_blocks v1.3.1 + cII_energy_candidates v0.1.1 — Tools/tools case-collision hardening (Task #101/#110 follow-up)]",
          body: "- `Tools/check_jacobian_blocks.py` v1.3 → **v1.3.1**. Defect: first live execution on Windows after the Task #101 rename (`Tools/` → `tools/`) raised `ModuleNotFoundError: No module named 'Tools'` at line 886 inside `run_decisive_cII_test()`, where the lazy import `from Tools import cII_energy_candidates` hard-coded a case-sensitive package prefix. Python 3.12 `FileFinder` is case-sensitive, whereas Windows NTFS is case-insensitive, so the hard-coded casing is fragile. Fix: (i) sys.path bootstrap now prepends `_THIS_FILE_DIR` in addition to `_PDE_DIR` and `_REPO_ROOT_DIR`, so sibling tool modules are directly importable; (ii) the lazy import now reads `import cII_energy_candidates as _cand_mod` (bare sibling form, case-agnostic); (iii) the CLI example in the module docstring and the argparse help text have been updated to `--cII-energy-module cII_energy_candidates:E_cII_C` (no package prefix). - `Tools/cII_energy_candidates.py` v0.1 → **v0.1.1**. Mirror fix in `_self_test()`: the spec-form round-trip exercises `resolve_candidate(\"cII_energy_candidates:E_cII_C\")` instead of the previous capital-T form, aligning the self-test with the case-agnostic import contract."
        },
        {
          date: "2026-04-22",
          title: "[Math65 v0.1 (NEW, SKELETON) + check_jacobian_blocks v1.2.1 → v1.3 + cII_energy_candidates v0.1 (NEW) — decisive cII grad-vs-impl test scaffolding (Task #110)]",
          body: "- `docs/math/TECT-Math65-cII-EulerLagrange-Rewrite.tex.txt` **v0.1 (NEW, SKELETON)**. Pre-surgery theoretical scaffold for the Math64 §6 decisive diagnostic. Contents: (§1) Frame, scope, **critical finding** — the executable backend implements $F_{\\mathrm{cII}}^{\\mathrm{impl}}$ directly as a projected-divergence residual with NO pre-existing scalar $E_{\\mathrm{cII}}[\\Psi]$ in the module; consequently the decisive test $\\Delta_{\\mathrm{cII}} = \\lVert F_{\\mathrm{cII}}^{\\mathrm{impl}} - F_{\\mathrm{cII}}^{\\mathrm{grad}}\\rVert_{F}$ cannot be evaluated until Math65 supplies a candidate. (§2) Three candidate functionals **$E_{\\mathrm{cII}}^{(A)}, E_{\\mathrm{cII}}^{(B)}, E_{\\mathrm{cII}}^{(C)}$**, with propositions `math65-A-status` (INCOMPLETE parent), `math65-B-status` (density-normalised; candidate anti-Hermitian artefact), `math65-C-status` (CANONICAL EL-consistent projected-current parent). (§3) **Helmholtz-Hodge obstruction analysis** — Proposition `math65-hodge` establishes the identity $a_{\\mathrm{cII}}(\\Psi) \\ge c_{0}\\sum_{T}\\lVert \\nabla\\times\\mathbf{V}_{T}(\\Psi)\\rVert_{L^{2}}$, mapping the $4.357\\times 10^{-7}$ anti-Hermitian mass to an $L^{2}$-curl cha"
        },
        {
          date: "2026-04-22",
          title: "[Math63 v1.6 → v1.7 + Math64 v1.0 → v1.1 — §2A.3 post-closure verdict: FULL SYM-PD + decisive cII grad-vs-impl gate (Task #109)]",
          body: "- `docs/math/TECT-Math63-Solver-Redesign-v2.5.tex.txt` v1.6 → v1.7. Header Status extended to \"§2A.3 Stage $\\alpha$ CLOSED — Corollary 2A.3 promoted to window-level; solver-routing verdict refined — FULL SYM-PD $\\Rightarrow$ default PCG; decisive grad-vs-impl cII test mandated\". New v1.6 → v1.7 changelog block in the header documents the PI read-out of R-2026-04-22-003: (a) at the full-operator level the §2A.1 \\emph{relative} ratio $\\rho_{\\mathrm{FULL}} = \\mathrm{antisym}/\\lVert\\mathcal{J}\\rVert_{F} \\approx 1.62\\times 10^{-10}$ at every $\\mu^{2}\\in\\mathcal{W}$ under the cII-on configuration, which lies eight decades below the §2A.1 classification threshold $\\tau_{\\mathrm{rel}} = 10^{-8}$; the scale explanation is $\\lVert\\mathcal{J}_{\\mathrm{FULL}}\\rVert_{F}\\approx 2.7\\times 10^{+3}$ at the thermal seed, so the absolute anti-Hermitian mass $4.357\\times 10^{-7}$ is block-structural at cII but operationally inert at the full-operator level. (b) The Math64 §5 resolutions (X)/(Y)/(Z) are premature until the anti-Hermitian signature is distinguished between an assembly bug in the current projected-divergence implementation vs a design defect in the scalar Class-I"
        },
        {
          date: "2026-04-22",
          title: "[Math63 v1.5 → v1.6 + Math64 v1.0 (NEW) — §2A.3 Stage α CLOSED: Corollary 2A.3 promoted to window-level (Task #109)]",
          body: "- `docs/math/TECT-Math63-Solver-Redesign-v2.5.tex.txt` v1.5 → v1.6. Header Status updated to \"§§2A.1/2A.2/2A.3 addenda; §2A.3 Stage $\\alpha$ CLOSED — Corollary 2A.3 promoted to window-level\". Header changelog gains a v1.5 → v1.6 block documenting the Trigger (live Stage $\\alpha$ four-configuration sweep on user local machine, R-2026-04-22-003), Evidence (four per-config aggregate tables at $\\mu^{2}\\in\\{-1.0,-0.8,-0.6,-0.4,-0.2,-0.1\\}$; $a_{\\alpha_A} = a_{\\alpha_B} = 4.35668\\times 10^{-7}$ bit-identical to ten decimal places under FD and `torch.func.jvp` backends; $a_{\\alpha_D}(\\mathrm{FULL}) = 1.421\\times 10^{-14}$ under structural cII ablation, two decades below the $10^{-12}$ threshold), and Decision (promote Corollary 2A.3 from single-state to window-level; close Stage $\\alpha$; reformulate §2D gate as absolute bound; file Math64 companion audit note). - New §2A.3 subsubsection **\"Stage $\\alpha$ CLOSED: sole-carrier claim promoted to window-level under two backends and structural ablation (2026-04-22)\"** with: boxed Eq. `math63-2A3-stage-alpha-result` tabulating $(\\alpha_A, \\alpha_B, \\alpha_C, \\alpha_D) = (4.3567\\times 10^{-7}, 4.3567\\times 10^{-7}, 1.421"
        },
        {
          date: "2026-04-22",
          title: "[check_jacobian_blocks v1.2 → v1.2.1 — argparse negative-list CLI usability hotfix (Task #109)]",
          body: "- `Tools/check_jacobian_blocks.py` v1.2 → v1.2.1. Python's `argparse` refuses to accept a value that begins with `-` (e.g. `-1.0,-0.8,-0.6,-0.4,-0.2,-0.1`) as the argument of a string-typed option when given in the space-separated form `--mu2-list <neg-csv>`, because argparse cannot disambiguate between \"option-value that happens to look negative\" and \"an unknown optional flag\". The R-2026-04-22 Stage $\\alpha$ driver invocation `python Tools/check_jacobian_blocks.py --backend fd --mu2-list -1.0,-0.8,-0.6,-0.4,-0.2,-0.1` hit exactly this failure: `error: argument --mu2-list: expected one argument`. - **Fix** (v1.2.1): new helper `_glue_negative_list_value(argv, option_name)` preprocesses `sys.argv[1:]` inside `main()` before `parser.parse_args(...)` runs. A token matching `option_name` (currently only `--mu2-list`) whose immediate successor looks like a negative numerical value (`startswith(\"-\")` and contains a digit, a comma, or `.digit`) is folded into the equals-sign form `option_name=<value>` as a single token. All other token patterns, including already-equals-sign-formatted invocations and positive-numerical CSVs, are left untouched. - **Verification**: AST-parse clean;"
        },
        {
          date: "2026-04-22",
          title: "[Math63 v1.4 → v1.5 + check_jacobian_blocks v1.1 → v1.2 — §2A.3 Stage α plan sealed (autograd / multi-mu2 / cII-off extension) (Task #109)]",
          body: "- `Tools/check_jacobian_blocks.py` v1.1 → v1.2. Three orthogonal CLI flags added: - **`--backend {fd,autograd}`** routes the cII Jacobian-vector product through either the pre-existing central-finite-difference path at $\\varepsilon_{\\mathrm{classII\\_hess}} = 5\\times 10^{-7}$ (matching `backend.hessian_vec`) or a forward-mode JVP via `torch.func.jvp`, with `torch.autograd.functional.jvp` as graceful fallback for PyTorch $<2.0$. The autograd path evaluates $(d/dt)|_{t=0}F_{\\mathrm{cII}}(\\Psi + t\\,v) = A(\\Psi)v + B(\\Psi)\\overline{v}$ exactly on `complex128`, removing the central-FD $\\mathcal{O}(\\varepsilon^{2})\\sim 10^{-13}$ truncation floor and the $\\mathcal{O}(\\varepsilon^{-1}u_{\\mathrm{round}})\\sim 2\\times 10^{-10}$ cancellation noise that v1.1 carried. - **`--mu2-list CSV`** replaces the single `--mu2 VALUE` driver with a loop over a list of continuation points, each with its own fresh thermal BCC seed via `math56_constants.build_seed_bcc`. The canonical Stage $\\alpha$ list mirrors the original R-2026-04-22 signal window: $\\mu^{2} \\in \\{-1.0, -0.8, -0.6, -0.4, -0.2, -0.1\\}$. - **`--cII-off`** zeros $\\{\\alpha_{X}, \\beta_{X}, c_{JJ}, c_{JK}\\}$ in a `params"
        },
        {
          date: "2026-04-22",
          title: "[Math63 v1.3 → v1.4 — §2A.3 Step (D1) live execution: S1 empirically confirmed, F_cII isolated as sole carrier of the anti-Hermitian component (Task #109)]",
          body: "- **Step (D1) live sweep executed** on user local machine via `Tools/check_jacobian_blocks.py` v1.1 with `(N, μ², n_probes, σ, seed) = (32, -0.5, 5, 10^{-2}, 42)` on `PDE/config_template_brazovskii.json`. Per-block relative antisymmetry $\\operatorname{antisym}/\\lVert\\mathcal{J}_X\\rVert_F$: - $F_{\\mathrm{bra}}$: $3.97\\times 10^{-18}$ ($\\lVert\\mathcal{J}\\rVert_F = 2.69\\times 10^{+3}$), SYM-PD. - $F_{\\mathrm{fam}}$: $1.23\\times 10^{-18}$ ($\\lVert\\mathcal{J}\\rVert_F = 4.41\\times 10^{-2}$), SYM-PD. - $F_{\\mathrm{lock}}$: $3.54\\times 10^{-18}$ ($\\lVert\\mathcal{J}\\rVert_F = 1.23\\times 10^{-1}$), SYM-PD. - $F_{\\mathrm{shell}}$: $0$ ($\\lVert\\mathcal{J}\\rVert_F = 0$, dormant: $\\eta_{\\mathrm{shell}} = 0$ in config). - $F_{\\mathrm{nl}}$: $4.60\\times 10^{-18}$ ($\\lVert\\mathcal{J}\\rVert_F = 2.30\\times 10^{-4}$), SYM-IND. - $F_{\\mathrm{cII}}$: **$5.84\\times 10^{-3}$** ($\\lVert\\mathcal{J}\\rVert_F = 7.46\\times 10^{-5}$), **ASYM** (exceeds threshold $10^{-8}$ by factor $5.84\\times 10^{+5}$). - FULL: $1.62\\times 10^{-10}$ ($\\lVert\\mathcal{J}\\rVert_F = 2.69\\times 10^{+3}$), SYM-PD (below threshold on the thermal seed). - **Absolute anti-Hermitian norm isol"
        },
        {
          date: "2026-04-22",
          title: "[check_jacobian_blocks v1.0 → v1.1 — sys.path bootstrap hotfix for Step (D1) live execution (Task #109)]",
          body: "- `Tools/check_jacobian_blocks.py` v1.0 → v1.1. First live invocation aborted at `_build_seed()` line 499 with `ModuleNotFoundError: No module named 'math56_constants'`. Root cause: v1.0 relied on ambient `sys.path`, but `math56_constants.py` and `real_backend_pt_bcc_mixed_v3.py` both live in `Contents/PDE/`, which is not on `sys.path` when the script is launched from `Contents/` via `python Tools/check_jacobian_blocks.py ...`. This is the exact analogue of the `continuation_mu2_v25.py` v2.5.0 → v2.5.1 fix (Task #100) and belongs to the same class of import-bootstrap errors that the v2.0 probe tool already resolved. Fix: insert a `sys.path` bootstrap block immediately after the stdlib imports (lines 105–122 of v1.1) that uses `os.path.abspath(__file__)` as the anchor to compute `_THIS_FILE_DIR = .../Contents/Tools`, `_REPO_ROOT_DIR = .../Contents`, `_PDE_DIR = .../Contents/PDE`, and prepends both `_PDE_DIR` and `_REPO_ROOT_DIR` to `sys.path` if not already present. Both `from math56_constants import build_seed_bcc` and `importlib.import_module('real_backend_pt_bcc_mixed_v3')` now resolve deterministically regardless of launch directory. Patch is import-time only; the probe logic, W"
        },
        {
          date: "2026-04-22",
          title: "[check_jacobian_blocks v1.0 — Math63 §2A.3 BCC Jacobian Residual Anti-Hermitian Component Diagnostic, Step (D1) landing (Task #109)]",
          body: "- `Tools/check_jacobian_blocks.py` v1.0 **created** (~460 lines). Sibling to `Tools/check_jacobian_symmetry.py` v2.0 (which is retained unchanged as the full-residual reference); does **not** supersede it. Implements Step (D1) of the Math63 §2A.3 diagnostic plan: the operator-level block decomposition probe. Six additive residual blocks of `real_backend_pt_bcc_mixed_v3.residual()` are probed **in isolation** under the v2.0 complex-Hermitian protocol (real-self-adjoint criterion $\\operatorname{Re}\\langle u, \\mathcal{J}v\\rangle = \\operatorname{Re}\\langle \\mathcal{J}u, v\\rangle$, complex $\\mathcal{CN}(0,I)$ probes, `torch.vdot`/`np.vdot` sesquilinear inner product, threshold $\\operatorname{antisym}/\\lVert J\\rVert < 10^{-8}$). - Block registry: `{\"bra\"=F_bra, \"fam\"=F_fam, \"lock\"=F_lock, \"shell\"=F_shell, \"nl\"=F_nl, \"cII\"=F_cII}` following the additive decomposition `F = F_bra + F_fam + F_lock + F_shell + F_nl + F_cII` (Definition 2A.3-1 of Math63 v1.3). - `F_nl` (quartic + sextic) uses the **analytical Wirtinger JVP** from Lemma 2A.3-2, not a finite-difference approximation: `delta_rho = 2·Re(Ψ* · v)`, `dq = λ(ρ·v + δρ·Ψ)`, `ds = γ(ρ²·v + 2ρ·δρ·Ψ)`. Reference for"
        },
        {
          date: "2026-04-22",
          title: "[continuation_mu2_v25 v2.5.7 + tect_newton_krylov minor — Math63 §2A.2 Exception-Handling Policy (Task #108)]",
          body: "- `PDE/continuation_mu2_v25.py` v2.5.6 → v2.5.7. Three broad `except Exception` branches on the Math63 v2.5 live-execution path narrowed in accordance with Math63 §2A.2 addendum. Module header bumped and full Trigger/Evidence(A-D)/Decision(P1-P5)/Retires/Math-note block inserted. - **Line 299 (import fallback)**: `except Exception as _probe_err:` → `except (ImportError, ModuleNotFoundError) as _probe_err:`. Rationale: a `SyntaxError`, `NameError`, `TypeError`, or `AttributeError` raised from inside `tools.check_jacobian_symmetry` is a programming defect, not a missing-module condition, and must propagate rather than silently disable §2A routing. - **Line 488 (`probe_jacobian_cached`, the Layer-5 culprit)**: split into two branches per §2A.2 dichotomy. `except (AttributeError, TypeError, NameError, ImportError): raise` forecloses the concealment path that let `backend.residual_bcc` and the complex→real cast survive four releases each. `except (RuntimeError, ValueError, ArithmeticError, MemoryError, np.linalg.LinAlgError) as e:` retains graceful degradation for CUDA OOM / numerical overflow / singular-Jacobian conditions but now logs `type(e).__name__: str(e)` to stderr **uncondition"
        },
        {
          date: "2026-04-22",
          title: "[check_jacobian_symmetry v2.0 — complex-Hermitian probe (Math63 §2A.1 addendum)]",
          body: "**Trigger**: The v2.5.5 shape-contract fix landed and the subsequent live Stage $[4/4]$ diagnostic run (`R-2026-04-22-001`) emitted"
        },
        {
          date: "2026-04-22",
          title: "[continuation_mu2_v25 seed shape fix — build_seed_bcc factory (v2.5.5)]",
          body: "**Trigger**: The v2.5.4 attribute-name fix (`residual_bcc` $\\to$ `residual`) landed and the subsequent live Stage $[4/4]$ run printed a *new* error at every fifth Newton iteration of every one of the six $\\mu^{2}$ points:"
        },
        {
          date: "2026-04-22",
          title: "[continuation_mu2_v25 Math63 §2A probe wiring (v2.5.4)]",
          body: "**Trigger**: End-to-end execution of the v2.5.3 driver terminated *correctly* with `Status: SKELETON_ONLY`, exit code $10$, and the honest MANIFEST per-point table — i.e. the honest-reporting contract from v2.5.3 worked as specified. The same clean run, however, surfaced a previously silenced defect visible at every Newton iteration of every one of the six $\\mu^{2}$ points:"
        },
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