---
id: laz-300
title: lazpy
order: 300
kind: phase
page: Phase 3, scale and memory: many copies, our core passes the full tests, memory reads
hours: phase-3
---
# Phase 3, scale and memory: many copies, our core passes the full tests, memory reads

## What it is
The instance pool and speed table, our built core gated with the full test batch, then memory reads and writes. Steps laz-310, laz-320, laz-330 (PLAN.md: E, F2, G).

## Exit gate
Every step's gate passes (each step file names its PLAN.md line). Before any step is built: the phase plan
(`docs/plans/`), opus review 1, revision, opus review 2, revision (Guy's rule: two loops per phase).

## Evidence
none yet

## Pointers
- Plan section: `docs/PLAN.md` section 3
- Phase plan: `docs/plans/phase-3.md` (index), `phase-e.md`, `phase-f2.md`, `phase-g.md`
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- Guy 2026-11-12 chose four phases over ten small ones ("4 phases (Recommended)"), each with one plan and two
  review loops; the ten PLAN.md phases became steps.
- Plan revision 0 (aed5ccfac0370b719, opus, 19:16-19:51). Hours: E 1.1, F2 0.85, G 0.9, review loops 0.5, phase
  3.35 (PLAN.md 2.75; the 0.6 over: G's ABI 3 bump for the watch list, F2 must make our core's option profile
  apply, E's live slot gate). Order: E1 and F2 together; timed runs never overlap (core build, F2-2, E2, G2); G
  after F2 merges, on main plus E1; merge E then G. Proposed departures: P7 error -11 AZH_E_UNMAPPED and the
  public GuestMemoryError(.addr, .length); P8 our core applies core/options-lazpy.txt first (azhost
  --lazpy-profile, Python LAZ_LAZPY_PROFILE), since nothing applies it today. Interface change: azh_stats valid
  any time after open. Open: Q1 (Guy) the real-scene speed row: a Gen3D field-scene state and .3dsx for one
  local run, never committed, or skip it (plan default: skip, cap stays provisional on a light scene); Q2 (Guy)
  approve P7; Q3 (Guy) the cap rule fixed before the run: keep 3 unless 3 instances give under 1.25x the total
  of 2 or the end load is at or above 2 x cores, then 2, else 1, never above 3; Q4 (review) keep F2's stock-core
  regression run or leave it to the phase-end suite (about 30 min machine); Q5 (review) fixed 4 MiB watch area
  or a size set at open. Risks in phase-3.md section 8 (ABI 3 refuses ABI-2 state files: Gen3D's states must be
  remade; map grows to 4,890,624 bytes, sparse). The step items point at PLAN.md:289/304/310; the real lines
  are :296 (E), :311 (F2), :317 (G): fix when the items move.
- Review 1 (ab3db82a4ace714b2, opus, 19:53-20:10; docs/reviews/phase-3-review-1.md): 5 blockers, 9 should fix, 12
  nice; ready after B1-B5 and S1-S3. Q4: cut F2's stock regression to a smoke run (gate C c and f plus the
  matching pytest, about 5 min); Q5: keep the fixed 4 MiB area, Python reads its size from the layout row. Phase
  about 3.1 h after the cuts. D takes B1 (host_paths and LAZ_CORE), B2 (nice at least 10) and S7 (abi range) now.
- Guy 2026-11-12 20:5x: Q1 "Skip it (Recommended)" (no Gen3D scene; the cap stays provisional on a light scene);
  Q2 "Approve (Recommended)" (P7: AZH_E_UNMAPPED -11 and GuestMemoryError); Q3 "Allow 4 too": the speed table
  adds a 4-copy row (about 10 more minutes of machine time) and the cap rule may reach 4.
- From the Phase 4 plan (item 400's notes): our built core carries Azahar's built-in console key blob
  (ENABLE_BUILTIN_KEYBLOB ON by default); P9 rebuilds with it off plus -ffile-prefix-map, before F2, so F2 gates
  the binary that ships.
- P9 done by the main loop 21:04-21:09 (main loop's default for Guy's G1, the conservative side):
  tools/build-core.sh configures -DENABLE_BUILTIN_KEYBLOB=OFF and -ffile-prefix-map=$PWD/= for C and C++, refuses
  to go on unless CMakeCache shows OFF, and refuses to copy the dylib if any *.o.d names default_keys.h. The
  rebuild took 5 min (exit 0). Checks: CMakeCache ENABLE_BUILTIN_KEYBLOB:BOOL=OFF; 0 .o.d files name
  default_keys.h (key.cpp.o.d did before); the first 32 blob bytes of default_keys.h are not in the dylib;
  0 strings contain /Users/ (461 before); version string still -lazpy.1; 3 lazpy_ exports. F2 gates this binary.
- Revision 1 (a848bdbe41c898002, opus, 20:59-21:15; phase-3.md section 13 "Changes from review 1"): all of B1-B5,
  S1-S9, N1-N12 taken (N7 as a committed tools/hold_slot.py; S1's G wait bounded at 150 min). Hours E 1.1, F2
  0.75, G 0.85, loops 0.5: about 3.2 h, plus 0.2 main loop. Phase 2 holds H1-H7 (phase-3.md section 6). Rule T:
  every timed part, reruns included, runs alone; E2 after step-f2 merges, with main merged into E first. Q3 cap
  rule (phase-e.md section 7): start at 1; for n = 2, 3, 4 step up only if T(n) >= 1.25 x T(n-1) and end load
  < 2 x cores; a failed check on our core's rows keeps 3. F2's first check f1 "keyblob". The plan's step 0 (the
  P9 rebuild) is already done (e40e59c). For Phase 2 (should): test_state.py::test_newer_abi_refused uses the
  literal "abi=2\n"; use _abi.AZH_ABI_VERSION. For Phase 4: phase-h.md:138 (ABI-2 states still load), drop
  phase-4.md's P9 contingency (lines 138, 293), R1 holds after F2, re-read R2's size and R4's link line on the
  new build; docs items listed in the report (cap 1-4 provisional, SlotTimeout, tools/hold_slot.py, profile
  applied first, watch size from the layout).
