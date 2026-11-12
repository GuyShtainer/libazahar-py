---
id: laz-06
title: lazpy
order: 06
kind: phase
page: Check whether the existing Python libretro host (libretro.py) can run the Azahar core headless
hours: build ~ libretro.py
---
# Can libretro.py host the Azahar core?

## What it is
libretro.py (MIT, Python) is a libretro frontend made for testing cores. If it hosts Azahar's Vulkan core headless
on macOS, the plan can reuse it instead of growing our own host. A short probe for the plan (laz-10), weighed against
Guy's speed rule (the per-frame path stays native).

## Exit gate
`docs/research/` (libretro-py-probe.md) answers: Vulkan HW core support yes/no (source and a real try), memory maps,
per-frame Python overhead measured or estimated, and a verdict.

## Evidence
2026-11-12, sonnet agent af4e0b90795498306: verdict "borrow parts, not usable as the host". libretro.py v0.12.0 has no
Vulkan context (`libretro/api/video/context.py` VULKAN note) and its negotiation-interface handler is
`return False  # TODO` (`drivers/environment/composite.py`); both spot-checked by the main loop. Real try: Vulkan
load fails ("Failed to load game"); Software boots Gen3D at 20.3 fps. Loop cost about 90 us per frame on a trivial
core. Report: `docs/research/libretro-py-probe.md`. Its line that Azahar never sends SET_MEMORY_MAPS contradicts
the source reading in prior-art.md and is unverified; spike 2 tests it.

## Pointers
- Prior art: `docs/research/prior-art.md`
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- 2026-11-12 probe done, details in `docs/research/libretro-py-probe.md`. Verdict: borrow parts, not usable as host.
- libretro.py v0.12.0 has no Vulkan: SET_HW_RENDER Vulkan is refused (`api/video/context.py:68-74`), the negotiation
  interface is a `return False` TODO (`drivers/environment/composite.py:1293`). Real try: Vulkan option gives "Failed to load game".
- Software renderer works headless through it (Gen3D boots, 20 fps, slower than fe2 software). Python loop cost 90 us/frame
  (11k run/s on its sample core), upper bound. SET_MEMORY_MAPS is implemented but Azahar never sends it.
