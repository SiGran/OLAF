---
name: check
description: Run OLAF's full local quality gate (ruff, mypy, bandit, pre-commit, pytest without GUI) the way CI runs it, then report a clean pass/fail summary with the failing output. Use when the user says "run the checks", "check", "lint and test", "is this green?", "run CI locally", or invokes /check.
---

# /check — OLAF local quality gate

You are reproducing the checks CI runs, locally, so the user avoids a red-CI round-trip. Mirror
the commands in `CONTRIBUTING.md` / `docs/contributing.rst`. This skill does not commit, push, or
fix anything unless the user asks — it runs the gate and reports.

## What to run (all via `uv run`, from the repo root)

Run these and collect each one's result. They are independent, so batch them:

```bash
uv run ruff check .
uv run mypy .
uv run bandit -r olaf
uv run pytest -m "not gui"
```

Notes:
- `mypy` is configured (`pyproject.toml`) to check `olaf/` only; tests are ignored. Don't fight it.
  CI invokes it as `uv run mypy olaf` (positional); `uv run mypy .` is equivalent given that config,
  but prefer `mypy olaf` if you want to match CI exactly.
- `bandit` excludes `tests/`. Run it against `olaf` as shown.
- Use `-m "not gui"` for pytest: the GUI tests need `$DISPLAY` and auto-skip headless, but being
  explicit keeps the summary clean. Add `--cov=olaf --cov-report=term-missing` only if the user
  asks about coverage.
- If the user has `pre-commit` installed and asks for the full hook set, also run
  `uv run pre-commit run --all-files` — it overlaps with ruff but can catch formatting/EOF hooks.
- If `uv` is not available, fall back to bare `ruff` / `mypy` / `bandit` / `pytest`, and say so.

## Interpreting results

- **ruff**: report the rule code + file:line for each finding. Line length is 100. If the user
  asks, you may run `uv run ruff check --fix .` for the autofixable ones — but only on request,
  and never let a fix touch scientific logic silently.
- **mypy**: report the error and the `file:line`. Do not add `# type: ignore` to make it pass
  unless the user agrees — a real type error near `olaf/processing/` can mask a numerical bug.
- **bandit**: report severity + confidence. Most OLAF hits are low-severity; flag any
  medium/high explicitly.
- **pytest**: paste the final summary line verbatim (e.g. `108 passed, 11 skipped`). If tests
  fail, show the failing test IDs and the assertion/traceback tail — do not summarize a failure
  as "some tests failed". If a **golden** test fails (anything asserting against
  `tests/test_data/goldens/`), call it out specifically: it may mean a numerical output changed,
  which is a scientific-review event, not a flake. Do not regenerate goldens as part of `/check`.

## Report

Give a compact status table — one row per tool, PASS/FAIL, and the headline number — followed by
the details for any FAIL. Lead with the overall verdict (green / not green) in the first sentence.
Do not commit, push, amend, or edit files to make the gate pass unless the user explicitly asks;
if you do fix something on request, re-run only the affected check to confirm.
