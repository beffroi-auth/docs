---
title: A Symfony relying party
status: draft
description: Pointing a Symfony application at Beffroi with the oidc_login authenticator, and checking tokens on a resource server.
---

# A Symfony relying party

The client of reference for this provider is Symfony's own `oidc_login` authenticator. Anything Beffroi
emits must be consumable by it with no patch, and anything it can verify, Beffroi must produce. When a
limit shows up in the authenticator, it is fixed upstream in Symfony rather than worked around here.

That makes a Symfony application the shortest path to a sign-in you can watch end to end: a firewall with
`oidc_login` pointed at the issuer, a client declared on the provider side, and the callback the
authenticator expects.

This page will carry that configuration, both halves of it: the firewall that signs a person in, and the
`access_token` firewall of a resource server checking what the provider issued, by introspection or by
verifying an `at+jwt` itself.

Until it is written, the reference relying party is
[beffroi-php/oidc-demo](https://github.com/beffroi-php/oidc-demo): a Symfony application on `oidc_login`, a
resource server that checks the same access token several ways, an API Platform API behind the
introspection endpoint where every operation names the scope it needs, and a forge where a client is
composed option by option out of what the provider announces and registered on the spot, from one that
puts the whole authorization request in the URL of a browser to one that pushes it signed, reads a signed
response, holds a bound token and opens an encrypted ID token.
