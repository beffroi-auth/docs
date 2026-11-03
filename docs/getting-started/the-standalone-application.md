---
title: Running the application
description: 'beffroi/op on your machine and as a deployment of its own: the development stack, the production image, and the first start in the order it has to happen.'
---

# Running the application

`beffroi/op` is the provider: a Symfony application served by FrankenPHP in worker mode, with PostgreSQL for
the model and for the writes the protocol does not wait on, each lane of Messenger a queue of the database.
The development stack the conformance plans run against is this application.

It is the `apps/op` directory of the monorepo, [beffroi-auth/beffroi](https://github.com/beffroi-auth/beffroi).
Its `composer.json` resolves the `beffroi/*` packages through path repositories to `../../src/*`, so the
application is built from a working copy of the monorepo: [beffroi-auth/op](https://github.com/beffroi-auth/op)
is a read-only mirror of that one directory, and installs nothing on its own.

## Where it keeps what

The packages under it bring the protocols and the identity model. Everything else is the application's own
code and configuration, in its own directories.

| What | Where it lives |
|---|---|
| The configuration of the provider, each value a deployment chooses read from the environment | `config/packages/beffroi.yaml` |
| The routes of both planes, and the root of the issuer, `/`, which sends a browser to the home of the account | `config/beffroi/routes.php`, imported by `config/routes/beffroi.yaml`; `config/routes/home.yaml` |
| The controllers, the security, the persistence and the console commands | `src/` |
| The Doctrine mapping of the model of the packages, and the migrations | `config/beffroi/doctrine/`, `migrations/` |
| The pages, their layout and their stylesheet, Tailwind and DaisyUI, built by the standalone Tailwind binary it pins | `templates/beffroi/`, `templates/layout/`, `assets/styles/app.css` |
| Every sentence of the pages, in English and in French | `translations/` |
| The theme a visitor reads the pages in, light, dark or the one of their system, chosen by a form posted to `/theme` | `src/Theme/` |
| The firewall of the interaction pages, with its four logins: a password, a passkey, a code, and an upstream SAML identity provider | `config/packages/security.yaml` |
| The headers a deployment answers with, and the name and attributes of the session cookie | `config/packages/nelmio_security.yaml`, `nelmio_cors.yaml`, `framework.yaml` |
| Where the lanes of Messenger go, a queue of the database each, through `BEFFROI_MESSENGER_DSN` | `.env` |
| FrankenPHP and Caddy, with the host that asks for a client certificate | `frankenphp/` |

[:beffroi-arrow-right: The application, page by page](../application/index.md)

## On your machine

The development stack runs the application in Docker beside PostgreSQL, whose table `messenger_messages`
holds the queues of the lanes as well. It is driven from the
root of the monorepo by Castor, 0.23 or later, and asks the machine for Docker Compose and Composer besides.
The two `composer install` below run on the machine and not in a container, so it also needs PHP 8.4 or later
with the extensions the locked packages require, `intl`, `dom` and `zip` among them.

``` bash
git clone git@github.com:beffroi-auth/beffroi.git && cd beffroi
composer install && (cd apps/op && composer install)
castor start
castor provision
```

`castor start` brings up the provider on `https://op.localhost`, the host that asks for a client certificate
on `https://mtls.op.localhost` and PostgreSQL. On a machine with an mkcert authority, the stack
serves a certificate mkcert issues there for its names, which a browser that trusts mkcert accepts; on any
other, Caddy issues one from its internal authority. On a stack that names no key management service yet, the
worker is created and left stopped, because it refuses to start without one.

`castor provision` is what a first start needs, in order, and it can be run again at will:

1. it writes into `apps/op/.env.local` what is missing there: the key management service, a sodium key
   generated in place unless `--kms file`, `--kms vault` or `--kms aws` names another backend, the secrets of
   the clients the stack declares, and the password of the development user;
2. it plays the migrations;
3. it writes the row of the tenant with `beffroi:tenant:synchronize`;
4. it draws the keys of the tenant, the key messages are sealed to first, or checks with the key management
   service that the keys already there still open;
5. it creates the user `alice` with a verified email address, describes her with the claims of the
   `profile`, `phone` and `address` scopes, and sets her password;
6. it issues the client certificate of the stack, on the machine, under `var/mtls/`;
7. it starts the worker.

It ends by printing where the discovery document and the JWK Set are, the key management service, the
username, password and subject of `alice`, and the secrets of the clients. `https://op.localhost/` sends a
browser to the home of the account, which asks it to sign in.

The clients of the stack are declared for the development environment only: the clients of the OpenID
conformance suite, and those of the demonstrations of the repository, among them
[oidc-demo](a-symfony-relying-party.md#the-reference-relying-party). `castor stop` takes the stack down,
`castor logs` follows its logs and `castor console` runs a console command in the container that serves it.

## As a deployment of its own

The production image is built from the root of the monorepo, which is the build context its `Dockerfile`
expects:

``` bash
docker build --file apps/op/Dockerfile --target frankenphp_prod .
```

The build copies `apps/op/` without what a working copy holds beside the repository, such as the `.env.local`
the development stack writes, installs the application without its development dependencies, compiles
the `.env` of the repository for production with `composer dump-env prod`, builds the stylesheet and compiles
the assets. What a deployment chooses is then read from the environment when the container starts: the
issuer, the database, the key management service, the lanes, and every other setting of the provider.

[:beffroi-arrow-right: The environment the application reads](../application/configuration.md) and
[whole deployments written with it](../application/examples.md)

### The Compose file of the image

The monorepo carries a deployment of the published image, `ghcr.io/beffroi-auth/op`, in one file at its root,
[`compose.prod.yaml`](https://github.com/beffroi-auth/beffroi/blob/0.0.x/compose.prod.yaml). It stands alone,
so it is downloaded without the rest of the monorepo, and runs three services: the server, the worker and
PostgreSQL, whose table `messenger_messages` holds the queues of the lanes. No broker runs beside them.

``` bash
docker compose -f compose.prod.yaml up -d --wait op
```

- **It reads its environment from a `.env` beside it**, and refuses to start without five variables, none of
  which it gives a value: `SERVER_NAME`, the host Caddy serves and obtains a certificate for, which makes the
  issuer `https://<host>`; `APP_SECRET`; `POSTGRES_PASSWORD`, written into a URL as it stands; and
  `BEFFROI_KMS_DSN` with `BEFFROI_KMS_KEY_ID`.
- **The two processes mount the same five volumes**, for `var/keys`, `var/kms`, `var/geoip`, `var/webauthn`
  and `var/share`. Under the file backend, the master key of the tenant is drawn once into the volume of
  `var/kms`, before anything is sealed, by the command the header of the file gives.
- **The processes run as `www-data`, uid 33.** The volumes are theirs from their first mount, and what a
  deployment mounts in their place, a directory of its own or the key of the file backend given as a secret,
  is readable by that uid, and writable where it stands for one of these volumes.
- **The two processes read the six variables the file names**, the issuer, `DEFAULT_URI`, `APP_SECRET`, the
  database and the key management service, written once for both. Compose hands a container nothing else of
  its `.env`, so any other variable is added to the environment of both processes:
  [one host](../application/examples.md#one-host).
- **Only the server publishes ports**, 80 and 443 over TCP and 443 over UDP. PostgreSQL is reached by the two
  processes alone.
- **The worker has a health check of its own**, that the consumer is the first process of its container: the
  one of the image asks Caddy, which the worker does not run.
- **The host that asks for a client certificate is off**, and three commented variables of the server turn it
  on: `CADDY_EXTRA_CONFIG`, `MTLS_SERVER_NAME` and `BEFFROI_MTLS_ORIGIN`.
- **Caddy terminates TLS**, and two commented variables of the server hand it to a proxy in front of the
  image: `TLS_TERMINATION`, which serves the site of `SERVER_NAME` on plain HTTP, on port 80, to the proxy
  that asks for that host, and `SYMFONY_TRUSTED_PROXIES`, which names the proxy to Symfony:
  [behind a proxy](../application/deployment.md#behind-a-proxy).

Its header gives the first start in the order below, the worker started last.

### The first start, in order

The order is the one of `castor provision`, and two of its constraints hold for every deployment: the tenant
has a row before it has a key, and its first key is the one messages are sealed to.

1. **The schema.** The container that serves HTTP waits for the database and plays the migrations before
   FrankenPHP starts, every time it starts.
2. **The tenant and its keys**, in a container of the image:

    ``` bash
    bin/console beffroi:tenant:synchronize
    bin/console beffroi:keys:generate --algorithm=MESSAGE-SEAL
    bin/console beffroi:keys:generate
    ```

    Drawing a key announces it on a transport, and what goes on a transport is sealed to the key the tenant
    keeps for its messages. That key is therefore the first one: a tenant that does not hold it yet has
    `beffroi:keys:generate` fail on the message it cannot seal. The second command draws the key of the
    default signature algorithm, `RS256`, which the access tokens are signed with, and the ID tokens of a
    client that names no other algorithm.

3. **The keys of what this application turns on.** Its configuration turns on web push and the SAML identity
   provider, each with a key of its own:

    ``` bash
    bin/console beffroi:keys:generate --algorithm=VAPID
    bin/console beffroi:keys:generate --algorithm=SAML-SIGNING
    ```

    The discovery document announces every algorithm the application is wired with, and a key is drawn for each
    one a client uses: a client that registers `ES256` for what the provider signs for it needs the key of
    `ES256`, and one that encrypts to the provider with `ECDH-ES+A256KW` the key of that algorithm. The
    development stack draws both.

4. **A person who can sign in**:

    ``` bash
    bin/console beffroi:user:create alice --email alice@example.com
    bin/console beffroi:user:set-password alice
    ```

5. **The worker**, once the steps above are done: the same image, running `bin/console messenger:consume` on
   the schedule and the four lanes of the provider.

[:beffroi-arrow-right: The image, the processes and the worker](../application/deployment.md)

## Then

1. [The tenant and its keys](tenant-and-keys.md), for what each of those commands does.
2. [Your first client](your-first-client.md): the image declares none, and a client registers itself.
3. [A Symfony relying party](a-symfony-relying-party.md), to see a sign-in end to end.
