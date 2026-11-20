# Step I: the legal audit and the public release (item laz-420)

Brief for one sonnet builder, **revision 2 (final)** (2026-11-13), plus the main loop's own steps (the downloads,
spike 2's rewording, G8b, I2, I3, the push, I5). It takes in review 2 (B1, B2, B4, S1-S4, S8, S9, N1, N5, N6) and the
ip-legal consult (docs/reviews/release-ip-legal.md, sections 1-10). Phase index: `docs/plans/phase-4.md` (order,
ownership, merges, departures P9-P19, interfaces R1-R35, the questions for Guy in section 7). Contract:
`docs/PLAN.md:330` ("Phase I") and section 2.7's release paragraph. Where this brief disagrees with PLAN.md on a goal,
PLAN.md wins: stop and report, **except** the approved departures (P9 and Phase 3's P9b: keys, ClCertA and key loading
out, OpenSSL 3; P10 the source asset; P11 NOTICES here; P12 the pins filled at I2; P13 the draft prerelease; P14
OpenSSL's source asset; P15 and P18 the history rewrites; P16 the README route on our core; P17 the stock core out of
every default; P19 the zip's notices, the snapshot asset and a few code lines), which you follow.

**Never write a key or certificate byte value, its offset in any binary, or how the key blob is decoded**, in any
file, output line, report or commit message. Say "the key blob" and "the ClCertA arrays". Code that needs the bytes
(check `keyblob` through `keyblob_findings()`, check `history-bytes`) reads them at run time from SRC with
`gate_f2._header_bytes()` and prints counts only; a plant that needs them writes them only into a temp folder outside
the repo and deletes it.

You work in `../libazahar-py-i` (branch `step-i`, made at main after Phase 3 merged and G8b ran). "MAIN" is
`~/VSCodeProjects/3ds-toolkit/projects/libazahar-py`. After your step 0's links: "CORE" is
`build-core/azahar_lazpy_libretro.dylib` (the 01:06 build), "INPUTS" `build-core/build.inputs`, "BUILD"
`build-core/build/`, "LINK" `BUILD/src/citra_libretro/CMakeFiles/citra_libretro.dir/link.txt`, "DEPS" every `*.o.d`
under BUILD, "TREE" `dl/azahar-src/build-src/azahar-unified-source-2126.2/` (the stripped tree the core was built
from), "SRC" `dl/azahar-src/unpacked/azahar-unified-source-2126.2/` (the full reading copy), "TARBALL"
`dl/azahar-src/src.tar.xz`, "OSSL" `dl/openssl-src/openssl-3.6.5.tar.gz` (the main loop downloaded it), "SNAP"
`dl/sysarch-src/citra_system_archives-f470e0c.tar.gz` (the citra_system_archives snapshot, the main loop downloaded
it), "KEG" the value of INPUTS' `openssl_prefix=` (the resolved Cellar path, `/opt/homebrew/Cellar/openssl@3/3.6.5`;
review 2 B2), "FORMULA" `KEG/.brew/openssl@3.rb` (the formula the keg was installed from), "APP"
`build/testapp.3dsx`. All of them are MAIN's files, read only (APP is rebuilt in your worktree, 3.6).

**Never commit, never push, never call `gh`, never edit item files, never write in MAIN, never run
`tools/build-core.sh`** (in a worktree it would delete MAIN's build tree through the `dl/` link), **never run anything
from inside a download**: Python that reads TARBALL, SRC, TREE, OSSL or SNAP runs with `-I`; bsdtar only lists and
copies their members. Read first: the repo's `CLAUDE.md`, `docs/map/rules.md`, phase-4.md (all of it; section 0 is
why this step looks as it does), `~/.claude/git-publishing-preferences.md`, `~/.claude/ip-publishing-policy.md`,
`core/README.md`, `core/PIN`, `tools/build-core.sh`, `tools/fetch.sh`, `tools/untar_checked.py`, `tests/gate_f2.py`
(`keyblob_findings`, `KEY_ARRAYS`, `_header_bytes`), `tests/python/conftest.py`, `docs/reviews/release-ip-legal.md`
(the consult), `~/.claude/python-golden-rules.md`, `~/.claude/shell-golden-rules.md`, `~/.claude/c-golden-rules.md`
(one line in `host/azhost_main.c`).

## 1. Goal and gate

A staged release in `runs/release/v0.1.0/` whose every file meets its licence obligations and carries no key, no
certificate, no private string and no third-party content we may not ship; notices generated from what the core
really links and includes, inside the core zip too; `fetch.sh` able to fetch our core and test app by sha256, with
no stock-core download; our core as the library's default. The gate (yours, in I1):

1. `python3 -I tools/release_check.py runs/release/v0.1.0 --skip-pins` prints `PASS` (or the named `SKIP`/`PEND`
   lines of section 3.3) for every check and exits 0; `--plant-red` fails each planted check on its plant.
