---
title: What is Beffroi?
description: An OAuth 2.0 authorization server, an OpenID Provider and a SAML 2.0 identity provider written in PHP, installed in a Symfony application or deployed as a standalone one.
---

# What is Beffroi?

Beffroi is an OAuth 2.0 authorization server, an OpenID Connect provider and a SAML 2.0 identity provider,
written in PHP. It is the box that signs your users in, issues the tokens your APIs check, and tells the
applications you trust who is at the door. Where an organisation already runs an identity provider of its
own, it can send that organisation's people there to sign in, as a SAML service provider.

It comes in three shapes, and you choose one:

- **a Symfony bundle** you install in an application you already run;
- **a standalone application**, a Symfony skeleton on that bundle, which is the recommended deployment;
- **pure-PHP libraries** underneath, usable without Symfony, which is where the protocols actually live.

## What it is for

An identity provider has as many reasons to live in the team's own stack as its database does, and none
to be somewhere else by default. The protocol knowledge is the job of this project, not of the team that
installs it: you should be able to read what applies, replace it, and leave with your users.

## What it owns

Beffroi owns its identity model. It has its own user, its own credentials, its own linked identities, its
own groups, and its own tenant, and it never hooks onto the `User` entity of the application that hosts
it. A provider that borrows the host's user model cannot hold a stable subject identifier, cannot hold
several kinds of credential per person, and cannot be moved out of the application later.

A person in Beffroi can hold a password, a passkey, a TOTP secret and backup codes at the same time, each
one a credential of its own kind, each one revocable on its own. And a person is one person whichever
protocol reaches them: a browser signed in by OpenID Connect is signed in for SAML, and a session that ends
ends for both.

## What it refuses to do

The list is short, and none of it is behind an option:

- no implicit flow, no resource owner password credentials grant;
- PKCE with `S256` only, never `plain`;
- redirect URIs matched exactly, never by prefix or pattern;
- `iss` in every authorization response, so a client can tell who answered;
- no redirect followed to a third party, no boolean coming from a third party ever cast;
- in SAML, no signature under SHA-1, nothing encrypted in CBC, and no response taken that nobody asked for.

Those are rules of the code, not settings of a file. There is no `insecure_` option and no global
compatibility switch to turn them off. [Secure by default](secure-by-default.md) says why, and names the
few exceptions that exist, each one bounded.

## What proves it

The protocols are judged from outside. The conformance suite of the OpenID Foundation runs against the
provider in continuous integration, plan by plan, in the strict mode a certification submission asks
for. A green run nobody started is not a result, so the runs that matter are asked for by hand and read.
SAML has no certification programme, so it is judged by the implementations it has to work with,
SimpleSAMLphp and Microsoft Entra ID among them, and every signature it writes is verified by tools that are
not its own. [Conformance](conformance.md) says which plans run and what they cover.

## Where to go next

- [Packages](packages.md), if you want to know which of the eight you need.
- [Getting started](../getting-started/installation.md), if you want a provider answering on your machine.
- [OAuth 2.0 and OpenID Connect](../oidc/index.md), or [SAML 2.0](../saml/index.md), if you came for a
  protocol.
