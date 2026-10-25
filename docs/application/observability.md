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
another obligation says its own, and a timed step forgets what is past it.

- **Every act done in the name of a person names them**, by the subject their account carries, and the client
  it was done on behalf of. That is what lets a person read what happened to their account, on [the page of
  their acts](../symfony-bundle/account.md#the-pages), and what `beffroi:user:journal` reads to answer a
  request about it.
- **The reads that hand a person over to a third party are acts too**: an introspection that tells a resource
  server who a token names, and a UserInfo answer.
- **What a client was given is kept beside the act that gave it**: at each issue of tokens, the scopes, the
  claims asked for by name, the authorization details and the shape of the token, sealed, so that what an
  application obtained of somebody still has an answer after the consent it was given under was taken back.
- **What a record used to say** is kept the same way, under a retention of its own, `history.retention`, six
  months as well unless the deployment says otherwise.

What a client was given is kept exactly as long as the act that gave it, and forgotten by the same timed
step: an act whose details are gone, or details whose act is gone, would be half an answer.

**A provenance says from where and not only from which address.** The enrichment reads the GeoLite2
databases of addresses, refreshed weekly by a timed step and installed by `beffroi:geoip:refresh`. They are
published by MaxMind under their own licence, so nothing is shipped and nothing is downloaded without a
licence key: a deployment that names none serves every flow with a provenance that says an address and no
place.

This page will describe the logs, the metrics, the audit records, and the retention.
