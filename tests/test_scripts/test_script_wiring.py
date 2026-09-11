"""Wiring tests for the three pipeline entry-point scripts.

These tests verify that each script's ``run(config)`` translates a validated config into the
correct calls on the underlying processing classes and writes a provenance copy. The
processing classes are replaced with lightweight spies so the tests are deterministic, fast
and independent of real data (and of the pre-existing GraphDataCSV bug flagged in TODO.md).
"""

import math

import pytest

import olaf.main as main_mod
import olaf.main_final_combine as final_mod
import olaf.main_for_blanks as blanks_mod
from olaf.config import BlankConfig, FinalCombineConfig, MainConfig

# --------------------------------------------------------------------------- spies


class _Recorder:
    """Collects constructor args and method calls made on fake processing classes."""

    def __init__(self):
        self.init_args = None
        self.init_kwargs = None
        self.calls = {}


def _make_fake(recorder: _Recorder):
    class _Fake:
        def __init__(self, *args, **kwargs):
            recorder.init_args = args
            recorder.init_kwargs = kwargs

        def __getattr__(self, name):
            def _method(*args, **kwargs):
                recorder.calls[name] = {"args": args, "kwargs": kwargs}
                return None

            return _method

    return _Fake


class _FakeWindow:
    """Stand-in for the Tk root so ``run`` can drive the mandatory GUI headlessly."""

    def mainloop(self):
        return None

    def __getattr__(self, name):
        return lambda *args, **kwargs: None


def _stub_gui(monkeypatch):
    """Replace the Tk root and FreezingReviewer so the review step is a headless no-op.

    Stage 1 always opens the reviewer GUI; these wiring tests stub it out (rather than
    remove it) so they stay deterministic and runnable without a ``$DISPLAY``.
    """
    monkeypatch.setattr(main_mod.tk, "Tk", lambda *args, **kwargs: _FakeWindow())
    monkeypatch.setattr(main_mod, "FreezingReviewer", _make_fake(_Recorder()))


# --------------------------------------------------------------------------- main.py


def _main_config(folder):
    return MainConfig(
        data_folder=str(folder),
        site="SITE",
        start_time="2025-07-16 16:20:00",
        end_time="2025-07-16 17:52:00",
        filter_color="white",
        notes="none",
        user="tester",
        IS="IS2",
        num_samples=6,
        sample_type="air",
        vol_air_filt=620.48,
        wells_per_sample=32,
        proportion_filter_used=1.0,
        vol_susp=10,
        treatment=["base"],
        dict_samples_to_dilution={"Sample_0": 1, "Sample_5": math.inf},
        freezing_point_depression_dict={"Sample_0": 2},
    )


def test_main_run_wires_processing_classes(tmp_path, monkeypatch):
    folder = tmp_path / "SITE 07.16.25 base"
    folder.mkdir()
    config = _main_config(folder)

    spaced_rec, graph_rec = _Recorder(), _Recorder()
    _stub_gui(monkeypatch)
    monkeypatch.setattr(main_mod, "SpacedTempCSV", _make_fake(spaced_rec))
    monkeypatch.setattr(main_mod, "GraphDataCSV", _make_fake(graph_rec))

    main_mod.run(config)

    # SpacedTempCSV(data_folder, num_samples, includes=treatment)
    assert spaced_rec.init_args[0] == config.data_folder
    assert spaced_rec.init_args[1] == config.num_samples
    assert spaced_rec.init_kwargs["includes"] == ("base",)
    # create_temp_csv(dilution, fpd, wells, sample_type)
    ctc = spaced_rec.calls["create_temp_csv"]["args"]
    assert ctc[0] == config.dict_samples_to_dilution
    assert ctc[1] == config.freezing_point_depression_dict
    assert ctc[2] == config.wells_per_sample
    assert ctc[3] == config.sample_type

    # GraphDataCSV(folder, num_samples, sample_type, vol_air_filt, wells, prop, vol_susp, dict)
    gargs = graph_rec.init_args
    assert gargs[2] == config.sample_type
    assert gargs[3] == config.effective_vol_air_filt
    assert gargs[5] == config.proportion_filter_used
    assert graph_rec.init_kwargs["includes"] == ("07.16.25", "base")
    # convert_INPs_L(header, show_plot=...)
    assert "site = SITE" in graph_rec.calls["convert_INPs_L"]["args"][0]


def test_main_run_writes_provenance(tmp_path, monkeypatch):
    folder = tmp_path / "SITE 07.16.25 base"
    folder.mkdir()
    cfg_path = tmp_path / "run.toml"
    cfg_path.write_text('site = "SITE"\n')
    config = _main_config(folder)

    _stub_gui(monkeypatch)
    monkeypatch.setattr(main_mod, "SpacedTempCSV", _make_fake(_Recorder()))
    monkeypatch.setattr(main_mod, "GraphDataCSV", _make_fake(_Recorder()))

    main_mod.run(config)
    main_mod.save_copy(cfg_path, config.data_folder, config.provenance_stem())

    written = list(folder.glob("used_config_*.toml"))
    assert written == [folder / "used_config_SITE_2025-07-16_base.toml"]


# --------------------------------------------------------------------------- main_for_blanks.py


def test_blanks_run_wires_corrector(tmp_path, monkeypatch):
    config = BlankConfig(
        project_folder=str(tmp_path),
        blank_includes=["INPs_L", "blank"],
        blank_excludes=["x"],
        sample_excludes=["05.22.25"],
        multiple_per_day=True,
        only_within_dates=False,
        show_comp_plot=True,
    )
    rec = _Recorder()
    monkeypatch.setattr(blanks_mod, "BlankCorrector", _make_fake(rec))

    blanks_mod.run(config)

    assert rec.init_args[0] == config.project_folder
    assert rec.init_args[1] == ("INPs_L", "blank")
    assert rec.init_args[3] == ("05.22.25",)
    assert rec.init_kwargs["multiple_per_day"] is True
    assert "average_blanks" in rec.calls
    apply_kwargs = rec.calls["apply_blanks"]["kwargs"]
    assert apply_kwargs["only_within_dates"] is False
    assert apply_kwargs["show_comp_plot"] is True


# --------------------------------------------------------------------------- main_final_combine.py


def test_final_run_wires_creation(tmp_path, monkeypatch):
    config = FinalCombineConfig(
        project_folder=str(tmp_path),
        includes=["INPs_L", "blank_corrected"],
        excludes=["blanks"],
        treatment_dict={"base": 0, "heat": 1},
    )
    rec = _Recorder()
    monkeypatch.setattr(final_mod, "FinalFileCreation", _make_fake(rec))

    final_mod.run(config)

    assert rec.init_args[0] == config.project_folder
    assert rec.init_args[1] == ("INPs_L", "blank_corrected")
    assert rec.init_args[2] == ("blanks",)
    caf = rec.calls["create_all_final_files"]["args"]
    assert caf[0] == config.treatment_dict
    assert "-9999" in caf[1]  # header includes the error signal


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-v"])
