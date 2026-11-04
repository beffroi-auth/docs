---
title: Access tokens
description: The two shapes an access token is written in, a signed at+jwt or an opaque reference, what each one carries, and what the provider and a resource server ask of one.
---

# Access tokens

An access token is what a client presents to a resource server. The provider writes it in one of two shapes,
and each client receives its access tokens in one of them, so a resource server knows from the client what it
is validating:

| Shape | `access_token_format` | What it is | How a resource server reads it | At the revocation endpoint |
|---|---|---|---|---|
| Self-contained | `jwt` | A JWT signed by the tenant, of type `at+jwt` (RFC 9068) | Offline, against the [JWK Set](../discovery-and-jwks.md) of the issuer | Refused: it expires on its own (RFC 7009 §2.2.1) |
| Reference | `opaque` | 256 random bits in base64url, 43 characters, which mean something to this provider alone | At the [introspection endpoint](../introspection-and-revocation.md) (RFC 7662) | Taken back at once |

**Every client of the image receives the self-contained shape.** The shape of a client is its
`access_token_format`, a member of the deployment: a registration that carries it is refused with
`invalid_client_metadata`, and no variable gives it to a client, so every client of the image takes `jwt`, the
first shape the provider is wired with ([what the image does not
set](../clients.md#what-the-image-does-not-set)).

Both shapes live `BEFFROI_ACCESS_TOKEN_TTL` seconds, ten minutes in the image: the self-contained one cannot
be taken back, so its lifetime is what bounds it, and the opaque one gets the same, a revocation being a
facility and not a reason to live longer. A deployment sets it in its environment
([configuration](../../application/configuration.md#keys-and-lifetimes)):

``` dotenv
BEFFROI_ACCESS_TOKEN_TTL=600
```

No access token is ever encrypted.

## What it says

Both shapes carry the same facts: the self-contained one in its claims, the reference in the record the
provider keeps under its SHA-256, which introspection renders under the same names.

| Claim | What it holds |
|---|---|
| `iss` | The issuer of the tenant |
| `sub` | Who the token is about: for a person who signed in, the subject this provider gives them for this client, public or [pairwise](../pairwise-subjects.md); for a client acting for itself, its `client_id`; for a token of a token exchange or of a JWT bearer assertion, the subject the grant named |
| `client_id` | The client the token was issued to (RFC 9068 §2.2) |
| `aud` | The resources it is addressed to (RFC 8707 §2), named by the request or carried by what the grant spends, as the page of each grant says: a token exchange that names none is addressed to every resource of the presented token, and a token of an authorization that carries no resource is addressed to the `client_id`, as every token of a client of the image is. One value is written as a string, several as a list |
| `exp`, `iat` | When it expires, and when it was issued |
| `scope` | The scopes it carries, space-delimited |
| `auth_time`, `acr`, `amr`, `sid` | What the session had proven when the authorization was granted, and that session (RFC 9068 §2.2.1). Absent from a token nobody signed in for |
| `grant_id` | The grant the token descends from, which the provider asks, of a token somebody signed in for, whether it is still alive |
| `authorization_details` | What the person agreed to beyond the scopes (RFC 9396 §7), when there is any |
| `act` | Who acts for the subject (RFC 8693 §4.1), on a token of a [token exchange](../grants/token-exchange.md) |
| `cnf` | What the token is bound to: `jkt`, the thumbprint of a DPoP key (RFC 9449 §6.1), or `x5t#S256`, the thumbprint of a certificate (RFC 8705 §3.1) |

The self-contained shape carries four claims more, which introspection does not render: `jti`, a random UUID;
`userinfo_claims`, the claims the client asked for by name for the UserInfo endpoint (OIDC Core §5.5);
`may_act`, who may act for the subject of a token of this client (RFC 8693 §4.4), when it carries one, which
no client of the image does; and `person`, below.

### The header

`typ` is `at+jwt` (RFC 9068 §2.1), `kid` names the key of the JWK Set that signed it, and `alg` is the
algorithm the provider signs with by default, the first one it is wired with, `RS256`. It is never the
algorithm the client registered for its ID tokens: an access token is read by resource servers, not by the
client.

### The person a token is about

**A token whose `sub` was written for another client says who it is about, sealed.** A token issued by a
[token exchange](../grants/token-exchange.md) of a token issued on a sign-in keeps the `sub` of that token,
written for the client it was issued to, which may be a pairwise subject the client now holding it cannot
read; a token of a [JWT bearer](../grants/jwt-bearer.md) assertion names a person nobody signed in for here.
For both, the provider keeps the person beside the token: on the record of a reference, and in a
self-contained token as the private claim `person` (RFC 7519 §4.3), sealed by the key management service of
the tenant. Only the provider opens it, and a resource server reads it as it reads any claim it was given no
meaning for. A token a client holds for itself is about nobody and carries none, and so does a token of a
token exchange whose presented token named nobody.

## What the provider asks of a token it is presented

The provider's own endpoints that take an access token, UserInfo, introspection and the token exchange, read
both shapes the same way and ask more of a token than its signature:

1. it was issued by this tenant, and it has not expired, with no leeway, the clock being the provider's own;
2. the session it descends from has not ended;
3. the grant it descends from has not been revoked;
4. the person it is about is still served.

A token nobody signed in for at this provider descends from no session and no grant, and the second and third
questions are not asked of it; the fourth is, when it names a person, as a token of a JWT bearer assertion
does. A resource server that holds the token and the JWK Set and nothing else cannot ask the other three,
which is what verifying offline means: **a self-contained token outlives the end of its session, the consent
taken back and the revocation of its grant wherever it is verified offline**, until it expires. Introspection
answers `"active": false` for it from the instant any of those happened.

The UserInfo endpoint takes only a token addressed to the client itself, the one a request that names no
resource gets, as every request of a client of the image does: a token addressed to a resource is refused
there with `invalid_token`, whatever it is good for elsewhere.

## Choosing a shape

A deployment of the image has no choice to make: every client of it receives `jwt`, above. The two shapes
answer two kinds of resource server:

=== "jwt"

    For a resource server that verifies tokens itself, with no call to the provider per request. The token
    cannot be taken back: the revocation endpoint answers `unsupported_token_type` for one, and the end of a
    session, a consent taken back or a replayed code reach it only at the provider's own endpoints and at
    introspection. Its lifetime is therefore the window in which a stolen one is worth something.

=== "opaque"

    For a resource server that asks the provider about every token. The revocation endpoint takes one back at
    once, and the end of a session or a consent taken back removes the ones a person signed in for. The
    resource server introspects as the client the token was issued to: introspection describes a token to that
    client and to nobody else (RFC 7662 §2.2), and only to a client that authenticates.

A token is a bearer token unless the request that obtained it binds it: to the key of its DPoP proof, or to
the certificate of its connection for a client that authenticates with that certificate (`tls_client_auth`,
`self_signed_tls_client_auth`) or registered `tls_client_certificate_bound_access_tokens`
([grants](../grants/index.md#what-the-token-endpoint-does)). The
`token_type` of the answer then says `DPoP` for a key and `Bearer` for a certificate.
[Sender-constrained tokens](../sender-constrained/index.md) says what a resource server then asks of the
caller.

## Adding a shape

A shape is two classes answering to one name, which is what a client carries in `access_token_format`: an
issuer implementing `Beffroi\Oidc\Port\AccessTokenShapeIssuerInterface`, tagged
`beffroi.oidc.access_token_issuer`, and a verifier implementing
`Beffroi\Oidc\Port\AccessTokenVerifierInterface`, tagged `beffroi.oidc.access_token_verifier`. The first
tagged issuer is the shape a client that carries none takes, `jwt` in the application. A shape written with no
verifier, read with no issuer, or written by two issuers is refused, a token the provider writes and cannot
read back being a token nobody can spend.
