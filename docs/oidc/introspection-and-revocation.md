---
title: Introspection and revocation
description: What a token is, told to the client it was issued to and to nobody else, as JSON or as a signed JWT, and how a client gives a token back. RFC 7662, RFC 9701 and RFC 7009.
---

# Introspection and revocation

Introspection describes an access token to the client it was issued to and to nobody else, as JSON or as a
signed JWT (RFC 7662, RFC 9701). Revocation lets a client give back a token it holds, and answers the same way
whether the token existed or not (RFC 7009). Both are `POST` endpoints of the protocol plane, and both
authenticate the client first, exactly as the token endpoint does.

## Introspection

`POST /introspect`, the `introspection_endpoint` of the discovery document, with the token in the `token`
parameter of the form body. `token_type_hint` is accepted and ignored.

**The caller is a confidential client.** It authenticates with one of the methods announced in
`introspection_endpoint_auth_methods_supported`, which are the wired methods that authenticate a client, every
one but `none`. A public client is refused with `invalid_client`, status `401`, since it has nothing to
authenticate with.

**A token is described to the client it was issued to, and to nobody else** (RFC 7662 §2.2, §4). Everything
else is answered `{"active": false}` and nothing more, whatever the reason:

- a value the provider did not issue, or no longer holds;
- a token issued to another client;
- an expired token;
- a token of a client no longer registered;
- a refresh token, introspection describing access tokens only;
- for a token somebody signed in for, and a token exchanged from one: a session that has ended, a grant
  that has been revoked, or a person the provider no longer serves, an account that is disabled among them.

The rules are the ones UserInfo applies, read in one place for both shapes of token, so that an `at+jwt` of
a session ended at the [end session endpoint](logout.md) is described as inactive from that moment, where a
resource server that verifies it offline accepts it until it expires.

**A token that descends from no sign-in is asked none of the last three questions.** A token a client holds
for itself names nobody. A token of the JWT bearer grant, and a token exchanged from one, names a person
without descending from a sign-in of theirs: it is described as active until it expires, whatever became of
that person's account in the meantime.

### What an active token is described with

`active` first, then the members of RFC 7662 §2.2 and those of RFC 9068 §2.2.1, whatever the shape of the
token, `at+jwt` or opaque:

| Member | What it says |
|---|---|
| `active` | `true`, a JSON boolean |
| `scope` | The scopes of the token, space-separated |
| `client_id` | The client the token was issued to, which is the caller |
| `token_type` | `DPoP` for a token bound to a key, `Bearer` otherwise |
| `exp`, `iat` | When the token expires and when it was issued |
| `sub` | The subject identifier the token was written with. For a token somebody signed in for and a token of the JWT bearer grant, the one its client knows the person by, public or pairwise; for an exchanged token, the `sub` of the token presented at the exchange, as the client of that token knew it; for a token a client holds for itself, the client |
| `aud` | The client, or the resources the token was asked for (RFC 8707 §2): a string for one value, an array for several |
| `iss` | The issuer |
| `auth_time`, `acr`, `amr`, `sid` | The sign-in the token descends from. Absent from a token a client holds for itself, which descends from none (RFC 6749 §4.4) |
| `grant_id` | The grant the token descends from, a UUID |
| `act` | Who holds the token on behalf of its subject, the most recent actor outermost (RFC 8693 §4.1). Absent when nobody does |
| `authorization_details` | What the token is good for beyond its scopes (RFC 9396 §9). Absent when it carries none |
| `cnf` | What the token is bound to, `jkt` or `x5t#S256` (RFC 7800 §3.1). Absent from a bearer token |

A token bound to a certificate is described whatever certificate the caller presented: the client may
introspect its token however it authenticates today, and the `cnf` is what a resource server needs to make
its own check (RFC 8705 §3.2). [Sender-constrained tokens](sender-constrained/index.md) says what to compare
it with.

### A signed answer

A request whose `Accept` header names `application/token-introspection+jwt` is answered with a JWT of that
type (RFC 9701 §4, §5), whatever the client registered:

| Where | Member | Value |
|---|---|---|
| Header | `typ` | `token-introspection+jwt` |
| Header | `alg`, `kid` | The algorithm the provider signs with by default, `RS256` in the bundle, and the key that signed |
| Claims | `iss` | The issuer |
| Claims | `aud` | The client that asked |
| Claims | `iat` | When the request was received |
| Claims | `token_introspection` | The members above, `{"active": false}` included |

