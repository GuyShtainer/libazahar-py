# Phase 8 D briefs: four builder lanes (sonnet), then one review (opus)

Plan: `docs/plans/phase-8.md`, Phase D (line 208; rows D1-D5). Q4's recommended answers are in force: D after v1.2.0,
two releases (v1.3.0 after D), the hosted-runner state-boot bound records instead of failing, and the pinned MSYS2
Mesa download for D3. Each lane runs in its own worktree `runs/p8/wt/<lane>/` (branch `p8-<lane>`), made at main by
the main loop. The phase B lane rules apply unchanged: `docs/plans/phase-8b-briefs.md`, "Rules for every lane".
Every PC job goes through `runs/p8/bin/pclane` and takes the shared PC lock.

Rules added for phase D:
- **CI.** You never push and never dispatch a workflow: the main loop does, once the PC proves the same steps. Every
  failed GitHub run mails Guy, so new workflows start as `workflow_dispatch` only. Pin every action by full commit sha
  (as `core-win64.yml` does) and every download by sha256.
- **Release tools.** `tools/mkrelease.sh` and `tools/release_check.py` are shared by lanes `hostbin` and `ci`; only
  lane `hostbin` edits them.
- **The v1.2.0 promise.** Nothing in the Python API, `host/azhost.h`, the `azhost` command line, the exit codes or the
  file formats changes. A new public name joins the promise at v1.3.0 and goes in `tests/python/test_api.py`'s lists.

The interface lanes `hostbin` and `ci` share (fixed here, so they can run in parallel):
- `sh tools/fetch.sh --host` downloads the prebuilt host for the running system from the release (`REL_TAG`, or
  `LAZ_RELEASE_BASE` when set), checks its sha256 against a pin in `tools/fetch.sh`, and unpacks it into `build/`:
  `build/libazhost.dll` and `build/azhost.exe` on Windows, `build/libazhost.dylib` and `build/azhost` on macOS. Those
  are the paths the Python layer already reads (`python/libazahar/_paths.py`), so nothing else changes.
- The zips: `libazahar-py-host-<version>-windows-x64.zip` and `libazahar-py-host-<version>-macos-arm64.zip`, each
  with the two binaries, `LICENSE`, and a `SOURCE.md` naming the repository commit it was built from.
- The pins: `LAZPY_HOST_SHA_WIN` and `LAZPY_HOST_SHA_MAC`, both `TBD` until the binaries exist; `--host` with a `TBD`
  pin dies with one clear line (as `pin_set` does for the Windows core).

## Lane `hostbin`: D1 prebuilt host binaries (part of item 840)

Read the D1 row (line 212) and do what it says.
- `.github/workflows/host-bin.yml` (`workflow_dispatch` only):
  - a Windows job reusing `test-windows.yml`'s MSYS2 setup, header fetch and host build steps verbatim (copy them;
    do not refactor `test-windows.yml`);
  - a macOS job reusing `test.yml`'s header fetch and host build steps, then `codesign --force -s -` on both Mach-O
    files as the last step that touches them (R05 M3), and the macOS 15 / arm64 check `test.yml` runs;
  - each job zips its two binaries as above and uploads the zip as an artifact;
  - an attest job per zip, as `core-win64.yml`'s attest job does (`actions/attest-build-provenance` at the same sha),
    running only after both builds pass.
- `tools/fetch.sh --host`, as the interface above. Extend `tests/fetch_fallback.sh` if it covers the other pins.
- `tools/mkrelease.sh`: `--host-artifact-win DIR` and `--host-artifact-mac DIR` add the two zips to the release and
  to `SHA256SUMS`; without them the release is staged as today (v1.2.0's command line must still work unchanged).
- `tools/release_check.py`: rows for the two zips (present, in `SHA256SUMS`, the sha equals the pin, the zip holds
  exactly the listed files, `SOURCE.md` names a commit); a missing host zip is SKIP, not PASS. Its own tests run in
  `test.yml` ("the release check tests itself"): extend them.
- `tools/clone_check.sh`: `--no-build` follows the README's new no-compiler route instead of building the host (no
  `make`; `fetch.sh --host`). Keep every current mode as it is.
- README: a "no compiler" route for each system (fetch the host, the core and the test app; pip; quickstart), beside
  the current routes. `docs/USING.md`: only the section that lists `fetch.sh`'s flags.
