#!/usr/bin/env python3
"""docs_check.py: the claims in the docs hold (step H's gate). Stdlib only, no network. Run: python3 -I tools/docs_check.py

    python3 -I tools/docs_check.py [--allow-missing PATH ...] [--plant-red]
    python3 -I tools/docs_check.py --emit-steps README.md [--block build]

Each check prints PASS <name> or FAIL <name>: <reason>; any FAIL exits 1. --plant-red plants one fault per check in a
temp copy of the docs and prints the FAIL lines it provokes (exit 1 when every plant fails exactly its own check, exit 2
when one does not). --emit-steps prints the README's steps block (or, with --block build, the build block) and exits 0.
"""
from __future__ import annotations

import argparse
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ("README.md", "STATUS.md", "docs/USING.md", "docs/HOST-API.md", "examples/README.md")
FIRST = "not affiliated with or endorsed by the Azahar project"
FORBIDDEN = (
    "full speed", "clean room", "clean-room", "50x", "51x", "/users/", "laz_lazpy_core",
    "macos 11 or later", "macos 11+", "macos 11.0 or later", "macos 11 and later",
    "decrypt", "aes_keys", "keys.txt", "title.keys", "prod.keys", "seeddb", "boot9", "sysdata", "clcerta",
    "patreon", "ko-fi", "donate", "sponsor", "azahar-emu/azahar/releases/download",
)
FENCE = re.compile(r"^```")


def read_docs(base: Path) -> dict[str, str]:
    """The five docs and every file under examples/, by repo-relative name."""
    out = {name: (base / name).read_text(encoding="utf-8") for name in DOCS if (base / name).is_file()}
    for path in sorted(q for q in (base / "examples").rglob("*") if q.is_file()) if (base / "examples").is_dir() else []:
        out.setdefault(f"examples/{path.relative_to(base / 'examples').as_posix()}", path.read_text(encoding="utf-8"))
    return out


def repo_files(root: Path) -> set[str]:
    """Tracked files plus untracked new ones (git), and every parent folder of them."""
    names: set[str] = set()
    for args in (["ls-files"], ["ls-files", "-o", "--exclude-standard"]):
        done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
        names.update(line for line in done.stdout.splitlines() if line)
    for name in list(names):
        names.update(str(p) for p in Path(name).parents if str(p) != ".")
    return names


def fenced_blocks(text: str) -> list[tuple[int, str, str]]:
    """(line index of the opening fence, its info word, its body) for every fenced block."""
    lines, blocks, start = text.split("\n"), [], None
    for index, line in enumerate(lines):
        if FENCE.match(line) and start is None:
            start = index
        elif FENCE.match(line):
            blocks.append((start, lines[start][3:].strip(), "\n".join(lines[start + 1:index])))
            start = None
    return blocks


def without_fences(text: str) -> str:
    lines, keep, inside = text.split("\n"), [], False
    for line in lines:
        if FENCE.match(line):
            inside = not inside
        elif not inside:
            keep.append(line)
    return "\n".join(keep)


def block_after(text: str, marker: str) -> str | None:
    """The body of the first fenced block that opens within 4 lines after the marker line; None when absent."""
    lines = text.split("\n")
    at = next((i for i, line in enumerate(lines) if line.strip() == f"<!-- docs_check: {marker} -->"), None)
    if at is None:
        return None
    for start, _, body in fenced_blocks(text):
        if at < start <= at + 4:
            return body
    return None


def section(text: str, title: str) -> list[str]:
    """The lines of the '## ...title...' section, up to the next '## ' heading."""
    lines, out, inside = text.split("\n"), [], False
    for line in lines:
        if line.startswith("## "):
            inside = title.lower() in line.lower()
        elif inside:
            out.append(line)
    return out


# ---- the checks: each returns a list of problems (empty: pass) ----

def check_numbers(docs: dict[str, str], root: Path) -> list[str]:
    rows = [ln for ln in section(docs.get("README.md", ""), "Measured numbers") if ln.startswith("|")]
    problems, data = [], [r for r in rows[2:]]
    if not data:
        return ["README has no Measured numbers table rows"]
    files = repo_files(root)
    for row in data:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) != 6 or not all(cells[1:5]):
            problems.append(f"row needs What|Value|Scene|Load|Date|Source, all filled: {row[:60]}")
            continue
        problems += row_problems(cells, root, files)
    return problems


