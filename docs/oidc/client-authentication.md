---
title: Client authentication
description: The seven methods a client may register, what each one reads of a request and checks, and how a refusal is answered.
---

# Client authentication

A client authenticates with the one method it registered and with no other (RFC 6749 §2.3.1). The method is
read wherever the provider has to know which client is calling: the token endpoint, the
[introspection and revocation](introspection-and-revocation.md) endpoints, the [pushed authorization
request](pushed-authorization-requests.md) endpoint, the device authorization endpoint and the backchannel
authentication endpoint. A request that presents another method than the registered one is refused exactly
as a request that presents a wrong secret is.

## The methods

The bundle wires seven, in this order:

| Method | What the request carries | What is checked | What the client registers |
|---|---|---|---|
| `client_secret_basic` | `Authorization: Basic`, the identifier and the secret form-urlencoded and joined by a colon (RFC 6749 §2.3.1, RFC 7617 §2) | The secret, against the hash the provider keeps | A secret |
| `client_secret_post` | `client_id` and `client_secret` in the body (RFC 6749 §2.3.1) | The same | A secret |
| `private_key_jwt` | `client_assertion`, a JWT it signed with a key of its own (RFC 7523 §2.2, OIDC Core §9) | The signature against the keys the client publishes, then the claims | `jwks` or `jwks_uri` |
| `client_secret_jwt` | `client_assertion`, a JWT signed with its secret under `HS256` (OIDC Core §9) | The MAC with the secret the provider keeps, then the claims | A secret |
| `tls_client_auth` | `client_id`, and a certificate at the TLS handshake (RFC 8705 §2.1) | The one value of RFC 8705 §2.1.2 it registered, read out of the certificate | One of the five `tls_client_auth_*` values |
| `self_signed_tls_client_auth` | `client_id`, and a certificate at the TLS handshake (RFC 8705 §2.2) | That the certificate is one the client publishes | `jwks` or `jwks_uri` |
| `none` | `client_id` alone (RFC 6749 §2.1) | Nothing: the client names itself | Nothing |

A client that registers no method takes `client_secret_basic`, the first one wired for a declared client and
the default of RFC 7591 §2 for one that registers itself. What the wiring holds is what a client may
register and what the discovery document announces, so a method taken out of the wiring is neither accepted
nor announced.

| Member of the discovery document | What it lists |
|---|---|
| `token_endpoint_auth_methods_supported`, `revocation_endpoint_auth_methods_supported` | The seven methods, in the order above |
| `introspection_endpoint_auth_methods_supported` | The six that authenticate a client: `none` is refused there (RFC 7662 §2.1) |
| `token_endpoint_auth_signing_alg_values_supported` and its two siblings | What an assertion may be signed with: `RS256`, `PS256`, `ES256` and `EdDSA` for `private_key_jwt`, `HS256` for `client_secret_jwt` |

## A shared secret

`client_secret_basic` and `client_secret_post` present the secret itself, and the provider keeps only a hash
of it, made by the password hasher of the core and compared by it. A request whose client is unknown, or
registered for another method, pays the same verification against a decoy hash, so the time an answer takes
says nothing about which clients exist.

`client_secret_basic` reads a header made of `Basic`, whatever its case, then spaces or tabs, then one token
(RFC 7235 §2.1). A token that does not decode to an identifier and a secret joined by a colon, an empty one
included, is `invalid_request`; a header of another form is not one the method reads. `client_secret_post`
takes the secret from a body that also names the client in `client_id`, and a `client_secret` without one is
`invalid_request`.

`client_secret_jwt` signs an assertion with the secret, so the provider has to hold the secret to compute the
same MAC: it keeps the secret itself, sealed in the row of a client that registered itself. That is the cost
of the method: a compromised process of the provider holds what computes the MAC as well.

## An assertion

`private_key_jwt` and `client_secret_jwt` carry the same assertion, in the same two parameters:

``` http
POST /token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=...&redirect_uri=...&code_verifier=...
&client_assertion_type=urn%3Aietf%3Aparams%3Aoauth%3Aclient-assertion-type%3Ajwt-bearer
&client_assertion=eyJhbGciOiJFUzI1NiIsImtpZCI6IjEifQ...
```

`client_assertion_type` is `urn:ietf:params:oauth:client-assertion-type:jwt-bearer` and nothing else, and the
two parameters come together or not at all. Which of the two methods reads the assertion is decided by its
`alg`: `HS256` is `client_secret_jwt`, an algorithm the provider signs with is `private_key_jwt`. The
signature is verified first, and nothing the assertion says is believed before it is. Then:

| Claim | What it has to say |
|---|---|
| `iss`, `sub` | The `client_id`, both of them. A `client_id` in the body, when there is one, names the same client |
| `aud` | One value, and only one: the issuer of the tenant. A client registered for the backchannel grant may name the token endpoint or the backchannel authentication endpoint instead, on either host the provider serves them on (CIBA Core §7.1) |
| `exp` | Present, not past, and no further ahead than the lifetime the provider accepts |
| `iat` | Present, and not in the future |
| `jti` | Present, and never seen before for that client: it is remembered until the `exp` in the `beffroi.client_assertions` cache pool, which a deployment of several machines points at a store they share |

**The key is the client's and nobody else's.** A `kid` in the header names one of the keys the client
publishes, a header without one is tried against all of them, and a key that names another `alg`, or a `use`
other than `sig`, is not tried. `jwk`, `jku` and `x5c` in the header are ignored (RFC 8725 §3.10).

