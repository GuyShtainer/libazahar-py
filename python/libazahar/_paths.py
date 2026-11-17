"""Where things live: the repo root, the host library, the core, MoltenVK and the option profile (all absolute)."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from .errors import HostError

__all__ = ["repo_root", "host_path", "core_path", "mvk_path", "profile_path", "lazpy_profile"]

MVK_DEFAULT = "dl/moltenvk/MoltenVK/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib"
SUFFIX = ".dylib" if sys.platform == "darwin" else ".dll" if sys.platform == "win32" else ".so"   # shared libraries
WIN_VULKAN = "vulkan-1.dll"     # Windows: the Vulkan loader, found by the host in System32 (never resolved here)


def repo_root() -> Path:
    """``LAZ_ROOT``, else the repo this package sits in (right for an editable install or a run from the tree)."""
    env = os.environ.get("LAZ_ROOT")
    root = Path(env) if env else Path(__file__).resolve().parents[2]
    return root.resolve()


def host_path() -> Path:
    """``LAZ_HOST``, else ``<root>/build/libazhost<suffix>``; HostError when it is not there."""
    env = os.environ.get("LAZ_HOST")
    path = Path(env) if env else repo_root() / "build" / f"libazhost{SUFFIX}"
    path = path.resolve()
    if not path.is_file():
        raise HostError(f"host library {path} not found: build it with make, set LAZ_ROOT or LAZ_HOST, "
                        "or install with pip install -e .")
    return path


def core_path(core: Optional[str] = None) -> Path:
    """The core: the argument, else ``LAZ_CORE``, else our core at ``<root>/dl/lazpy-core/azahar_lazpy_libretro<suffix>``
    (``tools/fetch.sh --lazpy-core`` puts it there)."""
    chosen = core or os.environ.get("LAZ_CORE")
    return (Path(chosen) if chosen else repo_root() / "dl" / "lazpy-core" / f"azahar_lazpy_libretro{SUFFIX}").resolve()


def mvk_path() -> Path:
    """MoltenVK: ``LAZ_MVK``, else the default under ``<root>/dl/moltenvk/``. On Windows, with ``LAZ_MVK`` unset, the
    bare name ``vulkan-1.dll`` (not a path: the host loads it from System32)."""
    env = os.environ.get("LAZ_MVK")
    if not env and sys.platform == "win32":
        return Path(WIN_VULKAN)
    return (Path(env) if env else repo_root() / MVK_DEFAULT).resolve()


def profile_path() -> Path:
    """The option profile: ``LAZ_PROFILE``, else ``<root>/host/options-default.txt``."""
    env = os.environ.get("LAZ_PROFILE")
    return (Path(env) if env else repo_root() / "host" / "options-default.txt").resolve()


def lazpy_profile() -> Optional[Path]:
    """The option lines our core adds: ``LAZ_LAZPY_PROFILE`` (the text ``none`` gives None; a missing file it names is a
    HostError), else ``<root>/core/options-lazpy.txt``, or None when that file is not there (a pip install has no core/)."""
    env = os.environ.get("LAZ_LAZPY_PROFILE")
    if env == "none":
        return None
    if env:
        path = Path(env).resolve()
        if not path.is_file():
            raise HostError(f"LAZ_LAZPY_PROFILE {path} is not a file")
        return path
    path = (repo_root() / "core" / "options-lazpy.txt").resolve()
    return path if path.is_file() else None
