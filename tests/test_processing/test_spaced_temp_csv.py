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

import pytest

# from olaf.processing.spaced_temp_csv import SpacedTempCSV


class TestCreateTempCSV:
    """Happy-path and golden-file regression tests over real folders."""

    def test_air_sample_sgp_golden(
        self,
        sgp_test_folder,
        sample_dilution_dict_a,
        goldens_root,
        assert_csv_matches_golden,
    ) -> None:
        """
        Given: tests/test_data/SGP 2.21.24 base/ (reviewed .dat, air sample, 6 dilutions)
        When:  SpacedTempCSV.create_temp_csv with sample_type="air", empty fpd dict.
        Then:  Result equals goldens/test_spaced_temp_csv/air_sgp.csv.

        Real data: tests/test_data/SGP 2.21.24 base/
        """
        # TODO: SpacedTempCSV(sgp_test_folder, num_samples=6, includes=("reviewed",))
        # TODO: actual = stc.create_temp_csv(sample_dilution_dict_a, {}, 32, "air", save=False)
        # TODO: assert_csv_matches_golden(actual,
        #          goldens_root / "test_spaced_temp_csv" / "air_sgp.csv")
        pytest.skip("not implemented")

    def test_air_sample_kcg_golden(
        self,
        kcg_test_folder,
        sample_dilution_dict_a,
        goldens_root,
        assert_csv_matches_golden,
    ) -> None:
        """
        Secondary golden over KCG 09.23.24 base/. Catches regressions specific to
        KCG header / column layout differences vs SGP.

        Real data: tests/test_data/KCG 09.23.24 base/
        """
        pytest.skip("not implemented")

    def test_temperature_binning_at_05c_intervals(self, sgp_test_folder) -> None:
        """
        Given: any reviewed dataset
        When:  create_temp_csv runs
        Then:  output 'degC' column values are all multiples of TEMP_STEP (0.5),
               descending, no duplicates.

        Source: olaf/CONSTANTS.py TEMP_STEP; spaced_temp_csv.py binning loop.
        """
        pytest.skip("not implemented")

    def test_side_b_descending_dilution_dict(self, sgp_test_folder, sample_dilution_dict_b) -> None:
        """
        Given: same reviewed .dat but with side-B (descending) dilution dict.
        When:  create_temp_csv runs.
        Then:  Output dilution-to-sample column mapping is reversed relative to
               side A; per-row frozen counts within each dilution match.

        Source: spaced_temp_csv.py column renaming logic.
        """
        pytest.skip("not implemented")


class TestSaltSampleFPD:
    """Salt / sea-water samples shift temperatures by freezing_point_depression_dict."""

    def test_salt_sample_with_fpd_dict(
        self,
        sgp_test_folder,
        sample_dilution_dict_a,
        freezing_point_depression_dict,
    ) -> None:
        """
        Given: reviewed .dat treated as a salt sample with fpd applied.
        When:  create_temp_csv(..., fpd_dict, ..., sample_type="salt")
        Then:  Sample_0 column starts ~2 deg C colder than air baseline; Sample_1
               column ~0.2 deg C colder; others unchanged.

        Source: spaced_temp_csv.py:88-100
        """
        pytest.skip("not implemented")

    def test_salt_sample_missing_fpd_key_pins_current_behavior(
        self,
        sgp_test_folder,
        sample_dilution_dict_a,
    ) -> None:
        """
        BUG #7 anchor.
        Given: salt sample but fpd_dict missing the least-diluted sample's key.
        When:  create_temp_csv runs.
        Then:  currently raises TypeError (round(10*None+4)). After fix it should
               default missing keys to 0 and run cleanly. This test pins CURRENT
               behavior so the fix produces an intentional diff.

        Source: spaced_temp_csv.py:88-90
        """
        # TODO: with pytest.raises(TypeError):  stc.create_temp_csv(..., fpd={}, ...,
        #       sample_type="salt")
        pytest.skip("not implemented - pins bug #7 current behavior")


class TestSavedFiles:
    """When save=True, create_temp_csv writes one binned CSV (and fpd artifacts if salt)."""

    def test_air_sample_writes_single_frozen_at_temp_csv(
        self, sgp_test_folder, sample_dilution_dict_a, tmp_path
    ) -> None:
        """Air samples: exactly one frozen_at_temp_*.csv written next to the .dat."""
        pytest.skip("not implemented")

    def test_salt_sample_writes_extra_fpd_artifacts(
        self,
        sgp_test_folder,
        sample_dilution_dict_a,
        freezing_point_depression_dict,
        tmp_path,
    ) -> None:
        """Salt samples: additional fpd artifacts emitted (verify exact filenames)."""
        pytest.skip("not implemented")
