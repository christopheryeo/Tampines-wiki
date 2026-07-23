---
decisionId: unify-dual-source-article-intake
title: Unify DSTA and crawler articles at the Inputs doorway
status: accepted
date: 2026-07-23
affects: [raw, Inputs, scripts, entities/article, issue-radar]
---

## Context

Articles arrive by two routes. DSTA deliveries first land under `raw/` as preserved source evidence.
Crawler-produced articles land directly under `Inputs/articles/`. Both routes must ultimately pass
through the same input schema and the same enrichment, database-staging, compile, and cascade gates.

## Decision

`Inputs/articles/` is the single processing doorway:

1. DSTA route: `raw/` → `raw_feed_to_inputs.py` → `Inputs/articles/YYYY-MM/`.
2. Crawler route: crawler → `Inputs/articles/`; loose root files are routed by publication month
   into `Inputs/articles/YYYY-MM/`.
3. Shared route: enrichment and reviewed UAT staging scan both loose files and month subfolders by
   default.
4. Wiki route: monthly input folders compile and cascade into `entities/article/YYYY-MM/`.

No enrichment, database staging, or entity cascade may read preserved `raw/` files directly.
Source-route provenance remains in `sourceType`, identifiers, URLs, and staging raw JSON.

## Consequences

- A new deterministic month router handles loose crawler arrivals without changing their contents.
- `--loose-only` remains available for an explicitly bounded loose-file batch.
- DSTA and crawler articles receive the same radar fields and safety gates once they reach Inputs.
- Preserved DSTA exports remain immutable evidence.
