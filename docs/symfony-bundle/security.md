---
title: Security
description: The firewalls an application declares, the four logins of the bundle, what a login opens, the attempts and budgets that bound it, and what a post from another site gets.
---

# Security

The bundle brings everything a firewall of Symfony is assembled from, the user provider, the user checker
and four authenticators, and the application declares the firewall itself. What the firewall authenticates
is a person of the provider, never the user of the host application, and what a login opens is the session
of the provider: it records what was proven, and it is not the login session of the host application.

## The firewalls

Besides the one of its development tools, the standalone application declares two firewalls: the protocol
endpoints, which authenticate their clients themselves and open no session, and the interaction pages, where
the logins of the provider live.

``` yaml title="config/packages/security.yaml"
security:
    providers:
        beffroi:
            id: Beffroi\Bundle\Security\IdentityUserProvider

    firewalls:
        dev:
            pattern: ^/(_profiler|_wdt|assets|build)/
            security: false
        beffroi_protocol:
            pattern: ^/(\.well-known/(openid-configuration|oauth-authorization-server)|jwks|token|userinfo|introspect|revoke|par|device_authorization|backchannel_authentication|register(/.+)?)$
            security: false
        beffroi_interaction:
            lazy: true
            provider: beffroi
            user_checker: Beffroi\Bundle\Security\UserChecker
            entry_point: Beffroi\Bundle\Security\PasswordLoginAuthenticator
            custom_authenticators:
                - Beffroi\Bundle\Security\PasswordLoginAuthenticator
                - Beffroi\Bundle\Security\PasskeyLoginAuthenticator
                - Beffroi\Bundle\Security\TotpLoginAuthenticator
                - Beffroi\Bundle\Security\UpstreamAssertionAuthenticator

    access_control: []
```

| Firewall | What it covers |
|---|---|
| `dev` | The profiler, its toolbar and the static assets of the application |
| `beffroi_protocol` | The paths its pattern lists: the discovery document and the RFC 8414 metadata, the JWK Set, and the token, UserInfo, introspection, revocation, pushed authorization, device authorization, backchannel authentication and registration endpoints. Nothing there reads a cookie or starts a session: a client authenticates at the endpoint, and a bearer token is checked by the endpoint that receives it |
| `beffroi_interaction` | Every other path: the pages a browser reads, where the four logins of the provider are, and the metadata of both SAML roles, `/saml/metadata`, `/saml/sp/metadata` and `/saml/sp/metadata/{identityProvider}`, which are routes of the protocol plane the pattern above does not list |

There is no `access_control`. The pages decide for themselves whether a session is needed: the login page
shows its form, the consent page sends a browser without a session to the login, and a page of the account
other than its home refuses one with `login_required`. A provider whose routes are mounted under a path
carries that path in the pattern of `beffroi_protocol`.

The password hasher of the users of the bundle is not the application's to declare: the bundle prepends
`Beffroi\Bundle\Security\CorePasswordHasher` for them, the hasher of the core, so that a password is hashed
and verified by one policy wherever it is read.

## The user the firewall sees

`IdentityUserProvider` loads a person of the tenant by the username typed, and refreshes them between two
requests by their identifier, so that a rename does not sign anybody out; a person gone, of another tenant or
disabled is not refreshed. What the firewall holds is a `SecurityUser`, with the role `ROLE_USER`, serialised
into the HTTP session as an identifier, a username, a state and a hash, the rows being read again at the next
request. `UserChecker` reads the state of the account after the proof and never before it, so a disabled
account answers like a wrong password.

## The four logins

| Authenticator | Reads | On | What it proves |
|---|---|---|---|
| `PasswordLoginAuthenticator` | `_username`, `_password` | `POST /login` | `pwd` |
| `PasskeyLoginAuthenticator` | `_passkey`, the assertion the page signed | `POST /login/passkey` | What the flags of the assertion say |
| `TotpLoginAuthenticator` | `_code`, a code of the authenticator application or a backup code | `POST /login/code` | What the first step proved, and `otp` |
| `UpstreamAssertionAuthenticator` | The response an upstream SAML identity provider posted, and its `RelayState` | `POST /saml/sp/acs` | `fed`, and the method its `AuthnContextClassRef` names exactly, when it names one |

