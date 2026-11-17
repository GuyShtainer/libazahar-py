Zero blockers not fixed: yes

# Phase 7 fix check (W3, item laz-708)

Reviewed: `p7-int` at 9bb34ef. It is port-win-v1 (1c8650f) with merges of p7-w2a (55a4ff4), p7-w2b1 (edfb145) and
p7-w2b2 (e3d839f). The W6 docs branch `p7-docs` (0d7475e, also based on 1c8650f) was reviewed separately, since it
merges at W4. This was a read-only review: no build, test or CI run on the Mac or the PC. The only run evidence is the
main loop's W1a re-run in `runs/p7/w3/`.

Result: no blocker is left open, and this review found none. It found 1 major, 7 minor and 13 nits (P7-R3-1 to
P7-R3-21). The major is a placeholder scan that misses two files, so the release could ship with placeholder text in
it. Fix it before W9's `--pre-push` run.

## 1. State of every earlier finding

Line numbers refer to `p7-int` unless the text says `p7-docs`.

### P7-R1 (the phase 7 diff review)

| Finding | Sev | State | Where (commit or file:line) |
| --- | --- | --- | --- |
| P7-R1-1 | blocker | fixed | `git diff v1.0.0 -- tools/build-core.sh` is empty. The win64 route lives in the new `tools/build-core-win64.sh` and `tools/toolchain-win64.cmake` (edfb145) |
| P7-R1-2 | should | fixed | `Makefile:91`, `:100`, `:105`: `build/libazhost.dll` and `build/azhost.exe`, with objects in `build/win64/` (55a4ff4) |
| P7-R1-3 | should | fixed | `Makefile:80-81`: `WIN_CC ?= gcc`, `ZLIB_PREFIX ?= /mingw64`. The MSYS2 comment is at `:67`, and the MINGW64 guard at `:75-77` |
| P7-R1-4 | should | fixed | `host/plat/win_compat.c:34-36`: `GetFullPathNameA` runs before the load. The new test is `tests/python/test_windows_cli.py` |
| P7-R1-5 | should | fixed | `.github/workflows/test-windows.yml` (55a4ff4) and `.github/workflows/core-win64.yml` (edfb145) |
| P7-R1-6 | should | fixed | `tests/gate_f2.py` takes a target, plus the new `tests/gate_f2_pe.py` (edfb145). fetch, mknotices, mkrelease, release_check and clone_check are ported (e3d839f) |
| P7-R1-7 | should | fixed | `LAZ_WIN_PY` in `tools/clone_check.sh:9`, `:58`, with a 3.10 guard in the Python tools (e3d839f) |
| P7-R1-8 | should | moved to W4 | The first real macOS compile is the `test.yml` run on p7-int. Pushing it is Guy's call |
| P7-R1-9 | should | fixed on p7-docs, merges at W4 | README, STATUS, USING (Windows defaults, table 15a), release notes, and the 1.1.0 bump (0d7475e and earlier p7-docs commits) |
| P7-R1-10 | nit | fixed | `host/plat/win_compat.h:2` scope rewritten. The TerminateProcess note now sits on `azh_win_exit`, at `:27` |
| P7-R1-11 | nit | fixed | `host/plat/win_compat.c:60-62`: `err_text` is set on a missing symbol |
| P7-R1-12 | nit | fixed | `host/plat/win_sdcopy.c:153`: `FILE_ATTRIBUTE_NORMAL` alone |
| P7-R1-13 | nit | fixed | `host/match.c:127`, `:160`: one open, then `fstat`. `azh__file_size_fresh` stays for `run.c:255` |
| P7-R1-14 | nit | fixed | `tools/hold_slot.py:54`, `:72`: the assign's return is checked and the child is killed on failure (`use_last_error=True`) |
| P7-R1-15 | nit | fixed | `tools/speed_table.py:85`: skipped on darwin. `:90` has `timeout=10` |
| P7-R1-16 | nit | fixed | `tests/python/test_threads_live.py:64`: `pe_exports` parses the export table |
| P7-R1-17 | nit | fixed | `tests/python/test_client.py`: the trailing blank line is gone |
| P7-R1-18 | nit | fixed | `tools/check-obinary.sh:7`, `:10`: comments are stripped, and `MIN_SITES=11` makes a count below 11 fail |
| P7-R1-19 | nit | fixed | `host/vk.c:30`: the assert now comes before `strnlen` |

