#!/usr/bin/env python3
"""Write NOTICES.md for the libazahar-py core and test app, from what the core really links and includes.

Usage: python3 -I tools/mknotices.py --link LINK.txt --deps BUILD --tree TREE --src SRC --inputs build.inputs
           --openssl openssl-3.6.5.tar.gz --sysarch citra_system_archives.tar.gz [--ofl FILE] [--unifont FILE] > NOTICES.md

Reads the link line's static libraries and every compile dependency file (*.o.d) under BUILD, sorts each path into a
component (table COMPONENTS), a src/ notice (table SRC_NOTICES), OpenSSL (the Cellar path in build.inputs), generated
or system. An unknown path, an unknown component or any externals/libressl path exits 1 naming it. Licence texts are
copied verbatim from SRC, the OpenSSL tarball and the snapshot (tarfile, nothing extracted). Output has no dates.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import tarfile
from pathlib import Path

# name -> (folder under externals/, licence sources, short name, libs from the link line, extra required text)
# A licence source is a path under externals/, or (path, first line, last line) for a header's licence comment, or
# ("MIT-BODY", path, comment path, a, b): the header's copyright lines plus the MIT body of another component's file.
C = "dynarmic/externals/"
COMPONENTS = {
    "boost": ("boost", ["boost/LICENSE_1_0.txt"], "BSL-1.0", ["boost_iostreams", "boost_serialization"], ""),
    "cryptopp": ("cryptopp", ["cryptopp/LICENSE"], "BSL-1.0 (Crypto++)", ["cryptopp"], ""),
    "dds-ktx": ("dds-ktx", ["dds-ktx/LICENSE"], "BSD-2-Clause", [], ""),
    "dynarmic": ("dynarmic", ["dynarmic/LICENSE.txt"], "0BSD", ["dynarmic"], ""),
    "enet": ("enet", ["enet/LICENSE"], "MIT", ["enet"], ""),
    "faad2": ("faad2", [("faad2/faad2/README", 12, 39)], "GPL-2.0-or-later", ["faad2"],
              "Code from FAAD2 is copyright (c) Nero AG, www.nero.com"),
    "fmt": ("fmt", ["fmt/LICENSE"], "MIT", ["fmt"], ""),
    "glslang": ("glslang", ["glslang/LICENSE.txt"], "BSD-3-Clause and others (see text)", ["glslang", "SPIRV"], ""),
    "httplib": ("httplib", [("MIT-BODY", "httplib/httplib.h", 3, 5)], "MIT", [], ""),
    "json": ("json", [("MIT-BODY", "json/json.hpp", 6, 7)], "MIT", [], ""),
    "library-headers": ("library-headers", ["library-headers/ffmpeg/LICENSE.md"], "LGPL-2.1-or-later (FFmpeg headers)", [], ""),
    "libretro-common": ("libretro-common", [("libretro-common/libretro-common/include/libretro.h", 1, 28)], "MIT", [], ""),
    "lodepng": ("lodepng", ["lodepng/lodepng/LICENSE"], "Zlib", ["lodepng"], ""),
    "mcl": (C + "mcl", [C + "mcl/LICENSE"], "MIT", ["mcl"], ""),
    "microprofile": ("microprofile", [("microprofile/microprofile.h", 2, 22)], "Unlicense", [], ""),
    "nihstro": ("nihstro", ["nihstro/license.txt"], "BSD-3-Clause", [], ""),
    "oaknut": ("oaknut", ["oaknut/LICENSE"], "MIT", [], ""),
    "open_source_archives": ("open_source_archives", [], "see the system archives section", [], ""),
    "robin-map": (C + "robin-map", [C + "robin-map/LICENSE"], "MIT", [], ""),
    "sirit": ("sirit", ["sirit/sirit/LICENSE.txt"], "BSD-3-Clause", ["sirit"], ""),
    "soundtouch": ("soundtouch", ["soundtouch/COPYING.TXT"], "LGPL-2.1", ["SoundTouch"],
                   "LGPL-2.1: this release's complete corresponding source of the whole work lets you relink"),
    "spirv-headers": ("spirv-headers", ["spirv-headers/LICENSE"], "MIT (Khronos)", [], ""),
    "spirv-tools": ("spirv-tools", ["spirv-tools/LICENSE"], "Apache-2.0", ["SPIRV-Tools", "SPIRV-Tools-opt"], ""),
    "teakra": ("teakra", ["teakra/LICENSE"], "MIT", ["teakra"], ""),
    "vma": ("vma", ["vma/LICENSE.txt"], "MIT", [], ""),
    "vulkan-headers": ("vulkan-headers", ["vulkan-headers/LICENSE.md", "vulkan-headers/LICENSES/Apache-2.0.txt",
                                          "vulkan-headers/LICENSES/MIT.txt"], "Apache-2.0 OR MIT", [], ""),
    "xxHash": ("xxHash", ["xxHash/LICENSE"], "BSD-2-Clause", ["xxhash"], ""),
    "zstd": ("zstd", ["zstd/LICENSE"], "BSD-3-Clause", ["zstd", "zstd_seekable"], ""),
}
OWN_LIBS = {"audio_core", "citra_common", "citra_core", "network", "video_core"}
OPENSSL_LIBS = {"ssl", "crypto"}
MIT_BODY_FROM = "dynarmic/externals/robin-map/LICENSE"

# regex on a src/ notice block -> (holder, short name, verbatim?); GPL-family notices name their holder only
SRC_NOTICES = [
    (r"yuzu [Ee]mulator", "yuzu Emulator Project", "GPL-2.0-or-later", False),
    (r"Dolphin Emulator|Gekko Emulator|PPSSPP", "Dolphin, Gekko and PPSSPP projects", "GPL-2.0-or-later", False),
    (r"Skyeye|Advanced RISC Machines|ARM Limited|Michael\.Kang", "SkyEye, ARM and ARMulator authors",
     "GPL-2.0-or-later", False),
    (r"Google, Inc\.", "Google, Inc. (CityHash)", "MIT", True),
    (r"Tony Wasserka", "Tony Wasserka", "BSD-3-Clause", True),
    (r"Kyle Lutz", "Kyle Lutz", "BSL-1.0", True),
    (r"Robert Ramey", "Robert Ramey and Matthias Troyer (Boost.Serialization)", "BSL-1.0", True),
    (r"bloc97", "bloc97", "MIT", True),
    (r"BreadFish64", "BreadFish64", "MIT", True),
    (r"Pixellizer", "The Pixellizer Group", "MIT", True),
]
OWN_RE = re.compile(r"(Citra|Azahar) Emulator Project")
FLAG_RE = re.compile(r"Copyright|SPDX-License-Identifier|Permission is hereby granted")
SYSTEM = ("/Applications/", "/Library/", "/usr/", "/System/")


def die(msg: str) -> None:
    print(f"mknotices: {msg}", file=sys.stderr)
    raise SystemExit(1)


def read_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in path.read_text(errors="replace").splitlines():
        key, sep, val = raw.partition("=")
        if sep:
            out[key.strip()] = val.strip()
    return out


def dep_paths(deps: Path) -> set[str]:
    paths: set[str] = set()
    for root, _dirs, files in os.walk(deps, followlinks=True):
        for name in files:
            if name.endswith(".o.d"):
                text = (Path(root) / name).read_text(errors="replace").replace("\\\n", " ")
                paths.update(w for w in text.split()[1:] if not w.endswith(":"))
    return paths


def classify(paths: set[str], tree_name: str, keg: str) -> tuple[set[str], set[str], bool]:
    """Return (component names, src/ files, uses OpenSSL); exit 1 on anything unknown."""
    comps: set[str] = set()
    src: set[str] = set()
    ssl = False
    for raw in sorted(paths):
        path = raw.replace("/./", "/")
        found = re.search("/" + re.escape(tree_name) + "/(.*)$", path)
        if path.startswith(keg + "/"):
            ssl = True
        elif "/build-core/build/" in path or path.startswith(SYSTEM):
            continue
        elif found is None:
            die(f"unclassified dependency path: {raw}")
        elif found.group(1).startswith("src/"):
            src.add(found.group(1))
        elif found.group(1).startswith("externals/"):
            comps.add(external_name(found.group(1), raw))
        else:
            die(f"unclassified dependency path: {raw}")
    return comps, src, ssl


def external_name(rel: str, raw: str) -> str:
    parts = rel.split("/")
    if parts[1] == "libressl":
        die(f"externals/libressl in the dependencies: {raw}")
    name = parts[3] if parts[1] == "dynarmic" and parts[2:3] == ["externals"] and len(parts) > 3 else parts[1]
    if name not in COMPONENTS:
        die(f"component missing from the table: {name} ({raw})")
    return name


def link_libs(link: Path) -> set[str]:
    libs = set()
    for word in link.read_text(errors="replace").split():
        if word.endswith(".a"):
            libs.add(re.sub(r"^lib|\.a$", "", os.path.basename(word)))
    known = OWN_LIBS | OPENSSL_LIBS | {lib for c in COMPONENTS.values() for lib in c[3]}
    for lib in sorted(libs - known):
        die(f"link line holds a library missing from the table: {lib}")
    return libs


def comment_block(lines: list[str], idx: int) -> str:
    def is_comment(line: str) -> bool:
        text = line.lstrip()
        return text.startswith(("//", "/*", "*")) or re.match(r"#(\s|$)", text) is not None

    lo = hi = idx
    while lo > 0 and is_comment(lines[lo - 1]):
        lo -= 1
    while hi + 1 < len(lines) and is_comment(lines[hi + 1]):
        hi += 1
    return re.sub(r"[\w.+-]+@gmail\.com", "[address omitted]", "\n".join(lines[lo:hi + 1]))


def scan_src(tree: Path, files: set[str]) -> dict[str, tuple[str, str, bool, set[str], set[str]]]:
    """Group the src/ notices: regex -> (holder, short, verbatim, files, distinct blocks)."""
    for path in (tree / "src" / "video_core" / "host_shaders").rglob("*"):
        if path.is_file():
            files.add(str(path.relative_to(tree)))
    groups: dict[str, tuple[str, str, bool, set[str], set[str]]] = {}
    for rel in sorted(files):
        lines = (tree / rel).read_text(errors="replace").split("\n")[:40]
        hits = [i for i, ln in enumerate(lines) if FLAG_RE.search(ln) and not OWN_RE.search(ln)]
        if not hits:
            continue
        block = comment_block(lines, hits[0])
        for pattern, holder, short, verbatim in SRC_NOTICES:
            if re.search(pattern, block):
                entry = groups.setdefault(pattern, (holder, short, verbatim, set(), set()))
                entry[3].add(rel)
                entry[4].add(block)
                break
        else:
            die(f"src/ notice missing from the table: {rel}")
    return groups


def fence(text: str) -> str:
    return "```text\n" + text.rstrip("\n") + "\n```\n"


def licence_text(src: Path, spec: object) -> str:
    ext = src / "externals"
    if isinstance(spec, str):
        return (ext / spec).read_text(errors="replace")
    if spec[0] == "MIT-BODY":
        _tag, path, first, last = spec
        head = "\n".join((ext / path).read_text(errors="replace").split("\n")[first - 1:last])
        body = (ext / MIT_BODY_FROM).read_text(errors="replace").split("\n\n", 2)[-1]
        return head + "\n\n(MIT licence; the permission text is the same as in the robin-map licence file:)\n\n" + body
    path, first, last = spec
    return "\n".join((ext / path).read_text(errors="replace").split("\n")[first - 1:last])


def component_section(name: str, src: Path, libs: set[str]) -> str:
    folder, specs, short, own_libs, extra = COMPONENTS[name]
    use = "linked (static)" if libs & set(own_libs) else "headers only"
    out = [f"### {name}\n", f"Folder: `externals/{folder}`. Use: {use}. Licence: {short}.\n"]
    for spec in specs:
        out.append(fence(licence_text(src, spec)))
    if extra:
        out.append(extra + "\n")
    if name == "faad2":
        out.append("Copyright (C) 2003-2005 M. Bakker, Nero AG, http://www.nero.com\n")
    return "\n".join(out)


def read_member(tar_path: Path, suffix: str) -> str | None:
    with tarfile.open(tar_path) as archive:
        for member in archive.getmembers():
            if member.isfile() and re.fullmatch(r"[^/]+/" + re.escape(suffix), member.name):
                return archive.extractfile(member).read().decode("utf-8", errors="replace")  # type: ignore[union-attr]
    return None


def openssl_section(ossl: Path, version: str) -> str:
    licence = read_member(ossl, "LICENSE.txt") or die("OpenSSL tarball has no LICENSE.txt") or ""
    readme = read_member(ossl, "README.md") or ""
    line = next((ln.strip() for ln in readme.split("\n") if "The OpenSSL Project Authors" in ln), None)
    if line is None:
        die("no OpenSSL Project Authors copyright line in the tarball's README.md")
    notice = read_member(ossl, "NOTICE")
    out = [f"### openssl\n", f"OpenSSL {version} (Homebrew `openssl@3`, statically linked), Apache-2.0.\n",
           line + "\n", fence(licence)]
    out.append(fence(notice) if notice else "OpenSSL's source tarball has no NOTICE file (checked).\n")
    return "\n".join(out)


def src_section(groups: dict) -> str:
    out = ["## Inside Azahar's tree\n",
           "Files of Azahar's own source that carry another project's notice (listed by holder; the MIT, BSD and "
           "Boost notices are quoted verbatim, the GPL-family ones are covered by the GPL text that travels with the "
           "binary).\n"]
    for _pattern, (holder, short, verbatim, files, blocks) in sorted(groups.items(), key=lambda kv: kv[1][0]):
        out.append(f"### {holder} ({short})\n")
        out.append("Files:\n" + "\n".join(f"- `{f}`" for f in sorted(files)) + "\n")
        if verbatim:
            out += [fence(b) for b in sorted(blocks)]
    return "\n".join(out)


def archives_section(tree: Path, snap: Path, ofl: Path | None, uni: Path | None) -> str:
    head = ["## open_source_archives\n",
            "Open-source replacement system archives generated by the Citra project's citra_system_archives "
            "(GPLv2 or later). Azahar's tarball has no licence file for them; the generator's snapshot is a release "
            "asset (`citra_system_archives-f470e0c.tar.gz`).\n"]
    inc = tree / "externals" / "open_source_archives" / "include"
    for header in sorted(inc.glob("*.h")):
        first = header.read_text(errors="replace").split("\n")[0]
        commit = re.search(r"Git Hash:\s*([0-9a-f]{7})", first)
        if commit is None:
            die(f"no generator commit in {header.name}")
        digest = hashlib.sha256(header.read_bytes()).hexdigest()
        head.append(f"- `externals/open_source_archives/include/{header.name}`: sha256 {digest}, generator commit "
                    f"{commit.group(1)}")
    head.append("\n47cdc93 cannot be found in citra_system_archives' history; its content matches 2d98119.\n")
    head.append("The font holds glyphs from Montserrat Regular 4.000 and GNU Unifont 10.0.05.\n")
    head.append(font_texts(snap, ofl, uni))
    return "\n".join(head)


def font_texts(snap: Path, ofl: Path | None, uni: Path | None) -> str:
    ofl_text = read_member_deep(snap, "OFL") or (ofl.read_text() if ofl else None)
    uni_text = read_member_deep(snap, "unifont-notice") or (uni.read_text() if uni else None)
    if ofl_text is None or uni_text is None:
        die("no OFL text or no Unifont notice (snapshot has none; pass --ofl and --unifont)")
    # The OFL file's first line carries a contact address; the font's own name record line replaces it.
    ofl_body = ofl_text.split("\n", 2)[2] if ofl_text.startswith("Copyright") else ofl_text
    uni_lines = uni_text.split("\n")
    return "\n".join([
        "Montserrat Regular 4.000: Copyright 2011 - 2016 The Montserrat Project Authors. SIL Open Font License 1.1:\n",
        fence(ofl_body),
        f"GNU Unifont 10.0.05: {uni_lines[0]} GPLv2 or later with the GNU font embedding exception.\n",
        fence("\n".join(uni_lines[2:]))])


def read_member_deep(snap: Path, kind: str) -> str | None:
    """A licence text from the snapshot's members, when it holds one (it does not: the OFL and notice files are given)."""
    names = {"OFL": re.compile(r"(^|/)OFL[^/]*\.txt$", re.I), "unifont-notice": re.compile(r"unifont[^/]*(notice|licen)", re.I)}
    with tarfile.open(snap) as archive:
        for member in archive.getmembers():
            if member.isfile() and names[kind].search(member.name):
                return archive.extractfile(member).read().decode("utf-8", errors="replace")  # type: ignore[union-attr]
    return None


