# Code Backup Policy — pre-edit version snapshots

**Binding from**: 2026-04-29
**Maintainer**: Jusang Lee (`jtkor@outlook.com`)
**Helper**: `Codes/scripts/backup_code.sh`
**Log**: `Codes/_backup_log.md` (append-only)

This policy defines how TECT preserves the previous version of a code file BEFORE editing it for a version bump. Git already preserves full history, but operational debugging and quick rollback often need the previous version present in the working tree at a labelled path — not a `git checkout` step.

---

## §1. When backup is mandatory

Any non-trivial edit to a code file in `Codes/` that increments a version (driver `__version__`, tool module-version header, or behavioural breaking change) MUST be preceded by a backup.

Trivial edits (typo fixes, comment-only changes, formatting) do NOT require backup; only behavioural / version-incrementing edits do.

---

## §2. Naming convention (binding)

Backup path is **side-by-side** with the source:

```
<dirname>/<stem>.old.<version>.<ext>
```

Examples:
- `Codes/pde/continuation_mu2_v25.py` v2.6.7 → `Codes/pde/continuation_mu2_v25.old.v2.6.7.py`
- `Codes/tools/generate_website.py` v0.6 → `Codes/tools/generate_website.old.v0.6.py`
- `Codes/scripts/sandbox_commit.sh` v2.0 → `Codes/scripts/sandbox_commit.old.v2.0.sh`

Rules:
- The literal infix `.old.` separates the stem from the version label, making the backup unmistakable in any file listing.
- Version label must include the leading `v` (e.g. `v2.6.7`, NOT `2.6.7`).
- The original extension is preserved at the end so editor syntax-highlighting still works on the backup.

---

## §3. Helper script

`Codes/scripts/backup_code.sh`:

```bash
bash Codes/scripts/backup_code.sh <path/to/file.py> [--version vX.Y.Z]
```

Behaviour:
1. Auto-detects version from `__version__ = "..."` or `Module version: vX.Y.Z` header pattern.
2. Falls back to `--version` argument if auto-detection fails.
3. Creates the backup at `<stem>.old.<version>.<ext>`.
4. Refuses if the backup already exists (idempotent — prevents accidental over-write of an existing snapshot).
5. Appends a row to `Codes/_backup_log.md` with date (UTC), source, backup, version, and current git SHA.

Exit codes: 0 success, 1 usage, 2 source missing, 3 unknown arg, 4 version unknown, 5 backup exists.

---

## §4. Workflow

```bash
# Before bumping continuation_mu2_v25.py from v2.6.7 to v2.6.8:
bash Codes/scripts/backup_code.sh Codes/pde/continuation_mu2_v25.py
# → creates Codes/pde/continuation_mu2_v25.old.v2.6.7.py

# Now edit the file, bump __version__ to "v2.6.8", make the changes.
# Commit both the new file and the .old. backup in the same atomic commit.
```

**Atomic commit rule**: the `.old.<version>.<ext>` backup MUST be part of the same commit that bumps the version. This guarantees the backup is reachable from any future checkout of the version-bump commit.

---

## §5. What the backup is NOT for

- Backup is NOT a substitute for `git log` / `git blame` / `git checkout`. Git is the canonical history.
- Backup is NOT an excuse to delay version bumps. If the file changes substantively, version-bump it AND back-up the previous version.
- Backup is NOT for ad-hoc "I might revert" snapshots. Those belong in feature branches.

The backup pattern is for **operational reachability**: a single `ls Codes/pde/` reveals every previous version present in the working tree at labelled paths.

---

## §6. Exceptions

The following file classes are exempt from this policy:
- Auto-generated files (`Website/data/*.js` / `Website/data/timeline.json` etc.) — always regenerable from canonical sources.
- One-shot supplementary scripts in `Codes/supplementary/Math*.py` — typically not version-bumped; if rerun-with-changes, follow §1.
- Test files in `Codes/tests/` — version pinning lives in `pytest.ini` / fixtures; backup not required.

---

## §7. Cleanup

Old backups (e.g. v1.x of a file currently at v3.x) MAY be moved to `Codes/_backup_archive/<file>.old.<version>.<ext>` after 6 months OR if the working tree clutter becomes excessive (≥ 5 backups of one file). The `_backup_log.md` row remains as the trail.

Archival moves are NOT routine; they require an explicit maintenance commit.

---

## §8. Cross-references

- `Codes/scripts/backup_code.sh` — helper script.
- `Codes/_backup_log.md` — append-only trail (auto-emitted).
- `CLAUDE.md` §10 (Code manual discipline) — version-bump correlation with `Docs/manual/CODE_MANUAL.md` updates.
- `CLAUDE.md` §3 (Atomic-write rule) — backup goes in the same commit as the version bump.
- `Docs/policy/UPDATE_POLICY.md` §13 — file-location discipline.

---

End of CODE_BACKUP_POLICY.md (binding from 2026-04-29).
