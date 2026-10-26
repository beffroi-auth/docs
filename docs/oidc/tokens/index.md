---
title: Tokens
description: The three tokens the provider issues, the shape of each, how long each one lives and the options that change it.
---

# Tokens

Three kinds of token leave this provider, all of them at the token endpoint, and a client never has to guess
which one it is holding:

| Token | Who it is for | Its shape | How long it lives | Page |
|---|---|---|---|---|
| Access token | A resource server | A JWT of type `at+jwt` or an opaque reference, as the client registered | `tokens.access_token_ttl`, 600 seconds | [Access tokens](access-tokens.md) |
| ID token | The client, about the person who signed in | A JWT signed by the tenant, encrypted when the client asked for it | `tokens.id_token_ttl`, 600 seconds | [ID tokens](id-tokens.md) |
| Refresh token | The token endpoint, to ask again | An opaque reference | `tokens.refresh_token_ttl`, 30 days, within `tokens.refresh_token_absolute_ttl`, 90 days | [Refresh tokens](refresh-tokens.md) |

The authorization endpoint answers with a code and never with a token, and [the grants](../grants/index.md)
say which of the three each way of asking issues. [Encryption](encryption.md) says what the provider encrypts,
and for whom.

**A reference is worth nothing outside the provider, and nothing inside a copy of its database.** An opaque
access token, a refresh token, an authorization code, a device code and an `auth_req_id` are each 256 random
bits in base64url, 43 characters, and the provider keeps the SHA-256 of each, never the value. The user code
a device shows is the one value made to be typed by a person, eight characters out of twenty consonants,
and it is kept as its SHA-256 too ([device code](../grants/device-code.md)).

## Lifetimes

Every lifetime is a number of seconds, at least one, set under `tokens`; some have a ceiling, which a
configuration past it fails to load with.

| Option | Default | At most | What it is |
|---|---|---|---|
| `authorization_code_ttl` | `60` | `600` | An [authorization code](../grants/authorization-code.md), RFC 6749 §4.1.2 recommending ten minutes at most |
| `access_token_ttl` | `600` | | Both shapes of access token |
| `id_token_ttl` | `600` | | An ID token |
| `refresh_token_ttl` | `2592000` | `refresh_token_absolute_ttl` | One refresh token, from the moment it was issued |
| `refresh_token_absolute_ttl` | `7776000` | | A family of refresh tokens, from the authorization that started it |
| `request_uri_ttl` | `60` | `600` | The reference a [pushed authorization request](../pushed-authorization-requests.md) is answered with (RFC 9126 §2.2) |
| `device_code_ttl` | `600` | `1800` | A [device code](../grants/device-code.md) and the user code beside it |
| `device_code_interval` | `5` | `30` | How long a device waits between two polls |
| `backchannel_authentication_ttl` | `300` | `3600` | A [backchannel request](../grants/backchannel-authentication.md) that asked for no `requested_expiry` |
| `backchannel_authentication_max_requested_expiry` | `1800` | `3600` | The longest a backchannel request lives, whatever it asks for |
| `backchannel_authentication_interval` | `5` | `30` | How long a client waits between two polls of a backchannel request |

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    tokens:
        authorization_code_ttl: 60
        access_token_ttl: 600
        id_token_ttl: 600
        refresh_token_ttl: 2592000
        refresh_token_absolute_ttl: 7776000
```

[The standalone application](../../application/index.md) reads `access_token_ttl` and `id_token_ttl` from the
environment variables `BEFFROI_ACCESS_TOKEN_TTL` and `BEFFROI_ID_TOKEN_TTL`, both `600` in its `.env`.

**A lifetime is also how long a retired signing key is kept.** The rotation of a signing key dates its
retirement from the longest lifetime among what the tenant signs with it, the ID token and the self-contained
access token among them, so that a token signed just before a rotation verifies until it expires. Lengthening
one of these lifetimes delays every retirement by as much. [Keys](../../core/keys.md) describes the rotation.
