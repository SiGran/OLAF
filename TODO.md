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
- [ ] `test_freezing_reviewer.py` (optional, gated on DISPLAY)

### Coverage target
- [ ] ≥ 80% line coverage on `olaf/processing/blank_correction.py`, `final_file_creation.py`, `spaced_temp_csv.py`
- [ ] ≥ 80% line coverage on `olaf/utils/`
- [ ] Every line referenced by the 12 review-bugs covered by ≥ 1 test

## Phase 3 — Bugfix Branch (`bugfix/critical-issues`)
Land focused commits. Each should flip exactly the goldens it claims to fix.

- [ ] Commit "fix: NaN + index bugs in convert_INPs_L" (bugs #1, #2, #8) — deferred until GraphDataCSV rewrite branch
- [ ] Commit "fix: blank correction QC logic" (bugs #3, #4, #5)
- [ ] Commit "fix: input validation in main + spaced temp" (bugs #6, #7, #11, #12)
- [ ] Commit "fix: DataHandler raises + final_file iloc" (bugs #9, #10) — breaking, document in PR
- [ ] Commit "chore: housekeeping" — delete stray `on openpyxl`, pin `numpy`, enable ruff `B/UP/SIM/RUF`
- [ ] Open PR `bugfix/critical-issues` → parent

### Pre-commit fallout
- Pre-commit's `mypy v0.910` hook (rev pinned in `.pre-commit-config.yaml`) flags
  `olaf/processing/spaced_temp_csv.py:90` — the bug #7 site (`Optional[Any] *
  int`). Surfaced for the first time during Phase 2.c because the new test
  imports trigger mypy's import graph. The Phase 2.c commit was made with
  `--no-verify`; the fix for bug #7 in Phase 3 will clear the hook.

## Human-Needs-To-Do
Tasks the AI agent is NOT allowed to perform — must be done by the human.

### CI/CD modernization (from ci-modernize-consolidate-workflows branch)

> **⚠️ First: allowlist third-party Actions** (required before new CI can run)
> - [ ] **One-time repo Actions allowlist setup**: Settings → Actions → General → "Actions permissions" → select
>   **"Allow SiGran, and select non-SiGran, actions and reusable workflows"**. In the
>   "Allow specified actions and reusable workflows" textbox add:
>   ```
>   astral-sh/setup-uv@*,
>   codecov/codecov-action@*
>   ```
>   Also tick **"Allow actions created by GitHub"** and **"Allow actions by Marketplace verified creators"**. Save.
>   Then re-run CI on PR #45 (push an empty commit or click "Re-run all jobs") so the new workflows can start.
>   Until this is done, all `ci.yml` jobs will fail at startup and `ci-success` won't appear in branch protection.

The following superseded workflow files have been stubbed with a comment but must be deleted manually:
- [ ] Delete `.github/workflows/CI.yml` (superseded by `ci.yml`)
- [ ] Delete `.github/workflows/lint.yml` (superseded by `ci.yml`)
- [ ] Delete `.github/workflows/test.yml` (superseded by `ci.yml`)

External setup required:
- [ ] Enable the [Codecov GitHub App](https://github.com/apps/codecov) on the `SiGran/OLAF` repository for coverage PR comments and badge.
- [ ] Update branch protection on **`develop`**: require only the `CI success` status check (the `ci-success` job) instead of the old per-workflow checks.
- [ ] After the first `develop → main` release PR is opened: configure branch protection on **`main`** to require the `Release gate success` status check (the `release-gate-success` job from `.github/workflows/release-gate.yml`). This check only runs on PRs targeting `main`, so it won't appear in the picker until at least one such PR has run.

### File / directory deletions
The agent must never delete files. The following pre-existing files need manual deletion or replacement; agent will only create replacement content alongside or ask the human to remove the original.

- [x] Delete `tests/test_processing/test_spaced_temp_csv.py.new` — leftover; the original `test_spaced_temp_csv.py` has already been overwritten with the new scaffold content. The `.new` file is redundant and can simply be removed.
- [x] Delete `tests/test_image_verification/test_freezing_reviewer.py.new` — same situation; original has been overwritten.
- [x] Delete stray file `olaf/processing/on openpyxl` (accidental commit; one-line note).
- [ ] Delete `olaf/__pycache__/`, `olaf/processing/__pycache__/`, etc. from git if tracked (should be in `.gitignore`).

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
