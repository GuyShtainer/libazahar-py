"""Bad arguments raise ArgumentError (a LibAzaharError and a ValueError); fresh_sd's clear; Shot's whole-run frame.
No emulator."""
from __future__ import annotations

import os

import pytest

from libazahar import ArgumentError, Buttons, LibAzaharError, Shot, _abi, errors
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
    os.symlink(target, link)
    with pytest.raises(ArgumentError):
        _clear_sd(link)
    assert (target / "f").is_file()


def test_shot_keeps_its_old_shape():
    shot = Shot(5, "t.png", "b.png")
    assert shot.frame == 5 and shot.frame_total == 0


def test_missing_core_names_the_fix(tmp_path):
    from libazahar import BootError, Emulator
    app = tmp_path / "app.3dsx"
    app.write_bytes(b"3DSX")
    with pytest.raises(BootError, match="fetch.sh --lazpy-core"):
        Emulator(app, tmp_path / "w", core=tmp_path / "no-such-core.dylib")
