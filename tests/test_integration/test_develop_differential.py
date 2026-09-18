"""Differential tests: current engines vs. the ``develop`` snapshot, over generated data.

Fixture-based parity (see ``test_develop_parity.py``) only proves parity on the fixtures.
The campaign archive is far larger than ``tests/test_data/``, so a spectrum shape that does
not appear locally could still appear there. These tests search the input space directly by
running both implementations over thousands of generated spectra, needing no real data at
all.

The reference implementations are verbatim snapshots of ``develop`` at ``70f3845``, vendored
under ``tests/reference/`` (see the README there).

Register of intentional behavior changes on ``numerical-core``
--------------------------------------------------------------
Four are **not observable** through the pipeline and so must never produce a difference here:

===========================================  ==========================================
Change                                       Why it cannot surface
===========================================  ==========================================
``qc_flag`` object -> int64                  0/1 render identically; dtype not compared
``_error_calc`` all-frozen -> NaN            Step 4 already prunes ``samples >= 30``,
                                             a strict superset of ``== wells_per_sample``
``_error_calc`` DataFrame + scalar dilution  Unreachable; production passes an Index
``save=False`` skips extrapolated CSV        Side-effect file only, not a returned value
===========================================  ==========================================

Four **are** observable. All of them are corrections that the old code failed to make:

===========================================  ==========================================
Trigger                                      Effect on output
===========================================  ==========================================
Usable row preceded by ``ERROR_SIGNAL``,     value raised to the last usable value,
below the last usable value                  ``qc_flag`` 0 -> 1 (scientist-confirmed)
Zero row between baseline and a lower value  same, walk now steps over the zero
``INPs_L`` filename with 2+ ``(``            file skipped instead of NameError / writing
                                             to the previous folder's path
Extrapolation fully covers missing temps     run completes instead of ValueError
===========================================  ==========================================

The first two are what ``_final_check`` can exhibit, and both have the *same* signature:
**the new value is never lower than the old one, and every differing row carries
``qc_flag == 1``.** That is the invariant asserted below. Anything else is an unclassified
difference and fails — which is the entire point of this module.

Set ``OLAF_DIFF_CASES`` to raise the iteration count for a deeper local search
(e.g. ``OLAF_DIFF_CASES=20000``); the committed default keeps CI fast.
"""

from __future__ import annotations

import importlib.util
import os
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from olaf.CONSTANTS import ERROR_SIGNAL
from olaf.processing.blank_correction import BlankCorrector
from olaf.processing.graph_data_csv import GraphDataCSV

_REFERENCE_DIR = Path(__file__).resolve().parents[1] / "reference"
_CASES = int(os.environ.get("OLAF_DIFF_CASES", "400"))


