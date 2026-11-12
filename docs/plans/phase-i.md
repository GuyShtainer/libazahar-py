# Step I: the legal audit and the public release (item laz-420)

Brief for one sonnet builder, **revision 1** (2026-11-13), plus the main loop's own steps (I-pre, the history
rewrite, I2, I3, the push, I5). Phase index: `docs/plans/phase-4.md` (order, ownership, merges, departures P9-P16,
interfaces R1-R30, Guy's items G1-G9). Contract: `docs/PLAN.md:330` ("Phase I") and section 2.7's release paragraph.
Where this brief disagrees with PLAN.md on a goal, PLAN.md wins: stop and report, **except** the approved departures
(P9 and Phase 3's P9b: keys, ClCertA and key loading out, OpenSSL 3; P10 the source asset; P11 NOTICES here; P12 the
pins filled at I2; P13 the draft prerelease; P14 OpenSSL's source asset; P15 the history rewrite; P16 the README
route on our core), which you follow.

You work in `../libazahar-py-i` (branch `step-i`, made at main after Phase 3 merged). "MAIN" is
`/Users/guyshtainer/VSCodeProjects/3ds-toolkit/projects/libazahar-py`. After your step 0's links: "CORE" is
`build-core/azahar_lazpy_libretro.dylib`, "INPUTS" `build-core/build.inputs`, "BUILD" `build-core/build/`, "LINK"
`BUILD/src/citra_libretro/CMakeFiles/citra_libretro.dir/link.txt`, "DEPS" every `*.o.d` under BUILD, "TREE"
`dl/azahar-src/build-src/azahar-unified-source-2126.2/` (the stripped tree the core was built from), "SRC"
`dl/azahar-src/unpacked/azahar-unified-source-2126.2/` (the full reading copy), "TARBALL" `dl/azahar-src/src.tar.xz`,
"OSSL" `dl/openssl-src/openssl-3.6.5.tar.gz` (the main loop downloaded it, I-pre), "KEG" `/opt/homebrew/opt/openssl@3`,
"APP" `build/testapp.3dsx`. All of them are MAIN's files, read only.

**Never commit, never push, never call `gh`, never edit item files, never write in MAIN, never run
`tools/build-core.sh`** (in a worktree it would delete MAIN's build tree through the `dl/` link), **never run anything
from inside a download**: Python that reads TARBALL, SRC, TREE or OSSL runs with `-I`; bsdtar only lists and copies
their members. Read first: the repo's `CLAUDE.md`, `docs/map/rules.md`, phase-4.md (all of it; section 0 is why this
step looks as it does), `~/.claude/git-publishing-preferences.md`, `~/.claude/ip-publishing-policy.md`,
`core/README.md`, `core/PIN`, `tools/build-core.sh`, `tools/fetch.sh`, `tools/untar_checked.py`, `tests/gate_f2.py`
(`keyblob_findings`), `docs/reviews/release-ip-legal.md` (the consult's answer), `~/.claude/python-golden-rules.md`,
`~/.claude/shell-golden-rules.md`.

## 1. Goal and gate

A staged release in `runs/release/v0.1.0/` whose every file meets its licence obligations and carries no key, no
certificate, no private string and no third-party content we may not ship; notices generated from what the core
really links and includes; `fetch.sh` able to fetch our core and test app by sha256. The gate (yours, in I1):

1. `python3 -I tools/release_check.py runs/release/v0.1.0 --skip-pins` prints `PASS` (or the named `SKIP`/`PEND`
   lines of section 3.3) for every check and exits 0; `--plant-red` fails each planted check on its plant.
2. `tools/mkrelease.sh v0.1.0` run twice gives byte-identical core zip, source asset and test app (compare the two
   `SHA256SUMS` minus the build-files line, which embeds HEAD's commit id).
3. Gate 2 of fetch.sh: with the pins temporarily set to the staged files' sha256 in a temp copy of the repo,
   `LAZ_RELEASE_BASE=file://$PWD/runs/release/v0.1.0 LAZPY_ROOT=<temp copy> <temp copy>/tools/fetch.sh --lazpy-core
   --testapp` downloads, verifies and unpacks both and prints the `LAZ_CORE=` line; a second run downloads nothing;
   a copy with one byte flipped is refused, deleted, and the script exits non-zero. Nothing else is fetched (S9).
   `tools/fetch.sh --openssl-src` in your worktree (OSSL seeded through the `dl/openssl-src` link) prints that the
   file is present and verified and downloads nothing.

The main loop's gates after the merges (section 6): I2's `release_check` with the needle file, `docs_check.py`
without `--allow-missing`, the fresh clone of main; I3's audit says **shippable**; then Guy's words (G6, G7) and I5.

## 2. Facts (checked 2026-11-13; phase-4.md section 8 and R1-R30 have the evidence)

- **P9b** (commit 5e95423, Phase 3's step 0; the build started 00:49 in MAIN): patches 0000-0008 (0007 removes the
  default ClCertA, 0008 makes `GetKeysStream()` load nothing); `core/PIN` has `LAZ_CORE_DROP=src/core/hw/default_keys.h
  src/core/hle/service/http/ctr-common-1-cert.h src/core/hle/service/http/ctr-common-1-key.h`, `OPENSSL_VERSION=3.6.5`,
  `OPENSSL_ROOT=/opt/homebrew/opt/openssl@3`; `build-core.sh` deletes the drop list after the unpack and before the
  patches (it dies if an entry is missing from the fresh tree, and if `LAZ_CORE_DROP` is empty), configures with
  `-DENABLE_BUILTIN_KEYBLOB=OFF -DUSE_SYSTEM_OPENSSL=ON -DOPENSSL_ROOT_DIR=<keg> -DOPENSSL_USE_STATIC_LIBS=TRUE
  -ffile-prefix-map=$PWD/=`, dies unless `OPENSSL_SSL_LIBRARY`/`OPENSSL_CRYPTO_LIBRARY` are the keg's `.a` files,
  dies if a `.o.d` names a drop-list basename or `LibreSSL` is in the core's strings, and installs the dylib
  atomically. F2's f1 (`keyblob_findings(build_dir, core, src_root, tree, drop) -> list[str]`, empty = pass) gates it.
- INPUTS lines (R27): `tarball=`, `pin=`, `script=`, `patch <name>=<sha256>` (0000-0008), `drop=`, `openssl=3.6.5
  /opt/homebrew/opt/openssl@3 libssl.a=<sha256> libcrypto.a=<sha256>`, `head=` (5e95423: a pre-rewrite SHA; after G8
  it is translated by `docs/commit-map-g8.tsv`, never compared), `clean=`, `cmake=` (the cmake binary only).
- The version: the core holds `2126.2` and `-lazpy.1` as separate strings (patch 0005 joins them at run time); there
  is no `2126.2-lazpy.1` literal (review 1 B5).
- LINK's static libraries (R4): cryptopp, mcl, dynarmic, enet, faad2, fmt, SPIRV, glslang, boost_iostreams,
  boost_serialization, zstd_seekable, lodepng, sirit, SoundTouch, SPIRV-Tools, SPIRV-Tools-opt, teakra, xxhash, zstd,
  Azahar's `audio_core`, `citra_common`, `citra_core`, `network`, `video_core`, and the keg's `libssl.a` and
  `libcrypto.a`. Review LINK again in I0: it is the P9b build's.
- DEPS name the `externals/` each compile read (boost, spirv-tools, cryptopp, dynarmic, oaknut, glslang, mcl, fmt,
  zstd, libretro-common, spirv-headers, faad2, robin-map under dynarmic, soundtouch, teakra, sirit, enet, xxHash,
  open_source_archives, lodepng, vulkan-headers, library-headers (ffmpeg/include only), microprofile, nihstro, vma,
  dds-ktx, httplib, json), files under TREE's `src/`, the keg's `include/openssl/`, the macOS SDK, and generated files
  under BUILD. After P9b no DEPS path may contain `externals/libressl/`.
- Licence files (head of each, all under SRC `externals/`): boost `boost/LICENSE_1_0.txt` (BSL-1.0); cryptopp
  `cryptopp/LICENSE`; dynarmic `dynarmic/LICENSE.txt`; mcl `dynarmic/externals/mcl/LICENSE`; robin-map
  `dynarmic/externals/robin-map/LICENSE`; oaknut `oaknut/LICENSE`; enet `enet/LICENSE`; **faad2: the grant is in
  `faad2/faad2/README:12-39`** (GPLv2 or later; "Any non-GPL usage ... strictly forbidden" :19-20; the required line
  "Code from FAAD2 is copyright (c) Nero AG, www.nero.com" :22-23), with the GPLv2 text in `faad2/faad2/COPYING`; fmt
  `fmt/LICENSE`; glslang `glslang/LICENSE.txt`; lodepng `lodepng/lodepng/LICENSE`; sirit `sirit/sirit/LICENSE.txt`;
  SoundTouch `soundtouch/COPYING.TXT` (LGPL-2.1); SPIRV-Tools `spirv-tools/LICENSE` (Apache-2.0, no NOTICE);
  spirv-headers `spirv-headers/LICENSE`; teakra `teakra/LICENSE`; vma `vma/LICENSE.txt`; vulkan-headers
  `vulkan-headers/LICENSE.md` (and `LICENSES/`); xxHash `xxHash/LICENSE`; zstd `zstd/LICENSE`; nihstro
  `nihstro/license.txt`; dds-ktx `dds-ktx/LICENSE`; ffmpeg headers `library-headers/ffmpeg/LICENSE.md`;
  libretro-common, json, httplib, microprofile: the licence comment at the top of the header used;
  `open_source_archives/`: **no licence file** (Readme: generated by B3n30/citra_system_archives at 0baa5f57; it
  lists only the font and the bad-word list, while `include/` also holds the Mii data and the country list).
- **OpenSSL 3.6.5** (R30): KEG's `sbom.spdx.json` names the source
  `https://github.com/openssl/openssl/releases/download/openssl-3.6.5/openssl-3.6.5.tar.gz`, sha256
  `a2157c2830efdec3788939b00c9b0638306d3f0bbb76dc4832ee503bb397df98`, the bottle sha256
  `0994a8029175af4578c3b93b3020e58dffa638ca21dc22d862c6bc02fea7e73b`, no patches; `openssl version -a` gives the
  platform, the compiler flags and `OPENSSLDIR`. KEG has `LICENSE.txt` (Apache-2.0) and no NOTICE (Homebrew copies
  `notice` files into kegs, `metafiles.rb:13`), so OSSL most likely has none: check its member list.
- Third-party notices inside Azahar's own `src/` (review 1 S7): `src/common/cityhash.{h,cpp}` (MIT),
  `src/common/bit_field.h`, `vector_math.h` (Tony Wasserka), `src/core/file_sys/plugin_3gx*` and
  `src/core/hle/service/plgldr/plgldr.*` (MIT, The Pixellizer Group), `src/video_core/host_shaders/texture_filtering/*.frag`
  (the shaders are embedded through generated headers, so DEPS name the generated files, not the `.frag` sources).
- Azahar: SRC `license.txt` is the GPLv2 text (no OpenSSL exception); the sources say "GPLv2 or any later version".
  The binary links Apache-2.0 code (SPIRV-Tools, OpenSSL 3), which GPLv2 does not accept, so the binary goes out under
  **GPLv3** (G4, a fact).
- The P9b core is 21,828,992 bytes; `vtool -show-build`: minos 11.0, sdk 26.2, but its libcrypto objects are built
  for macOS 15.0 (linker warning), so it needs macOS 15+ (R31; the release says so). It holds OpenSSL's Homebrew
  directories as strings (R30) and no `/Users/` string. `build/libazhost.dylib` and `build/azhost` are minos 15.0.
- The stock Azahar zip ships the dylib alone; the stock dylib carries the key blob and ClCertA (phase-4.md 0.6).
- `fetch.sh` (R7): helpers `get URL SHA FILE`, `ok`, `verify`, `sha_of`, a pins block at the top, `LAZPY_ROOT`; the
  parser takes one argument (`--force`), `fetch.sh:38-43`.
- No `user.email` in this repo's git config; section 8.2 sets it before the tag.
- `.gitignore` ignores `*.3dsx`, `*.zip`, `*.tar`, `*.tar.xz`, `*.tar.gz`, `*.dylib`, `runs/`, `dl/`, `build-*/`.
- bsdtar 3.5.3 copies members from an archive given as `@file` without extracting; `--exclude`, `--uid`, `--gid`,
  `--uname`, `--gname`. Apple zip 3.0's `-X` drops extra attributes. `git archive` of a commit stores the commit id and
  uses the commit time as every file's mtime (deterministic per commit, different per commit).

## 3. What to build

### 3.1 `tools/mknotices.py` -> `NOTICES.md` (P11; stdlib, `python3 -I`, about 200 lines, functions under 40)

`python3 -I tools/mknotices.py --link LINK --deps BUILD --tree TREE --src SRC --inputs INPUTS --openssl OSSL >
NOTICES.md`. Two tables in the script: (a) components: name -> (its `externals/` folder or `openssl`, its licence file
or the file whose top comment holds the licence, a short SPDX-style name, "linked" or "headers only", extra required
lines); (b) known `src/` notices: path glob -> (holder, short name). The script:

1. reads LINK's `.a` inputs and every DEPS path; normalises `externals/./x` to `externals/x` and
   `dynarmic/externals/<y>` to `<y>`; classifies each path as TREE `externals/<name>` (-> table a), TREE `src/` (-> 2),
   KEG (-> `openssl`), BUILD (generated; skipped), the macOS SDK or `/usr/include` (system; skipped). **Any other path,
   any `externals/libressl` path and any name missing from table (a) exits 1 naming it**, so a new dependency or a
   LibreSSL relapse cannot slip through;
2. scans the TREE `src/` files DEPS name, plus every file under TREE `src/video_core/host_shaders/`, reading the first
   40 lines: Azahar's own header (`Copyright ... Citra Emulator Project` or `Azahar Emulator Project` with the "GPLv2
   or any later version" line) is skipped; any other `Copyright`, `SPDX-License-Identifier` or `Permission is hereby
   granted` line must match table (b), else exit 1; the matching comment block is kept verbatim;
3. writes NOTICES.md, in this order:
   - a header: what the file covers (the core `azahar_lazpy_libretro.dylib` and the test app `testapp.3dsx`; the
     repo's own code is GPLv3, `LICENSE`); "The core binary is distributed under GPLv3 (Azahar's 'or any later
     version' grant permits it; the binary links Apache-2.0 code, which GPLv2 does not accept)";
   - libazahar-py's changes: one line per patch from INPUTS (name, sha256) and "each changed file carries a
     'Modified by libazahar-py' notice (patch 0000)"; the files removed before the build (INPUTS `drop=`);
   - Azahar (GPLv2 or later; the Citra and Azahar teams; commit 219d743a...);
   - "Inside Azahar's tree": each table-(b) file with its notice block verbatim;
   - one section per component in name order: name, folder, how it is used, short name, then the licence text
     **verbatim** in a fenced block (read from SRC, never retyped); faad2's section adds the Nero AG line as a plain
     line; SoundTouch's adds "LGPL-2.1: this release's complete corresponding source of the whole work lets you
     relink"; `openssl`: "OpenSSL 3.6.5 (Homebrew `openssl@3`, statically linked), Apache-2.0", `LICENSE.txt` verbatim
     from OSSL (read with `tarfile`, no extraction), and the top-level `NOTICE` file's text verbatim **if OSSL has
     one** (Apache-2.0 4(d)), else the line "OpenSSL's source tarball has no NOTICE file (checked)";
   - `open_source_archives`: the generator, its commit, the four files and "no licence file in Azahar's tarball";
   - the test app: ours, GPLv3-or-later, source in this repository at the release tag; built with devkitPro's
     devkitARM, libctru, citro2d and citro3d (zlib licence; libctru's default icon is in its SMDH) and newlib's libc and
     libm (BSD-style notices: the licence file devkitARM ships, found with `find /opt/devkitpro -iname 'COPYING*'
     -o -iname 'LICENSE*'`, verbatim; if none is installed, name newlib, "BSD-style, see COPYING.NEWLIB in newlib's
     source" and report it);
   - "Not included": MoltenVK (Apache-2.0) and the stock core are fetched by `tools/fetch.sh` from their upstreams,
     never shipped; Azahar's tarball contains `externals/libressl`, which this build neither compiles nor links; no
     ROMs, keys, certificates, system files or NAND data; the key blob, the default HTTP client certificate and key
     loading are removed (P9b).
   The GPL texts are not pasted (they travel as `LICENSE` and `COPYING-azahar.txt` in the zip). Output is
   deterministic: no dates, sorted sections.

### 3.2 `tools/mkrelease.sh`, the assets, `SOURCE.md`, `core/PIN-nokeys`, `core/OPENSSL.md`, the notes

`tools/mkrelease.sh <tag>` (POSIX sh, `set -eu`, about 120 lines): inputs CORE, INPUTS, APP, TARBALL, OSSL at the
repo-relative paths above, each overridable (`LAZ_REL_CORE`, `LAZ_REL_INPUTS`, `LAZ_REL_APP`, `LAZ_REL_TARBALL`,
`LAZ_REL_OSSL`); it verifies TARBALL against `core/PIN` and OSSL against `core/OPENSSL.md`'s sha256 first (a mismatch
stops), then writes `runs/release/<tag>/` fresh (`rm -rf`, using a staging folder `runs/release/<tag>.stage/`):

| Asset | How |
|---|---|
| `azahar_lazpy_libretro-2126.2-lazpy.1-macos-arm64.zip` | stage `azahar_lazpy_libretro.dylib` (CORE), `NOTICES.md`, `LICENSE`, `COPYING-azahar.txt` (SRC `license.txt`), `SOURCE.md`, `build.inputs` (INPUTS); `touch -t 202601010000` each; `zip -X -9 -q` from inside the stage folder, names sorted |
| `azahar-unified-source-2126.2-lazpy-nokeys.tar.xz` | P10 (a): write `<SRC_TOP>/LIBAZAHAR-PY-REMOVED.txt` in a stage folder (text below, `touch -t 202601010000`), then `tar -c -J -f OUT --uid 0 --gid 0 --uname '' --gname '' -C <stage> <SRC_TOP>/LIBAZAHAR-PY-REMOVED.txt --exclude '<SRC_TOP>/<entry>' (one per drop-list entry) @TARBALL` |
| `openssl-3.6.5.tar.gz` | OSSL, copied byte for byte (P14) |
| `libazahar-py-core-build-<tag>.tar.gz` | `git archive --format=tar.gz --prefix=libazahar-py-core-build/ -o OUT HEAD core tools/build-core.sh tools/untar_checked.py` (committed files only, review 1 S11) |
| `testapp.3dsx` | APP, copied |
| `NOTICES.md`, `SOURCE.md` | also as plain assets |
| `SHA256SUMS` | `shasum -a 256` of every other asset, sorted by name |

`LIBAZAHAR-PY-REMOVED.txt` (N6; fixed text, so the asset is deterministic): "libazahar-py removed these files from
Azahar's azahar-unified-source-2126.2.tar.xz (sha256 <SRC_SHA256>) on 2026-11-13, before building its core: <path>
sha256 <hex> (one line per drop-list entry, hashed from TARBALL's member). They hold Azahar's built-in key data and
its default HTTP client certificate, which this build does not use (patches 0007 and 0008, ENABLE_BUILTIN_KEYBLOB=OFF).
Every other file is unchanged."

`SOURCE.md` (written by mkrelease.sh from INPUTS and fixed text; no timestamps; **no sha256 of the core zip or of the
build-files asset**, which `SHA256SUMS` holds): what the binary is (macOS 15 or later, arm64; Azahar 2126.2, commit 219d743a, our patches with
each sha256 from INPUTS, the build script's sha256, the commit it was built at: INPUTS `head=`, translated through
`docs/commit-map-g8.tsv` when that file exists, and the tag); the Corresponding Source on this release page: (1)
the source asset with its sha256 (Azahar's tarball, URL and sha256, minus the drop list, plus the note member; the
binary was built from exactly this tree plus the patches), (2) `openssl-3.6.5.tar.gz` with its sha256 and OpenSSL's
own URL (the source of the statically linked `libssl.a` and `libcrypto.a`; `core/OPENSSL.md` says how they were
built), (3) the build-files asset (patches, pins, options, `OPENSSL.md`, the build script), (4) this repository at the
tag; the build: the `cmake` lines quoted from `tools/build-core.sh` at HEAD (whose sha256 equals INPUTS `script=`,
checked) and the compiler identification lines from `build-core/configure.log` (review 1 S3: real flags, never a
template); "Azahar's tarball also contains `externals/libressl`; this build does not compile or link it
(`USE_SYSTEM_OPENSSL=ON`)"; how to rebuild: Homebrew `openssl@3` at the pinned version (or OpenSSL built from (2) as
`core/OPENSSL.md` says), then `LAZ_CORE_PIN=core/PIN-nokeys tools/build-core.sh --build`.

`core/PIN-nokeys` (new, committed): `core/PIN`'s keys with `SRC_URL` = our release URL of the source asset,
`SRC_SHA256`/`SRC_SIZE` of it, `SRC_FILE=dl/azahar-src/src-nokeys.tar.xz`, `SRC_TOP` unchanged, `OPENSSL_*` copied,
and `LAZ_CORE_DROP=LIBAZAHAR-PY-REMOVED.txt` (today's `build-core.sh` refuses an empty drop list and requires each
entry to exist; the note member exists in the stripped tree and nothing reads it), with a comment line naming the
original tarball and why the drop entry is the note. The source asset is deterministic, so its sha256 is known in I1.

`core/OPENSSL.md` (new, about 30 lines): version 3.6.5; the upstream URL and sha256 (from KEG's SBOM, and equal to
OSSL; the main loop also checked OpenSSL's published `.sha256` when it fetched, I-pre); "Homebrew `openssl@3` bottle,
sha256 <bottle>, built <SBOM builtDate>, no patches (the SBOM lists none)"; `openssl version -a`'s platform,
compiler and `OPENSSLDIR` lines verbatim; the formula's configure arguments, from `HOMEBREW_NO_AUTO_UPDATE=1 brew cat
openssl@3` run with a 30-second limit (if it fails or needs the network, write "see Homebrew's formula
`Formula/o/openssl@3.rb` in homebrew-core" and report it: phase-4.md Q7); the two `.a` sha256 from INPUTS; how to
build the same libraries from OSSL (`./Configure darwin64-arm64-cc <those arguments>`, `make`) and point
`LAZ_OPENSSL_ROOT` at them; "the release attaches this exact tarball".

`docs/release-notes/v0.1.0.md` (about 30 lines): what it is (one line), "early prerelease", a link to `STATUS.md`; the
assets, one line each (no sha256: `SHA256SUMS` holds them); "Requires macOS 15 or later on Apple silicon (the
statically linked OpenSSL is built for macOS 15)"; "The core binary is GPLv3; its complete corresponding
source is on this page: the Azahar source asset, the OpenSSL source tarball, the build files, and this repository at
the tag"; "Homebrew only: no ROMs, keys, certificates or system files; our core is built without Azahar's built-in
key data and default HTTP client certificate, and it loads no keys"; the non-affiliation line; "Install: see README".
**No admission text of any kind** (policy rule 5), no speed numbers.

### 3.3 `tools/release_check.py <dir> [--skip-pins] [--pre-push] [--plant-red]` (stdlib, `python3 -I`, about 260 lines)

Each check prints `PASS <name>`, `FAIL <name>: <reason>`, `SKIP <name>: <why>` or `PEND <name>: <what>` (PEND only in
I1, for paths not committed yet); any FAIL exits 1; under `--pre-push` every SKIP and PEND is a FAIL. The core is
read from inside the zip (extracted to a temp file). File inputs are overridable for the plants (`--nm-output`,
`--otool-output`, `--link`, `--inputs`, `--fetch`, `--pyproject`).

1. **assets**: exactly 3.2's file set; `SHA256SUMS` matches every file.
2. **keyblob**: `gate_f2.keyblob_findings(BUILD, <core from the zip>, SRC, TREE, <core/PIN's LAZ_CORE_DROP split>)`
   (imported from `tests/`, review 1 B1, Phase 3 review 2 S5) returns `[]`; each finding is printed. Plus
   `ENABLE_BUILTIN_KEYBLOB:BOOL=OFF` in `BUILD/CMakeCache.txt`.
3. **exports**: `nm -gU` lists exactly 25 `_retro_*` plus `_lazpy_read_memory`, `_lazpy_write_memory`,
   `_lazpy_movie_play`.
4. **version**: the core's strings hold `2126.2` and `-lazpy.1` (separately, B5); INPUTS' `patch 0005-lazpy-version.patch`
   hash equals the checkout's file.
5. **linkage**: `otool -L` shows only `/System/Library/...` and `/usr/lib/...` plus its own `@rpath` id; no
   `libMoltenVK`, `libvulkan`, `libssl`, `libcrypto`; no `MVKInstance`/`MVKDevice` string.
6. **openssl** (G3): LINK names the keg's `libssl.a` and `libcrypto.a` (the paths INPUTS' `openssl=` line gives) and
   no path containing `libressl`; `BUILD/CMakeCache.txt` has `USE_SYSTEM_OPENSSL:BOOL=ON`; no DEPS file names
   `externals/libressl/`; the core's strings hold `OpenSSL 3.6.5` and no `LibreSSL` or `libressl`; the version in
   INPUTS, that string, OSSL's file name and `core/OPENSSL.md` agree; OSSL's sha256 equals `core/OPENSSL.md`'s and the
   SBOM's; the staged OpenSSL asset equals OSSL. KEG's `.a` sha256 are compared with INPUTS and a difference is a
   `FAIL` only under `--pre-push` (risk 13: the release offers 3.6.5 either way, but a changed keg means
   `brew pin` was lost and nobody can recheck the link).
7. **inputs**: INPUTS exists; `clean=yes`; its `pin=`, `script=`, every `patch` hash and `drop=` equal the
   checkout's `core/PIN`, `tools/build-core.sh`, `core/patches/*` and `LAZ_CORE_DROP` (review 1 S2), with no patch
   missing or extra; `head=` is printed, never compared (G8 changes it).
8. **private**: in the core's strings, the zip's text files, the build-files asset, `testapp.3dsx`, `NOTICES.md`,
   `SOURCE.md` and the release notes (not the two upstream tarballs, whose sha256 equal upstream's): FAIL on `/Users/`,
   on any `@gmail.com` address, on any address ending `.local`, on a MAC address form, and on an IPv4 literal in
   10/8, 172.16/12, 192.168/16 or 169.254/16; other IPv4 literals (Azahar's `8.8.8.8`) and other email addresses are
   printed as `NOTE` lines for the audit (B7). OpenSSL's compiled-in Homebrew paths (`OPENSSLDIR`
   `/opt/homebrew/etc/openssl@3`, `ENGINESDIR` and `MODULESDIR` under `/opt/homebrew/Cellar/openssl@3/3.6.5/lib`) are
   expected: printed as `NOTE expected` lines, never a FAIL; any other `/opt/homebrew/` string is a plain `NOTE`. **Needles** (B2): if `LAZ_PRIVATE_NEEDLES` names a readable file, each
   of its lines (the text left of `==>` when a line has one) is searched case-insensitively in the same files; a hit
   prints only the file name and the needle's line number, never the needle. No variable: `SKIP` (FAIL under
   `--pre-push`). **Never put a needle, or the needle file's path, in this script, its output, or any tracked file.**
9. **notices**: `mknotices.py` re-run to a temp file equals the working tree's `NOTICES.md` byte for byte (B6), and
   the zip's `NOTICES.md` equals it; under `--pre-push` the working tree's equals HEAD's.
10. **source** (P10 (a)): list the source asset's and TARBALL's members side by side (`tarfile`, no extraction): the
    same names in the same order except the drop-list entries (absent) and the note member (present, first); for every
    other member the same type, mode, size, mtime, link target and content sha256 (uid, gid and names not compared);
    the note member's text equals the expected text; `core/PIN-nokeys`'s `SRC_SHA256` and `SRC_SIZE` equal the asset's.
11. **build-files**: the asset equals a fresh `git archive` of HEAD with the same arguments; a listed path that is
    in the working tree but not in HEAD (in I1: `core/PIN-nokeys`, `core/OPENSSL.md`) is `PEND`.
12. **pins**: fetch.sh's `--lazpy-core` and `--testapp` sha256 pins equal the staged zip's and `testapp.3dsx`'s; the
    URLs use the tag and `https://github.com/GuyShtainer/libazahar-py/releases/download/`. `--skip-pins` makes this
    `SKIP` (I1: the main loop fills the pins at I2, P12).
13. **repo**: `git ls-files` has no path matching rules.md 1's list (`.dylib .zip .tar .tar.xz .tar.gz .3ds .cci .cxi
    .cia .3dsx .gba .nds .sav`, `aes_keys.txt`, `seeddb.bin`, `dl/`, `vendor/`, `runs/`, `build*/`, `sdmc/`, `nand/`,
    `sysdata/`); `git log --all --diff-filter=A --name-only --format=` has none either; every commit's author and
    committer email is the no-reply address; with the needle file: `git grep -I -c -i -F -f <needles> $(git rev-list
    --all) --`, `git log --all --format=%B` and every tag message hold no needle (print counts only); no
    `refs/replace/` and no ref other than `refs/heads/*` and `refs/tags/*`.
14. **versions**: `pyproject.toml`'s `version` and `python/libazahar/__init__.py`'s `__version__` both equal the tag
    without its `v` (S10).
15. `--pre-push` adds: `git status --porcelain` empty; `git config user.email` is the no-reply address and `user.name`
    is `Guy Shtainer`; every tag's tagger email is the no-reply address; `python3 -I tools/docs_check.py` passes; the
    release notes contain none of `bundles`, `includes ©`, `ripped`, and no speed token (`\b\d+(\.\d+)?\s?x\b`,
    `\bfps\b`); "keys" only inside "no keys" or "key data".
17. **macos** (R31; listed after 16 but run before it): `vtool -show-build` of the core (from the zip) and of
    `build/libazhost.dylib` and `build/azhost` in the checkout: platform macOS, arm64 only; the host binaries' minos is
    15.0; the core's is printed (11.0 on the v0.1.0 core, a known header mismatch that STATUS states) and a minos above
    15.0 is a FAIL; the release notes and `SOURCE.md` (and, under `--pre-push`, README.md) hold "macOS 15 or later".
16. `--plant-red`: in a temp copy of the staged folder, plant one fault per check and pass only if each check fails on
    its plant: a stray asset (1); a ClCertA window appended to a core copy (2, through `keyblob_findings` on the copy);
    an extra name in a fake `nm` output (3); a core copy without `-lazpy.1` (4); a fake `otool` line with `libssl`
    (5); a LINK copy with an `externals/libressl/` path (6); an INPUTS copy with one patch hash changed (7); `/Users/x`
    in a SOURCE.md copy (8); a NOTICES section dropped (9); one member's content changed in a re-packed copy of the
    source asset (10); a changed pin in a fetch.sh copy (12); a pyproject copy at `0.1.0.dev0` (14); a SOURCE.md copy without "macOS 15 or later" (17). Not planted: 11,
    13, 15 (they read git state); say so.

### 3.4 `tools/fetch.sh`: part flags, `--lazpy-core`, `--testapp` (P12, P16)

The parser loops over its arguments (S9). Part flags: `--stock-core`, `--moltenvk`, `--headers` (the libretro and
Vulkan headers), `--lazpy-core`, `--testapp`, `--openssl-src` (OpenSSL's own release tarball from R30's upstream URL,
pinned by R30's sha256, into `dl/openssl-src/openssl-3.6.5.tar.gz`: for anyone rebuilding the core, P14); plus
`--force`. **No part flag = `--stock-core --moltenvk --headers`**
(what fetch.sh does today, so the tests and docs that call it keep working). A part flag fetches only its own files.
A second pins block below the first holds the release tag (`v0.1.0`), the base URL
(`https://github.com/GuyShtainer/libazahar-py/releases/download/$TAG`) and two sha256 lines with placeholders
(`LAZPY_CORE_SHA=TBD-at-I2`, `TESTAPP_SHA=TBD-at-I2`); a `TBD` pin makes its flag die with "pins are filled at
release time". `LAZ_RELEASE_BASE` overrides the base URL (the clone at I2 and your gate 3). `--lazpy-core`: `get` the
zip into `dl/lazpy-core/`, `verify` it, `unzip -o` only `azahar_lazpy_libretro.dylib`, `NOTICES.md` and `SOURCE.md`
into `dl/lazpy-core/`, print `LAZ_CORE=<root>/dl/lazpy-core/azahar_lazpy_libretro.dylib`. `--testapp`: `get` into
`dl/testapp/testapp.3dsx`, copy to `build/testapp.3dsx` (`mkdir -p build`). Keep the helpers and the "download only if
missing or wrong; a mismatch deletes and exits" rule; no new dependency. The usage line lists every flag; the comment
at the top says what each fetches. curl sets no quarantine attribute, so the dylib loads.

## 4. Files (you create or edit only these)

| Path | Role |
|---|---|
| `tools/mknotices.py`, `NOTICES.md` (generated, committed) | 3.1 |
| `tools/mkrelease.sh`, `core/PIN-nokeys`, `core/OPENSSL.md` | 3.2 |
| `tools/release_check.py` | 3.3 |
| `tools/fetch.sh` | 3.4 only |
| `docs/release-notes/v0.1.0.md` | 3.2 |
| `core/README.md` | the "Licenses" section only: the drop list and patches 0007/0008 (removed key data, certificate and key loading); OpenSSL 3 static (`core/OPENSSL.md`); the release's source assets (P10, P14); the binary is GPLv3 (G4); `PIN-nokeys`; remove "ships with the unchanged source tarball" |
| `pyproject.toml`, `python/libazahar/__init__.py` | the version line in each: `0.1.0` |

Not yours: `README.md`, `STATUS.md`, `docs/USING.md`, `docs/HOST-API.md`, `examples/`, `tools/docs_check.py`,
`tools/clone_check.sh` (step H), `tools/build-core.sh`, `core/PIN`, `core/patches/`, `tests/` (you import
`tests/gate_f2.py`, never edit it), every other code file, `docs/map/*`, item files, the handoff. The map lines go in
your report (the main loop commits them with your files, phase-4.md N8): `docs/map/tools.md` (mknotices,
mkrelease, release_check), `docs/map/runners.md` (section 10), `docs/map/code.md` (`docs/release-notes/`,
`core/PIN-nokeys`, `core/OPENSSL.md`, `NOTICES.md`).

## 5. Steps, with a checkpoint after each (save files as you go; never commit)

**Before you are launched (main loop, not you):** I-pre (the ip-legal consult, 9.1) is answered in
`docs/reviews/release-ip-legal.md`; OSSL is downloaded and verified in MAIN (section 6, I-pre); F2 gated the P9b build;
the launch message says which defaults hold (G2 (a); whether the consult holds the core asset back).

0. **I0 (about 0.1 h).** Seed: `mkdir -p dl build-core && for d in azahar moltenvk libretro-headers vulkan-headers
   azahar-src openssl-src; do [ -e MAIN/dl/$d ] && ln -s MAIN/dl/$d dl/$d; done`, `for f in azahar_lazpy_libretro.dylib
   build.inputs build configure.log; do ln -s MAIN/build-core/$f build-core/$f; done`, `cp -R MAIN/vendor .`,
   `mkdir -p build && cp MAIN/build/testapp.3dsx build/` (a stand-in for I1; I2 rebuilds it). Check phase-4.md rows
   R1-R7, R9-R11, R23, R26-R30 against the files: `python3 -I -c "import sys; sys.path.insert(0, 'tests'); import
   gate_f2; ..."` calling `keyblob_findings` on CORE (**a non-empty list stops the step: report "P9b not gated"**;
   nothing else here is valid on that binary); INPUTS against the checkout (check 7's rule); LINK's list; the DEPS
   component list (print it) and the absence of `externals/libressl`; `nm -gU CORE | grep -c`; `otool -L CORE`;
   `strings -a CORE | grep -c -e /Users/ -e LibreSSL` (both 0); `strings -a CORE | grep 'OpenSSL 3'`; `tar -tzf OSSL |
   grep -i -E '^openssl-3\.6\.5/(NOTICE|LICENSE)'` (record whether a NOTICE exists); `shasum -a 256 KEG/lib/libssl.a
   KEG/lib/libcrypto.a` against INPUTS. Checkpoint: the rows table with what you found, `runs/i/rows.md`.
1. **I1 (about 0.4 h).** In order: 3.1 (run it; read `NOTICES.md` once end to end), `core/OPENSSL.md`, the
   `LIBAZAHAR-PY-REMOVED.txt` text and `mkrelease.sh` (stage), `core/PIN-nokeys` (from the staged source asset), 3.4,
   then re-stage, 3.3, the release notes, `core/README.md`, the two version lines. Run gates 1-3. Long commands (the
   xz pack, about 1-3 min) run in the foreground under the 10-minute limit; anything longer runs with
   `run_in_background`, an rc file from a `trap ... EXIT` and a bounded Monitor wait. Checkpoint: gates 1-3 quoted;
   the asset list with sizes and sha256; **the exact list of paths for the main loop to `git add`**, with the map
   lines. **End the run with the report "I1 done"**.
2. **I4 (only when the as-built review, I2 or the audit finds faults; the main loop resumes you with them).** Fix
   exactly the findings; re-stage; gate 1; report "I4 done" with the changed paths and the new sha256 values.
3. Stop every waiter and background task you started (TaskStop) before each hand-back.

## 6. The main loop's steps (not the builder's)

- **I-pre (now; about 0.1 h with the agent).** Dispatch `ip-legal` with 9.1; save its answer verbatim to
  `docs/reviews/release-ip-legal.md`. Download OSSL: `mkdir -p dl/openssl-src && curl -fsSL -o
  dl/openssl-src/openssl-3.6.5.tar.gz <URL from R30>` and `curl -fsSL <URL>.sha256` (OpenSSL publishes one beside
  each tarball); both must equal R30's sha256 (else delete and stop); the URL and sha256 are recorded in R30 and,
  later, `core/OPENSSL.md` (rules.md 2). `brew pin openssl@3` (risk 13).
- **G8, the history rewrite** (section 8.1): as soon as the P9b build ends and before Phase 3's worktrees are made
  (recommended), else after both Phase 4 merges and before I2.
- **I2 (after both H and I merge to main and their worktrees are removed; about 0.15 h).** In MAIN:
  1. `git status --porcelain` empty; `git worktree list` shows MAIN only.
  2. The test app from the tag's source (S12): the README's build block, emitted by `python3 -I tools/docs_check.py
     --emit-steps README.md --block build`, run under `env -i HOME="$HOME" PATH=/usr/bin:/bin:/usr/sbin:/sbin
     LANG=en_US.UTF-8 sh -eux` (it sets `DEVKITPRO`, `DEVKITARM` and PATH itself, B3).
  3. `tools/mkrelease.sh v0.1.0`; read the zip's and `testapp.3dsx`'s sha256; write them into fetch.sh's two pin
     lines; commit `tools/fetch.sh` alone ("fetch.sh: v0.1.0 release pins"); `tools/mkrelease.sh v0.1.0` again (the
     build-files asset now names the new HEAD; the zip and the test app must keep their sha256: compare).
  4. `LAZ_PRIVATE_NEEDLES=<the file> python3 -I tools/release_check.py runs/release/v0.1.0`; `python3 -I
     tools/docs_check.py`.
  5. The fresh clone (S8): `sh tools/clone_check.sh --repo "$PWD" --branch main --out runs/clone-i2 --release-base
     "file://$PWD/runs/release/v0.1.0"`, started with `run_in_background` and an rc file from a `trap ... EXIT`;
     wait with Monitor on the rc file (bounded 30 min). It must end `clone ok` (the README steps, the quickstart on our
     core, the build block, the fast pytest). The log is I2's Evidence.
  A failure resumes the builder that owns the failing file (or a fresh sonnet with its brief).
- **I3 (the audit):** dispatch `release-legal-audit` with 9.2; save its report verbatim to
  `docs/reviews/release-legal-audit-v0.1.0.md`; BLOCKERs go to I4, then re-stage (I2 steps 3-5) and a re-audit of
  only the changed items. SHOULD items: decided with Guy. Commit the report. If a fix lands after the audit, I2's
  steps 3-5 run again before the push.
- **The push (G5-G7):** section 8.2, only on Guy's word.
- **I5 (after Guy publishes; about 0.05 h):** in a new folder under MAIN's `runs/`: `gh release download v0.1.0 -R
  GuyShtainer/libazahar-py -D assets && (cd assets && shasum -a 256 -c SHA256SUMS)`; `sh tools/clone_check.sh --repo
  https://github.com/GuyShtainer/libazahar-py --branch main --out runs/clone-i5` (real URLs, no `--release-base`);
  then in that clone `.venv/bin/python examples/memory_watch.py` with the `LAZ_CORE` line `fetch.sh` printed: prints
  `memory_watch ok`. The release URL and these lines are item 420's Evidence. Then delete the pre-rewrite bundle
  (8.1 step 4).

## 7. Machine-sharing rules

No emulator in I0, I1 or I4 (the checks read files). Never a timed run. No network: gate 3's `file://` fetch is the
only download-like action. No `gh`, no `git push`, no tag. Never write in MAIN (your staged folder is your worktree's
`runs/release/`). Never kill a process you did not start. Folders under `runs/i*` and `runs/release/` (ignored).

## 8. The history rewrite and the push (the main loop's)

### 8.1 The history rewrite (G8, P15)

Why: one plan line named the local part of Guy's personal address (phase-4.md 0.5). The rewrite replaces it in every
blob of history; HEAD's tree does not change (the line is already gone).

1. **Preconditions.** The P9b build has ended (`build-core/build.exit` exists). No agent is writing in MAIN (check the
   handoff's "Running now"; plan writers and reviewers write in MAIN's `docs/`). `git status --porcelain
   --untracked-files=no` is empty in MAIN (filter-repo ends with a reset of the main worktree; untracked and ignored
   files such as `dl/`, `build-core/`, `runs/` stay). For every other worktree: either it is removed (its `git status
   --porcelain` empty, its branch merged) or `git merge-base --is-ancestor 15d0323 <its branch>` is false, so its
   commits keep their SHAs (today: `step-c` and `step-d` do not contain 15d0323). Phase 3's worktrees are made after
   the rewrite, or the rewrite waits until they are merged and removed.
2. **The tool.** `git filter-repo --version` (2.47.0 at `/opt/homebrew/bin/git-filter-repo`). If it is missing:
   `brew install git-filter-repo`. If that is impossible, the fallback is `git filter-branch -f --tree-filter '<a
   script outside the repo that rewrites docs/plans/phase-i.md from the replacement file>' -- --all`, slower but a
   hundred commits take seconds; the same checks before and after.
3. **The replacement file.** The main loop makes it at run time, mode 600, in a private folder outside the repo. Its
   path is kept in the main loop's session and its private memory only, **never in a tracked file, a commit message,
   the handoff, an item or a report**. Lines `literal==>[redacted address]`: the full address first, then its local
   part. The literals are extracted by a command from Guy's `~/.claude/git-publishing-preferences.md` (the address is
   written there), never typed into any file. The same file is `release_check`'s needle file
   (`LAZ_PRIVATE_NEEDLES`).
4. **Before.** Save `git rev-parse HEAD HEAD^{tree}`, `git rev-list --all --count`, `git for-each-ref` and the
   identity list (`git log --all --format='%ae %ce' | sort -u`) to `runs/g8/before.txt` (ignored). Scan, printing
   counts only: per commit `git grep -I -c -i -F -f <needles only> <commit> --`; `git log --all --format=%B | grep -c
   -i -F -f <needles only>`; tag messages. Expected (2026-11-13 00:55): 6 commits from 15d0323 to 8a16f9e, one path,
   `docs/plans/phase-i.md`, 0 messages, 0 at HEAD, no tags. Any other hit: list the paths (not the text) and extend
   the plan before rewriting. Backup: `git bundle create <the private folder>/pre-rewrite.bundle --all` and `git bundle
   verify` (it holds the old text: never inside the repo; deleted after I5).
5. **Rewrite.** In MAIN: `git filter-repo --force --replace-text <file> --replace-message <file>` (`--force` because
   MAIN is not a fresh clone; the default `--replace-refs update-no-add` adds no `refs/replace/`). It rewrites every
   ref; only `main` changes (15d0323 and the commits after it). It expires reflogs and repacks, so the old objects
   leave MAIN's store; `.git/filter-repo/commit-map` lists old and new SHAs.
6. **After.** The same scan: 0 everywhere. `git rev-parse HEAD^{tree}` equals the saved tree; `git rev-list --all
   --count` equals the saved count; the identity list is unchanged; `git for-each-ref refs/replace` is empty; `git
   fsck` is clean; `step-c`, `step-d` (or whatever branches remain) have their old SHAs and `git -C <worktree>
   status --porcelain` is unchanged.
7. **The commit map.** From `.git/filter-repo/commit-map`, write `docs/commit-map-g8.tsv` (old short SHA, new short
   SHA, subject) for the rewritten commits only, and one line in `docs/map/README.md` ("SHAs older than the rewrite in
   plans, reviews, items, `hours.tsv` and `build-core/build.inputs`: `docs/commit-map-g8.tsv`"). Old SHAs in text are
   not edited. Commit both with exact paths.
8. **Re-run the checks.** `python3 -I tools/status_check.py --strict-handoff`, `tools/map_check.py`, `tools/mkprogress.py`
   (republish only inside /progress), `make check`. If Phase 4 is already at I2 or later: I2's steps 3-5, and the audit
   (I3) runs after the rewrite, never before.
9. **Outside this repo.** Gen3D's or the toolkit's notes may cite libazahar-py SHAs: they go stale; the map answers
   them. Tell the 3ds-toolkit main loop (review 1 B2): plan files written by the same sessions elsewhere may hold the
   same kind of line; each repo checks its own history before its first push.

### 8.2 The push and the release (only on Guy's word)

```
cd /Users/guyshtainer/VSCodeProjects/3ds-toolkit/projects/libazahar-py
git config user.name "Guy Shtainer"
git config user.email "293649481+GuyShtainer@users.noreply.github.com"
LAZ_PRIVATE_NEEDLES=<the file> python3 -I tools/release_check.py runs/release/v0.1.0 --pre-push   # all PASS
gh auth status                                  # must say GuyShtainer, not Guy-Shtainer (clear the old token if so)
gh repo view GuyShtainer/libazahar-py >/dev/null 2>&1 || \
  gh repo create GuyShtainer/libazahar-py --public --description "Headless, scriptable Azahar (3DS libretro core) for testing homebrew"   # G5: only if Guy said we may create it
git remote add origin https://github.com/GuyShtainer/libazahar-py.git
git ls-remote origin                            # must work (empty) before anything is pushed: catches a PAT 403 (G5)
git push -u origin main                         # main only: never --all or --mirror; step-* branches stay local
git tag -a v0.1.0 -m "libazahar-py v0.1.0"
git for-each-ref refs/tags --format='%(refname:short) %(taggeremail)'   # the no-reply address
git push origin v0.1.0
gh release create v0.1.0 -R GuyShtainer/libazahar-py --verify-tag --draft --prerelease \
  --title "libazahar-py v0.1.0 (prerelease)" --notes-file docs/release-notes/v0.1.0.md runs/release/v0.1.0/*
gh release view v0.1.0 -R GuyShtainer/libazahar-py --json isDraft,isPrerelease,assets --jq '.isDraft, .isPrerelease, [.assets[].name]'
```
The tag is made at the HEAD the build-files asset was archived from (`release_check --pre-push` check 11 proves it).
Then Guy opens the draft, checks it and publishes it (G7), or says "publish" and the main loop runs `gh release edit
v0.1.0 -R GuyShtainer/libazahar-py --draft=false`. If the consult held the core asset back, the `gh release create`
line lists every asset except the core zip, the Azahar source asset and the OpenSSL tarball, and STATUS says how to
build the core.

## 9. The two legal briefs (the main loop pastes these)

### 9.1 I-pre: the `ip-legal` consult (now; it needs no build)

"libazahar-py (public GPLv3, `GuyShtainer/libazahar-py`, not pushed yet) will release a patched build of Azahar's
3DS libretro core (Azahar is GPLv2-or-later) for macOS arm64. Read `docs/plans/phase-4.md` sections 0, 5 and 8 and
`~/.claude/ip-publishing-policy.md`. Answer each, with the policy rule or legal ground, and say which need counsel:
(1) Our core is built with Azahar's built-in console key blob off, with Nintendo's embedded default ClCertA (the
ctr-common-1 HTTPS client certificate and its private key) removed by a patch, and with key loading removed (it reads
no `aes_keys.txt`, so it holds and accepts no console keys and cannot run an encrypted title). Azahar's AES and NCCH
code is still compiled in, inert. Is that core within policy rule 7 for a public release, or counsel-worthy? (2) The
GPL source for that binary: (a) re-host Azahar's tarball minus the three removed headers, with a note member naming
them (our default), (b) point to Azahar's own release asset (GPLv3 6(d)), or (c) re-host the unchanged tarball (holds
the key blob and ClCertA). Which, and why? The re-hosted tarball still holds Azahar's AES/NCCH source and an unbuilt
LibreSSL: any problem? (3) The core statically links OpenSSL 3.6.5 (Apache-2.0) instead of Azahar's bundled LibreSSL
(whose OpenSSL/SSLeay licences are GPL-incompatible on their texts). Confirm Apache-2.0 into a GPLv3 binary is fine,
and that re-hosting OpenSSL's unchanged release tarball plus its licence in NOTICES.md (and a NOTICE file's text if
it has one) meets Apache-2.0 section 4. (4) The binary goes out under GPLv3 (Azahar's 'or later'; SPIRV-Tools and
OpenSSL are Apache-2.0); faad2 (GPLv2 or later, 'any non-GPL usage forbidden', a required Nero AG line) is inside:
anything beyond carrying its line? (5) The core compiles in 'open source' 3DS system archives (shared font, Mii data,
country list, bad-word list) generated by github.com/B3n30/citra_system_archives: what must we verify before shipping
them in a binary? (6) The name 'libazahar-py' (Azahar is the upstream project's name; Guy approved the name subject to
this check). (7) Our `tools/fetch.sh` and test suite download Azahar's own stock libretro core from Azahar's GitHub
release (never re-hosted by us); that binary embeds the key blob and ClCertA. Is scripting that download within
rule 7? Our README's default route will use our core instead (phase-4.md P16). (8) A tracked research file names the
commercial game used for a local speed measurement and its product code (`docs/research/spike-2-real-scene.md:22,
57`): keep, reword, or remove before the push? Write the answer to `docs/reviews/release-ip-legal.md` and add any
durable finding to the learn skill's `ip-law-and-publishing.md`."

### 9.2 I3: the `release-legal-audit` brief

"Audit libazahar-py for its first push and its first GitHub release, v0.1.0, before anything is public. Repo: MAIN
(on `main`, no remote yet; its history was rewritten on <date> to remove a private address: `docs/commit-map-g8.tsv`).
Staged assets: `MAIN/runs/release/v0.1.0/` (the core zip, the Azahar source asset, `openssl-3.6.5.tar.gz`, the
build-files asset, `testapp.3dsx`, `NOTICES.md`, `SOURCE.md`, `SHA256SUMS`). Release notes:
`docs/release-notes/v0.1.0.md`. Read `~/.claude/ip-publishing-policy.md`, `docs/map/rules.md`, `docs/plans/phase-4.md`
(sections 0, 5, 8) and `docs/reviews/release-ip-legal.md` first. The machine checks already passed: re-run `python3
-I tools/release_check.py runs/release/v0.1.0` and read its output (its needle checks were run by the main loop with a
private file; their PASS lines are in <I2's log>). Audit and grade (BLOCKER / SHOULD / INFO): (1) the tree and the full
history (`git log --all -p`) for ROMs, BIOS, saves, keys, certificates, system data, ripped assets, commercial-game
screenshots, decomp code, secrets, private data (grade the tracked claude.ai artifact links, the `/Users/...` paths,
and the research file's game name and product code, `docs/research/spike-2-real-scene.md:22, 57`); (2) the core
binary: no key blob, no ClCertA (Azahar's `ctr-common-1-cert.h`/`-key.h` arrays), no key loading, no MoltenVK, no
LibreSSL, no private strings (OpenSSL's compiled-in Homebrew directories, `OPENSSLDIR` `/opt/homebrew/etc/openssl@3`
and `ENGINESDIR`/`MODULESDIR` under `/opt/homebrew/Cellar/openssl@3/3.6.5/lib`, are expected, not leaks); the compiled-in system archives' provenance; (3) the Azahar source asset: complete
corresponding source for the binary (the binary was built from this stripped tree plus the patches; SOURCE.md and the
note member), nothing in it we may not re-host; `default_keys.h` carries a GPL header, which does not make console
keys shippable; (4) the OpenSSL tarball and NOTICES' OpenSSL section against Apache-2.0 section 4; (5) the test app:
our own code and glyphs, no Nintendo assets; (6) NOTICES.md: every linked component's licence text, the `src/`
notices, faad2's Nero line, the GPL texts present in the zip; (7) every claim in README.md, STATUS.md, the release
notes and SOURCE.md: no overclaim, the non-affiliation lines, no admission text, nominative names only, no key or
decryption instructions; the README's route uses our core (the stock core is optional; grade fetch.sh's stock
download per the consult's answer 7); (8) the name. Say **shippable** or **not shippable** for each of: the repo, its
history, the core zip, the Azahar source asset, the OpenSSL asset, the build-files asset, the test app, the notices
and the docs' claims, with exact remediations."

## 10. The builder's report (I1 and I4)

Gates 1-3 as printed (with `--plant-red`); `runs/i/rows.md`; the asset table (name, size, sha256); the LINK and DEPS
component lists and any table row you had to add (components and `src/` notices); whether OSSL has a NOTICE; whether
`brew cat` worked; line counts per file and the longest function; the paths to `git add` with their map lines; runners
lines for `docs/map/runners.md`:
```
tools/mkrelease.sh v0.1.0                                    # stage the release in runs/release/v0.1.0/
python3 -I tools/release_check.py runs/release/v0.1.0        # step I's machine checks (--pre-push before a push)
python3 -I tools/mknotices.py --link <link.txt> --deps build-core/build --tree <build-src tree> --src <unpacked tree> --inputs build-core/build.inputs --openssl dl/openssl-src/openssl-3.6.5.tar.gz > NOTICES.md
tools/fetch.sh --moltenvk --headers --lazpy-core --testapp   # the README route: our core and the test app from the release
```
lines for `docs/map/tools.md`; and a final **"Lessons and notes"** block for item 420.

## 11. Hours (agent wall time)

Builder 0.6 h (I0 0.1, I1 0.4, I4 0.1 if needed) and the commit 0.05 h: **0.65 h**; the as-built review is the joint
one in phase-4.md (0.2 h for H and I). The main loop's I-pre (0.1 with the consult), G8 (0.1), I2 (0.15), I3 (0.1)
and I5 (0.05) are phase-4.md's 0.5 h. Against PLAN.md's 0.6 h for I: the key blob and ClCertA checks, OpenSSL's
notice and source, the `src/` notices and the needles add about 0.11 h; dropping `release_pack.py` and the configure
check saves about 0.11 h. The xz pack and the audit's reading are machine time; Guy's steps are his.

## 12. Review checklist (the joint opus as-built review)

1. `release_check` calls `gate_f2.keyblob_findings` (no second set of windows), reads the core inside the zip, and
   its plant for check 2 fires through that function.
2. NOTICES.md is generated; licence texts verbatim from SRC and OSSL; every LINK and DEPS path classified; an unknown
   component, an unknown path, an `externals/libressl` path or an unknown `src/` notice exits 1; faad2's Nero line;
   OpenSSL's Apache text and its NOTICE status; the G4 sentence.
3. The source asset differs from TARBALL by exactly the drop list and the note member, member by member; two packs give
   the same bytes; `PIN-nokeys` matches it and names the note as its drop entry.
4. The OpenSSL asset equals upstream's tarball (sha256 from the SBOM and `.sha256`), `core/OPENSSL.md` is complete, and
   check 6 proves LibreSSL absent from the link line, DEPS and the strings.
5. Check 17 and the docs say macOS 15 or later; OpenSSL's Homebrew paths are expected NOTEs, not FAILs.
6. SOURCE.md and the release notes are honest and complete (where every piece of source is, how to rebuild, the real
   cmake lines), with no admission text, no speed numbers, no key instructions, no core-zip or build-asset hash.
7. `fetch.sh`'s flags keep its helpers and its "download only if missing or wrong" rule; no flag means today's set; a
   `TBD` pin dies; gate 3's corrupted copy is refused and deleted.
8. `release_check` covers rules.md 1 over the tree and the history, the identities, the needles without ever printing
   one, and `--pre-push`'s identity, tagger, clean-tree and docs checks.
9. Nothing committed, pushed or sent to GitHub; nothing written in MAIN; nothing run from inside a download;
   `build-core.sh` never run; no item file edited; no needle or needle-file path anywhere in the diff.
