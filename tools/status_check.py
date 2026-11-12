#!/usr/bin/env python3
"""Check the status folders, the entry file and the handoff against their formats.

Fails (exit 1) when:
  - a status file breaks the template (head keys, sections, file name, evidence on done items);
  - docs/status/README.md is over its line budget or its generated lists are out of date;
  - docs/progress.html is not what the generator would write now;
  - the slim handoff is over its line budget, holds a session log, a bold-labelled block, or more than one dated
    state block, or a "Running now" row names no item that sits in a 1-in-progress/ folder;
  - an hours-ledger row (docs/hours.tsv) is claimed by no item or by two;
  - an item in 2-next/ or 4-not-started/ has build or main-loop hours booked (its work started).

A handoff still in the old long format (no slim marker on line 1) is reported and does not fail, so the
check can run before the swap. Pass --strict-handoff to make that a failure too.

Usage:
    python3 -I tools/status_check.py [--handoff PATH] [--strict-handoff]
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mkprogress  # noqa: E402  (a sibling script; -I keeps the script folder off the path)

HANDOFF_BUDGET = 80
HANDOFF_MARKER = "<!-- handoff: slim v1"
HANDOFF_SECTIONS = ("Running now", "Next steps, in order", "Waiting on Guy (only what blocks a step above)",
                    "Pointers")
ASOF_RE = re.compile(r"^As of: \d{4}-\d{2}-\d{2} \d{2}:\d{2}\b")
STATE_BLOCK_RE = re.compile(r"\*\*[^*\n]*(\bState \d{1,2}:\d{2}|\b(LATEST|RESUMED|HALTED|STOPPED)\b|\(\d{4}-\d{2}-\d{2}[^)]*\))[^*\n]*\*\*")
LOG_RE = re.compile(r"^#+ +(Session log|Session —|Session -|History|Changelog|Log)\b", re.IGNORECASE)
BLOCK_RE = re.compile(r"^\*\*")  # a bold-labelled paragraph ("**Where things stand.**"): a state block by another name
RUNNING = "Running now"
AGENT_ID_RE = re.compile(r"\b(?:[0-9a-f]{8,}|main)\b")


def check_generated(status: mkprogress.Status) -> list[str]:
    """Return a finding for each generated file that differs from what the generator would write now."""
    findings = []
    if mkprogress.render_entry(status) != mkprogress.ENTRY.read_text(encoding="utf-8"):
        findings.append("docs/status/README.md: the generated lists are out of date; run python3 -I tools/mkprogress.py")
    page = mkprogress.PAGE.read_text(encoding="utf-8") if mkprogress.PAGE.is_file() else ""
    if mkprogress.render_page(status) != page:
        findings.append("docs/progress.html: not what the generator writes now; run python3 -I tools/mkprogress.py")
    return findings


def check_links(status: mkprogress.Status) -> list[str]:
    """Return a finding for each status file that names another status file at a place where it no longer is."""
    known = {item.path.name: mkprogress.rel(item.path) for item in status.items}
    findings = []
    for path in sorted(mkprogress.STATUS.rglob("*.md")):
        for target in re.findall(r"`(docs/status/(?:[a-z0-9]+)/\d-[a-z-]+/[^`\s]+\.md)`", path.read_text(encoding="utf-8")):
            if (mkprogress.REPO / target).is_file():
                continue
            now = known.get(Path(target).name, "nowhere")
            findings.append(f"{mkprogress.rel(path)}: points at {target}, which is now at {now}")
    return findings


def check_handoff(path: Path, strict: bool) -> tuple[list[str], list[str]]:
    """Return (findings, notes) for the handoff file: its budget, its single dated state, its fixed sections."""
    if not path.is_file():
        return [f"{path}: no such file"], []
    lines = path.read_text(encoding="utf-8").rstrip("\n").split("\n")
    name = path.name
    if not lines[0].startswith(HANDOFF_MARKER):
        note = (f"{name}: old long format ({len(lines)} lines, no slim marker on line 1). "
                "Rewrite it whole from docs/status/templates/handoff.md")
        return ([note], []) if strict else ([], [note])
    findings = []
    if len(lines) > HANDOFF_BUDGET:
        findings.append(f"{name}: {len(lines)} lines, the budget is {HANDOFF_BUDGET}. Rewrite it whole from "
                        "docs/status/templates/handoff.md; move history into the item files")
    stamps = [number for number, line in enumerate(lines, 1) if ASOF_RE.match(line)]
    if len(stamps) != 1:
        findings.append(f"{name}: needs exactly one 'As of: YYYY-MM-DD hh:mm' line, found {len(stamps)}")
    for number, line in enumerate(lines, 1):
        if STATE_BLOCK_RE.search(line):
            findings.append(f"{name}:{number}: a dated state block. The handoff holds one state, the 'As of' line; "
                            "it is rewritten, never appended")
        if LOG_RE.match(line):
            findings.append(f"{name}:{number}: a log heading. History goes to the item files and git log")
        if BLOCK_RE.match(line):
            findings.append(f"{name}:{number}: a bold-labelled block. The handoff holds only the template's rows and "
                            "steps; state goes in a 'Running now' row, rulings and history in the item file")
    headings = [line[3:].strip() for line in lines if line.startswith("## ")]
    if tuple(headings) != HANDOFF_SECTIONS:
        findings.append(f"{name}: the '## ' sections must be exactly, in order: {'; '.join(HANDOFF_SECTIONS)}")
    return findings, []


STARTED_ROLES = ("build", "main")  # ledger roles that mean the item's own work ran (measure, plan, consult do not)


def check_started_items(status: mkprogress.Status) -> list[str]:
    """Return a finding for each item still in 2-next/ or 4-not-started/ that has build or main-loop hours booked.

    Booked build work means the item started, so its file must sit in 1-in-progress/ (or a later folder).
    """
    waiting = (mkprogress.STATE_NAMES[1], mkprogress.STATE_NAMES[3])
    booked: dict[str, float] = {}
    with mkprogress.LEDGER.open(encoding="utf-8", newline="") as handle:
        for record in csv.DictReader(handle, delimiter="\t"):
            if record.get("role") not in STARTED_ROLES:
                continue
            row = mkprogress.Row(record["date"], record["bet"], record["phase"], 1.0)
            for ident, hit in mkprogress.claim_hours(status.items, (row,)).items():
                if hit:
                    booked[ident] = booked.get(ident, 0.0) + float(record["hours"])
    return [f"{mkprogress.rel(item.path)}: {booked[item.ident]:.2f} h of build or main-loop work are booked to "
            f"{item.ident}, but it sits in {item.state}/. git mv it to 1-in-progress/ and add its Evidence"
            for item in status.items if item.state in waiting and booked.get(item.ident, 0.0) > 0]


def check_running_items(path: Path, status: mkprogress.Status) -> list[str]:
    """Return a finding for each 'Running now' row that names no item file sitting in a 1-in-progress/ folder.

    This keeps the item files managed: work that runs has an item, and that item is in progress.
    """
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").split("\n")
    doing = {item.ident for item in status.items if item.state == mkprogress.STATE_NAMES[0]}
    known = {item.ident: item.state for item in status.items}
    findings = []
    inside = False
    rows = 0
    agent_col: int | None = None
    for number, line in enumerate(lines, 1):
        if line.startswith("## "):
            inside = line[3:].strip() == RUNNING
            continue
        if not inside or not line.startswith("|") or re.match(r"^\|[\s|:-]+\|?\s*$", line):
            continue
        rows += 1
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if rows == 1:
            agent_col = next((i for i, cell in enumerate(cells) if "agent" in cell.lower()), None)
            if agent_col is None:
                findings.append(f"{path.name}:{number}: the 'Running now' table needs an 'Agent id' column")
            continue  # the table's head row
        if agent_col is not None and not AGENT_ID_RE.search(cells[agent_col] if agent_col < len(cells) else ""):
            findings.append(f"{path.name}:{number}: the agent id cell needs the real id from the launch result "
                            "(8+ hex characters) or 'main' for the main loop's own work, not a model name")
        named = [ident for ident in known if re.search(rf"(?<![\w-]){re.escape(ident)}(?![\w-])", line)]
        if not any(ident in doing for ident in named):
            where = ", ".join(f"{ident} is in {known[ident]}" for ident in named) or "no item id"
            findings.append(f"{path.name}:{number}: a running row needs the id of an item in 1-in-progress/ ({where}). "
                            "Copy docs/status/templates/item.md into the track's 1-in-progress/ (or git mv the "
                            "item there) and name its id in the row")
    return findings


def main(argv: list[str]) -> int:
    """Run every check and print the findings."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--handoff", type=Path, default=None,
                        help="the handoff file to check (default: the one HANDOFF.md under docs/status/<track>/1-in-progress/)")
    parser.add_argument("--strict-handoff", action="store_true", help="fail when the handoff is still in the old format")
    args = parser.parse_args(argv)
    try:
        status = mkprogress.load_status()
        findings = check_generated(status) + check_links(status) + check_started_items(status)
    except mkprogress.StatusError as error:
        print(f"status_check: FAIL: {error}", file=sys.stderr)
        return 1
    handoffs = (args.handoff,) if args.handoff else mkprogress.find_handoffs()
    if len(handoffs) != 1:
        handoff_findings, notes = [f"docs/status/: needs exactly one HANDOFF.md in a track's 1-in-progress/ folder, "
                                   f"found {len(handoffs)}"], []
    else:
        handoff_findings, notes = check_handoff(handoffs[0].resolve(), args.strict_handoff)
        handoff_findings += check_running_items(handoffs[0].resolve(), status)
    findings += handoff_findings
    for note in notes:
        print(f"status_check: note: {note}")
    for finding in findings:
        print(f"status_check: FAIL: {finding}", file=sys.stderr)
    if findings:
        return 1
    rows = len(mkprogress.load_ledger())
    print(f"status_check: OK: {len(status.items)} status files, {rows} ledger rows each claimed once, "
          "entry file and page current")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
