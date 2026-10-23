---
title: The standalone application
status: draft
description: The deployment the project recommends: the Symfony skeleton, the bundle and FrankenPHP, already assembled.
---

# The standalone application

`beffroi/op` is a Symfony skeleton on `beffroi/symfony-bundle`, served by FrankenPHP in worker mode, with
PostgreSQL for the model and a broker for the writes the protocol does not wait on. It is the deployment
the project supports, and the one the conformance plans run against.

It separates the two planes of the provider in the same image: a process serving the protocol endpoints and
a process serving the interactions can be restricted with `BEFFROI_PLANE`, so a browser never reaches a
machine that only answers clients.

This page will carry the deployment itself: the image, the environment, the migrations, and the first
start. Until it is written, [the application section](../application/index.md) holds what is settled, and
the repository of the application is [beffroi-auth/op](https://github.com/beffroi-auth/op).
