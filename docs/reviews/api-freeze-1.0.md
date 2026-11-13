# 1.0 API freeze review

Reviewer: opus agent a5a4eeb6772bd50c9, 2026-11-13 11:20-11:25, read-only, on branch core-rev2 (plan step V1 of
`docs/plans/phase-v1.md`). Saved verbatim by the main loop.

**Verdict:** this can be frozen once 13 changes are made. Most of the surface is sound: errors share one base class, close() can be called twice, `Emulator` takes optional arguments by keyword only, and units are consistent within each layer (seconds in Python, ms on the command line). Five problems would cost us most if frozen:
- The two profile parsers diverge, and azhost has silent truncation bugs.
- azhost exits with code 2 (usage) when a savestate fails.
- The input-script format is not written down anywhere.
- `run()` still takes `inputs` and `shots` positionally.
- `run_until` names the same options differently from `run`.

Only three changes break callers. Neither internal user is hit by any of them (see the last section).

## Change before 1.0

1. **One option-profile parser, two implementations** (`python/libazahar/emulator.py:27-38`, `host/azhost_main.c:244-296`). Today azhost reads with `fgets(line, 512)`, so a longer line silently splits into two "lines". Past line 4096 it silently stops reading. It never trims, and only `#` in column 0 is a comment. Python strips every line, treats an indented `#` as a comment, and splits on every `splitlines()` separator (`\v`, `\f`, U+2028 included). A missing `=` gives `HostError`, and a missing file leaks a raw `FileNotFoundError`. Fix: implement the spec below.
   - Move the C parser into a pure `host/profile.c` (`int azh__profile_parse(const char *path, int (*cb)(const char*, const char*))`) and use it for both `--profile` and `--lazpy-profile`. `--opt` uses the same pair rule.
   - Python: `_read_profile` raises `ArgumentError(f"{path}:{n}: ...")`, and `HostError` for an unreadable file.
   - Tests: a new `tests/host/test_profile.c` and `tests/python/test_profile_format.py`, both driven by one case table in `tests/data/profile-cases/` (the cases that must pass and the ones that must fail, the same files on both sides).
   - Docs: USING section 14 gets the spec.
2. **azhost exit codes** (`host/azhost_main.c:222-242`, `host/azhost.h:16-19`).
   - `AZH_E_SAVESTATE` (a failed `--state` or `--save`) currently prints "UsageError" and exits 2. Add `AZH_EXIT_STATE = 9` (class `StateError`) and the row `const.AZH_EXIT_STATE` in `api.c`.
   - `print_escaped` (`:532-543`) leaves `"` alone, so a guest message containing a quote breaks the summary line. Escape it as `\"` and promise that `msg=` is always the last key: new keys go before it.
   - Write the table below into USING section 3, and point HOST-API.md:94-97 at it.
   - HOST-API.md:95-96 says the opposite of what the code does. On **our** core a guest exit prints the summary and then exits 10. On the **stock** core the process `_exit`s from inside the run, with no summary for that batch (`host/env.c:42-56`, `msg.c:75`). Fix the text.
   - Tests: add exit-code cases to the C or CLI checks (a missing `--state` file gives 9; `--debug-stop` on the stock core gives 7).
3. **Input-script format: write it down and remove the octal trap** (`host/azhost_main.c:356-442`). Nothing documents it, yet the plan freezes "the format USING writes down".
   - Today `strtol(p, &end, 0)` reads `010` as 8. Accept only decimal (with an optional `-`) and `0x` hex; a leading `0` means decimal.
   - A line longer than 511 bytes should be an error naming the line. Today a long comment line is split into two reads and the second half fails as an unclear "want 7 integers".
   - Spec for USING (new section 4a):
     - One record per line: `frame buttons touch_x touch_y touch_down circle_x circle_y`, 7 int32 fields separated by spaces, tabs or commas.
     - A `#` anywhere starts a comment that runs to the end of the line. Blank lines are skipped.
     - Each record is the **whole** held state, unlike Python's items, which change only their own part.
     - The script applies to batch 1 only. At most 1,000,000 records.
   - Test: extend `tests/host/test_input.c` or add a CLI case (`010` is 10, `0x10` is 16).
4. **`run()` options become keyword-only** (`emulator.py:166`).
   - New signature: `run(self, frames: int, *, inputs=(), shots=(), stop_file=None, stop_text=None, stop_every=30, stop_new=False, debug_text=None, wall_limit=None, timeout=None, watch=None, watch_every=1)`. Positional `run(600, INPUTS, SHOTS)` is unreadable, and freezing it pins the argument order forever.
   - Also validate `watch_every` as 1..100000, matching `stop_every` and `AZH_WATCH_EVERY_MAX`. Today 0 is accepted and quietly means 1 (`:266-278`).
   - Tests: `test_state.py:41,58`, `test_memory_live.py:115`, `d_helpers.py:36`.
