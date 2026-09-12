---
type: plan
name: topic-date-range-crawl
status: ready
created: 2026-09-06
owner: ChatGPT Codex
---

# Topic Date-Range Crawl Plan

## Purpose

Run a reusable, governed crawl for one Topic Entity across one inclusive publication-date range.
The plan discovers any number of candidate article URLs, maps each unique URL to a NewsAPI.ai
article URI, retrieves the article by that URI, normalizes complete source-backed results into the
vault's raw article contract, enriches them, and compiles/cascades the accepted batch.

The plan contains no fixed issue, topic, query, or date. Each invocation supplies those values.

## Required invocation inputs

The invoking Goal must provide only:

1. `topic` — one Topic Entity ID, exact display name, wikilink, or unambiguous entity path;
2. `dateStart` — inclusive `YYYY-MM-DD` publication-date boundary; and
3. `dateEnd` — inclusive `YYYY-MM-DD` publication-date boundary.

Optional inputs:

- `timezone` — defaults to `Asia/Singapore`;
- `maxCandidates` — a safety ceiling on unique canonical URLs;
- `languages` or named source constraints; and
- `runLabel` — a short run identifier.

Stop before crawling if the Topic cannot be resolved to exactly one canonical Topic Entity, either
date is absent or invalid, `dateStart` is later than `dateEnd`, or the requested scope conflicts
with the Topic's stored crawl instructions.

## Goal prompt

Use this minimal prompt to execute the plan without duplicating its instructions:

> Execute `scripts/topic_crawl_plan.md` with topic `<TOPIC>`, dateStart `<YYYY-MM-DD>`, and dateEnd
> `<YYYY-MM-DD>`. Follow the plan through completion.

Add any optional invocation inputs from the preceding section to the same prompt only when needed.

## Governing rules

- Follow `README.md`, `scripts/entity_cascade_procedure.md`, and
  `scripts/enriched_radar_load_procedure.md` where applicable.
- Markdown notes are the source of truth. Databases, indexes, catalogs, dashboards, and radar
  outputs are derived surfaces.
- Preserve provenance from discovery through cascade. Do not enrich article claims or complete
  missing article text from model background knowledge.
- Treat credentials as runtime-only secrets. Read the NewsAPI.ai key from
  `NEWSAPI_AI_API_KEY`; never persist the key, credential-bearing headers, or credential-bearing
  URLs in the repository, article notes, receipts, manifests, or logs.
- Treat URL discovery, NewsAPI.ai URI mapping, body retrieval, normalization, enrichment, and
  compile/cascade as separate checkpoints.
- Never overwrite an existing raw or compiled article note.
- Time every compile/cascade run and report elapsed time, processed count, and average processing
  time per article. If zero articles are processed, report zero without a misleading average.

## Completion definition

The run is complete when every discovered candidate has a recorded disposition and every accepted
article has either:

1. passed URL-to-URI mapping, URI-based retrieval, completeness, identity, date, deduplication,
   normalization, enrichment, compile, cascade, and validation; or
2. been rejected, deduplicated, or held with a specific evidence-backed reason.

A zero-result run is valid only after all configured discovery paths complete successfully. A zero
from one crawler or endpoint is not proof that no public articles exist.

## Stage 1 — Resolve and freeze the Topic

1. Resolve `topic` to exactly one file under `entities/topic/`.
2. Read its canonical `topicId`, exact `displayName`, aliases, status, `## Crawl Prompt`,
   `crawlStatus`, and `lastCrawledAt`.
3. Require an active Topic and one usable Crawl Prompt. Do not silently substitute a broader or
   similarly named classification Topic.
4. Create a run directory under `runs/YYYY-MM-DD/artifacts/topic-crawls/` using the Topic ID,
   requested date range, and a unique timestamp or suffix.
5. Freeze the Topic file, invocation inputs, resolved timezone, current crawl checkpoint, search
   scope, maximum-candidate limit, and starting loose-input inventory in the run directory.
6. Apply the governed `Queued` and `In progress` Topic transitions immediately around the physical
   crawl. Do not advance `lastCrawledAt` until all required crawl stages succeed.

## Stage 2 — Discover candidate article URLs

Use both the Topic Entity and its Crawl Prompt to construct multiple search variants rather than
depending on one literal query.

1. Search the public web using:
   - the exact Topic `displayName`;
   - meaningful aliases and named entities recorded in the Topic;
   - required inclusions and exclusions from `## Crawl Prompt`; and
   - the inclusive date range and requested timezone.
2. Where configured, call the development media-scanner webhook once for this Topic using:

   ```json
   {
     "sessionId": "topic-crawl-<topicId>-<unique-run-suffix>",
     "query": "<exact Topic displayName>\n\nOnly include articles published between <dateStart> and <dateEnd> (<timezone>)."
   }
   ```

