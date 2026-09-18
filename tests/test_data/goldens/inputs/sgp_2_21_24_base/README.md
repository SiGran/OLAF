# SGP 2.21.24 base — canonical primary fixture

Status: **mostly complete** ⚠️ (re-verified 2026-09-17)

Two caveats found when auditing:
- `frozen_at_temp_expected.csv` is **unreadable**: its temperature column is named with a
  literal `…` (U+2026) instead of `degC`, so no engine can load it. No test references it.
  Repair the header before relying on it.
- `frozen_at_temp_changed.csv` is referenced by no test.
- `inps_L_expected.csv` is used only as a header-parsing fixture in `test_df_utils`, not as a
  numerical golden. The `GraphDataCSV` rewrite it was "deferred until" has since landed, so it
  could now back a real golden.

| File | Source (in real folder) | Used by |
|---|---|---|
| `reviewed.dat` | `test1_reviewed_sgp ment 02.21.24 a base.dat` | `SpacedTempCSV` tests, `DataHandler` tests, `FreezingReviewer` GUI |
| `frozen_at_temp_expected.csv` | `test1_VERIFIED_changed_frozen_at_temp_sgp men 02.21.24 a base.csv` | `SpacedTempCSV.create_temp_csv` golden |
| `frozen_at_temp_changed.csv` | `test1_changed_frozen_at_temp_sgp men 02.21.24 a base.csv` | reference / alt comparison |
| `inps_L_expected.csv` | `INPs_L_frozen_at_temp_test1_reviewed_sgp ment 02.21.24 a base.csv` | header-parsing fixture in `test_df_utils` (not a numerical golden) |
| `dat_images/Image_{1,2,10}.png` | `dat_Images/Image_{1,2,10}.png` | `FreezingReviewer` smoke test |

Dilution dict used to produce these files: **side A**, 6 samples
`{Sample_0:1, Sample_1:11, Sample_2:121, Sample_3:1331, Sample_4:14641, Sample_5:inf}`

`num_samples=6`, `wells_per_sample=32`, `sample_type="air"`.
