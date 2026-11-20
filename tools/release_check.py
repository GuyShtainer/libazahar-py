#!/usr/bin/env python3
"""Machine checks for a staged release (step I).

Usage: python3 -I tools/release_check.py runs/release/<tag> (for example runs/release/v1.0.0) [--skip-pins] [--pre-push] [--plant-red]
           [--nm-output F] [--otool-output F] [--strings-output F] [--link F] [--inputs F] [--fetch F]
           [--pyproject F] [--repo DIR]
       $LAZ_WIN_PY -I tools/release_check.py <dir> --inherit v1.0.0 --gate-f2 FILE [--inherit-sums FILE]
           [--no-runtime-source] [--skip-pins] [--pre-push] [--plant-red] [--fetch F] [--repo DIR]

--inherit v1.0.0 checks a v1.1.0 release staged by `mkrelease.sh --inherit` (the PC, the Windows Python, MSYS2): the
macOS side is the v1.0.0 bytes, checked against the pinned digest of v1.0.0's SHA256SUMS (downloaded from the v1.0.0
page, or --inherit-sums FILE; either way it must match the pin); the Windows zip is checked from --gate-f2 (the CI
artifact's gate_f2.txt: shared contract 1) instead of the live tree. --plant-red exits 0 when every plant failed on
its own reason, 2 when one did not.

python3 -I tools/release_check.py --self-test checks check 13 with the reading copy absent (SKIP, PEND under --pre-push),
and the "1c host zips" row on staged stand-ins (including a throwaway git repo for the commit rule).

Check 1c (both release kinds): the prebuilt host zips libazahar-py-host-<version>-windows-x64.zip and -macos-arm64.zip
(<version> is the tag without the v). A zip that is absent is a SKIP, never a PASS (and, as for every SKIP, a FAIL under
--pre-push). A zip that is present must be listed in SHA256SUMS with its own sha256, equal fetch.sh's pin
(LAZPY_HOST_SHA_WIN / LAZPY_HOST_SHA_MAC; TBD is a PEND, --skip-pins a SKIP), hold exactly its two binaries, LICENSE
and SOURCE.md (the Windows zip also NOTICES.md), and its SOURCE.md must name a commit (a 40-hex id). That commit must be
an ancestor of the tag (HEAD when the tag does not exist yet) and host/ and the Makefile must be identical at the commit
and at the tag; otherwise FAIL. A repo with no history (or without that commit) is a SKIP with its reason. A host
binary holding a /Users/ path (a macOS build that was not stripped) is a FAIL.

Prints one line per check: PASS, FAIL, SKIP or PEND, plus NOTE lines for the audit. Any FAIL exits 1; under
--pre-push every SKIP and PEND is a FAIL. --plant-red plants one fault per check in a temp folder outside the repo
and passes only if each check fails on its plant. Key material is never printed or written: windows of the key and
certificate arrays are made in memory from the reading copy of Azahar's source at run time (tests/gate_f2.py).
LAZ_PRIVATE_NEEDLES, when it names a file, adds private-string needles; the value - (or stdin) reads them from
standard input instead, so they never touch a disk. A hit prints only a file name and a line number, never the needle.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 10):  # the PC's default python is 3.7: use LAZ_WIN_PY (the venv's python.exe)
    raise SystemExit("release_check.py: Python 3.10 or newer is needed; run it with the interpreter in LAZ_WIN_PY")

import argparse
import hashlib
import io
import itertools
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

Items = list[tuple[str, str]]  # (kind, message); kind is FAIL, NOTE, SKIP or PEND
NOREPLY = "293649481+GuyShtainer@users.noreply.github.com"
SRC_REL = "dl/azahar-src/unpacked/azahar-unified-source-2126.2"
TREE_REL = "dl/azahar-src/build-src/azahar-unified-source-2126.2"
LINK_REL = "build-core/build/src/citra_libretro/CMakeFiles/citra_libretro.dir/link.txt"
FORBIDDEN_SUFFIX = (".dylib", ".zip", ".tar", ".tar.xz", ".tar.gz", ".3ds", ".cci", ".cxi", ".cia", ".3dsx", ".gba",
                    ".nds", ".sav")
FORBIDDEN_NAMES = ("aes_keys.txt", "keys.txt", "seeddb.bin")
FORBIDDEN_DIRS = ("dl", "vendor", "runs", "sdmc", "nand", "sysdata")
KEY_WORDS = ("keys.txt", "aes_keys", "seeddb", "boot9", "title.keys")
LONG_HEX_RUN = re.compile(r"(0x[0-9a-fA-F]{1,2}[\s,]+){7}0x[0-9a-fA-F]{1,2}")
ZIP_NAMES = ["COPYING-azahar.txt", "LICENSE", "NOTICES.md", "SOURCE.md", "azahar_lazpy_libretro.dylib", "build.inputs"]
EXPORT_EXTRA = {"_lazpy_read_memory", "_lazpy_write_memory", "_lazpy_movie_play", "_lazpy_threads"}
OSSL_EXPECTED = ("/opt/homebrew/etc/openssl@3", "/opt/homebrew/Cellar/openssl@3/")
# devkitPro's newlib is built on its maintainer's machine; its assert strings (dtoa.c, mprec.c) carry that build
# path into every devkitARM program, the test app included. A third-party toolchain path, not ours: a NOTE, not a FAIL.
DKP_NEWLIB_RE = re.compile(r"/home/davem/projects/devkitpro/pacman-packages/devkitarm/newlib/src/newlib-[\w.]+/newlib/[\w./-]+")


class AssetError(Exception):
    """An asset the checks need is missing, or more than one file matches it."""


# the build-files asset's tag per platform: "*" until main() knows the release tag (and, with --inherit, v1.0.0's)
BUILD_TAG = {"mac": "*", "win": "*"}


def asset(rel: Path, platform: str, kind: str) -> Path:
    """The one file for (platform, kind) in a staged release; AssetError when zero or several files match."""
    patterns = {("mac", "zip"): "azahar_lazpy_libretro-*-macos-arm64.zip", ("win", "zip"): "azahar_lazpy_libretro-*-windows-x64.zip",
                ("mac", "build"): f"libazahar-py-core-build-{BUILD_TAG['mac']}.tar.gz",
                ("win", "build"): f"libazahar-py-core-build-{BUILD_TAG['win']}.tar.gz"}
    pattern = patterns[(platform, kind)]
    found = sorted(rel.glob(pattern))
    if len(found) != 1:
        raise AssetError(f"{len(found)} files match {pattern} in {rel.name}; exactly one is needed")
    return found[0]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def run(cmd: list[str], cwd: Path | None = None, data: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, input=data, capture_output=True, check=False)


def run_text(cmd: list[str], cwd: Path | None = None) -> str:
    return run(cmd, cwd).stdout.decode("utf-8", errors="replace")


def read_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in path.read_text(errors="replace").splitlines():
        key, sep, value = raw.partition("=")
        if sep and not raw.lstrip().startswith("#"):
            out[key.strip()] = value.strip()
    return out


def git(repo: Path, *argv: str) -> str:
    return run_text(["git", "-C", str(repo), *argv])


# ------------------------------------------------------------------------------------------- 1 assets
def expected_assets(pin: dict[str, str], tag: str) -> list[str]:
    return sorted([f"azahar_lazpy_libretro-{pin['AZAHAR_TAG']}-lazpy.{pin['LAZPY_REV']}-macos-arm64.zip",
                   f"azahar-unified-source-{pin['AZAHAR_TAG']}-lazpy-nokeys.tar.xz",
                   f"openssl-{pin['OPENSSL_VERSION']}.tar.gz", "citra_system_archives-f470e0c.tar.gz",
                   f"libazahar-py-core-build-{tag}.tar.gz", "testapp.3dsx", "NOTICES.md", "SOURCE.md", "SHA256SUMS"])


def asset_set(rel: Path, names: list[str]) -> tuple[list[str], Items]:
    """The expected names plus the host zips found (a caller may already list them), and a FAIL if rel holds another set."""
    have = sorted(p.name for p in rel.iterdir())
    names = sorted(set(names) | set(host_names_present(rel)))
    if have != names:
        return names, [("FAIL", f"asset set differs: extra {sorted(set(have) - set(names))}, missing {sorted(set(names) - set(have))}")]
    return names, []


def assets_findings(rel: Path, names: list[str]) -> Items:
    names, out = asset_set(rel, names)
    if out:
        return out
    for line in (rel / "SHA256SUMS").read_text().splitlines():
        digest, _sep, name = line.partition("  ")
        if not (rel / name).is_file() or sha256_file(rel / name) != digest:
            out.append(("FAIL", f"SHA256SUMS does not match {name}"))
    listed = {line.partition("  ")[2] for line in (rel / "SHA256SUMS").read_text().splitlines()}
    if listed != set(names) - {"SHA256SUMS"}:
        out.append(("FAIL", "SHA256SUMS lists a different file set"))
    out += zip_findings(asset(rel, "mac", "zip"))
    return out


def zip_findings(zip_path: Path) -> Items:
    with zipfile.ZipFile(zip_path) as archive:
        names = sorted(archive.namelist())
        licence = archive.read("LICENSE").decode(errors="replace").splitlines()[:2] if "LICENSE" in names else []
    out: Items = []
    if names != ZIP_NAMES:
        out.append(("FAIL", f"core zip members are {names}"))
    if not licence or "GNU GENERAL PUBLIC LICENSE" not in licence[0] or "Version 3" not in licence[1]:
        out.append(("FAIL", "the zip's LICENSE is not the GPLv3 text"))
    return out


# ------------------------------------------------------------------------------------------- 1c host zips
HOST_KINDS = {  # key: (file name part, the zip members besides LICENSE and SOURCE.md (Windows adds NOTICES.md), fetch.sh pin name)
    "win": ("windows-x64", ["NOTICES.md", "azhost.exe", "libazhost.dll"], "LAZPY_HOST_SHA_WIN"),
    "mac": ("macos-arm64", ["azhost", "libazhost.dylib"], "LAZPY_HOST_SHA_MAC"),
}
HOST_GLOB = "libazahar-py-host-*.zip"


def host_zip_name(tag: str, key: str) -> str:
    return f"libazahar-py-host-{tag.removeprefix('v')}-{HOST_KINDS[key][0]}.zip"


def host_names_present(rel: Path) -> list[str]:
    """The host zips in a staged release (any name that matches the glob), for the asset set of check 1."""
    return sorted(p.name for p in rel.glob(HOST_GLOB))


def host_commit_findings(repo: Path | None, tag: str, name: str, source: str) -> Items:
    """The commit SOURCE.md names must be an ancestor of the tag and leave host/ and the Makefile as they are at the tag."""
    found = re.search(r"\b[0-9a-f]{40}\b", source)
    if found is None:
        return []
    if repo is None:
        return [("SKIP", f"{name}: no repo given, so the build commit was not compared with the tag")]
    commit = found.group(0)
    # no ^{commit} peel in these arguments: the MSYS git on Windows expands the braces
    if run(["git", "-C", str(repo), "cat-file", "-t", commit]).stdout.strip() != b"commit":
        return [("SKIP", f"{name}: commit {commit[:12]} is not in this repo (no history, or a shallow clone), so it was not compared with the tag")]
    ref = tag if run(["git", "-C", str(repo), "rev-parse", "-q", "--verify", f"refs/tags/{tag}"]).returncode == 0 else "HEAD"
    out: Items = []
    if run(["git", "-C", str(repo), "merge-base", "--is-ancestor", commit, ref]).returncode != 0:
        out.append(("FAIL", f"{name}: build commit {commit[:12]} is not an ancestor of {ref}"))
    elif run(["git", "-C", str(repo), "diff", "--quiet", commit, ref, "--", "host", "Makefile"]).returncode != 0:
        out.append(("FAIL", f"{name}: host/ or the Makefile changed between the build commit {commit[:12]} and {ref}: build the host again"))
    return out


def host_one_findings(rel: Path, tag: str, key: str, fetch_values: dict[str, str], skip_pins: bool,
                      repo: Path | None = None) -> Items:
    name = host_zip_name(tag, key)
    path = rel / name
    if not path.is_file():
        return [("SKIP", f"{name} is not in this release (the host zips come with v1.3.0 and later)")]
    out: Items = []
    digest = sha256_file(path)
    sums = parse_sums(read_text(rel / "SHA256SUMS"))
    if sums.get(name) != digest:
        out.append(("FAIL", f"SHA256SUMS has no matching line for {name}"))
    binaries = HOST_KINDS[key][1]
    try:
        with zipfile.ZipFile(path) as archive:
            members = sorted(archive.namelist())
            source = archive.read("SOURCE.md").decode(errors="replace") if "SOURCE.md" in members else ""
            licence = archive.read("LICENSE").decode(errors="replace").splitlines()[:2] if "LICENSE" in members else []
    except zipfile.BadZipFile:
        return out + [("FAIL", f"{name} is not a zip")]
    if members != sorted(binaries + ["LICENSE", "SOURCE.md"]):
        out.append(("FAIL", f"{name} members are {members}"))
    if not licence or "GNU GENERAL PUBLIC LICENSE" not in licence[0] or "Version 3" not in licence[1]:
        out.append(("FAIL", f"{name}'s LICENSE is not the GPLv3 text"))
    if not re.search(r"\b[0-9a-f]{40}\b", source):
        out.append(("FAIL", f"{name}'s SOURCE.md names no commit"))
    out += host_commit_findings(repo, tag, name, source)
    # private strings in the text and the binaries. A Windows runner path is a NOTE (the debug info carries it); a /Users/
    # path stays a FAIL: the macOS job runs `strip -S`, so any path left in a Mach-O file means it did not.
    with zipfile.ZipFile(path) as archive:
        for member in members:
            if member == "LICENSE":
                continue
            data = archive.read(member)
            text = data.decode(errors="replace") if member == "SOURCE.md" else strings_py(data)
            for label, regex in PRIVATE_RES:
                if regex.search(text):
                    out.append(("NOTE" if label == "GitHub runner path" else "FAIL", f"{name}: {member} holds a {label}"))
    pin_name = HOST_KINDS[key][2]
    pin = fetch_values.get(pin_name, "")
    if skip_pins:
        out.append(("SKIP", f"{pin_name}: --skip-pins"))
    elif not pin or pin.startswith("TBD"):
        out.append(("PEND", f"fetch.sh {pin_name} is TBD (the main loop sets it when the release is staged)"))
    elif pin != digest:
        out.append(("FAIL", f"fetch.sh {pin_name} differs from the staged {name}"))
    return out


def host_findings(rel: Path, tag: str, fetch_text: str, skip_pins: bool, repo: Path | None = None) -> Items:
    values = dict(re.findall(r"^([A-Z_]+)=(\S+)$", fetch_text, re.M))
    wanted = {host_zip_name(tag, key) for key in HOST_KINDS}
    out: Items = [("FAIL", f"{name} is not a host zip of {tag}") for name in host_names_present(rel) if name not in wanted]
    for key in HOST_KINDS:
        out += host_one_findings(rel, tag, key, values, skip_pins, repo)
    return out


# ------------------------------------------------------------------------------------------- 2 keyblob
def zip_member(zip_path: Path, name: str) -> bytes:
    with zipfile.ZipFile(zip_path) as archive:
        return archive.read(name)


def keyblob_check(rel: Path, repo: Path, inputs: Path) -> Items:
    sys.path.insert(0, str(repo / "tests"))
    import gate_f2
    core = repo / "build-core" / "azahar_lazpy_libretro.dylib"
    zipped = zip_member(asset(rel, "mac", "zip"), "azahar_lazpy_libretro.dylib")
    out: Items = []
    if sha256_bytes(zipped) != sha256_file(core):
        out.append(("FAIL", "the zip's dylib is not the gated core (sha256 differs from build-core/)"))
    findings = gate_f2.keyblob_findings(repo / "build-core", core, repo / SRC_REL, repo / TREE_REL, repo)
    out += [("FAIL", f"keyblob: {item}") for item in findings]
    head = read_kv(inputs).get("head", "?")
    out.append(("NOTE", f"build.inputs head={head} (translate with docs/commit-map-g8c.tsv, then g8b, then g8)"))
    return out


# ------------------------------------------------------------------------------------------- 3-5 binary
def exports_findings(nm_text: str) -> Items:
    names = {line.split()[-1] for line in nm_text.splitlines() if len(line.split()) >= 3}
    retro = {n for n in names if n.startswith("_retro_")}
    out: Items = []
    if len(retro) != 25:
        out.append(("FAIL", f"{len(retro)} _retro_* exports, expected 25"))
    if names - retro != EXPORT_EXTRA:
        out.append(("FAIL", f"other exports are {sorted(names - retro)}"))
    return out


def version_findings(strings_text: str) -> Items:
    return [] if "2126.2" in strings_text.split() or "2126.2" in strings_text else [("FAIL", "no 2126.2 string in the core")]


def linkage_findings(otool_text: str, strings_text: str) -> Items:
    out: Items = []
    for line in otool_text.splitlines()[1:]:
        path = line.strip().split(" (")[0]
        if not path:
            continue
        if not (path.startswith(("/System/Library/", "/usr/lib/")) or path == "@rpath/azahar_libretro.dylib"):
            out.append(("FAIL", f"links {path}"))
        if "libMoltenVK" in path or "libvulkan" in path:
            out.append(("FAIL", f"links {path}"))
    for needle in ("MVKInstance", "MVKDevice"):
        if needle in strings_text:
            out.append(("FAIL", f"the core holds {needle}"))
    return out


# ------------------------------------------------------------------------------------------- 6 openssl
def md_sha(md_text: str) -> str:
    found = re.search(r"Source:.*?([0-9a-f]{64})", md_text, re.S)
    return found.group(1) if found else ""


def sbom_sha(keg: Path) -> str:
    try:
        doc = json.loads((keg / "sbom.spdx.json").read_text())
    except (OSError, ValueError):
        return ""
    for package in doc.get("packages", []):
        if str(package.get("downloadLocation", "")).endswith(".tar.gz") and "github.com/openssl/openssl" in package["downloadLocation"]:
            return package["checksums"][0]["checksumValue"]
    return ""


def openssl_findings(ossl: Path, staged: Path, md_text: str, sbom: str, version: str, md_version: str,
                     pre_push: bool) -> Items:
    out: Items = []
    want = sha256_file(ossl)
    if md_sha(md_text) != want:
        out.append(("FAIL", "OSSL sha256 differs from core/OPENSSL.md's"))
    if sbom and sbom != want:
        out.append(("FAIL", "OSSL sha256 differs from the keg's SBOM"))
    if sha256_file(staged) != want:
        out.append(("FAIL", "the staged OpenSSL asset is not OSSL"))
    if not (ossl.name == f"openssl-{version}.tar.gz" and f"Version: {version}" in md_text and md_version == version):
        out.append(("FAIL", "openssl_version, the tarball name and core/OPENSSL.md disagree"))
    return out


def keg_findings(inputs: dict[str, str], pre_push: bool) -> Items:
    keg = Path(inputs.get("openssl_prefix", ""))
    out: Items = []
    now = os.path.realpath("/opt/homebrew/opt/openssl@3")
    out.append(("NOTE", f"openssl_prefix {keg} ; /opt/homebrew/opt/openssl@3 resolves to {now}"))
    if str(keg) != now:
        out.append(("FAIL" if pre_push else "NOTE", "openssl_prefix is not what /opt/homebrew/opt/openssl@3 resolves to"))
    for lib, key in (("libssl.a", "openssl_libssl_sha256"), ("libcrypto.a", "openssl_libcrypto_sha256")):
        path = keg / "lib" / lib
        if not path.is_file() or sha256_file(path) != inputs.get(key):
            out.append(("FAIL" if pre_push else "NOTE", f"{lib} in the keg no longer matches build.inputs (the pin was lost)"))
    return out


# ------------------------------------------------------------------------------------------- 7 private
PRIVATE_RES = [("/Users/", re.compile(r"/Users/")), ("@gmail.com", re.compile(r"@gmail\.com", re.I)),
               (".local address", re.compile(r"[A-Za-z0-9][\w.-]*\.local\b")),
               ("MAC address", re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")),
               ("private IPv4", re.compile(r"\b(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168|169\.254)\.\d{1,3}\.\d{1,3}\b")),
               # index 4 above is used by private_notes: new patterns go after it
               ("Windows profile path", re.compile(r"\b[a-z]:[\\/]+Users[\\/]+[^\s\\/\"'<>]+", re.I)),
               ("Linux home path", re.compile(r"(?<![\w.])/home/[A-Za-z_][\w.-]*")),
               ("MSYS2 profile path", re.compile(r"(?<!\w)/[a-z]/Users/[^\s/\"'<>]+", re.I)),
               ("WSL profile path", re.compile(r"/mnt/[a-z]/Users/[^\s/\"'<>]+", re.I)),
               ("GitHub runner path", re.compile(r"/home/runner\b|\b[a-z]:[\\/]+a[\\/]|\brunneradmin\b|/__w/|/github/home\b", re.I))]
PRIVATE_PLANTS = [("Windows profile path", "C:\\Users\\x\\a"), ("Windows profile path", "d:/users/x/a"),
                  ("Linux home path", "see /home/someone/x"), ("MSYS2 profile path", "see /c/Users/x/y"),
                  ("WSL profile path", "see /mnt/c/Users/x/y"), ("GitHub runner path", "see /home/runner/work/r/r"),
                  ("GitHub runner path", "D:\\a\\r\\r"), ("GitHub runner path", "C:\\Users\\runneradmin\\x")]
IPV4_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def load_needles(path: str | None) -> list[tuple[int, re.Pattern[str]]]:
    if path in ("-", "stdin", "/dev/stdin"):  # the needles come on standard input: they never touch a disk
        text = sys.stdin.read()
    elif path and Path(path).is_file():
        text = Path(path).read_text(errors="replace")
    else:
        return []
    out = []
    for number, raw in enumerate(text.splitlines(), 1):
        left = raw.partition("==>")[0].strip()
        if left and not left.startswith("#"):
            if left.startswith("regex:"):
                pattern = left[len("regex:"):]
            else:
                pattern = re.escape(left[len("literal:"):] if left.startswith("literal:") else left)
            out.append((number, re.compile(pattern, re.I)))
    return out


NOTICE_FILES = ("NOTICES.md", "zip:NOTICES.md", "NOTICES-windows-x64.md", "zip-mac:NOTICES.md", "zip-win:NOTICES.md")


def allowed_addresses(repo: Path, notices: str) -> frozenset[str]:
    """Addresses that NOTICES.md quotes and that appear in a pinned upstream input (the font files, the newlib file,
    the Azahar source files it names). Only these may stay in NOTICES.md."""
    upstream = [repo / "dl/font-licences/Montserrat-v4.001-OFL.txt", repo / "dl/font-licences/unifont-10.0.05-notice.txt",
                repo / "dl/newlib-licence/COPYING.NEWLIB-4.6.0"]
    upstream += [repo / TREE_REL / rel for rel in re.findall(r"^- `(src/[^`]+)`", notices, re.M)]
    upstream += [repo / SRC_REL / "externals" / path for path in re.findall(r"^Folder: `externals/([^`]+)`", notices, re.M)]
    text = "\n".join(p.read_text(errors="replace") for p in upstream if p.is_file())
    return frozenset(a for a in EMAIL_RE.findall(notices) if a.lower().endswith("@gmail.com") and a in text)


def private_findings(texts: dict[str, str], needles: list[tuple[int, re.Pattern[str]]], need_file: bool,
                     allowed: frozenset[str] = frozenset()) -> Items:
    out: Items = []
    for name, text in sorted(texts.items()):
        shown = text
        if name in NOTICE_FILES:
            for address in allowed:
                shown = shown.replace(address, "")
        if name == "testapp strings":
            for path in sorted(set(DKP_NEWLIB_RE.findall(shown))):
                out.append(("NOTE", f"NOTE expected: {name} holds devkitPro's newlib build path {path}"))
            shown = DKP_NEWLIB_RE.sub("", shown)
        for label, regex in PRIVATE_RES:
            if regex.search(shown):
                out.append(("FAIL", f"{name} holds a {label}"))
        for number, regex in needles:
            if regex.search(text):
                out.append(("FAIL", f"{name} hits needle line {number}"))
        out += private_notes(name, shown)
    if not needles and need_file:
        out.append(("SKIP", "LAZ_PRIVATE_NEEDLES is not set: the needle search did not run"))
    return out


def private_notes(name: str, text: str) -> Items:
    notes: Items = []
    others = sorted({m for m in IPV4_RE.findall(text) if not PRIVATE_RES[4][1].fullmatch(m)})
    if others:
        notes.append(("NOTE", f"{name}: IPv4 literals {others[:5]} ({len(others)})"))
    mails = sorted({m for m in EMAIL_RE.findall(text) if not m.lower().endswith("@gmail.com")})
    if mails:
        notes.append(("NOTE", f"{name}: email-like strings {len(mails)} (audit)"))
    homebrew = sorted({m for m in re.findall(r"/opt/homebrew/[\w@./-]*", text)})
    for path in homebrew:
        kind = "NOTE expected" if path.startswith(OSSL_EXPECTED) else "NOTE"
        notes.append(("NOTE", f"{kind}: {name} holds {path}"))
    return notes


def strings_of(data: bytes, tmp: Path, label: str) -> str:
    path = tmp / label
    path.write_bytes(data)
    return run_text(["/usr/bin/strings", "-a", str(path)])


def private_texts(rel: Path, repo: Path, tmp: Path, core_strings: str) -> dict[str, str]:
    zip_path = asset(rel, "mac", "zip")
    texts = {"core strings": core_strings}
    with zipfile.ZipFile(zip_path) as archive:
        for name in ZIP_NAMES:
            if name != "azahar_lazpy_libretro.dylib":
                texts[f"zip:{name}"] = archive.read(name).decode(errors="replace")
    with tarfile.open(asset(rel, "mac", "build")) as build:
        for member in build.getmembers():
            if member.isfile():
                texts[f"build-files:{member.name}"] = build.extractfile(member).read().decode(errors="replace")  # type: ignore[union-attr]
    texts["testapp strings"] = strings_of((rel / "testapp.3dsx").read_bytes(), tmp, "testapp.bin")
    for name in ("NOTICES.md", "SOURCE.md"):
        texts[name] = (rel / name).read_text(errors="replace")
    notes = repo / "docs" / "release-notes" / f"{rel.name}.md"
    if notes.is_file():
        texts["release notes"] = notes.read_text(errors="replace")
    return texts


# ------------------------------------------------------------------------------------------- 8 notices
NOTICE_PHRASES = ("The OpenSSL Project Authors", "Code from FAAD2 is copyright (c) Nero AG, www.nero.com",
                  "SIL OPEN FONT LICENSE Version 1.1", "Copyright 2011 - 2016 The Montserrat Project Authors",
                  "GNU Unifont 10.0.05", "Copyright (C) 1998-2017 Roman Czyborra", "848af47", "5e6b5df", "bbe60b5", "47cdc93",
                  "open_source_archives")


def notices_phrase_findings(text: str) -> Items:
    out: Items = [("FAIL", f"NOTICES.md lacks: {p}") for p in NOTICE_PHRASES if p not in text]
    if "Nintendo's" in text:
        out.append(("FAIL", "NOTICES.md says \"Nintendo's\""))
    return out


def notices_check(rel: Path, repo: Path, pre_push: bool, link: Path, inputs: Path) -> Items:
    cmd = [sys.executable, "-I", str(repo / "tools" / "mknotices.py"), "--link", str(link), "--deps", str(repo / "build-core" / "build"),
           "--tree", str(repo / TREE_REL), "--src", str(repo / SRC_REL), "--inputs", str(inputs),
           "--openssl", str(repo / "dl/openssl-src/openssl-3.6.5.tar.gz"),
           "--sysarch", str(repo / "dl/sysarch-src/citra_system_archives-f470e0c.tar.gz"),
           "--newlib", str(repo / "dl/newlib-licence/COPYING.NEWLIB-4.6.0"),
           "--ofl", str(repo / "dl/font-licences/Montserrat-v4.001-OFL.txt"),
           "--unifont", str(repo / "dl/font-licences/unifont-10.0.05-notice.txt")]
    made = run(cmd, cwd=repo)
    if made.returncode != 0:
        return [("FAIL", "mknotices.py failed: " + made.stderr.decode(errors="replace").strip()[:200])]
    work = (repo / "NOTICES.md").read_bytes()
    out: Items = []
    if made.stdout != work:
        out.append(("FAIL", "mknotices.py output differs from NOTICES.md"))
    if zip_member(asset(rel, "mac", "zip"), "NOTICES.md") != work or (rel / "NOTICES.md").read_bytes() != work:
        out.append(("FAIL", "the zip's or the staged NOTICES.md differs from the working tree's"))
    if pre_push and run(["git", "-C", str(repo), "show", "HEAD:NOTICES.md"]).stdout != work:
        out.append(("FAIL", "the working tree's NOTICES.md differs from HEAD's"))
    return out + notices_phrase_findings(work.decode(errors="replace"))


# ------------------------------------------------------------------------------------------- 9 source
def tar_entries(path: Path, hash_content: bool):
    """Yield (name, type, mode, size, mtime, linkname, sha256-or-None) for every member, in order."""
    with tarfile.open(path, "r:xz" if str(path).endswith(".xz") else "r:*") as archive:
        for member in archive:
            digest = None
            if hash_content and member.isfile():
                digest = hashlib.sha256(archive.extractfile(member).read()).hexdigest()  # type: ignore[union-attr]
            yield (member.name, member.type, member.mode, member.size, int(member.mtime), member.linkname, digest)


def is_dropped(name: str, drop: list[str], top: str) -> bool:
    bare = name.rstrip("/")
    return any(bare == f"{top}/{e}" or bare.startswith(f"{top}/{e}/") for e in drop)


def dropped_in_asset(names: list[str], drop: list[str], top: str) -> Items:
    hits = [n for n in names if is_dropped(n, drop, top)]
    return [("FAIL", f"{len(hits)} dropped member(s) are in the source asset, first {hits[0]}")] if hits else []


def note_findings(text: str, tarball_sha: str, expected_n: int) -> Items:
    out: Items = []
    if not text.startswith("Removed by libazahar-py on 2026-11-13 from Azahar's"):
        out.append(("FAIL", "the note member does not start as expected"))
    for needle in ("src/core/hw/default_keys.h", "ctr-common-1-cert.h", "ctr-common-1-key.h", "externals/libressl/",
                   f"{expected_n} members", tarball_sha):
        if needle not in text:
            out.append(("FAIL", f"the note lacks {needle}"))
    if set(re.findall(r"\b[0-9a-f]{64}\b", text)) - {tarball_sha}:
        out.append(("FAIL", "the note holds a 64-hex string other than the tarball's sha256"))
    return out


def compare_members(asset: Path, tarball: Path, drop: list[str], top: str) -> Items:
    kept = (e for e in tar_entries(tarball, True) if not is_dropped(e[0], drop, top))
    mine = tar_entries(asset, True)
    first = next(mine, None)
    out: Items = []
    if first is None or not first[0].endswith("/LIBAZAHAR-PY-REMOVED.txt"):
        out.append(("FAIL", "the note member is not first in the source asset"))
    count = 0
    for want, got in itertools.zip_longest(kept, mine):
        count += 1
        if want is None or got is None:
            out.append(("FAIL", "the source asset and the tarball minus the drop list have different member counts"))
            break
        if want != got:
            out.append(("FAIL", f"member differs from the tarball's: {want[0]}"))
            break
    return out


def source_check(rel: Path, repo: Path, pin: dict[str, str], tmp: Path) -> Items:
    asset = rel / f"azahar-unified-source-{pin['AZAHAR_TAG']}-lazpy-nokeys.tar.xz"
    tarball = repo / pin["SRC_FILE"]
    drop = pin["LAZ_CORE_DROP"].split()
    top = pin["SRC_TOP"]
    names = [e[0] for e in tar_entries(asset, False)]
    original = [e[0] for e in tar_entries(tarball, False)]
    n_libressl = sum(1 for n in original if is_dropped(n, ["externals/libressl"], top))
    out = dropped_in_asset(names, drop, top)
    out += compare_members(asset, tarball, drop, top)
    with tarfile.open(asset) as archive:
        note = archive.extractfile(names[0]).read().decode()  # type: ignore[union-attr]
    out += note_findings(note, pin["SRC_SHA256"], n_libressl)
    out += untar_findings(repo, asset, len(names), tmp)
    nokeys = read_kv(repo / "core" / "PIN-nokeys") if (repo / "core" / "PIN-nokeys").is_file() else {}
    if nokeys.get("SRC_SHA256") != sha256_file(asset) or nokeys.get("SRC_SIZE") != str(asset.stat().st_size):
        out.append(("FAIL", "core/PIN-nokeys SRC_SHA256 or SRC_SIZE differs from the source asset"))
    out += snapshot_findings(rel, repo)
    return out


def untar_findings(repo: Path, asset: Path, members: int, tmp: Path) -> Items:
    dest = tmp / "untar"
    done = run([sys.executable, "-I", str(repo / "tools" / "untar_checked.py"), str(asset), str(dest)])
    shutil.rmtree(dest, ignore_errors=True)
    found = re.search(r"members=(\d+)", done.stdout.decode(errors="replace"))
    if done.returncode != 0 or found is None or int(found.group(1)) != members:
        return [("FAIL", f"untar_checked.py rc={done.returncode} members={found.group(1) if found else '?'} (asset has {members})")]
    return []


def snapshot_findings(rel: Path, repo: Path) -> Items:
    line = re.search(r"^SNAP_SHA=([0-9a-f]{64})", (repo / "tools" / "mkrelease.sh").read_text(), re.M)
    snap = repo / "dl/sysarch-src/citra_system_archives-f470e0c.tar.gz"
    got = sha256_file(rel / "citra_system_archives-f470e0c.tar.gz")
    if line is None or got != line.group(1) or got != sha256_file(snap):
        return [("FAIL", "the snapshot asset differs from SNAP or from mkrelease.sh's SNAP_SHA")]
    return []


# ------------------------------------------------------------------------------------------- 10 build-files
def build_files_check(rel: Path, repo: Path) -> Items:
    built = asset(rel, "mac", "build")
    fresh = run(["git", "-C", str(repo), "archive", "--format=tar.gz", "--prefix=libazahar-py-core-build/", "HEAD", "core",
                 "tools/build-core.sh", "tools/untar_checked.py"]).stdout
    out: Items = []
    if fresh != built.read_bytes():
        out.append(("FAIL", "the build-files asset differs from a fresh git archive of HEAD"))
    dirty = git(repo, "status", "--porcelain", "--", "core", "tools/build-core.sh", "tools/untar_checked.py").splitlines()
    if dirty:
        out.append(("PEND", "not committed yet: " + ", ".join(line[3:] for line in dirty)))
    return out


# ------------------------------------------------------------------------------------------- 11 pins
def pins_findings(fetch_text: str, zip_name: str, zip_sha: str, app_sha: str, tag: str, skip_pins: bool) -> Items:
    out: Items = []
    if "azahar-emu" in fetch_text:
        out.append(("FAIL", "fetch.sh names azahar-emu (the stock core is not fetched)"))
    values = dict(re.findall(r"^([A-Z_]+)=(\S+)$", fetch_text, re.M))
    if values.get("REL_TAG") != tag:
        out.append(("FAIL", f"fetch.sh REL_TAG is {values.get('REL_TAG')}, expected {tag}"))
    if "https://github.com/GuyShtainer/libazahar-py/releases/download/" not in fetch_text:
        out.append(("FAIL", "fetch.sh does not use the GuyShtainer release URL"))
    if values.get("LAZPY_CORE_ZIP") != zip_name:
        out.append(("FAIL", "fetch.sh names another core zip"))
    if skip_pins:
        return out + [("SKIP", "pins: --skip-pins (the main loop fills them at I2)")]
    if values.get("LAZPY_CORE_SHA") != zip_sha or values.get("TESTAPP_SHA") != app_sha:
        out.append(("FAIL", "fetch.sh pins differ from the staged zip or test app"))
    return out


# ------------------------------------------------------------------------------------------- 12 repo
def forbidden_path(path: str) -> bool:
    parts = path.split("/")
    name = parts[-1]
    return (path.endswith(FORBIDDEN_SUFFIX) or name in FORBIDDEN_NAMES or any(p in FORBIDDEN_DIRS for p in parts[:-1])
            or parts[0].startswith("build") and len(parts) > 1)


def repo_paths_findings(repo: Path) -> Items:
    tracked = git(repo, "ls-files").splitlines()
    added = {p for p in git(repo, "log", "--all", "--diff-filter=A", "--name-only", "--format=").splitlines() if p}
    out: Items = []
    bad = [p for p in tracked if forbidden_path(p)]
    old = sorted(p for p in added if forbidden_path(p))
    if bad:
        out.append(("FAIL", f"{len(bad)} tracked path(s) on the never-commit list, first {bad[0]}"))
    if old:
        out.append(("FAIL", f"{len(old)} path(s) on the never-commit list were added in history, first {old[0]}"))
    if ".github/FUNDING.yml" in tracked or ".github/FUNDING.yml" in added:
        out.append(("FAIL", ".github/FUNDING.yml is tracked or was added"))
    return out


def repo_content_findings(repo: Path) -> Items:
    out: Items = []
    code = [p for p in git(repo, "ls-files", "host", "python", "testapp", "examples", "tools/fetch.sh").splitlines()]
    for path in code:
        text = (repo / path).read_text(errors="replace") if (repo / path).is_file() else ""
        for word in KEY_WORDS:
            if word in text:
                out.append(("FAIL", f"{path} holds '{word}'"))
    for path in git(repo, "ls-files", "*.md").splitlines():
        if (repo / path).is_file() and LONG_HEX_RUN.search((repo / path).read_text(errors="replace")):
            out.append(("FAIL", f"{path} holds a run of 8 or more 0xNN tokens"))
    return out


def repo_identity_findings(repo: Path) -> Items:
    emails = set(git(repo, "log", "--all", "--format=%ae%n%ce").split())
    refs = [r for r in git(repo, "for-each-ref", "--format=%(refname)").split() if not r.startswith(("refs/heads/", "refs/tags/"))]
    out: Items = []
    if emails != {NOREPLY}:
        out.append(("FAIL", f"commit identities are {len(emails)} address(es), not only the no-reply address"))
    if refs or git(repo, "for-each-ref", "refs/replace"):
        out.append(("FAIL", "a ref other than refs/heads or refs/tags (or refs/replace) exists"))
    return out


def iter_blobs(repo: Path):
    """Yield (first path, blob bytes) for every distinct blob reachable from any ref, through one cat-file process."""
    listing = git(repo, "rev-list", "--all", "--objects").splitlines()
    first_path: dict[str, str] = {}
    for line in listing:
        sha, _sep, path = line.partition(" ")
        first_path.setdefault(sha, path)
    kinds = run(["git", "-C", str(repo), "cat-file", "--batch-check"], data=("\n".join(first_path) + "\n").encode()).stdout.decode().splitlines()
    wanted = [line.split()[0] for line in kinds if line.split()[1] == "blob"]
    proc = subprocess.Popen(["git", "-C", str(repo), "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    assert proc.stdin is not None and proc.stdout is not None
    for sha in wanted:
        proc.stdin.write(sha.encode() + b"\n")
        proc.stdin.flush()
        header = proc.stdout.readline().split()
        data = proc.stdout.read(int(header[2]))
        proc.stdout.read(1)
        yield first_path[sha], data
    proc.stdin.close()
    proc.wait()


def message_texts(repo: Path) -> list[str]:
    commits = git(repo, "log", "--all", "--format=%B%x00").split("\x00")
    tags = git(repo, "for-each-ref", "refs/tags", "--format=%(contents)%00").split("\x00")
    return commits + tags


def needle_history_findings(repo: Path, needles: list[tuple[int, re.Pattern[str]]]) -> Items:
    if not needles:
        return [("SKIP", "history needles: LAZ_PRIVATE_NEEDLES is not set")]
    blobs = hits = 0
    for _path, data in iter_blobs(repo):
        blobs += 1
        text = data.decode("utf-8", errors="replace")
        hits += any(regex.search(text) for _n, regex in needles)
    hits += sum(any(regex.search(t) for _n, regex in needles) for t in message_texts(repo))
    return [("FAIL", f"history needles: {hits} blob/message hit(s) in {blobs} blobs")] if hits else []


# ------------------------------------------------------------------------------------------- 13 history-bytes
def make_windows(repo: Path) -> tuple[set[bytes], Items]:
    sys.path.insert(0, str(repo / "tests"))
    import gate_f2
    windows: set[bytes] = set()
    out: Items = []
    for rel, array in gate_f2.KEY_ARRAYS:
        data = gate_f2._header_bytes(repo / SRC_REL, rel, array)
        if len(data) < 128:
            out.append(("FAIL", f"history-bytes: {rel} in the reading copy parses to {len(data)} bytes: nothing was checked"))
            continue
        windows.update(data[i:i + 6] for i in range(len(data) - 5) if len(set(data[i:i + 6])) >= 4)
    return windows, out


def history_bytes_check(repo: Path, pre_push: bool) -> Items:
    """Check 13. Without the reading copy there are no windows to search for: SKIP (PEND under --pre-push), never a PASS."""
    if not (repo / SRC_REL).is_dir():  # only whether the path exists is looked at here
        kind = "PEND" if pre_push else "SKIP"
        return [(kind, "the reading copy of Azahar's key headers is not on this machine; v1.0.0's history was checked at "
                       "v1.0.0 and the CI leak check covers the artifacts")]
    windows, bad = make_windows(repo)
    return bad + ([] if bad else history_bytes_findings(repo, windows))


TOKEN_RUN = re.compile(r"(?:(?:0x[0-9a-fA-F]{1,2}|\b[0-9a-fA-F]{2}\b)[\s,]+){5,}(?:0x[0-9a-fA-F]{1,2}|\b[0-9a-fA-F]{2}\b)")
HEX_STRING = re.compile(r"\b[0-9a-fA-F]{12,}\b")


def hex_candidates(text: str):
    """Yield byte strings from runs of hex byte tokens and from long hex strings (both nibble alignments)."""
    for found in TOKEN_RUN.finditer(text):
        yield bytes(int(a or b, 16) for a, b in re.findall(r"0x([0-9a-fA-F]{1,2})|\b([0-9a-fA-F]{2})\b", found.group(0)))
    for found in HEX_STRING.finditer(text):
        for start in (0, 1):
            chunk = found.group(0)[start:]
            yield bytes.fromhex(chunk[:len(chunk) - len(chunk) % 2])


def has_window(text: str, windows: set[bytes]) -> bool:
    for data in hex_candidates(text):
        if any(data[i:i + 6] in windows for i in range(len(data) - 5)):
            return True
    return False


def history_bytes_findings(repo: Path, windows: set[bytes]) -> Items:
    blobs = 0
    hits: list[str] = []
    for path, data in iter_blobs(repo):
        blobs += 1
        if b"\x00" in data[:8000]:
            continue
        if has_window(data.decode("utf-8", errors="replace"), windows):
            hits.append(path)
    hits += ["(a commit or tag message)" for text in message_texts(repo) if has_window(text, windows)]
    out: Items = [("NOTE", f"history-bytes: {blobs} blobs, {len(hits)} hits")]
    out += [("FAIL", f"history-bytes: hit in {where}") for where in hits]
    return out


# ------------------------------------------------------------------------------------------- 14 versions, 15 pre-push, 16 macos
def versions_findings(pyproject: str, init_text: str, tag: str) -> Items:
    version = tag.lstrip("v")
    a = re.search(r'^version\s*=\s*"([^"]*)"', pyproject, re.M)
    b = re.search(r'^__version__\s*=\s*"([^"]*)"', init_text, re.M)
    out: Items = []
    if not a or a.group(1) != version:
        out.append(("FAIL", f"pyproject version is {a.group(1) if a else '?'}, expected {version}"))
    if not b or b.group(1) != version:
        out.append(("FAIL", f"__version__ is {b.group(1) if b else '?'}, expected {version}"))
    return out


def pre_push_findings(repo: Path, notes_text: str) -> Items:
    out: Items = []
    if git(repo, "status", "--porcelain").strip():
        out.append(("FAIL", "git status is not clean"))
    if git(repo, "config", "user.email").strip() != NOREPLY or git(repo, "config", "user.name").strip() != "Guy Shtainer":
        out.append(("FAIL", "git user.name/user.email is not Guy Shtainer / the no-reply address"))
    for line in git(repo, "for-each-ref", "refs/tags", "--format=%(taggeremail)").splitlines():
        if line.strip() and line.strip("<> ") != NOREPLY:
            out.append(("FAIL", "a tagger email is not the no-reply address"))
    docs = repo / "tools" / "docs_check.py"
    if not docs.is_file() or run([sys.executable, "-I", str(docs)], cwd=repo).returncode != 0:
        out.append(("FAIL", "tools/docs_check.py is missing or fails"))
    out += notes_wording_findings(notes_text)
    return out


def notes_wording_findings(text: str) -> Items:
    out: Items = [("FAIL", f"release notes hold '{w}'") for w in ("bundles", "includes ©", "ripped") if w in text]
    if re.search(r"\b\d+(\.\d+)?\s?x\b|\bfps\b", text):
        out.append(("FAIL", "release notes hold a speed token"))
    for found in re.finditer(r"\bkeys?\b", text):
        window = text[max(0, found.start() - 3):found.end() + 5]
        before = text[max(0, found.start() - 11):found.start()]
        if not (before.endswith("no ") or before.endswith("no console ") or "key data" in window):
            out.append(("FAIL", "release notes hold 'key' outside 'no keys', 'no console keys' or 'key data'"))
            break
    return out


def vtool_info(text: str) -> tuple[str, str]:
    platform = re.search(r"platform (\S+)", text)
    minos = re.search(r"minos (\S+)", text)
    return (platform.group(1) if platform else "?", minos.group(1) if minos else "?")


def macos_binary_findings(label: str, vtool: str, archs: str, host: bool) -> Items:
    platform, minos = vtool_info(vtool)
    out: Items = []
    if platform != "MACOS" or archs.split() != ["arm64"]:
        out.append(("FAIL", f"{label}: platform {platform}, archs {archs.strip()}"))
    try:
        too_new = tuple(int(x) for x in minos.split(".")) > (15, 0)
    except ValueError:
        too_new = True
    if too_new or (host and minos != "15.0"):
        out.append(("FAIL", f"{label}: minos {minos}"))
    out.append(("NOTE", f"{label}: minos {minos}"))
    return out


def wording_findings(texts: dict[str, str]) -> Items:
    return [("FAIL", f"{name} lacks 'macOS 15 or later'") for name in ("release notes", "SOURCE.md")
            if "macOS 15 or later" not in texts.get(name, "")]


def macos_check(core: Path, repo: Path, texts: dict[str, str], pre_push: bool) -> Items:
    out = macos_binary_findings("core", run_text(["vtool", "-show-build", str(core)]), run_text(["lipo", "-archs", str(core)]), False)
    for name in ("libazhost.dylib", "azhost"):
        path = repo / "build" / name
        out += macos_binary_findings(name, run_text(["vtool", "-show-build", str(path)]), run_text(["lipo", "-archs", str(path)]), True)
    out += wording_findings(texts)
    readme = repo / "README.md"
    if not readme.is_file() or "macOS 15 or later" not in readme.read_text(errors="replace"):
        out.append(("FAIL" if pre_push else "NOTE", "README.md lacks 'macOS 15 or later'"))
    return out


# ------------------------------------------------------------------------------------------- v1.1.0 (--inherit)
# A release staged by `mkrelease.sh --inherit v1.0.0`: the macOS side is v1.0.0's bytes (checked against the pinned
# digest of v1.0.0's SHA256SUMS), the Windows side is checked from gate_f2.txt (shared contract 1) and the staged files.
INHERIT_TAG = "v1.0.0"
V1_0_0_SHA256SUMS = "288c2a257948498bb5c0f4e56a582ee311fd6654aa523b51fc85876e5ce19bec"
INHERIT_BASE = "https://github.com/GuyShtainer/libazahar-py/releases/download/{tag}"
ZIP_NAMES_WIN = ["COPYING-azahar.txt", "LICENSE", "NOTICES.md", "SOURCE.md", "azahar_lazpy_libretro.dll", "build.inputs"]
RT_ASSET = "mingw-w64-runtime-source.tar"
BUILD_FILES_REQUIRED = {"core", "tools/build-core-win64.sh", "tools/toolchain-win64.cmake", "tools/untar_checked.py",
                        ".github/workflows/core-win64.yml", "tools/build-files.txt"}
GATE_F2_LINES = [r"gate_f2 1 target=win64", r"head=[0-9a-f]{40}", r"image=ubuntu:26\.04@sha256:[0-9a-f]{64}",
                 r"core=azahar_lazpy_libretro\.dll", r"core_sha256=[0-9a-f]{64}", r"PASS droplist cmake",
                 r"PASS deps files=(\d+)", r"PASS fresh", r"PASS window arrays=(\d+) windows=(\d+) hits=0",
                 r"PASS pe machine=x86-64", r"PASS imports n=(\d+)", r"END"]
WIN_PIECES = ("Windows 11 and AMD and Intel GPUs are untested.",
              "CI adds Windows Server 2025 for the build, the fast tests and the core load test.",
              "No Windows speed figures.", "Windows 10 Pro 22H2", "RTX 3060", "Python 3.10.11",
              "A GPU driver with Vulkan is required")
WIN_REJECT = ("work in progress, not proven", "no CI and no download", "nothing in this release runs on Windows")
PLACEHOLDERS = ("<pick after W9>", "<from W7>", "<OPENSSLDIR from build.inputs>", "TO BE FILLED")
WIN_NOTICE_PHRASES = ("The OpenSSL Project Authors", "SIL OPEN FONT LICENSE Version 1.1", "GNU Unifont 10.0.05", "mingw-w64",
                      "winpthreads")
# the verbatim licence files of the linked runtime (ip-legal): one marker from each of winpthreads' COPYING and
# COPYING.MinGW-w64-runtime.txt, plus a floor on the length. W2b1's mknotices writes both texts whole.
WIN_LICENCE_MARKERS = ("Lockless Inc", "MinGW-w64 runtime licensing", "Redistributions in binary form must reproduce")
WIN_NOTICES_MIN_CHARS = 20000
WIN_NOTICE_REJECT = ("MoltenVK",)
WIN_NOTICE_FETCH_RE = re.compile(r"fetch\.sh[^\n]{0,80}Vulkan|Vulkan[^\n]{0,80}fetch\.sh", re.I)


def inherited_names(pin: dict[str, str]) -> list[str]:
    """The seven assets re-uploaded byte for byte from v1.0.0."""
    return [f"azahar_lazpy_libretro-{pin['AZAHAR_TAG']}-lazpy.{pin['LAZPY_REV']}-macos-arm64.zip", "NOTICES.md",
            f"azahar-unified-source-{pin['AZAHAR_TAG']}-lazpy-nokeys.tar.xz", f"openssl-{pin['OPENSSL_VERSION']}.tar.gz",
            "citra_system_archives-f470e0c.tar.gz", "testapp.3dsx", f"libazahar-py-core-build-{INHERIT_TAG}.tar.gz"]


def expected_assets_v11(pin: dict[str, str], tag: str, runtime: bool) -> list[str]:
    names = inherited_names(pin) + [f"azahar_lazpy_libretro-{pin['AZAHAR_TAG']}-lazpy.{pin['LAZPY_REV']}-windows-x64.zip",
                                    "NOTICES-windows-x64.md", f"libazahar-py-core-build-{tag}.tar.gz", "SOURCE.md", "SHA256SUMS"]
    return sorted(names + ([RT_ASSET] if runtime else []))


def load_inherit_sums(args: argparse.Namespace) -> bytes:
    """v1.0.0's SHA256SUMS: --inherit-sums FILE, else the v1.0.0 page (LAZ_INHERIT_BASE replaces its URL)."""
    if args.inherit_sums:
        return Path(args.inherit_sums).read_bytes()
    base = os.environ.get("LAZ_INHERIT_BASE") or INHERIT_BASE.format(tag=args.inherit)
    with urllib.request.urlopen(f"{base}/SHA256SUMS", timeout=60) as handle:  # noqa: S310 (checked against the pin below)
        return handle.read()


