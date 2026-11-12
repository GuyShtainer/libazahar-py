"""Step F2's gate (docs/plans/phase-f2.md): our patched core, keys off, as rebuilt by step 0, against everything
Phases 1 and 2 built. Prints PASS/FAIL/RECORD lines; the summary goes to runs/f2/summary.txt.

``keyblob_findings`` / ``keyblob_records`` are importable without side effects (Phase 4's release_check uses them).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _use_repo_paths() -> None:
    """Put tests/ and python/ on sys.path; called by main() and the lazy imports, never at import time."""
    for sub in ("python", "tests"):
        p = str(REPO / sub)
        if p not in sys.path:
            sys.path.insert(0, p)

OPENSSL_RE = re.compile(r"OpenSSL|openssl@3")
DROP_BASENAMES_EXTRA = ("libressl",)
NM = "/usr/bin/nm"
OTOOL = "/usr/bin/otool"
STRINGS = "/usr/bin/strings"
LOG = "testapp/log.txt"
HEADER_BYTES = 256
T_STATE_BOUND = 2.5
ALL_IDS = ["keyblob", "symbols", "version", "dbg", "r1", "r2", "cross", "stock_r1"]
lines_out: list[str] = []
fail_count = 0


# ---------------------------------------------------------------- shared small helpers
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_kv(path: Path) -> dict[str, str]:
    """``KEY=value`` lines (core/PIN style): never executed; the first ``=`` splits."""
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip() and not raw.startswith("#") and "=" in raw:
            key, _, value = raw.partition("=")
            out[key.strip()] = value.strip()
    return out


def run_text(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace", check=False).stdout


# ---------------------------------------------------------------- f1: the supply chain of the rebuilt core
def _header_bytes(src_root: Path, rel: str, array: str) -> bytes:
    """All ``0x..`` tokens of the array's initializer in a reading-copy header (empty bytes when the file is missing)."""
    path = src_root / "src" / rel
    if not path.is_file():
        return b""
    text = path.read_text(encoding="utf-8", errors="replace")
    found = re.search(r"\b" + re.escape(array) + r"\s*\[[^\]]*\]\s*=\s*\{(.*?)\}", text, re.DOTALL)
    if found is None:
        return b""
    return bytes(int(tok, 16) for tok in re.findall(r"0x[0-9a-fA-F]{1,2}", found.group(1)))


KEY_ARRAYS = (("core/hw/default_keys.h", "default_keys_enc"),
              ("core/hle/service/http/ctr-common-1-cert.h", "ctr_common_1_cert_bin"),
              ("core/hle/service/http/ctr-common-1-key.h", "ctr_common_1_key_bin"))


def _window_findings(core_bytes: bytes, src_root: Path) -> list[str]:
    bad: list[str] = []
    for rel, array in KEY_ARRAYS:
        data = _header_bytes(src_root, rel, array)
        if len(data) < 128:
            bad.append(f"windows: {rel} in the reading copy is missing or parses to {len(data)} bytes: nothing was checked")
            continue
        n = len(data)
        for k in range(8):
            off = k * (n - 16) // 7
            if core_bytes.find(data[off:off + 16]) >= 0:
                bad.append(f"windows: the core holds window {k} of {array}")
    return bad


def _inputs_findings(build_dir: Path, repo: Path) -> tuple[dict[str, str], list[str]]:
    bad: list[str] = []
    pin = read_kv(repo / "core" / "PIN")
    path = build_dir / "build.inputs"
    if not path.is_file():
        return {}, ["build.inputs: missing (the old build has none)"]
    got = read_kv(path)       # "patch NAME=sha": the first '=' splits, names hold none
    want = {"tarball": pin.get("SRC_SHA256", "?"), "pin": sha256_file(repo / "core" / "PIN"),
            "script": sha256_file(repo / "tools" / "build-core.sh"), "drop": pin.get("LAZ_CORE_DROP", "?"),
            "openssl_version": pin.get("OPENSSL_VERSION", "?"), "clean": "yes"}
    for key, value in want.items():
        if got.get(key) != value:
            bad.append(f"build.inputs: {key}={got.get(key)!r}, want {value!r}")
    patches = {f"patch {p.name}": sha256_file(p) for p in sorted((repo / "core" / "patches").glob("*.patch"))}
    have = {k: v for k, v in got.items() if k.startswith("patch ")}
    for key in sorted(set(patches) | set(have)):
        if have.get(key) != patches.get(key):
            bad.append(f"build.inputs: {key} recorded {have.get(key)!r}, tree has {patches.get(key)!r}")
    for number in ("0007", "0008"):
        if not any(k.startswith(f"patch {number}-") for k in have):
            bad.append(f"build.inputs: patch {number} not among the recorded patches")
    for key in ("openssl_libssl_sha256", "openssl_libcrypto_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", got.get(key, "")):
            bad.append(f"build.inputs: {key} missing or not a sha256")
    return got, bad


