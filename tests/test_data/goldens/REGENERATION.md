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

Highest value first:

1. **A blank-correction fixture containing `ERROR_SIGNAL` rows.** Without one, the bug #5
   behavior change is unpinned end-to-end. Pick a real spectrum with a `-9999` gap and a
   drop after it — exactly the case Part 1 item 1 decides.
2. **A stage-1 `INPs_L` golden** for `compute_INPs_L`, so the INP/L engine has a
   regression fixture at all. Input already exists at
   `goldens/inputs/sgp_2_21_24_base/reviewed.dat`.
3. **A fixture producing `qc_flag = 1`** so the ordinary monotonicity correction is locked.

---

## Session checklist

- [ ] Part 1 decisions recorded in `TODO_overhaul.md`
- [ ] Suite green before regenerating
- [ ] Goldens regenerated per module, diff reviewed line by line with the scientist
- [ ] Suite green after regenerating
- [ ] Two `final_file_creation` tests un-skipped (Part 3)
- [ ] `ERROR_SIGNAL` fixture curated (Part 4.1)
- [ ] Stage-1 `INPs_L` golden added (Part 4.2)
- [ ] `TODO_overhaul.md` A.3 human item closed out
