---
title: Token exchange
status: draft
description: Acting for somebody else, RFC 8693.
---

# Token exchange

Token exchange is how a gateway acts on behalf of a service, or a service on behalf of a person, without
either of them handing over their own token. The result names the subject and the actor, and a resource
server can tell them apart.

**The issued token knows the person it is about.** Its `sub` is the one the presented token carried, written
for the client that token was issued to (RFC 8693 §2.2.1), which may be a pairwise subject the client that
asked cannot read. So the provider keeps the person beside it: on the record of an opaque token, and, in a
self-contained one, as a private claim `person` sealed by the key management service of the tenant, which the
provider alone can open and which tells the holder nothing it did not know. That is what lets introspection
describe an exchanged token, and the act that describes it lands in the journal of that person. A token a
client holds for itself is about nobody, and carries no such claim.

This page will describe the parameters, delegation against impersonation, and what the issued token claims.
