---
title: Observability
description: The journal of the acts, where a request came from, what a client was given, what a record used to say, the logs, and what the image exposes.
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
| The client it concerned, by the identifier it was registered under, when it concerns one | In the clear |
| The identifier of the row | A UUIDv7, so the journal sorts by time on its primary key |

**The reads that hand a person over to a third party are acts too**: an introspection that tells a resource
server who a token names, `introspection.answered`, and a UserInfo answer, `userinfo.answered`. An
introspection that describes nobody, because the token is inactive or held by a client for itself, writes
nothing.

A person reads the acts of their account on [the page of their acts](../symfony-bundle/account.md#the-pages).
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

## The logs

The logs are for failures. In production, Monolog writes JSON to the standard error of the process, in two
handlers:

| Handler | What it writes |
|---|---|
| `main` | Every channel but deprecations, held in a buffer of the fifty latest records and written, with what follows, once one of them is an error. An error that is a `404` or a `405` is not one |
| `deprecation` | The deprecations, as they come |

A console command also writes its log lines on its own output, the `event` and `doctrine` channels aside. In
the development environment every channel but `event` goes to `var/log/dev.log`, from `debug` up.

Besides what Symfony logs of a request or a message that fails, the provider writes these lines of its own:

| Level | When |
|---|---|
| `info` | A timed step forgot or removed something: acts of the journal and what a client was given at them, changes of a record, expired archives, rows that could no longer do anything, clients that registered themselves and that nobody used. A GeoLite2 database, or the metadata of a SAML peer, was refreshed or found unchanged. A push service answered that a subscription is gone, and the subscription was taken out |
| `warning` | A refresh of the GeoLite2 databases was refused. A database of addresses cannot be read, or answered a record the provider cannot read. A push service did not take a notification. A claim was not sent to a SAML service provider, its value being neither a string, an integer, a boolean nor a list of them |
| `error` | The metadata of a SAML peer were refused, or those of a whole role could not be refreshed. A client that registered itself holds metadata the provider now refuses, and is served as no client |

In production an `info` or a `warning` reaches the log only beside an error. The acts are in the journal, not in
the log.

Caddy writes an access log for each of its sites, one line per request with its path and query string.
`CADDY_SERVER_LOG_OPTIONS` adds directives to both logs. On the site of `SERVER_NAME`, the `authorization`
parameter of the query is replaced by `REDACTED`; the site that asks for a client certificate replaces
nothing. A path is written as it was requested, the link of an enrolment ticket, `/enrol/{ticket}/{value}`,
included.

## Metrics and health

The provider exports no metrics of its own. The health check of the image reads the metrics endpoint of the
Caddy admin API inside the container, `http://localhost:2019/metrics`, and the development stack reports its
worker healthy while `messenger:consume` is the first process of its container.

The panel the provider adds to the Symfony profiler is wired only in a kernel that runs in debug, and the web
profiler is registered in the development and test environments alone: a production kernel has neither.
