# Phase 7 plan: the Windows port proven (release v1.1.0)

Revision 2, 2026-11-17 12:10 IST, opus planner for the main loop (eb). This revision answers two things:
- Review 2 (`docs/reviews/phase-7-review-2.md`: 3 blockers, 13 shoulds and 7 nits, tagged [R2-*]; verdict "ready to
  execute after fixes").
- The main loop's decisions on review 2.

Revision 1 (5dc0a34) answered review 1 (tags [R1-*]); revision 0 is in git before it. Two reviews are done, so work
starts from this revision. The agent briefs are in `docs/plans/phase-7-briefs.md`. Item laz-700.

Guy, 2026-11-17: "update the repo so it says windows is ot proven and its a WIP. / and move forward so its windows
proven". The first half is done (a551d5f, pushed). This plan is the second half.

Guy, 2026-11-17, on pushing: "moev forward doesnt include push to github. but this time you can push to github".
- Pushes in this phase are main and the v1.1.0 tag only, never a scratch branch [R1-B5].
- Main is pushed only when the push cannot break existing users (D7) [R1-S1].
- The tag is pushed only after both CI files are green on its commit [R1-S2].
- Publishing the GitHub release needs Guy's word. It is asked for at the end of W8, with the audit verdict, so W9
  and W10 run in one sitting [R2-S11].

Guy, 2026-11-17, on the Mac: the Mac is closed to all 3DS work (emulators, builds, pytest, gates). It is for editing,
git, `gh` and ssh only (flag `~/.lazpy/PC_ONLY`).
- Every build and gate runs on the PC (MSYS2) or on GitHub's runners.
- No step has a "rerun on the Mac" fallback.
- A `lane-pc` exit 77 means "not run": requeue it on the PC.

## 1. What "Windows proven" means (the exit gate)

All of these hold, each with its evidence file:
- Branch `port-win-v1` is reviewed (one full opus diff review), fixed, and merged into main.
- Before the tag (W7): a clone of the candidate release commit, taken from the local bundle, passes on the PC. It
  follows only the README's Windows steps, builds the host, passes `make test-host`, and passes the full pytest with
  `LAZ_REQUIRE_EMULATOR=1`. Its skips are exactly section 6's list, checked by `tools/skips_check.py` [R2-S8].
- After publishing (W10): the same clone check passes from GitHub main and the real release URLs. This is the
  "fresh clone of GitHub" proof [R1-S1].
- The Windows core is built in GitHub CI from main. All of gate_f2 runs on the live build tree there, including the
  window search. The core loads on a clean windows-2025 runner with no extra runtime DLLs (W5) [R1-S11, R2-S1].
- `test.yml` and `test-windows.yml` are green on the tagged commit (W9) [R1-S2].
- The macOS side is shown unchanged by section 7's three parts, without running anything on the Mac.
- release-legal-audit says v1.1.0 is shippable, and `release_check.py --pre-push` passes every check on the PC.
- README, STATUS and USING say "Windows: proven on one PC" with the exact limits (section 6). No speed claims.

## 2. Decisions taken by default (Guy may overrule; each is reversible until the tag push)

**D1. Version 1.1.0.** Windows support is an addition, so it is a minor release (owner condition 1).

**D2. The Mac side of v1.1.0 is inherited from v1.0.0 by checksum** [R1-B3, R1-B4, R2-S3].
- `mkrelease.sh` and `release_check.py` pin `V1_0_0_SHA256SUMS=288c2a257948498bb5c0f4e56a582ee311fd6654aa523b51fc85876e5ce19bec`
  (the GitHub digest of v1.0.0's SHA256SUMS).
- The steps:
  1. Download v1.0.0's SHA256SUMS from the v1.0.0 page and check it against that pin.
  2. Download seven assets from the same page and check each against its line in SHA256SUMS: the Mac core zip,
     `NOTICES.md`, the nokeys source, `openssl-3.6.5.tar.gz`, the citra snapshot, `testapp.3dsx`, and
     `libazahar-py-core-build-v1.0.0.tar.gz`.
  3. Cross-check five of them against the pins the repo already holds: the nokeys source (`core/PIN-nokeys`), OpenSSL
     (`core/OPENSSL.md`), the snapshot (`mkrelease.sh` `SNAP_SHA`), NOTICES.md (the repo file), and the Mac zip and
     test app (`fetch.sh`).
  4. Upload all seven byte-identical.
- Nothing is rebuilt for the Mac, and nothing runs on the Mac.
- `git diff v1.0.0 -- NOTICES.md tools/build-core.sh core/PIN core/PIN-nokeys core/patches` stays empty. Today it is.

**D3. `tools/build-core.sh` stays byte-identical to v1.0.0.**
- The branch's win64 case moves into a new `tools/build-core-win64.sh`.
- Its OpenSSL part is copied from the toolkit's `tools/pc/build-ossl-win.sh` (D5) [R1-N3].
- gate_f2 takes the build script per target [R1-S4].

**D4. The Windows core is built in GitHub CI** [R1-B1].
- Where: `.github/workflows/core-win64.yml`, which runs only on `workflow_dispatch`, on main. It has three jobs.
- Job 1, the build:
  - Runs on ubuntu-latest, in the container `ubuntu:26.04@sha256:<digest>`. The digest is pinned and recorded in
    build.inputs [R2-S6].
  - The first step installs, before checkout: `apt-get install -y --no-install-recommends git ca-certificates curl
    perl python3 cmake ninja-build make xz-utils file gcc-mingw-w64-x86-64-posix g++-mingw-w64-x86-64-posix
    binutils-mingw-w64-x86-64` [R2-B3].
  - The build runs as a non-root user: `useradd -m b`, `git config --system --add safe.directory "$GITHUB_WORKSPACE"`,
    then `su b -c ...`. `build-core-win64.sh` keeps v1.0.0's refusal to run as root.
  - The job fails at once if `git rev-parse HEAD` fails, so `head=none` cannot happen [R2-B3].
  - Where `shasum` is absent, the job uses `sha256sum`, through the same three-line `sha_of` fallback that fetch.sh
    gets (copied, not sourced) [R2-B3].
  - After the build, all of gate_f2 win64 runs on the live tree, including the window search (D10) [R2-S1].
  - It runs mknotices win64 and fetches the mingw runtime source (D13).
  - It writes `gate_f2.txt` (section 3, W2b1) and uploads one artifact: the DLL, build.inputs,
    `NOTICES-windows-x64.md`, `gate_f2.txt` and the runtime source tar. It prints the DLL's sha256 in the log.
  - It adds `actions/attest-build-provenance` for the DLL (`id-token: write`, `attestations: write`). That is a
    permanent record, because logs expire after 90 days [R2-S6].
- Job 2, the load test, on windows-2025:
  - Downloads the artifact into a fresh empty folder.
  - Loads the DLL with Python 3.10's `ctypes.CDLL`, with the default `winmode` and never `os.add_dll_directory`. The
    default search does not use PATH for dependents, so mingw or Strawberry DLLs on the runner's PATH cannot hide a
    missing runtime DLL [R2-N1].
  - Reads `retro_api_version` and every `lazpy_*` export.
  - Checks the imports against the allow-list.
  - Fails on any load error [R1-S11].
- Job 3, the leak check, on ubuntu-latest, `needs: [build]`, `permissions: actions: read`:
  - Downloads job 1's log through the API and the artifact.
  - Re-extracts the three key headers (D10).
  - Runs gate_f2's 16-byte window search over the log text and every artifact file.
  - Deletes the headers.
  - Fails on any hit. It prints only counts, never bytes.
- The PC's old private core DLL (`EFD22238...`) never ships (finding B1).

**D4-fallback.** Use WSL on the PC only if job 1 fails twice for a reason outside our code, meaning outside the repo
and the workflow (the image or the runners) [R2-B3].
- Build in `/var/tmp/lazpy-w5`, which survives a WSL restart.
- Start WSL only when C: has at least 34 GB free and the free-memory rule allows a 12 GB VM.
- One session only, announced on the PC board, with `wsl --shutdown` after.
- Never the Mac [R1-B1, R1-N5].

**D5. OpenSSL for Windows** [R2-B2, R1-S8].
- The toolkit's A1 recipe is copied verbatim, with only `--prefix` and `--openssldir` changed:
  `CC=gcc-posix ./Configure mingw64 no-shared no-tests no-ssl3 no-ssl3-method no-zlib
  --cross-compile-prefix=x86_64-w64-mingw32- --prefix=/opt/lazpy/openssl-3.6.5-mingw64
  --openssldir="C:/Program Files/Common Files/SSL" --libdir=lib`, then `make build_libs` and `make install_dev`.
- The prefix is a real, neutral path with no spaces and no username, so build.inputs needs no masking (finding B2
  closes). Job 1 creates `/opt/lazpy` owned by user `b`.
- build.inputs records:
  - the full Configure line;
  - `openssl_src_sha256=`, which must equal `core/OPENSSL.md`'s `a2157c28...` and the inherited
    `openssl-3.6.5.tar.gz` asset [R2-S12];
  - the OPENSSLDIR, ENGINESDIR and MODULESDIR strings found in the DLL. USING's CA row quotes them.
- `core/OPENSSL.md` gets a Windows section.
- The source tarball is fetched from the v1.0.0 page.

**D6. No prebuilt Windows host binaries.** Users build `libazhost.dll` and `azhost.exe` with MSYS2 `make`, as macOS
users run `make`. (Open question Q2.)

**D7. fetch.sh's fallback, so pushing the pins breaks no existing user** [R1-S1, R2-S2].
1. Pins: `REL_TAG=v1.1.0` and a new `REL_TAG_PREV=v1.0.0`.
2. When the fallback fires: only for an asset whose pinned sha is the same in both releases (the Mac zip and the test
   app), and only after a download failure on `REL_TAG` (any non-zero curl exit, with no HTTP code parsing). It then
   tries `REL_TAG_PREV` once.
3. A sha mismatch never falls back. It still deletes the file and dies.
4. The fallback goes through the same `get()` with the same pinned sha.
5. `REL_BASE_PREV` comes from `LAZ_RELEASE_BASE_PREV`, or else from the GitHub URL for `REL_TAG_PREV`. When
   `LAZ_RELEASE_BASE` is set and `LAZ_RELEASE_BASE_PREV` is not, there is no fallback, so a test against a local base
   never reaches the network.
6. It prints `fell back to v1.0.0 for <asset>` on stderr.
7. `LAZ_FETCH_OS` overrides `uname -s`, so the PC can test the Mac zip path.
8. The Windows zip has no fallback. Before publishing, fetch says "v1.1.0 is not published yet".
9. The rule "REL_TAG follows the newest tag" (phase-v1 section 1) still holds.
10. The real-world test is `macos-live.yml` on W9's push of main. At that point v1.1.0 has no published assets, so its
    Mac fetch must print the fallback line and pass the sha check.

**D8. Windows fetch is the same `tools/fetch.sh`, run in the MSYS2 MINGW64 shell.** No PowerShell twin.

**D9. The release tools run on the PC in MSYS2 with the Windows Python** [R1-N6, R2-N6].
- `LAZ_WIN_PY` is the existing venv's interpreter, `C:\lazpy\venv\Scripts\python.exe`. That path holds no username.
  Never a bare `python3`: on the PC that is 3.7, or the Store alias.
- clone_check needs a base interpreter to make a fresh venv. It reads it at run time from the `home =` line of
  `C:\lazpy\venv\pyvenv.cfg`. That path holds the local username, so it is never written into a tracked file, a
  brief, or a log copied into the repo.
- These run on the PC: mkrelease (Windows mode), release_check, and the PE, needle and UTF-16 scans.
- `gh` runs on the Mac, because it is a GitHub operation. Bytes move between the Mac and the PC over ssh.

**D10. The key search runs only in CI** [R1-B2, R2-S1].
- Job 1 fetches Azahar's own tarball pinned in `core/PIN` and checks its sha (`85c8b56f...`).
- It extracts only the three headers in `core/PIN`'s drop list (`default_keys.h`, `ctr-common-1-cert.h`,
  `ctr-common-1-key.h`), into `$RUNNER_TEMP/keyhdr`, outside the workspace.
- It deletes them before the artifact upload.
- The headers never land in an artifact, a log line or the repo. Job 3's leak check is the gate for that. The PC
  fetches nothing.

**D11. Users on the release candidate (W7c) have no deadline,** as in phase-v1's D6. W8 runs during the wait
[R1-S13].

**D12. Owner conditions hold.**
- Condition 3: main's Makefile lines stay as they are for macOS, in the sense of section 7's `make -B -n` test
  [R1-S5].
- Condition 5: `DEFAULT_CAP` stays 4.
- Condition 7: no Linux asset.

**D13. The mingw runtime source** [R1-S10, R2-S6].
- Job 1 runs `apt-get source gcc-mingw-w64 mingw-w64`. The deb-src line goes in deb822 form: `Types: deb deb-src` in
  `/etc/apt/sources.list.d/ubuntu.sources`.
- It also runs `apt-get download gcc-N-source`, a binary package that carries the GCC tarball. N comes from
  `dpkg-query -W gcc-mingw-w64-x86-64-posix`.
- It packs them as `mingw-w64-runtime-source.tar`.
- Each GCC ident in the DLL is mapped to a package from evidence, not guessed: `strings` over each archive named in
  linkLibs.rsp, then `dpkg -S` on that archive's path. The map goes in build.inputs.
- The asset is dropped only if W1b and W8 both say it is not needed.

**D14. Branches** [R2-B1].
- `p7-int` comes off port-win-v1 and takes the merges of W2a, W2b1 and W2b2.
- `p7-docs` comes off `p7-int` and takes W6.
- W4 merges `p7-int` into main.
- W4's clone check runs on a bundle of `p7-docs`, so it tests the real README Windows block without pushing it.
- W7 merges `p7-docs` plus the pins into local main.

## 3. Steps, in order

Each step gets an item under laz-700 (ids 701-714, created by W0). Hours book to `phase-7`. Evidence lives under
`runs/p7/<step>/` (gitignored), and the item's Evidence line names it.

"PC runner" means `tools/pc/lane-pc`, or the plain ssh runner in docs/map/runners.md.

`$NEEDLES` is the private-needle list: the local usernames on the Mac and the PC, and Guy's real email.
- It lives only in the main loop's environment.
- It reaches the PC only on stdin, as `LAZ_PRIVATE_NEEDLES`.
- It never appears in argv, in a file on the PC, in a log, in CI, or in an agent brief [R1-N4].
- Only the main loop runs the needle scan.

Order:
1. W0, W1a, W1.
2. W2a, W2b1, W2b2 and W6 (four sonnet agents), with W1b in the expensive slot.
3. W3, W4, W5, W7.
4. W7c and W8 side by side. Guy's publish word is asked for at the end of W8.
5. W9 and W10 in one sitting.

Never two expensive agents (opus, ip-legal, release-legal-audit) at once. Main-loop steps carry a numbered checklist;
delegated steps point to their brief.

**W0. Items and pre-flight.** Owner: main loop. 0.3 h.
1. Create items 701-714 and rewrite the handoff. On the Mac, run `python3 -I tools/status_check.py --strict-handoff`.
   It reads status files only, so it is no 3DS work.
2. Read-only PC pre-flight:
   - free disk on C: and D:, and free RAM;
   - the MSYS2 packages, and the version of `C:\lazpy\venv\Scripts\python.exe`;
   - Developer Mode. Review 2 found it off, so the account cannot make symlinks and the symlink skip is allowed.
3. Announce on the PC board, then on the PC run `pacman -S --needed zip unzip` (mkrelease needs zip, fetch needs
   unzip).
4. Make the worktrees for W2a, W2b1, W2b2 and W6 at the port-win-v1 tip.

Gate: status_check exits 0. `runs/p7/w0/preflight.txt` lists every tool with its version, and the symlink answer.

**W1a. Darwin-visible diff, on the PC.** Owner: main loop. 0.25 h. [R1-B5, R2-N5]
1. Write `runs/p7/w1a/darwin_pp.sh`. It holds the stub folder: an empty file for every system header either tree
   includes. The stubs define nothing, so `O_BINARY` stays undefined, as on macOS.
2. On the PC, with MSYS2 gcc, run this over `host/*.c tests/host/*.c tests/test_version.c` for v1.0.0 and for the
   branch tip, each in a fresh folder at the same depth:
   `gcc -E -P -undef -nostdinc -isystem <stubs> -D__APPLE__=1 -D__MACH__=1 -D__arm64__=1 -D__aarch64__=1
   -D__LP64__=1 -D__clang__=1 -D__STDC_VERSION__=201112L -Ivendor -Ivendor/include -Ihost`
3. In the same two folders, before any build, run `make -B -n all test-host test-version check` with MSYS2's make,
   and normalise the folder paths [R2-S8].

Gate: `runs/p7/w1a/darwin-pp.diff` and `runs/p7/w1a/make-n.diff` exist. A planted `#ifdef __APPLE__` line in a
scratch copy shows up in the diff (the stub method is not blind).

**W1. Full diff review of port-win-v1.** Owner: opus agent. 1.25 h. Brief W1.
Gate: `docs/reviews/phase-7-diff-review.md` has:
- the findings P7-R1-n, each with a severity and a file:line;
- the three Darwin-visible sections (C, Makefile, Python), each complete;
- the owner conditions quoted [R1-S5].

**W1b. Licence delta.** Owner: ip-legal agent, in the expensive slot while W2 runs. 0.25 h. Brief W1b.
Gate: `docs/reviews/phase-7-ip-legal.md` answers each question with yes, no or a named action.

**W2a. Fixes: host, Python, tests, Makefile, CI files.** Owner: sonnet agent. 2.0 h. Brief W2a.
- Gate (on the PC): `make check && make && make test-host && make test-version` in a clean MINGW64 shell.
- Then the fast pytest through `skips_check.py --fast`, and `skips_check.py --self-test` (W2a owns it).
- Then `make -B -n HOST_OS=Darwin ...` equals v1.0.0's except the check-obinary line.

**W2b1. Fixes: the Windows core build route.** Owner: sonnet agent. 2.75 h. Brief W2b-build.
- Gate: gate_f2's planted reds pass on the PC with the toolkit's known DLL (the window-search case uses a fake
  header).
- `git diff v1.0.0 -- tools/build-core.sh` is empty.
- `actionlint` shows no error in `core-win64.yml`. actionlint runs on the PC: it is a Go binary for Windows, fetched
  once into `D:\lazpy\tools`.

**W2b2. Fixes: the release tools.** Owner: sonnet agent. 2.5 h. Brief W2b-release.
- Gate (on the PC): `release_check.py --plant-red` exits 0, and each new planted case fails as expected.
- The fetch fallback tests pass: two local folders, the `LAZ_FETCH_OS=Darwin` case, and the sha-mismatch case.

**W6. Docs, version, release notes.** Owner: sonnet agent (edits only), on branch `p7-docs`. 1.0 h. Brief W6.
- Gate: on the PC after W4, `docs_check.py` exits 0.
- The new wording checks (R2-S4) pass on its texts.

**W3. Check of the fix diff.** Owner: opus agent. 0.75 h. Brief W3. Before it starts, the main loop does this
(0.2 h):
1. Merge W2a, W2b1 and W2b2 into `p7-int`, then W6 into `p7-docs` (D14).
2. Run `python3 -I tools/mkmap.py` and `map_check.py`. They read repo text only, with no 3DS work.
3. Rerun W1a's two diffs on `p7-int` on the PC.

Gate: `docs/reviews/phase-7-fix-check.md` gives every P7-R1 finding and every R1/R2 finding claimed by W2 or W6 one
of "fixed", "not fixed" or "moved", with the commit. Zero blockers are "not fixed".

**W4. Merge and push main (no release claims).** Owner: main loop. 1.0 h.
1. `git merge --no-ff p7-int` into local main, committed as the no-reply identity. W6 is not in it (D14).
2. Bundle main and `p7-docs` to the PC.
3. On the PC, in a fresh tree from the main bundle (`D:\lazpy\p7\w4`):
   - `make check && make && make test-host && make test-version`;
   - the fast pytest through `skips_check.py --fast`;
   - `test_state_boot` alone, three times on a quiet PC. This is the owed state-restore rerun.
4. On the PC: `sh tools/clone_check.sh --until host --repo <p7-docs bundle> --branch p7-docs --out
   D:/lazpy/p7/w4cc`. This is the first real Windows-mode run [R1-S14, R2-B1]. `--until host` drops fetch.sh's
   `--lazpy-core --testapp` flags and says so in its log, because the Windows pin does not exist yet.
5. Push main. Users are safe: fetch.sh still says v1.0.0, and README still says Windows is a work in progress.
6. Run `gh run watch` on test.yml (including its `make -B -n` and vtool steps) and on test-windows.yml. Record the
   step outcome of macos-live.yml's pytest step [R2-S8].

Gate:
- The PC logs show 0 failed, and `test_state_boot` passes 3/3.
- `D:/lazpy/p7/w4cc/rc` is 0.
- test.yml and test-windows.yml are green on the merge commit. If one is red, fix it on main before W5.

**W5. Build the Windows core in CI and check it on the PC.** Owner: main loop, because the needle scan stays with the
main loop. 0.4 h, plus about 40 minutes of CI wall time. [R1-B1, R2-S1]
1. `gh workflow run core-win64.yml --ref main`, then `gh run watch`. All three jobs must be green: build, load test
   and leak check.
2. Run `gh run download` on the Mac (a GitHub operation), then copy the artifact to `D:\lazpy\p7\w5\` over ssh.
3. On the PC:
   - Check that the DLL's sha matches `gate_f2.txt` and the job log line.
   - Check that `gate_f2.txt` has every PASS line, its `head=` and the image digest.
   - Check the PE machine and the imports, delay-loads included.
   - Run the needle scan with `$NEEDLES` on stdin, over `strings -a` and `strings -el` of the DLL, build.inputs and
     the NOTICES.
4. Boot the test app once with the W4 host. This is a smoke test, not proof [R1-S14].

Gate: `runs/p7/w5/checks.txt` holds every PASS line, the run id, the artifact sha and the attestation URL. The needle
scan has 0 hits, and every GCC ident has a package line.

**W7. Stage the release and prove the clone, before any release push.** Owner: main loop. 1.0 h. [R1-S1]
1. On the PC, in MSYS2: `sh tools/mkrelease.sh --inherit v1.0.0 --win-artifact D:/lazpy/p7/w5 --out
   D:/lazpy/rel/v1.1.0`. Record the sha of the staged SHA256SUMS in the W7 log [R2-N2].
2. On the Mac, commit the pins on `p7-docs`: `REL_TAG=v1.1.0`, `REL_TAG_PREV=v1.0.0`, `LAZPY_CORE_ZIP_WIN` and
   `LAZPY_CORE_SHA_WIN`. The Mac pin and `TESTAPP_SHA` are unchanged. Merge `p7-docs` into local main as the
   candidate release commit. Do not push.
3. Check free RAM. It must be at least 4.4 GB for 4 copies (2 + 4 x 0.6 GB). Announce on the PC board.
4. Bundle main to the PC.
5. On the PC: `sh tools/clone_check.sh --repo <bundle> --branch main --out D:/lazpy/p7/w7 --release-base <file URL of
   D:/lazpy/rel/v1.1.0> --stock-core C:/lazpy/probe/azahar_libretro.dll --fixture <copied v1.0.0 fixture dir>`
   [R2-S9]. It runs:
   - the README Windows steps;
   - `make test-host`;
   - the quickstart;
   - the full pytest with `LAZ_REQUIRE_EMULATOR=1 -rs --junitxml`, then `skips_check.py --list w7`.
6. On the PC: `$LAZ_WIN_PY -I tools/release_check.py D:/lazpy/rel/v1.1.0 --inherit v1.0.0 --gate-f2
   D:/lazpy/p7/w5/gate_f2.txt`, without `--pre-push`, with `$NEEDLES` on stdin.

Gate:
- `D:/lazpy/p7/w7/rc` is 0, and `skips_check` exits 0.
- `test_release_fixture` ran and passed. If it did not, its failure is a documented difference in the release notes,
  and W8 signs it off.
- release_check prints no FAIL.

**W7c. Users on the release candidate.** Owner: main loop (eb, the PC-runner owner). 0.3 h. Runs beside W8.
[R1-S13]
1. Make a release-candidate deploy id from the W7 host and the W5 core. The default deploy is not switched.
2. Ask Gen3D and 3DPlatinum to run their next normal job on that id. This proves the core and `azhost.exe` through
   the toolkit's job path. W7 covers the README's Python path.

Gate: each project's job log line names the release-candidate deploy id and says PASS. There is no deadline (D11).

**W8. Legal audit, then Guy's publish word.** Owner: release-legal-audit agent, in the expensive slot. 0.75 h, plus
0.5 h of fixes. Brief W8. Runs beside W7c.
1. Run the audit. Fixes go in, and the main loop re-stages. If a fix touches anything outside `docs/reviews/`,
   `docs/status/` and `docs/hours.tsv`, the main loop reruns W7's clone_check.
2. At the end, the main loop asks Guy for the publish word, giving him the audit verdict and W7's results [R2-S11].
   If Guy wants a gap between the push and publishing, W9's README says "Windows: release pending", and W10 changes
   that line to "proven".

Gate: `runs/reviews/release-legal-audit-v1.1.0.md` says shippable. It is kept private and gitignored, as v1.0.0's
was. Guy's word is quoted in item 712.

**W9. Final gate, push main, CI green, tag, draft, publish.** Owner: main loop. 0.5 h. Needs Guy's word from W8.
[R1-S2, R2-S7, R2-S13]
1. In the PC's bundle clone, set the no-reply identity in its local git config only. Check that `git rev-parse HEAD`
   on the PC equals the Mac commit about to be pushed, and write both into the log.
2. On the PC, with `$NEEDLES` on stdin: `$LAZ_WIN_PY -I tools/release_check.py D:/lazpy/rel/v1.1.0 --pre-push
   --inherit v1.0.0 --gate-f2 D:/lazpy/p7/w5/gate_f2.txt`. Every check must PASS or print the inherited NOTE.
3. Build-files gate: `git diff <build.inputs head=> HEAD -- $(cat tools/build-files.txt)` is empty. That file is the
   one member list, used by both mkrelease and this gate [R2-S7].
4. Push main. Then `gh run watch` until test.yml and test-windows.yml are green on that commit. If either is red,
   fix it, re-gate and push again. No tag before green.
5. Record macos-live.yml's fetch step on this push: it must show `fell back to v1.0.0` and pass. This is D7's
   real-world test [R2-S2].
6. Tag `v1.1.0` (annotated, no-reply identity) on that commit and push the tag.
7. Copy the staged folder from the PC to the Mac over ssh. Then run `gh release create v1.1.0 --draft --verify-tag
   --notes-file docs/release-notes/v1.1.0.md` with every asset.
8. Copy check: read the asset names and digests with `gh api repos/GuyShtainer/libazahar-py/releases --jq '.[] |
   select(.tag_name=="v1.1.0") | .assets[] | [.name,.digest]'`. Each digest must equal its SHA256SUMS line. The
   digest of SHA256SUMS itself must equal the sha W7 logged [R2-N2]. Nothing is hashed on the Mac.
9. Publish: `gh release edit v1.1.0 --draft=false`, on Guy's word from W8.

Gate: steps 2, 3, 4, 5 and 8 each logged PASS in `runs/p7/w9/`. `gh release view v1.1.0 --json isDraft` shows false.

**W10. Post-publish checks.** Owner: main loop, in the same sitting as W9. 0.2 h.
1. On the PC, `curl` every asset from the real URLs into a new folder and check SHA256SUMS.
2. On the PC: `sh tools/clone_check.sh --repo https://github.com/GuyShtainer/libazahar-py --branch main --out
   D:/lazpy/p7/w10 --stock-core C:/lazpy/probe/azahar_libretro.dll --fixture <same>`, with no `--release-base`
   [R2-S9].
3. If W8 chose the gap wording, swap the README line, push, and see CI green.

Gate: `runs/p7/w10/` holds the checksum output, clone_check's `rc` of 0, and `skips_check --list w7` exit 0. Item 700
moves to done.

## 4. The v1.1.0 assets and their licences

| Asset | What | Licence and source |
|---|---|---|
| `azahar_lazpy_libretro-2126.2-lazpy.2-macos-arm64.zip` | v1.0.0 bytes (`ced9a362...`), inherited | as v1.0.0 |
| `libazahar-py-core-build-v1.0.0.tar.gz` | v1.0.0 bytes (`7a4d9c52...`), inherited; the Mac zip's SOURCE.md names it [R1-B4] | GPLv3 |
| `NOTICES.md` | v1.0.0 bytes, inherited (Mac notices) | |
| `azahar-unified-source-2126.2-lazpy-nokeys.tar.xz` | v1.0.0 bytes, inherited; the core's source on both platforms | GPLv3 |
| `openssl-3.6.5.tar.gz` | v1.0.0 bytes, inherited | Apache-2.0 |
| `citra_system_archives-f470e0c.tar.gz` | v1.0.0 bytes, inherited | as v1.0.0 |
| `testapp.3dsx` | v1.0.0 bytes (`ba106998...`), inherited; built from `testapp/` in the repo | ours, GPLv3 |
| `azahar_lazpy_libretro-2126.2-lazpy.2-windows-x64.zip` | the DLL, NOTICES.md (Windows), SOURCE.md (Windows), LICENSE, COPYING-azahar.txt, build.inputs | GPLv3 (Azahar, ours); OpenSSL Apache-2.0; libstdc++/libgcc GPLv3 + Runtime Exception; winpthreads MIT-style; mingw-w64 CRT ZPL and public domain |
| `NOTICES-windows-x64.md` | the Windows zip's NOTICES.md, also on the page | |
| `libazahar-py-core-build-v1.1.0.tar.gz` | `git archive` of the members in `tools/build-files.txt`: `core`, `tools/build-core-win64.sh`, `tools/toolchain-win64.cmake`, `tools/untar_checked.py`, `.github/workflows/core-win64.yml` [R2-S7] | GPLv3 |
| `mingw-w64-runtime-source.tar` | D13's source packages | as packaged (GPLv3 + RLE, ZPL, MIT-style) |
| `SOURCE.md` | maps each binary to its source. The Mac zip maps to the v1.0.0 build-files asset. The Windows zip maps to the v1.1.0 build-files asset, the nokeys source, OpenSSL and the runtime source (for libstdc++, libgcc, winpthreads and the CRT). `testapp.3dsx` maps to the repo at the tag [R1-B4, R2-N3] | |
| `SHA256SUMS` | sha256 of every other asset | |

What the binaries link:
- The core DLL imports only Windows system DLLs: ADVAPI32, bcrypt, CRYPT32, KERNEL32, msvcrt, ole32, SHELL32,
  USER32, WINMM and WS2_32. libstdc++, libgcc and winpthreads are linked statically. msvcrt.dll is a Windows system
  library. No MSVC runtime is used or shipped. Job 2 proves that no other DLL is needed.
- OpenSSL 3.6.5 is linked statically (D5).
- Vulkan: the host loads `vulkan-1.dll` from System32 only. On the PC that is the loader the NVIDIA driver installs
  (1.4.341, driver 610.88). Nothing Vulkan ships. Mesa dzn is not used.
- The host is not shipped. The user builds it with MSYS2 MINGW64 gcc, using `-static -static-libgcc` and a static
  zlib from `/mingw64`. It imports bcrypt, KERNEL32 and msvcrt, so the host and the core share one C runtime. The
  Makefile refuses the other MSYS2 shells [R1-S12].
- Corresponding source: every shipped binary's source is on the v1.1.0 page and in the repo at the tag. W8 gates
  this.

## 5. CI

`test-windows.yml` runs on `windows-2025`.
- It pins its actions by sha: `actions/checkout`, `actions/setup-python` (3.10 and 3.14), and `msys2/setup-msys2`
  (W2a records that sha with `gh api`).
- It uses MINGW64 with `path-type: inherit`, and installs the README's pacman packages plus
  `mingw-w64-x86_64-clang` [R1-S6].
- Steps: `sh tools/fetch.sh --headers`, `make check`, `make`, `make test-version`, `make test-host`,
  `pip install -e . pytest numpy`, then `python -m pytest -q -m "not slow" -rs --junitxml=...` followed by
  `skips_check.py --fast` [R2-N7].
- It checks:
  - that the README's package list builds the host on a clean machine;
  - the host C tests (about 308,000 checks);
  - check-obinary and the clang analysis of the Windows sources;
  - the Python layer without a core.
- It cannot check: a core boot, frames, screenshots, states, the pool, timing, or anything that needs a GPU. The
  runners have no GPU and no Vulkan driver. These are proven on the PC in W4, W7 and W10.

`core-win64.yml` holds D4's three jobs.

`test.yml` (macos-15) gains two steps:
- A `make -B -n` diff. It runs before `make`, on a `v1.0.0` worktree (`fetch-depth: 0`) and on HEAD, at the same
  path depth, with the paths normalised [R2-S8].
- `vtool -show-build build/libazhost.dylib` must show minos 15.0 and arm64.

`macos-live.yml` (section 7) is best-effort:
- It sets `continue-on-error` at the job level and `LAZ_REQUIRE_EMULATOR=1` on its pytest step.
- Its result is read from that step's outcome (`gh run view --json jobs`) and its summary line (passed > 0, 0 failed),
  never from the run's conclusion [R2-S8].

Blocking: there is no branch protection. A red run blocks because W9 pushes the tag only after test.yml and
test-windows.yml are green [R1-N2].

## 6. Version, the 1.0 promise on Windows, and the limits

v1.1.0. The 1.0 promise (top of USING, phase-v1 section 1) holds on Windows. These differences are documented in a
USING table:
- File names: `libazhost.dll`, `azhost.exe` and `azahar_lazpy_libretro.dll`.
- `LAZ_MVK` names the Vulkan loader. The default is `vulkan-1.dll` from System32. A GPU driver with Vulkan is
  required [R2-N4].
- `LoadWarning` is never raised.
- The worker runs at BELOW_NORMAL priority instead of a nice value.
- Slots live in `%LOCALAPPDATA%\libazahar-py\slots`. `Slot.fd` is a HANDLE.
- Paths must be ASCII and under 260 characters, so clone into a path like `C:\src` [R1-N7].
- The SD folder is case-insensitive.
- `runs/` behind a junction is not supported.
- States between macOS and Windows: W7 tests them with the v1.0.0 fixture, and the result goes in the release notes.
- The guest's HTTPS finds a CA file only at the compiled-in OPENSSLDIR, quoted from build.inputs.

Limits, written in STATUS, in the wording W6 settles. release_check's Windows wording check holds STATUS and the
release notes to that wording [R2-S4].
- Proven on one PC only: Windows 10 Pro 22H2, x64, RTX 3060, NVIDIA driver 610.88, Python 3.10.11.
- CI adds Windows Server 2025 for the build, the fast tests and the core load test.
- Windows 11 and AMD and Intel GPUs are untested.
- No Windows speed figures (rule 7). The instance cap stays 4.

Allowed skips are checked by `tools/skips_check.py <junit> --list <name>` [R1-S7, R2-S8, R2-N7]. It exits non-zero on
any skip not on the named list, and it checks the message conditions.
- `--fast` (W2a, W4 and CI): only skips whose message comes from conftest's core, host or emulator fixtures, plus the
  win32 by-design skips below. Any other skip in a fast test fails.
- `--list w7` (W7 and W10, with `--stock-core` and `--fixture` given), exactly these:
  - `test_threads_live.py::test_k_threads_lazpy1_core` and `test_threads_live.py::test_k_states_both_ways`: there is
    no lazpy.1 Windows core.
  - `test_slots.py::test_s5_load_warning`: by design. `test_s5_windows_has_no_load_warning` runs in its place.
  - `test_lazpy_profile.py::test_worker_nice_floor`, in all its cases.
  - `test_api.py::test_long_batch_outlives_a_short_timeout`, only with the "not longer than the timeout" message.
  - `test_arguments.py::test_clear_sd_refuses_a_symlink`, only with the "cannot create a symlink" message (Developer
    Mode is off).
  - `test_map.py`'s numpy importorskip is not allowed, because clone_check installs numpy.
  - `test_release_fixture.py` and `test_profile_format.py` must run, not skip.

## 7. macOS unchanged, without the Mac [R1-S5]

1. The Mac assets are v1.0.0's bytes, checked against pinned digests (D2). `tools/build-core.sh` and the core pins
   are v1.0.0's bytes.
2. C: W1a's stub-header preprocess diff on the PC. The stubs leave `O_BINARY` undefined. W1 reviews every hunk, and
   W3 checks them again.
3. Makefile: `make -B -n all test-host test-version check` gives the same commands as v1.0.0, apart from the owner's
   check-obinary line. It runs in fresh folders before any build: on the PC before the merge (W1a, W2a, W3), and in
   test.yml on macos-15 after it (W4) [R2-S8].
4. Python: W1 gives a verdict on every Darwin-visible line, and names the test that covers it.
5. test.yml on macos-15 (Python 3.10 and 3.14): the build, `make check`, the host C tests and the fast pytest, green
   on the merge and release commits.
6. Best-effort: `macos-live.yml` runs the slow suite with `LAZ_REQUIRE_EMULATOR=1` on the public v1.0.0 core.
   - If its pytest step passes (passed > 0 and 0 failed), STATUS says the macOS emulator suite passed in CI on v1.1.0.
   - If not, STATUS says: "macOS: the emulator suite last ran on a Mac at v1.0.0; the v1.1.0 changes visible on macOS
     are reviewed and pass the CI build and fast tests."
7. The owed I5 part 2 is closed as superseded. macos-live does a fresh fetch and build of the public v1.0.0 assets,
   and W10 does the Windows clone check from the real URLs.

## 8. Out of scope

- Linux (`port-linux`), Intel Macs, Windows on ARM and 32-bit Windows.
- The Mesa dzn route, prebuilt Windows host binaries, and audio.
- The PC-runner tools in the toolkit, a PowerShell fetch, and any Mac rerun.
- A native MSYS2 build of the core, and a software-Vulkan boot in CI.

## 9. Findings from planning (each fixed or gated by a named step)

- B1. The PC's private core DLL holds the WSL home path, with a local username, seven times (in OpenSSL's paths). It
  never ships. D4 and D5 fix this; W5 and W9 gate it.
