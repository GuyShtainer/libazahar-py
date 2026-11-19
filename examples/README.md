# Examples

Run each from the repository folder, with the Python layer installed (`.venv/bin/pip install -e .`; on Windows the
venv's programs are in `.venv/Scripts/`, so `.venv/Scripts/python examples/quickstart.py`) and
`build/testapp.3dsx` in place (see the README's Install). Each uses only the standard library and the package, prints
`<name> ok` as its last line, and exits non-zero with one plain line when a check fails. Each reads the core from
`LAZ_CORE`, else the library's default.

- `quickstart.py`: boots the test app, holds A, takes a shot, checks the frame count, both screen sizes and A in the
  app's log. Either core. `.venv/bin/python examples/quickstart.py`
- `pool_shots.py`: five instances through a `Pool`, one shot each, in separate folders. Either core. It warns that
  `Pool(5)` is above the default cap of 4, so the fifth job waits for a slot; that is the cap working.
  `.venv/bin/python examples/pool_shots.py`
- `memory_watch.py`: reads the test app's 32-byte record with the watch list and `emu.memory`. Our core only; on
  Azahar's own core it prints `needs our core: see README, Two cores` and exits 3.
  `.venv/bin/python examples/memory_watch.py`
- `verdict.py`: runs the test app with `run_until` on a line it writes (`booted f=`) and exits by the table in USING
  section 3: 0 pass, 1 the test failed, 2 bad argument, 3 boot failure, 10 the guest exited, 11 a guest error, 12 timed
  out, 13 the worker or host crashed (or could not run). The test app writes no PASS or FAIL
  line, so the example waits for that log line; point `RESULT_FILE` and `PASS_TEXT` at your own app's result file.
  `.venv/bin/python examples/verdict.py`

Run `nice -n 10` on a shared machine. Each example makes its folder under `runs/`, which git ignores.
