---
type: plan
name: topic-crawl
status: ready
created: 2026-09-06
updated: 2026-09-12
owner: ChatGPT Codex
---

# Topic Crawl Plan

## Purpose

Run a governed, restartable crawl **by topic** using a **two-source union** so coverage is broader
than any single discovery path. For each selected canonical Topic Entity, over one inclusive
publication-date range:

- **SET A** — crawl the topic with **NewsAPI.ai keyword search**; the returned articles are SET A,
  and their canonical URLs/URIs are remembered.
- **SET B** — ask **Claude** for all article URLs related to the topic, then **remove any URL
  already in SET A**; the remainder is SET B.
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
- **`dateStart`** / **`dateEnd`** — inclusive `YYYY-MM-DD` publication-date boundaries.

Optional:
- **`timezone`** — defaults to `Asia/Singapore`. Never infer a default date window.
- **`maxCandidates`** — safety ceiling on unique canonical URLs per topic (applies to SET B).
- **`languages`** / named source constraints; **`runLabel`** — short run identifier.
- **`retryPolicy`** — finite retry count and backoff (else the runtime default).

## Goal prompt

> Execute `scripts/topic_crawl_plan.md` (with `scripts/start_topic_crawl.md` for the endpoint call).
> Topics: `<topic IDs, or "the next N eligible topics">`. Date range `<YYYY-MM-DD>` to
> `<YYYY-MM-DD>`, inclusive. Timezone `Asia/Singapore`. Use the runtime endpoint and
> `NEWSAPI_AI_API_KEY` without exposing secrets. Build SET A from NewsAPI.ai keyword search, SET B
> from Claude's related-URL list minus SET A, then crawl SET B. Run every step and gate in order;
> produce per-topic manifests and a run receipt; advance checkpoints only after validation; rebuild
> the Topic catalog; and report per-topic SET A / SET B / accepted / rejected / duplicate counts,
> failures, elapsed time, and average time per topic. Do not mark complete until all required gates
> pass.

## Governing rules

- Follow `README.md`, `scripts/entity_cascade_procedure.md`, and
  `scripts/enriched_radar_load_procedure.md` where applicable.
- Markdown notes are the source of truth; databases, indexes, catalogs, dashboards, and radar
  outputs are derived surfaces.
- Preserve provenance from discovery through cascade. Never enrich article claims or complete
  missing body text from model knowledge or live lookups outside the provider response and
  preserved source evidence.
- **Claude's URL list is candidate discovery only, and must be grounded** (live web/tool, not
  recalled from memory). Every SET B URL must pass URI mapping, in-range date, identity, and
  completeness gates; unmappable or unverifiable URLs are held or rejected, **never fabricated**.
- Credentials are runtime-only. Read the key from `NEWSAPI_AI_API_KEY`; never persist the key,
  credential-bearing headers, or credential-bearing URLs in the repository, notes, receipts,
  manifests, or logs. Verify credential presence with safe booleans only.
- Treat SET A discovery, Claude discovery, URI mapping, retrieval, normalization, enrichment, and
  compile/cascade as **separate checkpoints**. Never overwrite an existing raw or compiled note.
- Record how each article was discovered (SET A keyword vs SET B Claude-suggested) in the run
  manifests, not in new frontmatter fields.
- Time every compile/cascade run and report elapsed time, processed count, and average per article
  (report zero honestly rather than a misleading average).

---

## Step 0 — Preflight (once per run)

1. Read the current Topic Entity notes and canonical taxonomy.
2. Select only **active** canonical topics; exclude archived notes, legacy `Imported article topic`
   notes, and topics already `Queued` or `In progress`.
3. Validate the date range and timezone; stop if a boundary is absent/invalid or `dateStart` >
   `dateEnd`.
4. Verify the runtime endpoint, `NEWSAPI_AI_API_KEY`, and Claude grounded-discovery availability
   (safe booleans only).
5. Freeze the selected topic IDs, checkpoints, prompts, and invocation parameters in a run manifest
   under `runs/YYYY-MM-DD/artifacts/topic-crawls/`.

**Gate:** stop before any endpoint call if topic selection, dates, or runtime readiness fails.

Then run Steps 1–10 **per topic**, isolating failures to the affected topic.

## Step 1 — Resolve and freeze the topic

1. Resolve the topic to exactly one file under `entities/topic/`; read its `topicId`, exact
   `displayName`, aliases, status, `## Crawl Prompt`, `crawlStatus`, and `lastCrawledAt`.
