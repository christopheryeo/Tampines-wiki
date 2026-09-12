---
type: operating-plan
name: wiki-quality-check
status: ready-for-goal-run
last_updated: 2026-09-07
---

# Tampines Wiki Detailed Quality Check and Remediation Plan

Saving this plan does not execute it. Run it only when Christopher starts the quality-check goal.

## 1. Objectives and scope

Establish whether the wiki is structurally sound, accurately represents its preserved sources, supports reliable retrieval, and has consistent generated outputs. Correct defects where evidence is conclusive and record unresolved cases explicitly.

The run will:

1. Validate every compiled article and every active entity domain mechanically.
2. Verify article-to-entity relationships, Coverage backlinks, counts, and entity identity.
3. Review a reproducible sample of 200 articles against preserved evidence, plus all cases flagged for content review.
4. Check catalogs, available local indexes, dashboard data, saved answers, and existing issue assessments.
5. Repair mechanical defects and evidence-backed content errors, then verify the resulting wiki.
6. Produce a reproducible audit trail, before/after measurements, and an actionable unresolved-defect register.

Authorized remediation includes deterministic repairs and content corrections conclusively supported by preserved evidence. Ambiguous identity merges, unsupported factual additions, destructive deletions, schema changes, and new interpretations remain unresolved for review.

Preserve `raw/`, original identifiers, source evidence, and historical log entries. Do not requeue held articles, ingest new articles, change production/UAT databases, deploy applications, or generate new operational radar assessments.

Markdown remains the source of truth. No live-web enrichment or model-background factual additions.


User clarification: Duplicate stories from different media outlets are valid separate records and must be preserved, including syndicated or identical text. Duplicate-identity review concerns entity identities; story similarity alone is not a defect or a reason to merge or delete article records.


User scope clarification: The audit does not fact-check whether published news reports are true. Content checks verify faithful representation of retained reports: summaries, quotations, attribution, entity relationships and classifications. Final reporting groups the work into five checks: faithful summaries; correct relationships; consistent classifications; current generated outputs; and end-to-end verification. Existing preservation rules and evidence-based review scope still apply.

## 2. Execution procedure

### A. Establish the baseline

- Read the current README, agent instructions, development handoff, frozen schemas, domain manuals, and relevant cascade/query procedures.
- Record a unique run ID, SGT start time, code revision, working-tree changes, tool/runtime versions, and exact scope.
- Inventory compiled articles by month and source type; entity notes by domain; generated outputs; and available preserved source records.
- Count loose intake files freshly with a direct, depth-one listing excluding metadata. Keep intake and holds separate from compiled-corpus totals.
- Save a manifest of paths and content hashes for audited files. Record pre-existing changes without overwriting them.
- Before repairs, retain exact before-images of every affected file, including ignored article files that Git cannot restore.
- Store detailed local evidence under `runs/<SGT-date>/artifacts/<run-id>/`. Keep canonical operation receipts in the date directory, following the existing receipt format.

### B. Run full-corpus structural checks

Use the existing validators as the starting point:

```bash
python3 scripts/article_quality.py --check --json --no-run-log
python3 scripts/check_links.py --no-run-log
python3 scripts/validate_tags.py --articles
python3 scripts/validate_issues.py
python3 scripts/repair_stranded_coverage.py
```

The last command must run in its default dry-run mode during diagnosis. Verify current command behavior before execution.

Validate:

- Frontmatter syntax, required fields, types, enums, IDs, filenames, publication-month placement, and required sections.
- Duplicate source IDs and compiled/intake overlap, classifying retained hold evidence separately from accidental duplication.
- Broken, malformed, ambiguous, alias-only, and noncanonical wikilinks.
- Tag identity, aliases, assignments, and applicable status rules.
- Every entity domain against its own frozen registry, including domains not fully covered by existing validators.
- Coverage labels, misplaced backlinks, duplicate relationships, and orphan notes.

Existing validator success is not sufficient by itself. Capture complete findings where tools truncate output, and supplement missing checks with bounded audit tooling. Preserve current schemas and interfaces.

