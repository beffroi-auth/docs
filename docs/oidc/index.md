---
title: OAuth 2.0 and OpenID Connect
description: 'What beffroi/oidc implements: clients, authorization requests, grants, tokens, discovery, logout.'
---

# OAuth 2.0 and OpenID Connect

`beffroi/oidc` is the protocol, in pure PHP, on top of [the identity core](../core/index.md). It knows no
HTTP: it reads values, applies the rules of the specifications, and returns what the answer must contain.
Turning that into a request and a response is the job of [the bundle](../symfony-bundle/index.md).

## The shape of a sign-in

``` mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant C as Client
    participant P as Beffroi
    C->>P: Authorization request (PAR, or in the URL)
    P->>B: Login page, then consent
    B->>P: Credentials, then the answer
    P->>C: Redirect with the code, and iss
    C->>P: Token request, with the PKCE verifier
    P->>C: Access token, ID token, refresh token
    C->>P: UserInfo, with the access token
```

Every step of that exchange has a page below, and each page cites the section of the specification it
describes.

## What is served

<div class="grid cards" markdown>

-   **[Clients](clients.md)**

    ---

    What a client is, where it came from, what it registered, and [how it authenticates](client-authentication.md).

-   **[Authorization requests](authorization-request.md)**

    ---

    What is read, what is refused, PKCE, and the `iss` that goes back in every response.

-   **[Grants](grants/index.md)**

    ---

    Authorization code, refresh token, client credentials, device code, CIBA, token exchange, JWT bearer.

-   **[Tokens](tokens/index.md)**

    ---

    Access tokens as `at+jwt` or as references, ID tokens, refresh tokens, and what is encrypted.

-   **[Discovery and JWKS](discovery-and-jwks.md)**

    ---

    The document the provider publishes, derived from what is wired rather than from a list kept beside it.

-   **[Logout](logout.md)**

    ---

    RP-initiated, front-channel and back-channel, and what each one can promise.

</div>

## Hardening a client can ask for

The provider does not need a different deployment to serve a demanding client. The same endpoints accept
[pushed authorization requests](pushed-authorization-requests.md),
[signed request objects](request-objects.md), [signed and encrypted
responses](response-modes.md), and tokens bound to a key with [DPoP](sender-constrained/dpop.md) or to a
certificate with [mutual TLS](sender-constrained/mutual-tls.md). A client that asks for none of it keeps
working, and the FAPI 2.0 profiles are what prove the strict end of that range.

## One source of truth

What the provider announces is derived from what it is wired with. The discovery document reads the grants
that are tagged, the client authentication methods that are registered and the algorithms that are
available, so there is no list to keep in agreement with the code. Enabling a grant announces it; removing
it stops announcing it. [Discovery and JWKS](discovery-and-jwks.md) says what that produces.
