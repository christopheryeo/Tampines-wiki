---
type: procedure
name: issue-radar
status: active
last_updated: 2026-09-17
---

# Issue Radar Procedure

Turns deterministic radar flags into filed, cited issue assessments in `entities/issues/`. The
split follows the vault's core division of labour: `scripts/issue_radar.py` does the counting from
read-only canonical product tables (velocity, breadth, institutional attachment, recurrence — mechanical, hindsight-free); this
procedure does the judgment (clustering, ramification, catalysts, posture). Neither replaces the
other: the radar over-generates by design (~20x at tag level), and the judgment pass must never
invent signals the radar did not report.

**Cadence:** run after every ingest/cascade batch, before the nightly catalog rebuild. A pass with
no new flags still updates `lastScored` on every active (`hot`/`warm`/`watch`) issue. A completed
ingest receipt without a same-or-later radar run receipt is an incomplete operating cycle, not an
all-clear.

**Hard rules (inherited from the cascade procedure):** piped `[[real-filename|Display]]` links
only; no enrichment from live web or model background knowledge — every claim, and especially
every catalyst date, must be quoted from a citing article already in the vault; quote flow-list
values beginning with `#`; append-only logs.

## Step 1 — Run the signal layer (mechanical)

1. First run `python3 scripts/validate_tags.py --articles` and require a pass. Then run against UAT
   while developing or validating:
   `python3 scripts/issue_radar.py --source uat --defaults-file <read-only-client.cnf>`.
   Run against production only with an approved read-only account (preferably a replica):
   `python3 scripts/issue_radar.py --source production --defaults-file <read-only-client.cnf>`.
   Add `--asof <date>` for reconstruction. Capture every flag at WARM or above; WATCH flags are
   optional at analyst discretion. The script never writes to either database.
2. Freeze the source input at the same `--asof` date by adding
   `--input-manifest-output <uat-input-manifest.json>` to the radar command. Build the Markdown
   manifest with `review_issue_radar_run.py --manifest-output <markdown-manifest.json>`, then run
   `python3 scripts/verify_issue_radar_parity.py --uat-manifest <uat-input-manifest.json>
   --markdown-manifest <markdown-manifest.json> --output <parity.json>` and require `PASS` before
   accepting scores for clustering or filing. This validates source-ID article, tag-multiset, and
   coverage-multiset parity. Stop on an unexplained difference; a local/UAT count mismatch is not
   a harmless aggregate warning.
3. Do not edit, reweight, or suppress the script's output by hand. If the thresholds seem wrong,
   that is a Decision-note conversation, not an in-pass adjustment.
4. Save both `--json-output` and `--text-output`, repeat the run, and require identical hashes.
   Independently verify the structured output with
   `python3 scripts/verify_issue_radar_output.py <radar.json> --output <verification.json>`.
   Any tag-eligibility, assignment, projection, or event-family change invalidates this checkpoint:
   freeze new inputs and rerun it before clustering.

## Step 2 — Cluster flags into issue objects (judgment)

5. Build the complete flag-disposition ledger, non-transitive article/entity/topic-overlap clusters,
   event-family composition, coherence status, compiled
   evidence pack, and frozen article manifest:
   `python3 scripts/review_issue_radar_run.py --radar-json <radar.json> --json-output
   <review-pack.json> --markdown-output <review-pack.md> --manifest-output <manifest.json>`.
   This helper never uses tag-name similarity and never decides ramification.
6. Retrieve the complete current roster by following `scripts/issues_list.md` with
   `scope: all`, `format: json`, and `verified: true`; stop if its `complete` value is false. For
   each flag, decide: does this tag belong to an issue already on the watchlist? Updating an
   existing note is the default; minting a new issue is the exception. (Backtest reference:
   `amos yee`, `enlistment act`, `cmpb`, `deportation`, `fines`, `chicago` were six flags but one
   issue.)
