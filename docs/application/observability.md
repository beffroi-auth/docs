---
title: Observability
status: draft
description: What is recorded of a request, a session and a token.
---

# Observability

Every session and every event carries a request context: address, user agent, and what is derived from them,
enriched asynchronously so that a sign-in never waits on it. What is recorded, and for how long, is a
property of the deployment.

**The acts of the provider are written down, kept and read**: who did what, when and from where. Nothing
turns the journal on; what a deployment configures is how long an act is kept, six months by default,
which is the duration the CNIL deliberation 2021-122 holds for a log of connections. A deployment under
another obligation says its own, and a timed step forgets what is past it. What a person reads of their own
sign-ins comes from that journal, and what their record used to say is kept the same way and for the same
duration.

**A provenance says from where and not only from which address.** The enrichment reads the GeoLite2
databases of addresses, refreshed weekly by a timed step and installed by `beffroi:geoip:refresh`. They are
published by MaxMind under their own licence, so nothing is shipped and nothing is downloaded without a
licence key: a deployment that names none serves every flow with a provenance that says an address and no
place.

This page will describe the logs, the metrics, the audit records, and the retention.
