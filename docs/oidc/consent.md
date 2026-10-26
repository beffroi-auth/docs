---
title: Consent
description: When a person is asked what a client may obtain, what the consent page shows, what a consent holds, and what taking one back takes away.
---

# Consent

A consent is what a person agreed to let one client obtain about them: a set of scopes, and the
[authorization details](authorization-details.md) the client asked for beyond them. It is recorded once per
person and client, and a request that asks for no more than it covers is answered without asking again. A
person reads their consents and takes any of them back from [the pages of their
account](../symfony-bundle/account.md), and an operator does the same at the console.

## When a person is asked

The question is asked during an [interaction](interactions.md), once the person is signed in:

- **A client registered with `requires_consent: false`** is never asked about, `prompt=consent` included. It
  is the first-party application of the deployment, and only a declaration names one: a client that
  registers itself never obtains the member.
- **Any other client** is asked about when no consent of this person is in force for it, when the one in
  force does not cover every scope of the request, or every authorization detail of it, and whenever the
  request says `prompt=consent`.
- **With `prompt=none`**, a request that would have shown the page is answered `consent_required` at the
  redirect URI instead (OIDC Core §3.1.2.6).

A consent covers a scope when it holds it, and an authorization detail when it holds an identical one, the
same type with the same members: a request that changes anything in a detail asks again. A request that asks
for no detail is covered by any consent that holds its scopes.

## The page

The consent page, `/consent`, says who is asking and what for, in the language of the interaction:

| What it shows | Where it comes from |
|---|---|
| "Authorize *the client*", as its title | The `client_name` of the client, or its `client_id` when it registered none |
| Its logo | The `logo_uri` of the client, loaded by the browser of the person with no referrer. The provider never fetches it |
| "You are signed in as *username*." | The account of the session |
| Every scope of the request | `openid`, `profile`, `email`, `address`, `phone` and `offline_access` in words, any other scope by its name |
| What the request asks for beyond its scopes | One line per authorization detail, in the words its type gives |
| Links to the client's pages | `policy_uri`, `tos_uri` and `client_uri`, in that order, each only when registered, opened in a new tab with no referrer |
| Two buttons, Allow and Deny | |

The page lists every scope the request asks for, those already agreed to included, and every authorization
detail. A consent records scopes and details, and the claims a request names one by one in its `claims`
parameter are not listed on the page: they are served whatever the consent holds ([scopes and
claims](scopes-and-claims.md)). Its Content-Security-Policy is the one of the deployment, completed with
the origin of the client's logo and the one of the tenant's logo in `img-src`, and the origin of the redirect
URI in `form-action`, where the answer is carried after an Allow: nothing a client registers makes the page
load anything else. The template is `consent.html.twig`, which an application overrides like every page of
the bundle ([pages](../symfony-bundle/pages.md)).

**Allow** records the consent and the interaction goes on, to the code. **Deny** ends the interaction, and
the client receives `access_denied` at its redirect URI (RFC 6749 §4.1.2.1). A form posted without the token
the page was rendered with is refused with a `403` page and decides nothing.

## What a consent holds

| Field | What it is |
|---|---|
| The person and the client | One consent in force per pair |
| The scopes | Every scope agreed to |
| The authorization details | Every detail agreed to, each once, none when nothing beyond the scopes was asked |
| When it was given, and when it was taken back | A consent taken back stays as a record, and asks again |

**A new agreement extends, and never takes back.** When a person agrees to a request while a consent is in
force, the provider records a new consent holding the scopes and the details of both, each once, and takes
the previous one back at that instant. A request that asked for less does not narrow what was agreed before,
and a request that asked for no detail keeps the details already held. A `ConsentGranted` event names the new
consent and the one it replaced.

The same consent is recorded whichever page asked for it: the consent page of an authorization request, the
page where a person approves the code of a device, and the page where they approve a backchannel request. The
last two add scopes alone, those flows reading no authorization detail.

## Taking it back

A person takes a consent back from the page of their account that lists the applications they allowed; an
operator does it at the console:

``` bash
bin/console beffroi:user:applications alice
bin/console beffroi:user:revoke-consent alice billing
```

`beffroi:user:applications` lists the consents in force of a person, with what each client holds.
`beffroi:user:revoke-consent` takes back the consent a person gave a client, and says so when there was none.
Either way the same thing happens, and **what was issued under the consent goes with it**:

- the consent is taken back, so the next authorization request of that client asks again;
- every grant this person left to this client is revoked, an authorization code, a device code they approved
  and a backchannel request naming them alike, so no access token that descends from one opens UserInfo or
  is described as active by the introspection endpoint any more;
- every refresh token the client holds for this person is revoked, so nothing renews;
- every opaque access token the client holds for this person is removed, and an unknown token is an invalid
  one (RFC 6750 §3.1).

A self-contained access token in the hands of a resource server that verifies it offline is still worth
something until it expires, ten minutes by default (RFC 9068 §4): nothing the provider does reaches it there.
Its introspection says it is inactive from the instant the consent is taken back.

A `ConsentRevoked` event names the consent, the client, the person, and what went with it, by identifier.

[:beffroi-arrow-right: The account pages](../symfony-bundle/account.md) and
[interactions](interactions.md)
