# Phase 8 C as-built review

**Verdict: ready with changes.** Four majors and 19 minors. Nothing breaks the 1.x promise or the frozen
`libazahar.__all__`. The ABI bump is clean: states keep meta ABI 3, the layout is unchanged, and an ABI 4 host is
refused before any call. Audio costs nothing when it is off. The command line follows section 3's exit table.
The majors:
- the untested movie call in the ABI 5 promise (finding 1);
- one docstring that describes the real component file's header (finding 2);
- no fast test of the audio plumbing, with one of its two documented return types never run (finding 3);
- two of the four C2 gate checks pass on an empty capture (finding 4).

Fix findings 2-4 before item 832 (C2) moves to done. C1 (item 831) has no majors. Fix finding 1 before C6 stages v1.2.0. The minors can
land in the same sonnet pass.

Reviewed: `git diff 22ceb34..HEAD -- python host tests testapp-tone Makefile docs/USING.md docs/HOST-API.md` on local
main (head c29d1fb): lane `cli` (C1, merge e30a80a) and lane `hostav` (C2, with the C3 host call, merge f71627a). Also
read: the Phase C rows of `docs/plans/phase-8.md`, `docs/plans/phase-8c-briefs.md`, item 833's notes,
`runs/p8/a4/notes.md` (for one point of finding 2), `~/.claude/c-golden-rules.md`, and `host/api.c`, `host/run.c`,
`host/core.c`, `host/state.c`, `python/libazahar/_slots.py`, `_client.py` and `_paths.py` where they back a claim.
Read-only: nothing was built or run (no make, no pytest, no emulator). `python3 -I tools/docs_check.py` passes.

## Findings

### Major

**1. The movie call ships in ABI 5 untested, and the docs say it plays a movie. Take it out before v1.2.0, unless C6a
and its live test land first.**
- Where: host/azhost.h:110-111; host/movie.c (all); host/api.c:381-384; host/libazhost.exports:18;
  python/libazahar/_host.py:29; python/libazahar/_worker.py:41-47; docs/HOST-API.md:25,50; docs/USING.md:123-127,273,490.
- What is wrong:
  - It has never run. Item 833 says the core's playback desyncs as soon as the app starts IR_RST, so no correct movie
    exists for it today. The error mapping in `core_code` (-2, -4, -5) and the call window (after `retro_load_game`,
    before `context_reset`) come from the patch's comments, not from a run.
  - HOST-API's promise is at source level: in 1.x the names, argument orders and meanings of the `azh_*` calls do not
    change. Publishing `azh_movie_play` in v1.2.0 freezes a contract before the core fix exists. That fix (type skipping,
    or one cursor per record type) may need more from the caller, such as which services the app starts.
  - HOST-API line 50 says it "plays a `.ctm` movie from boot", with no caveat. USING sections 4 and 12 say "the host can
    pass it a file", which reads as working.
  - `_host.load` now requires the symbol, so the dead call is part of the load check.
  - The worker's `args[8]` movie argument is unreachable: `Emulator` never sends a ninth argument, and no test sends one.
  - `azh_boot(app, state)` after `azh_movie_play` is not refused. A movie from boot plus a state load cannot both hold.
- Judgment: shipping it is wrong as things stand. A thin call the core already exports is cheap to keep, but only once
  something proves it. The ABI cost does not decide it: host and Python ship as one unit, and C6a rebuilds the core
  anyway.
- Fix:
  - Now: remove the worker's `args[8]` path, and say in HOST-API's row and in `azhost.h` that the call is unproven and
    the current core's playback desyncs.
  - Before v1.2.0 is staged (C6 step 1): if C6a's core patch and `test_exact_inputs_live.py` have not landed, remove
    `azh_movie_play` from the header, the exports, `_PROTOTYPES`, `boot_game` and the docs. Keep `movie.c` on a branch
    named in item 833. Bring it back with the patch (one ABI bump then, which is cheap). If it stays, `azh_boot` refuses
    a state together with a movie (`AZH_E_ARG`).

