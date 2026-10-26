---
title: Persistence
description: The Doctrine mapping of the model, the tables, the migrations, the DBAL types, and what a sealed column changes about a query.
---

# Persistence

The provider keeps its model with Doctrine ORM. The classes of the core, of OpenID Connect and of SAML know
nothing of Doctrine: the bundle maps them from XML files of its own, declares their types and their
migrations to Doctrine itself, and the application writes none of it. The schema is therefore the same
whether the bundle is installed in an existing application or deployed in the standalone one.

## What the bundle maps

| Mapping | Directory of the bundle | Namespace |
|---|---|---|
| `BeffroiCore` | `config/doctrine/core` | `Beffroi\Core\Domain` |
| `BeffroiOidc` | `config/doctrine/oidc` | `Beffroi\Oidc\Domain` |
| `BeffroiSaml` | `config/doctrine/saml` | `Beffroi\Saml\Domain` |

One XML file per class, named after it, as `Identity.User.orm.xml`. The application maps its own entities
beside them and none of them is ever a user of the provider: a person of the provider is a row of
`beffroi_user`, whatever the host application calls its own users.

## The tables

Every table is prefixed `beffroi_`, and every table of the mapping but `beffroi_tenant` carries the tenant
it belongs to, by a foreign key on `tenant_id`.

=== "Identity"

    | Table | What a row is |
    |---|---|
    | `beffroi_tenant` | The tenant: its issuer, its slug, its name, its look, the claims its people may change, its `acr` vocabulary and the floor of its logins |
    | `beffroi_user` | A person: the subject, in the clear and unique in the tenant, the username, the e-mail address, the telephone number, the postal address, the claims of the profile and the source that created them |
    | `beffroi_password_credential` | The password of a person, its hash typed by its algorithm, and when a list of compromised passwords was last asked about it and when it was found there |
    | `beffroi_passkey_credential` | A passkey: the credential record of WebAuthn, its name and its revocation |
    | `beffroi_totp_credential` | An authenticator application: its secret, the last time step accepted and the hashed backup codes |
    | `beffroi_enrolment_ticket` | The ticket that opens one enrolment of a first passkey, by a hash of its value |
    | `beffroi_linked_identity` | Who a person is at an upstream provider, and what that provider said of them |
    | `beffroi_group`, `beffroi_group_membership` | The groups of the tenant and who belongs to them, each with its source |
    | `beffroi_push_subscription` | A browser of a person the provider can reach by [web push](web-push.md) |
    | `beffroi_authentication_session` | A session: what it proved, from where it was opened and last seen, when it ends and why it ended |
    | `beffroi_journal` | One act of the provider |
    | `beffroi_claim_change` | What a claim of a person said before they changed it, and what it says now |
    | `beffroi_personal_archive` | The archive a person asked for of everything the provider holds of them |

=== "OpenID Connect"

    | Table | What a row is |
    |---|---|
    | `beffroi_client` | A client the provider registered itself. A client declared in the configuration has no row |
    | `beffroi_initial_access_token` | An initial access token, by the digest of its value |
    | `beffroi_interaction` | An authorization request parked while the person signs in and consents |
    | `beffroi_pushed_authorization_request` | A pushed request, by the hash of its reference, its parameters as the client wrote them |
    | `beffroi_consent` | What a person agreed to let a client obtain |
    | `beffroi_authorization_code` | A code, by its hash, kept past its use so that a replay is told from an unknown code |
    | `beffroi_device_authorization_request` | A device authorization request, by the hash of the code the device polls with |
    | `beffroi_backchannel_authentication_request` | A backchannel authentication request, by the hash of the identifier the client comes back with |
    | `beffroi_refresh_token`, `beffroi_refresh_token_family` | A refresh token by its hash, and the lineage every token of a grant names |
    | `beffroi_access_token`, `beffroi_client_access_token`, `beffroi_subject_access_token` | An opaque access token by its hash: one somebody signed in for, one a client holds for itself, one whose subject was named by what the client presented |
    | `beffroi_pairwise_subject` | The identifier one sector sees a person under |
    | `beffroi_disclosure` | What a client was given of a person, at one act of the protocol |

