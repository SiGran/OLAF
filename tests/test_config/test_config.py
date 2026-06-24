"""Tests for the olaf.config package: loading, validation, and provenance."""

import math
import warnings
from pathlib import Path

import pytest

from olaf.config import (
    BlankConfig,
    FinalCombineConfig,
    MainConfig,
    load_config,
    resolve_config_path,
    save_provenance_copy,
)
from olaf.config.models import sanitize_for_filename

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = REPO_ROOT / "configs" / "templates"


# --------------------------------------------------------------------------- loader


def test_load_main_template():
    config = load_config(TEMPLATES / "main.example.toml", MainConfig)
    assert config.site == "RAM_CINC"
    assert config.treatment == ["base"]
    assert isinstance(config.test_folder, Path)


def test_load_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_config(TEMPLATES / "does_not_exist.toml", MainConfig)


def test_load_invalid_toml_raises(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text("this is = not valid = toml")
    with pytest.raises(ValueError, match="Could not parse TOML"):
        load_config(bad, MainConfig)


def test_load_validation_error_raises(tmp_path):
    cfg = tmp_path / "cfg.toml"
    cfg.write_text('site = "X"\n')  # missing required fields
    with pytest.raises(ValueError, match="Invalid configuration"):
        load_config(cfg, MainConfig)


def test_resolve_config_path_uses_default():
    assert resolve_config_path("a/default.toml", argv=[]) == Path("a/default.toml")


def test_resolve_config_path_cli_overrides_default():
    assert resolve_config_path("a/default.toml", argv=["cli.toml"]) == Path("cli.toml")


# --------------------------------------------------------------------------- provenance


def test_save_provenance_copy(tmp_path):
    cfg = tmp_path / "run.toml"
    cfg.write_text('site = "X"\n')
    out = tmp_path / "out"
    out.mkdir()
    copied = save_provenance_copy(cfg, out)
    assert copied == out / "used_config_run.toml"
    assert copied.read_text() == 'site = "X"\n'


def test_save_provenance_copy_no_overwrite(tmp_path):
    cfg = tmp_path / "run.toml"
    cfg.write_text("a = 1\n")
    out = tmp_path / "out"
    out.mkdir()
    first = save_provenance_copy(cfg, out)
    second = save_provenance_copy(cfg, out)
    assert first != second
    assert second.name == "used_config_run(1).toml"


def test_save_provenance_copy_missing_dir_returns_none(tmp_path):
    cfg = tmp_path / "run.toml"
    cfg.write_text("a = 1\n")
    assert save_provenance_copy(cfg, tmp_path / "nope") is None


def test_save_provenance_copy_with_name(tmp_path):
    cfg = tmp_path / "generic.toml"
    cfg.write_text("a = 1\n")
    out = tmp_path / "out"
    out.mkdir()
    copied = save_provenance_copy(cfg, out, name="SGP_2024-02-21_base")
    assert copied == out / "used_config_SGP_2024-02-21_base.toml"
    assert copied.read_text() == "a = 1\n"


def test_save_provenance_copy_with_name_no_overwrite(tmp_path):
    cfg = tmp_path / "generic.toml"
    cfg.write_text("a = 1\n")
    out = tmp_path / "out"
    out.mkdir()
    first = save_provenance_copy(cfg, out, name="SITE_2024-01-01_heat")
    second = save_provenance_copy(cfg, out, name="SITE_2024-01-01_heat")
    assert first != second
    assert second.name == "used_config_SITE_2024-01-01_heat(1).toml"


# --------------------------------------------------------------------------- sanitization


def test_sanitize_for_filename_replaces_unsafe_chars():
    assert sanitize_for_filename("NSA no.2 05/22/25 base") == "NSA_no.2_05_22_25_base"


def test_sanitize_for_filename_empty_falls_back():
    assert sanitize_for_filename("   ") == "config"


# --------------------------------------------------------------------------- MainConfig


def _main_data(**overrides):
    data = {
        "test_folder": "data/SITE 07.16.25 base",
        "site": "SITE",
        "start_time": "2025-07-16 16:20:00",
        "end_time": "2025-07-16 17:52:00",
        "filter_color": "white",
        "notes": "none",
        "user": "tester",
        "IS": "IS2",
        "num_samples": 6,
        "wells_per_sample": 32,
        "dict_samples_to_dilution": {"Sample_0": 1, "Sample_5": math.inf},
    }
    data.update(overrides)
    return data


def test_main_inf_dilution():
    config = MainConfig(**_main_data())
    assert math.isinf(config.dict_samples_to_dilution["Sample_5"])


def test_main_treatment_string_coerced_to_list():
    config = MainConfig(**_main_data(treatment="heat", test_folder="data/SITE heat"))
    assert config.treatment == ["heat"]


def test_main_proportion_out_of_range_rejected():
    with pytest.raises(ValueError):
        MainConfig(**_main_data(proportion_filter_used=1.5))


def test_main_effective_vol_air_filt_blank():
    config = MainConfig(**_main_data(treatment=["blank"], vol_air_filt=620.0))
    assert config.effective_vol_air_filt == 1


def test_main_effective_vol_air_filt_soil():
    config = MainConfig(**_main_data(sample_type="soil", vol_susp=10, dry_mass=2))
    assert config.effective_vol_air_filt == 5


def test_main_to_header_contains_site_and_treatment():
    header = MainConfig(**_main_data()).to_header()
    assert "site = SITE" in header
    assert "treatment = base" in header


def test_main_to_header_tbs_adds_altitudes():
    config = MainConfig(**_main_data(site="TBS_SITE", test_folder="data/TBS_SITE 07.16.25 base"))
    header = config.to_header()
    assert "lower_altitude" in header and "upper_altitude" in header


def test_main_warns_on_treatment_folder_mismatch():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        MainConfig(**_main_data(treatment=["heat"]))  # folder says "base"
    assert any("does not match" in str(w.message) for w in caught)


def test_main_warns_on_well_count_mismatch():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        MainConfig(**_main_data(wells_per_sample=30))
    assert any("not equal to 192" in str(w.message) for w in caught)


def test_main_check_dates_returns_matching_date():
    config = MainConfig(**_main_data())
    assert config.check_dates() == ["07.16.25"]


def test_main_check_dates_warns_on_mismatch():
    config = MainConfig(**_main_data(start_time="2025-01-01 00:00:00"))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        dates = config.check_dates()
    assert dates == []
    assert any("does not match" in str(w.message) for w in caught)


def test_main_rejects_unknown_field():
    with pytest.raises(ValueError):
        MainConfig(**_main_data(unknown_field=1))


def test_main_provenance_stem():
    config = MainConfig(**_main_data())
    assert config.provenance_stem() == "SITE_2025-07-16_base"


def test_main_provenance_stem_sanitized():
    config = MainConfig(**_main_data(site="My Site/2", treatment=["heat"]))
    stem = config.provenance_stem()
    assert "/" not in stem and " " not in stem
    assert stem.startswith("My_Site_2_2025-07-16_heat")


# --------------------------------------------------------------------------- BlankConfig


def test_blank_template_loads():
    config = load_config(TEMPLATES / "blanks.example.toml", BlankConfig)
    assert config.multiple_per_day is True
    assert config.sample_excludes == ["05.22.25"]


def test_blank_defaults():
    config = BlankConfig(project_folder="some/folder")
    assert config.blank_includes == ["INPs_L_frozen_at_temp_reviewed", "blank"]
    assert config.only_within_dates is True


def test_blank_provenance_stem():
    config = BlankConfig(project_folder="data/NSA_qc_flag_test")
    assert config.provenance_stem() == "NSA_qc_flag_test_blank_correction"


# ----------------------------------------------------------------------- FinalCombineConfig


def test_final_template_loads():
    config = load_config(TEMPLATES / "final_combine.example.toml", FinalCombineConfig)
    assert config.treatment_dict == {"base": 0, "heat": 1, "peroxide": 2}


def test_final_build_header_injects_error_signal():
    config = FinalCombineConfig(project_folder="p")
    header = config.build_header_start()
    assert "-9999" in header
    assert "ARM Mentor:" in header


def test_final_header_override():
    config = FinalCombineConfig(project_folder="p", header_start="custom\n")
    assert config.build_header_start() == "custom\n"


def test_final_provenance_stem():
    config = FinalCombineConfig(project_folder="data/NSA_qc_flag_test")
    assert config.provenance_stem() == "NSA_qc_flag_test_final_combine"
