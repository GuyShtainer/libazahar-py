"""Windows only: azhost.exe loads a core named by a relative path (P7-R1-4), the host DLL sits where Python looks for it
(B5), and the export-table reader finds the host's exports. No core is needed: our own host DLL stands in for the core,
so the load succeeds and azhost then names the first retro_* symbol it cannot find."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from libazahar import _paths
from test_threads_live import pe_exports

REPO = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows only: the LoadLibrary rules")


def _build() -> Path:
    exe, dll = REPO / "build" / "azhost.exe", REPO / "build" / "libazhost.dll"
    for path in (exe, dll):
        if not path.is_file():
            pytest.skip(f"needs_core: {path.name} is missing (run make)")
    return exe


def _run(exe: Path, cwd: Path, *more: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "LAZ_CORE"}
    return subprocess.run([str(exe), "run", "x.3dsx", "--sys", "sys", "--out", "out", "--frames", "1", *more],
                          cwd=cwd, env=env, capture_output=True, text=True, timeout=60)


def _stand_in(folder: Path, name: str) -> None:
    target = folder / "dl" / "lazpy-core"
    target.mkdir(parents=True)
    shutil.copyfile(REPO / "build" / "libazhost.dll", target / name)


def test_default_relative_core_loads(tmp_path: Path):
    exe = _build()
    _stand_in(tmp_path, "azahar_lazpy_libretro.dll")
    res = _run(exe, tmp_path)
    assert "Windows error 87" not in res.stderr, res.stderr
    assert "missing symbol retro_api_version" in res.stderr, res.stderr


def test_relative_core_argument_loads(tmp_path: Path):
    exe = _build()
    _stand_in(tmp_path, "other_core.dll")
    res = _run(exe, tmp_path, "--core", "dl/lazpy-core/other_core.dll")
    assert "Windows error 87" not in res.stderr, res.stderr
    assert "missing symbol retro_api_version" in res.stderr, res.stderr


def test_host_dll_is_where_python_looks(monkeypatch):
    _build()
    monkeypatch.delenv("LAZ_HOST", raising=False)
    assert _paths.host_path() == (REPO / "build" / "libazhost.dll").resolve()


def test_pe_exports_reads_the_host_dll():
    _build()
    names = pe_exports(REPO / "build" / "libazhost.dll")
    assert {"azh_open", "azh_close", "azh_boot", "azh_run"} <= names
    assert "retro_api_version" not in names
