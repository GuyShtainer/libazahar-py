"""Every host code maps to its class (no emulator)."""
import signal

import pytest

from libazahar import _abi, errors


@pytest.mark.parametrize("code,cls", [
    (_abi.AZH_E_BOOT, errors.BootError), (_abi.AZH_E_CORE, errors.HostError),
    (_abi.AZH_E_VULKAN, errors.HostError), (_abi.AZH_E_ORDER, errors.HostError), (_abi.AZH_E_IO, errors.HostError),
    (_abi.AZH_E_NOMEM, errors.HostError), (_abi.AZH_E_UNSUPPORTED, errors.HostError),
    (_abi.AZH_E_NEEDS_LAZPY_CORE, errors.NeedsLazpyCore), (_abi.AZH_E_SAVESTATE, errors.StateError),
    (_abi.AZH_E_ARG, ValueError), (-99, errors.HostError)])
def test_code_maps_to_class(code, cls):
    exc = errors.from_code(code, "host text")
    assert type(exc) is cls and "host text" in str(exc)


def test_start_makes_core_and_vulkan_boot_errors():
    assert isinstance(errors.from_code(_abi.AZH_E_CORE, "x", during_start=True), errors.BootError)
    assert isinstance(errors.from_code(_abi.AZH_E_VULKAN, "x", during_start=True), errors.BootError)
    assert type(errors.from_code(_abi.AZH_E_IO, "x", during_start=True)) is errors.HostError


def test_all_derive_from_base():
    for cls in (errors.BootError, errors.GuestError, errors.HostTimeout, errors.HostCrashed, errors.StateError,
                errors.NeedsLazpyCore, errors.HostError):
        assert issubclass(cls, errors.LibAzaharError)


def test_guest_error_carries_result_and_crash_details():
    assert errors.GuestError("m", result=7).result == 7
    crash = errors.HostCrashed(-11, 11, "msg", "log", "err")
    assert crash.signal == signal.SIGSEGV and "log" in str(crash) and "err" in str(crash)
    assert errors.HostTimeout("run", 3.0, "last").seconds == 3.0