5. **`run_until` uses `run`'s vocabulary** (`emulator.py:311-320`). New signature: `run_until(self, file, text, max_frames, *, stop_every=30, stop_new=False, inputs=(), shots=(), wall_limit=None, debug_text=None, timeout=None, watch=None, watch_every=1)`. Today `every` and `new_only` duplicate `stop_every` and `stop_new`, and `wall_limit` cannot be passed at all. Tests: `test_c_checks.py:100,118-122`, `test_state.py:37`.
6. **Error classes and leaks.**
   - (a) `SlotTimeout.op` is `"acquire"` (`_slots.py:39`), but USING:85 and :182 promise `"slot"`. Make it `"slot"`.
   - (b) Move `SlotTimeout` and `LoadWarning` into `errors.py`; `_slots` re-imports them. Public classes should not live in a private module (their repr and pickle path currently show `libazahar._slots`).
   - (c) Raw `OSError`s leak out of the constructor: a missing `sd_seed` (`emulator.py:113`, `:125`) and a missing profile (`:30`). Check `sd_seed` with `is_dir()` up front and raise `ArgumentError`; a missing profile becomes `HostError`.
   - (d) HOST-API.md:55 says that `AZH_E_ARG` maps to `ValueError`. It should say `ArgumentError`.
   - (e) Add a table of which call raises what to USING section 8:
     - Constructor: `ArgumentError`, `BootError`, `HostError`, `SlotTimeout`, `HostTimeout`, `HostCrashed`.
     - `run`: `ArgumentError`, `GuestError`, `NeedsLazpyCore`, `HostTimeout`, `HostCrashed`, `HostError`.
     - State calls: `StateError`, or `HostError` for I/O.
     - Memory calls: `GuestMemoryError`, `NeedsLazpyCore`, `ArgumentError`, or `TypeError` for non-bytes data.
     - Any call after close: `HostError`.
   - Tests: `test_slots.py` (`.op`) and `test_errors.py` (class module and constructor errors).
7. **Shrink what each submodule exports, and say what the promise covers.**
   - `errors.__all__` lists `HostCallError` and `from_code` (`errors.py:9-10`). Drop them; `HostCallError` is only used by `_worker` and `_host`.
   - `inputs.__all__` lists `Held`, `fold` and `held_after` (`inputs.py:12`). Drop them; the export list should be just `Buttons`, `Touch`, `Circle`.
   - USING should say: "The promise is `libazahar.__all__`; `libazahar.errors` stays importable." 3DPlatinum imports `libazahar.errors.LibAzaharError`.
   - Test: an `__all__` snapshot test in `test_api.py` (the fast tier), so that removing a name is caught.
8. **Returned paths become `pathlib.Path`.** Change `Shot.top` and `Shot.bottom`, `SaveInfo.path`, and `shot()` to return `Tuple[Path, Path]` (`results.py:17-18,58`, `emulator.py:365-370,397`). Inputs already accept `str | Path`, and `emu.sd` and `emu.workdir` are already `Path`. Freezing `str` rules out `Path` for good. Also make `Shot.frame_total` required, dropping its default of 0 (`results.py:19`). Docs: USING sections 3, 9 and 10. The tests already wrap these values in `Path(...)`.
9. **Pool and thread-safety behaviour.** `Pool.__exit__` (`pool.py:84-85`) waits for every *queued* job even when the `with` body raised, so a Ctrl-C can wait hours. Use `self._executor.shutdown(wait=True, cancel_futures=exc[0] is not None)`. Also document in USING section 13:
   - An Emulator is used from one thread at a time.
   - Separate Emulators may run in parallel threads or processes.
   - A Pool reusing `root` reuses `job-NNNN/sys/`, the SD card included, unless `fresh_sd=True`.
   - `factory=` is a test hook outside the promise.
   - Test: `test_pool.py`, an exception in the body cancels pending jobs.
10. **Document every public name, and make `app` and `workdir` read-only.** `Emulator.app`, `.workdir`, `.timeout` and `.boot_timeout` are plain mutable attributes nobody documents (`emulator.py:77-80`), yet `examples/pool_shots.py` reads `emu.workdir`. Make `app` and `workdir` properties, and document `timeout` and `boot_timeout` as settable. Several names in `__all__` appear nowhere in USING:
    - `stats()` and `Stats`. Its units: `peak_rss` is in bytes (`api.c:645`); `frames` is frames since boot.
    - `pid`, `run_frame()` and `shot()`.
    - The attributes of `HostCrashed` (`returncode`, `signal`, `message`, `log_tail`, `err_tail`) and `HostTimeout` (`op`, `seconds`, `message`).
    - `Memory`, which is exported for type hints and never constructed by users.

    Docs: a new USING section 20, "API reference" (one line per `__all__` name).
