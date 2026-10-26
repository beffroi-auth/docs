---
title: Token exchange
description: Turning an access token of this provider into another one for a narrower audience, RFC 8693, delegation against impersonation, and what the issued token says.
---

# Token exchange

A client presents an access token this provider issued and receives another one, about the same subject,
addressed to resources the first one was already addressed to, and good for no scope the first one did not
carry (RFC 8693 §2.1). It is how a gateway that received a person's token calls the service behind it with a
token of its own, narrowed to that service, and how a service tells the resource it calls that it acts for
somebody else.

The presented token may have been issued to any client of the tenant: holding it is what the request is
about. What the client may do with it is registered in advance and never asked for, and the answer is an
access token and nothing else.

## Registering a client for it

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients:
        gateway:
            client_name: 'API gateway'
            secret: '%env(GATEWAY_SECRET)%'
            token_endpoint_auth_method: client_secret_basic
            grant_types: ['urn:ietf:params:oauth:grant-type:token-exchange', client_credentials]
            scope: 'invoices.read'
            resources: ['https://invoices.example.com']
            token_exchange:
                subject_token_types: ['urn:ietf:params:oauth:token-type:access_token']
                may_act_for_a_user: true
```

| Member | What it decides |
|---|---|
| `token_exchange.subject_token_types` | The types of token the client may present as a `subject_token` or as an `actor_token` (RFC 8693 §3), at least one. The provider reads one type, `urn:ietf:params:oauth:token-type:access_token`, an access token of this provider in either shape; a name it does not read is refused |
| `token_exchange.may_act_for_a_user` | Whether the client may present a token issued on a sign-in at this provider. `false` by default: a service that only ever exchanges tokens clients hold for themselves is not the same party as a gateway carrying a person's token, and the registration says which of the two it is. A token that carries no sign-in, one a client holds for itself or one of a [JWT bearer](jwt-bearer.md) assertion, is presented without it |
| `resources` | The resources the new token may be addressed to. Every resource of the new token is one of these as well as one of the presented token |
| `scope` | The scopes the new token may carry. Every scope of the new token is one of these as well as one of the presented token |
| `may_act` | Registered on the client the presented token was issued to, not on this one: [below](#who-may-act) |

A client registered for the grant declares `token_exchange`, and a `token_exchange` without the grant is
refused. The `client_id` of a client registered for the grant is one a `sub` can be, one to 255 visible ASCII
characters and no space, since it is named where a subject is expected. `client_credentials` is beside the
grant in the example for the [delegation](#delegation-and-impersonation), whose actor token is a token the
client holds for itself.

**The new token never holds more than the registration of the client that asks.** A request that names no
`scope` asks for every scope of the presented token, and one that names no `resource` for every resource it
is addressed to; when that is more than the client registered, the request fails and no token is issued. A
client that may be presented a token holding more than it registered names, in `scope` and `resource`, what
it registered. The request of a public client fails the same way: an exchanged token is issued only to a
client that authenticates itself.

## The request

| Parameter | |
|---|---|
| `grant_type` | `urn:ietf:params:oauth:grant-type:token-exchange` |
| `subject_token` | Required: the token the new one is about |
| `subject_token_type` | Required, a type the provider reads and the client registered |
| `actor_token` | Optional: the token of whoever acts, which makes the exchange a delegation |
| `actor_token_type` | Required with an `actor_token`, refused without one |
| `requested_token_type` | Optional, and `urn:ietf:params:oauth:token-type:access_token` when present: it is the one type the provider issues |
| `scope` | Optional: a subset of the scopes of the presented token, each one registered by the client. Absent, the request asks for all of the presented token's |
| `resource` | Optional and repeatable: a subset of the resources the presented token is addressed to, each one registered by the client. Absent, the request asks for all of the presented token's |
| `audience` | Refused: what a token of this provider is addressed to is named by `resource` (RFC 8707 §2), and a logical name beside it would be a second way of saying it with nothing registered behind it |

## What is checked

| Refusal | Error |
|---|---|
| The client did not register `token_exchange` | `unauthorized_client` |
| A `requested_token_type` other than the access token type | `invalid_request` |
| An `audience` parameter | `invalid_target` |
| A token type the provider does not read, or the client did not register, or a type missing beside its token, or present without one | `invalid_request` |
| A presented token this provider does not honour, below | `invalid_request` |
| A subject token somebody signed in for, presented by a client not registered with `may_act_for_a_user` | `invalid_request` |
| An actor token issued to another client than the one presenting it | `invalid_request` |
| A party `may_act` does not name | `invalid_request` |
| A scope the presented token does not carry, or a `scope` that is not a list of scope tokens | `invalid_scope` |
| A resource the presented token is not addressed to, or a presented token addressed to its own client and to no resource | `invalid_target` |

A scope or a resource of the new token that the client did not register, and a public client, make the
request fail with no token issued, as said above.

**A presented token is read the way the provider's own endpoints read one.** It is an access token of this
provider, in either shape, that has not expired; and a token issued on a sign-in at this provider is one
whose session has not ended, whose grant has not been revoked, and which names a person the provider still
serves, so that a session somebody ended cannot be turned into a fresh token by a service that kept an old
one. What the client is told is that the token is not good, and not which of those questions it failed
(RFC 8693 §2.2.2).

**A token addressed to its own client is not exchangeable.** It was asked for no resource, so there is
nothing to narrow, and the new token could only be addressed outside what the old one covered.

## Delegation and impersonation

The two cases of RFC 8693 §1.3 are told apart by the request and by nothing else: no flag, scope or
registration member turns one into the other.

=== "Delegation, with an actor token"

    The new token names who acts for the subject in an `act` claim (RFC 8693 §4.1), whose `sub` is the
    subject of the actor token. The actor token is a token issued to the client that presents it, typically
    one it holds for itself, whose `sub` is its `client_id`: a token is held by whoever holds it, so a client
    that could present somebody else's would write that somebody into the `act` of a token they never asked
    for.

    When the presented token already carried an `act`, the new actor is added around it, the most recent
    actor outermost, so a chain of exchanges nests and is never flattened:

    ``` json
    "act": {
        "sub": "invoices-worker",
        "act": {
            "sub": "gateway"
        }
    }
    ```

=== "Impersonation, without one"

    The new token says nothing of anybody acting beyond what the presented token already said: it is the
    subject, and the `act` the presented token carried, if any, is carried unchanged.

### Who may act

`may_act` is the word of the subject's side on the matter (RFC 8693 §4.4). Registered on a client, it names
the one party that may act for the subject of a token issued to that client: it is written on every
self-contained token that client receives, and an exchange of one of its tokens is refused with
`invalid_request` for anybody else, whatever the registration of the client that asks says. The party
compared is the one about to hold the new token: the outermost actor the new token would name or, when it
would name none, the client that asked, whose `client_id` stands for it. A client that registered no
`may_act` leaves the decision to the registration of whoever asks.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients:
        frontend:
            # ...
            may_act: gateway
```

