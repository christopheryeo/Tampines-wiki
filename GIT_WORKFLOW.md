# Git & Pull Request Workflow

The end-to-end process for making a scoped Tampines Wiki change and getting it
into `main` through a pull request (PR).

Read `README.md` before starting work. It is the authoritative operating guide
for this vault; `AGENTS.md` contains the project rules.

## The golden rule

> **Always work on a branch that is _not_ `main` before you commit.**

A PR merges a source branch into `main`, so the source branch must be different
from `main`. Never push directly to `main`.

## Before you start

1. Check that the working tree is clean, or that any existing changes are
   clearly unrelated and will not be staged.
2. Do not commit secrets such as `.env.local`.
3. Do not commit ignored or generated material, including derived indexes,
   catalogs, dashboard outputs, or bulk `runs/` receipts, unless the scoped work
   explicitly requires it.
4. Do not hand-edit generated catalogs or indexes. Use the documented scripts
   where appropriate.

## The stages

### 1. Branch — start from an up-to-date `main`

```bash
git checkout main
git pull
git checkout -b codex/short-change-description
```

Use a concise branch name that describes the scoped change. If you are already
on the intended non-`main` branch, confirm it is the correct branch before
continuing.

### 2. Make and verify the scoped change

Follow `README.md`, `AGENTS.md`, and the relevant procedure under `scripts/`.
For vault work, preserve provenance and frozen schemas. Run the relevant
validation or maintenance command before committing.

### 3. Review — confirm the exact changes to publish

```bash
git status --short
git diff --check
git diff
```

Confirm that the diff contains only the intended tracked files. Stop and
separate unrelated pre-existing changes rather than including them accidentally.

### 4. Stage — add only the intended files

```bash
git add path/to/intended-file.md path/to/other-intended-file.py
git diff --cached --check
git diff --cached
```

Avoid `git add -A` in a dirty checkout. It can stage unrelated work, generated
artifacts, or confidential configuration.

### 5. Commit — save the staged change locally

```bash
git commit -m "Concise description of the change"
```

### 6. Push — publish the branch to GitHub

```bash
git push -u origin codex/short-change-description
```

### 7. Create PR — propose merging into `main`

```bash
gh pr create --base main --head codex/short-change-description
```

Creating a PR does **not** merge it. Describe the scoped change, the validation
performed, and any material limitations in the PR.

### 8. Merge — Giselle merges the PR

Do **not** merge your own PR or push to `main`. **Giselle** watches implementer
PRs on `christopheryeo/Tampines-wiki` and performs the merge under preapproval
once CI is green (per `DEVELOPMENT.md` / `docs/development-process.md`). Your
responsibility ends at opening a clear, correctly scoped PR; leave the merge to
Giselle. A PR is not shipped until Giselle has merged it.

### 9. Sync and tidy — update local `main`

```bash
git checkout main
git pull
git branch -d codex/short-change-description
```

Only delete the local branch after confirming Giselle merged the PR. The remote
branch is normally deleted by GitHub during the merge.

## Quick reference

```
read rules → branch → change & validate → review → stage → commit → push → PR → (Giselle merges) → sync & tidy
```

This document governs the Git and PR path for a scoped Tampines Wiki change up to
opening the PR. The merge is owned by **Giselle**, as defined in `DEVELOPMENT.md`
and `docs/development-process.md`.
