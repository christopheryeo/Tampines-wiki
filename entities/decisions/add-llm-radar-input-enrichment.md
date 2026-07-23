---
decisionId: add-llm-radar-input-enrichment
title: Add evidence-backed LLM enrichment for missing radar inputs
status: superseded
date: 2026-07-23
affects: [scripts, Inputs, issue-radar]
---

## Context
New loose articles arrived with usable titles, summaries, URLs and observation dates, but empty
tags, outlets and countries. Their category, tone and event type were also uniform defaults. Those
values are insufficient for the issue radar's tag, breadth, institutional, opinionated and
unfacilitated signals.

## Decision
Add a pre-compile enrichment step that constrains issue tags to the existing production tag
inventory, derives outlet metadata from the source URL, and uses two independent structured model
passes for institutional category, tone and event type. Each model pass must provide evidence and
confidence. Only agreeing results above the configured threshold may be applied automatically;
all other results go to review. The assessment artifact retains provenance and model/prompt
versions. It does not store the API key.

## Superseded by

Superseded on 2026-07-23 by [[fold-enrichment-into-compile]], which moves enrichment inside the
compile runner, resolves outlet metadata from a generated `entities/outlet/` index rather than from
the model, and replaces the two-pass agreement check with a single-pass confidence gate. The
evidence and confidence requirements set out below remain binding on that gate.

## Consequences
- Original upstream values remain untouched unless the enrichment runner is invoked with
  `--apply`.
- Generated values use only fields already registered in the input article schema; classification
  evidence and confidence remain in a separate run artifact.
- Low-confidence or disagreeing classifications are never silently converted into radar inputs.
- The enriched input still requires a separate reviewed load into the canonical product tables
  before `issue_radar.py` can use it.
