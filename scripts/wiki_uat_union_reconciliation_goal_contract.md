---
type: goal-contract
name: wiki-uat-union-reconciliation
status: completed
owner: Christopher (chris@sentient.io)
created: 2026-07-29
applies_to: [entities/article, Inputs/articles, MSM_dataset_UAT]
---

# Wiki and UAT Union Reconciliation Goal Contract

This contract defines a reviewable Goal Mode run for reconciling the compiled
Markdown wiki with `MSM_dataset_UAT`. It does not authorize execution by itself.
Execution begins only after Christopher approves the contract and invokes it as
a goal.

Production database `MSM_dataset` is outside this contract and must never be
written, migrated, truncated, or otherwise changed.

## 1. Objective

Converge the wiki and UAT on the preserved union of **22,820 independent
articles**, without deleting articles or deduplicating stories:

1. Import 5,192 usable UAT-only legacy articles into the wiki.
2. Load 816 wiki-only July articles into UAT.
3. Preserve all duplicates because duplicate coverage supports the issue radar.
4. Establish a reusable compiled-wiki-to-UAT projection workflow so future
   cascade batches cannot silently leave UAT behind.
5. Preserve provenance, stable identity mapping, article relationships, and
   rollback evidence throughout the migration.

For this contract, **synchronized** means more than equal article counts. Every
wiki article must resolve to exactly one UAT article, and every projected parent
field plus the complete coverage, media, tag, and user-group child-row
multisets must match the values represented by the compiled wiki note and its
database-projection metadata.

## 2. Starting Boundary

Before any write:

1. Read `README.md`, `AGENTS.md`, this contract, the article-domain index, and
   the accepted `derive-database-from-compiled-wiki` decision.
2. Query live UAT read-only and directly count compiled wiki articles.
3. Require exactly 17,628 wiki articles and 22,004 UAT articles.
4. Freeze manifests and content hashes for both populations.
5. Reconfirm the expected differences:
   - 5,192 UAT-only legacy records.
   - 816 wiki-only July records.
   - 205 source-ID collisions between UAT legacy rows and existing wiki notes.
6. Create a consistent UAT backup and record table counts and checksums.
7. Confirm the configured target is exactly `MSM_dataset_UAT` and uses
   `UAT_*` tables. Refuse `MSM_dataset`, production, or an ambiguous target.

Any discrepancy is a breakout and blocks writes.

## 3. Identity and Projection Contract

Before migrating records:

1. Record a schema decision authorizing a structured
   `## Database Projection` section in compiled article notes.
2. Store the database-facing metadata needed for deterministic projection,
   including category, topic, vendor identity, document metadata, coverage,
   media, issue tags, and user groups.
3. Add a persistent UAT identity map from wiki `sourceId` to UAT `article_id`.
4. Treat wiki `sourceId` as the logical identity and UAT article IDs as derived
   internal identifiers.
5. Use `uat-legacy-<article_id>` as the wiki identity for every migrated legacy
   record. This resolves all 205 known collisions without overwriting or
   conflating either article.
6. Preserve database-only values exactly when available. Do not invent missing
   URLs or vendor IDs.

## 4. Import UAT-Only Records Into the Wiki

Develop `scripts/uat_to_inputs.py` with deterministic `prepare`,
`verify-bundle`, and `apply` commands.

The importer must:

1. Read UAT only through SELECT queries.
2. Export complete parent and child records into a hashed, reviewable bundle.
3. Require exactly 5,192 records:
   - March 2026: 690.
   - April 2026: 1,629.
   - May 2026: 1,957.
   - June 2026: 916.
4. Preserve title, description, date, category, topic, tone, sentiment, event
   type, outlets, countries, tags, media, user groups, and original UAT ID.
5. Leave the source URL blank for the 4,502 records that lack one; the hashed
   UAT snapshot and identity map provide migration provenance.
6. Write reviewed intake notes only after bundle verification.
7. Run timed cascade dry runs and real cascade runs month by month.
8. Run article quality, catalog, backlink, and hard-link validation after each
   month.

No source record may be overwritten, silently skipped, or merged.

## 5. Project the Completed Wiki Into UAT

Develop `scripts/project_wiki_to_uat.py` with deterministic `prepare`,
`verify-bundle`, `diff`, and `load` commands.

The projector must:

1. Backfill database-projection metadata from exact UAT evidence for articles
   already represented in UAT.
2. Use the July 23 and July 29 assessments for the 766 wiki-only articles those
   artifacts cover.
3. Perform direct AI-assistant review for the remaining 50 wiki-only articles.
   Do not call an external model API.
4. Generate a first UAT delta containing exactly 816 inserts, zero updates, and
   zero deletes.
5. Allocate stable positive UAT article IDs above the current maximum.
6. Preserve wiki source IDs as external provenance.
7. Load articles, coverage, media, tags, and user groups in one
   rollback-on-failure UAT transaction.
8. Persist the identity crosswalk and validate both UAT analytical views.
9. Require explicit attributed approval before executing the UAT transaction.
10. Compare every projected article field and child-row multiset after commit;
    matching monthly and total counts alone is not sufficient.