def parse_sums(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        digest, _sep, name = line.partition("  ")
        if re.fullmatch(r"[0-9a-f]{64}", digest) and name:
            out[name] = digest
    return out


def inherit_findings(sums: bytes, rel: Path, pin: dict[str, str], repo: Path) -> Items:
    """The seven inherited assets are v1.0.0's bytes: SHA256SUMS against the pin, each asset against its line, five of
    them against the pins this repo already holds."""
    if sha256_bytes(sums) != V1_0_0_SHA256SUMS:
        return [("FAIL", "v1.0.0's SHA256SUMS does not match the pinned digest V1_0_0_SHA256SUMS")]
    lines = parse_sums(sums.decode(errors="replace"))
    out: Items = []
    for name in inherited_names(pin):
        if name not in lines:
            out.append(("FAIL", f"v1.0.0's SHA256SUMS has no line for {name}"))
        elif not (rel / name).is_file() or sha256_file(rel / name) != lines[name]:
            out.append(("FAIL", f"{name} differs from v1.0.0's SHA256SUMS line (not the v1.0.0 bytes)"))
    nokeys = read_kv(repo / "core" / "PIN-nokeys")
    names = inherited_names(pin)
    pins = [(names[2], nokeys.get("SRC_SHA256", ""), "core/PIN-nokeys"), (names[3], md_sha(read_text(repo / "core" / "OPENSSL.md")), "core/OPENSSL.md"),
            (names[4], mkrelease_pin(repo, "SNAP_SHA"), "mkrelease.sh SNAP_SHA"),
            (names[1], sha256_file(repo / "NOTICES.md") if (repo / "NOTICES.md").is_file() else "", "the repo's NOTICES.md")]
    fetch = read_text(repo / "tools" / "fetch.sh")
    values = dict(re.findall(r"^([A-Z_]+)=(\S+)$", fetch, re.M))
    pins += [(names[0], values.get("LAZPY_CORE_SHA", ""), "fetch.sh LAZPY_CORE_SHA"), (names[5], values.get("TESTAPP_SHA", ""), "fetch.sh TESTAPP_SHA")]
    for name, want, label in pins:
        if not (rel / name).is_file() or not want or sha256_file(rel / name) != want:
            out.append(("FAIL", f"{name} does not match {label}"))
    return out


def read_text(path: Path) -> str:
    return path.read_text(errors="replace") if path.is_file() else ""


def mkrelease_pin(repo: Path, name: str) -> str:
    found = re.search(rf"^{name}=([0-9a-f]{{64}})", read_text(repo / "tools" / "mkrelease.sh"), re.M)
    return found.group(1) if found else ""


def assets_findings_v11(rel: Path, names: list[str], pin: dict[str, str]) -> Items:
    names, out = asset_set(rel, names)
    if out:
        return out
    sums = parse_sums((rel / "SHA256SUMS").read_text())
    if set(sums) != set(names) - {"SHA256SUMS"}:
        out.append(("FAIL", "SHA256SUMS lists a different file set"))
    for name, digest in sums.items():
        if not (rel / name).is_file() or sha256_file(rel / name) != digest:
            out.append(("FAIL", f"SHA256SUMS does not match {name}"))
    out += zip_findings(asset(rel, "mac", "zip"))
    with zipfile.ZipFile(asset(rel, "win", "zip")) as archive:
        members = sorted(archive.namelist())
        licence = archive.read("LICENSE").decode(errors="replace").splitlines()[:2] if "LICENSE" in members else []
    if members != ZIP_NAMES_WIN:
        out.append(("FAIL", f"Windows zip members are {members}"))
    if not licence or "GNU GENERAL PUBLIC LICENSE" not in licence[0] or "Version 3" not in licence[1]:
        out.append(("FAIL", "the Windows zip's LICENSE is not the GPLv3 text"))
    return out


def gate_f2_findings(text: str, dll_sha: str, inputs: dict[str, str]) -> Items:
    """Shared contract 1: every line once and in order, no FAIL line, END last, and the three bindings."""
    out: Items = []
    if "\r" in text or not text.endswith("\n"):
        out.append(("FAIL", "gate_f2.txt must be LF text ending in a newline"))
    lines = text.rstrip("\n").split("\n")
    for line in lines:
        if line.startswith("FAIL "):
            out.append(("FAIL", f"gate_f2.txt has a FAIL line: {line[:100]}"))
    if out:
        return out
    if len(lines) != len(GATE_F2_LINES):
        return [("FAIL", f"gate_f2.txt has {len(lines)} lines, expected {len(GATE_F2_LINES)}")]
    counts: list[tuple[str, ...]] = []
    for number, (line, pattern) in enumerate(zip(lines, GATE_F2_LINES), 1):
        found = re.fullmatch(pattern, line)
        if not found:
            out.append(("FAIL", f"gate_f2.txt line {number} is not '{pattern}' (out of order, missing or repeated)"))
        counts.append(found.groups() if found else ())
    if out:
        return out
    if lines[-1] != "END":
        out.append(("FAIL", "gate_f2.txt does not end with END"))
    if int(counts[8][0]) < 1 or int(counts[8][1]) < 1:
        out.append(("FAIL", f"gate_f2.txt window search read arrays={counts[8][0]} windows={counts[8][1]}: both must be at least 1"))
    if int(counts[6][0]) < 1000:
        out.append(("FAIL", f"gate_f2.txt read {counts[6][0]} .o.d files, at least 1000 are needed"))
    values = dict(line.split("=", 1) for line in lines if "=" in line and not line.startswith("PASS"))
    if values.get("core_sha256") != dll_sha:
        out.append(("FAIL", "gate_f2.txt core_sha256 is not the sha256 of the DLL in the Windows zip"))
    if values.get("head") != inputs.get("head"):
        out.append(("FAIL", "gate_f2.txt head differs from build.inputs head="))
    if values.get("image") != inputs.get("image"):
        out.append(("FAIL", "gate_f2.txt image differs from build.inputs image="))
    return out


def windows_openssl_findings(inputs: dict[str, str], md_text: str, inherited: Path) -> Items:
    got = inputs.get("openssl_src_sha256", "")
    out: Items = []
    if not got:
        return [("FAIL", "build.inputs has no openssl_src_sha256=")]
    if got != md_sha(md_text):
        out.append(("FAIL", "build.inputs openssl_src_sha256 differs from core/OPENSSL.md's"))
    if not inherited.is_file() or got != sha256_file(inherited):
        out.append(("FAIL", "build.inputs openssl_src_sha256 differs from the inherited openssl tarball's"))
    return out


def openssl_v11_findings(staged: Path, md_text: str, version: str, md_version: str) -> Items:
    out: Items = []
    if md_sha(md_text) != sha256_file(staged):
        out.append(("FAIL", "the staged OpenSSL asset differs from core/OPENSSL.md's sha256"))
    if not (staged.name == f"openssl-{version}.tar.gz" and f"Version: {version}" in md_text and md_version == version):
        out.append(("FAIL", "the OpenSSL pin, the tarball name and core/OPENSSL.md disagree"))
    return out


def build_member_findings(members: list[str], listed: list[str]) -> Items:
    """The build-files tar's member list against tools/build-files.txt (shared contract 2)."""
    names = {m.rstrip("/") for m in members}
    names.discard("libazahar-py-core-build")
    names = {n[len("libazahar-py-core-build/"):] if n.startswith("libazahar-py-core-build/") else n for n in names}
    out: Items = []
    if listed != sorted(listed) or len(set(listed)) != len(listed) or "" in listed:
        out.append(("FAIL", "tools/build-files.txt is not sorted, unique and free of blank lines"))
    missing = sorted(BUILD_FILES_REQUIRED - set(listed))
    if missing:
        out.append(("FAIL", f"tools/build-files.txt lacks {missing}"))
    for path in listed:
        if not any(n == path or n.startswith(path + "/") for n in names):
            out.append(("FAIL", f"the build-files asset lacks {path} (tools/build-files.txt lists it)"))
    parents = {"/".join(p.split("/")[:i]) for p in listed for i in range(1, len(p.split("/")))}
    for name in sorted(names):
        if name and not any(name == p or name.startswith(p + "/") for p in listed) and name not in parents:
            out.append(("FAIL", f"the build-files asset holds {name}, which tools/build-files.txt does not list"))
    return out


def build_files_v11_check(rel: Path, repo: Path) -> Items:
    raw = read_text(repo / "tools" / "build-files.txt")
    if not raw or "" in raw.rstrip("\n").split("\n"):
        return [("FAIL", "tools/build-files.txt is missing, empty or has a blank line")]
    listed = raw.rstrip("\n").split("\n")
    win = asset(rel, "win", "build")
    with tarfile.open(win) as archive:
        members = archive.getnames()
    out = build_member_findings(members, listed)
    fresh = run(["git", "-C", str(repo), "archive", "--format=tar.gz", "--prefix=libazahar-py-core-build/", "HEAD", *listed]).stdout
    if fresh != win.read_bytes():
        out.append(("FAIL", "the build-files asset differs from a fresh git archive of HEAD over tools/build-files.txt"))
    dirty = git(repo, "status", "--porcelain", "--", *listed).splitlines()
    if dirty:
        out.append(("PEND", "not committed yet: " + ", ".join(line[3:] for line in dirty)))
    return out


def source_md_v11_findings(text: str, names: list[str]) -> Items:
    return [("FAIL", f"SOURCE.md does not name {name}") for name in names if name != "SHA256SUMS" and name not in text]


def windows_notices_findings(text: str) -> Items:
    out: Items = [("FAIL", f"NOTICES-windows-x64.md lacks: {p}") for p in WIN_NOTICE_PHRASES if p not in text]
    out += [("FAIL", f"NOTICES-windows-x64.md lacks the verbatim licence text (marker: {m})") for m in WIN_LICENCE_MARKERS if m not in text]
    if len(text) < WIN_NOTICES_MIN_CHARS:
        out.append(("FAIL", f"NOTICES-windows-x64.md is only {len(text)} characters: the two runtime licence files are not in it whole"))
    out += [("FAIL", f"NOTICES-windows-x64.md mentions {w}: the Windows build neither ships nor fetches it") for w in WIN_NOTICE_REJECT if w in text]
    if WIN_NOTICE_FETCH_RE.search(text):
        out.append(("FAIL", "NOTICES-windows-x64.md says fetch.sh fetches Vulkan: it does not on Windows"))
    if "Nintendo's" in text:
        out.append(("FAIL", "NOTICES-windows-x64.md says \"Nintendo's\""))
    return out


def norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def windows_wording_findings(status: str, notes: str, readme: str, using: str = "", openssl_md: str = "") -> Items:
    """The Windows twin of wording_findings: STATUS and the release notes hold W6's pieces, the README holds two.
    USING.md and core/OPENSSL.md are only scanned for placeholders (they hold some until W5 and W7 fill them)."""
    out: Items = []
    texts = {"STATUS.md": norm_ws(status), "release notes": norm_ws(notes), "README.md": norm_ws(readme)}
    for name in ("STATUS.md", "release notes"):
        out += [("FAIL", f"{name} lacks '{piece}'") for piece in WIN_PIECES if piece not in texts[name]]
    for piece in ("proven on one PC", "A GPU driver with Vulkan is required"):
        if piece not in texts["README.md"]:
            out.append(("FAIL", f"README.md lacks '{piece}'"))
    for name, text in texts.items():
        out += [("FAIL", f"{name} holds '{bad}'") for bad in WIN_REJECT if bad in text]
        out += [("PEND", f"{name} still holds the placeholder {mark}") for mark in PLACEHOLDERS if mark in text]
    for name, text in (("docs/USING.md", using), ("core/OPENSSL.md", openssl_md)):
        out += [("PEND", f"{name} still holds the placeholder {mark}") for mark in PLACEHOLDERS if mark in norm_ws(text)]
    return out


def strings_py(data: bytes) -> str:
    """The printable ASCII and UTF-16LE strings of a binary (there is no strings tool on the PC)."""
    ascii_runs = re.findall(rb"[\x20-\x7e]{4,}", data)
    wide_runs = re.findall(rb"(?:[\x20-\x7e]\x00){4,}", data)
    return "\n".join(r.decode("ascii") for r in ascii_runs) + "\n" + "\n".join(r.decode("utf-16le") for r in wide_runs)


def private_texts_v11(rel: Path, repo: Path, pin: dict[str, str]) -> dict[str, str]:
    texts: dict[str, str] = {}
    for platform, dll in (("mac", "azahar_lazpy_libretro.dylib"), ("win", "azahar_lazpy_libretro.dll")):
        with zipfile.ZipFile(asset(rel, platform, "zip")) as archive:
            for name in archive.namelist():
                data = archive.read(name)
                texts[f"zip-{platform}:{name}" if name != dll else f"{platform} core strings"] = (
                    strings_py(data) if name == dll else data.decode(errors="replace"))
    for platform in ("mac", "win"):
        with tarfile.open(asset(rel, platform, "build")) as build:
            for member in build.getmembers():
                if member.isfile():
                    texts[f"build-files-{platform}:{member.name}"] = build.extractfile(member).read().decode(errors="replace")  # type: ignore[union-attr]
    texts["testapp strings"] = strings_py((rel / "testapp.3dsx").read_bytes())
    for name in ("NOTICES.md", "NOTICES-windows-x64.md", "SOURCE.md"):
        texts[name] = (rel / name).read_text(errors="replace")
    for name in ("release notes",):
        notes = repo / "docs" / "release-notes" / f"{rel.name}.md"
        if notes.is_file():
            texts[name] = notes.read_text(errors="replace")
    return texts


def pins_v11_findings(fetch_text: str, win_zip: str, win_sha: str, inherit: str, skip_pins: bool) -> Items:
    values = dict(re.findall(r"^([A-Z_]+)=(\S+)$", fetch_text, re.M))
    out: Items = []
    if values.get("REL_TAG_PREV") != inherit:
        out.append(("FAIL", f"fetch.sh REL_TAG_PREV is {values.get('REL_TAG_PREV')}, expected {inherit}"))
    if values.get("LAZPY_CORE_ZIP_WIN") != win_zip:
        out.append(("FAIL", "fetch.sh LAZPY_CORE_ZIP_WIN names another zip"))
    if skip_pins:
        return out + [("SKIP", "Windows pin: --skip-pins")]
    if values.get("LAZPY_CORE_SHA_WIN", "TBD").startswith("TBD"):
        out.append(("PEND", "fetch.sh LAZPY_CORE_SHA_WIN is TBD (the main loop sets it in W7)"))
    elif values.get("LAZPY_CORE_SHA_WIN") != win_sha:
        out.append(("FAIL", "fetch.sh LAZPY_CORE_SHA_WIN differs from the staged Windows zip"))
    return out


def run_checks_v11(ctx: "Ctx", tmp: Path) -> list[tuple[str, Items]]:
    """Every check of a v1.1.0 release, each guarded so a missing or doubled asset is a FAIL of that check."""
    args, repo, rel, pin = ctx.args, ctx.repo, ctx.rel, ctx.pin
    runtime = not args.no_runtime_source
    results: list[tuple[str, Items]] = []

    def guard(name: str, fn) -> None:  # type: ignore[no-untyped-def]
        try:
            results.append((name, fn()))
        except AssetError as error:
            results.append((name, [("FAIL", str(error))]))

    win_zip = asset(rel, "win", "zip")
    with zipfile.ZipFile(win_zip) as archive:
        win_inputs_text = archive.read("build.inputs").decode(errors="replace")
        win_dll = archive.read("azahar_lazpy_libretro.dll")
    inputs_path = tmp / "win-build.inputs"
    inputs_path.write_text(win_inputs_text)
    inputs = read_kv(inputs_path)
    texts = private_texts_v11(rel, repo, pin)
    needles = load_needles(os.environ.get("LAZ_PRIVATE_NEEDLES"))
    mac_notices = texts["NOTICES.md"]
    allowed = frozenset(a for a in EMAIL_RE.findall(mac_notices) if a.lower().endswith("@gmail.com"))
    names = sorted(expected_assets_v11(pin, rel.name, runtime) + host_names_present(rel))

    guard("1 assets", lambda: assets_findings_v11(rel, names, pin))
    try:
        sums = load_inherit_sums(args)
        guard("1b inherit", lambda: inherit_findings(sums, rel, pin, repo))
    except OSError as error:
        results.append(("1b inherit", [("SKIP", f"v1.0.0's SHA256SUMS could not be read: {error}")]))
    if args.gate_f2:
        guard("2 gate_f2", lambda: gate_f2_findings(Path(args.gate_f2).read_text(), sha256_bytes(win_dll), inputs))
    else:
        results.append(("2 gate_f2", [("SKIP", "--gate-f2 FILE not given: the Windows keyblob check did not run")]))
    results.append(("1c host zips", host_findings(rel, rel.name, ctx.fetch_text, args.skip_pins, repo)))
    results.append(("2 keyblob (macOS)", [("NOTE", "inherited from v1.0.0: the macOS core is the v1.0.0 bytes (see 1b)")]))
    dll_strings = texts["win core strings"]
    results.append(("3-5 binary", ([("NOTE", "macOS exports, version and linkage: inherited from v1.0.0 (see 1b)")]
                                   + version_findings(dll_strings))))
    guard("6 openssl", lambda: openssl_v11_findings(rel / f"openssl-{pin['OPENSSL_VERSION']}.tar.gz", ctx.openssl_md,
                                                    pin["OPENSSL_VERSION"], pin["OPENSSL_VERSION"])
          + windows_openssl_findings(inputs, ctx.openssl_md, rel / f"openssl-{pin['OPENSSL_VERSION']}.tar.gz"))
    results.append(("7 private", private_findings(texts, needles, True, allowed)))
    win_notices = (rel / "NOTICES-windows-x64.md").read_bytes()
    guard("8 notices", lambda: ([] if zip_member(asset(rel, "win", "zip"), "NOTICES.md") == win_notices
                                else [("FAIL", "the Windows zip's NOTICES.md differs from NOTICES-windows-x64.md")])
          + windows_notices_findings(win_notices.decode(errors="replace"))
          + ([] if sha256_file(rel / "NOTICES.md") == sha256_file(repo / "NOTICES.md")
             else [("FAIL", "NOTICES.md is not the repo's (the v1.0.0 bytes)")]))
    results.append(("9 source", source_md_v11_findings(texts["SOURCE.md"], names)))
    guard("10 build-files", lambda: build_files_v11_check(rel, repo))
    fetch = ctx.fetch_text
    zip_name = asset(rel, "mac", "zip").name
    results.append(("11 pins", pins_findings(fetch, zip_name, sha256_file(asset(rel, "mac", "zip")), sha256_file(rel / "testapp.3dsx"),
                                             rel.name, args.skip_pins)
                    + pins_v11_findings(fetch, win_zip.name, sha256_file(win_zip), args.inherit, args.skip_pins)))
    results.append(("12 repo", repo_paths_findings(repo) + repo_content_findings(repo) + repo_identity_findings(repo)
                    + needle_history_findings(repo, needles)))
    results.append(("13 history-bytes", history_bytes_check(repo, args.pre_push)))
    pyproject = Path(args.pyproject) if args.pyproject else repo / "pyproject.toml"
    results.append(("14 versions", versions_findings(pyproject.read_text(), (repo / "python/libazahar/__init__.py").read_text(), rel.name)))
    if args.pre_push:
        results.append(("15 pre-push", pre_push_findings(repo, texts.get("release notes", ""))))
    readme = read_text(repo / "README.md")
    results.append(("16 macos", [("NOTE", "binary parts (minos, arch of the dylibs): inherited from v1.0.0 (see 1b)")] + wording_findings(texts)
                    + ([] if "macOS 15 or later" in readme else [("FAIL" if args.pre_push else "NOTE", "README.md lacks 'macOS 15 or later'")])))
    results.append(("16 windows", windows_wording_findings(read_text(repo / "STATUS.md"), texts.get("release notes", ""), readme,
                                                                read_text(repo / "docs" / "USING.md"), ctx.openssl_md)))
    return results


def link_or_copy(src: Path, dst: Path) -> None:
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def plant_cases_v11(ctx: "Ctx", tmp: Path) -> list[tuple[str, bool]]:
    """One plant per new v1.1.0 check; each must fail on its own reason."""
    rel, repo, pin = ctx.rel, ctx.repo, ctx.pin
    results: list[tuple[str, bool]] = []
    names = expected_assets_v11(pin, rel.name, not ctx.args.no_runtime_source)
    shadow = tmp / "shadow"
    shadow.mkdir()
    for path in rel.iterdir():
        link_or_copy(path, shadow / path.name)
    (shadow / "STRAY.bin").write_bytes(b"x")
    results.append(planted("1 assets (stray file)", assets_findings_v11(shadow, names, pin), "asset set differs"))
    third = tmp / "third"
    third.mkdir()
    for path in rel.iterdir():
        link_or_copy(path, third / path.name)
    link_or_copy(asset(rel, "win", "zip"), third / "azahar_lazpy_libretro-extra-windows-x64.zip")
    try:
        asset(third, "win", "zip")
        third_items: Items = []
    except AssetError as error:
        third_items = [("FAIL", str(error))]
    results.append(planted("1 assets (a third zip)", third_items, "exactly one"))
    plant_doubled_asset(ctx, tmp, results)
    sums = tmp / "sums"
    sums.write_bytes(b"0" * 64 + b"  NOTICES.md\n")
    results.append(planted("1b inherit (bad SHA256SUMS digest)", inherit_findings(sums.read_bytes(), rel, pin, repo), "pinned digest"))
    listed = [line for line in read_text(repo / "tools" / "build-files.txt").split("\n") if line]
    with tarfile.open(asset(rel, "win", "build")) as archive:
        members = [m for m in archive.getnames() if not m.endswith(".github/workflows/core-win64.yml")]
    results.append(planted("10 build-files (no workflow)", build_member_findings(members, listed),
                           "lacks .github/workflows/core-win64.yml"))
    with tarfile.open(asset(rel, "win", "build")) as archive:
        extra = archive.getnames() + ["libazahar-py-core-build/tools/stray.sh"]
    results.append(planted("10 build-files (unlisted member)", build_member_findings(extra, listed), "does not list"))
    good_head, good_image = "a" * 40, "ubuntu:26.04@sha256:" + "b" * 64
    dll_sha = "c" * 64
    body = ["gate_f2 1 target=win64", f"head={good_head}", f"image={good_image}", "core=azahar_lazpy_libretro.dll",
            f"core_sha256={dll_sha}", "PASS droplist cmake", "PASS deps files=1200", "PASS fresh",
            "PASS window arrays=3 windows=500 hits=0", "PASS pe machine=x86-64", "PASS imports n=10", "END"]
    gi = {"head": good_head, "image": good_image}
    assert not gate_f2_findings("\n".join(body) + "\n", dll_sha, gi), "the planted gate_f2 baseline must pass"
    failed = [("FAIL window arrays=3 windows=500 hits=2" if line.startswith("PASS window") else line) for line in body]
    results.append(planted("2 gate_f2 (a FAIL line)", gate_f2_findings("\n".join(failed) + "\n", dll_sha, gi), "FAIL line"))
    empty = [("PASS window arrays=0 windows=500 hits=0" if line.startswith("PASS window") else line) for line in body]
    results.append(planted("2 gate_f2 (arrays=0)", gate_f2_findings("\n".join(empty) + "\n", dll_sha, gi), "both must be at least 1"))
    empty = [("PASS window arrays=3 windows=0 hits=0" if line.startswith("PASS window") else line) for line in body]
    results.append(planted("2 gate_f2 (windows=0)", gate_f2_findings("\n".join(empty) + "\n", dll_sha, gi), "both must be at least 1"))
    results.append(planted("2 gate_f2 (core sha differs)", gate_f2_findings("\n".join(body) + "\n", "d" * 64, gi), "core_sha256"))
    swapped = body[:5] + [body[6], body[5]] + body[7:]
    results.append(planted("2 gate_f2 (lines out of order)", gate_f2_findings("\n".join(swapped) + "\n", dll_sha, gi), "out of order"))
    results.append(planted("2 gate_f2 (head differs)", gate_f2_findings("\n".join(body) + "\n", dll_sha, {**gi, "head": "e" * 40}), "head differs"))
    good_sha = md_sha(ctx.openssl_md)
    results.append(planted("6 openssl (src sha differs)", windows_openssl_findings({"openssl_src_sha256": "0" * 64}, ctx.openssl_md,
                                                                                    rel / f"openssl-{pin['OPENSSL_VERSION']}.tar.gz"),
                           "openssl_src_sha256 differs from core/OPENSSL.md"))
    results.append(planted("6 openssl (no src sha)", windows_openssl_findings({}, ctx.openssl_md, rel / "x"), "no openssl_src_sha256"))
    assert good_sha, "core/OPENSSL.md has no source sha"
    status = "\n".join(WIN_PIECES)
    results.append(planted("16 windows (a piece missing)", windows_wording_findings(status.replace("RTX 3060", ""), status, "proven on one PC. A GPU driver with Vulkan is required"),
                           "lacks 'RTX 3060'"))
    results.append(planted("16 windows (rejected phrase)", windows_wording_findings(status, status + " work in progress, not proven",
                                                                                    "proven on one PC. A GPU driver with Vulkan is required"),
                           "holds 'work in progress, not proven'"))
    pages = ("proven on one PC. A GPU driver with Vulkan is required",)
    for where, kwargs in (("docs/USING.md", {"using": "path <from W7> here"}), ("core/OPENSSL.md", {"openssl_md": "TO BE FILLED from the first CI run"}),
                          ("docs/USING.md", {"using": "path <OPENSSLDIR from build.inputs> here"})):
        found = windows_wording_findings(status, status, pages[0], **kwargs)  # type: ignore[arg-type]
        results.append(planted(f"16 windows (placeholder in {where}: {kwargs[next(iter(kwargs))][:12]})", [("FAIL", m) for k, m in found if k == "PEND"],
                               f"{where} still holds the placeholder"))
    assert not windows_wording_findings(status, status, pages[0]), "the placeholder baseline must pass"
    results.append(planted("8 notices (Windows phrase missing)", windows_notices_findings("The OpenSSL Project Authors"), "lacks: mingw-w64"))
    good_notices = " ".join(WIN_NOTICE_PHRASES + WIN_LICENCE_MARKERS) + " " + "x" * WIN_NOTICES_MIN_CHARS
    assert not windows_notices_findings(good_notices), "the good Windows notices stand-in must pass"
    results.append(planted("8 notices (runtime licence text missing)", windows_notices_findings(good_notices.replace("Lockless Inc", "")), "verbatim licence text"))
    results.append(planted("8 notices (too short)", windows_notices_findings(" ".join(WIN_NOTICE_PHRASES + WIN_LICENCE_MARKERS)), "characters"))
    results.append(planted("8 notices (fetch.sh Vulkan)", windows_notices_findings(good_notices + " fetch.sh fetches Vulkan"), "fetches Vulkan"))
    results.append(planted("8 notices (MoltenVK)", windows_notices_findings(good_notices + " MoltenVK"), "mentions MoltenVK"))
    fetch = ctx.fetch_text
    sha_plant = re.sub(r"^LAZPY_CORE_SHA_WIN=\S+", "LAZPY_CORE_SHA_WIN=" + "0" * 64, fetch, flags=re.M)
    results.append(planted("11 pins (Windows sha)", pins_v11_findings(sha_plant, asset(rel, "win", "zip").name,
                                                                      sha256_file(asset(rel, "win", "zip")), ctx.args.inherit, False),
                           "LAZPY_CORE_SHA_WIN differs"))
    results.append(planted("7 private (/Users/)", private_findings({"SOURCE.md": "see /Users/x/y"}, [], False), "/Users/"))
    plants_private_paths(results)
    results.append(planted("7 private (needle)", private_findings({"win core strings": "xx secretword yy"},
                                                                  [(1, re.compile("secretword"))], False), "hits needle line 1"))
    plant12 = temp_git_repo(tmp, "p12", {".github/FUNDING.yml": "x\n"})
    results.append(planted("12 repo (FUNDING.yml)", repo_paths_findings(plant12), "FUNDING.yml"))
    results.append(planted("14 versions", versions_findings('version = "0.1.0.dev0"', '__version__ = "0.1.0.dev0"', rel.name), "pyproject version"))
    results.append(planted("16 macos (wording)", wording_findings({"release notes": "ok", "SOURCE.md": "no wording here"}),
                           "lacks 'macOS 15 or later'"))
    return results


# ------------------------------------------------------------------------------------------- 17 plants
def plants_private_paths(results: list[tuple[str, bool]]) -> None:
    """One plant per Windows, Linux, MSYS2, WSL and CI path form (R3-5); each must fail on its own label."""
    for number, (label, text) in enumerate(PRIVATE_PLANTS, 1):
        results.append(planted(f"7 private ({label}, {number})", private_findings({"SOURCE.md": text}, [], False), f"holds a {label}"))


def plant_doubled_asset(ctx: "Ctx", tmp: Path, results: list[tuple[str, bool]]) -> None:
    """A second macOS zip: building the Ctx must raise AssetError, which main turns into 'FAIL 1 assets' (R3-4)."""
    doubled = tmp / "doubled"
    doubled.mkdir()
    for path in ctx.rel.iterdir():
        link_or_copy(path, doubled / path.name)
    link_or_copy(ctx.zip_path, doubled / "azahar_lazpy_libretro-extra-macos-arm64.zip")
    try:
        Ctx(argparse.Namespace(**{**vars(ctx.args), "dir": str(doubled)}))
        items: Items = []
    except AssetError as error:
        items = [("FAIL", str(error))]
    results.append(planted("1 assets (a doubled macOS zip in Ctx)", items, "exactly one"))


def planted(name: str, items: Items, expect: str) -> tuple[str, bool]:
    """True when the check failed with the finding the plant should provoke (not just any FAIL)."""
    return name, any(kind == "FAIL" and expect in msg for kind, msg in items)


def temp_git_repo(tmp: Path, name: str, files: dict[str, str]) -> Path:
    repo = tmp / name
    repo.mkdir()
    for key, value in (("init", "-q"), ("config user.email", NOREPLY), ("config user.name", "Guy Shtainer")):
        run(["git", "-C", str(repo), *key.split(), value] if key != "init" else ["git", "-C", str(repo), "init", "-q"])
    for rel_path, text in files.items():
        (repo / rel_path).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel_path).write_text(text)
    run(["git", "-C", str(repo), "add", "-A"])
    run(["git", "-C", str(repo), "commit", "-q", "-m", "plant"])
    return repo


