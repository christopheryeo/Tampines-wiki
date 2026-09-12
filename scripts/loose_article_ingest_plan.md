---
type: plan
name: loose-article-ingest
status: active
owner: Christopher (chris@sentient.io)
created: 2026-08-31
last_updated: 2026-08-31
applies_to: [Inputs/articles, entities/article, entity cascades, UAT projection, UAT load]
---

# Loose-Article Ingest Plan

This is the single authoritative plan for a crawler batch that lands as loose Markdown files
directly under `Inputs/articles/`. It combines the former reusable batch procedure with the former
Goal contract. It governs interactive, Goal-mode, and scheduled execution.

The two predecessor files remain temporarily in `scripts/` for one canonical-plan validation run.
They are not execution authorities. After that run succeeds, update validation evidence and remove
both predecessor files. Historical Decision notes remain unchanged.

## Goal invocation

> Execute `scripts/loose_article_ingest_plan.md` completely against the current loose-article
> batch. Continue through route, enrichment, local cascade, quality gates, one final UAT bundle,
> attributed automated approval, UAT load, and post-load parity. Never write production. Finish
> only when every accepted input is reconciled or a documented stop condition is reached.

## Objective

Process one frozen loose-input batch through:

`inventory -> source-empty and duplicate disposition -> route -> enrich -> remediate -> completeness
gate -> local compile/cascade by month -> article quality -> link quality -> one final UAT bundle ->
attributed approval -> UAT load -> post-load parity -> final reconciliation`

Quality and provenance are constraints; throughput is measured but never allowed to weaken a gate.

## Authority and boundaries

1. Markdown under `entities/article/` is the database source of truth after compilation.
2. Raw crawler files remain unchanged until an authorized routing, hold, enrichment, or cascade step.
3. Local cascade never calls projection or database tools.
4. `scripts/project_wiki_to_uat.py` is the sole active compiled-wiki-to-UAT projector and loader.
5. Production `MSM_dataset` is read-only and is never a projection or load target.
6. External source retrieval or model-API data transfer requires explicit approval for that run.
   Saved-evidence-only in-app reviews do not require external transfer.
7. UAT loading does not require a second human pause after every exact-bundle gate passes. The
   executing Goal agent creates the attributed approval under Christopher Yeo's standing
   authorization dated 2026-08-14, bound only to that verified bundle.
8. Frozen schemas, accepted policy Decisions, piped wikilinks, append-only logs, generated-catalog
   rules, and the source-of-truth principle remain in force throughout.

## Batch boundary

1. Start the end-to-end timer before inventory.
2. Fresh-list direct Markdown files under `Inputs/articles/`, excluding `.DS_Store` and folders.
3. Freeze a master manifest containing path, filename, article ID, title, publication date, and
   SHA-256 for every starting file.
4. Later arrivals belong to the next batch unless Christopher explicitly adds them.
5. A missing file or changed hash after freezing is a hard stop.
6. Preserve the master manifest plus separate eligible, source-empty hold, duplicate hold,
   publisher-review hold, and accepted manifests.

## Phase 1 - Source evidence and duplicate disposition

### Exact source-empty holds

An exact source-empty stub has a non-empty article ID and all of the following empty: title,
publication date, URL, body, and `rawNewsApiResponse`. Determine the count freshly.

Move each exact stub without content changes into `Inputs/articles/holds/<run-id>/`, record its hash
and reason, and exclude it from enrichment, cascade, and UAT. Never fill it from model background
knowledge. Partially evidenced files are not source-empty; they enter bounded remediation.

Require:

`master count = eligible count + exact source-empty hold count`

### Publisher-aware duplicate audit

Repeated text, a source duplicate flag, shared wire copy, or the same topic is a review signal, not
an exclusion. Verify the publishing outlet from saved evidence in this order:

1. `publisherDomain` or normalized article URL hostname;
2. canonical outlet identity or alias;
3. saved publisher name supported by source metadata.

The quoted or originating agency is not automatically the publishing outlet. A different verified
publishing outlet remains an independent eligible record. Hold only a verified same-outlet repeat
of the same source record, normally supported by the same upstream ID or exact canonical URL plus
matching title, date, and evidence. An unresolved publisher or different-outlet identity collision
is a hard stop; never overwrite a compiled article or fabricate an ID.

