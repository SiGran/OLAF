# Rename `IS` → `instrument` + cold-plate DI background resolution

## Context

OLAF's stage-1 config identifies the instrument with a free-form `IS` string
(`olaf/config/models.py:53`, values like `"IS2"`, `"IS3a"`). Nothing branches on it — it is
pure header passthrough (`models.py:135`). The name is also an Ice-Spectrometer-ism that
does not generalise, and every stage-1 run silently assumes the INS workflow.

That assumption breaks for the **cold plate**. On the INS, the DI (deionized water)
background is a column *inside* the sample plate: the `Sample_N = inf` entry in
`dict_samples_to_dilution`, consumed at `olaf/processing/graph_data_csv.py:208-231`.
Cold-plate sample runs carry no DI column at all. The DI background instead lives in one or
more **separate `.dat` files in the same data folder**, which must each be reviewed and
temperature-binned in their own right; when there is more than one they are combined into a
single DI spectrum by averaging or summing frozen well counts per temperature bin.

This change renames `IS` to `instrument`, makes the cold-plate DI files a declared and
validated part of the config, and carries each DI run as far as a `frozen_at_temp_*.csv`
plus a combined DI file. Feeding that DI spectrum into the INP calculation is deliberately
**out of scope** (see below).

## Where the DI check belongs

Two different checks, two different layers:

| Check | Layer | Why there |
|---|---|---|
| **Do the declared DI `.dat` files exist?** | `MainConfig` validator, `olaf/config/models.py` | Fails the run *before* the GUI opens. Matches the existing precedent `_require_conditional_optional_keys` (`models.py:76-98`), and `load_config` already turns `ValidationError` into a readable message via `_validation_message` (`loader.py:80-124`). |
| **Does each DI already have a `frozen_at_temp_*.csv`? Is there a combined DI file?** | New `olaf/processing/di_background.py`, called from `olaf/main.py::run` | These are *derived artifacts* whose absence triggers work (a GUI pass). Runtime state, not config validity. |

The config validator touching the filesystem is new for this repo. It is acceptable because
it is gated on the cold-plate instrument — every existing config and all 46 tests in
`tests/test_config/test_config.py` (which build `MainConfig` with non-existent `data_folder`
paths via the `_main_data()` helper) keep passing untouched.

## Golden-fixture impact: none

Verified before planning — **no file under `tests/test_data/goldens/expected/` contains a
metadata header**; they are all bare CSV (`degC,dilution,INPS_L,...`). The rename therefore
breaks no golden and needs no regeneration.

Two golden *inputs* do carry `IS = ` in their headers
(`goldens/inputs/tbs bnf 03.21.25 s2 0_250a base/*.csv`), as does one provenance copy
(`tests/test_data/test_project/SGP 6.14.24 base/used_config_*.toml`). These are fixed
historical files read generically via `header_to_dict`, so stage 2/3 pass the old key
through unchanged. **Leave them exactly as they are** — they are a faithful record of what
old OLAF wrote, and real-world archived files will look the same.

## 1. The rename — `olaf/config/models.py`

Replace the field (keeping its position, so the header key order shifts only in name):

```python
instrument: str      # was: IS: str
```

Free-form `str`, not a `Literal` — it has to keep holding `"IS2"`, `"IS3a"`, and any future
unit name, so an enum would be brittle. Cold-plate behaviour keys off the value.

`to_header()` (`models.py:135`): `f"IS = {self.IS}\n"` → `f"instrument = {self.instrument}\n"`.

Add a normalising helper so a typo cannot silently fall back to the INS path — the
dangerous failure here is a cold-plate run processed as INS with no DI at all:

```python
@property
def is_cold_plate(self) -> bool:
    return re.sub(r"[^a-z]", "", self.instrument.lower()) == "coldplate"
```

This accepts `cold-plate`, `cold plate`, `Cold_Plate`, `coldplate`. Anything else is treated
as an ice spectrometer, unchanged from today's behaviour.

## 2. New cold-plate config fields — `olaf/config/models.py`

```python
di_files: list[Path] = Field(default_factory=list)
di_combined: Literal["avg", "sum", "single"] | None = None
```

`di_files` entries are relative to `data_folder` when relative, used as-is when absolute.
Expose the resolution once so the validator and `run()` agree:

```python
@property
def resolved_di_files(self) -> list[Path]:
    return [p if p.is_absolute() else self.data_folder / p for p in self.di_files]
```

New `@model_validator(mode="after")` — `_validate_cold_plate_di`:

- not cold-plate, but `di_files` or `di_combined` set → `ValueError`
  (`di_files`/`di_combined` only apply to `instrument = "cold-plate"`).
