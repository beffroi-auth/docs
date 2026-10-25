---
title: Identity core
description: What beffroi/core holds: tenants, users, credentials, groups, sessions and keys, in pure PHP.
---

# Identity core

`beffroi/core` is the identity model and nothing else. It knows no protocol, no HTTP, no container and no
ORM: no class in it has ever heard of OAuth, of a `Request` or of Doctrine. What it needs from the outside,
it asks for through a port.

That is what makes it testable without a kernel, and what makes the provider's identity model its own
rather than borrowed from whatever application hosts it.

## What it holds

<div class="grid cards" markdown>

-   **[Tenants](tenants.md)**

    ---

    The unit everything else belongs to. One issuer, one set of keys, one population of users.

-   **[Users](users.md)**

    ---

    A person, their username, their standard claims, and the subject identifier clients know them by.

-   **[Credentials](credentials/index.md)**

    ---

    A password, a passkey, a TOTP secret, backup codes. Several per person, each one its own kind.

-   **[Authentication sessions](authentication-sessions.md)**

    ---

    What a person proved, when, and from where. What a grant reads to say `acr` and `auth_time`.

-   **[Groups](groups.md)**

    ---

    Membership, and where each membership came from: declared here, or pushed by a directory.

-   **[Linked identities](linked-identities.md)**

    ---

    The same person at an upstream provider, so federation does not duplicate them.

-   **[Keys](keys.md)**

    ---

    The signing keys of the tenant, sealed by a key management service, rotated without an outage.

-   **[Personal data](personal-data.md)**

    ---

    Sealed columns, blind indexes, and data keys that can be rewrapped while the provider runs.

</div>

## How it is laid out

Four layers, and the dependencies only ever point inwards.

| Layer | What is in it | What it may depend on |
|---|---|---|
| `Domain` | The model and its rules. A rule of an entity lives on the entity | PHP, PSR interfaces, and the libraries the model is built from |
| `Port` | The interfaces the outside implements: repositories, clock, hashers, key management | `Domain` |
| `Application` | The use cases that orchestrate. One responsibility each, named after what they do: `SessionOpener`, `SessionTerminator`, `UserProvisioner` | `Domain` and `Port` |
| `Bridge` | The implementations: a password hasher, a TOTP library, an in-memory repository for tests | all of the above, and the library it bridges |

A static analysis of the dependency graph fails the build when a layer reaches where it is not allowed to,
so the rule is not a convention anybody can forget.

## Adding to it

A new kind of credential, a new password algorithm, a new source of randomness is a class that implements
the interface of its capability, tagged in the wiring. It is never a new case in a `match`, never a new
value in an enumeration of kinds, and never a class name read from a string. A kind names itself, and it
declares what it can do by the interfaces it implements: a credential that can be revoked implements
`RevocableCredentialInterface`, one identified at an upstream provider implements
`ExternallyIdentifiedCredentialInterface`.

[:beffroi-arrow-right: The ports of the core](ports.md)