def header_section(inputs: dict[str, str], commit: str) -> str:
    patches = [f"- `{k[6:]}` sha256 {v}" for k, v in sorted(inputs.items()) if k.startswith("patch ")]
    return "\n".join([
        "# NOTICES\n",
        "This file covers the core `azahar_lazpy_libretro.dylib` and the test app `testapp.3dsx`. The repository's "
        "own code is GPLv3 (`LICENSE`). The core binary is distributed under GPLv3 (Azahar's 'or any later version' "
        "grant permits it; the binary links Apache-2.0 code, which GPLv2 does not accept).\n",
        "## libazahar-py's changes to Azahar\n", "\n".join(patches) + "\n",
        "Each changed file carries a 'Modified by libazahar-py' notice (patch 0000). Removed before the build: three "
        "header files (`src/core/hw/default_keys.h` and the two `src/core/hle/service/http/ctr-common-1-*.h` "
        "headers; console key and certificate data, not used by this build) and `externals/libressl/`, the bundled "
        "LibreSSL, not used: this build links OpenSSL 3.\n",
        "## Azahar\n",
        f"Azahar 2126.2, commit {commit}, GPLv2 or later, by the Citra and Azahar teams. The GPL texts travel as "
        "`LICENSE` and `COPYING-azahar.txt` in the core zip.\n"])