3. Treat webhook output as an additional candidate source. Until it passes a known-positive test,
   do not treat a zero webhook result as proof of zero coverage.
4. For every search hit, record the search provider, exact query, result rank, discovered URL,
   apparent title, apparent publisher, apparent publication timestamp, Topic ID, and discovery
   time.
5. Follow only public article-result URLs. Search pages, topic indexes, category pages, homepages,
   snippets, social posts without an underlying article, and non-article documents are discovery
   evidence only.
6. Resolve redirects, remove non-identity tracking parameters, and retain both discovered and
   canonical URLs.
7. Deduplicate canonical URLs before consuming NewsAPI.ai calls. Continue through available result
   pages until there are no new in-range URLs or `maxCandidates` is reached.

## Stage 3 — Map every unique URL to a NewsAPI.ai URI

For each unique canonical URL, call:

`POST https://eventregistry.org/api/v1/articleMapper`

with a JSON body assembled programmatically:

```json
{
  "articleUrl": "<canonical article URL>",
  "apiKey": "<runtime NEWSAPI_AI_API_KEY>"
}
```

Rules:

1. Make one mapping attempt per canonical URL unless a retry is justified by a transient transport
   or server error.
2. Validate the HTTP status, response content type, and response structure before reading the URI.
3. Record the returned NewsAPI.ai article URI against the canonical URL in the mapping manifest.
4. Deduplicate again by NewsAPI.ai article URI. Several discovered URLs that map to one URI are one
   article, not several articles.
5. A URL that cannot be mapped may be checked with NewsAPI.ai's direct URL extraction endpoint to
   diagnose indexing or canonicalization, but it must not be described as URI-retrieved unless a
   URI is actually obtained. Hold or reject it under the explicit fallback rules below.

## Stage 4 — Retrieve each mapped article by NewsAPI.ai URI

For every unique mapped URI, call:

`POST https://eventregistry.org/api/v1/article/getArticle`

with:

```json
{
  "action": "getArticle",
  "articleUri": "<NewsAPI.ai article URI>",
  "infoArticleBodyLen": -1,
  "resultType": "info",
  "apiKey": "<runtime NEWSAPI_AI_API_KEY>"
}
```

This URI-based call is the primary article retrieval path. `infoArticleBodyLen: -1` requests the
maximum body stored by NewsAPI.ai, but does not by itself prove that the publisher's complete body
was captured.

For each response, safely record:

- canonical URL and all mapped discovered URLs;
- NewsAPI.ai article URI;
- endpoint, request time, HTTP status, content type, and retrieval disposition;
- returned title, outlet/source, publication timestamp, language, and duplicate status;
- body character count, word count, paragraph count, and SHA-256 hash; and
- whether identity, date, and completeness gates passed.

Never retain the API key or sensitive request headers in these artifacts.

## Stage 5 — Apply identity, date, and complete-body gates

An article is eligible only when:

1. its returned URL, title, source, and publication event correspond to the discovered article;
2. its source publication timestamp, converted to the invocation timezone, falls inside the
   inclusive `dateStart` to `dateEnd` range;
3. its lead and paragraph structure are coherent and its ending is plausible rather than abruptly
   truncated;
4. the body is non-empty source text; and
5. it is not already present in `Inputs/articles/` or `entities/article/` by article ID, canonical
   URL, NewsAPI.ai URI in the run evidence, or source identity.

A character or word count alone is not evidence that a body is complete.

If URI retrieval is missing or apparently partial, call
`POST https://analytics.eventregistry.org/api/v1/extractArticleInfo` with the canonical `url` and
the runtime API key for comparison or recovery. If that still does not produce a complete body,
use an approved direct publisher-URL retrieval method and repeat the identity and completeness
checks. Record the exact retrieval route and outcome.

If a complete source-backed body remains unavailable, hold the candidate. Never synthesize or
infer omitted text, and never pass a partial body downstream as a complete article.

## Stage 6 — Normalize each accepted article

Write each accepted result to `Inputs/articles/YYYY-MM/`, where `YYYY-MM` comes from its verified
publication date in the invocation timezone.

Use:

- `articleId`: `crawl-` plus the lowercase SHA-256 digest of the canonical URL; and
- filename: `<articleId>-<slugified-title>.md`.

Each raw note must use the frozen intake contract:

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

Provider IDs, discovery queries, mapping records, retrieval methods, hashes, and completeness
decisions belong in the run manifests, not in new frontmatter fields. Serialize YAML safely. A
normalized note is staged, not cascade-ready, until all required enrichment values are reviewed.

## Stage 7 — Enrich and validate the frozen batch

1. Freeze a newline-delimited manifest of only the newly normalized filenames.
2. Run `scripts/enrich_radar_inputs.py` against that manifest to assess existing-vocabulary tags,
   outlet, outlet country, institutional category, tone, sentiment, and event type.
3. Require the configured independent classification agreement and confidence threshold before
   applying judgment-heavy values.
