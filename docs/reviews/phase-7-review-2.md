# Phase 7 ("Windows proven", v1.1.0): review 2 of 2

Reviewer: opus, fresh (review loop 2). Plan: `docs/plans/phase-7.md` revision 1 (5dc0a34). Checked against main,
port-win-v1 (1c8650f), the v1.0.0 release page, the toolkit's PC records and the PC itself (read-only). Nothing was
built or run on the Mac. Tags: [R2-B] blocker, [R2-S] should, [R2-N] nit.

## 0. Facts measured for this review

- `gh api repos/GuyShtainer/libazahar-py`: public, default branch main, Actions on, artifact and log retention 90
  days, default workflow token read-only. Local main is 3 docs commits ahead of origin/main (a551d5f).
- v1.0.0 is published (2026-11-17 09:08Z) with 9 assets, each with a GitHub `digest`:
  SHA256SUMS `288c2a257948498bb5c0f4e56a582ee311fd6654aa523b51fc85876e5ce19bec`,
  core-build-v1.0.0 `7a4d9c529586275f74af6ac43eb3a24c5fba738eb76eed8bb53ea72f43914857`,
  top-level SOURCE.md `23fbd93f...`. Neither the SHA256SUMS nor the core-build digest is pinned anywhere in the repo
  (`grep -rn 288c2a25\|7a4d9c52` empty). The other inherited assets are anchored: nokeys in `core/PIN-nokeys`,
  OpenSSL in `core/OPENSSL.md`, the snapshot in `mkrelease.sh` SNAP_SHA, NOTICES.md equals the repo file, the Mac zip
  and test app in `fetch.sh:42-44`.
- `git diff v1.0.0 main -- NOTICES.md tools/build-core.sh core/` is empty (D2/D3 hold today).
- PC (read-only ssh): LongPathsEnabled=1; Developer Mode off (so the symlink skip is allowed); C: 29.7 GB free,
  D: 2428 GB; free RAM 6.61 GB. MSYS2: no `zip`/`unzip`, `sha256sum` yes, `shasum` only in `/usr/bin/core_perl`,
  mingw64 `objdump`/`strings` yes, `uptime` absent. `C:\lazpy\probe\azahar_libretro.dll` exists. The venv's base
  Python is under `C:\Users\<user>\AppData\Local\Programs\Python\Python310`: the path holds a space and the local
  username.
- Branch preprocessor conditions added: only `_WIN32` tests, one `__APPLE__`, and `#ifndef O_BINARY`
  (`host/plat/azh_plat.h`). So W1a's stub-header method sees every Darwin-visible change, provided the stubs leave
  `O_BINARY` undefined (as macOS does).
- Branch skip sites (all 12) map to section 6's list: test_api:109, test_arguments:49, test_lazpy_profile:58/68,
  test_profile_format:46, test_release_fixture:22, test_slots:94/105, test_threads_live:74/168/182,
  test_client:123, test_map:51 (importorskip numpy).

## 1. Did revision 1 close review 1's blockers?

| R1 | Verdict | Note |
|---|---|---|
| B1 (WSL build) | Closed, with new gaps | CI container replaces WSL. The container needs work the plan does not list: R2-B3, R2-S6. |
| B2 (no key headers) | Closed in principle | D10 works (long paths on), but moving the window search into CI is cheaper and safer: R2-S1. |
| B3 (release_check Mac-bound) | Closed with gaps | Inherit is not anchored (R2-S3), check 16 inherited wholesale loses the new-text checks (R2-S4), seven `next(glob)` sites pick one of two zips (R2-S5). |
| B4 (Mac SOURCE.md names core-build-v1.0.0) | Closed | The asset is inherited by bytes; the top-level SOURCE.md maps each zip. |
| B5 (scratch-branch push) | Closed | W1a runs on the PC with stubs; no push. |

## 2. Blockers

