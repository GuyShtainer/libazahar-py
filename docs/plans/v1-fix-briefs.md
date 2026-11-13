# Phase 6 step V1: fix briefs after the diff review

Written 2026-11-13 by the main loop for item laz-610. The source is `docs/reviews/api-freeze-1.0-diff-review.md`
(findings 1-11 and the nits). The rules of `docs/plans/v1-briefs.md` ("Rules for both agents") hold unchanged,
except the emulator time limit (emulator tests are allowed now). Two cheap agents work at once in the worktree
../libazahar-py-k (branch core-rev2) on separate files. The main loop edits `docs/USING.md` afterwards from the
agents' runs/v1/fix-*-progress.md notes; agents never edit USING.md.

## Decisions (the main loop's, binding on both agents)

- D-a: invalid UTF-8 anywhere in a profile line (comments included) is an error naming the line, in both parsers.
- D-b: a NUL byte anywhere is an error naming the line, in both parsers.
- D-c: a BOM (EF BB BF) at the start of any line is an error naming the line, in both parsers (C already does).
- D-d: both parsers read in file order and report the first error. More than 4096 lines is reported at line 4097
  (`error line 4097` in the case table; Python `"<path>:4097: more than 4096 lines"`; azhost
  `UsageError: <path> line 4097: more than 4096 lines`). Update the existing too-many-lines cases.
- D-e: Python's `options=` pairs pass the same one-line rule as a profile line (built as `key=value`); a bad pair is
  `ArgumentError` naming the key. `--opt` already does.
- D-f: azhost `--seed`: a missing seed folder stays a usage error (exit 2); a copy failure is I/O (exit 6).
  `--save`: a write failure stays exit 6; only drain or serialize failures are 9. (The main loop fixes USING's table.)
- D-g: input script: drop one trailing `\r` before the 511-byte check (as the profile does); reaching the line bound
  with data left is an error, never a silent cut; `0x0x10` is an error; `0X` is accepted (USING will say so).

## Brief HF: host fixes (name: hostfix)

Your files: `host/*`, `Makefile`, `tests/host/*`, `tests/data/profile-cases/*`, `tests/python/test_profile_format.py`,
`tests/gate-a.sh`, `docs/HOST-API.md`, runs/v1/fix-host-progress.md.
- Review 1 (C side of D-a, D-b, D-c), 3 (D-d, C side), 5, 6 and the `0x0x` nit (D-g), 2 (D-f, the seed copy), 9
  (HOST-API.md's guest-break wording), 11's `tests/gate-a.sh` (unset `LAZ_ROOT` and `LAZPY_ROOT` before it runs
  fetch.sh in the fresh copy).
- New shared cases in `tests/data/profile-cases/`: `bad-utf8`, `bad-utf8-comment`, `nul-in-value`, `bom-line-2`,
  `bad-line-then-too-many` (line 1 `bad`, then 4096 more lines: `error line 1`), and the updated too-many cases.
  Make `test_profile_format.py`'s error check compare the exact line number in the message, not only the path.
- Review 10: a test of `msg=` escaping `"`, `\`, a newline and the `\r` drop (make `print_escaped` testable in a
  pure file, or a CLI check); a CLI test (slow tier is fine) that a failing `--save` write exits 6 and a failing load
  exits 9; run the exit-7 test with `LAZ_STOCK_CORE=<MAIN>/dl/azahar/azahar_libretro.dylib` (read-only use of that
  file is allowed) and record its result.
- Gates: `make check`, `make test-host`, the fast pytest, and the slow profile/CLI tests you touched.

## Brief PF: Python fixes (name: pyfix)

Your files: `python/libazahar/*` except `_abi.py`, `tests/python/*` except `test_profile_format.py`, runs/v1/fix-py-progress.md.
- Review 1 (Python side of D-a, D-b, D-c), 3 (D-d: stream the lines; first error wins; 4097 for too many), 4 (D-e),
  7 (any `OSError` while making `workdir` or its folders is `HostError` with the path), 8 (`__reduce__` for
  `HostTimeout`, `SlotTimeout`, `HostCrashed`, plus a pickle round-trip test of every class in `errors.__all__`),
  the nits on `stop_every` (through `_index`), `wall_limit` and `timeout` (a non-number is `ArgumentError`).
- Write in your progress file the exact USING.md lines the main loop must change (section 3 types, section 8,
  section 14 rules, section 20's `HostCrashed.signal_name`).
- Gates: the fast pytest, and the slow tests you touched (nice 10, at most 2 instances, worktree core).
