# Step K: core revision 2 (3DPlatinum's tick seed and thread registers), plan revision 2

Written 2026-11-13 by the main loop (opus) for item laz-510 (phase laz-500). Revision 1 answered
`docs/reviews/phase-k-review-1.md` (tags like [B1]); revision 2 answers `docs/reviews/phase-k-review-2.md` (tags like
[R2-B1]). The asks are quoted verbatim in item laz-500's notes. Note: the worktree, patches, host and Python edits
started while review 2 ran (uncommitted, in the worktree); they were brought in line with review 2 before any commit
or build.

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
  - `build/testapp.3dsx` and `build/testapp.elf` are copied from MAIN (the pinned app sha stays), and MAIN's
    git-ignored `vendor/` (libretro and Vulkan headers the host Makefile reads) is copied in [R2-B1].
  - `tools/fetch.sh` never runs in the worktree: its `--force` and its sha-mismatch delete would reach MAIN through
    the `dl/` links [R2-B1].
  - openssl-src, sysarch-src and the licence folders are not needed (they feed mkrelease and release_check only).
- Safety checks before the build, all must hold or nothing runs:
  `for d in dl dl/azahar-src build-core; do { [ ! -L "$d" ] && [ "$(cd -P "$d" && pwd)" = "$(pwd -P)/$d" ]; } ||
  { echo "unsafe $d"; exit 1; }; done` (each pass fails on its own [R2-S1]; build-core is created first with mkdir), and
  `dl/azahar-src/build-src` does not exist or is not a link.
- The build runs as `env -u LAZPY_ROOT -u LAZ_CORE_PIN -u LAZ_CORE_PATCHES -u LAZ_OPENSSL_PREFIX tools/build-core.sh
  --detach` from the worktree (the script nices itself), so `ROOT` and the inputs are the worktree's even if any of
  these is exported [S6, R2-S3]. The main loop does the work itself (no builder agent).
- Everything is **committed on the branch before the build** so `build.inputs` says `clean=yes` [S7].
- The progress files (items, docs/hours.tsv, the handoff, plans, reviews) are written on main only; the branch holds
  code, tests and product docs, so the merge does not conflict [R2-N6].
- The branch merges into main **after v0.1.0 is tagged** (then it becomes the next release with its own narrow legal
  re-audit of the diff), unless Guy rules otherwise. After the merge, main's `build-core/` is still lazpy.1 and cannot
  be moved from the worktree (its CMake cache pins absolute paths): one more full build on main (machine time 30-60
  min) comes before main's gates [R2-S5].
- 3DPlatinum tests from the worktree: its core, host **and** Python (MAIN's host refuses a lazpy.2 core), with
  `LAZ_ROOT=<wt>` set explicitly [S9, R2-S3].

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
  - A core's current thread is read from the live CPU through `GetCore(core).SaveContext(tmp)` (arm_interface.h:178,
    no side effects) and then the same `ThreadContext` accessors (:32-52) as every other thread's saved `context`, so
    there is one read path [R2-S7].
  - Returns 0, -1 not running, -3 bad arguments; `*count` is the total even when it exceeds `max` (the caller retries
    larger). Called only between frames, like the memory exports.
- Host [S4]:
  - `int azh_threads(azh_thread *out, int32_t max, int32_t *count)` in `host/mem.c`, public in `host/api.c`, listed in
    `host/libazhost.exports`.
  - `azh__mem_bind` binds `lazpy_threads` separately and as optional: a core with the memory exports and without it
    is a lazpy.1 core, not a half-exported one. Calling `azh_threads` there gives AZH_E_NEEDS_LAZPY_CORE with "core
    lacks lazpy_threads (lazpy.1)".
  - The status names (`ThreadStatus`, thread.h:50-61) are mapped by value in Python (`_abi.THREAD_STATUS_NAMES`);
    the struct carries the raw number [R2-N3].
  - `AZH_ABI_VERSION` 3 -> 4 for the layout table (new `azh_thread` rows and size); a new `AZH_STATE_META_ABI` stays 3
    and is what `state.c:286` writes and `:396` checks, so states stay loadable by v0.1.0's host both ways [S3].
    Tests: test_memory.py:181-184 moves to abi 4 and 150 fields; test_memory_live.py:239-240 keeps "abi=3";
    test_state.py:114-116 uses `_abi.AZH_STATE_META_ABI` (a new const row); test_abi.py:38 uses abi 3 as the wrong
    one; `thread` joins `_abi._STRUCTS` [R2-B2]. Review 2's H1 (skip the bump) was weighed: the edits were already
    made and pass, and the abi number tells a reader which host has `azh_threads`, so the bump stays.
  - No azhost CLI command (hour-saving: 3DPlatinum uses Python; `azhost layout` prints the new rows anyway).