def small_tar(path: Path, names: list[str]) -> None:
    """A tiny xz tar of empty-ish files, for the member-count plant."""
    with tarfile.open(path, "w:xz") as archive:
        for name in names:
            info = tarfile.TarInfo(name)
            info.size = 3
            archive.addfile(info, io.BytesIO(b"abc"))


def plants_assets(ctx: "Ctx", tmp: Path, results: list[tuple[str, bool]]) -> None:
    shadow = tmp / "shadow"
    shadow.mkdir()
    for path in ctx.rel.iterdir():
        (shadow / path.name).symlink_to(path)
    (shadow / "STRAY.bin").write_bytes(b"x")
    results.append(planted("1 assets", assets_findings(shadow, expected_assets(ctx.pin, ctx.rel.name)), "asset set differs"))
    tarball, short = tmp / "full.tar.xz", tmp / "short.tar.xz"
    small_tar(tarball, ["t/a", "t/b", "t/c", "t/externals/libressl/x"])
    small_tar(short, ["t/LIBAZAHAR-PY-REMOVED.txt", "t/a", "t/b"])
    results.append(planted("9 source (last member dropped)", compare_members(short, tarball, ["externals/libressl"], "t"),
                           "different member counts"))
    results.append(planted("9 source (dropped member kept)", dropped_in_asset(
        ["t/LIBAZAHAR-PY-REMOVED.txt", "t/externals/libressl/LICENSE"], ctx.pin["LAZ_CORE_DROP"].split(), "t"), "dropped member"))