### Plan review 1 (R1)

| Finding | State | Where |
| --- | --- | --- |
| R1-B1 WSL route | fixed (CI route, D4) | `core-win64.yml`: a container build, the gate, a load test on windows-2025, the leak check, and attest |
| R1-B2 no key arrays | fixed | `tests/gate_f2.py:77-84` reads `KEY_ARRAYS` from the headers. The headers exist only in CI (D10, `core-win64.yml:70`) |
| R1-B3 release_check Mac-bound | fixed (inherit, D2) | `tools/mkrelease.sh:22` pins the digest. `release_check.py:764-774` holds the inherited and v1.1 names |
| R1-B4 Mac SOURCE.md | fixed | The top-level SOURCE.md maps every binary, the testapp included (mkrelease) |
| R1-B5 W1a push | moved (plan, done) | W1a ran on the PC with stub headers. There was no push |
| R1-S1 fetch break at W7 | fixed (D7) | `tools/fetch.sh:51`, `:113-114`. Tested by `tests/fetch_fallback.sh` |
| R1-S2 tag after green CI | moved to W9 | Main loop |
| R1-S3 W2b size | moved (plan) | Split into W2b1 and W2b2 |
| R1-S4 gate_f2 on win64 | fixed | `tests/gate_f2_pe.py`, and the gate step in `core-win64.yml` |
| R1-S5 macOS proof covers C only | fixed | W1a, plus `test.yml`'s `make -B -n` diff against v1.0.0 (one allowed line) |
| R1-S6 make check on MSYS2 | fixed | The Windows `check` target runs check-obinary, then clang. `test-windows.yml` installs clang |
| R1-S7 skip list | fixed | `tools/skips_check.py`, `tests/data/allowed-skips/fast.txt`, `tests/data/allowed-skips/w7.txt` |
| R1-S8 OpenSSL paths | fixed | `/opt/lazpy` prefix, A1 recipe (D5), in `build-core-win64.sh` |
| R1-S9 Windows paths in privacy scan | part fixed | UTF-16 strings are scanned. Windows and CI path patterns are not: see P7-R3-5. The W5 needle scan covers most of it |
| R1-S10 runtime source | fixed (D13) | The runtime-source step in `core-win64.yml`, and `RT_ASSET` at `release_check.py:741`. Version pin: see P7-R3-6 |
| R1-S11 load before tag | fixed | The `load-test` job in `core-win64.yml:162-204` |
| R1-S12 fresh MSYS2 gaps | part fixed | sha256sum fallback (`fetch.sh:83`) and the MINGW64 guard are in. The README pacman line lacks curl: see P7-R3-8 |
| R1-S13 W7c shared deploy | moved (plan) | Main loop |
| R1-S14 vacuous gates | fixed | `clone_check.sh --until host` is a real run, and `MIN_SITES` was added. The skip checks fail on any unlisted skip |
| R1-N1 zip members | fixed | `ZIP_NAMES_WIN` at `release_check.py:740`. fetch unzips per OS |
| R1-N2 non-blocking wording | moved to W9 | `continue-on-error` is used in the CI files. Branch protection is the main loop's |
| R1-N3 OpenSSL build script | fixed | The Windows section of `core/OPENSSL.md` |
| R1-N4 needles on stdin | fixed | The needles reach W5 on stdin only |
| R1-N5 WSL hours | moved (plan) | Not a code item |
| R1-N6 no bare python3 | fixed | clone_check uses `LAZ_WIN_PY` |
| R1-N7 ASCII path | fixed on p7-docs | README (p7-docs):75: "a short path with ASCII letters only, such as" `C:\src` |

