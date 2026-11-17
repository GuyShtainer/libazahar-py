"""pytest setup: import paths, the skip-or-fail rule (LAZ_REQUIRE_EMULATOR), and per-test work folders."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Callable, NamedTuple

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


# The skip messages of every core, host or emulator fixture start with this, and the tests that use those fixtures carry
# the needs_core marker (set below). tools/skips_check.py allows exactly such skips in the fast tier.
NEEDS_CORE = "needs_core: "
CORE_FIXTURES = {"host_lib", "host_paths", "stock_core", "lazpy_core"}


def pytest_collection_modifyitems(items: list) -> None:
    """Mark every test that asks for a core, host or emulator fixture with ``needs_core``."""
    for item in items:
        if CORE_FIXTURES & set(getattr(item, "fixturenames", ())):
            item.add_marker(pytest.mark.needs_core)


def _missing(what: Path, why: str) -> None:
    text = f"{what} is missing ({why})"
    if os.environ.get("LAZ_REQUIRE_EMULATOR") == "1":
        pytest.fail(text)
    pytest.skip(NEEDS_CORE + text)


@pytest.fixture(scope="session")
def host_lib() -> Path:
    """build/libazhost<suffix> (skip, or fail under LAZ_REQUIRE_EMULATOR=1, when it is not built)."""
    from libazahar import _paths
    path = REPO / "build" / f"libazhost{_paths.SUFFIX}"
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
        _missing(core, "run tools/fetch.sh --lazpy-core or set LAZ_CORE")
    if not app.is_file():
        _missing(app, "run make testapp")
    return HostPaths(host_lib, core, app)


def _stock_core_path() -> Path:
    """``LAZ_STOCK_CORE`` as a path; skip when unset (always, even under LAZ_REQUIRE_EMULATOR=1: the stock core is
    never required); a failure under LAZ_REQUIRE_EMULATOR=1 when it names no file."""
    env = os.environ.get("LAZ_STOCK_CORE")
    if not env:
        pytest.skip(NEEDS_CORE + "set LAZ_STOCK_CORE to Azahar's own core to compare cores")
    core = Path(env)
    if not core.is_file():
        _missing(core, "LAZ_STOCK_CORE names no file")
    return core


@pytest.fixture(scope="session")
def stock_core() -> Path:
    """Azahar's own core, only when ``LAZ_STOCK_CORE`` names it (tests that compare cores; otherwise they skip)."""
    return _stock_core_path()


@pytest.fixture(scope="session")
def lazpy_core() -> Path:
    """Our patched core: ``LAZ_CORE`` when it names one, else build-core/ under the repo, else dl/lazpy-core/."""
    from libazahar import _paths
    chosen = _paths.core_path()
    candidates = [chosen] if _kind(chosen) == "lazpy" else []
    name = f"azahar_lazpy_libretro{_paths.SUFFIX}"
    candidates += [REPO / "build-core" / name, REPO / "dl" / "lazpy-core" / name]
    core = next((c for c in candidates if c.is_file()), candidates[0])
    if not core.is_file():
        _missing(core, "run tools/fetch.sh --lazpy-core, build our core or set LAZ_CORE")
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
