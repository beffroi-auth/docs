---
title: Beffroi
description: An identity provider for the Symfony ecosystem. OAuth 2.0, OpenID Connect and SAML 2.0, on a pure-PHP core.
hide:
  - navigation
---

<div class="bf-hero" markdown>

<p class="bf-label">OAuth 2.0 · OpenID Connect · SAML 2.0 · PHP 8.4</p>

# The tower that decides who gets in.

<p class="bf-hero__lead">An identity provider for the Symfony ecosystem. On the map of a Symfony application
the interface is Symfony, the API is API Platform, and the identity provider is always somewhere else.
Beffroi paints that last box the same colour as the other two.</p>

[Get started](operators/getting-started/installation.md){ .md-button .md-button--primary }
[What is Beffroi?](the-project/what-is-beffroi.md){ .md-button }

</div>

!!! info "Beffroi is 0.x"

    These pages document `0.2.x`, not released yet. Until `1.0`, the public API may change between minor
    versions, and only the latest release is supported ([versions](the-project/versions.md)).

<div class="grid cards" markdown>

-   :beffroi-docs:{ .lg .middle } **Start here**

    ---

    What Beffroi is, what it refuses to do, the conformance it is tested for, and how it is versioned.

    [:beffroi-arrow-right: What is Beffroi?](the-project/what-is-beffroi.md)

-   :beffroi-code:{ .lg .middle } **Developers**

    ---

    For whoever writes an application that signs people in with Beffroi, a resource server that reads its
    tokens, or code on its packages: the protocol, the clients, the tokens and the ports.

    [:beffroi-arrow-right: The documentation for developers](developers/index.md)

-   :beffroi-server:{ .lg .middle } **Operators**

    ---

    For whoever installs, configures and runs an instance: the image, its variables, the tenant and its
    keys, SAML partners, the console, operating and observing it.

    [:beffroi-arrow-right: The documentation for operators](operators/index.md)

-   :beffroi-settings:{ .lg .middle } **Administrators**

    ---

    For whoever administers the tenants of an instance and their people, with the terminal client of the
    administration API.

    [:beffroi-arrow-right: The documentation for administrators](administrators/index.md)

-   :beffroi-user:{ .lg .middle } **Users**

    ---

    For a person with an account: signing in, passkeys and the second factor, the applications they allowed,
    and what is held about them.

    [:beffroi-arrow-right: The documentation for users](users/index.md)

</div>

## What it is made of

| Package | What it holds | Depends on |
|---|---|---|
| [`beffroi/core`](developers/core/index.md) | Tenants, users, credentials, linked identities, groups, authentication sessions, keys. Pure PHP, no protocol, no HTTP, no Doctrine | PHP, PSR interfaces, a handful of libraries |
| [`beffroi/oidc`](developers/oidc/index.md) | OAuth 2.0 and OpenID Connect: clients, authorization requests, grants, tokens, discovery, JWKS, UserInfo, logout. Pure PHP | `beffroi/core` |
| [`beffroi/saml`](operators/saml/index.md) | SAML 2.0: the identity provider and the service provider of a tenant, their metadata, single logout on the session of the core. Pure PHP | `beffroi/core` and the three packages below |
| [`beffroi/saml2-model`](developers/saml/packages.md#saml2-model) | The SAML 2.0 messages, assertions and metadata, read strictly, validated and written. No HTTP | `beffroi/xml-security` |
| [`beffroi/saml2-bindings`](developers/saml/packages.md#saml2-bindings) | The HTTP-Redirect and HTTP-POST bindings, on strings and arrays | `beffroi/saml2-model` |
| [`beffroi/xml-security`](developers/saml/packages.md#xml-security) | A safe DOM, XML Signature and XML Encryption | PHP, with `dom`, `libxml` and `openssl` |
| [`beffroi/beffroi`](operators/application/index.md) | The provider: the application that serves the protocols, with its configuration, controllers, security, persistence, pages and console, on FrankenPHP | the core and both protocols, plus Symfony |

## What it will not do

Secure by default means there is no option to do it wrong: no implicit flow, no password grant, PKCE with
`S256` only, redirect URIs compared exactly, `iss` in every authorization response. Those are properties of
the code, not settings of a file.

[:beffroi-arrow-right: Secure by default](the-project/secure-by-default.md)

## Where the rest lives

The code is one monorepo, [`beffroi-auth/beffroi`](https://github.com/beffroi-auth/beffroi), split read-only
into one repository per package. This site is written in
[`beffroi-auth/docs`](https://github.com/beffroi-auth/docs), one branch per version of the packages it
describes.

The website of the project is [beffroi.tech](https://beffroi.tech), and the project has an account on
[Bluesky](https://bsky.app/profile/beffroi.tech) and a page on
[LinkedIn](https://www.linkedin.com/company/beffroi-auth).
