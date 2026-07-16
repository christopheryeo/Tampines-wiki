---
type: domain-index
domain: Organisations
subtype: organisation
status: active
last_updated: 2026-07-06
---

# Domain: Entities — Organisations

**Purpose:** the canonical record for every organisation named in SAF/MINDEF-relevant coverage — government bodies, armed forces, defence agencies, defence-industry firms, and other institutions surfaced in article `Related Entities`. Each note is a lean Layer 2 (Wiki) entity record anchoring the monitoring graph's "who".

**Domain type:** `Entities` (knowledge domain, per §2)
**Note type:** `entity`, subtype `organisation`
**Status:** active schema, **currently empty** — notes are created by cascade as articles mentioning each organisation are ingested (§6).

This file is curated and doubles as the domain's operating instructions (§5).

## Operating Instructions

1. **Cascade population (§6).** Organisation notes are not ingested directly. When an article is compiled (Step 2), each organisation in its `Related Entities` is cascaded: created from the Template if missing, otherwise its `mentionCount` is incremented and the inbound article link added.
2. **No live web enrichment.** When cascading a new (or existing) organisation note, populate `Summary`/body content only from what the citing article(s) actually say — never from a live internet search or model background knowledge. This is especially strict here: most notes in this domain will be `#saf`-flagged. If genuine external enrichment is wanted (e.g. an organisation's official mandate), land the source in `Inbox/Links/` first (URL + fetch timestamp) and cite it explicitly (§1 traceability; §7 "organized lie" failure mode).
3. **Flat namespace.** No `YYYY-MM/` sub-folders — an organisation is a stable entity, not a dated event. All notes live directly in this folder.
4. **Naming.** `orgId` = slugified organisation name (e.g. `mindef`, `dsta`, `singapore-armed-forces`). Filename = `<orgId>.md` (no doubling — see [[drop-doubled-slug-filenames]]).
5. **YAML registry — proposed; freeze via a Decision note (§3) before first population:**

| Field | Type | Notes |
|---|---|---|
| orgId | string, unique | slugified name — the stable identity/id field |
| displayName | string | human-readable organisation name (title field) |
| orgType | enum | `Government` \| `Military` \| `Defence Agency` \| `Defence Industry` \| `Media` \| `Other` |
| country | string | home country — should resolve to a `[[country/<name>]]` note |
| aliases | list | acronyms and alternate names (e.g. `MINDEF`, `Ministry of Defence`) |
| mentionCount | number | count of inbound article references — maintained by cascade |

   **Relationships live in the body, not YAML:** links to referencing articles, to related people, and to the home country are `[[wikilinks]]` in the note body ("multi-value relationship lists never belong in YAML", §3).

6. **Sensitive-data flag (§10).** Organisations on the deny-list (SAF, MINDEF, DSTA, and related bodies) are the primary trigger for the `#saf` flag. Any organisation note whose body carries deny-listed detail must include `#saf` in a `tags` line, and exports must route through the sanitized derived copy — never share these notes directly.
7. **Lint (§8).** Checked for orphan organisations (zero inbound links), duplicate entities hiding behind un-merged aliases, broken `country` wikilinks, `mentionCount` drift, and frontmatter conformance against the registry above.
8. **Scale note (§1/§7).** Bounded domain. Route bulk queries through the `traverse_index` MCP tool (§8) against `wiki.db` rather than direct file reads.

## Producing a List

When asked to produce a list of **all** organisations in this domain — a full roster, not a targeted query — never output a flat alphabetical dump. Render it **grouped and nested**, built from `catalog.md` / `wiki.db` (read the columns; don't open every note):

1. **Primary — group by home country (`country`), A–Z.** Organisations with no country go in a trailing **"(Country unknown)"** group.
2. **Secondary — within each country, group by `orgType`, in registry enum order**: `Government`, `Military`, `Defence Agency`, `Defence Industry`, `Media`, `Other`.
3. **Sort within a type** by `mentionCount` (highest first), then `displayName` A–Z.

Render each note as `- [[<orgId>|<displayName>]]`.

```
### Singapore
#### Government
- [[mindef|MINDEF]]
```

## Template

Copy the block below verbatim as the starting point for every new organisation note in this domain.

~~~md
---
orgId:
displayName:
orgType:
country:
aliases: []
mentionCount: 0
tags: []  # quote any #-prefixed value, e.g. ['#saf'] — unquoted breaks the whole frontmatter block
---

## Summary
<!-- 1-2 sentences: what this organisation is and its monitoring relevance -->

## Coverage
<!-- populated by cascade: [[<sourceId>-<slug>|<short label>]] links mentioning this organisation (bare filename — Obsidian resolves by filename, not a folder-qualified "Article/" path) -->

## Related Entities
<!-- [[People/...]], [[Country/...]], peer [[Organisations/...]] -->

## AI Context
<!-- note #saf here if this organisation is deny-listed under §10 -->
~~~

## See also

- `../article/index.md` — Sources · Articles domain (source of `Related Entities` mentions)
- `../people/index.md` — paired People domain (organisation ↔ person affiliations)
- `../country/index.md` — resolves each organisation's `country` field
- root `index.md` — master map
- `catalog.md` — auto-generated, exhaustive list of every organisation note (never hand-edited)
- `log.md` — append-only cascade ledger
