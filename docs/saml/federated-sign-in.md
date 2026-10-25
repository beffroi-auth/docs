---
title: Signing in through an organisation
description: The login page that asks for the address first, the request sent to the identity provider of that domain, the response it takes back, the person created at the first sign-in and the session it opens.
---

# Signing in through an organisation

Once a tenant declares an [upstream identity provider](upstream-identity-providers.md), the people of its
domains sign in there and nowhere else. The person who arrives at the login page is sent to the identity
provider of their organisation, signs in as they do every morning, and comes back to the client or to the
page that was waiting, as a person of the tenant.

``` mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant P as Beffroi
    participant I as Identity provider of the organisation
    B->>P: The login page asks for the address
    B->>P: alice@example.org
    P->>B: A signed AuthnRequest, to the provider of example.org
    B->>I: The person signs in there
    I->>B: A signed Response
    B->>P: POST /saml/sp/acs
    P->>B: The interaction goes on, a code goes to the client
```

## The login page asks for the address first

**When the tenant has an upstream identity provider**, the login page of an interaction shows one field, the
address, and nothing else: no password, no passkey, no passkey offered by the browser's autofill. The same
holds for the login a page of the provider asks for on its own, the approval of a device, a request waiting
for an answer, the pages of the account or the single sign-on of a service provider. A tenant without an
upstream identity provider shows the usual page.

The field is posted to `/login/address`, and what was typed decides where the browser goes:

| What was typed | Where the browser goes |
|---|---|
| An address of a domain an identity provider answers for | To the sign-on of that identity provider, `/saml/sp/sign-on`, by a `303`, which sends it on to the provider |
| An address of any other domain | Back to the usual login page, its username field holding what was typed, with a way back to the address |
| A value without an `@` | The same: a username, of no domain |
| An address whose domain cannot be read | Back to the page of the address, which says so |

The domain is read one way everywhere it is read: the whole part after the last `@`, through the IDNA of
UTS #46 into its A-label, lower-cased, so an address typed in capitals, in Unicode or in its A-label belongs
to the same domain.

**Nothing here reads a person.** The answer depends on the domain and on the declarations of the tenant, and
on nothing else: the page answers the same status, the same headers and the same body whether somebody holds
that address or not, and waits on no lookup a clock could tell apart. The field holds what this browser typed
last, or the `login_hint` of the request when it is an address, as the client wrote it.

**A `login_hint` of a federated domain skips the page.** When the authorization request carries a
`login_hint` (OIDC Core §3.1.2.1) that is an address of a domain an identity provider answers for, the login
page sends the browser to that provider at once and shows nothing. Every later render of that login goes
there again: such an interaction is signed in through the identity provider or not at all.

## The request sent upstream

The sign-on starts at `/saml/sp/sign-on`, and only from the login page: the redirection that sends the
browser there carries a reference drawn for that login and kept in the session of that browser, used once and
valid one minute. A sign-on that presents no reference, or one this browser was not given, writes no request:
a page of another site can send a browser to that route but cannot read its session, so nobody can start the
login of a person who did not ask for one and have it answered by a session held elsewhere.

The request is an `AuthnRequest` written and signed by the SAML key of the tenant:

| What | Value |
|---|---|
| Where it goes | The first single sign-on service of the accepted metadata on HTTP-Redirect, or on HTTP-POST when the provider offers no other, never an address a request or a page names |
| Signature | RSA-SHA256, over the query string for HTTP-Redirect, in the XML for HTTP-POST |
| `Issuer` | The entity ID of the service provider of the tenant |
| `AssertionConsumerServiceURL` | `/saml/sp/acs`, with the HTTP-POST binding |
| `NameIDPolicy` | `persistent`, with `AllowCreate="true"` |
| `ForceAuthn` | When the client asked for a login the session of this browser cannot answer, and when a page asks a signed-in person for a fresh proof |
| `RelayState` | 32 random bytes in base64url, and nothing else: no URL, no value of the request |

`ForceAuthn` follows what the login page itself would ask of a browser that holds a session of the provider:
`prompt=login`, a `max_age` that session exceeds, a step-up, `prompt=select_account`, an `id_token_hint` naming
another person. A browser that holds no session forces a login for `prompt=login` alone, and the age of what
the person proved is checked when the response comes back. Without it, a session the person left open at their
identity provider would answer a client that asked for a fresh login.

The request is remembered in the HTTP session of the browser, under its `RelayState`, for ten minutes, eight
at most per browser: what a response answers is read there, and nowhere else.

**The address can go with it.** An identity provider that reads a hint on its sign-in page is declared with
`address_parameter`, `login_hint` for Microsoft Entra ID, and the address typed on the login page, or the
`login_hint` that skipped it, is added in that parameter: after the `Signature` over HTTP-Redirect, outside
what is signed, and in the query of the form's action over HTTP-POST. It goes only to the provider that
answers for its domain, and it is a hint and never a proof: the person is who the signed assertion names,
whatever the form at the provider was prefilled with.

## The response taken back

