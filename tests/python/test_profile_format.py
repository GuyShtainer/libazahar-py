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
        assert text.startswith(f"{path}:{line}:") or (line == 0 and str(path) in text), text
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
