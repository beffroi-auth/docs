---
title: Specifications
description: The specifications Beffroi implements, the ones it refuses, and where each one is documented.
---

# Specifications

A page of this site cites the specification it describes by number and section, so you can read the source
rather than this paraphrase of it. The table below is the index.

## OAuth 2.0

| Specification | What it brings | Page |
|---|---|---|
| RFC 6749 | The framework: clients, authorization requests, grants | [Authorization request](../oidc/authorization-request.md) |
| RFC 6750 | Bearer tokens on a resource server | [Access tokens](../oidc/tokens/access-tokens.md) |
| RFC 7009 | Token revocation | [Introspection and revocation](../oidc/introspection-and-revocation.md) |
| RFC 7521, RFC 7523 | Client authentication and grants by JWT assertion | [Client authentication](../oidc/client-authentication.md), [JWT bearer](../oidc/grants/jwt-bearer.md) |
| RFC 7591, RFC 7592 | Dynamic client registration, and managing a registration | [Dynamic registration](../oidc/dynamic-registration.md) |
| RFC 7636 | PKCE, mandatory here, `S256` only | [Authorization request](../oidc/authorization-request.md) |
| RFC 7662 | Token introspection | [Introspection and revocation](../oidc/introspection-and-revocation.md) |
| RFC 8414 | Authorization server metadata | [Discovery and JWKS](../oidc/discovery-and-jwks.md) |
| RFC 8628 | The device authorization grant | [Device code](../oidc/grants/device-code.md) |
| RFC 8693 | Token exchange, delegation and impersonation | [Token exchange](../oidc/grants/token-exchange.md) |
| RFC 8705 | Mutual TLS client authentication and certificate-bound tokens | [Mutual TLS](../oidc/sender-constrained/mutual-tls.md) |
| RFC 8707 | Resource indicators, the audience a client asks for | [Resources](../oidc/resources.md) |
| RFC 7800 | The `cnf` claim: the key a token is bound to | [Sender-constrained tokens](../oidc/sender-constrained/index.md) |
| RFC 9068 | The JWT profile of access tokens, `at+jwt` | [Access tokens](../oidc/tokens/access-tokens.md) |
| RFC 9101 | Request objects, the signed authorization request | [Request objects](../oidc/request-objects.md) |
| RFC 9126 | Pushed authorization requests | [Pushed authorization requests](../oidc/pushed-authorization-requests.md) |
| RFC 9207 | `iss` in the authorization response, always | [Authorization request](../oidc/authorization-request.md) |
| RFC 9396 | Rich authorization requests, `authorization_details` | [Authorization details](../oidc/authorization-details.md) |
| RFC 9449 | DPoP, a token bound to a key the client proves it holds | [DPoP](../oidc/sender-constrained/dpop.md) |
| RFC 9701 | A signed introspection response, `application/token-introspection+jwt` | [Introspection and revocation](../oidc/introspection-and-revocation.md) |
| RFC 9728 | `protected_resources`, the resources a client may name, read from the clients themselves | [Resources](../oidc/resources.md) |

RFC 8725 (JSON Web Token best current practices) and RFC 9700 (OAuth 2.0 security best current practice)
are not features; they are the rules the rest is written against. [Secure by
default](../the-project/secure-by-default.md) says which of their recommendations are properties of the
code here.

## OpenID Connect

| Specification | What it brings | Page |
|---|---|---|
| OpenID Connect Core 1.0 | ID tokens, UserInfo, claims, `prompt`, `acr`, `max_age` | [OAuth 2.0 and OpenID Connect](../oidc/index.md) |
| OpenID Connect Discovery 1.0 | `/.well-known/openid-configuration` | [Discovery and JWKS](../oidc/discovery-and-jwks.md) |
| OpenID Connect Dynamic Registration 1.0 | Registration, the OIDC reading of it | [Dynamic registration](../oidc/dynamic-registration.md) |
| RP-Initiated Logout 1.0 | A client asking for a session to end | [Logout](../oidc/logout.md) |
| Front-Channel Logout 1.0 | Telling the other clients through the browser | [Logout](../oidc/logout.md) |
| Back-Channel Logout 1.0 | Telling them server to server, with a logout token | [Logout](../oidc/logout.md) |
| JARM | A signed, and optionally encrypted, authorization response | [Response modes](../oidc/response-modes.md) |
| CIBA Core 1.0 | The decoupled flow, where the device that asks is not the one that answers | [Backchannel authentication](../oidc/grants/backchannel-authentication.md) |
| FAPI 2.0 Security Profile, FAPI 2.0 Message Signing | The profile open banking actually deploys | [Conformance](../the-project/conformance.md) |

## SAML 2.0

