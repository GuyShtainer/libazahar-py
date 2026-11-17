---
id: laz-711
title: lazpy
order: 711
kind: step
parent: laz-700
page: Windows proof: stage the release and prove a fresh clone works
hours: -
---
# Windows proof: stage the release and prove a fresh clone works

## What it is
Main loop: stage v1.1.0, clone_check on the PC from the bundle; W7c: Gen3D and 3DP each run one real job on the release candidate.

## Exit gate
The W7 and W7c gates in the plan. Plan: `docs/plans/phase-7.md` line 311.

## Evidence
- 2026-11-17 20:00 started. W5 is done (run 44138010543, DLL 9f45bca5...). Order: merge main into p7-docs (1.1.0
  lives there), bundle it to the PC, stage with mkrelease --inherit v1.0.0 --win-artifact D:/lazpy/p7/w5/art, then
  the pins. Guy 2026-11-17: no pushes for now. The PC crashed at 19:3x under 3DP + Gen3D load (WHEA cache error):
  one light PC job at a time until Guy has looked; the 4-copy clone_check waits for his word on the PC.
- 2026-11-17 20:03 W7 step 1 staged on the PC from p7-docs cadcc30 (main merged in; the build files equal 6345b83, 0 diff
  lines): mkrelease --inherit v1.0.0 rc 0, the seven inherited assets and five repo pins ok; D:/lazpy/rel/v1.1.0
  SHA256SUMS sha256 711634f8cef341c8264acf215cebc76ae76ca2b59e611f174ff9df6ca6f51c8a (log runs/p7/w7/stage.out).
  Windows zip sha256 791efc1a...; the Mac zip and test app equal the v1.0.0 pins.
