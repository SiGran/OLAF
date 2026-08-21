# OLAF Test Scaffolding & Bugfix TODO

Tracking document for the regression-test → bugfix initiative. Update checkboxes as items land.

## Phase 0 — Inventory & Plan ✅
- [x] Code review of full codebase (12 bugs documented)
- [x] Inventory `tests/test_data/` real folders
- [x] Decisions locked: real-data first, `assert_frame_equal` goldens (Option A), placeholder for GraphDataCSV rewrite (option ii)

## Phase 1 — Test Framework Scaffold (current phase)
Create stubs only. Every test ends with `pytest.skip("not implemented")` so suite stays green.

### 1.1 Infrastructure
- [x] Create `tests/conftest.py` with real-data path fixtures, dilution dicts, golden helper, synthetic factories
- [x] Update `pyproject.toml` `[tool.pytest.ini_options]`: register `integration` + `gui` markers, `addopts = "--strict-markers -ra"`
- [x] Create `tests/test_data/goldens/` tree (with `.gitkeep`) for committed expected CSVs
- [x] Create `tests/README.md` (fixture catalog, marker conventions, golden regen via `OLAF_REGEN_GOLDEN=1`, real-data inventory)

### 1.2 Test module stubs
- [x] Rewrite `tests/test_processing/test_spaced_temp_csv.py` (overwritten; old broken test_create_temp_csv removed)
- [x] Create `tests/test_processing/test_blank_correction.py`
- [x] Create `tests/test_processing/test_final_file_creation.py`
- [x] Create `tests/test_processing/test_graph_data_csv.py` — single placeholder skip (rewrite pending)
- [x] Create `tests/test_utils/__init__.py` + `test_df_utils.py`, `test_path_utils.py`, `test_math_utils.py`, `test_type_utils.py`, `test_data_handler.py` (already existed from prior scaffolding)
- [x] Audit/replace `tests/test_image_verification/test_freezing_reviewer.py` (overwritten; `test_dummy` replaced with GUI stubs gated on $DISPLAY)

### 1.3 Verification
- [x] `pytest tests/ -v` runs green: 0 failed, 0 errored, 93 skipped
- [x] Commit phase 1 on branch `develop` (renamed from `renaming-samping`) — commit `0b3faad`

## Phase 2 — Fill Test Bodies (user-driven, one PR per file)
Each test gets a body + golden file. Run `OLAF_REGEN_GOLDEN=1 pytest <test>` to (re)generate goldens.

### Real-data → primary case map
| Test module | Primary real folder | Notes |
|---|---|---|
| `test_spaced_temp_csv` | `tests/test_data/SGP 2.21.24 base/` | Reviewed `.dat` present; 6 samples, air |
| `test_blank_correction::TestFindBlankFiles` | `tests/test_data/test_project/` | Contains `SGP 5.15.24 6.20.24 blanks/` |
| `test_blank_correction::TestAverageBlanks` | `tests/test_data/capek/KCG 05.21.24 07.19.24 blank/` | Two blank dates in one folder |
| `test_blank_correction::TestApplyBlanks` | `tests/test_data/test_project/SGP 6.20.24 base redo/` | Has `blank_corrected_*.csv` outputs |
| `test_blank_correction::TestFinalCheck` | synthetic (`tmp_path` factory) | Real non-monotonic cases unlikely |
| `test_blank_correction::TestExtrapolateBlanks` | `tests/test_data/test_project/extrapolated_blanks.csv` (reference) + synthetic | |
| `test_final_file_creation` | `tests/test_data/test_project/final_files/` & `capek/final_files/` | ARM-format goldens |
| `test_data_handler` | `tests/test_data/SGP 2.21.24 base/` | Many `(N)`-versioned files for find-latest tests |
| `test_df_utils` / `test_path_utils` / `test_math_utils` / `test_type_utils` | mostly inline | Read 1-2 real headers |
| `test_freezing_reviewer` | `tests/test_data/SGP 2.21.24 base/dat_Images/` | Skipped without `$DISPLAY` |

