---
title: Keys
status: draft
description: The signing keys of a tenant: sealed, published, rotated without an outage.
---

# Keys

A tenant signs with keys it owns, each one sealed by a key management service: the application asks for an
operation and never holds the master key. A key has a status, a use and dates, and the JWK Set publishes the
ones a client may need, which includes a key staged for a rotation and a key still retiring.

A rotation is therefore not an outage: the new key is published before it is used, and the old one stays
published until nothing it signed can still be verified.

**A key works for an age**, ninety days by default, counted from the moment it became active. Reaching it
asks nothing of anybody: a timed step stages a successor behind it, and `beffroi:keys:list --check` fails
on an active key past its age with nothing staged, which is what a planning that has stopped looks like
from outside.

**A tenant keeps one key it does not publish.** The JWK Set holds the keys a client may need; the key the
bodies of the messages are sealed to is a key of the tenant like the others, with the same rotation, the
same rewrapping and the same retirement window, and it appears in no published document.

This page will describe the statuses, the rotation, the staging delay, and what `--compromised` does
differently.
