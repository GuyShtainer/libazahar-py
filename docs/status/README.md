---
asof: 2026-11-12 16:02
---
# libazahar-py status: read this first

A headless, scriptable host for the Azahar 3DS emulator's libretro core, plus a Python layer. Public GPLv3, always
publish-ready. What to do this hour: `docs/status/lazpy/1-in-progress/HANDOFF.md`.

## Now
- Set up on 2026-11-12 from a Gen3D test: Azahar's libretro core runs a 3DS homebrew app with no window and saves screenshots of both screens, about 50x real time on an idle menu.
- A second test (memory reads, real speed in a 3D game scene) is running in the Gen3D session.

## Next
- Plan the whole project, two review rounds with revisions, then one plan per phase.

## Where each item is
<!-- generated:begin (python3 -I tools/mkprogress.py; do not edit by hand) -->
### libazahar-py (`docs/status/lazpy/`)
- in-progress: `docs/status/lazpy/1-in-progress/20-phase-f1-core-build.md`
- in-progress: `docs/status/lazpy/1-in-progress/21-phase-a-host-library.md`
- in-progress: `docs/status/lazpy/1-in-progress/22-phase-b-test-app.md`
- files: 1 in `3-waiting-on-guy/`, 7 in `4-not-started/`, 8 in `5-done/`, 0 in `6-parked/`
<!-- generated:end -->

## How to change a status (one step)
`git mv` the item file to its new state folder, fill its Evidence, then run
`python3 -I tools/mkprogress.py && python3 -I tools/status_check.py --strict-handoff && python3 -I tools/map_check.py`
and republish `docs/progress.html` (not published yet: `docs/status/lazpy/3-waiting-on-guy/ask-01-progress-page.md`).
The Now and Next lines above are written by hand; they are the page's Now block, and Guy says when they change.

## Where everything else is
- `docs/map/README.md`: the map index (code, tools, plans, rules, runners).
- `docs/status/lazpy/<state>/`: one file per phase, step or ask. Open one only when you work on it; its last
  section holds the lessons and notes.
- `docs/status/templates/`: the format (from 3DPlatinum's design, via Gen3D).
- `docs/progress.html` is generated for Guy. Never read it to orient, never edit it.
