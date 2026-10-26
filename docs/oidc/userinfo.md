---
title: UserInfo
description: The claims an access token entitles its client to read about the person it was issued for, as JSON or as a signed and encrypted JWT, and every refusal. OIDC Core §5.3.
---

# UserInfo

UserInfo answers the claims an access token allows, about the person the token was issued for, to the client
it was issued to (OIDC Core §5.3). It is the one endpoint where the answer depends on the token and on the
consent behind it rather than on the request, and the protected resource of the provider itself: the rules
a resource server applies to an access token, the provider applies here.

## The request

`GET` or `POST` at `/userinfo`, the `userinfo_endpoint` of the discovery document. The access token travels in
one of two places, never both, and never in the query string (RFC 6750 §2.3, RFC 9700 §4.3.2):

- the `Authorization` header, under `Bearer` or `DPoP`, the scheme read without regard to case; a header of
  a scheme the provider does not serve is left alone, as if the request carried none. A token bound to a key
  is honoured under `DPoP` only, with its proof in the `DPoP` header (RFC 9449 §7.1), and a token bound to a
  certificate under `Bearer` only; a token bound to nothing is served under either;
- the `access_token` parameter of a `POST` form body (RFC 6750 §2.2), which carries a bearer token and
  nothing else.

**The token must be one the provider honours today.** Issued by the provider and not expired, issued to a
client still registered, descending from a session that has not ended and from a grant that has not been
revoked, naming a person the provider still serves, an account that is disabled being one it does not. An
`at+jwt` is held to the same rules as an opaque token here, by the `sid` and the `grant_id` it carries: a
token of a session ended at the [end session endpoint](logout.md) is refused at once, where a resource server
that verifies it offline accepts it until it expires.

**It must be bound as it was issued.** A token bound to a key is honoured when the request presents it under
`DPoP` with a valid proof of that key; a token bound to a certificate, when the connection presents the same
certificate, which is what the `userinfo_endpoint` of the [mutual TLS aliases](sender-constrained/mutual-tls.md#the-endpoint-aliases)
is for.

**It must have been asked for no resource.** A token asked for a resource (RFC 8707 §2) is addressed to that
resource and not to its client, and is refused here with `invalid_token`, however valid it is there: a client
that comes for the claims of its user asks for a token that names no resource. The client credentials and
JWT bearer grants are always asked for a resource, and a token exchange always issues a token addressed to
resources, so their tokens, a token a client holds for itself among them, are refused this way.

**It must carry `openid`.** A token somebody signed in for whose scopes leave `openid` out, which a device
authorization request may do and a refresh may narrow them to, is refused with `insufficient_scope`
(OIDC Core §5.3.1).

## The answer

The claims of the person, as the token entitles its client to them:

- `sub` first, the subject identifier this client knows the person by, public or
  [pairwise](pairwise-subjects.md) as the client registered (OIDC Core §8), never the identifier of the
  account;
- the claims the scopes of the token stand for (OIDC Core §5.4);
- the claims the authorization request asked for by name in the `userinfo` member of its `claims` parameter
  (OIDC Core §5.5), by their names: the `essential`, `value` and `values` such a request may carry decide
  nothing here.

A claim the provider holds no value of is left out rather than sent empty, and a name it does not know is no
error. [Scopes and claims](scopes-and-claims.md) says which claims each scope stands for.

**JSON unless the client registered otherwise**, with `Content-Type: application/json`, `Cache-Control:
no-store` and `Pragma: no-cache`. A client that registered a signature, an encryption or both receives a JWT
instead (OIDC Core §5.3.2), served as `application/jwt` with the same two caching headers:

| Member of the registration | What it does to the answer |
|---|---|
| `userinfo_signed_response_alg` | The claims are signed by the active key of the tenant under that algorithm, the header naming `alg` and `kid`, and `iss` and `aud`, the issuer and the client, are added beside them |
| `userinfo_encrypted_response_alg`, `userinfo_encrypted_response_enc` | The answer is encrypted to a key the client publishes in `jwks` or behind `jwks_uri`, the header naming the two algorithms and the `kid` of that key when it has one. The two come together, never one alone |

Signed then encrypted, never the other way round: with both, the payload of the JWE is the JWS, and its
header says `"cty": "JWT"` (RFC 7519 §5.2). Encrypted without a signature, the payload is the JSON of the
claims, `iss` and `aud` included. Each algorithm is one the provider is wired with, which the discovery
document announces in `userinfo_signing_alg_values_supported`, `userinfo_encryption_alg_values_supported` and
`userinfo_encryption_enc_values_supported`; a registration naming another is refused.
[Encryption](tokens/encryption.md) says what the provider encrypts with.

**Every answer the endpoint writes carries `x-fapi-interaction-id`**, served or refused: the value the
request sent in that header when it sent one UUID, a UUID drawn for the exchange otherwise (FAPI 1.0 Advanced
Final §6.2.1), so that the client and the provider find the same exchange in their logs.

## Refusals

Every refusal is a challenge of RFC 6750 §3: a `WWW-Authenticate` header naming the scheme that would have
worked and, unless the request carried no token at all, the `error` and its `error_description`, repeated as
a JSON body. The same two caching headers come with each.

| The request | Status | `WWW-Authenticate` |
|---|---|---|
| Carries no access token | `401` | `Bearer, DPoP`, with no error and an empty body |
| Sends the token in the header and in the body, or in a header or a parameter of the wrong shape | `400` | `Bearer error="invalid_request"` |
| Carries a client certificate in a header, or reaches PHP with a certificate that cannot be read | `400` | `Bearer error="invalid_request"` |
| Carries a DPoP proof that does not verify, or names another request or another token | `401` | `DPoP error="invalid_dpop_proof"` |
| Carries a proof without the nonce the provider asks for | `401` | `DPoP error="use_dpop_nonce"`, and a fresh nonce in `DPoP-Nonce` |
| Presents a token the provider does not honour, or one addressed to a resource, which every token a client holds for itself is | `401` | `Bearer error="invalid_token"` |
| Does not prove what the token is bound to, or presents it under the wrong scheme | `401` | `error="invalid_token"`, under `DPoP` for a token bound to a key and `Bearer` for one bound to a certificate |
| Presents a token somebody signed in for, without `openid` | `403` | `Bearer error="insufficient_scope"`, with `scope="openid"` |

The descriptions say which rule refused and nothing more: a token refused because it was not issued here
reads the same whatever gave it away. [DPoP](sender-constrained/dpop.md) gives the rules of a proof.

## The journal

**Every answer is an act**, `userinfo.answered`, in the journal of the person whose claims were served,
naming the client they were served to: it is one of the two reads that hand a personal datum to a third
party, [introspection](introspection-and-revocation.md) being the other. It is written once the answer
exists, so a request that was refused writes nothing, nothing of anybody having left. The act says that the
read happened, who asked and about whom, and not which claims were served.
