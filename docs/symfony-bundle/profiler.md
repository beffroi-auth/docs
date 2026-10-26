---
title: The profiler panel
description: What the provider received, decided and emitted during a request, in the Symfony profiler, and what it withholds.
---

# The profiler panel

A request that is pushed, signed or bound to a key says nothing to whoever watches it from outside: the
browser carries a reference, the client posts a JWT, the endpoint answers a document. The panel the bundle
adds to the Symfony profiler says what the provider received, decided and emitted during the request, read
where the provider itself reads it.

## When it is there

The panel is wired when the kernel runs in debug, and nothing else turns it on: a deployment that does not run
in debug has no panel and no option to give it one. It is a page of the Symfony profiler, so the kernel
registers `WebProfilerBundle` and the profiler of the framework collects, which the standalone application
does in development.

It reports on a request that reached a route of the provider, one whose name starts with
`beffroi_interaction_` or `beffroi_protocol_`, and on no other: on a page of the host application, the toolbar
carries no entry of the provider. A route the process refuses for its plane is not reported as one it served.

What it shows is recorded by observers that decorate services the provider already uses, the reader of an
authorization request, the repository of the clients, the issuers of the tokens, the providers of the keys,
and add nothing to what those services do: the panel says what the request did and never what a list kept
beside the code claims.

## What it shows

The toolbar shows how many facts were recorded and, per tab, their headings. The panel groups them under
their tabs, in the order the request first spoke of each.

| Tab | Heading | What it says |
|---|---|---|
| Request | Endpoint | The route, the method and the path; the certificate the edge handed over, by the `x5t#S256` a token would be bound to (RFC 8705 §3.1), or that one was carried in a header and refused; whether a DPoP proof was presented (RFC 9449 §4.1) |
| Request | Authorization request | How it came in, in the query, pushed (RFC 9126 §4) or carried by a request object (OIDC Core §6.1); the query the browser carried and the request as the provider read it, side by side; the parameters of the query that were dropped |
| Request | JWT received, not yet verified | The `alg`, `kid`, `typ` and claims of every compact JWT read during the request, before anything verified it: a request object, a client assertion, a DPoP proof, a software statement, the assertion of a trusted issuer, and also the access token in the shape of a JWT and the signed ID token the token endpoint has just issued, which the panel reads back the same way to describe them |
| Interaction | Interaction | The authorization request the provider parked while the person signs in and consents: where it is, its dates, its language, the client, the redirection URI, the response mode, the scopes, the PKCE method, whether a `state`, a `nonce`, a `login_hint` and an `id_token_hint` were carried, `prompt`, `max_age`, `acr_values`, `ui_locales`, `display`, `dpop_jkt`, the claims asked for by name, and the session and consent attached to it |
| Client | Client | The client as it is registered: its identifier, its name, its authentication method, whether it must push its requests, whether it needs PKCE and consent, its grant types, its scopes, the shape of its access tokens and of its ID tokens, UserInfo answers and authorization responses |
| Client | Consent | The consent the request found or wrote, its scopes and when it was granted |
| Session | Session | The `sid`, the `auth_time`, the `amr` and the `acr` of the session, when it expires and whether it has ended |
| Decision | Decision | What the authorization endpoint decided and why: the login and the classes a step-up is still short of, with the kinds of credential that would reach one; the consent and the scopes asked; the answer and the names of the parameters sent back; or the refusal, with its `error` and its description |
| Tokens | Access token | The grant, the shape, the `jti`, the `aud`, the `exp`, the scopes of the response and the scopes granted, the binding of the token, and what the session had proven, or that nobody signed in |
| Tokens | ID token | Its `aud` and shape, whether the `nonce` was carried back, the `acr`, `amr` and `auth_time`, the claims the client asked for by name and the claims it carries |
| Keys | Key | The key that signed, or that opened what a client encrypted to the provider: its `kid`, algorithm, use and status, and the name of the key management client that opens it |
| Events | Event | Every event the provider announced during the request, by its name and the moment it happened |
| Response | Answer | The status, the content type, and the members of a JSON answer |
| Provider | What this provider serves | The discovery document of the tenant, member by member, read from the handler that answers it |
| Provider | Provider | Why the discovery document cannot be built, in its place, when it cannot |

## What it withholds

The panel withholds a value by its name, wherever it is written: a parameter a client sent, a member an
endpoint answered, a claim of a JWT.

- **A value under the name of a credential is said to be there and never written down**: `token`, `code`,
  `code_verifier`, `client_secret`, `request`, `client_assertion`, `dpop`, and every name that ends in
  `_token` or `_token_hint`, whether it was received or sent, written by the provider or read by it. The panel
  writes `(present, withheld)` in its place.
- **A claim about a person is named only**, every claim the provider serves being one: the panel writes
  `(a claim about the user, named only)`.
- **Every other value is written as it is.** That includes values a client polls or presents with: the
  `device_code`, `user_code` and `verification_uri_complete` of an answer of the device authorization
  endpoint, the `auth_req_id` of an answer of the backchannel authentication endpoint, and the `request_uri`
  of an answer of the pushed authorization endpoint, which the query of the browser then carries too.
- **What the provider encrypted for its client is not opened**: an ID token encrypted for its client is said
  to be so, and an answer that is not JSON is described as a page, a redirection or a document signed for the
  client rather than read.
- **A key is named by its `kid`**, its algorithm, its use and its status, never by its material, and the key
  management client by the name it carries in `key_management.clients`, never by its DSN, which may hold a
  credential.
- **A session is named by its identifier**, which tokens carry as `sid` anyway, and an event by its name and
  the moment it happened, never by what it carries.

## The panel of the key management service

`symfony/key-management` has a panel of its own, and in debug the bundle hands it what the provider seals and
opens: the envelopes of the keys and secrets of the tenant, and the store of the data keys of its sealed
columns. That panel then reports a request that read a sealed column, its calls grouped by scope,
`<slug>.<family>`. A data key is opened once per key and per process, so a request served by a process that
already holds it reports no call to the service, which is what that panel is there to show.

[:beffroi-arrow-right: Key management](key-management.md)
