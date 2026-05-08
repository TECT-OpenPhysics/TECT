# Paper TI-2 — BCC Selection Uniqueness Among Crystallographic Competitors

> ⚠️ **Audit notice (Math314 family closure, 2026-05-02)**: README metadata predates the Math314 audit. Current canonical status in `.tex` `AUDIT-FLAG` block; scorecard at [`../../PAPERS_STATUS_REGISTRY.md`](../../PAPERS_STATUS_REGISTRY.md) (Rev 10).

**Status**: `[DRAFT][NEEDS_UPDATE]` — Wave 2 top-impact, post-Math314-AddB: structural over-claim downgraded — title/abstract/Theorem 1 recast as "Conditional BCC ranking within the SMA shell model" with explicit "NOT a global-minimum theorem" disclaimer; new Remark on cubic-stabilisation effective-vs-explicit nomenclature.
**Author**: Jusang Lee (jtkor@outlook.com)
**Date**: 2026-05-02
**Tags**: Crystallography, free-energy minimisation, phase selection

---

## Abstract

We rigorously prove that body-centered cubic (BCC) structure is the unique global minimum of the Brazovskii free-energy functional among nine standard 3D crystallographic competitors at the TECT operating point $(\mu^2, \lambda, \gamma) = (5 \times 10^{-3}, -0.43, 1.62)$. The proof combines analytical enumeration via single-mode approximation (SMA), explicit Brazovskii cubic-stabilisation-coefficient computation, and numerical free-energy ranking. BCC achieves maximum four-wave resonance count $N_{\text{loop}}^{\rm BCC} = 6$, generating cubic-stabilisation coefficient $\mathcal{C}_{\rm BCC} = 6$, yielding free-energy advantage $\Delta F_{\rm gap} = 0.30$ (approximately 10× over nearest competitor gyroid). The rigorous answer to "why BCC?" emerges from first-principle Brazovskii minimisation, not postulate. Status: STRONG CLOSURE DRAFT (single-shell caveat; multi-shell correction pending).

## Canonical proof-archive source

- `Docs/math/TECT-Math194-BCC-uniqueness-among-3D-crystallographic-competitors.tex.txt` — full enumeration and ranking

## Key results

- **BCC free energy**: $F_{\rm BCC}/V = 0.00$ (reference)
- **Nearest competitor (gyroid)**: $F_{\rm gyroid}/V = +0.30$ (10× Brazovskii separation)
- **Cubic stabilisation**: $\mathcal{C}_{\rm BCC} = 6$ (maximum among nine competitors)
- **Operating point**: $(\mu^2, \lambda, \gamma, q_0) = (5\times10^{-3}, -0.43, 1.62, 0.6802)$

## Nine competitors ranked

1. BCC ($\mathcal{C} = 6$): $\Delta F = 0.00$
2. Gyroid ($\mathcal{C} = 1$): $\Delta F = +0.30$
3. FCC ($\mathcal{C} = 2$): $\Delta F = +0.42$
4. HCP ($\mathcal{C} = 1$): $\Delta F = +0.45$
5. A15 ($\mathcal{C} = 3$): $\Delta F = +0.58$
6. $\sigma$-phase ($\mathcal{C} = 2$): $\Delta F = +0.62$
7. Simple cubic ($\mathcal{C} = 0$): $\Delta F = +0.89$
8. Hexagonal ($\mathcal{C} = 0$): $\Delta F = +0.91$
9. Lamellar ($\mathcal{C} = 0$): $\Delta F = +1.2$

## Honest scope limitations

- Single-mode truncation (first shell only at $|\mathbf{k}| = q_0$)
- Equal-amplitude ansatz (protected by Michel's theorem but may miss asymmetric perturbations)
- No multi-shell interactions (higher shells at deeper $\mu^2 < -0.1$ not explored)

## Compilation

```bash
cd Docs/papers/top_impact/Paper-TI-2-BCC-Uniqueness
pdflatex Paper-TI-2.tex
bibtex Paper-TI-2
pdflatex Paper-TI-2.tex
pdflatex Paper-TI-2.tex
```

## Status history

| Date | Status | Note |
|---|---|---|
| 2026-05-02 | `[STUB]` → `[DRAFT]` | Wave 2 standalone written; pending compilation + review |
