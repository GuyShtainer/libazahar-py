# Phase 8 B as-built review

**Verdict: ready with changes.** No blockers. Seven majors, 18 minors. Nothing breaks the 1.x promise or the frozen
`libazahar.__all__`. The Windows Job object is correct as built: struct layout, handle lifetime, and a fallback that
never kills the wrong process. Six of the majors are about tests and docs: some claims in the docs go further than the
tests show, a few tests cannot fail or will fail on another file system, and the macOS wiring has no test at all. The
seventh is the verdict example, which does not follow the exit table it is cited for. Fix the majors before the
phase B items move to done. The minors can land in the same sonnet pass or go to Phase C.

Reviewed: `git diff 637d911..HEAD -- python tests tools docs/USING.md examples` on main (merge ee6b04d). Also read: the
plan's B rows (`docs/plans/phase-8.md`), the lane briefs, items 821 to 829, the Python golden rules, and `host/png.c`,
`host/frame.c` and `host/azhost_main.c`, where they back a claim. Read-only: nothing was run (no emulator, no pytest).

## Findings

### Major

**1. The verdict example does not exit by the table USING section 3 says it follows.**
- Where: docs/USING.md:69-72; examples/verdict.py:49-58.
- What is wrong:
  - USING says the example exits 10 for a guest exit and 11 for a guest error. The code maps `GuestError` to 1
    (EXIT_FAILED).
  - A guest exit makes `run_until` return `stopped_by == "guest_exited"`, which falls into the "no PASS line" branch
    and also exits 1.
  - The catch-all `except LibAzaharError` exits 13 ("worker or host crashed") for `HostError`, including "cannot load
    the host", for `StateError` and for `NeedsLazpyCore`. None of these is a crash.
  - `SlotTimeout` is a `HostTimeout`, so it exits 12 "timed out, worker killed", but no worker was ever started.
  - An uncaught Python exception also exits 1, so a bug in the script itself reads as "the test failed".
- Fix:
  - In the example: `GuestError` exits 11; `stopped_by == "guest_exited"` exits 10; catch `SlotTimeout` before
    `HostTimeout` and give it its own line (or 12, with honest text); send `HostError` and `StateError` to a
    "harness error" code, or document 13 as "crashed or host error".
  - In USING section 3: say that an uncaught exception in a script exits 1.
  - Or change the USING sentence to match the code, but then the "one table" claim goes.

**2. The new live evidence test passes on NTFS by timing luck and will fail on APFS or ext4.**
- Where: tests/python/test_live_errors.py:59; python/libazahar/errors.py:41-47; host/frame.c:148,154.
- What is wrong:
  - `newest_shot` picks the PNG with the largest `(st_mtime_ns, name)`.
  - The host writes `<prefix>_top.png` and then `<prefix>_bottom.png`, so on a file system with fine timestamps the
    bottom file is newer.
  - The test asserts the top file's name (`taken[0]`). It passed on the PC only because the two NTFS timestamps tied
    and the name tie-break (`top` > `bottom`) chose top.
  - It will fail on the Mac, and it can flake on Windows when the two writes fall in different clock ticks.
- Fix: assert `any(p.name in str(error) for p in taken)`. Or define the newest shot by its prefix and name the pair
  (better evidence, and a one-line change in `attach_evidence`).

**3. The strict xfail on the handle test hides every failure, not just the leak.**
- Where: tests/python/test_handles_live.py:52-55.
- What is wrong:
  - `xfail(strict=True)` without `raises=` turns any exception in the body into "xfailed". That covers a boot
    failure, a `StateError` from `load_state`, and an `OSError` from `OpenProcess` or `GetProcessHandleCount`.
  - Windows is the only platform where this case runs today, so a broken test shows as expected and green.
  - The docstring and the xfail reason cite `LEAK-NOTES.md`. That file is not in the repo: its text was moved into
    item 829.
- Fix: `raises=AssertionError`, and cite item 829 instead of LEAK-NOTES.md.

**4. USING 10a says the clock base is fixed and shifts with the seed. The test leaves the clock field out.**
- Where: docs/USING.md:215; tests/python/test_determinism.py:16.
- What is wrong:
  - The row says the fixed start time (`citra_init_clock=FixedTime`, `citra_init_time`) reaches `osGetTime` and
    `time()`, and that "the guest's clock shifts with" the tick seed.
  - `SAME` leaves out `t`, the test app's `osGetTime()` reading, with the note "the app's own clock reading".
  - So the clock half of the row has never been checked. If `t` does repeat, the test is weaker than it needs to be.
    If it does not, the row is wrong.
