# Phase 3 plan, review 2 (of revision 1, commit 8a16f9e)

Opus review, 2026-11-12, about 21:20-22:10. Reviewed: `docs/plans/phase-3.md` (index), `phase-e.md`, `phase-f2.md`,
`phase-g.md`. Checked against: SRC = `dl/azahar-src/unpacked/azahar-unified-source-2126.2/` (the reading copy),
PATCHES = `core/patches/0000-0006`, main at 254b76b (C merged at 7584a8d, P9 committed at e40e59c), MAIN's
`build-core/` (the 21:09 keys-off build), the build tree `dl/azahar-src/build-src/`, step D at `../libazahar-py-d`
(88cdbe6), `docs/reviews/phase-3-review-1.md`, `docs/reviews/phase-4-review-1.md`. `phase-2-d-as-built.md` is still
"(in progress)" (7 lines), so nothing of D's as-built review is used here. Nothing built, run or committed.

Grades: **blocker** (a gate cannot pass as written, or the binary we gate is not the one that may ship), **should
fix** (a builder would ask, or a gate or a record is weaker or staler than it says), **nice**.

**Counts: 3 blockers, 7 should fix, 10 nice.** Review 1: all 26 findings are fixed in the text (section 2). Verdict
in section 7.

## 1. Own findings

### Blockers

- **B1. F2 gates a binary that still carries Nintendo's ClCertA, and the plan's step 0 is stale.**
  phase-3.md:43-44, 103-109, 121, 154-158, 249, 362-363; phase-f2.md:10-11, 22-28, 55-59, 170-174, 206-214. The
  plan's "step 0" (the P9 rebuild) is done (e40e59c, dylib 21:09, 19,145,936 bytes, cache `OFF`, 0 `.o.d` naming
  `default_keys.h`). But Phase 4 review 1 B1 found, and I confirm in SRC, that `src/core/hle/service/http/
  ctr-common-1-cert.h` (`ctr_common_1_cert_bin[1264]`) and
  `ctr-common-1-key.h` (`ctr_common_1_key_bin[1232]`) are included with no
  `#ifdef` at `http_c.cpp:37-38` and copied in the fallback branch at `http_c.cpp:2281-2289` (`if
  (file_result.Failed()) { LOG_ERROR(..."ClCertA file missing, using default"); ... memcpy ... }`). MAIN's
  `build-core/build/src/core/CMakeFiles/citra_core.dir/hle/service/http/http_c.cpp.o.d` names both headers today.
  The main loop treats removing them as a must. As written, F2's f1 passes on the 21:09 binary (it checks only the
  key blob), so F2 would gate, and G and E2 would measure, a binary that cannot ship. **Fix:** section 4 of this
  file gives the exact placement (a new main-loop step 0, patch 0007, the drop list, `build.inputs`, and F2's f1
  additions).
