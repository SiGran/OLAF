# Data wanted from the scientists

**Short list on purpose.** Most remaining test gaps can be filled from files already in this
repository — those are a developer job and are not listed here. What follows is only the
things that genuinely need someone with access to the real campaign data, or a scientific
judgement call.

Two questions to answer, three files to find (a fourth, the TBS run, has been supplied). Nothing here is urgent enough to interrupt
fieldwork; it is a "next time you are in the data" list.

Last verified against the repository on 2026-09-17.

---

## Part 1 — Two questions (no files needed, ~5 minutes)

### Q1. A peroxide sample is labelled `heat`. Which is right?

File: `goldens/inputs/capek/KCG 7.09.24 peroxide/INPs_L_frozen_at_temp_reviewed_capek 7.09.24 a peroxide.csv`

Its folder and filename say **peroxide**, but line 8 of the file header says:

```
treatment = heat
```

The original in `tests/test_data/capek/KCG 7.09.24 peroxide/` says the same, so this is not a
copying mistake — it is in the source data.

**Why it matters:** the final ARM file carries a `Treatment_flag` taken from that header
(0 = untreated, 1 = heat, 2 = peroxide). As it stands this sample would be published as heat
treated.

**What we need:** was this run peroxide or heat? If peroxide, the header needs fixing at the
source and anywhere it was already published.

### Q2. Which SGP 2.21.24 binned file is the verified one?

Two files in `tests/test_data/SGP 2.21.24 base/` claim to be the binned frozen-well counts:

| File | Temperature column |
|---|---|
| `test1_VERIFIED_changed_frozen_at_temp_sgp men 02.21.24 a base.csv` | `…` — corrupted |
| `test1_frozen_at_temp_sgp men 02.21.24 a base.csv` | `degC` — correct |

The one marked **VERIFIED** has a corrupted header: its temperature column is named with a
literal ellipsis character instead of `degC`, which no part of OLAF can read. The copy in
`goldens/inputs/sgp_2_21_24_base/frozen_at_temp_expected.csv` inherited the problem.

**What we need:** which of the two is the manually verified output? If it is the VERIFIED
one, we will repair the column name and keep the numbers untouched.

---

## Part 2 — Files to find

For each: **copy** the file, never move it. Small CSVs only — a few kB each. Keep the
original folder name (it carries the `MM.DD.YY` date pattern the code reads).

### F1. A spectrum containing a `-9999` gap with real values *after* it ⭐ highest value

**Put it in:** `goldens/inputs/error_signal_gap/` (create the folder)

**What to look for:** any `INPs_L_*.csv` or `blank_corrected_*.csv` where a `-9999` row sits
in the **middle** of the spectrum, with ordinary numbers both above and below it — not the
usual run of `-9999` at the cold end.

**Why:** the branch fixes a bug where a physically impossible drop just after a `-9999` was
silently kept. We have no example of this anywhere, so the fix is only covered by artificial
tests. One real spectrum would let us lock it down properly.

**If you cannot find one, say so** — that is a useful answer. It means the bug never affected
real output, which is worth recording.

### F2. A project folder spanning several dates and sites

**Put it in:** `goldens/inputs/multi_date_project/`

**What we need:** the `INPs_L_*.csv` from
- one blank folder covering a date range, and
- three or four sample folders on **different dates**, ideally from **two different sites**.

Roughly 5–8 files.

**Why:** our only project fixture (capek) is one site on one day, so the code that groups
results by site and date is untested against real data.

### F3. A TBS (tethered balloon) experiment — ✅ **DONE, thank you**

Supplied 2026-09-17 as `goldens/inputs/tbs bnf 03.21.25 s2 0_250a base/`:
`BNF_M1_TBS`, 2025-03-21, `lower_altitude = 0`, `upper_altitude = 272`, with the raw and
reviewed `.dat` plus the INPs_L and blank-corrected CSVs.

It turned out to be worth more than the altitude coverage it was asked for. Its
blank-corrected file uses the current 6-column schema **including `qc_flag`, with 11 of its
30 rows flagged `1`** — real monotonicity corrections, which no other fixture had. That makes
it the first fixture able to pin the correction logic against real data, and the first with a
modern-schema blank-corrected file.

### F4. A soil sample experiment

**Put it in:** `goldens/inputs/soil_sample/`

**What we need:** one `INPs_L_*.csv` from a soil run, plus the `dry_mass` value used for it.

**Why:** soil samples use a different concentration formula (`vol_susp / dry_mass` instead of
air volume). That branch has never been run against real data.

---

## How to hand it over

Copy the files into the folders above, then tell whoever is handling the merge. Or just point
at the source folders and let them do the copying — that is often faster and avoids
transcription mistakes.

Please do **not** edit any numbers to "clean them up". Odd values are often the exact cases
worth capturing.

## What happens next

Each file becomes a *golden*: a frozen copy of the correct output that the test suite checks
on every change. Once one is in place, any future edit that would alter those numbers fails
immediately instead of quietly shipping. Anything you flag as wrong gets fixed first — a
golden must never record a known-bad number.
