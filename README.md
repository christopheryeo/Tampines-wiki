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
│   ├── raw_feed_to_inputs.py      ← derives preserved raw feeds into Inputs/articles/
│   ├── ingest_cascade.py          ← timed raw-input compile + entity cascade runner
│   ├── article_quality.py         ← article schema check + source-backed safe repair
│   ├── stage_mysql_feeds.py       ← deterministic raw-feed to isolated UAT staging bundle
│   ├── check_links.py             ← vault-wide [[wikilink]] integrity checker (report-only)
│   ├── fix_links.py               ← vault-wide [[wikilink]] lint + auto-fix (run regularly)
│   ├── regenerate_coverage_labels.py
│   │                            ← repairs malformed entity Coverage labels from article summaries
│   ├── link_orphan_entity_bodies.py
│   │                            ← conservatively links orphan entity body mentions to peer entities
│   ├── patch_coverage.py          ← safely updates an entity's Coverage list + counts
│   ├── people_country_inference.py← proposes missing person-country fills for review
│   ├── run_logger.py              ← writes canonical run receipts and throughput metrics
│   ├── issue_radar.py             ← early-warning signal layer (read-only over product tables)
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

The Python scripts are grouped by broad operating function. They should stay deterministic and source-backed: scripts do mechanical work, while procedure documents cover judgment-heavy steps.

#### Intake and source staging

##### `raw_feed_to_inputs.py` — preserved feed export to raw intake notes
Derives JSON-style source exports from `raw/feed data/` into Markdown intake notes under `Inputs/articles/YYYY-MM/`. It writes the raw intake schema only: frontmatter plus source narrative body, no wikilinks, no compiled article sections, and no entity cascade. Default mode is a dry run; pass `--write` to create files. It checks both `Inputs/articles/` and `entities/article/` targets so reruns stay idempotent after later ingest moves files onward.

Common use:

```bash
python3 scripts/raw_feed_to_inputs.py --month 2026-05
python3 scripts/raw_feed_to_inputs.py --all --write
```

##### `stage_mysql_feeds.py` — deterministic UAT staging bundle
Validates preserved monthly feed exports against the approved source-to-UAT mapping, reconfirms expected file hashes, and writes escaped UTF-8 TSV files plus explicit MySQL `LOAD DATA LOCAL INFILE` and validation SQL. It writes no database data itself and never edits `raw/`. Staged records retain source file, source row, raw article ID, canonical raw JSON, and SHA-256 record hashes; known identity and quality exceptions are routed into `UAT_stg_quarantine` rather than corrected, truncated, merged, or discarded. `verify-bundle` recomputes generated file hashes, row counts, and per-source record-hash chains before or after database execution.

#### Ingest, cascade, and catalogs

##### `ingest_cascade.py` — timed raw-input compile + cascade runner
Runs the full batch process for a month of intake files. It counts `Inputs/articles/YYYY-MM/*.md`, compiles each raw item into `entities/article/YYYY-MM/`, moves raw files out of `Inputs/`, creates missing outlet/country/topic notes, updates entity Coverage backlinks, rebuilds affected catalogs, runs focused hard-error validation over touched notes, updates the article-domain cascade status table, and writes a timed `ingest_cascade` receipt through `run_logger.py`.

Use it for month batches that are already staged in `Inputs/articles/YYYY-MM/`:

```bash
python3 scripts/ingest_cascade.py --month 2026-07
python3 scripts/ingest_cascade.py --input-dir Inputs/articles/2026-07
python3 scripts/ingest_cascade.py --month 2026-07 --dry-run
```

Important boundaries: `--dry-run` previews without writing; outlets, countries, and topics can be created from raw metadata; people, organisations, and places are only linked when already present because creating them still requires judgment. The timer covers the full operation through validation and receipt writing, and each real run should report elapsed time, processed article count, and average seconds per article.

##### `patch_coverage.py` — safely update entity Coverage lists and counts
Handles the mechanical bookkeeping half of linking existing entities to newly-ingested articles. It increments mention/article counts by exactly the number of genuinely new `(entity, article)` pairs and appends matching `- [[article|label]]` lines to `## Coverage`. It does not decide which entities are new, write summaries, or touch related-entity prose.

Input is a JSON list of update objects with `domain`, `id`, `article`, optional `label`, and optional `alias`. Rows are grouped by entity automatically, and the script is idempotent: article links already present in Coverage are skipped, not re-added or re-counted. `outlet` is special-cased: `articleCount` is a pre-computed corpus-wide total and is never incremented.

##### `generate_catalog.py` — rebuild a domain's `catalog.md`
Regenerates one domain catalog from note frontmatter. `catalog.md` is always fully rewritten, so it must never be hand-edited. `article` and `outlet` use hand-tuned column sets; other domains read their column list from their own `index.md` YAML registry table. Run it after any ingest or entity update that changes a domain folder:

```bash
python3 scripts/generate_catalog.py people
```

#### Validation, linting, and safe repair

