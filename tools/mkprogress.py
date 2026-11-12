#!/usr/bin/env python3
"""Build Guy's progress page and the entry file's lists from the status folders.

The status folders under docs/status/ are the only source: a file's folder is its
state, its head carries the page line. The bar counts items done out of all items
not parked; hours spent come from docs/hours.tsv. Nothing reads the clock, so two
runs give the same bytes.

Usage:
    python3 -I tools/mkprogress.py           write docs/progress.html and the lists in docs/status/README.md
    python3 -I tools/mkprogress.py --hours   print recorded hours per item and phase, write nothing
"""
from __future__ import annotations

import argparse
import csv
import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STATUS = REPO / "docs" / "status"
ENTRY = STATUS / "README.md"
PAGE = REPO / "docs" / "progress.html"
LEDGER = REPO / "docs" / "hours.tsv"
ENTRY_BUDGET = 60
GEN_BEGIN = "<!-- generated:begin (python3 -I tools/mkprogress.py; do not edit by hand) -->"
GEN_END = "<!-- generated:end -->"

# Folder name, word on the page, CSS class. The folder order is the reading order.
STATES = (
    ("1-in-progress", "now", "doing"),
    ("2-next", "next", "next"),
    ("3-waiting-on-guy", "waiting on you", "guy"),
    ("4-not-started", "to do", "todo"),
    ("5-done", "done", "done"),
    ("6-parked", "parked", "parked"),
)
STATE_NAMES = tuple(name for name, _, _ in STATES)
HANDOFF_NAME = "HANDOFF.md"
HANDOFF_STATE = "1-in-progress"


def find_handoffs() -> tuple[Path, ...]:
    """Return every handoff file: the one HANDOFF.md in the in-progress folder of the track being worked on."""
    return tuple(sorted(STATUS.glob(f"*/{HANDOFF_STATE}/{HANDOFF_NAME}")))


DONE, PARKED, WAITING = "5-done", "6-parked", "3-waiting-on-guy"
ID_PREFIX = {"lazpy": "laz-"}
HEAD_KEYS = ("id", "title", "order", "kind", "parent", "page", "hours", "default", "blocks")
SECTIONS = {
    "phase": ("What it is", "Exit gate", "Evidence", "Pointers", "Lessons and notes"),
    "step": ("What it is", "Exit gate", "Evidence", "Pointers", "Lessons and notes"),
    "ask": ("The ask", "Default", "Pointers"),
}
NO_LEDGER = ("The bar counts items done out of all items not parked; hours are what was spent, from "
             "docs/hours.tsv; the page shows no time left.")


class StatusError(Exception):
    """A status file or the entry file breaks the format."""


@dataclass(frozen=True)
class Item:
    """One status file: a phase, a step of a phase, or an ask to Guy."""

    ident: str
    title: str
    order: int
    kind: str
    state: str
    path: Path
    name: str
    page: str
    claim: str
    parent: str
    default: str
    blocks: str
    sections: dict[str, str]


@dataclass(frozen=True)
class Row:
    """One row of the hours ledger."""

    date: str
    bet: str
    phase: str
    hours: float


@dataclass(frozen=True)
class Title:
    """One track: its folder name, its name on the page and its order."""

    key: str
    name: str
    order: int


@dataclass(frozen=True)
class Status:
    """Everything the page is built from."""

    asof: str
    now: tuple[str, ...]
    next_up: tuple[str, ...]
    titles: tuple[Title, ...]
    items: tuple[Item, ...]
    spent: dict[str, float]  # ledger hours claimed by each item itself (steps not rolled up)


# ----------------------------------------------------------------------------- reading