def plants_binary(ctx: "Ctx", tmp: Path, results: list[tuple[str, bool]], array: bytes) -> None:
    import gate_f2
    repo = ctx.repo
    core_copy = tmp / "core.dylib"
    core_copy.write_bytes((repo / "build-core" / "azahar_lazpy_libretro.dylib").read_bytes() + array[:16])  # window 0
    found = gate_f2.keyblob_findings(repo / "build-core", core_copy, repo / SRC_REL, repo / TREE_REL, repo)
    results.append(planted("2 keyblob", [("FAIL", f"keyblob: {item}") for item in found], "the core holds window"))
    results.append(planted("3 exports", exports_findings(ctx.nm_text + "0000000000000000 T _extra_symbol\n"), "other exports"))
    results.append(planted("4 version", version_findings("no version here\n"), "no 2126.2"))
    results.append(planted("5 linkage", linkage_findings(ctx.otool_text + "\t/x/libMoltenVK.dylib (compatibility version 1.0.0)\n", ""),
                           "libMoltenVK"))
    ossl_copy = tmp / "openssl-3.6.5.tar.gz"
    data = bytearray((repo / "dl/openssl-src/openssl-3.6.5.tar.gz").read_bytes())
    data[1000] ^= 1
    ossl_copy.write_bytes(bytes(data))
    results.append(planted("6 openssl", openssl_findings(ossl_copy, ctx.rel / "openssl-3.6.5.tar.gz", ctx.openssl_md, "", "3.6.5",
                                                         "3.6.5", False), "differs from core/OPENSSL.md"))


