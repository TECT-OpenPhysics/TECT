# Website/data/_narrative/ — User-editable narrative content

This directory holds the narrative prose blocks that complement the
auto-generated lists and tables in `Website/data/*.js`. Edit any `.md`
file here and re-run `python -u Codes/tools/generate_website.py --all`
to refresh the website.

## File mapping

Each `.md` file is composed into one or more `Website/data/*.js` files
by the generator. The composition map is:

| Narrative file | Inserted into | Position |
|---|---|---|
| `index_subtitle.md` | `index.js` | `subtitle` field |
| `index_about.md` | `index.js` | top card "What is TECT?" |
| `index_how_to_read.md` | `index.js` | second card |
| `theory_subtitle.md` | `theory.js` | `subtitle` field |
| `theory_axiom.md` | `theory.js` | first card |
| `theory_regime.md` | `theory.js` | second card |
| `theory_locked_params.md` | `theory.js` | third card |
| `theory_honest_positioning.md` | `theory.js` | bottom card |
| `history_subtitle.md` | `history.js` | `subtitle` field |
| `history_milestones.md` | `history.js` | top milestones timeline |
| `results_assessment.md` | `results.js` | top "Honest-status assessment" card |
| `records_intro.md` | `records.js` | top intro paragraph |

Files not in this map are ignored by the generator (you can use them
for drafts, notes, or future additions).

## Format

Plain Markdown. The generator supports:

- Paragraphs (separated by blank lines)
- Headings (`## h2`, `### h3`)
- Bullet lists (`- item`)
- Numbered lists (`1. item`)
- `inline code`
- **bold**, *italic*
- Links: `[text](url)`
- Inline math: `$ x = y $`
- Display math: `$$ x = y $$`

HTML tags are passed through verbatim (use sparingly).

## Workflow

1. Edit any `.md` file with your narrative content.
2. Run `python -u Codes/tools/generate_website.py --all` to regenerate
   the corresponding `.js` files.
3. Commit the changed `.js` files (and the `.md` source) together.

## Adding a new narrative section

1. Create the `.md` file in this directory.
2. Add an entry to the composition map in
   `Codes/tools/generate_website.py` constant `NARRATIVE_MAP`.
3. The generator's renderer for the target page will pick it up.

## Why this architecture?

Pre-v0.2 the website data files (`*.js`) mixed pure data (lists of
Math notes, CHANGELOG entries, Open Questions) with hand-written
narrative prose. Updating the data caused the prose to drift; updating
the prose risked clobbering data. v0.2 separates the two: data is
auto-extracted from canonical `Docs/` and prose lives here in editable
`.md` files. Re-running the generator composes both into the final
`.js` output.

See `Docs/math/TECT-Math84-Website-Generator-Architecture.tex.txt` for
the formal design rationale.