2. Require an active Topic and one usable Crawl Prompt — never silently substitute a broader or
   similarly named Topic.
3. Freeze the Topic file, invocation inputs, resolved timezone, current checkpoint, search scope,
   `maxCandidates`, and starting loose-input inventory in the run directory.
4. Apply the governed `Queued` → `In progress` transitions immediately around the physical crawl. Do
   not advance `lastCrawledAt` yet.

## Step 2 — Prepare and validate the crawl prompt

1. Validate exactly one usable `## Crawl Prompt` for the topic.
2. If missing/invalid, build one from the canonical definition, aliases, scope, inclusions, and
   exclusions per the topic-crawl procedure; record its version/hash in the manifest.

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
1. Page through results until no new in-range articles remain or `maxCandidates` is reached.
2. For every returned article, record the canonical URL, NewsAPI.ai article URI, title, source,
   publication timestamp, language, and body — and **remember the canonical URLs and URIs as SET A**.
3. Canonicalize URLs (resolve redirects, strip non-identity tracking params) and deduplicate SET A by
   canonical URL and by URI.
4. SET A articles are already retrieved; carry them forward to the gates in Step 7 (no mapping
   needed).

**Gate:** a zero SET A result is valid only when the keyword search itself completed successfully — a
zero is not proof that no coverage exists (SET B may still find articles).

## Step 4 — SET B candidates: ask Claude for related URLs

1. Ask **Claude** (grounded with live web/tool access) for **all article URLs related to the topic**
   within the date range, using the Topic `displayName`, aliases, and the Crawl Prompt's inclusions/
   exclusions. Request a plain list of direct article URLs only — no homepages, index/category pages,
   snippets, or commentary.
2. Record the exact request and Claude's raw returned list in the run manifest.
3. Canonicalize every returned URL (resolve redirects, strip non-identity tracking params); drop
   obvious non-article URLs.

## Step 5 — Compute SET B = Claude URLs − SET A

1. Remove from Claude's canonicalized list every URL already present in SET A, comparing on the
   **canonical** URL (case-insensitive, trailing slash ignored, tracking params removed).
2. Deduplicate the remainder among itself. The result is **SET B**.
3. Apply `maxCandidates` to SET B if set. Record SET B and the removed-as-duplicate count.

## Step 6 — Crawl SET B: map to URI and retrieve

For each SET B URL:
1. Map it to a NewsAPI.ai URI: `POST https://eventregistry.org/api/v1/articleMapper`
   ```json
   { "articleUrl": "<canonical article URL>", "apiKey": "<runtime NEWSAPI_AI_API_KEY>" }
   ```
   Validate HTTP status, content type, and structure before reading the URI. One attempt per URL
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

## Step 7 — Gate SET A ∪ SET B (identity, in-range date, complete body)

Apply the same gates to every candidate from both sets. Accept only when:
1. its returned URL/title/source/event correspond to the discovered article;
2. its publication timestamp, in the invocation timezone, falls inside `dateStart`..`dateEnd`
   **(this date gate is essential for SET B, whose URLs are not date-bounded at discovery)**;
3. its structure is coherent and not abruptly truncated;
4. the body is non-empty source text (a character/word count alone is not proof of completeness);
   and
5. it is not already present in `Inputs/articles/` or `entities/article/` by article ID, canonical
   URL, URI, or source identity.

Drop out-of-range, hallucinated, non-article, or incomplete candidates with a recorded reason. The
surviving set is the topic's accepted articles = **SET A ∪ validated SET B**.

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

## Step 9 — Enrich and validate the frozen batch

1. Freeze a newline-delimited manifest of only the newly normalized filenames.
2. Run `scripts/enrich_radar_inputs.py` to assess existing-vocabulary tags, outlet, outlet country,
   institutional category, tone, sentiment, and event type.
3. Require the configured independent-agreement and confidence thresholds before applying
   judgment-heavy values; send disagreements/low-confidence/missing evidence to attributed review;
   apply only reviewed results.
4. Confirm completeness:
   ```bash
   python3 scripts/enrich_radar_inputs.py --input-dir Inputs/articles/<YYYY-MM> --manifest <frozen-manifest-path> --check-complete
   ```
   Process separate publication months separately when the range crosses a month boundary.

## Step 10 — Compile, cascade, and close the topic

For each affected month:
1. Dry preview: `python3 scripts/ingest_cascade.py --month <YYYY-MM> --manifest <month-manifest> --dry-run`
2. Resolve every preview error or hold the affected article.
3. Real run: the same command without `--dry-run`.
4. Confirm articles moved to `entities/article/YYYY-MM/` and that backlinks, coverage, catalogs,
   logs, and validation updated per the cascade procedure.
