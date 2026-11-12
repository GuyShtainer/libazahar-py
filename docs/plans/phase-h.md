# Step H: the docs a stranger can follow (item laz-410)

Brief for one sonnet builder, revision 0 (2026-11-12). Phase index: `docs/plans/phase-4.md` (order, ownership,
merges, departures, interfaces). Contract: `docs/PLAN.md:324` ("Phase H") and PLAN section 5 (out of scope). Where
this brief disagrees with PLAN.md on a goal, PLAN.md wins: stop and report (except the approved departures P1-P13 of
phase-2.md, phase-3.md and phase-4.md section 5, which you follow; P11 moves `NOTICES.md` to step I, so you only
link it).

You work in `../libazahar-py-h` (branch `step-h`, made at main **after Phase 3 merged**). "MAIN" is
`/Users/guyshtainer/VSCodeProjects/3ds-toolkit/projects/libazahar-py`. "OURS" is
`MAIN/build-core/azahar_lazpy_libretro.dylib` (absolute; read only); "STOCK" is `dl/azahar/azahar_libretro.dylib`.
**Never commit, never edit item files, never write in MAIN, never push, never touch the network except the fresh
clone's own downloads in H2.** Read first: the repo's `CLAUDE.md`, `docs/map/rules.md`, `docs/map/README.md`,
phase-4.md sections 0, 3, 5, 6, `~/.claude/git-publishing-preferences.md` (the "README + honest STATUS" and "Credit &
legal" parts), `~/.claude/ip-publishing-policy.md` (the "Method & terminology" part), `~/.claude/python-golden-rules.md`
(for `tools/docs_check.py` and the examples), and the item files 410, 310, 320, 330 and every `5-done/` item's
Evidence (read only: they say what is gated).

## 1. Goal and gate

A README a stranger can follow from a fresh clone to a working example, a STATUS that lists what works, what does
not and what was dropped, a finished USING guide, a host API reference and three examples; **no claim that no gate
proved, and no number without its source, load and date.** The gate (headless, this Mac):

1. `python3 -I tools/docs_check.py --allow-missing NOTICES.md` passes (section 3.6's checks; `NOTICES.md` is step
   I's file, P11, so on this branch its link may dangle; the main loop runs the check without the flag after both
   merges). `python3 -I tools/docs_check.py --plant-red` must fail with one line per planted fault (section 3.6).
2. **The fresh clone (H2):** after the main loop commits H1 on `step-h`, `git clone --branch step-h
   ../libazahar-py-h runs/h-clone/repo` (inside your worktree's ignored `runs/`); in the clone, under a clean
   environment (`env -i HOME="$HOME" PATH=/Library/Frameworks/Python.framework/Versions/3.14/bin:/usr/bin:/bin:
   /usr/sbin:/sbin LANG=en_US.UTF-8`, so no `LAZ_*` variable, no conda and no venv leaks in; the first PATH entry
   stands for "a Python 3.10+ installed as README's Requirements say", because Apple's `/usr/bin/python3` is 3.9.6),
   run exactly the README's steps block (`python3 -I tools/docs_check.py --emit-steps
   README.md > runs/h-clone/steps.sh`, then `sh -eux runs/h-clone/steps.sh` with the clone as cwd). It ends with
   `examples/quickstart.py` printing `quickstart ok` as its last line. **Nothing from MAIN or your worktree**: no
   symlinked `dl/`, no copied `vendor/`, no prebuilt `build/`. The log `runs/h-clone/steps.log` and an rc file.
3. In the same clone after step 2: `.venv/bin/python -m pytest -q tests/python -m "not slow"` passes (the install
   works without our core; phase-4.md Q3).
4. In your worktree with OURS (H1, not the clone): `LAZ_CORE=OURS .venv/bin/python examples/memory_watch.py` prints
   `memory_watch ok`; with STOCK it prints the `NeedsLazpyCore` hint and exits 3 (section 3.5).
   `examples/pool_shots.py` prints `pool_shots ok` (3 instances through the slot cap).

## 2. Facts (checked 2026-11-12; re-check the planned ones in H0)

- PLAN's Phase H deliverables: README (what it is, honest status, measured numbers with load and date, install in a
  venv, a 10-line example), `STATUS.md` (what works, what does not, what was considered and dropped: a fuller memory
  map, savestate parsing, an upstream pull request), `docs/USING.md` finished, `docs/HOST-API.md`, examples.
  PLAN section 5 lists the rest of "dropped / out of scope": Windows and Linux, audio output, any window, patching
  HID's touch truncation, Azahar's RPC server and gdb stub, commercial games in tests or docs, `.cia` installs,
  wireless, motion and camera, PyPI, a Python CLI, HOME, CI on GitHub runners (the first follow-up), Gen3D's adapter.
- **The only speed numbers that may appear** (rules.md 7: never an idle screen's): (a) step E's table in
  `docs/research/speed-table-e.md` (test app, labelled a light scene; every row has its load and date); (b) spike 2's
  real-scene table, `docs/research/spike-2-real-scene.md:30-43`: 334-345 fps, 5.6-5.7x at load 26.7 (16:07,
  2026-11-12); 129 fps, 2.2x at load 68-96; 3 instances 136-138 fps each at load 58-90; 0.5-0.8 GB per instance;
  "a clean re-measure on a quiet machine is still owed". Spike 2's game is commercial and local: name it as "a
  Gen-3 3D-field homebrew scene (Gen3D) on a busy machine", never attach or describe its pictures. Spike 1's
  ~50x (an idle menu) is **never** quoted.
- Memory per instance, state-boot ratio, input offsets: only from the items' Evidence or the research files
  (step D's gate measured the state boot's wall time ratio; step C's report the input offsets m).
- `tools/fetch.sh` downloads the stock core zip (7.35 MB), MoltenVK (59.6 MB), the libretro and Vulkan headers;
  `make` builds `build/libazhost.dylib` and `build/azhost`; `make testapp` builds `build/testapp.3dsx` with
  devkitARM first in PATH (`PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH`; Homebrew's arm gcc
  silently changes results). `pip install -e .` needs `setuptools>=77` (from PyPI, network) and Python 3.10 or newer
  (this Mac: python.org's 3.14.0 first in PATH). **Apple's `/usr/bin/python3` is 3.9.6** (checked 2026-11-12), so on
  a stock Mac `pip install -e .` fails on `requires-python`: the README's Requirements line says "Python 3.10 or newer
  (python.org or Homebrew; macOS's own `python3` is 3.9)", and the steps block uses `python3` as found first in PATH.
  The worker runs `python -I`, so a venv, not the user site.
- After step I, users without devkitARM get `testapp.3dsx` and our core from the release with `tools/fetch.sh
  --testapp` and `tools/fetch.sh --lazpy-core` (step I's flags, phase-i.md 3.4). Write those lines in the README as
  "after the first release"; your gate does not run them.
- The repo's name and account: `https://github.com/GuyShtainer/libazahar-py` (not created yet: write the URL; it is
  right once Guy creates the repo).
- Policy wording: say "documented reverse engineering" and never "clean room"; non-affiliation disclaimer; "ships no
  copyrighted content, bring your own homebrew"; Pokémon or Nintendo names only nominatively; art-free.
- Keys: the docs never explain how to supply console keys or run encrypted titles. Say only: "Homebrew only. No
  keys, no system files, no encrypted titles; our core is built without Azahar's built-in key blob" (P9; if P9 is not
  done when you write, say nothing about the blob and report it).

## 3. What to write

### 3.1 `README.md` (rewritten whole; about 120-160 lines; plain, short sentences)

In this order:
1. Title, then 2-3 lines: what it is (a headless host for Azahar's 3DS libretro core on macOS arm64, plus a Python
   layer: no window, several copies at once, buttons and touch, screenshots, savestates, guest memory on our core),
   who it is for (automated tests of 3DS homebrew), named after libmgba-py.
2. **Status** (3-6 lines): "v0.1.0, an early prerelease", the one-line list of what works with a pointer to
   `STATUS.md`, and what does not (the big ones only: macOS arm64 only, no audio, homebrew only).
3. **Measured numbers**: one table, columns `What | Value | Scene | Load | Date | Source`. `Source` is
   `docs/research/<file>.md:<line>` (the line holding the value). Rows: E's light-scene x real time for 1 and 3
   instances on each core E measured, the host share, memory per instance; spike 2's real-scene row (single
   instance, load 26.7) and its loaded row (load 68-96). Under the table one line: "Speed depends on the scene and the
   machine's load; the light rows are the test app, the real-scene rows are one game on a busy machine." No other
   number about speed anywhere in the README.
