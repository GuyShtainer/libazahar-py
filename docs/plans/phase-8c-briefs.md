# Phase 8 C briefs: two builder lanes (sonnet), then one review (opus)

Plan: `docs/plans/phase-8.md`, Phase C (line 180; rows C1-C6a). C4 is dropped: phase A measured file I/O under 1 % of
a state load (`runs/p8/a/decisions.md`). Two lanes run in parallel, each in its own worktree made at main by the main
loop. The phase B lane rules apply unchanged: `docs/plans/phase-8b-briefs.md`, "Rules for every lane". Every PC job
goes through `runs/p8/bin/pclane` and takes the shared PC lock.

## Lane `cli`: C1 the command line (item 831)

Read the C1 row (line 186) and do what it says.
- `python/libazahar/__main__.py` (it only calls `_cli.main`) and `python/libazahar/_cli.py` (argparse, standard library
  only).
- `python -m libazahar doctor` prints:
  - the OS, Python, the host and core paths and versions;
  - the slots in use, with their PIDs (`_slots`);
  - a 60-frame boot of the test app if it is present, with the Vulkan device lines from that boot's `host.log`
    ("unknown" without one).
  It exits 0 when every part works, else 1.
- `python -m libazahar run APP --frames N [--inputs FILE] [--shot F ...] [--state P] [--save P] [--json]`:
  - `--inputs` reads `azhost`'s input-script format (USING 4a). Reuse the parser if one exists in Python. Else write
    one, and test it against the examples in USING 4a.
  - `--json` prints one JSON object: the RunResult fields and the shot paths, or the error class with `.workdir` and
    `.log_path`.
  - Build the JSON from `dataclasses.fields(RunResult)` generically, leaving out values that are not JSON (arrays,
    bytes). The lane `hostav` adds audio fields to RunResult at the same time.
  - Exit codes come from USING section 3's table (the verdict codes 1, 12 and 13, plus 2, 3, 10 and 11).
- `--help` works on both commands.
- Tests:
  - `tests/python/test_cli.py` with the fake worker (`tests/python/fakeworker.py`; read how test_client uses it): fast,
    no emulator;
  - one live run of `run` and one of `doctor` on the PC.
- USING:
  - a new section "2a. The command line";
  - your own block at the end of section 20;
  - a line in section 3 if the CLI's exit codes differ in any way (they should not).
- `pyproject.toml`: a `libazahar` console script entry pointing at `libazahar._cli:main`, only if the project already
  declares scripts or the plan asks for it. Otherwise leave it to `python -m`, and say so.

## Lane `hostav`: C2 audio capture, then C3 exact inputs (items 832, 833)

Read the C2 and C3 rows (lines 187-188), `runs/p8/a4/notes.md` (the phase A probe: what works and why), and
`runs/p8/a4/host-audio.patch` (a scratch patch that counted samples; never merged).
- **Rules that bite in this lane:**
  - The DSP component file is our own made-up file only (`runs/p8/a4/mkcdc.py`: an ASCII tag and a fixed pattern).
    Never fetch, use or name Nintendo's DSP firmware, or any system file. Never write how to get one.
  - In public docs, say: "the app's audio library looks for a component file on the SD card; the tests seed a
    made-up one, which Azahar's high-level DSP ignores apart from logging its hash".
  - Host C stays free of libctru and citro; read `~/.claude/c-golden-rules.md`.
  - Host C builds only on the PC: run `make` in your lane through pclane. `vendor/` is in the repo; if it is not,
    copy it from `/d/lazpy/p7/w10/repo/vendor`.
  - The Mac build is checked later in CI (`test.yml`). Write C that builds with clang on macOS too: no Windows-only
    calls outside `host/plat/`.
- **C2:**
  - One ABI bump, to 5, in `host/azhost.h`. `AZH_STATE_META_ABI` stays 3 unless states change.
  - The host collects the core's audio batches (`retro_audio_sample` and `retro_audio_sample_batch`) per run batch
    into a file in the workdir, or a buffer the Python side reads.
  - `run(..., audio=True)` fills `RunResult.audio` (int16 stereo; a numpy array if numpy is present, else
    `array('h')` or bytes; pick one and document it) and `RunResult.audio_rate`. Without `audio=True` nothing is kept
    and nothing costs.
  - The tone app: move `runs/p8/a4/tone/` into the repo as `testapp-tone/` (its own README, the same license as
    `testapp/`). Build it on the PC with `DEVKITPRO=/c/devkitPro-r67.1` (the pinned devkitARM r67.1, never the r68 at
    `D:\devkitPro`).
  - Live test `tests/python/test_audio_live.py`, which skips with its reason when `build/testapp-tone.3dsx` is
    missing. It checks:
    - the sample count is within one frame's worth of the rate;
    - the tone's frequency, from the spectrum's peak, is 440 Hz within 2 %;
    - silence comes before the tone's start frame;
    - without the component file, there is no audio and the tone app's log shows its init failure.
- **C3:**
  - Python writes Azahar's movie file (`.ctm`) from a held-input movie, and calls `lazpy_movie_play` before boot
    (`core/patches/0006-lazpy-movie-play.patch`): `run(..., exact_inputs=True)`, from boot only.
  - Read the movie format from the pinned core's own source (`core/PIN`: Azahar tag 2126.2,
    `src/core/movie.cpp/.h`). Fetch that one file pair from GitHub at that commit; do not download the whole source.
  - The host needs a call that passes the path to the core's export before boot. Put it in the same ABI 5 bump.
  - If the movie needs a core change, stop C3: write what is needed into item 833's notes text in your final
    message.
  - Live test `tests/python/test_exact_inputs_live.py`: offset 0 for buttons, ZL/ZR, the circle pad and touch, over
    30 changes each, 3 repeats. It compares against USING 4's measured offsets, where today m = 0, 1, 1 and 2.
- **Docs:**
  - `docs/HOST-API.md`: ABI 5 and the new calls.
  - USING:
    - a new section "12b. Audio";
    - section 4: exact inputs and the movie-from-boot limit;
    - your own block at the end of section 20.
- The full fast suite and the live tests that touch the host (`test_c_checks.py`, `test_live_errors.py`) must still
  pass with the ABI 5 host. Run them once before you finish.

## The review (opus), after both lanes merge

`docs/reviews/phase-8c-as-built.md`, the same checks as phase B's review (the last section of phase-8b-briefs.md).
Also check:
- the ABI bump: old states still load; an ABI 4 host is refused with a clear error;
- the C diff, for anything that breaks the macOS build;
- the audio and movie docs against the legal rules above.
