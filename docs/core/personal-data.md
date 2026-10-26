---
title: Personal data
description: What is sealed, what is indexed blind, the data keys of a tenant and what they cover, what leaves the process sealed, and the one operation that cannot be undone.
---

# Personal data

Personal data is sealed in its column with a data key of the tenant, itself wrapped by the master key of that
tenant in the key management service, so a database alone reads nothing. The lookups that must still work match a
blind index, a keyed tag of the value, rather than a readable column.

The data keys can be wrapped by another key management client while the provider serves sign-ins, and destroying
them is the one operation that cannot be undone. The same rule holds past the database: what the provider writes
to a transport leaves sealed too.

## What is sealed

Every class of the model that a row holds says, field by field, what it holds of a person: a personal datum sealed
under the data key of its table, a blind index of such a datum, or a field a dump gives away together with the
sentence that says why that gives nothing away. The suite of the bundle walks the schema against those
declarations, and refuses a column no declaration names, a declaration no column carries, and a field sealed under
the key of another table than its own.

| Family | What it seals |
|---|---|
| `user` | The username, the email address, the profile, the phone number, the postal address, and the source that created the person, which says which organisation they are of |
| `linked_identity` | The provider, the subject it gives the person, and the snapshot of what it said |
| `passkey_credential` | The name a person gave a passkey |
| `push_subscription` | The endpoint of a browser web push reaches, and the name a person gave it |
| `authentication_session` | Where a session was opened from and last seen from |
| `claim_change` | What a claim said before a person changed it, what it says after, and where the change came from |
| `journal` | Where each act came from |
| `personal_archive` | The archive a person asked for |
| `interaction` | The `login_hint` and the `id_token_hint` of an authorization request |
| `pushed_authorization_request` | The parameters a client pushed |
| `device_authorization_request` | Where a device authorization request came from |
| `backchannel_authentication_request` | The binding message of a backchannel request, and where it came from |
| `client` | What a registered client wrote of itself, what the registration policy wrote on it, and its secret |
| `disclosure` | What a client was given of a person: the scopes, the claims and the authorization details |
| `saml_service_provider`, `saml_upstream_identity_provider` | The metadata accepted for a SAML peer, whose contacts name people |

Each family is the name of its table without the `beffroi_` prefix. What stays readable is named as plainly, each
field with the sentence that says why it gives nothing away. Among them: the subject, a stable pseudonym that names a
person without saying anything about them; the tenant; dates, states and counts; digests and envelopes, which do
not open; what a browser, an authenticator or a client publishes anyway, such as the public key of a passkey;
identifiers drawn at random; the identifier of a client, and what a request asked of the protocol, such as its
scopes; what a session proved, which every token issued from it carries; the names of the groups of the tenant;
and the name of an act or of a claim, never its value.

A sealed column is binary in the database, whatever length its mapping states: that length is the one the model
checks of the value in clear. An option of the mapping that describes the stored value, such as `jsonb`, does not
apply to a sealed column, which holds a ciphertext no query of the database reads into.

!!! note "A ciphertext is bound to its tenant, not to its row"

    The authenticated data of every sealed value name the tenant, so a value of one tenant does not open for
    another, wherever it is found. They do not name the table, the column or the row: within one tenant and one
    family, a value moved into another row of the same column opens there.

## Blind indexes

A sealed column holds a different ciphertext for every write of the same value, so `WHERE username = ?` matches
nothing. The columns that are looked up carry a sibling instead: a keyed tag of the value under the index key of
the tenant, sixty-four hexadecimal characters, written in the same statement as the value it indexes, which is what
a lookup matches and what a unique constraint holds.

| Column | Read as | What matches on it |
|---|---|---|
| The username of a person | Byte for byte | A login, the console naming a person, the uniqueness of a username in the tenant |
| The email address of a person | The whole address in lower case, its local part included | A sign-in through an upstream provider, the first one or a later one that brings another address, which refuses an address another person holds |
| The provider of a linked identity | Byte for byte | Every lookup of a linked identity, beside the subject, and the uniqueness of a pair |
| The subject of a linked identity | Byte for byte | The sign-in through a provider, and an assertion of a trusted issuer |

**A tag says which rows share a value and never what the value is.** That is the one thing a column gives up by
carrying one, which is why only these four do: a username, an address and a subject are high-entropy and looked
up by equality. The provider is not: a tenant federates from a handful of them, so its column says which rows
share one and the largest group is guessable. It carries a tag because a linked identity is looked up, and held
unique, by the pair.
`gender`, `locale`, `zoneinfo` and `birthdate` carry none.

The columns derive their tags under subkeys named after themselves, so a username that happens to be an address
does not share the tag of that address. A deployment whose projection of the username or of the address changed
derives those tags again for every person of the tenant, in pages of a hundred, a second run writing nothing; the
tags of the linked identities are not re-derived by it:

``` bash
bin/console beffroi:user:reindex
```

## The data keys of a tenant

| Scope | What it covers | Its life |
|---|---|---|
| `<slug>.<family>`, one per family of the table above | Every sealed value of that family | Minted at the first write of the family. After thirty days, the next write mints another, and the older keys stay to open what they sealed |
| `<slug>.blind_index` | Every blind index of the tenant | Minted at the first lookup or write that needs it, never replaced: every tag already written was derived under it |

