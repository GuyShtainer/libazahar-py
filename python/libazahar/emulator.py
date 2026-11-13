"""The Emulator: one headless Azahar instance in its own worker process (docs/plans/phase-d.md 4.6)."""
from __future__ import annotations

import operator
import os
import shutil
import struct
import weakref
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from . import _abi, _paths
from ._client import Wait, WorkerClient, reap_process
from .errors import ArgumentError, BootError, GuestError, HostError
from .inputs import Buttons, Circle, Held, Item, Touch, _TouchUp, apply_item, check_buttons, fold, held_after
from .memory import Memory
from .results import RunResult, SaveInfo, Shot, Stats, ThreadInfo, WatchRow

__all__ = ["Emulator"]

MAX_FRAMES = 100_000_000
MAX_EVERY = 100_000
STATE_EXTRA_S = 10.0
RECORD_FRAME_IGNORED = 1
Options = Union[Mapping[str, str], Sequence[Tuple[str, str]], None]


MAX_PROFILE_LINE = 511
MAX_PROFILE_LINES = 4096


def _profile_line(path: Path, number: int, raw: bytes) -> Optional[Tuple[str, str]]:
    """One profile line (without its ``\\n``) as ``(key, value)``, or None for a blank or comment line."""
    if raw.endswith(b"\r"):
        raw = raw[:-1]
    if len(raw) > MAX_PROFILE_LINE:
        raise ArgumentError(f"{path}:{number}: line is {len(raw)} bytes, over the {MAX_PROFILE_LINE} byte limit")
    if not raw:
        return None
    if b"\0" in raw:
        raise ArgumentError(f"{path}:{number}: NUL byte in the line")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ArgumentError(f"{path}:{number}: the line starts with a UTF-8 byte order mark")
    try:
        line = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ArgumentError(f"{path}:{number}: not valid UTF-8") from None
    if line.startswith("#"):
        return None
    if line[0] in " \t" or line[-1] in " \t":
        raise ArgumentError(f"{path}:{number}: line starts or ends with a space or tab")
    key, sep, value = line.partition("=")
    if not sep:
        raise ArgumentError(f"{path}:{number}: no '=' in the line")
    if not key or " " in key or "\t" in key:
        raise ArgumentError(f"{path}:{number}: the key is empty or holds a space or tab")
    return key, value


def _read_profile(path: Path) -> List[Tuple[str, str]]:
    """The ``key=value`` pairs of an option profile, in file order (the format is in docs/USING.md section 14).

    Lines split on ``\\n`` only (one trailing ``\\r`` is dropped); a line is at most 511 bytes and a file at most 4096
    lines; a line whose first byte is ``#`` is a comment; nothing is trimmed, so padding is an error. Every line
    (comments too) must be valid UTF-8 with no NUL byte, and no line may start with a byte order mark. The lines are
    read in file order and the first error wins; a 4097th line is the error ``<path>:4097: more than 4096 lines``.
    Raises ArgumentError ``<path>:<line>: <reason>`` for a bad line and HostError when the file cannot be read.
    """
    pairs: List[Tuple[str, str]] = []
    try:
        with open(path, "rb") as handle:
            for number, raw in enumerate(handle, 1):
                if number > MAX_PROFILE_LINES:
                    raise ArgumentError(f"{path}:{number}: more than {MAX_PROFILE_LINES} lines")
                pair = _profile_line(path, number, raw[:-1] if raw.endswith(b"\n") else raw)
                if pair is not None:
                    pairs.append(pair)
    except OSError as exc:
        raise HostError(f"cannot read the option profile {path}: {exc.strerror or exc}") from exc
    return pairs


