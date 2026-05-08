# Devil's-Advocate Review — v1 Rigorous Rewrites (2026-04-20, pass 2)

Subject: `TECT-Math49-rigorous.tex.txt`, `TECT-Math49b-rigorous.tex.txt`,
`TECT-Math49c-rigorous.tex.txt`, `TECT-Math_EP-rigorous.tex.txt`,
`TECT-Math_IR_Bound-rigorous.tex.txt`.

Purpose: the v1 rewrites were produced to address the defects
flagged in the first devil's-advocate pass of the same date. This
second pass checks whether the v1 drafts close those defects
without introducing new ones, and whether the main closure claims
are actually proved.

---

## Math49-rigorous — verdict: STILL PROOF SKETCH

**Defects closed from v0:**
- (D1) real-dim 12 now stated correctly (Eq.~(1)).
- (D2) Todd genus now used; A-hat explicitly distinguished.
- (D3) instanton number $k$ no longer asserted; Remark after
  Theorem 1 explains why no $k$ is needed.
- (D4) "$2+1=3$" arithmetic removed; replaced by explicit
  Schubert-pairing framework.

**New defects in v1:**
- (N1) **The main theorem is not proved.** Theorem 1 carries a
  "Proof sketch (to be completed in v2)" label and defers the
  actual computation to a pending SageMath/Macaulay2 certificate.
  The HRR framework is set up correctly but the arithmetic
  yielding the integer $3$ is not executed. Status of
  $\chi(\mathrm{Gr}(2,5), E_L) = 3$ remains ASSERTED, not
  PROVED.
- (N2) Lemma 2 ("Hypercharge fixing") is vague: writes
  "$a = 1/12$ in rational units; integer-normalised $(a,b) =
  (1, -2)$ after multiplication by the $\mathbb{Z}_6$-quotient
  factor that trivialises the line bundle". This is not a
  well-defined specification; the factor $\mathbb{Z}_6$ on the
  total space only reshuffles equivalent bundles and does not
  "trivialise" anything.
- (N3) $E_L$ is a \emph{direct sum} $S \otimes \mathcal{L}^a
  \oplus Q \otimes \mathcal{M}^b$ of two bundles of different
  ranks (2 and 3). HRR applied to a direct sum splits:
  $\chi(E_L) = \chi(S\otimes\mathcal{L}^a) +
  \chi(Q\otimes\mathcal{M}^b)$. The physical mechanism by which
  "3 generations" emerges from this split is not explained;
  in particular the split $3 = 2 + 1$ that was rejected in v0
  as hand-waving could reappear here if the two summands
  contribute 2 and 1 separately.
- (N4) Prop.~1 ("Polarisation from BCC") is stated as an
  "outline"; no actual derivation.

**Assessment:** v1 is an honestly-flagged scaffold with the correct
framework but without the computation. A v2 with the computer-algebra
certificate is required before Pillar 6 can be labelled PROVED.

---

## Math49b-rigorous — verdict: LARGELY CORRECT, one section messy

**Defects closed from v0:**
- (D1) $U(1)_Y^3$ sum now explicit with all five Weyl fields and
  multiplicities $(6,3,3,2,1)$; arithmetic checks
  $1 - 32 + 4 - 9 + 36 = 0$ (Eq.~after \eqref{eq:AYYY}).
- (D2) $SU(2)_W^3$ vanishing now correctly attributed to
  $d^{abc} = 0$ in $\mathfrak{su}(2)$ (Eq.~\eqref{eq:dabc-vanish}).
- Hypercharges derived from $\mathbf{5}$-branching (Lemma 1) rather
  than postulated.

**New defects in v1:**
- (N5) **$SU(3)_c^2 U(1)_Y$ section (§2.5) contains a self-correcting
  mid-proof passage** ("This cannot be correct; the anomaly must
  vanish. The resolution is...") that should be removed and replaced
  with the clean calculation. The final boxed result is correct
  but the path to it is messy.
- (N6) The step from $\mathrm{Tr}(T^a T^b) = T(R)\,\delta^{ab}$ to
  "the anomaly coefficient reduces to $\sum_f T(R_f) Y_f$"
  suppresses a factor of $d^{abc}$ (for Abelian $U(1)_Y$, the
  relevant structure is simply $\sum T(R) Y$, so the reduction
  is correct; but the reader is not told this).

**Verdict:** v2 needs a cleanup of §2.5 (remove the self-correction)
and an explicit one-line justification of why the Abelian $U(1)_Y$
axis reduces to $T(R) Y$ without the non-Abelian $d^{abc}$ factor.

Arithmetic: all six boxed identities check out. Theorem 1 as stated
is proved.

---

## Math49c-rigorous — verdict: LEMMA 2 PROOF INCORRECT

**Defects closed from v0:**
- $\pi_1(\mathrm{SO}(3)/O) = 2O$ (not $\mathbb{Z}_2$) now correct
  (Lemma 1).
- The missing disclination-charge lemma is now stated (Lemma 2).

**New defects in v1:**
- (N7) **Lemma 2 proof contains a factual error.** The proof
  asserts: "$O$ contains $R_\pi^{(100)}$ but does not contain
  $R_{\pi/2}^{(100)}$". This is false: $\pi/2$-rotations about the
  $\langle 100\rangle$ axes ARE generators of the octahedral
  rotation group $O$ of order 24. The correct statement is that
  $R_{\pi/2}^{(100)}$ has order $4$ in $O$
  ($(R_{\pi/2}^{(100)})^4 = R_{2\pi}^{(100)} = \mathbb{1}$), and
  its lift to $\mathrm{SU}(2)$ has order $8$
  ($(\tilde R_{\pi/2}^{(100)})^8 = \mathbb{1}$ while
  $(\tilde R_{\pi/2}^{(100)})^4 = -\mathbb{1}$).
  The conclusion of Lemma 2 is still correct; the justification
  needs rewriting.

**Verdict:** v2 needs a corrected proof of Lemma 2, keyed to the
"order-4 in $O$ lifts to order-8 in $2O$, fourth-power lands on
central $-\mathbb{1}$" mechanism. The rest of the note (Theorem 1,
Theorem 2, connection to fermion statistics) is correct.