- 2026-11-17 20:03 W7 step 2 pins on p7-docs: fetch.sh REL_TAG=v1.1.0 (REL_TAG_PREV v1.0.0), LAZPY_CORE_SHA_WIN. Found:
  the DLL's OPENSSLDIR is "/opt/lazpy/openssl-3.6.5-mingw64/C:/Program Files/Common Files/SSL" (Configure runs on
  Linux, sees C:/ as relative and joins the prefix), not the planned Windows path: the guest's HTTPS finds no CA file
  on Windows. STATUS, USING, the release notes and core/OPENSSL.md say so; core/OPENSSL.md also gets the two .a shas
  of run 44138010543. DEVIATION for W9 step 3: core/ is a build file, so `git diff 6345b83 HEAD -- build files` is
  not empty; it holds only core/OPENSSL.md prose and the two .a shas, never the "- Source:" line the build reads.
  W8's auditor and W9's gate check exactly that. Re-stage after this commit (the build-files asset is HEAD's).
- 2026-11-17 20:07 W7 step 6 (release_check, light) on the PC over a fresh clone of main 9bf51ee, re-staged from it
  (SHA256SUMS sha256 300384cb4aa1cb4ed9593c777864fbffdca251cbf1075e8347e10d633cc6a586): rc 0, 17 PASS, no FAIL;
  PEND only for `<from W7>` (savestates, from the clone_check) and `<pick after W9>`. --plant-red rc 0. Fixed on
  the way: (1) the test app (v1.0.0's bytes) holds devkitPro's newlib build path (/home/davem/..., dtoa.c and
  mprec.c asserts): now a NOTE for that exact path in the test app only (9bf51ee); (2) the PC venv's Python cannot
  verify GitHub's certificate: SSL_CERT_FILE=MSYS2's ca-bundle.crt for release_check; (3) the bundle clone's
  refs/remotes/origin: `git remote remove origin`. Every commit needs a re-stage (git archive embeds HEAD's id).
  Logs: runs/p7/w7/release_check3.out, stage3.out. Steps 3-5 (4-copy clone_check) wait for Guy's word on the PC.
- 2026-11-17 20:24 W7 steps 3-5, clone_check run 2 (4 copies, Guy "Run it, 4 copies"), main 9fe82b8: 1 failed,
  298 passed. Run 1 (015fd8a) had 6 failures, fixed: (1) Azahar's own CI-built Windows stock core names itself
  "219d743" (the pinned commit; GenerateBuildInfo ignores GIT-TAG under CI): pins.h AZH_STOCK_COMMIT, accepted
  exactly, no suffixes (4 tests); (2) the v1.0.0 fixture (macOS) is refused on Windows, boost "incompatible native
  format - size of long": a documented limit now (USING 15a, release notes); the fixture test expects StateError plus
  that host.log reason (0913489); (3) test_k_threads skips without build/testapp.elf (the release test app has
  none), listed in allowed-skips/w7.txt. release_check on staging 0913489 (SHA256SUMS 0f94dcb3...): rc 0, PEND only
  `<pick after W9>`; plant-red rc 0 (runs/p7/w7/release_check5.out).
- 2026-11-17 20:35 clone_check run 3 (0913489): 2 failed, 297 passed, 8 skipped, under other sessions' builds (PC
  CPU 46 %): test_state_boot 2.97 s over Guy's 2.5 s bound (passed on the quiet run 2), and test_m5_stock_core_refuses
  found no start line after 30 frames: the memory test now boots up to 300 frames until the line is logged (d6b9793).
  The bound stays; run 4 needs a quiet PC. Then 20:48 the PC crashed a second time (3DP's builds running; nothing of
  ours). 20:51: all PC work held until Guy has looked at the PC; d6b9793 still needs a re-stage before run 4.
- 2026-11-17 22:26 W7 GATE PASSED. Guy ~20:56 "Run with 2 copies" (LAZ_MAX_INSTANCES=2 in cc-pc.sh; the pool gate
  still runs its 3 workers). Run 4 (309fd0e, PC busy): 1 failed, 298 passed: test_g1_g2_g4 kill-to-acquire 1.875 s over
  1.0 s, load again. Run 5 in a quiet window that Gen3D, 3DP and gba-toolkit held for it (PC 8 %, no builders): 299
  passed, 8 skipped, skips_check --list w7 0 problems (the fixture test ran and passed, by the documented cross-OS
  refusal), clone ok 270 s (runs/p7/w7/cc5.out). release_check on staging 309fd0e (SHA256SUMS 25487e9a...): rc 0,
  17 PASS, PEND only `<pick after W9>`, plant-red rc 0 (release_check6.out). W8's staged copy refreshed; all 13 check.
  W7c (Gen3D and 3DP jobs on a release-candidate deploy id) is open.
- 2026-11-17 22:30 W7c started. Found: the PC job path has no per-job deploy choice (job_native.py takes the folder
  from STAMP.native.win_lib or STAMP.py.root only), so "a release-candidate deploy id, default not switched" needs
  an opt-in first. A sonnet agent adds job.json "deploy" (+ LAZPY_DEPLOY in lazpy-py), checked against the folder's
  own shas, in toolkit worktree .claude/worktrees/rc-deploy (tests on the PC). Then the main loop deploys it, builds
  deploy-win-<sha> and deploy-py-<sha> from the W7 host and the W5 core, and asks Gen3D and 3DP for one job each.
- 2026-11-17 22:41 W7c deploy ready. Toolkit 1bc50a5: per-job opt-in (job.json "deploy", LAZPY_DEPLOY); the pyjob name check
  skips job-written __pycache__ (the live deploy-py-94713d6e07 has 15 .pyc). PC: all three live folders hash to
  their names; job_native_py_test 34 OK; lazpy_py_test's Windows failures (POSIX fakes) identical to main 95ab1d5.
  C:\lazpy\bin\job_native.py replaced (old copy .before-rcdeploy). RC folders from clone 309fd0e (host build of
  W7 cc5) + W5 core 9f45bca5...: deploy-win-99d843c8c2, deploy-py-04f977e97f (base 6345b83, fp fb0def449f16);
  STAMP.json unchanged. Asked Gen3D and 3DP for one normal job each with LAZPY_DEPLOY.
- 2026-11-17 23:00 W7c 3DP PASS: one Black 2 field run, 1 copy, lane-pc PC-tree route, LAZPY_DEPLOY=deploy-py-04f977e97f:
  "GATE lane-pc PC PASS: host=pcn:de55a1309e fp=fb0def44 wall=42s", rc 0, 6000 frames (job bw2-b2-1794949035-7261-446).
  The route keeps no result JSON, so the deploy proof is the fp: fb0def44 is the RC folder's deploy.json fp
  (fb0def449f16; the live STAMP py fp is 4b0a90edbb15), and the RC folder got its first 15 .pyc at 22:57. Gen3D open.
- 2026-11-17 23:26 W7c Gen3D PASS: six lane-pc jobs (owner g3d, ~23:10-23:20, 1 copy each) with LAZPY_DEPLOY=deploy-py-04f977e97f;
  every HOST.txt shows fp=fb0def44... (the RC folder); the two s1-new jobs passed their gate, the s1-base jobs are
  Gen3D's expected-to-fail baselines; no deploy error. W7 and W7c gates PASSED; item done.

## Pointers
- Plan section: `docs/plans/phase-7.md:311`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
None yet; planned in phase-7 revision 2.