def _cache_findings(build_dir: Path, prefix: str) -> list[str]:
    cache = build_dir / "build" / "CMakeCache.txt"
    text = cache.read_text(encoding="utf-8", errors="replace") if cache.is_file() else ""
    want = {"ENABLE_BUILTIN_KEYBLOB": "OFF", "USE_SYSTEM_OPENSSL": "ON",
            "OPENSSL_SSL_LIBRARY": f"{prefix}/lib/libssl.a", "OPENSSL_CRYPTO_LIBRARY": f"{prefix}/lib/libcrypto.a"}
    bad: list[str] = []
    for key, value in want.items():
        if not re.search(r"^" + re.escape(key) + r":[A-Z]*=" + re.escape(value) + r"$", text, re.MULTILINE):
            bad.append(f"cache: no line {key}:<type>={value}")
    return bad


def _od_findings(build_dir: Path, drop: list[str]) -> list[str]:
    names = [Path(entry).name for entry in drop] + list(DROP_BASENAMES_EXTRA)
    count = 0
    hits: list[str] = []
    for folder, _, files in os.walk(build_dir / "build"):
        for name in files:
            if name.endswith(".o.d"):
                count += 1
                text = (Path(folder) / name).read_text(encoding="utf-8", errors="replace")
                hits += [f"{Path(folder, name).name} names {n}" for n in names if n in text]
    bad = [f"o.d: {count} dependency files, want at least 1000"] if count < 1000 else []
    return bad + [f"o.d: {h}" for h in hits[:5]]


def _strings_findings(core: Path, version: str) -> list[str]:
    lines = run_text([STRINGS, "-a", str(core)]).splitlines()
    bad: list[str] = []
    if not any(line.strip() == "-lazpy.1" for line in lines):
        bad.append("strings: no line equal to -lazpy.1")
    if any("/Users/" in line for line in lines):
        bad.append("strings: a line holds /Users/ (a build path leaked)")
    if any("ClCertA file missing, using default" in line for line in lines):
        bad.append("strings: the default-ClCertA text is still in the core")
    if any("libressl" in line.lower() for line in lines):
        bad.append("strings: a line holds libressl")
    if not any(line.strip() == version or f"OpenSSL {version}" in line for line in lines):
        bad.append(f"strings: no line equal to {version} or holding 'OpenSSL {version}'")
    return bad


def keyblob_findings(build_dir: Path, core: Path, src_root: Path, tree: Path, repo: Path) -> list[str]:
    """Everything f1 checks; an empty list means the rebuilt core is the one that may ship."""
    build_dir, core, src_root, tree, repo = (Path(x) for x in (build_dir, core, src_root, tree, repo))
    bad: list[str] = []
    exit_file = build_dir / "build.exit"
    if not exit_file.is_file() or exit_file.read_text().strip() != "0":
        bad.append("build.exit: missing or not 0")
    cache = build_dir / "build" / "CMakeCache.txt"
    if not core.is_file() or not cache.is_file() or core.stat().st_mtime <= cache.stat().st_mtime:
        bad.append("core: missing, or not newer than build/CMakeCache.txt")
    got, found = _inputs_findings(build_dir, repo)
    bad += found
    pin = read_kv(repo / "core" / "PIN")
    drop = pin.get("LAZ_CORE_DROP", "").split()
    prefix = got.get("openssl_prefix", "")
    bad += _cache_findings(build_dir, prefix)
    if not (tree / "CMakeLists.txt").is_file():
        bad.append(f"tree: {tree} is not the build tree (no CMakeLists.txt): the drop list was not checked")
    else:
        bad += [f"tree: dropped entry {entry} is present in the build tree" for entry in drop if os.path.lexists(tree / entry)]
    if not drop:
        bad.append("PIN: LAZ_CORE_DROP is empty")
    bad += _od_findings(build_dir, drop)
    if core.is_file():
        bad += _window_findings(core.read_bytes(), src_root)
        bad += _strings_findings(core, pin.get("OPENSSL_VERSION", "?"))
        libs = run_text([OTOOL, "-L", str(core)])
        bad += [f"otool: links {m}" for m in sorted(set(re.findall(r"lib(?:ssl|crypto)[\w.-]*", libs)))]
    link = build_dir / "build" / "src" / "citra_libretro" / "CMakeFiles" / "citra_libretro.dir" / "link.txt"
    link_text = link.read_text(errors="replace") if link.is_file() else ""
    for lib in ("libssl.a", "libcrypto.a"):
        if f"{prefix}/lib/{lib}" not in link_text:
            bad.append(f"link.txt: does not name {prefix}/lib/{lib}")
    if "libressl" in link_text.lower():
        bad.append("link.txt: holds libressl")
    return bad