def split_head(path: Path) -> tuple[dict[str, str], str]:
    """Return the key: value head of a status file and the text after it."""
    lines = path.read_text(encoding="utf-8").split("\n")
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        raise StatusError(f"{rel(path)}: no head between two '---' lines")
    end = lines.index("---", 1)
    head: dict[str, str] = {}
    for line in lines[1:end]:
        key, sep, value = line.partition(": ")
        if not sep or not value.strip():
            raise StatusError(f"{rel(path)}: head line is not 'key: value': {line!r}")
        if key in head:
            raise StatusError(f"{rel(path)}: head key twice: {key}")
        head[key] = value.strip()
    return head, "\n".join(lines[end + 1:])


def rel(path: Path) -> str:
    """Return a path as text relative to the repo."""
    return path.relative_to(REPO).as_posix()


def parse_sections(body: str) -> tuple[str, dict[str, str]]:
    """Return the '# name' of a file and its '## section' texts."""
    name = ""
    sections: dict[str, str] = {}
    current = ""
    for line in body.split("\n"):
        if line.startswith("# ") and not name:
            name = line[2:].strip()
        elif line.startswith("## "):
            current = line[3:].strip()
            sections[current] = ""
        elif current:
            sections[current] += line + "\n"
    return name, {key: text.strip() for key, text in sections.items()}


def parse_item(path: Path, title: str, state: str) -> Item:
    """Read one status file and check it against the fixed template."""
    head, body = split_head(path)
    unknown = [key for key in head if key not in HEAD_KEYS]
    if unknown:
        raise StatusError(f"{rel(path)}: unknown head key(s): {', '.join(unknown)}")
    for key in ("id", "title", "order", "kind", "page"):
        if key not in head:
            raise StatusError(f"{rel(path)}: head lacks '{key}'")
    kind = head["kind"]
    if kind not in SECTIONS:
        raise StatusError(f"{rel(path)}: kind must be phase, step or ask: {kind!r}")
    if head["title"] != title:
        raise StatusError(f"{rel(path)}: title says {head['title']!r} but the file is under {title}/")
    if not head["id"].startswith(ID_PREFIX.get(title, title + "-")):
        raise StatusError(f"{rel(path)}: id {head['id']!r} does not start with the track's prefix")
    if not head["order"].isdigit():
        raise StatusError(f"{rel(path)}: order is not a number: {head['order']!r}")
    stem_ok = path.name.startswith("ask-") if kind == "ask" else path.name.startswith(head["order"] + "-")
    if not stem_ok:
        raise StatusError(f"{rel(path)}: the file name must start with 'ask-' (asks) or with the order number")
    if kind != "ask" and "hours" not in head:
        raise StatusError(f"{rel(path)}: head lacks 'hours' (a ledger phase, PHASE ~ regex, or '-')")
    if kind == "ask" and "hours" in head:
        raise StatusError(f"{rel(path)}: an ask has no 'hours' key")
    if (kind == "step") != ("parent" in head):
        raise StatusError(f"{rel(path)}: 'parent' is for steps, and every step needs one")
    name, sections = parse_sections(body)
    missing = [section for section in SECTIONS[kind] if not sections.get(section)]
    if not name or missing:
        raise StatusError(f"{rel(path)}: needs a '# name' line and these filled sections: {', '.join(missing) or '-'}")
    if kind != "ask" and state == DONE and sections["Evidence"].lower().startswith("none yet"):
        raise StatusError(f"{rel(path)}: a done item needs evidence (commit, gate line or review file)")
    if kind == "ask" and state == DONE and not sections.get("Answer"):
        raise StatusError(f"{rel(path)}: an answered ask needs an '## Answer' section with Guy's words")
    return Item(
        ident=head["id"], title=title, order=int(head["order"]), kind=kind, state=state, path=path,
        name=name, page=head["page"], claim=head.get("hours", "-"), parent=head.get("parent", ""),
        default=head.get("default", "-"), blocks=head.get("blocks", "-"), sections=sections)


