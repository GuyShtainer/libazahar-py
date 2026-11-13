"""The option-profile parser's rules one by one (no emulator). The shared case table is test_profile_format.py."""
from __future__ import annotations

import pytest

from libazahar import ArgumentError, HostError
from libazahar.emulator import _read_profile


def parse(tmp_path, data: bytes):
    path = tmp_path / "profile.txt"
    path.write_bytes(data)
    return _read_profile(path)


def test_pairs_comments_and_blank_lines(tmp_path):
    data = b"# comment\n\ncitra_is_new_3ds=New 3DS\nempty=\nk=a=b\nx=# not a comment\n"
    assert parse(tmp_path, data) == [("citra_is_new_3ds", "New 3DS"), ("empty", ""), ("k", "a=b"), ("x", "# not a comment")]


def test_crlf_and_a_last_line_without_newline(tmp_path):
    assert parse(tmp_path, b"a=1\r\nb=2") == [("a", "1"), ("b", "2")]


def test_only_newline_splits_lines(tmp_path):
    assert parse(tmp_path, "a=x y\x0bz\n".encode()) == [("a", "x y\x0bz")]


@pytest.mark.parametrize("data,line", [
    (b"a=1\n b=2\n", 2), (b"a=1 \n", 1), (b"\ta=1\n", 1), (b"a=1\n  # indented\n", 2), (b"novalue\n", 1),
    (b"=v\n", 1), (b"a b=c\n", 1), (b"ok=1\n# c\nbad\xff=1\n", 3), (b"a=" + b"x" * 509 + b"\n\n" + b"b=" + b"x" * 510 + b"\n", 3)])
def test_bad_lines_name_the_line(tmp_path, data, line):
    with pytest.raises(ArgumentError, match=rf"profile\.txt:{line}: "):
        parse(tmp_path, data)


def test_line_limits(tmp_path):
    assert parse(tmp_path, b"k=" + b"x" * 509 + b"\n")[0][1] == "x" * 509          # 511 bytes: allowed
    with pytest.raises(ArgumentError, match=r":1: "):
        parse(tmp_path, b"k=" + b"x" * 510 + b"\n")                                 # 512 bytes
    assert len(parse(tmp_path, b"a=1\n" * 4096)) == 4096
    with pytest.raises(ArgumentError, match=r":0: "):
        parse(tmp_path, b"a=1\n" * 4097)
    with pytest.raises(ArgumentError, match=r":0: "):
        parse(tmp_path, b"#\n" * 4097)


def test_unreadable_file_is_host_error(tmp_path):
    with pytest.raises(HostError, match="no-such"):
        _read_profile(tmp_path / "no-such.txt")
    with pytest.raises(HostError):
        _read_profile(tmp_path)                       # a folder
