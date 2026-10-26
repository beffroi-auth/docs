---
title: Operating it
description: What a deployment runs, what time runs on its own, rotations, data keys, failures, a compromised key, and what to back up.
---

# Operating it

A provider is operated, not installed once: keys rotate, data keys are rewrapped, migrations run, backups are
taken and restored. Each of those has a command, and each command says what it did. The commands are
[the console commands of the bundle](../reference/console-commands.md), run with `bin/console` in a container
of the image, or with `castor console` on the development stack.

## At every deployment

1. **The migrations** are played by the HTTP server each time it starts, before it serves anything. A process
   that booted before a migration changing the type of a column reads that column with the type it booted
   with, and a worker runs for an hour, so a migration played by hand is followed by a restart of the server
   and of the workers. `castor console` does that on the development stack whenever the command it runs is
   the migration.
2. **The row of the tenant** follows the configuration: `beffroi:tenant:synchronize` creates it, or writes on
   it the name, the `acr` policy, the look and the claims its people may change of themselves that the
   configuration says, then prints the row. The provider serves nothing while the row and the configuration
   disagree. A changed issuer is refused: the issuer of a tenant does not change, every token issued so far
   names it.
3. **Two questions for the pipeline**, both of which write nothing and fail when the answer is no:
   `beffroi:keys:list --check` opens the keys in use and the ones about to be with the key management
   service, and fails on one it cannot open or that has worked past its age with nothing staged behind it;
   `beffroi:doctor` says whether the deployment holds together, one line per point it looks at.

## What time does on its own

