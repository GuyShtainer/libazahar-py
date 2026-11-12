# Phase 3, scale and memory: the phase plan (item laz-300)

Opus phase plan, 2026-11-13, **revision 2, the final one** (after review 2, `docs/reviews/phase-3-review-2.md`, which
took revision 1 at 8a16f9e; revision 1 answered review 1, revision 0 is cb3406c). Steps: E (laz-310,
`docs/plans/phase-e.md`), F2 (laz-320, `docs/plans/phase-f2.md`) and G (laz-330, `docs/plans/phase-g.md`). Each brief is
complete on its own for one sonnet builder in its own worktree. This file is the index: order, checkpoints, file
ownership, merge plan, hours, the departures from PLAN.md, the interfaces taken from Phases 1 and 2 (with Phase 2's
holds), the interfaces left for Phase 4, the checked facts, the risks, the hour-saving pass, the changes from review 1
(section 13) and from review 2 (section 14). Review 2 said no third review loop is needed if its fix list is taken as
written; section 14 names the few departures.

Contract: `docs/PLAN.md` (final) sections 2.2, 2.4, 2.5, 2.7, 2.8, 2.9, the grouping paragraph of section 3 and its
**Phase E (PLAN.md:296), Phase F2 (PLAN.md:311) and Phase G (PLAN.md:317)** paragraphs. The step item files 310,
320 and 330 still name PLAN.md lines 289, 304 and 310 (in "The gate" and "Plan section"); the main loop rewrites
them to **:296, :311 and :317** in the commit that moves each item to `1-in-progress/` (section 4 step 1). This plan
refines PLAN.md. Where a brief disagrees with PLAN.md on a goal, PLAN.md wins and the builder stops and reports,
**except for the approved departures** (Phase 2's P1-P6, this plan's P7-P8 and the refinements R1-R4 of section 5),
which the builders follow without stopping.

