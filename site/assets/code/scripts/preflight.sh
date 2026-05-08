#!/bin/bash
# =====================================================================
# preflight.sh v1.0 -- TECT sandbox-session preflight check
#
# PURPOSE : Run at the start of a Cowork session (or before any git
#           operation) to catch Claude-Desktop-crash damage early:
#             (1) stale git locks (truncate if > 5 min old)
#             (2) truncated scripts (delegate to verify_scripts_integrity.sh)
#             (3) basic repo sanity
#
# USAGE   : bash Codes/scripts/preflight.sh
#           [exit 0 means safe to proceed; non-zero means do NOT commit]
# =====================================================================

_PREFLIGHT_SENTINEL="preflight_v1_0_eof_sentinel_DO_NOT_REMOVE"
_self_check() {
    if ! tail -3 "${BASH_SOURCE[0]}" | grep -q "^# ${_PREFLIGHT_SENTINEL}\$"; then
        echo "FATAL: $0 truncated (no EOF sentinel). Restore from git." >&2
        exit 9
    fi
}
_self_check

set -u

echo "=== TECT sandbox preflight v1.0 ==="
echo ""

FAIL=0

# -------------------- (1) repo sanity --------------------
if [[ ! -d .git ]]; then
    echo "  [FAIL] .git/ not present -- run from repo root." >&2
    exit 2
fi

HEAD_REF=$(cat .git/HEAD 2>/dev/null || echo "")
if [[ ! "$HEAD_REF" =~ ^ref:\ refs/heads/.* ]]; then
    echo "  [FAIL] HEAD is not a normal symbolic ref: $HEAD_REF" >&2
    FAIL=1
else
    echo "  [OK]   HEAD: $HEAD_REF"
fi

# -------------------- (2) stale git locks --------------------
echo ""
echo "-- stale-lock scan --"
_scan_lock() {
    local lock="$1"
    [[ -e "$lock" ]] || { echo "  [OK]   $lock (absent)"; return 0; }
    local mtime_epoch
    mtime_epoch=$(stat -c %Y "$lock" 2>/dev/null || stat -f %m "$lock" 2>/dev/null || echo 0)
    local age_sec=$(( $(date +%s) - mtime_epoch ))
    if [[ $age_sec -gt 300 ]]; then
        echo "  [WARN] $lock (age ${age_sec}s > 300s) -- truncating"
        : > "$lock" 2>/dev/null || {
            echo "         [FAIL] could not truncate (WSL permission?)"
            echo "         run PowerShell: Remove-Item -Force $lock"
            FAIL=1
        }
    else
        echo "  [OK?]  $lock (age ${age_sec}s <= 300s; possibly live)"
    fi
}
BRANCH_FILE=".git/$(echo "$HEAD_REF" | sed 's/^ref: //')"
_scan_lock ".git/index.lock"
_scan_lock ".git/HEAD.lock"
_scan_lock "$BRANCH_FILE.lock"

# -------------------- (3) script integrity --------------------
echo ""
echo "-- script integrity --"
if [[ -x Codes/scripts/verify_scripts_integrity.sh ]] || [[ -f Codes/scripts/verify_scripts_integrity.sh ]]; then
    if ! bash Codes/scripts/verify_scripts_integrity.sh; then
        FAIL=1
    fi
else
    echo "  [WARN] verify_scripts_integrity.sh missing"
    FAIL=1
fi

# -------------------- summary --------------------
echo ""
if [[ $FAIL -eq 0 ]]; then
    echo "=== [OK] preflight passed -- safe to commit ==="
    exit 0
else
    echo "=== [FAIL] preflight found issues -- see Docs/policy/CRASH_RECOVERY.md ==="
    exit 1
fi

# ---------------------------------------------------------------------
# EOF SENTINEL
# ---------------------------------------------------------------------
# preflight_v1_0_eof_sentinel_DO_NOT_REMOVE
