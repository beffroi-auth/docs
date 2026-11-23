---
title: Observability
description: The journal of the acts, where a request came from, what a client was given, what a record used to say, the chains that show a row changed in the database, the logs, and what the image exposes.
---

# Observability

Every session and every event carries a request context: an address, a user agent, and what is derived from
them, enriched asynchronously so that a sign-in never waits on it. What is recorded, and for how long, is a
property of the deployment.

## The journal

**The acts of the provider are written down, kept and read**: who did what, when and from where. Nothing
turns the journal on; what a deployment configures is how long an act is kept, `journal.retention`, 180 days
by default, which is the duration the CNIL deliberation 2021-122 holds for a log of connections. A deployment
under another obligation says its own, and a timed step forgets, once a day, what is past it.

Every event of the core and of the protocols is an act, written under the name the event gives itself:
`user.authenticated`, `authentication.failed`, `tokens.issued`, `consent.revoked`, `session.ended`,
`tenant.key_rotated` and the others. The worker writes it on the lane the events travel on, so the journal is
never on the path of a request, and an act that cannot be written down does not undo what was done.

A row holds what follows and nothing else, no field a caller could fill with a secret:

| What | How it is kept |
|---|---|
| The name of the act | In the clear |
| When it happened | In the clear |
| The tenant | In the clear |
| Where it came from: the address, the user agent and the place derived from them | Sealed under the data key of the tenant, in a family of its own |
| The person it was done in the name of, by the subject their account carries, when it names one | In the clear: a subject names a person without saying anything about them |
| The client it concerned, by the identifier it was registered under, when it concerns one. A refused authentication of a client names the client the request named when the tenant holds it, and none otherwise | In the clear |
| The administrator who did it through the administration API, by the subject their account carries, when one did | In the clear, as the subject is |
| Why a refusal refused and the method it refused, in words the provider gives them, when the act is a refusal: a reason such as `invalid_credential`, `too_many_attempts`, `unknown_client` or `untrusted_certificate`, and a method such as `pwd` or `client_secret_basic` | In the clear: they say nothing of a person |
| The identifier of the row | A UUIDv7, so the journal sorts by time on its primary key |