5. Report input/processed/created/held/failure counts, elapsed time, and average seconds per article.

Then close the topic:
- Mark the topic crawl `Complete` and advance `lastCrawledAt` **only** if SET A search, SET B
  discovery, and all required retrieval/bookkeeping succeeded (via the governed completion procedure).
- On any required-service failure, mark it `Failed`, retain all recoverable evidence, and leave
  `lastCrawledAt` unchanged.
- A zero-result topic may close complete only when both SET A search and SET B discovery were
  verified operational and the report states that zero in-range articles were found.

Do not project to UAT, run the Issue Radar, or edit Issue entities unless the invoking goal
explicitly adds that downstream work. This plan's default boundary ends at a validated Markdown
cascade.

## Step 11 — Complete the run (once per run)

1. Reconcile SET A, Claude-discovery, SET B, mapping, retrieval, normalization, enrichment, and
   cascade manifests so every candidate has exactly one terminal disposition.
2. Rebuild `entities/topic/catalog.md` from source notes.
3. Write the run receipt: selected topics, per-topic SET A / SET B / accepted / rejected / duplicate
   counts, failures, elapsed time, and average time per topic.

## Failure, retry, and resume rules

- Isolate failures by topic and by article wherever possible; one candidate's hold/rejection does not
  stop independent candidates unless it signals a systemic discovery/credential/endpoint/schema/
  provenance problem.
- Retry only the configured finite number of times with the configured backoff. Never retry
  indefinitely, and never treat a timeout as a successful zero-result crawl.
- Never advance a checkpoint from an incomplete, mismatched, or malformed provider response.
- If a run stops partway, resume from the run manifest and per-topic checkpoints (SET A captured,
  SET B computed, SET B fetched) rather than duplicating completed work.

## Stop conditions

Stop the affected stage without fabricating success when: the topic is absent/ambiguous/inactive or
lacks usable crawl instructions; a date boundary is absent/invalid; `NEWSAPI_AI_API_KEY` is
unavailable/rejected; Claude grounded discovery is unavailable when SET B is required; a response
cannot be attributed to the submitted topic/URL/URI; URL-to-URI mapping fails and approved fallback
cannot resolve it; identity/date evidence conflicts irreconcilably; a body is missing/partial and no
approved source-backed retrieval recovers it; the article already exists or conflicts with an existing
source identity; required enrichment stays invalid; the input contract / article-quality / tag / link
checks fail; or continuing would require a production write or an unauthorized schema/rule change.

## Acceptance checklist (per topic)

- [ ] Exactly one canonical Topic Entity resolved and frozen; both dates and timezone validated.
- [ ] SET A built from NewsAPI.ai keyword search; its URLs/URIs recorded, canonicalized, deduplicated.
- [ ] Claude related-URL list captured (grounded) and canonicalized.
- [ ] SET B computed as Claude URLs minus SET A (canonical dedup), then deduped by URI against SET A.
- [ ] Every SET B URL has a URI-mapping disposition; multiple URLs → one URI treated as one article.
- [ ] Every retrieved article used `article/getArticle` with `infoArticleBodyLen: -1`; key never
      persisted.
- [ ] SET A ∪ SET B passed identity, in-range date, complete-body, provenance, and duplicate gates;
      partial/missing bodies source-recovered or held (never generated); hallucinated/out-of-range
      SET B URLs dropped with reasons.
- [ ] Every accepted raw note uses the frozen input contract and plain source narrative.
- [ ] Every frozen note passed `enrich_radar_inputs.py --check-complete` after review.
- [ ] Compile/cascade validation passed for every processed month; timed receipt reports totals.
- [ ] Every candidate has one final disposition; topic status/checkpoint reflect verified completion.

## Final report

Return one run report with: topics (IDs, names, date range, timezone, run directory, final statuses);
SET A keyword queries and counts; Claude discovery request and returned-URL count; SET B size after
removing SET A and after URI dedup; NewsAPI.ai mapping attempts, unique URIs, retrievals, extraction
fallbacks, and failures; complete/partial/missing/held/normalized/enriched/cascaded counts split by
SET A vs SET B; per-month compile/cascade totals, elapsed time, and average processing time;
validation outcomes and unresolved limitations; and paths to receipts, manifests, assessments,
held-item evidence, created article notes, and affected entity notes.
