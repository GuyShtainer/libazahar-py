# Step E as-built review (item laz-310), opus, 2026-11-13

**Verdict: PASS, no blocker. Merge after the five SHOULD fixes (all in E's own files, none in a file step G edits),
then the post-merge F2 timing changes. Nothing is held for G's three files except NICE items.**

Scope: E1 `git diff 6898a4b..a74aaec`, the merge 8c06e26, E2's uncommitted edits (`_slots.py` `DEFAULT_CAP = 2`,
`test_pool_live.py` `own_seed`, new `docs/research/speed-table-e.md`), the run evidence under `<wt>/runs/`, and step
G's commit 32f3b7c (for conflicts). `<wt>` = `../libazahar-py-e`. Read-only, except one pure check:
`nice -n 10 python3 -m pytest -q -m "not slow" tests/python/test_slots.py tests/python/test_pool.py` gave 12 passed
in 1.7 s, and one lsof check with D's fake worker under a private `LAZ_SLOT_DIR` (temp folder under `<wt>/runs/`,
removed after). No emulator started.

## Section 12 checklist

| # | Result | Evidence |
|---|---|---|
| 1 | PASS | `_slots.acquire` (`_slots.py:130-150`): `max_rounds = max(1, ceil(limit/0.1) + 2)` (`:141`) bounds the loop. `_try_round` closes the fd on `BlockingIOError` and on any other exception (`:113-127`). Nothing is written into a lock file (s4 checks size 0, `test_slots.py:89`). `SlotTimeout(HostTimeout)` (`:35-45`) calls D's `HostTimeout.__init__("acquire", seconds)` (`errors.py:32`) and overrides `__str__`, naming the cap and the folder. s1 checks both (`test_slots.py:38-39`). `slot_dir()`, `cap()` and `_timeout_default()` read `os.environ` on every call (`:48-77`); s3 checks a value set after import (`test_slots.py:81-82`). |
| 2 | PASS (one leak path, S5) | `_client.py:126-141`: acquire, `Popen` inside `try`, release on `BaseException` (`:130-135`) and right after `Popen` (`:136-137`). `slot.txt` is written after `Popen` (`:140-141`, `:158-163`). `pass_fds` is `(child_fd,)` or `(child_fd, slot.fd)` (`:150-153`). `_take_slot = (argv is None) if slot is None else bool(slot)` (`:75`), and only s6 passes `slot=True` (`test_slots.py:130`). |
| 3 | PASS | Code path as in 2. lsof check: with D's fake worker spawned `slot=True` under cap 1, the parent had **no** `slot-*.lock` fd, the worker had 1, a second `acquire(timeout=0.2)` raised, and after `close()` the slot was free. `hold_slot.py:43` makes only `slot.fd` inheritable before `execvp` (`:44`). |
| 4 | PASS | `Pool._job` runs `with self._factory(...) as emu` (`pool.py:57`). A constructor failure is closed by `Emulator.__init__`'s own `except BaseException: self.close()` (`emulator.py:87-89`). Results come back in item order (`:68-74`); overrides win (`:56`). p1-p3 check these. |
| 5 | PASS with a note (S1) | `gate_slots` (`test_pool_live.py:39-57`) unsets both variables, takes the real slots, then sets the private folder and cap 3. g2 measures `slot.txt` `acquired - t_kill` (`:97-104`), the time at the lock, not the boot. g4 checks `>= 10` (`:89`). Log: `g2: kill to acquire 0.063 s; slot 1 (killed one: 1)`, `g4: worker nice values [10, 10, 10]`, `2 passed`, rc 0. **But** `min(REAL_SLOTS, _slots.cap())` (`:46`) now holds 2 real slots (DEFAULT_CAP 2) while the gate runs 3 workers. |
| 6 | PASS | `run.c:414-416` logs the timing line only on `rc == AZH_OK`, after `wall_s` is set. The batch logic is unchanged (`:374`, `:378-380` only add sums). `png.c` has no `azh_log` (its includes are stdlib and zlib only) and is still in `TEST_SRC` (`Makefile:42`). `azh_png_level` reads the variable once, with end and range checks (`png.c:21-43`). `log_png_level_once` logs once (`run.c:325-340`). Evidence: 602 `batch frames=` lines in `extra-roundtrip/host.log`, and `png level=1` in `extra-shots-l1/host.log:108`. |
| 7 | PASS | Tick and x-real checks (`speed_table.py:125-126`), plus `stopped_by == "wall_limit"` (`:132`). `cap_rule` (`:42-66`) is unit-tested (`test_slots.py:167-177`). 4-instance rows run only on the cap core (`:295`). The table title says "light scene". `DEFAULT_CAP = 2` (`_slots.py:25`) matches `table.json` `cap`. |
| 8 | PASS | `git -C <wt> diff` touches only `_slots.py` (one line), `test_pool_live.py` (E's own test) and the new doc. |
| 9 | PASS with notes | The package's public names have hints and docstrings. Fds are closed on every path except S5 and the fixture (S1). `hold_slot.py` `parse`/`main` and `speed_table.py` have no type hints (tools, NICE N8). C: every return is checked or cast to `(void)`; the only new globals are file statics (`png.c:16-19`, `run.c:18`). |
| 10 | PASS | `a74aaec` was committed by the main loop (noreply identity). The worktree status shows only E2's 3 paths. `MAIN/build-core/build.exit` dates from 01:06, before E2 (01:56). `build-core/` in `<wt>` is the one symlink. Nothing E wrote is in MAIN. |

Table vs JSON (spot-check). Our core, n=2: the frames and walls in `table.json` give 1585.0 + 1582.4 = 3167.4 total;
x_real 26.49 = 1585.0 / 59.831; ticks/vblank 4481136.0; RSS 795.5 MB (the table uses 1e6). Stock core, n=3: 926.1 +
926.3 + 926.1 = 2778.5; load 35.9/36.3. The gains are 3167.4 / 2177.4 = 1.455 and 3539.9 / 3167.4 = 1.118, and
L(2) = 15.06 < 24, so cap 2 is correct by the fixed rule. Every row reports `wall_limit` and `check_ok`. Host share
0.05-0.07 %.

Privacy: `docs/research/speed-table-e.md` has no `/Users/` path (headings were relativised), no email, and no key
or certificate data. `table.md`/`table.json` hold absolute paths but are under ignored `runs/`.

## The `keys` line

The line is not about key loading. `option_lines` (`speed_table.py:94-101`) keeps whatever follows the first
`"option "` in every host.log line. The host's own count line, `core registered 38 option keys` (`host/options.c:66`;
32 on the stock core), contains `option keys`, so the parse kept the word `keys`. The real option lines are the
`option %s=%s` lines from `options.c:164`.

