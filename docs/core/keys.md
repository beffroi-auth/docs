---
title: Keys
description: The keys of a tenant: what each one is for, sealed by the key management service, published or kept, and rotated without an outage.
---

# Keys

A tenant signs and decrypts with keys it owns, each one sealed by a key management service: the private half is
sealed before anything is written, and the master key that seals it never leaves the service. A key has an
algorithm, which says what it is for, a status and the dates of its life, and the JWK Set publishes the ones a
client may need, a key staged for a rotation and a key still retiring among them.

A rotation is therefore not an outage: the new key is published before it is used, and the old one stays
published until nothing it signed can still arrive.

## What a key is for

The algorithm of a key is what it is for, and the `use` its JWK publishes (RFC 7517 §4.2) is checked against
the algorithm rather than trusted: a key that signs never opens anything, and a key that is encrypted to never
signs. A tenant holds one active key per algorithm.

| Algorithm | Use | Published | What it is |
|---|---|---|---|
| `RS256` | `sig` | In the JWK Set | The default signature algorithm, the first wired: what signs a self-contained access token and a signed introspection response, and the ID token or the signed authorization response of a client that registered no algorithm for it, a logout token following the ID token. RSA, 3072 bits |
| `PS256` | `sig` | In the JWK Set | RSA, 3072 bits |
| `ES256` | `sig` | In the JWK Set | P-256 |
| `EdDSA` | `sig` | In the JWK Set | Ed25519 |
| `ECDH-ES+A256KW` | `enc` | In the JWK Set | What a client encrypts to the provider with, over P-256 |
| `RSA-OAEP-256` | `enc` | In the JWK Set | The same, RSA, 3072 bits |
| `MESSAGE-SEAL` | `enc` | Kept | What the body of every message written to a transport is sealed to, as a JWE under `ECDH-ES+A256KW` and `A256GCM` |
| `VAPID` | `sig` | Kept | The key a browser is handed when it subscribes to web push (RFC 8292), wired where web push is turned on |
| `SAML-SIGNING` | `sig` | Kept | The SAML key of the tenant, which both SAML roles sign with and whose certificate their metadata carry, wired where a SAML role is turned on |
| `SAML-ENCRYPTION:` and an entity ID | `enc` | Kept | The key one [upstream SAML identity provider](../saml/upstream-identity-providers.md#the-key-it-encrypts-for) encrypts for, one per provider declared |

An RSA key is drawn at 3072 bits, 2048 being the floor the code refuses to go under. A kept key is a key of the
tenant like the others, with the same custody, the same statuses and the same commands, and none of them appears
in the JWK Set: a key the JWK Set published would be one any reader of it could encrypt to or verify against.
The key of a capability a deployment turns off stays where it is, served, rotated and drawn by nothing, and is
back in service as it was the day the capability is turned on again.

**The message key is the first key of a tenant.** A body is sealed to it or not written at all, and every other
key announces its own staging on a transport, so a tenant is given that one before any other:

``` bash
bin/console beffroi:keys:generate --algorithm=MESSAGE-SEAL
bin/console beffroi:keys:generate
```

The second line draws a key of the default signature algorithm. `--algorithm` names any other, among those the
deployment is wired with.

## Custody

The private half of a key is drawn in the process, sealed in an envelope by the key management service the
configuration names, and only then written; the master key never leaves that service, and the private key never
reaches it. The envelope is bound to the tenant, and told from the envelope of a TOTP secret: sealed for one
tenant, it does not open for another. The `kid` is the RFC 7638 thumbprint of the public key, SHA-256, so the same material carries the same
name whoever drew it, and one material is the key of one algorithm: a second algorithm under a `kid` already held
is refused.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    keys:
        kms: op
        key_id: '%env(BEFFROI_KMS_KEY_ID)%'
```

| Option | Default | What it decides |
|---|---|---|
| `kms` | required | The key management client that seals the keys, an entry of `key_management.clients` |
| `key_id` | required | The master key of that service the keys are sealed under, `{tenant}` standing for the slug of the tenant, one master key each |
| `data_key_secrets` | `['%kernel.secret%']`, the secret of the kernel | The secrets every data key of [personal data](personal-data.md#the-data-keys-of-a-tenant) is bound to its row under, the first binding a new one |
| `storage` | `%kernel.project_dir%/var/keys` | The directory of the sealed keys, one JSON file per key under the slug of its tenant, written through a sibling file renamed into place |
| `jwks_max_age` | `300` | How long a client may cache the JWK Set, in seconds, which the staging delay derives from |
| `staging_delay` | `jwks_max_age` plus sixty seconds | How long a new key is published before it is used, in seconds |
| `age` | `7776000`, ninety days | How long a key works before a successor is staged behind it, in seconds, counted from its activation |

[Key management](../symfony-bundle/key-management.md) says how the clients are declared. A process opens a key
once and keeps it open for as long as it is the key that answers, so a worker that serves many requests asks the
service once per key, where a process rebuilt at each request asks at each request. A key another has replaced,
or that has retired, is let go.

## The life of a key

| Status | Published | What it does | What moves it on |
|---|---|---|---|
| `staged` | Yes | Signs nothing yet; a JWE a client encrypted to it opens | Its staging delay elapsing, or `beffroi:keys:activate` |
| `active` | Yes | The one key of its algorithm in use: the key that signs, for a key of the `sig` use | A successor taking over |
| `retiring` | Yes | Signs nothing; what it signed still verifies, and what was encrypted to it still opens | Its retirement date passing, or `beffroi:keys:retire` |
| `retired` | No | Nothing: a JWS naming its `kid` is refused, a JWE encrypted to it does not open | Nothing, retired is the last status |

"Published" is said of the algorithms the JWK Set carries; a kept key goes through the same four statuses
without ever being published. The key a body is sealed to is the newest `MESSAGE-SEAL` key in service, a staged
one included, since nobody reads the JWK Set for it.

**A retiring key stays for its window.** When a key takes over, the one it replaces starts retiring until the
longest lifetime among what is bound to a key of its use has passed. For a key of the `sig` use, that is the ID
token, the self-contained access token where a client of the tenant is registered for that shape, the logout token
while its delivery may still be tried where back-channel logout is served, and the signed authorization response
where a response mode that signs is served. For a key of the `enc` use, that is the longest a request object is
accepted to stand and the lifetime of a pushed authorization request. `beffroi:keys:list` shows the date each
retiring key is due.

## Rotating without an outage

``` bash
bin/console beffroi:keys:rotate
```

`beffroi:keys:rotate` draws a new key of its algorithm, the default signature algorithm unless `--algorithm` names
another, and publishes it at once. The key in use stays the active one until the staging delay has elapsed, and a
client that cached the JWK Set has seen the new key before anything is signed with it. Then the new key takes
over, and the old one retires with its window.

| Option | What it changes |
|---|---|
| None | The new key is staged and takes over once its staging delay has elapsed |
| `--now` | The new key takes over at once. A relying party whose copy of the JWK Set is younger than sixty seconds refuses the new tokens, or encrypts to the old key, until its copy is that old |
| `--compromised` | The new key takes over at once, and the active one leaves the JWK Set in the same call, with no window: nothing it signed is honoured afterwards |

A tenant that holds no active key of the algorithm gets the new key active at once, whatever the options, since
nobody caches an empty JWK Set. `beffroi:keys:generate` is `beffroi:keys:rotate --now` under another name, for the
first key of a tenant.

| Command | What it does |
|---|---|
| `beffroi:keys:activate <kid>` | A staged key takes over before its delay has elapsed; the active one starts retiring |
| `beffroi:keys:retire <kid>` | A retiring key leaves the JWK Set, once its retirement date has passed |
| `beffroi:keys:retire <kid> --force` | The same before its date, for a key nothing bound to can arrive any more, or after a compromise |
| `beffroi:keys:retire --due` | Every retiring key past its date, which is what the timed step does |

The active key is never retired by hand: a tenant without an active key signs nothing, so a rotation comes
first. Each step writes its act to the journal, `tenant.key_staged`, `tenant.key_rotated` and `tenant.key_retired`,
and the event of a retirement carries why: `due` when its date had passed, `forced` when it had not, `compromised`
after `--compromised`.

## What time does on its own

A timed step runs every minute, on the `scheduler_beffroi` transport the worker consumes, and does three things in
an order that lets one tick finish what the previous one began:

1. **A key that has worked for its age gets a successor**, staged and not activated, when nothing of its algorithm
   is staged already. Nobody has to ask, and a deployment nobody watches does not sign with the same key for ever.
2. **A staged key whose delay has elapsed takes over**, and the key it replaces starts retiring.
3. **A retiring key past its date leaves the JWK Set.**

The age has to be longer than the retirement window of the use of the key, or every rotation would leave one more
key in the JWK Set: the step refuses an age that is not, the first time a key reaches it, rather than staging a
successor.

`beffroi:keys:list --check` opens the active and the staged keys with the key management service, says of an
active key whether it has worked past its age and whether a successor is staged behind it, and fails on a key
that does not open, or on an active key past its age with nothing staged: from outside, that is what a schedule
that has stopped looks like. `--all` lists the retired keys too.

## The figures of a family

How long a new key is staged and how long it works is the schedule its family declares, so a key that costs
somebody a step at every rotation is not rotated at the pace of one nobody sees:

| Family | Staged for | Works for | Set by |
|---|---|---|---|
| The keys of the JWK Set, and `MESSAGE-SEAL` and `VAPID` beside them | the `max-age` of the JWK Set plus sixty seconds, 360 seconds by default | ninety days | `beffroi.keys.staging_delay`, `beffroi.keys.age` |
| `SAML-SIGNING`, and the `SAML-ENCRYPTION` key of each upstream identity provider | seven days | 365 days | `beffroi.saml.identity_provider.staging_delay`, `age` |

The SAML keys are staged for a week because their next certificate is published in metadata that service
providers fetch once a day, and that some administrators upload by hand. [The identity
provider](../saml/identity-provider.md#a-rotation-without-an-outage) says why each figure is what it is.

## When the service loses a key

A key management service that does not answer, or refuses, makes the request that needed a key answer `503`
with a `Retry-After` of ten seconds, and the act `kms.unavailable` is written: nothing was refused to anybody,
and the same request is served once the service is back. A service that lost its master key leaves envelopes
nothing opens. `beffroi:keys:list --check` names each active or staged key it cannot open, with its algorithm.
For a dead active key, the way out is a rotation per algorithm, `beffroi:keys:rotate --now --algorithm=<name>`:
the new key is sealed under the master key the service holds and takes over at once, and the dead key retires
with its window, its public half still verifying what it signed. Nothing is deleted. A rotation leaves a dead
staged key where it is, and the timed step activates it once its delay has elapsed, as it activates any staged
key.
