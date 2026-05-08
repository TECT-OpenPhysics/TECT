# Paper TI-1 — Hirzebruch–Riemann–Roch Index Formula Corrected

> ⚠️ **Audit notice (Math314 family closure, 2026-05-02)**: README metadata predates the Math314 audit. Current canonical status in `.tex` `AUDIT-FLAG` block; scorecard at [`../../PAPERS_STATUS_REGISTRY.md`](../../PAPERS_STATUS_REGISTRY.md) (Rev 10).

**Status**: `[DRAFT][NEEDS_UPDATE]` — Wave 2 top-impact, post-Math314-AddB: MATHEMATICAL DEFECT REPAIRED in place — original `ind(D_E^c) = 16 - μ` (rank-conflated) restructured into (i) main theorem `ind = r - μ` (general rank), (ii) corollary `r=16 ⟹ ind = 16 - μ`, (iii) separate remark on Picard classification. Q-2026-05-02-Math171-AddA-Rank-Dependence opened for parent Math171-AddA patch.
**Author**: Jusang Lee (jtkor@outlook.com)
**Date**: 2026-05-02
**Tags**: Index theory, algebraic geometry, topological classification

---

## Abstract

We correct a degree-arithmetic error in the computation of the spin-c Dirac index on $\mathbb{CP}^2$ and establish the corrected Hirzebruch–Riemann–Roch formula $\mathrm{ind}(D_E^c) = 16 - \mu$, where $\mu = c_2(E)/H^2$. The original error (Math171 §3.3) treated a degree-0 constant term as if it could be rewritten as a degree-2 form before integration, violating degree-parity constraints on a 4-dimensional complex manifold. Using the canonical complex spin-c structure with determinant bundle $c_1(L_{\rm can}) = 3H$, the spin-c Dirac index becomes the holomorphic Euler characteristic. We prove that all holomorphic line bundles on $\mathbb{CP}^2$ are classified by a unique integer via $\mathrm{Pic}(\mathbb{CP}^2) \cong \mathbb{Z}$, with no continuous moduli. Status: PROVED unconditional.

## Canonical proof-archive source

- `Docs/math/TECT-Math171-AddA-degree-arithmetic-correction.tex.txt` — full derivation and error analysis

## Key formulas

- Corrected index: $\mathrm{ind}(D_E^c) = 16 - \mu$ (rank-16 bundle with $c_1(E) = 0$)
- Todd class: $\mathrm{td}(T\mathbb{CP}^2) = 1 + 3H/2 + H^2$
- Picard group: $\mathrm{Pic}(\mathbb{CP}^2) \cong \mathbb{Z}$ (no Pic⁰ continuous component)

## Scope and limitations

- Applies to rank-$r$ holomorphic bundles on $\mathbb{CP}^2$ with $c_1(E) = 0$
- Canonical spin-c structure assumed (other spin-c structures shift $c_1(L)$ and change the formula)
- TECT Pillar 4 application: U(1)_χ bundle uniquely parameterized by integer $k_\chi$

## Compilation

```bash
cd Docs/papers/top_impact/Paper-TI-1-HRR-Index-Formula
pdflatex Paper-TI-1.tex
bibtex Paper-TI-1
pdflatex Paper-TI-1.tex
pdflatex Paper-TI-1.tex
```

## Status history

| Date | Status | Note |
|---|---|---|
| 2026-05-02 | `[STUB]` → `[DRAFT]` | Wave 2 standalone written; pending compilation + review |
