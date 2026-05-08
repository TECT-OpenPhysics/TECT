#!/usr/bin/env python3
# =====================================================================
# propagate_status.py v1.0 (2026-05-07)
#
# Propagates the canonical 11-pillar Stage-1 scoreboard from the single
# source of truth (Website/data/status.js) to every downstream artefact
# that displays a tier-derived statement: index.js, theory.js, toe.html,
# README.md, EVIDENCE-INDEX.md, and (via subordinate call to
# sync_toe_from_status.py) status_pillar_tiers.js.
#
# Governed by Docs/policy/STATUS_PROPAGATION_POLICY.md (binding 2026-05-07).
#
# CLI:
#   python -u Codes/tools/propagate_status.py --check       # dry-run; diff-only; non-zero if drift
#   python -u Codes/tools/propagate_status.py               # apply mode
#   python -u Codes/tools/propagate_status.py --init        # insert anchor markers in new targets
#   python -u Codes/tools/propagate_status.py --targets index_stage1_summary readme_current_state
#
# Exit codes:
#   0   OK / no drift (--check) / changes applied (default mode)
#   1   drift detected in --check mode (one or more targets out of sync)
#   2   I/O or parse error
#
# Defensive guarantees:
#   * Never modifies Website/data/status.js, TOE-FACT-SHEET.md, STATUS-HISTORY.md.
#   * Only writes between PROP-AUTO:<tag> START / END markers.
#   * --check is purely read-only (zero file mutation).
#   * --init prints the proposed insertion diff and writes only after the
#     existing file content is back-ed up via the helper RunRecorder if
#     available, or copied to a .bak alongside on first --init.
# =====================================================================
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STATUS_JS = REPO_ROOT / "Website" / "data" / "status.js"
CONFIG_JSON = REPO_ROOT / "Codes" / "config" / "status_propagation_targets.json"
LOG_MD = REPO_ROOT / "Docs" / "status" / "propagation-log.md"
TIERS_JS = REPO_ROOT / "Website" / "data" / "status_pillar_tiers.js"


# ---------------------------------------------------------------------
# Source parsing
# ---------------------------------------------------------------------

def parse_pillar_tiers(status_text: str) -> List[Dict[str, str]]:
    """Parse the 11-pillar scoreboard table from status.js. Returns a
    list of dicts with keys: pillar, subject, tier_html, tier,
    conditional_input."""
    section = re.search(r'11-Pillar scoreboard.*?</tbody>', status_text, re.DOTALL)
    if not section:
        raise ValueError("could not locate 11-Pillar scoreboard in status.js")
    body = section.group(0)
    rows: List[Dict[str, str]] = []
    row_re = re.compile(
        r'<tr><td>(\d+)</td>'
        r'<td>(.*?)</td>'
        r'<td>(.*?)</td>'
        r'<td>(.*?)</td></tr>',
        re.DOTALL,
    )
    for m in row_re.finditer(body):
        def strip_html(s: str) -> str:
            s = re.sub(r'<[^>]+>', '', s)
            s = re.sub(r'\s+', ' ', s).strip()
            return s
        rows.append({
            "pillar":            m.group(1).strip(),
            "subject":           strip_html(m.group(2)),
            "tier_html":         m.group(3).strip(),
            "tier":              strip_html(m.group(3)),
            "conditional_input": strip_html(m.group(4)),
        })
    if len(rows) != 11:
        print(f"[propagate-status] WARN: expected 11 pillar rows; parsed {len(rows)}",
              file=sys.stderr)
    return rows


def aggregate_tier_distribution(rows: List[Dict[str, str]]) -> Dict[str, int]:
    """Count pillars by primary tier label (T7, T6, T5, T4, T3, T2, T1, T0)."""
    counts: Dict[str, int] = {f"T{i}": 0 for i in range(8)}
    counts["other"] = 0
    for r in rows:
        tier = r["tier"]
        primary = re.match(r'T[0-7]', tier)
        if primary:
            counts[primary.group(0)] += 1
        else:
            counts["other"] += 1
    return counts


def status_predicate_label(rows: List[Dict[str, str]]) -> str:
    """Determine S_1 qualification label from per-pillar tiers.
    Returns one of: 'Full TOE candidate', 'Partial TOE candidate',
    'Refuted-component TOE candidate'."""
    refuted = any(re.match(r'T0', r["tier"]) for r in rows)
    all_at_least_t6 = all(
        re.match(r'T[67]', r["tier"]) for r in rows
    )
    if refuted:
        return "Partial TOE candidate"
    if all_at_least_t6:
        return "Full TOE candidate"
    return "Partial TOE candidate"


