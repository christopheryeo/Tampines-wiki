# 30 Root Article Ingest — 2026-09-04

## Outcome

- Starting loose root queue: **30** Markdown articles.
- Compiled and cascaded: **15** articles — 13 for 2026-08 and 2 for 2026-09.
- Held as verified same-source records already compiled: **15** — 4 exact destination conflicts and 11 normalized-output conflicts.
- Exact source-empty holds: **0**.
- Same-batch same-source duplicate holds: **0**.
- Accepted cross-outlet duplicate coverage: **9 records across 4 story clusters**. Each retained record has a distinct publisher domain, native ID, and canonical URL.
- Loose root files remaining: **0**.
- Monthly input files remaining: **0**.
- Batch reconciliation: **30 = 15 cascaded + 15 held**.

The 15 held files are preserved under `Inputs/holds/20260904T140828+0800-30-root-ingest/`. No pre-existing hold was requeued.

## Timing

- End-to-end timer: 2026-09-04 14:08:28 to 15:11:25 SGT.
- Total elapsed: **62 minutes 57 seconds** (includes the explicit external-transfer approval pause).
- End-to-end average: **251.8 seconds per cascaded article**.
- Cascade execution: **57.39 seconds total**, averaging **3.83 seconds per article**.
  - 2026-08: 13 articles, 33.09 seconds, 2.55 seconds per article.
  - 2026-09: 2 articles, 24.30 seconds, 12.15 seconds per article.

## Enrichment and cascade

- Ran saved-evidence review plus the approved two-pass model workflow.
- Recovered one source-fetch/API timeout with a bounded single-article retry.
- Reconciled model disagreements and canonical outlet identities using independent read-only article reviews and saved wiki evidence.
- All 15 accepted inputs passed the shared completeness contract before cascade.
- Corrected the generic `AsiaOne` headline on article `9443208418` from its saved URL and body before compilation.
- Preserved distinct-outlet syndication for the Ng Eng Hen award, Malaysian defence-management, haze-preparedness, and NS60 recognition clusters.
- Entity cascade totals: 15 outlet updates, 15 country updates, 31 organisation updates, 18 people updates, 20 place updates, 62 topic creations, and 51 topic updates.

## Validation

- Article quality: **15 scanned, 0 errors, 0 warnings**.
- Link hard gate: **passed** across 58,070 notes — no broken links and no YAML errors.
- Remaining reported findings are historical advisories outside this batch: 10 malformed labels in the legacy topic archive, 2 unbalanced-bracket source-text notes, and 2,514 unlinked-entity advisories across 2,417 older articles.
- Repaired six occurrences of three inert `[[nid:...]]` CMS placeholders in older AsiaOne source/projection text because they blocked the focused August link gate.
- Fixed numeric enrichment fields appended as quoted strings and corrected link checking so runtime dependencies and run artifacts are excluded from validation-source parsing while documentation remains a valid link target.
- Regression suite: **11 tests passed** across `tests.test_enrich_radar_inputs` and `tests.test_check_links`.

## Receipts and evidence

- Frozen manifest and enrichment evidence: `runs/2026-09-04/artifacts/20260904T140828+0800-30-root-ingest/`.
- August cascade receipt: `runs/2026-09-04/20260904T145922-ingest_cascade-5c1b.json`.
- September cascade receipt: `runs/2026-09-04/20260904T145957-ingest_cascade-3fe4.json`.

Run receipts and bulk wiki data remain local generated/source-of-truth artifacts and are not added to git.
