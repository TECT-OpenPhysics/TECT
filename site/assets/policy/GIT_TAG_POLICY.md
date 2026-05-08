# TECT git tag policy

Status: **approved 2026-04-15**. Applies from the first commit of the TECT repository onwards.

## 1. Purpose

Every numerical result produced by TECT must be externally reproducible from a single `(theory_version, code_git_sha)` pair. Theory versions are already stamped in `CHANGELOG.md`; git tags are the mechanism by which a code_git_sha becomes citable.

## 2. Tag naming

Tags track the theory axis of the three-axis version model (theory / module / result).

- Every theory-level change recorded in `CHANGELOG.md` gets a git tag identical to the theory tag in the changelog header, e.g. `Math38-Brazovskii-2026-04-15`.
- Tags are **annotated**, never lightweight: `git tag -a Math38-Brazovskii-2026-04-15 -m "..."`.
- Tag messages quote the changelog entry verbatim (Theory / Code / Results / Docs / Infrastructure sections).
- Tags are **never moved** once pushed. If a tagged commit turns out to be wrong, publish a superseding tag (next Math-NN) with a clear `Supersedes: <old-tag>` line and leave the old tag in place for audit.

## 3. When to tag

- Immediately after every accepted `CHANGELOG.md` entry lands on `main`.
- Before any `tect_version_manifest.json` is written in production: the run must reference a tag that already exists.
- Never mid-branch. Tags go on `main` only.

## 4. Procedure

```bash
# 1. Verify changelog entry is present and main is up to date
grep '^## `Math' CHANGELOG.md | head -1     # should match new tag
git pull --ff-only origin main

# 2. Create the annotated tag with the changelog entry in the message
TAG=Math38-Brazovskii-2026-04-15
git tag -a "$TAG" -m "$(sed -n "/^## \`$TAG\`/,/^## \`/p" CHANGELOG.md | head -n -1)"

# 3. Push (tag-only push is explicit — no --follow-tags)
git push origin "$TAG"

# 4. Record the tag \u2194 commit mapping in the sync doc
SHA=$(git rev-parse "$TAG^{commit}")
echo "| $TAG | $SHA |" >> docs/status/TECT-Theory-Code-Sync.md
```

## 5. Pre-existing history (2026-04-15 and earlier)

This policy takes effect at the moment the TECT repository is initialised as git. The three retroactive theory tags — `Math37-Step5-2026-04-15`, `Math37-AddA-2026-04-15`, `Math38-Brazovskii-2026-04-15` — are applied to the initial commit since they were all produced on the same working directory state. Any future change begins with a new commit and its own tag.

## 6. What is NOT tagged

- Module-version bumps that do not touch theory: these get `MODULE_VERSIONS` dict updates and a `stamp_version_headers.py` re-run, recorded under the next theory tag's [Code] section, but do **not** get their own git tag.
- Per-run result tags (`R-<date>-<seq>-<theory>`): these live only in `tect_version_manifest.json` artefacts; they are not git tags.

## 7. Enforcement

`tools/build_version_index.py --check` will (in a later revision) cross-verify that every theory tag in `CHANGELOG.md` has a matching git tag reachable from `main`. Failing this check blocks the commit.

## 8. Governance

Edits to this policy require a documented entry in `CHANGELOG.md` under [Infrastructure] and a pull request with two reviewers.
