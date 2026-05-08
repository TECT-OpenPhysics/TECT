#!/usr/bin/env bash
# =====================================================================
# TECT — Master paper-track build pipeline (bash, v2.0)
# =====================================================================
# Builds every TeX paper across the four canonical categories:
#   Docs/papers/papers/Paper-*/Paper-*.tex
#   Docs/papers/auxiliary/Auxiliary-*/Auxiliary-*.tex
#   Docs/papers/top_impact/Paper-TI-*/Paper-TI-*.tex
#   Docs/papers/epochs/Epoch-*/Epoch-*.tex
#
# Usage (from repo root):
#   bash Codes/scripts/build-all-papers.sh
#   bash Codes/scripts/build-all-papers.sh --filter 'Paper-0[0-3]'
#   bash Codes/scripts/build-all-papers.sh --categories papers,top_impact --clean
#   bash Codes/scripts/build-all-papers.sh --quiet --jobs 4
#   bash Codes/scripts/build-all-papers.sh --list-only
#
# Flags:
#   --filter <regex>       only stems matching the regex
#   --categories <csv>     subset of {papers,auxiliary,top_impact,epochs}
#   --clean                pass --clean to per-paper builder
#   --no-bibtex            pass --no-bibtex to per-paper builder
#   --quiet                pass --quiet to per-paper builder
#   --list-only            print target list and exit
#   --jobs N               parallel build (xargs -P N), default 1
#   --log-dir <dir>        master log dir (default: Runs/build_logs/)
# =====================================================================
set -e

FILTER=""
CATEGORIES="papers,auxiliary,top_impact,epochs"
CLEAN=0; NO_BIBTEX=0; QUIET=0; LIST_ONLY=0
JOBS=1
LOG_DIR=""

while [ $# -gt 0 ]; do
  case "$1" in
    --filter)      FILTER="$2"; shift 2;;
    --categories)  CATEGORIES="$2"; shift 2;;
    --clean)       CLEAN=1; shift;;
    --no-bibtex)   NO_BIBTEX=1; shift;;
    --quiet)       QUIET=1; shift;;
    --list-only)   LIST_ONLY=1; shift;;
    --jobs)        JOBS="$2"; shift 2;;
    --log-dir)     LOG_DIR="$2"; shift 2;;
    -h|--help)     sed -n '1,30p' "$0"; exit 0;;
    *) echo "unknown arg: $1" >&2; exit 64;;
  esac
done

# ---------------------------------------------------------------------
# Repo root
# ---------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PAPERS_ROOT="$REPO_ROOT/Docs/papers"
[ -d "$PAPERS_ROOT" ] || { echo "[FATAL] $PAPERS_ROOT missing" >&2; exit 6; }

BUILDER="$PAPERS_ROOT/papers/_shared/build-paper.sh"
[ -f "$BUILDER" ] || { echo "[FATAL] $BUILDER missing" >&2; exit 6; }

# ---------------------------------------------------------------------
# Build target list (TAB-separated: category<TAB>dir<TAB>stem)
# ---------------------------------------------------------------------
TARGETS_FILE="$(mktemp)"
trap 'rm -f "$TARGETS_FILE"' EXIT

IFS=',' read -r -a CAT_ARR <<< "$CATEGORIES"
for cat in "${CAT_ARR[@]}"; do
  case "$cat" in
    papers)     ROOT="$PAPERS_ROOT/papers";     PATTERN="Paper-*";;
    auxiliary)  ROOT="$PAPERS_ROOT/auxiliary";  PATTERN="Auxiliary-*";;
    top_impact) ROOT="$PAPERS_ROOT/top_impact"; PATTERN="Paper-TI-*";;
    epochs)     ROOT="$PAPERS_ROOT/epochs";     PATTERN="Epoch-*";;
    *) echo "[WARN] unknown category: $cat" >&2; continue;;
  esac
  [ -d "$ROOT" ] || { echo "[WARN] missing: $ROOT" >&2; continue; }
  while IFS= read -r d; do
    base="$(basename "$d")"
    case "$base" in _shared|_legacy) continue;; esac
    while IFS= read -r tex; do
      stem="$(basename "$tex" .tex)"
      [ -n "$FILTER" ] && ! echo "$stem $base" | grep -qE "$FILTER" && continue
      printf "%s\t%s\t%s\n" "$cat" "$d" "$stem" >> "$TARGETS_FILE"
    done < <(find "$d" -maxdepth 1 -type f -name "${PATTERN}.tex" 2>/dev/null | sort)
  done < <(find "$ROOT" -maxdepth 1 -mindepth 1 -type d -name "$PATTERN" 2>/dev/null | sort)
done

N_TARGETS=$(wc -l < "$TARGETS_FILE")
echo "[TECT-build-all] $N_TARGETS targets selected"

if [ "$LIST_ONLY" = 1 ]; then
  awk -F'\t' '{ printf "  [%s] %s  (%s)\n", $1, $3, $2 }' "$TARGETS_FILE"
  exit 0
fi

[ "$N_TARGETS" -gt 0 ] || { echo "[INFO] no targets matched"; exit 0; }

# ---------------------------------------------------------------------
# Per-target build runner (called by xargs)
# ---------------------------------------------------------------------
RESULTS_FILE="$(mktemp)"
trap 'rm -f "$TARGETS_FILE" "$RESULTS_FILE"' EXIT

