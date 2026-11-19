"""The command line (libazahar._cli) against a fake Emulator: fast, no emulator. One live run of each command is at the end."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from libazahar import (BootError, Buttons, Circle, GuestError, HostCrashed, HostError, HostTimeout, RunResult, Shot,
                       SlotTimeout, StateError, Touch, _cli, errors)
from libazahar.results import SaveInfo

REPO = Path(__file__).resolve().parents[2]


class FakeEmu:
    """Stands in for Emulator: records its call and plays one scripted outcome (a RunResult or an exception)."""

    outcome = None
    last = None

    def __init__(self, app, workdir, **kwargs):
        FakeEmu.last = self
        self.app, self.workdir, self.kwargs, self.ran, self.closed = app, Path(workdir), kwargs, None, False
        if isinstance(FakeEmu.outcome, BaseException) and getattr(FakeEmu.outcome, "at_boot", False):
            raise FakeEmu.outcome

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.closed = True

    def run(self, frames, **kwargs):
        self.ran = (frames, kwargs)
        if isinstance(FakeEmu.outcome, BaseException):
            raise FakeEmu.outcome
        if FakeEmu.outcome is not None:
            if FakeEmu.outcome.stopped_by == "guest_exited":
                self.closed = True          # like the real Emulator: the guest is gone, so there is nothing to save
            return FakeEmu.outcome
        shots = {f: Shot(f, Path(f"shots/a{f}_top.png"), Path(f"shots/a{f}_bottom.png"), f) for f in kwargs["shots"]}
        return RunResult(frames=frames, stopped_by="frames", first_frame=1, last_frame=frames, frame_total=frames,
                         vblanks=frames, wall_s=0.5, shots=shots)

    def save_state(self, path):
        return SaveInfo(Path(path), 2, 12)


@pytest.fixture(autouse=True)
def fake(monkeypatch):
    FakeEmu.outcome, FakeEmu.last = None, None
    monkeypatch.setattr(_cli, "Emulator", FakeEmu)


def run_cli(capsys, *argv):
    code = _cli.main(list(argv))
    out = capsys.readouterr()
    return code, out.out, out.err


# ---- the script parser: the examples of USING 4a ----
def script(tmp_path, text):
    path = tmp_path / "in.txt"
    path.write_bytes(text.encode())
    return path


def test_script_whole_state_becomes_items(tmp_path):
    path = script(tmp_path, "# a comment\n\n1 0x1 0 0 0 0 0\n30, 0, 10\t20, 1, -5, 0x7FFF  # touch\r\n")
    assert _cli.parse_script(path) == [
        (1, Buttons.A), (1, Touch.up), (1, Circle(0, 0)),
        (30, Buttons(0)), (30, Touch(10, 20)), (30, Circle(-5, 0x7FFF))]


def test_script_leading_zero_is_decimal_and_hex_is_hex(tmp_path):
    (_, first), = [p for p in _cli.parse_script(script(tmp_path, "5 010 0 0 0 0 0\n")) if isinstance(p[1], Buttons)]
    (_, second), = [p for p in _cli.parse_script(script(tmp_path, "5 0x10 0 0 0 0 0\n")) if isinstance(p[1], Buttons)]
    assert int(first) == 10 and int(second) == 16


@pytest.mark.parametrize("text, match", [
    ("1 2 3\n", r"line 1: expected 7 fields, got 3"),
    ("\n1 0x0x10 0 0 0 0 0\n", r"line 2: .*0x0x10"),
    ("1 0 0 0 0 0 99999999999\n", r"line 1: .*int32"),
    ("1 0 0 0 0 0 0 0\n", r"line 1: expected 7 fields"),
    ("1 0 0 0 0 0 0\x00\n", r"line 1: NUL"),
    ("1 0 0 0 0 0 0 #" + "x" * 520 + "\n", r"line 1: the line is .* over the 511"),
])
def test_script_bad_lines_name_the_line(tmp_path, text, match):
    with pytest.raises(errors.ArgumentError, match=match):
        _cli.parse_script(script(tmp_path, text))


def test_script_unreadable_is_an_argument_error(tmp_path):
    with pytest.raises(errors.ArgumentError, match="cannot read the input script"):
        _cli.parse_script(tmp_path / "missing.txt")


# ---- JSON ----
def test_to_jsonable_drops_arrays_and_bytes_and_keeps_the_rest():
    import array
    assert _cli.to_jsonable({"a": b"x", "b": array.array("h", [1]), "c": (1, b"y", "z"), "d": Path("p")}) == \
        {"c": [1, "z"], "d": "p"}


def test_every_runresult_field_reaches_the_json(tmp_path, capsys):
    import dataclasses
    code, out, _ = run_cli(capsys, "run", "app.3dsx", "--frames", "3", "--shot", "2", "--json", "--workdir", str(tmp_path))
    assert code == 0
    result = json.loads(out)["result"]
    wanted = {f.name for f in dataclasses.fields(RunResult)}
    assert set(result) == wanted
    assert Path(result["shots"]["2"]["top"]) == Path("shots/a2_top.png")


# ---- run ----
def test_run_passes_the_options(tmp_path, capsys):
    inputs = script(tmp_path, "2 0x1 0 0 0 0 0\n")
    code, out, _ = run_cli(capsys, "run", "a.3dsx", "--frames", "5", "--inputs", str(inputs), "--shot", "1", "--shot", "5",
                           "--state", "s", "--timeout", "7", "--workdir", str(tmp_path / "w"), "--save", "st")
    frames, kwargs = FakeEmu.last.ran
    assert code == 0 and frames == 5 and kwargs["shots"] == [1, 5]
    assert kwargs["inputs"][0] == (2, Buttons.A)
    assert FakeEmu.last.kwargs == {"state": Path("s"), "sd_seed": None, "timeout": 7.0}
    assert "frames=5 stop=frames" in out and "shot 5:" in out and "saved k=2 frame=12" in out


def test_run_json_success_keys(tmp_path, capsys):
    code, out, _ = run_cli(capsys, "run", "a", "--frames", "2", "--json", "--workdir", str(tmp_path), "--save", "st")
    body = json.loads(out)
    assert code == 0 and body["ok"] is True and body["exit_code"] == 0 and body["workdir"] == str(tmp_path.resolve())
    assert body["saved"] == {"path": "st", "k": 2, "frame_total": 12}


def err(cls, *args, evidence=True):
    exc = cls(*args)
    if evidence:
        exc.workdir, exc.log_path = Path("/w"), Path("/w/host.log")
    return exc


@pytest.mark.parametrize("exc, code", [
    (errors.ArgumentError("bad"), 2),
    (err(BootError, "no boot"), 3),
    (err(GuestError, "fatal"), 11),
    (err(HostTimeout, "run", 3.0), 12),
    (err(HostCrashed, -11, 11), 13),
    (err(HostError, "no host"), 13),
    (err(StateError, "bad state"), 13),
    (SlotTimeout(1.0, 2, Path("/slots")), 13),
])
def test_exit_codes_by_the_table(exc, code, tmp_path, capsys):
    FakeEmu.outcome = exc
    got, out, _ = run_cli(capsys, "run", "a", "--frames", "2", "--json", "--workdir", str(tmp_path))
    body = json.loads(out)
    assert got == code == body["exit_code"] and body["ok"] is False
    expected = None if exc.workdir is None else str(exc.workdir)
    assert body["error"]["class"] == type(exc).__name__ and body["error"]["workdir"] == expected and "message" in body["error"]
    assert body["error"]["log_path"] == (None if exc.log_path is None else str(exc.log_path))


def test_error_without_json_goes_to_stderr(tmp_path, capsys):
    FakeEmu.outcome = err(BootError, "no boot")
    code, out, errtext = run_cli(capsys, "run", "a", "--frames", "2", "--workdir", str(tmp_path))
    assert code == 3 and out == "" and errtext.startswith("BootError: no boot")


def test_guest_exit_is_code_10(tmp_path, capsys):
    FakeEmu.outcome = RunResult(frames=4, stopped_by="guest_exited", first_frame=1, last_frame=4, frame_total=4, vblanks=4, wall_s=0.0)
    code, out, _ = run_cli(capsys, "run", "a", "--frames", "9", "--json", "--workdir", str(tmp_path), "--save", "st")
    body = json.loads(out)
    assert code == 10 and body["result"]["stopped_by"] == "guest_exited"
    assert body["ok"] is False and body["exit_code"] == 10 and body["saved"] is None and "error" not in body
    assert FakeEmu.last.closed


def test_bad_script_exits_2(tmp_path, capsys):
    code, _, errtext = run_cli(capsys, "run", "a", "--frames", "2", "--inputs", str(script(tmp_path, "1 2\n")), "--workdir", str(tmp_path))
    assert code == 2 and "expected 7 fields" in errtext and FakeEmu.last is None


def test_missing_script_exits_2_and_makes_no_folder(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    code, _, errtext = run_cli(capsys, "run", "a", "--frames", "2", "--inputs", str(tmp_path / "none.txt"))
    assert code == 2 and "cannot read the input script" in errtext and FakeEmu.last is None
    assert list(tmp_path.iterdir()) == []


def test_default_workdir_is_made_after_the_script_and_kept(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    code, out, _ = run_cli(capsys, "run", "a", "--frames", "2", "--json")
    folder = Path(json.loads(out)["workdir"])
    assert code == 0 and folder.is_dir() and folder.parent.resolve() == tmp_path.resolve()
    code, out, _ = run_cli(capsys, "run", "a", "--frames", "2", "--inputs", str(script(tmp_path, "1 2\n")), "--json")
    body = json.loads(out)
    assert code == 2 and body["workdir"] is None and len(list(tmp_path.glob("libazahar-run-*"))) == 1


@pytest.mark.parametrize("argv", [["--frames", "0"], ["--frames", "-3"], ["--frames", "2", "--shot", "0"]])
def test_non_positive_counts_exit_2_before_any_boot(argv, capsys):
    with pytest.raises(SystemExit) as caught:
        _cli.main(["run", "a", *argv])
    assert caught.value.code == 2 and FakeEmu.last is None
    capsys.readouterr()


def test_shot_or_input_frame_beyond_the_batch_exits_2_before_any_boot(tmp_path, capsys):
    code, _, errtext = run_cli(capsys, "run", "a", "--frames", "3", "--shot", "4", "--workdir", str(tmp_path / "w"))
    assert code == 2 and "--shot 4" in errtext and FakeEmu.last is None
    code, _, errtext = run_cli(capsys, "run", "a", "--frames", "3", "--inputs", str(script(tmp_path, "9 0 0 0 0 0 0\n")),
                               "--workdir", str(tmp_path / "w"))
    assert code == 2 and "frame 9" in errtext and FakeEmu.last is None and not (tmp_path / "w").exists()


def test_a_folder_that_cannot_be_made_exits_13_not_a_traceback(tmp_path, capsys):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    FakeEmu.outcome = PermissionError(13, "Permission denied")
    code, out, _ = run_cli(capsys, "run", "a", "--frames", "2", "--json", "--workdir", str(blocker))
    body = json.loads(out)
    assert code == 13 == body["exit_code"] and body["ok"] is False and body["error"]["class"] == "PermissionError"
    code, _, errtext = run_cli(capsys, "run", "a", "--frames", "2", "--workdir", str(blocker))
    assert code == 13 and errtext.startswith("PermissionError:")


def test_usage_errors_exit_2(capsys):
    for argv in (["run", "a"], ["run", "a", "--frames", "x"], [], ["bogus"]):
        with pytest.raises(SystemExit) as caught:
            _cli.main(argv)
        assert caught.value.code == 2
    capsys.readouterr()


def test_help_works_on_both_commands(capsys):
    for argv in (["--help"], ["doctor", "--help"], ["run", "--help"]):
        with pytest.raises(SystemExit) as caught:
            _cli.main(argv)
        assert caught.value.code == 0
    out = capsys.readouterr().out
    assert "--frames" in out and "doctor" in out


# ---- doctor (no emulator: the boot part is skipped without the test app) ----
def test_doctor_reports_the_parts_and_fails_without_a_host(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("LAZ_ROOT", str(tmp_path))
    monkeypatch.delenv("LAZ_HOST", raising=False)
    monkeypatch.setenv("LAZ_SLOT_DIR", str(tmp_path / "slots"))
    monkeypatch.setenv("LAZ_MAX_INSTANCES", "2")
    code, out, _ = run_cli(capsys, "doctor")
    assert code == 1 and "host: FAILED: HostError" in out and "[FAIL]" in out
    assert "slots: 0 of 2 in use" in out and "vulkan: unknown" in out and out.rstrip().endswith("doctor: FAILED")


def test_doctor_counts_a_held_slot(tmp_path, monkeypatch):
    monkeypatch.setenv("LAZ_SLOT_DIR", str(tmp_path / "slots"))
    monkeypatch.setenv("LAZ_MAX_INSTANCES", "2")
    from libazahar import _slots
    with _slots.acquire(1.0) as held:
        text, ok = _cli.slot_report()
    assert ok and text.splitlines()[0].startswith("1 of 2 in use")
    line = next(l for l in text.splitlines() if l.startswith(f"  slot {held.index}:"))
    if shutil.which("lsof") and sys.platform != "win32":
        assert line == f"  slot {held.index}: pid {os.getpid()}"
    else:
        assert line.endswith("pid unknown")
    # the probe let go of every slot it tried: both are free again
    with _slots.acquire(0.0) as first, _slots.acquire(0.0) as second:
        assert {first.index, second.index} == {0, 1}


def test_doctor_probe_holds_at_most_one_slot_at_a_time(tmp_path, monkeypatch):
    monkeypatch.setenv("LAZ_SLOT_DIR", str(tmp_path / "slots"))
    monkeypatch.setenv("LAZ_MAX_INSTANCES", "3")
    from libazahar import _slots
    seen = []
    real = _cli._slot_is_free

    def spy(folder, index):
        free = real(folder, index)
        # right after one probe returns, nothing is held: all 3 slots can be taken at once
        with _slots.acquire(0.0) as a, _slots.acquire(0.0) as b, _slots.acquire(0.0) as c:
            seen.append({a.index, b.index, c.index})
        return free

    monkeypatch.setattr(_cli, "_slot_is_free", spy)
    text, _ = _cli.slot_report()
    assert text.startswith("0 of 3 in use") and seen == [{0, 1, 2}] * 3


def test_holder_pid_survives_a_slow_or_broken_lsof(monkeypatch, tmp_path):
    if sys.platform == "win32":
        pytest.skip("no lsof on Windows: the answer is always unknown")
    monkeypatch.setattr(shutil, "which", lambda name: "/bin/lsof")
    for exc in (subprocess.TimeoutExpired("lsof", 20), PermissionError(13, "no")):
        def boom(*a, _exc=exc, **k):
            raise _exc
        monkeypatch.setattr(subprocess, "run", boom)
        assert _cli._holder_pid(tmp_path / "slot-0.lock") == "unknown"


def test_doctor_without_a_boot_says_so_in_the_last_line(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(_cli, "_check_host", lambda: ("host", True))
    monkeypatch.setattr(_cli, "_check_core", lambda: ("core", True))
    monkeypatch.setattr(_cli, "slot_report", lambda: ("0 of 1 in use", True))
    monkeypatch.setattr(_cli._paths, "repo_root", lambda: tmp_path)
    code, out, _ = run_cli(capsys, "doctor")
    assert code == 0 and out.rstrip().endswith("doctor: ok (boot skipped: no test app)")


def test_vulkan_lines(tmp_path):
    log = tmp_path / "host.log"
    log.write_text('[info] negotiation: version 2\n[info] vulkan device: index=0 of 2 name="GPU A" type=2\n'
                   '[info] vulkan device ready, queue family 0\n')
    assert _cli.vulkan_lines(log) == ['vulkan device: index=0 of 2 name="GPU A" type=2']
    assert _cli.vulkan_lines(tmp_path / "none.log") == []


# ---- live (needs the host, a core and the test app) ----
def module_run(*argv, cwd):
    env = dict(os.environ, PYTHONPATH=str(REPO / "python"))
    return subprocess.run([sys.executable, "-m", "libazahar", *argv], capture_output=True, text=True, env=env, cwd=cwd,
                          timeout=600, check=False)


@pytest.mark.slow
def test_live_run_json(host_paths, tmp_path):
    done = module_run("run", str(host_paths.app), "--frames", "30", "--shot", "30", "--json", "--workdir", str(tmp_path / "w"), cwd=tmp_path)
    assert done.returncode == 0, done.stderr
    body = json.loads(done.stdout)
    assert body["ok"] and body["result"]["frames"] == 30 and body["result"]["stopped_by"] == "frames"
    assert Path(body["result"]["shots"]["30"]["top"]).is_file()


@pytest.mark.slow
def test_live_doctor(host_paths, tmp_path):
    done = module_run("doctor", cwd=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "boot: 60 frames" in done.stdout and "doctor: ok" in done.stdout
    print(done.stdout)