- Gate (PC): build the host in your lane as today, zip it by hand as the workflow would, stage it with
  `LAZ_RELEASE_BASE=file:///...` (read how C6 staged v1.2.0: `docs/status/lazpy/5-done/830-phase-c-v1-2-0.md`), and
  run `clone_check.sh --no-build` against that staging on the PC. The hosted macOS run comes later, from the main loop.

## Lane `ci`: D2 the user CI recipe (part of item 840)

Read the D2 row (line 213) and do what it says.
- `docs/CI.md`: how a homebrew author runs their own app under libazahar-py in GitHub Actions on macOS, in plain steps.
- `examples/ci/macos.yml`: the recipe, a trimmed copy of `.github/workflows/macos-live.yml`: checkout, `fetch.sh
  --host --lazpy-core --testapp` (the interface above), pip, then `examples/verdict.py` on the user's app. Comments
  name what to change. Pin actions by sha as our workflows do.
- `.github/workflows/macos-live.yml`: one new step that runs the recipe's run-and-verdict part on our test app. Until a
  release carries the host zips, that step uses the host the job already builds (say so in a comment); after v1.3.0 it
  uses `fetch.sh --host`. Do not change the job's `continue-on-error` or how its result is read.
- `tests/python/test_state.py`'s state-boot bound (2.5 s, Guy's ruling): on a hosted runner (`GITHUB_ACTIONS=true`
  and `CI` set) the test records the time (print it and add it as a junit property with `record_property`) and does
  not fail on it; everywhere else it stays a gate, unchanged. A fast test proves both branches with the env patched.
- `docs/USING.md`: one line pointing at `docs/CI.md` in the section on testing, and the bound's hosted-runner rule
  where the bound is written (section 10a or the states section; find it).
- Gate (PC): the recipe's run-and-verdict commands run on the PC on the test app (pclane, live), and the fast test.

## Lane `wincilive`: D3 Windows emulator tests in CI (part of item 840)

Read the D3 row (line 214) and `runs/p8/a/decisions.md` section A5 (the lavapipe trial: inconclusive on the PC because
the elevated ssh session makes the Vulkan loader ignore `VK_DRIVER_FILES`). Read `runs/p8/a5/pins.txt` (MSYS2's mesa
package and its 15 runtime packages, sha256-pinned).
- `.github/workflows/test-windows-live.yml` (`workflow_dispatch` only): `test-windows.yml`'s steps, then download the
  pinned packages (sha256-checked, unpacked into a folder in the workspace, never into the MSYS2 install), register
  lavapipe's ICD JSON under `HKLM\SOFTWARE\Khronos\Vulkan\Drivers` on the runner (the runner is thrown away), fetch the
  lazpy core and the test app, and run the slow tests that need no second copy.
- The job is best effort until proven: `continue-on-error: true` on the job (so a red run mails no one), and its result
  is read from the pytest step's own outcome and summary line, as `macos-live.yml` does. A step before pytest prints
  the Vulkan device line from one short boot's `host.log`: a pass counts only when that line names lavapipe (A5's
  lesson).
- No PC registry change. The PC proves what it can: the download, sha256 checks and unpacking steps as a shell script
  the workflow calls (`tools/` or `.github/scripts/`, your pick), run on the PC through pclane as a fast job.
- Gate: the PC script run; the workflow passes `actionlint` if the PC has it (it may not: then say so). The main loop
  dispatches it three times; three passes of three, each naming lavapipe, and it may join the push trigger.

## Lane `gym`: D4 the gymnasium-style example (part of item 840)

Read the D4 row (line 215) and do what it says.
- `examples/gym_env.py`: an environment class with gymnasium's API (`reset`, `step`, `observation_space`,
  `action_space`), gymnasium imported only inside it and optional; outside the promise (say so at its top).
  - Observation: the top screen as an array. Action: a small discrete set of the test app's buttons.
  - Reward: from `emu.memory` (a value the test app keeps; read `testapp/README.md` and `tests/testapp_log.py`).
  - `reset` loads a state and releases every held input (B1).
- `examples/README.md`: one line. `docs/USING.md`: none (the example is outside the promise).
- Gate (PC, live): gymnasium's own `gymnasium.utils.env_checker.check_env` passes, then 200 steps run. gymnasium is
  not on the PC: make a lane venv under your PC lane folder with `--system-site-packages` from `$PY` and pip install
  one pinned gymnasium version into it. Nothing outside your lane folder. If pip is refused, stop and report.
- A fast test that imports the example without gymnasium and gets the clear "install gymnasium" error.

## Review: D5 (opus, after the four lanes merge)

The main loop writes this brief at merge time from the four lanes' final messages, as `phase-8c-briefs.md` did.
