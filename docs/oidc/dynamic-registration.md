---
title: Dynamic registration
description: A client the provider has never seen, RFC 7591 and RFC 7592: closed by default, the three modes a tenant opens it in, what a registration may and may not ask for, and how a client reads, replaces and deletes itself.
---

# Dynamic registration

A client may register itself at `/register` (RFC 7591), and then read, replace and delete its own
registration at the URI it was handed (RFC 7592). Registration is closed by default: a tenant opens it by
naming a mode, which decides what authorises a registration. A client that registers itself is read by the
reader a [declared](clients.md) client is read by, under the same rules, and is held besides to what its
tenant offers.

## Opening it

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    client_registration:
        mode: initial_access_token
        default_scope: 'openid profile email'
        keep_a_client_unused_for: 7776000
        keep_a_client_never_used_for: 604800
```

| Option | Default | What it decides |
|---|---|---|
| `mode` | none | What authorises a registration: `initial_access_token`, `software_statement` or `open`. Left out, or empty, the tenant registers nobody and announces no registration endpoint |
| `default_scope` | none | What a client that names no `scope` is registered with (RFC 7591 §2). Left out, `openid` alone. It is held to what the tenant hands out like every registered scope, so a scope written here that the tenant does not offer refuses every registration that names no scope |
| `exempt_confidential_clients_from_pkce` | `false` | The confidential clients this policy registers are registered without the PKCE requirement. A public client is never exempted, and a challenge an exempted client sends is verified all the same |
| `keep_a_client_unused_for` | `7776000` | Seconds a client that was used may go unused before it is deleted, ninety days |
| `keep_a_client_never_used_for` | `604800` | Seconds a client that was never used lives at all, seven days |
| `statement_issuers` | none | The authorities whose software statements the tenant accepts, for the `software_statement` mode |
| `statement_max_lifetime` | `300` | Seconds ahead of the request the `exp` of a software statement may be |
| `statement_leeway` | `30` | Seconds allowed of the clock of an authority, both ways |
| `sector_identifier_timeout` | `3.0` | Seconds one read of a `sector_identifier_uri` is given, connection included |
| `sector_identifier_max_size` | `65536` | Bytes a `sector_identifier_uri` may answer before the read stops |

**Closed is the absence of the endpoint, not a mode that refuses.** A tenant that names no mode answers a
registration, a `POST` to `/register`, with a `404`, as it answers a path it does not serve, and its
discovery document has no `registration_endpoint`. A tenant that names a mode announces the endpoint, and its
endpoint answers. `/register` takes a `POST` and no other method, whether the tenant registers or not. A mode
nothing wired serves is a mistake of the deployment: the first registration fails on it, naming the modes
that are wired.

## The three modes

=== "An initial access token"

    `mode: initial_access_token` registers a client presented by an initial access token the tenant issued
    (RFC 7591 §1.2): a credential for the team that integrates, named, worth a number of registrations and
    no more, expiring, and revocable. It opens no other endpoint, carries no subject and no scope, and says
    one thing only: that whoever holds it may register a client with this tenant.

    ``` http
    POST /register HTTP/1.1
    Host: op.example.com
    Content-Type: application/json
    Authorization: Bearer 0NM8Z6ijkVrFDzEaMPwCLWmTvdFxNsRwBCzu8UxS4pQ

    {"client_name": "Billing", "redirect_uris": ["https://billing.example.com/oidc/callback"]}
    ```

    The token is spent in the request it authorises, before the metadata is read: a token worth one
    registration registers one, whether the registration that followed was written or refused. A token
    unknown, spent, expired or revoked is answered exactly as a request that carries none, so that whoever
    does not hold a token of this tenant learns nothing about the one they presented.

    ``` bash
    bin/console beffroi:client:token:issue 'Billing team' --registrations=1 --days=30
    bin/console beffroi:client:token:list
    bin/console beffroi:client:token:revoke 0192f1a4-6c1e-7b8a-9c3d-2e4f5a6b7c8d
    ```

    `beffroi:client:token:issue` prints the value once, and the provider keeps its SHA-256 and never the
    value: a token that was lost is replaced by issuing another. It is worth one registration and thirty days
    unless the command says otherwise, a day at least. `beffroi:client:token:list` shows what each token has
    served of what it is worth, and whether it still authorises anything. `beffroi:client:token:revoke`
    takes one back at once, and the clients it registered stay.

=== "A software statement"

    `mode: software_statement` registers a client presented by a statement an authority the tenant pins
    signed (RFC 7591 §2.3), in the `software_statement` member of the body. The provider issues nothing: the
    proof is the authority's, which is what lets a registration cross the boundary of an organisation.

    ``` yaml title="config/packages/beffroi.yaml"
    beffroi:
        client_registration:
            mode: software_statement
            statement_issuers:
                'https://authority.example.org':
                    jwks: '%env(json:AUTHORITY_JWKS)%'
                    signing_algorithms: ['ES256']
    ```

    An authority is keyed by the `iss` it signs with, an absolute URI compared byte for byte, and pins its
    public keys inline and the algorithms it signs with, among those the provider verifies. The key comes
    from this configuration and never from the statement: a key or a `jwks_uri` the statement names is never
    read (RFC 8725 §3.10). A tenant that pins no authority accepts no statement.

    The statement is verified before any of it is read as metadata. Its signature is checked against the
    keys of the authority its `iss` names, under one of the algorithms pinned for it. Its `aud` names the
    issuer of the tenant, once. Its `exp` is
    present, not past, and no further ahead than `statement_max_lifetime`. Its `iat` is present and not in
    the future. Its `jti` is present and never seen before, remembered until the `exp`, so one statement
    registers one client. RFC 7591 §2.3 asks none of this of a statement; the provider asks it of every
    signed thing it takes back. Whatever fails, the answer is the same `invalid_software_statement`.

    **What a statement says outranks what the client sent** (RFC 7591 §3.1.1): a member both carry is the
    statement's, so the registration is written with the `client_name` and the `logo_uri` the authority
    signed. A statement is held to what the tenant offers as a body is: one that names a scope, a grant or a
    method the tenant does not offer is refused with `invalid_client_metadata`, as a body naming it would be.
    The claims of RFC 7519 §4.1 of the statement describe the statement and are not metadata. A
    [replacement](#reading-replacing-and-deleting-itself) of the registration reads no statement.

    The statement is the credential of this mode, and it travels in the body: a body that is not a JSON
    object is refused with `invalid_client_metadata` before anything else is read, and a JSON object that
    carries no statement is answered `401`.

=== "Open"

    `mode: open` registers whoever asks, with no credential at all (RFC 7591 §1.3): nothing authorises, so
    nothing is read and nothing is refused before the metadata is, and everything else, the reader, the
    policy and the refusals, is the same. A credential presented anyway is read by nothing and spent by
    nothing.

    A client nobody vouched for chooses the name and the logo a person reads on the consent page, and a tenant
    that names this mode for its real users lets anybody write them. The standalone application writes a
    `client_registration` in its development environment alone, where the mode is `open` unless the
    environment names another, for the conformance suite to register its clients.

## The request

``` http
POST /register HTTP/1.1
Host: op.example.com
Content-Type: application/json
Authorization: Bearer 0NM8Z6ijkVrFDzEaMPwCLWmTvdFxNsRwBCzu8UxS4pQ

