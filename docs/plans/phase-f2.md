# Step F2: gate our patched core, as rebuilt by step 0 ("P9b"), with the full test batch (item laz-320)

Brief for one sonnet builder, revision 2 (2026-11-13, after review 2; final). Phase index: `docs/plans/phase-3.md`
(order, ownership, merges, departures, interfaces, Phase 2's holds H1-H7). Contract: `docs/PLAN.md:311` ("Phase F2"),
sections 2.4 and 2.7. Where this brief disagrees with PLAN.md on a goal, PLAN.md wins: stop and report (except the
approved departures P1-P8 and refinements R1-R4 of phase-3.md section 5 and phase-2.md section 5, which you follow; R4,
what "exact" means for the debug-text stop, is this step's).

You work in `../libazahar-py-f2` (branch `step-f2`, made at main after Phase 2 merged). "MAIN" is
`/Users/guyshtainer/VSCodeProjects/3ds-toolkit/projects/libazahar-py`. "OURS" is
`MAIN/build-core/azahar_lazpy_libretro.dylib` (absolute path; **read only**), the core the main loop is rebuilding
in step 0 (phase-3.md section 4 step 0: key blob off, patch 0007 no default ClCertA, patch 0008 no key loading, the
three Nintendo headers and `externals/libressl` dropped from the build tree, static OpenSSL 3.6.5 from Homebrew in
place of LibreSSL). You are launched while that build runs; you run **no emulator** until it has ended with 0 and
its `build.inputs` matches your tree (section 7). "STOCK" is `dl/azahar/azahar_libretro.dylib` in your worktree (a
link to MAIN's). **Never commit, never edit item files, never write in MAIN, never run `tools/build-core.sh`** (in a
worktree its build tree is the linked `dl/azahar-src/build-src`, MAIN's: a run would delete it and start a full
build; the build is the main loop's). Read first: the
repo's `CLAUDE.md`, `docs/map/rules.md`, phase-3.md sections 2, 3, 5 and 6, phase-c.md sections 3.4, 3.5, 6, 8,
phase-d.md sections 3, 4 and 8, `core/README.md`, `core/options-lazpy.txt`, `tests/gate_c.py`,
`tests/python/conftest.py`, `~/.claude/python-golden-rules.md` and `~/.claude/c-golden-rules.md`.

## 1. Goal and gate

Prove that the core we will ship (keys off) works with everything Phases 1 and 2 built, applied with its own option
profile, and that it gives the exact repeats the stock core cannot. The gate (headless, this Mac):

1. **f1 the rebuilt core's supply chain** (`gate_f2.py` id `keyblob`, the first check; all of it in
   `keyblob_findings`, section 6, so Phase 4's `release_check` imports one implementation):
   - `MAIN/build-core/build.exit` holds `0`; OURS's mtime is later than `MAIN/build-core/build/CMakeCache.txt`'s;
   - `MAIN/build-core/build.inputs` exists (the 21:09 build has none, which is what tells the new build from the old
     one); its `tarball=` equals `core/PIN`'s `SRC_SHA256`; its `pin=`, `script=` and every `patch <name>=` equal the
     sha256 of your tree's `core/PIN`, `tools/build-core.sh` and `core/patches/*.patch` (the same names, no more, no
     fewer; 0007 and 0008 among them); `drop=` equals `core/PIN`'s `LAZ_CORE_DROP`; `clean=yes`;
     `openssl_version=` equals `core/PIN`'s `OPENSSL_VERSION`; both `openssl_*_sha256=` lines present. RECORD `head=`,
     `openssl_prefix=`, and whether the two `.a` files at that prefix still have the recorded sha256;
   - the cache has the exact lines `ENABLE_BUILTIN_KEYBLOB:BOOL=OFF`, `USE_SYSTEM_OPENSSL:BOOL=ON`,
     `OPENSSL_SSL_LIBRARY:FILEPATH=<openssl_prefix>/lib/libssl.a`, `OPENSSL_CRYPTO_LIBRARY:FILEPATH=<openssl_prefix>/
     lib/libcrypto.a` (match the type field as `:[A-Z]*=`, since a `-D` without a type may stay `UNINITIALIZED`);
   - every `LAZ_CORE_DROP` entry (read from `core/PIN`, never typed) is absent from the **build tree**
     `MAIN/dl/azahar-src/build-src/<SRC_TOP>/` (not `unpacked/`, the reading copy, which keeps them);
   - a walk of `MAIN/build-core/build/` finds at least 1,000 `*.o.d` files and **none** names the basename of any drop
     entry (`default_keys.h`, `ctr-common-1-cert.h`, `ctr-common-1-key.h`, `libressl`);
   - OURS holds none of 8 evenly spaced 16-byte windows of each of `default_keys_enc` (`src/core/hw/default_keys.h`),
     `ctr_common_1_cert_bin` and `ctr_common_1_key_bin` (`src/core/hle/service/http/ctr-common-1-*.h`), the `0x..`
     tokens parsed from the **reading copy's** headers (FAIL if a header is missing there or parses to under 128
     bytes: then nothing was checked);
   - `strings -a OURS`: a line equal to `-lazpy.1`; **no** line holding `/Users/` (review 2 N4); no line holding
     `ClCertA file missing, using default` (N5, the text 0007 removes); no line holding `libressl`, any case (the
     21:09 build has `externals/libressl/...` paths); at least one line equal to the pinned version (`3.6.5`) or
     holding `OpenSSL 3.6.5` (the providers' version string; the 21:09 build has none);
   - `/usr/bin/otool -L OURS` names no `libssl` or `libcrypto`;
   - `MAIN/build-core/build/src/citra_libretro/CMakeFiles/citra_libretro.dir/link.txt` names
     `<openssl_prefix>/lib/libssl.a` and `<openssl_prefix>/lib/libcrypto.a` and holds no `libressl`, any case.
   RECORD: OURS's size; every `strings` line holding `OpenSSL` or `openssl@3` (count and the first 5); the link
   line's `-framework` and `-l` items and `otool -L`'s list (so a library the static OpenSSL needed shows); the count
   of `built for newer macOS` lines in `MAIN/build-core/build.log`.
2. **f2** `/usr/bin/nm -gU OURS` lists exactly the 25 `_retro_*` names of SRC `citra_libretro/libretro.osx.def` plus
   `_lazpy_read_memory`, `_lazpy_write_memory`, `_lazpy_movie_play` (28, nothing else); STOCK lists exactly the 25.
3. **f3** a run on OURS writes `2126.2-lazpy.1` as the core version in host.log (`core <name> version <v>`), and the
   `option <key>=<value>` lines logged at boot hold the six keys of `core/options-lazpy.txt` with its values (P8).
4. **f4** on OURS: `make test-host` passes; `python3 -I tests/gate_c.py --core OURS` prints PASS for C(a)-(f) with
   the our-core expectations of section 5; `LAZ_CORE=OURS LAZ_REQUIRE_EMULATOR=1 python3 -m pytest -q -rs
   tests/python` passes with 0 skipped (its header line says `kind=lazpy`); **no host.log** written by these two
   parts holds C's exit-path line, grepped right after each part (section 7 step 2).
5. **f5** C(e)'s repeat (section 6, r1): two runs on OURS in fresh folders give identical shot sha256s, a
   byte-identical SD `log.txt` (`s=` and `t=` included) and identical summary lines with the `wall=`, `fps=` and
   `wall_ms_mean=` fields removed.
6. **f6** D's state boot repeat (section 6, r2): two full chains on OURS give identical shot sha256s and log lines
   after the state for the two restored instances; each chain's `t_state` is under 2.5 s (Guy's bound, hold H5).
7. **f7** the debug-text stop (section 6, dbg; refinement R4): `stop=debug_text`; the batch's last frame is within {0,
   1} of the `ready` line's host frame and **equal across two runs**; the SD log at the stop ends at the `ready f=200`
   line or the one per-frame line after it.
