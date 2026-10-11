---
title: Passwords
status: draft
description: Typed hashes, the algorithm named in the hash, and rehashing on the next sign-in.
---

# Passwords

A password is stored as a hash that says which algorithm produced it, so several algorithms coexist and a
hash made by an older one is replaced the next time the person signs in successfully. A new algorithm is a
class implementing the hasher interface of its capability, registered in the wiring.

A prospective password is refused rather than warned about when it is shorter than eight characters,
longer than four kilobytes, or too easy to guess by the estimate the core applies. The floor is in the
code and not in a configuration: an option to lower it is the option to do it wrong.

It is also refused when a list of compromised values holds it, which is what NIST SP 800-63B §5.1.1.2 asks
for and what no length rule catches. The list is asked by range: the first five hexadecimal characters of
the SHA-1 of the password go out, the thirty-five that are left are compared locally, and no API key is
needed. A deployment that names no endpoint asks nobody and poses passwords on the rules of the core
alone, no password and no prefix of one ever leaving it.

A password already in use is looked up again after a login, at most once every thirty days per person, on
a lane that no sign-in waits on. What the list was later found to hold is read on
[the password page of the account](../../symfony-bundle/account.md) rather than in the one request that
noticed it.

This page will describe the shape of a stored hash, the algorithms available, and how a migration from
another provider's hashes is handled.
