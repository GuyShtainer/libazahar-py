# Phase 4 plan, review 2 (revision 1 of phase-4.md, phase-h.md, phase-i.md; the last review)

Opus review, 2026-11-13, 01:00-01:25. Read: CLAUDE.md, docs/map/rules.md, the three plan files as revision 1 left
them (committed 027553b, now 7d51534 after G8), `docs/reviews/phase-4-review-1.md`, `core/PIN`, `core/README.md`,
`tools/build-core.sh` (main at 7c33f38, before G8 799e8c3), `docs/plans/phase-3.md` section 4 item 0 and section
12, `docs/plans/phase-f2.md` sections 1 and 6, items 300 and 400 (their last notes), the finished step-0 build in
MAIN (`build-core/build.inputs`, `CMakeCache.txt`, `link.txt`, one `.o.d`, `build.exit` 0 at 01:06), the Homebrew
keg, `/opt/homebrew/bin/git-filter-repo`, the commit map, `python/libazahar/` (for Gen3D's friction points) and
Gen3D's `docs/phase2-safe/LAZPY-TRY-1.md:46-58`. Nothing built, run or committed; no emulator. Line numbers below are
of the files at HEAD 76019a9 (G8 did not change any tree). Grades as review 1: **BLOCKER** (ships something wrong,
or a gate cannot pass as written), **SHOULD** (fix in revision 2), **NICE**.

Counts: **4 blockers, 9 should fix, 7 nice.** Verdict in section I: **ready after revision 2** (text edits plus one
Makefile line; no third review).

Privacy: this file never names Guy's personal address or its local part. I did not re-run the needle scan (it would
read the address); I read G8's recorded result (item 400's last note) and checked the commit map's row count.

Events while this review ran: the step-0 rebuild ended 01:06 (exit 0); **G8 ran 01:06-01:08** (commit 6898a4b,
`docs/commit-map-g8.tsv`); Phase 3's E and F2 worktrees were made after it (at 6898a4b). So Q6 is answered by
events (section F).

## A. Verified facts (my own checks)

- **Step 0 as built** (`tools/build-core.sh` at HEAD; `build-core/build.inputs` of the 01:02 build):
  - the pin key is `OPENSSL_PREFIX=/opt/homebrew/opt/openssl@3` (`core/PIN:11`), resolved with `cd -P`
    (`build-core.sh:70`) to `/opt/homebrew/Cellar/openssl@3/3.6.5`; the override is **`LAZ_OPENSSL_PREFIX`**
    (`build-core.sh:8, 39`); there is no `OPENSSL_ROOT` and no `LAZ_OPENSSL_ROOT` anywhere in the code;
  - `LAZ_CORE_DROP` has four entries, the fourth a **directory**, `externals/libressl` (`core/PIN:9`); the drop loop
    takes directories (`rm -rf`, `build-core.sh:89-96`); the `.o.d` guard greps each entry's basename
    (`:161-166`), so `libressl` is guarded;
  - `build.inputs` is written after the configure guards, before the compile (`build-core.sh:140-158`, not
    `:130-145`); keys `openssl_version=`, `openssl_prefix=` (the Cellar path), `openssl_libssl_sha256=`,
    `openssl_libcrypto_sha256=` (`:150-153`), and `cmake=` is **the whole configure command** with `$ROOT` as
    `<repo>` (`:156`; the file's last line today), so Phase 4's "ask 6" is done;
  - today's file: `head=799e8c3...` (the commit map gives 7c33f38), `clean=yes`, libssl.a `23c6a50d...`,
    libcrypto.a `88981a4c...` (the same `.a` files as the 00:52 build);
  - `CMakeCache.txt`: `USE_SYSTEM_OPENSSL:BOOL=ON`, `OPENSSL_SSL_LIBRARY:FILEPATH=/opt/homebrew/Cellar/openssl@3/
    3.6.5/lib/libssl.a` (and libcrypto); `link.txt` names those two Cellar paths; `nus_download.cpp.o.d` names
    `/opt/homebrew/Cellar/openssl@3/3.6.5/include/openssl/ssl.h`. **No build file names `/opt/homebrew/opt/`.**
- `keyblob_findings(build_dir, core, src_root, tree, repo)`: the drop list and pins come from `repo/core/PIN`
  (phase-f2.md:218-224, phase-3.md:573, :659-661). f1 inside it already checks the inputs' hashes, `clean=yes`, the
  OpenSSL version, the cache lines, the drop entries, the `.o.d` files, the windows, the strings (`-lazpy.1`, no
  `/Users/`, no `libressl`, `OpenSSL 3.6.5`), `otool -L` and `link.txt` (phase-f2.md:28-54), and **requires OURS's
  mtime to be later than `CMakeCache.txt`'s** (phase-f2.md:30).
- **`build/testapp.3dsx` (151,948 bytes, 00:53) holds 6 `/Users/<user>/VSCodeProjects/...` strings**: `assert()`'s
  `__FILE__` paths (`testapp/source/draw2d.c:4, 23, 48, 57`, `font.c:4`); `testapp/Makefile:22-23` has no prefix map.
  `build/libazhost.dylib`: 0.
- Homebrew keg: `/opt/homebrew/Cellar/openssl@3/3.6.5/.brew/openssl@3.rb` exists (6,723 bytes, sha256
  `8fa691c3aade8a06699a7f36f11bf66dd81a7747f9163642a08d71df155a3853`, dated with the bottle): the formula Homebrew
  installed. Its configure arguments: `--prefix`, `--openssldir`, `no-ssl3`, `no-ssl3-method`, `no-zlib` plus
  superenv's cflags/cppflags/ldflags (lines 44-56), `darwin64-arm64-cc enable-ec_nistp_64_gcc_128` (:85),
  `perl ./Configure` (:93). There is **no homebrew-core tap** (`/opt/homebrew/Library/Taps/homebrew/homebrew-core`
  absent), so `brew cat` needs the network. `INSTALL_RECEIPT.json`'s `source.path` holds a home-folder path (never
  copy it). `brew list --pinned` shows `openssl@3` (pinned 01:04). Both `.a` sizes match R30.
