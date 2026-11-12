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
none yet

## Pointers
- Prior art: `docs/research/prior-art.md`
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
