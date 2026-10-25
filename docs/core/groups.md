---
title: Groups
status: draft
description: Membership, and where each membership came from.
---

# Groups

A group belongs to a tenant and holds members, and every membership carries its source: written here, or
pushed by a directory. That is what lets a provider accept provisioning later without a directory silently
taking over what somebody created by hand.

| Source | What writes it |
|---|---|
| `local` | An operator, with `beffroi:group:create` for a group |
| `upstream_claims` | An upstream provider, through the groups its declaration maps |
| `scim` | A directory pushing its people, once SCIM is served |

**A group is created here, never by a provider.** The declaration of an [upstream identity
provider](../saml/upstream-identity-providers.md#declaring-an-identity-provider) maps the values of an
attribute to the names of groups of the tenant, and a value naming nothing, or a group the tenant does not
hold, is no group. The group itself is local:

``` bash
bin/console beffroi:group:create Staff
```

**The memberships a provider asserts are what it said at the last sign-in.** At each sign-in of a person that
provider created, when its declaration maps groups, a membership whose group it no longer asserts goes, one it
still asserts stays with its date, and a group newly asserted gets one, in the same unit as the rest of the
sign-in and before the session it opens serves anything. A membership of another source is left as it is, a
person an operator linked to the provider is given none, and the table holds one per group and person.

`beffroi:user:show` lists the groups of a person with the source of each membership, and the archive a person
asks for carries them. No claim hands the groups to a client of OpenID Connect.

This page will describe the model in full.