8. **f8** recorded, not gated: a stock-made state loaded into OURS and an OURS state loaded into STOCK (ok, or the
   error class and text); r1 on STOCK twice (which fields differ); the state bytes of the two r2 chains after the
   256-byte header; `drain_ms` and `t_state` of each r2 chain.
9. **f9** the stock smoke (review 1, Q4) after your edits: `python3 -I tests/gate_c.py --core STOCK --only c,f`
   passes, and `LAZ_CORE=STOCK LAZ_REQUIRE_EMULATOR=1 python3 -m pytest -q -rs tests/python -k "c4 or guest_exit or
   lazpy"` passes with 0 skipped (the stock c4 test, D's guest-exit test, your profile tests and your our-core c4
   twin, which takes `lazpy_core` whatever `LAZ_CORE` says). The phase-end suite runs everything on stock later.

## 2. Facts (checked; SRC = `MAIN/dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/`, PATCHES = `core/patches/`)

- The key blob: `option(ENABLE_BUILTIN_KEYBLOB ... ON)` (SRC `CMakeLists.txt:154`) adds `src/core/hw/default_keys.h`
  to `citra_core` when on (`src/core/CMakeLists.txt:501-503`; `key.cpp:21-23` includes it only under the option).
  The P9 build (21:09, e40e59c) is OFF with no `.o.d` naming the header, but it still holds Nintendo's ClCertA and
  links LibreSSL; step 0's build replaces it.
