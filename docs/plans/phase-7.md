# Phase 7 plan: the Windows port proven (release v1.1.0)

Revision 0, 2026-11-17 11:25 IST, opus planner. Awaits review 1 and review 2 (opus, one at a time). Item laz-700.

Guy, 2026-11-17: "update the repo so it says windows is ot proven and its a WIP. / and move forward so its windows
proven". The first half is done (a551d5f, pushed). This plan is the second half.

Guy, 2026-11-17, on pushing: "moev forward doesnt include push to github. but this time you can push to github". So in
this phase the main loop pushes reviewed, gated work (main, then the v1.1.0 tag) without asking again. Publishing the
GitHub release still needs Guy's word (W10).

Guy, 2026-11-17, on the Mac: the Mac is closed to all 3DS work (emulators, builds, pytest, gates). It is for editing,
git and ssh only (flag `~/.lazpy/PC_ONLY`). Every build and gate in this plan runs on the PC (Windows, MSYS2 or WSL) or
on GitHub's CI runners. No step has a "rerun on the Mac" fallback. A `lane-pc` exit 77 means "not run": requeue it on
the PC.

## 1. What "Windows proven" means (the exit gate)

All of these hold, each with its evidence file:
- Branch `port-win-v1` is reviewed (one full opus diff review), fixed, and merged into main.
- A fresh clone of GitHub main on the PC, following only the README's Windows steps, builds the host, passes
  `make test-host`, and passes the full pytest with `LAZ_REQUIRE_EMULATOR=1`. The only skips allowed are listed in
  section 6.
- A Windows CI job (`.github/workflows/test-windows.yml`) is green on the release commit.
- The macOS side is shown unchanged (section 7) without running anything on the Mac.
- release-legal-audit says shippable for v1.1.0. `release_check.py --pre-push` passes every check.
- v1.1.0 is tagged and pushed, with a Windows core asset. Guy publishes it. After publishing, the post-publish checks
  pass from the real GitHub URLs.
- README, STATUS and USING say "Windows: proven on one PC" with the exact limits (section 6). No speed claims.

## 2. Decisions taken by default (reviewers or Guy may overrule; each is reversible until the tag push)

- D1. Version 1.1.0. Windows support is an addition, so it is a minor release (owner condition 1).
- D2. The core stays 2126.2-lazpy.2. The macOS core zip is re-uploaded byte-identical from v1.0.0 (sha
  `ced9a362...`). No Mac core rebuild, so the Mac fetch pin keeps its sha.
- D3. `tools/build-core.sh` stays byte-identical to v1.0.0 on main. The branch's win64 case moves into a new
  `tools/build-core-win64.sh`. Reason: `tests/gate_f2.py` checks that the core's build.inputs `script=` line equals
  the sha of `tools/build-core.sh`. If the branch's edits merged, the v1.0.0 Mac core would fail its keyblob check.
- D4. The Windows core is built in WSL Ubuntu on the PC (the proven A1 route: mingw-w64 gcc-posix cross build). It is
  built from a fresh clone of GitHub main at the merge commit, in a neutral path (`/tmp/lazpy-w5`), never from a dev
  tree. The old private core DLL on the PC (sha `EFD22238...`, Nov 13) never ships (finding B1).