### Plan review 2 (R2)

| Finding | State | Where |
| --- | --- | --- |
| R2-B1 README block not in W4 tree | moved to W4 | HS7: the W4 clone check runs on the p7-int bundle after p7-docs merges. The `steps-win` marker is on p7-docs and clone_check's awk reads it |
| R2-B2 OpenSSL Configure line | fixed | `build-core-win64.sh` uses the A1 recipe (`build_libs` and `install_dev`) |
| R2-B3 container fails on our code | fixed | The non-root build user (`core-win64.yml:54`, `:61`) and the package list (`:35`, `:43`) |
| R2-S1 build-tree checks in CI | fixed | The gate and the leak check run in CI. The key headers never reach the PC |
| R2-S2 fetch fallback spec | fixed | `fetch.sh`, D7 points 1-10. Covered by `tests/fetch_fallback.sh` (7 checks) |
| R2-S3 inherit anchored | fixed | `mkrelease.sh:22` pins `V1_0_0_SHA256SUMS`, and each of the seven assets is checked against its line |
| R2-S4 check 16 split | fixed | The macOS half keeps `wording_findings` live (`release_check.py:1098`). The Windows half is at `:1100` and `:968` |
| R2-S5 single-zip sites | fixed | `asset()` takes the platform (`release_check.py:69-78`). The plants include "a third zip" |
| R2-S6 container provenance | fixed | The image digest is pinned and its line appears once (`core-win64.yml:23`). The runtime source is recorded |
| R2-S7 W9 diff gate | moved to W9 | `tools/build-files.txt` exists for it |
| R2-S8 vacuous gates | fixed (the CI pieces) | junit plus skips_check in `test.yml` and `test-windows.yml`, and `MIN_SITES` |
| R2-S9 W10 skip list | fixed | `--list w7` and `MUST_RUN` in `skips_check.py`. clone_check passes `--junitxml` |
| R2-S10 clone_check Windows | fixed | The clean env, PYBIN from `pyvenv.cfg`, no re-run on Windows, and load.sh |
| R2-S11 "Windows proven" push | moved to W8/W9 | Main loop |
| R2-S12 OpenSSL source sha | fixed | The first `- Source:` line of `core/OPENSSL.md`. mkrelease and release_check check it |
| R2-S13 PC pre-push clone | moved to W9 | Main loop |
| R2-N1 load test winmode | fixed | `core-win64.yml:204`: `ctypes.CDLL` with the default winmode |
| R2-N2 SHA256SUMS digest | moved to W9 | Main loop |
| R2-N3 SOURCE.md maps the testapp | fixed | mkrelease's top-level SOURCE.md |
| R2-N4 Vulkan driver line | fixed on p7-docs | README (p7-docs):18 |
| R2-N5 O_BINARY undefined in stubs | moved (W1a, done) | `planted` check 1x / 0x in the W1a re-run notes |
| R2-N6 LAZ_WIN_PY holds the username | fixed | Read from the env only. clone_check's `cenv.sh` is written under the git-ignored `runs/` |
| R2-N7 one automated skip list | fixed | `tests/data/allowed-skips/fast.txt` is shared by the CI files |

## 2. The W1a re-run: darwin-pp-fixes and make -n

- `darwin-pp-fixes.diff` (port-win-v1 to p7-int, macOS predefines) has 3 hunks in 2 files:
  - `host/match.c`, two hunks. On Darwin the size comes from `st_size`, and the open now happens after the size
    check. The extra close is dead code. This behaves the same as v1.0.0.
  - `host/vk.c`, one hunk. The assert moves before `strnlen`.
  - All three are correct and harmless on macOS.
