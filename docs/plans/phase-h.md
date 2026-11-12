# Step H: the docs a stranger can follow (item laz-410)

Brief for one sonnet builder, **revision 1** (2026-11-13). Phase index: `docs/plans/phase-4.md` (order, ownership,
merges, departures P9-P16, interfaces R1-R31, Guy's items G1-G9). Contract: `docs/PLAN.md:324` ("Phase H") and PLAN
section 5 (out of scope). Where this brief disagrees with PLAN.md on a goal, PLAN.md wins: stop and report, except the
approved departures of phase-2.md, phase-3.md and phase-4.md section 5, which you follow: P11 moves `NOTICES.md` to
step I (you only link it); P16 makes the README's route use **our released core**; the fresh clone moved from this
step to the main loop's I2 (review 1 S8): you write `tools/clone_check.sh`, the main loop runs it.

You work in `../libazahar-py-h` (branch `step-h`, made at main **after Phase 3 merged**). "MAIN" is
`/Users/guyshtainer/VSCodeProjects/3ds-toolkit/projects/libazahar-py`. After step 0's link, "OURS" is
`build-core/azahar_lazpy_libretro.dylib` (a link to MAIN's P9b core; read only) and "STOCK" is
`dl/azahar/azahar_libretro.dylib`. **Never commit, never edit item files, never write in MAIN, never push, never call
`gh`, never run `tools/build-core.sh`** (in a worktree it would delete MAIN's build tree through the `dl/` link). The
only network use is H0's `pip install`. Read first: the repo's `CLAUDE.md`, `docs/map/rules.md`, `docs/map/README.md`,
phase-4.md sections 0, 3, 5, 6 and 7, `~/.claude/git-publishing-preferences.md` (the "README + honest STATUS" and
"Credit & legal" parts), `~/.claude/ip-publishing-policy.md` (the "Method & terminology" part),
`~/.claude/python-golden-rules.md` (for `tools/docs_check.py` and the examples), `~/.claude/shell-golden-rules.md`
(for `tools/clone_check.sh`), and the item files 410, 310, 320, 330 and every `5-done/` item's Evidence (read only:
they say what is gated).

## 1. Goal and gate

A README a stranger can follow from a fresh clone to a working example, a STATUS that lists what works, what does
not and what was dropped, a finished USING guide, a host API reference, three examples, a docs checker and the
fresh-clone script; **no claim that no gate proved, and no number without its source, load and date.** The gate
(yours, headless, this Mac, in H1):

1. `python3 -I tools/docs_check.py --allow-missing NOTICES.md` passes (section 3.6; `NOTICES.md` is step I's file, so
   its link may dangle here; the main loop runs the check without the flag at I2). `python3 -I tools/docs_check.py
   --plant-red` fails with one line per planted fault.
2. The examples in your worktree (`nice -n 10`, one at a time except the pool): `examples/quickstart.py` prints
   `quickstart ok` with `LAZ_CORE=OURS` and again with STOCK; `examples/pool_shots.py` prints `pool_shots ok` (3
   instances through the slot cap); `examples/memory_watch.py` prints `memory_watch ok` with OURS, and with STOCK
   prints the one-line `NeedsLazpyCore` hint and exits 3.
3. `sh -n tools/clone_check.sh` is clean, and `sh tools/clone_check.sh --dry-run --repo "$PWD" --branch step-h --out
   runs/h-clone-dry` prints the commands it would run (the clone, the steps block, the build block, the quickstart,
   the pytest), each on its own line, and exits 0 without cloning or downloading. The real run is the main loop's, at
   I2, on main.

## 2. Facts (checked 2026-11-13; re-check the planned ones in H0)

- PLAN's Phase H deliverables: README (what it is, honest status, measured numbers with load and date, install in a
  venv, a 10-line example), `STATUS.md` (what works, what does not, what was considered and dropped: a fuller memory
  map, savestate parsing, an upstream pull request), `docs/USING.md` finished, `docs/HOST-API.md`, examples.
  PLAN section 5 lists the rest of "dropped / out of scope": Windows and Linux, audio output, any window, patching
  HID's touch truncation, Azahar's RPC server and gdb stub, commercial games in tests or docs, `.cia` installs,
  wireless, motion and camera, PyPI, a Python CLI, HOME, CI on GitHub runners (the first follow-up), Gen3D's adapter.
- **The only speed numbers that may appear** (rules.md 7: never an idle screen's): (a) step E's table in
  `docs/research/speed-table-e.md` (R18: the test app, labelled a light scene; every row has its load and date); (b)
  spike 2's real-scene table, `docs/research/spike-2-real-scene.md:30-42` (R19): 334-345 fps, 5.6-5.7x at load 26.7
  (16:07, 2026-11-12); 129 fps, 2.2x at load 68-96; 3 instances 136-138 fps each at load 58-90; 0.5-0.8 GB per
  instance; "a clean re-measure on a quiet machine is still owed". Spike 2's scene is a commercial game run locally
  (G9, default): the docs name no game; describe it as "one commercial game's 3D field scene, run locally, on a busy
  machine"; never attach or describe its pictures. Spike 1's ~50x and spike 2's "51x" (idle menus, R25) are **never**
  quoted.
- Memory per instance, state-boot ratio, input offsets: only from the items' Evidence or the research files (R20).
- **The README's route (P16):** `tools/fetch.sh --moltenvk --headers --lazpy-core --testapp` (MoltenVK and the headers
  from upstream; our core zip and `testapp.3dsx` from our release, all sha256-pinned; step I adds these flags,
  phase-i.md 3.4; no flag = today's set: stock core, MoltenVK, headers), then `make`, the venv, `LAZ_CORE` pointed at
  `dl/lazpy-core/azahar_lazpy_libretro.dylib` (fetch.sh prints the line), the quickstart. The route needs **no
  devkitARM**. The stock core is optional (plain `tools/fetch.sh` or `--stock-core`), for contributors comparing
  cores; ip-legal question 7 may remove it later (phase-4.md risk 12): write it as one optional line.
- Before the first release exists, the route's two release downloads cannot work from GitHub. I2's fresh clone sets
  `LAZ_RELEASE_BASE=file://<MAIN>/runs/release/v0.1.0` (fetch.sh's override) and is the only deviation from the
  README; I5 repeats it with the real URLs after publishing. Your gate does not run the route.
- **The build block** (contributors, and I2's test-app build from the tag's source, S12): `make testapp` needs
  `DEVKITPRO` and `DEVKITARM` set (testapp/Makefile:5-6, R8) and devkitARM first in PATH (Homebrew's arm gcc silently
  changes results). One line: `DEVKITPRO=/opt/devkitpro DEVKITARM=/opt/devkitpro/devkitARM
  PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make testapp` (review 1 B3: `env -i` drops them,
  so the block sets them itself).
- `pip install -e .` needs `setuptools>=77` (from PyPI) and Python 3.10 or newer (R11). **Apple's `/usr/bin/python3`
  is 3.9.6**, so Requirements says "Python 3.10 or newer (python.org or Homebrew; macOS's own `python3` is 3.9)". The
  worker runs `python -I`, so a venv, not the user site. **No pytest in any dependency or extra** (R11, B4): USING's
  contributor section and the clone run `.venv/bin/pip install pytest` first.
- **macOS 15 or later** (R31): the core's statically linked libcrypto is built for macOS 15.0, so the core needs
  macOS 15+ even though its header says 11.0; `build/libazhost.dylib` and `build/azhost` are minos 15.0. Requirements
  says "macOS 15 or later on Apple silicon"; STATUS's Known limits says the header mismatch. Never write "11.0".
- **Keys and certificates** (P9b, gated by F2, R1): our core is built without Azahar's built-in key data and its
  default HTTP client certificate, and it loads no keys. The docs say only: "Homebrew only. No keys, no system files,
  no encrypted titles. Our core is built without Azahar's built-in key data and default HTTP client certificate, and
  it loads no keys." Never explain how to supply keys or run encrypted titles.
- OpenSSL's compiled-in Homebrew paths (R30): the guest's HTTPS finds a CA file only where Homebrew's `openssl@3` is
  installed. One Known-limits line; it does not affect testing homebrew.
- **States** (R29): an ABI-3 host loads ABI-2 and ABI-3 states; an ABI-2 host refuses ABI-3 states. (Revision 0 had
  this backwards.)
- `SlotTimeout` is a `HostTimeout` (R14): `.op == "slot"`, `.seconds`, its text names the cap and the slot folder.
- Environment (R12): `LAZ_ROOT`, `LAZ_HOST`, `LAZ_CORE` (no default for our core: the default is the stock core's
  path), `LAZ_MVK`, `LAZ_PROFILE`, `LAZ_LAZPY_PROFILE`, `LAZ_MAX_INSTANCES`, `LAZ_SLOT_DIR`, `LAZ_SLOT_TIMEOUT`
  (default 3600 s), `LAZ_PNG_LEVEL` (0-9, default 1), `LAZ_LOG_LEVEL`, `LAZ_ANY_CORE`, `MVK_CONFIG_LOG_LEVEL`,
  `LAZ_STATE_ANY_APP`; tests only `LAZ_REQUIRE_EMULATOR`. **There is no `LAZ_LAZPY_CORE`.**
- `azhost` has **no `--help`** (R22): any other first argument prints the usage to stderr and exits non-zero
  (`azhost_main.c:34-40, 159-160`).
- D's USING section 11 already says repeats are exact only on our core (R21, 721209f): H0 confirms it.
- The repo's name and account: `https://github.com/GuyShtainer/libazahar-py` (not created yet: write the URL).
- Policy wording: "documented reverse engineering", never "clean room"; the non-affiliation lines; "ships no
  copyrighted content, bring your own homebrew"; Pokémon or Nintendo names only nominatively; art-free.
- The core binary's licence is GPLv3 (G4, a fact): Azahar is GPLv2 or later, and the binary links Apache-2.0 code
  (SPIRV-Tools, OpenSSL 3), which GPLv2 does not accept.

## 3. What to write

### 3.1 `README.md` (rewritten whole; about 120-160 lines; plain, short sentences)

In this order:
1. Title, then 2-3 lines: what it is (a headless host for Azahar's 3DS libretro core on macOS arm64, plus a Python
   layer: no window, several copies at once, buttons and touch, screenshots, savestates, guest memory on our core),
   who it is for (automated tests of 3DS homebrew), named after libmgba-py.
2. **Status** (3-6 lines): "v0.1.0, an early prerelease", the one-line list of what works with a pointer to
   `STATUS.md`, and what does not (the big ones only: macOS 15+ on Apple silicon only, no audio, homebrew only).
3. **Measured numbers**: one table, columns `What | Value | Scene | Load | Date | Source`. `Source` is
   `docs/research/<file>.md:<line>` (the line holding the value). Rows: E's light-scene x real time for 1 and 3
   instances on each core E measured, the host share, memory per instance; spike 2's real-scene row (single
   instance, load 26.7) and its loaded row (load 68-96). Under the table one line: "Speed depends on the scene and the
   machine's load; the light rows are the test app, the real-scene rows are one commercial game's scene run locally on
   a busy machine." No other number about speed anywhere in the README.
4. **Requirements**: macOS 15 or later on Apple silicon (R31), Xcode command-line tools, Python 3.10 or newer
   (python.org or Homebrew; macOS's own `python3` is 3.9), `curl`, `shasum` and `unzip` (stock). devkitARM is needed
   only to build the test app yourself.
5. **Install** (numbered): step 1 is `git clone https://github.com/GuyShtainer/libazahar-py && cd libazahar-py`; then
   the marker line `<!-- docs_check: steps -->` and one fenced `sh` block, one command per line, each with a `#`
   comment:
   ```
   tools/fetch.sh --moltenvk --headers --lazpy-core --testapp   # MoltenVK, headers, our core, the test app (sha256-pinned)
   make                                                         # build/libazhost.dylib and build/azhost
   python3 -m venv .venv && .venv/bin/pip install -e .          # the Python layer (editable install only)
   export LAZ_CORE="$PWD/dl/lazpy-core/azahar_lazpy_libretro.dylib"   # use our core (fetch.sh prints this line)
   .venv/bin/python examples/quickstart.py                      # prints "quickstart ok"
   ```
   Then "Build the test app yourself" with the marker `<!-- docs_check: steps-build -->` and one fenced `sh` block
   holding the build block line (section 2) and its comment ("instead of `--testapp`; needs devkitPro"). Then one
   optional line: "To compare with Azahar's unchanged core: `tools/fetch.sh --stock-core` (see `docs/USING.md`, Two
   cores)." Use the merged code's real commands; if a command differs, the block follows the code and you report it.
6. **Example**: the marker line `<!-- docs_check: quickstart -->`, then a fenced `python` block that is byte for byte
   `examples/quickstart.py` (section 3.5). About 10-15 lines.
7. **Two cores**: a small table, our core vs the stock core: where it comes from (our release via `fetch.sh
   --lazpy-core`, or `tools/build-core.sh` / Azahar's release via `fetch.sh --stock-core`), memory reads and writes,
   the watch list, the debug-text stop, exact repeats, poll-exact movies (only if F2 gated `lazpy_movie_play`; else
   "not tested"), key data and the default certificate (ours: removed). Each "yes" must be gated (a STATUS item). One
   plain line: "Point at a core with `LAZ_CORE=<path>`; without it the host uses the stock core's path,
   `dl/azahar/azahar_libretro.dylib`" (R12).
8. **Docs**: links to `STATUS.md`, `docs/USING.md`, `docs/HOST-API.md`, `examples/README.md`, `core/README.md`,
   `NOTICES.md`.
9. **Licence and credits**: libazahar-py is GPLv3 (`LICENSE`). Azahar (GPLv2 or later) by the Azahar and Citra
   teams; our patched core binary is distributed under GPLv3, with its complete source on the release page (G4);
   MoltenVK (Apache-2.0) and the stock core are downloaded by `fetch.sh` from their upstreams, never included; the
   libretro headers are MIT; `NOTICES.md` lists every component in the core; credit libmgba-py for the idea and name.
10. **Legal**: "Homebrew only. This repository and its releases contain no ROMs, game data, system files, NAND data,
    keys or encrypted titles. Our core is built without Azahar's built-in key data and default HTTP client
    certificate, and it loads no keys. Nintendo 3DS is a trademark of Nintendo; this project is not affiliated with or
    endorsed by Nintendo or by the Azahar project." Keep it to 3-5 lines.

### 3.2 `STATUS.md` (repo root; about 60-100 lines)

- `## What works` : one bullet per gated feature, each ending with `(laz-NNN)`, the item whose file is in
  `docs/status/lazpy/5-done/` and whose Evidence proves it (host library and CLI laz-120; test app laz-130; our core
  build laz-110; input and stops laz-210; Python layer and savestates laz-220; many instances and the speed table
  laz-310; our core's gate, including P9b's removed key data, certificate and key loading, laz-320; memory laz-330).
  If an item is not in `5-done/` when you write, its feature goes under "What does not work yet". docs_check
  enforces this (3.6).
- `## What does not work yet` : honest list (whatever was not gated, plus: macOS 15+ on Apple silicon only; the
  default instance cap rests on a light scene and stays provisional until a real-scene row exists, Phase 3 Q1; spike
  2's re-measure on a quiet machine is owed; poll-exact movies if not gated).
- `## Known limits` : stock-core runs do not repeat exactly (PLAN risk 3); touch rows 63, 125, 126, 127 (D's USING
  section 5); an ABI-3 host loads ABI-2 and ABI-3 states, an older host refuses newer states, and states may not load
  across core versions (R29); torn reads (G); one `azh_open` per process; the slot cap counts only libazahar's own
  workers; the v0.1.0 core's header says macOS 11.0 but it needs macOS 15 (its OpenSSL is built for 15, R31); the
  guest's HTTPS finds a CA file only where Homebrew's `openssl@3` is installed (R30; homebrew tests do not need it).
- `## Considered and dropped` : a fuller SET_MEMORY_MAPS table, savestate parsing, an upstream pull request (Guy:
  "no need to submit a pull request, we edit the core to our needs"), building OpenSSL ourselves for macOS 11-14
  (phase-4.md risk 9), and PLAN section 5's out-of-scope list, one line each with the reason in a few words.
- `## Next` : CI on GitHub runners (about 0.5 h), a quiet-machine real-scene speed row, Gen3D's adapter (Gen3D's own
  work).
- Dates: "as of <date>, commit <short sha of main at H0>". (If G8 rewrites history after H0, the main loop
  translates this SHA through `docs/commit-map-g8.tsv` when it commits; you write the SHA you saw.)

### 3.3 `docs/USING.md` (finish; keep D's and G's sections, edit only where a fact changed)

Add, after D's section 11 (stock core vs ours) or folded into it:
- **Many instances**: `Pool(n, app, root, ...)`, `submit`/`map`/`close`, one fresh instance per job in
  `root/job-NNNN/`; the machine-wide slot cap (`LAZ_MAX_INSTANCES`, default from E's rule; `LAZ_SLOT_DIR`;
  `LAZ_SLOT_TIMEOUT`, default 3600 s); `SlotTimeout` (a `HostTimeout`, `.op == "slot"`); `LoadWarning`; `nice`; the
  cap counts only libazahar's workers. The docstring example from phase-e 3.3.
- **Our core's profile**: F2's one line ("on our core `core/options-lazpy.txt` is applied first ..."),
  `--lazpy-profile FILE|none`, `LAZ_LAZPY_PROFILE`.
- **Environment**: one table of every variable in section 2's list (name, what it does, default, Python or host),
  checked against the code in H0. Includes `LAZ_PNG_LEVEL`, `LAZ_LOG_LEVEL`, `LAZ_ANY_CORE`, `MVK_CONFIG_LOG_LEVEL`,
  `LAZ_STATE_ANY_APP`; `LAZ_REQUIRE_EMULATOR` marked "tests only". No `LAZ_LAZPY_CORE`.
- **Cores table**: the README's table with the details (which option gives which property).
- **Getting our core**: the release (`tools/fetch.sh --lazpy-core`, then `LAZ_CORE` as printed) or build it
  (`nice -n 10 tools/build-core.sh --detach`, 15-90 min, `build-core/build.exit`; needs Homebrew `openssl@3` at the
  version in `core/PIN`); `core/README.md` for the patches, `core/OPENSSL.md` for OpenSSL.
- **Contributors**: `.venv/bin/pip install pytest`, then `.venv/bin/python -m pytest -q tests/python -m "not slow"`
  (the fast set needs no emulator); `make check` for the rest.
- **Troubleshooting**: MoltenVK missing (run `fetch.sh --moltenvk`); a downloaded dylib quarantined by a browser
  (`xattr -d com.apple.quarantine <file>`; curl sets none); devkitARM must come first in PATH and `DEVKITPRO`/
  `DEVKITARM` set for `make testapp`; `SlotTimeout` means other instances hold every slot (see the slot folder); the
  load warning; `HostTimeout` on the first frames (shader compiles: `boot_timeout`); the core refuses to load on macOS
  older than 15.
- Check every env variable and name in USING against the merged code (H0) and fix stale ones.

### 3.4 `docs/HOST-API.md` (about 80-120 lines plus the layout block)

For C users and for anyone reading the Python layer's worker: build (`make`; `build/libazhost.dylib`, header
`host/azhost.h`); the ABI version and `azh_abi_layout()` (callers check sizes and offsets at load, as `_abi.py`
does); the call order (open, options, boot, run/shot/stats/read/write, close; `azh_error`, `azh_abi_layout` any
time); one table of the `azh_*` functions, each with one line and "see `azhost.h` line N" (the header's comments are
the reference; do not restate struct fields); the error enum as a table (number, name, Python class); the map file in
one paragraph (what it holds; offsets come from `azhost layout`); the `azhost` CLI: it has no `--help`; paste the
usage text it prints for an unknown first argument (`build/azhost usage 2>&1`) verbatim in a fenced block, and say
it exits non-zero (N1); then `build/azhost layout`'s **full** output verbatim in a collapsed `<details>` block with
the date and commit (review 1 N10 declined: HOST-API has no length budget, and the full layout is the reference).
"The ABI may change before 1.0; each change bumps `AZH_ABI_VERSION`."

### 3.5 `examples/` (each runs from the repo root; stdlib only; each prints `<name> ok` as its last line on success and
exits non-zero with one plain line on failure)

- `quickstart.py` (10-15 lines, the README block): boot the test app (path argument, default `build/testapp.3dsx`)
  in `runs/quickstart/`, run about 300 frames holding A from a frame in the middle, ask a shot on the last frame,
  check (1) the batch ran the frames asked, (2) both screen PNGs exist with sizes 400x240 and 320x240 (read the PNG
  header with `struct`, no image library), (3) a log line after the press shows A in its `k=` field (the app's log is
  `emu.sd / "testapp/log.txt"` or wherever the merged API exposes the SD, R24; A is libctru bit 0); then print
  `quickstart ok`. The core comes from `LAZ_CORE` (the library's own default), so it runs on either core. Use the
  merged API's real names (R13); no import from `tests/`.
- `pool_shots.py`: `Pool(3, ...)` over three seeds (2D, 3D, 2D with `ready_at`), one shot each; check each job's
  folder and shot are separate; `pool_shots ok`. Either core.
- `memory_watch.py`: on our core read `addr_global` from the app's `start` line, `run(60, watch=[(addr_global,
  8)])`, check the 60 rows' magic (0x4C415A52) and consecutive frames, one `emu.memory.u32(addr_global + 4)`; print
  `memory_watch ok`. On the stock core catch `NeedsLazpyCore`, print one line ("needs our core: see README, Two
  cores") and exit 3.
- `examples/README.md`: one line per example, which core it needs, its run command.

### 3.6 `tools/docs_check.py` (stdlib, `python3 -I`, about 130-160 lines, functions under about 40 lines)

`python3 -I tools/docs_check.py [--allow-missing PATH ...] [--emit-steps README.md [--block build]] [--plant-red]`.
Checks, each printing `PASS <name>` or `FAIL <name>: <reason>`; the run exits 1 on any FAIL:

1. **numbers**: the README's "Measured numbers" table: every row has non-empty Value, Scene, Load and Date; every
   `Source` is `docs/research/<file>.md:<line>` naming a tracked file; every number token in Value **and in Load and
   Date** (regex `\d[\d,.:-]*`) appears in that line or within 2 lines of it (N2).
2. **forbidden**: none of `full speed`, `clean room`, `clean-room`, `aes_keys`, `seeddb`, `prod.keys`, `50x`, `51x`,
   `/Users/`, `macOS 11`, `LAZ_LAZPY_CORE` in README.md, STATUS.md, docs/USING.md, docs/HOST-API.md, examples/
   (case-insensitive).
3. **gated**: every bullet under STATUS.md's `## What works` ends with `(laz-NNN)` and
   `docs/status/lazpy/5-done/NNN-*.md` exists with an id line `id: laz-NNN`.