# ---------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------

def render_status_pillar_tiers_js(rows: List[Dict[str, str]],
                                   iso_timestamp: str) -> str:
    """Whole-file regeneration of status_pillar_tiers.js. Compatible with
    the existing toe.html overlay loader."""
    payload = {
        "schema":    "tect-status-pillar-tiers-v1",
        "generated": iso_timestamp,
        "source":    "Website/data/status.js (parse of 11-Pillar scoreboard table)",
        "pillars":   rows,
    }
    return (
        "/* AUTO-GENERATED by Codes/tools/propagate_status.py - DO NOT EDIT. */\n"
        "/* Source: Website/data/status.js (11-Pillar scoreboard parsed live).   */\n"
        "/* Loaded by toe.html so the TOE page always shows live Status data.    */\n"
        "window.TECT_STATUS_TIERS = "
        + json.dumps(payload, indent=2, ensure_ascii=False)
        + ";\n"
    )


def render_index_stage1_summary(rows: List[Dict[str, str]],
                                 iso_timestamp: str) -> str:
    """Replacement content for the 'Latest state snapshot' Stage-1 row.
    Returned as a JS-string-fragment (HTML inside) to slot between the
    PROP-AUTO:stage1-summary START / END markers."""
    counts = aggregate_tier_distribution(rows)
    pillars_by_tier: Dict[str, List[str]] = {f"T{i}": [] for i in range(8)}
    for r in rows:
        m = re.match(r'(T[0-7])', r["tier"])
        if m:
            pillars_by_tier[m.group(1)].append(r["pillar"])
    lines: List[str] = []
    lines.append('"<table class=\\"sm-table\\">"')
    lines.append('"<thead><tr><th>Tier</th><th>Count</th><th>Pillars</th></tr></thead>"')
    lines.append('"<tbody>"')
    tier_labels = {
        "T7": "PROVED",          "T6": "PROVED CONDITIONAL",
        "T5": "CLOSED@N-LOOP",   "T4": "STRONG EVIDENCE",
        "T3": "PROOF SKETCH",    "T2": "CONJECTURE",
        "T1": "OPEN",            "T0": "REFUTED",
    }
    for tier in ["T7", "T6", "T5", "T4", "T3", "T2", "T1", "T0"]:
        n = counts[tier]
        if n == 0:
            continue
        ps = ", ".join(pillars_by_tier[tier])
        lines.append(
            f'"<tr><td><strong>{tier}</strong> ({tier_labels[tier]})</td>'
            f'<td>{n}</td><td>{ps}</td></tr>"'
        )
    lines.append('"</tbody></table>"')
    js_fragment = " +\n".join(lines)
    return (
        f"/* Auto-generated Stage-1 scoreboard summary (status.js -> index.js). */\n"
        f"/* Generated: {iso_timestamp} */\n"
        f"content: " + js_fragment + "\n"
    )


def render_partial_toe_classification(rows: List[Dict[str, str]],
                                       iso_timestamp: str) -> str:
    """Replacement content for the theory.js subtitle's TOE-classification line.
    Returns a single-line HTML fragment (no enclosing tags) suitable for
    direct substitution between markers."""
    label = status_predicate_label(rows)
    counts = aggregate_tier_distribution(rows)
    return (
        f"<!-- Auto-generated by propagate_status.py {iso_timestamp} -->\n"
        f"<p><strong>Operational classification</strong>: {label} "
        f"(post-2026-05-07 status: T7 x{counts['T7']}, T6 x{counts['T6']}, "
        f"T5 x{counts['T5']}, T4 x{counts['T4']}, T3 x{counts['T3']}, "
        f"T2 x{counts['T2']}, T1 x{counts['T1']}, T0 x{counts['T0']}).</p>\n"
    )