##### `article_quality.py` — compiled article metadata validation + safe repair
Validates compiled article notes against the frozen article registry: required fields, types and enums, native `sourceId` agreement with the filename, unique IDs, publication-month placement, and core compiled sections. `--check` is read-only and is a post-compile/pre-cascade or nightly gate. `--fix-safe` repairs only provenance-backed ID/source-type defects confirmed by preserved raw exports or URL-backed crawl provenance; reviewed sentiment corrections must be supplied explicitly with `--sentiment-overrides <json>`. Applied repairs keep body and filename unchanged, append the article audit log, and write a timed lint receipt.

##### `check_links.py` — vault-wide wikilink integrity check
Scans Markdown notes for `[[wikilink]]` references and reports hard failures and warnings: broken targets, target-embedded nested links, unbalanced links, alias-only links, YAML errors, and unlinked entity mentions in article prose. By default it skips documentation/template noise and always excludes `Inputs/`. It writes a `lint` receipt by default. Exit code is `1` for hard failures such as broken links, target-corrupting nested links, or YAML errors; advisory findings do not fail on their own.

##### `fix_links.py` — lint + mechanical wikilink repair
Runs the same detection as `check_links.py`, then applies safe repairs: normalize target-embedded nested links and isolated single-bracket closes; rewrite alias-only links to canonical piped links; relocate compiled-but-unmoved article notes from `Inputs/articles/<month>/` into `entities/article/<month>/`; repair known YAML corruption patterns; regenerate malformed Coverage labels; and connect otherwise-orphaned entity notes to explicitly named peer entities in prose. Article prose link backfill is opt-in with `--link-entities`. Anything still ambiguous is reported, never guessed. It writes a `lint` receipt by default and is intended for regular post-ingest or scheduled maintenance.

##### `regenerate_coverage_labels.py` — repair malformed Coverage display labels
Repairs entity Coverage lines whose display label contains an embedded wikilink. The outer article target is preserved exactly; only the display label is replaced, and the replacement is derived from the cited article's own `## Summary`. Use `--dry-run` to preview and `--log` to append one audit entry per changed entity note. This utility is also called through `fix_links.py`'s Coverage-label pass.

##### `link_orphan_entity_bodies.py` — add conservative peer links to orphan entity notes
Finds entity notes with no outgoing entity links and scans their body prose for explicit peer-entity names. YAML, Coverage, Source, AI Context, resolver notes, template comments, existing links, and the note's own name are excluded. Only unambiguous multiword names and uppercase acronyms are linked, so it is conservative enough for mechanical repair. Use `--dry-run` to preview, `--log` to append audit entries, and `--report <path>` for the full change list. This utility is also called through `fix_links.py`'s orphan-body pass.

#### Entity review and inference

##### `people_country_inference.py` — propose missing person-country fills
Builds the review table described in `people_country_inference_procedure.md`. Default mode is read-only and vault-grounded: it scans `entities/people/catalog.md` for blank `country` fields, inspects person notes and bounded Coverage article summaries for direct country/title evidence, and emits CSV or Markdown rows with evidence and recommended action. With `--internet-confirm`, it adds a Wikipedia API confirmation pass and records the external source URL plus fetch timestamp, but still writes only a review table; note edits remain a separate approved follow-up.

#### Operations and run receipts

##### `run_logger.py` — canonical operation receipts
Creates and validates structured run receipts under `runs/YYYY-MM-DD/`. Use it for raw-to-inputs, ingest, cascade, lint, and query operations where throughput matters. Receipts follow `run-log.v1` and capture `operation`, `startedAt`, `endedAt`, `durationSec`, article/file metrics, and stage metrics. It can be imported as `RunLogger` by scripts or used directly for ad hoc measured runs.

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

#### Issue radar and signal analysis

##### `issue_radar.py` — early-warning signal layer
Scores every candidate issue weekly on six structural signals read directly from the canonical MySQL product tables: `articles`, `article_tags`, and `article_coverage` (or their `UAT_`-prefixed equivalents). Signals are computed strictly from data on or before the evaluation date: acceleration (articles in the last 28 days vs the prior 28), breadth expansion (never-before-seen outlets and countries), institutional attachment (share of recent coverage in government, parliamentary, or policy categories, and its rise), recurrence (distinct coverage waves separated by silent weeks), unfacilitated share, and opinionated share. Flags come out tiered — **HOT**, **WARM**, **WATCH** — and every flag carries plain-language reasons ("27 never-seen outlets", "institutional share rose 0%→91%"), so nothing is a mystery score.

UAT is the safe default: run `python3 scripts/issue_radar.py --source uat --defaults-file <read-only-client.cnf>`. Production must be selected explicitly with `--source production` and should use a SELECT-only account or read replica. Add `--asof YYYY-MM-DD` for historical reconstruction, `--issue "<tag>"` for one issue's weekly series, or `--top N --min-tier WARM` to control the report. It is **read-only** — it never writes to MySQL or the vault; filing its output is the judgment layer's job, per `issue_radar_procedure.md`. Candidates are tag-level and deliberately over-generate (~20x); clustering them into real issues is judgment, not counting. The Python code remains stdlib-only and invokes the installed MySQL client for authenticated access. `index/wiki.db` is not used by the radar.

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
