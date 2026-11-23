---
title: Console commands
description: 'What the commands of the application need explained beyond their help: the rotation of a key, the data keys, the chains of records, the role of the database, and the doctor.'
---

# Console commands

The application has commands for the tenant, the statistics of the instance, the people and their journal,
groups, clients, keys, data keys, the chains of records, the role of the database, the metadata of SAML peers,
the databases of addresses and the metadata of FIDO. [The reference](../reference/console-commands.md) lists
every one of them; `bin/console <command> --help` gives its arguments and options. This page explains the ones
a help screen does not: the rotation of a key, the data keys, the chains of records, the role of the database,
and the doctor.

## What every command shares

**A command works on the tenant of the configuration.** One that needs its row stops when the row is missing
or no longer says what the configuration says, and names the field and the command that fixes it:

``` text
The tenant "default" of the configuration has no row yet: synchronise it before serving requests.
Run "beffroi:tenant:synchronize" first.
```

**A command that reads is never the command that writes.** `beffroi:user:show` reads and
`beffroi:user:profile` writes; `beffroi:data-keys:list` reads and `beffroi:data-keys:rewrap` writes.

**What a command does is an act like any other**, written to the journal with the console as where it came
from: `beffroi-console/<command> (<user>@<host>)`, the user being the one behind `sudo` before the one of the
shell. A step of the schedule is written as `beffroi-scheduler/beffroi (<host>)`.

**What a command did not write is printed as text.** A name a person, a client, an administrator or a
directory chose, and what a remote source answered, reach the terminal without their control characters, the
bidirectional ones included, and with the markup of the console escaped: nothing they hold moves the cursor,
sets the title or the clipboard, or reads as another name. What the operator typed and what the code writes
are printed as they are.

## Rotating a key

A key of the tenant is staged, then active, then retiring, then retired. Of the keys it publishes, the JWK Set
carries the first three, so a relying party sees a key before anything is signed with it and keeps verifying
it once another has taken over. [Keys](../tenant/keys.md) says what each key of a tenant is for.

| Command | What it does |
|---|---|
| `beffroi:keys:generate` | Draws a key, seals it and makes it the active one of its algorithm at once. The right command for a tenant that has no key of that algorithm, and a rotation with no staging delay on one that has |
| `beffroi:keys:rotate` | Stages a key: published at once, active once the staging delay has elapsed. On a tenant that has no active key of the algorithm, the key is active at once |
| `beffroi:keys:activate <kid>` | Makes a staged key active before its delay has elapsed |
| `beffroi:keys:retire <kid>` | Takes a retiring key out of the JWK Set once its retirement date has passed, or before it with `--force`; `--due` retires every key past its date that nothing holds |
| `beffroi:keys:list` | The keys in service with their use, status and dates, or every key with `--all`; `--check` is described below |

``` bash
bin/console beffroi:keys:rotate --algorithm=ES256
bin/console beffroi:keys:list
```

`--algorithm` names the key: a JWS algorithm for a key that signs, a JWE key management algorithm for a key
clients encrypt to, or the name of a key the tenant keeps, `MESSAGE-SEAL`, `VAPID`, `SAML-SIGNING`, or
`SAML-ENCRYPTION:` followed by the entity ID of an upstream identity provider. Left out, it is the default
signature algorithm, `RS256`. One run reaches one algorithm, and a tenant holds one active key per algorithm.

### Time does the rest

