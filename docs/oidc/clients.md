---
title: Clients
description: What a client is, the two places it comes from, every member it registers, and what the provider refuses when it reads one.
---

# Clients

A client is an application the provider answers, known by its `client_id`. It holds the addresses a browser
may be sent back to, the one method it authenticates with, the scopes and resources it may ask for, and how
it wants the documents written for it. A client comes from one of two places: the configuration of the
deployment declares it, or it registered itself at the [registration endpoint](dynamic-registration.md). Both
are read by the same reader under the same rules, so the same members mean the same thing wherever they were
written; the source decides what a member left out stands for, who may change the client and how it goes
away. A registration is held to two rules more, when it is written: the scopes it names are ones its tenant
hands out, and a `sector_identifier_uri` it names is backed by the document behind it ([pairwise
subjects](pairwise-subjects.md)).

## Declaring one

Clients a deployment knows in advance are declared under `beffroi.clients`, keyed by their `client_id`.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients:
        billing:
            client_name: 'Billing'
            logo_uri: 'https://billing.example.com/logo.svg'
            policy_uri: 'https://billing.example.com/privacy'
            redirect_uris: ['https://billing.example.com/oidc/callback']
            post_logout_redirect_uris: ['https://billing.example.com/']
            token_endpoint_auth_method: private_key_jwt
            jwks_uri: 'https://billing.example.com/.well-known/jwks.json'
            scope: 'openid profile email offline_access invoices.read'
            resources: ['https://api.example.com/']
