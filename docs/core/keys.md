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

**A key works for an age**, counted from the moment it became active. Reaching it asks nothing of anybody: a
timed step stages a successor behind it, and `beffroi:keys:list --check` fails on an active key past its age
with nothing staged, which is what a planning that has stopped looks like from outside.

**The figures belong to the family of the key.** How long a new key is staged and how long it works is the
schedule its family declares, so a key that costs a person a step at every rotation is not rotated at the pace
of one nobody sees:

| Family | Staged for | Works for | Set by |
|---|---|---|---|
| The keys of the JWK Set, and the keys kept beside them | the `max-age` of the JWK Set plus sixty seconds, 360 seconds by default | ninety days | `beffroi.keys.staging_delay`, `beffroi.keys.age` |
| The SAML signing key, and the key each upstream SAML identity provider encrypts for | seven days | 365 days | `beffroi.saml.identity_provider.staging_delay`, `age` |

The SAML keys are staged for a week because their next certificate is published in metadata that service
providers fetch once a day, and that some administrators upload by hand. [The identity
provider](../saml/identity-provider.md#a-rotation-without-an-outage) says why each figure is what it is.

**A tenant keeps keys it does not publish.** The JWK Set holds the keys a client may need. Beside them, the
tenant holds the key the bodies of its messages are sealed to, the key it hands to browsers for web push, its
SAML signing key, whose certificate the SAML metadata carry, and one key for each upstream SAML identity
provider that encrypts for it. Each is a key of the tenant like the others, with the same custody, the same
commands and the same rewrapping, and none of them appears in the JWK Set.

This page will describe the statuses, the rotation, the staging delay, and what `--compromised` does
differently.
