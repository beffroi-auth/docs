---
title: Interactions
description: What waits between an authorization request and its answer, what decides that a person sees a login or a consent page, and what a client learns of an interaction that did not finish.
---

# Interactions

An interaction is the part of an authorization request a person sees: signing in, proving one more factor,
agreeing to what a client asks. The authorization endpoint signs nobody in. Once a request is
[read](authorization-request.md), it decides whether anything is missing, and when something is, it parks
the request in an interaction and sends the browser to the page that asks for it. The page resumes the
interaction once it has its answer, and the same rules are applied again, until a code is issued or the
request is refused.

## The interaction

| What | Value |
|---|---|
| Its identifier | 256 random bits in base64url, in the query of the pages that serve it: `/login?interaction=...`, `/consent?interaction=...` |
| What it holds | The request as it was read, the language of its pages, and, once they are known, the session it goes on with and the consent it was given |
| How long it waits | Ten minutes from the request |
| Who may resume it | The browser that began it: the identifier is remembered in the HTTP session of that browser, which keeps the eight most recent ones, forgets the oldest first, and forgets one when it ends |
| How it ends | Once, with a code issued or a refusal, after which it cannot be resumed |

A page that names an interaction this browser did not begin answers `400`, saying no request is waiting for
it, and tells nobody whether the interaction exists: an identifier read in a log or taken from another
browser resumes nothing. The tabs of one browser share its session, so a person may finish an interaction in
another tab of the same browser.

Every page of an interaction belongs to the interaction plane. A process started with
`BEFFROI_PLANE=protocol` answers `404` to all of them, `/authorize` included, so a machine that serves only
the protocol never shows a login form ([routes and planes](../symfony-bundle/routes-and-planes.md)).

## What decides a login

With the request in hand and the session the browser holds, the questions are asked in this order, and the
first that answers sends the browser to the login page:

| | The request | The browser is sent to log in |
|---|---|---|
| 1 | Any | When it holds no session of this tenant, or one that has ended or expired |
| 2 | `id_token_hint` | When the `sub` of the hint is not the subject identifier of the account signed in |
| 3 | `acr_values` or `claims` asking for an `acr` | When the session satisfies none of the classes asked for, and a credential of this person would: a step-up |
| 4 | `prompt=login` | Always |
| 5 | `prompt=select_account` | Always: there is no account chooser, so it is a login again |
| 6 | `max_age` | When the authentication of the session is older than that many seconds |

A login made during this interaction answers questions 3 to 6, whatever it proved, so a person is not sent
round again for having signed in a moment ago. The login page says why it is shown: "Please sign in again to
continue." for a reason other than the absence of a session, and, for a step-up, that the client requires a
stronger sign-in than the one the person has, with the credentials they hold that would satisfy it, a passkey,
the password, or the password followed by a code. A login of the person already signed in adds what it
proved to the session the browser holds; a login of somebody else ends that session first.

The `id_token_hint` is compared with the subject identifier the account carries, which is the `sub` a client
of the `public` kind holds. An `id_token_hint` carrying the `sub` of a [pairwise](pairwise-subjects.md)
client never names the account signed in, so a request carrying one is sent to the login page every time.

### The class asked for

`acr_values` asks for a class of authentication voluntarily. A `claims` request of `acr` in `id_token`, with
`values` or `value`, asks for one too, and binds the provider when it says `"essential": true` (OIDC Core
§5.5.1.1). The second wins when both are sent. The classes are the ones of the [tenant](../core/tenants.md), and the ID
token carries in `acr` the first class asked for that the session satisfies, or the class of the session when
none was asked for or none is satisfied.

- **An essential request the provider cannot meet at all**, none of the classes asked for being one it can
  prove, a name the tenant does not declare or a class no login it is wired with produces, is refused before
  any page with `unmet_authentication_requirements` (OIDC Core §5.5.1.1).
- **An essential request this person cannot meet**, the session satisfying none of the classes and none of
  their credentials able to, is refused the same way, with no step-up page.
- **An essential request still unmet after the login** of the interaction is refused the same way.
- **A voluntary request is never refused**: when nothing satisfies it, the token carries the class the
  session has.

