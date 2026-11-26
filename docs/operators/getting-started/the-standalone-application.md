---
title: Running the application
description: 'beffroi/beffroi from its published image with one Compose file, and from the sources as the development stack: what each needs, and the first start in the order it has to happen.'
---

# Running the application

`beffroi/beffroi` is the provider: a Symfony application served by FrankenPHP in worker mode, with PostgreSQL for
the model and for the writes the protocol does not wait on, each lane of Messenger a queue of the database.
It runs two ways:

| | What the machine needs | For |
|---|---|---|
| [The image alone](#with-the-image-alone) | Docker with Compose | Running the provider, on your machine or on a server |
| [From the sources](#from-the-sources) | Docker with Compose, a working copy of the monorepo, Castor, Composer and PHP 8.4 or later | Working on its code, and the development stack the conformance plans run against |

## With the image alone

### The Compose file of the image

The published image, `ghcr.io/beffroi-auth/beffroi`, is deployed by one file,
[`compose.prod.yaml`](https://github.com/beffroi-auth/beffroi/blob/0.1.x/compose.prod.yaml), which stands alone:
it is downloaded without the rest of the monorepo, and nothing is cloned, built or installed on the machine. It
runs three services: the server, the worker and PostgreSQL, whose table `messenger_messages` holds the queues of
the lanes. No broker runs beside them.

``` bash
mkdir beffroi && cd beffroi
curl -fsSLO https://raw.githubusercontent.com/beffroi-auth/beffroi/0.1.x/compose.prod.yaml
```

Its header lists what it needs and gives every command of the [first start](#the-first-start-in-order).

- **It reads its environment from a `.env` beside it**, and refuses to start without five variables, none of
  which it gives a value: `SERVER_NAME`, the host Caddy serves and obtains a certificate for, which makes the
  issuer `https://<host>`; `APP_SECRET`; `POSTGRES_PASSWORD`, written into a URL as it stands; and
  `BEFFROI_KMS_DSN` with `BEFFROI_KMS_KEY_ID`.
- **No client exists until `BEFFROI_REGISTRATION_MODE` is set** in that `.env`: the image declares none, a
  client registers itself (RFC 7591), and while the mode is empty the tenant serves no registration endpoint
  and its discovery document names no `registration_endpoint`. For the clients of an organisation, the mode is
  `initial_access_token`, the [first start](#the-first-start-in-order) issues the token, and
  [dynamic registration](../../developers/oidc/dynamic-registration.md#the-three-modes) says what each mode allows.
- **The two processes mount the same five volumes**, for `var/keys`, `var/kms`, `var/geoip`, `var/webauthn`
  and `var/share`. Under the file backend, the master key of the tenant is drawn once into the volume of
  `var/kms`, before anything is sealed, by the command the header of the file gives.
- **The processes run as `www-data`, uid 33.** The volumes are theirs from their first mount, and what a
  deployment mounts in their place, a directory of its own or the key of the file backend given as a secret,
  is readable by that uid, and writable where it stands for one of these volumes.
- **The two processes read the seven variables the file names**, the issuer, `DEFAULT_URI`, `APP_SECRET`, the
  database, the key management service and the mode of registration, written once for both. Compose hands a
  container nothing else of its `.env`, so any other variable is added to the environment of both processes:
  [one host](../application/examples.md#one-host).
- **A secret may be a file**, which `docker inspect` does not show: a deployment replaces the line of a variable
  that carries one, `APP_SECRET` for instance, with its `_FILE` twin naming a file a `secrets:` entry mounts
  under `/run/secrets`, readable by uid 33, and never sets both. PostgreSQL reads `POSTGRES_PASSWORD_FILE` the
  same way: [a secret in a file](../application/configuration.md#a-secret-in-a-file).
- **The processes may connect as a role of their own**, which reads and writes what they serve and rewrites no
  row of the journal, of the history of claims or of what clients were given. That role is created once, its
  name made of lowercase letters, digits and underscores, its password of URL-safe characters, then named by
  `BEFFROI_DATABASE_USER` and `BEFFROI_DATABASE_PASSWORD`:

    ``` bash
    docker compose -f compose.prod.yaml up -d --wait database
    docker compose -f compose.prod.yaml exec database psql -U beffroi -c "CREATE ROLE beffroi_runtime LOGIN PASSWORD '<password>'"
    ```

    The server plays the migrations as `POSTGRES_USER`, the role that owns the tables, through
    `BEFFROI_MIGRATIONS_DATABASE_URL`, and grants the other role. Left unset, the processes connect as
    `POSTGRES_USER`, and whoever holds its password can rewrite any row.

- **Only the server publishes ports**, 80 and 443 over TCP and 443 over UDP. PostgreSQL is reached by the two
  processes alone.
- **The worker has a health check of its own**, that the consumer is the first process of its container: the
  one of the image asks the provider through Caddy, which the worker does not run.
- **The host that asks for a client certificate is off**, and three commented variables of the server turn it
  on: `CADDY_EXTRA_CONFIG`, `MTLS_SERVER_NAME` and `BEFFROI_MTLS_ORIGIN`.
- **Caddy terminates TLS**, and two commented variables of the server hand it to a proxy in front of the
  image: `TLS_TERMINATION`, which serves the site of `SERVER_NAME` on plain HTTP, on port 80, to the proxy
  that asks for that host, and `SYMFONY_TRUSTED_PROXIES: private_ranges`, which names to Symfony a proxy
  on a private network and the loopback address the health check of the image asks from:
  [behind a proxy](../application/deployment.md#behind-a-proxy).

### The first start, in order

Two constraints hold for every deployment: the tenant has a row before it has a key, and its first key is the
one messages are sealed to. The worker is therefore started last. Each command runs from the directory of
`compose.prod.yaml` and its `.env`.

1. **The schema and the tenant.** The server waits for the database, plays the migrations as the role that
   owns the tables, grants the role the processes connect as when it is another, and writes the row of the
   tenant its environment describes (`beffroi:tenant:synchronize`) before FrankenPHP starts, every time it
   starts:

    ``` bash
    docker compose -f compose.prod.yaml up -d --wait op
    ```

2. **The keys of the tenant**, in the container of the server:

    ``` bash
    docker compose -f compose.prod.yaml exec op bin/console beffroi:keys:generate --algorithm=MESSAGE-SEAL
    docker compose -f compose.prod.yaml exec op bin/console beffroi:keys:generate
    ```

    Drawing a key announces it on a transport, and what goes on a transport is sealed to the key the tenant
    keeps for its messages. That key is therefore the first one: a tenant that does not hold it yet has
    `beffroi:keys:generate` fail on the message it cannot seal. The second command draws the key of the
    default signature algorithm, `RS256`, which the access tokens are signed with, and the ID tokens of a
    client that names no other algorithm.

3. **The keys of what this application turns on.** Its configuration turns on web push and the SAML identity
   provider, each with a key of its own:

    ``` bash
    docker compose -f compose.prod.yaml exec op bin/console beffroi:keys:generate --algorithm=VAPID
    docker compose -f compose.prod.yaml exec op bin/console beffroi:keys:generate --algorithm=SAML-SIGNING
    ```

    The discovery document announces every algorithm the application is wired with, and a key is drawn for each
    one a client uses: a client that registers `ES256` for what the provider signs for it needs the key of
    `ES256`, and one that encrypts to the provider with `ECDH-ES+A256KW` the key of that algorithm. The
    development stack draws both.

4. **A person who can sign in**:

    ``` bash
    docker compose -f compose.prod.yaml exec op bin/console beffroi:user:create alice --email alice@example.com
    docker compose -f compose.prod.yaml exec op bin/console beffroi:user:set-password alice
    ```

5. **A client.** Under `BEFFROI_REGISTRATION_MODE=initial_access_token`, a token for the team that integrates,
   printed once, with which its client registers itself:
   [your first client](../../developers/connect/your-first-client.md).

    ``` bash
    docker compose -f compose.prod.yaml exec op bin/console beffroi:client:token:issue 'My application'
    ```

6. **The worker**, once the steps above are done: the same image, running `bin/console messenger:consume` on
   the schedule and the four lanes of the provider.

    ``` bash
    docker compose -f compose.prod.yaml up -d --wait
    ```

[:beffroi-arrow-right: The image, the processes and the worker](../application/deployment.md)

### Building the image

The published image is the one to deploy. From a working copy of the monorepo ([from the
sources](#from-the-sources)), the same image is built from its root, which is the build context its
`Dockerfile` expects:

``` bash
docker build --file apps/beffroi/Dockerfile --target frankenphp_prod .
```

The build copies `apps/beffroi/` without what a working copy holds beside the repository, such as the `.env.local`
the development stack writes, installs the application without its development dependencies, compiles
the `.env` of the repository for production with `composer dump-env prod`, builds the stylesheet and compiles
the assets. What a deployment chooses is then read from the environment when the container starts: the
issuer, the database, the key management service, the lanes, and every other setting of the provider.

[:beffroi-arrow-right: The environment the application reads](../application/configuration.md) and
[whole deployments written with it](../application/examples.md)

## From the sources

The application is the `apps/beffroi` directory of the monorepo,
[beffroi-auth/beffroi](https://github.com/beffroi-auth/beffroi). Its `composer.json` resolves the `beffroi/*`
packages through path repositories to `../../src/*`, so the application is built from a working copy of the
monorepo: [beffroi-auth/application](https://github.com/beffroi-auth/application) is a read-only mirror of that
one directory, and installs nothing on its own.

The development stack runs the application in Docker beside PostgreSQL, whose table `messenger_messages`
holds the queues of the lanes as well. It is driven from the
root of the monorepo by Castor, 0.23 or later, and asks the machine for Docker Compose and Composer besides.
The two `composer install` below run on the machine and not in a container, so it also needs PHP 8.4 or later
with the extensions the locked packages require, `intl`, `dom` and `zip` among them.

``` bash
git clone git@github.com:beffroi-auth/beffroi.git && cd beffroi
composer install && (cd apps/beffroi && composer install)
castor start
castor provision
```

`castor start` brings up the provider on `https://op.localhost`, the host that asks for a client certificate
on `https://mtls.op.localhost` and PostgreSQL. On a machine with an mkcert authority, the stack
serves a certificate mkcert issues there for its names, which a browser that trusts mkcert accepts; on any
other, Caddy issues one from its internal authority. On a stack that names no key management service yet, the
worker is created and left stopped, because it refuses to start without one.

`castor provision` is what a first start needs, in order, and it can be run again at will:

1. it writes into `apps/beffroi/.env.local` what is missing there: the key management service, a sodium key
   generated in place unless `--kms file`, `--kms vault` or `--kms aws` names another backend, with sodium or Vault
   a second key in `BEFFROI_KMS_DSN_SECOND` for a move of the data keys, the secrets of the clients the stack
   declares, the password of the development user, the origin of the host that asks for a client certificate,
   `BEFFROI_MTLS_ORIGIN=https://mtls.op.localhost`, and the open registration of clients,
   `BEFFROI_REGISTRATION_MODE=open`. Whatever the file held, it sets the public key sets of the clients of the FAPI
   2.0 and FAPI-CIBA conformance plans, of the issuer of assertions the stack trusts and of the authority whose
   software statements the tenant accepts to what their keys publish, and under Vault it writes a new token into
   `BEFFROI_KMS_DSN` when the one there no longer works;
2. it plays the migrations;
3. it writes the row of the tenant with `beffroi:tenant:synchronize`;
4. it draws the keys of the tenant, the key messages are sealed to first, or checks with the key management
   service that the keys already there still open;
5. it creates the user `alice` with a verified email address, describes her with the claims of the `profile`,
   `phone` and `address` scopes, sets her password, writes her subject into `.env.local` as
   `BEFFROI_DEV_USER_SUBJECT`, and says she is the subject `alice@issuer.demo.localhost` at the issuer of
   assertions the stack trusts;
6. it issues the client certificate of the stack, on the machine, under `var/mtls/`;
7. it starts the worker.

It ends by printing where the discovery document and the JWK Set are, the key management service, the
username, password and subject of `alice`, and the secrets of the clients. `https://op.localhost/` sends a
browser to the home of the account, which asks it to sign in.

The clients of the stack are declared for the development environment only: the clients of the OpenID
conformance suite, and those of the demonstrations of the repository, among them
[oidc-demo](../../developers/connect/symfony.md#the-reference-application). `castor stop` takes the stack down,
`castor logs` follows its logs and `castor console` runs a console command in the container that serves it.

### Where it keeps what

The packages under it bring the protocols and the identity model. Everything else is the application's own
code and configuration, in its own directories.

| What | Where it lives |
|---|---|
| The configuration of the provider, each value a deployment chooses read from the environment | `config/packages/beffroi.yaml` |
| The routes of both planes, and the root of the issuer, `/`, which sends a browser to the home of the account | `config/beffroi/routes.php`, imported by `config/routes/beffroi.yaml`; `config/routes/home.yaml` |
| The controllers, the security, the persistence and the console commands | `src/` |
| The Doctrine mapping of the model of the packages, and the migrations | `config/beffroi/doctrine/`, `migrations/` |
| The pages, their layout and their stylesheet, Tailwind and DaisyUI, built by the standalone Tailwind binary it pins | `templates/beffroi/`, `templates/layout/`, `assets/styles/app.css` |
| Every sentence of the pages and the messages, in the thirty-one languages the application ships | `translations/` |
| The theme a visitor reads the pages in, light, dark or the one of their system, chosen by a form posted to `/theme` | `src/Theme/` |
| The firewall of the interaction pages, with its four logins: a password, a passkey, a code, and an upstream SAML identity provider | `config/packages/security.yaml` |
| The headers a deployment answers with, and the name and attributes of the session cookie | `config/packages/nelmio_security.yaml`, `nelmio_cors.yaml`, `framework.yaml` |
| Where the lanes of Messenger go, a queue of the database each, through `BEFFROI_MESSENGER_DSN` | `.env` |
| FrankenPHP and Caddy, with the host that asks for a client certificate | `frankenphp/` |

[:beffroi-arrow-right: The application, page by page](../application/index.md)

## Then

1. [The tenant and its keys](tenant-and-keys.md), for what each of those commands does.
2. [Your first client](../../developers/connect/your-first-client.md): the image declares none, and a client registers itself once `BEFFROI_REGISTRATION_MODE` names a mode.
3. [Add sign-in to a Symfony application](../../developers/connect/symfony.md), to see a sign-in end to end.