2. `tools/mkrelease.sh v0.1.0` run twice gives byte-identical core zip, source asset and test app (compare the two
   `SHA256SUMS` minus the build-files line, which embeds HEAD's commit id).
3. Gate 3 of fetch.sh: with the pins temporarily set to the staged files' sha256 in a temp copy of the repo,
   `LAZ_RELEASE_BASE=file://$PWD/runs/release/v0.1.0 LAZPY_ROOT=<temp copy> <temp copy>/tools/fetch.sh --lazpy-core
   --testapp` downloads, verifies and unpacks both and prints that the core is at the default path; a second run
   downloads nothing; a copy with one byte flipped is refused, deleted, and the script exits non-zero. Nothing else
   is fetched (S9). `grep -c azahar-emu tools/fetch.sh` is 0.
4. P17 and B4: `.venv/bin/python -m pytest -q tests/python -m "not slow"` passes (the new `test_paths.py` included);
   `make` builds `build/azhost`; `make testapp` (the README's build block) then `strings -a build/testapp.3dsx | grep
   -c /Users/` is 0.

The main loop's gates after the merges (section 6): I2's `release_check` with the private file, `docs_check.py`
without `--allow-missing`, the fresh clone of main with the full suite; I3's audit says **shippable**; then Guy's
words (Q2-Q4) and I5.

## 2. Facts (checked 2026-11-13; phase-4.md section 8 and R1-R35 have the evidence)

- **Step 0 as built** (Phase 3's P9b, commit 7c33f38, 799e8c3 before G8; the build ended 01:06, exit 0; review 2
  section A): patches 0000-0008 (0007 removes the default ClCertA, 0008 makes `GetKeysStream()` load nothing);
  `core/PIN` has `LAZ_CORE_DROP` with **four** entries: `src/core/hw/default_keys.h`, the two
  `src/core/hle/service/http/ctr-common-1-*.h` headers and the **directory** `externals/libressl` (review 2 B1);
  `OPENSSL_VERSION=3.6.5`, `OPENSSL_PREFIX=/opt/homebrew/opt/openssl@3`, which `build-core.sh:70` resolves with `cd -P`
  to the Cellar path (override `LAZ_OPENSSL_PREFIX`, `:8, 39`; **there is no `OPENSSL_ROOT` or `LAZ_OPENSSL_ROOT`**).
  `build-core.sh` deletes the drop list after the unpack and before the patches (files and directories, `:89-96`; it
  dies if an entry is missing from the fresh tree, and if `LAZ_CORE_DROP` is empty, `:40-42`), configures with
  `-DENABLE_BUILTIN_KEYBLOB=OFF -DUSE_SYSTEM_OPENSSL=ON` and the static OpenSSL at the Cellar path, dies unless
  `OPENSSL_SSL_LIBRARY`/`OPENSSL_CRYPTO_LIBRARY` are KEG's `.a` files, dies if a `.o.d` names a drop-list basename or
  `LibreSSL` is in the core's strings, and installs the dylib atomically. F2's f1,
  `keyblob_findings(build_dir, core, src_root, tree, repo) -> list[str]` (empty = pass), gates it. Its `build_dir` is
  **`build-core/`**, not BUILD: it reads `build_dir/build.exit`, `build_dir/build.inputs` and `build_dir/build/`
  (CMakeCache, `.o.d` files, link.txt), compares INPUTS with the checkout at `repo` (`core/PIN`, the script, the
  patches), and requires the core's mtime to be later than `CMakeCache.txt`'s (S1).
- INPUTS keys (R27, review 2 A; `build-core.sh:140-158`): `tarball=`, `pin=`, `script=`, `patch <name>=<sha256>`
  (0000-0008), `drop=`, `openssl_version=`, `openssl_prefix=`, `openssl_libssl_sha256=`, `openssl_libcrypto_sha256=`,
  `head=` (799e8c3: a pre-G8 SHA; the maps translate it, never compared), `clean=yes`, and `cmake=` (the **full**
  executed cmake command with `<repo>` for the checkout, `:156`).
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
- **The system archives** (R34, consult section 5): four headers under `externals/open_source_archives/include/`
  (`shared_font.app.romfs.h`, `mii.app.romfs.h`, `country_list.app.romfs.h`, `bad_word_list.app.romfs.h`), each naming
  its own generator commit in its header comment (848af47 font, 5e6b5df Mii, bbe60b5 country list, 47cdc93 bad-word
  list; 47cdc93 is not in B3n30/citra_system_archives' history, its content matches 2d98119). The font holds glyphs
  from Montserrat Regular 4.000 (SIL OFL 1.1, "Copyright 2011 - 2016 The Montserrat Project Authors") and GNU Unifont
  10.0.05 (GPLv2 or later with the GNU font embedding exception). The generator is GPLv2 or later. A snapshot of the
  generator repository at f470e0c (SNAP) holds four of the generator commits. Wording: "open-source replacement system
  archives generated by the Citra project's citra_system_archives", **never "Nintendo's" archives**.
- **OpenSSL 3.6.5** (R30): KEG's `sbom.spdx.json` names the source
  `https://github.com/openssl/openssl/releases/download/openssl-3.6.5/openssl-3.6.5.tar.gz`, sha256
  `a2157c2830efdec3788939b00c9b0638306d3f0bbb76dc4832ee503bb397df98`, the bottle sha256
  `0994a8029175af4578c3b93b3020e58dffa638ca21dc22d862c6bc02fea7e73b`, no patches; `openssl version -a` gives the
  platform, the compiler flags and `OPENSSLDIR`. KEG has `LICENSE.txt` (Apache-2.0) and no NOTICE (Homebrew copies
  `notice` files into kegs, `metafiles.rb:13`); the tag has no top-level NOTICE (consult section 3), so 4(d) most
  likely owes nothing: I0 checks OSSL's member list. OpenSSL's copyright line is "The OpenSSL Project Authors" (in
  OSSL's `LICENSE.txt` header or `README.md`; quote it from the file). FORMULA (`KEG/.brew/openssl@3.rb`) is the
  formula the keg came from (review 2 S9: no `brew cat`, no network); `KEG/INSTALL_RECEIPT.json` may name the
  homebrew-core commit (`tap_git_head`).
- `openssl@3` is `brew pin`ned since 01:04 (Phase 3 ask 1), held until I5.
- Third-party notices inside Azahar's own `src/` (review 1 S7): `src/common/cityhash.{h,cpp}` (MIT),
  `src/common/bit_field.h`, `vector_math.h` (Tony Wasserka), `src/core/file_sys/plugin_3gx*` and
  `src/core/hle/service/plgldr/plgldr.*` (MIT, The Pixellizer Group), `src/video_core/host_shaders/texture_filtering/*.frag`
  (the shaders are embedded through generated headers, so DEPS name the generated files, not the `.frag` sources).
- Azahar: SRC `license.txt` is the GPLv2 text (no OpenSSL exception); the sources say "GPLv2 or any later version".
  The binary links Apache-2.0 code (SPIRV-Tools, OpenSSL 3), which GPLv2 does not accept, so the binary goes out under
  **GPLv3** (G4, a fact).
- The 01:06 core is 21,828,992 bytes (item 300's last note); `vtool -show-build`: minos 11.0, sdk 26.2, but its libcrypto objects are built
  for macOS 15.0 (linker warning), so it needs macOS 15+ (R31; the release says so). It holds OpenSSL's Homebrew
  directories as strings (R30) and no `/Users/` string. `build/libazhost.dylib` and `build/azhost` are minos 15.0.
- The stock Azahar dylib carries the key blob and ClCertA (phase-4.md 0.6). The consult grades our scripted fetch of
  it YELLOW (section 7), so P17 removes it (default; phase-4.md Q1).
- `fetch.sh` (R7): helpers `get URL SHA FILE`, `ok`, `verify`, `sha_of`, a pins block at the top (`:17-36`; the stock
  core's `CORE_VER`, `CORE_URL`, `CORE_SHA` at `:18-20`), `LAZPY_ROOT`; the parser takes one argument (`--force`,
  `:38-43`); `--force` deletes the stock dylib (`:80`); the stock fetch and unzip are `:85-93`.
- **The stock core in code and tests at bd62873** (P17's work list; F2 adds two): `host/azhost_main.c:13` (`DEFAULT_CORE
  "dl/azahar/azahar_libretro.dylib"`); `python/libazahar/_paths.py:34-36` (`core_path()`'s default and docstring);
  `tests/python/conftest.py:61` (`host_paths`' hint "run tools/fetch.sh or set LAZ_CORE"), `:67-73` (`stock_core`,
  the fixed `dl/azahar/` path), `:76-84` (`lazpy_core`, falls back to `build-core/` only); `tests/gate-b.sh:45`
  (`build/fe2 dl/azahar/azahar_libretro.dylib`); `tests/python/test_c_checks.py:135-137` (D's
  `test_c4_debug_text_needs_our_core`, through `stock_core`). F2's diff (R32) adds `tests/gate_c.py:283` (fallback
  `os.environ.get("LAZ_CORE") or "dl/azahar/azahar_libretro.dylib"`) and `tests/gate_f2.py --stock` (required; it stays
  so, and its runners line passes `--stock "$LAZ_STOCK_CORE"`). E's and G's tests are not on main yet: I0 greps them.
- **The test app's paths** (R33, review 2 B4): `build/testapp.3dsx` holds 6 `/Users/` strings from `assert()`'s
  `__FILE__` (`testapp/source/draw2d.c`, `font.c`); `testapp/Makefile:9` sets `TOPDIR ?= $(CURDIR)` (= `testapp/`),
  `:22-23` the `CFLAGS`, with no prefix map.
- `tools/untar_checked.py` is our own stdlib unpacker (rules.md 2's checked extraction); it runs on a downloaded
  archive without running anything from it.
- No `user.email` in this repo's git config; section 8.2 sets it before the tag.
- `.gitignore` ignores `*.3dsx`, `*.zip`, `*.tar`, `*.tar.xz`, `*.tar.gz`, `*.dylib`, `runs/`, `dl/`, `build-*/`.
- bsdtar 3.5.3 copies members from an archive given as `@file` without extracting; `--exclude`, `--uid`, `--gid`,
  `--uname`, `--gname`. Apple zip 3.0's `-X` drops extra attributes. `git archive` of a commit stores the commit id and
  uses the commit time as every file's mtime (deterministic per commit, different per commit).

## 3. What to build

### 3.1 `tools/mknotices.py` -> `NOTICES.md` (P11; stdlib, `python3 -I`, about 230 lines, functions under 40)

`python3 -I tools/mknotices.py --link LINK --deps BUILD --tree TREE --src SRC --inputs INPUTS --openssl OSSL --sysarch
SNAP [--ofl FILE] [--unifont FILE] > NOTICES.md`. KEG is read from INPUTS' `openssl_prefix=` (B2), never typed. Two tables in the script: (a) components: name -> (its `externals/` folder or `openssl`, its licence file
or the file whose top comment holds the licence, a short SPDX-style name, "linked" or "headers only", extra required
lines); (b) known `src/` notices: path glob -> (holder, short name). The script:

1. reads LINK's `.a` inputs and every DEPS path; normalises `externals/./x` to `externals/x` and
   `dynarmic/externals/<y>` to `<y>`; classifies each path as TREE `externals/<name>` (-> table a), TREE `src/` (-> 2),
   a path under KEG (the Cellar path; -> `openssl`), BUILD (generated; skipped), the macOS SDK or `/usr/include` (system; skipped). **Any other path,
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
     'Modified by libazahar-py' notice (patch 0000)"; what was removed before the build, in words (the three header
     paths, "console key and certificate data, not used by this build", and "`externals/libressl/`, the bundled
     LibreSSL, not used: this build links OpenSSL 3"; **no hashes of the three headers**, consult section 2);
   - Azahar (GPLv2 or later; the Citra and Azahar teams; commit 219d743a...);
   - "Inside Azahar's tree": each table-(b) file with its notice block verbatim;
   - one section per component in name order: name, folder, how it is used, short name, then the licence text
     **verbatim** in a fenced block (read from SRC, never retyped); faad2's section adds the Nero AG line as a plain
     line, and the copyright line from its file headers (M. Bakker, Nero AG), both verbatim (consult section 4);
     SoundTouch's adds "LGPL-2.1: this release's complete corresponding source of the whole work lets you
     relink"; `openssl`: "OpenSSL 3.6.5 (Homebrew `openssl@3`, statically linked), Apache-2.0", OpenSSL's copyright
     line ("Copyright ... The OpenSSL Project Authors", quoted from OSSL), `LICENSE.txt` verbatim from OSSL (read with
     `tarfile`, no extraction), and the top-level `NOTICE` file's text verbatim **if OSSL has one** (Apache-2.0
     4(d)), else the line "OpenSSL's source tarball has no NOTICE file (checked)";
   - `open_source_archives` (consult section 5): "open-source replacement system archives generated by the Citra
     project's citra_system_archives (GPLv2 or later)"; per header: its path, its sha256 (from TREE, which I0 proves
     equal to TARBALL's member) and the generator commit **read from the header's own comment** (never typed); the
     line "47cdc93 cannot be found in citra_system_archives' history; its content matches 2d98119"; "no licence file
     in Azahar's tarball; the generator's snapshot at f470e0c is a release asset"; then the font: "glyphs from
     Montserrat Regular 4.000 and GNU Unifont 10.0.05", Montserrat's copyright line, the full SIL OFL 1.1 text
     verbatim, and Unifont's copyright line with "GPLv2 or later with the GNU font embedding exception". The OFL and
     Unifont texts come from SNAP's members when it holds them (`tarfile`, no extraction), else from `--ofl` and
     `--unifont` (files the main loop downloaded, section 6); none found exits 1. Never the word "Nintendo's";
   - the test app: ours, GPLv3-or-later, source in this repository at the release tag; built with devkitPro's
     devkitARM, libctru, citro2d and citro3d (zlib licence; libctru's default icon is in its SMDH) and newlib's libc and
     libm (BSD-style notices: the licence file devkitARM ships, found with `find /opt/devkitpro -iname 'COPYING*'
     -o -iname 'LICENSE*'`, verbatim; if none is installed, name newlib, "BSD-style, see COPYING.NEWLIB in newlib's
     source" and report it);
   - "Not included": MoltenVK (Apache-2.0) is fetched by `tools/fetch.sh` from its upstream, never shipped; "Azahar's
     original tarball also contains the bundled LibreSSL; we removed it with the three headers" (review 2 B1); no
     ROMs, keys, certificates, system files or NAND data; the key blob, the default HTTP client certificate and key
     loading are removed (P9b). Nothing about Azahar's own core (P17).
   The GPL texts are not pasted (they travel as `LICENSE` and `COPYING-azahar.txt` in the zip). Output is
   deterministic: no dates, sorted sections.

### 3.2 `tools/mkrelease.sh`, the assets, `SOURCE.md`, `core/PIN-nokeys`, `core/OPENSSL.md`, the notes

`tools/mkrelease.sh <tag>` (POSIX sh, `set -eu`, about 130 lines): inputs CORE, INPUTS, APP, TARBALL, OSSL, SNAP at
the repo-relative paths above, each overridable (`LAZ_REL_CORE`, `LAZ_REL_INPUTS`, `LAZ_REL_APP`, `LAZ_REL_TARBALL`,
`LAZ_REL_OSSL`, `LAZ_REL_SNAP`); it verifies TARBALL against `core/PIN`, OSSL against `core/OPENSSL.md`'s sha256 and
SNAP against the script's own `SNAP_SHA=` line first (a mismatch stops), then writes `runs/release/<tag>/` fresh (`rm -rf`, using a staging folder
`runs/release/<tag>.stage/`):

| Asset | How |
|---|---|
| `azahar_lazpy_libretro-2126.2-lazpy.1-macos-arm64.zip` | stage `azahar_lazpy_libretro.dylib` (CORE), `NOTICES.md`, `LICENSE` (the GPLv3 text), `COPYING-azahar.txt` (SRC `license.txt`), `SOURCE.md`, `build.inputs` (INPUTS); `touch -t 202601010000` each; `zip -X -9 -q` from inside the stage folder, names sorted. NOTICES.md and the GPLv3 text **inside** the zip are what Apache-2.0 4(a), OFL condition 2 and faad2's line need (consult sections 3-5, P19) |
| `azahar-unified-source-2126.2-lazpy-nokeys.tar.xz` | P10 (a): write `<SRC_TOP>/LIBAZAHAR-PY-REMOVED.txt` in a stage folder (text below, `touch -t 202601010000`), then `tar -c -J -f OUT --uid 0 --gid 0 --uname '' --gname '' -C <stage> <SRC_TOP>/LIBAZAHAR-PY-REMOVED.txt --exclude '<SRC_TOP>/<entry>' (one per drop-list entry; bsdtar's `--exclude` of a directory name drops the whole directory) @TARBALL`; then `tar -tf OUT \| grep -c externals/libressl` must be 0 (B1) |
| `openssl-3.6.5.tar.gz` | OSSL, copied byte for byte (P14) |
| `citra_system_archives-f470e0c.tar.gz` | SNAP, copied byte for byte (P19, consult section 5 item 4) |
| `libazahar-py-core-build-<tag>.tar.gz` | `git archive --format=tar.gz --prefix=libazahar-py-core-build/ -o OUT HEAD core tools/build-core.sh tools/untar_checked.py` (committed files only, review 1 S11) |
| `testapp.3dsx` | APP, copied |
| `NOTICES.md`, `SOURCE.md` | also as plain assets |
| `SHA256SUMS` | `shasum -a 256` of every other asset, sorted by name |

SNAP's sha256 is pinned once: a `SNAP_SHA=` line at the top of `mkrelease.sh`, with a comment naming the snapshot's
commit (the launch message gives the value from the main loop's download, section 6). `release_check` and SOURCE.md
read it from there.

`LIBAZAHAR-PY-REMOVED.txt` (fixed text, so the asset is deterministic; consult section 2's wording, **no hashes of
the key and certificate headers**): "Removed by libazahar-py on 2026-11-13 from Azahar's
azahar-unified-source-2126.2.tar.xz (sha256 <SRC_SHA256>), before building its core:
src/core/hw/default_keys.h, src/core/hle/service/http/ctr-common-1-cert.h and
src/core/hle/service/http/ctr-common-1-key.h (console key and certificate data, not used by this build: patches 0007
and 0008, ENABLE_BUILTIN_KEYBLOB=OFF); externals/libressl/, the bundled LibreSSL, <n> members (not used: this build
links OpenSSL 3.6.5, USE_SYSTEM_OPENSSL=ON). Every other file is unchanged." `<n>` is counted from TARBALL's member
list. The tarball's own sha256 is fine to print (it is Azahar's published value); no other hash appears.

`SOURCE.md` (written by mkrelease.sh from INPUTS and fixed text; no timestamps; **no sha256 of the core zip or of the
build-files asset**, which `SHA256SUMS` holds): what the binary is (macOS 15 or later, arm64; Azahar 2126.2, commit
219d743a, our patches with each sha256 from INPUTS, the build script's sha256, the commit it was built at: INPUTS
`head=` with "translate older SHAs with `docs/commit-map-g8.tsv`, then docs/commit-map-g8b.tsv", and the tag); the
Corresponding Source on this release page: (1) the source asset with its sha256 (Azahar's tarball, its URL and
sha256, minus the drop list, plus the note member; the binary was built from exactly this tree plus the patches), (2)
`openssl-3.6.5.tar.gz` with its sha256 and OpenSSL's own URL (the source of the statically linked `libssl.a` and
`libcrypto.a`; `core/OPENSSL.md` says how they were built), (3) `citra_system_archives-f470e0c.tar.gz` with its
sha256 (the generator and fonts behind the compiled-in system archives), (4) the build-files asset (patches, pins,
options, `OPENSSL.md`, the build script), (5) this repository at the tag. The build (S3): INPUTS' `cmake=` line
**verbatim** in a fenced block, plus `build-core/configure.log`'s two "compiler identification" lines (check
`private` scans both). "Azahar's original tarball also contains the bundled LibreSSL; we removed it with the three
headers" (B1). How to rebuild (S4), in plain words: "Homebrew ships only its current `openssl@3`. If it is 3.6.5,
`tools/build-core.sh` finds it. If not, build 3.6.5 from (2) with the recipe in `core/OPENSSL.md` (not tested by this
project) and set `LAZ_OPENSSL_PREFIX` to its install prefix. Then `LAZ_CORE_PIN=core/PIN-nokeys tools/build-core.sh
--build`."

`core/PIN-nokeys` (new, committed): `core/PIN`'s keys with `SRC_URL` = our release URL of the source asset,
`SRC_SHA256`/`SRC_SIZE` of it, `SRC_FILE=dl/azahar-src/src-nokeys.tar.xz`, `SRC_TOP` unchanged, `OPENSSL_*` copied,
and `LAZ_CORE_DROP=LIBAZAHAR-PY-REMOVED.txt` (`build-core.sh:40-42` refuses an empty drop list and requires each
entry to exist; the note member exists in the stripped tree and nothing reads it), with a comment line naming the
original tarball and why the drop entry is the note. The source asset is deterministic, so its sha256 is known in I1.
Never edit `core/PIN` itself: its sha256 is INPUTS' `pin=`, which check `keyblob` compares (S6).

`core/OPENSSL.md` (new, about 40 lines; review 2 S4, S9; consult section 3): version 3.6.5; the upstream URL and
sha256 (from KEG's SBOM, equal to OSSL; the main loop also checked OpenSSL's published `.sha256`); "Homebrew
`openssl@3` bottle, sha256 <bottle>, built <SBOM builtDate>, no patches (the SBOM lists none)"; the formula: FORMULA's
sha256, its path in homebrew-core (`Formula/o/openssl@3.rb`), the homebrew-core commit from
`KEG/INSTALL_RECEIPT.json`'s `tap_git_head` if it has one (else "not recorded in the keg"; never copy the receipt's
`source.path`, a home-folder path, R30), and its configure
arguments quoted from FORMULA (the `args` list and the `Configure` call; FORMULA is not attached); `KEG/bin/openssl
version -a`'s platform, compiler and `OPENSSLDIR` lines verbatim; the two `.a` sha256 from INPUTS; "Homebrew ships
only its current `openssl@3`"; the recipe to build the same libraries from OSSL, **marked "not tested by this
project"**: unpack, `./Configure darwin64-arm64-cc --prefix=<dir> no-shared <the formula's arguments>`, `make`, `make
install_sw`, then `LAZ_OPENSSL_PREFIX=<dir>`; "the release attaches this exact tarball".

docs/release-notes/v0.1.0.md (about 30 lines): what it is (one line), "early prerelease", a link to `STATUS.md`;
"Unofficial: not affiliated with or endorsed by the Azahar project"; the assets, one line each (no sha256:
`SHA256SUMS` holds them); "Requires macOS 15 or later on Apple silicon (the statically linked OpenSSL is built for
macOS 15)"; "The core binary is GPLv3; its complete corresponding source is on this page: the Azahar source asset,
the OpenSSL source tarball, the system-archive generator snapshot, the build files, and this repository at the tag";
"Homebrew only: no ROMs, keys, certificates or system files; our core is built without Azahar's built-in key data and
default HTTP client certificate, and it loads no keys"; the Nintendo non-affiliation line; "Install: see README".
**No admission text of any kind** (policy rule 5), no speed numbers, no images.

### 3.3 `tools/release_check.py <dir> [--skip-pins] [--pre-push] [--plant-red]` (stdlib, `python3 -I`, about 280 lines)

Each check prints `PASS <name>`, `FAIL <name>: <reason>`, `SKIP <name>: <why>` or `PEND <name>: <what>` (PEND only in
I1, for paths not committed yet); any FAIL exits 1; under `--pre-push` every SKIP and PEND is a FAIL. File inputs are
overridable for the plants (`--nm-output`, `--otool-output`, `--strings-output`, `--link`, `--inputs`, `--fetch`,
`--pyproject`, `--repo`). Numbered in run order (review 2 N1). Checks 4-6 keep only what `keyblob_findings()` does not
already prove (review 2 S2): one implementation of the step-0 rules, Phase 3's.

1. **assets**: exactly 3.2's file set; `SHA256SUMS` matches every file; the core zip's members are exactly the six
   names of 3.2 (P19), and its `LICENSE` is the GPLv3 text (first line).
2. **keyblob** (S1, B2): first `sha256(the zip's dylib) == sha256(CORE)` (read from the zip in memory, never
   extracted with its 2026-01-01 mtime); then `gate_f2.keyblob_findings(Path("build-core"), CORE, SRC, TREE,
   repo=<the checkout's root>)` (imported from `tests/`) returns `[]`; each finding is printed; INPUTS' `head=` is
   printed (the old check 7's print).
3. **exports**: `nm -gU` lists exactly 25 `_retro_*` plus `_lazpy_read_memory`, `_lazpy_write_memory`,
   `_lazpy_movie_play`.
4. **version**: the core's strings hold `2126.2` (`-lazpy.1` and patch 0005's hash are f1's).
5. **linkage**: `otool -L` shows only `/System/Library/...` and `/usr/lib/...` plus its own `@rpath` id; no
   `libMoltenVK` or `libvulkan`; no `MVKInstance`/`MVKDevice` string (libssl and libcrypto are f1's).
6. **openssl** (G3): OSSL's sha256 equals `core/OPENSSL.md`'s and KEG's SBOM's; the staged OpenSSL asset equals OSSL;
   INPUTS' `openssl_version=` equals the version in OSSL's file name and in `core/OPENSSL.md`; KEG (INPUTS'
   `openssl_prefix=`) equals `cd -P /opt/homebrew/opt/openssl@3` (printed; a difference is a FAIL under
   `--pre-push`); KEG's two `.a` sha256 equal INPUTS' `openssl_*_sha256=` (a difference is a FAIL only under
   `--pre-push`: the pin was lost and nobody can recheck the link, risk 13).
7. **private**: in the core's strings, the zip's text files, the build-files asset, `testapp.3dsx`, `NOTICES.md`,
   `SOURCE.md` and the release notes (not the three upstream tarballs, whose sha256 are pinned): FAIL on `/Users/`, on
   any `@gmail.com` address, on any address ending `.local`, on a MAC address form, and on an IPv4 literal in 10/8,
   172.16/12, 192.168/16 or 169.254/16; other IPv4 literals (Azahar's `8.8.8.8`) and other email addresses are printed
   as `NOTE` lines for the audit. OpenSSL's compiled-in Homebrew paths (`OPENSSLDIR` `/opt/homebrew/etc/openssl@3`,
   `ENGINESDIR` and `MODULESDIR` under `/opt/homebrew/Cellar/openssl@3/3.6.5/lib`) and the zipped INPUTS'
   `openssl_prefix=` are expected: printed as `NOTE expected` lines, never a FAIL; any other `/opt/homebrew/` string is
   a plain `NOTE`. **Needles:** if `LAZ_PRIVATE_NEEDLES` names a readable file, each of its lines (the text left of
   `==>` when a line has one; a `regex:` line is used as a regex) is searched case-insensitively in the same files; a
   hit prints only the file name and the needle's line number, never the needle. No variable: `SKIP` (FAIL under
   `--pre-push`). **Never put a needle, or the needle file's path, in this script, its output, or any tracked file.**
8. **notices**: `mknotices.py` re-run to a temp file equals the working tree's `NOTICES.md` byte for byte, and the
   zip's `NOTICES.md` equals it; under `--pre-push` the working tree's equals HEAD's. It holds: "The OpenSSL Project
   Authors"; faad2's Nero line; "SIL OPEN FONT LICENSE Version 1.1" and Montserrat's copyright line; Unifont's line;
   a citra_system_archives section naming the four generator commits; and not the word "Nintendo's" (consult 3-5).
9. **source** (P10 (a), B1, S4): list the source asset's and TARBALL's members side by side (`tarfile`, no
   extraction). A member is **dropped** if its name equals a drop-list entry or starts with `<entry>/`; FAIL if any
   dropped member is in the asset. Every other TARBALL member is in the asset in the same order, with the same type,
   mode, size, mtime, link target and content sha256 (uid, gid and names not compared); the note member is present,
   first, and equals the expected text, which holds no 64-hex string other than TARBALL's own sha256 (consult
   section 2); `python3 -I tools/untar_checked.py <asset> <temp dir>` exits 0 and its `members=` count equals the
   asset's (the temp dir is removed after); `core/PIN-nokeys`' `SRC_SHA256` and `SRC_SIZE` equal the asset's; the
   snapshot asset equals SNAP and `mkrelease.sh`'s `SNAP_SHA=`.
10. **build-files**: the asset equals a fresh `git archive` of HEAD with the same arguments; a listed path that is in
    the working tree but not in HEAD (in I1: `core/PIN-nokeys`, `core/OPENSSL.md`) is `PEND`.
11. **pins**: fetch.sh's `--lazpy-core` and `--testapp` sha256 pins equal the staged zip's and `testapp.3dsx`'s; the
    URLs use the tag and `https://github.com/GuyShtainer/libazahar-py/releases/download/`; fetch.sh holds no
    `azahar-emu` string (P17; if Guy accepts the YELLOW, Q1, this one line changes to "only inside the
    `--stock-core` branch"). `--skip-pins` makes the sha256 part `SKIP` (I1: the main loop fills the pins at I2, P12).
12. **repo**: `git ls-files` has no path matching rules.md 1's list (`.dylib .zip .tar .tar.xz .tar.gz .3ds .cci .cxi
    .cia .3dsx .gba .nds .sav`, `aes_keys.txt`, `keys.txt`, `seeddb.bin`, `dl/`, `vendor/`, `runs/`, `build*/`,
    `sdmc/`, `nand/`, `sysdata/`) and no `.github/FUNDING.yml` (consult condition 4); `git log --all --diff-filter=A
    --name-only --format=` has none either; the tracked code (`host/`, `python/`, `testapp/`, `examples/`,
    `tools/fetch.sh`) holds none of `keys.txt`, `aes_keys`, `seeddb`, `boot9`, `title.keys` (condition 1); no tracked
    `.md` holds a run of 8 or more `0xNN` tokens (regex `(0x[0-9a-fA-F]{1,2}[\s,]+){7}0x[0-9a-fA-F]{1,2}`; condition
    5); every commit's author and committer email is the no-reply address; with the needle file: every blob in `git
    rev-list --all --objects`, every commit message and every tag message holds no needle (counts only); no
    `refs/replace/` and no ref other than `refs/heads/*` and `refs/tags/*`.
13. **history-bytes** (new; consult sections 1 and 9): needles made **at run time** from SRC with
    `gate_f2._header_bytes(SRC, rel, array)` for each of `gate_f2.KEY_ARRAYS`: every 6-byte window of each array that
    has at least 4 distinct byte values, held in a Python `set` in memory (never written to disk). Then every blob of
    `git rev-list --all --objects` (each blob once, through `git cat-file --batch`), every commit message and every
    tag message: find each run of hex byte tokens (`0x` optional, separated by spaces or commas) and each hex string
    of 12 or more digits (both byte alignments), turn it into bytes and look up each 6-byte window in the set. Prints
    only `history-bytes: <n> blobs, <m> hits` and, per hit, the blob's first path and commit (never the bytes or the
    match position). A hit is a FAIL (another G8b pass, risk 7). SRC missing or an array parsing to fewer than 128
    bytes is a FAIL (nothing was checked).
14. **versions**: `pyproject.toml`'s `version` and `python/libazahar/__init__.py`'s `__version__` both equal the tag
    without its `v` (S10).
15. `--pre-push` adds: `git status --porcelain` empty; `git config user.email` is the no-reply address and `user.name`
    is `Guy Shtainer`; every tag's tagger email is the no-reply address; `python3 -I tools/docs_check.py` passes; the
    release notes contain none of `bundles`, `includes ©`, `ripped`, and no speed token (`\b\d+(\.\d+)?\s?x\b`,
    `\bfps\b`); "keys" only inside "no keys" or "key data".
16. **macos** (R31): `vtool -show-build` of the core (from the zip, in memory or a temp copy) and of
    `build/libazhost.dylib` and `build/azhost` in the checkout: platform macOS, arm64 only; the host binaries' minos is
    15.0; the core's is printed (11.0 on the v0.1.0 core, a known header mismatch that STATUS states) and a minos above
    15.0 is a FAIL; the release notes and `SOURCE.md` (and, under `--pre-push`, README.md) hold "macOS 15 or later".
17. `--plant-red`: in a temp folder outside the repo, plant one fault per check and pass only if each check fails on
    its plant: a stray asset (1); a core copy (fresh mtime) with a ClCertA window appended, made at run time from
    `_header_bytes` in the temp folder, through `keyblob_findings` on the copy (2); an extra name in a fake `nm` output
    (3); a fake strings output without `2126.2` (4); a fake `otool` line with `libMoltenVK` (5); an OSSL copy with one
    byte flipped (6); `/Users/x` in a SOURCE.md copy (7); a NOTICES copy without the OFL text (8); a re-packed source
    asset copy that keeps one `externals/libressl/` member (9); a fetch.sh copy with a changed pin and one with an
    `azahar-emu` URL (11); a temp git repo with a tracked `.github/FUNDING.yml` and a `.md` with eight `0x00` tokens
    (12); a temp git repo with one commit whose `.md` holds one array window as hex text, written by the plant in the
    temp folder (13); a pyproject copy at `0.1.0.dev0` (14); a SOURCE.md copy without "macOS 15 or later" (16). Not
    planted: 10 and 15 (they read this repo's git state); say so. The temp folder is deleted at the end, so no window
    outlives the run.

### 3.4 `tools/fetch.sh`: part flags, `--lazpy-core`, `--testapp`, no stock core (P12, P16, P17)

The parser loops over its arguments (S9). Part flags: `--moltenvk`, `--headers` (the libretro and Vulkan headers),
`--lazpy-core`, `--testapp`; plus `--force`. **No part flag = `--moltenvk --headers`.** A part flag fetches only its
own files. **The stock core goes (P17, consult section 7):** delete the `CORE_VER`/`CORE_URL`/`CORE_SHA` pins
(`:18-20`), the stock fetch and unzip (`:85-93`) and the stock path in `--force` (`:80`); the top comment no longer
says "the Azahar libretro core"; nothing in the script names `azahar-emu` (check 11). There is no `--openssl-src`
flag: OSSL is a release asset and the main loop's one-time download (section 6). A second pins block below the first
holds the release tag (`v0.1.0`), the base URL (`https://github.com/GuyShtainer/libazahar-py/releases/download/$TAG`)
and two sha256 lines with placeholders (`LAZPY_CORE_SHA=TBD-at-I2`, `TESTAPP_SHA=TBD-at-I2`); a `TBD` pin makes its
flag die with "pins are filled at release time". `LAZ_RELEASE_BASE` overrides the base URL (the clone at I2 and your
gate 3). `--lazpy-core`: `get` the zip into `dl/lazpy-core/`, `verify` it, `unzip -o` only
`azahar_lazpy_libretro.dylib`, `NOTICES.md` and `SOURCE.md` into `dl/lazpy-core/`, then print "our core is at
dl/lazpy-core/azahar_lazpy_libretro.dylib, the default core path (LAZ_CORE overrides it)". `--testapp`: `get` into
`dl/testapp/testapp.3dsx`, copy to `build/testapp.3dsx` (`mkdir -p build`). Keep the helpers and the "download only
if missing or wrong; a mismatch deletes and exits" rule; no new dependency. The usage line lists every flag; the
comment at the top says what each fetches. curl sets no quarantine attribute, so the dylib loads.

**If Guy accepts the YELLOW instead (phase-4.md Q1; the launch message says so):** keep the stock pins and fetch as
an opt-in `--stock-core` flag that is never part of the no-flag set, and check 11 allows `azahar-emu` only inside
that branch. Everything else in 3.4 and 3.5 stays.

### 3.5 P17: our core is the default, and the stock core is opt-in for tests (exact changes)

Apply these on top of F2's merged lines (R32: F2 edits `_paths.py`, `azhost_main.c` and `tests/` too). I0 lists every
hit first (section 5); a hit not below is changed the same way and reported.

| File | Change |
|---|---|
| `python/libazahar/_paths.py:34-36` | `core_path()`'s default becomes `repo_root() / "dl" / "lazpy-core" / "azahar_lazpy_libretro.dylib"`; the docstring says so |
| `host/azhost_main.c:13` | `#define DEFAULT_CORE "dl/lazpy-core/azahar_lazpy_libretro.dylib"` (the usage text, if it names the default, follows) |
| `tests/python/conftest.py:61` | `host_paths`' hint: "run tools/fetch.sh --lazpy-core or set LAZ_CORE" |
| `tests/python/conftest.py:67-73` | `stock_core` reads `LAZ_STOCK_CORE`. Unset: `pytest.skip("set LAZ_STOCK_CORE to Azahar's own core to compare cores")`, **always, even under `LAZ_REQUIRE_EMULATOR=1`** (the stock core is never required). Set but not a file: `_missing(core, "LAZ_STOCK_CORE names no file")` (a failure under `LAZ_REQUIRE_EMULATOR=1`). The docstring says so |
| `tests/python/conftest.py:76-84` | `lazpy_core`: `LAZ_CORE` when it names our core, else `build-core/azahar_lazpy_libretro.dylib`, else `dl/lazpy-core/azahar_lazpy_libretro.dylib` (the first that exists); hint "run tools/fetch.sh --lazpy-core or set LAZ_CORE" |
| `tests/gate-b.sh:45` | `build/fe2 "${LAZ_STOCK_CORE:?set LAZ_STOCK_CORE to Azahar's own core}" ...` |
| `tests/gate_c.py:283` (F2) | the fallback becomes `str(_paths.core_path())` (import it the way the script already reaches `python/`; if it does not, put `python/` on `sys.path` inside `main()`), so no stock path remains |
| `tests/gate_f2.py` (F2) | unchanged: `--stock` stays required; the runners line passes `--stock "$LAZ_STOCK_CORE"` (the main loop writes it) |
| `tests/python/test_paths.py` (new, no emulator) | with `LAZ_CORE` unset, `core_path()` ends in `dl/lazpy-core/azahar_lazpy_libretro.dylib`; with it set, it is that path; the `stock_core` fixture skips with `LAZ_STOCK_CORE` unset even when `LAZ_REQUIRE_EMULATOR=1` (use `pytester` or call the fixture's helper directly, whichever the conftest's shape allows) |
| E's and G's tests (after the merge) | every `dl/azahar/` path or stock assumption I0 finds: through `stock_core` (so it skips without `LAZ_STOCK_CORE`) or through the default core |

`test_c4_debug_text_needs_our_core` (D) keeps using `stock_core`, so it skips without `LAZ_STOCK_CORE`; F2's
`test_c4_debug_text_on_our_core` covers our core. The main loop updates rules.md rule 3's "the stock core is fetched
by a script" clause and runners.md's `fetch.sh` and c4 lines from your report (section 10); you do not edit
`docs/map/`. You run the fast pytest only; the full suite runs in the clone at I2 (`LAZ_REQUIRE_EMULATOR=1`, our core
at the default path, no stock core: risk 12).

### 3.6 The test app's paths (review 2 B4, R33)

One line in `testapp/Makefile`, after `:23`: `CFLAGS  += -ffile-prefix-map=$(abspath $(TOPDIR)/..)/=` (TOPDIR is
`testapp/`, so the repo root maps to nothing and `assert()` keeps `testapp/source/draw2d.c`). Then the README's build
block (`DEVKITPRO=/opt/devkitpro DEVKITARM=/opt/devkitpro/devkitARM PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH
make testapp`) in your worktree, and `strings -a build/testapp.3dsx | grep -c /Users/` must be 0 and `strings -a
build/testapp.3dsx | grep -c 'testapp/source/'` above 0 (the asserts are still there). **Never `-DNDEBUG`** (it changes
the app). If the paths survive (devkitPro's rules compile from another folder), try `-fmacro-prefix-map` with the
same value and report which worked.

## 4. Files (you create or edit only these)

| Path | Role |
|---|---|
| `tools/mknotices.py`, `NOTICES.md` (generated, committed) | 3.1 |
| `tools/mkrelease.sh`, `core/PIN-nokeys`, `core/OPENSSL.md` | 3.2 |
| `tools/release_check.py` | 3.3 |
| `tools/fetch.sh` | 3.4 only |
| `python/libazahar/_paths.py`, `host/azhost_main.c`, `tests/python/conftest.py`, `tests/gate-b.sh`, `tests/gate_c.py`, `tests/python/test_paths.py` (new), and the E/G test lines I0 finds | 3.5 only (P17) |
| `testapp/Makefile` | 3.6 only (one line, B4) |
| docs/release-notes/v0.1.0.md | 3.2 |
| `core/README.md` | the "Licenses" section only: the drop list (three headers and `externals/libressl/`) and patches 0007/0008 (removed key data, certificate and key loading); OpenSSL 3 static (`core/OPENSSL.md`); the release's source assets (P10, P14, the snapshot); the binary is GPLv3 (G4); `PIN-nokeys`; remove "ships with the unchanged source tarball" |
| `pyproject.toml`, `python/libazahar/__init__.py` | the version line in each: `0.1.0` |

Not yours: `README.md`, `STATUS.md`, `docs/USING.md`, docs/HOST-API.md, `examples/`, `tools/docs_check.py`,
`tools/clone_check.sh` (step H), `tools/build-core.sh`, `core/PIN`, `core/patches/` (patch 0008's comment waits for
the next `LAZPY_REV`), `tests/gate_f2.py` (you import it, never edit it), every code file not in the table,
`docs/map/*`, item files, the handoff. The map lines go in your report (the main loop commits them with your files,
phase-4.md N8): `docs/map/tools.md` (mknotices, mkrelease, release_check), `docs/map/runners.md` (section 10, with
the `LAZ_STOCK_CORE` lines), `docs/map/code.md` (docs/release-notes/, `core/PIN-nokeys`, `core/OPENSSL.md`,
`NOTICES.md`, `tests/python/test_paths.py`).

## 5. Steps, with a checkpoint after each (save files as you go; never commit)

**Before you are launched (main loop, not you):** Phase 3 merged and its worktrees removed; spike 2's rewording and
G8b done (section 8.1b); OSSL and SNAP downloaded and verified in MAIN (section 6); the launch message gives SNAP's
sha256, Q1's answer (default: remove the stock fetch) and which defaults hold (G2 (a); the consult's GREEN).

0. **I0 (about 0.13 h).** Seed: `mkdir -p dl build-core && for d in azahar moltenvk libretro-headers vulkan-headers
   azahar-src openssl-src sysarch-src; do [ -e MAIN/dl/$d ] && ln -s MAIN/dl/$d dl/$d; done`, `for f in
   azahar_lazpy_libretro.dylib build.inputs build.exit build configure.log; do ln -s MAIN/build-core/$f build-core/$f;
   done`, `cp -R MAIN/vendor .`, `make`, `python3 -m venv .venv && .venv/bin/pip install -e . && .venv/bin/pip install
   pytest`. Then, recording each in `runs/i/rows.md`:
   1. phase-4.md rows R1-R7, R9-R11, R23, R26-R35 against the files;
   2. `keyblob_findings(Path("build-core"), CORE, SRC, TREE, Path("."))` through `python3 -I -c "import sys;
      sys.path.insert(0, 'tests'); import gate_f2; ..."`: **a non-empty list stops the step: report "step 0 not
      gated"**; nothing else here is valid on that binary;
   3. KEG: INPUTS' `openssl_prefix=` equals `cd -P /opt/homebrew/opt/openssl@3 && pwd`; `shasum -a 256
      KEG/lib/libssl.a KEG/lib/libcrypto.a` against INPUTS; FORMULA exists; `KEG/INSTALL_RECEIPT.json`'s
      `tap_git_head` (print it or "none");
   4. LINK's list; the DEPS component list (print it); no DEPS path under `externals/libressl`; `nm -gU CORE | grep
      -c`; `otool -L CORE`; `strings -a CORE | grep -c -e /Users/ -e LibreSSL` (both 0); `tar -tzf OSSL | grep -i -E
      '^openssl-3\.6\.5/(NOTICE|LICENSE)'` (record whether a NOTICE exists); `tar -tf TARBALL | grep -c
      '/externals/libressl/'` (the `<n>` for the note);
   5. **the consult's five archive checks (section 5), as commands** (print counts and sha256 only):
      (a) for each of the four headers: `shasum -a 256 TREE/externals/open_source_archives/include/<h>` equals
      `tar -xOJf TARBALL <SRC_TOP>/externals/open_source_archives/include/<h> | shasum -a 256`;
      (b) decode the bad-word and Mii headers in memory (`python3 -I`: parse the array's `0x` tokens the way
      `_header_bytes` does, then read the RomFS directory with `struct`): the bad-word data holds only the placeholder
      pattern (print "placeholder only" or the count of other lines, never the text); the Mii data is a 73,600-byte
      RomFS holding one file, `CFL_Res.dat` (print the size and the names);
      (c) each header's generator commit, read from its comment (print the four short SHAs);
      (d) SNAP's member list holds the OFL text and the Unifont notice (record the member names, or "absent": then the
      main loop downloads them, section 6);
      (e) the wording rule (never "Nintendo's" archives) is 3.1's and check 8's: nothing to run here;
   6. **every stock-core hit** in the merged code and tests: `git grep -n -e 'dl/azahar/' -e 'azahar_libretro\.dylib'
      -e stock_core -e 'fetch.sh' -e NeedsLazpyCore -- host python tests tools Makefile`, each with what 3.5 does
      to it;
   7. `strings -a MAIN/build/testapp.3dsx | grep -c /Users/` (6 expected, R33);
   8. the long `0xNN` run regex of check 12 over `git ls-files '*.md'` (0 expected).
   Checkpoint: `runs/i/rows.md`.
1. **I1 (about 0.47 h).** In order: 3.6 (the Makefile line, `make testapp` with the build block, the strings counts);
   3.5 (P17; the fast pytest); 3.1 (run it; read `NOTICES.md` once end to end); `core/OPENSSL.md`; the
   `LIBAZAHAR-PY-REMOVED.txt` text and `mkrelease.sh` (stage); `core/PIN-nokeys` (from the staged source asset);
   3.4; then re-stage, 3.3, the release notes, `core/README.md`, the two version lines. Run gates 1-4. Long commands
   (the xz pack, about 1-3 min) run in the foreground under the 10-minute limit; anything longer runs with
   `run_in_background`, an rc file from a `trap ... EXIT` and a bounded Monitor wait. Checkpoint: gates 1-4 quoted;
   the asset list with sizes and sha256; **the exact list of paths for the main loop to `git add`**, with the map
   lines. **End the run with the report "I1 done"**.
2. **I4 (only when the as-built review, I2 or the audit finds faults; the main loop resumes you with them).** Fix
   exactly the findings; re-stage; gate 1; report "I4 done" with the changed paths and the new sha256 values.
3. Stop every waiter and background task you started (TaskStop) before each hand-back.

## 6. The main loop's steps (not the builder's)

Done (records): I-pre, the ip-legal consult, saved as docs/reviews/release-ip-legal.md (2026-11-13); `brew pin
openssl@3` (01:04); G8 (01:06-01:08, 6898a4b, section 8.1); the consult's section 9 material reworded at HEAD
(776e8da).

**Before the builders launch, in this order:**
1. Phase 3 merged (E, F2, G) and every worktree but MAIN removed (`git status --porcelain --ignored` empty in each
   first).
2. **Spike 2's rewording at HEAD** (consult section 8; Q5): in `docs/research/spike-2-real-scene.md` (lines 22 and 57
   at bd62873) replace the game's title, product code and revision, and the game file's location with "one commercial
   game's 3D field scene, run locally" (plus "dumped from the maintainer's own cartridge" only if Guy approved Q5).
   Keep the numbers. Commit that path alone. The removed words never go into a commit message, the handoff, a report
   or any other file except the private replace file (8.1b).
3. **G8b** (section 8.1b), then its map and checks.
4. **Downloads** (rules.md 2: each into its own folder under `dl/`, hashed before any use, never unpacked, never run):
   - OSSL if not there: `mkdir -p dl/openssl-src && curl -fsSL -o dl/openssl-src/openssl-3.6.5.tar.gz <R30's URL>` and
     `curl -fsSL <URL>.sha256`; both must equal R30's sha256 (else delete and stop).
   - SNAP: the full commit id from `gh api repos/B3n30/citra_system_archives/commits/f470e0c --jq .sha` (read only);
     `mkdir -p dl/sysarch-src && curl -fsSL -o dl/sysarch-src/citra_system_archives-f470e0c.tar.gz
     https://github.com/B3n30/citra_system_archives/archive/<full id>.tar.gz`; `shasum -a 256` it and record the value
     in the launch message (GitHub makes archive tarballs on the fly; we ship our downloaded bytes and pin our own
     sha256, so upstream's byte stability does not matter). `tar -tzf` lists its members (no extraction).
   - The font texts, only if I0 finds SNAP lacks them (or before launch, if `tar -tzf` shows none): Montserrat's
     `OFL.txt` and Unifont's licence notice from their upstream repositories, into `dl/font-licences/`, each sha256
     recorded in the launch message.
5. The launch message: Q1's answer (default: remove the stock fetch), G2 (a), the consult's GREEN, SNAP's sha256, the
   font files if any.

- **I2 (after both H and I merge to main and their worktrees are removed; about 0.15 h).** In MAIN:
  1. `git status --porcelain` empty; `git worktree list` shows MAIN only. With I's merge, commit the rules.md rule 3
     and runners.md lines from I's report (the stock core is no longer fetched; `LAZ_STOCK_CORE`; `gate_f2.py --stock
     "$LAZ_STOCK_CORE"`).
  2. The test app from the tag's source (S12): the README's build block, emitted by `python3 -I tools/docs_check.py
     --emit-steps README.md --block build`, run under `env -i HOME="$HOME" PATH=/usr/bin:/bin:/usr/sbin:/sbin
     LANG=en_US.UTF-8 sh -eux` (it sets `DEVKITPRO`, `DEVKITARM` and PATH itself, B3); `strings -a
     build/testapp.3dsx | grep -c /Users/` is 0 (B4).
  3. `tools/mkrelease.sh v0.1.0`; read the zip's and `testapp.3dsx`'s sha256; write them into fetch.sh's two pin
     lines; commit `tools/fetch.sh` alone ("fetch.sh: v0.1.0 release pins"); `tools/mkrelease.sh v0.1.0` again (the
     build-files asset now names the new HEAD; the zip and the test app must keep their sha256: compare).
  4. `LAZ_PRIVATE_NEEDLES=<the private replace file> python3 -I tools/release_check.py runs/release/v0.1.0`; `python3
     -I tools/docs_check.py`.
  5. The fresh clone (S8): `sh tools/clone_check.sh --repo "$PWD" --branch main --out runs/clone-i2 --release-base
     "file://$PWD/runs/release/v0.1.0"`, started with `run_in_background` and an rc file from a `trap ... EXIT`;
     wait with Monitor on the rc file (bounded 45 min). It must end `clone ok` (the README steps, the quickstart on our
     core at the default path, the build block, the **full** pytest with `LAZ_REQUIRE_EMULATOR=1`; a time-bound
     failure is re-run once with the load printed, phase-h.md 3.7). The log is I2's Evidence.
  A failure resumes the builder that owns the failing file (or a fresh sonnet with its brief).
- **I3 (the audit):** dispatch `release-legal-audit` with 9.2; save its report verbatim to
  docs/reviews/release-legal-audit-v0.1.0.md; BLOCKERs go to I4, then re-stage (I2 steps 3-5) and a re-audit of only
  the changed items. SHOULD items: decided with Guy. Commit the report. If a fix lands after the audit, I2's steps 3-5
  run again before the push.
- **The push (Q2-Q4, G5-G7):** section 8.2, only on Guy's word.
- **I5 (after Guy publishes; about 0.05 h):** in a new folder under MAIN's `runs/`: `gh release download v0.1.0 -R
  GuyShtainer/libazahar-py -D assets && (cd assets && shasum -a 256 -c SHA256SUMS)`; `sh tools/clone_check.sh --repo
  https://github.com/GuyShtainer/libazahar-py --branch main --out runs/clone-i5` (real URLs, no `--release-base`);
  then in that clone `.venv/bin/python examples/memory_watch.py` (our core is the default): prints `memory_watch ok`.
  The release URL and these lines are item 420's Evidence. Then delete the G8 and G8b bundles (8.1, 8.1b).

## 7. Machine-sharing rules

No emulator in I0, I1 or I4 (the checks read files; the fast pytest needs none). Never a timed run. No network
except I0's `pip install`: gate 3's `file://` fetch is the only download-like action. No `gh`, no `git push`, no tag. Never write in MAIN (your staged folder is your worktree's
`runs/release/`). Never kill a process you did not start. Folders under `runs/i*` and `runs/release/` (ignored).

## 8. The history rewrite and the push (the main loop's)

### 8.1 The first history rewrite (G8, P15): a record, and the procedure

**Done 01:06-01:08 (6898a4b).** One plan line had named the local part of Guy's personal address (phase-4.md 0.5).
20 commits rewritten (15d0323 became 1844a5d, and the 19 after it); 98 commits before and after; HEAD's tree,
identities and refs other than `main` unchanged; no `refs/replace`; fsck clean; 0 hits in every commit and message;
the map is `docs/commit-map-g8.tsv` (20 rows), pointed at from `docs/map/README.md`. The pre-rewrite bundle sits in
the session's private folder until I5. The steps it followed are the procedure 8.1b reuses:

1. **Preconditions**: no agent writing in MAIN; `git status --porcelain --untracked-files=no` empty (filter-repo ends
   with a reset of the main worktree; untracked and ignored files stay); no other worktree holds an affected commit.
2. **The tool**: `git filter-repo` 2.47.0; the fallback is `git filter-branch -f --tree-filter '<a script outside
   the repo>' -- --all`.
3. **The replace file**: made at run time, mode 600, in the session's private folder outside the repo; its path is
   never in a tracked file, a commit message, the handoff, an item or a report. The same file is `release_check`'s
   needle file (`LAZ_PRIVATE_NEEDLES`).
4. **Before**: save `git rev-parse HEAD HEAD^{tree}`, `git rev-list --all --count`, `git for-each-ref` and the identity
   list (`git log --all --format='%ae %ce' | sort -u`) to `runs/g8*/before.txt` (ignored); scan with counts only; `git
   bundle create <private folder>/<name>.bundle --all` and `git bundle verify`.
5. **Rewrite**: `git filter-repo --force --replace-text <file> --replace-message <file>`.
6. **After**: the same scan, 0 everywhere; the counts, identities and refs as saved; `git for-each-ref refs/replace`
   empty; `git fsck` clean.
7. **The map**: from `.git/filter-repo/commit-map`, the rewritten commits only (old short SHA, new short SHA,
   subject); one line in `docs/map/README.md`; commit with exact paths.
8. **Re-run the checks**: `python3 -I tools/status_check.py --strict-handoff`, `tools/map_check.py`,
   `tools/mkprogress.py` (republish only inside /progress), `make check`.
9. **Outside this repo**: other repos' notes that cite these SHAs go stale; the maps answer them.

### 8.1b The second history rewrite (G8b, P18; the main loop, before the builders launch)

Why: 22 of 100 commits (consult section 9, counted 2026-11-13) carry key-material fragments, offsets and decode notes
that the rewording at 776e8da removed from HEAD only, and spike 2's research file named a commercial game, its product
code and where the game file sat (consult section 8, reworded at HEAD in section 6 step 2). Both block the push.

1. **Preconditions**: 8.1's, plus: Phase 3's worktrees merged and removed (only MAIN; `git worktree list`), so only
   `main` is rewritten; spike 2's rewording committed; no Phase 4 worktree exists yet; the time from `date`.
2. **The replace file, by commands** (never typed from memory, never shown in output): append to the private file of
   8.1 (mode 600, outside the repo):
   - from `git show --word-diff=porcelain 776e8da`: every removed run (`-` lines) becomes `literal==>[removed]`, and
     where the rewording put a phrase in its place (the `+` line that follows), `literal==><that phrase>`, so the
     history reads as HEAD does; drop runs that are plain words also used elsewhere (`the`, `and`, a path), so only
     the material itself is replaced: the main loop reads the generated lines by line count and length, not by
     printing them, and removes too-short lines (under 12 characters) by command;
   - where one fragment appears in older commits with other spacing or line breaks, a `regex:` line (`\s+` between
     tokens) instead of a literal;
   - from the spike 2 rewording commit's word-diff, the same way (the title, the product code and revision, the
     location);
   - the G8 lines stay (one file serves both passes and `LAZ_PRIVATE_NEEDLES`).
3. **Before**: as 8.1 step 4, into `runs/g8b/before.txt`; scan per commit with `git grep -I -c -i -F -f <the literal
   lines' left sides, written to a second private temp file>` and the regex lines with `-E`, plus messages and tags;
   counts and paths only. Expected: the 22 commits of consult section 9 and the commits since `dc2fe80` that hold the
   spike 2 lines. Any other path: list it (the path, not the text) and extend the file before rewriting. Run
   `release_check`'s `history-bytes` logic too (a short `python3 -I` call into the merged `tools/release_check.py`
   if I has merged, else the same window search written inline, counts only): note its count.
4. **Bundle**: `git bundle create <private folder>/pre-g8b.bundle --all`, `git bundle verify`.
5. **Rewrite**: `git filter-repo --force --replace-text <file> --replace-message <file>`.
6. **After**: the step-3 scan gives 0 everywhere; `git rev-parse HEAD^{tree}` equals the saved tree (the rewording
   is already at HEAD, so nothing at HEAD matches; if it differs, restore from the bundle and find the line that
   matched); `git rev-list --all --count` equals the saved count; identities unchanged; no `refs/replace`; `git fsck`
   clean; `python3 -I tools/status_check.py --strict-handoff` passes.
7. **The map**: docs/commit-map-g8b.tsv from `.git/filter-repo/commit-map`, columns `old`, `new`, `subject`, `pre_g8`
   (the pre-G8 SHA from `docs/commit-map-g8.tsv` when the old SHA is in it, else empty), rewritten commits only; one
   more line in `docs/map/README.md` ("SHAs older than 2026-11-13's second rewrite: docs/commit-map-g8b.tsv, then
   docs/commit-map-g8.tsv"). Commit both with exact paths.
8. **Re-run the checks** as 8.1 step 8.
9. **Gen3D's copy** (review 2 N5): Gen3D used an rsync copy of the package (LAZPY-TRY-1.md:9-10). Ask Gen3D's session
   to confirm the copy holds no `.git` (or to delete it): a `.git` there would hold the pre-rewrite history. Tell the
   3ds-toolkit main loop that the maps exist.
10. **Delete both bundles after I5** (they hold the old text).

### 8.2 The push and the release (only on Guy's word)

```
cd ~/VSCodeProjects/3ds-toolkit/projects/libazahar-py
git config user.name "Guy Shtainer"
git config user.email "293649481+GuyShtainer@users.noreply.github.com"
LAZ_PRIVATE_NEEDLES=<the private file> python3 -I tools/release_check.py runs/release/v0.1.0 --pre-push   # all PASS
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
The tag is made at the HEAD the build-files asset was archived from (`release_check --pre-push` check 10, build-files, proves it).
Then Guy opens the draft, checks it and publishes it (G7), or says "publish" and the main loop runs `gh release edit
v0.1.0 -R GuyShtainer/libazahar-py --draft=false`. If the audit held the core asset back (phase-4.md risk 2), the `gh
release create` line lists every asset except the core zip, the Azahar source asset, the OpenSSL tarball and the
snapshot, and STATUS says how to build the core.

## 9. The two legal briefs (the main loop pastes these)

### 9.1 I-pre: the `ip-legal` consult (done, a record)

Asked 2026-11-13 with revision 1's eight questions (the core under rule 7, the source asset, OpenSSL, faad2, the
system archives, the name, the stock-core fetch, spike 2's game lines); answered in
docs/reviews/release-ip-legal.md, sections 1-10, including the unasked section 9. Its question 2's "unbuilt
LibreSSL" is moot: the drop list removes it (review 2 B1). phase-4.md 13.3 maps each section to where it went.

### 9.2 I3: the `release-legal-audit` brief

"Audit libazahar-py for its first push and its first GitHub release, v0.1.0, before anything is public. Repo: MAIN
(on `main`, no remote yet). Its history was rewritten twice on 2026-11-13: G8 removed a private address
(`docs/commit-map-g8.tsv`), G8b removed key-material fragments, offsets and decode notes, and one commercial game's
title, product code and file location (docs/commit-map-g8b.tsv). Staged assets: `MAIN/runs/release/v0.1.0/` (the
core zip with NOTICES.md, LICENSE, COPYING-azahar.txt, SOURCE.md and build.inputs inside; the Azahar source asset;
`openssl-3.6.5.tar.gz`; the citra_system_archives snapshot; the build-files asset; `testapp.3dsx`; `NOTICES.md`;
`SOURCE.md`; `SHA256SUMS`). Release notes: docs/release-notes/v0.1.0.md. Read `~/.claude/ip-publishing-policy.md`,
`docs/map/rules.md`, `docs/plans/phase-4.md` (sections 0, 5, 7, 8) and `docs/reviews/release-ip-legal.md` first.
**Never write a key or certificate byte value, an offset or a decode note in your report**; say 'the key blob' and
'the ClCertA arrays'. The machine checks already passed: re-run `python3 -I tools/release_check.py
runs/release/v0.1.0` and read its output (its needle checks were run by the main loop with a private file; their PASS
lines are in <I2's log>; `history-bytes` runs without it). Audit and grade (BLOCKER / SHOULD / INFO):
(1) the tree and the full history (`git log --all -p`) for ROMs, BIOS, saves, keys, certificates, system data, ripped
assets, commercial-game screenshots, decomp code, secrets, private data, key-material fragments or extraction hints
(consult section 9); grade the tracked claude.ai artifact links, the `/Users/...` paths in plans and reviews, and
`docs/research/spike-1-headless-core.md:18, 27-28` (it records the stock core's URL and sha256 as rules.md 2's
download record, not a script);
(2) the core binary in the zip: `keyblob_findings()` is empty on this exact file (check 2 proves the zip's dylib is
the gated one); no key loading; no MoltenVK; **no LibreSSL** (the drop list removed it from the source too); no
private strings (OpenSSL's compiled-in Homebrew directories, `OPENSSLDIR` `/opt/homebrew/etc/openssl@3` and
`ENGINESDIR`/`MODULESDIR` under `/opt/homebrew/Cellar/openssl@3/3.6.5/lib`, and the zipped `build.inputs`'
`openssl_prefix=`, a Homebrew path, are expected, not leaks); the compiled-in system archives against the consult's
section 5 (the five checks' results are in I's `runs/i/rows.md`, quoted in item 420);
(3) the Azahar source asset: complete corresponding source for the binary (built from this stripped tree plus the
patches; SOURCE.md and the note member), the note is neutral and holds **no hash of the key and certificate
headers** (consult section 2), nothing in it we may not re-host; `default_keys.h` carries a GPL header, which does not
make console keys shippable; and `core/PIN`'s `SRC_URL`, which still names Azahar's unchanged tarball as the build
input (phase-4.md risk 17): grade it;
(4) the OpenSSL tarball, `core/OPENSSL.md` and NOTICES' OpenSSL section against Apache-2.0 section 4, with NOTICES and
the GPLv3 text inside the zip (consult section 3);
(5) the test app: our own code and glyphs, no Nintendo assets, no `/Users/` strings;
(6) NOTICES.md: every linked component's licence text, the `src/` notices, faad2's Nero and Bakker lines, OFL-1.1
with Montserrat's line, Unifont's notice, the citra_system_archives notice with its four generator commits, never
'Nintendo's' archives; the snapshot asset;
(7) every claim in README.md, STATUS.md, the release notes and SOURCE.md: no overclaim; the README's first paragraph
says 'unofficial; not affiliated with or endorsed by the Azahar project'; no Azahar logo or image; no admission text;
nominative names only; no key or decryption instructions; no stock-core URL, hash or contents (the consult's section
7; fetch.sh no longer downloads it, unless Guy accepted the YELLOW: then grade the opt-in flag);
(8) the name and the fallback name in phase-4.md Q8.
Say **shippable** or **not shippable** for each of: the repo, its history, the core zip, the Azahar source asset, the
OpenSSL asset, the snapshot asset, the build-files asset, the test app, the notices and the docs' claims, with exact
remediations."

## 10. The builder's report (I1 and I4)

Gates 1-4 as printed (with `--plant-red`); `runs/i/rows.md` (with the five archive checks and the stock-core hits);
the asset table (name, size, sha256); the LINK and DEPS component lists and any table row you had to add (components
and `src/` notices); whether OSSL has a NOTICE; FORMULA's sha256 and whether the receipt named a homebrew-core commit;
whether SNAP held the font texts; the P17 hits you changed beyond 3.5's table; whether `-ffile-prefix-map` alone
cleared the test app; line counts per file and the longest function; the paths to `git add` with their map lines; the
rules.md rule 3 wording you propose; runners lines for `docs/map/runners.md`:
```
tools/mkrelease.sh v0.1.0                                    # stage the release in runs/release/v0.1.0/
python3 -I tools/release_check.py runs/release/v0.1.0        # step I's machine checks (--pre-push before a push)
python3 -I tools/mknotices.py --link <link.txt> --deps build-core/build --tree <build-src tree> --src <unpacked tree> --inputs build-core/build.inputs --openssl dl/openssl-src/openssl-3.6.5.tar.gz --sysarch dl/sysarch-src/citra_system_archives-f470e0c.tar.gz > NOTICES.md
tools/fetch.sh --moltenvk --headers --lazpy-core --testapp   # the README route: our core (the default path) and the test app
LAZ_STOCK_CORE=<Azahar's own core> .venv/bin/python -m pytest -q tests/python   # adds the core-comparison tests
```
lines for `docs/map/tools.md`; and a final **"Lessons and notes"** block for item 420. Never a byte value, an offset
or the needle file's path in the report.

## 11. Hours (agent wall time)

Builder 0.70 h (I0 0.13, I1 0.47, I4 0.1 if needed) and the commit 0.05 h: **0.75 h**; the as-built review is the
joint one in phase-4.md (0.2 h for H and I). Against revision 1's 0.65 h: review 2 net -0.02 h (B1, B4, S4 +0.06;
S2, S3, S9 -0.08); the note without hashes -0.01; no `--openssl-src` -0.02; P17's code and tests +0.06; the
consult's notices (OFL, Unifont, the archives, two copyright lines) +0.03; the five archive checks in I0 +0.02; the
snapshot asset +0.01; the standing checks (`history-bytes`, the `repo` additions) +0.03. The main loop's steps
(spike 2's rewording, G8b, the downloads, I2, I3, I5) are phase-4.md's 0.62 h. The xz pack, the clone's full suite
and the audit's reading are machine time; Guy's steps are his.

## 12. Review checklist (the joint opus as-built review)

1. `release_check` check 2 proves the zip's dylib equals CORE by sha256, then calls `gate_f2.keyblob_findings` with
   `build-core/` and `repo=` (no second set of windows); its plant fires through that function; checks 4-6 hold only
   what f1 lacks (S2).
2. NOTICES.md is generated; licence texts verbatim from SRC, OSSL and SNAP (or the named font files); every LINK and
   DEPS path classified by KEG's Cellar path; an unknown component, an unknown path, an `externals/libressl` path or
   an unknown `src/` notice exits 1; faad2's Nero and Bakker lines; OpenSSL's copyright line, Apache text and NOTICE
   status; OFL-1.1 with Montserrat's line; Unifont; the archives' generator commits read from the headers; never
   "Nintendo's"; the G4 sentence; the zip holds NOTICES.md and the GPLv3 text.
3. The source asset differs from TARBALL by exactly the dropped members (the prefix rule) and the note member; no
   `externals/libressl` member; the note names the three headers without hashes; `untar_checked.py` accepts it; two
   packs give the same bytes; `PIN-nokeys` matches it and names the note as its drop entry.
4. The OpenSSL asset equals upstream's tarball; `core/OPENSSL.md` quotes FORMULA, uses `LAZ_OPENSSL_PREFIX`, says
   Homebrew ships only its current version, and marks the recipe "not tested"; the snapshot asset equals SNAP.
5. Check 16 and the docs say macOS 15 or later; OpenSSL's Homebrew paths are expected NOTEs, not FAILs.
6. SOURCE.md and the release notes are honest and complete (where every piece of source is, the rebuild text, INPUTS'
   `cmake=` verbatim, both commit maps), with no admission text, no speed numbers, no key instructions, no core-zip or
   build-asset hash, no image.
7. `fetch.sh` keeps its helpers and its "download only if missing or wrong" rule; no flag means `--moltenvk
   --headers`; no `azahar-emu` string (or, under Q1's YELLOW, only in the opt-in branch); a `TBD` pin dies; gate 3's
   corrupted copy is refused and deleted.
8. P17: `_paths.py` and `azhost` default to `dl/lazpy-core/azahar_lazpy_libretro.dylib`; `stock_core` skips without
   `LAZ_STOCK_CORE` even under `LAZ_REQUIRE_EMULATOR=1`; no `dl/azahar/` path left in `host/`, `python/`, `tests/` or
   `tools/`; `test_paths.py` covers both; H's docs say the same (phase-h.md 12 item 5).
9. The test app: one Makefile line, no `-DNDEBUG`, 0 `/Users/` strings, the asserts still compiled in.
10. `release_check` covers rules.md 1 over the tree and the history, the identities, the needles without ever
    printing one, `history-bytes` without ever writing a window to disk or output, the long-`0xNN` and FUNDING and
    key-word checks, and `--pre-push`'s identity, tagger, clean-tree and docs checks.
11. Nothing committed, pushed or sent to GitHub; nothing written in MAIN; nothing run from inside a download;
    `build-core.sh` never run; no item file edited; no needle, needle-file path, byte value or offset anywhere in the
    diff or the report.