- **G8 is done** (item 400, last note; 6898a4b): 20 commits rewritten. The map has 20 rows, which is complete: of the
  25 commits in `1844a5d^..bf73f3c`, 20 descend from 1844a5d (rewritten) and 5 are step-d's (unchanged SHAs).
  `git worktree list`: MAIN, `-c`, `-d`, `-e`, `-f2`; no `refs/replace`. `git filter-repo --force` skips the
  "fresh clone" sanity check that would abort on several worktrees (`git-filter-repo:3327-3330`, `:3512-3515`).
- rules.md 1 paths: none in `git ls-files`, none ever added in history (the plan's check 13 pattern, run by hand).
- Gen3D's friction (section G): `timeout` is already a no-progress limit: the heartbeat moves every frame
  (`host/run.c:117`), the client times out when it stands still (`_client.py:153-176`; docstrings
  `emulator.py:57-58, 145`); bad input frames raise `ValueError` (`inputs.py:146`); `run()` keys `result.shots` by
  batch frame (`emulator.py:142, 181-190`) while USING says "Shot names carry absolute frame numbers"
  (`docs/USING.md:24`); nothing clears `sys/Azahar/sdmc/` on reuse (`emulator.py:55-56, 76`).

## B. Blockers

- **B1. The drop list now holds a directory, and four places in phase-i.md assume three files.** `core/PIN:9` adds
  `externals/libressl`; Phase 4's source asset is "TARBALL minus `LAZ_CORE_DROP`" (P10, phase-4.md:201), so the
  asset **has no LibreSSL**. Then:
  1. the note member (phase-i.md:174-178) wants "`<path>` sha256 `<hex>` (one line per drop-list entry, hashed from
     TARBALL's member)": a directory has no sha256; and "They hold Azahar's built-in key data and its default HTTP
     client certificate" is **false** for the fourth entry, inside the shipped source;
  2. check 10 (phase-i.md:256-259) compares "the same names ... except the drop-list entries": read literally, every
     member under `externals/libressl/` is "missing", so the check cannot pass, or the builder improvises;
  3. SOURCE.md's "Azahar's tarball also contains `externals/libressl`; this build does not compile or link it"
     (phase-i.md:190-191), NOTICES' "Not included" line (:151) and phase-4.md 0.4 (:55-56, "LibreSSL's sources stay
     inside Azahar's tarball ... unbuilt; SOURCE.md says so") and section 13's S5 line (:442-443) describe a
     tarball we no longer ship;
  4. R5 (phase-4.md:223) and R28 (:246) list three entries ("any of the three headers").
  **Fix:** the note text lists the three files with their sha256 and "`externals/libressl/` (the bundled LibreSSL,
  `<n>` members): not used, the core links OpenSSL 3.6.5 (`USE_SYSTEM_OPENSSL=ON`)"; for a directory entry write
  its member count and the sha256 of its sorted `name sha256` lines. Check 10: a member is "dropped" if its name
  equals an entry or starts with `<entry>/`; FAIL if any such member is present in the asset. SOURCE.md and NOTICES:
  "Azahar's original tarball also contains the bundled LibreSSL; we removed it with the three headers". Fix
  0.4, S5's line, R5, R28. I1 also prints `tar -tf <asset> | grep -c 'externals/libressl'` (0). The consult (9.1 Q2)
  was asked about "an unbuilt LibreSSL" in the asset: moot now, no re-ask; say so in the audit brief (9.2 (3)).
  Hours: +0.02 (I).
