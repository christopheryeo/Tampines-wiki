---
decisionId: run-issue-radar-on-product-tables
title: Run the issue radar directly on canonical product tables
status: accepted
date: 2026-07-23
affects: [scripts, entities/issues]
---

## Context
The prototype radar read `index/wiki.db`, a generated SQLite file last updated before the current
article corpus and database-import work. This created a second, stale representation of article
tags and coverage. The canonical MySQL product tables already contain the fields used by all six
radar signals: article dates/categories/tone/event type, source tags, and outlet/country coverage.

## Decision
`scripts/issue_radar.py` will read the canonical product tables directly: `articles`,
`article_tags`, and `article_coverage` in production, or their `UAT_`-prefixed equivalents while
developing and validating in `MSM_dataset_UAT`. Database access is read-only. UAT is the default;
production must be selected explicitly. `index/wiki.db` is no longer a radar dependency.

## Consequences
- The radar is developed and validated against UAT, then can use production through the same
  read-only query with a different database/table-prefix configuration.
- The MySQL account used for production should have `SELECT` permission only; a read replica is
  preferred when available.
- Radar flags remain transient output. Judgment, clustering, and issue-note filing remain in the
  existing issue-radar procedure and do not write to the product database.
- Historical candidate selection is restricted to articles on or before `--asof`, removing the
  prototype's future-data eligibility leak.
