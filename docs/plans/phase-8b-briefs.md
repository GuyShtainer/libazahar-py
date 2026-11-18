# Phase 8 B briefs: five builder lanes (sonnet), then one review (opus)

Guy, 2026-11-18 ~21:00: "you have my green light. go". Plan: `docs/plans/phase-8.md`, Phase B table (B0-B8). Phase
A's findings added B9 (item 829). Five lanes run in parallel, each in its own worktree made at main by the main loop.

## Rules for every lane (paste at the top of each brief)

- **Where you work.** Your worktree is `runs/p8/wt/<lane>/` in the libazahar-py repo; its branch is `p8-<lane>`. Edit
  only there, and only the files your brief lists, plus tests you add. No commits, pushes, tags or branch changes: the
  main loop commits.
- **The Mac.** It is closed to 3DS work: no emulator, no `make`, no pytest on it. Every test runs on the Windows PC
  through `<main>/runs/p8/bin/pclane`, where `<main>` is the main checkout (the parent of `runs/`). Read its header.
  - Every PC job takes the shared PC lock, fast ones too: since the PC crash of 2026-11-18, one job of ours runs at a
    time. Never pass `--nolock`.
  - Fast tests: `pclane <worktree> <lane> -- '$PY -m pytest -q -m "not slow" tests/python'`.
  - Live tests:
    `pclane <worktree> <lane> -- 'LAZ_REQUIRE_EMULATOR=1 $PY -m pytest -q -rs tests/python/<file>'`.
  - The PC lane copies your worktree's files. It reuses the v1.1.0 host, core and test app, and host C is unchanged
    in phase B. Keep each live run short and run one at a time. Never start a run of 2 or more copies without
    `--copies 2`.
- **The PC.** It is shared with other projects and crashes under heavy load. Never run two of your jobs at once. Never
  kill a process you did not start. If pclane exits 75 or 76 (no lock, or not enough RAM), wait and retry later. Never
  work around the lock.
- **Code rules.** Read `~/.claude/python-golden-rules.md` before writing Python. Follow the package's style, and its
  ctypes and keyword-only API shape (`docs/HOST-API.md`, `docs/USING.md` section 20).
  - Every new public name joins the frozen promise at v1.2.0, so update `tests/python/test_api.py`'s lists where it
    keeps them.
  - Keep `python3 -I tools/docs_check.py` passing; run it on the PC as a fast job: `$PY -I tools/docs_check.py`.
- **Docs.** Plain English, no game titles, no personal paths, usernames or emails, no speed claims. In `docs/USING.md`,
  edit only the sections your brief names. Add your API entries as your own block at the end of section 20, so lanes
  merge cleanly.
- **Hard rules:** `docs/map/rules.md`. Save as you go: write the test skeleton first, then fill it in.
- **Your final message:** the files changed, every test command you ran and its last line, and the three things the
  main loop most needs to know (above all anything left undone or any skip).

## Lane `images`: B1 determinism and B3 compare/verdict (items 822, 824)

Read the B1 and B3 rows of the plan (lines 166 and 168) and do exactly what they say.
- New module `python/libazahar/images.py`:
  - `digest(screens)`: a stable hash of the top and bottom screen pixels.
  - `compare(a, b, *, max_delta=0, max_pixels=0)` on arrays or our PNG paths, returning a small result: the largest
    channel delta, the count of differing pixels, and whether it is within the limits.
  - `write_diff(path)`.
  - numpy is imported lazily; without it, a clear error names the `numpy` extra. Add the extra to `pyproject.toml` if
    it is missing.
  - The PNG reader accepts only the host's own format (`host/png.c`: 8-bit RGBA, filter 0, one IDAT) and refuses
    every other.
- `tests/python/test_images.py`: fast, no emulator.
- `tests/python/test_determinism.py`: live, every case of the B1 row. The test app's record format is in
  `tests/testapp_log.py`, `testapp/source/record.c` and `testapp/README.md`.
- `examples/verdict.py`, plus its line in `examples/README.md`. The test app does not write PASS/FAIL. Read what
  docs_check runs for examples. Write the guest side as an SD file the example seeds or checks; do not change the
  test app. If that cannot be shown honestly with the test app, say so and keep the example to `run_until` on a log
  line it does write.