4. **quickstart**: the fenced block after `<!-- docs_check: quickstart -->` equals `examples/quickstart.py` byte for
   byte (one trailing newline normalised).
5. **steps**: a fenced `sh` block follows `<!-- docs_check: steps -->` and one follows `<!-- docs_check: steps-build
   -->`; the build block sets `DEVKITPRO` and `DEVKITARM` (B3). `--emit-steps README.md` prints the steps block only;
   `--block build` prints the build block only; both exit 0.
6. **links**: every relative Markdown link in README.md, STATUS.md, docs/USING.md, docs/HOST-API.md,
   examples/README.md resolves to a path in `git ls-files` **or** an untracked new file (`git ls-files -o
   --exclude-standard`, so uncommitted step files count), except paths given with `--allow-missing`. Anchors are not
   checked.
7. `--plant-red`: copies the five docs into a temp folder, plants one fault per check (a Value number not in its
   source line, a Date not in it, a `full speed`, a works bullet with `(laz-999)`, one changed byte in the example, a
   missing steps-build marker, a dead link), runs checks 1-6 on the copies, and passes only if each check fails
   exactly on its plant.

Revision 0's `stray-numbers` check is dropped (phase-4.md section 11: false-positive prone; `forbidden` holds the
known bad numbers and the as-built review reads for stray ones).

