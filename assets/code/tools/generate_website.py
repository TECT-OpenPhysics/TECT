#!/usr/bin/env python3
# =====================================================================
# generate_website.py
# Theory tag:  Math84-Website-Generator-v0p2-narrative-composition-2026-04-24
# Module version: v0.2 (narrative composition added)
# Purpose:     Auto-generate Website/data/*.js files from the canonical
#              Docs/ theory records, COMPOSED with user-editable
#              narrative .md files in Website/data/_narrative/.
#              Replaces manual .js editing which has been error-prone.
#
# v0.2 (2026-04-24): added Website/data/_narrative/*.md loading +
# markdown-to-HTML conversion + composition into the rendered .js.
# Pure data (Math notes, scorecard, CHANGELOG) auto-extracted from
# Docs/. Pure narrative (executive summary, axiom prose, honest
# positioning) loaded from _narrative/. Composition map in
# NARRATIVE_MAP constant.
#
# Single source of truth: Docs/math/, Docs/status/, CHANGELOG.md.
# Generated targets: Website/data/{math-notes.js, timeline.json,
#                                  history.js, theory.js, index.js,
#                                  records.js}.
#
# Architecture:
#   1. Parse canonical sources into structured records.
#   2. Render each Website/data/*.js by template substitution from
#      the structured records.
#   3. Idempotent: re-running with no source changes produces no diff.
#   4. --check mode: dry-run, prints what would change without writing.
#
# Usage:
#   python -u Codes/tools/generate_website.py --all
#   python -u Codes/tools/generate_website.py --math-notes
#   python -u Codes/tools/generate_website.py --timeline
#   python -u Codes/tools/generate_website.py --all --check
#
# Math note: Docs/math/TECT-Math84-Website-Generator-Architecture.tex.txt
# =====================================================================

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# ============================================================================
# Path resolution
# ============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent             # Contents/
DOCS_MATH = REPO_ROOT / "Docs" / "math"
DOCS_STATUS = REPO_ROOT / "Docs" / "status"
DOCS_POLICY = REPO_ROOT / "Docs" / "policy"
DOCS_MANUAL = REPO_ROOT / "Docs" / "manual"
CODES_DIR = REPO_ROOT / "Codes"
RUNS_DIR = REPO_ROOT / "Runs"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
WEBSITE_ROOT = REPO_ROOT / "Website"
WEB_DATA = WEBSITE_ROOT / "data"
WEB_ASSETS = WEBSITE_ROOT / "assets"
WEB_ARCHIVE = WEB_DATA / "_archive"
NARRATIVE_DIR = WEB_DATA / "_narrative"

# v0.3 Pagination thresholds
HISTORY_PAGE_SIZE = 30          # entries per history page
RECORDS_PAGE_SIZE = 50          # OPEN-Q + NEG-RES per page

# v0.3 Asset copy roots: (source path under REPO_ROOT, destination subdir under WEB_ASSETS)
ASSET_COPY_PLAN = [
    (DOCS_MATH,                "math"),                # all Math notes (.tex.txt)
    (DOCS_POLICY,              "policy"),              # CLAUDE.md, UPDATE_POLICY, REPO_LAYOUT, GIT_TAG_POLICY
    (DOCS_MANUAL,              "manual"),              # CODE_MANUAL.md
    (CODES_DIR / "pde",        "code/pde"),            # PDE solver core
    (CODES_DIR / "tools",      "code/tools"),          # diagnostic tools
    (CODES_DIR / "tests",      "code/tests"),          # pytest suite
    (CODES_DIR / "scripts",    "code/scripts"),        # PowerShell / bash
    (CODES_DIR / "supplementary", "code/supplementary"), # verification scripts
    # 2026-05-01 fix: results.js generator (paginate_results, line 1140 etc.)
    # emits href="assets/runs/<run_id>/..." with NO class prefix; the
    # existence check at line 1146 also probes Website/assets/runs/<run_id>/.
    # Therefore copy_assets must FLATTEN one level: copy Runs/<class>/<run_id>/*
    # directly into Website/assets/runs/<run_id>/*. Pre-2026-05-01 the dest
    # subdir included the class ("runs/continuation"), which produced the
    # 14 broken-link errors observed in the inaugural snapshot run at
    # 2026-05-01T18:32 (snapshot-log: [PARTIAL]).
    (RUNS_DIR / "audit",       "runs"),                # JSON audit snapshots (flatten one level)
    (RUNS_DIR / "continuation", "runs"),               # endpoint JSONs       (flatten one level)
    (RUNS_DIR / "logs",        "runs"),                # long-running logs    (flatten one level)
    (DOCS_STATUS,              "status"),              # status ledgers
    (REPO_ROOT / "CHANGELOG.md", "CHANGELOG.md"),       # single file (top-level)
    (REPO_ROOT / "CLAUDE.md",  "CLAUDE.md"),           # single file
    (REPO_ROOT / "NAVIGATION.md", "NAVIGATION.md"),     # single file
]

# Which file extensions to copy (skip binary/derivative artifacts)
COPY_EXTENSIONS = {".tex.txt", ".md", ".py", ".json", ".log", ".ps1", ".sh", ".bat", ".txt", ".js"}
COPY_MAX_SIZE = 5 * 1024 * 1024   # 5 MB per file (skip larger)

# Composition map: which narrative .md files compose into which .js targets,
# at which composition slot. The renderers consult this map to embed prose.
NARRATIVE_MAP = {
    "index.js": {
        "subtitle": "index_subtitle.md",
        "cards": [
            ("What is TECT?", "index_about.md"),
            ("How to read this site", "index_how_to_read.md"),
        ],
    },
    "theory.js": {
        "subtitle": "theory_subtitle.md",
        "cards": [
            ("Axiom A0", "theory_axiom.md"),
            ("Brazovskii regime", "theory_regime.md"),
            ("Locked parameters", "theory_locked_params.md"),
            ("Honest positioning", "theory_honest_positioning.md"),
            ("TOE qualification hierarchy — Stages 1 / 2 / 3 (snapshot)", "theory_stage_hierarchy.md"),
            ("Stage 1 — TOE emergence, eleven-pillar framework", "theory_stage1_detail.md"),
            ("Stage 2 — Global Closure Theorem sub-components", "theory_stage2_detail.md"),
            ("Stage 3 — external phenomenological qualification", "theory_stage3_detail.md"),
            ("Pillar 10 phase-transition origin & hbar derivation chain", "theory_hbar_origin.md"),
            ("TOE candidate cross-framework comparison", "theory_cross_framework.md"),
        ],
    },
    "history.js": {
        "subtitle": "history_subtitle.md",   # optional; missing files silently skipped
        "cards": [],
    },
    "results.js": {
        "subtitle": None,
        "cards": [
            ("Honest-status assessment", "results_assessment.md"),
        ],
    },
    "records.js": {
        "subtitle": None,
        "cards": [
            ("Records overview", "records_intro.md"),
        ],
    },
}


# ============================================================================
# Structured records
# ============================================================================
@dataclass
class MathNoteHeader:
    """Parsed header metadata from a TECT-Math<NN>*.tex.txt file."""
    filename: str
    theory_tag: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None
    classification: Optional[str] = None
    date: Optional[str] = None        # YYYY-MM-DD if extractable
    audit_status: Optional[str] = None
    one_line: Optional[str] = None     # short summary for math-notes.js bullet


@dataclass
class ChangelogEntry:
    """One `## [tag] — DATE` block in CHANGELOG.md."""
    raw_title: str
    date: Optional[str] = None
    summary: Optional[str] = None
    body_first_paragraph: Optional[str] = None


@dataclass
class OpenQuestion:
    tag: str                           # Q-YYYY-MM-DD-...
    statement: Optional[str] = None
    status: str = "OPEN"               # OPEN / RESOLVED / etc.
    last_reviewed: Optional[str] = None


@dataclass
class NegativeResult:
    tag: str                           # F-/R-/D-...
    title: Optional[str] = None
    summary: Optional[str] = None


@dataclass
class PillarStatus:
    number: int
    name: str
    status: str
    notes: Optional[str] = None


# ============================================================================
# Parsers
# ============================================================================
HEADER_FIELD_RE = re.compile(r"^%\s*([A-Za-z][A-Za-z\s\-]+?)\s*:\s*(.+?)\s*$")
TITLE_RE = re.compile(r"\\title\{(.+?)(?:\\\\|\})", re.DOTALL)
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def parse_math_note_header(path: Path, max_header_lines: int = 80) -> MathNoteHeader:
    """Extract metadata from a TECT-Math*.tex.txt file's leading `%` header."""
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="utf-8-sig", errors="replace")

    lines = content.splitlines()
    header_lines = lines[:max_header_lines]

    out = MathNoteHeader(filename=path.name)

    for line in header_lines:
        if not line.startswith("%"):
            continue
        m = HEADER_FIELD_RE.match(line)
        if not m:
            continue
        key, val = m.group(1).strip().lower(), m.group(2).strip()
        if "theory tag" in key or "theory_tag" in key:
            out.theory_tag = val
        elif key == "status":
            out.status = val
        elif key == "classification":
            out.classification = val
        elif key == "date":
            out.date = val
            d = DATE_RE.search(val)
            if d:
                out.date = d.group(1)
        elif key == "title":
            out.title = val

    # Fallback: extract title from \title{...}
    if not out.title:
        tm = TITLE_RE.search(content)
        if tm:
            out.title = tm.group(1).strip().replace("\n", " ")

    # Fallback: extract date from theory_tag
    if not out.date and out.theory_tag:
        d = DATE_RE.search(out.theory_tag)
        if d:
            out.date = d.group(1)

    # Fallback: extract date from filename (rare)
    if not out.date:
        d = DATE_RE.search(path.name)
        if d:
            out.date = d.group(1)

    # Construct one-line summary: classification or status
    parts = []
    if out.title:
        parts.append(out.title)
    elif out.theory_tag:
        parts.append(out.theory_tag)
    if out.status:
        parts.append(f"[{out.status}]")
    out.one_line = " ".join(parts) if parts else path.name

    # Detect AUDIT-STATUS banner
    audit_match = re.search(r"\[AUDIT-STATUS[^\]]*\]\s*([A-Z\-/]+(?:[^\n]*))", content)
    if audit_match:
        out.audit_status = audit_match.group(1).strip()[:100]

    return out


def collect_math_notes() -> list[MathNoteHeader]:
    """Scan Docs/math/ and return MathNoteHeader for every .tex.txt file."""
    results = []
    for p in sorted(DOCS_MATH.glob("TECT-Math*.tex.txt")):
        try:
            results.append(parse_math_note_header(p))
        except Exception as e:
            print(f"[WARN] Failed to parse {p.name}: {e}", file=sys.stderr)
    return results


