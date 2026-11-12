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
2026-11-12, sonnet agent a445421c9b1810c3e, on a temp copy (`LAZPY_ROOT=<dir>`): run 1 fetched and verified all 5
downloads; run 2 printed five "have ... (sha256 ok)" lines and fetched nothing (re-run by the main loop too, exit 0);
a zeroed pin printed `SHA256 MISMATCH`, deleted the file, unpacked nothing, exit 1; fe2.c built against the fetched
`vendor/`. `shellcheck -s sh` clean. Not yet run against the repo's own `dl/` (the spike's copies stay there).

## Pointers
- URLs and sha256: `docs/research/spike-1-headless-core.md` (Part 2)
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.

- 2026-11-12 (agent): `tools/fetch.sh` written, shellcheck -s sh clean. Pins: core 2126.2 zip, MoltenVK 1.4.2 tar (both
  sha256 from spike 1); libretro.h + libretro_vulkan.h from RetroArch commit 807245dd (libretro-common/include);
  Vulkan-Headers tag v1.4.368 archive (include/ only). `LAZPY_ROOT=<dir>` overrides the root for tests; `--force` refetches.
- Tested on a temp copy only: run 1 fetched all, run 2 downloaded nothing, wrong pin gave exit 1 with the file deleted,
  fe2.c built against the fetched vendor/.
- Not clean: (1) the pinned libretro.h is newer than the copy the spike used (differs in the video-decode interface
  v3 to v4 and new GL-thread-context text; libretro_vulkan.h is byte-identical); fe2.c still builds. (2) The Vulkan-Headers
  pin is GitHub's generated tag archive; GitHub does not promise generated archives stay byte-identical, so the sha256 could
  one day mismatch with no real change (fix: re-pin). (3) Hashes of the header downloads were computed by me, not from a
  published checksum.
