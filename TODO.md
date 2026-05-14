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
- [ ] Commit phase 1 as `test/regression-baseline` branch

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
- [ ] `test_utils/*` (fastest, simplest)
- [ ] `test_data_handler.py`
- [ ] `test_spaced_temp_csv.py`
- [ ] `test_blank_correction.py` (largest, biggest payoff)
- [ ] `test_final_file_creation.py`
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

## Human-Needs-To-Do
Tasks the AI agent is NOT allowed to perform — must be done by the human.

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

