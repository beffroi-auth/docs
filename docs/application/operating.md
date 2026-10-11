---
title: Operating it
status: draft
description: Rotations, migrations, backups, and what to do when a key is compromised.
---

# Operating it

A provider is operated, not installed once: keys rotate, data keys are rewrapped, migrations run, backups are
taken and restored. Each of those has a command, and each command says what it did.

Some of it is not operated at all, because time does it: one timed step per thing that comes round, each
one handled like any other write, so a deployment that runs the worker runs them.

| Every | What it does |
|---|---|
| minute | Advances the lifecycle of the keys: stages a successor for a key that has worked its age, activates a staged key whose delay has elapsed, retires a key past its date |
| hour | Drops the clients nobody uses any more, forgets the archives past their week, and drops the rows that can no longer do anything |
| day | Forgets the acts of the journal past their retention, and the changes of a record past theirs |
| week | Refreshes the databases of addresses, which is the cadence they are published at |

`beffroi:doctor` is what to ask first when something does not work: it reads, writes nothing, and says
which points this deployment answers for.

This page will describe the routine operations, and the two that are not routine: a compromised key, and a
restore.
