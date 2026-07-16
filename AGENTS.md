# Media Monitoring Project Agent Instructions

## Project Summary

This project is a file-based media monitoring knowledge vault for SAF/MINDEF coverage. It ingests raw media items from RSS-style feeds and crawled articles, compiles each item into a structured Markdown article note, and cascades links out to the relevant people, organisations, places, outlets, countries, appointments, topics, and issues.

The vault is designed to work as both:

1. A plain-text Markdown corpus that remains readable and editable without special tooling.
2. An Obsidian-friendly connected wiki using Obsidian wikilink syntax.

The Markdown notes are the source of truth. Generated files such as `catalog.md`, `index/wiki.db`, and dashboard outputs are derived artifacts and can be rebuilt.

## Mandatory Startup Step

Before doing any work in this project, read and ingest `README.md` in the project root.

Use the README as the authoritative operating guide for:

1. The directory structure.
2. The article ingest flow.
3. Entity cascade rules.
4. Query procedures.
5. Issue radar behavior.
6. Script purposes and expected usage.
7. The source-of-truth principle.

Do not rely on memory alone when working in this vault. Re-read the relevant README section and, when needed, the corresponding procedure document under `scripts/`.

## Core Workflow

Raw articles land in `Inputs/articles/YYYY-MM/`. They are outside the queryable wiki until they are compiled and moved into `entities/article/YYYY-MM/`.

Ingesting an article requires two steps:

1. Compile the raw item into the article-note schema with proper frontmatter, summary sections, and Obsidian wikilinks.
2. Cascade every linked entity into the correct domain folder, creating or updating backlinks, coverage lists, counts, catalogs, and logs as required.

An article only counts as ingested once it has been moved into `entities/article/` and the relevant entity links have been cascaded.

## Raw DSTA Source Data

`raw/` contains DSTA-provided source exports received on 2026-07-16. Preserve it as source evidence, do not edit it directly, and consult `README.md` for the full handling rules before deriving ingest-ready files into `Inputs/articles/YYYY-MM/`.

## Important Folders

1. `Inputs/` — raw, not-yet-cascaded media items.
2. `raw/` — original DSTA-provided feed exports and archive; preserve as source evidence.
3. `entities/` — the wiki itself, divided into knowledge domains.
4. `entities/article/` — compiled article notes.
5. `entities/issues/` — issue radar assessments and watchlist entries.
6. `scripts/` — deterministic maintenance scripts and judgment-based operating procedures.
7. `schemas/` — frozen field definitions.
8. `index/wiki.db` — generated SQLite mirror for fast queries.
9. `dashboards/` — saved dashboard layouts and SQL-backed views.
10. `topics/` — topic monitoring definitions.
11. `runs/` — ingest receipts.

## System File Rules

Each domain under `entities/` uses three system files:

1. `index.md` — hand-maintained operating manual and schema registry for the domain.
2. `catalog.md` — generated complete listing. Do not hand-edit.
3. `log.md` — append-only audit ledger. Never rewrite old entries.

## Script Guidance

Use the scripts for mechanical, error-prone bookkeeping:

1. `scripts/generate_catalog.py` rebuilds domain catalogs.
2. `scripts/check_links.py` reports broken or fragile wikilinks.
3. `scripts/fix_links.py` repairs safe classes of wikilink and YAML issues.
4. `scripts/patch_coverage.py` updates coverage lists and mention counts idempotently.
5. `scripts/issue_radar.py` computes read-only early-warning signals over the wiki database.

Use the procedure documents for judgment-based work:

1. `scripts/entity_cascade_procedure.md` for ingest and entity cascade.
2. `scripts/query_procedure.md` for answering questions from the vault.
3. `scripts/issue_radar_procedure.md` for turning radar flags into filed issue assessments.

## Issue Radar

The issue radar is an early-warning layer on top of the linked corpus. It looks for structural signs that coverage is percolating toward a blow-up, including acceleration, breadth expansion, institutional attachment, recurrence, unfacilitated share, and opinionated share.

`issue_radar.py` only computes deterministic signals. Judgment about clustering, ramification, catalysts, posture, and filing belongs in `scripts/issue_radar_procedure.md` and `entities/issues/`.

## Operating Principles

1. Preserve provenance end to end.
2. Do not enrich summaries or entities from live web lookups or model background knowledge unless the README or procedure explicitly allows it.
3. Use piped wikilinks in the canonical form "real filename pipe display name".
4. Treat schemas as frozen. Record schema or rule changes in `entities/decisions/` before applying them.
5. Keep generated files generated. Do not manually edit catalogs or derived indexes.
6. Prefer scripts for repeatable mechanical updates and procedures for judgment-heavy work.

## Learned Preferences

### Input Article Counting Must Be Fresh And Explicit

When Christopher asks how many loose input files are in `Inputs/articles/`, always run a fresh direct listing of files at `Inputs/articles/` with `maxdepth 1`, exclude system metadata such as `.DS_Store`, and report the count of real article files. If there is any ambiguity, include both counts: real loose article files and total direct files including metadata.

**Why:** On 2026-07-17, an earlier answer reported 4 loose article files when there were actually 8. The error came from relying on stale or incomplete output instead of re-listing the folder immediately before answering.

**How to apply:** Before answering any count of loose intake files, verify with a current direct file listing and, when useful, show or summarize the filenames so Christopher can reconcile the result quickly.

### Cascade Runs Must Be Timed

Whenever the article compile/cascade process is run, time the whole process from start to finish and report the total elapsed time, number of articles processed, and average processing time per article.

**Why:** Christopher wants visibility into throughput and operational efficiency for the media-monitoring ingest pipeline.

**How to apply:** Start timing before the first compile/cascade action and stop only after the final validation or cascade bookkeeping step completes. If a run processes zero articles or aborts partway through, report that explicitly instead of calculating a misleading average.
