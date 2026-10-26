---
title: Console commands
description: What the commands of the bundle need explained beyond their help: the rotation of a key, the data keys, and the doctor.
---

# Console commands

The bundle adds the commands for the tenant, the people and their journal, groups, clients, keys, data keys,
the metadata of SAML peers, the databases of addresses and the metadata of FIDO. [The
reference](../reference/console-commands.md) lists every one of them; `bin/console <command> --help` gives its
arguments and options. This page explains the ones a help screen does not: the rotation of a key, the data
keys, and the doctor.

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

## Rotating a key

A key of the tenant is staged, then active, then retiring, then retired. Of the keys it publishes, the JWK Set
carries the first three, so a relying party sees a key before anything is signed with it and keeps verifying
it once another has taken over. [Keys](../core/keys.md) says what each key of a tenant is for.

| Command | What it does |
|---|---|
| `beffroi:keys:generate` | Draws a key, seals it and makes it the active one of its algorithm at once. The right command for a tenant that has no key of that algorithm, and a rotation with no staging delay on one that has |
| `beffroi:keys:rotate` | Stages a key: published at once, active once the staging delay has elapsed. On a tenant that has no active key of the algorithm, the key is active at once |
| `beffroi:keys:activate <kid>` | Makes a staged key active before its delay has elapsed |
| `beffroi:keys:retire <kid>` | Takes a retiring key out of the JWK Set once its retirement date has passed, or before it with `--force`; `--due` retires every key past its date |
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
the one that activates it.

| Figure | Default | Set by |
|---|---|---|
| The staging delay, how long a new key is published before it signs | `jwks_max_age` plus sixty seconds: 360 seconds with the default `jwks_max_age` of 300 | `beffroi.keys.staging_delay` |
| The age, how long a key works before a successor is staged, counted from its activation | 90 days | `beffroi.keys.age`, in seconds |
| The retirement window, how long a replaced key stays published | The longest lifetime of what is bound to a key of that use: the ID tokens, access tokens, signed authorization responses and logout tokens for a key that signs, the request objects and pushed requests a client may still be encrypting for a key it encrypts to | Read from those lifetimes, never set on its own |

The sixty seconds are the cooldown of Symfony's `oidc_login`, which fetches the JWK Set again on a `kid` it does
not know only once its copy is that old: they cover a relying party whose copy came late through a shared
cache. An age that is not
longer than the retirement window of its use is refused at the first tick that reaches it, since every rotation
would otherwise leave one more key in the JWK Set. The SAML signing key has figures of its own, seven days of
staging and a year of age by default, under [`beffroi.saml.identity_provider`](../saml/identity-provider.md).

### Rotating by hand

**`--now` skips the staging delay.** The new key signs at once and the previous one starts retiring: a relying
party whose copy of the JWK Set is younger than sixty seconds refuses the new tokens, or encrypts to the old
key, until its copy is that old. It is for an operator who knows every relying party is cold.

**`--compromised` leaves no window.** The new key takes over at once and the compromised one leaves the JWK
Set at the same moment: nothing bound to it is honoured from then on.

``` bash
bin/console beffroi:keys:rotate --compromised --algorithm=RS256
```

**`beffroi:keys:retire --force`** takes a retiring key out before its date, after a compromise or when
everything bound to it is known to have expired; the journal says it was retired before its date.

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
protected, and every ciphertext goes on naming the same key.

``` bash
bin/console beffroi:data-keys:rewrap --to=second --dry-run
bin/console beffroi:data-keys:rewrap --to=second --from=op
```

- `--to` names the client of `key_management.clients` that wraps the keys from now on, and the command lists
  the clients of the deployment when it is missing.
- `--from` moves only the keys that client holds; all of them without it.
- `--dry-run` lists what would move and writes nothing.

The master key is the one `beffroi.keys.key_id` gives the tenant, resolved from the configuration and never
asked for: an operator who had to type it could type the one of another tenant. It moves one tenant, the one
of the configuration, and nothing schedules it.

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

## The doctor

``` bash
bin/console beffroi:doctor
```

The doctor reads and writes nothing, so it is safe on a provider serving traffic. It looks at every point
before it answers, prints one line per point, explains the ones it does not answer for, and fails when one is
red, so a deployment pipeline can ask the question. A point is a class tagged `beffroi.doctor_check`, so a
deployment adds one by adding a class; a run with nothing tagged fails rather than answering for nothing.

The bundle tags one point: whether the lane a logout token is sent on is retried on the schedule the token is
written for, the one `beffroi.back_channel_logout` sets. On a deployment that keeps the lane of notifications
the bundle declares, with the defaults of that section, the run reads:

``` text
 [ok] Back-channel logout: how long a logout token is retried
      A logout token is retried on "async_notifications" for 3 minutes 20 seconds and stops being verifiable after 3 minutes 55 seconds, both read from the schedule this provider publishes (Beffroi\Bundle\Messenger\NotificationRetryPolicy): a client that is restarting is reached, and nothing arrives after the "exp" of the token has passed or after the key that signed it has left the JWK Set.
```

The two figures are the budget a logout token is written for; [Messenger](messenger.md#what-the-application-writes)
says what that budget bounds. The point is red when the notifications are routed to a lane retried on another
schedule, or to no lane at all.

[:beffroi-arrow-right: Messenger](messenger.md)
