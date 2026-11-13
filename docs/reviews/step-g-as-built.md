# Step G as-built review (item laz-330; opus, 2026-11-13)

**Verdict: PASS, no blockers. Fix the 3 SHOULDs before the merge (about 20 minutes, no emulator except S3's one
file).** Code reviewed: `git diff 9ca360d 32f3b7c` in `../libazahar-py-g` (step-g). Spec: docs/plans/phase-g.md
sections 1-11 and 13, checklist section 12.

My own checks in the G worktree, under nice -n 10, with no emulator started: `make check` clean; `make test-host` 307782 checks,
0 failed; `pytest -m "not slow" tests/python/test_memory.py tests/python/test_abi.py` 39 passed; `build/azhost layout`
matches `runs/g/layout.txt`, and a diff against MAIN's ABI-2 `build/azhost layout` shows only appended rows (below).
One deviation from read-only: the host.map disk probe (finding A) wrote and deleted small files in the worktree's
ignored `runs/g-review/`. That folder is gone again.

## Section 12 checklist

| # | Item | Result |
|---|---|---|
| 1 | ABI 3 appends only | PASS. Layout diff ABI 2 -> 3: only appended rows and the named sizes (batch 3348 -> 3612, result 304 -> 312, map 695,296 -> 4,890,624). 137 `fields[]` rows (`runs/g/layout.txt` has 138 lines including `abi=3`). `AZH_ABI_VERSION` 3 in host/azhost.h:9 and _abi.py:56. `check_layout` passes at import (test_memory.py:177-180). |
| 2 | Argument order, code map, NULL/wrap | PASS. Every call site matches patch 0001 `(vaddr, buf, len)`: mem.c:12-13 typedefs, mem.c:77, :93, :163. The Python prototypes (`_host.py:23-24`) and the worker calls (`_worker.py:86`, `:93`) use `azh_read(addr, len, buf)`, correctly. Codes: watch.c:36-49 (0/-1/-2/-3/other -> 0/ORDER/UNMAPPED/ARG/CORE). NULL is refused at mem.c:71 and :87, the 4 GiB wrap at watch.c:26, both before the core call. |
| 3 | Stock core refuses before any frame | PASS. `memory_gate` api.c:557-567. Watch: mem.c:110-112, through `check_batch` api.c:502, before `azh_run_batch_inputs`. Proven live by m5. |
| 4 | Watch rows | PASS. The row comes after `azh__run_one_frame` and before `take_shots`/`stop_after` (run.c:378-380). The last frame always gets a row (mem.c:195-196, only on rc OK, run.c:394-396). Rows <= ceil(frames_run/every) <= ceil(frames/every) <= rows_max: the plan checks this (watch.c:111) and the writer asserts it (mem.c:158; asserts are live, no NDEBUG). Row end <= 64 + rows_max x row_bytes <= AREA_BYTES. Release stores at mem.c:138, :142, :178. |
| 5 | Map grew only by the area | PASS, with one departure. The area sits page-aligned at 696,320 and nothing else moved. `watch_copy` is bounded by the mapped file length (`_map.py:82-85`, `len(mm) - WATCH_DATA`), not by the layout's `map.watch_data` size. The host sizes the file from that same constant, and the mmap length can never be overrun, so I accept the departure. |
| 6 | watch.c pure, in TEST_SRC, registered | PASS. Makefile:42, test_main.c:41, test_main.h:16. Its includes are `azh_pure.h`, stdint, stdio and string only. |
| 7 | Python shape only; error fields; widths | PASS. `_fill_watch` emulator.py:243 checks shape plus u32 fit (needed for ctypes); the plan is left to the host. `GuestMemoryError` gets `.addr`/`.length` (memory.py `_call`). Widths are little-endian and range-checked; `raw_read`/`raw_write` exist. `WatchRow.data` holds `bytes` copies. See S1 for the int footgun. |
| 8 | Live tests | PASS except m2 (S3). m1 compares all nine fields with the record's own frame line, and the torn rule is exactly "each mismatched field from line f-1", bounded at 1 % (test_memory_live.py:64-92). m3 asserts exactly one hit (:167); m4's probe is bounded at 4096 pages (:187); every test names its core; m7 rewrites the meta to `abi=2` and runs (:228-239). |
| 9 | Process | PASS. The builder waited for E2 (progress.md: ended its run "waiting for E2" at 02:02, resumed after `e-speed.rc` at 02:05). Part 1 ran under `hold_slot`, part 2 through `_slots`. MAIN's tree is clean. `host/state.c`, `test_state.py`, `core/patches/` and item files are untouched. No sign of a `build-core.sh` run (`build-core/` holds only the link). A half-exported core fails at open: core.c:101-105 returns `AZH_E_CORE`, and `azh_fail` writes the one host.log line. This is checked in code only: no test covers it. |