4. **Requirements**: macOS on Apple silicon (tested on macOS 15 arm64; built for 11.0 and later, untested there),
   Xcode command-line tools, Python 3.10+, `curl` and `shasum` (stock), devkitPro's devkitARM only to build the test
   app yourself.
5. **Install** (numbered): step 1 is `git clone https://github.com/GuyShtainer/libazahar-py && cd
   libazahar-py`; then the steps block, preceded by the marker line `<!-- docs_check: steps -->` and written as one
   fenced `sh` block, one command per line, each with a `#` comment:
   ```
   tools/fetch.sh                                       # the stock core, MoltenVK, headers (sha256-pinned)
   make                                                 # build/libazhost.dylib and build/azhost
   python3 -m venv .venv && .venv/bin/pip install -e .  # the Python layer (editable install only)
   PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make testapp   # build/testapp.3dsx
   .venv/bin/python examples/quickstart.py              # prints "quickstart ok"
   ```
   Below the block: "No devkitARM? After the first release, `tools/fetch.sh --testapp` downloads our
   `testapp.3dsx` instead of `make testapp`." Use the merged code's real commands; if any differ, the block follows
   the code.
6. **Example**: the marker line `<!-- docs_check: quickstart -->`, then a fenced `python` block that is
   byte-for-byte `examples/quickstart.py` (section 3.5). About 10-15 lines.