- Fix: add `t` to `SAME`, and in `test_two_tick_seeds_differ` assert how `t` changes between the two seeds. If `t`
  does not repeat, rewrite the row to say the clock is not fixed, or not checked.

**5. USING 15a promises that `azhost.exe` opens no window, but the test never runs `azhost.exe`.**
- Where: docs/USING.md:413-416; tests/python/test_windows_windows.py:91-103, 144-156.
- What is wrong:
  - `worker_pids` adds "every azhost.exe that is a child of this test process". The test starts no `azhost.exe`, so
    that set is always empty and the azhost half of the claim (and of the B6 row) is untested.
  - The windows are listed only between batches (after `emu.run` returns), but the docstring says "mid-run". A window
    that lives only inside a batch would be missed.
- Fix:
  - Add a case that starts `azhost.exe` (a few hundred frames) and lists windows while it runs, or drop
    `azhost.exe` from the USING sentence.
  - For the worker, list the windows from a thread during one long batch, for example `run(600)`.

**6. On macOS, nothing tests that the real worker starts its parent watch.**
- Where: python/libazahar/_worker.py:234-235; tests/python/fakeworker.py:25-28.
- What is wrong:
  - The fake worker calls `_worker.start_parent_watch(os.getppid())` itself. So the fast mid-batch test on macOS
    proves the kqueue thread, but not the wiring in `_worker.main`.
  - A fault planted there (delete line 235) passes every fast test on macOS. Only the live macOS cases would catch
    it, and they have not run.
- Fix (cheap and fast): a test that calls `_worker.main` with `LAZ_HOST` unset over a `multiprocessing.Pipe`. It sends
  `fatal` and returns 1. With `_worker.start_parent_watch` monkeypatched to record its argument, assert it was called
  once with `os.getppid()` off Windows and not at all on Windows. Or move the setup into one `_worker` function that
  both `main` and the fake worker call.

**7. The "in a job" test cannot fail, and the second worker's job assignment is never checked.**
- Where: tests/python/test_parent_death.py:94-106; python/libazahar/_job.py:198-221.
- What is wrong:
  - `IsProcessInJob(handle, NULL, ...)` is TRUE when the process is in any job. Over OpenSSH, and on CI runners, every
    child is already in the session's job, so the test passes with `_job.assign` removed. It also never checks
    kill-on-close, although that is in its name.
  - The real guard is the fast mid-batch case: item 826 says it failed with the assignment removed. But that case
    starts one worker.
  - From the second worker on, the parent is often itself in a job (SSH, CI). Each later worker then starts in that
    outer job and must be moved down into ours, the nested-job path.
  - If that assignment failed, the only sign would be one `RuntimeWarning`, and no test asserts that there is none.
    The pool tests (2 and 3 copies) would pass either way.
- Fix:
  - Pass `_job._job` as the job handle, and read `JobObjectExtendedLimitInformation` back with
    `QueryInformationJobObject` to check `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`.
  - Start two fake workers in one test with `warnings.simplefilter("error", RuntimeWarning)`, and assert that both
    are in our job.

### Minor

**8. The fallback to today's behaviour is tested only inside `assign`.**
- Where: tests/python/test_parent_death.py:109-125; python/libazahar/_worker.py:128-133, 259-272.
- What is wrong:
  - The test proves one warning and a False return. It does not show that a spawn whose assignment fails still
    works, or that the worker then ends on EOF.
  - The fake worker does not use `_serve`, so `_leave` (the Windows `hard_exit` on EOF) has no coverage.
- Fix: in `FAKE_PARENT` and `LIVE_PARENT`, an env switch that sets `_job.assign = lambda proc: False`. Then run the
  between-batches case on Windows: the worker must be gone within 5 s and the slot free. That is one live run, cheap.

**9. If the job assignment raises anything but `OSError`, the started worker is left running and holds its slot.**
- Where: python/libazahar/_job.py:218; python/libazahar/_client.py:192-196, 148-154.
- What is wrong:
  - `assign` catches only `OSError`. A `ctypes.ArgumentError` or `AttributeError` would come out of `_popen_windows`
    after `Popen` succeeded.
  - `_spawn`'s handler then closes the pipe and the parent's slot handle, but the process is not yet in
    `self._proc`, so it is never killed. The orphan holds the slot lock until the job closes, or forever if there is
    no job.
  - The plan says a failure must leave today's behaviour.
- Fix: in `_popen_windows`, on any exception after `Popen`, kill and wait for `proc` before re-raising. Or catch
  `(OSError, ctypes.ArgumentError, AttributeError)` in `assign`.

