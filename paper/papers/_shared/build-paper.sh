#!/usr/bin/env bash
# =====================================================================
# TECT canonical paper build script (bash, v2.0)
# =====================================================================
# Usage:
#   bash _shared/build-paper.sh <PaperStem> [--clean] [--no-bibtex] [--quiet]
#
# <PaperStem> is the path WITHOUT the .tex extension, e.g.
#   Paper-03-Pillar3-Emergent-Gravity/Paper-03
#
# Smart pass-counting:
#   pass 1 : pdflatex generates .aux
#   bibtex : run only if (a) source contains \bibliography{} AND (b) .bbl is stale
#   pass 2 : pdflatex resolves \ref / \cref forward references
#   pass 3 : run only if pass-2 .log still reports undefined references
#
# Exit codes:
#   0  build succeeded.   1  pdflatex pass 1 failed.   2  bibtex failed.
#   3  pdflatex pass 2 failed.   4  pdflatex extra-pass failed.   5  no PDF.
# =====================================================================
set -e

CLEAN=0; NO_BIBTEX=0; QUIET=0; PAPER_STEM=""
MAX_REF_PASSES=3

while [ $# -gt 0 ]; do
  case "$1" in
    --clean)      CLEAN=1; shift;;
    --no-bibtex)  NO_BIBTEX=1; shift;;
    --quiet)      QUIET=1; shift;;
    --max-ref-passes) MAX_REF_PASSES="$2"; shift 2;;
    -h|--help)
      sed -n '1,30p' "$0"; exit 0;;
    *)
      if [ -z "$PAPER_STEM" ]; then PAPER_STEM="$1"; shift
      else echo "[TECT-build] unknown arg: $1" >&2; exit 64; fi;;
  esac
done

[ -n "$PAPER_STEM" ] || { echo "[TECT-build] missing <PaperStem>" >&2; exit 64; }

BASE="$(basename "$PAPER_STEM")"
DIR="$(dirname "$PAPER_STEM")"
[ -d "$DIR" ] || { echo "[TECT-build] dir not found: $DIR" >&2; exit 5; }

cd "$DIR"
SRC="${BASE}.tex"
[ -f "$SRC" ] || { echo "[TECT-build] source not found: ${DIR}/${SRC}" >&2; exit 5; }

BUILD_LOG="${BASE}.build.log"
echo "# TECT build log for $BASE ($(date -Iseconds))" > "$BUILD_LOG"

phase() {
  if [ "$QUIET" = 0 ]; then echo "[TECT-build] $1"; fi
  echo "[TECT-build] $1" >> "$BUILD_LOG"
}

run_latex() {
  # Capture stdout to BUILD_LOG; stream tail to console if not quiet.
  local cmd="$1"; shift
  local tmp; tmp="$(mktemp)"
  "$cmd" "$@" > "$tmp" 2>&1; rc=$?
  cat "$tmp" >> "$BUILD_LOG"
  if [ "$QUIET" = 0 ]; then tail -n 8 "$tmp" | sed 's/^/  /'; fi
  rm -f "$tmp"
  return $rc
}

count_undef_refs() {
  # Count undefined references / citations in *.log
  local logf="${BASE}.log"
  [ -f "$logf" ] || { echo 0; return; }
  grep -cE "Reference \`[^']+' on page [0-9]+ undefined|Citation \`[^']+' on page [0-9]+ undefined|There were undefined references" "$logf" || true
}

# 0. Optional clean
if [ "$CLEAN" = 1 ]; then
  phase "clean: removing aux/bbl/blg/toc/log/out for $BASE"
  rm -f "${BASE}.aux" "${BASE}.bbl" "${BASE}.blg" "${BASE}.toc" "${BASE}.log" \
        "${BASE}.out" "${BASE}.run.xml" "${BASE}.synctex.gz" \
        "${BASE}.fls" "${BASE}.fdb_latexmk"
fi

# 1. pdflatex pass 1
phase "pass 1: pdflatex $BASE"
if ! run_latex pdflatex -interaction=nonstopmode -halt-on-error "$SRC"; then
  phase "ERROR: pdflatex pass 1 failed; see $BUILD_LOG"; exit 1
fi

# 2. bibtex (conditional)
NEED_BIBTEX=0
if [ "$NO_BIBTEX" = 0 ]; then
  if grep -q '\\bibliography{' "$SRC"; then
    # Skip bibtex if source has no \cite{} commands at all (bibtex would
    # emit "I found no \citation commands" + exit 1, spurious noise).
    if grep -qE '\\cite[a-z]*\{' "$SRC"; then
      if [ ! -f "${BASE}.bbl" ] || [ "$SRC" -nt "${BASE}.bbl" ]; then
        NEED_BIBTEX=1
      fi
    else
      phase "bibtex: SKIP (source has \\bibliography{} but zero \\cite{})"
    fi
  fi
fi
if [ "$NEED_BIBTEX" = 1 ]; then
  phase "bibtex $BASE"
  if ! run_latex bibtex "$BASE"; then
    phase "WARN: bibtex returned non-zero (continuing)"
  fi
else
  phase "bibtex: SKIP (no \\bibliography or .bbl up-to-date or --no-bibtex)"
fi

# 3. pdflatex pass 2
phase "pass 2: pdflatex $BASE"
if ! run_latex pdflatex -interaction=nonstopmode -halt-on-error "$SRC"; then
  phase "ERROR: pdflatex pass 2 failed; see $BUILD_LOG"; exit 3
fi

# 3b. extra passes if undefined refs remain
EXTRA=0
while [ "$EXTRA" -lt "$((MAX_REF_PASSES - 1))" ]; do
  UNDEF=$(count_undef_refs)
  [ "$UNDEF" -le 0 ] && break
  EXTRA=$((EXTRA + 1))
  phase "pass $((EXTRA + 2)): pdflatex $BASE (still $UNDEF undefined refs)"
  if ! run_latex pdflatex -interaction=nonstopmode -halt-on-error "$SRC"; then
    phase "ERROR: pdflatex extra pass failed; see $BUILD_LOG"; exit 4
  fi
done

# 4. PDF check
if [ ! -s "${BASE}.pdf" ]; then
  phase "ERROR: no PDF produced for $BASE"; exit 5
fi
SIZE_KB=$(( $(stat -c %s "${BASE}.pdf" 2>/dev/null || stat -f %z "${BASE}.pdf") / 1024 ))
phase "OK: ${DIR}/${BASE}.pdf  (size = ${SIZE_KB} KB)"

UNDEF=$(count_undef_refs)
if [ "$UNDEF" -gt 0 ]; then
  phase "WARN: $UNDEF undefined-reference warnings remain after $((EXTRA + 2)) passes"
fi
exit 0
