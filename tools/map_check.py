#!/usr/bin/env python3
"""Check that the maps and the status files still point at things that exist.

Exit 1, with one FAIL line per finding, when:
  - a path named in back-ticks or in a code block of docs/map/*.md, docs/status/**/*.md or a slim
    handoff is gone (a pattern must match at least one file; `path:N` needs a file of N lines);
  - a top-level folder, or a top-level file git tracks or would track, is not named in docs/map/code.md;
  - a folder that holds scripts is not named in docs/map/tools.md;
  - a generated list is stale;
  - a `make <target>` named in a hand-written map is not a target of any make file;
  - a map file is not linked from the index docs/map/README.md.

Not checked: text between a line that starts "<!-- unchecked:begin" and a line that starts
"<!-- unchecked:end -->" (old text kept word for word), and paths under folders that come and go (worktrees,
build output, working copies). 
Usage:
    python3 -I tools/map_check.py
"""
from __future__ import annotations

import glob
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mkmap  # noqa: E402  (python3 -I does not put the script folder on the path)

REPO = mkmap.REPO
MAP = REPO / "docs" / "map"
STATUS = REPO / "docs" / "status"
INDEX = MAP / "README.md"
CODE_MAP = MAP / "code.md"
TOOLS_MAP = MAP / "tools.md"
VERBATIM: tuple[str, ...] = ()
HISTORY: tuple[str, ...] = ()
VOLATILE = ("build/", "build-", ".claude/worktrees/", "tmp/", "temp/", "runs/", "dl/", "cores/", "vendor/", ".venv/",
            "roms/", "sdmc/")
SKIP_TOP = (".git", ".DS_Store")
UNCHECKED_BEGIN = "<!-- unchecked:begin"
UNCHECKED_END = "<!-- unchecked:end -->"
PLACEHOLDER_MARKS = ("<", ">", "$", "{", "}", "=", "…", "...", "|", "\\")
PATTERN_MARKS = ("*", "?", "[")
SPAN_RE = re.compile(r"`([^`\n]+)`")
MAKE_RE = re.compile(r"\bmake (?!-C )((?:[A-Za-z0-9_.-]+ ?)+)")  # `make -C <dir>` names another make file: not checked
LINE_REF_RE = re.compile(r"^(.+?):(\d+)(?:-(\d+))?$")

Span = tuple[int, str]


class MapCheckError(Exception):
    """A map file is malformed in a way that stops the check itself."""


def rel(path: Path) -> str:
    """Return a path as text relative to the repository."""
    return path.relative_to(REPO).as_posix()


def checked_lines(path: Path) -> list[Span]:
    """Return (line number, text) for every line of one file outside its unchecked blocks."""
    kept: list[Span] = []
    skipping = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith(UNCHECKED_BEGIN):
            skipping = True
        elif line.startswith(UNCHECKED_END):
            skipping = False
        elif not skipping:
            kept.append((number, line))
    if skipping:
        raise MapCheckError(f"{rel(path)}: an unchecked block is opened and never closed")
    return kept


def spans(path: Path) -> list[Span]:
    """Return every back-ticked span and every line of a fenced code block of one file."""
    found: list[Span] = []
    fenced = False
    for number, line in checked_lines(path):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif fenced:
            found.append((number, line))
        else:
            found.extend((number, text) for text in SPAN_RE.findall(line))
    return found


def top_names() -> tuple[frozenset[str], frozenset[str]]:
    """Return (top-level folders on disk, top-level files git tracks or would track)."""
    folders = frozenset(p.name for p in REPO.iterdir() if p.is_dir() and p.name not in SKIP_TOP)
    files = frozenset(f for f in mkmap.list_files() if "/" not in f and f not in SKIP_TOP)
    return folders, files


def path_tokens(span: str, tops: frozenset[str]) -> list[str]:
    """Return the words of one span that name a path this check can test."""
    tokens: list[str] = []
    for raw in span.split():
        token = raw.strip("\"'(),;")
        if not token or any(mark in token for mark in PLACEHOLDER_MARKS):
            continue
        first = token.split("/", 1)[0]
        if token.startswith(("/Users/", "../", "~/")) or ("/" in token and first in tops):
            tokens.append(token)
    return tokens


def moved_hint(path_text: str) -> str:
    """Say where a status file is now, when a file of that name exists elsewhere under docs/status/."""
    if not path_text.startswith("docs/status/"):
        return ""
    name = Path(path_text).name
    hits = sorted(rel(p) for p in STATUS.rglob(name)) if name else []
    return f" (now at {hits[0]})" if len(hits) == 1 else ""


def line_count(path: Path) -> int:
    """Return the number of lines of one file."""
    return len(path.read_bytes().splitlines())


