---
decisionId: add-outlet-country-aliases
title: Add aliases field to Outlet and Country YAML registries
status: accepted
date: 2026-07-06
affects: [entities/outlet, entities/country]
---

## Context
Cascade-created entity notes in `outlet` and `country` follow the vault's doubled-slug filename
convention (`<id>-<id>.md`, e.g. `8days-8days.md`, `singapore-singapore.md`). Obsidian resolves
`[[wikilinks]]` by matching a filename or a registered `aliases:` frontmatter entry — never a
folder-qualified path or an arbitrary `displayName` field. Articles link to these entities using
their plain display name (e.g. `[[8Days]]`, `[[Singapore]]`), which does not match the doubled-slug
filename and, until now, had no `aliases` field to resolve through.

This surfaced concretely on 2026-07-06 while cascading article `816663`: the article's `[[Singapore]]`
link, and a corrected `[[8Days]]` link (originally miswritten as `[[Outlet/8Days]]`, which caused
Obsidian to auto-create a stray empty note), had no registered field to resolve to the real notes.

Every other entity domain (`organisations`, `people`, `topic`) already carries an `aliases` field in
its frozen registry for exactly this reason; `outlet` and `country` were the two exceptions.

## Decision
Add `aliases: list` to the frozen YAML registry of both `entities/outlet/index.md` and
`entities/country/index.md`, matching the field's definition in the sibling domains — alternate
names/acronyms a wikilink may use to resolve to this note. At minimum, every note's own `displayName`
should also appear in its own `aliases` list, since the doubled-slug filename never matches the
display name on its own.

## Consequences
- `entities/outlet/index.md` and `entities/country/index.md` registries updated to include `aliases`;
  both domains' templates updated to match. `catalog.md` for both now shows an `aliases` column
  automatically (the generator reads its column set from each domain's registry table).
- `entities/outlet/8days-8days.md` and `entities/country/singapore-singapore.md` — the two notes
  touched by the `816663` cascade — backfilled with `aliases: [8Days]` / `aliases: [Singapore]`.
- The other 393 outlet notes, and any future country notes, are **not** retroactively backfilled —
  `aliases` is populated on demand by cascade as each note is next touched, consistent with how the
  field already behaves in `organisations`/`people`/`topic`.
- Article `816663`'s `[[Outlet/8Days]]` link corrected to the bare `[[8Days]]`, matching the
  vault-wide bare-filename link convention documented in `scripts/entity_cascade_procedure.md`.
