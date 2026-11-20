<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-20 11:02 (session 3ds-toolkit-eb)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-830: nothing running; next is C6 step 1 (staging v1.2.0 on the PC) | - | main | - |

Phase 8 is under way: Guy, 2026-11-18 ~21:00, "you have my green light. go". He did not answer Q1-Q5, so the
plan's recommended answers apply (laz-810 notes). Phase A is done: runs/p8/a/decisions.md. All lane PC jobs go
through runs/p8/bin/pclane under one shared PC lock (one job of ours at a time since the 2026-11-18 PC crash).

## Next steps, in order
1. Phase C (laz-830): C1 command line and C2 audio done (laz-831, 832). C3 exact inputs parked (laz-833) for the
   next core phase with the leak fix. Phase B closed 11:01 (laz-820: CI green on pushed 4bb6f43, both workflows; the
   3-copy pool tests passed in macos-live). The clock fix (laz-834) is merged and proven on a UTC host.
2. Next, C6 step 1: stage v1.2.0 on the PC from core-win64's artifact (D:/lazpy/p8/c6/art, run 44691632561). The
   clone of D:/lazpy/p8/c6/main.bundle needs `git clone -b main`, then `git remote remove origin`; rebundle main at
   the current head first. Then mkrelease.sh --inherit v1.0.0 --win-artifact <art> --out <dir>/v1.2.0, fill in the
   fetch.sh pins (REL_TAG, the Windows zip sha256), the OpenSSL docs (core/OPENSSL.md 81-83, STATUS.md:100,
   USING:484; the prefix is now fixed), the note that v1.1.0 Windows states may not load, then release_check
   --pre-push (SSL_CERT_FILE = MSYS2's ca-bundle). Then C6 steps 3-10 under the plan's phase C table
   (docs/plans/phase-8.md). The release audit must also read commit 44ad3c5's text (review finding 2).
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