Some of it is not operated at all, because time does it: one timed step per thing that comes round, handed to
the lane of the writes like any other, so a deployment that runs [the worker](deployment.md#the-worker) runs
them. A step that forgets reads a bounded number of rows and leaves the rest to the next run, and logs a line
only when it did something.

| Every | What it does |
|---|---|
| minute | Advances the lifecycle of the keys: stages a successor for a key that has worked its age, activates a staged key whose delay has elapsed, retires a key past its date |
| hour | Drops the clients that registered themselves and that nobody uses any more, forgets the archives past their week, drops the rows that can no longer do anything, and reads again the metadata of the SAML service providers and upstream identity providers |
| day | Forgets the acts of the journal past their retention, with what a client was given at each, and the changes of a record past theirs |
| week | Refreshes the GeoLite2 databases of addresses, which is the cadence MaxMind publishes them at |

## Keys

**A rotation asks nothing of anybody.** A key works for an age, ninety days, or a year for the SAML signing
key, and the step of the minute stages its successor; the successor is published for the staging delay, 360
seconds with the values of the application or seven days for the SAML key, then takes over, and the key it
replaces stays published while what is bound to it may still arrive.

By hand, the same thing is three commands:

``` bash
bin/console beffroi:keys:rotate
bin/console beffroi:keys:activate <kid>
bin/console beffroi:keys:retire --due
```

`beffroi:keys:rotate` stages a key of the default signature algorithm, or of the one `--algorithm` names, and
says when it takes over. `beffroi:keys:activate` makes a staged key the active one before its delay has
elapsed. `--now` on the rotation does both at once: a relying party whose copy of the JWK Set is younger than
sixty seconds then refuses the new tokens, or encrypts to the old key, until its copy is that old.

### A compromised key

``` bash
bin/console beffroi:keys:rotate --compromised
```

The new key takes over at once, and the compromised one leaves the JWK Set with no window: nothing bound to it
is honoured from then on. `--algorithm` names the key when it is not one of the default signature algorithm.
A key that is already retiring is taken out of the JWK Set before its date by
`beffroi:keys:retire <kid> --force`.

## Data keys

Personal data is sealed under a data key per tenant and per family of columns, and the data keys are wrapped
by the master key of the tenant.

| Command | What it does |
|---|---|
| `beffroi:data-keys:list` | Lists the data keys of the tenant by scope, with when each was minted, the master key that wraps it and the key management client that opens it. Reads only, and never opens a key |
| `beffroi:data-keys:rewrap --to=<client>` | Wraps the data keys of the tenant with another client from then on, or with another master key of the same one, `--from` narrowing it to the keys one client holds and `--dry-run` listing what would move. No sealed value is read or rewritten, and the master key is derived from `BEFFROI_KMS_KEY_ID` rather than asked for. Each key it moves is bound again under the first secret of `beffroi.keys.data_key_secrets` |
| `beffroi:data-keys:destroy` | Erases the data keys of the tenant, which makes every personal datum it had sealed unreadable for good. It asks for the slug of the tenant to be typed back, and cannot be undone |

The clients of this application are `op`, which every key of the tenant is sealed with, and `second`, which is
built from `BEFFROI_KMS_DSN_SECOND` when that variable names one. Nothing schedules a rewrap: a person asks
for it.

The data keys are bound under `APP_SECRET`, which `beffroi.keys.data_key_secrets` takes as long as
`config/packages/beffroi.yaml` names no secret of its own. A new value replaces it in the three steps of
[personal data](../core/personal-data.md#rotating-the-secret-that-binds-them): `%kernel.secret%` first and the
previous value second in `beffroi.keys.data_key_secrets`, given to every process; `beffroi:data-keys:rewrap`
towards the client that wraps the keys, `op` unless they were moved; then the previous value dropped. Changed
alone, it leaves every sealed value unreadable.

## The data downloaded

| Command | When it is run by hand | Its timed step |
|---|---|---|
| `beffroi:geoip:refresh` | The day a licence key is named, and to read why a refresh was refused | Every week |
| `beffroi:saml:service-provider:refresh`, `beffroi:saml:identity-provider:refresh` | For the first reading of a peer just declared, and to read why a document was refused | Every hour |
| `beffroi:webauthn:mds-refresh`, `beffroi:webauthn:mds-import` | To fill the FIDO metadata an attestation is checked against | None |

## When something fails

**`beffroi:doctor` is what to ask first.** It reads, writes nothing, and is safe on a provider serving
traffic. What it looks at is what is wired, and in this application that is one point: whether a logout
token is retried for as long as it stays verifiable. A deployment that sends the notifications to a transport
of its own, retried on another schedule, keeps a provider that works and logout tokens a client may refuse
when they arrive late, after a rotation or after the client restarts, which nothing else shows.

**A message that fails is tried again, then kept.** The three lanes of the provider's own writes retry it on
the numbers the bundle prepends; the lane of the notifications retries it on the schedule of the back-channel
logout, which is also how long a logout token stays verifiable.

| Lanes | Retries | First wait | Multiplier | Longest wait |
|---|---|---|---|---|
| `async_priority_high`, `async_priority_medium`, `async_priority_low` | 4 | 1 second | 4 | 30 seconds |
| `async_notifications` | 6 | 2 seconds | 3 | 60 seconds |

What is still failing after that lands in the failure transport, `failed`, a table of the database. Its body
stays sealed there; the class of the message, its stamps and its tenant are in the clear, so that
`messenger:failed:show` names a failed message, dates it and says why without opening it.

**A key management service that does not answer is a `503`.** Wherever a request needed it, the answer is
`503 Service Unavailable` with `Retry-After: 10`: nothing was refused to the person, counted against them or
forgotten, and the same request is served once the service is back. The outage is an act of the journal,
`kms.unavailable`, with the provenance of the request that met it. The worker does not start without a key
management service at all.

**A spent load budget is a `429`**, with a `Retry-After` and `Cache-Control: no-store`, and an act of the
journal, `load.budget_spent`.

## What to back up

One directory to back up, one key management service and one secret to keep.

| What | Where | What it holds |
|---|---|---|
| The database | PostgreSQL | Everything the model writes, the personal data sealed in their columns, and the data keys wrapped by the master key |
| The sealed keys | `var/keys` | One file per key of the tenant, and the pairwise salt of the tenant beside them, each sealed by the key management service |
| The master key | The key management service | What opens all of the above |
| The secret of the kernel | `APP_SECRET`, in the environment of every process | What every data key is bound to its row under: under another secret, the database opens no sealed value |

No command restores a deployment: a restore is the database and `var/keys` put back together, under the same
master key and the same `APP_SECRET`. The pairwise subjects of OpenID Connect and the persistent identifiers of SAML are computed from
the salt and never drawn, so they are the same after a restore that brings the salt back with the database. The GeoLite2
databases in `var/geoip` and the FIDO metadata in `var/webauthn` are written again by the commands that wrote
them.
