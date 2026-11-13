# V1 API-freeze commit review (branch core-rev2, 64f5d18)

Reviewer: opus agent a04d832ad11619ae6, 2026-11-13 12:00-12:12, read-only, on commit 64f5d18 against
`docs/reviews/api-freeze-1.0.md`. Saved verbatim by the main loop; only the scratchpad paths are shortened (the
session scratchpad, not tracked).

**Verdict: not ready to merge yet. Two fixes are small but needed first.**

Most of the commit is right. Items 1-13 are done. The gates pass when I rerun them: `make`, `make check`, test-host (307918 checks, 0 failed) and fast pytest (195 passed). The HOST-API layout dump is byte-identical to `build/azhost layout` (152 lines), and the header line numbers in HOST-API's function table match `azhost.h`. The summary line prints the frozen keys in order, with `msg=` last. `__all__` holds no test hooks.

The two blockers:
- The two profile parsers disagree on bytes the frozen format covers.
- The frozen exit-code table promises codes the code does not return for some cases.

Notes and harness: the session scratchpad's `v1review/notes.md`. The C-vs-Python comparison output is `diff-out.txt` in the same folder.

## Must fix

1. **The C and Python profile parsers disagree on three inputs.** I ran the same files through both parsers.
   - **Invalid UTF-8.** `a=\xff`: C accepts it (`host/profile.c` has no UTF-8 check). Python refuses it (`python/libazahar/emulator.py:40-43`). USING.md:278 says "The file is UTF-8".
   - **NUL byte.** `a=b\x00c`: C refuses it (`host/profile.c:36-39`). Python accepts it. ctypes then cuts the value to `b` without a word (I checked: `strlen` sees 1 byte). That breaks USING.md:281, "never a silent cut".
   - **BOM at the start of line 2.** C refuses line 2 (`host/profile.c:40-44` checks every line). Python checks only the file start (`emulator.py:66-67`) and returns the key `'﻿k'`.
   - **Why the tests missed it.** The shared table has no such cases. `tests/python/test_profile_parser.py` tests `bad\xff=1` on the Python side only.
   - **Fix:** C checks UTF-8 on non-comment lines. Python refuses NUL. Both check the BOM on line 1 only (or both on every line). Add `bad-utf8`, `nul-in-value` and `bom-line-2` to `tests/data/profile-cases/`.

2. **The exit-code table (USING.md:51-66) is wrong in two places.** This table is frozen by the promise.
   - **Seed failures exit 2, not 6.** USING.md:60 says an unreadable seed exits 6. But `host/azhost_main.c:474-476` turns every `seed_sd` failure into `AZH_E_ARG`, which prints `UsageError` and exits 2. Fix: return `AZH_E_IO` when the copy fails, or change the row.
   - **A `--save` I/O failure exits 6, not 9.** USING.md:63 says a failed `--save` exits 9. But a write failure returns `AZH_E_IO` (`host/state.c:269`), so it exits 6. Only the drain or serialize failures return 9 (`state.c:249-262`). Fix: say so in row 9, matching USING.md:173.

## Should fix

3. **The two parsers report different errors for a file that breaks both a line rule and the line count.** Case: line 1 is `bad`, then 4096 more lines. C reports `error line 1`. Python reports `:0:`, because it counts lines first (`emulator.py:71-72`). C also calls the callback for lines 1-4096 before it fails at line 4097. Align the order and add the case to the table.

4. **USING.md:276 overclaims for `options=`.** It says `options=` pairs use the same `key=value` rule. `_pairs` (`emulator.py:77-81`) checks nothing: padded keys and values, empty keys and NUL all go straight to the host. Either check them with the same rule or reword the line to cover `--opt` only.

5. **The input-script length limit treats CRLF differently from the profile.** A 511-byte input-script line ending in CRLF is refused. I ran azhost on it: `line longer than 511 bytes`, exit 2. The cause is `azhost_main.c:356,374`: fgets reads 511 bytes plus the `\r` with no `\n`. The profile parser allows the same line. USING.md:91 does not say which. Fix: drop one `\r` before measuring, as the profile does, or document it.