The step `AdvanceKeyLifecycle` of [the schedule](messenger.md#what-time-does-on-its-own) runs every minute and
does, in this order, what the commands do by hand: it stages a successor for every active key that has worked
for its age, activates every staged key whose delay has elapsed, and retires every retiring key past its date.
A tenant nobody watches does not sign with the same key for ever, and the tick that stages a successor is never
the one that activates it. A staged key whose delay elapses while a newer key of its algorithm is active is not
activated by the step: it starts retiring, with the window of its use, without having signed anything.
`beffroi:keys:activate` naming it before the step reaches it is the one way it still takes over. A message key past
its date stays retiring while a message waiting in the failure transport is sealed to it.

| Figure | In the image | Set by |
|---|---|---|
| The staging delay, how long a new key is published before it signs | `BEFFROI_JWKS_MAX_AGE` plus sixty seconds: 360 seconds with the 300 of the image | `BEFFROI_KEY_STAGING_DELAY`, in seconds |
| The age, how long a key works before a successor is staged, counted from its activation | 90 days | `BEFFROI_KEY_AGE`, in seconds |
| The retirement window, how long a replaced key stays published | The longest lifetime of what is bound to a key of that use: the ID tokens, access tokens, signed authorization responses and logout tokens for a key that signs, the request objects and pushed requests a client may still be encrypting for a key it encrypts to | Read from those lifetimes, never set on its own |

The sixty seconds are the cooldown of Symfony's `oidc_login`, which fetches the JWK Set again on a `kid` it
does not know only once its copy is that old: they cover a relying party whose copy came late through a shared
cache. An age that is not longer than the retirement window of its use is refused at the first tick that
reaches it, since every rotation would otherwise leave one more key in the JWK Set. The SAML signing key has
figures of its own, seven days of staging and a year of age in the image, `BEFFROI_SAML_KEY_STAGING_DELAY` and
`BEFFROI_SAML_KEY_AGE` ([the SAML identity provider](../saml/identity-provider.md)).

### Rotating by hand

**`--now` skips the staging delay.** The new key signs at once and the previous one starts retiring: a relying
party whose copy of the JWK Set is younger than sixty seconds refuses the new tokens, or encrypts to the old
key, until its copy is that old. It is for an operator who knows every relying party is cold.

**`--compromised` leaves no window.** The new key takes over at once, and the compromised one leaves the JWK
Set at the same moment with every other key of its algorithm, those waiting to take over and those still
retiring: nothing bound to any of them is honoured from then on, and the JWK Set holds the new key alone for
that algorithm.

``` bash
bin/console beffroi:keys:rotate --compromised --algorithm=RS256
```

**`beffroi:keys:retire --force`** takes a retiring key out before its date, after a compromise or when
everything bound to it is known to have expired; the journal says it was retired before its date. Without
`--force`, a message key a message of the failure transport is sealed to is refused, the refusal saying what
holds it, until `messenger:failed:retry` replays the message or `messenger:failed:remove` removes it; with
`--force`, the key retires all the same, and that message then does not open.

### Checking the keys

``` bash
bin/console beffroi:keys:list --check
```

`--check` opens the active and the staged keys with the key management service, and says of each active key
whether it has worked past its age and whether a successor is staged behind it. A retiring key is not opened
by the check: in service, it is opened only to read what was encrypted to it. It fails in two cases, and says
what to do in both:

- **A key the service cannot open.** If the service is down, the same run passes once it is back. If it lost
  the master key, the envelopes sealed under it are dead: the command prints one
  `beffroi:keys:rotate --now --algorithm=<name>` per algorithm, each rotation sealing a new key under the master
  key the service holds now, the dead key retiring with its window, its public half still verifying what it
  signed. Nothing is deleted.
- **An active key past its age with nothing staged behind it.** The step of the schedule stages one every
  minute, so this is a worker that does not consume `scheduler_beffroi`: the command names the transport, and
  the rotation that does the same thing by hand.

## Data keys

The columns that carry a personal datum are sealed under data keys of the tenant, one per family of columns,
wrapped by its master key. [Persistence](persistence.md#sealed-columns) says which columns; these commands
are how an operator holds the keys.

**`beffroi:data-keys:list`** shows the keys by scope, `<slug>.<family>`, with when each was minted, the master
key that wraps it and the client that opens it. The last key of a scope is the one a write uses; the ones before
it still open what they sealed, and a rotation never erases them. A family that has sealed nothing yet has no
key, a data key being minted at the first write of its family. The command never opens a key.

**`beffroi:data-keys:rewrap`** wraps the data keys of the tenant with another client from now on, or with
another master key of the same one. No sealed value is read or rewritten: what changes is how a data key is
protected, and every ciphertext goes on naming the same key. Each key it moves is bound again under the first
secret of `BEFFROI_DATA_KEY_SECRETS`, `APP_SECRET` while that variable is not set, so the command run towards
the client that already wraps the keys is how that secret is replaced ([personal
data](../tenant/personal-data.md#rotating-the-secret-that-binds-them)).

``` bash
bin/console beffroi:data-keys:rewrap --to=second --dry-run
bin/console beffroi:data-keys:rewrap --to=second --from=op
```

- `--to` names the client that wraps the keys from now on, `op`, built from `BEFFROI_KMS_DSN`, or `second`,
  built from `BEFFROI_KMS_DSN_SECOND`, and the command lists the clients when it is missing.
- `--from` moves only the keys that client holds; all of them without it.
- `--dry-run` lists what would move and writes nothing.
- `--accept-unbound` moves as well the keys wrapped under no context, which open nothing until they are
  wrapped again under their reference and their scope.

The master key is the one `BEFFROI_KMS_KEY_ID` names for the tenant, resolved from the environment and never
asked for: an operator who had to type it could type the one of another tenant. It moves one tenant, the one
of `BEFFROI_TENANT_SLUG`, and nothing schedules it.

**`beffroi:data-keys:destroy`** erases every data key of the tenant, the key of its blind indexes with them.
Every column they sealed keeps its ciphertext, and nothing in this database opens it again: that is the
erasure of a tenant, and it cannot be undone, no more than `beffroi:tenant:login-floor`, which forgets the
credentials the floor forbids, secret and row, or `beffroi:client:delete`, which deletes a client that
registered itself. It asks for the slug of the tenant typed back, and has no `--force`:

``` bash
bin/console beffroi:data-keys:destroy default
```

The rows stay; what is gone is the means of reading them. The keys of the tenant, its pairwise salt and the
envelopes sealed under its master key are not touched.

[:beffroi-arrow-right: Key management](key-management.md#moving-to-another-client)

## The chains of records

The journal, the history of claims and what clients were given are three chains, `journal`, `claim_history`
and `disclosures`: each row is linked to the one before it, and the worker signs the head of each chain every
five minutes ([persistence](persistence.md#the-chained-records)). The last signature of a chain is the file
`var/keys/<slug>/chains/<chain>.jws`, and each signature is also a line of the log channel `chain`, whose
`context.checkpoint` is the compact JWS: a deployment that collects its logs keeps a copy that neither the
database nor `var/keys` holds.

``` bash
bin/console beffroi:chain:verify
bin/console beffroi:chain:verify journal --against=head.json
```

**`beffroi:chain:verify`** walks every chain whole against its last signature, or the one it names, and says
which positions each keeps and up to where its signature holds. It fails at the first position that does not
follow, naming the position and never what the row holds, and on rows that sit outside the chain. It reads and
writes nothing. `--against` names a file holding a signed head of the chain named, the compact JWS or the line
of the log that carries it, and fails when the chain ends before that head or holds another row at its
position: a database put back to an earlier moment, with an older signature beside it, is seen there.

**`beffroi:chain:sign-anew`** links one chain again as the database holds it, and signs it, once a person has
read what its check found: whatever was changed, added or removed before cannot be told from the rest afterwards,
so it prints what the whole walk finds first, and refuses until the slug of the tenant is typed back. The act
`tenant.chain_signed_anew` names the positions linked again. It rewrites the links of the chain, which a role
granted by [`beffroi:database:grant`](#the-role-of-the-database) cannot do: on a deployment whose processes run
as such a role, it is run with `DATABASE_URL` naming the role that owns the tables.

``` bash
bin/console beffroi:chain:sign-anew journal default
```

A chain found broken is cut by no retention until one of two things is done: the database and the key storage
restored from the same backup, or the chain signed anew.

## The role of the database

``` bash
bin/console beffroi:database:grant beffroi_runtime
```

**`beffroi:database:grant`** grants the role the server and the worker connect as what they serve, and on the
chained records nothing but appending: no update and no deletion of `beffroi_journal`, `beffroi_claim_change`,
`beffroi_disclosure` and `beffroi_chain_link`, no deletion of `beffroi_tenant`, and the function the
retentions forget through. It runs as the role that owns the tables, after the migrations, and prints the
statements it played. It refuses a role named otherwise than in lowercase letters, digits and underscores, the
role it runs as, and a database other than PostgreSQL. The server of the image runs it at every start, after
the migrations, when `BEFFROI_MIGRATIONS_DATABASE_URL` names a role other than the one of `DATABASE_URL`
([persistence](persistence.md#the-role-the-processes-connect-as)).

## The doctor

``` bash
bin/console beffroi:doctor
```

The doctor reads and writes nothing, so it is safe on a provider serving traffic. It looks at every point
before it answers, prints one line per point, explains the ones it does not answer for, and fails when one is
red, so a deployment pipeline can ask the question. A point is a class tagged `beffroi.doctor_check`, so a
point added is a class added; a run with nothing tagged fails rather than answering for nothing.

The application tags five points, looked at in this order.

- `App\Doctor\ClientsSignedWithHeldKeys` reads every client of the tenant, declared or registered, and is red
  when one receives its ID tokens, its authorization responses or its UserInfo responses signed with an
  algorithm the tenant holds no active key for, the default one counting for a client that names none: the
  first of them it asks for would fail with a server error. Its finding names the client, the documents and the
  algorithm, and says that `bin/console beffroi:keys:generate --algorithm=<algorithm>` draws the missing key.
- `App\Doctor\ChainHoldsTogether`, once for each [chain of records](#the-chains-of-records), `journal`,
  `claim_history` and `disclosures`, checks the last signature of the chain, the row it signs, the first row kept
  and the rows written since, in a time that does not grow with the chain. It is red on a signature that does not
  verify, at the first position that does not follow among the rows it reads, on rows outside a chain nobody has
  signed yet, and on a break the daily walk of the whole chain found, until the chain is restored or signed anew. It is red as well when the schedule has
  stopped: the chain last signed more than two passes ago, ten minutes, its first row waiting as long with no
  signature, or the chain last walked whole more than two days ago.
- `App\Doctor\NotificationsLanePatience` says whether the lane a logout token is sent on is retried on the
  schedule the token is written for, the one `beffroi.back_channel_logout` sets.

On a deployment that holds a key for every algorithm its clients are signed with, and keeps the lane of
notifications the application declares, `async_notifications`, with the defaults of that section, the first
point and the last read:

``` text
 [ok] Clients: the keys their documents are signed with
      The tenant "default" holds an active key for every algorithm it signs the documents of its clients with.

 [ok] Back-channel logout: how long a logout token is retried
      A logout token is retried on "async_notifications" for 3 minutes 20 seconds and stops being verifiable after 3 minutes 55 seconds, both read from the schedule this provider publishes (App\Messenger\NotificationRetryPolicy): a client that is restarting is reached, and nothing arrives after the "exp" of the token has passed or after the key that signed it has left the JWK Set.
```

The two figures are the budget a logout token is written for; [Messenger](messenger.md#what-the-application-writes)
says what that budget bounds. The last point is red when the notifications are routed to a lane retried on
another schedule, or to no lane at all.

[:beffroi-arrow-right: Messenger](messenger.md)
