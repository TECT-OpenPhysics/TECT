# Paper 02 — Lorentz-Invariance Bound from Kinematic Lattice Dynamics

> ⚠️ **Audit notice (Math314 family closure, 2026-05-02)**: README metadata predates the Math314 4-stage hostile-referee audit cycle. Current canonical status in `.tex` header `AUDIT-FLAG` block; scorecard in [`../../PAPERS_STATUS_REGISTRY.md`](../../PAPERS_STATUS_REGISTRY.md) (Rev 10). Legacy `Paper-02.md` mirror DEPRECATED.

**Status**: `[DRAFT][NEEDS_UPDATE]` — post-Math314-AddC: ≤ → ≲ notation per CLAUDE.md §15.6 rule #7; recast as conditional Lorentz-consistency bound

---

## Abstract

We prove a rigorous upper bound on the deviation of the transverse phonon speed $c_T$ from the speed of light $c$ in a Brazovskii-type topological condensate. Using kinematic constraints from the BCC lattice structure and the consistency of Lorentz invariance at the effective field theory level, we establish that $|c_T - c| / c \leq 4.8 \times 10^{-4}$ at the lattice scale $a_{\rm BCC} = 4\sqrt{\pi}\,\ell_P$ under the H-suppression hypothesis.

**Tier**: T6 PROVED CONDITIONAL

**Canonical sources**:
- `Docs/math/TECT-Math_IR_Bound-v4-thm-v4-2-final-formalization.tex.txt`

**Open hypotheses**: H-suppression (tracked separately)

**Falsification gate**: None; fully conditional

---

## Compilation

```bash
cd Docs/papers/papers/Paper-02-Pillar2-IR-Bound
pdflatex Paper-02.tex
bibtex Paper-02
pdflatex Paper-02.tex
pdflatex Paper-02.tex
```

**Output**: `Paper-02.pdf`

---

## References

See `references.bib` (auto-generated from canonical Math notes).