def testapp_section() -> str:
    text = ["## The test app\n",
            "`testapp.3dsx` is ours, GPLv3-or-later; its source is in this repository at the release tag. It is built "
            "with devkitPro's devkitARM, libctru, citro2d and citro3d (zlib licence; libctru's default icon is in its "
            "SMDH) and newlib's libc and libm (BSD-style notices).\n"]
    found = sorted(Path("/opt/devkitpro").glob("**/COPYING.NEWLIB")) if Path("/opt/devkitpro").is_dir() else []
    if found:
        text.append(fence(found[0].read_text(errors="replace")))
    else:
        text.append("newlib: BSD-style, see COPYING.NEWLIB in newlib's source.\n")
    return "\n".join(text)


def tail_section() -> str:
    return "\n".join([
        "## Not included\n",
        "MoltenVK (Apache-2.0) is fetched by `tools/fetch.sh` from its upstream, never shipped. Azahar's original "
        "tarball also contains the bundled LibreSSL; we removed it with the three headers. No ROMs, keys, "
        "certificates, system files or NAND data are included; the key blob, the default HTTP client certificate and "
        "key loading are removed.\n"])


def build(args: argparse.Namespace) -> str:
    inputs = read_kv(Path(args.inputs))
    keg = inputs.get("openssl_prefix") or die("build.inputs has no openssl_prefix") or ""
    tree, src = Path(args.tree), Path(args.src)
    comps, src_files, ssl = classify(dep_paths(Path(args.deps)), tree.resolve().name, keg)
    libs = link_libs(Path(args.link))
    if not ssl or not OPENSSL_LIBS <= libs:
        die("OpenSSL is not both linked and included")
    pin = read_kv(Path(__file__).resolve().parents[1] / "core" / "PIN")
    parts = [header_section(inputs, pin.get("AZAHAR_COMMIT", "?")), src_section(scan_src(tree, src_files)),
             "## Components\n"]
    for name in sorted(comps - {"open_source_archives"}):
        parts.append(component_section(name, src, libs))
    parts.append(openssl_section(Path(args.openssl), inputs.get("openssl_version", "?")))
    if "open_source_archives" in comps:
        parts.append(archives_section(tree, Path(args.sysarch), Path(args.ofl) if args.ofl else None,
                                      Path(args.unifont) if args.unifont else None))
    parts += [testapp_section(), tail_section()]
    return "\n".join(parts)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for flag in ("link", "deps", "tree", "src", "inputs", "openssl", "sysarch"):
        ap.add_argument("--" + flag, required=True)
    ap.add_argument("--ofl")
    ap.add_argument("--unifont")
    sys.stdout.write(build(ap.parse_args(argv)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
