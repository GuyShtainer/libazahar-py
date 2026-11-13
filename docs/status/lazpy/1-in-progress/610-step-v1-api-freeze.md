---
id: laz-610
title: lazpy
order: 610
kind: step
parent: laz-600
page: Freeze the public API for 1.0 and write down its file formats
hours: -
---
# API freeze for 1.0 (plan step V1)

## What it is
Freeze the public API for 1.0: review every public name, default and file format, apply the few changes worth making now, write down the option-profile format and the azhost exit codes.

## Exit gate
`docs/plans/phase-v1.md` section 3, V1: make, make test-host, the fast pytest and the changed tests pass on the branch.

## Evidence
none yet

## Pointers
- Plan: `docs/plans/phase-v1.md` section 3
- Reviews: `docs/reviews/phase-v1-review-1.md`, `docs/reviews/phase-v1-review-2.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- 2026-11-13 11:25: the review is saved (`docs/reviews/api-freeze-1.0.md`): 13 changes before 1.0, three of them
  breaking for callers (keyword-only `run` options, `run_until`'s names, `Path` returns), none hitting Gen3D or
  3DPlatinum by the reviewer's check. All 13 taken; item 13's Touch/Circle range check skipped (optional).
- 2026-11-13 11:28: briefs `docs/plans/v1-briefs.md`; two sonnet agents in the worktree on separate files (host:
  items 1 C side, 2, 3, 12; python: items 1 Python side, 4-10, 13). Item 11 (the `LAZPY_ROOT` alias) is the main
  loop's. 3DPlatinum left the worktree first (its word came by 11:28).
- 2026-11-13 by 12:00: both agents done; branch commit 64f5d18 holds all 13 changes and the USING.md text (the promise
  paragraph before section 1, exit codes and summary keys in section 3, new 4a, the errors table in 8, the profile
  format in 14, section 20 API reference). Gates on the branch: make check; test-host 307918 checks, 0 failed; fast
  pytest 195 passed, 47 deselected; the python agent's slow tier (api, c_checks, memory_live, state, pool_live,
  live_errors) 32 passed, 2 skipped; host agent's slow test_profile_format 5 passed, 1 skipped (exit 7 needs
  LAZ_STOCK_CORE). The layout test now expects 151 fields (the AZH_EXIT_STATE row). Next: the opus review of
  64f5d18 (agent a04d832ad11619ae6), its fixes, then V0b.

- 2026-11-13 12:12: the diff review is saved (`docs/reviews/api-freeze-1.0-diff-review.md`): not ready; must-fix 1
  (the C and Python profile parsers differ on invalid UTF-8, NUL and a BOM on line 2) and 2 (the exit table's seed
  and `--save` rows), 9 should-fix, nits. Decisions D-a..D-g and two fix briefs: `docs/plans/v1-fix-briefs.md`;
  agents hostfix a444f6a4e5d19a299 and pyfix aa0abb629238080e0 in the worktree by 12:15. Review 11's plan line
  (phase-v1.md section 1, the environment-variable promise) is fixed on main. The main loop edits USING.md after.
