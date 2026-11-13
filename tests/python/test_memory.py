"""Guest memory API without an emulator: widths, argument checks, watch shape, WatchRow, watch_copy, ABI 3 layout."""
import ctypes
import struct

import pytest

from libazahar import _abi, _map
from libazahar.emulator import Emulator
from libazahar.errors import GuestMemoryError, HostError, from_code
from libazahar.memory import Memory
from libazahar.results import WatchRow


class Fake:
    """A stand-in transport: a dict of bytes at addresses; records the calls."""

    def __init__(self):
        self.calls = []
        self.fail = None

    def __call__(self, op, args):
        self.calls.append((op, args))
        if self.fail is not None:
            raise self.fail
        if op == "read":
            return bytes(range(args[1] % 256)) if args[1] < 256 else bytes(args[1])
        return None


@pytest.fixture
def mem():
    fake = Fake()
    memory = Memory(fake)
    memory.fake = fake
    return memory


def test_width_round_trips(mem):
    mem.u16.raw_write(0x100, 0xBEEF)
    assert mem.fake.calls[-1] == ("write", (0x100, b"\xef\xbe"))
    mem.s8.raw_write(0x101, -1)
    assert mem.fake.calls[-1] == ("write", (0x101, b"\xff"))
    mem.u64.raw_write(0x102, (1 << 64) - 1)
    assert mem.fake.calls[-1][1][1] == b"\xff" * 8
    mem.write_u32(0x104, 0x01020304)
    assert mem.fake.calls[-1][1][1] == b"\x04\x03\x02\x01"
    mem.fake.calls.clear()
    assert mem.u32(0x10) == struct.unpack("<I", bytes(range(4)))[0]
    assert mem.s8.raw_read(0x10) == 0 and mem.u8(0x10) == 0
    assert mem.fake.calls[0] == ("read", (0x10, 4))


@pytest.mark.parametrize("name,value", [("u8", 256), ("u8", -1), ("s8", 128), ("s8", -129), ("u16", 1 << 16),
                                        ("u32", 1 << 32), ("u64", 1 << 64), ("s64", 1 << 63), ("u32", True),
                                        ("u32", 1.5)])
def test_write_range_checks(mem, name, value):
    with pytest.raises(ValueError):
        mem.widths[name].raw_write(0x100, value)
    assert not mem.fake.calls


@pytest.mark.parametrize("addr,length", [(-1, 4), (1 << 32, 4), (0x100, 0), (0x100, -3),
                                         (0x100, _abi.AZH_MEM_MAX_LEN + 1), (0xFFFFFFFC, 8), (0xFFFFFFFF, 2),
                                         (1.5, 4), (True, 4)])
def test_read_argument_checks(mem, addr, length):
    with pytest.raises(ValueError):
        mem.read(addr, length)
    assert not mem.fake.calls


def test_write_argument_checks(mem):
    with pytest.raises(ValueError):
        mem.write(0x100, b"")
    with pytest.raises(ValueError):
        mem.write(0xFFFFFFFC, bytes(8))
    with pytest.raises(ValueError):
        mem.write(-1, b"x")
    calls = len(mem.fake.calls)
    with pytest.raises(TypeError):
        mem.write(0x100, 5)
    assert len(mem.fake.calls) == calls
    mem.write(0xFFFFFFFC, bytes(4))
    mem.write(0x10, memoryview(b"ab"))
    assert mem.fake.calls[-1] == ("write", (0x10, b"ab"))


def test_guest_memory_error_gets_the_request(mem):
    mem.fake.fail = GuestMemoryError("unmapped")
    with pytest.raises(GuestMemoryError) as info:
        mem.read(0x1234, 16)
    assert info.value.addr == 0x1234 and info.value.length == 16
    with pytest.raises(GuestMemoryError) as info:
        mem.write(0x2000, b"abc")
    assert (info.value.addr, info.value.length) == (0x2000, 3)


def test_from_code_unmapped():
    err = from_code(_abi.AZH_E_UNMAPPED, "a page is unmapped")
    assert isinstance(err, GuestMemoryError) and not isinstance(err, ValueError)
    assert err.addr is None and err.length is None


def test_watch_shape_checks():
    batch = _abi.Batch()
    fill = Emulator._fill_watch
    assert fill(batch, None, 1) == [] and batch.n_watch == 0
    assert fill(batch, [(0x1000, 8), (0x2000, 2)], 10) == [8, 2]
    assert batch.n_watch == 2 and batch.watch_every == 10 and batch.watch[1].addr == 0x2000
    for bad in ([5], [(1, 2, 3)], [("a", 1)], [(1, 1.5)], [(-1, 1)], [(1, True)], [(1 << 32, 1)], 7 * [None]):
        with pytest.raises(ValueError):
            fill(_abi.Batch(), bad, 1)
    with pytest.raises(ValueError):
        fill(_abi.Batch(), [(0, 1)] * 33, 1)
    with pytest.raises(ValueError):
        fill(_abi.Batch(), [(0, 1)], -1)
    with pytest.raises(ValueError):
        fill(_abi.Batch(), [(0, 1)], 1.5)
    assert fill(_abi.Batch(), [(0, 1)] * 32, 0) == [1] * 32          # the host's plan decides word counts and size


