"""End-to-end goldens pinning the two engines rewritten on ``numerical-core``.

These goldens are generated from **develop's** code (see
``scripts/regen_develop_baseline.sh``) and must then pass unchanged against this branch.
Green here is the proof that the refactor moved nothing it was not meant to move.

Scope and limits
----------------
This module covers the inputs committed to the repository. It cannot speak for data nobody
has looked at - that is the job of ``test_develop_differential.py``, which runs both
implementations over generated spectra, and of ``scripts/scan_trigger_conditions.py``, which
reports whether any spectrum in a given archive would produce different output.

The register of intentional behavior changes lives in ``test_develop_differential.py``'s
module docstring. None of those changes is triggered by the inputs used here, which is
asserted directly by :class:`TestParityInputsAreTriggerFree` - so every golden below is
valid under *both* versions, and no fixture ever pins pre-fix behavior.

Regenerating
------------
Only when behavior is intentionally changed, and never by copying archived products::

    bash scripts/regen_develop_baseline.sh   # against develop's engines
    uv run pytest tests/test_integration -q  # must then pass unchanged
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest

from olaf.CONSTANTS import ERROR_SIGNAL
from olaf.processing.blank_correction import BlankCorrector
from olaf.processing.graph_data_csv import GraphDataCSV
from olaf.utils.df_utils import read_with_flexible_header

# ``sgp_2_21_24_base`` is deliberately absent: its committed frozen_at_temp_expected.csv has
# a literal Unicode ellipsis as the temperature column name instead of ``degC``, so no engine
# can read it. Tracked in TODO.md; restore it here once the fixture is repaired.
_STAGE1_FIXTURES = ["kcg_09_23_24_base", "sgp_3_28_24_base"]

_DILUTION = {
    "Sample_0": 1,
    "Sample_1": 11,
    "Sample_2": 121,
    "Sample_3": 1331,
    "Sample_4": 14641,
    "Sample_5": float("inf"),
}
_GRAPH_KWARGS = dict(
    num_samples=6,
    sample_type="air",
    vol_air_filt=620.48,
    wells_per_sample=32,
    filter_used=1.0,
    vol_susp=10.0,
    dict_samples_to_dilution=_DILUTION,
)
_CAPEK_INCLUDES = ("INPs_L",)
_CAPEK_EXCLUDES = ("blank_corrected",)
_CORRECTED_COLUMNS = ("degC", "dilution", "INPS_L", "lower_CI", "upper_CI", "qc_flag")


def _treatment_of(path: Path) -> str:
    """Stable label for a produced file: its parent folder, which names the treatment.

    The filename itself carries a collision counter such as ``(1)`` that depends on what
    already sits in the fixture, so it is not stable enough to key a golden on.
    """
    return path.parent.name


def _stage1_folder(goldens_root: Path, fixture: str, tmp_path: Path) -> Path:
    """Copy a committed frozen_at_temp fixture under a name GraphDataCSV will select."""
    src = goldens_root / "inputs" / fixture / "frozen_at_temp_expected.csv"
    if not src.exists():
        pytest.skip(f"missing committed fixture: {src}")
    work = tmp_path / fixture
    work.mkdir(parents=True)
    shutil.copy(src, work / "frozen_at_temp_reviewed_base.csv")
    return work


class TestStage1Parity:
    """``GraphDataCSV`` - previously pinned by no golden at all."""

    @pytest.mark.parametrize("fixture", _STAGE1_FIXTURES)
    def test_inps_l_spectrum_matches_develop(
        self, fixture, goldens_root, assert_csv_matches_golden, tmp_path
    ) -> None:
        work = _stage1_folder(goldens_root, fixture, tmp_path)
        result = GraphDataCSV(work, **_GRAPH_KWARGS).convert_INPs_L(
            "site = TEST\n", save=False, show_plot=False
        )
        assert_csv_matches_golden(
            result,
            goldens_root / "expected" / "test_develop_parity" / f"inps_L_{fixture}.csv",
        )


class TestStage2Parity:
    """``BlankCorrector`` over the committed capek mini-project (blanks + 3 treatments)."""

    def test_combined_blank_matches_develop(
        self, capek_golden_folder, goldens_root, assert_csv_matches_golden
    ) -> None:
        if not any(capek_golden_folder.rglob("INPs_L*.csv")):
            pytest.skip("capek golden inputs not curated")
        bc = BlankCorrector(
            project_folder=capek_golden_folder,
            blank_includes=_CAPEK_INCLUDES,
            blank_excludes=_CAPEK_EXCLUDES,
            sample_excludes=(),
        )
        result = bc.average_blanks(save=False).reset_index()
        # average_blanks emits tuples such as (1,) in the dilution column (bug #17); the CSV
        # round-trip stores them as strings, so normalise both sides until that is fixed.
        result["dilution"] = result["dilution"].astype(str)
        assert_csv_matches_golden(
            result,
            goldens_root / "expected" / "test_develop_parity" / "capek_combined_blank.csv",
        )

    def test_every_blank_corrected_file_matches_develop(
        self, capek_golden_folder, goldens_root, assert_csv_matches_golden, tmp_path
    ) -> None:
        """All treatments, not just the first - the existing suite only checked one."""
        if not any(capek_golden_folder.rglob("INPs_L*.csv")):
            pytest.skip("capek golden inputs not curated")
        work = tmp_path / "capek"
        shutil.copytree(capek_golden_folder, work)
        # The fixture ships a legacy blank_corrected file of its own, so compare the set
        # before and after rather than globbing - otherwise the committed one is mistaken
        # for output and fails to parse.
        pre_existing = set(work.rglob("blank_corrected_*.csv"))
        bc = BlankCorrector(
            project_folder=work,
            blank_includes=_CAPEK_INCLUDES,
            blank_excludes=_CAPEK_EXCLUDES,
            sample_excludes=(),
        )
        bc.average_blanks(save=False)
        bc.apply_blanks(save=True, only_within_dates=False)

        produced = sorted(set(work.rglob("blank_corrected_*.csv")) - pre_existing)
        if not produced:
            pytest.skip("no blank-corrected output produced from the capek fixture")

        # One golden covering every treatment. Comparing file-by-file would silently cover
        # only the first: assert_csv_matches_golden calls pytest.skip() in regen mode, which
        # aborts the loop, so the later treatments would never get a baseline written.
        frames = []
        for path in produced:
            _, actual = read_with_flexible_header(path, expected_columns=_CORRECTED_COLUMNS)
            actual = actual.copy()
            actual.insert(0, "source_file", _treatment_of(path))
            frames.append(actual)
        combined = pd.concat(frames, ignore_index=True).sort_values(
            ["source_file", "degC"], ignore_index=True
        )
        assert combined["source_file"].nunique() == len(produced), "treatment labels collided"
        assert_csv_matches_golden(
            combined,
            goldens_root / "expected" / "test_develop_parity" / "capek_blank_corrected_all.csv",
        )


class TestParityInputsAreTriggerFree:
    """Guard: no parity input may contain a condition where the two versions disagree.

    Without this, someone could later add a fixture containing an ``ERROR_SIGNAL`` gap,
    regenerate the baselines from develop, and silently pin pre-fix behavior as correct.
    """

    @staticmethod
    def _crossable(value: float) -> bool:
        """Values the new walk-back steps over: exactly ERROR_SIGNAL and zero.

        NaN is deliberately NOT crossable. The walk breaks on anything that is neither
        ERROR_SIGNAL nor zero, so it stops at a NaN, and ``current < NaN`` is False - both
        versions therefore leave a NaN gap alone and agree. Treating NaN as crossable here
        produced false positives on two committed fixtures.
        """
        return value == ERROR_SIGNAL or value == 0

    @classmethod
    def _bridges(cls, values: list[float]) -> list[int]:
        """Rows the branch corrects but develop does not.

        Develop compared against the *immediate* predecessor and bailed out if it was
        ERROR_SIGNAL or zero, so the two versions can only diverge where the immediate
        predecessor is crossable and some earlier non-crossable value exceeds the current
        one. Kept in sync with ``scripts/scan_trigger_conditions.py``.
        """
        hits = []
        for i, current in enumerate(values):
            if i == 0 or cls._crossable(current):
                continue
            if not cls._crossable(values[i - 1]):
                continue  # develop saw a usable predecessor too, so both behave the same
            j = i - 1
            while j >= 0 and cls._crossable(values[j]):
                j -= 1
            if j >= 0 and current < values[j]:
                hits.append(i)
        return hits

    def _spectra(self, goldens_root: Path):
        for path in sorted((goldens_root / "inputs").rglob("*.csv")):
            try:
                _, df = read_with_flexible_header(path)
            except Exception:  # malformed legacy fixtures are not this guard's concern
                continue
            if "INPS_L" in df.columns:
                yield path, df["INPS_L"].astype(float).tolist()

    def test_no_committed_input_contains_a_bridge_trigger(self, goldens_root) -> None:
        offenders = [
            f"{path}: rows {rows}"
            for path, values in self._spectra(goldens_root)
            if (rows := self._bridges(values))
        ]
        assert not offenders, (
            "Parity inputs contain gap/zero-bridge triggers, so a develop-generated golden "
            "would pin pre-fix behavior. Cover these with unit tests instead:\n"
            + "\n".join(offenders)
        )

    def test_no_committed_input_has_a_multi_paren_name(self, goldens_root) -> None:
        offenders = [
            str(p)
            for p in (goldens_root / "inputs").rglob("INPs_L*.csv")
            if p.stem.endswith(")") and p.stem.count("(") >= 2
        ]
        assert not offenders, "multi-parenthesis filenames differ between versions:\n" + "\n".join(
            offenders
        )

    def test_guard_detects_a_planted_trigger(self) -> None:
        """Negative control - a guard that cannot fail protects nothing."""
        assert self._bridges([10.0, 50.0, float(ERROR_SIGNAL), 30.0, 160.0]) == [3]
        assert self._bridges([10.0, 0.0, 5.0]) == [2]
        # No gap: develop compares against the same predecessor, so both versions agree.
        assert self._bridges([10.0, 50.0, 60.0]) == []
        assert self._bridges([10.0, 50.0, 30.0]) == []
        # A NaN gap stops the walk in both versions - must not be reported.
        assert self._bridges([10.0, 50.0, float("nan"), 30.0]) == []
        # Gap present but no drop below the last usable value.
        assert self._bridges([10.0, float(ERROR_SIGNAL), 60.0]) == []


def test_pandas_frame_equality_is_actually_strict() -> None:
    """Sanity check on the comparison itself, so a silent no-op cannot look like success."""
    left = pd.DataFrame({"a": [1.0, 2.0]})
    right = pd.DataFrame({"a": [1.0, 2.0 + 1e-6]})
    with pytest.raises(AssertionError):
        pd.testing.assert_frame_equal(left, right, rtol=1e-9)


class TestDirectParityAgainstDevelop:
    """Run develop's engines and the current ones over the *same committed inputs*.

    Stronger than the golden tests above and independent of them: it needs no baseline file
    and cannot go stale, because develop's implementation is executed here and now. The
    golden tests exist for permanence; this exists for proof.
    """

    @pytest.fixture(scope="class")
    def dev(self):
        from tests.test_integration.test_develop_differential import (
            DevBlankCorrector,
            DevGraphDataCSV,
        )

        return DevBlankCorrector, DevGraphDataCSV

    @pytest.mark.parametrize("fixture", _STAGE1_FIXTURES)
    def test_stage1_identical(self, fixture, dev, goldens_root, tmp_path) -> None:
        _, dev_graph = dev
        work_new = _stage1_folder(goldens_root, fixture, tmp_path / "new")
        work_old = _stage1_folder(goldens_root, fixture, tmp_path / "old")
        new = GraphDataCSV(work_new, **_GRAPH_KWARGS).convert_INPs_L(
            "site = TEST\n", save=False, show_plot=False
        )
        old = dev_graph(work_old, **_GRAPH_KWARGS).convert_INPs_L(
            "site = TEST\n", save=False, show_plot=False
        )
        pd.testing.assert_frame_equal(
            old.reset_index(drop=True),
            new.reset_index(drop=True),
            rtol=1e-12,
            check_dtype=False,
            obj=fixture,
        )

    def test_stage2_identical(self, dev, capek_golden_folder, tmp_path) -> None:
        dev_blank, _ = dev
        if not any(capek_golden_folder.rglob("INPs_L*.csv")):
            pytest.skip("capek golden inputs not curated")

        produced = {}
        for label, cls in (("old", dev_blank), ("new", BlankCorrector)):
            work = tmp_path / label
            shutil.copytree(capek_golden_folder, work)
            pre_existing = set(work.rglob("blank_corrected_*.csv"))
            corrector = cls(
                project_folder=work,
                blank_includes=_CAPEK_INCLUDES,
                blank_excludes=_CAPEK_EXCLUDES,
                sample_excludes=(),
            )
            corrector.average_blanks(save=False)
            corrector.apply_blanks(save=True, only_within_dates=False)
            produced[label] = sorted(set(work.rglob("blank_corrected_*.csv")) - pre_existing)

        assert [p.name for p in produced["old"]] == [p.name for p in produced["new"]], (
            "the two versions emitted different blank-corrected filenames"
        )
        assert produced["new"], "no blank-corrected output produced from the capek fixture"

        columns = ("degC", "dilution", "INPS_L", "lower_CI", "upper_CI", "qc_flag")
        for old_path, new_path in zip(produced["old"], produced["new"], strict=True):
            _, old_df = read_with_flexible_header(old_path, expected_columns=columns)
            _, new_df = read_with_flexible_header(new_path, expected_columns=columns)
            # qc_flag moved from an object column to int64; the CSV bytes are unchanged and
            # check_dtype=False keeps that from masquerading as a numerical difference.
            pd.testing.assert_frame_equal(
                old_df.reset_index(drop=True),
                new_df.reset_index(drop=True),
                rtol=1e-12,
                check_dtype=False,
                obj=new_path.name,
            )
