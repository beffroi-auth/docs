---
title: Configuration
description: Every variable the application reads and what each one decides, the four key management backends, and what its configuration files say for a deployment.
---

# Configuration

Everything a deployment chooses is an environment variable: the issuer, the key management service, the
database, the lifetimes, the look of the tenant, the roles it plays and the lists of its policy. The
configuration files hold what stays the same from one deployment to the next, and the clients.

`apps/op/.env` holds the value an image takes when the deployment names none, and the production image
compiles it with `composer dump-env prod`. A real environment variable wins over it, which is how a deployment
says its own, and an empty one wins too: an empty `BEFFROI_SAML_IDENTITY_PROVIDER` turns off the identity
provider `.env` turns on. `.env` carries no secret of a deployment: the key management service, the key it
seals under and the secret of the kernel are empty there, and the database is the one of the development
stack. That stack writes its own secrets into `.env.local`, which is never committed and never reaches an image.

Each variable that fills the `beffroi:` tree is read when the container builds the service it reaches, not when the container is compiled,
so changing one asks for a restart of the processes and not for a new image. A value is held there to the
bounds the [configuration tree](../reference/configuration.md) sets for the option it fills, and to the rules
between options: a value out of bounds is refused by the first request or command that needs it, not when the
image is built.

[:beffroi-arrow-right: Whole deployments written with these variables](examples.md)

## What a deployment sets

`.env` carries the values of the development stack, and every deployment replaces these:

