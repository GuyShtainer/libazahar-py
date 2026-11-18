<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-18 20:04 (session 3ds-toolkit-eb). SLOWSTOP DONE 11:48

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
- Nothing runs: no agents, no PC jobs, no wake-ups. Phase 7 is done: v1.1.0 (Windows x64 proven) was published
  2026-11-18 00:07 and passed its post-publish checks at 01:52 (items 713, 714 and 700 are in 5-done).
- Guy's 2026-11-18 answers are carried out: the private pre-rewrite backups and CI run 44130873582's superseded
  artifact are deleted, and the status commits are pushed.
- Item 500: asks from Gen3D and 3DPlatinum. On Guy's word (2026-11-18), the peer sessions were told to stop
  messaging this session. Take a new ask only when Guy restarts the work.

## Next steps, in order
1. A new phase starts only on Guy's word: an opus plan with two review loops first. Guy's private side work for
   this project is in the memory index (index-lazpy), never in this repo.
2. Deferred to the next core rebuild (from the release audit):
   - the Windows zip's own SOURCE.md snapshot entry;
   - the OpenSSL ENGINESDIR/MODULESDIR prefix;
   - release_check check 13 printing PASS when it did not run.

## Waiting on Guy (only what blocks a step above)
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
