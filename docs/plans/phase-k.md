# Step K: core revision 2 (3DPlatinum's tick seed and thread registers), plan revision 1

Written 2026-11-13 by the main loop (opus) for item laz-510 (phase laz-500). Revision 1 answers every finding of
`docs/reviews/phase-k-review-1.md` (tags in brackets, e.g. [B1]); review 2 goes to docs/reviews/phase-k-review-2.md.
The asks are quoted verbatim in item laz-500's notes.

## 1. Goal

One core rebuild, `2126.2-lazpy.2`, that gives 3DPlatinum:
- **A4 (wanted):** the tick seed `init_ticks_override` as a core option, so `citra_init_ticks_type=Fixed` plus
  `citra_init_ticks_override=1000` matches its old windowed profile's pin (its count lines then match).
- **A1 (low priority):** pc, lr, sp and cpsr of every guest thread, read between batches, to replace its gdb aid.

and carries what was queued for the next core revision: the dylib's minimum macOS header says 15.0, patch 0008's
stale comment, and core/PIN-nokeys as the default pin (the release audit's remediation 6; R1 itself still waits on
Guy).

## 2. Where the work happens (the release must not move)

- v0.1.0 is staged from main with core lazpy.1 and waits on Guy. Main's `build-core/` dylib is what the staged zip
  packs and what Gen3D and 3DPlatinum read through `LAZ_CORE`. It must not change.
- Branch `core-rev2` from main, worktree `../libazahar-py-k` (check `git worktree list` and a case-insensitive name
  clash first). Seeding its `dl/` [S6, B2]:
  - `dl/` and `dl/azahar-src/` are **real folders** made with mkdir.
  - `dl/azahar-src/src-nokeys.tar.xz` is a link to the staged
    `runs/release/v0.1.0/azahar-unified-source-2126.2-lazpy-nokeys.tar.xz` (the script deletes a tarball only if it
    downloaded it itself). `src.tar.xz` is not linked: only mkrelease reads it, and mkrelease does not run here.
  - `dl/azahar-src/unpacked` is a link to MAIN's (read-only use: the window check reads it; the script never deletes
    it).
  - `dl/moltenvk`, `dl/libretro-headers`, `dl/vulkan-headers`, `dl/azahar` are links to MAIN's (read-only).
  - `build/testapp.3dsx` and `build/testapp.elf` are copied from MAIN (the pinned app sha stays).
  - openssl-src, sysarch-src and the licence folders are not needed (they feed mkrelease and release_check only).
- Safety checks before the build, all must hold or nothing runs:
  `for d in dl dl/azahar-src build-core; do [ ! -L "$d" ] && [ "$(cd -P "$d" && pwd)" = "$(pwd -P)/$d" ]; done`
  (build-core is created first with mkdir), and `dl/azahar-src/build-src` does not exist or is not a link.
- The build runs as `env -u LAZPY_ROOT nice tools/build-core.sh --detach` from the worktree, so `ROOT` is the
  worktree even if `LAZPY_ROOT` is exported [S6]. The main loop does the work itself (no builder agent).
