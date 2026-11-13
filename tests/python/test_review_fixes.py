"""Fixes after the V1 diff review: options= pair rule, bad numbers, workdir errors, pickling (no emulator)."""
from __future__ import annotations

import pickle
from pathlib import Path

import pytest

from libazahar import ArgumentError, Emulator, HostError, errors
from libazahar.emulator import _pairs


@pytest.mark.parametrize("key,value", [
    (" k", "v"), ("k", "v "), ("", "v"), ("a b", "v"), ("a=b", "v"), ("k", "a\x00b"), ("k", "a\nb"), ("k", "v\r"),
    ("k", "\udcff"), ("k", "x" * 600), ("#k", "v"), ("﻿k", "v")])
def test_options_pairs_follow_the_line_rule(key, value):
    with pytest.raises(ArgumentError, match="options"):
        _pairs({key: value})


def test_good_options_pairs_pass():
    assert _pairs({"a": "1", "b": 2, "c": ""}) == [("a", "1"), ("b", "2"), ("c", "")]
    assert _pairs([("k", "a=b"), ("k", "x y")]) == [("k", "a=b"), ("k", "x y")]


def test_bad_stop_every_and_numbers():
    from libazahar.emulator import Emulator as E
    from libazahar import _abi
    for bad in (1.5, True, "3"):
        with pytest.raises(ArgumentError):
            E._fill_stops(_abi.Batch(), "f", "t", bad, False, None, None)
    for bad in ("5", True, float("nan"), [1]):
        with pytest.raises(ArgumentError):
            E._fill_stops(_abi.Batch(), None, None, 30, False, None, bad)
    for bad in ("5", None, True):
        with pytest.raises(ArgumentError):
            Emulator(__file__, Path("/nonexistent-x"), timeout=bad)  # type: ignore[arg-type]


def test_unwritable_workdir_is_host_error(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    with pytest.raises(HostError, match="file"):
        Emulator(__file__, blocker / "work")


def _make(cls):
    if cls is errors.HostTimeout:
        return cls("run", 2.5, "last msg")
    if cls is errors.SlotTimeout:
        return cls(1.5, 4, Path("/tmp/slots"))
    if cls is errors.HostCrashed:
        return cls(-11, 11, "m", "log", "err")
    if cls is errors.GuestError:
        return cls("boom", None)
    if cls is errors.GuestMemoryError:
        return cls("unmapped", 0x1000, 8)
    return cls("some text")


@pytest.mark.parametrize("name", errors.__all__)
def test_every_error_pickles(name):
    cls = getattr(errors, name)
    exc = _make(cls)
    back = pickle.loads(pickle.dumps(exc))
    assert type(back) is cls and str(back) == str(exc) and back.args == exc.args
    for attr, value in vars(exc).items():
        assert getattr(back, attr) == value