4. Send disagreements, low-confidence results, missing evidence, and invalid values to attributed
   review.
5. Apply only reviewed results to the raw notes.
6. Run:

   ```bash
   python3 scripts/enrich_radar_inputs.py \
     --input-dir Inputs/articles/<YYYY-MM> \
     --manifest <frozen-manifest-path> \
     --check-complete
   ```

7. Require every selected raw note to pass the shared completeness contract before compile/cascade.
   Process separate publication months separately when the requested date range crosses a month
   boundary.

## Stage 8 — Compile and cascade

For each affected month:

1. Run a dry preview against the frozen month-specific manifest:

   ```bash
   python3 scripts/ingest_cascade.py \
     --month <YYYY-MM> \
     --manifest <month-manifest-path> \
     --dry-run
   ```

2. Resolve every preview error or place the affected article on hold.
3. Run the same command without `--dry-run` for the approved manifest.
4. Confirm that successful articles moved to `entities/article/YYYY-MM/` and that all required
   entity backlinks, coverage data, generated catalogs, logs, and validation results were updated
   according to the cascade procedure.
5. Report input count, processed count, created count, held count, failure count, total elapsed
   time, and average seconds per processed article from the timed receipt.

Do not project to UAT, run the Issue Radar, or edit Issue entities unless the invoking Goal
explicitly adds that downstream work. This generic plan's default boundary ends with a validated
Markdown cascade.

## Stage 9 — Close the Topic crawl

1. Reconcile the URL-discovery, URI-mapping, retrieval, normalization, enrichment, and cascade
   manifests so every candidate has exactly one terminal disposition.
2. Mark the Topic crawl `Complete` and advance `lastCrawledAt` only if all required discovery paths
   and bookkeeping succeeded.
3. If a required service failed, mark the Topic crawl `Failed`, retain all recoverable evidence,
   and leave `lastCrawledAt` unchanged.
4. A successful zero-result run may close as complete only when the discovery paths themselves were
   verified operational and the final report explicitly states that zero in-range candidates were
   found.

## Acceptance checklist

- [ ] Exactly one canonical Topic Entity was resolved and frozen.
- [ ] Both inclusive dates and the timezone were validated.
- [ ] All public-search and configured crawler queries are recorded.
- [ ] All candidate URLs are canonicalized and deduplicated.
- [ ] Every unique URL has a NewsAPI.ai URI-mapping disposition.
- [ ] Every accepted URI was retrieved through `article/getArticle` with
      `infoArticleBodyLen: -1`.
- [ ] Multiple URLs mapping to one URI are treated as one article.
- [ ] The API key was obtained at runtime and never persisted.
- [ ] Every accepted article passed identity, in-range date, complete-body, provenance, and
      duplicate gates.
- [ ] Missing or partial bodies were recovered from a source-backed route or held without generated
      completion.
- [ ] Every accepted raw note uses the frozen input contract and plain source narrative.
- [ ] Every frozen raw note passed `enrich_radar_inputs.py --check-complete` after review.
- [ ] Compile/cascade validation passed for every processed month.
- [ ] The timed receipt reports totals, elapsed time, and average processing time where applicable.
- [ ] Every discovered candidate has one final disposition.
- [ ] Topic status and checkpoint reflect verified completion rather than request submission.

## Stop conditions

Stop the affected stage without fabricating success when:

- the Topic is absent, ambiguous, inactive, or lacks usable crawl instructions;
- a date boundary is absent or invalid;
- `NEWSAPI_AI_API_KEY` is unavailable or rejected;
- a discovery or retrieval response cannot be attributed to the submitted Topic, URL, or URI;
- URL-to-URI mapping fails and approved fallback handling cannot resolve it;
- returned identity or publication-date evidence conflicts and cannot be reconciled;
- a body is missing or partial and no approved source-backed retrieval can recover it;
- the article already exists or conflicts with an existing source identity;
- required enrichment fields remain invalid or unresolved;
- the frozen input contract, article-quality checks, tag checks, or link checks fail; or
- continuing would require a production write or an unauthorized schema/rule change.

One candidate's rejection or hold does not stop independent candidates unless the failure indicates
a systemic discovery, credential, endpoint, schema, or provenance problem.

## Final report

Return one run report containing:

1. Topic ID, display name, date range, timezone, run directory, and final Topic crawl status;
2. discovery queries and counts by provider;
3. URLs found, canonicalized, deduplicated, rejected, and admitted;
4. NewsAPI.ai mapping attempts, unique URIs, URI retrievals, extraction fallbacks, and failures;
5. complete, partial, missing, held, normalized, enriched, and cascaded article counts;
6. per-month compile/cascade totals, elapsed time, and average processing time;
7. validation outcomes and any unresolved limitations; and
8. paths to receipts, manifests, assessments, held-item evidence, created article notes, and
   affected entity notes.