- D5. OpenSSL for Windows is built by a script in the repo (moved from the toolkit's `tools/pc/build-ossl-win.sh`),
  with OpenSSL's own mingw defaults for the compiled-in paths (`C:/Program Files/...`) and a `DESTDIR` install inside
  the build tree. No home path is compiled in. Same source tarball as macOS (sha `a2157c28...`).
- D6. No prebuilt Windows host binaries. Users build `libazhost.dll` and `azhost.exe` with MSYS2 `make`, as macOS users
  run `make`. The release ships only the core DLL for Windows. (Open question Q2.)
- D7. Windows fetch is the same `tools/fetch.sh`, run in the MSYS2 MINGW64 shell. No PowerShell twin.
- D8. The release tools run on the PC in WSL Ubuntu: `tools/mkrelease.sh`, `tools/release_check.py`, and gate_f2's
  16-byte window search (WSL holds the full source after W5). `gh` runs on the Mac (a GitHub operation, not a gate).
- D9. Owner conditions hold: the Darwin Makefile block stays verbatim (cond 3), `DEFAULT_CAP` stays 4 (cond 5), no
  Linux asset (cond 7).

## 3. Steps, in order

Each step gets an item under laz-700 (ids 701-712, created by W0). Hours book to `phase-7`. Evidence lives under
`runs/p7/<step>/` (gitignored) and is named in the item's Evidence line. "PC runner" means `tools/pc/lane-pc` or the
plain ssh runner in docs/map/runners.md. `$NEEDLES` is the private-needle list (local usernames on Mac, WSL and
Windows, and Guy's real email); it lives only in the main loop's environment as `LAZ_PRIVATE_NEEDLES`, never in a file
in the repo.

**W0. Items and pre-flight.** Owner: main loop. 0.3 h.
- Create items 701-712, rewrite the handoff. Read-only pre-flight on the PC: free disk on C: and D: (at least 30 GB on
  the WSL drive), WSL Ubuntu present, the WSL packages (`gcc-mingw-w64-x86-64-posix`, `g++-mingw-w64-x86-64-posix`,
  `cmake`, `ninja-build`, `zip`, `unzip`, `python3`, `perl`), the MSYS2 packages, the venv's Python version.
- Gate: `python3 -I tools/status_check.py --strict-handoff` exit 0; `runs/p7/w0/preflight.txt` lists every tool with
  its version, and every missing one has an install line for W5.

**W1. Full diff review of port-win-v1.** Owner: opus agent (the one expensive slot). 1.25 h.
- Reads `git diff main...port-win-v1` (56 files, +1653/-134) for correctness on Windows and proves the macOS paths
  are unchanged. Inputs given to it: the Darwin preprocessed-source diff from W1a, the owner conditions file, USING's
  1.0 promise, and findings B1-B12 from section 9.
- W1a (main loop, 0.2 h, before W1): a one-off CI job on GitHub's macos-15 runner (`workflow_dispatch`, on a scratch
  branch that is deleted after) runs `cc -E -P` with the Makefile's Darwin flags on every `host/**/*.c` in both
  trees, and uploads the diff as an artifact. Every hunk is a line the Mac compiler sees differently.
- Gate: `docs/reviews/phase-7-diff-review.md` exists. Every finding has a tag (P7-R1-n), a severity and a file:line.
  It has a section "Darwin-visible changes" that lists every hunk of the W1a diff with a verdict. It confirms owner
  conditions 3 and 5 by quoting the lines.

**W1b. Licence questions.** Owner: ip-legal agent (run after W1 ends, never beside another expensive agent). 0.4 h.
- Questions: (1) the core statically links libstdc++ and libgcc (GPLv3 with the GCC Runtime Library Exception),
  winpthreads (MIT-style) and the mingw-w64 CRT (ZPL, public domain and others). Must the release attach the exact
  Ubuntu source packages for `gcc-mingw-w64` and `mingw-w64`, or is a notice plus a pinned archive link enough?
  (2) The wording "Windows" and "NVIDIA" in docs (nominative use). (3) That shipping no Vulkan loader and no MSVC
  runtime needs nothing more.
- Gate: `docs/reviews/phase-7-ip-legal.md` answers each question with yes, no, or a named action. Durable findings go
  to the learn skill's `references/ip-law-and-publishing.md`.

**W2a. Fixes: host, Python, tests, Makefile, CI.** Owner: sonnet agent, worktree `lazpy-p7a` on port-win-v1 (made by
the main loop at the branch tip). 2.0 h. Runs beside W2b.
- The W1 findings in host/, python/, tests/ and the Makefile.
- Makefile: on MSYS2 (`uname -s` starts with `MINGW64_NT`) the defaults become `WIN_CC=gcc` and
  `ZLIB_PREFIX=/mingw64` (finding B6), and plain `make` builds `build/libazhost.dll` and `build/azhost.exe`, the paths
  Python looks in (finding B5). The cross build (`make win64` from WSL) keeps `build/win64/`. The Darwin block stays
  byte-identical.
- `.github/workflows/test-windows.yml` (finding B10), as in section 5. Non-blocking for now.
- Tests run on the PC only, through the PC runner (exit 77: requeue).
- Gate, on the PC in a fresh MSYS2 MINGW64 shell in the agent's synced tree: `make check && make && make test-host &&
  make test-version`, then `python -m pytest -q -m "not slow" tests/python` with the venv. Logs in `runs/p7/w2a/`.
  Plus `git diff main -- Makefile` shows no line changed inside the Darwin block (W3 checks it).

**W2b. Fixes: the release tools.** Owner: sonnet agent, worktree `lazpy-p7b` on a branch off port-win-v1. 3.0 h.
- `tools/build-core.sh` back to its v1.0.0 bytes. `tools/build-core-win64.sh` holds the win64 route, including the
  OpenSSL build (D5, finding B8) and `openssl_prefix=` masked as `<repo>/...` in build.inputs (finding B2).
  build.inputs also records the WSL package versions (`dpkg-query -W` lines for the mingw-w64, cmake and ninja
  packages) and every GCC ident found in the DLL (finding B4).
- `tests/gate_f2.py`: a PE import check (allow-list: ADVAPI32, bcrypt, CRYPT32, KERNEL32, msvcrt, ole32, SHELL32,
  USER32, WINMM, WS2_32), read from `objdump -p` "DLL Name:" lines, with a stdlib PE parser if objdump is absent. The
  16-byte window search runs on the DLL bytes as it does on the dylib. Replaces the toolkit's `tools/pc/gate_f2_pe.py`
  (finding B9).
- `tools/mknotices.py`: a win64 mode that reads the win64 build tree, knows the mingw-w64 system prefixes, and adds
  the runtime components (libstdc++, libgcc, winpthreads, mingw-w64 CRT) with their licence texts. Output:
  `NOTICES-windows-x64.md`, committed beside `NOTICES.md`.
- `tools/mkrelease.sh`: builds the v1.1.0 asset set (section 4). It copies the v1.0.0 Mac zip and asserts its sha,
  and builds the Windows zip. The Windows SOURCE.md text says how to rebuild with `build-core-win64.sh`.
- `tools/release_check.py`: `expected_assets()` gets the two new names; the keyblob check runs on both cores; a new
  Windows check (PE x64 machine, the import allow-list, no `-g` debug sections, no needle); the macOS check passes by
  sha-equality with the v1.0.0 gated zip when `vtool`/`lipo` are absent (WSL); `build_files_check` lists the new
  scripts; `pins_findings` checks `LAZPY_CORE_ZIP_WIN` and `LAZPY_CORE_SHA_WIN`.
- `tools/fetch.sh`: picks the Windows zip and sha when `uname -s` starts with `MINGW64_NT`, unpacks the `.dll`, and
  `--moltenvk` prints "not needed on Windows" and exits 0 for that part. `unzip` comes from pacman (finding B7).
- `tools/clone_check.sh`: a Windows mode (chosen by `uname -s`). It runs the README's `steps-windows` block in a clean
  MSYS2 environment that keeps only `SYSTEMROOT`, `WINDIR`, `LOCALAPPDATA`, `TEMP`, `TMP`, `USERPROFILE`, `HOME` and a
  PATH of MSYS2 plus the Windows Python. It drops `nice` and runs the full pytest with `LAZ_REQUIRE_EMULATOR=1`.
  `tools/docs_check.py` learns `--block windows` and checks the `steps-windows` marker.
- Every tool keeps its `--plant-red` or self-test where it has one, and each new check gets a planted-red case.
- Gate, on the PC: `python -I tools/release_check.py --plant-red` exit 0 and each new planted case fails as expected
  (WSL or MSYS2 Python); `sh tools/clone_check.sh --dry-run ...` prints the Windows steps; `git diff v1.0.0 --
  tools/build-core.sh` is empty. Logs in `runs/p7/w2b/`.

**W3. Check of the fix diff.** Owner: opus agent. 0.75 h. After W2a and W2b are merged into port-win-v1 by the main
loop.
- Reads only the W2 commits against each W1 finding. Re-runs W1a's Darwin diff on the new tip.
- Gate: `docs/reviews/phase-7-fix-check.md` gives each P7-R1 finding "fixed", "not fixed" or "moved", with the commit.
  Zero "not fixed" blockers.

**W4. Merge and push main.** Owner: main loop. 1.0 h.
- Merge port-win-v1 into main locally with `--no-ff`, commit as the no-reply identity. Bundle it to the PC.
- PC gates on the merge commit, from the bundle, in a fresh tree (`D:\lazpy\p7\w4`), with the PC's existing private
  core as `LAZ_CORE` (it is fine for tests; it never ships): `make check && make && make test-host`, then the full
  pytest with `LAZ_REQUIRE_EMULATOR=1` and `LAZ_STOCK_CORE=C:/lazpy/probe/azahar_libretro.dll`. Then
  `test_state_boot` alone, three times on a quiet PC (the owed state-restore rerun). Announce the run on the PC board
  first (it starts up to 4 copies).
- Push main (allowed). Wait for both CI files on the merge commit.
- Gate: `runs/p7/w4/pytest.log` ends with 0 failed and only section-6 skips; `test_state_boot` 3/3 pass; `gh run list
  --branch main --limit 2` shows test.yml green (macOS build, host tests, fast pytest on 3.10 and 3.14) and
  test-windows.yml finished (green, or red with a filed finding; it is non-blocking until W10).

**W5. Build the Windows core.** Owner: sonnet agent driving the PC. 2.0 h (the build itself is about 1.5 h). Runs
beside W6.
- Announce on the PC board that WSL starts for about 2 hours. In WSL: fresh clone of GitHub main at the W4 commit into
  `/tmp/lazpy-w5`, `sh tools/fetch.sh --headers`, the nokeys source per core/PIN-nokeys, then
  `sh tools/build-core-win64.sh`. Then generate `NOTICES-windows-x64.md` with mknotices.
- Checks in WSL: the gate_f2 keyblob check (PE imports and the 16-byte window search against the full source),
  `strings -el` and `strings` over the DLL grepped for `$NEEDLES` and for `/home/`, `/tmp/lazpy`, `C:/Users`
  (zero hits), build.inputs has `target=win64`, `head=` equal to the W4 commit, and `script=` equal to the sha of
  `tools/build-core-win64.sh` at that commit.
- Then copy the DLL and build.inputs to the Windows side, boot the test app once with the W4 host from the PC runner,
  and `wsl --shutdown`.
- Gate: `runs/p7/w5/checks.txt` holds each check's PASS line; one boot log with frames and a screenshot sha; `wsl -l -v`
  shows Stopped. If `NOTICES-windows-x64.md` differs from the committed one, the main loop commits the new one.

**W6. Docs, version, release notes.** Owner: sonnet agent (edits only, on the Mac). 1.25 h. Beside W5.
- `pyproject.toml` and `__version__` to 1.1.0. README: a Windows section with a `<!-- docs_check: steps-windows -->`
  block (install MSYS2, `pacman -S make mingw-w64-x86_64-gcc mingw-w64-x86_64-zlib unzip git`, install Python 3.10+
  from python.org, clone, `sh tools/fetch.sh --headers --lazpy-core --testapp`, `make`, `make test-host`, venv, `pip
  install -e .`, the quickstart). STATUS: Windows "proven on one PC" with the limits. USING: a Windows section with
  the differences table (section 6) and the `LAZ_MVK` meaning on Windows. `docs/release-notes/v1.1.0.md`. tools.md and
  runners.md for the new tools; `python3 -I tools/mkmap.py`.
- Gate: on the PC (docs_check runs Python on repo files, so it is a gate): `python -I tools/docs_check.py` exit 0 and
  `python -I tools/map_check.py` exit 0, through the PC runner.

**W7. Stage the release and prove the fresh clone.** Owner: main loop. 1.25 h.
- In WSL (restarted for this step, then shut down): `tools/mkrelease.sh` into `D:\lazpy\rel\v1.1.0` (section 4).
  Fill the fetch.sh pins (`REL_TAG=v1.1.0`, `LAZPY_CORE_ZIP_WIN`, `LAZPY_CORE_SHA_WIN`; the Mac pin and
  `TESTAPP_SHA` unchanged), commit on the Mac, push main.
- On the PC, in the MSYS2 shell: `sh tools/clone_check.sh --repo https://github.com/GuyShtainer/libazahar-py --branch
  main --out D:/lazpy/p7/w7 --release-base file:///D:/lazpy/rel/v1.1.0`. This is the exit gate's fresh clone: the
  README Windows steps, `make test-host`, the quickstart, and the full pytest with `LAZ_REQUIRE_EMULATOR=1`.
- On the PC: the v1.0.0 state fixture loads under the Windows host (test_release_fixture with the fixture copied to
  `D:\lazpy\p7\fixtures`), and a state saved on Windows is kept for the next release.
- Gate: `D:/lazpy/p7/w7/rc` holds 0; the pytest log has only section-6 skips; the fixture test passes or its failure is
  written into the release notes as a documented difference.

**W7c. Users on the release candidate.** Owner: main loop sends one ask each to Gen3D and 3DPlatinum. 0.3 h of ours.
- The PC deploy those projects already use is switched to the release-candidate host and core. Their next normal job
  on it counts. No deadline (as phase-v1's D6); the release waits for both.
- Gate: each project's job log line names the release-candidate deploy id and says PASS; quoted in item 710.

**W8. Legal audit.** Owner: release-legal-audit agent (the one expensive slot). 0.75 h, plus 0.5 h of fixes.
- Brief as phase-i section 9.2, plus: the Windows zip, the mingw runtime pieces and W1b's answers, the strings scan,
  the "Windows proven" wording in README/STATUS/USING, and the history since v1.0.0.
- Fixes go in, then the main loop re-stages (W7's mkrelease again).
- Gate: `docs/reviews/release-legal-audit-v1.1.0.md` says shippable. Any re-stage reruns the W7 gate's `release_check`.

**W9. Final stage, tag, push, draft.** Owner: main loop. 0.4 h.
- In WSL: `LAZ_PRIVATE_NEEDLES=$NEEDLES python3 -I tools/release_check.py D:/lazpy/rel/v1.1.0 --pre-push` (path as
  WSL sees it): every check PASS. Copy the staged folder to the Mac over ssh; on the Mac, `shasum -a 256 -c
  SHA256SUMS` checks the copy (an integrity check of copied files, not a 3DS gate).
- Tag `v1.1.0` (annotated, no-reply identity) on the pinned commit. Push main and the tag (allowed).
  `gh release create v1.1.0 --draft --verify-tag` with every asset and the release notes.
- Gate: `gh release view v1.1.0 --json isDraft,assets` shows a draft with exactly the section-4 asset names, and each
  asset's sha matches SHA256SUMS.

**W10. Guy publishes; post-publish checks.** Owner: Guy publishes; then main loop. 0.3 h.
- On the PC: `curl` every asset from the real URL into a new folder, check `SHA256SUMS`, run clone_check again with no
  `--release-base`. On GitHub: switch test-windows.yml to blocking, and add the load-only step (fetch the released
  core, load it, read `retro_api_version` and the lazpy version export; no Vulkan needed) to prove the DLL needs no
  extra runtime DLLs on a clean Windows Server.
- Gate: `runs/p7/w10/` holds the checksum output and the clone_check `rc` = 0; the next CI run on main is green in both
  files. Item 700 moves to done.

Order: W0, W1a, W1, then W2a + W2b (two sonnets) with W1b in the expensive slot, W3, W4, then W5 + W6, W7, W7c, W8,
W9, W10. Never two expensive agents (opus, ip-legal, release-legal-audit) at once.

## 4. The v1.1.0 assets and their licences

| Asset | What | Licence and source |
|---|---|---|
| `azahar_lazpy_libretro-2126.2-lazpy.2-macos-arm64.zip` | v1.0.0 bytes (sha `ced9a362...`) | as v1.0.0 |
| `azahar_lazpy_libretro-2126.2-lazpy.2-windows-x64.zip` | the DLL, NOTICES (Windows), LICENSE, COPYING-azahar.txt, SOURCE.md (Windows text), build.inputs | GPLv3 (Azahar, ours); OpenSSL Apache-2.0; static libstdc++/libgcc GPLv3 + Runtime Exception; winpthreads MIT-style; mingw-w64 CRT ZPL and public domain |
| `azahar-unified-source-2126.2-lazpy-nokeys.tar.xz` | the core's corresponding source, same bytes as v1.0.0 | GPLv3 |
| `openssl-3.6.5.tar.gz` | OpenSSL source, same bytes | Apache-2.0 |
| `citra_system_archives-f470e0c.tar.gz` | same snapshot as v1.0.0 | as v1.0.0 |
| `libazahar-py-core-build-v1.1.0.tar.gz` | `git archive` of `core`, `tools/build-core.sh`, `tools/build-core-win64.sh`, `tools/toolchain-win64.cmake`, `tools/untar_checked.py` | GPLv3 (the scripts used to control compilation) |
| `NOTICES.md`, `NOTICES-windows-x64.md` | third-party notices per platform | |
| `SOURCE.md` | where each binary's source is, both platforms | |
| `testapp.3dsx` | same bytes as v1.0.0 (sha `ba106998...`) | ours |
| `SHA256SUMS` | sha256 of every asset | |
| mingw-w64 runtime source (only if W1b says so) | Ubuntu source packages for `gcc-mingw-w64` and `mingw-w64` at the versions in build.inputs | as packaged |

What the binaries link:
- The core DLL imports only Windows system DLLs: ADVAPI32, bcrypt, CRYPT32, KERNEL32, msvcrt, ole32, SHELL32,
  USER32, WINMM, WS2_32 (checked on the private build; W5 checks the release build). libstdc++, libgcc and winpthreads
  are static. msvcrt.dll is a Windows system library. No MSVC runtime is used or shipped.
- OpenSSL 3.6.5 is static, built by `tools/build-core-win64.sh` with `Configure mingw64 no-shared`, the default
  compiled-in paths, and a `DESTDIR` install in the build tree.
- Vulkan: the host loads `vulkan-1.dll` from System32 only. On the PC that is the loader the NVIDIA driver installs
  (1.4.341, driver 610.88). Nothing Vulkan ships. Mesa dzn is not used (it was the old WSL route; it drew 3D markers
  black).
- The host (not shipped) is built by the user with MSYS2 MINGW64 gcc, `-static -static-libgcc`, zlib static from
  `/mingw64`. It imports bcrypt, KERNEL32 and msvcrt. Both the host and the core use msvcrt, so they share one C
  runtime. The UCRT64 shell is not supported (untested).
- Corresponding source: every shipped binary's source is on the release page (the rows above) and the repo at the tag.
  release-legal-audit (W8) gates this before the push.

## 5. CI on Windows

`.github/workflows/test-windows.yml`, on `windows-2025`. Actions pinned by sha: `actions/checkout`,
`actions/setup-python` (3.10 and 3.14), `msys2/setup-msys2` (sha recorded in W2a with `gh api`), MINGW64 environment,
`path-type: inherit` so the Windows Python is visible.

Steps: `sh tools/fetch.sh --headers`, `make check`, `make`, `make test-version`, `make test-host`, `pip install -e .
pytest numpy`, `python -m pytest -q -m "not slow" tests/python`. After W10, the load-only step.

It can check: the README's package list builds the host on a clean machine; the host C tests (about 308,000
checks); `check-obinary`; the Python layer without a core (paths, slot lock, worker start, options, input scripts);
after W10, that the released DLL loads with no extra runtime DLLs.

It cannot check: booting the core, frames, screenshots, states, the pool, timing, or anything that needs a GPU (the
runners have no GPU and no Vulkan driver); the core build (about 1.5 h and the full source); `clang --analyze`.
Those are proven only on the PC, by W4, W5 and W7.

It is non-blocking until v1.1.0 is published; W10 makes it blocking.

## 6. Version, the 1.0 promise on Windows, and the limits

v1.1.0. The 1.0 promise (USING top, phase-v1 section 1) holds on Windows, with these documented differences, all in
a USING table:
- File names: `libazhost.dll`, `azhost.exe`, `azahar_lazpy_libretro.dll`.
- `LAZ_MVK` names the Vulkan loader; the default is `vulkan-1.dll` from System32.
- `LoadWarning` is never raised (Windows has no load average).
- Worker priority is BELOW_NORMAL instead of `nice`.
- Slots live in `%LOCALAPPDATA%\libazahar-py\slots`; `Slot.fd` is a HANDLE, not a file descriptor.
- Paths must be ASCII and under 260 characters (the host uses the `*A` Windows calls).
- The SD folder is case-insensitive.
- `runs/` behind a junction is not supported (it broke test_pool_live).
- States between macOS and Windows: tested in W7 with the v1.0.0 fixture; the result goes in the release notes.
- The guest's HTTPS finds a CA file only where OpenSSL's compiled-in paths point (`C:/Program Files/Common
  Files/SSL`), as the macOS limit.

Limits written in STATUS: proven on one PC only (Windows 10 Pro 22H2, x64, RTX 3060, NVIDIA driver 610.88, Python
3.10.11); CI adds Windows Server 2025 for the build and fast tests; AMD and Intel GPUs and Windows 11 are untested; no
Windows speed figures (rule 7); the instance cap stays 4.

Full Windows pytest skips allowed: tests that need `LAZ_CORE_OLD` (there is no lazpy.1 Windows core), the `nice` test
(`test_lazpy_profile.py`, win32), and nothing else. `LAZ_STOCK_CORE` is set on the PC, so the stock-core tests run.

## 7. macOS unchanged, without the Mac

The Mac runs no 3DS work in this phase, so the macOS emulator suite is not rerun. The proof is:
- The macOS core zip is the v1.0.0 bytes (D2), and `tools/build-core.sh` is the v1.0.0 bytes (D3).
- W1a and W3's Darwin preprocessed-source diff: every line the Mac compiler sees differently is listed and reviewed.
- test.yml on macos-15 (3.10 and 3.14): build, host C tests, fast pytest, green on the merge and release commits.
- STATUS says: "macOS: the emulator suite last ran at v1.0.0; v1.1.0 changes on macOS are reviewed and pass CI build
  and fast tests." (Open question Q4.)
- The owed I5 part 2 (a v1.0.0 clone check of macOS from GitHub) cannot run on the PC: v1.0.0 has no Windows route. It
  is closed as superseded by W10's clone check of v1.1.0 from the real URLs (Windows) and test.yml (macOS build).

## 8. Out of scope

Linux (`port-linux`), Intel Macs, Windows on ARM, 32-bit Windows, the Mesa dzn route, prebuilt Windows host
binaries, a core build in CI, audio, the PC-runner tools in the toolkit, a PowerShell fetch, and any Mac rerun.

## 9. Findings from planning (each is fixed or gated by a named step)

- B1. The PC's private core DLL holds the WSL home path (with a local username) seven times: OpenSSL's OPENSSLDIR,
  ENGINESDIR, MODULESDIR and `ct_log_list.cnf`. It never ships. Fixed by D5 and gated in W5 and W9.
- B2. build.inputs' `openssl_prefix=` line is not masked (only the `cmake=` line is). W2b.
- B3. The private DLL's build.inputs lacks the `openssl_*`, `head=` and `cmake=` lines. Not a release candidate. D4.
- B4. The private DLL holds two GCC idents, "(GNU) 13-posix" and "(GNU) 15-win32". W5 records where each comes from;
  one with no listed source blocks the release.
- B5. `make win64` writes to `build/win64/`, but Python looks in `build/`. A fresh clone's README steps would fail.
  W2a.
- B6. `WIN_CC` and `ZLIB_PREFIX` default to WSL values. W2a.
- B7. MSYS2 has no `unzip`; `fetch.sh` needs it. README pacman line, W6.
- B8. `build-ossl-win.sh` lives in the toolkit, not the repo; it controls compilation, so it belongs to the
  corresponding source. W2b.
- B9. The PE keyblob twin lives in the toolkit. W2b.
- B10. The branch has no CI file. W2a.
- B11. Merging the branch's `tools/build-core.sh` edits would break the v1.0.0 Mac core's keyblob check. D3.
- B12. `fetch.sh`, `mkrelease.sh`, `release_check.py`, `clone_check.sh` and `mknotices.py` are macOS-only. W2b.
- B13. The PC's default `python` on PATH is 3.7; the README must say "Python 3.10 or newer from python.org" and use the
  venv's interpreter. W6.

## 10. Hour-saving pass (what was cut)

- No Mac core rebuild (D2, D3): about 2 h and a Mac session saved.
- One full opus review (W1) plus a narrow fix check (W3), not two full reviews.
- No prebuilt Windows host binaries (D6): no second notices file, no host licence review.
- No PowerShell fetch (D7). Existing tools get a platform branch, no new twins.
- No core build in CI and no software-Vulkan CI boot.
- No new OpenSSL or source assets: v1.0.0's bytes are reused.
- The keyblob window search runs in WSL beside the build (the full source is already there).
- Users confirm through their normal next job on the release-candidate deploy (W7c), not a special test.
- No Windows speed rows.
- The owed I5 part 2 is closed by W10 instead of a separate run.

## 11. Hours (estimates; actuals to docs/hours.tsv, phase `phase-7`)

| Step | Owner | Hours |
|---|---|---|
| W0 | main loop | 0.3 |
| W1a + W1 | main loop + opus | 0.2 + 1.25 |
| W1b | ip-legal | 0.4 |
| W2a | sonnet | 2.0 |
| W2b | sonnet | 3.0 |
| W3 | opus | 0.75 |
| W4 | main loop | 1.0 |
| W5 | sonnet | 2.0 |
| W6 | sonnet | 1.25 |
| W7 + W7c | main loop | 1.25 + 0.3 |
| W8 | release-legal-audit + fixes | 1.25 |
| W9 | main loop | 0.4 |
| W10 | main loop | 0.3 |
| Plan reviews 1 and 2 | opus | 1.5 |

Total about 17 h of work (range 14 to 24 h). With W2a/W2b and W5/W6 in parallel, about 13 h end to end, plus waits for
the PC, the users and Guy.

## 12. Risks

- The WSL core build fails or differs from A1 (Ubuntu packages may have moved since Nov 13). W0 records the versions;
  W5 records them in build.inputs.
- The neutral OpenSSL prefix changes the guest's HTTPS behaviour. Covered by the HTTPS tests in the full pytest; the
  limit is documented.
- The PC is shared with other sessions. Every heavy run is announced on the PC board; lane-pc waits when busy.
- Timing bounds may fail under load (the state-restore test). W4 reruns it quiet three times.
- Apple's or GNU objdump may print PE imports differently. The stdlib parser is the fallback.
- The macOS emulator suite is not rerun (section 7). A macOS-only regression in a host C change would show only in
  Mac users' runs. The Darwin diff review is the guard.

## 13. Open questions for Guy

- Q1. Publishing v1.1.0 (W10) is the only step that needs your word.
- Q2. Build-from-source host on Windows (default), or also ship prebuilt `libazhost.dll` and `azhost.exe`?
- Q3. WSL runs for about 2 hours on the PC for the core build (W5) and briefly in W7 and W9. Default: yes, announced,
  shut down after.
- Q4. Is "proven on one PC (Windows 10, RTX 3060, NVIDIA)" the right wording, and is it fine that v1.1.0 does not
  rerun the macOS emulator suite (section 7)?
