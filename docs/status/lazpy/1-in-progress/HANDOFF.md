<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-20 21:55 (session 3ds-toolkit-eb)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-840 the v1.3.0 release-legal-audit (brief runs/p8/c6/audit-brief-v1.3.0.md) | Mac, read-only | a86ab729607f17d77 | it writes runs/reviews/release-legal-audit-v1.3.0.md |

Phase 8 is under way: Guy, 2026-11-18 ~21:00, "you have my green light. go". He did not answer Q1-Q5, so the
plan's recommended answers apply (laz-840 notes). v1.2.0 is published (laz-830 done 15:58, clone check from GitHub
passed). All PC jobs go through one shared PC lock (D:/lazpy/p8/pc.lock; one job of ours at a time since the
2026-11-18 PC crash).

## Next steps, in order
1. Release v1.3.0 (laz-840; Guy: "Release v1.3.0", and "Stop asking every little thing ... I wanna share it"): the
   candidate f1cc46f (pushed up to db83f99) passed CI, the PC clone checks by both routes, release_check and a private
   side test (laz-840 Evidence). Staged files: D:/lazpy/p8/c6/rel/v1.3.0 and runs/p8/c6/staged3 (SHA256SUMS 29640eaf...).
   After the audit: fix and restage if it asks, then push, tag v1.3.0 at the candidate, publish with all 15 staged
   files, check the published digests, clone check from GitHub on the PC (scratchpad gh.sh with the tag).
2. After publishing: macos-live gets a `host: release` dispatch input (`fetch.sh --host`, no make) and one run: the
   macOS no-compiler check; record it in STATUS. Then close laz-840 (git mv to 5-done), STATUS line 3 at the tag.
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