Our core's n=1 host.log has no line about reading a key file or loading keys. Its one key-related line is the HTTP
service reporting at boot that its client-certificate key is missing (`Service.HTTP <Error> ... DecryptClCertA`).
That is what patches 0007 and 0008 should produce: no default ClCertA, and an empty `GetKeysStream`. The parse would
also pick up `options.c:37`'s `option <k> skipped (...)` warnings. Fix: S2.

## BLOCKER

None.

## SHOULD

- **S1 `tests/python/test_pool_live.py:45-57`: the fixture leaks real slots on a mid-list timeout and is out of step
  with cap 2.**
  - The leak: `held = [_slots.acquire(timeout=1800) for ...]` runs before the `try`. If the 2nd acquire raises
    `SlotTimeout`, the 1st slot's fd is never closed (`Slot` has no finalizer), so this pytest process holds a real
    machine slot until it exits.
  - The cap: with DEFAULT_CAP 2 the gate holds 2 real slots (all of them, so no other user runs) but runs 3
    workers (g1, g3), one above the machine cap.
  - Fix:
    ```python
    held = []
    try:
        for _ in range(min(REAL_SLOTS, _slots.cap())):
            held.append(_slots.acquire(timeout=1800))
        ...  # the setenv lines and the info print
        yield private
    finally:
        for slot in held:
            slot.release()
    ```
    Also add a docstring line: "the gate holds every real slot (`cap()`, 2 by default) and runs 3 workers, one above
    the default cap, on purpose; never run it under an outer `hold_slot.py`" (an outer slot plus the fixture's 2 is
    more than cap 2, so the fixture would wait 1800 s and fail).
- **S2 `tools/speed_table.py:94-101`: the option parse takes non-option lines (the `keys` line).** Fix:
  `OPTION_RE = re.compile(r"\] option (\w+=.*)$")`, then
  `out = [m.group(1).strip() for line in ... if (m := OPTION_RE.search(line))]`. This is the same shape as
  gate_f2's `\boption (\w+)=(\S.*?)\s*$` (`gate_f2.py:314`), which is not affected. Delete the two `keys` lines in
  `docs/research/speed-table-e.md` (`:48`, `:92`).