def plants_text(ctx: "Ctx", tmp: Path, results: list[tuple[str, bool]], array: bytes) -> None:
    repo, rel, fetch = ctx.repo, ctx.rel, ctx.fetch_text
    notices = (repo / "NOTICES.md").read_text(errors="replace")
    allowed = allowed_addresses(repo, notices)
    results.append(planted("7 private (/Users/)", private_findings({"SOURCE.md": "see /Users/x/y"}, [], False), "/Users/"))
    plants_private_paths(results)
    results.append(planted("7 private (foreign gmail address)", private_findings(
        {"NOTICES.md": notices + "\ncontact: nobody.x@gmail.com\n"}, [], False, allowed), "@gmail.com"))
    results.append(planted("8 notices", notices_phrase_findings(notices.replace("SIL OPEN FONT LICENSE Version 1.1", "REMOVED")),
                           "SIL OPEN FONT"))
    sha_plant = re.sub(r"^TESTAPP_SHA=\S+", "TESTAPP_SHA=" + "0" * 64, fetch, flags=re.M)
    results.append(planted("11 pins (sha)", pins_findings(sha_plant, ctx.zip_name, ctx.zip_sha, ctx.app_sha, rel.name, False), "pins differ"))
    results.append(planted("11 pins (azahar-emu)", pins_findings(fetch + "\n# https://github.com/azahar-emu/x\n", ctx.zip_name,
                                                                ctx.zip_sha, ctx.app_sha, rel.name, True), "azahar-emu"))
    plant12 = temp_git_repo(tmp, "p12", {".github/FUNDING.yml": "x\n", "a.md": "0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00\n"})
    found12 = repo_paths_findings(plant12) + repo_content_findings(plant12)
    results.append(planted("12 repo (FUNDING.yml)", found12, "FUNDING.yml"))
    results.append(planted("12 repo (long 0xNN run)", found12, "0xNN"))
    windows, _bad = make_windows(repo)
    text = " ".join(f"{b:02x}" for b in array[16:32])
    plant13 = temp_git_repo(tmp, "p13", {"note.md": f"bytes: {text}\n"})
    results.append(planted("13 history-bytes", history_bytes_findings(plant13, windows), "history-bytes: hit"))
    results.append(planted("14 versions", versions_findings('version = "0.1.0.dev0"', '__version__ = "0.1.0.dev0"', rel.name),
                           "pyproject version"))
    results.append(planted("16 macos", wording_findings({"release notes": "ok", "SOURCE.md": "no wording here"}), "lacks 'macOS 15 or later'"))


