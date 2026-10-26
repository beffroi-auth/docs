---
title: Resources
description: The audience a client asks its access token for with the resource parameter, RFC 8707, at each endpoint that reads it.
---

# Resources

A client names, in `resource`, the resource server it intends to call, and its access token is issued for
that audience rather than for everything the client might reach (RFC 8707 §2). A resource server that
receives a token addressed elsewhere has what it needs to refuse it. A request made for a person that names no
resource gets a token addressed to the client itself, which is the token UserInfo accepts.

## Registering resources

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients:
        billing:
            # ...
            resources:
                - 'https://api.example.com/'
                - 'urn:example:ledger'
```

`resources` is the closed list of what a client may ask a token for, with no pattern and no wildcard. Each
value is an absolute URI (RFC 3986 §4.3) without a fragment. A query is allowed, RFC 8707 §2 recognising that
it is sometimes what scopes the request, and a URN is a resource as an HTTPS URL is: a resource is an
identifier, which the provider never fetches. What a request names is compared byte for byte with the list.

A client that registers no resource asks for none. Only a declaration writes the list: a client that
[registers itself](dynamic-registration.md) and sends `resources` is refused with `invalid_client_metadata`,
so it asks for none either.

## Asking for one

At the authorization endpoint and at the [pushed authorization request
endpoint](pushed-authorization-requests.md), `resource` may be sent several times, once per resource, which no
other parameter may:

``` http
GET /authorize?response_type=code&client_id=billing&...
    &resource=https%3A%2F%2Fapi.example.com%2F
    &resource=urn%3Aexample%3Aledger HTTP/1.1
```

In a [request object](request-objects.md), the same claim carries a list of strings. A value named twice
counts once. A value that is not an absolute URI without a fragment, and a resource the client did not
register, are both `invalid_target`, at the redirect URI of an authorization request and as JSON at the
pushed request endpoint; the description names no resource, what a client registered being nothing an error
teaches whoever sent the request. A request that names none asks for none, and nothing is filled in from the
registration: a token valid at several resources is valid at each of them (RFC 8707 §3), so it is asked for
and never assumed.

The resources named travel with the authorization: the code carries them, and the token endpoint may narrow
them and never widen them.

## What the access token says

| | Resources asked for | None asked for |
|---|---|---|
| `aud` of the access token | The resources, a string for one and a list for several (RFC 7519 §4.1.3) | The `client_id` |
| `client_id` of the access token | The client, whatever the audience | The client |
| `aud` at the introspection endpoint | The same as the token | The same as the token |
| UserInfo | Refused, `invalid_token` with a `401`: the token is addressed to a resource of its own and not to this provider | Answered |

The opaque shape of access token is described by the introspection endpoint with the same `aud`. When the
provider reads a self-contained token of its own back, it accepts in `aud` only the client itself and the
resources that client registered, so a value it would never have written is refused before anything else is
believed.

## At the token endpoint

| Grant | A `resource` named | None named |
|---|---|---|
| `authorization_code`, `refresh_token` | Narrows the access token of this response to those, among the ones the authorization carries. The refresh token stays bound to them all, so a later refresh may ask for another of them | The resources of the authorization |
| `client_credentials` | Among the ones the client registered | Refused with `invalid_target`: a token with nobody behind it is addressed to a resource, or it is not issued |
| JWT bearer | Among the ones the client registered | Refused with `invalid_target` |
| Token exchange | Narrows to some of the resources the presented token is addressed to | The resources of the presented token. One addressed to its client and to no resource has none to pass on, and is not exchanged |

A resource outside what the line allows is `invalid_target`, in the JSON of the token endpoint. A token
exchange is held to the registration of the client that asks as well: the resources its access token is
addressed to, and the scopes it carries, are ones that client registered, so an exchange never reaches a
resource or a scope its registration does not name. The device
authorization endpoint and the backchannel authentication endpoint read `resource` when the flow starts,
against the resources the client registered, answering `invalid_target` in their own JSON, and a request that
names none there gets a token addressed to the client, a person being behind those flows.

## What the tenant announces

What a tenant announces as its protected resources is read from the clients that registered one, never from
a list kept beside them, and it is the `protected_resources` member of RFC 9728 §4: the one member of the
registry that says what the values of a `resource` parameter are, RFC 8707 registering none of its own. Every
resource a client of the tenant registered is in it, each once. A tenant whose clients registered none
announces nothing rather than an empty list, which a client would read as "no resource is acceptable here".

[:beffroi-arrow-right: Access tokens](tokens/access-tokens.md) and [introspection and
revocation](introspection-and-revocation.md)