**2. The made-up component's docstring describes a field of the real file's header, and the field is not needed.**
- Where: tests/python/dsp_component.py:4,20.
- What is wrong:
  - "Our own bytes: an ASCII tag, a size word at 0x104, a fixed pattern elsewhere" tells the reader where the real file
    keeps its size. That describes the format of Nintendo's file, which the lane rules forbid in code comments and docs.
    Code may hold the path the app opens (line 21), and nothing more.
  - The phase A notes (`runs/p8/a4/notes.md:32`) say only libctru's fallback block path reads a u32 at 0x104. The
    file-read path that the tests use reads the whole file, and Azahar's high-level DSP only hashes it. So line 20
    writes a format detail that nothing uses.
- Fix:
  - Drop line 20 and the "size word at 0x104" words. The docstring becomes: "Our own bytes: an ASCII tag and a fixed
    pattern. Azahar's high-level DSP only logs a hash of the file."
  - Rerun `test_audio_live.py` on the PC to confirm.
  - The text is in local commit 44ad3c5. Ask `release-legal-audit` at C6 step 8 whether history needs rewriting before
    the first push of this range.

**3. The audio plumbing in Python has no fast test, and one of its two documented return types has never run.**
- Where: python/libazahar/emulator.py:152-184 (`_take`, `_drop`, `_samples`), 339-360; python/libazahar/_worker.py:60-81;
  docs/USING.md:302-303; python/libazahar/results.py:41-44.
- What is wrong:
  - The only test is the live `test_audio_live.py` on the PC. The fast suite (CI, `test.yml`) runs none of C2's Python.
  - USING promises a numpy `(n, 2)` array when numpy is installed, else an `array('h')`. Whichever of the two the PC
    lacks has never run, including the fallback's big-endian `byteswap`.
  - Nothing tests these:
    - `_take`'s byte-count check (the only guard that the file and the host's count agree);
    - the reply shape of `_op_run` (a three-tuple only with a path);
    - that the `finally` disarms the capture;
    - that `audio=False` sends a two-element request.
- Fix: a fast `test_audio.py`:
  - `_samples` on known bytes in both forms (monkeypatch the numpy import away);
  - `_take` with a short file (HostError, file removed);
  - `_op_run` against a fake `lib` recording its calls: `azh_audio_capture(path)`, then `azh_run`, then
    `azh_audio_info`, then `azh_audio_capture(None)`, with the last also on an `azh_run` failure;
  - `Emulator.run(audio=False)` sending exactly two arguments, through the fake worker.

**4. Two of the four C2 gate checks pass on an empty capture, and the stereo check cannot see a channel fault.**
- Where: tests/python/test_audio_live.py:54,62-63,66,86-87; plan row C2 (docs/plans/phase-8.md:187).
- What is wrong:
  - "Silence before the tone frame": `assert not any(pre_l) and not any(pre_r)` is true for an empty list. The test's
    own count comment (lines 67-69) says the core emits no samples until the DSP starts, so `before.audio` is empty.
    The check then proves nothing. It passes even if the first armed batch drops its audio entirely.
  - "Without the component file, there is no audio": the same vacuous `not any([])`. The log half (`ndsp_started=0`,
    a non-zero init code) is real.
  - `left == right` holds for swapped channels, and for a host that writes one channel twice. The app plays the same
    sample on both sides, so the stereo layout USING promises ("interleaved left, right") is unproven.
- Fix:
  - Say what is true and assert it. Either `len(pre_l) == 0` ("no samples before the sound starts"; update USING 12b),
    or, if the core does emit zeros there, a length within a frame of `START_FRAME * one_frame` and all zero.
  - The same for the no-component case: assert the exact length expected.
  - Make the tone app play different channels, for example right = -left, or right at half amplitude. Assert each
    channel's peak and sign so a swap or a duplicate fails.

### Minor

**5. `audio.raw` outlives a failed batch, and USING says it is removed when the batch returns.**
- Where: python/libazahar/emulator.py:339-360; docs/USING.md:310.
- What is wrong: on a HostError (an `azh_run` refusal), a HostTimeout or a HostCrashed, `request` raises. `_drop` is
  never reached, so the file stays in the workdir until the next audio batch. That is up to about 80 MB for a 10 minute
  batch. On Windows, a worker still holding the file open (finding 6) also defeats `unlink`.
- Fix: wrap from `request` to `_take` in `try/except BaseException: _drop(audio_file); raise`. Add the error case to the
  test of finding 3.

