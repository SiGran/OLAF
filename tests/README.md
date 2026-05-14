# OLAF Test Suite

## Layout
```
tests/
├── conftest.py                    # shared fixtures (see fixture catalog in its docstring)
├── test_data/
│   ├── SGP 2.21.24 base/         # primary real data (reviewed .dat + Stage 1 outputs + images)
│   ├── SGP 3.28.24 base/         # secondary
│   ├── KCG 09.23.24 base/        # alternative real dataset
│   ├── capek/                    # full multi-treatment project (Stage 2 + 3)
│   ├── test_project/             # alternative multi-treatment project
│   └── goldens/                  # committed expected outputs (regen via env var, see below)
├── test_processing/
├── test_utils/
└── test_image_verification/
```

## Running

```bash
# All unit tests (fast, real-data goldens included)
pytest tests/

# With coverage
pytest tests/ --cov=olaf --cov-report=term-missing

# Skip GUI tests (auto-skipped without $DISPLAY)
pytest tests/ -m "not gui"

# Only integration / real-data goldens
pytest tests/ -m integration

# Regenerate golden CSVs for one test file
OLAF_REGEN_GOLDEN=1 pytest tests/test_processing/test_spaced_temp_csv.py
# When OLAF_REGEN_GOLDEN is set, the assert_csv_matches_golden helper writes the
# actual output to the expected golden path and pytest.skip()s the test.
# Inspect the diff with git, then commit if it looks right.
```

## Markers

| Marker | Meaning |
|---|---|
| `integration` | Uses real-data goldens; slower than pure unit tests |
| `gui` | Requires `$DISPLAY`; auto-skipped on headless runs |

Both are registered in `pyproject.toml`. `addopts = "--strict-markers -ra"` so typos in marker names fail loudly.

## Writing a new test

1. Pick a fixture from `conftest.py` for the real-data folder you need.
2. Use the stub template inside each `test_*.py` file (Given/When/Then docstring + `pytest.skip`).
3. Replace `pytest.skip(...)` with the implementation.
4. For golden-style assertions:
   ```python
   def test_foo(self, sgp_test_folder, goldens_root, assert_csv_matches_golden):
       actual = my_function(sgp_test_folder)
       golden = goldens_root / "test_spaced_temp_csv" / "air_sample_sgp.csv"
       assert_csv_matches_golden(actual, golden)
   ```
5. First run with `OLAF_REGEN_GOLDEN=1` to create the golden file. Inspect via `git diff`. Commit.

## Real-data inventory

See the comment block at the top of `tests/conftest.py` for a folder-by-folder breakdown of what real data is available and which tests it can serve.

## Golden file conventions

- One subfolder per test module: `tests/test_data/goldens/<module>/<case>.csv`
- CSV-only (no pickle), so diffs are reviewable.
- Always written with `index=False, lineterminator="\n"` for cross-platform stability.
- Comparison uses `rtol=1e-9, check_dtype=False` to absorb float rep + dtype drift.

## Edge cases that need synthetic data

A few cases can't be exercised by the committed real data. These use the synthetic factory fixtures (`synthetic_dat_factory`, `synthetic_inps_csv_factory`, `synthetic_blank_folder`) which write to `tmp_path`. They are stubbed `NotImplementedError` and should be implemented as needed when the first test that uses them is written.

Known cases needing synthetic data:
- `SpacedTempCSV` with `freezing_point_depression_dict` missing a key (bug #7)
- `BlankCorrector._final_check` non-monotonic input (bugs #3, #4, #5)
- `FinalFileCreation._final_check` with NaN / negative / zero-leading rows (bug #10)
- `GraphDataCSV` edge cases with empty `last_4_i` (bug #2) — deferred to rewrite

