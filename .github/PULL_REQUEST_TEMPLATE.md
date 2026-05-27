<!--
Humans: fill in the sections below. Delete any that don't apply.
Agents (Claude Code, Copilot, etc.): use .github/PULL_REQUEST_TEMPLATE/agent.md
instead — it has the full agent-specific checklist this project expects.
-->

## Summary

<!-- 1–3 sentences: what changes and why. -->

## Changes

<!-- Bullet list of the user-visible / reviewer-visible changes. -->
-

## Test plan

<!-- How you verified this works. Commands, manual steps, or "N/A — docs only". -->
- [ ] `uv run pytest -m "not gui"` passes locally
- [ ] `uv run ruff check .` clean
- [ ] `uv run mypy .` clean

## Notes for review

<!-- Anything reviewers should pay extra attention to. Optional. -->
