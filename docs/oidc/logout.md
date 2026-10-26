---
title: Logout
description: A client asking for a session to end, the clients told through the browser and server to server, what ends a session, and what a logout can and cannot promise.
---

# Logout

Three specifications, and they are not interchangeable. RP-Initiated Logout 1.0 is a client asking for a
session to end; Front-Channel Logout 1.0 tells the other clients of that session through the browser; and
Back-Channel Logout 1.0 tells them server to server, with a signed logout token. A provider that implements
only the first one has not logged anybody out of anywhere else. The provider implements the three, and
announces them in its discovery document: `end_session_endpoint`, and `frontchannel_logout_supported`,
`frontchannel_logout_session_supported`, `backchannel_logout_supported` and
`backchannel_logout_session_supported` set to `true`.

## The end session endpoint

`GET` or `POST` at `/logout`, a page of the interaction plane (RP-Initiated Logout 1.0 §2). The parameters
are read from the query of a `GET` and from the form body of a `POST`.

| Parameter | What the provider does with it |
|---|---|
| `id_token_hint` | An ID token the provider issued: signed by a key the tenant publishes, its `iss` the issuer, a `sub`, and a `sid` when it carries one. Its `exp` is not read, a hint describing a session that may be long past. It names the client, by the first of its audiences that is a client of the tenant |
| `client_id` | The client, when the request names it. With a hint, it must be one of the audiences of the hint |
| `post_logout_redirect_uri` | Where the browser goes once the logout is done: one of the `post_logout_redirect_uris` the client registered, compared byte for byte (§3). It needs a client, named by the hint or by `client_id` |
| `state` | Given back with the redirection, printable ASCII |
| `ui_locales` | The language of the pages the browser is shown |
| `logout_hint` | Read as text without control characters, and carried to the confirmation page. It decides nothing |

**What is refused is a page, never a redirection** (§4): a hint that is not a signed compact JWT, or whose
audiences name no client of the tenant, a `client_id` the tenant does not know or that is not an audience of
the hint, a `post_logout_redirect_uri` the client did not register or that no client is named for, a parameter
of the wrong shape. The browser is shown the error page of the provider, status `400`, with the error
`invalid_request` and its description; nothing reaches the client.

**A hint the provider cannot verify is read as no hint.** A hint signed by a key the tenant no longer
publishes, or one that does not say what an ID token of the provider says, names no client: the person is
asked, and a `post_logout_redirect_uri` that only that hint could have justified is dropped rather than
refused (§6).

### What happens to the session

The session is the one the browser holds with the tenant.

- **No active session:** there is nothing to end. The browser is sent to the `post_logout_redirect_uri`
  with its `state`, or shown the page that says it is signed out.
- **A hint that proves the session:** its `sub`, read for the client the hint was issued to, names the person
  signed in, and its `sid` is the session the browser holds. The session ends at once, without a question. A
  client of [pairwise](pairwise-subjects.md) identifiers proves it with the identifier of its sector, as a
  client of public identifiers does with the subject the account carries.
- **Anything else:** no hint, a hint that could not be verified, a hint of another person or of nobody, a hint of another
  session or with no `sid`. The person is asked, on a page that names the client when one is named and the
  person signed in, with two buttons, *Sign out* and *Stay signed in*. The page posts the same parameters
  back with the answer and a form token; a form posted without a valid token is refused with a page, status
  `403`. *Stay signed in* ends nothing and sends the browser nowhere: the page says the person is still
  signed in and that nothing was changed.

