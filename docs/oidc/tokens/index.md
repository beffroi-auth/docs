---
title: Tokens
description: The three tokens the provider issues, the shape of each, how long each one lives and the variables that change it.
---

# Tokens

Three kinds of token leave this provider, all of them at the token endpoint, and a client never has to guess
which one it is holding:

| Token | Who it is for | Its shape | How long it lives | Page |
|---|---|---|---|---|
| Access token | A resource server | A JWT of type `at+jwt` for every client of the image; an opaque reference is the other shape the provider writes | `BEFFROI_ACCESS_TOKEN_TTL`, 600 seconds | [Access tokens](access-tokens.md) |
| ID token | The client, about the person who signed in | A JWT signed by the tenant, encrypted when the client asked for it | `BEFFROI_ID_TOKEN_TTL`, 600 seconds | [ID tokens](id-tokens.md) |
| Refresh token | The token endpoint, to ask again | An opaque reference | `BEFFROI_REFRESH_TOKEN_TTL`, 30 days, within `BEFFROI_REFRESH_TOKEN_ABSOLUTE_TTL`, 90 days | [Refresh tokens](refresh-tokens.md) |

The authorization endpoint answers with a code and never with a token, and [the grants](../grants/index.md)
say which of the three each way of asking issues. [Encryption](encryption.md) says what the provider encrypts,
and for whom.

**A reference is worth nothing outside the provider, and nothing inside a copy of its database.** An opaque
access token, a refresh token, an authorization code, a device code and an `auth_req_id` are each 256 random
bits in base64url, 43 characters, and the provider keeps the SHA-256 of each, never the value. The user code
a device shows is the one value made to be typed by a person, eight characters out of twenty consonants,
and it is kept as its SHA-256 too ([device code](../grants/device-code.md)).

## Lifetimes

Every lifetime is a variable of the environment, a number of seconds, one at least; some have a ceiling, and
a value past it is refused by the first request or command that needs it
([configuration](../../application/configuration.md#keys-and-lifetimes)).

| Variable | In the image | At most | What it is |
|---|---|---|---|
| `BEFFROI_AUTHORIZATION_CODE_TTL` | `60` | `600` | An [authorization code](../grants/authorization-code.md), RFC 6749 §4.1.2 recommending ten minutes at most |
| `BEFFROI_ACCESS_TOKEN_TTL` | `600` | | Both shapes of access token |
| `BEFFROI_ID_TOKEN_TTL` | `600` | | An ID token |
| `BEFFROI_REFRESH_TOKEN_TTL` | `2592000` | `BEFFROI_REFRESH_TOKEN_ABSOLUTE_TTL` | One refresh token, from the moment it was issued |
| `BEFFROI_REFRESH_TOKEN_ABSOLUTE_TTL` | `7776000` | | A family of refresh tokens, from the authorization that started it |
| `BEFFROI_REQUEST_URI_TTL` | `60` | `600` | The reference a [pushed authorization request](../pushed-authorization-requests.md) is answered with (RFC 9126 §2.2) |
| `BEFFROI_DEVICE_CODE_TTL` | `600` | `1800` | A [device code](../grants/device-code.md) and the user code beside it |
| `BEFFROI_DEVICE_CODE_INTERVAL` | `5` | `30` | How long a device waits between two polls |
| `BEFFROI_BACKCHANNEL_AUTHENTICATION_TTL` | `300` | `3600` | A [backchannel request](../grants/backchannel-authentication.md) that asked for no `requested_expiry` |
| `BEFFROI_BACKCHANNEL_AUTHENTICATION_MAX_REQUESTED_EXPIRY` | `1800` | `3600` | The longest a backchannel request lives, whatever it asks for |
| `BEFFROI_BACKCHANNEL_AUTHENTICATION_INTERVAL` | `5` | `30` | How long a client waits between two polls of a backchannel request |

A deployment names the lifetimes it wants in its environment, here at the values of the image, and a change
asks for a restart of the processes:

``` dotenv
BEFFROI_AUTHORIZATION_CODE_TTL=60
BEFFROI_ACCESS_TOKEN_TTL=600
BEFFROI_ID_TOKEN_TTL=600
BEFFROI_REFRESH_TOKEN_TTL=2592000
BEFFROI_REFRESH_TOKEN_ABSOLUTE_TTL=7776000
```

**A lifetime is also how long a retired signing key is kept.** The rotation of a signing key dates its
retirement from the longest lifetime among what the tenant signs with it, the ID token and the self-contained
access token among them, so that a token signed just before a rotation verifies until it expires. Lengthening
one of these lifetimes delays every retirement by as much. [Keys](../../core/keys.md) describes the rotation.
