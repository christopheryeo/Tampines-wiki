# Media Scanner Workflow — Documentation

Source: [`Media Scanner Workflow - Tampines.json`](Media%20Scanner%20Workflow%20-%20Tampines.json)
Workflow name: **Media Scanner Workflow** · 27 nodes · `active: true`

## Description

The Media Scanner is an automated intake pipeline that sits in front of the Tampines Wiki and turns
a plain-language media query into filed, structured articles. A caller — a person, a scheduler, or
another workflow — sends it a topic to watch (for example, a set of keywords about Tampines,
optionally combined with AND/OR logic) together with a session ID and, if desired, the name of the
target Dropbox vault. The workflow hands that query to a Gemini-powered AI agent that has a toolbox
of scrapers wired to it. Rather than blindly scraping everything, the agent follows a deliberate
search strategy baked into its system prompt: for a simple OR-list of topics it tries them one at a
time and stops at the first that yields hits; for two AND-joined groups it pairs the terms by
position and runs every combination. As it searches, it reads each returned article and issues a
**relevance verdict** — a confidence score and a one-line reason — for every article ID,
deduplicating as it goes, and emits that verdict list as strict JSON.

The workflow then reunites those verdicts with the actual article content the agent's tools pulled
back (preserved because the agent runs with "return intermediate steps" on). If the agent found
nothing, the run short-circuits and reports an empty result. Otherwise, a code node reconstructs
each relevant news article into a standardized record — title, URL, author, published date,
carefully-separated publisher location vs. country, concepts, duplicate flags, the raw API response,
and the AI's relevance judgement — and renders it as a Markdown file with YAML frontmatter and a safe
`<articleId>-<slug>.md` filename. Those files are uploaded to `/{vault}/Inputs/articles/` in Dropbox
in throttled batches (a two-second pause between batches to stay within Dropbox's rate limits),
landing them exactly where the wiki's ingest pipeline expects raw intake. Finally the workflow
returns a completion summary — session ID, status, and article count — to whoever called it. In
effect it replaces manual news clipping with an AI relevance filter that writes straight into the
vault's intake folder. As currently wired it is news-only: the social scrapers are attached to the
agent but their results are never filed, and the news sub-workflow tool is disconnected.

## Process

**Triggers & input shaping**

1. **Webhook** (`webhook` v2.1) — exposes `POST /media-scanner` (response mode = "response node", so
   the workflow controls the final reply). The main external entry point; receives the query in the
   request body.
2. **Executed by AI Agent** (`executeWorkflowTrigger` v1.1) — alternative entry when another workflow
   calls this one as a sub-workflow, passing `query` and `sessionId`.
3. **DATA** (`code` v2) — normalises whichever trigger fired into one object:
   `{ sessionId, action:"web", chatInput: query, dropbox_root }`, defaulting `dropbox_root` to
   `"tampines-wiki"` if absent.

**AI search & classification (the agent and its sub-nodes)**

4. **AI Agent** (`langchain.agent` v3.1, Tools Agent) — the orchestrator. Reads the query, decides
   which scraper tools to call and with what terms, applies the OR/AND search strategy, judges
   relevance, deduplicates, and outputs a JSON verdict list. Runs with `returnIntermediateSteps:
   true` so raw tool results are retained.
5. **Google Gemini Chat Model** (`lmChatGoogleGemini` v1) — the LLM powering the agent (credential:
   *Google Gemini*).
6. **Simple Memory** (`memoryBufferWindow` v1.3) — short conversation buffer so the agent has context
   within a session.
7. **Structured Output Parser** (`outputParserStructured` v1.3) — forces the agent's final answer
   into the required schema (`output[]` of `articleId / relevant / relevance_confidence /
   relevance_reason`); tolerates accidental double-nesting.
8. **News Scrapper** (`httpRequestTool` v4.4) — the agent tool that queries NewsAPI.ai's
   `getArticles` endpoint (credential: *News API Key*). **This is the only source whose results are
   actually filed downstream.**
9. **Social scrapers ×9** (`httpRequestTool` v4.4, one each) — **Twitter, Instagram, Tik Tok,
   LinkedIn (profile), LinkedIn (Jobs), Reddit, Youtube, Facebook (Comments), Facebook (Posts)** —
   all call Apify actors via `run-sync-get-dataset-items`, with request bodies filled from
   `$fromAI(...)` (credential: *Apify Token*). Callable by the agent, but their output is not
   persisted by the current pipeline.
10. **Call 'News Scrapper Sub-Workflow'** (`toolWorkflow` v2.2) — a tool meant to invoke a separate
    news sub-workflow (`BTRWBlpuSGS0ozed`). **Not connected to the agent, so it never runs.**

**Branch on results**

11. **Check existing folder - Dropbox** (`httpRequest` v4.4) — lists `/{dropbox_root}/Inputs/articles`
    in Dropbox (credential: *SentientDropbox*). Passes items into the `If`; its result isn't actually
    consumed by the branch logic.
12. **If** (`if` v2.3) — tests whether `AI Agent.output` is an empty array. True (empty) → node 13;
    False (has articles) → node 14.
13. **No Articles found** (`code` v2) — returns `{ articles: [] }` and routes straight to the response.

**Compile matched articles into files**

14. **Response** (`code` v2) — the reassembly step. Extracts the raw news articles from the agent's
    `intermediateSteps` (tool `news_scrapper`), joins each AI verdict to its raw article by ID,
    quarantines verdicts with no matching source, builds a standardized article object, renders
    YAML-frontmatter Markdown, derives a `<articleId>-<slug>.md` filename, and emits each article with
    a base64 Markdown binary attached.

**Throttled upload loop**

15. **Loop Over Items** (`splitInBatches` v3, batch 10) — iterates the compiled articles in batches;
    "done" branch → node 18, "loop" branch → node 16.
16. **Wait** (`wait` v1.1, 2s) — pauses between batches to respect Dropbox rate limits.
17. **Upload a file** (`dropbox` v1) — writes each Markdown file to
    `/{dropbox_root}/Inputs/articles/{fileName}` (credential: *SentientDropbox*), then returns to the
    loop.

**Finish**

18. **Rebuild Response Items** (`code` v2) — after all uploads, builds the summary
    `{ sessionId, status:"completed", articleCount, error:null }`.
19. **Respond to Webhook** (`respondToWebhook` v1.5, `respondWith: allIncomingItems`) — returns the
    final payload to the caller: the completion summary (articles filed) or `{ articles: [] }`
    (nothing found).

## Credentials referenced (reference only — no secret values in the JSON)

| Credential | Type | Used by |
|---|---|---|
| Google Gemini | `googlePalmApi` | Chat model |
| Apify Token | `httpQueryAuth` | 10 social/media scraper tools |
| News API Key | `httpQueryAuth` | News Scrapper |
| SentientDropbox | `dropboxOAuth2Api` | Check folder, Upload a file |
| SentientDropboxv2 | `dropboxApi` | Attached to Check folder (unused) |

---

# n8n Validation Report 2026-09-10

Validated the workflow against the n8n node model referenced in
[`n8n Documentation Reference.md`](n8n%20Documentation%20Reference.md) (built-in node types, core
nodes, and cluster nodes).

## Verdict

**Structurally sound and n8n-valid**, with several logic gaps worth fixing. All 27 nodes use real
n8n node types, and the AI/cluster wiring conforms to n8n's documented root-node + sub-node model.

## What conforms (PASS)

- **AI Agent** (`agent` v3.1) is a valid root node and the modern *Tools Agent* — **not** the v1
  "agent type" node the docs flag for removal in n8n 3.0.
- Sub-nodes connect on the correct connection types: `ai_languageModel` (Gemini), `ai_memory`
  (Simple Memory), `ai_outputParser` (Structured Output Parser, with `hasOutputParser: true`), and
  `ai_tool` (the scraper tools).
- `returnIntermediateSteps: true` is set — the downstream `Response` node depends on it. Consistent.
- Webhook `responseMode: responseNode` correctly pairs with the `Respond to Webhook` node, and
  **both** terminal branches reach it exactly once.
- The `splitInBatches` loop is wired correctly (done → Rebuild; loop → Wait → Upload → back).
- The output-parser JSON schema matches exactly what the system prompt tells the agent to emit, and
  defensively tolerates double-nesting.

## Findings

### Medium

1. **Orphaned tool node.** `Call 'News Scrapper Sub-Workflow'` (`toolWorkflow`, → workflow
   `BTRWBlpuSGS0ozed`) has an **empty `ai_tool` connection**, so it never runs. News is actually
   sourced by the separate `News Scrapper` HTTP tool. **Fix:** wire it to the AI Agent or delete it.
2. **Only News Scrapper output is persisted.** The `Response` node processes only intermediate steps
   whose tool name is `news_scrapper`. The 10 social tools are connected and callable, but their
   results are **never written to files** — silently dropped. In practice this is a news-only
   pipeline with unused social tools. **Fix:** confirm intent; either handle social outputs or remove
   the unused tools.
3. **`Check existing folder - Dropbox` is unused and a failure point.** Its `list_folder` result is
   never read (the `If` branches on `AI Agent.output`, not this node). On a not-yet-created
   `Inputs/articles` path, `list_folder` returns **409 and halts the run** even when articles were
   found; `Upload a file` auto-creates parent folders anyway. **Fix:** remove it, or set
   `continueOnFail` / actually consume its output for dedup.

### Low

4. **Inconsistent response payloads.** The "no articles" branch returns `{articles: []}`; the success
   branch returns `{sessionId, status, articleCount, error}`. A caller cannot parse one shape.
5. **`$fromAI` key mismatch in scraper bodies.** e.g. the Twitter tool guards on
   `$fromAI('searchTerms')` but inserts `$fromAI('keywords')`, and its description names `keywords`.
   Guard key and inserted key differ, so the branch can misfire. Worth a consistency pass across all
   tool bodies.
6. **Brittle coupling / stray credential.** `Response` hard-codes the tool-name string
   `news_scrapper`; renaming the `News Scrapper` node silently breaks file output. `Check existing
   folder - Dropbox` also carries a second, unused Dropbox credential (`SentientDropboxv2`).

## Method / limitation

Node types and the cluster-node architecture were verified against the n8n docs. This pass did **not**
exhaustively cross-check every parameter of every node against its individual reference page (the
automated docs fetch was too coarse for that). A deeper per-node parameter audit can be done on request.
