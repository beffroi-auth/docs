---
title: Examples
description: Whole deployments of the image written with its variables alone: one host with PostgreSQL, behind a proxy that terminates TLS, and the lists a deployment writes in JSON.
---

# Examples

Each example runs the image as it is published, configured by its environment alone, with Docker Compose.
`op.example.com` stands for the name of the deployment, and every variable it sets is in
[configuration](configuration.md).

## One host

The server and the worker on one machine beside PostgreSQL, the lanes in the database, and Caddy terminating
TLS for a public name, with a certificate it obtains itself.

``` yaml title="compose.yaml"
services:
  database:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: beffroi
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?}
      POSTGRES_DB: beffroi
    volumes:
      - database:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "beffroi"]
      interval: 5s
    restart: unless-stopped

  op:
    image: ghcr.io/beffroi-auth/op:0.0.x
    environment: &environment
      APP_SECRET: ${APP_SECRET:?}
      DATABASE_URL: postgresql://beffroi:${POSTGRES_PASSWORD}@database:5432/beffroi?serverVersion=16&charset=utf8
      BEFFROI_ISSUER: https://op.example.com
      DEFAULT_URI: https://op.example.com
      SERVER_NAME: op.example.com
      BEFFROI_KMS_DSN: sodium+dir:///run/secrets?ext=.key
      BEFFROI_KMS_KEY_ID: beffroi-{tenant}
      BEFFROI_REGISTRATION_MODE: initial_access_token
      BEFFROI_WEB_PUSH_SUBJECT: mailto:security@example.com
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    volumes:
      - keys:/app/var/keys
      - geoip:/app/var/geoip
      - webauthn:/app/var/webauthn
      - caddy_data:/data
      - caddy_config:/config
    secrets: &secrets
      - source: kms_key
        target: beffroi-default.key
    depends_on:
      database:
        condition: service_healthy
    restart: unless-stopped

  worker:
    image: ghcr.io/beffroi-auth/op:0.0.x
    command:
      - bin/console
      - messenger:consume
      - scheduler_beffroi
      - async_notifications
      - async_priority_high
      - async_priority_medium
      - async_priority_low
      - --time-limit=3600
      - --memory-limit=256M
    environment: *environment
    volumes:
      - keys:/app/var/keys
      - geoip:/app/var/geoip
      - webauthn:/app/var/webauthn
    secrets: *secrets
    healthcheck:
      disable: true
    depends_on:
      op:
        condition: service_healthy
    restart: unless-stopped

volumes:
  database:
  keys:
  geoip:
  webauthn:
  caddy_data:
  caddy_config:

secrets:
  kms_key:
    file: ./beffroi-default.key
```

Compose reads the two secrets of the file from a `.env` beside it, and the key management service from a
file of thirty-two random bytes:

``` bash
printf 'POSTGRES_PASSWORD=%s\nAPP_SECRET=%s\n' "$(openssl rand -hex 24)" "$(openssl rand -hex 32)" > .env
head -c 32 /dev/urandom > beffroi-default.key
chmod 600 .env beffroi-default.key
```

The key is kept somewhere else as well: lost, it opens nothing it sealed, and replacing it is a rotation, not a
new file under the same name.

