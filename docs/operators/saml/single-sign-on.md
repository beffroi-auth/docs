---
title: Single sign-on
description: What an AuthnRequest of a service provider is checked for, the session that answers it, and the signed assertion posted back, with the persistent NameID it carries.
---

# Single sign-on

A service provider sends the browser to the single sign-on service of the tenant with an `AuthnRequest`, and
the browser comes back to it with a signed `Response`. This is the Web Browser SSO profile (SAML Profiles
§4.1), over the two bindings a browser can carry.

``` mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant S as Service provider
    participant P as Beffroi
    S->>B: AuthnRequest, to /saml/sso
    B->>P: GET (HTTP-Redirect) or POST (HTTP-POST)
    P->>B: The login page, unless a session answers
    B->>P: The person signs in
    P->>B: A page that posts the signed Response
    B->>S: POST to its assertion consumer service
```

## The request

The single sign-on service is `/saml/sso`, `GET` for HTTP-Redirect and `POST` for HTTP-POST, at the one URL
the metadata publish. What is read, in this order:

1. **The binding.** One message parameter, every parameter at most once under its own name, every input
   bounded before it is decoded. Over HTTP-Redirect, the signature is verified over the query string exactly
   as it arrived, `SAMLRequest`, `RelayState` and `SigAlg` in that order (SAML Bindings §3.4.4.1), never over
   a version rebuilt from the parsed parameters.
2. **The service provider.** The one its `Issuer` names must be declared, and its metadata accepted.
3. **The signature.** Required unless the service provider and its metadata both say it does not sign, and
   verified whenever it is there: [the signature a request
   needs](service-providers.md#the-signature-a-request-needs).
4. **The assertion consumer service.** One of those the accepted metadata list. An
   `AssertionConsumerServiceURL` or an `AssertionConsumerServiceIndex` of the request is honoured only when it
   designates one of them, signed or not.

A request refused at any of these steps has nowhere trustworthy to be answered at, so it gets no SAML answer:
the browser is shown a page that names the rule, and never a value of the message.

The `RelayState` is opaque. It is read up to 1024 bytes and given back byte for byte, where SAML Bindings
§3.4.3 says 80: real service providers send longer ones, and the identity provider has to echo what it
received.

**A request posted from another site is posted again.** Under `SameSite=Lax` a browser sends no session
cookie with a `POST` coming from another site, which is exactly what the HTTP-POST binding is. A form posted
from another site without the session cookie is answered with a page of the provider's own origin that posts
the same body again, once, and the second post carries the session the browser holds: a person who is
signed in is not asked to sign in again because the service provider chose that binding.

## What answers it

In this order, so that nobody signs in to be refused afterwards:

| The request | The answer |
|---|---|
| A `NameIDPolicy` whose `Format` is neither `persistent` nor `unspecified` | `Requester`, `InvalidNameIDPolicy` (SAML Core §3.4.1.1): the identity provider writes no other format |
| A `RequestedAuthnContext` | `Responder`, `NoAuthnContext` (SAML Core §3.3.2.2.1): the identity provider states no class of its own |
| A browser holding an active session of the tenant, and, when the request says `ForceAuthn="true"`, a proof made in the second the request arrived or later | The assertion, at once |
| `IsPassive="true"` and no session that answers | `Responder`, `NoPassive` (SAML Core §3.4.1), without showing a page |
| Anything else | The login page of the provider |

A failure is a `Response` of that status and no assertion, signed like every response and posted to the
assertion consumer service of the metadata.

**The login is the provider's**, the page every flow signs in through, second factor and floor of the tenant
included. The request waits for it in the session of the browser that sent it, never in a URL, under a
reference drawn for it, for ten minutes, eight at most per browser, the oldest forgotten first. It is answered
once and forgotten: a browser that comes back later, or that did not send it, finds nothing and is shown the
page of a refusal.

**One session for both protocols.** The session is the one OpenID Connect opens. A person signed in by an
OpenID Connect client reaches a service provider without signing in again, and the other way round.

## The response

| What | Value |
|---|---|
| Signatures | The assertion is signed, then the response over it, under RSA-SHA256, by the active SAML key of the tenant. Each signature carries in its `KeyInfo` the certificate the metadata publish for that key |
| `Issuer` | The entity ID of the tenant, the URL of its metadata, with no `Format` |
| `Destination`, `Recipient` | The assertion consumer service resolved from the metadata |
| `InResponseTo` | The `ID` of the request, on the response and on its bearer confirmation |
| `AudienceRestriction` | One `Audience`, the entity ID of the service provider |
| Validity | Five minutes: the `Conditions` run from the `IssueInstant` of the assertion, their `NotBefore`, to 300 seconds later, and the bearer confirmation ends with them |
| `AuthnStatement` | The `AuthnInstant` is the latest proof of the session; the `SessionIndex` is the identifier of the session, the one the `sid` of OpenID Connect carries; the class is `urn:oasis:names:tc:SAML:2.0:ac:classes:unspecified`, and no `SessionNotOnOrAfter` |
| Attributes | The ones [its declaration maps](service-providers.md#the-attributes-it-receives) |

The bearer confirmation carries no `NotBefore`, which SAML Profiles §4.1.4.2 forbids it. The `KeyInfo` is a
hint for the service providers that need to tell which key signed, Microsoft Entra ID among them, and
nothing more: whoever verifies the signature takes the key from the metadata, as Beffroi does.

## The NameID

The subject of the assertion is a persistent identifier (SAML Core §8.3.7), its `NameQualifier` the entity ID
of the tenant and its `SPNameQualifier` the entity ID of the service provider. Its value is computed, never
drawn and never stored:

``` text
base64url( SHA-256( entity ID of the service provider ‖ NUL ‖ sub ‖ NUL ‖ salt ‖ NUL ) )
```

Forty-three characters, without padding. The salt is the secret of the tenant its pairwise subjects are
computed with (OIDC Core §8.1), sealed by the key management service. So:

- **the same person gets the same value** at every login, in every worker, after a restore and after an
  import that keeps the subjects;
- **two service providers get two values** they cannot relate to each other;
- **it is never the `sub`**, nor a username nor an address, and nobody who knows the `sub` an OpenID Connect
  client holds can compute the `NameID` a service provider receives. SAML Core §8.3.7 asks for values with
  "no discernible correspondence with the subject's actual identifier".

## The page that posts it

The browser carries the response with a page that posts a form to the assertion consumer service: every
name and value escaped for an HTML attribute, a one-line script that submits it and that its
`Content-Security-Policy` allows by its hash and allows nothing else, `default-src 'none'`, `base-uri
'none'` and `frame-ancestors 'none'`, a button inside `noscript` for a browser without scripts, and
`Cache-Control: no-cache, no-store`.

That page names no `form-action`. A browser checks that directive over every redirection a submission
follows, and an assertion consumer service answers the post by sending the browser on to wherever its
application lives, an origin no metadata state: Entra's `login.srf`, for one, sends it on to the client that
asked Entra. A `form-action` there would leave the browser on a blank page. What it would still close, a form
injected into the page, needs markup the page does not let in.

A success records that this service provider took part in the session, which is what [single
logout](single-logout.md) reads to tell it when the session ends.