The first three read the form token of the page, `_csrf_token` under the identifier `authenticate`. Each of
the four hands what it read to the use cases of the core, or of the SAML package for the fourth, where the
order of a login is written once. Symfony's form login is not wired: it would verify a hash the core has
verified.

**The password.** The form token is checked before the password reaches the core, so a form without its
token costs the person it names no attempt and no act in their journal, and an empty field is refused
without being counted. The core then asks whether the floor of the tenant reads anything a password proves,
names the person, counts the attempt, verifies the hash, refuses a disabled account and a person of a
[federated domain](../saml/federated-sign-in.md) after the password, empties the count, dates the credential
and rehashes it when the policy has moved, and announces the act. A name nobody holds, too many
attempts and a person who holds no password are refused at the cost of a hash all the same, so that the time
a refusal takes does not say whether the account exists. Whatever the reason, the page shows one message.

**The passkey.** The assertion is verified against the options this browser was handed for its ceremony, and
taken once. A passkey of another tenant, a revoked one, one whose backup eligibility is not what it was at the
enrolment, and the passkey of a person of a federated domain are refused after the signature is verified, so
that a refusal costs what an acceptance costs; a disabled account is refused by the user checker after them.

**The second step.** A password of a person who holds an active second factor opens nothing. It is held in
the HTTP session as a pending login for five minutes, the token the firewall had just set is dropped, and the
browser is sent to the code page. The code is verified by the core, which counts the attempt and accepts a
code once or spends a backup code; a refused code sends the browser back to the code page, the pending login
kept for another try within its five minutes, with the message of what was typed and never of why it was
refused.

**The assertion of an upstream identity provider.** It is read only for a request this browser remembers
under the `RelayState` it carries, and once. It needs no form token: what binds it to the browser is that
request, remembered in its HTTP session. It is held to the floor of the tenant before the person it names is
written, and the person is created at their first sign-in. A deployment that does not turn on the service
provider of SAML wires nothing behind it, and the authenticator takes no request.

[:beffroi-arrow-right: Signing in through an organisation](../saml/federated-sign-in.md)

**Where the browser goes next.** A login that succeeds sends the browser back to the login page of its
interaction, which resumes it, or to the page of the provider that asked for a login without being an
authorization request, such as the device page or a page of the account. A login that serves no
authorization request and whose password was found in a list of compromised passwords goes to the password
page of [the account](account.md) first. A password or a passkey that fails goes back to the login page,
never to the page that asked for it.

## What a login opens

**Opening a session is where the floor of the tenant holds.** A login whose proofs do not satisfy the
predicate the tenant requires of every login opens no session, whichever of the four it came through, and
the refusal is announced like every other. A session is opened for twelve hours, or until the end an upstream
identity provider sets with its `SessionNotOnOrAfter` when that comes first.

**A login of the person whose session the browser holds opens nothing.** The proofs it brings are recorded
on the session that browser holds, which moves its `auth_time` and leaves the tokens issued under it alone;
the check of the floor made when a session is opened is not made again there. A browser bound to the session
of somebody else ends that session first, then opens one for the person who signed in.

**The browser is bound to its session in the HTTP session.** The identifier of the HTTP session is
regenerated, and it then holds the identifier of the session of the provider under `_beffroi_session`, with
the interactions this browser began under `_beffroi_interactions`, eight at most, the oldest forgotten
first. Only the browser that began an interaction may resume it. The proofs are also copied into the token of
the firewall, one timestamp per method.

[:beffroi-arrow-right: Authentication sessions](../core/authentication-sessions.md)

## Attempts and budgets

Two limits bound a guess, and they are rules of the provider rather than settings: the bundle declares their
limiters itself and an application does not tune them.