- **The two processes read the same environment and the same three directories.** The server signs with keys
  the worker rotates, and the worker places addresses with the databases the console downloads:
  [what the processes share](deployment.md#what-the-processes-share).
- **The master key is a secret of Compose**, mounted at `/run/secrets/beffroi-default.key`, outside the volume
  that holds the keys it seals.
- **`/data` keeps what Caddy obtains**, its certificate and the account it obtains it under, and `/config` the
  configuration it last ran. A container that loses `/data` asks the authority again.
- **The worker turns off the health check of the image**, which asks the admin API of Caddy, and only the
  server runs Caddy.
- **`BEFFROI_REGISTRATION_MODE` is what lets a client exist**, the image declaring none.

The first start is the one of [the standalone application](../getting-started/the-standalone-application.md#the-first-start-in-order):
the server first, which waits for the database and plays the migrations; then the tenant, its keys and a
person; then the worker, once the key it opens messages with exists.

``` bash
docker compose up -d --wait op
docker compose exec op bin/console beffroi:tenant:synchronize
docker compose exec op bin/console beffroi:keys:generate --algorithm=MESSAGE-SEAL
docker compose exec op bin/console beffroi:keys:generate
docker compose exec op bin/console beffroi:keys:generate --algorithm=VAPID
docker compose exec op bin/console beffroi:keys:generate --algorithm=SAML-SIGNING
docker compose exec op bin/console beffroi:user:create alice --email alice@example.com
docker compose exec op bin/console beffroi:user:set-password alice
docker compose up -d
```

A client then registers itself with an initial access token the console issues, printed once, which it
presents as a bearer token to `https://op.example.com/register`
([dynamic registration](../oidc/dynamic-registration.md)):

``` bash
docker compose exec op bin/console beffroi:client:token:issue 'My application' --registrations=1 --days=1
```

## Behind a proxy that terminates TLS

The proxy terminates TLS for `op.example.com` and sends the server plain HTTP on port 8080 of the machine,
asking for `op.example.com`. The issuer and `SERVER_NAME` stay what the file above names.

``` yaml title="compose.override.yaml"
services:
  op:
    environment:
      TLS_TERMINATION: proxy
      SYMFONY_TRUSTED_PROXIES: private_ranges
      SYMFONY_TRUSTED_HOSTS: '^op\.example\.com$$'
    ports: !override
      - "127.0.0.1:8080:80"
```

- **`TLS_TERMINATION: proxy` serves the site of `SERVER_NAME` on plain HTTP**, as `http://op.example.com` on
  port 80 of the container, which answers that host alone; `SERVER_NAME: ":80"` would answer every host. The
  TLS a client meets is the one of the proxy: [behind a proxy](deployment.md#behind-a-proxy).
- **The proxy is trusted for what it forwards.** It sends `X-Forwarded-For`, `X-Forwarded-Proto` and
  `X-Forwarded-Port`, and `SYMFONY_TRUSTED_PROXIES` names where it connects from: `private_ranges` for a
  proxy on a private network, its address otherwise. Without it, every request comes from the proxy and over
  plain HTTP, and the provider sends a `GET` to HTTPS again and again.
- **`SYMFONY_TRUSTED_HOSTS` refuses with `400` any other host that reaches Symfony.** Caddy answers a host
  other than `op.example.com` with an empty `200` before it does, and the variable is what holds the line under
  `SERVER_NAME: ":80"`. `$$` is how a Compose file writes a `$`.
- **`!override` replaces the ports of `compose.yaml`** instead of adding to them: the proxy reaches port 8080
  on the loopback address of the machine, and nothing else is published.
- **The address of a person is read from `X-Forwarded-For`, past the proxies Symfony trusts.** It is what the
  load budget of an origin counts and what a session and an act of the journal record.

A proxy that names the person in a header of its own, `CF-Connecting-IP` behind Cloudflare, has Caddy read
that header and write the address into `X-Forwarded-For`, where Symfony reads it. The same override, with two
more variables:

``` yaml title="compose.override.yaml"
services:
  op:
    environment:
      TLS_TERMINATION: proxy
      SYMFONY_TRUSTED_PROXIES: private_ranges
      SYMFONY_TRUSTED_HOSTS: '^op\.example\.com$$'
      CADDY_GLOBAL_OPTIONS: |
        servers {
          trusted_proxies static private_ranges
          client_ip_headers CF-Connecting-IP X-Forwarded-For
        }
      CADDY_SERVER_EXTRA_DIRECTIVES: request_header X-Forwarded-For {client_ip}
    ports: !override
      - "127.0.0.1:8080:80"
```

Caddy reads the first of those headers the request carries when it comes from a proxy `trusted_proxies`
names, and the address of the peer otherwise. FrankenPHP hands PHP the request as it arrived, so without
`CADDY_SERVER_EXTRA_DIRECTIVES` Symfony never sees what Caddy read. Whoever reaches the proxy without going through the
network that writes the header writes it at will: the address is worth what the filtering of the origin is
worth.

## Lists in JSON

Seven lists of the configuration are a JSON document each, of the shape the
[configuration reference](../reference/configuration.md) gives the list. A document fits on one line in single
quotes, or spreads over several in a literal block:

``` yaml title="compose.yaml"
services:
  op:
    environment:
      BEFFROI_TENANT_SELF_SERVED_CLAIMS: '["nickname","picture","locale","zoneinfo"]'
      BEFFROI_TENANT_AUTHENTICATION_CLASSES: '{"phr":"phishing_resistant","2":"two_factors","1":"single_factor"}'
      BEFFROI_SAML_SERVICE_PROVIDERS: |
        {
          "https://sp.example.com/saml/metadata": {
            "metadata": "https://sp.example.com/saml/metadata",
            "attributes": {
              "urn:oid:0.9.2342.19200300.100.1.3": { "claim": "email", "friendly_name": "mail" },
              "urn:oid:2.16.840.1.113730.3.1.241": { "claim": "name", "friendly_name": "displayName" }
            }
          }
        }
```

An attribute named under the default format, `uri`, is named by an absolute URI (SAML Core §8.2.2), the OID of
`mail` and of `displayName` here. `{}` or `[]` is a list with nothing in it. An empty variable is no JSON document at all, and is refused when
the service it reaches is built. The first two lists are written in the row of the tenant, so a change to
either is followed by `beffroi:tenant:synchronize`:
[the tenant](configuration.md#the-tenant).
