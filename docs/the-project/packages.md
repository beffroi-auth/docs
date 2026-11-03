---
title: Packages
description: The seven packages of Beffroi, what each one depends on, and which one you need.
---

# Packages

Beffroi is developed as one monorepo, [`beffroi-auth/beffroi`](https://github.com/beffroi-auth/beffroi), and
published as seven packages. Each package is split read-only into its own repository, so you can read the
history of one part without the rest.

| Package | Namespace | What it is | Repository |
|---|---|---|---|
| `beffroi/core` | `Beffroi\Core` | The identity model: tenants, people, credentials, linked identities, groups, sessions, keys | [beffroi-auth/core](https://github.com/beffroi-auth/core) |
| `beffroi/oidc` | `Beffroi\Oidc` | OAuth 2.0 and OpenID Connect | [beffroi-auth/oidc](https://github.com/beffroi-auth/oidc) |
| `beffroi/saml` | `Beffroi\Saml` | SAML 2.0, the identity provider and the service provider of a tenant | [beffroi-auth/saml](https://github.com/beffroi-auth/saml) |
| `beffroi/saml2-model` | `Beffroi\Saml2\Model` | The SAML 2.0 messages, assertions and metadata, read strictly and written | [beffroi-auth/saml2-model](https://github.com/beffroi-auth/saml2-model) |
| `beffroi/saml2-bindings` | `Beffroi\Saml2\Bindings` | The HTTP-Redirect and HTTP-POST bindings | [beffroi-auth/saml2-bindings](https://github.com/beffroi-auth/saml2-bindings) |
| `beffroi/xml-security` | `Beffroi\Xml` | A safe DOM, XML Signature and XML Encryption | [beffroi-auth/xml-security](https://github.com/beffroi-auth/xml-security) |
| `beffroi/op` | `App` | The provider, the application that carries the Symfony integration | [beffroi-auth/op](https://github.com/beffroi-auth/op) |

## Which one do I need?

=== "I want a provider"

    Deploy `beffroi/op`, the application. It holds the protocols, the identity model, the pages, the
    persistence and the console, on FrankenPHP, and a deployment sets it through its environment.

    [:beffroi-arrow-right: The application](../application/index.md)

=== "I run a Symfony application"

    Deploy `beffroi/op` beside it, and sign people in to your application through it with the `oidc_login`
    authenticator of Symfony. Your application is a client of the provider: nothing of the provider is
    installed in it.

    [:beffroi-arrow-right: A Symfony relying party](../getting-started/a-symfony-relying-party.md)

=== "I want it inside code of my own"

    Require `beffroi/oidc`, `beffroi/saml`, or both. They are pure PHP: they know no HTTP, no container and
    no ORM, and they talk to the world through ports you implement. What you write around them is your own
    integration.

    [:beffroi-arrow-right: The ports of the protocol](../oidc/ports.md)

=== "I only need to read and write SAML"

    Require `beffroi/saml2-bindings`, which brings `beffroi/saml2-model` and `beffroi/xml-security`. They know
    nothing of Beffroi: the messages, their signatures and their encryption, for any PHP project that speaks
    SAML.

    [:beffroi-arrow-right: The SAML packages](../saml/packages.md)

## What depends on what

The direction never reverses. The core knows nothing of the protocols, the protocols know nothing of each
other nor of Symfony, and the application is the only place where a `Request`, a container or a Doctrine
entity manager appears.

``` mermaid
graph RL
  op["beffroi/op<br/><small>the application</small>"] --> oidc["beffroi/oidc"]
  op --> saml["beffroi/saml"]
  op --> core["beffroi/core"]
  oidc --> core
  saml --> core
  saml --> bindings["beffroi/saml2-bindings"]
  bindings --> model["beffroi/saml2-model"]
  model --> xml["beffroi/xml-security"]
```

Inside the pure-PHP packages of the provider, the core and the two protocols, the same rule is drawn again,
in four layers: `Domain` holds the model and its rules, `Port` the interfaces the outside implements,
`Application` the use cases that orchestrate them, and `Bridge` the implementations that need a library. A
static analysis of the dependency graph fails the build when a package or a layer reaches where it should
not.

## Requirements

| What | Which |
|---|---|
| PHP | 8.4 or later, with `intl`; `zip` for the application; `dom`, `libxml` and `openssl` for the XML of SAML, `zlib` for its HTTP-Redirect binding |
| Symfony | 8.2, for the application |
| Database | PostgreSQL, through Doctrine ORM |
| Licence | MIT, for all seven packages |

The cryptography of the tokens and the credentials is not written here. Signatures and encryption of JOSE
come from [`web-token/jwt-library`](https://github.com/web-token/jwt-framework), WebAuthn from
[`web-auth/webauthn-lib`](https://github.com/web-auth/webauthn-framework), TOTP from
[`spomky-labs/otphp`](https://github.com/Spomky-Labs/otphp), certificates from
[`spomky-labs/pki-framework`](https://github.com/Spomky-Labs/pki-framework), and key management from
`symfony/key-management`. The XML of SAML is the exception, written here on purpose, because no library of
the PHP ecosystem reads it safely by construction: [the SAML packages](../saml/packages.md) say what that
buys.
