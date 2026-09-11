# Media Scanner Workflow — Documentation

Source: [`Media Scanner Workflow - News Only.json`](Media%20Scanner%20Workflow%20-%20News%20Only.json)
Workflow name: **Media Scanner Workflow - News Only** · 20 nodes · `active: false`

> This documents the current **News Only** version. It supersedes the original 27-node
> `Media Scanner Workflow - Tampines.json` (which also carried social-media scrapers and has been
> removed). The n8n Validation Report below is updated to **v2** for this version.

## Description

The Media Scanner is an automated intake pipeline that sits in front of the Tampines Wiki and turns
a plain-language media query into filed, structured **news** articles. A caller — a person, a
scheduler, or another workflow — sends it a topic to watch (optionally combined with AND/OR logic)
together with a session ID and, if desired, the name of the target Dropbox vault. The workflow hands
that query to a Gemini-powered AI agent that runs a two-source discovery procedure per topic:

1. **SET A** — call NewsAPI.ai with the topic keyword (keyword search).
2. **SET B** — ask Gemini (with live Google-Search grounding) for a second, independent list of
   candidate article URLs on the same topic.
3. **SET C = B − A** — drop any SET B URL already present in SET A (case-insensitive, trailing-slash
   tolerant).
4. For up to three SET C URLs, resolve each URL to an Event Registry URI and fetch the full article.
5. The working pool for the topic is **A ∪ C**; the agent classifies every article for relevance.

