---
id: laz-410
title: lazpy
order: 410
kind: step
parent: laz-400
page: Docs: README, status, usage and API
hours: -
---
# Step H: docs: README, status, usage and API

## What it is
README with honest status and measured numbers, STATUS.md, USING.md, HOST-API.md, NOTICES.md, examples.

## Exit gate
The gate in `docs/PLAN.md` line 317 ("Phase H"), run headless on this Mac with a pass/fail answer.

## Evidence
none yet

## Pointers
- Plan section: `docs/PLAN.md:317`
- Phase plan: `docs/plans/phase-4.md` (index), `docs/plans/phase-h.md` (the builder's brief, revision 2)
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- 2026-11-13 03:18, main loop: launched per phase-4.md section 2 after Phase 3 (29cb592 before G8b), G8b (896c2fe) and
  the downloads (item 400's notes). Launch defaults: Q1 remove the stock fetch (P17), G2 (a), the consult GREEN.
  H builder af156d29564cfc9ce (sonnet), launched 03:19 in ../libazahar-py-h (step-h at 896c2fe).
- H1 done 03:29 (af156d29564cfc9ce), committed on step-h as 4ce7181 by the main loop with the map lines (code.md,
  tools.md, runners.md); needle 0, no /Users/, no hex runs, no removed material. Gates: 1 docs_check
  --allow-missing NOTICES.md PASS on all eight checks (without the flag only NOTICES.md's link fails, step I's file);
  --plant-red nine FAIL lines, one per plant, rc 1. 2 on our core: quickstart, pool_shots, memory_watch ok; on the
  stock core: quickstart ok, memory_watch exits 3 "needs our core", pool_shots ok (load 18-26, no timings). 3
  clone_check.sh sh -n clean, --dry-run six steps, nothing cloned. README numbers: speed-table-e.md rows 27, 29, 36,
  38 and spike-2-real-scene.md rows 32, 34, 35, each with its load; no game named.
  Departures: docs_check's Source refs take comma lists (file:27,3) so the date line counts; README steps call
  `sh tools/fetch.sh` (the file is mode 100644); poll-exact movies are "not tested" (no gate ran lazpy_movie_play).
  For I's review (P17 not in the code yet at 896c2fe): _paths.py:34-36 and azhost_main.c:13 default to the stock
  path; LAZ_STOCK_CORE absent; fetch.sh has no part flags or LAZ_RELEASE_BASE; core/PIN-nokeys, core/OPENSSL.md and
  NOTICES.md missing. Proposed (not made): a hint in the missing-core BootError ("run tools/fetch.sh --lazpy-core or
  set LAZ_CORE"); stale "until D" comments in host/azhost.h 13, 86, 90, 91; fetch.sh executable.
  Lessons: a "number within 2 lines of its source" rule needs a second line for a file-header date; a plant that
  adds an image must point at a real file or the links check fails too; the first-paragraph phrase must stay on one
  line; the README block is compared with examples/quickstart.py, which deletes its own runs/quickstart first.
