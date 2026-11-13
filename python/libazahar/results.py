"""Result types returned by the Emulator."""
from __future__ import annotations

from dataclasses import dataclass, field
import struct
from typing import Dict, Tuple

__all__ = ["Shot", "WatchRow", "RunResult", "SaveInfo", "Stats", "ThreadInfo"]


@dataclass(frozen=True)
class Shot:
    """Paths of the two PNGs of one shot frame. ``frame`` is the batch frame (the key in ``RunResult.shots``);
    ``frame_total`` is the frame counted since boot, the number in the file names."""

    frame: int
    top: str
    bottom: str
    frame_total: int = 0


@dataclass(frozen=True)
class WatchRow:
    """One row of a batch's watch list: the absolute frame it was read after, the row status (0, or an AZH_E_* code of
    the first entry that failed), and one ``bytes`` per watch entry in list order (a failed entry reads as zeros).
    The guest may be part-way into a frame when a row is read, so a multi-field record can be torn."""

    frame: int
    status: int
    data: Tuple[bytes, ...]

    def u32(self, entry: int, word: int = 0) -> int:
        """The little-endian u32 at ``word`` of watch entry ``entry``."""
        return int(struct.unpack_from("<I", self.data[entry], 4 * word)[0])


@dataclass(frozen=True)
class RunResult:
    """What one batch did. ``frames`` counts the frame that triggered a stop; ``first_frame`` and ``last_frame`` are
    absolute (1-based since boot); ``shots`` maps a batch frame to its Shot."""

    frames: int
    stopped_by: str
    first_frame: int
    last_frame: int
    frame_total: int
    vblanks: int
    wall_s: float
    message: str = ""
    shots: Dict[int, Shot] = field(default_factory=dict)
    watch: Tuple[WatchRow, ...] = ()


@dataclass(frozen=True)
class SaveInfo:
    """A saved state: ``k`` guest VBlanks the save's drain ran; a state at frame N is at N + k."""

    path: str
    k: int
    frame_total: int


@dataclass(frozen=True)
class Stats:
    """The host's counters (azh_stats)."""

    frames: int
    wall_s: float
    user_s: float
    sys_s: float
    peak_rss: int
    core_name: str
    core_version: str
    is_lazpy_core: bool


@dataclass(frozen=True)
class ThreadInfo:
    """One guest thread from ``Emulator.threads()`` (core lazpy.2). ``status`` is Azahar's ThreadStatus number and
    ``status_name`` its name; ``is_current`` marks the thread a core was running (its registers come from the live
    CPU, every other thread's from its saved context); ``pid`` is 0xFFFFFFFF for a thread with no owner process.
    Bit 5 of ``cpsr`` is the Thumb bit."""

    tid: int
    pid: int
    status: int
    status_name: str
    core: int
    priority: int
    is_current: bool
    pc: int
    lr: int
    sp: int
    cpsr: int
