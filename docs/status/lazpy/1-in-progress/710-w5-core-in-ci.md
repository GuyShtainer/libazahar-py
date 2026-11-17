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
- 2026-11-17 16:26 rerun 44098242676 (main cb4db2b): the runtime-source step passes; the NOTICES step FAILED:
  "mknotices: unclassified dependency path: .../build-core/win64-fstat.h", the two-line fstat shim build-core-win64.sh
  writes and force-includes (our own file). Fix: mknotices skips exactly that path (OWN_GENERATED); a check on the Mac
  accepts it and still refuses build-core/other.h rc 1. It is the only file the script generates. Rerun next.
- 2026-11-17 16:50 rerun 44103759556 (main 14c2687): the shim passes; mknotices then stopped at "component missing
  from the table: zycore". dynarmic's x86-64 backend (Windows only) uses xbyak (top-level externals/xbyak, added before
  dynarmic), zydis and zycore. Fix: the table gains xbyak (BSD-3-Clause, xbyak/COPYRIGHT), zydis and zycore (MIT,
  their LICENSE files; libs Zydis, Zycore); every licence file exists in the pinned source. mknotices now lists all
  missing components and all unknown link libraries in one message (libressl still refused). Not in the W1b licence
  delta; all three permissive (notice only). Rerun next.
- 2026-11-17 17:16 rerun 44107891900 (main 05acacd): the three pass; mknotices lists one more: glad (Azahar turns
  ENABLE_OPENGL on for Windows, off on Apple). glad has no licence file: the table quotes glad v0.1.36's README
  (fetched with gh from Dav1dde/glad at tag v0.1.36: "Public Domain, WTFPL or CC0", GL sources Apache-2.0) and
  khrplatform.h's Khronos notice verbatim (lines 4-25); lib glad (static). Flagged for the W8 audit in item 712.
- 2026-11-17 17:37 rerun 44112733637 (main 1b660f6): the components all pass; link_libs stopped at two words of the
  core itself: "-Wl,--out-implib,libazahar_libretro.dll.a" and CMake's CMakeFiles/citra_libretro.dir/objects.a. Fix:
  exactly those two words are skipped (OWN_LINK_WORD_RE, fullmatch); a fake other.dir/objects.a and libevil.dll.a still
  fail rc 1. Ahead of the rerun, the src/ notice scan run over every src/ file of the pinned tree: only 2 Android files
  miss the table (never built for Windows). Rerun next.
- 2026-11-17 17:59 rerun 44116764453 (main 8404fa3): link libs pass; mknotices then: "OpenSSL is not both linked and
  included". gate_f2 (passed) already proves the link names /opt/lazpy/openssl-3.6.5-mingw64/lib/libssl.a and
  libcrypto.a, and Azahar builds httplib with CPPHTTPLIB_OPENSSL_SUPPORT on every platform, so the dependency-side
  test is the suspect; the job log holds no dependency paths. The message now names which half failed, the libraries
  seen and four dependency paths naming ssl. Rerun for that data.
- 2026-11-17 18:30 rerun 44121073708 (main 6000112): the data says the other half: headers under the OpenSSL prefix
  yes, linked [] of crypto, ssl. build-core-win64.sh and gate_f2 find the library paths by substring in link.all, but
  mknotices' whole-word read misses them: the words of mingw's linkLibs.rsp (likely quoted; macOS has no rsp). Fix:
  link words drop surrounding quotes (a quoted + unquoted fixture reads citra_core, crypto, ssl); the error prints the
  raw words naming ssl/crypto; the orphan-library check lists every case at once. Rerun next.
- 2026-11-17 18:52 rerun 44126760281 (main e3cc3f5): the build job PASSED (NOTICES written; DLL sha256 11d010ad16a8...).
  The leak check then failed closed without scanning: the runner's newer gh refuses to write a body with terminal escape
  sequences (the log's colours), 6 tries, "the job log could not be fetched"; the artifact was deleted as designed and
  the load test found no artifact. Not a leak: the main loop's needle scan of the full run log, 0 hits; the logs stay.
  Fix: the log is fetched with curl and the token (any gh version); the same fetch on the Mac: 271119 bytes, end marker
  and gate_f2 line present. Rerun next.

## Pointers
- Plan section: `docs/plans/phase-7.md:295`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
None yet; planned in phase-7 revision 2.