=== "SAML"

    | Table | What a row is |
    |---|---|
    | `beffroi_saml_service_provider` | The newest metadata document accepted for a service provider |
    | `beffroi_saml_upstream_identity_provider` | The newest metadata document accepted for an upstream identity provider |
    | `beffroi_saml_remembered_message` | An assertion or a logout message already accepted, until the window in which it would be accepted again has closed |
    | `beffroi_saml_session_participant` | A service provider that took part in a session |
    | `beffroi_saml_logout_chain` | A single logout the provider plays through the browser that began it |

=== "Keys"

    | Table | What a row is |
    |---|---|
    | `beffroi_data_key` | A data key of a tenant, wrapped by its master key, with the client and the master key that wrapped it. No mapping describes it: it is the table of the data key store, created by a migration of the bundle and declared to the schema the ORM assembles, so that a comparison of the schema does not offer to drop it |

The keys of the tenant are not in the database. Each one is a file of `beffroi.keys.storage`, its private
half sealed by the [key management service](key-management.md).

## The migrations

The bundle ships its migrations in its own directory, under the namespace `Beffroi\Bundle\Migrations`, and
declares them to Doctrine Migrations. They are played with those of the application:

``` bash
bin/console doctrine:migrations:migrate
```

**They are written for PostgreSQL**, and each one stops on another platform with `This migration is written
for PostgreSQL.`

**A migration that seals columns says two things before it runs.** It refuses a table that holds rows,
naming the table and the count: a sealed column is binary and refuses a null, and nothing puts a value in
clear into it, so the rows are sealed by a script of the deployment's own or the table is emptied. And it says
to restart what serves requests and what consumes the buses once it has run, because a process that booted
before it reads those columns with the type they had.

## A value object in one column

**A value object a column holds whole goes in one column**, with a DBAL type of the bundle: the bundle
declares thirty-three of them, `beffroi_subject`, `beffroi_scopes`, `beffroi_request_context` or
`beffroi_password_hash` among them. What the column holds is written by the object itself, in the package
that owns it, and read back through its constructor, so a row edited by hand into something the object
refuses fails when it is loaded, as a conversion error naming the type, and never further down.

**Some of them read the wiring back.** A stored password hash names its algorithm, a confirmation of
RFC 8705 or RFC 9449 names its kind, an `authorization_details` names its type, a PKCE challenge names its
method, and the `acr` vocabulary and the floor of a tenant name their predicates. Each is read back as the
class the deployment wires under that name, so a row naming something the deployment no longer wires fails
at load rather than being read as something else: a password algorithm leaves the wiring once no hash of it
is left, or every row holding one fails to load.

**One embeddable is left in the mapping**, the authorization request, embedded by `beffroi_interaction` and
by nothing else. An embeddable fixes the type of each of its fields once for the whole model, so the same
value could not be sealed in one table and readable in another; this one stays because its first field is a
client, which no mapping carries, so no DBAL type could hand the object back whole.

**A client is not a row a table joins.** A client declared in the configuration has no row at all, so the
tables keep `client_id`, and the client is put back on a row once it is loaded, from the sources of clients
the deployment wires. A row whose client is no longer registered, removed from the configuration or deleted,
is treated as absent: a token or a consent of a client that does not exist is not one.

## Sealed columns

Thirty-three columns hold a personal datum, or the secret of a client, sealed under a data key of their
tenant. A data key is minted per tenant and per family of columns, the family being the name of the table
without its prefix, so the key that opens one table of a tenant opens no other table and no other tenant.

