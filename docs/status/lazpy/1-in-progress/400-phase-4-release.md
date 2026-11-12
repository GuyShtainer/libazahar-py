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
- Revision 1 launched 00:38 (a739c8de18f2e6992, fresh opus), with Phase 3 review 2's asks and both rulings.
- Revision 1 (a739c8de18f2e6992, opus, 00:38-01:02; phase-4.md section 13, one line per review-1 finding): all of
  review 1 taken except N10 (the full layout listing stays, collapsed). Hours H 0.45, I 0.65, one joint as-built
  review 0.2, main loop and legal agents 0.5, loops 0.4: about 2.2 h against PLAN.md's 1.1. P9b facts taken:
  v0.1.0 says "macOS 15 or later" (Homebrew's libcrypto.a objects are minos 15.0; R31: libazhost and azhost already
  15.0; building OpenSSL for macOS 11 declined, a Phase 5 candidate, risk 9); OPENSSLDIR/ENGINESDIR/MODULESDIR
  strings expected (R30, risk 14); R2 21,828,992 bytes. For Phase 3 (section 12): brew pin openssl@3 (done 01:04 by
  the main loop), keep keyblob_findings importable, keep MAIN's build-core/build and build.inputs until the release,
  G8 after P9b and before Phase 3's worktrees (the main loop does it so), optional MACOSX_DEPLOYMENT_TARGET=15.0 at
  the next core rebuild. Stock core also embeds the key blob and ClCertA, so the README route uses our core (P16);
  ip-legal question 7 asks whether fetching the stock core is within policy. Open for review 2: Q5 (README route on
  our core), Q6 (G8 timing), Q7 (brew cat as OpenSSL's build-script source). For Guy: G5, G6, G7 (plus hygiene
  defaults), G9 (spike 2's game: default say nothing), whether macOS 11-14 users matter for v0.1.0.
- Review 2 (a520c6028898077dc, opus) and the ip-legal consult of phase-i.md 9.1 (aee2a9ba07ce653cf; its brief
  names the four drop entries) launched 01:05. Review 2 also gets Gen3D's first use (Gen3D
  docs/phase2-safe/LAZPY-TRY-1.md, f8d3830 in Gen3D: 36000 frames at 222.6 fps in one run(), stock core, no crash,
  boot 0.9 s, peak RSS 848 MB): (1) run(timeout=) bounds the whole batch, a no-progress timeout asked about;
  (2) an input at frame 0 raises a plain ValueError from inputs.fold, not a LibAzaharError, and USING.md's run()
  line lacks the 1-based rule; (3) shot keys are batch frames, shot file names whole-run frames; (4) a reused
  workdir keeps the old SD with the warm shader cache. H's docs carry 2-4; 1 and 2's error class are code.
- G8 done by the main loop 01:06-01:08 (phase-i.md 8.1): before scan as expected (6 commits 15d0323-8a16f9e, one
  path, 0 messages, 0 at HEAD, no tags); backup bundle verified, outside the repo; git filter-repo --force with
  --replace-text and --replace-message; after: HEAD tree unchanged, 98 commits before and after, identities
  unchanged, no refs/replace, fsck clean, 0 hits in every commit and message, step-c and step-d keep their SHAs,
  both worktrees clean. 20 commits rewritten (15d0323 -> 1844a5d onward): docs/commit-map-g8.tsv, pointed at from
  docs/map/README.md. Checks rerun: status_check, map_check, mkprogress, make check. The I3 audit runs after this.
- Review 2 (a520c6028898077dc, opus, 01:05-01:17; docs/reviews/phase-4-review-2.md): 4 blockers, 9 should fix,
  7 nice; ready after revision 2, no third loop. B1 the drop list's directory entry (externals/libressl) breaks
  I's per-entry sha256 note member, its text and check 10; SOURCE/NOTICES still claim an unbuilt LibreSSL ships.
  B2 I's links to step 0 are stale (KEG path vs /opt/homebrew/Cellar/openssl@3/3.6.5, check 6's old openssl= key,
  check 2's keyblob_findings arguments, LAZ_OPENSSL_ROOT -> LAZ_OPENSSL_PREFIX, old SHAs). B3 docs_check forbids
  "macOS 11" in STATUS.md while STATUS must state the 11.0 header mismatch. B4 build/testapp.3dsx holds 6 /Users/
  strings from assert() paths (testapp/Makefile:22-23 has no prefix map): step I gets one -ffile-prefix-map line
  there plus a strings count. Q5 keep P16; Q6 settled (G8 done); Q7 use the keg's .brew/openssl@3.rb, offline.
  Gen3D friction: USING lines in H now; ArgumentError(LibAzaharError, ValueError) and a fresh_sd option after
  v0.1.0 (0.1 h each). Hours about 2.15. For Guy later: may rules.md 2's exception cover building OpenSSL from
  its pinned tarball (with risk 9's macOS 11 build)? Revision 2 waits for the ip-legal consult, then takes both.