- **B2. Step I's interface with step 0 is stale in four ways that break its gates or ship a wrong instruction.**
  1. "KEG" is `/opt/homebrew/opt/openssl@3` (phase-i.md:17), and mknotices classifies DEPS paths as KEG and exits 1
     on "any other path" (:121-125); every OpenSSL path in DEPS and LINK is `/opt/homebrew/Cellar/openssl@3/3.6.5/...`
     (section A), so mknotices exits 1 on the first OpenSSL header;
  2. check 6 reads "the paths INPUTS' `openssl=` line gives" (:234): there is no `openssl=` line (keys
     `openssl_version=`, `openssl_prefix=`, `openssl_*_sha256=`); phase-i.md:60-62 and R27 (phase-4.md:245) quote
     the old one-line format and "`cmake=` (the cmake binary only)";
  3. check 2 calls `keyblob_findings(BUILD, core, SRC, TREE, <LAZ_CORE_DROP split>)` (phase-i.md:225-226; R28
     phase-4.md:246): the planned signature's last argument is `repo` (section A), so the call is a `TypeError` or
     checks the wrong thing;
  4. `LAZ_OPENSSL_ROOT` (phase-i.md:207, phase-4.md:342) does not exist: the code reads `LAZ_OPENSSL_PREFIX`, so
     `core/OPENSSL.md`'s rebuild recipe would ship a variable the script ignores (the user's own OpenSSL is then
     silently not used, or the build dies on the version check).
  Also stale in the same paragraphs: `OPENSSL_ROOT` (phase-4.md:22, phase-i.md:54), "commit 5e95423 ... started
  00:49" (phase-4.md:17-18, :219; phase-i.md:51), `head=5e95423` (phase-4.md:64, :245; phase-i.md:61), `<keg>` in the
  configure line (phase-i.md:56).
  **Fix:** define KEG as INPUTS' `openssl_prefix=` (the resolved Cellar path), and at I0 check that `cd -P
  /opt/homebrew/opt/openssl@3` gives the same path; mknotices and check 6 classify by that prefix; R27 and
  phase-i.md 2 quote section A's key list; check 2 passes `repo=<the checkout>`; `LAZ_OPENSSL_PREFIX` everywhere;
  step 0's current SHAs as "7c33f38 (799e8c3 before G8)". Hours: 0 (text).
- **B3. H's own docs_check forbids what H's STATUS must say.** `forbidden` holds `macOS 11` for STATUS.md
  (phase-h.md:241-243), while STATUS must say "the v0.1.0 core's header says macOS 11.0 but it needs macOS 15"
  (:167) and "building OpenSSL ourselves for macOS 11-14" (:170-171); phase-h.md:78 says "Never write '11.0'",
  :167 says write it. Gate 1 cannot pass as written. **Fix:** forbid the claims, not the number: `macOS 11 or
  later`, `macOS 11+`, `macOS 11.0 or later`, `macOS 11 and later`; :78 becomes "never write 11.0 as a
  requirement"; the STATUS lines stand. Plant for check 2 unchanged (`full speed`). Hours: 0.
- **B4. The shipped test app carries home-folder paths, so check 8 fails and the plan forbids the fix.** Section A:
  6 `/Users/<user>/...` strings from `assert()`. Check 8 FAILs on `/Users/` in `testapp.3dsx` (phase-i.md:244-246);
  I2 rebuilds the app in MAIN (`/Users/...` again) and the clone builds it under `runs/clone-i2/` (also
  `/Users/...`); `testapp/` is on Phase 4's no-touch list (phase-4.md:170). **Fix:** give I one line in
  `testapp/Makefile`: `CFLAGS += -ffile-prefix-map=$(abspath $(CURDIR)/..)/=` (or whatever root the Makefile
  compiles from; I1 verifies `strings -a build/testapp.3dsx | grep -c /Users/` is 0 after `make testapp`, and
  `assert` keeps working); add the row to section 3 and phase-i.md section 4; I0 adds the `strings` count to its
  rows. Do **not** use `-DNDEBUG` (it changes the app). Hours: +0.02 (I).

## C. Should fix

- **S1. `keyblob_findings` on the zip's core may fail on mtime.** f1 requires the core's mtime to be later than
  `CMakeCache.txt`'s (phase-f2.md:30); mkrelease sets `touch -t 202601010000` (phase-i.md:166) and "extracted to a
  temp file" (:221) does not say how: `unzip` restores 2026-01-01 and check 2 FAILs. **Fix:** check 2 first proves
  `sha256(zip's dylib) == sha256(CORE)`, then calls `keyblob_findings` on CORE (MAIN's real file); the plant copies
  the core (a fresh mtime) and appends the window. Hours: 0.