**Once the session has ended**, the browser goes, in this order, through the
[front-channel logout page](#front-channel-logout) when a client of the session registered a
`frontchannel_logout_uri`, then through the SAML service providers that signed in under the session, as
[single logout](../saml/single-logout.md) describes, and lands at the `post_logout_redirect_uri` with its
`state` and no `iss`, which RFC 9207 gives authorization responses only, or on the page that says the browser
is signed out. When no client of the session registered a front-channel URI and no service provider signed
in under it, the browser goes straight there, with a `302` to the `post_logout_redirect_uri` when there is
one.

The confirmation page names, in its `form-action`, the origin of the `post_logout_redirect_uri` and of the
single logout service of each SAML service provider the chain would go to: a browser checks that directive
over every redirection of a submission.

**A request posted from another site** arrives without the session cookie, which is `SameSite=Lax`, and
would find no session to end. The provider posts it again from its own origin first, so that the session it
ends is the one the browser holds and the confirmation page is one the browser can answer. It reads where a
post comes from in `Sec-Fetch-Site`, and serves a browser that does not send it as the request came.

## Front-channel logout

Once a browser has ended its session, it is given a page that loads one frame per client of that session
that registered a `frontchannel_logout_uri` (Front-Channel Logout 1.0 §2, §3).

**The clients of a session** are the clients that exchanged an authorization code issued in it, each once,
in the order of the first code each was issued; a client no longer registered is skipped. The back channel
tells the same clients.

**The URI of each frame** is the one the client registered, with `iss` and `sid` added as query parameters
when the client registered `frontchannel_logout_session_required: true`, and as it is otherwise, §2 making the
two conditional.

**The page loads nothing but those frames.** Its `Content-Security-Policy` is `default-src 'none'`, with the
origins of the frames in `frame-src`, the one script of the page named by its hash in `script-src`, and
`form-action 'none'`, `base-uri 'none'` and `frame-ancestors 'none'`. It is served with `Cache-Control:
no-store`. The script moves the browser on once every frame has loaded or failed, and after three seconds at
the latest, since a logout has to end even when a client never answers; a browser that runs no script is
moved on after the same three seconds. With nowhere to go, the page has no script and says the browser may be
closed.

**What it can promise is what it says.** A frame of another origin reaches its client only if the browser
sends that client its cookies, and a browser that blocks third-party cookies does not. The page says the
provider asked the applications, those the browser let it reach were told, and the others sign the person
out when they are next used: it does not say the person is signed out everywhere. The back channel is what
does not depend on a browser.

## Back-channel logout

**Every session that ends is announced** to each client of that session that registered a
`backchannel_logout_uri`, with one logout token each (Back-Channel Logout 1.0 §2.6), whatever ended it: the
announcement is made on the end of the session, never on the request that asked for it.

### The logout token

A JWT signed by the active key of the tenant, under the algorithm the client registered for its ID tokens,
`id_token_signed_response_alg`, or the algorithm the provider signs with by default when it registered none,
since that is the one the client knows how to verify (§2.6). Its header names `typ: logout+jwt`, `alg` and
`kid`.

| Claim | Value |
|---|---|
| `iss` | The issuer |
| `sub` | The subject identifier the client knows the person by, public or pairwise, never the identifier of the account |
| `aud` | The client |
| `iat` | When the token was minted |
| `exp` | `iat` plus the budget of its delivery below, two hundred and thirty-five seconds by default |
| `jti` | A UUID drawn for this token |
| `events` | `{"http://schemas.openid.net/event/backchannel-logout": {}}` |
| `sid` | The session that ended, always, whether the client registered `backchannel_logout_session_required` or not |

It carries no `nonce`, which is how a client tells it from an ID token (§2.4). The key that signed it stays in
the JWK Set at least until that `exp`, so a client that receives the token late but in time can still verify
it ([discovery and JWKS](discovery-and-jwks.md)).

### Its delivery

The token is minted on the lane of the events once the session has ended, and carried to the client on the
lane of the notifications: a client that cannot be reached holds no logout back, and nothing a client does
reaches the person, whose session is already closed.

**One request per attempt:** a `POST` of `application/x-www-form-urlencoded` whose only parameter is
`logout_token` (§2.5), with no cookie and no authentication, read for its status code and nothing else. No
redirect is followed: the URI a client registered is where the token goes, and nobody else moves it.

| The client answers | What the provider does |
|---|---|
| A `2xx` status | Done |
| `400` or `501`, which §2.8 makes final | Gives up at once |
| A redirection | Gives up at once: the same answer would come back every time, and the provider follows none. The client registers the URL it redirects to instead |
| Any other status, or nothing within the timeout | Sends it again later, waiting longer each time and never more than `retry_max_delay` seconds |

A client that refuses the token is given up on, and that is said, never kept quiet: an act of the journal,
`logout_token.given_up`, naming the client and the person, so that somebody can see that a client was left
believing its user signed in.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    back_channel_logout:
        timeout: 5.0
        retries: 6
        retry_delay: 2
        retry_multiplier: 3
        retry_max_delay: 60
```

| Option | Default | What it decides |
|---|---|---|
| `timeout` | `5.0` | Seconds one attempt is given, connection included, `0.1` at least. A client that hangs holds no worker |
| `retries` | `6` | How many retries the budget of a delivery counts |
| `retry_delay` | `2` | Seconds before the first retry |
| `retry_multiplier` | `3` | What each wait is multiplied by to give the next one |
| `retry_max_delay` | `60` | Seconds a wait never exceeds |

These numbers make the budget a logout token is written for. With the defaults, the waits before the first
six retries are 2, 6, 18, 54, 60 and 60 seconds, and two hundred seconds of waiting plus five seconds for each
of the seven attempts they count make two hundred and thirty-five seconds. That budget is the `exp` of the
token, and the key that signed it stays in the JWK Set at least that long once it retires: changing one of
these numbers moves both.

**The budget bounds the token, not the sending.** A client still out of reach when the budget has run out
may be sent the token again, `retry_max_delay` seconds apart, and what it then receives is past its `exp`,
which a client refuses as it would an expired ID token (§2.6). A client that answers within the budget
receives a token it can act on; after it, it can only receive an expired one.

## What ends a session

A session ends:

- at the end session endpoint, as above;
- on [the pages of the account](../symfony-bundle/account.md), when its person ends it, ends every other
  session, or changes their password, which ends every other session;
- with `beffroi:user:revoke-session`, at the console;
- by a `LogoutRequest` of a SAML service provider, at the [single logout service](../saml/single-logout.md);
- when another person signs in on the browser that held it.

Each end is an act, `session.ended`, and each one is announced on the back channel. Only the ones a browser
ends itself, at the end session endpoint, on the page of the account for the session of that browser, and at
the single logout service, go through the front-channel page and the SAML service providers.

**A session that reaches its expiry is not ended.** It is no longer active, so an authorization code issued
under it and not exchanged yet is refused with `invalid_grant`. But nothing is announced to its clients, and
the access tokens and the refresh tokens issued under it keep their own lifetimes.

## Every end of a session revokes what was issued under it

However a session ends, the refresh tokens issued under it are revoked, rotated ones included, and its opaque
access tokens removed, on the lane of the events and dated by the end. The provider does not wait for that
lane to refuse them: it reads the session itself, so from the moment the session ended, UserInfo and
introspection refuse every access token of it, an `at+jwt` included by its `sid`, and the token endpoint
refuses its refresh tokens and its codes not exchanged yet with `invalid_grant`. A refresh token of the
session presented before the lane has revoked it is the act `refresh_token.outlived_its_session`, and so is a
successor a refresh in flight saved after that revocation, which is revoked in turn. Once revoked, a refresh
token is refused as any revoked token is, and that refusal writes nothing.

What the provider cannot reach is a self-contained access token in the hands of a resource server that
verifies it offline (RFC 9068 §4): it is accepted there until it expires, ten minutes after it was issued
unless `tokens.access_token_ttl` says otherwise. A resource server that has to know at once introspects, or
its clients are declared with opaque access tokens.

**A session is shared with SAML.** The session a client signed in under is the one the SAML service
providers of the browser signed in under too, which is why the end session endpoint goes through them before
it reaches the `post_logout_redirect_uri`, and why a `LogoutRequest` of a service provider ends the session of
the clients of OpenID Connect as well. [Single logout](../saml/single-logout.md) says how that chain is
played.

## What a client registers

| Member | What it is for |
|---|---|
| `post_logout_redirect_uris` | Where a logout may send the browser back to, compared byte for byte (RP-Initiated Logout 1.0 §3) |
| `frontchannel_logout_uri` | Loaded in a frame of the front-channel page when a session the client signed in under ends. HTTPS, or plain HTTP on a loopback host |
| `frontchannel_logout_session_required` | `iss` and `sid` added to that URI. It needs a `frontchannel_logout_uri`. Default `false` |
| `backchannel_logout_uri` | Where the logout token is posted. HTTPS, or plain HTTP on a loopback host |
| `backchannel_logout_session_required` | Whether the client reads the `sid` of the logout token, which is sent either way. It needs a `backchannel_logout_uri`. Default `false` |

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients:
        portal:
            # ...
            post_logout_redirect_uris: ['https://portal.example.com/signed-out']
            frontchannel_logout_uri: 'https://portal.example.com/logout/frontchannel'
            frontchannel_logout_session_required: true
            backchannel_logout_uri: 'https://portal.example.com/logout/backchannel'
```

## What a logout can promise

- **A session ended without its browser tells its clients only by the back channel.** The console, the page
  of the account read on another browser, the other sessions closed or a password changed, a new person
  signing in: no frame is loaded and no SAML service provider is told, SOAP being out of scope.
- **The front channel reaches the clients the browser lets it reach**, and says so.
- **A logout token is good for two hundred and thirty-five seconds by default**: a client the provider cannot
  reach within that time is left believing its user signed in, and a client that refuses the token is
  written down as given up on.
- **A self-contained access token outlives the session at a resource server that verifies it offline**, up
  to its expiry; the provider refuses it from the end of the session.
- **A session that expires is not a session that ends**: nothing is announced for it.
