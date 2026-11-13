"""The machine-wide instance cap: a fixed set of lock files, one ``flock`` each (docs/plans/phase-e.md 3.1).

A slot is the exclusive ``flock`` on ``slot-<k>.lock`` for ``k`` below the cap. The lock belongs to the open file
description, so the worker process that inherits the fd keeps the slot and the kernel frees it the moment that
process dies, however it dies; a parent that was SIGKILLed leaks nothing. Nothing is ever written into a lock file.

The cap is machine-wide only if every user reads the same ``LAZ_MAX_INSTANCES``: a process with cap 5 takes slots
3 and 4 beside three cap-3 users. The folder, the cap and the timeout are read from the environment on every
call, never at import, so a test or a tool may change them between acquisitions.
"""
from __future__ import annotations

import fcntl
import math
import os
import time
import warnings
from pathlib import Path
from typing import Optional

from .errors import ArgumentError, LoadWarning, SlotTimeout

__all__ = ["DEFAULT_CAP", "Slot", "SlotTimeout", "LoadWarning", "slot_dir", "cap", "acquire", "warn_if_loaded", "waited_in"]

DEFAULT_CAP = 4                 # tools/speed_table.py cap_rule on a real 3D scene, docs/research/real-scene-v3.md
MAX_CAP = 64
DEFAULT_TIMEOUT_S = 3600.0
ROUND_SLEEP_S = 0.1


def slot_dir() -> Path:
    """The lock folder: ``LAZ_SLOT_DIR``, else ``~/Library/Caches/libazahar-py/slots``; created mode 0700."""
    text = os.environ.get("LAZ_SLOT_DIR")
    folder = Path(text) if text else Path.home() / "Library" / "Caches" / "libazahar-py" / "slots"
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    return folder


def cap() -> int:
    """The number of slots: ``LAZ_MAX_INSTANCES`` (an int 1..64), else DEFAULT_CAP. ArgumentError names the variable."""
    text = os.environ.get("LAZ_MAX_INSTANCES")
    if text is None:
        return DEFAULT_CAP
    try:
        value = int(text)
    except ValueError:
        raise ArgumentError(f"LAZ_MAX_INSTANCES={text!r} is not an integer from 1 to {MAX_CAP}") from None
    if not 1 <= value <= MAX_CAP:
        raise ArgumentError(f"LAZ_MAX_INSTANCES={value} is outside 1 to {MAX_CAP}")
    return value


def _timeout_default() -> float:
    text = os.environ.get("LAZ_SLOT_TIMEOUT")
    if text is None:
        return DEFAULT_TIMEOUT_S
    try:
        return float(text)
    except ValueError:
        raise ArgumentError(f"LAZ_SLOT_TIMEOUT={text!r} is not a number of seconds") from None


class Slot:
    """One held slot: ``index``, the lock file's ``fd`` (inheritable by a child on request), ``path`` and
    ``waited_s``. ``release()`` closes the fd (idempotent); a context manager."""

    def __init__(self, index: int, fd: int, path: Path, waited_s: float) -> None:
        self.index = index
        self.fd = fd
        self.path = path
        self.waited_s = waited_s
        self.acquired = time.time()

    def release(self) -> None:
        """Close the fd. The lock stays alive in any process that inherited the fd."""
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def __enter__(self) -> "Slot":
        return self

    def __exit__(self, *exc: object) -> None:
        self.release()


def waited_in(workdir: Path) -> float:
    """The seconds an Emulator waited for its slot, from ``<workdir>/slot.txt`` (0.0 when the file is missing)."""
    try:
        text = (Path(workdir) / "slot.txt").read_text()
    except FileNotFoundError:
        return 0.0
    return float(dict(part.split("=", 1) for part in text.split())["waited_s"])


def warn_if_loaded(stacklevel: int = 3) -> None:
    """Warn (LoadWarning) when the 1-minute load average is above twice the core count."""
    load = os.getloadavg()[0]
    cores = os.cpu_count() or 1
    if load > 2 * cores:
        warnings.warn(LoadWarning(f"load {load:.1f} is above 2 x {cores} cores; other sessions' emulators share "
                                  "this Mac"), stacklevel=stacklevel)


def _try_round(folder: Path, slots: int) -> Optional[tuple]:
    """One pass over the lock files; ``(index, fd, path)`` of the first free one, else None."""
    for index in range(slots):
        path = folder / f"slot-{index}.lock"
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            continue
        except BaseException:
            os.close(fd)
            raise
        return index, fd, path
    return None


def acquire(timeout: Optional[float] = None) -> Slot:
    """Take a free slot, waiting up to ``timeout`` seconds (None: ``LAZ_SLOT_TIMEOUT``, default 3600).

    Raises SlotTimeout (a HostTimeout) when all are held, ArgumentError for a bad ``LAZ_MAX_INSTANCES``. Warns
    LoadWarning once when the machine is loaded.
    """
    limit = _timeout_default() if timeout is None else float(timeout)
    slots = cap()
    folder = slot_dir()
    warn_if_loaded()
    begin = time.monotonic()
    max_rounds = max(1, math.ceil(limit / ROUND_SLEEP_S) + 2)
    for _ in range(max_rounds):
        found = _try_round(folder, slots)
        waited = time.monotonic() - begin
        if found is not None:
            return Slot(found[0], found[1], found[2], waited)
        if waited >= limit:
            break
        time.sleep(min(ROUND_SLEEP_S, max(limit - waited, 0.0)))
    raise SlotTimeout(limit, slots, folder)
