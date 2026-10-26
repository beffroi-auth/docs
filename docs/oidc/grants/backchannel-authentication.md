---
title: Backchannel authentication
description: CIBA Core 1.0, the client names a person, the person approves on a page of the provider, and the client polls or is pinged for the tokens.
---

# Backchannel authentication

In Client-Initiated Backchannel Authentication (CIBA Core 1.0) the client has no browser anywhere in the
flow, and the device that asks is not the one that answers. The client names the person it wants
authenticated, the provider lets that person know, the person approves on a page of the provider they
already know, and the client collects the tokens at the token endpoint, by polling or once the provider has
pinged it.

``` mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant P as Beffroi
    participant U as The person
    C->>P: POST /backchannel_authentication, naming the person
    P->>C: auth_req_id, expires_in, interval
    P-->>U: A notification, on the channels the deployment wired
    U->>P: /account/approvals, signed in: Allow
    P-->>C: A ping, in ping mode
    C->>P: POST /token with the auth_req_id
    P->>C: Access token, ID token, refresh token
```

## Registering a client

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients:
        branch-terminal:
            client_name: 'Branch terminal'
            token_endpoint_auth_method: private_key_jwt
            jwks_uri: 'https://terminal.example.com/jwks.json'
            grant_types: ['urn:openid:params:grant-type:ciba', refresh_token]
            scope: 'openid profile'
            backchannel_token_delivery_mode: ping
            backchannel_client_notification_endpoint: 'https://terminal.example.com/ciba/notify'
```

| Member | What it decides |
|---|---|
| `grant_types` | `urn:openid:params:grant-type:ciba`, with `refresh_token` beside it for a client that renews |
| `backchannel_token_delivery_mode` | `poll` or `ping` (CIBA Core §4), the two modes the provider is wired with. It has no default: a client that registered none is refused at the backchannel authentication endpoint with `unauthorized_client`, so that a client of another flow never becomes a client of this one by accident |
| `backchannel_client_notification_endpoint` | Where the provider pings the client (CIBA Core §10.2): required with `ping` and refused without it. HTTPS, or plain HTTP on a loopback host |
| `require_signed_request_object` | Every request of this client is a request object it signed, as FAPI-CIBA §5.2.2 asks: an unsigned one is `invalid_request` |

A client of this flow registers no redirect URI, nothing of it sending a browser to the client, and one is
refused unless the client is also registered for `authorization_code`. Push mode, where the tokens
themselves are sent to the client (CIBA Core §10.3), is not served: the token endpoint is the one place this
provider hands out a token.

Two rules follow from registering the grant. A client that authenticates with an assertion, `private_key_jwt`
or `client_secret_jwt`, may name in its `aud` the issuer, the URL of the token endpoint or the URL of the
backchannel authentication endpoint, the three CIBA Core §7.1 lets it choose from, and those URLs on the host
that asks for a certificate when the deployment serves one; a client of no backchannel grant names the issuer
alone. And a client that takes [pairwise subjects](../pairwise-subjects.md), registers no redirect URI and no
`sector_identifier_uri` is of the sector of the host of its `jwks_uri` (CIBA Core §4).

## The request

`POST /backchannel_authentication` (CIBA Core §7.1). The client authenticates exactly as at the token
endpoint, then:

| Parameter | |
|---|---|
| `scope` | Required, `openid` among the scopes, every one of them registered. There is no default: what the person is shown is what the request named |
| `login_hint`, `id_token_hint`, `login_hint_token` | Exactly one of the three, naming the person: [below](#naming-the-person) |
| `binding_message` | Optional: shown to the person beside the name of the client, at most 64 characters of letters and their marks, digits, spaces, currency signs and the punctuation `. , : ; ! ? ( ) [ ] @ # % + * / = _ -` |
| `acr_values` | Optional: the classes the client would like the authentication to reach, in its order of preference |
| `requested_expiry` | Optional: a positive number of seconds the request should live. More than the ceiling is served the ceiling, not refused |
| `client_notification_token` | Required of a `ping` client and refused from a `poll` one: what the provider presents when it pings, a bearer token (RFC 6750 §2.1) of 22 to 1024 characters |
| `resource` | Optional and repeatable, among the resources the client registered (RFC 8707 §2) |
| `user_code` | Refused: the provider takes none, and says so in `backchannel_user_code_parameter_supported` |
| `request` or `request_uri` | The request as a signed request object (CIBA Core §7.1.1), whose parameters are then the request |

