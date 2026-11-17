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

## Pointers
- Plan section: `docs/plans/phase-7.md:276`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
None yet; planned in phase-7 revision 2.
