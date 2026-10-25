---
title: SCIM
status: draft
description: Receiving what a directory pushes, and keeping it synchronised. Planned, not implemented.
---

# SCIM

!!! warning "Not implemented yet"

    No SCIM endpoint is served at this point. This page says what is decided, so that nobody has to guess
    from an empty section. It will be replaced by the documentation of the endpoints the day they exist.

SCIM is how a directory pushes its people into a provider instead of being asked for them: Entra ID and
Okta both speak it, and for a company already running one, provisioning through SCIM is what makes an
identity provider usable without anyone creating a single user by hand.

## What it will serve

The receiving half, first: `/Users` and `/Groups` as RFC 7644 defines them, over the schema of RFC 7643.
Beffroi is the target of the provisioning, which is what Entra and Okta know how to drive, and what their
own validators judge.

## What is already decided

- **Groups carry a source.** The identity model holds, for every membership, where it came from: written in
  this provider, asserted by an upstream identity provider, or pushed by a directory. A directory may not
  quietly take over a group somebody created here, and what it pushed must be distinguishable from what was
  written by hand. That is a property of the [groups](../core/groups.md) model, and it exists before SCIM
  does.
- **The provenance model is the one federation uses.** What SCIM pushes and what a federated sign-in brings
  back are the same question asked twice: who told us this, and may they change it. A person already names
  the source that created them, and what a source holds a manual description does not change: a directory
  will be one more source, under the same rule.
- **The connector is judged from outside.** The success criterion is the Entra and Okta connectors, and their
  validators, against this provider. Not a test suite of our own.

## What it will not do

Beffroi will not push to other directories, and will not be a SCIM client. Signing a person in against the
identity provider of their organisation is federation, not provisioning, and it has [its own
place](../saml/upstream-identity-providers.md) in the SAML section.
