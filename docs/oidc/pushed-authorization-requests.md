---
title: Pushed authorization requests
description: The authorization request sent server to server first, RFC 9126: the endpoint, the reference it answers with, how long it lives, and what a client may be held to.
---

# Pushed authorization requests

The client pushes its authorization request to the provider, authenticating itself, and receives a
`request_uri` the browser then carries to the authorization endpoint (RFC 9126). Nothing of the request
travels in a URL the browser can read or change, and the request is read when it is pushed, by the two stages
the authorization endpoint reads one with, before any browser is sent anywhere.

## Pushing a request

``` http
POST /par HTTP/1.1
Host: op.example.com
Content-Type: application/x-www-form-urlencoded
Authorization: Basic YmlsbGluZzpzM2NyM3Q...

response_type=code
&redirect_uri=https%3A%2F%2Fbilling.example.com%2Foidc%2Fcallback
&scope=openid%20profile
&state=af0ifjsldkj
&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
&code_challenge_method=S256
```

`/par` takes a `POST` and nothing else, its parameters in the form of the body. The client authenticates
exactly as it does at the token endpoint, with the method it registered ([client
authentication](client-authentication.md)); a public client names itself in `client_id`. The request is then
read by the two stages the authorization endpoint reads one with ([the order of the
checks](authorization-request.md#the-order-of-the-checks)), the redirect URI included: what either stage
refuses is refused here, by the same code. What the authorization endpoint asks of a request once it is read,
the verification of an `id_token_hint` and whether an essential `acr` is one the provider can prove, is asked
when the browser brings the reference there, and refused at the redirect URI.

- The request names the client that authenticated and no other: a `client_id` of the body that names another
  is refused, and one left out is the authenticated client.
- A `request_uri` in the body is refused with `invalid_request`. A `request`, a [request
  object](request-objects.md) by value, is read here, against the client that has just authenticated, and is
  verified once, at this endpoint.
- A request that carries a DPoP proof reserves its code for the key the proof proves, as a `dpop_jkt` would
  (RFC 9449 §10.1), and one that names a `dpop_jkt` and proves another key is refused with `invalid_request`
  ([DPoP](sender-constrained/dpop.md)).

The answer is a `201`:

``` http
HTTP/1.1 201 Created
Content-Type: application/json
Cache-Control: no-cache, no-store
Pragma: no-cache

{"request_uri":"urn:ietf:params:oauth:request_uri:6esc_11ACC5bwc014ltc14eY22cQ2xpZW50UmVxdWVz","expires_in":60}
```

The reference is the URN of RFC 9126 §2.2 followed by 256 random bits in base64url. The provider keeps its
SHA-256 and never its value, beside the parameters of the request as the client wrote them, or as the object
it pushed carried them, without what authenticated it: `client_secret`, `client_assertion` and
`client_assertion_type` authenticate the request that carried them and nothing else. The parameters are sealed
where they are kept, since they carry the hints of the request word for word.

**A refusal is never a redirection.** Whatever the endpoint refuses, a parameter, the redirect URI or the
client, is answered in the JSON of RFC 6749 §5.2 with the headers above, even when the request names a
redirect URI the provider would otherwise have answered to: no browser has been sent anywhere yet. A client
authentication that fails is `invalid_client`, a `401`; one the request does not carry as it should, a
`client_id` of the body that names another client included, is `invalid_request`, a `400`, as every other
refusal of the request is ([client authentication](client-authentication.md#how-a-request-is-read-and-refused)).
A request past a [budget of load](errors.md#refused-for-load), the one of its address or the one of its
client, is answered `429`, with `Retry-After`, `Cache-Control: no-store` and an `error_description` but no
`error` member.

## How long a reference lives

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    tokens:
        request_uri_ttl: 60
```

| Option | Default | What it decides |
|---|---|---|
| `tokens.request_uri_ttl` | `60` | Seconds a reference lives, at most `600` (RFC 9126 §2.2) |

`expires_in` is the number of seconds the reference still has, never more than it has.

## Using the reference

``` http
GET /authorize?client_id=billing&request_uri=urn%3Aietf%3Aparams%3Aoauth%3Arequest_uri%3A6esc_11ACC5bwc014ltc14eY22cQ2xpZW50UmVxdWVz HTTP/1.1
```

`client_id` and `request_uri` are the whole of the request: the parameters are the ones that were pushed, and
any other parameter of the query is dropped, so the query never contradicts what was pushed (RFC 9126 §4).

**A reference is read by the client it was issued to**, before it expires, and **spent with the code it
buys** (FAPI 2.0 Security Profile §5.3.1). Until a code is issued, the reference may be read again: a person
who reloads the page they were sent to is still holding a request nobody has answered. Two interactions
begun on one reference cannot both finish: the reference is claimed when the code is issued, and the second
to claim it is refused.

| What the reference is | Answered with |
|---|---|
| Unknown, issued to another client, past its lifetime, or spent | A page, `400`, `invalid_request_uri`, the four the same answer. The audit trail keeps which it was, and both clients |
| Spent by another interaction at the moment this one issues its code | A page, `400`, `invalid_request_uri` |

A `request_uri` that is not a reference of this provider, not of the form of the URN above, is read as a
[request object by reference](request-objects.md) instead, and is fetched only from a URL the client
registered.

## Requiring it

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients:
        billing:
            # ...
            require_pushed_authorization_requests: true
```

A client registered with `require_pushed_authorization_requests` starts an authorization request in no
other way (RFC 9126 §6). An ordinary request of that client is refused on a page, with `invalid_request`,
before its redirect URI is even read, so that nothing of the request goes back to the browser that carried
it. It is a member of the client, and nothing of the deployment sets it for every client.

The discovery document announces `pushed_authorization_request_endpoint`, and
`require_pushed_authorization_requests` (RFC 9126 §5) as `true` exactly when the tenant has clients and every
one of them carries the requirement, whichever source holds them, and `false` as soon as one does not. When
the deployment serves a host that asks for a certificate, the endpoint is announced under that host as well,
in `mtls_endpoint_aliases` ([mutual TLS](sender-constrained/mutual-tls.md)).

[:beffroi-arrow-right: Authorization request](authorization-request.md) and [request
objects](request-objects.md)