def keyblob_records(build_dir: Path, core: Path, src_root: Path, tree: Path, repo: Path) -> list[str]:
    """RECORD lines for f1: sizes, head, the OpenSSL prefix and archives, strings, link items, otool, linker notes."""
    build_dir, core = Path(build_dir), Path(core)
    got = read_kv(build_dir / "build.inputs") if (build_dir / "build.inputs").is_file() else {}
    prefix = got.get("openssl_prefix", "")
    out = [f"core size {core.stat().st_size} bytes", f"head={got.get('head')} openssl_prefix={prefix}"]
    for lib, key in (("libssl.a", "openssl_libssl_sha256"), ("libcrypto.a", "openssl_libcrypto_sha256")):
        archive = Path(prefix) / "lib" / lib
        now = sha256_file(archive) if archive.is_file() else None
        out.append(f"{archive} still matches the recorded sha256: {now == got.get(key)}")
    hits = [x for x in run_text([STRINGS, "-a", str(core)]).splitlines() if OPENSSL_RE.search(x)]
    out.append(f"strings holding OpenSSL/openssl@3: {len(hits)}; first 5: {hits[:5]}")
    link = build_dir / "build" / "src" / "citra_libretro" / "CMakeFiles" / "citra_libretro.dir" / "link.txt"
    text = link.read_text(errors="replace") if link.is_file() else ""
    frameworks = re.findall(r"-framework\s+(\S+)", text)
    libs = re.findall(r"(?<!\S)-l(\S+)", text)
    out.append(f"link line -framework: {frameworks}; -l: {libs}")
    out.append("otool -L: " + " | ".join(x.strip().split(" (")[0] for x in run_text([OTOOL, "-L", str(core)]).splitlines()[1:]))
    log = build_dir / "build.log"
    out.append("'built for newer 'macOS' version' lines in build.log: " +
               str(sum("built for newer 'macOS' version" in x for x in log.read_text(errors="replace").splitlines()) if log.is_file() else "no log"))
    return out


# ---------------------------------------------------------------- f2: the exported symbols
def def_names(src_root: Path) -> list[str]:
    path = Path(src_root) / "src" / "citra_libretro" / "libretro.osx.def"
    return [x.strip() for x in path.read_text().splitlines() if x.startswith("_")]


def exported(core: Path) -> set[str]:
    return {x.split()[-1] for x in run_text([NM, "-gU", str(core)]).splitlines() if x.strip()}


LAZPY_EXTRA = ["_lazpy_read_memory", "_lazpy_write_memory", "_lazpy_movie_play"]


def symbol_findings(ours: Path, stock: Path, src_root: Path) -> tuple[list[str], list[str]]:
    """(findings for ours, findings for stock); the expected sets come from SRC's libretro.osx.def."""
    names = set(def_names(src_root))
    res = []
    for core, want in ((ours, names | set(LAZPY_EXTRA)), (stock, names)):
        have = exported(core)
        res.append([f"{core.name}: extra {sorted(have - want)}, missing {sorted(want - have)}"] if have != want else [])
    return res[0], res[1]


# ---------------------------------------------------------------- output
def emit(kind: str, ident: str, detail: str) -> None:
    global fail_count
    fail_count += kind == "FAIL"
    line = f"{kind} {ident} {detail}"
    lines_out.append(line)
    print(line, flush=True)


def check(ident: str, ok: bool, detail: str) -> None:
    emit("PASS" if ok else "FAIL", ident, detail)


def record(ident: str, detail: str) -> None:
    emit("RECORD", ident, detail)


