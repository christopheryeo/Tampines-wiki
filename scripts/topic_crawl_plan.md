---
type: plan
name: topic-crawl
status: ready
created: 2026-09-06
updated: 2026-09-18
owner: ChatGPT Codex
---

# Topic Crawl Plan

## Objective

Produce the complete, source-backed set of in-range news articles for each selected canonical Topic
Entity — via a two-source union (NewsAPI.ai keyword search ∪ environment-grounded URL backfill) — and land
them as enriched, cascaded vault articles, advancing each topic's crawl checkpoint.

Run a governed, restartable crawl **by topic** using a **two-source union** so coverage is broader
than any single discovery path. For each selected canonical Topic Entity, over one inclusive
publication-date range:

- **SET A** — crawl the topic with **NewsAPI.ai keyword search**; the returned articles are SET A,
  and their canonical URLs/URIs are remembered.
- **SET B** — use the grounded URL-discovery capability of the current execution environment for
  all article URLs related to the topic, then **remove any URL already in SET A**; the remainder is
  SET B. In a Claude environment use Claude-grounded discovery; in a Codex environment use
  Codex-grounded discovery.
- **Crawl SET B** — fetch every SET B article through NewsAPI.ai (URL → URI → article), gated the
  same way as SET A.

The accepted result is **SET A ∪ (validated SET B)** — the full set of articles crawled about the
topic over the date range. Accepted articles are then normalized into the raw article contract,
enriched, and compiled/cascaded, and the topic checkpoint is advanced.

The plan is reusable and contains no fixed topic, query, or date. A goal prompt supplies the
run-specific topic(s) and date range. It handles **one topic per pass** and loops over multiple
topics with per-topic isolation and checkpoints, so a run can stop partway and resume without
duplicating completed work.

> This file supersedes the former single-topic `topic_crawl_plan.md` and the
> `multi_step_topic_crawl_plan.md`, which have been merged here.

## Invocation inputs

Required:
- **`topics`** — one canonical Topic (ID, exact display name, wikilink, or unambiguous path), an
  explicit list of them, or "the next N eligible topics".
- **`dateStart`** / **`dateEnd`** — inclusive `YYYY-MM-DD` publication-date boundaries, expressed
  in the invocation **`timezone`** — not in the provider's timezone. See the Step 3 provider date
  window rule before submitting them to NewsAPI.ai.

Optional:
- **`timezone`** — defaults to `Asia/Singapore`. Never infer a default date window.
- **`maxCandidates`** — safety ceiling on unique canonical URLs per topic. Defaults to
  **500** for both SET A and SET B, independently. Record the provider total, retrieved count,
  and any uncollected remainder in the manifest; a ceiling is never evidence that the provider
  returned no further coverage.
- **`languages`** / named source constraints; **`runLabel`** — short run identifier.
- **`retryPolicy`** — finite retry count and backoff (else the runtime default).

## Goal prompt

> Execute `scripts/topic_crawl_plan.md`.
> Topics: `<topic IDs, or "the next N eligible topics">`. Date range `<YYYY-MM-DD>` to
> `<YYYY-MM-DD>`, inclusive. Timezone `Asia/Singapore`. Use the runtime endpoint and
> `NEWSAPI_AI_API_KEY` without exposing secrets. Build SET A from NewsAPI.ai keyword search, SET B
> from the current environment's grounded related-URL list minus SET A (Claude-grounded in Claude;
> Codex-grounded in Codex), then crawl SET B. Run every step and gate in order;
> produce per-topic manifests and a run receipt; advance checkpoints only after validation; rebuild
> the Topic catalog; and report per-topic SET A / SET B / accepted / rejected / duplicate counts,
> failures, elapsed time, and average time per topic. Do not mark complete until all required gates
> pass.

For an autonomous Goal Mode run, use the stricter invocation and durable-state
requirements in `scripts/topic_crawl_goal_contract.md`. That contract replaces
routine review handoffs with the approved policy and a candidate-level terminal
ledger; it does **not** relax this plan's source, relevance, or validation gates.

## Governing rules

- Follow `README.md`, `scripts/entity_cascade_procedure.md`, and
  `scripts/enriched_radar_load_procedure.md` where applicable.
- Markdown notes are the source of truth; databases, indexes, catalogs, dashboards, and radar
  outputs are derived surfaces.
- Preserve provenance from discovery through cascade. Never enrich article claims or complete
  missing body text from model knowledge or live lookups outside the provider response and
  preserved source evidence.
- The environment's grounded URL list is candidate discovery only and must use live web/tool
  access, not recalled knowledge. In a Claude environment use Claude-grounded discovery; in a
  Codex environment use Codex-grounded discovery. Every SET B URL must pass URI mapping,
  in-range date, identity, and completeness gates; unmappable or unverifiable URLs are held or
  rejected, **never fabricated**.
