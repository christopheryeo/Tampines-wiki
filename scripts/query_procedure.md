---
type: procedure
name: entity-query
status: active
last_updated: 2026-07-25
---

# Entity Query Procedure

Applies §6's Query operation ("index-first navigation with answer-filing"): given a natural-language
question about one or more entities (e.g. "What did Chan Chun Sing talk about?"), resolve them, read
the compiled synthesis first, expand to source articles only as needed, and answer with citations.
Never full-text-grep the raw article corpus as a first move — every step below routes through an
index, a catalog, or an entity note's own compiled summary instead.

**Answer delivery:** the reply to the user is the direct answer only — phrased naturally, with no
citations and no references to the wiki, corpus, or these steps (all internal). Provide sources or
explain the process only when the user explicitly asks (see Step 5, item 21).

**Scope note:** only `entities/article/` is queryable — every note there has completed the cascade
procedure and is reflected in a domain `catalog.md`. Raw items still sitting in `Inputs/articles/`
have not been cascaded yet (no entity links, not in any catalog) and are out of scope for this
procedure entirely; if a question can only be answered from one of those, that's a sign the item
needs to go through Ingest first, not a case to special-case here.

## List-type queries (full-roster requests)

Some questions ask not "what did X do?" but "list **all** X" — every person, every outlet, every article, every topic, and so on. These are a distinct answer shape and are handled differently from the entity-traversal flow in Steps 2–4:

- **Step 0 still applies.** Check the search cache first, exactly as below — a repeated roster request should reuse its cached answer if it is relevant and not stale. A roster is stale under the same three triggers as Step 0 item 3, with the domain's note count standing in for `## Coverage`: (a) the domain's note count has *changed* — grown or shrunk — since the cached `askedDate`; (b) the roster is `timeSensitive` and older than the horizon; or (c) it was produced under an older `procedureVersion`.
- **Resolve the *domain*, not an entity.** Identify which domain the roster is over (people → `entities/people/`, outlets → `entities/outlet/`, etc.) and build the list from that domain's `catalog.md` (or `wiki.db`) — never by opening every note or grepping the corpus.
- **Render per that domain's `## Producing a List` convention.** Each domain's `index.md` carries a `## Producing a List` section defining exactly how a full roster of that domain must be grouped, nested, sorted, and labelled (e.g. people group by organisation then country; articles group by date then outlet). Follow it verbatim rather than inventing an ad-hoc ordering — this is what keeps roster output consistent and reviewable. Steps 2–4's inbound-Coverage traversal does not apply to a roster; the grouping fields all come from the catalog columns.
- **Still file to the cache (Step 7).** A roster request is filed back to `entities/search/` like any other query, with `## Entities Resolved` recording the domain(s) listed.

## Step 0 — Check the search cache first (mandatory; run before anything else)

1. Search `entities/search/catalog.md`'s `query` column for entries similar in wording or topic to
   the new question — this is a candidate search, not a requirement of exact match. Similarity of
   phrasing is just the filter for which candidates to look at next; it is not itself grounds to
   reuse anything.
2. **Judge relevance explicitly, for every candidate surfaced.** Open the candidate note and check
   whether its `## Question`/`## Answer` actually addresses what *this* query is asking — not just
   whether the wording overlaps. Similar phrasing does not guarantee the same question: "what was
   said about X" and "what happened at X" can diverge. A cached entry that only superficially matches
   must be treated as no match and set aside.
3. For any candidate that passes the relevance check, also check it isn't stale. An entry is stale if
   **any** of these three triggers fires — check all three:
   - **(a) Coverage changed.** Anything in its resolved entities' `## Coverage` has *changed* — grown
     *or* shrunk — since the entry's `askedDate` (spot-check `mentionCount`/`articleCount` on the
     relevant entity notes named in `## Entities Resolved`). A fall counts as much as a rise: a
     redaction or removal can invalidate an answer just as new coverage can. Appointment notes
     (`entities/appointments/`) carry neither `## Coverage` nor `mentionCount`; for those this trigger
     fires only if that appointment's `## Holders`/`currentHolder` changed since `askedDate`.
   - **(b) Time-sensitive and past its horizon.** The entry's `timeSensitive` field is `true` and it
     was asked more than `TIME_SENSITIVE_HORIZON_DAYS` (default 7) ago. A question framed relative to
     "now" — "recent", "latest", "lately", "these days", "been doing", "this week/month", "so far",
     "current" — decays as the clock moves even when no coverage changed, because "recent" means
     something different today than on `askedDate`. Stable factual questions ("Who is X?") are not
     time-sensitive and never expire on age alone. See `entities/search/index.md` for how
     `timeSensitive` is set and the horizon tuned.
   - **(c) Answered under an older procedure.** The entry's `procedureVersion` is older than this
     file's current `last_updated`. A cached answer composed under a superseded version of this
     procedure may no longer match what the current method would produce, so it is retired rather than
     trusted. A **blank or absent** `procedureVersion` (as on every entry filed before this field
     existed) does **not** by itself fire this trigger — such an entry is governed by (a) and (b)
     instead, exactly as it was before the field was added.
   If none of (a)–(c) fires, the entry is fresh.
