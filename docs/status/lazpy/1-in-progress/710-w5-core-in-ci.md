---
id: laz-710
title: lazpy
order: 710
kind: step
parent: laz-700
page: Windows proof: build the Windows core in CI and check it on the PC
hours: -
---
# Windows proof: build the Windows core in CI and check it on the PC

## What it is
Main loop: dispatch core-win64.yml, download, sha match, needle scan, one smoke boot on the PC.

## Exit gate
The W5 gate in the plan. Plan: `docs/plans/phase-7.md` line 295.

## Evidence
- 2026-11-17 14:35 core-win64.yml dispatched on main 49c81ed: run 44084612822 (watch log runs/p7/w5/watch.txt).
- 2026-11-17 15:00 run 44084612822: build job FAILED at the gate_f2 step: "FAIL deps deps: 0 dependency files, want
  at least 1000" (droplist cmake, fresh, window hits=0, pe machine, imports n=10 all PASS; core built). Cause: mingw
  objects are .obj, so CMake's depfiles are *.obj.d; three Windows paths counted only *.o.d (gate_f2_pe deps_scan
  loud; mknotices dep_paths and build-core-win64.sh's drop-list grep silent). Load test, leak check, attest skipped.
- 2026-11-17 15:02 Fixed on main (the three paths take .obj.d too; the Mac-only gate_f2.py and build-core.sh untouched).
  PC: gate_f2_pe --plant-red rc 0 "all planted reds fail as expected" (fixture now half .obj.d); mknotices dep_paths
  reads a .obj.d. Lesson: a CMake mingw build's depfiles are *.obj.d. Rerun next.
- 2026-11-17 15:30 rerun 44088845869 (main 015fe3f): the gate_f2 step now passes (the .obj.d fix held); the build job
  FAILED one step later, "mingw-w64 runtime source": "E: Version '13.2.0-6ubuntu1' for 'gcc-13-source' was not found".
  26.04 still ships the mingw gcc built from gcc-13 13.2.0-6ubuntu1 (Built-Using), which the archive has dropped: the
  P7-R3-6 check failing closed as designed.
- 2026-11-17 15:36 Fix: apt-get download stays first; else the same version's source package (gcc-13 13.2.0-6ubuntu1:
  .dsc, .debian.tar.xz, .orig.tar.gz) from Launchpad's API, each file checked against Launchpad's size + sha256 and the
  .dsc's Checksums-Sha256, the .dsc's Version checked; anything else exits 1. The fetch code ran on the PC: rc 0, 3
  files; a made-up version rc 1 "launchpad has no gcc-13 13.2.0-6ubuntu99". bash -n and the python parse OK.
- 2026-11-17 15:58 rerun 44094377884 (main 7b861d8): the Launchpad fallback held (3 files verified, runtime-source tar
  105 MB); the same step then FAILED: the licence loop's glob mingw-w64_*.orig.tar.* also matched the new upstream
  signature mingw-w64_13.0.0.orig.tar.bz2.asc ("tar: This does not look like a tar archive"). Fix: the loop skips
  *.asc; tested locally on a .bz2 + .asc pair, both licence files found, rc 0. Rerun next.

## Pointers
- Plan section: `docs/plans/phase-7.md:295`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
None yet; planned in phase-7 revision 2.
