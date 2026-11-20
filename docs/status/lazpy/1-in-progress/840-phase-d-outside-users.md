---
id: laz-840
title: lazpy
order: 840
kind: phase
page: Phase 8 D: outside users (prebuilt host, CI recipe, GPU-less CI), then v1.3.0
hours: phase-8d
---
# Phase 8 D: outside users, then v1.3.0

## What it is
Steps D1-D5 of the plan.

## Exit gate
As C6, plus the no-compiler clone check on both systems.

## Evidence
2026-11-20 15:59: started after v1.2.0 (Q4's recommended answer, in force). Next: the D lane briefs.
2026-11-20 16:34: the four lanes (D1-D4) merged on main: the prebuilt-host workflow and `fetch.sh --host` (pins TBD until
its first run), the macOS CI recipe and the hosted-runner state-boot rule, the Windows emulator CI workflow, the
gymnasium-style example. PC on the merged tree: fast tests 359 passed, 6 skipped; release_check self-test 15 of 15;
fetch_fallback 13 of 13; test_state live 4 passed. No workflow has run yet. Next: D5 review.
2026-11-20 16:57: D5 review (1 high, 4 medium, 12 low) and its two fix lanes merged: the macOS host stripped of build paths
before signing, a NOTICES.md in the Windows host zip, release_check 1c ties the host zip's commit to the tag, a pinned
Vulkan loader for the Windows emulator CI. PC: fast tests 359 passed, 6 skipped; release_check self-test 24 of 24;
fetch_fallback 14 of 14; doctor ok with the pinned loader; test_state live 4 passed. No workflow has run yet.
2026-11-20 20:24: pushed da90a6a; its runs: test-windows 44789137190 green; test.yml 44789218257 green; macos-live
44789222255 432 passed, 25 skipped, 0 failed, the recipe step "verdict ok"; host-bin 44789150709 green, both zips
hold the listed files and no build path, the macOS files signed ad hoc (named 1.2.0: the pins wait for a host-bin run
after the version bump); test-windows-live 44789154862 booted on lavapipe ("llvmpipe (LLVM 23.1.5, 256 bits)"),
76 passed, 1 failed: test_stencil_readback_counts, cleared pixels' depth reads back other than the clear value (the
stencil and the quad match), so not a pass; that test is deselected in that workflow only, with the reason.

## Pointers
- Plan section: `docs/plans/phase-8.md:208`
- Review: `docs/reviews/phase-8-plan-review.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.

- Guy, 2026-11-18 ~21:00, verbatim: "you have my green light. go". Q1-Q5 not answered: the plan's recommended
answers are in force (Q1 yes, Q3 yes, Q4 yes to D after v1.2.0 / two releases / the hosted bound / the MSYS2 Mesa
download, Q5 probe now) until Guy says otherwise.