- Credentials are runtime-only. Read the key from `NEWSAPI_AI_API_KEY`; never persist the key,
  credential-bearing headers, or credential-bearing URLs in the repository, notes, receipts,
  manifests, or logs. Verify credential presence with safe booleans only.
- Treat SET A discovery, grounded environment discovery, URI mapping, retrieval, normalization,
  enrichment, and compile/cascade as **separate checkpoints**. Never overwrite an existing raw or
  compiled note.
- Record how each article was discovered (SET A keyword vs SET B environment-grounded suggestion)
  and the environment used (Claude or Codex) in the run manifests, not in new frontmatter fields.
- Both discovery paths over-collect. **Never ingest a keyword or URL match without a topical-relevance
  judgement** (Step 7): each candidate is judged relevant/off-topic from its own content against the
  topic definition, and only relevant articles are cascaded.
- Time every compile/cascade run and report elapsed time, processed count, and average per article
  (report zero honestly rather than a misleading average).
- Keep outcome levels separate: a candidate that passes its identity, date, completeness, duplicate,
  normalization, enrichment, and article-quality gates remains `succeeded` even if an unrelated
  repository-wide validation or bookkeeping check later fails. Record `held` or `rejected` only for
  that candidate's own failed gate. The topic crawl status is run-level and may be `Failed` or
  incomplete while individual articles remain successful; never relabel successfully processed
  articles as failed because the overall topic run failed.

---

## Step 0 — Preflight (once per run)

1. Read the current Topic Entity notes and canonical taxonomy.
2. Select only **active** canonical topics; exclude archived notes, legacy `Imported article topic`
   notes, and topics already `Queued` or `In progress`.
3. Validate the date range and timezone; stop if a boundary is absent/invalid or `dateStart` >
   `dateEnd`.
4. Verify the runtime endpoint, `NEWSAPI_AI_API_KEY`, and the current environment's grounded URL
   discovery availability (safe booleans only). Default an omitted `maxCandidates` to 500 and
   record it explicitly.
5. Freeze the selected topic IDs, checkpoints, prompts, and invocation parameters in a run manifest
   under `runs/YYYY-MM-DD/artifacts/topic-crawls/`.

**Gate:** stop before any endpoint call if topic selection, dates, or runtime readiness fails.

Then run Steps 1–10 **per topic**, isolating failures to the affected topic.

## Step 1 — Resolve and freeze the topic

1. Resolve the topic to exactly one file under `entities/topic/`; read its `topicId`, exact
   `displayName`, aliases, status, `## Crawl Prompt`, `crawlStatus`, and `lastCrawledAt`.
2. Require an active Topic and one usable Crawl Prompt — never silently substitute a broader or
   similarly named Topic. If the topic does not resolve to exactly one active Topic Entity, register
   it first via `scripts/add_topic.md`, then re-run the plan for it (this plan never creates a topic).
3. Freeze the Topic file, invocation inputs, resolved timezone, current checkpoint, search scope,
   `maxCandidates`, and starting loose-input inventory in the run directory.
4. Apply the governed `Queued` → `In progress` transitions immediately around the physical crawl via
   `scripts/update_topic_crawl_status.md` (one call per transition). Do not advance `lastCrawledAt`
   yet — only `scripts/end_topic_crawl.md` may advance it, at completion (Step 10).

## Step 2 — Prepare and validate the crawl prompt

1. Validate exactly one usable `## Crawl Prompt` for the topic.
2. If missing/invalid, build one from the canonical definition, aliases, scope, inclusions, and
   exclusions per the topic-crawl procedure; record its version/hash in the manifest.
3. Build and freeze a `search-profile.json` in the run directory. It must contain the exact SET A
   keyword variants derived from the topic's display name, aliases, and Crawl Prompt, plus the
   approved official publisher domains implied by the topic scope. It is a run artifact, not a
   change to the frozen Topic schema. Use the recorded keyword variants within one independent
   500-candidate ceiling per topic, deduplicating results by canonical URL and URI.

**Gate:** only a topic with a validated prompt proceeds to discovery.

## Step 3 — SET A: crawl the topic with NewsAPI.ai keyword search