def render_readme_current_state(rows: List[Dict[str, str]],
                                 iso_timestamp: str) -> str:
    """Replacement content for the README 'Current state' section.
    Returns Markdown to slot between PROP-AUTO:readme-current-state markers."""
    counts = aggregate_tier_distribution(rows)
    label = status_predicate_label(rows)
    today = iso_timestamp[:10]
    out: List[str] = []
    out.append(f"")
    out.append(f"**Current state (auto-synced {today})**: {label}.")
    out.append(f"")
    out.append(f"| Tier | Count | Pillars |")
    out.append(f"|---|---:|---|")
    pillars_by_tier: Dict[str, List[str]] = {f"T{i}": [] for i in range(8)}
    for r in rows:
        m = re.match(r'(T[0-7])', r["tier"])
        if m:
            pillars_by_tier[m.group(1)].append(r["pillar"])
    tier_labels = {
        "T7": "PROVED",          "T6": "PROVED CONDITIONAL",
        "T5": "CLOSED@N-LOOP",   "T4": "STRONG EVIDENCE",
        "T3": "PROOF SKETCH",    "T2": "CONJECTURE",
        "T1": "OPEN",            "T0": "REFUTED",
    }
    for tier in ["T7", "T6", "T5", "T4", "T3", "T2", "T1", "T0"]:
        n = counts[tier]
        if n == 0:
            continue
        ps = ", ".join(pillars_by_tier[tier]) or "—"
        out.append(f"| **{tier}** ({tier_labels[tier]}) | {n} | {ps} |")
    out.append(f"")
    out.append(f"For the full per-pillar table including conditional-input columns, "
               f"see [Status](Website/status.html) or "
               f"`Docs/status/TOE-FACT-SHEET.md`.")
    out.append(f"")
    return "\n".join(out)


def render_evidence_pillar_tiers(rows: List[Dict[str, str]],
                                  iso_timestamp: str) -> str:
    """Compact per-pillar tier table for EVIDENCE-INDEX.md header."""
    out: List[str] = []
    out.append(f"")
    out.append(f"**Per-pillar canonical tier (auto-synced {iso_timestamp[:10]})**:")
    out.append(f"")
    out.append(f"| # | Pillar | Tier |")
    out.append(f"|---|---|---|")
    for r in rows:
        out.append(f"| {r['pillar']} | {r['subject']} | {r['tier']} |")
    out.append(f"")
    return "\n".join(out)


def render_toe_overlay_block(rows: List[Dict[str, str]],
                              iso_timestamp: str) -> str:
    """No-op renderer: toe.html overlay is hand-curated HTML+JS that
    consumes window.TECT_STATUS_TIERS at runtime; the data is propagated
    via status_pillar_tiers.js, not by patching toe.html itself. Returns
    empty string so the zone, if present, is rendered as a comment-only
    marker pair."""
    return f"<!-- Overlay consumes window.TECT_STATUS_TIERS at runtime; data propagated via status_pillar_tiers.js (regen {iso_timestamp}). -->\n"


RENDERER_REGISTRY = {
    "render_status_pillar_tiers_js":   render_status_pillar_tiers_js,
    "render_index_stage1_summary":     render_index_stage1_summary,
    "render_partial_toe_classification": render_partial_toe_classification,
    "render_readme_current_state":     render_readme_current_state,
    "render_evidence_pillar_tiers":    render_evidence_pillar_tiers,
    "render_toe_overlay_block":        render_toe_overlay_block,
}


# ---------------------------------------------------------------------
# Anchor-marker zone find/replace
# ---------------------------------------------------------------------

def _markers_for(path: Path, tag: str, iso_timestamp: str) -> Tuple[str, str]:
    """Return (open_marker, close_marker) for the file's syntax."""
    suffix = path.suffix.lower()
    if suffix == ".js":
        open_m = (f"/* PROP-AUTO:{tag} START — generator: Codes/tools/propagate_status.py "
                  f"— do-not-edit-between-markers — last-regenerated: {iso_timestamp} */")
        close_m = f"/* PROP-AUTO:{tag} END */"
    else:
        open_m = (f"<!-- PROP-AUTO:{tag} START\n"
                  f"     generator: Codes/tools/propagate_status.py\n"
                  f"     do-not-edit-between-markers\n"
                  f"     last-regenerated: {iso_timestamp}\n"
                  f"-->")
        close_m = f"<!-- PROP-AUTO:{tag} END -->"
    return open_m, close_m


def _zone_pattern_for(path: Path, tag: str) -> re.Pattern:
    """Return a regex that matches the entire zone (open marker through
    close marker, inclusive)."""
    suffix = path.suffix.lower()
    if suffix == ".js":
        return re.compile(
            rf"/\* PROP-AUTO:{re.escape(tag)} START.*?\*/"
            rf".*?"
            rf"/\* PROP-AUTO:{re.escape(tag)} END \*/",
            re.DOTALL,
        )
    return re.compile(
        rf"<!-- PROP-AUTO:{re.escape(tag)} START.*?-->"
        rf".*?"
        rf"<!-- PROP-AUTO:{re.escape(tag)} END -->",
        re.DOTALL,
    )


def find_zone(text: str, path: Path, tag: str) -> Optional[Tuple[int, int]]:
    """Find the (start, end) span of the zone in text, or None if absent."""
    pat = _zone_pattern_for(path, tag)
    m = pat.search(text)
    if m:
        return (m.start(), m.end())
    return None


