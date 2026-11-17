---
id: laz-703
title: lazpy
order: 703
kind: step
parent: laz-700
page: Windows proof: check the licences of what the Windows download adds
hours: -
---
# Windows proof: check the licences of what the Windows download adds

## What it is
ip-legal agent: the licence delta of the Windows core and host (static OpenSSL, mingw runtimes, the runtime source asset).

## Exit gate
The W1b gate in the plan. Plan: `docs/plans/phase-7.md` line 244.

## Evidence
- 2026-11-17 W1b PASS: docs/reviews/phase-7-ip-legal.md answers all 7 questions with yes/no and an action.
  One v1.1.0 blocker (1b): the Windows NOTICES must carry winpthreads COPYING and COPYING.MinGW-w64-runtime.txt
  verbatim, from the linked version (relayed to W2b1 mknotices, W2b2 release_check). Others: keep the D13 source
  tar (libquadmath check via a link map, W2b1/W5); no Vulkan or zlib notice; inherited assets checked against the
  live v1.0.0 page (W2b2); tested-on wording rule applied on p7-docs (9eab645); attest only after the key search,
  permissions on the attest step only (W2b1). Knowledge base: toolkit 7625227.

## Pointers
- Plan section: `docs/plans/phase-7.md:244`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
- Left open: whether libquadmath, libssp or libatomic is linked (W5's link map settles it); encryption export
  rules (US EAR 742.15(b), Israel) never researched, not new with Windows, low.