def _pairs(options: Options) -> List[Tuple[str, str]]:
    """The ``options=`` pairs as strings; each must pass the one-line profile rule when written as ``key=value``."""
    if options is None:
        return []
    items = options.items() if isinstance(options, Mapping) else options
    out: List[Tuple[str, str]] = []
    for key, value in items:
        key, value = str(key), str(value)
        try:
            if "\n" in key or "\n" in value or value.endswith("\r"):
                raise ArgumentError("a newline or a trailing CR cannot be written on one line")
            pair = _profile_line(Path("options"), 1, f"{key}={value}".encode("utf-8", "surrogateescape"))
            if pair != (key, value):
                raise ArgumentError("not a valid key=value pair")
        except (ArgumentError, UnicodeEncodeError) as exc:
            raise ArgumentError(f"options: bad pair for key {key!r}: {str(exc).split(': ', 2)[-1]}") from None
        out.append((key, value))
    return out


def _index(value: object, message: str) -> int:
    """``value`` as an int through ``operator.index`` (numpy integers pass; floats and bools do not)."""
    if isinstance(value, bool):
        raise ArgumentError(message)
    try:
        return operator.index(value)       # type: ignore[arg-type]
    except TypeError:
        raise ArgumentError(message) from None


def _seconds(value: object, name: str) -> float:
    """``value`` as a finite number of seconds (a bool, a string or NaN is an ArgumentError)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) and not hasattr(value, "__float__"):
        raise ArgumentError(f"{name} must be a number of seconds")
    try:
        number = float(value)       # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise ArgumentError(f"{name} must be a number of seconds") from None
    if number != number:
        raise ArgumentError(f"{name} must be a number of seconds")
    return number


def _check_sd_file(name: str) -> str:
    if not name or os.path.isabs(name) or ".." in Path(name).parts:
        raise ArgumentError(f"stop_file {name!r} must be a relative path inside the SD folder, without '..'")
    return name


def _check_sd_seed(sd_seed: Union[str, Path, None]) -> None:
    if sd_seed is None:
        return
    folder = Path(sd_seed)
    if folder.name == "sdmc":
        raise ArgumentError("sd_seed must not be named 'sdmc' (pass the folder whose contents become the SD card)")
    if not folder.is_dir():
        raise ArgumentError(f"sd_seed {folder} is not a folder")


def _clear_sd(sd: Path) -> None:
    """Delete the SD folder of a reused workdir (never through a symlink), so seed files land on an empty card."""
    if sd.is_symlink():
        raise ArgumentError(f"fresh_sd: {sd} is a symlink; refusing to clear it")
    if sd.is_dir():
        shutil.rmtree(sd)


class Emulator:
    """One emulator instance. Use as a context manager, or call :meth:`close`.

    ``workdir`` holds ``sys/`` (the SD folder is ``sys/Azahar/sdmc/``), ``shots/``, ``host.log``, ``host.map`` and
    ``worker.err``. ``sd_seed`` (a folder, never named ``sdmc``) is copied into the SD folder before a normal boot,
    and after a state boot (so seed files land on top of the state's snapshot). ``fresh_sd=True`` empties
    the SD folder first and keeps the rest of ``sys/`` (the warm shader cache). ``timeout`` is how long the heartbeat
    may stand still during a ``run`` (no new frame), not a bound on the batch; ``boot_timeout`` covers ``start`` and
    the first frames (shader compiles). ``app`` and ``workdir`` are read-only; ``timeout`` and
    ``boot_timeout`` (seconds) may be set at any time. Raises ArgumentError (also a ValueError; includes a missing
    ``sd_seed`` folder), BootError, HostError (includes an unreadable profile), SlotTimeout, HostTimeout, HostCrashed.
    """

    def __init__(self, app: Union[str, Path], workdir: Union[str, Path], *, sd_seed: Union[str, Path, None] = None,
                 state: Union[str, Path, None] = None, core: Union[str, Path, None] = None, options: Options = None,
                 timeout: float = 30.0, boot_timeout: float = 300.0, fresh_sd: bool = False) -> None:
        self.timeout = _seconds(timeout, "timeout")
        self.boot_timeout = _seconds(boot_timeout, "boot_timeout")
        self._app = Path(app).resolve()
        self._workdir = Path(workdir).resolve()
        if not self._app.is_file():
            raise ArgumentError(f"app {self._app} is not a file")
        _check_sd_seed(sd_seed)
        self._held = Held()
        self._is_lazpy = False
        self._memory: Optional[Memory] = None
        self._shots_dir = self._workdir / "shots"
        self._sd = self._workdir / "sys" / "Azahar" / "sdmc"
        folder = self._workdir
        try:
            if fresh_sd:
                _clear_sd(self._sd)
            for folder in (self._sd, self._shots_dir):
                folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise HostError(f"cannot make the working folder {folder}: {exc.strerror or exc}") from exc
        host = _paths.host_path()
        env = dict(os.environ)
        env["LAZ_HOST"] = str(host)
        env["LAZ_MVK"] = str(_paths.mvk_path())
        self._client = WorkerClient(self._workdir, self._workdir / "host.map", self._workdir / "host.log", env)
        self._finalizer: Optional[weakref.finalize] = None
        try:
            self._boot(core, options, sd_seed, state)
        except BaseException:
            self.close()
            raise

    def _boot(self, core: Union[str, Path, None], options: Options, sd_seed: Union[str, Path, None],
              state: Union[str, Path, None]) -> None:
        core_file = _paths.core_path(None if core is None else str(core))
        if not core_file.is_file():
            raise BootError(f"core {core_file} is missing: run tools/fetch.sh --lazpy-core, or set LAZ_CORE (or core=) "
                            "to a core file")
        if sd_seed is not None and state is None:
            shutil.copytree(sd_seed, self._sd, symlinks=False, dirs_exist_ok=True)
        pairs = _read_profile(_paths.profile_path()) + _pairs(options)
        lazpy_file = _paths.lazpy_profile()
        lazpy_pairs = _read_profile(lazpy_file) if lazpy_file is not None else []
        self._client.spawn(self.boot_timeout)
        self._finalizer = weakref.finalize(self, reap_process, self._client.proc)
        args = (str(core_file), str(self._workdir / "sys"),
                str(self._workdir / "host.log"), str(self._workdir / "host.map"), pairs, str(self.app),
                str(Path(state).resolve()) if state is not None else None, lazpy_pairs)
        _, stats = self._client.request("start", args, Wait(total=self.boot_timeout))
        self._is_lazpy = bool(stats["is_lazpy_core"])
        if sd_seed is not None and state is not None:
            shutil.copytree(sd_seed, self._sd, symlinks=False, dirs_exist_ok=True)

    # ---- properties ----
    @property
    def app(self) -> Path:
        """The app file, resolved. Read-only."""
        return self._app

    @property
    def workdir(self) -> Path:
        """The working folder, resolved. Read-only."""
        return self._workdir

    @property
    def sd(self) -> Path:
        """The emulated SD card's folder."""
        return self._sd

    @property
    def pid(self) -> int:
        """The worker's pid."""
        return self._client.pid

    @property
    def closed(self) -> bool:
        """True after close(), or after the worker died or the guest exited."""
        return self._client.closed

    @property
    def frame_total(self) -> int:
        """Frames run since boot (a state's frame count plus its k after a load), read from the map."""
        hostmap = self._client.host_map()
        return hostmap.frame_total() if hostmap is not None else self._client.final_frame_total

    @property
    def memory(self) -> Memory:
        """Guest memory by virtual address (our core only): ``read``, ``write``, ``u32(addr)``, ``raw_read``."""
        if self._memory is None:
            self._memory = Memory(self._memory_request)
        return self._memory

    def _memory_request(self, op: str, args: tuple) -> object:
        self._live()
        _, payload = self._client.request(op, args, Wait(total=self.timeout))
        return payload

    def _live(self) -> None:
        if self._client.closed:
            raise HostError("the emulator is closed")

    # ---- running ----
    def run(self, frames: int, *, inputs: Iterable[Tuple[int, Item]] = (), shots: Iterable[int] = (),
            stop_file: Optional[str] = None, stop_text: Optional[str] = None, stop_every: int = 30,
            stop_new: bool = False, debug_text: Optional[str] = None, wall_limit: Optional[float] = None,
            timeout: Optional[float] = None, watch: Optional[Sequence[Tuple[int, int]]] = None,
            watch_every: int = 1) -> RunResult:
        """Run ``frames`` guest frames (one frame = one guest VBlank, 1-based within the batch).

        ``inputs`` are ``(frame, item)`` pairs; an item is Buttons/int (the whole button mask), ``Touch(x, y)``,
        ``Touch.up`` or ``Circle(x, y)``, and changes only its part of the held state; the state reached by the last
        frame run stays after the batch.
        ``shots`` are batch frames to save as PNG (``result.shots[f]``). ``stop_file`` (relative to the SD folder) with
        ``stop_text`` stops the batch when the file holds the text, checked every ``stop_every`` frames and after the
        last; ``stop_new`` looks only at text written after the batch starts. ``inputs``, ``shots`` and the rest are keyword-only. ``debug_text`` needs our core.
        ``wall_limit`` is in seconds. ``watch`` (our core only) is a list of ``(addr, words)`` pairs: after every
        ``watch_every``-th frame (and after the last frame run) the host reads each entry (``words`` u32 words at guest
        address ``addr``) into ``result.watch``, a tuple of ``WatchRow``; the host refuses a batch whose rows do not
        fit and says the largest frame count that does. The guest may be part-way into a frame at each read.
        ``timeout`` replaces the heartbeat timeout for this call: seconds with no new frame, not the batch's wall
        time, so a long batch needs no big value (``wall_limit`` bounds the wall time). Returns a RunResult;
        a guest exit gives ``stopped_by == "guest_exited"`` and a closed Emulator on both cores (on our core the
        worker is shut down cleanly after the result is built). On the stock core the exit result has ``wall_s`` 0.0 and
        no ``shots`` even if PNGs were written before the exit. A guest crash raises GuestError (with
        ``.result`` when the batch ended with ``guest_error``; the Emulator stays open then; the third error in one
        frame ends the worker and the Emulator is closed). Raises ArgumentError for bad arguments, GuestError,
        HostTimeout, HostCrashed.
        """
        self._live()
        batch, shot_frames = self._build_batch(frames, shots, stop_file, stop_text, stop_every, stop_new,
                                               debug_text, wall_limit)
        watch_sizes = self._fill_watch(batch, watch, watch_every)
        prev = self._held
        records, _ = fold(inputs, frames, prev)
        before = self.frame_total
        wait = Wait(heartbeat=self.timeout if timeout is None else _seconds(timeout, "timeout"), first_heartbeat=self.boot_timeout)
        kind, payload = self._client.request("run", (records.tobytes(), bytes(batch)), wait, frame_before=before)
        if kind == "exited":
            self._held = held_after(records, payload["frames"], prev)
            result = RunResult(frames=payload["frames"], stopped_by="guest_exited", first_frame=before + 1,
                               last_frame=payload["frame_total"], frame_total=payload["frame_total"],
                               vblanks=payload["vblanks"], wall_s=0.0, message=payload["message"])
            self.close()
            return result
        result = self._result(_abi.Result.from_buffer_copy(payload), shot_frames, before, watch_sizes)
        self._held = held_after(records, result.frames, prev)
        if result.stopped_by == "guest_error":
            raise GuestError(result.message or "the guest stopped with a fatal error", result)
        if result.stopped_by == "guest_exited":      # one rule on both cores: after a guest exit the Emulator is closed
            self._close(min(self.timeout, 5.0))      # a stalled retro_unload_game costs 5 s, not 30
        return result

    def _build_batch(self, frames: int, shots: Iterable[int], stop_file: Optional[str], stop_text: Optional[str],
                     stop_every: int, stop_new: bool, debug_text: Optional[str],
                     wall_limit: Optional[float]) -> Tuple[_abi.Batch, List[int]]:
        frames = _index(frames, f"frames must be an integer 1..{MAX_FRAMES}")
        if not 1 <= frames <= MAX_FRAMES:
            raise ArgumentError(f"frames must be an integer 1..{MAX_FRAMES}")
        shot_frames = sorted({_index(f, "shots must be integers") for f in shots})
        if len(shot_frames) > _abi.AZH_MAX_SHOTS or any(not 1 <= f <= frames for f in shot_frames):
            raise ArgumentError(f"shots: at most {_abi.AZH_MAX_SHOTS} frames, each within 1..{frames}")
        if (stop_file is None) != (stop_text is None):
            raise ArgumentError("stop_file and stop_text go together")
        batch = _abi.Batch()
        batch.frames = frames
        batch.n_shots = len(shot_frames)
        for index, frame in enumerate(shot_frames):
            batch.shots[index].frame = frame
            batch.shots[index].screens = _abi.AZH_SCREEN_BOTH
            batch.shots[index].format = _abi.AZH_FMT_PNG
        batch.shot_dir = str(self._shots_dir).encode()
        self._fill_stops(batch, stop_file, stop_text, stop_every, stop_new, debug_text, wall_limit)
        return batch, shot_frames

    @staticmethod
    def _fill_stops(batch: _abi.Batch, stop_file: Optional[str], stop_text: Optional[str], stop_every: int,
                    stop_new: bool, debug_text: Optional[str], wall_limit: Optional[float]) -> None:
        if stop_file is not None and stop_text is not None:
            data = stop_text.encode()
            if not data or len(data) > 255:
                raise ArgumentError("stop_text must be 1..255 bytes")
            stop_every = _index(stop_every, f"stop_every must be an integer 1..{MAX_EVERY}")
            if not 1 <= stop_every <= MAX_EVERY:
                raise ArgumentError(f"stop_every must be an integer 1..{MAX_EVERY}")
            batch.sd_file = _check_sd_file(stop_file).encode()
            batch.sd_text = data
            batch.sd_every = stop_every
            batch.sd_from_end = 1 if stop_new else 0
        if debug_text:
            data = debug_text.encode()
            if len(data) > 255:
                raise ArgumentError("debug_text must be under 256 bytes")
            batch.debug_text = data
        if wall_limit is not None:
            wall_limit = _seconds(wall_limit, "wall_limit")
            if wall_limit <= 0:
                raise ArgumentError("wall_limit must be positive seconds")
            batch.wall_limit_ms = max(1, int(wall_limit * 1000))

    @staticmethod
    def _fill_watch(batch: _abi.Batch, watch: Optional[Sequence[Tuple[int, int]]], every: int) -> List[int]:
        """Shape checks only (the host's plan checks the rest); returns the words of each entry."""
        entries = [] if watch is None else list(watch)
        if len(entries) > _abi.AZH_MAX_WATCH:
            raise ArgumentError(f"watch: at most {_abi.AZH_MAX_WATCH} entries")
        every = _index(every, f"watch_every must be an integer 1..{MAX_EVERY}")
        if not 1 <= every <= MAX_EVERY:
            raise ArgumentError(f"watch_every must be an integer 1..{MAX_EVERY}")
        words: List[int] = []
        for entry in entries:
            if (not isinstance(entry, (tuple, list)) or len(entry) != 2
                    or any(isinstance(v, bool) or not isinstance(v, int) for v in entry)):
                raise ArgumentError(f"watch entry {entry!r} must be an (addr, words) pair of integers")
            addr, count = entry
            if not 0 <= addr < (1 << 32) or not 0 <= count < (1 << 32):
                raise ArgumentError(f"watch entry {entry!r}: addr and words must fit an unsigned 32-bit integer")
            words.append(count)
        batch.n_watch = len(entries)
        batch.watch_every = min(every, 0x7FFFFFFF)
        for index, (addr, count) in enumerate(entries):
            batch.watch[index].addr = addr
            batch.watch[index].words = count
        return words

    def _watch_rows(self, count: int, words: List[int]) -> Tuple[WatchRow, ...]:
        """The rows of the batch just run, copied out of the map and split per entry."""
        if count <= 0:
            return ()
        hostmap = self._client.host_map()
        if hostmap is None:
            raise HostError("the map is gone: the watch rows cannot be read")
        rows: List[WatchRow] = []
        for frame, status, blob in hostmap.watch_copy(count):
            parts, at = [], 0
            for n in words:
                parts.append(blob[at:at + 4 * n])
                at += 4 * n
            rows.append(WatchRow(frame, status, tuple(parts)))
        return tuple(rows)

    def _result(self, raw: _abi.Result, shot_frames: List[int], before: int,
                watch_sizes: Optional[List[int]] = None) -> RunResult:
        done: Dict[int, Shot] = {}
        for frame in shot_frames[:raw.shots_done]:
            stem = self._shots_dir / f"shot_{before + frame:06d}"
            done[frame] = Shot(frame, Path(f"{stem}_top.png"), Path(f"{stem}_bottom.png"), before + frame)
        return RunResult(frames=raw.frames_run, stopped_by=_abi.STOP_NAMES.get(raw.stop_reason, str(raw.stop_reason)),
                         first_frame=raw.first_frame, last_frame=raw.last_frame, frame_total=self.frame_total,
                         vblanks=raw.vblanks, wall_s=raw.wall_s, message=raw.message.decode("utf-8", "replace"),
                         shots=done, watch=self._watch_rows(raw.watch_rows, watch_sizes or []))

    def run_until(self, file: str, text: str, max_frames: int, *, stop_every: int = 30, stop_new: bool = False,
                  inputs: Iterable[Tuple[int, Item]] = (), shots: Iterable[int] = (),
                  wall_limit: Optional[float] = None, debug_text: Optional[str] = None,
                  timeout: Optional[float] = None, watch: Optional[Sequence[Tuple[int, int]]] = None,
                  watch_every: int = 1) -> RunResult:
        """Run until ``text`` appears in the SD file ``file`` (checked every ``stop_every`` frames) or ``max_frames``.

        Takes the same options as :meth:`run` under the same names. The caller checks ``result.stopped_by == "sd_text"``.
        """
        return self.run(max_frames, inputs=inputs, shots=shots, stop_file=file, stop_text=text, stop_every=stop_every,
                        stop_new=stop_new, debug_text=debug_text, wall_limit=wall_limit, timeout=timeout,
                        watch=watch, watch_every=watch_every)

    def run_frame(self) -> RunResult:
        """Run exactly one frame."""
        return self.run(1)

    # ---- input now ----
    def set_input(self, buttons: Union[Buttons, int, None] = None, touch: Union[Touch, _TouchUp, None] = None,
                  circle: Optional[Circle] = None) -> None:
        """Change the held input now; an argument left as None keeps its part of the held state."""
        self._live()
        held = self._held
        for item in (buttons, touch, circle):
            if item is not None:
                held = apply_item(held, item)
        kind, _ = self._client.request("set_input", (held.as_record(RECORD_FRAME_IGNORED),),
                                       Wait(total=self.timeout))
        assert kind == "ok"
        self._held = held

    def set_keys(self, raw: int) -> None:
        """Hold exactly the buttons in ``raw`` (libmgba-py's name for the whole mask)."""
        self.set_input(buttons=check_buttons(int(raw)))

    # ---- pictures ----
    def screens(self) -> Tuple[Any, Any]:
        """The current top (400x240) and bottom (320x240) screens as RGBA ``(240, w, 4)`` uint8 arrays.

        One raw shot is taken; the returned numpy arrays (``bytes`` when numpy is absent) are read-only views of the
        instance's map, so they change at the next raw shot (the next ``screens()`` or a batch RAW shot). Call
        ``.copy()`` to keep a frame. Raises HostError if the map does not show this frame.
        """
        self._live()
        self._client.request("shot", (_abi.AZH_SCREEN_BOTH, _abi.AZH_FMT_RAW, None), Wait(total=self.timeout))
        hostmap = self._client.host_map()
        if hostmap is None or hostmap.px_frame() != hostmap.frame_total():
            raise HostError("the map's pixel frame does not match frame_total after a raw shot")
        top, bottom = hostmap.pixels(_abi.AZH_SCREEN_TOP), hostmap.pixels(_abi.AZH_SCREEN_BOTTOM)
        try:
            import numpy
        except ImportError:
            return bytes(top), bytes(bottom)
        return (numpy.frombuffer(top, dtype=numpy.uint8).reshape(240, 400, 4),
                numpy.frombuffer(bottom, dtype=numpy.uint8).reshape(240, 320, 4))

    def shot(self, path_prefix: Union[str, Path]) -> Tuple[Path, Path]:
        """Save the current frame as ``<prefix>_top.png`` and ``<prefix>_bottom.png``; returns the two paths."""
        self._live()
        prefix = str(Path(path_prefix).resolve())
        self._client.request("shot", (_abi.AZH_SCREEN_BOTH, _abi.AZH_FMT_PNG, prefix), Wait(total=self.timeout))
        return Path(f"{prefix}_top.png"), Path(f"{prefix}_bottom.png")

    # ---- states ----
    def save_state(self, path: Union[str, Path]) -> SaveInfo:
        """Save a state at ``path`` (plus ``<path>.sd/`` and ``<path>.meta``). ``SaveInfo.k`` is the number of guest
        VBlanks the save's drain ran; a state "at frame N" is at N + k. Raises StateError."""
        self._live()
        target = str(Path(path).resolve())
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        _, k = self._client.request("save_state", (target,), Wait(total=self.timeout + STATE_EXTRA_S))
        return SaveInfo(path=Path(target), k=int(k), frame_total=self.frame_total)

    def load_state(self, path: Union[str, Path]) -> None:
        """Restore a state made by the same app; the SD folder becomes the snapshot's. Raises StateError."""
        self._live()
        self._client.request("load_state", (str(Path(path).resolve()),), Wait(total=self.timeout + STATE_EXTRA_S))

    def threads(self) -> Tuple[ThreadInfo, ...]:
        """Every guest thread on every core, with its pc, lr, sp and cpsr, read between batches (core lazpy.2).
        System-module threads are listed too: filter by ``pid``. Raises NeedsLazpyCore on the stock core and on a
        lazpy.1 core."""
        self._live()
        _, raw = self._client.request("threads", (), Wait(total=self.timeout))
        assert isinstance(raw, bytes) and len(raw) % struct.calcsize("<10I") == 0
        out = []
        for tid, pid, status, core, priority, flags, pc, lr, sp, cpsr in struct.iter_unpack("<10I", raw):
            out.append(ThreadInfo(tid, pid, status, _abi.THREAD_STATUS_NAMES.get(status, f"status_{status}"), core,
                                  priority, bool(flags & _abi.AZH_THREAD_CURRENT), pc, lr, sp, cpsr))
        return tuple(out)

    def stats(self) -> Stats:
        """The host's counters."""
        self._live()
        _, raw = self._client.request("stats", (), Wait(total=self.timeout))
        return Stats(**raw)

    # ---- closing ----
    def close(self) -> None:
        """Stop the worker (graceful, then SIGKILL of our own worker) and reap it. Safe to call twice."""
        self._close(self.timeout)

    def _close(self, graceful: float) -> None:
        self._client.close(graceful)
        if self._finalizer is not None:
            self._finalizer.detach()

    def __enter__(self) -> "Emulator":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
