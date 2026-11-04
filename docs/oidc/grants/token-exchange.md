---
title: Token exchange
description: Turning an access token of this provider into another one for a narrower audience, RFC 8693, delegation against impersonation, and why no client of a deployment of the image is registered for it.
---

# Token exchange

A client presents an access token this provider issued and receives another one, about the same subject,
addressed to resources the first one was already addressed to, and good for no scope the first one did not
carry (RFC 8693 §2.1). It is how a gateway that received a person's token calls the service behind it with a
token of its own, narrowed to that service, and how a service tells the resource it calls that it acts for
somebody else.

**No client of a deployment of the image is registered for it**, and no access token of the image is one it
takes: [registering a client for it](#registering-a-client-for-it) says why. The rest of this page is what the
grant does for a client that carries `token_exchange` and a token addressed to a resource.

## Registering a client for it

What a client may do at the exchange is registered in advance and never asked for, in the `token_exchange`
member:

- `subject_token_types`, the types of token the client may present as a `subject_token` or an `actor_token`
  (RFC 8693 §3), at least one. The provider reads one type, `urn:ietf:params:oauth:token-type:access_token`,
  an access token of this provider in either shape.
- `may_act_for_a_user`, whether the client may present a token issued on a sign-in at this provider, `false`
  when left out. A token that carries no sign-in, one a client holds for itself or one of a [JWT
  bearer](jwt-bearer.md) assertion, is presented without it.

The grant and the member come together or not at all. The `client_id` of a client of the grant is one a `sub`
can be, one to 255 visible ASCII characters and no space, since it is named where a subject is expected, and a
public client is refused the grant.

**`token_exchange` is a member of the deployment.** A registration that carries it is refused with
`invalid_client_metadata`, and so is a registration that names the grant without it. A deployment of the image
declares no client, and no variable gives the member to one, so no client of the image is registered for the
grant, and the token endpoint answers a request of it with `unauthorized_client` ([what the image does not
set](../clients.md#what-the-image-does-not-set)).

**Nor is an access token of the image exchangeable.** A client of the image registers no resource, so each of
its access tokens is addressed to the client itself, and an exchange refuses a token addressed to its own
client: it was asked for no resource, so there is nothing to narrow.

## The request

| Parameter | |
|---|---|
| `grant_type` | `urn:ietf:params:oauth:grant-type:token-exchange` |
| `subject_token` | Required: the token the new one is about, which may have been issued to any client of the tenant |
| `subject_token_type` | Required, a type the provider reads and the client registered |
| `actor_token` | Optional: the token of whoever acts, which makes the exchange a delegation |
| `actor_token_type` | Required with an `actor_token`, refused without one |
| `requested_token_type` | Optional, and `urn:ietf:params:oauth:token-type:access_token` when present: it is the one type the provider issues |
| `scope` | Optional: a subset of the scopes of the presented token, each one registered by the client. Absent, all of the presented token's |
| `resource` | Optional and repeatable: a subset of the resources the presented token is addressed to, each one registered by the client. Absent, all of the presented token's |
| `audience` | Refused with `invalid_target`: what a token of this provider is addressed to is named by `resource` (RFC 8707 §2) |

## What is checked

A presented token is read the way the provider's own endpoints read one: an access token of this provider that
has not expired; when it was issued on a sign-in, whose session has not ended and whose grant has not been
revoked; and when it names a person, one the provider still serves. The client is told that the token is not
good, and not which of those questions it failed (RFC 8693 §2.2.2).

A client not registered for the exchange is refused with `unauthorized_client`. A `requested_token_type` of
another type, a token type the provider does not read or the client did not register, a presented token it
does not honour, a token issued on a sign-in presented by a client without `may_act_for_a_user`, an actor
token issued to another client than the one presenting it, and a party `may_act` does not name are
`invalid_request`. A scope the presented token does not carry, or the client did not register, is
`invalid_scope`; a resource the presented token is not addressed to, or the client did not register, and a
presented token addressed to its own client, are `invalid_target`.

## Delegation and impersonation

The two cases of RFC 8693 §1.1 are told apart by the request and by nothing else. With an `actor_token`, the
exchange is a delegation: the new token names who acts for the subject in an `act` claim (RFC 8693 §4.1),
whose `sub` is the subject of the actor token, which has to be a token issued to the client that presents it.
An `act` the presented token already carried is nested inside the new one, the most recent actor outermost.
Without one, it is an impersonation: the new token says nothing of anybody acting beyond what the presented
token said, and carries its `act`, if any, unchanged.

### Who may act

`may_act` is the word of the subject's side (RFC 8693 §4.4). Registered on a client, it names the one party
that may act for the subject of a token issued to that client: it is written on every self-contained token
that client receives, and an exchange of a token of that client is refused with `invalid_request` for anybody
else, the party compared being the outermost actor the new token would name or, when it would name none, the
client that asked. It is a member of the deployment too, which no client of the image carries ([what the image
does not set](../clients.md#what-the-image-does-not-set)).

## What the issued token says

| Claim | Value |
|---|---|
| `sub` | The `sub` of the presented token, unchanged (RFC 8693 §2.2.1) |
| `client_id` | The client that asked for the exchange |
| `aud` | The resources the request named, or every resource the presented token is addressed to |
| `scope` | The scopes the request named, or every scope of the presented token |
| `act` | Who acts for the subject, on a delegation, and on an impersonation of a token that already said |
| `sid`, `auth_time`, `acr`, `amr` | The sign-in of the presented token, unchanged, when it had one |
| `grant_id` | The grant of the presented token |
| `person` | The person the token is about, sealed by the key management service of the tenant, when the presented token names a person ([access tokens](../tokens/access-tokens.md#the-person-a-token-is-about)) |
| `cnf` | What the exchange request binds the new token to ([grants](index.md#what-the-token-endpoint-does)), whatever the presented token was bound to |

The answer carries the access token, `issued_token_type` set to
`urn:ietf:params:oauth:token-type:access_token` (RFC 8693 §2.2.1), its `token_type`, `expires_in` and `scope`,
and no refresh token and no ID token. The new token descends from the grant the presented one descended from:
taking that grant back takes both, and the end of the session the presented token named refuses both.