**10. The live "during boot" case probably kills the parent before the core starts.**
- Where: tests/python/test_parent_death.py:226-236, 250-252.
- What is wrong: `slot.txt` is written right after `Popen`, and the kill comes 0.3 s later. That is during Python
  start-up or the hello, before the long `start` call, so the case does not show a death inside `azh_start`.
- Fix: wait until `host.log` exists, or the map shows that `start` has begun, and then kill.

**11. The live parent-death cases never check that the slot was held before the kill.**
- Where: tests/python/test_parent_death.py:207-213, 237.
- What is wrong:
  - `slot_is_free` would also pass if the worker took no slot, or took one in another folder.
  - It catches `except Exception`, against golden rule 3.
- Fix: before the kill, assert that `_slots.acquire(timeout=0.5)` raises `SlotTimeout`. In `slot_is_free`, catch only
  `SlotTimeout`.

**12. The held-input test cannot tell "kept" from "restored from the state".**
- Where: tests/python/test_determinism.py:67-80; docs/USING.md:220.
- What is wrong:
  - A is held both when the state is saved and when it is loaded. So a `load_state` that restored the input stored
    in the state would pass too.
  - USING claims "load_state does not change the held buttons".
- Fix: save with nothing held, then hold A, load, run: A must still be down. Use `int(Buttons.A)` in place of `1`.

**13. The newest-shot unit test cannot catch a pick by name.**
- Where: tests/python/test_errors.py:83-94.
- What is wrong: the file with the newer mtime (`z_top.png`) is also last by name, so a `newest_shot` that sorted by
  name would pass.
- Fix: make the older mtime belong to the later name (set `z_` back to time 1 and keep `a_` new).

**14. Nothing tests the evidence that `Emulator` itself attaches.**
- Where: python/libazahar/emulator.py:339, 266, 314, 397, 465.
- What is wrong: the fast tests drive `WorkerClient` only, and the live crash test covers only the client path.
  Removing any of these `annotate` calls fails no test.
- Fix (cheap): in `test_api.py::test_closed_emulator_raises`, assert `log_path == workdir / "host.log"`. In an
  existing live guest-error test, assert `.workdir` and `.log_path`.

**15. USING section 8 says every live-instance error carries the evidence, but some do not.**
- Where: python/libazahar/errors.py:155-169; python/libazahar/emulator.py:177, 185, 203; python/libazahar/_map.py:101-105.
- What is wrong:
  - `SlotTimeout` gets the fields (it is a `HostTimeout` and is raised inside `spawn`). But its own `__str__` drops
    the evidence line, and its `__reduce__` drops the fields when it is pickled.
  - Some `HostError`s carry nothing: "host library ... not found" and "cannot make the working folder" (raised
    before the client exists), and the `_map.py` watch-row errors.
  - The "core ... is missing" `BootError` names a `host.log` that does not exist yet.
- Fix: do not attach evidence to `SlotTimeout`, since no worker exists yet, and say so. Word USING section 8 as
  "errors raised once the worker has started", or attach evidence at the extra sites.

**16. Every annotated error lists the whole `shots/` tree.**
- Where: python/libazahar/errors.py:50-58.
- What is wrong: `attach_evidence` runs `rglob` and a `stat` per PNG for every error. A script that probes guest
  memory and catches `GuestMemoryError` page by page pays O(shots) each time.
- Fix: keep only the workdir, and look up the newest shot lazily in `__str__`, caching the answer.

**17. Settle the images API names now: they freeze at v1.2.0.**
- Where: python/libazahar/images.py:557, 612-636.
- What is wrong:
  - `CompareResult.max_delta` is the measured largest delta, while `compare(max_delta=)` is the limit. One name, two
    meanings.
  - `write_diff` marks every pixel that differs, not the ones over the limit, so a diff made with a tolerance shows
    pixels that passed.
  - `_differs` is a parameter of the public dataclass constructor, and `write_diff` on a result built by hand raises
    `AttributeError`.
  - `read_png` has a public name, is not in `__all__`, and is used by the tests.
- Fix: rename the field (for example `largest_delta`), or document both meanings side by side. Decide which pixels
  `write_diff` marks (perhaps an `over_only=` keyword). Give `_differs` `init=False`, set through a private factory.
  Rename `read_png` to `_read_png`, or export it and document it.

**18. The new names are not frozen yet.**
- Where: tests/python/test_api.py:133-135.
- What is wrong: only `images.__all__` is frozen. Nothing freezes `compare`'s keyword-only limits, the
  `CompareResult` fields, or `.workdir` and `.log_path` on the seven error classes. Item 823 notes the last gap.
