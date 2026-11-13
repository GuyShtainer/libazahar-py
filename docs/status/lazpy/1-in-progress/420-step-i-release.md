---
id: laz-420
title: lazpy
order: 420
kind: step
parent: laz-400
page: Legal audit and the public GitHub release
hours: -
---
# Step I: legal audit and the public GitHub release

## What it is
The release legal audit over repo, history and assets; a release with our core, Azahar's source tarball unchanged, our patches, notices and the test app. Push only on Guy's word.

## Exit gate
The gate in `docs/PLAN.md` line 323 ("Phase I"), run headless on this Mac with a pass/fail answer.

## Evidence
- 2026-11-13 04:11: I1 done. Built in 46c808e, review fixes (S4-S6 with COPYING.NEWLIB quoted, N4-N9) in 3c11544, merged
  into main with --no-ff (code.md and runners.md conflicts kept both sides; runners' mknotices line gained --newlib).
  Gates after the fixes: release_check runs/release/v0.1.0 --skip-pins 0 FAIL; --plant-red all 18 plants caught, rc 1;
  pytest -m "not slow" 110 passed in the worktree, 109 passed + 1 skip (process already nice) on merged main;
  docs_check PASS on all eight checks with NOTICES.md present. The worktree's staging copy is kept in runs/step-i/
  (ignored). I2 (pins commit, mkrelease in MAIN, --pre-push, clone_check), I3 (release-legal-audit) and I4 remain here;
  the item stays in 1-in-progress until I3 passes.
- 2026-11-13 04:19: I2 steps 2-4 done in MAIN. The test app from the README's build block under env -i: rc 0,
  0 warnings, 0 /Users/ strings, sha256 53b699e8... equal to the staged one (an incremental build first showed 6
  /Users/ strings from stale objects: make clean before a release build). mkrelease, the pins committed alone
  (5d91d40), mkrelease again: only the build-files asset changed. release_check's needle loader did not strip the
  private file's literal: prefix, so those lines could never match; fixed in a9d144e (a planted literal line now
  matches) and re-staged. Check 15 wanted the repo's own git identity: set in .git/config (local) to Guy's no-reply
  identity. Then release_check --pre-push with the private needle file: rc 0, PASS 1-16; --plant-red 18 of 18 caught;
  docs_check all PASS. Logs: runs/i2/ (ignored).
- 2026-11-13 04:21: I2 step 5 done: clone_check from a fresh clone of main with the staged release as file:// base
  ended "clone ok: 114 s wall" (rc 0): the README steps, quickstart on our core at the default path, the build block,
  quickstart on the built host, the full pytest with LAZ_REQUIRE_EMULATOR=1: 136 passed, 3 skipped (two need
  LAZ_STOCK_CORE, one needs a process not already nice). Log: runs/clone-i2/ (ignored). I2 done; I3 next.

## Pointers
- Plan section: `docs/PLAN.md:323`
- Phase plan: `docs/plans/phase-4.md` (index), `docs/plans/phase-i.md` (the builder's brief, revision 2)
- Review: `docs/reviews/phase-4-as-built.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- 2026-11-13 03:18, main loop: launched per phase-4.md section 2 after Phase 3 (29cb592 before G8b), G8b (896c2fe) and
  the downloads (item 400's notes). Launch defaults: Q1 remove the stock fetch (P17), G2 (a), the consult GREEN.
  I builder a8e760acbd1172ce5 (sonnet), launched 03:19 in ../libazahar-py-i (step-i at 896c2fe).
- I1 done 03:42 (a8e760acbd1172ce5), committed on step-i as 46c808e by the main loop with rule 3's new wording
  (no stock fetch; LAZ_STOCK_CORE; GPLv3 corresponding source), runners.md (gate B's fe2 runner, gate F2's --stock,
  c4, the prototype, a release block), tools.md and code.md lines; needle 0, no removed material, no array window
  in any staged file (the /Users/, @gmail and 0xNN hits are the checks' own patterns and plants). keyblob_findings()
  empty at I0. Gates: 1 release_check --skip-pins rc 0 (checks 1-6, 8, 9, 13, 14, 16 PASS; 7 and 12's needle part
  SKIP without LAZ_PRIVATE_NEEDLES; 10 PEND until committed; 11 skipped); --plant-red: every planted check failed on
  its plant (10 and 15 not planted). 2 mkrelease.sh three runs, identical SHA256SUMS. 3 fetch.sh --lazpy-core
  --testapp on a file:// base: verified and unpacked, second run only "have", a flipped byte deleted (rc 1), a TBD
  pin refused. 4 fast pytest 110 passed (numpy installed by hand: pip install -e . does not pull it), make ok,
  testapp /Users/ strings 6 -> 0. Staged (runs/release/v0.1.0, HEAD 896c2fe): core zip 8,865,648 bytes sha256
  8e54029b...; source asset 43,500,628 f7a70044... (core/PIN-nokeys); OpenSSL and SNAP as downloaded; test app
  151,540 53b699e8...; NOTICES.md 177,483; SOURCE.md 4,137.
  Departures: (1) the OFL's first line (copyright plus the upstream author's contact address) is not quoted, since
  check 7 fails on @gmail.com; NOTICES uses the font's name-record copyright line; one Boost block's address became
  "[address omitted]". (2) source notices matched by regex; GPL-family holders listed by holder and file. (3)
  SOURCE.md's compiler is AppleClang 17.0.0.17000604 from CMakeC*Compiler.cmake (configure.log has no such line and
  holds /Users/). (4) nlohmann json and httplib carry no licence text: their SPDX lines plus the MIT body from
  robin-map's LICENSE. (5) no newlib licence file under /opt/devkitpro: named "BSD-style, see COPYING.NEWLIB". (6)
  bsdtar keeps uid 1001/"runner" on @archive members and whole-second mtimes; check 9 compares neither uid nor
  names. (7) gate_c's fallback was line 290. (8) fetch.sh and mkrelease.sh mode 755. (9) --force deletes only the
  chosen parts. Left for others: docs/USING.md:10 still says fetch.sh fetches the stock core (step H's file);
  tests/gate-a.sh:32 still works (no-flag fetch = MoltenVK plus headers). release_check.py is 845 lines.
  Lessons: bsdtar's --uid/--gid/--uname skip @archive members and it drops fractional mtimes; cp onto an existing
  644 file keeps 644, so gate 3 runs fetch.sh with sh or after chmod.
