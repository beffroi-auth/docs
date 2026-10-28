---
title: Deployment
description: The image, the HTTP server in worker mode, the worker, the two planes, what the processes share, TLS and the host that asks for a client certificate.
---

# Deployment

One image runs two kinds of process: the HTTP server, FrankenPHP in worker mode inside the Caddy server it is
built on, and the worker, which consumes the lanes of Messenger and the schedule of the timed steps. Beside them
the provider needs PostgreSQL and a key management service, and no broker.

## The image

`apps/op/Dockerfile` builds on `dunglas/frankenphp:1-php8.5` and adds the extensions the provider needs:
`apcu`, `intl`, `opcache`, `zip`, `pdo_pgsql`, `gmp`, `sodium` and `uuid`. Its build context is the
root of the monorepo, because the application installs the packages beside it through path repositories.

| Stage | What it is |
|---|---|
| `frankenphp_base` | The extensions, the PHP settings of the application, the entrypoint and the Caddy configuration |
| `frankenphp_dev` | The development image, into which the stack mounts the monorepo, running FrankenPHP with `--watch` |
| `frankenphp_prod` | The production image: the packages are copied to `/src` and the application to `/app`, installed without the development dependencies, with an authoritative class map, the `.env` of the repository compiled for production, the stylesheet built and the assets compiled |

``` bash
docker build --file apps/op/Dockerfile --target frankenphp_prod .
```

`apps/op/` is copied without what a working copy holds beside the repository: `Dockerfile.dockerignore` leaves
out its `.env.local`, where the development stack writes its key management service, the secrets of its
clients and the password of its user, and its `var/` and `vendor/`. The image compiles the environment the
repository holds, and a deployment sets its own: [configuration](configuration.md).

The production image sets `APP_ENV=prod`, reads `php.ini-production`, preloads `config/preload.php` into
OPcache, and turns worker mode on: the kernel is booted once per worker and serves every request that worker
takes, so a signing key opened with the key management service stays open in it, and the service is asked once
per key and per worker rather than once per signature.

## The HTTP server

The command of the image is `frankenphp run --config /etc/frankenphp/Caddyfile`. Before it starts, the
entrypoint does two things when `.env` names a `DATABASE_URL`, which the one of the application does:

1. it waits for the database, sixty attempts one second apart, and stops at once on an error it cannot
   recover from;
2. it plays the migrations, `doctrine:migrations:migrate --no-interaction --all-or-nothing`, every time the
   server starts. The migrations of the bundle are written for PostgreSQL and refuse any other platform.

The health check of the image asks the metrics endpoint of the Caddy admin API inside the container,
`curl -f http://localhost:2019/metrics`, after a start period of sixty seconds. Only the server runs Caddy, so
a container that runs the worker turns that check off or replaces it.

### The two planes

Every route of the bundle carries its plane in its name, `beffroi_protocol_*` for what a client or a resource
server calls and `beffroi_interaction_*` for what a browser reads. `BEFFROI_PLANE` restricts a process to one
of them:

| `BEFFROI_PLANE` | What the process serves |
|---|---|
| `all` | Both planes, which is what `.env` says |
| `protocol` | The protocol plane; every route of the interaction plane answers `404` |
| `interaction` | The interaction plane; every route of the protocol plane answers `404` |

The refusal comes after the router and before the firewall, so a request to the other plane opens no session
and counts against no budget. The root `/` of the application belongs to the interaction plane, and a route
whose name carries no plane, such as `/theme`, is served by every process. A process serves its plane on each
of its hosts, the one that asks for a client certificate included. Whatever sends a request to one process or
the other reads its path, and [the endpoints](../reference/endpoints.md) give the plane of every path.

## The worker

The worker is the same image, running the consumer of Messenger on the schedule and the four lanes of the
provider, in this order, which is the order it takes them in:

``` bash
bin/console messenger:consume scheduler_beffroi async_notifications async_priority_high async_priority_medium async_priority_low --time-limit=3600 --memory-limit=256M
```

Started with `bin/console`, the entrypoint waits for the database as it does for the server, and plays no
migration: the server is the process that migrates, and the development stack starts the worker once the server
reports healthy. The consumer stops after an hour, or once it holds 256 MB, and the restart policy of the stack
starts it again.

