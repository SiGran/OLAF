# SGP 2.21.24 base — canonical primary fixture

Status: **complete** ✅

| File | Source (in real folder) | Used by |
|---|---|---|
| `reviewed.dat` | `test1_reviewed_sgp ment 02.21.24 a base.dat` | `SpacedTempCSV` tests, `DataHandler` tests, `FreezingReviewer` GUI |
| `frozen_at_temp_expected.csv` | `test1_VERIFIED_changed_frozen_at_temp_sgp men 02.21.24 a base.csv` | `SpacedTempCSV.create_temp_csv` golden |
| `frozen_at_temp_changed.csv` | `test1_changed_frozen_at_temp_sgp men 02.21.24 a base.csv` | reference / alt comparison |
| `inps_L_expected.csv` | `INPs_L_frozen_at_temp_test1_reviewed_sgp ment 02.21.24 a base.csv` | `GraphDataCSV` (deferred until rewrite) |
| `dat_images/Image_{1,2,10}.png` | `dat_Images/Image_{1,2,10}.png` | `FreezingReviewer` smoke test |

Dilution dict used to produce these files: **side A**, 6 samples
`{Sample_0:1, Sample_1:11, Sample_2:121, Sample_3:1331, Sample_4:14641, Sample_5:inf}`

`num_samples=6`, `wells_per_sample=32`, `sample_type="air"`.

