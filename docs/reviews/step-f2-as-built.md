# Step F2 as-built review (item laz-320), opus, 2026-11-13

**Verdict: merge after fixes B1 and S1-S5** (none of them needs an emulator, except S3's one-second `gate_c --only f`
on our core, which can ride the queued quiet rerun). r2's `t_state` failure is load: the check is built as the plan
says, and the stock core misses the same bound under the same load (below).

Scope: plan `docs/plans/phase-f2.md` section 12, items 0-9. Item 0 is on main (a00119c, 7c33f38; README touched again
in 776e8da). Items 1-9 are the uncommitted worktree `../libazahar-py-f2` (branch step-f2, HEAD 6898a4b, nothing
committed). Evidence is under `<wt>/runs/f2/`. I ran no emulator. The pure checks I ran, all at nice 10:
`tests/python/test_lazpy_profile.py` (7 passed); an import test of `gate_f2`; and `keyblob_findings` on the real paths
(`[]`) and on a wrong tree path (also `[]`, which is B1).

## Checklist

| # | Grade | Evidence |
|---|---|---|
| 0 | PASS (S4, N7, N8) | 0007 (`core/patches/0007-lazpy-no-default-clcert.patch:7` notice; `:15-16` both includes removed; `:24-32` the whole fallback copy becomes `LOG_ERROR(..., "ClCertA file missing"); return;`; `:33` the `else` branch is intact). 0008 (`:7` notice; `:34` `return std::istringstream("");`). `core/PIN:9-11` drop, OpenSSL version and prefix. `tools/build-core.sh`: the OpenSSL pin is checked at `:69-75`, before the STAMP and unpack at `:77-80`. STAMP covers the tarball sha, the patches and `drop=` (`:77`). Drop refusals at `:91-92`. Configure flags `:115-122`, guards `:127-136`. `build.inputs` is written at `:140-158`, before the compile at `:160`. Guards: `.o.d` `:161-166`, link line `:167-169`, LibreSSL strings `:171`, otool `:178-180`. Atomic install (tmp, strip, sign, verify, mv) `:174-181`. README rows `core/README.md:24-25`, licence `:48-51`. `build-core/build.inputs`: every sha equals MAIN's and the worktree's `core/PIN`, `tools/build-core.sh` and `core/patches/*` (checked with shasum); `clean=yes`; `head=799e8c3` is the pre-G8 name of 7c33f38 (`docs/commit-map-g8.tsv:19`). Build tree: all four drop entries absent, the reading copy keeps them; the only remaining key-blob references are under `ENABLE_BUILTIN_KEYBLOB` (`src/core/CMakeLists.txt:502`, `key.cpp:23`), which is OFF. |
| 1 | PASS with B1, S1, S5 | `tests/gate_f2.py:160-192` covers every f1 bullet. Pins and drop list come from `repo/core/PIN` (`:93`, `:172-173`), never typed. Patch set compared both ways (`:104-108`); 0007/0008 required (`:109-111`); cache regex `:[A-Z]*=` (`:125`); `.o.d` at least 1000 and basenames (`:130-141`); windows parsed from the reading copy, with a FAIL under 128 bytes (`:59-88`); strings (`:144-157`); otool (`:183-184`); link.txt (`:185-191`). It ran first and passed (`gate_f2.out`: `PASS keyblob all f1 checks hold`; `main` breaks on a keyblob FAIL at `:535-538`). Import: no gate_c or libazahar import at load, but `:19-20` prepends two paths to `sys.path` (S1). |
| 2 | PASS | `def_names` reads `libretro.osx.def` lines starting with `_` (`:220-222`). `symbol_findings` compares the sets both ways (`:236-238`), so an extra export fails. Only the plan's three lazpy names are typed (`:229`). |
| 3 | PASS | azhost: `apply_lazpy_profile` (`host/azhost_main.c:468-479`) runs `azh_stats` and returns at once unless `is_lazpy_core` and not `none`. It reuses `apply_profile`, so errors have the same message and exit code. Order: lazpy, then `--profile`, then `--opt` (`:513-519`); default `:13`/`:158`; help `:41`. Worker: `option_plan` (`python/libazahar/_worker.py:27-31`) is used at `:37` after `azh_open`, before `azh_boot`. `_paths.lazpy_profile` (`_paths.py:51-63`): `none` gives None; a missing file named by the variable is a HostError; a missing default gives None. The no-shared-key test is `test_lazpy_profile.py:51-54` (it also asserts 6 keys). |
| 4 | PASS (N13) | `git diff --stat` shows no change to `host/api.c` or `tests/python/conftest.py`. `emulator.py:175` uses `self._close(min(self.timeout, 5.0))`, exactly the plan's call. |
| 5 | PASS with S3 | Stock branches of `gate_c.py` are unchanged (moved under `else`, `:258-262`; c4 `:207`). Ours: c4 `:201-206` (rc 0, `debug_text`, last < 600). f1 is stricter than stock's (rc 10, 9 summaries, `guest_exited`, `(16)`). f3 uses the summary's `last` as the plan allows. f2 at `:253` checks the missing exit-path line and stop code 4, but only *prints* `exit_code` (0), where stock asserts `== 10` (S3). `c_values` takes `sums[:8]` on ours (`:245`), the same batches stock has. The D twin is `test_c_checks.py:142-146`; the stock c4 test is untouched. |
| 6 | PASS | r1: shot sha256s plus byte-equal `log.txt` (`gate_f2.py:359-369`); summaries compared field by field with exactly `wall`, `fps`, `wall_ms_mean` dropped (`:371-376`; N3). r2: compares b1 to b2 on lines and shots (`:453`), and bounds `t_state < 2.5` per chain (`:455-456`). The state comparison skips exactly `HEADER_BYTES = 256` (`:28`, `:459-462`). |
| 7 | PASS | d3 = summary `last` - (ready.v + c_min), with c_min from batches 2-9 (`:314`, `:326`). d4 compares batch 1's `last` and its `last 1:` line across the two runs (`:331`). The SD stop is a RECORD (`:335`). Output: 201/201, d3 = 0 both runs. |
| 8 | PASS (N2, N4) | `batch.sh` greps `runs/c-gate` straight after gate_c and `runs/d-pytest` straight after pytest, both before the smoke. gate_f2 greps its own azhost and r2 host.logs (`:265-278`, `:436-437`). `exitpath-ours.txt` is 0 bytes. The two host.logs that hold the line now (`c-gate/f`, `d-pytest/test_f_guest_exit`) are the stock smoke's: version `2126.2`, written 01:21, after the greps. The text is a substring of `host/env.c:44` minus `[error] `. |
| 9 | PASS with notes (N5, N11) | `gate_c.run_azhost` is reused (`:273-278`); exit is non-zero on `gate_c.failed` (`:539-543`). Every part ran under `runs/f2/hold_slot.py`, one at a time (`batch.sh`), with the batch at nice 15. `build.exit` dates from 01:06; the first emulator run was after 01:09 (`progress.md`). r2 copies `sys/` minus `sdmc` (`:422`). No core/ change, no item file touched, nothing committed. One exception: `runs/f2/rerun.sh` ran D's `test_state_boot` from MAIN, which wrote MAIN's ignored `runs/d-pytest/` (N11). |