4. **If a candidate passes both checks (relevant and fresh):** return its `## Answer` directly as the
   answer to the user, citing the cache entry itself alongside its original `## Sources Cited`.
   Increment its `reuseCount` by 1 and append a `log.md` entry for that update. **Stop here** — the
   rest of this procedure does not run, and no new search-cache entry is created for a repeat
   question.
5. **If no candidate is found, none is relevant, or the best match is stale:** proceed with the
   normal path starting at Step 1. If a stale-but-otherwise-relevant entry was found, mark it
   `status: superseded` now and link the new entry to it once written (Step 7). This query becomes a
   new cache entry at Step 7 regardless of how Step 0 turned out.

## Step 1 — Resolve (analysis only, no writes)

6. Extract every candidate entity name from the query — not just the first proper noun. A query can
   name more than one entity (e.g. "What did Chan Chun Sing and MINDEF say about ACAMM?" names three).
7. For each candidate, resolve it against the relevant domain's `catalog.md` — match against the
   `displayName` and `aliases` columns, not a full-text search across the article corpus. Check
   whichever domain catalog best fits the candidate's apparent type (person → `people/catalog.md`,
   organisation → `organisations/catalog.md`, etc.); if the type is unclear, check more than one.
8. If a candidate resolves to more than one entity (name collision) or to none at all, stop and
   disambiguate — ask the user, or state plainly that no entity note exists for it yet. Don't guess,
   and don't fall back to scanning the raw corpus as a substitute for resolution.
