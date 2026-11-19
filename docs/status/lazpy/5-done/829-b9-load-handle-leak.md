---
id: laz-829
title: lazpy
order: 829
kind: step
parent: laz-820
page: Phase B: each state load leaks two Windows handles; find and fix
hours: -
---
# B9: handle leak per state load (from A2)

## What it is
Phase B: each state load leaks two Windows handles; find and fix.

## Exit gate
The plan row's gate, run on the PC through runs/p8/bin/pclane; the lane merged on main; the phase B review passed.

## Evidence
2026-11-19 01:42: lane leak merged on main. The leak is in the core's unserialize step: about 2.2 Semaphore
handles per load_state (20 loads: 65 -> 109), every other type flat; save_state and run leak nothing.
test_handles_live.py on the PC: 1 xfailed (Windows, strict), 1 skipped (the macOS/Linux variant). Waits on the core
fix in C6a and the phase B review.
2026-11-19 02:16: the review (docs/reviews/phase-8b-as-built.md, ready with changes) and its fixes merged (lanes fimg, flife, fmisc). Second full PC gate: 379 passed, 11 skipped, 1 xfailed (laz-829), 1 failed: test_m5_stock_core_refuses, a load flake (3 of 3 alone at 02:16; its boot retry doubled to 600 frames). Done here: the guard (strict xfail) is in place; the core fix moves to C6a (laz-830 notes).

## Pointers
- From A2: runs/p8/a/decisions.md (outside git); item 820's notes
- Briefs: `docs/plans/phase-8b-briefs.md`

## Lessons and notes
Read this part only when you work on this item.

- Main loop: the test runs 60 loads, not 200 (about 130 leaked handles today, far over the 5 % bound; ~1.5 min
  instead of ~4.8). The xfail is strict: when the core patch lands it reports XPASS as a failure; remove it then.
- C6a must carry the trace build below to find the owner.

### The lane's notes (moved here from LEAK-NOTES.md)

Result: the leak is in the core (Azahar), not in host C or Python. No source change; a live test, marked xfail on
Windows, guards it.

### Method
A scratch probe (NtQuerySystemInformation class 64, SystemExtendedHandleInformation, filtered to the worker pid;
types by DuplicateHandle + NtQueryObject) took the worker's handle type counts before and after N loads of a saved
state. Windows PC, release core lazpy.2, test app.

### Evidence
- 20 loads: Semaphore 65 -> 109 (+44, 2.2 per load); Event +1 to +3 (noise); File, Section, Key, Mutant, Thread,
  IoCompletion unchanged in net count. 10 loads: Semaphore +24.
- The leaked semaphores are all (current 0, maximum 2147483647) (NtQuerySemaphore), the shape of the MinGW
  winpthreads condition variable / sem_t semaphore (a condition variable owns two). So about one leaked object per
  load that holds a condition variable or semaphore, created while the core restores a state.
- 20 x save_state: no change at all (serialize and the drain are clean). 20 x run(3): no change.
- host.log per load: sd_ms 3 to 11 (replace_sd), drain_ms ~550, unserialize_ms ~800 to 960. The leak is in the
  unserialize step: host/state.c's SD replace and file reads create no Semaphore (grep: only FindFirstFile/FindClose
  in win_sdcopy.c, CreateFileMapping with CloseHandle in win_compat.c; no semaphore API), and Python's side is the
  parent process, whose handles stayed flat in A2.
- Same leak (about 2.2 per load) with citra_use_cpu_jit=disabled, citra_use_hw_shader=disabled and
  citra_use_shader_jit=disabled: not the JIT or the shader paths. (Software renderer cannot be tried: the host
  requires a Vulkan context.)

### Not found
Which core object it is: the core source is not on the PC, and a stack of the CreateSemaphore calls needs a debugger
or a rebuilt core. Smallest next step for C6a: build the core with a CreateSemaphoreW/CreateEventW trace (or run it
under a debugger with a breakpoint on CreateSemaphoreW during unserialize) to get the allocation stack; the likely
shape is an object (thread worker, Common::Event, or a Vulkan scheduler/renderer piece) that System::LoadState
recreates without destroying the old one, or a shared_ptr cycle in the restored kernel/service objects.
Effect size: about 2 handles per load, RSS flat, so 300 loads cost about 700 handles; Windows allows ~16 million per
process, so it is not a practical limit before the process is closed.

### Test
tests/python/test_handles_live.py: 200 loads, handle count within 5 % (Windows, xfail strict with this reason);
the same check counts descriptors on macOS/Linux (/proc or lsof) and is not run here.
