---
title: Introspection and revocation
status: draft
description: Asking what a token is, and ending it. RFC 7662 and RFC 7009.
---

# Introspection and revocation

Introspection describes a token to the client it was issued to and to nobody else, as JSON or as a signed
JWT. Revocation ends a token and what depends on it, and it answers the same way whether the token existed or
not.

The signed form is RFC 9701: the response is a JWT, `application/token-introspection+jwt`, for a client
that registered that it wants one, and the algorithms it may be signed with are announced in the discovery
document beside the endpoint itself.

**An answer that hands a person over is an act of their journal.** An introspection that describes an active
token issued for a person tells a third party who that token names, so it is written, `introspection.answered`,
naming the client that asked and the person. An answer `active: false` writes nothing, and neither does the
description of a token a client holds for itself, which hands over nobody.

This page will describe both endpoints, who may call them, what introspection returns, and what a revocation
reaches.
