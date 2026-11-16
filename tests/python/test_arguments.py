"""Bad arguments raise ArgumentError (a LibAzaharError and a ValueError); fresh_sd's clear; Shot's whole-run frame.
No emulator."""
from __future__ import annotations

import inspect
import os
from pathlib import Path

import numpy as np
import pytest

from libazahar import ArgumentError, Buttons, LibAzaharError, Shot, _abi, errors
from libazahar import Emulator
from libazahar.emulator import _clear_sd
from libazahar.inputs import Held, fold


def test_argument_error_is_both():
    assert issubclass(ArgumentError, LibAzaharError) and issubclass(ArgumentError, ValueError)
    assert type(errors.from_code(_abi.AZH_E_ARG, "host text")) is ArgumentError


@pytest.mark.parametrize("frame", [0, -1, 11])
def test_input_frame_outside_batch_is_library_error(frame):
    with pytest.raises(LibAzaharError, match=r"outside 1\.\.10"):
        fold([(frame, Buttons.A)], 10, Held())


def test_clear_sd_empties_the_card_only(tmp_path):
    sd = tmp_path / "sys" / "Azahar" / "sdmc"
    (sd / "app").mkdir(parents=True)
    (sd / "app" / "old.csv").write_text("x")
    keep = tmp_path / "sys" / "Azahar" / "shaders"
    keep.mkdir()
    (keep / "cache.bin").write_text("y")
    _clear_sd(sd)
    assert not sd.exists() and (keep / "cache.bin").is_file()
    _clear_sd(sd)                                       # a missing card is fine


def test_clear_sd_refuses_a_symlink(tmp_path):
    target = tmp_path / "elsewhere"
    target.mkdir()
    (target / "f").write_text("z")
    link = tmp_path / "sdmc"
    try:
        os.symlink(target, link)
    except OSError as exc:                  # Windows without Developer Mode may not create symlinks
        pytest.skip(f"cannot create a symlink here: {exc}")
    with pytest.raises(ArgumentError):
        _clear_sd(link)
    assert (target / "f").is_file()


def test_shot_holds_paths_and_requires_frame_total():
    shot = Shot(5, Path("t.png"), Path("b.png"), 305)
    assert shot.frame == 5 and shot.frame_total == 305 and isinstance(shot.top, Path)
    with pytest.raises(TypeError):
        Shot(5, Path("t.png"), Path("b.png"))        # type: ignore[call-arg]


def test_missing_core_names_the_fix(tmp_path):
    from libazahar import BootError, Emulator
    app = tmp_path / "app.3dsx"
    app.write_bytes(b"3DSX")
    with pytest.raises(BootError, match="fetch.sh --lazpy-core"):
        Emulator(app, tmp_path / "w", core=tmp_path / "no-such-core.dylib")


def test_run_options_are_keyword_only():
    for method in (Emulator.run, Emulator.run_until):
        positional = [p.name for p in inspect.signature(method).parameters.values()
                      if p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD]
        assert positional == (["self", "frames"] if method is Emulator.run else ["self", "file", "text", "max_frames"])
    assert "inputs" in inspect.signature(Emulator.run_until).parameters


def test_run_until_uses_runs_vocabulary():
    run_names = set(inspect.signature(Emulator.run).parameters) - {"frames"}
    until_names = set(inspect.signature(Emulator.run_until).parameters) - {"file", "text", "max_frames"}
    assert until_names == run_names - {"stop_file", "stop_text"}


def _batch(frames, shots=()):
    emu = Emulator.__new__(Emulator)
    emu._shots_dir = Path("shots")
    return emu._build_batch(frames, shots, None, None, 30, False, None, None)


def test_frames_and_shots_take_numpy_integers_but_not_floats():
    batch, shot_frames = _batch(np.int64(10), [np.int32(3), 4])
    assert batch.frames == 10 and shot_frames == [3, 4]
    for bad in (1.5, np.float64(2.0), True, "3"):
        with pytest.raises(ArgumentError):
            _batch(bad)
    with pytest.raises(ArgumentError, match="shots"):
        _batch(10, [1.5])


@pytest.mark.parametrize("every", [0, -1, 100_001, 1.5, True])
def test_watch_every_must_be_1_to_100000(every):
    with pytest.raises(ArgumentError, match="watch_every"):
        Emulator._fill_watch(_abi.Batch(), None, every)
    assert Emulator._fill_watch(_abi.Batch(), None, 100_000) == []
