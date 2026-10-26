---
title: Groups
description: The groups of a tenant, the memberships of its people, and where each membership came from.
---

# Groups

A group belongs to a tenant and holds members, and every membership carries its source: written here, asserted
by an upstream identity provider, or pushed by a directory. That is what lets a provider accept memberships from
outside without a directory silently taking over what somebody decided here, and what tells a person reading
their own file which door to knock on.

## What a group is

| Field | What it holds |
|---|---|
| Name | Unique within the tenant and compared exactly, case included. In Unicode Normalization Form C, without whitespace at either end, 255 characters at most |
| Source | Where the group comes from: `local` for every group, a group being created here and never by a provider |
| Created at | When it was created |

A membership is a group, a person of the same tenant, the source of that membership and the date it was added.
The table holds one membership per group and person, whatever its source.

## Where a membership comes from

| Source | What it is | What writes it |
|---|---|---|
| `local` | A membership decided in this provider | No command or page of the bundle writes one |
| `upstream_claims` | A membership an upstream identity provider asserted at the last sign-in | The sign-in through that provider, when its declaration maps groups |
| `scim` | A membership a directory pushed | Nothing: SCIM is [not implemented](../scim/index.md) |

## A group is created here

The group itself is local. An operator creates it, and its name is taken as it is typed, never trimmed or folded,
since the declaration of a provider names it exactly:

``` bash
bin/console beffroi:group:create Staff
```

A name the rules above refuse is refused, and so is a name the tenant already holds. The command prints the
name, the source, the identifier of the row and the slug of the tenant.

**No provider creates one.** The declaration of an [upstream identity
provider](../saml/upstream-identity-providers.md#declaring-an-identity-provider) maps the values of an
attribute to the names of groups of the tenant. A value the map does not name, a name the tenant holds no group
under, and a value that is not a string are ignored: what a provider sends never becomes a group.

## What a provider asserts

**The memberships a provider asserts are what it said at the last sign-in.** At each sign-in of a person that
provider created, when its declaration maps groups:

- a membership of source `upstream_claims` whose group it no longer asserts goes;
- one whose group it still asserts stays, with the date it was added;
- a group newly asserted gets one, of source `upstream_claims`.

The removals are written before the additions, in the same unit as the rest of the sign-in, so all of it is kept
or none of it, and before the session the sign-in opens serves anything: nothing that session serves reads a
membership the provider has taken away.

**A membership of another source is left as it is.** A membership of source `local` or `scim` stays when the
provider asserts its group, which gives no second membership, and stays when the provider stops asserting it. A
provider whose declaration maps no groups leaves every membership as it was, and a person an operator
[linked by hand](linked-identities.md#an-operator-writes-one-by-hand) to a provider, which did not create them,
is given none.

## Reading them

`beffroi:user:show` lists the groups of a person, each with the source of the membership and the date it was
added, and the archive a person asks for carries the same three facts in its `groups` chapter.

No claim of OpenID Connect and no SAML attribute carries the groups of a person to a client.