def plant_cases(ctx: "Ctx", tmp: Path) -> list[tuple[str, bool]]:
    sys.path.insert(0, str(ctx.repo / "tests"))
    import gate_f2
    array = gate_f2._header_bytes(ctx.repo / SRC_REL, *gate_f2.KEY_ARRAYS[1])
    results: list[tuple[str, bool]] = []
    plants_assets(ctx, tmp, results)
    plant_doubled_asset(ctx, tmp, results)
    plants_binary(ctx, tmp, results, array)
    plants_text(ctx, tmp, results, array)
    return results


# ------------------------------------------------------------------------------------------- driver
class Ctx:
    """Everything the checks share: the release folder, the repo, the pins and the temp folder."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.rel = Path(args.dir).resolve()
        self.repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parents[1]
        self.pin = read_kv(self.repo / "core" / "PIN")
        self.inputs_path = Path(args.inputs) if args.inputs else self.repo / "build-core" / "build.inputs"
        self.inputs = read_kv(self.inputs_path) if self.inputs_path.is_file() else {}
        self.zip_path = asset(self.rel, "mac", "zip")
        self.zip_name = self.zip_path.name
        self.zip_sha = sha256_file(self.zip_path)
        self.app_sha = sha256_file(self.rel / "testapp.3dsx")
        self.fetch_text = Path(args.fetch or self.repo / "tools" / "fetch.sh").read_text()
        self.openssl_md = (self.repo / "core" / "OPENSSL.md").read_text()
        self.nm_text = ""
        self.otool_text = ""


def prepare_binary(ctx: Ctx, tmp: Path) -> str:
    """Write the zip's dylib to the temp folder; fill ctx.nm_text/otool_text; return the strings text."""
    core = tmp / "azahar_lazpy_libretro.dylib"
    core.write_bytes(zip_member(ctx.zip_path, "azahar_lazpy_libretro.dylib"))
    args = ctx.args
    ctx.nm_text = Path(args.nm_output).read_text() if args.nm_output else run_text(["/usr/bin/nm", "-gU", str(core)])
    ctx.otool_text = Path(args.otool_output).read_text() if args.otool_output else run_text(["/usr/bin/otool", "-L", str(core)])
    return Path(args.strings_output).read_text() if args.strings_output else run_text(["/usr/bin/strings", "-a", str(core)])


