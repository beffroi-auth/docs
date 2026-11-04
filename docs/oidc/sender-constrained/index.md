---
title: Sender-constrained tokens
description: Tokens bound to a key or a certificate the client proves again every time it presents them, how the binding is written, and which clients must bind.
---

# Sender-constrained tokens

A bearer token opens what it opens for whoever presents it. A sender-constrained token is bound to something
its client proves again every time it presents the token: a key it signs a proof with, [DPoP](dpop.md)
(RFC 9449), or the certificate of its TLS connection, [mutual TLS](mutual-tls.md) (RFC 8705). Whoever takes
the token without what it is bound to holds a token that UserInfo refuses, and so does every resource server
that checks the binding.

## The two bindings

| | DPoP | Mutual TLS |
|---|---|---|
| What the client proves | A key, with a proof it signs for each request and sends in the `DPoP` header | The certificate it presented at the TLS handshake |
| Which clients are bound | Every client whose token request carries a proof | A client that authenticates with its certificate, and a client that registered `tls_client_certificate_bound_access_tokens` |
| What the token names in `cnf` (RFC 7800 §3.1) | `jkt`, the JWK SHA-256 thumbprint of the public key (RFC 7638 §3) | `x5t#S256`, the SHA-256 thumbprint of the DER encoding of the certificate (RFC 8705 §3.1) |
| `token_type` of the token response and of introspection | `DPoP` | `Bearer` |
| How the token is presented | `Authorization: DPoP <token>`, with a new proof that names the token in `ath` | `Authorization: Bearer <token>`, on a connection that presents the same certificate |

**The binding is made at the token endpoint, by every grant.** The access token of an authorization code, a
refresh token, client credentials, a device code, a backchannel authentication, a token exchange and a JWT
bearer grant is bound to what the token request proved. An ID token carries no binding.

**Both shapes of access token carry it.** An `at+jwt` carries `cnf` among its claims, and an opaque token keeps
the same member in its record, which [introspection](../introspection-and-revocation.md) returns. A resource
server that verifies an `at+jwt` offline reads the binding in the token; one that introspects reads it in the
answer.

**A token is bound to one thing.** A token request that proves a certificate the tokens would be bound to, and
a DPoP key as well, is refused with `invalid_dpop_proof`, status `400`, rather than arbitrated: a token names
one thing in its `cnf`, and the provider does not choose for the client. A certificate presented only because
the listener asked for one binds
nothing (see [mutual TLS](mutual-tls.md#tokens-bound-to-the-certificate)), so a client that authenticates
another way may send a DPoP proof over that connection.

## Refresh tokens

The refresh token of a **public client** is bound to what the token request proved, key or certificate, and
it is refreshed only by a request that proves the same thing again: any other request is answered
`invalid_grant`. Such a token is not rotated when it is used, the binding being what tells it from a copy. A
public client that binds nothing has its refresh token rotated at every use instead.

The refresh token of a **confidential client** is bound to nothing, since the client authenticates every time
it refreshes. The access token a refresh issues is bound to what that refresh request proves, which may be a
key the earlier tokens were not bound to.

[:beffroi-arrow-right: Refresh tokens](../tokens/refresh-tokens.md)

## A client that must bind

Two members of a registration refuse a token request rather than answer it with bearer tokens. Both are read
at the token endpoint, after the client has authenticated and before the grant is read, and both refuse with
`invalid_request`, status `400`.

| Member | What a token request of that client must prove | Who sets it |
|---|---|---|
| `require_sender_constrained_tokens` | A certificate its tokens are bound to, or a DPoP key, whichever (FAPI 2.0 Security Profile §5.3.2.1) | Nobody on a deployment of the image. It is a member of the deployment: a client that registers itself and sends it is refused with `invalid_client_metadata`, and no client of the image holds it ([what the image does not set](../clients.md#what-the-image-does-not-set)) |
| `tls_client_certificate_bound_access_tokens` | The certificate of its connection, whatever way it authenticates (RFC 8705 §3.4) | The client, when it registers, RFC 8705 §3.4 making it a member of a registration |

A client of the image that must bind therefore registers the second ([dynamic
registration](../dynamic-registration.md)):

``` json
{
    "client_name": "Payments",
    "redirect_uris": ["https://payments.example.com/oidc/callback"],
    "token_endpoint_auth_method": "private_key_jwt",
    "jwks_uri": "https://payments.example.com/.well-known/jwks.json",
    "tls_client_certificate_bound_access_tokens": true
}
```

Its token requests go to the token endpoint of the host that asks for a certificate, the ordinary host asking
for none ([mutual TLS](mutual-tls.md#the-endpoint-aliases)). The image serves that host once a deployment
turns it on, with `CADDY_EXTRA_CONFIG` and `MTLS_SERVER_NAME`: until then no host asks for a certificate, and
every token request of such a client is refused with `invalid_request`.
`tls_client_certificate_bound_access_tokens` defaults to `false`, and no variable binds the tokens of every
client. Nothing holds a client to DPoP either: the provider reads no `dpop_bound_access_tokens` (RFC 9449
§5.2), and a registration that carries it is refused with `invalid_client_metadata`, as one carrying any
member the provider does not read is. A client binds its tokens to a key by sending a proof with its token
requests.

## Where the binding is checked

At a resource of the provider, which is [UserInfo](../userinfo.md): a bound token is honoured only when the
request proves again what it is bound to, and refused with `invalid_token`, status `401`, otherwise. A
resource server of your own makes the same check against the `cnf` it reads, as RFC 9449 §7.1 and
RFC 8705 §3.2 describe; [DPoP](dpop.md#what-a-resource-server-checks) and [mutual
TLS](mutual-tls.md#tokens-bound-to-the-certificate) say what each one compares.

**What the provider announces.** The discovery document always carries `dpop_signing_alg_values_supported`,
the signature algorithms the provider is wired with. It carries `tls_client_certificate_bound_access_tokens`
set to `true` because a client authentication method that proves a certificate is wired, which the
application does. The bare challenge of UserInfo, answered to a request that carries no token at all, is what
is read from the bindings themselves, both wired in the application: `WWW-Authenticate: Bearer, DPoP`.
