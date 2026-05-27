"""
Tests for olaf.processing.spaced_temp_csv

Class under test:
    - SpacedTempCSV(folder_path, num_samples, includes=(...))
        .create_temp_csv(
            dict_samples_to_dilution,
            freezing_point_depression_dict,
            wells_per_sample,
            sample_type,
            save=True,
        ) -> pd.DataFrame

Reference: olaf/processing/spaced_temp_csv.py
Bugs from review covered here:
    #7  TypeError if fpd dict missing a key  (spaced_temp_csv.py:88-90)
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from olaf.CONSTANTS import TEMP_STEP
from olaf.processing.spaced_temp_csv import SpacedTempCSV

# ---------------------------------------------------------------------------
# Local helpers
# ---------------------------------------------------------------------------


def _copy_reviewed_dat(src_folder: Path, dst_folder: Path) -> Path:
    """Copy the canonical reviewed.dat into a writable tmp folder."""
    dst_folder.mkdir(parents=True, exist_ok=True)
    shutil.copy(src_folder / "reviewed.dat", dst_folder / "reviewed.dat")
    return dst_folder


# ---------------------------------------------------------------------------
# Happy-path / golden tests
# ---------------------------------------------------------------------------


class TestCreateTempCSV:
    """Happy-path and golden-file regression tests over real folders."""

    def test_air_sample_sgp_golden(
        self,
        sgp_golden_folder,
        sample_dilution_dict_a,
        goldens_root,
        assert_csv_matches_golden,
    ) -> None:
        """
        Given: goldens/inputs/sgp_2_21_24_base/reviewed.dat
        When:  SpacedTempCSV.create_temp_csv with sample_type="air", empty fpd dict.
        Then:  Result equals goldens/expected/test_spaced_temp_csv/air_sgp.csv.
        """
        stc = SpacedTempCSV(sgp_golden_folder, num_samples=6, includes=("reviewed",))
        actual = stc.create_temp_csv(
            sample_dilution_dict_a,
            freezing_point_depression_dict={},
            wells_per_sample=32,
            sample_type="air",
            save=False,
        )
        assert_csv_matches_golden(
            actual,
            goldens_root / "expected" / "test_spaced_temp_csv" / "air_sgp.csv",
        )

    def test_air_sample_kcg_golden(
        self,
        goldens_root,
        sample_dilution_dict_a,
        assert_csv_matches_golden,
    ) -> None:
        """
        Secondary golden over goldens/inputs/kcg_09_23_24_base/. Catches regressions
        specific to KCG header / column layout differences vs SGP.

        Skipped until a human curates reviewed.dat under
        goldens/inputs/kcg_09_23_24_base/.
        """
        kcg_input = goldens_root / "inputs" / "kcg_09_23_24_base"
        if not (kcg_input / "reviewed.dat").exists():
            pytest.skip("KCG golden input not curated yet (see goldens README)")
        stc = SpacedTempCSV(kcg_input, num_samples=6, includes=("reviewed",))
        actual = stc.create_temp_csv(
            sample_dilution_dict_a,
            freezing_point_depression_dict={},
            wells_per_sample=32,
            sample_type="air",
            save=False,
        )
        assert_csv_matches_golden(
            actual,
            goldens_root / "expected" / "test_spaced_temp_csv" / "air_kcg.csv",
        )

    def test_temperature_binning_at_05c_intervals(
        self, sgp_golden_folder, sample_dilution_dict_a
    ) -> None:
        """
        Given: any reviewed dataset
        When:  create_temp_csv runs
        Then:  degC column is strictly decreasing; all rows except at most one
               (the first-frozen anchor row, rounded to 1 dp) sit on the 0.5 grid.

        Source: olaf/CONSTANTS.py TEMP_STEP; spaced_temp_csv.py binning loop.
        """
        stc = SpacedTempCSV(sgp_golden_folder, num_samples=6, includes=("reviewed",))
        df = stc.create_temp_csv(
            sample_dilution_dict_a,
            freezing_point_depression_dict={},
            wells_per_sample=32,
            sample_type="air",
            save=False,
        )
        temps = df["degC"].tolist()
        assert all(b < a for a, b in zip(temps, temps[1:])), f"degC not descending: {temps}"
        off_grid = [t for t in temps if abs((t / TEMP_STEP) - round(t / TEMP_STEP)) > 1e-9]
        assert len(off_grid) <= 1, f"more than one off-grid temp: {off_grid}"

    def test_side_b_descending_dilution_dict(
        self, sgp_golden_folder, sample_dilution_dict_b
    ) -> None:
        """
        Given: same reviewed .dat but with side-B dilution dict (Sample_5 most
               concentrated).
        When:  create_temp_csv runs with sample_type="air".
        Then:  Sample_5 (new least-diluted) ends with at least as many frozen wells
               as Sample_0; Sample_5 starts freezing at warmer-or-equal temperature
               than Sample_0; output schema intact.
        """
        stc = SpacedTempCSV(sgp_golden_folder, num_samples=6, includes=("reviewed",))
        df = stc.create_temp_csv(
            sample_dilution_dict_b,
            freezing_point_depression_dict={},
            wells_per_sample=32,
            sample_type="air",
            save=False,
        )
        assert list(df.columns) == ["degC"] + [f"Sample_{i}" for i in range(6)]
        assert df["Sample_5"].max() >= df["Sample_0"].max()
        first_s5 = df.loc[df["Sample_5"].ne(0).idxmax(), "degC"]
        first_s0_mask = df["Sample_0"].ne(0)
        if first_s0_mask.any():
            first_s0 = df.loc[first_s0_mask.idxmax(), "degC"]
            assert first_s5 >= first_s0  # type: ignore[operator,call-overload]  # pandas scalar comparison


class TestSaltSampleFPD:
    """Salt / sea-water samples shift temperatures by freezing_point_depression_dict."""

    def test_salt_sample_with_fpd_dict(
        self,
        sgp_golden_folder,
        sample_dilution_dict_a,
        freezing_point_depression_dict,
        goldens_root,
        assert_csv_matches_golden,
    ) -> None:
        """
        Given: reviewed .dat treated as a salt sample with fpd applied
               (Sample_0 -> 2 degC, Sample_1 -> 0.2 degC).
        When:  create_temp_csv(..., fpd_dict, ..., sample_type="salt")
        Then:  Output matches goldens/expected/test_spaced_temp_csv/salt_sgp.csv.
               Salt has more rows than air; Sample_0 first-nonzero is warmer.

        Source: spaced_temp_csv.py:88-100, 135-138
        """
        stc_air = SpacedTempCSV(sgp_golden_folder, num_samples=6, includes=("reviewed",))
        air = stc_air.create_temp_csv(sample_dilution_dict_a, {}, 32, "air", save=False)

        stc_salt = SpacedTempCSV(sgp_golden_folder, num_samples=6, includes=("reviewed",))
        salt = stc_salt.create_temp_csv(
            sample_dilution_dict_a,
            freezing_point_depression_dict,
            wells_per_sample=32,
            sample_type="salt",
            save=False,
        )

        assert len(salt) > len(air)
        first_s0_air = air.loc[air["Sample_0"].ne(0).idxmax(), "degC"]
        first_s0_salt = salt.loc[salt["Sample_0"].ne(0).idxmax(), "degC"]
        assert first_s0_salt > first_s0_air, (  # type: ignore[operator,call-overload]  # pandas scalar comparison
            f"salt Sample_0 should be shifted warmer: air={first_s0_air} " f"salt={first_s0_salt}"
        )

        assert_csv_matches_golden(
            salt,
            goldens_root / "expected" / "test_spaced_temp_csv" / "salt_sgp.csv",
        )

    def test_salt_sample_missing_fpd_key_raises_value_error(
        self,
        sgp_golden_folder,
        sample_dilution_dict_a,
    ) -> None:
        """
        BUG #7 fix verification.
        Given: salt sample but fpd_dict missing the least-diluted sample's key.
        When:  create_temp_csv runs.
        Then:  raises ValueError with a clear message naming the missing sample.

        Previously this site raised an opaque TypeError via round(10*None+4).
        The fix in olaf/processing/spaced_temp_csv.py guards the .get() result
        and raises ValueError instead.

        Source: spaced_temp_csv.py:88-100
        """
        stc = SpacedTempCSV(sgp_golden_folder, num_samples=6, includes=("reviewed",))
        with pytest.raises(ValueError, match="freezing point depression"):
            stc.create_temp_csv(
                sample_dilution_dict_a,
                freezing_point_depression_dict={},  # missing Sample_0 key
                wells_per_sample=32,
                sample_type="salt",
                save=False,
            )


class TestSavedFiles:
    """When save=True, create_temp_csv writes the binned CSV (and fpd artifacts if salt)."""

    def test_air_sample_writes_frozen_at_temp_and_dilution_csv(
        self, sgp_golden_folder, sample_dilution_dict_a, tmp_path
    ) -> None:
        """
        Air samples: writes frozen_at_temp_*.csv and dilution_dict_*.csv next to
        the .dat, but NOT an fpd dict file.
        """
        work = _copy_reviewed_dat(sgp_golden_folder, tmp_path / "air_run")
        stc = SpacedTempCSV(work, num_samples=6, includes=("reviewed",))
        stc.create_temp_csv(
            sample_dilution_dict_a,
            freezing_point_depression_dict={},
            wells_per_sample=32,
            sample_type="air",
            save=True,
        )

        written = sorted(p.name for p in work.iterdir())
        assert any(
            n.startswith("frozen_at_temp_") and n.endswith(".csv") for n in written
        ), f"missing frozen_at_temp_*.csv in {written}"
        assert any(
            n.startswith("dilution_dict_") and n.endswith(".csv") for n in written
        ), f"missing dilution_dict_*.csv in {written}"
        assert not any(
            n.startswith("frz_pnt_dep_dict_") for n in written
        ), f"air sample should not emit fpd file, got {written}"

    def test_salt_sample_writes_extra_fpd_artifacts(
        self,
        sgp_golden_folder,
        sample_dilution_dict_a,
        freezing_point_depression_dict,
        tmp_path,
    ) -> None:
        """
        Salt samples: additional `frz_pnt_dep_dict_*.csv` artifact emitted alongside
        the frozen_at_temp and dilution_dict files.
        """
        work = _copy_reviewed_dat(sgp_golden_folder, tmp_path / "salt_run")
        stc = SpacedTempCSV(work, num_samples=6, includes=("reviewed",))
        stc.create_temp_csv(
            sample_dilution_dict_a,
            freezing_point_depression_dict,
            wells_per_sample=32,
            sample_type="salt",
            save=True,
        )

        written = sorted(p.name for p in work.iterdir())
        assert any(n.startswith("frozen_at_temp_") and n.endswith(".csv") for n in written)
        assert any(n.startswith("dilution_dict_") and n.endswith(".csv") for n in written)
        assert any(
            n.startswith("frz_pnt_dep_dict_") and n.endswith(".csv") for n in written
        ), f"salt sample missing fpd artifact in {written}"