| Variable | Why |
|---|---|
| `APP_SECRET` | `.env` names none |
| `DATABASE_URL` | `.env` names the database of the development stack |
| `BEFFROI_ISSUER` and `DEFAULT_URI` | `.env` names the issuer of the development stack, `https://op.localhost` |
| `BEFFROI_KMS_DSN` and `BEFFROI_KMS_KEY_ID` | `.env` names no key management service, and nothing is sealed or signed without one |
| `SERVER_NAME` | The host Caddy serves, `localhost` when it is not set. Behind a proxy that terminates TLS, the host the proxy asks for, which `TLS_TERMINATION` serves over plain HTTP: [behind a proxy](deployment.md#behind-a-proxy) |

Three more decide what a deployment of real people does:

- `BEFFROI_REGISTRATION_MODE`, without which no client can exist: the image declares none, and a client
  reaches a deployment by registering itself.
- `BEFFROI_WEB_PUSH_SUBJECT`, the contact a push service is given, which `.env` sets to the one of the
  development stack.
- `SYMFONY_TRUSTED_PROXIES`, behind a proxy, without which every request has the address of the proxy.

## The provider

| Variable | In `.env` | What it decides |
|---|---|---|
| `BEFFROI_ISSUER` | `https://op.localhost` | The issuer of the tenant (OIDC Discovery 1.0 §3), which every token names and every client compares byte for byte: an absolute `https` URL with no query, no fragment and no trailing slash, plain HTTP on a loopback host only. The application imports its routes at the root, so its issuer is an origin with no path. A tenant keeps the issuer its row was written with: `beffroi:tenant:synchronize` refuses another |
| `BEFFROI_TENANT_SLUG` | `default` | The stable name of the tenant, from which its identifier is derived. Renaming it is creating another tenant, with other keys and other rows, so a deployment names it once |
| `BEFFROI_KMS_DSN` | empty | The key management service that seals the keys of the tenant, its pairwise salt and its data keys, as the DSN of the client `op` of `config/packages/key_management.yaml`. [The backends](#the-key-management-service) are below |
| `BEFFROI_KMS_KEY_ID` | empty | The master key of that service the tenant is sealed under. `{tenant}` in it stands for the slug of the tenant, one master key per tenant |
| `BEFFROI_KMS_DSN_SECOND` | empty | A second client, `second`, holding a key under the same identifier, for a run that moves the data keys from one to the other. Empty, the client is declared and never built |
| `BEFFROI_DATA_KEY_SECRETS` | not set | The secrets every data key of personal data is bound to its row under, as a JSON list, the one that binds a new row first. Not set, `APP_SECRET` alone binds them. [Operating it](operating.md#data-keys) says how a rotation of `APP_SECRET` uses it |
| `BEFFROI_PLANE` | `all` | The plane this process serves: `all`, `interaction` or `protocol`. A route of a plane the process does not serve answers `404` |
| `BEFFROI_MESSENGER_DSN` | `doctrine://default?queue_name={lane}` | Where the four lanes go: one DSN for the four, `{lane}` in it standing for the name of each lane, so that each is a queue of its own. A DSN that names no `{lane}` is refused when the transport of a lane is built. The value of `.env` is a queue of the table `messenger_messages` per lane, which the transport creates the first time it reaches it. The image carries the transport of no broker, so a deployment of it keeps its lanes in the database. A message that fails stays in the database whatever this names |
| `BEFFROI_MTLS_ORIGIN` | empty | The origin of the host that asks for a client certificate, announced in `mtls_endpoint_aliases` (RFC 8705 §5). Empty, the discovery document announces no alias, which is what a deployment serving one host leaves |
| `GEOIP_LICENSE_KEY` | empty | The licence key of the MaxMind account the GeoLite2 databases are downloaded under. Empty, nothing is downloaded, and every session and every act says an address and no place |
| `BEFFROI_BREACHED_PASSWORDS_ENDPOINT` | empty | The range endpoint a password is compared against before it is written (NIST SP 800-63B §3.1.1.2): `https://api.pwnedpasswords.com/range/`, where the first five hexadecimal characters of the SHA-1 of a password leave and the rest is compared locally. Empty, nobody is asked, and passwords are posed on the rules of the core alone |
| `BEFFROI_BREACHED_PASSWORDS_TIMEOUT` | `2` | The seconds one lookup in that list is given, a tenth of a second at least. A lookup still unanswered by then refuses the password |

## The tenant

Eight variables are lists of the configuration, three of them here. Each is a JSON document of the shape the
list has in the [configuration tree](../reference/configuration.md), `[]` or `{}` for none. An empty variable
is no JSON document, and is refused.

| Variable | In `.env` | What it decides |
|---|---|---|
| `BEFFROI_TENANT_NAME` | empty | What the pages and the consent call the tenant. Empty, the host of the issuer |
| `BEFFROI_TENANT_LOGO_URI` | empty | The logo every page shows, an absolute `https` URL. Empty, the placeholder mark the image serves at `/tenant-logo.svg` under the issuer. Every page that shows the logo names its origin in its `img-src`. A logo served from another host shows on the pages served under `Cross-Origin-Embedder-Policy: require-corp`, every page but those of `/authorize`, `/login`, `/consent`, `/logout`, `/device` and `/initiate-login`, only when that host answers `Cross-Origin-Resource-Policy: cross-origin` |
| `BEFFROI_TENANT_PRIMARY_COLOR` | `#1f6feb` | The colour the buttons and the links of the pages are drawn in: `#` and three or six hexadecimal digits. Named with the next one or not at all, an empty variable being no colour |
| `BEFFROI_TENANT_PRIMARY_CONTENT_COLOR` | `#ffffff` | The colour of what is written on it, in the same notation |
| `BEFFROI_TENANT_SELF_SERVED_CLAIMS` | the fourteen claims of OIDC Core §5.1 the application lets a person change, from `name` to `phone_number` | What a person may change of themselves on the page of their account. A tenant whose directory owns the data names `[]` |
| `BEFFROI_TENANT_AUTHENTICATION_CLASSES` | `{}` | The `acr` vocabulary of the tenant, class name to predicate, in order. `{}` is the default policy of the core |
| `BEFFROI_TENANT_SCOPES` | `[]` | The scopes of the APIs the tenant protects, as `["invoices.read","invoices.pay"]`. The tenant hands out tokens for them beside `openid`, the scopes of its claims and `offline_access`, announces them, and a client that registers itself may register them |

**Six of them are written in the row of the tenant**, with its issuer: its name, its logo and its two colours,
the claims a person changes and its `acr` classes. `beffroi:tenant:synchronize` writes them, and every request
and every message compares the row with the environment of its process: while the two differ, each one that
reads the tenant fails, and the log names the setting that differs, `look` for the logo and the colours,
while the timed steps wait. Changing one of them is therefore a restart of
every process with the new value, and `bin/console beffroi:tenant:synchronize` run in one of them; a process
still on the previous value stops serving from that moment.

## Keys and lifetimes

In seconds. [`keys`](../reference/configuration.md#keys) and [`tokens`](../reference/configuration.md#tokens)
say what each one decides.

| Variable | In `.env` | What it decides |
|---|---|---|
| `BEFFROI_JWKS_MAX_AGE` | `300` | How long a relying party may cache the JWK Set (RFC 7517 §5) |
| `BEFFROI_KEY_STAGING_DELAY` | empty | How long a new key is published before it signs. Empty, `BEFFROI_JWKS_MAX_AGE` plus sixty seconds, the delay after which Symfony's `oidc_login` reads the set again for a `kid` it does not hold: 360 with the values of `.env`. The SAML signing key has [its own](#saml) |
| `BEFFROI_KEY_AGE` | `7776000`, ninety days | How long a key signs before a successor is staged behind it |
| `BEFFROI_ACCESS_TOKEN_TTL` | `600` | The lifetime of an access token, whether it is an `at+jwt` or an opaque reference |
| `BEFFROI_ID_TOKEN_TTL` | `600` | The lifetime of an ID token |
| `BEFFROI_AUTHORIZATION_CODE_TTL` | `60` | How long an authorization code can be spent, 600 at most (RFC 6749 §4.1.2) |
| `BEFFROI_REFRESH_TOKEN_TTL` | `2592000`, thirty days | The sliding lifetime of a refresh token, renewed at each rotation, and never longer than the absolute one |
| `BEFFROI_REFRESH_TOKEN_ABSOLUTE_TTL` | `7776000`, ninety days | The lifetime of a family of refresh tokens, counted from the authorization that started it |
| `BEFFROI_REQUEST_URI_TTL` | `60` | The lifetime of the `request_uri` of a pushed request, 600 at most (RFC 9126 §2.2) |
| `BEFFROI_DEVICE_CODE_TTL` | `600` | The lifetime of a device code and its user code, 1800 at most (RFC 8628 §3.2) |
| `BEFFROI_BACKCHANNEL_AUTHENTICATION_TTL` | `300` | The lifetime of a backchannel request whose client asks for none, 3600 at most (CIBA Core §7.1) |
| `BEFFROI_DEVICE_CODE_INTERVAL` | `5` | The seconds a device waits between two polls, 30 at most (RFC 8628 §3.5) |
| `BEFFROI_BACKCHANNEL_AUTHENTICATION_INTERVAL` | `5` | The seconds a client of the backchannel flow waits between two polls, 30 at most (CIBA Core §11) |
| `BEFFROI_BACKCHANNEL_AUTHENTICATION_MAX_REQUESTED_EXPIRY` | `1800` | The longest lifetime a client may ask for with `requested_expiry`, 3600 at most (CIBA Core §7.1) |

Every lifetime is a second at least.

## Clients and their requests

| Variable | In `.env` | What it decides |
|---|---|---|
| `BEFFROI_DPOP_NONCE_REQUIRED` | `false` | Whether a DPoP proof carries a nonce this provider issued (RFC 9449 §8), `true` or `false` |
| `BEFFROI_DPOP_PROOF_MAX_AGE` | `60` | How long a proof stands from its `iat`, a second at least (RFC 9449 §11.1) |
| `BEFFROI_DPOP_LEEWAY` | `30` | What is allowed of the clock of its client, both ways, none at least |
| `BEFFROI_DPOP_NONCE_TTL` | `300` | How long a nonce this provider issued is accepted, a second at least |
| `BEFFROI_INTERACTION_LOGIN_HINT` | `sub` | What a `login_hint` names on the login page (OIDC Core §3.1.2.1): `sub`, the subject this provider issued to the client, `username`, the name a person signs in with, or `none` |
| `BEFFROI_BACKCHANNEL_AUTHENTICATION_LOGIN_HINT` | `sub` | What a `login_hint` names in a backchannel request (CIBA Core §7.1), among the same three |
| `BEFFROI_CLIENT_ASSERTION_MAX_LIFETIME` | `300` | How long an assertion a client signs to authenticate may stand ahead of the request, a second at least (RFC 7523 §3). The trusted issuers are held to it too |
| `BEFFROI_CLIENT_ASSERTION_LEEWAY` | `30` | What is allowed of the clock of its signer, none at least |
| `BEFFROI_JWKS_URI_TIMEOUT` | `3` | The seconds one read of the `jwks_uri` of a client or of a trusted issuer is given, a tenth of a second at least |
| `BEFFROI_JWKS_URI_MAX_SIZE` | `65536` | The bytes that read may answer, one at least |
| `BEFFROI_JWKS_URI_TTL` | `86400` | How long the keys read back are kept, a second at least |
| `BEFFROI_JWKS_URI_REFETCH_COOLDOWN` | `300` | How often a `kid` the kept set does not hold may cost another read, none at least |
| `BEFFROI_REQUEST_OBJECT_MAX_LIFETIME` | `3600` | How long a request object may stand from its `nbf`, a second at least (RFC 9101 §4) |
| `BEFFROI_REQUEST_OBJECT_LEEWAY` | `30` | What is allowed of the clock of its client, none at least |
| `BEFFROI_REQUEST_OBJECT_TIMEOUT` | `3` | The seconds one read of a `request_uri` a client hosts is given, a tenth of a second at least |
| `BEFFROI_REQUEST_OBJECT_MAX_SIZE` | `65536` | The bytes that read may answer, one at least |
| `BEFFROI_TRUSTED_ISSUERS` | `{}` | The issuers whose assertions the tenant accepts as an authorization (RFC 7523 §2.1), keyed by the `iss` they sign with |

## Registration

| Variable | In `.env` | What it decides |
|---|---|---|
| `BEFFROI_REGISTRATION_MODE` | empty | What authorises a client that registers itself (RFC 7591): `initial_access_token`, a credential `beffroi:client:token:issue` issues; `software_statement`, a statement of an authority the tenant pins (RFC 7591 §2.3); or `open`, whoever asks, which only a tenant with no real user writes. Empty, the tenant has no registration endpoint at all, in its discovery document as on the wire |
| `BEFFROI_REGISTRATION_DEFAULT_SCOPE` | empty | The scopes a client that names none is registered with, space-delimited (RFC 7591 §2). Empty, `openid` alone |
| `BEFFROI_REGISTRATION_KEEP_A_CLIENT_UNUSED_FOR` | `7776000`, ninety days | How long a client that registered itself is kept unused once it was used, a second at least |
| `BEFFROI_REGISTRATION_KEEP_A_CLIENT_NEVER_USED_FOR` | `604800`, seven days | How long it is kept when it never was, a second at least |
| `BEFFROI_REGISTRATION_SECTOR_IDENTIFIER_TIMEOUT` | `3` | The seconds one read of its `sector_identifier_uri` is given, a tenth of a second at least (OIDC Registration §5) |
| `BEFFROI_REGISTRATION_SECTOR_IDENTIFIER_MAX_SIZE` | `65536` | The bytes that read may answer, one at least |
| `BEFFROI_REGISTRATION_STATEMENT_MAX_LIFETIME` | `300` | How long a software statement may stand ahead of the request, a second at least (RFC 7591 §2.3) |
| `BEFFROI_REGISTRATION_STATEMENT_LEEWAY` | `30` | What is allowed of the clock of its authority, none at least |
| `BEFFROI_REGISTRATION_STATEMENT_ISSUERS` | `{}` | The authorities whose software statements the tenant accepts, keyed by the `iss` they sign with, which the mode `software_statement` reads |

## Notifications

| Variable | In `.env` | What it decides |
|---|---|---|
| `BEFFROI_WEB_PUSH_SUBJECT` | `mailto:operator@op.localhost` | The contact a push service is given (RFC 8292 §2.1), a `mailto:` or `https:` URI at which the operator of the deployment can be reached. Naming one turns [web push](web-push.md) on, and empty turns it off: the tenant then hands out no key and reaches nobody by push. The one of `.env` is the development stack's, so a deployment names its own |
| `BEFFROI_WEB_PUSH_TIMEOUT` | `3` | The seconds one push is given, a tenth of a second at least |
| `BEFFROI_BACK_CHANNEL_LOGOUT_TIMEOUT` | `5` | The seconds one attempt to send a logout token to a client is given, a tenth of a second at least (Back-Channel Logout 1.0 §2.5) |
| `BEFFROI_BACK_CHANNEL_LOGOUT_RETRIES` | `6` | How many times a send that did not reach its client comes back, none at least |
| `BEFFROI_BACK_CHANNEL_LOGOUT_RETRY_DELAY` | `2` | The wait before the first return, a second at least |
| `BEFFROI_BACK_CHANNEL_LOGOUT_RETRY_MULTIPLIER` | `3` | What each wait is multiplied by to give the next, once at least |
| `BEFFROI_BACK_CHANNEL_LOGOUT_RETRY_MAX_DELAY` | `60` | The longest wait, a second at least |
| `BEFFROI_CLIENT_NOTIFICATION_TIMEOUT` | `3` | The seconds the call that tells a client its backchannel request was answered is given, a tenth of a second at least (CIBA Core §10.2) |

The four figures of the returns are the schedule of the whole lane of notifications, which carries the pushes
and the notifications of the backchannel flow as well as the logout tokens.

## SAML

| Variable | In `.env` | What it decides |
|---|---|---|
| `BEFFROI_SAML_IDENTITY_PROVIDER` | `true` | Whether the tenant is a [SAML identity provider](../saml/identity-provider.md), `true` or `false`: its metadata at `/saml/metadata`, and the service providers below |
| `BEFFROI_SAML_SERVICE_PROVIDER` | `false` | Whether the tenant is a [SAML service provider](../saml/upstream-identity-providers.md) to the upstream identity providers below |
| `BEFFROI_SAML_SERVICE_PROVIDER_ENTITY_ID` | empty | The entity ID of that service provider, absolute, and never the one of the identity provider. Empty, the URL of its metadata |
| `BEFFROI_SAML_KEY_STAGING_DELAY` | `604800`, seven days | How long a new SAML key is published before it signs, none at least |
| `BEFFROI_SAML_KEY_AGE` | `31536000`, a year | How long a SAML key works before a successor is staged behind it, a second at least |
| `BEFFROI_SAML_METADATA_CACHE_DURATION` | `86400`, a day | How long a service provider keeps the metadata, a second at least and shorter than the staging delay |
| `BEFFROI_SAML_WANT_AUTHN_REQUESTS_SIGNED` | `true` | Whether the metadata ask a service provider to sign its requests |
| `BEFFROI_SAML_SERVICE_PROVIDERS` | `{}` | The [service providers](../saml/service-providers.md) the identity provider serves, keyed by entity ID |
| `BEFFROI_SAML_IDENTITY_PROVIDERS` | `{}` | The [upstream identity providers](../saml/upstream-identity-providers.md) the service provider receives assertions of, keyed by entity ID |

The routes and services of both roles are in every image. A role turned off serves nothing, and a list that
names a peer of it is refused whole wherever it is read, the sign-in and the logout among them, until the role
is turned on again or the list is emptied. With both off, the tenant draws no SAML key.
The SAML key is the key of both roles, rotated by the three figures above whichever role is on.

## The journal and the load

| Variable | In `.env` | What it decides |
|---|---|---|
| `BEFFROI_JOURNAL_RETENTION` | `180` | How long an act of the journal is kept, in days |
| `BEFFROI_HISTORY_RETENTION` | `180` | How long a change of a claim is kept, in days |
| `BEFFROI_LOAD_ORIGIN_LIMIT` | `2400` | The requests one client address may send in a window |
| `BEFFROI_LOAD_ORIGIN_INTERVAL` | `60` | That window, in seconds |
| `BEFFROI_LOAD_CLIENT_LIMIT` | `1200` | The requests one authenticated client may send in a window |
| `BEFFROI_LOAD_CLIENT_INTERVAL` | `60` | That window, in seconds |

A budget too low on `/token` or on `/jwks` is an outage a deployment inflicts on itself, so both are measured
on what its own clients send.

## Symfony and the database

| Variable | In `.env` | What it decides |
|---|---|---|
| `APP_ENV` | `dev` | The environment of the kernel. The production image sets `prod` |
| `APP_DEBUG` | not set | Whether the kernel runs in debug mode, off in `prod` when it is not set. The image compiles its container with debug off |
| `APP_SECRET` | empty | The secret of the kernel, `framework.secret`. `.env.dev` and `.env.test` give one each, for their own environment, so a production environment names its own. While `BEFFROI_DATA_KEY_SECRETS` is not set, it is also the secret every data key of personal data is bound to its row under: the store of the data keys refuses an empty one the first time it is used, and changing it alone leaves the personal data unreadable: [operating it](operating.md#data-keys) says how it is replaced |
| `APP_SHARE_DIR` | `var/share` | The share directory of Symfony, one per environment beneath it, `var/share/prod` for a production kernel. It holds the filesystem pool of `cache.app`, and with it the [caches the processes share](deployment.md#what-the-processes-share). It is compiled into the container when the image is built: set when a container starts, it moves nothing |
| `DEFAULT_URI` | `https://op.localhost` | The URL Symfony generates absolute URLs under outside a request, in the console and in the worker, `framework.router.default_uri`: the issuer |
| `DEFAULT_LOCALE` | `en` | The language a page falls back to, among the two the application serves, `en` and `fr` |
| `DATABASE_URL` | `postgresql://beffroi:beffroi@127.0.0.1:5432/beffroi?serverVersion=16&charset=utf8` | The PostgreSQL database. The entrypoint of the image waits for it, and the migrations refuse any other platform |
| `SYMFONY_TRUSTED_PROXIES` | not set | The proxies whose forwarded address and scheme Symfony reads, `framework.trusted_proxies`. The application names none. Behind a proxy that terminates TLS, a deployment names it: without it, every request reads as plain HTTP from the address of the proxy. Addresses or networks separated by commas, `private_ranges` standing for every private network |
| `SYMFONY_TRUSTED_HEADERS` | not set | The headers Symfony reads from those proxies, separated by commas. Not set, `x-forwarded-for`, `x-forwarded-port` and `x-forwarded-proto` |
| `SYMFONY_TRUSTED_HOSTS` | not set | The hosts a request may name, as regular expressions separated by commas, `framework.trusted_hosts`. A request that names another is refused with `400`. Not set, every host |
| `SYMFONY_TRUST_X_SENDFILE_TYPE_HEADER` | not set | Whether a file Symfony answers with, a script of the provider, is handed to a proxy that asks for it with `X-Sendfile-Type`. Not set, never |
| `FRANKENPHP_LOOP_MAX` | not set | The requests a PHP worker of the server serves before it restarts, read by the runtime of Symfony: 500 when it is not set, never with `0` or a negative number |

The kernel and the runtime of Symfony read others, which a deployment leaves unset, among them `APP_RUNTIME`,
`APP_RUNTIME_OPTIONS`, `APP_RUNTIME_ENV` and `APP_RUNTIME_MODE`, which choose and describe the runtime the
image ships with, `APP_CACHE_DIR` and `APP_BUILD_DIR`, which move the directories the image compiled its
container into, and `APP_LOG_DIR`, which moves its logs.

## The web server

These are read by Caddy and FrankenPHP, not by the kernel.

| Variable | What it decides |
|---|---|
| `SERVER_NAME` | The host Caddy serves the provider on, `localhost` when it is not set. When Caddy terminates TLS, it obtains the certificate of that host itself, from a public authority for a public name and from its internal authority for `localhost`, and keeps it under `/data` |
| `TLS_TERMINATION` | Who terminates the TLS of the site of `SERVER_NAME`. `caddy`, when it is not set: Caddy, with the TLS a FAPI 1 plan measures. `proxy`: a proxy in front of the image, which sends the site plain HTTP, `SERVER_NAME` then naming the one host the proxy asks for, or `:<port>` for any host, without a scheme. Any other value stops Caddy from starting. The host that asks for a client certificate keeps its own TLS either way |
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

    It is the backend of a deployment that has no key management service.
    [The Compose file of the image](../getting-started/the-standalone-application.md#the-compose-file-of-the-image)
    keeps that directory in a volume of its own, mounted on the server and on the worker, and its header gives
    the same command, run in the image, to draw the key into it once before anything is sealed.

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
them reaches a deployment with a new image. `config/packages/beffroi.yaml` names a variable for every option a
deployment chooses, and compiles only what is the same for every deployment of the image:

| Section | What the application writes | What it means for a deployment |
|---|---|---|
| `keys.kms` | `op` | The client of `config/packages/key_management.yaml` the keys are sealed with, built from `BEFFROI_KMS_DSN` |
| `keys.storage`, `webauthn.metadata_storage`, `geoip.storage` | `var/keys`, `var/webauthn` and `var/geoip` under the application | The directories of the sealed keys, of the FIDO metadata and of the GeoLite2 databases |
| `clients` | None | The image declares no client: a client registers itself, as [your first client](../getting-started/your-first-client.md) does |

No variable sets the exemption of confidential clients from PKCE either: the application leaves
`client_registration.exempt_confidential_clients_from_pkce` at `false`, so every client registers with PKCE
required.

[:beffroi-arrow-right: The whole configuration tree](../reference/configuration.md)

## What only development reads

The image leaves out what only the development stack, the suite of the application and its lab read:
`config/packages/dev/`, the debug bundle and the profiler, the demonstration of the flows and the lab.
`config/packages/dev/beffroi.yaml` declares what the development stack needs and nothing a deployment does:
the clients of the OpenID conformance suite and of the demonstrations, the registration policy of the Dynamic
OP plan, a SAML service provider with the peers it is judged by, an authority whose software statements it
accepts and an issuer of assertions it trusts. Its lists replace the JSON documents the environment carries for
them.

Their variables are read in the development environment: the `CONFORMANCE_*`, `OIDC_DEMO_*` and `DEMO_*`
secrets and key sets, `BEFFROI_DEV_USER_SUBJECT`, `BEFFROI_DEMO_HOST_IP`, `APP_PROFILER` and
`VAR_DUMPER_SERVER`. The development stack writes the secrets and the key sets into `.env.local`, and `open`
there for `BEFFROI_REGISTRATION_MODE`, which it reads as every deployment does. The demonstration of the flows is wired in
the test environment of the application's own suite as well, so three of them are read there too,
`DEMO_SERVICE_SECRET`, `DEMO_CIBA_POLL_SECRET` and `BEFFROI_DEV_USER_SUBJECT`, which `.env.test` gives as
fixtures. A production kernel reads none of them.
