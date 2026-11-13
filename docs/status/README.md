---
asof: 2026-11-13 00:40
---
# libazahar-py status: read this first

A headless, scriptable host for the Azahar 3DS emulator's libretro core, plus a Python layer. Public GPLv3, always
publish-ready. What to do this hour: `docs/status/lazpy/1-in-progress/HANDOFF.md`.

## Now
- Phase 1 is done: our patched core builds (now with Azahar's built-in console keys turned off and no build paths in
  the binary), the host library and the test app pass their gates.
- Phase 2: button, touch and circle-pad input and the stop rules are merged (28 gate checks). The Python layer
  passes its full test run (69 tests, state boot about 1.6 s against Guy's 2.5 s bound); its review asked for six
  small fixes, being made now; then it merges and Phase 2 is done.
- Phase 3 (many copies, our core's full test run, memory reads): two reviews done; the final revision is being
  written. It adds one more core rebuild: OpenSSL 3 instead of LibreSSL (Guy), Nintendo's HTTPS client
  certificate removed, and no console keys loaded.
- Phase 4 (docs, legal audit, release): plan and one review done; revision 1 is being written (history rewrite
  before the first push, OpenSSL's source offered with the release).

## Next
- Merge the Python layer and close Phase 2; the core rebuild; then Phase 3's builders (worker pool and speed table,
  core gate, memory reads). Gen3D can start using the tool once Phase 2 is merged.
- Phase 4's second review and revision, then docs and the release. Pushing waits on Guy (repo, "push", publish).

## Where each item is
<!-- generated:begin (python3 -I tools/mkprogress.py; do not edit by hand) -->
### libazahar-py (`docs/status/lazpy/`)
- in-progress: `docs/status/lazpy/1-in-progress/400-phase-4-release.md`
- files: 0 in `3-waiting-on-guy/`, 2 in `4-not-started/`, 20 in `5-done/`, 0 in `6-parked/`
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
