"""The ctypes layout check against the built host's azh_abi_layout (loads the dylib, calls only that one function)."""
import ctypes

import pytest

from libazahar import _abi, _map
from libazahar.errors import HostError


@pytest.fixture(scope="module")
def layout(host_lib):
    lib = ctypes.CDLL(str(host_lib))
    lib.azh_abi_layout.argtypes = [ctypes.POINTER(_abi.Layout)]
    out = _abi.Layout()
    assert lib.azh_abi_layout(ctypes.byref(out)) == 0
    return out


def copy(layout):
    return _abi.Layout.from_buffer_copy(layout)


def test_passes(layout):
    _abi.check_layout(layout)
    assert layout.size_layout == ctypes.sizeof(_abi.Layout) and layout.n_fields > 100


def test_wrong_size_layout_is_caught_before_rows(layout):
    bad = copy(layout)
    bad.size_layout += 8
    bad.fields[0].offset = 999          # a row error that must not be reached first
    with pytest.raises(HostError, match="size_layout"):
        _abi.check_layout(bad)


def test_wrong_abi(layout):
    bad = copy(layout)
    bad.abi = 3                          # the host before thread registers
    with pytest.raises(HostError, match="abi"):
        _abi.check_layout(bad)


def test_moved_batch_field(layout):
    fields = list(_abi.Batch._fields_)
    fields.insert(0, fields.pop([name for name, _ in fields].index("sd_every")))
    moved = type("MovedBatch", (ctypes.Structure,), {"_fields_": fields})
    with pytest.raises(HostError, match="batch"):
        _abi.check_layout(layout, structs={"batch": moved})


def test_changed_map_constant(layout, monkeypatch):
    monkeypatch.setattr(_map, "HEARTBEAT", _map.HEARTBEAT + 1)
    with pytest.raises(HostError, match="map.heartbeat"):
        _abi.check_layout(layout)


def test_changed_abi_constant(layout, monkeypatch):
    monkeypatch.setattr(_abi, "AZH_CIRCLE_MAX", 32766)
    with pytest.raises(HostError, match="const.AZH_CIRCLE_MAX"):
        _abi.check_layout(layout)


def test_row_unknown_to_python(layout):
    bad = copy(layout)
    bad.fields[bad.n_fields - 1].name = b"const.AZH_NOPE"
    with pytest.raises(HostError, match="unknown to _abi.py"):
        _abi.check_layout(bad)
