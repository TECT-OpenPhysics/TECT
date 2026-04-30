# TECT Crash-Recovery Playbook

**Binding from**: 2026-04-24
**Triggered by**: incident `Math80-Incident-bad-commit-a603092-2026-04-24`
**Governed by**: `Docs/policy/UPDATE_POLICY.md` §9 (failure discipline) + CLAUDE.md §6 (audit discipline)

---

## 0. What this document covers

Claude Desktop can crash mid-write or mid-`git` operation, leaving the TECT repository in one of two failure modes:

| Mode | Symptom | Cost |
|---|---|---|
| **A. Script truncation** | A `.sh` / `.ps1` / `.py` file ends mid-line; next invocation fails with `unexpected EOF` or silently corrupts state. | **High**: a truncated `sandbox_commit.sh` produced bad commit `a603092` with 49 phantom file deletions (2026-04-24). |
| **B. Stale git lock** | `.git/index.lock`, `.git/HEAD.lock`, or `.git/refs/heads/<branch>.lock` (0-byte). Sandbox cannot remove them due to WSL 9p permissions. Subsequent `git` operations error with `fatal: Unable to create '.git/index.lock': File exists`. | Medium: blocks all git operations until cleaned from Windows side. |

This playbook is the single mechanical rulebook for detecting and repairing both modes.

---

## 1. Four-layer defense

| Layer | Tool | When triggered |
|---|---|---|
| **L1 detection** | EOF sentinels + `_self_integrity_check()` at start of each critical script | Every script invocation |
| **L2 bypass** | `GIT_INDEX_FILE=/tmp/...` + direct write to `.git/refs/heads/<branch>` | `sandbox_commit.sh` always |
| **L3 batch diagnosis** | `Codes/scripts/verify_scripts_integrity.sh` | Session start + on demand |
| **L4 Windows cleanup** | `Codes/scripts/recover_after_crash.ps1` | After any Claude Desktop crash |

---

## 2. Standard session-start procedure

From **sandbox**:
```bash
bash Codes/scripts/preflight.sh
```

Expected output on clean session:
```
=== TECT sandbox preflight v1.0 ===
  [OK]   HEAD: ref: refs/heads/main
  [OK]   .git/index.lock (absent)
  [OK]   .git/HEAD.lock (absent)
  ...
=== [OK] preflight passed -- safe to commit ===
```

If preflight fails with `[FAIL] could not truncate lock (WSL permission?)`, the user must run the Windows-side recovery:

```powershell
cd C:\Dev\TECT2\Contents
powershell -ExecutionPolicy Bypass -File Codes\scripts\recover_after_crash.ps1
```

---

## 3. Recovery procedures by mode

### 3.1 Mode A — Truncated script

**Detection** (sandbox or Windows):
```bash
bash Codes/scripts/verify_scripts_integrity.sh --fix-suggest
```

Each critical script must end with a line of the form
```
# <script_name>_v<N>_<M>_eof_sentinel_DO_NOT_REMOVE
```

If the tool reports `[TRUNCAT]`, the script is corrupted. Recovery priority:
1. `git checkout HEAD -- <script-path>` — if the last-committed version is known good.
2. `git show HEAD~1:<script-path> > <script-path>` — if the current HEAD is itself the bad commit.
3. Manual restoration from `Codes/scripts/<script>.sh.bak` if we maintain a backup copy.

**Add a new script to the integrity registry**: edit `Codes/scripts/verify_scripts_integrity.sh` REGISTRY array; add an EOF sentinel to the target script.

### 3.2 Mode B — Stale git lock (from Windows)

```powershell
cd C:\Dev\TECT2\Contents
Remove-Item -Force -ErrorAction SilentlyContinue `
    .git\index.lock, .git\HEAD.lock, .git\refs\heads\main.lock