def load_titles() -> tuple[Title, ...]:
    """Return the tracks: every folder under docs/status/ that holds a TITLE.md."""
    titles = []
    for path in sorted(STATUS.glob("*/TITLE.md")):
        head, _ = split_head(path)
        for key in ("title", "name", "order"):
            if key not in head:
                raise StatusError(f"{rel(path)}: head lacks '{key}'")
        if head["title"] != path.parent.name:
            raise StatusError(f"{rel(path)}: title says {head['title']!r}, folder says {path.parent.name!r}")
        titles.append(Title(head["title"], head["name"], int(head["order"])))
    if not titles:
        raise StatusError("docs/status/: no track folder with a TITLE.md")
    return tuple(sorted(titles, key=lambda title: title.order))


def load_items(titles: tuple[Title, ...]) -> tuple[Item, ...]:
    """Read every status file of every track; the folder is the state."""
    items: list[Item] = []
    for title in titles:
        folder = STATUS / title.key
        for child in sorted(folder.iterdir()):
            if child.is_dir() and child.name not in STATE_NAMES:
                raise StatusError(f"{rel(child)}: not a state folder; the states are {', '.join(STATE_NAMES)}")
        for state in STATE_NAMES:
            for path in sorted((folder / state).glob("*")):
                if path.suffix != ".md" or not path.is_file():
                    raise StatusError(f"{rel(path)}: a state folder holds item files (.md) only")
                if state == HANDOFF_STATE and path.name == HANDOFF_NAME:
                    continue  # the handoff lives beside the items it is about; it is not an item
                items.append(parse_item(path, title.key, state))
    check_items(items)
    return tuple(sorted(items, key=lambda item: (item.title, item.order, item.ident)))


def check_items(items: list[Item]) -> None:
    """Check what one file cannot know: ids are unique and every step's parent is a phase."""
    seen: dict[str, Path] = {}
    for item in items:
        if item.ident in seen:
            raise StatusError(f"{rel(item.path)}: id {item.ident} is also in {rel(seen[item.ident])}")
        seen[item.ident] = item.path
    phases = {item.ident for item in items if item.kind == "phase"}
    for item in items:
        if item.kind == "step" and item.parent not in phases:
            raise StatusError(f"{rel(item.path)}: parent {item.parent!r} is not a phase")


def load_ledger() -> tuple[Row, ...]:
    """Read docs/hours.tsv."""
    rows = []
    with LEDGER.open(encoding="utf-8", newline="") as handle:
        for line, record in enumerate(csv.DictReader(handle, delimiter="\t"), 2):
            try:
                rows.append(Row(record["date"], record["bet"], record["phase"], float(record["hours"])))
            except (KeyError, TypeError, ValueError):
                raise StatusError(f"docs/hours.tsv:{line}: needs date, bet, phase and a number of hours") from None
    return tuple(rows)


def claim_hours(items: tuple[Item, ...], rows: tuple[Row, ...]) -> dict[str, float]:
    """Give every ledger row to exactly one item and return the hours per item id.

    An item claims a ledger phase with 'hours: PHASE', or part of one with
    'hours: PHASE ~ regex' (matched against the bet column). The regex form wins
    over the plain form. A row nobody claims, or two claim, is an error.
    """
    plain: dict[str, list[Item]] = {}
    narrow: dict[str, list[tuple[re.Pattern[str], Item]]] = {}
    for item in items:
        if item.claim == "-":
            continue
        phase, sep, pattern = item.claim.partition(" ~ ")
        if sep:
            narrow.setdefault(phase, []).append((re.compile(pattern), item))
        else:
            plain.setdefault(phase, []).append(item)
    spent = {item.ident: 0.0 for item in items}
    for row in rows:
        owners = [item for pattern, item in narrow.get(row.phase, []) if pattern.search(row.bet)]
        if not owners:
            owners = plain.get(row.phase, [])
        if len(owners) != 1:
            names = ", ".join(owner.ident for owner in owners) or "no item"
            raise StatusError(f"docs/hours.tsv: the row '{row.bet[:60]}' (phase {row.phase}) is claimed by {names}; "
                              "exactly one item's 'hours:' key must claim it")
        spent[owners[0].ident] += row.hours
    return spent


