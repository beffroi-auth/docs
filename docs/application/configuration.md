---
title: Configuration
description: Every variable the application reads and what each one decides, the four key management backends, and what its configuration files say for a deployment.
---

# Configuration

What changes from one machine to the next is an environment variable: the issuer, the key management service,
the database, the broker, the lifetimes, the host that asks for a client certificate. What the deployment is,
its clients, its look, the protocols it turns on, is written in its configuration files.

`apps/op/.env` holds the values of the development stack, and the production image compiles it with
`composer dump-env prod`, together with a `.env.local` when the checkout it is built from holds one. A real
environment variable wins over both, which is how a deployment says its own. `.env` carries no secret of a
deployment: the key management service, the key it seals under and the secrets of the clients are empty there,
and the database and the broker are those of the development stack. That stack writes its own secrets into
`.env.local`, which is never committed and which an image is built without.

## The provider

| Variable | In `.env` | What it decides |
|---|---|---|
| `BEFFROI_ISSUER` | `https://op.localhost` | The issuer of the tenant (OIDC Discovery 1.0 §3), which every token names and every client compares byte for byte: an absolute `https` URL with no query, no fragment and no trailing slash, plain HTTP on a loopback host only. The application imports the routes of the bundle at the root, so its issuer is an origin with no path. A tenant keeps the issuer its row was written with: `beffroi:tenant:synchronize` refuses another |
| `BEFFROI_KMS_DSN` | empty | The key management service that seals the keys of the tenant, its pairwise salt and its data keys, as the DSN of the client `op` of `config/packages/key_management.yaml`. [The backends](#the-key-management-service) are below |
| `BEFFROI_KMS_KEY_ID` | empty | The master key of that service the tenant is sealed under. `{tenant}` in it stands for the slug of the tenant, one master key per tenant |
| `BEFFROI_KMS_DSN_SECOND` | empty | A second client, `second`, holding a key under the same identifier, for a run that moves the data keys from one to the other. Empty, the client is declared and never built |
| `BEFFROI_PLANE` | `all` | The plane this process serves: `all`, `interaction` or `protocol`. A route of a plane the process does not serve answers `404` |
| `BEFFROI_MTLS_ORIGIN` | `https://mtls.op.localhost` | The origin of the host that asks for a client certificate, announced in `mtls_endpoint_aliases` (RFC 8705 §5). Empty, the discovery document announces no alias, which is what a deployment serving one host sets |
| `BEFFROI_JWKS_MAX_AGE` | `300` | How long, in seconds, a relying party may cache the JWK Set (RFC 7517 §5). A key staged by a rotation, the SAML signing key aside, is published for this long plus sixty seconds before it takes over, 360 seconds with this value |
| `BEFFROI_ACCESS_TOKEN_TTL` | `600` | The lifetime of an access token in seconds, whether it is an `at+jwt` or an opaque reference |
| `BEFFROI_ID_TOKEN_TTL` | `600` | The lifetime of an ID token in seconds |
| `GEOIP_LICENSE_KEY` | empty | The licence key of the MaxMind account the GeoLite2 databases are downloaded under. Empty, nothing is downloaded, and every session and every act says an address and no place |
| `BEFFROI_BREACHED_PASSWORDS_ENDPOINT` | empty | The range endpoint a password is compared against before it is written (NIST SP 800-63B §3.1.1.2): `https://api.pwnedpasswords.com/range/`, where the first five hexadecimal characters of the SHA-1 of a password leave and the rest is compared locally. Empty, nobody is asked, and passwords are posed on the rules of the core alone |

Each of these is read when the kernel needs it and not when its container is compiled, so changing one asks
for a restart of the processes and not for a new image.

## Symfony, the database and the broker

| Variable | In `.env` | What it decides |
|---|---|---|
| `APP_ENV` | `dev` | The environment of the kernel. The production image sets `prod` |
| `APP_SECRET` | empty | The secret of the kernel, `framework.secret`. `.env.dev` and `.env.test` give one each, for their own environment, so a production environment names its own. It is also the secret every data key of personal data is bound to its row under, `beffroi.keys.data_key_secrets` naming no other: the store of the data keys refuses an empty one the first time it is used, and a new one replaces it only as [operating it](operating.md#data-keys) says |
| `APP_SHARE_DIR` | `var/share` | The share directory of Symfony, one per environment beneath it, `var/share/prod` for a production kernel. It holds the filesystem pool of `cache.app`, and with it the [caches of the bundle](deployment.md#what-the-processes-share) |
| `DEFAULT_URI` | `https://op.localhost` | The URL Symfony generates absolute URLs under outside a request, `framework.router.default_uri` |
| `DEFAULT_LOCALE` | `en` | The language a page falls back to, among the two the application serves, `en` and `fr` |
| `DATABASE_URL` | `postgresql://beffroi:beffroi@127.0.0.1:5432/beffroi?serverVersion=16&charset=utf8` | The PostgreSQL database. The entrypoint of the image waits for it, and the migrations refuse any other platform |
| `MESSENGER_TRANSPORT_DSN` | `amqp://beffroi:beffroi@localhost:5672/%2f/messages` | The broker of the four lanes. Each lane names an exchange and a queue, which only an AMQP transport takes, so this is an `amqp://` DSN. The failure transport stays in the database |
| `SYMFONY_TRUSTED_PROXIES` | not set | The proxies whose forwarded address Symfony reads, `framework.trusted_proxies`. The application names none |

The bundle reads its own default for the lanes, `BEFFROI_MESSENGER_DSN`, only where an application declares no
transport of the same name. This one declares all four, so that variable is not read here.

## The web server

These are read by Caddy and FrankenPHP, not by the kernel.

| Variable | What it decides |
|---|---|
| `SERVER_NAME` | The host Caddy serves the provider on, `localhost` when it is not set |
| `MTLS_SERVER_NAME` | The host of the listener that asks for a client certificate, in `mtls.Caddyfile` |
| `CADDY_EXTRA_CONFIG` | Configuration added to the `Caddyfile` beside the site of `SERVER_NAME`. `import mtls.Caddyfile` is what serves the host that asks for a client certificate |
| `CADDY_GLOBAL_OPTIONS` | Directives added to the global options of the `Caddyfile` |
| `CADDY_SERVER_EXTRA_DIRECTIVES` | Directives added to the site of `SERVER_NAME`, such as a `tls` directive naming a certificate and its key |
| `CADDY_SERVER_LOG_OPTIONS` | Directives added to the `log` block of each site |
| `FRANKENPHP_CONFIG` | Directives of the `frankenphp` block. The production image sets `import worker.Caddyfile`, which is worker mode |
| `FRANKENPHP_WORKER_CONFIG` | Directives added to the `worker` block: the `watch` lines of the development stack, nothing in production |

## The key management service

The DSN and the key identifier are what change from one backend to the next: the code and the envelope are
the same. An envelope sealed by one backend does not open with another.

=== "Sodium"

    A key inline in the environment, which is what the development stack provisions.

    ``` bash
    BEFFROI_KMS_DSN="sodium://?keys[signing]=<32 bytes, base64url>"
    BEFFROI_KMS_KEY_ID="signing"
    ```

    Whoever reads the environment of the process holds the master key.

=== "A file"

    The same sodium key read from a file of its own, one per tenant, outside the web root and outside the
    sealed keys: it holds against a dump of the storage, not against a compromise of the host.

    ``` bash
    BEFFROI_KMS_DSN="sodium+dir:///app/var/kms?ext=.key"
    BEFFROI_KMS_KEY_ID="beffroi-{tenant}"
    ```

    The file of the tenant `default` is `/app/var/kms/beffroi-default.key`: thirty-two bytes and nothing else,
    mode `0600` in a directory `0700`, which the development stack writes this way when it is missing:

    ``` bash
    umask 077 && mkdir -p /app/var/kms && chmod 700 /app/var/kms && head -c 32 /dev/urandom > /app/var/kms/beffroi-default.key
    ```

=== "HashiCorp Vault"

    The Transit engine wraps the data key of every envelope, and the private key never reaches Vault.

    ``` bash
    BEFFROI_KMS_DSN="hashicorp-vault-transit://<token>@<host>:8200"
    BEFFROI_KMS_KEY_ID="beffroi-{tenant}"
    ```

    The Transit key of a tenant is `beffroi-<slug>`, of type `aes256-gcm96` and created with `derived=true`:
    the envelope carries a context that binds it to its tenant, Vault honours a context on a derived key only,
    and the bridge refuses to seal under a key that is not one. The development stack also creates it not
    exportable, with no plaintext backup, and refuses its deletion. The token needs three paths and nothing
    else:

    ``` hcl
    path "transit/datakey/plaintext/beffroi-*" {
      capabilities = ["update"]
    }

    path "transit/decrypt/beffroi-*" {
      capabilities = ["update"]
    }

    path "transit/keys/beffroi-*" {
      capabilities = ["read"]
    }
    ```

    The Vault of the development stack is a dev server answering over plain HTTP, which its DSN says with
    `?scheme=http`.

=== "AWS KMS"

    A symmetric key of the account wraps the data key of every envelope.

    ``` bash
    BEFFROI_KMS_DSN="aws-kms://default?region=<region>"
    BEFFROI_KMS_KEY_ID="alias/beffroi-{tenant}"
    ```

    The credentials come from the DSN or from the provider chain of async-aws, and any host other than
    `default` in the DSN is a custom endpoint. The key of a tenant is a `SYMMETRIC_DEFAULT` key for
    `ENCRYPT_DECRYPT`, behind the alias `alias/beffroi-<slug>`, so a new key behind the same alias changes
    nothing in the configuration.

## What the files say

The configuration files are compiled into the container of the kernel when the image is built, so a change to
them reaches a deployment with a new image. Outside the development environment,
`config/packages/beffroi.yaml` says this:

| Section | What the application writes | What it means for a deployment |
|---|---|---|
| `tenant.look` | The logo at `/tenant-logo.svg`, a placeholder served from the issuer, and the colours `#1f6feb` on `#ffffff` | The mark and the colours of the tenant, on every page. A logo served from another host needs that origin in the `img-src` of `config/packages/nelmio_security.yaml`, and the host to answer `Cross-Origin-Resource-Policy: cross-origin`, the pages of the account requiring it |
| `tenant.self_served_claims` | Fourteen claims of OIDC Core §5.1, from `name` to `phone_number` | What a person may change of themselves on the page of their account. A tenant whose directory owns the data names none |
| `web_push.subject` | `mailto:operator@op.localhost` | Naming a subject turns web push on (RFC 8292 §2.1): a `mailto:` or `https:` URI at which a push service reaches the operator. Without the section, no push leaves the deployment |
| `saml.identity_provider` | Requests signed, a key staged for seven days and working for a year, metadata cached for a day | The tenant is a SAML identity provider and serves its metadata at `/saml/metadata`. Without the section, it draws no SAML key and serves no metadata |
| `tokens` | Codes for 60 seconds; refresh tokens for thirty days and ninety days at most from the authorization, the thirty days renewed at each rotation of the tokens that rotate, those of a public client bound to no key or certificate | The lifetimes the environment does not carry |
| `clients` | None | The clients of the deployment, declared as [your first client](../getting-started/your-first-client.md) is |

The application writes no `client_registration` outside development, so its tenant has no registration
endpoint. Everything else keeps the defaults of the bundle: an act of the journal and a change of a record are
kept 180 days, an origin may send 2400 requests a minute and an authenticated client 1200.

[:beffroi-arrow-right: The whole configuration tree](../reference/configuration.md)

## What only development reads

The blocks under `when@dev` declare what the development stack needs and nothing a deployment does: the clients
of the OpenID conformance suite and of the demonstrations, an open registration endpoint for the Dynamic OP
plan, a SAML service provider with the peers it is judged by, and an issuer of assertions it trusts. Their
variables are read in the development environment: `BEFFROI_REGISTRATION_MODE`, the `CONFORMANCE_*`,
`OIDC_DEMO_*` and `DEMO_*` secrets and key sets, `BEFFROI_DEV_USER_SUBJECT`, `BEFFROI_DEMO_HOST_IP`,
`APP_PROFILER` and `VAR_DUMPER_SERVER`. The demonstration of the flows is wired in the test environment of the
application's own suite as well, so three of them are read there too, `DEMO_SERVICE_SECRET`,
`DEMO_CIBA_POLL_SECRET` and `BEFFROI_DEV_USER_SUBJECT`, which `.env.test` gives as fixtures. A production
kernel reads none of them.
