# Phase 2 step C: as-built review (opus, 2026-11-12)

Subject: branch `step-c` in `../libazahar-py-c`, C1 at 0651a8d plus C2/C3 uncommitted. Brief: `docs/plans/phase-c.md`
revision 2, section 14 checklist. Builder's report: item 210 "Lessons and notes".

Verdict: **mergeable after B1 and S1-S4** (all small, C's own files; no header change). Rerun once after the
fixes: `make check && make && make test-host` and the whole `gate_c.py` (about 2 min). Re-checked here:
`make check` clean, `make` clean, `test-host: 307679 checks, 0 failed`; the builder's `runs/c-gate.log`
(28 passed, rc file 0) and `runs/c-gate-plant.log` (a1/a2 FAIL with offsets -2/-1, a3/a4 PASS) read as reported.
Checklist items 1-13 of phase-c.md section 14 hold except where a finding below says otherwise.

## Blocker

- **B1. `host/api.c:366-369` (azh_boot): a state boot never loads the app, and D's warm-up frame would trip an assert.**
  `rc = (state_or_null != NULL) ? azh__state_boot(app, state_or_null) : boot_game(app);` routes a state boot past
  `boot_game` (static in api.c, so state.c cannot call it). PLAN.md 2.9 says the state boot "loads the app, completes
  the Vulkan setup and the first `retro_run`, loads the state", and phase-d.md 3.4 says `azh__state_boot` is "called
  by `azh_boot` once A's boot path has loaded the app". So C1's routing contradicts both; D built to phase-d 3.4
  (`../libazahar-py-d/host/state.c:485-502`: meta and sha checks, `STATE_WARMUP_FRAMES` = 1 call of
  `azh__run_one_frame`, then the restore). Second fault: `azh__run_one_frame` asserts `azh_g.phase ==
  AZH_PH_BOOTED` (`host/run.c:110`) and `env_message` runs the detector only when the phase is BOOTED
  (`host/env.c:85`), but azh_boot sets BOOTED only after the state boot returns. Fix (C's builder, api.c only; D's
  proposal, accepted):
  ```c
  rc = boot_game(app);
  if (rc != AZH_OK) {
      azh_g.phase = AZH_PH_DEAD;
      return rc;
  }
  azh_g.t_boot = mono_s();
  azh_g.phase = AZH_PH_BOOTED;          /* before the state boot: its warm-up frame needs it (run.c:110, env.c:85) */
  if (state_or_null != NULL) {
      rc = azh__state_boot(app, state_or_null);
      if (rc != AZH_OK) {
          azh_g.phase = AZH_PH_DEAD;    /* the app is loaded and Vulkan is up: azh_boot runs once, no retry */
          return rc;
      }
  }
  return AZH_OK;
  ```
  and delete the `rc == AZH_E_UNSUPPORTED && state_or_null != NULL` "stays open" branch: once `boot_game` has run
  the instance cannot go back to OPEN (a second `retro_load_game` is not supported), and with D's real `state.c` no
  UNSUPPORTED comes from there any more. A refused state (wrong app, missing meta) now costs one app load and Vulkan
  setup before the refusal, but still no guest frame (restore_check runs before the warm-up); that is acceptable
  and matches PLAN 2.9's order. On the stub `state.c` of C's branch, a state boot now returns UNSUPPORTED with the
  phase DEAD; azhost has no `--state` flag in C, so no C gate check changes. The `t_boot` move keeps
  `azh_stats.wall_s` measured from the end of the app load, as before.

## Should fix

- **S1. `host/run.c:314-341` (run_frames): an SD read error lets the batch run to its end.** `stop_after` stores
  `found < 0` in `sd_error` and the loop goes on (`stop < 0`), so a 10,000,000-frame batch whose SD path became a
  folder or unreadable runs every frame before returning `AZH_E_IO`. Fix: add `&& sd_error == 0` to the `for`
  condition (the error then ends the batch at the frame that hit it; `frames_run` and `vblanks` already count it).
- **S2. `host/azhost_main.c:377-392` (load_inputs): a bad token is read as 0, extra integers are ignored, and an
  out-of-range value wraps.** `strtol` with `end == p` leaves `p` in place, so `1 2 x` gives `1 2 0 0 0 0 0`
  silently; an 8th integer is dropped; `(int32_t)strtol(...)` wraps `0x100000000` to 0 (a valid record). Fix: per
  field, fail (`UsageError ... line N`) when `end == p`, when `errno == ERANGE` or the value is outside
  INT32_MIN..INT32_MAX; after 7 fields, fail unless only separators and the newline remain. Split the per-line parse
  into its own function (`load_inputs` is 66 lines, C rule 4).
- **S3. `host/run.c:60-65` (azh__counters_set): the map keeps the old totals.** D calls it at the end of a restore
  (phase-d 3.3 step 7); the map's `frame_total`/`vblanks_total` then show the warm-up frame's values until the next
  `retro_run`, and D's `HostMap.frame_total()` (and its death mapping's `F`) read the map. Fix: end the function with
  `azh_map_set_counters(frame_total, vblanks);` (run.c is C's; no header change; D needs no edit).
- **S4. `tests/gate_c.py:43-50, 251` (run_azhost / SIGTERM): the child is orphaned on SIGTERM.** The handler raises
  `SystemExit` out of `communicate()`; the `finally` writes the rc file but the `nice azhost` child keeps running
  (scenario a: up to 900 frames of emulator on a shared machine, rule 5). Fix: in `run_azhost`, wrap the
  `communicate` in `try: ... except BaseException: child.kill(); child.wait(); raise` (own child only), keeping the
  `TimeoutExpired` branch as is.

## Nice

- **N1. `host/log.c:122, 134-142`: a data race on `dbg_text` while re-arming.** A core thread other than the run thread
  (our core logs synchronously on whichever thread logs, with `instant_debug_log`) can be inside `strstr(fmt,
  dbg_text)` when the run thread rewrites the text, and can set `dbg_hit` after the arm cleared it: a spurious
  debug stop at the next batch's first check. Rare and our-core only. Fix when our core lands (Phase F2): two text
  buffers and an atomic index (the writer fills the idle buffer, then flips the index and clears the hit), or note
  it in the code.
- **N2. `host/api.c:392`: `strstr(sd_file, "..")` refuses `log..txt`.** Safe but too broad; check for a `..`
  component (`..` at the start or after `/`, followed by `/` or the end).
- **N3. `tests/gate_c.py`: a missing output becomes a traceback, not FAIL lines.** After a timeout or a crashed run,
  `read_png`/`read_map` raise (scenarios b, d, f) and the later scenarios do not run (rc is still 1, so no false
  pass). Wrap each scenario call in `main` in `try/except (OSError, KeyError, IndexError, ValueError)` that reports
  `FAIL <scenario> crashed: <exc>`. a3 does not check "at most one in-between line" (it finds the first steady
  line, so a slower approach still passes the offset rule): add a check that between the change's planned host frame
  and the steady line at most one line differs from both the old and the new value.
- **N4. Python rules: missing docstrings** on `get_log`, `c_values`, `delay`, `layout_rows`, `scenario_*`
  (gate_c.py) and `_extract` (checks_c.py); the module-level `passed`/`failed` counters with `global` (rule 7: a
  small counter object passed to `report`); lines over 120 columns (gate_c.py 22, 50, 139, 167, 188, 191, 200, 221,
  234; azhost_main.c 40-41).
- **N5. `host/azhost_main.c:97-98`:** the same assert twice in `set_flag`.
- **N6.** `--stop-new` (run.c `sd_start`'s `stat`) is exercised only by the pure test of the matcher, not by a run;
  D's integration test of `run_until(..., new_only=True)` (or whatever D names it) should cover it.

## The eight deviations

1. **Three shared symbols declared locally** (`extern azh_msgstate azh_msgs` in run.c:14, `azh_run_batch_inputs`
   and `azh_run_raw_shot` in run.c:16-17 and api.c:456-457). **Accept now; the main loop moves them into
   `host/azh_internal.h` in C's merge commit** (three lines under "run.c additions", the local copies deleted).
   It is an internal header, additive, no ABI or layout change, and D's branch never edits that file, so D's merge
   does not conflict. Until then the compiler does not cross-check the two copies (C rule 6/8 spirit).
2. **No per-frame max; `wall_ms_mean`, and c3's bound `3.0 s + max(1.0 s, 5 x mean)`.** **Accept.** A per-frame max
   needs a new `azh_result` field (frozen). The check can still fail: a missing stop runs 10,000,000 frames and
   times out; a stop more than 1 s late fails; `wall >= 3.0` holds by construction (`run.c:308`). The summary field
   is `wall_ms_mean`, not the brief's `wall_ms_max`: `docs/map/runners.md` and USING.md must say so.
3. **azhost links `build/obj/sdcopy.o` directly** (Makefile:20-21). **Accept.** sdcopy.c has no file statics, so two
   copies (library and program) share no state; exporting an `azh__` symbol from the public dylib would be worse.
4. **Gate ids `a2.N.hid` / `a2.N.irrst`.** **Accept**: two kinds need two lines; the planted red then reads
   `FAIL a2.1.hid` (and `.irrst`). Quote the new ids in the item's Evidence.
5. **A frame asked for PNG and RAW reads back twice.** **Accept.** Sharing one readback means editing A's `frame.c`
   (not C's file); the two reads give equal bytes (d4), and the cost is one extra 0.77 MB readback on that frame
   only. `run.c:127-138` duplicates frame.c:100-110's source choice (8 lines); fine until A's file is opened again.
6. **The thread assert is armed only inside `retro_run`** (`run.c:26, 32`). **Accept.** The documented callers
   (HID pad poll, `PollEvents`) run inside `retro_run`, and D's drain (`retro_serialize_size`) runs the guest on the
   same thread but outside it, where an always-armed assert keyed to the last `retro_run` thread would also pass;
   the narrower form costs nothing.
7. **One message per run, the stronger kind wins** (`msg.c:54-64`). **Accept.** `azh_msgstate` has one `first`
   buffer (frozen); with exited > error > break it always matches the stop reason the batch reports (the stop order
   in `run.c:288-306` is the same ranking).
8. **A guest exit or error ends azhost with 10 or 11 and no later batches; a break continues**
   (`azhost_main.c:591-594`). **Accept.** This also covers the stock core's returned error (one or two error
   messages in one `retro_run`, so `stop=guest_error` with a summary, then exit 11), which the brief's "on our core"
   did not foresee; one rule for both cores is simpler. Write it in `docs/map/runners.md`.

## For step D

- **B1 changes azh_boot's order** (app load and Vulkan setup first, phase BOOTED, then `azh__state_boot`). D's
  `state.c:485-502` needs no edit; it now runs with the app loaded and the phase BOOTED, so its warm-up
  `azh__run_one_frame` passes the `run.c:110` assert and its messages reach the detector. Any state-boot failure
  leaves the instance DEAD (no OPEN fallback): the Python side closes the worker on a failed `start` anyway.
  `azhost run ... --state FILE` then works through the same path.
- **S3**: `azh__counters_set` will also write the map's totals; D does not call `azh_map_set_counters` itself.
- **A guest error on the stock core arrives two ways**: a returned batch with `stop_reason == AZH_STOP_GUEST_ERROR`
  (one or two error messages in that `retro_run`) or `_exit(11)` (the third in one `retro_run`). D's death mapping
  covers 11; the returned case must map to the same `GuestError` (or `RunResult(stopped_by="guest_error")`, D's
  choice, but one rule for both, written in USING.md).
- `azh_result.message` is the stopping kind's message from the last `retro_run`, cut to 255 bytes; the map's
  message (1023 bytes, `msg_seq` +1 per SET_MESSAGE) and host.log have more.
- Messages that arrive outside a batch frame (D's drain inside `retro_serialize_size`) set the detector's flags,
  which the next frame's `azh__msg_begin_run` clears: a break or a non-fatal error during a drain is not a stop. A
  stock 16 or a third error there `_exit`s (D's "exited during <op>" mapping). If D wants to warn, compare
  `msg_seq` before and after the drain.
- Raw pixels: `px_frame` is -1 during a copy and the frame after; the worker writes them inside its own op, so a
  read after the op's reply is consistent.
- c3 through Python: there is no per-frame max; use C's bound, `3.0 + max(1.0, 5 * batch1.wall_s / batch1.frames)`
  seconds.
- Gate ids changed as deviation 4 says; the check functions in `tests/checks_c.py` are unchanged by the fixes.
