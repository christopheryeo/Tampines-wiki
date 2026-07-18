# Media Monitoring Wiki

A file-based knowledge vault that tracks monitored media coverage. It ingests raw media items (RSS-style feeds and crawled articles), compiles each into a structured Markdown note, and cascades links out to every person, organisation, place, outlet, country, and topic the item mentions — so the whole corpus is navigable as a connected wiki rather than a flat pile of clippings. On top of that connected corpus it runs an **issue radar**: an early-warning layer that watches for percolating issues — coverage clusters whose structure says they are heading toward a blow-up — weeks before they peak.

The vault is plain Markdown plus a few YAML/JSON config files and Python scripts. It is designed to open cleanly in Obsidian (note the `[[wikilinks]]`) while remaining fully readable and editable as ordinary text files.

---

## Directory structure

```
media-monitoring/
├── README.md              ← this file
├── wiki.yaml              ← vault manifest (name, description, registered entities)
│
├── Inputs/                ← raw, not-yet-cascaded items awaiting Ingest (raw input schema)
│   └── articles/
│       └── YYYY-MM/       ← one raw feed/crawl item per file (grouped by month), named
│                             <articleId>-<slug>.md; compiled + moved to
│                             entities/article/YYYY-MM/ once cascaded
│
├── raw/                   ← original source-provided feed exports and archive; preserved as
│                             source evidence, not edited directly
│   ├── feed data.zip      ← original archive received on 2026-07-16
│   └── feed data/         ← extracted monthly JSON-style feed exports
│
├── entities/              ← the wiki itself: one folder per knowledge domain
│   ├── article/           ← compiled source notes for every piece of coverage that has completed
│   │                         the cascade procedure (grouped by month) — not-yet-processed items
│   │                         stay in Inputs/articles/ until then
│   ├── outlet/            ← the media outlets that published coverage
│   ├── people/            ← named individuals mentioned in coverage
│   ├── organisations/     ← agencies, companies, units, and other bodies
│   ├── appointments/      ← named offices and appointments, with dated holders — resolves an
│   │                         office title to the person who held it on the relevant date
│   ├── place/             ← specific locations (camps, bases, buildings, districts)
│   ├── country/           ← countries referenced across coverage
│   ├── topic/             ← recurring themes and named exercises/events
│   ├── issues/            ← the early-warning watchlist: live risk assessments (status, score,
│   │                         ramification, catalysts) layered above topics — see Issue radar below
│   ├── search/            ← saved answers to natural-language questions asked of the vault
│   └── decisions/         ← the vault's own change log — every rule/schema change, with rationale
│
├── schemas/               ← frozen field definitions for the two core entities
│   ├── article.yaml
│   └── outlet.yaml
│
├── scripts/               ← maintenance tooling and the written procedures agents follow
│   ├── generate_catalog.py        ← rebuilds every domain's catalog.md
│   ├── check_links.py             ← vault-wide [[wikilink]] integrity checker (report-only)
│   ├── fix_links.py               ← vault-wide [[wikilink]] lint + auto-fix (run regularly)
│   ├── patch_coverage.py          ← safely updates an entity's Coverage list + counts
│   ├── people_country_inference.py← proposes missing person-country fills for review
│   ├── run_logger.py              ← writes canonical run receipts and throughput metrics
│   ├── issue_radar.py             ← early-warning signal layer (read-only over wiki.db)
│   ├── entity_cascade_procedure.md← how a raw item becomes notes + cascaded links
│   ├── query_procedure.md         ← how to answer questions against the vault
│   ├── people_country_inference_procedure.md
│   │                            ← how to infer missing person countries from vault context
│   └── issue_radar_procedure.md   ← how radar flags become filed issue assessments
│
├── topics/                ← monitoring topic definitions (keywords, sources, schedule)
│   └── sa26.json
│
├── dashboards/            ← saved dashboard layouts (tiles + their SQL queries)
│   └── default.json
│
├── runs/                  ← per-run ingest receipts (items found / new / duplicates)
│   └── YYYY-MM-DD/        ← canonical run receipts plus artifacts/ for temporary JSON
│
├── index/                 ← generated query index
│   └── wiki.db            ← SQLite mirror of the notes, for fast SQL-style queries
│
├── .obsidian/             ← Obsidian app settings (safe to ignore outside Obsidian)
└── .claude/               ← agent settings for this vault
```

