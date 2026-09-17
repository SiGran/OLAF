# Test Data Goldens

This is the **only** committed test-data tree. All tests should reference files
under `tests/test_data/goldens/`, never the raw `tests/test_data/<real-folder>/`
trees (those are local-only and untracked).

## Structure

```
goldens/
├── inputs/                      # canonical inputs for tests + their expected outputs
│   ├── sgp_2_21_24_base/        # primary SGP fixture (used by SpacedTempCSV tests)
│   │   ├── reviewed.dat                    # input: reviewed .dat (8970 rows)
│   │   ├── frozen_at_temp_expected.csv     # golden: SpacedTempCSV output (verified)
│   │   ├── frozen_at_temp_changed.csv      # alt golden: pre-verification output
│   │   ├── inps_L_expected.csv             # golden: GraphDataCSV final INPs/L
│   │   └── dat_images/                     # 3 images for FreezingReviewer GUI smoke
│   ├── sgp_3_28_24_base/        # needs human curation — see .NEEDED.md
│   ├── kcg_09_23_24_base/       # needs human curation — see .NEEDED.md
│   ├── capek/                   # needs human curation — see .NEEDED.md
│   └── test_project/            # needs human curation — see .NEEDED.md
└── expected/                    # per-test goldens generated via OLAF_REGEN_GOLDEN=1
    └── (empty for now)
```

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