## What the issued token says

| Claim | Value |
|---|---|
| `sub` | The `sub` of the presented token, unchanged, as it was written for the client that token was issued to (RFC 8693 §2.2.1) |
| `client_id` | The client that asked for the exchange |
| `aud` | The resources the request named, or every resource the presented token is addressed to |
| `scope` | The scopes the request named, or every scope of the presented token |
| `act` | Who acts for the subject, on a delegation, and on an impersonation of a token that already said |
| `sid`, `auth_time`, `acr`, `amr` | The sign-in of the presented token, unchanged, when it had one |
| `grant_id` | The grant of the presented token |
| `person` | The person the token is about, sealed, when the presented token was issued on a sign-in: below |
| `may_act` | In the self-contained shape, when the client that asked registered one |
| `cnf` | What the new token is bound to: what the exchange request binds it to ([grants](index.md#what-the-token-endpoint-does)), whatever the presented token was bound to |

The answer carries the access token, `issued_token_type` set to `urn:ietf:params:oauth:token-type:access_token`
(RFC 8693 §2.2.1), its `token_type`, `expires_in` and `scope`, and no refresh token and no ID token. The new
token lives `tokens.access_token_ttl`, in the shape the client that asked registered.

**The new token descends from the grant the presented one descended from.** Taking that grant back takes
both, and the end of the session the presented token named refuses both, at the provider's own endpoints
and at its introspection.

**The issued token knows the person it is about, when the presented token was issued on a sign-in.** Its
`sub` was written for another client, and may be a pairwise subject the client that asked cannot read. So
the provider keeps the person the presented token named beside it: on the record of an opaque token, and,
in a self-contained one, as the private claim `person`, sealed by the key management service of the tenant,
which only the provider can open and which tells the holder nothing it did not know. That is what lets the
provider's own endpoints and introspection read an exchanged token, and what puts the acts it gives rise to,
the tokens issued and the introspections that describe it, in the journal of that person.

A presented token that carries no sign-in names no person to the exchange: a token a client holds for
itself, and a token of a [JWT bearer](jwt-bearer.md) assertion alike. The token issued for it then carries
no `person` claim, its record names nobody, and its `tokens.issued` act is written in no journal.
