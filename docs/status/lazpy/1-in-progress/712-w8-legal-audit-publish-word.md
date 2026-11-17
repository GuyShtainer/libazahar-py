---
id: laz-712
title: lazpy
order: 712
kind: step
parent: laz-700
page: Windows proof: legal audit, then Guy's word to publish
hours: -
---
# Windows proof: legal audit, then Guy's word to publish

## What it is
release-legal-audit agent; then the main loop asks Guy for the publish word (quoted here verbatim).

## Exit gate
The W8 gate in the plan; Guy's publish word quoted below. Plan: `docs/plans/phase-7.md` line 343.

## Evidence
- 2026-11-17 22:28 started: release-legal-audit on candidate 309fd0e with runs/p7/w8/brief.md (staged copy refreshed).
- 2026-11-17 22:45 audit returned: SHIPPABLE, no blocker (runs/reviews/release-legal-audit-v1.1.0.md, private; audited b60741b,
  status-only past 309fd0e). The seven inherited assets match v1.0.0's digests (local and published); the staged
  SHA256SUMS checks 12 of 12. Fixed now: S1 the loose SOURCE.md's Windows entry names the system-archive snapshot
  (mkrelease.sh top_source_md); N2 "official" -> "Azahar's own CI-built" (release notes); N3 the savestate rows say
  which side was run (USING 15a, release notes); N4 STATUS lists the no-ELF thread-test skip; N7 stale fetch.sh comment;
  N9 .gitignore *.dll *.exe. P2: release_check's check 13 cannot run on the PC (the key-header reading copy is Mac-only
  and never copied); run on the Mac read-only, make_windows + history_bytes_findings: 1647 blobs, 0 hits. N8: the
  planted nobody.x@gmail.com is invented. P1: the W9 build-files exemption is recorded in item 713.
- 2026-11-17 22:47 re-staged from 3543987 (runs/p7/w7/stage7.out): mkrelease rc 0, Windows zip sha unchanged (791efc1a...),
  SHA256SUMS 01d284b81ac07689...; release_check rc 0, all PASS, PEND only `<pick after W9>`, plant-red rc 0
  (release_check7.out). runs/p7/w8/staged/ refreshed: 12 of 12 check. Next: Guy's publish word.

## Pointers
- Plan section: `docs/plans/phase-7.md:343`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
- Deferred to the next Windows core rebuild (the W8 audit): S1's other half, the zip's own SOURCE.md (mkrelease.sh
  win_zip_source_md) should name citra_system_archives-f470e0c.tar.gz too; changing it now changes the zip sha that
  W7 proved (fetch.sh LAZPY_CORE_SHA_WIN). N1: OpenSSL's ENGINESDIR and MODULESDIR resolve to C:\opt\... on Windows,
  which a plain user can create (CVE-2019-1552 class; low, the config path cannot exist): fix the prefix
  (core/OPENSSL.md, tools/build-core-win64.sh). N6: CI run 44130873582's superseded artifact stays downloadable until
  2027-02-15; deleting it is Guy's call; consider retention-days in core-win64.yml. P2: release_check's check 13 prints
  NOTE then PASS where it cannot run; it should say PEND or SKIP. N11: keep tag v1.0.0 and its page for good.
- For the audit (found in W5, 2026-11-17): the Windows core holds four components the macOS core does not and the W1b
  licence delta did not list: xbyak (BSD-3-Clause), zydis and zycore (MIT), all dynarmic's x86-64 backend; and glad
  (Azahar sets ENABLE_OPENGL on Windows), which ships no licence file: NOTICES-windows-x64.md quotes glad v0.1.36's
  README ("Public Domain, WTFPL or CC0"; GL spec Apache-2.0) and khrplatform.h's Khronos notice. Check those texts.
