"""Typed errors of libazahar (docs/plans/phase-d.md 4.5). Every error carries the host's text."""
from __future__ import annotations

import signal as _signal
from pathlib import Path
from typing import Optional

from . import _abi

__all__ = ["LibAzaharError", "ArgumentError", "BootError", "GuestError", "HostTimeout", "HostCrashed", "StateError",
           "NeedsLazpyCore", "GuestMemoryError", "HostError", "SlotTimeout", "LoadWarning"]


class LibAzaharError(Exception):
    """Base class of every error this package raises on purpose.

    An error raised by a live instance (BootError, GuestError, HostTimeout, HostCrashed, StateError, HostError,
    GuestMemoryError) also carries ``workdir`` and ``log_path`` (both None on the others); its text then names
    ``host.log`` and the newest PNG under ``shots/``, if any."""

    workdir: Optional[Path] = None
    log_path: Optional[Path] = None
    _shot_name: Optional[str] = None

    def __str__(self) -> str:
        text = super().__str__()
        if self.log_path is not None:
            text += f"\n(evidence: {self.log_path}"
            text += f"; newest shot taken: {self._shot_name})" if self._shot_name else "; no shot taken)"
        return text


EVIDENCE_TYPES: tuple = ()      # filled below, after the classes exist


def _state(exc: LibAzaharError) -> dict:
    """The evidence fields, so a pickled error keeps them (a custom ``__reduce__`` would drop ``__dict__``)."""
    return {k: v for k, v in exc.__dict__.items() if k in ("workdir", "log_path", "_shot_name")}


def newest_shot(workdir: Path) -> Optional[Path]:
    """The newest PNG under ``<workdir>/shots/`` (by modification time, then name), or None."""
    try:
        shots = [p for p in (Path(workdir) / "shots").rglob("*.png") if p.is_file()]
        return max(shots, key=lambda p: (p.stat().st_mtime_ns, p.name)) if shots else None
    except OSError:
        return None


def attach_evidence(exc: BaseException, workdir: Path, log_path: Path) -> BaseException:
    """Give a live-instance error its ``workdir`` and ``log_path`` and the newest shot's name. Other errors, and an
    error already marked, pass through unchanged. Returns ``exc``."""
    if isinstance(exc, EVIDENCE_TYPES) and exc.log_path is None:
        exc.workdir = Path(workdir)
        exc.log_path = Path(log_path)
        shot = newest_shot(workdir)
        exc._shot_name = str(shot.relative_to(workdir)) if shot is not None else None
    return exc


class ArgumentError(LibAzaharError, ValueError):
    """A bad argument (a frame outside 1..N, a bad address, a bad option). It is also a ValueError."""


class BootError(LibAzaharError):
    """The core, Vulkan or the app failed to start (also the first frame's boot check)."""


class GuestError(LibAzaharError):
    """The guest stopped with a fatal error; ``result`` holds the RunResult when there is one."""

    def __init__(self, message: str, result: object = None) -> None:
        super().__init__(message)
        self.result = result

    def __reduce__(self):  # type: ignore[no-untyped-def]
        return (GuestError, (self.args[0] if self.args else "", self.result), _state(self))


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

    def __reduce__(self):  # type: ignore[no-untyped-def]
        return (HostTimeout, (self.op, self.seconds, self.message), _state(self))


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

    def __reduce__(self):  # type: ignore[no-untyped-def]
        return (HostCrashed, (self.returncode, self.signal, self.message, self.log_tail, self.err_tail), _state(self))

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


class GuestMemoryError(LibAzaharError):
    """A guest address range has an unmapped page (AZH_E_UNMAPPED). A read or write is all-or-nothing, so a failed write
    changed nothing. ``addr`` and ``length`` are the request (None when unknown)."""

    def __init__(self, message: str, addr: Optional[int] = None, length: Optional[int] = None) -> None:
        super().__init__(message)
        self.addr = addr
        self.length = length

    def __reduce__(self):  # type: ignore[no-untyped-def]
        return (GuestMemoryError, (self.args[0] if self.args else "", self.addr, self.length), _state(self))


class HostError(LibAzaharError):
    """Wrong call order, I/O, memory, an unsupported call, an ABI mismatch or a missing host."""


class SlotTimeout(HostTimeout):
    """No slot became free in time (a HostTimeout, so ``except HostTimeout`` still catches it). ``op`` is ``"slot"``;
    ``slots`` is the cap and ``folder`` the lock folder."""

    def __init__(self, seconds: float, slots: int, folder: Path) -> None:
        super().__init__("slot", seconds)          # HostTimeout needs (op, seconds); there is no guest message here
        self.slots = slots
        self.folder = Path(folder)
        self.args = (str(self),)

    def __reduce__(self):  # type: ignore[no-untyped-def]
        return (SlotTimeout, (self.seconds, self.slots, self.folder))

    def __str__(self) -> str:
        return f"no libazahar slot free after {self.seconds:g} s: all {self.slots} are held; see {self.folder}"


EVIDENCE_TYPES = (BootError, GuestError, HostTimeout, HostCrashed, StateError, HostError, GuestMemoryError)


class LoadWarning(UserWarning):
    """The machine's 1-minute load average is above twice its core count."""


class HostCallError(Exception):
    """Internal: a negative return of an azh_* call with the host's error text."""

    def __init__(self, code: int, text: str) -> None:
        super().__init__(f"{code}: {text}")
        self.code = code
        self.text = text


def from_code(code: int, text: str, during_start: bool = False) -> Exception:
    """Map an AZH_E_* code and the host's text to the exception to raise (ArgumentError for AZH_E_ARG)."""
    if code == _abi.AZH_E_ARG:
        return ArgumentError(text)
    if code == _abi.AZH_E_BOOT or (during_start and code in (_abi.AZH_E_CORE, _abi.AZH_E_VULKAN)):
        return BootError(text)
    if code == _abi.AZH_E_SAVESTATE:
        return StateError(text)
    if code == _abi.AZH_E_NEEDS_LAZPY_CORE:
        return NeedsLazpyCore(text)
    if code == _abi.AZH_E_UNMAPPED:
        return GuestMemoryError(text)
    return HostError(text)