```

The declarations are read as a whole, the first time the provider reads a client, and one that does not hold
together is refused there with the client and the rule it broke, before anything is served under it:
`bin/console beffroi:client:list` reads them, and is the quickest way to see a mistake. The same refusal
reaches a client that registers itself, as the `400` of RFC 7591 §3.2.2.

**What a member left out means depends on the source.** A declaration takes what an application that signs
a person in comes for; a client that registers itself takes what RFC 7591 §2 says it gets.

| Member | Declared and left out | Registered and left out |
|---|---|---|
| `grant_types` | `authorization_code` and `refresh_token` | `authorization_code` |
| `scope` | `openid profile email` | `openid`, or the default set the policy of the tenant names |
| `token_endpoint_auth_method` | The first method wired, `client_secret_basic` | `client_secret_basic` |
| `access_token_format` | The first shape wired, `jwt` | `jwt`, a client that registers itself never naming this member |
| `subject_type` | The first kind wired, `public` | The same |

**A secret is chosen by the deployment for a declared client, and drawn by the provider for a registered
one.** A declared `secret` is at least 32 visible ASCII characters (RFC 6749 appendix A.2), a value to
generate and put in an environment variable, never in the file. It is hashed with the password hasher of the
core the first time the client is looked up in a process, and kept as a hash, except for a client that
authenticates with `client_secret_jwt`: that method computes a MAC with the secret, so the provider keeps the
secret itself. A client registers a secret exactly when the method it registered proves one, and a
declaration that carries a secret for any other method is refused.

## What a client registers

Every member below is spelled the same in the configuration and in a registration request, under the name
RFC 7591 §2, OIDC Registration §2 or the specification of its feature gives it, the members marked
*deployment* being this provider's own. `secret` is written in the configuration alone, and `software_id`,
`software_version` and `software_statement` in a registration request alone: the configuration has no such
option and refuses it. A member this provider does not read is refused rather than ignored, and a value of the
wrong kind is refused rather than converted: a string where a list is expected, or `"true"` where a boolean
is.

The members marked *deployment* are written by whoever declares a client, or by the [registration
policy](dynamic-registration.md) of the tenant. They are exceptions to a rule, or privileges, and a client
that registers itself never obtains one: one in the body of its registration request is refused with
`invalid_client_metadata`, and a software statement does not grant one either.

### Who is asking

| Member | What it decides |
|---|---|
| `client_name` | The name the consent page shows. A client that registers none is shown under its `client_id` |
| `logo_uri` | The image the consent page shows. The browser of the person loads it from the client, with no referrer, and the provider never fetches it |
| `policy_uri`, `tos_uri`, `client_uri` | The pages the consent page links to, in that order |
| `contacts` | Ways to reach the people responsible for the client. No page shows them |

### Where a browser goes

| Member | What it decides |
|---|---|
| `redirect_uris` | Where the answer of the authorization endpoint may go, compared byte for byte with the `redirect_uri` of a request (RFC 6749 §3.1.2.3) |
| `post_logout_redirect_uris` | Where a browser may be sent after a logout, compared the same way |
| `initiate_login_uri` | Where the provider sends a browser to have this client begin a login (OIDC Core §4), from `/initiate-login?client_id=...`. HTTPS, on a loopback host as anywhere else |

### What it may ask for

| Member | What it decides |
|---|---|
| `grant_types` | The grants it may use at the token endpoint, among those the provider is wired with |
| `response_types` | `code`, and nothing else. It is not kept, the grants saying the same thing: a registration that names `code` without the grant that answers with one is refused |
| `scope` | The closed list of scopes it may ask for, space delimited (RFC 6749 §3.3). A scope outside it is `invalid_scope` |
| `resources` | *Deployment.* The resources it may ask an access token for (RFC 8707 §2). See [resources](resources.md) |
| `authorization_details_types` | The types of authorization detail it may ask for (RFC 9396 §2), among those the provider is wired with. See [authorization details](authorization-details.md) |

### How it proves who it is

| Member | What it decides |
|---|---|
| `token_endpoint_auth_method` | The one method it authenticates with, among those the provider is wired with. See [client authentication](client-authentication.md) |
| `secret` | Configuration only: the shared secret of a declared client whose method proves one |
| `jwks`, `jwks_uri` | Its public keys, inline or behind a URL, one or the other and never both. A symmetric key (`kty: oct`) is refused |
| `tls_client_auth_subject_dn`, `tls_client_auth_san_dns`, `tls_client_auth_san_uri`, `tls_client_auth_san_ip`, `tls_client_auth_san_email` | What names it in its certificate (RFC 8705 §2.1.2), exactly one of the five, for `tls_client_auth` and for no other method |

### How its requests are made

| Member | What it decides |
|---|---|
| `requires_pkce` | *Deployment.* `true` by default. `false` is accepted for a confidential client only, which may then send no `code_challenge`; a challenge it sends is verified all the same |
| `require_pushed_authorization_requests` | Its authorization requests are only read from a [pushed request](pushed-authorization-requests.md) (RFC 9126 §6) |
| `require_signed_request_object` | Its authorization requests are only read from a [request object](request-objects.md), whose signature is what `request_object_signing_alg` says, and its backchannel authentication requests only from an object it signed |
| `request_object_signing_alg` | The one algorithm its request objects are signed with, or `none` for unsigned objects. Left out, any algorithm the provider verifies, and never an unsigned object |
| `request_uris` | The URLs a request object of this client may be read back from, compared byte for byte, fragment included |

### What it receives

| Member | What it decides |
|---|---|
| `access_token_format` | *Deployment.* The shape of its access tokens: `jwt` or `opaque`. See [access tokens](tokens/access-tokens.md) |
| `require_sender_constrained_tokens` | *Deployment.* A token request that proves neither a certificate nor a key is refused with `invalid_request` rather than answered with bearer tokens |
| `tls_client_certificate_bound_access_tokens` | Its tokens are bound to the certificate of its connection whichever way it authenticated (RFC 8705 §3.4), and a token request that presents none is refused with `invalid_request` |
| `id_token_signed_response_alg` | The algorithm its ID tokens and logout tokens are signed with. Left out, `RS256`, the first algorithm wired |
| `id_token_encrypted_response_alg`, `id_token_encrypted_response_enc` | Its ID tokens encrypted to one of its keys once signed. The two go together, neither has a default |
| `userinfo_signed_response_alg` | Its UserInfo answer as a signed JWT (`application/jwt`). Left out, plain JSON |
| `userinfo_encrypted_response_alg`, `userinfo_encrypted_response_enc` | Its UserInfo answer encrypted to one of its keys |
| `authorization_signed_response_alg` | The algorithm of its [signed authorization responses](response-modes.md). Left out, `RS256` |
| `authorization_encrypted_response_alg`, `authorization_encrypted_response_enc` | Its signed authorization responses encrypted to one of its keys |
| `requires_consent` | *Deployment.* `true` by default. `false` names a first-party application, which no [consent page](consent.md) is shown for |

What encryption a client may register, and which of its keys a document is addressed to, is on [the page
about encryption](tokens/encryption.md).

### Who it sees

| Member | What it decides |
|---|---|
| `subject_type` | `public` or `pairwise`, the kind of `sub` it sees for a person (OIDC Core §8) |
| `sector_identifier_uri` | The sector its pairwise identifiers belong to. See [pairwise subjects](pairwise-subjects.md) |

### Logout, backchannel authentication and token exchange

| Member | What it decides |
|---|---|
| `backchannel_logout_uri`, `backchannel_logout_session_required` | Where a logout token is posted, and whether the client reads its `sid` (Back-Channel Logout 1.0 §2.2). See [logout](logout.md) |
| `frontchannel_logout_uri`, `frontchannel_logout_session_required` | The page loaded in a frame at a logout, and whether it receives `iss` and `sid` (Front-Channel Logout 1.0 §2) |
| `backchannel_token_delivery_mode` | `poll` or `ping`, for a client of the backchannel flow (CIBA Core §4). No default. See [backchannel authentication](grants/backchannel-authentication.md) |
| `backchannel_client_notification_endpoint` | Where the provider calls a `ping` client back. Required with `ping`, refused with another mode or with none |
| `token_exchange` | *Deployment.* For a client of the token exchange grant: `subject_token_types`, and `may_act_for_a_user`. See [token exchange](grants/token-exchange.md) |
| `may_act` | *Deployment.* Who may act for the subject of a token issued to this client (RFC 8693 §4.4) |

### What it says of its software

| Member | What it decides |
|---|---|
| `software_id`, `software_version` | Registration only: what the software the client is an instance of calls itself, and its version (RFC 7591 §2) |
| `software_statement` | Registration only: read by the registration mode that takes one, never as metadata. See [dynamic registration](dynamic-registration.md) |

## The addresses a client registers

Every URL a client registers, whatever the provider does with it, is held to one rule: an absolute URI, with
no fragment and no credentials, whose host is a name of letters, digits, hyphens and dots or an IP address,
in HTTPS. Plain HTTP is accepted on a loopback host only, `localhost`, a name under `.localhost`, an address
of `127.0.0.0/8` or `[::1]`. A custom scheme is not an address the provider sends anybody to, and is refused.

Three members depart from it, each for its own reason. `initiate_login_uri` is HTTPS on a loopback host too,
OIDC Registration §2 giving it no exception. `request_uris` may carry a fragment, which OIDC Core §6.2 gives
a meaning, and the URL is read back without it. `resources` are identifiers and never fetched, so a URN is a
resource as an HTTPS URL is (RFC 8707 §2). `tls_client_auth_san_uri` is no address either: it is the text a
certificate is compared with, and only has to be non-empty.

**A redirect URI matches byte for byte**, a trailing slash or a letter in another case included, and a
registered query is part of what matches. The one exception is the loopback redirection of a native
application (RFC 8252 §7.3), and it belongs to a **public** client only: a redirect URI registered in plain
HTTP on `127.0.0.1` or `[::1]` matches the same URI on any port, the path and the query compared byte for
byte. A public client therefore registers the loopback interface by its address and never by a name: plain
HTTP anywhere but on `127.0.0.1` and `[::1]` is refused for it (RFC 8252 §8.3). A confidential client keeps
the port it registered. The same holds for `post_logout_redirect_uris`.

## What a registration has to hold

Each rule below is checked where the client is read, so a declaration that breaks one is refused when the
declarations are read, and a registration that breaks one is refused with `invalid_client_metadata`. A
registration is refused with `invalid_redirect_uri` instead for a value of `redirect_uris` or
`post_logout_redirect_uris` that the rule of every address refuses, and for redirect URIs its grants do not
call for, or call for and lack; the rule a public client's loopback addresses follow answers
`invalid_client_metadata`, as every other one does.

- The `client_id` is printable ASCII with no space at either end (RFC 6749 appendix A.1). A client of
  `client_credentials` or of the token exchange is named where a subject is expected, the `sub` of its own
  tokens or the `act` of an exchanged one, so its identifier is 1 to 255 visible ASCII characters with no
  space at all (OIDC Core §2).
- The `client_name` is not empty, and neither is any of the `contacts`.
- A method that proves a shared secret has one, and any other method has none.
- `jwks` and `jwks_uri` are never both there. One of them is, for `private_key_jwt`,
  `self_signed_tls_client_auth`, a `request_object_signing_alg` naming an algorithm, and any encrypted
  response. An inline `jwks` holds a key every encryption the client registered can be addressed to.
- `tls_client_auth` comes with exactly one of the five certificate values, and every other method with none.
- The client is registered for at least one grant. `refresh_token` comes with a grant that issues one:
  `authorization_code`, the device code or the backchannel grant.
- A client of `authorization_code` registers at least one redirect URI, and a client of no grant that sends a
  browser back registers none, and no `response_types` either.
- `client_credentials` is refused to a public client, which proves nothing.
- The token exchange grant and the `token_exchange` member come together or not at all, and the token types
  it names are ones the provider reads.
- `requires_pkce: false` is refused to a public client.
- A client with `require_signed_request_object` (RFC 9101 §10.5) does not register
  `request_object_signing_alg: none`, the one value under which an unsigned request object is read.
- `backchannel_logout_session_required` needs a `backchannel_logout_uri`, and
  `frontchannel_logout_session_required` a `frontchannel_logout_uri`.
- An encryption names its `alg` and its `enc` together. OIDC Registration §2 would default the `enc` to
  `A128CBC-HS256`, which the provider is not wired with, so it takes no default.
- A `pairwise` client has a sector: its `sector_identifier_uri`, its redirect URIs all on one host, or, when
  it registers no redirect URI, its `jwks_uri`.
- Every name is one the provider is wired with: a grant, a method, an algorithm, an access token shape, a
  delivery mode, a kind of subject, a type of authorization detail. The refusal lists the wired names.

## Public and confidential

A client is **public** when it registered `token_endpoint_auth_method: none`: it names itself and proves
nothing, as a native or a browser application cannot keep a secret. Everything else is **confidential**.
What protects the code of a public client is PKCE, which is mandatory for it, and the exact redirect URI.
Besides the loopback exception above, the difference shows where a rule asks for a client that proves
itself: `requires_pkce: false` and `client_credentials` are refused to a public client at its registration,
the [introspection endpoint](introspection-and-revocation.md) refuses it, and a refresh token reaches it only
when it asks for `offline_access` ([refresh tokens](tokens/refresh-tokens.md)).

## Reading what exists

``` bash
bin/console beffroi:client:list
bin/console beffroi:client:show billing
bin/console beffroi:client:delete 3x4mpl3Cl13nt1d3nt1f13rDr4wnByTh3Pr0v1d3rXX
```

`beffroi:client:list` prints every client of the tenant with its name and its source, `configuration` or
`registration`, and for a registered client when it registered and when it was last used.
`beffroi:client:show` prints the same for one client, and for a registered one the members it registered and
the ones the registration policy of the tenant wrote on it; for a declared one it points at the
configuration, which is the whole of what it is. `beffroi:client:delete` deletes a client that registered
itself, and refuses a declared one, which goes away with its block in the configuration.

A registered client whose stored registration the reader refuses, a row naming a member this version does not
read or breaking a rule it holds, is answered as no client at all, and the reason is written to the log as an
error.

[:beffroi-arrow-right: Client authentication](client-authentication.md) and [dynamic
registration](dynamic-registration.md)
