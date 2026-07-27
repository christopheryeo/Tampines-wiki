---
type: test-fixture
name: golden-query-cases
target: scripts/query_procedure.md
status: draft
vault_snapshot: 2026-07-24
snapshot_notes: >
  Expected answers below are the authoritative reference as of the 2026-07-24
  vault state (search/catalog.md note_count 21; appointments/catalog.md note_count 10;
  chan-chun-sing mentionCount 2014). Count-sensitive fields are marked per case.
  Re-baseline after any ingestion that changes a cited entity's Coverage.
---

# Golden Q&A Test Set — Query Procedure

A fixed set of reference questions for regression-testing `scripts/query_procedure.md`.
Each case is "golden": its `Expected answer` is treated as authoritative, so any drift in the
answer substance, the resolved-entity set, or the cited sources signals a regression in the
procedure — not a wrong expectation.

Every case is grounded in an already-answered, verified entry in `entities/search/` (or, for the
appointment case, the appointments catalog + note). The `Grounded in` field names that source of
truth so a reviewer can confirm the expectation independently.

**How to grade.** Match on *substance and structure*, not exact wording:

- **Answer** — the listed facts must all appear; no fabricated facts beyond what the grounding note
  supports; delivery obeys Step 5 item 21 (no wiki/corpus references, no appended citations in the
  user-facing text).
- **Entities resolved** — must equal the expected set (order-independent). Missing or extra entities
  both fail.
- **Sources** — the expected article/source IDs must be the ones the answer rests on. A superset that
  pulls in unrelated articles fails (Step 3 is "ranked not exhaustive").
- **Path** — the procedure must reach the answer via the expected path (e.g. a Summary-only case must
  not blanket-read Coverage; the cache-hit case must short-circuit at Step 0).

Each case's pass/fail is meant to be visible in the run output, so this set can also serve as a
`/goal` completion condition (e.g. "all golden query cases pass").

---

## Case 1 — Single-entity, Summary-only (Step 2 stops at Summary)

- **Question (verbatim):** Who is Chan Chun Sing?
- **Path exercised:** Step 1 resolve → Step 2 read `## Summary` only → Step 5 answer. **Must NOT**
  expand into `## Coverage` articles (Step 3 item 14 — Summary already answers a basic identity/role
  question).
- **Expected answer (substance):** Singapore's Defence Minister, concurrently Coordinating Minister
  for Public Services. Prefers direct, hands-on engagement (personally phoned Qatar's defence
  minister over the Strait of Hormuz blockade risk, Mar 2026); decades-long friendship with
  Indonesia's defence minister Sjafrie Sjamsoeddin. Recent work spans regional defence diplomacy
  (19th ADMM in KL, 26th ACAMM opening speech, Navy@Vivo), procurement (G550, MMRC 2), and Public
  Services duties (national water resilience). Rhetoric is values-driven/long-horizon.
- **Expected entities resolved:** `chan-chun-sing`
- **Expected sources:** `757551`
- **Grounded in:** `entities/search/who-is-chan-chun-sing-bad9ad92.md`
- **Snapshot-sensitive:** Yes — answered from Summary at mentionCount 2014. Substance is stable, but
  re-confirm if the Summary is recompiled.

## Case 2 — Single-entity with Coverage expansion (Step 3 article reads)

- **Question (verbatim):** Tell me more about RSN
- **Path exercised:** Step 1 resolve (acronym → `rsn`) → Step 2 Summary + Coverage → Step 3 rank and
  read the backing articles. A multi-facet answer that cites specific articles, unlike Case 1.
- **Expected answer (substance):** RSN = Republic of Singapore Navy, a SAF service branch. Covers:
  leadership (Chief of Navy RADM Sean Wat; father-and-son submariners ME1 Kee Jie En / SLTC (Ret)
  Kee Kian Peng; 7th Flotilla family support), modernisation (Digital Transformation Office low-code,
  Mar 2026), fleet & industry (TKMS + ST Engineering submarine-maintenance-hub MoU for 218SG fleet;
  Genasys ~US$2.0M USV comms order), people pipeline (30 officers of the 253-cadet commissioning; US
  CNO ADM Daryl Caudle visit), and heritage (Navy Museum; DSTA 26th-anniversary retrospective).
- **Expected entities resolved:** `rsn`
- **Expected sources:** `793259`, `801234`, `1008066`, `1029768`, `1004835`, `1014225`, `1032776`,
  `1020721`, `1015627`
- **Grounded in:** `entities/search/tell-me-more-about-rsn-fba9527a.md`
- **Snapshot-sensitive:** Yes — Coverage-count sensitive (mentionCount 8 at answer time). New RSN
  articles would legitimately extend the source list; re-baseline rather than fail in that case.

