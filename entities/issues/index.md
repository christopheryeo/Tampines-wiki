---
type: domain-index
domain: Issues
subtype: issue
status: active
last_updated: 2026-07-08
---

# Domain: Issues

**Purpose:** the vault's early-warning watchlist — one note per *percolating issue*: a coverage
cluster whose structure (recurrence, breadth expansion, institutional attachment, acceleration,
unfacilitated share) indicates rising blow-up risk with real ramifications. Where `topic` notes
classify coverage, an `issue` note records a live *assessment*: score, status, rationale, predicted
catalysts, and recommended posture. Created per [[add-issues-domain]].

**Domain type:** `Entities` (knowledge domain, per §2)
**Note type:** `entity`, subtype `issue`

This file is curated and doubles as the domain's operating instructions (§5).

## Operating Instructions

1. **Population by radar procedure only.** Issue notes are created and updated exclusively by
   following `scripts/issue_radar_procedure.md` (deterministic flags from `scripts/issue_radar.py`,
   then agent clustering + ramification assessment). Never populated by the article cascade, and
   never created ad hoc mid-query.
2. **One note per issue object, not per radar tag.** Tag-level flags fragment (the 2026-03-31
   backtest collapsed 115 HOT tags into 6 issues). Before creating a note, check `catalog.md` for
   an existing issue this flag belongs to — updating an existing note is the default; minting a new
   one is the exception.
3. **Flat namespace & naming.** No `YYYY-MM/` sub-folders. `issueId` = slugified issue name
   (e.g. `ns-enforcement-enlistment-act`). Filename = `<issueId>.md` (single slug, per
   [[drop-doubled-slug-filenames]]).
4. **No live web enrichment.** Assessments, rationale, and catalysts are written only from the
   citing articles and entity notes already in the vault (§1 traceability). Catalyst dates must be
   quoted from a cited article, never from model background knowledge.
5. **Dismissals are kept.** A flag judged benign (facilitated, event-shaped, no ramification) is
   still filed with `status: dismissed` and a one-line reason — dismissals are the calibration data
   for radar thresholds. Never delete a dismissed note.
6. **YAML registry — frozen per [[add-issues-domain]]; changes only via a new Decision note (§3):**

| Field | Type | Notes |
|---|---|---|
| issueId | string, unique | slugified issue name — the stable identity/id field |
| displayName | string | human-readable issue name (title field) |
| status | enum | `watch` \| `warm` \| `hot` \| `dismissed` \| `closed` |
| ramification | enum | `low` \| `moderate` \| `high` \| `severe` — judgment layer output |
| score | number | latest radar score (0–1) |
| firstFlagged | date | date the radar first flagged any constituent tag |
| lastScored | date | date of the most recent radar/procedure pass |
| clusterTags | list | radar tag-flags folded into this issue |
| aliases | list | alternate names a wikilink may use to resolve to this note |
| articleCount | number | count of inbound article references in `## Coverage` |

   **Relationships live in the body, not YAML:** links to articles, entities, and catalysts are
   `[[wikilinks]]` in the note body ("multi-value relationship lists never belong in YAML", §3).
7. **Sensitive-data flag (§10).** An issue built on deny-listed entities inherits the `#saf` flag —
   set `tags: ['#saf']` is not in the registry; instead treat the whole note as export-restricted
   at export time when any constituent entity is deny-listed, per the search-domain precedent.
8. **Lint (§8).** Checked for: `status` inconsistent with latest `score`/tier floors, `lastScored`
   older than the most recent ingest run, `clusterTags` naming tags that no longer flag, catalyst
   dates in the past without a follow-up entry, and frontmatter conformance against the registry.
9. **Scale note (§1/§7).** Small, bounded domain (active issues, not coverage). Route bulk queries
   through `wiki.db` / `catalog.md` rather than direct file reads.

## Producing a List

When asked to produce a list of **all** issues in this domain — a full roster, not a targeted
query — never output a flat alphabetical dump. Render it **grouped and nested**, built from
`catalog.md` (read the columns; don't open every note):

1. **Primary — group by `status`**, in this order: `🔥 hot`, `🔴 warm`, `🟠 watch`, `✅ closed`, `✅ dismissed`.
2. **Secondary — within each status, group by `ramification`**, in this order: `severe`, `high`,
   `moderate`, `low`.
3. **Sort within a group** by `score` (highest first), then `displayName` A–Z.

Render each note as `- <displayName> — score <score> , first flagged <firstflagged>. <15-word summary of the note's ## Assessment section>`.

## Template

Copy the block below verbatim as the starting point for every new issue note in this domain.

~~~md
---
issueId:
displayName:
status: watch
ramification: low
score: 0.0
firstFlagged:
lastScored:
clusterTags: []
aliases: []
articleCount: 0
---

## Assessment
<!-- 2-4 sentences: what this issue is, why it was flagged, and why it matters (or doesn't).
     Written from citing articles only. -->

## Signals
<!-- latest radar output lines for the constituent tags, dated. Append per pass; never rewrite. -->

## Catalysts
<!-- known future events that could re-ignite coverage, each with a date and a citing
     [[article|label]] link. e.g. court dates, parliament sittings, scheduled visits/exercises. -->

## Coverage
<!-- representative [[<sourceId>-<slug>|<short label>]] article links backing this assessment -->

## Posture
<!-- recommended stance: monitor / prepare lines / brief principal / act. One line, dated. -->

## Notes
<!-- optional: related issues [[...]], related topics [[...]] -->
~~~

## See also

- `../topic/index.md` — Topics domain (classification; issues are assessments layered above topics)
- `../decisions/add-issues-domain.md` — the Decision note authorizing this domain
- `scripts/issue_radar.py` — deterministic signal layer
- `scripts/issue_radar_procedure.md` — the judgment-layer SOP that populates this domain
