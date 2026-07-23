---
decisionId: enforce-article-quality-gates
title: Enforce source-backed article metadata quality gates
status: accepted
date: 2026-07-22
affects: [entities/article, scripts, dashboards]
---

## Context
An audit of all 16,837 compiled article notes found valid YAML throughout, but also found 3,366
May notes whose `sourceId` incorrectly contained the filename slug, 3,384 unsupported `sourceType`
values, five missing or invalid `toneSentiment` values, and generated artifacts that could silently
accept those values. The preserved DSTA feed exports contain the native May article IDs and identify
those records as `productType: FEED`; the 18 `news` records are URL-backed crawl inputs absent from
the feed exports. Existing link linting checks YAML syntax and wikilink integrity but does not enforce
the frozen article registry.

## Decision
1. Add `scripts/article_quality.py` as the deterministic article-frontmatter validator and safe
   repair tool. It validates the frozen registry, filename/native-ID agreement, enums, required
   values, uniqueness, publication-month placement, and core compiled sections.
2. Permit automatic repair only where provenance is deterministic: native IDs and `feed` status
   confirmed by preserved raw exports, and `crawl` status confirmed by URL-backed records absent
   from those exports. Sentiment remains a reviewed classification, never guessed by the repairer.
3. Make the article-quality check a required post-compile/pre-cascade and nightly gate, alongside
   the existing wikilink lint gate.
4. Parse generated catalogs with a real YAML parser so generated artifacts cannot conceal invalid
   multiline or typed frontmatter.

## Consequences
- The existing article registry and enum values do not change.
- Safe repairs preserve filenames and article bodies, so existing wikilinks remain stable.
- Every applied repair is logged and timed through the canonical run logger.
- Invalid or ambiguous source metadata blocks the gate and must be resolved from preserved source
  evidence or explicit human review.