**6. The host's capture call has three edge faults.**
- Where: host/audio.c:49-55, 56-58, 62-65.
- What is wrong:
  - In phase DEAD (the first frame failed, `run.c:103`), `azh_audio_capture(NULL)` returns `AZH_E_ORDER` before it
    closes. The worker's `finally` then leaves the file open until `azh_close`.
  - A path that is too long is checked after the old capture is closed. Golden rule 7 (validate before acting): a
    refused call changes state.
  - When `fopen` fails, `cap_failed` stays 0, so a later `azh_audio_info` reports `AZH_OK` with 0 frames for a capture
    that never started.
- Fix:
  - A NULL path closes in any phase after open.
  - Check the length first.
  - Set `cap_failed = 1` when `fopen` or `setvbuf` fails.

**7. The new C relies on an unchecked thread claim, has few asserts, and has not been analyzed.**
- Where: host/audio.c:21-32, 74-90; host/movie.c:21-24, 46-60; host/frame.c:75-89.
- What is wrong:
  - "The core's callbacks run inside retro_run, on the run thread, so no lock" is the whole thread-safety argument.
    Unlike the input callbacks (`run.c:21,27`), `azh__audio_push` does not assert it. Phase A's matching sample count
    suggests the claim holds, but nothing checks it.
  - Golden rule 5: `azh_audio_info`, `azh__movie_clear`, `core_code` and both audio callbacks have no asserts.
    `*rate_out = (int32_t)(sample_rate + 0.5)` has no range check, and a NaN or huge rate is undefined behavior.
  - By reading, nothing that `clang --analyze` flags stands out: every return is checked or cast, there are no leaks on
    the `setvbuf` failure path, and the `void *` to function pointer copy uses `memcpy`. Nothing breaks the macOS clang
    build either:
    - `-Wmissing-prototypes`: every new extern is in `azh_internal.h` or `azhost.h`;
    - `-Wshadow`: nothing is shadowed;
    - `dlsym`: `dlfcn.h` on macOS, the `win_compat.h` macro on Windows;
    - the `Makefile` globs `host/*.c`, so both new files build on both halves.

    But `make check` has not run.
- Fix:
  - Export a run-thread check from `run.c` (for example `azh__in_run_thread()`) and assert it in `azh__audio_push`.
  - Add an assert or two to each function above, and assert `sample_rate > 0 && sample_rate < 1e6` before the cast.
  - Run `make check` on the PC (both halves) and read `test.yml`'s macOS build before C5 closes.

**8. "After a guest exit the audio is empty" is true on one path only.**
- Where: docs/USING.md:305; python/libazahar/emulator.py:346-354, 364-365.
- What is wrong: when the worker exits with `AZH_EXIT_GUEST_EXITED` (the stock core), the audio is empty. On our core,
  a guest exit can come back as a normal result with `stopped_by == "guest_exited"` (line 364), and then `_take` fills
  `audio`. On that path `audio_rate` stays 0 with an empty array. No test covers either path.
- Fix: "After a guest exit the audio may be empty (always on the stock core)". On the empty path, set `audio_rate`
  anyway, or document the 0.