**[R2-B1] W4's clone check runs a README block that is not in the W4 tree.** Step W4.
- Evidence: W4 merges `p7-int` *minus the W6 commit* (plan:252), then runs `clone_check.sh --until host --repo
  <bundle> --branch main` (plan:256). Windows mode "runs the README's `steps-windows` block" (plan:216), and that
  block is added only by W6 (plan:233). `tools/clone_check.sh:70` emits the steps with `docs_check.py --emit-steps
  README.md`; with no Windows block in the tree, step 2 fails, so `w4cc/rc` = 0 cannot happen.
- Fix: pick one and write it into W4. (a) Run W4's clone check against a `p7-int` bundle (with W6), `--branch
  p7-int`, so it tests the real README text without pushing it. Or (b) split W6: the README Windows block, marked
  "work in progress, not released", lands in W4; the claims (STATUS, release notes, "proven") stay in W6 for W9.
  (a) costs nothing and keeps W4's "no release claims" promise.

**[R2-B2] D5's OpenSSL Configure line is not the recipe that works.** Steps D5, W2b1.
- Evidence: plan:59-60 gives `Configure mingw64 no-shared --prefix=... --openssldir=...`. The toolkit's working A1
  recipe (`3ds-toolkit/tools/pc/build-ossl-win.sh`) is
  `CC=gcc-posix ./Configure mingw64 no-shared no-tests no-ssl3 no-ssl3-method no-zlib
  --cross-compile-prefix=x86_64-w64-mingw32- --prefix=... --openssldir=... --libdir=lib`, then `make build_libs`
  and `make install_dev`. Without `--libdir=lib`, OpenSSL 3's mingw64 target installs to `lib64`, but
  `build-core.sh:75,125,159` (copied into the win64 route) and gate_f2's link.txt check want `$prefix/lib/libssl.a`.
  Without `--cross-compile-prefix` and `CC=gcc-posix`, Configure picks the host gcc (A1's first run failed exactly
  here) or the win32 thread model, which also changes the GCC ident set (finding B4).
- Fix: copy A1's line verbatim and change only `--prefix` and `--openssldir`. Keep `build_libs` + `install_dev`
  (no docs, no tests: about 5 minutes less CI). Record the full Configure line in build.inputs.

**[R2-B3] The CI container fails on our own code before it builds anything.** Steps D4, W2b1, W5.
- Evidence: GitHub container jobs run as root unless told otherwise. `build-core.sh:18` is
  `[ "$(id -u)" -ne 0 ] || die "refusing to run as root"`, and the branch's win64 route keeps that line. The bare
  `ubuntu:26.04` image has no git (actions/checkout then falls back to the REST API, leaves no `.git`, and
  `build-core.sh:161`'s `git rev-parse HEAD || echo none` writes `head=none`; W5 catches it only after 40 minutes),
  no `perl` for `shasum` (`build-core.sh:66,81,148`), no python3 (for `untar_checked.py`), cmake, make, xz or curl.
  D4-fallback triggers only "for a reason not in our code" (plan:55), so this failure has no planned route.
- Fix: in `core-win64.yml`, a first step `apt-get update && apt-get install -y --no-install-recommends git
  ca-certificates curl perl python3 cmake ninja-build make xz-utils file gcc-mingw-w64-x86-64-posix
  g++-mingw-w64-x86-64-posix binutils-mingw-w64-x86-64` before checkout; then run the build as a non-root user
  (`useradd -m b; git config --system --add safe.directory "$GITHUB_WORKSPACE"; su b -c ...`). Or let
  `build-core-win64.sh` accept root when `CI=true` and `GITHUB_ACTIONS=true`, with a one-line reason. Use
  `sha256sum` where `shasum` is absent (the same `sha_of` fallback W2b2 adds to fetch.sh). Fail the job at once if
  `git rev-parse HEAD` fails.

## 3. Shoulds

**[R2-S1] Run every build-tree check in CI, not on the PC (also an hour saving).** Steps W2b1, W5, W7.
- Evidence: `tests/gate_f2.py` `keyblob_findings` needs the build tree: the CMakeLists drop-list check, `_od_findings`
  reads the `.o.d` *contents* and wants at least 1000 files, and "core newer than CMakeCache" is meaningless after a
  download. The plan's build-meta tarball carries "the `.o.d` list" (plan:52), not the contents, so the PC run in W5
  cannot pass these checks as written. The window search needs only the three key headers from Azahar's tarball
  (`core/PIN` drop list), not a 43 MB unpack on the PC (D10).
- Fix: in job 1, after the build: fetch the `core/PIN` tarball (sha-checked), extract only the three headers named in
  its drop list, run all of gate_f2 win64 (window search included) on the live tree, and write the PASS lines plus the
  DLL sha into the artifact as `gate_f2.txt`. On the PC, W5 checks the DLL sha against that file and runs only what
  must run there: the needle scan (needles never go to CI), PE machine, imports, UTF-16 strings. release_check's
  `--build-meta`/`--src` then read `gate_f2.txt` instead of a tree. Drops D10's PC fetch entirely.

**[R2-S2] Specify the fetch fallback exactly.** Steps D7, W2b2.
- Evidence: `fetch.sh:41` derives `REL_BASE` from `LAZ_RELEASE_BASE` or the GitHub URL; `get()` (`fetch.sh:68-87`)
  uses `curl -fsSL` and dies on a sha mismatch. "A 404 retries `REL_TAG_PREV`" (plan:67) cannot be tested as the W2b2
  gate says (plan:224): a missing `file://` file gives curl exit 37 and no HTTP code, never a 404. On MINGW64,
  fetch.sh picks the Windows zip (plan:214), so the PC gate never exercises the Mac zip's fallback.
