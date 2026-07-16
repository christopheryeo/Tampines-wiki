---
type: domain-index
domain: Appointments
subtype: appointment
status: active
last_updated: 2026-07-09
---

# Domain: Entities — Appointments

**Purpose:** the canonical record for every named **office / appointment** that MINDEF/SAF coverage refers to by a role-acronym — CDF, PS(Def), CNV, and the like. An appointment is a *stable* entity keyed by its acronym; the **person** who holds it is a time-varying relationship, not part of the appointment's identity. This domain gives the resolver a fixed anchor so that a bare acronym in an article ("CDF said...", "PS approved...") resolves to whoever held the office **at that article's date** — not to whoever happens to hold it now.

**Domain type:** `Entities` (knowledge domain, per §2)
**Note type:** `entity`, subtype `appointment`
**Status:** active schema, frozen by Decision [[add-appointments-domain]].

## Why this domain exists

Before this domain, role-acronyms were baked into each person's `aliases` as combined tokens (`CDF Aaron Beng`, `CNV Sean Wat`). That resolves a rank+name string fine, but it has no home for a **bare** acronym, and it binds the acronym to one person — which breaks the moment the office changes hands. This corpus already contains such a handover: **PS(Defence)** passed from [[chan-heng-kee|Chan Heng Kee]] (who moved to Head of Civil Service) to [[joseph-leong|Joseph Leong]] during the monitoring window. An appointment-keyed model resolves "PS said X" correctly on both sides of that handover and makes "who was PS(Def) in Jan 2026?" a queryable fact.

## Operating Instructions

1. **Appointment != person.** One note per office, keyed by acronym. The office is the stable entity; holders are dated links in the body, newest first. Never rename an appointment note when the holder changes — only add a holder line.
2. **Holders live in the body, not YAML (§3).** The `## Holders` section is a dated wikilink list. `currentHolder` in YAML is a convenience pointer only, kept in sync with the top holder line.
3. **Person notes keep name+rank aliases only.** Strip bare role-acronyms (`CDF`, `PS`, `CNV`) out of person `aliases`; a rank+name alias (`VADM Aaron Beng`) is fine. The bare acronym belongs to the appointment.
4. **Resolver rule.** When an article mentions a bare role-acronym or a bald title with no name, resolve: acronym -> appointment note -> the holder whose date range covers the article's `publishedDate`. If the date is ambiguous, resolve to `currentHolder` and flag for review.
5. **Provenance (§1 / §2).** Holder facts here are reference data drawn from official MINDEF pages (organisation, leadership biographies), cited with a fetch timestamp in each note's `## Source`. This is the sanctioned "landed external source" path, not article-cascade — appointment notes are **not** created by cascade.
6. **Sensitive-data flag (§10).** MINDEF/SAF appointments carry `#saf`; treat as deny-listed for external/demo export, routed through the sanitized derived copy only.
7. **Naming.** `appointmentId` = slugified office short-name (e.g. `cdf`, `ps-defence`). Filename = `<appointmentId>.md`.

## YAML registry (frozen — see [[add-appointments-domain]])

| Field | Type | Notes |
|---|---|---|
| appointmentId | string, unique | slugified office short-name — the stable id |
| displayName | string | human-readable office title |
| acronyms | list | every acronym / short form the office is cited by (the resolver's match keys) |
| org | string | owning organisation — resolves to an `[[organisations/<name>]]` note |
| country | string | associated country — resolves to a `[[country/<name>]]` note |
| currentHolder | string | `personId` of the current holder — convenience pointer, mirrors top of `## Holders` |
| aliases | list | full-title variants and honorific forms (non-acronym) |
| tags | list | `#saf` where applicable |

**Relationships live in the body:** holders (dated), owning org, and country are `[[wikilinks]]` in the note body, never multi-value YAML (§3).

## Producing a List

When asked for all appointments, render grouped by `org` (A–Z), then by seniority within each org where known (political office holders -> permanent secretaries -> SAF chiefs), else `displayName` A–Z. Render each as `- [[<appointmentId>|<displayName>]] — current: [[<currentHolder>]]`.

## Template

```
---
appointmentId: <slug>
displayName: <office title>
acronyms: [<ACRONYM>, ...]
org: <orgId>
country: <countryId>
currentHolder: <personId>
aliases: [<full-title variants>]
tags: ['#saf']
---

## Office
<one line on what the office is and where it sits>

## Holders
- <YYYY-MM> – present: [[<personId>|<Rank Name>]]
- <YYYY-MM> – <YYYY-MM>: [[<personId>|<Rank Name>]]

## Resolver Note
Bare "<ACRONYM>" / "<title>" with no name -> this office -> holder valid at the article date.

## Source
<official MINDEF page>, last updated <date>; fetched <date>.

## AI Context
Reference/glossary entity — `#saf`, excluded from external/demo export (§10). Holder facts sourced from the official MINDEF page cited above (§1 traceability; §2 landed-source path), not article cascade.
```