- Python [S4]: `_host.load` turns a missing host function (an older libazhost) into HostError("host lacks azh_threads
  ...") rather than AttributeError [R2-S6]; a `"threads"` op in `_worker.py`, the signature in `_host.py`, the client method,
  `emu.threads() -> tuple[ThreadInfo, ...]` (`tid, pid, status, status_name, core, priority, is_current, pc, lr, sp,
  cpsr`), `_abi.py` mirrors ABI 4. NeedsLazpyCore on the stock core and on a lazpy.1 core.

## 5. The version pin and the queued items

- Host accepts either core [B1]: `host/pins.h` holds the list `{"-lazpy.1", "-lazpy.2"}`; `version.c` matches any
  entry. Update tests/test_version.c:20-22, tests/gate_f2.py:153 and :311, and the core.c:74 message. A lazpy.1 core
  still runs everything but `threads()`.
- `tools/build-core.sh`:
  - `-DCMAKE_OSX_DEPLOYMENT_TARGET=15.0` on the cmake line (:111), plus `MACOSX_DEPLOYMENT_TARGET=15.0` in the
    script's own export (:15, which overrides the outer environment); after configure, grep the cache for
    `^CMAKE_OSX_DEPLOYMENT_TARGET:[A-Z]*=15.0$` [S5, R2-S4].
  - `LAZ_CORE_PIN` default `core/PIN-nokeys`; core/PIN stays for the route from Azahar's own tarball.
  - An assert that patch 0005's suffix equals `-lazpy.$LAZPY_REV` of the chosen pin [N2].
- Both pins `LAZPY_REV=2`; patch 0005's suffix `-lazpy.2`; the PIN-nokeys header comment (:4) updated [S9].
- Patch 0008's own notice line (0008:7) names `sysdata/keys.txt`, not `aes_keys.txt` [N1].
- Patch 0000's notice lines: `lazpy_threads` and the .def line, "six" -> "seven" options (0000:17), `-lazpy.1` ->
  `-lazpy.2` (0000:27) [S9].
- `tests/gate_f2.py`: `_inputs_findings` accepts either pin, chosen by the `pin=` sha in build.inputs, and takes that
  pin's tarball sha and drop list [B2]; `keyblob_findings` keeps core/PIN's drop list (the three key headers and
  libressl) for its tree and `.o.d` checks, so the check is not weakened; the strings check's `-lazpy.N` comes from the
  pin's `LAZPY_REV` [R2-S2]; the :526 comment is corrected [R2-N5]; `LAZPY_EXTRA` (:238) and `tools/release_check.py:44` `EXPORT_EXTRA` gain
  `lazpy_threads` [B3].
- `tools/fetch.sh` is **unchanged** on the branch (v0.1.0, lazpy.1): the core and the test app share its tag, and the
  lazpy.1 core still loads [S8]. It moves when the next release is staged.
- Docs: USING.md:218 and :247 (the new `LAZ_CORE_PIN` default) [R2-N5]; NOTICES.md regenerated (`tools/mknotices.py`), core/README.md (:10 `LAZPY_REV`, :19, :22, :25, a 0009 row),
  STATUS.md (:46, :83; the macOS header line leaves Known limits), README, USING.md [S9].

## 6. Gates (all headless, on this Mac, pass/fail)

1. **Build:** the build exits 0; `build.inputs` says `clean=yes`, names PIN-nokeys and patches 0000-0009 by sha;
   `otool -l` shows minos 15.0 and the cache says 15.0; the version string ends `-lazpy.2`; `nm -gU` lists
   `_lazpy_threads`. Key material: `gate_f2.keyblob_findings(<wt>/build-core, ...)` called directly finds nothing,
   and `gate_f2._inputs_findings` passes with PIN-nokeys [B2].
2. **No regression:** the full pytest in the worktree, with `LAZ_ROOT`, `LAZ_HOST`, `LAZ_PROFILE` and
   `LAZ_LAZPY_PROFILE` unset [R2-S3], and with `LAZ_CORE=<wt>/build-core/azahar_lazpy_libretro.dylib`,
   `LAZ_STOCK_CORE=<MAIN>/dl/azahar/azahar_libretro.dylib` and `LAZ_REQUIRE_EMULATOR=1`: all pass. Extra two-core
   tests with `LAZ_CORE_OLD=<MAIN>/build-core/...`: a state saved under lazpy.1 loads into lazpy.2; a state saved by
   the branch host has `abi=3` in its meta; a state saved under lazpy.2 loads into lazpy.1 (the reverse) [R2-N4]; the
   lazpy.1 core boots under the branch host and its `threads()` raises NeedsLazpyCore.
3. **A4** [S2]: boot the test app with `citra_init_ticks_type=Fixed` and override 0, then 1000000; after 300 frames
   read the u32 at 0x1FF81000 (`date_time_counter`, expect 1) and the u64 at 0x1FF81048 (`date_time_1.update_tick`,
   src/core/hle/kernel/shared_page.h:35 and :75) [R2-N1]. Review 2 checked that v(0) is exactly 0. Pass: v(1000000) - v(0) == 1000000 exactly, and v(0) < 2^20. A `Random` boot gives a
   value different from both. A state saved at frame 300 of the 1000000 boot and loaded into a fresh 0-override boot
   reads the 1000000 value. Refusals: `-5`, `1x`, `4294967296` give ArgumentError.
4. **A1** [N4, R2-B3]: after `run(300)` on the test app: at least one thread whose pid is the app's; its main thread
   (the lowest tid with the app's pid) has pc in the app's .text and lr nonzero; sp within libctru's stack:
   `top - __stacksize__ <= sp <= top`, where `top` is the u32 read at `&fake_heap_start` and both symbols come from
   `nm build/testapp.elf` (libctru moves sp into the heap; the loader's stack below 0x10000000 is abandoned); exactly one `is_current` thread per core at most; two calls with no run
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
