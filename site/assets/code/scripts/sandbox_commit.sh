#!/bin/bash
# =====================================================================
# sandbox_commit.sh v2.0 -- crash-safe git commit from Cowork sandbox
# =====================================================================

_SANDBOX_COMMIT_SENTINEL="sandbox_commit_v2_0_eof_sentinel_DO_NOT_REMOVE"
_self_integrity_check() {
    local src="${BASH_SOURCE[0]}"
    if [[ ! -r "$src" ]]; then
        echo "FATAL: cannot read $src" >&2; exit 9
    fi
    if ! tail -5 "$src" | grep -qF "# ${_SANDBOX_COMMIT_SENTINEL}"; then
        echo "" >&2
        echo "================================================================" >&2
        echo "  FATAL: $0 TRUNCATED -- EOF sentinel missing." >&2
        echo "  Likely Claude Desktop crash / Write-tool truncation." >&2
        echo "  Recovery: git checkout HEAD -- $0" >&2
        echo "            or see Docs/policy/CRASH_RECOVERY.md sec 3" >&2
        echo "================================================================" >&2
        exit 9
    fi
}
_self_integrity_check

set -u

# -------------------- argument parsing --------------------
MSG=""; MSG_FILE=""; FILES=()
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <msg | -F msg_file> <file1> [<file2> ...]" >&2; exit 1
fi
if [[ "$1" == "-F" ]]; then
    MSG_FILE="$2"; shift 2
    [[ -f "$MSG_FILE" ]] || { echo "Error: $MSG_FILE not found" >&2; exit 1; }
    MSG=$(cat "$MSG_FILE")
else
    MSG="$1"; shift