def parse_changelog(top_n: int = 30) -> list[ChangelogEntry]:
    """Parse CHANGELOG.md, return up-to-N most recent entries."""
    if not CHANGELOG.exists():
        return []
    content = CHANGELOG.read_text(encoding="utf-8", errors="replace")
    # Entry pattern: ## [...] — YYYY-MM-DD
    pattern = re.compile(
        r"^## (\[.*?\][^\n]*?)\s+[—\-]+\s+(\d{4}-\d{2}-\d{2})\s*$",
        re.MULTILINE,
    )
    entries = []
    matches = list(pattern.finditer(content))
    for i, m in enumerate(matches[:top_n]):
        title = m.group(1).strip()
        date = m.group(2)
        # Body: from end of this match to start of next (or 4000 chars max)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else min(start + 4000, len(content))
        body = content[start:end].strip()
        # Extract first MEANINGFUL paragraph: skip section headers like ### [Trigger]
        # and grab the first paragraph that has actual content.
        paras = [p.strip() for p in body.split("\n\n") if p.strip()]
        first_meaningful = None
        current_section = None
        _hangul = re.compile(r"[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F]")
        _userlead = re.compile(r"^(User\s+(devil|feedback|executed|request|asked|directive|prompted|input)|user feedback|User-prompted|Triggered by user)", re.I)
        for p in paras:
            stripped = p.strip()
            sec_m = re.match(r"^#+\s+\[([^\]]+)\]\s*$", stripped)
            if sec_m:
                current_section = sec_m.group(1).strip().lower()
                continue
            if re.match(r"^#+\s+\S", stripped) and len(stripped.split("\n")[0]) < 80 and len(stripped.split("\n")) == 1:
                continue
            if current_section == "trigger":
                continue
            text_lines = stripped.split("\n")
            cleaned_lines = [ln for ln in text_lines if not re.match(r"^#+\s+", ln)]
            cleaned = "\n".join(cleaned_lines).strip()
            if not cleaned or len(cleaned) <= 30:
                continue
            if _hangul.search(cleaned):
                continue
            if _userlead.match(cleaned):
                continue
            first_meaningful = cleaned
            break
        entries.append(ChangelogEntry(
            raw_title=title,
            date=date,
            summary=title,
            body_first_paragraph=first_meaningful or (paras[0] if paras else None),
        ))
    return entries


def parse_open_questions() -> list[OpenQuestion]:
    p = DOCS_STATUS / "OPEN-QUESTIONS.md"
    if not p.exists():
        return []
    content = p.read_text(encoding="utf-8", errors="replace")
    # Active section
    active_match = re.search(r"^## Active\s*$(.*?)(?=^## |\Z)", content, re.MULTILINE | re.DOTALL)
    if not active_match:
        return []
    active = active_match.group(1)
    # Each entry: ### Q-... — title — [STATUS DATE]
    entry_re = re.compile(
        r"^### (Q-[\d\-]+-\S+?)\s*[—\-]+\s*(.+?)\s*$",
        re.MULTILINE,
    )
    out = []
    for m in entry_re.finditer(active):
        out.append(OpenQuestion(
            tag=m.group(1),
            statement=m.group(2)[:200],
            status="OPEN",
        ))
    return out


def parse_negative_results() -> list[NegativeResult]:
    p = DOCS_STATUS / "NEGATIVE-RESULTS.md"
    if not p.exists():
        return []
    content = p.read_text(encoding="utf-8", errors="replace")
    entry_re = re.compile(
        r"^### ([FRD]-\d{4}-\d{2}-\d{2}-\S+?)\s*[—\-]+\s*(.+?)\s*$",
        re.MULTILINE,
    )
    out = []
    for m in entry_re.finditer(content):
        out.append(NegativeResult(
            tag=m.group(1),
            title=m.group(2)[:200],
        ))
    return out


def parse_toe_fact_sheet_scorecard() -> list[PillarStatus]:
    p = DOCS_STATUS / "TOE-FACT-SHEET.md"
    if not p.exists():
        return []
    content = p.read_text(encoding="utf-8", errors="replace")
    # Find scorecard table: rows like `| 1 | Mass | **STATUS** | notes... |`
    row_re = re.compile(
        r"^\|\s*(\d{1,2})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|\s*$",
        re.MULTILINE,
    )
    pillars = {}
    for m in row_re.finditer(content):
        try:
            num = int(m.group(1))
            if 1 <= num <= 11:
                pillars[num] = PillarStatus(
                    number=num,
                    name=m.group(2).strip(),
                    status=m.group(3).strip(),
                    notes=m.group(4).strip()[:500],
                )
        except ValueError:
            continue
    return [pillars[i] for i in sorted(pillars.keys())]


# ============================================================================
# Narrative loading + markdown-to-HTML conversion
# ============================================================================
def load_narrative(filename: str) -> Optional[str]:
    """Read a narrative .md file from Website/data/_narrative/. Returns None if missing."""
    p = NARRATIVE_DIR / filename
    if not p.exists():
        return None
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[WARN] Failed to read {p}: {e}", file=sys.stderr)
        return None


def md_to_html(md: str) -> str:
    """Minimal markdown-to-HTML converter sufficient for narrative blocks.

    Supports: paragraphs, ## h2, ### h3, bullet/numbered lists, **bold**,
    *italic*, `code`, [text](url), tables (pipe-syntax, GFM), inline math
    $...$ and display math $$...$$ (passed through as-is for MathJax).
    HTML tags pass through verbatim.
    """
    if not md:
        return ""

    # Split into block-level chunks separated by blank lines.
    lines = md.replace("\r\n", "\n").split("\n")
    blocks = []
    current = []
    for line in lines:
        if line.strip() == "":
            if current:
                blocks.append("\n".join(current))
                current = []
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))

    out_html = []
    # Block-level HTML tags that should pass through verbatim
    # (without being wrapped in <p>...</p>). Used for embedded tables,
    # divs, kpi-rows, etc. in narrative .md files.
    _block_html_starts = ("<table", "<div", "<ul", "<ol", "<dl", "<pre",
                          "<blockquote", "<figure", "<details", "<section",
                          "<header", "<footer", "<aside")

    for block in blocks:
        stripped = block.strip()

        # Raw block-level HTML: pass through unchanged (Math82-AddG3-website
        # narrative-with-tables fix, 2026-04-24).
        _lower = stripped.lower()
        if any(_lower.startswith(tag) for tag in _block_html_starts):
            out_html.append(stripped)
            continue

        # Horizontal rule
        if re.match(r"^-{3,}$", stripped):
            out_html.append("<hr/>")
            continue

        # Heading
        if stripped.startswith("#### "):
            out_html.append(f"<h4>{_inline_md(stripped[5:].strip())}</h4>")
            continue
        if stripped.startswith("### "):
            out_html.append(f"<h3>{_inline_md(stripped[4:].strip())}</h3>")
            continue
        if stripped.startswith("## "):
            out_html.append(f"<h2>{_inline_md(stripped[3:].strip())}</h2>")
            continue

        # Table (GFM pipe syntax)
        if "\n" in stripped and re.search(r"^\|.+\|$", stripped.split("\n")[0]) and re.search(r"^\|[\s:|-]+\|$", stripped.split("\n")[1] if len(stripped.split("\n")) > 1 else ""):
            out_html.append(_render_md_table(stripped))
            continue

        # Bullet list
        if all(re.match(r"^\s*-\s+", ln) for ln in stripped.split("\n")):
            items = [re.sub(r"^\s*-\s+", "", ln) for ln in stripped.split("\n")]
            out_html.append("<ul>" + "".join(f"<li>{_inline_md(it)}</li>" for it in items) + "</ul>")
            continue

        # Numbered list
        if all(re.match(r"^\s*\d+\.\s+", ln) for ln in stripped.split("\n")):
            items = [re.sub(r"^\s*\d+\.\s+", "", ln) for ln in stripped.split("\n")]
            out_html.append("<ol>" + "".join(f"<li>{_inline_md(it)}</li>" for it in items) + "</ol>")
            continue

        # Default: paragraph
        # Join lines within a paragraph with a space (GFM-style soft break)
        para = " ".join(stripped.split("\n"))
        out_html.append(f"<p>{_inline_md(para)}</p>")

    return "\n".join(out_html)


def _inline_md(text: str) -> str:
    """Apply inline markdown transforms within a paragraph or heading."""
    # Code: `text` -> <code>text</code> (do this first to protect contents)
    code_segments = []
    def _code_sub(m):
        code_segments.append(m.group(1))
        return f"\x00CODE{len(code_segments)-1}\x00"
    text = re.sub(r"`([^`]+)`", _code_sub, text)
    # Bold: **text**
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    # Italic: *text* (avoid double-asterisks already converted)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    # Links: [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # Restore code segments
    for i, seg in enumerate(code_segments):
        text = text.replace(f"\x00CODE{i}\x00", f"<code>{seg}</code>")
    return text