Record separately: source-empty holds, same-outlet repeat holds, different-outlet duplicates
accepted, compiled-path conflicts, and unresolved publisher reviews.

## Phase 2 - Route

Run the dry route against the frozen eligible manifest:

```bash
python3 scripts/route_input_articles.py --manifest <eligible-manifest>
```

Audit every invalid date, existing monthly destination, and compiled destination. When every
accepted file is routable, apply the same frozen manifest:

```bash
python3 scripts/route_input_articles.py --manifest <eligible-manifest> --write
```

Record planned, routed, skipped, blocked, accepted-duplicate, held, and unresolved counts, touched
months, elapsed time, and files per second. Expected source-empty and verified same-outlet holds do
not fail routing; an accepted unroutable file does.

## Phase 3 - Enrich

Enrichment precedes compile/cascade. Pass the frozen eligible manifest to every command so earlier
monthly inputs cannot enter the batch accidentally.

### Review modes

Use either:

1. the configured two-pass model/API workflow after explicit approval for external data transfer;
   or
2. two independent in-app reviews using saved input evidence only, reconciled by
   `scripts/reconcile_local_enrichment_reviews.py`.

Both reviews apply the accepted sentiment, tone, metadata, and event-type Decisions. A third
independent AI adjudicates exactly each remaining field-specific disagreement or low-confidence
subset. Its result must include the final value, confidence, literal saved evidence, applicable
policy rule, and rationale. Each adjudication clears only its own domain.

Required normalized fields are: `articleId`, `articleTitle`, `publishedDate`, `category`, `topic`,
`tone`, `toneSentiment`, `eventType`, `tags`, `outlets`, `countries`, `coverageCount`, `mediaCount`,
`sourceType`, and `url`, plus a non-empty source body. Crawler inputs use `sourceType: crawl`.

Preview, assess, and apply only `readyForCascade` results:

```bash
python3 scripts/enrich_radar_inputs.py --manifest <eligible-manifest> --no-fetch
python3 scripts/enrich_radar_inputs.py --manifest <eligible-manifest>
python3 scripts/enrich_radar_inputs.py --manifest <eligible-manifest> --apply
python3 scripts/enrich_radar_inputs.py --manifest <eligible-manifest> --check-complete
```

### Bounded remediation

An initial completeness failure starts remediation; it is not an immediate hold.

1. Diagnose every failed field and distinguish missing, invalid, disagreement, publisher, and
   insufficient-evidence cases.
2. Re-read only saved body, raw response, publisher metadata, and canonical wiki evidence unless
   external retrieval was already approved.
3. Invoke the appropriate third reviewer where policy permits.
4. Apply only evidence-backed corrections and rerun the shared completeness gate over the failed
   subset.
5. Permit at most two remediation cycles after the initial failed gate.
6. Keep exact source-empty files on their exact hold. Put a partially evidenced file still unable
   to support required fields after two cycles on an `enrichment-source-insufficient` hold.
7. Continue with the accepted subset unless none is ready.

Record every cycle's input, field findings, decisions, changed files, remaining failures, evidence,
confidence, timing, and artifacts. Never lower the gate or invent evidence.

## Phase 4 - Shared completeness gate

The accepted manifest must pass:

```bash
python3 scripts/enrich_radar_inputs.py --manifest <accepted-manifest> --check-complete
```

`scripts/ingest_cascade.py` enforces the same contract batch-wide before mutation. No incomplete
accepted file may proceed, and cascade never substitutes classification defaults.

## Phase 5 - Local compile and cascade

Identify touched publication months from the accepted manifest and process one month at a time.

Before the first monthly dry-run, compute each accepted input's actual `ingest_cascade.py` output
filename. If that compiled path already exists, hold the input only when its non-empty source ID and
canonical URL exactly match the compiled note; record both paths and the input hash. Stop on any
identity disagreement. This catches title-slug truncation and normalization collisions that routing
alone cannot see. Use `scripts/partition_cascade_output_conflicts.py` for this gate.

For each month:

