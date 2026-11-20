# Phase 8 plan review (laz-803)

Reviewer: opus, 2026-11-18. Reviews `docs/plans/phase-8.md` rev 0 (328 lines) against `docs/research/p8/01`-`06`,
README.md, STATUS.md, docs/USING.md, docs/HOST-API.md, the Python package, the tests, `docs/hours.tsv` and
`docs/map/rules.md`. Line numbers are the plan's unless a file is named.

## Verdict

**Not ready as written; one revision fixes it.** The plan's shape is sound: measure first, then the Must gaps
siblings and agents feel, then the asked-for Shoulds and one release. Most "have" marks hold when the pointed-at
code and tests are opened. But:
- the v1.2.0 release step has no working key-bytes scan of the new history (finding 1, blocker);
- one Must mark is wrong (M4: its proof cannot run without the Mac);
- one research Must is missing (held input across a state load);
- the determinism step under-lists the randomness sources;
- the exit-code tables clash;
- B7 is out of order, and its gate is not a gate;
- the full PC gate breaks the 2-copy rule as written;
- the main-loop and CI hours repeat phase 7's under-estimate.

None of this needs a new phase. All of it fits in the single revision (laz-804).

Counts: 1 blocker, 10 major, 11 minor.

## Findings

Format: number, severity, the plan line, what is wrong, then the fix.

### Blocker

**1. Blocker. L242-251 (C6 steps 2 and 6); also D4.** The release's key-bytes scan of the git history does not
run on the PC, and it says PASS anyway.
- `tools/release_check.py` check 13 (history bytes, around L1109-1114) runs only where the key-header reading copy
  exists. That copy is on the Mac only and is never copied off it. Anywhere else, the check adds a NOTE and the
  report still prints PASS.
- Item 712 already records this as P2 ("prints NOTE then PASS where it cannot run; it should say PEND or SKIP").
  v1.1.0 was cleared by a read-only Mac run (1647 blobs, 0 hits).
- With the Mac closed, C6 step 2 on the PC would show a green release check while the phase-8 commits have never
  been scanned for key bytes. Rule 1 (keys never shipped) has no working check for v1.2.0, and the same holds for
  v1.3.0.
- The plan's L32 parks this as "deferred to the next core rebuild". It is a tool fix and needs no core.

*Fix:*
- Move the check-13 fix into phase B as its own small step (sonnet, about 0.1 h): SKIP or PEND instead of PASS
  where the reading copy is missing, plus a test that plants the missing copy.
- Add a C6 step and a D4 step that close it. Either a short read-only check-13 run on the Mac (ask Guy for about
  15 minutes; no 3DS work, only a git scan), or Guy's written ruling that the release may ship with check 13
  pending. Either way the decision is written down before the push.

### Major

**2. Major. L30-32 ("No core rebuild in phase 8").** The plan says a core rebuild is impossible. It is a choice,
and only half true.
- A Windows core rebuild has a working, attested route (`core-win64.yml`, phase 7 W5). Only a macOS rebuild lacks
  a route.
- Of the three items HANDOFF.md (L19-22) defers "to the next core rebuild", two are Windows-only:
  - the Windows zip's SOURCE.md entry (an `mkrelease.sh` change);
  - the OpenSSL ENGINESDIR/MODULESDIR prefix in `build-core-win64.sh`. This is a CVE-2019-1552-class issue (low
    risk, but a security item in a shipped binary).
- The third (check 13) needs no core at all (finding 1).
- The cost of a Windows-only rebuild is known: a new core revision, so states made on the old Windows core may not
  load. USING's promise already allows that ("States may not survive a core change").

*Fix:*
- Reword L30-32 as "no core rebuild by choice". Give the reason: a Windows-only rebuild costs a CI round plus a
  state-compatibility note.
- Add a Q for Guy (merge it into Q1 so Q stays at five): fold the two Windows items into C6 through
  `core-win64.yml`, or defer them again with the reason written down.
- Move check 13 into B (finding 1).

**3. Major. L44 (M4, "have"; proof "gate A's window check").** The proof cannot run in phase 8.
- `tests/gate-a.sh` checks for a window with `lsappinfo`, which is macOS-only, and the Mac is closed.
- No Windows window or focus test exists anywhere (no EnumWindows, no foreground check).
- The Windows worker starts with CREATE_NO_WINDOW. That is good design, but it is not a test, and the GPU driver
  or the core could still open a window.
- The pointer `STATUS.md:98` is "Audio output: not built"; the window line is :99.

