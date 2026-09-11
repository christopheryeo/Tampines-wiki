# Media Scanner Workflow — Documentation

Source: [`Media Scanner Workflow - News Only.json`](Media%20Scanner%20Workflow%20-%20News%20Only.json)
Workflow name: **Media Scanner Workflow - News Only** · 22 nodes · `active: false`

> This documents the current **News Only** version. It supersedes the original 27-node
> `Media Scanner Workflow - Tampines.json` (which also carried social-media scrapers and has been
> removed). The n8n Validation Report below is at **v3**.

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
pipeline expects raw intake. Before uploading, the workflow checks the target folder exists and
returns a graceful error response if it does not. Finally it returns a completion summary — session
ID, status, and article count — to whoever called it. In effect it replaces manual news clipping with
a keyword + LLM-discovery union and an AI relevance filter that writes straight into the vault's
intake folder.

## Process

**Triggers & input shaping**

1. **Webhook** (`webhook` v2.1) — `POST /media-scanner` (response mode = "response node"). Main entry.
2. **Executed by AI Agent** (`executeWorkflowTrigger` v1.1) — sub-workflow entry (`query`, `sessionId`).
3. **DATA** (`code` v2) — normalises input into `{ sessionId, action:"web", chatInput, dropbox_root }`,
   defaulting `dropbox_root` to `"tampines-wiki"`.

**AI search, discovery & classification (agent + sub-nodes)**

4. **AI Agent** (`langchain.agent` v3.1, Tools Agent) — orchestrates the SET A/B/C procedure per topic
   (prompt-driven), pools A ∪ C, classifies relevance, outputs verdict JSON. `returnIntermediateSteps:
   true`. Hard budget: 40 iterations, with documented per-topic cost (~8 calls) and graceful early
   stop when low.
5. **Google Gemini Chat Model** (`lmChatGoogleGemini` v1, `models/gemini-3.7-flash`) — agent LLM
   (credential: *Google Gemini Api account*).
6. **Simple Memory** (`memoryBufferWindow` v1.3) — session buffer.
7. **Structured Output Parser** (`outputParserStructured` v1.3) — enforces the `output[]` schema.
8. **News Scrapper** (`httpRequestTool` v4.4) — **SET A**: NewsAPI.ai `getArticles` by keyword
   (≤100 English news, full body). Credential: *News API Key*.
9. **Gemini URL Search** (`httpRequestTool` v4.4) — **SET B**: Gemini (`gemini-3.7-flash`) with
   Google-Search grounding returns candidate article URLs. Credential: *Google Gemini Api account*.
10. **NewsAPI - URL to URI Mapper** (`httpRequestTool` v4.4) — **SET C step 1**: `articleMapper`
    URL → Event Registry URI. Credential: *News API Key*.
11. **NewsAPI - Get Article by URI** (`httpRequestTool` v4.4) — **SET C step 2**: `getArticle` fetches
    the full article by URI. Credential: *News API Key*.

> **Agent procedure per topic:** News Scrapper (SET A) → Gemini URL Search (SET B) → SET C = B − A →
> for ≤3 SET C URLs, map to URI then fetch → classify A ∪ C. Topic-parsing: **Case A** (OR-list) tries
> topics one at a time and stops at the first with hits; **Case B** (AND-joined groups) pairs terms by
> position and runs every pair.

**Folder pre-check (graceful)**

12. **Check existing folder - Dropbox** (`httpRequest` v4.4, `onError: continueErrorOutput`) — lists
    `/{dropbox_root}/Inputs/articles`. Success → node 15; error → node 13.
13. **Is Folder Missing?** (`if` v2.2) — tests the error for a Dropbox `path/not_found` shape. True →
    node 14; false (other error) → node 15.
14. **Build Folder Missing Error** (`code` v2) — returns a graceful error payload → Respond to Webhook.

**Branch on results**

15. **If** (`if` v2.3) — is `AI Agent.output` empty? True → node 16; False → node 17.
16. **No Articles found** (`code` v2) — returns the `no_articles` payload → Respond to Webhook.

**Compile matched articles into files**

17. **Response** (`code` v2) — extracts raw articles from the agent's `intermediateSteps` for **both**
    News Scrapper (SET A) and Get Article by URI (SET C) — matched via a `normalizeToolName()` helper —
    joins each AI verdict by ID, quarantines verdicts with no matching raw article, renders
    YAML-frontmatter Markdown, derives `<articleId>-<slug>.md`, and attaches a base64 Markdown binary.

**Throttled upload loop**