---

## The `Inputs/` folder — the raw intake

`Inputs/` is where raw coverage lands *before* it becomes part of the wiki. It sits deliberately outside `entities/` and outside every `catalog.md`, so anything here is invisible to queries until it has been ingested. Items are stored one per file under `Inputs/articles/YYYY-MM/`, grouped by publication month, and named `<articleId>-<slug>.md`.

These raw files use their own **input schema**, which is *not* the compiled article-note schema used in `entities/article/`. Their frontmatter carries the fields the ingest pipeline emits — `articleId`, `articleTitle`, `publishedDate`, `category`, `topic`, `tone`, `toneSentiment`, `eventType`, `tags`, `outlets`, `countries`, `coverageCount`, `mediaCount`, `sourceType`, and `url` — and the body is the raw report as **plain narrative text with no `[[wikilinks]]` yet**. (Note the differences from a compiled note: here `tags` are plain strings like `[Exercise, Training]` rather than quoted `#`-hashtags, links are absent rather than piped, and there is no `## Summary`/`## Related Entities` structure.)

Two `sourceType` variants arrive through the same folder:

- **`feed`** — items from the RSS-style feed pipeline, with a numeric `articleId` (e.g. `757544-…`) and typically `url: null`.
- **`crawl`** — items from a web crawler, with a `crawl-<hash>` `articleId` (e.g. `crawl-fff1…`), a populated `topic`, and a real source `url`.

Ingesting a raw item is a **two-step** move: first *compile* it — rewrite its frontmatter and body into the article-note template, turning the plain narrative into a summary with `[[wikilinks]]` — then *cascade* those links out to every entity they touch. Compiling includes **moving** the file (same filename) into `entities/article/YYYY-MM/`; it is never left duplicated in `Inputs/`. Only after that move does the item count as "in the wiki". The full method is defined in `scripts/entity_cascade_procedure.md`.

---

## The `raw/` folder — source exports

`raw/` is the preserved source-data folder for feed files received on the morning of **2026-07-16**. It currently contains the original archive, `raw/feed data.zip`, and extracted monthly feed exports under `raw/feed data/` for April, May, June, and July 2026.

These files are JSON-style feed exports. They contain article/feed records with fields such as article IDs, titles, descriptions, tags, coverage outlets, countries, sentiment lists, document metadata, and source URLs. They are upstream source evidence, not ingest-ready wiki notes.

Treat `raw/` differently from `Inputs/`:

- **`raw/`** preserves the received source material. Do not edit, normalize, or hand-correct these files directly.
- **`Inputs/`** holds derived, not-yet-cascaded article files that are ready to be compiled into the wiki.

When transforming source exports into wiki intake files, derive new files into `Inputs/articles/YYYY-MM/`, preserve original identifiers and provenance, and document or script any parsing/normalization step. Keep `raw/feed data.zip` as the original archive unless it is explicitly replaced or removed by instruction.

---

## The `entities/` domains

Each subfolder under `entities/` is a **knowledge domain**. Every domain holds a set of entity notes (one Markdown file per thing) plus a standard trio of **system files** described below.

