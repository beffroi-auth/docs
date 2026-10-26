---
title: Grants
description: The seven grants of the token endpoint, what each one answers with, and what a client registers to use one.
---

# Grants

A grant is a way of obtaining tokens at the token endpoint, `POST /token` (RFC 6749 §3.2). The provider
serves seven, and a client uses the ones it registered in `grant_types` and no other.

| `grant_type` | What the client presents | Who the tokens are about | Page |
|---|---|---|---|
| `authorization_code` | The code a browser brought back to it | The person who signed in and agreed | [Authorization code](authorization-code.md) |
| `refresh_token` | A refresh token it was issued | The person of the authorization it renews | [Refresh token](refresh-token.md) |
| `client_credentials` | Its own authentication, and nothing else | Nobody: the client itself | [Client credentials](client-credentials.md) |
| `urn:ietf:params:oauth:grant-type:device_code` | The device code it is polling with | The person who confirmed the code on another device | [Device code](device-code.md) |
| `urn:openid:params:grant-type:ciba` | The `auth_req_id` of a backchannel request | The person who approved it on a page of the provider | [Backchannel authentication](backchannel-authentication.md) |
| `urn:ietf:params:oauth:grant-type:token-exchange` | An access token of this provider | Whoever that token is about | [Token exchange](token-exchange.md) |
| `urn:ietf:params:oauth:grant-type:jwt-bearer` | An assertion signed by an issuer the tenant trusts | The person the assertion names | [JWT bearer](jwt-bearer.md) |

No class serves the resource owner password credentials grant, and the authorization endpoint answers with a
code and nothing else, so there is no implicit flow either: a `grant_type` of `password` is answered
`unsupported_grant_type`, as every name the provider does not serve is. [Secure by
default](../../the-project/secure-by-default.md) says why neither exists.

## What the token endpoint does

The endpoint takes a `POST` of form parameters and answers in JSON, a success as an error, with
`Cache-Control: no-store` and `Pragma: no-cache`. It reads a request in this order and stops at the first
refusal:

1. **The client.** It authenticates with the one method it registered ([client
   authentication](../client-authentication.md)). A request whose authentication is malformed is
   `invalid_request`: credentials that cannot be read, two authentication mechanisms in one request, or a
   `client_id` that is not the one the credentials name. A client that does not prove who it is, or proves
   it with another method than the one it registered, is `invalid_client`.

2. **What the request binds its tokens to** (RFC 8705 §3, RFC 9449 §5):
    - the key of the DPoP proof the request carries;
    - the certificate of the TLS connection, for a client that authenticates with `tls_client_auth` or
      `self_signed_tls_client_auth`, or that registered `tls_client_certificate_bound_access_tokens`. A client
      that authenticates with a secret or an assertion and registered no such binding gets bearer tokens,
      whatever certificate its connection presented;
    - and nothing else: a request that would bind both a certificate and a key is refused with
      `invalid_dpop_proof`.

    A client registered with `require_sender_constrained_tokens` whose request binds nothing, and a client
    registered with `tls_client_certificate_bound_access_tokens` whose request presents no certificate, are
    refused with `invalid_request` before anything the request came to spend is read.

3. **The grant type.** `grant_type` is looked up among the grants the provider is wired with, and a name
   none of them gives itself is `unsupported_grant_type`.

4. **The registration.** A client that did not register that grant is `unauthorized_client`.

5. **The grant**, whose refusals are the errors of RFC 6749 §5.2 and of the specification it implements.

Of those errors, `invalid_client` is answered `401` and every other one `400`. A request refused because a
load budget is spent, that of the address it comes from or that of the client once it has authenticated, is
answered `429` with a `Retry-After` header and an `error_description`, and no `error` member.
[Sender-constrained tokens](../sender-constrained/index.md) says what a binding changes for the client that
holds the tokens.

### The answer

| Member | When it is there |
|---|---|
| `access_token` | Always |
| `token_type` | Always: `DPoP` for a token bound to a key, `Bearer` otherwise, a token bound to a certificate included (RFC 8705 §3) |
| `expires_in` | Always, the seconds the access token lives |
| `issued_token_type` | In the answer of a token exchange (RFC 8693 §2.2.1), and of no other grant |
| `refresh_token` | When the grant issued one |
| `id_token` | When `openid` is among the scopes of the answer and a person who signed in at this provider is behind it |
| `scope` | Always, the scopes the access token carries |
| `authorization_details` | When the authorization carries details beyond its scopes (RFC 9396 §7) |

