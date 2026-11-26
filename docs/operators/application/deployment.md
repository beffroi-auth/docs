---
title: Deployment
description: The image, the HTTP server in worker mode and its health check, the worker, the planes, what the processes share, TLS and the host that asks for a client certificate.
---

# Deployment

One image runs two kinds of process: the HTTP server, FrankenPHP in worker mode inside the Caddy server it is
built on, and the worker, which consumes the lanes of Messenger and the schedule of the timed steps. Beside them the provider
needs PostgreSQL, which holds the lanes of Messenger as well as the model, and a key management service.

## The image

`apps/beffroi/Dockerfile` builds on `dunglas/frankenphp:1.14.0-php8.5-trixie` and adds the extensions the
provider needs, `apcu`, `intl`, `opcache`, `zip`, `pdo_pgsql`, `gmp`, `sodium` and `uuid`, and the program
`gpg`, which encrypts the mail written to a person who gave an OpenPGP key. Its build context is the root of
the monorepo, because the application installs the packages beside it through path repositories.

| Stage | What it is |
|---|---|
| `frankenphp_base` | The extensions, `gpg`, the PHP settings of the application, the entrypoint and the Caddy configuration |
| `frankenphp_dev` | The development image, into which the stack mounts the monorepo, running FrankenPHP with `--watch` |
| `frankenphp_prod_builder` | Where the production image is built: the packages are copied to `/src` and the application to `/app`, installed without the development dependencies, with an authoritative class map, the `.env` of the repository compiled for production, the stylesheet built and the assets compiled |
| `frankenphp_prod` | The production image, on `debian:13.8-slim`: FrankenPHP, PHP, the extensions and the libraries they load, `gpg`, the packages and the application, and no compiler, Composer or Node. Every process runs as `www-data`, uid 33 |

Each base image is named by its version and pinned by the digest of that tag, so a build of a commit takes the
PHP, FrankenPHP and Debian that commit names, and a rebuild of the same tag upstream reaches the image as a
change of the digest in the repository.

``` bash
docker build --file apps/beffroi/Dockerfile --target frankenphp_prod .
```

