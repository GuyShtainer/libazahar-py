---
id: laz-320
title: lazpy
order: 320
kind: step
parent: laz-300
page: Our patched core passes the full test batch, with exact repeats
hours: -
---
# Step F2: our patched core passes the full test batch, with exact repeats

## What it is
Gate our built core: its exported symbols and version, the Phase C and D tests on it, identical repeats and state boots, the exact debug-text stop.

## Exit gate
The gate in `docs/PLAN.md` line 311 ("Phase F2"), run headless on this Mac with a pass/fail answer.

## Evidence
none yet

## Pointers
- Plan section: `docs/PLAN.md:311`
- Phase plan: `docs/plans/phase-f2.md` (the builder brief), `docs/plans/phase-3.md`
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- Builder a76e4f3e6572c2142 (sonnet), launched 01:09 in ../libazahar-py-f2 (step-f2 at 6898a4b), forced hand-back
  mid-batch. F2-0 done (make test-host 307743 checks 0 failed; 49 passed). F2-1 done: --lazpy-profile in
  host/azhost_main.c, _paths.lazpy_profile(), _worker.option_plan() and an 8th start element, emulator.py reads
  the lazpy profile and closes after guest_exited via a private _close(graceful); gate_c.py --core/--core-kind;
  test_c4_debug_text_on_our_core; new tests/python/test_lazpy_profile.py (6) and tests/gate_f2.py
  (keyblob_findings, keyblob_records, symbol_findings; scenarios keyblob, symbols, version, dbg, r1, r2, cross,
  stock_r1). make check rc 0; 55 passed. Keyblob check on the stock core: 30 findings (not vacuous).
  PASS f1 keyblob (OURS 21,828,992 bytes; both .a sha256 still match; 70 OpenSSL strings; link line frameworks
  Cocoa, AVFoundation, IOSurface, no -l; otool lists no SSL), f2 symbols (28 ours, 25 stock), f3 version
  2126.2-lazpy.1 and the 6 option keys logged; f4 gate_c on OURS 28 passed 0 failed. Its "built for newer macOS:
  0" RECORD is wrong: the linker writes built for newer 'macOS' version (quotes); the count is 944.
  Departures: hold_slot around whole processes (one slot each, children inherit); batch.sh first removes
  runs/c-gate and runs/d-pytest; exit-path grep text is host/env.c's write(2) payload. The batch (runs/f2/batch.sh,
  started 01:14:44 under load 24-40) runs on; f4's pytest and f5-f9 pending; the builder is resumed on
  runs/f2-batch.rc.
- Batch result 01:14-01:15: every failure (pytest OURS 21, gate_f2 1, smoke pytest 3) is the worker dying at
  start: os.nice(0) raises PermissionError at nice 20 on macOS (the batch nested nice -n 10 twice); works at 0,
  10, 15; os.getpriority/setpriority work at 20. A real bug in hold H2 (_worker.py:120): any caller at nice 20
  kills every Emulator. Second builder a83e1355c6bcddc1f (sonnet, fresh; the first ran out of context) fixes it
  with getpriority/setpriority plus a unit test, fixes the batch's nesting and the 'macOS' quote in the count,
  and reruns the batch.
- Second run (a83e1355c6bcddc1f): _worker.raise_nice_floor(floor=10) with getpriority/setpriority, no os.nice
  left; test_worker_nice_step_survives_nice_20 (not slow; 56 passed); batch.sh has one nice layer and logs its
  nice; gate_f2.py counts built for newer 'macOS' version. make check rc 0, test-host 307743/0. Batch rerun
  started 01:17:47 at nice 15 (session at nice 5 plus nice -n 10), load 15-32; a restart to nice 10 was denied,
  so the nice-15 batch stands. The main loop waits on runs/f2-batch.rc and collects f4-f9 itself.
- Batch rerun ended 01:21:11 (runs/f2/*.rc in the F2 worktree): gate_c 0, pytest 0, smoke gate_c 0, smoke pytest 0,
  gate_f2 1; 0 lines in exitpath-ours.txt. gate_f2: every f-check PASS (keyblob, symbols ours/stock, version
  2126.2-lazpy.1, options, dbg d1-d4, r1 identical, r2 boot and restored equal, cross both ways ok) except
  r2.1.t_state 2.80 s (bound 2.5) at load 28; r2.2 1.91 s. RECORD: 944 built-for-newer-macOS lines; the libssl.a
  and libcrypto.a sha256 still match; stock_r1 differs only in log fields s and t (shots match).
- 01:24 rerun of r2 alone plus test_state_boot (Gen3D held; load rose to 46 from other sessions' builds): r2.1 2.60 s,
  r2.2 4.88 s, state_boot failed; correctness parts passed. drain_ms and unserialize_ms carry the time (about
  0.5-1.4 s each), so the bound is a load floor. runs/f2/quiet-rerun.sh waits until the 1-min load is under 10
  and the 5-min under 14, then reruns both once (waiter bi08wz1d9, 4 h at most). The bound stays as planned.
