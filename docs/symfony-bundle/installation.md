---
title: Installing the bundle
description: What the bundle requires, what it writes into the configuration of the other bundles, what the application writes, and the first run.
---

# Installing the bundle

The bundle is installed as any Symfony bundle is, and most of what it needs from the other bundles of the
kernel it writes itself. What it cannot know is the application's to write: the key management client, the
issuer, the firewall, the path the routes are mounted under. [Getting started](../getting-started/installation.md)
is the short path through it; this page is the whole of it.

## What it requires

| What | Version |
|---|---|
| PHP | 8.4 or later, with the `intl` and `zip` extensions |
| Symfony | 8.2 |
| Doctrine | ORM 3.7, DBAL 4.4, DoctrineBundle 3.3, Doctrine Migrations 3.9 |
| Database | PostgreSQL: the migrations the bundle ships are written for it and stop on any other platform |
| Key management | A client of `symfony/key-management`, declared by the application |

The kernel registers `FrameworkBundle`, `DoctrineBundle`, `SecurityBundle`, `TwigBundle` and the bundle
itself. To play the migrations it also registers `DoctrineMigrationsBundle`, which the standalone
application requires, and in development `WebProfilerBundle` shows [the panel of the
provider](profiler.md).

## Requiring and registering it

``` bash
composer require beffroi/symfony-bundle
```

The package has no Symfony Flex recipe: the configuration, the routes and the firewall below are written by
hand. The bundle is registered for every environment:

``` php title="config/bundles.php"
return [
    // ...
    Beffroi\Bundle\BeffroiBundle::class => ['all' => true],
];
```

## What the bundle writes for the other bundles

When the container is built, the bundle prepends its part to the configuration of the bundles it works
with, and only of those the kernel registers. An application writes none of this, and a prepended
configuration being merged first, a key the application writes itself is the one that stands.

| Extension | What the bundle adds |
|---|---|
| `doctrine` | Its DBAL types, and three XML mappings, `BeffroiCore`, `BeffroiOidc` and `BeffroiSaml`, for the model of the three packages. The types that seal a column are registered when the bundles boot |
| `doctrine_migrations` | The directory of its migrations, under the namespace `Beffroi\Bundle\Migrations` |
| `security` | The password hasher of `Beffroi\Bundle\Security\SecurityUser`, which is `Beffroi\Bundle\Security\CorePasswordHasher`, the hasher of the core |
| `rate_limiter` | Two limiters, `beffroi_code_attempts` and `beffroi_password_attempts`: five attempts per user in a sliding window of one minute |
| `framework` | Eight cache pools on `cache.app`: `beffroi.client_keys`, `beffroi.issuer_keys`, `beffroi.client_assertions`, `beffroi.issuer_assertions`, `beffroi.software_statements`, `beffroi.request_objects`, `beffroi.dpop` and `beffroi.load` |
| `messenger` | The three buses, their middleware, the routing of every message, the serializer and the transports |
| `scheduler` | `use_messenger_routing: true`, so that the recurring messages of the provider are routed by their class like every other message |

[:beffroi-arrow-right: Persistence](persistence.md) &nbsp; [:beffroi-arrow-right: Messenger](messenger.md)

## What the application writes

### The key management client

The bundle seals with a client it does not build. The client is declared under `key_management.clients`,
and the bundle names it:

``` yaml title="config/packages/key_management.yaml"
key_management:
    clients:
        op: 'service://beffroi.kms.op'

services:
    beffroi.kms.op:
        class: Symfony\Component\KeyManagement\EncrypterInterface
        factory: ['@key_management.factory', 'fromString']
        arguments: ['%env(BEFFROI_KMS_DSN)%']
```

[:beffroi-arrow-right: Key management](key-management.md)

### The configuration of the bundle

Two sections are required: the tenant with its issuer, and the keys with the client that seals them and the
master key they are sealed under. Every other section has a default, or is a feature the deployment does
not serve until it names it.

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    tenant:
        issuer: '%env(BEFFROI_ISSUER)%'
    keys:
        kms: op
        key_id: '%env(BEFFROI_KMS_KEY_ID)%'
```

A `kms` that names no client of `key_management.clients` fails the build of the container, and the message
lists the clients that are registered.

[:beffroi-arrow-right: The configuration, section by section](configuration.md)

### The routes

``` yaml title="config/routes/beffroi.yaml"
beffroi:
    resource: '@BeffroiBundle/config/routes.php'