| Family | The columns it seals |
|---|---|
| `user` | `username`, `email`, `phone_number`, `address`, `profile`, `source` |
| `linked_identity` | `provider`, `subject`, `claims` |
| `passkey_credential` | `name` |
| `push_subscription` | `endpoint`, `label` |
| `authentication_session` | `created_from`, `last_seen_from` |
| `interaction` | `login_hint`, `id_token_hint` |
| `pushed_authorization_request` | `parameters` |
| `device_authorization_request` | `requested_from` |
| `backchannel_authentication_request` | `binding_message`, `requested_from` |
| `client` | `metadata`, `assigned_metadata`, `secret` |
| `journal` | `context` |
| `claim_change` | `was`, `became`, `context` |
| `disclosure` | `scopes`, `claims`, `authorization_details` |
| `personal_archive` | `content` |
| `saml_service_provider` | `document` |
| `saml_upstream_identity_provider` | `document` |

Three columns hold an envelope of the key management service instead, opened under the master key of the
tenant: the secret of an authenticator application, and the identifier and the token of a backchannel request
whose client the provider calls back.

A value is sealed under the tenant of the unit of work in progress, and a write that has none is refused
rather than sealed under a scope of no tenant. The data keys are what [the console](console-commands.md#data-keys)
lists, moves to another client and erases.

### What a sealed column changes about a query

- **It cannot be searched.** Every value is sealed under a random initialisation vector, so two writes of the
  same username give two ciphertexts and `WHERE username = ?` matches nothing.
- **What is searched is a blind index**, a keyed tag of the value in a column beside it, equal for equal
  values. Four columns carry one: `beffroi_user.username` in `username_index`, `beffroi_user.email` in
  `email_index`, folded whole, local part and domain, and the pair `provider` and `subject` of
  `beffroi_linked_identity` in `provider_index` and `subject_index`. The unique constraints are held on those
  columns, a constraint on a sealed column refusing nothing. The key of the tags is one per tenant, a data key
  of its own that never rotates.
- **The tag is written by the bundle, on the flush of the entity manager**, in the same statement as the
  value. A row written through DBAL, or changed by a bulk `UPDATE`, keeps whatever tag it had, and a search
  then finds the row by what it used to hold. `beffroi:user:reindex` derives the tags of every person of the
  tenant again.
- **The column is unbounded binary.** The `length` a mapping gives a sealed column is the length the model
  checks, not the width of the column, and an option that describes the stored value no longer holds: no
  query reads into the JSON of `beffroi_user.address`, which is a ciphertext.
- **A ciphertext is bound to its tenant, not to its row.** Within one tenant and one family, a value copied
  into another row of the same column opens there.

[:beffroi-arrow-right: Personal data](../core/personal-data.md)

## What goes away, and when

The protocol writes rows that stop being worth anything, and it keeps them past that moment on purpose, so
that a second presentation of a code or a token is told from a value nobody issued. Timed steps of the
[schedule](messenger.md#what-time-does-on-its-own) then drop them, each statement bounded and the next run
taking what it left.

| Step | Every | What it drops |
|---|---|---|
| The rows that are dead | Hour | Interactions, pushed requests, codes, device and backchannel requests, refresh tokens, opaque access tokens, enrolment tickets and sessions that nothing alive needs any more |
| The journal | Day | The acts older than `beffroi.journal.retention` days, 180 by default, and the disclosures with them |
| The history of a record | Day | The changes of claims older than `beffroi.history.retention` days, 180 by default |
| The archives | Hour | The archives past their expiry, a week after they were asked for |
| The unused clients | Hour | The clients that registered themselves and went unused longer than `client_registration.keep_a_client_unused_for`, ninety days by default, or were never used within `keep_a_client_never_used_for`, seven days by default |

A session is dropped last: the codes, refresh tokens and access tokens of a login name it under a foreign key
that cascades, and their own time is past before the session's. The SAML store of messages already accepted
and the logout chains drop their closed rows before each insertion.
