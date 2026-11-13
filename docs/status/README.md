---
asof: 2026-11-13 12:49
---
# libazahar-py status: read this first

A headless, scriptable host for the Azahar 3DS emulator's libretro core, plus a Python layer. Public GPLv3, always
publish-ready. What to do this hour: `docs/status/lazpy/1-in-progress/HANDOFF.md`.

## Now
- Phases 1-3 are done, and phase 4's v0.1.0 staging was audited shippable. Guy then asked for v1.0.0 instead
  (phase 6): the API is frozen with a written promise, the depth-stencil readback is fixed, CI is ready, and the
  final core is built on main with its gates green. Version 1.0.0 docs are written. Nothing is pushed.
- The user check found a blocker: in Gen3D, restoring a saved state crashes on the first 3D draw. The cause is
  upstream Azahar's (the stock core crashes too): after a restore the renderer never selects its shader cache for
  a `.3dsx`. A one-line core fix is next.

## Next
- The core fix, a new core build, the gates, then Gen3D and 3DPlatinum test the new core again.
- Then the speed rows on a quiet machine, the full test pass, staging with the legal re-audit, and Guy's word to
  push and publish v1.0.0.

## Where each item is
<!-- generated:begin (python3 -I tools/mkprogress.py; do not edit by hand) -->
### libazahar-py (`docs/status/lazpy/`)
- in-progress: `docs/status/lazpy/1-in-progress/400-phase-4-release.md`
- in-progress: `docs/status/lazpy/1-in-progress/420-step-i-release.md`
- in-progress: `docs/status/lazpy/1-in-progress/500-phase-5-user-asks.md`
- in-progress: `docs/status/lazpy/1-in-progress/600-phase-6-v1-release.md`
- in-progress: `docs/status/lazpy/1-in-progress/660-step-m-state-restore-shader-cache.md`
- files: 0 in `3-waiting-on-guy/`, 0 in `4-not-started/`, 26 in `5-done/`, 0 in `6-parked/`
<!-- generated:end -->

## How to change a status (one step)
`git mv` the item file to its new state folder, fill its Evidence, then run
`python3 -I tools/mkprogress.py && python3 -I tools/status_check.py --strict-handoff && python3 -I tools/map_check.py`
and republish `docs/progress.html` with `~/.claude/bin/republish.sh --apply docs/progress.html https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH`
(only inside the progress command or when Guy asks).
The Now and Next lines above are written by hand; they are the page's Now block, and Guy says when they change.

## Where everything else is
- `docs/map/README.md`: the map index (code, tools, plans, rules, runners).
- `docs/status/lazpy/<state>/`: one file per phase, step or ask. Open one only when you work on it; its last
  section holds the lessons and notes.
- `docs/status/templates/`: the format (from 3DPlatinum's design, via Gen3D).
- `docs/progress.html` is generated for Guy. Never read it to orient, never edit it.