- Fix: write into D7:
  (1) fall back on any download failure (curl exit != 0), never on a sha mismatch: a mismatch still deletes and dies.
  (2) The fallback uses the same pinned sha through `get()`.
  (3) `REL_BASE_PREV` comes from `LAZ_RELEASE_BASE_PREV`; when `LAZ_RELEASE_BASE` is set and the PREV variable is
  not, no fallback, so a test against a local base never reaches the network.
  (4) Print `fell back to v1.0.0 for <asset>` on stderr.
  (5) W2b2 gate: test with `LAZ_RELEASE_BASE` and `LAZ_RELEASE_BASE_PREV` as two local folders, with the test app (the
  one same-sha asset on the Windows path), plus a `LAZ_FETCH_OS=Darwin` override (or a host test of `get_fallback`)
  for the Mac zip. One sha-mismatch case must still die.
  (6) macos-live.yml on W9's push fetches the Mac zip from a v1.1.0 page that is still a draft, so it proves the real
  fallback for free. Record that run in W9.

**[R2-S3] Anchor `--inherit v1.0.0` to pinned digests.** Steps W2b2, W7, W9.
- Evidence: `mkrelease.sh --inherit` "checks each against v1.0.0's SHA256SUMS" (plan:195), downloaded from the same
  page, so the check is circular. Two of the seven inherited assets (core-build-v1.0.0, and SHA256SUMS itself) have no
  pin in the repo (section 0).
- Fix: pin `V1_0_0_SHA256SUMS=288c2a25...19bec` in mkrelease.sh and release_check.py. Check the downloaded SHA256SUMS
  against it first, then each asset against its line, and cross-check the five that already have repo pins.

**[R2-S4] Do not inherit check 16 wholesale.** Step W2b2.
- Evidence: `release_check.py:685-693` `macos_check` includes `wording_findings` (`:680`), which checks the *release
  notes* and *SOURCE.md* for "macOS 15 or later", and a README check. In v1.1.0 these three files are new, so
  inheriting check 16's NOTE (plan:203) skips the only check on the new texts.
- Fix: inherit only check 16's binary parts (the dylib's minos/arch). Keep `wording_findings` and the README check
  live on the v1.1.0 texts, and add the Windows twin ("Windows 10 or later, x64", whatever W6 settles).

**[R2-S5] Make the seven single-zip sites per platform, with a plant-red.** Step W2b2.
- Evidence: `release_check.py:102,128,297,303,345,447,808` each use `next(rel.glob("azahar_lazpy_libretro-*.zip"))`
  or `next(rel.glob("libazahar-py-core-build-*.tar.gz"))`. With two zips and two build-files assets, each site picks
  one arbitrarily (directory order differs between macOS and NTFS). `build_files_check` (`:447`) must use the v1.1.0
  member list (`build-core-win64.sh`, the toolchain file, the workflow).