*Fix:*
- Mark M4 partial.
- Add a small B step (sonnet, about 0.15 h): during a live run on the PC, list the top-level windows owned by the
  worker PID and by `azhost.exe`, and the foreground window before and after. Assert none are owned and the
  foreground is unchanged. Gate: PC.
- Keep gate A for the Mac when it frees. Fix the pointer.

**4. Major. L45 (M5) and L177-182 (B1).** A research Must is missing: input state across a state load.
- R01 lists the input latch in the snapshot as a Must (nes-py #110) and has failure mode F7 (a snapshot that omits
  peripheral state). R02 section 4 says to define exactly what a state restores.
- In `python/libazahar/emulator.py`, `load_state()` (about L490-493) leaves `self._held` as it was. Buttons held
  before the load stay held after it. `Emulator(state=...)` starts with nothing held. USING section 11 (L166-180)
  says neither.
- An RL reset that loads a state while A is held starts the next episode with A down. That is a silent
  determinism break between two "same" resets.

*Fix:*
- Decide the rule: clear the held input on load (the simplest rule, matching a fresh `Emulator(state=)`), or keep
  it and document it.
- Write the rule in USING section 11 and in B1's "What repeats" list.
- Add a live test: hold, save, load, run; assert the test-app log shows the chosen behaviour (PC, about 0.1 h on
  B1).

**5. Major. L177-182 (B1, "lists every input to a run").** The list is incomplete. Checked in the pinned core
source (azahar-unified-source-2126.2):
- `ps:ps` GenerateRandomBytes (`ps_ps.cpp` about L150-156) and `ssl:C` GenerateRandomData (`ssl_c.cpp` about
  L25-31) use host randomness, whatever the options say.
- cfg makes a fresh console unique ID (`cfg.cpp` about L1254) and MAC address (about L1413) from an auto-seeded
  random pool whenever it creates a new config. Every fresh workdir gets a different console ID and MAC.
- Our fixed options (`core/options-lazpy.txt`) are only correct for our core. The stock core ignores some of them.
  The option profile in force is itself a run input.
- Workdir reuse is also a run input: the SD card, NAND, the config and the shader cache carry over.
- So is the held input after `load_state` (finding 4).

The plan's test (two seeds give different `tick` fields; same seeds give equal digests on the test app) is good,
but the test app calls none of these services, so it cannot catch them.

*Fix:*
- List every source above in "What repeats", each marked fixed, fixed only on our core, or not fixed (needs a
  core change).
- Say which guest calls reach the unfixed ones (ps and ssl random bytes; any read of the console ID or MAC on a
  fresh workdir).
- Add "same workdir or fresh workdir" to the inputs.
- No core change in phase 8 (by choice, finding 2), so these stay listed, not fixed.

**6. Major. L56 (M16), L202-208 (B7), L212 (B exit gate).** B7 is in the wrong phase, its gate is not a gate,
and it overrides a ruling without asking.
- *Order.* B is "siblings and agents first" (L173), but a hosted-runner recipe serves only outside users (T). The
  plan's own ordering puts that work in D.
- *Evidence.* M16's Must status rests on R03 M7 and R05 S1. R03 M7 is no-GPU operation (the plan's S10 Should), and
  R05 S1 (software Vulkan) is a Should. R03 rates a CI wrapper N5, a Nice. So the plan promotes the Nice and
  demotes the research Must.