### Implementation order (recommended)
- [x] `test_utils/test_type_utils.py` (7 tests, all passing)
- [x] `test_utils/test_math_utils.py` (11 tests, all passing)
- [x] `test_utils/test_df_utils.py` (17 tests, all passing; surfaced: unique_dilutions can't handle lists)
- [x] `test_utils/test_path_utils.py` (23 tests, all passing; surfaced: sort_files_by_date trailing-number regex doesn't match `(N).csv` versioning)
- [x] `test_utils/test_data_handler.py` (10 tests, all passing; pins bug #9 silent-failure behavior)
- [x] `test_spaced_temp_csv.py` (7 passing + 1 skipped pending KCG golden curation; pins bug #7 TypeError; new goldens at `goldens/expected/test_spaced_temp_csv/{air_sgp,salt_sgp}.csv`; added `sgp_golden_folder` fixture)
- [x] `test_blank_correction.py` (13 passing + 4 skipped pending capek golden curation; pins bugs #3/#4/#5 with synthetic `_final_check` inputs; added `synthetic_inps_csv_factory`, `synthetic_blank_folder`, `capek_golden_folder` fixtures)
- [x] `test_final_file_creation.py` (15 passing + 2 skipped pending qc_flag re-emission of committed blank_corrected fixtures; pins bug #10 with RangeIndex synthetic input; surfaced bug #16: `expected_columns` requires qc_flag column that legacy fixtures lack — current code returns empty `files_per_date` on those folders)
- [x] `test_freezing_reviewer.py` (5 GUI smoke tests; gated on usable $DISPLAY via subprocess `tk.Tk()`+`tk.Label()` probe; auto-skip in headless CI)

### Coverage target
- [x] ≥ 80% line coverage on `olaf/processing/blank_correction.py`, `final_file_creation.py`, `spaced_temp_csv.py` (86%, 96%, 100%)
- [x] ≥ 80% line coverage on `olaf/utils/` (data_handler 92%, df_utils 96%, math 100%, path 100%, type 100%; plot_utils excluded — visualization-only)
- [ ] Every line referenced by the 12 review-bugs covered by ≥ 1 test

## Phase 3 — Bugfix Branch (`bugfix/critical-issues`)

> **Decision (deferred):** The behavioral bugfixes below are **intentionally not
> being landed yet**. A larger overhaul is planned that will redesign the
> affected code paths (blank-correction QC, `DataHandler` error contract,
> `final_file` indexing, `GraphDataCSV`), so fixing the semantics now would just
> create churn we'd redo. Instead, the test suite continues to **pin the current
> (develop) behavior** as characterization tests, and this branch ships only
> **zero-behavior housekeeping** (numpy pin + ruff `B/UP/SIM/RUF` + lint cleanup).
> The bug semantics will be designed correctly as part of the overhaul.

- [ ] Commit "fix: NaN + index bugs in convert_INPs_L" (bugs #1, #2, #8) — deferred to GraphDataCSV rewrite/overhaul
- [ ] Commit "fix: blank correction QC logic" (bugs #3, #4, #5) — deferred to overhaul; current behavior pinned
- [ ] Commit "fix: input validation in main + spaced temp" (bugs #6, #11, #12) — deferred to overhaul; bug #7 already fixed on develop
- [ ] Commit "fix: DataHandler raises + final_file iloc" (bugs #9, #10) — deferred to overhaul (breaking; needs holistic design)
- [x] Commit "chore: housekeeping" — pin `numpy`, enable ruff `B/UP/SIM/RUF`, behavior-preserving lint cleanup
- [x] Open PR `bugfix/critical-issues` → parent (now scoped to housekeeping only)

### Pre-commit fallout
- Pre-commit's `mypy v0.910` hook (rev pinned in `.pre-commit-config.yaml`) flags
  `olaf/processing/spaced_temp_csv.py:90` — the bug #7 site (`Optional[Any] *
  int`). Surfaced for the first time during Phase 2.c because the new test
  imports trigger mypy's import graph. The Phase 2.c commit was made with
  `--no-verify`; the fix for bug #7 in Phase 3 will clear the hook.

## Human-Needs-To-Do
Tasks the AI agent is NOT allowed to perform — must be done by the human.

### CI/CD modernization (from ci-modernize-consolidate-workflows branch)

> **⚠️ Allowlist already configured** — `astral-sh/setup-uv@*` and `codecov/codecov-action@*` are in the allowlist; CI is green.

External setup required:
- [ ] **Codecov token** (optional but recommended for PR comments): Coverage is uploading successfully (`status: queued`) but Codecov warns `Branch is protected but no token was provided`. PR comments / badges will be more reliable with a token. To fix: go to [codecov.io/gh/SiGran/OLAF](https://codecov.io/gh/SiGran/OLAF), copy the upload token, add it as a repo secret `CODECOV_TOKEN` (Settings → Secrets and variables → Actions), then add `token: ${{ secrets.CODECOV_TOKEN }}` to the `codecov/codecov-action` step in `.github/workflows/ci.yml`.
- [ ] Update branch protection on **`develop`**: require only the `CI success` status check (the `ci-success` job) instead of the old per-workflow checks.
- [ ] After the first `develop → main` release PR is opened: configure branch protection on **`main`** to require the `Release gate success` status check (the `release-gate-success` job from `.github/workflows/release-gate.yml`). This check only runs on PRs targeting `main`, so it won't appear in the picker until at least one such PR has run.

### File / directory deletions
The agent must never delete files. The following pre-existing files need manual deletion or replacement; agent will only create replacement content alongside or ask the human to remove the original.

- [x] Delete `tests/test_processing/test_spaced_temp_csv.py.new` — leftover; the original `test_spaced_temp_csv.py` has already been overwritten with the new scaffold content. The `.new` file is redundant and can simply be removed.
- [x] Delete `tests/test_image_verification/test_freezing_reviewer.py.new` — same situation; original has been overwritten.
- [x] Delete stray file `olaf/processing/on openpyxl` (accidental commit; one-line note).
- [ ] Delete `olaf/__pycache__/`, `olaf/processing/__pycache__/`, etc. from git if tracked (should be in `.gitignore`).
- [ ] Delete the stray nested virtualenv `olaf/.venv/` (untracked; not in git). It makes local
  `bandit -r olaf` runs scan ~25k venv findings and take minutes; CI is unaffected (clean
  checkout). Until deleted, run bandit locally as `bandit -r olaf -x olaf/.venv`.
- [ ] Delete `configs/RAM_CINC/main/A12_07.16.25_base.toml` and the now-empty `configs/RAM_CINC/main/` directory. The stage-1 config folder was renamed back from `main/` to `process/` (naming stays consistent with `blanks/` and `final_combine/`); the correct config now lives at `configs/RAM_CINC/process/A12_07.16.25_base.toml`. The `main/` copy is now untracked (already unstaged); just remove the directory — the agent cannot delete files.

### Environment / external setup
- [ ] Create the `bugfix/critical-issues` git branch from current HEAD when Phase 1 is green.
- [ ] Run `OLAF_REGEN_GOLDEN=1 pytest tests/test_processing/test_spaced_temp_csv.py` etc. after each test body is written; `git diff` the goldens; commit if correct.
- [ ] Tag `pre-bugfix-snapshot` before merging Phase 3 PR for easy rollback.
- [ ] Verify `tests/test_data/test_project/` and `tests/test_data/capek/` are committed (large folders; check `.gitignore`).
- [ ] **Curate `tests/test_data/goldens/inputs/capek/` per its `.NEEDED.md`** to unlock the 4 skipped real-data tests in `test_blank_correction.py` (copy blank + sample subfolders from raw `tests/test_data/capek/`).
- [ ] **Optional**: copy `dat_images/*.png` (3 files, ~8 MB total) into `tests/test_data/goldens/inputs/sgp_2_21_24_base/dat_images/` and `git add` only when Phase 2.e (GUI tests) gets implemented — they were intentionally left out of the Phase 2.c commit to keep repo size down.

### Decisions reserved for human
- [ ] Approve any breaking API changes (e.g., `DataHandler.get_data_file` raising instead of returning a tuple — bug #9 fix).
- [ ] Decide whether to commit the regenerated goldens for previously-buggy behavior, or hand-edit them to the correct expected values before commit.

## Phase 4 — Future Work (out of scope here)
- [ ] Major rewrite of `GraphDataCSV.convert_INPs_L` (separate branch, picks up bugs #1, #2, #8)
- [ ] `print → logging` migration
- [ ] YAML/CLI config for `main*.py`
- [ ] Consolidate `plot_utils` ↔ `processing/plots.py`
- [ ] GUI inheritance → composition refactor

## Bug Index (reference)
1. `prev_val == np.nan` always False — `graph_data_csv.py:259,261`
2. `UnboundLocalError` if `last_4_i` empty — `graph_data_csv.py:289-292`
3. `qc_flag = int` (class, not 0) — `blank_correction.py:393`
4. Pathological chained comparison — `blank_correction.py:402-410`
5. `prev_temp -= 1` on float temp label — `blank_correction.py:411`
6. `ValueError(...)` constructed not raised — `main.py:122`
7. `TypeError` if fpd key missing — `spaced_temp_csv.py:88-90`
8. Lost exception chaining — `graph_data_csv.py:78`
9. `DataHandler` returns `(None, exc)` instead of raising — `data_handler.py:67-75`
10. `iloc` with label index — `final_file_creation.py:205`
11. `"blank" in treatment` doesn't match `"blank heat"` — `main.py:95`
12. Malformed `Path("D:OLAF/...")` — `main.py:18`
13. *(surfaced in Phase 2)* `unique_dilutions` can't handle lists — `pandas.Series.unique()` raises TypeError on unhashable types — `df_utils.py:50`
14. *(surfaced in Phase 2)* `sort_files_by_date` trailing-number regex `(\d+)\.csv$` requires digit immediately before `.csv`; `(N).csv` versioning gives 0 for all versioned files — `path_utils.py:117`
15. *(surfaced in Phase 2.c)* `_extrapolate_blanks` raises `ValueError: setting an array element with a sequence` when the input `df_blanks` has a numeric-dtype `dilution` column: `df_blanks.loc[temp] = {"dilution": (1,), ...}` cannot inject a tuple into a single int/float cell. Real combined-blank CSVs ship with object-dtype tuple cells so this never triggers in production, but it's an unguarded invariant — `blank_correction.py:506`
16. *(surfaced in Phase 2.d)* `FinalFileCreation._get_files_per_date` and `create_all_final_files` hard-code `expected_columns=(..., "qc_flag")` in `read_with_flexible_header`. Any blank_corrected_*.csv emitted before bug #3's fix lands has only 5 columns (no qc_flag); `read_with_flexible_header` then fails to locate the column-header row, prints "No columns ... found", returns the whole file as header_lines, and `skiprows=0` reads garbage. Net effect: silent empty `files_per_date` on every legacy project folder (incl. the committed `tests/test_data/test_project/` and `tests/test_data/capek/` fixtures). — `final_file_creation.py:36,73-80`
17. *(surfaced in Phase 2.e)* `BlankCorrector.average_blanks` populates the `dilution` column with Python tuples (e.g. `(1,)`) rather than scalars. When the resulting DataFrame is written to CSV and read back via `pd.read_csv`, the cell becomes the string `"(1,)"` — so a round-trip `assert_frame_equal(written, read_back)` mismatches by dtype/value unless the test casts `dilution` to `str` first. The committed golden `tests/test_data/goldens/expected/test_blank_correction/capek_combined_blank.csv` pins this: line 2 reads `-20.0,"(1,)",13.338…`. — `blank_correction.py` (`average_blanks` `dilution` assignment)

## Release process (develop → main)

1. Bump version in `pyproject.toml` (`version = "X.Y.Z"`).
2. Open a PR from `develop` to `main`.
3. The "Release gate" workflow runs automatically and verifies:
   - Integration tests pass (`tests/test_integration`).
   - Full Python matrix (3.11, 3.12, 3.13) is green.
   - Sphinx docs build cleanly with `-W` (warnings as errors).
   - `pyproject.toml` version was bumped vs `main`.
4. After merge, tag the release: `git tag vX.Y.Z && git push --tags`.
5. Docs auto-deploy to GitHub Pages on push to `main`.

## Branch protection setup (one-time)

- [ ] On `develop`: require `CI success` status check.
- [ ] On `main`: require `CI success` AND `Release gate success`. The latter
      only becomes selectable after the first develop→main PR opens.

## Option C release readiness (prep for first develop → main PR)

The release-gate workflow is in place. Before opening the first `develop → main`
release PR, work through the following so the gate passes cleanly and the
release is well-formed.

### Required
- [ ] **Decide initial main-tracking version.** Currently `pyproject.toml` says
      `0.1.0`. Pick a target (e.g. `0.2.0` for a minor bump or `1.0.0` if this
      counts as the first stable release). The version-bump-check release-gate
      job will fail if the version in the release PR is unchanged from `main`.
- [ ] **Local docs build with warnings as errors.** Run
      `uv run sphinx-build -W -b html docs _build` from the repo root and fix any
      warnings (broken refs, missing TOC entries, autoapi issues) before
      opening the release PR. The `docs-build-check` job uses the same flags.
- [ ] **Local integration test run.** Run `uv run pytest tests/test_integration -v`
      and confirm all tests pass (or are intentionally skipped) on the develop
      tip. The release-gate `integration-tests` job runs this exact command.
- [ ] **Verify Python 3.13 compatibility.** The release-gate `full-matrix` job
      tries 3.11, 3.12, **and 3.13**. Run locally:
      `uv sync --all-extras --frozen --python 3.13 && uv run pytest -m "not gui"`.
      If 3.13 fails due to a dep that doesn't support it yet (most likely
      `pandas-stubs` or `matplotlib`), either pin/update that dep or drop 3.13
      from the matrix in `release-gate.yml` and open a follow-up task.
- [ ] **Codecov token configured** (see Human-Needs-To-Do above). Not required
      for the release-gate to pass, but required for reliable PR-comment
      coverage on the release PR.

### Recommended
- [ ] **Start a `CHANGELOG.md`** (or `docs/changelog.rst`) capturing what landed
      since `main`. Even a short bullet list per version is useful. Wire it into
      the Sphinx toctree if added under `docs/`.
- [ ] **Add status badges to `README.md`**: CI status, Codecov coverage, docs
      build (and PyPI / Python versions later if/when published).
- [ ] **Audit develop-only features.** Walk `git log main..develop` and confirm
      every commit is intended for the release. If anything is half-done or
      experimental, either finish it, revert it, or split it onto a feature
      branch before opening the release PR.
- [ ] **Pre-create the release PR title/body template** so the PR body is ready
      to fill in (links to changelog entries, screenshot of release-gate run,
      "fixes #..." section).

### Optional / future
- [ ] **Release workflow on tag push.** After the first successful release, add
      a `.github/workflows/release.yml` triggered on `push: tags: ['v*']` that
      creates a GitHub Release with autogenerated notes and attaches build
      artifacts. Out of scope for this PR.
- [ ] **PyPI publishing.** Configure trusted publishing
      ([docs.pypi.org](https://docs.pypi.org/trusted-publishers/)) and add a
      `release-publish` job to the release workflow. Out of scope.
- [ ] **Zenodo / DOI integration** for scientific citation, if desired.
- [ ] **Dependabot grouping.** Tune `.github/dependabot.yml` to group
      patch-level GitHub Actions bumps so the PR queue stays manageable.
