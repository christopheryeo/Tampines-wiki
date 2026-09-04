# Input Holds Audit — 2026-09-04

## Decision

The live hold area contains **2,258 Markdown files**. No held file is safe to move directly into the live ingest queue.

- **1,808 files are correctly parked** because their source is already compiled, they are verified duplicate arrivals, they are retained consumed-source evidence, they are explicit duplicate stubs or placeholders, or they carry an earlier off-topic decision.
- **450 files, representing 438 unique article IDs, are conditional recovery candidates.** They are exact source-empty stubs and contain no title, publication date, URL, article body, or raw source response. They cannot be recovered from the held file itself. A new source acquisition is required before any can enter an ingest batch.
- The 30 loose root articles were excluded from this audit and were not changed.

This is an inventory and recommendation only. No files under `Inputs/articles/holds/` were moved, rewritten, deleted, or reprocessed.

## Method and gates

The audit performed a fresh recursive listing, parsed all 2,258 notes, indexed the compiled article corpus by native article ID, and read the originating run manifests.

The integrity gates produced these results:

- All 2,258 files were assigned to one of nine hold buckets.
- All 2,258 have run provenance. For 2,232 files, the current bytes match the SHA-256 recorded when the file was held.
- The remaining 26 are the `consumed` source copies. Their run manifest identifies them, and every one has an exact-URL compiled counterpart. Their final enriched bytes were not separately hash-attested after the run moved them to `consumed/`.
- Every duplicate, already-compiled, collision, post-route, cascade-conflict, consumed, duplicate-stub, and off-topic item has a compiled article with the same article ID. Every source-bearing item in those classes also has the same canonical URL as its compiled counterpart.
- Every `source-empty` and `duplicate-stub` file satisfies the exact empty-source contract.
- Every `off-topic-irrelevant` file remains explicitly marked `relevant: false`.
- The audit found no hash drift, missing compiled counterpart, broken disposition invariant, or unreadable provenance manifest.

## Counts and disposition by bucket

| Hold bucket | Files | Audit result | Disposition | Recommended fix path |
|---|---:|---|---|---|
| `source-empty` | 844 | 394 files are now resolved or intentionally closed; 450 files / 438 unique IDs still have no source evidence | Split | Keep all parked. For the 438 unresolved IDs, reacquire the source from the authorized upstream crawler or provider, then require non-empty title, date, URL, body, and raw response before considering a new intake file. Never requeue the empty stub itself. |
| `duplicate-arrivals` | 561 | All manifest hashes match; all have exact-ID and exact-URL compiled counterparts | Correctly parked | No ingest action. Retain as duplicate evidence until a separate retention policy authorizes deletion or cold archival. |
| `already-compiled` | 402 | All manifest hashes match; all have exact-ID and exact-URL compiled counterparts | Correctly parked | No ingest action. The compiled note remains canonical. |
| `cascade-already-compiled` | 282 | All manifest hashes match; all computed cascade outputs already exist with the same ID and URL | Correctly parked | No ingest action. Keep the conflict evidence; do not run cascade again. |
| `already-compiled-normalized-collision` | 63 | All were previously proven semantic duplicates; current hashes and compiled URLs still agree | Correctly parked | No ingest action. Preserve as evidence of filename normalization collisions. |
| `duplicate-stub` | 49 | All are exact empty stubs and all 49 article IDs have compiled counterparts | Correctly parked | No recovery needed. Do not reacquire or requeue these stubs. |
| `consumed` | 26 | All are source-bearing copies retained after successful cascade; all have exact-ID and exact-URL compiled counterparts | Correctly parked | No ingest action. For future runs, record a final post-enrichment SHA-256 when moving a source copy into `consumed/`. |
| `off-topic-irrelevant` | 18 | All remain marked irrelevant; exact-ID and exact-URL compiled counterparts now exist | Correctly parked, with a separate scope question | Do not requeue. If current scope requires strict exclusion, audit the 18 compiled counterparts in a separate bounded task; the hold copies themselves need no repair. |
| `already-compiled-post-route` | 13 | All manifest hashes match; all have exact-ID and exact-URL compiled counterparts | Correctly parked | No ingest action. Preserve as post-route conflict evidence. |
| **Total** | **2,258** | **1,808 correctly parked; 450 conditional recovery files** |  |  |

## Source-empty recovery detail

The 844 source-empty files contain 830 unique article IDs. Their current status is:

- 391 files now have a compiled counterpart by exact article ID.
- One URL-valued article ID resolves to an exact compiled source URL.
- One article ID with a trailing `+` resolves to its compiled normalized ID.
- One file is an explicit duplicate-check placeholder and is intentionally closed.
- 450 files remain unresolved, representing 438 unique IDs. Twelve are repeat empty stubs across run folders.

