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
| `local` | A membership decided in this provider | `beffroi:group:add-member` and `beffroi:group:remove-member`, and an administrator through the administration API |
| `upstream_claims` | A membership an upstream identity provider asserted at the last sign-in | The sign-in through that provider, when its declaration maps groups |
| `scim` | A membership a directory pushed | Nothing: SCIM is [not implemented](../scim/index.md) |

## A group is created here

The group itself is local. An operator creates it, or an administrator through the administration API, and its
name is taken as it is typed, never trimmed or folded, since the declaration of a provider names it exactly:

``` bash
bin/console beffroi:group:create Staff
```

A name the rules above refuse is refused, and so is a name the tenant already holds. The command prints the
name, the source, the identifier of the row and the slug of the tenant. Creating a group is an act of the
tenant, `group.created`, and of no person, a group holding nobody when it is created.

**No provider creates one.** The declaration of an [upstream identity
provider](../../operators/saml/upstream-identity-providers.md#declaring-an-identity-provider) maps the values of an
attribute to the names of groups of the tenant. A value the map does not name, a name the tenant holds no group
under, and a value that is not a string are ignored: what a provider sends never becomes a group.

## A member is added here

A membership of source `local` is given and taken back from the console, which names the group exactly as the
tenant holds it, then the username:

``` bash
bin/console beffroi:group:add-member Staff alice
bin/console beffroi:group:remove-member Staff alice
```

An administrator does the same through the administration API. Adding a person who is a member already is
refused, and so is taking out a person who is not one. The tenant takes back no membership an upstream provider
or a directory gave: the next assertion or the next push would write it again. Each change is an act of the
person, `group_membership.added` or `group_membership.removed`, which names the administrator who made it
through the API.

## Who administers the tenant

The members of the groups `tenant.administrators` names, `BEFFROI_TENANT_ADMINISTRATORS` in the image, administer
the tenant, whatever the source of their membership: a local group the console fills, or a group an upstream
provider or a directory holds the members of. The role is read from the groups of the person at the moment it is
asked, never from a list of people kept beside them. The image names no group, so nobody administers a tenant
whose deployment says nothing. A name is compared exactly, and a name no group carries yet is accepted.

``` dotenv
BEFFROI_TENANT_ADMINISTRATORS='["administrators"]'
```

A person taken out of such a group stops administering the tenant at once: the next access token addressed to
its [administration API](../../developers/oidc/resources.md#the-administration-api) is refused, and so is the next request
that presents one already issued. An administrator does not take themselves out of such a group through the API.

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
added, and the archive a person asks for carries the same three facts in its `groups` chapter. Through the
administration API, an administrator lists the groups of the tenant with how many members each holds and
whether they administer it, which delivers nobody, and reads the members of one, which is an act of each
member, `administration.membership_read`.

No claim of OpenID Connect and no SAML attribute carries the groups of a person to a client.
