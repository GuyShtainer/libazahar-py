---
id: laz-510
title: lazpy
order: 510
kind: step
parent: laz-500
page: Core revision 2: tick seed option and thread registers for 3DPlatinum
hours: -
---
# Step K: core revision 2 (3DPlatinum's tick seed and thread registers)

## What it is
One core rebuild (2126.2-lazpy.2) carrying 3DPlatinum's two asks (A4: `citra_init_ticks_override` as an option;
A1: each guest thread's pc, lr and sp between batches) and the items queued for the next core revision (the macOS 15
header, patch 0008's comment, core/PIN-nokeys as the default pin). Built in its own worktree with a real dl/ (never
MAIN's build tree), on branch core-rev2; merged after v0.1.0 is tagged unless Guy rules otherwise.

## Exit gate
`docs/plans/phase-k.md` section 6 (written 2026-11-13, two opus reviews before work).

## Evidence
none yet

## Pointers
- Plan: `docs/plans/phase-k.md`
- Asks verbatim: item laz-500's notes.

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- 2026-11-13 10:28 and 10:42: reviews 1 and 2 saved (`docs/reviews/phase-k-review-1.md`, `docs/reviews/phase-k-review-2.md`);
  plan revision 2 answers both.
- Process slip, recorded honestly: the worktree seeding and the code edits started at 10:33, while review 2 still ran
  (the rule is two reviews, then execute). Nothing was committed or built before review 2 returned; its findings were
  applied to the edits (two of its blockers, the missing vendor/ headers and the two ABI tests, were already fixed).
- Patch method that worked: a scratch git repo with the six touched files from the unpacked source, one commit per
  patch, fixup commits squashed with `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash`, then a fresh apply of the
  whole stack at fuzz 0 compared byte for byte with the scratch tree. Git's diff aligns hunks differently from the
  original patches, so unchanged patches are kept as they are and changed ones are edited in place where small.
