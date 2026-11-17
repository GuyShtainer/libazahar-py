"""The win64 twin of tests/gate_f2.py's keyblob check, for the Windows core DLL (docs/plans/phase-7.md, D4 and D10).

Job 1 of .github/workflows/core-win64.yml runs it on the live build tree. It writes ``gate_f2.txt`` (the contract in
docs/plans/phase-7-briefs.md, "Shared contract 1"), and exits 1 if any check failed. It prints counts and names only,
never a byte of a key header.

  gate_f2_pe.py --repo . --build-dir build-core --src-root KEYHDR/<top> [--core DLL] [--tree TREE] [--out FILE]
  gate_f2_pe.py --plant-red --dll KNOWN.dll        proves every check fails on a planted case (uses a copy of the DLL)

``--src-root`` is the folder that holds ``src/core/hw/default_keys.h`` and the two ``ctr-common-1-*.h`` headers; the
workflow extracts exactly those three files from core/PIN's tarball into a folder outside the workspace.
The PE parts are plain Python (no objdump), so they run in CI and on the PC alike.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import random
import re
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import gate_f2 as g  # noqa: E402  (importable without side effects)

CORE_NAME = "azahar_lazpy_libretro.dll"
KEY_FILES = ("default_keys.h", "ctr-common-1-cert.h", "ctr-common-1-key.h")
# the Mach-O check flags the default-ClCertA text; the upstream file-name messages are not key data
KEY_STRINGS = ("ClCertA file missing, using default", "default_keys_enc", "ctr_common_1_key_bin", "ctr_common_1_cert_bin")
ALLOW = {x.lower() for x in (
    "KERNEL32.dll", "USER32.dll", "GDI32.dll", "ADVAPI32.dll", "WS2_32.dll", "CRYPT32.dll", "bcrypt.dll", "ole32.dll",
    "OLEAUT32.dll", "SHELL32.dll", "SHLWAPI.dll", "WINMM.dll", "msvcrt.dll", "ntdll.dll", "IMM32.dll", "VERSION.dll",
    "COMDLG32.dll", "IPHLPAPI.DLL", "SECUR32.dll", "ncrypt.dll", "SETUPAPI.dll", "DBGHELP.dll")}
MACHINES = {0x8664: "x86-64", 0x14C: "x86", 0xAA64: "arm64"}
LEAK_MARKS = ("/Users/", "/home/", "/__w/")
HEAD_RE = re.compile(r"[0-9a-f]{40}")
IMAGE_RE = re.compile(r"[^@\s]+@sha256:[0-9a-f]{64}")


# ---------------------------------------------------------------- PE parsing (no external tools)
def pe_info(data: bytes) -> tuple[int, list[tuple[str, int]]]:
    """(machine, [(imported DLL name, file offset of the name)]); ValueError when it is not a PE32+ file we can read."""
    if data[:2] != b"MZ" or len(data) < 0x40:
        raise ValueError("not a PE file (no MZ header)")
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        raise ValueError("not a PE file (no PE signature)")
    machine, nsec, _t, _s, _n, optsize, _c = struct.unpack_from("<HHIIIHH", data, pe + 4)
    opt = pe + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    if magic != 0x20B:
        raise ValueError(f"optional header magic {magic:#x}, want 0x20b (PE32+)")
    sections = []
    for i in range(nsec):
        vsize, va, rawsize, rawptr = struct.unpack_from("<IIII", data, opt + optsize + i * 40 + 8)
        sections.append((va, max(vsize, rawsize), rawptr))

    def off(rva: int) -> int:
        for va, size, raw in sections:
            if va <= rva < va + size:
                return raw + rva - va
        raise ValueError(f"RVA {rva:#x} is in no section")

    imp_rva, imp_size = struct.unpack_from("<II", data, opt + 112 + 8)
    names: list[tuple[str, int]] = []
    if imp_rva and imp_size:
        pos = off(imp_rva)
        while True:
            desc = data[pos:pos + 20]
            if len(desc) < 20 or desc == bytes(20):
                break
            name_off = off(struct.unpack_from("<I", desc, 12)[0])
            end = data.index(b"\0", name_off)
            names.append((data[name_off:end].decode("ascii", "replace"), name_off))
            pos += 20
    return machine, names


def machine_findings(data: bytes) -> tuple[str, list[str]]:
    try:
        machine, _names = pe_info(data)
    except (ValueError, struct.error) as exc:
        return "?", [f"pe: {exc}"]
    if machine != 0x8664:
        return MACHINES.get(machine, hex(machine)), [f"pe: machine is {MACHINES.get(machine, hex(machine))}, want x86-64"]
    return "x86-64", []


def import_findings(data: bytes) -> tuple[int, list[str]]:
    """(distinct imported DLLs, findings): every import must be a system DLL on the allow-list, and no SSL DLL."""
    try:
        _m, names = pe_info(data)
    except (ValueError, struct.error) as exc:
        return 0, [f"imports: {exc}"]
    bad: list[str] = []
    if not names:
        bad.append("imports: the DLL has no import table")
    dlls = sorted({n for n, _ in names}, key=str.lower)
    for dll in dlls:
        low = dll.lower()
        if re.search(r"libssl|libcrypto|libtls|libressl", low):
            bad.append(f"imports: SSL DLL {dll}")
        elif low not in ALLOW and not low.startswith("api-ms-win-crt-"):
            bad.append(f"imports: {dll} is not on the system allow-list")
    return len(dlls), bad


# ---------------------------------------------------------------- the DLL's strings
def ascii_strings(data: bytes, minlen: int = 4) -> list[str]:
    return [m.decode("ascii") for m in re.findall(rb"[\x20-\x7e]{%d,}" % minlen, data)]


def strings_findings(lines: list[str], version: str, suffix: str, prefix: str) -> list[str]:
    """The Linux build's twin of gate_f2._strings_findings. OpenSSL bakes its install prefix in (OPENSSLDIR and the like);
    only that exact prefix is allowed, with whatever quoting surrounds it; any other build path is a leak."""
    bad: list[str] = []
    if not any(suffix in line for line in lines):    # PE: the compiler inlines the string, so no standalone line
        bad.append(f"strings: no line holding {suffix}")
    rest = [line.replace(prefix, "") if prefix else line for line in lines]
    for mark in LEAK_MARKS + ("/opt/lazpy",):
        if any(mark in line for line in rest):
            bad.append(f"strings: a line holds {mark} (a build path leaked)")
    for text in KEY_STRINGS:
        if any(text in line for line in lines):
            bad.append(f"strings: keyblob or certificate text {text!r} is in the core")
    if any("libressl" in line.lower() for line in lines):
        bad.append("strings: a line holds libressl")
    if not any(line.strip() == version or f"OpenSSL {version}" in line for line in lines):
        bad.append(f"strings: no line equal to {version} or holding 'OpenSSL {version}'")
    return bad


# ---------------------------------------------------------------- the checks of contract 1
def deps_scan(build_dir: Path, drop: list[str]) -> tuple[int, list[str]]:
    """(.o.d files read, findings): at least 1000 files, none naming a drop-list path or a key file or libressl."""
    names = [Path(entry).name for entry in drop] + list(KEY_FILES) + list(g.DROP_BASENAMES_EXTRA)
    count = 0
    hits: list[str] = []
    for folder, _, files in os.walk(Path(build_dir) / "build"):
        for name in files:
            if name.endswith(".o.d"):
                count += 1
                text = (Path(folder) / name).read_text(encoding="utf-8", errors="replace")
                hits += [f"{name} names {n}" for n in names if n in text]
    bad = [f"deps: {count} dependency files, want at least 1000"] if count < 1000 else []
    return count, bad + [f"deps: {h}" for h in hits[:5]]


def fresh_findings(core: Path, build_dir: Path) -> list[str]:
    cache = Path(build_dir) / "build" / "CMakeCache.txt"
    if not core.is_file() or not cache.is_file() or core.stat().st_mtime <= cache.stat().st_mtime:
        return ["fresh: the core is missing, or not newer than build/CMakeCache.txt"]
    return []


def window_findings(core_bytes: bytes, src_root: Path, version: str, suffix: str, prefix: str) -> tuple[int, int, int, list[str]]:
    """(arrays, windows, hits, findings): gate_f2's 16-byte window search over the DLL, then the DLL's strings."""
    found = g._window_findings(core_bytes, Path(src_root))
    hits = sum(1 for f in found if f.startswith("windows: the core holds window"))
    found += strings_findings(ascii_strings(core_bytes), version, suffix, prefix)
    return len(g.KEY_ARRAYS), 8 * len(g.KEY_ARRAYS), hits, found


def droplist_cmake_findings(build_dir: Path, tree: Path, repo: Path) -> list[str]:
    """Build exit, build.inputs, the drop list in the tree, the CMake cache, the link line and the configure log."""
    build_dir, tree, repo = Path(build_dir), Path(tree), Path(repo)
    bad: list[str] = []
    exit_file = build_dir / "build.exit"
    if not exit_file.is_file() or exit_file.read_text().strip() != "0":
        bad.append("build.exit: missing or not 0")
    got, found = g._inputs_findings(build_dir, repo, "win64")
    bad += found
    if not any(k.startswith("target") and "win64" in k + v for k, v in got.items()):
        bad.append("build.inputs: no target=win64 line")
    for key, rule in (("head", HEAD_RE), ("image", IMAGE_RE)):
        if not rule.fullmatch(got.get(key, "")):
            bad.append(f"build.inputs: {key} is missing or malformed")
    prefix = got.get("openssl_prefix", "")
    bad += g._cache_findings(build_dir, prefix)
    drop = g.read_kv(repo / "core" / "PIN").get("LAZ_CORE_DROP", "").split()
    if not drop:
        bad.append("PIN: LAZ_CORE_DROP is empty")
    if not (tree / "CMakeLists.txt").is_file():
        bad.append(f"tree: {tree.name} is not the build tree (no CMakeLists.txt): the drop list was not checked")
    else:
        bad += [f"tree: dropped entry {entry} is present in the build tree" for entry in drop if os.path.lexists(tree / entry)]
        for folder, _, files in os.walk(tree):
            bad += [f"tree: key file {name} is present under {Path(folder).relative_to(tree)}" for name in files if name in KEY_FILES]
    ldir = build_dir / "build" / "src" / "citra_libretro" / "CMakeFiles" / "citra_libretro.dir"   # mingw: libraries in linkLibs.rsp
    link = "".join((ldir / n).read_text(errors="replace") for n in ("link.txt", "linkLibs.rsp") if (ldir / n).is_file())
    for lib in ("libssl.a", "libcrypto.a"):
        if f"{prefix}/lib/{lib}" not in link:
            bad.append(f"link: does not name {prefix}/lib/{lib}")
    if "libressl" in link.lower():
        bad.append("link: holds libressl")
    if "-lole32" not in link:
        bad.append("link: no -lole32")
    log = build_dir / "configure.log"
    text = log.read_text(errors="replace") if log.is_file() else ""
    bad += [f"configure.log: no {s!r}" for s in ("SSE4.2 enabled", "Enabling SSE2 for xxHash") if s not in text]
    return bad


# ---------------------------------------------------------------- the report
def one_line(text: str) -> str:
    return " ".join(text.split())[:300]


def result_line(name: str, ok_detail: str, findings: list[str]) -> str:
    return f"PASS {name}" + (f" {ok_detail}" if ok_detail else "") if not findings else f"FAIL {name} {one_line('; '.join(findings))}"


def report_text(head: str, image: str, core_sha: str, results: list[str]) -> str:
    lines = ["gate_f2 1 target=win64", f"head={head}", f"image={image}", f"core={CORE_NAME}", f"core_sha256={core_sha}"]
    return "\n".join(lines + results + ["END"]) + "\n"


def contract_findings(text: str, core_sha: str, head: str, image: str) -> list[str]:
    """The reader's rules for contract 1 (release_check's --gate-f2 repeats them): every line once, in order, no FAIL."""
    lines = text.split("\n")
    bad: list[str] = []
    if lines[-1] != "":
        bad.append("no final line feed")
    lines = lines[:-1]
    if "\r" in text:
        bad.append("CR in the file")
    want = [r"gate_f2 1 target=win64", f"head={head}", f"image={re.escape(image)}", rf"core={re.escape(CORE_NAME)}",
            f"core_sha256={core_sha}", r"PASS droplist cmake", r"PASS deps files=\d+", r"PASS fresh",
            r"PASS window arrays=\d+ windows=\d+ hits=0", r"PASS pe machine=x86-64", r"PASS imports n=\d+", r"END"]
    if len(lines) != len(want):
        bad.append(f"{len(lines)} lines, want {len(want)}")
    for i, rule in enumerate(want):
        if i < len(lines) and not re.fullmatch(rule, lines[i]):
            bad.append(f"line {i + 1} is not {rule!r}")
    bad += [f"line {i + 1} is a FAIL line" for i, x in enumerate(lines) if x.startswith("FAIL ")]
    if not lines or lines[-1] != "END":
        bad.append("END is not the last line")
    return bad


def run_all(args: argparse.Namespace) -> int:
    repo, build_dir, core = Path(args.repo).resolve(), Path(args.build_dir).resolve(), Path(args.core)
    got = g.read_kv(build_dir / "build.inputs") if (build_dir / "build.inputs").is_file() else {}
    head, image = got.get("head", ""), got.get("image", "")
    live = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip()
    if not HEAD_RE.fullmatch(head) or head != live:
        print("gate_f2_pe: build.inputs head= is missing, malformed, or not this checkout's HEAD", file=sys.stderr)
        return 2
    if not IMAGE_RE.fullmatch(image):
        print("gate_f2_pe: build.inputs image= is missing or not <name>@sha256:<64 hex>", file=sys.stderr)
        return 2
    if not core.is_file():
        print(f"gate_f2_pe: no core at {core.name}", file=sys.stderr)
        return 2
    data = core.read_bytes()
    core_sha = hashlib.sha256(data).hexdigest()
    pin = g.read_kv(repo / "core" / "PIN")
    pin_used = g.built_pin(build_dir, repo)
    version, suffix = pin.get("OPENSSL_VERSION", "?"), "-lazpy." + g.read_kv(pin_used).get("LAZPY_REV", "?")
    prefix = got.get("openssl_prefix", "")
    tree = Path(args.tree) if args.tree else repo / "dl" / "azahar-src" / "build-src" / pin.get("SRC_TOP", "?")
    results: list[str] = []
    results.append(result_line("droplist cmake", "", droplist_cmake_findings(build_dir, tree, repo)))
    n_deps, found = deps_scan(build_dir, pin.get("LAZ_CORE_DROP", "").split())
    results.append(result_line("deps", f"files={n_deps}", found))
    results.append(result_line("fresh", "", fresh_findings(core, build_dir)))
    arrays, windows, hits, found = window_findings(data, Path(args.src_root), version, suffix, prefix)
    results.append(result_line("window", f"arrays={arrays} windows={windows} hits={hits}", found))
    machine, found = machine_findings(data)
    results.append(result_line("pe", f"machine={machine}", found))
    n_imp, found = import_findings(data)
    results.append(result_line("imports", f"n={n_imp}", found))
    text = report_text(head, image, core_sha, results)
    Path(args.out).write_bytes(text.encode("utf-8"))
    for line in text.splitlines():
        print(line)
    return 1 if any(x.startswith("FAIL ") for x in results) else 0


# ---------------------------------------------------------------- planted reds
def fake_headers(root: Path, rng: random.Random) -> dict[str, bytes]:
    """Three fake key headers (random bytes, never real keys) under root/src/..., returned by array name."""
    arrays: dict[str, bytes] = {}
    for rel, array in g.KEY_ARRAYS:
        data = bytes(rng.randrange(256) for _ in range(256))
        path = Path(root) / "src" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        body = ", ".join(f"0x{b:02x}" for b in data)
        path.write_text(f"static const unsigned char {array}[256] = {{ {body} }};\n")
        arrays[array] = data
    return arrays


def plant_red(dll: Path) -> int:
    """Each check must pass on the known-good DLL and fail on its planted case. Works on copies; prints names only."""
    rng = random.Random(7)
    problems: list[str] = []

    def expect(name: str, cond: bool) -> None:
        print(("ok   " if cond else "FAIL ") + name)
        if not cond:
            problems.append(name)

    data = dll.read_bytes()
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        version, suffix, prefix = "3.6.5", "-lazpy.2", "/opt/lazpy/openssl-3.6.5-mingw64"
        # window search: a fake header of random bytes, clean on the DLL, then planted into a copy
        keys = work / "hdr"
        arrays = fake_headers(keys, rng)
        _a, _w, hits, found = window_findings(data, keys, version, suffix, prefix)
        expect("window: random fake headers do not hit the DLL", hits == 0 and not any("window" in f for f in found))
        for k in (0, 3, 7):
            array, blob = "default_keys_enc", arrays["default_keys_enc"]
            off = k * (len(blob) - 16) // 7
            planted = data + blob[off:off + 16]
            _a, _w, hits, found = window_findings(planted, keys, version, suffix, prefix)
            expect(f"window: planted window {k} of {array} is found", hits >= 1 and any(f"window {k} of {array}" in f for f in found))
        empty = work / "nohdr"
        empty.mkdir()
        _a, _w, _h, found = window_findings(data, empty, version, suffix, prefix)
        expect("window: missing headers are a finding (nothing was checked)", any("nothing was checked" in f for f in found))
        lines = ["x -lazpy.2 y", "OpenSSL 3.6.5 7 Oct", "fine"]
        expect("strings: clean lines pass", not strings_findings(lines, version, suffix, prefix))
        for plant in ("ClCertA file missing, using default", "default_keys_enc", "C:/__w/x", "/home/u/x", "libressl 3", "/opt/lazpy/other"):
            expect(f"strings: planted {plant!r} flagged", bool(strings_findings(lines + [plant], version, suffix, prefix)))
        expect("strings: the OpenSSL prefix itself is allowed", not strings_findings(lines + [f'OPENSSLDIR: "{prefix}/ssl"'], version, suffix, prefix))
        # PE machine
        mach, found = machine_findings(data)
        expect("pe machine: the known DLL is x86-64", mach == "x86-64" and not found)
        pe = struct.unpack_from("<I", data, 0x3C)[0]
        bad_mach = bytearray(data)
        struct.pack_into("<H", bad_mach, pe + 4, 0x14C)
        expect("pe machine: a planted x86 machine is flagged", bool(machine_findings(bytes(bad_mach))[1]))
        expect("pe machine: a non-PE file is flagged", bool(machine_findings(b"not a pe file at all" * 10)[1]))
        # imports
        n_imp, found = import_findings(data)
        expect(f"imports: the known DLL passes ({n_imp} DLLs)", n_imp > 0 and not found)
        _m, names = pe_info(data)
        first, at = names[0]
        for label, repl in (("not on the allow-list", b"KERNEL33.dll"), ("an SSL DLL", b"libssl-3.dll")):
            plant = bytearray(data)
            plant[at:at + len(first)] = repl.ljust(len(first), b"x")[:len(first)]
            expect(f"imports: {label} is flagged", bool(import_findings(bytes(plant))[1]))
        # fresh
        build = work / "b1"
        (build / "build").mkdir(parents=True)
        cache = build / "build" / "CMakeCache.txt"
        cache.write_text("x\n")
        core = work / "core.dll"
        core.write_bytes(data)
        os.utime(cache, (time.time(), time.time()))
        os.utime(core, (time.time() - 100, time.time() - 100))
        expect("fresh: a core older than the cache is flagged", bool(fresh_findings(core, build)))
        os.utime(core, (time.time() + 100, time.time() + 100))
        expect("fresh: a newer core passes", not fresh_findings(core, build))
        expect("fresh: a missing core is flagged", bool(fresh_findings(work / "none.dll", build)))
        # deps
        for i in range(1000):
            (build / "build" / f"f{i}.cpp.o.d").write_text("f.o: /usr/include/stdio.h\n")
        count, found = deps_scan(build, ["src/core/hw/default_keys.h", "externals/libressl"])
        expect("deps: 1000 clean files pass", count == 1000 and not found)
        (build / "build" / "evil.cpp.o.d").write_text("f.o: src/core/hw/default_keys.h\n")
        expect("deps: a file naming a drop-list header is flagged", any("default_keys.h" in f for f in deps_scan(build, ["src/core/hw/default_keys.h"])[1]))
        expect("deps: 0 files are flagged", any("at least 1000" in f for f in deps_scan(work / "none", [])[1]))
        # the report, written by the code and read back against contract 1
        head, image, sha = "a" * 40, "ubuntu:26.04@sha256:" + "b" * 64, hashlib.sha256(data).hexdigest()
        green = [result_line("droplist cmake", "", []), result_line("deps", "files=1200", []), result_line("fresh", "", []),
                 result_line("window", "arrays=3 windows=24 hits=0", []), result_line("pe", "machine=x86-64", []),
                 result_line("imports", "n=9", [])]    # built by the same writer run_all uses
        out = work / "gate_f2.txt"
        out.write_bytes(report_text(head, image, sha, green).encode("utf-8"))
        text = out.read_bytes().decode("utf-8")
        expect("report: a written green file satisfies contract 1", not contract_findings(text, sha, head, image))
        expect("report: a wrong core sha is flagged", bool(contract_findings(text, "0" * 64, head, image)))
        expect("report: a wrong image is flagged", bool(contract_findings(text, sha, head, "ubuntu:26.04@sha256:" + "c" * 64)))
        red = list(green)
        red[3] = result_line("window", "", ["windows: the core holds window 3 of default_keys_enc"])
        expect("report: a FAIL line is written in place of PASS",
               red[3].startswith("FAIL window ") and bool(contract_findings(report_text(head, image, sha, red), sha, head, image)))
        expect("report: swapped lines are flagged", bool(contract_findings(report_text(head, image, sha, green[1::-1] + green[2:]), sha, head, image)))
        expect("report: a dropped line is flagged", bool(contract_findings(report_text(head, image, sha, green[:-1]), sha, head, image)))
        expect("report: CR line ends are flagged", bool(contract_findings(text.replace("\n", "\r\n"), sha, head, image)))
    print(f"plant-red: {len(problems)} problems" if problems else "plant-red: all planted reds fail as expected")
    return 1 if problems else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--build-dir", default=None)
    ap.add_argument("--core", default=None)
    ap.add_argument("--tree", default=None)
    ap.add_argument("--src-root", default=None, help="folder holding src/core/hw/default_keys.h and the two ctr-common-1 headers")
    ap.add_argument("--out", default=None)
    ap.add_argument("--plant-red", action="store_true")
    ap.add_argument("--dll", default=None, help="with --plant-red: a known-good core DLL (copied, never printed)")
    args = ap.parse_args(argv)
    if args.plant_red:
        if not args.dll:
            ap.error("--plant-red needs --dll")
        return plant_red(Path(args.dll))
    if not args.src_root:
        ap.error("--src-root is required")
    args.build_dir = args.build_dir or str(Path(args.repo) / "build-core")
    args.core = args.core or str(Path(args.build_dir) / CORE_NAME)
    args.out = args.out or str(Path(args.build_dir) / "gate_f2.txt")
    return run_all(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
