"""libazahar: a headless, scriptable Azahar (libretro core) for testing 3DS homebrew. See docs/USING.md."""
from .emulator import Emulator
from .errors import (BootError, GuestError, HostCrashed, HostError, HostTimeout, LibAzaharError, NeedsLazpyCore,
                     StateError)
from .inputs import Buttons, Circle, Touch
from .results import RunResult, SaveInfo, Shot, Stats

__version__ = "0.1.0.dev0"

__all__ = ["Emulator", "Buttons", "Touch", "Circle", "RunResult", "Shot", "SaveInfo", "Stats", "LibAzaharError",
           "BootError", "GuestError", "HostTimeout", "HostCrashed", "StateError", "NeedsLazpyCore", "HostError",
           "__version__"]