## Case 3 — Multi-entity relationship (Step 4 cross-entity traversal)

- **Question (verbatim):** How is Lawrence Wong related to Gan Kim Yong?
- **Path exercised:** Step 1 resolve both people → Step 2 read both Summaries/Coverage → Step 3 open
  the single shared article → Step 4 check both notes' `## Related Entities` (finds no direct
  cross-link). Tests that a relationship query traverses *both* entities and reports the shared-source
  overlap, not just one entity's view.
- **Expected answer (substance):** Two connections only — (1) both senior members of the same
  government (Wong = PM & Finance Minister; Gan = DPM), both resolving to `singapore`; (2) they
  co-appear in one article (993332, SCMP, 2 Mar 2026, "Singapore strives to remain equidistant amid
  US-China rivalry"), in parallel not direct interaction (Wong cited re Chinese-language AI
  disinformation; Gan on monitoring the Middle East conflict / reassessing the 2-4% GDP forecast).
  No direct link beyond that shared mention; neither note lists the other in Related Entities.
- **Expected entities resolved:** `lawrence-wong`, `gan-kim-yong` (context: `singapore`)
- **Expected sources:** `993332`
- **Grounded in:** `entities/search/how-is-lawrence-wong-related-to-gan-kim-yong-8d7e52de.md`
- **Snapshot-sensitive:** Moderate — a future article co-mentioning both would change the answer;
  re-baseline on new co-appearances.

## Case 4 — Roster / list query (domain roster path + Producing a List)

- **Question (verbatim):** Give me a list of people who are related to defense
- **Path exercised:** List-type path (not entity-traversal) — resolve the *domain*/anchor
  (`defence`), build the roster from its Related Entities > People, render per the explicit format
  request. Tests that roster requests do NOT fall into the Steps 2–4 inbound-Coverage flow.
- **Expected answer (substance):** The 159 people linked as Related Entities on `defence`, rendered
  as a numbered list. Provenance caveat must be preserved: this roster comes from `defence.md`'s
  manually populated Related Entities, weaker provenance than a Coverage-backed roster (no
  article-level citations).
- **Expected entities resolved:** `defence` (Related Entities > People, 159 entries)
- **Expected sources:** none (roster drawn from `defence.md` Related Entities, not article cascade)
- **Grounded in:** `entities/search/give-me-a-list-of-people-related-to-defense-6e3ef48d.md`
- **Snapshot-sensitive:** Yes — the count (159) is exact-as-of-snapshot. Treat a changed count as
  re-baseline, not regression, unless the roster path itself broke.

## Case 5 — Cache hit / reworded repeat (Step 0 short-circuit)

- **Question (verbatim):** What did people say about Seletar Aerospace Park?
- **Path exercised:** Step 0 only. Must recognise this as a relevant, fresh match for the cached
  `what was said about Seletar Aerospace Park?`, return that answer, increment its `reuseCount`, and
  **stop** — no re-resolution, no new article reads, no new cache entry (Steps 1–7 must NOT run).
  This is Worked Example C in the procedure.
- **Expected answer (substance):** Nothing was really "said" about it — it's a location, not a
  subject of remarks. The one thing on record: Princess Anne visited the Airbus Asia Training Centre
  at Seletar Aerospace Park on 13 Nov 2025 during her two-day UK state visit, between meeting PM
  Lawrence Wong at the Istana and visiting Rolls-Royce's Singapore facilities.
- **Expected entities resolved:** `seletar-aerospace-park` (from the cached entry; no fresh
  resolution performed)
- **Expected sources:** `782384`
- **Expected side effect:** `reuseCount` on the cached entry increments (was 1 at snapshot); a
  `log.md` entry is appended; **no** new `entities/search/` note is created.
- **Grounded in:** `entities/search/what-was-said-about-seletar-aerospace-park-2afdbe03.md`
- **Snapshot-sensitive:** Freshness check keys on `seletar-aerospace-park` mentionCount (1 at
  snapshot). If that grows, the correct behaviour flips to a cache *miss* — which is itself a valid
  thing to assert once the staleness rule is formalised.

## Case 6 — Appointment / holder question (appointments Holders path)

- **Question (verbatim):** Who is the current CDF?
- **Path exercised:** Appointment path — resolve bare acronym `CDF` against the `acronyms` column in
  `appointments/catalog.md` → open `cdf.md` → read `## Holders` / `currentHolder`. Must NOT attempt a
  Summary/Coverage traversal (appointment notes have neither).
- **Expected answer (substance):** VADM Aaron Beng — the current Chief of Defence Force (as of
  2026-03-31), the professional head of the SAF.
