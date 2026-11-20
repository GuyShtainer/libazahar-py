# Step G: reading and writing the game's memory, and the watch list (item laz-330)

Brief for one sonnet builder, revision 2 (2026-11-13, after review 2; final). Phase index: `docs/plans/phase-3.md`
(order, ownership, merges, departures, interfaces, Phase 2's holds H1-H7). Contract: `docs/PLAN.md:317` ("Phase G"),
sections 2.2 (`azh_read`/`azh_write`, the watch list) and 2.5 (`emu.memory`, libmgba-py's names). Where this brief
disagrees with PLAN.md on a goal, PLAN.md wins: stop and report (except the approved departures P1-P8 and refinements
R1-R4 of phase-3.md section 5 and phase-2.md section 5, which you follow; P7, approved by Guy, and R1 are this step's).

You work in `../libazahar-py-g` (branch `step-g`, made at main **after step F2 merged**, with step E's E1 commit merged
in; phase-3.md section 2). "MAIN" is `~/VSCodeProjects/3ds-toolkit/projects/libazahar-py`. "OURS" is
`MAIN/build-core/azahar_lazpy_libretro.dylib` (absolute; read only; step 0's build, which F2 gated); "STOCK" is
`dl/azahar/azahar_libretro.dylib`. **Never commit, never edit item files, never write in MAIN, never run
`tools/build-core.sh`** (in a worktree its build tree is the linked `dl/azahar-src/build-src`, MAIN's: a run would
delete it and start a full build). Read first: the repo's `CLAUDE.md`, `docs/map/rules.md`, phase-3.md sections 2, 3, 5,
6, phase-c.md section 3 (the frozen ABI 2 you extend), phase-d.md section 4,
`core/patches/0001-lazpy-memory-exports.patch`, `testapp/source/main.c`, `record.h`, `control.h`,
`tests/python/conftest.py`, `~/.claude/c-golden-rules.md` and `~/.claude/python-golden-rules.md`.

## 1. Goal and gate

Memory reads and writes by guest virtual address through our core's two exports, a per-frame watch list whose rows
land in the map, typed errors, and the stock core refusing all of it. The gate (headless, this Mac):

1. `make check && make && make test-host` clean (with `tests/host/test_watch.c`); `build/azhost layout` prints
   `abi=3` and the new rows (137 `fields[]` rows if C's 114 are as built); `python3 -m pytest -q tests/python -m "not
   slow"` passes (ABI 3 checked at import).
2. `LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python/test_memory_live.py` passes, 0 skipped.
   Every test names its core explicitly (D's `lazpy_core` / `stock_core` fixtures, hold H1; review 1 B4), so this
   one run covers both cores whatever `LAZ_CORE` says:
   - **m1** (ours) for 600 frames, `read` calls of both records (global and heap, the addresses the `start` line
     logs) give the logged values of their own `frame`: magic, frame, vblank, keys, tx, ty, cx, cy and tick (= `s=`);
   - **m2** (ours) one `run(600, watch=[(global, 8), (heap, 8)])` gives 600 rows that pass the same check, and a
     `watch_every=10` batch gives exactly 60 rows;
   - **m3** (ours) a write of the control struct's `ready_at` makes the next event line the app logs `ready
     f=<written>` (refinement R1: the event line, since the record is rewritten every frame);
   - **m4** (ours) a read straddling the end of a mapped region and a fully unmapped read (and address 0) raise
     `GuestMemoryError`; the in-range part reads fine; a straddling write raises and changes nothing;
   - **m5** (stock) every memory call and a `run(..., watch=...)` raise `NeedsLazpyCore`, and the Emulator then runs
     on;
   - **m6** (ours, record) `du -k host.map` and `stats().peak_rss` after m2;
   - **m7** (ours) a state whose meta says `abi=2` loads under ABI 3 and runs (hold H3).
3. Regression on OURS: `python3 -I tests/gate_c.py --core OURS` passes; `LAZ_CORE=OURS LAZ_REQUIRE_EMULATOR=1 python3
   -m pytest -q -rs tests/python --ignore=tests/python/test_pool_live.py` passes 0 skipped (D's, F2's, E's non-live
   and G's tests, gate 2's included; E's live pool test runs 3 instances and belongs to E's gate and the phase-end
   suite).

Torn reads: a record whose fields do not all match line `frame` but each match line `frame` or `frame - 1` is
**torn** (section 2); m1 and m2 print the counts and fail above 1 % per address. Any other mismatch fails.

## 2. Facts (checked; SRC = `MAIN/dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/`, PATCHES = `core/patches/`)

- PATCHES 0001: `extern "C" int lazpy_read_memory(uint32_t vaddr, void *buf, uint32_t len)` and
  `lazpy_write_memory(uint32_t vaddr, const void *buf, uint32_t len)` (note: **address, buffer, length**; A's
  `azh_read(addr, len, buf)` has the length second). Returns 0 ok; -1 not powered on or no current process (or a
  caught exception); -2 a page in the range is unmapped; -3 bad arguments (NULL buffer, len 0, len > 0x4000000, or
  `vaddr + len > 2^32`). Every page of the range is checked with `IsValidVirtualAddress` **before** any byte moves,
  so a failed write changes nothing. Both are in the `.def`, so `dlsym` finds them (F2's f2).
- `ReadBlock` alone would zero-fill unmapped pages and `WriteBlock` skip them (SRC core/memory.cpp:173-229,
  247-253), which is why the exports check first. `IsValidVirtualAddress` is a page pointer or a non-Unmapped
  attribute (memory.cpp:824-837); pages are 0x1000 (memory.h:34).
- `ReadBlock` flushes the GPU cache for rasterizer-cached pages (VRAM, linear heap; memory.cpp:212-217);
  `retro_run` registers the calling thread as the core-loop thread (citra_libretro.cpp:284). The worker has one
  thread that makes every `azh_*` call, so reads and writes run on the core-loop thread, between frames, as the
  patch requires.
- A's detection: `dlsym(core, "lazpy_read_memory")` in `azh_core_open` (`host/core.c:100`) sets `is_lazpy_core`.
  Bind both exports at the same place. Today's `azh_read`/`azh_write` go through `memory_gate()` (`host/api.c:531-557`):
  ORDER before open, `AZH_E_NEEDS_LAZPY_CORE` on stock, `AZH_E_UNSUPPORTED` "arrives in step G" on ours.
- `retro_run` returns after the slice in which the VBlank fired (citra_libretro.cpp:286-306; `MAX_SLICE_LENGTH`
  clock / 234), so when a batch returns the guest may be part-way into its next frame. The app's per-frame order is
  `hidScanInput`, `record_fill(&g_record)`, `memcpy` to the heap copy, then the log line (testapp/source/main.c:
  137-156): a read can land inside `record_fill` (torn) or between the global and the heap copy (the heap one frame
  behind). Hence section 1's torn rule.
- The record: `laz_record` 32 bytes, magic 0x4C415A52 at 0, frame 4, vblank 8, keys 12 (u32), tx 16, ty 18 (u16), cx
  20, cy 22 (i16), tick 24 (u64) (testapp/source/record.h:14-21). The log line `f= v= s= t= k= tx= ty= td= cx= cy=`
  is formatted from `g_record` (record.c:58-61; `td` is bit 20 of `k`). `start addr_global=0x%08lx
  addr_heap=0x%08lx` gives both addresses (record.c:44-46).
- A host write into the record is overwritten next frame and never reaches a log line (main.c:150-155). The control
  struct is read every frame: `static laz_control g_ctl` (main.c:23) with `int mode3d` at 0, u32 `break_at` 4,
  `exit_at` 8, `ready_at` 12, `boot_frames` 16 (control.h:11-19); `run_events` logs `ready f=` when `g_ctl.ready_at
  == f` (main.c:159-170). `ready_at` and `exit_at` accept 1..1,000,000. In C's `build/testapp.elf`, `g_ctl` sits
  at 0x00122d74 and `g_record` at 0x00122dd8 (review 1), so m3's ±64 KiB scan and m4's upward probe both work.
- 3DS user address 0 is unmapped (the app image starts at 0x00100000).
- The map after C: 695,296 bytes, version 2, bytes 1108-4095 free. The next page boundary is 696,320 (170 x 4096).
  An `ftruncate`d file's untouched pages take no disk on APFS and no memory until touched.
- ABI 2 has 114 `fields[]` rows (`host/api.c:49-164`) under `AZH_MAX_FIELDS` 160 with a `_Static_assert`
  (`api.c:166`); this step adds 23 (section 3.1): 137 fit, so `AZH_MAX_FIELDS` and `azh_layout` (6452) do not change.
- D's `from_code` maps `AZH_E_ARG` to `ValueError` carrying the host's text (`errors.py:96-97`), so the host's watch
  plan message (with the largest-frames hint) already reaches the caller; Python does not repeat the plan.
- States: `host/state.c` accepts `2 <= meta.abi <= AZH_ABI_VERSION` (hold H3), so ABI-2 states load after this step.
  D's as-built fix S3 builds `test_newer_abi_refused` (`tests/python/test_state.py:116-124`) from
  `_abi.AZH_ABI_VERSION` (plus an abi-1 case), so it follows ABI 3 with no edit; if the merged test still has the
  literal `"abi=2\n"`, report it (do not edit `test_state.py`). The meta parse is strict on keys
  (`statemeta.c:154`): add no meta key.
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
#define AZH_WATCH_AREA_BYTES 4194304            /* header + rows (fixed 4 MiB; review 1 Q5) */
#define AZH_WATCH_HDR_BYTES 64
#define AZH_WATCH_ROW_HDR 16
typedef struct { uint32_t addr, words; } azh_watch;     /* the watch entry type */
```
- `azh_batch`: append `int32_t n_watch; int32_t watch_every; azh_watch watch[AZH_MAX_WATCH];` (0 entries: no rows,
  ABI 2 behaviour). Size 3348 -> **3612**.
- `azh_result`: append `int32_t watch_rows; int32_t watch_status;` (rows written; 0, or the first non-zero row
  status). Size 304 -> **312**.
- `azh_stats` (240) and `azh_layout` (6452) unchanged.
- Map version 3, size **4,890,624** (696,320 + 4,194,304). The watch area at 696,320:

| Offset | Type | `fields[]` name | Meaning |
|---|---|---|---|
| +0 | u32 | `map.watch_rows` | rows written in this batch; release store after each row |
| +4 | u32 | `map.watch_row_bytes` | 16 + 4 x total words |
| +8 | u32 | `map.watch_words` | total words per row (the sum of the entries' words) |
| +12 | u32 | `map.watch_seq` | +1 at the start of every batch with watch entries |
| +16 | i64 | `map.watch_first` | the absolute frame before the batch's first frame |
| +64 | rows | `map.watch_data` (offset 696,384, size 4,194,240) | row k at +64 + k x row_bytes: i64 absolute frame, i32 status (0 or an `AZH_E_*`), u32 failed entries, then the words of each entry in list order (a failed entry's words are 0) |

`fields[]` gains 23 rows: `batch.n_watch`, `batch.watch_every`, `batch.watch`, `watch.addr`, `watch.words`,
`watch.__size__`, `result.watch_rows`, `result.watch_status`, the six `map.watch_*` rows, and `const.` rows for
`AZH_E_UNMAPPED`, `AZH_MEM_MAX_LEN`, `AZH_MAX_WATCH`, `AZH_WATCH_MAX_WORDS`, `AZH_WATCH_EVERY_MAX`,
`AZH_WATCH_AREA_OFF`, `AZH_WATCH_AREA_BYTES`, `AZH_WATCH_HDR_BYTES`, `AZH_WATCH_ROW_HDR`; the existing
`map.__size__`, `batch.__size__` and `result.__size__` rows take their new values. Same table style as C1 (plain
`offsetof`/`sizeof` rows, no macros, C rule 8). Report the final row count.

### 3.2 Pure functions (`azh_pure.h`, implemented in a new pure `host/watch.c`; review 1 B5)

```c
int azh__mem_check(uint32_t addr, uint32_t len, char *err, size_t cap);      /* 0, or AZH_E_ARG with a reason */
int azh__mem_code(int core_rc);              /* 0->0, -1->AZH_E_ORDER, -2->AZH_E_UNMAPPED, -3->AZH_E_ARG, other->AZH_E_CORE */
int azh__watch_plan(const azh_watch *w, int32_t n, int32_t frames, int32_t every,
                    uint32_t *row_bytes, uint32_t *total_words, uint32_t *rows_max, char *err, size_t cap);
```
`azh__mem_check`: len 1..`AZH_MEM_MAX_LEN`; `(uint64_t)addr + len <= 2^32`. `azh__watch_plan`: n 0..32; every 0
means 1, else 1..`AZH_WATCH_EVERY_MAX`; each entry's words 1..256 and `addr + 4 x words <= 2^32`; rows needed =
`frames / every + (frames % every != 0)`; `rows_needed x row_bytes <= AZH_WATCH_AREA_BYTES - AZH_WATCH_HDR_BYTES`,
else `AZH_E_ARG` whose text names the largest `frames` that fits at this `every`. `host/watch.c` includes only
`azh_pure.h` (which brings `azhost.h`), `<stdint.h>`, `<string.h>`, `<stdio.h>`: no `dlsym`, no `azh_g`, no
`azh_fail`, so it links into `build/test-host`. Add `host/watch.c` to the `Makefile`'s `TEST_SRC`; the
`tests/host/*.c` wildcard already picks up `tests/host/test_watch.c`; register `test_watch()` with one line in
`tests/host/test_main.h` and one call in `tests/host/test_main.c`.

### 3.3 Behaviour

- `azh_read(addr, len, buf)` / `azh_write(addr, len, buf)` replace `memory_gate()`'s step-G stub: call order as
  `azh_shot` (after boot; `AZH_E_ORDER` before); stock core: `AZH_E_NEEDS_LAZPY_CORE` (keep today's text); `buf` NULL
  or `azh__mem_check` failing: `AZH_E_ARG`; then the export, its code through `azh__mem_code`; the error text names
  the address and length (`"guest memory 0x%08x+%u: a page is unmapped"`; for -1 `"guest memory 0x%08x+%u: the core
  has no current process"`). No host.log line per call (they can be frequent).
- `azh_run` with `n_watch > 0`: on the stock core `AZH_E_NEEDS_LAZPY_CORE` before any frame (beside C's debug-text
  check); `azh__watch_plan` failing: `AZH_E_ARG` before any frame. At the batch start (only when `n_watch > 0`):
  `watch_rows = 0`, the row size, the words, `watch_first`, `watch_seq + 1`.
- After each `retro_run`, between `azh__run_one_frame` and `take_shots` (`host/run.c` `run_frames`; C's order, and after
  E1's timing code): when batch frame `i % every == 0`, write one row: the absolute frame, then for each entry
  `lazpy_read_memory(addr, row_ptr, 4 x words)`; a non-zero code zeroes that entry's words, sets the row status to the
  first mapped code and counts the entry as failed. Then the release store of `watch_rows`. At every batch exit that
  returns 0, if the last frame run has no row yet, write it. (`i` is `run_frames`'s 1-based batch frame, `for (i = 1; i
  <= b->frames; ...)`, so 600 frames at `every` 10 give exactly 60 rows; review 2 N2.) `result.watch_rows` and
  `watch_status` filled. An unmapped watch never stops the batch (a game may unmap and remap).
- `host/mem.c` (not pure) holds the two bound function pointers (file statics; `azh__mem_bind(void *core_handle)`
  called beside A's `is_lazpy_core` detection in `core.c`; A detects our core by `lazpy_read_memory` alone
  (`host/core.c:100`): a core that exports `lazpy_read_memory` but not `lazpy_write_memory` is a hard `AZH_E_CORE`
  at `azh_open` with the text "our core lacks lazpy_write_memory" and one host.log line, so `is_lazpy_core` never
  names a half-exported core; review 2 N6), `azh_read`/`azh_write`'s bodies (called from `api.c`), and the row writer
  (`azh__watch_begin`, `azh__watch_row`, `azh__watch_finish`, called from `run.c`). C rules: functions under about
  60 lines, about 2 asserts each, checked returns, bounded loops (entries <= 32, rows <= rows_max).

## 4. The Python side

- `_abi.py`: `Watch` (`addr`, `words` as `c_uint32`), the appended `Batch` and `Result` fields, the new constants,
  the expected abi 3; `check_layout` already checks every `fields[]` row (D), so the new rows are checked too,
  **except** that `map.watch_data`'s size and `map.__size__` are checked by shape, not equality (review 1 Q5):
  `map.watch_data`'s offset equals `_map.WATCH_DATA`, its size holds at least one row of the largest kind
  (`>= 16 + 4 x AZH_MAX_WATCH x AZH_WATCH_MAX_WORDS`, 32,784 bytes), and `map.__size__ == offset + size`. The two host
  values are kept (`_map.watch_area(layout)` or a `HostMap` argument) and used by every bound below, so a later
  resize of the area is a host-only change with no ABI bump.
- `_map.py`: `WATCH_ROWS = 696320`, `WATCH_ROW_BYTES`, `WATCH_WORDS`, `WATCH_SEQ`, `WATCH_FIRST`, `WATCH_DATA =
  696384`; the expected size comes from the host's layout (above), with `4890624` only as the documented ABI-3
  value in a comment and in `rows()` for D's equality checks of the other rows; `HostMap.watch_copy(rows: int) ->
  list[tuple[int, int, bytes]]` (frame, status, the row's words as bytes), reading `watch_rows` first and refusing
  any row that would pass the area's end. Copies, never views.
- `results.py`: `WatchRow(frame: int, status: int, data: tuple[bytes, ...])` (frozen; one `bytes` per watch entry,
  in list order) with `u32(entry: int, word: int = 0) -> int`; `RunResult` appends `watch: tuple[WatchRow, ...] =
  ()`.
- `errors.py`: `GuestMemoryError(LibAzaharError)` (a direct subclass, not a `ValueError`: the argument was valid)
  with `.addr` and `.length` (None when unknown); `from_code` maps `AZH_E_UNMAPPED` to it.
- `_worker.py`: ops `read` (addr, length) -> `("ok", bytes)` (a `ctypes.create_string_buffer`, copied out) and
  `write` (addr, bytes) -> `("ok", None)`; errors as D's other ops.
- `memory.py` (new): `class Memory` made by the Emulator (`emu.memory`, one per Emulator, created on first use):
  - `read(addr: int, length: int) -> bytes` and `write(addr: int, data: bytes | bytearray | memoryview) -> None`;
    Python checks first (`ValueError`): `0 <= addr <= 0xFFFFFFFF`, `1 <= length <= AZH_MEM_MAX_LEN`, `addr +
    length <= 2^32`; a `GuestMemoryError` from the worker gets `.addr` and `.length` set.
  - widths `u8, u16, u32, u64, s8, s16, s32, s64`: small objects that are callable (`emu.memory.u32(addr)`, PLAN
    2.5) and have `raw_read(addr)` and `raw_write(addr, value)` (libmgba-py's names); little-endian `struct`.
  - `write_u8 .. write_u64(addr, value)` (range-checked: `ValueError` outside the width).
  - The docstring says: reads and writes happen between batches; the guest may be part-way into a frame, so a
    multi-field record can be torn; the watch list has the same property.
- `emulator.py`: the `memory` property; `run(..., watch=None, watch_every=1)` (`watch` a sequence of `(addr,
  words)` pairs of ints). Python checks only the shape (`ValueError`): a sequence of int pairs, at most
  `AZH_MAX_WATCH` entries, `watch_every` an int >= 0. Everything else (word counts, the 4 GiB wrap, whether the
  batch fits) is the host's `azh__watch_plan`, whose `AZH_E_ARG` text arrives as `ValueError` (review 1 N4). After
  the reply, `RunResult.watch` from `watch_copy(result.watch_rows)`, decoded into `WatchRow`s with each entry's
  bytes. `run_until` passes `watch` and `watch_every` through to `run`.
- `__init__.py`: export `Memory`, `WatchRow`, `GuestMemoryError`.
- `tests/python/fakeworker.py`: only the map size (it uses `_map`'s constants; check).
- `docs/USING.md`: a short "Guest memory" section: our core only; addresses are guest virtual addresses of the
  current process; `read`/`write`/`u32(...)`/`raw_read`; the watch list and its frame-count limit (the error names
  the largest batch that fits); torn reads; `GuestMemoryError` vs `NeedsLazpyCore`; **states made under ABI 2 still
  load** (hold H3).

## 5. Files (you create or edit only these)

| Path | Role |
|---|---|
| `host/azhost.h`, `host/azh_internal.h`, `host/azh_pure.h` | 3.1, 3.2 (`azh_pure.h` already holds E1's `azh_png_level` lines: add below them) |
| `host/watch.c` (new, pure), `host/mem.c` (new), `host/api.c`, `host/run.c`, `host/hostmap.c`, `host/core.c` (only the bind call beside the detection) | 3.2, 3.3 |
| `Makefile` (`TEST_SRC` gains `host/watch.c`), `tests/host/test_watch.c` (new), `tests/host/test_main.c`, `tests/host/test_main.h` (one line each) | section 6 |
| `python/libazahar/_abi.py`, `_map.py`, `results.py`, `errors.py`, `_worker.py`, `emulator.py`, `memory.py` (new), `__init__.py` | section 4 |
| `tests/python/fakeworker.py`, `tests/python/test_abi.py`, `tests/python/test_map.py` | ABI 3 updates only |
| `tests/python/test_memory.py` (new), `tests/python/test_memory_live.py` (new) | section 6 |
| `docs/USING.md` | section 4's memory section only |

No core patch, no rebuild. Everything else is outside your files: in particular `host/state.c` (H3 is Phase 2's),
`tests/python/conftest.py`, E's `_slots.py`, `pool.py`, `_client.py`, `tools/speed_table.py`, `tools/hold_slot.py`
and F2's `azhost_main.c` logic, `_paths.py`, `gate_f2.py`. If a check fails because of one of them, stop and report.

## 6. Tests

`tests/host/test_watch.c` (pure, `make test-host`): `azh__mem_check` (len 0, `AZH_MEM_MAX_LEN` ok, +1 refused,
`0xFFFFFFFC`+4 ok, +8 refused); `azh__mem_code` for 0, -1, -2, -3, -7; `azh__watch_plan` (n 33, words 0 and 257,
every 0 -> 1 and 100,001, an entry wrapping 4 GiB, `(8, 8)` gives row bytes 80 and total words 16, the largest
`frames` that fits at every 1 and 10 accepted and one more refused, and its error text naming that largest value).

`tests/python/test_memory.py` (no emulator): width packing round trips (`u16` 0xBEEF, `s8` -1, `u64` max), write
range checks, `read`/`write` argument checks (negative, > 0xFFFFFFFF, length 0, over the cap, a 4 GiB wrap), the
watch shape checks (not a pair, 33 entries, a negative `watch_every`), `WatchRow.u32`, `watch_copy` on a fake map
file built with `_map`'s offsets (including a row count that would pass the area's end: refused), and
`check_layout` with altered map rows: a 2 MiB watch area with a matching `map.__size__` accepted, a moved
`map.watch_data` offset refused.

`tests/python/test_memory_live.py` (`@pytest.mark.slow`; D's fixtures; one Emulator at a time; every test takes
`lazpy_core` or `stock_core` and passes it as `core=`, through `d_helpers.boot(host_paths, workdir, seed_dir,
core=...)`):
- Common: `seed()` in 2D with inputs that vary keys, touch and circle (`set_input` at fixed iterations); `run(30)`;
  parse `addr_global` and `addr_heap` from the `start` line (`testapp_log.parse_log`, or a regex if it does not
  expose the start line; report which).
- **m1** (`lazpy_core`): 600 x (`run(1)`, `read(global, 32)`, `read(heap, 32)`); then compare each record with the
  log line of its own `frame` (section 1, torn rule); frames non-decreasing per address; at least 590 distinct
  frames per address; print the lag (how many reads were one frame behind).
- **m2** (`lazpy_core`): `run(600, watch=[(global, 8), (heap, 8)])`: 600 rows, status 0, absolute frames consecutive
  from `watch_first + 1`; each row's two records pass m1's check; then `run(600, ..., watch_every=10)`: 60 rows.
- **m3** (`lazpy_core`): seed `exit_at=999001`, `ready_at=999002`. Scan `[(global & ~0xFFF) - 0x10000, (global &
  ~0xFFF) + 0x10000)` page by page with `read(page, 4096)`, skipping pages that raise `GuestMemoryError`, for
  `struct.pack("<II", 999001, 999002)`: exactly one hit at X (else FAIL with the count), and the u32s at X - 8
  (`mode3d`), X - 4 (`break_at`), X + 8 (`boot_frames`) are 0. `ready = X + 4`. Then `f = memory.u32(global + 4)`;
  `memory.write_u32(ready, f + 2)`; `memory.u32(ready) == f + 2`; `run(10)`; the first event line logged after the
  write is `ready f=<f + 2>` (the app checks `ready_at == f` each frame, so `f + 2` is still ahead even if the guest
  is already inside frame f + 1).
- **m4** (`lazpy_core`): from `global & ~0xFFF`, `read(page + k x 0x1000, 4)` for k = 1..4096 until the first
  `GuestMemoryError`: that page is P (none within 16 MiB: FAIL). `read(P - 8, 16)` raises `GuestMemoryError` with
  `.addr == P - 8` and `.length == 16`; `read(P - 8, 8)` returns 8 bytes; `read(P, 4)` and `read(0, 4)` raise
  `GuestMemoryError`; `write(P - 4, bytes(8))` raises and `read(P - 4, 4)` is unchanged; `read(0xFFFFFFFC, 8)`
  raises `ValueError` before any request; `run(1)` still works.
- **m5** (`stock_core`): `read`, `write`, each width call, each `write_*`, and `run(1, watch=[(global, 1)])` raise
  `NeedsLazpyCore`; then `run(1)` works.
- **m6** (`lazpy_core`, record): `du -k host.map` and `stats().peak_rss` after m2, printed.
- **m7** (`lazpy_core`): `run(60)`, `save_state(workdir / "st" / "state")`, close; rewrite the meta's `abi=3` line
  to `abi=2`; a new Emulator from that state boots and `run(10)` gives `stopped_by == "frames"`.

## 7. Steps, with a checkpoint after each (save files as you go; never commit)

0. **Seed the worktree**: `mkdir -p dl && for d in azahar moltenvk libretro-headers vulkan-headers azahar-src; do [ -e
   MAIN/dl/$d ] && ln -s MAIN/dl/$d dl/$d; done`, `cp -R MAIN/vendor .`, `make`, `PATH=/opt/devkitpro/devkitARM/bin:
   /opt/devkitpro/tools/bin:$PATH make testapp` (or copy `MAIN/build/testapp.3dsx`), and `mkdir -p build-core && ln
   -sf MAIN/build-core/azahar_lazpy_libretro.dylib build-core/azahar_lazpy_libretro.dylib` (D's `lazpy_core` falls
   back to the checkout's `build-core/`; without the link gate 2's our-core tests fail; the link is your
   worktree's, ignored; MAIN's `build-core/` stays read-only; review 2 B2). Checkpoint: `git log --oneline -3` shows
   F2's merge and E1's commit; `make test-host` and the non-slow pytest pass (baseline counts).
1. **G1 (about 0.4 h; no emulator).** Sections 3, 4, the pure tests of 6; write `test_memory_live.py` without
   running it. Checkpoint: gate 1; `azhost layout` output saved to `runs/g/layout.txt` with the four sizes (3612, 312,
   240, 6452) and the row count.
2. **G2 (about 0.15 h of agent time; timed).** **First**, if the main loop's message said step E2 is running and
   `../libazahar-py-e/runs/e-speed.rc` does not exist, wait with Monitor until it does (bounded **150 min**). On a
   timeout, stop the waiter and **end your run** with a "waiting for E2" report (G1's results in it); never start G2
   beside E2. The main loop resumes you when the machine is free (phase-3.md rule T). Then one background batch, one
   instance at a time, as `runs/g/batch.sh` with one rc per part:
   1. `python3 -I tools/hold_slot.py -- python3 -I tests/gate_c.py --core OURS` (E1's tool holds one slot around the
      gate's azhost runs);
   2. `LAZ_CORE=OURS LAZ_REQUIRE_EMULATOR=1 python3 -m pytest -q -rs tests/python
      --ignore=tests/python/test_pool_live.py` (the Emulator takes its own slot through E1's `_slots`; this one run
      is gate 2 and gate 3's pytest).
   Start it as `sh -c 'trap "echo \$? > runs/g-batch.rc" EXIT; nice -n 10 sh runs/g/batch.sh > runs/g-batch.log
   2>&1'` with `run_in_background`; Monitor until `runs/g-batch.rc` exists (bounded 120 min). Without Monitor: each
   part (and each slow test file) as a foreground call under the 10-minute limit; say so. Write USING.md's section
   while it runs. Checkpoint: gates 1-3; quote them (gate 2 from the `test_memory_live.py` lines of part 2).
3. The report (section 9) ends the run. Stop every waiter and background task you started (TaskStop) first.

## 8. Machine-sharing rules

- G1 runs no emulator. G2 runs one instance at a time, never beside step E's speed table (step 2's wait), the core
  build or any other timed part, always nice'd (the worker's nice, `nice -n 10` on the batch), through the slot cap,
  folders under `runs/g*`, `runs/c-gate/`, `runs/d-pytest/` (ignored).
- Never open a window; PNGs with the Read tool. Never kill a process you did not start. Never write in MAIN.
- Write only the guest memory of your own Emulators (it is the test app); no write test against anything else.
- No `sleep` polling; one Monitor wait per long run, stopped before hand-back.

## 9. The builder's report

Gates 1-3 as printed; the four struct sizes and the `fields[]` row count; the torn-read counts per address for m1 and
m2, which fields were torn, and m1's lag; m3's hit address X, its offset from `addr_global`, and the frame written; m4's
P and its offset from `addr_global`; m6's numbers; m7's result; the wait for E's table; whether the merged
`test_newer_abi_refused` passed under ABI 3 with no edit; line counts per new or edited file and the longest function;
anything the core did that section 2 did not predict; the runners block for `docs/map/runners.md`:
```
LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python/test_memory_live.py   # step G's gate (both cores)
```
lines for `.gitignore` (none expected); and a final **"Lessons and notes"** block, ready to paste into item 330.

## 10. Hours (agent wall time)

Builder 0.55 h (G1 0.4: the ABI 3 bump, `watch.c`, `mem.c`, the watch rows, `memory.py`; G2 0.15), the opus as-built
review 0.2 h, the commit 0.1 h: **0.85 h**, against PLAN.md's 0.5 (which did not count the ABI bump the watch list
needs). The wait for E's table and the batch are machine time.

## 11. Interfaces assumed

From phase-3.md section 6: H1, H3, A1-A3, A10, B1-B7, F1, C1-C3, C6, C7, D1, D3, D5-D7, D9, D10, plus E1's `_slots`
(`acquire()`, `Slot.fd`), E1's `tools/hold_slot.py`, F2's `gate_c.py --core` and our-core expectations. If a merged
name or offset differs (C1's row count, `testapp_log`'s start-line parsing, D's `RunResult` field order, the D
fixtures' names), follow the code and report the difference.

## 12. Review checklist (the opus as-built review)

1. ABI 3 appends only: every ABI 2 offset and size unchanged except the named sizes (`azh_batch` 3612,
   `azh_result` 312, map 4,890,624); `fields[]` has every new field and constant (137 rows); `_abi.check_layout`
   passes at import; `AZH_ABI_VERSION` 3 in C and Python.
2. The argument order is translated correctly (`azh_read(addr, len, buf)` -> `lazpy_read_memory(addr, buf, len)`);
   the core's codes map as P7 says; `NULL` and the 4 GiB wrap are refused before the call.
3. The stock core gives `AZH_E_NEEDS_LAZPY_CORE` for `azh_read`, `azh_write` and any watch, before any frame.
4. Watch rows: written after `azh__run_one_frame` and before the shot and stops; the last frame always has a row;
   the row count can never pass `rows_max` (checked in the plan, asserted in the writer); `watch_rows` is a release
   store.
5. The map size grew only by the watch area, page-aligned at 696,320; nothing else in the map moved; Python takes the
   area's size from the layout and bounds `watch_copy` by it.
6. `host/watch.c` is pure and in `TEST_SRC`; `test_watch()` is registered; `make test-host` runs it.
7. Python checks the watch shape only and leaves the plan to the host; `GuestMemoryError` carries `.addr` and
   `.length`; widths are little-endian and range-checked; `raw_read`/`raw_write` exist; `RunResult.watch` holds
   copies.
8. m1/m2 compare all nine fields against the record's own frame; the torn rule is exactly "each field from line f
   or f - 1", counted and bounded at 1 %; m3 finds exactly one hit; m4's P comes from a bounded probe; every live
   test names its core; m7 loads an ABI-2 state.
9. G2 waited for E's speed table if it was running (or ended its run on the timeout); every run went through the slot
   cap; nothing written in MAIN; no item file touched; nothing committed; no core patch; `host/state.c` and
   `tests/python/test_state.py` untouched; `tools/build-core.sh` never run; a half-exported core fails at open.
