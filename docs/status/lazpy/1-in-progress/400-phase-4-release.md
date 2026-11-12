---
id: laz-400
title: lazpy
order: 400
kind: phase
page: Phase 4, release: docs, the legal audit and the public GitHub release
hours: phase-4
---
# Phase 4, release: docs, the legal audit and the public GitHub release

## What it is
Docs with honest numbers, the release legal audit, and the release with our core and its full source. Push only on Guy's word. Steps laz-410, laz-420 (PLAN.md: H, I).

## Exit gate
Every step's gate passes (each step file names its PLAN.md line). Before any step is built: the phase plan
(`docs/plans/`), opus review 1, revision, opus review 2, revision (Guy's rule: two loops per phase).

## Evidence
none yet

## Pointers
- Plan section: `docs/PLAN.md` section 3
- Phase plan: `docs/plans/phase-4.md` (index), `phase-h.md`, `phase-i.md`
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- Guy 2026-11-12 chose four phases over ten small ones ("4 phases (Recommended)"), each with one plan and two
  review loops; the ten PLAN.md phases became steps.
- Plan revision 0 (a867570428c4f7738, opus, 20:00-20:20). Hours about 2.25 h plus Guy (PLAN.md 1.1): H 0.75, I
  0.8, main loop and the two legal agents 0.3, review loops 0.4. Urgent: our built core contains Azahar's
  built-in 3DS console AES key blob: ENABLE_BUILTIN_KEYBLOB is ON by default (CMakeLists.txt:154),
  src/core/hw/default_keys.h is read by key.cpp:302-312; ON in
  build-core/build/CMakeCache.txt; the [removed] 13,960,800 of the dylib; Azahar's unchanged
  tarball holds the same header. Breaks the policy's no-key-handling rule. P9: -DENABLE_BUILTIN_KEYBLOB=OFF and
  -ffile-prefix-map (removes 461 home-path strings) in one rebuild before F2. P10: the source asset is Azahar's
  tarball minus default_keys.h, re-packed deterministically, with SOURCE.md proving from the build's .o.d files
  that no object read it. P11 NOTICES generated from the link line in I; P12 fetch.sh pins before the push; P13 a
  draft prerelease Guy publishes. Facts: LibreSSL static (advertising clause), SPIRV-Tools Apache-2.0 (so GPLv3
  only), faad2 GPLv2+, SoundTouch LGPL-2.1, no MPL code; system archives (font, Mii, country and bad-word lists)
  carry no licence file; Apple python3 is 3.9.6 (README: Python 3.10+); no git user.email is set, so tags set the
  identity. Guy: G1 rebuild key blob off before F2; G2 source-asset option after ip-legal; G3 LibreSSL (default:
  follow ip-legal, no core binary if it says counsel); G4 core binary under GPLv3; G5 create the GitHub repo on
  GuyShtainer; G6 "push"; G7 publish the draft (v0.1.0 prerelease). Review: Q1 P10(a) vs (b); Q2 attach
  libazhost.dylib; Q3 fast tests in H2's clone; Q4 commit release notes. The ip-legal consult brief is
  phase-i.md 9.1 (no build, can run now).
- Review 1 (ab421b8f1945fcdfa, opus, 21:00-21:17; docs/reviews/phase-4-review-1.md): 7 blockers, 17 should fix, 10
  nice; not ready until B1-B7, S1-S3, S8, S11. B1: Azahar always embeds Nintendo's ClCertA (the ctr-common-1
  HTTPS client certificate and its private key, AES-encrypted under slot 0x0D) from
  src/core/hle/service/http/ctr-common-1-{cert,key}.h, included with no #ifdef at http_c.cpp:37-38, fallback at
  :2280-2288; both arrays are in the 21:09 keys-off binary; phase-4.md:270
  wrongly says it is not embedded. Fix: patch 0007 removes it (optional 0008: load no keys at all), drop list in
  core/PIN deleted after unpack, build.inputs record, in the rebuild F2 gates. B2: phase-i.md:172 named the
  local part of Guy's personal address beside @gmail; removed from the plan 21:17, but commit 15d0323 holds it, so
  history needs a rewrite before the first push (Guy: G8). B3 env -i drops DEVKITARM; B4 pytest not a dependency;
  B5 the binary has no joined 2126.2-lazpy.1 string (patch 0005 joins at run time); B6 release_check compares
  against files not yet committed in I1; B7 Azahar's 8.8.8.8 literal trips the IPv4 check. LibreSSL: incompatible
  with GPLv3 on the licence texts (COPYING:17-72 OpenSSL, :74-132 SSLeay, :127-131 "cannot ... GNU Public
  Licence"); way out: static OpenSSL 3.x (Apache-2.0) through USE_SYSTEM_OPENSSL, or hold back the core asset;
  only a lawyer can weigh upstream's practice. faad2 needs a "Code from FAAD2 is copyright (c) Nero AG" line
  (README:12-39). NOTICES misses MIT/BSD files from Azahar's src/ (S7). P10(a) sound; S1 build the shipped binary
  from the stripped tree, S2 record the build inputs. G4 is a fact (GPLv3 only, via SPIRV-Tools Apache-2.0); G2
  default (a); G5 git pushes with a fine-grained PAT that may not cover a new repo. Q1 (a) with bsdtar @archive
  --exclude (no release_pack.py); Q2 no host dylib; Q3 keep pytest, installed explicitly; Q4 commit the notes.
  Hours about 2.05 h. USING section 11's "Stock: exact repeats" contradicts PLAN's risk 3 (S13, D fixes).
- Guy 2026-11-13 00:3x: G8 "Rewrite before push (Recommended)": rewrite this repo's history before the first
  push so no commit names his personal address or its local part. G3 "Switch to OpenSSL 3" (static OpenSSL 3 in
  Phase 3's P9b rebuild; Phase 4 offers its exact source and carries its Apache-2.0 licence).
- Revision 1 launched 00:41 (a739c8de18f2e6992, fresh opus), with Phase 3 review 2's asks and both rulings.
