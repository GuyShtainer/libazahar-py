---
asof: 2026-11-13 08:09
---
# libazahar-py status: read this first

A headless, scriptable host for the Azahar 3DS emulator's libretro core, plus a Python layer. Public GPLv3, always
publish-ready. What to do this hour: `docs/status/lazpy/1-in-progress/HANDOFF.md`.

## Now
- Phases 1-3 are done: our own core (no console keys, no Nintendo certificate, OpenSSL 3), the host library, the
  test app, input and stops, the Python layer and savestates, many copies at once, and guest memory reads.
- Phase 4 is built and audited: README, STATUS, usage and API docs, examples, the notices, the release tools. The
  legal audit found one blocker (the old stock-core download line in history); a third history rewrite removed
  it, and the re-audit graded v0.1.0 shippable.
- The release is staged locally: pre-push check 16 of 16, and a fresh clone runs the README route and the full
  test suite (136 passed, 3 expected skips). Nothing is pushed.

## Next
- Guy: accept the audit's one open risk (the default core build downloads Azahar's unchanged source and deletes
  its key files before compiling), then create the repo and say "push".
- Then: re-stage at the tagged commit, push main and the tag, a draft release for Guy to publish, and the check of
  the published release.

## Where each item is
<!-- generated:begin (python3 -I tools/mkprogress.py; do not edit by hand) -->
### libazahar-py (`docs/status/lazpy/`)
- in-progress: `docs/status/lazpy/1-in-progress/400-phase-4-release.md`
- in-progress: `docs/status/lazpy/1-in-progress/420-step-i-release.md`
- files: 0 in `3-waiting-on-guy/`, 0 in `4-not-started/`, 22 in `5-done/`, 0 in `6-parked/`
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
