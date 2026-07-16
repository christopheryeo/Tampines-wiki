---
decisionId: add-appointments-domain
title: Add Appointments domain to model MINDEF/SAF role-acronyms as time-varying offices
status: accepted
date: 2026-07-09
affects: [entities/appointments, entities/people]
---

## Context
MINDEF/SAF coverage routinely refers to leaders by role-acronym — CDF, PS(Def), CNV, COA, CAF, CDI, SMS(Def), MOS(Def) — often bare, with no name attached ("CDF said...", "PS approved..."). Until now these acronyms lived only inside each person's `aliases` as combined tokens (`CDF Aaron Beng`, `CNV Sean Wat`). That binding has two failure modes:

1. **No home for a bare acronym.** A standalone "CDF" or "PS" matches an alias only fuzzily and ambiguously.
2. **Time-instability.** An appointment is held by different people over time; binding the acronym to one person mis-resolves the moment the office changes hands. This corpus already contains such a handover — PS(Defence) passed from Chan Heng Kee (promoted to Head of Civil Service) to Joseph Leong within the Nov 2025 – Mar 2026 window (org page, last updated 31 Mar 2026). A person-bound "PS" alias would resolve every article to one holder regardless of date.

The monitoring archive spans a fixed historical window, so correct resolution *as at the article date* is a first-class requirement, not a nicety.

## Decision
1. Create a new knowledge domain `entities/appointments/` — one note per office, keyed by acronym (`appointmentId`), with a frozen YAML registry defined in its `index.md` (appointmentId, displayName, acronyms, org, country, currentHolder, aliases, tags). This note authorizes that registry's initial freeze.
2. Model **holders as dated `[[wikilinks]]` in the note body**, newest first (§3 — multi-value, time-varying relationships never belong in YAML). `currentHolder` is a YAML convenience pointer only.
3. Adopt the **resolver rule**: a bare role-acronym or bald title with no name resolves acronym -> appointment note -> the holder whose date range covers the article's `publishedDate`; ambiguous dates resolve to `currentHolder` and are flagged.
4. **Person notes keep name+rank aliases only** (`VADM Aaron Beng`) and drop bare role-acronyms (`CDF`, `PS`) — the bare acronym now belongs to the appointment. (Refactor of existing person aliases is deferred; not part of this build.)
5. Appointment notes are **not** created by cascade. Holder facts are reference data from official MINDEF pages (organisation, leadership biographies), cited with a fetch timestamp per §2's landed-source path.

## Consequences
- New domain scaffolded with `index.md`. Initial population: the 10 core MINDEF SG offices (Minister for Defence, SMS(Def), MOS(Def), PS(Def), PS(Def Dev), CDF, COA, CNV, CAF, CDI).
- "Who held office X at date D?" and "who is X now?" become queryable from the appointment note alone.
- MINDEF/SAF appointments are `#saf`-sensitive — excluded from external/demo export (§10).
- Procedure carve-outs applied (2026-07-09): `entity_cascade_procedure.md` now flags `appointments` as a non-cascade domain (no `## Coverage`/`mentionCount`, never run through `patch_coverage.py`), and `query_procedure.md` documents holder queries via `## Holders`/`currentHolder`. Impact review of all `scripts/` confirmed no code changes needed — `patch_coverage.py`'s `ValueError` on an unknown domain is the correct guard and stays strict.
- Deferred: (a) strip bare acronyms from existing person `aliases`; (b) extend the set to warrant-officer appointments (SAF Sergeant Major, service SMs) and other MINDEF deputy-secretary roles; (c) rebuild `index/wiki.db` so the domain is queryable via SQL (no build script in `scripts/` — runs via the nightly routine).