- Step 0 (phase-3.md section 4 step 0, the main loop's): patch 0007 removes `http_c.cpp:37-38`'s two includes of
  `ctr-common-1-cert.h`/`-key.h` and the fallback copy at `:2281-2289` (now `LOG_ERROR(..., "ClCertA file missing");
  return;`); patch 0008 makes `GetKeysStream()` (`key.cpp:292-314`, the one key source of AES, RSA `rsa.cpp:101` and
  ECC `ecc.cpp:65`) return an empty stream; `core/PIN`'s `LAZ_CORE_DROP` lists the three headers and
  `externals/libressl`, deleted after unpack and before the patches; the configure has `USE_SYSTEM_OPENSSL=ON` with
  the explicit static `libssl.a`/`libcrypto.a` of the pinned keg; `--build` writes `build-core/build.inputs` (one
  `key=value` per line: `tarball`, `pin`, `script`, `patch <name>` per patch, `drop`, `openssl_version`,
  `openssl_prefix`, `openssl_libssl_sha256`, `openssl_libcrypto_sha256`, `head`, `clean`, `cmake`) before compiling.
  The script dies on each of its own guards, so a 0 in `build.exit` already implies most of f1; `gate_f2.py` checks
  them again from the files, independently.
- With no keys, `DecryptClCertA()` (run from the HTTP service's constructor, `http_c.cpp:2507`) returns at the
  missing key slot 0x0D (`:2262-2266`) before the removed branch, so neither 0007 nor 0008 changes anything the
  test app can see: your whole batch on OURS is the "homebrew needs no keys and no ClCertA" proof.
- OpenSSL here: `/opt/homebrew/opt/openssl@3` -> `Cellar/openssl@3/3.6.5`; its objects say `minos 15.0` (our target
  is 11.0, so `ld` may warn: record, do not fix); the full text `OpenSSL 3.6.5 29 Sep 2026` lives only in
  `cversion.o`, which the link pulls only if something calls `OpenSSL_version`, while the bare `3.6.5` sits in the
  providers the core does use (hence f1's either-or).
- macOS exports only what `libretro.osx.def` lists (SRC citra_libretro/CMakeLists.txt:96); the file has 25 symbols
  after two comment lines. Patch 0001 appends `_lazpy_read_memory`, `_lazpy_write_memory`; 0006 `_lazpy_movie_play`.
- Patch 0005 makes the version `g_build_fullname + "-lazpy.1"` at run time, so the dylib holds `-lazpy.1` as its own
  string and the logged version is `2126.2-lazpy.1`; A's `azh_version_ok` accepts it (`host/pins.h`).
- Our core's six options exist only when it registers them (patch 0002, **with stock defaults**); A's
  `azh_set_option` refuses an unregistered key with `AZH_E_ARG`, so **the lazpy lines must not be sent to the stock
  core**. No Phase 1 or 2 code applies `core/options-lazpy.txt` (P8): you add that. host.log logs one `option
  <key>=<value>` line per registered key at boot (`host/options.c:164`).
- `azh_stats` is already valid after `azh_open` (hold H6), so azhost and the worker can learn `is_lazpy_core`
  before they set options. Change nothing in `host/api.c`.
- D's Emulator already closes itself after a returned `guest_exited` (hold H7, `emulator.py` `run`).
- What makes repeats exact on our core, and what breaks them on stock: async HLE work on `std::async` unless
  `deterministic_async_operations` (SRC settings.h:490-491; hle_ipc.h:306, 348); a random tick base unless
  `init_ticks_type=Fixed` (core_timing.cpp:37-44), so `s=` differs on stock; the host clock unless
  `init_clock=FixedTime` (shared_page.cpp:34-63), so `t=` differs on stock; the log on its own thread unless
  `instant_debug_log` (backend.cpp:353-357, which also flushes per entry), why a debug-text stop is refused on stock.
- On our core status 16 does not `_exit`: patch 0003 makes `retro_run` return after `DisplayMessage`, C flags
  `AZH_ACT_EXITED` and the batch returns `stop=guest_exited`; azhost exits 10 after printing the summary. A crash is
  `guest_error` with no count; the Emulator stays open after a `GuestError` on our core.
- A state's 256-byte `CSTHeader` holds the program id, the revision, the wall-clock time of the save and the build
  name (SRC core/savestate.cpp:24-36, 262); the body after it is zstd (`:303-304`). A state is refused when its
  revision is not `g_scm_rev` (`:291-301`); both cores take `GIT_REV` from the same `GIT-COMMIT`, so they may accept
  each other's states; D's meta only warns on a different `core_version`. f8 records what happens.
- C's exit-path line is one fixed `write(2)` in `host/env.c:40-56`; take its exact text from there.
- The summary line is `frames= wall= fps= shots= stop= first= last= vblanks= wall_ms_mean= batch= msg=` (hold H4).
- `tests/gate_c.py` has `run_azhost(ident, flags, control, timeout)` writing under the module global `RUNS`
  (`runs/c-gate/<ident>/`), killing its own child on a timeout or any `BaseException`, returning rc, parsed
  summaries (`checks_c.parse_summary`) and `last` lines; reuse it (section 6).
- D's fixtures (hold H1): `host_paths` follows `LAZ_CORE`; `lazpy_core` and `stock_core` name a core whatever
  `LAZ_CORE` says; the session header prints `core=<path> kind=<kind>`. D's `test_c4_debug_text_needs_our_core`
  passes `core=stock_core`.

## 3. The code changes (F2-1)

### 3.1 `azhost` applies our core's profile (`host/azhost_main.c`)

New flag `--lazpy-profile FILE|none`, default `core/options-lazpy.txt` (relative to the current directory, like A's
`--profile` default). After `azh_open`: `azh_stats`; if `is_lazpy_core`, apply the file's lines with A's profile
reader and `azh_set_option` **first**, then A's `--profile` lines, then each `--opt` (later wins, A's rule). `none`
skips it. On the stock core the lazpy file is not read. A missing or bad lazpy file on our core is handled exactly
as A handles a missing or bad `--profile` (same message shape, same exit code). Add the flag to `--help`.

### 3.2 The Python side

- `_paths.py`: `lazpy_profile() -> Path | None`: `LAZ_LAZPY_PROFILE` (the text `none` gives None), else
  `<root>/core/options-lazpy.txt`, resolved; a missing default file gives None with no error (a pip user without the
  repo's `core/`), a missing file named by the variable gives `HostError`.
- `_worker.py`: the `start` request gains `lazpy_options` (an ordered list of pairs, maybe empty). After `azh_open`:
  `azh_stats`; then apply `option_plan(is_lazpy, lazpy_options, options)` in order, then `azh_boot`. `option_plan`
  is a small pure function (lazpy pairs first only when `is_lazpy`, then the others) so it is unit-tested.
- `emulator.py`: read the lazpy file with D's `_read_profile` and send its pairs. In `run`, the close after a
  returned `guest_exited` (H7's line) waits at most 5 s for the graceful close (`self._client.close(min(self.timeout,
  5.0))`), then D's SIGKILL of its own worker, so a stalled `retro_unload_game` does not cost 30 s. Nothing else in
  the Emulator changes.

### 3.3 Core-kind switches in the tests (no expectation loosened)

- `tests/gate_c.py`: `--core PATH` (passed to `azhost --core` through a module-level flag list that `run_azhost`
  appends; default as before) and `--core-kind auto|stock|lazpy` (auto: `/usr/bin/nm -gU <core>` lists
  `_lazpy_read_memory`). The first printed line is `core=<path> kind=<kind>` (D's header shape). Our-core
  expectations in section 5; the stock expectations are unchanged.
- `tests/python/test_c_checks.py`: add `test_c4_debug_text_on_our_core(host_paths, lazpy_core, workdir, seed)`: on
  `core=lazpy_core`, `run(600, debug_text="ready f=")` with `ready_at=200` gives `stopped_by == "debug_text"` and
  `last_frame < 600`. Do not touch the stock c4 test.
- D's other live tests run on whichever core `LAZ_CORE` names. Run them on OURS first; edit
  `test_live_errors.py`, `test_state.py` or `test_api.py` **only** where a check fails for a core reason (an
  expectation that differs by design, section 5), branching on `"lazpy" in host_paths.core.name` with an our-core
  assertion at least as strict as the stock one. Do not edit `conftest.py` (D's; a missing fixture is reported).
- New `tests/python/test_lazpy_profile.py` (no emulator): `option_plan` order and the stock skip; `lazpy_profile()`
  with the variable set, `none`, unset with and without the file; **no key of `core/options-lazpy.txt` appears in
  `host/options-default.txt`** (so the order between the two files can never matter).

## 4. Files (you create or edit only these)

| Path | Role |
|---|---|
| `host/azhost_main.c` | 3.1 only |
| `python/libazahar/_paths.py`, `_worker.py`, `emulator.py` | 3.2 only |
| `tests/gate_c.py`, `tests/python/test_c_checks.py` | 3.3 only |
| `tests/python/test_live_errors.py`, `test_state.py`, `test_api.py` | 3.3, only where a run proves an our-core branch is needed |
| `tests/python/test_lazpy_profile.py`, `tests/gate_f2.py` | new |

Run artefacts go under `runs/f2/` (ignored), including the slot helper of section 9. Everything else is outside your
files (phase-3.md section 3): in particular `host/api.c`, `host/run.c`, `host/png.c`, `core/` (no patch changes in
this step), `tools/build-core.sh`, `python/libazahar/_client.py` and `__init__.py` (step E edits them in parallel),
`tests/python/conftest.py`, every header, `testapp/`, `tests/testapp_log.py`, `tests/checks_c.py` (import only). If
a check fails because of another Phase 2 file, stop and report with the failing output; edit it only if the main
loop names the file in a message.

## 5. Our-core expectations in C's and D's tests

| Check | Stock (unchanged) | Ours |
|---|---|---|
| C(c) c4 `--debug-stop "ready f="` | exit 7, stderr `NeedsLazpyCore:` | exit 0, `stop=debug_text`, batch 1's `last` below 600 |
| C(e) break | `stop=guest_break`, runs on | the same |
| C(f) exit | f1 exit 10; f2 map stop code 4, `exit_code` 10, message `(16)`; f3; f4 | f1 exit 10 **after** a summary line with `stop=guest_exited` and `msg` holding `(16)`; f2 no exit-path line in host.log, and the map's stop code and `exit_code` as the code writes them on this path (read `azhost_main.c`; report the values); f3 with the summary's `last` in place of the map's `frame_total` if the map does not carry it; f4 the same |
| D's debug-text test | `test_c4_debug_text_needs_our_core` (stock, explicit): `NeedsLazpyCore` | your twin `test_c4_debug_text_on_our_core` (explicit `lazpy_core`): `stopped_by == "debug_text"` |
| D's guest-exit test (`test_f_guest_exit`) | `RunResult(stopped_by="guest_exited")` from the death mapping, Emulator closed | the same `RunResult` from the reply, Emulator closed (H7) |
| D's state boot (`test_state_boot`; D's as-built S2 put the bound inside it) | `t_state < 2.5 s` (H5) | the same bound |
| Everything else | as written | identical expectations |

## 6. `tests/gate_f2.py` (new; stdlib plus `tests/` modules)

`python3 -I tests/gate_f2.py --ours OURS --stock STOCK [--only keyblob,symbols,version,dbg,r1,r2,cross,stock_r1]`.
It inserts the absolute `tests/` and `python/` paths into `sys.path` first (phase-2.md B12). Every scenario runs in
a fresh `runs/f2/<id>/`: import `gate_c`, set `gate_c.RUNS = <repo>/runs/f2` and reuse `gate_c.run_azhost` (pass
`--core <core>` in its flags) and `checks_c.parse_summary` rather than a second runner (review 1 N12). Lines printed:
`PASS <id> ...`, `FAIL <id> ...`, `RECORD <id> ...`; the summary goes to `runs/f2/summary.txt`; exit 0 only if no
FAIL **and `gate_c.failed` is 0** (`gate_c.run_azhost` reports a timeout through `gate_c.report`, which bumps
`gate_c.failed`, not your counter; review 2 N3). `keyblob` and `symbols` run no emulator.

- **keyblob** (f1): file reads plus one `strings -a`, one `otool -L` and `shasum`-equivalent `hashlib` reads, as
  section 1 f1 lists them. Write it as one function
  `keyblob_findings(build_dir: Path, core: Path, src_root: Path, tree: Path, repo: Path) -> list[str]` (empty means
  pass; each string one finding naming the check) plus a small `keyblob_records(...) -> list[str]` for the RECORD
  lines, both importable without side effects (Phase 4's `release_check.py` imports them): `build_dir` =
  `MAIN/build-core`, `core` = OURS, `src_root` = the reading copy `MAIN/dl/azahar-src/unpacked/<SRC_TOP>`, `tree` =
  the build tree `MAIN/dl/azahar-src/build-src/<SRC_TOP>`, `repo` = the checkout whose `core/PIN`, `core/patches/`
  and `tools/build-core.sh` are hashed (your worktree; `LAZ_CORE_DROP`, `OPENSSL_VERSION` and `SRC_SHA256` come from
  its `core/PIN`, read like the script: `KEY=value` lines, never executed). `--build-dir`, `--src-root`, `--tree`
  default to those MAIN paths. The windows: parse every `0x..` token of the array's initializer, take 8 windows of
  16 bytes at offsets `k * (n - 16) // 7`, k = 0..7, and search OURS's bytes for each.
- **symbols**: f2. The 25 names are read from SRC's `libretro.osx.def` (lines starting with `_`), not typed in. Print
  any extra or missing name.
- **version**: a 30-frame run on OURS; f3, the six key=value pairs found among the `option ` lines.
- **dbg** (f7), twice (`.1`, `.2`): seed `ready_at=200`; `--frames 600,1,1,1,1,1,1,1,1 --debug-stop "ready f="
  --print-last-line testapp/log.txt`. d1 batch 1 `stop=debug_text`; c_min from batches 2-9 with
  `checks_c.boot_offsets`; d2 batch 1's `last 1:` line is `ready f=200 ...` or the per-frame line `f=201 ...`; d3
  `last - (ready.v + c_min)` is 0 or 1 (printed); d4 run 2's batch-1 `last` and `last 1:` line equal run 1's. Also
  one `--stop-every 1` SD-stop run of the same seed: print its `last` beside the debug stop's (a RECORD line).
- **r1** (f5), twice on OURS: seed `break_at=300`; an inputs file written by the gate (A held frames 120-129, B
  140-149, touch (160, 120) down 150-159, circle (32767, 0) 170-179, all before the break); `--frames 600,120
  --inputs r1.txt --shot 100,250 --print-last-line testapp/log.txt`. Batch 1 must stop `guest_break` (as C(e)).
  Compare the two runs: the four PNGs' sha256, `log.txt` bytes, the summary lines with the `wall=`, `fps=` and
  `wall_ms_mean=` fields removed. Any difference is a FAIL naming the first differing line and field.
- **stock_r1** (f8): r1 twice on STOCK; RECORD which fields differ (expected: `s=` and `t=`) and whether the shots
  match.
- **r2** (f6), two chains on OURS, in Python through `libazahar` (core passed as `core=OURS`):
  1. `a = Emulator(app, runs/f2/r2-<c>/a, sd_seed=seed(boot_frames=1200))` (in a script, `seed(**keys)` is
     `testapp_log.write_control(folder, **keys)` on a fresh folder, `tests/testapp_log.py:11`, as D's fixture does);
     `a.run(1300)`; the log has the `booted` line; `S = a.save_state(runs/f2/r2-<c>/s.state)`; note the SD `log.txt`
     length at the save; `a.run(300, shots=[100, 300])`; keep a's log lines after the noted length and its shot sha256s;
     `a.close()`.
  2. First copy a's `sys/` minus the SD card into b, as D's `test_state_boot` does (`tests/python/test_state.py:48-51`;
     the shader cache and NAND come along, hold H5): `shutil.copytree(a_dir / "sys", b_dir / "sys",
     ignore=shutil.ignore_patterns("sdmc"))`; RECORD the copied top folders under `sys/Azahar/`. Then `t0 =
     time.monotonic(); b = Emulator(app, runs/f2/r2-<c>/b, state=s.state); t_state = time.monotonic() - t0`
     (D's definition, hold H5); `b.run(300, shots=[100, 300])`; b's log lines after the snapshot's length and its
     shot sha256s; the `state load ...` line from b's host.log (it holds `drain_ms`); `b.close()`.
  Gate: b of chain 1 equals b of chain 2 (lines and shot hashes); `t_state < 2.5` per chain. RECORD: a1 == a2; a_c ==
  b_c within a chain; the two `s.state` files equal after byte 256 (and their first 256 bytes, expected to differ
  only in the time field); `drain_ms`, `t_state`.
- **cross** (f8): `x = Emulator(app, ..., core=STOCK)`, `run(300)`, `save_state(stock.state)`, close; then
  `Emulator(app, ..., core=OURS, state=stock.state)` and `run(60)`: RECORD ok (and whether the log's `f` continues
  from the save) or the error class and text. The reverse with r2's chain-1 `s.state` into STOCK.

## 7. Steps, with a checkpoint after each (save files as you go; never commit)

0. **F2-0 (about 0.05 h; no emulator).** You are launched together with step E, right after the main loop started
   step 0's build (`MAIN/build-core/build.exit` is absent while it runs). Seed the worktree: `mkdir -p dl && for d
   in azahar moltenvk libretro-headers vulkan-headers azahar-src; do [ -e MAIN/dl/$d ] && ln -s MAIN/dl/$d dl/$d;
   done` (link the children, never `dl/` itself), `cp -R MAIN/vendor .`, **`mkdir -p build-core && ln -sf
   MAIN/build-core/azahar_lazpy_libretro.dylib build-core/azahar_lazpy_libretro.dylib`** (D's `lazpy_core` falls back
   to the checkout's `build-core/`; the link is your worktree's, ignored, and resolves to the new dylib once the
   build installs it; MAIN's `build-core/` stays read-only; review 2 B2), `make`,
   `PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make testapp` (or copy
   `MAIN/build/testapp.3dsx`). Checkpoint: `make test-host` and `python3 -m pytest -q tests/python -m "not slow"`
   pass (baseline counts printed; after D's fixes about 49 passed).
1. **F2-1 (about 0.23 h; no emulator).** Sections 3 and 6, all of `gate_f2.py` written (keyblob and symbols first),
   none of it run on OURS yet. Checkpoint: `make check && make && make test-host` clean; `python3 -m pytest -q
   tests/python -m "not slow"` passes with `test_lazpy_profile.py`; `python3 -I tests/gate_f2.py --help` works.
   **Then wait for the build** (rule T): Monitor until `MAIN/build-core/build.exit` exists (an until-loop, bounded
   **150 min**). On a timeout, stop the waiter and end your run with a "waiting for the build" report (F2-0 and F2-1
   results in it); the main loop resumes you. If `build.exit` is not `0`, stop and report the last 30 lines of
   `MAIN/build-core/build.log`; the build is the main loop's. On `0`: run `python3 -I tests/gate_f2.py --only
   keyblob,symbols,version` (one 30-frame emulator run, through the slot helper; it replaces revision 1's by-hand
   check). Checkpoint: f1, f2, f3. **If f1 fails, stop and report "the gated build is not the build that may ship"
   with every finding**: nothing else in this step is valid on that binary.
2. **F2-2 (about 0.2 h of agent time; about 45-65 min of machine time).** One background batch, every emulator
   command through the slot helper, one instance at a time, as `runs/f2/batch.sh` with one rc file per part
   (`runs/f2/<part>.rc`), in this order:
   1. `gate_c.py --core OURS`; then at once `grep -rlF "<the env.c line>" runs/c-gate --include host.log >
      runs/f2/exitpath-ours.txt` (B3: before any stock part can write there);
   2. `LAZ_CORE=OURS LAZ_REQUIRE_EMULATOR=1 python3 -m pytest -q -rs tests/python`; then at once the same grep over
      `runs/d-pytest`, appended to `runs/f2/exitpath-ours.txt` (the stock c4 test there is refused before any
      frame, so it cannot write the line either);
   3. `gate_f2.py` (all ids; its our-core host.logs are grepped by the gate itself into the same file);
   4. the stock smoke (f9).
   Start it as `sh -c 'trap "echo \$? > runs/f2-batch.rc" EXIT; nice -n 10 sh runs/f2/batch.sh > runs/f2-batch.log
   2>&1'` with `run_in_background`; wait with Monitor until `runs/f2-batch.rc` exists (bounded 120 min). f4's grep
   passes when `runs/f2/exitpath-ours.txt` is empty. Without Monitor: run each part as its own foreground call,
   each split under the 10-minute limit (`gate_c.py --only`, pytest per file, `gate_f2.py --only`), grep after each
   our-core part, and say so. Checkpoint: f1-f9; quote every PASS/FAIL/RECORD line.
3. The report (section 10) ends the run. Stop every waiter and background task you started (TaskStop) first. If the
   opus review asks for fixes, the main loop resumes you; any emulator rerun then is a timed part (phase-3.md rule
   T): the resume message says when the machine is free.

## 8. When a repeat is not identical

Do not tune and do not add options. Record the first differing log line (both versions), which fields differ, the
first differing shot frame, and whether the a1 == a2 RECORD differs at the same place. Then report; the main loop
takes it to review (a new core patch is a change of scope for Phase 3). The rest of the batch still runs. If a
difference looks key-related (a file or service that needs console keys), say so: the main loop takes it to Guy,
and the key blob stays off.

## 9. Machine-sharing rules

- One emulator instance at a time, always nice'd, folders under `runs/f2*`, `runs/c-gate/`, `runs/d-pytest/`
  (ignored). Step E's builder runs no emulator while your batch runs (the main loop holds it at its E1 checkpoint);
  no emulator of yours runs beside the core build (section 7 step 1's wait). Never run `tools/build-core.sh`.
- **The slot cap** (phase-3.md section 2): step E's `_slots.py` is not in your tree, so every emulator command runs
  under `runs/f2/hold_slot.py` (about 20 lines, ignored, not committed): it opens `LAZ_SLOT_DIR` or
  `~/Library/Caches/libazahar-py/slots/` (mkdir 0700), tries `slot-0.lock` .. `slot-<LAZ_MAX_INSTANCES or 3,
  minus 1>.lock` (0600) with `fcntl.flock(LOCK_EX | LOCK_NB)` each 0.1 s up to 1 h, prints the slot and the wait to
  stderr, `os.set_inheritable(fd, True)`, then `os.execvp` the command (the lock lives on in the command's process
  and dies with it). Run it with `python3 -I`.
- Never open a window: no Azahar app, no `open`, no Preview; PNGs with the Read tool.
- Never kill a process you did not start; timeouts kill only your own child. Never write in MAIN's `build-core/`.
- No `sleep` polling; one Monitor wait per long run, stopped before hand-back.

## 10. The builder's report

F2-0's result; the build wait (start, end, `build.exit`); f1-f9 as printed (with f1's RECORD lines: size, `head=`,
the OpenSSL prefix and whether its `.a` files still match, the `OpenSSL` strings, the link line's `-framework`/`-l`
items, `otool -L`, the `built for newer macOS` count); every changed assertion in C's and
D's tests (old and new, with the reason); the `option_plan` and the azhost order as built; the r1 and r2
comparisons and every RECORD line (stock's differing fields, the state bytes after byte 256, `drain_ms` and
`t_state`, cross-core results); the dbg frames of both runs; the slot waits; C(f)'s map values on our core; line
counts per edited file and the longest function; the runners block for `docs/map/runners.md`:
```
build/azhost run <app> ... --core build-core/azahar_lazpy_libretro.dylib [--lazpy-profile core/options-lazpy.txt|none]
python3 -I tests/gate_c.py --core <core> [--core-kind auto|stock|lazpy]
python3 -I tests/gate_f2.py --ours <our core> --stock <stock core> [--only ...]   # step F2's gate (keyblob first)
```
lines for `.gitignore` (none expected); one line for USING.md (Phase 4): "on our core `core/options-lazpy.txt` is
applied first; `LAZ_LAZPY_PROFILE=none` turns it off; `instant_debug_log` flushes the log per guest line"; and a
final **"Lessons and notes"** block, ready to paste into item 320 (with the drain numbers for D 3.3's note: whether
a drain-only export is worth a Phase 4 item, which it is only if `drain_ms` is over half of `t_state`).

## 11. Hours (agent wall time)

Builder 0.48 h (F2-0 0.05, F2-1 0.23, F2-2 0.2), the opus as-built review 0.2 h, the commit 0.1 h: **0.78 h**,
against PLAN.md's 0.75 (P8's profile application and f1's supply-chain checks, offset by Phase 2's holds, the reused
runner, the stock smoke and the by-hand check folded into `--only keyblob,symbols,version`). The build wait and the
batch are machine time; the rebuild is the main loop's.

## 12. Review checklist (the opus as-built review)

0. Step 0's diff on main (the main loop's commit): patches 0007 and 0008 (each with its notice line; 0007 removes
   both includes and the whole fallback copy, the `else` branch intact; 0008 returns an empty stream), the
   `core/PIN` lines, `tools/build-core.sh` (the OpenSSL pin check before any unpack, the STAMP over patches and drop
   list, the drop's refusals, the configure flags and guards, `build.inputs` before compiling, the `.o.d`, link-line
   and `otool` guards, the atomic install), `core/README.md`'s rows and licence lines; and `build.inputs` itself.
1. `keyblob_findings(build_dir, core, src_root, tree, repo)` checks everything section 1 f1 lists, reads the drop
   list and the pins from `repo/core/PIN` (none typed), parses the windows from the reading copy and fails when a
   header is missing; it ran first and passed; it and `keyblob_records` import without side effects.
2. f2 compares against the `.def` file read from the source, not a typed list; it fails on any extra export.
3. The lazpy profile is applied only when `is_lazpy_core`, first, before the profile and the caller's options, in
   azhost and in the worker alike; `none` and a missing default behave as 3.1 and 3.2 say; the no-shared-key test
   exists.
4. `host/api.c` and `conftest.py` are untouched; the close after a returned `guest_exited` waits at most 5 s.
5. Every changed test assertion is at least as strict on our core as the stock one; no stock expectation changed.
6. r1 compares bytes and hashes (no fuzzy match) with exactly `wall=`, `fps=`, `wall_ms_mean=` removed; r2's gate
   compares the two restored instances across chains and bounds `t_state`; the state comparison skips exactly the
   256-byte header.
7. dbg's d3 and d4 are computed from the printed `last` values; the SD-stop comparison is a RECORD only.
8. The exit-path grep uses the exact text from `env.c` and ran right after each our-core part, before the stock
   smoke; `runs/f2/exitpath-ours.txt` is empty.
9. `gate_f2.py` reuses `gate_c.run_azhost` and exits non-zero when `gate_c.failed` is; every emulator command ran
   under the slot helper, one at a time, nice'd, none before `build.exit` held 0; r2 copied a's `sys/` minus `sdmc`
   into b; nothing written in MAIN; `tools/build-core.sh` never run; no item file touched; nothing committed; no
   file under `core/` changed.

## 13. Interfaces assumed

From phase-3.md section 6: H1, H4-H7, A3-A7, A12, B1-B3, B9, F1-F5, C4-C7, D1-D10, SD. If a merged name, flag or line
differs from those rows (the exit-path text, `--print-last-line`'s format, D's fixtures or the `start` arguments),
follow the code and report the difference.