Gate 2's "0 skipped" is proven even though the file was never run alone. Part 2 ran with `-rs`, and its summary
lists one skip only (`test_lazpy_profile.py:65`, nice). `LAZ_REQUIRE_EMULATOR=1` turns a missing core into a failure
(conftest.py:26-30), and part 2 had 0 failures. So all 6 tests in test_memory_live.py ran and passed, with m5 on the
stock core.

## BLOCKER

None.

## SHOULD

**S1. `Memory.write(addr, 5)` silently writes 5 zero bytes into guest memory** (python/libazahar/memory.py:84,
`payload = bytes(data)`). `bytes(int)` is a zero buffer of that length, and a script that writes `write(addr, value)`
when it meant `write_u32` corrupts guest memory without an error. Fix: before `bytes(data)` add
`if not isinstance(data, (bytes, bytearray, memoryview)): raise TypeError("data must be bytes, bytearray or memoryview")`.
Add `mem.write(0x100, 5)` -> TypeError, with no call recorded, to `test_write_argument_checks` (test_memory.py).

**S2. Resizing the watch area is not a host-only change, so review 1 Q5 and section 4 are not met.**
`const.AZH_WATCH_AREA_BYTES` goes through the equality check in `_check_const_row` (_abi.py:70, :178-184). A host
with any other area size fails the import check. `test_smaller_watch_area_with_matching_map_size_is_accepted`
(test_memory.py:183-188) changes only the map rows and leaves the const row alone, so it passes when the real case
would fail. Fix: in `_check_const_row`, treat `AZH_WATCH_AREA_BYTES` like the shape rows. Accept any value equal to the
host's `map.__size__` minus `AZH_WATCH_AREA_OFF` (pass `host_data` in: `value == data_offset + data_size -
AZH_WATCH_AREA_OFF`). In the test, also set `row_of(bad, "const.AZH_WATCH_AREA_BYTES").offset = data.offset +
data.size - 696320`. This matters for finding A: it is what makes "shrink the area" a host-only option.

**S3. m2 cannot catch stale or repeated watch rows** (test_memory_live.py:131-143). `verify()` compares each row with
its own frame's line. If every row held the same bytes (a writer bug), all 600 rows would be "clean", and the only
frame check is on `r.frame`, which the host makes itself. Fix: after the `res` lines, add
`gf = [decode(r.data[0])["frame"] for r in res.watch]; assert all(b >= a for a, b in zip(gf, gf[1:])) and len(set(gf)) >= 590`,
the same for the heap entry, and for `res10` add strictly increasing guest frames with `len(set(...)) >= 59`. Rerun
test_memory_live.py alone (one emulator at a time, nice'd) after the fix.

## NICE

- N1. emulator.py:266-276: check `row_bytes == 16 + 4 * sum(words)` (read `map.watch_row_bytes` or return it from
  `watch_copy`). Then a mismatch raises HostError, where today it gives short slices with no error.
- N2. hostmap.c:53's comment is half right. The untouched watch area takes no RAM, but APFS allocates the whole file on
  disk (finding A). Reword the comment: "no RAM until written; APFS still allocates small sparse files whole on disk".
- N3. watch.c:113-117: the "largest batch" hint, `rows_max x every`, can exceed the 100,000,000 frame cap (for example
  1 word at every 100000). Clamp the hint to `min(rows_max * every, 100000000)`.
- N4. A failed memory call goes through `azh_fail` (mem.c:48-62), which writes a host.log ERROR line each time. A probe
  loop (m3's ±64 KiB scan, or a Gen3D script) fills host.log, against section 3.3's "no host.log line per call". A
  quiet variant of the fail call (sets the error text, no log line) for `mem_fail` fixes it.
- N5. test_memory_live.py:26 appends to `runs/g/live-numbers.txt` forever, in the folder `tests/gate-a.sh` also
  uses. Use `runs/g-memory/` and truncate the file at the first `note()` of a session.
- N6. tests/checks_c.py:65 turns the 4 MB `map.watch_data` into one Python int on every `read_map`. Skip
  `map.watch_*` there (outside G's files; for whoever next edits checks_c).
- N7. Add `_Static_assert`s in azh_internal.h for `AZH_MAP_OFF_WATCH_ROWS == AZH_WATCH_AREA_OFF`,
  `AZH_MAP_OFF_WATCH_DATA == AZH_WATCH_AREA_OFF + AZH_WATCH_HDR_BYTES`, `AZH_WATCH_AREA_OFF % 4096 == 0` and
  `AZH_MAP_PX_END <= AZH_WATCH_AREA_OFF`. Today the literals 696320/696384 are tied together only by comments.
- N8. USING.md puts section "12a" before section 12. Several added lines run past 120 columns (`__init__.py:3`, `:13`;
  azh_internal.h:4; azh_pure.h:2). This is cosmetic.

## Judged findings

**(a) host.map at 4,890,624 bytes and 4776 KiB on disk for every instance.** The code is not the cause. hostmap.c:53
now memsets only the first 695,296 bytes (`AZH_MAP_PX_END`), and the watch area is written only when `n_watch > 0`
(mem.c `azh__watch_begin`/`write_row`).

I probed this volume (APFS): ftruncate to 4,890,624, then one 4 KiB write. du shows 4776 KiB after the flush, whether
the write is pwrite or mmap, at the start, middle or end. A 16 MiB file is also allocated whole (16384 KiB); a file
of 20 MiB or more stays sparse (16 KiB). So APFS allocates small sparse files whole on their first write. The trigger
is the file's size (the threshold is between 16 and 20 MiB here); the builder blamed mmap writes, but mmap is not the
trigger.

RAM is not affected: untouched pages are never resident, and m6's peak_rss of 1.5 GB is the core. 4.7 MB of disk per
live instance is about 0.5 % of one instance's RAM, and the cap is 2. **Acceptable as built; do not change it now.**
Never rely on the over-16-MiB sparse behaviour, which is undocumented.

If a smaller file is ever wanted, the cheapest fix is to shrink `AZH_WATCH_AREA_BYTES`. That is a host-only change
with no ABI bump once S2 is in, because Python then checks the area's shape only. The cost: at 1 MiB, the largest
`(8,8)` every-1 batch drops from 52,428 to 13,106 frames. Creating the area only when a watch is asked for would need
a variable `map.__size__` and a remap in `HostMap` (an ABI-shape change, more work), so it is not worth it.

**(b) Argument order.** Correct at every site (checklist 2). The only translation from `(addr, len, buf)` to the
core's `(vaddr, buf, len)` is at mem.c:77, :93 and :163. Python never calls the core directly.

**(c) The torn rule never fired. Is the test strong enough?** It would *catch* a tear. `record_fill` writes in struct
order (testapp/source/record.c:25-33). `frame` (+4), `vblank` (+8) and `tick` (+24) change every frame, so any tear
between the `frame` store and the `tick` store leaves a mismatched field that matches line f-1. That counts as torn,
or, if the compiler reorders the stores, it fails as "bad", which is stricter. But the test cannot *provoke* a tear.
The reads land while the app is parked in its VBlank wait: m1's lag is 0 of 600, so no read ever fell between
`record_fill` and the heap memcpy. The slice ends about a million cycles from a store sequence of a few dozen cycles.
So "0 torn" proves the reads are correct; it proves nothing about tear handling. A real tear probe would need a
test-app mode that rewrites the record in a busy loop. That is not needed for this step; leave it to a later step.

## Merge with step E (E2)

- **No textual conflicts.** E2's uncommitted edits are `_slots.py` (DEFAULT_CAP 2), `test_pool_live.py` (`own_seed`)
  and `docs/research/speed-table-e.md`, and G touches none of them. step-e's committed tree (8c06e26) is identical to
  G's base 9ca360d (`git diff 9ca360d step-e` is empty).
- **DEFAULT_CAP 2 does not affect G.** No G test holds more than one Emulator at once: m7 closes the first before
  opening the second. `test_pool.py` pins `LAZ_MAX_INSTANCES=3` (:34), and `test_slots.py` uses the env or
  `_slots.DEFAULT_CAP` symbolically. G's tree still says 3 (`_slots.py:25`) until E2 lands.
- **For E's reviewer (fixes held until step-g merges):**
  - `__init__.py`: G rewrote the `from .errors import (...)` line (now includes `GuestMemoryError`), added
    `from .memory import Memory`, added `WatchRow` to the results import, and added three names to `__all__`. Any
    E fix to those lines conflicts textually; keep both sides.
  - `host/run.c`: G added `azh__watch_begin(b)` at the end of `batch_init` (:284), `azh__watch_row(b, i)` between E1's
    `core_ns`/`vblanks` lines and the shot block (:378-380), and `azh__watch_finish` after `stop_reason` (:394-396).
    The row reads run outside `core_ns`, so E1's timing line now books them to `host_ms`. If E's fix restructures
    `run_frames`, keep the row after `azh__run_one_frame` and before `take_shots`, and call the finish only when
    rc is OK.
  - `host/azh_pure.h`: G edited the header comment (line 2, adding `watch.c`) and appended the `watch.c` block
    directly below E1's `azh_png_level_bad` lines (:29-33). An E edit to the png lines will need a hand merge only if
    it touches the last png line.
