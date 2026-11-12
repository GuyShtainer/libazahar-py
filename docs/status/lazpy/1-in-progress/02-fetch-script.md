---
id: laz-02
title: lazpy
order: 02
kind: phase
page: A script that downloads the Azahar core, MoltenVK and the headers, checked by sha256
hours: build ~ fetch script
---
# The download script for the core, MoltenVK and headers

## What it is
`tools/` (fetch.sh): downloads the Azahar libretro core and MoltenVK (pinned URLs and sha256 from spike 1) and the
libretro and Vulkan headers into ignored folders, so a fresh clone can build the prototype. The README promises it.
Started before the plan as a reversible default (Guy 2026-11-12 allowed 6 cheap agents); the plan may move or reshape it.

## Exit gate
On a clean temp copy, `tools/` (fetch.sh) fetches everything, verifies every sha256, fails loudly on a mismatch, and a
second run downloads nothing.

## Evidence
none yet

## Pointers
- URLs and sha256: `docs/research/spike-1-headless-core.md` (Part 2)
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
