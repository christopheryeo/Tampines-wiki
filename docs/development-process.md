# Tampines Wiki — development process

Living map of the Tampines Wiki vault + issue-radar development process. Maintained by Morgan (COS). Last refreshed **2026-09-10**.

This file describes **who does what** and **where the truth lives**. It does not replace `DEVELOPMENT.md` (Now/Next/Done) or `AGENTS.md` (wiki constitution).

---

## Process (how work moves)

1. **Felix** writes **Now / Next** on `DEVELOPMENT.md` (one Now = one named tool + one branch).
2. **Claude Code** implements app / site / tooling Now lines (e.g. `issue-radar-site/` when in scope); opens a PR; in that same PR clears the Now line and appends Done (`implement` or `maintenance`).
3. **ChatGPT Codex** implements vault/wiki Now lines (ingest, cascade, issue radar content, topics, scripts); opens a PR; Done with `wiki` tag only.
4. **Giselle** watches and merges implementer PRs on GitHub (preapproved merge path when CI is green; no handoff-only PRs).
5. **Felix** logs **Features** in Product Inventory only for real user-facing capabilities after merge — not every PR, and not routine vault ingest.
6. Human-blocked work goes to **Owen’s ClickUp** (Tampines Wiki List — not a second Now/Next).
7. Human delivery next (Arivumathi check, crawl, present to nsiewpin, SMTC story chase) stays on Owen / ClickUp, not on `DEVELOPMENT.md`.
8. **Product Management room** holds the Tampines Wiki development cycle; **Tampines room** is client delivery and human blockers.

---

## AI agents and tools in that process

| Who | Lane |
|---|---|
| Felix | Now/Next on `DEVELOPMENT.md`; Features after merge |
| Claude Code | App / site / tooling implement Now → PR |
| ChatGPT Codex | Vault/wiki Now → PR |
| Giselle | Watch + merge PRs on `christopheryeo/Tampines-wiki` |
| Owen | ClickUp Tampines Wiki List; chase human blockers and delivery |
| Leni | Folder map / Project Home knowledge |
| Morgan | COS / room dispatch; does not keep `DEVELOPMENT.md` |
| Vivien | Inbox/calendar only (not implement) |
| Vera / Theo | Product QC when that lane is used |
| Ben | Methods advice only |

Jimmy is Influential Brands account only — not on Tampines Wiki.

---

## Files (local)

**Git root / vault:** `Customer Folders/tampines-wiki/`  
**Remote:** `https://github.com/christopheryeo/Tampines-wiki.git`

### Process and constitution

| Path | Purpose |
|---|---|
| `DEVELOPMENT.md` | Roles, Policies, Now / Next / Done |
| `AGENTS.md` | Wiki constitution and operating rules |
| `CLAUDE.md` | Imports `AGENTS.md` then `DEVELOPMENT.md` for Claude Code |
| `README.md` | Repo / folder map — read before vault work |
| `wiki.yaml` | Wiki config |
| `docs/development-process.md` | This file |
| `Knowledge/Project Home.md` | Project stamp (git, ClickUp, room, delivery next) |
| `../../Alex (Dev)/Knowledge/Product Inventory.md` | Features catalogue (Felix) |

### Vault surfaces (summary)

| Surface | Notes |
|---|---|
| `scripts/`, `schemas/`, `entities/`, `topics/`, `Inputs/`, `raw/`, `runs/` | Vault ingest and cascade |
| `issue-radar-site/` | Site / radar UI when named on a Now line |
| `dashboards/`, `index/`, `_index/`, `tests/` | Supporting surfaces |
| `.env.local` | Secrets — never commit |

Prefer committing tracked script, schema, and site files for the Now line — not bulk `runs/` receipts unless the Now line explicitly says so.

---

## PRs / GitHub

- **Repo:** `christopheryeo/Tampines-wiki`
- **Rule:** nobody pushes to `main`
- **One Now cycle** = one branch = one PR (work + clear that Now line + one Done line)
- Do not open or link GitHub Issues for Now/Next
- Claude Code and ChatGPT Codex do not invent Features or write Product Inventory
- Merged PRs wake Felix (Features judgement) and Giselle (merge watch)

---

## ClickUp

- **Tampines Wiki List** — Owen; human delivery and blockers only
- Not a mirror of `DEVELOPMENT.md` Now/Next
- Tasks need a **human** owner; bots are never assignees

---

## Rooms

| Room | Use |
|---|---|
| Tampines | Client delivery (Arivumathi, crawl, nsiewpin present, SMTC stories, human blockers) |
| Product Management | Tampines Wiki development cycle (Felix one-Now handoff) |

Tampines channel members (as of inventory): Morgan, Owen, Vivien, Giselle, Leni, Felix.

---

## Related locks (do not reopen without Christopher)

- `DEVELOPMENT.md` is the build handoff; `AGENTS.md` + `README.md` stay the vault constitution
- Human waits do not belong on Now/Next
- 450 source-empty hold IDs stay parked until Christopher names a recovery path (see Next on `DEVELOPMENT.md`)
- Giselle auto-watches/merges implementer PRs under preapproval when CI is green
- Journal stays on Drive only (link in Project Home / DEVELOPMENT)
- Payment is in; open human risk remains overdue Q2 SMTC stories (see Project Home)

---

## Revision log

- 2026-09-10 — Initial process map written from `DEVELOPMENT.md`, Project Home, and live git remote (mirrored from Influential Brands process grain).
