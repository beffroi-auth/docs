---
title: Deployment
status: draft
description: The image, FrankenPHP in worker mode, and the two planes.
---

# Deployment

The application runs on FrankenPHP in worker mode, with a process per plane when a deployment separates them,
PostgreSQL for the model and a broker for the asynchronous writes. TLS terminates in front of it, and the
listener that asks for a client certificate is a host of its own.

**The security headers are shared by a rule**: the bundle writes what belongs to a page it builds, the
application writes what belongs to a deployment, and neither writes a header the other does, because a
header written twice collides rather than being replaced. What this application answers with is in two
files of its configuration, and nothing it writes is written again in the web server or at the edge.

[:octicons-arrow-right-24: The headers](../the-project/secure-by-default.md#what-a-deployment-answers-with)

This page will describe the image, the processes, the health checks, and the reverse proxy.
