<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-18 22:56 (session 3ds-toolkit-eb)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-812 soak: 100 boots, then 300 state loads, one copy | PC D:\lazpy\p8\a2 (old v1.1.0 lane; no code change since) | main (bg brmxfinee) | runs/p8/a2/full.out ends with "local rc=" |

Phase 8 is under way: Guy, 2026-11-18 ~21:00, "you have my green light. go". He did not answer Q1-Q5, so the
plan's recommended answers apply (laz-810 notes). Item 500 (the peers' asks) stays open and the peers stay quiet.

## Next steps, in order
1. After laz-812: write numbers and the build-or-drop lines into runs/p8/a/decisions.md; laz-812 to 5-done.
2. laz-813: one copy, then two, of the test app's 3D scene (GPU memory, peak RSS, fps), one PC job at a time.
3. laz-814: the audio probe, a scratch host patch in a worktree, never merged; laz-815: the GPU-less Vulkan trial.
4. Close laz-810 with runs/p8/a/decisions.md; then phase B (laz-820): its briefs from docs/plans/phase-8.md (B0-B8).

## Waiting on Guy (only what blocks a step above)
- Pushes: each one needs his word. Local main is ahead of origin, and phase 8 commits stay local until he says so.
- The PC install of diffutils and actionlint: the classifier denied it; Guy was asked and has not answered.
The full list is generated into `docs/status/README.md`.

## Pointers
- Plan: `docs/plans/phase-8.md` (rev 1; phase A at its "Phase A" section). Review: `docs/reviews/phase-8-plan-review.md`.
- Items: laz-810 and its steps 811-815; 820, 830 and 840 in 4-not-started.
- PC commands: `docs/map/runners.md` (Windows PC section); the helper runs/p8/bin/pc is outside git.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH. Republish it only inside the progress command
  or when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