- **article** — the heart of the vault. One note per piece of coverage, carrying the summary, sentiment/tone classification, event type, tags, and links to every entity it mentions. Notes are grouped into `YYYY-MM/` sub-folders (e.g. `2026-03/`) purely for navigation. Filenames are `<sourceId>-<slugified-title>.md`. Only cascade-complete articles live here — a raw item sits in `Inputs/articles/YYYY-MM/` under the same filename until it's compiled, at which point it is *moved* into this folder (never left duplicated in both places).
- **outlet** — the "who published it" record for each media outlet, with country, media category, and a running count of articles.
- **people**, **organisations**, **place**, **country** — the entities that articles mention. Each note carries a short summary plus a Coverage list linking back to the articles it appears in.
- **topic** — recurring themes and named events/exercises (e.g. exercises, policy debates) used to group related coverage.
- **appointments** — named offices and appointments that coverage cites by title. Each note is keyed by its office title and is *stable over time*; the holder is a dated `[[wikilink]]` in the body, so an office reference in an article resolves to whoever held the office **at that article's date**, not whoever holds it now. Not populated by cascade — holder facts come from official reference pages. Authorized by the [[add-appointments-domain]] decision.
- **issues** — the early-warning watchlist. Where a topic note *classifies* coverage, an issue note records a live *assessment* of a rising risk: its status (`watch`/`warm`/`hot`/`dismissed`/`closed`), radar score, judged ramification, the signals that fired, known future catalysts (court dates, sittings, visits — each cited to an article), and a recommended posture. Populated only via `scripts/issue_radar_procedure.md`, never by the article cascade. Dismissed flags are kept as calibration data. Authorized by the [[add-issues-domain]] decision.
- **search** — saved natural-language questions and the answers the vault produced, so past queries are reusable.
- **decisions** — the vault's amendment log. Because schemas and rules are *frozen*, any change to how the vault works is recorded here first, with its reasoning, before being applied.

---

## System files (in every domain folder)

Every folder under `entities/` contains the same three system files. Together they make each domain self-describing, exhaustively listed, and fully auditable.

### `index.md` — the curated front door *(hand-maintained)*
The domain's operating manual. It states the domain's purpose, its note type, the **frozen YAML field registry** every note must follow, and the step-by-step instructions for adding or updating notes here. This file doubles as the schema of record for the domain — you should be able to work in a folder by reading its `index.md` alone. It is edited by hand, and only deliberately.

### `catalog.md` — the complete listing *(auto-generated — never hand-edit)*
A generated table of **every** note in the domain, one row each, with the key fields pulled straight from note frontmatter (dates, IDs, titles, status, sentiment, tags, and a link to the file). It is produced by `scripts/generate_catalog.py` and rebuilt whenever the domain changes. Because it is regenerated wholesale, any manual edits are overwritten — treat it as read-only.

### `log.md` — the append-only ledger *(never edit prior entries)*
A chronological record of every action taken in the domain: what was ingested or changed, when, from which source, and why. Entries are only ever *appended* — mistakes are corrected going forward with a new entry, never by rewriting history. Each entry timestamps the action and `[[wikilinks]]` to the entity it touched, so the log doubles as a navigable audit trail.

The division of labour is deliberate: `index.md` says how the domain *should* work, `catalog.md` shows what *is* in it right now, and `log.md` records how it *got* that way.

---

## Supporting files