**Keys behind a `jwks_uri` are read and kept.** The URL is read with one `GET`, no redirect followed, any
status but `2xx` refused, within a time and a size of its own. The set is kept in the `beffroi.client_keys`
cache pool, filed under its URL, and read again when an assertion names a `kid` the kept set does not hold, at
most once per cooldown: a client that rotates its key is followed at once, and one that signs with a key it
never published cannot make the provider call it on every request. A set that cannot be read refuses the
authentication, and the reason goes to the audit trail.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    client_authentication:
        assertion_max_lifetime: 300
        assertion_leeway: 30
        jwks_timeout: 3.0
        jwks_max_size: 65536
        jwks_ttl: 86400
        jwks_refetch_cooldown: 300
```

| Option | Default | What it decides |
|---|---|---|
| `assertion_max_lifetime` | `300` | Seconds ahead of the request the `exp` of an assertion may be (RFC 7523 §3) |
| `assertion_leeway` | `30` | Seconds allowed of the clock of a client, both ways |
| `jwks_timeout` | `3.0` | Seconds one read of a `jwks_uri` is given, connection included |
| `jwks_max_size` | `65536` | Bytes a `jwks_uri` may answer before the read stops |
| `jwks_ttl` | `86400` | Seconds a set read from a `jwks_uri` is kept |
| `jwks_refetch_cooldown` | `300` | Seconds between two reads of one `jwks_uri` when an assertion names an unknown `kid` |

The same six options bound the assertions of the issuers a tenant trusts for the [JWT bearer
grant](grants/jwt-bearer.md), and the reads of the sets they publish.

## A certificate

`tls_client_auth` and `self_signed_tls_client_auth` read the same thing, the certificate of the connection,
and the client names itself in `client_id`. The certificate is the one the TLS listener in front of the
provider writes in the `SSL_CLIENT_CERT` server variable, never a header: a request that carries
`SSL-Client-Cert`, `X-SSL-Client-Cert`, `X-Client-Cert` or `X-Forwarded-Client-Cert` is refused with
`invalid_request`. Only the leaf reaches the provider, so the chain, the validity period and the revocation of
the certificate are judged by the listener, which is where a deployment that turns `tls_client_auth` on says
which authorities it accepts.

- **`tls_client_auth`** compares one value read out of the certificate with the one the client registered:
  its subject distinguished name, written as RFC 4514 writes one and normalised when the client is read, so
  that `openssl x509 -noout -subject -nameopt RFC2253` prints a name it can register as it is; or one entry
  of its subject alternative name, a DNS name compared without regard to case, a URI compared as text, an IP
  address compared as the octets it stands for, an email address compared as written.
- **`self_signed_tls_client_auth`** authenticates a certificate the client publishes in its JWK Set, as the
  first entry of the `x5c` of a key (RFC 7517 §4.7) or by its `x5t#S256` (§4.9). The certificate is compared,
  not the key inside it, so a certificate reissued on the same key is published before it is presented.

Both bind the tokens of the request to the certificate that authenticated it (RFC 8705 §3.1). A certificate
presented beside a secret or an assertion authenticates nothing: the listener asked for it, the request did
not choose it. Whether it binds the tokens of such a client is what the client registered in
`tls_client_certificate_bound_access_tokens`. [Mutual TLS](sender-constrained/mutual-tls.md) says how a
deployment serves the host that asks for a certificate, and what a bound token is then.

## A public client

`none` is not an authentication, and it is announced as what it is: the client names itself in `client_id`
and proves nothing, which is what a native or a browser application can do. The introspection endpoint
refuses it with `invalid_client`, describing a token only to a client that proves who it is (RFC 7662 §2.1),
and a client that registers it is refused `client_credentials` and `requires_pkce: false`. What protects a
public client is PKCE and its exact redirect URI, never this method.

## How a request is read, and refused

The request presents one mechanism or it is refused before anything is verified: credentials in the
`Authorization` header and others in the body are two mechanisms (RFC 6749 §2.3), and so are a secret and an
assertion. The two certificate methods read one thing and are one mechanism, the registration of the client
saying which of them verifies it. An `Authorization` header no method reads, of another scheme than `Basic`
or not of its form, is refused when nothing else in the request proves the client, a public client naming
itself included; beside a credential of the body or a certificate of the connection that proves the client,
it is not read.

| What the request does | Error | Status |
|---|---|---|
| A credential parameter that is not a single string, `Basic` credentials that do not decode, half of an assertion, another `client_assertion_type`, an assertion that is no JWT | `invalid_request` | `400` |
| Two mechanisms at once | `invalid_request` | `400` |
| A `client_id` in the body that names another client than the credentials | `invalid_request` | `400` |
| An `Authorization` header no method reads, and nothing else that proves the client, or no credential at all | `invalid_client` | `401` |
| An unknown client, a method other than the registered one, a wrong secret, an assertion refused or replayed, keys that cannot be read, a certificate that is not the client's | `invalid_client`, described `Client authentication failed.` | `401` |

Every refusal of the last line reads the same, so an answer does not say whether a client exists or which
method it registered; why it was refused goes to the audit trail, with the client and the method, as a
`ClientAuthenticationFailed` event. A `401` carries `WWW-Authenticate: Basic realm="<issuer>"` when the client
used the `Authorization` header, and no challenge otherwise (RFC 6749 §5.2).

A client that authenticates counts one request against its own load budget, `load.client`, 1200 requests in
60 seconds by default, here and nowhere else, this being the one place its identifier is proven rather than
claimed. A public client counts nothing there, the budget of the address it calls from bounding it. A spent
budget is answered `429` with a `Retry-After`.

[:beffroi-arrow-right: Clients](clients.md), [DPoP](sender-constrained/dpop.md) and [mutual
TLS](sender-constrained/mutual-tls.md)