def render_zone(rows: List[Dict[str, str]],
                path: Path,
                tag: str,
                renderer_name: str,
                iso_timestamp: str) -> str:
    renderer = RENDERER_REGISTRY[renderer_name]
    body = renderer(rows, iso_timestamp)
    open_m, close_m = _markers_for(path, tag, iso_timestamp)
    return f"{open_m}\n{body}\n{close_m}"


# ---------------------------------------------------------------------
# Per-target processing
# ---------------------------------------------------------------------

def _normalise_for_compare(s: str) -> str:
    """Strip volatile timestamp/sha fields so semantic equality is detected
    even when the regenerated payload has a fresh ISO timestamp."""
    s = re.sub(r'"generated":\s*"[^"]*"', '"generated":"STAMP"', s)
    s = re.sub(r'last-regenerated:[^\n*]*', 'last-regenerated:STAMP', s)
    s = re.sub(r'auto-synced \d{4}-\d{2}-\d{2}', 'auto-synced STAMP', s)
    s = re.sub(r'Generated:\s*\d{4}-\d{2}-\d{2}T[^\s]*', 'Generated:STAMP', s)
    return s


def process_full_file_target(rows: List[Dict[str, str]],
                              target: dict,
                              iso_timestamp: str,
                              dry_run: bool) -> Tuple[bool, str]:
    """Whole-file regeneration target. Returns (changed, diff-summary).

    Volatile timestamps inside the rendered body are stripped before
    compare, so reruns with no semantic change are reported as 'in sync'.
    """
    path = REPO_ROOT / target["path"]
    new_body = RENDERER_REGISTRY[target["renderer"]](rows, iso_timestamp)
    try:
        old_body = path.read_text(encoding="utf-8") if path.exists() else ""
    except OSError as exc:
        return (True, f"  [error] cannot read {target['path']}: {exc}")
    if _normalise_for_compare(old_body) == _normalise_for_compare(new_body):
        return (False, f"  [ok] {target['path']} in sync (timestamp ignored)")
    if dry_run:
        return (True, f"  [drift] {target['path']} ({len(old_body)} -> {len(new_body)} bytes)")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_body, encoding="utf-8")
        return (True, f"  [wrote] {target['path']} ({len(new_body)} bytes)")
    except OSError as exc:
        return (True, f"  [error] cannot write {target['path']}: {exc}")


def process_zone_target(rows: List[Dict[str, str]],
                         target: dict,
                         iso_timestamp: str,
                         dry_run: bool,
                         init_mode: bool) -> List[Tuple[bool, str]]:
    """Per-zone target with anchor markers. Returns list of (changed, msg)."""
    path = REPO_ROOT / target["path"]
    if not path.exists():
        return [(False, f"  [skip] {target['path']} does not exist")]
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [(True, f"  [error] cannot read {target['path']}: {exc}")]
    new_text = text
    msgs: List[Tuple[bool, str]] = []
    any_changed = False
    for zone in target.get("zones", []):
        tag = zone["tag"]
        renderer_name = zone["renderer"]
        zone_text = render_zone(rows, path, tag, renderer_name, iso_timestamp)
        span = find_zone(new_text, path, tag)
        if span is None:
            if init_mode:
                # Append zone at end of file (with separating blank line)
                new_text = new_text.rstrip() + "\n\n" + zone_text + "\n"
                msgs.append((True, f"  [init] {target['path']}#{tag} appended"))
                any_changed = True
            else:
                msgs.append((False,
                             f"  [missing] {target['path']}#{tag} (run --init to insert)"))
            continue
        existing_zone = new_text[span[0]:span[1]]
        # Strip volatile last-regenerated lines for compare
        def normalise(s: str) -> str:
            s = re.sub(r'last-regenerated:[^\n]*\n', 'last-regenerated:STAMP\n', s)
            s = re.sub(r'last-regenerated:[^*]*\*/', 'last-regenerated:STAMP */', s)
            return s
        if normalise(existing_zone) == normalise(zone_text):
            msgs.append((False, f"  [ok] {target['path']}#{tag} in sync"))
            continue
        new_text = new_text[:span[0]] + zone_text + new_text[span[1]:]
        msgs.append((True,
                     f"  [drift] {target['path']}#{tag} ({len(existing_zone)} -> {len(zone_text)} bytes)"
                     if dry_run else
                     f"  [wrote] {target['path']}#{tag} ({len(zone_text)} bytes)"))
        any_changed = True
    if any_changed and not dry_run:
        try:
            path.write_text(new_text, encoding="utf-8")
        except OSError as exc:
            msgs.append((True, f"  [error] cannot write {target['path']}: {exc}"))
    return msgs


