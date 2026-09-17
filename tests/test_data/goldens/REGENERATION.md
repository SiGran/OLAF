# Golden regeneration protocol

A working session run **together with a scientist**. The mechanics take about 20 minutes;
the decisions in Part 1 are the real work and should be settled before anything is
regenerated.

Read `README.md` in this folder first for what goldens are and where they live.

---

## Why this session is needed

Milestone A of the overhaul (`TODO_overhaul.md`) changed how three things behave. All
existing goldens still pass — **this session is not about repairing broken fixtures.** It
exists because of what the goldens *do not yet cover*:

| Gap | Consequence today |
| --- | --- |
| No golden contains an `ERROR_SIGNAL` (`-9999`) row | The bug #5 fix (correcting a non-monotonic drop across a gap) is pinned by unit tests only, not by any end-to-end fixture |
| No golden contains a `qc_flag = 1` row | The monotonicity correction path has never been locked against real data |
| No golden pins `GraphDataCSV.compute_INPs_L` output | Stage 1 — the INP/L engine itself — has no regression fixture. `inputs/sgp_2_21_24_base/inps_L_expected.csv` exists but is only used as a header-parsing fixture in `test_df_utils.py` |
| `test_project/` and `capek/` blank-corrected inputs use the legacy 5-column schema | Two golden tests in `test_final_file_creation.py` skip instead of running |

The committed blank-correction golden (`capek 7.09.24 a base`) has 37 rows, **zero**
`-9999` rows and **zero** `qc_flag = 1` rows. It passes before and after Milestone A
precisely because it never touches the changed code paths.

---

## Part 1 — Decide these first (scientist's call, not the code's)

Each item states what the code does **today**. Confirm or overrule before regenerating,
because the answer changes what the new goldens should contain.