def gc():
    _use_repo_paths()
    import gate_c
    gate_c.RUNS = REPO / "runs" / "f2"
    return gate_c


def note_exitpath(host_log: Path) -> None:
    """Append the host.log's path to runs/f2/exitpath-ours.txt when it holds C's exit-path line."""
    gate_c = gc()
    if host_log.is_file() and gate_c.EXIT_PATH_LINE in host_log.read_text(errors="replace"):
        with open(REPO / "runs" / "f2" / "exitpath-ours.txt", "a") as handle:
            handle.write(f"{host_log}\n")


def azrun(ident: str, core: Path, flags: list[str], control: dict, timeout: int = 900) -> dict:
    gate_c = gc()
    res = gate_c.run_azhost(ident, ["--core", str(core)] + flags, control, timeout)
    if "lazpy" in core.name:
        note_exitpath(res["out"] / "host.log")
    return res


# ---------------------------------------------------------------- scenarios
def scen_keyblob(a) -> None:
    args = (a.build_dir, a.ours, a.src_root, a.tree, REPO)
    found = keyblob_findings(*args)
    check("keyblob", not found, "all f1 checks hold" if not found else "; ".join(found))
    for text in keyblob_records(*args):
        record("keyblob", text)


def scen_symbols(a) -> None:
    ours, stock = symbol_findings(a.ours, a.stock, a.src_root)
    check("symbols.ours", not ours, "the 25 retro_* names plus the 3 lazpy_* names" if not ours else "; ".join(ours))
    check("symbols.stock", not stock, "exactly the 25 retro_* names" if not stock else "; ".join(stock))


def scen_version(a) -> None:
    res = azrun("version", a.ours, ["--frames", "30"], {})
    log = (res["out"] / "host.log").read_text(errors="replace") if (res["out"] / "host.log").exists() else ""
    found = re.search(r"core (.+?) version (\S+)", log)
    version = found.group(2) if found else None
    check("version", res["rc"] == 0 and version == "2126.2-lazpy.1", f"rc={res['rc']} core version {version!r}")
    want = [tuple(x.split("=", 1)) for x in (REPO / "core" / "options-lazpy.txt").read_text().splitlines()
            if x.strip() and not x.startswith("#")]
    logged = dict(re.findall(r"\boption (\w+)=(\S.*?)\s*$", log, re.MULTILINE))
    wrong = [f"{k}: logged {logged.get(k)!r}, want {v!r}" for k, v in want if logged.get(k) != v]
    check("options", len(want) == 6 and not wrong, f"{len(want)} keys of options-lazpy.txt " + ("logged with its values" if not wrong else "; ".join(wrong)))


def dbg_run(a, ident: str) -> dict:
    res = azrun(ident, a.ours, ["--frames", "600,1,1,1,1,1,1,1,1", "--debug-stop", "ready f=", "--print-last-line", LOG],
                {"ready_at": 200})
    gate_c = gc()
    sums = res["summaries"]
    cs = gate_c.cc.boot_offsets(sums[1:], {i: res["last"][i + 1] for i in range(1, len(sums)) if i + 1 in res["last"]})
    _, events = gate_c.get_log(res)
    ready = [e for e in events if e["kind"] == "ready"]
    first = res["last"].get(1) or {}
    return {"res": res, "last": sums[0]["last"] if sums else None, "stop": sums[0]["stop"] if sums else None,
            "c_min": min(cs) if cs else None, "ready_v": ready[0]["v"] if ready else None, "line1": first}


def scen_dbg(a) -> None:
    runs = [dbg_run(a, f"dbg.{n}") for n in (1, 2)]
    for n, r in enumerate(runs, start=1):
        line = r["line1"]
        d3 = r["last"] - (r["ready_v"] + r["c_min"]) if None not in (r["last"], r["ready_v"], r["c_min"]) else None
        check(f"dbg.{n}.d1", r["stop"] == "debug_text", f"batch 1 stop={r['stop']}")
        ok2 = (line.get("kind") == "ready" and line.get("f") == 200) or (line.get("kind") == "frame" and line.get("f") == 201)
        check(f"dbg.{n}.d2", ok2, f"batch 1 last line kind={line.get('kind')} f={line.get('f')}")
        check(f"dbg.{n}.d3", d3 in (0, 1), f"last={r['last']} ready.v={r['ready_v']} c_min={r['c_min']} last-(ready.v+c_min)={d3}")
    check("dbg.d4", runs[0]["last"] == runs[1]["last"] and runs[0]["line1"] == runs[1]["line1"],
          f"last {runs[0]['last']} vs {runs[1]['last']}; line {runs[0]['line1']} vs {runs[1]['line1']}")
    sd = azrun("dbg.sd", a.ours, ["--frames", "600", "--stop-file", LOG, "--stop-text", "ready f=", "--stop-every", "1"],
               {"ready_at": 200})
    record("dbg.sd", f"--stop-every 1: stop={sd['summaries'][0]['stop'] if sd['summaries'] else None} last="
                     f"{sd['summaries'][0]['last'] if sd['summaries'] else None}; the debug stop's last {runs[0]['last']}")