As it works, the agent issues a **relevance verdict** — a confidence score and a one-line reason —
for every article ID, deduplicating by ID. The workflow then reunites those verdicts with the actual
article content the tools pulled back (preserved because the agent runs with "return intermediate
steps" on) from **both** the keyword search and the fetch-by-URI tool. If nothing relevant was found,
the run short-circuits and reports an empty result. Otherwise a code node reconstructs each relevant
article into a standardized record — title, URL, author, published date, carefully-separated
publisher location vs. country, concepts, duplicate flags, the raw API response, and the AI's
verdict — and renders it as a Markdown file with YAML frontmatter and a safe `<articleId>-<slug>.md`
filename. Files are uploaded to `/{vault}/Inputs/articles/` in Dropbox in throttled batches (a
two-second pause between batches to respect rate limits), landing exactly where the wiki's ingest
pipeline expects raw intake. Finally the workflow returns a completion summary — session ID, status,
and article count — to whoever called it. In effect it replaces manual news clipping with a
keyword + LLM-discovery union and an AI relevance filter that writes straight into the vault's
intake folder.

## Process

**Triggers & input shaping**

1. **Webhook** (`webhook` v2.1) — exposes `POST /media-scanner` (response mode = "response node").
   The main external entry point; receives the query in the request body.
2. **Executed by AI Agent** (`executeWorkflowTrigger` v1.1) — alternative entry when another workflow
   calls this one as a sub-workflow, passing `query` and `sessionId`.
3. **DATA** (`code` v2) — normalises whichever trigger fired into one object:
   `{ sessionId, action:"web", chatInput: query, dropbox_root }`, defaulting `dropbox_root` to
   `"tampines-wiki"` if absent.

**AI search, discovery & classification (the agent and its sub-nodes)**

4. **AI Agent** (`langchain.agent` v3.1, Tools Agent) — the orchestrator. Per topic it runs the
   SET A/B/C procedure (prompt-driven, see below), pools A ∪ C, judges relevance, deduplicates, and
   outputs a JSON verdict list. Runs with `returnIntermediateSteps: true` so raw tool results are
   retained. Hard budget: 10 iterations.
5. **Google Gemini Chat Model** (`lmChatGoogleGemini` v1, `models/gemini-3.7-flash`) — the LLM
   powering the agent (credential: *Google Gemini Api account*).
6. **Simple Memory** (`memoryBufferWindow` v1.3) — short conversation buffer within a session.
7. **Structured Output Parser** (`outputParserStructured` v1.3) — forces the agent's final answer
   into the required schema (`output[]` of `articleId / relevant / relevance_confidence /
   relevance_reason`).
8. **News Scrapper** (`httpRequestTool` v4.4) — **SET A**: NewsAPI.ai `getArticles` by a single
   keyword (≤100 recent English news articles, full body). Credential: *News API Key*.
9. **Gemini URL Search** (`httpRequestTool` v4.4) — **SET B**: calls Gemini (`gemini-2.5-flash`) with
   Google-Search grounding and asks for a raw JSON array of candidate article URLs. Credential:
   *Google Gemini Api account* (predefined `googlePalmApi`).
10. **NewsAPI - URL to URI Mapper** (`httpRequestTool` v4.4) — **SET C step 1**: `articleMapper`
    converts a SET C URL into an Event Registry article URI. Credential: *News API Key*.
11. **NewsAPI - Get Article by URI** (`httpRequestTool` v4.4) — **SET C step 2**: `getArticle`
    fetches the full article for a URI, to add to the working pool. Credential: *News API Key*.

> **Agent procedure per topic (from the system prompt):** call News Scrapper (SET A) → call Gemini
> URL Search (SET B) → compute SET C = B − A → for at most 3 SET C URLs, map to URI then fetch →
> classify relevance over A ∪ C. It also carries the earlier topic-parsing rules: **Case A** (OR-list)
> tries topics one at a time and stops at the first with hits; **Case B** (two AND-joined groups)
> pairs terms by position and runs every pair.

**Branch on results**

12. **Check existing folder - Dropbox** (`httpRequest` v4.4) — lists `/{dropbox_root}/Inputs/articles`
    (credential: *Dropbox account*). Passes items into the `If`; its result isn't consumed by the
    branch logic.
13. **If** (`if` v2.3) — tests whether `AI Agent.output` is an empty array. True (empty) → node 14;
    False (has articles) → node 15.
14. **No Articles found** (`code` v2) — returns `{ articles: [] }` and routes to the response.

**Compile matched articles into files**

15. **Response** (`code` v2) — extracts raw articles from the agent's `intermediateSteps` for **both**
    `news_scrapper` (SET A) and `newsapi_-_get_article_by_uri` (SET C), keyed by URI; joins each AI
    verdict to its raw article by ID; quarantines verdicts with no matching raw article; renders
    YAML-frontmatter Markdown; derives an `<articleId>-<slug>.md` filename; emits each article with a
    base64 Markdown binary attached.

**Throttled upload loop**

16. **Loop Over Items** (`splitInBatches` v3, batch 10) — "done" → node 19, "loop" → node 17.
17. **Wait** (`wait` v1.1, 2s) — pauses between batches to respect Dropbox rate limits.
18. **Upload a file** (`dropbox` v1) — writes each Markdown file to
    `/{dropbox_root}/Inputs/articles/{fileName}` (credential: *Dropbox account*), then returns to the
    loop.

**Finish**

19. **Rebuild Response Items** (`code` v2) — builds the summary
    `{ sessionId, status:"completed", articleCount, error:null }`.
20. **Respond to Webhook** (`respondToWebhook` v1.5) — returns the final payload: the completion
    summary (articles filed) or `{ articles: [] }` (nothing found).

## Credentials referenced (reference only — no secret values in the JSON)

| Credential | Type | Used by |
|---|---|---|
| Google Gemini Api account | `googlePalmApi` | Chat model; Gemini URL Search |
| News API Key | `httpQueryAuth` | News Scrapper, URL to URI Mapper, Get Article by URI (and, stray/unused, on Gemini URL Search) |
| Dropbox account | `dropboxOAuth2Api` | Check folder, Upload a file |

---

# n8n Validation Report 2026-09-10 (v2 — News Only)

Validates `Media Scanner Workflow - News Only.json` against the n8n node model referenced in
[`n8n Documentation Reference.md`](n8n%20Documentation%20Reference.md), the intended SET A/B/C design,
and the findings from the v1 review of the original 27-node workflow.

## Verdict

The core design gap is **closed**: the workflow now implements the keyword + Gemini-discovery union
with per-URL backfill (SET A/B/C), drops the unused social scrapers and the orphan sub-workflow tool,
and the quarantine no longer discards discovered articles. Most v1 findings are resolved. A few
remain, plus several new robustness items to address before activation (the workflow is
`active: false`).

## Against the intended SET A / B / C design

| Intended | New (News Only) workflow |
|---|---|
| SET A — NewsAPI keyword search | ✅ Present (News Scrapper). |
| SET B — Gemini returns article URLs | ✅ Added — Gemini URL Search (Google-Search grounded). |
| SET C = B − A | ✅ Specified in the prompt (dedup vs SET A URLs). Agent-driven, not deterministic code. |
| Fetch each SET C URL | ✅ Added — URL→URI Mapper then Get Article by URI (capped at 3/topic). |
| Write A ∪ C | ✅ Response pools both sources. |
| Remove the quarantine-discard | ✅ Fixed — quarantine now only flags truly-missing articles. |

## Against the v1 validation findings

| Finding | Status |
|---|---|
| M1 — orphaned sub-workflow tool | ✅ Removed. |
| M2 — social scraper outputs never persisted | ✅ Resolved (social tools removed; news-only). |
| M3 — "Check existing folder" unused + 409-halts on missing folder | ❌ Not addressed. |
| L4 — inconsistent response payloads | ❌ Not addressed. |
| L5 — `$fromAI` guard/insert key mismatch | ✅ Resolved (those tools removed). |
| L6 — brittle tool-name coupling + stray Dropbox cred | ⚠️ Partial — stray cred gone; tool-name coupling remains (see N1). |

## New issues in this version

- **N1 (Medium)** — the `Response` node keys off the exact sanitised tool names `news_scrapper` and
  `newsapi_-_get_article_by_uri`. If n8n sanitises "NewsAPI - Get Article by URI" to anything else,
  **every SET C article silently falls into quarantine** and is never filed. Needs a live test.
- **N2 (Medium)** — 10-iteration budget vs. per-topic cost. One topic can need up to 8 calls
  (News Scrapper + Gemini + up to 3 Mapper + up to 3 Get-Article), and the "batch in a single step"
  instruction can't run — Mapper and Get-Article each take a single `$fromAI` value. Multi-topic
  OR-lists will overrun the budget and truncate.
- **N3 (Low–Med)** — Gemini URL Search returns the full `generateContent` envelope, not a clean URL
  array; the agent must extract `candidates[0].content.parts[0].text` and JSON-parse it. Fragile.
- **N4 (Low)** — Gemini URL Search has a stray, unused *News API Key* credential attached (it uses
  the Gemini credential). Remove it.
- **N5 (Low)** — model mismatch: chat model is `models/gemini-3.7-flash`, the URL-search tool uses
  `gemini-2.5-flash`. Confirm the intended model and align.
- **Prompt typo (Case B)** — "2nd term of Group B with 2nd term of Group B" should read Group A with
  Group B.

## Still open from v1
- **M3** — `Check existing folder - Dropbox` still errors (409) and halts the run if the folder
  doesn't exist, and its result isn't used anyway. Add error handling / `continueOnFail`, or drop it
  (the upload auto-creates the folder).
- **L4** — the two response branches still return different shapes (`{articles:[]}` vs
  `{sessionId, status, articleCount}`). Make them consistent.

## Open design decision
- **Case A (OR-list)** still stops at the first topic that returns hits and silently skips the rest —
  for monitoring several distinct topics this under-collects, and each skipped topic also skips its
  A/B/C discovery. Decide whether to run all topics and dedup (like Case B), or keep early-stop on the
  basis that an OR-list is only ever synonyms of one topic.

## Method / limitation
Node types and the cluster-node architecture were verified against the n8n docs. This pass did not
exhaustively cross-check every parameter of every node against its individual reference page, and the
SET A/B/C set logic is agent-driven (prompt-enforced), so its correctness depends on the LLM
following the procedure — worth a live end-to-end test before activation.
