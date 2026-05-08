**Four-ledger records model.** The TECT project records are structured as four append-only ledgers plus an evidence-index navigation layer:

- **Proved** (`CHANGELOG.md` + `Docs/status/research-log.md`): one row per theory tag / milestone. See [History](history.html) for the chronological mirror.
- **Failed** (`Docs/status/NEGATIVE-RESULTS.md`): F (failed hypothesis), R (retracted result), D (dead-end approach) entries. Never redacted.
- **Open** (`Docs/status/OPEN-QUESTIONS.md`): active conjectures and numerical frontiers with Q-tags and 30/60/90-day review cadence.
- **Index** (`Docs/status/EVIDENCE-INDEX.md`): live claim → evidence map.

Below: the auto-generated lists of currently-active OPEN questions and all NEGATIVE-RESULTS entries, extracted from the canonical `Docs/status/` markdown ledgers by `Codes/tools/generate_website.py`.
