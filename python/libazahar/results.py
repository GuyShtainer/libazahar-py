"""Result types returned by the Emulator."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

__all__ = ["Shot", "RunResult", "SaveInfo", "Stats"]


@dataclass(frozen=True)
class Shot:
    """Paths of the two PNGs of one shot frame."""

    frame: int
    top: str
    bottom: str


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
