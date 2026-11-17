---
asof: 2026-11-13 19:53
---
# libazahar-py status: read this first

A headless, scriptable host for the Azahar 3DS emulator's libretro core, plus a Python layer. Public GPLv3, always
publish-ready. What to do this hour: `docs/status/lazpy/1-in-progress/HANDOFF.md`.

## Now
- v1.0.0 is staged and checked, ready to publish. Gen3D and 3DPlatinum both passed their own tests on the final
  core; the state-restore crash they found is fixed. A real 3D scene runs at about 9x real time, four copies at
  once. The full test pass had 0 failures. The legal re-audit's changes are done, including a fourth history
  rewrite, and the pre-push check passes 16 of 16.
- Guy held the push (2026-11-13: "We will push in the future"). Nothing is pushed.

## Next
- On Guy's word: stage once more (later commits make the build-files asset stale), the pre-push check, then the
  repo, the push, the tag and the draft release, and the check of the published release.

## Where each item is
<!-- generated:begin (python3 -I tools/mkprogress.py; do not edit by hand) -->
### libazahar-py (`docs/status/lazpy/`)
- in-progress: `docs/status/lazpy/1-in-progress/400-phase-4-release.md`
- in-progress: `docs/status/lazpy/1-in-progress/420-step-i-release.md`
- in-progress: `docs/status/lazpy/1-in-progress/500-phase-5-user-asks.md`
- in-progress: `docs/status/lazpy/1-in-progress/600-phase-6-v1-release.md`
- in-progress: `docs/status/lazpy/1-in-progress/700-phase-7-windows-proven.md`
- in-progress: `docs/status/lazpy/1-in-progress/710-w5-core-in-ci.md`
- files: 0 in `3-waiting-on-guy/`, 4 in `4-not-started/`, 36 in `5-done/`, 0 in `6-parked/`
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
