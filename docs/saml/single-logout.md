---
title: Single logout
description: A logout a service provider asks for, the chain through which the provider tells every other service provider of a session, and what each of them can promise.
---

# Single logout

A session of the provider can be ended from either side. A service provider asks for it with a
`LogoutRequest`; or the session ends at the provider, and every service provider that signed in under it is
told. Both go through the browser, the front channel of the Single Logout profile over HTTP-Redirect and
HTTP-POST (SAML Profiles §4.4.3), at the single logout service of the tenant, `/saml/slo`.

## A logout a service provider asks for

**The request is the service provider's, signed.** A `LogoutRequest` is accepted from a declared service
provider whose accepted metadata list a single logout service it can be answered at, and only signed, in its
XML or over the query string of HTTP-Redirect, under the keys of its metadata (SAML Profiles §4.4.4.1). A
declaration that says its sign-on requests are unsigned relaxes nothing here, and no setting does. A request
that is refused ends nothing and gets no SAML answer: the browser is shown the page of a refusal.

**Accepted once.** The issuer and the `ID` of every request accepted are remembered until the window in which
it would be accepted again has closed, eight minutes at most, in one store every worker of the deployment
shares. The same request presented again ends nothing.

**The sessions it names, of the person it names.** A `SessionIndex` is the identifier of a session, the one
the assertion carried, and a request names up to sixteen. A session is ended only when its user is the
person of the `NameID`, a persistent identifier the provider computes again for that service provider and
compares, never one it looks up.

| The request | The status of the answer |
|---|---|
| Names sessions of that person, or sessions that have ended already, or that do not exist | `Success` |
| Names a session of another person | `Requester`, `UnknownPrincipal`, and no session of the request ends |
| Names no `SessionIndex` | `Requester`, `RequestUnsupported`, and nothing ends |

**The sessions end as every session ends**, at once and before the answer is written, since the answer says
whether they ended (SAML Core §3.7.3.2). The clients of OpenID Connect that signed in under them are told by
the back channel, their refresh tokens are revoked and their opaque access tokens removed, exactly as when
the session ends at the end session endpoint. The other service providers of the session are told through
the browser, in the chain below, before the one that asked is answered.

**The answer goes where the metadata say.** A signed `LogoutResponse`, to the first single logout service the
accepted metadata list on the binding the request came over, or else the first one listed, at its
`ResponseLocation` when it has one (SAML Metadata §2.2.2), never to an address the request carries. Its
`RelayState` is the one received, byte for byte, and its status says `PartialLogout` under `Success` when one
of the other service providers did not log out.

A key management service that does not answer when the signing key is opened ends nothing and answers
`503`: no session ends whose answer cannot be signed.

## The provider tells the others

The chain starts wherever a browser ends the session it holds:

- the end session endpoint of OpenID Connect, once it has ended the session (RP-Initiated Logout 1.0 §2);
- the sessions page of the account, when the session closed is the one of the browser reading it;
- the single logout service, when a service provider's request ended sessions.

``` mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant P as Beffroi
    participant S1 as Service provider 1
    participant S2 as Service provider 2
    B->>P: Ends the session
    P->>B: The front-channel logout page of the OpenID Connect clients
    P->>B: LogoutRequest for service provider 1
    B->>S1: LogoutRequest
    S1->>B: LogoutResponse
    B->>P: LogoutResponse
    P->>B: LogoutRequest for service provider 2
    B->>S2: LogoutRequest
    S2->>B: LogoutResponse
    B->>P: LogoutResponse, then where the logout ends
```

**The session has ended before the chain begins.** Whatever becomes of the chain, a service provider that
never answers or a browser closed half way, nothing of the provider stays open.

**The OpenID Connect clients first.** The browser is given the front-channel logout page of the ended
sessions, one frame per client that registered a `frontchannel_logout_uri` (Front-Channel Logout 1.0 §2),
and then goes on to the service providers.

**Every service provider of the session, but the one that asked**, session by session, in the order they
first signed in. Each is sent a signed `LogoutRequest`: a new `ID`, valid five minutes, the persistent
`NameID` computed again for it, one `SessionIndex`, and no `RelayState`, its answer being found by its
`InResponseTo`. It goes to the first single logout service of its metadata, read again when it is written.
Its `LogoutResponse` is read before the next one is told: signed, from that service provider, for that
request. A status other than `Success` is an answer and not a refusal, and the chain goes on.

**Passed over**, and counted as a service provider that did not log out: one the configuration no longer
declares, one whose metadata no longer read, one with no single logout service on HTTP-Redirect or
HTTP-POST, one whose request cannot be written.

**Kept by the provider, played once, by the browser that began it.** Where the chain stands is a row of the
provider and nothing the browser holds, since the session cookie no longer exists and an answer posted from
another site arrives without it. The row is bound to the browser that began the chain by a cookie of its
own, `__Host-beffroi_saml_logout`: `Secure`, `HttpOnly`, its path `/`, no `Domain`, `SameSite=None` because
an answer over HTTP-POST is a post from another site, and worth the ten minutes the chain stays open, renewed
at every step. A step presented without it, by the server of a service provider or by anybody who read a URL
in a log, moves nothing.

**Where it ends.** For a logout a service provider asked for, its `LogoutResponse`. For the end session
endpoint, the `post_logout_redirect_uri` with its `state`, as RP-Initiated Logout 1.0 §3 builds it, or the
page that says the browser is signed out. For the page of the account, that page.

A service provider that never answers holds the browser where it is: the chain closes ten minutes after its
last step, the service providers after it are not told, and the one that asked gets no answer. Nothing of the
provider is held open by it.

## What a logout can promise

**A session ended without its browser tells no service provider.** The console, the page of the account read
in another browser, closing every other session of an account, a new login that replaces a session: the
clients of OpenID Connect learn it by the back channel, and a service provider has no channel without the
browser, SOAP being out of scope.

**Every end of a session revokes what was issued under it**, whatever ended it: the refresh tokens of
OpenID Connect issued in the session are revoked and its opaque access tokens removed.

**The pages that start a chain name where it goes.** The confirmation page of the end session endpoint and
the sessions page of the account name, in their `form-action`, the origin of the single logout service each
service provider of the session would be told at. A browser checks that directive over every redirection of
a submission, and the chain is a series of them.
