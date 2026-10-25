---
title: JWT bearer
status: draft
description: An assertion from an issuer the tenant trusts, RFC 7523.
---

# JWT bearer

A client presents a JWT signed by an issuer the tenant has pinned, and gets a token in exchange. What the
tenant trusts is declared explicitly: an issuer, its keys, and what it is allowed to assert.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    trusted_issuers:
        'https://issuer.example.com':
            jwks_uri: 'https://issuer.example.com/jwks.json'
            signing_algorithms: ['ES256']
            clients: ['gateway']
            identity_provider: example-issuer
            trusted_scopes: ['invoices.read']
```

| Option | What it decides |
|---|---|
| The key | The `iss` the issuer signs with. An issuer nobody declared is unknown |
| `jwks` or `jwks_uri` | Its keys, inline or read back from a URL, one or the other and never both. A URL is read with one `GET` over HTTPS, no redirect followed, kept in a pool the workers share, and read again at most once per cooldown when an assertion names a `kid` the kept set does not hold, which is how an issuer that rotates its keys is followed. The keys are the only ones an assertion is verified against, whatever its header names (RFC 8725 §3.10) |
| `signing_algorithms` | The algorithms an assertion may be signed with, among those the provider is wired with |
| `clients` | The clients that may present its assertions. An issuer trusted for a gateway is not trusted for every client |
| `identity_provider` | The source of the linked identities its subjects name: a `sub` is a person of the tenant only when a linked identity of that source says so, and nobody is ever created from an assertion |
| `trusted_scopes` | What it is trusted for. `openid` buys nothing here, the grant authenticating nobody |

A link between a person and a subject of the issuer is written by an operator, with `beffroi:user:link` and
the name given in `identity_provider`.

This page will describe what is checked of an assertion, and what it may obtain.
