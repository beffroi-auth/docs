---
title: Linked identities
description: The same person at an upstream provider, recognised by the provider and the subject it gives them, so that federation never duplicates them.
---

# Linked identities

A linked identity says that a user of this tenant is a given subject at a named upstream provider. Whoever
presents that subject at that provider is that user, and nobody else: it is what keeps a person from being
created again every time they arrive by another door, and the one way a subject an upstream provider names
becomes a person of this tenant at all. Nothing infers one. A row is written by a sign-in through the provider,
or by an operator, and by nothing else.

## What one holds

| Field | What it holds |
|---|---|
| Provider | The upstream provider, named as the federation knows it: the entity ID of an [upstream SAML identity provider](../saml/upstream-identity-providers.md), or the `identity_provider` of a trusted issuer |
| Subject | The value that provider gives the person, compared byte for byte. It is not the `sub` this provider issues |
| Claims | The last snapshot of what the provider said of the person, empty when it said nothing |
| Linked at, last seen at | When the link was written, and when it was last written again |

**The pair names one person of the tenant.** The store holds one row per provider and subject, and linking a
pair to a second person is refused, naming the person it already names. Linking it again to the same person
is what a second run of an import does: the snapshot is replaced and the date it was last seen moves, the row
keeps its person.

**It is sealed.** The provider, the subject and the snapshot are personal data, sealed under the data key of
the tenant like every column of a person. A lookup matches two blind indexes beside them, keyed tags of the
provider and of the subject, and the uniqueness of the pair is held on those tags. The tag of the provider is
the one of the model on a column with few distinct values: it says which rows share a provider, which is the
price of the uniqueness of the pair. [Personal data](personal-data.md) says what that means.

## Federation writes them

At the first sign-in through an [upstream identity provider](../saml/federated-sign-in.md#the-person), the
person and their linked identity are created together, in one unit, all of it kept or none of it. The snapshot
holds the claims the provider said, by the names of OIDC Core §5.1, the address, and the telephone number when
it said one. At the next sign-ins, nothing is created: the snapshot is refreshed, and what the provider fills
is written again for a person it created.

**A person is found by their link and never by their address.** An address is given again to somebody else
when its holder leaves; a subject is not. So an address that another person of the tenant holds, as a mailbox
or as a username, refuses a first sign-in rather than linking that person on its own.

## An operator writes one by hand

For a person who exists already and is to sign in through a provider, or be named by the assertions of a
trusted issuer:

``` bash
bin/console beffroi:user:link alice 'https://idp.example.org/saml/metadata' 'the-subject-it-gives-alice'
```

| Argument | What it says |
|---|---|
| `username` | The user of this tenant |
| `provider` | The upstream provider, as the configuration that trusts it names it |
| `subject` | The subject that provider gives this user, compared byte for byte |

The command prints the username, the provider, the subject, the identifier of the row and the slug of the
tenant. Run again, it refreshes the link with an empty snapshot. A person linked that way signs in through
the provider under the link, with none of the rules of a first sign-in: the provider did not create them, so
nothing it fills is written of them, and only the snapshot of the link is refreshed.

No command removes a link.

## What reads them

| Reader | What it asks |
|---|---|
| [Signing in through an organisation](../saml/federated-sign-in.md) | The person a SAML assertion names: the link of that provider and that subject, created with the person at the first sign-in |
| [The JWT bearer grant](../oidc/grants/jwt-bearer.md), RFC 7523 §3 | The user an assertion of a trusted issuer is about: the link of the `identity_provider` that issuer is declared with and of the subject of the assertion. An assertion about somebody no link resolves, or about a disabled user, is refused as an assertion of an unknown issuer is, and no user is ever created there |

The person reads their links in the archive they ask for: one line per link, with the provider, the subject,
the snapshot and the two dates.