## BLOCKER

- **B1, `tests/gate_f2.py:176`: the drop check passes on a wrong tree path.** `(tree / entry).exists()` is False
  for every entry when `tree` does not exist. With `tree=/nonexistent/tree`, `keyblob_findings(...)` returned `[]`
  (I ran it). Phase 4's `release_check` imports this function, so a mistyped path would pass a release.
  Fix: before the comprehension, add
  `if not (tree / "CMakeLists.txt").is_file(): bad.append(f"tree: {tree} is not the unpacked build tree")`.
  Then use `os.path.lexists(tree / entry)`, so a dangling link counts as present. Rerun `--only keyblob,symbols`
  (no emulator).

## SHOULD

- **S1, `tests/gate_f2.py:19-20`: `sys.path` changes at import.** Importing the module prepends `<repo>/python` and
  `<repo>/tests`, so in `release_check` the checkout's `libazahar` would shadow an installed one. Fix: move the two
  inserts into a `_setup_paths()` helper, called first in `main()` and in `gc()`/`r2_chain`/`scen_cross`.
  `keyblob_*` need neither path.
- **S2, `tests/python/test_lazpy_profile.py:57-66`: the nice test is half a test.** It asserts `>= 10` from nice 20,
  so a version that lowered 20 to 10 would pass. Fix: assert `== 20`. Add a below-floor case run in a subprocess:
  `p = os.getpriority(os.PRIO_PROCESS, 0); print(_worker.raise_nice_floor(p + 1), os.getpriority(os.PRIO_PROCESS, 0))`,
  expecting `p+1 p+1` (skip when p is 20). Also call `raise_nice_floor(floor=p - 1)` and expect `p` (never lowered).
  The function itself is right: `_worker.py:118-124` only raises the nice value, works from any start, and does not
  call `os.nice(0)`.
