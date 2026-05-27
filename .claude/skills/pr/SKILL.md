---
name: pr
description: Open a GitHub pull request for the current branch following OLAF conventions (base branch develop, Conventional Commits subject, agent PR template body, no force pushes). Use when the user says "open a PR", "make a PR", "create a pull request", or invokes /pr.
---

# /pr — OLAF pull request workflow

You are opening a pull request from the current branch into `develop` (or `main` only if explicitly asked — `develop` is the integration branch per CONTRIBUTING.md). The base PR workflow in your Bash tool instructions still applies — this skill layers OLAF-specific rules on top.

## Hard rules

- **Base branch is `develop`** unless the user names a different target. Never open a PR directly against `main` without confirmation — `main` only receives release PRs from `develop` (see `docs/release-process.rst`).
- **Never force-push.** If the remote branch has diverged, stop and ask the user how to proceed.
- **Never use `--no-verify` or skip hooks** when pushing or committing during this flow.
- **Never delete files** (`rm`, `git rm`, branch deletion, etc.) — see `CLAUDE.md`.
- If commits on the branch were made by `/commit`, this skill is the natural follow-up. If the branch has uncommitted changes, stop and tell the user to commit first (or invoke `/commit`) — do not silently bundle them.

## Step 1 — Inspect branch state (run in parallel)

Run these in a single Bash message:

- `git status` (no `-uall` flag)
- `git rev-parse --abbrev-ref HEAD` to confirm branch name
- `git log --oneline develop..HEAD` (or `origin/develop..HEAD`) to see every commit that will be in the PR — **not just the most recent one**
- `git diff develop...HEAD --stat` (three-dot: diff vs. the merge base, which is what GitHub shows)
- `git remote -v` to confirm the GitHub remote exists

If `git log develop..HEAD` is empty, stop — there is nothing to PR.

If `git status` shows uncommitted changes, stop and tell the user. Do not stage or commit anything as part of this skill.

## Step 2 — Push the branch if needed

- If the branch has no upstream: `git push -u origin <branch>`
- If the branch is behind/ahead of its upstream: report the state and ask before pushing. **Never** `git push --force` or `--force-with-lease` without explicit user permission.
- If push fails because the branch is behind: stop. Do not auto-rebase or auto-merge.

## Step 3 — Draft the PR title

Same Conventional Commits rules as `/commit`:

- Prefix: `feat:`, `fix:`, `test:`, `ci:`, `chore:`, `docs:`, `refactor:`
- Lowercase after prefix, no trailing period, ≤72 chars
- Imperative mood
- Summarize the **whole branch**, not the latest commit. Read `git log develop..HEAD` and synthesize.

## Step 4 — Draft the PR body

The body must follow the structure in `.github/PULL_REQUEST_TEMPLATE/agent.md`. Read that file at PR-creation time so you pick up any updates. The required sections, in order:

1. **Summary** — 1–3 sentences, what + why (the motivation, not a paraphrase of the diff).
2. **Motivation / context** — link to the issue, `TODO.md` entry, or conversation that prompted the work. Name the scope boundary (what this PR intentionally does *not* do).
3. **Changes** — bullet list grouped by area; for each non-trivial change, name the file and the behavior change.
4. **Scientific / numerical impact** — explicit statement about whether any numerical result, golden fixture, or `CONSTANTS.py` value changed. If none, write "N/A — no numerical or output change."
5. **Test plan** — checkbox list of which checks were run locally, with the pytest summary line pasted in. Mirrors `CONTRIBUTING.md` / `docs/contributing.rst`.
6. **Agent operating rules — confirmations** — checkboxes confirming no file deletions, no `--no-verify`, no force pushes, user-config sections preserved, no secrets.
7. **Files added / large additions** — list new files >100 lines, new directories, new test fixtures. Justify each. Write "None" if none.
8. **Dependencies** — note any `pyproject.toml` / `uv.lock` / `requirements*.in` change with the reason. Write "No dependency changes." if none.
9. **Human-Needs-To-Do** — anything a human must do that this PR could not (file deletions, GUI verification, golden regeneration). Add matching checkboxes to `TODO.md` under "Human-Needs-To-Do" in the same PR if you can.
10. **Notes for review** — areas you're least confident about; specific lines you want a second pair of eyes on.

Trailer: keep the `Generated with Claude Code` line for fully-agent-authored PRs so reviewers know to apply extra scrutiny.

## Step 5 — Run local checks before opening (recommended)

If they haven't been run on this branch, suggest the user run (or run yourself if they ask):

```bash
uv run ruff check .
uv run mypy .
uv run bandit -r olaf
uv run pre-commit run --all-files
uv run pytest -m "not gui"
```

Paste the pytest summary line into the **Test plan** section. CI will run them anyway, but a clean local run avoids a red-CI round-trip.

## Step 6 — Create the PR

Always pass the body via a heredoc to preserve formatting:

```bash
gh pr create \
  --base develop \
  --title "<conventional-commits subject>" \
  --body "$(cat <<'EOF'
## Summary

...

## Test plan

- [x] `uv run pytest -m "not gui"` — 108 passed, 11 skipped
...

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

If the user wants a draft PR, add `--draft`.

## Step 7 — Report

Tell the user:

- The PR URL (from `gh pr create` output)
- The base and head branches
- Which CI checks will run (lint, typecheck, security, pre-commit, test → `ci-success` aggregator per `docs/contributing.rst`)
- Anything you put under **Human-Needs-To-Do** that needs follow-up

Do not merge. Merging requires a separate explicit ask from the user, and `main`-bound merges go through the release gate.