R1_STATES = [(120, 1, 0, 0, 0, 0, 0), (130, 0, 0, 0, 0, 0, 0), (140, 2, 0, 0, 0, 0, 0), (150, 0, 0, 0, 0, 0, 0),
             (150, 0, 1, 160, 120, 0, 0), (160, 0, 0, 0, 0, 0, 0), (170, 0, 0, 0, 0, 32767, 0), (180, 0, 0, 0, 0, 0, 0)]


def r1_run(core: Path, ident: str) -> dict:
    gate_c = gc()
    inputs = REPO / "runs" / "f2" / f"{ident}-inputs.txt"
    inputs.parent.mkdir(parents=True, exist_ok=True)
    gate_c.write_inputs(inputs, R1_STATES)
    res = azrun(ident, core, ["--frames", "600,120", "--inputs", str(inputs), "--shot", "100,250", "--print-last-line", LOG],
                {"break_at": 300})
    res["shots"] = {n: sha256_file(res["out"] / n) for n in ("shot_000100_top.png", "shot_000100_bottom.png",
                                                              "shot_000250_top.png", "shot_000250_bottom.png")
                    if (res["out"] / n).is_file()}
    return res


def r1_diff(x: dict, y: dict) -> list[str]:
    """Every difference between two r1 runs: shot hashes, the SD log (first differing line and field), summary fields."""
    diffs: list[str] = []
    for name in sorted(set(x["shots"]) | set(y["shots"])):
        if x["shots"].get(name) != y["shots"].get(name):
            diffs.append(f"shot {name}: {x['shots'].get(name)} vs {y['shots'].get(name)}")
    la = x["log"].read_bytes() if x["log"].exists() else b""
    lb = y["log"].read_bytes() if y["log"].exists() else b""
    if la != lb:
        ra, rb = la.decode(errors="replace").splitlines(), lb.decode(errors="replace").splitlines()
        first = next((i for i, (p, q) in enumerate(zip(ra, rb)) if p != q), min(len(ra), len(rb)))
        pa, pb = (ra[first] if first < len(ra) else ""), (rb[first] if first < len(rb) else "")
        fields = [f"{k.split('=')[0]}" for k, l in zip(pa.split(), pb.split()) if k != l]
        diffs.append(f"log.txt differs at line {first + 1} (fields {fields}): {pa!r} vs {pb!r}; lengths {len(la)} vs {len(lb)}")
    sa, sb = x["summaries"], y["summaries"]
    drop = ("wall", "fps", "wall_ms_mean")
    if len(sa) != len(sb):
        diffs.append(f"summary count {len(sa)} vs {len(sb)}")
    for i, (p, q) in enumerate(zip(sa, sb), start=1):
        pa, pb = {k: v for k, v in p.items() if k not in drop}, {k: v for k, v in q.items() if k not in drop}
        diffs += [f"summary {i} {k}: {pa.get(k)!r} vs {pb.get(k)!r}" for k in sorted(set(pa) | set(pb)) if pa.get(k) != pb.get(k)]
    return diffs


def scen_r1(a) -> None:
    x, y = r1_run(a.ours, "r1.1"), r1_run(a.ours, "r1.2")
    stops = [r["summaries"][0]["stop"] if r["summaries"] else None for r in (x, y)]
    check("r1.break", stops == ["guest_break", "guest_break"] and len(x["shots"]) == len(y["shots"]) == 4, f"batch 1 stops {stops}, shots {len(x['shots'])}/{len(y['shots'])}")
    diffs = r1_diff(x, y)
    check("r1", not diffs, "shots, log.txt and summaries identical" if not diffs else "; ".join(diffs[:6]))
    record("r1", f"shot sha256s {x['shots']}; log.txt {x['log'].stat().st_size if x['log'].exists() else 0} bytes")