- `make-n.diff` (v1.0.0 to p7-int, `HOST_OS=Darwin`) adds one line, `tools/check-obinary.sh`.
- `make-n-fixes.diff` (port-win-v1 to p7-int) is empty.
- So the macOS build commands are unchanged except for the `check-obinary.sh` line. `test.yml`'s `make -B -n` diff
  enforces the same rule in CI.

## 3. New findings

| Id | Sev | File:line | Fault | Fix |
| --- | --- | --- | --- | --- |
| P7-R3-1 | major | `tools/release_check.py:753`, `:968-980`; `docs/USING.md:366-367` (p7-docs); `core/OPENSSL.md:76-77` | `PLACEHOLDERS` are only looked for in STATUS.md, the release notes and README.md, where a hit is PEND (FAIL under `--pre-push`). USING.md holds `<from W7>` and `<OPENSSLDIR from build.inputs>`, and OPENSSL.md holds "TO BE FILLED from the first CI run" twice. No check reads either file for them, and docs_check.py has no placeholder scan. The release could ship with all four still in the text. | Pass USING.md and core/OPENSSL.md to the placeholder loop. Add "TO BE FILLED" to `PLACEHOLDERS`. Add a plant-red case that puts a placeholder in USING.md. |
| P7-R3-2 | minor | `.github/workflows/core-win64.yml:270-282` | The leak check runs `_window_findings` on the raw bytes of the job log and the artifacts. If a step prints header bytes as text (`0x12, 0x34, ...` or a hex dump), the log holds ASCII, and no 16-byte window matches. Plan HS9 chose to reuse the existing search, so this is a known limit. It still leaves the leak check blind to the likeliest way a log leaks. | Before the window search, also decode each run of `0x..` tokens and each long hex string in the log to bytes, and search those bytes. Add one planted log line. |
| P7-R3-3 | minor | `core/OPENSSL.md:78` | The note says the `--openssldir` path is one "the core never reads: no OpenSSL config, engine or module is loaded". USING table 15a (p7-docs) says the guest's HTTPS finds its CA file only at the compiled-in OPENSSLDIR. OpenSSL 3 also tries to load `openssl.cnf` from there by default. The two docs contradict each other. | Reword: the path is the compiled-in default. The core reads the CA file there if one exists, and nothing ships there. |
| P7-R3-4 | minor | `tools/release_check.py:1303-1306`, `:1393` vs `:1398-1412` | `Ctx.__init__` calls `asset()` and hashes `testapp.3dsx` before `main` enters its `try`. A missing or doubled zip, or a missing testapp, gives a Python traceback, not the "FAIL 1 assets" line. | Build `Ctx` inside the `try`, or catch `AssetError` and `OSError` around it and print the FAIL line. |
| P7-R3-5 | minor | `tools/release_check.py:251` | `PRIVATE_RES` matches only the macOS home prefix. A Windows profile path (drive letter, then the Users folder), a Linux home folder, an MSYS2 or WSL drive mount of the Users folder, or a CI workspace path (the `__w` and `github/home` folders) in a binary or doc passes. This is R1-S9's second half. | Add these patterns, case-insensitive for the drive form, with one plant each. |
| P7-R3-6 | minor | `.github/workflows/core-win64.yml:97` | `apt-get download "gcc-$N-source"` takes whatever version the archive offers. It is not matched to the `Built-Using` version of the mingw-w64 gcc that built the core. The runtime source on the page could then be for a different gcc release than the one in the binary. | Read `Built-Using` from `gcc-mingw-w64-x86-64-posix` and download `gcc-$N-source=<that version>`, or fail. Record the version in `build.inputs`. |
| P7-R3-7 | minor | `.github/workflows/core-win64.yml:124-125` | mknotices reads `/usr/share/doc/<pkg>/copyright`. The minimized Ubuntu image's dpkg excludes can drop `/usr/share/doc`, and some packages' doc folders are symlinks to another package. The step fails closed, so the result is a red run, not a bad release. | If the file is missing, fetch the package with `apt-get download` and take the copyright file from `dpkg-deb -x`. |
| P7-R3-8 | minor | `README.md:81` (p7-docs); `tools/clone_check.sh` PATH | The pacman line installs `git make zip unzip mingw-w64-x86_64-gcc mingw-w64-x86_64-zlib` but not curl, which fetch.sh needs (R1-S12). A user's shell inherits System32's `curl.exe`. clone_check's clean PATH (`PYBIN:/mingw64/bin:/usr/bin:/bin`) does not, so a fresh MSYS2 without curl fails there. The PC passed only because its MSYS2 already has curl. | Add `curl` to the pacman line. |
| P7-R3-9 | nit | `.github/workflows/core-win64.yml:35`, `:43` | `apt-get install` runs without `DEBIAN_FRONTEND=noninteractive`. A package such as tzdata can stop at a prompt. | Set it in the job env. |
| P7-R3-10 | nit | `.github/workflows/core-win64.yml:45`, `:164`, `:229` | `actions/checkout` keeps its default `persist-credentials: true`. The token stays in `.git/config` while the build runs untrusted upstream cmake. | Add `persist-credentials: false`. |
| P7-R3-11 | nit | `.github/workflows/core-win64.yml:241-243` | The job log is fetched once with no retry. GitHub can return 404 for a few seconds after a job ends. This fails closed and gives a spurious red run. | Retry a few times with a short wait. |
| P7-R3-12 | nit | `tools/release_check.py:852` | `gate_f2_findings` checks the line order and `hits=0`, but not that `arrays=` and `windows=` are positive. A gate that searched nothing would pass, although gate_f2 itself already fails closed on that. | Require `arrays>=1` and `windows>=1`. |
| P7-R3-13 | nit | `Makefile:63` | The Darwin `.PHONY` still names `win64`, `test-version-win`, `test-host-win` and `check-obinary`. They are harmless, but the names are stale. | Drop the names the Darwin half no longer defines. Otherwise W1a's `make -n` diff stays as it is. |
| P7-R3-14 | nit | `Makefile:4` | `HOST_OS ?= $(shell uname -s)` also takes `HOST_OS` from the environment, so a stray export switches the half that is built. | Keep `?=` for the `make HOST_OS=Darwin -n` check, and say in the comment that the environment can set it, or read it only from the command line. |
| P7-R3-15 | nit | `tools/release_check.py:951` | `windows_notices_findings` takes `mac_text` and never uses it. | Drop the parameter, or use it for the "shared font notices" comparison it seems meant for. |
| P7-R3-16 | nit | `examples/README.md` (p7-docs, 0d7475e) | W6 edited a file outside its listed files. The edit itself is correct (Windows venv paths). | Record it in W6's evidence, or list the file in the brief. |
| P7-R3-17 | nit | `tools/fetch.sh:77`, `:206` | `MISSING_HINT` is set globally for the Windows zip and never cleared. A later testapp download failure prints "not published yet". | Clear it after the core download, or make it local to that call. |
| P7-R3-18 | nit | `tools/fetch.sh:114` | "fell back to v1.0.0 for <asset>" is printed before the fallback download runs. If the fallback also fails, the log says it fell back. | Print it after the fallback download and its sha check pass. |
| P7-R3-19 | nit | `tools/mkrelease.sh:133`; no `.gitattributes` | `$(cat tools/build-files.txt)` breaks if a Windows checkout gives the file CRLF line ends, because each path then ends in `\r`. | Add `.gitattributes` with `tools/build-files.txt text eol=lf` (or `* text=auto eol=lf` for shell scripts), or strip `\r` when reading. |
| P7-R3-20 | nit | `tools/check-obinary.sh:10` | `sed 's|//.*$||'` also cuts any line at a `//` inside a string (a URL). A site on such a line would be lost. This fails closed through `MIN_SITES`. | Accept it, or only strip `//` when it follows whitespace or `;`. |
| P7-R3-21 | nit | `tests/fetch_fallback.sh:47` | `env -u` is not POSIX. It works on macOS and GNU env, which are the only ones in use. | Accept it, or use `unset` in a subshell. |