**The reads that hand a person over to a third party are acts too**: an introspection that tells a resource
server who a token names, `introspection.answered`, and a UserInfo answer, `userinfo.answered`. An
introspection that describes nobody, because the token is inactive or held by a client for itself, writes
nothing. The reads an administrator makes of a person through the administration API are acts of that person
as well, each naming the administrator: `administration.person_read`, `administration.sessions_read`,
`administration.journal_read`, `administration.consents_read`, and `administration.membership_read` once for
each member of a group read. A write of the API that changes nothing and answers with the person is the read
`administration.person_read`, and the logout tokens sent for a session an administrator ended,
`logout_token.issued` and `logout_token.given_up`, name that administrator. A read refused because the
administrator spent [their budget of persons](security.md#attempts-and-budgets) delivers nobody and is the act
`administration.read_refused`, in the journal of the administrator.

A person reads the acts of their account on [the page of their acts](account.md#the-pages).
An operator reads them with `beffroi:user:journal`:

``` bash
bin/console beffroi:user:journal alice --from=2026-01-01 --to=2026-01-31 --act=tokens.issued --format=json
```

`--from` and `--to` are two days in UTC, both included, `--act` is repeatable, `--client` narrows to one
application, and `--format=json` writes the document a request about what happened in somebody's name is
answered with. A period that reaches past what the deployment keeps is answered with how long it keeps an act
and the day that reaches, never with an empty table that looks complete.

## Where a request came from

| What | Where it comes from |
|---|---|
| The address | The address of the client as Symfony reads it, behind the proxies `SYMFONY_TRUSTED_PROXIES` names |
| The user agent | The `User-Agent` header, its surrounding whitespace trimmed and cut at 1024 characters, and none when it is empty |
| The place | Derived from the address on the lane of the events, from the GeoLite2 City and ASN databases, and written back on the session that recorded it |

A console command records `beffroi-console/<command> (<user>@<host>)` in place of a user agent, and a timed
step `beffroi-scheduler/<schedule> (<host>)`, with no address in either.

**A provenance says from where and not only from which address.** The databases are read locally: what leaves
the provider is a request for a file once a week, carrying the licence key of the deployment and nothing of
anybody who signed in. They are published by MaxMind under their own licence, so nothing is shipped and
nothing is downloaded without a licence key: a deployment that names none in `GEOIP_LICENSE_KEY` serves every
flow with a provenance that says an address and no place.

## What a client was given

At each act that hands something over, the provider keeps what left with it: the scopes, the claims asked for
by name (OIDC Core §5.5) and the authorization details (RFC 9396 §7), sealed in a family of their own, and the
shape of the access token, under the subject of the person, as the journal names them. What an application
obtained of somebody therefore still has an answer after the consent it was given under was taken back.

It is kept exactly as long as the act that gave it, and forgotten by the same timed step: an act whose details
are gone, or details whose act is gone, would be half an answer.

## What a record used to say

The changes of the claims of a person, what each one said before and after, are kept sealed under the data key
of the tenant, under a retention of their own, `history.retention`, 180 days as well unless the deployment says
otherwise, and forgotten by a timed step once a day. A person reads them at `/account/profile/changes`.

## The chains

**A row of the journal, of the history of claims or of what a client was given that is changed, added or
removed in the database after the provider wrote it is seen.** Each of the three records is a chain per tenant,
whose head the worker signs every five minutes and keeps beside the keys of the tenant, outside the database:
[the chained records](persistence.md#the-chained-records). A deployment watches them in two places:

- **The log channel `chain`**, [below](#the-logs), which carries a copy of each signed head as it is signed.
  Kept by the log collector of the deployment, it is the copy neither the database nor the key storage holds,
  and `beffroi:chain:verify --against` compares a chain with it.
- **One point per chain** of `beffroi:doctor` and of `GET /health`, red at the first position that does not
  follow, named and never by what the row holds, and red as well when the schedule has stopped: the chain last
  signed more than ten minutes ago, or last walked whole more than two days ago.

What to do with a chain that does not follow is in [the console](console-commands.md#the-chains-of-records),
and the role that keeps the processes from rewriting a row in
[persistence](persistence.md#the-role-the-processes-connect-as).

## The logs

The logs are for failures. In production, Monolog writes JSON to the standard error of the process, in three
handlers:

| Handler | What it writes |
|---|---|
| `main` | Every channel but deprecations and `chain`, held in a buffer of the fifty latest records and written, with what follows, once one of them is an error. An error that is a `404` or a `405` is not one |
| `chain` | The signed head of a [chain](#the-chains), at `notice`, as it comes and never held back for an error: one line naming the chain, the tenant and the position signed, with the hash of that position and the JWS itself, which `beffroi:chain:verify --against` reads |
| `deprecation` | The deprecations, as they come |

A console command also writes its log lines on its own output, the `event` and `doctrine` channels aside. In
the development environment every channel but `event` goes to `var/log/dev.log`, from `debug` up.

The records Symfony writes of every request it routes, on the `request` channel, which `main` writes out with
the first error of the request, keep no value of a ticket or of the confirmation of an address and no value of
a parameter of the query: each is written `REDACTED`, its name kept. No log line carries the endpoint of a push
subscription: a push that fails is logged with the subscription, the tenant and what failed, the endpoint
written as "the endpoint".

Besides what Symfony logs of a request or a message that fails, the provider writes these lines of its own:

| Level | When |
|---|---|
| `info` | A timed step forgot or removed something: acts of the journal and what a client was given at them, changes of a record, expired archives, rows that could no longer do anything, clients that registered themselves and that nobody used. A GeoLite2 database, or the metadata of a SAML peer, was refreshed or found unchanged. A push service answered that a subscription is gone, and the subscription was taken out |
| `warning` | A refresh of the GeoLite2 databases was refused. A database of addresses cannot be read, or answered a record the provider cannot read. A push service did not take a notification. An address marked verified is one a mail cannot carry, and nothing is written to it. A claim was not sent to a SAML service provider, its value being neither a string, an integer, a boolean nor a list of them |
| `error` | The deployment cannot write a mail, its DSN being one no installed factory reads or its sender none or no address, or cannot send a text, its DSN being one no installed bridge reads, or a text was refused before it left; each is said again at each message. The metadata of a SAML peer were refused, or those of a whole role could not be refreshed. A client that registered itself holds metadata the provider now refuses, and is served as no client. The keys a thread of the server or the worker opens when it starts could not be opened, the key management service not answering or refusing one, and each is opened at its first use. A chain was not signed, or its retention forgot nothing of it, and why |

In production an `info` or a `warning` reaches the log only beside an error. The acts are in the journal, not in
the log.

Caddy writes an access log for each of its sites, one line per request, which keeps the path and the names of
the parameters of the query and never a value: the value of every parameter of the query is written
`REDACTED`, whatever its name, and so is the value that follows the identifier of a ticket or of the
confirmation of an address in a path, `/enrol/{ticket}/{value}`, `/password/{ticket}/{value}`,
`/two-factor/{ticket}/{value}` and `/account/addresses/{claim}/{confirmation}/{value}`. The three sites, the one
of `SERVER_NAME`, the one that asks for a client certificate and the one of the administration API, write it
alike, and `CADDY_SERVER_LOG_OPTIONS` adds directives to the log of each.

## Metrics and health

The provider exports no metrics of its own. Caddy serves its metrics on its administration API, which the production
image runs without unless `CADDY_ADMIN` names an address for it. The health check of the production image asks the
provider itself for a document it serves, through the site of `SERVER_NAME`:
[the health check](deployment.md#the-health-check).
Each check is a line of the access log of that site, under the user agent `docker-healthcheck`. The Compose
files of the repository report their worker healthy while `messenger:consume` is the first process of its
container.

What the instance knows of itself is read on request, and nothing is kept between two reads.
`beffroi:statistics`, and `GET /statistics` of the administration API, give its people, clients and open
sessions, its keys by state, its acts by name over what the journal keeps and the messages waiting in each
lane; `GET /health` of the same API gives the points `beffroi:doctor` looks at, among them one per
[chain](#the-chains).

The panel the provider adds to the Symfony profiler is wired only in a kernel that runs in debug, and the web
profiler is registered in the development and test environments alone: a production kernel has neither.
