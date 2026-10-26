---
title: Authorization code
description: Spending the code a browser brought back, RFC 6749 §4.1.3 and OIDC Core §3.1.3, every check the exchange runs, and what a code presented twice takes with it.
---

# Authorization code

The authorization code grant ends every flow that goes through a browser. The [authorization
request](../authorization-request.md) brings the person to the provider, the provider signs them in and asks
for their [consent](../consent.md) where one is needed, and the browser carries a code back to a redirect URI
of the client. The client then spends that code at the token endpoint (RFC 6749 §4.1.3), with the PKCE
verifier that only it holds.

## The code

| | |
|---|---|
| Lifetime | 60 seconds, `tokens.authorization_code_ttl`, at most 600 (RFC 6749 §4.1.2) |
| Value | 256 random bits in base64url, 43 characters |
| What the provider keeps | Its SHA-256, never the value |
| Bound to | The client, the redirect URI of the request, the PKCE challenge, the DPoP key the request reserved it for when it reserved it for one (RFC 9449 §10), and the session it was issued in |
| What it carries | The scopes, the resources, the authorization details, the `nonce` and the `claims` of the request, and what the session had proven at that instant: `auth_time`, `acr` and `amr` |

What the session had proven is frozen on the code: a step-up or a new login afterwards changes the session,
and never a code already issued nor a token that descends from one.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    tokens:
        authorization_code_ttl: 60
```

## The request

| Parameter | |
|---|---|
| `grant_type` | `authorization_code` |
| `code` | Required |
| `redirect_uri` | Required: the one the authorization request carried, as it carried it |
| `code_verifier` | Required when the authorization request carried a `code_challenge` (RFC 7636 §4.5), refused when it carried none |
| `resource` | Optional and repeatable: narrows what the access token is addressed to, among the resources of the authorization (RFC 8707 §2.2) |
| `authorization_details` | Optional: narrows the details the access token carries, among those of the authorization (RFC 9396 §7) |

The client authenticates beside them with the method it registered, which for a public client is its
`client_id` and nothing else ([client authentication](../client-authentication.md)).

## What is checked

**A code is spent by its first presentation, whatever comes of it.** It is looked up by its digest and
consumed atomically before anything else is compared: of any number of requests presenting the same code at
once, exactly one is the first, and a presentation that fails a check below has spent the code all the same.
Every refusal of this list is `invalid_grant` with the one description `The authorization code is invalid.`,
so that a client guessing learns nothing of which check it failed.

1. The code is one this provider issued, and it was not presented before.
2. It was issued to the client that authenticated.
3. It has not expired.
4. `redirect_uri` is the redirect URI of the authorization request, compared as a string (RFC 6749 §4.1.3).
5. PKCE holds (RFC 7636 §4.6): the `code_verifier`, transformed with `S256`, is the `code_challenge` of the
   request. A code issued without a challenge, which only a confidential client registered with
   `requires_pkce: false` obtains, is refused when a `code_verifier` comes with it (RFC 9700 §4.8.2).
6. A code the request reserved for a key, with `dpop_jkt` or by the DPoP proof of its pushed request, is spent
   by a request whose DPoP proof is signed by that key (RFC 9449 §10), and by no other.
7. The session the code was issued in is still active: it has not ended, and it has not expired.

A missing `code` or `redirect_uri` is `invalid_request`, answered before the code is read, which leaves it
unspent. A `code_verifier` that is not 43 to 128 unreserved characters (RFC 7636 §4.1) is refused. Other
refusals come after every check has passed, and the code is spent: a `resource` the authorization does not
carry is `invalid_target`, and an `authorization_details` it does not carry is
`invalid_authorization_details`.

## What the answer carries

- **An access token**, in the shape the client registered ([access tokens](../tokens/access-tokens.md)). It is
  addressed to the resources the token request named, or to all those of the authorization when it named
  none, or to the client itself when the authorization carries none. It is bound to what this request binds
  it to, the key of its DPoP proof or the certificate of its connection, as
  [grants](index.md#what-the-token-endpoint-does) says, and is a bearer token otherwise.
- **An ID token** when `openid` is among the scopes, carrying the `nonce` of the authorization request
  ([ID tokens](../tokens/id-tokens.md)).
- **A refresh token** when one is due: the client is registered for `refresh_token`, and either
  `offline_access` was granted or the client is confidential. It starts a family whose absolute lifetime is
  `tokens.refresh_token_absolute_ttl`, ninety days by default, and it carries the whole authorization,
  whatever subset of its resources and details the access token beside it was narrowed to ([refresh
  tokens](../tokens/refresh-tokens.md)).

The act `tokens.issued` is written in the journal of the person, with what the client was given.

## A code presented twice

A code presented a second time is refused with `invalid_grant`, and the authorization it stood for is taken
back (RFC 6749 §4.1.2): one of the two presentations may have been an attacker's, and the provider cannot
tell which.

| What descends from the code | What happens to it |
|---|---|
| The grant itself | Revoked: the provider's own endpoints and its introspection refuse every access token of that grant from then on |
| Every refresh token descending from the code | Revoked, the rotated ones included |
| The opaque access tokens of the grant | Removed, so that wherever they are presented they are unknown |
| A self-contained access token of the grant | Accepted until it expires by a resource server that verifies it offline against the JWK Set, which nothing the provider does can reach. It lives `tokens.access_token_ttl`, ten minutes by default |

The act `authorization_code.replayed` is written in the journal of the person, naming the client the code
was issued to, the client that presented it again, and the refresh tokens it revoked.
