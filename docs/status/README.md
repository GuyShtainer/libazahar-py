---
asof: 2026-11-12 16:02
---
# libazahar-py status: read this first

A headless, scriptable host for the Azahar 3DS emulator's libretro core, plus a Python layer. Public GPLv3, always
publish-ready. What to do this hour: `docs/status/lazpy/1-in-progress/HANDOFF.md`.

## Now
- The plan is final (`docs/PLAN.md`): two full reviews, two revisions and a short source check. Ten phases, about 11 h of agent time plus 1-2 h of machine time for the first core build.
- Tests so far: the core runs a 3DS homebrew app with no window and screenshots both screens; a real 3D scene runs about 5.6x real time on a busy machine, and three copies give about 3.2x one copy's total. Memory reads need our own patched core (the stock one exposes no game memory).
- Building has started: our patched core's build script, the host library and the test app, side by side. Their build briefs are being written.

## Next
- Buttons, touch and stop rules; then the Python layer with savestates and starting a run from a saved state, where Gen3D starts using the tool.
- Then many copies at once with a speed table, our core passing the full test set, memory reads, docs, the legal audit and the public release.

## Where each item is
<!-- generated:begin (python3 -I tools/mkprogress.py; do not edit by hand) -->
### libazahar-py (`docs/status/lazpy/`)
- in-progress: `docs/status/lazpy/1-in-progress/20-phase-f1-core-build.md`
- in-progress: `docs/status/lazpy/1-in-progress/21-phase-a-host-library.md`
- in-progress: `docs/status/lazpy/1-in-progress/22-phase-b-test-app.md`
- files: 0 in `3-waiting-on-guy/`, 7 in `4-not-started/`, 9 in `5-done/`, 0 in `6-parked/`
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