Inputs. Phase 1: merged at 570eebf (A, B, F1). Phase 2: step C merged on main at 7584a8d (its as-built fixes in; step
C's own branch at ba21233, C1 at 0651a8d); step D on `step-d` at 88cdbe6 (D3 done, 69 passed), its as-built review done
(`docs/reviews/phase-2-d-as-built.md`, S1-S6), its fixes being made now; **D merges on main before step 0 and before any
Phase 3 build**. The P9 rebuild is done (e40e59c; `build-core/` dylib 21:09, 19,145,936 bytes,
`ENABLE_BUILTIN_KEYBLOB:BOOL=OFF`, no `.o.d` naming `default_keys.h`, 0 `/Users/` strings); it is replaced by step 0's
build ("P9b", section 4), which is the binary Phase 3 gates. **Phase 2 delivers the holds H1-H7 of section 6 before its
merge**; the briefs treat them as facts. Every interface this plan takes is a row of section 6. **If the merged code
differs from a row, the builder follows the code and reports the row.**

Hours are agent wall time (PLAN.md's unit). Machine time (emulator batches, the core rebuild, a wait for a slot or
for another step's timed run) is not counted.

## 1. The three steps

| Step | Delivers | Gate (headless, this Mac) | Hours |
|---|---|---|---|
| E, laz-310 | `python/libazahar/_slots.py` (the machine-wide `flock` slot cap, `SlotTimeout`, `LoadWarning`) and `pool.py` (`Pool`); `tools/hold_slot.py` (hold one slot, exec a command); the worker spawned holding its slot; zlib level 1 (`LAZ_PNG_LEVEL`); one timing line per batch in host.log; `tools/speed_table.py`; unit and live tests; `docs/research/speed-table-e.md` with the default cap | `python3 -m pytest -q tests/python -m "not slow"` passes; `LAZ_REQUIRE_EMULATOR=1 python3 -m pytest -q -rs tests/python/test_pool_live.py` passes 0 skipped: 3 instances give correct, separate logs and shots; a 4th waits under cap 3; a SIGKILL frees the slot within 1 s; every worker at nice >= 10; the speed table for 1, 2, 3 and 4 instances of the test app's 3D scene, 60 s each, with the guest-time check, written, and the default cap (1-4) set by the rule fixed in phase-e.md section 7 | 1.11 |
| F2, laz-320 | the gate of **our core as rebuilt by step 0 ("P9b": key blob off, no ClCertA, no key loading, static OpenSSL 3 instead of LibreSSL)**; our core applied with its own profile (`core/options-lazpy.txt`) by `azhost` and by the worker; core-kind switches in C's gate and an our-core twin of D's debug-text test; `tests/gate_f2.py` (the core's supply chain, symbols, version, exact repeats, the exact debug-text stop, cross-core states) | **f1, first** (`keyblob_findings`, phase-f2.md section 6): `build.exit` 0 and `build.inputs` matching the worktree's patches, PIN and script, listing 0007 and 0008, `clean=yes`, OpenSSL as pinned; every `LAZ_CORE_DROP` entry absent from the build tree; no `.o.d` names a dropped file; none of 8 windows of each of the key blob, Nintendo's ClCertA cert and key in the dylib; no `/Users/`, no "ClCertA file missing, using default", no `libressl` string; the pinned OpenSSL version string present; `otool -L` without libssl/libcrypto; the link line names the pinned static libs; `strings` holds `-lazpy.1`; `nm -gU` shows exactly the 25 `_retro_*` plus `_lazpy_read_memory`, `_lazpy_write_memory`, `_lazpy_movie_play`; host.log shows `2126.2-lazpy.1` and the six lazpy options; on our core gate C passes and `LAZ_REQUIRE_EMULATOR=1` pytest passes 0 skipped, stop reasons returned (no exit-path line in any our-core host.log); C(e)'s repeat and D's state boot give identical shot hashes and log lines across two runs; the debug-text stop's frame is exact and equal across runs; stock states into ours (and back) recorded; a stock smoke run still passes | 0.78 |
| G, laz-330 | ABI 3: `azh_read`/`azh_write` through the exports (`host/mem.c`), the per-frame watch list into a watch area of the map (pure planning in `host/watch.c`), `AZH_E_UNMAPPED`; Python `emu.memory` (`read`, `write`, `u8`..`u64`, signed, `write_*`, libmgba-py's `.raw_read`), `run(..., watch=)`, `RunResult.watch`, `GuestMemoryError`; unit and live tests | on our core: both records (global and heap) read back the logged values frame by frame for 600 frames, by `read` calls and by the watch list; a write changes the next logged event line (R1); a straddling read and a fully unmapped read both raise `GuestMemoryError`; on the stock core every memory call and any watch raises `NeedsLazpyCore`; an ABI-2 state loads under ABI 3; `make test-host`, gate C and D's pytest still pass | 0.85 |

Phase total: **2.74 h** of step work plus 0.5 h for the two review loops (both done) = **about 3.25 h**, against
PLAN.md's 1.0 + 0.75 + 0.5 + 0.5 = **2.75 h**. The 0.5 h over is named per step in section 7. Step 0 (P9b: the two
patches, the drop list, the OpenSSL switch, the script edits, the configure check, the commit and the launch,
about 0.2 h) and the checkpoint choreography (commits on branches, two worktree merges, two resumes, about 0.2 h)
are main-loop time, **about 0.4 h**, booked to the main loop.

## 2. Order, checkpoints and the parallel split

```
Phase 2 merged on main (D's fixes in; the holds H1-H7 of section 6 are in its code), its last emulator run ended
Main loop, step 0 "P9b" (section 4): patches 0007 + 0008, LAZ_CORE_DROP + OpenSSL pins in core/PIN, the
  build-core.sh edits, core/README.md; --configure-only check in MAIN; commit on main; tools/build-core.sh
  --detach in MAIN (nice'd; a re-unpack and a citra_core recompile: about 20-40 min quiet, 60-120 loaded);
  NO emulator run meanwhile (rule T)
  |  worktrees made from main after step 0's commit; E and F2 launched together
  E builder (sonnet, ../libazahar-py-e, step-e)       F2 builder (sonnet, ../libazahar-py-f2, step-f2)
  |                                                   |  F2-0: seed, baseline (no emulator)
  |  E1: _slots, pool, hold_slot, client spawn,       |  F2-1: profile application, test switches, gate_f2.py
  |      png level, run.c timing line, speed_table,   |        (all of it written; no emulator)
  |      unit tests; NO emulator                      |  waits (Monitor, 150 min) on MAIN build.exit; then f1
  |                                                   |        first (keyblob, symbols, version)
  |                                                   |  F2-2: the batch on our core, the stock smoke
  |  ENDS ITS RUN: "E1 done"                          |        (timed, one instance)
  |  main loop commits E1 on step-e (sha noted)       |  ENDS ITS RUN: "F2 done"
  |                                                   opus as-built review of F2; fixes (reruns: rule T); commit;
  |                                                   merge step-f2 into main
  |  main loop: git -C ../libazahar-py-e merge --no-edit main; resume E: "E1 committed at <sha>; main (with F2)
  |  merged into your tree at <sha>; go on with E2"
  |  E2: live pool gate, the speed table 1-4          main loop: git worktree add -b step-g ../libazahar-py-g main;
  |      (writes runs/e-speed.rc from a trap)         in it: git merge --no-edit <E1 sha>; launch G (message names
  |  ENDS ITS RUN: "E done"                           ../libazahar-py-e/runs/e-speed.rc and that E2 is running)
  v                                                   G1: ABI 3, mem.c, watch.c, watch area, Python memory; no emulator
  opus as-built review of E; fixes (rule T, and      G2: waits on e-speed.rc (Monitor, bounded 150 min), then
  the held-fix rule of section 4 step 5); commit;         one batch: gate C on OURS, one pytest covering both cores
  merge step-e into main                              ENDS ITS RUN: "G done"
                                                      main loop: git merge --no-edit main in ../libazahar-py-g;
                                                      opus as-built review of G; fixes; commit; merge step-g
  phase-end suite (section 4 step 7)
```

- **A builder never waits for the main loop.** A sub-agent reports only by ending its run, so each checkpoint is the
  end of a run: E after E1 and after E2, F2 at its end, G at its end (or at a "waiting for E2" timeout). The main
  loop commits, then resumes the same agent with SendMessage (its context kept). The main loop writes each
  builder's agent id into the handoff at launch. If a resume fails, the fallback is a fresh sonnet given the brief,
  the earlier report and `git log step-<x>`; the reports list exact paths and measured values to make that possible.
- **How a builder waits on its own long command** (Phase 2 S9): never `sleep`-poll, never "be woken". Long runs
  write an rc file from a `trap ... EXIT`; the builder starts them with `run_in_background` and waits with the
  Monitor tool on "the rc file exists" (an until-loop, bounded); it stops every waiter it started (TaskStop) before
  it hands back. Without Monitor, it runs the work in foreground parts under the 10-minute Bash limit and says so.
- **Rule T: timed parts never overlap** (rules.md 5 and 7; PLAN 2.8). A timed part is anything that runs an emulator or
  the core build: step 0's rebuild, F2's first emulator check and F2-2, E2, G2, **every emulator rerun after an as-built
  review**, and the phase-end suite. Exactly one runs at a time, in the order they become ready. A part that becomes
  ready while another runs waits on that part's rc file (a builder with Monitor; the main loop with a background waiter)
  before it starts; step 0's rc file is `MAIN/build-core/build.exit`. E1, F2-0, F2-1 and G1 run no emulator and may
  overlap anything, the rebuild included. F2 runs its first emulator check (`gate_f2.py --only keyblob,symbols,version`)
  only after `build.exit` holds 0 and `build.inputs` matches its tree. F2-2 runs one emulator at a time; E2 up to 4 (the
  4-instance row); G2 one at a time. Since E2 starts only after step-f2 merged (S2), F2's review reruns always come
  before E2; E's review reruns queue behind G2 if G2 is running.
- **G's wait for E2.** G2 starts only when `../libazahar-py-e/runs/e-speed.rc` exists. G waits with Monitor
  (bounded **150 min**: E2's own bounds are 45 min for the live tests plus 75 min for the table, plus margin). On a
  timeout G **ends its run** with a "waiting for E2" report (G1's results in it) and never starts G2 on its own;
  the main loop resumes it when E2 is over.
- **One slot convention, fixed here** because E builds it while F2 already needs it: the folder is `LAZ_SLOT_DIR`,
  else `~/Library/Caches/libazahar-py/slots/` (mode 0700); the files are `slot-0.lock` .. `slot-<cap-1>.lock` (mode
  0600); a slot is held by `flock(LOCK_EX|LOCK_NB)` on its own open file description; the cap is
  `LAZ_MAX_INSTANCES`, default `_slots.DEFAULT_CAP` (3 until E2's rule sets it, 1-4). Both variables are read on
  every call, never cached at import. The cap is machine-wide only if every user reads the same
  `LAZ_MAX_INSTANCES` (a process with cap 5 takes slots 3 and 4 beside three cap-3 users); `_slots`'s docstring says
  so (N8). F2 has no `_slots.py` in its tree, so it holds one slot around each emulator command with a 20-line
  helper in its ignored `runs/f2/` (phase-f2.md section 9). G and the phase-end suite use E1's committed
  `tools/hold_slot.py` for azhost commands and the Emulator's own slot for Python tests.
- **Why F2 goes first on the machine:** it is on the critical path to G (G needs F2's profile application, and its
  gate needs our core applied right), and E2's our-core rows must run our core as users will (with P8 applied, S2),
  so E2 runs after step-f2 merged and its worktree merged main.
- **Step 0, "P9b", the core that may ship** (section 4 step 0 is the recipe). P9 (key blob off, prefix map) is done
  (e40e59c, the 21:09 build). Three more things must not be in the binary we gate: Nintendo's ClCertA certificate and
  key (`http_c.cpp:37-38`, copied in the fallback at `:2281-2289`; Phase 4 review 1 B1), any key loading at all (Q6,
  main-loop default yes: patch 0008), and LibreSSL, whose OpenSSL/SSLeay licence reads as GPLv3-incompatible (Phase 4
  review 1; Guy, 2026-11-13: "Switch to OpenSSL 3"). Step 0 adds patches 0007 and 0008, deletes the three Nintendo
  headers and `externals/libressl` from the build tree after unpacking (`LAZ_CORE_DROP` in `core/PIN`), configures
  with `USE_SYSTEM_OPENSSL=ON` against the **static** `libssl.a`/`libcrypto.a` of Homebrew's `openssl@3` keg, pinned
  to 3.6.5 in `core/PIN` (the script refuses another version, so a brew upgrade cannot silently change the next
  build), and writes `build-core/build.inputs` (what went in). The STAMP hashes the patches and the drop list, so the
  tree is re-unpacked; the OpenSSL include path changes `citra_core`'s and `network`'s flags, so those recompile
  (machine time; F2 writes its code meanwhile). If `build.exit` is not 0, the main loop reads `build.log`, fixes and
  reruns (`LAZ_CORE_LTO=OFF` if the linker died). A missing system library at the static link (a framework, zlib)
  may be added and is recorded; **if static OpenSSL cannot be linked, the main loop stops and reports to Guy: never
  the OpenSSL dylib, never back to LibreSSL**. E1 goes on meanwhile; E2 then waits for F2-2 as usual.
- **Why G's worktree carries E1:** G edits `python/libazahar/__init__.py`, `host/run.c` and `host/azh_pure.h` after
  E1 has edited them (E1's exports, its timing line, its `azh_png_level` prototype). Merging E1's commit into G's
  worktree at launch (Phase 2's D-at-C1 pattern) means G's edits sit on top of E1's and the final merges are
  conflict-free. **E2 edits none of E1's shared files** (`__init__.py`, `_client.py`, `host/run.c`, `host/png.c`,
  `host/azh_pure.h`); E2's only E1-file edit is the value of `DEFAULT_CAP` in `_slots.py`, which G does not touch.
  A fix found in E2 to a shared file is reported to the main loop, which sequences it (section 4 step 5).

## 3. File ownership (who creates or edits what)

| File | Owner in Phase 3 | What changes |
|---|---|---|
| `core/patches/0007-lazpy-no-default-clcert.patch`, `core/patches/0008-lazpy-no-key-loading.patch` (new), `core/PIN`, `core/README.md`, `tools/build-core.sh` | **the main loop, step 0** (on main, before F2's first emulator check) | section 4 step 0 (the P9 flags and guards are already committed at e40e59c) |
| `python/libazahar/_slots.py`, `pool.py`, `tools/hold_slot.py` | E (new) | phase-e.md section 3; E2 may change only the value of `DEFAULT_CAP` |
| `python/libazahar/_client.py` | E | `WorkerClient(..., slot=None)`: the spawn of the real worker acquires a slot (a fake worker only with `slot=True`), passes its fd in `pass_fds` and as `argv[3]`, closes the parent's copy, writes `<workdir>/slot.txt` |
| `python/libazahar/__init__.py` | E (E1), then G | E1 exports `Pool`, `LoadWarning`, `SlotTimeout`; G exports `Memory`, `WatchRow`, `GuestMemoryError` |
| `host/png.c` | E | `int azh_png_level(void)` from `LAZ_PNG_LEVEL` (0-9, default 1), used by `compress2`; stays pure |
| `host/azh_pure.h` | E (E1: one prototype), then G | E1: `azh_png_level`; G: the watch and memory pure functions |
| `host/run.c` | E (E1: the timing line and the one `png level=` line), then G | G adds the watch rows after each `retro_run` |
| `tools/speed_table.py`, `tests/python/test_slots.py`, `test_pool.py`, `test_pool_live.py`, `docs/research/speed-table-e.md` | E (new) | phase-e.md |
| `host/azhost_main.c` | F2 | `--lazpy-profile` |
| `python/libazahar/_paths.py`, `_worker.py`, `emulator.py` | F2, then G | F2: `lazpy_profile()`, the option plan, a 5 s close wait after a returned guest exit; G: the `read`/`write` ops, `emu.memory`, `run(watch=)` |
| `tests/gate_c.py`, `tests/python/test_c_checks.py` | F2 | `--core`, `--core-kind` and the our-core expectations; an our-core twin of c4 with `lazpy_core` |
| `tests/python/test_live_errors.py`, `test_state.py`, `test_api.py` | F2, only for an our-core branch a run proves needed | each changed assertion listed in the report |
| `tests/gate_f2.py`, `tests/python/test_lazpy_profile.py` | F2 (new) | phase-f2.md |
| `host/azhost.h`, `host/azh_internal.h`, `host/hostmap.c`, `host/core.c` (only the bind call beside A's detection), `host/api.c` | G | ABI 3 (phase-g.md section 3) |
| `host/mem.c`, `host/watch.c` (pure, in `TEST_SRC`), `tests/host/test_watch.c`, `python/libazahar/memory.py`, `tests/python/test_memory.py`, `test_memory_live.py` | G (new) | phase-g.md |
| `tests/host/test_main.c`, `tests/host/test_main.h` | G | one line each: register `test_watch()` |
| `Makefile` | G | `TEST_SRC` gains `host/watch.c` (the `tests/host/*.c` wildcard already takes `test_watch.c`) |
| `python/libazahar/_abi.py`, `_map.py`, `results.py`, `errors.py`, `tests/python/fakeworker.py`, `tests/python/test_abi.py`, `test_map.py`, `docs/USING.md` (a memory section) | G | ABI 3 mirrors, the watch area (its size read from the layout), `GuestMemoryError` |
| `tests/python/test_state.py` | nobody | D's as-built S3 builds `test_newer_abi_refused` from `_abi.AZH_ABI_VERSION`; G only reports if the merged test still has the literal |

A file listed for two steps is edited by the second only after the first's commit is in its worktree (section 2).
**No builder edits a file outside its rows.** F2 may edit another Phase 2 file only when a check fails because of it
and the main loop names the file in a message. Nobody touches: `testapp/`, `tests/check_testapp.py`,
`tests/gate-a.sh`, `tests/gate-b.sh`, `tests/testapp_log.py`, `tests/checks_c.py` (import only),
`tests/python/conftest.py` (D's fixtures are the holds H1; a missing fixture is reported, not added), `host/state.c`,
`host/statemeta.c`, `host/crop.c`, `host/frame.c`, `core/`, `.gitignore`, `docs/map/*`, `docs/PLAN.md`,
`docs/plans/*`, `docs/hours.tsv`, the handoff, **every item file**, `prototype/`, `README.md`, and MAIN (read and
copy only; MAIN's `build-core/` is read only for builders). **No builder ever runs `tools/build-core.sh`**: in a
worktree its build tree is `dl/azahar-src/build-src`, which the seeding links to MAIN's, so a run would delete
MAIN's build tree and start a full build (review 2 N10). Lines the main loop must add (`.gitignore`,
`docs/map/runners.md`, `docs/map/tools.md`) and the "Lessons and notes" block for the item go in each builder's
report.

## 4. Merge plan (the main loop does every commit; agents never commit)

0. **Step 0, "P9b"** (main loop, on main in MAIN; a timed part under rule T). **When:** D merged on main and Phase
   2's last emulator run ended (D's fix reruns); nothing else timed running. **Files** (the main loop writes them; no
   builder, review 2 section 4):
   - `core/patches/0007-lazpy-no-default-clcert.patch` on `src/core/hle/service/http/http_c.cpp`: one notice line
     after line 3, `// Modified by libazahar-py, 2026: removes the built-in default ClCertA (the ctr-common-1
     certificate and key); without the console's own ClCertA file the HTTP service has no client certificate.
     Licensed GPLv2 or later, as this file.` (0000's pattern, GPLv2 2(a)); delete lines 37-38 (the two `#include
     "ctr-common-1-*.h"`); in `DecryptClCertA` replace the fallback body (`:2282-2288`, from `LOG_ERROR(...
     "ClCertA file missing, using default");` through the second `memcpy`) with `LOG_ERROR(Service_HTTP, "ClCertA
     file missing");` and `return;`; the `else` branch stays.
   - `core/patches/0008-lazpy-no-key-loading.patch` on `src/core/hw/aes/key.cpp` (Q6, default yes): one notice line
     after line 3, `// Modified by libazahar-py, 2026: GetKeysStream returns an empty stream, so no AES, RSA or ECC
     key is ever loaded (aes_keys.txt is not read). Licensed GPLv2 or later, as this file.`; in `GetKeysStream()`
     (`:292-314`) keep the `filepath` and `CreateFullPath` lines and replace the rest of the body with `return
     std::istringstream("");` (RSA `rsa.cpp:101` and ECC `ecc.cpp:65` read the same stream).
     Make both with `diff -u` from copies of the reading tree's two files (`unpacked/`; no patch 0000-0006 touches
     either file, checked 2026-11-13), labels `a/src/...` and `b/src/...`, so they apply after 0006 with `--fuzz 0`.
   - `core/PIN` gains three lines (`LAZPY_REV=1` and the `-lazpy.1` suffix stay: nothing is released, `build.inputs`
     tells builds apart, N7):
     ```
     LAZ_CORE_DROP=src/core/hw/default_keys.h src/core/hle/service/http/ctr-common-1-cert.h src/core/hle/service/http/ctr-common-1-key.h externals/libressl
     OPENSSL_VERSION=3.6.5
     OPENSSL_PREFIX=/opt/homebrew/opt/openssl@3
     ```
   - `tools/build-core.sh` (POSIX sh, `set -eu` kept):
     (a) **OpenSSL pin**, before the tarball step: `OSSL_VER=$(pin OPENSSL_VERSION)`; `OSSL=$(cd -P
     "${LAZ_OPENSSL_PREFIX:-$(pin OPENSSL_PREFIX)}" && pwd) || die ...` (the keg's real path,
     `/opt/homebrew/Cellar/openssl@3/3.6.5`; never `/opt/homebrew` itself, whose `include/` holds every brew
     header); die unless `$OSSL/lib/libssl.a`, `$OSSL/lib/libcrypto.a`, `$OSSL/include/openssl/opensslv.h` exist;
     die "OpenSSL at $OSSL is <x>, core/PIN pins $OSSL_VER (re-pin core/PIN on purpose)" unless `sed -n 's/^#
     *define OPENSSL_VERSION_STR "\(.*\)"$/\1/p'` of `opensslv.h` equals `$OSSL_VER`, and unless `strings -a
     $OSSL/lib/libcrypto.a` has a line holding `OpenSSL $OSSL_VER ` (header and library agree; do not trust `brew
     info`, whose JSON here says 3.6.1/3.5.9 while the keg is 3.6.5).
     (b) **STAMP** hashes the patches and the drop list: `$({ cat "$PATCHES"/*.patch; pin LAZ_CORE_DROP; } | shasum
     -a 256 | cut -d' ' -f1)`.
     (c) **drop**, after the unpack and before the patches, under `set -f`: an empty list dies; each entry that
     starts with `/`, holds `..`, or is not in the fresh tree (`[ -e "$TREE/$E" ]`) removes `$BUILD_SRC` and dies;
     else `rm -rf -- "$TREE/$E"` and `say "dropped $E"`.
     (d) before configure, `rm -rf build-core/build/externals/libressl` (the bundled LibreSSL's stale objects and
     `.o.d` files from earlier builds).
     (e) **configure** gains `-DUSE_SYSTEM_OPENSSL=ON -DOPENSSL_USE_STATIC_LIBS=TRUE -DOPENSSL_ROOT_DIR="$OSSL"
     -DOPENSSL_INCLUDE_DIR="$OSSL/include" -DOPENSSL_SSL_LIBRARY="$OSSL/lib/libssl.a"
     -DOPENSSL_CRYPTO_LIBRARY="$OSSL/lib/libcrypto.a"` (explicit paths: `find_package(OpenSSL 1.1)` at
     `externals/CMakeLists.txt:320-322` then takes them as found; its `OpenSSL::SSL`/`OpenSSL::Crypto` reach
     `httplib` (`:362`), which `citra_core` links (`src/core/CMakeLists.txt:508`), so the static libs land on
     `citra_libretro`'s link line). Build the command once as `set -- cmake ...` and run `"$@"`, so step (g) can
     write the same words.
     (f) **after configure**, die unless the cache has the exact lines `USE_SYSTEM_OPENSSL:BOOL=ON`,
     `OPENSSL_SSL_LIBRARY:FILEPATH=$OSSL/lib/libssl.a`, `OPENSSL_CRYPTO_LIBRARY:FILEPATH=$OSSL/lib/libcrypto.a`
     (the type field may read `FILEPATH` or `UNINITIALIZED` for a `-D` without a type: match `:[A-Z]*=`; beside the
     existing `ENABLE_BUILTIN_KEYBLOB:BOOL=OFF` guard) and the cache's
     `FIND_PACKAGE_MESSAGE_DETAILS_OpenSSL:INTERNAL=` line holds `v$OSSL_VER` (not `configure.log`'s "Found
     OpenSSL" line: CMake prints it only when the details change, so the second configure, `--build` after
     `--configure-only`, would not have it).
     (g) **`--build` writes `build-core/build.inputs`** after the configure guards and before compiling (to `.tmp`,
     then `mv`); `--detach` deletes the old one beside `build.exit` (`:25`). One `key=value` per line:
     ```
     tarball=<sha256 of the tarball>
     pin=<sha256 of core/PIN>
     script=<sha256 of tools/build-core.sh>
     patch <file name>=<sha256>          (one line per applied patch, in name order)
     drop=<LAZ_CORE_DROP>
     openssl_version=<OSSL_VER>
     openssl_prefix=<OSSL>
     openssl_libssl_sha256=<sha256 of $OSSL/lib/libssl.a>
     openssl_libcrypto_sha256=<sha256 of $OSSL/lib/libcrypto.a>
     head=<git -C "$ROOT" rev-parse HEAD, or none>
     clean=<yes when git -C "$ROOT" status --porcelain -- core tools/build-core.sh prints nothing, else no>
     cmake=<the configure command's words, with $ROOT written as <repo> (no user name in a file Phase 4 quotes)>
     ```
     (h) **after the compile**: the `.o.d` guard (`:110-112`) loops over every drop entry's basename (`grep -lF`;
     die "an object still reads <entry>, which is dropped"); `L=build-core/build/src/citra_libretro/CMakeFiles/
     citra_libretro.dir/link.txt` must name `$OSSL/lib/libssl.a` and `$OSSL/lib/libcrypto.a` and must not hold
     `libressl` (case-insensitive).
     (i) **atomic install** (N8): `cp` to `$DYLIB.tmp`, `strip -x`, `codesign --force -s -`, `codesign -v`, die if
     `otool -L "$DYLIB.tmp"` names `libssl` or `libcrypto` ("static OpenSSL only; stop and report"), then `mv -f
     "$DYLIB.tmp" "$DYLIB"`.
     Header comment: `LAZ_OPENSSL_PREFIX` (default the PIN's `OPENSSL_PREFIX`).
   - `core/README.md`: rows for 0007 and 0008; a "Dropped from the tree" paragraph (the list, deleted after unpack
     and before the patches, in the STAMP; turning `ENABLE_BUILTIN_KEYBLOB` or the bundled LibreSSL back on now
     fails at configure); an "OpenSSL" paragraph (static OpenSSL 3.6.5 from Homebrew's `openssl@3` keg, pinned in
     PIN, another version refused, `brew install openssl@3` a build prerequisite); Licenses: OpenSSL 3 is
     Apache-2.0, so the combined binary is distributed under GPLv3 (Azahar's "or later"); the source of a published
     binary is the tarball minus the drop list, plus the patches, plus OpenSSL 3.6.5's source (Phase 4 writes the
     offer).
   **Checks before the commit** (in MAIN; `T=dl/azahar-src/build-src/azahar-unified-source-2126.2`):
   `sh -n tools/build-core.sh`; `nice -n 10 tools/build-core.sh --configure-only` (it re-unpacks because the STAMP
   changed, drops, patches 0000-0008 with `--fuzz 0`, configures with the OpenSSL guards; a few minutes, no
   compile; this replaces review 2's scratch unpack and also tests the script and the static-OpenSSL configure):
   four `dropped` lines, `patch 0007-lazpy-no-default-clcert.patch ok`, `patch 0008-lazpy-no-key-loading.patch
   ok`, `applied 9 patches, 0 rejects`, `configure done`; `grep -c ctr_common_1
   $T/src/core/hle/service/http/http_c.cpp` = 0; `grep -c default_keys_enc $T/src/core/hw/aes/key.cpp` = 0; none of
   the four drop entries exists under `$T`; `grep -c 'Modified by libazahar-py' $T/src/core/hle/service/http/http_c.cpp
   $T/src/core/hw/aes/key.cpp` = 1 each; `grep -E '^(USE_SYSTEM_OPENSSL|OPENSSL_SSL_LIBRARY|OPENSSL_CRYPTO_LIBRARY|
   ENABLE_BUILTIN_KEYBLOB):' build-core/build/CMakeCache.txt` shows ON, the two keg `.a` paths, OFF; `grep 'Found
   OpenSSL' build-core/configure.log` says `found suitable version "3.6.5"` and the cache's
   `FIND_PACKAGE_MESSAGE_DETAILS_OpenSSL` line holds `v3.6.5`.
   **Commit** on main with exact paths (`git add core/patches/0007-lazpy-no-default-clcert.patch
   core/patches/0008-lazpy-no-key-loading.patch core/PIN core/README.md tools/build-core.sh` plus the item and
   handoff files the project rules ask; `git diff --cached --stat`; `status_check.py --strict-handoff`).
   **Launch**: `tools/build-core.sh --detach` in MAIN; a background waiter (`run_in_background`) until
   `build-core/build.exit` exists, bounded 150 min. On 0: `cat build-core/build.inputs` (`clean=yes`, `head=` the
   commit), `otool -L build-core/azahar_lazpy_libretro.dylib`, and `grep -c 'built for newer macOS'
   build-core/build.log` into the handoff (Homebrew's objects say `minos 15.0`, our target is 11.0: risk 11). On
   non-0: section 2's failure rule. E1 and F2-0/F2-1 run meanwhile; no emulator runs until `build.exit` is 0.
1. Before launch: Phase 2 merged; the holds H1-H7 checked in main's code (section 6 names the lines). Move items
   310 and 320 to `1-in-progress/` (and 330 at G's launch), each with its PLAN.md pointer corrected (310 :296, 320
   :311, 330 :317). **After step 0's commit** (so F2's tree hashes to what `build.inputs` records): `git worktree
   list` and a case-insensitive name check (`ls .. | grep -i libazahar-py-`), then `git worktree add -b step-e
   ../libazahar-py-e main` and `git worktree add -b step-f2 ../libazahar-py-f2 main`. Dispatch both sonnets
   without isolation, cwd in the worktree, **together, right after `--detach` started**; they seed `dl/`,
   `vendor/` and the `build-core/` link themselves (each brief's step 0). Agent ids into the handoff.
2. At "E1 done": commit exactly E1's paths on `step-e` (`git add <paths>`, `git diff --cached --stat`); note the sha
   for step 4. Do not resume E yet.
3. At "F2 done": opus as-built review of the step-f2 diff (phase-f2.md section 12); fixes by the resumed F2
   builder if any (reruns under rule T); commit; merge `step-f2` into main; paste the report's "Lessons and notes"
   into item 320 and move it with its Evidence line (one commit with the moved item, per the project's CLAUDE.md).
4. Then, in this order: `git -C ../libazahar-py-e merge --no-edit main` (E1 touches no F2 file, so it is clean; a
   conflict stops and goes to the main loop); resume E with "E1 committed at <sha>; main (with F2) merged into your
   tree at <sha>; go on with E2". `git worktree add -b step-g ../libazahar-py-g main`; in it `git merge --no-edit
   <E1 sha>` (clean for the same reason); launch G with phase-g.md and a message naming
   `../libazahar-py-e/runs/e-speed.rc` and that E2 is running.
5. At "E done": opus as-built review of the step-e diff (phase-e.md section 12). Fixes to files G does not edit go
   on `step-e` (reruns under rule T, queued behind G2 if it runs). **Fixes to `__init__.py`, `host/run.c` or
   `host/azh_pure.h` (files G edits on top of E1) are held** and made on main by the main loop right after step-g
   merges (step 6), never on step-e after G launched. Commit; merge `step-e` into main (clean whether or not step-g
   merged first, step 6); item 310 as in 3. Leave G's worktree alone now.
6. At "G done" (or a resumed G's end): in `../libazahar-py-g` `git merge --no-edit main` (brings E2's files, none
   of which G edits); opus as-built review (phase-g.md section 12); fixes; commit; merge `step-g`; item 330. Then
   any held E fix on main, with its rerun under rule T; then the phase item 300. Remove each worktree only after
   `git status --porcelain` is empty in it. **If G is done first**, merge step-g first (its tree holds E1's
   commit, the same sha as step-e's); step-e's later merge is still clean because E's fixes to G's shared files are
   held (step 5) and E2 edits only `DEFAULT_CAP` and E's own files (review 2 S7).
7. After the phase merges, the full suite runs once as one background batch (the main loop is woken on exit),
   every azhost command under `tools/hold_slot.py`: gates A and B; `gate_c.py` on both cores; `gate_f2.py`; the
   full pytest with `LAZ_CORE` set to each core in turn, each with `--ignore=tests/python/test_pool_live.py` (the
   explicit-core tests run both ways regardless); E's live pool test once (review 2 N9).

## 5. Departures from PLAN.md and refinements

Phase 2's P1-P6 stay approved and in force. This phase's:

| # | PLAN.md says | Phase 3 does | Why | Status |
|---|---|---|---|---|
| P7 | PLAN 2.5's error classes (plus P6's `HostError`) | adds `AZH_E_UNMAPPED` (-11) and `GuestMemoryError` (a direct `LibAzaharError`, not a `ValueError`, with `.addr` and `.length`) for a read or write that touches an unmapped guest page; the core's -1 maps to `AZH_E_ORDER` (`HostError`, its text says "no current process"), -3 to `AZH_E_ARG` (`ValueError`) | PLAN's gate asks for "a clean error" on unmapped reads; a caller probing memory (Gen3D's harness, G's own straddle test) must tell "that page is not mapped" from a host bug without parsing text | **approved** (Guy, Q2, 2026-11-12) |
| P8 | PLAN 2.4: "a committed option profile ... Users override per key" (one profile) | on our core, the lines of `core/options-lazpy.txt` are applied first, then the profile, then the caller's options (later wins); azhost `--lazpy-profile FILE\|none`, Python `LAZ_LAZPY_PROFILE` | PLAN 2.4 says our core's options are "all pinned on in our core's profile", but no Phase 1 or 2 code applies that file: patch 0002 registers the six keys with stock defaults, so without it the debug-text stop is `AZH_E_ARG` on our core and repeats are not exact. The two files share no key (checked by a test) | **approved** (review 1: "sound and necessary") |
| R1 | PLAN Phase G: "a write changes the next logged line" | m3 checks the next **event** line (`ready f=<written>`) after a write of the control struct's `ready_at` | the record behind the per-frame line is rewritten from scratch every frame (B6), so a write into it can never reach a log line; the control struct is read every frame | refinement (review 1 N10) |
| R2 | PLAN Phase E: "running 1, 2 and 3 instances"; "sets the default cap" | the table adds a 4-instance row on the cap's core, and the cap rule may reach 4 | Guy, Q3 ("Allow 4 too"); the rule is fixed in phase-e.md section 7 before any run | **approved** (Guy) |
| R3 | PLAN Phase E: "an optional local row on a Gen3D 3D scene that agents may skip" | skipped; the cap stays marked provisional (light scene); `speed_table.py` has no state-row option | Guy, Q1 ("Skip it") | **approved** (Guy) |
| R4 | PLAN.md:314: "the debug-text stop fires on the exact frame" | "exact" = the same host frame on every run (F2's d4) and within one frame of the ready line's host frame (d3: `last - (ready.v + c_min)` is 0 or 1) | the host frame a guest line lands in depends on where the slice ends (`citra_libretro.cpp:286-306`); exactness is carried by d4 | refinement (review 2 S3) |

Not departures, listed so the reviews see them: ABI 3 appends fields to `azh_batch` and `azh_result` and grows the
map (G); states made under ABI 2 still load under ABI 3 (H3); `azh_stats` is already valid after open (H6), so F2
changes nothing there; P9 (key blob off) is Phase 4's departure, and step 0 ("P9b": no ClCertA, no key loading,
static OpenSSL 3, Guy's ruling) applies it with Phase 4 review 1's asks before F2, so F2 gates the binary that ships.

## 6. Interfaces taken from Phases 1 and 2

"State": **holds** (checked in code on main, 2026-11-12, main at 0928a6f with C merged at 7584a8d), **hold** (Phase
2 delivers it before its merge; checked in `../libazahar-py-d`'s working tree while D's fixer runs), **planned**
(not yet in any code). The builder checks every row against the merged code and reports a difference.

**Phase 2's holds** (the briefs rely on them; the main loop checks each in main before launch). D's as-built fixes
(S1 `held_after` in `emulator.py` `run`, S3 the abi test, optional N1/N5) move some of D's line numbers below; the
builders follow the merged code. Expected baselines after D's fixes: non-slow pytest "49 passed", full "69 passed".
- **H1** `tests/python/conftest.py`: `host_paths` resolves the core with `_paths.core_path()` (honours `LAZ_CORE`) and
  checks that file; session fixtures `stock_core` (`<repo>/dl/azahar/azahar_libretro.dylib`) and `lazpy_core`
  (`LAZ_CORE` when it names our core, else `<repo>/build-core/azahar_lazpy_libretro.dylib`, where `<repo>` is **the
  checkout the tests run in**, so every worktree links `build-core/azahar_lazpy_libretro.dylib` to MAIN's in its step 0,
  review 2 B2), each skipping, or failing under `LAZ_REQUIRE_EMULATOR=1`, when missing; the session header prints
  `core=<path> kind=<kind>` (kind `lazpy` when the file name holds "lazpy", else `stock`). D's c4 test already passes
  `core=stock_core`.
- **H2** the worker's nice is **at least 10**: it raises its niceness to 10 only when the parent is nicer
  (`_worker.py`), so under `nice -n 10` the workers sit at exactly 10.
- **H3** `host/state.c` accepts `2 <= meta.abi <= AZH_ABI_VERSION` (an ABI-2 state loads under ABI 3).
- **H4** the azhost summary is `frames= wall= fps= shots= stop= first= last= vblanks= wall_ms_mean= batch= msg=`
  (`host/azhost_main.c:565`); there is no `wall_ms_max`.
- **H5** D3's state boot is gated by an absolute bound: `t_state` (the wall of the restoring `Emulator(...)`) under
  **2.5 s** on the test app (Guy's ruling); `test_state_boot` records `t_state`, the ratio and the load line in
  `runs/d-pytest/state-times.txt`, then asserts the bound itself (D's as-built S2 removes
  `test_state_boot_wall_ratio`); the 10 % ratio is recorded only. Its recipe copies a's `sys/` minus `Azahar/sdmc`
  into b before b boots (`test_state.py:48-51`), so the shader cache and NAND come along.
- **H6** `azh_stats` is valid any time after `azh_open` (`host/api.c` `azh_stats`: refuses only `AZH_PH_NONE`).
- **H7** the Emulator closes itself after a returned `guest_exited` on both cores (`emulator.py` `run`), with
  `close(self.timeout)`.

| # | What Phase 3 relies on | Source | State | Used by |
|---|---|---|---|---|
| A1 | `AZH_E_*` -1 ARG, -2 ORDER, -3 CORE, -4 BOOT, -5 VULKAN, -6 IO, -7 NOMEM, -8 UNSUPPORTED, -9 NEEDS_LAZPY_CORE, -10 SAVESTATE; G adds -11 | `host/azhost.h:11-13` | holds | G |
| A2 | `int azh_read(uint32_t addr, uint32_t len, void *buf)`, `int azh_write(uint32_t addr, uint32_t len, const void *buf)` exist; after open on our core they return `AZH_E_UNSUPPORTED` ("arrives in step G"), on stock `AZH_E_NEEDS_LAZPY_CORE`; G tightens the order to "after boot" | `host/api.c` `memory_gate` | holds | G |
| A3 | Our core is detected at `azh_open` by `dlsym(core, "lazpy_read_memory")` in `azh_core_open`; the result is `azh_stats.is_lazpy_core` | `host/core.c:100` | holds | F2, G |
| A4 | Call order: open, options, boot, then run/shot; `azh_stats` after open (H6); `azh_abi_layout`, `azh_error` in any state | `host/api.c` | holds | F2 |
| A5 | `azh_set_option` checks at once that the key was registered by the core and the value is listed, else `AZH_E_ARG` naming the key; our core registers its six extra keys; at boot host.log has one `option <key>=<value>` line per key (`host/options.c:164`) | phase-a; `host/options.c` | holds | F2, E (the option set per table row) |
| A6 | `azhost run` defaults are relative to the current directory; `--profile host/options-default.txt`; profile then `--opt`, later wins | `host/azhost_main.c:155, 496-499` | holds | F2 |
| A7 | `azh_version_ok` accepts `2126.2` and `2126.2-lazpy.1` (`host/pins.h`); host.log logs `core <name> version <v>` at open (`host/core.c:72`) | as built | holds | F2 |
| A8 | `host/png.c` is **pure** (stdlib and zlib only) and in `TEST_SRC` (`Makefile:42` in D's tree, which merges first; 41 on main today); `#define PNG_LEVEL 6` at `png.c:11`, used by `compress2` at `:136` | as built | holds | E |
| A9 | The readback runs only on asked shot frames (`run.c` `run_frames` takes shots only for asked frames) | `host/run.c:310-330` | holds | E |
| A10 | `azh_stats_t` fields: frames, wall_s, user_s, sys_s, peak_rss, core_name, core_version, is_lazpy_core; size 240 | `host/azhost.h` | holds | E, F2 |
| A11 | One `azh_open` per process (`api.c` `opened_once`) | as built | holds | E |
| A12 | `log.c` writes the core's line literally | `host/log.c` | holds (C merged; the builder checks) | F2 |
| B1-B9 | The test app: `build/testapp.3dsx` (devkitARM first in PATH); control keys `draw`, `break_at`, `exit_at`, `ready_at` (1-1,000,000), `boot_frames` (1-10,000); `start addr_global= addr_heap= ...` line, per-frame `f= v= s= t= k= tx= ty= td= cx= cy=`, events `ready`, `booted`, `break`, `exit`; in 3D `v == f`; `laz_record` 32 bytes (magic 0, frame 4, vblank 8, keys 12, tx 16, ty 18, cx 20, cy 22, tick 24); per frame `hidScanInput`, `record_fill(&g_record)`, heap `memcpy`, log; `static laz_control g_ctl` (`mode3d` 0, `break_at` 4, `exit_at` 8, `ready_at` 12, `boot_frames` 16, `error_count` 20, `error_line` 24); `LAZ_FRAME_CAP` 100,000,000; `check_testapp.py markers` | `testapp/source/record.c:43-48, 58-61`, `record.h:13-21`, `control.h:11-19`, `main.c:16, 23-25, 137-174`, `scene3d.c:77-85` | holds (review 1 found `g_ctl` 100 bytes from `g_record` in C's `testapp.elf`) | all |
| F1 | Patch 0001: `lazpy_read_memory(uint32_t vaddr, void *buf, uint32_t len)` and `lazpy_write_memory(uint32_t vaddr, const void *buf, uint32_t len)`: 0 ok, -1 not running / no process / exception, -2 a page unmapped, -3 bad args (NULL, len 0, len > 0x4000000, `vaddr + len > 2^32`); every page checked before any byte moves | `core/patches/0001-lazpy-memory-exports.patch` | holds | G |
| F2a | `lazpy_movie_play(const char *path)` | patch 0006 | holds | not used |
| F3 | The six options in `core/options-lazpy.txt`; patch 0002 registers them **with stock defaults** | `core/options-lazpy.txt`; patch 0002 | holds | F2, E |
| F4 | Patch 0003 (our `retro_run` returns after `DisplayMessage`), 0004 (log filter), 0005 (the version is `g_build_fullname + "-lazpy.1"`, assembled at run time; the dylib's strings hold `-lazpy.1`) | patches 0003-0005 | holds | F2 |
| F5 | `tools/build-core.sh --detach` in MAIN: `build-core/build.pid`, `build.exit`, `build.log`; output `build-core/azahar_lazpy_libretro.dylib`; the first build (keys ON) ended 19:40 (19,195,472 bytes, key blob in it); the P9 build (e40e59c) ended 21:09 with 0 (19,145,936 bytes, keys OFF, 0 `/Users/`, but ClCertA in and LibreSSL linked); **step 0's build replaces it** and adds `build-core/build.inputs` | `tools/build-core.sh:95-117` (committed at e40e59c); section 4 step 0 | holds (21:09); planned (step 0) | F2 |
| C1 | ABI 2: `azh_batch` 3348, `azh_result` 304, `azh_stats` 240, `azh_layout` 6452 (`n_fields`, `fields[160]` of 40 bytes); **114** `field_rows`; `_Static_assert` rows <= `AZH_MAX_FIELDS` (160) | `host/api.c:49-166`, `host/azhost.h:38, 66` | holds | G |
| C2 | Map version 2; offsets 16 heartbeat .. 1104 exit_code, 4096 pixels; size 695,296; bytes 1108-4095 free | `host/hostmap.c`; `python/libazahar/_map.py` | holds | G |
| C3 | After each `retro_run` (`azh__run_one_frame`): totals, then `take_shots`, then the stops; every stop returns 0 | `host/run.c:102, 173, 310-330` | holds | E (timing line), G (watch rows between `azh__run_one_frame` and `take_shots`) |
| C4 | On our core status 16 is `AZH_ACT_EXITED` (`stop=guest_exited`); a crash is `AZH_ACT_ERROR` with no count; the exit path (`_exit`) runs only on stock and writes one fixed line (`host/env.c:40-56`) | `host/msg.c:75`, `host/env.c` | holds | F2 |
| C5 | On our core a debug-text stop needs `citra_instant_debug_log=enabled` in the option store, else `AZH_E_ARG`; on stock `AZH_E_NEEDS_LAZPY_CORE` | `host/api.c` `check_stop_rules` | holds | F2 |
| C6 | `azhost run` flags `--inputs`, `--sd-seed`, `--stop-*`, `--debug-stop`, `--wall-limit-ms`, `--frames N[,N2]`, `--raw-shot`, `--print-last-line`, `--save`; summary as H4; exit 10/11 on our core; exit 7 for a debug stop on stock; `azhost layout` prints `abi=<n>` and every row | `host/azhost_main.c` | holds | F2, G |
| C7 | `tests/gate_c.py` scenarios a-f, `--only`, `run_azhost(ident, flags, control, timeout)` (kills its child on any `BaseException`), PASS/FAIL lines, `runs/c-gate.rc`; no `--core` yet; no `abi=` literal | `tests/gate_c.py:26-60, 245` | holds | F2 (switches, reuse), G |
| D1 | Modules `__init__`, `_abi`, `_host`, `_worker`, `_map`, `_client`, `_paths`, `inputs`, `results`, `errors`, `emulator`; stdlib only, numpy optional | phase-d 4.1 | hold | E, F2, G |
| D2 | Worker spawn: `python -I -c "<...> main(int(sys.argv[1]))" <child fd> <pkg_parent>`, `pass_fds=(child_fd,)`, cwd the workdir, stderr to `worker.err`; the fake worker's argv is a callable | `_client.py:28-29, 42-44, 108-126` (D tree) | hold | E |
| D3 | Worker ops `start` (core, sysdir, log, map, options, app, state; `azh_stats` after boot), `run`, `set_input`, `shot`, `save_state`, `load_state`, `stats`, `close`; replies `("ok", x)` / `("err", code, text)`; nice as H2 | `_worker.py:27-41, 110-112` | hold | E, F2, G |
| D4 | Wait loop and death mapping: exit 10 during `run` gives `("exited", info)` and `RunResult(stopped_by="guest_exited")`; H7; 11 `GuestError`; else `HostCrashed`; heartbeat timeout `HostTimeout` and SIGKILL of its own worker | `_client.py:212-249`, `emulator.py` | hold | E, F2 |
| D5 | Errors: `LibAzaharError`; `BootError`, `GuestError` (`.result`), `HostTimeout(op, seconds, message)` (the third argument prints as "(last guest message: ...)"), `HostCrashed`, `StateError`, `NeedsLazpyCore`, `HostError`, internal `HostCallError`; `AZH_E_ARG` becomes `ValueError` with the host's text; `errors.from_code(code, text)` | `errors.py:32-36, 96-97` | hold | E (`SlotTimeout`), G |
| D6 | `Emulator(app, workdir, *, sd_seed, state, core, options, timeout=30.0, boot_timeout=300.0)`; `run(frames, inputs, shots, *, stop_file, stop_text, stop_every, stop_new, debug_text, wall_limit, timeout)`; `run_until` delegates to `run`; `set_input`, `run_frame`, `set_keys`, `screens`, `shot`, `save_state`, `load_state`, `stats`, `sd`, `frame_total`, `pid`, `closed`, `close` | `emulator.py:62-64, 133-175, 226-232, 306-311` | hold | E, F2, G |
| D7 | `RunResult(frames, stopped_by, first_frame, last_frame, frame_total, vblanks, wall_s, message, shots)` (frozen; `shots` has a default); `Stats` mirrors `azh_stats` | `results.py:19-32` | hold | E, G |
| D8 | `_paths`: `repo_root`, `host_path`, `core_path` (`LAZ_CORE`, else `<root>/dl/azahar/azahar_libretro.dylib`), `mvk_path`, `profile_path` (`LAZ_PROFILE`); `emulator.py` `_read_profile(path)` reads `key=value` lines | `_paths.py`, `emulator.py:25-48` | hold | F2 |
| D9 | States: `<path>`, `<path>.sd/`, `<path>.meta` (`abi=`, `k=`, `frame_total=`, ...); a different `core_version` only warns; abi range as H3; `test_newer_abi_refused` built from `_abi.AZH_ABI_VERSION` with an abi-1 case (D's as-built S3); the meta parse is strict on keys, so a new meta key would have to be optional for ABI-2 metas (G adds none) | `host/state.c:395-398`; `tests/python/test_state.py:116-124`; `statemeta.c:154` | hold | F2, G |
| D10 | Fixtures as H1, `workdir` (`runs/d-pytest/<test>/`, deleted and remade), `seed(**control_keys)`, `repo_root`; `d_helpers.boot(paths, workdir, seed_dir, **kwargs)`; marker `slow` (`pyproject.toml:22`); `fakeworker.py` modes | `tests/python/conftest.py`, `d_helpers.py` | hold | E, F2, G |
| SD | SD file writes are synchronous on the emulator thread; OpenFile, SetSize, Close are async on the stock core | phase-2.md SD | holds | F2 |

## 7. Hours, against PLAN.md (agent wall time)

| Step | Builder | Review | Commit | Total | PLAN.md | Why the difference |
|---|---|---|---|---|---|---|
| E | 0.81 (E1 0.41, E2 0.4) | 0.2 | 0.1 | **1.11** | 1.0 | the live slot gate holds real slots while it tests a private cap; the 4-instance row and its rule (R2, +0.03 h); the `slot=` keyword (review 2 B3, +0.01 h); less the cut state row (R3) and the cut `_slots` timing print |
| F2 | 0.48 (F2-0 0.05, F2-1 0.23, F2-2 0.2) | 0.2 | 0.1 | **0.78** | 0.75 | P8's profile application and f1's supply-chain checks (review 2 B1, N3-N5, the OpenSSL checks: +0.05 h), offset by the cuts: no `azh_stats` change (H6), no conftest work and no guest-exit close code beyond a 5 s wait (H1, H7), `gate_c`'s runner reused (N12), the stock smoke (Q4), the by-hand 30-frame check folded into `--only keyblob,symbols,version` (-0.02 h) |
| G | 0.55 (G1 0.4, G2 0.15) | 0.2 | 0.1 | **0.85** | 0.5 | PLAN's 0.5 h did not count the ABI 3 bump the watch list needs (header, `fields[]`, `_abi.py`, the map area); less the cut Python mirror of the watch plan (N4) and the halved G2 batch (B4) |
| Review loops | | | | 0.5 | 0.5 | |
| **Phase** | | | | **3.24** | **2.75** | |

Main loop (not in the table): step 0 (the two patches, PIN, the script edits, README, the configure check, the
commit and the launch, about 0.2 h) and the checkpoint choreography and the item moves (about 0.2 h): **about 0.4 h**.

## 8. Risks for this phase

1. **Step 0's rebuild fails or changes behaviour.** A failure is the main loop's (section 2); F2 runs no emulator
   until `build.exit` is 0 and `build.inputs` matches. With the key blob off, 0008 and 0007, the core loads no keys
   and has no ClCertA; the test app is an unencrypted `.3dsx` and needs neither (`DecryptClCertA` returns at the
   missing key slot 0x0D, `http_c.cpp:2262-2266`, before the removed branch). If F2's batch shows a difference from
   Phase 2's results that traces to keys, F2 reports it and the main loop takes it to Guy (Phase 4's G1); nobody
   turns the blob, the keys or the ClCertA back on.
2. **Repeats are not identical on our core** (a host thread still leaks into guest time: the Vulkan presentation
   thread, shader compiles, an async path the option does not cover). F2 records the first differing log line and
   shot, does not tune, and reports; a new patch is a Phase 3 change of scope.
3. **Torn reads in G**: `retro_run` returns after the slice in which the VBlank fired, so the guest may be part-way
   through `record_fill` for the next frame. G's checks allow a record whose fields all come from line f or f-1 and
   fail above 1 % of reads; the watch rows share the risk.
4. **Phase 2's holds are not all in the merged code.** The main loop checks H1-H7 before launch; a missing hold is
   either added to Phase 2 before its merge or named to the builder whose brief relies on it.
5. **The control-struct write test depends on B's layout** (B7) and on the u32 pair (999001, 999002) appearing once
   near `addr_global`. G scans a bounded window and fails with the hit count if it is not exactly one.
6. **Timed runs overlap** another session's emulators. Each table row records the load at its start and end; the
   slot cap counts only libazahar's workers; rules.md 5. The cap rule (phase-e.md section 7) is fixed in advance.
7. **The 4-instance row loads a shared Mac.** It runs 4 instances for 60 s on one core only, through the real slot
   folder (all 4 slots held, so cap-3 users wait); the rule refuses 4 unless the end load is below 2 x cores.
8. **The map grows to 4,890,624 bytes per instance** (the 4 MiB watch area). The file is `ftruncate`d, so unwritten
   pages cost no disk on APFS and no memory until touched. G measures `du -k host.map` and RSS.
9. **A between-frames read touches GPU-cached pages** (VRAM, linear heap): `ReadBlock` flushes the rasterizer cache
   for them. It runs on the worker's one thread, the same thread as `retro_run`, so it is safe; reads are only made
   by the thread that runs batches.
10. **The default cap rests on a light scene** (Guy, Q1: no real-scene row). The table labels it "light" (rules.md
    7) and the cap stays marked provisional; spike 2's real-scene numbers are quoted beside it.
11. **Static OpenSSL from Homebrew.** (a) The static link may need a system library the dylib did not (Homebrew's
    `libcrypto.3.dylib` links only `libSystem`, so probably none): the main loop may add a system framework or zlib
    and records it; F2 RECORDs the link line's `-framework`/`-l` items. If static linking is impossible, stop and
    report to Guy; never the dylib, never LibreSSL. (b) Homebrew's objects are built for macOS 15.0 (`minos 15.0` in
    `libcrypto.a`, checked 2026-11-13) while our `MACOSX_DEPLOYMENT_TARGET` is 11.0: `ld` warns, and the core's real
    minimum becomes 15.0; F2 records the warning count, Phase 4 states the minimum (section 12). (c) The rebuild
    recompiles `citra_core` and `network` (their OpenSSL include path changes): 60-120 min on a loaded Mac, on the
    critical path F2 -> E2 -> G2; F2-0 and F2-1 run meanwhile. (d) A `brew upgrade` changes the keg: the script
    refuses another version, so a later build stops until `core/PIN` is re-pinned on purpose.

## 9. Hour-saving pass (revision 1)

Kept from revision 0 (each still the cheapest path): the slot fd passed to the worker with `pass_fds` (no worker
slot code); `ThreadPoolExecutor` for `Pool`; the kill-frees-slot check with a plain `sleep` child plus one
Emulator-level kill; one batch per instance per row; the per-batch timing line instead of a profiler; D's nice and
A's readback-on-asked-frames only checked; one table run for both cores; `--lazpy-profile` defaulting on; the
repeats reusing gate C's and D's shapes; no core patch in G; the write test through a scanned control struct; no
azhost memory flags; copied watch rows; no ring buffer; libmgba-py's `raw_read` names.

Revision 1, each item checked against the code or the review:

| Cut, existing thing or cheaper test | Saves | Verdict |
|---|---|---|
| Phase 2's holds H1, H6, H7: D's `host_paths`/`lazpy_core`/`stock_core`, `azh_stats` after open, D's close after a returned exit already exist | F2's conftest edits, its `api.c` change and its close-after-exit code (about 0.08 h) | taken (F2) |
| `gate_c.run_azhost` and its summary parsing imported by `gate_f2.py` (N12) | a second azhost runner (about 0.03 h) | taken (F2) |
| The stock smoke (Q4): `gate_c.py --core STOCK --only c,f` plus `pytest -k "c4 or guest_exit or lazpy"` on STOCK | about 25 min of machine time on the critical path, 0.03 h | taken (F2) |
| The key-blob check as plain file reads in `gate_f2.py` (the cache line, a walk of `.o.d` files, a byte search) instead of a new tool; Phase 4's `release_check.py` may import it | a second checker | taken (F2) |
| No Python mirror of `azh__watch_plan` (N4): C's `AZH_E_ARG` text with the largest-frames hint already reaches the caller as `ValueError` | about 0.05 h | taken (G) |
| Explicit `core=lazpy_core` / `core=stock_core` in G's live tests (B4): one pytest run covers both cores, so G2 is two parts (gate C, one pytest) instead of four | about 0.05 h, about 15 min machine | taken (G) |
| No `AZH_MAX_FIELDS` branch (N3): 114 + 23 = 137 <= 160 | a branch and a size | taken (G) |
| `tools/hold_slot.py` committed by E1 (N7), used by G2 and the phase-end suite | two throw-away helpers | taken (E; F2 keeps its temporary one: E1 is not in its tree) |
| No state-row option in `speed_table.py` (Guy, Q1) | about 0.02 h | taken (E) |
| The 4-instance row on the cap's core only (ours), not on both cores | about 2 min machine | taken (E) |
| The `_slots` 1,000-pair timing print | 0.01 h | cut (E) |
| G stops at "waiting for E2" instead of a longer wait | an unbounded Monitor wait | taken (G) |
| A ready-made lock library (`filelock`, `fasteners`) or POSIX named semaphores for the cap | nothing: not stdlib, and a named semaphore is not released when its holder dies on macOS | declined (review 1 checked) |
| The stock core's `SET_MEMORY_MAPS` instead of the lazpy exports | nothing: it covers only heap and VRAM VMAs present at load, never the app image | declined (review 1 section 5) |
| A sticky `azh_set_watch()` call instead of appending to `azh_batch` | nothing: the ABI still moves for the map rows | declined |
| Reading `g_ctl`'s address from `testapp.elf` with devkitARM `nm` | exact, but a devkitARM dependency in a pytest; the scan costs nothing | declined |
| Drop the phase-end suite (G2 already ran gate C and pytest on ours) | about 45 min machine at the very end, off the critical path | declined: it is the only run of the merged tree (E2's files, held fixes) on both cores |

Revision 2 (review 2 section 6's rows taken, plus this revision's own):

| Cut, existing thing or cheaper test | Saves | Verdict |
|---|---|---|
| 0007, 0008, the drop list, `build.inputs` **and the OpenSSL switch** in one rebuild (step 0) | Phase 4's second rebuild and a gate_f2 rerun (about 0.1 h agent, 20-40 min machine); a third rebuild for OpenSSL | taken (Q6 default yes; Guy's OpenSSL ruling) |
| F2 launched with E right after `--detach`; it seeds, writes F2-1's code and `gate_f2.py`, then waits (Monitor, 150 min) on `build.exit` 0 and a matching `build.inputs` | the rebuild's 20-120 min off the critical path F2 -> E2 -> G2 as far as F2's own agent time reaches | taken |
| The main loop writes the patches and the script change (no brief, worktree or checkpoint for about 60 lines) | about 0.1 h against a sonnet step | taken |
| `--configure-only` in MAIN as step 0's pre-commit check, instead of review 2's scratch unpack outside `dl/` | about 0.02 h main loop, and it also tests the script edits and the static-OpenSSL configure before the commit and before a long build | taken (departure, section 14) |
| F2-1's by-hand 30-frame check replaced by `gate_f2.py --only keyblob,symbols,version` right after the build | about 0.02 h F2 and one emulator start | taken |
| The OpenSSL and LibreSSL checks inside `keyblob_findings` (the same `strings -a` pass, the same build tree) | a second checker in F2 and in Phase 4's `release_check` | taken |
| `externals/libressl` in the drop list: the bundled LibreSSL cannot be configured by mistake (configure fails) | a separate "LibreSSL not configured" guard | taken |
| One `keyblob_findings` imported by Phase 4's `release_check` | a second implementation in Phase 4 | taken |
| `--ignore=tests/python/test_pool_live.py` in the phase-end per-core pytests (N9) | about 6 min machine | taken |
| D's as-built S3 fixes the abi literal | G's one-line `test_state.py` row | taken (row dropped) |
| Build OpenSSL 3.6.5 from source for macOS 11.0 instead of Homebrew's static libs | nothing now (about 0.2 h plus a pinned download); it only matters for the release's minimum macOS | declined: Guy's ruling names Homebrew's libs; Phase 4 decides (section 12) |
| Raise `LAZ_CORE_JOBS` above 4 for this rebuild | 10-30 min machine on the critical path | declined: a shared Mac (rules.md 5) |
| Cut G2's gate C part | about 10 min machine | declined (review 2: G changes the host library azhost links) |
| Cut F2's `stock_r1` record | about 4 min machine | declined (review 2: Phase 4's USING fix needs it) |

## 10. Facts checked for this plan (reviewers: verify these)

"SRC" = `dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/` (GIT-COMMIT 219d743a1e698101fe1ab8bef43e6563126c3c27,
GIT-TAG 2126.2), read 2026-11-12. "PATCHES" = `core/patches/`. Review 1 verified every row of revision 0's list
(its section 5); the rows below are the ones the briefs use, plus revision 1's new ones (marked new).

| Fact | Where |
|---|---|
| `BASE_CLOCK_RATE_ARM11 = 268111856`; one frame is 4,481,136 ticks (59.831 Hz); `MAX_SLICE_LENGTH` = clock / 234 | SRC core/core_timing.h:37, 40-42, 184 |
| Random base ticks from `std::random_device`; Fixed uses the override | SRC core/core_timing.cpp:37-44; common/settings.h:506-507 |
| `init_clock` SystemTime (plus DST hour) / FixedTime (`init_time` default 946681277) | SRC core/hle/kernel/shared_page.cpp:34-63; settings.h:503-505 |
| `deterministic_async_operations` gates `std::async` in HLE requests | SRC settings.h:490-491; hle_ipc.h:306, 348 |
| `instant_debug_log` writes inline **and flushes every backend per entry** (a speed cost on a chatty app) | SRC settings.h:659; common/logging/backend.cpp:353-357 |
| One `retro_run` = one VBlank: `GPU::VBlankCallback` presents every VBlank, the present calls `SwapBuffers`, which sets `submittedFrame` and ends the loop | SRC video_core/gpu.cpp:488-498; libretro_vk.cpp:710-711; citra_libretro/emu_window/libretro_window.cpp:68-71; the loop citra_libretro.cpp:282-306, its end condition emu_window/libretro_window.cpp:327-331 |
| `ReadBlock` zero-fills unmapped pages, flushes cached pages; `WriteBlock` skips unmapped | SRC core/memory.cpp:173-229, 247-253 |
| `IsValidVirtualAddress`; `CITRA_PAGE_SIZE` 0x1000; `Kernel::GetCurrentProcess()` | SRC memory.cpp:824-837; memory.h:34; kernel.h:319 |
| Exports from `libretro.osx.def` via `-exported_symbols_list` | SRC citra_libretro/CMakeLists.txt:32, 96 |
| A state is refused on program id or revision; the body after the 256-byte `CSTHeader` is zstd | SRC core/savestate.cpp:291-304 |
| `GIT_REV` from `GIT-COMMIT`, `BUILD_FULLNAME` from `GIT-TAG` (so the version is `2126.2-lazpy.1`) | CMakeModules/GenerateBuildInfo.cmake:13-16, 40-55 |
| `async_shader_compilation` defaults to false; `frame_limit` forced to 0 by the libretro core | SRC settings.h:537; core_settings.cpp:1133 |
| macOS `flock(2)`: locks belong to the open file description; an inherited fd keeps the lock after the parent closes; Python `subprocess` uses fork+exec with `pass_fds`, so a sibling thread's child never keeps a slot fd past `exec` | `man 2 flock`; Python docs; review 1 |
| `option(ENABLE_BUILTIN_KEYBLOB ... ON)`; the P9 build (21:09) has `ENABLE_BUILTIN_KEYBLOB:BOOL=OFF` (CMakeCache.txt:728), 1,659 `.o.d` files, none naming `default_keys.h`, one (`http_c.cpp.o.d`) naming `ctr-common-1-*`; the keys-on build's blob [removed] | SRC CMakeLists.txt:154; `build-core/build/`; phase-4.md section 0 |
| `tools/build-core.sh` (committed at e40e59c) passes `-DENABLE_BUILTIN_KEYBLOB=OFF` and `-ffile-prefix-map=$PWD/=` for C and C++ (configure `:95-103`), dies if the cache does not say OFF (`:104-105`), and dies if any `.o.d` names `default_keys.h` (`:110-112`); it installs the dylib in place (`:113-117`); the STAMP hashes the patches (`:68`) | `tools/build-core.sh` |
| `strings -a` of the 21:09 dylib holds `-lazpy.1` as its own string (patch 0005) and 0 lines holding `/Users/` | `strings -a build-core/azahar_lazpy_libretro.dylib`; patch 0005 line 9 |
| new (rev 2): `http_c.cpp:37-38` include `ctr-common-1-cert.h` (`ctr_common_1_cert_bin[1264]`) and `ctr-common-1-key.h` (`[1232]`) with no `#ifdef`; `DecryptClCertA()` (`:2262`) returns at the missing key slot 0x0D (`:2263-2266`), else copies the defaults when the NAND file is missing (`:2281-2289`); it runs from the HTTP service's constructor (`:2507`); no other file names them; `default_keys.h` is included only under `#ifdef ENABLE_BUILTIN_KEYBLOB` (`key.cpp:21-23`) and named in CMake only under the option (`src/core/CMakeLists.txt:501-503`) | SRC core/hle/service/http/http_c.cpp; core/hw/aes/key.cpp |
| new (rev 2): `GetKeysStream()` (`key.cpp:292-314`) is the one key source of AES (`key.cpp:152`), RSA (`rsa.cpp:101`) and ECC (`ecc.cpp:65`) | SRC core/hw |
| new (rev 2): OpenSSL: `USE_SYSTEM_OPENSSL` (default OFF, `externals/cmake-modules/CitraHandleSystemLibs.cmake:9`) makes `externals/CMakeLists.txt:320-322` call `find_package(OpenSSL 1.1)` (not REQUIRED; a miss leaves `OpenSSL::SSL` undefined, so generation fails) and skip `add_subdirectory(libressl)` (`:323-333`); `httplib` links `${OPENSSL_LIBRARIES}` (`:361-362`); `citra_core` (`src/core/CMakeLists.txt:508`) and `network` link `httplib`; `web_service` is off in our build (`ENABLE_WEB_SERVICE:BOOL=OFF`); `<openssl/rand.h>` is included only by `ssl_c.cpp` and `am.cpp` | SRC; `build-core/build/CMakeCache.txt` |
| new (rev 2): the 21:09 dylib links LibreSSL (`link.txt`: `../../externals/libressl/ssl/libssl.a`, `.../crypto/libcrypto.a`), holds `externals/libressl/...` source-path strings but no "LibreSSL" string, and no line equal to `3.6.5`; so f1's `libressl` and version checks both fail on it | `strings -a`, `link.txt`, 2026-11-13 |
| new (rev 2): Homebrew `openssl@3` here: `/opt/homebrew/opt/openssl@3` -> `../Cellar/openssl@3/3.6.5`; `opensslv.h` `OPENSSL_VERSION_STR "3.6.5"`, text `OpenSSL 3.6.5 29 Sep 2026`; `libssl.a` 1,475,544 bytes sha256 `23c6a50d6e01660db8ad58ed2f71305bf634970f044be2289b18d55ebc0370d9`, `libcrypto.a` 8,593,624 bytes sha256 `88981a4c6ce3c36127d12f6e7053b926d8a70ec1dbd0fa259113e6c8514a0583`; its objects say `minos 15.0`; `libcrypto.3.dylib` links only `libSystem`; the version text lives only in `cversion.o` (pulled only if something calls `OpenSSL_version`), the bare `3.6.5` also in the providers (`defltprov.o`, `baseprov.o`, `provider_core.o`); `brew info --json` disagrees (3.6.1 installed, 3.5.9 stable), so the header is the source of truth; cmake 4.3.4 | `ls`, `otool`, `strings`, `shasum`, 2026-11-13 |
| new: host.log has one `option <key>=<value>` line per registered key at boot (`(core default)` when unset) | `host/options.c:164` |
| This Mac: 12 cores (6 performance), 18 GB RAM, load 17-24 at planning time; PLAN's load warning is above 2 x cpu_count = 24 | `sysctl`, `uptime`, 2026-11-12 |

## 11. Questions (all answered)

- **Q1 (Guy, 2026-11-12): the real-scene row.** "Skip it": no Gen3D row; the cap stays provisional on a light
  scene (R3).
- **Q2 (Guy): P7.** "Approve": `AZH_E_UNMAPPED` -11, `GuestMemoryError` with `.addr`, `.length`.
- **Q3 (Guy): the cap rule.** "Allow 4 too": a 4-instance row, and the rule may reach 4, in the same shape: step up
  from n-1 to n only if T(n) >= 1.25 x T(n-1) and the end load of the n row is below 2 x cores (phase-e.md section
  7, written before any run).
- **Q4 (review 1): F2's stock regression.** Cut to the stock smoke (phase-f2.md f9).
- **Q5 (review 1): the watch area.** Fixed 4 MiB; Python reads the area's size from the layout's `map.watch_data`
  and `map.__size__` rows, so a later resize is host-only with no ABI bump (phase-g.md section 4).
- **Q6 (review 2 S4): patch 0008 (load no keys at all) in the same rebuild?** Main-loop default **yes** (2026-11-13;
  the conservative side, reversible by dropping the patch); it is in step 0. If Guy later says no, Phase 4 drops
  0008 and owns that rebuild plus `gate_f2.py --only keyblob,symbols,version` and a short our-core smoke.
- **Guy, 2026-11-13, LibreSSL** (its OpenSSL/SSLeay licence reads as GPLv3-incompatible, Phase 4 review 1): "Switch
  to OpenSSL 3". In step 0: `USE_SYSTEM_OPENSSL=ON` against Homebrew's static OpenSSL 3.6.5, pinned in `core/PIN`;
  F2's f1 checks it; static or nothing (risk 11).
- **Main-loop rulings, 2026-11-12/13:** the main loop writes the patches and the script change itself and runs the
  rebuild (review 2's choice); F2 launches with E and waits on `build.exit` plus a matching `build.inputs`; D's
  as-built review is done and D merges before Phase 3 builds, its abi literal fixed in D.

## 12. Interfaces for Phase 4 (H: docs, I: release)

- `Pool(n, app, root, **emulator_kwargs)` with `submit`, `map`, `close`; `LoadWarning`; `SlotTimeout`;
  `LAZ_MAX_INSTANCES`, `LAZ_SLOT_DIR`, `LAZ_SLOT_TIMEOUT`; `<workdir>/slot.txt`; `tools/hold_slot.py`; the default
  cap set by E2's rule (1-4, marked provisional); USING.md: the cap is machine-wide only if every user reads the
  same `LAZ_MAX_INSTANCES` (N8).
- `docs/research/speed-table-e.md`: the numbers the README quotes, each with load and date, test-app rows labelled
  light; the default cap and its rule; the effective option set per core.
- `core/options-lazpy.txt` applied automatically on our core (P8); `azhost --lazpy-profile`; `LAZ_LAZPY_PROFILE`;
  USING.md: `instant_debug_log` flushes the log per guest line (a speed cost on chatty apps).
- `tests/gate_f2.py`'s results: the supply chain of the gated build (no key blob, no ClCertA, no key loading, no
  LibreSSL, OpenSSL as pinned), repeat exactness, the debug-stop frame, cross-core state loading (for STATUS.md).
- ABI 3: `azh_read`, `azh_write`, the `azh_watch` entry type, the watch area (its size from the layout),
  `AZH_E_UNMAPPED`; `emu.memory` with libmgba-py's names; `run(watch=)`, `RunResult.watch`; `GuestMemoryError`
  (for `docs/HOST-API.md` and USING.md).
- **Core supply chain** (review 2 S5): patches 0000-0008 (0007 no default ClCertA, 0008 no key loading, Q6);
  `LAZ_CORE_DROP` in `core/PIN` (the three Nintendo headers and `externals/libressl`, deleted after unpack and
  before the patches); `OPENSSL_VERSION=3.6.5` and `OPENSSL_PREFIX` in `core/PIN` (`LAZ_OPENSSL_PREFIX` overrides
  the prefix; the script refuses another version); `build-core/build.inputs` (format in section 4 step 0 (g));
  `gate_f2.keyblob_findings(build_dir, core, src_root, tree, repo) -> list[str]` (phase-f2.md section 6; the drop
  list and the OpenSSL pins come from `repo/core/PIN`) for `release_check`, which imports it instead of
  re-implementing the windows.
- **Environment** Phase 3 adds: `LAZ_MAX_INSTANCES`, `LAZ_SLOT_DIR`, `LAZ_SLOT_TIMEOUT` (default 3600),
  `LAZ_PNG_LEVEL` (0-9, default 1), `LAZ_LAZPY_PROFILE`, and the build-only `LAZ_OPENSSL_PREFIX`; there is **no**
  `LAZ_LAZPY_CORE` (D took `LAZ_CORE`; Phase 4's R12 drops it).
- **`SlotTimeout`** subclasses `HostTimeout` (so `except HostTimeout` catches it), `.op == "slot"`, `.seconds`, text
  "no libazahar slot free after <s> s: all <cap> are held; see <dir>". Fake workers never take a slot unless asked
  (`WorkerClient(..., slot=True)`).
- **States both ways:** an ABI-3 host loads metas with `abi` 2..3; an ABI-2 host refuses an ABI-3 state
  (`host/state.c:395-396`, `meta.abi > AZH_ABI_VERSION`).
- **What Phase 4 must change because of step 0:** (a) the Corresponding Source of a published core is the tarball
  minus `LAZ_CORE_DROP` plus patches 0000-0008 plus `tools/build-core.sh`, **plus OpenSSL 3.6.5's source** (Apache-2.0;
  Phase 4 pins its tarball URL and sha256 in `core/PIN`, and checks whether Homebrew's formula patches it, in which
  case those patches go with it); P10 option (a)'s re-pack drops the whole list, not only `default_keys.h`. (b)
  NOTICES: OpenSSL's Apache-2.0 licence (and its NOTICE, if any) replaces LibreSSL's entry; R4's link line changes
  (two absolute keg paths instead of `externals/libressl/...`); G3 (LibreSSL) is closed by Guy's ruling. (c) The
  binary is distributed under GPLv3 (Apache-2.0 is GPLv3-compatible, not GPLv2-compatible; Azahar's "or later"
  allows it): README, `core/README.md`, the release notes. (d) The minimum macOS: Homebrew's objects say 15.0
  while we build for 11.0; state 15.0 as the core's minimum, or build OpenSSL from source for 11.0 (risk 11). (e)
  `release_check` reads `build.inputs` and `LAZ_CORE_DROP` as defined here, imports `keyblob_findings`, and drops
  its configure-only check 10 (the binary is built from the stripped tree). (f) If Q6 is reversed, Phase 4 owns
  that rebuild and F2's partial rerun. (g) STATUS/USING: ABI-2 states load under ABI 3, an ABI-2 host refuses
  ABI-3 states, `SlotTimeout` is a `HostTimeout`, our core loads no keys (encrypted titles cannot run on it).
- The release (I) ships `azahar_lazpy_libretro.dylib` from step 0's build that F2 gated (Phase 4's R1 then holds).

## 13. Changes from review 1

One line per finding (`docs/reviews/phase-3-review-1.md`), then Guy's answers and the other inputs.

- B1 (host_paths ignores `LAZ_CORE`): taken by Phase 2 as hold H1; F2 edits no conftest; the session header line
  prints the core and its kind.
- B2 (nice 10 is an increment): Phase 2's worker is "at least 10" (H2); g4 asserts `nice >= 10`; every table row
  records the workers' nice.
- B3 (exit-path grep sees stock artefacts): F2's `batch.sh` greps right after each our-core part into
  `runs/f2/exitpath-ours.txt`, before any stock part runs.
- B4 (gate 4's stock test): G's live tests take `lazpy_core` / `stock_core` explicitly; one pytest run covers m1-m7
  on both cores with 0 skipped; G2 is two parts.
- B5 (`test_mem.c` cannot link): the pure functions live in a new pure `host/watch.c` in `TEST_SRC`, tested by
  `tests/host/test_watch.c`; `test_main.c`/`.h` (one line each) and the `Makefile` are in G's rows.
- S1 (three overlap seams): rule T in section 2 (every rerun after a review is a timed part and queues); G's wait
  bound is 150 min (E2's bounds grew with the 4-instance row) and a timeout ends G's run with a report.
- S2 (E2's our-core rows without P8): E is resumed only after step-f2 merged, with `git merge --no-edit main` in
  its worktree first; every table row records the effective option set.
- S3 (`wall_ms_max`): r1 strips `wall=`, `fps=`, `wall_ms_mean=`; row C6 and hold H4 say `wall_ms_mean`.
- S4 (`png.c` is pure): `azh_png_level()` in `png.c` with `getenv`/`strtol` only; `run.c` writes the `png level=`
  line once per process; `azh_pure.h` is in E1's rows.
- S5 (env read at import): `slot_dir()` and `cap()` read the environment on every call; the live fixture takes its
  real slots first, then sets the private folder and cap with `monkeypatch`.
- S6 (merging main into G mid-step): main is merged into G's worktree only at "G done"; E fixes to files G edits are
  held until step-g merges (section 4 step 5).
- S7 (ABI 3 refuses ABI-2 states): Phase 2 takes the abi range (H3); risk 7 is gone; G adds m7 (an ABI-2 state
  loads under ABI 3) and USING.md says ABI-2 states load.
- S8 (`HostTimeout` text): `SlotTimeout(HostTimeout)` in `_slots.py` with its own message, exported.
- S9 (no C(g) error-count test): the row is dropped; D's debug-text test is named (`test_c4_debug_text_needs_our_core`).
- N1 (F2-0 already answered): the build-failed branch and the long wait are cut; F2-0 now checks the P9 rebuild
  (key blob absent, version, symbols), since the binary F2 gates is a new one.
- N2 (`azh_stats` after open is a no-op): F2's 3.1 is dropped (H6, row A4).
- N3 (`AZH_MAX_FIELDS` moot): the branch and the 10,292 size are dropped; G asserts 137 rows.
- N4 (Python mirror of `azh__watch_plan`): dropped; Python checks types and the 32-entry count only.
- N5 (`--extra-rows` and a hanging barrier): the usage line names `--extra-rows` and `--only-extra`; the barrier has
  a timeout and a broken barrier is a `CHECK FAIL slot` row.
- N6 (`t_state` not in the log): `t_state` is defined as D does (H5), measured around b's `Emulator(...)`.
- N7 (three throw-away slot holders): E1 commits `tools/hold_slot.py` (a tool file rather than `python -I -m`,
  which cannot find the package under `-I`); G and the phase-end suite use it; F2 keeps its temporary one.
- N8 (machine-wide only with one cap value): in `_slots`'s docstring and the Phase 4 USING line.
- N9 (30 s close after an exit): the close after a returned `guest_exited` waits 5 s, then D's SIGKILL.
- N10 (m3 checks the event line): listed as refinement R1 in section 5.
- N11 (wrong C1 commit; `azh_watch` is a type): fixed in the header and section 12.
- N12 (a second azhost runner): `gate_f2.py` imports `gate_c.run_azhost` and its summary parsing.
- Guy Q1-Q3, review Q4-Q5: section 11; R2 and R3 in section 5; E's cap rule in phase-e.md section 7.
- Phase 2's holds H1-H7 (D's fixtures, nice, abi range, `wall_ms_mean`, C merged at 7584a8d with `azh_stats`
  after open, D3's 2.5 s state-boot bound): section 6; the steps they replace are dropped.
- P9 (Phase 4): the main loop's rebuild before F2 (section 2, section 4 step 0); F2's first check is the key blob.
- The step items' PLAN.md pointers: named as :296, :311, :317 here; the main loop corrects the item files at the
  move (section 4 step 1).
- Hour-saving pass redone (section 9): about 3.2 h, against revision 0's 3.35 h.

## 14. Changes from review 2

One line per finding of `docs/reviews/phase-3-review-2.md` (all taken as written unless a line says "departure"),
then the rulings.

- B1 (F2 gates a binary with ClCertA; step 0 stale): step 0 "P9b" in section 4 (patch 0007, 0008, `LAZ_CORE_DROP`,
  the script's drop/STAMP/guard/`build.inputs`/atomic install, `core/README.md`; main loop; commit; `--detach`;
  waiter); f1 is `keyblob_findings` with every review-2 check (phase-f2.md 1, 6); section 3's step-0 row; F2's
  review checklist item 0. **Departure (small):** the signature is `keyblob_findings(build_dir, core, src_root, tree,
  repo)`, the drop list read from `repo/core/PIN` rather than passed (review 2 asked for "read from core/PIN, not
  typed"; one argument also gives the inputs to hash).
- B2 (`lazpy_core` falls back to the checkout's `build-core/`): every brief's step 0 links
  `build-core/azahar_lazpy_libretro.dylib` to MAIN's; H1 says the fallback is the checkout's.
- B3 (fake-worker spawns take real slots): `WorkerClient(..., slot=None)`, a slot only for the real worker unless
  `slot=True`; s6 passes `slot=True` with a private `LAZ_SLOT_DIR`; E's checklist item 2.
- S1 (stale facts): header, sections 2, 3, 4 step 0, 6 (F5), 10 rewritten to the state after P9 (e40e59c, 21:09,
  19,145,936 bytes, OFF, 0 `/Users/`) and D at 88cdbe6; "the STAMP holds" removed.
- S2 (r2 without D's `sys/` copy): phase-f2.md r2 step 2 copies a's `sys/` minus `sdmc` and RECORDs the folders;
  `seed()` = `testapp_log.write_control`.
- S3 (the {0, 1} tolerance): R4 in section 5.
- S4 (0008 needs a decision): Q6 in section 11, main-loop default yes, 0008 in step 0; section 12 (f) for a later no.
- S5 (section 12 incomplete): section 12's supply-chain, environment, `SlotTimeout` and states lines.
- S6 (E's rerun line): phase-e.md step 3.
- S7 (G may finish first): section 4 step 6.
- N1 citations: fixed in section 10 and phase-e.md section 2 (`emu_window/libretro_window.cpp:68-71`, the loop
  `citra_libretro.cpp:282-306` ending at `emu_window/libretro_window.cpp:327-331`, `Makefile:42` (D's tree; 41 on main
  today), ClCertA `http_c.cpp:2281-2289`).
- N2: phase-g.md 3.3 says `i` is `run_frames`'s 1-based batch frame.
- N3: `gate_f2.py` exits non-zero when `gate_c.failed` is non-zero too (phase-f2.md 6).
- N4: f1 FAILs on any `/Users/` line.
- N5: f1 FAILs on "ClCertA file missing, using default".
- N6: a core exporting only one of the two memory exports is a hard `AZH_E_CORE` at open (phase-g.md 3.3).
- N7: 0007's and 0008's notice lines; `core/README.md` rows; no version bump (`-lazpy.1`, `LAZPY_REV=1`).
- N8: atomic install in step 0 (i).
- N9: `--ignore=tests/python/test_pool_live.py` in the phase-end per-core pytests (section 4 step 7).
- N10: "never run `tools/build-core.sh`" in section 3 and in the three briefs.
- Hours: E 1.11, F2 0.78, G 0.85, loops 0.5 = 3.24 h; main loop 0.4 h (review 2 said 0.35; +0.05 for the OpenSSL
  switch). Section 9 takes review 2's rows and adds this revision's.
- **Departure (small, hour-saving):** step 0's pre-commit check is `tools/build-core.sh --configure-only` in MAIN
  instead of a scratch unpack outside `dl/`: it runs the real edited script (OpenSSL pin, drop, patches with `--fuzz
  0`, the configure guards) on the tree the build will use; the checks review 2 listed (0 rejects, `ctr_common_1`
  count 0) are run on that tree.
- **Addition:** `externals/libressl` joins the drop list, so the bundled LibreSSL cannot be configured by mistake;
  the `.o.d` guard covers it, and step 0 (d) removes the old LibreSSL objects from the build folder first.
- **Additions (small):** the OpenSSL version guard reads the cache's `FIND_PACKAGE_MESSAGE_DETAILS_OpenSSL` line, not
  `configure.log` (CMake prints "Found OpenSSL" only once); `build.inputs`'s `cmake=` line writes `$ROOT` as
  `<repo>` (no user name); `keyblob_records` beside `keyblob_findings` for the RECORD lines.
- Guy's OpenSSL ruling: section 2 (step 0 paragraph), section 4 step 0 (a), (e)-(i), `core/PIN`'s pins, f1's
  OpenSSL checks (phase-f2.md 1, 6), risk 11, facts, section 12 (a)-(d).
- Q6 default yes: 0008 in step 0. The main loop writes and runs step 0; F2 launches with E and waits on
  `build.exit` plus a matching `build.inputs` (section 2, phase-f2.md section 7).
- D's as-built review (S1-S6): H5 (the bound inline in `test_state_boot`), D9 (abi test built from the constant; G's
  `test_state.py` row dropped), the expected baselines (49 / 69), and the moved line numbers noted in section 6.