{
    "client_name": "Billing",
    "redirect_uris": ["https://billing.example.com/oidc/callback"],
    "token_endpoint_auth_method": "private_key_jwt",
    "jwks_uri": "https://billing.example.com/.well-known/jwks.json",
    "scope": "openid profile email"
}
```

The body is one JSON object whose members are the metadata of the client, the members [clients](clients.md)
lists, read by the same reader under the same rules. A body that is not a JSON object carries no metadata
and is refused with `invalid_client_metadata`: in the `initial_access_token` mode once the token has been
read, and in the `software_statement` mode before anything, the statement being in the body.

What a client may register is what the specifications define, and what the tenant offers:

- **The members this provider defines for itself are not a client's to send**: `requires_consent`,
  `requires_pkce`, `access_token_format`, `resources`, `token_exchange`, `may_act` and
  `require_sender_constrained_tokens` are exceptions and privileges. A body that carries one is refused, and a
  software statement does not grant one either: a client that registers itself never obtains them.
- **A member nobody reads is refused**, `client_id` and `client_secret` included: the provider draws both.
- **What a member names is one the provider is wired with**: a grant, a method, an algorithm, a mode of
  delivery, a kind of subject, a type of authorization detail.
- **A scope is one the tenant hands out**, the ones its discovery document lists in `scopes_supported`.
- **A `sector_identifier_uri` is proven**: the provider reads the document behind it once, with one `GET`,
  no redirect followed, within `sector_identifier_timeout` and `sector_identifier_max_size`, and the document
  is the JSON array of URIs of OIDC Registration §5 that lists every redirect URI of the client, or its
  `jwks_uri` when it registers no redirect URI (CIBA Core §4). A document that cannot be read, or that leaves
  one out, refuses the registration ([pairwise subjects](pairwise-subjects.md)).

What a client leaves out takes the defaults of RFC 7591 §2: the `authorization_code` grant alone, the `code`
response type that goes with it, and `client_secret_basic`. A scope left out is the `default_scope` of the
tenant, or `openid` alone. The registration policy writes beside the registration what it grants, the
default scope on a registration that named none and the PKCE exemption on a confidential client when the
tenant grants it, and that is read back before what the client sent, until the policy writes the
registration again.

## The answer

``` http
HTTP/1.1 201 Created
Content-Type: application/json
Cache-Control: no-cache, no-store
Pragma: no-cache

