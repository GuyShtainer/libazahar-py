---
id: laz-834
title: lazpy
order: 834
kind: step
parent: laz-830
page: Phase C: the guest clock no longer depends on the host's time zone
hours: -
---
# The guest clock no longer depends on the host's time zone

## What it is
Found by the macOS live run on pushed main (run 44462572191): the tick seed did not move the guest clock there.
Azahar's shared page measures the fixed start time against 2000-01-01 00:00 in the host's local time zone
(`std::mktime`, `src/core/hle/kernel/shared_page.cpp`, `GetSystemTimeSince2000`). Our start time, 946681277, is
1999-12-31 23:01:17 UTC: on a UTC host it is before that midnight, so the guest clock reads 0 at boot and the seed
cannot move it; on the PC (UTC+2) it is after. So one seed gave a different guest clock on machines in different
time zones. Fix: the worker runs with `TZ=UTC0`, and the start time is 946688477 (the clock Guy's UTC+2 machines
saw in winter, now on every machine).

## Exit gate
`test_determinism.py` passes on the PC under the PC's own zone and under `TZ=GMT0` (the macOS runner's case), and a
new test shows two runs under different parent time zones give the same records. The full PC gate stays green.

## Evidence
none yet

## Pointers
- Plan section: `docs/plans/phase-8.md:180` (phase C); found in C6 step 5 (the macOS CI read)
- Review: none yet

## Lessons and notes
- 2026-11-20 02:15, the PC: `TZ=GMT0` makes `test_two_tick_seeds_differ` fail exactly as on the macOS runner (t moved
  by 0); the PC's own zone (+0200) passes. Cause confirmed.
- A night decision (Guy asleep): built in lane p8-tz (runs/p8/wt/tz), not merged until he says so.
- `azhost` (the C command line) does not set TZ itself: whoever runs it directly sets `TZ=UTC0` to match.
