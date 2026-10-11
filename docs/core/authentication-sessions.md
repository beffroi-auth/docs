---
title: Authentication sessions
status: draft
description: What a person proved, when, and from where.
---

# Authentication sessions

A session records what was actually proven: which credentials, at what time, from which address and user
agent. A grant reads a snapshot of it rather than the live session, which is what makes `auth_time`, `acr`
and `amr` mean something at the moment the token was issued and not at the moment it is read.

The values of `amr` are the ones RFC 8176 §2 lists, with `mfa` beside the specific methods when two
factors of different kinds were proven.

This page will describe opening a session, what a snapshot holds, re-authentication with `prompt=login` and
`max_age`, and termination.
