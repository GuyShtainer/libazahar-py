# Step K: core revision 2 (3DPlatinum's tick seed and thread registers), plan revision 0

Written 2026-11-13 by the main loop (opus) for item laz-510 (phase laz-500). Two opus reviews before any code; their
files go to docs/reviews/phase-k-review-1.md and -2.md. The asks are quoted verbatim in item laz-500's notes.

## 1. Goal

One core rebuild, `2126.2-lazpy.2`, that gives 3DPlatinum:
- **A4 (wanted):** the tick seed `init_ticks_override` as a core option, so `citra_init_ticks_type=Fixed` plus
  `citra_init_ticks_override=1000` matches its old windowed profile's pin (its count lines then match).
- **A1 (low priority):** pc, lr and sp of every guest thread, read between batches, to replace its gdb aid.

and carries what was queued for the next core revision: the dylib's minimum macOS header says 15.0 (the core needs 15:
its OpenSSL is built for 15), patch 0008's stale comment, and core/PIN-nokeys as the default pin (the release audit's
remediation 6; R1 itself still waits on Guy).

## 2. Where the work happens (the release must not move)

- v0.1.0 is staged from main with core lazpy.1 and is waiting on Guy. Main's `build-core/` dylib is what the staged
  zip packs and what Gen3D and 3DPlatinum read through `LAZ_CORE`. It must not change. So:
- Branch `core-rev2` from main, worktree `../libazahar-py-k` (check `git worktree list` and a case-insensitive name
  clash first). Its `dl/` is a **real folder**, not links: copy MAIN's `dl/azahar-src/src.tar.xz` and the staged
  `runs/release/v0.1.0/azahar-unified-source-2126.2-lazpy-nokeys.tar.xz` (as `dl/azahar-src/src-nokeys.tar.xz`) in,
  and link only the read-only parts the host needs (`moltenvk`, `libretro-headers`, `vulkan-headers`, `azahar`). The
  rule "never run build-core.sh in a worktree" exists because a linked `dl/azahar-src` makes the script delete MAIN's
  build tree; with a real `dl/azahar-src` it is safe. Step 0 checks `[ ! -L dl/azahar-src ]` before any build.
- A full build (fresh tree, LTO) runs `nice`d with `--detach`. The main loop does the work itself (no builder agent).
- The branch merges into main **after v0.1.0 is tagged** (then it becomes the next release with its own narrow
  legal re-audit of the diff), unless Guy rules otherwise. 3DPlatinum may test from the worktree's core by path.

## 3. A4: the tick seed option

- Patch 0002 (`core/patches/0002-lazpy-options.patch`) gains a seventh option, `citra_init_ticks_override`, declared
  like `citra_init_time` (a few listed values: `0` default, `1000`), fetched as text and parsed with `std::stoll`
  (non-digits or overflow fall back to 0), set into `Settings::values.init_ticks_override`. The comment at its line 136
  goes. Azahar reads it in `core_timing.cpp:39` only when `init_ticks_type` is Fixed.
- `host/options.c:120` accepts any decimal for `citra_init_time` only; the same rule extends to
  `citra_init_ticks_override` (digits only; a leading minus refused: the 3DS tick is unsigned in practice).
- `core/options-lazpy.txt` keeps its lines; `citra_init_ticks_override=0` is not added (default equals stock).
- docs: USING.md's option section, core/README.md's patch table row for 0002 ("seven core options").

## 4. A1: thread registers

- New core patch `0009-lazpy-thread-regs.patch` exporting
  `extern "C" int lazpy_threads(lazpy_thread* out, uint32_t max, uint32_t* count)`: for every core id below
  `GetNumCores()`, every thread in `Kernel().GetThreadManager(core).GetThreadList()`: thread id, owner process id,
  status, core id, priority, and pc, lr, sp. For a thread that is the current thread of its core the registers come
  from `GetCore(core)` (the live CPU), else from the thread's saved `context` (`arm_interface.h:32-46`). Returns 0, -1
  not running, -3 bad arguments; `*count` is the total even when it exceeds `max` (the caller retries larger). Call only
  between frames, like the memory exports. The struct is plain C, little-endian u32 fields, fixed size (32 bytes).
