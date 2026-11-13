# Step L: agent briefs (the D24S8 stencil readback fix)

Written 2026-11-13 by 12:03 by the main loop for item laz-520. The source is `docs/research/stencil-readback.md` (the
cause, the patch, the repro recipe). Two cheap agents work at once in the worktree ../libazahar-py-k (branch
core-rev2) on separate files. The fix must land in `core/patches` before V0b's main build (`docs/plans/phase-v1.md`).

## Rules for both agents

- Work only in the worktree ../libazahar-py-k. Never write in MAIN, Gen3D or 3DPlatinum. No git commands except
  `git status`, `git diff` and `git log` (the main loop commits). Never run tools/fetch.sh (the worktree's dl/ parts
  link to MAIN). Only the files listed under "Your files".
- Emulator runs: `nice -n 10`, `env -u LAZ_ROOT -u LAZ_HOST -u LAZ_PROFILE -u LAZ_LAZPY_PROFILE`,
  `LAZ_CORE=<worktree>/build-core/azahar_lazpy_libretro.dylib`, at most 2 instances at once, headless only (the
  Python layer or `build/azhost`), never a window. devkitARM first in `PATH`
  (`PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH`).
- Progress as you go in runs/stencil/<your name>-progress.md (numbers, what failed). Final message: files changed,
  tests run with their last lines, anything left.
- Public text: plain English, no game names.

## Brief R: the test-app repro (name: repro)

Your files: `testapp/source/*` (a new `stencil.c`/`stencil.h` is fine), `testapp/Makefile` if needed,
`testapp/README.md`, `tests/python/test_stencil_live.py` (new), runs/stencil/.
- Add a stencil self-test to the test app, following "Test-app repro" in `docs/research/stencil-readback.md`
  (MAIN's copy: ../libazahar-py/docs/research/stencil-readback.md): a D24S8 target, a 32-bit clear to depth fffffe
  and stencil 00, one 100x80 quad writing stencil 0x80 at depth 4001ff, a GX TextureCopy back to linear memory,
  then the counts (stencil histogram, the 0x80 bbox after de-tiling, depth mismatches). Variants (a) first use,
  (b) a dummy draw before the fill, (d) a second readback in the same process; (c) is optional.
- The app runs it only when asked (a new word in `sdmc:/testapp/control.txt`, or a new control mode; read
  `testapp/source/control.c`), so every existing test keeps its exact output. Log the counts in one line to the
  SD log (`sdlog`), for example `stencil v=a n80=8000 n00=... nff=... bbox=x0,y0,x1,y1 dbad=0`.
- `tests/python/test_stencil_live.py` (slow tier): boots the app N times (fresh process each; N=10, an env
  override is fine), reads the line, and asserts the exact counts for (a), (b) and (d).
- Run it on the worktree's current core (no fix yet) and record the counts per launch: we expect (a) to fail on
  some launches and (b), (d) to pass. If (a) never fails in 10 launches, also try variant B of the recipe (EQUAL /
  INCR) and say so. Run `make testapp`, `make`, the fast pytest (`python3 -m pytest -q -m "not slow" tests/python`)
  and the existing slow tests that use the test app's log (`tests/python/test_api.py -m slow`) to show nothing
  else moved.

## Brief P: the core patch (name: patch)

Your files: `core/patches/0010-lazpy-ds-barriers.patch` (new), `NOTICES.md` (its patch-hash list), and
runs/stencil/.
- Write the patch as "Proposed patch" in the research doc says (the `Surface::AccessFlags` and
  `PipelineStageFlags` widening in `video_core/renderer_vulkan/vk_texture_runtime.cpp`; the transfer write in
  the source scope of the pre-barriers of `DepthToBuffer` and `ConvertDS24S8ToRGBA8` in `vk_blit_helper.cpp`).
  Read the real source first: `dl/azahar-src/unpacked/azahar-unified-source-2126.2/` (read-only) and the
  patched tree in `dl/azahar-src/build-src/`. Check every line number and name the doc cites; if one is wrong,
  say so and fix the patch to the real code. Do NOT take the optional shader change or the Mip0 fix.
- Match the format of the other patches (read `core/patches/0009-lazpy-thread-regs.patch` and how
  `tools/build-core.sh` applies them, lines 81-111). Prove it applies after 0000-0009 with no fuzz and no rejects
  on a scratch copy of the unpacked source (copy to runs/stencil/apply-check/, apply 0000-0010 with the same
  `patch` flags the script uses, then delete the copy).
- Add its sha256 row to `NOTICES.md` in the same form as 0009's row.
- Do NOT run tools/build-core.sh; the main loop runs the build after the repro shows red.