The assertion consumer service is `/saml/sp/acs`, `POST` only, a body in `application/x-www-form-urlencoded`
and nothing else (`415`). The identity provider posts it from its own site, so it arrives without the session
cookie, and it is posted again once from the provider's own origin, as a [sign-on
request](single-sign-on.md#the-request) is.

**A response nobody asked for is refused.** The `RelayState` has to name a request this browser remembers,
sent less than ten minutes ago, and it is forgotten as it is read, so a form posted twice finds nothing the
second time. A response that answers no request this provider sent cannot be told apart from one an attacker
obtained for their own account, which is how a victim gets signed in to the attacker's.

**It is verified under the provider the request went to**, never under one the message names: its
`InResponseTo` is that request, its `Issuer` that provider, its `Destination` and `Recipient` the URL of the
assertion consumer service, its `Audience` the entity ID of the service provider. Every assertion is covered
by a signature, its own or the response's, made by a key of the provider's metadata, and is accepted once.
An encrypted assertion is opened [by the keys of that provider alone](upstream-identity-providers.md#the-key-it-encrypts-for).

**A response whose status is not `Success`** carries no assertion and signs nobody in. The person cancelled or
failed at their identity provider, so the client is answered `access_denied` at its redirection URI with its
`state`, or `login_required` when the provider answered `NoPassive` to a request with `prompt=none` (OIDC
Core §3.1.2.6), and nothing the identity provider wrote reaches the client.

Every refusal is a page that names the rule and never a value of the response, opens no session and writes
nothing of the person. A response the service provider does not take, a person it may not sign in and a login
under the floor of the tenant are each written to the journal as a refused login, with the method `fed`.

## The person

**Named by the provider, never by an address.** The subject is the value of a persistent `NameID`, or, for a
provider declared with `subject_attribute`, the one value of that attribute. A subject that is the same
mailbox as the address of the assertion is refused whatever names it, so a mailbox given to somebody new
never leads to the account of the one who held it.

**Found by the link, never by the address.** The person is the one whose linked identity names that provider
and that subject. At the first sign-in there is none, and the person is created in one unit, all of it kept or
none of it:

- the person, its subject drawn as any other, its username its address, the address verified, the provider
  answering for its domain;
- its source, the identity provider, with the claims of the profile it filled;
- its linked identity, with what the provider said;
- a telephone number, unverified, when the profile maps one;
- its memberships, the groups the declaration maps the values of the groups attribute to.

The address has to be in a domain of that provider, and held by no other person of the tenant, as a mailbox
or as a username: an existing account is never linked on its own. An administrator who wants a person who
already exists to sign in through a provider links them by hand, naming the entity ID of the provider and the
subject it gives that person:

``` bash
bin/console beffroi:user:link alice 'https://idp.example.org/saml/metadata' 'the-subject-it-gives-alice'
```

A person linked that way signs in under the link with none of the rules of a first sign-in, only the
snapshot of the linked identity being refreshed.

**The provider keeps what it fills.** At every later sign-in, what the source holds becomes exactly what the
provider fills and says now, the memberships it asserts are replaced, and the username follows the address
when the provider sends another one. A claim it no longer says is released to the person, with the value it
wrote last. What the source holds, neither the person on the page of their account nor an operator with
`beffroi:user:profile` can change.

**A disabled person is refused** before anything of them is written: an account an administrator disabled
keeps what it held and stops following the provider. The page says what it says of every refusal, and
nothing of the state of the account.

## The session

| What | Value |
|---|---|
| `amr` | `fed`, a federated assertion, and the class of the provider where its meaning is exactly a method (RFC 8176 §2): `Password` and `PasswordProtectedTransport` add `pwd`, `Smartcard` adds `sc`, `TimeSyncToken` adds `otp`, any other class adds nothing |
| `auth_time` | The `AuthnInstant` of the assertion, the instant the person authenticated at their provider, never the instant the response arrived |
| Its end | No later than the `SessionNotOnOrAfter` the provider set, which is the one way it has of ending the session it vouches for. An assertion whose `SessionNotOnOrAfter` has passed is refused |

The session is opened under the [floor of the tenant](../core/tenants.md#the-floor-of-its-logins), like
every login: a tenant that asks for two factors refuses a login that proved `fed` and `pwd` alone.

**What the client asked is held at the response.** A login made during the interaction, an `AuthnInstant` at
or after the instant it began, satisfies `prompt=login`, a `max_age` and a step-up. An earlier one does not:
the request is sent once more with `ForceAuthn` when the first one did not carry it, and when it did, the
client is answered `login_required`, or `account_selection_required` for `prompt=select_account`. A request
is never sent a third time, so a provider that ignores `ForceAuthn` never sends the browser round without end.
The comparison has no tolerance for clocks, and a provider whose clock lags by more than the time a person
takes to sign in answers `login_required` until its clock is set.

**The browser goes back to what was waiting**, and nowhere a response or a parameter names: the login page of
the interaction, which resumes it and sends the code to the redirection URI the client registered, or the page
of the provider that asked for the login.

## No local credential for an organisation's people

A person whose address is of a domain an identity provider answers for, their mailbox or a username holding
an `@`, signs in through that provider and through nothing else.

- **At the login**, a password, a passkey and the code that completes a password are refused for them,
  whatever the page offered, so a form written by hand fails as the page would. A refused password answers
  as a wrong one, at the cost of a wrong one, and the journal records why.
- **On the pages of the account**, no form that would pose a password, a passkey or an authenticator
  application is offered, and the page says why: their organisation signs them in.
- **Anywhere a credential is posed**, the console setting a password, an enrolment ticket for a passkey, a
  TOTP, a renewal of backup codes, the replacement of a password held before the domain was federated: the
  answer is the same refusal.

So a person who leaves the organisation and loses their account in its directory has no local password left
that outlives the departure.

On a tenant with an upstream identity provider, an address whose domain cannot be read counts as one of a
federated domain, refused rather than taken for an address of none. The account an administrator keeps for
the day the identity provider is down therefore has a username without an `@`, or an address in a domain of
two labels at least that no provider declares, and never one such as `admin@localhost`.
