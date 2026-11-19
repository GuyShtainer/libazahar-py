---
id: laz-830
title: lazpy
order: 830
kind: phase
page: Phase 8 C: command line, audio, exact input, then release v1.2.0
hours: phase-8c
---
# Phase 8 C: agents and siblings, then v1.2.0

## What it is
Steps C1-C6a of the plan, then the v1.2.0 release.

## Exit gate
v1.2.0 published, audit shippable, post-publish clone check passes.

## Evidence
2026-11-19 02:32: full PC gate on merged phase C (host ABI 5 and the tone app built in the lane): 409 passed, 11
skipped, 1 xfailed (laz-829), 4 failed: test_verdict_live.py ran the example with -I, which ignores PYTHONPATH, so it
imported the venv's installed v1.1.0 (ABI 4). Fixed (the repo's package first on sys.path); 02:34 rerun of the
verdict, audio and CLI tests: 37 passed. C3 waits on a core patch (laz-833, into C6a). The review runs.

## Pointers
- Plan section: `docs/plans/phase-8.md:180`
- Review: `docs/reviews/phase-8-plan-review.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.

- Guy, 2026-11-18 ~21:00, verbatim: "you have my green light. go". Q1-Q5 not answered: the plan's recommended
answers are in force (Q1 yes, Q3 yes, Q4 yes to D after v1.2.0 / two releases / the hosted bound / the MSYS2 Mesa
download, Q5 probe now) until Guy says otherwise.
- From laz-829 (2026-11-19): C6a's core rebuild must also fix the unserialize step's leak of about 2.2 Semaphore
handles per load_state (a winpthreads condvar shape; needs a traced core build). Then flip test_handles_live.py's
strict xfail to a pass.
