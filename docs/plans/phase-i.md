# Step I: the legal audit and the public release (item laz-420)

Brief for one sonnet builder, revision 0 (2026-11-12), plus the main loop's own steps (I2, I3, the push, I5).
Phase index: `docs/plans/phase-4.md` (order, ownership, merges, departures P9-P13, interfaces R1-R26, Guy's items
G1-G7). Contract: `docs/PLAN.md:330` ("Phase I") and section 2.7's release paragraph. Where this brief disagrees with
PLAN.md on a goal, PLAN.md wins: stop and report, **except** the approved departures (P9 key blob off, P10 the
source asset, P11 NOTICES here, P12 the fetch pin before the push, P13 the draft prerelease), which you follow.

You work in `../libazahar-py-i` (branch `step-i`, made at main after Phase 3 merged). "MAIN" is
`/Users/guyshtainer/VSCodeProjects/3ds-toolkit/projects/libazahar-py`. "CORE" is
`MAIN/build-core/azahar_lazpy_libretro.dylib`, "LINK" is
`MAIN/build-core/build/src/citra_libretro/CMakeFiles/citra_libretro.dir/link.txt`, "DEPS" is every `*.o.d` under
`MAIN/build-core/build/`, "TARBALL" is `MAIN/dl/azahar-src/src.tar.xz` (verified against `core/PIN`), "SRC" is
`MAIN/dl/azahar-src/unpacked/azahar-unified-source-2126.2/`, "APP" is `MAIN/build/testapp.3dsx`. All of them read
only. **Never commit, never push, never call `gh`, never edit item files, never write in MAIN, never run anything
from inside a download** (rules.md 2: Python that reads TARBALL or SRC runs with `-I`; nothing in them is executed;
the one exception is `tools/build-core.sh --configure-only` in check 3.3(10), which is our build script running
Azahar's CMake on the pinned source, rules.md 2's allowed case). Read first: the repo's `CLAUDE.md`,
`docs/map/rules.md`, phase-4.md (all of it: section 0 is why this step looks as it does),
`~/.claude/git-publishing-preferences.md`, `~/.claude/ip-publishing-policy.md`, `core/README.md`, `core/PIN`,
`tools/build-core.sh`, `tools/fetch.sh`, `tools/untar_checked.py`, `docs/reviews/release-ip-legal.md` (the consult's
answer, I-pre), `~/.claude/python-golden-rules.md`, `~/.claude/shell-golden-rules.md`.

## 1. Goal and gate

A staged release in `runs/release/v0.1.0/` whose every file meets its licence obligations and carries no key, no
private string and no third-party content we may not ship; the notices generated from what the core really links;
`fetch.sh` able to fetch our core and test app by sha256; and an audit that says shippable. The gate:

1. `python3 -I tools/release_check.py runs/release/v0.1.0` prints `PASS` for every check of section 3.3 and exits 0;
   `--plant-red` fails each planted fault (3.3, last item).
2. `LAZ_RELEASE_BASE=file://$PWD/runs/release/v0.1.0 LAZPY_ROOT=<a temp copy of the repo> tools/fetch.sh
   --lazpy-core --testapp` downloads, verifies and unpacks both; a second run downloads nothing; a corrupted copy (one
   byte flipped) is refused, deleted and the script exits non-zero.
