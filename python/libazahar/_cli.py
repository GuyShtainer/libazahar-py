"""The command line: ``python -m libazahar doctor`` and ``python -m libazahar run`` (docs/USING.md section 2a).

Standard library only. Exit codes follow the table in USING section 3: 0 ok, 1 a failed check, 2 bad usage or
argument, 3 boot failure, 10 guest exited, 11 guest error, 12 timed out, 13 worker or host crashed or could not run.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import __version__, _host, _paths, _slots
from .emulator import Emulator
from .errors import ArgumentError, BootError, GuestError, HostError, HostTimeout, LibAzaharError
from .inputs import Buttons, Circle, Item, Touch
from .results import RunResult

__all__ = ["main", "parse_script", "to_jsonable"]

EXIT_OK, EXIT_FAILED, EXIT_USAGE, EXIT_BOOT = 0, 1, 2, 3
EXIT_GUEST_EXITED, EXIT_GUEST_ERROR, EXIT_TIMEOUT, EXIT_CRASHED = 10, 11, 12, 13
DOCTOR_FRAMES = 60
MAX_SCRIPT_LINE = 511
INT32_MIN, INT32_MAX = -(1 << 31), (1 << 31) - 1
_NUMBER = re.compile(r"^-?(0[xX][0-9a-fA-F]+|[0-9]+)$")
_SKIP = object()       # a value that is not JSON (an array or bytes): left out


# ---- the input script (USING section 4a) ----
def _script_int(text: str, where: str) -> int:
    if not _NUMBER.match(text):
        raise ArgumentError(f"{where}: {text!r} is not a decimal or 0x hex integer")
    negative = text.startswith("-")
    body = text[1:] if negative else text
    value = int(body, 16) if body[:2] in ("0x", "0X") else int(body, 10)     # a leading 0 is not octal
    value = -value if negative else value
    if not INT32_MIN <= value <= INT32_MAX:
        raise ArgumentError(f"{where}: {text!r} does not fit an int32")
    return value


def parse_script(path: Path) -> List[Tuple[int, Item]]:
    """Read an ``azhost --inputs`` script as ``(frame, item)`` pairs for ``Emulator.run(inputs=...)``.

    One record per line, ``frame buttons touch_x touch_y touch_down circle_x circle_y``, 7 int32 fields split on spaces,
    tabs or commas; ``#`` starts a comment. A record is the whole held state, so it becomes up to three items on its
    frame: the button mask, ``Touch(x, y)`` or ``Touch.up``, and ``Circle(x, y)``. Raises ArgumentError
    ``<file> line N: ...`` for a bad line and HostError when the file cannot be read.
    """
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise HostError(f"cannot read the input script {path}: {exc.strerror or exc}") from exc
    pairs: List[Tuple[int, Item]] = []
    for number, line in enumerate(raw.split(b"\n"), 1):
        where = f"{path} line {number}"
        if line.endswith(b"\r"):
            line = line[:-1]
        if len(line) > MAX_SCRIPT_LINE:
            raise ArgumentError(f"{where}: the line is {len(line)} bytes, over the {MAX_SCRIPT_LINE} byte limit")
        if b"\0" in line:
            raise ArgumentError(f"{where}: NUL byte in the line")
        text = line.decode("utf-8", "replace").split("#", 1)[0]
        fields = [part for part in re.split(r"[ \t,]+", text) if part]
        if not fields:
            continue
        if len(fields) != 7:
            raise ArgumentError(f"{where}: expected 7 fields, got {len(fields)}")
        frame, buttons, touch_x, touch_y, touch_down, circle_x, circle_y = (_script_int(f, where) for f in fields)
        pairs.append((frame, Buttons(buttons)))
        pairs.append((frame, Touch(touch_x, touch_y) if touch_down else Touch.up))
        pairs.append((frame, Circle(circle_x, circle_y)))
    return pairs


# ---- JSON ----
def to_jsonable(value: Any) -> Any:
    """``value`` as plain JSON data: dataclasses by their fields, paths as text, tuples as lists, dict keys as text.
    Arrays and bytes are not JSON: they are left out of a dict and a list (the ``_SKIP`` marker never escapes)."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _clean({f.name: to_jsonable(getattr(value, f.name)) for f in dataclasses.fields(value)})
    if isinstance(value, dict):
        return _clean({str(k): to_jsonable(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return [v for v in (to_jsonable(item) for item in value) if v is not _SKIP]
    return _SKIP


def _clean(mapping: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in mapping.items() if v is not _SKIP}


def _error_json(exc: BaseException) -> Dict[str, Any]:
    return {"class": type(exc).__name__, "message": str(exc),
            "workdir": to_jsonable(getattr(exc, "workdir", None)), "log_path": to_jsonable(getattr(exc, "log_path", None))}


# ---- run ----
def exit_code_of(exc: BaseException) -> int:
    """The exit code of an error, by USING section 3's table."""
    if isinstance(exc, ArgumentError):
        return EXIT_USAGE
    if isinstance(exc, BootError):
        return EXIT_BOOT
    if isinstance(exc, GuestError):
        return EXIT_GUEST_ERROR
    if isinstance(exc, HostTimeout) and not isinstance(exc, _slots.SlotTimeout):
        return EXIT_TIMEOUT
    return EXIT_CRASHED          # HostCrashed, HostError, StateError, SlotTimeout and any other library error


def _run_once(args: argparse.Namespace, workdir: Path) -> Tuple[RunResult, Optional[Any]]:
    """Boot, run, save; returns the result and the SaveInfo (None unless ``--save``)."""
    inputs = parse_script(args.inputs) if args.inputs else []
    kwargs: Dict[str, Any] = {"state": args.state, "sd_seed": args.sd_seed}
    if args.timeout is not None:
        kwargs["timeout"] = args.timeout
    with Emulator(args.app, workdir, **kwargs) as emu:
        result = emu.run(args.frames, inputs=inputs, shots=args.shot)
        saved = emu.save_state(args.save) if args.save and not emu.closed else None
    return result, saved


def _print_result(result: RunResult, saved: Optional[Any], workdir: Path) -> None:
    print(f"frames={result.frames} stop={result.stopped_by} first={result.first_frame} last={result.last_frame} "
          f"vblanks={result.vblanks} wall={result.wall_s:.3f}")
    for frame in sorted(result.shots):
        shot = result.shots[frame]
        print(f"shot {frame}: {shot.top} {shot.bottom}")
    if saved is not None:
        print(f"saved k={saved.k} frame={saved.frame_total} path={saved.path}")
    print(f"workdir: {workdir}")


def command_run(args: argparse.Namespace) -> int:
    """``run``: boot APP, run ``--frames`` frames, print one summary (or one JSON object); returns the exit code."""
    made = args.workdir is None
    workdir = Path(tempfile.mkdtemp(prefix="libazahar-run-")) if made else Path(args.workdir)
    try:
        result, saved = _run_once(args, workdir)
    except LibAzaharError as exc:
        code = exit_code_of(exc)
        if args.json:
            print(json.dumps({"ok": False, "exit_code": code, "workdir": str(workdir.resolve()), "error": _error_json(exc)}))
        else:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            print(f"workdir: {workdir.resolve()}", file=sys.stderr)
        return code
    code = EXIT_GUEST_EXITED if result.stopped_by == "guest_exited" else EXIT_OK
    if args.json:
        print(json.dumps({"ok": code == EXIT_OK, "exit_code": code, "workdir": str(workdir.resolve()),
                          "result": to_jsonable(result), "saved": to_jsonable(saved)}))
    else:
        _print_result(result, saved, workdir.resolve())
    return code


# ---- doctor ----
def vulkan_lines(log: Path) -> List[str]:
    """The Vulkan device lines of a ``host.log`` (the text after the log prefix); empty when there are none."""
    try:
        text = log.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return [line[line.index("vulkan device:"):].strip() for line in text.splitlines() if "vulkan device:" in line
            and "ready" not in line]


def slot_report() -> Tuple[str, bool]:
    """The slots: how many are in use and the PIDs holding them. Probes by taking every free slot for a moment, so a
    free slot is briefly held. PIDs come from ``lsof`` where it exists, else ``unknown`` (Windows has no stock tool)."""
    cap, folder = _slots.cap(), _slots.slot_dir()
    taken: List[_slots.Slot] = []
    try:
        while len(taken) < cap:
            found = _slots._try_round(folder, cap)
            if found is None:
                break
            taken.append(_slots.Slot(found[0], found[1], found[2], 0.0))
        free = {slot.index for slot in taken}
    finally:
        for slot in taken:
            slot.release()
    lines = [f"{cap - len(free)} of {cap} in use ({folder})"]
    for index in range(cap):
        if index not in free:
            lines.append(f"  slot {index}: pid {_holder_pid(folder / f'slot-{index}.lock')}")
    return "\n".join(lines), True


def _holder_pid(lock: Path) -> str:
    """The pid holding a lock file, via ``lsof -t`` (not on Windows); ``unknown`` when it cannot be told."""
    tool = shutil.which("lsof")
    if tool is None or sys.platform == "win32":
        return "unknown"
    done = subprocess.run([tool, "-t", "--", str(lock)], capture_output=True, text=True, check=False, timeout=20)
    pids = done.stdout.split()
    return ",".join(pids) if pids else "unknown"


def _check_host() -> Tuple[str, bool]:
    path = _paths.host_path()
    lib, layout = _host.load(path)
    del lib
    return f"{path} (abi {layout.abi})", True


def _check_core() -> Tuple[str, bool]:
    core = _paths.core_path()
    if not core.is_file():
        return f"{core} is missing", False
    return f"{core} (version in the boot below)", True


def _check_boot() -> Tuple[List[str], bool]:
    """Boot the test app for 60 frames; returns the report lines and whether it worked."""
    app = _paths.repo_root() / "build" / "testapp.3dsx"
    if not app.is_file():
        return ["skipped (no test app at " + str(app) + ")", "vulkan: unknown"], True
    workdir = Path(tempfile.mkdtemp(prefix="libazahar-doctor-"))
    lines: List[str] = []
    ok = True
    try:
        with Emulator(app, workdir) as emu:
            result = emu.run(DOCTOR_FRAMES)
            stats = emu.stats()
        lines.append(f"{result.frames} frames, stopped by {result.stopped_by}; core {stats.core_name} {stats.core_version}")
        ok = result.frames == DOCTOR_FRAMES
    except LibAzaharError as exc:
        lines.append(f"FAILED: {type(exc).__name__}: {exc}")
        ok = False
    devices = vulkan_lines(workdir / "host.log")
    lines.extend(f"vulkan: {line}" for line in devices or ["unknown"])
    if ok:
        shutil.rmtree(workdir, ignore_errors=True)
    else:
        lines.append(f"kept: {workdir}")
    return lines, ok


def command_doctor(args: argparse.Namespace) -> int:
    """``doctor``: print what works; returns 0 when every part works, else 1."""
    del args
    print(f"libazahar {__version__}; {platform.platform()}; Python {platform.python_version()}")
    ok = True
    for name, check in (("host", _check_host), ("core", _check_core), ("slots", slot_report)):
        try:
            text, part = check()
        except LibAzaharError as exc:
            text, part = f"FAILED: {type(exc).__name__}: {exc}", False
        print(f"{name}: {text}" + ("" if part else "   [FAIL]"))
        ok = ok and part
    if ok:
        lines, part = _check_boot()
        print(f"boot: {lines[0]}" + ("" if part else "   [FAIL]"))
        for line in lines[1:]:
            print(f"  {line}")
        ok = ok and part
    else:
        print("boot: skipped (the host or the core is not usable)\n  vulkan: unknown")
    print("doctor: ok" if ok else "doctor: FAILED")
    return EXIT_OK if ok else EXIT_FAILED


# ---- parser ----
def build_parser() -> argparse.ArgumentParser:
    """The argument parser: ``doctor`` and ``run``."""
    parser = argparse.ArgumentParser(prog="python -m libazahar", description="A headless, scriptable Azahar (docs/USING.md).")
    parser.add_argument("--version", action="version", version=f"libazahar {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="{doctor,run}")
    sub.add_parser("doctor", help="check the host, the core, the slots and a 60-frame boot of the test app",
                   description="Print the OS, Python, host and core, the slots in use and a 60-frame boot of the test app. "
                               "Exit 0 when every part works, else 1.")
    run = sub.add_parser("run", help="boot an app and run frames", description="Boot APP, run --frames frames, print one "
                         "summary (or one JSON object with --json). Exit codes: USING section 3.")
    run.add_argument("app", metavar="APP", help="the .3dsx / .cia / .elf file to run")
    run.add_argument("--frames", type=int, required=True, metavar="N", help="guest frames to run (one frame = one VBlank)")
    run.add_argument("--inputs", type=Path, metavar="FILE", help="an azhost input script (USING section 4a)")
    run.add_argument("--shot", type=int, action="append", default=[], metavar="F", help="save both screens at batch frame F (repeatable)")
    run.add_argument("--state", type=Path, metavar="P", help="boot from this savestate")
    run.add_argument("--save", type=Path, metavar="P", help="save a state here after the run")
    run.add_argument("--json", action="store_true", help="print one JSON object instead of the summary")
    run.add_argument("--workdir", type=Path, metavar="DIR", help="the working folder (default: a new temporary one, kept)")
    run.add_argument("--sd-seed", type=Path, metavar="DIR", help="a folder copied onto the emulated SD card")
    run.add_argument("--timeout", type=float, metavar="S", help="no-progress limit in seconds (default 30)")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the command line; returns the exit code."""
    args = build_parser().parse_args(argv)
    return command_doctor(args) if args.command == "doctor" else command_run(args)