The answer is signed and not encrypted. A resource server verifies it against the JWK Set of the provider,
whose URL it reads in the `jwks_uri` of the discovery document. The document announces the signing
algorithms the provider is wired with in `introspection_signing_alg_values_supported`, and the answer is
signed with the default one among them.

Either answer is served with `Cache-Control: no-store` and `Pragma: no-cache`, as `application/json` or as
`application/token-introspection+jwt`.

### The journal

**An answer that hands a person over is an act of their journal.** An introspection that describes an active
token somebody signed in for, or a token exchanged from one, tells a third party who that token names, so it
is written down, `introspection.answered`, naming the client that asked and the person. An answer
`{"active": false}` writes nothing, since it describes nobody. The act is written for a token that descends
from a sign-in and for no other: the description of a token a client holds for itself writes nothing, and
neither does the description of a token of the JWT bearer grant or exchanged from one.

## Revocation

`POST /revoke`, the `revocation_endpoint` of the discovery document, with the token in the `token` parameter.
`token_type_hint` is accepted and ignored: the provider recognises what it is given.

**Every client may revoke its own tokens.** It authenticates with the methods announced in
`revocation_endpoint_auth_methods_supported`, which are the methods of the token endpoint, `none` included: a
public client names itself in `client_id` and revokes what was issued to it.

| The token | What the provider does | The answer |
|---|---|---|
| An opaque access token issued to the caller | Removes it: it is refused everywhere from then on | `200` |
| A refresh token issued to the caller | Revokes it, and removes the opaque access tokens of its grant (RFC 7009 §2.1) | `200` |
| A refresh token already revoked | Nothing | `200` |
| An `at+jwt` that verifies, whichever client it was issued to: signed by a published key of the tenant, not expired, issued to a client still registered, whatever became of its session, its grant or its person | Nothing: a self-contained token cannot be taken back (RFC 7009 §2.2.1) | `400`, `unsupported_token_type` |
| An `at+jwt` that does not verify: expired, or not issued by the provider | Nothing | `200` |
| Any other token issued to another client, or a value the provider does not know | Nothing (RFC 7009 §2.2) | `200` |

A `200` has an empty body, with `Cache-Control: no-store` and `Pragma: no-cache`, so that the answer says
nothing about whether the token existed.

**What a revocation does not reach.** An `at+jwt` issued under the grant of a refresh token that was revoked
stays valid until it expires, at a resource server as at the endpoints of the provider: the provider keeps no
list of the self-contained tokens it would refuse, and its lifetime is what bounds it, ten minutes unless
`tokens.access_token_ttl` says otherwise. A client whose access tokens must be taken back at once is declared
with `access_token_format: opaque`.

**Every revocation is an act**, `token.revoked`, in the journal of the person the token was issued for; the
revocation of a token a client held for itself names nobody.

Revocation ends one token and what depends on it. What takes back everything issued under a session is the
end of that session, at the [end session endpoint](logout.md) or anywhere else, and what takes back the
grants, the refresh tokens and the opaque access tokens a client holds for a person is that person taking back
their consent, on [the page of their account](../symfony-bundle/account.md) or with
`beffroi:user:revoke-consent`. In both cases an `at+jwt` is refused by the provider from that moment, and
accepted by a resource server that verifies it offline until it expires.

## Refusals

Both endpoints answer with the errors of RFC 6749 §5.2, as JSON, with `Cache-Control: no-store` and
`Pragma: no-cache`:

| Error | Status | When |
|---|---|---|
| `invalid_client` | `401` | The client does not authenticate, or is a public client at the introspection endpoint. A client that tried the `Authorization` header is answered `WWW-Authenticate: Basic realm="<issuer>"` |
| `invalid_request` | `400` | The `token` parameter is missing, a parameter is repeated, the request cannot be read as a client authentication, or it carries a client certificate in a header |
| `unsupported_token_type` | `400` | At the revocation endpoint, an `at+jwt` that verifies |

Introspection never answers an error for a token that is not active: that is `{"active": false}`. Every
failed client authentication is an act, `client_authentication.failed`; [errors](errors.md) says what the
journal keeps of it.