1. **Correcting across an `ERROR_SIGNAL` gap.** When INP/L drops with decreasing
   temperature, the value is replaced with the previous one and flagged. Before Milestone
   A, a drop sitting immediately after a `-9999` gap was silently kept. Now the code walks
   back past the gap and corrects against the last usable value.
   *Question:* should a gap break the monotonicity chain (old behavior, arguably "we don't
   know what happened across the gap"), or bridge it (new behavior)?
   → `olaf/processing/blank_correction.py`, `_final_check`

2. **Confidence intervals inherited across a gap.** When a correction bridges a gap, the
   replacement `upper_CI` is combined from a temperature bin that may be several
   `TEMP_STEP`s away, and `lower_CI` is inherited outright.
   *Question:* is inheriting a CI from a distant bin acceptable, or should a bridged
   correction widen the CI, or emit `ERROR_SIGNAL` instead?

3. **Two different error-combination formulas coexist.** Blank subtraction propagates
   error as root-**sum**-square: `sqrt(sample² + blank²)`. The monotonicity correction in
   `_final_check` uses `math_utils.rms`, which is root-**mean**-square — for two terms
   that is `sqrt((a² + b²)/2)`, i.e. RSS ÷ √2, about 29 % narrower.
   *Question:* is that intentional (different physical meaning) or a latent bug? Nothing
   was changed here; the inconsistency is pre-existing and needs a scientist to rule.

4. **Zero baseline.** The code never corrects a value against a row whose INP/L is `0`;
   the walk-back stops there and the current value is left alone. Kept deliberately from
   the legacy implementation.
   *Question:* correct, or should a zero row be skipped like `ERROR_SIGNAL`?

5. **`qc_flag` vocabulary.** Currently `0` = untouched, `1` = replaced for monotonicity.
   *Question:* worth distinguishing a plain correction from a gap-bridging correction
   (e.g. `2`) so the ARM output records which happened? Changing this changes the ARM file
   schema, so decide now rather than after regeneration.

Record the answers in `TODO_overhaul.md` under Milestone A.3 as you go — the reasoning is
worth more later than the decision alone.

---

## Part 1b — Build the before/after comparison (do this *with* Part 1)

The Part 1 questions are much easier to answer against real numbers than in the abstract.
Generate the pre-fix output as a **throwaway reference** and diff it against current code.

> Do **not** commit goldens generated from pre-fix code. They would pin the very behavior
> Milestone A fixed — e.g. locking in an uncorrected non-monotonic drop as "expected" —
> and you would have to regenerate a second time after merging.

The pre-fix engine is whatever `develop` held before the Milestone A merge; extract just
the module rather than checking the whole branch out:

```bash
SCRATCH=$(mktemp -d)
git show <pre-milestone-A-commit>:olaf/processing/blank_correction.py > "$SCRATCH/bc_old.py"
```

Then run both against the same input and diff. For the `ERROR_SIGNAL`-gap case the
difference looks like this (drop at -21.5 after a gap at -21.0):

| degC | INPS_L before | INPS_L after | upper_CI before | upper_CI after | qc_flag |
| --- | --- | --- | --- | --- | --- |
| -21.0 | -9999 | -9999 | -9999 | -9999 | 0 -> 0 |
| -21.5 | 30.0 | **50.0** | 45.0 | **61.85** | 0 -> **1** |

That single row is Part 1 items 1 and 2 made concrete: the value is pulled up to the last
usable reading, and the CI it inherits comes from a bin two `TEMP_STEP`s away. Ask the
scientist to rule on that row, then regenerate.

Recommended order for the whole session:

1. Curate the input fixtures first — inputs do not depend on which code version you run.
2. Generate outputs from both the pre-fix and current engine into a scratch folder.
3. Diff, decide (Part 1), record the reasoning.
4. Only then regenerate and commit the goldens (Part 2).

---

## Part 2 — How to regenerate

**Where:** repository root, on a branch (never directly on `develop`).

```bash
git checkout -b goldens/milestone-a-recuration
```

The mechanism is `assert_csv_matches_golden` (`tests/conftest.py:213`). With
`OLAF_REGEN_GOLDEN` set to any non-empty value it **writes** the actual output to the
golden path and **skips** the test; otherwise it compares with `rtol=1e-9` and
`check_dtype=False`.

1. **Confirm green before touching anything.** A regen run on top of an unexpected failure
   bakes the failure into the fixture.
   ```bash
   uv run pytest -m "not gui" -q
   ```

2. **Regenerate one module at a time**, never the whole suite at once — a narrow diff is
   the entire point.
   ```bash
   OLAF_REGEN_GOLDEN=1 uv run pytest tests/test_processing/test_blank_correction.py -q
   ```
   Expect **skips**, not passes: each regenerated test skips with
   `regenerated golden: <path>`.

3. **Read the diff with the scientist.** This is the step that matters.
   ```bash
   git diff --stat tests/test_data/goldens/
   git diff tests/test_data/goldens/
   ```
   Numbers that changed must be explainable by a decision from Part 1. Anything else is a
   bug, not a new golden — stop and investigate.

4. **Re-run normally to confirm the new goldens pass.**
   ```bash
   uv run pytest -m "not gui" -q
   ```

5. **Commit the fixtures with the reasoning**, one commit per module, stating which Part 1
   decision drove the change.

> Goldens are written with `index=False, lineterminator="\n"`. Never hand-edit one — if a
> value looks wrong, fix the code or the input fixture and regenerate.

---

## Part 3 — Un-skipping the two `final_file_creation` tests

These two skip because their **input** fixtures are stale, so `OLAF_REGEN_GOLDEN` alone
will not help — it regenerates expected outputs, not inputs.

`test_test_project_final_files_golden` and `test_capek_final_files_golden` require at least
one `blank_corrected_*.csv` carrying the 6-column header
(`degC,dilution,INPS_L,lower_CI,upper_CI,qc_flag`) in their project folder. The committed
ones predate `qc_flag`.

1. Run stage 2 on the real `capek` / `test_project` data with current code to produce
   fresh `blank_corrected_*.csv` files.
2. Copy one representative file per treatment folder into
   `goldens/inputs/<folder>/` using clean filenames (see `README.md` conventions — copy,
   never move).
3. Re-run the two tests; they should now execute instead of skipping, then regenerate
   their expected outputs per Part 2.

---

## Part 4 — New fixtures worth curating in the same session

A survey of every sample folder in `tests/test_data/test_project/` (stage 2 re-run with
current code, 2026-09-17) found these concrete candidates.

### 4.1 `qc_flag = 1` fixture — **use `SGP 6.20.24 base redo`**

40 rows, **4 real monotonicity corrections**, no `ERROR_SIGNAL`. Source:
`INPs_L_frozen_at_temp_reviewed_sgp 6.20.24 a base redo2.csv`.

| degC | dilution | INPS_L | lower_CI | upper_CI | qc_flag |
| --- | --- | --- | --- | --- | --- |
| -16.5 | 11 | 0.360172 | 0.169566 | 0.149757 | 1 |
| -18.5 | 121 | 0.947794 | 0.637230 | 0.587333 | 1 |
| -19.0 | 121 | 0.947794 | 0.637230 | 0.728434 | 1 |
| -19.5 | 121 | 0.947794 | 0.637230 | 0.819991 | 1 |

The three-row plateau at 0.947794 is the correction holding a value flat across falling
temperature, with `lower_CI` inherited unchanged and `upper_CI` growing through repeated
`rms` combination — **Part 1 items 2 and 3 visible in real data**. Note the -16.5 row,
where `upper_CI` (0.1498) came out *smaller* than `lower_CI` (0.1696): the `rms`
combination shrank the upper half-width below the lower one. Ask the scientist whether
that is physically acceptable before pinning it in a golden.

### 4.2 `ERROR_SIGNAL` fixture — `SGP 7.20.24 peroxide` (partial)

24 rows of which **23 are `-9999`**, contiguous and trailing. Pins the `THRESHOLD_ERROR`
replacement path, which no golden currently covers. It is degenerate (almost the whole
spectrum is error) and it does **not** exercise bug #5.

### 4.3 Bug #5 (gap followed by a drop) — **no real data available**

Scanned every processed `.csv` under `tests/test_data/` and `data/`, then re-ran stage 2
over all 12 sample folders of `test_project`. **Zero** spectra contain a usable value after
an `ERROR_SIGNAL` gap, so none can trigger the bug #5 correction. Every `-9999` run found
is trailing: the threshold replacement fires at the cold tail, where nothing follows.

Two consequences:

- The real-world blast radius of bug #5 in this archive appears to be **nil** — worth
  saying out loud to the scientists, since it lowers the urgency of re-processing old data.
- A fixture for it has to come from the wider campaign archive (look for a spectrum whose
  below-CI rows are scattered mid-spectrum rather than at the cold tail) or be derived by
  hand from a real spectrum. Until then bug #5 stays covered by unit tests only.

### 4.4 Stage-1 `INPs_L` golden

Still needed, for `compute_INPs_L`; input already exists at
`goldens/inputs/sgp_2_21_24_base/reviewed.dat`.

### 4.5 Blockers found while surveying

Only 4 of 12 sample folders could be processed at all:

- 4 folders (`SGP 5.15.24 heat/peroxide`, `SGP 6.02.24 heat/peroxide`) die with a bare
  `KeyError: 'proportion_filter_used'` — legacy `INPs_L` headers predating that field.
- 4 folders have no `INPs_L` file at all.
- `find_latest_file` prefers the headerless `INPs_L__*.csv` (double underscore) variant
  over the proper one, so `SGP 6.20.24 base redo` also crashes until that file is moved
  aside. Whatever is curated into `goldens/inputs/` must use the single-underscore,
  full-header file.

---

## Session checklist

- [ ] Input fixtures curated first (including one with an `ERROR_SIGNAL` gap)
- [ ] Before/after comparison generated into a scratch folder (Part 1b), never committed
- [ ] Part 1 decisions recorded in `TODO_overhaul.md`
- [ ] Suite green before regenerating
- [ ] Goldens regenerated per module, diff reviewed line by line with the scientist
- [ ] Suite green after regenerating
- [ ] Two `final_file_creation` tests un-skipped (Part 3)
- [ ] `ERROR_SIGNAL` fixture curated (Part 4.1)
- [ ] Stage-1 `INPs_L` golden added (Part 4.2)
- [ ] `TODO_overhaul.md` A.3 human item closed out