| Transport | What it carries |
|---|---|
| `scheduler_beffroi` | The clock of the timed steps. One process consumes it: the steps are idempotent, and are not written to run twice at once |
| `async_notifications` | What the provider carries to somebody it does not own: logout tokens (Back-Channel Logout 1.0 §2.5), the notification that a backchannel request was answered (CIBA Core §10.2), and web push to the browsers of a person (RFC 8030) |
| `async_priority_high` | Nothing the bundle routes |
| `async_priority_medium` | The writes a request does not wait for, and the timed steps the schedule hands over |
| `async_priority_low` | The events of the core and of the protocol, which the journal writes down and the enrichment of a provenance reads |

The worker is therefore the one process that calls a client back, and the one that writes the
[journal](observability.md). A provider whose worker stops goes on answering requests, and the lanes keep the
messages until a worker consumes them.

The lanes are four queues of the table `messenger_messages` of the database, one per lane, which the transport
creates the first time it reaches it. The application requires the transport of no broker, and the image
carries the PHP extension of none. What fails for good lands in the failure transport, `failed`, a queue of the
same table.

## What the processes share

The server signs with keys the worker rotates, and the worker enriches with databases the console downloads,
so some state has to be the same for all of them.

| What | Where | Written by | Read by |
|---|---|---|---|
| The sealed keys of the tenant, and its pairwise salt | `var/keys` | `beffroi:keys:*`, the timed step of the key lifecycle, and the first process that needs the salt | Every process that signs, decrypts or seals |
| The key of the file backend, when that is the key management service | The directory its DSN names: `/run/secrets` for a secret the orchestrator mounts, `var/kms` on the development stack | Whoever provisions it | Every process |
| The GeoLite2 databases of addresses | `var/geoip` | `beffroi:geoip:refresh`, the weekly step | The worker, which enriches a provenance |
| The FIDO metadata | `var/webauthn` | `beffroi:webauthn:mds-refresh`, `beffroi:webauthn:mds-import` | The passkey ceremonies, which check an attestation against it |

