---
decisionId: fold-enrichment-into-compile
title: Fold radar enrichment into compile with a lookup-first, single-pass model gate
status: accepted
date: 2026-07-23
affects: [scripts, Inputs, entities/article, entities/outlet, issue-radar]
---

## Context

[[add-llm-radar-input-enrichment]] added `scripts/enrich_radar_inputs.py` as a separate pre-compile
stage that fills six radar fields using two independent structured model passes, applying a value
only when both passes agree above the confidence threshold.

Two things have since become clear from the implementation and the corpus.

First, that decision recorded that the runner "derives outlet metadata from the source URL", but it
does not. `outlet_name` and `outlet_country` are members of the model response schema and are
requested from the model in both passes, then compared for agreement. The only URL parsing in the
script is `public_url()`, an SSRF guard. Meanwhile the vault already holds 530 notes under
`entities/outlet/`, each carrying its country, and `ingest_cascade.ensure_outlet()` already resolves
outlets deterministically against them during cascade. The corpus can answer for known outlets what
the model is currently being paid twice to guess.

Second, an article now takes two separate per-article passes over its text — enrichment, then
compile — where only the judgement-bearing fields need a model at all.

## Decision

Enrichment ceases to be a separate stage and becomes the first phase of compile.

1. A generated outlet index, derived from `entities/outlet/`, resolves outlet name, outlet country,
   and institutional category by domain lookup. The model is consulted only for outlets the index
   does not know, and any newly resolved outlet is written back to the index.
2. The model is called **once** per article, for the fields that genuinely require judgement: tone,
   event type, issue tags, and the compiled summary and key points.
3. The dual-pass agreement check is replaced by a single-pass confidence gate evaluated inside the
   compile runner. Its thresholds and evidence requirements are those already set by
   [[add-llm-radar-input-enrichment]]: evidence must be short verbatim excerpts from the supplied
   source text, and insufficient evidence must lower confidence rather than invent a value.
4. Articles failing the gate are **held in `Inputs/`, uncompiled**, and listed in the run's review
   artifact. They do not enter `entities/article/`.
5. Issue tags continue to be constrained to the existing production tag inventory and continue to
   be preserved in the compiled body's `## Issue Tags` section and as topic links, per
   [[add-enriched-input-database-bridge]]. The article YAML `tags` registry is unchanged and
   remains reserved for `#source` and `#saf`.

## Consequences

- The standalone `--apply` review gate is deliberately given up. Review moves from "enrich, inspect
  the artifact, then apply" to "compile, with failures held back and listed". A wrong-but-confident
  classification now lands in a compiled note rather than waiting in an artifact, so the held-back
  queue and the assessment artifact become the review surface.
- Cross-checking by model disagreement is lost for the fields still classified by model. Confidence
  and evidence remain the only automatic gate.
- Per-article model calls drop from two to one, and further for every article whose outlet the
  index already knows.
- `scripts/enrich_radar_inputs.py` is retired; [[add-llm-radar-input-enrichment]] is superseded by
  this note.
- Outlet metadata becomes deterministic and auditable against the vault instead of model-derived,
  and improves as the outlet domain grows.
- Original upstream input values remain untouched until an article compiles successfully.