## 6. Recurrence Prevention

After successful reconciliation:

1. Update `ingest_cascade.py` to preserve database-projection metadata before
   moving an input article.
2. Make every successful cascade automatically prepare and verify a UAT delta.
3. Keep the actual UAT database load behind explicit approval.
4. Retire `stage_mysql_feeds.py` and `stage_enriched_radar_inputs.py` from
   active use after the new projector passes acceptance.
5. Update `README.md`, procedures, and `AGENTS.md` with the new source-of-truth,
   approval, timing, and reporting rules.
6. Report wiki count, UAT count, delta size, elapsed time, and average seconds
   per article after every cascade and UAT projection run.

## 7. Performance Measurement

Time the complete process from the initial baseline query through final
idempotence validation. Record separate wall-clock timings for:

1. Baseline inventory and backup.
2. UAT export and bundle verification.
3. Intake materialisation.
4. Each monthly cascade dry run and real run.
5. Article-quality and link gates.
6. Projection metadata backfill.
7. AI review of the 50 unmatched articles.
8. UAT bundle generation and verification.
9. UAT transactional load.
10. Final reconciliation, views, radar check, and idempotence rerun.

The final report must include total elapsed time, processed counts, failures,
exclusions, and average seconds per article for each article-processing stage.
Do not calculate a misleading average for an aborted or zero-article stage.

## 8. Success End Conditions

The goal succeeds only when all of these conditions are true:

1. The wiki and UAT each contain exactly 22,820 articles.
2. Final monthly counts match in both systems:

| Month | Required count |
|---|---:|
| 2025-11 | 1,306 |
| 2025-12 | 1,556 |
| 2026-01 | 1,572 |
| 2026-02 | 2,808 |
| 2026-03 | 2,045 |
| 2026-04 | 3,290 |
| 2026-05 | 5,323 |
| 2026-06 | 3,136 |
| 2026-07 | 1,784 |
| **Total** | **22,820** |

3. All 5,192 UAT-only articles have compiled wiki notes and cascaded entity
   relationships.
4. All 816 formerly wiki-only articles exist in canonical UAT.
5. Every wiki article has exactly one UAT identity mapping.
6. UAT contains no article outside that identity map and the wiki contains no
   article absent from it.
7. Every projected parent field matches between the compiled wiki projection
   and UAT.
8. Coverage, media, tag, and user-group child-row multisets match for every
   mapped article.
9. All expected 205 identity collisions remain represented as two independent
   records.
10. No article or duplicate was deleted, merged, or silently excluded.
11. `Inputs/articles/` contains no successfully processed article.
12. Article-quality checks have zero errors and zero warnings.
13. Hard-link checks have zero broken links, YAML errors, and nested target
    failures.
14. UAT has zero duplicate primary keys, foreign-key orphans, missing child
    relationships, or failed view reconciliations.
15. A second projection run produces a zero-change diff across inserts,
    updates, deletes, parent fields, and child-row multisets.
16. The issue radar runs read-only against UAT and can read the reconciled tags
    and article relationships.
17. Production `MSM_dataset` is unchanged.
18. The final receipt contains backup paths, manifests, hashes, approvals,
    counts, timings, averages, and tested rollback instructions.

## 9. Breakout Conditions

Stop before proceeding to the next stage and wait for Christopher's decision
when any of these conditions occurs:

1. The starting wiki or UAT count differs from the frozen baseline.
2. The live UAT population changes after the manifest is frozen.
3. The configured database is not exactly `MSM_dataset_UAT`.
4. A command would write to `MSM_dataset` or another production database.
5. The UAT-only population is not exactly 5,192.
6. Identity collisions differ from the expected 205.
7. A UAT-only record lacks enough evidence to create a meaningful article note.
8. Projection metadata cannot be reconstructed from UAT, reviewed artifacts,
   or direct AI-assistant review.
9. A proposed write would overwrite, merge, delete, or silently exclude an
   article.
10. The initial UAT delta proposes anything other than 816 inserts, zero
    updates, and zero deletes.
11. A cascade dry run reports destructive changes, unexpected destination
    conflicts, or schema failures.
12. A real cascade leaves partial movements or incomplete bookkeeping.
13. Any quality, link, identity, count, foreign-key, view, transaction, radar,
    or idempotence gate fails.
14. The UAT transaction cannot prove rollback safety before commit.
15. Production non-mutation cannot be demonstrated.

For every breakout, preserve completed artifacts and timings, identify exact
affected records, and do not bypass or loosen a gate.

## 10. Goal Invocation

After Christopher approves this contract, invoke Goal Mode with:

> Execute the complete wiki-and-UAT union reconciliation defined in
> `scripts/wiki_uat_union_reconciliation_goal_contract.md`. Preserve every
> article and duplicate, converge both systems on exactly 22,820 records, keep
> production untouched, enforce every validation and breakout condition,
> require approval before the UAT transaction, time every stage, and finish
> only when all success end conditions are satisfied or a documented breakout
> requires Christopher's decision.