def run_checks(ctx: Ctx, tmp: Path) -> list[tuple[str, Items]]:
    args, repo, rel = ctx.args, ctx.repo, ctx.rel
    core_strings = prepare_binary(ctx, tmp)
    link = Path(args.link) if args.link else repo / LINK_REL
    texts = private_texts(rel, repo, tmp, core_strings)
    needles = load_needles(os.environ.get("LAZ_PRIVATE_NEEDLES"))
    results: list[tuple[str, Items]] = [
        ("1 assets", assets_findings(rel, expected_assets(ctx.pin, rel.name))),
        ("1c host zips", host_findings(rel, rel.name, ctx.fetch_text, args.skip_pins, repo)),
        ("2 keyblob", keyblob_check(rel, repo, ctx.inputs_path)),
        ("3 exports", exports_findings(ctx.nm_text)),
        ("4 version", version_findings(core_strings)),
        ("5 linkage", linkage_findings(ctx.otool_text, core_strings)),
        ("6 openssl", openssl_findings(repo / f"dl/openssl-src/openssl-{ctx.pin['OPENSSL_VERSION']}.tar.gz",
                                       rel / f"openssl-{ctx.pin['OPENSSL_VERSION']}.tar.gz", ctx.openssl_md,
                                       sbom_sha(Path(ctx.inputs.get("openssl_prefix", "/nonexistent"))),
                                       ctx.inputs.get("openssl_version", "?"), ctx.pin["OPENSSL_VERSION"], args.pre_push)
                      + keg_findings(ctx.inputs, args.pre_push)),
        ("7 private", private_findings(texts, needles, True, allowed_addresses(repo, texts["NOTICES.md"]))),
        ("8 notices", notices_check(rel, repo, args.pre_push, link, ctx.inputs_path)),
        ("9 source", source_check(rel, repo, ctx.pin, tmp)),
        ("10 build-files", build_files_check(rel, repo)),
        ("11 pins", pins_findings(ctx.fetch_text, ctx.zip_name, ctx.zip_sha, ctx.app_sha, rel.name, args.skip_pins)),
        ("12 repo", repo_paths_findings(repo) + repo_content_findings(repo) + repo_identity_findings(repo)
         + needle_history_findings(repo, needles)),
    ]
    results.append(("13 history-bytes", history_bytes_check(repo, args.pre_push)))
    pyproject = Path(args.pyproject) if args.pyproject else repo / "pyproject.toml"
    results.append(("14 versions", versions_findings(pyproject.read_text(), (repo / "python/libazahar/__init__.py").read_text(), rel.name)))
    if args.pre_push:
        results.append(("15 pre-push", pre_push_findings(repo, texts.get("release notes", ""))))
    results.append(("16 macos", macos_check(tmp / "azahar_lazpy_libretro.dylib", repo, texts, args.pre_push)))
    return results


def report(results: list[tuple[str, Items]], pre_push: bool) -> int:
    failed = 0
    for name, items in results:
        for kind, message in items:
            if kind == "NOTE":
                print(f"NOTE {name}: {message}")
        kinds = {kind for kind, _m in items}
        bad = [m for k, m in items if k == "FAIL" or (pre_push and k in ("SKIP", "PEND"))]
        if bad:
            failed += 1
            for message in bad:
                print(f"FAIL {name}: {message}")
        elif "SKIP" in kinds:
            print(f"SKIP {name}: " + "; ".join(m for k, m in items if k == "SKIP"))
        elif "PEND" in kinds:
            print(f"PEND {name}: " + "; ".join(m for k, m in items if k == "PEND"))
        else:
            print(f"PASS {name}")
    return 1 if failed else 0


HOST_LICENCE = "GNU GENERAL PUBLIC LICENSE\n Version 3, 29 June 2007\n"
HOST_COMMIT = "0123456789abcdef0123456789abcdef01234567"  # not in any repo: the commit rule SKIPs on it
HOST_STAND = {"commit": HOST_COMMIT}  # the commit host_stage writes; host_self_test points it at a throwaway repo's commit


