---
type: domain-index
domain: Countries
subtype: country
status: active
last_updated: 2026-07-06
---

# Domain: Entities — Countries

**Purpose:** the canonical place record for every country referenced in SAF/MINDEF-relevant coverage — either as an article's `countries` value or as an outlet's home `country`. Each note is a lean Layer 2 (Wiki) entity record giving geographic context to the monitoring graph.

**Domain type:** `Entities` (knowledge domain, per §2)
**Note type:** `entity`, subtype `country`
**Status:** active schema, **currently empty** — notes are created by cascade as articles and outlets referencing each country are ingested (§6).

This file is curated and doubles as the domain's operating instructions (§5).

## Operating Instructions

1. **Cascade population (§6).** Country notes are not ingested directly. When an article (via its `countries` list) or an outlet (via its `country` field) is compiled, each named country is cascaded: created from the Template if missing, otherwise its `mentionCount` is incremented and the inbound link added.
2. **No live web enrichment.** When cascading a new (or existing) country note, populate `Notes`/body content only from what the citing article(s)/outlets actually say — never from a live internet search or model background knowledge. If genuine external enrichment is wanted (e.g. region/ISO code reference data), land the source in `Inbox/Links/` first (URL + fetch timestamp) and cite it explicitly (§1 traceability; §7 "organized lie" failure mode).
3. **Flat namespace.** No `YYYY-MM/` sub-folders — a country is a stable entity, not a dated event. All notes live directly in this folder.
4. **Naming.** `countryId` = slugified country name (e.g. `singapore`, `united-states`). Filename = `<countryId>.md` (no doubling — see [[drop-doubled-slug-filenames]]).
5. **YAML registry — proposed; freeze via a Decision note (§3) before first population:**

| Field | Type | Notes |
|---|---|---|
| countryId | string, unique | slugified name — the stable identity/id field |
| displayName | string | human-readable country name (title field) |
| region | string | e.g. `Southeast Asia`, `East Asia`, `Europe`, `Middle East` |
| iso2 | string | ISO 3166-1 alpha-2 code, optional |
| mentionCount | number | count of inbound article + outlet references — maintained by cascade |
| aliases | list | names a wikilink may use to resolve here (e.g. `[displayName]`) — added per [[add-outlet-country-aliases]], since the doubled-slug filename never matches the bare display name |

   **Relationships live in the body, not YAML:** links to referencing articles and to outlets headquartered here are `[[wikilinks]]` in the note body ("multi-value relationship lists never belong in YAML", §3).

6. **Sensitive-data flag (§10).** Country notes are geographic context and are not normally `#saf`-flagged. Apply `#saf` only if a body ever paraphrases deny-listed material.
7. **Lint (§8).** Checked for orphan countries (zero inbound links), broken wikilinks, `mentionCount` drift, and frontmatter conformance against the registry above.
8. **Scale note (§1/§7).** Small, bounded domain (~one note per country). Still route bulk queries through the `traverse_index` MCP tool (§8) against `wiki.db` rather than direct file reads.

## Producing a List

When asked to produce a list of **all** countries in this domain — a full roster, not a targeted query — never output a flat alphabetical dump. Render it **grouped**, built from `catalog.md` / `wiki.db` (read the columns; don't open every note):

1. **Primary — group by `region`, A–Z** (e.g. `Southeast Asia`, `East Asia`, `Europe`, `Middle East`). Countries with no region go in a trailing **"(Region unknown)"** group.
2. **No secondary grouping** — a country has only one natural axis. **Sort within a region** by `mentionCount` (highest first), then `displayName` A–Z.

Render each note as `- [[<countryId>|<displayName>]]`.

```
### Southeast Asia
- [[singapore|Singapore]]
- [[malaysia|Malaysia]]
```

## Template

Copy the block below verbatim as the starting point for every new country note in this domain.

~~~md
---
countryId:
displayName:
region:
iso2:
mentionCount: 0
aliases: []
---

## Coverage
<!-- populated by cascade: [[<sourceId>-<slug>|<short label>]] links referencing this country (bare filename — Obsidian resolves by filename, not a folder-qualified "Article/" path) -->

## Outlets Based Here
<!-- populated by cascade: [[<outletId>|<Display Name>]] links whose country resolves here (piped, real filename — not folder-qualified "Outlet/" text) -->

## Notes
<!-- optional: monitoring relevance of this country to SAF/MINDEF -->
~~~

## See also

- `../article/index.md` — Sources · Articles domain (source of `countries` references)
- `../outlet/index.md` — Outlets domain (source of `country` references)
- root `index.md` — master map
- `catalog.md` — auto-generated, exhaustive list of every country note (never hand-edited)
- `log.md` — append-only cascade ledger
