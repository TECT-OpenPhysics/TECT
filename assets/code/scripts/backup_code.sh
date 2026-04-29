#!/usr/bin/env bash
# =====================================================================
# backup_code.sh — Snapshot a code file BEFORE editing it.
#
# Usage:
#   bash Codes/scripts/backup_code.sh <path/to/file.py> [--version vX.Y.Z]
#
# Behaviour:
#   1. Reads the version from the file's __version__ string OR from
#      the optional --version argument.
#   2. Creates a sibling backup at:
#        <stem>.old.<version>.<ext>
#      e.g. continuation_mu2_v25.py v2.6.7 →
#           continuation_mu2_v25.old.v2.6.7.py
#   3. If the backup already exists, refuses (idempotent — prevents
#      double-backup of the same version).
#   4. Records the backup in Codes/_backup_log.md with date + git SHA.
#
# Rationale (Docs/policy/CODE_BACKUP_POLICY.md):
#   Git already preserves history, BUT operational debugging / rollback
#   often needs the file present in the working tree at a specific
#   labelled version, NOT a git checkout step. The .old.<version>.<ext>
#   pattern keeps the labelled snapshot side-by-side for fast access.
#
# Author: Jusang Lee + collaboration (2026-04-29).
# =====================================================================

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <path/to/file> [--version vX.Y.Z]" >&2
    exit 1
fi

src="$1"
shift

if [ ! -f "$src" ]; then
    echo "[backup_code] source not found: $src" >&2
    exit 2
fi

# Parse optional --version argument
explicit_version=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --version)
            shift
            explicit_version="$1"
            shift
            ;;
        *)
            echo "[backup_code] unknown argument: $1" >&2
            exit 3
            ;;
    esac
done

# Auto-detect version from __version__ = "X.Y.Z" or from header comment.
auto_version=""
if [ -z "$explicit_version" ]; then
    auto_version=$(
        grep -oE '__version__\s*=\s*"[^"]+"' "$src" 2>/dev/null \
            | head -1 \
            | sed -E 's/__version__\s*=\s*"([^"]+)"/\1/'
    )
    if [ -z "$auto_version" ]; then
        # Try header pattern e.g. "Module version: v2.6.7"
        auto_version=$(
            grep -oE '[Mm]odule version[[:space:]]*[:=][[:space:]]*v?[0-9]+\.[0-9]+(\.[0-9]+)?' "$src" 2>/dev/null \
                | head -1 \
                | grep -oE 'v?[0-9]+\.[0-9]+(\.[0-9]+)?'
        )
    fi
fi

version="${explicit_version:-$auto_version}"

if [ -z "$version" ]; then
    echo "[backup_code] could not determine version. Pass --version vX.Y.Z." >&2
    exit 4
fi

# Normalise: ensure leading 'v'
case "$version" in
    v*) ;;
    *) version="v$version" ;;
esac

# Build backup path: <dirname>/<stem>.old.<version>.<ext>
dir=$(dirname "$src")
file=$(basename "$src")
stem="${file%.*}"
ext="${file##*.}"
if [ "$stem" = "$file" ]; then
    # No extension
    backup="$dir/$file.old.$version"
else
    backup="$dir/$stem.old.$version.$ext"
fi

if [ -e "$backup" ]; then
    echo "[backup_code] backup already exists: $backup (refusing to overwrite)" >&2
    exit 5
fi

cp -p "$src" "$backup"
echo "[backup_code] $src -> $backup"

# Append to _backup_log.md (root of Codes/) for trail
log="Codes/_backup_log.md"
if [ ! -f "$log" ]; then
    cat > "$log" <<EOF
# TECT Code Backup Log

Append-only record of pre-edit code snapshots created via
\`Codes/scripts/backup_code.sh\` (per \`Docs/policy/CODE_BACKUP_POLICY.md\`).
Each entry = one snapshot. Do NOT edit by hand; \`backup_code.sh\` appends
on every successful backup.

| Date (UTC) | Source | Backup | Version | Git SHA |
|---|---|---|---|---|
EOF
fi

git_sha=$(git rev-parse --short=10 HEAD 2>/dev/null || echo "unknown")
date_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "| $date_utc | \`$src\` | \`$backup\` | $version | $git_sha |" >> "$log"

echo "[backup_code] log updated: $log"
exit 0
