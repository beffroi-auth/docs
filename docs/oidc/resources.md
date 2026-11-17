---
title: Resources
description: 'The audience a client asks its access token for with the resource parameter, RFC 8707: which resources a client holds, and what each endpoint does with one.'
---

# Resources

A client names, in `resource`, the resource server it intends to call, and its access token is issued for
that audience rather than for everything the client might reach (RFC 8707 §2). A resource server that
receives a token addressed elsewhere has what it needs to refuse it. A request made for a person that names no
resource gets a token addressed to the client itself, which is the token UserInfo accepts.

**A client asks only for the resources it holds.** What a client may name is the closed list of its
`resources`. A client of the image holds one only when the initial access token it registered with gave it,
and a client that holds none has every `resource` parameter refused and every access token addressed to
itself.

## Registering resources

`resources` is the closed list of what a client may ask a token for, with no pattern and no wildcard, compared
byte for byte with what a request names. It is a member of the deployment: a client that [registers
itself](dynamic-registration.md) and sends it is refused with `invalid_client_metadata`, and the registration
policy of a tenant writes none. A client of the image holds the resources the initial access token it
registered with gives, which the console issues with `--resource`, once per resource, and keeps them when it
replaces its registration ([what the image does not set](clients.md#what-the-image-does-not-set)). A client
that holds none asks for none.

``` bash
bin/console beffroi:client:token:issue 'Billing team' --resource=https://api.example.com/
```

For a resource server that accepts the access tokens of a client that holds no resource, that means:

- the `aud` of every access token is the `client_id` of its client, so a resource server that checks the
  audience (RFC 9068 §4) checks it against the identifiers of the clients that call it;
- the `aud` of a token tells no resource server from another: the tokens a client presents to two resource
  servers carry the same `aud`, and a token one of them receives can be presented to the other. What tells
  them apart is the `scope` of the token, one scope per API the tenant protects in `BEFFROI_TENANT_SCOPES`,
  which a resource server holds a token to;
- `client_credentials` and the JWT bearer grant, which address a token to a resource or issue none, issue that
  client none ([below](#at-the-token-endpoint)).

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
request. For a client that holds neither resource above, the request above is refused. A request that names
none asks for none, and nothing is filled in.

## What the access token says

| | An authorization that carries no resource | One that carries resources |
|---|---|---|
| `aud` of the access token | The `client_id` | The resources the token is addressed to |
| `client_id` of the access token | The client | The client |
| `aud` at the introspection endpoint | The same as the token | The same as the token |
| UserInfo | Answered | Refused with `invalid_token` |

When the provider reads a self-contained token of its own back, it accepts in `aud` only the client itself and
the resources that client holds, the client alone for a client that holds none, so a value it would never have
written is refused before anything else is believed.

## At the token endpoint

| Grant | A `resource` named | None named |
|---|---|---|
| `authorization_code`, `refresh_token` | The token is narrowed to the resources named, among those of the authorization; one the authorization does not carry is `invalid_target` | The token is addressed to every resource of the authorization, or to the client when it carries none |
| `client_credentials` | The token is addressed to the resources named, among those the client holds; any other is `invalid_target` | Refused with `invalid_target`: a token with nobody behind it is addressed to a resource, or it is not issued |
| JWT bearer | As `client_credentials` | Refused with `invalid_target` |

A client that holds no resource therefore obtains no token under `client_credentials` or the JWT bearer grant:
a token request under them that the other checks of its grant let through is refused with `invalid_target`,
in the JSON of the token endpoint. A client is registered for the [token
exchange](grants/token-exchange.md) only when its initial access token gave it `token_exchange`, a member of
the deployment as well. The device authorization endpoint and the backchannel authentication endpoint read
`resource` when the flow starts, and refuse a value the client does not hold with `invalid_target` in their own
JSON; a request that names none there gets a token addressed to the client, a person being behind those flows.

## What the tenant announces

What a tenant announces as its protected resources is read from the resources its clients hold, never from a
list kept beside them, and it is the `protected_resources` member of RFC 9728 §4: the one member of the
registry that says what the values of a `resource` parameter are, RFC 8707 registering none of its own. A
tenant whose clients hold none announces nothing rather than an empty list, which a client would read as "no
resource is acceptable here", and that is what a deployment of the image announces until the initial access
token of one of its clients gives a resource. The administration API of the tenant is never announced.

[:beffroi-arrow-right: Access tokens](tokens/access-tokens.md) and [introspection and
revocation](introspection-and-revocation.md)