`apps/beffroi/` is copied without what a working copy holds beside the repository: `Dockerfile.dockerignore` leaves
out its `.env.local`, where `castor provision` writes the values of the development stack
([on your machine](../getting-started/the-standalone-application.md#on-your-machine)), and its `var/` and
`vendor/`. The image compiles the environment the
repository holds, and a deployment sets its own: [configuration](configuration.md).

The production image sets `APP_ENV=prod`, reads `php.ini-production`, preloads `config/preload.php` into
OPcache, and turns worker mode on: the kernel is booted once per worker and serves every request that worker
takes, so a signing key opened with the key management service stays open in it, and the service is asked once
per key and per worker rather than once per signature. By default, the provider runs four such threads and the
administration API two, whatever the cores of the host, each holding its own connection to PostgreSQL for as
long as it lives: a server that serves the administration API and the worker that consumes the lanes hold seven
connections at rest ([`FRANKENPHP_WORKER_NUM`](configuration.md#the-web-server)).

**A secret may be a file.** Each of the ten variables that carry a secret, `APP_SECRET`, `DATABASE_URL` and
`BEFFROI_KMS_DSN` among them, may be given as a file instead, which `docker inspect` does not show: its `_FILE`
twin names the file, such as one a secret of Compose or Swarm mounts ([a secret in a
file](configuration.md#a-secret-in-a-file)). `gpg`, the one
program the provider starts, starts with none of the environment of the provider: the `gpg` the processes find,
`/usr/local/bin/gpg`, hands Debian's its `PATH` and its `GNUPGHOME` and nothing else.

## The HTTP server

The command of the image is `frankenphp run --config /etc/frankenphp/Caddyfile`. Before it starts, the
entrypoint checks the sizes that bound a request, below, then does three things when `.env` names a
`DATABASE_URL`, which the one of the application does:

1. it waits for the database, sixty attempts one second apart, and stops at once on an error it cannot
   recover from;
2. it plays the migrations, `doctrine:migrations:migrate --no-interaction --all-or-nothing`, every time the
   server starts, as the role `BEFFROI_MIGRATIONS_DATABASE_URL` names, or as the role of `DATABASE_URL` when
   that variable is not set. The migrations of the application, in `migrations/`, are written for PostgreSQL
   and refuse any other platform. When the role of `DATABASE_URL` is another, it then grants that role what
   the processes serve, `beffroi:database:grant`: [the role the processes connect as](persistence.md#the-role-the-processes-connect-as);
3. it writes the row of the tenant its environment describes, `beffroi:tenant:synchronize`, which changes
   only what changed. A configuration the tenant refuses, or that moved its issuer, stops the container
   before it serves, at every start.

The production image runs Caddy without its own administration API, which answers whoever reaches its address
with no credential and can stop or reconfigure the server. A deployment that wants it, for the metrics Caddy
serves there, names its address in `CADDY_ADMIN`.

Caddy bounds the size of a request before it reaches the provider. On the listeners of its sites, a request
whose request line and headers go over the bound, as the Go server Caddy is built on counts them, is answered
`431` (RFC 6585 §5). On each site, a body over the bound of that site is answered `413` (RFC 9110 §15.5.14),
whether its length is announced or it is chunked. The defaults let through the largest SAML message the
provider reads from a posted form, and the largest S/MIME key with its certificates the administration API
takes: [the variables of the web server](configuration.md#the-web-server).

Caddy keeps a size as a whole number of bytes, and starts on one that bounds nothing: zero bytes in any unit,
such as `0`, `0KiB` or `0.4B`, or 8 EiB and more, which wraps below zero. A body is then read whatever its
size, and the headers are held to the bound Caddy applies when it is given none. The entrypoint therefore has
Caddy read each of `CADDY_MAX_HEADER_SIZE`, `CADDY_REQUEST_BODY_MAX_SIZE` and
`CADDY_ADMINISTRATION_REQUEST_BODY_MAX_SIZE` the environment sets, and stops the container on such a size,
with one line on its error output:

``` text
CADDY_REQUEST_BODY_MAX_SIZE=0 is not a bound: give it a size of 1B or more, below 8EiB.
```

A value Caddy cannot read as a size, an empty one, `-1`, or 16 EiB and more, is left to Caddy, which refuses
it as it starts.

### The health check

The `HEALTHCHECK` of the production image runs `/usr/local/bin/docker-healthcheck`, a PHP script, with a start
period of sixty seconds. It asks the site of `SERVER_NAME` for a document the provider serves, over the
loopback address, `127.0.0.1`, under the host of the issuer: the discovery document, or `/copy.js` in a
process whose `BEFFROI_PLANE` is `interaction`, which answers `404` on the discovery path.

| `TLS_TERMINATION` | The request of the check |
|---|---|
| `caddy` | `https` on port 443, the host of the issuer in its `Host` header and its SNI. The certificate Caddy presents is not verified, the request never leaving the container |
| `proxy` | `http` on port 80, the host of the issuer in its `Host` header, with `X-Forwarded-Proto: https`, as the proxy sends it |

A port that the first address of `SERVER_NAME` names replaces 443 or 80. Caddy answers an empty `200` to a host
none of its sites names, so the check passes on a `200` with a body alone, and fails when the site of
`SERVER_NAME` does not serve the host of the issuer. It follows no redirect and gives up after ten seconds
without an answer. When it fails, it writes the URL, the host and what was answered, the status and any
`Location`, or why nothing was, on its error output, which `docker inspect` shows in the health of the
container. It reads `BEFFROI_ISSUER`, `SERVER_NAME`, `TLS_TERMINATION` and `BEFFROI_PLANE` as Symfony does,
from the environment first, then from the `.env` the image compiled.

Both documents read the row of the tenant, so the check fails while the server cannot reach the database, and
while the kernel refuses its configuration, which fails every request. Behind a proxy, it passes only when
Symfony reads its `X-Forwarded-Proto` from the loopback address: [behind a proxy](#behind-a-proxy).

Only the server runs Caddy, so a container that runs the worker turns that check off or replaces it. The
Compose file of the image gives its worker a check of its own, that the consumer is the first process of its
container.

### The planes

Every route of the provider, the ones `config/beffroi/routes.php` imports, carries its plane in its name,
`beffroi_protocol_*` for what a client or a resource server calls and `beffroi_interaction_*` for what a browser
reads. The administration API of the tenant is a third plane, `beffroi_administration_*`. `BEFFROI_PLANE`
restricts a process to its planes:

| `BEFFROI_PLANE` | What the process serves |
|---|---|
| `provider` | The protocol and interaction planes, never the administration API, which is what `.env` says |
| `protocol` | The protocol plane; every route of the interaction plane answers `404` |
| `interaction` | The interaction plane; every route of the protocol plane answers `404` |
| `administration` | The administration API alone, the value the worker of `/etc/frankenphp/administration.Caddyfile` sets |

In a process of the protocol or of the interaction plane, the refusal comes after the router and before the
firewall, so a request to the other plane opens no session and counts against no budget. The root `/` of the application and the choice of a theme, `/theme`, belong to
the interaction plane, as every route the image serves belongs to a plane. A process serves its plane on each
of its hosts, the one that asks for a client certificate included. Whatever sends a request to the process
of the protocol or to that of the interaction reads its path, and [the endpoints](../../developers/reference/endpoints.md) give
the plane of every path. The administration API is reached by its own host, the site of
`/etc/frankenphp/administration.Caddyfile`, [below](#the-host-of-the-administration-api), whose worker serves
that plane whatever `BEFFROI_PLANE` the container sets.

## The worker

The worker is the same image, running the consumer of Messenger on the schedule and the four lanes of the
provider, in this order, which is the order it takes them in:

``` bash
bin/console messenger:consume scheduler_beffroi async_notifications async_priority_high async_priority_medium async_priority_low --time-limit=3600 --memory-limit=256M
```

Started with `bin/console`, the entrypoint waits for the database as it does for the server, and checks no
size, plays no migration and writes no tenant: the server does all three, and the development stack starts
the worker once the server reports healthy. The consumer stops after an hour, or once it holds 256 MB, and the restart policy of the stack
starts it again.

| Transport | What it carries |
|---|---|
| `scheduler_beffroi` | The clock of the timed steps. One process consumes it: the steps are idempotent, and are not written to run twice at once |
| `async_notifications` | What the provider carries to somebody it does not own: logout tokens (Back-Channel Logout 1.0 §2.5), the notification that a backchannel request was answered (CIBA Core §10.2), web push to the browsers of a person (RFC 8030), and a mail or a text to the address or the number of a person, when it is marked verified |
| `async_priority_high` | Nothing the application routes |
| `async_priority_medium` | The writes a request does not wait for, and the timed steps the schedule hands over |
| `async_priority_low` | The events of the core and of the protocol, which the journal writes down and the enrichment of a provenance reads |

The worker is therefore the one process that calls a client back, and the one that writes the
[journal](observability.md). A provider whose worker stops goes on answering requests, and the lanes keep the
messages until a worker consumes them.

The lanes are four queues of the table `messenger_messages` of the database, one per lane, which a migration
creates as the owner of the tables, no transport creating it. The application requires the transport of no broker, and the image
carries the PHP extension of none. What fails for good lands in the failure transport, `failed`, a queue of the
same table.

## What the processes share

The server signs with keys the worker rotates, and the worker enriches with databases the console downloads,
so some state has to be the same for all of them.

| What | Where | Written by | Read by |
|---|---|---|---|
| The sealed keys of the tenant, its pairwise salt, and the last signed head of each of its [chains](observability.md#the-chains), in `<slug>/chains/` | `var/keys` | `beffroi:keys:*`, the timed step of the key lifecycle, the first process that needs the salt, and what signs a chain: its timed step, the daily steps of retention and `beffroi:chain:sign-anew` | Every process that signs, decrypts or seals, or checks a chain |
| The key of the file backend, when that is the key management service | The directory its DSN names, `var/kms` on the development stack and in the Compose file of the image | Whoever provisions it | Every process |
| The GeoLite2 databases of addresses | `var/geoip` | `beffroi:geoip:refresh`, the weekly step | The worker, which enriches a provenance |
| The FIDO metadata, and the list of passkey providers of the community in its directory `community/` | `var/webauthn` | `beffroi:webauthn:mds-refresh`, `beffroi:webauthn:mds-import`, and `beffroi:webauthn:aaguids-refresh` for the list | The page of the passkeys and `beffroi:user:show`, which name the authenticator of a passkey from both, and the enrolment of a passkey under the `direct` or `enterprise` policy of the tenant, which reads them for the model and its status reports |

The development stack gives `var/keys`, `var/kms` and `var/geoip` a volume each, and the Compose file of the
image, [`compose.prod.yaml`](../getting-started/the-standalone-application.md#the-compose-file-of-the-image),
adds `var/webauthn` and `var/share` to them, mounted on the server and on the worker alike: a rotation done by
one process changes nothing for another that does not see the same directory.

The application keeps eight caches in pools of their own:

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
when they share that directory, which the volume of `var/share` of the Compose file of the image does, and
each holds its own otherwise: no variable points the pools at another store. The counts of the
[limits on guesses and of the budgets of a person or an administrator](security.md#attempts-and-budgets) are
kept by Symfony in `cache.rate_limiter`, a pool on `cache.app` as well: they are shared as these pools are.

**The locks are in the database.** The counts of those limits and budgets, and the identifiers the guards
against replay remember in the pools of the assertions, the software statements, the request objects and DPoP,
are read and written under a lock every process of the deployment shares, an advisory lock of PostgreSQL on
the connection of Doctrine (`config/packages/lock.yaml`). Requests at once, on one server or on several, are
counted one after the other, and an identifier presented twice at once is taken once. The load budgets take no
lock.

**The session of a browser is in the database**, in `beffroi_session`, which every process reaches. A session
opens on the connection Doctrine holds at that moment, under an advisory lock of PostgreSQL, each row under the
SHA-256 of the identifier its cookie carries and its data sealed under a data key of the tenant, as personal
data is, bound to that hash: a row moved under another identifier opens as no session. A browser is therefore
tied to no server: servers behind one proxy that share the database, the volumes above and the key management
service each read the sessions the others wrote, and a redeployment that replaces them one at a time signs
nobody out.

## TLS and the hosts

Caddy terminates TLS for the host of `SERVER_NAME`, unless a proxy in front of the image does
([below](#behind-a-proxy)), and for the host that asks for a client certificate in every deployment. On these
two hosts, when it terminates their TLS, it serves one snippet of its `Caddyfile`, which is the TLS a FAPI 1.0
plan measures: an RSA key of 2048 bits, and below TLS 1.3 the two suites of FAPI 1.0 Advanced Final
§8.5 a listener built on Go can offer, `TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256` and
`TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384`. TLS 1.2 is the floor Caddy already holds.

**The host that asks for a client certificate is a host of its own** (RFC 8705 §5). It is served when
`CADDY_EXTRA_CONFIG` imports `mtls.Caddyfile`, under the name `MTLS_SERVER_NAME` gives it, and named to the
application in `BEFFROI_MTLS_ORIGIN`, which announces it to clients and wires the two methods that read a
certificate and the binding of a token to one. Its listener asks for a certificate and serves the connection
when none is presented, so a client that authenticates another way never fails at the handshake. The ordinary
host asks for nothing.

- **The certificate reaches PHP in a server variable, `SSL_CLIENT_CERT`, and never in a header.** A client
  sets every header of its request and no variable of the process that serves it. A request carrying a
  certificate in `Ssl-Client-Cert`, `X-Ssl-Client-Cert`, `X-Client-Cert` or `X-Forwarded-Client-Cert` is
  refused with `invalid_request` (RFC 6749 §5.2) at an endpoint that reads a certificate. The TLS connection
  of that host therefore ends at this listener.
- **The listener judges no certificate, and only the leaf reaches PHP.** Its `client_auth` asks for a
  certificate in `mode request`, under which Caddy validates no chain, a `trust_pool` included. The handshake
  proves that the client holds the private key of what it presented (RFC 8446 §4.4.3), which is what
  `self_signed_tls_client_auth` (RFC 8705 §2.2) needs.
- **The provider validates the leaf of `tls_client_auth` itself** (RFC 8705 §2.1, §7.4), against the
  authorities `BEFFROI_MTLS_CERTIFICATE_AUTHORITIES` names, a JSON list of PEM certificates: a certificate one
  of them signed, valid at the moment of the request and carrying the name its client registered,
  authenticates that client. Each authority is therefore the one that signs the client certificates itself,
  intermediate or root, and a certificate that is no certificate authority (RFC 5280 §4.2.1.9) is refused.
  Revocation is not checked. With no authority named, the default, `tls_client_auth` is neither announced nor
  registered, and a client of that method is refused like any client of a method the provider does not wire.

### The host of the administration API

**The administration API is a host of its own**, served when `CADDY_EXTRA_CONFIG` imports
`administration.Caddyfile`, under the address `ADMINISTRATION_SERVER_NAME` gives it, which is the host of
`BEFFROI_TENANT_ADMINISTRATION_RESOURCE`. Its worker serves the routes of the administration API and no other,
and the processes of the host of `SERVER_NAME` never load them. That site follows neither `TLS_TERMINATION` nor
the snippet above: Caddy serves it with the certificate it holds or obtains for that name, under its own
defaults, and behind a proxy that terminates TLS the variable names a plain HTTP address, such as `:81`. A
deployment that does not import the file serves no administration API.

``` dotenv
ADMINISTRATION_SERVER_NAME=admin.example.com
CADDY_EXTRA_CONFIG='import administration.Caddyfile'
BEFFROI_TENANT_ADMINISTRATION_RESOURCE=https://admin.example.com
```

[:beffroi-arrow-right: The variables of the web server](configuration.md#the-web-server)

## Behind a proxy

**A proxy that terminates TLS sends the server plain HTTP.** With `TLS_TERMINATION` set to `proxy`, the site of
`SERVER_NAME` is `http://` followed by `SERVER_NAME`, which then names one host, the one the proxy asks for, or
`:<port>` for any host. It is served on port 80 unless `SERVER_NAME` names another, and never with the TLS
Caddy would choose by itself for a host: a list of hosts is refused, or read as one address. A scheme written
there, `http://op.example.com`, gives a site no request of the proxy reaches. Under `caddy`, the value the
variable takes when it is not set, the site carries the TLS above, and Caddy refuses a plain HTTP address. A
misspelt value, `Proxy` or an empty one, stops Caddy as it starts without a word in its log, and
`frankenphp adapt --config /etc/frankenphp/Caddyfile`, run in the image with the same environment, says why.
The TLS a client meets on the host of `SERVER_NAME` is then the one of the proxy.

The scheme and the address of a request are read by Symfony behind the proxies it trusts, and the application
names none: `framework.trusted_proxies` reads `SYMFONY_TRUSTED_PROXIES`. That address is what the load budget
of an origin is counted under, an IPv6 address by its /64, 2400 requests a minute by default before a `429`,
and what every session and every act of the journal records as where it came from. Behind a proxy that is not named there, every request
reads as plain HTTP and has the address of the proxy: a request of a safe method, a `GET` or a `HEAD` among
them, is sent to the same address over HTTPS, without end, and the others, a `POST` among them, are
served as they came, under the address of the proxy.

[The health check](#the-health-check) asks the server from the loopback address, `127.0.0.1`, with the
`X-Forwarded-Proto` the proxy would send, so `SYMFONY_TRUSTED_PROXIES` names that address as well, and
`SYMFONY_TRUSTED_HEADERS`, when it is set, keeps `x-forwarded-proto`. Otherwise Symfony reads the check as
plain HTTP, sends it to HTTPS, and the container is unhealthy. `private_ranges` holds the loopback address,
and a deployment that names its proxy by its address adds `127.0.0.1`.

A proxy that names the client in a header Symfony does not read, `CF-Connecting-IP` behind Cloudflare, has
Caddy read it, with `client_ip_headers` and `trusted_proxies` in `CADDY_SERVER_OPTIONS`, the options of the one
`servers` block the image writes for every listener of its sites, and write it into `X-Forwarded-For`, with
`request_header X-Forwarded-For {client_ip}` in `CADDY_SERVER_EXTRA_DIRECTIVES`, and in
`CADDY_ADMINISTRATION_EXTRA_DIRECTIVES` for the site of the administration API, each site carrying its own:
FrankenPHP hands PHP the address of its peer and the headers as they arrived, whatever Caddy read. A
`servers { }` block written in `CADDY_GLOBAL_OPTIONS` is a second block for the same listeners, which Caddy
refuses as it starts.

The host that asks for a client certificate terminates its TLS in Caddy whatever `TLS_TERMINATION` says. A
client presents its certificate in the handshake, so a proxy in front of that host passes its connections
through without terminating them.

[:beffroi-arrow-right: Behind a proxy that terminates TLS](examples.md#behind-a-proxy-that-terminates-tls)

## The headers

**Two layers write the security headers, and where they meet, one gives way.** `App\Http\InteractionPages`
gives every page of the interaction plane `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`,
`Cache-Control: no-store` and the floor of a content policy, `frame-ancestors 'none'`. The application writes
the headers of a deployment on every answer, from two files of its configuration,
`config/packages/nelmio_security.yaml` and `config/packages/nelmio_cors.yaml`:

- `X-Frame-Options` is left as a page already carries it, and `Referrer-Policy` is written again with the
  value the pages carry, `no-referrer`;
- on a page whose content policy is the floor alone, `App\Http\DeploymentPolicyPrevails` drops the floor
  before the policy of the deployment is written, so one policy is sent. A page that computed a whole policy
  of its own keeps it, the form post response and the front-channel logout page, and so does a redirection.

A header written twice is not replaced, it collides: two content policies are both enforced, and what applies
is their intersection. Nothing the application writes is therefore written again in the web server or at the
edge. The assets compiled into `public/assets/` are answered by FrankenPHP without asking PHP, and carry none
of these headers.

The application names the session cookie in `config/packages/framework.yaml`: `__Host-beffroi_session`,
`Secure`, `HttpOnly`, `SameSite=Lax`, on the path `/` and with no `Domain`. HSTS is not sent in the
development environment, where it would pin every `.localhost` name of the machine to HTTPS.

[:beffroi-arrow-right: The headers](../../the-project/secure-by-default.md#what-a-deployment-answers-with)

## What leaves the provider

A deployment that filters what goes out reads it here. No outbound redirect is followed, whoever asks, but
two, each to the one host the application names: a download of MaxMind is followed to its storage, and a
revocation list of the test service of the FIDO Alliance to the host that serves it. A text leaves for Sweego
alone, the one bridge of `symfony/notifier` the image installs.

**A URL of the protocol reaches no network of the deployment, whoever wrote it.** The `jwks_uri` of a client or
of a trusted issuer, a `request_uri`, a `sector_identifier_uri`, a `backchannel_logout_uri`, a
`backchannel_client_notification_endpoint` and the endpoint of a push subscription are refused a private,
loopback, link-local or reserved address, IPv4 mapped in IPv6 included: the address is checked once the name is
resolved and on every address the request connects to, and the one checked is the one connected to, so a name
that resolves twice cannot rebind. A deployment whose clients answer on its own networks names those networks,
and no wider, in `BEFFROI_OUTBOUND_REACHABLE_PRIVATE_NETWORKS`, a JSON list of IP addresses or networks in CIDR
notation, `[]` by default: `'["10.20.0.0/16"]'`. The requests whose URL the deployment fixes, to the key
management service, the SAML peers, MaxMind, the FIDO metadata, the list of passkey providers the community
keeps, the list of compromised passwords and the bridge of mail and SMS, are not held to it.

| From | To | When |
|---|---|---|
| Every process | The key management service | To open a key, a salt or a data key, and to seal one |
| The server | The `jwks_uri` of a client or of a trusted issuer | To read its keys, which are then kept a day, and again when an assertion names a key the kept set does not hold, never less than five minutes after the last read, one that failed included |
| The server | The `request_uri` of a client | When an authorization request names one |
| The server | The `sector_identifier_uri` of a client | When a client registers or replaces itself |
| The server, the console | The list of compromised passwords, when one is named | When a password is written, and the answer is waited for |
| The worker | The list of compromised passwords, when one is named | After a login, for a password already posed |
| The worker | The `backchannel_logout_uri` of a client | When a session that client signed in ends |
| The worker | The `backchannel_client_notification_endpoint` of a client | When a backchannel request in `ping` mode is answered |
| The worker | The push service of a browser | When a backchannel request waits on the person who subscribed that browser, and when a way of signing in to their account changes |
| The worker | The mail server `BEFFROI_MAIL_DSN` names, when it names one and `BEFFROI_MAIL_SENDER` names a sender | When a backchannel request waits on a person whose address is marked verified, when a way of signing in to their account changes, and when a person asks for the code that confirms an address they wrote |
| The worker | The API of Sweego, `api.sweego.io` unless the DSN names another host, when `BEFFROI_SMS_DSN` names one | The same three, for a phone number |
| The worker, the console | The metadata of the SAML peers given by URL | Every hour, and on `beffroi:saml:*:refresh` |
| The worker, the console | MaxMind, when a licence key is named | Every week, and on `beffroi:geoip:refresh`. A download, and what it unpacks to, stops and is refused past 512 MiB |
| The console | The FIDO Metadata Service, and the revocation lists the certificates of the chain of its BLOB name | On `beffroi:webauthn:mds-refresh` |
| The console | The list of passkey providers the community keeps, the `aaguid.json` of `passkeydeveloper/passkey-authenticator-aaguids` on `raw.githubusercontent.com` | On `beffroi:webauthn:aaguids-refresh` |
