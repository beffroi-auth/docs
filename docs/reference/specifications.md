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

## Credentials

| Specification | What it brings | Page |
|---|---|---|
| W3C Web Authentication Level 3 | Passkeys, enrolment and assertion | [Passkeys](../core/credentials/passkeys.md) |
| RFC 4226, RFC 6238 | HOTP and TOTP, the second factor from an application | [TOTP](../core/credentials/totp.md) |
| RFC 9106 | Argon2, one of the password algorithms a hash names | [Passwords](../core/credentials/passwords.md) |
| RFC 8176 | The authentication method references a session reports, `amr` | [Authentication sessions](../core/authentication-sessions.md) |
| RFC 7517, RFC 7515, RFC 7516, RFC 7518, RFC 7519 | JOSE: keys, signatures, encryption, algorithms, claims | [Keys](../core/keys.md) |

NIST SP 800-63B §5.1.1.2 is what the rules of a password are written against: a floor on the length, an
estimate of how hard it is to guess, and a comparison against a list of compromised values rather than a
composition rule. [Passwords](../core/credentials/passwords.md) says what each of them refuses.

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

## What is not implemented yet

SCIM (RFC 7643, RFC 7644) and SAML 2.0 with XML Signature and XML Encryption are planned, and each has a
page saying what is decided so far: [SCIM](../scim/index.md), [SAML 2.0](../saml/index.md). OpenID
Federation, the shared signals family, verifiable credentials and the other drafts are tracked without a
date, and none of them is announced as coming.
