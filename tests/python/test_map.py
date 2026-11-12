"""HostMap against a synthetic host.map (no emulator)."""
import struct

import numpy as np
import pytest

from libazahar import _map


def make_map(path, **values):
    buf = bytearray(_map.SIZE)
    buf[:8] = _map.MAGIC
    struct.pack_into("<Q", buf, _map.HEARTBEAT, values.get("heartbeat", 0))
    struct.pack_into("<i", buf, _map.STOP_CODE, values.get("stop", 0))
    text = values.get("message", "").encode()
    buf[_map.MSG:_map.MSG + len(text)] = text
    struct.pack_into("<I", buf, _map.MSG_LEN, len(text))
    struct.pack_into("<q", buf, _map.PX_FRAME, values.get("px_frame", -1))
    struct.pack_into("<q", buf, _map.FRAME_TOTAL, values.get("frame_total", 0))
    struct.pack_into("<q", buf, _map.VBLANKS_TOTAL, values.get("vblanks", 0))
    struct.pack_into("<I", buf, _map.MSG_SEQ, 3)
    struct.pack_into("<I", buf, _map.PID, 4242)
    struct.pack_into("<i", buf, _map.EXIT_CODE, values.get("exit", 0))
    buf[_map.PIXELS] = 9
    buf[_map.PIXELS + _map.TOP_BYTES] = 7
    path.write_bytes(bytes(buf))


def test_every_reader(tmp_path):
    path = tmp_path / "host.map"
    make_map(path, heartbeat=77, stop=3, message="hello", px_frame=12, frame_total=1234, vblanks=999, exit=10)
    host = _map.HostMap(path)
    assert host.valid() and host.heartbeat() == 77 and host.stop_code() == 3 and host.message() == "hello"
    assert host.frame_total() == 1234 and host.vblanks_total() == 999 and host.exit_code() == 10
    assert host.px_frame() == 12 and host.pid() == 4242 and host.msg_seq() == 3
    assert host.pixels(1)[0] == 9 and host.pixels(2)[0] == 7
    assert len(host.pixels(1)) == 400 * 240 * 4 and len(host.pixels(2)) == 320 * 240 * 4
    host.close()


def test_zero_file_is_not_valid(tmp_path):
    path = tmp_path / "host.map"
    path.write_bytes(bytes(_map.SIZE))
    host = _map.HostMap(path)
    assert not host.valid()
    host.close()


def test_close_with_live_view_does_not_raise(tmp_path):
    path = tmp_path / "host.map"
    make_map(path)
    host = _map.HostMap(path)
    view = host.pixels(1)
    array = np.frombuffer(view, dtype=np.uint8)
    host.close()
    host.close()
    assert array[0] == 9
    with pytest.raises(ValueError):
        host.pixels(3)