## 4. Other points checked and found sound

- core-win64.yml:
  - Container and build: the image digest is pinned once and the line count is checked. The build runs as the
    non-root user `b`.
  - Key headers: they are extracted to `$RUNNER_TEMP/keyhdr` with a trap that deletes them, and they are never in
    an artifact.
  - Permissions: `id-token: write` and `attestations: write` are on the attest job only (`:295-296`). The leak check
    has `actions: read` (`:227`).
  - Delete-on-leak runs on `always() && needs.leak-check.result == 'failure'`, with `actions: write` (`:319-332`).
- test-windows.yml: actions pinned by sha, the MSYS2 MINGW64 shell with `path-type: inherit`, junit plus skips_check.
- macos-live.yml: `continue-on-error` at job level, `LAZ_REQUIRE_EMULATOR=1`. W9 reads the result.
- test.yml:
  - It still runs everything v1.0.0 ran, on the same Python matrix.
  - It adds the `make -B -n` diff (one allowed line), `vtool` minos 15.0 and `lipo` arm64, then junit plus
    skips_check fast.
- fetch.sh:
  - D7 holds: one fallback on any download failure, never on a sha mismatch, and the fallback line goes to stderr.
  - `REL_TAG_PREV=v1.0.0`. `LAZ_RELEASE_BASE` clears the fallback base unless `LAZ_RELEASE_BASE_PREV` is set.
  - The Windows zip has no fallback. `LAZPY_CORE_SHA_WIN=TBD` makes `pin_set` die.