The development stack gives `var/keys`, `var/kms` and `var/geoip` a volume each, and the Compose file of the
image, [`compose.prod.yaml`](../getting-started/the-standalone-application.md#the-compose-file-of-the-image),
adds `var/webauthn` and `var/share` to them, mounted on the server and on the worker alike: a rotation done by
one process changes nothing for another that does not see the same directory.

The bundle keeps eight caches in pools of their own, so that a deployment can point them at a shared store
without touching the rest of its cache:

| Pool | What it holds |
|---|---|
| `beffroi.client_keys` | The keys read from the `jwks_uri` of a client |
| `beffroi.issuer_keys` | The keys read from the `jwks_uri` of a trusted issuer |
| `beffroi.client_assertions` | The client assertions already seen |
| `beffroi.issuer_assertions` | The assertions of trusted issuers already seen |
| `beffroi.software_statements` | The software statements already seen |
| `beffroi.request_objects` | The request objects already seen |
| `beffroi.dpop` | What DPoP remembers of a proof |
| `beffroi.load` | What each load budget has been asked |

Each of them is on `cache.app`, which the application leaves on the filesystem adapter Symfony gives it, in
`%kernel.share_dir%/pools/app`. The share directory carries the environment, so with the `APP_SHARE_DIR` of
`.env` the pools of a production kernel are in `var/share/prod/pools/app`. Two containers share these pools
when they share that directory, or once a deployment points the pools at a store they both reach, and each
holds its own otherwise. The application names no session handler either, so the session of a browser lives
where the native handler of PHP keeps it, in the container that served it.

## TLS and the two hosts

Caddy terminates TLS for the host of `SERVER_NAME`. Both hosts of the image use one snippet of its
`Caddyfile`, which is the TLS a FAPI 1.0 plan measures: an RSA key of 2048 bits, and below TLS 1.3 the two
suites of FAPI 1.0 Advanced Final §8.5 a listener built on Go can offer,
`TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256` and `TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384`. TLS 1.2 is the floor
Caddy already holds.

**The host that asks for a client certificate is a host of its own** (RFC 8705 §5). It is served when
`CADDY_EXTRA_CONFIG` imports `mtls.Caddyfile`, under the name `MTLS_SERVER_NAME` gives it, and announced to
clients through `BEFFROI_MTLS_ORIGIN`. Its listener asks for a certificate and serves the connection when none
is presented, so a client that authenticates another way never fails at the handshake. The ordinary host asks
for nothing.

- **The certificate reaches PHP in a server variable, `SSL_CLIENT_CERT`, and never in a header.** A client
  sets every header of its request and no variable of the process that serves it. A request carrying a
  certificate in `Ssl-Client-Cert`, `X-Ssl-Client-Cert`, `X-Client-Cert` or `X-Forwarded-Client-Cert` is
  refused with `invalid_request` (RFC 6749 §5.2) at an endpoint that reads a certificate. The TLS connection
  of that host therefore ends at this listener.
- **Only the leaf reaches PHP**, so no chain is validated there. The handshake proves that the client holds
  the private key of what it presented (RFC 8446 §4.4.3), which is what `self_signed_tls_client_auth`
  (RFC 8705 §2.2) needs. A deployment that authenticates clients with `tls_client_auth` (RFC 8705 §2.1) adds a
  `trust_pool` to the `client_auth` block of `mtls.Caddyfile`, so the chain is validated at the edge.

[:beffroi-arrow-right: The variables of the web server](configuration.md#the-web-server)

## Behind a proxy

The address of a request is read by Symfony behind the proxies it trusts, and the application names none:
`framework.trusted_proxies` reads `SYMFONY_TRUSTED_PROXIES`. That address is what the load budget of an origin
is counted under, 2400 requests a minute by default before a `429`, and what every session and every act of
the journal records as where it came from. Behind a proxy that is not named there, every request has the
address of the proxy.

[:beffroi-arrow-right: Behind a proxy that terminates TLS](examples.md#behind-a-proxy-that-terminates-tls)

## The headers

**Two layers write the security headers, and where they meet, one gives way.** The bundle gives every page of
the interaction plane `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` and
the floor of a content policy, `frame-ancestors 'none'`. The application writes the headers of a deployment on
every answer, from two files of its configuration, `config/packages/nelmio_security.yaml` and
`config/packages/nelmio_cors.yaml`:

- `X-Frame-Options` is left as a page already carries it, and `Referrer-Policy` is written again with the
  value the pages carry, `no-referrer`;
- on a page whose content policy is the floor alone, `App\Http\DeploymentPolicyPrevails` drops the floor
  before the policy of the deployment is written, so one policy is sent. A page that computed a whole policy
  of its own keeps it, the form post response and the front-channel logout page, and so does a redirection.

A header written twice is not replaced, it collides: two content policies are both enforced, and what applies
is their intersection. Nothing the application writes is therefore written again in the web server or at the
edge. The assets compiled into `public/assets/` are answered by FrankenPHP without asking PHP, and carry none
of these headers.

The session cookie is the one header of the provider no bundle sets, so the application names it:
`__Host-beffroi_session`, `Secure`, `HttpOnly`, `SameSite=Lax`, on the path `/` and with no `Domain`. HSTS is
not sent in the development environment, where it would pin every `.localhost` name of the machine to HTTPS.

[:beffroi-arrow-right: The headers](../the-project/secure-by-default.md#what-a-deployment-answers-with)

## What leaves the provider

A deployment that filters what goes out reads it here. No outbound redirect is followed, whoever asks.

| From | To | When |
|---|---|---|
| Every process | The key management service | To open a key, a salt or a data key, and to seal one |
| The server | The `jwks_uri` of a client or of a trusted issuer | To read its keys, which are then kept a day, and again when an assertion names a key the kept set does not hold |
| The server | The `request_uri` of a client | When an authorization request names one |
| The server | The `sector_identifier_uri` of a client | When a client registers or replaces itself |
| The server, the console | The list of compromised passwords, when one is named | When a password is written, and the answer is waited for |
| The worker | The list of compromised passwords, when one is named | After a login, for a password already posed |
| The worker | The `backchannel_logout_uri` of a client | When a session that client signed in ends |
| The worker | The `backchannel_client_notification_endpoint` of a client | When a backchannel request in `ping` mode is answered |
| The worker | The push service of a browser | When a backchannel request waits on the person who subscribed that browser |
| The worker, the console | The metadata of the SAML peers given by URL | Every hour, and on `beffroi:saml:*:refresh` |
| The worker, the console | MaxMind, when a licence key is named | Every week, and on `beffroi:geoip:refresh` |
| The console | The FIDO Metadata Service | On `beffroi:webauthn:mds-refresh` |
