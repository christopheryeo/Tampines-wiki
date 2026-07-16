---
type: domain-index
domain: Outlets
subtype: outlet
status: active
last_updated: 2026-07-06
---

# Domain: Entities — Outlets

**Purpose:** the canonical record for every media outlet that has published a piece of coverage relevant to SAF/MINDEF monitoring. Each note is a lean Layer 2 (Wiki) entity record — the "who published it" counterpart to the `article` source domain. Outlet notes are created and refreshed by cascade when an article that cites them is ingested (§6, Step 2).

**Domain type:** `Entities` (knowledge domain, per §2)
**Note type:** `entity`, subtype `outlet`
**Schema of record:** `../../schemas/outlet.yaml` (frozen — changes only via a Decision note, §3)

This file is curated and doubles as the domain's operating instructions (§5) — it replaces needing to consult a separate schema file to work in this folder.

## Operating Instructions

1. **Cascade population (§6).** Outlet notes are not ingested directly. When an article is compiled (Step 2), each outlet in its `Covered By` list is cascaded: if the outlet note is missing it is created from the Template; if it exists, any new `channels` are merged. Do not hand-author coverage counts.
   - **`articleCount` is a pre-computed grand total, not a cascade-incremented running tally.** It was populated at initial ingestion from every raw article's `outlets:` field across the *whole* corpus (~9,307 articles) — it already counts every raw article attributed to this outlet, including ones not yet individually compiled into the wiki template. **Do not increment it when cascading an article that already exists in the raw corpus** (i.e. essentially every article this procedure will ever touch) — that double-counts. Only increment it for a genuinely *new* raw article arriving after the aggregate was last computed (rare; verify first with `grep -rl "outlets:.*<outletId>" entities/article/` against the *raw*, not-yet-migrated corpus). Discovered and corrected 2026-07-06 after 10 outlets were wrongly incremented — see [[fix-articlecount-double-counting]].
2. **No live web enrichment.** When cascading a new (or existing) outlet note, populate `Profile`/body content only from what the citing article(s) actually say — never from a live internet search or model background knowledge. If genuine external enrichment is wanted (e.g. outlet reach, ownership), land the source in `Inbox/Links/` first (URL + fetch timestamp) and cite it explicitly (§1 traceability; §7 "organized lie" failure mode).
3. **Flat namespace.** Unlike `article`, outlet notes are **not** grouped into `YYYY-MM/` sub-folders — an outlet is a stable entity, not a dated event. All notes live directly in this folder.
4. **Naming.** `outletId` = slugified outlet name. Filename = `<outletId>.md`. (Until 2026-07-06 this was the doubled `<outletId>-<outletId>.md` — see [[drop-doubled-slug-filenames]] for why that was dropped and how the 395 existing notes were migrated.)
5. **YAML registry — frozen, mirrors `schemas/outlet.yaml`, changes only via a Decision note (§3):**

| Field | Type | Notes |
|---|---|---|
| outletId | string, unique | slugified name — the stable identity/id field |
| displayName | string | human-readable outlet name (title field) |
| country | string | HQ country — should resolve to a `[[country/<name>]]` note |
| mediaCategory | string | classification, e.g. `Mainstream Media`, `Trade/Defence`, `Wire/Agency`, `Broadcast` |
| channels | list | distribution channels (Web, Print, TV, Radio, Social); often empty |
| articleCount | number | pre-computed grand total across the raw corpus at ingestion — **not** incremented per cascade run (see item 1); never hand-edited |
| aliases | list | names a wikilink may use to resolve here (e.g. `[displayName]`) — added per [[add-outlet-country-aliases]], since the doubled-slug filename never matches the bare display name |

   **Relationships live in the body, not YAML:** links to the articles an outlet covered and to its home `country` are `[[wikilinks]]` in the note body ("multi-value relationship lists never belong in YAML", §3).

6. **Sensitive-data flag (§10).** Outlet notes hold no SAF/MINDEF content themselves, so they are not normally `#saf`-flagged. If an outlet body ever quotes deny-listed material, apply `#saf` and route exports through the sanitized derived copy.
7. **Lint (§8).** Checked for orphan outlets (an outlet with `articleCount: 0` and no inbound article links), broken `country` wikilinks, `articleCount` drift against the actual inbound link count, and frontmatter conformance against the registry above.
8. **Scale note (§1/§7).** This domain is moderate (~395 notes) but still route dashboard tiles and bulk queries through the `traverse_index` MCP tool (§8) against `wiki.db`, not direct file reads.

## Producing a List

When asked to produce a list of **all** outlets in this domain — a full roster, not a targeted query — never output a flat alphabetical dump. Render it **grouped and nested**, built from `catalog.md` / `wiki.db` (read the columns; don't open every note):

1. **Primary — group by home country (`country`), A–Z.** Outlets with no country go in a trailing **"(Country unknown)"** group.
2. **Secondary — within each country, group by `mediaCategory`, A–Z** (e.g. `Mainstream Media`, `Trade/Defence`, `Wire/Agency`, `Broadcast`).
3. **Sort within a category** by `articleCount` (highest first), then `displayName` A–Z.

Render each note as `- [[<outletId>|<displayName>]]`.

```
### Singapore
#### Mainstream Media
- [[channel-u|Channel U]]
```

## Template

Copy the block below verbatim as the starting point for every new outlet note in this domain.

~~~md
---
outletId:
displayName:
country:
mediaCategory:
channels: []
articleCount: 0
aliases: []
---

## Coverage
<!-- populated by cascade: [[<sourceId>-<slug>|<short label>]] links, most recent first (bare filename — Obsidian resolves by filename, not a folder-qualified "Article/" path) -->

## Profile
<!-- optional: 1-2 lines on the outlet, its reach, and monitoring relevance -->
~~~

## See also

- `../article/index.md` — the paired Sources · Articles domain (the "what was published")
- `../../schemas/outlet.yaml` — the frozen field schema this registry mirrors
- `../country/index.md` — resolves each outlet's `country` field
- root `index.md` — master map
- `catalog.md` — auto-generated, exhaustive list of every outlet note (never hand-edited)
- `log.md` — append-only cascade ledger
