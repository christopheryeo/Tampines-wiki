---
decisionId: fix-articlecount-double-counting
title: Stop incrementing outlet articleCount on cascade — it is a pre-computed grand total
status: accepted
date: 2026-07-06
affects: [entities/outlet]
---

## Context
`scripts/entity_cascade_procedure.md` Step 3 instructed incrementing an existing entity's count field
(`articleCount` for outlets, `mentionCount` elsewhere) by 1 every time a cascade run added a new
citing article. This was correct for `mentionCount` (organisations/people/country/place all start at
0 and are built up purely by cascade — no prior data existed before these domains were scaffolded
today). It was **wrong for `outlet.articleCount`**.

Verified via `grep -rl "outlets:.*<outletId>" entities/article/` against the raw (pre-migration)
corpus: `msn-malaysia`'s pre-existing `articleCount: 45` already equalled 44 other raw articles still
in old schema *plus* `762104` itself (already migrated) — i.e. the count was a grand total computed
once, at initial ingestion, over the entire ~9,307-article corpus via each raw article's `outlets:`
field. It was never a running tally starting at zero. Every article this session cascaded already
existed in that raw corpus, so it was already counted — incrementing on top double-counted it.

This went unnoticed through the first two cascades (`816663` → `8days` 6→7; `757551`/`793259` →
`8world-news` 252→253→254) and was only caught while updating 8 more outlets in this batch, when the
Myanmar outlet's `articleCount: 1` turned out to be *exactly* the one article being cascaded, with
zero other raw articles — an unmissable tell once checked.

## Decision
`outlet.articleCount` is never incremented by this cascade procedure going forward, except for a
verified genuinely-new raw article (rare — would require re-verifying the aggregate is stale, not
just checking `outlets:` in already-migrated articles). All other domains' `mentionCount` fields are
unaffected by this decision; they remain incremented per cascade run as before, since they had no
pre-existing aggregate to double-count against.

## Consequences
- Reverted `articleCount` on 10 outlet notes to their correct pre-existing values: `8days` (7→6),
  `8world-news` (254→252), `msn-malaysia` (46→45), `channel-news-asia-online` (428→427), `mothership`
  (76→75), `lianhe-zaobao-online` (388→387), `straits-times-online` (770→769), `channel-news-asia`
  (87→86), `asiaone-news` (97→96), `ministry-of-information-republic-of-the-union-of-myanmar` (2→1).
- Their `## Coverage` backlinks and `aliases` backfills are **not** reverted — those are correct and
  independent of the count-field bug.
- `entities/outlet/index.md` operating instructions and YAML registry updated to state this
  explicitly; `scripts/entity_cascade_procedure.md` Step 3 item 10 updated to carve out this
  exception.
- `entities/outlet/catalog.md` regenerated to reflect the corrected counts.
- No other domain (`organisations`, `people`, `country`, `place`) is affected — none had a
  pre-existing count aggregate before today's cascades began.
