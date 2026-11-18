---
id: laz-714
title: lazpy
order: 714
kind: step
parent: laz-700
page: Windows proof: check the published release from a fresh download
hours: -
---
# Windows proof: check the published release from a fresh download

## What it is
Main loop: post-publish download and clone check on the PC; the Windows CI job becomes blocking.

## Exit gate
The W10 gate in the plan. Plan: `docs/plans/phase-7.md` line 376.

## Evidence
- 2026-11-18 00:09 started: v1.1.0 published (item 713). A waiter starts runs/p7/w10/w10-pc.sh when 3DP's PC
  build ends (one job on the PC).
- 2026-11-18 01:52 done: all 13 assets curled from the release URLs match SHA256SUMS (rc 0); clone_check from
  GitHub main (cec470d, 2 copies) 299 passed, 8 skipped, skips_check w7 0 problems, rc 0 (runs/p7/w10/w10.out, notes.md).

## Pointers
- Plan section: `docs/plans/phase-7.md:376`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
None yet; planned in phase-7 revision 2.
