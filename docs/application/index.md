---
title: The standalone application
description: beffroi/op, the deployment the project recommends: the Symfony skeleton, the bundle and FrankenPHP.
---

# The standalone application

`beffroi/op` is a provider you deploy rather than a provider you assemble: a Symfony skeleton on
[the bundle](../symfony-bundle/index.md), served by FrankenPHP in worker mode, with PostgreSQL for the
model and a broker for the writes the protocol does not wait on.

It is the deployment the project supports, and the one the conformance plans are run against, so a profile
reported green is green on this application.

## Why there is one at all

The bundle alone leaves a dozen decisions to whoever installs it: the web server, the worker, the broker,
the key management client, the migrations, the two planes, the images. Those decisions are the same for
almost everybody, so the project makes them once, in an application, instead of writing them again in a
guide. A team that wants to make them differently still can: the bundle is the same bundle.

## In this section

| Page | What it covers |
|---|---|
| [Deployment](deployment.md) | The image, FrankenPHP in worker mode, and the two planes |
| [Configuration](configuration.md) | The environment the application reads, and what each variable decides |
| [Operating it](operating.md) | Rotating keys, rewrapping data keys, migrations, backups |
| [Observability](observability.md) | What the provider records of a request, a session and a token |

It is the `apps/op` directory of the monorepo, mirrored read only as
[beffroi-auth/op](https://github.com/beffroi-auth/op). It resolves the packages from the directories beside
it, so it installs nothing on its own: it is worked on inside the monorepo, and deployed from an image built
there rather than from a clone of its mirror.