def row_problems(cells: list[str], root: Path, files: set[str]) -> list[str]:
    what, value, _scene, load, date, source = cells
    match = re.fullmatch(r"`?(docs/research/[\w.-]+\.md):(\d+(?:,\d+)*)`?", source)
    if not match or match.group(1) not in files:
        return [f"{what}: Source {source!r} is not docs/research/<tracked file>.md:<line>"]
    lines = (root / match.group(1)).read_text(encoding="utf-8").split("\n")
    near = "\n".join("\n".join(lines[max(0, int(n) - 3):int(n) + 2]) for n in match.group(2).split(","))
    out = []
    for token in re.findall(r"\d[\d,.:-]*", " ".join((value, load, date))):
        token = token.rstrip(".,:-")
        if not re.search(r"(?<![\d.,:-])" + re.escape(token) + r"(?!\d)", near):
            out.append(f"{what}: {token} is not within 2 lines of {match.group(1)}:{match.group(2)}")
    return out


def check_forbidden(docs: dict[str, str], root: Path) -> list[str]:
    out = []
    for name, text in docs.items():
        low = text.lower()
        out += [f"{name}: {word!r}" for word in FORBIDDEN if word in low]
    return out


def check_gated(docs: dict[str, str], root: Path) -> list[str]:
    body = "\n".join(section(docs.get("STATUS.md", ""), "What works"))
    bullets = re.split(r"\n(?=- )", body.strip())
    bullets = [re.sub(r"\s*\n\s*", " ", b).strip() for b in bullets if b.startswith("- ")]
    out = [] if bullets else ["STATUS.md has no bullets under What works"]
    for bullet in bullets:
        match = re.search(r"\(laz-(\d+)\)$", bullet)
        if not match:
            out.append(f"bullet without a closing (laz-NNN): {bullet[:50]}")
            continue
        found = [p for p in (root / "docs/status/lazpy/5-done").glob(f"{match.group(1)}-*.md")
                 if f"id: laz-{match.group(1)}" in p.read_text(encoding="utf-8").split("\n")]
        if not found:
            out.append(f"laz-{match.group(1)} has no item file with that id in 5-done/")
    return out


def check_quickstart(docs: dict[str, str], root: Path) -> list[str]:
    block = block_after(docs.get("README.md", ""), "quickstart")
    if block is None:
        return ["README has no fenced block after the quickstart marker"]
    if block.rstrip("\n") != docs.get("examples/quickstart.py", "").rstrip("\n"):
        return ["the README block differs from examples/quickstart.py"]
    return []


def check_steps(docs: dict[str, str], root: Path) -> list[str]:
    readme, out = docs.get("README.md", ""), []
    for marker in ("steps", "steps-build"):
        if block_after(readme, marker) is None:
            out.append(f"no fenced block after <!-- docs_check: {marker} -->")
    build = block_after(readme, "steps-build") or ""
    out += [f"the build block does not set {var}" for var in ("DEVKITPRO", "DEVKITARM") if f"{var}=" not in build]
    return out


def check_links(docs: dict[str, str], root: Path, allow: tuple[str, ...] = ()) -> list[str]:
    files, out = repo_files(root), []
    allowed = {posixpath.normpath(a) for a in allow}
    for name in DOCS:
        for target in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", without_fences(docs.get(name, ""))):
            if re.match(r"(https?:|mailto:|#)", target):
                continue
            path = posixpath.normpath(posixpath.join(posixpath.dirname(name), target.split("#")[0]))
            if path not in files and path not in allowed:
                out.append(f"{name}: link {target} does not resolve")
    return out


def check_first_paragraph(docs: dict[str, str], root: Path) -> list[str]:
    lines = docs.get("README.md", "").split("\n")
    start = next((i for i, ln in enumerate(lines) if ln.startswith("# ")), None)
    if start is None:
        return ["README has no title line"]
    para, started = [], False
    for line in lines[start + 1:]:
        if line.strip():
            started = True
            para.append(line.strip())
        elif started:
            break
    return [] if FIRST.lower() in " ".join(para).lower() else [f"the first paragraph lacks: {FIRST}"]


def check_images(docs: dict[str, str], root: Path) -> list[str]:
    return [f"{n}: an image" for n in DOCS if "![" in docs.get(n, "") or "<img" in docs.get(n, "").lower()]


