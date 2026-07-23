---
decisionId: derive-database-from-compiled-wiki
title: Derive the article database from the compiled wiki, not from raw a second time
status: accepted
date: 2026-07-23
affects: [scripts, scripts/sql, raw, entities/article, database, issue-radar]
---

## Context

The vault currently parses the same source material twice. `scripts/ingest_cascade.py` compiles
raw intake into `entities/article/YYYY-MM/`, while `scripts/stage_mysql_feeds.py` independently
re-reads the preserved exports under `raw/feed data/` and maps them into UAT staging. A third path,
`scripts/stage_enriched_radar_inputs.py`, was added by [[add-enriched-input-database-bridge]] to
carry enriched Markdown into the same database because the raw-feed stager could not accept it.

The result is two parsers, two quarantine/review surfaces, and two representations of one corpus
that must be reconciled by hand whenever they disagree. [[unify-dual-source-article-intake]] closed
the equivalent split at the *intake* doorway; the same split remains open at the *database* end.
`index/wiki.db` already demonstrates the correct shape: a store derived from the Markdown rather
than re-derived from source.

The staged phase files compound this. `scripts/sql/` holds nineteen numbered files in which
`phase7_*` rehearses rollback and `phase8_manual_*` restates load, validation, and rollback as a
manual variant of paths `phase5_*` already defines, while the enriched bridge performs its final
load in a single rollback-on-failure transaction.

## Decision

The compiled wiki is the sole upstream of the article database.

1. A single projection step reads `entities/` and writes every derived store — the MySQL article
   tables, `index/wiki.db`, and dashboard data. Preserved `raw/` files are never read by any
   database path.
2. `scripts/stage_mysql_feeds.py` and `scripts/stage_enriched_radar_inputs.py` are retired and
   replaced by that one projection runner.
3. The guarantees established by [[add-enriched-input-database-bridge]] carry forward unchanged and
   are binding on the projection runner: external IDs preserved as provenance, canonical IDs
   allocated above the current UAT maximum, a strict review queue for anything incomplete, UAT as
   the safe default, transactional load that rolls back on validation failure, and production
   promotion kept outside the automatic path.
4. `scripts/sql/` collapses to load → validate → commit-or-rollback. The `phase7_*` rehearsal files
   and the `phase8_manual_*` variants are retired as duplicate paths of `phase5_*`.
5. Provenance reaching the database comes from the compiled note's own source fields, which already
   cite the original export.

## Consequences

- The independent cross-check between the two parsers is deliberately given up. Divergence between
  the wiki and the database is no longer possible, so there is no longer anything to cross-check;
  a compile defect now reaches the database instead of being caught by disagreement. Article-level
  validation at compile time (per [[enforce-article-quality-gates]]) becomes the gate that
  previously sat between the two parsers.
- An article must be compiled before it can reach the database. The former ability to load raw
  feeds into UAT without cascading them is removed.
- `raw/` remains immutable preserved evidence and loses its only remaining automated reader.
- Restating the database requires only a re-projection from `entities/`, with no re-parse of source.
- The radar's inputs are unaffected in shape; `issue_radar.py` continues to read the product tables
  read-only.
