# Phase 6 step V4: agent brief (version and docs for v1.0.0)

Written 2026-11-13 by the main loop for item laz-600. The step is `docs/plans/phase-v1.md` section 3, V4; the
promise it writes down is section 1 of that plan. One cheap agent, on MAIN (there is no worktree now).

## Rules

- MAIN is this repo's main checkout. Two other projects are running their
  release tests against MAIN's core and host right now: never touch `build/`, `build-core/`, `dl/`, `core/`,
  `host/`, `testapp/` or `tools/build-core.sh`, never run `make`, `tools/fetch.sh`, `tools/build-core.sh`,
  `tools/mkrelease.sh` or any emulator test. No git commands except `git status`, `git diff`, `git log`, `git grep`
  and `git rm` of the one file named below (the main loop commits). Never write in Gen3D or 3DPlatinum.
- Never edit `docs/status/`, `docs/hours.tsv`, `docs/progress.html`, `docs/plans/` or `docs/reviews/`.
- Public text: plain English, short sentences, no game names, no key or certificate bytes, offsets or decode steps.
  Never claim what no gate ran. Measured speed numbers in README stay as they are (step V3 updates them later).
- Progress as you go in runs/v4/progress.md. Final message: the files changed, the checks run with their last lines,
  and anything left.

## Your files and the changes

- `pyproject.toml` version and `python/libazahar/__init__.py` `__version__`: `1.0.0`. Check that no test pins the
  old value (`git grep -n 0.1.0 tests`); if one does, update it.
- `tools/fetch.sh`: `REL_TAG=v1.0.0`; `LAZPY_CORE_ZIP=azahar_lazpy_libretro-2126.2-lazpy.2-macos-arm64.zip`;
  `LAZPY_CORE_SHA=TBD` and `TESTAPP_SHA=TBD` (V8 fills them; read `pin_set` at :94-101 to confirm `TBD` is refused
  with a clear message, and say so). Nothing else in fetch.sh.
- `tools/mkrelease.sh:17` and `tools/release_check.py:4`: the usage examples say `<tag>` (for example `v1.0.0`).
  Leave `release_check.py:781`'s planted test values alone.
- `STATUS.md` rewritten for 1.0, keeping its shape (What works, What does not work yet, Known limits, Considered and
  dropped) and its rule that every "works" line names the item whose Evidence proves it:
  - The head: "As of 2026-11-13. v1.0.0." (no commit hash; release_check checks it at V8 if it needs one: read
    `tools/release_check.py` for what it checks in STATUS.md and README.md and follow that).
  - Add to What works: `threads()` (guest thread list) and `citra_init_ticks_override` (the tick seed) on core
    lazpy.2 (laz-510); the strict option-profile and input-script formats, the exit codes and the API freeze (laz-610);
    the depth-stencil readback fix on MoltenVK (laz-520, our test-app check).
  - Poll-exact movies: "our core exports `lazpy_movie_play`; the host and Python do not call it; not in 1.0."
  - Remove the "macOS 11.0 header" limit (the lazpy.2 core's header says 15.0) and the "ABI may change before 1.0"
    line; put in its place the promise from `docs/USING.md`'s paragraph before section 1, in one or two lines.
  - The build line names `core/PIN-nokeys` as the gated route.
  - The instance cap line stays provisional (V3 decides it).
  - "removed before v0.1.0" becomes "removed before the first release".
- `README.md`: the version line (line 10) says v1.0.0, the first release, with the promise in one sentence (semantic
  versioning from 1.0.0; see `docs/USING.md`). Any other v0.1.0 or prerelease wording, also.
- `docs/USING.md`: the places that say "Poll-exact" or "poll-exact" (find them by text) say "our core exports it; the
  host and Python do not call it". Nothing else in USING.md.
- `docs/map/runners.md`: the v0.1.0 commands become v1.0.0.
- `docs/release-notes/v1.0.0.md` (new): what 1.0 is, the promise (short), what is new since the last internal state
  (the 1.0 API changes: keyword-only run options, `run_until`'s `stop_every`/`stop_new`, `Path` returns, strict
  profile format, exit code 9, the tick seed, `threads()`, the stencil fix), the assets (read `tools/mkrelease.sh`
  for their names and copy the shape of `docs/release-notes/v0.1.0.md`), "macOS 15 or later on Apple silicon",
  Python 3.10 or newer (tested on 3.14 here; CI runs 3.10). It must pass `notes_wording_findings` in
  `tools/release_check.py` (no speed tokens, no "fps", "key" only in the allowed phrases): run that function on
  your file and show the result.
- `git rm docs/release-notes/v0.1.0.md`.
- `NOTICES.md`: regenerate with `tools/mknotices.py` if it reads only MAIN's build-core/build.inputs and sources (read
  it first; if it would write anywhere but NOTICES.md or needs a build, stop and say so).
- Gates: `python3 -I tools/docs_check.py`, `python3 -I tools/mkmap.py` then `python3 -I tools/map_check.py`, the fast
  pytest (`env -u LAZ_ROOT -u LAZ_HOST -u LAZ_PROFILE -u LAZ_LAZPY_PROFILE python3 -m pytest -q -m "not slow"
  tests/python`), and `git grep -n -E 'v?0\.1\.0'` outside docs/status, docs/plans, docs/reviews, docs/research,
  docs/hours.tsv, docs/commit-map* and docs/progress.html: list what is left and why.