## What each grant answers with

| Grant | ID token | Refresh token | A public client |
|---|---|---|---|
| Authorization code | With `openid` | When one is due | Served |
| Refresh token | With `openid` | Its successor, when the token rotates | Served |
| Client credentials | Never, `openid` being refused | Never | Refused at registration |
| Device code | With `openid` | When one is due | Served |
| Backchannel authentication | Always, `openid` being required | When one is due | Served |
| Token exchange | Never | Never | Its request fails: no token is issued |
| JWT bearer | Never, `openid` being refused | Never | Its request fails: no token is issued |

A refresh token is due when the client is registered for `refresh_token` and either `offline_access` is
among the scopes or the client is confidential. [Refresh token](refresh-token.md) says what spending one
does.

## What a registration carries

A client declared in the configuration that names no `grant_types` is registered for `authorization_code`
and `refresh_token`; a client that registers itself and names none is registered for `authorization_code`
alone, which is what RFC 7591 §2 gives it. What a client names is read against the grants the provider is
wired with, and against what each of them does:

- **A name no wired grant gives itself** is refused.
- **`refresh_token`** needs, beside it, a grant that issues refresh tokens: `authorization_code`, the device
  code grant or backchannel authentication.
- **`authorization_code`** needs at least one redirect URI. A client registered for no grant that sends a
  browser back to it registers no redirect URI and no `response_types`: a redirect URI nothing would ever
  use is refused.
- **`client_credentials`** needs an authentication method that proves something, so `none` is refused, and
  a `client_id` that can be a `sub`: one to 255 visible ASCII characters, and no space.
- **Token exchange** needs a `token_exchange` declaration, and a `token_exchange` declaration needs the
  grant. The `client_id` is held to the same rule as for `client_credentials`.

A declared client that breaks one of these rules is an error of the configuration, raised with the name of
the client as soon as the clients are read. A registration request that breaks one is answered
`invalid_redirect_uri` for the two rules on redirect URIs and `invalid_client_metadata` for the others.

One more condition is read at the endpoint and not at registration: a client of backchannel authentication
is served only once it registered a `backchannel_token_delivery_mode`, a member with no default. A client
registered for the grant without one is accepted, and refused at the backchannel authentication endpoint
with `unauthorized_client`. [Clients](../clients.md) has every other member of a registration.

## What is announced

`grant_types_supported`, in the [discovery document](../discovery-and-jwks.md), is the list of the wired
grants in the order they are wired, which is the order of the table at the top of this page. The members
that go with a grant follow it: the backchannel authentication endpoint and its metadata are announced only
while a grant of that flow is wired, and `offline_access` is offered only while a wired grant issues refresh
tokens and another spends them.

## Adding a grant

A grant is a class implementing `Beffroi\Oidc\Application\Token\GrantInterface`, tagged
`beffroi.oidc.grant`. It names its `grant_type`, and turns an authenticated client and the parameters of a
request into tokens or into an error of RFC 6749 §5.2. The token endpoint, the reading of a registration and
the discovery document read the one tagged list, so a grant added to the wiring is served, registrable and
announced, and a grant removed from it is none of the three. Two grants that give themselves the same name
are refused, and so is a token endpoint wired with none.

What a grant does beyond that is declared by the interfaces it implements beside `GrantInterface`, in the same
namespace, and never by a rule written about its name:

| Interface | What the grant declares | What it changes |
|---|---|---|
| `IssuesRefreshTokensInterface` | Its answer may carry a refresh token | The rule on `refresh_token`, and the offer of `offline_access` |
| `SpendsRefreshTokensInterface` | It spends a refresh token | Whether a refresh token is due, the rule on `refresh_token`, and the offer of `offline_access` |
| `SendsTheUserToTheClientInterface` | Its flow sends a browser back to the client | The rule on redirect URIs and response types |
| `ActsForTheClientItselfInterface` | Nobody is signed in behind it | The rule on public clients and on the `client_id` |
| `AsksTheUserOnAnotherDeviceInterface` | Its flow starts at the device authorization endpoint | That endpoint, which refuses a client of no such grant |
| `AsksTheUserThroughABackchannelInterface` | Its flow starts at the backchannel authentication endpoint | That endpoint, its metadata, and the audiences a client assertion may name |
| `ExchangesATokenInterface` | It takes a token and gives one back | The rule on `token_exchange` |
