#!/bin/bash
# =====================================================================
# verify_scripts_integrity.sh v1.0 -- batch EOF-sentinel integrity check
#                                     across critical scripts.
#
# PURPOSE : Detect Claude-Desktop-crash-induced truncation in any
#           script registered below. Each script must carry a
#           final-line EOF sentinel of the form
#             # <script_basename_without_ext>_eof_sentinel_DO_NOT_REMOVE
#           (or any custom pattern, see REGISTRY).
#
#           Run at session start (from preflight.sh) or manually.
#
# USAGE   : bash Codes/scripts/verify_scripts_integrity.sh [--fix-suggest]
#
# EXIT    : 0 all good;  1 one or more scripts truncated;  2 usage error
# =====================================================================

_VERIFY_SENTINEL="verify_scripts_integrity_v1_0_eof_sentinel_DO_NOT_REMOVE"
_self_check() {
    if ! tail -3 "${BASH_SOURCE[0]}" | grep -q "^# ${_VERIFY_SENTINEL}\$"; then
        echo "FATAL: $0 is truncated (no EOF sentinel). Restore from git." >&2
        exit 9
    fi
}
_self_check

set -u
FIX_SUGGEST=0
if [[ "${1:-}" == "--fix-suggest" ]]; then FIX_SUGGEST=1; fi

# ---------------------------------------------------------------------
# REGISTRY  (script_path, expected_sentinel_string)
# Add entries here for any script whose truncation could corrupt repo state.
# ---------------------------------------------------------------------
declare -a REGISTRY=(
    "Codes/scripts/sandbox_commit.sh|sandbox_commit_v2_0_eof_sentinel_DO_NOT_REMOVE"
    "Codes/scripts/verify_scripts_integrity.sh|verify_scripts_integrity_v1_0_eof_sentinel_DO_NOT_REMOVE"
    "Codes/scripts/preflight.sh|preflight_v1_0_eof_sentinel_DO_NOT_REMOVE"
)

FAIL=0
echo "=== verify_scripts_integrity v1.0 ==="
echo ""

# Check sentinel-registered scripts (strict: missing sentinel => FAIL)
echo "-- sentinel-registered scripts --"
for entry in "${REGISTRY[@]}"; do
    IFS='|' read -r path sentinel <<< "$entry"
    if [[ ! -f "$path" ]]; then
        echo "  [MISSING] $path"
        FAIL=1
        continue
    fi
    if tail -5 "$path" | grep -qF "# ${sentinel}"; then
        echo "  [OK]      $path"
    else
        echo "  [TRUNCAT] $path  (missing sentinel '${sentinel}')"
        FAIL=1
        if [[ $FIX_SUGGEST -eq 1 ]]; then
            echo "      fix: git checkout HEAD -- $path"
        fi
    fi
done

# Non-destructive truncation hint for Python: only check for very obvious
# signs (zero length, ends with unclosed triple-quoted string). Python
# has too many legitimate endings (bare `pass`, bare variable names in
# __all__, etc.) to do reliable heuristics, so we stay conservative.
echo ""
echo "-- conservative Python truncation hint (zero-byte only) --"
while IFS= read -r py; do
    if [[ ! -s "$py" ]]; then
        echo "  [ZERO-B]  $py  (empty file)"
        FAIL=1
    fi
done < <(find Codes/ -name '*.py' 2>/dev/null)

echo ""
if [[ $FAIL -eq 0 ]]; then
    echo "=== [OK] all checked scripts look intact ==="
    exit 0
else
    echo "=== [FAIL] one or more scripts look truncated ==="
    echo "    Run with --fix-suggest for per-file recovery hints."
    echo "    Or: bash Codes/scripts/verify_scripts_integrity.sh --fix-suggest"
    exit 1
fi

# ---------------------------------------------------------------------
# EOF SENTINEL
# ---------------------------------------------------------------------
# verify_scripts_integrity_v1_0_eof_sentinel_DO_NOT_REMOVE
