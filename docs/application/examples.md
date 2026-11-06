---
title: Examples
description: 'Whole deployments of the image written with its variables alone: one host with PostgreSQL, behind a proxy that terminates TLS, and the lists a deployment writes in JSON.'
---

# Examples

Each example runs the image as it is published, configured by its environment alone, with Docker Compose and
the Compose file of the image, [`compose.prod.yaml`](../getting-started/the-standalone-application.md#the-compose-file-of-the-image).
`op.example.com` stands for the name of the deployment, and every variable it gives the provider is in
[configuration](configuration.md).

## One host

`compose.prod.yaml` is one host: the server and the worker beside PostgreSQL, the lanes in the database, and
Caddy terminating TLS for a public name, with a certificate it obtains itself. A deployment writes two files
beside it. The first is the `.env` Compose reads, with the five variables the file requires and the name of
the second:

``` bash
cat > .env <<EOF
COMPOSE_FILE=compose.prod.yaml:compose.override.yaml
SERVER_NAME=op.example.com
APP_SECRET=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 24)
BEFFROI_KMS_DSN=sodium+dir:///app/var/kms?ext=.key
BEFFROI_KMS_KEY_ID=beffroi-{tenant}
EOF
chmod 600 .env
```

The second gives both processes what `compose.prod.yaml` does not name. Compose merges it into
`compose.prod.yaml`, and every command below reads both through `COMPOSE_FILE`:

``` yaml title="compose.override.yaml"
x-deployment: &deployment
  BEFFROI_REGISTRATION_MODE: initial_access_token
  BEFFROI_WEB_PUSH_SUBJECT: mailto:security@example.com

services:
  op:
    environment: *deployment
  worker:
    environment: *deployment
```

The master key of the file backend is drawn once into the volume of `var/kms`, before anything is sealed, and
a copy of it is kept somewhere else: lost, it opens nothing it sealed, and replacing it is a rotation, not a
new file under the same name.

``` bash
docker compose run --rm --no-deps --entrypoint sh op -c 'umask 077 && mkdir -p var/kms && chmod 700 var/kms && head -c 32 /dev/urandom > var/kms/beffroi-default.key'
docker compose run --rm --no-deps --entrypoint cat op var/kms/beffroi-default.key > beffroi-default.key
```

- **The two processes read the same variables of the provider and mount the same five volumes.** The server signs with keys the
  worker rotates, and the worker places addresses with the databases the console downloads:
  [what the processes share](deployment.md#what-the-processes-share).
- **Compose hands a container what its file names, and nothing else of `.env`.** A variable written in
  `.env` alone reaches no process, so the variables of the deployment are written under
  `x-deployment`, which both processes take.
- **`/data` keeps what Caddy obtains**, its certificate and the account it obtains it under, and `/config` the
  configuration it last ran. A container that loses `/data` asks the authority again.
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
docker compose up -d --wait
```

A client then registers itself with an initial access token the console issues, printed once, which it
presents as a bearer token to `https://op.example.com/register`
([dynamic registration](../oidc/dynamic-registration.md)):

``` bash
docker compose exec op bin/console beffroi:client:token:issue 'My application' --registrations=1 --days=1
```

## Behind a proxy that terminates TLS

The proxy terminates TLS for `op.example.com` and sends the server plain HTTP on port 8080 of the machine,
asking for `op.example.com`. The issuer and `SERVER_NAME` stay what `.env` names, and the server of
`compose.override.yaml` gains three variables and its ports:

``` yaml title="compose.override.yaml"
x-deployment: &deployment
  BEFFROI_REGISTRATION_MODE: initial_access_token
  BEFFROI_WEB_PUSH_SUBJECT: mailto:security@example.com

services:
  op:
    environment:
      <<: *deployment
      TLS_TERMINATION: proxy
      SYMFONY_TRUSTED_PROXIES: private_ranges
      SYMFONY_TRUSTED_HOSTS: '^op\.example\.com$$'
    ports: !override
      - "127.0.0.1:8080:80"
  worker:
    environment: *deployment
```

- **`TLS_TERMINATION: proxy` serves the site of `SERVER_NAME` on plain HTTP**, as `http://op.example.com` on
  port 80 of the container, which answers that host alone; `SERVER_NAME: ":80"` among the variables of the
  server would answer every host. The
  TLS a client meets is the one of the proxy: [behind a proxy](deployment.md#behind-a-proxy).
- **The proxy is trusted for what it forwards.** It sends `X-Forwarded-For`, `X-Forwarded-Proto` and
  `X-Forwarded-Port`, and `SYMFONY_TRUSTED_PROXIES` names where it connects from: `private_ranges` for a
  proxy on a private network, its address otherwise. Without it, every request comes from the proxy and over
  plain HTTP, and the provider sends a `GET` to HTTPS again and again.
- **`SYMFONY_TRUSTED_HOSTS` refuses with `400` any other host that reaches Symfony.** Caddy answers a host
  other than `op.example.com` with an empty `200` before it does, and the variable is what holds the line under
  `SERVER_NAME: ":80"`. `$$` is how a Compose file writes a `$`.
- **`!override` replaces the ports of `compose.prod.yaml`** instead of adding to them: the proxy reaches port
  8080 on the loopback address of the machine, and nothing else is published.
- **The address of a person is read from `X-Forwarded-For`, past the proxies Symfony trusts.** It is what the
  load budget of an origin counts and what a session and an act of the journal record.

A proxy that names the person in a header of its own, `CF-Connecting-IP` behind Cloudflare, has Caddy read
that header and write the address into `X-Forwarded-For`, where Symfony reads it. The same file, the server
with two more variables:

``` yaml title="compose.override.yaml"
x-deployment: &deployment
  BEFFROI_REGISTRATION_MODE: initial_access_token
  BEFFROI_WEB_PUSH_SUBJECT: mailto:security@example.com

services:
  op:
    environment:
      <<: *deployment
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
  worker:
    environment: *deployment
```

Caddy reads the first of those headers the request carries when it comes from a proxy `trusted_proxies`
names, and the address of the peer otherwise. FrankenPHP hands PHP the request as it arrived, so without
`CADDY_SERVER_EXTRA_DIRECTIVES` Symfony never sees what Caddy read. Whoever reaches the proxy without going
through the network that writes the header writes it at will: the address is worth what the filtering of the
origin is worth.

## Lists in JSON

Eight lists of the configuration are a JSON document each, of the shape the
[configuration reference](../reference/configuration.md) gives the list. A document fits on one line in single
quotes, or spreads over several in a literal block. Both processes read the tenant, so its lists are written
under `x-deployment`:

``` yaml title="compose.override.yaml"
x-deployment: &deployment
  BEFFROI_REGISTRATION_MODE: initial_access_token
  BEFFROI_WEB_PUSH_SUBJECT: mailto:security@example.com
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
`mail` and of `displayName` here. `{}` or `[]` is a list with nothing in it. An empty variable is no JSON
document at all, and is refused when the service it reaches is built. The first two lists are written in the
row of the tenant, so a change to either is followed by `beffroi:tenant:synchronize`:
[the tenant](configuration.md#the-tenant).