- release_check.py:
  - `asset()` raises on zero or two matches.
  - The gate_f2 reader matches contract 1's lines and order, and checks `core_sha256` against the zip's DLL.
  - The Windows build-files check compares bytes with a fresh `git archive`.
- build-files.txt matches contract 2 exactly. skips_check.py matches contract 3: `--list fast|w7`, `MUST_RUN` for
  w7, exit codes 0, 1 and 2, and ALLOWED / NOT ALLOWED lines.
- clone_check.sh:
  - `q()` quotes every value into `cenv.sh` under `env -i`.
  - The Windows mode takes PYBIN from `pyvenv.cfg` through `cygpath`, extracts the `steps-win` block with awk, and
    `--until host` cuts the right steps.
- mkrelease.sh `--inherit`: the digest pin, the seven assets against their lines, the five repo pins and the Windows
  zip members.
- Cross-branch seams:
  - p7-docs holds the `steps-win` marker that clone_check needs. It also holds every `WIN_PIECES` string and no
    `WIN_REJECT` word.
  - USING's placeholders are the one gap (P7-R3-1).
  - mkrelease's grep reads the first `- Source:` line of `core/OPENSSL.md`, which is still the OpenSSL source sha.

## 5. Not checked (needs a run)

- actionlint on the four workflow files.
- `make check` with clang, on Windows or on macOS.
- A real macOS compile of p7-int (P7-R1-8, at W4).
- Any real CI run of core-win64, test-windows or macos-live: the container build, the gate, the load test, the leak
  check and attest.
- Whether the Azahar build needs the host gcc in the container.
- In the ubuntu:26.04 image:
  - whether the `/usr/share/doc/*/copyright` files exist, or are symlinks (P7-R3-7);
  - the gcc-source version against Built-Using (P7-R3-6).
- mknotices' runtime licence markers against the real licence files.
- clone_check's Windows clean env in full mode (W7, W10).
- `vtool` minos 15.0 on the runner.