7. **Two cores**: a small table, stock core vs our core: where it comes from (fetch.sh from Azahar's release / our
   release or `tools/build-core.sh`), memory reads and writes, the watch list, the debug-text stop, exact repeats,
   poll-exact movies (only if F2 gated `lazpy_movie_play`; else "not tested"). Each "yes" must be gated (STATUS item).
   One line: how to point at our core (`LAZ_CORE=<path>` or the default path the code uses: check `_paths.py`).
8. **Docs**: links to `STATUS.md`, `docs/USING.md`, `docs/HOST-API.md`, `examples/README.md`, `core/README.md`,
   `NOTICES.md`.
9. **Licence and credits**: libazahar-py is GPLv3 (`LICENSE`). Azahar (GPLv2 or later) by the Azahar and Citra
   teams; our patched core binary is distributed under GPLv3 with its source on the release page (phase-4.md G4: if
   Guy has not answered, write "under the GPL" and report); MoltenVK (Apache-2.0) and the stock core are downloaded
   by `fetch.sh`, never included; the libretro headers are MIT; credit libmgba-py for the idea and names.
10. **Legal**: "Homebrew only. This repository and its releases contain no ROMs, game data, system files, NAND
    data, keys or encrypted titles. Nintendo 3DS is a trademark of Nintendo; this project is not affiliated with or
    endorsed by Nintendo or by the Azahar project." Keep it to 3-4 lines.

### 3.2 `STATUS.md` (repo root; about 60-100 lines)

- `## What works` : one bullet per gated feature, each ending with `(laz-NNN)`, the item whose file is in
  `docs/status/lazpy/5-done/` and whose Evidence proves it (host library and CLI laz-120; test app laz-130; our core
  build laz-110; input and stops laz-210; Python layer and savestates laz-220; many instances and the speed table
  laz-310; our core's gate laz-320; memory laz-330). If an item is not in `5-done/` when you write, its feature goes
  under "What does not work yet". docs_check enforces this (3.6).
- `## What does not work yet` : honest list (whatever was not gated, plus: macOS arm64 only; the default instance
  cap rests on a light scene and stays provisional until a real-scene row exists, Phase 3 Q1; spike 2's re-measure
  on a quiet machine is owed; poll-exact movies if not gated).
- `## Known limits` : stock-core runs do not repeat exactly (PLAN risk 3); touch rows 63, 125, 126, 127 (D's USING
  section 5); states may not load across core versions, and ABI-2 states are refused after ABI 3; torn reads (G);
  one `azh_open` per process; the cap counts only libazahar's own workers.
- `## Considered and dropped` : a fuller SET_MEMORY_MAPS table, savestate parsing, an upstream pull request (Guy:
  "no need to submit a pull request, we edit the core to our needs"), and PLAN section 5's out-of-scope list, one line
  each with the reason in a few words.
- `## Next` : CI on GitHub runners (about 0.5 h), a quiet-machine real-scene speed row, Gen3D's adapter (Gen3D's own
  work).
- Dates: "as of <date>, commit <short sha of main at H0>".

### 3.3 `docs/USING.md` (finish; keep D's and G's sections, edit only where a fact changed)

