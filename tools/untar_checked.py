#!/usr/bin/env python3
"""Unpack a source tarball only if every member is safe.

Usage: python3 -I untar_checked.py <tar.xz> <dest>

Pre-scans the whole archive and refuses (prints "REFUSED: <member>: <why>", exit 1, writes nothing) a member that
is absolute, has a ".." component, is a device or fifo, is outside one single top folder, or is a link whose
resolved target leaves that top folder. Otherwise extracts with filter="data" and prints "top=<name> members=<N>".
"""
import posixpath
import sys
import tarfile
from pathlib import Path


def refusal(member: tarfile.TarInfo, top: str) -> str | None:
    """Return why `member` is unsafe, or None when it is fine. `top` is the expected top folder name."""
    name = member.name
    parts = name.split("/")
    if name.startswith("/") or ".." in parts:
        return "absolute path or '..' component"
    if member.isdev() or member.isfifo():
        return "device or fifo"
    if parts[0] != top:
        return f"outside the single top folder '{top}'"
    if member.issym() or member.islnk():
        base = posixpath.dirname(name) if member.issym() else ""
        target = posixpath.normpath(posixpath.join(base, member.linkname))
        if member.linkname.startswith("/") or not (target == top or target.startswith(top + "/")):
            return f"link target '{member.linkname}' leaves the top folder"
    return None


def check_archive(tar_path: Path) -> tuple[str, int]:
    """Scan all members; return (top folder, member count) or raise SystemExit(1) after printing REFUSED."""
    with tarfile.open(tar_path, "r:xz") as archive:
        members = archive.getmembers()
    if not members:
        print("REFUSED: empty archive")
        raise SystemExit(1)
    top = members[0].name.split("/")[0]
    for member in members:
        why = refusal(member, top)
        if why is not None:
            print(f"REFUSED: {member.name}: {why}")
            raise SystemExit(1)
    return top, len(members)


def main(argv: list[str]) -> int:
    """Check then extract; returns the process exit code."""
    if len(argv) != 3:
        print("usage: untar_checked.py <tar.xz> <dest>", file=sys.stderr)
        return 2
    tar_path, dest = Path(argv[1]), Path(argv[2])
    top, count = check_archive(tar_path)
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "r:xz") as archive:
        archive.extractall(dest, filter="data")
    print(f"top={top} members={count}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