- Fix: one helper `asset(platform, kind)` that fails if the glob matches anything other than exactly one file; each
  site loops over the platforms it applies to. Add a planted case: a third zip, and a v1.1.0 build asset missing the
  workflow file.

**[R2-S6] Container provenance and the GCC runtime source.** Steps D4, W2b1.
- Evidence: `ubuntu:26.04` is a moving tag; the 90-day retention means the CI log (the only build record besides
  build.inputs) expires. plan:175-176 says `apt-get source gcc-mingw-w64 mingw-w64` "plus the gcc-N-source package it
  names": `gcc-N-source` is a *binary* package (it ships the GCC tarball), so `apt-get source` does not fetch it;
  `deb-src` in 26.04 is in deb822 format (`/etc/apt/sources.list.d/ubuntu.sources`, `Types: deb deb-src`), not a
  `sources.list` line.
- Fix: pin the image by digest (`ubuntu:26.04@sha256:...`) and write it into build.inputs. Fetch with
  `apt-get source gcc-mingw-w64 mingw-w64` plus `apt-get download gcc-N-source`, with N from `dpkg-query -W
  gcc-mingw-w64-x86-64-posix`. Map each GCC ident to a package by `strings` over each linked archive in linkLibs.rsp,
  then `dpkg -S` on its path, not by guess. Optional: `actions/attest-build-provenance` (needs `id-token: write` and
  `attestations: write`) gives a permanent record; at minimum print the DLL sha in the log and copy the run log into
  the build-files asset.

**[R2-S7] The W9 diff gate misses files that control the build.** Step W9.
- Evidence: plan:326 diffs only `tools/build-core-win64.sh tools/toolchain-win64.cmake core/` from "the W4 commit".
  The CI build is also controlled by `.github/workflows/core-win64.yml` and `tools/untar_checked.py`, and both are in
  the v1.1.0 build-files asset (section 4). W4 can take fixes "on main before W5" (plan:262), so "the W4 commit" may
  not be the one built.
- Fix: diff from build.inputs' `head=` to v1.1.0 over exactly the build-files asset's member list (one list, used by
  both mkrelease and the gate).

**[R2-S8] Three gates are vacuous or can pass while hiding failures.** Steps W2a, W4, W7, section 5, section 7.
- `make -n` diff (plan:156): GNU make `-n` prints nothing for up-to-date targets, so on HEAD after `make` the diff
  compares a full listing with an empty one. Fix: `make -B -n`, both checkouts in fresh folders at the same depth
  (or paths normalised), and the step placed before `make`.
- Skips: `clone_check.sh:64` passes `-rf`, which does not list skips, so "the pytest log's skips are exactly section 6"
  (plan:293) cannot be read from the log. Fix: `-rs` (or `-ra`) plus `--junitxml`, and a small compare script
  (`tools/skips_check.py <junit> <allowed-list>`) that exits non-zero on any skip not in the list, with the message
  conditions (timing, symlink) checked.
- macos-live.yml (plan:160): no `LAZ_REQUIRE_EMULATOR=1`, so a failed fetch turns every slow test into a skip and the
  job "passes"; and with `continue-on-error`, the *run* is green whatever happens. Fix: set
  `LAZ_REQUIRE_EMULATOR=1`; STATUS uses the job's step outcome (`gh run view --json jobs`) and the pytest summary line
  (passed count > 0, 0 failed), never the run conclusion.

**[R2-S9] W10's skip list needs W7's environment.** Steps W7, W10, W2b2.
- Evidence: section 6 says W10 has "the same list as W7" (plan:425), but W7's list assumes `LAZ_STOCK_CORE` set and
  the fixture copied (plan:288-289). W10 sets neither, and `clone_check.sh:37` `env -i` drops `LAZ_STOCK_CORE` anyway.