| Specification | What it brings | Page |
|---|---|---|
| SAML 2.0 Core | Assertions, the request and response protocol, `NameID` formats, status codes | [SAML 2.0](../saml/index.md) |
| SAML 2.0 Bindings §3.4, §3.5 | HTTP-Redirect, with its detached signature, and HTTP-POST | [Single sign-on](../saml/single-sign-on.md) |
| SAML 2.0 Profiles §4.1 | Web Browser SSO, both roles | [Single sign-on](../saml/single-sign-on.md), [signing in through an organisation](../saml/federated-sign-in.md) |
| SAML 2.0 Profiles §4.4 | Single Logout over the front channel | [Single logout](../saml/single-logout.md) |
| SAML 2.0 Metadata | The documents a peer is configured from, `cacheDuration`, the entity ID that resolves to them (§4.1) | [The identity provider](../saml/identity-provider.md), [service providers](../saml/service-providers.md) |
| SAML V2.0 Metadata Interoperability Profile | A certificate in metadata as the notation of a key, not a path to validate | [The identity provider](../saml/identity-provider.md) |
| SAML 2.0 Authentication Context | The classes an upstream assertion states, mapped to `amr` where they mean exactly a method | [Signing in through an organisation](../saml/federated-sign-in.md) |
| XML Signature Syntax and Processing, Exclusive XML Canonicalization 1.0 | Signing and verifying an element, enveloped | [The SAML packages](../saml/packages.md) |
| XML Encryption Syntax and Processing 1.1 | AES-GCM under RSA-OAEP, an assertion encrypted for a peer | [The SAML packages](../saml/packages.md) |
| RFC 5280 | The X.509 certificate around a SAML key | [The identity provider](../saml/identity-provider.md) |
| Unicode Technical Standard #46 | The IDNA a domain of an address goes through before it is compared | [Signing in through an organisation](../saml/federated-sign-in.md) |

## Credentials

| Specification | What it brings | Page |
|---|---|---|
| W3C Web Authentication Level 3 | Passkeys, enrolment and assertion | [Passkeys](../core/credentials/passkeys.md) |
| RFC 4226, RFC 6238 | HOTP and TOTP, the second factor from an application | [TOTP](../core/credentials/totp.md) |
| RFC 9106 | Argon2, one of the password algorithms a hash names | [Passwords](../core/credentials/passwords.md) |
| RFC 8176 | The authentication method references a session reports, `amr` | [Authentication sessions](../core/authentication-sessions.md) |
| OpenID Connect EAP ACR Values 1.0 | `phr` and `phrh`, the classes a passkey answers, and the predicates a tenant names the floor of its logins with | [Tenants](../core/tenants.md) |
| RFC 7517, RFC 7515, RFC 7516, RFC 7518, RFC 7519 | JOSE: keys, signatures, encryption, algorithms, claims | [Keys](../core/keys.md) |

NIST SP 800-63B §3.1.1.2 is what the rules of a password are written against: a floor on the length, fifteen
characters for a password that signs somebody in alone and eight for one a second factor goes with, an estimate
of how hard it is to guess, and a comparison against a list of compromised values rather than a composition
rule. [Passwords](../core/credentials/passwords.md) says what each of them refuses.

## Reaching a person

| Specification | What it brings | Page |
|---|---|---|
| RFC 8030 | Web push, the message a push service carries | [Web push](../symfony-bundle/web-push.md) |
| RFC 8291 | The encryption of that message, which only the browser can open | [Web push](../symfony-bundle/web-push.md) |
| RFC 8292 | VAPID, the application server key a tenant draws and signs with | [Web push](../symfony-bundle/web-push.md) |

## What is deliberately not implemented

| Specification | Why |
|---|---|
| The implicit flow and the hybrid response types that carry a token in a fragment | Tokens in a URL are read by history, logs and referrers. OIDC Core keeps them, Beffroi does not |
| The resource owner password credentials grant | It teaches applications to collect passwords |
| PKCE with `plain` | It protects nothing against an attacker who can read the request |
| OpenID Connect Session Management 1.0 | It rests on third party cookies in an iframe, which browsers no longer allow. Front-channel and back-channel logout do the job |
| RSA-SHA1 and DSA-SHA1, which SAML Bindings §3.4.4.1 requires | An algorithm a message names is an algorithm an attacker chooses, and SHA-1 has collisions. SHA-256 and up, in XML and over HTTP-Redirect |
| Encrypting an assertion in AES-CBC | CBC authenticates nothing. A service provider that asks for encryption gets AES-GCM, and CBC is only ever opened under a signature that covers it |
| The SAML Artifact and SOAP bindings, SAML 1.x, WS-Federation | A sign-on and a logout travel through the browser, over HTTP-Redirect and HTTP-POST |

## What is not implemented yet

SCIM (RFC 7643, RFC 7644) is planned, and has a page saying what is decided so far: [SCIM](../scim/index.md).
OpenID Federation, the shared signals family, verifiable credentials and the other drafts are tracked without
a date, and none of them is announced as coming.
