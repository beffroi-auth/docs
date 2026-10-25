---
title: Passkeys
status: draft
description: WebAuthn enrolment and assertion, and what a passkey lets a relying party require.
---

# Passkeys

A passkey is a WebAuthn credential (W3C Web Authentication Level 3), enrolled from the account pages and
usable on its own, with no password in the way. It is what lets a client require a stronger authentication
with `acr_values`, and what the provider answers `acr` with once it has been used.

## Synced or bound

Whether a passkey may be synced to other devices is the backup eligibility flag its authenticator set when it
was created, which WebAuthn Level 3 §6.1.3 forbids to change. The flag recorded at the enrolment is the one
the provider reads for the rest of the life of that passkey: it decides whether a login with it answers `phr`
or `phrh`, and an assertion that carries another flag is refused, as a revoked passkey is, rather than
rewriting the record.

## A first passkey from a ticket

A person created on a tenant that signs its people in by passkey has nothing to sign in with, and no password
to be given. An administrator issues them a ticket instead:

``` bash
bin/console beffroi:user:enrolment-ticket alice
```

The command prints a link, `/enrol/{ticket}/{value}` under the issuer, once, and the row keeps a hash of what
it carries, so a store read by somebody else opens nothing. Whoever issued it hands it over.

- **It opens one enrolment, once.** The page asks the browser for a passkey, and the ticket is spent only
  when the passkey is in the rows: a ceremony that could not finish leaves the person their link.
- **For seventy-two hours**, which covers a weekend between the day it is issued and the day somebody starts.
  What is not used in three days is issued again.
- **One at a time.** Issuing a ticket forgets the unspent ones of that person, so a link forgotten in a mailbox
  stops opening anything the day another is issued. A disabled account gets none.
- **It proves no login.** Once the passkey is posed, the browser is sent to sign in with it: the session comes
  from the passkey, never from possession of the link.

The page needs a browser that can hold a passkey, and says so to one that cannot. Issuing a ticket is an act
of the journal of that person.

## Not for the people of an organisation

A person whose address is of a domain an [upstream identity provider](../../saml/federated-sign-in.md)
answers for signs in there, and is posed no passkey here: the pages of the account offer them no form, and an
enrolment, a ticket's included, is refused.

This page will describe enrolment, assertion, what is checked of an attestation, and the FIDO metadata the
check reads.
