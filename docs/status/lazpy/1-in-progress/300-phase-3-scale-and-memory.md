---
id: laz-300
title: lazpy
order: 300
kind: phase
page: Phase 3, scale and memory: many copies, our core passes the full tests, memory reads
hours: phase-3
---
# Phase 3, scale and memory: many copies, our core passes the full tests, memory reads

## What it is
The instance pool and speed table, our built core gated with the full test batch, then memory reads and writes. Steps laz-310, laz-320, laz-330 (PLAN.md: E, F2, G).

## Exit gate
Every step's gate passes (each step file names its PLAN.md line). Before any step is built: the phase plan
(`docs/plans/`), opus review 1, revision, opus review 2, revision (Guy's rule: two loops per phase).

## Evidence
none yet

## Pointers
- Plan section: `docs/PLAN.md` section 3
- Phase plan: `docs/plans/phase-3.md` (index), `phase-e.md`, `phase-f2.md`, `phase-g.md`
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- Guy 2026-11-12 chose four phases over ten small ones ("4 phases (Recommended)"), each with one plan and two
  review loops; the ten PLAN.md phases became steps.
- Plan revision 0 (aed5ccfac0370b719, opus, 19:16-19:51). Hours: E 1.1, F2 0.85, G 0.9, review loops 0.5, phase
  3.35 (PLAN.md 2.75; the 0.6 over: G's ABI 3 bump for the watch list, F2 must make our core's option profile
  apply, E's live slot gate). Order: E1 and F2 together; timed runs never overlap (core build, F2-2, E2, G2); G
  after F2 merges, on main plus E1; merge E then G. Proposed departures: P7 error -11 AZH_E_UNMAPPED and the
  public GuestMemoryError(.addr, .length); P8 our core applies core/options-lazpy.txt first (azhost
  --lazpy-profile, Python LAZ_LAZPY_PROFILE), since nothing applies it today. Interface change: azh_stats valid
  any time after open. Open: Q1 (Guy) the real-scene speed row: a Gen3D field-scene state and .3dsx for one
  local run, never committed, or skip it (plan default: skip, cap stays provisional on a light scene); Q2 (Guy)
  approve P7; Q3 (Guy) the cap rule fixed before the run: keep 3 unless 3 instances give under 1.25x the total
  of 2 or the end load is at or above 2 x cores, then 2, else 1, never above 3; Q4 (review) keep F2's stock-core
  regression run or leave it to the phase-end suite (about 30 min machine); Q5 (review) fixed 4 MiB watch area
  or a size set at open. Risks in phase-3.md section 8 (ABI 3 refuses ABI-2 state files: Gen3D's states must be
  remade; map grows to 4,890,624 bytes, sparse). The step items point at PLAN.md:289/304/310; the real lines
  are :296 (E), :311 (F2), :317 (G): fix when the items move.
- Review 1 (ab3db82a4ace714b2, opus, 19:53-20:10; docs/reviews/phase-3-review-1.md): 5 blockers, 9 should fix, 12
  nice; ready after B1-B5 and S1-S3. Q4: cut F2's stock regression to a smoke run (gate C c and f plus the
  matching pytest, about 5 min); Q5: keep the fixed 4 MiB area, Python reads its size from the layout row. Phase
  about 3.1 h after the cuts. D takes B1 (host_paths and LAZ_CORE), B2 (nice at least 10) and S7 (abi range) now.
- Guy 2026-11-12 20:5x: Q1 "Skip it (Recommended)" (no Gen3D scene; the cap stays provisional on a light scene);
  Q2 "Approve (Recommended)" (P7: AZH_E_UNMAPPED -11 and GuestMemoryError); Q3 "Allow 4 too": the speed table
  adds a 4-copy row (about 10 more minutes of machine time) and the cap rule may reach 4.
- From the Phase 4 plan (item 400's notes): our built core carries Azahar's built-in console key blob
  (ENABLE_BUILTIN_KEYBLOB ON by default); P9 rebuilds with it off plus -ffile-prefix-map, before F2, so F2 gates
  the binary that ships.
- P9 done by the main loop 21:04-21:09 (main loop's default for Guy's G1, the conservative side):
  tools/build-core.sh configures -DENABLE_BUILTIN_KEYBLOB=OFF and -ffile-prefix-map=$PWD/= for C and C++, refuses
  to go on unless CMakeCache shows OFF, and refuses to copy the dylib if any *.o.d names default_keys.h. The
  rebuild took 5 min (exit 0). Checks: CMakeCache ENABLE_BUILTIN_KEYBLOB:BOOL=OFF; 0 .o.d files name
  default_keys.h (key.cpp.o.d did before); the first 32 blob bytes of default_keys.h are not in the dylib;
  0 strings contain /Users/ (461 before); version string still -lazpy.1; 3 lazpy_ exports. F2 gates this binary.
- Revision 1 (a848bdbe41c898002, opus, 20:59-21:15; phase-3.md section 13 "Changes from review 1"): all of B1-B5,
  S1-S9, N1-N12 taken (N7 as a committed tools/hold_slot.py; S1's G wait bounded at 150 min). Hours E 1.1, F2
  0.75, G 0.85, loops 0.5: about 3.2 h, plus 0.2 main loop. Phase 2 holds H1-H7 (phase-3.md section 6). Rule T:
  every timed part, reruns included, runs alone; E2 after step-f2 merges, with main merged into E first. Q3 cap
  rule (phase-e.md section 7): start at 1; for n = 2, 3, 4 step up only if T(n) >= 1.25 x T(n-1) and end load
  < 2 x cores; a failed check on our core's rows keeps 3. F2's first check f1 "keyblob". The plan's step 0 (the
  P9 rebuild) is already done (e40e59c). For Phase 2 (should): test_state.py::test_newer_abi_refused uses the
  literal "abi=2\n"; use _abi.AZH_ABI_VERSION. For Phase 4: phase-h.md:138 (ABI-2 states still load), drop
  phase-4.md's P9 contingency (lines 138, 293), R1 holds after F2, re-read R2's size and R4's link line on the
  new build; docs items listed in the report (cap 1-4 provisional, SlotTimeout, tools/hold_slot.py, profile
  applied first, watch size from the layout).
- Review 2 (aa4b2b6826aa2442e, opus, 21:19-21:38; docs/reviews/phase-3-review-2.md): 3 blockers, 7 should fix,
  10 nice; all 26 review-1 findings fixed. B1 F2 would gate a binary that still holds ClCertA (http_c.cpp:37-38,
  2281-2289; MAIN's http_c.cpp.o.d names both headers): main-loop step 0 "P9b" (patch 0007 no default ClCertA,
  optional 0008 no key loading, LAZ_CORE_DROP in core/PIN, build.inputs, atomic install) and keyblob_findings().
  B2 lazpy_core falls back to <checkout>/build-core/, absent in worktrees: link MAIN's dylib in each step 0. B3
  E1's slot acquire in WorkerClient.spawn would make fake-worker tests take real slots: slot=None. Ready after
  revision 2 takes section 8's list; no third loop.
- Guy 2026-11-13 00:3x, on LibreSSL (Phase 4 review 1): "Switch to OpenSSL 3": the P9b rebuild links a static
  OpenSSL 3 (Homebrew openssl@3 3.6.5, /opt/homebrew/opt/openssl@3/lib/libssl.a, libcrypto.a) through
  USE_SYSTEM_OPENSSL. Main-loop default for Q6: patch 0008 (load no keys) goes in the same rebuild.
- Revision 2 launched 00:38 (ae13bb77d6994c473, fresh opus).
- P9b by the main loop (00:45-00:49, commit 5e95423; rebuild launched 00:49, pid 60994): patch 0007 (http_c.cpp: no built-in ClCertA; a missing console file is
  an error and returns), patch 0008 (key.cpp: GetKeysStream() returns an empty stream), core/PIN LAZ_CORE_DROP
  (default_keys.h, ctr-common-1-cert.h, ctr-common-1-key.h, deleted after unpack, before the patches; an entry
  not in the tree fails the build), OPENSSL_VERSION=3.6.5 and OPENSSL_ROOT. tools/build-core.sh: static
  OpenSSL via USE_SYSTEM_OPENSSL (CMakeCache must name the .a files; otool must show no SSL dylib; no LibreSSL
  string), build-core/build.inputs (sha256 of tarball, pin, script, each patch, both .a files; drop list; head;
  clean), the .o.d guard over every drop entry, an atomic install through $DYLIB.tmp. 0007 and 0008 apply with
  --fuzz 0 on a fresh 2126.2 tree after 0000-0006 with the drop files gone; the remaining references are
  under #ifdef ENABLE_BUILTIN_KEYBLOB (OFF) or file-name strings. The rebuild runs next in MAIN, detached.
- P9b rebuild 00:49-00:52, exit 0, 21,828,992 bytes (19,145,936 before). build-core/build.inputs: head 5e95423,
  clean=yes, 9 patches, the drop list, openssl=3.6.5 with both .a sha256. Checks: 3 files dropped, 9 patches ok;
  CMakeCache keyblob OFF, USE_SYSTEM_OPENSSL ON, both libraries the static .a; 0 .o.d name a drop file; otool -L
  shows no SSL dylib; 0 LibreSSL strings, "OpenSSL 3.6.5 29 Sep 2026" present; 0 /Users/ strings; -lazpy.1;
  3 lazpy_ exports; "ClCertA file missing" present, "using default" absent; 0 of the 32-byte windows of
  ctr-common-1-cert.h, ctr-common-1-key.h, default_keys.h found in the dylib (the same check on the old core
  found 5 of 5 cert and 5 of 5 key windows, 0 blob). C's checks on the new core: 10 passed. D gate: 68 passed,
  1 failed: test_state_boot 5.50 s against the 2.5 s bound, on the stock core (host_paths), under load 45 on 12
  cores (another session's devkitARM LTO build), so load, not P9b; rerun it alone on a quiet machine.
  For Phase 4: Homebrew's libcrypto.a objects are built for macOS 15.0 while the core says minos 11.0 (ld warns
  per object); OpenSSL's OPENSSLDIR/ENGINESDIR/MODULESDIR /opt/homebrew strings are in the core (not private).
  Both sent to Phase 4 revision 1 (a739c8de18f2e6992). Scratch tree deleted.
- Revision 2 (ae13bb77d6994c473, opus, 00:38-00:57; phase-3.md section 14 "Changes from review 2"): final, all
  of review 2 taken with 8 departures listed there. Hours E 1.11, F2 0.78, G 0.85, loops 0.5: 3.24 h, plus about
  0.4 main loop. Its step 0 (section 4 item 0) differs from the P9b build of 5e95423 in: externals/libressl on the
  drop list, OPENSSL_PREFIX (keg real path via cd -P) for OPENSSL_ROOT, the version read from opensslv.h and
  libcrypto.a strings, explicit OPENSSL_* cache paths, the FIND_PACKAGE_MESSAGE_DETAILS_OpenSSL guard, split
  build.inputs keys (openssl_version, openssl_prefix, openssl_*_sha256), cmake= with <repo>, the link.txt check,
  otool on the .tmp before install. The main loop aligns the script to it and rebuilds, so F2's f1 gates the
  plan's format.
- Step 0 aligned to revision 2 by the main loop: core/PIN drop list gains externals/libressl, OPENSSL_ROOT ->
  OPENSSL_PREFIX; 0007 and 0008 regenerated with the plan's notice lines, 0008 now replaces GetKeysStream's body
  (default_keys_enc count 0, was 2 in dead code); build-core.sh takes the plan's (a)-(i). --configure-only in MAIN:
  4 dropped lines, 9 patches 0 rejects, configure done; ctr_common_1 0, default_keys_enc 0, one notice per file;
  cache USE_SYSTEM_OPENSSL ON, both libraries the keg .a (/opt/homebrew/Cellar/openssl@3/3.6.5), keyblob OFF,
  FIND_PACKAGE_MESSAGE_DETAILS_OpenSSL v3.6.5; configure.log found suitable version "3.6.5". The 00:52 build had
  605 stale .o.d under build-core/build/externals/libressl; (d) removes them.