### C. Reconcile the relationship graph

Build an independent inventory of article-to-entity relationships from canonical article metadata and body links.

For each domain:

- Compare expected relationships with entity Coverage entries.
- Identify missing, duplicate, dangling, and unsupported backlinks.
- Recompute counts using that domain's documented semantics; do not assume every count equals the number of Coverage lines.
- Check ambiguous names and aliases for possible identity collisions.
- Verify dated appointment references against preserved holder evidence.
- Distinguish legitimate entity-only relationships and zero-coverage notes from defects.

Existing scripts must perform supported bookkeeping repairs, especially Coverage updates. Do not reimplement `patch_coverage.py` mechanics inline.

### D. Review source accuracy

Select 200 distinct compiled articles, or the entire corpus if smaller.

Use a reproducible selection method:

- Allocate 100 articles proportionally across publication-month/source-type groups, ensuring each nonempty group is represented where the allocation permits.
- Select 100 further articles by risk: structural warnings, missing source mappings, sparse or unusually short summaries, dense entity linking, and previously repaired batches.
- Resolve allocation ties and ordering using a fixed SHA-256 hash of `tampines-wiki-qc-v1` plus the article's relative path.
- Fill any unused risk allocation from the remaining corpus using the same ordering.
- Save the selected manifest, group counts, and selection reasons.

For each selected article, compare the compiled note with available preserved evidence for:

- Identity, publication date, outlet, and provenance.
- Accuracy and completeness of the summary.
- Names, roles, dates, quantities, quotations, and key qualifications.
- Material omissions and unsupported additions.
- Entity selection and disambiguation.
- Sentiment, tone, event type, and topic/tag choices against the applicable definitions.

Classify each review as accurate, defective, or unverifiable. Missing source evidence is never a pass.

Review every additional article flagged for a substantive content concern. When a substantive defect appears, review 50 additional articles from the same identifiable ingest batch, or month/source group if no batch mapping exists. If the same defect recurs, inspect the whole affected group. Deduplicate expanded selections.

Review linked entity descriptions affected by these findings, all identity-collision candidates, and all existing issue assessments. Correct factual content only when preserved evidence resolves the issue conclusively.

### E. Verify derived outputs and retrieval

- Generate comparison outputs in isolation before replacing local derived artifacts.
- Compare catalog membership and key values against canonical notes; detect missing, extra, and duplicate rows.
- Check available local index and dashboard builders for missing records, incorrect relationships, stale values, and documented exclusions.
- Rebuild affected derived outputs using their established generators after repairs.
- If a builder or underlying source is unavailable, identify the exact unchecked surface rather than inventing a replacement.

For retrieval:

- Run existing golden query cases against the current corpus.
- Add 12 reproducible audit cases: two each for entity identity, chronological coverage, complete rosters/counts, cross-entity relationships, absent evidence, and search-cache freshness.
- Select concrete subjects from the frozen manifest and record independently checked expected results before evaluating answers.
- Require resolvable citations, source support, correct ordering/counts, and explicit treatment of insufficient evidence.
- Keep audit query outputs in run artifacts so testing does not create misleading user-search history.

For existing issues, verify schema, citations, Coverage, score/status consistency, dated catalysts, and supporting assessments. Leave radar recomputation and database comparisons to the separate radar-quality workflow.

### F. Remediate and verify

For each finding, record:

- Stable finding ID, severity, affected paths, and defect class.
- Observed and expected behavior.
- Evidence and proposed correction.
- Applied changes, before/after hashes, and verification result.
- Remaining uncertainty or required decision.

Severity:

- Critical: destructive behavior, source corruption, or broadly misleading results.
- Major: unsupported substantive claims, wrong identities, missing relationships affecting retrieval, or invalid canonical records.
- Minor: localized formatting or advisory defects without material factual impact.

Preview bulk repairs and validate the first 20 affected notes, or all notes if fewer, before expanding to the full affected set.