def scen_stock_r1(a) -> None:
    x, y = r1_run(a.stock, "stock-r1.1"), r1_run(a.stock, "stock-r1.2")
    diffs = r1_diff(x, y)
    record("stock_r1", f"{len(diffs)} differences on the stock core: " + ("; ".join(diffs[:6]) if diffs else "none"))
    record("stock_r1", f"shots match: {x['shots'] == y['shots']}")


def tree_files(folder: Path) -> list[str]:
    return sorted(str(p.relative_to(folder)) for p in folder.glob("*")) if folder.is_dir() else []


def r2_chain(a, c: int) -> dict:
    _use_repo_paths()
    import testapp_log as tl
    from libazahar import Emulator
    wd = REPO / "runs" / "f2" / f"r2-{c}"
    shutil.rmtree(wd, ignore_errors=True)
    tl.write_control(wd / "seed", boot_frames=1200)
    app = REPO / "build" / "testapp.3dsx"
    out: dict = {}
    emu = Emulator(app, wd / "a", sd_seed=wd / "seed", core=a.ours)
    try:
        emu.run(1300)
        log_a = emu.sd / LOG
        out["booted"] = "booted" in log_a.read_text(errors="replace")
        info = emu.save_state(wd / "s.state")
        length = log_a.stat().st_size
        shots_a = emu.run(300, shots=[100, 300]).shots
        data = log_a.read_bytes()
        out["a_lines"] = data[length:].decode(errors="replace").splitlines()
        out["a_shots"] = {f: (sha256_file(Path(s.top)), sha256_file(Path(s.bottom))) for f, s in shots_a.items()}
        out["k"] = info.k
    finally:
        emu.close()
    shutil.copytree(wd / "a" / "sys", wd / "b" / "sys", ignore=shutil.ignore_patterns("sdmc"))
    out["copied"] = tree_files(wd / "b" / "sys") + tree_files(wd / "b" / "sys" / "Azahar")
    t0 = time.monotonic()
    emu_b = Emulator(app, wd / "b", state=wd / "s.state", core=a.ours)
    out["t_state"] = time.monotonic() - t0
    try:
        snap = (Path(f"{wd / 's.state'}.sd") / LOG).stat().st_size
        shots_b = emu_b.run(300, shots=[100, 300]).shots
        out["b_lines"] = (emu_b.sd / LOG).read_bytes()[snap:].decode(errors="replace").splitlines()
        out["b_shots"] = {f: (sha256_file(Path(s.top)), sha256_file(Path(s.bottom))) for f, s in shots_b.items()}
    finally:
        emu_b.close()
    host_log = wd / "b" / "host.log"
    out["load_line"] = next((x for x in host_log.read_text(errors="replace").splitlines() if "state load" in x), "")
    for sub in ("a", "b"):
        note_exitpath(wd / sub / "host.log")
    out["state"] = (wd / "s.state").read_bytes()
    out["state_path"] = wd / "s.state"
    return out


def scen_r2(a) -> None:
    chains = []
    for c in (1, 2):
        try:
            chains.append(r2_chain(a, c))
        except Exception as exc:       # a failed chain must show as FAIL, not a traceback
            check(f"r2.{c}", False, f"{type(exc).__name__}: {exc}")
            return
    b1, b2 = chains[0], chains[1]
    check("r2.boot", all(ch["booted"] for ch in chains), "the log has the booted line in both chains")
    check("r2.b", b1["b_lines"] == b2["b_lines"] and b1["b_shots"] == b2["b_shots"] and len(b1["b_lines"]) > 200,
          f"restored instances: {len(b1['b_lines'])} vs {len(b2['b_lines'])} log lines, shots equal {b1['b_shots'] == b2['b_shots']}")
    for c, ch in enumerate(chains, start=1):
        check(f"r2.{c}.t_state", ch["t_state"] < T_STATE_BOUND, f"t_state={ch['t_state']:.2f} s (bound {T_STATE_BOUND}) load={os.getloadavg()}")
        record(f"r2.{c}", f"a==b {ch['a_lines'] == ch['b_lines']} (lines), shots equal {ch['a_shots'] == ch['b_shots']}; k={ch['k']}; {ch['load_line']}")
        record(f"r2.{c}", f"copied into b/sys: {ch['copied']}")
    s1, s2 = b1["state"], b2["state"]
    diff_head = [i for i in range(min(HEADER_BYTES, len(s1), len(s2))) if s1[i] != s2[i]]
    record("r2", f"a1==a2 lines {b1['a_lines'] == b2['a_lines']} shots {b1['a_shots'] == b2['a_shots']}; state files after byte {HEADER_BYTES} equal "
                 f"{s1[HEADER_BYTES:] == s2[HEADER_BYTES:]} ({len(s1)} vs {len(s2)} bytes); header bytes differing {diff_head}")


