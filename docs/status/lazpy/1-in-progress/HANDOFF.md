<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-20 16:35 (session 3ds-toolkit-eb)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-840: D5 review of the merged phase D (findings to runs/p8/d/d5-review.md) | main checkout, read only | a60222a9ce0913557 | it sends its final message |

Phase 8 is under way: Guy, 2026-11-18 ~21:00, "you have my green light. go". He did not answer Q1-Q5, so the
plan's recommended answers apply (laz-840 notes). v1.2.0 is published (laz-830 done 15:58, clone check from GitHub
passed). All PC jobs go through one shared PC lock (D:/lazpy/p8/pc.lock; one job of ours at a time since the
2026-11-18 PC crash).

## Next steps, in order
1. Phase D (laz-840, plan `docs/plans/phase-8.md:208`): the four lanes (briefs `docs/plans/phase-8d-briefs.md`)
   are merged on main and pass on the PC. PC lanes copy the v1.2.0 host, test app and Windows core from
   D:/lazpy/p8/base-v1.2.0 (runs/p8/bin/pclane). Not run yet: host-bin.yml, test-windows-live.yml (3 of 3 naming
   lavapipe) and macos-live's recipe step; each needs a push, so Guy's word. The host pins in tools/fetch.sh stay
   TBD until host-bin.yml's first run. For D5: the recipe pins ref v1.3.0 (works once that tag exists); hostbin's
   clone check skips step failed only on the lane setup (runs/p8/d/hostbin-notes.md); a hosted -g build may embed
   runner paths (check the first artifact).
2. Then D5: the opus review (running; brief at the end of `docs/plans/phase-8d-briefs.md`), fixes, merge, release v1.3.0 by C6's list plus the no-compiler clone check on both systems.
3. The PC STAMP (C:\lazpy\STAMP.json) got a quick refresh about 11:00 on Guy's word ("Quick refresh, redeploy later"):
   only core/options-lazpy.txt's drift hash changed. The full redeploy (deploy_py.py + deploy_win.py with the new
   profile) waits for a quiet PC moment. Tell Gen3D and 3DP the new deploy ids a little BEFORE it (Gen3D's lanes
   remake their savestate checkpoints after it).
4. docs_check's links check fails on the PC lane only (no .git there); it runs on the Mac.
5. History rewrite leftovers (private): the commit map runs/p8/c6/commit-map-private.txt and the deleted CI run list
   runs/p8/c6/deleted-ci-runs-private.txt stay out of git. Old ids survive only inside GitHub's cached objects until
   its own clean-up; Guy may ask GitHub Support for a purge.

## Waiting on Guy (only what blocks a step above)
- Pushes: each one needs his word, and after a red CI run he is asked again before the next push.
- The PC install of diffutils and actionlint: the classifier denied it; Guy was asked and has not answered.
The full list is generated into `docs/status/README.md`.

## Pointers
- Plan: `docs/plans/phase-8.md` (rev 1; phase D at line 208, Q4 at line 314).
- Items: laz-840 in 1-in-progress; 830 and 835 in 5-done; 833 parked (next core phase, with laz-829's leak fix).
- PC commands: `docs/map/runners.md` (Windows PC section); the release staging dir D:/lazpy/p8/c6 (art = the
  v1.2.0 Windows core's CI artifact, rel/v1.2.0 = the published files).
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH. Republish it only inside the progress command
  or when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
