---
id: laz-520
title: lazpy
order: 520
kind: step
parent: laz-500
page: Depth-stencil readback gives wrong stencil values on first use (3DPlatinum's ask)
hours: -
---
# Step L: D24S8 stencil readback on the Vulkan route (3DPlatinum's A3 rev b)

## What it is
On our core (Vulkan via MoltenVK), copying a D24S8 depth-stencil buffer back to guest memory returns exact depth but
wrong stencil values on first use, different from launch to launch. Azahar's windowed 2125.1.2 passes the same
checks. It blocks 3DPlatinum's test-migration gate, and a renderer result that changes between runs undercuts 1.0's
"exact repeats" claim, so it is weighed as a 1.0 item.

## Exit gate
Our own test-app repro (a stencil-writing quad read back through a GX copy) gives the exact counts on 10 launches in
a row on our core, and 3DPlatinum's self-test passes on the final core. The plan line is written once the cause is
known (the investigation's report).

## Evidence
none yet

## Pointers
- Ask verbatim: the notes below.
- Investigation notes (scratchpad, not tracked) until the report is saved under docs/research/.

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- 2026-11-13 by 11:51, 3DPlatinum (3ds-toolkit-f4), verbatim: "ask A3 rev b (it now blocks our test-migration exit
  gate). On lazpy.1 (2126.2, Vulkan via MoltenVK, resolution 1), reading back a D24S8 depth-stencil buffer to guest
  memory with a GX TextureCopy returns the right depth but the wrong stencil, and the wrong values change between
  launches with identical guest input. A self-test clears the buffer to depth fffffe and stencil 00, draws one opaque
  quad covering 100x80 px that writes stencil 0x80, then copies the buffer back. - One launch: 8000 px with stencil
  0x80, clear stencil 00 (correct). - Two other launches: 480 px (bbox 40..127 x 40..109) and 240 px (bbox 48..79 x
  80..109), with clear stencil ff. - In all three the depth codes are exact (4001ff inside, fffffe at the clear). A
  second app's check reads stencil ff where 0x81 is written and 0x88 where 0x89 is written. Later readbacks in the
  same process pass. Windowed Azahar 2125.1.2 (also Vulkan, same options) passed every one of these checks exactly.
  ... Questions: is the stencil aspect of a D24S8 surface kept through the memory fill (clear) and the DepthToBuffer
  download on MoltenVK? Is it a first-use or ordering issue (barrier, StencilView)? Does citra_graphics_api=Software
  (if the core takes it) give 8000 / 00 as a diagnostic? This joins the earlier readback note (the edge-marked count
  jitter, 28 px in 1.53 M), likely the same path."
- Their repro is in their tree (make targets that write there); we never write there, so our own test app gets a
  repro. Told them the core takes `citra_graphics_api=Software` (the host handles software frames) as a diagnostic.
