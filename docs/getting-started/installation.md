---
title: Installation
description: What Beffroi needs to run, and where the application that serves it comes from.
---

# Installation

Beffroi is deployed as one application, `beffroi/op`, which runs on its own beside the applications it signs
people in to. They talk to it through the protocols it serves, and none of them installs it. A team that wants
the provider inside code of its own has [the components](../the-project/packages.md), and what it writes around
them is its own integration.

## What it needs

| What | Why |
|---|---|
| Database | PostgreSQL, through Doctrine ORM |
| A key management service | To seal the signing keys and the data keys. A key in a file of its own is the floor where no service is at hand, and holds against a dump of the storage, not against a compromise of the host; Vault, AWS KMS or another provider `symfony/key-management` supports keeps the key off the host |
| TLS | The provider serves nothing useful over plain HTTP, and the specifications require HTTPS on every endpoint |

The image of the application carries the rest: PHP with the extensions the provider needs, and FrankenPHP to
serve it.

No message broker is needed. The writes the protocol does not need the result of are dispatched
asynchronously, to four lanes that are queues of the database, `doctrine://default?queue_name={lane}` in
`BEFFROI_MESSENGER_DSN`, where they wait for a worker that consumes them (`messenger:consume`).

!!! info "Not public yet"

    The `beffroi/*` packages are not on Packagist at this point, and the monorepo,
    [beffroi-auth/beffroi](https://github.com/beffroi-auth/beffroi), and its image, `ghcr.io/beffroi-auth/op`,
    are private. The pages that follow run the application from a working copy of the monorepo, and from that
    image.

## The application

`beffroi/op` is a Symfony application served by FrankenPHP in worker mode. It holds the protocols, the
identity model, the pages, the console and the persistence, and a deployment chooses what differs from one
machine to the next through the environment: the issuer, the database, the key management service, and the
rest the configuration page lists. It runs on your machine as a development stack, and anywhere else from its
production image.

[:beffroi-arrow-right: The application, on your machine and as a deployment](the-standalone-application.md)

The issuer is the exact string the provider announces as `iss` and the prefix every endpoint is served
under. It is not a cosmetic setting: a client compares it byte by byte, and it never changes for a tenant.
Every token the tenant issued names it, so a configuration that names another issuer for the same tenant is
refused rather than served: another issuer is another tenant, under another slug.

[:beffroi-arrow-right: The environment the application reads](../application/configuration.md)

## Then

1. [The application](the-standalone-application.md), on your machine or as a deployment of its own.
2. [The tenant and its keys](tenant-and-keys.md), without which nothing can be signed.
3. [Your first client](your-first-client.md), so something can ask for a token.
4. [A Symfony relying party](a-symfony-relying-party.md), to see a sign-in end to end.
