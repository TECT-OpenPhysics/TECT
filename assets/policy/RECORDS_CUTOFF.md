# TECT Records Cutoff

**Binding from**: 2026-04-15
**Supersedes**: `PDE/RETRO_MANIFEST_NOTE.md` (withdrawn — see §3)
**Governed by**: `docs/policy/UPDATE_POLICY.md` §10.3

## 1. Cutoff declaration

The date **2026-04-15** is the formal start of the TECT record
system. From this date forward every artefact — theory tag, code
version, production run, website edit — carries provenance as
defined by `docs/policy/UPDATE_POLICY.md`.

All artefacts dated **before 2026-04-15** are treated as
*pre-cutoff historical material*. They are archived for audit but
are not cited as evidence in any paper, website page, or theory
statement.

## 2. What this means in practice

| Artefact class | Pre-cutoff (before 2026-04-15) | Post-cutoff (from 2026-04-15) |
|---|---|---|
| Theory notes | Archived under `docs/math/`; not removed | Cited as primary evidence |
| Paper drafts | Archived under `docs/papers/`; content may be re-used after post-cutoff verification | Cited as primary evidence once verified |
| Code versions | Present in git history; may be referenced by SHA for forensic context | Cited via `MODULE_VERSIONS` + header version |
| Production runs | Kept as historical debugging material only | Cited via `tect_version_manifest.json` |
| Numerical claims | MUST NOT be cited; re-run under current solver required | Cited via result tag |
| Negative results | Pre-cutoff failures are logged in `NEGATIVE-RESULTS.md` only if still pedagogically relevant (current 8 entries are of this class) | Logged per §9 for every future failure |

The existing `F-2026-04-15-*`, `R-2026-04-15-*`, `D-2026-04-15-*`
entries in `NEGATIVE-RESULTS.md` document pre-cutoff mistakes that
shaped the current theory. They are dated to the cutoff itself,
not to their original occurrence, because the cutoff is when the
record began. This is honest bookkeeping, not backdating.

## 3. Why `RETRO_MANIFEST_NOTE.md` was withdrawn

The earlier plan (`RETRO_MANIFEST_NOTE.md`) proposed reconstructing
`tect_version_manifest.json` files retroactively for pre-cutoff
runs under `schema_version: "1.0-retro"`. This is withdrawn for
three reasons:

1. **Source-file identification by git commit date is ambiguous**
   when multiple uncommitted edits sat in the working tree at run
   time.
2. **Regime classification from `(λ, γ)` sign alone** is unreliable
   when the run's `config.json` is missing or was overwritten.
3. **Reconstructed provenance is not evidence.** Citing it in a
   paper would require a forward-confirmation run anyway, and the
   confirmation run — under the current solver — is itself
   sufficient evidence. The retro manifest adds no information.

Therefore: no retro manifests are written. Pre-cutoff runs stay
pre-cutoff.

## 4. How pre-cutoff material may still be used

- **Forensic analysis** — inspecting old runs to understand how a
  bug was introduced. Such use is internal and must not appear in
  papers or public pages.
- **Pedagogical reference** in `NEGATIVE-RESULTS.md` — when a pre-
  cutoff failure shapes current policy (e.g. the GL-regime error),
  the failure itself is recorded. The underlying numerical files
  are not cited.
- **Re-derivation source** — a pre-cutoff result may motivate a
  post-cutoff derivation, but the derivation must stand on its own
  and the post-cutoff run is the evidence.

## 5. Canonical statement for papers and website

> The TECT record system begins on 2026-04-15. All claims cited in
> this work rest on post-cutoff derivations and runs. Pre-cutoff
> material, where referenced, is treated as historical context
> only.

This sentence (or a localisation of it) appears in the Website
`records.html` page and should appear in the front matter of any
paper that cites the repository's provenance system.