- **S3 `docs/research/speed-table-e.md`: spec items missing or unclear (section 7, last paragraph).**
  - Line 3-4: add the core versions, `2126.2-lazpy.1` (ours) and `2126.2` (stock), taken from `table.json`
    `core_version`.
  - Line 3: replace "8c06e26 plus E2 edits (uncommitted at writing)" with the E2 commit sha at commit time.
  - Line 5: explain nice 15. The table process itself ran at nice 15 (its launch shell was already at nice 5), and
    the worker keeps a parent's nice above 10 (H2). Under a plain `nice -n 10` it is 10, as g4 measured.
  - Line 39: separate the two cap reasons with "; ".
  - Line 18: add "level 1 was not faster than level 6 on the test app's tiny PNGs (6.21 vs 5.76 ms, 3930 vs 1882
    bytes); PLAN's level-1 win is not shown by this scene; no tuning".
- **S4 `tests/python/test_pool.py:70-73`: p4's "no warning at cap 3" check is silently skipped on a loaded Mac.** It
  was skipped in this review's run (load 37.5), and the E2 runs were at load 32-36. Fix:
  `monkeypatch.setattr(_slots.os, "getloadavg", lambda: (0.0, 0.0, 0.0))` (add the `monkeypatch` argument) and drop
  the `if`.
- **S5 `python/libazahar/_client.py:126-127`: slot leak if `multiprocessing.Pipe()` raises (for example EMFILE)
  after `acquire`.** The fd stays open in the parent, so the parent holds a machine slot for its lifetime. Fix (not a
  G file, so on step-e):
  ```python
  slot = _slots.acquire() if self._take_slot else None
  try:
      parent, child = multiprocessing.Pipe(duplex=True)
  except BaseException:
      if slot is not None:
          slot.release()
      raise
  ```
  This is a change to `_client.py`, which section 4 bars in E2. It is a review fix, which phase-3.md section 4 step 5
  allows on step-e because G does not edit `_client.py`.

## Post-merge changes for F2's timing (main loop, after step-e merges; SHOULD)

E records the wait: `<workdir>/slot.txt` has `waited_s=<x>` (`_client.py:160-163`). The speed table copies it per
instance (`speed_table.py:148`, all 0.0 in this run) and `hold_slot.py` prints it (`:42`). Nothing on `Emulator`
exposes it, and `emulator.py` is a G file, so read `slot.txt`:
`waited = float(dict(p.split("=") for p in (wd / "slot.txt").read_text().split())["waited_s"])`.

1. `tests/gate_f2.py:435-437` (r2 chain): after `emu_b = Emulator(...)`, compute
   `out["slot_wait_b"] = waited(wd / "b")` and `out["t_state"] = time.monotonic() - t0 - out["slot_wait_b"]`. Add
   `slot_wait={...}` to the `r2.<c>.t_state` check text (`:467`).
2. `tests/python/test_state.py:32-52` (`test_state_boot`): subtract `wd_a`'s `waited_s` from `t_core_start` and
   `t_boot`, and `wd_b`'s from `t_state`. Print both waits in `report`. The window between `emu_a.close()` and
   `emu_b`'s acquire lets another session take the freed slot, so `t_state` can include a wait even on a free run.
3. Run gate_f2.py and every pytest **without** an outer `hold_slot.py`; their Emulators take their own slots. Under
   cap 2, an outer slot plus one Emulator uses both slots, so any second user (or `LAZ_MAX_INSTANCES=1`) leaves it
   waiting up to 3600 s (`LAZ_SLOT_TIMEOUT` default).
4. `tests/gate_c.py:46-48` (`run_azhost`, also used by gate_f2 `:285`): take a slot per azhost run in-process. Insert
   `<repo>/python` on `sys.path`, then:
   ```python
   slot = _slots.acquire()
   try:
       child = Popen(cmd, ..., pass_fds=(slot.fd,))
   finally:
       slot.release()
   ```
   Record `slot.waited_s` in the result dict. Done this way, the wait is not inside `communicate(timeout=600)`. A
   `hold_slot.py` prefix would put it inside, which can kill a run as a false "timeout". After this, gate_c.py
   itself is not wrapped either.
5. Correct `docs/plans/phase-3.md` section 4 step 7 ("every azhost command under tools/hold_slot.py ...
   `gate_f2.py`; the full pytest"):
   - wrap only gate-a.sh and gate-b.sh's direct `build/azhost` lines with `tools/hold_slot.py --`, one slot per line (gate-a.sh:56's
     background run is the only azhost alive at that point, so its wrapped slot is freed when it is killed or ends);
   - leave gate_c, gate_f2, the pytest runs and E's live test unwrapped.

