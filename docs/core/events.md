---
title: The events of the core
description: What the core announces, what every event carries, what each one of the core carries beyond that, and how they leave the process.
---

# The events of the core

The core dispatches PSR-14 events and nothing else: it knows no bus and no broker. An event is built where it is
raised, its constructor takes exactly what it carries, and it carries a domain object only when that object
survives the queue it may be written to, the facts by identifier otherwise. The protocol and the SAML package
raise events of the same shape, and [the reference](../reference/events.md) lists every one of the three
packages with what listens to it.

## What every event carries

Every event implements `DomainEventInterface`, and so carries four things:

| Member | What it is |
|---|---|
| `name()` | The name of the act, which the journal writes down: a label the event gives itself, such as `user.authenticated`, and never a class name |
| `occurredAt` | When it happened |
| `tenant` | The tenant it happened in |
| `context` | The provenance of the request it came from: when the request was received, the address and the user agent. A command of the console names itself, the user of the shell and the host in place of a user agent, `beffroi-console/<command> (<user>@<host>)`, and a timed step names the schedule and the host, `beffroi-scheduler/beffroi (<host>)`, both with no address |

Two interfaces say more of an event that means more:

| Interface | What it adds | Read by |
|---|---|---|
| `ConcernsAPersonInterface` | `subject()`, the person the act concerns, by the subject their account carries and never by the `sub` a client was given, a pairwise one included. Null where the act named nobody: a login refused on an identifier no account answers happened to no one this provider knows | The journal, which files the act under that person |
| `SessionProvenanceInterface` | `sessionId()`, the session whose row holds the very provenance the event carries | The enrichment that finds the place of that provenance and writes it on the row of the session |

**An event that names a domain object carries it whole**, as its row holds it: a credential with its hash or its
envelope and the person it belongs to, a session with its two provenances, a key with its sealed private half.
That is why the body of every message is sealed on its way out. What reaches the journal of the acts is the act,
its date, its provenance, sealed, the subject and the client, and nothing else of what the event carries. An
event that names facts carries the facts and no more: `person.provisioned` carries the subject and the name of
the provider, never what the provider said, and an archive is named by its identifier and never carried.

## The events

### Signing in

| Act | Class | Raised when | Carries beyond the four |
|---|---|---|---|
| `user.authenticated` | `UserAuthenticated` | A session is opened, whatever proved it | The session, whose opening gives the event its date and its provenance |
| `authentication.failed` | `AuthenticationFailed` | A login is refused, whatever was tried | The method the attempt claimed, null when a passkey ceremony failed before naming one; the reason; the identifier as typed, null when nothing was typed; the user, null when no account answers |
| `session.ended` | `AuthenticationSessionEnded` | A session ends, whatever ended it | The session, which says who ended it: `user` or `relying_party`, the two the bundle writes |
| `password.used` | `PasswordUsed` | A password is accepted, whether or not a code follows | The credential |
| `passkey.used` | `PasskeyUsed` | A passkey assertion is verified | The credential, and whether its sign count did not grow |
| `totp.used` | `TotpUsed` | A code of the authenticator application is accepted | The credential |
| `backup_code.used` | `BackupCodeUsed` | A backup code is spent | The credential |
| `person.provisioned` | `PersonProvisioned` | An upstream provider creates a person, at their first sign-in through it | The subject of the person and the name of the provider |

The reason of a refused login is one of `unknown_user`, `no_such_credential`, `invalid_credential`,
`disabled_user`, `revoked_credential`, `replayed_code`, `too_many_attempts`, `expired_login`, `below_the_floor`,
`federated_domain`, `upstream_response_refused` and `upstream_person_refused`. It is written for the audit, and
the person is told no more than the page needs: the login page says the same thing whatever the reason, and the
page of a code says apart when too many codes have been tried.

### Credentials

| Act | Class | Raised when | Carries beyond the four |
|---|---|---|---|
| `credential.enrolled` | `CredentialEnrolled` | A passkey or a TOTP is enrolled | The credential |
| `credential.renamed` | `CredentialRenamed` | A person renames a passkey | The credential, and the name it had |
| `credential.revoked` | `CredentialRevoked` | A credential is revoked | The credential |
| `credential.forgotten` | `CredentialForgotten` | The floor of the tenant forgets a credential, row and secret | The credential, the only trace left of it |
| `password.changed` | `PasswordChanged` | A person replaces their own password | The credential |
| `password.rehashed` | `PasswordRehashed` | A password is stored again under the current algorithm and parameters | The credential |
| `backup_codes.renewed` | `BackupCodesRenewed` | A person draws another set of backup codes | The credential, and never a code |
| `enrolment_ticket.issued` | `EnrolmentTicketIssued` | An administrator issues an enrolment ticket | The ticket, which holds a hash of its value |

### The person and their record

| Act | Class | Raised when | Carries beyond the four |
|---|---|---|---|
| `person.described_themselves` | `PersonDescribedThemselves` | A person says something of themselves on their account | The user, the name of the claim, and whether they took it back |
| `archive.asked` | `PersonAskedForTheirArchive` | A person asks for their archive | The identifier of the archive and the subject of the person |
| `archive.taken` | `PersonTookTheirArchive` | A person downloads their archive | The same |
| `archive.dropped` | `PersonDroppedTheirArchive` | A person has their archive dropped | The same |

### Keys and data keys

| Act | Class | Raised when | Carries beyond the four |
|---|---|---|---|
| `tenant.key_staged` | `TenantKeyStaged` | A key is drawn and staged, used for nothing yet, and published in the JWK Set when its algorithm is one the set carries | The key |
| `tenant.key_rotated` | `TenantKeyRotated` | A key takes over | The key activated, and the key it replaced, null for the first of its algorithm |
| `tenant.key_retired` | `TenantKeyRetired` | A key leaves the service | The key, and why: `due`, `forced` or `compromised` |
| `tenant.data_keys_rewrapped` | `TenantDataKeysRewrapped` | The data keys of the tenant are wrapped by another client | How many keys over how many scopes, the client they came from when one was named, the client and the master key that wrap them from then on |
| `tenant.data_keys_destroyed` | `TenantDataKeysDestroyed` | The data keys of the tenant are erased | How many keys over how many scopes |

### The deployment

| Act | Class | Raised when | Carries beyond the four |
|---|---|---|---|
| `kms.unavailable` | `KmsUnavailable` | The key management service of the tenant does not answer, or refuses, on the path of a request | What the service said, and never a secret, a key or an envelope |
| `load.budget_spent` | `LoadBudgetSpent` | A request is refused because a budget that bounds a load is spent | The budget, the route asked for, and the client the budget was counted on, null for the budget of an origin |

The page of the account that reads the journal of a person shows every act of this list that concerns a person,
`password.rehashed` excepted, which is this provider storing a hash again and nothing the person did.

## How they leave

In the bundle, the dispatcher the core is handed is `EventBusDispatcher`, which replays every event on the
`event.bus` of Messenger; an event raised by the handler of a message leaves once that handler has committed
its work. Every event is routed by the
interface they all implement to the transport `async_priority_low`, the database unless the deployment names a
broker, and its body is sealed to the message key of the tenant on its way out. Nothing listens in the process
that raised it: a worker that consumes the transport is where every listener runs, and an event nothing listens to
is announced all the same.

What listens is a message handler of `event.bus`. The handlers of the bundle are classes marked
`#[AsMessageHandler(bus: 'event.bus')]` whose `__invoke()` is typed on an event, or on an interface every event of
a kind implements, which is how the one that writes the journal hears every event of the three packages.
[Messenger](../symfony-bundle/messenger.md) describes the buses and the transports.
