---
title: Console commands
description: Every command the bundle adds, what it does, and whether it writes.
---

# Console commands

Every command of the bundle is prefixed `beffroi:`, and those that act on identity act on the tenant the
configuration names. A command that reads is never the command that writes: `beffroi:user:show` reads,
`beffroi:user:profile` writes, and they are two classes.

Run `bin/console beffroi:<group>:<command> --help` for the arguments and the options of one of them; the
table below is the map.

## The deployment and the tenant

| Command | What it does |
|---|---|
| `beffroi:doctor` | Say whether this deployment holds together: one line per point looked at, and what to do about the ones it does not answer for. Reads and writes nothing, so it is safe on a provider serving traffic, and it fails when a point is red so a deployment pipeline can ask the question too. |
| `beffroi:tenant:synchronize` | Write the row of the tenant of the configuration: created, renamed, or left alone. |

What `beffroi:doctor` looks at is what is wired, one class per point, so a deployment that adds a point
adds a class. It looks at every one of them before it answers: a doctor that stops on the first thing that
is broken never reaches the second.

## Users, their credentials and what they agreed to

| Command | What it does |
|---|---|
| `beffroi:user:applications` | List the applications a user agreed to, with what each one holds of them and what it has asked that is still waiting. |
| `beffroi:user:create` | Create a user of the tenant; give them a password with beffroi:user:set-password. |
| `beffroi:user:link` | Say that a user of the tenant is a given subject at an upstream provider; run again to refresh it. |
| `beffroi:user:profile` | Describe a user with the standard claims of OIDC Core section 5.1; what is not said is cleared, a run that says nothing writes nothing. To read a user, see beffroi:user:show. |
| `beffroi:user:revoke-consent` | Take back the consent a user gave a client, and the access it holds; the next authorization request asks again. |
| `beffroi:user:revoke-credential` | Revoke a credential of a user by its identifier; the credential stays listed as revoked. |
| `beffroi:user:revoke-session` | End a session of a user by its identifier; the relying parties of that session are told by the back-channel. |
| `beffroi:user:sessions` | List the sessions open in the name of a user, with what each one proved and where it was last seen. |
| `beffroi:user:set-password` | Set or replace the password of a user, asked on the terminal or read from the standard input. |
| `beffroi:user:show` | Show a user: the identity, the standard claims that are set, and the credentials with their kind, identifier, name and dates. |

## Clients and initial access tokens

| Command | What it does |
|---|---|
| `beffroi:client:delete` | Delete a client that registered itself; a client declared in the configuration is refused. |
| `beffroi:client:list` | List the clients of the tenant: where each came from, when it was registered and when it was last used. |
| `beffroi:client:show` | Show a client of the tenant: where it came from, its dates, and what it registered. |
| `beffroi:client:token:issue` | Issue an initial access token for the tenant; the value is printed once and never again. |
| `beffroi:client:token:list` | List the initial access tokens of the tenant: what each has served, what it has left and whether it still authorises anything. |
| `beffroi:client:token:revoke` | Revoke an initial access token by its identifier; it authorises no registration from that instant. |

## Signing keys

| Command | What it does |
|---|---|
| `beffroi:keys:activate` | Make a staged key the active one of its algorithm before its staging delay elapsed; the key it takes over from starts retiring. |
| `beffroi:keys:generate` | Generate a key, seal it with the configured KMS and make it the active one of its algorithm at once; "beffroi:keys:rotate" is the rotation without an outage. |
| `beffroi:keys:list` | List the keys of the tenant with their use, status and dates: the published ones, or every key with `--all`; `--check` opens the keys in use, or about to be, with the KMS and fails on one it cannot open, or that has worked past its age with nothing staged behind it. |
| `beffroi:keys:retire` | Take a retiring key out of the JWK Set: one key by its identifier, before its retirement date with --force; or every key past its date with --due. |
| `beffroi:keys:rotate` | Stage a new key, sealed by the configured KMS and published at once; it takes over once the staging delay elapsed, or at once with --now; --compromised retires the previous key with no window. |

## Data keys

| Command | What it does |
|---|---|
| `beffroi:data-keys:destroy` | Erase the data keys of the tenant, which makes every personal datum it had sealed unreadable for good. Asks for the slug to be typed back. Cannot be undone. |
| `beffroi:data-keys:list` | List the data keys of the tenant by scope, with when each was minted, the master key that wraps it and the KMS client that opens it; reads only, and never opens a key. |
| `beffroi:data-keys:rewrap` | Wrap the data keys of the tenant with another KMS client from now on, or with another master key of the same one; --dry-run lists what would move. No sealed value is read or rewritten. |

## Addresses

| Command | What it does |
|---|---|
| `beffroi:geoip:refresh` | Download the GeoLite2 databases of addresses now, refuse what is not one of the editions the enrichment reads, and store them for the enrichment of a provenance; `--url` for a mirror or a database already unpacked. |

A timed step runs the same object once a week, which is the cadence the databases are published at, so the
command is for installing them the day a deployment subscribes and for reading why a refresh was refused.
A deployment that names no licence key downloads nothing and serves every flow with a provenance that says
an address and no place.

## Passkeys and FIDO metadata

| Command | What it does |
|---|---|
| `beffroi:webauthn:mds-import` | Store a metadata statement file (unsigned, trusted as the file is) next to the FIDO Metadata BLOB, for the keys of a manufacturer the service does not list or the authenticators of the FIDO conformance tools. |
| `beffroi:webauthn:mds-refresh` | Download the FIDO Metadata BLOB, verify its signature under the pinned root and store it for the passkey ceremonies; --url for another service, --root for another root. |

## What a command may not do

A command never bypasses a rule the protocol applies. It cannot mint a token for a user, cannot read a
signing key it is not allowed to open, and cannot read a personal datum the key management service refuses
to unseal. `beffroi:data-keys:destroy` is the one that cannot be undone, and it asks for the slug of the
tenant to be typed back before it runs.