def load_entry() -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    """Return the 'as of' stamp and the hand-written Now and Next lines of the entry file."""
    head, body = split_head(ENTRY)
    if "asof" not in head:
        raise StatusError("docs/status/README.md: head lacks 'asof'")
    _, sections = parse_sections(body)
    lists = []
    for section in ("Now", "Next"):
        lines = tuple(line[2:].strip() for line in sections.get(section, "").split("\n") if line.startswith("- "))
        if not lines:
            raise StatusError(f"docs/status/README.md: '## {section}' needs at least one '- ' line")
        lists.append(lines)
    return head["asof"], lists[0], lists[1]


def load_status() -> Status:
    """Read the status folders and the entry file; fail on the first format error."""
    titles = load_titles()
    items = load_items(titles)
    asof, now, next_up = load_entry()
    spent = claim_hours(items, load_ledger())
    return Status(asof, now, next_up, titles, items, spent)


# ----------------------------------------------------------------------------- numbers

def phases_of(title: str, status: Status) -> list[Item]:
    """Return the track's phases that are not parked, in reading order."""
    return [item for item in status.items if item.title == title and item.kind == "phase" and item.state != PARKED]


def counted(title: str, status: Status) -> tuple[int, int]:
    """Return (items done, items not parked) over phases and steps; asks are not counted."""
    live = [item for item in status.items
            if item.title == title and item.kind in ("phase", "step") and item.state != PARKED]
    return sum(1 for item in live if item.state == DONE), len(live)


def percent(title: str, status: Status) -> int:
    """Return the whole-number percentage of counted items that are done."""
    done, whole = counted(title, status)
    return round(100 * done / whole) if whole else 0


def hours_of(item: Item, status: Status) -> float:
    """Return the hours spent on an item; a phase also holds the hours of its steps."""
    own = status.spent[item.ident]
    if item.kind == "phase":
        own += sum(status.spent[step.ident] for step in status.items if step.kind == "step" and step.parent == item.ident)
    return own


def hours_note(item: Item, status: Status) -> str:
    """Return ' (0.25 h)' for an item with recorded hours, else nothing."""
    value = hours_of(item, status)
    return f" ({value:.2f} h)" if value > 0 else ""


# ----------------------------------------------------------------------------- the page