Call `POST https://eventregistry.org/api/v1/article/getArticles` once per topic (paging as needed):
```json
{
  "action": "getArticles",
  "keyword": "<exact Topic displayName or a validated prompt keyword>",
  "lang": ["eng"],
  "dateStart": "<YYYY-MM-DD>",
  "dateEnd": "<YYYY-MM-DD>",
  "articlesSortBy": "date",
  "articleBodyLen": -1,
  "dataType": ["news"],
  "isDuplicateFilter": "keepAll",
  "resultType": "articles",
  "apiKey": "<runtime NEWSAPI_AI_API_KEY>"
}
```
1. Page through results using the provider's `articlesPage` parameter until no new in-range
   articles remain or `maxCandidates` is reached. Request at most 100 articles per page; validate
   the returned `articles.page`, `articles.pages`, `articles.count`, and `articles.totalResults`
   before accepting each page. A provider response that repeats page 1 for a requested later page
   is a paging failure, not a duplicate page or a complete result.
2. For every returned article, record the canonical URL, NewsAPI.ai article URI, title, source,
   publication timestamp, language, and body — and **remember the canonical URLs and URIs as SET A**.
3. Canonicalize URLs (resolve redirects, strip non-identity tracking params) and deduplicate SET A by
   canonical URL and by URI.
4. SET A articles are already retrieved; carry them forward to the gates in Step 7 (no mapping
   needed).

**Provider date window (required).** NewsAPI.ai's `dateStart`/`dateEnd` select **UTC** days, while
`dateStart`/`dateEnd` as invoked — and the Step 7 date gate — are days in the invocation `timezone`.
For `Asia/Singapore` (UTC+8) the two windows are offset by eight hours, so submitting the local dates
verbatim silently crawls the wrong window. Instead:

1. Convert the local window to UTC instants: `windowStart = dateStart 00:00` and
   `windowEnd = dateEnd+1 00:00`, both in the invocation timezone, expressed as UTC.
2. Submit the **UTC days that overlap** that span — `dateStart` = `windowStart`'s UTC date and
   `dateEnd` = (`windowEnd` − 1s)'s UTC date. For a single Singapore day this is always a two-day
   provider window.
3. Keep Step 7 gate 2 as the authority: discard any returned article whose publication timestamp
   falls outside `windowStart`..`windowEnd`. The widened provider window over-collects by design;
   the gate, not the query, defines the result.
4. Because `articlesSortBy: "date"` returns newest first, paging may stop as soon as a page's oldest
   `dateTimePub` precedes `windowStart` — the window is then fully covered.

Record the local window, the derived UTC provider window, and the scanned-vs-in-window counts in the
manifest.

> **Evidence (2026-09-18 daily run).** Submitting the local dates verbatim for a same-day Singapore
> crawl (`dateStart` = `dateEnd` = `2026-09-18`, run at 03:00 SGT = 19:00 UTC on 2026-09-17) returned
> `totalResults: 0` for **every** topic — and also for a `Trump` control keyword — because that UTC day
> had not yet begun. Converting to the overlapping UTC window `2026-09-17`..`2026-09-18` and applying
> the Step 7 gate returned 6,183 in-window candidates across 92 query groups. Left uncorrected, the
> run would have closed all 96 canonical topics with a false zero. The same offset silently drops the
> 00:00–08:00 SGT slice of **every** day-bounded crawl, whatever time of day it runs.

**Keyword selection (required).** NewsAPI.ai treats a multi-word `keyword` as a near-exact phrase, so
the literal display name usually under-collects (e.g. `Taiwan Strait Security` → a handful; a
Singapore-anchored multi-word phrase → zero). Derive the SET A keyword from the topic's **core subject
phrase(s)** — a short phrase that genuinely appears in coverage — or pass a keyword **array** with
`keywordOper: "or"`, not the whole display name. For a cluster of Singapore-specific topics, one broad
Singapore-defence pool (`MINDEF`, `Singapore Armed Forces`, `Singapore defence`) that is then
classified per sub-topic outperforms many narrow per-topic queries.

**High-volume recall rule (required).** When the provider `totalResults` for the chosen keyword is
much larger than `maxCandidates` (order of magnitude), the date-sorted first `maxCandidates` cover only
the most recent few days, and relevant items earlier in the window fall past the cap. In that case do
**not** trust the recent-N slice: add a Singapore/topic anchor to the SET A query (narrowing to the
relevant sub-stream), and/or page by date buckets across the window. Record the provider total, the
retrieved count, and the uncollected remainder in the manifest.

**Gate:** a zero SET A result is valid only when the keyword search itself completed successfully — a
zero is not proof that no coverage exists (SET B may still find articles).

## Step 3A — SET A relevance gate

Before any SET B discovery, assess every unique SET A article against the resolved Topic Entity's
definition, aliases, inclusions/exclusions, title, metadata, and returned source body. Record
`relevant`, `relevanceConfidence`, `relevanceReason`, and one terminal outcome for each candidate:

