#!/usr/bin/env python3
"""Machine checks for a staged release (step I).

Usage: python3 -I tools/release_check.py runs/release/v0.1.0 [--skip-pins] [--pre-push] [--plant-red]
           [--nm-output F] [--otool-output F] [--strings-output F] [--link F] [--inputs F] [--fetch F]
           [--pyproject F] [--repo DIR]

Prints one line per check: PASS, FAIL, SKIP or PEND, plus NOTE lines for the audit. Any FAIL exits 1; under
--pre-push every SKIP and PEND is a FAIL. --plant-red plants one fault per check in a temp folder outside the repo
and passes only if each check fails on its plant. Key material is never printed or written: windows of the key and
certificate arrays are made in memory from the reading copy of Azahar's source at run time (tests/gate_f2.py).
LAZ_PRIVATE_NEEDLES, when it names a file, adds private-string needles; a hit prints only a file name and a line
number, never the needle.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
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
EXPORT_EXTRA = {"_lazpy_read_memory", "_lazpy_write_memory", "_lazpy_movie_play"}
OSSL_EXPECTED = ("/opt/homebrew/etc/openssl@3", "/opt/homebrew/Cellar/openssl@3/")


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


def assets_findings(rel: Path, names: list[str]) -> Items:
    have = sorted(p.name for p in rel.iterdir())
    out: Items = []
    if have != names:
        out.append(("FAIL", f"asset set differs: extra {sorted(set(have) - set(names))}, missing {sorted(set(names) - set(have))}"))
        return out
    for line in (rel / "SHA256SUMS").read_text().splitlines():
        digest, _sep, name = line.partition("  ")
        if not (rel / name).is_file() or sha256_file(rel / name) != digest:
            out.append(("FAIL", f"SHA256SUMS does not match {name}"))
    listed = {line.partition("  ")[2] for line in (rel / "SHA256SUMS").read_text().splitlines()}
    if listed != set(names) - {"SHA256SUMS"}:
        out.append(("FAIL", "SHA256SUMS lists a different file set"))
    out += zip_findings(next(rel.glob("azahar_lazpy_libretro-*.zip")))
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


# ------------------------------------------------------------------------------------------- 2 keyblob
def zip_member(zip_path: Path, name: str) -> bytes:
    with zipfile.ZipFile(zip_path) as archive:
        return archive.read(name)


def keyblob_check(rel: Path, repo: Path, inputs: Path) -> Items:
    sys.path.insert(0, str(repo / "tests"))
    import gate_f2
    core = repo / "build-core" / "azahar_lazpy_libretro.dylib"
    zipped = zip_member(next(rel.glob("azahar_lazpy_libretro-*.zip")), "azahar_lazpy_libretro.dylib")
    out: Items = []
    if sha256_bytes(zipped) != sha256_file(core):
        out.append(("FAIL", "the zip's dylib is not the gated core (sha256 differs from build-core/)"))
    findings = gate_f2.keyblob_findings(repo / "build-core", core, repo / SRC_REL, repo / TREE_REL, repo)
    out += [("FAIL", f"keyblob: {item}") for item in findings]
    head = read_kv(inputs).get("head", "?")
    out.append(("NOTE", f"build.inputs head={head} (translate with docs/commit-map-g8.tsv then docs/commit-map-g8b.tsv)"))
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
               ("private IPv4", re.compile(r"\b(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168|169\.254)\.\d{1,3}\.\d{1,3}\b"))]
IPV4_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def load_needles(path: str | None) -> list[tuple[int, re.Pattern[str]]]:
    if not path or not Path(path).is_file():
        return []
    out = []
    for number, raw in enumerate(Path(path).read_text(errors="replace").splitlines(), 1):
        left = raw.partition("==>")[0].strip()
        if left and not left.startswith("#"):
            if left.startswith("regex:"):
                pattern = left[len("regex:"):]
            else:
                pattern = re.escape(left[len("literal:"):] if left.startswith("literal:") else left)
            out.append((number, re.compile(pattern, re.I)))
    return out


NOTICE_FILES = ("NOTICES.md", "zip:NOTICES.md")


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
    zip_path = next(rel.glob("azahar_lazpy_libretro-*.zip"))
    texts = {"core strings": core_strings}
    with zipfile.ZipFile(zip_path) as archive:
        for name in ZIP_NAMES:
            if name != "azahar_lazpy_libretro.dylib":
                texts[f"zip:{name}"] = archive.read(name).decode(errors="replace")
    with tarfile.open(next(rel.glob("libazahar-py-core-build-*.tar.gz"))) as build:
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
    if zip_member(next(rel.glob("azahar_lazpy_libretro-*.zip")), "NOTICES.md") != work or (rel / "NOTICES.md").read_bytes() != work:
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
    asset = next(rel.glob("libazahar-py-core-build-*.tar.gz"))
    fresh = run(["git", "-C", str(repo), "archive", "--format=tar.gz", "--prefix=libazahar-py-core-build/", "HEAD", "core",
                 "tools/build-core.sh", "tools/untar_checked.py"]).stdout
    out: Items = []
    if fresh != asset.read_bytes():
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
        if not (text[max(0, found.start() - 3):found.start()] == "no " or "key data" in window):
            out.append(("FAIL", "release notes hold 'key' outside 'no keys' or 'key data'"))
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


# ------------------------------------------------------------------------------------------- 17 plants
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
        self.inputs = read_kv(self.inputs_path)
        self.zip_path = next(self.rel.glob("azahar_lazpy_libretro-*.zip"))
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
    windows, bad = make_windows(repo)
    results.append(("13 history-bytes", bad + ([] if bad else history_bytes_findings(repo, windows))))
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


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dir")
    ap.add_argument("--skip-pins", action="store_true")
    ap.add_argument("--pre-push", action="store_true")
    ap.add_argument("--plant-red", action="store_true")
    for flag in ("nm-output", "otool-output", "strings-output", "link", "inputs", "fetch", "pyproject", "repo"):
        ap.add_argument("--" + flag)
    args = ap.parse_args(argv)
    ctx = Ctx(args)
    with tempfile.TemporaryDirectory(prefix="release_check.") as name:
        tmp = Path(name)
        if args.plant_red:
            prepare_binary(ctx, tmp)
            caught = plant_cases(ctx, tmp)
            for check, ok in caught:
                print(f"{'PASS' if ok else 'FAIL'} plant {check}: {'failed on its plant' if ok else 'did NOT fail on its plant'}")
            print("not planted: 10 build-files and 15 pre-push (they read this repo's git state)")
            return 1 if all(ok for _c, ok in caught) else 2  # as docs_check.py: 1 = every plant failed its check
        return report(run_checks(ctx, tmp), args.pre_push)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
