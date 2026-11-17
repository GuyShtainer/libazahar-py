# Phase 7 agent briefs (Windows proven, v1.1.0)

Written 2026-11-17 12:14 IST by the opus planner, for the main loop (eb). The plan is `docs/plans/phase-7.md`,
revision 2. Each brief below is ready to paste. Before pasting, the main loop fills in `<worktree>` and the times.

Main-loop steps (W0, W1a, W4, W5, W7, W7c, W9, W10) have no brief. They are numbered checklists in the plan. W5 is
now a main-loop step, because the needle scan stays with the main loop (plan section 10, HS8).

## Rules for every agent (paste at the top of each brief)

- Work only in your own worktree, `<worktree>`. Never write in the main checkout, Gen3D, 3DPlatinum or the toolkit.
- No commits, pushes, tags or branch changes. Run only `git status`, `git diff` and `git log`. The main loop commits.
- Write only your listed files, plus your notes file. If a change needs another file, write that need in your notes
  and leave the file alone.
- Save as you go. After each finding or each gate run, append it to `runs/p7/<step>/notes.md`: what is done, what
  failed, the numbers, and the last lines of each command. A stop then loses nothing.
- The Mac is closed to 3DS work. On the Mac you may edit, read, `grep` and `git diff`. Every build, test and gate
  runs on the PC through the PC runner (`docs/map/runners.md`), or in CI. lane-pc exit 77 means "not run": wait,
  then requeue on the PC. Never run anything again on the Mac as a fallback.