```bash
python3 scripts/ingest_cascade.py --month YYYY-MM --manifest <accepted-manifest> --dry-run
python3 scripts/ingest_cascade.py --month YYYY-MM --manifest <accepted-manifest>
```

Each real run must remain local-only and report elapsed time, processed articles, seconds per
article, focused validation errors, inputs remaining, entity updates, and receipt path. Stop on a
nonzero exit, hard validation error, catalog or log failure, manifest file left behind after claimed
success, or any projection/database invocation.

## Phase 6 - Article and link quality

Run the compiled-article gate:

```bash
python3 scripts/article_quality.py --check
```

Preview and apply only provenance-backed safe repairs. Stop on ambiguous identity, duplicate source
ID, wrong month, reviewed-sentiment change without an explicit override, or body rewriting.

Then run link repair preview and confirmation:

```bash
python3 scripts/fix_links.py --dry-run
python3 scripts/fix_links.py
python3 scripts/check_links.py
```

Permit one mechanical repair pass. Stop on unresolved broken links, YAML errors, ambiguous aliases,
or judgment-required entity linking. Record notes scanned, findings, repairs, timing, throughput,
and receipts.

## Phase 7 - One final UAT bundle and load

Only after all accepted articles have cascaded and the batch-wide article/link gates pass:

1. Run `project_wiki_to_uat.py prepare-current` once for the complete frozen batch.
2. Run `verify-bundle`.
3. Apply required projection backfills to local Markdown.
4. Run `verify-bundle` again.
5. Run the live UAT `diff`.
6. Stop on any proposed delete, unexpected update, identity mismatch, wrong target, or failed
   verification.
7. Create the loader approval only now with `approved: true`, the exact `bundleId`, current
   `approvedAt`, `approvedBy: Codex Goal agent under Christopher Yeo's standing authorization dated
   2026-08-14`, and the originating instruction as `approvalSource`.
8. Load only `MSM_dataset_UAT` through `project_wiki_to_uat.py load` using that exact bundle and
   approval file.
9. Run the post-load diff and bundle verification. Require exact compiled-Markdown-to-UAT parent
   and child-multiset parity. Verify rollback and no partial changes after any failed transaction.

Preserve the bundle ID, hashes, delta counts, approval evidence, load receipt, and parity evidence.

## Phase 8 - Final reconciliation and performance report

Stop the end-to-end timer only after reconciliation. Require:

`starting count = cascaded + source-empty holds + verified same-outlet holds + enrichment holds +
publisher-review holds + other documented breakouts`

Report:

1. starting, eligible, routed, enriched, cascaded, and remaining counts;
2. every hold and accepted-duplicate disposition;
3. touched months and per-month cascade counts;
4. enrichment/remediation status;
5. article-quality and link-quality status;
6. final UAT bundle, inserts, updates, deletes, approval, load receipt, and post-load parity;
7. total elapsed time, seconds per article, per-stage throughput, slowest stage, and all receipts.

Use this stage table:

| stage | command | start | end | elapsed sec | input count | success/output count | failure count | throughput | receipt/artifact |
|---|---|---|---|---:|---:|---:|---:|---:|---|

## Hard stop conditions

Stop and report the exact affected files, stage, elapsed time, evidence, and safest next decision on:

- manifest drift;
- unapproved external data transfer or unavailable required model/runtime access;
- unresolved classifications after the bounded remediation loop;
- unresolved publisher identity or provenance-safe duplicate identity;
- invalid routing or destination collision for an accepted file;
- cascade, schema, catalog, audit-log, article-quality, or link hard failure;
- a required non-mechanical repair or schema change;
- UAT delete, unexpected update, identity mismatch, wrong target, failed verification, approval
  construction failure, transaction failure, rollback doubt, or post-load parity failure;
- any production target or production write.

Difficulty, volume, an initial enrichment failure, an expected source-empty hold, or a verified
same-outlet hold is not by itself a stop condition.

## Success conditions

The run succeeds only when every frozen starting file is reconciled; every accepted article passed
the shared completeness gate before cascade; every accepted article compiled and cascaded locally;
article and link gates have no hard failures; exactly one final verified UAT bundle was approved and
loaded; post-load parity is exact; receipts and performance metrics are complete; and production
was untouched.
