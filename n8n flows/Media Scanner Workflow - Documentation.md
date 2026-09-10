# Media Scanner Workflow — Documentation

Source: [`Media Scanner Workflow - Tampines.json`](Media%20Scanner%20Workflow%20-%20Tampines.json)
Workflow name: **Media Scanner Workflow** · 27 nodes · `active: true`

## Purpose

An n8n workflow that takes a media-monitoring query, uses an AI agent to search news (and,
optionally, social) sources for relevant articles, classifies each for relevance, compiles the
matches into Markdown notes with YAML frontmatter, and uploads them to Dropbox under the target
vault's `Inputs/articles/` folder — the intake path the Tampines Wiki ingests from.

## Entry points

The workflow has two triggers, both feeding the `DATA` node:

| Trigger | Type | Notes |
|---|---|---|
| **Webhook** | `n8n-nodes-base.webhook` (v2.1) | `POST /media-scanner`, `responseMode: responseNode`. The primary external entry point. |
| **Executed by AI Agent** | `n8n-nodes-base.executeWorkflowTrigger` (v1.1) | Lets another workflow call this one as a sub-workflow, passing `query` and `sessionId`. |

`DATA` (`code` v2) normalises either input into `{ sessionId, action: "web", chatInput: query,
dropbox_root }`, defaulting `dropbox_root` to `"tampines-wiki"` when not supplied.

## AI classification stage

`DATA` → **AI Agent** (`@n8n/n8n-nodes-langchain.agent` v3.1, Tools Agent).

The agent is configured with `returnIntermediateSteps: true` and `hasOutputParser: true`, and a
system prompt that instructs it to: try topics one at a time (OR-lists) or as positional AND-pairs;
deduplicate by `articleId`; and emit **raw JSON only** in the shape
`{ "output": [ { articleId, relevant, relevance_confidence, relevance_reason } ] }` (or `{"output": []}`
when nothing relevant is found).

Attached sub-nodes:

| Sub-node | Type | Connection | Role |
|---|---|---|---|
| Google Gemini Chat Model | `lmChatGoogleGemini` (v1) | `ai_languageModel` | The LLM (cred: *Google Gemini*). |
| Simple Memory | `memoryBufferWindow` (v1.3) | `ai_memory` | Conversation buffer. |
| Structured Output Parser | `outputParserStructured` (v1.3) | `ai_outputParser` | Enforces the `output[]` schema; tolerates accidental double-nesting. |
| News Scrapper | `httpRequestTool` (v4.4) | `ai_tool` | NewsAPI.ai `getArticles` (cred: *News API Key*). **The source actually persisted downstream.** |
| Twitter / Instagram / TikTok / LinkedIn (profile) / LinkedIn (Jobs) / Reddit / YouTube / Facebook (Comments) / Facebook (Posts) | `httpRequestTool` (v4.4) | `ai_tool` | Apify actor calls via `run-sync-get-dataset-items` (cred: *Apify Token*). Bodies built with `$fromAI(...)`. |
| Call 'News Scrapper Sub-Workflow' | `toolWorkflow` (v2.2) | `ai_tool` (unconnected) | Points at workflow `BTRWBlpuSGS0ozed`. **Currently orphaned — see validation report.** |

## Processing and delivery pipeline

1. **AI Agent** `main` → **Check existing folder - Dropbox** (`httpRequest` v4.4) — `POST list_folder`
   on `/{{dropbox_root}}/Inputs/articles` (cred: *SentientDropbox*).
2. → **If** (`if` v2.3) — condition: `AI Agent.output` array **is empty**.
   - **true (empty)** → **No Articles found** (`code` v2, returns `{articles: []}`) → **Respond to Webhook**.
   - **false (has articles)** → **Response** (`code` v2).
3. **Response** joins each AI classification back to its raw NewsAPI article (pulled from the agent's
   `intermediateSteps` where the tool name is `news_scrapper`), builds a standardized article object,
   renders YAML frontmatter + body into a Markdown file (base64 binary), and derives a safe filename
   `<articleId>-<slug>.md`. Classifications with no matching raw article are dropped (quarantine
   object built but not emitted to the normal pipeline).
4. **Response** → **Loop Over Items** (`splitInBatches` v3, batch 10):
   - **loop** → **Wait** (`wait` v1.1, 2s) → **Upload a file** (`dropbox` v1) to
     `=/{{ DATA.dropbox_root }}/Inputs/articles/{{ Response.fileName }}` (cred: *SentientDropbox*) → back to the loop.
   - **done** → **Rebuild Response Items** (`code` v2, returns `{ sessionId, status: "completed",
     articleCount, error: null }`) → **Respond to Webhook**.
5. **Respond to Webhook** (`respondToWebhook` v1.5, `respondWith: allIncomingItems`) returns the
   final payload.

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
