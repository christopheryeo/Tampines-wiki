---
decisionId: drop-doubled-slug-filenames
title: Drop the doubled <id>-<id>.md filename convention for entity domains
status: accepted
date: 2026-07-06
affects: [entities/outlet, entities/organisations, entities/people, entities/topic, entities/country, entities/place]
---

## Context
Every entity-domain note (outlet, organisation, person, topic, country, place) was named
`<id>-<id>.md` — e.g. `mindef-mindef.md`, `straits-times-straits-times.md`. The `entities/outlet/`
notes predate this session (created 2026-07-03); the convention was copied into every newer domain
for consistency without re-examining why it existed.

The mechanical cause: a single filename template, `f"{id}-{slug(title)}.md"`, applied uniformly
across the vault. For `article` notes this is sensible (`sourceId` and the title-slug are different
strings). For entity domains, the id field (`outletId`, `orgId`, ...) already **is** the slugified
display name, so the same template doubles it: `mindef` + `-` + `slug("MINDEF")` = `mindef-mindef`.

This doubling is the root enabling cause of the link-resolution incident on 2026-07-06 (see
[[add-outlet-country-aliases]] and `scripts/entity_cascade_procedure.md`'s "Why piped links, always"
section): a bare wikilink typed as the display name (`[[MINDEF]]`) can never match a doubled
filename, forcing reliance on `aliases:` frontmatter resolution — which then proved fragile against
both invalid YAML (unquoted `#` in flow lists) and Obsidian cache staleness. Piped links
(`[[mindef|MINDEF]]`) fixed the immediate symptom, but the doubled filename was the unforced error
underneath it.

## Decision
Entity-domain filenames are simply `<id>.md` — no doubling. Applied to all six entity domains:
`outlet` (395 notes, renamed), `organisations` (2), `country` (1), `place` (3), `people` (0, schema
only), `topic` (0, schema only). Every note's own frontmatter `<x>Id` field remains the source of
truth for its filename; the rename was driven by re-reading each note's id field, not by
pattern-matching the old filename text.

`article` notes are unaffected — `<sourceId>-<slugified-title>.md` stays as-is, since `sourceId` and
the title-slug are genuinely different strings there and the doubling problem doesn't apply.

Piped links (`[[real-filename|Display Name]]`) remain mandatory for every cascade-created
cross-reference regardless of this fix — the filename simplification removes the *original reason*
alias-dependent bare links were ever fragile, but piped links are still the safer default per
[[add-outlet-country-aliases]] and are not being reverted.

## Consequences
- Renamed 401 files total across `entities/outlet/` (395), `entities/organisations/` (2),
  `entities/country/` (1), `entities/place/` (3), driven by each file's own `<x>Id` frontmatter
  field via `/tmp/rename_migration.py`.
- Rewrote every referencing wikilink vault-wide (8 files: the article, 5 entity notes, and
  `scripts/entity_cascade_procedure.md`) to point at the new filenames, preserving piped display
  text.
- Updated the "Naming" rule in `entities/{outlet,organisations,people,topic,country,place}/index.md`
  from `<id>-<id>.md` to `<id>.md`.
- Regenerated `catalog.md` for `outlet`, `organisations`, `country`, `place`.
- `entities/decisions/index.md`'s own naming convention ("no doubled-slug filename... unlike the
  cascade-populated entity domains") is now just "no doubled-slug filename" — entity domains match
  the decisions domain's convention now, not the reverse.
