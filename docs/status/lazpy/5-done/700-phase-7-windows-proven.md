---
id: laz-700
title: lazpy
order: 700
kind: phase
page: Windows: the native Windows port proven, reviewed and released
hours: phase-7
---
# Phase 7: the Windows port, proven

## What it is
Guy, 2026-11-17 (by 11:08), verbatim: "update the repo so it says windows is ot proven and its a WIP. / and move forward so
its windows proven". The native Windows port (branch port-win on the PC, D:\lazpy\src\lazpy-win, 7471be0, cut on
0537394 = f93c755 since G8e) already runs internal Gen3D and 3DP jobs. This phase turns it into a supported platform:
rebased onto main, reviewed, gated on the PC, with a Windows CI job and a Windows release download.

## Exit gate
docs/plans/phase-7.md (to be written: opus plan, two review loops). Draft gate: port-win merged into main; the full
test suite with `LAZ_REQUIRE_EMULATOR=1` passes on the PC from a fresh clone; a Windows CI job is green; a
release-legal audit is clean; a release with a Windows asset is published on Guy's word.

## Evidence
- 2026-11-18 01:52 done: v1.1.0 with the Windows x64 core published 2026-11-18 00:07 on Guy's word ("Yes, publish
  after the jobs"); fresh clone from GitHub passes the full suite on the PC (item 714); test-windows green on cec470d;
  release-legal audit shippable (item 712). Steps 701-714 in 5-done.

## Pointers
- The port so far: toolkit docs/pc-worker/NATIVE-PLAN-v3.md, docs/pc-worker/lanes/WB.md, docs/pc-worker/HANDOFF.md
  (lanes B5-B8 were the open list); item 500's notes from 2026-11-13 21:28 on.
- Commit map for the rebase: `docs/commit-map-g8e.tsv`.

## Lessons and notes
- 2026-11-17 11:09: README and STATUS say "Windows: work in progress, not proven" (Guy's ask).
- 2026-11-17 11:13: port-win rebased on the PC onto main a551d5f as port-win-v1 (1c8650f, 22 commits, clean; port-win
  kept); bundle runs/p7/port-win-v1.bundle (sha256 4669d8a4…) fetched to the Mac as local branch port-win-v1. Opus
  plan agent writing docs/plans/phase-7.md (notes in runs/p7/notes.md).
- 2026-11-17 11:14: Guy, verbatim: "moev forward doesnt include push to github. but this time you can push to github". So
  phase 7 may push reviewed, gated work to GitHub (main, the tag); publishing the release still waits for his word.
