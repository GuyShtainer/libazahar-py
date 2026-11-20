---
id: laz-835
title: lazpy
order: 835
kind: step
parent: laz-830
page: Phase C: the rebuilt Windows core, OpenSSL's folders at their Windows defaults (C6a)
hours: -
---
# The rebuilt Windows core: OpenSSL's folders at their Windows defaults

## What it is
Plan step C6a (Q1's recommended yes, one CI round). The v1.1.0 Windows core had OpenSSL's OPENSSLDIR joined to the
cross build's prefix (`/opt/lazpy/openssl-3.6.5-mingw64/C:/Program Files/Common Files/SSL`), and ENGINESDIR and
MODULESDIR inside that prefix (a CVE-2019-1552-class item in a shipped binary). `tools/build-core-win64.sh` now sets
all three on OpenSSL's make line to OpenSSL's own Windows defaults, records the line in `build.inputs`, and fails if
the DLL holds other strings. The zip's SOURCE.md also names the system-archives snapshot.

## Exit gate
One `core-win64.yml` run, green, with an attested artifact whose DLL holds the three Windows paths; not green: defer
again with the reason written.

## Evidence
2026-11-20 06:59 UTC: core-win64 run 44691632561 on pushed 5cf51cf (the one round) green; artifact core-win64, the
DLL's sha256 ee3e9e0a76fa8a5a..., attestation verify rc 0; build.inputs openssl_openssldir "C:/Program Files/Common
Files/SSL", openssl_enginesdir "C:/Program Files/OpenSSL/lib/engines-3", openssl_modulesdir "C:/Program
Files/OpenSSL/lib/ossl-modules"; gate_f2.txt starts `gate_f2 1 target=win64`, head=5cf51cf. The code: 587c171.
The release's clone checks (C6 steps 3-4) run on this core. Done.

## Pointers
- Plan: `docs/plans/phase-8.md:192` (C6a), Q1 at line 311
- Docs: core/OPENSSL.md (Windows section), STATUS.md, docs/USING.md section 15a, docs/release-notes/v1.2.0.md

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.

- OpenSSL's Configure on Linux does not see `C:/` as absolute and joins it to the prefix; setting the three dirs on
  `make build_libs` is what reaches the compiled-in strings.
- The Windows zip keeps its file name (lazpy.2); only `SHA256SUMS` and `tools/fetch.sh` tell the two builds apart.
