"""pytest setup: import paths, the skip-or-fail rule (LAZ_REQUIRE_EMULATOR), and per-test work folders."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Callable, Dict, NamedTuple

import pytest

REPO = Path(__file__).resolve().parents[2]
for _folder in (REPO / "python", REPO / "tests", Path(__file__).resolve().parent):   # before any import of the package
    if str(_folder) not in sys.path:
        sys.path.insert(0, str(_folder))


class HostPaths(NamedTuple):
    """The files an emulator test needs."""

    host: Path
    core: Path
    app: Path


def _missing(what: Path, why: str) -> None:
    text = f"{what} is missing ({why})"
    if os.environ.get("LAZ_REQUIRE_EMULATOR") == "1":
        pytest.fail(text)
    pytest.skip(text)


@pytest.fixture(scope="session")
def host_lib() -> Path:
    """build/libazhost.dylib (skip, or fail under LAZ_REQUIRE_EMULATOR=1, when it is not built)."""
    path = REPO / "build" / "libazhost.dylib"
    if not path.is_file():
        _missing(path, "run make")
    return path


def _kind(core: Path) -> str:
    """``lazpy`` for our patched core (its file name says so), else ``stock``."""
    return "lazpy" if "lazpy" in core.name else "stock"


def pytest_report_header(config: pytest.Config) -> str:
    """One line at session start: the core the default tests use."""
    from libazahar import _paths
    core = _paths.core_path()
    return f"core={core} kind={_kind(core)}"


@pytest.fixture(scope="session")
def host_paths(host_lib: Path) -> HostPaths:
    """The host library, the core (``LAZ_CORE`` wins) and the test app (skip, or fail under LAZ_REQUIRE_EMULATOR=1)."""
    from libazahar import _paths
    core = _paths.core_path()
    app = REPO / "build" / "testapp.3dsx"
    if not core.is_file():
        _missing(core, "run tools/fetch.sh or set LAZ_CORE")
    if not app.is_file():
        _missing(app, "run make testapp")
    return HostPaths(host_lib, core, app)


@pytest.fixture(scope="session")
def stock_core() -> Path:
    """The stock core (the default path under the repo), for tests that need it whatever ``LAZ_CORE`` says."""
    core = REPO / "dl" / "azahar" / "azahar_libretro.dylib"
    if not core.is_file():
        _missing(core, "run tools/fetch.sh")
    return core


@pytest.fixture(scope="session")
def lazpy_core() -> Path:
    """Our patched core: ``LAZ_CORE`` when it names one, else build-core/ under the repo."""
    from libazahar import _paths
    chosen = _paths.core_path()
    core = chosen if _kind(chosen) == "lazpy" else REPO / "build-core" / "azahar_lazpy_libretro.dylib"
    if not core.is_file():
        _missing(core, "build our core or set LAZ_CORE")
    return core


@pytest.fixture
def workdir(request: pytest.FixtureRequest) -> Path:
    """A fresh ``runs/d-pytest/<test name>/``."""
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", request.node.name)
    path = REPO / "runs" / "d-pytest" / name
    if path.exists():
        import shutil
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


@pytest.fixture
def seed(workdir: Path) -> Callable[..., Path]:
    """Build an SD seed folder holding the test app's control file (needs ``testapp_log`` from step C)."""
    def make(**control_keys: object) -> Path:
        import testapp_log
        folder = workdir / "seed"
        testapp_log.write_control(folder, **control_keys)
        return folder
    return make


@pytest.fixture
def repo_root() -> Path:
    """The repo root."""
    return REPO


def pytest_collection_modifyitems(items: list) -> None:
    """Nothing is skipped here: slow tests are selected with -m."""
    _: Dict[str, int] = {}
    assert _ == {}
