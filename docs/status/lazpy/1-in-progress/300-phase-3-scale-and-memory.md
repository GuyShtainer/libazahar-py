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
