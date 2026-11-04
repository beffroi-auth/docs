---
title: Resources
description: 'The audience a client asks its access token for with the resource parameter, RFC 8707: why a client of the image asks for none, and what each endpoint does with one.'
---

# Resources

A client names, in `resource`, the resource server it intends to call, and its access token is issued for
that audience rather than for everything the client might reach (RFC 8707 §2). A resource server that
receives a token addressed elsewhere has what it needs to refuse it. A request made for a person that names no
resource gets a token addressed to the client itself, which is the token UserInfo accepts.

**A client of the image asks for no resource.** What a client may name is the closed list of its `resources`,
and no client of a deployment of the image holds one: every `resource` parameter is refused, and every access
token is addressed to the client it was issued to.

## Registering resources

`resources` is the closed list of what a client may ask a token for, with no pattern and no wildcard, compared
byte for byte with what a request names. It is a member of the deployment: a client that [registers
itself](dynamic-registration.md) and sends it is refused with `invalid_client_metadata`, the registration
policy of a tenant writes none, no variable gives one to a client, and the image declares no client. No client
of the image holds a resource ([what the image does not set](clients.md#what-the-image-does-not-set)), and a
client that holds none asks for none.

For a resource server that accepts the access tokens of the image, that means:

- the `aud` of every access token is the `client_id` of its client, so a resource server that checks the
  audience (RFC 9068 §4) checks it against the identifiers of the clients that call it;
- the `aud` of a token tells no resource server from another: the tokens a client presents to two resource
  servers carry the same `aud`, and a token one of them receives can be presented to the other. What tells
  them apart is the `scope` of the token, one scope per API the tenant protects in `BEFFROI_TENANT_SCOPES`,
  which a resource server holds a token to;
- `client_credentials` and the JWT bearer grant, which address a token to a resource or issue none, issue none
  ([below](#at-the-token-endpoint)).

## Asking for one

At the authorization endpoint and at the [pushed authorization request
endpoint](pushed-authorization-requests.md), `resource` may be sent several times, once per resource, which no
other parameter may:

``` http
GET /authorize?response_type=code&client_id=s6Bh3dRkqt3Hm9vBkrnfeR7_xU2ZyQ4lJaN0cP8TwYg&...
    &resource=https%3A%2F%2Fapi.example.com%2F
    &resource=urn%3Aexample%3Aledger HTTP/1.1
```

In a [request object](request-objects.md), the same claim carries a list of strings. A value that is not an
absolute URI without a fragment (RFC 3986 §4.3), and a resource the client does not hold, are both
`invalid_target`, at the redirect URI of an authorization request and as JSON at the pushed request endpoint;
the description names no resource, what a client holds being nothing an error teaches whoever sent the
request. On the image every value is one or the other, so the request above is refused. A request that names
none asks for none, and nothing is filled in.

## What the access token says

| | On the image |
|---|---|
| `aud` of the access token | The `client_id` |
| `client_id` of the access token | The client |
| `aud` at the introspection endpoint | The same as the token |
| UserInfo | Answered |

When the provider reads a self-contained token of its own back, it accepts in `aud` only the client itself and
the resources that client holds, the client alone on the image, so a value it would never have written is
refused before anything else is believed.

## At the token endpoint

| Grant | A `resource` named | None named |
|---|---|---|
| `authorization_code`, `refresh_token` | Refused with `invalid_target`: the authorization carries no resource to narrow to | The token is addressed to the client |
| `client_credentials` | Refused with `invalid_target`: the client holds no resource | Refused with `invalid_target`: a token with nobody behind it is addressed to a resource, or it is not issued |
| JWT bearer | Refused with `invalid_target` | Refused with `invalid_target` |

A deployment of the image therefore issues no token under `client_credentials` or the JWT bearer grant: a
client may register either, and a token request under them that the other checks of its grant let through is
refused with `invalid_target`, in the JSON of the token endpoint. No client of the image is registered for
the [token exchange](grants/token-exchange.md), whose `token_exchange` member is a member of the deployment as
well. The device authorization endpoint and the backchannel authentication endpoint read `resource` when the
flow starts, and refuse any value with `invalid_target` in their own JSON; a request that names none there
gets a token addressed to the client, a person being behind those flows.

## What the tenant announces

What a tenant announces as its protected resources is read from the resources its clients hold, never from a
list kept beside them, and it is the `protected_resources` member of RFC 9728 §4: the one member of the
registry that says what the values of a `resource` parameter are, RFC 8707 registering none of its own. A
tenant whose clients hold none announces nothing rather than an empty list, which a client would read as "no
resource is acceptable here", and that is what a deployment of the image announces.

[:beffroi-arrow-right: Access tokens](tokens/access-tokens.md) and [introspection and
revocation](introspection-and-revocation.md)
