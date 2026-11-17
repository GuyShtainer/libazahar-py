---
id: laz-705
title: lazpy
order: 705
kind: step
parent: laz-700
page: Windows proof: a clean build route for the Windows core
hours: -
---
# Windows proof: a clean build route for the Windows core

## What it is
Sonnet agent: build-core-win64.sh with the OpenSSL recipe and a neutral prefix, build.sh untouched at its v1.0.0 bytes, the CI core-build workflow, gate_f2 PE mode.

## Exit gate
The W2b1 gate in the plan. Plan: `docs/plans/phase-7.md` line 252.

## Evidence
- 2026-11-17 12:55 W2b1 local gates PASS, committed on branch p7-w2b1 (edfb145): `git diff v1.0.0 --
  tools/build-core.sh` empty; gate_f2_pe.py --plant-red on the PC with the known DLL: "all planted reds fail as
  expected", rc 0; py_compile OK; sh -n OK; shellcheck info-only (run on the Mac, read-only lint). actionlint not
  run (not on the PC). Licence actions from W1b built in (verbatim runtime licences, link map, attest job only).

## Pointers
- Plan section: `docs/plans/phase-7.md:252`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
- Unproven until W5's CI run: gcc-N-source on Ubuntu 26.04, GCC ident mapping, OPENSSLDIR strings in the DLL,
  the link-map parse, the strings checks. mknotices win64 not re-run end to end after its last edit. Main loop
  after W5: fill core/OPENSSL.md's libssl.a/libcrypto.a sha256 from build.inputs; on a leak failure, also delete
  the run's logs. D4's apt line lacked patch and dpkg-dev; a second install step adds them.