- B2. build.inputs' `openssl_prefix=` was not masked. D5 removes the need.
- B3. The private DLL's build.inputs lacks the `openssl_*`, `head=` and `cmake=` lines. D4.
- B4. The private DLL holds two GCC idents, "13-posix" and "15-win32". D13 maps each ident by evidence. An ident
  with no package blocks the release.
- B5. `make win64` writes to `build/win64/`, but Python looks in `build/`. W2a.
- B6. The `WIN_CC` and `ZLIB_PREFIX` defaults are WSL values. W2a.
- B7. MSYS2 has no `zip` or `unzip`. Covered by W0 and the README pacman line.
- B8. The OpenSSL build script lives in the toolkit. D5 and W2b1.
- B9. The PE keyblob twin lives in the toolkit. W2b1.
- B10. The branch has no CI file. W2a.
- B11. The branch's `tools/build-core.sh` edits would break the v1.0.0 Mac core's keyblob check. D3.
- B12. The release tools are macOS-only. W2b1, W2b2, D2.
- B13. The PC's default `python` is 3.7. D9.
- B14 (review 2). The venv's base interpreter path holds the local username. D9 [R2-N6].

Where review 2's findings land:

| Finding | Where |
|---|---|
| R2-B1 | D14, W4 |
| R2-B2 | D5 |
| R2-B3 | D4 |
| R2-S1 | D4, D10, W5 |
| R2-S2 | D7, W9 |
| R2-S3 | D2 |
| R2-S4 | brief W2b-release, section 6 |
| R2-S5 | brief W2b-release |
| R2-S6 | D4, D13 |
| R2-S7 | W9, section 4 |
| R2-S8 | W1a, section 5, section 6, section 7 |
| R2-S9 | W7, W10 |
| R2-S10 | brief W2b-release |
| R2-S11 | W8, W9 |
| R2-S12 | D5 |
| R2-S13 | W9 |
| R2-N1 | D4 job 2 |
| R2-N2 | W7, W9 |
| R2-N3 | section 4 |
| R2-N4 | section 6, brief W6 |
| R2-N5 | W1a |
| R2-N6 | D9, the briefs |
| R2-N7 | section 6 |

