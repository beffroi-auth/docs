---
title: Installation
description: What Beffroi needs to run, and how to require it in an application or deploy it as one.
---

# Installation

## What it needs

| What | Why |
|---|---|
| PHP | 8.4 or later |
| Database | PostgreSQL, through Doctrine ORM |
| A key management service | To seal the signing keys and the data keys. For development, a local file-backed client is enough; a deployment uses Vault, AWS KMS or another provider `symfony/key-management` supports |
| TLS | The provider serves nothing useful over plain HTTP, and the specifications require HTTPS on every endpoint |

A message broker is not required to start. The writes the protocol does not need the result of are
dispatched asynchronously, to four lanes that default to the database, a queue each of
`doctrine://default?queue_name={lane}`, where they wait for a worker that consumes them
(`messenger:consume`). A broker takes their place by its DSN in `BEFFROI_MESSENGER_DSN`, which writes `{lane}`
where the name of each lane goes.

!!! info "Nothing is published yet"

    The `beffroi/*` packages are not on Packagist at this point, so the commands below describe the
    installation of the version this documentation follows rather than one you can run today. The pages are
    written now so that the first release does not ship undocumented.

## In a Symfony application

``` bash
composer require beffroi/symfony-bundle
```

Without Symfony Flex, register the bundle yourself:

``` php title="config/bundles.php"
return [
    // ...
    Beffroi\Bundle\BeffroiBundle::class => ['all' => true],
];
```

Then import the routes of the bundle under the path your issuer uses. A provider whose issuer is
`https://op.example.com` imports them at the root:

``` yaml title="config/routes/beffroi.yaml"
beffroi:
    resource: '@BeffroiBundle/config/routes.php'
    prefix: /
```

What the configuration cannot do without is the issuer, and the client of `symfony/key-management` the
private keys are sealed with, which the application declares and the bundle names:

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

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    tenant:
        issuer: '%env(BEFFROI_ISSUER)%'
    keys:
        kms: op
        key_id: '%env(BEFFROI_KMS_KEY_ID)%'
        storage: '%kernel.project_dir%/var/keys'
    clients: []
```

A name `key_management.clients` does not hold fails the build of the container. The firewall of the pages,
the session cookie and the rest an application writes are on [installing the
bundle](../symfony-bundle/installation.md).

The issuer is the exact string the provider announces as `iss` and the prefix every endpoint is served
under. It is not a cosmetic setting: a client compares it byte by byte, and it never changes for a tenant.
Every token the tenant issued names it, so a configuration that names another issuer for the same tenant is
refused rather than served: another issuer is another tenant, under another slug.

[:beffroi-arrow-right: The whole configuration tree](../symfony-bundle/configuration.md)

## As an application of its own

If you have no application to host it, do not write one. `beffroi/op` is the Symfony skeleton, the bundle
and FrankenPHP already assembled, and it is the deployment the project supports.

[:beffroi-arrow-right: The standalone application](the-standalone-application.md)

## Then

1. [The tenant and its keys](tenant-and-keys.md), without which nothing can be signed.
2. [Your first client](your-first-client.md), so something can ask for a token.
3. [A Symfony relying party](a-symfony-relying-party.md), to see a sign-in end to end.
