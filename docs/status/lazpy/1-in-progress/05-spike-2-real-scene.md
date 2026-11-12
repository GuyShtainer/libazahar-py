---
id: laz-05
title: lazpy
order: 05
kind: phase
page: Second test: memory reads and the real speed in a 3D game scene
hours: -
---
# Spike 2: memory reads, and the real speed on a 3D scene

## What it is
Spike 1 ran the core headless at ~50x on an idle menu, with no input and no memory reads. Spike 2 adds button input,
plays a real Gen3D game into its 3D world, measures speed against the guest's own clock (one and three instances),
and tests memory reads (the libretro memory map first, the gdb stub second). Run by the Gen3D session.

## Exit gate
Its hand-back, copied into `docs/research/` (spike-2-real-scene.md) with the verdicts and the speed table.

## Evidence
none yet

## Pointers
- Brief: in the Gen3D repo (not this one), docs/phase1-flip, file BRIEF-headless-check.md.
- Spike 1: `docs/research/spike-1-headless-core.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.

- 2026-11-12: started 15:46 by the Gen3D session, agent a8bc5d5c (sonnet), cap 60 min, in that session's scratchpad.
  At 15:54 it was told to try the libretro memory map first (see `docs/research/prior-art.md`). Its hours go in
  Gen3D's ledger. When it hands back, the Gen3D session copies the result here and moves this item.