build_one() {
  local cat="$1" dir="$2" stem="$3"
  local stem_path="$dir/$stem"
  local args=("$stem_path")
  [ "$CLEAN" = 1 ]     && args+=(--clean)
  [ "$NO_BIBTEX" = 1 ] && args+=(--no-bibtex)
  [ "$QUIET" = 1 ]     && args+=(--quiet)
  local t0; t0=$(date +%s%N)
  bash "$BUILDER" "${args[@]}"
  local rc=$?
  local t1; t1=$(date +%s%N)
  local ms=$(( (t1 - t0) / 1000000 ))
  local pdf="$dir/$stem.pdf"
  local sz=0
  [ -f "$pdf" ] && sz=$(stat -c %s "$pdf" 2>/dev/null || stat -f %z "$pdf")
  local status="OK"; [ "$rc" -ne 0 ] && status="FAIL"
  printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$cat" "$stem" "$dir" "$rc" "$status" "$sz" "$ms" >> "$RESULTS_FILE"
  return $rc
}
export -f build_one
export BUILDER CLEAN NO_BIBTEX QUIET RESULTS_FILE

GRAND_T0=$(date +%s)

if [ "$JOBS" -ge 2 ]; then
  echo "[TECT-build-all] running with --jobs $JOBS (xargs -P)"
  awk -F'\t' '{ print $1 "\x1F" $2 "\x1F" $3 }' "$TARGETS_FILE" | \
    xargs -P "$JOBS" -I {} bash -c '
      IFS=$'"'"'\x1F'"'"' read -r cat dir stem <<< "{}"
      build_one "$cat" "$dir" "$stem"
    ' || true
else
  i=0
  while IFS=$'\t' read -r cat dir stem; do
    i=$((i+1))
    echo ""
    echo "============================================================"
    echo "[$i/$N_TARGETS] $cat :: $stem"
    echo "============================================================"
    build_one "$cat" "$dir" "$stem" || true
  done < "$TARGETS_FILE"
fi

GRAND_T1=$(date +%s)
ELAPSED=$((GRAND_T1 - GRAND_T0))

# ---------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------
echo ""
echo "============================================================"
echo "  Summary  (${ELAPSED}s elapsed)"
echo "============================================================"
N_OK=$(awk -F'\t' '$5=="OK"{n++} END{print n+0}' "$RESULTS_FILE")
N_FAIL=$(awk -F'\t' '$5=="FAIL"{n++} END{print n+0}' "$RESULTS_FILE")
N_TOTAL=$(wc -l < "$RESULTS_FILE")
printf "%-12s %-46s %-6s %-4s %10s %8s\n" "Category" "Stem" "Status" "Exit" "PDF KB" "ms"
printf "%-12s %-46s %-6s %-4s %10s %8s\n" "----" "----" "----" "----" "----" "----"
awk -F'\t' '{
  printf "%-12s %-46s %-6s %-4s %10.1f %8d\n", $1, $2, $5, $4, $6/1024, $7
}' "$RESULTS_FILE" | sort
echo ""
echo "[Total] OK=$N_OK  FAIL=$N_FAIL  ($N_TOTAL files)"

# Group by category
echo ""
awk -F'\t' '{ tot[$1]++; if($5=="OK") ok[$1]++; else fail[$1]++ }
END {
  for (c in tot) printf "  [%-12s] OK=%2d  FAIL=%2d  total=%2d\n", c, ok[c]+0, fail[c]+0, tot[c]
}' "$RESULTS_FILE" | sort

if [ "$N_FAIL" -gt 0 ]; then
  echo ""
  echo "[FAILED targets — see *.build.log]"
  awk -F'\t' '$5=="FAIL"{ printf "  %s  %s  exit=%s  log=%s/%s.build.log\n", $1, $2, $4, $3, $2 }' "$RESULTS_FILE"
fi

# ---------------------------------------------------------------------
# JSON log
# ---------------------------------------------------------------------
[ -z "$LOG_DIR" ] && LOG_DIR="$REPO_ROOT/Runs/build_logs"
mkdir -p "$LOG_DIR"
TS=$(date +"%Y%m%d-%H%M%S")
JSON="$LOG_DIR/build-$TS.json"

{
  echo "{"
  echo "  \"schema\": \"tect-build-all-papers-v2.0\","
  echo "  \"timestamp\": \"$(date -Iseconds)\","
  echo "  \"elapsed_sec\": $ELAPSED,"
  echo "  \"filter\": \"$FILTER\","
  echo "  \"categories\": \"$CATEGORIES\","
  echo "  \"clean\": $CLEAN, \"no_bibtex\": $NO_BIBTEX, \"jobs\": $JOBS,"
  echo "  \"total\": $N_TOTAL, \"ok\": $N_OK, \"fail\": $N_FAIL,"
  echo "  \"results\": ["
  awk -F'\t' '{
    printf "    {\"category\":\"%s\",\"stem\":\"%s\",\"dir\":\"%s\",\"exit_code\":%s,\"status\":\"%s\",\"pdf_bytes\":%s,\"duration_ms\":%s}", $1,$2,$3,$4,$5,$6,$7
    if (NR < TOT) printf ",\n"; else printf "\n"
  }' TOT="$N_TOTAL" "$RESULTS_FILE"
  echo "  ]"
  echo "}"
} > "$JSON"
echo ""
echo "[log] $JSON"

[ "$N_FAIL" = 0 ] && exit 0 || exit 1