- Fix: clone_check gets `--stock-core PATH` and `--fixture DIR` (passed into the clean env and copied, respectively).
  W10 uses both, or section 6 lists W10's own skips.

**[R2-S10] clone_check Windows mode details.** Step W2b2.
- Evidence: `clone_check.sh:37` builds `PATH=$PYBIN:...` unquoted inside an `eval`ed string. The PC's Python folder
  holds a space (section 0), so the env breaks. `clone_check.sh:67` calls `uptime`, absent in MSYS2. `:71`'s build
  block builds the test app with devkitARM, which the Windows README does not install.
- Fix: put the venv's `Scripts` folder (or the Python folder via `cygpath -u`) in PATH with quoting tested on the
  PC's real path, never written into a tracked file. Replace `uptime` with a portable load note (or none on Windows).
  Windows mode skips the build block and uses the release test app; say so in its log.

**[R2-S11] Don't push "Windows proven" before Guy's word.** Steps W9, W10, section 13.
- Evidence: W9 pushes main with W6's README/STATUS ("Windows proven", plan:240) and fetch pins, while the v1.1.0
  release is a draft until W10. In that window, a Windows user following main's README gets "v1.1.0 is not published
  yet" (D7), and the public README claims a release that does not exist.
- Fix: ask Guy for the publish word at the end of W8 (with the audit verdict), so W9 runs push, tag, draft and
  publish in one sitting. If he wants a gap, W9's README says "Windows: release pending" until W10 swaps the line.

**[R2-S12] OpenSSL source sha must be recorded and checked on Windows.** Steps W2b1, W2b2.
- Evidence: `build-core.sh:66` checks the tarball sha and `:159` records `openssl_libssl_sha256`, but nothing records
  the *source* sha in build.inputs; D5 says "same source tarball as macOS" with no gate.
- Fix: build.inputs records `openssl_src_sha256=`; the Windows check 6 compares it with `core/OPENSSL.md`'s
  `a2157c28...`, and with the inherited `openssl-3.6.5.tar.gz` asset.

**[R2-S13] The PC's `--pre-push` run needs the PC clone set up like the Mac's.** Steps W9.
- Evidence: `release_check.py:630-635` `pre_push_findings` reads `git config user.email` and `user.name` and the
  status in the repo it runs in. On the PC that is the bundle clone, not the Mac repo that pushes.
- Fix: in W9, set the no-reply identity in the PC clone (local config only), and check that the PC clone's HEAD equals
  the Mac commit about to be pushed (`git rev-parse HEAD` on both, compared in the log).

## 4. Nits

- [R2-N1] W5/core-win64 load test: load from a fresh empty folder with Python 3.8+ `ctypes.CDLL` default `winmode`,
  never `os.add_dll_directory`, and check the imports against the allow-list there too. Windows runner images put
  mingw and Strawberry DLLs on PATH; the default search does not use PATH for dependents, which is what we want. Note
  it in the script.
- [R2-N2] W9's digest copy check: SHA256SUMS has no line for itself. Compare its GitHub digest with the sha the PC
  computed at staging (W7 log).
- [R2-N3] The top-level SOURCE.md must also map `testapp.3dsx` (ours, built from the repo at the tag) and the Windows
  zip to the inherited nokeys source.
- [R2-N4] README Windows section: say a Vulkan-capable GPU driver is needed (System32 `vulkan-1.dll`), since CI cannot
  prove boots without one.