## 10. Hour-saving pass (redone on revision 2)

Kept from revision 1: H1-H10 (CI build, Mac inheritance, inherited bytes, no full pytest at W4, no interim push, W6
beside W2, W8 beside W7c, gate_f2 from `gate_f2_pe.py`, a delta-only ip-legal brief, W1a on the PC).

New in this revision:

| # | Cut | Saves |
|---|---|---|
| HS1 | All build-tree checks and the window search run in CI job 1. The 43 MB PC fetch and the `--build-meta`/`--src` port of the tree checks are dropped; release_check reads `gate_f2.txt` | 0.7 h |
| HS2 | Only the three key headers are extracted | 0.1 h |
| HS3 | The A1 OpenSSL recipe is copied verbatim (`build_libs` + `install_dev`) | 0.3 h of debugging, about 5 minutes per CI run |
| HS4 | Guy's word comes at the end of W8, so W9 and W10 run in one sitting | 0.2 h, and hours of wall time |
| HS5 | macos-live on W9's push is the real fallback test; the PC test keeps only local folders | 0.1 h |
| HS6 | The fallback fires on any download failure, with no HTTP code parsing | 0.1 h |
| HS7 | W4's clone check runs on the `p7-docs` bundle, so W6 is not split | 0.2 h |
| HS8 | W5 becomes a short main-loop step (sha match, scans, smoke boot) with no agent and no brief | 0.35 h |
| HS9 | The leak check reuses gate_f2's window search, with no new scanner | 0.2 h |

