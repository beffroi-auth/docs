---
title: Refresh tokens
description: What the provider keeps of a refresh token, how long one lives, what binds it, when it is replaced, and everything that ends it.
---

# Refresh tokens

A refresh token is the longest-lived thing the provider issues and the one that works while the person is
away, so it is the one held by the most rules. It is a reference, 256 random bits in base64url, 43
characters, that means something to this provider alone, and the client spends it at the token endpoint with
the [refresh token grant](../grants/refresh-token.md).

## When one is issued

The [authorization code](../grants/authorization-code.md), [device code](../grants/device-code.md) and
[backchannel authentication](../grants/backchannel-authentication.md) grants issue one when the client is
registered for `refresh_token`, and either `offline_access` is among the scopes of the authorization (OIDC
Core §11) or the client is confidential. A confidential client therefore gets one without asking for
`offline_access`, a public client gets one only by asking for it, and a client registered for no
`refresh_token` gets none. The client credentials, token exchange and JWT bearer grants never issue one.

## What is kept

The SHA-256 of the value, never the value, and beside it:

| | |
|---|---|
| Its family | The lineage of tokens descending from one authorization code, device code or backchannel request, which a reuse revokes at once and which carries the absolute lifetime |
| The client and the session | Of the same tenant, which is checked when the token is written |
| The authorization | Its scopes, resources, authorization details and `claims` request, whole, whatever an access token beside the refresh token was narrowed to |
| What the session had proven | The `auth_time`, `acr` and `amr` of the authorization, carried unchanged from one token of the family to the next (OIDC Core §12.2) |
| Its binding | For a public client only: the key or the certificate the request that obtained it was bound to |
| Its dates | When it was issued, when it expires, and when it was replaced or revoked, if it was |

## How long it lives

| Option | Default | What it bounds |
|---|---|---|
| `tokens.refresh_token_ttl` | `2592000` seconds, 30 days | One token, from the moment it was issued |
| `tokens.refresh_token_absolute_ttl` | `7776000` seconds, 90 days | Its family, from the authorization that started it. No rotation extends it, and no token of the family outlives it |

The first cannot exceed the second, and a configuration where it does fails to load.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    tokens:
        refresh_token_ttl: 2592000
        refresh_token_absolute_ttl: 7776000
```

**A token that is not replaced keeps the expiry it was issued with.** The refresh token of a confidential
client, and of a public client whose token is bound, is never replaced, so it stops working
`refresh_token_ttl` after it was issued, and the client then obtains a new authorization the way it obtained
the first. Only a token that rotates starts a new `refresh_token_ttl` at each rotation, until the family
ends.

## Rotation and reuse

A refresh token is told from a copy of itself by the authentication of a confidential client, by the key or
the certificate it is bound to, or by rotation (RFC 9700 §4.13.2), and one of the three is enough. So the
provider replaces a token at each use exactly where the first two are missing, the token of a public client
bound to nothing, and lets every other token stand: replacing it would add nothing, and would lock out a
client that lost the answer to a refresh.

A replaced token presented again is a reuse. The provider cannot tell the client from whoever copied the
token, so it revokes the whole family, the successor the client holds included, refuses the request with
`invalid_grant`, and writes the act `refresh_token.reuse_detected` in the journal of the person. The client
goes back to the person for a new authorization.

## Binding

A refresh token issued to a public client keeps what the request that obtained it was bound to, the key of
its DPoP proof or, for a client registered with `tls_client_certificate_bound_access_tokens`, the certificate
of its connection, and is refreshed only by a request that proves the same again (RFC 9449 §5, RFC 8705 §4):
such a client has no credentials, and the binding is what tells it from whoever took a copy. A refresh token
issued to a confidential client keeps no binding, the client authenticating at every refresh; the access
tokens of each refresh are bound to whatever that request binds them to
([grants](../grants/index.md#what-the-token-endpoint-does)).

## What ends one

| What happens | What it takes |
|---|---|
| The token expires, or its family does | That token |
| A token of its family is reused | The whole family |
| The authorization code it descends from is presented a second time (RFC 6749 §4.1.2) | Every refresh token descending from that code |
| Its session ends, at the end session endpoint, by a SAML logout, on the [account pages](../../symfony-bundle/account.md), with the console, or by a sign-in that replaced it | Every refresh token of that session |
| The person takes back their consent to that client, on the account pages or with `beffroi:user:revoke-consent` | Every refresh token that client holds for that person |
| The client revokes it at the revocation endpoint (RFC 7009 §2.1) | That token, and the opaque access tokens of its grant |

**The grant reads the session, and not only the token.** It refuses a token whose session has ended from the
instant the session ended, whatever the token's own state, while the revocation of the tokens of that session
is written on the lane of the events and dated by the end. A token that a refresh in flight saved after that
revocation ran is refused all the same, and revoked at its first use. A session that merely expired, without
anybody ending it, stops no refresh.

A token revoked keeps the date of its first revocation. [Introspection and
revocation](../introspection-and-revocation.md) describes the revocation endpoint, which answers the same
way whether the token existed or not.