## What decides a consent

Once the login is settled, a client registered with `requires_consent: false` is answered at once. Any other
client is sent to the [consent page](consent.md) when the person has not agreed yet to every scope and every
authorization detail of the request, or when the request says `prompt=consent`. A consent given during the
interaction answers that, and the code is issued.

## `prompt=none`

`prompt=none` asks for an answer without any page (OIDC Core §3.1.2.6). Where a login would have been shown,
the client is answered `login_required`, and where a consent would have been, `consent_required`, both at its
redirect URI. `none` combined with any other value of `prompt` is refused with `invalid_request`.

## The login page

The login page names the client asking, by the name it registered, and offers what the tenant admits: a
password form, a passkey, or both, the floor of the logins of the tenant deciding
([tenants](../core/tenants.md)). A refused login says one thing whatever the reason, "Sign-in failed. Check
your username and your password, then try again.", so the page tells nobody which accounts exist.

**A `login_hint` is read one way, the one the deployment chooses**, and never searched for (OIDC Core
§3.1.2.1). What it names fills the username field with the name that person signs in with, unless this
browser has just typed another, and a hint that names nobody leaves the field empty, as a request without a
hint would: the value the client sent appears nowhere on the login form. The step of the address, on a
tenant that federates domains, below, is the exception: a hint that holds an `@` fills its field as the
client wrote it.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    interaction:
        login_hint: sub
```

| Value | What the hint is read as |
|---|---|
| `sub`, the default | The `sub` this provider issued to that client, read for that client, so a [pairwise](pairwise-subjects.md) identifier names somebody only to a client of its sector |
| `username` | The name the person signs in with |
| `none` | Nothing of the bundle: a deployment that names its users some other way tags a `UserHintInterface` of its own `beffroi.oidc.login_hint` |

`backchannel_authentication.login_hint` takes the same three names for the `login_hint` of the backchannel
flow ([backchannel authentication](grants/backchannel-authentication.md)). Reading a `sub` costs what it
costs: a client that holds one can learn the name its person signs in with by rendering the page itself, and
`none` is the setting that does not pay it.

**On a tenant that federates domains**, the login of an interaction asks for the address first, and an
address of a domain an upstream identity provider answers for is sent to that provider; a `login_hint` that is
such an address sends the browser there without showing the page. What the client asked of the login,
`prompt=login`, a `max_age` or a step-up, is asked of that provider in turn and checked against the instant
the person authenticated there: [signing in through an organisation](../saml/federated-sign-in.md) says how.

## The language of the pages

The language of an interaction is chosen at `/authorize`: the language of the record of a person already
signed in, then the one this browser asked for, then `ui_locales`, then `Accept-Language`, then the default
of the deployment, each read against the languages the deployment serves. It is kept on the interaction, so
every page of the same journey is read in it, and it is never written in a URL. A visitor who picks another
language with the control the pages carry changes the language of the interaction too, for the pages that
follow ([translations](../symfony-bundle/translations.md)).

## What a client learns of an interaction that did not finish

| What happened | The client | The person |
|---|---|---|
| The person refused on the consent page | `access_denied` at its redirect URI, with `state` and `iss` | Is sent back to the client |
| `prompt=none`, and a page was needed | `login_required` or `consent_required` at its redirect URI | Sees no page |
| An essential `acr` could not be met | `unmet_authentication_requirements` at its redirect URI | Sees no page, or is sent back after the login |
| The interaction waited more than ten minutes | Nothing | Reads a page, `400`, saying the request took too long; once the expired interaction has been purged, which a timed step does every hour, saying no request is waiting for it |
| The interaction had ended, a code issued or a refusal given | Nothing | Reads a page, `400`, saying no request is waiting for it: the browser forgot the interaction when it ended. A request already on its way when another ended it reads that the request was already answered |
| The page was reached from another browser, or without an interaction | Nothing | Reads a page, `400`, saying no request is waiting for it |
| The person left | Nothing | |

A page that answers a person rather than the client asks them to start again from the application: nothing
is sent to a redirect URI on behalf of somebody who is no longer there.

[:beffroi-arrow-right: Consent](consent.md) and [authorization request](authorization-request.md)
