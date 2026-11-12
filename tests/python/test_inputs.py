"""Buttons, Touch, Circle and the fold (no emulator)."""
import pytest

from libazahar.inputs import Buttons, Circle, Held, Touch, fold, held_after

LIBCTRU = {"A": 1, "B": 2, "SELECT": 4, "START": 8, "DRIGHT": 16, "DLEFT": 32, "DUP": 64, "DDOWN": 128, "R": 256,
           "L": 512, "X": 1024, "Y": 2048, "ZL": 16384, "ZR": 32768}


def test_buttons_equal_libctru_bits():
    for name, value in LIBCTRU.items():
        assert int(Buttons[name]) == value, name
    assert Buttons.RIGHT == Buttons.DRIGHT and Buttons.UP == Buttons.DUP


def rows(array):
    return [tuple(array[i:i + 7]) for i in range(0, len(array), 7)]


def test_each_item_changes_only_its_part():
    out, held = fold([(1, Buttons.A | Buttons.B), (2, Touch(10, 20)), (3, Circle(100, -50)), (4, Touch.up)], 10, Held())
    assert rows(out) == [(1, 3, 0, 0, 0, 0, 0), (2, 3, 10, 20, 1, 0, 0), (3, 3, 10, 20, 1, 100, -50),
                         (4, 3, 10, 20, 0, 100, -50)]
    assert held == Held(3, 10, 20, 0, 100, -50)


def test_same_frame_folds_to_one_record_and_input_is_sorted():
    out, _ = fold([(5, Touch(1, 2)), (2, Buttons.X), (5, 4)], 10, Held())
    assert rows(out) == [(2, 1024, 0, 0, 0, 0, 0), (5, 4, 1, 2, 1, 0, 0)]


def test_held_carries_in():
    out, _ = fold([(1, Touch(5, 6))], 3, Held(buttons=8))
    assert rows(out) == [(1, 8, 5, 6, 1, 0, 0)]


@pytest.mark.parametrize("bad", [(0, Buttons.A), (11, Buttons.A), (1, 0x10000), (1, 1 << 12), (1, Touch(320, 0)),
                                 (1, Touch(0, 240)), (1, Touch(-1, 0)), (1, Circle(32768, 0)), (1, Circle(0, -32768)),
                                 (1, "A"), (1, 2.5)])
def test_validation_errors(bad):
    with pytest.raises(ValueError):
        fold([bad], 10, Held())


def test_held_after_an_early_stop():
    out, _ = fold([(2, Buttons.A), (50, Touch(5, 6))], 100, Held())
    assert held_after(out, 10, Held()) == Held(buttons=1)
    assert held_after(out, 50, Held()) == Held(1, 5, 6, 1, 0, 0)
    assert held_after(out, 1, Held(buttons=8)) == Held(buttons=8)
