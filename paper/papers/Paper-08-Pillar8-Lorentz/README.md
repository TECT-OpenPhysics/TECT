# Paper 08 — Lorentz Invariance via Interval-Arithmetic Certification

> ⚠️ **Audit notice (Math314 family closure, 2026-05-02)**: README metadata predates the Math314 audit. Current canonical status in `.tex` `AUDIT-FLAG` block; scorecard at [`../../PAPERS_STATUS_REGISTRY.md`](../../PAPERS_STATUS_REGISTRY.md) (Rev 10). Legacy `Paper-08.md` mirror DEPRECATED.

**Status**: `[DRAFT][NEEDS_UPDATE]` — post-Math314-AddC: TITLE MIS-CLASSIFICATION repaired — interval `J_1 ∈ [5.99e-2, 1.51e-1]` EXCLUDES 0, so this is a finite-lattice Lorentz-VIOLATION bound, NOT invariance certification. "95% confidence" → "deterministic enclosure". T7 PROVED claim retracted (Math319 V2/V3 execution gates pending).

---

## Abstract

We establish Pillar 8 of TECT using rigorous interval arithmetic (\texttt{mpmath}). The Lorentz-violation parameter $J_1$ is computed on a shell-adaptive BCC lattice with $N=256$ sites per dimension, certified to lie in $[5.99 \times 10^{-2}, 1.51 \times 10^{-1}]$. This interval confirms measurable but tolerable Lorentz violation consistent with TECT framework. Pillar 8 at T7 PROVED via certified numerical closure.

**Tier**: T7 PROVED (via interval-arithmetic certification)

**Canonical sources**:
- `Docs/math/TECT-Math_IR_Bound-v4-thm-v4-2-final-formalization.tex.txt`
- `Docs/math/TECT-Math_IR_Bound-v4-BZ-integrator.tex.txt`
- `Docs/math/TECT-Math_IR_Bound-v4-shell-adaptive.tex.txt`

**Numerical reproducibility**:
- `Runs/audit/lorentz_pillar8_N256_mpmath.py` (executable code)
- `Runs/audit/lorentz_pillar8_N256/run_diagnostics.json` (provenance)

**Falsification gate**: None — fully closed

---

## Compilation

```bash
cd Docs/papers/papers/Paper-08-Pillar8-Lorentz
pdflatex Paper-08.tex
bibtex Paper-08
pdflatex Paper-08.tex
pdflatex Paper-08.tex
```

**Output**: `Paper-08.pdf`

---

## References

See `references.bib` (auto-generated from canonical Math notes).
