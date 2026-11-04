---
title: Discovery and JWKS
description: The document a client reads before anything else, every member it publishes and what decides it, and the JWK Set through a rotation. OIDC Discovery 1.0, RFC 8414 and RFC 7517.
---

# Discovery and JWKS

Two documents describe the provider to whoever is about to talk to it. The discovery document says what the
provider serves and where (OIDC Discovery 1.0 §3, RFC 8414 §2), and the JWK Set publishes the public keys a
client verifies what it receives with and encrypts what it sends with (RFC 7517 §5). Both are read from what
the provider is wired with: a grant, a client authentication method or an algorithm is announced because it
is served, and stops being announced the moment it is not.

## The discovery document

One document, served at the two places a client looks for it:

| Method | Path | Specification |
|---|---|---|
| `GET` | `/.well-known/openid-configuration` | OIDC Discovery 1.0 §4 |
| `GET` | `/.well-known/oauth-authorization-server` | RFC 8414 §3 |

Both answer `200`, `application/json`, with `Cache-Control: public, max-age=3600`: a client may keep the
document an hour.

**The routes are where the issuer says they are.** OIDC Discovery 1.0 §4.1 appends the well-known path to the
issuer, and the application mounts its routes at the root, so its issuer is an origin: a deployment whose
issuer is `https://op.example.com` serves `https://op.example.com/.well-known/openid-configuration`. An issuer
that carries a path makes every endpoint that locates the others fail at the first request, with an error that
names both URLs, rather than publish endpoints a client would not find. RFC 8414 §3 inserts its well-known
segment between the host and the path of the issuer instead, and under an issuer that is an origin the two
locations are the same URL.

**Every URL is built from the issuer**, never from the `Host` header of the request that asked.

### What it publishes

Each specification the provider implements contributes its own members, in the order they are wired, and
nothing assembles a list of them beside the wiring. Two capabilities announcing the same member is a fault the
provider refuses rather than arbitrates.

| Members | What decides them |
|---|---|
| `issuer`, `authorization_endpoint`, `token_endpoint`, `userinfo_endpoint`, `jwks_uri` | The issuer, and the routes under it. Always present |
| `scopes_supported` | `openid`, the scopes the wired claims stand for, the scopes of the APIs `BEFFROI_TENANT_SCOPES` names, the scopes the clients of the tenant registered, and `offline_access` where a wired grant issues a refresh token and another spends one. [Scopes and claims](scopes-and-claims.md) |
| `claims_supported`, `claims_parameter_supported` | `sub` and the claims the provider serves; `true` |
| `response_types_supported` | `["code"]`, and nothing else: no implicit flow and no hybrid |
| `response_modes_supported` | The response modes wired, `query`, `form_post`, `query.jwt` and `form_post.jwt` in the application, plus `jwt` when a signed mode is among them (JARM §2.1). [Response modes](response-modes.md) |
| `grant_types_supported` | The grants the token endpoint is wired with, all seven in the application. [Grants](grants/index.md) |
| `code_challenge_methods_supported` | The PKCE methods wired: `S256`. `plain` is wired nowhere |
| `acr_values_supported` | The classes of the policy of the tenant that the logins it serves can prove, in the order the policy names them. [Tenants](../core/tenants.md) |
| `subject_types_supported` | The kinds of `sub` the provider assigns: `public` and `pairwise`. [Pairwise subjects](pairwise-subjects.md) |
| `token_endpoint_auth_methods_supported`, `token_endpoint_auth_signing_alg_values_supported` | The client authentication methods wired, in the order they are tried, and what their assertions may be signed with. [Client authentication](client-authentication.md) |
| `id_token_signing_alg_values_supported`, `userinfo_signing_alg_values_supported` | The signature algorithms the provider is wired with: `RS256`, `PS256`, `ES256` and `EdDSA` in the application |
| `id_token_encryption_*`, `userinfo_encryption_*`, `request_object_encryption_*` (`alg_values_supported`, `enc_values_supported`) | The encryption algorithms wired: `ECDH-ES+A256KW` and `RSA-OAEP-256`, with `A256GCM`. A provider wired with no key encryption or no content encryption algorithm announces none of these pairs rather than empty lists |
| `request_parameter_supported`, `request_uri_parameter_supported`, `require_request_uri_registration` | `true` all three: a `request_uri` is read only from a URL its client registered |
| `request_object_signing_alg_values_supported` | The signature algorithms wired, and `none` beside them only when a client of the tenant registered `request_object_signing_alg: none`. [Request objects](request-objects.md) |
| `authorization_response_iss_parameter_supported` | `true`: every authorization response carries `iss` (RFC 9207) |
| `pushed_authorization_request_endpoint`, `require_pushed_authorization_requests` | The endpoint; `true` only when every client registered for the tenant requires pushed requests. [Pushed authorization requests](pushed-authorization-requests.md) |
| `device_authorization_endpoint` | The endpoint where a device code is asked for (RFC 8628 §4) |
| `introspection_endpoint`, `introspection_endpoint_auth_methods_supported`, `introspection_endpoint_auth_signing_alg_values_supported`, `introspection_signing_alg_values_supported` | The endpoint, the wired methods that authenticate a client (all but `none`), what their assertions are signed with, and the signature algorithms wired (RFC 9701). [Introspection](introspection-and-revocation.md) |
| `revocation_endpoint`, `revocation_endpoint_auth_methods_supported`, `revocation_endpoint_auth_signing_alg_values_supported` | The endpoint, and the methods of the token endpoint, `none` included |
| `end_session_endpoint`, `frontchannel_logout_supported`, `frontchannel_logout_session_supported`, `backchannel_logout_supported`, `backchannel_logout_session_supported` | The endpoint, and `true` for each logout channel wired, both in the application. [Logout](logout.md) |
| `dpop_signing_alg_values_supported` | The signature algorithms wired. [DPoP](sender-constrained/dpop.md) |
| `tls_client_certificate_bound_access_tokens` | `true` when a method that authenticates by certificate is wired, which the application does. [Mutual TLS](sender-constrained/mutual-tls.md) |

