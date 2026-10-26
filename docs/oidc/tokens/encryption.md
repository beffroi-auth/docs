---
title: Encryption
description: The three documents the provider encrypts for a client that asks, the algorithms it encrypts with, the key it encrypts to, and what happens when that key cannot be read.
---

# Encryption

A client may ask for three of the documents the provider hands it to be encrypted to a key of its own: its ID
token, its UserInfo answer, and its signed authorization responses. The provider encrypts for the client that
registered it and for nobody else, and a client that registered nothing receives its documents unencrypted.

| Document | The pair a client registers | Signed before it is encrypted |
|---|---|---|
| [ID token](id-tokens.md) (OIDC Core §3.1.3.7) | `id_token_encrypted_response_alg`, `id_token_encrypted_response_enc` | Always |
| [UserInfo](../userinfo.md) answer (OIDC Core §5.3.2) | `userinfo_encrypted_response_alg`, `userinfo_encrypted_response_enc` | When the client also registered `userinfo_signed_response_alg`; otherwise what is encrypted is the plain JSON of the claims |
| Signed [authorization response](../response-modes.md) (JARM §3) | `authorization_encrypted_response_alg`, `authorization_encrypted_response_enc` | Always |

Access tokens, refresh tokens and logout tokens are never encrypted. A logout token is signed with the
algorithm the client registered for its ID tokens, and travels in clear.

**Signed, then encrypted, never the other way round** (OIDC Core §16.14). The signature says who wrote the
document and travels inside what hides it, so that a client that opens the JWE finds something to verify
rather than something to trust. A signed document inside a JWE is a nested JWT, and the header of the JWE
says so with `cty` `JWT` (RFC 7519 §5.2).

## Registering it

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients:
        my-application:
            # ...
            jwks_uri: 'https://app.example.com/jwks.json'
            id_token_encrypted_response_alg: RSA-OAEP-256
            id_token_encrypted_response_enc: A256GCM
            userinfo_signed_response_alg: ES256
            userinfo_encrypted_response_alg: RSA-OAEP-256
            userinfo_encrypted_response_enc: A256GCM
```

- **The two members of a pair come together.** OIDC Registration §2 lets the `enc` be left out and defaults it
  to `A128CBC-HS256`, which this provider is not wired with, so it takes no default: one member without the
  other is refused.
- **Each name is one the provider is wired with**, below, and any other is refused.
- **The client publishes its keys**, in `jwks` or behind a `jwks_uri`, and a client that registers an
  encryption and publishes neither is refused. A `jwks` written down is read at registration and has to hold
  a key the registered algorithm can be addressed to; a set behind a URL is read when a document is minted.

A declared client that breaks one of these rules is an error of the configuration, and a registration request
that breaks one is answered `invalid_client_metadata`.

## The algorithms

| | Wired | Announced in the discovery document as |
|---|---|---|
| Key management, the `alg` | `ECDH-ES+A256KW`, to an `EC` key, and `RSA-OAEP-256`, to an `RSA` key | `id_token_encryption_alg_values_supported`, `userinfo_encryption_alg_values_supported`, `authorization_encryption_alg_values_supported` |
| Content encryption, the `enc` | `A256GCM` | `id_token_encryption_enc_values_supported`, `userinfo_encryption_enc_values_supported`, `authorization_encryption_enc_values_supported` |

The document announces what is wired and nothing else. The two `authorization_` members are announced only
while the provider serves a response mode that signs its answer, and a provider wired with no algorithm of one
of the two lists announces none of these members at all, since it can encrypt nothing. The same two lists are
what a client may encrypt a [request object](../request-objects.md) to the tenant with, in the other direction.

## The key it is encrypted to

The provider encrypts to a key the client publishes, chosen by what the keys say of themselves (RFC 7517 §4.2,
§4.4):

1. Only a key of the type the algorithm takes is a candidate: `EC` for `ECDH-ES+A256KW`, `RSA` for
   `RSA-OAEP-256`.
2. A key whose `use` is anything but `enc` is never one.
3. A key that names an `alg` is a candidate for that algorithm and no other.
4. Among the candidates, a key that names the algorithm wins over one whose `use` is `enc`, which wins over
   one that says neither, and inside each of the three the first one published wins.

A client that publishes several keys therefore chooses the one it is encrypted to by saying more about it.

A set behind a `jwks_uri` is read with one `GET`, over HTTPS or in plain HTTP on a loopback host, no redirect
followed. What is read is kept for `client_authentication.jwks_ttl` seconds, a day by default, in a pool the
workers share, under the URL it was read from. Encrypting a document never reads it again before that, a
document addressed to a client naming no `kid` the provider could find missing. The kept set serves every
use of the keys of the client, though, and a signature of the client whose header names a `kid` the set does
not hold, the assertion of `private_key_jwt` or a request object, reads it again, at most once per
`client_authentication.jwks_refetch_cooldown`, 300 seconds by default. A client that replaces its encryption
key publishes the new one and keeps the private half of the old one for `jwks_ttl` after that.

## When the key cannot be read

**No document leaves in clear.** When the set behind the `jwks_uri` cannot be read, or holds no key the
registered algorithm can be addressed to, the provider writes nothing for that client, and the request that
was to carry the document fails: the token request that was to carry the ID token, once the code, the device
code or the `auth_req_id` it presented has been spent, the UserInfo request, or the authorization response.

A read is given `client_authentication.jwks_timeout` seconds, 3 by default, and
`client_authentication.jwks_max_size` bytes, 65536 by default, before it counts as a set that cannot be
read.
