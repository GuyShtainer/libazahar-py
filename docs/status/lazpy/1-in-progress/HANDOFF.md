<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 03:15 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-400: Phase 4's before-launch steps (phase-4.md section 2): downloads, Gen3D's copy check, the launch | MAIN | main | H and I builders launched |

Not running: Phase 3 is done (item 300). G8b is done (item 400's notes; map docs/commit-map-g8b.tsv); only MAIN
and main remain.

## Next steps, in order
1. Ask Gen3D's session to confirm its rsync copy of the package has no .git (phase-i.md 8.1b step 9); tell the
   toolkit main loop the G8b map exists.
2. Downloads (phase-i.md 6 step 4): OSSL if missing, the system-archives snapshot (SNAP), font licence texts if
   SNAP lacks them; each sha256 goes in the launch message.
3. Launch H and I builders side by side (phase-4.md section 2; items 410, 420 to 1-in-progress first), Q1 default
   (remove the stock fetch). I owns tests/gate-b.sh:45; the gate's event lines changed at Phase 3's close.
4. Then the joint as-built review, merges, I2, the release-legal-audit (I3); the push waits for Guy.

## Waiting on Guy (only what blocks a step above)
- Phase 4's G5-G7 (repo creation, the word "push", publishing the draft), G9 (spike 2's game: default say
  nothing), and whether macOS 11-14 users matter for v0.1.0 (default: "macOS 15 or later"): item 400's notes.
- Phase 4's questions Q1-Q9 (docs/plans/phase-4.md section 7), first Q1: remove the scripted stock-core download
  (recommended) or accept its YELLOW grade (docs/reviews/release-ip-legal.md section 7). G1, G3 and G8 are answered and done.
The full list is generated into `docs/status/README.md`.

## Pointers
- Phase 1: `docs/status/lazpy/5-done/100-phase-1-foundation.md` (its notes hold Phase 2's asks and review 2's
  verdict); review `docs/reviews/phase-1-review-2.md`.
- Phase 2: `docs/status/lazpy/5-done/200-phase-2-control.md`; plans `docs/plans/phase-2.md`, `phase-c.md`,
  `phase-d.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH (version 5, 2026-11-13 00:41); republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
