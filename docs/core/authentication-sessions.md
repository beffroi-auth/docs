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
factors of different kinds were proven, and `fed` for a federated assertion, which RFC 8176 does not register
and which Microsoft Entra ID writes for one.

A session is opened under the [floor of the logins of its tenant](tenants.md#the-floor-of-its-logins): proofs
that do not satisfy it open nothing, wherever the login came from.

**A login through an organisation records `fed`.** A session opened by an assertion of an [upstream identity
provider](../saml/federated-sign-in.md#the-session) proves `fed`, and the method its class names where that
class means exactly one. Its `auth_time` is the instant the person authenticated at their provider, and it
ends no later than the `SessionNotOnOrAfter` that provider set.

**One session for every protocol.** The identifier of a session is the `sid` of the ID tokens issued under it
and the `SessionIndex` of the SAML assertions, so a logout asked for by either names the same session.

**Every end revokes what was issued under it.** However a session ends, at the end session endpoint, from the
page of the account, by the console, by a SAML logout request or replaced by a new login, the refresh tokens
issued in it are revoked and its opaque access tokens removed, on the lane of the events, beside the
back-channel logout that tells its clients. The provider refuses a token of an ended session at its use in
the meantime.

This page will describe opening a session, what a snapshot holds, re-authentication with `prompt=login` and
`max_age`, and termination.
