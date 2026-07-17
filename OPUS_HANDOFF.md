# Opus handoff — `toml-config` branch cleanup + overhaul roadmap

Paste this file (or `@OPUS_HANDOFF.md`) to Opus to continue the work. It is a map of
**what still needs to happen** and **which instructions govern each piece**. Read the linked
files at work time — they are the source of truth; this doc just routes you to them.

Governing rules for every task below:
- `CLAUDE.md` → **Agent Operating Rules** (no file deletions — supersede + add a
  `TODO.md` "Human-Needs-To-Do" checkbox instead; scripts stay thin; new inputs go in
  `olaf/config/models.py` **and** the matching `configs/templates/*.example.toml`).
- Anything touching `olaf/processing/`, `olaf/utils/math_utils.py`, `CONSTANTS.py`,
  `olaf/config/models.py`, or a golden under `tests/test_data/goldens/` → run the
  **`science-reviewer`** agent on the diff before committing.
- New/changed tests → use the **`test-author`** agent; it must not regenerate goldens.
- Finish with **`/check`**, then **`/commit`**, then **`/pr`** (base branch `develop`).

---

## 1. Agent & skill health check (done — mostly reasonable)

All four skills and both agents are well-scoped and their external references resolve
(`develop` branch, `.github/PULL_REQUEST_TEMPLATE/agent.md`, `CONTRIBUTING.md`,
`docs/contributing.rst`, `docs/release-process.rst`, `tests/README.md`,
`tests/test_data/goldens/`, `assert_csv_matches_golden` in `tests/conftest.py`, `TODO.md`).
Two stale spots inside the skills need a fix (see task 2c), and they are self-consistent
otherwise.

| Definition | File | Verdict |
|---|---|---|
| `science-reviewer` (agent, opus) | `.claude/agents/science-reviewer.md` | Good. Scope + statistics checks accurate. |
| `test-author` (agent, opus) | `.claude/agents/test-author.md` | Good. Golden = human-only rule is correct. |
| `/check` | `.claude/skills/check/SKILL.md` | Good. Mirrors CI (ruff/mypy/bandit/pytest). |
| `/commit` | `.claude/skills/commit/SKILL.md` | Good (trailer refreshed to Opus 4.8). |
| `/new-config` | `.claude/skills/new-config/SKILL.md` | Good (`process/` is canonical again — see §2). |
| `/pr` | `.claude/skills/pr/SKILL.md` | Good. Base `develop`, agent PR template. |

---

## 2. Immediate: finish the half-done `toml-config` migration — ✅ DONE

