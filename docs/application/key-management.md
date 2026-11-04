---
title: Key management
description: The client of symfony/key-management the application seals with, what it seals, the backends it runs against, and what moves when the client changes.
---

# Key management

The application seals the private keys of the tenant, its data keys and the secrets it holds for people with
`op`, a client of `symfony/key-management` that `config/packages/key_management.yaml` declares. Which provider
stands behind that client is the deployment's to say, by the DSN of `BEFFROI_KMS_DSN`. The key management
service keeps the master keys and never signs: a private key is opened in the process that uses it, and what
is sealed never reaches the service, only the data key it is sealed with, to be wrapped or opened.

## Naming the client

`config/packages/key_management.yaml` declares two clients, each built from a DSN of the environment: `op`
from `BEFFROI_KMS_DSN`, and `second` from `BEFFROI_KMS_DSN_SECOND`, for a [move to another
client](#moving-to-another-client). The application's configuration names `op`, no variable names another,
and the provider seals with it and never with `second`. The image compiles the file as it is:

``` yaml title="config/packages/key_management.yaml"
key_management:
    clients:
        op: 'service://beffroi.kms.op'
        second: 'service://beffroi.kms.second'

services:
    beffroi.kms.op:
        class: Symfony\Component\KeyManagement\EncrypterInterface
        factory: ['@key_management.factory', 'fromString']
        arguments: ['%env(BEFFROI_KMS_DSN)%']

    beffroi.kms.second:
        class: Symfony\Component\KeyManagement\EncrypterInterface
        factory: ['@key_management.factory', 'fromString']
        arguments: ['%env(BEFFROI_KMS_DSN_SECOND)%']
```

A deployment names the service and the master key of `op`, two variables the image leaves empty, since nothing
is sealed or signed under a key everybody has:

``` dotenv
BEFFROI_KMS_DSN="sodium+dir:///app/var/kms?ext=.key"
BEFFROI_KMS_KEY_ID="beffroi-{tenant}"
```

| Variable | In the image | What it decides |
|---|---|---|
| `BEFFROI_KMS_DSN` | empty | The DSN `op` is built from: which service seals, and how it is reached. [The backends](#the-backends) are below |
| `BEFFROI_KMS_KEY_ID` | empty | The master key of that service the keys of the tenant are sealed under, in the terms of the backend: the name of a sodium key, a Transit key of Vault, an alias or an ARN of AWS. `{tenant}` stands for the slug of the tenant, which gives every tenant a master key of its own |
| `BEFFROI_KMS_DSN_SECOND` | empty | The DSN `second` is built from, for a [move to another client](#moving-to-another-client). Empty, the client is declared and never built |

The sealed keys and the pairwise salt are kept in `var/keys` of the application, a directory no variable
moves. How long the JWK Set is cached, how long a new key is staged and how long a key works are
`BEFFROI_JWKS_MAX_AGE`, `BEFFROI_KEY_STAGING_DELAY` and `BEFFROI_KEY_AGE`, on
[configuration](configuration.md#keys-and-lifetimes), and what they do to a rotation is on [the console
commands](console-commands.md#rotating-a-key).

**The DSN reaches the client through a service.** The `dsn` of a client is validated when the container is
built and takes no environment variable, while the DSN of a deployment comes from its environment and may
carry a credential. So the application builds each client from the environment with the factory of the
component, `key_management.factory`, and names it with `service://`.

**Each client is one provider.** A DSN names one service, and `symfony/key-management` makes a client of
several providers only from the `members` a client is given in `key_management.yaml`, which the file above
gives neither of its two: a deployment of the image seals with the one service `BEFFROI_KMS_DSN` names.

## What it seals

| What | Where it lives |
|---|---|
| The keys of the tenant, the ones that sign, the ones clients encrypt to, and the ones it keeps rather than publishing: the key messages are sealed to, the application server key of web push and the SAML keys | One file per key, `var/keys/<slug>/<kid>.json`: the public half in the clear, the private half sealed. The directory is created `0700` and every file `0600` |
| The pairwise salt of the tenant (OIDC Core §8.1), drawn at its first use and never again | `var/keys/<slug>/pairwise.salt`, sealed |
| The data keys of the sealed columns, one per tenant and per family of columns | Rows of `beffroi_data_key`, wrapped by the master key of the tenant; each row names the client and the master key that wrapped it, and is bound to its reference and its scope under a secret of `BEFFROI_DATA_KEY_SECRETS`, `APP_SECRET` while that variable is not set, which the database does not hold |
| The secrets held for people: the secret of an authenticator application, the identifier and token of a backchannel request whose client is called back, the person a self-contained access token is about, an enrolment of an authenticator application in progress | Envelopes, in their column, in the token, or in the HTTP session of the browser |

Every envelope is bound to its tenant and to its use: sealed for one tenant it does not open for another, and a
sealed key does not open as a secret. Every process of a deployment reads the same storage directory: the
worker rotates the keys the processes that serve requests open.

[:beffroi-arrow-right: Keys](../core/keys.md) &nbsp; [:beffroi-arrow-right: Personal data](../core/personal-data.md)

## The backends

The DSN is the only thing that changes between two backends: the code and the envelope are the same. The
suites that boot the provider run whole on a sodium key written in their DSN, and the tests of custody, the
sealed keys, the secrets of an authenticator application and the search of a dump of the database, run again
on a key file. The custody tests of Vault Transit and of AWS KMS run where a suite is pointed at one, which the
development stack of the project does, AWS through LocalStack, and are skipped otherwise.

=== "Sodium, in the environment"

    A sodium key written in the DSN itself, which is what the development stack provisions. Whoever reads the
    environment of the process holds the master key.

    ``` dotenv
    BEFFROI_KMS_DSN="sodium://?keys[signing]=<32 bytes, base64url>"
    BEFFROI_KMS_KEY_ID="signing"
    ```

=== "Sodium, in a file"

    The same sodium key read from a file of its own, mode `0600`, outside the web root and outside the
    storage of the sealed keys: what a self-hosted deployment without a key management service uses. It holds
    against a copy of the sealed keys, not against a compromise of the host.
    [Configuration](configuration.md#the-key-management-service) says how the key is drawn into its volume.

    ``` dotenv
    BEFFROI_KMS_DSN="sodium+dir:///app/var/kms?ext=.key"
    BEFFROI_KMS_KEY_ID="beffroi-{tenant}"
    ```

=== "HashiCorp Vault Transit"

    A Transit key per tenant, and a token minted under a policy that allows data keys and decryption under
    those keys, their configuration and nothing else. The client is `symfony/hashicorp-vault-key-management`.
    A Vault that answers in plain HTTP, as the one of the development stack does, is named with
    `?scheme=http` at the end of the DSN.

    ``` dotenv
    BEFFROI_KMS_DSN="hashicorp-vault-transit://<token>@<host>:8200"
    BEFFROI_KMS_KEY_ID="beffroi-{tenant}"
    ```

=== "AWS KMS"

    An alias per tenant, and the credentials of the provider chain of the SDK. The client is
    `symfony/aws-key-management`.

    ``` dotenv
    BEFFROI_KMS_DSN="aws-kms://default?region=<region>"
    BEFFROI_KMS_KEY_ID="alias/beffroi-{tenant}"
    ```

## Opening a key

A process opens a key once, the first time it needs it, and keeps it open for as long as it lives, by tenant
and by `kid`; a key that retires is forgotten. Served by FrankenPHP in worker mode, as the image of the
application is, a process pays one opening per key for all the signatures it makes; a process rebuilt at each
request pays one at each request. The sealed columns follow the same rule with their data keys, one opening
per data key and per process.

``` bash
bin/console beffroi:keys:list --check
```

Opens the keys in use and the ones about to be, and fails on a key the service cannot open: a key the provider
cannot open is an outage at the first token request, so this is worth a run in a deployment pipeline.

## When the service does not answer

A key management service that does not answer, or whose backend refuses, is an outage and not an error of the
request. Wherever it stands on the path of a request, the first opening of a signing key on a process that has
not signed yet, the secret of an authenticator application at the code page, the enrolment of one, the request
is answered `503 Service Unavailable` with `Retry-After: 10`, the same request being served once the service is
back. Nothing was refused to the person and nothing was counted: a pending login keeps waiting for the same
code. The outage is announced to the journal with the words of the service, and nothing of what was being
opened.

An envelope the service refuses to open, tampered with, sealed for another tenant or another use, or wrapped
under a master key the service does not know when it opens it, is not an outage: it is an error, and no
retry changes it.

## Moving to another client

**The data keys move without a single sealed value being read.** `BEFFROI_KMS_DSN_SECOND` names the new
service in the environment of every process, and the data keys of the tenant are wrapped again by `second`:

``` bash
bin/console beffroi:data-keys:rewrap --to=second --dry-run
bin/console beffroi:data-keys:rewrap --to=second
```

The master key is the one `BEFFROI_KMS_KEY_ID` gives the tenant, resolved and never typed, so the new service
holds a key under the same identifier. Every row names the client that wraps it, so the columns read through
the rewrap and after it, a row `second` wraps opening for as long as `BEFFROI_KMS_DSN_SECOND` names its
service. A data key minted later, at the rotation of a family or at the first write of a new one, is wrapped
by `op`, under the service `BEFFROI_KMS_DSN` names when the key is minted. `BEFFROI_KMS_DSN_SECOND` stays
empty, and `second` never built, on a deployment that moves nothing.

**The keys of the tenant move by rotation.** An envelope sealed by one service does not open with another, so
once `BEFFROI_KMS_DSN` names the new service, every algorithm the tenant holds gets a new key sealed by it:

``` bash
bin/console beffroi:keys:rotate --now --algorithm=RS256
```

The key it replaces retires with its window, its public half still verifying what it signed; nothing is
deleted. `beffroi:keys:list --check` names the algorithms whose keys the client cannot open.

**The pairwise salt and the secrets held for people have no command that moves them.** They are opened
through `op`, so they open only for as long as `BEFFROI_KMS_DSN` names the service that sealed them.

!!! warning "Pointing `BEFFROI_KMS_DSN` at another service"

    Once `BEFFROI_KMS_DSN` names another service, the pairwise salt and the secrets held for people no longer
    open, and so does a data key `op` minted under the previous service after the rewrap. The image has no
    command that moves them first.

[:beffroi-arrow-right: The commands, in full](console-commands.md#data-keys)
