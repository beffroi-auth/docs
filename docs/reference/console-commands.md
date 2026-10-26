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
| `beffroi:tenant:login-floor` | Name the floor of every login of the tenant, and forget the credentials it forbids. |
| `beffroi:tenant:synchronize` | Write the row of the tenant of the configuration: created, renamed, or left alone. |

What `beffroi:doctor` looks at is what is wired, one class per point, so a deployment that adds a point
adds a class. It looks at every one of them before it answers: a doctor that stops on the first thing that
is broken never reaches the second.

`beffroi:tenant:login-floor` takes the name of a predicate, `single_factor`, `two_factors`,
`phishing_resistant` or `phishing_resistant_hardware`, and writes it on the row of the tenant rather than in
a file, since hardening a tenant is an act with a date. It asks before it runs, because every credential the
floor reads nothing of is forgotten, its secret and its row: under `phishing_resistant`, the passwords, the
one-time codes and the backup codes of every person go. Lowering the floor afterwards gives nobody back what
was forgotten. [The floor of its logins](../core/tenants.md#the-floor-of-its-logins) says what it changes.

## Users, their credentials and what they agreed to

| Command | What it does |
|---|---|
| `beffroi:user:applications` | List the applications a user agreed to, with what each one holds of them and what it has asked that is still waiting. |
| `beffroi:user:create` | Create a user of the tenant; give them a password with beffroi:user:set-password. |
| `beffroi:user:enrolment-ticket` | Issue the link that lets a person pose their first passkey, and print it. |
| `beffroi:user:journal` | List the acts of a user over a period, with the application each one was done on behalf of; for answering a request about what happened in their name. |
| `beffroi:user:link` | Say that a user of the tenant is a given subject at an upstream provider; run again to refresh it. |
| `beffroi:user:profile` | Describe a user with the standard claims of OIDC Core section 5.1; what is not said is cleared, except what the upstream provider that created the user holds, which is kept, and saying that otherwise is refused; a run that says nothing writes nothing. To read a user, see beffroi:user:show. |
| `beffroi:user:reindex` | Derive again the blind indexes of every person of the tenant, after the projection of one changed. |
| `beffroi:user:revoke-consent` | Take back the consent a user gave a client, and the access it holds; the next authorization request asks again. |
| `beffroi:user:revoke-credential` | Revoke a credential of a user by its identifier; the credential stays listed as revoked. |
| `beffroi:user:revoke-session` | End a session of a user by its identifier; the relying parties of that session are told by the back-channel. |
| `beffroi:user:sessions` | List the sessions open in the name of a user, with what each one proved and where it was last seen. |
| `beffroi:user:set-password` | Set or replace the password of a user, asked on the terminal or read from the standard input. |
| `beffroi:user:show` | Show a user: the identity with the source that created it, the standard claims that are set, the credentials with their kind, identifier, name and dates, and the groups with the source of each membership. |

**An enrolment ticket** is for a person who has nothing to sign in with yet, on a tenant that signs its people
in by passkey and holds no password of theirs to give them. The link opens one enrolment of a passkey, once,
for seventy-two hours, and it is printed once: the row holds a hash of what it carries. Issuing another one
for the same person takes the first one away, and a disabled account gets none. It proves no login either:
the session that follows comes from the passkey that was just posed.

**The journal of a person** is read over `--from` and `--to`, two days in UTC, both included, narrowed with
`--act`, repeatable, and `--client`, and written as a table or, with `--format=json`, as the document a
request under article 15 of the GDPR is answered with. A period that reaches past what the deployment keeps is
answered with how long it keeps an act and the day that reaches, never with an empty table that looks
complete.

## Groups

| Command | What it does |
|---|---|
| `beffroi:group:create` | Create a group of the tenant, which the declaration of an upstream provider may map the groups it asserts to. |

No upstream provider creates a group: the declaration of one maps the values it asserts to groups that exist
already, by their name, and a value naming a group the tenant does not hold is no group.

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

`--algorithm` names the key a command acts on: a JWS algorithm for a key that signs tokens, a JWE key
management algorithm for a key clients encrypt to, or one of the keys the tenant keeps rather than publishing,
among them `SAML-SIGNING`, the key both SAML roles sign with, and `SAML-ENCRYPTION:` followed by the entity ID
of an upstream identity provider, the key that provider encrypts for. Left out, it is the default signature
algorithm.

## Data keys

| Command | What it does |
|---|---|
| `beffroi:data-keys:destroy` | Erase the data keys of the tenant, which makes every personal datum it had sealed unreadable for good. Asks for the slug to be typed back. Cannot be undone. |
| `beffroi:data-keys:list` | List the data keys of the tenant by scope, with when each was minted, the master key that wraps it and the KMS client that opens it; reads only, and never opens a key. |
| `beffroi:data-keys:rewrap` | Wrap the data keys of the tenant with another KMS client from now on, or with another master key of the same one; --dry-run lists what would move. No sealed value is read or rewritten. |

## Addresses

| Command | What it does |
|---|---|
| `beffroi:geoip:refresh` | Download the GeoLite2 databases of addresses now, refuse what is not one, and store them for the enrichment of a provenance; `--url` for a mirror or a file already unpacked. |

A timed step runs the same object once a week, which is the cadence the databases are published at, so the
command is for installing them the day a deployment subscribes and for reading why a refresh was refused.
A deployment that names no licence key downloads nothing and serves every flow with a provenance that says
an address and no place.

## SAML metadata

| Command | What it does |
|---|---|
| `beffroi:saml:service-provider:refresh` | Read the metadata of the service providers the configuration declares, or of one of them, and keep each document accepted; an expired or an older document is refused and the one accepted kept. |
| `beffroi:saml:service-provider:forget` | Forget the metadata accepted for a service provider, so that the next refresh registers it again as a first one; the refresh refuses older documents only against what is accepted. |
| `beffroi:saml:identity-provider:refresh` | Read the metadata of the upstream identity providers the configuration declares, or of one of them, and keep each document accepted; an expired or an older document is refused and the one accepted kept. |
| `beffroi:saml:identity-provider:forget` | Forget the metadata accepted for an upstream identity provider, so that the next refresh registers it again as a first one; the refresh refuses older documents only against what is accepted. |

A timed step runs the same refresh every hour for the peers of both roles, so the command is for the first
reading of a peer just declared and for reading why a document was refused. Forgetting is never a step of the
schedule: it is the one way back from a signed document an operator decides to stop holding the provider to.

[:beffroi-arrow-right: SAML 2.0](../saml/index.md)

## Passkeys and FIDO metadata

| Command | What it does |
|---|---|
| `beffroi:webauthn:mds-import` | Store a metadata statement file (unsigned, trusted as the file is) next to the FIDO Metadata BLOB, for the keys of a manufacturer the service does not list or the authenticators of the FIDO conformance tools. |
| `beffroi:webauthn:mds-refresh` | Download the FIDO Metadata BLOB, verify its signature under the pinned root and store it for the passkey ceremonies; --url for another service, --root for another root. |

## What a command may not do

A command never bypasses a rule the protocol applies. It cannot mint a token for a user, cannot read a
signing key it is not allowed to open, and cannot read a personal datum the key management service refuses
to unseal.

Three commands cannot be undone. `beffroi:data-keys:destroy` asks for the slug of the tenant to be typed back
before it runs, `beffroi:tenant:login-floor` asks before it forgets the credentials the floor leaves out, and
`beffroi:client:delete` deletes a client that registered itself.
