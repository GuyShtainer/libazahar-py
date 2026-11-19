"""The audio plumbing in Python, with no emulator: the sample forms, the capture file's guard, the worker's call order
and the request the Emulator sends. The live check on the tone app is test_audio_live.py."""
from __future__ import annotations

import ctypes
import struct
import sys
from array import array

import pytest

from libazahar import _abi, _worker, emulator
from libazahar.emulator import Emulator, _samples, _take
from libazahar.errors import HostError
from libazahar.inputs import Held

PAIRS = [(1, -1), (300, -300), (32767, -32768)]
RAW = b"".join(struct.pack("<hh", left, right) for left, right in PAIRS)


@pytest.fixture
def no_numpy(monkeypatch):
    monkeypatch.setitem(sys.modules, "numpy", None)      # `import numpy` now raises ImportError


def test_samples_numpy_form():
    np = pytest.importorskip("numpy")
    out = _samples(RAW)
    assert isinstance(out, np.ndarray) and out.shape == (3, 2) and out.dtype == np.dtype("=i2")
    assert out.tolist() == [list(pair) for pair in PAIRS]


def test_samples_fallback_form(no_numpy):
    out = _samples(RAW)
    assert isinstance(out, array) and out.typecode == "h"
    assert list(out) == [v for pair in PAIRS for v in pair]


def test_samples_fallback_swaps_on_a_big_endian_machine(no_numpy, monkeypatch):
    native_is_little = sys.byteorder == "little"
    monkeypatch.setattr(emulator.sys, "byteorder", "big")
    out = _samples(RAW)
    if native_is_little:        # the branch ran on a little-endian machine: every value came back byte-swapped
        assert list(out) == [struct.unpack("<h", struct.pack(">h", v))[0] for pair in PAIRS for v in pair]


def test_empty_capture_is_an_empty_array(no_numpy):
    assert len(_samples(b"")) == 0


@pytest.mark.parametrize("numpy_present", [True, False])
def test_take_reads_and_removes_the_file(tmp_path, monkeypatch, numpy_present):
    if numpy_present:
        pytest.importorskip("numpy")
    else:
        monkeypatch.setitem(sys.modules, "numpy", None)
    path = tmp_path / "audio.raw"
    path.write_bytes(RAW)
    out = _take(path, len(PAIRS))
    assert [int(v) for v in list(out.reshape(-1) if hasattr(out, "reshape") else out)] == [v for p in PAIRS for v in p]
    assert not path.exists()


@pytest.mark.parametrize("claimed", [2, 4])
def test_take_refuses_a_count_that_disagrees_with_the_file(tmp_path, claimed):
    path = tmp_path / "audio.raw"
    path.write_bytes(RAW)
    with pytest.raises(HostError, match="host counted"):
        _take(path, claimed)
    assert not path.exists()


def test_take_missing_file_is_a_host_error(tmp_path):
    with pytest.raises(HostError, match="cannot read the audio file"):
        _take(tmp_path / "nothing.raw", 0)


class FakeLib:
    """Stands in for the loaded host: records the calls and answers like a host that ran ``frames`` stereo frames."""

    def __init__(self, run_rc=0):
        self.calls = []
        self.run_rc = run_rc

    def azh_audio_capture(self, path):
        self.calls.append(("capture", path))
        return 0

    def azh_run(self, records, count, batch, result):
        self.calls.append(("run", count))
        return self.run_rc

    def azh_audio_info(self, frames, rate):
        self.calls.append(("info",))
        frames._obj.value, rate._obj.value = 1234, 32728
        return 0

    def azh_error(self):
        return b"refused"


def run_args(*extra):
    return (b"", bytes(_abi.Batch())) + extra


def test_op_run_with_audio_arms_runs_reads_and_disarms():
    lib = FakeLib()
    reply = _worker._op_run(lib, run_args("a.raw"))
    assert [c[0] for c in lib.calls] == ["capture", "run", "info", "capture"]
    assert lib.calls[0] == ("capture", b"a.raw") and lib.calls[-1] == ("capture", None)
    result_bytes, frames, rate = reply
    assert (frames, rate) == (1234, 32728) and len(result_bytes) == ctypes.sizeof(_abi.Result)


def test_op_run_disarms_when_the_run_fails():
    lib = FakeLib(run_rc=-3)
    with pytest.raises(Exception):
        _worker._op_run(lib, run_args("a.raw"))
    assert [c[0] for c in lib.calls] == ["capture", "run", "capture"] and lib.calls[-1] == ("capture", None)


def test_op_run_without_audio_touches_no_audio_call():
    lib = FakeLib()
    reply = _worker._op_run(lib, run_args())
    assert [c[0] for c in lib.calls] == ["run"] and isinstance(reply, bytes)


class FakeClient:
    """Records the requests an Emulator sends and replies with a zero Result (and a capture file when asked)."""

    closed = False
    final_frame_total = 0

    def __init__(self, error=None):
        self.requests = []
        self.error = error

    def host_map(self):
        return None

    def annotate(self, exc):
        return exc

    def request(self, op, args, wait, frame_before=0):
        self.requests.append((op, args))
        if self.error is not None:
            raise self.error
        result = bytes(_abi.Result())
        if len(args) == 3:
            open(args[2], "wb").write(RAW)
            return "ok", (result, len(PAIRS), 32728)
        return "ok", result


def make_emulator(tmp_path, client):
    emu = object.__new__(Emulator)
    emu.timeout, emu.boot_timeout = 30.0, 300.0
    emu._workdir, emu._shots_dir = tmp_path, tmp_path / "shots"
    emu._held, emu._client = Held(), client
    return emu


def test_run_without_audio_sends_exactly_two_arguments(tmp_path):
    client = FakeClient()
    result = make_emulator(tmp_path, client).run(3)
    (op, args), = client.requests
    assert op == "run" and len(args) == 2
    assert result.audio is None and result.audio_rate == 0


def test_run_with_audio_sends_the_path_and_returns_the_samples(tmp_path):
    client = FakeClient()
    result = make_emulator(tmp_path, client).run(3, audio=True)
    (op, args), = client.requests
    assert len(args) == 3 and args[2] == str(tmp_path / "audio.raw")
    assert result.audio_rate == 32728 and len(result.audio) == len(PAIRS)
    assert not (tmp_path / "audio.raw").exists()


def test_a_failed_batch_leaves_no_capture_file(tmp_path):
    (tmp_path / "audio.raw").write_bytes(RAW)             # what a refused batch could leave behind
    client = FakeClient(error=HostError("the host refused the batch"))
    with pytest.raises(HostError, match="refused"):
        make_emulator(tmp_path, client).run(3, audio=True)
    assert not (tmp_path / "audio.raw").exists()