18. **Loop Over Items** (`splitInBatches` v3, batch 10) — "done" → node 21, "loop" → node 19.
19. **Wait** (`wait` v1.1, 2s) — inter-batch pause for Dropbox rate limits.
20. **Upload a file** (`dropbox` v1) — writes to `/{dropbox_root}/Inputs/articles/{fileName}`, back to
    the loop.

**Finish**

21. **Rebuild Response Items** (`code` v2) — builds the `completed` summary payload.
22. **Respond to Webhook** (`respondToWebhook` v1.5) — returns the final payload. All terminal branches
    (`no_articles`, `completed`, `error`) share one schema: `{ sessionId, status, articleCount,
    articles, error }`.

## Credentials referenced (reference only — no secret values in the JSON)

| Credential | Type | Used by |
|---|---|---|
| Google Gemini Api account | `googlePalmApi` | Chat model; Gemini URL Search |
| News API Key | `httpQueryAuth` | News Scrapper, URL to URI Mapper, Get Article by URI |
| Dropbox account | `dropboxOAuth2Api` | Check folder, Upload a file |

---

# n8n Validation Report 2026-09-11 (v3 — News Only)

Validates `Media Scanner Workflow - News Only.json` (22-node revision) against the n8n node model in
[`n8n Documentation Reference.md`](n8n%20Documentation%20Reference.md), the intended SET A/B/C design,
and the v1/v2 findings.

## Verdict

**Production-candidate.** Every actionable v1 and v2 finding is resolved except the Case A early-stop,
which is a design decision (not a defect), plus a few items to confirm on a live run. The workflow is
still `active: false`.

## Against the intended SET A / B / C design

| Intended | Status |
|---|---|
| SET A — NewsAPI keyword search | ✅ News Scrapper. |
| SET B — Gemini returns article URLs | ✅ Gemini URL Search (Google-Search grounded). |
| SET C = B − A | ✅ Prompt-driven dedup vs SET A URLs. |
| Fetch each SET C URL | ✅ URL→URI Mapper + Get Article by URI (≤3/topic). |
| Write A ∪ C | ✅ Response pools both sources. |
| No quarantine-discard | ✅ Quarantine only flags truly-missing articles. |

## v1 + v2 findings — status

| Finding | Status |
|---|---|
| M1 orphaned sub-workflow tool | ✅ Removed. |
| M2 social outputs never persisted | ✅ Resolved (news-only). |
| M3 Dropbox 409 halt on missing folder | ✅ **Fixed** — `onError: continueErrorOutput` → Is Folder Missing? → graceful error response. |
| L4 inconsistent response payloads | ✅ **Fixed** — all branches share `{sessionId, status, articleCount, articles, error}`. |
| L5 `$fromAI` key mismatch | ✅ Resolved. |
| L6 tool-name coupling + stray Dropbox cred | ✅ Resolved. |
| N1 brittle tool-name matching | ✅ **Fixed** — `normalizeToolName()` strips non-alphanumerics on both sides. |
| N2 iteration budget too small | ✅ **Fixed** — budget 40, realistic per-topic cost documented. |
| N3 Gemini returns full envelope | ⚠️ Partial — prompt tightened (no fences/commentary); agent still extracts from the envelope. |
| N4 stray News-API cred on Gemini tool | ✅ Removed. |
| N5 model mismatch | ✅ Aligned — both use `gemini-3.7-flash`. |
| Case B typo | ✅ Fixed. |

## Remaining items

1. **Open design decision — Case A (OR-list) still stops at the first topic with hits.** Decide: run
   all topics and dedup (comprehensive monitoring), or keep early-stop (OR-list = synonyms of one
   topic).
2. **Confirm `gemini-3.7-flash` is a real/available model** — both the chat model and the URL-search
   tool now depend on it; a wrong name fails both.
3. **Confirm the folder-missing detector** — `Is Folder Missing?` matches the Dropbox error shape
   `path/not_found`. If it doesn't match, a truly-missing folder falls through to the normal path
   (harmless — the upload auto-creates the folder — the graceful message just won't fire).
4. **N3 (optional)** — normalise Gemini's output to a clean URL array before it reaches the agent.
5. **Live end-to-end test** — the SET A/B/C logic is agent/prompt-driven, so a real run is the only
   true proof it executes the procedure.

## Method / limitation
Node types and the cluster-node architecture were verified against the n8n docs. This pass did not
exhaustively cross-check every parameter of every node against its individual reference page, and the
SET A/B/C set logic is prompt-enforced (agent-driven), so a live end-to-end test remains the
definitive check before activation.