11. **Environment variables.**
    - The scripts read `LAZPY_ROOT` (`tools/build-core.sh:11`, `tools/mkrelease.sh:19`, USING:227) and the library reads `LAZ_ROOT`, with the same meaning. Rename to `LAZ_ROOT` and keep `LAZPY_ROOT` as an alias for 1.x.
    - Limit the promise to the first table of USING section 15. Say outright that the build/fetch table and the test-only variables (`LAZ_REQUIRE_EMULATOR`, `LAZ_STOCK_CORE`, `LAZ_CORE_OLD`) may change.
    - Update phase-v1 section 1 to match.
12. **`azhost.h` comments and HOST-API.md are stale**, and that header is "the reference" (HOST-API.md:9).
    - Header: drop the step-history comments (`reserved for step D`, `step G`, `state: step D`, `step C; must be empty / 0 in A`, lines 14-15, 62-64 and 91). State in the `azh_set_option` comment (`:90`) that an unknown key or value returns `AZH_E_ARG`. Delete the trailing whitespace on line 23.
    - HOST-API.md:
      - Change "ABI 3" to 4 (lines 5 and 15).
      - Add `azh_threads` to the call order and the function table (lines 22-46).
      - Fix the header line numbers.
      - Replace "may change before 1.0" with the promise.
      - Regenerate the layout dump at ABI 4.
13. **Minor validation, all non-breaking for valid input.** `shots` accepts `1.5` and truncates it (`emulator.py:221`). `frames` refuses a numpy integer. Use `operator.index` in both places. Optionally check `Touch` and `Circle` ranges in `__post_init__`, so a bad point fails where it is built rather than at `run`.

## Keep (checked)

- The `Emulator(app, workdir, *, ...)` signature and its defaults: `timeout` 30 s of no progress, `boot_timeout` 300 s, `fresh_sd=False`.
- `wall_limit` in seconds in Python and `--wall-limit-ms` on the command line. `RunResult.wall_s` and `Stats.*_s`.
- The `stopped_by` strings, the 7 in USING section 7. Promise that new values may be added and callers must accept unknown ones.
- `close()` can be called twice on both `Emulator` and `Pool`. Both are context managers and neither swallows exceptions. After a guest exit the Emulator is closed on both cores.
- The error tree:
  - Every class derives from `LibAzaharError`.
  - `ArgumentError` is also a `ValueError`, and `SlotTimeout` is a `HostTimeout`.
  - `GuestError.result` is set only while the Emulator is still open.
- Frozen dataclasses for results. `RunResult.shots` is a dict inside a frozen dataclass: compared by equality, not hashable. Acceptable; the docs should say so.
- `screens()` returns read-only numpy views, or `bytes` when numpy is missing (documented).
- `Buttons` (libctru names plus the `UP`/`DOWN`/`LEFT`/`RIGHT` aliases), `Touch.up`, `Circle`.
- `set_input` and `set_keys(raw)` (the libmgba-py name).
- Memory names (libmgba-py): callable widths, `raw_read`/`raw_write`, `write_u8..u64`. The missing `write_s*` methods can be added later.
- `SaveInfo.k`: the name is terse but defined everywhere as "N + k".
- `LAZ_*` names and the `none` sentinel. `LAZ_PNG_LEVEL` silently falling back to 1 is lenient, but documented.
- The C names: `azh_stats_t` versus the other typedefs, and `AZH_EXIT_NEEDS_LAZPY` versus `AZH_E_NEEDS_LAZPY_CORE`. Both are inconsistent, but renaming costs more than it gains.
- The export list matches the 15 header functions. The struct layouts may grow under the promise.
- The azhost flags. `--debug-stop` doesn't match Python's `debug_text`; adding `--debug-text` later is allowed.
- The `saved k= frame=` and `last N:` stdout lines: document them as frozen. The `Class: text` line on stderr is informative only, outside the promise.
- Not in this list: a public `read_profile()` helper, or `options=Path`. 3DPlatinum copied Python's parser (`tools/emu/lazpy/boot.py:15-25`), which suggests demand, but either can be a 1.x addition.

## Option-profile format (proposed spec)