- PC paths: your scratch tree is `D:\lazpy\p7\<step>\`. The Windows Python is `C:\lazpy\venv\Scripts\python.exe`.
  Never write the venv's base interpreter path, a local username, an email address or a `/Users/...` path into any
  file, log copy or message. Use `C:\...` and `D:\...` paths as written here.
- Never commit, copy or print the core DLL's bytes, ROMs, keys or the Azahar key headers. On the PC, at most 2
  emulator copies at once, never a window, and only on the free-RAM rule in runners.md.
- Style: read a file before you edit it, and keep its style. Public docs are plain English, with no game names and
  no speed claims.
- Your final message: the files changed, each gate with its last lines and exit code, and anything left open.

## Shared contract 1: `gate_f2.txt` (writer W2b-build, reader W2b-release)

Job 1 of `core-win64.yml` writes it next to the DLL. It is UTF-8 text with LF line ends, and the lines come in this
order:

```
gate_f2 1 target=win64
head=<40 hex, git rev-parse HEAD>
image=ubuntu:26.04@sha256:<64 hex>
core=azahar_lazpy_libretro.dll
core_sha256=<64 hex>
PASS droplist cmake
PASS deps files=<n>
PASS fresh
PASS window arrays=<n> windows=<n> hits=0
PASS pe machine=x86-64
PASS imports n=<n>
END
```

- `deps`: the number of `.o.d` files read must be at least 1000, and none may name a drop-list path.
- `fresh`: the core must be newer than CMakeCache.txt.
- `window`: the 16-byte window search over the DLL, using the three headers.
- Any failed check writes `FAIL <name> <reason>` in place of its PASS line, and the job then fails.
- The reader (`release_check.py --gate-f2 FILE`) passes only if:
  - every line is present, exactly once and in order;
  - there are no FAIL lines;
  - `END` is the last line;
  - `core_sha256` equals the sha of the staged DLL;
  - `head` equals build.inputs' `head=`;
  - `image` equals build.inputs' `image=`.

## Shared contract 2: `tools/build-files.txt` (writer W2b-build, readers W2b-release and W9)

There is one repo path per line, sorted, with no comments. It holds the members of
`libazahar-py-core-build-v1.1.0.tar.gz`: `core`, `tools/build-core-win64.sh`, `tools/toolchain-win64.cmake`,
`tools/untar_checked.py`, `.github/workflows/core-win64.yml`, and `tools/build-files.txt` itself.
- mkrelease runs `git archive` over exactly these paths.
- release_check's build-files check compares the tar's member list with this file.
- W9 runs `git diff <head=> HEAD -- $(cat tools/build-files.txt)`.

## Shared contract 3: `tools/skips_check.py` (writer W2a, readers W2b-release's clone_check and the main loop)

`skips_check.py <junit.xml> --list fast|w7` exits 0 only when every skipped test is on the named list with its
message condition (plan section 6). Two more rules:
- On `--list w7`, `test_release_fixture.py` and `test_profile_format.py` must have run and passed.
- On any list, there must be no failures or errors.

It prints one line per skip: `ALLOWED <nodeid>` or `NOT ALLOWED <nodeid>: <message>`.

---

## Brief W1: full diff review of port-win-v1 (opus)

Model: opus. Step W1, item laz-702. Paste the common rules first. This is a review only: write nothing but the review
file and your notes.

Inputs:
- `git diff v1.0.0 port-win-v1` (65 files, about 1,700 lines added).
- `runs/p7/w1a/darwin-pp.diff` and `runs/p7/w1a/make-n.diff`, the main loop's preprocessed C and `make -B -n` diffs
  as seen on macOS.
- The plan, sections 2, 6 and 7.
- `docs/map/rules.md`, and the owner conditions in `docs/plans/phase-v1.md`.

Do:
1. Review every hunk for correctness on Windows and for any change visible on macOS.
2. Write three Darwin-visible sections, each complete:
   - C: every hunk in `darwin-pp.diff`, with a verdict.
   - Makefile: every line in `make-n.diff`. Only the check-obinary line may differ.
   - Python: every changed line that runs when `sys.platform == "darwin"`, with a verdict and the test that covers
     it.
3. Quote owner conditions 1, 3, 5 and 7, and say whether each holds.
4. Check the plan's findings B5, B6 and B10-B13 against the branch, and say which ones W2 must fix.

Files owned: `docs/reviews/phase-7-diff-review.md` (new), `runs/p7/w1/notes.md`.

Gate:
- Every finding is `P7-R1-<n>`, with a severity (blocker, should or nit), a `file:line` and a fix.
- The three Darwin sections cover every hunk and line in the two diff files. Count them, and print the counts.
- The verdict is one of "fix then merge" or "do not merge".

## Brief W1b: licence delta for v1.1.0 (ip-legal)

Model: ip-legal agent. Step W1b, item laz-703. Paste the common rules first. Write only the answer file and your
notes.

Inputs:
- The plan's section 4 (the asset table), and D4, D5 and D13.
- `docs/reviews/release-ip-legal.md` (the v1.0.0 consultation), and v1.0.0's audit, kept privately at
  `runs/reviews/release-legal-audit-v1.0.0.md` in the main checkout. Read it there; never quote its redacted parts.
- The skill's `references/ip-law-and-publishing.md`.

This is a delta from v1.0.0, which was audited shippable. Answer only these questions:
1. The DLL links libstdc++, libgcc and winpthreads statically, plus the mingw-w64 CRT, all from Ubuntu's packages.
   Is shipping D13's source tar needed, or just wise? Does GPLv3 with the Runtime Exception need anything more than
   the NOTICES text?
2. OpenSSL 3.6.5 (Apache-2.0) is linked statically into a GPLv3 DLL, as in v1.0.0's Mac core. Does anything differ
   on Windows?
3. The host loads `vulkan-1.dll` from System32 and ships nothing Vulkan. Is any notice needed?
4. Users build the host themselves with MSYS2. Does the release owe anything for MSYS2's zlib, linked statically
   into a binary we do not ship?
5. Seven assets are re-uploaded byte-identical from v1.0.0. Is that fine as is?
6. Does using the names "Windows", "NVIDIA" and "RTX 3060" in README and STATUS (as tested-on facts) need any wording
   rule?
7. Is GitHub's build attestation (a public record of the build) a privacy or legal issue? The attestation holds the
   workflow and the repo, not the user.

Files owned: `docs/reviews/phase-7-ip-legal.md` (new), `runs/p7/w1b/notes.md`.

Gate: each question gets a yes or no, with a named action or "none". Record any lasting finding in your notes for the
main loop to add to the knowledge base.

## Brief W2a: host, Python, tests, Makefile and CI files (sonnet)

Model: sonnet. Step W2a, item laz-704. Paste the common rules first. Worktree `<worktree>`, at the port-win-v1 tip.

Inputs:
- W1's review, the findings marked for W2a.
- Plan findings B5, B6 and B10.
- Plan sections 5 and 6, and [R2-N1], [R2-N7] and [R2-S8].

Files owned:
- `host/*`, `Makefile`, `tests/host/*`, `tests/test_version.c`, `tools/check-obinary.sh`.
- `python/libazahar/*`, except the `__version__` line (W6 owns it).
- `tests/python/*`, and `pytest.ini` or the `[tool.pytest]` table if one exists.
- `tools/skips_check.py` (new), and `tests/data/allowed-skips/fast.txt` and `w7.txt` (new).
- `.github/workflows/test.yml`, `.github/workflows/test-windows.yml` (new) and `.github/workflows/macos-live.yml`
  (new).

Do:
1. Fix every P7-R1 finding W1 gives to W2a.
2. B5: make `make win64`'s output path and Python's lookup agree.
3. B6: the `WIN_CC` and `ZLIB_PREFIX` defaults are the MSYS2 MINGW64 values. The Makefile refuses the other MSYS2
   shells.
4. Add a `needs_core` marker in conftest. Every core-, host- or emulator-fixture skip carries it.
5. Write `tools/skips_check.py` and its two lists, following shared contract 3 and plan section 6, with a
   `--self-test` that uses planted junit files.
6. Write the CI files as plan section 5 says:
   - Pin every action by sha, and get the msys2/setup-msys2 sha with `gh api`.
   - In test.yml: the `make -B -n` diff on a v1.0.0 worktree with `fetch-depth: 0`, run before `make`, at the same
     path depth, with the paths normalised. Also the `vtool -show-build` step.
   - In macos-live.yml: `continue-on-error` at the job level, and `LAZ_REQUIRE_EMULATOR=1` plus `-rs` on the pytest
     step.

Gates (run on the PC, in a clean MINGW64 shell, in `D:\lazpy\p7\w2a`):
- `make check && make && make test-host && make test-version` gives exit 0.
- `C:\lazpy\venv\Scripts\python.exe -m pytest -q -m "not slow" -rs --junitxml=fast.xml tests/python`, then
  `skips_check.py fast.xml --list fast` gives exit 0.
- `skips_check.py --self-test` gives exit 0.
- `make -B -n HOST_OS=Darwin all test-host test-version check` in a fresh copy matches v1.0.0's at the same depth,
  except the check-obinary line. Save the diff in your notes folder.
- `actionlint` gives no errors on your three workflow files (`D:\lazpy\tools\actionlint.exe`).

## Brief W2b-build: the Windows core build route (sonnet)

Model: sonnet. Step W2b1, item laz-705. Paste the common rules first. Worktree `<worktree>`, at the port-win-v1 tip.

Inputs:
- Plan D3, D4, D5, D10 and D13, and [R2-B2], [R2-B3], [R2-S1], [R2-S6] and [R2-S12].
- Shared contracts 1 and 2.
- The toolkit's `tools/pc/build-ossl-win.sh`, which is the A1 OpenSSL recipe, and its PE keyblob twin
  `gate_f2_pe.py`. Read both; copy, do not import.
- v1.0.0's `tools/build-core.sh`.

Files owned:
- `tools/build-core-win64.sh` (new) and `tools/toolchain-win64.cmake`.
- `tools/build-core.sh`: restore it to v1.0.0's bytes; nothing else.
- `.github/workflows/core-win64.yml` (new).
- `tests/gate_f2.py`, `tests/gate_f2_pe.py` (new) and `tools/mknotices.py`.
- `tools/build-files.txt` (new), and the Windows section of `core/OPENSSL.md`.

Do:
1. `build-core-win64.sh`:
   - Move the branch's win64 case here.
   - Copy the A1 OpenSSL Configure line verbatim. Change only `--prefix=/opt/lazpy/openssl-3.6.5-mingw64` and
     `--openssldir="C:/Program Files/Common Files/SSL"`. Run `make build_libs` and `make install_dev`.
   - Check the tarball sha with the three-line `sha_of` fallback copied from fetch.sh: `shasum -a 256` if present,
     else `sha256sum`.
   - Refuse to run as root, as v1.0.0 does.
   - Write build.inputs with `head=`, `image=`, `cmake=`, the full Configure line, `openssl_src_sha256=`, the
     OPENSSLDIR, ENGINESDIR and MODULESDIR strings found in the DLL, the mingw package versions, and the GCC-ident
     map.
2. `core-win64.yml` (`workflow_dispatch` only):
   - Job 1 runs in container `ubuntu:26.04@sha256:<digest>`; look the digest up and pin it. Its first step, before
     checkout, is the plan's D4 `apt-get install` line. Then add the deb822 `deb-src` types and create user `b`.
     Run `git config --system --add safe.directory "$GITHUB_WORKSPACE"`, create `/opt/lazpy` owned by `b`, and
     build with `su b -c`.
   - Job 1 fails at once if `git rev-parse HEAD` fails.
   - After the build, job 1 extracts only the three key headers from the `core/PIN` tarball into
     `$RUNNER_TEMP/keyhdr`, outside the workspace, and runs all of gate_f2 win64 on the live tree. It writes
     `gate_f2.txt`, then deletes the headers.
   - Job 1 runs mknotices win64 and packs `mingw-w64-runtime-source.tar` (D13). Map each GCC ident with `strings`
     over the linkLibs.rsp archives plus `dpkg -S`.
   - Job 1 prints the DLL sha, attests it, and uploads the artifact.
   - Job 2 (windows-2025) runs the load test in a fresh empty folder, as plan D4 says [R2-N1].
   - Job 3 runs the leak check from plan D4. It reuses gate_f2's window search, fails closed on a missing or
     truncated log, and prints only counts.
3. Write `tools/build-files.txt` and the `core/OPENSSL.md` Windows section.

Never put the key headers, their bytes or their hashes into a file in the workspace, a log line or the artifact.

Gates (on the PC, `D:\lazpy\p7\w2b1`):
- `git diff v1.0.0 -- tools/build-core.sh` is empty.
- gate_f2's planted reds pass with the toolkit's known Windows DLL, `C:\lazpy\probe\azahar_libretro.dll`:
  - the window-search case uses a fake header made of random bytes, planted into a copy;
  - one case each for the PE machine, imports, `fresh` and `deps`;
  - a `gate_f2.txt` written by the code, read back and checked against contract 1.
- `actionlint` gives no errors on `core-win64.yml`.
- `sh -n tools/build-core-win64.sh` passes, and `shellcheck` too, if it is on the PC.
- Not a gate here: the real CI run is W5, in the main loop, after the merge.

## Brief W2b-release: the release tools (sonnet)

Model: sonnet. Step W2b2, item laz-706. Paste the common rules first. Worktree `<worktree>`, at the port-win-v1 tip.

Inputs:
- Plan D2, D7, D9 and sections 4 and 6, and [R2-S2], [R2-S3], [R2-S4], [R2-S5], [R2-S9], [R2-S10] and [R2-S12].
- Shared contracts 1, 2 and 3.
- Review 2's notes on `release_check.py` line numbers.

Files owned:
- `tools/mkrelease.sh`, `tools/release_check.py`, `tools/fetch.sh` and `tools/clone_check.sh`.
- `tests/fetch_fallback.sh` (new).

Do:
1. `fetch.sh`: the fallback exactly as plan D7, points 1-8.
   - The pins stay at v1.0.0 in your work; the main loop sets them in W7. Add `REL_TAG_PREV`, `LAZ_RELEASE_BASE_PREV`
     and `LAZ_FETCH_OS`.
   - Add the three-line `sha_of` fallback (`shasum -a 256`, else `sha256sum`).
2. `tests/fetch_fallback.sh` uses two local folders as the release bases (current and previous). The cases:
   - the asset is missing from current, so fetch falls back and prints the notice;
   - `LAZ_FETCH_OS=Darwin` for the Mac zip;
   - a wrong-sha file in current dies with no fallback;
   - `LAZ_RELEASE_BASE` set without `_PREV` gives no fallback;
   - the Windows zip missing dies with "v1.1.0 is not published yet".
3. `mkrelease.sh --inherit v1.0.0 --win-artifact DIR --out DIR`:
   - Check `V1_0_0_SHA256SUMS=288c2a257948498bb5c0f4e56a582ee311fd6654aa523b51fc85876e5ce19bec` first, then each of
     the seven lines, then the five repo pins (D2).
   - Build the Windows zip, the `git archive` of `tools/build-files.txt` and SOURCE.md (the mapping in plan section
     4), then SHA256SUMS. Use zip from MSYS2.
4. `release_check.py`:
   - The same SHA256SUMS pin, in `--inherit` mode.
   - An `asset(platform, kind)` helper that requires exactly one match, used at every `next(glob)` site (about lines
     102, 128, 297, 303, 345, 447 and 808 today).
   - `--gate-f2 FILE` reads contract 1, and replaces the live-tree keyblob check for win64.
   - Check 16: inherit only the Mac binary parts. `wording_findings` and the README check stay live, and a Windows
     twin of the wording check covers STATUS and the release notes.
   - The build-files check compares against `tools/build-files.txt`.
   - Windows check 6 compares build.inputs' `openssl_src_sha256=` with `core/OPENSSL.md` and with the inherited
     tarball.
   - It reads the private needles from `LAZ_PRIVATE_NEEDLES` on stdin only, as today.
   - Add planted reds: a third zip, a build asset missing the workflow, a bad SHA256SUMS digest, a `gate_f2.txt` with
     a FAIL line, and an openssl sha mismatch.
5. `clone_check.sh`, Windows mode:
   - Add `--until host`, `--stock-core PATH`, `--fixture DIR`, `--release-base URL` and `--branch NAME`.
   - Quote every path. PATH holds a space on the PC. Test it with the real interpreter path, read at run time from
     pyvenv.cfg's `home =` line; never write that path anywhere.
   - Replace `uptime` with a portable load line.
   - Skip the devkitARM testapp build block and use the release testapp.
   - Run pytest with `-rs --junitxml`, then `tools/skips_check.py --list w7`. Write `rc`.

Gates (on the PC, `D:\lazpy\p7\w2b2`):
- `release_check.py --plant-red` exits 0, and each new planted case fails for its own reason.
- `sh tests/fetch_fallback.sh` exits 0 and prints every case.
- `sh -n` passes on all three shell tools.
- `clone_check.sh --until host` runs to `rc` 0 against a bundle of your worktree. The main loop gives you the bundle
  path.

## Brief W6: docs, version and release notes (sonnet)

Model: sonnet. Step W6, item laz-707. Paste the common rules first. Worktree `<worktree>` on branch `p7-docs`, made
by the main loop. Edits only: no builds.

Inputs:
- Plan sections 1, 4 and 6, D6 and D7, and [R2-N4] and [R2-S4].
- The current `README.md`, `STATUS.md` and `docs/USING.md`.
- `docs/release-notes/v1.0.0.md`.

Files owned:
- `README.md`, `STATUS.md`, `docs/USING.md` and `docs/release-notes/v1.1.0.md` (new).
- The `version =` line in `pyproject.toml` and the `__version__` line in `python/libazahar/__init__.py`, both set to
  `1.1.0`.

Do:
1. README Windows block:
   - The MSYS2 MINGW64 shell, and the pacman line, including `zip`, `unzip` and zlib.
   - Clone into a short ASCII path such as `C:\src`.
   - `sh tools/fetch.sh`, `make`, and `pip install -e .` with a Python 3.10+.
   - Say that a GPU driver with Vulkan is required [R2-N4].
   - Replace the "work in progress" text with "proven on one PC", using section 6's limits.
2. USING: the differences table from plan section 6, including the OPENSSLDIR line. Leave a placeholder
   `<OPENSSLDIR from build.inputs>` for W5's value; the main loop fills it in.
3. STATUS: the limits, and the macOS sentence from plan section 7, item 6. Write both variants, and mark the one to
   keep as `<pick after W9>`.
4. Release notes: what is new, the differences, the limits, the inherited Mac assets, and the state test across
   systems as `<from W7>`.
5. No speed figures, no game names, and no claims past section 6.

Gate:
- Write the exact sentences that release_check's new Windows wording check must accept, in your notes for W2b2's
  owner.
- On the PC after W4: `C:\lazpy\venv\Scripts\python.exe -I tools/docs_check.py` exits 0.

## Brief W3: check of the fix diff (opus)

Model: opus. Step W3, item laz-708. Paste the common rules first. This is a review only.

Inputs:
- `git diff port-win-v1 p7-int` and `git diff p7-int p7-docs`.
- `docs/reviews/phase-7-diff-review.md`, `docs/reviews/phase-7-review-1.md` and `docs/reviews/phase-7-review-2.md`.
- The main loop's reruns of W1a on `p7-int`: `runs/p7/w3/darwin-pp.diff` and `runs/p7/w3/make-n.diff`.
- The W2a, W2b1, W2b2 and W6 notes under `runs/p7/`.

Do:
1. For every P7-R1 finding, and every R1 or R2 finding that the plan gives to W2 or W6, say "fixed", "not fixed" or
   "moved", with the commit or the file:line.
2. Review new code for new faults, especially:
   - `core-win64.yml`: the container, the non-root build, header handling and the leak check;
   - fetch.sh's fallback rules;
   - release_check's `asset()` helper and its `--gate-f2` reader;
   - clone_check's quoting.
3. Confirm again that the Darwin-visible diffs hold only the reviewed hunks.

Files owned: `docs/reviews/phase-7-fix-check.md` (new), `runs/p7/w3/notes.md`.

Gate: there is a table with every finding and its state. Zero blockers are "not fixed". Any new finding is
`P7-R3-<n>`, with a severity.

## Brief W8: release audit of v1.1.0 (release-legal-audit)

Model: release-legal-audit agent. Step W8, item laz-712. Paste the common rules first. Read-only, except your
report and notes.

Inputs:
- The staged release, copied read-only to `runs/p7/w8/staged/` by the main loop. It has the Windows zip, NOTICES,
  SOURCE.md and SHA256SUMS. Inherited assets are listed by name and sha only.
- The repo at the candidate release commit (local main, not pushed).
- `runs/p7/w5/checks.txt`, `runs/p7/w7/` (clone_check and release_check output), and
  `docs/reviews/phase-7-ip-legal.md`.
- v1.0.0's audit, kept privately at `runs/reviews/release-legal-audit-v1.0.0.md` in the main checkout.

Do:
1. Audit the delta from v1.0.0:
   - the Windows zip's contents and NOTICES;
   - the corresponding source for each shipped binary (SOURCE.md against the actual assets);
   - the mingw runtime source tar;
   - the README, STATUS, USING and release-notes claims against the evidence;
   - the repo history since v1.0.0, for ROMs, keys, secrets, private paths and emails. The needle scan's results
     are in `runs/p7/w7/`; do not ask for the needles.
2. Confirm that the seven inherited assets are listed with v1.0.0's digests.

Files owned: `runs/reviews/release-legal-audit-v1.1.0.md` (new; gitignored and private, as v1.0.0's was),
`runs/p7/w8/notes.md`.

Gate: the verdict is "shippable" or "not shippable", with each remediation named by file. The main loop then asks Guy
for the publish word.