- Fix: three asserts, using `inspect.signature(images.compare)` with KEYWORD_ONLY limits,
  `dataclasses.fields(CompareResult)`, and `hasattr` on each class in `EVIDENCE_TYPES`.

**19. No test reads a PNG written by the host through `images`.**
- Where: tests/python/test_images.py (synthetic PNGs only).
- What is wrong:
  - The claim that the reader matches `host/png.c` rests on reading the source. It does match: one IDAT, filter 0,
    8-bit RGBA.
  - Comparing a `screens()` array with a shot PNG, which USING section 20 implies works, is untested.
- Fix: `test_c_checks.py:153` already has a shot and screens from the same frame. Add
  `images.compare(first.shots[300].top, <top array>).within`.

**20. USING 19's outer-timeout advice names a `timeout` command that macOS and Windows lack.**
- Where: docs/USING.md:472-474.
- What is wrong:
  - macOS ships no `timeout` (Homebrew coreutils has `gtimeout`), and Windows' `timeout` only waits.
  - The sentence also reads as if Python scripts need an outer timeout. In Python, the heartbeat `timeout` does
    catch a hang inside one frame.
- Fix: limit the sentence to `azhost`, and name the tools on each system (coreutils `timeout` or `gtimeout`, a
  `subprocess.run(timeout=)` wrapper, or PowerShell `Wait-Process -Timeout`).

**21. The USING 19 error table is missing some errors.**
- Where: docs/USING.md:479-494.
- What is wrong: the plan asks for "each error". The table has no `NeedsLazpyCore` and no `ArgumentError`. It also
  lacks the parent-side `HostError` texts: "host library ... not found", "cannot make the working folder" and
  "cannot read the option profile".
- Fix: add those rows.

**22. The release check self-test is not in CI.**
- Where: tools/release_check.py:1444-1468; .github/workflows/.
- What is wrong: the B0 gate says "`--self-test` (CI fast)", but no workflow runs it.
- Fix: one step in `test.yml`: `python3 -I tools/release_check.py --self-test`.

**23. The verdict example was never run for its failure codes.**
- Where: examples/verdict.py; item 824.
- What is wrong:
  - The B3 gate names "the example in docs_check", but `docs_check` only reads the example's text.
  - Item 824 says that 1, 12 and 13 were not run.
- Fix: three cheap plants, each one live run of about 600 frames:
  - an unmatched `PASS_TEXT` must exit 1;
  - a very small `timeout=` on `run_until` must exit 12;
  - a timer that hard-kills `emu.pid` must exit 13.
  An env override in the example would let a small live test run all three.

