---
asof: 2026-11-12 18:31
---
# libazahar-py status: read this first

A headless, scriptable host for the Azahar 3DS emulator's libretro core, plus a Python layer. Public GPLv3, always
publish-ready. What to do this hour: `docs/status/lazpy/1-in-progress/HANDOFF.md`.

## Now
- The whole plan is final (`docs/PLAN.md`). The work is four phases, each planned and reviewed twice before it is built. Nothing is built yet.
- Tests so far: the core runs a 3DS homebrew app with no window and screenshots both screens; a real 3D scene runs about 5.6x real time on a busy machine, and three copies give about 3.2x one copy's total. Memory reads need our own patched core (the stock one exposes no game memory).
- Phase 1 (our patched core build, the host library, the test app): both reviews done; the last one found two plan errors (a record's size, missing interface notes) and moved the long core build to after review. One revision left, then building.
- Phase 2 (input, stop rules, the Python layer, savestates): one review and one revision done, about 4.4 h of build work; one review loop left.
- Session paused by a slow stop at 18:11; nothing running.

## Next
- Phase 1's last revision and Phase 2's second review, side by side (briefs ready in `docs/plans/next-briefs.md`); then Phase 1's three builders and our core's first build. Gen3D starts using the tool at the end of Phase 2.
- Then many copies at once with a speed table, our core passing the full test set, memory reads, docs, the legal audit and the public release.

## Where each item is
<!-- generated:begin (python3 -I tools/mkprogress.py; do not edit by hand) -->
### libazahar-py (`docs/status/lazpy/`)
- in-progress: `docs/status/lazpy/1-in-progress/100-phase-1-foundation.md`
- in-progress: `docs/status/lazpy/1-in-progress/200-phase-2-control.md`
- in-progress: `docs/status/lazpy/1-in-progress/210-step-c-input-and-stops.md`
- in-progress: `docs/status/lazpy/1-in-progress/220-step-d-python-and-states.md`
- in-progress: `docs/status/lazpy/1-in-progress/300-phase-3-scale-and-memory.md`
- files: 0 in `3-waiting-on-guy/`, 6 in `4-not-started/`, 12 in `5-done/`, 0 in `6-parked/`
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
