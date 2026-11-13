# Phase 6 step V1: agent briefs (API freeze changes)

Written 2026-11-13 11:28 by the main loop for item laz-610. The source is `docs/reviews/api-freeze-1.0.md` (items 1-13,
the profile spec and the exit-code table); `docs/plans/phase-v1.md` section 3 V1 is the step. Two cheap agents work
at once in the worktree ../libazahar-py-k (branch core-rev2) on separate files. The main loop does item 11, merges
the USING.md texts, commits, and has the diff reviewed.

## Rules for both agents

- Work only in the worktree ../libazahar-py-k. Never write in MAIN, Gen3D or 3DPlatinum. No git commands except
  `git status` and `git diff` (the main loop commits). Never run tools/build-core.sh or tools/fetch.sh (the
  worktree's dl/ parts link to MAIN). Never touch build-core/ or dl/.
- Only the files listed under "Your files". If a change needs another file, write the need into your progress file
  and leave the file alone.
- Tests: `make`, `make test-host`, and `python3 -m pytest -q -m "not slow" tests/python` any time. Emulator tests
  (slow tier, azhost runs) only after 11:55 (another session's timed run ends then), always with `nice -n 10`,
  `env -u LAZ_ROOT -u LAZ_HOST -u LAZ_PROFILE -u LAZ_LAZPY_PROFILE`, and
  `LAZ_CORE=<worktree>/build-core/azahar_lazpy_libretro.dylib`. At most 2 emulator instances at once. Never open a
  window.
- Write progress as you go to runs/v1/<your name>-progress.md (what is done, what failed, numbers), so a stop loses
  nothing. Your final message: the files changed, the tests run with their last lines, and anything left.
- Style: the repo's C and Python style (read the file before editing). Public docs: plain English, no game names.

## Shared contract: the profile case table

`tests/data/profile-cases/` holds pairs: `<name>.txt` is a profile file, `<name>.expect` is either the applied
`key=value` lines in order (an accepted file), or one line `error line N` (a refused file; N is 1-based, 0 for a
whole-file error such as too many lines). The host agent writes the cases and both tests; the Python agent makes
`libazahar.emulator._read_profile(path) -> List[Tuple[str, str]]` follow the spec (review section "Option-profile
format"): `ArgumentError(f"{path}:{n}: <reason>")` for a bad line, `HostError` for an unreadable file.

## Brief A: host (name: host)

Items 1 (the C side, the case table and both tests), 2, 3 and 12 of the review.
Your files: `host/*`, `Makefile` (a new test target is fine), `tests/host/*`, `tests/data/profile-cases/*`,
`tests/python/test_profile_format.py` (new), `python/libazahar/_abi.py` (only the new `AZH_EXIT_STATE` constant
next to the other const rows), `docs/HOST-API.md`, and runs/v1/using-host.md (new, the USING.md text: the exit-code
table for section 3, the input-script spec as a new section 4a, the profile spec for section 14; the main loop
pastes it in).
- Item 1: a pure `host/profile.c` (no libretro headers; follow `host/azh_pure.h`'s pattern) used by `--profile`,
  `--lazpy-profile` and the `--opt` pair rule; `tests/host/test_profile.c` reads the case table and is part of
  `make test-host`; `tests/python/test_profile_format.py` (fast tier) runs every case through `_read_profile`.
- Item 2: `AZH_EXIT_STATE = 9`, the const row in `host/api.c`, `_abi.py`'s constant; `print_escaped` escapes `"`;
  `msg=` stays last; CLI cases (a missing `--state` file gives 9) in the C or CLI checks; HOST-API.md's exit-code
  text fixed as the review says.
- Item 3: decimal or `0x` hex only (a leading `0` is decimal), a line over 511 bytes is an error naming the line; a
  test (`010` is 10, `0x10` is 16).
- Item 12: `azhost.h` comments and HOST-API.md as the review lists (ABI 4, `azh_threads`, the line numbers, the
  promise in place of "may change before 1.0": host and Python are one unit, the C promise is source level; the
  layout dump at ABI 4 from `azh_abi_layout`).

## Brief B: Python (name: python)

Items 1 (the Python parser), 4, 5, 6, 7, 8, 9, 10 and 13 (only `operator.index` for `frames` and `shots`; skip the
Touch/Circle range check) of the review.
Your files: `python/libazahar/*` except `_abi.py`, `tests/python/*` except `test_profile_format.py`, `examples/*`,
and runs/v1/using-python.md (new, the USING.md text: the which-call-raises-what table for section 8, the Path
returns for sections 3, 9 and 10, the thread and Pool notes for section 13, the sentence "The promise is
`libazahar.__all__`; `libazahar.errors` stays importable.", and a new section 20 "API reference", one line per
`__all__` name; the main loop pastes it in).
- Item 4 and 5: the exact signatures in the review; update every caller in tests and examples.
- Item 6: `SlotTimeout.op == "slot"`; `SlotTimeout` and `LoadWarning` defined in `errors.py` (re-imported by
  `_slots`); `sd_seed` checked up front (`ArgumentError`); a missing profile gives `HostError`.
- Item 7: `errors.__all__` and `inputs.__all__` trimmed; an `__all__` snapshot test in `tests/python/test_api.py`.
- Item 8: `Path` returns, `Shot.frame_total` required.
- Item 9: `Pool.__exit__` cancels pending jobs when the body raised; a test.
- Item 10: `app` and `workdir` read-only properties.
