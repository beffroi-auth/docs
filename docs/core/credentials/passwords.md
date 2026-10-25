---
title: Passwords
status: draft
description: Typed hashes, the algorithm named in the hash, and rehashing on the next sign-in.
---

# Passwords

A password is stored as a hash that says which algorithm produced it, so several algorithms coexist and a
hash made by an older one is replaced the next time the person signs in successfully. A new algorithm is a
class implementing the hasher interface of its capability, registered in the wiring.

A new hash is Argon2id with the four lanes and the 64 MiB of memory RFC 9106 §4 recommends. A hash made with
fewer, or by another algorithm a migration brought in, verifies as it is and is replaced at the next
successful sign-in.

A prospective password is refused rather than warned about when it is too short, longer than 4096 bytes, or
too easy to guess by the estimate the core applies. How short is too short is two numbers, as NIST SP 800-63B
§3.1.1.2 makes it, and the floor of the logins of the tenant decides which one applies:

| The floor of the tenant | The length a password has to reach |
|---|---|
| `single_factor`, a password being the whole of a login | fifteen characters |
| `two_factors`, a second factor going with it | eight characters |

A floor that reads nothing a password proves, `phishing_resistant`, holds no password at all. The length is
counted in characters, each code point one, and the page, the console and the core read the same number. A
password already stored is left as it is when the floor moves, since a hash says nothing of the length behind
it. Both numbers are in the code and not in a configuration: an option to lower one is the option to do it
wrong.

It is also refused when a list of compromised values holds it, which is what NIST SP 800-63B §3.1.1.2 asks
for and what no length rule catches. The list is asked by range: the first five hexadecimal characters of
the SHA-1 of the password go out, the thirty-five that are left are compared locally, and no API key is
needed. A deployment that names no endpoint asks nobody and poses passwords on the rules of the core
alone, no password and no prefix of one ever leaving it.

A password already in use is looked up again after a login, at most once every thirty days per person, on
a lane that no sign-in waits on. What the list was later found to hold is read on
[the password page of the account](../../symfony-bundle/account.md#what-the-password-page-says) rather than in
the one request that noticed it, and the next login that serves no authorization request sends the person
there before the page they were going to: a login a client is waiting on is interrupted by nothing.

A person whose address is of a domain an [upstream identity provider](../../saml/federated-sign-in.md) answers
for has no password here. One is neither set for them nor accepted from them, and a password they held before
their domain was federated is refused at the login and can no longer be replaced.

This page will describe the shape of a stored hash, the algorithms available, and how a migration from
another provider's hashes is handled.
