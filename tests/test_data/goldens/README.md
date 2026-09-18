# Test Data Goldens

This is the committed test-data tree. Tests should reference files under
`tests/test_data/goldens/`, never the raw `tests/test_data/<real-folder>/` trees, which are
local-only and untracked.

> Not quite the *only* committed tree: four legacy files under
> `tests/test_data/SGP 2.21.24 base/` are still tracked and used by `sgp_test_folder`. Those
> tests skip in CI because the versioned copies they need are untracked. Migrating them here
> is listed under Coverage gaps below.

## Structure

Verified 2026-09-17. `inputs/` holds committed test inputs; `expected/` holds generated
goldens.

```
goldens/
├── inputs/
│   ├── sgp_2_21_24_base/        ✅ curated — primary SGP fixture
│   │   ├── reviewed.dat                    input: reviewed .dat, used by 16 references
│   │   ├── frozen_at_temp_expected.csv     backs a stage-1 develop-parity golden (the
│   │   │                                   corrupted "…" column name was repaired
│   │   │                                   2026-09-17; counts unchanged)
│   │   ├── frozen_at_temp_changed.csv      referenced by no test
│   │   ├── inps_L_expected.csv             used only as a header-parsing fixture in
│   │   │                                   test_df_utils, NOT as a numerical golden
│   │   └── dat_images/                     3 images for the FreezingReviewer GUI smoke test
│   ├── sgp_3_28_24_base/        ✅ curated (reviewed.dat + frozen_at_temp_expected.csv)
│   ├── kcg_09_23_24_base/       ✅ curated (all 4 files present and in use)
│   ├── capek/                   ✅ curated — blanks + base/heat/peroxide; final_files/ EMPTY
│   └── test_project/            ❌ EMPTY — nothing curated yet
└── expected/
    ├── test_spaced_temp_csv/    3 goldens
    ├── test_blank_correction/   2 goldens
    ├── test_develop_parity/     5 goldens (generated from develop — see below)
    └── test_final_file_creation/ ❌ does not exist; stage 3 has no golden coverage
```

## Coverage gaps (what still needs adding)

> Anything on this list that needs **real campaign data or a scientist's judgement** is
> written up for them in [`FIXTURES_WANTED.md`](FIXTURES_WANTED.md). Everything else is a
> developer job and can be done from files already in this repository.


Ranked. Status verified 2026-09-17 by running the suite, not by reading these docs.

1. ~~**Stage 3 (`FinalFileCreation`) has no golden at all.**~~ **CLOSED 2026-09-17** by
   `TestStage3Parity` in `tests/test_integration/test_develop_parity.py`, which runs stage 2
   first to produce a 6-column input instead of requiring a curated one, then pins the ARM
   body (111 rows, all three `Treatment_flag` values). The two `TestRealProjectIntegration`
   tests still skip, but they are no longer the only stage-3 coverage.
2. **`inputs/test_project/` is empty**, so `test_test_project_final_files_golden` can never
   run. This is now the only *skipping* test without an equivalent elsewhere: it would add
   multi-date and multi-site grouping, which the single-day capek fixture cannot cover. Note
   the real `tests/test_data/test_project/` is 4.6 GB — curate only the handful of small CSVs
   needed, never the tree.
3. **`inputs/capek/final_files/` is empty**, so the ARM-format output of
   `create_all_final_files` is unpinned.
4. **`sgp_3_28_24_base/` is curated but unused.** Its `.NEEDED.md` names a
   `test_air_sample_sgp_3_28_golden` that was never written. The fixture is ready; only the
   test is missing. (It *is* used by the develop-parity tests.)
5. ~~**`sgp_2_21_24_base/frozen_at_temp_expected.csv` is unreadable**~~ **FIXED 2026-09-17.**
   Re-curated from `test1_frozen_at_temp_sgp men 02.21.24 a base.csv`, whose well counts are
   cell-for-cell identical to the corrupted copy (only the column name and `-5` vs `-5.0`
   formatting differed), so no numbers changed. The fixture is now a third stage-1
   develop-parity case.

Lower priority: `frozen_at_temp_changed.csv` is referenced by no test; the four tracked
files under `tests/test_data/SGP 2.21.24 base/` should migrate here so their tests stop
skipping in CI.

## Conventions

- Use **clean filenames** in goldens/ (`reviewed.dat`, not
  `test1_reviewed_sgp ment 02.21.24 a base.dat`). Spaces in filenames cause
  endless quoting pain.
- File contents are **bit-identical copies** of curated real outputs. Never
  hand-edit them — if you need different values, point a test at a different
  golden, or regenerate via `OLAF_REGEN_GOLDEN=1`.
- The original messy filenames in the real-data folders stay there (the agent
  cannot delete them); see `TODO.md` Human-Needs-To-Do for cleanup.

## Workflow for adding a new fixture

1. Identify what real file you want to use (e.g. a representative
   `blank_corrected_*.csv` from `capek/KCG 7.09.24 base/`).
2. Copy it into `goldens/inputs/<folder>/<clean_name>.csv`. **Copy, never move
   or symlink** — keeps the real folder intact and the golden self-contained.
3. Update the relevant test fixture in `tests/conftest.py` to point at the new
   path (or use an existing fixture if one fits).
4. Commit the file. Goldens are part of the repo from now on.

## Develop-parity goldens (`expected/test_develop_parity/`)

These are generated from **develop's** engines, not from this branch, and must then pass
unchanged here - that is what makes them proof rather than a self-portrait. Regenerate only
with:

```bash
bash scripts/regen_develop_baseline.sh      # swaps develop's two engines in, then restores
uv run pytest -m "not gui" -q               # must pass unchanged afterwards
```

They are one third of the assurance story; see
`tests/test_integration/test_develop_parity.py` for the other two (differential fuzzing over
generated spectra, and `scripts/scan_trigger_conditions.py` for checking a real archive).

## Regenerating goldens (`expected/`)

> For a full re-curation — the decisions that need a scientist, un-skipping the
> `final_file_creation` tests, and which fixtures are still missing — follow
> [`REGENERATION.md`](REGENERATION.md) in this folder.

For tests that use `assert_csv_matches_golden(actual, golden_path)`:

```bash
OLAF_REGEN_GOLDEN=1 pytest tests/test_processing/test_spaced_temp_csv.py
```

The helper writes the actual output to `golden_path` (creating parents) and
skips the test. Inspect with `git diff`, then `git add` if correct.
