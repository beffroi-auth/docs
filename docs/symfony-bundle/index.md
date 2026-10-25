---
title: The Symfony bundle
description: What beffroi/symfony-bundle adds to an application: configuration, routes, persistence, security, pages and commands.
---

# The Symfony bundle

`beffroi/symfony-bundle` is the only place in Beffroi where Symfony appears. A `Request`, the container, the
entity manager, a Twig template and a console command live here and nowhere else, which is what keeps the
two packages underneath usable without a framework.

## What it brings

| Page | What it covers |
|---|---|
| [Configuration](configuration.md) | One tree under `beffroi`, section by section, validated when the container is built |
| [Routes and planes](routes-and-planes.md) | The controllers of both planes, and `BEFFROI_PLANE` to restrict a process to one |
| [Persistence](persistence.md) | The Doctrine mapping, the migrations, and the DBAL types that read value objects back |
| [Security](security.md) | The firewalls, the authenticators, and what a session carries |
| [Key management](key-management.md) | The key management client the private keys are sealed with |
| [Pages](pages.md) | Login, consent, logout, device, and how to make them yours |
| [Translations](translations.md) | Every user-facing string, in XLIFF, and how a page decides which language it speaks |
| [Messenger](messenger.md) | Which writes are asynchronous, and which ones the protocol waits for |
| [The account pages](account.md) | What a person sees of themselves, and what they can take back |
| [Console commands](console-commands.md) | Tenant, users, clients, keys, data keys, FIDO metadata |
| [The profiler panel](profiler.md) | What the provider did during a request, in the Symfony profiler |

## Installing it

``` bash
composer require beffroi/symfony-bundle
```

[:beffroi-arrow-right: Installation, in full](installation.md)

## Conventions it follows

Knowing these makes the rest of this section predictable.

- **A controller is `final readonly`, one action per class**, with the route on `__invoke()`. There is no
  controller with six methods.
- **A route name carries its plane**: `beffroi_protocol_*` is server to server, `beffroi_interaction_*` is a
  browser. Nothing is ambiguous, and a process can be restricted to one of the two.
- **A value object a column holds whole goes in one column**, with a DBAL type of the bundle that reads it
  back through the object's own constructor, rather than a Doctrine embeddable fixing one type per field
  for the whole model. One embeddable is left in the mapping, embedded by one entity, and it is named where
  the mapping is described.
- **No write is synchronous unless the protocol needs its result in the same request.** Every exception is
  listed in the Messenger configuration with the reason it is one.
- **Every user-facing string is translated.** A signed-in person reads the pages in the language of their
  record; for anybody else the language comes from what the browser asked for, then `ui_locales`, then
  `Accept-Language`, and never from the URL.
- **A test never sleeps.** Time moves with a mocked clock, which survives a kernel reboot.
