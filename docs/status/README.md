---
asof: 2026-11-20 22:55
---
# libazahar-py status: read this first

A headless, scriptable host for the Azahar 3DS emulator's libretro core, plus a Python layer. Public GPLv3, always
publish-ready. What to do this hour: `docs/status/lazpy/1-in-progress/HANDOFF.md`.

## Now
- v1.3.0 (for outside users: the prebuilt host, a CI recipe for your own app, a gymnasium-style example) was
  published 2026-11-20 ~22:08. Its files matched their checksums on GitHub; after publishing, the no-compiler route
  passed on both systems (a fresh clone from GitHub on the PC; a hosted macOS runner) and the Windows emulator CI
  passed on the published core. Phase 8 is done (v1.1.0 to v1.3.0).
- Nothing runs.

## Next
- A new phase only on Guy's word: the parked exact-frame inputs (laz-833) needs an opus plan and two review loops.

## Where each item is
<!-- generated:begin (python3 -I tools/mkprogress.py; do not edit by hand) -->
### libazahar-py (`docs/status/lazpy/`)
- in-progress: `docs/status/lazpy/1-in-progress/500-phase-5-user-asks.md`
- files: 0 in `3-waiting-on-guy/`, 0 in `4-not-started/`, 76 in `5-done/`, 1 in `6-parked/`
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
