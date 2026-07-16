---
type: domain-index
domain: Topics
subtype: topic
status: active
last_updated: 2026-07-06
---

# Domain: Entities — Topics

**Purpose:** the canonical record for every subject theme used to classify SAF/MINDEF-relevant coverage — the controlled vocabulary behind each article's `topic` value and `category` classification. Each note is a lean Layer 2 (Wiki) entity record that lets the monitoring graph roll coverage up by theme.

**Domain type:** `Entities` (knowledge domain, per §2)
**Note type:** `entity`, subtype `topic`
**Status:** active schema, **currently empty** — notes are created by cascade as articles carrying each topic are ingested (§6).

This file is curated and doubles as the domain's operating instructions (§5).

## Operating Instructions

1. **Cascade population (§6).** Topic notes are not ingested directly. When an article is compiled (Step 2), its `topic` (and, where a topic doubles as a category, its `category`) is cascaded: created from the Template if missing, otherwise its `articleCount` is incremented and the inbound article link added.
2. **Controlled vocabulary.** Topics are a curated vocabulary, not free tags — prefer merging a near-duplicate into an existing topic over minting a new one. New topics should be added deliberately; drift here fragments every roll-up.
3. **Flat namespace & naming.** No `YYYY-MM/` sub-folders. `topicId` = slugified topic name (e.g. `defence-procurement`, `ns-policy`). Filename = `<topicId>.md` (no doubling — see [[drop-doubled-slug-filenames]]).
4. **No live web enrichment.** When cascading a new (or existing) topic note, populate `Definition`/`Notes` only from what the citing article(s) actually say — never from a live internet search or model background knowledge. If genuine external enrichment is wanted, land the source in `Inbox/Links/` first (URL + fetch timestamp) and cite it explicitly (§1 traceability; §7 "organized lie" failure mode).
5. **YAML registry — proposed; freeze via a Decision note (§3) before first population:**

| Field | Type | Notes |
|---|---|---|
| topicId | string, unique | slugified name — the stable identity/id field |
| displayName | string | human-readable topic name (title field) |
| category | enum | broad grouping the topic rolls up into (mirrors the article `category` enum) |
| aliases | list | synonyms folded into this topic |
| articleCount | number | count of inbound article references — maintained by cascade |

   **Relationships live in the body, not YAML:** links to the articles carrying this topic are `[[wikilinks]]` in the note body ("multi-value relationship lists never belong in YAML", §3).

6. **Sensitive-data flag (§10).** Topic labels are classification metadata and are not normally `#saf`-flagged. A topic that exists only to group deny-listed material should still be treated as sensitive at export time — route through the sanitized derived copy.
7. **Lint (§8).** Checked for orphan topics (zero inbound links), redundant near-duplicate topics that should be merged, `articleCount` drift, and frontmatter conformance against the registry above.
8. **Scale note (§1/§7).** Small, bounded vocabulary. Route bulk queries through the `traverse_index` MCP tool (§8) against `wiki.db` rather than direct file reads.

## Producing a List

When asked to produce a list of **all** topics in this domain — a full roster, not a targeted query — never output a flat alphabetical dump. Render it **grouped**, built from `catalog.md` / `wiki.db` (read the columns; don't open every note):

1. **Primary — group by `category`** (the broad grouping the topic rolls up into, mirroring the article `category` enum), categories ordered A–Z. Topics with no category go in a trailing **"(Uncategorised)"** group.
2. **No secondary grouping** — a topic has only one natural axis. **Sort within a category** by `articleCount` (highest first), then `displayName` A–Z.

Render each note as `- [[<topicId>|<displayName>]]`.

```
### Military Exercise
- [[ex-wallaby-2025|Ex Wallaby 2025]]
```

## Template

Copy the block below verbatim as the starting point for every new topic note in this domain.

~~~md
---
topicId:
displayName:
category:
aliases: []
articleCount: 0
---

## Definition
<!-- 1-2 sentences: what this topic covers and its classification boundary -->

## Coverage
<!-- populated by cascade: [[<sourceId>-<slug>|<short label>]] links classified under this topic (bare filename — Obsidian resolves by filename, not a folder-qualified "Article/" path) -->

## Notes
<!-- optional: monitoring relevance, related topics [[Topic/...]] -->
~~~

## See also

- `../article/index.md` — Sources · Articles domain (source of `topic` and `category` values)
- `../../schemas/article.yaml` — defines the article `topic` and `category` fields this domain mirrors
- `../../topics/` — seed topic definitions (e.g. `sa26.json`)
- root `index.md` — master map
- `catalog.md` — auto-generated, exhaustive list of every topic note (never hand-edited)
- `log.md` — append-only cascade ledger
