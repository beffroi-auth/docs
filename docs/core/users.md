---
title: Users
status: draft
description: A person in the provider: their username, their claims, and the stable subject clients know them by.
---

# Users

A user belongs to a tenant, is named by a username unique within it, and is known to clients by a subject
identifier that never changes, even when the username or the email address does. The standard claims of
OIDC Core §5.1 are held beside the identity, each one as what it is rather than as a row in a bag of
strings.

**A person names the source that created them.** Local, for a person an operator or a script created; or an
upstream provider, for a person created at their [first sign-in through their
organisation](../saml/federated-sign-in.md#the-person), with the claims of their profile that provider fills.
What a source holds, a manual description does not change: `beffroi:user:profile` refuses a held claim said
otherwise, naming the provider, keeps a held claim it is not told about rather than clearing it, and accepts
one said with its current value, so a provisioning script can run again; the page of the account offers the
person no line to change it either. A claim the provider stops saying is released to the person, with the
value it wrote last. `beffroi:user:show` prints the source beside the identity.

A person a provider created is named by their address, which is their username, and the username follows the
address when the provider sends another one.

This page will describe the identity, the claims that are set and the ones that are not, and the difference
between the two.
