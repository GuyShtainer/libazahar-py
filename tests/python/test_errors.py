"""Every host code maps to its class (no emulator)."""
import signal

import pytest

from libazahar import _abi, errors


@pytest.mark.parametrize("code,cls", [
    (_abi.AZH_E_BOOT, errors.BootError), (_abi.AZH_E_CORE, errors.HostError),
    (_abi.AZH_E_VULKAN, errors.HostError), (_abi.AZH_E_ORDER, errors.HostError), (_abi.AZH_E_IO, errors.HostError),
    (_abi.AZH_E_NOMEM, errors.HostError), (_abi.AZH_E_UNSUPPORTED, errors.HostError),
    (_abi.AZH_E_NEEDS_LAZPY_CORE, errors.NeedsLazpyCore), (_abi.AZH_E_SAVESTATE, errors.StateError),
    (_abi.AZH_E_ARG, errors.ArgumentError), (-99, errors.HostError)])
def test_code_maps_to_class(code, cls):
    exc = errors.from_code(code, "host text")
    assert type(exc) is cls and "host text" in str(exc)


def test_start_makes_core_and_vulkan_boot_errors():
    assert isinstance(errors.from_code(_abi.AZH_E_CORE, "x", during_start=True), errors.BootError)
    assert isinstance(errors.from_code(_abi.AZH_E_VULKAN, "x", during_start=True), errors.BootError)
    assert type(errors.from_code(_abi.AZH_E_IO, "x", during_start=True)) is errors.HostError


def test_all_derive_from_base():
    for cls in (errors.ArgumentError, errors.BootError, errors.GuestError, errors.HostTimeout, errors.HostCrashed, errors.StateError,
                errors.NeedsLazpyCore, errors.HostError):
        assert issubclass(cls, errors.LibAzaharError)


def test_guest_error_carries_result_and_crash_details():
    assert errors.GuestError("m", result=7).result == 7
    crash = errors.HostCrashed(-11, 11, "msg", "log", "err")
    assert crash.signal == signal.SIGSEGV and "log" in str(crash) and "err" in str(crash)
    assert errors.HostTimeout("run", 3.0, "last").seconds == 3.0


def test_slot_and_load_classes_live_in_errors():
    assert errors.SlotTimeout.__module__ == "libazahar.errors" and errors.LoadWarning.__module__ == "libazahar.errors"
    assert issubclass(errors.SlotTimeout, errors.HostTimeout)
    assert errors.SlotTimeout(1.0, 2, "/x").op == "slot"


def test_constructor_refuses_a_missing_sd_seed_with_argument_error(tmp_path):
    from libazahar import Emulator
    app = tmp_path / "app.3dsx"
    app.write_bytes(b"3DSX")
    with pytest.raises(errors.ArgumentError, match="sd_seed"):
        Emulator(app, tmp_path / "w", sd_seed=tmp_path / "no-such-folder")


def test_constructor_turns_a_missing_profile_into_host_error(tmp_path, monkeypatch):
    from libazahar import Emulator
    app, core = tmp_path / "app.3dsx", tmp_path / "core.dylib"
    app.write_bytes(b"3DSX")
    core.write_bytes(b"x")
    monkeypatch.setenv("LAZ_PROFILE", str(tmp_path / "no-such-profile.txt"))
    with pytest.raises(errors.HostError, match="no-such-profile"):
        Emulator(app, tmp_path / "w", core=core)


def test_app_and_workdir_are_read_only(tmp_path):
    from libazahar import Emulator
    app = tmp_path / "app.3dsx"
    app.write_bytes(b"3DSX")
    emu = Emulator.__new__(Emulator)
    emu._app, emu._workdir = app, tmp_path
    assert emu.app == app and emu.workdir == tmp_path
    with pytest.raises(AttributeError):
        emu.app = tmp_path                            # type: ignore[misc]
    with pytest.raises(AttributeError):
        emu.workdir = tmp_path                        # type: ignore[misc]


# ---- evidence on failure (B2) ----
LIVE_ERRORS = [lambda: errors.BootError("b"), lambda: errors.GuestError("g", 7), lambda: errors.HostTimeout("run", 2.0, "m"),
               lambda: errors.HostCrashed(-11, 11, "m", "log", "err"), lambda: errors.StateError("s"),
               lambda: errors.HostError("h"), lambda: errors.GuestMemoryError("u", 4, 8)]


@pytest.mark.parametrize("make", LIVE_ERRORS)
def test_evidence_names_the_log_and_the_newest_shot_and_survives_pickling(make, tmp_path):
    import pickle
    shots = tmp_path / "shots"
    shots.mkdir()
    (shots / "a_top.png").write_bytes(b"x")
    newest = shots / "z_top.png"
    newest.write_bytes(b"y")
    import os
    os.utime(shots / "a_top.png", (1, 1))
    exc = make()
    assert exc.workdir is None and exc.log_path is None            # a fresh error carries nothing yet
    errors.attach_evidence(exc, tmp_path, tmp_path / "host.log")
    assert exc.workdir == tmp_path and exc.log_path == tmp_path / "host.log"
    text = str(exc)
    assert "host.log" in text and "z_top.png" in text and "a_top.png" not in text
    back = pickle.loads(pickle.dumps(exc))
    assert type(back) is type(exc) and str(back) == text
    assert back.workdir == tmp_path and back.log_path == tmp_path / "host.log"


def test_evidence_without_a_shot_and_for_other_errors(tmp_path):
    exc = errors.attach_evidence(errors.HostError("h"), tmp_path, tmp_path / "host.log")
    assert "no shot taken" in str(exc)
    arg = errors.attach_evidence(errors.ArgumentError("a"), tmp_path, tmp_path / "host.log")
    assert arg.log_path is None and "evidence" not in str(arg)
    assert errors.attach_evidence(exc, tmp_path / "other", tmp_path / "other.log").log_path == tmp_path / "host.log"


def test_pickled_errors_without_evidence_still_round_trip():
    import pickle
    for make in LIVE_ERRORS:
        exc = make()
        back = pickle.loads(pickle.dumps(exc))
        assert str(back) == str(exc) and back.log_path is None
