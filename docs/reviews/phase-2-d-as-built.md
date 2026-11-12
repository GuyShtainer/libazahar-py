# Phase 2 step D: as-built review (opus, 2026-11-12)

Subject: branch `step-d` in `../libazahar-py-d` at 88cdbe6 (D1+D2 b24c436, D3 c1e614e + 88cdbe6, main merged at
1cf3609). Brief: `docs/plans/phase-d.md` revision 2 (section 13 checklist), `docs/plans/phase-2.md` D row and P1-P6.
Builder reports and rulings: item 220 "Lessons and notes". Phase 3 holds: `docs/plans/phase-3.md` section 6.

Verdict: **mergeable after S1-S6** (all small, D's own files, no header change; no blocker). After the fixes, rerun
the fast suite, then the full gate once (about 70 s) and the planted red once (about 10 s, N7). Counts: blocker 0,
should fix 6, nice 18.

Re-checked by this review in the D tree (no emulator run): `make check` clean, `make` up to date, `make test-host`
"307743 checks, 0 failed"; `python3 -m pytest -q -m "not slow" tests/python` "48 passed, 21 deselected in 2.54s";
`test_client.py -s`: fake round trip 0.014 ms, 691,200-byte map copy 0.142 ms, segv death to raise 0.065 s, hang
stop to raise 1.00 s; `runs/d3-venv/bin/python -I` imports 0.1.0.dev0 and `_paths` resolves the D repo and its
`build/libazhost.dylib`. Checklist items 1-11 of phase-d.md section 13 hold, except where a finding says otherwise.

## 1. Gates: tested, able to fail, numbers against the logs

| Gate | Test | Can it fail? | Log |
|---|---|---|---|
| make check, make, test-host | D2's `test_statemeta.c` (round trip, each key missing and repeated, bad ints, over-long text, bad sha, files) | yes | rerun here: 307743 checks |
| C (a)-(f) through Python | `test_c_checks.py` (10) | yes; same checkers as gate_c (`checks_c.offsets_ok`, f3 0..10, c3 bound from batch 1, d4 `screens()` bytes == PNG bytes) | `runs/d-cc.log`: a2 hid m=0 {0: 1, 1: 29}, irrst m=1 {1: 6}, circle m=1 {1: 5}, b touch m=2 {2: 40}, c3 3.00 s vs 4.00 s; our core `runs/d3-lazpy.log` 10 passed |
| SIGSEGV to HostCrashed < 1 s | `test_live_errors.py` asserts `signal == SIGSEGV`, delay < 1.0, closed | yes | `runs/d3-live.log` 0.428 s |
| SIGSTOP to HostTimeout 2.8-6 s, then no process | asserts both | yes | 3.11 s |
| 200,000 frames, `stopped_by == "frames"` | asserts both | yes | 39.5 s |
| other app refused before any frame | `test_other_app` (map `frame_total` 0, meta app named, then `LAZ_STATE_ANY_APP=1` boots) | yes | in the full run |
| state boot: same fields, log bytes, counters, markers, under 2.5 s (Guy) | `test_state_boot` (at least 590 lines compared) + `test_state_boot_wall_ratio` | yes, but the bound sits in a second test fed by a module global (S2) | `runs/d-pytest/state-times.txt` (21:04) |
| venv `pip install -e .` imports | `runs/d-venv`, `runs/d3-venv` | yes | rechecked here |
| planted red | `LAZ_TEST_PLANT_RED=1` shifts B's keys by one v | yes: "12 lines differ, first (6028 ...), (6077 ...)" | `runs/d3-red.log` (20:07, before the final test edits: N7) |
| full suite, 0 skipped | 69 tests | yes | `runs/d3-full.log` "69 passed in 70.35s", header `kind=stock` |

The numbers match the logs, with one correction: the item's "D fixes" state times (t_boot 4.98, t_state 1.55, ratio
0.311, drain 440.5, unserialize 595.6) are not on disk any more; the 21:04 exit-fix run overwrote
`state-times.txt` with `t_core_start=0.40 t_boot=5.09 t_state=1.62 ratio=0.317 fixed_ratio=0.259 k=0
frame_total=6030 v_save=6027`, `state load meta_ms=0.0 sha_ms=0.1 read_ms=0.2 drain_ms=433.0 sd_ms=0.5
unserialize_ms=643.6 bytes=266797`, B's `sys/` seeded with `Azahar`, `Azahar/cheats`, `Azahar/nand`,
`Azahar/shaders`, `Azahar/sysdata`. Quote those in the Evidence line. k was 0 in every save, so the
`frame_total += k` branch never ran with k > 0 (N6). The SIGSEGV and SIGSTOP delays come from the 20:06 run (an
earlier worker, before the nice change); the final run asserts the same bounds under `-q` but prints nothing.

