---
id: laz-812
title: lazpy
order: 812
kind: step
parent: laz-810
page: Phase A: 100 boots and 300 state loads, watching memory and leftovers
hours: -
---
# A2: soak and reset cost

## What it is
100 boot-and-close cycles and 300 load_state calls on the PC, measuring growth and leftovers.

## Exit gate
Numbers in runs/p8/a2/ and a build-or-drop line for a B fix step and C4.

## Evidence
2026-11-19 01:14: 100 boots clean; 300 loads: RSS flat, worker handles +2 per load (415 -> 1023), so fix step B9 is opened;
median load 1183 ms, file I/O under 1 %, so C4 is dropped (runs/p8/a/decisions.md, outside git).

## Pointers
- Plan section: `docs/plans/phase-8.md:149`
- Review: `docs/reviews/phase-8-plan-review.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.

- Guy, 2026-11-18 ~21:00, verbatim: "you have my green light. go". Q1-Q5 not answered: the plan's recommended
answers are in force (Q1 yes, Q3 yes, Q4 yes to D after v1.2.0 / two releases / the hosted bound / the MSYS2 Mesa
download, Q5 probe now) until Guy says otherwise.
- 2026-11-18 22:56-23:00, one copy on a busy PC: 100 boot/close cycles clean. Parent RSS 17.7 -> 17.8 MB, handles 162
  flat, 1 slot lock file (by design), 49 workdir files each, no child alive after close, GPU memory flat. The 300 loads
  were cut at load 50 by a PC crash (two of our jobs at once: this soak plus the A5 unpack). In those 50 loads, worker
  handles went 417 -> 523 (about 2 per load) and RSS 990 -> 998 MB; each load took 1.6-2.2 s (drain about 0.85 s,
  unserialize about 1.3 s, file read 0.2 ms). Loads rerun alone 2026-11-19.