Use existing repair utilities only after reviewing their current behavior and scope. For additional tooling, add focused regression tests covering the actual defect and preservation of unaffected content.

Append audit entries; never rewrite historical logs. Any identity consolidation must retain provenance and resolve all inbound references; leave uncertain or destructive consolidations for review.

After remediation, rerun the full structural and graph checks, all affected semantic reviews, derived-output comparisons, and retrieval cases. Run the repository test suite once for final tooling verification; repeat only where subsequent changes justify it.

## 3. End conditions and breakout conditions

### Successful end conditions

Mark the wiki PASS only when:

1. Every planned audit surface has been evaluated.
2. Full-corpus validators report zero hard failures.
3. Relationship and count reconciliation has no unexplained discrepancies.
4. The 200-article review and all required expansions are complete.
5. All reviewed substantive defects are corrected and reverified.
6. Every warning has a documented disposition; none is silently ignored.
7. Derived outputs reconcile and retrieval cases pass.
8. No unresolved Critical or Major findings remain.
9. Source preservation and noninterference checks pass.
10. Final evidence, repair records, receipts, and handoff are complete.

A sampled PASS applies to the stated review scope; it does not certify that every article was semantically reviewed.

Use CONDITIONAL PASS only for remaining Minor findings or explicit verification limitations without a known Critical/Major defect. Use FAIL when known hard errors or substantive defects remain.

Goal completion is distinct from wiki quality: the audit goal can finish with a documented FAIL or CONDITIONAL PASS once all authorized, feasible work is complete and every remainder has an exact blocker and next action. Never manufacture a clean result to finish the goal.

### Breakout conditions

| Trigger | Required response |
|---|---|
| Concurrent changes invalidate the manifest | Pause affected writes, record the drift, and rebaseline affected files once. If changes continue, defer that surface and continue independent checks. |
| Repair produces unrelated changes or damages provenance | Stop that repair batch immediately. Restore only the run's own changes where safe, preserve evidence, and diagnose before resuming. |
| Source is absent, contradictory, or insufficient | Mark the finding unverifiable or ambiguous. Continue other work; do not guess. |
| Fix requires schema changes, destructive consolidation, held-input recovery, external disclosure, or database writes | Leave the item unresolved with the exact required decision. Continue authorized local work. |
| Missing dependency, unavailable builder, access restriction, or tool failure | Record command, error, impact, and safe alternatives attempted. Do not count the check as passed. |
| The same defect survives two repair-and-recheck cycles | Stop automatic retries for that defect class, preserve the reproducer, and continue unaffected classes. |
| Explicit execution budget is reached | Save a resumable checkpoint, completed coverage, remaining queue, and limitations. Do not claim successful completion. |

A local breakout does not stop the entire audit when useful independent work remains. If a future goal becomes genuinely blocked, use the goal tool's applicable blocked-status rules.

## 4. Deliverables and reporting

Produce:

- `quality-report.md`: objectives, scope, before/after metrics, quality verdict, limitations, and highest-priority findings.
- `findings.json` and a readable findings table containing every finding and its disposition.
- Corpus and sample manifests, source-review evidence, complete validator outputs, query expectations/results, and before-images.
- A remediation ledger and resumable checkpoint.
- Total elapsed time, files/articles checked, source reviews completed, repairs applied, and unresolved counts. Report structural throughput and semantic-review throughput separately.

No public API or frozen-schema changes are planned. Supplemental audit tools and regression tests are permitted where needed to close demonstrated validation gaps.

For tracked changes, follow the project's branch/PR handoff rules, preserve unrelated work, and never push directly to `main`. Include material commands, counts, outcomes, failures, timing, and limitations in the relevant PR. Do not create Now/Next entries or claim unmerged work as shipped.

## 5. Reusable goal prompt

> Complete the Tampines Wiki quality check and remediation according to `scripts/wiki_quality_check_plan.md`. Follow its objectives, scope, end conditions, breakout conditions, and reporting requirements. Continue until all authorized, feasible work is complete, and report any unresolved blockers explicitly.