Add, after D's section 11 (stock core vs ours) or folded into it:
- **Many instances**: `Pool(n, app, root, ...)`, `submit`/`map`/`close`, one fresh instance per job in
  `root/job-NNNN/`; the machine-wide slot cap (`LAZ_MAX_INSTANCES`, default from E's rule; `LAZ_SLOT_DIR`,
  `LAZ_SLOT_TIMEOUT`); `LoadWarning`; `nice`; the cap counts only libazahar's workers. The docstring example from
  phase-e 3.3.
- **Our core's profile**: F2's one line ("on our core `core/options-lazpy.txt` is applied first ..."), `--lazpy-profile`,
  `LAZ_LAZPY_PROFILE`.
- **Cores table**: the README's table with the details (which option gives which property).
- **Getting our core**: the release (`tools/fetch.sh --lazpy-core`, after the first release) or `nice -n 10
  tools/build-core.sh --detach` (15-90 min, `build-core/build.exit`); `core/README.md` for the patches and updates.
- **Troubleshooting**: MoltenVK missing (run `fetch.sh`); a downloaded dylib quarantined by a browser (`xattr -d
  com.apple.quarantine <file>`; curl sets none); devkitARM must come first in PATH; a slot timeout means other
  instances hold every slot; the load warning; `HostTimeout` on the first frames (shader compiles: `boot_timeout`).
- Check every env variable and name in USING against the merged code (H0) and fix stale ones.

### 3.4 `docs/HOST-API.md` (about 80-120 lines)

For C users and for anyone reading the Python layer's worker: build (`make`; `build/libazhost.dylib`, header
`host/azhost.h`); the ABI version and `azh_abi_layout()` (callers check sizes and offsets at load, as `_abi.py`
does); the call order (open, options, boot, run/shot/stats/read/write, close; `azh_error`, `azh_abi_layout` any
time); one table of the `azh_*` functions, each with one line and "see `azhost.h` line N" (the header's comments are
the reference; do not restate struct fields); the error enum as a table (number, name, Python class); the map file in
one paragraph (what it holds; offsets come from `azhost layout`); the `azhost` CLI (`run`, `layout`; paste `build/azhost
--help` or its usage output verbatim in a fenced block); `build/azhost layout` output verbatim in a collapsed
`<details>` block, with the date and commit. "The ABI may change before 1.0; each change bumps `AZH_ABI_VERSION`."

### 3.5 `examples/` (each runs from the repo root; stdlib only; each prints `<name> ok` as its last line on success and
exits non-zero with one plain line on failure)

- `quickstart.py` (10-15 lines, the README block): boot the test app (path argument, default `build/testapp.3dsx`)
  in `runs/quickstart/`, run about 300 frames holding A from a frame in the middle, ask a shot on the last frame,
  check (1) the batch ran the frames asked, (2) both screen PNGs exist with sizes 400x240 and 320x240 (read the PNG
  header with `struct`, no image library), (3) a log line after the press shows A in its `k=` field (the app's log
  is `emu.sd / "testapp/log.txt"` or wherever the merged API exposes the SD; A is libctru bit 0); then print
  `quickstart ok`. Use the merged API's real names (R13); no import from `tests/`.
- `pool_shots.py`: `Pool(3, ...)` over three seeds (2D, 3D, 2D with `ready_at`), one shot each; check each job's
  folder and shot are separate; `pool_shots ok`.
- `memory_watch.py`: on our core read `addr_global` from the app's `start` line, `run(60, watch=[(addr_global,
  8)])`, check the 60 rows' magic (0x4C415A52) and consecutive frames, one `emu.memory.u32(addr_global + 4)`; print
  `memory_watch ok`. On the stock core catch `NeedsLazpyCore`, print one line ("needs our core: see README, Two
  cores") and exit 3.
- `examples/README.md`: one line per example, which core it needs, its run command.

### 3.6 `tools/docs_check.py` (stdlib, `python3 -I`, about 120-160 lines, functions under about 40 lines)

`python3 -I tools/docs_check.py [--allow-missing PATH ...] [--emit-steps README.md] [--plant-red]`. Checks, each
printing `PASS <name>` or `FAIL <name>: <reason>` and the run exiting 1 on any FAIL:

1. **numbers**: the README's "Measured numbers" table: every row has non-empty Value, Scene, Load and Date; every
   `Source` is `docs/research/<file>.md:<line>` naming a tracked file; every number token in Value (regex
   `\d[\d,.]*`) appears in that line or within 2 lines of it.
2. **stray-numbers**: outside that table, the README, STATUS.md and USING.md contain no speed-like token:
   `\b\d+(\.\d+)?\s?x\b` (x real time), `fps`, `real time` with a digit in the same sentence, except inside lines that
   cite `docs/research/` (USING may cite). Version strings (`2126.2`, `3.10`, `v0.1.0`, `1.4.2`) are not speed tokens.
3. **forbidden**: none of `full speed`, `clean room`, `clean-room`, `aes_keys`, `seeddb`, `prod.keys`, `50x`,
   `51x`, `/Users/` in README.md, STATUS.md, docs/USING.md, docs/HOST-API.md, examples/ (case-insensitive).
4. **gated**: every bullet under STATUS.md's `## What works` ends with `(laz-NNN)` and
   `docs/status/lazpy/5-done/NNN-*.md` exists with an id line `id: laz-NNN`.