6. **Long input scripts are cut without an error.** The input-script loop stops after 4,000,000 lines (`azhost_main.c:369`, `lines < 4 * AZH_MAX_INPUTS`). The rest of the file is ignored and the run goes ahead. This existed before the commit, but the format is now frozen. Fix: make it an error when fgets still returns data at the bound. (Verified by reading only; running it would load a core.)

7. **The constructor leaks a raw `PermissionError`.** `Emulator(app, "/System/x")` raises `PermissionError` from `emulator.py:148-149`. I ran it. The USING.md:143 table lists only libazahar classes. Fix: wrap it in `HostError`.

8. **Three error classes cannot be unpickled.** `HostTimeout`, `SlotTimeout` and `HostCrashed` fail a pickle round-trip with `TypeError: missing ... positional argument`. I ran it. USING.md:254 promises separate Emulators in parallel processes. My inference: a process pool could not hand these errors back to the parent. The freeze pins their constructors, so add `__reduce__` now.

9. **HOST-API.md:97-98 says "a guest break stops `azhost`".** It does not. `run_batches` in `azhost_main.c` goes on to the next batch and to `--save`, and table row 0 lists `guest_break` under "Every batch ran". Reword it.

10. **Promised behaviours with no test:**
    - No test of `msg=` escaping `"` (`print_escaped` is static, with no unit or CLI test).
    - The exit-7 test (`test_cli_debug_stop_on_stock_core_exits_7`) was skipped in the agents' run because no stock core was set (`runs/v1/host-progress.md:14`). The exit-7 path has not run.
    - No test for the `--save` failure exit code.
    - No shared-table cases for the inputs in items 1 and 3.
    - In `test_profile_format.py`, the line-0 check only asserts that the path appears in the text.

11. **Spec gaps:**
    - Item 11 says to update phase-v1 section 1. MAIN's `docs/plans/phase-v1.md:19` still says "the environment variables of USING.md section 15". That file is on main, not on this branch.
    - Item 11 names `LAZ_CORE_OLD` as a test-only variable, but USING.md:322 leaves it out (`tests/python/test_threads_live.py:130` reads it).
    - Scripts now honour `LAZ_ROOT`, so `tests/gate-a.sh:32` (fetch.sh in a fresh copy) and `tools/mkrelease.sh` from a worktree follow an exported `LAZ_ROOT` into another tree. Unset it in gate-a.sh. No variable is set in this session; this is from reading the scripts.

## Nits

- `script_token` accepts `0x0x10` as 16, because `strtol` with base 16 skips its own `0x` (`host/input.c` script_token). I ran it. It also accepts `0X`, which USING.md:87 does not mention.
- `stop_every` does not go through `_index` (`emulator.py:312`). `1.5` raises a raw `TypeError` and `True` is taken as 1. `wall_limit="5"` raises a raw `TypeError`. I ran both. USING.md:137 says `ArgumentError` for every bad argument.
- USING.md:70 does not say that `print_escaped` drops `\r` from `msg=`.
- For more than 4096 lines azhost prints `UsageError: <path>: more than 4096 lines`, with no `line N`, unlike the format in USING.md:295. Python uses `:0:`, which USING.md:293 does not mention.
- `HostCrashed.signal_name` is public but missing from section 20.
- `__version__` and pyproject.toml still say 0.1.0. That is probably a later step; I did not check it against the plan.

## Checked and fine

- Items 4, 5, 6, 7, 8, 9, 10 and 13 match the spec; the commit says it skips the optional Touch/Circle range check.
- A missing `--state` file returns `AZH_E_SAVESTATE` (`state.c:171,393`), so it exits 9.
- The C parser's 511/512-byte, CR, 4096/4097-line, comment, empty-key and empty-value handling matches Python on every table case and on about 20 extra odd files of mine.
- The `Pool.__exit__` cancel test is sound.
- `run`/`run_until` signatures match the spec, and no positional callers are left in python/, tools/, examples/ or tests/.