def test_watch_row_u32():
    row = WatchRow(7, 0, (struct.pack("<II", 5, 6), struct.pack("<I", 9)))
    assert row.u32(0) == 5 and row.u32(0, 1) == 6 and row.u32(1) == 9
    with pytest.raises(struct.error):
        row.u32(1, 1)


def fake_map(path, rows, row_bytes, words=0, size=_map.SIZE):
    buf = bytearray(size)
    buf[:8] = _map.MAGIC
    struct.pack_into("<I", buf, _map.WATCH_ROWS, rows)
    struct.pack_into("<I", buf, _map.WATCH_ROW_BYTES, row_bytes)
    struct.pack_into("<I", buf, _map.WATCH_WORDS, words)
    for index in range(rows):
        base = _map.WATCH_DATA + index * row_bytes
        if base + row_bytes > size:
            break
        struct.pack_into("<qiI", buf, base, 100 + index, 0, 0)
        buf[base + 16:base + row_bytes] = bytes([index & 255]) * (row_bytes - 16)
    path.write_bytes(bytes(buf))
    return _map.HostMap(path)


def test_watch_copy(tmp_path):
    host = fake_map(tmp_path / "m", 3, 48)
    assert host.valid()
    got = host.watch_copy(3)
    assert [g[0] for g in got] == [100, 101, 102] and got[2][2] == bytes([2]) * 32 and got[1][1] == 0
    assert host.watch_copy(0) == [] and len(host.watch_copy(1)) == 1
    with pytest.raises(HostError):
        host.watch_copy(4)                    # the map holds only 3
    host.close()


def test_watch_copy_refuses_rows_past_the_area(tmp_path):
    size = _map.WATCH_DATA + _map.WATCH_MIN_DATA + 100          # a small file: the area is what the file holds
    host = fake_map(tmp_path / "m", 1000, 4096, size=size)
    assert host.valid() and host.watch_area() == _map.WATCH_MIN_DATA + 100
    with pytest.raises(HostError, match="pass the end"):
        host.watch_copy(1000)
    assert len(host.watch_copy(8)) == 8
    host.close()


@pytest.fixture(scope="module")
def layout(host_lib):
    lib = ctypes.CDLL(str(host_lib))
    lib.azh_abi_layout.argtypes = [ctypes.POINTER(_abi.Layout)]
    out = _abi.Layout()
    assert lib.azh_abi_layout(ctypes.byref(out)) == 0
    return out


def row_of(layout, name):
    for index in range(layout.n_fields):
        if layout.fields[index].name.decode() == name:
            return layout.fields[index]
    raise KeyError(name)


def test_layout_is_abi_4(layout):
    _abi.check_layout(layout)
    assert layout.abi == 4 and layout.size_batch == 3612 and layout.size_result == 312
    assert layout.n_fields == 150 and layout.map_size == 4890624


def test_smaller_watch_area_with_matching_map_size_is_accepted(layout):
    bad = _abi.Layout.from_buffer_copy(layout)
    data = row_of(bad, "map.watch_data")
    data.size = 2 * 1024 * 1024 - 64
    row_of(bad, "map.__size__").size = data.offset + data.size
    row_of(bad, "const.AZH_WATCH_AREA_BYTES").offset = data.offset + data.size - 696320
    _abi.check_layout(bad)


def test_moved_watch_data_offset_is_refused(layout):
    bad = _abi.Layout.from_buffer_copy(layout)
    row_of(bad, "map.watch_data").offset += 64
    with pytest.raises(HostError, match="map.watch_data"):
        _abi.check_layout(bad)


def test_watch_area_too_small_for_one_row_is_refused(layout):
    bad = _abi.Layout.from_buffer_copy(layout)
    data = row_of(bad, "map.watch_data")
    data.size = 1000
    row_of(bad, "map.__size__").size = data.offset + data.size
    with pytest.raises(HostError, match="map.watch_data"):
        _abi.check_layout(bad)


def test_map_size_that_is_not_offset_plus_size_is_refused(layout):
    bad = _abi.Layout.from_buffer_copy(layout)
    row_of(bad, "map.__size__").size += 4096
    with pytest.raises(HostError, match="map.__size__"):
        _abi.check_layout(bad)