- USING:
  - a new section "10a. What repeats" (B1's table);
  - section 3: the exit-code table (1 test failed, 12 timed out, 13 crashed; `azhost`'s codes keep their meanings).
    Check `host/azhost_main.c` for which codes are taken; the plan says 1, 12 and 13 are free;
  - your block in section 20.
- Live runs: about 3 runs of test_determinism. Each boots a few copies one after another, never at once.

## Lane `life`: B2 evidence on failure and B5 parent death (items 823, 826)

Read the B2 and B5 rows (lines 167 and 170).
- B2:
  - `python/libazahar/errors.py`: `.workdir` and `.log_path` on the live errors. Pickling must keep working; there is
    a test for it.
  - `python/libazahar/emulator.py` and `_client.py`, where the errors are raised.
  - Tests: extend `tests/python/test_errors.py` and the fake-worker tests (`tests/python/fakeworker.py`), plus one
    live crash case in `test_live_errors.py`.
  - USING section 19 becomes a table keyed by each error's opening text, with the `azhost` outer-timeout line.
- B5:
  - A Windows Job object with kill-on-close, created at the first spawn, in `_client.py` (or a new `_job.py`). It
    uses ctypes on kernel32: CreateJobObjectW, SetInformationJobObject with
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE, and
    AssignProcessToJobObject. A failure gives one warning and falls back to today's behaviour.
  - The worker ends in `hard_exit` on EOF on Windows.
  - macOS: a kqueue parent-exit thread in `_worker.py`. It cannot be run here: unit-test what you can with mocks, and
    say plainly that the macOS live check waits.
  - Live on the PC, the plan's A1 script. Kill the parent between batches, mid-batch (about 20000 frames) and during
    boot. The worker must be gone within 5 s and the slot free. Write it as `tests/python/test_parent_death.py`. The
    parent is a subprocess you start and kill with `TerminateProcess`, which is how a crashed or killed script ends.
- USING: section 8 (errors and timeouts, the parent-death promise), section 19, and your block in section 20.

## Lane `live`: B4 re-press, B6 window test, B7 pool at two (items 825, 827, 828)

Read the B4, B6 and B7 rows (lines 169, 171 and 172). These are tests only, plus USING section 4 (the re-press rule)
and section 15a (the window promise on Windows).
- B4 `tests/python/test_repress.py`:
  - press, release for 1 frame, press again, for A, then for ZL and ZR, which go through another service;
  - a touch release and a re-tap.
  - The test app's log must show two presses each. If 1 frame is not enough, measure the minimum gap that works,
    and state that in USING.
- B6 `tests/python/test_windows_windows.py` (Windows only; it skips elsewhere with a reason):
  - enumerate every top-level window, hidden ones included, with EnumWindows and GetWindowThreadProcessId through
    ctypes, during a live run;
  - assert that none belongs to the worker's pid or to azhost.exe;
  - first create your own hidden window and require it to be found (the positive control);
  - the foreground check skips over SSH with that reason.
- B7: extend `tests/python/test_pool_live.py` to 2 live copies under a private cap of 2, where a third job waits.
  Keep g1, g2 and g4's checks. This is the only run with 2 copies, so use `--copies 2`.

## Lane `rel`: B0 release check 13 (item 821)

Read the B0 row (line 165) and `tools/release_check.py`, check 13 and `--self-test`. Where the key-header reading copy
is missing, check 13 reports SKIP, or PEND under `--pre-push`, and never a NOTE inside a PASS. Add a self-test case
with the copy absent. Run `$PY -I tools/release_check.py --self-test` on the PC as a fast job. Never read, copy or
print the key-header copy itself; check only whether its path exists.

## Lane `leak`: B9 handle leak per state load (item 829)

Phase A measured it on Windows: in one Emulator, each `load_state` raises the worker's handle count by about 2 (415
to 1023 over 300 loads), while RSS stays flat.
- The scripts are in `<main>/runs/p8/a2/soak.py` (the ctypes GetProcessHandleCount helper); read them.
- Find which handles leak, and whether in host C (`host/state.c` restore path, `host/plat/win_sdcopy.c`
  `azh__copy_tree` / `remove_dir`, Python's `_client.py`) or in the core. Use the handle type breakdown, e.g.
  NtQueryObject or NtQuerySystemInformation(SystemExtendedHandleInformation) for the worker pid, before and after 20
  loads. Also time `replace_sd` alone.
- Then:
  - If the leak is in Python or host C: fix it. Host C is allowed for this lane only. Rebuild on the PC in your lane
    with `make` through the lane's cenv; pclane copies the source, and `vendor/` must come from
    `/d/lazpy/p7/w10/repo/vendor`.
  - Add a live test: 200 loads keep the handle count within 5 % (Windows), and on macOS the open fd count is checked
    the same way via `/dev/fd`, with a skip here.
  - If the leak is in the core: write the evidence and the smallest core patch idea into item 829's notes text in
    your final message. The core is rebuilt only in C6a. The test is then marked xfail with that reason.
- Live runs: one at a time, short (20-300 loads).

## The review (opus), after the five lanes merge

`docs/reviews/phase-8b-as-built.md`: read the diff of phase B on main (`git diff <base>..HEAD`) against the plan's B
rows and USING. Check:
- names, arguments, error attributes and exit codes against the promise;
- that every test can fail (a planted fault where it is cheap);
- the Job object's fallback;
- that the docs claim no more than the tests prove.

Give numbered findings with a severity and a fix. No code edits.