A signed request object is read and verified as at the authorization endpoint ([request
objects](../request-objects.md)), and it carries an `iat` and a `jti` besides: the `jti` is remembered until
the `exp` of the object, so that one signed request is made once.

| Refusal | Error |
|---|---|
| The client is not registered for the grant, or registered no delivery mode | `unauthorized_client` |
| No `scope` | `invalid_request` |
| No `openid` in it, a scope the client did not register, or a `scope` that is not a list of scope tokens | `invalid_scope` |
| A resource the client did not register, or one that is not an absolute URI without a fragment | `invalid_target` |
| A `binding_message` the person could not be shown as it was sent | `invalid_binding_message` |
| No hint or several, a hint the provider does not read, an `acr_values` that is not a space-separated list of classes, a `user_code`, a `requested_expiry` that is not a positive number of seconds | `invalid_request` |
| A `client_notification_token` missing from a `ping` client, sent by a `poll` one, or not a bearer token of 22 to 1024 characters | `invalid_request` |
| A `request` and a `request_uri` together, a request object that cannot be read or verified, an unsigned one from a client that requires a signed one, a signed one without `iat` or `jti`, or one whose `jti` was used already | `invalid_request` |
| A `request_uri` the client did not register, or whose object cannot be read back | `invalid_request_uri` |

A request object this endpoint will not read is `invalid_request`, and not the `invalid_request_object` of the
authorization endpoint: CIBA Core §13 does not name that error.

### The answer

``` json
{
    "auth_req_id": "1bMVbP0yKpXLzwWWE8VgXGDxeQOCX3Bz6DkWnAAgiKM",
    "expires_in": 300,
    "interval": 5
}
```

`200`, never cached (`Cache-Control: no-store`, CIBA Core §7.3). The `auth_req_id` is 256 random bits in
base64url, 43 characters, of which the provider keeps the SHA-256 and, for a `ping` client only, the value
itself sealed by the key management service of the tenant, together with the `client_notification_token`,
since it has to present both when it pings.

| Option | Default | At most | What it is |
|---|---|---|---|
| `tokens.backchannel_authentication_ttl` | `300` seconds | `3600` | How long a request lives when it asks for no `requested_expiry`, never longer than the option below |
| `tokens.backchannel_authentication_max_requested_expiry` | `1800` seconds | `3600` | The longest a request lives, whatever it asks for |
| `tokens.backchannel_authentication_interval` | `5` seconds | `30` | How long the client waits between two polls |

## Naming the person

| Hint | How it is read |
|---|---|
| `login_hint` | As `backchannel_authentication.login_hint` says, below |
| `id_token_hint` | An ID token this provider issued to this very client, whose `sub` names the person; its `exp` is not looked at, a hint describing a past sign-in being the ordinary case. A token of another issuer, or issued to another client, is `invalid_request` |
| `login_hint_token` | Read by nothing the bundle wires, so `invalid_request` |

| `login_hint` | What the hint is |
|---|---|
| `sub`, the default | The subject this provider gives the person for this client, public or pairwise |
| `username` | The name the person signs in with |
| `none` | Nothing the bundle reads: the deployment tags a reader of its own, and without one a `login_hint` is `invalid_request` |

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    backchannel_authentication:
        login_hint: sub
