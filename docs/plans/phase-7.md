# Phase 7 plan: the Windows port proven (release v1.1.0)

Revision 1, 2026-11-17 11:48 IST, opus planner for the main loop (eb). Answers review 1
(`docs/reviews/phase-7-review-1.md`: 5 blockers, 14 shoulds, 7 nits, tags [R1-*]) and the main loop's decisions on
it. Revision 0 (11:25) is in git. Review 2 comes next. Item laz-700.

Guy, 2026-11-17: "update the repo so it says windows is ot proven and its a WIP. / and move forward so its windows
proven". The first half is done (a551d5f, pushed). This plan is the second half.

Guy, 2026-11-17, on pushing: "moev forward doesnt include push to github. but this time you can push to github".
Pushes in this phase are main and the v1.1.0 tag only, never a scratch branch [R1-B5]. Main is pushed only when the
push cannot break existing users (fetch.sh, section 2 D7) [R1-S1]. The tag is pushed only after both CI files are
green on its commit [R1-S2]. Publishing the GitHub release needs Guy's word (W10).

Guy, 2026-11-17, on the Mac: the Mac is closed to all 3DS work (emulators, builds, pytest, gates). It is for editing,
git, `gh` and ssh only (flag `~/.lazpy/PC_ONLY`). Every build and gate runs on the PC (MSYS2) or on GitHub's runners.
No step has a "rerun on the Mac" fallback. A `lane-pc` exit 77 means "not run": requeue it on the PC.

## 1. What "Windows proven" means (the exit gate)

All of these hold, each with its evidence file:
- Branch `port-win-v1` is reviewed (one full opus diff review), fixed, and merged into main.
- Before the tag: a clone of the release commit (from the local bundle) on the PC, following only the README's
  Windows steps, builds the host, passes `make test-host`, and passes the full pytest with `LAZ_REQUIRE_EMULATOR=1`,
  with only the skips that section 6 names (W7).
- After publishing: the same clone check from GitHub main and the real release URLs passes (W10). That is the "fresh
  clone of GitHub" proof [R1-S1].
- The Windows core is built in GitHub CI from the merged main, and loads on a clean windows-2025 runner with no extra
  runtime DLLs (W5) [R1-S11].
- `test.yml` and `test-windows.yml` are green on the tagged commit (W9) [R1-S2].
- The macOS side is shown unchanged with section 7's three parts, without running anything on the Mac.
- release-legal-audit says shippable for v1.1.0. `release_check.py --pre-push` passes every check on the PC.
- README, STATUS and USING say "Windows: proven on one PC" with the exact limits (section 6). No speed claims.

## 2. Decisions taken by default (review 2 or Guy may overrule; each is reversible until the tag push)