---

## Math_EP-rigorous — verdict: CORRECT FOR SCALAR, GAP FOR SPINOR

**Defects closed from v0:**
- (D1) $m_I$ and $m_G$ now defined independently (Defs.~1 and 2).
- (D2) Sign-flip comment removed; sign convention fixed.
- Theorem 1 proved via Noether--Hilbert identity.

**New defects in v1:**
- (N8) The proof (Step 3) identifies
  $T^{\mathrm{grav}\,\mu\nu}$ with $T^{\mathrm{Noeth}\,\mu\nu}$
  for a scalar field theory "with no spin connection". The TECT
  defect IS a Dirac zero mode, which carries spin; the scalar
  case covered by v1 therefore applies to the collective
  coordinate $X(\tau)$ but not to the fermionic zero mode
  sitting inside the defect. The full WEP for the Dirac zero mode
  requires Belinfante--Rosenfeld improvement, which v1 honestly
  flags but does not execute.
- (N9) The phrase "Noether--Hilbert identity" is informal; the
  standard terminology is "Noether's theorem + metric-variation
  stress tensor coincide for scalar Lagrangians" with no
  derivative coupling.

**Verdict:** v1 proves WEP for the scalar collective coordinate
of a BCC defect; it does not cover the full fermionic zero-mode
spectrum. v2 must execute the Belinfante--Rosenfeld improvement
explicitly.

---

## Math_IR_Bound-rigorous — verdict: RELEVANCE ANALYSIS INVERTED

**Defects closed from v0:**
- (D1) Correct $O_h$-invariant cubic operator
  $\sum_i (\partial_i\Psi)^4 - \tfrac{1}{3}(\sum_i(\partial_i\Psi)^2)^2$
  now used (Eq.~\eqref{eq:Oc4-correct}).
- (D2) Canonical dimension $[\mathcal{O}^{(c)}_4] = 6$ correctly
  computed.
- (D3) 1-loop $\eta$ asserted-value removed; v1 states the formula
  structurally and flags numerical evaluation as OPEN.
- (D4) $10^{-70}$ bound explicitly refuted; replaced by
  derivable $\sim 10^{-38}$ bound under stated scale assumptions.

**New defects in v1:**
- (N10) **Lemma 1 conclusion about RG relevance is inverted.**
  The Lemma states: "The operator $\int d^3x\, \mathcal{O}^{(c)}_4$
  has dimension $6 - 3 = 3$, i.e., it is a relevant operator at
  the Gaussian fixed point (irrelevant would require dim $> 3$)."
  Correct RG analysis: in $d = 3$ with operator dimension
  $\Delta = 6$, the coupling $g$ in $\int d^3x\, g\, \mathcal{O}$
  has dimension $[g] = d - \Delta = -3$, so $g(\mu) \sim \mu^{-3}$
  shrinks as $\mu \to 0$ (IR). The operator is therefore
  \emph{irrelevant} at the Gaussian fixed point, not relevant.
  The conclusion the scaffold wanted (IR-irrelevance) is
  actually correct; only the argument is inverted.
- (N11) The Brazovskii fixed point (not Gaussian) is the
  physically relevant one. Its scaling is anisotropic around the
  shell (momenta transverse to the shell scale canonically,
  radial momenta with quartic dispersion). The canonical-dim
  analysis of Lemma 1 uses standard isotropic $d = 3$ scaling,
  which may not apply directly at the Brazovskii fixed point.

**Verdict:** v1 correctly identifies the correct operator and
honestly refutes the $10^{-70}$ claim, but its RG-relevance
analysis has an inverted conclusion. v2 must (a) correct
Lemma 1 to state "irrelevant, not relevant"; (b) separately
analyse the Brazovskii-fixed-point scaling; (c) compute the
1-loop $\eta$ numerically.

---

## Summary of pass-2 defects

| Note | Pass-2 status | Remaining defects | Action required for v2 |
|---|---|---|---|
| Math49-rigorous | SCAFFOLD (framework correct, proof pending) | N1 (proof not executed), N2 (hypercharge), N3 (split), N4 (polarisation) | Compute HRR integral via CAS |
| Math49b-rigorous | NEAR-COMPLETE | N5 (messy §2.5), N6 (brief justification) | Rewrite §2.5 cleanly |
| Math49c-rigorous | NEAR-COMPLETE with LEMMA 2 BUG | N7 (wrong proof of Lemma 2) | Re-derive Lemma 2 via order-4-in-$O$, order-8-in-$2O$ |
| Math_EP-rigorous | PARTIAL (scalar OK, spinor open) | N8 (spinor case), N9 (terminology) | Belinfante--Rosenfeld step |
| Math_IR_Bound-rigorous | SCAFFOLD with correct operator | N10 (relevance inversion), N11 (Brazovskii scaling) | Redo RG analysis; 1-loop BZ integral |

## Pass-2 verdict

Two of the five notes (Math49b, Math49c) are NEAR-COMPLETE with
localised fixable issues. Two (Math49, Math_IR_Bound) are
structurally correct SCAFFOLDS whose main claim remains unproved.
One (Math_EP) is correct for the scalar collective coordinate but
does not cover the fermionic zero-mode spectrum that the TECT
defect actually carries.

No pillar label should be promoted from SCAFFOLD until the
listed defects are resolved. The feedback loop must produce v2
drafts.
