# Post-Mortem & Recurrence-Prevention Policy

**Binding from**: 2026-04-29
**Maintainer**: Jusang Lee (`jtkor@outlook.com`)
**Trigger event**: 2026-04-29 — Results page rendered empty due to JS-string escape bug; user discovered the failure, not pre-commit verification. Root cause: no completeness verification ran between code edit and commit.
**Cross-references**: `CLAUDE.md` §6.3.7 (mandatory completeness verification), `Codes/tools/verify_website.py` (helper).

---

## §1. Why this policy exists

A bug ("Results page empty") was committed and reached the user before verification. The fix was straightforward, but the **systemic problem** is that there was no automated check between "edit complete" and "commit landed". Future bugs of the same class (escape errors, missing files, stale manifests, broken download links) will keep recurring unless a verification step runs **before every commit that touches Website/, Codes/, or Docs/**.

This policy mandates two separate but linked disciplines:

1. **Post-mortem on every observed failure**: when a user reports a defect, write a short note that identifies the root cause, the failure-mode class, and the recurrence-prevention mechanism that closes the class.
2. **Pre-commit completeness verification**: run an automated check that catches the same class of defect before it ships again.

---

## §2. Post-mortem note format

Every observed failure (bug report from user, audit-rollback, broken link, etc.) gets a post-mortem note at `Docs/postmortem/YYYY-MM-DD-<descriptor>.md` with these sections:

| Section | Content |
|---|---|
| Trigger | Verbatim user message or audit verdict |
| Failure mode | Concrete observable: "Results page renders blank", "404 on download X", "manifest count mismatch" |
| Root cause | Mechanical explanation (file:line + reasoning) |
| Class of defect | Generic name: "JS-string escape bug", "missing-asset link", "stale-manifest", etc. |
| Recurrence prevention | Specific check added to `verify_website.py` (or equivalent) that would have caught the bug |
| Verification proof | Output of the verification helper showing the new check passes after the fix |
| Cross-references | Commit SHA(s) for the fix, related Math notes / policies |

---

## §3. Recurrence-prevention check classes (binding)

Each defect class observed once is permanently registered as a check in `Codes/tools/verify_website.py`. Current classes (will grow):

| Class | Check | Helper function |
|---|---|---|
| **JS-string escape bug** | regex for `(?<!\\)href="` inside `window.TECT_<NAME>` data files | `check_js_syntax` |
| **Broken download link** | every `href="assets/X"` resolves to an existing file in `Website/assets/X` | `check_download_links` |
| **Missing HTML wrapper** | every `Website/data/<page>.js` has matching `Website/<page>.html` | `check_html_wrappers` |
| **Stale manifest** | `manifest.json` count matches actual file count | `check_manifest_freshness` |
| **Stale auto-page source-count** | declared file count in auto-gen header matches actual canonical source | `check_auto_freshness` |
| **Empty TECT_<NAME> blocks** | data file is parseable but has empty `blocks: []` (escape-bug symptom) | `check_empty_tect_objects` |

Adding a new check after a new defect is the **first step** of any post-mortem; the fix follows the check.

---

## §4. Pre-commit verification gate (CLAUDE.md §6.3.7)

Every commit that touches `Website/`, `Codes/tools/generate_website.py`, or `Codes/tools/verify_website.py` MUST run:

```bash
python -u Codes/tools/verify_website.py
```

and exit code 0 before `git commit`. The helper exits 1 on any error; warnings do not block commit but should be addressed.

This is **automation**, not a manual checklist. The verification step is the minimal cost of a publication-grade commit.

For commits touching only theory notes (`Docs/math/*.tex.txt`) or run results (`Runs/<class>/<run_id>/`) without Website / generator changes, the verification step is recommended but not required.

---

## §5. The 2026-04-29 reference incident

**Trigger**: User: "Results 페이지에 내용이 없어, Notes가 다운로드 되지 않아."

**Failure mode 1**: `Website/data/results.js` rendered as a parseable JS file but `window.TECT_RESULTS.blocks: []` was effectively empty (the table HTML inside terminated the outer JS string early due to embedded `<a href="...">` quotes).

**Root cause 1**: `Codes/tools/generate_website.py` `render_results_js` v0.8 added per-run download links via `dl = ['<a href=\\"...\\">...</a>']` (Python-source single-backslash escape). After Python interpretation the literal string contained `<a href="...">` (single backslash gone), and that string was then concatenated into an outer JS string `'"<p>..." + dl_links + "..."<\p>"'`. The **embedded** `"` then terminated the outer JS string at parse time.

**Class of defect**: JS-string escape bug (2-level escape: Python source → Python string → JS source → JS string).

**Recurrence prevention**: `verify_website.py` `check_js_syntax` regex `(?<!\\)href="` flags any unescaped `href="` inside a TECT data file; combined with `node --check` (when available) for full JS parse.

**Failure mode 2**: `Website/assets/math/` had 330 files; `Docs/math/` had 397 files; 67 newer Math notes had no asset counterpart, so download links on Notes page returned 404.

**Root cause 2**: No automated sync between `Docs/math/*.tex.txt` (canonical source) and `Website/assets/math/` (download mirror). Manual `cp` was the only mechanism, and it was last run 5 days earlier.

**Recurrence prevention**: `verify_website.py` `check_auto_freshness` compares declared count in `math-notes.js` header against actual `Docs/math/TECT-Math*.tex.txt` count; warns + fails when mismatched. Future enhancement: `--copy-assets-quick` flag in `generate_website.py` to keep math/ in sync without the full assets copy.

**Verification proof**: After fixes, `python Codes/tools/verify_website.py` output:
```
errors:   0
warnings: 0
OK: website verification passed.
```

---

## §6. Workflow

```bash
# 1. Edit Website/, Codes/tools/, or templates as needed.
# 2. Re-generate auto pages (if generator was touched):
python -u Codes/tools/generate_website.py --all

# 3. (Mandatory if Website/ touched): Verify completeness.
python -u Codes/tools/verify_website.py

# 4. If errors: fix them, GOTO 2. Add a new check to verify_website.py
#    if the bug is in a new class.

# 5. Commit only after step 3 prints "OK: website verification passed".
bash Codes/scripts/sandbox_commit.sh "..." <files...>

# 6. If a user later reports a defect that slipped through:
#    - Write Docs/postmortem/YYYY-MM-DD-<descriptor>.md
#    - Add the recurrence-prevention check to verify_website.py
#    - Both go in the same commit as the fix.
```

---

## §7. Cross-references

- `CLAUDE.md` §6.3.7 — Pre-commit completeness verification (binding rule).
- `Codes/tools/verify_website.py` — automated checker.
- `Docs/policy/WEBSITE_AUTO_SYNC.md` — per-page sync mode table.
- `Docs/postmortem/2026-04-29-results-empty-and-notes-broken.md` — first reference incident.

---

End of POSTMORTEM_RECURRENCE_POLICY.md (binding from 2026-04-29).
