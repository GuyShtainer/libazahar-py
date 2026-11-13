---
id: laz-500
title: lazpy
order: 500
kind: phase
page: Asks from the projects that use it (Gen3D, 3DPlatinum)
hours: phase-5
---
# Phase 5: asks from the projects that use libazahar-py

## What it is
Since 2026-11-13 Gen3D and 3DPlatinum use only libazahar-py for their automated emulator runs (Guy: "they can and
need to use only it"). Their asks land here as steps, each with its repro, tests and docs. Work that changes the core
goes on a branch and merges after v0.1.0 is tagged, unless Guy rules otherwise.

## Exit gate
Open-ended: each step has its own gate; the phase closes when Guy closes it.

## Evidence
none yet

## Pointers
- Steps: `docs/status/lazpy/5-done/510-step-k-core-rev-2.md`, `docs/status/lazpy/5-done/520-step-l-stencil-readback.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- 2026-11-13 09:40, 3DPlatinum (3ds-toolkit-f4), verbatim asks: "A4 (wanted): expose the 3DS tick seed
  `init_ticks_override` as a core option. Why: Platinum's old windowed profile pins init_ticks_type=1 (Fixed) and
  init_ticks_override=1000 ...; our core leaves the override at 0 (core/patches/0002-lazpy-options.patch:136), so the
  guest's tick counter starts from another value and count lines may differ. Repro: boot 3DP.3dsx with
  citra_init_ticks_type=Fixed on both routes and compare the hwlog count lines. ... We may also ask about lle_applets
  later" and "A1 (low priority): read pc, lr and sp of each guest thread between batches on our core, to replace a
  gdb-based debug aid (Platinum tools/emu/boot/where.py halts and reads each thread over gdb). Repro: boot 3DP.3dsx on
  an empty SD for 600 frames, then compare with what where.py gets on the windowed route."
- 2026-11-13 09:32, 3DPlatinum: its sound lane will need an audio route (audio output is not built); an ask with a
  repro follows when that lane nears.
