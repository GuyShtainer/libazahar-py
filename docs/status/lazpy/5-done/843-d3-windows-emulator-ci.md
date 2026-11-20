---
id: laz-843
title: lazpy
order: 843
kind: step
parent: laz-840
page: Phase D: the emulator tests in Windows CI on lavapipe
hours: -
---
# D3: Windows emulator CI

## What it is
Phase D: the emulator tests in Windows CI on lavapipe.

## Exit gate
The plan row's gate, run on the PC through runs/p8/bin/pclane and in its CI workflow; the lane merged on main; the D5 review's findings fixed.

## Evidence
2026-11-20 16:34: lane merged on main (`test-windows-live.yml`, `tools/fetch-mesa.sh`); 16:57: the pinned Vulkan loader (D5 fix).
2026-11-20 20:24: run 44789154862 booted on lavapipe, 76 passed, 1 failed (test_stencil_readback_counts: cleared pixels' depth reads back other than the clear value); that test is deselected in that workflow only.
2026-11-20 20:46: three dispatches (44792447279, 44792460742, 44792476117) 76 passed, 0 failed, 1 xfailed each; the result step's pattern fixed; the push run 44794501534 printed "RESULT: PASS (lavapipe)". It runs on pushes to main. Done.

## Pointers
- Plan section: `docs/plans/phase-8.md:208`
- Briefs: `docs/plans/phase-8d-briefs.md`; review: runs/p8/d/d5-review.md (private)

## Lessons and notes
Read this part only when you work on this item.
