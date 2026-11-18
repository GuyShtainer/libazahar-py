<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-18 20:59 (session 3ds-toolkit-eb)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
- Nothing runs. Phase 8 planning is done (laz-800 to 804 in 5-done): `docs/plans/phase-8.md` rev 1, given to Guy
  2026-11-18 20:59 with its five questions (section on open questions). Plan only: no execution without his go.
- Phase 7 is done: v1.1.0 (Windows x64 proven) published 2026-11-18 00:07; status commits pushed (e0addc0, CI green).
- Item 500: asks from Gen3D and 3DPlatinum; the peers were told to stop messaging this session (Guy, 2026-11-18).

## Next steps, in order
1. On Guy's go and answers to Q1-Q5 of docs/plans/phase-8.md: one item per phase (A, B, C, then D) in
   4-not-started, phase A's item to 1-in-progress, then its briefs from the plan's step tables.
   Guy asked for a single revision. Plan only: after laz-804, stop and report; no execution without his go.
2. Deferred to the next core rebuild (from the release audit):
   - the Windows zip's own SOURCE.md snapshot entry;
   - the OpenSSL ENGINESDIR/MODULESDIR prefix;
   - release_check check 13 printing PASS when it did not run.

## Waiting on Guy (only what blocks a step above)
- The go for phase 8 and answers to its Q1-Q5 (step 1).
- Pushes: each push needs his word (the 2026-11-18 grant covered the status commits only).
- The PC install of diffutils and actionlint: the permission classifier denied it; Guy was asked and has not answered.
The full list is generated into `docs/status/README.md`.

## Pointers
- Items: `docs/status/lazpy/5-done/700-phase-7-windows-proven.md` and its steps 701-714;
  `500-phase-5-user-asks.md` (in progress).
- Release logs: runs/p7/w9/notes.md and runs/p7/w10/notes.md. The private audit is
  runs/reviews/release-legal-audit-v1.1.0.md.
- PC worker: the toolkit's docs/pc-worker/HANDOFF.md and `guy-decisions.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH. Republish it only inside the progress command
  or when Guy asks.
- Rules that bite every turn: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
