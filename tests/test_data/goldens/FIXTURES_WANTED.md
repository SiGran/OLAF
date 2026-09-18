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

*Q2's header half was
resolved on 2026-09-17; only its second half still needs an answer.*

### Q1. A peroxide sample is labelled `heat` in its header. Which is right?

File: `goldens/inputs/capek/KCG 7.09.24 peroxide/INPs_L_frozen_at_temp_reviewed_capek 7.09.24 a peroxide.csv`

Its folder and filename say **peroxide**, but line 8 of the file header says:

```
treatment = heat
```

The original in `tests/test_data/capek/KCG 7.09.24 peroxide/` says the same, so this is not a
copying mistake — it is in the source data.

**Why it matters — and what it does *not* affect.** We checked
(`final_file_creation.py:95-99`): the ARM `Treatment_flag` is read from the **filename**, not
from this header, so the published ARM file labels this sample correctly as peroxide. The
wrong header is not currently corrupting released data.

Where it does show up is anything that reads the header's `treatment` field: the plot
filenames and the "Treatment:" labels drawn on the INP spectrum plots
(`plot_utils.py:62,104,188,220`) would say *heat* for this peroxide sample. It is also
simply a mislabelled file, which is worth correcting before it misleads someone.

**What we need:** was this run peroxide or heat? If peroxide, the header should be fixed at
the source.

### Q2. Which SGP 2.21.24 binned counts are the reviewed ones?

**The header part of this question is resolved — no action needed there.** The file marked
`VERIFIED` had a corrupted temperature column name (a literal `…` instead of `degC`), but we
compared it cell by cell against `test1_frozen_at_temp_sgp men 02.21.24 a base.csv` and the
**frozen-well counts are identical**. The only other difference is cosmetic: whole-number
temperatures written `-5` instead of `-5.0`. The golden has been repaired from the
clean-header copy, so no numbers changed.

**What is still worth a look.** A third file,
`test1_changed_frozen_at_temp_sgp men 02.21.24 a base.csv`, has **9 different well counts**
across 8 temperatures:

| degC | change |
|---|---|
| -9.5 | Sample_5: 12 → 13 |
| -10.5 | Sample_4: 8 → 9, Sample_5: 26 → 30 |
| -11.5 | Sample_4: 18 → 19 |
| -20.5 | Sample_4: 32 → 31 |
| -24.0 | Sample_2: 15 → 16 |
| -25.5 | Sample_0: 5 → 6 |
| -26.0 | Sample_1: 13 → 14 |
| -29.0 | Sample_0: 14 → 15 |

These look like manual well-count adjustments from the review GUI (mostly ±1, plus one +4).

**What we need:** which set is the reviewed, publishable one — the counts above, or the ones
without them? Confusingly the file named `VERIFIED_changed` holds the *unchanged* counts,
so the naming cannot be trusted to answer it.

**Context, not a question:** neither set can be reproduced from the `reviewed.dat` committed
here, which covers only -20.0 to -29.5 degC while these files run from -4.5. The committed
`.dat` is evidently a trimmed copy. That is fine for testing, but it means these curated
counts cannot be regenerated from anything in the repository.

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
