---
type: domain-index
domain: Decisions
subtype: decision
status: active
last_updated: 2026-07-06
---

# Domain: Decisions

**Purpose:** the append-only record of governance decisions that change a frozen schema, naming
convention, or operating rule elsewhere in this wiki — per §3, "field names, types, and allowed
values [for a note type's registry] are frozen... and may only change via a Decision note." Every
registry change anywhere in `entities/` must be traceable to exactly one note here.

**Domain type:** `Decisions` (knowledge domain, per §2)
**Note type:** `decision`

This file is curated and doubles as the domain's operating instructions (§5).

## Operating Instructions

1. **When to create one.** Any time a frozen YAML registry (documented in a domain's `index.md`), a
   naming convention, or a vault-wide operating rule needs to change. Never edit a frozen registry
   directly without a Decision note existing first — the Decision is what authorizes the edit.
2. **No live web enrichment.** Context/Consequences are written from what actually happened in this
   vault (the triggering incident, the notes/domains touched) — not from external research. This
   domain is governance history, not a knowledge-base topic.
3. **Flat namespace & naming.** No `YYYY-MM/` sub-folders. `decisionId` = slugified short title.
   Filename = `<decisionId>.md` — single-slug, same as every other domain since
   [[drop-doubled-slug-filenames]]. (This domain's filename was never doubled to begin with; the
   entity domains have since matched it, not the other way around.)
4. **YAML registry — frozen, changes only via a Decision note about this domain itself (§3):**

| Field | Type | Notes |
|---|---|---|
| decisionId | string, unique | slugified short title — the stable identity/id field |
| title | string | human-readable title (title field) |
| status | enum | `proposed` \| `accepted` \| `superseded` \| `rejected` |
| date | date | date decided |
| affects | list | domain(s) or file(s) whose registry/convention this changes |

   **Relationships live in the body, not YAML:** links to the domains/notes affected are
   `[[wikilinks]]` in the note body.
5. **Sensitive-data flag (§10).** Not normally `#saf`-flagged unless the decision itself concerns
   deny-listed material.
6. **Lint (§8).** Checked for `status: proposed` decisions left unresolved, and for registry changes
   found elsewhere in the vault that lack a corresponding Decision note here.
7. **Scale note (§1/§7).** Small, bounded domain — expected to stay well under the token ceiling.

## Producing a List

When asked to produce a list of **all** decisions in this domain — a full roster, not a targeted query — never output a flat chronological dump. Render it **grouped and nested**, built from `catalog.md` (read the columns; don't open every note):

1. **Primary — group by affected domain (`affects`), A–Z.** A decision that affects several domains appears under each. Decisions affecting nothing specific go in a trailing **"(Vault-wide)"** group.
2. **Secondary — within each domain, group by `status`, in this order**: `proposed`, `accepted`, `superseded`, `rejected`.
3. **Sort within a status** by `date` (newest first), then `title` A–Z.

Render each note as `- [[<decisionId>|<title>]]`.

```
### outlet
#### accepted
- [[add-outlet-country-aliases|Add outlet & country aliases]]
```

## Template

Copy the block below verbatim as the starting point for every new decision note in this domain.

~~~md
---
decisionId:
title:
status: accepted
date:
affects: []
---

## Context
<!-- what problem prompted this decision -->

## Decision
<!-- what was decided, stated plainly -->

## Consequences
<!-- what changes as a result; what becomes frozen/updated -->
~~~

## See also

- root `index.md` — master map
- `catalog.md` — auto-generated, exhaustive list of every decision note (never hand-edited)
- `log.md` — append-only ledger
