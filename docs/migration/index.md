---
title: Migration
status: draft
description: What changes between versions, and what to do about it.
---

# Migration

This section holds one page per version that asks something of you, with the changes listed and the way to
make them.

There is nothing here yet: no version of Beffroi is released, so no version has to be migrated from. The
first page will appear with the first release that changes a public interface.

## What to expect

- **Until `1.0`**, a minor version may change the public API. What changes is listed here, with the reason
  and the replacement, before the version is published.
- **A migration page describes the version it belongs to**, read from the version selector at the top of the
  page. It never describes a version you are not reading.
- **A database change ships as a Doctrine migration**, never as a sentence telling you to run some SQL.
- **A removal is announced before it happens.** A deprecation in one minor version, the removal in the next
  major one.

## Coming from another provider

Three things exist, and one does not.

- **The subjects can be kept.** `beffroi:user:create --subject` creates a person under the `sub` the clients
  already know them by, so an application that stored it finds the same person.
- **The old provider can stay where it is, upstream.** An identity provider that speaks SAML 2.0 is declared
  [upstream of the tenant](../saml/upstream-identity-providers.md): the people of its domains sign in there,
  and each is created here at their first sign-in, with the claims and the groups its declaration maps.
- **A person who exists here can be tied to it by hand**, with `beffroi:user:link`, and then signs in under
  that link.
- **A password hash cannot be imported.** No command takes one: a password is set from its value, and a person
  without one poses a passkey from an [enrolment ticket](../core/credentials/passkeys.md) or signs in through
  their organisation. Importing the people of a directory as they are is what [SCIM](../scim/index.md) will
  serve.
