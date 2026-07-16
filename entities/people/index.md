---
type: domain-index
domain: People
subtype: person
status: active
last_updated: 2026-07-06
---

# Domain: Entities — People

**Purpose:** the canonical record for every named individual surfaced in SAF/MINDEF-relevant coverage — ministers, officers, spokespeople, analysts, and quoted sources appearing in article `Related Entities`. Each note is a lean Layer 2 (Wiki) entity record giving the monitoring graph its human actors.

**Domain type:** `Entities` (knowledge domain, per §2)
**Note type:** `entity`, subtype `person`
**Status:** active schema, **currently empty** — notes are created by cascade as articles naming each person are ingested (§6).

This file is curated and doubles as the domain's operating instructions (§5).

## Operating Instructions

1. **Cascade population (§6).** Person notes are not ingested directly. When an article is compiled (Step 2), each person in its `Related Entities` is cascaded: created from the Template if missing, otherwise its `mentionCount` is incremented and the inbound article link added.
2. **No live web enrichment.** When cascading a new (or existing) person note, populate `Summary`/body content only from what the citing article(s) actually say — never from a live internet search or model background knowledge. Named SAF/MINDEF personnel are commonly `#saf`-flagged; be especially strict there. If genuine external enrichment is wanted (e.g. an official bio), land the source in `Inbox/Links/` first (URL + fetch timestamp) and cite it explicitly (§1 traceability; §7 "organized lie" failure mode).
3. **Flat namespace.** No `YYYY-MM/` sub-folders — a person is a stable entity, not a dated event. All notes live directly in this folder.
4. **Naming.** `personId` = slugified full name (e.g. `ng-eng-hen`). Filename = `<personId>.md` (no doubling — see [[drop-doubled-slug-filenames]]).
5. **YAML registry — proposed; freeze via a Decision note (§3) before first population:**

| Field | Type | Notes |
|---|---|---|
| personId | string, unique | slugified name — the stable identity/id field |
| displayName | string | human-readable full name (title field) |
| role | string | current title / role, e.g. `Minister for Defence` |
| affiliation | string | primary organisation — should resolve to an `[[organisations/<name>]]` note |
| country | string | associated country — should resolve to a `[[country/<name>]]` note |
| aliases | list | alternate spellings, honorifics, former titles |
| mentionCount | number | count of inbound article references — maintained by cascade |

   **Relationships live in the body, not YAML:** links to referencing articles, to the person's affiliation, and to country are `[[wikilinks]]` in the note body ("multi-value relationship lists never belong in YAML", §3).

6. **Sensitive-data flag (§10).** Named SAF/MINDEF personnel are a `#saf` trigger. Any person note whose body carries deny-listed detail must include `#saf` in a `tags` line; exports route through the sanitized derived copy only — never share directly. Apply the same transcription-correction dictionary as the source domain when normalising names.
7. **Lint (§8).** Checked for orphan people (zero inbound links), duplicate entities behind un-merged aliases, broken `affiliation`/`country` wikilinks, `mentionCount` drift, and frontmatter conformance against the registry above.
8. **Scale note (§1/§7).** Bounded domain. Route bulk queries through the `traverse_index` MCP tool (§8) against `wiki.db` rather than direct file reads.

## Producing a List

When asked to produce a list of **all** people in this domain — a full roster, not a targeted query — never output a flat alphabetical dump. Render it **grouped and nested**, built from `catalog.md` / `wiki.db` (read the columns; don't open every note):

1. **Primary — group by `country`, A–Z.** People with no country go in a trailing **"(Country unknown)"** group.
2. **Secondary — within each country, group by organisation (`affiliation`), A–Z.** People with no affiliation go in a trailing **"(Unaffiliated)"** group.
3. **Sort within an organisation** by `mentionCount` (highest first), then `displayName` A–Z.

Render each note as `- [[<personId>|<displayName>]]`.

```
### Singapore
#### MINDEF
- [[chan-chun-sing|Chan Chun Sing]]
```

## Template

Copy the block below verbatim as the starting point for every new person note in this domain.

~~~md
---
personId:
displayName:
role:
affiliation:
country:
aliases: []
mentionCount: 0
tags: []  # quote any #-prefixed value, e.g. ['#saf'] — unquoted breaks the whole frontmatter block
---

## Summary
<!-- 1-2 sentences: who this person is and their monitoring relevance -->

## Coverage
<!-- populated by cascade: [[<sourceId>-<slug>|<short label>]] links naming this person (bare filename — Obsidian resolves by filename, not a folder-qualified "Article/" path) -->

## Related Entities
<!-- [[Organisations/...]] affiliation, [[Country/...]] -->

## AI Context
<!-- note #saf here if this person is deny-listed under §10 -->
~~~

## See also

- `../article/index.md` — Sources · Articles domain (source of `Related Entities` mentions)
- `../organisations/index.md` — paired Organisations domain (person ↔ organisation affiliations)
- `../country/index.md` — resolves each person's `country` field
- root `index.md` — master map
- `catalog.md` — auto-generated, exhaustive list of every person note (never hand-edited)
- `log.md` — append-only cascade ledger