- **S3, `tests/gate_c.py:253`: our-core f2 does not assert `exit_code`.** Only `env.c` `exit_path` writes it, and
  that path does not run on our core, so the map holds 0. Fix: add `and m["exit_code"] == 0` to the condition, which
  makes it as strict as stock's `== 10`. Rerun `gate_c.py --core OURS --only f` (one short run; fold it into the
  quiet rerun).
- **S4, `core/README.md:48-49` (MAIN, step 0): the licence lines contradict each other.** One line says a published
  binary "ships with the unchanged source tarball plus these patches". The unchanged tarball holds the dropped key
  blob and certificate headers. `:51` correctly says "the tarball minus the drop list". Fix: in `:48-49`, write
  "ships with its corresponding source (`:51`)" in place of "the unchanged source tarball plus these patches".
- **S5, `tests/gate_f2.py:87`: a window FAIL prints the window's offset into the key array.** It only prints on a
  failure, but the rule is never to print key or certificate offsets. Fix: use the message
  `f"windows: the core holds window {k} of {array}"`.

## NICE

- N1 `_worker.py:129`: `raise_nice_floor()` sits outside `main`'s try, so an OSError would kill the worker with no
  `fatal` message. Setpriority upward cannot fail for one's own process on macOS, so wrap it: on `OSError`, carry on.
- N2 `gate_f2.py:483-489`: `scen_cross` does not grep its our-core host.log (`cross/y`). I grepped it: no exit-path
  line. Fix: call `note_exitpath(wd / name / "host.log")` when `core` is ours.