- **relevant** — carries forward to the identity/date/completeness/duplicate gates in Step 7;
- **off-topic** — rejected immediately and never proceeds to enrichment, staging, or cascade;
- **held** — insufficient or conflicting source evidence; never infer relevance from model knowledge.

The SET A relevance decision is mandatory before calling grounded URL discovery. Retain every SET A
canonical URL and URI for SET B deduplication even when the article is off-topic or held.

## Step 4 — SET B candidates: environment-grounded related URLs

1. Use the grounded URL-discovery capability of the current environment for **all article URLs
   related to the topic** within the date range, using the Topic `displayName`, aliases, and the
   Crawl Prompt's inclusions/exclusions. In Claude use Claude-grounded discovery; in Codex use
   Codex-grounded discovery. Request a plain list of direct article URLs only — no homepages,
   index/category pages, snippets, or commentary.
2. Record the exact request, environment name, and raw returned list in the run manifest.
3. Canonicalize every returned URL (resolve redirects, strip non-identity tracking params); drop
   obvious non-article URLs.
4. When SET A is operational but returns zero or materially weak coverage, run the same bounded,
   attributable direct-article discovery against the frozen official-domain list in the search
   profile. Treat those URLs as SET B; retain the query, source domain, and results. This improves
   recall for official Singapore security coverage without treating a provider zero as proof of no
   coverage.

## Step 4A — SET B URL relevance gate

Before URI mapping or provider retrieval, assess each remaining grounded URL using the discovery
result's attributable title, snippet, publication evidence, and URL path against the resolved Topic
Entity. Record `urlRelevant`, `urlRelevanceConfidence`, and `urlRelevanceReason`:

- reject clearly off-topic, non-article, duplicate, or out-of-range candidates immediately;
- hold candidates without sufficient attributable evidence;
- map and retrieve only URLs assessed as plausibly relevant.

This is a cost-control gate, not the final relevance decision. A URL that passes it must still pass
the source-body relevance gate in Step 7.

## Step 5 — Compute SET B = grounded URLs − SET A

1. Remove from the environment's canonicalized list every URL already present in SET A, comparing on the
   **canonical** URL (case-insensitive, trailing slash ignored, tracking params removed).
2. Deduplicate the remainder among itself. The result is **SET B**.
3. Apply `maxCandidates` to SET B if set. Record SET B and the removed-as-duplicate count.

## Step 6 — Crawl SET B: map to URI and retrieve

For each SET B URL:
1. Map it to a NewsAPI.ai URI: `POST https://eventregistry.org/api/v1/articleMapper`
   ```json
   { "articleUrl": "<canonical article URL>", "apiKey": "<runtime NEWSAPI_AI_API_KEY>" }
   ```
   Validate HTTP status, content type, and structure before reading the URI. A `200` response whose
   requested URL maps to `null`, an empty string, or an unrecognised value is `mapping-unusable`,
   not success: record it and immediately take the Step 6 extraction fallback. One attempt per URL
   unless a transient error justifies a retry.
2. **Deduplicate by URI**, including against SET A — if a SET B URL maps to a URI already in SET A,
   it is the same article; drop it.
3. Retrieve each remaining unique URI: `POST https://eventregistry.org/api/v1/article/getArticle`
   ```json
   {
     "action": "getArticle",
     "articleUri": "<NewsAPI.ai article URI>",
     "infoArticleBodyLen": -1,
     "resultType": "info",
     "apiKey": "<runtime NEWSAPI_AI_API_KEY>"
   }
   ```
4. If a URL cannot be mapped or the URI body is missing/partial, try
   `POST https://analytics.eventregistry.org/api/v1/extractArticleInfo` with the canonical `url`, then
   an approved direct publisher-URL retrieval. Record the exact route. If a complete source-backed
   body still isn't available, **hold** the candidate — never synthesize text.
5. **Official Singapore sources (required path).** The highest-value SET B items are often official
   releases on `mindef.gov.sg` / `mfa.gov.sg` that do not map in NewsAPI.ai; a *summarizing* fetch
   (e.g. a small-model WebFetch) returns paraphrase, not the source body, and must never be normalized
   as if verbatim — that is synthesis, and the candidate is **held**. Retrieve these only through an
   approved **full-text** extractor for the whitelisted official domains that returns the complete
   published text; otherwise hold. Always run `extractArticleInfo` (or equivalent) first to read the
   **true publication date** and drop out-of-range items before any body work — a discovery snippet's
   date is not authoritative (a "Singapore urges Israel on Gaza aid" item surfaced in a 2026 window was
   in fact dated 2025 and was correctly dropped by this check).

## Step 7 — Final source-body gate for SET A ∪ SET B