- cold-plate:
  - empty `di_files` → `ValueError` naming the field and pointing at the template.
  - **any resolved path that is not an existing file → `ValueError` listing every missing
    path.** This is the hard error the workflow needs.
  - `len > 1` and `di_combined is None` → `ValueError` (must pick `avg` or `sum`).
  - `len > 1` and `di_combined == "single"` → `ValueError` ("`single` combines nothing;
    list exactly one DI file or choose `avg`/`sum`").
  - `len == 1` and `di_combined is None` → default it to `"single"`.

DI plates share the sample plate's geometry, so `num_samples`, `wells_per_sample` and
`dict_samples_to_dilution` are reused as-is — no DI-specific geometry fields.

## 3. Loader hint — `olaf/config/loader.py`

`instrument` replacing a required field means every un-migrated stage-1 config now fails
both as "missing `instrument`" and "extra `IS`", so `detect_stage` (`models.py:285-301`)
returns `None` and `_validation_message` emits a misleading stage suggestion. Extend the
existing `moved_keys` special case (`loader.py:~110`) with a sibling branch: when the errors
show `extra_forbidden` on `IS` or `missing` on `instrument`, say plainly that `IS` was
renamed to `instrument`, and point at `configs/templates/main.example.toml`.

## 4. New module — `olaf/processing/di_background.py`

Thin orchestrator over existing pieces; no new numerics beyond the groupby.

```python
def find_frozen_at_temp(di_dat: Path) -> Path | None
```
Glob `di_dat.parent` for `frozen_at_temp_*{di_dat.stem}*.csv` — the `*` absorbs the
`reviewed_` infix that `SpacedTempCSV` inherits from the reviewed `.dat`
(`spaced_temp_csv.py:160-162` saves as `frozen_at_temp_{data_file.stem}.csv`). Resolve
multiple hits with `find_latest_file` (`olaf/utils/path_utils.py:22`). `None` if absent.

```python
def ensure_frozen_at_temp(di_dat: Path, config: MainConfig) -> Path
```
If `find_frozen_at_temp` hits, return it — **no GUI**. Otherwise run the stage-1 front half
for that one file, reusing exactly what `main.py` already uses: `FreezingReviewer`, then
`SpacedTempCSV(...).create_temp_csv(...)`. Pin both to the single DI file with
`includes=(di_dat.stem,)` so `DataHandler`'s substring matcher (`data_handler.py:53-66`)
cannot pick up a sample `.dat`. Re-glob afterwards; raise if it still isn't there.

```python
def combined_path(data_folder: Path, method: str, date: str) -> Path
def find_combined(data_folder: Path, method: str, date: str) -> Path | None
def combine_di(frozen_csvs, method, data_folder, date) -> Path
```
Naming `combined_DI_{method}_{MM.DD.YY}.csv`, mirroring stage 2's
`combined_blank_{earliest}_{latest}.csv` (`blank_correction.py:148-152`). The date is the
`DATE_PATTERN` match from the DI filename (`olaf/CONSTANTS.py:16`) — this is what makes the
existing-combined check specific to that DI set *and* that combination method.

`combine_di` short-circuits on `find_combined`. Otherwise `pd.concat` the `frozen_at_temp`
frames and `groupby("degC").agg("mean" | "sum")` over the `Sample_*` columns — same shape as
`BlankCorrector.average_blanks` (`blank_correction.py:116-146`), but on well counts, not
INPs. `avg` rounds back to integer counts; `sum` adds counts and leaves `wells_per_sample`
unchanged. `single` returns the one `frozen_at_temp` csv directly, writing nothing. Write
via `save_df_file` (`path_utils.py:61`) to keep the `(N)` collision and header conventions.

## 5. Wiring — `olaf/main.py::run`

One block at the top of `run()`, before the sample GUI, so DI gaps surface first:

```python
if config.is_cold_plate:
    frozen = [ensure_frozen_at_temp(p, config) for p in config.resolved_di_files]
    di_path = combine_di(frozen, config.di_combined, config.data_folder, di_date)
    print(f"cold-plate DI background: {di_path}")
```

Then keep the sample side from matching a DI file: pass
`excludes=(*existing, *(p.stem for p in config.resolved_di_files))` to the sample
`FreezingReviewer`, `SpacedTempCSV` and `GraphDataCSV` calls (`main.py:26-62`).

## 6. Template, configs and docs

- `configs/templates/main.example.toml:21` — `IS = "IS2"` → `instrument = "IS2"`, with a
  comment listing the cold-plate value, plus a commented cold-plate block showing
  `di_files = ["cold plate DI 07.16.25.dat"]` and `di_combined = "avg"` (values `avg`,
  `sum`, `single`; cold-plate only).
- `configs/RAM_CINC/main-process/A12_07.16.25_base.toml:9` — same rename. The stale
  duplicates under `configs/RAM_CINC/main/` and `configs/RAM_CINC/process/` are already
  queued for human deletion (TODO.md:232) — leave them.
- `configs/README.md` — "Migration notes" bullet: `IS` renamed to `instrument`; old configs
  are rejected at load with a hint.
- `README.md:105,117,175` — update the `IS` prose and the example config snippet.

## 7. Tests

`tests/test_config/test_config.py` — rename `"IS": "IS2"` → `"instrument": "IS2"` in the
`_main_data()` helper at :187 (one line covers all 46 existing tests). New cases: missing
`instrument` rejected; `IS` still present rejected with the rename hint; `to_header()` emits
`instrument = `; `is_cold_plate` true for the spelling variants and false for `IS2`;
cold-plate with a missing DI path rejected (real `tmp_path` `data_folder`); cold-plate with
no `di_files` rejected; `di_files` on a non-cold-plate config rejected; `single` with two
files rejected; one file defaults `di_combined` to `"single"`; `resolved_di_files` handles
relative and absolute.

`tests/test_scripts/test_script_wiring.py:78` — `IS="IS2"` → `instrument="IS2"`.

New `tests/test_processing/test_di_background.py` — `find_frozen_at_temp` matching across
the `reviewed_` infix and `(N)` versions; `combine_di` avg/sum arithmetic against a small
hand-built pair of frames; `find_combined` short-circuiting so no GUI opens when the
combined file already exists.

## Out of scope — flag, do not build

- **Consuming the DI spectrum in the INP calculation.** `graph_data_csv.py:208-231` still
  requires a `float("inf")` column from `dict_samples_to_dilution`. Injecting the combined
  DI as that column is the natural next step, but it lands in the Heavy-review numeric core
  (TODO_overhaul.md review tiers) and needs a `science-reviewer` pass plus before/after
  golden equivalence. A cold-plate run will get as far as a combined DI file and then still
  need its own `inf` handling.
- Bug #11 (`"blank" in self.treatment`) and the structured-filename refactor
  (TODO_overhaul.md Milestone E), which this brushes against but does not fix.

## Execution order

1. Branch `cold-plate-instrument` off `numerical-core`.
2. Commit this plan into the repo as `docs/plans/cold-plate-instrument.md`.
3. Rename `IS` → `instrument` everywhere (§1, §6, §7) and run the suite — it must be green
   with no golden changes. Commit separately, so the rename is reviewable on its own.
4. Add the DI config fields, validator and loader hint (§2, §3) + tests.
5. Add `di_background.py` and wire `main.py` (§4, §5) + tests.
6. `ruff check olaf/`, `mypy olaf/`, full suite.

## Verification

1. `ruff check olaf/ && mypy olaf/` — the new `Literal`, properties and module type-clean.
2. `pytest tests/ -m "not gui"` — full suite green, **goldens byte-identical** (proof no
   numeric path moved and the rename really is header-only).
3. `git diff --stat tests/test_data/` after the run must be empty.
4. INS regression: `python -m olaf.main configs/RAM_CINC/main-process/A12_07.16.25_base.toml`
   behaves exactly as before, with `instrument = IS2` in the output header.
5. Negative config check, no GUI may open: a scratch cold-plate config pointing at a
   `di_files` entry that does not exist must fail the load naming the missing path.
6. Cold-plate happy path, in a scratch copy of a data folder with two DI `.dat` files: first
   run opens the GUI once per DI (plus the sample) and writes `combined_DI_avg_<date>.csv`;
   re-running finds both `frozen_at_temp` files and the combined file and opens **no** DI GUI.

---

## As built — deltas from the plan above

Implemented on branch `cold-plate-instrument`. Where the code differs from the plan:

- **No golden regeneration was needed.** Confirmed empirically: `git status tests/test_data/`
  stays clean across the full suite, and no `goldens/expected/` file carries a header.
- **`excludes` was threaded through the GUI stack.** `FreezingReviewer` had no `excludes`
  parameter, so the sample review could still match a DI `.dat` whose name happened to
  contain the treatment. Added an optional `excludes: tuple = ()` to `FreezingReviewer` →
  `ButtonHandler` → `DataLoader`. With `di_excludes = ()` on a non-cold-plate run, `main.py`
  passes exactly the previous defaults (`("frozen",)`, `("INPs_L", "dict")`, `()`), so this
  is an exact no-op for every existing workflow.
- **`resolve_di_background(config)`** is the single entry point `main.py` calls; it wraps
  `ensure_frozen_at_temp` → `di_dates` → `combine_di`.
- **A `di_count` column** was added to the combined file. DI runs need not cover the same
  temperature range, so a bin fed by fewer runs than its neighbours would otherwise be
  silently indistinguishable — for `sum` especially, that would understate the bin. This
  follows the `blank_count` precedent in `BlankCorrector.average_blanks`.
- **`_match_versions` replaced the plan's trailing-wildcard globs.** A trailing `*` let one
  name swallow another that merely starts the same way: `combined_DI_avg_07.16.25` matched
  `combined_DI_avg_07.16.25_07.17.25.csv`, a different DI set. Matching is now the exact
  name plus its `(N)` versions, covered by regression tests.
- **The combined file carries a provenance header** (`di_combined`, `di_date`,
  `di_source_files`) via `save_df_file`. Read it back with `read_with_flexible_header`, not
  a bare `pd.read_csv`.

Still out of scope, unchanged: feeding the DI spectrum into `graph_data_csv.py`. A
cold-plate run produces its combined DI file and then still needs `inf`-column handling.
