# Paper 05 — Chirality from Index-Theoretic Protection

> ⚠️ **Audit notice (Math314 family closure, 2026-05-02)**: README metadata predates the Math314 audit. Current canonical status in `.tex` `AUDIT-FLAG` block; scorecard at [`../../PAPERS_STATUS_REGISTRY.md`](../../PAPERS_STATUS_REGISTRY.md) (Rev 10). Legacy `Paper-05.md` mirror DEPRECATED.

**Status**: `[DRAFT][NEEDS_UPDATE][REWRITE_REQUIRED]` — post-Math314-AddC: original `Index(D) = wind(m)` identification on 3D Brillouin torus does NOT hold without Callias / domain-wall framework. Recast as MECHANISM NOTE; full theorem-level rewrite tracked under Q-2026-05-02-Pillar5-Mechanism-Rewrite.

---

## Abstract

We establish that chirality emerges from the topological structure of the Dirac operator in the TECT framework. The Atiyah–Singer index theorem guarantees zero modes protected by valley $\mathbb{Z}_2^V$ symmetry. The number of chiral fermion families equals the winding number of the condensate order parameter. Pillar 5 at T7 PROVED — no external hypotheses required.

**Tier**: T7 PROVED

**Canonical sources**:
- `Docs/math/TECT-Math10.tex.txt`
- `Docs/math/TECT-Math11.tex.txt`
- `Docs/math/TECT-Math12.tex.txt`
- `Docs/math/TECT-Math13.tex.txt`
- `Docs/math/TECT-Math14.tex.txt`

**Open hypotheses**: None — fully unconditional

**Falsification gate**: None — theorem complete

---

## Compilation

```bash
cd Docs/papers/papers/Paper-05-Pillar5-Chirality
pdflatex Paper-05.tex
bibtex Paper-05
pdflatex Paper-05.tex
pdflatex Paper-05.tex
```

**Output**: `Paper-05.pdf`

---

## References

See `references.bib` (auto-generated from canonical Math notes).