def host_stage(rel: Path, key: str, tag: str = "v9.9.9", extra: dict[str, bytes] | None = None, drop: tuple[str, ...] = (),
               source: str | None = None, listed: bool = True) -> str:
    """Write one stand-in host zip into rel (and its SHA256SUMS line); return its sha256."""
    name = host_zip_name(tag, key)
    members = {b: b"stand-in binary\n" for b in HOST_KINDS[key][1]}
    members["LICENSE"] = HOST_LICENCE.encode()
    members["SOURCE.md"] = (source if source is not None else f"# SOURCE\nBuilt at commit {HOST_STAND['commit']}\n").encode()
    members.update(extra or {})
    with zipfile.ZipFile(rel / name, "w") as archive:
        for member, data in members.items():
            if member not in drop:
                archive.writestr(member, data)
    digest = sha256_file(rel / name)
    if listed:
        with (rel / "SHA256SUMS").open("a") as handle:
            handle.write(f"{digest}  {name}\n")
    return digest


def _git_try(repo: Path, *argv: str) -> str | None:
    """A git command's stdout, or None when git is missing or the command fails (the self-test then skips its repo cases)."""
    try:
        done = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                               "-c", "commit.gpgsign=false", *argv], capture_output=True, check=False)
    except OSError:
        return None
    return done.stdout.decode().strip() if done.returncode == 0 else None


def _make_host_repo(root: Path) -> dict[str, str] | None:
    """A throwaway repo: commit a (host/, Makefile), b (docs only), c (host/ edited), and a side commit s from a.
    Returns the commit ids, or None if git is not usable here."""
    (root / "host").mkdir(parents=True)
    (root / "host/a.c").write_text("int a;\n")
    (root / "Makefile").write_text("all:\n")
    if _git_try(root, "init", "-q") is None:
        return None
    ids: dict[str, str] = {}
    _git_try(root, "add", "-A")
    if _git_try(root, "commit", "-q", "-m", "a") is None:
        return None
    ids["a"] = _git_try(root, "rev-parse", "HEAD") or ""
    _git_try(root, "checkout", "-q", "-b", "side")
    (root / "side.txt").write_text("s\n")
    _git_try(root, "add", "-A")
    _git_try(root, "commit", "-q", "-m", "s")
    ids["s"] = _git_try(root, "rev-parse", "HEAD") or ""
    _git_try(root, "checkout", "-q", "-")
    (root / "doc.txt").write_text("b\n")
    _git_try(root, "add", "-A")
    _git_try(root, "commit", "-q", "-m", "b")
    ids["b"] = _git_try(root, "rev-parse", "HEAD") or ""
    (root / "host/a.c").write_text("int a, c;\n")
    _git_try(root, "add", "-A")
    _git_try(root, "commit", "-q", "-m", "c")
    ids["c"] = _git_try(root, "rev-parse", "HEAD") or ""
    return ids if all(len(v) == 40 for v in ids.values()) and len(ids) == 4 else None


def host_self_test() -> tuple[int, int]:
    """Check 1c on stand-in zips in a temp folder: (cases, failed). Each case names the kinds it expects."""
    import contextlib
    tag = "v9.9.9"
    cases: list[tuple[str, dict[str, object]]] = []
    repo_dir = tempfile.TemporaryDirectory(prefix="release_check.hostrepo.")
    ids = _make_host_repo(Path(repo_dir.name) / "r")
    repo: Path | None = Path(repo_dir.name) / "r"

    def run(label: str, build, want: set[str], pin_of=None, skip_pins: bool = False,  # type: ignore[no-untyped-def]
            at: str | None = None, with_repo: bool = True) -> None:
        # at: the commit to check out in the throwaway repo before the case (HEAD is what the tag stands for)
        if ids is not None and at is not None:
            _git_try(repo, "checkout", "-q", "-f", ids[at])  # type: ignore[arg-type]
        HOST_STAND["commit"] = ids["a"] if ids is not None else HOST_COMMIT
        with tempfile.TemporaryDirectory(prefix="release_check.host.") as name:
            rel = Path(name)
            (rel / "SHA256SUMS").write_text("")
            digests = build(rel)
            win, mac = digests.get("win", "0" * 64), digests.get("mac", "0" * 64)
            pins = pin_of(win, mac) if pin_of else (win, mac)
            fetch = f"LAZPY_HOST_SHA_WIN={pins[0]}\nLAZPY_HOST_SHA_MAC={pins[1]}\n"
            items = host_findings(rel, tag, fetch, skip_pins, repo if with_repo and ids is not None else None)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = report([("1c host zips", items)], False)
        kinds = {kind for kind, _m in items}
        line = out.getvalue()
        ok = want <= kinds and not (kinds - want - {"NOTE"}) and ("PASS 1c" in line) == (not kinds - {"NOTE"}) \
            and (code == 1) == ("FAIL" in kinds)
        print(f"{'ok  ' if ok else 'FAIL'} 1c host zips, {label}: {sorted(kinds)}, exit {code}")
        cases.append((label, {"ok": ok}))

    # the default repo state: HEAD is commit a, the build commit (no tag ref exists, so HEAD stands for the tag)
    run("no host zip at all is SKIP, never PASS", lambda rel: {}, {"SKIP"}, at="a")
    run("both zips right is PASS", lambda rel: {"win": host_stage(rel, "win"), "mac": host_stage(rel, "mac")}, set())
    run("one zip right, the other absent is SKIP", lambda rel: {"win": host_stage(rel, "win")}, {"SKIP"})
    run("an extra member", lambda rel: {"win": host_stage(rel, "win", extra={"stray.txt": b"x"}), "mac": host_stage(rel, "mac")}, {"FAIL"})
    run("a binary missing", lambda rel: {"mac": host_stage(rel, "mac", drop=("azhost",)), "win": host_stage(rel, "win")}, {"FAIL"})
    run("SOURCE.md names no commit", lambda rel: {"win": host_stage(rel, "win", source="# SOURCE\nbuilt somewhere\n"),
                                                    "mac": host_stage(rel, "mac")}, {"FAIL"})
    run("not listed in SHA256SUMS", lambda rel: {"win": host_stage(rel, "win", listed=False), "mac": host_stage(rel, "mac")}, {"FAIL"})
    run("the pin differs", lambda rel: {"win": host_stage(rel, "win"), "mac": host_stage(rel, "mac")}, {"FAIL"},
        pin_of=lambda win, mac: ("1" * 64, mac))
    run("the pin is TBD", lambda rel: {"win": host_stage(rel, "win"), "mac": host_stage(rel, "mac")}, {"PEND"},
        pin_of=lambda win, mac: ("TBD", "TBD"))
    run("--skip-pins", lambda rel: {"win": host_stage(rel, "win"), "mac": host_stage(rel, "mac")}, {"SKIP"}, skip_pins=True)
    run("a private path in SOURCE.md", lambda rel: {"win": host_stage(rel, "win", source=f"commit {HOST_STAND['commit']} in /Users/someone/x\n"),
                                                     "mac": host_stage(rel, "mac")}, {"FAIL"})
    run("a runner path is only a NOTE", lambda rel: {"win": host_stage(rel, "win", source=f"commit {HOST_STAND['commit']} in D:\\a\\r\\r\n"),
                                                      "mac": host_stage(rel, "mac")}, set())

    run("a runner path inside a Windows binary is only a NOTE", lambda rel: {"win": host_stage(rel, "win",
        extra={"libazhost.dll": b"\x00D:/a/r/r/build/obj/x.o\x00more\x00"}), "mac": host_stage(rel, "mac")}, set())
    run("a /Users/runner path inside a macOS binary is a FAIL", lambda rel: {"win": host_stage(rel, "win"),
        "mac": host_stage(rel, "mac", extra={"libazhost.dylib": b"\x00/Users/runner/work/r/r/build/obj/x.o\x00more\x00"})}, {"FAIL"})
    run("the Windows zip has no NOTICES.md", lambda rel: {"win": host_stage(rel, "win", drop=("NOTICES.md",)),
                                                           "mac": host_stage(rel, "mac")}, {"FAIL"})
    run("no repo given: the commit rule SKIPs", lambda rel: {"win": host_stage(rel, "win"), "mac": host_stage(rel, "mac")}, {"SKIP"},
        with_repo=False)
    run("the build commit is not in the repo: SKIP with a reason", lambda rel: {"win": host_stage(rel, "win", source=f"commit {HOST_COMMIT}\n"),
                                                                              "mac": host_stage(rel, "mac", source=f"commit {HOST_COMMIT}\n")}, {"SKIP"})
    if ids is not None:
        run("a docs-only change after the build commit is fine", lambda rel: {"win": host_stage(rel, "win"), "mac": host_stage(rel, "mac")},
            set(), at="b")
        run("host/ changed after the build commit", lambda rel: {"win": host_stage(rel, "win"), "mac": host_stage(rel, "mac")},
            {"FAIL"}, at="c")
        run("the build commit is not an ancestor of the tag", lambda rel: {"win": host_stage(rel, "win", source=f"commit {ids['s']}\n"),
                                                                           "mac": host_stage(rel, "mac")}, {"FAIL"}, at="b")
        _git_try(repo, "tag", "v9.9.9", ids["b"])  # type: ignore[arg-type]
        run("a tag ref wins over HEAD (tag at b, HEAD at c)", lambda rel: {"win": host_stage(rel, "win"), "mac": host_stage(rel, "mac")},
            set(), at="c")

    def other_tag(rel: Path) -> dict[str, str]:
        host_stage(rel, "win", tag="v1.0.0")  # a zip of another version
        return {"mac": host_stage(rel, "mac")}
    run("a zip of another version", other_tag, {"FAIL", "SKIP"})
    # check 1 with the host zips listed by the caller too (v1.3.0's staging listed them twice and got a FAIL)
    with tempfile.TemporaryDirectory(prefix="release_check.host1.") as name:
        rel = Path(name)
        (rel / "SHA256SUMS").write_text("")
        host_stage(rel, "win"); host_stage(rel, "mac")
        listed = sorted(["SHA256SUMS"] + host_names_present(rel))
        twice = [m for _k, m in asset_set(rel, listed)[1]]
        ok = not twice
        print(f"{'ok  ' if ok else 'FAIL'} 1 assets, the host zips listed by the caller and found: {twice or 'no set finding'}")
        cases.append(("1 assets with host zips listed", {"ok": ok}))
    HOST_STAND["commit"] = HOST_COMMIT
    repo_dir.cleanup()
    bad = sum(1 for _l, r in cases if not r["ok"])
    if ids is None:
        print("note  the repo cases of check 1c did not run: git is not usable here")
    return len(cases), bad


def self_test() -> int:
    """Check 13 with the reading copy absent must report SKIP (PEND under --pre-push), with no NOTE and no PASS."""
    import contextlib
    failed = 0
    with tempfile.TemporaryDirectory(prefix="release_check.self.") as name:
        empty = Path(name)  # a repo folder without SRC_REL
        for pre_push, want in ((False, "SKIP"), (True, "PEND")):
            items = history_bytes_check(empty, pre_push)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = report([("13 history-bytes", items)], pre_push)
            lines = out.getvalue().splitlines()
            ok = (len(items) == 1 and items[0][0] == want and len(lines) == 1
                  and lines[0].startswith(("FAIL " if pre_push else want + " ") + "13 history-bytes")
                  and "NOTE" not in out.getvalue() and "PASS" not in out.getvalue() and code == (1 if pre_push else 0))
            print(f"{'ok  ' if ok else 'FAIL'} 13 history-bytes, reading copy absent{' (--pre-push)' if pre_push else ''}: "
                  f"{want} item, exit {code}")
            failed += not ok
    total, bad = host_self_test()
    failed += bad
    total += 2
    print(f"release_check self-test: {total - failed} of {total} cases passed")
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dir")
    ap.add_argument("--skip-pins", action="store_true")
    ap.add_argument("--pre-push", action="store_true")
    ap.add_argument("--plant-red", action="store_true")
    ap.add_argument("--no-runtime-source", action="store_true")
    for flag in ("nm-output", "otool-output", "strings-output", "link", "inputs", "fetch", "pyproject", "repo", "inherit", "gate-f2",
                 "inherit-sums"):
        ap.add_argument("--" + flag)
    args = ap.parse_args(argv)
    if args.inherit and args.inherit != INHERIT_TAG:
        print(f"release_check: --inherit supports {INHERIT_TAG} only", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="release_check.") as name:
        tmp = Path(name)
        if args.inherit:
            BUILD_TAG.update(mac=args.inherit, win=Path(args.dir).resolve().name)
        try:
            try:
                ctx = Ctx(args)  # the asset lookups and the testapp hash live here: a missing or doubled file is a FAIL line
            except OSError as error:
                raise AssetError(f"{error.filename or 'a release file'}: {error.strerror or error}") from error
            if args.plant_red:
                if args.inherit:
                    caught = plant_cases_v11(ctx, tmp)
                else:
                    prepare_binary(ctx, tmp)
                    caught = plant_cases(ctx, tmp)
                for check, ok in caught:
                    print(f"{'PASS' if ok else 'FAIL'} plant {check}: {'failed on its plant' if ok else 'did NOT fail on its plant'}")
                print("not planted: 10 build-files (fresh archive part) and 15 pre-push (they read this repo's git state)")
                return 0 if all(ok for _c, ok in caught) else 2  # 0 = every plant failed on its own reason
            return report(run_checks_v11(ctx, tmp) if args.inherit else run_checks(ctx, tmp), args.pre_push)
        except AssetError as error:
            print(f"FAIL 1 assets: {error}")
            return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