- Host: `int azh_threads(azh_thread *out, int32_t max, int32_t *count)` in `host/mem.c` (dlsym'd beside the memory
  exports; a core with the memory exports but not this one gives AZH_E_NEEDS_LAZPY_CORE with "core lacks
  lazpy_threads (lazpy.1)"); `AZH_ABI_VERSION` 3 -> 4 with the layout table row; `azhost threads` prints one line per
  thread. The state ABI is untouched (states keep loading across 3 and 4).
- Python: `emu.threads() -> tuple[ThreadInfo, ...]` (`tid, pid, status, core, priority, pc, lr, sp`, plus a
  `status_name`), `NeedsLazpyCore` on the stock core and on a lazpy.1 core. `_abi.py` mirrors ABI 4.

## 5. The queued items

- `tools/build-core.sh`: `MACOSX_DEPLOYMENT_TARGET=15.0`; `LAZ_CORE_PIN` default `core/PIN-nokeys`. core/PIN stays for
  the route from Azahar's own tarball. Both pins `LAZPY_REV=2`; patch 0005's suffix `-lazpy.2` (or read from the pin).
- Patch 0008's comment names `sysdata/keys.txt` (Azahar's real file), not `aes_keys.txt` (item 400's notes, line 114).
- `tools/fetch.sh` names the lazpy.2 zip; its pin stays TBD on the branch until the next release stages it.
- STATUS.md (the macOS header line moves out of Known limits), README, USING.md, core/README.md.

## 6. Gates (all headless, on this Mac, pass/fail)

1. **Build:** `tools/build-core.sh --detach` in the worktree, exit 0; `build.inputs` names PIN-nokeys and every patch
   0000-0009 by sha; `otool -l` shows minos 15.0; the version string ends `-lazpy.2`; release_check's key-material
   check on the new dylib finds nothing (`python3 -I tools/release_check.py` check 2 run on the worktree's dylib).
2. **No regression:** the full pytest in the worktree with `LAZ_CORE=<worktree>/build-core/...` and
   `LAZ_STOCK_CORE=MAIN/dl/azahar/azahar_libretro.dylib`, `LAZ_REQUIRE_EMULATOR=1`: everything passes, the
   two-core tests included (exact repeats, states across cores, lazpy.1 states loading into lazpy.2).
3. **A4:** a live test boots the test app twice with `citra_init_ticks_type=Fixed` and overrides 0 and 1000000 and
   reads the kernel shared page's tick field (the shared page at 0x1FF81000 is mapped in every process; the builder
   finds the u64 tick in its date-time block and names the offset with a source line); the two values differ by
   1000000 within the frames run. A third boot with `Random` differs from both. Option refusals: `-5` and `1x` give
   ArgumentError.
4. **A1:** a live test after `run(300)` on the test app: at least one thread of the app's process; its main thread's
   pc lies in the test app's .text (from `nm`/`otool` on build/testapp.elf, or the 3dsx header), sp in the stack
   region, lr nonzero; two calls with no run between give equal tuples; the stock core raises NeedsLazpyCore.
5. **3DPlatinum's repros**, run by 3DPlatinum on its side: A4 count lines equal to the windowed route; A1 compared
   with where.py. The main loop asks, then records its answer verbatim.
6. docs_check PASS, status checks, map checks; the fast pytest in MAIN still passes against the branch's Python.

## 7. Hours (estimate) and order

0 worktree and dl seeding 0.1 h; A4 patch and host 0.3 h; A1 patch, host, ABI, Python 1.2 h; queued items 0.2 h;
one full core build (machine time 30-60 min, nice'd, overlapping docs work); gates 0.5 h; docs 0.3 h. About 2.6 h of
work. Order: A4 and A1 patches first, so one build carries both; a configure-only run first catches patch-apply errors.

## 8. Risks

- A full LTO build at high load can take over an hour; it runs detached and is not timed (rule T does not apply).
- `GetThreadList()` of a core that runs no app threads is empty; system-module threads may be listed under other
  process ids: the API reports all, and the doc says to filter by `pid`.
- Reading the live CPU registers is only valid between frames (the host already calls exports only then).
- PIN-nokeys as default fetches from the v0.1.0 release URL: a fresh clone's default build works only after v0.1.0 is
  published; the branch merges after that, so main never points at a missing asset.
