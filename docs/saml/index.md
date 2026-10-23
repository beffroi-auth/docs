---
title: SAML 2.0
status: draft
description: SAML 2.0 as an identity provider and as a service provider, with XML Signature and XML Encryption. Planned, not implemented.
---

# SAML 2.0

!!! warning "Not implemented yet"

    Beffroi serves no SAML endpoint at this point. This page says what is decided and what the shape will
    be, and it will be replaced by the documentation of the real thing.

SAML 2.0 is still what a large part of the installed base speaks, and an identity provider that cannot
answer it cannot replace the one a company already has. It is planned as a first-class protocol, not as a
compatibility layer bolted to the side.

## The shape

- **Both roles.** Identity provider, so applications that speak SAML can sign in against Beffroi; and
  service provider, so Beffroi can sign a person in against an existing SAML identity provider during a
  migration.
- **Both bindings that matter**, HTTP-Redirect and HTTP-POST, including the detached signature of a redirect,
  where the order of the parameters is part of what is signed.
- **The validity rules, all of them**: clock skew, `AudienceRestriction`, `InResponseTo`, `Recipient`,
  `NotBefore` and `NotOnOrAfter`, and replay detection by assertion identifier.

## Why the XML is written here

XML Signature and XML Encryption are the two specifications where a permissive parser becomes a
vulnerability: signature wrapping, entity expansion, canonicalisation that does not cover what you think it
covers. The PHP ecosystem has no library for them that is safe by construction, so they are being written
for this project, in packages of their own, with a safe DOM, an identifier index and a guarded
canonicalisation.

| Package | What it holds |
|---|---|
| [`xml-security`](https://github.com/beffroi-auth/xml-security) | The safe DOM, the identifier index, canonicalisation, signature and encryption |
| [`saml2-model`](https://github.com/beffroi-auth/saml2-model) | The `samlp`, `saml` and `md` objects, strict parsing, the validity rules, the `NameID` formats. No HTTP |
| [`saml2-bindings`](https://github.com/beffroi-auth/saml2-bindings) | HTTP-Redirect and HTTP-POST, on strings and arrays, never on a `Request` |

## What will judge it

SimpleSAMLphp as a service provider and as an identity provider, a SAML application on Entra ID, a test
ADFS, and the published corpora of XML signature attacks. There is no certification programme for SAML, so
the judge is interoperation with what is deployed, plus the attacks that are known.
