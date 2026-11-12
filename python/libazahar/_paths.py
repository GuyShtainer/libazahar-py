"""Where things live: the repo root, the host library, the core, MoltenVK and the option profile (all absolute)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .errors import HostError

__all__ = ["repo_root", "host_path", "core_path", "mvk_path", "profile_path"]

MVK_DEFAULT = "dl/moltenvk/MoltenVK/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib"


def repo_root() -> Path:
    """``LAZ_ROOT``, else the repo this package sits in (right for an editable install or a run from the tree)."""
    env = os.environ.get("LAZ_ROOT")
    root = Path(env) if env else Path(__file__).resolve().parents[2]
    return root.resolve()


def host_path() -> Path:
    """``LAZ_HOST``, else ``<root>/build/libazhost.dylib``; HostError when it is not there."""
    env = os.environ.get("LAZ_HOST")
    path = Path(env) if env else repo_root() / "build" / "libazhost.dylib"
    path = path.resolve()
    if not path.is_file():
        raise HostError(f"host library {path} not found: build it with make, set LAZ_ROOT or LAZ_HOST, "
                        "or install with pip install -e .")
    return path


def core_path(core: Optional[str] = None) -> Path:
    """The core: the argument, else ``LAZ_CORE``, else ``<root>/dl/azahar/azahar_libretro.dylib``."""
    chosen = core or os.environ.get("LAZ_CORE")
    return (Path(chosen) if chosen else repo_root() / "dl" / "azahar" / "azahar_libretro.dylib").resolve()


def mvk_path() -> Path:
    """MoltenVK: ``LAZ_MVK``, else the default under ``<root>/dl/moltenvk/``."""
    env = os.environ.get("LAZ_MVK")
    return (Path(env) if env else repo_root() / MVK_DEFAULT).resolve()


def profile_path() -> Path:
    """The option profile: ``LAZ_PROFILE``, else ``<root>/host/options-default.txt``."""
    env = os.environ.get("LAZ_PROFILE")
    return (Path(env) if env else repo_root() / "host" / "options-default.txt").resolve()
