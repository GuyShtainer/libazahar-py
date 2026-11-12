"""Typed errors of libazahar (docs/plans/phase-d.md 4.5). Every error carries the host's text."""
from __future__ import annotations

import signal as _signal
from typing import Optional

from . import _abi

__all__ = ["LibAzaharError", "BootError", "GuestError", "HostTimeout", "HostCrashed", "StateError",
           "NeedsLazpyCore", "HostError", "HostCallError", "from_code"]


class LibAzaharError(Exception):
    """Base class of every error this package raises on purpose."""


class BootError(LibAzaharError):
    """The core, Vulkan or the app failed to start (also the first frame's boot check)."""


class GuestError(LibAzaharError):
    """The guest stopped with a fatal error; ``result`` holds the RunResult when there is one."""

    def __init__(self, message: str, result: object = None) -> None:
        super().__init__(message)
        self.result = result


class HostTimeout(LibAzaharError):
    """A call did not finish in time; the worker was killed and reaped."""

    def __init__(self, op: str, seconds: float, message: Optional[str] = None) -> None:
        text = f"{op} timed out after {seconds:.1f} s"
        if message:
            text += f" (last guest message: {message})"
        super().__init__(text)
        self.op = op
        self.seconds = seconds
        self.message = message


class HostCrashed(LibAzaharError):
    """The worker process died (a signal gives a negative return code)."""

    def __init__(self, returncode: int, signal_number: Optional[int], message: Optional[str] = None,
                 log_tail: str = "", err_tail: str = "") -> None:
        how = f"signal {signal_number}" if signal_number else f"exit code {returncode}"
        text = f"the worker died ({how})"
        if message:
            text += f"; last guest message: {message}"
        if log_tail:
            text += f"\n--- host.log tail ---\n{log_tail}"
        if err_tail:
            text += f"\n--- worker.err tail ---\n{err_tail}"
        super().__init__(text)
        self.returncode = returncode
        self.signal = signal_number
        self.message = message
        self.log_tail = log_tail
        self.err_tail = err_tail

    @staticmethod
    def signal_name(number: Optional[int]) -> str:
        """Name of a signal number, or its digits when unknown."""
        if number is None:
            return "none"
        try:
            return _signal.Signals(number).name
        except ValueError:
            return str(number)


class StateError(LibAzaharError):
    """A savestate could not be saved, read or restored (AZH_E_SAVESTATE)."""


class NeedsLazpyCore(LibAzaharError):
    """The call needs our patched core (AZH_E_NEEDS_LAZPY_CORE)."""


class HostError(LibAzaharError):
    """Wrong call order, I/O, memory, an unsupported call, an ABI mismatch or a missing host."""


class HostCallError(Exception):
    """Internal: a negative return of an azh_* call with the host's error text."""

    def __init__(self, code: int, text: str) -> None:
        super().__init__(f"{code}: {text}")
        self.code = code
        self.text = text


def from_code(code: int, text: str, during_start: bool = False) -> Exception:
    """Map an AZH_E_* code and the host's text to the exception to raise (ValueError for AZH_E_ARG)."""
    if code == _abi.AZH_E_ARG:
        return ValueError(text)
    if code == _abi.AZH_E_BOOT or (during_start and code in (_abi.AZH_E_CORE, _abi.AZH_E_VULKAN)):
        return BootError(text)
    if code == _abi.AZH_E_SAVESTATE:
        return StateError(text)
    if code == _abi.AZH_E_NEEDS_LAZPY_CORE:
        return NeedsLazpyCore(text)
    return HostError(text)
