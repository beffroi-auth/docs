---
title: DPoP
description: The proof a client signs for every request, what the provider checks of it, the tokens bound to its key, the nonce, and what a resource server compares. RFC 9449.
---

# DPoP

The client holds a key pair and signs a proof with it for every request it makes, the provider binds the
tokens it issues to the thumbprint of the public key, and a resource that checks the binding refuses a token
so bound to whoever cannot sign a proof with that key. The key belongs to the client and nobody vouches for
it, so a public client, which holds no secret, binds its tokens as well as a confidential one.

DPoP is always on. A client that sends no proof is not concerned, and gets bearer tokens unless its
registration [requires bound ones](index.md#a-client-that-must-bind).

## The proof

A proof is a JWT in the `DPoP` header of the request (RFC 9449 §4.1), one per request: a request that carries
two `DPoP` headers is refused with `invalid_dpop_proof`, since which of them was read would decide which key
the tokens are bound to.

| Where | Member | What the provider requires |
|---|---|---|
| Header | `typ` | `dpop+jwt` (RFC 9449 §4.2) |
| Header | `alg` | One of `dpop_signing_alg_values_supported`: the signature algorithms the provider is wired with, `RS256`, `PS256`, `ES256` and `EdDSA` in the bundle. No MAC algorithm is among them |
| Header | `jwk` | The public key the proof is signed with. A key that carries a private member (`d`, `p`, `q`, `dp`, `dq`, `qi`, or the `k` of a symmetric key) is refused. `kid`, `jku` and `x5c` are not read, and nothing is looked up anywhere |
| Claims | `jti` | A non-empty string, accepted once for that key |
| Claims | `htm` | The method of the request, compared exactly: `POST` is not `post` |
| Claims | `htu` | The URL of the endpoint, as below |
| Claims | `iat` | An integer, inside the window below |
| Claims | `ath` | Present exactly when the request presents an access token: the base64url SHA-256 of that token (RFC 9449 §4.2, §7.1) |
| Claims | `nonce` | When present, a non-empty string. It is compared with the nonces the provider issued only when the provider asks for [one](#the-nonce) |

**The signature is verified against the key the proof carries**, and what comes out is that key, named by
its JWK SHA-256 thumbprint (RFC 7638 §3): the 43 characters of base64url a token bound to it names in
`cnf.jkt`.

**`htu` names the endpoint the provider publishes**, never what a header of the request says. The URL is the
one under the issuer that the discovery document announces in `token_endpoint`,
`pushed_authorization_request_endpoint` or `userinfo_endpoint`, including for a request that reached the
[host of the mutual TLS aliases](mutual-tls.md#the-endpoint-aliases). The two are compared as URLs and not as
bytes (RFC 9449 §4.3, RFC 3986 §6.2.2 and §6.2.3): the query and the fragment are dropped, the scheme and the
host compared without regard to case, and a port that is the default of its scheme is the same URL as no
port, so `HTTPS://OP.EXAMPLE.COM:443/token` names `https://op.example.com/token`. The path is compared as it
is, RFC 3986 making it case sensitive.

**A proof stands for the time a request spends on the wire.** It is refused when its `iat` is more than
`leeway` seconds ahead of the clock of the provider, and when the request arrives `proof_max_age` plus
`leeway` seconds or more after its `iat`: 30 seconds ahead and 90 seconds behind, by default.

**A proof is used once.** Its `jti` is remembered with the thumbprint of the key until the proof stops being
accepted, so that two clients choosing the same `jti` do not collide, and a proof presented again inside its
window is refused (RFC 9449 §11.1).

## Where a proof is read

Three endpoints read the `DPoP` header, and every other endpoint ignores it.

| Endpoint | `htm` | `ath` | What the proof does there |
|---|---|---|---|
| `/token` | `POST` | Absent | Binds the tokens of the response to its key, and proves the key a code or a refresh token was bound to |
| `/par` | `POST` | Absent | Reserves the authorization code of the pushed request for its key |
| `/userinfo` | The method of the request, `GET` or `POST` | Required | Proves the key the access token is bound to |

At the token endpoint the proof is verified once the client has authenticated, and before anything of the
grant is read.

## Tokens bound to the key

A token request that carries a valid proof is answered with tokens bound to its key, whatever the grant:

- the token response says `"token_type": "DPoP"` (RFC 9449 §5), and the client presents the access token as
  `Authorization: DPoP <token>` from then on, with a proof beside it;
- an `at+jwt` carries `"cnf": {"jkt": "<thumbprint>"}` (RFC 9449 §6.1), and an opaque token keeps the same
  member in its record;
- introspection describes the token with `"token_type": "DPoP"` and the same `cnf`;
- the refresh token of a public client is bound to the key too, refreshed only by a request that proves it
  again and not rotated; the refresh token of a confidential client is bound to nothing.

A request that proves a certificate its tokens would be bound to and carries a proof as well is refused with
`invalid_dpop_proof`: a token is [bound to one thing](index.md#the-two-bindings).

## A code reserved for a key

An authorization request may name the key that will come and exchange its code, in `dpop_jkt` (RFC 9449 §10):
a JWK SHA-256 thumbprint, 43 characters of base64url, or the request is refused with `invalid_request`, sent
back to the redirect URI at the authorization endpoint and answered as JSON at `/par`.

A request pushed to `/par` with a proof is reserved for the key of that proof (RFC 9449 §10.1): the provider
writes the thumbprint into the request as the `dpop_jkt` the client could have written itself. A pushed
request that names a `dpop_jkt` of another key than the proof that carried it is refused with
`invalid_request`, rather than arbitrated.

**A reserved code is exchanged only by a request that proves that key.** The token endpoint answers any other
exchange with `invalid_grant`, and the attempt spends the code all the same: a code intercepted on its way back
through the browser is worth nothing to whoever does not hold the key. A code reserved for no key is exchanged
by whichever request the rest of the grant accepts.

## The nonce

The provider may ask that every proof carry a value it handed out (RFC 9449 §8), which says when the proof
was made in terms the provider knows rather than in the `iat` its client wrote. It is off by default.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    dpop:
        nonce:
            required: true
```

**With `required: true`**, a proof that carries no `nonce`, or one the provider did not issue in the last
`ttl` seconds, is refused with `use_dpop_nonce` and a fresh nonce in the `DPoP-Nonce` header of the answer. The
client makes its proof again with that nonce and sends the request again. A nonce stands for its whole
lifetime and is not spent by the first proof that carries it, what makes a proof single-use being its `jti`;
the provider hands out a new one only with a refusal, so a client keeps the last nonce it was given until the
next refusal.

**With `required: false`**, the `nonce` claim of a proof is compared with nothing, and no answer carries
`DPoP-Nonce`.

## Configuration

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    dpop:
        proof_max_age: 60
        leeway: 30
        nonce:
            required: false
            ttl: 300
```

| Option | Default | What it decides |
|---|---|---|
| `proof_max_age` | `60` | Seconds a proof stands from its `iat`, before the leeway is added, one at least. Every second beyond what a request spends on the wire is a second a proof taken off that wire may be sent again in |
| `leeway` | `30` | Seconds allowed of the clock of a client, added on both sides of the window: a proof is taken up to `leeway` seconds ahead of the provider, and until `proof_max_age` plus `leeway` seconds after its `iat` |
| `nonce.required` | `false` | Whether every proof carries a nonce the provider issued |
| `nonce.ttl` | `300` | Seconds a nonce is accepted once issued, one at least |

What a proof may be signed with is not an option: it is the list of signature algorithms the provider is
wired with, which the discovery document announces in `dpop_signing_alg_values_supported`.

!!! warning "The proofs already seen and the nonces live in a cache pool"

    Both are kept in the pool `beffroi.dpop`, which the bundle declares on `cache.app`. A deployment that
    runs on several machines points that pool at a store they all reach: otherwise a proof replayed on
    another machine is not recognised as a replay there, and a nonce one machine issued is refused by the
    next. The pool tells a hit from a miss and not an insertion from a replacement, so two presentations of
    one proof arriving in the same instant may both be taken; what a replay needs is a wider window than
    that.

## What a resource server checks

**UserInfo**, the resource of the provider, honours a token bound to a key only when the request presents it
under the `DPoP` scheme with a valid proof of that key, and refuses it with a `401` whose challenge names the
scheme that would have worked. The proof is verified before the token is read, and the binding once the token
is known to be valid:

| The request | Status | `WWW-Authenticate` |
|---|---|---|
| Presents the bound token as `Bearer` | `401` | `DPoP error="invalid_token"` |
| Presents it as `DPoP` with no proof, or with a proof of another key | `401` | `DPoP error="invalid_token"` |
| Carries a proof that does not verify, or that names another request or another token | `401` | `DPoP error="invalid_dpop_proof"` |
| Carries no nonce, or a stale one, while the provider asks for one | `401` | `DPoP error="use_dpop_nonce"`, and the fresh nonce in `DPoP-Nonce` |

The body of each refusal carries the same `error` and its `error_description` as JSON.
[UserInfo](../userinfo.md) gives the rest of its refusals.

**A resource server of your own** reads the thumbprint the token is bound to in the `cnf.jkt` of the `at+jwt`,
or in the `cnf` of the introspection answer, verifies the proof as RFC 9449 §4.3 describes, its `ath` included,
and compares the thumbprint of the key of the proof with that member (RFC 9449 §7.1). A token introspected as
`"token_type": "DPoP"` is one to refuse when it arrives under the `Bearer` scheme.

The same refusals at the endpoints that issue tokens are answers of RFC 6749 §5.2 rather than challenges:
`invalid_dpop_proof` and `use_dpop_nonce` are a `400` with the JSON body, and the second one carries the
`DPoP-Nonce` header (RFC 9449 §8).

!!! note "A client running in a page"

    The standalone application lets a script of any origin send the `DPoP` header to `/token`, `/par` and
    `/userinfo`, and read `DPoP-Nonce` and `WWW-Authenticate` in their answers, without credentials. Behind
    the bundle alone, that CORS policy is the application's to write.