```

CIBA Core §15 asks for an identifier that says nothing outside this provider, which the subject is and a
username is not, hence the default. A reader of its own is a class implementing
`Beffroi\Oidc\Application\Hint\UserHintInterface`, tagged `beffroi.oidc.ciba_user_hint`; two readers of the
same parameter are refused, a parameter being read one way. The `login_hint` of an authorization request,
read on the login page, is set apart with `interaction.login_hint`, which takes the same three values.

**Nobody is told whether the person exists.** A hint that names nobody is answered with an `auth_req_id` like
any other, and the request then goes the way of every request nobody answers, to `expired_token`. CIBA Core
§13 defines `unknown_user_id` for that case, and the provider never answers it: a client that names a
stranger learns exactly what a client that names somebody who never answers learns. The hints are read last,
after every other parameter, so that a request refused for anything else has looked nobody up.

## Reaching the person

When the hint named somebody, the provider puts the word on the [notifications
lane](../../symfony-bundle/messenger.md) and answers the client without waiting for it. What travels is the
name of the provider, the name of the client, the binding message when there is one, the expiry, and the
address of the page where requests are answered. It carries no identifier of the request and no link that
answers one, so that nothing reaching the person from outside can carry them to an approval.

What carries it to the person is a channel the deployment wires: a class implementing
`Beffroi\Bundle\Ciba\PendingApprovalChannelInterface`, tagged `beffroi.pending_approval_channel`. The bundle
ships one, [web push](../../symfony-bundle/web-push.md) to the browsers the person subscribed on the
notifications page of their account, wired when `web_push.subject` is set. A deployment that wires no channel
still serves this flow: the person finds the request on the page where requests are answered, which is where
any channel sends them anyway.

## Answering: `/account/approvals`

The page is "Requests waiting for you", the first card of the [account pages](../../symfony-bundle/account.md).
The person signs in first, then sees the requests made for them that are still waiting, oldest first, and
nothing else: there is no code to type and no link that carries a request, the requests being found by who
is signed in. Each one shows the provider that is asking, the client, its binding message, where the request
came from, by its address and what its user agent says, every scope of the request, and a warning that
whoever did not start it refuses it.

- **Allow and Refuse** are a `POST` with the form token of the page, naming the request by a handle of that
  very list. A request that was answered, has expired or was never this person's is not answerable, and the
  page says that nothing is waiting there any more, answered `400`.
- **A class the client asked for** with `acr_values` that the session proves none of, when a credential of
  the person would, sends them to the login of the provider for one more proof, and back to the page to
  answer. A class nothing of theirs could ever reach is asked of nobody: the request is approved with the
  class the session has, and the `acr` of the tokens says it.
- **Allowing** records a consent to those scopes for that client, as the consent page of a browser flow does,
  and freezes on the request the session and what it had proven. The `acr` of every token of the request is
  the first class the client asked for that the session satisfies, or the class the session has.
- **Refusing** ends the request, and the client learns `access_denied`.

## The ping

In `ping` mode, once the person has answered either way, the provider tells the client so at its
`backchannel_client_notification_endpoint` (CIBA Core §10.2):

``` http
POST /ciba/notify HTTP/1.1
Host: terminal.example.com
Authorization: Bearer <the client_notification_token of the request>
Content-Type: application/json

{"auth_req_id": "1bMVbP0yKpXLzwWWE8VgXGDxeQOCX3Bz6DkWnAAgiKM"}
```

- **No token travels there.** The ping says there is something to collect, and the client collects it at the
  token endpoint.
- **It leaves on the notifications lane**, never in the request of the person, with no cookie and no
  redirect followed. Each call is given `backchannel_authentication.client_notification_timeout` seconds,
  `3.0` by default, connection included.
- **A `2xx` is done.** A redirection and a `400`, `401`, `403`, `404`, `405` or `501` are given up at once, the
  same answer coming back at every try. Any other answer, or none, is tried again under the retry policy of
  the lane.
- **A client that cannot be reached holds nothing up**: it finds the same answer by polling.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    backchannel_authentication:
        client_notification_timeout: 3.0
```

## Collecting the tokens

The client sends `POST /token` with `grant_type=urn:openid:params:grant-type:ciba` and the `auth_req_id`
(CIBA Core §10.1), in either mode. The answers come in the order the client can act on them (CIBA Core §11):

| Answer | When |
|---|---|
| `invalid_grant` | The `auth_req_id` is unknown, or was issued to another client |
| `expired_token` | The request is past its lifetime: the client starts a new one |
| `access_denied` | The person refused |
| `slow_down` | Nobody has answered yet, and the client polled sooner than its interval allows: the interval grows by five seconds, for this request and for every poll after it |
| `authorization_pending` | Nobody has answered yet |
| `invalid_grant` | The person allowed, and the `auth_req_id` was spent already, or the session they allowed with has ended or is past its expiry |
| The tokens | The person allowed |

Every poll is recorded, the refused ones included, and a request that has an answer is answered however soon
it is asked, which is what a `ping` client needs, the ping coming sooner than its interval. The `auth_req_id`
is spent once, atomically.

The tokens are those of an ordinary authorization, descending from the session the person approved with: an
access token addressed to the resources of the request, or to the client itself when it named none; an ID
token, always, `openid` being required of the request, without a `nonce`; and a refresh token when one is
due. They are bound to what the token request binds them to ([grants](index.md#what-the-token-endpoint-does)),
never to anything the browser that approved proved.

## What is announced

While a grant of this flow is wired, the [discovery document](../discovery-and-jwks.md) carries:

| Member | Value |
|---|---|
| `backchannel_authentication_endpoint` | `/backchannel_authentication` under the issuer |
| `backchannel_token_delivery_modes_supported` | `poll` and `ping` |
| `backchannel_authentication_request_signing_alg_values_supported` | The algorithms the provider verifies a signature with |
| `backchannel_user_code_parameter_supported` | `false` |