CSS = """
:root {
  --surface: #fbfbfc; --raised: #eef0f3; --hairline: #d9dce2; --ink: #22262d; --muted: #5a616b;
  --accent: #b23a48; --done: #2e7d4f; --progress: #2a6cb0; --guy: #c0691a; --warn: #866a1c; --idle: #858a93;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --surface: #14161a; --raised: #1d2026; --hairline: #2b2f37; --ink: #e9ebef; --muted: #a2a8b2;
    --accent: #f08a96; --done: #62c48f; --progress: #78b4ea; --guy: #f0a455; --warn: #dfb94c; --idle: #7b8089;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --surface: #14161a; --raised: #1d2026; --hairline: #2b2f37; --ink: #e9ebef; --muted: #a2a8b2;
  --accent: #f08a96; --done: #62c48f; --progress: #78b4ea; --guy: #f0a455; --warn: #dfb94c; --idle: #7b8089;
  color-scheme: dark;
}
body { background: var(--surface); color: var(--ink); font: 16px/1.5 -apple-system, system-ui, "Segoe UI", sans-serif; }
.wrap { max-width: 42rem; margin: 0 auto; padding-block: 20px 48px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: flex; flex-direction: column; gap: 20px; }
h1, h2, h3, p, ul, ol { margin: 0; }
ul, ol { padding: 0; list-style: none; }
h1 { font-size: 1.5rem; line-height: 1.2; text-wrap: balance; }
h2 { font-size: .78rem; letter-spacing: .09em; text-transform: uppercase; color: var(--muted); font-weight: 650; }
.asof, .small { color: var(--muted); font-size: .85rem; }
.now { background: var(--raised); border-left: 4px solid var(--accent); border-radius: 10px; padding: 14px 16px;
  display: flex; flex-direction: column; gap: 8px; }
.now li + li { margin-top: 6px; }
.now .next { border-top: 1px solid var(--hairline); padding-top: 8px; }
.tag { font-size: .72rem; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; color: var(--accent);
  margin-right: 6px; }
.tabs { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; background: var(--raised); border-radius: 12px; padding: 4px; }
.tabs button { font: inherit; font-weight: 600; color: var(--muted); background: transparent; border: 0; border-radius: 9px;
  padding: 10px 8px; min-width: 0; cursor: pointer; }
.tabs button[aria-selected="true"] { background: var(--surface); color: var(--ink); box-shadow: 0 0 0 1px var(--hairline); }
.tabs button:focus-visible, summary:focus-visible { outline: 2px solid var(--progress); outline-offset: 2px; }
.panel { display: flex; flex-direction: column; gap: 22px; }
.panel > h3 { font-size: 1.2rem; }
.meter { display: flex; flex-direction: column; gap: 6px; }
.meter .top { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
.meter .pct { font-size: 2rem; font-weight: 700; line-height: 1; font-variant-numeric: tabular-nums; }
.meter .label { font-weight: 600; min-width: 0; }
.rough { font-size: .72rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--warn);
  border: 1px solid var(--warn); border-radius: 999px; padding: 1px 8px; }
.track { height: 12px; background: var(--raised); border-radius: 999px; overflow: hidden; box-shadow: inset 0 0 0 1px var(--hairline); }
.fill { height: 100%; min-width: 6px; background: var(--progress); border-radius: 999px; }
.block { display: flex; flex-direction: column; gap: 8px; }
.road li { display: grid; grid-template-columns: 1.15rem minmax(0, 1fr) auto; gap: 10px; align-items: start;
  padding: 9px 0; border-bottom: 1px solid var(--hairline); }
.road li:last-child { border-bottom: 0; }
.dot { width: .95rem; height: .95rem; border-radius: 50%; margin-top: .3rem; box-sizing: border-box; border: 2px solid var(--idle); }
.done .dot { background: var(--done); border-color: var(--done); }
.doing .dot { border-color: var(--progress); background: radial-gradient(circle, var(--progress) 0 42%, transparent 46%); }
.next .dot { border-color: var(--progress); }
.guy .dot { background: var(--guy); border-color: var(--guy); }
.parked .dot { border-style: dashed; }
.word { font-size: .72rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: var(--muted);
  white-space: nowrap; margin-top: .3rem; }
.done .word { color: var(--done); } .doing .word, .next .word { color: var(--progress); } .guy .word { color: var(--guy); }
.done .what { color: var(--muted); } .doing .what { font-weight: 650; }
.asks li { padding: 8px 0 8px 14px; border-left: 3px solid var(--guy); margin-bottom: 8px; }
details { border: 1px solid var(--hairline); border-radius: 10px; padding: 10px 14px; }
summary { cursor: pointer; font-weight: 600; }
details > div { display: flex; flex-direction: column; gap: 16px; margin-top: 12px; }
details h4 { margin: 0 0 4px; font-size: .9rem; }
.mono { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: .85em; }
footer { color: var(--muted); font-size: .85rem; border-top: 1px solid var(--hairline); padding-top: 14px; }
"""


def esc(text: str) -> str:
    """Return text safe to put inside HTML."""
    return html.escape(text, quote=True)


