---
title: Packages
description: The four packages of Beffroi, what each one depends on, and which one to install.
---

# Packages

Beffroi is developed as one monorepo, [`beffroi-auth/beffroi`](https://github.com/beffroi-auth/beffroi), and
published as four packages. Each package is split read-only into its own repository, so you can read the
history of one part without the rest.

| Package | Namespace | Repository |
|---|---|---|
| `beffroi/core` | `Beffroi\Core` | [beffroi-auth/core](https://github.com/beffroi-auth/core) |
| `beffroi/oidc` | `Beffroi\Oidc` | [beffroi-auth/oidc](https://github.com/beffroi-auth/oidc) |
| `beffroi/symfony-bundle` | `Beffroi\Bundle` | [beffroi-auth/symfony-bundle](https://github.com/beffroi-auth/symfony-bundle) |
| `beffroi/op` | `App` | [beffroi-auth/op](https://github.com/beffroi-auth/op) |

## Which one do I install?

=== "I run a Symfony application"

    Require `beffroi/symfony-bundle`. It pulls the core and the protocol with it, and brings the
    controllers, the Doctrine mapping, the console commands and the login and consent pages.

    [:octicons-arrow-right-24: Installing the bundle](../symfony-bundle/installation.md)

=== "I want a provider of its own"

    Deploy `beffroi/op`, the standalone application. It is the bundle, a Symfony skeleton, FrankenPHP and
    nothing you have to assemble yourself.

    [:octicons-arrow-right-24: The standalone application](../application/index.md)

=== "I am not using Symfony"

    Require `beffroi/oidc`. It is pure PHP: it knows no HTTP, no container and no ORM, and it talks to
    the world through ports you implement.

    [:octicons-arrow-right-24: The ports of the protocol](../oidc/ports.md)

## What depends on what

The direction never reverses. The core knows nothing of the protocol, the protocol knows nothing of
Symfony, and the bundle is the only place where a `Request`, a container or a Doctrine entity manager
appears.

``` mermaid
graph RL
  op["beffroi/op<br/><small>the application</small>"] --> bundle["beffroi/symfony-bundle"]
  bundle --> oidc["beffroi/oidc"]
  bundle --> core["beffroi/core"]
  oidc --> core
```

Inside the two pure-PHP packages the same rule is drawn again, in four layers: `Domain` holds the model
and its rules, `Port` the interfaces the outside implements, `Application` the use cases that orchestrate
them, and `Bridge` the implementations that need a library. A static analysis of the dependency graph
fails the build when a layer reaches where it should not.

## Requirements

| What | Which |
|---|---|
| PHP | 8.4 or later |
| Symfony | 8.2, for the bundle and the application |
| Database | PostgreSQL, through Doctrine ORM |
| Licence | MIT, for all four packages |

The cryptography is not written here. Signatures and encryption come from
[`web-token/jwt-library`](https://github.com/web-token/jwt-framework), WebAuthn from
[`web-auth/webauthn-lib`](https://github.com/web-auth/webauthn-framework), TOTP from
[`spomky-labs/otphp`](https://github.com/Spomky-Labs/otphp), certificates from
[`spomky-labs/pki-framework`](https://github.com/Spomky-Labs/pki-framework), and key management from
`symfony/key-management`.
