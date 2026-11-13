"""libazahar: a headless, scriptable Azahar (libretro core) for testing 3DS homebrew. See docs/USING.md."""
from .emulator import Emulator
from .errors import (BootError, GuestError, GuestMemoryError, HostCrashed, HostError, HostTimeout, LibAzaharError,
                     NeedsLazpyCore, StateError)
from ._slots import LoadWarning, SlotTimeout
from .inputs import Buttons, Circle, Touch
from .pool import Pool
from .memory import Memory
from .results import RunResult, SaveInfo, Shot, Stats, WatchRow

__version__ = "0.1.0"

__all__ = ["Emulator", "Buttons", "Touch", "Circle", "RunResult", "Shot", "WatchRow", "Memory", "GuestMemoryError",
           "SaveInfo", "Stats", "LibAzaharError", "BootError", "GuestError", "HostTimeout", "HostCrashed", "StateError",
           "NeedsLazpyCore", "HostError", "Pool", "LoadWarning", "SlotTimeout", "__version__"]
