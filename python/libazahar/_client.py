"""The parent side of one worker process: spawn, request, wait loop, death mapping, close.

Knows nothing about frames or inputs, so the pure tests drive it with a fake worker
(docs/plans/phase-d.md 4.2 to 4.4).
"""
from __future__ import annotations

import multiprocessing
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from . import _abi, _map, _slots
from .errors import GuestError, HostCrashed, HostError, HostTimeout, from_code

__all__ = ["Wait", "WorkerClient", "worker_argv", "tail_lines"]

POLL_S = 0.1
MAX_POLLS = 10 ** 9
REAP_S = 5.0
TAIL_LINES = 20
_WORKER_SNIPPET = ("import sys; sys.path.insert(0, sys.argv[2]); from libazahar._worker import main; "
                   "sys.exit(main(int(sys.argv[1])))")


@dataclass(frozen=True)
class Wait:
    """Limits of one request: ``total`` wall seconds, or a heartbeat watch (``heartbeat`` seconds without a change
    once the heartbeat has moved since start, ``first_heartbeat`` before that)."""

    total: Optional[float] = None
    heartbeat: Optional[float] = None
    first_heartbeat: Optional[float] = None


def worker_argv(child_fd: int, pkg_parent: Path) -> List[str]:
    """argv of the real worker: ``python -I -c`` with an explicit package root (docs/plans/phase-2.md P3)."""
    return [sys.executable, "-I", "-c", _WORKER_SNIPPET, str(child_fd), str(pkg_parent)]


def tail_lines(path: Path, count: int = TAIL_LINES) -> str:
    """The last ``count`` lines of a text file, or an empty string when it is not there."""
    try:
        data = Path(path).read_bytes()[-65536:]
    except OSError:
        return ""
    return "\n".join(data.decode("utf-8", "replace").splitlines()[-count:])


