---
title: Linked identities
status: draft
description: The same person at an upstream provider.
---

# Linked identities

A linked identity says that a user of this tenant is a given subject at a named upstream provider. It is
what federation writes, and what keeps a person from being duplicated every time they arrive by a different
door.

A linked identity is a provider and a subject, the provider named as the federation knows it, the entity ID
of an upstream SAML identity provider or the `identity_provider` of a trusted issuer, and the subject the
value that provider gives the person, compared byte for byte. The pair names one person of the tenant, and
the store refuses a second link of the same pair.

**Federation writes them.** At the first sign-in through an [upstream identity
provider](../saml/federated-sign-in.md#the-person), the person and their linked identity are created
together, with a snapshot of what the provider said; at the next ones the snapshot is refreshed. A person is
found by their link and never by their address: an address is given again to somebody else, a subject is
not.

**An operator writes one by hand**, for a person who exists already and is to sign in through a provider:

``` bash
bin/console beffroi:user:link alice 'https://idp.example.org/saml/metadata' 'the-subject-it-gives-alice'
```

Run again, it refreshes the link. A person linked that way signs in under the link without the rules of a
first sign-in, nothing the provider fills being written of them.

This page will describe the model in full.