## Tests that start 3+ Emulators at once (with DEFAULT_CAP 2)

| Test or gate | At once | Cap it uses | Under cap 2 |
|---|---|---|---|
| `test_pool_live.py` g1/g2/g4 | 3 alive + a 4th waiting | private folder, cap 3 (`:50-51`), after holding the real slots | runs. It holds 2 real slots and runs 3 (S1); it waits up to 1800 s if another user holds a real slot |
| `test_pool_live.py` g3 | 3 (Pool(3)) | same private cap 3 | same as above |
| `tools/speed_table.py` n=3, n=4 rows | 3, 4 | sets `LAZ_MAX_INSTANCES=4` for itself (`:281`), real folder | runs. Slots 2-3 are above the default cap, which the module doc allows (cap-5 example) |

Every other live test or gate (D's `test_state.py`, `test_api.py`, `test_live_errors.py`; G's
`test_memory_live.py`; gate_f2 r2 and cross) runs one Emulator at a time. `test_state_boot` and r2 close emu_a
before emu_b. No other test sets a cap. `Pool(n > cap)` only warns (p4).

## NICE

- N1 `_client.py:121-125`: also unlink a stale `slot.txt` beside `host.map` at spawn. In a reused workdir the old
  file stays visible while the new spawn waits.
- N2 `_slots.py:80-101`: `Slot` has no finalizer. An unreleased `Slot` that is dropped keeps the lock for the
  process's life. Add `def __del__(self): self.release()` (safe: `release` is idempotent).
- N3 `_slots.py:70-77`, `:141`: `LAZ_SLOT_TIMEOUT=inf` raises `OverflowError` from `math.ceil`, and `nan` raises a
  `ValueError` that does not name the variable. Reject non-finite or negative values in `_timeout_default` with a
  ValueError that names it.
- N4 `host/run.c:414-416` (**held**): one host.log line per batch. The round trip wrote 602, so a `run(1)`-per-frame
  harness grows host.log by about a line per frame. This follows the spec; document it in USING.md (Phase 4), or
  gate the line on `frames_run > 1` if Gen3D minds.
- N5 `host/run.c:18`, `:123` (**held**): `last_run_ns` passes the retro_run wall through a file static. An
  out-parameter of `azh__run_one_frame` would be explicit. Cosmetic.
- N6 `python/libazahar/__init__.py:13` (**held**): the `__all__` line is 150 chars. G rewrites these lines (32f3b7c),
  so fold the wrap into G's version on main.
- N7 `tests/python/test_slots.py`:
  - `:107`: the first `client = make(work, "ok")` is dead.
  - `:143`, `:151`: these `os.environ.update`/`pop` calls should be `monkeypatch.setenv`. As written, they pop a
    caller's pre-set `LAZ_SLOT_DIR` for the rest of the session.
  - `:172-177`: add the "stop at 3 for load" case, where n=4's load fails and the cap is 3.
- N8 `tools/hold_slot.py:44-45`: `return 127` is unreachable. A missing command gives a traceback and exit 1; wrap
  `execvp` in `except OSError` (print, return 127). Also add hints on `parse`/`main`.
- N9 `tests/python/test_pool_live.py`:
  - `:99`: the join timeout uses `RUN_FRAMES` (a frame count) as seconds. Use a named `RUN_GRACE_S = 60`.
  - `:127`: `seed` is now unused in g3.
- N10 `_worker.py` (**held until step-g merges**: G edits `_worker.py`): the worker keeps the slot fd inheritable. If
  the core ever spawned a process, that process would keep the slot after the worker died. Use
  `os.set_inheritable(int(sys.argv[3]), False)` when argv[3] is present.
- N11 `tools/speed_table.py:281`: with its own cap 4, a row can run beside two cap-2 users' instances without
  waiting. The recorded waits are 0.0, so a busy row does not show as one. Say so in the tool's docstring; the load
  columns are the evidence.

## Conflicts with step G

G's commit 32f3b7c edits `host/run.c` (watch hooks inside `run_frames`, after E's `core_ns` sum; the watch time
counts as `host_ms`, which is correct), `host/azh_pure.h` and `__init__.py` on top of E1. It also edits
`emulator.py`, `_worker.py`, `errors.py` and `_map.py`. Every SHOULD above is in a file G does not touch
(`test_pool_live.py`, `speed_table.py`, the research doc, `test_pool.py`, `_client.py`), so step-e merges cleanly
in either order. The held items (N4-N6, N10) go on main after step-g merges.