- *Gate.* "3 of 3 (or Guy told)" passes once a message is sent, so it gates nothing. Hosted macOS dispatches that
  never start are cancelled, and each cancel mails Guy (the workflow's own comment). "Retry the next day" for two
  days means more mails.
- *Ruling.* The 2.5 s `test_state_boot` bound is "Guy's ruling" (USING about L175). STATUS L59-61 shows it is the
  one failing test on hosted macOS (5.3 s). Relaxing it under `CI` is the whole point of the change, so it needs
  Guy's word, not a risk note (L305-306).

*Fix:*
- Move B7 to D, next to D1 (it uses D1's no-compiler route anyway). Make M16 a Should, and S10 the row R03 M7
  backs.
- Gate: one green dispatch plus the same steps passing on the PC. A dispatch that has not started within 30
  minutes is cancelled once, with no retry loop.
- Add the `test_state_boot` relaxation to a Q for Guy (it fits in Q1 or Q3).

**7. Major. L221-226 (C1) and L189-190 (B3).** Three exit-code tables clash, and all of them freeze at v1.2.0.
- `azhost` already has a frozen table: 4 is core failed and 5 is Vulkan failed.
- C1 makes 4 timeout and 5 crash.
- B3's `examples/verdict.py` uses a third set: 0 pass, 1 fail, 2 harness error or timeout.
- An agent that reads `$?` from both tools would misread every boot failure. R03 M1 asks for one convention that
  tells pass, fail, timeout and harness error apart.
- C1's `--inputs FILE` should not invent a new format: `azhost` already reads an input script (USING section 4a).

*Fix:*
- One table in USING, used by `azhost`, the CLI and the example. Keep `azhost`'s existing codes and meanings, and
  give timeout and crash new numbers that do not collide.
- The example uses the same table, so pass/fail becomes 0/1, and harness error and timeout take their table codes.
- C1 reads the existing input-script format.

**8. Major. L135-137 ("Full PC gate ... At most 2 copies") and L46 (M6, "PC, 2 copies").** As written, the gate
breaks the light-load rule.
- `tests/python/test_pool_live.py` holds every real slot (the default cap of 2), then boots three workers at once
  under a private cap of 3 (a fourth waits).
- In phase 7, Guy's "Run with 2 copies" set `LAZ_MAX_INSTANCES=2`, but the pool gate still ran 3 workers (item 711
  notes). The rule is 2.
- The same test's 1 s kill-to-acquire bound failed under load (W7 run 4: 1.875 s). It passed only in a quiet
  window that the other projects held for it.

*Fix:*
- Either cap the pool test at 2 live workers (boot 2 under a private cap of 2, and a third waits), which keeps
  g1/g2/g4, or record Guy's standing exception for this one test in the plan and on the PC board.
- State that the full PC gate needs a quiet window, booked on the board. Add that wait to the risks.

**9. Major. L276-296 (Hours).** The arithmetic adds up (A 2.0, B 3.6, C 6.15, D 6.5; A-C 11.75, all 18.25). The
grounding is selective.
- *Phase 7's split.* Its plan estimated 15.9 h and took 15.84 h, but only because the errors cancelled out:
  - sonnet steps estimated at 2-2.75 h took 0.2-0.4 h;
  - main-loop work estimated at about 4.6 h took about 13.1 h. W5 core-in-CI was estimated at 0.4 h and took
    4.93 h; W9+W10 were estimated at 0.7 h and took about 3.0 h.
- *Phase 6.* It estimated 6.5 h and took 7.69 h.
- *This plan.* It repeats the pattern: about 7.0 h of A-C is main loop, priced at phase 7's estimate rate, not its
  actual rate.
  - B7 at 0.8 h is a new CI workflow step plus a public doc. The comparable CI work took 0.92-4.93 h; likely 1.5 h
    or more.
  - C6 at 2.5 h: v1.1.0 took 6.35 h (W7 1.32, W8 1.85, W8b 0.18, W9 1.27, W10 1.73); likely 3.5 h or more.
  - D1 at 1.4 h is two new CI build routes. W5 alone took 4.93 h; likely 2.5-3.5 h.
  - D2 at 1.2 h is a new CI path on a software driver; likely 2 h or more.
- *Waits.* L291 excludes waits, but hours.tsv's main-loop rows include them. W10's 1.73 h is "wait for the PC,
  post-publish checks". The estimate and the actuals use different units.
- *Total.* L279's "phases 1-7: 46.95 h" matches nothing in hours.tsv. Phases 1-7 alone are 44.72 h; with setup,
  plan and build, 46.64 h; with phase 8 so far, 47.14 h.

*Fix:*
- Price main-loop steps at phase 7's actual ratio, or at least 1.5x.
- Count PC and CI waits inside the main-loop rows, as hours.tsv does.
- Lower the sonnet estimates to phase 7's actuals.
- A realistic A-C is about 15 h (range 13-19), and the whole phase about 23 h. Fix the 46.95 h figure.

**10. Major. L145-148 (A1) and L195-199 (B5).** A1's "drop B5" outcome is close to impossible, and B5 misses the
second orphan path.
- *Mid-batch.* The worker reads its pipe only between requests. In a 20000-frame batch it cannot see a dead parent
  until the batch ends, so A1's 5 s bound fails mid-batch by design. The probe confirms what the code already
  shows.
- *Exit on EOF.* When the parent dies between batches, the worker sees EOF, and `_serve` returns 0. The worker then
  takes a normal interpreter exit, with no `hard_exit`. On Windows, `hard_exit`'s own docstring says that path "can
  hang on exit" (DLL detach of the core and the GPU driver). A hung orphan holds its slot until someone kills it.
- *Job object.* R05 S4 names a Windows Job object (KILL_ON_JOB_CLOSE) as the kernel-enforced answer. The parent
  creates it at spawn, and Windows kills the worker when the parent dies, even mid-batch. No thread is needed on
  Windows.

*Fix:*
- Drop A1's decision and build B5 directly. Keep A1's script as B5's live gate (the mid-batch, between-batch and
  boot cases).
