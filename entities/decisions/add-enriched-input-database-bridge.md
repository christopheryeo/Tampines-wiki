---
decisionId: add-enriched-input-database-bridge
title: Add a reviewed enriched-input bridge into the shared article database
status: accepted
date: 2026-07-23
affects: [scripts, Inputs, issue-radar, database]
---

## Context

The radar enrichment runner writes approved tags, outlet metadata, institutional category, tone,
and event type into loose Markdown articles. The existing MySQL stager reads preserved raw JSON
feeds instead, requires signed-integer source IDs, and has no path for enriched Markdown inputs.
The loose batch also contains external IDs that are either non-numeric or outside the database's
signed-integer range.

## Decision

Add a deterministic bridge that reads enriched Markdown articles plus their assessment artifacts
and prepares an isolated UAT staging bundle. It must:

1. preserve the external article ID as provenance;
2. use unique negative staging IDs and allocate new positive canonical IDs above the current UAT
   maximum during transformation;
3. emit article, online-coverage, and tag rows without writing directly to the database;
4. admit an article automatically only when all four enrichment groups are auto-applicable and
   neither model requested review;
5. place every incomplete, disagreeing, or low-confidence article in a review queue;
6. load canonical UAT only through a transaction that rolls back when validation fails; and
7. keep production promotion outside the automatic UAT bridge.

The wiki article schema continues to reserve YAML `tags` for system classification. Exact enriched
issue tags are therefore preserved in compiled notes as an `## Issue Tags` body section and as
topic links, while the shared article database stores them in `article_tags`.

## Consequences

- The bridge is deterministic and makes no model or web calls.
- UAT remains the safe default and production is never written by the bridge.
- Articles on the review queue remain staged but are excluded from canonical UAT until approved
  and re-staged.
- Database IDs no longer depend on external ID format.
- The assessment JSON remains the evidence and confidence record; the shared article database
  receives only approved operational values.
