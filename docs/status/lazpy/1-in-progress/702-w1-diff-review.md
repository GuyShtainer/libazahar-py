---
id: laz-702
title: lazpy
order: 702
kind: step
parent: laz-700
page: Windows proof: review every change the Windows port makes
hours: -
---
# Windows proof: review every change the Windows port makes

## What it is
W1a (main loop, on the PC): the Darwin-visible preprocessed diff and the make -B -n diff of v1.0.0 vs the branch. W1 (opus): the full diff review of port-win-v1, including a per-line verdict on Python that macOS sees.

## Exit gate
runs/p7/w1a/darwin-pp.diff and make-n.diff exist (planted-line check passes); docs/reviews/phase-7-diff-review.md per the W1 gate. Plan: `docs/plans/phase-7.md` line 225.

## Evidence
none yet

## Pointers
- Plan section: `docs/plans/phase-7.md:225`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
None yet; planned in phase-7 revision 2.