- N3 `gate_f2.py:370-376`: the summaries are compared as parsed dicts. Ints parse the same either way, but comparing
  the raw lines (keep them in `run_azhost`'s result, or rebuild them) matches the plan's wording.
- N4 `gate_c.py:27`: `EXIT_PATH_LINE` is a typed copy. Add a pure test that asserts the text appears in
  `host/env.c`.
- N5 `runs/f2/hold_slot.py` (not committed): `range(max(n, 1))` with `n = cap - 1` tries slots 0..cap-2, one fewer
  than the plan, and it sleeps 0.1 s per busy slot. It is replaced by step E's `tools/hold_slot.py` after the merge.
- N6 r2: record `os.getpriority`, the load and a plain-boot `t_core_start` beside `t_state` (D's `fixed_ratio`). Then
  a run slowed by load can be told apart from a regression without a rerun.
- N7 `tools/build-core.sh:77,143-157`: `tools/untar_checked.py`, which writes the tree, is in neither the STAMP nor
  `build.inputs`, nor in the clean check. For Phase 4.
- N8 `core/patches/0008-lazpy-no-key-loading.patch:16-32`: the hunk's removed lines quote upstream's built-in
  key-blob branch. They are public GPL source and the IP consult read 0008, but `release-legal-audit` should rule
  on it explicitly.
- N9 `gate_c.py:266-271`: when `nm` fails (wrong path), `core_kind` silently answers `stock`. FAIL instead when the
  file is missing.
- N10 RECORD worth a lesson: on our core the two chains' `s.state` bodies differ after byte 256 (267631 vs 265022
  bytes; in the rerun, 265020 vs 265025), although a1 == a2 and b1 == b2. Exact repeats hold for what the guest does
  and what it shows, not for the state bytes, so nothing may hash state files as an identity. Only header byte 32
  differs, the save time.
- N11 `runs/f2/rerun.sh` ran D's `test_state_boot` from MAIN, writing ignored files under MAIN's `runs/d-pytest/`.
  The stock control is useful, but it breaks "never write in MAIN" unless the main loop asked. `quiet-rerun.sh`
  repeats it, and it waits with a `sleep 60` loop (rule: no sleep polling; use one Monitor until-loop).
- N12 the plan's `pytest -q` hides `pytest_report_header`, so `pytest-ours.out` has no `kind=lazpy` line. Other
  evidence covers it: 24 of the 26 host.logs in `runs/d-pytest` say `2126.2-lazpy.1`, and the 2 stock ones are the
  smoke's. For the gated run, drop `-q` (the plan's command, not the builder's error).
- N13 `emulator.py:175` comment: a stalled unload costs up to 10 s, not 5 s. `_client.close` polls 5 s, then waits
  `REAP_S` = 5 s before the SIGKILL. To make it 5 s in total, bound the reap wait too (D's file).

## r2's `t_state` (Guy's 2.5 s bound, H5)

The check is built as the plan says. `t0` is taken after the `sys/` copy and around the `Emulator(..., state=...)`
constructor only (`gate_f2.py:422-426`), the bound is a strict `<` per chain, and D's definition is kept.

What the time is made of (`[info] state load` lines; `host/state.c:438-458`):
- **`drain_ms` is not only a drain.** `restore_core` calls the core's `retro_serialize_size()`, which in Azahar runs
  `DrainAsyncOperations` **and then a full `SaveStateBuffer()`**, whose result the load throws away
  (SRC `citra_libretro/citra_libretro.cpp:692-709`). That is a whole serialize and compress, CPU-bound, before
  every load.
- Then `unserialize_ms` is a full `LoadStateBuffer` (`:722-737`), also CPU-bound. The rest is worker spawn, Python
  import, the core dlopen, Vulkan/MoltenVK init and the app boot.

| run | load (1 min) | t_state | drain | unserialize | rest |
|---|---|---|---|---|---|
| D quiet (item 300 notes) | low | 1.47-1.68 | 0.39-0.44 | ~0.60 | ~0.5 |
| batch r2.1 (ours) | 28 | 2.80 | 0.84 | 0.80 | 1.15 |
| batch r2.2 (ours) | 28 | 1.91 | 0.48 | 0.77 | 0.66 |
| rerun r2.1 (ours) | 46 | 2.60 | 0.91 | 1.02 | 0.68 |
| rerun r2.2 (ours) | 46 | 4.88 | 1.17 | 1.99 | 1.71 |
| rerun D `test_state_boot` (**stock**, MAIN) | 46 | 3.26 | 0.99 | 1.38 | 0.89 (t_core_start 1.14 vs 0.40-0.50 quiet) |

Every component grows together, by 1.2-3.3x, and the stock core fails the same bound in the same window. The
chain order does not explain it: chain 1 was slower in the batch, chain 2 in the rerun. The cold-cache `read_ms`
(1.6 ms vs 0.2 ms) and `sd_ms` (up to 13 ms) are negligible. Nothing on our core's side explains it; the cause is
CPU contention on a process at nice 15-20.

The quiet rerun is the right test. Expect about 1.5-1.9 s. Margin is thin, so record N6's numbers with it.

On D 3.3's question: `drain_ms` is 24-35% of `t_state`, under half, so by the plan's rule a drain-only export is not
a Phase 4 item. But "drain" is mostly a throwaway full save. A lazpy export that only drains, called in place of
`serialize_size` in `restore_core`, would cut about 0.4 s quiet and 0.5-1.2 s loaded. Worth one line in item 320's
notes as a cheap margin if the quiet rerun lands near 2.5.

## Merge with step E (a74aaec)

No file is touched by both. E: `host/png.c`, `host/run.c`, `host/azh_pure.h`, `_client.py`, `__init__.py`,
`_slots.py`, `pool.py`, `tools/hold_slot.py`, `tools/speed_table.py` and three tests. F2: `host/azhost_main.c`,
`_paths.py`, `_worker.py`, `emulator.py`, `tests/gate_c.py`, `test_c_checks.py` and two new files. Semantic points:

1. **Slots and `t_state`.** After E, `WorkerClient.spawn` calls `_slots.acquire()` (`_client.py`, E's spawn), so
   every `Emulator(...)` takes a machine slot inside D's and F2's `t_state` window. A slot wait then counts as load
   time. Worse, gate_f2 run under an outer `hold_slot` holds a slot while its Emulators need a second one: with
   `LAZ_MAX_INSTANCES=1` it waits until the slot timeout. Fix after the merge: run gate_f2 without the outer helper
   (the Emulator runs take their own slots), and wrap only the azhost runs (`gate_c.run_azhost`) in
   `tools/hold_slot.py`. Subtract `<b>/slot.txt`'s `waited_s` from `t_state`, or record it beside it, in both
   `gate_f2.py` r2 and D's `test_state_boot`.
2. The worker's argv gains `argv[3]` (the slot fd). F2's `_worker.main(fd)` and the snippet read `argv[1:3]`, so
   this is compatible. E leaves `_worker.py` alone, so F2's `raise_nice_floor` wins with no conflict. E's g4 check
   (worker nice >= 10) holds with it.
3. E's `run.c` adds a `batch frames= wall_ms= ...` line to **host.log** and sets the PNG level default to 1. F2
   parses stdout summaries plus only the host.log lines `core ... version`, `option ` and `state load`, so nothing
   clashes. r1's RECORDed shot hashes change after the merge; the comparison is within a run, so it is unaffected.
4. E leaves `_client.close` unchanged, so F2's `Emulator._close(graceful)` works as is.