- **`wiki.yaml`** — the vault manifest: its name, a one-line description, and the list of registered core entities.
- **`raw/`** — preserved source exports received on 2026-07-16, including the original archive and extracted monthly feed files. Do not edit directly; derive ingest-ready files into `Inputs/`.
- **`schemas/`** — frozen field definitions for `article` and `outlet`. Changing a schema requires a note in `entities/decisions/` first.
- **`scripts/`** — Python maintenance tools plus the written procedures agents follow. Detailed below under [The `scripts/` folder](#the-scripts-folder).
- **`topics/`** — one JSON file per monitored topic, defining its keywords, sources, run schedule, and last-run status.
- **`dashboards/`** — saved dashboard layouts; each tile pairs a natural-language question with the SQL that answers it.
- **`runs/`** — canonical JSON receipts for raw-to-inputs, ingest, cascade, lint, and query operations. Receipts record article/file counts, elapsed time, and average time per article/file. Temporary batch inputs, previews, and diagnostic JSON live under each day's `artifacts/` subfolder.
- **`index/wiki.db`** — a SQLite mirror of the notes that enables fast, SQL-style queries over the corpus. It is generated from the Markdown, which remains the source of truth.

## Version control policy

Git tracks the operating surface of the vault: scripts, schemas, configuration, procedure documents, domain manuals, append-only logs, decisions, and curated entity notes. It does **not** track bulk intake/source material, compiled article notes, generated catalogs, or generated query indexes.

Keep these rules aligned with `.gitignore`:

- Track entity domains such as `entities/people/`, `entities/organisations/`, `entities/outlet/`, `entities/place/`, `entities/country/`, `entities/topic/`, `entities/issues/`, and `entities/decisions/`.
- Do not track compiled article notes under `entities/article/`; they are bulk derived corpus data and remain local to the vault.
- Do not track generated `entities/**/catalog.md` files. Rebuild them with `scripts/generate_catalog.py` when needed.
- Keep `entities/**/index.md` and `entities/**/log.md` tracked unless a domain has an explicit exception, because they define domain behavior and preserve the audit ledger.

## The Purpose of the Wiki

The purpose of the wiki is to **ingest** articles. A raw item first lands in `Inputs/articles/YYYY-MM/` (one file per article, un-cascaded). Ingesting it is not just filing one note — it requires compiling that raw item into the domain's frontmatter/body template, relocating it (same filename) into `entities/article/YYYY-MM/`, and cascading entities through all the various files: every person, organisation, place, outlet, country, and topic the article mentions has to be created or updated, and links wired up in both directions across the affected folders. An article only counts as "in the wiki" once that move into `entities/article/` has happened — `Inputs/` is deliberately outside `entities/` and outside every `catalog.md`, so it sits outside the wiki's queryable surface until then. That whole process is defined by the **cascade procedure** (`entity_cascade_procedure.md`).

The second thing we do with the wiki is **query** it — ask a question and get a cited answer back. Querying the wiki is taken care of by the **query procedure** (`query_procedure.md`), which routes every question through the indexes and compiled summaries rather than brute-force searching the raw articles.

The third thing we do is **watch** it — the **issue radar**. Because the corpus is structured and linked, rising issues are visible *before* they peak: they recur across coverage waves instead of dying with the news cycle, spread to never-seen outlets and countries, and migrate into institutional categories (government, parliamentary, and policy categories). A backtest over the full corpus showed 2–17 weeks of structural lead time on real blowups (the Amos Yee / Enlistment Act complex flagged 16 weeks before its March 2026 peak; the US-Iran conflict's migration into a domestic repatriation operation flagged 2–5 weeks ahead), while flat, simmering coverage correctly never alarmed. The radar is two layers by design: `issue_radar.py` does the deterministic counting, and the **issue radar procedure** (`issue_radar_procedure.md`) does the judgment — clustering flags into issue objects, assessing ramification, extracting catalysts — and files the results into `entities/issues/`.

We also need to do **linting** — checking that all the wikilinks across the vault are correct and nothing points at a missing note, and fixing what can be fixed mechanically. That is done by `check_links.py` (reporting) and `fix_links.py` (reporting *and* auto-fixing) — see [`fix_links.py` — lint + auto-fix wikilinks](#fix_linkspy--lint--auto-fix-wikilinks) below.

So the folder holds two kinds of things: **Python programs** that perform mechanical, error-prone bookkeeping deterministically, and **procedure documents** that spell out — in prose — the judgment-based steps an agent (or person) follows by hand. The split is deliberate: anything that can be got wrong by miscounting or mis-editing is handed to code; anything that requires judgment stays written down as a procedure.

### Python scripts

#### `generate_catalog.py` — rebuild a domain's `catalog.md`
Regenerates one domain's `catalog.md` from the frontmatter of its notes, so the catalog is always an exhaustive, up-to-date mirror of what is actually in the folder. Run it as `python3 scripts/generate_catalog.py <domain>` (e.g. `article`, `outlet`, `people`). It reads every note in the domain, pulls the relevant fields, sorts them (articles by date newest-first; entities alphabetically), and **overwrites** `catalog.md` wholesale — first run creates the file, every run after replaces it, which is why the catalog must never be hand-edited.

The `article` and `outlet` domains have hand-tuned column sets (they predate the others and carry schema-migration fallbacks). Every other domain is handled generically: the script reads that domain's column list straight out of its own `index.md` "YAML registry" table, so a brand-new domain works the moment its `index.md` exists — no code change needed here. It is meant to run as part of the nightly routine after ingest, not ad hoc mid-task.

#### `patch_coverage.py` — safely update an entity's Coverage list and counts
Handles the mechanical "bookkeeping" half of linking an existing entity to newly-ingested articles: incrementing the entity's mention/article count by *exactly* the number of genuinely-new `(entity, article)` pairs and appending the matching `- [[article|label]]` lines to its `## Coverage` section. It deliberately does **not** decide which entities are new, write summary prose, or touch related-entity links — those are judgment calls that stay manual. It exists because doing this counting by hand caused real overcount and double-counting bugs.

It takes a JSON file listing update objects (`domain`, `id`, `article`, an optional display `label`, and an optional `alias`), grouping multiple rows for the same entity automatically so a whole batch runs in one pass. It is **idempotent** — an article already present in a Coverage block is silently skipped, never re-added or re-counted — so it is safe to re-run after an interrupted batch. Run `python3 scripts/patch_coverage.py updates.json`, or add `--dry-run` to preview changes without writing. The script writes a `cascade` receipt through `run_logger.py` by default; add `--no-run-log` only for tests or debugging runs that should not count toward throughput. The `outlet` domain is special-cased: its `articleCount` is a pre-computed corpus-wide total and is never incremented — only Coverage lines (and a missing `aliases` field) are added.

#### `people_country_inference.py` — propose missing person-country fills
Builds the review table described in `people_country_inference_procedure.md`. By default it is read-only and vault-grounded: it scans `entities/people/catalog.md` for blank `country` fields, inspects person notes and bounded Coverage article summaries for direct country/title evidence, and emits CSV or Markdown rows with evidence and recommended action. With `--internet-confirm`, it adds a Wikipedia API confirmation pass and records the external source URL plus fetch timestamp, but still writes only a review table; note edits remain a separate approved follow-up. Example: `python3 scripts/people_country_inference.py --internet-confirm --limit 50 --format markdown --summary`.

#### `run_logger.py` — canonical operation receipts
Creates and validates structured run receipts under `runs/YYYY-MM-DD/`. Use it for every raw-to-inputs, ingest, cascade, lint, and query operation where throughput matters. Receipts follow `run-log.v1` and must capture `operation`, `startedAt`, `endedAt`, `durationSec`, `articleMetrics.processedCount`, `articleMetrics.avgSecPerArticle`, and any `stageMetrics[]` for sub-steps such as `ingest`, `cascade`, or `lint`.

Canonical receipts are named `YYYYMMDDTHHMMSS-<operation>-<short-id>.json` and live directly under the date folder. Non-receipt JSON — patch inputs, orphan-link previews, dry-run outputs, or temporary diagnostics — belongs in `runs/YYYY-MM-DD/artifacts/` so throughput dashboards can safely read only the date-folder receipts.

Use it directly for ad hoc measurements:

```bash
python3 scripts/run_logger.py record --operation lint --processed-count 4580 --duration-sec 42.5 --files-scanned 7261 --notes "post-cascade link check"
```

Or import `RunLogger` in scripts that can time stages directly:

```python
from run_logger import RunLogger

with RunLogger("ingest_cascade", trigger="manual") as run:
    with run.stage("ingest", article_count=batch_size) as stage:
        ...
    with run.stage("cascade", article_count=batch_size) as stage:
        stage.set_metric("entityUpdates", {"people": 12, "organisations": 8})
        ...
    run.set_article_metrics(inputCount=batch_size, processedCount=batch_size, createdCount=batch_size)
```

Run `python3 scripts/run_logger.py sample` to inspect a valid example receipt, or `python3 scripts/run_logger.py validate <receipt.json>` before using a receipt in dashboards.

The caller should be the operation runner, not the person reviewing the vault. Today, `patch_coverage.py`, `check_links.py`, and `fix_links.py` call `RunLogger` themselves. Raw-to-inputs, ingest, and query runs should be wrapped by the script or agent procedure that actually executes those steps, using the import pattern above so the measured time starts before work begins and ends after validation/bookkeeping.

#### `check_links.py` — vault-wide wikilink integrity check
Scans every Markdown note for `[[wikilink]]` references and reports three classes of problem: **BROKEN** (target matches no filename and no alias — always a bug), **ALIAS-ONLY** (resolves only via a note's `aliases:` frontmatter, which is fragile in this vault — prefer the piped `[[real-filename|Display Name]]` form), and **YAML ERROR** (a note's frontmatter fails to parse, which silently drops every field and is usually the root cause behind the other two). By default it skips documentation and template files (`index.md`, `catalog.md`, `log.md`, templates, `scripts/*.md`, and the decisions log) where placeholder examples are expected to "fail".

Run `python3 scripts/check_links.py` to check the live data notes, `--include-docs` to check everything with no exclusions, or `--domain <name>` to restrict the scan to one domain. It writes a `lint` receipt by default, including notes scanned, article notes scanned, hard failures, and warning counts; add `--no-run-log` only for tests or debugging runs. It exits with code `1` if any broken link or YAML error is found (useful for wiring into a check gate); alias-only warnings never fail the exit code on their own. It requires PyYAML.

#### `fix_links.py` — lint + auto-fix wikilinks
Runs the same detection as `check_links.py`, then mechanically repairs the three classes of problem that don't require judgment: (1) rewrites ALIAS-ONLY links to the canonical piped `[[real-filename|Display]]` form, preserving whatever text was displayed before; (2) relocates BROKEN article links whose target is already a fully-compiled note sitting in `Inputs/articles/<month>/` (frontmatter starting `type: source`, a `sourceId` field, a `## Summary` section) into `entities/article/<month>/`, regenerating `catalog.md` and appending one backfilled `log.md` entry per article — repeating to a fixed point, since relocating one article can surface more of the same via its own body links; (3) repairs two known YAML frontmatter corruption patterns (an unquoted `#` starting a flow-list item; a backslash-escaped apostrophe inside a single-quoted scalar), only keeping the fix if it actually makes the frontmatter parse under PyYAML. Anything left — a BROKEN link with no match anywhere, or a YAML error that doesn't match either known pattern — needs a judgment call and is only reported, never guessed at (a missing entity still has to be created via `entity_cascade_procedure.md`).

Run `python3 scripts/fix_links.py` to scan, fix, and report; add `--dry-run` to preview without writing, `--domain <name>` to restrict entity-local passes to one domain (article relocation is always vault-wide), or `--skip-relocate`/`--skip-alias`/`--skip-yaml`/`--skip-coverage-labels`/`--skip-entity-body-links` to disable an individual pass. It writes a `lint` receipt by default, including scan size, changed files, safe fixes applied, and remaining manual-attention counts; add `--no-run-log` only for tests or debugging runs. In addition to structural, alias, YAML, and article-relocation repairs, it regenerates malformed Coverage labels from the cited article's own `## Summary` and connects otherwise-orphaned entity notes to explicitly named peer entities in their prose. Both passes preserve existing targets and log every changed entity. Exit code `1` if anything is left needing manual attention, `0` if clean. Meant to be run regularly — after any ingest/cascade batch, or on a schedule — so link rot never has a chance to accumulate. Requires PyYAML.

#### `issue_radar.py` — early-warning signal layer
Scores every candidate issue weekly on six structural signals, computed strictly from data on or before the evaluation date (so historical runs are hindsight-free): acceleration (articles in the last 28 days vs the prior 28), breadth expansion (never-before-seen outlets and countries), institutional attachment (share of recent coverage in government, parliamentary, or policy categories, and its rise), recurrence (distinct coverage waves separated by silent weeks), unfacilitated share, and opinionated share. Flags come out tiered — **HOT**, **WARM**, **WATCH** — and every flag carries plain-language reasons ("27 never-seen outlets", "institutional share rose 0%→91%"), so nothing is a mystery score.

Run `python3 scripts/issue_radar.py` for the current state, `--asof YYYY-MM-DD` for a historical reconstruction (this is how the backtest was done), `--issue "<tag>"` for one issue's weekly series, or `--top N --min-tier WARM` to control the report. It is **read-only** — it never writes to the vault; filing its output is the judgment layer's job, per `issue_radar_procedure.md`. Candidates are tag-level in this prototype and deliberately over-generate (~20x); clustering them into real issues is judgment, not counting, which is why it lives in the procedure. Stdlib only, no dependencies.

### Procedure documents

These are not run — they are read and followed. Each is a written standard operating procedure for a task where the steps require judgment and so cannot be safely automated end to end.

#### `entity_cascade_procedure.md` — turning an article into linked entities
The step-by-step method for the cascade half of ingest: given a compiled article note, extract every `[[wikilink]]` it contains, classify each into the right domain, create a note for any entity that does not yet exist (using that domain's `index.md` registry and template), and wire up links in **both** directions — the new entity backlinks to the citing article via its `## Coverage` section, and links out to its peer entities. It codifies the vault's hard rules: always use the piped `[[real-filename|Display Name]]` link form, never enrich from live web or model knowledge (only from the citing article), and quote flow-list values beginning with `#` (an unquoted hash-prefixed tag is invalid YAML and silently destroys the whole frontmatter block — the most expensive bug found while building the vault).

#### `query_procedure.md` — answering questions against the vault
The method for answering a natural-language question about entities without brute-force searching the raw corpus. It routes every step through an index, a catalog, or a compiled summary instead. It begins with a mandatory check of the `entities/search/` cache — reusing a prior answer only if it genuinely addresses the same question *and* is not stale (nothing in the resolved entities' Coverage has grown since) — then resolves each named entity against the relevant domain `catalog.md`, reads the compiled entity summaries first, and expands to individual source articles only as needed, always answering with citations. Every non-cached query is itself filed back into the search cache for reuse.

#### `people_country_inference_procedure.md` — filling missing person countries from context
The judgment procedure for proposing and, after approval, writing `country` values for person notes whose country is blank. It starts from already-ingested vault context: the person note, its Coverage articles, and directly relevant linked organisation/country/appointment notes. It requires a review table first (`suggestedCountry`, confidence, evidence, evidence file, and action), allows live web lookup only as an explicit confirmation pass with source URL and fetch timestamp, writes only high-confidence approved updates, appends one people-domain log entry per changed person, regenerates the people catalog, and runs the people-domain link/YAML gate. It explicitly forbids filling blanks from model background knowledge, name ethnicity, or article/outlet country alone.

#### `issue_radar_procedure.md` — turning radar flags into filed issue assessments
The judgment half of the issue radar. Five steps: run the signal layer (never hand-tuning its output mid-pass); cluster tag-level flags into issue objects by checking article/entity overlap (six flags like `amos yee`, `enlistment act`, `cmpb`, `deportation` are one issue — and issues are named for the risk, not the person carrying it); answer the **ramification questionnaire** from vault content only (who is forced to respond if this doubles? which standing fault line does it touch? what future dated catalysts do the citing articles mention? has anyone senior taken an irreversible position? is a foreign story migrating into domestic institutional categories?); file the result into `entities/issues/` per that domain's registry and template, keeping dismissals as calibration data; and surface only `warm`+ issues with `moderate`+ ramification — precision over recall at the alert layer, liberal filing at the watchlist layer. Its known limits are written down in the procedure itself: it detects *percolating* issues only — exogenous shocks have no media precursors and must never be claimed as detectable.

---

## Core principle

The Markdown notes are always the source of truth. Everything generated — `catalog.md` files, `wiki.db`, dashboards — is derived from them and can be rebuilt. Provenance is preserved end to end: every article note cites its original source, every change is logged, and summaries are drawn only from ingested source material, never from live web lookups or model background knowledge.
