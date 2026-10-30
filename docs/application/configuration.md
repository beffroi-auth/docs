---
title: Configuration
description: Every environment variable the image reads, the value it takes when a deployment names none, what it decides and the bounds it is held to.
---

# Configuration

A deployment of the image is configured by its environment and by nothing else: no configuration file is
mounted and no image is rebuilt to change what belongs to the deployment. The image compiles `apps/op/.env` when it is built,
and a variable the deployment does not set takes the value written there, which the column *In the image*
gives below. A variable the deployment sets wins, an empty one included: an empty
`BEFFROI_SAML_IDENTITY_PROVIDER` turns off the identity provider the image turns on.

A process reads a variable when it first builds what the variable changes, and keeps the value for its
lifetime. A change therefore takes effect when the processes restart, and needs no new image. A value outside
its bounds is refused at that moment, by the first request or the first message that needs it, and by every
one after it until the value is corrected; the log says what was refused.

[:beffroi-arrow-right: Whole deployments written with these variables](examples.md)

## What a deployment sets

The image carries the values of the development stack, and these have to be replaced by every deployment:

| Variable | Why |
|---|---|
| `APP_SECRET` | The image names none for production |
| `DATABASE_URL` | The image names the database of the development stack |
| `BEFFROI_ISSUER` and `DEFAULT_URI` | The image names the issuer of the development stack, `https://op.localhost` |
| `BEFFROI_KMS_DSN` and `BEFFROI_KMS_KEY_ID` | The image names no key management service, and nothing is sealed or signed without one |
| `SERVER_NAME` | The host the image serves and obtains a certificate for, `localhost` otherwise. Behind a proxy that terminates TLS, the host the proxy asks for, which `TLS_TERMINATION` serves over plain HTTP: [behind a proxy](examples.md#behind-a-proxy-that-terminates-tls) |

Three more decide what a deployment of real people does:

- `BEFFROI_REGISTRATION_MODE`, without which no client can exist: the image declares none, and a client
  reaches a deployment by registering itself.
- `BEFFROI_WEB_PUSH_SUBJECT`, the contact a push service is given, which the image sets to the one of the
  development stack.
- `SYMFONY_TRUSTED_PROXIES`, behind a proxy, without which every request has the address of the proxy.

## The provider

| Variable | In the image | What it decides |
|---|---|---|
| `BEFFROI_ISSUER` | `https://op.localhost` | The issuer of the tenant (OIDC Discovery 1.0 §3), which every token names and every client compares byte for byte: an absolute `https` URL with no query, no fragment, no credentials and no trailing slash, plain `http` on a loopback host only. The routes are served at the root, so the issuer is an origin with no path. A tenant keeps the issuer its row was written with: `beffroi:tenant:synchronize` refuses another |
| `DEFAULT_URI` | `https://op.localhost` | The URL Symfony builds absolute URLs under outside a request, in the console and in the worker: the issuer |
| `BEFFROI_TENANT_SLUG` | `default` | The stable name of the tenant, from which its identifier is derived, and which `{tenant}` stands for in `BEFFROI_KMS_KEY_ID`. Another slug is another tenant, with other rows and other keys |
| `BEFFROI_PLANE` | `all` | The plane this process serves: `all`, `interaction` or `protocol`. A route of a plane the process does not serve answers `404`: [the two planes](deployment.md#the-two-planes) |
| `BEFFROI_MTLS_ORIGIN` | empty | The origin of the host that asks for a client certificate, announced in `mtls_endpoint_aliases` (RFC 8705 §5). Empty, the discovery document announces no alias, which is what a deployment serving one host leaves |
| `DEFAULT_LOCALE` | `en` | The language a page falls back to, among the two the application serves, `en` and `fr` |

## The tenant

| Variable | In the image | What it decides |
|---|---|---|
| `BEFFROI_TENANT_NAME` | empty | What the pages and the consent call the tenant. Empty, the host of the issuer |
| `BEFFROI_TENANT_LOGO_URI` | empty | The logo every page shows, an absolute `https` URL. Empty, the placeholder mark the image serves at `/tenant-logo.svg` of the issuer. The content policy of the image lets a page load images from the issuer alone, and the consent page adds the origin of this logo: a logo served from another origin shows on the consent page only |
| `BEFFROI_TENANT_PRIMARY_COLOR` | `#1f6feb` | The colour the buttons and the links of the pages are drawn in: `#` and three or six hexadecimal digits. Set together with the next one or not at all; empty, no colour |
| `BEFFROI_TENANT_PRIMARY_CONTENT_COLOR` | `#ffffff` | The colour of what is written on the first one, in the same notation |
| `BEFFROI_TENANT_SELF_SERVED_CLAIMS` | the fourteen claims below | A JSON list of the claims of OIDC Core §5.1 a person may change of themselves on the page of their account. The image lists the fourteen the bundle lets a person change: `name`, `given_name`, `family_name`, `middle_name`, `nickname`, `preferred_username`, `birthdate`, `gender`, `locale`, `zoneinfo`, `profile`, `picture`, `website` and `phone_number`. `[]` for a tenant whose directory owns them |
| `BEFFROI_TENANT_AUTHENTICATION_CLASSES` | `{}` | A JSON object, the `acr` vocabulary of the tenant: each class name on a predicate, in the order a session is answered in. `{}` is the default policy, `phrh`, `phr`, `2` and `1`. [The shape](../reference/configuration.md#tenant) |

**These six are written in the row of the tenant, with its issuer.** `beffroi:tenant:synchronize` writes
them, and every process compares the row with its own environment: while the two differ, every request that
reads the tenant fails, and the log says which setting differs. Changing one of them is therefore a restart of
every process with the new value, and `bin/console beffroi:tenant:synchronize` run in one of them; a process
still on the previous value stops serving from that moment.

## Keys and secrets

| Variable | In the image | What it decides |
|---|---|---|
| `BEFFROI_KMS_DSN` | empty | The key management service that seals the keys of the tenant, its pairwise salt and its data keys, as a DSN of `symfony/key-management`: [the backends](#the-key-management-service) are below |
| `BEFFROI_KMS_KEY_ID` | empty | The master key of that service the tenant is sealed under. `{tenant}` in it stands for the slug of the tenant, one master key per tenant |
| `BEFFROI_KMS_DSN_SECOND` | empty | A second client, `second`, for a run that moves the data keys from one master key to another: [operating it](operating.md#data-keys). Empty, the client is declared and never built |
| `BEFFROI_JWKS_MAX_AGE` | `300` | How long a relying party may keep the JWK Set (RFC 7517 §5), in seconds, `0` or more: its `Cache-Control: max-age`, which the SAML metadata are served with as well |
| `BEFFROI_KEY_STAGING_DELAY` | empty | How long a new key is published before it signs, in seconds, `0` or more. Empty, `BEFFROI_JWKS_MAX_AGE` plus 60, the delay after which Symfony's `oidc_login` reads the set again for a `kid` it does not hold. The SAML keys have their own, below |
| `BEFFROI_KEY_AGE` | `7776000` | How long a key signs before the timed step stages a successor behind it, in seconds: ninety days. It is longer than the time a retiring key of its use stays published, which the timed step refuses otherwise when it runs. The SAML keys have their own |
| `APP_SECRET` | empty | The secret of the kernel, `framework.secret`. While `BEFFROI_DATA_KEY_SECRETS` is not set, it is also the one secret every data key of personal data is bound to its row under: the store of the data keys refuses an empty one the first time it is used, and a new value alone leaves the personal data unreadable, which [operating it](operating.md#data-keys) says how to avoid |
| `BEFFROI_DATA_KEY_SECRETS` | not set | A JSON list of the secrets the data keys are bound under. The first one binds a new key, and a key bound under any of them opens. Not set, `APP_SECRET` alone |

## The database and the lanes

| Variable | In the image | What it decides |
|---|---|---|
| `DATABASE_URL` | `postgresql://beffroi:beffroi@127.0.0.1:5432/beffroi?serverVersion=16&charset=utf8` | The PostgreSQL database, as a URL of Doctrine DBAL. The entrypoint of the image waits for it before it starts the server, the worker or a command, and the migrations refuse any other platform |
| `BEFFROI_MESSENGER_DSN` | `doctrine://default?queue_name={lane}` | Where the four lanes of the provider go, one DSN for the four: `{lane}` stands where the name of each lane is written, so that each lane is a queue of its own. In the image, a queue each of the table `messenger_messages` of the database, which the transport creates the first time it reaches it. The application requires the transport of no broker, so the image takes a `doctrine://` DSN alone. A DSN without `{lane}` is refused when the transport of a lane is built. What fails for good stays in the database, whatever this names |

## Symfony

| Variable | In the image | What it decides |
|---|---|---|
| `APP_ENV` | `prod` | The environment of the kernel. The image is built and compiled for `prod` |
| `APP_DEBUG` | not set | Whether the kernel runs in debug mode, off in `prod` when it is not set. The image compiles its container with debug off, and a kernel started with it on fails to build its own |
| `SYMFONY_TRUSTED_PROXIES` | not set | The proxies whose forwarded headers Symfony reads, as addresses or networks separated by commas, `private_ranges` standing for every private network. Not set, none: behind a proxy, every request has its address |
| `SYMFONY_TRUSTED_HEADERS` | not set | The headers Symfony reads from those proxies, separated by commas. Not set, `x-forwarded-for`, `x-forwarded-port` and `x-forwarded-proto` |
| `SYMFONY_TRUSTED_HOSTS` | not set | The hosts a request may name, as regular expressions separated by commas. A request that names another is refused with `400`. Not set, every host |
| `SYMFONY_TRUST_X_SENDFILE_TYPE_HEADER` | not set | Whether a file Symfony answers with, a script of the bundle, is handed to a proxy that asks for it with `X-Sendfile-Type`. Not set, never |
| `FRANKENPHP_LOOP_MAX` | not set | The requests a PHP worker of the server serves before it restarts, read by the runtime of Symfony: 500 when it is not set, never with `0` or a negative number |

The kernel and the runtime of Symfony read seven more, which a deployment leaves unset: `APP_RUNTIME`,
`APP_RUNTIME_OPTIONS`, `APP_RUNTIME_ENV` and `APP_RUNTIME_MODE`, which choose and describe the runtime the
image ships with, and `APP_CACHE_DIR`, `APP_BUILD_DIR` and `APP_LOG_DIR`, which move the directories the image
compiled its container into.

## Lifetimes

Every lifetime is in seconds and one second at least.

| Variable | In the image | What it decides |
|---|---|---|
| `BEFFROI_ACCESS_TOKEN_TTL` | `600` | The lifetime of an access token, whether it is an `at+jwt` or an opaque reference |
| `BEFFROI_ID_TOKEN_TTL` | `600` | The lifetime of an ID token |
| `BEFFROI_AUTHORIZATION_CODE_TTL` | `60` | The lifetime of an authorization code, 600 at most (RFC 6749 §4.1.2) |
| `BEFFROI_REFRESH_TOKEN_TTL` | `2592000` | The lifetime of a refresh token, thirty days, renewed at each rotation of a token that rotates. It is never longer than the next one |
| `BEFFROI_REFRESH_TOKEN_ABSOLUTE_TTL` | `7776000` | How long the refresh tokens of one authorization live at most, counted from the authorization whatever their rotations: ninety days |
| `BEFFROI_REQUEST_URI_TTL` | `60` | The lifetime of the `request_uri` of a pushed request (RFC 9126 §2.2), 600 at most |
| `BEFFROI_DEVICE_CODE_TTL` | `600` | The lifetime of a device code (RFC 8628 §3.2), 1800 at most |
| `BEFFROI_DEVICE_CODE_INTERVAL` | `5` | The `interval` a device waits between two polls (RFC 8628 §3.2), 30 at most |
| `BEFFROI_BACKCHANNEL_AUTHENTICATION_TTL` | `300` | The lifetime of a backchannel request whose client sends no `requested_expiry` (CIBA Core §7.3), 3600 at most and never longer than the longest one a client may ask for |
| `BEFFROI_BACKCHANNEL_AUTHENTICATION_INTERVAL` | `5` | The `interval` a client of that flow waits between two polls (CIBA Core §7.3), 30 at most |
| `BEFFROI_BACKCHANNEL_AUTHENTICATION_MAX_REQUESTED_EXPIRY` | `1800` | The longest `requested_expiry` such a client may ask for (CIBA Core §7.1), 3600 at most. A request that asks for more is served this, not refused |

## Clients that register themselves

| Variable | In the image | What it decides |
|---|---|---|
| `BEFFROI_REGISTRATION_MODE` | empty | What authorises a registration: `initial_access_token`, a token `beffroi:client:token:issue` issues (RFC 7591 §1.2); `software_statement`, a statement of an authority of `BEFFROI_REGISTRATION_STATEMENT_ISSUERS` (RFC 7591 §2.3); `open`, whoever asks (RFC 7591 §1.3), for a tenant with no real user. Empty, the tenant has no registration endpoint: [dynamic registration](../oidc/dynamic-registration.md) |
| `BEFFROI_REGISTRATION_DEFAULT_SCOPE` | empty | What a client that names no `scope` is registered with, space-delimited (RFC 7591 §2). Empty, `openid` alone |
| `BEFFROI_REGISTRATION_KEEP_A_CLIENT_UNUSED_FOR` | `7776000` | Seconds a registered client that was used may go unused before it is deleted, one at least: ninety days |
| `BEFFROI_REGISTRATION_KEEP_A_CLIENT_NEVER_USED_FOR` | `604800` | Seconds a registered client that was never used lives, one at least: seven days |
| `BEFFROI_REGISTRATION_SECTOR_IDENTIFIER_TIMEOUT` | `3` | Seconds one read of a `sector_identifier_uri` is given (OIDC Registration §5), 0.1 at least |
| `BEFFROI_REGISTRATION_SECTOR_IDENTIFIER_MAX_SIZE` | `65536` | Bytes such a document may answer before the read stops, one at least |
| `BEFFROI_REGISTRATION_STATEMENT_MAX_LIFETIME` | `300` | How far ahead of the request the `exp` of a software statement may be (RFC 7591 §2.3), one second at least |
| `BEFFROI_REGISTRATION_STATEMENT_LEEWAY` | `30` | Seconds allowed for the clock of an authority, both ways, `0` or more |
| `BEFFROI_REGISTRATION_STATEMENT_ISSUERS` | `{}` | A JSON object, the authorities whose software statements the tenant accepts, keyed by the `iss` they sign with: [the shape](../reference/configuration.md#client_registration) |

## Clients, their keys and their requests

| Variable | In the image | What it decides |
|---|---|---|
| `BEFFROI_CLIENT_ASSERTION_MAX_LIFETIME` | `300` | How far ahead of the request the `exp` of an assertion a client signs to authenticate may be (RFC 7523 §3), one second at least. The assertions of a trusted issuer are held to it as well |
| `BEFFROI_CLIENT_ASSERTION_LEEWAY` | `30` | Seconds allowed for the clock of a client or of a trusted issuer, both ways, `0` or more |
| `BEFFROI_JWKS_URI_TIMEOUT` | `3` | Seconds one read of the `jwks_uri` of a client or of a trusted issuer is given, 0.1 at least |
| `BEFFROI_JWKS_URI_MAX_SIZE` | `65536` | Bytes such a JWK Set may answer before the read stops, one at least |
| `BEFFROI_JWKS_URI_TTL` | `86400` | Seconds the keys read back are kept, one at least: a day |
| `BEFFROI_JWKS_URI_REFETCH_COOLDOWN` | `300` | Seconds between two reads caused by a `kid` the kept set does not hold, `0` or more |
| `BEFFROI_REQUEST_OBJECT_MAX_LIFETIME` | `3600` | How long a request object may stand from its `nbf` (RFC 9101 §4), one second at least |
| `BEFFROI_REQUEST_OBJECT_LEEWAY` | `30` | Seconds allowed for the clock of the client that signed it, both ways, `0` or more |
| `BEFFROI_REQUEST_OBJECT_TIMEOUT` | `3` | Seconds one read of a `request_uri` a client hosts is given, 0.1 at least |
| `BEFFROI_REQUEST_OBJECT_MAX_SIZE` | `65536` | Bytes such a request object may answer before the read stops, one at least |
| `BEFFROI_DPOP_NONCE_REQUIRED` | `false` | Whether a DPoP proof carries a nonce this provider issued (RFC 9449 §8), `true` or `false` |
| `BEFFROI_DPOP_PROOF_MAX_AGE` | `60` | How long a DPoP proof stands from its `iat` (RFC 9449 §4.3), one second at least |
| `BEFFROI_DPOP_LEEWAY` | `30` | Seconds allowed for the clock of the client that signed a proof, both ways, `0` or more |
| `BEFFROI_DPOP_NONCE_TTL` | `300` | How long a nonce this provider issues is accepted, one second at least |
| `BEFFROI_INTERACTION_LOGIN_HINT` | `sub` | What a `login_hint` names on the login page (OIDC Core §3.1.2.1): `sub`, the subject this provider issued to that client; `username`, the name a person signs in with; or `none`, nothing |
| `BEFFROI_BACKCHANNEL_AUTHENTICATION_LOGIN_HINT` | `sub` | What a `login_hint` names in a backchannel request (CIBA Core §7.1), with the same three values |
| `BEFFROI_TRUSTED_ISSUERS` | `{}` | A JSON object, the issuers whose assertions the tenant accepts as an authorization grant (RFC 7523 §2.1), keyed by their `iss`: [the shape](../reference/configuration.md#trusted_issuers). `{}`, none, and the grant serves nobody |

## What leaves the provider

| Variable | In the image | What it decides |
|---|---|---|
| `BEFFROI_BACK_CHANNEL_LOGOUT_TIMEOUT` | `5` | Seconds one send of a logout token is given (Back-Channel Logout 1.0 §2.5), 0.1 at least |
| `BEFFROI_BACK_CHANNEL_LOGOUT_RETRIES` | `6` | How many times a send that did not reach its client comes back, `0` or more |
| `BEFFROI_BACK_CHANNEL_LOGOUT_RETRY_DELAY` | `2` | Seconds before the first return, one at least |
| `BEFFROI_BACK_CHANNEL_LOGOUT_RETRY_MULTIPLIER` | `3` | What each wait is multiplied by to give the next, one at least |
| `BEFFROI_BACK_CHANNEL_LOGOUT_RETRY_MAX_DELAY` | `60` | The longest wait in seconds, one at least |
| `BEFFROI_CLIENT_NOTIFICATION_TIMEOUT` | `3` | Seconds one call to the notification endpoint of a client in `ping` mode is given, when its backchannel request is answered (CIBA Core §10.2), 0.1 at least |
| `BEFFROI_WEB_PUSH_SUBJECT` | `mailto:operator@op.localhost` | The contact a push service is given in the token this provider signs for it (RFC 8292 §2.1), a `mailto:` or `https:` URI at which the operator can be reached. Naming one turns web push on; empty turns it off, the tenant then hands out no key and reaches nobody by push. The image names the one of the development stack |
| `BEFFROI_WEB_PUSH_TIMEOUT` | `3` | Seconds one push is given, 0.1 at least |
| `BEFFROI_BREACHED_PASSWORDS_ENDPOINT` | empty | The range endpoint a password is compared against before it is written (NIST SP 800-63B-4 §3.1.1.2): `https://api.pwnedpasswords.com/range/`, where the first five hexadecimal characters of the SHA-1 of a password leave and the rest is compared here. Empty, nobody is asked, and passwords are posed on the rules of the core alone |
| `BEFFROI_BREACHED_PASSWORDS_TIMEOUT` | `2` | Seconds one lookup is given, 0.1 at least. A lookup still unanswered by then refuses the password |
| `GEOIP_LICENSE_KEY` | empty | The licence key of the MaxMind account the GeoLite2 databases are downloaded under. Empty, nothing is downloaded, and every session and every act says an address and no place |

The four figures of the returns are also the schedule of the lane `async_notifications`, which carries the
notifications of the backchannel flow and the pushes as well, and with the timeout of one send they bound how
long a logout token stays on its way: [Messenger](../symfony-bundle/messenger.md).

## Retention and load

| Variable | In the image | What it decides |
|---|---|---|
| `BEFFROI_JOURNAL_RETENTION` | `180` | Days an act of the journal is kept, one at least |
| `BEFFROI_HISTORY_RETENTION` | `180` | Days a change of a claim is kept, one at least |
| `BEFFROI_LOAD_ORIGIN_LIMIT` | `2400` | The requests one client address may send in the window below before a `429`, one at least |
| `BEFFROI_LOAD_ORIGIN_INTERVAL` | `60` | That window, in seconds, one at least |
| `BEFFROI_LOAD_CLIENT_LIMIT` | `1200` | The requests one authenticated client may send in the window below before a `429`, one at least |
| `BEFFROI_LOAD_CLIENT_INTERVAL` | `60` | That window, in seconds, one at least |

## SAML

| Variable | In the image | What it decides |
|---|---|---|
| `BEFFROI_SAML_IDENTITY_PROVIDER` | `true` | Whether the tenant is a [SAML identity provider](../saml/identity-provider.md), serving its metadata at `/saml/metadata`, `true` or `false` |
| `BEFFROI_SAML_SERVICE_PROVIDER` | `false` | Whether the tenant is a SAML service provider to [upstream identity providers](../saml/upstream-identity-providers.md). With both roles off, the tenant draws no SAML key |
| `BEFFROI_SAML_SERVICE_PROVIDER_ENTITY_ID` | empty | The entity ID of that service provider, an absolute URI and never the one of the identity provider. Empty, the URL of its metadata, `/saml/sp/metadata` of the issuer |
| `BEFFROI_SAML_KEY_STAGING_DELAY` | `604800` | Seconds a new SAML key is published in the metadata before it is used, `0` or more: seven days |
| `BEFFROI_SAML_KEY_AGE` | `31536000` | Seconds a SAML key works before the timed step stages a successor behind it, one at least: a year |
| `BEFFROI_SAML_METADATA_CACHE_DURATION` | `86400` | The `cacheDuration` of the metadata of both roles (SAML Metadata §2.3.2), one second at least and strictly shorter than the staging delay: a day |
| `BEFFROI_SAML_WANT_AUTHN_REQUESTS_SIGNED` | `true` | What the metadata say in `WantAuthnRequestsSigned` (SAML Metadata §2.4.3). It announces and decides nothing: whether a request needs a signature is decided per service provider |
| `BEFFROI_SAML_SERVICE_PROVIDERS` | `{}` | A JSON object, the service providers the identity provider serves, keyed by entity ID: [the shape](../reference/configuration.md#samlservice_providers). Refused while the identity provider is off |
| `BEFFROI_SAML_IDENTITY_PROVIDERS` | `{}` | A JSON object, the upstream identity providers the service provider receives assertions of, keyed by entity ID: [the shape](../reference/configuration.md#samlidentity_providers). Refused while the service provider is off |

## The web server

These are read by Caddy and FrankenPHP, not by the kernel.

| Variable | In the image | What it decides |
|---|---|---|
| `SERVER_NAME` | not set | The host Caddy serves the provider on, `localhost` when it is not set. When Caddy terminates TLS, it obtains the certificate of that host itself, from a public authority for a public name and from its internal authority for `localhost`, and keeps it under `/data`; a plain HTTP address is refused then. When a proxy does, one host, the one the proxy asks for, or `:<port>` for any host, written without a scheme |
| `TLS_TERMINATION` | not set | Who terminates TLS for the site of `SERVER_NAME`: `caddy` when it is not set, with the TLS of the image, or `proxy`, a proxy in front of the image, the site then being `http://` followed by `SERVER_NAME`, on port 80 unless `SERVER_NAME` names another. Caddy refuses to start on a misspelt value, `Proxy` or an empty one. The host of `MTLS_SERVER_NAME` terminates its TLS in Caddy whatever this says: [behind a proxy](deployment.md#behind-a-proxy) |
| `MTLS_SERVER_NAME` | not set | The host of the listener that asks for a client certificate, in `mtls.Caddyfile` |
| `CADDY_EXTRA_CONFIG` | not set | Configuration added to the `Caddyfile` beside the site of `SERVER_NAME`. `import mtls.Caddyfile` is what serves the host that asks for a client certificate |
| `CADDY_GLOBAL_OPTIONS` | not set | Directives added to the global options of the `Caddyfile` |
| `CADDY_SERVER_EXTRA_DIRECTIVES` | not set | Directives added to the site of `SERVER_NAME`, such as a `tls` directive naming a certificate and its key |
| `CADDY_SERVER_LOG_OPTIONS` | not set | Directives added to the `log` block of each site |
| `FRANKENPHP_CONFIG` | `import worker.Caddyfile` | Directives of the `frankenphp` block. The image sets worker mode |
| `FRANKENPHP_WORKER_CONFIG` | not set | Directives added to the `worker` block: the `watch` lines of the development stack, nothing in production |

## The key management service

The DSN and the key identifier are what change from one backend to the next: the code and the envelope are
the same. An envelope sealed by one backend does not open with another.

=== "A file"

    A sodium key read from a file of its own, one per tenant, outside the web root and outside the sealed
    keys: it holds against a dump of the storage, not against a compromise of the host. It is the backend of
    a deployment that has no key management service.

    ``` bash
    BEFFROI_KMS_DSN="sodium+dir:///run/secrets?ext=.key"
    BEFFROI_KMS_KEY_ID="beffroi-{tenant}"
    ```

    The file of the tenant `default` is then `/run/secrets/beffroi-default.key`: thirty-two random bytes and
    nothing else, which the orchestrator mounts there as a secret, as [one host](examples.md#one-host) does.

    ``` bash
    head -c 32 /dev/urandom > beffroi-default.key
    ```

=== "Sodium"

    The key inline in the environment, which is what the development stack provisions.

    ``` bash
    BEFFROI_KMS_DSN="sodium://?keys[signing]=<32 bytes, base64url>"
    BEFFROI_KMS_KEY_ID="signing"
    ```

    Whoever reads the environment of the process holds the master key.

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

## What no variable sets

- **The clients.** A client registers itself, and the image declares none.
- **The exemption of confidential clients from PKCE.** The image registers every client with PKCE required:
  the exemption is a field of the policy of a tenant, and not a setting of a deployment.
- **The name of the key management client and the directories of the image.** The keys are sealed with the
  client `op`, and the sealed keys, the GeoLite2 databases and the FIDO metadata live in `/app/var/keys`,
  `/app/var/geoip` and `/app/var/webauthn`, where a deployment mounts its volumes.
- **The share directory**, `/app/var/share/prod`, where the filesystem pool of `cache.app` keeps
  [the caches of the bundle](deployment.md#what-the-processes-share). `APP_SHARE_DIR` is compiled into the
  container when the image is built, and set when a container starts, it moves nothing.

## What only development reads

The image compiles the whole `.env`, and the variables of the development stack and of its tests with it:
`CONFORMANCE_BASIC_SECRET`, `CONFORMANCE_BASIC_SECOND_SECRET`, `CONFORMANCE_POST_SECRET`,
`CONFORMANCE_ACCESS_TOKEN_FORMAT`, `OIDC_DEMO_SECRET`, `OIDC_DEMO_OPAQUE_SECRET`, `OIDC_DEMO_SECOND_SECRET`,
`BEFFROI_DEMO_HOST_IP` and `APP_PROFILER`. Only the configuration of the development environment reads them,
with the other secrets and key sets the development stack writes into `.env.local`, so a production kernel
reads none of them, and a deployment sets none of them.