### 3.7 `tools/clone_check.sh` (POSIX sh, `set -eu`, about 70 lines; run by the main loop at I2 and I5)

`sh tools/clone_check.sh --repo <path or URL> --branch <name> --out <dir> [--release-base <url>] [--dry-run]`.
1. `rm -rf <out>`; `git clone --branch <branch> <repo> <out>/repo`.
2. A clean environment for every later command: `env -i HOME="$HOME"
   PATH=/Library/Frameworks/Python.framework/Versions/3.14/bin:/usr/bin:/bin:/usr/sbin:/sbin LANG=en_US.UTF-8`, plus
   `LAZ_RELEASE_BASE=<url>` only when `--release-base` is given (the one named deviation). The first PATH entry
   stands for "a Python 3.10+ installed as Requirements says"; if that folder is missing, find the newest
   `/Library/Frameworks/Python.framework/Versions/3.1*/bin` and say which.
3. In the clone: `python3 -I tools/docs_check.py --emit-steps README.md > <out>/steps.sh`, then `sh -eux
   <out>/steps.sh` (the README's steps, which end with the quickstart). The log must hold `quickstart ok`.
4. `python3 -I tools/docs_check.py --emit-steps README.md --block build > <out>/build.sh`, then `sh -eux
   <out>/build.sh` (it sets `DEVKITPRO`, `DEVKITARM` and PATH itself), then the quickstart again on the freshly built
   `build/testapp.3dsx` (must print `quickstart ok`).
5. `.venv/bin/pip install pytest` and `.venv/bin/python -m pytest -q tests/python -m "not slow"`.
6. Print `clone ok`, the wall time and `du -sh <out>/repo/dl`. Every step's output goes to `<out>/clone.log`; the
   exit code goes to `<out>/rc` from a `trap ... EXIT`; any failure exits non-zero naming the step.
`--dry-run` prints each command instead of running it. Nothing from MAIN or a worktree is used: no symlinked `dl/`,
no copied `vendor/`, no prebuilt `build/`.

## 4. Files (you create or edit only these)

| Path | Role |
|---|---|
| `README.md`, `STATUS.md` (new) | 3.1, 3.2 |
| `docs/USING.md`, `docs/HOST-API.md` (new) | 3.3, 3.4 |
| `examples/quickstart.py`, `pool_shots.py`, `memory_watch.py`, `examples/README.md` (all new) | 3.5 |
| `tools/docs_check.py`, `tools/clone_check.sh` (new) | 3.6, 3.7 |

Not yours: `NOTICES.md`, `tools/fetch.sh`, `pyproject.toml`, `python/libazahar/__init__.py`, `core/README.md` (step
I), every code file under `host/`, `python/`, `testapp/`, `tests/`, `core/`; `docs/research/*` (sources, read only),
`docs/map/*`, item files, the handoff, `docs/hours.tsv`. A code bug found while documenting is reported with the fix
you propose; the docs describe the code as it is. The map lines go in your report (the main loop commits them with
your files): `docs/map/code.md` (`examples/`, `STATUS.md`, `docs/HOST-API.md`), `docs/map/tools.md`
(`tools/docs_check.py`, `tools/clone_check.sh`), `docs/map/runners.md` (section 9).

## 5. Steps, with a checkpoint after each (save files as you go; never commit)

0. **H0: seed and check (about 0.05 h).** `mkdir -p dl build-core && for d in azahar moltenvk libretro-headers
   vulkan-headers azahar-src; do [ -e MAIN/dl/$d ] && ln -s MAIN/dl/$d dl/$d; done`, `ln -s
   MAIN/build-core/azahar_lazpy_libretro.dylib build-core/`, `cp -R MAIN/vendor .`, `make`, the build block line
   (section 2) for `make testapp`, `python3 -m venv .venv && .venv/bin/pip install -e . && .venv/bin/pip install
   pytest`. Then check phase-4.md section 6 rows R7-R25, R29 and R31 against the merged code: the Python names
   (`.venv/bin/python -I -c "import libazahar, inspect; ..."`), the env variables (`grep -n "LAZ_\|MVK_"
   python/libazahar/*.py host/*.c`), `build/azhost usage; echo $?` (no `--help`, N1), `build/azhost layout | head -3`,
   `vtool -show-build build/azhost build/libazhost.dylib`, D's USING section 11 line (S13), `ls docs/research/`, `ls
   docs/status/lazpy/5-done/`. Checkpoint: a table of rows that differ (row, what the code says), `runs/h/rows.md`.
1. **H1 (about 0.35 h).** Write section 3's files in the order 3.5 (examples first: they pin the API names), 3.6,
   3.7, 3.1, 3.2, 3.3, 3.4. Run gate 2 (all `nice -n 10`, one at a time except the pool, folders under `runs/`,
   ignored), then gates 1 and 3. Checkpoint: gates 1-3 output quoted; **the exact list of paths for the main loop to
   `git add`**, with the map lines. **End the run with the report "H1 done"** (section 9).
2. **Fixes (only when the joint as-built review or I2's clone finds faults in your files; the main loop resumes you
   with them).** Fix exactly the findings; re-run gates 1-3; report "H fixes done" with the changed paths.
3. Stop every waiter and background task you started (TaskStop) before each hand-back.

## 6. Machine-sharing rules

- At most one emulator at a time, except `pool_shots.py` (3, through the slot cap); everything nice'd; nothing timed.
  No window; PNGs read with the Read tool if you look at them. Never kill a process you did not start. Never write in
  MAIN.
- The only network use is H0's `pip install`. No `git push`, no `gh`, no clone (gate 3 is a dry run).
- No `sleep` polling; one Monitor wait per long run (an rc file from a `trap ... EXIT`, bounded), stopped before
  hand-back. Without Monitor, foreground parts under the 10-minute limit, and say so.

## 7. Writing rules

Plain, short sentences; no marketing words ("blazing", "seamless", "powerful"); say what a thing does, then how to
use it. Every claim is either gated (an item in `5-done/`) or written as "not yet" or "not tested". Numbers only from
section 2's sources, with load and date. Nominative names only; no game named. No screenshots in v0.1.0 (phase-4.md
section 11). Keep the README under about 160 lines: detail goes to USING. Never write a personal address, a
`/Users/` path or a machine name.

## 8. Interfaces assumed

phase-4.md section 6: R1 (the key sentence), R7-R9, R11-R25, R29-R31. If a merged name, flag or env variable
differs, follow the code and list the difference in the report.

## 9. The builder's report (H1 and fixes)

Gates 1-3 as printed (with `--plant-red`'s lines and the dry run's commands); `runs/h/rows.md`'s differences; the
paths to add; line counts per file; every number in the README with its source line; anything in the code that the
docs had to call "not yet" (with its item); proposed code fixes; the map lines; runners lines for
`docs/map/runners.md`:
```
python3 -I tools/docs_check.py                    # README numbers, the example and steps blocks, links, claims (step H's gate)
.venv/bin/python examples/quickstart.py           # prints "quickstart ok"
sh tools/clone_check.sh --repo "$PWD" --branch main --out runs/clone --release-base "file://$PWD/runs/release/v0.1.0"   # the fresh clone (I2)
```
and a final **"Lessons and notes"** block, ready to paste into item 410.

## 10. Hours (agent wall time)

Builder 0.4 h (H0 0.05, H1 0.35) and the commit 0.05 h: **0.45 h**, against PLAN.md's 0.5. The as-built review is
the joint one (phase-4.md, 0.2 h for H and I). The fresh clone moved to I2 (main loop's time, about 0.1 h less than
revision 0's H2 with its commit-resume cycle); `clone_check.sh` adds about 0.03 h; dropping `stray-numbers` saves
about 0.02 h. The example runs are machine time.

## 11. What H leaves for I and the main loop

The README names fetch.sh's `--moltenvk --headers --lazpy-core --testapp --stock-core` flags (I writes them); the
`NOTICES.md` link (I writes the file); `docs_check.py` without `--allow-missing` and `clone_check.sh` on main, both
at I2 (the main loop).

## 12. Review checklist (the joint opus as-built review)

1. Every number in README is in its source line, with load and date (both checked); no spike 1 or "51x" number;
   spike 2's rows labelled one commercial game's scene, local, busy machine; no game named.
2. Every "works" bullet maps to a done item whose Evidence proves that exact feature (open the item, not just its
   folder); nothing ungated is called working.
3. The steps block is the P16 route (our core, no devkitARM); the build block sets `DEVKITPRO` and `DEVKITARM`;
   `clone_check.sh` runs exactly those blocks in a clean environment, borrows nothing from MAIN, installs pytest, and
   its `--release-base` is the only deviation.
4. The example block equals `examples/quickstart.py`; the example checks something real (frames, both PNG sizes, the
   A press in the app's log), not just "no exception".
5. USING's names and env variables match the merged code (spot-check five; no `LAZ_LAZPY_CORE`; `LAZ_PNG_LEVEL` and
   the slot variables present); `SlotTimeout` described as a `HostTimeout`; states as R29; HOST-API cites `azhost.h`
   lines that exist; the pasted usage and layout outputs are current; "no `--help`" said.
6. Requirements and STATUS say macOS 15 or later (R31) and the header mismatch; the OpenSSL CA line is in Known
   limits.
7. Legal lines: no ROM/keys/system data; the key-data, certificate and key-loading sentence; non-affiliation with
   Nintendo and Azahar; no "clean room"; no key instructions; nominative names; the core binary under GPLv3.
8. `docs_check.py --plant-red` fails on each plant; the scripts follow the Python and shell golden rules (functions
   short, `-I`-safe, no network in docs_check).
9. Nothing committed; no item file, map, PLAN or research file edited; no write in MAIN; no push.
