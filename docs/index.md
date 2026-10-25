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

[Get started](getting-started/installation.md){ .md-button .md-button--primary }
[What is Beffroi?](the-project/what-is-beffroi.md){ .md-button }

</div>

!!! info "This documentation describes a version that is not released yet"

    No `beffroi/*` package is published on Packagist at this point. Every page here states what the code
    does today, in the branch this version of the documentation follows. What is not written yet is marked
    as a stub rather than guessed at.

<div class="grid cards" markdown>

-   :beffroi-docs:{ .lg .middle } **Start here**

    ---

    What Beffroi is, what it refuses to do, and the packages it is made of.

    [:beffroi-arrow-right: What is Beffroi?](the-project/what-is-beffroi.md)

-   :beffroi-server:{ .lg .middle } **Run a provider**

    ---

    The standalone application, a tenant, a signing key, a first client, a user who signs in.

    [:beffroi-arrow-right: Getting started](getting-started/installation.md)

-   :beffroi-package:{ .lg .middle } **Add it to an application**

    ---

    The bundle in an existing Symfony application: configuration, routes, persistence, pages.

    [:beffroi-arrow-right: The Symfony bundle](symfony-bundle/index.md)

-   :beffroi-token:{ .lg .middle } **Read the protocol**

    ---

    Clients, grants, tokens, discovery, logout, and what each endpoint answers.

    [:beffroi-arrow-right: OAuth 2.0 and OpenID Connect](oidc/index.md)

-   :beffroi-federation:{ .lg .middle } **Speak SAML**

    ---

    The identity provider of the applications that speak SAML 2.0, and the service provider of the identity
    provider of an organisation.

    [:beffroi-arrow-right: SAML 2.0](saml/index.md)

</div>

## What it is made of

| Package | What it holds | Depends on |
|---|---|---|
| [`beffroi/core`](core/index.md) | Tenants, users, credentials, linked identities, groups, authentication sessions, keys. Pure PHP, no protocol, no HTTP, no Doctrine | PHP, PSR interfaces, a handful of libraries |
| [`beffroi/oidc`](oidc/index.md) | OAuth 2.0 and OpenID Connect: clients, authorization requests, grants, tokens, discovery, JWKS, UserInfo, logout. Pure PHP | `beffroi/core` |
| [`beffroi/saml`](saml/index.md) | SAML 2.0: the identity provider and the service provider of a tenant, their metadata, single logout on the session of the core. Pure PHP | `beffroi/core` and the three packages below |
| [`beffroi/saml2-model`](saml/packages.md#saml2-model) | The SAML 2.0 messages, assertions and metadata, read strictly, validated and written. No HTTP | `beffroi/xml-security` |
| [`beffroi/saml2-bindings`](saml/packages.md#saml2-bindings) | The HTTP-Redirect and HTTP-POST bindings, on strings and arrays | `beffroi/saml2-model` |
| [`beffroi/xml-security`](saml/packages.md#xml-security) | A safe DOM, XML Signature and XML Encryption | PHP, with `dom`, `libxml` and `openssl` |
| [`beffroi/symfony-bundle`](symfony-bundle/index.md) | The Symfony integration: configuration, controllers, security, persistence, login and consent pages | the core and both protocols, plus Symfony |
| [`beffroi/op`](application/index.md) | The standalone application, on FrankenPHP. The recommended deployment | the bundle |

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
