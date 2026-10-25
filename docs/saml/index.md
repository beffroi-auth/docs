---
title: SAML 2.0
description: SAML 2.0 in both roles, the identity provider of the applications that speak it and the service provider of the identity providers upstream of a tenant, on the same people and the same sessions as OpenID Connect.
---

# SAML 2.0

SAML 2.0 is still what a large part of the installed base speaks, and an identity provider that cannot
answer it cannot replace the one a company already has. Beffroi serves it in both roles, on the tenant, the
people and the sessions OpenID Connect uses: one person of the core, two protocols to reach them. A browser
signed in by one is signed in for the other, and a session that ends ends for both.

## The two roles

| Role | What it is for | Turned on by |
|---|---|---|
| [Identity provider](identity-provider.md) | An application that speaks SAML signs its users in against Beffroi: a SimpleSAMLphp or Shibboleth service provider, a product that asks for a SAML identity provider, Microsoft Entra ID federating its guests | `beffroi.saml.identity_provider` |
| [Service provider](upstream-identity-providers.md) | Beffroi signs a person in against the SAML identity provider of their organisation, found by the domain of their address, and then answers the OpenID Connect client or the page that was waiting | `beffroi.saml.service_provider` |

``` mermaid
graph LR
  sp["An application<br/><small>SAML service provider</small>"] -- "AuthnRequest" --> b["Beffroi"]
  rp["A client<br/><small>OpenID Connect</small>"] -- "authorization request" --> b
  b -- "AuthnRequest" --> up["The identity provider<br/>of an organisation<br/><small>upstream</small>"]
```

Both roles are off by default, and each is a switch of its own. A deployment that turns neither on serves no
SAML endpoint and draws no SAML key, so nothing of this section costs anything to a provider that does not
use it.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    saml:
        identity_provider: true
        service_provider: true
```

The peers themselves, the service providers on one side and the upstream identity providers on the other,
are declared in the same section, keyed by their entity ID. They are configuration and nothing else: no
request registers one and no page edits one.

## What is served

Paths are relative to the issuer, as every route of the bundle.

| Method | Path | Role | What it is |
|---|---|---|---|
| `GET` | `/saml/metadata` | identity provider | The metadata of the identity provider. Its URL is its entity ID |
| `GET` `POST` | `/saml/sso` | identity provider | Single sign-on, over HTTP-Redirect and HTTP-POST at the one URL |
| `GET` `POST` | `/saml/slo` | identity provider | Single logout, over both bindings, a request or an answer |
| `GET` | `/saml/sp/metadata` | service provider | The metadata of the service provider. Its URL is its entity ID unless the deployment names another |
| `GET` | `/saml/sp/metadata/{identity provider}` | service provider | The same metadata with the encryption certificates meant for one upstream identity provider |
| `POST` | `/saml/sp/acs` | service provider | The assertion consumer service, over HTTP-POST |

A role the deployment did not turn on answers `404` at its endpoints, whatever keys the tenant holds.
[The endpoints](../reference/endpoints.md#saml-20) lists the routes behind them, the ones a login sends a
browser back through included.

## What is always true

None of the rules below has an option. They are properties of the code, held by its tests, and a peer that
needs one of them relaxed is a peer this provider does not serve.

| Rule | Why |
|---|---|
| Every assertion is signed, and every response over it, under RSA-SHA256 | A service provider that verifies either finds a signature, and an assertion stands alone as the statement of the tenant |
| SHA-1, MD5, HMAC, DSA and ECDSA are refused, in an XML signature and over the query string of HTTP-Redirect | A verifier that honours the algorithm a message names verifies what the attacker made verifiable |
| An assertion sent encrypted is encrypted under AES-256-GCM, its key under RSA-OAEP. Nothing is ever encrypted in CBC | CBC authenticates nothing, which is what padding oracles are made of |
| A message is read only in what a signature covers | Signature wrapping hands the verifier one element and the reader another |
| A peer's keys come from its metadata, never from the `KeyInfo` of a message | A message that names the key it is verified with verifies under the attacker's key |
| Every assertion and every logout message is accepted once | A message taken off the wire is not a second login, nor a second logout |
| A peer is declared by the deployment, and its metadata come from a file of the deployment or an `https` URL, no redirect followed | A peer registered by a request, or metadata fetched wherever a redirect points, is a peer an attacker chose |
| Every endpoint a browser is sent to is `https` on a host | An assertion posted in clear, or to a `javascript:` URL, is an assertion given away |
| A response nobody asked for is refused, and no assertion is sent unasked | Nothing binds an unsolicited response to the browser that carries it, which is how a victim is signed in to an attacker's account |

The XML underneath goes through one hardened loader, which refuses a document type declaration, an entity,
two elements under the same identifier and a document past its bounds before anything reads it, and
nothing else in the provider parses XML. [The SAML packages](packages.md) says what each of the libraries
guarantees.

## What is not served

- The Artifact and SOAP bindings, SAML 1.x and WS-Federation. A single logout reaches a service provider
  through the browser that ended the session, never server to server.
- Metadata aggregates of an inter-institution federation: an `md:EntitiesDescriptor` is refused by name,
  and each peer is declared on its own.
- An administration interface for the peers. They are configuration, and the console reads and refreshes
  their metadata.
- Single logout with an upstream identity provider, which the metadata of the service provider do not
  announce.
- Sign-on started by an identity provider. Every assertion the identity provider writes answers an
  `AuthnRequest`, and every response the service provider takes answers a request it sent.
- The groups an upstream identity provider asserts are memberships of the tenant. No claim hands them to a
  client of OpenID Connect.

## In this section

| Page | What it covers |
|---|---|
| [The identity provider](identity-provider.md) | Turning the role on, its key, its certificate and its metadata |
| [Service providers](service-providers.md) | Declaring one: its metadata, the attributes it receives, the signature its requests need, the encryption it asks for |
| [Single sign-on](single-sign-on.md) | What a request is answered with, the session it reuses and the assertion it is given |
| [Single logout](single-logout.md) | A logout a service provider asks for, and the one the provider tells every service provider of a session about |
| [Upstream identity providers](upstream-identity-providers.md) | The tenant as a service provider: its metadata, the identity providers it trusts and what it reads of their assertions |
| [Signing in through an organisation](federated-sign-in.md) | The login page that asks for the address first, the person created at the first sign-in, and the session it opens |
| [Microsoft Entra ID](microsoft-entra-id.md) | Entra federating its guests to Beffroi, and Entra as the upstream identity provider of a tenant |
| [The SAML packages](packages.md) | `xml-security`, `saml2-model` and `saml2-bindings`, which carry the format, and what each one guarantees |
