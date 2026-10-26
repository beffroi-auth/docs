---
title: Request objects
description: The authorization request as a JWT the client signed, RFC 9101: by value or by reference, the algorithms a client registers, what is checked, and what is refused.
---

# Request objects

A request object is the authorization request as a JWT the client signed (RFC 9101, OIDC Core §6), so the
provider reads what the client meant rather than what a browser passed along. The parameters are the claims
of the object, and nothing of it is believed before its signature is verified, under the algorithm the client
registered and against the keys it publishes. A client that registered nothing is never read an unsigned
object.

## Two ways in

| Parameter | What it carries |
|---|---|
| `request` | The object itself, by value |
| `request_uri` | The URL the object is published at, read back by the provider (RFC 9101 §5.2) |

The two together are no request at all, and are refused with `invalid_request`, unless the `request_uri` is
a reference of the [pushed authorization request endpoint](pushed-authorization-requests.md): the request is
then the one that was pushed, and a `request` beside the reference is dropped with every other parameter of
the query. `client_id` is sent outside the object as well, because the provider has to know whose keys verify
it before it reads anything of it (RFC 9101 §5).

**The object is the request.** Its parameters replace those of the query, which are dropped, `client_id`
apart (OIDC Core §6.1): what the client signed and what the provider reads are one request, and the redirect
URI is matched against the registration of the client byte for byte as it is everywhere else, so an object
chooses how the answer travels and never where it goes. What the object asks is then judged exactly as an
[authorization request](authorization-request.md) in the query would be.

Both ways are served at the authorization endpoint. The [pushed authorization request
endpoint](pushed-authorization-requests.md) takes the object by value, verifies it there, once, and keeps
what it carried, so the authorization endpoint reads a pushed request as it reads any other.

## What a client registers

| Member | What it means for its objects |
|---|---|
| `request_object_signing_alg` absent | Signed under any algorithm the provider verifies: `RS256`, `PS256`, `ES256` or `EdDSA`. Never unsigned |
| `request_object_signing_alg` naming one of those | Signed under that algorithm and no other. The client publishes its keys in `jwks` or behind a `jwks_uri` |
| `request_object_signing_alg: none` | Unsigned, and read all the same: the one exception, registered client by client, never a switch of the deployment |
| `request_uris` | The URLs its objects may be read back from, compared byte for byte, fragment included |
| `require_signed_request_object` | Its authorization requests are read from a request object and from nothing else, signed as its `request_object_signing_alg` says. A request without one is refused on a page, with `invalid_request`, before its redirect URI is read. Its backchannel authentication requests are read from an object it signed, and from nothing else |

An object signed under an algorithm the client did not register is refused unread, whatever its signature is
worth. The discovery document lists in `request_object_signing_alg_values_supported` the algorithms the
provider verifies, and `none` beside them only when a client of the tenant registered it: the member says what
a client of this tenant may register, not what any client is read under.

## What is checked

The key is one the client publishes, named by the `kid` of the header or, without one, tried among all of
them; a key that names another `alg`, or a `use` other than `sig`, is not tried, and `jwk`, `jku` and `x5c` in
the header are ignored (RFC 8725 §3.10). Keys behind a `jwks_uri` are read as they are for a [client
assertion](client-authentication.md). Once the signature verifies:

| Claim | What it has to say |
|---|---|
| `client_id` | When the object carries one, the `client_id` the request names outside it |
| `iss` | The `client_id` (RFC 9101 §4) |
| `aud` | The issuer of the tenant among its values, so an object made for another provider, or another tenant, is not replayed here (RFC 9101 §10.2) |
| `nbf` | Present, and not in the future |
| `exp` | Present, not past, and no more than the maximum lifetime after `nbf` |

These are asked of every signed object, whatever the client. An unsigned object, from a client that
registered `none`, is held to the `client_id` rule alone, OIDC Core §6.1 leaving the other claims optional
for an object whoever wrote it could have written. The authorization endpoint and the pushed authorization
request endpoint do not read `iat` and `jti`. The backchannel authentication endpoint asks both of a signed
object, and remembers the `jti` until the `exp` of the object, so one signed backchannel request is made once
(CIBA Core §7.1.1): an object without them, or with a `jti` already used, is refused there with
`invalid_request`.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    request_objects:
        max_lifetime: 3600
        leeway: 30
        timeout: 3.0
        max_size: 65536
