---
title: Backup codes
description: The ten single-use codes that stand in for the authenticator application of a TOTP, how they are drawn, spent and renewed, and what is left when the last one is used.
---

# Backup codes

Backup codes are what a person types on the code page when their authenticator application is out of reach. They
are not a credential of their own: the [TOTP](totp.md) holds them, ten of them, and they prove what a code of the
application proves, `otp`. Each one is accepted once, stored as a hash, and shown once, on the page that drew it.

## What a code is

| Property | Value |
|---|---|
| Length | Ten characters, written in two groups of five joined by a hyphen |
| Alphabet | The alphabet of RFC 4648 §6, the capital letters and the digits 2 to 7 |
| Entropy | Fifty bits: one byte drawn from the randomness of the deployment per character, its low five bits picking one of the thirty-two |
| At rest | A hash, made by the password hasher as a password is, `argon2id`, and the instant it was spent |

What the person types is compared in capitals, with the spaces and the hyphens taken out, so a code copied with its
hyphen, typed without it or in lower case is the same code.

## Shown once

A set is drawn when the TOTP is set up, and each time the person asks for another. Each time, the codes are the
response to the form that asked, one numbered list with a button that copies it where the browser lets the page
write to the clipboard, and they are stored hashed: nothing shows them again, the pages of the account included. Drawing them at the set-up
costs no hash until the first code of the application has confirmed it, so an enrolment abandoned leaves nothing.

## Spending one

On the code page, anything other than six digits is read as a backup code. It is held to the limit of the codes of
the application, five per person in a sliding window of one minute, and it is verified against every unspent code
of the set without stopping at the first that matches, the first that matched being the one spent. A code spent is
refused afterwards, as a code nobody issued is, and the page says that a backup code was refused and works only
once.

A code accepted writes the act `backup_code.used` to the journal of the person, not `totp.used`: what the two prove
is the same, what they say of the account is not, a spent code being one the person no longer has.

## Drawing another set

On [the page of the second factor](../../symfony-bundle/account.md#enrolling-a-second-factor), a person who
holds a TOTP draws another set with a proof made in the last five minutes. The ten new codes replace the whole
set at that instant: the ones they had stop working, spent or not, which is what somebody who lost their list
needs. It is not an enrolment: the application and what it proves are untouched, nothing is scanned again and no
code is asked for. The act `backup_codes.renewed` goes to the journal of the person and says when, which is what
somebody reading an old list on paper needs to know.

No set is drawn for a revoked TOTP, and none for a person of a domain an [upstream identity
provider](../../saml/federated-sign-in.md) answers for.

## When the last one is used

Nothing else happens: the TOTP stays active, the application goes on signing the person in, and the page of the
second factor counts what is left, down to `No backup code left`. A person who reaches it draws another set there.
Removing the application on that page, revoking the TOTP from the console or raising the floor of the tenant to
one that reads no `otp` takes every code of the set with it.
