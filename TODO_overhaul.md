# OLAF Overhaul TODO

Tracking document for the **community-package overhaul** initiative. This is the roadmap that came
out of the full-codebase critical review. It sits alongside `TODO.md` (which tracks the
test-scaffolding + bug index); cross-references to that bug index are noted as `bug #N`.

Update checkboxes as items land. Follow the `CLAUDE.md` agent rules (no file deletions; goldens and
breaking API changes are human-only).

## Steering decisions (locked)

- **Vision = community package.** Other labs install and run OLAF; third parties produce ARM
  submissions. Packaging, strict validation, extensibility, testability of the non-GUI stages, and
  documented methodology are first-class requirements.
- **Overhaul pulled forward.** The `GraphDataCSV` / blank-correction rewrite (previously `TODO.md`
  Phase 3/4) is a near-term priority, not deferred behind more scaffolding.
- **Researcher review is a hard constraint.** Stage 1's manual image validation always happens — the
  GUI always opens on a processing run and is never made optional or headless-by-default. Decoupling
  work is for testability, not to remove the human.
- **Stages 2–3 stay one-config-per-run.** No batch/multi-experiment mode.

> Because the audience is now external labs producing real ARM data, correctness bugs currently
> *pinned* by characterization tests can no longer stay parked — when the overhaul lands, those
> goldens must be **re-curated to correct values** (human-only), not left pinning wrong output.

---

## Milestone A — Numerical-core overhaul  ⟵ highest priority
Make the two calculation engines pure, testable, and correct; fold in the parked bugs.

### A.1 `graph_data_csv.py` (`GraphDataCSV.convert_INPs_L`)
- [x] Extract the dilution-blending logic out of the nested closure `error_logic_selecting_values`
      into a documented, unit-tested module-level function with explicit inputs/outputs and stated
      invariants (monotonicity preserved, CI-bounded selection). Now `_select_blended_value`, with
      unit tests for all four decision branches. Behaviour-preserving (output byte-identical).
- [x] Fix `bug #1`: `prev_val == np.nan` always False → use `pd.isna(prev_val)`. **Output-affecting**
      when the accumulated result has an interior NaN gap; there is no numerical golden yet, so a
      human should curate one to lock the corrected spectrum (see A.3 / Human-Needs-To-Do).
- [x] Fix `bug #2`: `UnboundLocalError` when `last_4_i` is empty — initialise `i = -1` so the next
      dilution fills the whole column. Only affects previously-crashing inputs.
- [x] Fix `bug #8`: lost exception chaining → `raise ValueError(...) from e`. No numerical change.
      Tests: `tests/test_processing/test_graph_data_csv.py` — all three fail without their fix.
      The bug #1 test drives the down-swing-over-NaN-gap fallback and asserts the *dilution
      selection* flip (logic, not magnitude); corrected numerical magnitudes still need a
      human-curated golden.
- [x] Guard `log`/division explicitly with NaN masking instead of relying on the downstream
      `replace({inf: nan})`. Now `_inp_per_ml` computes the log only where
      `(N_total - col) > 0 and N_total > 0` and the dilution is finite; the `replace` is removed.
      Behaviour-preserving (output byte-identical) and removes the numpy `RuntimeWarning`s.

### A.2 `blank_correction.py`
- [ ] Fix `bug #3`: `df_corrected["qc_flag"] = int` (assigns the type) → `= 0` with integer dtype
      (line ~393); currently writes `<class 'int'>` into ARM files for uncorrected rows.
- [ ] Fix `bug #4`: rewrite the pathological chained comparison (lines ~402–409) as explicit `and`s.
- [ ] Fix `bug #5`: the ERROR_SIGNAL walk-back at line ~411 is dead code (unreachable given the
      current condition) and decrements a float temp label — make it reachable and index-based.
- [ ] Fix the all-wells-frozen division-by-zero in the error/CI calculation (`_error_calc`).

### A.3 Structure & fixtures
- [ ] Separate calculation from I/O and plotting: engines return DataFrames; a thin caller does file
      writes and `plot_INPS_L`. Reuse `math_utils.rms`, `df_utils.read_with_flexible_header`.
- [ ] **(Human)** Re-curate golden fixtures that currently pin buggy output (e.g. `qc_flag`,
      `capek_combined_blank.csv` tuple cells — `bug #17`) to correct values via
      `OLAF_REGEN_GOLDEN=1` + review. Agent writes tests; human confirms the numbers.

---

## Milestone B — Decouple review UI from pipeline plumbing (testability, NOT bypass)
**Researcher review stays mandatory; the GUI always opens.**
- [ ] Split `olaf/image_verification/` so the data/image loading + validation logic is a stateless,
      GUI-free unit, with the Tkinter widget as a thin shell — replace the
      `FreezingReviewer → ButtonHandler → DataLoader → DataHandler` inheritance-as-code-sharing with
      composition. Makes the loader/validator unit-testable without `$DISPLAY`.
- [ ] Preserve & **document** the reuse behavior: a run always opens the review GUI; the supported
      way to reuse a prior review is to close the GUI without changes, whereupon processing proceeds
      with the existing `reviewed_*.dat`. Document in README + docstrings; ensure
      closing-without-changes deterministically reuses prior reviewed data.
