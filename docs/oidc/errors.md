---
title: Errors
description: Which refusals go back to the client and which stay with the person, the shape of every answer, each error code and where it is answered, and what the journal keeps of a refusal.
---

# Errors

An error is either redirectable, and goes back to the client at a redirect URI that was validated first, or
it is not, and the person sees a page while the client learns nothing (RFC 9700 §4.1). Confusing the two is
how an open redirector is born, so which one an error is depends on where it was found, never on its code.

## Sent back, or shown

**The authorization endpoint reads a request in two stages.** The first establishes who is asking and where
an answer may go: the client, a request it had to push or sign and did not, the redirect URI compared byte
for byte, the request object or the pushed request the parameters are read from. A refusal there is a page,
since nothing says yet that the redirect URI belongs to the client. Everything after it is sent back to the
redirect URI (RFC 6749 §4.1.2.1), in the response mode the request asked for:

| Parameter | Value |
|---|---|
| `error` | The code |
| `error_description` | What the developer of the client needs to fix the request |
| `state` | The one the request carried, when it carried one |
| `iss` | The issuer, always (RFC 9207 §2) |

A request that asked for a signed response mode gets its refusal signed as it would have got its code (JARM
§2.1). A request that asked for a response mode the provider does not serve is refused with
`unsupported_response_mode` in the first mode the provider is wired with, `query` in the bundle, the only one
it is sure the client reads.

**The end session endpoint never redirects an error** (RP-Initiated Logout 1.0 §4): every refusal there is
a page. **Every other endpoint answers the caller directly**, a client or a resource server, and redirects
nothing anywhere.

## The shape of an answer

**The endpoints of the protocol** answer the JSON of RFC 6749 §5.2, with `Cache-Control: no-store` and
`Pragma: no-cache`: `/token`, `/par`, `/introspect`, `/revoke`, `/device_authorization` and
`/backchannel_authentication`.

``` json
{
    "error": "invalid_grant",
    "error_description": "The authorization code is invalid."
}
```

Two headers come with some refusals: `WWW-Authenticate: Basic realm="<issuer>"` with an `invalid_client` that
answers a client which tried the `Authorization` header (RFC 7235 §4.1), and `DPoP-Nonce` with a
`use_dpop_nonce` (RFC 9449 §8).