- **B2. `lazpy_core` resolves to `<worktree>/build-core/...`, which no worktree has.** D's fixture
  (`../libazahar-py-d/tests/python/conftest.py:76-84`) takes `LAZ_CORE` when it names our core, else `REPO /
  "build-core" / "azahar_lazpy_libretro.dylib"` with `REPO` = the checkout the tests run in. Our core lives only in
  MAIN's `build-core/`. So (a) F2's f9 stock smoke (`LAZ_CORE=STOCK ... -k "c4 or guest_exit or lazpy"`,
  phase-f2.md:48-51) selects F2's own our-core twin, whose `lazpy_core` is missing, and under
  `LAZ_REQUIRE_EMULATOR=1` it **fails**; (b) G's gate 2 command as written (phase-g.md:27, no `LAZ_CORE`) fails m1-m4,
  m6, m7 the same way (G2's batch sets `LAZ_CORE=OURS`, but the gate line, the as-built reruns and a resumed builder
  follow section 1). Phase 2 needs no change. **Fix (one line in each step 0):** after seeding `dl/` and `vendor/`,
  `mkdir -p build-core && ln -sf MAIN/build-core/azahar_lazpy_libretro.dylib build-core/azahar_lazpy_libretro.dylib`
  (ignored path; the name holds "lazpy", so `_kind` says lazpy; `is_file()` follows the link). Put it in phase-e.md
  step 0 (:298-302), phase-f2.md F2-0 (:207-211), phase-g.md step 0 (:280-283), and say in each brief that MAIN's
  `build-core/` stays read-only (the link is the worktree's).
- **B3. E1's slot makes D's fake-worker tests take real machine-wide slots, so G1 hangs while E2 runs.** phase-e.md
  3.2 (:100-108) puts `_slots.acquire()` in `WorkerClient.spawn`. D's `test_client.py:20-23` builds `WorkerClient(...,
  argv=argv)` with the fake worker, so with E1 every non-slow `test_client` spawn acquires a slot in the **real**
  folder with the default cap (the tests set no `LAZ_SLOT_DIR`; `acquire` reads the test process's environment, not
  the `env` dict). By the plan's own schedule G1 (and its step-0 baseline, phase-g.md:282-283) runs exactly while E2's
  live fixture holds 3 real slots (phase-e.md:209-211) and then while the table holds up to 4 (phase-e.md:239-242):
  each fake spawn then blocks for up to `LAZ_SLOT_TIMEOUT` (3600 s). The same hits E1's own gate 1 whenever another
  session holds slots, and anyone running the pure suite beside a pool. A sonnet stuck here will "fix" it outside
  its files. **Fix (E1, `_client.py` only):** `WorkerClient(..., slot: bool | None = None)`; `None` means "take a
  slot only for the real worker" (`argv is None`); s6 (phase-e.md:191-192) passes `slot=True` with a private
  `LAZ_SLOT_DIR` (monkeypatch); the docstring says fake workers never touch the cap. Add to phase-e.md section 12
  item 2: "a fake-worker spawn takes no slot unless asked".

### Should fix

- **S1. Stale facts and pointers** (they are what builders and the as-built reviews check):
  phase-3.md:19 "step D on `step-d` (c1e614e)" (now 88cdbe6, D3 done, 69 passed; as-built review running);
  :43-44 and :154-158 "commit `tools/build-core.sh` (P9) ... start the rebuild" (done at e40e59c); :105-107 "an
  uncommitted edit in MAIN ... The patches do not change, so the STAMP holds and the tree is not re-unpacked" (both
  false once 0007 lands: the STAMP hashes the patches, `tools/build-core.sh:68-70`); :121 "already edited in MAIN; the
  main loop commits it"; :249 F5 "planned (the P9 rebuild)" (now: done, 21:09, 19,145,936 bytes; replaced by step 0's
  build); :362 "today's build has `ENABLE_BUILTIN_KEYBLOB:BOOL=ON`" (now OFF at `CMakeCache.txt:728`) and "the blob's
  first 16 bytes ... of today's dylib" (of the 19:40 build); :363 "(uncommitted)" and `build-core.sh:95-112` (the
  committed lines are :95-112 for configure, :110-112 for the `.o.d` guard). Rewrite them to the state after step 0.
- **S2. F2's r2 does not follow D's state-boot recipe, but gates Guy's 2.5 s bound that was set on it.**
  phase-f2.md:190-199 builds b in a fresh folder; D's `test_state_boot` copies a's `sys/` minus `Azahar/sdmc/` into b
  first (`../libazahar-py-d/tests/python/test_state.py:48-51`; phase-d.md:365-367: "the shader cache and NAND come
  along, as in Gen3D's reused instance folders"). H5's `t_state < 2.5 s` was measured with that copy; without it b
  may pay a cold shader cache and f6 can fail for a reason that is not the core. **Fix:** r2 step 2 starts with the
  same `shutil.copytree(a/sys, b/sys, ignore=shutil.ignore_patterns("sdmc"))` and RECORDs the copied folders. Also
  say that `seed(...)` in a script is `testapp_log.write_control(folder, **keys)` (`tests/testapp_log.py:11`; D's
  fixture does exactly that, conftest.py:99-107).
- **S3. The debug-text stop's {0, 1} tolerance is an unlisted refinement.** PLAN.md:314 says "the debug-text stop
  fires on the exact frame"; phase-f2.md:42-44 and :181 accept `last - (ready.v + c_min)` of 0 or 1, and phase-3.md:32
  says "exact". The tolerance is reasonable (the host frame of a guest line depends on where the slice ends,
  `citra_libretro.cpp:287-306`), and exactness is carried by d4 (equal across two runs). **Fix:** add **R4** to
  phase-3.md section 5: "exact" = the same host frame on every run (d4) and within one frame of the ready line's
  host frame (d3); without it F2's as-built review must flag d3.
- **S4. Patch 0008 (no key loading) needs a decision before step 0's rebuild, and a default.** Every key path goes
  through `HW::AES::GetKeysStream()` (`core/hw/aes/key.cpp:292-314`; RSA at `core/hw/rsa/rsa.cpp:101`, ECC at
  `core/hw/ecc.cpp:65`), so 0008 is one hunk making it return `std::istringstream("")` (plus its notice line). Our
  runs never have an `aes_keys.txt` in `sys/`, so it changes nothing F2 can see; it does stop users running
  encrypted titles with their own keys. **Fix:** Q6 for Guy in section 11 (ask with the ip-legal consult, Phase 4
  review 1 S17): "build 0008 into the same rebuild?" Default **yes** (the conservative side, as the main loop's
  default for G1; reversible by dropping the patch). If it is not in step 0, Phase 4 owns a second rebuild plus a
  `gate_f2.py --only keyblob,symbols,version` and a short our-core smoke; say so in section 12.
- **S5. Section 12 does not give Phase 4 what it asks for.** Missing: (a) the core supply chain: patch 0007 (and
  0008 or not), `LAZ_CORE_DROP` in `core/PIN`, the `build-core/build.inputs` format, `keyblob_findings`'s final
  signature and its windows (Phase 4's `release_check` imports it instead of re-implementing them, Phase 4 review 1
  B1/S1/S2); (b) the environment variables Phase 3 adds: `LAZ_MAX_INSTANCES`, `LAZ_SLOT_DIR`, `LAZ_SLOT_TIMEOUT`
  (default 3600), **`LAZ_PNG_LEVEL`** (missing), `LAZ_LAZPY_PROFILE`, and that **no `LAZ_LAZPY_CORE` exists** (Phase 4
  R12 lists it from review 1's B4; D took `LAZ_CORE` instead); (c) `SlotTimeout`: a subclass of `HostTimeout` (so
  `except HostTimeout` catches it), its text "no libazahar slot free after <s> s: all <cap> are held; see <dir>",
  `.op == "slot"`, `.seconds`; (d) states both ways: an ABI-3 host loads metas with `abi` 2..3, an ABI-2 host
  refuses an ABI-3 state (`host/state.c:395-396`, `meta.abi > AZH_ABI_VERSION`). Paste-ready text in section 6.
- **S6. E's brief has no rule-T line for its own review reruns.** F2 has one (phase-f2.md:235-237, "the resume
  message says when the machine is free"); phase-e.md step 3 (:324) does not, yet E's reruns are the ones that
  queue behind G2 (phase-3.md:176). **Fix:** copy F2's sentence into phase-e.md step 3, naming
  `../libazahar-py-g/runs/g-batch.rc` as the file to wait on if the message says G2 is running.
- **S7. The merge plan assumes E finishes before G.** phase-3.md:175-182 ("merge `step-e` into main (clean: G is
  not merged)"). G can finish first (G2 needs only E2's table, and E's review and fixes come after). **Fix:** one
  line in step 6: "If G is done first, merge step-g first (its tree holds E1's commit, the same sha as step-e's);
  step-e's later merge is still clean because E's fixes to G's shared files are held (step 5) and E2 edits only
  `DEFAULT_CAP` and E's own files."

### Nice

- **N1. Citations.** `libretro_window.cpp:68-71` is `src/citra_libretro/emu_window/libretro_window.cpp:68-71`
  (phase-3.md:354, phase-e.md:44); the loop is `citra_libretro.cpp:282-306` and its end condition is
  `emu_window/libretro_window.cpp:327-331` (phase-3.md:354 says `citra_libretro.cpp:282-331`); `Makefile:41` is
  `Makefile:42` (phase-3.md:239, phase-e.md:59); the ClCertA fallback is `http_c.cpp:2281-2289` (Phase 4 review
  wrote 2280-2288). Every other SRC fact I checked holds: core_timing.h:37, 40-42, 184; core_timing.cpp:37-44;
  settings.h:490-491, 503-507, 537, 659; backend.cpp:353-357; hle_ipc.h:306, 348; gpu.cpp:488-498;
  libretro_vk.cpp:710-711; memory.cpp:173-229 (flush :213-217), 245-254, 824-837; memory.h:34; kernel.h:319;
  savestate.cpp:291-304; CMakeLists.txt:154; citra_libretro/CMakeLists.txt:32, 96; GenerateBuildInfo.cmake:13-16,
  40-55; shared_page.cpp:34-63; core_settings.cpp:1133. PATCHES 0001 (signatures, -1/-2/-3, cap, wrap, every page
  checked first, try/catch), 0002 (the six keys of `core/options-lazpy.txt`), 0005 (`"-lazpy.1"` joined at run
  time) as the plan quotes.
- **N2. Say the watch row's frame index is 1-based.** `host/run.c` `run_frames` loops `for (i = 1; i <= b->frames;
  ...)`. phase-g.md:164-167 ("when batch frame `i % every == 0` ... if the last frame run has no row yet, write it")
  gives m2's exactly 60 rows only with that `i`; a 0-based reading gives 61 and trips the `rows_max` assert. One
  clause: "(`i` is `run_frames`'s 1-based batch frame)".
- **N3. `gate_f2.py`'s exit code must count `gate_c.run_azhost`'s timeouts.** run_azhost reports a timeout through
  `gate_c.report`, which bumps `gate_c.failed`, not gate_f2's own counter (`tests/gate_c.py:26-31, 49`). Say:
  gate_f2 exits non-zero if `gate_c.failed` is non-zero too (or checks `rc == -9`).
- **N4. Gate the `/Users/` count now.** It is already 0 on the 21:09 build (item 300's notes) and Phase 4 gates it
  to 0; make f1 FAIL on > 0 instead of RECORD (phase-f2.md:27-28). Costs nothing.
- **N5. A direct marker for 0007:** f1 also checks that `strings -a OURS` holds no "ClCertA file missing, using
  default" (the removed log text).
- **N6. G's bind and `is_lazpy_core`.** A's detection uses `lazpy_read_memory` alone (`host/core.c:100`);
  phase-g.md:169-171 says "both must be found, else our core is treated as stock". Say whether `is_lazpy_core` is
  then reset (it also drives F2's profile plan), or that a half-exported core is a hard `AZH_E_CORE` at open.
- **N7. Patch 0007's notice and the version.** 0007 carries its own "Modified by libazahar-py, 2026: ..." line under
  `http_c.cpp:1-3` (0000's pattern; GPLv2 2(a)), and `core/README.md` gains the 0007 (and 0008) rows and the drop
  list. The version suffix stays `-lazpy.1` and `LAZPY_REV=1` (nothing has been released; `host/pins.h` and f1/f3
  are keyed to it; `build.inputs` tells builds apart). Say so, so nobody bumps it.
- **N8. Install the dylib atomically.** `tools/build-core.sh:114-117` copies over `build-core/azahar_lazpy_libretro.dylib`
  in place; a process that has it mapped (another session, a stray test) can be killed on page-in. `cp` to
  `$DYLIB.tmp`, strip and sign that, then `mv -f`. Two lines in step 0's edit.
- **N9. The phase-end suite runs the 3-instance pool test three times.** phase-3.md:184-187: "the full pytest with
  `LAZ_CORE` set to each core in turn" plus "E's live pool test once". Add `--ignore=tests/python/test_pool_live.py`
  to the two per-core runs (about 6 min machine).
- **N10. Say "never run `tools/build-core.sh`" in the three briefs.** In a worktree, `BUILD_SRC` is
  `$ROOT/dl/azahar-src/build-src` (`build-core.sh:43`) and step 0 links `dl/azahar-src` to MAIN's, so a builder's run
  would `rm -rf` MAIN's build tree (`:70`) and start a full build. The briefs say "the build is the main loop's";
  make it a prohibition.

## 2. Review 1's findings against revision 1's text

Every finding is taken, and the text says so where a builder will read it:

| Finding | Where it is fixed | Verdict |
|---|---|---|
| B1 host_paths ignores `LAZ_CORE` | H1 (phase-3.md:213-217); D's conftest.py:54-64 does it | fixed (but see B2 above: the `lazpy_core` fallback) |
| B2 nice is an increment | H2; g4 `>= 10` (phase-e.md:32-33, 227); D's `_worker.py:111-112` | fixed |
| B3 exit-path grep sees stock files | phase-f2.md:223-227 (grep right after each our-core part) | fixed |
| B4 stock test in an our-core run | phase-g.md:28-29, 249-251 (explicit `lazpy_core` / `stock_core`) | fixed |
| B5 `test_mem.c` cannot link | pure `host/watch.c` in `TEST_SRC`; `test_main.c/.h` in G's rows (phase-3.md:135-137) | fixed |
| S1 overlap seams | rule T (phase-3.md:79-86); G bound 150 min; timeout ends G's run | fixed (E's own rerun line missing: S6 above) |
| S2 E2 without P8 | E resumed after step-f2 merges, main merged first (phase-3.md:170-172) | fixed |
| S3 `wall_ms_max` | `wall_ms_mean` in f5, r1, H4, C6 | fixed |
| S4 png.c is pure | `azh_png_level()` in png.c, the log line in run.c, `azh_pure.h` in E1's rows | fixed |
| S5 env read at import | phase-e.md:83-84; fixture order :209-214 | fixed |
| S6 merging main into G mid-step | merge only at "G done"; held E fixes (phase-3.md:175-182) | fixed |
| S7 ABI 3 refuses ABI-2 states | H3; D's state.c:395 accepts 2..ABI; m7 | fixed |
| S8 `HostTimeout` text | `SlotTimeout(HostTimeout)` with its own text (phase-e.md:80, 91-93) | fixed |
| S9 C(g) row | dropped; c4 named | fixed |
| N1-N12 | phase-3.md section 13 lines 427-441; each checked in the briefs | fixed (N1's "F2-0 already answered" is undone by 0007: F2-0 checks a new build again, which is right) |
| Q4, Q5 | stock smoke (f9); 4 MiB area sized from the layout | fixed |
| Section 10 (Phase 2 asks) | D took B1/B4 (fixtures), B2 (nice), S7 (abi range); C's state boot fixed (D3 passes) | fixed |

No review-1 finding is unfixed. The only regressions are the stale facts of S1 (written before P9 and D3 finished).

## 3. The plan against what exists now (main 254b76b, D 88cdbe6)

**Phase 2's holds, each confirmed in D's code at 88cdbe6:**

| Hold | Where | Verdict |
|---|---|---|
| H1 | `tests/python/conftest.py:47-51` (header `core=<path> kind=<kind>`), `:54-64` (`host_paths` from `_paths.core_path()`), `:67-73` (`stock_core`), `:76-84` (`lazpy_core`); `test_c_checks.py:134-136` passes `core=stock_core` | holds; the fallback path is the checkout's, so worktrees need B2's link |
| H2 | `python/libazahar/_worker.py:111-112` (`if os.nice(0) < 10: os.nice(10 - os.nice(0))`) | holds |
| H3 | `host/state.c:395-396` (`meta.abi < 2 \|\| meta.abi > AZH_ABI_VERSION` refused) | holds |
| H4 | `host/azhost_main.c:565-566` (`frames= wall= fps= shots= stop= first= last= vblanks= wall_ms_mean= batch= msg=`) | holds |
| H5 | `tests/python/test_state.py:85-88` (`t_state < 2.5`), `:71-72` (`runs/d-pytest/state-times.txt`), the ratios recorded only | holds (recipe includes the `sys/` copy: S2) |
| H6 | `host/api.c:578-584` (`azh_stats` refuses only `AZH_PH_NONE`) | holds |
| H7 | `python/libazahar/emulator.py:166-167` then `close()` at `:306-308` (`self._client.close(self.timeout)`) | holds; F2 shortens it to 5 s as planned |

Also checked: D2 (`_client.py:28-29` snippet reads only `argv[1]`, `argv[2]`; `:42-44`; spawn `:108-126`; the fake's
argv is a callable and `fakeworker.py:13` reads only `argv[1..4]`, so an appended slot fd is harmless); D5
(`errors.py:29-38`); D6 (`run` frames 1..`MAX_FRAMES` = 100,000,000, so E's `run(10_000_000, wall_limit=60)` is
legal; `timeout` is a heartbeat, so a 60 s batch is fine); `gate_c.run_azhost` runs azhost with `cwd=ROOT`
(`tests/gate_c.py:43`), so F2's relative `--lazpy-profile` default resolves; `test_state.py:121` still has the
literal `"abi=2\n"` (G's one-line row covers it). No `filterwarnings = error` in `pyproject.toml`, so a
`LoadWarning` on a loaded Mac does not fail tests.

**Main and MAIN's build:** `build-core/build.exit` 0 (21:09), `CMakeCache.txt:728` OFF, 1,659 `.o.d` files, one
names `ctr-common-1-*` (http_c.cpp.o.d), none names `default_keys.h`. The generator is Unix Makefiles; its
`citra_core.dir/compiler_depend.make` has phony rules for every header (e.g. line 450591 for `ctr-common-1-cert.h`),
so deleting a header that an old `.o.d` names does not break `make`. `untar_checked.py:59` extracts with
`filter="data"`, which keeps the tarball's mtimes (the tree's files say Oct 9), so a re-unpack recompiles only the
patched files and what includes them.

## 4. Phase 4's asks: where each belongs in Phase 3

**The new step 0 ("P9b", the main loop's, before F2 gates):**
1. When: after Phase 2's last emulator run (D's as-built reruns) and before F2's emulator work; it is a timed part
   (rule T). E1 may run meanwhile.
2. Who: **the main loop** (it already owns `tools/build-core.sh`, phase-3.md:121; a builder cannot do it in a
   worktree without touching MAIN's build tree, N10; the work is about 0.15 h, less than a brief, a worktree and a
   checkpoint). It writes, on main:
   - `core/patches/0007-lazpy-no-default-clcert.patch`: removes `http_c.cpp:37-38` (the two includes), replaces the
     fallback body at `:2282-2288` with `LOG_ERROR(Service_HTTP, "ClCertA file missing"); return;` (the `else`
     branch stays), and adds the notice line under `:1-3` (N7). No other patch touches `http_c.cpp`, so it applies
     after 0006 with `--fuzz 0`.
   - optional `core/patches/0008-lazpy-no-key-loading.patch` (S4): `GetKeysStream()` (`key.cpp:292-314`) returns an
     empty stream; notice line under `key.cpp:1-3`.
   - `core/PIN`: `LAZ_CORE_DROP=src/core/hw/default_keys.h src/core/hle/service/http/ctr-common-1-cert.h
     src/core/hle/service/http/ctr-common-1-key.h`.
   - `tools/build-core.sh`: (a) after the unpack and **before** the patches, delete each `LAZ_CORE_DROP` entry
     (die if an entry is not in the fresh tree, or is absolute or holds `..`); (b) the STAMP hashes the patches **and
     the drop list** (`{ cat "$PATCHES"/*.patch; pin LAZ_CORE_DROP; } | shasum`), so a list change re-unpacks;
     (c) the post-build `.o.d` guard (`:110-112`) covers every drop-list basename, not only `default_keys.h`;
     (d) `--build` writes `build-core/build.inputs` before compiling: `tarball=<sha256>`, `pin=<sha256 of
     core/PIN>`, `script=<sha256 of build-core.sh>`, one `patch <name>=<sha256>` line per applied patch, `drop=<the
     list>`, `head=<git rev-parse HEAD or none>`, `clean=<yes|no>` from `git status --porcelain -- core
     tools/build-core.sh`, and the cmake command line (Phase 4 S3 quotes it); (e) N8's atomic install.
   - `core/README.md`: the 0007/0008 rows and the drop list.
   It checks the stack on a scratch unpack outside `dl/` (`python3 -I tools/untar_checked.py dl/azahar-src/src.tar.xz
   <scratch>`, delete the drop list, `patch -p1 --forward --batch --fuzz 0` for 0000-0007/8: 0 rejects, `grep -c
   ctr_common_1 http_c.cpp` = 0), commits exact paths on main, runs `tools/build-core.sh --detach` in MAIN (it deletes
   the old `build.exit` first, `:25`), and waits in the background on `build-core/build.exit` (bounded 120 min).
   Expected: a re-unpack (the STAMP changed) and an incremental compile of the patched files plus the LTO link;
   the P9 rebuild took 5 min.
3. Section 3 gets one row: `core/patches/0007` (and 0008), `core/PIN`, `core/README.md`, `tools/build-core.sh`: the
   main loop, step 0. The "Nobody touches `core/`" line stays for builders.

**F2 gates it.** phase-f2.md's f1 (`keyblob`) gains, all in `keyblob_findings(build_dir, core, src_root, tree,
drop) -> list[str]` so Phase 4 imports one implementation:
- `build-core/build.inputs` exists; its patch, PIN and script hashes equal the F2 worktree's `core/patches/*`,
  `core/PIN`, `tools/build-core.sh`; it lists 0007 (and 0008 if Q6 said yes); `clean=yes`. RECORD `head`. This is
  also what tells the new build from the 21:09 one (whose stale `build.exit` 0 would otherwise pass f1's file
  checks).
- every `LAZ_CORE_DROP` entry (read from `core/PIN`, not typed) is **absent from the build tree**
  `MAIN/dl/azahar-src/build-src/<SRC_TOP>/` (not `unpacked/`, the reading copy, which keeps them);
- no `.o.d` under `MAIN/build-core/build/` names `default_keys.h`, `ctr-common-1-cert.h` or `ctr-common-1-key.h`;
- OURS holds none of 8 evenly spaced 16-byte windows of each of `default_keys_enc` (`core/hw/default_keys.h:11`),
  `ctr_common_1_cert_bin` and `ctr_common_1_key_bin` (the `0x..` tokens parsed from the reading copy's headers;
  FAIL if a header is missing there, since then nothing was checked);
- `strings -a OURS` has no line holding `/Users/` (N4) and none holding "ClCertA file missing, using default" (N5).
F2's facts gain: `DecryptClCertA()` runs at every boot from the HTTP service's constructor (`http_c.cpp:2507`) and
returns at the missing key slot 0x0D (`:2262-2266`) before the removed branch, so with no keys 0007 changes nothing
the test app can see; F2's whole batch on OURS is the "homebrew needs no keys and no ClCertA" proof. F2's as-built
review also reads step 0's diff on main (the two patches, the script, the PIN line) as checklist item 0.

**Does building from the stripped tree change anything else?** Checked:
- CMake: `default_keys.h` is named only under `ENABLE_BUILTIN_KEYBLOB` (`src/core/CMakeLists.txt:501-503`); the
  `ctr-common-1-*` headers are in no CMake file. So configure works, and turning the option back ON now fails at
  configure (fail-closed, a bonus).
- Make: the phony header rules (section 3) mean the deleted headers do not break the incremental build; http_c.cpp
  recompiles (patched) and its new `.o.d` drops the names.
- Order: delete before patching; 0007 must not touch a dropped file (it does not).
- The reading copy `unpacked/` keeps the headers (reviewers' SRC, the byte windows' source); only `build-src/` is
  stripped. The Corresponding Source becomes tarball + drop list + patches: Phase 4's P10(a) must ship exactly that
  (no Phase 3 change).
- `rm -rf build-src` on the re-unpack: nothing in Phase 3 reads `build-src/` except f1, after the build.
- Nothing else changes: the exports, the version, P8's profile and the Phase 2 behaviour stay; the core is still
  `-lazpy.1` (N7).

**Section 12 on ABI-2 states and SlotTimeout:** S5 above (and section 6, item 6).

## 5. The step briefs

- **Followable without asking:** yes, after B2, B3, S2 and N2. The briefs name every file, command, rc file and
  report field; the ownership table matches the briefs row for row (E and F2 share no file; G's shared files are
  edited after E1's and F2's commits are in its tree). The new step 0 adds one main-loop row (section 4).
- **Ownership:** clean, plus step 0's row. E1's `_client.py` change grows by B3's keyword only.
- **Gates that can fail:** every gate has a real failure path (byte compares, the guest-time check, the torn
  bound, the cap rule's CHECK FAIL path, `--plant-red`-style comparisons in D's tests). Two gates failed for the
  wrong reason as written (B2's f9 and G's gate 2 line); B3 makes G1 hang rather than fail. f1 as written passes on
  the wrong binary (B1).
- **Checkpoint reports end the run:** E1, E2, F2, G (and G's "waiting for E2") all end with a report; the main loop
  commits and resumes. Correct.
- **Rule T can be kept:** yes, with S6 (E's rerun line) and with step 0 inside it (the rebuild is a timed part; F2's
  emulator work waits for its `build.exit` and a matching `build.inputs`). One edge: E2's 4-instance row holds all
  4 real slots, so any cap-3 user (G1's fake tests before B3's fix) waits; after B3 only real Emulators wait, which
  is the point.

## 6. Hour-saving pass

| Item | Saves | Verdict |
|---|---|---|
| 0007, 0008, the drop list and `build.inputs` in **one** rebuild (step 0) | Phase 4's second rebuild and a gate_f2 rerun (about 0.1 h agent, 20-40 min machine) | take (S4's default yes) |
| Launch F2 together with E (after `--detach` started): F2 seeds, writes F2-1's code and `gate_f2.py`, then waits with Monitor (bounded 120 min) on `build.exit` = 0 **and** a matching `build.inputs` before f1 and before any emulator run | the rebuild's 10-40 min off the critical path F2 -> E2 -> G2 (0 agent hours) | take |
| The main loop writes the patches (no brief, worktree or checkpoint for 20 lines of diff) | about 0.1 h against a sonnet step | take |
| One `keyblob_findings` (windows parsed from SRC) imported by Phase 4's `release_check` | a second implementation in Phase 4 | take |
| `--ignore=tests/python/test_pool_live.py` in the phase-end per-core pytests (N9) | about 6 min machine | take |
| Cut G2's gate C part (the phase-end suite runs gate C anyway) | about 10 min machine | decline: G changes the host library azhost links (batch and map layout), and gate C on G's tree comes before G's review |
| Cut F2's `stock_r1` record | about 4 min machine | decline: it is the evidence for "stock repeats differ in `s=`/`t=`" that Phase 4's USING fix (its S13) needs |

Hours after revision 2: E 1.11 (B3 +0.01), F2 0.78 (f1's additions +0.03), G 0.85, loops 0.5: about **3.25 h**;
main loop 0.35 h (step 0 about 0.15 plus the choreography 0.2).

## 7. Verdict

**Ready to build after revision 2 takes B1-B3 and S1-S5** (text edits to the four plan files, plus the main loop's
step-0 work, which is code but small and is then gated by F2's f1 and read by F2's as-built review). S6, S7 and the
nice items fit in the same revision. **No third review loop is needed** if revision 2 takes section 8's list as
written: none of the fixes changes a design, and the one new piece of code (step 0) is checked by a gate that can
fail and by F2's as-built review. If revision 2 departs from the list (for example, a builder writes the patches
instead of the main loop), a short opus check of that part only is enough.

## 8. Fix list for revision 2 (paste-ready)

1. **(B1) phase-3.md sections 2, 3, 4 step 0, 8 risk 1, 10, 12; phase-f2.md 1 (f1), 2, 6 (keyblob), 7 (F2-0), 12
   item 1:** replace the done P9 step with step 0 "P9b" as written in section 4 above (patch 0007, optional 0008,
   `LAZ_CORE_DROP` in `core/PIN`, the `build-core.sh` drop/STAMP/guard/`build.inputs`/atomic-install edits,
   `core/README.md` rows; main loop; scratch-unpack check; commit; `--detach` in MAIN; background waiter). f1 =
   `keyblob_findings(build_dir, core, src_root, tree, drop)`: build.inputs matches the worktree's inputs and lists
   0007 (0008), drop-list files absent from `build-src/<TOP>/`, no `.o.d` names any of the three headers, none of 8
   windows of each of the three arrays in OURS, no `/Users/` and no "ClCertA file missing, using default" string.
   Section 3 row: `core/patches/0007` (0008), `core/PIN`, `core/README.md`, `tools/build-core.sh`: main loop, step 0.
   F2's section 12 gains item 0: review step 0's diff on main.
2. **(B2) phase-e.md step 0, phase-f2.md F2-0, phase-g.md step 0:** add `mkdir -p build-core && ln -sf
   MAIN/build-core/azahar_lazpy_libretro.dylib build-core/azahar_lazpy_libretro.dylib` ("D's `lazpy_core` falls back
   to the checkout's `build-core/`; MAIN's stays read-only"). H1's row says the fallback is the checkout's.
3. **(B3) phase-e.md 3.2, section 5 s6, section 12 item 2:** `WorkerClient(..., slot=None)`: a slot only for the real
   worker unless `slot=True`; s6 passes `slot=True` with a private `LAZ_SLOT_DIR`; the docstring says fake workers
   never touch the cap.
4. **(S1) phase-3.md:19, 43-44, 105-109, 121, 154-158, 249, 362-363:** the state after P9 (e40e59c, 21:09,
   19,145,936 bytes, OFF, 0 `/Users/`) and D at 88cdbe6; "the STAMP holds" removed (0007 re-unpacks).
5. **(S2) phase-f2.md r2 step 2:** copy a's `sys/` minus `sdmc` into b before b's `Emulator(...)` (as
   `test_state.py:48-51`), RECORD the copied folders; `seed()` in a script = `testapp_log.write_control`.
6. **(S3) phase-3.md section 5:** R4: "the debug-text stop is exact" = equal host frame across runs (d4) and within
   one frame of the ready line's host frame (d3).
7. **(S4) phase-3.md section 11:** Q6 (0008 in the same rebuild?), default yes; if no, section 12 says Phase 4 owns
   the rebuild and a `gate_f2.py --only keyblob,symbols,version` plus a short our-core smoke.
8. **(S5) phase-3.md section 12** gains: "Core supply chain: patches 0000-0007 (0008: Q6), `LAZ_CORE_DROP` in
   `core/PIN` (the three files deleted after unpack), `build-core/build.inputs` (format in section 4 step 0),
   `gate_f2.keyblob_findings(build_dir, core, src_root, tree, drop)` for `release_check`. Environment: `LAZ_MAX_INSTANCES`,
   `LAZ_SLOT_DIR`, `LAZ_SLOT_TIMEOUT` (3600), `LAZ_PNG_LEVEL` (0-9, default 1), `LAZ_LAZPY_PROFILE`; there is no
   `LAZ_LAZPY_CORE`. `SlotTimeout` subclasses `HostTimeout` (`.op == "slot"`, `.seconds`), text 'no libazahar slot
   free after <s> s: all <cap> are held; see <dir>'. States: an ABI-3 host loads ABI-2 and ABI-3 states; an ABI-2
   host refuses ABI-3 states (`host/state.c:395`)."
9. **(S6) phase-e.md step 3:** "If the opus review asks for fixes, the main loop resumes you; any emulator rerun is
   a timed part (phase-3.md rule T): the resume message says when the machine is free (wait on
   `../libazahar-py-g/runs/g-batch.rc` if it says G2 is running)."
10. **(S7) phase-3.md section 4 step 6:** the "G done first" line of S7.
11. **Nice:** N1 citations; N2 "`i` is `run_frames`'s 1-based batch frame" in phase-g.md 3.3; N3 gate_f2 counts
    `gate_c.failed`; N4 `/Users/` gated to 0; N5 the ClCertA log-text marker; N6 G's half-exported core rule; N7
    0007's notice line, `core/README.md` rows, no version bump; N8 atomic dylib install; N9 `--ignore` in the
    phase-end per-core pytests; N10 "never run `tools/build-core.sh`" in the three briefs.
12. **Hours:** E 1.11, F2 0.78, G 0.85, loops 0.5 = about 3.25 h; main loop 0.35 h (step 0 included). Section 9 adds
    section 6's rows.

## 9. For Phase 2 and Phase 4

- **Phase 2:** nothing blocks Phase 3. Optional: `lazpy_core` could also read a `LAZ_LAZPY_CORE` variable (B2's link
  makes it unnecessary). Still open from earlier lists: `test_state.py:121`'s `"abi=2\n"` literal (G covers it
  either way) and USING's "Stock: exact repeats" (Phase 4 review 1 S13).
- **Phase 4:** drop R12's `LAZ_LAZPY_CORE` and add `LAZ_PNG_LEVEL` and the slot variables; `release_check` imports
  `gate_f2.keyblob_findings` (one set of windows) and reads `build-core/build.inputs` and `LAZ_CORE_DROP` as Phase 3
  defines them; its configure-only check 10 goes (the binary is built from the stripped tree); if Q6 says no, Phase 4
  owns the 0008 rebuild and the F2 rerun; STATUS/USING: ABI-2 states load under ABI 3, an ABI-2 host refuses ABI-3
  states, `SlotTimeout` is a `HostTimeout`.