1. The file is UTF-8 without a BOM. Lines are split on `\n` only; one trailing `\r` is removed. A last line without a newline counts.
2. Each line is at most 511 bytes (the newline excluded). A file has at most 4096 lines, comment and blank lines included. Going over either limit is an **error**, never silent truncation.
3. A line that is empty after step 1 is skipped. A line whose **first byte** is `#` is a comment. A `#` anywhere else is part of the text.
4. Every other line is `key=value`, split at the first `=`. The key is non-empty and contains no space, tab or `=`. The value is everything after the `=`, verbatim: inner spaces are kept (`citra_is_new_3ds=New 3DS`), and it may be empty, in which case the host decides.
5. Nothing is trimmed. A line that starts or ends with a space or tab is an **error**; this includes an indented `#`.
6. Pairs are applied in file order, after the earlier sources: lazpy profile, then the default (or given) profile, then `options=` / `--opt` in order. **The later line wins**, inside a file and across sources.
7. An unknown key, or a value outside the core's list, is refused by the host (`AZH_E_ARG`, "unknown option key ..."). It is never ignored. On the stock core a lazpy-only key is unknown.
8. How errors surface:
   - Python: a bad line raises `ArgumentError("<path>:<line>: <reason>")`; an unreadable file raises `HostError`; an unknown key raises `ArgumentError` at boot.
   - azhost: a bad line or unknown key prints `UsageError: <path> line N: <reason>` and exits 2; an unreadable file prints `IOError` and exits 6.

## azhost exit codes (proposed USING table)

| Code | Meaning |
|---|---|
| 0 | Every batch ran. The stop reason is in each summary line (`frames`, `sd_text`, `debug_text`, `guest_break`, `wall_limit`). |
| 2 | Usage: a bad flag or value, a bad profile or input-script line, an unknown option key or value. |
| 3 | The app failed to boot (`AZH_E_BOOT`). |
| 4 | The core failed to load or has an unknown version (`AZH_E_CORE`). |
| 5 | Vulkan or MoltenVK failed (`AZH_E_VULKAN`). |
| 6 | I/O or out of memory: unreadable profile, inputs or seed; unwritable `--out` or `--sys` (`AZH_E_IO`, `AZH_E_NOMEM`). |
| 7 | The run needs our core (`AZH_E_NEEDS_LAZPY_CORE`), e.g. `--debug-stop` on the stock core. |
| 8 | Unsupported request (`AZH_E_UNSUPPORTED`), e.g. `--raw-shot` at a resolution factor other than 1. |
| 9 | **New.** A savestate could not be loaded (`--state`) or saved (`--save`) (`AZH_E_SAVESTATE`). |
| 10 | The guest exited. Our core: the batch's summary line (`stop=guest_exited`) comes first. Stock core: no summary for that batch. |
| 11 | A guest error ended the run. Our core: summary first (`stop=guest_error`). Stock core: none. |
| 128+n | Killed by signal n (shown by the shell; azhost never returns it itself). Codes 1 and 12-127 are reserved. |

Summary-line keys are frozen: `frames wall fps shots stop first last vblanks wall_ms_mean batch msg`. Units: `wall` in seconds, `wall_ms_mean` in ms, `batch` counts from 1. New keys are inserted before `msg`, which is always last and escapes `\\`, `\n` and `\"`.

## Breaks for users

- `run(frames, inputs, shots)` called positionally now raises `TypeError` (item 4). 3DPlatinum's `tools/emu/lazpy/boot.py:70` passes keywords, so it is not hit. Gen3D: I found no in-tree `libazahar` import on its checkout, so nothing to update.
- `run_until(..., every=, new_only=)` becomes `stop_every=` / `stop_new=` (item 5). Neither user calls `run_until`.
- `Shot.top`/`.bottom`, `SaveInfo.path` and the return of `shot()` become `Path` (item 8). Code doing `json.dumps(shot.top)` or calling `str` methods on them breaks. Neither user reads them; 3DPlatinum's JSON holds only `stopped_by`, `frames` and the counters.
- `SlotTimeout.op` changes from `"acquire"` to `"slot"` (item 6). No user reads it.
- Stricter profiles (spec items 2 and 5): padded or indented lines, and indented `#`, now fail loudly. 3DPlatinum's `tools/emu/lazpy/options.txt` is clean (I checked for leading and trailing whitespace) and it passes `options=` pairs rather than a profile path, so it is unaffected.
- azhost: a failed `--state` or `--save` exits 9 instead of 2, and input-script tokens with a leading zero are now decimal. Neither user calls `azhost` directly (3DPlatinum's `lazpy_run.sh` does not).
