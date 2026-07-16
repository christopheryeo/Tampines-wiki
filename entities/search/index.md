---
type: domain-index
domain: Search
subtype: query
status: active
last_updated: 2026-07-06
---

# Domain: Search — Query Cache

**Purpose:** a historical cache of every question asked of this wiki and the answer given, so that
`scripts/query_procedure.md` can check here *first* before re-running full entity resolution and
article-reading for a question that's the same as (or close to) one already answered. Each note is a
Layer 2 (Wiki) record of one question–answer exchange — the "have we been asked this before" layer
sitting in front of the rest of the vault.

**Domain type:** a governance/meta domain, alongside `Decisions` (per §2) — it's about the wiki's own
operation, not about SAF/MINDEF subject matter itself. Query/answer content routed through here can
still be `#saf`-sensitive (see item 6 below) even though the domain itself isn't a coverage domain.

**Note type:** `entity`, subtype `query`

This file is curated and doubles as the domain's operating instructions (§5).

## Operating Instructions

1. **Populated by the Query Procedure, not the Cascade Procedure.** Every time
   `scripts/query_procedure.md` runs to completion, it must file the question and the answer given as
   a note here — this is mandatory for every query, not just ones that produced a "genuinely new"
   synthesis (that's a separate, narrower bar — see `query_procedure.md` Step 6).
2. **Check here first.** Before Step 1 (Resolve) of `query_procedure.md`, scan this domain's
   `catalog.md` for a query whose `query` field is the same as, or close to, the new question. A
   match with `status: answered` can be reused directly (cite it, increment its `reuseCount`) instead
   of re-running full resolution — but only if nothing in the matched entities' `## Coverage` has
   changed since the cached entry's `askedDate` (check `mentionCount`/`articleCount` on the relevant
   entity notes). If the underlying coverage has grown, treat the cache as stale: mark it
   `status: superseded`, link the new entry to it, and answer fresh.
3. **No live web enrichment.** The `## Answer` stored here must be exactly what was actually
   composed from the wiki at query time (per `query_procedure.md` Step 5) — never touched up,
   re-researched, or extended with anything not in the original answer. If the answer later turns out
   to be wrong or incomplete, don't edit it — supersede it (see item 2).
4. **Flat namespace.** No `YYYY-MM/` sub-folders — a query is a stable record, not filed by when the
   underlying event happened (unlike `article`). All notes live directly in this folder.
5. **Naming.** `queryId` = the first ~6–8 slugified words of the question, plus a short content hash
   of the full question text (e.g. `what-was-said-about-seletar-aerospace-park-a1b2c3d4`) —
   deterministic, not random: asking the *exact* same question twice produces the *same* hash and
   therefore the same file (a natural duplicate-detector), while a differently-worded but similar
   question gets a different file (catching those requires the semantic check in item 2, not filename
   matching). Filename = `<queryId>.md` — single-slug, no doubling, per
   [[drop-doubled-slug-filenames]].
6. **YAML registry — proposed; freeze via a Decision note (§3) before further population:**

| Field | Type | Notes |
|---|---|---|
| queryId | string, unique | content-hash-based slug — the stable identity/id field |
| query | string | the literal question as asked, verbatim — this is the title/identity field, kept in YAML (not body) specifically so it's visible in `catalog.md` without opening every note, since scanning the catalog *is* the "search it first" mechanism until a `traverse_index`-style tool exists (§8) |
| askedDate | datetime | when the question was asked |
| status | enum | `answered` \| `unresolved` \| `superseded` |
| reuseCount | number | times this cached answer was matched and reused for a later similar question — maintained by the query procedure, never hand-edited |
| tags | list | classification only — `#saf` if the query/answer touches deny-listed material (quote any `#`-prefixed value, e.g. `['#saf']` — unquoted breaks the whole frontmatter block) |

   **Relationships live in the body, not YAML:** the entities resolved, the sources cited, and any
   superseding/superseded query are `[[wikilinks]]` in the note body ("multi-value relationship lists
   never belong in YAML", §3).
7. **Sensitive-data flag (§10).** If the question or answer touches SAF/MINDEF/DSTA content, tag
   `#saf` and route any export through the sanitized derived copy — the same rule as every other
   domain, applied to cached Q&A pairs, not just source coverage.
8. **Lint (§8).** Checked for orphan queries (an `answered` entry never reused, which is fine — not
   every question repeats — but worth noting if the domain grows large and reuse stays at zero, which
   would suggest the cache isn't being checked), `superseded` entries with no link to their
   replacement, and frontmatter conformance against the registry above.
9. **Scale note (§1/§7).** Starts empty; expected to grow indefinitely as more questions are asked.
   Once large, route the "check here first" step through the `traverse_index` MCP tool (§8) against
   `catalog.md` rather than loading the whole catalog into context — the same scale discipline as
   every other domain.

## Producing a List

When asked to produce a list of **all** cached queries in this domain — a full roster, not a targeted query — never output a flat dump. Render it **grouped and nested**, built from `catalog.md` (read the columns; don't open every note):

1. **Primary — group by `status`, in this order**: `answered`, `unresolved`, `superseded`.
2. **Secondary — within each status, group by `askedDate` by month (`YYYY-MM`), newest month first.**
3. **Sort within a month** by `askedDate` (newest first), then `reuseCount` (highest first).

Render each note as `- [[<queryId>|<query>]]`.

```
### answered
#### 2026-07
- [[what-did-chan-chun-sing-talk-about-<hash>|What did Chan Chun Sing talk about?]]
```

## Template

Copy the block below verbatim as the starting point for every new query note in this domain.

~~~md
---
queryId:
query:
askedDate:
status: answered
reuseCount: 0
tags: []
---

## Question
<!-- the literal question as asked, verbatim (may repeat the YAML `query` field — this is the
     readable version for a human opening the note) -->

## Answer
<!-- the synthesized answer actually given, exactly as composed in query_procedure.md Step 5 -->

## Entities Resolved
<!-- [[wikilinks]] to every entity note consulted (query_procedure.md Steps 1-2) -->

## Sources Cited
<!-- [[wikilinks]] to every article actually cited in the answer -->

## AI Context
<!-- note #saf here if this query/answer touches deny-listed material; note here if this entry
     supersedes or is superseded by another query note, with a [[wikilink]] to it -->
~~~

## See also

- `../../scripts/query_procedure.md` — the procedure that reads and writes this domain
- root `index.md` — master map
- `catalog.md` — auto-generated, exhaustive list of every query note (never hand-edited)
- `log.md` — append-only ledger