5. **quickstart**: the fenced block after `<!-- docs_check: quickstart -->` equals `examples/quickstart.py` byte for
   byte (one trailing newline normalised).
6. **steps**: a fenced `sh` block follows `<!-- docs_check: steps -->`; `--emit-steps` prints it (only it) and exits
   0.
7. **links**: every relative Markdown link in README.md, STATUS.md, docs/USING.md, docs/HOST-API.md,
   examples/README.md resolves to a path in `git ls-files` **or** an untracked-but-new file of this step (so H1's
   uncommitted files count; list them with `git ls-files -o --exclude-standard`), except paths given with
   `--allow-missing`. Anchors (`#...`) are not checked.
8. `--plant-red`: copies the five docs into a temp folder, plants one fault per check (a number not in its source
   line, a stray `9x`, a `full speed`, a works bullet with `(laz-999)`, one changed byte in the example, a missing
   steps marker, a dead link), runs checks 1-7 on the copies, and passes only if each check fails exactly on its plant.

## 4. Files (you create or edit only these)

| Path | Role |
|---|---|
| `README.md`, `STATUS.md` (new) | 3.1, 3.2 |
| `docs/USING.md`, `docs/HOST-API.md` (new) | 3.3, 3.4 |
| `examples/quickstart.py`, `pool_shots.py`, `memory_watch.py`, `examples/README.md` (all new) | 3.5 |
| `tools/docs_check.py` (new) | 3.6 |

Not yours: `NOTICES.md`, `tools/fetch.sh`, `pyproject.toml` (step I), every code file under `host/`, `python/`,
`testapp/`, `tests/`, `core/`; `docs/research/*` (sources, read only), `docs/map/*`, item files, the handoff,
`docs/hours.tsv`. A code bug found while documenting is reported with the fix you propose; the docs describe the code
as it is.

## 5. Steps, with a checkpoint after each (save files as you go; never commit)

0. **H0: seed and check (about 0.05 h).** `mkdir -p dl && for d in azahar moltenvk libretro-headers vulkan-headers
   azahar-src; do [ -e MAIN/dl/$d ] && ln -s MAIN/dl/$d dl/$d; done`, `cp -R MAIN/vendor .`, `make`, `PATH=/opt/
   devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make testapp`, `python3 -m venv .venv &&
   .venv/bin/pip install -e .`. Then check phase-4.md section 6 rows R7-R25 against the merged code: the Python
   names (`python3 -I -c "import libazahar, inspect; ..."` from the venv), the env variables (`grep -n "LAZ_"
   python/libazahar/*.py`), `azhost --help`, `azhost layout | head -3`, `ls docs/research/`, `ls
   docs/status/lazpy/5-done/`. Checkpoint: a table of rows that differ (row, what the code says), saved to
   `runs/h/rows.md`.
1. **H1 (about 0.35 h).** Write section 3's files in the order 3.5 (examples first: they pin the API names), 3.6,
   3.1, 3.2, 3.3, 3.4. Run `examples/quickstart.py` once with STOCK, `pool_shots.py` once, `memory_watch.py` with
   OURS and with STOCK (gate 4), all `nice -n 10`, one at a time except the pool, folders under `runs/` (ignored). Run
   gate 1. Checkpoint: gate 1 and gate 4 output quoted; **the exact list of paths for the main loop to `git add`**.
   **End the run with the report "H1 done"** (section 9).