## 2. Should fix

- **S1. `python/libazahar/emulator.py:154-158` (run): the held state goes wrong after an early stop.** `fold` returns
  the held state after *every* input of the batch, and `self._held = held` keeps it even when the batch stopped
  early (sd_text, wall_limit, break, guest_error). The host applies records only up to `frames_run`
  (`host/run.c:216-225`, 319-324), so `run_until(..., inputs=[(1, Buttons.A), (500, Buttons(0))])` that stops at
  frame 50 leaves A held in the host while Python thinks nothing is held; the next batch's records and `set_input`
  then start from the wrong state. Fix, in `inputs.py` (add `"held_after"` to `__all__`):
  ```python
  def held_after(records: "array[int]", frames_run: int, held: Held) -> Held:
      """The held state the host has after a batch that ran ``frames_run`` frames: its last record at or before then,
      else ``held`` (the state before the batch)."""
      step = _abi.AZH_INPUT_INTS
      for start in range(len(records) - step, -1, -step):
          if records[start] <= frames_run:
              return Held(*records[start + 1:start + step])
      return held
  ```
  In `emulator.py` `run`: keep `prev = self._held` before the request, delete `self._held = held` (line 158), and
  set `self._held = held_after(records, payload["frames"], prev)` in the `exited` branch and
  `self._held = held_after(records, result.frames, prev)` right after `result = self._result(...)` (before the
  `guest_error` raise). The `held` from `fold` is then unused (`records, _ = fold(...)`). Test in `test_inputs.py`:
  ```python
  def test_held_after_an_early_stop():
      out, _ = fold([(2, Buttons.A), (50, Touch(5, 6))], 100, Held())
      assert held_after(out, 10, Held()) == Held(buttons=1)
      assert held_after(out, 50, Held()) == Held(1, 5, 6, 1, 0, 0)
      assert held_after(out, 1, Held(buttons=8)) == Held(buttons=8)
  ```
  The run docstring's "which stays after the batch" becomes "the state reached by the last frame run stays".

- **S2. `tests/python/test_state.py:28, 70, 85-88`: the 2.5 s gate lives in a second test fed by a module global.**
  `TIMES` is module-level mutable state shared between tests (Python rule 7); `-k wall_ratio` alone, a reordering
  plugin, or a failure before line 70 turns the gate into "did not run first". The split was for the xfail, which is
  gone. Fix: delete `TIMES` (line 28), line 70 and `test_state_boot_wall_ratio` (85-88); at the end of
  `test_state_boot` add
  ```python
      assert t_state < 2.5, f"state boot {t_state:.2f} s, Guy's bound 2.5 s on the test app"
  ```
  (after the report is written, so a slow run still records its times). The full count stays 69 with S1's test.

- **S3. `tests/python/test_state.py:121-122` (test_newer_abi_refused): the literal `"abi=2\n"`.** It breaks when G
  raises the ABI (phase-3 D9). Fix: `from libazahar import _abi`, then
  ```python
      line = f"abi={_abi.AZH_ABI_VERSION}\n"
      assert line in text
      meta.write_text(text.replace(line, f"abi={_abi.AZH_ABI_VERSION + 1}\n", 1))
  ```
  and add one case for the low end (abi 1 refused) with the same `pytest.raises(StateError, match="abi")`.

- **S4. `host/state.c:505-521` (azh__state_load): a failure after the SD folder was replaced leaves a live,
  inconsistent instance.** If the copy back fails part way or `retro_unserialize` refuses, the SD folder is the
  snapshot (or half of it) while the guest runs on from the old state with its files reopened, and every later call
  works. A state boot is safe (api.c marks the instance DEAD). Fix: add `int replaced;` to `restore_t`, set
  `r->replaced = 1;` in `restore_core` just before `rc = replace_sd(path);`, and end `azh__state_load` with
  ```c
      rc = restore_apply(path, &r);
      if (rc != AZH_OK && r.replaced != 0) {
          azh_g.phase = AZH_PH_DEAD;      /* SD replaced, guest not restored: nothing after this is trustworthy */
          azh_log(AZH_LOG_ERROR, "load_state failed after the SD folder was replaced; the instance is closed");
      }
      return rc;
  ```
  In USING.md section 10 add: "a `load_state` that fails after the SD folder was replaced leaves the instance
  unusable (later calls raise HostError); close it and boot again."