A local evidence search found none of the 438 unresolved IDs in preserved `raw/`, `archive/`, or non-held `Inputs/articles/` files. The held files therefore cannot supply the missing source fields. The recovery gate must be a fresh, provenance-preserving acquisition, not inference or background enrichment.

| Originating run | Source-empty files | Resolved/closed | Conditional recovery |
|---|---:|---:|---:|
| `20260814T155332+0800-loose-goal` | 38 | 0 | 38 |
| `20260814T210304+0800-loose-goal` | 15 | 1 | 14 |
| `20260815T173433+0800-loose-goal` | 182 | 101 | 81 |
| `20260818T113653+0800-loose-goal` | 442 | 251 | 191 |
| `20260831T200105+0800-canonical-loose-ingest` | 167 | 41 | 126 |
| **Total** | **844** | **394** | **450** |

## Samples reviewed

Samples were checked against both the note content and their run evidence. The automated gates then applied the same checks to every file in the bucket.

| Class | Representative samples | Observed result |
|---|---|---|
| `source-empty` | `9427138315-untitled.md`; `9446381823-untitled.md`; `2026_08_1266310042-untitled.md` | Empty title/date/URL/body and `{}` raw response. Recovery requires a new source fetch. |
| `duplicate-arrivals` | `2026_08_1245306350-assumption-testing-the-iran-war-is-a-case-of-allia.md`; `2026_08_1246736993-the-draft-budget-of-minister-of-finance-riikka-pur.md` | Run manifest records identical URL, publisher, title, and body identity; compiled URL agrees. |
| `already-compiled` | `2026-08-1251622954-california-and-nevada-battle-multiple-large-wildfires.md`; `9427057750-driver-who-broke-sound-barrier-looks-to-do-it-again.md` | Current hash matches hold evidence and canonical compiled source exists. |
| `cascade-already-compiled` | `2026-08-1247803499-press-release-nigeria-joins-world-energy-council-as-newest-member-committee.md`; `2026-08-1248353871-sovereignty-below-the-threshold-why-arctic-security-demands-a-nordic-economic-strategy.md` | Computed cascade destination already exists with the same source URL. |
| `already-compiled-normalized-collision` | `2026-08-1251636596-trump-administration-releases-fifth-batch-of-ufo-files-including-new-videos-and-reports.md`; `9427387804-joint-base-charleston-re-named-joint-base-lindsey-graham-in-honor-of-late-senator.md` | Semantic-duplicate decision remains supported by hash and exact URL evidence. |
| `duplicate-stub` | `9414854040-untitled.md`; `9415100946-untitled.md` | Exact empty stubs; source-bearing records were successfully compiled. |
| `consumed` | `9415100946-reconfiguring-us-ethiopia-military-logistics-allia.md`; `9418248606-building-africas-defence-innovation-ecosystem-sov.md` | Retained source evidence after successful compile/cascade; compiled URLs agree. |
| `off-topic-irrelevant` | `9419450533-outh-africa-ivory-coast-advance-to-wafcon-quarter.md`; `9415665874-beyond-time-and-space-in-diplomacy-ambassador-jaiy.md` | Explicit sports/biographical false-positive decisions remain present; matching compiled sources warrant only a separate corpus-scope review. |
| `already-compiled-post-route` | `9393567011-column-the-legacy-of-trkiyes-most-contested-coup-attempt---hstoday.md`; `9399468443-usafs-autonomous-ai-fighter-drone-fires-live-amraam-missile-in-historic-test.md` | Post-route duplicates have unchanged hold hashes and exact compiled source URLs. |

## Recommended follow-up sequence

1. Leave all 2,258 hold files in place. Nothing in this audit should be fed into the live 30-article queue.
2. If recovery is desired, create a new bounded task for the 438 unresolved unique IDs. Freeze a deduplicated recovery manifest, reacquire source evidence through an authorized source, and route only newly source-complete records through the normal gates.
3. Before accepting a recovered record, recheck article ID, canonical URL, publication date, title, and body against the compiled corpus so a later duplicate cannot re-enter.
4. Separately decide whether the 18 compiled counterparts of the earlier off-topic files belong in the corpus. This is a scope decision, not an input-hold repair.
5. Add post-enrichment hash evidence to future `consumed/` moves. This improves auditability but does not require reprocessing the 26 existing records.

## Evidence sources

The result was reconciled against the hold folders themselves; the corresponding source-empty, duplicate, already-compiled, normalized-collision, cascade-conflict, and Africa-security hold manifests under `runs/2026-08-14/`, `runs/2026-08-15/`, `runs/2026-08-18/`, `runs/2026-08-21/`, and `runs/2026-08-31/`; and the current compiled article notes under `entities/article/`. The ignored run artifacts and article corpus remain local evidence and are not added to this PR.