- [R2-N5] W1a: the stubs must leave `O_BINARY` undefined (macOS has none), or the `#ifndef O_BINARY` hunk is hidden.
- [R2-N6] `LAZ_WIN_PY` holds the local username: name it only in the main loop's env or an untracked file; never in
  runners.md, a log copied into the repo, or an agent brief. (The PC's path is private-needle material.)
- [R2-N7] Section 6's W4/CI allowed skips ("any skip of a test that needs a core") should be the same automated list
  (R2-S8's script) with a `needs_core` marker, so a new skip in a fast test fails.

## 5. Hour-saving pass

| # | Change | Saves |
|---|---|---|
| HS1 | R2-S1: window search and all build-tree checks in CI; drop D10's 43 MB PC fetch/unpack and the `--build-meta`/`--src` port of tree checks | 0.6-0.8 h |
| HS2 | Extract only the three key headers (drop list) instead of the whole Azahar tarball | 0.1 h CI/PC time |
| HS3 | R2-B2: use `build-ossl-win.sh` verbatim (`build_libs` + `install_dev`) | about 0.3 h of debug, about 5 min per CI run |
| HS4 | R2-S11: Guy's word at the end of W8; W9 and W10 in one sitting | 0.2 h of ours, hours of wall time |
| HS5 | R2-S2(6): macos-live on W9's push is the real fallback test; the PC test keeps only local folders | 0.1 h |
| HS6 | R2-S2(1): fall back on any download failure, not on parsed HTTP codes | 0.1 h |
| HS7 | R2-B1(a): W4 clone check on the `p7-int` bundle instead of splitting W6 | 0.2 h |

Net effect: about 1.4-1.8 h off the 17.1 h, against about 0.5 h added by R2-B3, R2-S5 and R2-S8. Revised total: about
16 h.

## 6. Ordering, file ownership, cost rules

- Order holds. Never two expensive agents: W1 (opus), then W1b (ip-legal) beside the four sonnets, W3 (opus), W8
  (release-legal-audit) beside W7c (main loop only). This revision and this review are sequential opus runs. OK.
- File ownership: clean, with one gap. `tools/build-core-win64.sh` (W2b1) and `tools/fetch.sh` (W2b2) both need the
  `sha_of` fallback; W2b1 should copy the three lines rather than source fetch.sh. R2-S1's `gate_f2.txt` reader lands
  in `release_check.py` (W2b2) and its writer in `gate_f2.py` (W2b1): fix the file format in the briefs so they meet.
- Mac rule: no Mac build or emulator step; `status_check.py` on the Mac reads only status files. OK.
- Push rule: main and the tag only; no scratch branch. OK. Publishing needs Guy's word (Q1). OK, but see R2-S11.
- PC rule: W7's up-to-4 copies need 2 + 4 x 0.6 = 4.4 GB free; today's 6.61 GB allows it. Announce and check free RAM
  right before W7 (and W10), as planned.
- Privacy: needles on stdin only (plan:87-90). `PRIVATE_RES` additions (plan:210) cover `/__w/` and `/github/home`
  for the CI paths. OK.

## 7. Is the fetch.sh fallback safe?

Integrity: yes. Every byte still goes through `get()` with the same pinned sha, and a mismatch deletes and dies, so
the fallback cannot deliver anything but the v1.0.0 bytes we already pinned. A draft v1.1.0 asset is a 404 to
anonymous users, so the fallback fires until Guy publishes, and the primary path works afterwards. Under-specified:
the trigger (404 vs any failure; `file://` gives no 404), the PREV base under `LAZ_RELEASE_BASE`, a stderr notice, and
the Mac-zip path that the PC test cannot reach. R2-S2 fixes all of these.

## 8. Licence

- OpenSSL: static, Apache-2.0, source inherited by bytes (sha anchored). OK with R2-S12.
- mingw runtimes: the plan ships the Debian copyright files, COPYING3 and COPYING.RUNTIME, and the source asset. That
  is the conservative route and fine. It needs R2-S6's correct fetch of the GCC tarball. W1b and W8 may still drop
  the asset; if they keep it, the top-level SOURCE.md must name it as the source for libstdc++, libgcc, winpthreads
  and the CRT.
- GPL source offer: the core's source (nokeys, inherited), the scripts that control compilation (v1.1.0 build-files
  asset, with R2-S7's full member list) and the runtime sources are all on the page. Complete with R2-N3.

## Verdict

Verdict: ready to execute after fixes. Blockers 3 (R2-B1 to R2-B3), shoulds 13 (R2-S1 to R2-S13), nits 7 (R2-N1 to
R2-N7). All three blockers are spec fixes local to W4, D5 and the workflow, not structural; the planner can apply them
in place without a third review loop.