def _render_md_table(block: str) -> str:
    """Convert a GFM pipe table to <table> HTML."""
    lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
    # Header row, separator, body rows
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    body_rows = [[c.strip() for c in ln.strip("|").split("|")] for ln in lines[2:]]
    out = ["<table>", "<thead><tr>"]
    out.extend(f"<th>{_inline_md(h)}</th>" for h in header)
    out.append("</tr></thead>")
    out.append("<tbody>")
    for row in body_rows:
        out.append("<tr>" + "".join(f"<td>{_inline_md(c)}</td>" for c in row) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


# ============================================================================
# Renderers
# ============================================================================
def js_string_escape(s: str) -> str:
    """Escape a Python string for embedding in a JS double-quoted string."""
    if s is None:
        return ""
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def render_math_notes_js(notes: list[MathNoteHeader]) -> str:
    """Generate Website/data/math-notes.js content from parsed headers."""
    sorted_notes = sorted(notes, key=lambda n: (n.date or "0000-00-00"), reverse=True)

    lines = []
    lines.append("// AUTO-GENERATED by Codes/tools/generate_website.py — DO NOT EDIT BY HAND")
    lines.append(f"// Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"// Source: Docs/math/TECT-Math*.tex.txt ({len(sorted_notes)} files)")
    lines.append("")
    lines.append("window.TECT_MATH_NOTES = {")
    lines.append("  blocks: [")
    lines.append("    {")
    lines.append('      type: "heading",')
    lines.append('      level: 1,')
    lines.append('      text: "Notes"')
    lines.append("    },")
    lines.append("    {")
    lines.append('      type: "paragraph",')
    lines.append('      content: "Proof-level derivations supporting the Theory page. The list below is auto-generated from the canonical <code>Docs/math/TECT-Math&lt;NN&gt;*.tex.txt</code> files; each entry shows the file, status, and one-line title extracted from the source header. To update, edit the source notes and re-run <code>Codes/tools/generate_website.py</code>.",')
    lines.append('      class: "muted"')
    lines.append("    },")
    lines.append("    {")
    lines.append('      type: "card",')
    lines.append(f'      title: "All Math notes ({len(sorted_notes)} total, newest first)",')
    lines.append("      blocks: [")
    lines.append("        {")
    lines.append('          type: "list",')
    lines.append('          items: [')

    # English-only enforcement (CLAUDE.md §5.1 / OUTPUT_LANGUAGE_POLICY.md):
    # Some historical Math notes (Math01, Math06–Math28) carry Korean titles
    # auto-extracted from their tex.txt headers. Strip Hangul characters
    # (U+AC00–U+D7A3 + Jamo blocks) from the rendered title before emission;
    # the canonical English title remains in the underlying .tex.txt source
    # for archival traceability.
    _HANGUL_STRIP = re.compile(r"[ᄀ-ᇿ㄰-㆏가-힣]+")
    for note in sorted_notes:
        date_part = f"({note.date})" if note.date else ""
        raw_title = note.title or note.theory_tag or note.filename
        clean_title = _HANGUL_STRIP.sub("", raw_title).strip()
        clean_title = re.sub(r"\s{2,}", " ", clean_title)
        if not clean_title:
            clean_title = note.theory_tag or note.filename
        title_part = js_string_escape(clean_title)
        status_part = js_string_escape(note.status or note.classification or "")
        audit_part = ""
        if note.audit_status:
            audit_part = f' <span style=\\"color:#a04020;\\">[AUDIT: {js_string_escape(note.audit_status)[:60]}]</span>'

        if status_part:
            tag = (
                "tag-ok" if any(k in status_part.upper() for k in ("PROVED", "CLOSED", "THEOREM", "SEALED", "SUCCESS"))
                else "tag-warn" if any(k in status_part.upper() for k in ("PARTIAL", "OPEN", "DRAFT", "NEAR", "CONDITIONAL"))
                else "tag-gap" if any(k in status_part.upper() for k in ("FAIL", "RETRACT", "FALSIFIED", "SUPERSEDED"))
                else "tag-design"
            )
            status_html = f' <span class=\\"tag {tag}\\">{js_string_escape(status_part)[:80]}</span>'
        else:
            status_html = ""

        # v0.3: add download link to local asset copy
        download_link = f' <a href=\\"assets/math/{note.filename}\\" download class=\\"download-link\\">[\u2193 download]</a>'
        item = f'<code>{note.filename}</code> {date_part} &mdash; {title_part}{status_html}{audit_part}{download_link}'
        lines.append(f'            "{item}",')

    # Drop trailing comma
    if lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]

    lines.append("          ],")
    lines.append('          class: "tight"')
    lines.append("        }")
    lines.append("      ]")
    lines.append("    }")
    lines.append("  ]")
    lines.append("};")
    lines.append("")

    return "\n".join(lines)


def render_timeline_json(changelog: list[ChangelogEntry]) -> str:
    out = {
        "generated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC (auto)"),
        "description": "Chronological record of TECT theoretical and infrastructural milestones. AUTO-GENERATED from CHANGELOG.md — do not edit by hand. To update, edit CHANGELOG.md and re-run Codes/tools/generate_website.py.",
        "entries": [
            {
                "date": e.date,
                "title": e.raw_title,
                "summary": (e.body_first_paragraph or "")[:1500],
            }
            for e in changelog
        ],
    }
    return json.dumps(out, indent=2, ensure_ascii=False)


