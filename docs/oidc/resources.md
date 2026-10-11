---
title: Resources
status: draft
description: The audience a client asks its token for, RFC 8707.
---

# Resources

A client names the resource it intends to call, and the token is issued for that audience rather than for
everything the client might reach. A resource server that receives a token addressed elsewhere refuses it.

What a tenant announces as its protected resources is read from the clients that registered one, never
from a list kept beside them, and it is the `protected_resources` member of RFC 9728 §4: the one member of
the registry that says what the values of a `resource` parameter are, RFC 8707 registering none of its
own. A tenant whose clients registered none announces nothing rather than an empty list, which a client
would read as "no resource is acceptable here".

This page will describe the parameter, what the issued token carries, and what happens when several
resources are named.
