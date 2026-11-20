<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-20 22:26 (session 3ds-toolkit-eb)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
Nothing.

Phase 8 is finished. v1.3.0 is published (2026-11-20 ~22:08, tag at c2b0bb1, 15 files, digests equal SHA256SUMS);
the legal audit said shippable (runs/reviews/release-legal-audit-v1.3.0.md, private). After publishing, the
no-compiler route passed on both systems (a fresh clone from GitHub on the PC; macos-live with `host: release`)
and test-windows-live passed on the published core (laz-840 Evidence). All PC jobs go through one shared PC lock
(D:/lazpy/p8/pc.lock).

## Next steps, in order
1. Nothing is planned past phase 8. The next core phase (laz-833 exact-frame inputs, with laz-829's leak fix) is
   parked and needs a plan (opus: plan, two review loops) and Guy's go. Asks from Gen3D and 3DPlatinum go to laz-500.
2. Small follow-ups from the v1.3.0 audit, for the next release (none blocks): write `pacman -Q` into the Windows
   host zip in host-bin.yml (the linked MSYS2 versions are recorded nowhere permanent); the loose SOURCE.md's Notices
   could name the Windows host zip's own NOTICES.md; the never-commit list gaps the audit's N5 names.
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
- Items: 830, 835 and 840 in 5-done; 833 parked (next core phase, with laz-829's leak fix).
- PC commands: `docs/map/runners.md` (Windows PC section); the release staging dir D:/lazpy/p8/c6 (art = the
  v1.2.0 Windows core's CI artifact, rel/v1.2.0 = the published files).
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH. Republish it only inside the progress command
  or when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