- **S5. `docs/USING.md`: four lines not right.**
  - Lines 17-18 and 86, the seed order: line 17 says the seed is copied "before boot" and line 86 "restores the SD
    snapshot (after any seed)", which reads as the snapshot winning. The code (`emulator.py:93-104`) copies the seed
    after a state boot, so seed files land on top of the snapshot. Replace line 17-18's sentence with "`sd_seed` is a
    folder (never named `sdmc`) whose contents are copied onto the SD card: before boot, or with `state=` after the
    restore, so seed files land on top of the snapshot." and line 86's "(after any seed)" with "(then the seed on
    top)".
  - `wall_ms_mean` is not in USING.md at all (Phase 3 review 1 asked for it; H4). Add to section 3: "`RunResult.wall_s`
    is the batch's wall time; `azhost run` prints one summary per batch, `frames= wall= fps= shots= stop= first= last=
    vblanks= wall_ms_mean= batch= msg=` (the mean frame time; there is no max)."
  - Line 90 quotes test-app wall times against the doc's own line 4 rule, and the 5.7 s is stale (the final run:
    5.09 s). Replace the sentence with "Gate on the test app (Guy's ruling): a state boot takes under 2.5 s (1.6 s
    measured); a real game's state is larger, so time your own." and wrap to 120 columns.
  - Lines 63-65 tell users to "compare `msg_seq`", which no public API exposes. Replace with "Messages that arrive while
    the host drains for a savestate are not reported as stops; each is in `host.log` as a `core message:` line."

- **S6. `docs/map/code.md`: `.venv/` is not named.** USING.md's install makes `.venv/` at the top level, and
  map_check counts on-disk top-level entries even when ignored (the builder's own lesson), so following the doc in
  MAIN makes `map_check` fail. Fix: in the "Ignored, never committed" line add `.venv/` (the editable-install venv)
  next to `.pytest_cache/`, and rewrap the two lines D lengthened to 120 columns.

## 3. Nice

- N1. `emulator.py:159-162`: the stock `exited` branch returns without `self.close()`, so the map (fd and 695 KB
  mapping) and the finalizer stay until GC, unlike the lazpy path (H7 says "closes itself ... with close(self.timeout)").
  Fix: build the RunResult into a variable, `self.close()`, return it. Related: `_client.host_map()` reopens the map
  file after `close()` (line 88 checks only `_map is None`), so `emu.frame_total` after close maps it again and that
  map is never closed. Fix: `WorkerClient.close()` keeps `self.final_frame_total = self._map.frame_total()` before
  closing the map, `host_map()` returns None once `close()` has run, and `Emulator.frame_total` returns the kept value
  when the map is None.
- N2. `_worker.py:99-103`: only `HostCallError` is caught; a `ctypes.ArgumentError`, `TypeError` or `ValueError` in a
  handler kills the worker (HostCrashed, exit 1). Add `except (ctypes.ArgumentError, TypeError, ValueError) as exc:
  reply = ["err", _abi.AZH_E_ARG, f"{op}: {exc}"]`.
- N3. `state.c:332-342`: when the SD snapshot fails after a successful serialize, the k drain polls are in
  `vblanks_total` but not in `frame_total`. Move lines 341-342 (the counters bump) to just after `save_core`
  succeeds.
- N4. `state.c:264-268`: `strerror(errno)` after `write_file_atomic`, whose `unlink(tmp)` may have changed errno.
  Keep `errno` in `write_file_atomic` before the unlink.
- N5. `_client.py:116-122`: if `Popen` raises, `parent` and `child` leak. Wrap: `try: Popen(...) except
  BaseException: parent.close(); child.close(); raise`.
- N6. Untested branches: abi below 2 (S3 adds it), a save with k > 0 (k was 0 every time), a load whose drain times
  out. Note them in the item; no test needed now.
- N7. The planted red (`runs/d3-red.log`, 20:07) predates the final `test_state.py` (2.5 s bound, abi test). Its
  mechanism is unchanged, but after S2 run it once more and quote it (about 10 s).
- N8. Every SIGSEGV test run (live and fake) writes a `Python-*.ips` crash report in
  `~/Library/Logs/DiagnosticReports` (19:46, 20:05, 20:06 from the builder; 21:20 and 21:23 from this review's
  fast runs). The builder did not report it (phase-d step 3 asked). One line in USING.md section 8 or the tests'
  docstrings: "the crash tests leave a macOS crash report each run".
- N9. Over 120 columns: `emulator.py:295`, `test_api.py:49`, `test_c_checks.py:42`, `USING.md:90, 112`.
- N10. `conftest.py:116-119`: a do-nothing `pytest_collection_modifyitems`; delete it.
- N11. `test_map.py:4` imports numpy unconditionally, so the fast suite needs numpy although the package does not.
  `np = pytest.importorskip("numpy")` inside `test_close_with_live_view_does_not_raise`.
- N12. The meta's `app=` is the absolute app path (this Mac's user name). States are not shipped, but a shared state
  carries it; one USING.md line in section 10.
- N13. USING.md: section 11 "Stock: exact repeats" was not gated by D (the gate shows the same log fields from a
  state); say "the same log fields after a state restore (gated on the test app)". Section 8's HostError list lacks
  "unsupported" and "a guest exit outside `run`"; and an I/O failure while saving (AZH_E_IO) is a HostError, not a
  StateError: say so in section 10.
- N14. The stock exit result has `wall_s=0.0` and empty `shots` even when shot PNGs were written before the exit;
  say so in the `run` docstring and USING.md section 7.
- N15. `test_c_checks.py:186`: `frames == last_frame - first_frame + 1` is true by construction on the stock exit
  path (`emulator.py:160-161`); harmless, the f3 delay check carries the test.
- N16. `_worker.py:120` sends `("hello", n_fields)`, not the layout rows of phase-d 4.1; harmless (the worker checks
  the layout itself).
- N17. `host/azhost.h:75-76` still say "AZH_E_UNSUPPORTED until D"; the header is frozen, so for step H's docs pass.
- N18. `azhost run --save` / `--state` are not exercised by any D test; the runners line says so.

## 4. Departures from the brief

| # | Departure | Ruling |
|---|---|---|
| 1 | State boot gated by an absolute 2.5 s, ratios recorded only (phase-d 8 asked `t_state < 0.10 * t_boot`) | accepted: Guy's ruling; S2 puts the assert in the test |
| 2 | A returned `guest_exited` closes the Emulator on both cores (phase-d 4.4: exit 10 only) | accepted: main-loop ruling 21:02; N1 for the stock path's close |
| 3 | `GuestError` for a `guest_error` stop on either core, Emulator open; exit 11 GuestError, closed (4.5: stop on our core only) | accepted: C's as-built review asked for one rule; USING.md says it |
| 4 | Worker nice "at least 10" instead of `os.nice(10)` | accepted: Phase 3 review 1 (H2) |
| 5 | `state.c` accepts abi 2..AZH_ABI_VERSION (3.3: equal) | accepted: H3 |
| 6 | `host_paths` resolves the core by `_paths.core_path()` (LAZ_CORE), `stock_core`/`lazpy_core` fixtures, header `core= kind=` | accepted: H1 |
| 7 | I/O failures in save/restore are AZH_E_IO (HostError), bad files AZH_E_SAVESTATE (3.1: all SAVESTATE) | accepted; document (N13) |
| 8 | `RunResult.first_frame`/`last_frame` absolute, also on a guest exit (4.4: 1 and F) | accepted: matches `azh_result` (`run.c:319, 353`) |
| 9 | Worker reads the host path from `LAZ_HOST` set by the parent | accepted |
| 10 | `save_state` makes the state's parent folder | accepted |
| 11 | Held input persists across batches; `test_api.py:49` resets at frame 1 | accepted (by design, PLAN 2.5); S1 fixes the early-stop case |
| 12 | New `tests/python/d_helpers.py`; `.gitignore` `*.egg-info/`; `docs/map/code.md` edit (section 5 lists neither) | accepted: map_check needed code.md; S6 completes it |
| 13 | `statemeta.c` also includes `<fcntl.h> <unistd.h> <errno.h> <assert.h>` (3.1 lists four headers) | accepted: the brief asks it to do checked file I/O; no libretro, dual-compiles in test-host |
| 14 | Hello carries `n_fields`, not the rows | accepted (N16) |
| 15 | Wall-ratio check split into its own test with a module global | **not accepted**: S2 |

## 5. Phase 3's holds (phase-3.md section 6), checked in D's tree

- H1 holds: `conftest.py:54-64` (`_paths.core_path()`, checks the file), `stock_core` 67-73, `lazpy_core` 76-84,
  header 47-51 (`core=<path> kind=<kind>`), c4 takes `stock_core` (`test_c_checks.py:134-138`).
- H2 holds: `_worker.py:111-112`.
- H3 holds: `state.c:395-398`; the parse stays strict on keys (`statemeta.c:154`), so if G adds a meta key it must
  accept abi-2 metas without it (a note for G).
- H4 holds: `host/azhost_main.c:564-565`, no `wall_ms_max` anywhere; USING.md lacks it (S5).
- H5 holds in effect (`t_state < 2.5` asserted, times and the load line in `state-times.txt`), through the split test
  until S2.
- H6 holds: `host/api.c:578-585` refuses only `AZH_PH_NONE`.
- H7 holds on our core (`emulator.py:166-167`, `self.close()` passes `self.timeout`); on stock the worker is reaped
  and `closed` is True, but `close()` is not called (N1).
- Rows D1-D10 hold at the cited lines; D9's test needs S3. After S1 and N1, `emulator.py`'s line numbers in rows D6
  and D8 move: update phase-3.md's table at the merge.

## 6. Fix list for D's builder (paste-ready)

1. S1: `held_after` in `inputs.py` (+ `__all__`), `emulator.py` `run` uses it on both return paths and before the
   `guest_error` raise; `test_held_after_an_early_stop` in `test_inputs.py`; docstring line.
2. S2: inline `assert t_state < 2.5, ...` at the end of `test_state_boot`; delete `TIMES`, line 70 and
   `test_state_boot_wall_ratio`.
3. S3: `test_newer_abi_refused` built from `_abi.AZH_ABI_VERSION`; one abi-1 case.
4. S4: `restore_t.replaced`; `azh__state_load` marks DEAD after a failure past the SD replace; one USING.md line.
5. S5: USING.md seed order (lines 17-18, 86), `wall_ms_mean` in section 3, line 90 reworded and wrapped, lines 63-65
   pointing at `host.log`'s `core message:` lines.
6. S6: `.venv/` in code.md's ignored list; rewrap code.md's two long lines.
7. Optional in the same pass (each a few lines): N1, N2, N3, N5, N9, N10, N11, N14.
8. Rerun: `make check && make && make test-host`; `nice -n 10 python3 -m pytest -q -m "not slow" tests/python`
   (expect 49 passed); then in the background `LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs
   tests/python` (expect 69 passed, 0 skipped); then the planted red once (must fail with "lines differ"); quote the
   new `state-times.txt`.

## 7. Lines the merge adds

`docs/map/runners.md` (a new block after step C's; the builder's block with the commands and counts corrected):
```
python3 -m venv .venv && .venv/bin/pip install -e .          # the Python package (editable install only)
nice -n 10 python3 -m pytest -q -m "not slow" tests/python  # step D's fast tests, no emulator: "49 passed"
LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python   # step D's gate, about 70 s: "69 passed", 0 skipped
LAZ_CORE=build-core/azahar_lazpy_libretro.dylib LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q tests/python/test_c_checks.py   # C's checks on our core: "10 passed"
LAZ_TEST_PLANT_RED=1 LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q tests/python/test_state.py -k test_state_boot   # must FAIL: "lines differ"
build/azhost run <app.3dsx> --frames N --save runs/x.state   # a state from the command line (--state boots one; not gated in D)
```
and in the existing build block change the test-host count to `"test-host: 307743 checks, 0 failed"`.

`docs/map/tools.md`:
```
- `tests/python/`: step D's pytest suite. Fast (no emulator): inputs, errors, the map, the worker client against
  `tests/python/fakeworker.py`, the ABI check. Slow (`slow` marker, needs the core and `build/testapp.3dsx`): C's
  checks through Python, crashes and stalls, the 200,000-frame batch, savestates and state boot (`runs/d-pytest/`,
  times in `runs/d-pytest/state-times.txt`). `conftest.py` has the fixtures (`host_paths`, `stock_core`,
  `lazpy_core`, `workdir`, `seed`); `LAZ_REQUIRE_EMULATOR=1` turns a skip into a failure, `LAZ_CORE` picks the core,
  `LAZ_TEST_PLANT_RED=1` plants the state-boot red. `d_helpers.py`: shared boot and log helpers.
```
`.gitignore`: `*.egg-info/` is already on step-d; `.venv/`, `__pycache__/`, `.pytest_cache/` were there before.