**UserInfo** answers with a challenge of RFC 6750 §3, the `WWW-Authenticate` header naming the scheme that
would have worked, and the same JSON as its body. [UserInfo](userinfo.md#refusals) lists them.

**The registration endpoints** answer the errors of RFC 7591 §3.2.2 with a `400`, and a `401` carrying a
`Bearer` challenge to a request that presents no credential they act on; `/register` answers `404` on a
tenant that registers no client. [Dynamic registration](dynamic-registration.md) says when.

**A page** shows the person a sentence for the code, translated, and the `error_description` under it as it
is, for whoever has to fix the client. Its status is the status of the error.

**Every `error_description` is a sentence of the provider**, in English and in ASCII without a double quote
or a backslash (RFC 6749 §5.2), never a message of an exception and never something the request chose. A
refusal that would tell a registered client from an unknown one, or a token that exists from one that does
not, reads the same whatever the cause: a client that names itself and does not prove it is told `Client
authentication failed.`, a code or a refresh token that grants nothing is told it is invalid, and an access
token refused because it was not issued here is told so and nothing more.

## The error codes

| Code | Status | Where | Sent back |
|---|---|---|---|
| `invalid_request` | `400` | Every endpoint: a parameter missing, repeated or of the wrong shape, a client authentication that cannot be read, a client certificate in a header | At the authorization endpoint, after the first stage |
| `invalid_client` | `401` | Every endpoint that authenticates a client, and the introspection endpoint for a public client | Never |
| `invalid_grant` | `400` | `/token`: what the grant presents, a code, a refresh token, a device code, a backchannel request, a token or an assertion, grants nothing | Never |
| `unauthorized_client` | `400` | `/token`, for a grant the client is not registered for; `/device_authorization` and `/backchannel_authentication`, for a client not registered for that flow | Never |
| `unsupported_grant_type` | `400` | `/token`, for a grant the provider is not wired with | Never |
| `invalid_scope` | `400` | `/authorize`, `/par`, `/token`, `/device_authorization`, `/backchannel_authentication` | At the authorization endpoint |
| `invalid_target` | `400` | `/authorize`, `/par`, `/token`, for a resource that is malformed or that the client did not register (RFC 8707 §2) | At the authorization endpoint |
| `invalid_authorization_details` | `400` | `/authorize`, `/par`, `/token` (RFC 9396 §5) | At the authorization endpoint |
| `unsupported_response_type` | `400` | `/authorize`, `/par`: anything but `code` | At the authorization endpoint |
| `unsupported_response_mode` | `400` | `/authorize`, `/par` | At the authorization endpoint, in the default mode |
| `access_denied` | `400` | `/authorize`, when the person refuses on the consent page or the identity provider of their organisation authenticated nobody; `/token`, when the person denied a device code or a backchannel request | At the authorization endpoint |
| `login_required` | `400` | `/authorize`, under `prompt=none`, when the person is not signed in as the request demands | Always |
| `consent_required` | `400` | `/authorize`, under `prompt=none`, when no consent covers the request | Always |
| `account_selection_required` | `400` | `/authorize`, when the request asks for an account to be selected, `prompt=select_account`, and the identity provider of the organisation, asked to authenticate again, answers for the person it already holds a session of (OIDC Core §3.1.2.6) | Always |
| `unmet_authentication_requirements` | `400` | `/authorize`, for an essential `acr` the provider cannot meet | Always |
| `invalid_request_object` | `400` | `/authorize` and `/par`, for a request object that cannot be read, is not signed as the client registered, or does not verify (RFC 9101 §6.3) | Never: a page at the authorization endpoint |
| `invalid_request_uri` | `400` | `/authorize`, for the `request_uri` of a pushed request that grants nothing, never issued, expired, already used or pushed by another client, all four alike; and for a `request_uri` the client did not register, or behind which no request object can be read | Never: a page |
| `authorization_pending`, `slow_down` | `400` | `/token`, while a device code or a backchannel request waits for its person (RFC 8628 §3.5, CIBA Core §11) | Never |
| `expired_token` | `400` | `/token`, for a device code or a backchannel request past its lifetime | Never |
| `invalid_binding_message` | `400` | `/backchannel_authentication` (CIBA Core §13) | Never |
| `invalid_dpop_proof` | `400`, or `401` at `/userinfo` | `/token`, `/par`, `/userinfo` (RFC 9449 §5, §7.1) | Never |
| `use_dpop_nonce` | `400`, or `401` at `/userinfo` | The same three, when the provider asks for a nonce (RFC 9449 §8) | Never |
| `invalid_token` | `401` | `/userinfo`; the registration endpoints, for an initial or a registration access token they do not act on | Never |
| `insufficient_scope` | `403` | `/userinfo`, for a token somebody signed in for whose scopes leave `openid` out | Never |
| `unsupported_token_type` | `400` | `/revoke`, for an `at+jwt` (RFC 7009 §2.2.1) | Never |
| `invalid_client_metadata`, `invalid_redirect_uri`, `invalid_software_statement` | `400` | The registration endpoints (RFC 7591 §3.2.2) | Never |

A redirected error reaches the client only once its redirect URI is established: the same code, found in the
first stage of an authorization request, is a page.

## The pages

The interaction plane answers what cannot go back to a client with the error page of the provider, which
carries one of the codes above or one of its own:

| Code | Status | When |
|---|---|---|
| `unknown_interaction` | `400` | A page of a sign-in reached with no request of this browser waiting for it |
| `interaction_expired` | `400` | The request took too long |
| `interaction_completed` | `400` | The request was already answered |
| `invalid_csrf_token` | `403` | A form posted without the form token of the page that served it |
| `login_required` | `401` | A page of the account reached without a session; the page offers the sign-in |
| `no_login_to_begin` | `404` | A third-party initiated login naming no client that can begin one (OIDC Core §4) |
| `too_many_requests` | `429` | A budget of load is spent, as below |

The sentence of each code tells the person what to do next, which is to start again from the application,
or to sign in for `login_required`. [Translations](../symfony-bundle/translations.md) says how those
sentences are replaced.

## Refused for load

Two budgets bound what the provider takes, and both always exist:

- **the budget of an address**, counted on every route of the bundle, both planes, before any work is done:
  before a session is opened, a password hashed, an assertion or a proof verified;
- **the budget of a client**, counted where its authentication succeeded, at the endpoints that
  authenticate a client. A public client proves nothing and is bounded by the budget of its address.

A request past either one is answered `429` (RFC 6585 §4) with `Retry-After`, the seconds before the window
has room again, and `Cache-Control: no-store`. On the protocol plane the body is JSON with an
`error_description` and no `error` member, since none of the registered codes says a budget is spent and a
client is not meant to act on it but to wait; on the interaction plane it is the page `too_many_requests`.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    load:
        origin:
            limit: 2400
            interval: 60
        client:
            limit: 1200
            interval: 60
```

| Option | Default | What it decides |
|---|---|---|
| `origin.limit`, `origin.interval` | `2400` requests in `60` seconds | What one address may send, whatever it asks for. It is not counted per tenant: it bounds the load on the machine |
| `client.limit`, `client.interval` | `1200` requests in `60` seconds | What one authenticated client of one tenant may ask |

A number too low on `/token` or on `/jwks` is an outage a deployment inflicts on itself, so a deployment
sets them from what its own clients send.

## What the journal keeps

Among the refusals of the protocol, these are acts of the journal:

| Refusal | Act | Whom the act names |
|---|---|---|
| A client that fails to authenticate, `invalid_client`, or `invalid_request` when the authentication cannot be read | `client_authentication.failed` | Nobody |
| The `request_uri` of a pushed request that grants nothing, `invalid_request_uri` | `pushed_request.refused` | Nobody |
| An authorization code presented a second time, `invalid_grant`; the tokens issued from it are revoked | `authorization_code.replayed` | The person |
| A rotated refresh token presented again, `invalid_grant`; its family is revoked | `refresh_token.reuse_detected` | The person and the client |
| A refresh token of a session that has ended and that the end has not revoked yet, `invalid_grant`. Once revoked, it is refused as any revoked token is, and that writes nothing | `refresh_token.outlived_its_session` | The person and the client |
| A budget spent, `429` | `load.budget_spent` | Nobody |
| A logout token its client refused | `logout_token.given_up` | The person and the client |

An act says which act it is, when it happened, the address and the user agent of the request with the place
derived from the address, and the person and the client it names; it does not say which check failed. The
other refusals of the protocol are answered, and leave nothing in the journal.
