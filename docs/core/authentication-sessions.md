---
title: Authentication sessions
description: What a person proved, when and from where, how a session is opened and proved again, and what ends it.
---

# Authentication sessions

A session records what was actually proven: which methods, when each one was proven last, from which address
and with which user agent. It is the session of the provider and not of a client: one sign-in serves every
client of OpenID Connect and every SAML service provider of the tenant the browser goes on to. A grant reads a
snapshot of it rather than the live session, which is what makes `auth_time`, `acr` and `amr` mean something
at the moment a token was issued and not at the moment it is read.

## What a session holds

| Field | What it holds |
|---|---|
| Proofs | Each method proven, a value of RFC 8176 §2 or `fed`, with the instant it was proven last |
| Opened at | When the login that opened it ended |
| Expires at | Twelve hours after it was opened, or earlier when an upstream identity provider allows less |
| Created from, last seen from | The provenance of the request that opened it and of the request of its last proof: when it was received, the address and the user agent, with the place of the address once it is found |
| Ended at, ended by | The first end, and who ended it |

The identifier of a session is a UUID. It is the `sid` of the ID tokens, logout tokens and self-contained
access tokens issued under it, and the `SessionIndex` of the SAML assertions written from it, so a logout
asked for by either protocol names the same session.

The proofs stay readable in the database, every token issued from the session carrying them anyway; the two
provenances are sealed under the data key of the tenant. The place of an address is looked up once the session
is opened, on the lane of the events, in the GeoLite2 databases of the deployment and nowhere else: a deployment
that holds none keeps an address and no place, and no login waits for it. A later proof writes its provenance as
it was received and asks for no lookup of its own.

## What it proved

`amr` (RFC 8176 §2) is the list of methods proven, with `mfa` beside them when two factors of different kinds
were proven, a knowledge, a possession or an inherence. Each kind of credential says what one authentication
with it proves:

| Login | Methods |
|---|---|
| A password | `pwd` |
| A password, then a code | `pwd` and `otp`, so `mfa` too |
| A passkey bound to its authenticator | `hwk`, `user`, and `mfa` when the authenticator verified the user |
| A synced passkey | `swk`, `user`, and `mfa` when the authenticator verified the user |
| A sign-in through an upstream identity provider | `fed`, and `pwd`, `sc` or `otp` when its class of authentication means exactly that method |

`fed` is not a value RFC 8176 registers: it is the one Microsoft Entra ID writes for a federated assertion.
[Signing in through an organisation](../saml/federated-sign-in.md#the-session) gives the classes that add a
method.

`auth_time` (OIDC Core §2) is the most recent proof. A session opened by an upstream identity provider dates its
proof with the `AuthnInstant` of the assertion, the instant the person authenticated there, and never later than
the moment the response arrived.

`acr` is never stored. A session satisfies every class of the [policy of its
tenant](tenants.md#the-classes-it-answers-with) whose predicate holds on its proofs, and when nothing asks for a
class in particular it answers with the first of them.

## Opening one

Every login that opens a session ends in the same place, whatever it proved: a password, a password followed by
a code, a passkey, an assertion of an upstream identity provider. That place opens the session, writes the act
`user.authenticated` to the journal of the person, and refuses what does not reach the [floor of the logins of
the tenant](tenants.md#the-floor-of-its-logins): proofs under it open nothing, wherever the login came from, and
the refusal is written as a refused login.

**A password alone does not sign in a person who holds a second factor.** When the person holds an active TOTP,
the password the login page verified opens nothing: the login is held in the HTTP session of the browser for
five minutes, and the code page asks for a code. A code accepted in time opens the session on `pwd` and `otp`,
both dated when the code was accepted; past the five minutes, the password is asked again before any code is
read.

**The browser is bound to it.** The HTTP session of the browser holds the identifier of the session, and its own
identifier is drawn again at that moment, so a session identifier planted in a browser before the login names
nothing afterwards. A browser whose session has ended or expired is treated as a browser that holds none.

## Proving again

A login on a browser that already holds a session of the same person opens no second session: its proofs are
added to the session the browser holds, the newest proof of a method replacing the older one, so `auth_time`
moves to that login and `amr` grows by what it proved. No `user.authenticated` is written for it, the act of the
credential it used being written as for any login. The expiry of the session is never extended by it, and a
sign-in through an upstream identity provider that allows less shortens it. A login of another person on a
browser that holds a session ends that session first, and opens a new one.

Something asks for that login:

- **A client**, with `prompt=login`, a `max_age` the last proof of the session exceeds, an `acr` the session does
  not satisfy and the person could reach, `prompt=select_account`, or an `id_token_hint` naming another person
  (OIDC Core §3.1.2.1). A login made during the interaction answers all of them, the hint excepted, which only
  a session of the person it names answers. With `prompt=none`, a request that needs a login is answered
  `login_required` instead (OIDC Core §3.1.2.6).
  [Authorization requests](../oidc/authorization-request.md) say how each is read.
- **A page of the account** that adds or takes away a way in, when the newest proof of the session is more than
  five minutes old. [The account pages](../symfony-bundle/account.md#what-a-page-asks-before-it-opens) list
  them.

## The snapshot a grant reads

When an authorization is granted, the session is read once: its `auth_time`, its `amr`, and the `acr` answered
to the request, which is the class the request asked for that the session satisfies, or the class the session
answers with when the request asked for none. Those three values are frozen into the grant, and every token that
descends from it carries them, the code, the refresh token, the access token and the ID token alike. A later
login on the same session moves the session, and never a token already issued.

## Ending one

| What ends it | Ended by |
|---|---|
| The end session endpoint, OIDC RP-Initiated Logout 1.0 | `relying_party` |
| A `LogoutRequest` of a SAML service provider | `relying_party` |
| Close, on the page of the sessions of the account | `user` |
| Close every other one, on the same page, which keeps the session reading it | `user` |
| A password replaced on the page of the account, which ends every other session of the person | `user` |
| `beffroi:user:revoke-session`, with the identifier `beffroi:user:sessions` lists | `user` |
| A login of another person on the same browser | `user` |

The first end wins, and a session that has ended authenticates nothing afterwards. The act `session.ended`
goes to the journal of the person.

**Every end revokes what was issued under it.** On the lane of the events, beside the back-channel logout that
tells the clients of the session ([logout](../oidc/logout.md)), its refresh tokens are revoked, rotated ones
included, and its opaque access tokens removed, the revocation dated by the end of the session and not by the
moment the lane reached it. The provider refuses every token of an ended session at its use, in the meantime
and afterwards: UserInfo and introspection refuse an access token whose session ended, and the token endpoint a
refresh token whose session ended, revoking again what a refresh in flight had saved. A resource server that
verifies a self-contained access token offline accepts it until it expires, ten minutes by default
(`beffroi.tokens.access_token_ttl`).

!!! note "Expiry is not an end"

    A session past its twelve hours signs nobody in and is not offered to the browser that held it, and no
    option changes that duration. Nothing is announced when it passes, though, and nothing is revoked: the
    refresh tokens and access tokens issued under it keep the lifetimes they were issued with. What has not
    been exchanged yet, an authorization code, a device code or a backchannel request, is refused at the token
    endpoint once its session has expired.

The row of a session, ended or not, is dropped by an hourly step once its expiry is older than the absolute
lifetime of a refresh token family plus the lifetime of an access token, ninety days and ten minutes with the
defaults: until then, a token issued under it can still be presented, and its session is what answers for it.
