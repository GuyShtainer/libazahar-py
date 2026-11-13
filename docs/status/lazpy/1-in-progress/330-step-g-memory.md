---
id: laz-330
title: lazpy
order: 330
kind: step
parent: laz-300
page: Reading and writing the game's memory
hours: -
---
# Step G: reading and writing the game's memory

## What it is
Memory reads and writes through our core's exported calls, the per-frame watch list, a clear error on the stock core.

## Exit gate
The gate in `docs/PLAN.md` line 310 ("Phase G"), run headless on this Mac with a pass/fail answer.

## Evidence
none yet

## Pointers
- Plan section: `docs/PLAN.md:317`
- Phase plan: `docs/plans/phase-g.md` (the builder brief), `docs/plans/phase-3.md`
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- G1 (a974a8613e6508e64, sonnet, 01:56-02:03; uncommitted in ../libazahar-py-g, progress in runs/g/progress.md):
  ABI 3 (map v3, 4,890,624 bytes; 137 fields[] rows of 160), new host/watch.c (pure) and host/mem.c (binds the two
  lazpy exports; a half-exported core fails at azh_open), the watch hooks in run.c between the frame and the
  shots, python/libazahar/memory.py, USING.md section 12a. make check and make clean; test-host 307782/0 (+39);
  pytest not slow 102 passed, 1 skipped. test_memory_live.py written, not run. G2 (runs/g/batch.sh: gate_c on our
  core, then the full pytest with test_memory_live.py) waits for E's runs/e-speed.rc; then resume the builder.
  Runners line: LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python/test_memory_live.py.
- G2 (a974a8613e6508e64 resumed 02:04, "G done" 02:07); committed on step-g as 32f3b7c, main merged in at 1b3dc93.
  test_memory_live m1-m7 passed on both cores: m1 600 reads of each record, 0 torn; m2 600 watch rows, every=10
  gives 60, an oversize batch refused with the largest size that fits; m3 the control struct found once and a
  ready_at write honoured (ready f=31); m4 the first unmapped page above the globals raises GuestMemoryError with
  .addr/.length, a straddling write changes nothing; m5 the stock core raises NeedsLazpyCore for every call and runs
  on; m6 host.map du 4776 KiB on every instance (any mmap write into the sparse file allocates it all on this Mac;
  0.7 MB before), peak RSS 1.52 GB; m7 an abi=2 state loads under ABI 3. Gate 3 on our core: gate_c 28/0, full
  pytest 129 passed, 1 skipped (test_lazpy_profile's start-5 case under nice -n 10), load 27-32. Opus as-built
  review a73a231eabc07771f launched (judges the host.map size). test_memory_live alone, 0 skipped, still unproven.
- Lessons (builder): ABI 3 is append-only; azh_read(addr, len, buf) maps to lazpy_read_memory(addr, buf, len);
  _abi.check_layout checks the watch area by shape, so resizing it is host-only; a half-exported core is AZH_E_CORE
  at azh_open; the map's memset must stop before the watch area; on macOS read resident size, not du, for sparse use.
- As-built review (a73a231eabc07771f, docs/reviews/step-g-as-built.md): no blocker, checklist 1-9 PASS; merge after
  S1 (memory.write takes bytes-like only: write(addr, 5) was a silent 5-byte zero write), S2 (a watch-area resize
  must stay host-only: _abi checks the const by equality), S3 (m2 cannot catch stale watch rows). host.map's 4776
  KiB: APFS allocates a whole file under about 20 MiB on any write (16 MiB whole, 20 MiB and up sparse); RAM is
  unaffected; acceptable at cap 2, change nothing (a smaller area costs batch length). Argument order correct at
  every call site. The torn rule would catch a tear, but reads land while the app waits for VBlank, so 0 torn proves
  correct reads, not the torn handling. Main (with E) merged into step-g at 76beb4f. Fixer a16674883dc9a5396 takes
  S1-S3, E's post-merge timing changes (slot waits out of t_state; gate_c takes its own slot) and E's held NICEs.