**24. In USING 8 and 10a, the wording claims more than the tests show.**
- Where: docs/USING.md:169-175, 206-224.
- What is wrong:
  - Section 8 opens by stating macOS parent death as fact, and says only at the end of the paragraph that its live
    check has not run.
  - Section 10a mixes rows measured by the test with rows read from the profile and the code (random bytes, console
    ID and MAC, workdir reuse; item 822's note) and does not say which is which.
  - It advises a fresh folder for repeatable runs, while also saying that a fresh folder draws a random console ID.
    It gives no recipe for an app that reads the console ID. `fresh_sd=True` on a reused folder keeps the config.
- Fix: put "not yet run live" in the first sentence of section 8. Mark each 10a row as measured or as from the code,
  and add the `fresh_sd=True` recipe.

**25. Small style and golden-rule points.**
- tests/python/test_pool_live.py:40-41: the `hold_real_then_private` docstring still says "cap 3". The `fourth`
  names in `check_cap_kill_and_nice` mean "the one past the cap".
- examples/verdict.py:39, 57: lines over the repo's 120 columns. `finish` never returns, so type it `NoReturn`.
- python/libazahar/errors.py:33: the `EVIDENCE_TYPES: tuple = ()` placeholder is reassigned at line 172. Define it
  once, after the classes.
- python/libazahar/_job.py:142: `_failed` means "warned". Name it that.
- python/libazahar/images.py:579: `zlib.decompress` has no bound. Use
  `zlib.decompressobj().decompress(data, row * height + 1)`, so a hostile file cannot use up memory before the size
  check.
- python/libazahar/_worker.py:164-202: the watch calls `os._exit(0)` without a word. Write one line to stderr first
  (it lands in `worker.err`), such as "parent N gone: exiting". An `OSError` from `kqueue()` (for example EMFILE) ends
  the thread with only a traceback, and the worker falls back to EOF without saying so.

## Checked and sound

- **Job object struct layout (64-bit Windows).**
  - `JOBOBJECT_BASIC_LIMIT_INFORMATION` comes to 64 bytes: two 8-byte fields, `LimitFlags` plus 4 bytes of padding,
    two `SIZE_T`, `ActiveProcessLimit` plus 4 bytes of padding, `ULONG_PTR`, and two `DWORD`.
  - `IO_COUNTERS` is 48 bytes and the four `SIZE_T` add 32, so `JOBOBJECT_EXTENDED_LIMIT_INFORMATION` is 144 bytes.
    ctypes pads it the same way, and it also comes out right on 32-bit (112 bytes).
  - An `assert ctypes.sizeof(_Extended) == (144 if 64-bit else 112)` would cost one line.
- **Rights and job handle.** `OpenProcess` asks for `PROCESS_SET_QUOTA | PROCESS_TERMINATE`, which
  `AssignProcessToJobObject` needs.
  - The job handle is created non-inheritable (`lpJobAttributes` NULL), lives in a module global, and is closed only
    when the process ends. That is what kill-on-close needs.
  - Workers receive only the pipe and slot handles (`handle_list`), so no worker holds a copy of the job.
- **No false kill from a reused pid.** `Popen` keeps its process handle open, so the pid cannot be reused before
  `OpenProcess`. The worker starts no children, so the gap between `Popen` and the assignment is harmless.
- **Nested jobs.**
  - Windows 8 and later allow nesting, so assigning the first worker (already in an SSH or CI job) works, and the PC's
    live runs prove it.
  - On older Windows the assignment fails, and the code gives the promised one warning and falls back.
  - The second-worker path is open (finding 7).
- **One warning only.** It is given once per process. Later failures are silent, as the plan asks.
- **kqueue watch races.**
  - A parent that dies before registration gives `ProcessLookupError`.
  - A parent that dies after `getppid` in `main`, but leaves a zombie or a reused pid, is caught by the `getppid`
    recheck after registration: the worker has already been reparented.
  - `ppid <= 1` at start exits at once.
  - `kqueue.control` releases the GIL, and ctypes releases it during a batch, so the thread can run mid-batch.
  - `os._exit` from a non-main thread ends the whole process.
- **Slot lock on a parent death.**
  - POSIX: the worker holds the only remaining reference to the locked open file description, because the parent
    released its copy right after `Popen`. `_exit` closes it and the `flock` goes with it.
  - Windows: the slot handle closes with the process. The live cases there showed the slot free.
- **`_serve` on EOF or a broken pipe.** It now ends cleanly instead of crashing on `send`. Windows uses `hard_exit`
  there, as after `close`.
- **Pickling.** It holds for all seven classes: a three-item `__reduce__` and `BaseException.__setstate__`. Errors
  without evidence round-trip unchanged.
- **Release check 13.** SKIP, or PEND under `--pre-push`, and the self-test checks both lines and both exit codes. It
  reads only whether the path exists.
- **1.x promise.**
  - `libazahar.__all__` is unchanged, and `images` stays outside it.
  - `azhost`'s exit codes keep their meanings, and 1, 12 and 13 are not used by `host/azhost_main.c`.
  - `str(error)` gains a trailing line, while its opening text is unchanged. Code that compares the whole
    `str(error)` with `==` would see that new line. Note it in the changelog.
- **Re-press tests (B4).** They can fail: a lost one-frame release gives a count of 1.
- **Window test positive control (B6).** It is real. The window is made on the same desktop the worker inherits.
- **B7.** It keeps g1, g2 and g4 at a cap of 2.

## Not judged without a run

- **macOS:** the fast mid-batch case with the real `select.kqueue` (`test.yml`, macOS), and the three live
  parent-death cases.
- **Windows nested jobs:** whether the second and later workers' assignments succeed when the parent is itself in a
  job (SSH, the CI runner), and on an interactive desktop with no outer job. No `RuntimeWarning` in the 2- and 3-copy
  pool runs would answer it.
- **Clock field:** whether `t` (`osGetTime`) repeats across two fresh runs, and how it moves with the tick seed
  (finding 4).
- **Live evidence test:** the test of finding 2 on APFS (expected to fail as written).
- **Pool:** g1, g2 and g4 at 3 copies after the refactor (item 828).
- **Verdict example:** exits 1, 12 and 13 (finding 23).
- **Window tests:** the foreground check on a logged-in desktop, and any window `azhost.exe` might make (finding 5).
- **Handle test:** the macOS and Linux descriptor variant.
- **Release gates:** `test-windows.yml` on the merge commit, and the phase's full PC gate.