def render_records_js(open_qs: list[OpenQuestion], neg_results: list[NegativeResult]) -> str:
    lines = []
    lines.append("// AUTO-GENERATED by Codes/tools/generate_website.py — DO NOT EDIT BY HAND")
    lines.append(f"// Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"// Source: Docs/status/OPEN-QUESTIONS.md ({len(open_qs)} active), Docs/status/NEGATIVE-RESULTS.md ({len(neg_results)} entries)")
    lines.append("")
    lines.append("window.TECT_RECORDS = {")
    lines.append("  blocks: [")
    lines.append("    {")
    lines.append('      type: "heading", level: 1, text: "Records"')
    lines.append("    },")
    lines.append("    {")
    lines.append('      type: "card",')
    lines.append(f'      title: "Active OPEN questions ({len(open_qs)})",')
    lines.append("      blocks: [{")
    lines.append('          type: "list",')
    lines.append('          items: [')
    for q in open_qs:
        lines.append(f'            "<code>{js_string_escape(q.tag)}</code> &mdash; {js_string_escape(q.statement or "")}",')
    if open_qs and lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append("          ]")
    lines.append("      }]")
    lines.append("    },")
    lines.append("    {")
    lines.append('      type: "card",')
    lines.append(f'      title: "Negative results ({len(neg_results)} F/R/D entries)",')
    lines.append("      blocks: [{")
    lines.append('          type: "list",')
    lines.append('          items: [')
    for n in neg_results:
        lines.append(f'            "<code>{js_string_escape(n.tag)}</code> &mdash; {js_string_escape(n.title or "")}",')
    if neg_results and lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append("          ]")
    lines.append("      }]")
    lines.append("    }")
    lines.append("  ]")
    lines.append("};")
    return "\n".join(lines)


def render_history_js(changelog: list[ChangelogEntry]) -> str:
    lines = []
    lines.append("// AUTO-GENERATED by Codes/tools/generate_website.py — DO NOT EDIT BY HAND")
    lines.append(f"// Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"// Source: CHANGELOG.md (top {len(changelog)} entries)")
    lines.append("")
    lines.append("window.TECT_HISTORY = {")
    lines.append('  title: "History",')
    lines.append('  subtitle: "Chronological record of TECT development \u2014 AUTO-GENERATED from CHANGELOG.md.",')
    lines.append(f'  lastUpdated: "{datetime.utcnow().strftime("%Y-%m-%d (auto)")}",')
    lines.append('  blocks: [')
    lines.append('    {')
    lines.append('      type: "heading", level: 2, text: "Recent changelog entries"')
    lines.append('    },')
    lines.append('    {')
    lines.append('      type: "timeline",')
    lines.append('      items: [')
    for entry in changelog:
        title = js_string_escape(entry.raw_title)[:200]
        body = js_string_escape(entry.body_first_paragraph or "")[:1200]
        lines.append("        {")
        lines.append(f'          date: "{entry.date}",')
        lines.append(f'          title: "{title}",')
        lines.append(f'          body: "{body}"')
        lines.append("        },")
    if changelog and lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append("      ]")
    lines.append("    }")
    lines.append("  ]")
    lines.append("};")
    return "\n".join(lines)


def render_theory_js(scorecard: list[PillarStatus], top_changelog: list[ChangelogEntry]) -> str:
    lines = []
    lines.append("// AUTO-GENERATED by Codes/tools/generate_website.py v0.2 — DO NOT EDIT BY HAND")
    lines.append(f"// Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("// Source: TOE-FACT-SHEET.md (scorecard) + Website/data/_narrative/theory_*.md (narrative)")
    lines.append("")
    lines.append("window.TECT_THEORY = {")
    lines.append('  title: "Theory state",')

    sub_md = load_narrative(NARRATIVE_MAP["theory.js"]["subtitle"])
    if sub_md:
        subtitle = js_string_escape(md_to_html(sub_md).replace("<p>", "").replace("</p>", " ").strip())
    else:
        latest_tag = top_changelog[0].raw_title if top_changelog else "(no recent changelog)"
        subtitle = f"Latest theory tag: {js_string_escape(latest_tag)[:300]}."
    lines.append(f'  subtitle: "{subtitle}",')
    lines.append(f'  lastUpdated: "{datetime.utcnow().strftime("%Y-%m-%d (auto)")}",')
    lines.append('  blocks: [')

    # Narrative cards (axiom, regime, locked params, honest positioning)
    for card_title, narr_file in NARRATIVE_MAP["theory.js"]["cards"]:
        md = load_narrative(narr_file)
        if md:
            html = md_to_html(md)
            lines.append('    {')
            lines.append('      type: "card",')
            lines.append(f'      title: "{js_string_escape(card_title)}",')
            lines.append('      blocks: [{')
            lines.append('          type: "html",')
            lines.append(f'          content: "{js_string_escape(html)}"')
            lines.append('      }]')
            lines.append('    },')

    lines.append('    {')
    lines.append('      type: "card",')
    lines.append('      title: "11-Pillar Stage-1 Scorecard (canonical, auto-generated)",')
    lines.append('      blocks: [{')
    lines.append('          type: "table",')
    lines.append('          headers: ["#", "Pillar", "Status", "Notes (truncated)"],')
    lines.append('          rows: [')
    for p in scorecard:
        notes = js_string_escape(p.notes or "")[:300]
        lines.append(f'            ["{p.number}", "{js_string_escape(p.name)}", "{js_string_escape(p.status)}", "{notes}"],')
    if scorecard and lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append('          ]')
    lines.append('      }]')
    lines.append('    }')
    lines.append('  ]')
    lines.append('};')
    return "\n".join(lines)


def render_index_js(scorecard: list[PillarStatus], top_changelog: list[ChangelogEntry], math_notes_count: int) -> str:
    lines = []
    lines.append("// AUTO-GENERATED by Codes/tools/generate_website.py v0.2 — DO NOT EDIT BY HAND")
    lines.append(f"// Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("// Narrative composed from Website/data/_narrative/index_*.md")
    lines.append("")
    lines.append("window.TECT_INDEX = {")
    lines.append('  title: "Topological Energy Condensate Theory",')

    sub_md = load_narrative(NARRATIVE_MAP["index.js"]["subtitle"])
    if sub_md:
        subtitle = js_string_escape(md_to_html(sub_md).replace("<p>", "").replace("</p>", " ").strip())
    else:
        latest = top_changelog[0] if top_changelog else None
        subtitle = f"Latest update: {latest.date} \u2014 {js_string_escape(latest.raw_title)[:200]}" if latest else "TECT research dashboard"
    lines.append(f'  subtitle: "{subtitle}",')
    lines.append(f'  lastUpdated: "{datetime.utcnow().strftime("%Y-%m-%d (auto)")}",')

    # KPI: count statuses (mutually exclusive — each pillar in exactly one bucket)
    def status_bucket(s):
        u = s.upper()
        if "OPEN" in u or "NOT ADDRESSED" in u: return "open"
        if "PARTIAL" in u: return "partial"
        if "NEAR" in u: return "near"
        if "CONDITIONAL" in u or "CAVEAT" in u: return "cond"
        if "CLOSED" in u and "LOOP" in u: return "loop"
        if "PROVED" in u: return "proved"
        return "other"

    counts = {"proved": 0, "cond": 0, "loop": 0, "partial": 0, "near": 0, "open": 0, "other": 0}
    for p in scorecard:
        counts[status_bucket(p.status)] += 1

    lines.append('  blocks: [')

    # Narrative cards (composed from index_*.md)
    for card_title, narr_file in NARRATIVE_MAP["index.js"]["cards"]:
        md = load_narrative(narr_file)
        if md:
            html = md_to_html(md)
            lines.append('    {')
            lines.append('      type: "card",')
            lines.append(f'      title: "{js_string_escape(card_title)}",')
            lines.append('      blocks: [{')
            lines.append('          type: "html",')
            lines.append(f'          content: "{js_string_escape(html)}"')
            lines.append('      }]')
            lines.append('    },')

    lines.append('    {')
    lines.append('      type: "card",')
    lines.append('      title: "Stage-1 scorecard summary",')
    lines.append('      blocks: [{')
    lines.append('          type: "table",')
    lines.append('          headers: ["Status", "Count"],')
    lines.append('          rows: [')
    lines.append(f'            ["PROVED unconditional", "{counts["proved"]}"],')
    lines.append(f'            ["PROVED conditional / with caveat", "{counts["cond"]}"],')
    lines.append(f'            ["CLOSED@1-loop", "{counts["loop"]}"],')
    lines.append(f'            ["PARTIAL-ADVANCED", "{counts["partial"]}"],')
    lines.append(f'            ["NEAR-CLOSURE", "{counts["near"]}"],')
    lines.append(f'            ["OPEN / OPEN-NEGATIVE", "{counts["open"]}"]')
    lines.append('          ]')
    lines.append('      }]')
    lines.append('    },')
    lines.append('    {')
    lines.append('      type: "card",')
    lines.append('      title: "Repository statistics",')
    lines.append('      blocks: [{')
    lines.append('          type: "table",')
    lines.append('          headers: ["Metric", "Value"],')
    lines.append('          rows: [')
    lines.append(f'            ["Math notes (Docs/math/TECT-Math*.tex.txt)", "{math_notes_count}"],')
    lines.append(f'            ["Recent CHANGELOG entries displayed", "{len(top_changelog)}"],')
    lines.append(f'            ["Total pillars (sum check)", "{sum(counts.values())} (must = 11)"]')
    lines.append('          ]')
    lines.append('      }]')
    lines.append('    }')
    lines.append('  ]')
    lines.append('};')
    return "\n".join(lines)


# ============================================================================
# v0.3 Asset copying — make Website/ self-contained for standalone publish
# ============================================================================
import shutil
import hashlib

def _file_should_copy(p):
    """Return True if path p should be included in asset copy."""
    if not p.is_file():
        return False
    if p.stat().st_size > COPY_MAX_SIZE:
        return False
    name = p.name
    # Match either single-extension (.py, .md, .json) or compound (.tex.txt)
    if any(name.endswith(ext) for ext in COPY_EXTENSIONS):
        # Skip __pycache__, .pyc
        if "__pycache__" in p.parts or name.endswith(".pyc"):
            return False
        return True
    return False


def copy_assets(check=False):
    """Copy canonical Docs/ and Codes/ files into Website/assets/ for
    standalone publish + download links. Returns asset manifest dict.

    Manifest schema is `tect-asset-manifest-v1` (canonical, expected by
    verify_website.py check_manifest_freshness()). Pre-2026-05-01 the
    schema lacked the `count` field which caused verify to read
    declared=-1 and flag manifest-stale on every snapshot run; the fix
    adds the canonical fields (`schema`, `count`, `total_bytes`) so the
    manifest is verify-clean from step 2 of the snapshot pipeline.
    """
    print("\n--- Copying assets to Website/assets/ ---")
    manifest = {
        "generated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "schema": "tect-asset-manifest-v1",
        "description": "Asset inventory: copies of canonical Docs/ and Codes/ files for standalone Website publish. Each entry: src path (relative to repo root) -> dest path (relative to Website/assets/).",
        "files": [],
    }
    n_copied = 0
    n_skipped = 0

    if not check:
        WEB_ASSETS.mkdir(parents=True, exist_ok=True)

    for src, dest_subdir in ASSET_COPY_PLAN:
        if not src.exists():
            print(f"  [skip] {src.relative_to(REPO_ROOT)} (does not exist)")
            continue

        if src.is_file():
            # Single-file copy
            dst = WEB_ASSETS / dest_subdir
            if not check:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            try:
                size = src.stat().st_size
                manifest["files"].append({
                    "src": str(src.relative_to(REPO_ROOT)).replace("\\", "/"),
                    "dest": f"assets/{dest_subdir}",
                    "size_bytes": size,
                })
                n_copied += 1
            except Exception as e:
                print(f"  [err] {src.name}: {e}")
            continue
        for p in sorted(src.rglob("*")):
            if not _file_should_copy(p):
                if p.is_file():
                    n_skipped += 1
                continue
            rel = p.relative_to(src)
            dst = WEB_ASSETS / dest_subdir / rel
            if not check:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dst)
            manifest["files"].append({
                "src": str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
                "dest": f"assets/{dest_subdir}/{str(rel).replace(chr(92), '/')}",
                "size_bytes": p.stat().st_size,
            })
            n_copied += 1
    print(f"  Files copied : {n_copied}")
    print(f"  Files skipped: {n_skipped}")
    # 2026-05-01 fix: canonical schema requires `count` (matches the
    # verify_website.py --regen-manifest output schema). Without this,
    # check_manifest_freshness() reads declared=-1 (default) and flags
    # manifest-stale on every snapshot run.
    # Note: `count` is the number of files actually present in
    # Website/assets/ (excluding manifest.json itself), per the
    # verify_website.py rglob convention. We compute it from a fresh
    # walk of WEB_ASSETS rather than from len(manifest["files"]) so that
    # any pre-existing files (e.g., legacy assets/ contents not in
    # ASSET_COPY_PLAN) are also counted, matching the verifier's
    # rglob semantics exactly.
    if not check:
        WEB_ASSETS.mkdir(parents=True, exist_ok=True)
        # Compute the canonical `count` field with the same convention as
        # verify_website.py check_manifest_freshness() (rglob, exclude
        # manifest.json).
        manifest["count"] = sum(
            1 for p in WEB_ASSETS.rglob("*")
            if p.is_file() and p.name != "manifest.json"
        )
        manifest["total_bytes"] = sum(
            p.stat().st_size for p in WEB_ASSETS.rglob("*")
            if p.is_file() and p.name != "manifest.json"
        )
        with open(WEB_ASSETS / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"  Manifest written: Website/assets/manifest.json ({len(manifest['files'])} entries)")
    return manifest


def paginate_changelog(changelog, page_size=HISTORY_PAGE_SIZE):
    pages = []
    n_pages = (len(changelog) + page_size - 1) // page_size
    for i in range(n_pages):
        start = i * page_size
        end = start + page_size
        page_idx = i + 1
        if page_idx == 1:
            newer = None
        elif page_idx == 2:
            newer = "history.html"
        else:
            newer = f"history-page-{page_idx-1:03d}.html"
        if page_idx >= n_pages:
            older = None
        elif page_idx == 1:
            older = "history-page-002.html"
        else:
            older = f"history-page-{page_idx+1:03d}.html"
        nav = {
            "page": page_idx, "total": n_pages,
            "newer": newer, "older": older,
            "current_filename": ("history.html" if page_idx == 1 else f"history-page-{page_idx:03d}.html"),
        }
        pages.append((page_idx, changelog[start:end], nav))
    return pages


def write_history_page_html_wrapper(target_html, var_name, js_relpath, page_label, check):
    html = (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '  <meta charset="utf-8">\n'
        f'  <title>TECT \u2014 {page_label}</title>\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '  <link rel="stylesheet" href="assets/style.css">\n'
        '  <script>window.MathJax={tex:{inlineMath:[["$","$"],["\\\\(","\\\\)"]]}};</script>\n'
        '  <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>\n'
        '</head>\n<body>\n'
        '<header class="site" id="site-header"></header>\n'
        '<main class="wrap" id="page-content"></main>\n'
        '<footer class="site" id="site-footer"></footer>\n'
        '<script src="data/site.js"></script>\n'
        f'<script src="{js_relpath}"></script>\n'
        '<script src="assets/js/tect-render.js"></script>\n'
        f'<script>TECT.render("history", window.{var_name});</script>\n'
        '</body>\n</html>\n'
    )
    if not target_html.exists() or target_html.read_text(encoding="utf-8") != html:
        if not check:
            target_html.parent.mkdir(parents=True, exist_ok=True)
            target_html.write_text(html, encoding="utf-8", newline="\n")
        return True
    return False


def render_results_js(top_changelog) -> str:
    """v0.7 (2026-04-29): NEW LAYOUT - narrow 5-col summary table + per-run
    collapsible card with full CLI command extracted from RESULT.md s2
    Configuration block (or reconstructed from MANIFEST.md if absent)."""
    runs_root = REPO_ROOT / "Runs"
    runs = []
    if runs_root.exists():
        for class_dir in sorted(runs_root.iterdir()):
            if not class_dir.is_dir() or class_dir.name.startswith("_") or class_dir.name == "seeds":
                continue
            for run_dir in sorted(class_dir.iterdir()):
                if not run_dir.is_dir():
                    continue
                manifest = run_dir / "MANIFEST.md"
                result_md = run_dir / "RESULT.md"
                diag = run_dir / "run_diagnostics.json"
                if not (manifest.exists() or result_md.exists()):
                    continue
                run_info = {
                    "run_id": run_dir.name, "run_class": class_dir.name,
                    "status": "unknown", "mu2_schedule": "", "wall_time_s": None,
                    "driver": "", "theory_tag": "", "n_converged": None, "n_total": None,
                    "cli_command": "",
                    # 2026-05-01 fix: track MANIFEST.md existence so the
                    # download-link generator (line 1148) can suppress the
                    # link for runs that were persisted without one
                    # (e.g., crashed runs, pre-MANIFEST-discipline legacy
                    # runs from 2026-04-30T16:49–17:01 cluster).
                    "has_manifest_md": manifest.exists(),
                    "has_result_md": result_md.exists(),
                    "has_diagnostics_json": diag.exists(),
                    "mtime": run_dir.stat().st_mtime,
                }
                if manifest.exists():
                    try:
                        text = manifest.read_text(encoding="utf-8", errors="replace")
                        for key, pat in [
                            ("status", r"\*\*Status\*\*\s*:\s*([A-Z_]+)"),
                            ("driver", r"\*\*Driver\*\*\s*:\s*(.+)"),
                            ("theory_tag", r"\*\*Theory tag\*\*\s*:\s*(.+)"),
                        ]:
                            m = re.search(pat, text)
                            if m: run_info[key] = m.group(1).strip()
                        m = re.search(r"\*\*Points total\*\*\s*:\s*(\d+)", text)
                        if m: run_info["n_total"] = int(m.group(1))
                        m = re.search(r"\*\*Converged\*\*\s*:\s*(\d+)", text)
                        if m: run_info["n_converged"] = int(m.group(1))
                        m = re.search(r"\|\s*1\s*\|\s*([\-\+\d\.eE]+)", text)
                        if m: run_info["mu2_schedule"] = m.group(1).strip()
                        wm = re.findall(r"\|\s*([\d\.]+)\s*\|\s*$", text, re.MULTILINE)
                        if wm:
                            try: run_info["wall_time_s"] = float(wm[-1])
                            except Exception: pass
                    except Exception:
                        pass
                if result_md.exists():
                    try:
                        rtext = result_md.read_text(encoding="utf-8", errors="replace")
                        m = re.search(r"##\s*.2\..\s*Configuration[^\n]*\n+```(?:powershell|bash|sh)?\s*\n(.+?)\n```",
                                      rtext, re.DOTALL)
                        if m:
                            run_info["cli_command"] = m.group(1).strip()
                    except Exception:
                        pass
                if not run_info["cli_command"] and run_info["driver"]:
                    drv = run_info["driver"].split("(")[0].strip()
                    rcl = run_info["run_class"]
                    rid = run_info["run_id"]
                    run_info["cli_command"] = (
                        "# Reconstructed from MANIFEST.md (RESULT.md absent)\n"
                        f"python -u {drv} \\\n    --output \"Runs/{rcl}/{rid}\""
                    )
                runs.append(run_info)
    runs.sort(key=lambda r: r["mtime"], reverse=True)

    cards_html = []
    for card_title, narr_file in NARRATIVE_MAP.get("results.js", {}).get("cards", []):
        try:
            md = load_narrative(narr_file)
            if md:
                cards_html.append((card_title, md_to_html(md)))
        except Exception:
            pass

    def js_esc(s):
        return (s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")

    parts = []
    parts.append("// AUTO-GENERATED by Codes/tools/generate_website.py v0.8 -- DO NOT EDIT BY HAND")
    parts.append("// Generated: " + datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
    parts.append("// Source: Runs/<class>/<run_id>/ (MANIFEST.md + RESULT.md + run_diagnostics.json) -- " + str(len(runs)) + " runs")
    parts.append("// Layout: narrow 5-col summary + per-run collapsible card with extracted CLI command.")
    parts.append("")
    parts.append("window.TECT_RESULTS = {")
    parts.append('  title: "Numerical Results",')
    parts.append('  subtitle: "Canonical inventory auto-generated from Runs/<class>/<run_id>/. Each run carries a collapsible CLI command extracted verbatim from its RESULT.md s2 Configuration block.",')
    parts.append('  lastUpdated: "' + datetime.utcnow().strftime("%Y-%m-%d (auto)") + '",')
    parts.append('  blocks: [')

    summary_rows = []
    summary_rows.append('"<h3>Run summary (newest first)</h3>"')
    summary_rows.append('"<p>Compact 5-column overview. Click any run ID below the table to see the full CLI command + theory tag + per-point details.</p>"')
    summary_rows.append('"<table class=\\"results-runs-compact\\" style=\\"width:auto;border-collapse:collapse;\\"><thead><tr>"')
    summary_rows.append('"<th style=\\"padding:4px 8px;\\">Run ID</th><th style=\\"padding:4px 8px;\\">Status</th><th style=\\"padding:4px 8px;\\">Conv/Total</th><th style=\\"padding:4px 8px;\\">Wall (s)</th><th style=\\"padding:4px 8px;\\">RESULT.md</th>"')
    summary_rows.append('"</tr></thead><tbody>"')
    for r in runs:
        wall = "&mdash;" if r["wall_time_s"] is None else ("%.1f" % r["wall_time_s"])
        conv = "&mdash;" if r["n_converged"] is None or r["n_total"] is None else (str(r["n_converged"]) + "/" + str(r["n_total"]))
        rmd = "&#10003;" if r["has_result_md"] else "&mdash;"
        rid_short = r["run_id"][:46] + ("..." if len(r["run_id"]) > 46 else "")
        rst = (r["status"] or "").replace('"', "'")
        anchor = "run-" + re.sub(r"[^a-zA-Z0-9_-]", "-", r["run_id"])
        summary_rows.append('"<tr><td style=\\"padding:4px 8px;\\"><a href=\\"#' + anchor + '\\"><code>' + rid_short + '</code></a></td><td style=\\"padding:4px 8px;\\">' + rst + '</td><td style=\\"padding:4px 8px;\\">' + conv + '</td><td style=\\"padding:4px 8px;\\">' + wall + '</td><td style=\\"padding:4px 8px;text-align:center;\\">' + rmd + '</td></tr>"')
    summary_rows.append('"</tbody></table>"')
    parts.append('    { type: "html", content:')
    parts.append("      " + " +\n      ".join(summary_rows))
    parts.append('    },')

    parts.append('    { type: "html", content:')
    parts.append('      "<h3>Per-run details (CLI commands)</h3>" +')
    parts.append('      "<p>Each run below shows the full PowerShell / bash command exactly as launched. Post-2026-04-29 runs source from <code>RESULT.md</code> s2 Configuration; legacy runs are reconstructed from <code>MANIFEST.md</code>.</p>"')
    parts.append('    },')

    for r in runs:
        anchor = "run-" + re.sub(r"[^a-zA-Z0-9_-]", "-", r["run_id"])
        rid_safe = js_esc(r["run_id"])
        rcl_safe = js_esc(r["run_class"])
        rst_safe = js_esc(r["status"] or "")
        theory_safe = js_esc(r["theory_tag"] or "")
        cli_safe = js_esc(r["cli_command"] or "(no CLI extracted)")
        wall = "&mdash;" if r["wall_time_s"] is None else ("%.1f" % r["wall_time_s"])
        conv = "&mdash;" if r["n_converged"] is None or r["n_total"] is None else (str(r["n_converged"]) + "/" + str(r["n_total"]))
        mu2 = js_esc(r["mu2_schedule"] or "&mdash;")
        rmd_text = "&#10003; available" if r["has_result_md"] else "&mdash; absent (pre-2026-04-29)"
        diag_text = "&#10003; available" if r["has_diagnostics_json"] else "&mdash; absent (pre-v2.6.7)"
        cli_source = "RESULT.md s2" if r["has_result_md"] else "MANIFEST.md reconstruction"
        files_extra = ""
        if r["has_result_md"]:
            files_extra += ", <code>RESULT.md</code>"
        if r["has_diagnostics_json"]:
            files_extra += ", <code>run_diagnostics.json</code>"

        # v0.8 (2026-04-29): per-run download links to Website/assets/runs/<run_id>/
        # Escape: dl entries are concatenated as-is into outer JS strings, so
        # the rendered JS source must contain backslash-escaped quotes (\").
        # In a Python string literal the backslash is itself escaped → '\\\"'
        # produces literal `\"` in the rendered JS source, which JS reads as `"`.
        dl = []
        # 2026-05-01 fix: gate MANIFEST.md link on r["has_manifest_md"]
        # (added to run_info dict above). Pre-fix the link was emitted
        # unconditionally and verify_website.py flagged 4 broken-link
        # errors for legacy runs without a MANIFEST.md file
        # (math236_20260430_164956Z, _165551Z, _170121Z, _172601Z).
        if r.get("has_manifest_md", True):
            dl.append('<a href=\\\"assets/runs/' + rid_safe + '/MANIFEST.md\\\" download><code>MANIFEST.md</code></a>')
        if r["has_result_md"]:
            dl.append('<a href=\\\"assets/runs/' + rid_safe + '/RESULT.md\\\" download><code>RESULT.md</code></a>')
        if r["has_diagnostics_json"]:
            dl.append('<a href=\\\"assets/runs/' + rid_safe + '/run_diagnostics.json\\\" download><code>run_diagnostics.json</code></a>')
        for pf in ("Psi_final.npy", "Psi_checkpoint.npy"):
            asset_p = REPO_ROOT / "Website" / "assets" / "runs" / r["run_id"] / pf
            if asset_p.exists():
                dl.append('<a href=\\\"assets/runs/' + rid_safe + '/' + pf + '\\\" download><code>' + pf + '</code></a>')
        dl_links = " &middot; ".join(dl)

        body_pieces = [
            '"<details id=\\"' + anchor + '\\"><summary><strong><code>' + rid_safe + '</code></strong> &mdash; ' + rst_safe + '</summary>"',
            '"<table style=\\"margin:0.5em 0;border-collapse:collapse;\\"><tbody>"',
            '"<tr><td style=\\"padding:2px 8px;\\"><strong>Class</strong></td><td style=\\"padding:2px 8px;\\">' + rcl_safe + '</td></tr>"',
            '"<tr><td style=\\"padding:2px 8px;\\"><strong>Theory tag</strong></td><td style=\\"padding:2px 8px;\\"><code>' + theory_safe + '</code></td></tr>"',
            '"<tr><td style=\\"padding:2px 8px;\\"><strong>mu2 (1st pt)</strong></td><td style=\\"padding:2px 8px;\\">' + mu2 + '</td></tr>"',
            '"<tr><td style=\\"padding:2px 8px;\\"><strong>Conv/Total</strong></td><td style=\\"padding:2px 8px;\\">' + conv + '</td></tr>"',
            '"<tr><td style=\\"padding:2px 8px;\\"><strong>Wall</strong></td><td style=\\"padding:2px 8px;\\">' + wall + ' s</td></tr>"',
            '"<tr><td style=\\"padding:2px 8px;\\"><strong>RESULT.md</strong></td><td style=\\"padding:2px 8px;\\">' + rmd_text + '</td></tr>"',
            '"<tr><td style=\\"padding:2px 8px;\\"><strong>run_diagnostics.json</strong></td><td style=\\"padding:2px 8px;\\">' + diag_text + '</td></tr>"',
            '"</tbody></table>"',
            '"<p><strong>CLI command (verbatim from ' + cli_source + '):</strong></p>"',
            '"<pre style=\\"background:#0f172a;color:#e2e8f0;padding:0.75em;overflow-x:auto;font-size:0.85em;border-radius:4px;\\"><code>' + cli_safe + '</code></pre>"',
            '"<p style=\\"font-size:0.85em;color:#64748b;\\">Files: <code>Runs/' + rcl_safe + '/' + rid_safe + '/MANIFEST.md</code>' + files_extra + '</p>"',
            '"<p><strong>Downloads:</strong> ' + dl_links + '</p>"',
            '"</details>"',
        ]
        parts.append('    { type: "html", content:')
        parts.append("      " + " +\n      ".join(body_pieces))
        parts.append('    },')

    for title, html in cards_html:
        title_safe = title.replace('"', '\\"')
        html_safe = html.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
        parts.append('    { type: "html", content: "<h3>' + title_safe + '</h3>" + "' + html_safe + '" },')

    parts.append('    { type: "html", content:')
    parts.append('      "<h3>Most recent commits (live from CHANGELOG.md)</h3><ul>" +')
    for ch in top_changelog[:8]:
        tag_safe = js_esc(ch.raw_title or "")
        date_str = ch.date or ""
        parts.append('      "<li><strong>' + date_str + '</strong> &mdash; ' + tag_safe[:140] + '</li>" +')
    parts.append('      "</ul>"')
    parts.append('    }')
    parts.append('  ]')
    parts.append('};')
    return "\n".join(parts) + "\n"


def render_code_old_js() -> str:
    """v0.8 (2026-04-29): NEW — auto-generate code-old.js by scanning
    Codes/<subdir>/<file>.old.v*.<ext> backup pattern (per
    Docs/policy/CODE_BACKUP_POLICY.md). Also copies each backup to
    Website/assets/code-old/<original-relpath> so the file is downloadable.

    The 'old' page lets a reader retrieve any prior code version that
    produced any past numerical result, satisfying the reproducibility
    requirement: numerical run x previous code version = re-runnable
    archive.
    """
    import shutil
    codes = REPO_ROOT / "Codes"
    assets_old = WEBSITE_ROOT / "assets" / "code-old"
    assets_old.mkdir(parents=True, exist_ok=True)

    # Scan Codes/ recursively for *.old.v* files
    backups = []
    for fp in codes.rglob("*.old.v*"):
        if not fp.is_file():
            continue
        rel = fp.relative_to(codes).as_posix()
        # Parse: <stem>.old.v<version>.<ext>
        m = re.match(r"^(.+)\.old\.(v[0-9][^./]*)\.([^.]+)$", fp.name)
        if not m:
            continue
        stem, ver, ext = m.group(1), m.group(2), m.group(3)
        # Original (current) file
        original = fp.parent / (stem + "." + ext)
        # Mirror to assets/code-old preserving sub-tree under Codes/
        dest = assets_old / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(fp, dest)
        except Exception:
            pass
        backups.append({
            "rel": rel,
            "stem": stem,
            "version": ver,
            "ext": ext,
            "size": fp.stat().st_size,
            "mtime": fp.stat().st_mtime,
            "current_present": original.exists(),
            "current_rel": (fp.parent / (stem + "." + ext)).relative_to(codes).as_posix(),
        })
    # Group by current file (stem + ext + parent)
    groups = {}
    for b in backups:
        key = b["current_rel"]
        groups.setdefault(key, []).append(b)
    for k in groups:
        groups[k].sort(key=lambda x: x["version"], reverse=True)

    out = []
    out.append("// AUTO-GENERATED by Codes/tools/generate_website.py v0.8 -- DO NOT EDIT BY HAND")
    out.append("// Generated: " + datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
    out.append("// Source: Codes/<subdir>/<file>.old.v*.<ext> -- " + str(len(backups)) + " backups across " + str(len(groups)) + " files")
    out.append("")
    out.append("window.TECT_CODE_OLD = {")
    out.append('  title: "Codebase \u2014 Older Versions",')
    out.append('  subtitle: "Pre-version-bump backups of TECT code preserved per Docs/policy/CODE_BACKUP_POLICY.md. Each entry below is downloadable verbatim. Numerical runs that used these earlier versions remain re-runnable; pair the run\u0027s theory_tag with the backup that has the same version.",')
    out.append('  lastUpdated: "' + datetime.utcnow().strftime("%Y-%m-%d (auto)") + '",')
    out.append('  blocks: [')
    out.append('    { type: "html", content:')
    out.append('      "<h3>Older code versions (' + str(len(backups)) + ' backups across ' + str(len(groups)) + ' files)</h3>" +')
    out.append('      "<p>Each row shows one backup file at <code>Codes/&lt;path&gt;.old.&lt;version&gt;.&lt;ext&gt;</code>. The <em>current</em> file (left column) is the active production version; the <em>backup</em> column links to the previous version, downloadable as-is. The <a href=\\\"code.html\\\">main Codebase page</a> shows only current versions.</p>" +')
    out.append('      "<p><strong>Reproducibility rule</strong>: each numerical run on the <a href=\\\"results.html\\\">Results page</a> declares its <code>theory_tag</code> and <code>driver_version</code>. To re-run a past result, download the backup whose version matches that run\u0027s manifest.</p>"')
    out.append('    },')

    if not backups:
        out.append('    { type: "html", content: "<p><em>No backups detected. The first time a code file is version-bumped, run <code>bash Codes/scripts/backup_code.sh &lt;path&gt;</code> to create a side-by-side <code>.old.v&lt;X&gt;.&lt;ext&gt;</code> snapshot.</em></p>" },')
    else:
        out.append('    { type: "html", content:')
        out.append('      "<table class=\"old-versions\" style=\"border-collapse:collapse;\"><thead><tr>" +')
        out.append('      "<th style=\"padding:4px 8px;\">Current file</th>" +')
        out.append('      "<th style=\"padding:4px 8px;\">Version</th>" +')
        out.append('      "<th style=\"padding:4px 8px;\">Backup file (download)</th>" +')
        out.append('      "<th style=\"padding:4px 8px;\">Size (bytes)</th>" +')
        out.append('      "</tr></thead><tbody>"')
        for cur in sorted(groups.keys()):
            for b in groups[cur]:
                cur_safe = cur.replace('"', "'")
                ver_safe = b["version"].replace('"', "'")
                rel_safe = b["rel"].replace('"', "'")
                size_str = "{:,}".format(b["size"])
                cur_present_marker = "&#10003;" if b["current_present"] else "&mdash;"
                out.append('      + "<tr><td style=\"padding:4px 8px;\"><code>Codes/' + cur_safe + '</code> ' + cur_present_marker + '</td>" +')
                out.append('      "<td style=\"padding:4px 8px;\"><strong>' + ver_safe + '</strong></td>" +')
                out.append('      "<td style=\"padding:4px 8px;\"><a href=\"assets/code-old/' + rel_safe + '\" download><code>' + rel_safe + '</code></a></td>" +')
                out.append('      "<td style=\"padding:4px 8px;text-align:right;\">' + size_str + '</td></tr>"')
        out.append('      + "</tbody></table>"')
        out.append('    },')

    out.append('    { type: "html", content:')
    out.append('      "<h3>Backup policy</h3>" +')
    out.append('      "<p>Defined in <code>Docs/policy/CODE_BACKUP_POLICY.md</code> (binding from 2026-04-29). Whenever a TECT code file is version-bumped, a backup is created at <code>&lt;dir&gt;/&lt;stem&gt;.old.&lt;version&gt;.&lt;ext&gt;</code> using the helper script <code>Codes/scripts/backup_code.sh</code>. The backup is committed in the same atomic git commit as the version bump.</p>" +')
    out.append('      "<p>Append-only trail: <code>Codes/_backup_log.md</code> records date, source, backup path, version, and git SHA per snapshot.</p>" +')
    out.append('      "<p><a href=\\\"code.html\\\">&larr; Back to current Codebase</a></p>"')
    out.append('    }')
    out.append('  ]')
    out.append('};')
    return "\n".join(out) + "\n"



def _extract_file_purpose(fp):
    """v0.10 (2026-04-29): curated one-line purpose per file basename.
    Manual mapping is more reliable than docstring-extraction; auto-extract
    was confused by TECT-header boilerplate. Add new entries when new code
    files are introduced."""
    PURPOSE = {
        # PDE solver core
        "continuation_mu2_v25.py": "Newton-Krylov mu2-continuation driver with v2.6.7 newton_history persistence.",
        "continuation_mu2.py": "Earlier Newton-Krylov continuation driver (superseded by v25).",
        "continuation_mu2_fast.py": "Fast-iteration variant for short-tcg sweeps.",
        "record_run.py": "Universal driver-agnostic numerical-run recorder (run_diagnostics.json + RESULT.md skeleton).",
        "RESULT_TEMPLATE.md": "Per-run RESULT.md standard template (10 sections).",
        "bcc_analytic_seed.py": "Closed-form rank-2 BCC seed generator.",
        "bloch_linearization.py": "Bloch-momentum linearisation around BCC ground state.",
        "bz_eta_integrator.py": "Brazovskii eta-flow ODE integrator.",
        "bz_preconditioner.py": "Brazovskii-spectrum preconditioner for Krylov inner solver.",
        "bz_shell_adaptive.py": "Adaptive shell-projector for Brazovskii kinetic operator.",
        "carrier_audit.py": "Carrier-channel audit (per-mode contribution diagnostics).",
        "dirac_index_bcc.py": "Atiyah-Singer index extraction on BCC defect bundles.",
        "hess_jump_audit.py": "Hessian-jump second-order acceptance audit.",
        "intervalley_extractor_v4.py": "Intervalley coupling extractor (4-channel).",
        "live_m_parallel.py": "Parallel live-m diagnostic during continuation.",
        "make_rank2_bcc_seed.py": "Generate randomised rank-2 BCC seeds.",
        "math46_c2_extractor.py": "C2 second-Chern-class numerical extractor (Math46).",
        "math46_c3_extractor.py": "C3 third-Chern-class numerical extractor.",
        "math49c_v3_sim.py": "Math49c v3 spin-statistics simulation.",
        "math56_constants.py": "Math56 Brazovskii canonical-constants module.",
        "phase4_manual_extrapolation.py": "Phase-4 manual continuum extrapolation.",
        "projector_spectral.py": "Spectral projector onto BCC zero-mode subspace.",
        "q18_commensurability_sweep.py": "q18 commensurability sweep (Q18 question).",
        "rank2_check.py": "Rank-2 ansatz consistency checker.",
        "real_backend_pt_bcc_mixed_v3.py": "Real-backend PyTorch BCC mixed-precision implementation.",
        "remote_gap_audit.py": "Remote-mode gap-audit for spectral-gap claims.",
        "run_audit_pipeline.py": "Full audit-pipeline orchestrator.",
        "run_pipeline_n1.py": "N=1 pipeline single-shot run wrapper.",
        "stamp_version_headers.py": "Auto-stamp __version__ / __theory_version__ in PDE/*.py.",
        "sweep_mu2_phase3.py": "Phase-3 mu2-parameter sweep.",
        # Tools
        "build_version_index.py": "Auto-generate Website/data/version_index.json from canonical sources.",
        "cII_energy_candidates.py": "Candidate-list scanner for cII energy threshold.",
        "check_jacobian_blocks.py": "Jacobian block-structure verifier.",
        "check_jacobian_symmetry.py": "Jacobian symmetry probe (symmetric / asymmetric / indefinite).",
        "check_review_cadence.py": "OPEN-QUESTIONS / EVIDENCE-INDEX cadence monitor.",
        "compute_RF5.py": "RF5 anomaly coefficient computation.",
        "compute_aBCC_continuum.py": "Continuum-limit a_BCC extractor.",
        "extract_G_TECT.py": "Extract Newton's G from TECT primitive lattice inputs.",
        "extract_hbar_TECT.py": "Extract hbar from TECT primitive lattice inputs.",
        "generate_website.py": "Auto-generate Website/data/*.js + Website/assets/* from canonical sources.",
        "verify_website.py": "Website completeness + correctness verifier (CLAUDE.md s6.3.7 binding).",
        # Scripts
        "sandbox_commit.sh": "Sandbox-side atomic-commit helper (refuses forbidden file patterns).",
        "cleanup_root.ps1": "Auto-clean root-of-repo stray files (per REPO_LAYOUT.md s6).",
        "backup_code.sh": "Pre-edit code backup helper (per CODE_BACKUP_POLICY.md): creates <stem>.old.<version>.<ext>.",
        # Tests
        "__init__.py": "Package initialiser.",
    }
    return _extract_file_purpose_by_name(fp.name)


def _extract_file_purpose_by_name(name):
    """Basename-only variant; safe for use in inner loops where Path object
    is not in scope (avoids variable-capture bugs)."""
    PURPOSE = {
        # PDE solver core
        "continuation_mu2_v25.py": "Newton-Krylov mu2-continuation driver with v2.6.7 newton_history persistence.",
        "continuation_mu2.py": "Earlier Newton-Krylov continuation driver (superseded by v25).",
        "continuation_mu2_fast.py": "Fast-iteration variant for short-tcg sweeps.",
        "record_run.py": "Universal driver-agnostic numerical-run recorder (run_diagnostics.json + RESULT.md skeleton).",
        "RESULT_TEMPLATE.md": "Per-run RESULT.md standard template (10 sections).",
        "bcc_analytic_seed.py": "Closed-form rank-2 BCC seed generator.",
        "bloch_linearization.py": "Bloch-momentum linearisation around BCC ground state.",
        "bz_eta_integrator.py": "Brazovskii eta-flow ODE integrator.",
        "bz_preconditioner.py": "Brazovskii-spectrum preconditioner for Krylov inner solver.",
        "bz_shell_adaptive.py": "Adaptive shell-projector for Brazovskii kinetic operator.",
        "carrier_audit.py": "Carrier-channel audit (per-mode contribution diagnostics).",
        "dirac_index_bcc.py": "Atiyah-Singer index extraction on BCC defect bundles.",
        "hess_jump_audit.py": "Hessian-jump second-order acceptance audit.",
        "intervalley_extractor_v4.py": "Intervalley coupling extractor (4-channel).",
        "live_m_parallel.py": "Parallel live-m diagnostic during continuation.",
        "make_rank2_bcc_seed.py": "Generate randomised rank-2 BCC seeds.",
        "math46_c2_extractor.py": "C2 second-Chern-class numerical extractor (Math46).",
        "math46_c3_extractor.py": "C3 third-Chern-class numerical extractor.",
        "math49c_v3_sim.py": "Math49c v3 spin-statistics simulation.",
        "math56_constants.py": "Math56 Brazovskii canonical-constants module.",
        "phase4_manual_extrapolation.py": "Phase-4 manual continuum extrapolation.",
        "projector_spectral.py": "Spectral projector onto BCC zero-mode subspace.",
        "q18_commensurability_sweep.py": "q18 commensurability sweep (Q18 question).",
        "rank2_check.py": "Rank-2 ansatz consistency checker.",
        "real_backend_pt_bcc_mixed_v3.py": "Real-backend PyTorch BCC mixed-precision implementation.",
        "remote_gap_audit.py": "Remote-mode gap-audit for spectral-gap claims.",
        "run_audit_pipeline.py": "Full audit-pipeline orchestrator.",
        "run_pipeline_n1.py": "N=1 pipeline single-shot run wrapper.",
        "stamp_version_headers.py": "Auto-stamp __version__ / __theory_version__ in PDE/*.py.",
        "sweep_mu2_phase3.py": "Phase-3 mu2-parameter sweep.",
        "backend_consistency_audit.py": "Cross-backend (numpy / torch) consistency audit.",
        # Tools
        "build_version_index.py": "Auto-generate Website/data/version_index.json from canonical sources.",
        "cII_energy_candidates.py": "Candidate-list scanner for cII energy threshold.",
        "check_jacobian_blocks.py": "Jacobian block-structure verifier.",
        "check_jacobian_symmetry.py": "Jacobian symmetry probe (symmetric / asymmetric / indefinite).",
        "check_review_cadence.py": "OPEN-QUESTIONS / EVIDENCE-INDEX cadence monitor.",
        "compute_RF5.py": "RF5 anomaly coefficient computation.",
        "compute_aBCC_continuum.py": "Continuum-limit a_BCC extractor.",
        "extract_G_TECT.py": "Extract Newton's G from TECT primitive lattice inputs.",
        "extract_hbar_TECT.py": "Extract hbar from TECT primitive lattice inputs.",
        "generate_website.py": "Auto-generate Website/data/*.js + Website/assets/* from canonical sources.",
        "verify_website.py": "Website completeness + correctness verifier (CLAUDE.md s6.3.7 binding).",
        # Scripts
        "sandbox_commit.sh": "Sandbox-side atomic-commit helper (refuses forbidden file patterns).",
        "cleanup_root.ps1": "Auto-clean root-of-repo stray files (per REPO_LAYOUT.md s6).",
        "backup_code.sh": "Pre-edit code backup helper (per CODE_BACKUP_POLICY.md): creates <stem>.old.<version>.<ext>.",
        # Tests
        "__init__.py": "Package initialiser.",
    }
    if name in PURPOSE:
        return PURPOSE[name]
    # backup-versioned files: continuation_mu2_v25.old.v2.6.6.py
    m_old = re.match(r"^(.+)\.old\.v[\d.]+\.(?:py|sh|ps1|md|json|txt)$", name)
    if m_old:
        stem = m_old.group(1)
        for ext in (".py", ".sh", ".ps1", ".md", ".json", ".txt"):
            cand = stem + ext
            if cand in PURPOSE:
                return f"[backup snapshot] {PURPOSE[cand]}"
        return "[backup snapshot] Pre-version-bump archive."
    # supplementary Math*.py: extract Math number
    m = re.match(r"^(Math\d+)[_a-zA-Z0-9]*\.py$", name)
    if m:
        return f"Math note attached numerical script ({m.group(1)})."
    if name.endswith(".json"):
        return "Configuration / output JSON."
    if name.endswith((".sh", ".ps1", ".bat")):
        return "Shell / script."
    return ""


def render_code_js() -> str:
    sections = [
        ("PDE solver core", "pde", CODES_DIR / "pde",
         "Live numerical core: Newton-Krylov solver, Brazovskii backends, BCC-defect operators, BCC analytic seed, continuation drivers, projector / Hessian extractors."),
        ("Diagnostic tools", "tools", CODES_DIR / "tools",
         "Repository-discipline + audit utilities: Jacobian-symmetry probe, version stamper, generate_website.py, code-manual sync."),
        ("Supplementary verification scripts", "supplementary", CODES_DIR / "supplementary",
         "Math-note-attached numerical scripts: PV-scheme verification, RGE integration, residual-channel audits."),
        ("PowerShell / bash scripts", "scripts", CODES_DIR / "scripts",
         "Run drivers, sandbox-side commit helper, batch operations."),
        ("Test suite", "tests", CODES_DIR / "tests",
         "Pytest regression suite for solver + tools."),
    ]
    allowed_ext = {".py", ".sh", ".ps1", ".bat", ".json", ".md", ".txt"}
    lines = []
    lines.append("// AUTO-GENERATED by Codes/tools/generate_website.py v0.4 -- DO NOT EDIT BY HAND")
    lines.append(f"// Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("// Source: Codes/{pde,tools,supplementary,scripts,tests}/ -- automatic inventory")
    lines.append("")
    lines.append("window.TECT_CODE = {")
    lines.append('  title: "Codebase",')
    lines.append('  subtitle: "All code modules under Codes/ - auto-generated inventory with direct download links. New files appear, removed files disappear, and modification dates update on each website regeneration.",')
    lines.append(f'  lastUpdated: "{datetime.utcnow().strftime("%Y-%m-%d (auto)")}",')
    lines.append('  blocks: [')
    lines.append('    { type: "html", content: "<p>Click any filename to download the file directly. The full <a href=\\"assets/manifest.json\\">asset manifest</a> lists every shipped file with size in bytes. Files are physically copied into <code>Website/assets/code/</code> by the publish step (<code>generate_website.py --copy-assets</code> or <code>--publish</code>); old/removed source files automatically disappear on the next regeneration.</p>" + "<p style=\\"padding:0.6em;background:#f1f5f9;border-left:3px solid #0ea5e9;\\"><strong>&rarr; <a href=\\"code-old.html\\">Older versions (downloadable backups)</a></strong> &mdash; pre-version-bump snapshots per <code>Docs/policy/CODE_BACKUP_POLICY.md</code>. Pair a numerical run\\u0027s <code>theory_tag</code> + <code>driver_version</code> with the matching backup to reproduce past results.</p>" },')
    n_total = 0
    for title, dest_subdir, src_dir, description in sections:
        if not src_dir.exists():
            continue
        files = []
        for fp in sorted(src_dir.rglob("*")):
            if not fp.is_file() or fp.suffix.lower() not in allowed_ext:
                continue
            try:
                size = fp.stat().st_size
                if size > COPY_MAX_SIZE:
                    continue
                files.append((fp.relative_to(src_dir).as_posix(), size,
                              datetime.fromtimestamp(fp.stat().st_mtime).strftime("%Y-%m-%d"),
                              fp.name))
            except Exception:
                continue
        if not files:
            continue
        n_total += len(files)
        lines.append('    {')
        lines.append('      type: "card",')
        lines.append(f'      title: "{js_string_escape(title)} ({len(files)} files)",')
        lines.append('      blocks: [')
        lines.append(f'        {{ type: "html", content: "<p class=\\"muted\\">{js_string_escape(description)}</p>" }},')
        lines.append('        {')
        lines.append('          type: "table",')
        lines.append('          headers: ["File", "Size", "Modified", "Purpose"],')
        lines.append('          rows: [')
        for rel, sz, mt, basename in files:
            sz_str = f"{sz/1024:.1f} KB" if sz < 1024*1024 else f"{sz/1024/1024:.2f} MB"
            asset_path = f"assets/code/{dest_subdir}/{rel}"
            purpose = _extract_file_purpose_by_name(basename).replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'            ["<a href=\\"{asset_path}\\" download><code>{js_string_escape(rel)}</code></a>", "{sz_str}", "{mt}", "{purpose}"],')
        if files and lines[-1].endswith(","):
            lines[-1] = lines[-1][:-1]
        lines.append('          ]')
        lines.append('        }')
        lines.append('      ]')
        lines.append('    },')
    if lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append('  ],')
    lines.append(f'  footerNote: "Total modules indexed: {n_total}. New files added to Codes/ appear here automatically on the next generate_website.py --all run."')
    lines.append("};")
    return "\n".join(lines)



def render_history_page_js(entries, nav, var_name="TECT_HISTORY"):
    lines = []
    lines.append(f"// AUTO-GENERATED v0.3 page {nav['page']}/{nav['total']} — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"window.{var_name} = {{")
    lines.append(f'  title: "History (page {nav["page"]} of {nav["total"]})",')
    lines.append(f'  subtitle: "Chronological CHANGELOG mirror — auto-generated.",')
    lines.append(f'  lastUpdated: "{datetime.utcnow().strftime("%Y-%m-%d (auto)")}",')
    pagination_obj = {
        "page": nav["page"],
        "total": nav["total"],
        "newer": nav["newer"],
        "older": nav["older"],
        "archiveIndex": "history-archive-index.html",
    }
    lines.append(f'  pagination: {json.dumps(pagination_obj)},')
    lines.append('  blocks: [')
    nav_html = []
    if nav["newer"]: nav_html.append(f'<a href=\\"{nav["newer"]}\\">&larr; Newer</a>')
    nav_html.append(f'Page {nav["page"]} / {nav["total"]}')
    nav_html.append('<a href=\\"history-archive-index.html\\">archive index</a>')
    if nav["older"]: nav_html.append(f'<a href=\\"{nav["older"]}\\">Older &rarr;</a>')
    nav_str = " &middot; ".join(nav_html)
    lines.append('    { type: "html", content: "<div class=\\"pagination-nav\\">' + nav_str + '</div>" },')
    lines.append('    { type: "timeline", items: [')
    for entry in entries:
        title = js_string_escape(entry.raw_title)[:200]
        body = js_string_escape(entry.body_first_paragraph or "")[:1200]
        lines.append("        {")
        lines.append(f'          date: "{entry.date}",')
        lines.append(f'          title: "{title}",')
        lines.append(f'          body: "{body}"')
        lines.append("        },")
    if entries and lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append("      ]")
    lines.append('    },')
    lines.append('    { type: "html", content: "<div class=\\"pagination-nav\\">' + nav_str + '</div>" }')
    lines.append("  ]")
    lines.append("};")
    return "\n".join(lines)


def render_history_archive_index(pages):
    lines = []
    lines.append(f"// AUTO-GENERATED v0.3 history archive index — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("window.TECT_HISTORY_ARCHIVE_INDEX = {")
    lines.append('  title: "History Archive Index",')
    lines.append(f'  subtitle: "All history pages (newest first). Each contains up to {HISTORY_PAGE_SIZE} CHANGELOG entries.",')
    lines.append(f'  lastUpdated: "{datetime.utcnow().strftime("%Y-%m-%d (auto)")}",')
    lines.append('  blocks: [{ type: "card", title: "All history pages", blocks: [{ type: "list", items: [')
    for page_idx, entries, nav in pages:
        date_range = ""
        if entries:
            dates = [e.date for e in entries if e.date]
            if dates:
                date_range = f" ({dates[-1]} to {dates[0]})"
        link = nav["current_filename"]
        lines.append(f'    "<a href=\\"{link}\\">Page {page_idx} of {len(pages)}{date_range}</a>",')
    if pages and lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append("  ] }] }] };")
    return "\n".join(lines)


# v0.5 (2026-04-27): MANUAL_OVERRIDE marker mechanism. A hand-curated
# data file (e.g. index.js / theory.js / states.js / toe.js / papers.js
# / site.js after the rev-3..rev-5 website restructure) contains the
# string "@MANUAL_OVERRIDE" in a comment or docstring. write_or_check
# detects this marker and skips regeneration with a [skipped] message,
# preventing the generator from clobbering hand-curated narrative content.
# To re-enable auto-generation of a previously-overridden file, remove
# the @MANUAL_OVERRIDE marker (or replace the file with auto output).
MANUAL_OVERRIDE_MARKER = "@MANUAL_OVERRIDE"


def write_or_check(target, content, check):
    if target.exists():
        old = target.read_text(encoding="utf-8", errors="replace")
        # v0.5 manual-override guard: do not overwrite hand-curated files.
        if MANUAL_OVERRIDE_MARKER in old:
            return False, (
                f"  [skipped] {target.relative_to(REPO_ROOT)} "
                f"(@MANUAL_OVERRIDE present; hand-curated, generator declines to write)"
            )
        if old == content:
            return False, f"  [unchanged] {target.relative_to(REPO_ROOT)}"
        else:
            change_msg = f"  [changed] {target.relative_to(REPO_ROOT)} ({len(old)} -> {len(content)} bytes)"
    else:
        change_msg = f"  [created] {target.relative_to(REPO_ROOT)} ({len(content)} bytes)"
    if not check:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
    return True, change_msg


def main():
    parser = argparse.ArgumentParser(description="Auto-generate Website/data/*.js from canonical Docs/ + _narrative/ . v0.3: pagination + asset copy + standalone publish.")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--math-notes", action="store_true")
    parser.add_argument("--timeline", action="store_true")
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--theory", action="store_true")
    parser.add_argument("--index", action="store_true")
    parser.add_argument("--records", action="store_true")
    parser.add_argument("--code", action="store_true", help="v0.4: regenerate code.js auto-inventory")
    parser.add_argument("--results", action="store_true", help="v0.6: regenerate results.js from Runs/<class>/<run_id>/")
    parser.add_argument("--code-old", action="store_true", help="v0.8: regenerate code-old.js + copy backups to Website/assets/code-old/")
    parser.add_argument("--copy-assets", action="store_true", help="v0.3: copy Docs/+Codes/+Runs/ to Website/assets/")
    parser.add_argument("--publish", action="store_true", help="v0.3: --all + --copy-assets")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--top-n", type=int, default=30)
    args = parser.parse_args()

    if args.publish:
        args.all = True; args.copy_assets = True

    if not any([args.all, args.math_notes, args.timeline, args.history, args.theory, args.index, args.records, args.code, args.code_old, args.results, args.copy_assets]):
        args.all = True

    print("=" * 70, flush=True)
    print(f" generate_website.py v0.3 {'(DRY-RUN)' if args.check else ''}", flush=True)
    print("=" * 70, flush=True)
    print(f"  REPO_ROOT : {REPO_ROOT}", flush=True)
    print(f"  WEBSITE   : {WEBSITE_ROOT}", flush=True)

    print("\n--- Parsing canonical sources ---", flush=True)
    notes = collect_math_notes()
    print(f"  Math notes parsed: {len(notes)}", flush=True)
    changelog = parse_changelog(top_n=args.top_n)
    full_changelog = parse_changelog(top_n=10000)
    print(f"  CHANGELOG entries (top {args.top_n}): {len(changelog)}; full: {len(full_changelog)}", flush=True)
    open_qs = parse_open_questions()
    print(f"  OPEN-QUESTIONS Active: {len(open_qs)}", flush=True)
    neg_results = parse_negative_results()
    print(f"  NEGATIVE-RESULTS: {len(neg_results)}", flush=True)
    scorecard = parse_toe_fact_sheet_scorecard()
    print(f"  TOE-FACT-SHEET pillars: {len(scorecard)}", flush=True)
    if NARRATIVE_DIR.exists():
        print(f"  Narrative .md files: {len(list(NARRATIVE_DIR.glob('*.md')))}", flush=True)

    print("\n--- Rendering data targets ---", flush=True)
    n_changed = 0

    if args.all or args.math_notes:
        c, m = write_or_check(WEB_DATA / "math-notes.js", render_math_notes_js(notes), args.check)
        print(m, flush=True); n_changed += c
    if args.all or args.timeline:
        c, m = write_or_check(WEB_DATA / "timeline.json", render_timeline_json(changelog), args.check)
        print(m, flush=True); n_changed += c
    if args.all or args.history:
        if len(full_changelog) > HISTORY_PAGE_SIZE:
            pages = paginate_changelog(full_changelog, page_size=HISTORY_PAGE_SIZE)
            page_1 = pages[0]
            c, m = write_or_check(WEB_DATA / "history.js", render_history_page_js(page_1[1], page_1[2]), args.check)
            print(m, flush=True); n_changed += c
            archive_dir = WEB_DATA / "_archive"
            if not args.check:
                archive_dir.mkdir(parents=True, exist_ok=True)
            for page_idx, entries, nav in pages[1:]:
                fname = f"history-page-{page_idx:03d}.js"
                var_name = f"TECT_HISTORY_PAGE_{page_idx:03d}"
                c, m = write_or_check(archive_dir / fname, render_history_page_js(entries, nav, var_name=var_name), args.check)
                print(m, flush=True); n_changed += c
                if write_history_page_html_wrapper(WEBSITE_ROOT / f"history-page-{page_idx:03d}.html", var_name=var_name, js_relpath=f"data/_archive/history-page-{page_idx:03d}.js", page_label=f"History (page {page_idx} of {nav['total']})", check=args.check):
                    print(f"  [created] Website/history-page-{page_idx:03d}.html", flush=True); n_changed += 1
            c, m = write_or_check(archive_dir / "history-archive-index.js", render_history_archive_index(pages), args.check)
            print(m, flush=True); n_changed += c
            if write_history_page_html_wrapper(WEBSITE_ROOT / "history-archive-index.html", var_name="TECT_HISTORY_ARCHIVE_INDEX", js_relpath="data/_archive/history-archive-index.js", page_label="History -- archive index", check=args.check):
                print("  [created] Website/history-archive-index.html", flush=True); n_changed += 1
            print(f"  History pagination: {len(pages)} pages ({HISTORY_PAGE_SIZE}/page); HTML wrappers at Website/ root", flush=True)
        else:
            c, m = write_or_check(WEB_DATA / "history.js", render_history_js(full_changelog), args.check)
            print(m, flush=True); n_changed += c
    if args.all or args.theory:
        c, m = write_or_check(WEB_DATA / "theory.js", render_theory_js(scorecard, changelog), args.check)
        print(m, flush=True); n_changed += c
    if args.all or args.index:
        c, m = write_or_check(WEB_DATA / "index.js", render_index_js(scorecard, changelog, len(notes)), args.check)
        print(m, flush=True); n_changed += c
    if args.all or args.records:
        c, m = write_or_check(WEB_DATA / "records.js", render_records_js(open_qs, neg_results), args.check)
        print(m, flush=True); n_changed += c
    if args.all or args.results:
        c, m = write_or_check(WEB_DATA / "results.js", render_results_js(changelog), args.check)
        print(m, flush=True); n_changed += c

    if args.all or args.code:
        c, m = write_or_check(WEB_DATA / "code.js", render_code_js(), args.check)
        print(m, flush=True); n_changed += c

    if args.all or args.code_old:
        c, m = write_or_check(WEB_DATA / "code-old.js", render_code_old_js(), args.check)
        print(m, flush=True); n_changed += c

    if args.copy_assets:
        copy_assets(check=args.check)

    print(f"\n--- Done: {n_changed} data target(s) {'would change' if args.check else 'changed'} ---", flush=True)
    if args.copy_assets and not args.check:
        print(f"  Website/ is now self-contained: upload the entire Website/ folder to publish.", flush=True)




if __name__ == "__main__":
    main()
