---
type: domain-index
domain: Places
subtype: place
status: active
last_updated: 2026-07-06
---

# Domain: Entities — Places

**Purpose:** the canonical record for every sub-national location named in SAF/MINDEF-relevant
coverage — islands, camps, neighbourhoods, and named venues surfaced in article `Related Entities`
that are more specific than a `country` (e.g. `Pulau Tekong`, `Pasir Ris`, `White Sands Shopping Mall`).
Each note is a lean Layer 2 (Wiki) entity record giving the monitoring graph its geography below the
country level.

**Domain type:** `Entities` (knowledge domain, per §2)
**Note type:** `entity`, subtype `place`
**Status:** active schema, **currently empty** — notes are created by cascade as articles naming each
place are ingested (§6).

This file is curated and doubles as the domain's operating instructions (§5).

## Operating Instructions

1. **Cascade population (§6).** Place notes are not ingested directly. When an article is compiled
   (Step 2), each place in its `Related Entities` is cascaded: created from the Template if missing,
   otherwise its `mentionCount` is incremented and the inbound article link added.
2. **No live web enrichment.** When cascading a new (or existing) place note, populate `Summary`/body
   content only from what the citing article(s) actually say — never from a live internet search or
   model background knowledge. If genuine external enrichment is wanted (e.g. exact geographic
   coordinates), land the source in `Inbox/Links/` first (URL + fetch timestamp) and cite it explicitly
   (§1 traceability; §7 "organized lie" failure mode). This is especially strict for `#saf`-flagged
   places (military training grounds, camps).
3. **Flat namespace.** No `YYYY-MM/` sub-folders — a place is a stable entity, not a dated event. All
   notes live directly in this folder.
4. **Naming.** `placeId` = slugified place name (e.g. `pulau-tekong`, `white-sands-shopping-mall`).
   Filename = `<placeId>.md` (no doubling — see [[drop-doubled-slug-filenames]]).
5. **YAML registry — proposed; freeze via a Decision note (§3) before further population.** Includes
   `aliases` from day one — its absence in the original `outlet`/`country` registries caused Obsidian
   to auto-create stray empty stub notes when unresolved links were clicked (see
   [[add-outlet-country-aliases]]); this domain is scaffolded after that lesson, not before it:

| Field | Type | Notes |
|---|---|---|
| placeId | string, unique | slugified name — the stable identity/id field |
| displayName | string | human-readable place name (title field) |
| placeType | enum | `Island` \| `Camp/Training Ground` \| `Neighbourhood` \| `Landmark/Venue` \| `Other` |
| country | string | containing country — should resolve to a `[[country/<name>]]` note |
| aliases | list | names a wikilink may use to resolve here (e.g. `[displayName]`) — the doubled-slug filename never matches the bare display name |
| mentionCount | number | count of inbound article references — maintained by cascade |

   **Relationships live in the body, not YAML:** links to referencing articles and to the containing
   place/country are `[[wikilinks]]` in the note body ("multi-value relationship lists never belong in
   YAML", §3).
6. **Sensitive-data flag (§10).** Military training grounds and camps (e.g. `Pulau Tekong`) are a
   `#saf` trigger. Any place note whose body carries deny-listed detail must include `#saf` in a
   `tags` line, and exports must route through the sanitized derived copy — never share directly.
7. **Lint (§8).** Checked for orphan places (zero inbound links), broken `country`/containing-place
   wikilinks, `mentionCount` drift, and frontmatter conformance against the registry above.
8. **Scale note (§1/§7).** Bounded domain. Route bulk queries through the `traverse_index` MCP tool
   (§8) against `wiki.db` rather than direct file reads.

## Producing a List

When asked to produce a list of **all** places in this domain — a full roster, not a targeted query — never output a flat alphabetical dump. Render it **grouped and nested**, built from `catalog.md` / `wiki.db` (read the columns; don't open every note):

1. **Primary — group by containing country (`country`), A–Z.** Places with no country go in a trailing **"(Country unknown)"** group.
2. **Secondary — within each country, group by `placeType`, in registry enum order**: `Island`, `Camp/Training Ground`, `Neighbourhood`, `Landmark/Venue`, `Other`.
3. **Sort within a type** by `mentionCount` (highest first), then `displayName` A–Z.

Render each note as `- [[<placeId>|<displayName>]]`.

```
### Singapore
#### Camp/Training Ground
- [[pulau-tekong|Pulau Tekong]]
```

## Template

Copy the block below verbatim as the starting point for every new place note in this domain.

~~~md
---
placeId:
displayName:
placeType:
country:
aliases: []
mentionCount: 0
tags: []  # quote any #-prefixed value, e.g. ['#saf'] — unquoted breaks the whole frontmatter block
---

## Summary
<!-- 1-2 sentences: what this place is and its monitoring relevance -->

## Coverage
<!-- populated by cascade: [[<sourceId>-<slug>|<short label>]] links mentioning this place (bare filename) -->

## Located In
<!-- containing place/country, e.g. [[Country/Singapore]] or a parent [[Place/...]] -->

## AI Context
<!-- note #saf here if this place is deny-listed under §10 -->
~~~

## See also

- `../article/index.md` — Sources · Articles domain (source of `Related Entities` mentions)
- `../country/index.md` — paired Countries domain (each place's containing `country`)
- root `index.md` — master map
- `catalog.md` — auto-generated, exhaustive list of every place note (never hand-edited)
- `log.md` — append-only cascade ledger