def meter(label: str, pct: int, line: str) -> str:
    """Return one progress bar with its percentage and its count line."""
    return (f'<div class="meter"><div class="top"><span class="pct">{pct} %</span>'
            f'<span class="label">{esc(label)}</span></div>'
            f'<div class="track" role="img" aria-label="{pct} percent"><div class="fill" style="width:{pct}%"></div></div>'
            f'<p class="small">{esc(line)}</p></div>')


def road(items: list[Item], status: Status) -> str:
    """Return the list of items, one plain line each, with a done / now / to do mark."""
    words = {name: (word, css) for name, word, css in STATES}
    rows = []
    for item in items:
        if item.page == "-":
            continue
        word, css = words[item.state]
        rows.append(f'<li class="{css}"><span class="dot" aria-hidden="true"></span>'
                    f'<span class="what">{esc(item.page + hours_note(item, status))}</span><span class="word">{esc(word)}</span></li>')
    return '<ol class="road">' + "".join(rows) + "</ol>"


def meters(title: Title, status: Status) -> str:
    """Return the track's bar: items done out of all items not parked."""
    done, whole = counted(title.key, status)
    spent = sum(status.spent[item.ident] for item in status.items if item.title == title.key)
    line = f"{done} of {whole} items done; {spent:.2f} hours recorded in docs/hours.tsv."
    return meter("Items done, of all items not parked", percent(title.key, status), line)


def asks_block(title: Title, status: Status) -> str:
    """Return the 'waiting on you' list: the asks with a page line, and a count of the private ones."""
    asks = [item for item in status.items if item.title == title.key and item.kind == "ask" and item.state == WAITING]
    shown = [item for item in asks if item.page != "-"]
    hidden = len(asks) - len(shown)
    if not asks:
        return '<p class="small">Nothing waits on you here.</p>'
    rows = "".join(f"<li>{esc(item.page)}</li>" for item in shown)
    more = ""
    if hidden:
        noun = "private decision runs on its default" if hidden == 1 else "private decisions run on their defaults"
        more = f'<p class="small">Plus {hidden} {noun} until you say otherwise.</p>'
    return f'<ul class="asks">{rows}</ul>{more}'


def more_block(title: Title, status: Status) -> str:
    """Return the 'More' fold: the steps, what is parked, how the bar is counted."""
    parts = []
    steps = [item for item in status.items if item.title == title.key and item.kind == "step"]
    if steps:
        parts.append("<div><h4>The steps</h4>" + road(steps, status) + "</div>")
    parked = [item for item in status.items
              if item.title == title.key and item.kind == "phase" and item.state == PARKED and item.page != "-"]
    if parked:
        parts.append("<div><h4>Parked, not on the road now</h4>" + road(parked, status) + "</div>")
    parts.append(f'<div><h4>How the bar is counted</h4><p class="small">{esc(NO_LEDGER)}</p></div>')
    return "<details><summary>More</summary><div>" + "".join(parts) + "</div></details>"


def panel(title: Title, status: Status) -> str:
    """Return one track's panel."""
    return (f'<section class="panel" id="panel-{title.key}">'
            f"<h3>{esc(title.name)}</h3>{meters(title, status)}"
            f'<div class="block"><h2>The road</h2>{road(phases_of(title.key, status), status)}</div>'
            f'<div class="block"><h2>Waiting on you</h2>{asks_block(title, status)}</div>'
            f"{more_block(title, status)}</section>")


def render_page(status: Status) -> str:
    """Return the whole page: one self-contained file with no doctype, html, head or body tag, and no script."""
    now = "".join(f"<li>{esc(line)}</li>" for line in status.now)
    nxt = "".join(f'<p class="next"><span class="tag">Next</span>{esc(line)}</p>' for line in status.next_up)
    panels = "".join(panel(title, status) for title in status.titles)
    return (
        "<title>libazahar-py progress</title>\n"
        '<meta name="claude:viewport-fit-sides" content="cover">\n'
        f"<style>{CSS}</style>\n"
        '<div class="wrap">\n'
        f'<header><h1>libazahar-py</h1><p class="asof">Run the Azahar 3DS emulator with no window, many copies at once, '
        f'to test 3DS homebrew from scripts: buttons, touch, screenshots, memory. As of {esc(status.asof)}.</p></header>\n'
        f'<section class="now"><h2>Now</h2><ul>{now}</ul>{nxt}</section>\n'
        f"{panels}\n"
        f"<footer>{esc(NO_LEDGER)}</footer>\n"
        "</div>\n")


