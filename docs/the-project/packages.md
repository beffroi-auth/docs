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

    [:beffroi-arrow-right: The application](../application/index.md)

=== "I run a Symfony application"

    Deploy `beffroi/beffroi` beside it, and sign people in to your application through it with the `oidc_login`
    authenticator of Symfony. Your application is a client of the provider: nothing of the provider is
    installed in it.

    [:beffroi-arrow-right: Add sign-in to a Symfony application](../getting-started/symfony.md)

=== "I want it inside code of my own"

    Require `beffroi/oidc`, `beffroi/saml`, or both. They are pure PHP: they know no HTTP, no container and
    no ORM, and they talk to the world through ports you implement. What you write around them is your own
    integration.

    !!! note "Symfony 8.2 is in beta"

        `beffroi/core`, which both require, requires `symfony/key-management` 8.2, published only as
        pre-releases until Symfony 8.2.0 is out. Until then, the project that requires them sets
        `"minimum-stability": "beta"` and `"prefer-stable": true` in its `composer.json`.

    [:beffroi-arrow-right: The ports of the protocol](../oidc/ports.md)

=== "I only need to read and write SAML"

    Require `beffroi/saml2-bindings`, which brings `beffroi/saml2-model` and `beffroi/xml-security`. They know
    nothing of Beffroi: the messages, their signatures and their encryption, for any PHP project that speaks
    SAML.

    [:beffroi-arrow-right: The SAML packages](../saml/packages.md)

=== "I administer an instance from a terminal"

    `beffroi/tui` is the terminal client of the administration API of an instance: a client of the provider like
    any other, which talks to it over HTTP and installs none of the packages above.

    Each [release](https://github.com/beffroi-auth/beffroi/releases) carries it as `beffroi-tui.phar`, for PHP 8.4
    or later, and as an executable that carries its own PHP, for Linux on x86_64 and on arm64 and for macOS on
    Apple silicon. `SHA256SUMS` holds their digests, and `SHA256SUMS.asc` is its signature by the key that signs
    the release tags, `5E85 361F C66B B177 1393  8831 0B2A 1B99 31D6 2A89`, published at
    [github.com/Spomky.gpg](https://github.com/Spomky.gpg). There is no Windows build: the client drives the
    terminal through `stty`.

    ``` bash
    curl -fsSL https://github.com/Spomky.gpg | gpg --import
    gpg --verify SHA256SUMS.asc SHA256SUMS
    sha256sum --check --ignore-missing SHA256SUMS
    ```

    `beffroi-tui --version` prints the release a file was built from, and the client shows it on its home page
    and in its instance section. When the administration opens, before any sign-in, a release looks once for a
    newer release of its line, `0.1.*` for `0.1.0`, in the GitHub API and without any credential, and the
    screen names it with the command that installs it. Nothing turns that look off; on a machine that cannot
    reach GitHub, the screen says the update was not checked.

    ``` bash
    beffroi-tui self-update
    ./beffroi-tui-linux-x86_64 self-update      # an executable kept under its own name
    ```

    `self-update` replaces the PHAR or the executable that runs by the same file of the newest release of its
    line, and runs the verification above for you: `gpgv` checks `SHA256SUMS.asc` under the release key the
    client carries, never one fetched at run time, before the file is downloaded, and the file must match its
    line of `SHA256SUMS`, or nothing is replaced. It needs `gpgv` on the `PATH` and write access to the
    directory the program sits in, asks for no more privileges, and has no option: a copy in a directory only
    root writes to, such as `/usr/local/bin`, is refused. It never moves to another line, where a `0.x`
    version may break what it talks to: the next line is a new download. A copy installed by Composer is
    updated by Composer, and a build of anything but a release does not replace itself.

    The client reaches `api.github.com` for the list of releases and `github.com` for their files, which GitHub
    answers with one redirection to the host it stores them on. That redirection is followed once, to an
    `https` address only; no other request of the client follows one.

    [:beffroi-arrow-right: The administration plane](../reference/endpoints.md#the-administration-plane)

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
`symfony/key-management`. The XML of SAML is the exception, written here on purpose, because no library of
the PHP ecosystem reads it safely by construction: [the SAML packages](../saml/packages.md) say what that
buys.