- **Expected entities resolved:** `cdf` → `aaron-beng`
- **Expected sources:** MINDEF official pages backing the note (not an article cascade); no article ID
  required.
- **Grounded in:** `entities/appointments/cdf.md` (currentHolder: aaron-beng) +
  `appointments/catalog.md`
- **Snapshot-sensitive:** Yes — holder-sensitive. Freshness keys on the appointment's
  `## Holders`/`currentHolder` (procedure Step 0 item 3), not on a mentionCount.

## Case 7 — Null result (entity resolves, but no remarks on the asked topic)

- **Question (verbatim):** What did the PS say about defence?
- **Path exercised:** Resolve `PS` → Permanent Secretary (Defence) office (holder changed within the
  window: Chan Heng Kee → Joseph Leong) → read Coverage → find no defence remarks. Tests that "entity
  exists but says nothing on topic" returns a clean null answer, not a fabricated one or a fallback to
  grepping the corpus.
- **Expected answer (substance):** Nothing on record of the PS (Defence) making any statement about
  defence. The only coverage naming either holder is the March 2026 civil-service reshuffle (Head of
  Civil Service Leo Yip's 1 Apr 2026 retirement and associated permanent-secretary changes) — which
  reports the post, not any remarks by the office-holder on defence.
- **Expected entities resolved:** `ps-defence`, `joseph-leong`, `chan-heng-kee`
- **Expected sources:** `1004259`
- **Grounded in:** `entities/search/what-did-the-ps-say-about-defence-255a9ec2.md`
- **Snapshot-sensitive:** Moderate — would change only if a holder makes an on-record defence remark.

## Case 8 — Negative existence check (cross-check issues catalog before answering)

- **Question (verbatim):** So there is no cyber security breach in your wiki?
- **Path exercised:** Existence/negative check — confirm no `entities/issues/` note exists (check
  `issues/catalog.md` directly) while still surfacing the org-level coverage that *does* exist. Tests
  that the procedure distinguishes "no filed issue" from "nothing in the corpus," and doesn't overstate
  absence.
- **Expected answer (substance):** No filed incident/issue for a breach, but the corpus does reference
  a real attack: Mar 2026, cyber-espionage group UNC3886 targeted Singapore's critical information
  infrastructure. Coverage is entirely about the government response, not the breach — CSA tasked
  MINDEF's CSIT with home-grown threat-detection tools, already deployed in selected CII systems with a
  progressive rollout. Single wave, factual/neutral framing, wire-syndicated (Yahoo HK/MY/SG/TW) off
  the Straits Times report; never recurred or escalated, so it never crossed into the issue radar's
  watchlist. Sits as organisation-level coverage (CSA, CSIT notes), not as an issue.
- **Expected entities resolved:** `csa`, `csit`, `sectoral-cyber-defence-team`, `mindef`
- **Expected sources:** `993312`, `993314`, `993316`, `993318`, `993320`, `994160`
- **Grounded in:** `entities/search/so-there-is-no-cyber-security-breach-09254682.md`
- **Snapshot-sensitive:** Yes — depends on no cyber issue existing in `issues/catalog.md`. If one is
  ever filed, the correct answer changes; re-baseline.

---

## Coverage map (which path each case guards)

| # | Question | Path guarded |
|---|---|---|
| 1 | Who is Chan Chun Sing? | Single-entity, Summary-only (no Coverage expansion) |
| 2 | Tell me more about RSN | Single-entity with Coverage expansion (Step 3) |
| 3 | How is Lawrence Wong related to Gan Kim Yong? | Multi-entity relationship (Step 4 traversal) |
| 4 | Give me a list of people related to defense | Roster / list path + Producing a List |
| 5 | What did people say about Seletar Aerospace Park? | Cache hit / Step 0 short-circuit |
| 6 | Who is the current CDF? | Appointment / holder (Holders, not Coverage) |
| 7 | What did the PS say about defence? | Null result (resolves, no on-topic remarks) |
| 8 | So there is no cyber security breach in your wiki? | Negative existence check vs issues catalog |

## Notes for building the runner

- Grading is substance-based, so an exact string diff will produce false failures. Compare the
  expected fact list and the resolved-entity / source-ID sets, and separately assert the delivery
  rules (no wiki references, no appended citations).
- Cases 1, 2, 4, 6, 8 are count-/holder-sensitive. A runner should read the live count from the
  relevant `catalog.md` and, when it has moved past this file's `vault_snapshot`, flag the case as
  **re-baseline needed** rather than **failed** — a moved count is new data, not a broken procedure.
- Case 5 asserts a *side effect* (reuseCount increment, no new note). The runner needs to inspect the
  cache entry before/after, not just the answer text.
