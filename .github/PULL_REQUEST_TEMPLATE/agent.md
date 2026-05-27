<!--
This template is the GitHub-side counterpart to the `/pr` skill at
.claude/skills/pr/SKILL.md. Agents creating PRs should invoke `/pr`, which
walks through the same sections programmatically. Humans who want the
thorough checklist can select this template via `?template=agent.md` in the
GitHub compare URL; otherwise the default at
.github/PULL_REQUEST_TEMPLATE.md is used.

Fill in every section. Delete the HTML comments before submitting. If a
section genuinely does not apply, write "N/A — <one-line reason>" rather
than leaving it blank.
-->

## Summary

<!--
1–3 sentences. State what changed and *why* (the user-facing motivation or
the bug being fixed), not a paraphrase of the diff.
-->

## Motivation / context

<!--
Link the issue, TODO.md entry, or conversation that prompted this work.
If this is part of a multi-step plan, name the phase/stage and what comes
next. If there's no tracking issue, explain why this change was needed now.
-->

- Issue / TODO reference:
- Scope boundary (what this PR intentionally does NOT do):

## Changes

<!--
Bullet list grouped by area. For each non-trivial change, name the file
and the behavior change — not just "refactored X". Example:

- `olaf/processing/blank_correction.py`: cast `dilution` to `str` before
  comparison so tuple-valued dilutions round-trip through CSV correctly.
- `tests/conftest.py`: added `kcg_golden_folder` fixture pointing at the
  curated golden inputs.
-->

-

## Scientific / numerical impact

<!--
OLAF produces published scientific outputs. State explicitly:
  - Does this change any numerical result (INP concentrations, confidence
    intervals, blank corrections, ARM file contents)? If yes, describe the
    expected delta and how you verified it is intentional.
  - Did you update or regenerate any golden fixtures? If yes, list which
    ones and confirm a human has reviewed the diff.
  - Are any CONSTANTS.py values touched? If yes, justify.

If none of the above apply, write "N/A — no numerical or output change."
-->

## Test plan

<!-- Check every box that applies; write N/A with a reason for ones that don't. -->

- [ ] `uv run pytest -m "not gui"` passes (paste the final line: `N passed, M skipped`)
- [ ] `uv run ruff check .` clean
- [ ] `uv run mypy .` clean
- [ ] `uv run bandit -r olaf` clean (or new findings explained below)
- [ ] `uv run pre-commit run --all-files` clean
- [ ] New behavior is covered by a new or updated test
- [ ] If GUI code changed: `FreezingReviewer` smoke tests still pass on a display, OR explain why a manual check isn't feasible

Local results:

```
<paste the pytest summary line and any non-obvious output>
```

## Agent operating rules — confirmations

<!--
These mirror the non-negotiable rules in CLAUDE.md. Check each box to
confirm; reviewers will reject PRs that violate them.
-->

- [ ] **No file deletions.** I did not run `rm`, `git rm`, `Path.unlink`,
      `shutil.rmtree`, or any equivalent. Any superseded file was left in
      place (or a `.new` sibling was created) and an entry was added under
      "Human-Needs-To-Do" in `TODO.md`.
- [ ] **No `--no-verify`, `--no-gpg-sign`, or skipped pre-commit hooks** in
      commits on this branch.
- [ ] **No force pushes** to shared branches (`main`, `develop`).
- [ ] **User configuration sections preserved** at the top of `main.py`,
      `main_for_blanks.py`, and `main_final_combine.py` (if touched).
- [ ] **No secrets, credentials, or large binaries** added. New test data,
      if any, is justified below.

## Files added / large additions

<!--
List any new files >100 lines, new directories, new test fixtures, or new
dependencies. For each, justify why it had to be added rather than reusing
something existing. If none, write "None".
-->

- None

## Dependencies

<!--
Did `pyproject.toml`, `uv.lock`, or `requirements*.in` change? If yes, list
the package(s), the version pin, and the reason. If no, write "No dependency
changes."
-->

## Human-Needs-To-Do

<!--
Anything a human must do that this PR could not do itself: file deletions,
manual GUI verification, regenerating goldens on a machine with the real
data, updating Codecov tokens, rotating credentials, etc. Add matching
checkboxes to TODO.md under the "Human-Needs-To-Do" section.

If nothing is required, write "Nothing — this PR is fully self-contained."
-->

-

## Notes for review

<!--
Anything the reviewer should pay extra attention to: tradeoffs you weighed,
alternatives you rejected, areas of the diff you're least confident about.
Be specific — "please double-check the error-propagation math in
`blank_correction.py:142`" beats "let me know if anything looks off."
-->

---

<!--
Attribution: keep the trailing Co-authored-by line if a human reviewer is
collaborating on the PR. Add a "Generated with Claude Code" line if this PR
was authored end-to-end by an agent, so reviewers know to apply extra
scrutiny.
-->
