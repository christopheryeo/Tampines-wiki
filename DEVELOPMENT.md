# DEVELOPMENT.md

Handoff file for Tampines Wiki (`christopheryeo/Tampines-wiki`). This is not the wiki constitution. Wiki rules stay in `AGENTS.md` and `README.md`. Shipped features stay in the Features section of `../../Alex (Dev)/Knowledge/Product Inventory.md`. Human-blocked work stays on Owen’s ClickUp.

**Project home (Dropbox):** `/Users/chrisyeo/Dropbox/Work/CEO (Sentient)/Customer Folders/tampines-wiki`  
**Git remote:** `https://github.com/christopheryeo/Tampines-wiki`  
**Journal (Drive only):** https://docs.google.com/document/d/1LsucY9zwEWXukVwGftmpzUhfuguSj1VRxs_zK7EU6lw/edit  
**Updated:** 2026-09-04 SGT (formal project home + DEVELOPMENT.md)

## Roles

**Grok Bot (Felix).** Updates Now and Next. Writes each Now line as a short prompt the named tool can follow. After a merged PR, writes a Features line only for a user-facing capability he can name. Does not copy every PR. Does not implement vault scripts or front-end.

**Claude Code.** Implements the Now prompt named for Claude Code (app / site / tooling under tracked paths such as `issue-radar-site/` when that surface is in scope). Appends Done with implement or maintenance. Commits that work to a branch and opens or updates a PR. In that same PR, deletes only the Now line it just finished. Must not add Now or Next. Does not invent features. Does not write Product Inventory.

**ChatGPT Codex.** Works the Tampines vault (ingest, cascade, issue radar, topics, scripts). Implements the Now prompt named for ChatGPT Codex. Appends Done with the wiki tag only. Commits only tracked files for that Now line, on a branch, and opens or updates a PR. In that same PR, deletes only the Now line it just finished. Must not add Now or Next. Does not write Product Inventory.

**Morgan.** Does not keep this log. Dispatches the project; Owen keeps ClickUp true.

**Christopher.** Does not keep this log and does not commit. Looks only when a line is blocked on his yes, and that wait is not recorded here.

**Owen.** Human delivery (Arivumathi topic-crawl check, final crawl, present to nsiewpin, SMTC stories). Not a DEVELOPMENT.md owner.

**Giselle.** Merges sound implementer PRs on `christopheryeo/Tampines-wiki` when CI is green (preapproved).

## Policies

1. Features come from Now, or from a merged PR Felix has logged. Do not invent.
2. Now is a short prompt for one named tool, not a title. Next is queued and not started. Every Now and Next line names one tool: Claude Code or ChatGPT Codex. One Now line is one tool and one branch. The prompt names the surface, files it may touch, files it must not touch, the git rules, and a link to the PR for detail when one exists. Do not open or link GitHub Issues. Queued work stays in Next. Do not dump a novel. Claude Code implements only Now prompts named for it. ChatGPT Codex implements only Now prompts named for it. Felix moves a line from Next to Now when implementation starts.
3. If a line is waiting on a human, it does not belong here.
4. Do not copy wiki operating rules into this file. `AGENTS.md` and `README.md` stay the vault constitution, not a log.
5. Native GitHub only. Merged PRs on `christopheryeo/Tampines-wiki` wake Felix and Giselle.
6. Use Singapore Time (SGT, UTC+8) on Done lines.
7. A merged PR is the gate, not the feature list. Felix writes a Features line in `../../Alex (Dev)/Knowledge/Product Inventory.md` only for a user-facing capability he can name. Bug fixes, refactors, docs, dependency bumps, and vault ingest do not go there. GitHub stays the source. A Done line never counts as shipped. Work that never gets a PR is not shipped. Claude Code and ChatGPT Codex do not write Product Inventory. Do not create another catalogue in this repo.
8. Done is one dated handoff list. Each line is tagged implement, wiki, or maintenance, then who, then what. Tags sit on the line. ChatGPT Codex uses wiki only. Claude Code uses implement or maintenance only. Do not make separate headings. Do not add a Feature tag. Done gets a line only when the named tool actually opened this file.
9. `CLAUDE.md` imports `AGENTS.md` first, then this file.
10. The tool named on a Now line commits that work to a branch and opens or updates a PR. Nobody pushes to `main`. Nobody commits secrets (`.env.local`) or derived junk that `.gitignore` excludes. Prefer committing tracked script, schema, and site files for the Now line — not bulk `runs/` receipts unless the Now line explicitly says so.
11. One Now cycle is one branch and one PR. In that same PR the named tool must (a) commit the Now work, (b) delete only the Now line it just finished, and (c) append one Done line. Do not open a second PR only to clear Now. Do not clear Now without Done. Do not add Now or Next. Felix still writes Now and Next.

## Now (prompt for the named tool)

Format: tool — surface — files it may touch — files it must not touch — git — link

## Next

- ChatGPT Codex — vault: run ingest → enhance → cascade on the **30** loose markdown files at `Inputs/articles/` root (the live ready queue). Respect hold/fail rules; do not pull files out of `holds/` unless a prior Now cleared them. Do not invent Features. Do not push to `main`. Finish in one PR with work, clear Now, and one wiki Done line (Policy 11) when promoted.

## Done

- 2026-09-04 SGT — maintenance — Morgan — Added this DEVELOPMENT.md and CLAUDE.md to formalize Tampines Wiki as the project home with git (`christopheryeo/Tampines-wiki`).
- 2026-09-04 SGT — wiki — ChatGPT Codex — Audited the Tampines vault, repaired malformed Tag Coverage labels, and hardened link QA and repair logging.
- 2026-09-04 SGT — wiki — ChatGPT Codex — Audited all 2,258 parked input files, separated 1,808 correctly parked records from 450 source-recovery candidates, and documented a safe fix path for every hold bucket.
