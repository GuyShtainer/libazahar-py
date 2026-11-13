"""Inputs: buttons (libctru names and bits), touch, circle pad, and the movie fold of docs/plans/phase-c.md 3.4."""
from __future__ import annotations

import enum
from array import array
from dataclasses import dataclass, replace
from typing import ClassVar, Iterable, Tuple, Union

from . import _abi
from .errors import ArgumentError

__all__ = ["Buttons", "Touch", "Circle", "Held", "fold", "held_after"]

TOUCH_W = 320
TOUCH_H = 240


class Buttons(enum.IntFlag):
    """libctru KEY_* bits. The whole mask is held state: a Buttons value replaces all held buttons."""

    A = 1 << 0
    B = 1 << 1
    SELECT = 1 << 2
    START = 1 << 3
    DRIGHT = 1 << 4
    DLEFT = 1 << 5
    DUP = 1 << 6
    DDOWN = 1 << 7
    R = 1 << 8
    L = 1 << 9
    X = 1 << 10
    Y = 1 << 11
    ZL = 1 << 14
    ZR = 1 << 15
    RIGHT = 1 << 4
    LEFT = 1 << 5
    UP = 1 << 6
    DOWN = 1 << 7


@dataclass(frozen=True)
class Touch:
    """Touch the bottom screen at pixel (x, y): x 0..319, y 0..239. ``Touch.up`` lifts the stylus."""

    x: int
    y: int
    up: ClassVar["_TouchUp"]


class _TouchUp:
    """The lift-off marker (``Touch.up``)."""

    def __repr__(self) -> str:
        return "Touch.up"


Touch.up = _TouchUp()


@dataclass(frozen=True)
class Circle:
    """Circle pad position, -32767..32767 each, y positive is up."""

    x: int
    y: int


@dataclass(frozen=True)
class Held:
    """The whole held input state (what one record carries)."""

    buttons: int = 0
    touch_x: int = 0
    touch_y: int = 0
    touch_down: int = 0
    circle_x: int = 0
    circle_y: int = 0

    def as_record(self, frame: int) -> Tuple[int, ...]:
        """The 7-int record for ``frame`` (order of AZH_IN_*)."""
        return (frame, self.buttons, self.touch_x, self.touch_y, self.touch_down, self.circle_x, self.circle_y)


Item = Union[Buttons, int, Touch, Circle, _TouchUp]


def _check_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ArgumentError(f"{name} must be an integer, got {value!r}")
    return int(value)


def check_buttons(value: int) -> int:
    """Validate a button mask; returns it as a plain int."""
    mask = _check_int(value, "buttons")
    if mask < 0 or mask & ~_abi.AZH_BUTTONS_MASK:
        raise ArgumentError(f"buttons {mask:#x} has a bit outside the mask {_abi.AZH_BUTTONS_MASK:#x}")
    return mask


def check_touch(x: int, y: int) -> Tuple[int, int]:
    """Validate a touch point."""
    xi, yi = _check_int(x, "touch x"), _check_int(y, "touch y")
    if not 0 <= xi < TOUCH_W:
        raise ArgumentError(f"touch x {xi} must be 0..{TOUCH_W - 1}")
    if not 0 <= yi < TOUCH_H:
        raise ArgumentError(f"touch y {yi} must be 0..{TOUCH_H - 1}")
    return xi, yi


def check_circle(x: int, y: int) -> Tuple[int, int]:
    """Validate a circle pad position."""
    lim = _abi.AZH_CIRCLE_MAX
    xi, yi = _check_int(x, "circle x"), _check_int(y, "circle y")
    if not -lim <= xi <= lim or not -lim <= yi <= lim:
        raise ArgumentError(f"circle ({xi}, {yi}) must be within -{lim}..{lim}")
    return xi, yi


def apply_item(held: Held, item: Item) -> Held:
    """The held state after one input item; each kind changes only its own part."""
    if isinstance(item, Touch):
        x, y = check_touch(item.x, item.y)
        return replace(held, touch_x=x, touch_y=y, touch_down=1)
    if isinstance(item, _TouchUp):
        return replace(held, touch_down=0)
    if isinstance(item, Circle):
        x, y = check_circle(item.x, item.y)
        return replace(held, circle_x=x, circle_y=y)
    if isinstance(item, (int, Buttons)):
        return replace(held, buttons=check_buttons(int(item)))
    raise ArgumentError(f"unknown input item {item!r}")


def fold(inputs: Iterable[Tuple[int, Item]], frames: int, held: Held) -> Tuple["array[int]", Held]:
    """Fold (frame, item) pairs into one full record per frame that has an item.

    Frames are 1-based within the batch and sorted stably; several items on one frame fold into one record.
    Returns the flat ``array('i')`` of 7-int records and the held state after the last one. Raises ArgumentError for a
    frame outside 1..frames or an invalid item.
    """
    pairs = []
    for pair in inputs:
        frame, item = pair
        frame = _check_int(frame, "input frame")
        if not 1 <= frame <= frames:
            raise ArgumentError(f"input frame {frame} is outside 1..{frames}")
        pairs.append((frame, item))
    pairs.sort(key=lambda p: p[0])
    if len(pairs) > _abi.AZH_MAX_INPUTS:
        raise ArgumentError(f"more than {_abi.AZH_MAX_INPUTS} input records")
    out = array("i")
    index = 0
    while index < len(pairs):
        frame = pairs[index][0]
        while index < len(pairs) and pairs[index][0] == frame:
            held = apply_item(held, pairs[index][1])
            index += 1
        out.extend(held.as_record(frame))
    return out, held


def held_after(records: "array[int]", frames_run: int, held: Held) -> Held:
    """The held state the host has after a batch that ran ``frames_run`` frames: its last record at or before then,
    else ``held`` (the state before the batch)."""
    step = _abi.AZH_INPUT_INTS
    for start in range(len(records) - step, -1, -step):
        if records[start] <= frames_run:
            return Held(*records[start + 1:start + step])
    return held
