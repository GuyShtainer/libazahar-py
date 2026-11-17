"""P17: our core is the default core; the stock core is opt-in through LAZ_STOCK_CORE. No emulator needed."""
from __future__ import annotations

import pytest

import conftest
from libazahar import _paths


def test_default_core_is_ours(monkeypatch):
    monkeypatch.delenv("LAZ_CORE", raising=False)
    assert _paths.core_path().parts[-3:] == ("dl", "lazpy-core", f"azahar_lazpy_libretro{_paths.SUFFIX}")


def test_laz_core_wins(monkeypatch, tmp_path):
    mine = tmp_path / "some_core.dylib"
    monkeypatch.setenv("LAZ_CORE", str(mine))
    assert _paths.core_path() == mine.resolve()


@pytest.mark.parametrize("require", ["1", "0"])
def test_stock_core_skips_without_laz_stock_core(monkeypatch, require):
    monkeypatch.delenv("LAZ_STOCK_CORE", raising=False)
    monkeypatch.setenv("LAZ_REQUIRE_EMULATOR", require)
    with pytest.raises(pytest.skip.Exception):
        conftest._stock_core_path()


def test_stock_core_naming_no_file(monkeypatch, tmp_path):
    monkeypatch.setenv("LAZ_STOCK_CORE", str(tmp_path / "nope.dylib"))
    monkeypatch.setenv("LAZ_REQUIRE_EMULATOR", "1")
    with pytest.raises(pytest.fail.Exception):
        conftest._stock_core_path()
    monkeypatch.setenv("LAZ_REQUIRE_EMULATOR", "0")
    with pytest.raises(pytest.skip.Exception):
        conftest._stock_core_path()


def test_stock_core_path_when_set(monkeypatch, tmp_path):
    core = tmp_path / "stock.dylib"
    core.write_bytes(b"x")
    monkeypatch.setenv("LAZ_STOCK_CORE", str(core))
    assert conftest._stock_core_path() == core
