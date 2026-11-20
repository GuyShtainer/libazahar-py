<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-20 11:37 (session 3ds-toolkit-eb)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|

Phase 8 is under way: Guy, 2026-11-18 ~21:00, "you have my green light. go". He did not answer Q1-Q5, so the
plan's recommended answers apply (laz-810 notes). Phase A is done: runs/p8/a/decisions.md. All lane PC jobs go
through runs/p8/bin/pclane under one shared PC lock (one job of ours at a time since the 2026-11-18 PC crash).

## Next steps, in order
1. Phase C (laz-830): C1 command line and C2 audio done (laz-831, 832). C3 exact inputs parked (laz-833) for the
   next core phase with the leak fix. Phase B closed 11:01 (laz-820: CI green on pushed 4bb6f43, both workflows; the
   3-copy pool tests passed in macos-live). The clock fix (laz-834) is merged and proven on a UTC host.
2. C6 (laz-830 Evidence): steps 1-2 done 11:15, 3-4 done 11:35 (clone_check rc 0 on 1ea1686; fixture kept at
   D:/lazpy/p8/fixtures/v1.2.0), 6 done 11:36. Staging: D:/lazpy/p8/c6 (repo = bundle clone, identity set;
   rel/v1.2.0; art = core-win64's artifact). Re-stage after every commit (mkrelease, then release_check --pre-push
   --inherit v1.0.0 --gate-f2 art/gate_f2.txt, needles on stdin as path forms). Left: 5 macOS CI on the candidate
   (needs a push: Guy said "Wait" until the PC checks end; ask again), fill the notes' macOS line; 7 check 13 (Mac
   scan or Guy's ruling); 8 release-legal-audit (also commit 44ad3c5's text and check 12's history-only paths: Guy
   ruled "scrub current files", done in 94c2693; history stays); 9 his word, push, tag, publish; 10 clone_check
   from GitHub.
3. The PC STAMP (C:\lazpy\STAMP.json) got a quick refresh about 11:00 on Guy's word ("Quick refresh, redeploy later"):
   only core/options-lazpy.txt's drift hash changed, in all three stanzas (old copy STAMP.before-tz.json). The
   full redeploy (deploy_py.py + deploy_win.py with the new profile) waits for a quiet PC moment; then tell Gen3D
   and 3DP the new deploy ids. The dzn stanza's python/libazahar/_abi.py drift is older and not ours to fix.
4. docs_check's links check fails on the PC lane only (no .git there); it runs on the Mac.

## Waiting on Guy (only what blocks a step above)
- Pushes: each one needs his word, and after a red CI run he is asked again before the next push.
- The PC install of diffutils and actionlint: the classifier denied it; Guy was asked and has not answered.
The full list is generated into `docs/status/README.md`.

## Pointers
- Plan: `docs/plans/phase-8.md` (rev 1; phase B rows at lines 165-173). Lane briefs: `docs/plans/phase-8b-briefs.md`.
- Items: laz-830 in 1-in-progress; 840 in 4-not-started; 820-829 and 834 in 5-done.
- PC commands: `docs/map/runners.md` (Windows PC section); the helpers runs/p8/bin/pc and pclane are outside git.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH. Republish it only inside the progress command
  or when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
