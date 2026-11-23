---
title: Packages
description: The packages of Beffroi and its application, what each one depends on, and which one you need.
---

# Packages

Beffroi is developed as one monorepo, [`beffroi-auth/beffroi`](https://github.com/beffroi-auth/beffroi), and
split read-only into eight repositories, one per part, so you can read the history of one part without the
rest. Seven parts are packages published on Packagist. The application, `beffroi/beffroi`, is not: it is
deployed from its image, `ghcr.io/beffroi-auth/beffroi`.

| Package | Namespace | What it is | Repository |
|---|---|---|---|
| `beffroi/core` | `Beffroi\Core` | The identity model: tenants, people, credentials, linked identities, groups, sessions, keys | [beffroi-auth/core](https://github.com/beffroi-auth/core) |
| `beffroi/oidc` | `Beffroi\Oidc` | OAuth 2.0 and OpenID Connect | [beffroi-auth/oidc](https://github.com/beffroi-auth/oidc) |
| `beffroi/saml` | `Beffroi\Saml` | SAML 2.0, the identity provider and the service provider of a tenant | [beffroi-auth/saml](https://github.com/beffroi-auth/saml) |
| `beffroi/saml2-model` | `Beffroi\Saml2\Model` | The SAML 2.0 messages, assertions and metadata, read strictly and written | [beffroi-auth/saml2-model](https://github.com/beffroi-auth/saml2-model) |
| `beffroi/saml2-bindings` | `Beffroi\Saml2\Bindings` | The HTTP-Redirect and HTTP-POST bindings | [beffroi-auth/saml2-bindings](https://github.com/beffroi-auth/saml2-bindings) |
| `beffroi/xml-security` | `Beffroi\Xml` | A safe DOM, XML Signature and XML Encryption | [beffroi-auth/xml-security](https://github.com/beffroi-auth/xml-security) |
| `beffroi/beffroi` | `App` | The provider, the application that carries the Symfony integration | [beffroi-auth/application](https://github.com/beffroi-auth/application) |
| `beffroi/tui` | `Beffroi\Tui` | The terminal client of the administration of an instance: it talks to the administration API over HTTP and installs none of the packages above | [beffroi-auth/tui](https://github.com/beffroi-auth/tui) |

## Which one do I need?

=== "I want a provider"

    Deploy `beffroi/beffroi`, the application, from its image `ghcr.io/beffroi-auth/beffroi`. It holds the protocols, the identity model, the pages, the
    persistence and the console, on FrankenPHP, and a deployment sets it through its environment.

    [:beffroi-arrow-right: The application](../operators/application/index.md)

=== "I run a Symfony application"

    Deploy `beffroi/beffroi` beside it, and sign people in to your application through it with the `oidc_login`
    authenticator of Symfony. Your application is a client of the provider: nothing of the provider is
    installed in it.

    [:beffroi-arrow-right: Add sign-in to a Symfony application](connect/symfony.md)

=== "I want it inside code of my own"

    Require `beffroi/oidc`, `beffroi/saml`, or both. They are pure PHP: they know no HTTP, no container and
    no ORM, and they talk to the world through ports you implement. What you write around them is your own
    integration.

    !!! note "Symfony 8.2 is in beta"

        `beffroi/core`, which both require, requires `symfony/key-management` 8.2, published only as
        pre-releases until Symfony 8.2.0 is out. Until then, the project that requires them sets
        `"minimum-stability": "beta"` and `"prefer-stable": true` in its `composer.json`.

    [:beffroi-arrow-right: The ports of the protocol](oidc/ports.md)

=== "I only need to read and write SAML"

    Require `beffroi/saml2-bindings`, which brings `beffroi/saml2-model` and `beffroi/xml-security`. They know
    nothing of Beffroi: the messages, their signatures and their encryption, for any PHP project that speaks
    SAML.

    [:beffroi-arrow-right: The SAML packages](saml/packages.md)

=== "I administer an instance from a terminal"

    `beffroi/tui` is the terminal client of the administration API of an instance: a client of the provider like
    any other, which talks to it over HTTP and installs none of the packages above.

    [:beffroi-arrow-right: The terminal client](../administrators/terminal-client.md)

## What depends on what

The direction never reverses. The core knows nothing of the protocols, the protocols know nothing of each
other nor of Symfony, and the application is the only place where a `Request`, a container or a Doctrine
entity manager appears.

``` mermaid
graph RL
  app["beffroi/beffroi<br/><small>the application</small>"] --> oidc["beffroi/oidc"]
  app --> saml["beffroi/saml"]
  app --> core["beffroi/core"]
  oidc --> core
  saml --> core
  saml --> bindings["beffroi/saml2-bindings"]
  bindings --> model["beffroi/saml2-model"]
  model --> xml["beffroi/xml-security"]
```

The terminal client, `beffroi/tui`, depends on none of them: it is a client of the administration API of an
instance, and reads it over HTTP like any other client of the provider.

Inside the pure-PHP packages of the provider, the core and the two protocols, the same rule is drawn again,
in four layers: `Domain` holds the model and its rules, `Port` the interfaces the outside implements,
`Application` the use cases that orchestrate them, and `Bridge` the implementations that need a library. A
static analysis of the dependency graph fails the build when a package or a layer reaches where it should
not.

## Requirements

| What | Which |
|---|---|
| PHP | 8.4 or later, with `intl`; `zip` for the application; `dom`, `libxml` and `openssl` for the XML of SAML, `zlib` for its HTTP-Redirect binding; `dom`, `filter`, `iconv`, `libxml`, `mbstring`, `openssl`, `simplexml`, `sodium` and `zlib` for the PHAR of the terminal client, whose executables carry their own PHP |
| Symfony | 8.2, for the application and the terminal client |
| Database | PostgreSQL, through Doctrine ORM |
| Licence | MIT, for every package and for the application |

The cryptography of the tokens and the credentials is not written here. Signatures and encryption of JOSE
come from [`web-token/jwt-library`](https://github.com/web-token/jwt-framework), WebAuthn from
[`web-auth/webauthn-lib`](https://github.com/web-auth/webauthn-framework), TOTP from
[`spomky-labs/otphp`](https://github.com/Spomky-Labs/otphp), certificates from
[`spomky-labs/pki-framework`](https://github.com/Spomky-Labs/pki-framework), and key management from
`symfony/key-management`. The packages require `web-token/jwt-library` 4.2.7 and `web-auth/webauthn-lib` 5.3.15
at least, below which published advisories apply. The XML of SAML is the exception, written here on purpose, because no library of
the PHP ecosystem reads it safely by construction: [the SAML packages](saml/packages.md) say what that
buys.
