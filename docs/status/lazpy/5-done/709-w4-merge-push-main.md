---
id: laz-709
title: lazpy
order: 709
kind: step
parent: laz-700
page: Windows proof: merge the port and push it, no release claims yet
hours: -
---
# Windows proof: merge the port and push it, no release claims yet

## What it is
Main loop: merge --no-ff, the full test suite on the PC, the state-restore test 3 times, push main, CI green.

## Exit gate
The W4 gate in the plan. Plan: `docs/plans/phase-7.md` line 276.

## Evidence
- 2026-11-17 13:43: p7-int merged into local main --no-ff (361fef5); bundles of main and p7-docs on the PC
  (D:\lazpy\p7\w4); fresh-tree build and tests started.
- 2026-11-17 13:46 PC gates PASS on a fresh clone of main 361fef5: fetch --headers verified; make rc 0; test-host
  "307983 checks, 0 failed"; test-version ok; fast pytest 246 passed, 5 skipped, skips_check "251 tests, 5 skipped,
  0 problems (list fast)"; test_state_boot alone 3/3 passed (19-20 s each, free RAM 7.5 GB, one copy); clone_check
  --until host on the p7-docs bundle rc 0 ("307983 checks, 0 failed", fetch as --headers, logged). NOT RUN on the PC:
  make check (no clang; CI runs it). Logs runs/p7/w4/.
- 2026-11-17 13:47 main pushed (a551d5f..33378db), main only. CI: test 44077243102, test-windows 44077243228,
  macos-live 44077243684, watched.
- 2026-11-17 13:58 CI on 33378db: test (macOS, incl. make -B -n and vtool) green; macos-live green; test-windows RED
  at `make check`: clang's analyzer on host/azhost_main.c:512 (mingw-w64's _assert is not noreturn, so the analyzer
  walks past assert(p != NULL)). Fix: host/plat/analyze_assert.h forced into the Windows analysis only; the check
  now analyses every file before failing. make -n and a gcc parse with the header OK on the PC.
- 2026-11-17 14:16 CI on 9026e0b: test and macos-live green; test-windows: all files clean except host/frame.c:121
  (core.NullPointerArithm, a newer clang checker than Apple's; it cannot see that azh_fail returns an error). Fix: a
  `px == NULL` guard after frame_pixels in azh_frame_write (behaviour unchanged; one macOS-visible hunk, so W1a's
  macOS list gains it). PC: make rc 0, test-host "307983 checks, 0 failed".
- 2026-11-17 14:22 CI on 660d44b: make check (Windows clang analysis) now clean; test-host 47 FAIL, all profile cases:
  the runner's core.autocrlf=true checks the .expect files out as CRLF (the PC's bundle clones had no autocrlf). Fix:
  .gitattributes `* text=auto eol=lf`, the 3 CRLF inputs -text (1442a84; nothing renormalizes). PC, clones with
  core.autocrlf=true: 361fef5 test-host FAIL (reproduced), 1442a84 "307983 checks, 0 failed" with 3 CRLF files.
- 2026-11-17 14:35 W4 gate PASS on 49c81ed: test (macos-15, incl. make -B -n and vtool) green; test-windows green (make
  check clean, test-host "307983 checks, 0 failed", fast 246 passed 5 skipped, skips_check 0 problems); macos-live
  job green but its pytest step (the outcome that counts, R2-S8) FAILED: "2 failed, 292 passed, 13 skipped", the same
  2 on all three pushes, both CI-environment: test_state_boot timing 4.46 s > 2.5 s on the VM (3/3 on the PC), and
  test_k_threads needs testapp.elf (CI fetches only the .3dsx). So section 7.6's fallback macOS sentence goes in
  STATUS at W7. Done.

## Pointers
- Plan section: `docs/plans/phase-7.md:276`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
None yet; planned in phase-7 revision 2.
