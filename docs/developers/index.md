---
title: The documentation for developers
description: For whoever writes an application that signs people in with Beffroi, a resource server that reads its tokens, or code on its packages.
---

# The documentation for developers

These pages are for whoever writes code against Beffroi: an application that signs its people in through
it, an API that reads the access tokens it issues, or a project built on its PHP packages. Installing and
running the provider is in [the documentation for operators](../operators/index.md), administering its
tenants and their people is in [the documentation for administrators](../administrators/index.md), and what
a person does with their account is in [the documentation for users](../users/index.md).

| Section | What it holds |
|---|---|
| [Connect an application](connect/your-first-client.md) | Registering a client, then signing people in to a Symfony or a Laravel application |
| [OAuth 2.0 and OpenID Connect](oidc/index.md) | What each endpoint reads and answers: clients and their authentication, the authorization request, the grants, the tokens, discovery, logout and every error |
| [The packages](packages.md) | The packages Beffroi is made of, which one you need, and the ports and events of the identity core |
| [The profiler panel](profiler.md) | What the provider received, decided and emitted during a request, in the Symfony profiler |
| [Reference](reference/endpoints.md) | Every route, every event, and the specifications Beffroi implements |
| [Contributing](contributing.md) | Reporting a problem, sending a patch, and building this documentation |
