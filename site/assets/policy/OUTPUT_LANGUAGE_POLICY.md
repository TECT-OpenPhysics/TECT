# Output-Language Policy (binding from 2026-04-29)

**Maintainer**: Jusang Lee (`jtkor@outlook.com`)
**Binding from**: 2026-04-29
**Cross-references**: `CLAUDE.md` §5 (Communication discipline), `Codes/tools/verify_website.py` (`check_korean_text` enforcement).

---

## §1. Rule

All produced **artefacts** in this repository — Math notes, code, code comments, code docstrings, policy documents, post-mortems, README files, generated website pages, generated website data files (`Website/data/*.js`), website page wrappers (`Website/*.html`), and CHANGELOG entries — MUST be written in **English only**. Korean is reserved for **conversational layer** (chat between operator and AI collaborator); it MUST NOT enter any persisted artefact.

The single exception: archive snapshots already in the repository at the time this policy is adopted (`Website/assets/math/TECT-Math*-KOREAN-SUMMARY.txt`, etc.). These are read-only historical artefacts and are not regenerated; new content overwriting them MUST be English.

## §2. Why

Three reasons:

1. **International readership.** The repository is a candidate Theory-of-Everything programme; reviewers, collaborators, and downstream readers are not assumed to read Korean.
2. **Diff hygiene.** Mixed-language diffs are harder to review and version-control tools (in particular `git log`, `git blame`, GitHub's web interface) treat non-ASCII text inconsistently across operating systems.
3. **Verifier automation.** Korean text in a generated website data file is a strong indicator of a leaked chat-paste or an unconverted draft. Automated detection prevents shipping such pages to users.

## §3. Scope

| Path / file class | Language | Enforcement |
|---|---|---|
| `Docs/math/TECT-Math*.tex.txt` | English (LaTeX) | `verify_website.py check_korean_text` (warn) |
| `Docs/policy/*.md` | English | `verify_website.py` (warn) |
| `Docs/postmortem/*.md` | English | `verify_website.py` (warn) |
| `Docs/manual/CODE_MANUAL.md` | English | `verify_website.py` (warn) |
| `Codes/**/*.py` (code, docstrings, comments) | English | `verify_website.py` (warn) |
| `Codes/**/*.sh`, `*.ps1`, `*.bat` (scripts) | English | `verify_website.py` (warn) |
| `Website/data/*.js` | English | `verify_website.py check_korean_text` (**ERROR**) |
| `Website/data/_narrative/*.md` | English | `verify_website.py check_korean_text` (**ERROR**) |
| `Website/*.html` | English | `verify_website.py check_korean_text` (**ERROR**) |
| `CHANGELOG.md` | English | `verify_website.py` (warn) |
| `CLAUDE.md`, `NAVIGATION.md`, `README.md` | English | `verify_website.py` (warn) |
| Operator ↔ AI chat | Korean (operator preference) | (no enforcement; not persisted) |

The Website tier (`Website/data/*.js`, `Website/data/_narrative/*.md`, `Website/*.html`) is a **hard error**: any Korean character there blocks `verify_website.py` from passing, and CLAUDE.md §6.3.7 requires `verify_website.py` exit-0 before commit.

## §4. What about LaTeX commentary in Korean?

Forbidden in any persisted artefact. If a derivation insight first arose in a Korean chat exchange, the operator translates the *substantive content* into English and writes it to `Docs/math/TECT-MathNN-*.tex.txt`. The Korean version is not preserved as an artefact.

## §5. Detection

`Codes/tools/verify_website.py check_korean_text` scans for any character in the Hangul ranges:

- Hangul Syllables: `U+AC00–U+D7A3`
- Hangul Jamo: `U+1100–U+11FF`
- Hangul Compatibility Jamo: `U+3130–U+318F`

A match in the Website tier is reported as **error** (exit code 1); a match in the Docs/Codes/CHANGELOG tier is reported as **warning** (exit code 0 retained but flagged in stdout).

## §6. Workflow

```bash
# 1. Operator writes content — NEVER paste Korean directly into an artefact path.
# 2. AI collaborator: when producing a Math note, use the English LaTeX version
#    of any reasoning, NOT the Korean chat thread.
# 3. Pre-commit (CLAUDE.md §6.3.7):
python -u Codes/tools/verify_website.py
# 4. If "korean text detected" error fires: edit the file to translate, then re-run.
```

## §7. Cross-references

- `CLAUDE.md` §5 — Communication discipline (Korean for chat / English LaTeX for substance).
- `CLAUDE.md` §6.3.7 — Pre-commit completeness verification (binding).
- `Docs/policy/POSTMORTEM_RECURRENCE_POLICY.md` — every leaked-Korean incident must add a post-mortem note plus its specific check.
- `Codes/tools/verify_website.py` — automated checker.

---

End of OUTPUT_LANGUAGE_POLICY.md (binding from 2026-04-29).
