---
title: JWT bearer
description: An access token for a person, against an assertion signed by an issuer the tenant trusts, RFC 7523 §2.1, what the tenant declares, what is checked, and what is issued.
---

# JWT bearer

A client presents an assertion, a JWT signed by an issuer the tenant trusts, and receives an access token
for the person that assertion is about (RFC 7523 §2.1). The person signed in somewhere else, so this provider
authenticates nobody here: it issues no ID token, takes no `openid`, and creates nobody. The assertion names
somebody the tenant already knows, through an identity an operator linked, or it is refused.

Whoever holds the signing key of a trusted issuer can name a person of the tenant and be answered with an
access token, so everything about that issuer is declared in advance and nothing about it is inferred.

## Declaring the issuer

A deployment declares the issuers its tenant trusts in `BEFFROI_TRUSTED_ISSUERS`, a JSON document keyed by
the `iss` each one signs with ([configuration](../../application/configuration.md#clients-and-their-requests)):

``` dotenv
BEFFROI_TRUSTED_ISSUERS='{"https://issuer.example.com": {"jwks_uri": "https://issuer.example.com/jwks.json", "signing_algorithms": ["ES256"], "clients": ["iFpsLkPvxgJFX_iygElXmtfxqudA9s0D8plYPk_PnDk"], "identity_provider": "example-issuer", "trusted_scopes": ["invoices.read"]}}'
```

| Member | What it decides |
|---|---|
| The key | The `iss` the issuer signs with, an absolute URI without a fragment, compared byte for byte. An issuer nobody declared is unknown |
| `jwks` or `jwks_uri` | Its keys, written down as a JWK Set or read back from a URL, one or the other and never both, nor neither. A URL is HTTPS, or plain HTTP on a loopback host, and is read with one `GET`, no redirect followed. The keys read are kept in a pool the workers share, and read again at most once per cooldown when an assertion names a `kid` the kept set does not hold, which is how an issuer that rotates its keys is followed. These keys are the only ones an assertion is verified against, whatever its header names (RFC 8725 §3.10) |
| `signing_algorithms` | The algorithms an assertion of the issuer may be signed with, at least one, among those the provider is wired with: `RS256`, `PS256`, `ES256`, `EdDSA` |
| `clients` | The clients that may present its assertions, at least one, by the `client_id` the provider drew for each when it [registered](#registering-the-client). An issuer trusted for a gateway is not thereby trusted for every client of the tenant |
| `identity_provider` | The source of the linked identities its subjects name: a `sub` is a person of the tenant only when a linked identity of that source says so |
| `trusted_scopes` | What the issuer is trusted for, at least one scope. `openid` among them buys nothing, the grant refusing it |

A document that breaks one of these rules, or gives an issuer a member this table does not name, is refused
by the first request or command that reads the trusted issuers, and a change of the variable reaches the
processes when they restart. `{}`, the value of the image, trusts no issuer, and a tenant that trusts none
accepts no assertion.

What one read of a `jwks_uri` costs is set by the variables that bound the reads of the clients' sets too:
`BEFFROI_JWKS_URI_TTL`, how long the keys read are kept, `86400` seconds, a day, in the image;
`BEFFROI_JWKS_URI_REFETCH_COOLDOWN`, `300` seconds; `BEFFROI_JWKS_URI_TIMEOUT`, `3` seconds for one read,
connection included; and `BEFFROI_JWKS_URI_MAX_SIZE`, `65536` bytes. The pool of the issuers is not the pool of
the clients, so a client is never verified against a set read for an issuer.

## Linking the people

The `sub` of an assertion names a person of the tenant through a [linked identity](../../core/linked-identities.md)
of the source the issuer declares, and through nothing else. An operator writes that link before the issuer
can name the person:

``` bash
bin/console beffroi:user:link alice example-issuer 248289761001
```

The arguments are the username of the person, the source as `identity_provider` names it, and the subject that
source gives them, compared byte for byte. Running the command again refreshes the link. A subject no link
resolves, or that resolves to a disabled account, is refused like an assertion of an unknown issuer.

## Registering the client

The client reaches a deployment of the image by [registering itself](../dynamic-registration.md). The
deployment opens registration, and names the scopes of the API the client calls, which the tenant then hands
out ([configuration](../../application/configuration.md#the-tenant)):

``` dotenv
BEFFROI_REGISTRATION_MODE=initial_access_token
BEFFROI_TENANT_SCOPES='["invoices.read"]'
```

The client registers with:

``` json
{
    "client_name": "API gateway",
    "token_endpoint_auth_method": "client_secret_basic",
    "grant_types": ["urn:ietf:params:oauth:grant-type:jwt-bearer"],
    "scope": "invoices.read"
}
```

The answer carries the `client_id` the provider drew, which the `clients` of the issuer then name, and the
`client_secret`, said once. A public client is refused a registration for the grant: a token of this grant is
issued only to a client that authenticates itself.

!!! warning "No token for a client of the image"

    A request of this grant names at least one resource, among those the client registered, and `resources` is
    a member of the deployment: a registration that carries it is refused, and no variable gives it to a
    client ([what the image does not set](../clients.md#what-the-image-does-not-set)). A client of the image
    therefore registers no resource, and a request it makes with an assertion this provider accepts is refused
    with `invalid_target`: on a deployment of the image, the JWT bearer grant issues no token. The rest of
    this page is what the grant does for a client that carries resources.

The assertion is the authorization, not the authentication of the client (RFC 7523 §2.1): the client
authenticates beside it with the method it registered, as for every other grant. The two readings of an
assertion share no registration, no validator and no record of the assertions already seen, so an assertion
accepted as one is never thereby accepted as the other.

## The request

| Parameter | |
|---|---|
| `grant_type` | `urn:ietf:params:oauth:grant-type:jwt-bearer` |
| `assertion` | Required: the assertion, a compact JWS |
| `scope` | Required: a request that named nothing would otherwise be answered with everything the registration of the client and the declaration of the issuer have in common |
| `resource` | Required and repeatable, among the resources the client registered (RFC 8707 §2) |

## What is checked of the assertion

**Every refusal is the same refusal**: `invalid_grant`, with the one description `The assertion is not one
this provider accepts as an authorization (RFC 7523 section 3).` Whoever presents an assertion learns that it
was not accepted and nothing else: not whether the issuer is known, not whether the client may present its
assertions, not whether the subject resolves.

1. It is a compact JWS.
2. Its `iss` is an issuer the tenant declares, and the client is among the `clients` of that issuer. Nothing of
   the assertion is verified before that: which keys would verify it is the declaration's answer, never the
   assertion's.
3. Its signature verifies against the keys of that issuer, under one of its `signing_algorithms`, the `kid` of
   the header choosing among those keys only. Keys behind a `jwks_uri` that cannot be read are this same
   refusal.
4. Its `aud` is one value, the issuer identifier of the tenant.
5. It has an `exp`, which is still in the future and no further ahead than
   `BEFFROI_CLIENT_ASSERTION_MAX_LIFETIME`, 300 seconds in the image, both allowing
   `BEFFROI_CLIENT_ASSERTION_LEEWAY`, 30 seconds, of the clock of the issuer.
6. It has an `iat`, no further in the future than the leeway.
7. It has a `jti` this provider has not seen from that issuer before: the `jti` is remembered until the `exp`,
   so that an assertion is spent once.
8. It has a `sub`, which a linked identity of the source of the issuer resolves to a person whose account is
   enabled.

Then what it may obtain:

| Refusal | Error |
|---|---|
| No `resource`, or one the client did not register | `invalid_target` |
| No `scope` | `invalid_request` |
| `openid` among the scopes (OIDC Core §2) | `invalid_scope` |
| A scope the client did not register, or the issuer is not trusted for, or a `scope` that is not a list of scope tokens | `invalid_scope` |

## What the token says

The answer is an access token, with its `token_type`, `expires_in` and `scope`, and nothing else: no ID
token and no refresh token.

| Claim | Value |
|---|---|
| `sub` | The subject this provider gives the person for this client, public or [pairwise](../pairwise-subjects.md), never the subject of the issuer |
| `client_id` | The client |
| `aud` | The resources the request named |
| `scope` | The scopes the request named, within what the client registered and what the issuer is trusted for |
| `grant_id` | An identifier drawn for this answer |
| `person` | In the self-contained shape, the person, sealed by the key management service of the tenant, which only the provider can open; the record of an opaque token keeps the person beside it |
| `may_act` | In the self-contained shape, when the client carries one, a member of the deployment |
| `cnf` | What the token is bound to, when the request binds one ([grants](index.md#what-the-token-endpoint-does)) |

There is no `sid`, `auth_time`, `acr` or `amr`: the person was authenticated somewhere else, and how is not
this provider's to claim. The act `tokens.issued` is written in the journal of that person, and not under
the subject the client reads.
