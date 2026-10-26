---
title: Refresh token
description: Renewing an access token while the person is away, RFC 6749 §6, what offline_access changes, what is checked, and when a refresh token is replaced.
---

# Refresh token

A refresh token renews an access token while the person is elsewhere (RFC 6749 §6). The client spends it at
the token endpoint with `grant_type=refresh_token`, and it is the only client that can: a refresh token is
issued to one client and refused to every other. What a refresh token is, how long it lives and everything
that ends one are on [refresh tokens](../tokens/refresh-tokens.md); this page is the request.

## When a client gets one

Three grants issue refresh tokens: [authorization code](authorization-code.md), [device
code](device-code.md) and [backchannel authentication](backchannel-authentication.md). Their answer carries
one when the client is registered for `refresh_token`, and either:

- `offline_access` is among the scopes of the authorization (OIDC Core §11), or
- the client is confidential, whether it asked for `offline_access` or not.

So a public client gets one only by asking for `offline_access`, and a client registered for no
`refresh_token` gets none, whatever it asks for. The provider offers `offline_access` only while it is wired
with a grant that issues refresh tokens and a grant that spends them, and a client asks for it as for any
other scope, among the ones it registered.

## The request

| Parameter | |
|---|---|
| `grant_type` | `refresh_token` |
| `refresh_token` | Required |
| `scope` | Optional: a subset of the scopes of the refresh token, for this answer only (RFC 6749 §6) |
| `resource` | Optional and repeatable: a subset of the resources of the authorization, for this access token only (RFC 8707 §2.2) |
| `authorization_details` | Optional: a subset of the details of the authorization, for this access token only (RFC 9396 §7) |

The client authenticates beside them with the method it registered.

## What is checked

In this order. The first five refusals are `invalid_grant`, all with the one description `The refresh token
is invalid.`:

1. The token is one this provider issued, to the client that authenticated, and it has not been revoked.
2. It has not been replaced. A token that was rotated and is presented again is a reuse
   (RFC 9700 §4.13.2): its whole family is revoked, the successor the client holds included, and the act
   `refresh_token.reuse_detected` is written in the journal of the person.
3. The session it descends from has not ended. A session that merely expired does not stop a refresh,
   renewing while the person is away being what the token is for; a session that ended does, however it
   ended, and the act `refresh_token.outlived_its_session` is written.
4. It has not expired. Its own lifetime never reaches past the absolute lifetime of its family.
5. A token bound to a key or to a certificate is refreshed by a request that proves that key or presents that
   certificate again (RFC 9449 §5, RFC 8705 §4).
6. `scope` names nothing the token does not carry: `invalid_scope` otherwise. A `scope` that is not a list of
   scope tokens is `invalid_scope` too, before the token is even looked up.
7. `resource` and `authorization_details` narrow and never widen: `invalid_target` and
   `invalid_authorization_details` otherwise.

## Rotation

**A refresh token is replaced where nothing else tells it from a copy of itself** (RFC 9700 §4.13.2). Three
things can: the authentication of a confidential client, the key or the certificate the token is bound to,
and rotation. One is enough, so the provider rotates exactly where the other two are missing:

| The client | Its refresh token |
|---|---|
| Confidential | Stands. The answer carries no `refresh_token`, and the client keeps the one it holds until it expires |
| Public, the token bound to a DPoP key or to a certificate | Stands, for the same reason |
| Public, the token bound to nothing | Rotates. The token presented is marked replaced, and the answer carries its successor |

A successor belongs to the same family. It carries the whole authorization, whatever this request narrowed
for its access token, and what the session had proven when the authorization was granted. Its own lifetime,
`tokens.refresh_token_ttl`, starts at the rotation and never reaches past the end of the family. The act
`refresh_token.rotated` is written in the journal of the person.

## What the answer carries

- **An access token**, bound to what this request binds it to and not to what bound the request that
  obtained the refresh token ([grants](index.md#what-the-token-endpoint-does)): a confidential client whose
  tokens are bound to its certificate, and whose certificate was renewed, gets tokens bound to the new one.
- **An ID token** when `openid` is among the scopes of the answer. It describes the same authentication as
  the first one, the same `auth_time`, `acr` and `amr`, and it carries no `nonce`, the refresh having none to
  carry (OIDC Core §12.2).
- **A refresh token** when the token rotated, and only then.

A client takes a refresh token back itself at the revocation endpoint (RFC 7009 §2.1), which revokes that
token and removes the opaque access tokens of its grant. [Introspection and
revocation](../introspection-and-revocation.md) describes the endpoint.