9. At scale (§1/§7's ~100K-token single-index ceiling), this whole step is exactly what the §8
   `traverse_index` MCP tool is for: a deterministic catalog lookup outside the context window,
   returning only the matching record(s). Until that tool exists in this vault, do the equivalent by
   hand — read the relevant `catalog.md`, don't `grep` the article corpus.

## Step 2 — Read the compiled synthesis first (cheap; no article-reading yet)

10. Open the resolved entity note(s) directly, e.g. `entities/people/chan-chun-sing.md`.
11. Read `## Summary` first. It is a rolling synthesis maintained by every cascade run that touches
    this entity (`scripts/entity_cascade_procedure.md` Step 3) — not raw data restated. For many
    queries, this alone answers the question.
12. Note `## Coverage` — the bounded, citable list of articles backing that Summary. This is the
    traversal target for "what did X talk about"-style queries: **inbound** citations (who wrote
    about X), not outbound links.
13. Note `## Related Entities` but do **not** expand into them yet — they answer "who/what is this
    connected to," not "what did they do or say." Hold them in reserve for Step 4.

**Appointment notes are shaped differently — handle holder questions here, not via Coverage.** A note
in `entities/appointments/` has no `## Summary` and no `## Coverage`; it carries a `## Holders` section
(dated `[[wikilinks]]`, newest first) and a `currentHolder` frontmatter field. For a role/office
question — "who is the current CDF?", "who was PS in Jan 2026?" — resolve a bare role-acronym
(CDF, PS, CNV…) against the `acronyms` column in `appointments/catalog.md`, then read that note's
`## Holders` and return the holder whose date range covers the date asked (default to `currentHolder`
when no date is given). Do not expect a Summary/Coverage traversal for these; the answer is the
date-matched holder link, and its person note (if one exists) is the place to expand for detail.

## Step 3 — Expand to source articles only as needed, ranked not exhaustive

14. If the Summary already answers the query with enough specificity to cite properly, skip straight
    to Step 5.
15. If the query needs a direct quote, an exact date, or more granularity than the Summary carries,
    open the articles listed in `## Coverage` — but rank first, don't blanket-read every one. Use the
    domain catalog's `publishedDate`, `toneSentiment`, `topic`/`category` fields to pick the top-K
    most relevant entries, not the full list.
16. At scale, this ranking-then-reading step is again a `traverse_index` candidate: filter/sort
    deterministically outside context, then read only the file paths actually returned.

## Step 4 — Expand to Related Entities only for broader-context queries

17. If the query is about the broader event or context rather than just this entity — "what happened
    at the meeting Chan Chun Sing attended," not "what did Chan Chun Sing say" — follow the relevant
    `[[wikilink]]` from `## Related Entities` and repeat Steps 2–3 for that entity too (e.g. also
    open `acamm.md` for its own Summary/Coverage).
18. This is the four-signal relevance model from §7 in practice: direct wikilink/Coverage citation is
    the first-pass signal; shared-source overlap, structural (Adamic-Adar) similarity, and type
    affinity via Related Entities are second-pass expansion — used deliberately when the query calls
    for it, not by default on every query.

## Step 5 — Answer the question directly

19. Compose the answer from whatever was actually read in Steps 2–4. Every claim must still be
    grounded in a specific article (§1 traceability): you must be *able* to point to the exact source
    for each statement, and must never assert anything you did not actually read. This grounding is an
    **internal** discipline — keep the claim→source mapping ready in case the user asks for it, but do
    not make the delivered answer carry it (see item 21).
20. Add nothing not grounded in what was read. No live web search, no model background knowledge —
    the same "no live web enrichment" rule that governs Ingest (`scripts/entity_cascade_procedure.md`)
    applies equally to Query.
21. **Deliver the answer directly — no procedure narration, and no references to the wiki.** The reply
    is a natural, self-contained answer to the question, phrased as if answering from knowledge —
    nothing else. Two things stay out of it:
    - **The procedure's machinery.** No mention of cache hits/misses, step numbers, entity resolution,
      `catalog.md`/`wiki.db` lookups, `#saf`/export-status internals, or the fact that the answer was
      filed back to the search cache.
    - **The wiki itself, as a source or object.** Do not reveal that the answer is drawn from a
      wiki/corpus, and do not append article-filename citations or a "Sources:" list. Avoid framing
      that points at the store rather than the fact — e.g. "in the corpus", "according to the
      coverage", "the wiki records", "the note says", "on record", "documented". State the fact
      plainly instead (write "They spoke by phone on 8 Mar 2026", not "The coverage documents a call").
    All of Steps 0-7 still run exactly as written — they are simply invisible in the delivered answer.
    Surface any of this — the citations/sources behind a claim, or how the answer was produced — **only**
    when the user explicitly asks for it (e.g. "what's your source?", "how did you find that?", or a
    question about the procedure or the vault's mechanics).

## Step 6 — File back to an entity note only if genuinely new

22. If answering required synthesizing across multiple entities in a way not already captured in any
    single note (e.g. a cross-cutting narrative spanning Chan Chun Sing + ACAMM + Cai Dexian that no
    one entity's Summary tells on its own), consider filing that synthesis back as a permanent note,
    per §6 ("answers with citations, and files lasting syntheses back as permanent notes"). A
    single-entity lookup the Summary already answers does not need a new note — that would just
    duplicate what's already compiled. This is separate from, and narrower than, Step 7 below.

## Step 7 — File the query itself to the search cache (mandatory, every time this path is reached)

23. This step only runs when Step 0 did **not** short-circuit the procedure (i.e. no relevant, fresh
    cache hit was found). File this question and answer to `entities/search/` per its `index.md`
    Template — not optional, and not dependent on the answer being novel; the cache's whole value is
    recording *every* question asked down this path, not just the interesting ones.
24. `queryId` = slugified question + content hash (see `entities/search/index.md` item 5).
    `## Entities Resolved` = every entity opened in Steps 1–4. `## Sources Cited` = every article
    opened in Step 3. `status: answered` unless the question couldn't be resolved at all
    (`status: unresolved`). Set `timeSensitive: true` if the question is framed relative to "now"
    (per the relative-time cues in Step 0 item 3b), else `false`. Set `procedureVersion` to this
    file's current `last_updated` value, stamping the method the answer was composed under.
25. If Step 0 found a stale match and marked it `superseded`, link this new entry to it in
    `## AI Context` (and vice versa on the old entry — but by appending a note there, never editing
    its original `## Answer`, per the append-only principle §5 and the search domain's own rule
    against touching up stored answers).
26. Regenerate `entities/search/catalog.md` (`python3 scripts/generate_catalog.py search`) and append
    a `log.md` entry per `entities/search/index.md`'s own operating instructions.

## Worked example A — "What did Chan Chun Sing talk about?" (cache miss)

0. **Check cache**: search `entities/search/catalog.md` — no candidate with similar wording/topic
   exists yet (this is the procedure's first real run against the search cache). Nothing to judge for
   relevance. Continue to Step 1.
1. **Resolve**: "Chan Chun Sing" → `people/catalog.md` → matches `aliases: [Chan Chun Sing, Mr Chan]`
   → `entities/people/chan-chun-sing.md`.
2. **Read synthesis**: `## Summary` already states three things — ADMM regional defence cooperation
   remarks (31 Oct), Navy@Vivo "whole-of-nation effort" remarks (23 Nov), and the 26th ACAMM opening
   speech (26 Nov). `## Coverage` lists the three backing articles (`757551`, `801234`, `810798`).
3. **Expand to articles**: only needed if a direct quote is wanted — e.g. pulling the exact line from
   `801234` ("It's very encouraging for us because... it is actually a whole-of-nation effort").
4. **Expand to Related Entities**: only if the question were broader, e.g. "what happened at ACAMM"
   — then also open `acamm.md`.
5. **Answer**: cite all three articles by title, not just "per his entity note."
6. **File back to the entity**: not needed — the Summary already carried this; nothing new was
   synthesized.
7. **File to the search cache**: mandatory since Step 0 didn't short-circuit — create
   `entities/search/what-did-chan-chun-sing-talk-about-<hash>.md` recording the question, the answer
   given, `## Entities Resolved` (`chan-chun-sing`), and `## Sources Cited` (`757551`, `801234`,
   `810798`); regenerate `entities/search/catalog.md`; append a `log.md` entry.

## Worked example B — "What was said about Seletar Aerospace Park?" (cache miss, run for real)

This one was run for real (not hypothetical) before the search cache domain existed, so Step 0/Step 7
weren't yet available to it. See `entities/search/what-was-said-about-seletar-aerospace-park-*.md` for
the cache entry filed retroactively once the domain was onboarded — it's the first real record in
the domain and demonstrates the Template in practice: `## Question` verbatim, `## Answer` exactly as
given (Princess Anne's visit to the Airbus Asia Training Centre, 13 Nov 2025, per article `782384`),
`## Entities Resolved` (`seletar-aerospace-park`), `## Sources Cited` (`782384`).

## Worked example C — "What did people say about Seletar Aerospace Park?" (cache hit)

A later, differently-worded question on the same topic — this is what Step 0 exists for.

0. **Search cache**: `entities/search/catalog.md`'s `query` column surfaces
   `what was said about Seletar Aerospace park?` (Worked example B) as a wording/topic match.
   **Judge relevance**: read that entry's `## Question`/`## Answer` — both questions ask what was
   reported about the same place, not two different things dressed up in similar words. Passes.
   **Judge freshness**: `## Entities Resolved` names `seletar-aerospace-park`; its `mentionCount` in
   `place/catalog.md` is still `1`, unchanged since the cached entry's `askedDate` — not stale.
1. **Return cached answer**: give the user Worked example B's `## Answer` verbatim, citing both the
   cache entry and its original source (`782384`). Increment that entry's `reuseCount` from `0` to
   `1` and log the update.
2. **Stop.** Steps 1–7 do not run — no new resolution, no new article reads, no new cache entry.

> **Snapshot note.** This example captures the hit as it stood when `seletar-aerospace-park` had
> `mentionCount 1`. That count has since grown (8 as of 2026-07-25), so the *same* re-ask today would
> instead go stale under trigger (a) — coverage changed — and be answered fresh rather than reused.
> The example still illustrates the relevance/freshness judgement of Step 0; it is a point-in-time
> snapshot, not a claim that this query is permanently a hit.

## Why inbound before outbound

An entity's `## Related Entities` section is easy to reach for first because it's right there in the
same note — but it answers a different question than most natural-language queries actually ask.
"What did X talk about" is a question about **what was said about/by X**, which lives in the
`## Coverage` backlinks (inbound: articles that cite X), not in `## Related Entities` (outbound: other
entities X is connected to). Starting outbound risks answering an adjacent-but-wrong question (e.g.
describing MINDEF's role instead of what Chan Chun Sing personally said) and pulls in unrelated
context the query never asked for. Inbound-first, outbound-only-on-demand keeps the answer scoped to
what was actually asked, and keeps token cost proportional to the query's real breadth.