def path_fault(token: str) -> str | None:
    """Return what is wrong with one named path, or None when it is there."""
    match = LINE_REF_RE.match(token)
    path_text = match.group(1) if match else token.rstrip(":.")
    if path_text.startswith(VOLATILE):
        return None
    if path_text.startswith("~/"):
        target = str(Path.home() / path_text[2:])
    elif path_text.startswith("/"):
        target = path_text
    else:
        target = str(REPO / path_text)
    if any(mark in path_text for mark in PATTERN_MARKS):
        return None if glob.glob(target) else "no file matches this pattern"
    if not Path(target).exists():
        return "is gone" + moved_hint(path_text)
    if match and Path(target).is_file():
        wanted = int(match.group(3) or match.group(2))
        have = line_count(Path(target))
        if wanted > have:
            return f"line {wanted} is past the end ({have} lines)"
    return None


def scanned_files() -> list[Path]:
    """Return the files whose named paths are tested."""
    files = sorted(MAP.glob("*.md"))
    files += [p for p in sorted(STATUS.rglob("*.md")) if rel(p) not in VERBATIM + HISTORY]
    return files


def check_paths(tops: frozenset[str]) -> list[str]:
    """Return one finding per named path that does not exist."""
    faults: list[str] = []
    for path in scanned_files():
        for number, span in spans(path):
            for token in path_tokens(span, tops):
                fault = path_fault(token)
                if fault:
                    faults.append(f"{rel(path)}:{number}: `{token}` {fault}")
    return faults


def named(path: Path) -> frozenset[str]:
    """Return every back-ticked word of one map file, without a trailing slash."""
    words: set[str] = set()
    for _number, span in spans(path):
        words.update(word.strip("\"'(),;").rstrip("/") for word in span.split())
    return frozenset(words)


def check_top_cover(folders: frozenset[str], files: frozenset[str]) -> list[str]:
    """Return one finding per top-level folder or file that the code map does not name."""
    have = named(CODE_MAP)
    return [f"{rel(CODE_MAP)}: top-level `{name}` is not named" for name in sorted(folders | files) if name not in have]


def scripts(files: tuple[str, ...]) -> list[str]:
    """Return the scripts and make files under the script roots."""
    roots = tuple(root + "/" for root in mkmap.SCRIPT_ROOTS)
    return [f for f in files if f.startswith(roots) and f.endswith(mkmap.SCRIPT_SUFFIXES)]


def check_script_cover(files: tuple[str, ...]) -> list[str]:
    """Return one finding per script folder the tools map does not name."""
    have = named(TOOLS_MAP)
    found = scripts(files)
    folders = sorted({str(Path(script).parent) for script in found})
    return [f"{rel(TOOLS_MAP)}: script folder `{folder}/` is not named" for folder in folders if folder not in have]


def check_make_targets(files: tuple[str, ...]) -> list[str]:
    """Return one finding per `make <target>` of a hand-written map that no make file defines."""
    targets = mkmap.make_targets(files)
    faults: list[str] = []
    for path in sorted(MAP.glob("*.md")):
        for number, span in spans(path):
            for group in MAKE_RE.findall(span):
                for word in group.split():
                    if not word.startswith("-") and word not in targets:
                        faults.append(f"{rel(path)}:{number}: `make {word}` is not a target of any make file")
    return faults


def check_index() -> list[str]:
    """Return one finding per map file the index does not link."""
    have = named(INDEX)
    pages = sorted(MAP.glob("*.md")) + sorted(mkmap.GEN.glob("*.md"))
    return [f"{rel(INDEX)}: `{rel(page)}` is not linked" for page in pages if page != INDEX and rel(page) not in have]


def check_generated() -> list[str]:
    """Return one finding per generated list that differs from a fresh run."""
    return [f"{name}: stale; run python3 -I tools/mkmap.py" for name in mkmap.stale(mkmap.render_all())]


def main() -> int:
    """Run every check; print the findings; return the exit code."""
    try:
        files = mkmap.list_files()
        folders, top_files = top_names()
        tops = folders | top_files
        faults = check_paths(tops)
        faults += check_top_cover(folders, top_files)
        faults += check_script_cover(files)
        faults += check_make_targets(files)
        faults += check_index()
        faults += check_generated()
    except (MapCheckError, mkmap.MapError, OSError) as error:
        print(f"map_check: FAIL: {error}")
        return 1
    for fault in faults:
        print(f"map_check: FAIL: {fault}")
    if faults:
        return 1
    print(f"map_check: OK: {len(scanned_files())} files read, {len(tops)} top-level entries and "
          f"{len(scripts(files))} scripts covered, generated lists current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