CHECKS = (("numbers", check_numbers), ("forbidden", check_forbidden), ("gated", check_gated),
          ("quickstart", check_quickstart), ("steps", check_steps), ("links", check_links),
          ("first-paragraph", check_first_paragraph), ("images", check_images))


def run_checks(base: Path, allow: tuple[str, ...], quiet: bool = False) -> dict[str, list[str]]:
    docs, failed = read_docs(base), {}
    for name, func in CHECKS:
        problems = func(docs, ROOT, allow) if func is check_links else func(docs, ROOT)
        if problems:
            failed[name] = problems
        if not quiet:
            print(f"FAIL {name}: " + "; ".join(problems) if problems else f"PASS {name}")
    return failed


# ---- --plant-red ----

def plant(text: str, old: str, new: str) -> str:
    assert old in text, f"plant target {old!r} not found"
    return text.replace(old, new, 1)


def table_row(text: str) -> str:
    return next(ln for ln in section(text, "Measured numbers") if ln.startswith("|") and "---" not in ln
                and ln.split("|")[1].strip() != "What")


def make_plants(docs: dict[str, str]) -> list[tuple[str, str, str, callable]]:
    """(check, label, file, edit) one per planted fault."""
    row = table_row(docs["README.md"])
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    return [
        ("numbers", "a Value not in its source line", "README.md", lambda t: plant(t, row, row.replace(cells[1], "987654.3x", 1))),
        ("numbers", "a Date not in its source", "README.md", lambda t: plant(t, row, row.replace(cells[4], "1999-01-01", 1))),
        ("forbidden", "the words full speed and keys.txt", "STATUS.md", lambda t: t + "\nRuns at full speed with keys.txt.\n"),
        ("gated", "a works bullet with (laz-999)", "STATUS.md", lambda t: plant(t, "## What works\n", "## What works\n\n- planted (laz-999)\n")),
        ("quickstart", "one changed byte in the example", "examples/quickstart.py", lambda t: t + "#"),
        ("steps", "a missing steps-build marker", "README.md", lambda t: plant(t, "<!-- docs_check: steps-build -->", "")),
        ("links", "a dead link", "README.md", lambda t: t + "\n[planted](docs/NO-SUCH-FILE.md)\n"),
        ("first-paragraph", "the first paragraph without the line", "README.md", lambda t: plant(t, FIRST, "affiliated")),
        ("images", "one image", "README.md", lambda t: t + "\n![x](README.md)\n"),
    ]


def plant_red(allow: tuple[str, ...]) -> int:
    plants, missed = make_plants(read_docs(ROOT)), 0
    for check, label, name, edit in plants:
        with tempfile.TemporaryDirectory(prefix="docs_check_") as tmp:
            for src in read_docs(ROOT):
                (Path(tmp) / src).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / src, Path(tmp) / src)
            target = Path(tmp) / name
            target.write_text(edit(target.read_text(encoding="utf-8")), encoding="utf-8")
            failed = run_checks(Path(tmp), allow, quiet=True)
        if list(failed) == [check]:
            print(f"FAIL {check}: planted {label}: {'; '.join(failed[check][:3])}")
        else:
            missed += 1
            print(f"PLANT-MISS {check}: planted {label}: checks that failed: {sorted(failed) or 'none'}")
    return 2 if missed else 1


# ---- --emit-steps ----

def emit_steps(readme: Path, which: str) -> int:
    body = block_after(readme.read_text(encoding="utf-8"), "steps-build" if which == "build" else "steps")
    if body is None:
        print(f"docs_check: no {which} block in {readme}", file=sys.stderr)
        return 1
    print(body)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--allow-missing", nargs="*", default=[], metavar="PATH")
    parser.add_argument("--emit-steps", metavar="README")
    parser.add_argument("--block", choices=("steps", "build"), default="steps")
    parser.add_argument("--plant-red", action="store_true")
    args = parser.parse_args()
    if args.emit_steps:
        return emit_steps(Path(args.emit_steps), args.block)
    allow = tuple(args.allow_missing)
    if args.plant_red:
        return plant_red(allow)
    return 1 if run_checks(ROOT, allow) else 0


if __name__ == "__main__":
    sys.exit(main())