fi
# v2.1 (2026-05-07 Math353-AddA): support --files-from <listfile>
# in addition to positional arguments. Bypasses Windows CMD 8191-char
# limit when snapshot.ps1 has many changed files. Listfile may have
# CRLF endings (handled below).
FILES=()
while [[ $# -gt 0 ]]; do
    if [[ "$1" == "--files-from" ]]; then
        LIST_FILE="$2"; shift 2
        [[ -f "$LIST_FILE" ]] || { echo "Error: $LIST_FILE not found" >&2; exit 1; }
        while IFS= read -r line; do
            line="${line%$'\r'}"
            [[ -n "$line" ]] && FILES+=("$line")
        done < "$LIST_FILE"
    else
        FILES+=("$1"); shift
    fi
done
[[ ${#FILES[@]} -eq 0 ]] && { echo "Error: no files" >&2; exit 4; }

# -------------------- repo sanity + REPO_LAYOUT guard --------------------
[[ -d .git ]] || { echo "Error: not a repo" >&2; exit 2; }
HEAD_REF=$(cat .git/HEAD)
[[ "$HEAD_REF" =~ ^ref:\ refs/heads/.* ]] || { echo "Error: detached HEAD" >&2; exit 3; }
BRANCH_REF=$(echo "$HEAD_REF" | sed 's/^ref: //')
BRANCH_FILE=".git/$BRANCH_REF"
PARENT_SHA=$(git rev-parse HEAD)

_violations=()
for f in "${FILES[@]}"; do
    base=$(basename "$f"); dir=$(dirname "$f")
    [[ "$dir" != "." ]] && continue
    case "$base" in
        *commit*.sh|*commit*.py|*commit*.bat|\
        direct_*.sh|do_commit*.sh|run_commit*.sh|run_*_commit.sh|\
        temp_commit_*.sh|temp_*_commit.sh|\
        *_commit_msg.txt|*_commit_*.txt|COMMIT_MANIFEST_*.txt|COMMIT_*.txt|\
        .commit_message_temp.txt|.*_commit_trigger|.*_commit_msg)
            _violations+=("$f -> use Codes/scripts/sandbox_commit.sh");;
        Psi_BCC_*.npy|*.npy|*.npz) _violations+=("$f -> Runs/seeds/$base");;
        *.tex.txt) _violations+=("$f -> Docs/math/$base");;
    esac
done
if [[ ${#_violations[@]} -gt 0 ]]; then
    echo "[sandbox_commit] REPO_LAYOUT violation:" >&2
    for v in "${_violations[@]}"; do echo "  X $v" >&2; done
    exit 8
fi

echo "[sandbox_commit v2.0] HEAD branch  : $BRANCH_REF"
echo "[sandbox_commit v2.0] Parent SHA  : $PARENT_SHA"
echo "[sandbox_commit v2.0] Files to add: ${#FILES[@]}"

# -------------------- stale-lock truncation (>5 min) --------------------
_truncate_stale_lock() {
    local lock="$1"
    [[ -e "$lock" ]] || return 0
    local mt
    mt=$(stat -c %Y "$lock" 2>/dev/null || stat -f %m "$lock" 2>/dev/null || echo 0)
    local age=$(( $(date +%s) - mt ))
    if [[ $age -gt 300 ]]; then
        echo "[sandbox_commit v2.0] truncating stale lock $lock (age ${age}s)"
        : > "$lock" 2>/dev/null || true
    fi
}
_truncate_stale_lock ".git/index.lock"
_truncate_stale_lock ".git/HEAD.lock"
_truncate_stale_lock "$BRANCH_FILE.lock"

# -------------------- temp index + stage --------------------
TMP_IDX="/tmp/sandbox_commit_idx_$$"
trap 'rm -f "$TMP_IDX" 2>/dev/null || true' EXIT
export GIT_INDEX_FILE="$TMP_IDX"

git read-tree HEAD || { echo "Error: read-tree failed" >&2; exit 5; }

echo "[sandbox_commit v2.0] Staging files..."
for f in "${FILES[@]}"; do
    [[ -e "$f" ]] || { echo "  [skip] $f"; continue; }
    git add "$f" 2>&1 | grep -v 'unable to unlink' \
                      | grep -v 'LF will be replaced' \
                      | grep -v 'original line endings' | head -3
done

N_STAGED=$(git diff --cached --name-only | wc -l)
[[ "$N_STAGED" -eq 0 ]] && { echo "Nothing to commit."; exit 0; }
echo "[sandbox_commit v2.0] $N_STAGED file(s) staged."

# -------------------- write tree + commit --------------------
TREE_SHA=$(git write-tree)
[[ -n "$TREE_SHA" ]] || { echo "Error: write-tree failed" >&2; exit 6; }
echo "[sandbox_commit v2.0] Tree SHA   : $TREE_SHA"

COMMIT_SHA=$(echo "$MSG" | git -c user.email="${GIT_AUTHOR_EMAIL:-jtkor@outlook.com}" \
                                -c user.name="${GIT_AUTHOR_NAME:-Jusang Lee}" \
                              commit-tree "$TREE_SHA" -p "$PARENT_SHA")
[[ -n "$COMMIT_SHA" ]] || { echo "Error: commit-tree failed" >&2; exit 6; }
echo "[sandbox_commit v2.0] Commit SHA : $COMMIT_SHA"

# -------------------- direct ref update (bypass HEAD.lock) --------------------
if ! echo "$COMMIT_SHA" > "$BRANCH_FILE" 2>/dev/null; then
    echo "Error: direct write to $BRANCH_FILE failed." >&2
    echo "       Run PowerShell: Remove-Item -Force $BRANCH_FILE.lock" >&2
    exit 7
fi

AFTER=$(git rev-parse HEAD 2>/dev/null || cat "$BRANCH_FILE" | tr -d '[:space:]')
[[ "$AFTER" == "$COMMIT_SHA" ]] || { echo "Error: ref update did not stick" >&2; exit 7; }

echo "[sandbox_commit v2.0] [OK] ${COMMIT_SHA:0:10} -> $BRANCH_REF"
echo ""
git diff --stat "$PARENT_SHA" "$COMMIT_SHA" 2>&1 | tail -12

exit 0

# ---------------------------------------------------------------------
# sandbox_commit_v2_0_eof_sentinel_DO_NOT_REMOVE
