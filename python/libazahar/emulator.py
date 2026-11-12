"""The Emulator: one headless Azahar instance in its own worker process (docs/plans/phase-d.md 4.6)."""
from __future__ import annotations

import os
import shutil
import weakref
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from . import _abi, _paths
from ._client import Wait, WorkerClient, reap_process
from .errors import GuestError, HostError
from .inputs import Buttons, Circle, Held, Item, Touch, _TouchUp, apply_item, check_buttons, fold, held_after
from .results import RunResult, SaveInfo, Shot, Stats

__all__ = ["Emulator"]

MAX_FRAMES = 100_000_000
MAX_EVERY = 100_000
STATE_EXTRA_S = 10.0
RECORD_FRAME_IGNORED = 1
Options = Union[Mapping[str, str], Sequence[Tuple[str, str]], None]


def _read_profile(path: Path) -> List[Tuple[str, str]]:
    """The ``key=value`` lines of an option profile, in order (comments and blank lines skipped)."""
    pairs: List[Tuple[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            raise HostError(f"{path}: line without '=': {raw!r}")
        pairs.append((key.strip(), value.strip()))
    return pairs


def _pairs(options: Options) -> List[Tuple[str, str]]:
    if options is None:
        return []
    items = options.items() if isinstance(options, Mapping) else options
    return [(str(key), str(value)) for key, value in items]


def _check_sd_file(name: str) -> str:
    if not name or os.path.isabs(name) or ".." in Path(name).parts:
        raise ValueError(f"stop_file {name!r} must be a relative path inside the SD folder, without '..'")
    return name


class Emulator:
    """One emulator instance. Use as a context manager, or call :meth:`close`.

    ``workdir`` holds ``sys/`` (the SD folder is ``sys/Azahar/sdmc/``), ``shots/``, ``host.log``, ``host.map`` and
    ``worker.err``. ``sd_seed`` (a folder, never named ``sdmc``) is copied into the SD folder before a normal boot,
    and after a state boot (so seed files land on top of the state's snapshot). ``timeout`` is how long the heartbeat
    may stand still during a ``run``; ``boot_timeout`` covers ``start`` and the first frames (shader compiles).
    Raises BootError, HostError, StateError, HostCrashed, HostTimeout (see ``errors``), ValueError for bad arguments.
    """

    def __init__(self, app: Union[str, Path], workdir: Union[str, Path], *, sd_seed: Union[str, Path, None] = None,
                 state: Union[str, Path, None] = None, core: Union[str, Path, None] = None, options: Options = None,
                 timeout: float = 30.0, boot_timeout: float = 300.0) -> None:
        self.timeout = float(timeout)
        self.boot_timeout = float(boot_timeout)
        self.app = Path(app).resolve()
        self.workdir = Path(workdir).resolve()
        if not self.app.is_file():
            raise ValueError(f"app {self.app} is not a file")
        if sd_seed is not None and Path(sd_seed).name == "sdmc":
            raise ValueError("sd_seed must not be named 'sdmc' (pass the folder whose contents become the SD card)")
        self._held = Held()
        self._is_lazpy = False
        self._shots_dir = self.workdir / "shots"
        self._sd = self.workdir / "sys" / "Azahar" / "sdmc"
        for folder in (self._sd, self._shots_dir):
            folder.mkdir(parents=True, exist_ok=True)
        host = _paths.host_path()
        env = dict(os.environ)
        env["LAZ_HOST"] = str(host)
        env["LAZ_MVK"] = str(_paths.mvk_path())
        self._client = WorkerClient(self.workdir, self.workdir / "host.map", self.workdir / "host.log", env)
        self._finalizer: Optional[weakref.finalize] = None
        try:
            self._boot(core, options, sd_seed, state)
        except BaseException:
            self.close()
            raise

    def _boot(self, core: Union[str, Path, None], options: Options, sd_seed: Union[str, Path, None],
              state: Union[str, Path, None]) -> None:
        if sd_seed is not None and state is None:
            shutil.copytree(sd_seed, self._sd, symlinks=False, dirs_exist_ok=True)
        pairs = _read_profile(_paths.profile_path()) + _pairs(options)
        lazpy_file = _paths.lazpy_profile()
        lazpy_pairs = _read_profile(lazpy_file) if lazpy_file is not None else []
        self._client.spawn(self.boot_timeout)
        self._finalizer = weakref.finalize(self, reap_process, self._client.proc)
        args = (str(_paths.core_path(None if core is None else str(core))), str(self.workdir / "sys"),
                str(self.workdir / "host.log"), str(self.workdir / "host.map"), pairs, str(self.app),
                str(Path(state).resolve()) if state is not None else None, lazpy_pairs)
        _, stats = self._client.request("start", args, Wait(total=self.boot_timeout))
        self._is_lazpy = bool(stats["is_lazpy_core"])
        if sd_seed is not None and state is not None:
            shutil.copytree(sd_seed, self._sd, symlinks=False, dirs_exist_ok=True)

    # ---- properties ----
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

    def _live(self) -> None:
        if self._client.closed:
            raise HostError("the emulator is closed")

    # ---- running ----
    def run(self, frames: int, inputs: Iterable[Tuple[int, Item]] = (), shots: Iterable[int] = (), *,
            stop_file: Optional[str] = None, stop_text: Optional[str] = None, stop_every: int = 30,
            stop_new: bool = False, debug_text: Optional[str] = None, wall_limit: Optional[float] = None,
            timeout: Optional[float] = None) -> RunResult:
        """Run ``frames`` guest frames (one frame = one guest VBlank, 1-based within the batch).

        ``inputs`` are ``(frame, item)`` pairs; an item is Buttons/int (the whole button mask), ``Touch(x, y)``,
        ``Touch.up`` or ``Circle(x, y)``, and changes only its part of the held state; the state reached by the last
        frame run stays after the batch.
        ``shots`` are batch frames to save as PNG (``result.shots[f]``). ``stop_file`` (relative to the SD folder) with
        ``stop_text`` stops the batch when the file holds the text, checked every ``stop_every`` frames and after the
        last; ``stop_new`` looks only at text written after the batch starts. ``debug_text`` needs our core.
        ``wall_limit`` is in seconds. ``timeout`` replaces the heartbeat timeout for this call. Returns a RunResult;
        a guest exit gives ``stopped_by == "guest_exited"`` and a closed Emulator on both cores (on our core the
        worker is shut down cleanly after the result is built). On the stock core the exit result has ``wall_s`` 0.0 and
        no ``shots`` even if PNGs were written before the exit. A guest crash raises GuestError (with
        ``.result`` when the batch ended with ``guest_error``; the Emulator stays open then; the third error in one
        frame ends the worker and the Emulator is closed). Raises ValueError for bad arguments, GuestError,
        HostTimeout, HostCrashed.
        """
        self._live()
        batch, shot_frames = self._build_batch(frames, shots, stop_file, stop_text, stop_every, stop_new,
                                               debug_text, wall_limit)
        prev = self._held
        records, _ = fold(inputs, frames, prev)
        before = self.frame_total
        wait = Wait(heartbeat=self.timeout if timeout is None else float(timeout), first_heartbeat=self.boot_timeout)
        kind, payload = self._client.request("run", (records.tobytes(), bytes(batch)), wait, frame_before=before)
        if kind == "exited":
            self._held = held_after(records, payload["frames"], prev)
            result = RunResult(frames=payload["frames"], stopped_by="guest_exited", first_frame=before + 1,
                               last_frame=payload["frame_total"], frame_total=payload["frame_total"],
                               vblanks=payload["vblanks"], wall_s=0.0, message=payload["message"])
            self.close()
            return result
        result = self._result(_abi.Result.from_buffer_copy(payload), shot_frames, before)
        self._held = held_after(records, result.frames, prev)
        if result.stopped_by == "guest_error":
            raise GuestError(result.message or "the guest stopped with a fatal error", result)
        if result.stopped_by == "guest_exited":      # one rule on both cores: after a guest exit the Emulator is closed
            self._close(min(self.timeout, 5.0))      # a stalled retro_unload_game costs 5 s, not 30
        return result

    def _build_batch(self, frames: int, shots: Iterable[int], stop_file: Optional[str], stop_text: Optional[str],
                     stop_every: int, stop_new: bool, debug_text: Optional[str],
                     wall_limit: Optional[float]) -> Tuple[_abi.Batch, List[int]]:
        if isinstance(frames, bool) or not isinstance(frames, int) or not 1 <= frames <= MAX_FRAMES:
            raise ValueError(f"frames must be an integer 1..{MAX_FRAMES}")
        shot_frames = sorted(set(int(f) for f in shots))
        if len(shot_frames) > _abi.AZH_MAX_SHOTS or any(not 1 <= f <= frames for f in shot_frames):
            raise ValueError(f"shots: at most {_abi.AZH_MAX_SHOTS} frames, each within 1..{frames}")
        if (stop_file is None) != (stop_text is None):
            raise ValueError("stop_file and stop_text go together")
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
                raise ValueError("stop_text must be 1..255 bytes")
            if not 1 <= stop_every <= MAX_EVERY:
                raise ValueError(f"stop_every must be 1..{MAX_EVERY}")
            batch.sd_file = _check_sd_file(stop_file).encode()
            batch.sd_text = data
            batch.sd_every = stop_every
            batch.sd_from_end = 1 if stop_new else 0
        if debug_text:
            data = debug_text.encode()
            if len(data) > 255:
                raise ValueError("debug_text must be under 256 bytes")
            batch.debug_text = data
        if wall_limit is not None:
            if wall_limit <= 0:
                raise ValueError("wall_limit must be positive seconds")
            batch.wall_limit_ms = max(1, int(wall_limit * 1000))

    def _result(self, raw: _abi.Result, shot_frames: List[int], before: int) -> RunResult:
        done: Dict[int, Shot] = {}
        for frame in shot_frames[:raw.shots_done]:
            stem = self._shots_dir / f"shot_{before + frame:06d}"
            done[frame] = Shot(frame, f"{stem}_top.png", f"{stem}_bottom.png")
        return RunResult(frames=raw.frames_run, stopped_by=_abi.STOP_NAMES.get(raw.stop_reason, str(raw.stop_reason)),
                         first_frame=raw.first_frame, last_frame=raw.last_frame, frame_total=self.frame_total,
                         vblanks=raw.vblanks, wall_s=raw.wall_s, message=raw.message.decode("utf-8", "replace"),
                         shots=done)

    def run_until(self, file: str, text: str, max_frames: int, *, every: int = 30, new_only: bool = False,
                  inputs: Iterable[Tuple[int, Item]] = (), shots: Iterable[int] = (),
                  timeout: Optional[float] = None) -> RunResult:
        """Run until ``text`` appears in the SD file ``file`` (checked every ``every`` frames) or ``max_frames``.

        The caller checks ``result.stopped_by == "sd_text"``.
        """
        return self.run(max_frames, inputs, shots, stop_file=file, stop_text=text, stop_every=every,
                        stop_new=new_only, timeout=timeout)

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

    def shot(self, path_prefix: Union[str, Path]) -> Tuple[str, str]:
        """Save the current frame as ``<prefix>_top.png`` and ``<prefix>_bottom.png``; returns the two paths."""
        self._live()
        prefix = str(Path(path_prefix).resolve())
        self._client.request("shot", (_abi.AZH_SCREEN_BOTH, _abi.AZH_FMT_PNG, prefix), Wait(total=self.timeout))
        return f"{prefix}_top.png", f"{prefix}_bottom.png"

    # ---- states ----
    def save_state(self, path: Union[str, Path]) -> SaveInfo:
        """Save a state at ``path`` (plus ``<path>.sd/`` and ``<path>.meta``). ``SaveInfo.k`` is the number of guest
        VBlanks the save's drain ran; a state "at frame N" is at N + k. Raises StateError."""
        self._live()
        target = str(Path(path).resolve())
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        _, k = self._client.request("save_state", (target,), Wait(total=self.timeout + STATE_EXTRA_S))
        return SaveInfo(path=target, k=int(k), frame_total=self.frame_total)

    def load_state(self, path: Union[str, Path]) -> None:
        """Restore a state made by the same app; the SD folder becomes the snapshot's. Raises StateError."""
        self._live()
        self._client.request("load_state", (str(Path(path).resolve()),), Wait(total=self.timeout + STATE_EXTRA_S))

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
