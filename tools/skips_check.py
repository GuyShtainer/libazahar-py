#!/usr/bin/env python3
"""Check a pytest junit file: every skipped test must be on the named list, with its message.

    python3 -I tools/skips_check.py <junit.xml> --list fast|w7
    python3 -I tools/skips_check.py --self-test

Lists live in tests/data/allowed-skips/<name>.txt (format at the top of each). Exit 0 only when:
  - the file holds at least one test, and none failed or errored;
  - every skipped test is on the list and its message matches that line's regex;
  - with --list w7, test_release_fixture.py and test_profile_format.py each ran at least one test that passed.
Prints one line per skip: ``ALLOWED <nodeid>`` or ``NOT ALLOWED <nodeid>: <message>``, then a summary line.
Exit 1 on any breach, 2 on a bad call or an unreadable file.
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, NamedTuple, Optional, Tuple

LISTS = Path(__file__).resolve().parents[1] / "tests" / "data" / "allowed-skips"
MUST_RUN = {"w7": ("test_release_fixture.py", "test_profile_format.py")}


class Case(NamedTuple):
    nodeid: str          # tests/python/test_x.py::test_name[params]
    outcome: str         # passed, skipped, failed or error
    message: str


def parse_junit(path: Path) -> List[Case]:
    """Every testcase of a junit file, with its outcome and (for a skip, failure or error) its message."""
    root = ET.parse(path).getroot()
    cases: List[Case] = []
    for case in root.iter("testcase"):
        parts = (case.get("classname") or "").split(".")
        at = next((i for i, p in enumerate(parts) if p.startswith("test_")), len(parts))
        module = "/".join(parts[:at + 1]) + ".py" if at < len(parts) else "/".join(parts)
        nodeid = "::".join([module, *parts[at + 1:], case.get("name") or ""])
        outcome, message = "passed", ""
        for child in case:
            if child.tag in ("skipped", "failure", "error"):
                outcome = {"skipped": "skipped", "failure": "failed", "error": "error"}[child.tag]
                message = child.get("message") or (child.text or "").strip()
                break
        cases.append(Case(nodeid, outcome, re.sub(r"^Skipped: ", "", message)))
    return cases


def load_list(name: str) -> List[Tuple[str, "re.Pattern[str]"]]:
    """The rules of a list: (``file::name`` pattern, message regex)."""
    path = LISTS / f"{name}.txt"
    rules: List[Tuple[str, "re.Pattern[str]"]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        if " => " not in line:
            raise SystemExit(f"{path}:{number}: expected '<file>::<test> => <regex>'")
        where, regex = line.split(" => ", 1)
        rules.append((where.strip(), re.compile(regex)))
    return rules


def allowed(case: Case, rules: List[Tuple[str, "re.Pattern[str]"]]) -> bool:
    """True when some rule names the test (parameters ignored) and its regex matches the start of the message."""
    base = case.nodeid.split("[", 1)[0]
    short = base.rsplit("/", 1)[-1]
    for where, regex in rules:
        file_part, _, name_part = where.partition("::")
        have_file, _, have_name = short.partition("::")
        if file_part not in ("*", have_file) or name_part not in ("*", have_name.split("::")[-1]):
            continue
        if regex.search(case.message):
            return True
    return False


def check(junit: Path, list_name: str) -> int:
    """Run the check; print the lines; return the exit code."""
    cases = parse_junit(junit)
    rules = load_list(list_name)
    bad = 0
    if not cases:
        print("FAIL: the junit file holds no tests")
        return 1
    for case in cases:
        if case.outcome in ("failed", "error"):
            print(f"FAIL {case.outcome} {case.nodeid}: {case.message[:200]}")
            bad += 1
        elif case.outcome == "skipped":
            if allowed(case, rules):
                print(f"ALLOWED {case.nodeid}")
            else:
                print(f"NOT ALLOWED {case.nodeid}: {case.message}")
                bad += 1
    for name in MUST_RUN.get(list_name, ()):
        ran = [c for c in cases if c.nodeid.split("::")[0].endswith(name) and c.outcome == "passed"]
        if not ran:
            print(f"FAIL {name}: no test of it ran and passed")
            bad += 1
    skips = sum(c.outcome == "skipped" for c in cases)
    print(f"skips_check: {len(cases)} tests, {skips} skipped, {bad} problems (list {list_name})")
    return 1 if bad else 0


def _xml(cases: List[Tuple[str, str, str, str]]) -> str:
    """A junit file from (classname, name, kind, message); kind is '', skipped, failure or error."""
    rows = []
    for classname, name, kind, message in cases:
        inner = f'<{kind} message="{message}"/>' if kind else ""
        rows.append(f'<testcase classname="{classname}" name="{name}">{inner}</testcase>')
    return '<?xml version="1.0"?><testsuites><testsuite name="pytest">' + "".join(rows) + "</testsuite></testsuites>"


def self_test() -> int:
    """Plant junit files and check the verdicts. Each case: (name, list, cases, wanted exit code)."""
    py = "tests.python."
    good_w7 = [(py + "test_release_fixture", "test_release_fixture_loads[v1.0.0]", "", ""),
               (py + "test_profile_format", "test_profile_case[a]", "", "")]
    table = [
        ("fast: a clean run", "fast", [(py + "test_x", "test_a", "", "")], 0),
        ("fast: a core fixture skip", "fast", [(py + "test_x", "test_a", "skipped", "needs_core: build/libazhost.dll is missing")], 0),
        ("fast: a plain skip is refused", "fast", [(py + "test_x", "test_a", "skipped", "no reason")], 1),
        ("fast: the prefix must start the message", "fast", [(py + "test_x", "test_a", "skipped", "x needs_core: y")], 1),
        ("fast: a Windows by-design skip", "fast",
         [(py + "test_slots", "test_s5_load_warning", "skipped", "no load average on Windows; twin")], 0),
        ("fast: right test, wrong message", "fast",
         [(py + "test_slots", "test_s5_load_warning", "skipped", "something else")], 1),
        ("fast: a failure", "fast", [(py + "test_x", "test_a", "failure", "assert 1 == 2")], 1),
        ("fast: an error", "fast", [(py + "test_x", "test_a", "error", "fixture failed")], 1),
        ("fast: an empty file", "fast", [], 1),
        ("fast: numpy importorskip is refused", "fast",
         [(py + "test_map", "test_view", "skipped", "could not import 'numpy': No module named 'numpy'")], 1),
        ("w7: clean with the two files run", "w7", good_w7, 0),
        ("w7: a core skip is refused", "w7", good_w7 + [(py + "test_x", "test_a", "skipped", "needs_core: no core")], 1),
        ("w7: the lazpy.1 skip is allowed", "w7",
         good_w7 + [(py + "test_threads_live", "test_k_threads_lazpy1_core", "skipped", "set LAZ_CORE_OLD to a lazpy.1 core")], 0),
        ("w7: a parametrized by-design skip", "w7",
         good_w7 + [(py + "test_lazpy_profile", "test_worker_nice_floor[5-10]", "skipped", "no nice values on Windows: x")], 0),
        ("w7: the release fixture skipped", "w7",
         [(py + "test_release_fixture", "test_release_fixture_loads", "skipped", "no release fixture under runs"),
          (py + "test_profile_format", "test_profile_case[a]", "", "")], 1),
        ("w7: test_profile_format missing", "w7", [good_w7[0]], 1),
        ("w7: a failure beside good runs", "w7", good_w7 + [(py + "test_x", "test_a", "failure", "boom")], 1),
    ]
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for number, (label, list_name, cases, want) in enumerate(table):
            junit = Path(tmp) / f"planted{number}.xml"
            junit.write_text(_xml(cases), encoding="utf-8")
            print(f"--- {label}")
            got = check(junit, list_name)
            if got != want:
                print(f"SELF-TEST FAIL: {label}: exit {got}, wanted {want}")
                failed += 1
    print(f"skips_check self-test: {len(table) - failed} of {len(table)} planted cases gave the wanted exit code")
    return 1 if failed else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("junit", nargs="?", type=Path)
    parser.add_argument("--list", dest="list_name", choices=("fast", "w7"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.junit is None or args.list_name is None:
        parser.print_usage(sys.stderr)
        return 2
    try:
        return check(args.junit, args.list_name)
    except (OSError, ET.ParseError) as exc:
        print(f"skips_check: cannot read {args.junit}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