**9. Two public texts go beyond the agreed sentence about the component file.**
- Where: docs/USING.md:313 ("and fails to start without it"); testapp-tone/README.md:6 ("Without it the audio library
  fails to start and no audio is produced").
- What is wrong: the agreed sentence is "the app's audio library looks for a component file on the SD card; the tests
  seed a made-up one, which Azahar's high-level DSP ignores apart from logging its hash". The additions describe libctru,
  not Nintendo's file, so the risk is low. But the rule is to use that sentence and no other wording.
- Fix: use the agreed sentence word for word in both places. Where the failure matters, point to the test instead:
  "`test_no_component_file_gives_silence` shows what happens without it".

**10. The ABI 4 refusal is untested, and its text is wrong for older hosts.**
- Where: python/libazahar/_host.py:43; tests/python/test_abi.py.
- What is wrong:
  - The refusal itself is right. An ABI 4 host lacks `azh_audio_capture`, so `load` raises HostError before the layout
    check. Without the missing symbols, `check_layout` would refuse `abi 4` anyway.
  - No test covers the missing-symbol branch.
  - The text now blames "the audio and movie calls" for every missing name, including `azh_threads` on an ABI 3 host.
- Fix:
  - Message: `host {path} lacks {name}: an older libazhost (this Python needs ABI {AZH_ABI_VERSION}); rebuild with make`.
  - Add a fast test with a stand-in `CDLL` that lacks `azh_audio_capture` and expects that message.
  - Add a test for `bad.abi = 4` beside the existing `abi = 3` case.

**11. The doctor's slot probe holds every free slot at once.**
- Where: python/libazahar/_cli.py:181-200, 203-210.
- What is wrong:
  - It is safe in the ways that matter:
    - the locks are `flock`/share-mode-0 handles, so the kernel frees them if the doctor dies;
    - the fds are `O_CLOEXEC`, so `lsof` does not inherit them;
    - another process's `acquire` only sleeps a 0.1 s round and retries.
  - But while the doctor holds them, the cap looks full. An acquirer with `LAZ_SLOT_TIMEOUT=0` or a sub-0.1 s timeout
    gets a false SlotTimeout, and the B7 pool test ("a third waits") can see a wait it did not cause.
  - `subprocess.TimeoutExpired` from a slow `lsof` (20 s each, up to 64 slots) is not caught: a traceback, exit 1.
- Fix:
  - Probe one index at a time. Open `slot-<k>.lock`, try `LOCK_NB`, and on success unlock and close at once, so at most
    one slot is held, for microseconds. Note in USING 2a that a zero-timeout acquirer can still lose that window.
  - Catch `TimeoutExpired` and `OSError` in `_holder_pid`, and report `unknown`.

**12. "The command never returns 1" is not quite true.**
- Where: docs/USING.md:55-56; python/libazahar/_cli.py:147-160.
- What is wrong: `command_run` catches only `LibAzaharError`. An `OSError` from `tempfile.mkdtemp`, from
  `_slots.slot_dir()`'s `mkdir`, or from a `--workdir` that is a file before Emulator wraps it escapes as a traceback,
  exit 1. USING section 3 already says an uncaught exception exits 1.
- Fix: catch `OSError` in `command_run` as 13 (with the JSON object when `--json`). Or change the sentence to "returns 1
  only for a bug (a Python traceback)".

**13. Some bad arguments exit 13, or only after a full boot.**
- Where: python/libazahar/_cli.py:61, 126, 289-291.
- What is wrong:
  - An unreadable `--inputs` file raises HostError, which exits 13 ("the worker or host crashed or could not run"). It
    is a bad argument, so it should exit 2.
  - `--frames 0` and `--shot 0` are refused by `Emulator.run`, after the Emulator has taken a slot and booted (a cold
    boot can take minutes), and only then exit 2.
- Fix:
  - Raise ArgumentError for an unreadable script. `test_script_unreadable_is_a_host_error` changes with it.
  - Give argparse a positive-int type for `--frames` and `--shot`, or check `1 <= shot <= frames` before the Emulator
    is made.

**14. Each run without `--workdir` leaves a full instance folder behind, and a bad script leaves an empty one.**
- Where: python/libazahar/_cli.py:149-152; docs/USING.md:47-48.
- What is wrong:
  - Keeping the temp folder on success is documented and useful: the shots live there.
  - Each run then leaves `host.map` (4.9 MB), the SD and a shader cache in `$TMPDIR`, and every run boots cold.
  - `mkdtemp` runs before `parse_script`, so a bad `--inputs` leaves an empty folder that the error JSON then names.
  - No test covers the default (made) workdir: every test passes `--workdir`.
- Fix:
  - Make the folder after the script parses.
  - Add one sentence to USING 2a: the size, and "pass `--workdir` to reuse a warm cache".
  - Add a test that runs without `--workdir` and asserts the folder named in the JSON exists afterwards.

**15. The JSON shape of a guest exit is not documented.**
- Where: docs/USING.md:51-53; python/libazahar/_cli.py:161-164.
- What is wrong: a guest exit prints `ok: false`, `exit_code: 10`, a `result` and `saved: null`, with no `error` key.
  USING describes only "on success" and "on an error".
- Fix: add "after a guest exit: `ok` false, `exit_code` 10, `result`, `saved` `null`".

**16. The guest-exit test passes `--save` but never checks that no save happened.**
- Where: tests/python/test_cli.py:168-171; python/libazahar/_cli.py:132.
- What is wrong:
  - `FakeEmu.closed` stays False after a guest-exit outcome, so the fake does save and `saved` is not null.
  - The test asserts only the code and `stopped_by`. Removing `and not emu.closed` would still pass.
- Fix: the fake sets `self.closed = True` when its outcome stops by `guest_exited`. Assert
  `json.loads(out)["saved"] is None`.

**17. The held-slot doctor test passes with a broken PID lookup or a probe that never releases.**
- Where: tests/python/test_cli.py:207-213.
- What is wrong: `f"slot {held.index}: pid"` also matches `pid unknown`. Nothing checks that the slots are free after
  `slot_report` returns.
- Fix:
  - Where `lsof` exists, assert `str(os.getpid())` in the line.
  - After the call, release `held` and `acquire(0.0)` the cap's worth of slots.

**18. `doctor: ok` can be printed without a boot.**
- Where: python/libazahar/_cli.py:229-231, 224.
- What is wrong:
  - With no `build/testapp.3dsx`, the boot is "skipped" and counted as working, so the doctor exits 0 having never
    started the core.
  - The core's version then appears nowhere. The C1 row asks for "host and core paths and versions".
  - USING 2a describes this honestly, but the last line, "doctor: ok", does not.
- Fix: print `doctor: ok (boot skipped: no test app)` in that case. Optionally read the core's version without a boot,
  by having the worker report the `core_name` and `core_version` it got from `azh_open`.

**19. Two doc lines miss `audio`.**
- Where: docs/USING.md:70-71 (the keyword-only list of `run`'s options); README.md:13 ("What does not work: … audio
  output").
- What is wrong: `audio` is a new keyword-only option of `run` and `run_until`. The README line is still true (nothing
  plays), but next to capture it reads as "no audio at all".
- Fix: add `audio` to the list. At C6 step 1, change the README to "audio playback (capture works, USING 12b)".

**20. The count check is wider than the plan's gate, and the plan does not say so.**
- Where: tests/python/test_audio_live.py:67-72; docs/plans/phase-8.md:187 ("sample count within one frame's worth").
- What is wrong: the test allows 3 frames short (a measured 1.6-frame start lag) and 1 frame long. The reason is good,
  but the plan row and item 832's Evidence still state the one-frame gate.
- Fix: write the measured lag and the [-3, +1] frame window into item 832's Evidence, or tighten the test. Run `before`
  over frames 1-59 and `rest` from frame 61, so that the lag falls outside `rest`.

**21. Section 20 does not mention the new `audio` argument.**
- Where: docs/USING.md:567 (the `run(frames, *, ...)` line), 576.
- What is wrong: the brief asked the hostav lane for its own block at the end of section 20. The lane edited the
  `RunResult` line instead. The promise list therefore names `audio` and `audio_rate` as fields, but not `audio=` as an
  argument of `run` and `run_until`.
- Fix: add one line, "`run(..., audio=False)` and `run_until(..., audio=False)`: section 12b", or a hostav block like the
  CLI's.

**22. The whole capture is held in memory, twice with numpy.**
- Where: python/libazahar/emulator.py:152-184.
- What is wrong: `_take` reads the whole file, and `astype("=i2")` copies it again. A 10 minute batch is about 80 MB on
  disk and about 160 MB in the parent at the peak. USING mentions the disk use only.
- Fix: one sentence in USING 12b. With numpy, `numpy.fromfile(path, "<i2")` reads it without the second copy.

**23. The tone app's build line does not name the pinned toolchain.**
- Where: testapp-tone/README.md:4.
- What is wrong: the brief pins devkitARM r67.1, and the system devkitARM is r68 since 11-17. The README's `PATH=`
  line works with either and does not say which one built the tested binary.
- Fix: "built and tested with devkitARM r67.1 (`DEVKITPRO=/c/devkitPro-r67.1` on
  the PC)".

## Checked and found right

- **The promise.**
  - `libazahar.__all__` is unchanged. The only new public names are `RunResult.audio`, `RunResult.audio_rate` and the
    `audio=` argument of `run` and `run_until`.
  - `audio` is left out of `==` and `repr`. `RunResult` was never hashable, because `shots` is a dict.
  - The CLI's flags match USING 2a and section 20. Its `--json` keys are those promised.
  - Its exit codes follow section 3's table: ArgumentError 2, BootError 3, a guest exit 10, GuestError 11, HostTimeout
    12, and SlotTimeout, HostCrashed, HostError and StateError 13. SlotTimeout is caught before HostTimeout, as phase
    B's review asked for the verdict example.
- **The ABI bump.**
  - `AZH_ABI_VERSION` is 5 in C and in Python. `AZH_STATE_META_ABI` stays 3, and `state.c:415` still accepts metas 2
    and 3, so old states load.
  - No struct changed: `test_layout_is_abi_5` keeps 151 rows and the same sizes.
  - The three new ctypes prototypes match the C signatures (`c_char_p`; `POINTER(c_int64)`, `POINTER(c_int32)`).
  - An ABI 4 host is refused before any call (finding 10 covers only the test and the text).
- **Cost when `audio=False`.** Python sends the two-element request, makes no file and makes no extra host calls. In C,
  the callbacks reach `azh__audio_push`, which returns on `cap_file == NULL`: one call and one branch per batch. Nothing
  is kept.
- **File lifetime on success.** The worker's `finally` closes the file before the reply leaves `_op_run`, so the parent
  reads a closed and flushed file (this also matters on Windows). `_take` removes it in every case once it is read.
  `azh_audio_info`'s `fflush` makes a write failure come back as `AZH_E_IO` before the parent reads.
- **JSON.**
  - The JSON is built generically from `dataclasses.fields`.
  - Arrays and bytes are dropped, and the `_SKIP` marker never escapes (`to_jsonable` filters it at every level).
  - `test_every_runresult_field_reaches_the_json` fails if a field is added and forgotten.
- **The script parser.**
  - Hex, a leading-zero decimal, the 511-byte limit before the comment is cut, NUL and CRLF are all handled.
  - Each failure case names its line, and the tests fail on a planted fault in each rule.
- **Legal, apart from findings 2 and 9.**
  - The only path to the component file is in code (`dsp_component.py:21`). It is the path the app opens.
  - `audio.c`, `frame.c`, `movie.c`, HOST-API and the tone app's source neither name nor describe the real file. No text
    says how to get one.
  - The tone app is our own code under GPLv3.

## Tests: can each one fail?

| Test | Planted fault it catches | Fault that passes anyway |
|---|---|---|
| `test_script_*` (5) | wrong split, octal leading zero, missing range check, a wrong line number | none found |
| `test_to_jsonable_drops_arrays…` | an array or bytes leaking into the JSON | none |
| `test_every_runresult_field_reaches_the_json` | a hand-written field list | none for the CLI's own use |
| `test_run_passes_the_options` | a dropped or renamed kwarg; shots or inputs not passed | `--sd-seed DIR` ignored (only `None` is checked) |
| `test_run_json_success_keys` | a wrong key or a wrong `saved` | none |
| `test_exit_codes_by_the_table` | any wrong code; SlotTimeout ordered after HostTimeout | none |
| `test_error_without_json_goes_to_stderr` | an error printed to stdout | none |
| `test_guest_exit_is_code_10` | a wrong code | a save after a guest exit (finding 16) |
| `test_bad_script_exits_2`, `test_usage_errors_exit_2`, `test_help…` | a wrong code; the Emulator made before parsing | none |
| `test_doctor_reports_the_parts…` | a doctor that exits 0 without a host | none |
| `test_doctor_counts_a_held_slot` | a wrong count | a bad PID lookup; slots never released (finding 17) |
| `test_vulkan_lines` | a "ready" line counted | none |
| `test_live_run_json`, `test_live_doctor` (PC) | a broken `-m` entry, a broken boot or shot path | none |
| `test_tone_is_captured` (PC) | no capture, wrong rate, wrong count, appended (untruncated) file, wrong pitch or gain, audio kept on `audio=False` (Python side) | a channel swap or duplicate; an empty first batch; the C capture left armed after the batch (findings 3 and 4) |
| `test_no_component_file_gives_silence` (PC) | the app starting its sound without the file | a broken capture: empty passes (finding 4) |
| `test_layout_is_abi_5` | a constant or size mismatch between C and Python | none |
| `test_memory_live` (the boot retry 10 to 20) | not a C change; only the retry budget grew | n/a |

## Not judged without a run

- `make check` (clang analyze) on the new C, on both halves; the macOS build in `test.yml` (finding 7).
- Whether the core calls the audio callbacks only from inside `retro_run` (finding 7's assert answers it).
- Whether `before.audio` is really empty, or holds zeros (finding 4).
- The guest-exit audio paths on both cores (finding 8).
- Anything about `azh_movie_play`: it has never run (finding 1).

Verdict: ready with changes.
