---
name: commit
description: Create a git commit for the staged or unstaged changes in this OLAF working tree, following project conventions (Conventional Commits prefix, no file deletions, no --no-verify, Co-Authored-By trailer). Use when the user says "commit", "commit this", "make a commit", or invokes /commit.
---

# /commit — OLAF commit workflow

You are creating a git commit in the OLAF repository. Follow the steps below exactly. The base commit workflow in your Bash tool instructions still applies — this skill layers OLAF-specific rules on top.

## Hard rules (from CLAUDE.md)

- **Never delete files.** Do not run `rm`, `git rm`, `Path.unlink`, `shutil.rmtree`, or anything equivalent — not as part of staging, not as part of "cleanup". If a file must be superseded, leave the old one in place and add a checkbox under "Human-Needs-To-Do" in `TODO.md` for the human to remove it.
- **Never pass `--no-verify`, `--no-gpg-sign`, or `-c commit.gpgsign=false`** to `git commit`. If a pre-commit hook fails, fix the underlying issue and create a *new* commit — do not bypass and do not `--amend`.
- **Never amend** an existing commit unless the user explicitly asks. Pre-commit failures did *not* create the commit, so `--amend` would silently rewrite the previous one.
- **Never force-push or run destructive git commands** (`reset --hard`, `checkout .`, `clean -f`, `branch -D`) unless the user explicitly requests it.

## Step 1 — Inspect state (run in parallel)

Run these three Bash calls in a single message:

- `git status` (no `-uall` flag — it can OOM on large repos)
- `git diff` *and* `git diff --staged` (whichever is non-empty; both is fine)
- `git log --oneline -10` to mirror the project's commit-message style

If `git status` shows no changes, stop and tell the user there is nothing to commit. Do **not** create an empty commit.

## Step 2 — Decide what to stage

Default: stage only files the user clearly intended to change. Specifically:

- **Do** stage source files under `olaf/`, tests under `tests/`, docs under `docs/`, CI under `.github/`, and config like `pyproject.toml`, `uv.lock`, `CLAUDE.md`, `TODO.md`.
- **Do not** stage without asking:
  - `.idea/`, `.serena/`, `.venv/`, `_build/`, `__pycache__/`, `.python-version`
  - Anything under `tests/test_data/` larger than ~1 MB, or any `.xlsx`, `.xlsm`, `.dat`, `.png` you did not yourself create in this session
  - `.~lock.*#` Office lock files
  - `.env`, anything containing "secret", "token", "credential", "key.json"
- **Never** use `git add -A` or `git add .`. Always stage by explicit path.

If the working tree contains a mix of intended and unintended changes, list what you plan to stage and what you plan to leave, then proceed — do not ask the user to confirm each file individually unless something looks risky.

## Step 3 — Draft the commit message

OLAF uses **Conventional Commits**. Inspect `git log --oneline -20` to confirm — common prefixes in this repo:

- `feat:` — new user-facing functionality
- `fix:` — bug fix in existing behavior
- `test:` — adding or modifying tests only
- `ci:` — changes under `.github/workflows/` or `.github/actions/`
- `chore:` — TODO.md updates, lockfile bumps, dev-tooling tweaks, no behavior change
- `docs:` — `docs/`, `README.md`, `CONTRIBUTING.md`, docstrings only
- `refactor:` — restructuring without behavior change

Rules for the message:

- Subject line: lowercase after the prefix, no trailing period, ≤72 chars. Imperative mood ("add", "fix", "update" — not "added", "fixes").
- If the change is non-trivial, add a blank line then a body explaining the *why*, not the *what*. The diff already shows the what.
- If the change touches scientific outputs (anything in `olaf/processing/`, `CONSTANTS.py`, or any golden fixture under `tests/test_data/goldens/`), the body **must** state the expected numerical impact or explicitly say "no numerical change".
- If the change adds a Human-Needs-To-Do item (e.g., a superseded `.new` file), reference `TODO.md` in the body.

Always end the message with the trailer:

```
Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

(Update the model name if you are running as a different Claude model.)

## Step 4 — Create the commit (run in parallel)

In a single Bash message, run:

1. `git add <explicit paths>` — never `-A`, never `.`
2. `git commit -m "$(cat <<'EOF' ... EOF)"` — always use a heredoc for the message so formatting survives
3. (sequentially after the commit) `git status` to verify

Example skeleton:

```bash
git commit -m "$(cat <<'EOF'
feat: short imperative subject

Optional body explaining the why. Reference TODO.md if a human follow-up
is required.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

## Step 5 — Handle pre-commit failure

If the commit fails because a pre-commit hook (ruff, mypy, bandit, pre-commit) rejected it:

1. Read the hook output and fix the underlying problem in the code.
2. Re-stage the fixed files by explicit path.
3. Create a **new** commit (do not `--amend`, do not pass `--no-verify`).
4. If the fix is unrelated to the user's intent (e.g., a stray whitespace fix forced by the hook), mention it in the commit body.

## Step 6 — Report

Tell the user:

- The commit SHA (short form, from `git status` or `git log -1 --oneline`)
- The branch
- Whether anything was intentionally left unstaged, and why

Do **not** push. Pushing requires a separate explicit ask from the user.