A data key is 32 bytes, AES-256-GCM, held wrapped in the table `beffroi_data_key` by the master key the
configuration names for the tenant, `beffroi.keys.key_id` resolved for its slug, the one its own keys are sealed
under. A process opens each data key once and keeps it, so the key management service is asked once per key and not
once per value. Nothing in the ordinary life of a tenant removes a data key: a new key is minted beside the ones
there, and a rewrap changes what protects a key and not the key.

Each row is also bound to its reference and its scope: an HMAC-SHA256 of the two, under a key derived from the
data key and from a secret the database does not hold. A row edited, copied under another reference or scope,
or written into the table by whoever can write the database opens nothing, even when the key it carries is
wrapped under a master key the provider may use. The secrets are those of `beffroi.keys.data_key_secrets`, the
secret of the kernel unless the configuration names others, one list for the whole deployment: the first one
binds a new row, and a row bound under any of them opens. A row bound under a secret that is no longer listed
opens nothing, and neither does any value sealed under its key.

``` bash
bin/console beffroi:data-keys:list
```

It lists the keys of the tenant by scope, each with its reference, when it was minted, the master key that wraps
it, the key management client that opens it and whether it is the current key of its scope or a retired one. It
never opens a key. A tenant that holds none has sealed nothing yet, and the command says which families there are.

## Wrapping them with another client

``` bash
bin/console beffroi:data-keys:rewrap --to=second --dry-run
bin/console beffroi:data-keys:rewrap --to=second
```

| Option | What it says |
|---|---|
| `--to` | The key management client that wraps the data keys the tenant holds, a name of `key_management.clients` |
| `--from` | Move only the keys that client wraps; all of them when it is left out |
| `--dry-run` | List what would move, and write nothing |

The master key is not asked for: it is the one the configuration resolves for the slug of the tenant, so an
operator cannot type the master key of another tenant. No sealed value is read and none is rewritten, every
ciphertext going on referring to the same data key, the index key included. The provider serves while the keys
move: a read resolves the client and the master key from the row of the data key it names, whatever wrapped it.
The command moves the keys the tenant holds when it runs; a key minted afterwards, the first of a family or the
next one after thirty days, is wrapped by the client `beffroi.keys.kms` names. The act
`tenant.data_keys_rewrapped` goes to the journal, and its event carries the client the keys were taken from when
`--from` named one, the client and the master key that wrap them afterwards, how many keys moved, and how many
scopes the tenant holds. One tenant at a time, by hand: nothing schedules it.

The keys of the tenant itself, its signing and encryption keys, are sealed apart, one file each, and no command
rewraps them: a key sealed by another service is replaced by a [rotation](keys.md#rotating-without-an-outage).

## Rotating the secret that binds them

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    keys:
        data_key_secrets:
            - '%env(DATA_KEY_SECRET)%'           # the new secret, which binds
            - '%env(PREVIOUS_DATA_KEY_SECRET)%'  # the one it replaces, still read
```

1. Write the new secret first and keep the one it replaces second, and give that configuration to every
   process of the deployment before going on: a process that does not list a secret opens no row bound under
   it. The two variables are the deployment's own, and the bundle reads none of them by name.
2. Run `beffroi:data-keys:rewrap` with `--to` naming the client that already wraps the keys of the tenant, the
   one `beffroi.keys.kms` names unless a rewrap moved them. Every key is bound again under the first secret as
   it moves, and its value and every ciphertext sealed under it stay as they are.
3. Drop the old secret once the command has moved every key.

The secret of the kernel is replaced the same way when the configuration names no secret of its own,
`%kernel.secret%` written first and its previous value second: changed alone, it leaves every sealed value of
the deployment unreadable.

## Destroying them

``` bash
bin/console beffroi:data-keys:destroy example
```

The command erases every data key of the tenant, the index key included, and the slug has to be typed back:
without it, or with another one, it says how many keys over which scopes it would erase, and erases nothing. There
is no `--force`. Afterwards every column the keys sealed holds a ciphertext nothing opens, by anybody, and the rows
are still there: what is gone is the means of reading them. The act `tenant.data_keys_destroyed` goes to the
journal, and its event carries how many keys over how many scopes were erased, which is what cannot be counted
afterwards. It cannot be undone.

## Past the database

**What leaves the process on a transport leaves sealed.** The body of every message the provider writes to a
transport, an event, a command or a notification, is a JWE to the `MESSAGE-SEAL` key of the tenant, under
`ECDH-ES+A256KW` and `A256GCM`, its protected header naming the tenant, so a body moved to the queue of another
tenant does not open there. The serializer that seals it is the default one of every transport, the failure
transport included, so a broker, the table of a transport and a backup of either hold nothing readable. What stays
in the clear on a message is what makes a failed one readable: the class of the message, its stamps and the slug of
the tenant it was written under, nothing of a person among them.

The journal of the acts, what a client was given at each of them, what a record used to say and the archive a person
asks for are sealed where they sit like every other column of a person.

## How long it is kept

| What | Kept for | Forgotten by |
|---|---|---|
| An act of the journal, and what a client was given at it | `beffroi.journal.retention` days, 180 by default | A daily step |
| A change of a claim | `beffroi.history.retention` days, 180 by default | A daily step |
| The archive a person asked for | Seven days from the moment it was asked for, a figure in the code | An hourly step |

**The archive is the one file in which all of it stands in clear at once**, so it is held by rules rather than by
settings: it is sealed at rest in a family of its own, it expires a week after it was asked for, whether it was
built or not, and it leaves under a passphrase of the person's choosing when they ask for one, sixteen characters
at the least.

[:beffroi-arrow-right: Your data, on the account pages](../symfony-bundle/account.md#your-data)