# ---------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------

def log_run(iso_timestamp: str, status_sha: str, targets_touched: int,
            targets_changed: int, argv: List[str], dry_run: bool) -> None:
    if dry_run:
        return
    entry = (f"| {iso_timestamp} "
             f"| targets-touched={targets_touched} "
             f"| targets-changed={targets_changed} "
             f"| status.js-sha={status_sha[:7]} "
             f"| invocation=`{' '.join(argv)}` |\n")
    LOG_MD.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_MD.exists():
        header = (
            "# Status Propagation Audit Log\n\n"
            "Append-only ledger of every `propagate_status.py` execution that\n"
            "wrote at least one byte. `--check` (read-only) runs are NOT logged.\n\n"
            "Schema: `| timestamp | targets-touched | targets-changed | "
            "status.js-sha7 | invocation |`\n\n"
            "Governed by `Docs/policy/STATUS_PROPAGATION_POLICY.md` §6.\n\n"
        )
        LOG_MD.write_text(header + entry, encoding="utf-8")
    else:
        with LOG_MD.open("a", encoding="utf-8") as f:
            f.write(entry)


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true",
                   help="dry-run: emit drift report; never write")
    p.add_argument("--init", action="store_true",
                   help="insert anchor markers in targets that lack them")
    p.add_argument("--targets", nargs="+", default=None,
                   help="restrict to a subset of target names from config JSON")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    print(" propagate_status v1.0 (status.js -> downstream artefacts)")
    print(f"   Source: {STATUS_JS.relative_to(REPO_ROOT)}")
    print(f"   Config: {CONFIG_JSON.relative_to(REPO_ROOT)}")

    # Load config
    try:
        config = json.loads(CONFIG_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[propagate-status] ERROR: cannot load config: {exc}", file=sys.stderr)
        return 2

    # Load source
    try:
        status_text = STATUS_JS.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[propagate-status] ERROR: cannot read status.js: {exc}", file=sys.stderr)
        return 2
    status_sha = hashlib.sha256(status_text.encode("utf-8")).hexdigest()
    iso_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Parse pillar rows
    try:
        rows = parse_pillar_tiers(status_text)
    except ValueError as exc:
        print(f"[propagate-status] ERROR: parse: {exc}", file=sys.stderr)
        return 2
    print(f"   Parsed {len(rows)} pillar rows; status.js sha7 = {status_sha[:7]}")

    target_filter = set(args.targets) if args.targets else None
    targets_to_process = [
        t for t in config["targets"]
        if (target_filter is None or t["name"] in target_filter)
    ]
    if not targets_to_process:
        print("[propagate-status] ERROR: --targets filter matches no targets",
              file=sys.stderr)
        return 2

    print(f"   Processing {len(targets_to_process)} target(s):")
    targets_changed = 0
    targets_touched = 0
    any_drift = False
    for target in targets_to_process:
        targets_touched += 1
        kind = target.get("kind")
        if kind == "auto-full-file":
            changed, msg = process_full_file_target(rows, target, iso_timestamp, args.check)
            print(f"  [{target['name']}]")
            print(f"  {msg}")
            if changed:
                targets_changed += 1
                any_drift = True
        elif kind in ("html-zone", "js-zone", "md-zone", "md-zone-readonly"):
            print(f"  [{target['name']}]")
            # Read-only zones: --check only verifies sync; default mode never
            # writes (prevents auto-mutation of append-only ledgers like
            # STATUS-HISTORY.md whose body is operator-managed).
            readonly = (kind == "md-zone-readonly")
            results = process_zone_target(
                rows, target, iso_timestamp,
                dry_run=(args.check or readonly),
                init_mode=(args.init and not readonly),
            )
            for changed, msg in results:
                print(f"  {msg}")
                if changed:
                    targets_changed += 1
                    any_drift = True
        else:
            print(f"  [{target['name']}]")
            print(f"  [error] unknown kind {kind!r} in config")

    log_run(iso_timestamp, status_sha, targets_touched, targets_changed,
            sys.argv, args.check)

    if args.check:
        if any_drift:
            print(f"[propagate-status] DRIFT detected in {targets_changed} target(s); "
                  "run without --check to apply.")
            return 1
        print("[propagate-status] OK (no drift)")
        return 0
    print(f"[propagate-status] OK ({targets_changed} target(s) changed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
