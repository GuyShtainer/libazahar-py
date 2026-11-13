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
  `init_ticks_override` as a core option. Why: the sibling project's old windowed profile pins init_ticks_type=1 (Fixed) and
  init_ticks_override=1000 ...; our core leaves the override at 0 (core/patches/0002-lazpy-options.patch:136), so the
  guest's tick counter starts from another value and count lines may differ. Repro: boot 3DP.3dsx with
  citra_init_ticks_type=Fixed on both routes and compare the hwlog count lines. ... We may also ask about lle_applets
  later" and "A1 (low priority): read pc, lr and sp of each guest thread between batches on our core, to replace a
  gdb-based debug aid (the sibling project's tools/emu/boot/where.py halts and reads each thread over gdb). Repro: boot 3DP.3dsx on
  an empty SD for 600 frames, then compare with what where.py gets on the windowed route."
- 2026-11-13 09:32, 3DPlatinum: its sound lane will need an audio route (audio output is not built); an ask with a
  repro follows when that lane nears.
- 2026-11-13 13:47, the PC worker session (3ds-toolkit-11) asked whether we accept a Linux port in principle: about 200
  lines in `#ifdef __linux__` / `sys.platform` branches, the Mac build unchanged, plus `LAZ_VK_DEVICE` and a bare
  `libvulkan.so.1` loader name. The plan is in the toolkit's docs/pc-worker/GPU-PLAN-v2.md section 2.1. Answered yes,
  on conditions: it merges after v1.0.0 as 1.1.0, rebased only after our push; its core uses core/PIN-nokeys; the
  Darwin Makefile block stays verbatim; device choice unchanged on a one-GPU Mac; `DEFAULT_CAP` stays (the PC sets
  `LAZ_MAX_INSTANCES`); no core/ or build-core.sh change on main before v1.0.0; no Linux release asset without
  Guy and the legal audit; our own review and Mac gates before the merge; USING.md wording is ours.
- 2026-11-13 14:12, the PC worker's reply: the 8 conditions are binding in its final plan (toolkit
  docs/pc-worker/GPU-PLAN-v3.md section 8). No GPU-preference logic, only an index override (unset = the first
  device, as today). Its texts for us, verbatim, for the 1.1.0 merge:
  1. USING section 15 row: `| LAZ_VK_DEVICE | which Vulkan device the host uses: its index in the loader's list,
     from 0 | unset: the first device (as before) | host |`. Same name in tests/python's env list. Out of range or
     not a number = AZH_E_VULKAN at boot, message "LAZ_VK_DEVICE=<v>: <n> devices".
  2. CI: a second job `fast-linux`, runs-on ubuntu-24.04, same matrix, `sudo apt-get install -y zlib1g-dev
     libssl-dev`, then the same steps as `fast` minus `make check` (Darwin-only); its name says it runs no emulator.
  It waits for our "v1.0.0 is out" before any rebase; the bundle, its reviewed handover note and logs come after.