- B5 also calls `hard_exit` on EOF on Windows.
- On Windows, prefer the Job object (parent side, a few ctypes calls). Keep the getppid thread for POSIX.

**11. Major. L227-233 (C2).** Changing the main test app to play a tone breaks every state fixture, and it adds a
toolchain risk.
- The state meta pins the app's sha256 (USING section 11). `test_release_fixture.py` and the w7 skip list require
  the release fixture to load.
- A rebuilt test app, even from the same source, gets a new sha if the PC's devkitARM differs. The toolkit pins
  r67.1, and the system default moved to r68 on 2026-11-17.
- C2 and C3 each change the host. Two ABI bumps (5 and 6) in one release cost two rounds of `_abi` layout checks
  and docs.

*Fix:*
- Put the tone in a separate small test app (its own folder, built with the pinned devkitARM), and leave the main
  test app and its fixtures alone.
- Do one ABI bump (5) shared by C2 and C3, planned as one host change with one Darwin-visible diff.

### Minor

**12. Minor. L242-251 (C6).** C6 does not name the state-fixture checks.
*Fix:* run `test_release_fixture.py` on the v1.1.0 fixture (the cross-version promise) and make a v1.2.0 fixture
for the next release.

**13. Minor. L135-137 (full PC gate).** "Its skips checked by `tools/skips_check.py`" is not runnable as written.
- The tool needs `--list fast` or `--list w7`, plus the junit file.
- The w7 list also requires that `test_release_fixture.py` and `test_profile_format.py` ran.

*Fix:*
- Name the list and the junit path.
- Each new live test (determinism, re-press, windows, CLI, audio, poll-exact) adds its expected skips to the
  allowed-skips list in the same step.

**14. Minor. L23-24 ("the runner in `docs/map/runners.md`").** `docs/map/runners.md` has no PC section. The PC
runner lives in the toolkit (`tools/pc/lane-pc`, `docs/pc-worker`).
*Fix:* A0 adds the PC commands to runners.md (then `mkmap` and `map_check`), or the plan points at the toolkit
files.

**15. Minor. L192-194 (B4).** The re-press rule is tested on A only.
*Fix:* also test ZL/ZR (they come through a different service) and a touch release and re-tap. Agents tap far
more than they press A.

**16. Minor. L183-185 (B2).** Only four error classes gain the evidence fields.
- `StateError` and `HostError` are left out.
- R03 M5 asks for the last frame on a timeout. B2 names only the newest existing PNG, which may be hundreds of
  frames old.

*Fix:* cover all six classes, and say plainly in USING that the shot is the newest one taken, not the frame at the
timeout.

**17. Minor. L149-152 (A2).** "Peak RSS every 10 cycles" of boot-and-close measures nothing, because each boot is a
new worker process.
*Fix:* measure the parent's RSS and handle count, system free RAM, GPU memory, and leftover workdir files and slot
files across the 100 cycles. Keep the per-instance RSS only for the 300 `load_state` calls.

**18. Minor. L144-145 (A0) and L234-237 (C3).** C3's whole premise is that our core exports `lazpy_movie_play`.
*Fix:* A0 confirms the export in the shipped Windows core (a one-line export listing on the PC). If it is missing,
C3 is dropped before any brief is written.

**19. Minor. L221-222 (C1 doctor).** The host learns the Vulkan devices only during a core boot, and they appear in
`host.log`.
*Fix:* say that `doctor` reads them from the boot's `host.log`, and that without the test app it prints "unknown".

**20. Minor. L57-58 (S2) and the inventory.**
- S2's research cell omits R03 M1, which is the source for the verdict exit codes.
- R06 lists `test_c_checks` among the tests with no emulator, but it is marked slow and live. R06 also omits
  `test_memory.py` and `test_pool.py`.

*Fix:* add R03 M1 to S2. Correct the inventory's test grouping, or note in the plan that M1's and M3's proofs are
live (PC), not CI fast.

**21. Minor. L202-208 (B7 gate).** `macos-live.yml` has `continue-on-error` on the job, so a red run shows green.
*Fix:* the gate reads the pytest step's outcome and its summary line (passed above 0, failed 0), as the workflow's
own header says.

**22. Minor. L186-191 (B3).** "It needs numpy", but numpy is an optional extra in `pyproject.toml`.
*Fix:* `libazahar.images` imports numpy lazily, and without it raises a clear error naming the extra. The fast
CI test installs the extra.

## The six checks