```

Or one command via the recovery script:
```powershell
powershell -ExecutionPolicy Bypass -File Codes\scripts\recover_after_crash.ps1 -Force
```

### 3.3 Mode B — Stale git lock (from sandbox only)

Sandbox cannot `rm` the lock files due to WSL permissions, but:

1. **Truncation works**: `: > .git/index.lock` truncates the file to 0 bytes. Some git operations still fail because they check for file *existence*, not content.
2. **Bypass works**: `sandbox_commit.sh v2.0+` uses `GIT_INDEX_FILE=/tmp/...` and direct ref-file writes, so it works even with locks present.

So from sandbox, **prefer using `sandbox_commit.sh` over `git commit`** — it's lock-immune.

### 3.4 Mode B — Bad commit recovery (emergency)

If a corrupted commit (like `a603092` on 2026-04-24) made it into HEAD:

```bash
# 1. Inspect
git diff --name-status HEAD~1 HEAD | awk '{print $1}' | sort | uniq -c
# expect: only M + A entries. Many D entries => bad commit.

# 2. Direct ref rewind (sandbox-safe)
echo "<good-parent-SHA>" > .git/refs/heads/main

# 3. Re-do the commit via sandbox_commit.sh (which bypasses locks)
bash Codes/scripts/sandbox_commit.sh "<message>" <file1> <file2> ...
```

See incident `R-2026-04-24-bad-commit-a603092` in NEGATIVE-RESULTS.md for the canonical example.

---

## 4. EOF-sentinel discipline

Every script registered in `verify_scripts_integrity.sh` REGISTRY must satisfy:

1. Final content line is `# <name>_v<N>_<M>_eof_sentinel_DO_NOT_REMOVE`.
2. First 20 lines include a `_self_integrity_check()` function that calls `exit 9` if the sentinel is missing from `tail -3 "${BASH_SOURCE[0]}"`.
3. The sentinel name is **globally unique** (version-tagged) so that a stale backup doesn't silently pass.

**When bumping a script version**: increment `_v<N>_<M>`, change the sentinel string EVERYWHERE (top check + bottom sentinel + `verify_scripts_integrity.sh` REGISTRY entry).

---

## 5. Root-cause reference

**Why the truncation happens**: Claude Desktop's Write tool is not atomic. When it crashes mid-write, the target file is left truncated (whatever was flushed to disk before the crash). The fix (from Cowork/Claude side) would be atomic write-then-rename — not implementable from inside the agent. Our defense is self-integrity checks.

**Why the lock files linger**: WSL 9p mount (`C:\Dev\TECT2\Contents` mounted as `/sessions/eloquent-wonderful-franklin/mnt/Contents` in the sandbox) handles file ownership / unlink differently from native Windows NTFS. Files created by sandbox git have mode `rwx------` owned by the sandbox UID; Windows side owns the filesystem and can always `Remove-Item`, but sandbox cannot `unlink` them once they exist.

**Why direct ref write works**: The `echo "<sha>" > .git/refs/heads/main` operation is an *overwrite-in-place* of an EXISTING tracked file; it does not require unlink and does not consult the `.lock` sidecar. Git's `update-ref` fails because it does consult the lock. The bypass is therefore: write the ref file directly with a shell redirect.

---

## 6. Cross-references

- `CLAUDE.md` §11 (git discipline), §13 (file-location discipline)
- `Docs/policy/UPDATE_POLICY.md` §9 (failure discipline), §14 (session-start protocol)
- `Docs/policy/REPO_LAYOUT.md` §6 (canonical file locations)
- `Codes/scripts/sandbox_commit.sh` v2.0 (the lock-bypassed commit tool)
- `Codes/scripts/verify_scripts_integrity.sh` v1.0 (batch EOF check)
- `Codes/scripts/preflight.sh` v1.0 (session-start gate)
- `Codes/scripts/recover_after_crash.ps1` v1.0 (Windows-side cleanup)

---

## 7. Maintenance

When a new critical script is added, append to the registry in
`Codes/scripts/verify_scripts_integrity.sh` and add an EOF sentinel to the new script.

When the EOF-sentinel scheme is versioned, update:
1. The script itself (top check string + bottom sentinel line).
2. `verify_scripts_integrity.sh` REGISTRY.
3. `recover_after_crash.ps1` `$registry` array.
4. This document's §1 table + §4 discipline.

All four updates MUST ride together in a single commit (atomic-write, CLAUDE.md §3).