7. To test whether two flags are one issue, open a sample of each flag's recent citing articles
   (via the shared article database or the article catalog) and check overlap of articles and entities — shared
   articles means same issue. Never cluster on tag-name similarity alone.
8. Require both meaningful shared article/entity/topic evidence and a coherent event family. A
   generic descriptor or a named individual that crosses unrelated stories is non-cohesive, not an
   issue candidate; route it to a shadow-review or dismissal record with its evidence.
9. Name the issue by its risk, not its keyword (`ns-enforcement-enlistment-act`, not `amos-yee` —
   people are carriers of issues, not issues).
10. When article content must remain local, record any accepted judgment overrides in a run-specific
   decision JSON and run `local_issue_radar_review.py`. Its two local rubric passes may retain or
   dismiss candidates but cannot surface an alert without the separate, evidence-cited decision
   record. Do not transmit compiled article content to an external model without explicit approval.

## Step 3 — Ramification questionnaire (judgment, answered only from vault content)

11. For each issue object, answer in writing, citing articles:
   a. **Forced response** — if coverage doubles, who must respond: a minister, MINDEF, an agency,
      or no one? (Institutional-category migration is the strongest single predictor.)
   b. **Fault lines** — does it touch a standing sensitivity: NS fairness, sovereignty, foreign-
      policy neutrality, race/religion, procurement probity?
   c. **Catalysts** — do the citing articles mention future dated events (court dates, parliament
      sittings, scheduled visits, exercises, anniversaries)? Extract each with its date and source
      link. An accelerating issue with a known catalyst is schedulable risk.
   d. **Irreversible positions** — has anyone senior taken an on-record stance that constrains
      future response?
   e. **Migration** — is a foreign story acquiring domestic institutional categories (the US-Iran
      → repatriation pattern)?
12. Assign `ramification`: `severe` (multiple fault lines or forced minister-level response),
   `high` (one fault line, institutional response likely), `moderate` (contained but recurring),
   `low` (benign shape). Acceleration without ramification is a dismissal, not an alert.

## Step 4 — File (mechanical bookkeeping + judgment prose)

13. Create or update the issue note per the `entities/issues/index.md` registry and template:
   frontmatter fields from the radar output (`score`, `status` from tier, `clusterTags`,
   `firstFlagged` preserved from first filing, `lastScored` = today); replace `## Signal Scores`
   with the latest basis-tag snapshot (evaluation date, tag, tier, recent volume, source artifact,
   six raw components, weights, contributions, and total); append `## Signals`, never rewrite it;
   and write `## Assessment`, `## Catalysts`, `## Posture` per Step 3. State explicitly that the
   component snapshot is tag-level, not an issue-wide recalculation. For a dismissed issue with no
   current qualifying flag, retain and label its latest qualifying snapshot rather than inventing
   zero components.
14. Benign flags: file with `status: dismissed` and a one-line reason. Dismissals are calibration
   data — never deleted, and a dismissed issue that re-flags later is reopened, not duplicated.
15. Append one `log.md` entry per issue touched (full timestamp, wikilink, action, reasoning).
16. Regenerate the domain catalog: `python3 scripts/generate_catalog.py issues`, then validate it
    with `python3 scripts/validate_issues.py`.

## Step 5 — Surface (delivery)

17. Follow `scripts/issues_list.md` with `scope: alertable` to retrieve the issues eligible
    for delivery, then report them in the domain's Producing a List order with plain-language "why"
    lines and catalysts. Everything else stays on the quiet watchlist. A radar that cries wolf gets
    muted — precision over recall at the alert layer, liberal filing at the watchlist layer.

## Known limits

- Detects percolating issues only; exogenous shocks (bomb threats, sudden attacks) have no media
  precursors and must never be claimed as detectable.
- Tag-level candidates are a proxy; clustering quality is the judgment layer's responsibility.
- Corpus tone fields carry no negative-sentiment label; unfacilitated/opinionated share stands in.
