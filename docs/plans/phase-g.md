# Step G: reading and writing the game's memory, and the watch list (item laz-330)

Brief for one sonnet builder, revision 0 (2026-11-12). Phase index: `docs/plans/phase-3.md` (order, ownership,
merges, departures, interfaces). Contract: `docs/PLAN.md:317` ("Phase G"), sections 2.2 (`azh_read`/`azh_write`, the
watch list) and 2.5 (`emu.memory`, libmgba-py's names). Where this brief disagrees with PLAN.md on a goal, PLAN.md
wins: stop and report (except the approved departures P1-P8 of phase-3.md section 5 and phase-2.md section 5, which
you follow; P7 is this step's).

You work in `../libazahar-py-g` (branch `step-g`, made at main **after step F2 merged**, with step E's E1 commit
merged in; phase-3.md section 2). "MAIN" is `/Users/guyshtainer/VSCodeProjects/3ds-toolkit/projects/libazahar-py`.
"OURS" is `MAIN/build-core/azahar_lazpy_libretro.dylib` (absolute; read only); "STOCK" is
`dl/azahar/azahar_libretro.dylib`. **Never commit, never edit item files, never write in MAIN.** Read first: the
repo's `CLAUDE.md`, `docs/map/rules.md`, phase-3.md sections 2, 3, 5, 6, phase-c.md section 3 (the frozen ABI 2
you extend), phase-d.md section 4, `core/patches/0001-lazpy-memory-exports.patch`, `testapp/source/main.c`,
`record.h`, `control.h`, `~/.claude/c-golden-rules.md` and `~/.claude/python-golden-rules.md`.

## 1. Goal and gate

Memory reads and writes by guest virtual address through our core's two exports, a per-frame watch list whose rows
land in the map, typed errors, and the stock core refusing all of it. The gate (headless, this Mac):

1. `make check && make && make test-host` clean (with `tests/host/test_mem.c`); `build/azhost layout` prints
   `abi=3` and the new rows; `python3 -m pytest -q tests/python -m "not slow"` passes (ABI 3 checked at import).
2. `LAZ_CORE=OURS LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python/test_memory_live.py -k
   "not stock"` passes, 0 skipped:
   - **m1** for 600 frames, `read` calls of both records (global and heap, the addresses the `start` line logs) give
     the logged values of their own `frame`: magic, frame, vblank, keys, tx, ty, cx, cy and tick (= `s=`);
   - **m2** one `run(600, watch=[(global, 8), (heap, 8)])` gives 600 rows that pass the same check, and a
     `watch_every=10` batch gives exactly 60 rows;
   - **m3** a write of the control struct's `ready_at` makes the next event line the app logs `ready f=<written>`;
   - **m4** a read straddling the end of a mapped region and a fully unmapped read (and address 0) raise
     `GuestMemoryError`; the in-range part reads fine; a straddling write raises and changes nothing;
3. `LAZ_CORE=STOCK LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python/test_memory_live.py -k
   stock` passes, 0 skipped: **m5** every memory call and a `run(..., watch=...)` raise `NeedsLazpyCore`, and the
   Emulator then runs on.
4. Regression on OURS: `python3 -I tests/gate_c.py --core OURS` passes; `LAZ_CORE=OURS LAZ_REQUIRE_EMULATOR=1 python3
   -m pytest -q -rs tests/python --ignore=tests/python/test_pool_live.py` passes 0 skipped (D's, F2's, E's non-live
   and G's tests; E's live pool test runs 3 instances and belongs to E's gate and the phase-end suite).

Torn reads: a record whose fields do not all match line `frame` but each match line `frame` or `frame - 1` is
**torn** (section 2); m1 and m2 print the counts and fail above 1 % per address. Any other mismatch fails.

## 2. Facts (checked; SRC = `MAIN/dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/`, PATCHES = `core/patches/`)

- PATCHES 0001: `extern "C" int lazpy_read_memory(uint32_t vaddr, void *buf, uint32_t len)` and
  `lazpy_write_memory(uint32_t vaddr, const void *buf, uint32_t len)` (note: **address, buffer, length**; A's
  `azh_read(addr, len, buf)` has the length second). Returns 0 ok; -1 not powered on or no current process (or a
  caught exception); -2 a page in the range is unmapped; -3 bad arguments (NULL buffer, len 0, len > 0x4000000, or
  `vaddr + len > 2^32`). Every page of the range is checked with `IsValidVirtualAddress` **before** any byte moves,
  so a failed write changes nothing. Both are in the `.def`, so `dlsym` finds them (step F2's f2).
- `ReadBlock` alone would zero-fill unmapped pages and `WriteBlock` skip them (SRC core/memory.cpp:176-215,
  247-253), which is why the exports check first. `IsValidVirtualAddress` is a page pointer or a non-Unmapped
  attribute (memory.cpp:824-837); pages are 0x1000 (memory.h:34).
- `ReadBlock` flushes the GPU cache for rasterizer-cached pages (VRAM, linear heap; memory.cpp:213-); `retro_run`
  registers the calling thread as the core-loop thread (SRC citra_libretro/citra_libretro.cpp:284). The worker has
  one thread that makes every `azh_*` call, so reads and writes run on the core-loop thread, between frames, as the
  patch requires.
- A's detection: `dlsym(core, "lazpy_read_memory")` at `azh_open` sets `is_lazpy_core` (phase-a "3. The API"). Bind
  both exports at the same place.
- `retro_run` returns after the slice in which the VBlank fired (citra_libretro.cpp:286-306; `MAX_SLICE_LENGTH`
  clock / 234, core/core_timing.h:184), so when a batch returns the guest may be part-way into its next frame. The
  app's per-frame order is `hidScanInput`, `record_fill(&g_record)`, `memcpy` to the heap copy, then the log line
  (testapp/source/main.c:137-156): a read can land inside `record_fill` (torn) or between the global and the heap
  copy (the heap one frame behind). Hence section 1's torn rule.
- The record: `laz_record` 32 bytes, magic 0x4C415A52 at 0, frame 4, vblank 8, keys 12 (u32), tx 16, ty 18 (u16), cx
  20, cy 22 (i16), tick 24 (u64) (testapp/source/record.h:14-21). The log line `f= v= s= t= k= tx= ty= td= cx= cy=`
  is formatted from `g_record` (record.c:58-61; `td` is bit 20 of `k`). `start addr_global=0x%08lx
  addr_heap=0x%08lx` gives both addresses (record.c:44-46).
- A host write into the record is overwritten next frame and never reaches a log line (main.c:150-155). The control
  struct is read every frame: `static laz_control g_ctl` (main.c:23) with `int mode3d` at 0, u32 `break_at` 4,
  `exit_at` 8, `ready_at` 12, `boot_frames` 16 (control.h:11-19); `run_events` logs `ready f=` when `g_ctl.ready_at
  == f` (main.c:159-170). `ready_at` and `exit_at` accept 1..1,000,000 (phase-b). `g_ctl` and `g_record` are both
  file statics in main.c, so they sit in the app's `.data`/`.bss`, a few KiB apart.
- 3DS user address 0 is unmapped (the app image starts at 0x00100000).
- The map after C: 695,296 bytes, version 2, bytes 1108-4095 free (phase-c 3.3). The next page boundary is 696,320
  (170 x 4096). An `ftruncate`d file's untouched pages take no disk on APFS and no memory until touched.
- libmgba-py's memory names, which Gen3D's code already uses: `core.memory.u32.raw_read(addr)`,
  `core.memory.u8.raw_read(addr)` (gba-toolkit-share `tools/vsd_run.py`); PLAN 2.5 writes `emu.memory.u32(addr)`
  and `emu.memory.read(addr, 64)`.

## 3. ABI 3 (`host/azhost.h`, `azh_internal.h`, `azh_pure.h`; appended only, nothing renamed or moved)

### 3.1 Header additions

```c
#define AZH_ABI_VERSION 3                       /* was 2 */
AZH_E_UNMAPPED = -11,                           /* added to the error enum (P7): a guest page in the range is unmapped */
#define AZH_MEM_MAX_LEN 0x4000000u              /* the core's cap (patch 0001) */
#define AZH_MAX_WATCH 32                        /* entries per batch */
#define AZH_WATCH_MAX_WORDS 256                 /* u32 words per entry */
#define AZH_WATCH_EVERY_MAX 100000
#define AZH_WATCH_AREA_OFF 696320               /* page-aligned, right after the pixels */
#define AZH_WATCH_AREA_BYTES 4194304            /* header + rows */
#define AZH_WATCH_HDR_BYTES 64
#define AZH_WATCH_ROW_HDR 16
typedef struct { uint32_t addr, words; } azh_watch;
```
- `azh_batch`: append `int32_t n_watch; int32_t watch_every; azh_watch watch[AZH_MAX_WATCH];` (0 entries: no rows,
  ABI 2 behaviour). Size 3348 -> **3612**.
- `azh_result`: append `int32_t watch_rows; int32_t watch_status;` (rows written; 0, or the first non-zero row
  status). Size 304 -> **312**.
- `azh_stats` unchanged (240). `azh_layout` unchanged (6452) **unless** C1's `fields[]` table plus this step's rows
  exceed `AZH_MAX_FIELDS` (160): then `AZH_MAX_FIELDS` becomes 256 and `azh_layout` 10,292 bytes; count the rows
  first and report which.
- Map version 3, size **4,890,624** (696,320 + 4,194,304). The watch area at 696,320:

| Offset | Type | `fields[]` name | Meaning |
|---|---|---|---|
| +0 | u32 | `map.watch_rows` | rows written in this batch; release store after each row |
| +4 | u32 | `map.watch_row_bytes` | 16 + 4 x total words |
| +8 | u32 | `map.watch_words` | total words per row (the sum of the entries' words) |
| +12 | u32 | `map.watch_seq` | +1 at the start of every batch with watch entries |
| +16 | i64 | `map.watch_first` | the absolute frame before the batch's first frame |
| +64 | rows | `map.watch_data` | row k at +64 + k x row_bytes: i64 absolute frame, i32 status (0 or an `AZH_E_*`), u32 failed entries, then the words of each entry in list order (a failed entry's words are 0) |

`fields[]` gains: `batch.n_watch`, `batch.watch_every`, `batch.watch`, `watch.addr`, `watch.words`,
`watch.__size__`, `result.watch_rows`, `result.watch_status`, the six `map.watch_*` rows, the new `map.__size__`,
and `const.` rows for `AZH_E_UNMAPPED`, `AZH_MEM_MAX_LEN` and every `AZH_WATCH_*`/`AZH_MAX_WATCH` constant. Same
table style as C1 (plain `offsetof`/`sizeof` rows, no macros, C rule 8).

### 3.2 Pure functions (`azh_pure.h`, implemented in `host/mem.c`'s pure half or a new pure `host/watch.c`)

```c
int azh__mem_check(uint32_t addr, uint32_t len, char *err, size_t cap);      /* 0, or AZH_E_ARG with a reason */
int azh__mem_code(int core_rc);              /* 0->0, -1->AZH_E_ORDER, -2->AZH_E_UNMAPPED, -3->AZH_E_ARG, other->AZH_E_CORE */
int azh__watch_plan(const azh_watch *w, int32_t n, int32_t frames, int32_t every,
                    uint32_t *row_bytes, uint32_t *total_words, uint32_t *rows_max, char *err, size_t cap);
```
`azh__mem_check`: len 1..`AZH_MEM_MAX_LEN`; `(uint64_t)addr + len <= 2^32`. `azh__watch_plan`: n 0..32; every 0
means 1, else 1..`AZH_WATCH_EVERY_MAX`; each entry's words 1..256 and `addr + 4 x words <= 2^32`; rows needed =
`frames / every + (frames % every != 0)`; `rows_needed x row_bytes <= AZH_WATCH_AREA_BYTES - AZH_WATCH_HDR_BYTES`,
else `AZH_E_ARG` whose text names the largest `frames` that fits at this `every`. Pure files keep to `<stdint.h>`,
`<string.h>`, `<stdio.h>` (phase-2 convention).

### 3.3 Behaviour

- `azh_read(addr, len, buf)` / `azh_write(addr, len, buf)`: call order as `azh_shot` (after boot; `AZH_E_ORDER`
  before); stock core: `AZH_E_NEEDS_LAZPY_CORE` "memory access needs the libazahar core"; `buf` NULL or
  `azh__mem_check` failing: `AZH_E_ARG`; then the export, its code through `azh__mem_code`; the error text names the
  address and length (`"guest memory 0x%08x+%u: a page is unmapped"`). No host.log line per call (they can be
  frequent); one debug-level line is fine if A's logger has levels.
- `azh_run` with `n_watch > 0`: on the stock core `AZH_E_NEEDS_LAZPY_CORE` before any frame (beside C's debug-text
  check); `azh__watch_plan` failing: `AZH_E_ARG` before any frame. At the batch start (only when `n_watch > 0`):
  `watch_rows = 0`, the row size, the words, `watch_first`, `watch_seq + 1`.
- After each `retro_run`, after C's frame and vblank totals and before the shot and the stops (C's order, phase-c
  3.4): when batch frame `i % every == 0`, write one row: the absolute frame, then for each entry
  `lazpy_read_memory(addr, row_ptr, 4 x words)`; a non-zero code zeroes that entry's words, sets the row status to
  the first mapped code and counts the entry as failed. Then the release store of `watch_rows`. At every batch exit
  that returns 0, if the last frame run has no row yet, write it. `result.watch_rows` and `watch_status` filled.
  An unmapped watch never stops the batch (a game may unmap and remap).
- `host/mem.c` holds the two bound function pointers (file statics; `azh__mem_bind(void *core_handle)` called
  beside A's `is_lazpy_core` detection; both must be found, else our core is treated as stock and one host.log
  line says why), `azh_read`/`azh_write`'s bodies (called from `api.c`), and the row writer
  (`azh__watch_begin`, `azh__watch_row`, `azh__watch_finish`, called from `run.c`). C rules: functions under about
  60 lines, about 2 asserts each, checked returns, bounded loops (entries <= 32, rows <= rows_max).

## 4. The Python side

- `_abi.py`: `Watch` (`addr`, `words` as `c_uint32`), the appended `Batch` and `Result` fields, the new constants,
  the expected abi 3; `check_layout` already checks every `fields[]` row (D), so the new rows are checked too.
- `_map.py`: `WATCH_ROWS = 696320`, `WATCH_ROW_BYTES`, `WATCH_WORDS`, `WATCH_SEQ`, `WATCH_FIRST`, `WATCH_DATA =
  696384`, `SIZE = 4890624`; `HostMap.watch_copy(rows: int) -> list[tuple[int, int, bytes]]` (frame, status, the
  row's words as bytes), reading `watch_rows` first. Copies, never views (phase-3.md section 9).
- `results.py`: `WatchRow(frame: int, status: int, data: tuple[bytes, ...])` (frozen; one `bytes` per watch entry,
  in list order) with `u32(entry: int, word: int = 0) -> int`; `RunResult` appends `watch: tuple[WatchRow, ...] =
  ()`.
- `errors.py`: `GuestMemoryError(LibAzaharError)` with `.addr` and `.length` (None when unknown); `from_code` maps
  `AZH_E_UNMAPPED` to it.
- `_worker.py`: ops `read` (addr, length) -> `("ok", bytes)` (a `ctypes.create_string_buffer`, copied out) and
  `write` (addr, bytes) -> `("ok", None)`; errors as D's other ops.
- `memory.py` (new): `class Memory` made by the Emulator (`emu.memory`, one per Emulator, created on first use):
  - `read(addr: int, length: int) -> bytes` and `write(addr: int, data: bytes | bytearray | memoryview) -> None`;
    Python checks first (`ValueError`): `0 <= addr <= 0xFFFFFFFF`, `1 <= length <= AZH_MEM_MAX_LEN`, `addr +
    length <= 2^32`; a `GuestMemoryError` from the worker gets `.addr` and `.length` set.
  - widths `u8, u16, u32, u64, s8, s16, s32, s64`: small objects that are callable (`emu.memory.u32(addr)`, PLAN
    2.5) and have `raw_read(addr)` and `raw_write(addr, value)` (libmgba-py's names); little-endian `struct`.
  - `write_u8 .. write_u64(addr, value)` (range-checked: `ValueError` outside the width).
  - The docstring says: reads and writes happen between batches; the guest may be part-way into a frame (section 2),
    so a multi-field record can be torn; the watch list has the same property.
- `emulator.py`: the `memory` property; `run(..., watch=None, watch_every=1)` (`watch` a sequence of `(addr,
  words)`; Python validates as `azh__watch_plan` does and raises `ValueError` with the same largest-frames hint);
  after the reply, `RunResult.watch` from `watch_copy(result.watch_rows)`, decoded into `WatchRow`s with each entry's
  bytes. `run_until` passes `watch` and `watch_every` through if it delegates to `run`.
- `__init__.py`: export `Memory`, `WatchRow`, `GuestMemoryError`.
- `tests/python/fakeworker.py`: only the map size (it uses `_map`'s constants; check).
- `docs/USING.md`: a short "Guest memory" section: our core only; addresses are guest virtual addresses of the
  current process; `read`/`write`/`u32(...)`/`raw_read`; the watch list and its frame-count limit; torn reads;
  `GuestMemoryError` vs `NeedsLazpyCore`; ABI-2 states are refused after this step (phase-3.md risk 7).

## 5. Files (you create or edit only these)

| Path | Role |
|---|---|
| `host/azhost.h`, `host/azh_internal.h`, `host/azh_pure.h` | 3.1, 3.2 |
| `host/mem.c` (new; optionally a pure `host/watch.c`), `host/api.c`, `host/run.c`, `host/hostmap.c`, `host/core.c` (only the bind call beside the detection, if the detection is there) | 3.3 |
| `tests/host/test_mem.c` (new), `Makefile` (`test-host` builds it) | section 6 |
| `python/libazahar/_abi.py`, `_map.py`, `results.py`, `errors.py`, `_worker.py`, `emulator.py`, `memory.py` (new), `__init__.py` | section 4 |
| `tests/python/fakeworker.py`, `tests/python/test_abi.py`, `tests/python/test_map.py` | ABI 3 updates only |
| `tests/python/test_memory.py` (new), `tests/python/test_memory_live.py` (new) | section 6 |
| `tests/gate_c.py` | only if it checks `abi=2` literally (then `abi=3`) |
| `docs/USING.md` | section 4's memory section only |

No core patch, no rebuild (phase-3.md section 9). Everything else is outside your files: in particular E's
`_slots.py`, `pool.py`, `_client.py`, `tools/speed_table.py` and F2's `azhost_main.c` logic, `_paths.py`, `gate_f2.py`.
If a check fails because of one of them, stop and report.

## 6. Tests

`tests/host/test_mem.c` (pure, `make test-host`): `azh__mem_check` (len 0, `AZH_MEM_MAX_LEN` ok, +1 refused,
`0xFFFFFFFC`+4 ok, +8 refused); `azh__mem_code` for 0, -1, -2, -3, -7; `azh__watch_plan` (n 33, words 0 and 257, every
0 -> 1 and 100,001, an entry wrapping 4 GiB, `(8, 8)` gives row bytes 80 and total words 16, the largest `frames`
that fits at every 1 and 10 accepted and one more refused).

`tests/python/test_memory.py` (no emulator): width packing round trips (`u16` 0xBEEF, `s8` -1, `u64` max), write
range checks, `read`/`write` argument checks (negative, > 0xFFFFFFFF, length 0, over the cap, a 4 GiB wrap), the
watch validation mirror (the same cases as `azh__watch_plan`), `WatchRow.u32`, and `watch_copy` on a fake map file
built with `_map`'s offsets.

`tests/python/test_memory_live.py` (`@pytest.mark.slow`; D's fixtures; one Emulator at a time; F2's `core_kind`
fixture decides; the stock test's name contains `stock`, the others do not):
- Common: `seed()` in 2D with inputs that vary keys, touch and circle (`set_input` at fixed iterations); `run(30)`;
  parse `addr_global` and `addr_heap` from the `start` line (`testapp_log.parse_log`, or a regex if it does not
  expose the start line; report which).
- **m1**: 600 x (`run(1)`, `read(global, 32)`, `read(heap, 32)`); then compare each record with the log line of its
  own `frame` (section 1, torn rule); frames non-decreasing per address; at least 590 distinct frames per address.
- **m2**: `run(600, watch=[(global, 8), (heap, 8)])`: 600 rows, status 0, absolute frames consecutive from
  `watch_first + 1`; each row's two records pass m1's check; then `run(600, ..., watch_every=10)`: 60 rows.
- **m3**: seed `exit_at=999001`, `ready_at=999002`. Scan `[(global & ~0xFFF) - 0x10000, (global & ~0xFFF) +
  0x10000)` page by page with `read(page, 4096)`, skipping pages that raise `GuestMemoryError`, for
  `struct.pack("<II", 999001, 999002)`: exactly one hit at X (else FAIL with the count), and the u32s at X - 8
  (`mode3d`), X - 4 (`break_at`), X + 8 (`boot_frames`) are 0. `ready = X + 4`. Then `f = memory.u32(global + 4)`;
  `memory.write_u32(ready, f + 2)`; `memory.u32(ready) == f + 2`; `run(10)`; the first event line logged after the
  write is `ready f=<f + 2>` (the app checks `ready_at == f` each frame, so `f + 2` is still ahead even if the guest
  is already inside frame f + 1).
- **m4**: from `global & ~0xFFF`, `read(page + k x 0x1000, 4)` for k = 1..4096 until the first `GuestMemoryError`:
  that page is P (none within 16 MiB: FAIL). `read(P - 8, 16)` raises `GuestMemoryError` with `.addr == P - 8` and
  `.length == 16`; `read(P - 8, 8)` returns 8 bytes; `read(P, 4)` and `read(0, 4)` raise `GuestMemoryError`;
  `write(P - 4, bytes(8))` raises and `read(P - 4, 4)` is unchanged; `read(0xFFFFFFFC, 8)` raises `ValueError`
  before any request; `run(1)` still works.
- **m5 (stock)**: `read`, `write`, each width call, each `write_*`, and `run(1, watch=[(global, 1)])` raise
  `NeedsLazpyCore`; then `run(1)` works.
- **m6 (record)**: `du -k host.map` and `stats().peak_rss` after m2, printed.

## 7. Steps, with a checkpoint after each (save files as you go; never commit)

0. **Seed the worktree**: `mkdir -p dl && for d in azahar moltenvk libretro-headers vulkan-headers azahar-src; do [ -e
   MAIN/dl/$d ] && ln -s MAIN/dl/$d dl/$d; done`, `cp -R MAIN/vendor .`, `make`, `PATH=/opt/devkitpro/devkitARM/bin:
   /opt/devkitpro/tools/bin:$PATH make testapp` (or copy `MAIN/build/testapp.3dsx`). Checkpoint: `git log --oneline
   -3` shows F2's merge and E1's commit; `make test-host` and the non-slow pytest pass (baseline counts).
1. **G1 (about 0.4 h; no emulator).** Sections 3, 4, the pure tests of 6; write `test_memory_live.py` without
   running it. Checkpoint: gate 1; `azhost layout` output saved to `runs/g/layout.txt` with the four sizes (3612, 312,
   240, 6452 or 10,292).
2. **G2 (about 0.2 h of agent time; timed).** **First**, if the main loop's message said step E2 is still running and
   `../libazahar-py-e/runs/e-speed.rc` does not exist, wait with Monitor until it does (bounded 90 min) and report
   the wait (the speed table must not share the machine with you). Then one background batch, every emulator
   command through the slot cap (Python tests through the Emulator, which uses E1's `_slots`; `gate_c.py` under a
   one-slot holder `runs/g/hold_slot.py`, about 10 lines: `from libazahar._slots import acquire`, `os.set_inheritable
   (slot.fd, True)`, `os.execvp`), one instance at a time, in this order: the live tests on OURS (`-k "not stock"`),
   on STOCK (`-k stock`), gate C on OURS, the full pytest on OURS (gate 4's `--ignore`). As `runs/g/batch.sh` with one rc per part, started
   `sh -c 'trap "echo \$? > runs/g-batch.rc" EXIT; nice -n 10 sh runs/g/batch.sh > runs/g-batch.log 2>&1'` with
   `run_in_background`; Monitor until `runs/g-batch.rc` exists (bounded 120 min). Without Monitor: each part (and
   each slow test file) as a foreground call under the 10-minute limit; say so. Write USING.md's section while it
   runs. Checkpoint: gate 2-4; quote them.
3. The report (section 9) ends the run. Stop every waiter and background task you started (TaskStop) first.

## 8. Machine-sharing rules

- G1 runs no emulator. G2 runs one instance at a time, never beside step E's speed table (step 2's wait) or the
  core build, always nice'd (the worker's `os.nice(10)`, `nice -n 10` on the batch), through the slot cap, folders
  under `runs/g*`, `runs/c-gate/`, `runs/d-pytest/` (ignored).
- Never open a window; PNGs with the Read tool. Never kill a process you did not start. Never write in MAIN.
- Write only the guest memory of your own Emulators (it is the test app); no write test against anything else.
- No `sleep` polling; one Monitor wait per long run, stopped before hand-back.

## 9. The builder's report

Gate 1-4 as printed; the four struct sizes and the `fields[]` row count (and whether `AZH_MAX_FIELDS` moved); the
torn-read counts per address for m1 and m2 and which fields were torn; m3's hit address X, its offset from
`addr_global`, and the frame written; m4's P and its offset from `addr_global`; m6's numbers; the wait for E's table;
line counts per new or edited file and the longest function; anything the core did that section 2 did not predict;
the runners block for `docs/map/runners.md`:
```
LAZ_CORE=<our core> LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python/test_memory_live.py -k "not stock"   # step G's gate
LAZ_CORE=<stock core> LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python/test_memory_live.py -k stock
```
lines for `.gitignore` (none expected); and a final **"Lessons and notes"** block, ready to paste into item 330.

## 10. Hours (agent wall time)

Builder 0.6 h (G1 0.4: the ABI 3 bump, `mem.c`, the watch rows, `memory.py`; G2 0.2), the opus as-built review
0.2 h, the commit 0.1 h: **0.9 h**, against PLAN.md's 0.5 (which did not count the ABI bump the watch list needs).
The wait for E's table and the batch are machine time.

## 11. Interfaces assumed

From phase-3.md section 6: A1-A3, A10, B1-B3, B5-B7, F1, C1-C3, C6, C7, D1, D3, D5-D7, D9, D10, plus E1's `_slots`
(`acquire()`, `Slot.fd`) and F2's `core_kind` fixture and `gate_c.py --core`. If a merged name or offset differs
(C1's row count, `testapp_log`'s start-line parsing, D's `RunResult` field order), follow the code and report the
difference.

## 12. Review checklist (the opus as-built review)

1. ABI 3 appends only: every ABI 2 offset and size unchanged except the four named sizes; `fields[]` has every new
   field and constant; `_abi.check_layout` passes at import; `AZH_ABI_VERSION` 3 in C and Python.
2. The argument order is translated correctly (`azh_read(addr, len, buf)` -> `lazpy_read_memory(addr, buf, len)`);
   the core's codes map as P7 says; `NULL` and the 4 GiB wrap are refused before the call.
3. The stock core gives `AZH_E_NEEDS_LAZPY_CORE` for `azh_read`, `azh_write` and any watch, before any frame.
4. Watch rows: written after the totals and before the shot and stops; the last frame always has a row; the row
   count can never pass `rows_max` (checked in the plan, asserted in the writer); `watch_rows` is a release store.
5. The map size grew only by the watch area, page-aligned at 696,320; nothing else in the map moved.
6. Python validates before sending; `GuestMemoryError` carries `.addr` and `.length`; widths are little-endian and
   range-checked; `raw_read`/`raw_write` exist; `RunResult.watch` holds copies.
7. m1/m2 compare all nine fields against the record's own frame; the torn rule is exactly "each field from line f
   or f - 1", counted and bounded at 1 %; m3 finds exactly one hit; m4's P comes from a bounded probe.
8. G2 waited for E's speed table if it was running; every run went through the slot cap; nothing written in MAIN;
   no item file touched; nothing committed; no core patch.
