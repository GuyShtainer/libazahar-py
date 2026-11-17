# Phase 7 plan, review 1 (opus, read-only)

Reviews `docs/plans/phase-7.md` revision 0 (11:25) against branch `port-win-v1` (1c8650f), main's tools, Makefile and
`.github/workflows/test.yml`, `docs/map/rules.md`, phase-v1 and phase-i, and the toolkit's pc-worker files. Started
2026-11-17 11:44 IST. Nothing was edited apart from this file. Nothing ran on the Mac except git, gh and file reads.
Read-only PowerShell queries on the PC: `wsl -l -v`, `wsl --status/--version`, the Lxss registry key, `.wslconfig`,
drive free space, free RAM, the vhdx size, and `pacman -Q`.

## 0. Facts this review relies on (measured today)

- **PC WSL:** Ubuntu is listed as `Stopped`, version 2, and the registry shows State=1 (installed). WSL is 3.0.5 and
  WslService is Running. The `ext4.vhdx` is 30.4 GB, on **C:**, last written 00:23. That fits the deliberate shutdown
  at 00:22 (guy-decisions.md, "Overnight defaults": "told b8 'WSL free'... Windows had 2.4 GB free with WSL holding
  12 GB"). So WSL is **stopped by choice, not broken**. I did not start it, so "it boots" is unverified. The toolkit
  docs say the distro is Ubuntu 26.04 with systemd (gpu-plan-brief.md:13).
- **WSL settings:** `.wslconfig` has `memory=12GB`, `swap=8GB` and `vmIdleTimeout=-1`, on a 16 GB PC. Windows had
  4.9 GB free RAM at 11:4x.
- **Free disk:** C: has **29.6 GB** free and D: has 2.4 TB. In A1, the OpenSSL and core builds grew the vhdx by about
  5 GB (lanes/A1.md:39-40, "deleting files inside ext4 does not give it back"). A1's stop lines were 37 GB, then
  34 GB.
- **Build time:** A1's OpenSSL plus core build ran from 22:45 to `build.exit 0` at 23:11, **about 26 minutes**
  (lanes/A1.md:7-11). It did not take 1.5 h.
- **MSYS2 on the PC** (`pacman -Q`): gcc 16.2.0-7, binutils 2.47, crt, headers and winpthreads 14.0.0.r598, zlib,
  make, git, curl, perl and xz. It has **no** clang, cmake, ninja, unzip, zip, or mingw python.
- **Upstream route:** Azahar builds its own Windows libretro core **in CI, as a Linux mingw cross build in a
  container on ubuntu-latest** (`azahar-emu/azahar/.github/workflows/libretro.yml:125-149`, image
  `reallibretroretroarch/libretro-build-mxe-win-cross-cores:mingw12`). Its desktop Windows builds are MSVC or MXE.
  None of them is native MSYS2.
- **macOS CI today** (run 44053264174, main, 09:11Z): on macos-15 with Python 3.10 and 3.14, it runs
  `fetch.sh --headers`, `make check` (clang --analyze), `make`, `make test-version`, and `make test-host`
  (307,973 checks). Then the venv and `pytest -m "not slow"`: **244 passed, 56 deselected**. It fetches no core and
  no MoltenVK, and runs no emulator. All 56 live tests are outside it.

## 1. Blockers

**[R1-B1] W5, W7 and W9 depend on WSL in a way that cannot pass as written.** (Steps W0, D4, D8, W5, W7, W9.)
- Evidence 1: W0's own gate wants "at least 30 GB on the WSL drive". The WSL drive is C:, which has 29.6 GB free.
  The vhdx grows about 5 GB per build and never shrinks.
- Evidence 2: WSL's 12 GB memory cap, with `vmIdleTimeout=-1`, on a 16 GB PC that four sessions share under the
  dynamic free-memory rule (2 GB + 0.6 GB per copy). WSL was shut down at 00:22 for exactly this reason.
- Evidence 3: W5 builds in `/tmp/lazpy-w5` and ends with `wsl --shutdown`. W7 restarts WSL and runs
  `tools/mkrelease.sh`, which reads `build-core/build/CMakeFiles/*` and the core (mkrelease.sh:27-36, 86-87). W9
  runs `release_check.py`, whose checks 2 and 8 read `build-core/build` (CMakeCache, `.o.d`, link files,
  `build.exit`) through `gate_f2.keyblob_findings` (gate_f2.py:179-216) and mknotices (release_check.py:330-332).
  On systemd Ubuntu, `/tmp` is emptied at every boot (tmp.conf `D /tmp`), and on recent releases it is a tmpfs. So
  the build tree that W7 and W9 need is gone after W5's shutdown.
- Fix: take the WSL-free route in section 7 (the core is built in GitHub CI and its build metadata is uploaded as
  an artifact). If WSL is kept:
  - Build in `/var/tmp/lazpy-w5` or `/opt/lazpy-w5`, which are neutral and survive a boot.
  - Do W5, W7's mkrelease and W9's release_check in WSL sessions that reuse that tree.
  - Make W0's floor A1's 34 GB on C:, checked before each WSL start, and apply the free-RAM rule before starting.

**[R1-B2] The 16-byte window search has no key arrays to search for.** (Steps D8, W5, W9.)
- D8 says "WSL holds the full source after W5". But W5 fetches only the nokeys source ("the nokeys source per
  core/PIN-nokeys").
- `gate_f2._window_findings` (gate_f2.py:82-95) and release_check check 13 (`make_windows`,
  release_check.py:567-580) both read `default_keys.h` and the two `ctr-common-1-*.h` headers. They read them from
  `dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/...` (SRC_REL, release_check.py:34), which is the reading
  copy of **Azahar's own key-bearing tarball** (core/PIN). The nokeys tarball has had those headers dropped
  (core/PIN-nokeys header comment).
- The gate fails loudly ("nothing was checked"), so it is not vacuous. But W5's check and W9's 16 of 16 cannot pass.
- Fix: whichever machine runs these two checks (the PC, per section 7) fetches core/PIN's `SRC_URL` and checks its
  `SRC_SHA256`. The file is used only as a reading copy: unpacked by `untar_checked.py`, never built. Write this
  into W5 (or W7) and into D8.

**[R1-B3] release_check cannot gate the reused Mac core on the PC.** (Steps W2b and W9; section 7.) W2b changes only
check 16 ("passes by sha-equality when vtool/lipo are absent"). On the PC, without the Mac's build tree and Homebrew,
these checks also cannot pass:
- check 2 keyblob: it needs the Mac core at `build-core/azahar_lazpy_libretro.dylib` and the Mac `build-core/build`
  tree (release_check.py:124-137).
- check 3: Mach-O `nm -gU` (release_check.py:786).
- check 5: `/usr/bin/otool -L` (release_check.py:787).
- check 6: `keg_findings`, which resolves `/opt/homebrew/opt/openssl@3` and FAILs under `--pre-push`
  (release_check.py:203-216).
- check 8: mknotices regenerating NOTICES.md from the Mac build tree.
- check 16: it also runs `vtool`/`lipo` on `build/libazhost.dylib` and `build/azhost`, the host, not only the core
  (release_check.py:685-690).

There is a second problem. mkrelease would regenerate the nokeys source asset with bsdtar's `@archive` syntax
(mkrelease.sh:73). GNU tar cannot do that, and another bsdtar or xz version gives different bytes. The plan promises
"same bytes as v1.0.0".

Fix: an explicit inherit mode (`--inherit v1.0.0`).
- The Mac zip, NOTICES.md, the nokeys source, the OpenSSL tarball, the citra snapshot, `testapp.3dsx` and
  libazahar-py-core-build-v1.0.0.tar.gz (see R1-B4) must each equal its line in v1.0.0's published SHA256SUMS.
  Fetch them by URL from the v1.0.0 page with sha checks.
- `git diff v1.0.0 -- NOTICES.md tools/build-core.sh core/` must be empty.
- Checks 2-6, 8 and 9 for the Mac side then print `NOTE inherited from the v1.0.0 gate (16/16)`. The Windows
  binary gets its own PE checks.
- The host minos and arch part of check 16 moves to test.yml as a step: `vtool -show-build build/libazhost.dylib`
  showing minos 15.0 and arm64.
- mkrelease copies these assets and builds only the Windows zip, SOURCE.md, NOTICES-windows-x64.md, the v1.1.0
  core-build asset and SHA256SUMS.

**[R1-B4] Hosting the Mac zip on the v1.1.0 page makes its own SOURCE.md wrong.** (Step D2, section 4.)
- mkrelease writes into each zip's SOURCE.md "Corresponding Source, all on this release page". Its item 4 names
  `libazahar-py-core-build-$TAG.tar.gz` (mkrelease.sh:83, 95, built at 132).
- So the byte-identical v1.0.0 Mac zip on the v1.1.0 page points to `libazahar-py-core-build-v1.0.0.tar.gz`. Section
  4 does not list that asset, so the claim inside a shipped binary's zip would be false on that page.
- Fix: upload v1.0.0's core-build asset byte-identical as well. Add it to section 4, `expected_assets()` and W9's
  asset-name gate. The top-level v1.1.0 SOURCE.md maps each zip to its own build-files asset.

**[R1-B5] W1a as written breaks the push rule and cannot be dispatched.** (Step W1a, and W3's re-run.)
- (a) It pushes a scratch branch, which is outside "main and the tag only".
- (b) A `workflow_dispatch` workflow can be dispatched only when its file exists on the default branch. A file that
  lives only on a scratch branch cannot be dispatched.
- (c) test.yml has `on: push` with no branch filter, so the scratch push also runs the full macOS job.
- (d) "every `host/**/*.c`" includes `host/plat/win_*.c`, which Darwin never compiles: `LIB_SRC` is `host/*.c` only
  (Makefile:5). It also misses `tests/host/*.c`, `tests/host/*.h` and `tests/test_version.c`, which the Mac's
  test-host does compile and which the branch changes (plat_test.h is new; six test files change).
- Fix: run W1a (and W3's re-run) on the PC with MSYS2 gcc:
  `gcc -E -P -undef -nostdinc -isystem <stub dir> -D__APPLE__=1 -D__MACH__=1 -D__arm64__=1 -D__aarch64__=1 -D__LP64__=1 -D__clang__=1 -D__STDC_VERSION__=201112L -Ivendor -Ivendor/include -Ihost`
  - Run it over `host/*.c tests/host/*.c tests/test_version.c` for v1.0.0 and for the branch tip.
  - `<stub dir>` holds an empty file for every system header either tree includes.
  - Both trees see identical stubs, so the diff is exactly the change the Mac compiler sees in our own code.
- Confirm after W4's push of main with one test.yml step on macos-15: real `clang -E` with `fetch-depth: 0` against
  `v1.0.0`, with the diff uploaded as an artifact. This uses no scratch branch.

## 2. Should fix

**[R1-S1] Pushing main at W7 breaks `fetch.sh` for everyone until W10.** (Steps W7, W8, W9.)
- REL_BASE is built from REL_TAG (fetch.sh:39-40). Setting `REL_TAG=v1.1.0` on pushed main makes the Mac zip and
  test-app URLs 404: draft assets are not public.
- That lasts until Guy publishes. W7c has no deadline, so it could be days.
- Separately, W8's fixes land after W7's clone_check, so the clone_check did not run on the commit that gets
  tagged. W9 reruns only release_check.
- Fix: no push at W7. Run clone_check on the PC from the local merge bundle (clone_check accepts a path, line 4),
  with `--release-base`.
- Rerun clone_check if W8's fixes touch anything outside `docs/reviews/`, `docs/status/` and `docs/hours.tsv`.
- Push main with the pins only in W9. W10's clone_check from the real URLs is the "fresh clone of GitHub main"
  proof, so reword section 1 to say that.

**[R1-S2] Push the tag only after both CI files are green on the release commit.** (Step W9.)
- W9 pushes main and the tag together, but the exit gate wants test-windows.yml green on that commit.
- Fix: push main, `gh run watch` both workflows until green, then push the tag, then `gh release create --draft`.

**[R1-S3] W2b is far bigger than 3.0 h, and it overlaps W2a on files.** (Steps W2b and W2a.)
- W2b ports eight tools: build-core-win64.sh with OpenSSL, gate_f2 PE, mknotices win64, mkrelease, release_check
  (16 checks, most of them Mac-bound, see R1-B3), fetch.sh, clone_check Windows mode, and docs_check. A realistic
  estimate is 5-6 h, or about 4 h with the R1-B3 inheritance cut.
- Fix: split it into two parallel sonnets with fixed file ownership.
  - W2b1 is the build route: build-core-win64.sh, the OpenSSL build, `tests/gate_f2.py`, mknotices win64, and the
    CI build workflow from section 7.
  - W2b2 is the release tools: mkrelease, release_check, fetch.sh, clone_check and docs_check.
- W2a gives up `tests/gate_f2.py`.
- Neither agent runs mkmap or edits `docs/map/*`. The main loop runs `mkmap` and `map_check` once at the merge, or
  the three branches conflict on `docs/map/gen/`.

**[R1-S4] gate_f2 cannot pass on a win64 build as it stands, and B2's masking makes it worse.** (Step W2b; findings
B2 and B9.)
- `_inputs_findings` wants `script=` to be the sha of `tools/build-core.sh` (gate_f2.py:118). A win64 build records
  build-core-win64.sh.
- The link check reads only `link.txt` (gate_f2.py:207-212). mingw keeps the libraries in `linkLibs.rsp` (branch
  build-core.sh:204-207).
- The linkage check runs `otool -L` (gate_f2.py:205).
- Masking `openssl_prefix=` as `<repo>/...` (B2) breaks `_cache_findings(build_dir, prefix)` and the
  `{prefix}/lib/libssl.a` match.
- W2b lists only the PE import check.
- Fix: `keyblob_findings(..., target)` picks the script file, link.txt + linkLibs.rsp, and `objdump -p` "DLL Name"
  lines in place of otool. It unmasks `<repo>` before matching.
- Better still, use a neutral real prefix (R1-S8). Then nothing needs masking.
- Start from the toolkit's `tools/pc/gate_f2_pe.py`, which is already self-tested on this DLL (A1.md:15-19), rather
  than writing from scratch.

**[R1-S5] The macOS-unchanged proof covers C only, and "the Darwin block" does not exist.** (Section 7, W1, W2a, W3;
owner condition 3.)
- main's Makefile has no `uname` conditional. Its top half is unconditionally Darwin, and it has no
  `-Wno-unused-result`; that flag was port-linux's.
- The branch already changes a line the Mac runs: `check:` gains `tools/check-obinary.sh` (Makefile:26). The owner
  asked for it (guy-decisions "57 on B1's report", item 4).
- The Python changes are Darwin-visible too: `kill_own_worker`'s signature, `slot.txt` written with
  `newline="\n"`, `read_text(encoding=...)`, `_paths.SUFFIX`, hold_slot and speed_table. macOS CI runs none of the
  56 slow tests that exercise them.
- Fix:
  - (a) Define "Darwin unchanged" for the Makefile as: `make -n all test-host test-version` prints identical
    commands on macos-15 CI for v1.0.0 and the release commit, and `check` differs by the one owner-requested line.
    W2a wraps the MINGW64 part in `ifneq (,$(findstring MINGW64_NT,$(shell uname -s)))` and leaves main's lines
    unchanged in the else branch.
  - (b) W1's review lists every Python line not under a `_WIN`/`win32` guard, each with a verdict.
  - (c) Add a best-effort `continue-on-error` macOS live job. It needs no secret, because the v1.0.0 core and test
    app are public: `fetch.sh --moltenvk --headers --lazpy-core --testapp`, `make`, the quickstart, then
    `pytest -m slow`. About 0.5 h to write. If the macos-15 runner's paravirtual Metal device runs MoltenVK, this
    becomes the macOS proof Q4 asks about. If it fails, STATUS keeps the planned sentence.

**[R1-S6] `make check` cannot pass on MSYS2 or on the Windows runner.** (W2a's gate, section 5.)
- `check` runs `clang --analyze ... $(CFLAGS)` (Makefile:25-30). The PC's MSYS2 has no clang.
- CFLAGS lacks the Windows defines and `-Ihost/plat`.
- Section 5 lists `make check` as a CI step and also says CI "cannot check clang --analyze", which contradicts it.
- Fix: on MINGW64, `check` runs check-obinary. If `mingw-w64-x86_64-clang` is present, it also analyses `host/*.c`
  and `host/plat/*.c` with WIN_CFLAGS. Install that package in CI only.
- W2a also says what `make test-host` and `make test-version` build on MINGW64 (the win test sources, without
  `host/sdcopy.c`).

**[R1-S7] Section 6's allowed-skip list is incomplete, so W4's and W7's gates fail as written or get read loosely.**
Skips the list does not name:
- `test_slots.py:94`: test_s5 skips on Windows by design; its twin runs instead.
- `test_arguments.py:49`: making a symlink needs Developer Mode or admin rights on Windows.
- `test_release_fixture.py:22`: skips unless a fixture is present, which W4 lacks.
- `test_api.py:109`: a timing skip.
- `test_profile_format.py:46`: skips when build/ is missing.

Fix: list the exact skip node ids allowed for each run (W4, W7, W10). Require `test_release_fixture` to run, not
skip, in W7. Say whether the PC's account can make symlinks.

**[R1-S8] D5's OpenSSL paths are fragile.**
- "OpenSSL's own mingw defaults (`C:/Program Files/...`)" with a `DESTDIR` install puts spaces in the path.
  build-core.sh passes `$SSL_ROOT` through `set --`, `grep -F` checks against link.txt, and CMake cache regexes.
- DESTDIR with a drive-letter prefix behaves differently between OpenSSL's Makefile and other tools.
- Whether the cross-build default prefix is really `C:/Program Files/OpenSSL` is not verified anywhere in the plan.
- Fix: `Configure mingw64 no-shared --prefix=/opt/lazpy/openssl-3.6.5-mingw64 --openssldir="C:/Program Files/Common Files/SSL"`.
  - The prefix is a real, neutral install directory with no spaces and no username. Then B2 needs no masking.
  - The build records the OPENSSLDIR, ENGINESDIR and MODULESDIR strings found in the DLL in build.inputs, and
    USING's CA row quotes them.
  - `core/OPENSSL.md` (shipped in the core-build asset) gets a Windows section; today it is Homebrew-only.

**[R1-S9] release_check's privacy scan does not know Windows paths.**
- `PRIVATE_RES` matches only `/Users/` for paths (release_check.py:218).
- The DLL's strings come from `/usr/bin/strings -a` alone (release_check.py:290-293, 785-788), which reads only
  8-bit text. Windows code often stores wide (UTF-16) strings.
- W5's ad hoc grep has these patterns, but W9's gate of record does not.
- Fix: add these patterns to `PRIVATE_RES`:
  - `[A-Za-z]:[\\/]Users[\\/]`
  - `/home/`
  - `/mnt/[a-z]/`
  - `/__w/` and `/github/home`, if the CI route is taken
- Add `strings -el` of the DLL to the texts. Plant-red cases for each.

**[R1-S10] Licence: plan the mingw runtime source by default rather than after W1b.**
- Our own settled text says "OpenSSL is statically linked and bundled, so it is not a System Library. Its source ...
  belong[s] in Corresponding Source" (docs/reviews/release-ip-legal.md:147). libstdc++, libgcc, winpthreads and the
  CRT are statically linked into the DLL the same way.
- The GCC Runtime Library Exception settles libstdc++'s own terms, but not whether GPLv3 §1 treats it as a System
  Library of the compiler. That is a real open question. If W1b says "ship", the release needs a late re-stage plus
  a re-audit, about 1 h.
- Fix: W1b keeps its questions, but W2b1/W5 prepare the source asset anyway:
  - The exact Ubuntu source packages `gcc-mingw-w64` (with its gcc-N-source) and `mingw-w64`, at the versions in
    build.inputs. `apt-get source` in the build environment works.
  - The Windows NOTICES carry the Debian `copyright` files verbatim (`/usr/share/doc/<pkg>/copyright` for the
    runtime and `mingw-w64-x86-64-dev` packages), plus COPYING3 and COPYING.RUNTIME, rather than hand-typed texts
    in mknotices.
  - The asset is dropped only if W1b and W8 both say it is not needed.
- Vulkan from System32, no MSVC runtime, and the OpenSSL Apache-2.0 handling are correct as planned. Add one W1b
  question: the Windows build may compile different Azahar externals than macOS, so must the Windows NOTICES list
  exactly the externals in its own `.o.d` set? Yes is the expected answer, and mknotices win64 already does that.
  Then make NOTICE_PHRASES (release_check.py:315-320) per platform.

**[R1-S11] Load-only on clean Windows belongs before the tag, not after publishing.** (Step W10.)
- W10 is too late to catch a missing runtime DLL.
- Fix: with section 7's CI route, add a second job to the build workflow. It runs on windows-2025, downloads the
  artifact, calls LoadLibrary, reads `retro_api_version` and `lazpy_*`, and fails on any load error. That covers it
  at W5.
- With WSL kept, run objdump's complete import table, including the delay-load imports, at W5, and leave W10's step
  as a re-check.

**[R1-S12] Gaps in fetch.sh and the shell on a fresh MSYS2.** (Steps W2b, W6.)
- fetch.sh needs `shasum` (fetch.sh:73), which comes from perl's `/usr/bin/core_perl`. clone_check's clean PATH
  ("MSYS2 plus the Windows Python") must include that folder, or fetch fails.
- MSYS2's default shell is now UCRT64. There, `pacman -S mingw-w64-x86_64-gcc` installs a gcc that is not on PATH.
- Fix:
  - `sha_of` falls back to `sha256sum` (coreutils, always present).
  - The README pacman line adds `curl`.
  - The Makefile stops with "open the MSYS2 MINGW64 shell" when `$MSYSTEM` is not MINGW64. That also enforces the
    single-CRT claim in section 4.
  - W2b checks `--release-base` as a `file://` URL with MSYS2's curl (`file:///D:/...` may need to be
    `file:///d/...`).

**[R1-S13] W7c would edit a shared deploy and could block the release with no end.** (Step W7c.)
- The PC deploy and STAMP belong to the PC-runner owner (eb). The users' jobs go through the toolkit's
  boot_shim/job_native path, not the README's Python path. So they prove core plus azhost.exe only.
- Fix: ask eb for a separate release-candidate deploy id rather than switching the default.
- Run W8 during the W7c wait; the plan's order, W7, then W7c, then W8, serialises them.
- Ask Guy whether phase-v1's no-deadline rule (D6) holds for 1.1.0, or set a time limit.

**[R1-S14] Some gates are vacuous or too weak.**
- W2b's `clone_check.sh --dry-run` only prints the hard-coded command strings (clone_check.sh:50). It proves
  nothing about the Windows mode.
- W5's "boot the test app once" is a smoke test. That is fine, but it is not counted as proof.
- Fix: call the dry run what it is. Add to W4 a real Windows-mode run of clone_check steps 1-2 (clone from the
  bundle, the `steps-windows` block up to `make test-host`) with the core part skipped. Then W7 is not the first
  real run of the script.

## 3. Nits

- **[R1-N1]** fetch.sh unzips `azahar_lazpy_libretro.dylib NOTICES.md SOURCE.md` (fetch.sh:155). Decide the member
  names in the Windows zip: either NOTICES.md with Windows content, or teach fetch the `-windows-x64` name. Make
  release_check's `ZIP_NAMES` (release_check.py:43) per platform.
- **[R1-N2]** "Non-blocking until W10, then blocking" means nothing without branch protection. Say "continue-on-error
  removed", or say that the release gate (R1-S2) is what blocks.
- **[R1-N3]** Section 4's table should list the OpenSSL build script, or say it is inlined in build-core-win64.sh.
- **[R1-N4]** The private needles reach W5's sonnet and the PC only on stdin, never in argv, a PC file or a log.
- **[R1-N5]** Q3's "about 2 hours of WSL" should be about 40 minutes (A1 took 26 minutes). W0 should record the
  distro release (26.04 per the toolkit docs). LxssManager showing Stopped is normal on WSL 2.x.
- **[R1-N6]** clone_check's Windows mode must never call bare `python3`: on the PC that is 3.7 or the Store alias.
  Use the venv's base interpreter, named once.
- **[R1-N7]** Section 6's ASCII-path limit: the README should say "clone into an ASCII path such as `C:\src`". A
  non-ASCII user name breaks a clone under the home folder.

## 4. Hour-saving pass (required)

| # | Suggestion | Step | Saves |
|---|---|---|---|
| H1 | Build the core in CI (section 7), or at least right-size W5: the build takes 26 minutes, not 1.5 h. No WSL pre-flight, no WSL restarts in W7 and W9 | W0, W5, W7, W9 | 1.3 h of work, plus no PC RAM or disk taken from other sessions |
| H2 | Inherit the Mac-side checks from v1.0.0 by sha (R1-B3) rather than porting vtool, otool, nm, the keg check and mknotices-Mac to Linux | W2b | 1.5 h |
| H3 | Copy v1.0.0's asset bytes from its published page (nokeys source, OpenSSL, snapshot, test app, Mac zip, Mac core-build). mkrelease builds only the Windows pieces, so no bsdtar `@archive` port and no byte-drift debugging | W2b, W7 | 0.5 h |
| H4 | W4 drops the full pytest on the private core. W7 runs the full suite on the release core from a clean clone. W4 keeps make check, test-host, the fast pytest and test_state_boot ×3 | W4 | 0.5 h, plus about 0.5 h of PC time |
| H5 | No interim push at W7 (R1-S1), so no stale-clone_check loop after W8 | W7, W8 | 0.2 h, plus a main that keeps working |
| H6 | Start W6 (docs) right after W1, beside W2a/W2b. It touches no W2 file; its gate runs after W4 | W6 | 1.25 h end to end |
| H7 | Run W8 during the W7c wait (R1-S13) | W8 | the users' wait time, end to end |
| H8 | Base gate_f2's PE mode on the toolkit's self-tested `gate_f2_pe.py`, and use Debian `copyright` files verbatim for the runtime notices | W2b1 | 0.3 h + 0.5 h |
| H9 | W1b brief: give ip-legal the settled OpenSSL text and ask only the delta (whether the GCC runtime is a System Library, and the source-package format) | W1b | 0.15 h |
| H10 | W1a on the PC with stub headers (R1-B5): no CI round trip and no scratch branch to delete | W1a, W3 | 0.1 h |

Total: about 4.5-5 h of work saved, which brings the plan to about 12-13 h, and about 2-3 h of wall time.
Re-estimate W2b (R1-S3) at the same time: the cuts mostly offset its under-estimate.

## 5. Ordering and parallelism

- W2a, W2b1 and W2b2 have fixed file ownership (R1-S3). The main loop alone runs mkmap and edits `docs/map/*` at the
  merge.
- W6 moves up, beside W2 (H6). W1b keeps the expensive slot during W2, which is correct.
- W5 waits for W4's commit (it records `head=`). With the CI route, the workflow file reaches main in W4's push and
  is dispatched right after it. W6's gate and W5 run in parallel.
- W8 runs beside W7c (H7). W9 starts when both are done.
- W9's order becomes: push main, CI green, push the tag, then the draft (R1-S2).

## 6. Answers to the brief's questions

- **Do the gates prove "Windows works for a fresh user"?** Mostly yes, once R1-S1, S7, S12 and S14 are fixed. The
  real fresh-user proof is W10's clone_check from the published URLs. W7 is the pre-release rehearsal.
- **Licence:** correct in shape (static OpenSSL Apache-2.0, the GCC Runtime Library Exception, winpthreads, the CRT,
  Vulkan from System32, no MSVC runtime). Two gaps: the Mac zip's own SOURCE.md on the v1.1.0 page (R1-B4), and the
  runtime source asset left to a late "only if" (R1-S10).
- **Mac-closed rule:** the plan obeys it, apart from W1a's branch push (R1-B5). Its macOS proof is weaker than it
  needs to be. Byte-identical core and script, plus the C preprocess diff, plus build-and-fast-tests CI leave the
  Python and Makefile changes unexercised on macOS. R1-S5's `make -n` diff, the Python line list and the public-core
  macOS live probe close most of that gap cheaply.

## 7. WSL: recommendation

WSL is **stopped, not broken**: registered, State=1, clean vhdx. Keeping it costs a 12 GB VM on a shared 16 GB PC,
it grows C: (29.6 GB free, under W0's own floor), and its `/tmp` does not survive the shutdown W5 ends with.

The options:
- (a) WSL as planned: proven toolchain (A1), but R1-B1.
- (b) Native MSYS2 (gcc 16.2, CRT 14): one toolchain with the host, on D:. But gcc 16 is untested on Azahar 2126.2,
  cmake and ninja are missing, the configure steps are slow, and the A1 fstat workaround is untested on CRT 14. Too
  much new risk for a release.
- (c) **Recommended: a `workflow_dispatch` job in GitHub CI.** It runs on ubuntu-latest inside an `ubuntu:26.04`
  container, the same distro and mingw-w64 packages as A1, and it is the route Azahar itself uses for its Windows
  libretro core.
  - Source: the nokeys source and OpenSSL come from the public v1.0.0 page, with sha checks.
  - Build: `build-core-win64.sh`.
  - In the job: gate_f2's non-window checks and mknotices win64.
  - Artifacts: the DLL, build.inputs, the Windows NOTICES, and a small build-meta tarball (CMakeCache.txt, link.txt,
    linkLibs.rsp, the `.o.d` list, configure.log, CMakeFiles compiler files, build.exit). release_check later reads
    them with a `--build-meta` flag.
  - A second job runs on windows-2025 and does the load-only test (R1-S11).
  - On the PC (MSYS2 with the Windows Python; no WSL): the window search with core/PIN's tarball as a reading copy
    (R1-B2), the needle and UTF-16 scans, the boot, W7's mkrelease and W9's release_check.
  - `gh run download` on the Mac is a GitHub operation. The bytes then go to the PC.
  - This needs the workflow on main, which W4's allowed push provides. It drops section 8's "no core build in CI"
    line: that line's reasons (1.5 h, the full source) no longer hold.
  - Cost: about 0.5 h to write, inside W2b1. It removes R1-B1 entirely.
  - Fallback if the container build fails: WSL with R1-B1's fixes (`/var/tmp`, 34 GB C: floor, free-RAM rule, one
    session). It is announced on the PC board, and never Mac.

Verdict: needs replan

Counts: 5 blockers (R1-B1 to R1-B5), 14 should (R1-S1 to R1-S14), 7 nits (R1-N1 to R1-N7).