- [ ] Treat the saved review (`reviewed_*.dat` / `changes` column) as first-class provenance of the
      human decisions, written alongside `save_provenance_copy` output.

---

## Milestone C — Type the domain & tighten config
- [ ] Replace scattered string checks with `Enum`/`Literal` + a small strategy/registry for
      sample-type behavior. Touch points: `spaced_temp_csv.py` (`sample_type == "salt" or ...`),
      `config/models.py`, `plot_utils.py`, `final_file_creation.py`, and `if "TBS" in site`.
- [ ] Fix `bug #11`: `"blank" in treatment` doesn't match `"blank heat"` (`main.py:95`).
- [ ] `config/models.py`: constrain `sample_type` / `treatment` with `Literal`; promote soft
      `warnings.warn` data-quality checks (well-count, treatment-vs-folder) to hard errors or a
      `strict=true` flag.
- [ ] Move `to_header()` / `build_header_start()` formatting out of the pydantic models into a
      `HeaderFormatter` (models validate; formatter formats).
- [ ] Fix `bug #12`: fragile `DEFAULT_CONFIG = Path.cwd().parent/...` and `D:OLAF/...` → make
      location-independent (`Path(__file__)`-anchored or `OLAF_CONFIG_DIR`).

---

## Milestone D — Packaging & distribution (required for community package)
- [ ] Add `[project.scripts]` console entries (e.g. `olaf-process`, `olaf-blanks`, `olaf-combine`)
      so users run a command, not `python -m olaf.main` from repo root.
- [ ] **(Human decision)** Choose initial version (`0.2.0` vs `1.0.0`); currently stuck at `0.1.0`.
- [ ] Add a PyPI trusted-publishing `release.yml` on tag push (promote the optional `TODO.md` item).
- [ ] Add a CI smoke job that `pip install`s the built wheel in a clean venv and runs a console entry.
- [ ] Remove the dead `requirements.in` duplication *(human deletion per no-delete rule)*; document
      the numpy pin reason.

---

## Milestone E — Observability & scaling substrate
- [ ] `print → logging` migration across `processing/` (21+ call sites) with a configured logger, so
      long jobs are visible and errors carry context for non-programmers.
- [ ] Parse filenames into a structured dataclass (site/date/treatment/stage/version) instead of
      substring matching, hardening the conventions-as-database layer:
  - [ ] `DATE_PATTERN` MM.DD.YY ambiguity (`CONSTANTS.py`).
  - [ ] `bug #14`: `find_latest_file` `(N)` version regex (`path_utils.py`).
  - [ ] `DataHandler` substring `includes/excludes` false positives (`blank_corrected_base.csv`
        matches both `blank` and `base`).
- [ ] **(Human-approved, breaking)** Fix `bug #9`: `DataHandler` returns `(None, exc)` instead of
      raising — reserved for human approval per `TODO.md`.

---

## Milestone F — CI, docs & release gates
- [ ] Create a real `tests/test_integration/` that drives the **post-review** pipeline
      (`SpacedTempCSV` → `GraphDataCSV` → blank correction → final combine) on a committed
      `reviewed_*.dat` fixture with no GUI/`$DISPLAY` (enabled by Milestone B). Currently the dir is
      **missing** even though `release-gate.yml` runs `pytest tests/test_integration` — the gate is
      vacuous today. Keep GUI smoke tests under the `gui` marker.
- [ ] Enforce a coverage threshold (`--cov-fail-under=…`) and set `fail_ci_if_error` appropriately in
      `.github/workflows/ci.yml` (currently coverage is uploaded but not gated).
- [ ] Build docs in PR CI (not only `release-gate.yml`) with `-W`.
- [ ] Add `docs/methodology.rst` — INP formula, Agresti-Coull CIs, blank RMS error propagation,
      citations — so external users can audit the science.
- [ ] Start `CHANGELOG.md`.

---

## Sequencing notes
- **A and B are the unlock.** Correct engines + a review-decoupled (not review-removed) pipeline are
  what make a credible community release and a non-vacuous integration gate possible.
- Each milestone is its own PR series, not a single change.
- Golden re-curation and breaking API changes (`bug #9`, `DataHandler` contract) are human-run.
- Use the `science-reviewer` agent on every diff touching `olaf/processing/`, `math_utils.py`,
  `CONSTANTS.py`, `config/models.py`, or goldens.

## Human-Needs-To-Do (from this roadmap)
- [ ] Re-curate the goldens that pin buggy output once Milestone A lands (A.3).
- [ ] Curate a numerical golden for `GraphDataCSV.convert_INPs_L` output to lock the behaviour
      after the bug #1 fix (there was no output golden before). Write real values via
      `OLAF_REGEN_GOLDEN=1` on a `test_graph_data_csv` golden-assert test and confirm the numbers
      by hand — the current tests only assert the crash/chaining fixes and a NaN-gap smoke path.
- [ ] Decide the initial release version (D).
- [ ] Delete `requirements.in` if agreed (D) — agent cannot delete files.
- [ ] Approve the breaking `DataHandler` contract change (E, `bug #9`).