def _load_reference(module_name: str, filename: str):
    """Import a vendored develop snapshot under its own module name."""
    path = _REFERENCE_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        pytest.skip(f"cannot load reference module {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_dev_bc = _load_reference("_olaf_dev_blank_correction", "develop_blank_correction.py")
_dev_gdc = _load_reference("_olaf_dev_graph_data_csv", "develop_graph_data_csv.py")
DevBlankCorrector = _dev_bc.BlankCorrector
DevGraphDataCSV = _dev_gdc.GraphDataCSV


# --------------------------------------------------------------------------- helpers
def _call_final_check(cls, df_corrected, df_inps):
    """Run ``_final_check`` without invoking ``__init__`` (which does file discovery).

    Returns ``(result_or_None, exception_or_None)``.
    """
    instance = cls.__new__(cls)
    try:
        return cls._final_check(instance, df_corrected.copy(), df_inps.copy()), None
    except Exception as exc:  # we are classifying failures here, not handling them
        return None, exc


def _random_spectrum(rng: random.Random, n: int) -> list[float]:
    """A plausible INP/L column: mostly rising, sprinkled with the awkward values."""
    values: list[float] = []
    current = 10 ** rng.uniform(-4, 0)
    for _ in range(n):
        roll = rng.random()
        if roll < 0.12:
            values.append(float(ERROR_SIGNAL))
            continue
        if roll < 0.18:
            values.append(rng.choice([0.0, -0.0]))
            continue
        if roll < 0.28:
            # a downward step - the physically impossible case the correction exists for
            current = max(current * rng.uniform(0.1, 0.9), 1e-9)
        else:
            current = current * rng.uniform(1.0, 3.0)
        values.append(current)
    return values


def _make_case(rng: random.Random) -> tuple[pd.DataFrame, pd.DataFrame]:
    n = rng.randint(1, 40)
    inps = [10 ** rng.uniform(-4, 2) for _ in range(n)]
    if rng.random() < 0.2:  # original spectra containing zeros exercise the row filter
        for i in rng.sample(range(n), k=max(1, n // 8)):
            inps[i] = 0.0
    corrected = _random_spectrum(rng, n)
    lower = [abs(v) * rng.uniform(0.1, 0.9) for v in inps]
    upper = [abs(v) * rng.uniform(1.1, 2.0) for v in inps]
    degc = [-10.0 - 0.5 * i for i in range(n)]
    df_inps = pd.DataFrame({"degC": degc, "INPS_L": inps, "lower_CI": lower, "upper_CI": upper})
    df_corrected = pd.DataFrame(
        {"degC": degc, "INPS_L": corrected, "lower_CI": lower, "upper_CI": upper}
    )
    return df_corrected, df_inps


def _classify(old: pd.DataFrame, new: pd.DataFrame) -> list[str]:
    """Return a list of unclassified differences; empty means the delta is expected."""
    problems: list[str] = []
    if list(old.columns) != list(new.columns):
        problems.append(f"column mismatch: {list(old.columns)} vs {list(new.columns)}")
        return problems
    if len(old) != len(new):
        problems.append(f"row count differs: {len(old)} vs {len(new)}")
        return problems
    if not np.allclose(old["degC"], new["degC"], rtol=0, atol=0, equal_nan=True):
        problems.append("degC grid differs")
        return problems

    old_v = old["INPS_L"].to_numpy(dtype=float)
    new_v = new["INPS_L"].to_numpy(dtype=float)
    new_qc = new["qc_flag"].to_numpy(dtype=float)

    differs = ~(np.isclose(old_v, new_v, rtol=1e-12, atol=0, equal_nan=True))
    for i in np.flatnonzero(differs):
        # Every intentional change is a correction the old code failed to make. Such a
        # correction (a) only ever raises the value, (b) always flags the row, and (c)
        # copies a value from an earlier row rather than inventing a new number. All three
        # are checked, so an over- or under-correction cannot masquerade as expected.
        if new_v[i] < old_v[i]:
            problems.append(
                f"row {i} (degC {old['degC'].iloc[i]}): new value {new_v[i]!r} is LOWER "
                f"than old {old_v[i]!r} - corrections may only raise values"
            )
        elif new_qc[i] != 1:
            problems.append(
                f"row {i} (degC {old['degC'].iloc[i]}): value changed "
                f"{old_v[i]!r} -> {new_v[i]!r} but qc_flag is {new_qc[i]!r}, not 1"
            )
        elif not np.any(new_v[:i] == new_v[i]):
            problems.append(
                f"row {i} (degC {old['degC'].iloc[i]}): corrected to {new_v[i]!r}, which "
                f"matches no earlier row - a correction must copy the last usable value"
            )
    return problems


# --------------------------------------------------------------------------- tests
class TestFinalCheckDifferential:
    """``BlankCorrector._final_check`` - where most of the branch's change lives."""

    def test_generated_spectra_agree_or_differ_only_as_documented(self) -> None:
        rng = random.Random(20260917)
        identical = corrected_more = fixed_crash = 0
        failures: list[str] = []

        for case in range(_CASES):
            df_corrected, df_inps = _make_case(rng)
            old, old_exc = _call_final_check(DevBlankCorrector, df_corrected, df_inps)
            new, new_exc = _call_final_check(BlankCorrector, df_corrected, df_inps)

            if new_exc is not None and old_exc is None:
                failures.append(
                    f"case {case}: current code raised {type(new_exc).__name__}: {new_exc} "
                    f"where develop succeeded"
                )
                continue
            if new_exc is not None and old_exc is not None:
                continue  # both reject the input the same way
            if old_exc is not None:
                fixed_crash += 1  # develop crashed, current completes - a repaired failure
                continue

            assert old is not None and new is not None
            problems = _classify(old, new)
            if problems:
                failures.append(f"case {case}: " + "; ".join(problems))
            elif old["INPS_L"].equals(new["INPS_L"]):
                identical += 1
            else:
                corrected_more += 1

        assert not failures, (
            f"{len(failures)} unclassified difference(s) between develop and this branch:\n"
            + "\n".join(failures[:10])
        )
        # Guard against a vacuous pass: the generator must actually reach the engine.
        assert identical > 0, "no case produced identical output - generator is not exercising it"
        print(
            f"\n_final_check: {identical} identical, {corrected_more} corrected-more, "
            f"{fixed_crash} develop-crash-now-fixed, out of {_CASES} cases"
        )

    def test_current_code_never_crashes_where_develop_succeeded(self) -> None:
        """Split out so a crash regression is reported on its own, not buried in diffs."""
        rng = random.Random(777)
        regressions = []
        for case in range(_CASES):
            df_corrected, df_inps = _make_case(rng)
            _, old_exc = _call_final_check(DevBlankCorrector, df_corrected, df_inps)
            _, new_exc = _call_final_check(BlankCorrector, df_corrected, df_inps)
            if old_exc is None and new_exc is not None:
                regressions.append(f"case {case}: {type(new_exc).__name__}: {new_exc}")
        assert not regressions, "current code raises where develop did not:\n" + "\n".join(
            regressions[:10]
        )


class TestComputeINPsLDifferential:
    """``GraphDataCSV`` - the ``_error_calc`` change must be invisible in pipeline output."""

    @staticmethod
    def _write_frozen(folder: Path, rng: random.Random, wells: int = 32) -> None:
        n = rng.randint(4, 40)
        degc = [-4.0 - 0.5 * i for i in range(n)]
        cols: dict[str, list[int]] = {"degC": degc}  # type: ignore[dict-item]
        # Frozen-well counts rise as temperature falls, and rise with lower dilution.
        ceilings = [wells, wells, wells, wells // 2, wells // 4, wells // 8]
        for idx, ceiling in enumerate(ceilings):
            counts, current = [], 0
            for _ in range(n):
                if rng.random() < 0.5:
                    current = min(current + rng.randint(0, 3), ceiling)
                counts.append(current)
            cols[f"Sample_{idx}"] = counts
        pd.DataFrame(cols).to_csv(folder / "frozen_at_temp_reviewed_base.csv", index=False)

    def test_generated_frozen_counts_produce_identical_spectra(self, tmp_path: Path) -> None:
        rng = random.Random(4242)
        dilution = {
            "Sample_0": 1,
            "Sample_1": 11,
            "Sample_2": 121,
            "Sample_3": 1331,
            "Sample_4": 14641,
            "Sample_5": float("inf"),
        }
        kwargs = dict(
            num_samples=6,
            sample_type="air",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=dilution,
        )
        compared = 0
        cases = max(1, _CASES // 8)  # each case is far heavier than a _final_check case
        for case in range(cases):
            folder = tmp_path / f"case_{case}"
            folder.mkdir()
            self._write_frozen(folder, rng)
            try:
                old = DevGraphDataCSV(folder, **kwargs).convert_INPs_L(
                    "site = TEST\n", save=False, show_plot=False
                )
            except Exception:  # develop failing is not this branch's problem
                continue
            new = GraphDataCSV(folder, **kwargs).compute_INPs_L()
            pd.testing.assert_frame_equal(
                old.reset_index(drop=True),
                new.reset_index(drop=True),
                rtol=1e-12,
                check_dtype=False,
                obj=f"case {case}",
            )
            compared += 1
        assert compared > 0, "no case reached the comparison - generator produced nothing usable"
        print(f"\ncompute_INPs_L: {compared}/{cases} generated spectra identical to develop")
