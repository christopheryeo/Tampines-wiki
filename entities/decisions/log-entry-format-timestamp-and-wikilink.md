---
decisionId: log-entry-format-timestamp-and-wikilink
title: log.md entries must carry a full timestamp and a wikilink to the entity, one entity per line
status: accepted
date: 2026-07-06
affects: [scripts/entity_cascade_procedure.md, entities/article, entities/organisations, entities/people, entities/country, entities/place, entities/outlet, entities/decisions]
---

## Context
Every `log.md` entry so far carried only a date (`2026-07-06`, no time — entries on the same day
weren't orderable) and referenced entity files as backticked plain text (e.g. `` `mindef-mindef.md` ``)
rather than as clickable wikilinks. A single entry also often bundled multiple entities together
(e.g. one line covering 8 outlets, or 16 new organisation notes), so no single wikilink could
represent "the entity this line is about."

## Decision
Going forward, every `log.md` entry must carry:
1. A full timestamp (date **and** time, e.g. `` `date "+%Y-%m-%dT%H:%M:%S"` `` at write time), not
   date alone.
2. A `[[wikilink]]` to the entity file itself (not backticked plain text), pointing at the file's
   current real name.
3. Exactly one entity per line — a cascade touching five entities is five log lines, not one,
   because a wikilink only does its job if it names exactly one file.

`scripts/entity_cascade_procedure.md` Step 3 item 13 updated accordingly.

## Consequences
- **Existing entries were not split or given fabricated timestamps.** They were written before this
  decision, several batching many entities into one line with shared prose — retroactively forcing
  them into "one entity per line" would mean inventing which specific fragment of shared reasoning
  belongs to which entity, which isn't recoverable. Similarly, no exact original write-time was
  recorded, and backfilling a plausible-sounding one would be exactly the kind of fabricated
  precision §1/§7 warn against ("the organized lie") — worse than admitting we don't have it.
- Instead, every existing backticked entity-filename mention across all 7 domains' `log.md` files
  was mechanically converted to a real `[[wikilink]]` (pointing at the file's *current* name, even
  where the entry describes a since-renamed file — e.g. `[[mindef|mindef-mindef.md]]` displays the
  historical filename but links to the file that exists today). This was a pure navigation fix, not
  a content rewrite: prose, dates, and structure of every prior entry are unchanged.
- This note itself, appended to every domain's `log.md` at `2026-07-06T21:58:18`, is the marker: entries
  above it predate full timestamps and one-entity-per-line; entries from here on must have both.