```

| Option | Default | What it decides |
|---|---|---|
| `max_lifetime` | `3600` | Seconds an object may stand, from its `nbf` to its `exp` |
| `leeway` | `30` | Seconds allowed of the clock of the client, both ways |
| `timeout` | `3.0` | Seconds one read of a `request_uri` is given, connection included |
| `max_size` | `65536` | Bytes a `request_uri` may answer before the read stops |

## What an object may carry

The claims of the object are the parameters of the request, each named as the parameter it stands for
(RFC 6749 §8.2), except the ones RFC 7519 §4.1 reserves for what a token says about itself, `iss`, `aud`,
`exp`, `nbf`, `iat` and `jti`, which are never parameters. A claim is a string, or what the query would have
carried in its place (OIDC Core §6.1):

- an integer, as `max_age` is sent in an object, is the parameter written in digits;
- a list of strings is a parameter sent once per string, which is how `resource` travels in an object
  (RFC 8707 §2.1);
- any other object or array is the parameter written as its JSON, which is how `claims` and
  `authorization_details` travel.

A boolean, a fraction or a `null` is no parameter of an authorization request, and is refused rather than
converted, with a description that names the claim. An object carries no `request` and no `request_uri` of
its own (RFC 9101 §4).

## By reference

A `request_uri` that is not a reference of the [pushed authorization request
endpoint](pushed-authorization-requests.md) is a URL the object is published at, and it is read back only when
the client registered that very URL in `request_uris`, compared byte for byte, its fragment included. A URL the
client did not register is refused before any request leaves the provider, which is what
`require_request_uri_registration: true` announces.

The fragment, which OIDC Core §6.2 defines as the hash of the content, is not sent: the URL is read without
it, with one `GET` that sends `Accept: application/oauth-authz-req+jwt, application/jwt`, follows no redirect,
and refuses any status but `2xx`, an answer longer than `max_size` and a read longer than `timeout`. What comes
back is read as an object sent by value would be. The hash in the fragment is not compared with it.

## An encrypted object

A client may encrypt its object to a key the tenant publishes for encryption (RFC 9101 §6.1), the object
signed first and then encrypted, which is what `request` and `request_uri` carry. The JWE names the key it
was encrypted to in its `kid`, among the keys of the [JWK Set](discovery-and-jwks.md) of the tenant with `use:
enc`, its `alg` is the algorithm of that key, and its `alg` and `enc` are among those the provider is wired
with, which the discovery document announces in `request_object_encryption_alg_values_supported`,
`ECDH-ES+A256KW` and `RSA-OAEP-256`, and `request_object_encryption_enc_values_supported`, `A256GCM`. A JWE that
names no key, a key that signs or a key that has retired is refused.

What the JWE carries is the signed object, read and verified as one sent in clear: being encrypted says who
may read the request, never who wrote it (OIDC Core §16.14). For a client that registered `none`, the JWE may
carry the claims themselves, read as an unsigned object.

## Refusals

A refused object is an object that was not read, so nothing of it names where an answer could go: every
refusal is shown on a page at the authorization endpoint, with status `400`, and answered in JSON at the
pushed authorization request endpoint.

| Error | When |
|---|---|
| `invalid_request` | `request` and `request_uri` together; at the authorization endpoint, an unknown client or a `client_id` missing outside the object |
| `invalid_request_object` | An object that does not open or does not parse, an algorithm the client did not register, keys of the client that cannot be read, a signature no key of the client verifies, a claim refused as above, a claim whose value is no parameter |
| `invalid_request_uri` | A `request_uri` the client did not register, or one that cannot be read back |

At the pushed authorization request endpoint the client authenticates before its object is read ([client
authentication](client-authentication.md)): a client that is unknown there is refused with `invalid_client`,
and the object is read against the client that authenticated, whose identifier stands for a `client_id` the
body leaves out.

A description names the claim it refuses, and never repeats the `alg` of the object or a value it carries.

[:beffroi-arrow-right: Pushed authorization requests](pushed-authorization-requests.md) and [response
modes](response-modes.md)