**1. Is every Must backed by research?** Mostly yes.
- M1-M3 and M5-M15 cite research Musts, and the citations hold where checked: R01 section 2, R02 section 2, R03
  M2/M3/M5/M8, R04 section 2 and #5, R05 M4/M5/M7/M8.
- M16 is the exception. It promotes R03's Nice (N5) and R05's Should (S1) to a Must (finding 6).
- M15's parent-death half rests on R05 M4. R05 also found no user reports of orphaned workers. It is still a Must
  for our own agents, which kill runs on a shared PC.

**2. Is a research-supported Must missing?**
- Two are:
  - input state across a state load (R01 Must, F7; finding 4);
  - no-GPU operation (R03 M7), which the plan has as S10.
- Two are only partly covered:
  - R03 M1, one exit-code convention (finding 7);
  - R02 section 4, defining what a state restores (finding 4; USING already covers SD and NAND).

**3. Are the gates real and runnable on the PC or in CI?** Mostly. Exceptions:
- M4's proof is macOS-only (finding 3);
- check 13 does not run on the PC and says PASS (finding 1);
- B7's "or Guy told" gates nothing (finding 6);
- the full PC gate's skip check is under-specified (finding 13);
- the pool gate runs 3 copies and needs a quiet window (finding 8).

The fake-worker gates (B2, B5, C1) run in `test-windows.yml` on every push, which is real. `test.yml` for macOS is
manual and may not start. Every gate that needs it should also name its PC fallback.

**4. Are the hours grounded in hours.tsv?**
- Sonnet and review steps: yes, and they are slightly high.
- Main-loop, CI and release steps: no. They are priced at the rates phase 7 estimated, not the rates it achieved
  (finding 9).
- Waits are excluded, unlike the actuals.

**5. Does any step break a hard rule?**
- Light load: yes, as written. The full PC gate's pool test runs 3 workers (finding 8).
- Keys: the release has no working key-bytes history scan off the Mac (finding 1).
- No other breaks found:
  - A4 keeps Nintendo's DSP firmware out, and uses only our own component file.
  - A5's driver download follows the pinned-download rule (and asks Guy first).
  - The private side test is worded as the brief requires.
  - The plan makes no speed claims, and A3's numbers stay private.
  - Clean-room is kept.
  - CI-mail discipline is kept: PC first, manual workflows first. B7's retry loop is the exception (finding 6).

**6. Are the phases ordered by user value?** Yes, with one exception.
- The order follows user value: A measures cheaply; B serves siblings and agents at merge; C delivers the asked-for
  Shoulds and one release; D serves outside users on Guy's go.
- The exception is B7, which serves outside users only (finding 6).
- C3 (poll-exact) is a sibling ask and is rightly in C.
- C2 (audio) is rightly gated on 3DP.

## Hour-saving candidates

Each keeps every gate.

| # | Idea | Saves | Risk |
|---|---|---|---|
| H1 | Drop A1's decision and build B5 directly; A1's script becomes B5's live gate (finding 10) | about 0.3 h | none; the code already answers the question |
| H2 | Windows Job object (KILL_ON_JOB_CLOSE) in the parent instead of a watchdog thread on Windows | about 0.1 h, and it removes the mid-batch false-kill risk | Job nesting on old hosts; fine on Windows 8 and later |
| H3 | One ABI bump for C2 and C3, one host diff and one Darwin-visible review | about 0.4 h | the two features couple in one review |
| H4 | A separate tone app instead of changing the main test app (finding 11) | avoids a fixture rebuild round, about 0.5-1 h | one more small build artifact |
| H5 | Reuse `azhost`'s exit-code table and input-script parser for C1 (finding 7) | about 0.2 h, and one table to freeze, not three | none |
| H6 | Move B7 to D and gate it on one green dispatch plus the PC run, not 3 of 3 | about 0.5 h in B, plus avoided cancel mails | macOS flake caught later |
| H7 | Fix check 13's PASS as a tool change now, not with a core rebuild (finding 1) | removes a release blocker at about 0.1 h | none |
| H8 | Fold B6's error table into B2's doc change (same section, same agent) | about 0.1 h | none |
| H9 | Pure-Python PNG reader limited to the host's own format (8-bit RGBA, filter 0 on every row, one IDAT; `host/png.c`), already planned: keep it that narrow and refuse other PNGs | keeps B3 at 0.4 h | none |
| H10 | Run B1 to B5's live tests in one PC job (one full-gate run per phase, not per step), per Guy's large-batch rule | about 0.5-1 h of PC booking and waits | a failure needs a narrower rerun |
| H11 | Lower the sonnet estimates to phase 7's actuals and move those hours into the main-loop rows (no saving; better grounding) | 0 h, but the totals become honest | none |