# ----------------------------------------------------------------------------- the entry file

def entry_lists(status: Status) -> str:
    """Return the generated part of docs/status/README.md: where each open item is, what waits on Guy."""
    lines = [GEN_BEGIN]
    for title in status.titles:
        mine = [item for item in status.items if item.title == title.key]
        lines.append(f"### {title.name} (`docs/status/{title.key}/`)")
        for state in ("1-in-progress", "2-next"):
            for item in mine:
                if item.state == state and item.kind != "ask":
                    lines.append(f"- {state[2:]}: `{rel(item.path)}`")
        waiting = [item for item in mine if item.state == WAITING]
        for item in waiting:
            if item.kind != "ask":
                lines.append(f"- waiting on Guy: `{rel(item.path)}`")
        blocking = [item for item in waiting if item.kind == "ask" and item.blocks != "-"]
        for item in blocking:
            lines.append(f"- Guy must answer (blocks {item.blocks}): `{rel(item.path)}`")
        counts = ", ".join(f"{sum(1 for item in mine if item.state == state)} in `{state}/`"
                           for state in (WAITING, "4-not-started", DONE, PARKED))
        lines.append(f"- files: {counts}")
    lines.append(GEN_END)
    return "\n".join(lines)


def render_entry(status: Status) -> str:
    """Return docs/status/README.md with its generated part rewritten."""
    text = ENTRY.read_text(encoding="utf-8")
    if text.count(GEN_BEGIN) != 1 or text.count(GEN_END) != 1:
        raise StatusError("docs/status/README.md: needs exactly one generated:begin and one generated:end line")
    before, rest = text.split(GEN_BEGIN)
    _, after = rest.split(GEN_END)
    out = before + entry_lists(status) + after
    count = len(out.rstrip("\n").split("\n"))
    if count > ENTRY_BUDGET:
        raise StatusError(f"docs/status/README.md: {count} lines, the budget is {ENTRY_BUDGET}")
    return out


# ----------------------------------------------------------------------------- command line

def print_hours(status: Status) -> None:
    """Print recorded hours per item, and per phase (with its steps), and each track's total."""
    for title in status.titles:
        mine = [item for item in status.items if item.title == title.key and item.kind != "ask"]
        total = sum(status.spent[item.ident] for item in mine)
        print(f"{title.name}: {total:.2f} h recorded, {percent(title.key, status)} % items done")
        for item in mine:
            own = status.spent[item.ident]
            if item.kind == "phase":
                print(f"  {item.ident:9} {item.state:17} {hours_of(item, status):6.2f} h (own {own:.2f}) claims {item.claim}")
            elif own > 0 or item.claim != "-":
                print(f"    {item.ident:9} {item.state:17} {own:6.2f} h claims {item.claim}")


def main(argv: list[str]) -> int:
    """Build the page and the entry lists, or print the hours."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--hours", action="store_true", help="print recorded hours per item and write nothing")
    args = parser.parse_args(argv)
    try:
        status = load_status()
        if args.hours:
            print_hours(status)
            return 0
        entry, page = render_entry(status), render_page(status)
    except StatusError as error:
        print(f"mkprogress: {error}", file=sys.stderr)
        return 1
    ENTRY.write_text(entry, encoding="utf-8")
    PAGE.write_text(page, encoding="utf-8")
    print(f"mkprogress: wrote {rel(PAGE)} ({len(page.encode('utf-8'))} bytes) and the lists in {rel(ENTRY)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