- D1. Version 1.1.0. Windows support is an addition, so it is a minor release (owner condition 1).
- D2. The Mac side of v1.1.0 is inherited from v1.0.0 by checksum [R1-B3, R1-B4]. These v1.0.0 assets are fetched
  from the v1.0.0 page, each checked against v1.0.0's published SHA256SUMS, and uploaded byte-identical: the Mac core
  zip (`ced9a362...`), `NOTICES.md`, the nokeys source, `openssl-3.6.5.tar.gz`, the citra snapshot, `testapp.3dsx`
  (`ba106998...`) and `libazahar-py-core-build-v1.0.0.tar.gz` (the Mac zip's SOURCE.md names it). Nothing is rebuilt
  for the Mac and nothing runs on the Mac. `git diff v1.0.0 -- NOTICES.md tools/build-core.sh core/PIN
  core/PIN-nokeys core/patches` stays empty.
- D3. `tools/build-core.sh` stays byte-identical to v1.0.0. The branch's win64 case moves into a new
  `tools/build-core-win64.sh`, with the OpenSSL build inlined in it [R1-N3]. (gate_f2 checks that build.inputs'
  `script=` equals the sha of the build script; see W2b1 for the per-target script [R1-S4].)
- D4. The Windows core is built in GitHub CI [R1-B1, review section 7c]: a `workflow_dispatch` workflow on main
  (`.github/workflows/core-win64.yml`), job 1 on ubuntu-latest in an `ubuntu:26.04` container with the A1 toolchain
  (mingw-w64 gcc-posix from Ubuntu's packages). Azahar builds its own Windows libretro core the same way (a Linux
  mingw cross build in a container). It builds from the merged main, so `head=` is the W4 commit. It uploads one
  artifact: the DLL, build.inputs, the Windows NOTICES, a build-meta tarball (CMakeCache.txt, link.txt, linkLibs.rsp,
  the `.o.d` list, configure.log, CMakeFiles compiler files, build.exit) and the mingw runtime source packages.
  Job 2 runs on windows-2025: it downloads the artifact and does the load-only test. The PC's old private core DLL
  (`EFD22238...`) never ships (finding B1).
- D4-fallback. Only if the container build fails twice for a reason not in our code: WSL on the PC, building in
  `/var/tmp/lazpy-w5` (it survives a WSL restart), started only when C: has at least 34 GB free (A1's floor) and the
  free-memory rule allows a 12 GB VM, one session, announced on the PC board, `wsl --shutdown` after. Never the Mac.
  [R1-B1, R1-N5]
- D5. OpenSSL for Windows: `Configure mingw64 no-shared --prefix=/opt/lazpy/openssl-3.6.5-mingw64
  --openssldir="C:/Program Files/Common Files/SSL"`, inside the CI container [R1-S8]. The prefix is a real neutral
  path with no spaces and no username, so build.inputs needs no masking (finding B2 closes). build.inputs records the
  OPENSSLDIR, ENGINESDIR and MODULESDIR strings found in the DLL; USING's CA row quotes them. `core/OPENSSL.md` gets a
  Windows section. Same source tarball as macOS (`a2157c28...`), from the v1.0.0 page.
- D6. No prebuilt Windows host binaries. Users build `libazhost.dll` and `azhost.exe` with MSYS2 `make`, as macOS
  users run `make`. (Open question Q2.)
- D7. fetch.sh and existing users [R1-S1]. `REL_TAG` becomes v1.1.0 and a new `REL_TAG_PREV=v1.0.0` is added. For
  an asset whose pinned sha is the same in both releases (the Mac zip, the test app), a 404 on `REL_TAG` retries
  `REL_TAG_PREV`, under the same sha check. So the pin commit can be pushed before Guy publishes without breaking any
  Mac user. The Windows zip has no fallback: until publishing, fetch says "v1.1.0 is not published yet". The rule
  "REL_TAG follows the newest tag" (phase-v1 section 1) still holds.
- D8. Windows fetch is the same `tools/fetch.sh`, run in the MSYS2 MINGW64 shell. No PowerShell twin.
- D9. The release tools run on the PC in MSYS2 with the Windows Python 3.10 (named once by `LAZ_WIN_PY`, the venv's
  base interpreter; never a bare `python3`, which on the PC is 3.7 or the Store alias) [R1-N6]: mkrelease (Windows
  mode), release_check, and gate_f2's 16-byte window search. `gh` runs on the Mac (a GitHub operation); bytes move
  between the Mac and the PC over ssh.
- D10. The key search reads Azahar's own full source tarball pinned in `core/PIN` (`SRC_SHA256 85c8b56f...`, 43 MB),
  fetched on the PC into `D:\lazpy\p7\keysrc\` (outside the repo), sha-checked and unpacked by `untar_checked.py`.
  It is a read-only copy: never built, never shipped, never committed. [R1-B2]
- D11. Users on the release candidate (W7c) have no deadline, as phase-v1's D6. W8 runs during the wait [R1-S13].
- D12. Owner conditions hold: main's Makefile lines stay as they are for macOS (cond 3, in the sense of section 7's
  `make -n` test [R1-S5]), `DEFAULT_CAP` stays 4 (cond 5), no Linux asset (cond 7).

## 3. Steps, in order

Each step gets an item under laz-700 (ids 701-714, created by W0). Hours book to `phase-7`. Evidence lives under
`runs/p7/<step>/` (gitignored) and is named in the item's Evidence line. "PC runner" means `tools/pc/lane-pc` or the
plain ssh runner in docs/map/runners.md. `$NEEDLES` is the private-needle list (local usernames on the Mac and the
PC, and Guy's real email). It lives only in the main loop's environment and reaches the PC only on stdin, as
`LAZ_PRIVATE_NEEDLES`. It never appears in argv, in a file on the PC, in a log or in an agent brief [R1-N4]. Agents
that need the needle scan get the main loop to run it.

Order: W0, W1a, W1, then W2a + W2b1 + W2b2 + W6 (four sonnets) with W1b in the expensive slot, W3, W4, W5, W7, then
W7c and W8 side by side, W9, W10. Never two expensive agents (opus, ip-legal, release-legal-audit) at once.

**W0. Items and pre-flight.** Owner: main loop. 0.3 h.
- Create items 701-714 and rewrite the handoff.
- Read-only PC pre-flight: free disk on C: and D:, free RAM, the MSYS2 packages, the venv's Python and its base
  interpreter, and whether the PC account can make symlinks (Developer Mode) [R1-S7]. Then, announced on the PC
  board, `pacman -S --needed zip unzip` in the PC's MSYS2 (mkrelease needs zip, fetch needs unzip).
- Gate: `python3 -I tools/status_check.py --strict-handoff` exit 0 (on the Mac: it reads only status files, no 3DS
  work). `runs/p7/w0/preflight.txt` lists every tool with its version and says yes or no for symlinks.

**W1a. Darwin-visible diff, on the PC.** Owner: main loop. 0.25 h. [R1-B5]
- On the PC with MSYS2 gcc, for v1.0.0 and for the branch tip: `gcc -E -P -undef -nostdinc -isystem <stubs>
  -D__APPLE__=1 -D__MACH__=1 -D__arm64__=1 -D__aarch64__=1 -D__LP64__=1 -D__clang__=1 -D__STDC_VERSION__=201112L
  -Ivendor -Ivendor/include -Ihost` over `host/*.c tests/host/*.c tests/test_version.c` (the files the Mac compiles).
  `<stubs>` holds an empty file for every system header either tree includes, the same for both trees. The diff is
  exactly the change the Mac compiler sees in our own code.
- Also `make -n all test-host test-version check` with MSYS2's make, in both trees: the commands the Mac's make would
  print (main's Makefile has no OS test; the branch's top half is the same). [R1-S5]
- Gate: `runs/p7/w1a/darwin-pp.diff` and `runs/p7/w1a/make-n.diff` exist; the script that made them is
  `runs/p7/w1a/darwin_pp.sh`.

**W1. Full diff review of port-win-v1.** Owner: opus agent (the one expensive slot). 1.25 h.
- Reads `git diff main...port-win-v1` (56 files, +1653/-134) for correctness on Windows and for macOS sameness.
  Inputs: W1a's two diffs, the owner conditions, USING's 1.0 promise, findings B1-B13 (section 9) and review 1.
- Gate: `docs/reviews/phase-7-diff-review.md` exists. Every finding has a tag (P7-R1-n), a severity and a file:line.
  It has three sections, each complete:
  - "Darwin-visible C": every hunk of `darwin-pp.diff`, each with a verdict.
  - "Darwin-visible Makefile": every line of `make-n.diff`. The one allowed change is `check:` gaining
    `tools/check-obinary.sh` (owner request, guy-decisions "57 on B1's report", item 4).
  - "Darwin-visible Python": every changed Python line that is not under a `_WIN` or `sys.platform == "win32"` guard
    (for example `kill_own_worker`'s signature, `slot.txt` with `newline="\n"`, `read_text(encoding=...)`,
    `_paths.SUFFIX`, hold_slot, speed_table), each with a verdict and the test that covers it. [R1-S5]
  - It confirms owner conditions 3 and 5 by quoting the lines.

**W1b. Licence delta.** Owner: ip-legal agent (expensive slot, while W2 runs). 0.25 h. [R1-S10, H9]
- The brief gives the settled OpenSSL text (docs/reviews/release-ip-legal.md:147) and asks only the delta:
  (1) libstdc++, libgcc, winpthreads and the mingw-w64 CRT are statically linked into the DLL. Are they GPLv3 §1
  System Libraries, or must the exact Ubuntu source packages ship? (2) Must the Windows NOTICES list exactly the
  externals in the Windows build's own `.o.d` set? (3) The words "Windows" and "NVIDIA" in docs (nominative use).
  (4) No Vulkan loader and no MSVC runtime ship: does that need anything more?
- Gate: `docs/reviews/phase-7-ip-legal.md` answers each question with yes, no, or a named action. Durable findings
  go to the learn skill's `references/ip-law-and-publishing.md`.

File ownership in W2 [R1-S3]. Each W2 agent works in its own worktree, made by the main loop at the port-win-v1 tip.
None of them runs `mkmap` or edits `docs/map/*`; the main loop does that once at the merge. Agents never commit on
main; the main loop merges their branches. Their tests run on the PC through the PC runner (exit 77: requeue).

**W2a. Fixes: host, Python, tests, Makefile, CI.** Owner: sonnet agent, worktree `lazpy-p7a`. 2.0 h.
- Owns: `host/`, `python/`, `tests/python/`, `tests/host/`, `tests/test_version.c`, `Makefile`,
  `.github/workflows/test.yml`, `.github/workflows/test-windows.yml`, `.github/workflows/macos-live.yml`. Not
  `tests/gate_f2.py`.
- The W1 findings in those files.
- Makefile [R1-S5, R1-S6, R1-S12]: `HOST_OS ?= $(shell uname -s)`. The MSYS2 part sits in `ifneq (,$(findstring
  MINGW64_NT,$(HOST_OS)))`. Main's lines stay unchanged in the else branch. On MINGW64:
  - It stops with "open the MSYS2 MINGW64 shell" when `$MSYSTEM` is not `MINGW64` (one C runtime, msvcrt).
  - The defaults are `WIN_CC=gcc` and `ZLIB_PREFIX=/mingw64` (finding B6).
  - Plain `make` builds `build/libazhost.dll` and `build/azhost.exe`, the paths Python looks in (finding B5).
  - `make check` runs check-obinary. If clang is present, it also analyses `host/*.c` and `host/plat/*.c` with the
    Windows flags.
  - `make test-host` and `make test-version` build the Windows test sources (without `host/sdcopy.c`).
  - The WSL cross build (`make win64`) keeps `build/win64/`.
- `test-windows.yml`, as in section 5 (finding B10). No `continue-on-error`. The tag gate (W9) is what blocks
  [R1-N2].
- `test.yml` gets one step on macos-15: `make -n all test-host test-version check` for a `v1.0.0` checkout
  (`fetch-depth: 0`) and for HEAD, diffed. The only allowed difference is the check-obinary line. Another step checks
  the host: `vtool -show-build build/libazhost.dylib` shows minos 15.0 and arm64 (moved from release_check check 16
  [R1-B3]).
- `macos-live.yml`: best-effort, `continue-on-error`, on push to main and `workflow_dispatch`. It needs no secret,
  because the v1.0.0 core and test app are public: `fetch.sh --moltenvk --headers --lazpy-core --testapp`, `make`, the
  quickstart, then `pytest -m slow`. [R1-S5]
- Gate, on the PC in a clean MSYS2 MINGW64 shell in the synced tree: `make check && make && make test-host && make
  test-version`, then `$LAZ_WIN_PY -m pytest -q -m "not slow" tests/python` from the venv. Also on the PC:
  `make -n HOST_OS=Darwin all test-host test-version check` equals v1.0.0's except the check-obinary line. Logs in
  `runs/p7/w2a/`.

**W2b1. Fixes: the Windows core build route.** Owner: sonnet agent, worktree `lazpy-p7b1`. 2.5 h.
- Owns: `tools/build-core-win64.sh`, `tools/toolchain-win64.cmake`, `tools/build-core.sh` (back to v1.0.0 bytes),
  `.github/workflows/core-win64.yml`, `tests/gate_f2.py`, `tools/mknotices.py`, `core/OPENSSL.md`.
- `build-core-win64.sh`: the branch's win64 route plus the OpenSSL build (D5). build.inputs records `target=win64`,
  `head=`, `script=` (the sha of `build-core-win64.sh`), `openssl_prefix=/opt/lazpy/openssl-3.6.5-mingw64`, the
  OPENSSLDIR, ENGINESDIR and MODULESDIR strings, `dpkg-query -W` lines for the mingw-w64, gcc, binutils, cmake and
  ninja packages, and every GCC ident found in the DLL, each with its package (finding B4).
- `core-win64.yml` (D4): the two jobs. Actions pinned by sha. The container enables `deb-src` and runs `apt-get
  source gcc-mingw-w64 mingw-w64` (plus the gcc-N-source package it names) at the versions in build.inputs, packed as
  `mingw-w64-runtime-source.tar`, so the asset is ready whatever W1b says [R1-S10]. The windows-2025 job loads the DLL
  with `LoadLibrary` (a short ctypes script), reads `retro_api_version` and every `lazpy_*` export, and fails on any
  load error [R1-S11]. In the container: gate_f2's checks that need no key source, and mknotices win64.
- `tests/gate_f2.py` [R1-S4, H8]: `keyblob_findings(..., target)`, starting from the toolkit's self-tested
  `tools/pc/gate_f2_pe.py`. For win64 it uses `build-core-win64.sh` as the script, reads link.txt and linkLibs.rsp,
  and replaces otool with `objdump -p` "DLL Name:" lines (a stdlib PE parser if objdump is absent), against the
  allow-list ADVAPI32, bcrypt, CRYPT32, KERNEL32, msvcrt, ole32, SHELL32, USER32, WINMM, WS2_32. Delay-load imports are
  read too. The 16-byte window search runs on the DLL bytes, with the key source from D10.
- `tools/mknotices.py` win64 mode: reads the Windows build-meta (`.o.d` list, link files), knows the mingw-w64
  system prefixes, and lists only the externals in that set. The runtime components (libstdc++, libgcc, winpthreads,
  mingw-w64 CRT) carry the Debian `copyright` files verbatim, plus COPYING3 and COPYING.RUNTIME [R1-S10, H8].
- Gate: gate_f2's self-test (planted reds: wrong script sha, a non-allowed import, a missing linkLibs.rsp library, a
  planted 16-byte key window) passes on the PC with the toolkit's known DLL; `git diff v1.0.0 -- tools/build-core.sh`
  is empty; `actionlint` (or `gh workflow view` after W4) shows no error in `core-win64.yml`. Logs in `runs/p7/w2b1/`.

**W2b2. Fixes: the release tools.** Owner: sonnet agent, worktree `lazpy-p7b2`. 2.5 h.
- Owns: `tools/mkrelease.sh`, `tools/release_check.py`, `tools/fetch.sh`, `tools/clone_check.sh`,
  `tools/docs_check.py`.
- `mkrelease.sh --inherit v1.0.0` [R1-B3, H3]: fetches the seven D2 assets from the v1.0.0 page, checks each against
  v1.0.0's SHA256SUMS, and copies them. It builds only the Windows zip, `NOTICES-windows-x64.md`, the top-level
  SOURCE.md, `libazahar-py-core-build-v1.1.0.tar.gz`, the runtime source asset and SHA256SUMS. No bsdtar. The Windows
  zip's members are `azahar_lazpy_libretro.dll`, `NOTICES.md` (Windows text), `SOURCE.md` (Windows text),
  `LICENSE`, `COPYING-azahar.txt` and `build.inputs` [R1-N1]. The top-level SOURCE.md maps each zip to its own
  build-files asset (v1.0.0's for the Mac zip, v1.1.0's for the Windows zip) [R1-B4].
- `release_check.py`:
  - `--inherit v1.0.0`: the seven inherited assets must equal v1.0.0's SHA256SUMS lines, and D2's `git diff` must be
    empty. Then checks 2-6, 8, 9 and 16 print `NOTE inherited from the v1.0.0 gate (16/16)` for the Mac side.
    [R1-B3]
  - The Windows core gets its own checks: gate_f2 win64 (keyblob, PE x64 machine, imports, no `.debug_*` sections),
    notices, needles.
  - `--build-meta DIR` (the CI build-meta) and `--src DIR` (D10's key source) replace the `build-core/build` and
    `SRC_REL` defaults.
  - `expected_assets()`, `ZIP_NAMES` and `NOTICE_PHRASES` per platform [R1-N1, R1-S10].
  - `PRIVATE_RES` adds `[A-Za-z]:[\\/]Users[\\/]`, `/home/`, `/mnt/[a-z]/`, `/__w/`, `/github/home`; the DLL's text
    adds `strings -el` (UTF-16). Each new pattern gets a planted-red case. [R1-S9]
  - Tools are found with `shutil.which`, never `/usr/bin/...`, so the script runs under the Windows Python.
  - `pins_findings` checks `REL_TAG`, `REL_TAG_PREV`, `LAZPY_CORE_ZIP_WIN` and `LAZPY_CORE_SHA_WIN`.
- `fetch.sh`: on MINGW64 (`uname -s`) it picks the Windows zip and sha and unpacks the `.dll`; `--moltenvk` says "not
  needed on Windows". `sha_of` falls back to `sha256sum` [R1-S12]. D7's `REL_TAG_PREV` retry.
- `clone_check.sh` Windows mode (chosen by `uname -s`). It runs the README's `steps-windows` block in a clean
  environment. That environment keeps only `SYSTEMROOT`, `WINDIR`, `LOCALAPPDATA`, `TEMP`, `TMP`, `USERPROFILE`,
  `HOME`, `MSYSTEM=MINGW64`, and a PATH of `/mingw64/bin:/usr/bin:/usr/bin/core_perl` plus `$LAZ_WIN_PY`'s folder
  [R1-S12, R1-N6]. There is no `nice`. The full pytest runs with `LAZ_REQUIRE_EMULATOR=1`. A new `--until host`
  stops after `make test-host` [R1-S14]. `--release-base` is tested with MSYS2 curl as `file:///D:/...`, and the
  form that works is written in runners.md [R1-S12].
- `docs_check.py --block windows` and the `steps-windows` marker check.
- Gate, on the PC: `$LAZ_WIN_PY -I tools/release_check.py --plant-red` exit 0, with each new planted case failing as
  expected. `fetch.sh` run against a `file://` base without the v1.1.0 Mac zip falls back to the v1.0.0 path and
  passes the sha check. `clone_check.sh --dry-run` prints the Windows-mode commands. That is a listing, not proof
  [R1-S14]; W4 runs it for real. Logs in `runs/p7/w2b2/`.

**W6. Docs, version, release notes.** Owner: sonnet agent (edits only, on the Mac), worktree `lazpy-p7d`. 1.0 h.
Starts right after W1, beside W2 [H6]. Its commit stays local until W9.
- Owns: `README.md`, `STATUS.md`, `docs/USING.md`, `docs/release-notes/v1.1.0.md`, `pyproject.toml`,
  `python/libazahar/__init__.py` (the version line only), `docs/tools.md`, `docs/map/runners.md` text (not
  `docs/map/gen/`).
- Version 1.1.0. README: a Windows section with a `<!-- docs_check: steps-windows -->` block. The steps:
  - Install MSYS2 and open the MINGW64 shell.
  - `pacman -S --needed make git curl unzip mingw-w64-x86_64-gcc mingw-w64-x86_64-zlib`.
  - Install Python 3.10 or newer from python.org.
  - Clone into an ASCII path such as `C:\src` [R1-N7].
  - `sh tools/fetch.sh --headers --lazpy-core --testapp`, `make`, `make test-host`.
  - Make a venv with that Python, `pip install -e .`, and run the quickstart.
- STATUS: Windows "proven on one PC" with the limits, and section 7's macOS sentence.
- USING: a Windows section with section 6's differences table.
- Gate (after W4, on the PC through the PC runner): `$LAZ_WIN_PY -I tools/docs_check.py` exit 0.

**W3. Check of the fix diff.** Owner: opus agent. 0.75 h. After the main loop merges W2a, W2b1, W2b2 and W6 into a
local integration branch `p7-int` (from port-win-v1) and runs `python3 -I tools/mkmap.py` once.
- Reads only the W2/W6 commits against each W1 finding and each R1 finding they claim. The main loop reruns W1a's two
  diffs on `p7-int` (the PC, MSYS2) for it.
- Gate: `docs/reviews/phase-7-fix-check.md` gives each P7-R1 finding "fixed", "not fixed" or "moved", with the commit.
  Zero "not fixed" blockers. `make-n.diff` differs from v1.0.0 only by the check-obinary line.

**W4. Merge and push main (with no release claims).** Owner: main loop. 1.0 h.
- Merge `p7-int` minus the W6 commit into main locally with `--no-ff`, commit as the no-reply identity. The W6
  commit stays on `p7-int` for W9. Run `mkmap` and `map_check`. Bundle main to the PC.
- PC gates on the merge commit, in a fresh tree from the bundle (`D:\lazpy\p7\w4`): `make check && make && make
  test-host && make test-version`, the fast pytest, and `test_state_boot` alone three times on a quiet PC (the owed
  state-restore rerun) [H4]. Then `clone_check.sh --until host --repo <bundle> --branch main --out D:/lazpy/p7/w4cc`:
  the first real Windows-mode run [R1-S14].
- Push main. This is safe for users: fetch.sh still says v1.0.0, and README still says Windows is a work in progress.
  Then watch CI with `gh run watch`.
- Gate: the PC logs show 0 failed. `test_state_boot` passes 3/3. `D:/lazpy/p7/w4cc/rc` = 0. On the merge commit,
  `gh run list --branch main --limit 3` shows test.yml green, including the `make -n` and vtool steps, and
  test-windows.yml green. If one is red, fix on main before W5. macos-live.yml's result is recorded either way.

**W5. Build the Windows core in CI, then check it on the PC.** Owner: sonnet agent (drives `gh` on the Mac and the
PC runner). 0.75 h of work; the CI build itself takes about 30-40 minutes. [R1-B1, R1-B2, R1-S11, H1]
- `gh workflow run core-win64.yml --ref main`, then `gh run watch`. Both jobs must be green: the build, and the
  load-only test on windows-2025.
- `gh run download` on the Mac (a GitHub operation), then copy it to the PC (`D:\lazpy\p7\w5\`) over ssh.
- On the PC, in MSYS2:
  - Fetch the D10 key source to `D:\lazpy\p7\keysrc\`, sha-checked.
  - Run gate_f2 win64 with `--src` and `--build-meta` (the window search included).
  - The main loop runs the needle scan with `$NEEDLES` on stdin. It covers `strings -a` and `strings -el` of the DLL,
    and also build.inputs and the NOTICES.
  - Boot the test app once with the W4 host. That is a smoke test, not proof [R1-S14].
- Gate: `runs/p7/w5/checks.txt` holds every PASS line. The CI run id and the artifact's sha256 are recorded. The
  build.inputs `head=` equals the W4 commit. The needle scan has 0 hits. Any GCC ident that has no package line
  blocks.
- If the build fails twice for a reason outside our code: D4-fallback.

**W7. Stage the release and prove the clone, before any release push.** Owner: main loop. 1.0 h. [R1-S1]
- Stage on the PC in MSYS2: `sh tools/mkrelease.sh --inherit v1.0.0 --win-artifact D:/lazpy/p7/w5 --out
  D:/lazpy/rel/v1.1.0`.
- Fill the fetch.sh pins on `p7-int`'s W6 commit line: `REL_TAG=v1.1.0`, `REL_TAG_PREV=v1.0.0`,
  `LAZPY_CORE_ZIP_WIN` and `LAZPY_CORE_SHA_WIN` (the Mac pin and `TESTAPP_SHA` are unchanged). Merge it into local
  main as the candidate release commit. Do not push.
- Bundle it to the PC. On the PC: `sh tools/clone_check.sh --repo <bundle> --branch main --out D:/lazpy/p7/w7
  --release-base <file URL of D:/lazpy/rel/v1.1.0>`. This runs the README Windows steps, `make test-host`, the
  quickstart, and the full pytest with `LAZ_REQUIRE_EMULATOR=1`, `LAZ_STOCK_CORE=C:/lazpy/probe/azahar_libretro.dll`
  and the v1.0.0 release fixture copied into the clone's `runs/release-fixtures/`. Announce it on the PC board first:
  it starts up to 4 copies.
- `$LAZ_WIN_PY -I tools/release_check.py D:/lazpy/rel/v1.1.0 --inherit v1.0.0 --build-meta ... --src ...` (without
  `--pre-push` yet), with `$NEEDLES` on stdin.
- Gate: `D:/lazpy/p7/w7/rc` holds 0. The pytest log's skips are exactly section 6's W7 list.
  `test_release_fixture` ran and passed; if not, its failure is a documented difference in the release notes, signed
  off in W8. release_check prints no FAIL.

**W7c. Users on the release candidate.** Owner: main loop (eb, the PC-runner owner). 0.3 h of ours. Beside W8.
[R1-S13]
- Make a separate release-candidate deploy id with the W7 host and the W5 core. The default deploy is not switched.
  Ask Gen3D and 3DPlatinum to run their next normal job on that id. Note what it proves: the core and `azhost.exe`
  through the toolkit's job path, not the README's Python path, which W7 covers.
- Gate: each project's job log line names the release-candidate deploy id and says PASS; quoted in the item. No
  deadline (D11).

**W8. Legal audit.** Owner: release-legal-audit agent (the expensive slot). 0.75 h, plus 0.5 h of fixes. Runs beside
W7c [H7].
- The brief is phase-i section 9.2, plus: the inherited v1.0.0 assets and their sha proof, the Windows zip, the
  runtime source asset and W1b's answers, the needle and UTF-16 scans, the "Windows proven" wording in
  README/STATUS/USING, and the history since v1.0.0.
- Fixes go in, then the main loop re-stages with mkrelease. If a fix touches anything outside `docs/reviews/`,
  `docs/status/` and `docs/hours.tsv`, W7's clone_check runs again on the new commit [R1-S1].
- Gate: `docs/reviews/release-legal-audit-v1.1.0.md` says shippable. The runtime source asset is dropped only if W1b
  and W8 both say it is not needed [R1-S10].

**W9. Final gate, push main, CI green, tag, draft.** Owner: main loop. 0.5 h. [R1-S2]
- On the PC: `$LAZ_WIN_PY -I tools/release_check.py D:/lazpy/rel/v1.1.0 --pre-push --inherit v1.0.0 ...`, with
  `$NEEDLES` on stdin. Every check PASSes or prints the inherited NOTE.
- Push main with the release commit. D7 makes this safe before publishing. Then `gh run watch` until both test.yml
  and test-windows.yml are green on that commit. If one is red, fix it, re-gate and push again. No tag before green.
- Tag `v1.1.0` (annotated, no-reply identity) on that commit and push the tag.
- Copy the staged folder from the PC to the Mac over ssh. Then `gh release create v1.1.0 --draft --verify-tag
  --notes-file docs/release-notes/v1.1.0.md` with every asset.
- Gate: `gh release view v1.1.0 --json isDraft,assets` shows a draft with exactly section 4's asset names. `gh api
  repos/GuyShtainer/libazahar-py/releases --jq '...assets[] | [.name,.digest]'` gives each asset's sha256 from
  GitHub. It must equal the line in the PC's SHA256SUMS: this is the copy check, and it needs no hashing on the Mac.
  `git diff <W4 commit> v1.1.0 -- tools/build-core-win64.sh tools/toolchain-win64.cmake core/` is empty, so the
  CI-built DLL's `script=` still matches.

**W10. Guy publishes; post-publish checks.** Owner: Guy publishes; then the main loop. 0.3 h.
- On the PC:
  - `curl` every asset from the real URLs into a new folder and check SHA256SUMS.
  - Run `clone_check.sh` from `https://github.com/GuyShtainer/libazahar-py`, branch main, with no `--release-base`.
    This is the fresh-clone-of-GitHub proof.
- Gate: `runs/p7/w10/` holds the checksum output and clone_check's `rc` = 0. Item 700 moves to done.

## 4. The v1.1.0 assets and their licences

| Asset | What | Licence and source |
|---|---|---|
| `azahar_lazpy_libretro-2126.2-lazpy.2-macos-arm64.zip` | v1.0.0 bytes (`ced9a362...`), inherited | as v1.0.0 |
| `libazahar-py-core-build-v1.0.0.tar.gz` | v1.0.0 bytes, inherited; the Mac zip's SOURCE.md names it [R1-B4] | GPLv3 (the Mac build scripts) |
| `NOTICES.md` | v1.0.0 bytes, inherited (the Mac notices) | |
| `azahar-unified-source-2126.2-lazpy-nokeys.tar.xz` | v1.0.0 bytes, inherited; the core's corresponding source on both platforms | GPLv3 |
| `openssl-3.6.5.tar.gz` | v1.0.0 bytes, inherited | Apache-2.0 |
| `citra_system_archives-f470e0c.tar.gz` | v1.0.0 bytes, inherited | as v1.0.0 |
| `testapp.3dsx` | v1.0.0 bytes (`ba106998...`), inherited | ours |
| `azahar_lazpy_libretro-2126.2-lazpy.2-windows-x64.zip` | the DLL, NOTICES.md (Windows), SOURCE.md (Windows), LICENSE, COPYING-azahar.txt, build.inputs | GPLv3 (Azahar, ours); OpenSSL Apache-2.0; libstdc++ and libgcc GPLv3 + Runtime Exception; winpthreads MIT-style; mingw-w64 CRT ZPL and public domain |
| `NOTICES-windows-x64.md` | the Windows zip's NOTICES.md, also on the page | |
| `libazahar-py-core-build-v1.1.0.tar.gz` | `git archive` of `core`, `tools/build-core-win64.sh` (the OpenSSL build is inlined in it [R1-N3]), `tools/toolchain-win64.cmake`, `tools/untar_checked.py`, `.github/workflows/core-win64.yml` | GPLv3 (the scripts that control compilation) |
| `mingw-w64-runtime-source.tar` | Ubuntu source packages `gcc-mingw-w64` (with its gcc source) and `mingw-w64`, at build.inputs' versions; dropped only if W1b and W8 both say so [R1-S10] | as packaged (GPLv3 + RLE, ZPL, MIT-style) |
| `SOURCE.md` | each binary to its source: Mac zip to the v1.0.0 build-files asset, Windows zip to the v1.1.0 one | |
| `SHA256SUMS` | sha256 of every asset | |

What the binaries link:
- The core DLL imports only Windows system DLLs: ADVAPI32, bcrypt, CRYPT32, KERNEL32, msvcrt, ole32, SHELL32,
  USER32, WINMM, WS2_32 (seen on the private build; W5's gate_f2 checks the release build, delay-loads included).
  libstdc++, libgcc and winpthreads are static. msvcrt.dll is a Windows system library. No MSVC runtime is used or
  shipped. The windows-2025 load-only job proves that no other DLL is needed.
- OpenSSL 3.6.5 is static, built in the container by `build-core-win64.sh` (D5).
- Vulkan: the host loads `vulkan-1.dll` from System32 only. On the PC that is the loader the NVIDIA driver installs
  (1.4.341, driver 610.88). Nothing Vulkan ships. Mesa dzn is not used (it was the old WSL route and drew 3D markers
  black).
- The host (not shipped) is built by the user with MSYS2 MINGW64 gcc, `-static -static-libgcc`, zlib static from
  `/mingw64`. It imports bcrypt, KERNEL32 and msvcrt. The host and the core share one C runtime (msvcrt). The
  Makefile refuses other MSYS2 shells (UCRT64 and the rest) [R1-S12].
- Corresponding source: every shipped binary's source is on the v1.1.0 page (the rows above) and in the repo at the
  tag. release-legal-audit (W8) gates this before the tag push.

## 5. CI

`test-windows.yml` runs on `windows-2025`. Its actions are pinned by sha: `actions/checkout`, `actions/setup-python`
(3.10 and 3.14), and `msys2/setup-msys2` (its sha is recorded in W2a with `gh api`). It uses the MINGW64 environment
with `path-type: inherit`, so the Windows Python is visible, and installs the README's pacman packages plus
`mingw-w64-x86_64-clang` for the analyser [R1-S6].
- Steps: `sh tools/fetch.sh --headers`, `make check`, `make`, `make test-version`, `make test-host`, `pip install -e .
  pytest numpy`, `python -m pytest -q -m "not slow" tests/python`.
- It checks: that the README's package list builds the host on a clean machine; the host C tests (about 308,000
  checks); check-obinary and clang analysis of the Windows sources; and the Python layer without a core (paths, the
  slot lock, worker start, options, input scripts).
- It cannot check: booting the core, frames, screenshots, states, the pool, timing, or anything that needs a GPU. The
  runners have no GPU and no Vulkan driver, so these are proven only on the PC (W4, W7, W10).

`core-win64.yml` builds the core and runs the load-only test (D4, W5). It runs on `workflow_dispatch` only.

`test.yml` (macos-15) gains the `make -n` diff step and the vtool step (W2a). `macos-live.yml` is best-effort
(section 7).

Blocking: there is no branch protection. A red run blocks because W9 pushes the tag only after test.yml and
test-windows.yml are green [R1-N2].

## 6. Version, the 1.0 promise on Windows, and the limits

v1.1.0. The 1.0 promise (USING top, phase-v1 section 1) holds on Windows. These differences are documented in a USING
table:
- File names: `libazhost.dll`, `azhost.exe`, `azahar_lazpy_libretro.dll`.
- `LAZ_MVK` names the Vulkan loader. The default is `vulkan-1.dll` from System32.
- `LoadWarning` is never raised (Windows has no load average).
- The worker runs at BELOW_NORMAL priority instead of `nice`.
- Slots are in `%LOCALAPPDATA%\libazahar-py\slots`. `Slot.fd` is a HANDLE.
- Paths must be ASCII and under 260 characters, so clone into a path like `C:\src` [R1-N7].
- The SD folder is case-insensitive.
- `runs/` behind a junction is not supported.
- States between macOS and Windows are tested in W7 with the v1.0.0 fixture; the result is in the release notes.
- The guest's HTTPS finds a CA file only at the compiled-in OPENSSLDIR (quoted from build.inputs), the same limit as
  on macOS.

Limits in STATUS:
- Proven on one PC only: Windows 10 Pro 22H2, x64, RTX 3060, NVIDIA driver 610.88, Python 3.10.11. CI adds Windows
  Server 2025 for the build, the fast tests and the core load test.
- AMD and Intel GPUs and Windows 11 are untested.
- No Windows speed figures (rule 7). The instance cap stays 4.

Allowed skips, by run [R1-S7]. Any other skip fails the gate.
- W4 and CI (fast pytest): any skip of a test that needs a core or the emulator. The skip list goes in the log.
- W7 (full, `LAZ_REQUIRE_EMULATOR=1`, `LAZ_STOCK_CORE` set, fixture present), exactly:
  - `test_threads_live.py::test_k_threads_lazpy1_core` and `test_threads_live.py::test_k_states_both_ways`: there is
    no lazpy.1 Windows core.
  - `test_slots.py::test_s5_load_warning`: by design; `test_s5_windows_has_no_load_warning` runs instead.
  - `test_lazpy_profile.py::test_worker_nice_floor` (all its cases): Windows has no nice values.
  - `test_api.py::test_long_batch_outlives_a_short_timeout`: a timing skip, allowed only if its message says the
    batch was too short.
  - `test_arguments.py::test_clear_sd_refuses_a_symlink`: allowed only if W0 found that the account cannot make
    symlinks.
  - `test_release_fixture.py` and `test_profile_format.py` must run, not skip.
- W10: the same list as W7.

## 7. macOS unchanged, without the Mac [R1-S5]

The Mac runs no 3DS work in this phase, so this is the proof:
- The Mac assets are v1.0.0's bytes, checked by sha (D2). `tools/build-core.sh` and the core pins are v1.0.0's bytes.
- C: W1a's stub-header preprocess diff on the PC, every hunk reviewed in W1 and rechecked in W3.
- Makefile: `make -n all test-host test-version check` gives the same commands as v1.0.0, apart from the owner's
  check-obinary line. This is checked on the PC before the merge (W1a, W2a, W3) and on macos-15 in test.yml after it
  (W4).
- Python: W1's per-line verdict on every Darwin-visible line, each naming the test that covers it.
- test.yml on macos-15 (3.10 and 3.14): build, `make check`, host C tests and the fast pytest, green on the merge and
  release commits.
- Best-effort: `macos-live.yml` runs the slow suite on a macos-15 runner with the public v1.0.0 core, if the runner's
  paravirtual Metal device runs MoltenVK. If it passes, STATUS says the macOS emulator suite passed in CI on v1.1.0.
  If not, STATUS says: "macOS: the emulator suite last ran on a Mac at v1.0.0; the v1.1.0 changes visible on macOS
  are reviewed and pass the CI build and fast tests."
- The owed I5 part 2 (a macOS clone check of v1.0.0 from GitHub) cannot run on the PC, because v1.0.0 has no Windows
  route. It is closed as superseded: macos-live.yml does a fresh fetch-and-build of the public v1.0.0 assets, and W10
  does the Windows clone check from the real URLs.

## 8. Out of scope

Linux (`port-linux`), Intel Macs, Windows on ARM, 32-bit Windows, the Mesa dzn route, prebuilt Windows host binaries,
audio, the PC-runner tools in the toolkit, a PowerShell fetch, any Mac rerun, a Windows core built natively in MSYS2
(gcc 16 is untested on Azahar 2126.2; review 1 section 7b), and a software-Vulkan boot in CI.

## 9. Findings from planning (each is fixed or gated by a named step)

- B1. The PC's private core DLL holds the WSL home path (with a local username) seven times: OpenSSL's OPENSSLDIR,
  ENGINESDIR, MODULESDIR and `ct_log_list.cnf`. It never ships. D4 and D5 fix it; W5 and W9 gate it.
- B2. build.inputs' `openssl_prefix=` was not masked. D5's neutral real prefix removes the need [R1-S8].
- B3. The private DLL's build.inputs lacks the `openssl_*`, `head=` and `cmake=` lines. Not a release candidate. D4.
- B4. The private DLL holds two GCC idents, "(GNU) 13-posix" and "(GNU) 15-win32". The CI build records every ident
  with its package. An ident with no package blocks (W5).
- B5. `make win64` writes to `build/win64/`, but Python looks in `build/`. Fixed in W2a.
- B6. `WIN_CC` and `ZLIB_PREFIX` default to WSL values. Fixed in W2a.
- B7. MSYS2 has no `unzip` (or `zip`). Covered by the README pacman line and W0.
- B8. The OpenSSL build script lives in the toolkit. It moves into `build-core-win64.sh` (W2b1).
- B9. The PE keyblob twin lives in the toolkit. It moves into `tests/gate_f2.py` (W2b1).
- B10. The branch has no CI file. Fixed in W2a.
- B11. Merging the branch's `tools/build-core.sh` edits would break the v1.0.0 Mac core's keyblob check. D3.
- B12. `fetch.sh`, `mkrelease.sh`, `release_check.py`, `clone_check.sh` and `mknotices.py` are macOS-only. Fixed in
  W2b1 and W2b2, with the Mac side inherited (D2).
- B13. The PC's default `python` is 3.7. D9, and the README in W6.

Review 1's findings are answered in the steps tagged with their id. R1-B1 is in D4, D4-fallback and W5. R1-B2 is in
D10, W2b1 and W5. R1-B3 is in D2, W2a, W2b2 and W7. R1-B4 is in D2, W2b2 and section 4. R1-B5 is in W1a and W3.
R1-S1 to R1-S14 and R1-N1 to R1-N7 are tagged where they land.

## 10. Hour-saving pass (redone on this revision)

Taken from review 1's list:
- H1. The core is built in CI, which takes about 30-40 minutes of wall time. There is no WSL pre-flight, no WSL start
  or restart, and no PC RAM or C: disk is used. Saves about 1.3 h.
- H2. The Mac-side checks are inherited by sha. Saves about 1.5 h.
- H3. The inherited asset bytes are fetched from the v1.0.0 page. There is no bsdtar port. Saves about 0.5 h.
- H4. W4 runs no full pytest. W7 runs it once, on the release core. Saves about 0.5 h, plus PC time.
- H5. There is no interim push at W7. Saves about 0.2 h.
- H6. W6 runs beside W2. Saves about 1 h end to end.
- H7. W8 runs beside W7c. This saves the users' waiting time.
- H8. gate_f2 starts from `gate_f2_pe.py`, and the notices use the Debian copyright files. Saves about 0.8 h.
- H9. W1b asks only the delta. Saves about 0.15 h.
- H10. W1a runs on the PC. Saves about 0.1 h.

New cuts found this time:
- No load-only re-check after publishing. The windows-2025 job in W5 tests the same bytes (sha), so W10 drops it.
  Saves about 0.2 h.
- No real `clang -E` step in CI. The PC stub diff covers our C code, and the CI `make -n` step covers the Makefile.
  Saves about 0.15 h.
- The asset copy check uses GitHub's asset digests (W9), not a hash pass on the Mac or a download back to the PC.
  Saves about 0.1 h.
- The runtime source asset is built in the same CI run as the core, with no separate step. If it is dropped later,
  nothing is re-staged except SHA256SUMS. Saves about 0.5 h of late re-staging risk.
- The fetch fallback (D7) avoids a "push only after publish" second commit and a second CI wait. Saves about 0.3 h.

Re-estimated against revision 0: W2b was 3.0 h and is now W2b1 plus W2b2, 5.0 h in total, as review 1 says
[R1-S3]. The cuts mostly pay for that.

## 11. Hours (estimates; actuals to docs/hours.tsv, phase `phase-7`)

| Step | Owner | Hours |
|---|---|---|
| W0 | main loop | 0.3 |
| W1a | main loop (PC) | 0.25 |
| W1 | opus | 1.25 |
| W1b | ip-legal | 0.25 |
| W2a | sonnet | 2.0 |
| W2b1 | sonnet | 2.5 |
| W2b2 | sonnet | 2.5 |
| W6 | sonnet | 1.0 |
| W3 (with the merge and mkmap) | opus + main loop | 0.75 + 0.2 |
| W4 | main loop | 1.0 |
| W5 | sonnet | 0.75 |
| W7 | main loop | 1.0 |
| W7c | main loop | 0.3 |
| W8 | release-legal-audit + fixes | 1.25 |
| W9 | main loop | 0.5 |
| W10 | main loop | 0.3 |
| This revision and review 2 | opus | 1.0 |

Total: about 17.1 h of work (range 14 to 21 h). Revision 0 said about 17 h, but it under-counted W2b by about 2 h.
The work is now five steps bigger in content, at the same total. End to end, about 10 h of wall time. W2a, W2b1,
W2b2 and W6 run in parallel, and so do W7c and W8. On top of that come the waits for the CI build (about 40
minutes), the PC, the users and Guy.

## 12. Risks

- The ubuntu:26.04 container's mingw-w64 packages differ from A1's. build.inputs records the versions, and the
  load-only job and the PC tests use the same bytes that ship. If the build fails twice: D4-fallback.
- The CI artifact is the shipped binary. Its sha is recorded at download (W5) and checked again at W7 staging and at
  W9 (GitHub digest).
- The neutral OPENSSLDIR changes the guest's HTTPS lookup. The full pytest's HTTPS tests cover it, and the limit is
  documented.
- The PC is shared. Heavy runs (W7's full pytest) are announced, and lane-pc waits when the PC is busy.
- Timing bounds can fail under load. W4 runs the state-restore test quietly three times.
- macOS: if `macos-live.yml` cannot run MoltenVK, a macOS-only regression in a Darwin-visible change would show only
  in users' runs. W1's three Darwin lists are the guard.
- W7c has no deadline (D11), so the release can wait on another project's schedule.

## 13. Open questions for Guy

- Q1. Publishing v1.1.0 (W10) is the only step that needs your word.
- Q2. Should Windows users build the host from source (the default), or should the release also ship prebuilt
  `libazhost.dll` and `azhost.exe`?
- Q3. Is "proven on one PC (Windows 10, RTX 3060, NVIDIA)" the right wording? Is section 7's macOS sentence right if
  the macOS emulator suite cannot run in CI?
