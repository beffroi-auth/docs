---
title: ID tokens
description: What the provider says about an authentication, to one client, OIDC Core §2, the claims, the algorithms a client may register, and where an ID token is taken back.
---

# ID tokens

An ID token is a statement about an authentication, addressed to one client (OIDC Core §2): who the person is
to that client, when they proved it, how, and in which session. It is signed by the tenant, encrypted when
the client asked for it, and it leaves the provider at the token endpoint and nowhere else, the authorization
endpoint answering with a code alone. It is never a credential for an API.

## When one is issued

When `openid` is among the scopes of the answer and a person who signed in at this provider is behind it:

| Grant | ID token |
|---|---|
| [Authorization code](../grants/authorization-code.md) | With `openid`, carrying the `nonce` of the authorization request when it had one |
| [Refresh token](../grants/refresh-token.md) | With `openid` among the scopes of the refresh, describing the same authentication and carrying no `nonce` (OIDC Core §12.2) |
| [Device code](../grants/device-code.md) | With `openid` among the scopes the device asked for |
| [Backchannel authentication](../grants/backchannel-authentication.md) | Always, `openid` being required of the request |
| Client credentials, token exchange, JWT bearer | Never: nobody signed in at this provider |

## The claims

| Claim | What it holds |
|---|---|
| `iss` | The issuer of the tenant |
| `sub` | The subject this provider gives the person for this client, public or [pairwise](../pairwise-subjects.md) (OIDC Core §8) |
| `aud` | The `client_id`, as a string |
| `exp` | `tokens.id_token_ttl` seconds after `iat`, ten minutes by default |
| `iat` | When it was issued |
| `auth_time` | When the session last proved something, as it stood when the authorization was granted |
| `nonce` | The `nonce` of the authorization request, when it carried one |
| `acr` | Always. The first class the request asked for that the session satisfies, or, when it asked for none the session satisfies, the first class of the [policy of the tenant](../../core/tenants.md#the-classes-it-answers-with) the session satisfies |
| `amr` | The methods the session proved (RFC 8176 §2), and `mfa` beside them when two factors of different kinds were proven |
| `azp` | The `client_id` |
| `at_hash` | The left half of the digest of the access token of the same answer, under the hash of the signing algorithm, in base64url (OIDC Core §3.1.3.6) |
| `sid` | The session, in every ID token and for every client (Front-Channel Logout 1.0 §3, Back-Channel Logout 1.0 §2.1) |

What the session had proven is the one frozen when the authorization was granted: a step-up or a new login
afterwards moves the session, and never the `auth_time`, `acr` or `amr` of a token that descends from that
authorization, those of the ID tokens a refresh issues included.

Beside these, an ID token carries the claims the authorization request asked for by name in
`claims.id_token` (OIDC Core §5.5), when the person has a value for them and a wired claims provider serves
them; one of them never replaces a claim of the table. The claims the scopes stand for, those
of `profile` or `email`, are not in the ID token: the client reads them at the [UserInfo
endpoint](../userinfo.md).

The header carries `alg` and `kid`, and no `typ`: a resource server that requires `at+jwt` refuses an ID
token presented to it as an access token, which is the point.

## Signing

The client chooses the algorithm in `id_token_signed_response_alg` (OIDC Registration §2), among those the
provider is wired with: `RS256`, `PS256`, `ES256` and `EdDSA`. A client that registers none gets the first of
them, `RS256`, which OIDC Core §15.1 makes mandatory. A name nothing signs under, `none` among them, is
refused: a declared client is an error of the configuration, and a registration request is answered
`invalid_client_metadata`.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    tokens:
        id_token_ttl: 600
    clients:
        my-application:
            # ...
            id_token_signed_response_alg: ES256
```

The key is the active signing key of the tenant for that algorithm, published in the JWK Set under the `kid`
the header names ([keys](../../core/keys.md)). The logout tokens of a client are signed with the algorithm it
registered for its ID tokens, since that is the one it knows how to verify.

## Encryption

A client that registers `id_token_encrypted_response_alg` and `id_token_encrypted_response_enc` receives its ID
token signed, then encrypted to one of its keys (OIDC Core §3.1.3.7): a nested JWT, whose JWE header says
`cty` `JWT`. [Encryption](encryption.md) says which algorithms, which key, and what happens when the key cannot
be read.

## Where an ID token comes back

The provider takes an ID token it issued back as a hint. It reads one against the keys of the tenant, holds
its `iss` to the issuer, and leaves its `exp` aside, a hint describing a past sign-in being the ordinary
case:

| Where | What the hint says |
|---|---|
| `id_token_hint` of an authorization request | Who the client expects to be signed in; it must have been issued to that client (OIDC Core §3.1.2.1) |
| `id_token_hint` of a logout request | Which session the logout is about (RP-Initiated Logout 1.0 §2) |
| `id_token_hint` of a backchannel authentication request | Who the request is for; it must have been issued to that client (CIBA Core §7.1) |

At the authorization endpoint and at the backchannel authentication endpoint, a hint the tenant did not sign,
or of another issuer, is refused with `invalid_request`. At the end session endpoint, a signed hint the
provider cannot verify is read as no hint at all: the logout is not refused, and a browser that holds a
session is asked to confirm it ([logout](../logout.md)).

The hint is read as a signed ID token: a client whose ID tokens are encrypted sends back the signed token it
decrypted, and not one it encrypted again for the provider.