- Everything is **committed on the branch before the build** so `build.inputs` says `clean=yes` [S7].
- The branch merges into main **after v0.1.0 is tagged** (then it becomes the next release with its own narrow legal
  re-audit of the diff), unless Guy rules otherwise. 3DPlatinum tests from the worktree: its core, host **and**
  Python (MAIN's host refuses a lazpy.2 core) [S9].

## 3. A4: the tick seed option

- Patch 0002 gains a seventh option, `citra_init_ticks_override`, declared like `citra_init_time` (listed values
  `0` default and `1000`), fetched as text and parsed strictly [S1]: a leading digit, `std::stoull` with
  `pos == size()`, value at most 4294967295, then `static_cast<s64>`; anything else logs one line and keeps 0. Set into
  `Settings::values.init_ticks_override`. The stale comment in 0002 goes. Azahar reads it in `core_timing.cpp:39` only
  when `init_ticks_type` is Fixed; it takes effect at the next boot (options are parsed before `System::Init`).
- `host/options.c:120`: the free-decimal rule extends to `citra_init_ticks_override`: digits only, no sign, at most
  10 digits and at most 4294967295 [S1]; else AZH_E_ARG (Python: ArgumentError).
- `core/options-lazpy.txt` is unchanged (the default equals stock).
- docs (USING.md's option section): the override also shifts the guest clock by base/268 MHz (the system time is
  computed from global ticks), a played movie overrides it, and a loaded state keeps its own ticks [S2].

## 4. A1: thread registers

- Core: new patch `0009-lazpy-thread-regs.patch`:
  - `extern "C" int lazpy_threads(lazpy_thread* out, uint32_t max, uint32_t* count)`, plus its line in
    `src/citra_libretro/libretro.osx.def` [B3].
  - For each core id below `GetNumCores()` (4 on the New 3DS profile), every thread in
    `Kernel().GetThreadManager(core).GetThreadList()`.
  - Each record holds: tid, pid (0xFFFFFFFF when `owner_process.lock()` is empty), status (raw `ThreadStatus`), core
    id (the manager's), priority, flags (bit 0: current thread of its core), pc, lr, sp, cpsr [N3]. The struct is
    plain C, little-endian u32 fields, 40 bytes, with a static_assert on the size.
  - A core's current thread is read from the live CPU (`GetCore(core)`, the accessors at `arm_interface.h:32-52`);
    every other thread from its saved `context` (registers at `:54-58`) [N5].
  - Returns 0, -1 not running, -3 bad arguments; `*count` is the total even when it exceeds `max` (the caller retries
    larger). Called only between frames, like the memory exports.
- Host [S4]:
  - `int azh_threads(azh_thread *out, int32_t max, int32_t *count)` in `host/mem.c`, public in `host/api.c`, listed in
    `host/libazhost.exports`.
  - `azh__mem_bind` binds `lazpy_threads` separately and as optional: a core with the memory exports and without it
    is a lazpy.1 core, not a half-exported one. Calling `azh_threads` there gives AZH_E_NEEDS_LAZPY_CORE with "core
    lacks lazpy_threads (lazpy.1)".
  - The status names (`ThreadStatus`, thread.h:50-61) are mapped in the host by value, not by order [N3].
  - `AZH_ABI_VERSION` 3 -> 4 for the layout table (new `azh_thread` rows and size); a new `AZH_STATE_META_ABI` stays 3
    and is what `state.c:286` writes and `:396` checks, so states stay loadable by v0.1.0's host both ways [S3].
    Tests: test_memory.py:181-184 moves to abi 4 and the new field count; test_memory_live.py:239-240 keeps "abi=3".
  - No azhost CLI command (hour-saving: 3DPlatinum uses Python; `azhost layout` prints the new rows anyway).
- Python [S4]: a `"threads"` op in `_worker.py`, the signature in `_host.py`, the client method,
  `emu.threads() -> tuple[ThreadInfo, ...]` (`tid, pid, status, status_name, core, priority, is_current, pc, lr, sp,
  cpsr`), `_abi.py` mirrors ABI 4. NeedsLazpyCore on the stock core and on a lazpy.1 core.

## 5. The version pin and the queued items

- Host accepts either core [B1]: `host/pins.h` holds the list `{"-lazpy.1", "-lazpy.2"}`; `version.c` matches any
  entry. Update tests/test_version.c:20-22, tests/gate_f2.py:153 and :311, and the core.c:74 message. A lazpy.1 core
  still runs everything but `threads()`.
- `tools/build-core.sh`:
  - `-DCMAKE_OSX_DEPLOYMENT_TARGET=15.0` on the cmake line (:111), plus `MACOSX_DEPLOYMENT_TARGET=15.0` in the
    environment; after configure, grep the cache for `CMAKE_OSX_DEPLOYMENT_TARGET:STRING=15.0` [S5].
  - `LAZ_CORE_PIN` default `core/PIN-nokeys`; core/PIN stays for the route from Azahar's own tarball.
  - An assert that patch 0005's suffix equals `-lazpy.$LAZPY_REV` of the chosen pin [N2].
- Both pins `LAZPY_REV=2`; patch 0005's suffix `-lazpy.2`; the PIN-nokeys header comment (:4) updated [S9].
- Patch 0008's own notice line (0008:7) names `sysdata/keys.txt`, not `aes_keys.txt` [N1].
- Patch 0000's notice lines: `lazpy_threads` and the .def line, "six" -> "seven" options (0000:17), `-lazpy.1` ->
  `-lazpy.2` (0000:27) [S9].
- `tools/gate_f2.py`: `_inputs_findings` accepts either pin, chosen by the `pin=` sha in build.inputs, and takes that
  pin's tarball sha and drop list [B2]; `LAZPY_EXTRA` (:238) and `tools/release_check.py:44` `EXPORT_EXTRA` gain
  `lazpy_threads` [B3].
- `tools/fetch.sh` is **unchanged** on the branch (v0.1.0, lazpy.1): the core and the test app share its tag, and the
  lazpy.1 core still loads [S8]. It moves when the next release is staged.
- Docs: NOTICES.md regenerated (`tools/mknotices.py`), core/README.md (:10 `LAZPY_REV`, :19, :22, :25, a 0009 row),
  STATUS.md (:46, :83; the macOS header line leaves Known limits), README, USING.md [S9].

## 6. Gates (all headless, on this Mac, pass/fail)

1. **Build:** the build exits 0; `build.inputs` says `clean=yes`, names PIN-nokeys and patches 0000-0009 by sha;
   `otool -l` shows minos 15.0 and the cache says 15.0; the version string ends `-lazpy.2`; `nm -gU` lists
   `_lazpy_threads`. Key material: `gate_f2.keyblob_findings(<wt>/build-core, ...)` called directly finds nothing,
   and `gate_f2._inputs_findings` passes with PIN-nokeys [B2].
2. **No regression:** the full pytest in the worktree with `LAZ_CORE=<wt>/build-core/azahar_lazpy_libretro.dylib`,
   `LAZ_STOCK_CORE=<MAIN>/dl/azahar/azahar_libretro.dylib` and `LAZ_REQUIRE_EMULATOR=1`: all pass. Extra two-core
   tests with `LAZ_CORE_OLD=<MAIN>/build-core/...`: a state saved under lazpy.1 loads into lazpy.2; a state saved by
   the branch host has `abi=3` in its meta; the lazpy.1 core boots under the branch host and its `threads()` raises
   NeedsLazpyCore.
3. **A4** [S2]: boot the test app with `citra_init_ticks_type=Fixed` and override 0, then 1000000; after 300 frames
   read the u32 at 0x1FF81000 (`date_time_counter`, expect 1) and the u64 at 0x1FF81048 (`date_time_1.update_tick`,
   shared_page.h:35-37 and :72). Pass: v(1000000) - v(0) == 1000000 exactly, and v(0) < 2^20. A `Random` boot gives a
   value different from both. A state saved at frame 300 of the 1000000 boot and loaded into a fresh 0-override boot
   reads the 1000000 value. Refusals: `-5`, `1x`, `4294967296` give ArgumentError.
4. **A1** [N4]: after `run(300)` on the test app: at least one thread whose pid is the app's; its main thread's pc
   lies in the app's .text (`nm` / section headers of build/testapp.elf), sp below 0x10000000 and within the app's
   stack size of the stack top, lr nonzero; exactly one `is_current` thread per core at most; two calls with no run
   between give the same pid/tid set and equal records; the stock core raises NeedsLazpyCore.
5. **3DPlatinum's repros**, run on its side with the worktree's core, host and Python: A4 count lines equal to the
   windowed route; A1 compared with where.py. The main loop asks, then records its answer verbatim.
6. docs_check PASS, status checks, map checks; MAIN's fast pytest still passes.

## 7. Hours (estimate) and order

Order: worktree and seeding (0.1 h); A4 patch and host (0.3 h); A1 patch, host, ABI, Python (1.1 h, the CLI command
cut); pin list, gate code, build script, queued docs (0.4 h); commit; one configure-only run to catch patch-apply
errors; the full build (machine time 30-60 min, nice'd, detached, overlapping the docs work); gates 0.5 h; docs 0.3 h.
About 2.7 h of work.

## 8. Risks

- A full LTO build at high load can take over an hour; it runs detached and is not timed (rule T does not apply).
- `GetThreadList()` of a core with no app threads is empty; system-module threads appear under other pids: the API
  reports all, the doc says to filter by `pid`.
- The live registers are valid only between frames (the host calls exports only then).
- PIN-nokeys as default fetches from the v0.1.0 release URL: a fresh clone's default build works only after v0.1.0 is
  published; the branch merges after that, so main never points at a missing asset.
- Changing the tick option mid-run affects only the next boot or reset; the doc says so.