```

They are imported under the path of the issuer, which is no prefix at all for an issuer that is an origin.

[:beffroi-arrow-right: Routes and planes](routes-and-planes.md)

### The firewall

The application declares the user provider, the two firewalls of the provider and the authenticators on
the second; the bundle declares none of it.

[:beffroi-arrow-right: The firewalls](security.md#the-firewalls)

### The session

The pages bind a browser to its session through the HTTP session of the framework. The standalone
application names and bounds that cookie this way:

``` yaml title="config/packages/framework.yaml"
framework:
    session:
        name: '__Host-beffroi_session'
        cookie_secure: true
        cookie_httponly: true
        cookie_samesite: lax
        cookie_path: '/'
        cookie_domain: ~
```

The `__Host-` prefix has the browser refuse the cookie unless it is `Secure`, its path `/` and its domain
unnamed, which the issuer of that application, an origin alone, allows. `lax` is the one value that cannot be
tightened: a client sends the browser to the authorization endpoint by a top-level navigation from its own
site, and `strict` would leave the cookie behind on it, so every authorization request would meet a provider
that does not know the visitor. What `lax` does to a post from another site is answered by the provider
itself.

[:beffroi-arrow-right: A post from another site](security.md#a-post-from-another-site)

### What several processes share

A provider is several processes, the ones that serve requests and the worker, and some of what they hold
has to be the same for all of them.

- **The directory of the keys**, `beffroi.keys.storage`: the worker rotates the keys the other processes
  serve, so they read one directory.
- **The cache pools of the bundle**, the keys published by clients and trusted issuers, the assertions,
  statements, request objects and DPoP proofs already seen, and the counts of the load budgets: a
  deployment of more than one machine points them at a store they share.
- **The counts of the two limiters**, kept in the cache pool of the rate limiters.

Messenger needs nothing more to start: every lane of the provider is the database unless the environment
names a broker, and a worker consumes them.

[:beffroi-arrow-right: The worker](messenger.md#the-worker)

## The first run

``` bash
bin/console doctrine:migrations:migrate
bin/console beffroi:tenant:synchronize
bin/console beffroi:keys:generate --algorithm=MESSAGE-SEAL
bin/console beffroi:keys:generate
```

1. **The schema.** The migrations of the bundle are played with those of the application.
2. **The row of the tenant.** The tenant is declared in the configuration and the command writes the row
   that says the same thing. Until it exists, a request fails rather than being served, and a command that
   works on the tenant stops and says to run this one first.
3. **The key messages are sealed to.** Every message the provider writes to a transport is sealed to a key
   of the tenant, and a key that is drawn announces itself on a transport: this key comes first, or the
   next command stops on `Tenant "default" holds no MESSAGE-SEAL key: it is the first key a tenant is given,
   and nothing it writes to a transport leaves the process before it exists.`
4. **A signing key**, of the default algorithm when none is named.

A key of any other algorithm the deployment serves is drawn the same way, under its name: `VAPID` for [web
push](web-push.md), `SAML-SIGNING` for [the identity provider of SAML](../saml/identity-provider.md). Then
comes a first person.

[:beffroi-arrow-right: The tenant and its keys](../getting-started/tenant-and-keys.md)

## Checking the result

``` bash
bin/console beffroi:doctor
bin/console beffroi:keys:list --check
bin/console debug:router
```

- `beffroi:doctor` reads and writes nothing, says whether the deployment holds together point by point, and
  fails on a point it does not answer for, so a deployment pipeline can ask the same question.
- `beffroi:keys:list --check` opens the keys in use, and the ones about to be, with the key management
  service, and fails on one it cannot open or on one that has worked past its age with nothing staged
  behind it.
- `debug:router` lists the routes, those of the bundle under names that carry their plane.

The discovery document is the last check: `<issuer>/.well-known/openid-configuration` answers once the routes
are where the issuer says they are. Otherwise the first request that needs the endpoints fails with an
exception naming where the document is served and where the issuer makes clients look for it.

## Changing the configuration later

**What the configuration says of the tenant is copied to its row.** After a change of its name, its look,
the claims its people may change or its `acr` vocabulary, `beffroi:tenant:synchronize` writes the row again;
until it does, a request fails with an exception naming the field that disagrees. A changed issuer is
refused: every token issued so far names the old one, and another issuer is another tenant, under another
slug.

**A migration that seals columns says what to restart.** A process that booted before it reads those
columns with the type they had, so the processes that serve requests and the ones that consume the buses are
restarted once it has run. Such a migration also refuses to run on a table that holds rows, naming the
table and the count, since there is nothing to put in a sealed column from a value in clear.
