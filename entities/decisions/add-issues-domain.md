---
decisionId: add-issues-domain
title: Add Issues domain and issue-radar tooling for early-warning issue detection
status: accepted
date: 2026-07-08
affects: [entities/issues, scripts]
---

## Context
A backtest over the full corpus (9,299 articles, Nov 2025 – Mar 2026) showed that the vault's
biggest coverage blowups were structurally foreshadowed weeks in advance: the Amos Yee / Enlistment
Act complex showed institutional attachment and breadth expansion from 2025-11-20 (16 weeks before
its 2026-03-20 peak), the US-Iran conflict acquired domestic institutional categories 2–5 weeks
before the repatriation surge, and the UNC3886 entity existed in the vault from 2025-11-06, 13
weeks before the telco-attack blowup. These signals (recurrence across coverage waves, never-seen
outlets/countries, category migration into MINDEF/Parliament/COS Debate, unfacilitated share) are
computable deterministically from existing article frontmatter via `index/wiki.db` — but tag-level
flags over-generate by roughly 20x (115 HOT tags collapsed to 6 real issues on 2026-03-31), so a
judgment layer must cluster flags into issue objects and assess ramification before anything is
surfaced.

The vault previously had no home for this output: topics classify coverage, but nothing tracks a
*rising risk* with a status, a score, a rationale, and predicted catalysts.

## Decision
1. Create a new knowledge domain `entities/issues/` — one note per tracked issue (a percolating
   risk), with a frozen YAML registry defined in its `index.md` (issueId, displayName, status,
   ramification, score, firstFlagged, lastScored, clusterTags, aliases, articleCount). This note
   authorizes that registry's initial freeze.
2. Add `scripts/issue_radar.py` — the deterministic signal layer (read-only over `wiki.db`).
3. Add `scripts/issue_radar_procedure.md` — the written SOP for the judgment layer: clustering
   radar flags into issue objects, the ramification questionnaire, catalyst extraction, and filing
   into `entities/issues/`.

## Consequences
- New domain scaffolded with the standard system-file trio (`index.md`, `catalog.md`, `log.md`).
- `generate_catalog.py issues` works generically (reads the registry from the domain's `index.md`).
- Issue notes are created/updated only via `scripts/issue_radar_procedure.md`, never by cascade —
  this domain records *assessments about* coverage, not coverage itself.
- Dismissed flags are filed with `status: dismissed` and a reason, deliberately kept as calibration
  data for radar thresholds.
- The radar covers percolating issues only; exogenous shocks (e.g. bomb threats) have no media
  precursors and are out of scope by design.