Added by review 2's fixes: the container setup and the non-root user (R2-B3), the leak-check job, the asset helper
(R2-S5) and `skips_check.py` (R2-S8). Together about 0.75 h, mostly in W2b1 and W2b2.

## 11. Hours (estimates; actuals to docs/hours.tsv, phase `phase-7`)

| Step | Owner | Hours |
|---|---|---|
| W0 | main loop | 0.3 |
| W1a | main loop (PC) | 0.25 |
| W1 | opus | 1.25 |
| W1b | ip-legal | 0.25 |
| W2a | sonnet | 2.0 |
| W2b1 | sonnet | 2.75 |
| W2b2 | sonnet | 2.5 |
| W6 | sonnet | 1.0 |
| W3, plus the merges and mkmap | opus + main loop | 0.75 + 0.2 |
| W4 | main loop | 1.0 |
| W5 | main loop | 0.4 |
| W7 | main loop | 1.0 |
| W7c | main loop | 0.3 |
| W8 | release-legal-audit, plus fixes | 1.25 |
| W9 + W10 | main loop | 0.7 |

Total: about 15.9 h of execution work, range 13 to 20 h. Revision 1 estimated 17.1 h, including 1.0 h of planning;
planning actuals are booked separately.

End to end it takes about 9 h of wall time. W2a, W2b1, W2b2 and W6 run in parallel, and so do W7c and W8. On top of
that come the waits: the CI build takes about 40 minutes, and there are also the PC, the users and Guy's word.