2. **H2 (about 0.1 h; after the main loop's resume message "H1 committed at <sha>").** Gates 2 and 3: the fresh
   clone, the steps block, pytest. Run it as `runs/h-clone/run.sh` started with `sh -c 'trap "echo \$? >
   runs/h-clone.rc" EXIT; nice -n 10 sh runs/h-clone/run.sh > runs/h-clone/steps.log 2>&1'` and
   `run_in_background`; wait with Monitor until `runs/h-clone.rc` exists (bounded 30 min). Without Monitor, run it in
   the foreground in parts under the 10-minute limit and say so. If the clone fails because a file was not committed,
   report the path (the main loop adds it and resumes you); if it fails because a README step is wrong, fix the README
   (and `examples/quickstart.py` if needed), say so, and the main loop commits and resumes you for a second clone.
   Checkpoint: gate 2 and 3 quoted; the bytes downloaded (`du -sh runs/h-clone/repo/dl`); the wall time.
3. The report ends the run. Stop every waiter and background task you started (TaskStop) first.

## 6. Machine-sharing rules

- At most one emulator at a time, except `pool_shots.py` (3, through the slot cap); everything nice'd; nothing timed.
  No window, PNGs read with the Read tool if you look at them. Never kill a process you did not start. Never write in
  MAIN.
- The only network use is the clone's own `fetch.sh` and `pip install` in H2 (and H0's `pip install` in your
  worktree). No `git push`, no `gh`.
- No `sleep` polling; one Monitor wait per long run, stopped before hand-back.

## 7. Writing rules

Plain, short sentences; no marketing words ("blazing", "seamless", "powerful"); say what a thing does, then how to
use it. Every claim is either gated (an item in `5-done/`) or written as "not yet" or "not tested". Numbers only
from section 2's sources, with load and date. Nominative names only. No screenshots in v0.1.0 (phase-4.md section
11). Keep the README under about 160 lines: detail goes to USING.

## 8. Interfaces assumed

phase-4.md section 6: R7-R9, R11-R22, R24, R25 (R1 for the key-blob sentence). If a merged name, flag or env variable
differs, follow the code and list the difference in the report.

## 9. The builder's report (H1 and H2)

H1: gate 1 and gate 4 as printed (with `--plant-red`'s lines); `runs/h/rows.md`'s differences; the paths to add;
line counts per file; every number in the README with its source line; anything in the code that the docs had to
call "not yet" (with its item); proposed code fixes. H2: gates 2 and 3 as printed, the bytes and wall time, any
README change made after H1. Both: lines for `docs/map/code.md` (`examples/`), `docs/map/tools.md`
(`tools/docs_check.py`), `docs/map/runners.md`:
```
python3 -I tools/docs_check.py                    # README numbers, the example block, links, claims (step H's gate)
.venv/bin/python examples/quickstart.py           # prints "quickstart ok"
```
and a final **"Lessons and notes"** block, ready to paste into item 410.

## 10. Hours (agent wall time)

Builder 0.5 h (H0 0.05, H1 0.35, H2 0.1), the opus as-built review 0.15 h, the commits 0.1 h: **0.75 h**, against
PLAN.md's 0.5 (which had no docs checker and no commit-then-clone checkpoint; NOTICES moved to I). The clone's
downloads and the example runs are machine time.

## 11. What H leaves for I

The README's "Two cores" and "Install" lines that name `fetch.sh --lazpy-core` and `--testapp` (I adds the flags);
the README's licence line for the core binary (I's G4 answer); `docs_check.py`, which the main loop runs without
`--allow-missing` after both merges (I2).

## 12. Review checklist (the opus as-built review)

1. Every number in README is in its source line, with load and date; no speed token anywhere else; spike 1's 50x
   absent; spike 2's rows labelled one game, busy machine.
2. Every "works" bullet maps to a done item whose Evidence proves that exact feature (open the item, not just its
   folder); nothing ungated is called working.
3. The README's steps block, run in a clean clone with a clean environment, is what H2 ran (compare the log's
   commands with the block); no step borrows from MAIN.
4. The example block equals `examples/quickstart.py`; the example checks something real (frames, both PNG sizes, the
   A press in the app's log), not just "no exception".
5. USING's names and env variables match the merged code (spot-check five); HOST-API cites `azhost.h` lines that
   exist; the pasted `azhost` output is current.
6. Legal lines: no ROM/keys/system data; non-affiliation with Nintendo and Azahar; no "clean room"; no key
   instructions; nominative names; the GPLv3 line for the core binary as Guy decided (or flagged).
7. `docs_check.py --plant-red` fails on each plant; the script follows the Python golden rules (functions short,
   `-I`-safe, no network).
8. Nothing committed; no item file, map, PLAN or research file edited; no write in MAIN; no push.
