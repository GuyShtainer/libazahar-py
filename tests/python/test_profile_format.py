"""The option-profile format (USING section 14) and the azhost exit codes (USING section 3).

Every pair in tests/data/profile-cases/ runs through the Python parser; tests/host/test_profile.c runs the same pairs
through the C one. The azhost cases run the real program: the input-script ones stop before the core loads, the rest
need the emulator (slow tier)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from libazahar import ArgumentError
from libazahar import emulator as emu_mod

REPO = Path(__file__).resolve().parents[2]
CASES = REPO / "tests" / "data" / "profile-cases"
NAMES = sorted(p.stem for p in CASES.glob("*.txt"))


def test_case_table_is_there():
    assert len(NAMES) >= 30
    assert all((CASES / f"{n}.expect").is_file() for n in NAMES)


@pytest.mark.parametrize("name", NAMES)
def test_profile_case(name: str):
    path = CASES / f"{name}.txt"
    expect = (CASES / f"{name}.expect").read_bytes().decode("utf-8")
    if expect.startswith("error line "):
        line = int(expect.split()[2])
        with pytest.raises(ArgumentError) as info:
            emu_mod._read_profile(path)
        text = str(info.value)
        assert text.startswith(f"{path}:{line}: "), text        # the exact line number, never 0 (decision D-d)
        return
    pairs = emu_mod._read_profile(path)
    assert "".join(f"{k}={v}\n" for k, v in pairs) == expect


def azhost(*args: str, cwd: Path = REPO, timeout: int = 300) -> subprocess.CompletedProcess:
    exe = REPO / "build" / "azhost"
    if not exe.is_file():
        pytest.skip("build/azhost is missing (run make)")
    return subprocess.run(["nice", "-n", "10", str(exe), *args], cwd=cwd, capture_output=True, text=True,
                          timeout=timeout)


def run_args(workdir: Path, *more: str) -> list:
    return ["run", str(REPO / "build" / "testapp.3dsx"), "--sys", str(workdir / "sys"), "--out", str(workdir / "out"),
            "--frames", "1", *more]


@pytest.mark.parametrize("text,fragment", [
    ("1 0 0 0 0 0\n", "line 1"),                                  # six integers
    ("1 0 0 0 0 0 0 junk\n", "line 1"),                           # trailing junk
    ("# ok\n\n1 0x 0 0 0 0 0\n", "line 3"),                       # a hex prefix with no digits
    ("1 +5 0 0 0 0 0\n", "line 1"),                               # a plus sign
    ("1 0 0 0 0 0 0 # " + "x" * 600 + "\n", "longer than 511"),   # one long comment line
    ("# " + "x" * 600 + "\n", "longer than 511"),
])
def test_cli_input_script_refused(tmp_path: Path, text: str, fragment: str):
    script = tmp_path / "in.txt"
    script.write_text(text)
    res = azhost(*run_args(tmp_path, "--inputs", str(script)))
    assert res.returncode == 2, res.stderr
    assert "UsageError" in res.stderr and fragment in res.stderr, res.stderr


def test_cli_missing_input_script_exits_6(tmp_path: Path):
    res = azhost(*run_args(tmp_path, "--inputs", str(tmp_path / "nope.txt")))
    assert res.returncode == 6, res.stderr
    assert "IOError" in res.stderr


@pytest.mark.slow
def test_cli_bad_profile_line_exits_2(host_paths, tmp_path: Path):
    profile = tmp_path / "p.txt"
    profile.write_text("# fine\nbogus line\n")
    res = azhost(*run_args(tmp_path, "--core", str(host_paths.core), "--profile", str(profile)))
    assert res.returncode == 2, res.stderr
    assert f"UsageError: {profile} line 2:" in res.stderr, res.stderr


@pytest.mark.slow
def test_cli_unknown_key_in_profile_names_the_line(host_paths, tmp_path: Path):
    profile = tmp_path / "p.txt"
    profile.write_text("# fine\nno_such_option_key=1\n")
    res = azhost(*run_args(tmp_path, "--core", str(host_paths.core), "--profile", str(profile)))
    assert res.returncode == 2, res.stderr
    assert f"{profile} line 2:" in res.stderr, res.stderr


@pytest.mark.slow
def test_cli_missing_profile_exits_6(host_paths, tmp_path: Path):
    res = azhost(*run_args(tmp_path, "--core", str(host_paths.core), "--profile", str(tmp_path / "nope.txt")))
    assert res.returncode == 6, res.stderr


@pytest.mark.slow
def test_cli_bad_opt_exits_2(host_paths, tmp_path: Path):
    res = azhost(*run_args(tmp_path, "--core", str(host_paths.core), "--opt", " padded=1"))
    assert res.returncode == 2, res.stderr


@pytest.mark.slow
def test_cli_missing_state_exits_9(host_paths, tmp_path: Path):
    res = azhost(*run_args(tmp_path, "--core", str(host_paths.core), "--state", str(tmp_path / "nope.state")))
    assert res.returncode == 9, res.stderr
    assert "StateError" in res.stderr, res.stderr


@pytest.mark.slow
def test_cli_debug_stop_on_stock_core_exits_7(stock_core, host_paths, tmp_path: Path):
    res = azhost(*run_args(tmp_path, "--core", str(stock_core), "--debug-stop", "ready"))
    assert res.returncode == 7, res.stderr


# ---- the input-script rules (decision D-g); the accepted ones go on to the record check, which needs the core ----

def _script_run(host_paths, tmp_path: Path, data: bytes):
    script = tmp_path / "in.txt"
    script.write_bytes(data)
    return azhost(*run_args(tmp_path, "--core", str(host_paths.core), "--inputs", str(script)))


@pytest.mark.slow
@pytest.mark.parametrize("data", [
    b"5 0 0 0 0 0 0 #" + b"x" * 496 + b"\r\n",        # exactly 511 bytes then CRLF: accepted (the record is refused later)
    b"0X5 0 0 0 0 0 0\n",                              # an upper-case prefix is a hex number
])
def test_cli_input_script_accepted(host_paths, tmp_path: Path, data: bytes):
    assert len(data.split(b"\r")[0]) <= 511
    res = _script_run(host_paths, tmp_path, data)
    assert res.returncode == 2, res.stderr
    assert "input record 0: frame" in res.stderr, res.stderr    # it parsed; frame 5 is outside 1..1


@pytest.mark.parametrize("data,fragment", [
    (b"5 0 0 0 0 0 0 #" + b"x" * 497 + b"\r\n", "line 1: line longer than 511"),   # 512 bytes then CRLF
    (b"# ok\n1 0x0x10 0 0 0 0 0\n", "line 2"),                                     # two prefixes
    (b"# ok\n# a\x00b\n", "line 2: NUL byte"),
])
def test_cli_input_script_refused_late(tmp_path: Path, data: bytes, fragment: str):
    script = tmp_path / "in.txt"
    script.write_bytes(data)
    res = azhost(*run_args(tmp_path, "--inputs", str(script)))
    assert res.returncode == 2, res.stderr
    assert "UsageError" in res.stderr and fragment in res.stderr, res.stderr


@pytest.mark.slow
def test_cli_input_script_line_bound(host_paths, tmp_path: Path):
    """The 4,000,000th line is fine; data after it is an error, never a silent cut."""
    ok = b"# c\n" * 3_999_999 + b"5 0 0 0 0 0 0\n"
    res = _script_run(host_paths, tmp_path, ok)
    assert "input record 0: frame" in res.stderr, res.stderr[:300]
    res = _script_run(host_paths, tmp_path, ok + b"# c\n")
    assert res.returncode == 2, res.stderr
    assert "line 4000001: more than 4000000 lines" in res.stderr, res.stderr[:300]


# ---- exit codes (decision D-f and the review's item 10) ----

def test_cli_missing_seed_folder_exits_2(tmp_path: Path):
    res = azhost(*run_args(tmp_path, "--sd-seed", str(tmp_path / "no-such-seed")))
    assert res.returncode == 2, res.stderr
    assert "UsageError" in res.stderr, res.stderr


def test_cli_seed_copy_failure_exits_6(tmp_path: Path):
    seed = tmp_path / "seed"
    seed.mkdir()
    (seed / "f").write_text("x")
    (seed / "f").chmod(0)
    try:
        res = azhost(*run_args(tmp_path, "--sd-seed", str(seed)))
    finally:
        (seed / "f").chmod(0o600)
    assert res.returncode == 6, res.stderr
    assert "IOError" in res.stderr, res.stderr


@pytest.mark.slow
def test_cli_save_write_failure_exits_6(host_paths, tmp_path: Path):
    blocker = tmp_path / "blocker"
    blocker.write_text("a file, so nothing can be made under it")
    res = azhost(*run_args(tmp_path, "--core", str(host_paths.core), "--save", str(blocker / "x.state")))
    assert res.returncode == 6, res.stderr
    assert "cannot write" in res.stderr or "IOError" in res.stderr, res.stderr


@pytest.mark.slow
def test_cli_load_failure_exits_9(host_paths, tmp_path: Path):
    bad = tmp_path / "bad.state"
    bad.write_bytes(b"not a state file")
    res = azhost(*run_args(tmp_path, "--core", str(host_paths.core), "--state", str(bad)))
    assert res.returncode == 9, res.stderr
    assert "StateError" in res.stderr, res.stderr
