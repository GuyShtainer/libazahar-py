"""A stand-in worker for the ``_client.py`` tests. Run as: fakeworker.py <mode> <fd> <map> <pkg_parent>.

Modes: ok, exit10, exit11, segv, hang, eof, die_at_start. It speaks the real protocol (hello first, then
(op, args) requests, replies ("ok", payload)) and keeps a small ``host.map`` at the real offsets.
"""
import mmap
import os
import signal
import struct
import sys
import time

MODE, FD, MAP_PATH, PKG = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
sys.path.insert(0, PKG)
if sys.platform == "win32":
    import ctypes
    from multiprocessing.connection import PipeConnection as Connection  # noqa: E402

    ctypes.WinDLL("kernel32").SetErrorMode(0x8003)      # a crash ends the process at once: no WER box
else:
    from multiprocessing.connection import Connection  # noqa: E402

from libazahar import _map  # noqa: E402


def open_map():
    """Create a full-size map with the magic; returns the writable mmap."""
    with open(MAP_PATH, "wb") as handle:
        handle.truncate(_map.SIZE)
    handle = open(MAP_PATH, "r+b")
    view = mmap.mmap(handle.fileno(), 0)
    view[:8] = _map.MAGIC
    struct.pack_into("<I", view, _map.PID, os.getpid())
    return view


def put(view, fmt, offset, value):
    struct.pack_into(fmt, view, offset, value)


def message(view, text):
    raw = text.encode()
    view[_map.MSG:_map.MSG + len(raw)] = raw
    put(view, "<I", _map.MSG_LEN, len(raw))


def sidecar(name):
    with open(MAP_PATH + "." + name, "w") as handle:
        handle.write(repr(time.time()))


def beat(view):
    (value,) = struct.unpack_from("<Q", view, _map.HEARTBEAT)
    put(view, "<Q", _map.HEARTBEAT, value + 1)


def frames_total(view):
    return struct.unpack_from("<q", view, _map.FRAME_TOTAL)[0]


def handle_run(view, conn):
    total = frames_total(view)
    if MODE == "exit10":
        put(view, "<q", _map.FRAME_TOTAL, total + 7)
        message(view, "boom")
        put(view, "<i", _map.EXIT_CODE, 10)
        os._exit(10)
    if MODE == "exit11":
        message(view, "Fatal Error encountered (14)")
        os._exit(11)
    if MODE == "segv":
        sidecar("died")
        if sys.platform == "win32":
            # ctypes turns a real access violation into a Python exception, so end the process with that NTSTATUS
            kernel32 = ctypes.WinDLL("kernel32")
            kernel32.GetCurrentProcess.restype = ctypes.c_void_p
            kernel32.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint]
            kernel32.TerminateProcess(kernel32.GetCurrentProcess(), 0xC0000005)
        else:
            os.kill(os.getpid(), signal.SIGSEGV)
        time.sleep(30)
    if MODE == "hang":
        for _ in range(5):
            beat(view)
            time.sleep(0.1)
        sidecar("stopped")
        time.sleep(3600)
    if MODE == "eof":
        conn.close()
        os._exit(0)
    beat(view)
    put(view, "<q", _map.FRAME_TOTAL, total + 5)
    return b"result"


def main():
    if MODE == "die_at_start":
        os._exit(3)
    view = open_map()
    conn = Connection(FD)
    conn.send(("hello", 0))
    for _ in range(1 << 20):
        try:
            op, args = conn.recv()
        except EOFError:
            return 0
        if op == "run":
            reply = handle_run(view, conn)
        elif op == "save_state" and MODE == "exit10":
            message(view, "exiting during the drain")
            os._exit(10)
        elif op == "echo":
            reply = args
        else:
            reply = None
        conn.send(("ok", reply))
        if op == "close":
            return 0
    return 1


sys.exit(main())