| Limiter | What it counts | Bound |
|---|---|---|
| `beffroi_password_attempts` | The passwords tried on one person, counted once the person is named and before the hash is verified; a correct password empties the count | Five in a sliding window of one minute, per person |
| `beffroi_code_attempts` | The codes tried by one person: the code of an authenticator application or a backup code at `/login/code`, and the codes refused at `/device` | Five in a sliding window of one minute, per person |

The count is kept by person and by nothing else, never by address. The device page counts only the codes it
refuses, and answers `429` once the window is full.

Two budgets bound the load a deployment takes. Their existence is not configurable; their numbers are, under
`beffroi.load`, since they follow the size of a deployment.

| Budget | What it counts | Default |
|---|---|---|
| `origin` | Every request one client address sends to a route of either plane, before the firewall and before any work, whatever it asks for | `limit: 2400` requests in `interval: 60` seconds |
| `client` | Every request one authenticated client makes, per tenant, counted where its authentication succeeds | `limit: 1200` requests in `interval: 60` seconds |

A request refused for load answers `429 Too Many Requests` with a `Retry-After` and
`Cache-Control: no-store`: on the protocol plane, a JSON body that carries an `error_description` and no
`error`, since none of the registered values says that a budget is spent; on the interaction plane, the error
page with the code `too_many_requests`. The address a budget is counted on is the one Symfony reads behind the
proxies `framework.trusted_proxies` names, so a deployment behind a reverse proxy declares it, or every
request is counted under the address of the proxy.

## A post from another site

Under `SameSite=Lax`, a browser sends the session cookie with a top-level `GET` from another site and with no
`POST` from one. A page of another site that posts a browser to the provider therefore reaches it without the
session the browser holds, and two rules answer that. Both read where the post comes from in the
`Sec-Fetch-Site` header (Fetch Metadata Request Headers), so **a browser that does not send `Sec-Fetch-Site`
gets neither**: its post is served as it arrived, and the cookie of a session started for it is kept.

**The cookie of a new session is taken off the answer.** On every route of the interaction plane, a request
whose method is neither `GET` nor `HEAD`, whose `Sec-Fetch-Site` is `cross-site` and which carries no session
cookie is answered without the session cookie Symfony wrote for it. Otherwise the cookie of the session the
endpoint started would replace the one the browser holds, and sign it out of the provider.

**Five endpoints post the request again from the provider's own origin**, the second post carrying the
session cookie: `POST /authorize`, `POST /logout`, `POST /saml/sso`, `POST /saml/slo` and `POST /saml/sp/acs`.
They are the endpoints another site posts a browser to on purpose, and each asks before it reads anything, so
the first post spends nothing the second needs. The page that posts again is served when all of these hold:

- the body is a form, `application/x-www-form-urlencoded`;
- `Sec-Fetch-Site` is `cross-site` and the request carries no session cookie;
- every pair of the body would come back from a browser as it went: valid UTF-8, no control character, no
  carriage return or line feed outside a CR LF pair, and no pair named `_charset_` or named by nothing.

The body is posted again pair by pair, in its order, so the endpoint reads the second post as it would have
read the first. The action carries `_beffroi_posted_again=1` in its query, which no endpoint reads and which
decides nothing: the second post comes from the provider's own page, so no browser says it came from another
site, and that is what ends the loop. The page reads nothing of the HTTP session and starts none, speaks the
language the pages of the provider choose, the `ui_locales` of the posted body being read at the two
endpoints of OpenID Connect, submits itself with the one script its `Content-Security-Policy` names by its
hash, and keeps a button for a browser that runs no script.

At the assertion consumer service, a post from another site that cannot be posted again is refused as a
response that answers no request this browser remembers. A body that is not a form is refused with `415` at
the single sign-on, single logout and assertion consumer services.

## Form tokens

Every form a page of the provider renders carries a token, and a form that comes back without it is refused
with `403` and the error page `invalid_csrf_token`. At the three logins a missing token is a failed login
instead, and at the password form it costs no attempt. The names of the fields and the identifiers of the
tokens are what an overriding template keeps.

[:beffroi-arrow-right: What an override keeps](pages.md#what-an-override-keeps)
