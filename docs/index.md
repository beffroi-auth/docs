---
title: Beffroi
description: An identity provider for the Symfony ecosystem. OAuth 2.0 and OpenID Connect first, on a pure-PHP core.
hide:
  - navigation
---

<div class="bf-hero" markdown>

<p class="bf-hero__eyebrow">OAuth 2.0 · OpenID Connect · PHP 8.4</p>

# Beffroi

<p class="bf-hero__tagline">An OpenID Provider for the Symfony ecosystem. On the map of a Symfony
application the interface is Symfony, the API is API Platform, and the identity provider is always
somewhere else. Beffroi paints that last box the same colour as the other two.</p>

[Get started](getting-started/installation.md){ .md-button .md-button--primary }
[What is Beffroi?](the-project/what-is-beffroi.md){ .md-button }

</div>

!!! info "This documentation describes a version that is not released yet"

    No `beffroi/*` package is published on Packagist at this point, and the provider is not OpenID
    Certified yet. Every page here states what the code does today, in the branch this version of the
    documentation follows. What is not written yet is marked as a stub rather than guessed at.

<div class="grid cards" markdown>

-   :material-compass-outline:{ .lg .middle } **Start here**

    ---

    What Beffroi is, what it refuses to do, and the shape of the three packages.

    [:octicons-arrow-right-24: What is Beffroi?](the-project/what-is-beffroi.md)

-   :material-server-outline:{ .lg .middle } **Run a provider**

    ---

    The standalone application, a tenant, a signing key, a first client, a user who signs in.

    [:octicons-arrow-right-24: Getting started](getting-started/installation.md)

-   :material-language-php:{ .lg .middle } **Add it to an application**

    ---

    The bundle in an existing Symfony application: configuration, routes, persistence, pages.

    [:octicons-arrow-right-24: The Symfony bundle](symfony-bundle/index.md)

-   :material-key-chain-variant:{ .lg .middle } **Read the protocol**

    ---

    Clients, grants, tokens, discovery, logout, and what each endpoint answers.

    [:octicons-arrow-right-24: OAuth 2.0 and OpenID Connect](oidc/index.md)

</div>

## What it is made of

| Package | What it holds | Depends on |
|---|---|---|
| [`beffroi/core`](core/index.md) | Tenants, users, credentials, linked identities, groups, authentication sessions, keys. Pure PHP, no protocol, no HTTP, no Doctrine | PHP, PSR interfaces, a handful of libraries |
| [`beffroi/oidc`](oidc/index.md) | OAuth 2.0 and OpenID Connect: clients, authorization requests, grants, tokens, discovery, JWKS, UserInfo, logout. Pure PHP | `beffroi/core` |
| [`beffroi/symfony-bundle`](symfony-bundle/index.md) | The Symfony integration: configuration, controllers, security, persistence, login and consent pages | both, plus Symfony |
| [`beffroi/op`](application/index.md) | The standalone application, on FrankenPHP. The recommended deployment | the bundle |

## What it will not do

Secure by default means there is no option to do it wrong: no implicit flow, no password grant, PKCE with
`S256` only, redirect URIs compared exactly, `iss` in every authorization response. Those are properties of
the code, not settings of a file.

[:octicons-arrow-right-24: Secure by default](the-project/secure-by-default.md)

## Where the rest lives

The code is one monorepo, [`beffroi-auth/beffroi`](https://github.com/beffroi-auth/beffroi), split read-only
into one repository per package. This site is written in
[`beffroi-auth/docs`](https://github.com/beffroi-auth/docs), one branch per version of the packages it
describes.