## 12. Risks

- The pinned ubuntu:26.04 image's mingw-w64 packages differ from A1's. build.inputs records the image digest and the
  package versions. The load test and the PC tests use the bytes that ship. If job 1 fails twice for a reason outside
  our code, use D4-fallback.
- The CI artifact is the shipped binary. Its sha is checked against `gate_f2.txt` and the log (W5), at staging (W7),
  and by GitHub's digest (W9). The attestation is the permanent record.
- The leak check depends on job 1's log being complete. If the log is truncated (GitHub caps logs), job 3 fails
  closed.
- The neutral OPENSSLDIR changes the guest's HTTPS lookup. The full pytest's HTTPS tests cover it, and the limit is
  documented.
- The PC is shared. W7 and W10 check free RAM and announce on the board, and lane-pc waits when the PC is busy.
- Timing bounds can fail under load. W4 runs the state-restore test quietly three times.
- If macos-live cannot run MoltenVK, a macOS-only regression would show only in users' runs. W1's three Darwin lists
  are the guard.
- W7c has no deadline (D11).

## 13. Open questions for Guy

- Q1. Publishing v1.1.0: the main loop asks for your word at the end of W8, with the audit verdict and the PC
  results. Then it pushes, tags and publishes in one sitting.
- Q2. Windows users build the host from source (the default). Should the release also ship prebuilt `libazhost.dll`
  and `azhost.exe`?
- Q3. Is "proven on one PC (Windows 10, RTX 3060, NVIDIA)" the right wording? If the macOS emulator suite cannot run
  in CI, is section 7's macOS sentence right?