Some members are announced only when what they describe exists, and are absent otherwise rather than empty:

| Members | Present when |
|---|---|
| `registration_endpoint` | `BEFFROI_REGISTRATION_MODE` names a mode the tenant registers clients in. Empty, as it is in the image, the tenant has no registration endpoint at all. [Dynamic registration](dynamic-registration.md) |
| `backchannel_authentication_endpoint`, `backchannel_token_delivery_modes_supported`, `backchannel_authentication_request_signing_alg_values_supported`, `backchannel_user_code_parameter_supported` | A grant of the backchannel flow is wired; the last one is then `false`. [Backchannel authentication](grants/backchannel-authentication.md) |
| `authorization_signing_alg_values_supported`, `authorization_encryption_alg_values_supported`, `authorization_encryption_enc_values_supported` | A signed response mode is wired |
| `mtls_endpoint_aliases` | `BEFFROI_MTLS_ORIGIN` names the host that asks for a certificate. [Mutual TLS](sender-constrained/mutual-tls.md#the-endpoint-aliases) |
| `protected_resources` | A client of the tenant holds resources (RFC 9728 §4), which no client of the image does. [Resources](resources.md) |
| `authorization_details_types_supported` | A type of authorization detail is wired (RFC 9396 §10), which the image wires none of. [Authorization details](authorization-details.md) |

The document announces no `check_session_iframe`: OpenID Connect Session Management 1.0 is not implemented,
and logout goes through the front and back channels. Its content changes when the wiring or the registrations
of the tenant change, never during a key rotation, which is the JWK Set's business.

## The JWK Set

`GET /jwks`, the `jwks_uri` of the discovery document, answers `200` with `application/json` and the public
keys of the tenant (RFC 7517 §5).

**What it holds.** Every key of the tenant in service, staged, active or retiring, of an algorithm the tenant
publishes for: the keys it signs with and the keys a client encrypts to it with. Each JWK carries its `kid`,
`kty`, `alg` and `use`, and nothing private. The keys the tenant keeps for itself are never in it, whatever
their status: the key a browser is handed for web push, the key the tenant seals what leaves the process to,
and the SAML keys, whose certificates the [SAML metadata](../saml/identity-provider.md) publish.

**How long a client keeps it.** The answer says `Cache-Control: public, max-age=` followed by
`BEFFROI_JWKS_MAX_AGE`, three hundred seconds in the image. A set with no key in it is answered `no-store`, so
that no cache keeps an empty set for that long.

Two variables set the figures of the set, here at the values of the image
([configuration](../application/configuration.md#keys-and-lifetimes)):

``` dotenv
BEFFROI_JWKS_MAX_AGE=300
BEFFROI_KEY_STAGING_DELAY=
```

| Variable | In the image | What it decides |
|---|---|---|
| `BEFFROI_JWKS_MAX_AGE` | `300` | The `max-age` of the JWK Set, in seconds. The `max-age` of the SAML metadata reads it too |
| `BEFFROI_KEY_STAGING_DELAY` | empty | How long a new key is published before it signs, in seconds, for every key but the SAML signing key, which has its own. Empty, `BEFFROI_JWKS_MAX_AGE` plus `60` |

### Through a rotation

A rotation asks a client for nothing but to read the set again within its `max-age`.

1. **A new key is published before it signs**, for the staging delay: `BEFFROI_KEY_STAGING_DELAY` is empty in
   the image, which makes it three hundred and sixty seconds, the `max-age` of the set plus the sixty seconds
   a copy has to be old before Symfony's `oidc_login` fetches the set again on a `kid` it does not know. A
   client with a warm cache has seen the new key by the time anything is signed with it.
2. **The new key becomes active** once that delay has run, and signs from then on; the key it replaces is
   retiring, and stays in the set.
3. **The retiring key leaves the set** once nothing it signed can still be presented: the longest lifetime
   among the ID token, the `at+jwt` when a client of the tenant receives that shape, the logout token up to
   its `exp`, which is the budget of its delivery, and the signed authorization response when a signed mode
   is wired. A
   key a client encrypts to stays as long as a pushed request or a request object encrypted to it may still
   arrive. The timed step retires it past that date.

An operator can cut the first step short, and a client with a warm cache then meets a `kid` it does not know
yet: a key activated before its delay has run, with `beffroi:keys:activate`, a key that takes over at once,
with `beffroi:keys:rotate --now`, and a key that replaces a compromised one, with `--compromised`, after which
the compromised key leaves the set at once, with no window.
[Keys](../core/keys.md) gives the commands that rotate, activate and retire a key, and the timed step that
stages a successor once a key has worked its age.