{
    "client_id": "s6Bh3dRkqt3Hm9vBkrnfeR7_xU2ZyQ4lJaN0cP8TwYg",
    "client_id_issued_at": 1793001600,
    "registration_access_token": "Yx9o3Wq1fPz7kL2mN8rT4vB6cD0eF5gH1jK3lM9nQ2s",
    "registration_client_uri": "https://op.example.com/register/s6Bh3dRkqt3Hm9vBkrnfeR7_xU2ZyQ4lJaN0cP8TwYg",
    "client_name": "Billing",
    "redirect_uris": ["https://billing.example.com/oidc/callback"],
    "token_endpoint_auth_method": "private_key_jwt",
    "jwks_uri": "https://billing.example.com/.well-known/jwks.json",
    "scope": "openid profile email"
}
```

The `client_id` is drawn by the provider, 256 random bits in base64url, and a client cannot choose it. When
the method the client registered proves a secret, `client_secret_basic`, `client_secret_post` or
`client_secret_jwt`, the answer also carries a `client_secret` drawn the same way and `client_secret_expires_at`
at `0`, which says the secret does not expire (RFC 7591 §3.2.1). The metadata follow, as the client sent
them, a member a statement signed standing in place of the one the client sent.

**A secret and a registration access token are said once.** The provider keeps a hash of the secret, or the
secret sealed for `client_secret_jwt`, and the SHA-256 of the token, and answers neither again: a read of the
registration carries neither.

The registration is written before the answer is sent, so the client leaves with an identifier that exists.

## Reading, replacing and deleting itself

The `registration_client_uri` answers the three methods of RFC 7592 §2, with the registration access token as
a bearer credential and no other:

| Request | Answer |
|---|---|
| `GET` | `200`, the registration as the provider holds it, without the secret and without the token |
| `PUT` | `200`, the registration replaced whole (RFC 7592 §2.2) |
| `DELETE` | `204`, and the client is gone |
| Another method | `405` |

**A replacement is whole and never a patch**: a member the request leaves out is a member the client no longer
registers. The replacement is read by the reader, under the policy of the tenant and the rules a registration
body is read under, so it names nothing a registration body could not; it is read from the request alone,
whatever the mode, with no statement in front of it. The request names the client in `client_id`, the one
the URI answers for; it carries none of `client_id_issued_at`, `client_secret_expires_at`,
`registration_access_token` and `registration_client_uri`, which the provider assigned; and a `client_secret`
it echoes is the one it holds.
What the provider assigned stays: the identifier, the date and the token, which is not rotated. The secret is
the one thing that may change: a client that registers a method proving a secret where it held none, or one
its kept secret does not suit, is handed a new one, said once, and a client that registers a method proving
none keeps no secret.

**A deleted client is gone at once**, with its token: a request that presents it afterwards is answered as a
token nobody holds. What the client was issued, consents, grants and refresh tokens, is left where it is and
can no longer be spent, since nothing resolves the client it names. The sessions of the people who used it are
not touched.

A token that reads no client, a value nobody was handed, one drawn for another client, a client of another
tenant or a client that deleted itself, is answered `401` with `invalid_token` and the same description, so
the endpoint tells nobody which clients exist. The credential is read before the body: an unreadable body
presented with a token that reads nothing is a `401`, not a `400`. These endpoints are not announced in the
discovery document: a client holds the URI it was handed.

## The clients nobody uses

A registered client carries the date it was last used, an authorization code issued for it or tokens issued
to it at the token endpoint, and the provider deletes the ones nobody uses any more, on a timed step that
runs every hour: a client used, but not for `keep_a_client_unused_for`, and a client never used and
registered more than `keep_a_client_never_used_for` ago. One run deletes a hundred clients at most, and the
next run takes the rest; what it deleted is written to the log. A tenant with no registration policy deletes
nothing, and a declared client is never deleted: it goes away with its block in the configuration.

Each deletion, by the step, by the client itself or by `beffroi:client:delete`, emits the same
`RegisteredClientDeleted` event.

## Refusals

| Answer | When |
|---|---|
| `404` | A registration, at a tenant that registers nobody |
| `401`, `invalid_token`, `WWW-Authenticate: Bearer` | Nothing the request presents authorises it: no token, or one that authorises nothing; no statement in the `software_statement` mode; no registration access token of this client at its URI |
| `400`, `invalid_client_metadata` | A member that does not hold, is not read, is not the client's to send, names what the provider or the tenant does not offer, or a body that is not a JSON object |
| `400`, `invalid_redirect_uri` | A value of `redirect_uris` or `post_logout_redirect_uris` that is not an address a client may register, or the redirect URIs and the grants disagreeing. Every other address, and the rule the loopback addresses of a public client follow, answer `invalid_client_metadata` |
| `400`, `invalid_software_statement` | A statement the tenant does not accept, whatever the reason |

What these endpoints answer themselves, a registration, a read, a replacement, a deletion and their
refusals, carries `Cache-Control: no-cache, no-store` and `Pragma: no-cache`. The description of a `400` is
the sentence of the refusal, in ASCII (RFC 7591 §3.2.2), the same sentence a deployment reads when a
declaration of the same member is refused.

[:beffroi-arrow-right: Clients](clients.md) and [pairwise subjects](pairwise-subjects.md)
