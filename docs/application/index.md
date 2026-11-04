---
title: The application
description: 'beffroi/op, the provider: one Symfony application on the pure-PHP packages, served by FrankenPHP and set through its environment.'
---

# The application

`beffroi/op` is the provider. It is a Symfony application on the pure-PHP packages of Beffroi, served by
FrankenPHP in worker mode, with PostgreSQL for the model and for the writes the protocol does not wait on,
which wait there for its worker. It runs on its own, beside the applications it signs people in to, which
talk to it through the protocols it serves. The conformance plans are run against it, so a profile reported
green is green on this application.

It is the one place in Beffroi where the Symfony framework appears. A `Request`, the container, the entity
manager, a Twig template and a console command live here and nowhere else, which is what keeps the packages
underneath usable without a framework: they use a few standalone components, `symfony/uid` for identifiers
and `symfony/key-management` for the key management service, and nothing of the framework. A team that
wants the provider inside code of its own has those packages, and what it writes around them is its own
integration.

## Why it is one application

A provider needs a dozen decisions besides its protocols: the web server, the worker, where its lanes go,
the key management client, the migrations, the two planes, the image. They are the same for almost
everybody, so the project makes them once, in the application, and a deployment sets what differs from one
machine to the next through its environment.

## Running it

| Page | What it covers |
|---|---|
| [Deployment](deployment.md) | The image, FrankenPHP in worker mode, and the two planes |
| [Configuration](configuration.md) | The environment the application reads, and what each variable decides |
| [Examples](examples.md) | Whole deployments written with those variables: one host, behind a proxy, lists in JSON |
| [Console commands](console-commands.md) | Tenant, users, groups, clients, keys, data keys, SAML metadata, FIDO metadata |
| [Operating it](operating.md) | Rotating keys, rewrapping data keys, migrations, backups |
| [Observability](observability.md) | What the provider records of a request, a session and a token |

## How it is built

| Page | What it covers |
|---|---|
| [The configuration tree](configuration-tree.md) | One tree under `beffroi`, section by section, each value read from the variable a deployment sets: its shape checked when the container is built, the values of the environment when the provider first builds what they reach |
| [Routes and planes](routes-and-planes.md) | The controllers of both planes, and `BEFFROI_PLANE` to restrict a process to one |
| [Persistence](persistence.md) | The Doctrine mapping, the migrations, and the DBAL types that read value objects back |
| [Security](security.md) | The firewalls, the authenticators, and what a session carries |
| [Key management](key-management.md) | The key management client the private keys are sealed with |
| [Pages](pages.md) | Login, consent, logout, device, and what a deployment changes of them |
| [Translations](translations.md) | Every user-facing string, in XLIFF, and how a page decides which language it speaks |
| [The account pages](account.md) | What a person sees of themselves, and what they can take back |
| [Messenger](messenger.md) | Which writes are asynchronous, and which ones the protocol waits for |
| [Web push](web-push.md) | Reaching a person through the push service of a browser they signed in with |
| [The profiler panel](profiler.md) | What the provider did during a request, in the Symfony profiler |

## Conventions it follows

Knowing these makes the rest of this section predictable.

- **A controller is `final readonly`, one action per class**, with the route on `__invoke()`. There is no
  controller with six methods.
- **A route name carries its plane**: `beffroi_protocol_*` is server to server, `beffroi_interaction_*` is a
  browser, and a process can be restricted to one of the two. Every route of the image carries one, the
  choice of a theme, `beffroi_interaction_theme`, included.
- **A value object a column holds whole goes in one column**, with a DBAL type of the application that reads
  it back through the object's own constructor, rather than a Doctrine embeddable fixing one type per field
  for the whole model. One embeddable is left in the mapping, embedded by one entity, and it is named where
  the mapping is described.
- **What a request does not need the result of leaves as a message.** What the protocol or the page needs in
  the same request, a session opened or a passkey renamed, is written by the use case in that request; the
  rest, the acts of the journal, the enrichment of a provenance, the notifications, travels on a lane, and no
  message of the provider travels on the synchronous transport.
- **Every user-facing string is translated.** A signed-in person reads the pages in the language of their
  record; for anybody else the language comes from what the browser asked for, then `ui_locales`, then
  `Accept-Language`, and never from the URL.
- **A test never sleeps.** Time moves with a mocked clock, which survives a kernel reboot.

## Where it comes from

It is the `apps/op` directory of the monorepo, mirrored read only as
[beffroi-auth/op](https://github.com/beffroi-auth/op). It resolves the packages from the directories beside
it, so it installs nothing on its own: it is worked on inside the monorepo, and deployed from an image built
there rather than from a clone of its mirror.

[:beffroi-arrow-right: Running the application](../getting-started/the-standalone-application.md)