Apply the same gates to every candidate from both sets. Accept only when:
1. its returned URL/title/source/event correspond to the discovered article;
2. its publication timestamp, in the invocation timezone, falls inside `dateStart`..`dateEnd`
   **(this date gate is essential for SET B, whose URLs are not date-bounded at discovery)**;
3. its structure is coherent and not abruptly truncated;
4. the body is non-empty source text (a character/word count alone is not proof of completeness);
5. it is not already present in `Inputs/articles/` or `entities/article/` by article ID, canonical
   URL, URI, or source identity; and
6. **it is topically relevant to the resolved Topic Entity**. SET A must already have passed Step
   3A; this is the final source-body check for SET B and a consistency check for SET A.

**Relevance classification (required).** Keyword search (SET A) and URL discovery (SET B) both
over-collect: short tokens match unrelated coverage — e.g. "NS" matches railroads (Norfolk Southern,
Nederlandse Spoorwegen), "enlisted" matches *listed* firms, and bare "policy"/"system" match generic
news. So every candidate must be judged for topical relevance against the resolved topic's
`displayName`, `aliases`, definition, and `## Crawl Prompt` scope (its inclusions/exclusions), using
**only** the article's own title, body, and metadata — never live web or model background knowledge.
For each candidate record, in the run manifest, a boolean `relevant`, a 0–1 `relevanceConfidence`,
and a one-line `relevanceReason`. Accept only `relevant: true` candidates that also clear gates 1–5;
drop the rest with reason `off-topic`. When relevance is genuinely borderline, **hold** rather than
guess. These judgements are run evidence and are **not** written into article frontmatter.

**Vault relevance policy — Singapore-strategic (standing bar).** This is a Singapore (SAF / MINDEF)
media-monitoring vault, and many canonical topics are *regional or foreign by definition*. Judging
relevance against a topic's definition alone therefore admits enormous volumes of coverage with no
bearing on Singapore (a broad keyword can return thousands of in-definition but off-mission articles).
So relevance is judged against the topic definition **and** this vault bar: accept a candidate only
when it has a **Singapore nexus** (Singapore / SAF / MINDEF / a named SG agency, or an
ASEAN-neighbourhood matter that bears on Singapore) **or** is a **top-tier regional development** a
Singapore defence desk would track (a major state-level agreement, acquisition, incident, exercise, or
force-posture move). Drop routine third-country coverage, opinion/analysis/retrospective essays, and
tangential keyword matches. Yield scales with a topic's Singapore-centricity — regional/foreign topics
legitimately close with few or zero accepted, which is a correct result, not a failure. This bar is
the standing policy; a run does not re-litigate it.

**Duplicate gate (required, before normalization and enrichment).** Operationalize gate 5 as an
explicit pre-normalization step: for every relevant candidate, hash its `articleId`
(`crawl-<sha256-of-canonical-url>`) and canonical URL against existing `Inputs/articles/**` and
`entities/article/**`. Drop matches with a terminal `duplicate` disposition **here** — before Step 8
and before spending any enrichment call — rather than discovering them as an `ingest_cascade`
`FileExistsError` after enrichment has already been paid for. A prior run's compiled article means the
topic is already covered; record it as `duplicate`, not as a new cascade.

Drop out-of-range, hallucinated, non-article, incomplete, or **off-topic** candidates with a recorded
reason. The surviving set is the topic's accepted articles = **relevant SET A ∪ validated relevant
SET B**. No candidate may reach Step 8 without passing its applicable relevance gate(s).

## Step 8 — Normalize accepted articles

Write each accepted result to `Inputs/articles/YYYY-MM/` (month from its verified publication date in
the invocation timezone), with `articleId: crawl-<sha256-of-canonical-url>` and filename
`<articleId>-<slugified-title>.md`, using the frozen intake contract:
```markdown
---
articleId: crawl-<sha256-of-canonical-url>
articleTitle: <source title>
publishedDate: <YYYY-MM-DD in invocation timezone>
category: <validated enrichment value>
topic: <canonical Topic displayName>
tone: <Factual or Opinionated after enrichment>
toneSentiment: <Positive, Neutral, or Negative after enrichment>
eventType: <Facilitated or Unfacilitated after enrichment>
tags:
  - <active existing-vocabulary tag after enrichment>
outlets:
  - <canonical source outlet>
countries:
  - <validated country>
coverageCount: 1
mediaCount: 0
sourceType: crawl
url: <canonical article URL>
---

<complete retrieved source body as plain narrative text, without wikilinks or compiled sections>
```
Provider IDs, discovery method (SET A / SET B), queries, mapping/retrieval records, hashes, and
completeness decisions belong in the run manifests, not in new frontmatter fields. A normalized note
is staged, not cascade-ready, until enrichment is reviewed. Preserve existing input files unless this
run owns the same unique article ID.