class WorkerClient:
    """One worker process and its pipe. ``request`` returns ``("ok", payload)`` or, when the guest exited during a
    ``run``, ``("exited", info)``; every other outcome raises a LibAzaharError.

    ``slot`` (step E): ``None`` takes a machine-wide slot (``_slots.acquire``) only for the real worker (``argv`` is
    None); ``True`` takes one for a fake worker too; ``False`` never does. So the pure tests, which pass no keyword,
    never touch the real slot folder or the cap. The worker inherits the slot's lock fd (``pass_fds``; its number is
    ``argv[3]``) and the parent closes its copy right after ``Popen``: the slot is free the moment the worker dies,
    however it dies; the parent never holds a lock, so a parent killed with SIGKILL leaks nothing; ``close()`` frees
    the slot by reaping the worker. ``<workdir>/slot.txt`` records the slot after ``Popen``."""

    def __init__(self, workdir: Path, map_path: Path, log_path: Path, env: Dict[str, str],
                 argv: Optional[Callable[[int], List[str]]] = None, slot: Optional[bool] = None) -> None:
        self.workdir = Path(workdir)
        self.map_path = Path(map_path)
        self.log_path = Path(log_path)
        self.err_path = self.workdir / "worker.err"
        self._env = dict(env)
        self._argv = argv
        self._take_slot = (argv is None) if slot is None else bool(slot)
        self._proc: Optional[subprocess.Popen] = None
        self._conn: Optional[Connection] = None
        self._map: Optional[_map.HostMap] = None
        self._map_closed = False
        self.final_frame_total = 0          # the map's frame count, kept when close() unmaps it
        self._hb_base = 0
        self._hb_moved = False
        self.closed = False

    # ---- state ----
    @property
    def proc(self) -> Optional[subprocess.Popen]:
        """The worker's Popen (for finalizers)."""
        return self._proc

    @property
    def pid(self) -> int:
        """The worker's pid (0 before spawn)."""
        return self._proc.pid if self._proc is not None else 0

    def host_map(self) -> Optional[_map.HostMap]:
        """The worker's map once it exists and is valid, else None."""
        if self._map is None and not self._map_closed and self.map_path.is_file():
            try:
                candidate = _map.HostMap(self.map_path)
            except (OSError, ValueError):
                return None
            if candidate.valid():
                self._map = candidate
            else:
                candidate.close()
        return self._map

    def _heartbeat(self) -> int:
        hostmap = self.host_map()
        return hostmap.heartbeat() if hostmap is not None else 0

    def _message(self) -> Optional[str]:
        hostmap = self.host_map()
        return (hostmap.message() or None) if hostmap is not None else None

    # ---- spawn ----
    def spawn(self, boot_timeout: float) -> None:
        """Start the worker and wait for its hello. Raises HostError (the worker's fatal text) or HostCrashed."""
        assert self._proc is None, "spawn once"
        self.workdir.mkdir(parents=True, exist_ok=True)
        try:
            self.map_path.unlink()
        except FileNotFoundError:
            pass
        slot = _slots.acquire() if self._take_slot else None        # may wait; nothing to undo if it raises
        parent, child = multiprocessing.Pipe(duplex=True)
        try:
            self._proc = self._popen(child.fileno(), slot)
        except BaseException:
            parent.close()
            child.close()
            if slot is not None:
                slot.release()
            raise
        if slot is not None:
            slot.release()                  # the worker keeps the lock
        child.close()
        self._conn = parent
        if slot is not None:
            self._write_slot_txt(slot)
        kind, payload = self._wait("hello", Wait(total=boot_timeout), 0)
        assert kind == "ok"
        self._hb_base = self._heartbeat()

    def _popen(self, child_fd: int, slot: "Optional[_slots.Slot]") -> subprocess.Popen:
        """Start the worker with the pipe fd (and the slot fd, appended as ``argv[3]`` of the worker)."""
        pkg_parent = Path(__file__).resolve().parents[1]
        argv = self._argv(child_fd) if self._argv else worker_argv(child_fd, pkg_parent)
        fds = (child_fd,)
        if slot is not None:
            argv = [*argv, str(slot.fd)]
            fds = (child_fd, slot.fd)
        with open(self.err_path, "ab") as err_file:
            return subprocess.Popen(argv, pass_fds=fds, stdin=subprocess.DEVNULL, stdout=err_file,
                                    stderr=err_file, env=self._env, cwd=self.workdir)

    def _write_slot_txt(self, slot: "_slots.Slot") -> None:
        """``slot.txt`` in the workdir: which slot the worker holds (written after Popen)."""
        assert self._proc is not None
        text = (f"slot={slot.index} pid={self._proc.pid} acquired={slot.acquired:.6f} "
                f"waited_s={slot.waited_s:.3f}\n")
        (self.workdir / "slot.txt").write_text(text)

    # ---- request ----
    def request(self, op: str, args: Sequence[Any], wait: Wait, frame_before: int = 0) -> Tuple[str, Any]:
        """Send one request and wait for its reply under ``wait`` (see the module doc for the outcomes)."""
        if self.closed or self._proc is None or self._conn is None:
            raise HostError("the emulator is closed")
        try:
            self._conn.send((op, tuple(args)))
        except (BrokenPipeError, OSError):
            return self._died(op, frame_before)
        kind, payload = self._wait(op, wait, frame_before)
        if op == "start" and kind == "ok":
            self._hb_base = self._heartbeat()
            self._hb_moved = False
        return kind, payload

    def _limit(self, wait: Wait) -> Optional[float]:
        return wait.heartbeat if self._hb_moved or wait.first_heartbeat is None else wait.first_heartbeat

    def _wait(self, op: str, wait: Wait, frame_before: int) -> Tuple[str, Any]:
        assert self._conn is not None and self._proc is not None
        begin = time.monotonic()
        last_change = begin
        last_hb = self._heartbeat()
        for _ in range(MAX_POLLS):
            try:
                if self._conn.poll(POLL_S):
                    return self._reply(op, self._conn.recv(), frame_before)
            except (EOFError, ConnectionResetError, OSError):
                return self._died(op, frame_before)
            if self._proc.poll() is not None:
                return self._after_exit(op, frame_before)
            now = time.monotonic()
            if wait.heartbeat is not None:
                hb = self._heartbeat()
                if hb != last_hb:
                    last_hb, last_change = hb, now
                    if hb != self._hb_base:
                        self._hb_moved = True
                limit = self._limit(wait)
                if limit is not None and now - last_change > limit:
                    self._timeout(op, limit)
            if wait.total is not None and now - begin > wait.total:
                self._timeout(op, wait.total)
        raise HostError(f"{op}: wait loop ran out of polls")

    def _reply(self, op: str, msg: Any, frame_before: int) -> Tuple[str, Any]:
        kind = msg[0]
        if kind in ("ok", "hello"):
            return "ok", msg[1]
        if kind == "err":
            raise from_code(int(msg[1]), str(msg[2]), during_start=(op == "start"))
        if kind == "fatal":
            self._reap()
            raise HostError(str(msg[1]))
        raise HostError(f"unknown reply {kind!r} to {op}")

    def _after_exit(self, op: str, frame_before: int) -> Tuple[str, Any]:
        """The worker is gone: a reply written just before it exited still counts."""
        assert self._conn is not None
        try:
            if self._conn.poll(0):
                return self._reply(op, self._conn.recv(), frame_before)
        except (EOFError, OSError):
            pass
        return self._died(op, frame_before)

    # ---- death and timeout ----
    def _timeout(self, op: str, seconds: float) -> None:
        message = self._message()
        self._reap()
        raise HostTimeout(op, seconds, message)

    def _reap(self) -> None:
        """Kill our own worker if it still runs, reap it, drop the pipe. Safe to repeat."""
        proc = self._proc
        if proc is not None and proc.poll() is None:
            proc.kill()
        if proc is not None:
            proc.wait()
        if self._conn is not None:
            self._conn.close()
            self._conn = None
        self.closed = True

    def _died(self, op: str, frame_before: int) -> Tuple[str, Any]:
        """Death mapping: return code of the worker to the right outcome (docs/plans/phase-d.md 4.4)."""
        assert self._proc is not None
        try:
            code = self._proc.wait(timeout=REAP_S)
        except subprocess.TimeoutExpired:
            self._proc.kill()
            code = self._proc.wait()
        hostmap = self.host_map()
        message = self._message()
        self._reap()
        if code == _abi.AZH_EXIT_GUEST_EXITED:
            if op == "run":
                total = hostmap.frame_total() if hostmap is not None else frame_before
                frames = max(total - frame_before, 0)
                return "exited", {"frames": frames, "frame_total": total, "message": message or "",
                                  "vblanks": hostmap.vblanks_total() if hostmap is not None else 0}
            raise HostError(f"the guest exited during {op}: {message or 'no message'}")
        if code == _abi.AZH_EXIT_GUEST_ERROR:
            raise GuestError(message or "the guest stopped with a fatal error")
        number = -code if code < 0 else None
        raise HostCrashed(code, number, message, tail_lines(self.log_path), tail_lines(self.err_path))

    # ---- close ----
    def close(self, timeout: float = 30.0) -> None:
        """Always reaps: a graceful ``close`` request, then SIGKILL of our own worker. Idempotent."""
        if self._proc is None:
            self.closed = True
            return
        if not self.closed and self._conn is not None:
            try:
                self._conn.send(("close", ()))
                if self._conn.poll(timeout):
                    self._conn.recv()
                self._proc.wait(timeout=REAP_S)
            except (OSError, EOFError, subprocess.TimeoutExpired):
                pass
        self._reap()
        if self._map is not None:
            self.final_frame_total = self._map.frame_total()
            self._map.close()
            self._map = None
        self._map_closed = True

    def kill_own_worker(self, sig: int = signal.SIGKILL) -> None:
        """Send a signal to our own worker (tests use it; never anything else's process)."""
        if self._proc is not None and self._proc.poll() is None:
            os.kill(self._proc.pid, sig)


def reap_process(proc: Optional[subprocess.Popen]) -> None:
    """Finalizer helper: kill and reap a worker that was never closed."""
    if proc is not None and proc.poll() is None:
        proc.kill()
    if proc is not None:
        proc.wait()