All items below were completed directly (not handed to Opus). Local gate is green:
ruff clean, mypy clean, bandit clean (the stray `olaf/.venv/` must be excluded — it is a nested
virtualenv, not source), `149 passed, 3 skipped` (pre-existing roadmap skips). Summary of what
changed:
- **2a** `test_folder` → `data_folder` doc cleanup done in `configs/README.md`, `CLAUDE.md`, and
  a full refresh of `docs/usage.rst` (all three stages rewritten from the old "edit variables at
  the top of the script" style to the TOML flow).
- **2b** Folder naming: reverted to **`process/`** (consistent with `blanks/`/`final_combine/`).
  Config restored at `configs/RAM_CINC/process/A12_07.16.25_base.toml` (HEAD values +
  `data_folder` rename). The scratch `configs/RAM_CINC/main/` copy is still staged and must be
  removed by a human — see `TODO.md` → Human-Needs-To-Do → File / directory deletions.
- **2c** `DEFAULT_CONFIG` regression fixed in `olaf/main.py`: back to the plain relative string
  `"configs/RAM_CINC/process/A12_07.16.25_base.toml"` (matches the two sibling scripts; the
  broader `Path(__file__)`-anchoring for all three lives in Milestone C / bug #12). Also removed
  the now-unused `Path` import and an unused `app =` binding in the (now-live) GUI block.
- **2d** `/commit` trailer refreshed to Opus 4.8. `/new-config` needed no change once `process/`
  stayed canonical.

Remaining human step: delete the `configs/RAM_CINC/main/` copy (agent cannot), then `/commit`
+ `/pr` into `develop`.

<details><summary>Original section 2 plan (for reference)</summary>

Two renames were started on this branch and left partially applied. Code + tests are done and
green (38 passed in `tests/test_config` + `tests/test_scripts`); **docs and one script const are
not**. Also one real regression to fix.

### 2a. `test_folder` → `data_folder` rename (field rename — DONE in code, stale in docs)
Done: `olaf/config/models.py`, `olaf/main.py`, `tests/test_config/test_config.py`,
`tests/test_scripts/test_script_wiring.py`. Remaining stale references to update:
- `configs/README.md:52` — "`project_folder` / `test_folder` paths…" → `data_folder`.
- `CLAUDE.md:298` — "Config `test_folder` / `project_folder` paths…" → `data_folder`.
- `docs/usage.rst:20` — `test_folder = …` in the code block (this block is also outdated: it
  shows the old inline-editing style, not the TOML flow — worth refreshing).
- Leave `CLAUDE.md:259` (`sgp_test_folder`) alone — that is a pytest fixture name, not the field.

### 2b. `configs/<CAMPAIGN>/process/` → `configs/<CAMPAIGN>/main/` (DECISION NEEDED, then finish)
The stage-1 config folder was physically moved `process/ → main/` (new file staged at
`configs/RAM_CINC/main/A12_07.16.25_base.toml`; old `process/` copy deleted) and
`DEFAULT_CONFIG` was repointed at `main/`. But **9 doc references still say `process/`**, so
the repo is currently inconsistent.

> **Decide first:** `main/` matches the script name (`main.py`) but breaks the *functional*
> naming of its siblings `blanks/` and `final_combine/`. `process/` is more consistent with
> them. Pick one and apply it everywhere. Recommendation: keep **`process/`** (revert the
> folder move) for naming consistency — but this is the human/Opus call.

If finishing the move to `main/`, update all of: `CLAUDE.md:78,209,214`,
`.claude/skills/new-config/SKILL.md:31,83` (and the "Stage 1 (process)" label),
`olaf/main.py:6` (docstring), `configs/templates/main.example.toml:4,6`,
`configs/README.md:20,38`. If reverting to `process/`, move the config file back and repoint
`DEFAULT_CONFIG` (remember: agent cannot delete — supersede + `TODO.md` checkbox for the human
to remove the stray copy).

### 2c. REGRESSION — `DEFAULT_CONFIG` is broken (`olaf/main.py:19`)
```python
DEFAULT_CONFIG = Path.cwd().parent / "configs/RAM_CINC/main/A12_07.16.25_base.toml"
```
Run from the repo root, `Path.cwd().parent` is `…/PycharmProjects`, so this resolves to
`…/PycharmProjects/configs/RAM_CINC/main/…` — **which does not exist** (verified). The pre-branch
value was the working relative string `"configs/RAM_CINC/process/A12_07.16.25_base.toml"`. This
is exactly `TODO_overhaul.md` **bug #12**. Fix to a location-independent, repo-root-anchored path
(e.g. `Path(__file__).resolve().parents[1] / "configs/…"` or honor `OLAF_CONFIG_DIR`), not
`Path.cwd().parent`.

Also note: the staged `configs/RAM_CINC/main/A12_07.16.25_base.toml` looks like a **scratch
config** (`data_folder` points at `tests/test_data/test_project/SGP 6.14.24 base`,
`vol_air_filt = 1.0`). Confirm whether that is the intended committed default or should be
reverted to the real RAM_CINC A12 values.

### 2d. Skill self-fixes (surfaced by the health check)
- `.claude/skills/new-config/SKILL.md:31,83` — same `process/` vs `main/` stale path as 2b; fix
  together with the decision above.
- `.claude/skills/commit/SKILL.md:63,85` — `Co-Authored-By: Claude Opus 4.7` should be the
  current model (harness expects **Claude Opus 4.8**); the skill already says "update the model
  name if running as a different model," so just refresh the hardcoded example.

**Close-out for section 2:** `/check` → `science-reviewer` on the `models.py`/`main.py` diff →
`/commit` → `/pr` into `develop`.

</details>

---

## 3. Larger roadmap — the community-package overhaul

The full backlog lives in **`TODO_overhaul.md`** (milestones A–F, with cross-refs to the bug
index in `TODO.md`). Do not re-plan it here; work it milestone by milestone, one PR series each.
Sequencing and agent/skill routing:

- **Milestone A — numerical-core overhaul** (highest priority): `graph_data_csv.py` +
  `blank_correction.py`, folding in bugs #1–#5, #8. **Every diff → `science-reviewer`.** New
  behaviour → `test-author`. Golden re-curation is **human-only** (`OLAF_REGEN_GOLDEN=1` + review).
- **Milestone B — decouple review UI** (testability, *not* bypass): the GUI always opens; see the
  hard constraint in `TODO_overhaul.md` lines 17–19 and the `researcher-review-mandatory` memory.
- **Milestone C — type the domain & tighten config**: `Literal`/`Enum` for
  `sample_type`/`treatment`, promote soft `warnings.warn` to hard errors / `strict=true`, and
  **bug #12** (the same `DEFAULT_CONFIG` issue as task 2c — fix once, reference here).
- **Milestone D — packaging** (`[project.scripts]`, version choice, PyPI publish) — some items are
  human decisions (see `TODO_overhaul.md` "Human-Needs-To-Do").
- **Milestone E — logging/observability**; **Milestone F — CI/docs/release gates** (a real
  non-vacuous `tests/test_integration/`, coverage gate, `docs/methodology.rst`, `CHANGELOG.md`).

Human-only items are collected at the bottom of `TODO_overhaul.md` and in `TODO.md`
"Human-Needs-To-Do" — an agent must never do those (golden re-curation, version choice,
`requirements.in` deletion, breaking `DataHandler` contract change).

---

## Suggested first prompt to Opus

Section 2 is done; the next work is the roadmap in section 3 (start with Milestone A).

> Read `OPUS_HANDOFF.md` and `TODO_overhaul.md`. Begin Milestone A (numerical-core overhaul),
> starting with the `graph_data_csv.py` bugs (#1, #2, #8) as one focused PR series. Run the
> `science-reviewer` agent on every diff, use `test-author` for new tests, and never regenerate
> goldens yourself (human-only). Run `/check` and stop before committing so I can review.
