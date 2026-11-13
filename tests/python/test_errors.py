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
