---
title: Personal data
status: draft
description: Sealed columns, blind indexes, and data keys that can be rewrapped live.
---

# Personal data

Personal data is sealed in its column with a data key of the tenant, itself wrapped by the key management
service, so a database alone reads nothing. The lookups that must still work use blind indexes rather than
a readable column.

The data keys can be rewrapped onto another key management client while the provider serves sign-ins, and
destroying them is the one operation that cannot be undone.

The same rule holds past the database. The body of every message the provider writes to a transport is
sealed as well, so a broker or the table of a transport holds nothing readable, and the journal of the
acts, what a client was given at each of them, what a record used to say and the archive a person asks for
are sealed where they sit like every other column of a person. So is the source of a person, which says
which organisation they belong to, and so are the metadata accepted for a SAML peer, whose contacts name
people.

**The archive is the one file in which all of it stands in clear at once**, so it is held by rules rather
than by settings: it is sealed at rest in a scope of its own, it expires a week after it was asked for,
and that week is a figure in the code. It leaves under a passphrase of the person's choosing when they
ask for one.

[:beffroi-arrow-right: Your data, on the account pages](../symfony-bundle/account.md#your-data)

This page will describe what is sealed, what is indexed blind, the scopes a data key covers, and the
rewrapping.