3. `python3 -I tools/docs_check.py` (step H's, **without** `--allow-missing`, once both steps are on main: the main
   loop's I2) passes, so `NOTICES.md` is linked and present.
4. (Main loop, I3) `release-legal-audit` says **shippable** for: the repo tree, its full history, the core zip, the
   source asset, the build-files asset, `testapp.3dsx`, `NOTICES.md`, the release notes and the README's claims.
5. `git ls-files` shows no forbidden file (rules.md 1); `git log --all` has only the no-reply identity; the repo's
   own `git config user.email` is the no-reply address before any tag is made (3.3, check 13).
6. **Guy says push** (G6), then publishes the draft (G7). I5's post-release check passes.

## 2. Facts (checked 2026-11-12; phase-4.md section 8 has the evidence and line numbers)

- **The key blob** (phase-4.md section 0): `ENABLE_BUILTIN_KEYBLOB` defaults ON and puts `default_keys_enc[]`
  (SRC `src/core/hw/default_keys.h`) into the core; its first 16 bytes are `[removed]
  CD 8E 11`. With the option OFF, `key.cpp` does not include the header and `citra_core` does not list it (SRC
  src/core/hw/aes/key.cpp:21-23; src/core/CMakeLists.txt:501-503), and the header `#error`s if included.
- Today's DEPS list `default_keys.h` in exactly one file, `src/core/CMakeFiles/citra_core.dir/hw/aes/key.cpp.o.d`
  (because today's build has the option ON). After P9's rebuild, no DEPS file may name it. DEPS also show which
  `externals/` each compile read: boost, libressl, spirv-tools, cryptopp, dynarmic, oaknut, glslang, mcl, fmt, zstd,
  libretro-common, spirv-headers, faad2, robin-map (under dynarmic), soundtouch, teakra, sirit, enet, xxHash,
  open_source_archives, lodepng, vulkan-headers, library-headers (ffmpeg/include only), microprofile, nihstro, vma,
  dds-ktx, httplib, json.
- LINK's static libraries (R4): cryptopp, mcl, dynarmic, enet, faad2, fmt, SPIRV and glslang, boost_iostreams and
  boost_serialization, LibreSSL `libcrypto.a` and `libssl.a`, zstd_seekable, lodepng, sirit, SoundTouch, SPIRV-Tools
  and SPIRV-Tools-opt, teakra, xxhash, zstd, plus Azahar's `audio_core`, `citra_common`, `citra_core`, `network`,
  `video_core`.
- Licences (head of each file): boost `boost/LICENSE_1_0.txt` (BSL-1.0); cryptopp `cryptopp/LICENSE`; dynarmic
  `dynarmic/LICENSE.txt` (0BSD-style); mcl `dynarmic/externals/mcl/LICENSE`; robin-map
  `dynarmic/externals/robin-map/LICENSE`; oaknut `oaknut/LICENSE`; enet `enet/LICENSE`; faad2 `faad2/faad2/COPYING`
  (GPLv2 or later); fmt `fmt/LICENSE`; glslang `glslang/LICENSE.txt` (several parts); lodepng `lodepng/lodepng/LICENSE`
  (zlib); sirit `sirit/sirit/LICENSE.txt`; SoundTouch `soundtouch/COPYING.TXT` (LGPL-2.1); SPIRV-Tools
  `spirv-tools/LICENSE` (Apache-2.0, no NOTICE file); spirv-headers `spirv-headers/LICENSE`; teakra `teakra/LICENSE`;
  vma `vma/LICENSE.txt`; vulkan-headers `vulkan-headers/LICENSE.md` (and `LICENSES/`); xxHash `xxHash/LICENSE`; zstd
  `zstd/LICENSE`; LibreSSL `libressl/COPYING` (ISC for new code; the OpenSSL License and the SSLeay licence for the
  OpenSSL code); nihstro `nihstro/license.txt`; dds-ktx `dds-ktx/LICENSE`; ffmpeg headers
  `library-headers/ffmpeg/LICENSE.md`; libretro-common: the licence comment at the top of the headers used; json,
  httplib, microprofile: the licence comment at the top of `json.hpp`, `httplib.h`, `microprofile/microprofile.h`;
  `open_source_archives/`: **no licence file** (Readme: generated by B3n30/citra_system_archives at 0baa5f57):
  NOTICES records that, and the audit decides (phase-4.md risk 10). All paths under SRC `externals/`.
- Azahar itself: SRC `license.txt` is the GPLv2 text; the sources say "GPLv2 or any later version". The binary links
  Apache-2.0 SPIRV-Tools, which GPLv3 accepts and GPLv2 does not, so the binary is distributed under **GPLv3** (G4;
  if Guy has not answered, write it as the default and say so in the report).
- The stock Azahar zip ships the dylib alone, no licence file. We do better: the licences travel inside our zip.
- CORE today: 19,195,472 bytes, 461 `/Users/guyshtainer/...` strings (P9's prefix map removes them), no email.
- `fetch.sh`: `get URL SHA FILE` and `verify FILE SHA` helpers, a pins block at the top, `--force`, `LAZPY_ROOT`
  (tools/fetch.sh:1-60).
- The repo has **no** `user.email` in any git config (checked 2026-11-12: `git config --show-origin --get-all
  user.email` prints nothing), so a `git tag -a` made as is would take a machine-local address. Section 8 sets the
  repo's identity first, as Guy's preferences say.
- `.gitignore` ignores `*.3dsx`, `*.zip`, `*.tar*`, `*.dylib`, `runs/`: every staged asset is ignored; nothing in
  this step is committed except the tools, NOTICES, the notes, the pins and the docs lines in section 4.
- `gh` 2.95.0 has `release create --draft --prerelease --verify-tag --notes-file` (the main loop's commands only).

## 3. What to build

### 3.1 `tools/mknotices.py` -> `NOTICES.md` (P11; stdlib, `python3 -I`, about 120 lines)

`python3 -I tools/mknotices.py --link LINK --deps <build dir> --src SRC > NOTICES.md`. One table in the script maps
each component name to (its `externals/` folder, its licence file or the file whose top comment holds the licence,
an SPDX-style short name, "linked" or "headers only"). The script:
1. reads LINK's `.a` inputs and DEPS's `externals/<name>` prefixes (normalise `externals/./x` to `externals/x`, and
   `dynarmic/externals/<y>` to `<y>`); every name found must be in the table, else exit 1 naming it (so a new
   dependency after a core update cannot slip through);
2. writes `NOTICES.md`: a header (what this file covers: the core binary `azahar_lazpy_libretro.dylib` and the test
   app `testapp.3dsx`; the repo's own code is GPLv3, `LICENSE`); Azahar (GPLv2 or later, the Citra and Azahar
   teams, the commit, "distributed here under GPLv3, which its licence permits"; the "Modified by libazahar-py"
   patch list); then one section per component in name order: name, folder, how it is used, short name, then the
   licence text **verbatim** in a fenced block (read from SRC, never retyped); LibreSSL's section also carries the two
   acknowledgments its licence asks for, as plain lines ("This product includes software developed by the OpenSSL
   Project for use in the OpenSSL Toolkit (http://www.openssl.org/)" and "This product includes cryptographic
   software written by Eric Young (eay@cryptsoft.com)"); the `open_source_archives` section states the generator and
   commit and "no licence file in Azahar's tarball";
3. the test app section: ours, GPLv3-or-later, source in this repository at the release tag; built with devkitPro's
   libctru, citro2d and citro3d (zlib licence; credit, no notice required) and devkitARM;
4. a "Not included" section: MoltenVK (Apache-2.0) and the stock core are fetched by `tools/fetch.sh` from their
   upstreams, never shipped; no ROMs, keys, system files or NAND data; the key blob is not built in (P9).

The GPL texts are not pasted into NOTICES (they are `LICENSE`, GPLv3, and Azahar's `license.txt`, GPLv2, shipped as
files in the zip, 3.2).

### 3.2 `tools/release_pack.py` and `tools/mkrelease.sh`

`tools/release_pack.py` (stdlib, `python3 -I`, about 120 lines), two subcommands:
- `source TARBALL OUT.tar.xz --drop src/core/hw/default_keys.h` (P10 option (a)): stream TARBALL's members in their
  original order, refuse any absolute name, `..` part or a symlink pointing outside the tree (reuse
  `tools/untar_checked.py`'s check by import if it exposes one, else the same rule), skip exactly the dropped path(s)
  (exit 1 if a dropped path is not found), copy each kept member with its original `TarInfo` (name, mode, mtime,
  type, link target; `uid`/`gid` 0, `uname`/`gname` empty) into `tarfile.open(OUT, "w:xz", preset=9)`. Never
  extracts. Prints `kept=<n> dropped=<list> sha256=<hex>`. Two runs give the same bytes (checked in 3.3).
- `zip OUT.zip FILE...`: a deterministic zip (`zipfile`, fixed `date_time` 2026-01-01 00:00:00, sorted names, mode
  bits kept, `ZIP_DEFLATED` level 9).

`tools/mkrelease.sh <tag>` (POSIX sh, `set -eu`, about 80 lines; inputs CORE, APP, TARBALL from MAIN-relative paths
by default, each overridable by env `LAZ_REL_CORE`, `LAZ_REL_APP`, `LAZ_REL_TARBALL`), writes `runs/release/<tag>/`
fresh each time:

| Asset | Contents |
|---|---|
| `azahar_lazpy_libretro-2126.2-lazpy.1-macos-arm64.zip` | `azahar_lazpy_libretro.dylib` (CORE, copied), `NOTICES.md`, `LICENSE` (GPLv3, this repo's), `COPYING-azahar.txt` (SRC `license.txt`), `SOURCE.md` |
| `azahar-unified-source-2126.2-lazpy-nokeys.tar.xz` | option (a) only: `release_pack.py source` of TARBALL |
| `libazahar-py-core-build-<tag>.tar.gz` | `core/` (PIN, `PIN-nokeys`, patches, options, README), `tools/build-core.sh`, `tools/untar_checked.py`, `SOURCE.md` (made with `tar` from the repo's committed files; `--uid 0 --gid 0`) |
| `testapp.3dsx` | APP, copied |
| `NOTICES.md`, `SOURCE.md` | also as plain assets, readable on the release page |
| `SHA256SUMS` | `shasum -a 256` of every other asset, sorted by name |

`SOURCE.md` (written by mkrelease.sh from a template in the script): what the binary is (Azahar 2126.2, commit
219d743a, our patches 0000-0006 with each patch's sha256); the Corresponding Source on this release page: the
source asset (with its sha256), the build-files asset, and this repository at the tag; the build command
(`tools/build-core.sh --build`, the cmake flags it passes, including `-DENABLE_BUILTIN_KEYBLOB=OFF` and the prefix
map), the toolchain (`clang --version` first line, `sw_vers -productVersion`, `MACOSX_DEPLOYMENT_TARGET=11.0`); for
option (a): "this is Azahar's own `azahar-unified-source-2126.2.tar.xz` (URL, sha256 85c8b56f...) with one file
removed, `src/core/hw/default_keys.h` (sha256 <x>), which the build does not use with the key blob off; every other
member is byte-identical"; how to rebuild from it (`LAZ_CORE_PIN=core/PIN-nokeys tools/build-core.sh --build`). For
option (b): the same, with "the unchanged tarball is at Azahar's release page (URL)" instead of our asset.

`core/PIN-nokeys` (new, committed): the `core/PIN` keys with `SRC_URL` = our release URL of the source asset,
`SRC_SHA256`/`SRC_SIZE` of it, `SRC_FILE=dl/azahar-src/src-nokeys.tar.xz`, `SRC_TOP` unchanged, plus a comment line
naming the original. (Option (b): not made.)

`docs/release-notes/v0.1.0.md` (about 30 lines): what it is (one line), "early prerelease" and a link to
`STATUS.md`; the assets, one line each (no sha256 here: `SHA256SUMS` holds them, so the notes do not churn); "The
core binary is GPLv3; its complete corresponding source is on this page: ..." (the source assets and the tag);
"Homebrew only: no ROMs, keys, system files; our core is built without Azahar's built-in key blob"; the
non-affiliation line; "Install: see README". **No admission text of any kind** (policy rule 5), no speed numbers.

### 3.3 `tools/release_check.py <dir> [--pre-push] [--plant-red]` (stdlib, `python3 -I`, about 200 lines)

Each check prints `PASS <name>` or `FAIL <name>: <reason>`; any FAIL exits 1. The core is read from inside the zip.

1. **assets**: exactly the 3.2 file set, no other file; `SHA256SUMS` matches every file.
2. **keyblob**: the core holds none of 8 windows of 16 bytes taken from SRC's `default_keys_enc[]` (start, end, 6
   evenly spaced; parsed from the header text with `-I` Python); `MAIN/build-core/build/CMakeCache.txt` has
   `ENABLE_BUILTIN_KEYBLOB:BOOL=OFF`; no DEPS file names `default_keys.h`.
3. **exports**: `nm -gU` of the core lists exactly 25 `_retro_*` plus `_lazpy_read_memory`, `_lazpy_write_memory`,
   `_lazpy_movie_play` and nothing else.
4. **version**: the core's strings contain `2126.2-lazpy.1` (and the patch-0005 version string the host checks).
5. **linkage**: `otool -L` shows only `/System/Library/...` and `/usr/lib/...` plus its own `@rpath` id; no
   `libMoltenVK`, no `libvulkan`; `strings` holds no `MoltenVK` implementation marker (`MVKInstance`, `MVKDevice`).
6. **private**: no string in the core, the zip's text files, the build asset or `testapp.3dsx` matches `/Users/`,
   personal email forms, `.local` email forms, an IPv4 other than 0.0.0.0/127.x, a MAC address, or any entry of the
   untracked privacy denylist outside the repo (never name its entries in a tracked file; phase-4 review 1 B2). (The prefix map
   of P9 makes the core pass; a FAIL here on the core means P9's rebuild was not done.)
7. **notices**: `mknotices.py` re-run to a temp file is byte-equal to the committed `NOTICES.md` (so the notices
   match the binary's real link line and DEPS); `NOTICES.md` in the zip equals the repo's.
8. **source** (option (a)): unpack nothing; walk the source asset's and TARBALL's member lists side by side: the same
   names in the same order except the dropped file; for each kept member the same type, mode, size, link target and
   sha256 of the content; `release_pack.py source` run twice gives the same sha256; `core/PIN-nokeys`'s sha256 and
   size equal the asset's. (Option (b): SOURCE.md names the Azahar URL and sha256 equal to `core/PIN`.)
9. **build asset**: holds exactly the listed files, each byte-equal to the repo's committed copy at HEAD.
10. **configure**: in a temp `LAZPY_ROOT` holding a copy of `core/`, `tools/`, and the source asset at
    `PIN-nokeys`'s `SRC_FILE`, `LAZ_CORE_PIN=core/PIN-nokeys nice -n 10 tools/build-core.sh --configure-only`
    succeeds (proves the stripped tree configures with the key blob off; with it on, CMake would miss the header).
    About 1-3 min machine time; `--skip-configure` skips it when re-checking after a docs-only fix.
11. **pins**: `tools/fetch.sh`'s `--lazpy-core` and `--testapp` sha256 pins equal the staged zip's and
    `testapp.3dsx`'s; the URLs use tag `<tag>` and `https://github.com/GuyShtainer/libazahar-py/releases/download/`.
12. **repo**: `git ls-files` has no path matching rules.md 1's list (`.dylib .zip .tar .tar.xz .tar.gz .3ds .cci .cxi
    .cia .3dsx .gba .nds .sav`, `aes_keys.txt`, `seeddb.bin`, `dl/`, `vendor/`, `runs/`, `build*/`, `sdmc/`, `nand/`,
    `sysdata/`); `git log --all --diff-filter=A --name-only --format=` has none either (history); every commit's
    author and committer email is the no-reply address.
13. `--pre-push` adds: `git status --porcelain` empty; `git config user.email` is the no-reply address and
    `user.name` is `Guy Shtainer`; every tag's tagger email (`git for-each-ref refs/tags --format='%(taggeremail)'`)
    is the no-reply address; `docs_check.py` passes; the release notes contain none of `bundles`, `includes ©`,
    `ripped`, `keys` (except in "no keys" / "key blob" phrases), and no speed number.
14. `--plant-red`: in a temp copy of the staged folder, plant one fault per check (append the blob's first window to
    the core copy, add an extra export name to a fake `nm` output (the check takes `--nm-output FILE` for this),
    drop a NOTICES section, flip a byte in the source asset, add a stray asset, put `/Users/x` in SOURCE.md, change a
    pin), and pass only if each check fails on its plant. Checks 10, 12 and 13 are not planted (they read git and
    run CMake); say so.

### 3.4 `tools/fetch.sh --lazpy-core` and `--testapp` (P12)

A second pins block below the first (release tag, base URL, the two sha256 values filled in by you from the staged
files), `LAZ_RELEASE_BASE` overriding the base URL (for gate 2's `file://`). `--lazpy-core`: `get` the zip into
`dl/lazpy-core/`, `verify` it again, unzip only `azahar_lazpy_libretro.dylib` and `NOTICES.md` into
`dl/lazpy-core/`; print the `LAZ_CORE=` line to use. `--testapp`: `get` into `dl/testapp/testapp.3dsx`, then copy
to `build/testapp.3dsx` (where `make testapp` puts it). Without a flag, fetch.sh does what it does today; the flags
may be combined with each other and with `--force`. Keep the existing helpers; no new dependency. The usage comment
at the top gains two lines. curl does not set the quarantine attribute, so the dylib loads.

## 4. Files (you create or edit only these)

| Path | Role |
|---|---|
| `tools/mknotices.py`, `NOTICES.md` (generated, committed) | 3.1 |
| `tools/release_pack.py`, `tools/mkrelease.sh`, `core/PIN-nokeys` | 3.2 |
| `tools/release_check.py` | 3.3 |
| `tools/fetch.sh` | 3.4 only |
| `docs/release-notes/v0.1.0.md` | 3.2 |
| `core/README.md` | the "Licenses" section only: the key blob is off (P9); the release's source assets (P10); the binary is GPLv3 (G4); one line on `PIN-nokeys` |
| `pyproject.toml` | `version = "0.1.0"` only |

Not yours: `README.md`, `STATUS.md`, `docs/USING.md`, `docs/HOST-API.md`, `examples/`, `tools/docs_check.py` (step
H), `tools/build-core.sh` (the main loop applies P9 before launch, phase-4.md section 3), `core/patches/`,
`core/PIN`, every code file, `docs/map/*`, item files, the handoff. Lines the main loop must add to
`docs/map/tools.md`, `docs/map/runners.md` and `docs/map/code.md` (`docs/release-notes/`) go in your report.

## 5. Steps, with a checkpoint after each (save files as you go; never commit)

**Before you are launched (main loop, not you):** I-pre, the `ip-legal` consult (section 9.1), is answered and saved
to `docs/reviews/release-ip-legal.md`; Guy has answered G2 (the source option) and G4 (GPLv3), or the launch message
says which defaults hold; P9 is applied and the core rebuilt and gated by F2. The launch message names the option
(a/b) and whether G3 (LibreSSL) holds the core asset back.

0. **I0 (about 0.1 h).** Seed: `mkdir -p dl && for d in azahar moltenvk libretro-headers vulkan-headers azahar-src;
   do [ -e MAIN/dl/$d ] && ln -s MAIN/dl/$d dl/$d; done`, `cp -R MAIN/vendor .`. Check phase-4.md rows R1-R7, R9,
   R10, R23, R26 against the files: the key blob windows absent from CORE and `ENABLE_BUILTIN_KEYBLOB:BOOL=OFF` in
   the cache (**if either fails, stop and report "P9 not applied": nothing else in this step is valid on that
   binary**); LINK's list; DEPS's externals list (print it); `nm -gU CORE | grep -c`; `otool -L CORE`; `strings -a
   CORE | grep -c /Users/`. Checkpoint: the rows table with what you found, `runs/i/rows.md`.
1. **I1 (about 0.4 h).** In order: 3.1 (run it; read `NOTICES.md` once end to end), 3.2's `release_pack.py` (run
   `source` twice, compare sha256), `mkrelease.sh v0.1.0` (stage), 3.4 (fill the pins from the staged files), then
   `core/PIN-nokeys`, `SOURCE.md` via a re-stage, 3.3, the release notes, `core/README.md`, `pyproject.toml`. Run
   gate 1 (with `--plant-red`) and gate 2. Long commands (the xz pack, about 1-3 min; the configure check) run in the
   foreground under the 10-minute limit; if one would pass it, run it with `run_in_background`, an rc file from a
   `trap ... EXIT` and a bounded Monitor wait. Checkpoint: gate 1 and 2 output quoted; the asset list with sizes and
   sha256; **the exact list of paths for the main loop to `git add`**. **End the run with the report "I1 done"**.
2. **I4 (only if the audit or a review finds BLOCKERs; the main loop resumes you with the findings).** Fix exactly
   the findings; re-stage; gate 1; report "I4 done" with the changed paths and the new sha256 values (the pins in
   `fetch.sh` change with them).
3. Stop every waiter and background task you started (TaskStop) before each hand-back.

## 6. The main loop's steps (not the builder's)

- **I2 (after both H and I merge to main; about 0.05 h):** in MAIN, `tools/mkrelease.sh v0.1.0`; `python3 -I
  tools/release_check.py runs/release/v0.1.0`; `python3 -I tools/docs_check.py`. The staged files must have the
  sha256 values `fetch.sh` pins (the inputs are the same MAIN files the builder staged from, and the packing is
  deterministic); a mismatch resumes I.
- **I3 (the audit):** dispatch `release-legal-audit` with section 9.2's brief; save its report verbatim to
  `docs/reviews/release-legal-audit-v0.1.0.md`; BLOCKERs go to I4, then a re-audit of only the changed items.
  SHOULD items: the main loop decides with Guy. Commit the report.
- **The push (G5-G7):** section 8, only on Guy's word.
- **I5 (after Guy publishes; about 0.05 h):** in a new empty folder under MAIN's `runs/`: `gh release download
  v0.1.0 -R GuyShtainer/libazahar-py -D assets && (cd assets && shasum -a 256 -c SHA256SUMS)`; `git clone
  https://github.com/GuyShtainer/libazahar-py repo`; in the clone, the README's steps (or `docs_check.py
  --emit-steps`), then `tools/fetch.sh --lazpy-core --testapp` (real URLs), then `LAZ_CORE=<the printed path>
  .venv/bin/python examples/memory_watch.py` prints `memory_watch ok`. The release URL and these lines are item 420's
  Evidence.

## 7. Machine-sharing rules

No emulator in I0, I1 or I4 (the checks read files; the configure check runs CMake only, nice'd). Never a timed run.
No network: the only download-like action is gate 2's `file://` fetch. No `gh`, no `git push`, no tag. Never write
in MAIN (the staged folder is your worktree's `runs/release/`; I2's is MAIN's, the main loop's). Never kill a process
you did not start. Folders under `runs/i*` and `runs/release/` (ignored).

## 8. The push and the release (the main loop's exact commands, only on Guy's word)

```
cd /Users/guyshtainer/VSCodeProjects/3ds-toolkit/projects/libazahar-py
git config user.name "Guy Shtainer"
git config user.email "293649481+GuyShtainer@users.noreply.github.com"
python3 -I tools/release_check.py runs/release/v0.1.0 --pre-push --skip-configure   # all PASS
gh auth status                                  # must say GuyShtainer, not Guy-Shtainer (clear the old token if so)
gh repo view GuyShtainer/libazahar-py >/dev/null 2>&1 || \
  gh repo create GuyShtainer/libazahar-py --public --description "Headless, scriptable Azahar (3DS libretro core) for testing homebrew"   # G5: only if Guy said we may create it
git remote add origin https://github.com/GuyShtainer/libazahar-py.git
git push -u origin main
git tag -a v0.1.0 -m "libazahar-py v0.1.0"
git for-each-ref refs/tags --format='%(refname:short) %(taggeremail)'   # the no-reply address
git push origin v0.1.0
gh release create v0.1.0 -R GuyShtainer/libazahar-py --verify-tag --draft --prerelease \
  --title "libazahar-py v0.1.0 (prerelease)" --notes-file docs/release-notes/v0.1.0.md runs/release/v0.1.0/*
gh release view v0.1.0 -R GuyShtainer/libazahar-py --json isDraft,isPrerelease,assets --jq '.isDraft, .isPrerelease, [.assets[].name]'
```
Then Guy opens the draft, checks it and publishes it (G7), or says "publish" and the main loop runs `gh release edit
v0.1.0 -R GuyShtainer/libazahar-py --draft=false`. The repo is pushed before the release so its source archives at
the tag exist when the binary appears. If the audit held the core asset back (G3), the `gh release create` line
lists every asset except the core zip and the source asset, and STATUS.md says how to build the core.

## 9. The two legal briefs (the main loop pastes these)

### 9.1 I-pre: the `ip-legal` consult (run as early as possible; it needs no build)

"libazahar-py (public GPLv3, `GuyShtainer/libazahar-py`, not pushed yet) will release a patched build of Azahar's
3DS libretro core (Azahar is GPLv2-or-later) for macOS arm64. Read `docs/plans/phase-4.md` sections 0, 5 and 8 and
`~/.claude/ip-publishing-policy.md`. Answer each, with the policy rule or legal ground, and say which need counsel:
(1) Azahar's default build embeds an encrypted (zero-key) blob of 3DS console AES keys; we build with
`ENABLE_BUILTIN_KEYBLOB=OFF`. Is a build with the blob off, but with Azahar's AES/NCCH key-handling code still
present (inert without user-supplied keys), within policy rule 7 for a public release, or counsel-worthy? (2) The
GPL source for that binary: (a) re-host Azahar's tarball minus `default_keys.h`, (b) point to Azahar's own release
asset (GPLv3 §6(d)), or (c) re-host the unchanged tarball. Which, and why? (3) The core statically links LibreSSL
(OpenSSL and SSLeay licences, advertising clause) into GPL code, as Azahar's own releases do. May we redistribute it,
with the acknowledgments in NOTICES.md? (4) The binary also links Apache-2.0 SPIRV-Tools: distribute the binary under
GPLv3 (Azahar's 'or later')? (5) The core compiles in 'open source' 3DS system archives (shared font, Mii data, country
list, bad-word list) generated by github.com/B3n30/citra_system_archives: what must we verify before shipping them
in a binary? (6) The name 'libazahar-py' (Azahar is the upstream project's name; Guy approved the name subject to
this check). Write the answer to `docs/reviews/release-ip-legal.md` and add any durable finding to the learn skill's
`ip-law-and-publishing.md`."

### 9.2 I3: the `release-legal-audit` brief

"Audit libazahar-py for its first push and its first GitHub release, v0.1.0, before anything is public. Repo: MAIN
(on `main`, no remote yet). Staged assets: `MAIN/runs/release/v0.1.0/` (the core zip, the source asset if option
(a), the build-files asset, `testapp.3dsx`, `NOTICES.md`, `SOURCE.md`, `SHA256SUMS`). Release notes:
`docs/release-notes/v0.1.0.md`. Read `~/.claude/ip-publishing-policy.md`, `docs/map/rules.md`,
`docs/plans/phase-4.md` (sections 0, 5, 8) and `docs/reviews/release-ip-legal.md` first. The machine checks already
passed (`python3 -I tools/release_check.py runs/release/v0.1.0`: re-run it and read its output). Audit and grade
(BLOCKER / SHOULD / INFO): (1) the tree and the full history (`git log --all -p`) for ROMs, BIOS, saves, keys, system
data, ripped assets, commercial-game screenshots, decomp code, secrets, private data (the tracked claude.ai artifact
links and `/Users/...` paths: grade them); (2) the core binary: no key blob, no MoltenVK, no private strings; the
compiled-in system archives' provenance; LibreSSL's notices; (3) the source asset: complete corresponding source for
the binary (with SOURCE.md's proof), and nothing in it we may not re-host; (4) the test app: our own code and glyphs,
no Nintendo assets; (5) NOTICES.md: every linked component's licence text and the acknowledgments its licence
requires; the GPL texts present; (6) every claim in README.md, STATUS.md, the release notes and SOURCE.md: no
overclaim, the non-affiliation lines, no admission text, nominative names only, no key or decryption instructions;
(7) the name. Say **shippable** or **not shippable** for each of: the repo, its history, the core zip, the source
asset, the build-files asset, the test app, the notices and the docs' claims, with exact remediations."

## 10. The builder's report (I1 and I4)

Gates 1 and 2 as printed (with `--plant-red`); `runs/i/rows.md`; the asset table (name, size, sha256); the DEPS and
LINK component lists and any component the table had to add; the configure check's wall time; line counts per file
and the longest function; the paths to `git add`; runners lines for `docs/map/runners.md`:
```
tools/mkrelease.sh v0.1.0                                    # stage the release in runs/release/v0.1.0/
python3 -I tools/release_check.py runs/release/v0.1.0        # step I's machine checks
python3 -I tools/mknotices.py --link <link.txt> --deps build-core/build --src <unpacked tree> > NOTICES.md
tools/fetch.sh --lazpy-core --testapp                        # our core and the test app from the release
```
lines for `docs/map/tools.md`; and a final **"Lessons and notes"** block for item 420.

## 11. Hours (agent wall time)

Builder 0.6 h (I0 0.1, I1 0.4, I4 0.1 if needed), the opus as-built review 0.15 h, the commit 0.05 h: **0.8 h**;
plus the main loop's I2, I3 and I5, about 0.2 h with the audit agent's run. Against PLAN.md's 0.6 h, which did not
count the key blob (P9's check and P10's source asset, about 0.15 h) or generating the notices from the binary's real
inputs (0.1 h). The configure check, the xz pack and the audit's reading are machine time; Guy's steps are his.

## 12. Review checklist (the opus as-built review)

1. The key blob check uses windows parsed from SRC (not a hard-coded 16 bytes only), reads the core inside the zip,
   and also checks the cache line and DEPS; `--plant-red` proves it fires.
2. NOTICES.md is generated, its licence texts are verbatim from SRC, every LINK and DEPS component maps to a section,
   an unknown component exits 1; LibreSSL's two acknowledgments present; the GPL statement as Guy decided.
3. The source asset (option (a)) differs from TARBALL by exactly the dropped file, member by member; packing is
   deterministic; `PIN-nokeys` matches it; the configure check passed on it.
4. SOURCE.md and the release notes are honest and complete (where every piece of source is, how to rebuild), with no
   admission text, no speed numbers, no key instructions.
5. `fetch.sh`'s new flags keep its helpers and its "download only if missing or wrong" rule; the pins equal the staged
   files; gate 2's corrupted copy is refused and deleted.
6. `release_check.py` covers rules.md 1 over the tree and the history and the identity checks; `--pre-push` checks
   the repo's own `user.email` and the tag's tagger.
7. Nothing committed, pushed or sent to GitHub; nothing written in MAIN; nothing run from inside a download except
   the allowed configure; no item file edited.
