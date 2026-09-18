# SGP 2.21.24 base — canonical primary fixture

Status: **complete ✅** (re-verified 2026-09-17)

`frozen_at_temp_expected.csv` was re-curated on 2026-09-17. It previously came from
`test1_VERIFIED_changed_...csv`, whose temperature column was named with a literal `…`
(U+2026) instead of `degC`, making it unreadable. It now comes from
`test1_frozen_at_temp_...csv`, whose **frozen-well counts are cell-for-cell identical** -
the only other difference was whole-number temperatures written `-5` rather than `-5.0`. No
numbers changed; the file is simply now loadable.

Open question for a scientist, tracked in `../../FIXTURES_WANTED.md` Q2: the sibling
`frozen_at_temp_changed.csv` carries 9 different well counts, and it is not settled which set
is the reviewed one. Neither can be regenerated from the `reviewed.dat` committed here, which
covers only -20.0 to -29.5 degC while both curated files start at -4.5.

| File | Source (in real folder) | Used by |
|---|---|---|
| `reviewed.dat` | `test1_reviewed_sgp ment 02.21.24 a base.dat` | `SpacedTempCSV` tests, `DataHandler` tests, `FreezingReviewer` GUI |
| `frozen_at_temp_expected.csv` | `test1_VERIFIED_changed_frozen_at_temp_sgp men 02.21.24 a base.csv` | `SpacedTempCSV.create_temp_csv` golden |
| `frozen_at_temp_changed.csv` | `test1_changed_frozen_at_temp_sgp men 02.21.24 a base.csv` | reference / alt comparison |
| `inps_L_expected.csv` | `INPs_L_frozen_at_temp_test1_reviewed_sgp ment 02.21.24 a base.csv` | header-parsing fixture in `test_df_utils` (not a numerical golden) |
| `frozen_at_temp_expected.csv` | `test1_frozen_at_temp_sgp men 02.21.24 a base.csv` (re-curated 2026-09-17) | stage-1 develop-parity golden |
| `dat_images/Image_{1,2,10}.png` | `dat_Images/Image_{1,2,10}.png` | `FreezingReviewer` smoke test |

Dilution dict used to produce these files: **side A**, 6 samples
`{Sample_0:1, Sample_1:11, Sample_2:121, Sample_3:1331, Sample_4:14641, Sample_5:inf}`

`num_samples=6`, `wells_per_sample=32`, `sample_type="air"`.