**YAML safety (required).** Serialize every string frontmatter value safely — headline text routinely
contains colons, quotes, or a leading `#`/`[`, and an unquoted value breaks the whole YAML block
(the cascade's input gate then rejects the batch). Double-quote `articleTitle` and any string
`outlets`/`countries` value (JSON string form is valid YAML), or emit them with a YAML-safe
serializer. This is the same class of failure as the unquoted `#`-tag hazard in
`scripts/entity_cascade_procedure.md`.

## Step 9 — Enrich and validate the frozen batch

1. Freeze a newline-delimited manifest of only the newly normalized filenames.
2. Run `scripts/enrich_radar_inputs.py` to assess existing-vocabulary tags, outlet, outlet country,
   institutional category, tone, sentiment, and event type. Enrich **only** the frozen manifest of
   accepted, relevance-passed, de-duplicated inputs — **never** raw SET A. Every model call is spent
   after the relevance and duplicate gates, so off-topic and already-compiled articles cost nothing.
   - **Preserve the canonical topic (required).** Pass `--preserve-topic`. Without it, enrichment
     overwrites the note's `topic` with the first issue tag, and `ingest_cascade` then routes the
     Coverage backlink to the wrong canonical topic. (Alternatively, re-assert `topic: <canonical
     displayName>` on each accepted note after enrichment and before Step 10.)
   - **Reuse unchanged work (fewer calls).** Pass `--cache-dir <run>/artifacts/enrich-cache` so a
     rerun, resume, or re-crawl of a byte-identical input under the same model and prompt version
     costs **zero** API calls. This directly serves the "resume without redoing work" requirement.
   - **Optional call reducers (opt-in; validate before default).** `--conditional-review` skips the
     second pass when the primary pass is unambiguously high-confidence (`--review-skip-confidence`),
     and `--review-model` allows a cheaper/stronger review tier. Both trade the two-pass agreement
     guard for fewer calls, so run an A/B (same inputs, with vs without) and confirm classifications do
     not drift before relying on them. A future **batched** mode (N articles per structured request,
     as two batched passes) is the larger call-count win and is the next enrichment enhancement,
     gated behind the same A/B.
3. Require the configured independent-agreement and confidence thresholds before applying
   judgment-heavy values; send disagreements/low-confidence/missing evidence to attributed review;
   apply only reviewed results.
4. Confirm completeness:
   ```bash
   python3 scripts/enrich_radar_inputs.py --input-dir Inputs/articles/<YYYY-MM> --manifest <frozen-manifest-path> --check-complete
   ```
   Process separate publication months separately when the range crosses a month boundary.

### Step 9A — policy resolution and resilient execution

Apply `schemas/topic_crawl_resolution_policy.yaml` before human review. Record
the policy version, field-level rationale, and a distinct `policy-resolved`
outcome. Cascade only items whose every enrichment field has a terminal
decision; retain unsupported or conflicting evidence as `held`.

Before the full run, perform an authenticated one-article preflight. Use
bounded concurrency, per-item checkpoints, finite retries, and a live progress
receipt so a transient API or quota failure can resume without redoing work.

## Step 10 — Compile, cascade, and close the topic

For each affected month:
1. Dry preview: `python3 scripts/ingest_cascade.py --month <YYYY-MM> --manifest <month-manifest> --dry-run`
2. Resolve every preview error or hold the affected article.
3. Real run: the same command without `--dry-run`.
4. Confirm articles moved to `entities/article/YYYY-MM/` and that backlinks, coverage, catalogs,
   logs, and validation updated per the cascade procedure.
5. Assert that each cascaded article is linked in the intended canonical Topic's `## Coverage` block.
   Where the article's recorded topic identity is unambiguous, repair the missing backlink only with
   `scripts/patch_coverage.py`, then validate it; otherwise hold it.
6. Persist both the dry-run and real `ingest_cascade` receipts in the durable goal state. The real
   receipt must show the month, `status: ok`, non-zero processed count, zero failures, elapsed time,
   and average seconds per article. A file existing under `entities/article/` does not replace this
   receipt.
7. Report input/processed/created/held/failure counts, elapsed time, and average seconds per article.

The control tags `#source` and `#saf` remain on compiled article notes but are not issue tags and do
not need corresponding `entities/tag/` notes. Only issue tags from the active tag vocabulary are
resolved during cascade.

**Readback-validate every status write (required).** After each `update_topic_crawl_status` /
`end_topic_crawl` write, **re-read the note** and assert the frontmatter actually persisted the
intended `crawlStatus` (and, for completion, that `lastCrawledAt` advanced) before reporting success.
On this vault (Dropbox-synced), a write can be silently lost to a sync race — a completed crawl was
observed with its completion logged but the note still `In progress`. Do not trust the log line or the
write call; trust the re-read. Re-apply the transition if the readback disagrees.

Then close the topic:
- Mark the topic crawl `Complete` and advance `lastCrawledAt` **only** if SET A search, SET B
  discovery, and all required retrieval/bookkeeping succeeded — via `scripts/end_topic_crawl.md`, the
  only procedure that advances `lastCrawledAt` (`scripts/update_topic_crawl_status.md` routes a
  `Completed` target through it automatically).
- On any required-service failure, set the topic to `Failed` via `scripts/update_topic_crawl_status.md`,
  retain all recoverable evidence, and leave `lastCrawledAt` unchanged.
- A zero-result topic may close complete only when both SET A search and SET B discovery were
  verified operational and the report states that zero in-range articles were found.

Do not project to UAT, run the Issue Radar, or edit Issue entities unless the invoking goal
explicitly adds that downstream work. This plan's default boundary ends at a validated Markdown
cascade.

## Step 11 — Complete the run (once per run)

1. Reconcile SET A, its relevance gate, environment-grounded discovery, the SET B URL relevance
   gate, SET B mapping/retrieval/source-body relevance, normalization, enrichment, and cascade
   manifests so every candidate has exactly one terminal disposition.
   Deduplicate by canonical URL/provider URI before counting, while retaining all
   matched topics on the unique article record.
2. Rebuild `entities/topic/catalog.md` from source notes.
3. Write the run receipt: selected topics, per-topic SET A / SET B / accepted / rejected / duplicate
   counts, mapping-unusable/extraction-fallback counts, failures, per-month dry-run and real cascade
   receipt paths, elapsed time, and average time per topic. Use a single canonical `status` field in
   both durable state and receipt; do not introduce an alternate `goalStatus` field.

## Step 12 — Write the daily Crawl Log (once per run; mandatory)

After reconciliation and the run receipt, create or update the Singapore-date daily note in
`entities/crawl-log/` named `YYYY-MM-DD Crawl Log.md`. Add the completed crawl as one entry in
ascending actual-start-time order. The entry must include:

1. `#### Cascaded articles by topic` — only topics with one or more successfully cascaded articles,
   with each exact cascaded count.
2. `#### Crawl review` — outcome, dispositions, validation state, and receipt evidence.
3. `#### Lessons learned` — evidence-based operational learnings.
4. `#### Recommendations to improve the topic crawl plan` — evidence, recommended change, expected
   accuracy benefit, and expected OpenAI API-call reduction.

Record zero-result, partial, or failed crawls honestly in the review even when the topic table has
no rows. Treat each recorded recommendation as authorised for immediate implementation: apply the
scoped code or crawl-plan change, validate it, and record the result in the same Crawl Log entry.
Then update the daily note's aggregate frontmatter, append the domain audit `log.md` entry, and
regenerate `entities/crawl-log/catalog.md`.

## Breakout conditions

### Retry and resume
- Isolate failures by topic and by article wherever possible; one candidate's hold/rejection does not
  stop independent candidates unless it signals a systemic discovery/credential/endpoint/schema/
  provenance problem.
- Retry only the configured finite number of times with the configured backoff. Never retry
  indefinitely, and never treat a timeout as a successful zero-result crawl.
- Never advance a checkpoint from an incomplete, mismatched, or malformed provider response.
- If a run stops partway, resume from the run manifest and per-topic checkpoints (SET A captured,
  SET B computed, SET B fetched) rather than duplicating completed work.

### Stop triggers
Stop the affected stage without fabricating success when: the topic is absent/ambiguous/inactive or
lacks usable crawl instructions; a date boundary is absent/invalid; `NEWSAPI_AI_API_KEY` is
unavailable/rejected; grounded URL discovery is unavailable when SET B is required; a response
cannot be attributed to the submitted topic/URL/URI; URL-to-URI mapping fails and approved fallback
cannot resolve it; identity/date evidence conflicts irreconcilably; a body is missing/partial and no
approved source-backed retrieval recovers it; the article already exists or conflicts with an existing
source identity; required enrichment stays invalid; the input contract / article-quality / tag / link
checks fail; or continuing would require a production write or an unauthorized schema/rule change.

### Autonomous Goal Mode handoff rule

When invoked under `scripts/topic_crawl_goal_contract.md`, do **not** pause for ordinary candidate
judgement. Record individual retrieval, source-body, enrichment, identity, and relevance uncertainty
as an evidence-backed `held`, `rejected`, `off-topic`, or `duplicate` terminal disposition and continue
with independent candidates and topics. Handoff is required only for an unresolved credential or
required-discovery failure, systemic provider failure, provenance/manifest conflict, required rule or
schema change, unauthorized/destructive/production action, or unrecoverable validation failure. The
goal may close with held items, but never with an unreconciled candidate or unresolved critical event.

## End conditions (success)

The run succeeds only when the Step 11 run-level completion is done — every candidate across all
topics has exactly one final disposition, `entities/topic/catalog.md` is rebuilt, the run receipt
is written, and the Step 12 Crawl Log entry is recorded — and **every selected topic** passes all of
the following:

- [ ] Exactly one canonical Topic Entity resolved and frozen; both dates and timezone validated,
      and the provider date window derived from the invocation timezone per Step 3.
- [ ] SET A built from NewsAPI.ai keyword search; every page was verified with `articlesPage`, and
      its URLs/URIs recorded, canonicalized, deduplicated.
- [ ] Every SET A candidate passed the Set A relevance gate before SET B discovery, or has an
      explicit off-topic/held disposition.
- [ ] Environment-grounded related-URL list captured and canonicalized (Claude in Claude;
      Codex in Codex).
- [ ] SET B computed as grounded URLs minus SET A (canonical dedup), then deduped by URI against SET A.
- [ ] Every SET B URL passed the URL relevance gate before URI mapping/retrieval, then passed the
      final source-body relevance gate after retrieval.
- [ ] Every SET B URL has a URI-mapping disposition; multiple URLs → one URI treated as one article.
- [ ] Every `200` mapper response with no usable URI is explicitly `mapping-unusable` and follows the
      approved extraction fallback or receives a terminal hold.
- [ ] Every retrieved article used `article/getArticle` with `infoArticleBodyLen: -1`; key never
      persisted.
- [ ] SET A ∪ SET B passed identity, in-range date, complete-body, provenance, and duplicate gates;
      partial/missing bodies source-recovered or held (never generated); hallucinated/out-of-range
      SET B URLs dropped with reasons.
- [ ] Every accepted raw note uses the frozen input contract and plain source narrative.
- [ ] Every frozen note passed `enrich_radar_inputs.py --check-complete` after review.
- [ ] Compile/cascade validation passed for every processed month; timed receipt reports totals.
- [ ] Each cascaded article is backlinked from its intended canonical topic's Coverage block; every
      affected month has a valid dry-run and real cascade receipt in durable goal state.
- [ ] Every accepted article passed the topical-relevance gate; off-topic keyword/URL matches (e.g. a
      "NS" railroad hit) were dropped with `off-topic` reasons, not ingested.
- [ ] Every candidate has one final disposition; topic status/checkpoint reflect verified completion.
- [ ] The daily Crawl Log records the completed crawl, its positive cascaded-topic counts, review,
      lessons, and autonomous improvement recommendations.

## Tests / Verification

The plan is validated at two levels:

1. **Tooling tests (existing).** The plan orchestrates already-tested scripts — their unit tests are
   the mechanical safety net: `enrich_radar_inputs.py`, `ingest_cascade.py`, `article_quality.py`,
   `check_links.py`, and `generate_catalog.py` (see `tests/`). Run the repository test suite before
   relying on any change to them.
2. **End-to-end dry run (before a real crawl).** Validate the plan itself against a known topic and a
   narrow date range in an isolated run directory:
   - Pick one active canonical topic with known crawl history and a 2–3 day window.
   - Execute Steps 0–9, then Step 10 with `ingest_cascade.py --dry-run` only (do **not** cascade).
   - Record expected vs actual for **SET A count**, **SET B size** (after A-minus and URI dedup),
     **accepted count**, and rejected/held reasons; assert the dedup and in-range date gate behaved —
     no SET B URL already in SET A survived, and no out-of-range article was accepted.
   - Pass only if every candidate has exactly one disposition and the dry-run cascade preview is
     clean; then the same topic may be run for real.

A passing dry run on one topic validates the plan's mechanics, not every topic's coverage — do not
treat it as proof the whole batch will pass.

## Final report

Return one run report with: topics (IDs, names, date range, timezone, run directory, final statuses);
SET A keyword queries and counts; grounded discovery environment, request, and returned-URL count; SET B size after
removing SET A and after URI dedup; NewsAPI.ai mapping attempts, unique URIs, retrievals, extraction
fallbacks, and failures; complete/partial/missing/held/normalized/enriched/cascaded counts split by
SET A vs SET B; the relevance split (relevant vs `off-topic` dropped, with example off-topic titles);
per-month compile/cascade totals, elapsed time, and average processing time;
validation outcomes and unresolved limitations; and paths to receipts, manifests, assessments,
held-item evidence, created article notes, and affected entity notes.