def boot_err(fn) -> str:
    try:
        return fn()
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


def scen_cross(a) -> None:
    _use_repo_paths()
    import testapp_log as tl
    from libazahar import Emulator
    wd = REPO / "runs" / "f2" / "cross"
    shutil.rmtree(wd, ignore_errors=True)
    app = REPO / "build" / "testapp.3dsx"

    def last_f(path: Path) -> int | None:
        rows = tl.parse_log(path)[0] if path.exists() else []
        return rows[-1]["f"] if rows else None

    def load_into(name: str, state: Path, core: Path, src: str) -> None:
        def go() -> str:
            with Emulator(app, wd / name, state=state, core=core) as emu:
                before = last_f(emu.sd / LOG)
                emu.run(60)
                return f"ok, log f {before} at load, {last_f(emu.sd / LOG)} after 60 frames"
        record("cross", f"{src} state into {core.name}: {boot_err(go)}")

    def make() -> str:
        with Emulator(app, wd / "x", core=a.stock) as emu:
            emu.run(300)
            emu.save_state(wd / "stock.state")
        return "made"
    made = boot_err(make)
    if made != "made":
        record("cross", f"stock state not made: {made}")
    else:
        load_into("y", wd / "stock.state", a.ours, "stock")
    ours_state = REPO / "runs" / "f2" / "r2-1" / "s.state"
    if ours_state.is_file():
        load_into("z", ours_state, a.stock, "our-core")
    else:
        record("cross", f"no {ours_state}: run r2 first for the reverse direction")


SCENARIOS = {"keyblob": scen_keyblob, "symbols": scen_symbols, "version": scen_version, "dbg": scen_dbg, "r1": scen_r1,
             "r2": scen_r2, "cross": scen_cross, "stock_r1": scen_stock_r1}


def main() -> int:
    _use_repo_paths()
    default_main = Path(os.path.realpath(REPO / "dl" / "azahar-src")).parent.parent       # MAIN, also from a worktree
    top = read_kv(REPO / "core" / "PIN").get("SRC_TOP", "")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ours", type=Path, required=True)
    ap.add_argument("--stock", type=Path, required=True)
    ap.add_argument("--only", default=",".join(ALL_IDS))
    ap.add_argument("--build-dir", type=Path, default=default_main / "build-core")
    ap.add_argument("--src-root", type=Path, default=default_main / "dl" / "azahar-src" / "unpacked" / top)
    ap.add_argument("--tree", type=Path, default=default_main / "dl" / "azahar-src" / "build-src" / top)
    a = ap.parse_args()
    a.ours, a.stock = a.ours.resolve(), a.stock.resolve()
    (REPO / "runs" / "f2").mkdir(parents=True, exist_ok=True)
    only = [x for x in a.only.split(",") if x]
    unknown = [x for x in only if x not in SCENARIOS]
    if unknown:
        ap.error(f"unknown ids {unknown}; known {ALL_IDS}")
    print(f"ours={a.ours} stock={a.stock} load={os.getloadavg()}", flush=True)
    for ident in [x for x in ALL_IDS if x in only]:      # fixed order: keyblob first
        try:
            SCENARIOS[ident](a)
        except (OSError, KeyError, IndexError, ValueError, TypeError, subprocess.SubprocessError) as exc:
            check(ident, False, f"scenario error {type(exc).__name__}: {exc}")
        if ident == "keyblob" and fail_count:
            lines_out.append("STOP the gated build is not the build that may ship")
            print(lines_out[-1], flush=True)
            break
    failed_c = gc().failed if "gate_c" in sys.modules else 0
    lines_out.append(f"gate_f2: {fail_count} FAIL, gate_c.failed {failed_c}")
    print(lines_out[-1], flush=True)
    (REPO / "runs" / "f2" / "summary.txt").write_text("\n".join(lines_out) + "\n")
    return 0 if fail_count == 0 and failed_c == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