- **S2. release_check repeats what `keyblob_findings` already does.** Checks 4 (`-lazpy.1`, patch 0005's hash), 6
  (LINK's `.a` paths, no `libressl` in LINK/DEPS/strings, `USE_SYSTEM_OPENSSL`, `OpenSSL 3.6.5`), 7 (every input
  hash, `drop=`, `clean=`) and half of 5 (`otool` without libssl/libcrypto) are f1 items (phase-f2.md:28-54). Two
  implementations drift, and B2's fixes would have to land twice. **Fix:** check 2 is the import; check 4 keeps only
  `2126.2` in the strings; check 5 keeps MoltenVK/Vulkan; check 6 keeps OSSL's sha256 against `core/OPENSSL.md`
  and the SBOM, the staged asset against OSSL, `openssl_version=` against OSSL's name, and KEG's `.a` against INPUTS
  under `--pre-push`; check 7 goes (its `head=` print moves to check 2's output). Plants 6 and 7 go (plant 2 covers
  them through the function). Hours: -0.04 (I).
- **S3. SOURCE.md's build lines: one source, the real one.** phase-i.md:188-190 quotes "the `cmake` lines from
  `tools/build-core.sh` at HEAD" plus `configure.log`'s compiler lines; phase-4.md:440 says "SOURCE.md copies the
  cmake line from `build.inputs`". Step 0 made `cmake=` the executed words with `<repo>` (`build-core.sh:156`).
  **Fix:** SOURCE.md quotes INPUTS' `cmake=` line verbatim plus `configure.log`'s two "compiler identification" lines
  (check 8 scans them); drop the "quoted from build-core.sh" path and phase-4.md section 12 ask 6. Hours: -0.02 (I).
- **S4. The rebuild route we publish is only half true, and untested.** SOURCE.md and USING tell a stranger to
  rebuild with "Homebrew `openssl@3` at the pinned version" (phase-i.md:191-192, phase-h.md:191-192). Homebrew keeps
  one version: once `openssl@3` moves past 3.6.5, `brew install openssl@3` gives a version `build-core.sh:73`
  refuses. The other route, OpenSSL built from the attached tarball as `core/OPENSSL.md` says (phase-i.md:205-207),
  is never run here, and cannot be under rules.md 2 (only Azahar's CMake build may run from a download). Also the
  Azahar asset's own route (`LAZ_CORE_PIN=core/PIN-nokeys`) is never tried: nothing proves `untar_checked.py`
  accepts bsdtar's output. **Fix:** (1) SOURCE.md, USING and OPENSSL.md say plainly: "Homebrew ships only its
  current `openssl@3`; for 3.6.5 build it from `openssl-3.6.5.tar.gz` (recipe below, not tested by this project)
  and set `LAZ_OPENSSL_PREFIX`"; the recipe ends with `make install_sw` into a prefix; (2) release_check check 10
  also runs `python3 -I tools/untar_checked.py <asset> <tmp>` (our own script; seconds) and checks the member
  count; (3) a Guy question for Phase 5 (with risk 9's macOS 11 build): extend rules.md 2's exception to OpenSSL's
  pinned tarball so the recipe can be tested. Hours: +0.02 (I).
- **S5. G8 is done; the plan still branches on it.** phase-4.md:96-97, :111 ("[G8 here if not done 'now']"),
  :189 (merge step 5), :272-274 (G8 "recommended timing"), risks 15-16 (:358-362), section 11's G8 row (:376),
  section 12 Q6 and Phase 3 ask 4 (:393, :407-408), phase-i.md:360-361, and 8.1 written as a to-do. **Fix:** G8 is a
  record: "done 01:06-01:08 (6898a4b), 20 commits, `docs/commit-map-g8.tsv`, checks as 8.1 step 6"; delete the
  "if not done" branches; keep check 13's history scan, `--pre-push` with the needle file, and I5's bundle
  deletion; 8.1 stays as the procedure for a second pass (risk 7). Hours: 0.
- **S6. Phase 3's asks are mostly answered; say which.** Section 12 for Phase 3 (phase-4.md:401-419): 1 (`brew
  pin`, done 01:04), 4 (G8, done), 6 (full `cmake=`, done), 7 (`externals/libressl` dropped, done) are done; 2 and 3
  stand; 5 stays optional (PIN-nokeys' note-member trick still needed: `build-core.sh:40-42` refuses an empty drop
  list); 8 stands. R30's "not `brew pin`ned yet" (:248) and risk 13's "Ask" (:351-352) become "pinned 01:04".
  Also phase-3.md:586 says "Phase 4 pins its tarball URL and sha256 in `core/PIN`": Phase 4 must not (any edit to
  `core/PIN` breaks `pin=` against `build.inputs` and so check 2); one line in phase-4.md section 3 saying why.
  Hours: 0.
- **S7. Gen3D's friction: four USING lines for H** (section G). phase-h.md 3.3 gains them, and checklist item 5
  (phase-h.md:377-379) spot-checks them. Hours: +0.02 (H).
- **S8. R1, R2, R10 and the inputs paragraph describe the 00:52 build and 93 commits.** phase-4.md:17-23, :219-220,
  :228 (98 commits now); phase-i.md:100-102 ("The P9b core is 21,828,992 bytes": still true for the 01:06 build,
  item 300's last note, but say which build). R2's state "holds on P9b" should name the 01:06 build F2 gates.
  Hours: 0.
- **S9. Q7: take the formula from the keg, not `brew cat`** (section F). phase-i.md:203-205 and the report item
  "whether `brew cat` worked" (:531) change. Hours: -0.02 (I).

## D. Nice

- **N1.** Check numbering in 3.3 runs 15, 17, 16 (phase-i.md:273-287): renumber (16 = macos, 17 = plant-red).
- **N2.** USING's environment table (phase-h.md:88-91, 186-188) has no build-time variables: `LAZ_OPENSSL_PREFIX`,
  `LAZ_CORE_PIN`, `LAZ_CORE_PATCHES`, `LAZ_CORE_LTO`, `LAZ_CORE_JOBS` (`build-core.sh:7-8`), `LAZ_RELEASE_BASE` and
  `LAZPY_ROOT` (fetch.sh). One "build and fetch" sub-table in "Getting our core".
- **N3.** After the README route, `LAZ_CORE` lives only in that shell, and the library's default is the stock path
  (R12). USING's troubleshooting: "no core at `dl/azahar/azahar_libretro.dylib`: set `LAZ_CORE` (fetch.sh printed
  the line)"; H0 records the real error text. A default that prefers `dl/lazpy-core/...` is a code change for
  later (`_paths.py:34-36`).
- **N4.** Gen3D's 222.6 fps (LAZPY-TRY-1.md:20) is not a README number: its source is outside this repo, its SD held
  a commercial GBA game (G9's issue), and the machine was at load 13-46. phase-h.md section 2's "only speed numbers"
  list already excludes it; one sentence makes it explicit.
- **N5.** Gen3D used "an rsync copy" of the package (LAZPY-TRY-1.md:9-10). If that copy holds a `.git`, it holds the
  pre-G8 history: the main loop asks Gen3D's session to confirm it has none (or deletes it). One line in 8.1 step 9.
- **N6.** The audit brief (9.2 (3)) should say the Azahar asset holds no LibreSSL (B1), and (2) that the core's
  `openssl_prefix` in the zipped `build.inputs` is a Homebrew path, expected.
- **N7.** `docs_check`'s `forbidden` list could also hold `aes_keys.txt` instructions' cousins (`prod.keys` is there;
  `title.keys`, `boot9`, `sysdata`): cheap, catches a pasted troubleshooting line.

## E. Review 1's findings in revision 1's text

| Finding | In the text? |
|---|---|
| B1 ClCertA | Yes (0007, drop list, check 2 through `keyblob_findings`, 0.2, ip-legal (1), 9.2 (2)); R28 and check 2's call are stale (B2.3), and the drop list grew (B1) |
| B2 the address | Yes: needles from a private file (check 8, 13), never typed; G8 done (S5) |
| B3 devkitARM in `env -i` | Yes (phase-h.md:67-71, 3.7 step 4; I2 step 2) |
| B4 pytest | Yes (phase-h.md:74-75, 193, 3.7 step 5) |
| B5 version string | Yes (check 4, R3); folded into check 2 by S2 |
| B6 working tree vs HEAD | Yes (checks 9, 11, `--pre-push`) |
| B7 `8.8.8.8` | Yes (check 8) |
| S1 stripped tree | Yes (built so; check 10 is the member comparison) |
| S2 `build.inputs` | Yes, but quoted in the old format (B2.2) |
| S3 real prefix map | Partly: two sources disagree (S3 here) |
| S4 key loading | Yes (0008; ip-legal (1)) |
| S5 LibreSSL | Superseded by G3; its "sources ride in the tarball" line is now false (B1.3) |
| S6 citations | Yes (section 8) |
| S7 `src/` notices | Yes (3.1 step 2) |
| S8 clone on the pushed tree | Yes (I2 step 5, `clone_check.sh`) |
| S9 fetch flags | Yes (3.4) |
| S10 `__version__` | Yes (section 3 row, check 14) |
| S11 re-stage drift | Yes (`git archive`, pins at I2, no asset hash in SOURCE.md) |
| S12 test app from the tag | Yes (I2 step 2); but the app carries home paths (B4) |
| S13 D's USING line | Yes (fixed in D; H0 checks) |
| S14 safe defaults | Yes (section 7) |
| S15 audit misses | Yes (9.2 (1), (2)) |
| S16 Phase 3 rows | Yes (R12, R14, R29) |
| S17 consult now | Yes (it is running) |
| N1-N9 | Yes (N4's commit count is stale again: 98, S8) |
| N10 | Declined, with a reason |

## F. The open questions

- **Q5 (README route on our core): yes, keep P16, whatever ip-legal says on question 7.** Our core is the binary the
  audit grades and the one without the blob and ClCertA; the route then needs no devkitARM (B3 of review 1 leaves
  the main path) and no Homebrew. Sharpen two things: (1) the fallback chain when the consult holds the core asset
  back (risk 2): the route becomes the build block (`build-core.sh` plus `make testapp`), which needs Homebrew
  `openssl@3` at 3.6.5 or a self-built one (S4), so README's fallback text must say that, not just "build it"; (2)
  `LAZ_CORE` does not persist past the shell (N3). The stock-core line stays one optional line, removable in I4.
- **Q6 (G8 timing): settled by events.** G8 ran 01:06-01:08, after the step-0 build ended and before Phase 3's
  worktrees (both made at 6898a4b). Its checks passed (item 400). Nothing in Phase 4 waits on it any more; S5 lists
  the text to retire. One duty remains: nothing committed before the push may bring the needle back (check 13 and
  `--pre-push` with the needle file, already planned).
- **Q7 (`brew cat` for OpenSSL's build script): use the keg's own copy, `KEG/.brew/openssl@3.rb`, and do not attach
  it.** It is the formula Homebrew installed with this bottle, read offline (no tap here, so `brew cat` needs the
  network and could return a newer revision). `core/OPENSSL.md` records its sha256 (`8fa691c3...a3853`) and its
  homebrew-core path (`Formula/o/openssl@3.rb`), quotes its configure arguments (lines 44-56, 85, 93) and
  `openssl version -a`'s platform and compiler lines (the superenv flags' real values), and says "no patches"
  (SBOM). With the upstream tarball attached, that is the configure line and the build commands of the linked
  libraries, which is what "scripts used to control compilation" asks for a library we did not modify. Attaching the
  formula itself would add Homebrew's licence to NOTICES for a file nobody runs; the quote is enough. Never copy
  `INSTALL_RECEIPT.json` (a home-folder path).

## G. Gen3D's first use (LAZPY-TRY-1.md:46-58): what goes where

| # | Friction | Docs (H, `docs/USING.md`) | Code | Where and when |
|---|---|---|---|---|
| 1 | `run(timeout=)` felt like a wall bound for the batch | Section 3 or the `run()` line: "`timeout` is a no-progress limit: seconds with no new frame (default 30), not a bound on the batch; a long batch needs no big value. Use `wall_limit` for a wall bound. Raise `timeout` only when one frame can stall long (first shader compiles mid-run)." | none: the code already does this (`host/run.c:117`, `_client.py:153-176`) | H, now |
| 2 | input frame 0 raises a plain `ValueError` | Section 3: "`inputs` and `shots` take batch frames 1..`frames`; anything else raises `ValueError` (a bad argument, not a `LibAzaharError`: catch both)." | `class ArgumentError(LibAzaharError, ValueError)` raised for every bad argument (`inputs.py`, `emulator.py`, `errors.from_code`'s `AZH_E_ARG`), with one test. Backward compatible (still a `ValueError`), so it can wait | after v0.1.0 (Phase 5 or a follow-up), about 0.1 h; not Phase 4 (no `python/` edits) |
| 3 | shot keys are batch frames, file names whole-run frames | Section 3, next to "Shot names carry absolute frame numbers" (USING.md:24): "`result.shots` is keyed by the batch frame you asked for; the file name holds `first_frame + f - 1`." | none | H, now |
| 4 | a reused workdir keeps the old SD with the warm shader cache | Section 2: "Reusing `workdir` keeps everything under `sys/`, the SD included; `sd_seed` is copied on top and nothing is cleared. For a warm cache and a clean SD, delete `workdir/sys/Azahar/sdmc/` before creating the Emulator." | an option (`fresh_sd=True`, clear the SD folder before seeding), one test | after v0.1.0, about 0.1 h |

Phase 4 cost: about 0.02 h of H (S7). The two code items go to STATUS's `## Next` as one line each (H), and to a
Phase 5 item (the main loop).

## H. Hour-saving pass

| Change | Saves | Costs |
|---|---|---|
| S2: release_check leans on `keyblob_findings` (checks 4, 6, 7 shrink or go; plants 6, 7 go) | about 0.04 h and a second implementation of B2's fixes | none |
| S3: SOURCE.md quotes INPUTS' `cmake=` verbatim (step 0 already writes the real words) | about 0.02 h and the "which lines of build-core.sh" choice | none |
| Q7: the keg's `.brew/openssl@3.rb` instead of `brew cat` with a 30-second network attempt and a fallback | about 0.02 h and one report item | none |
| G8 already done (0.05 h booked, hours.tsv:75, against 0.1 planned) | 0.05 h off the main loop's 0.5 | spent |
| Not cheaper, but needed: B1 (note text, check 10 prefix rule, docs lines) +0.02; B4 (one Makefile line, a strings check) +0.02; S4 (honest rebuild text, the `untar_checked.py` run) +0.02; S7 (Gen3D's four USING lines) +0.02 | | +0.08 h |
| Considered, declined: `vtool -set-build-version` to write minos 15.0 into the core after the build (the shipped binary would then differ from the script's output; STATUS's line is cheaper); building OpenSSL for macOS 11 (risk 9, rules.md 2 forbids running its build here); ScanCode/`reuse` (as revision 1) | | |

**Net: about -0.05 h, so the phase is about 2.15 h** (H 0.47, I 0.63, joint as-built review 0.2, main loop and legal
agents 0.45, loops 0.4), against PLAN.md's 1.1 h plus loops.

## I. Verdict

**Ready after revision 2.** No new design is needed: B1-B3 are text fixes in phase-i.md and phase-h.md, B4 is one
`testapp/Makefile` line given to I with a `strings` check. With S1-S9 taken, both briefs match the code on main at
76019a9 and the build F2 is gating. No third review: the as-built review (phase-h.md 12, phase-i.md 12, plus B1's
check-10 rule, B4's count and S1's hash-then-path call) catches the rest.

Revision 2 order (the cheapest path): B2 and S8 together (one pass over the stale step-0 facts, both files), B1,
B3, B4, S1-S3 (release_check), S4, S5-S6 (G8 and the asks as records), S7 (Gen3D lines), S9 (Q7), then the nice
items. Section 14 lists each.

For Guy (no new blocking question): the open items stay G5, G6, G7, G9; one new item for later, not for v0.1.0:
whether rules.md 2's exception may cover building OpenSSL from its pinned tarball (S4, with risk 9's macOS 11 build).
