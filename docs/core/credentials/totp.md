---
title: TOTP
description: A time-based one-time password as the second factor of a password, RFC 6238: its parameters, its enrolment, the code page, replay and revocation.
---

# TOTP

A TOTP (RFC 6238, on the HOTP construction of RFC 4226) is the second factor of a password: a person sets up an
authenticator application from the pages of their account, and from then on a password alone signs them in no
more, the code page asking for the code the application shows. A person holds one active TOTP, which carries no
name, since nothing tells one authenticator application from another, and ten [backup
codes](backup-codes.md) go with it. What it proves is `otp` (RFC 8176 §2), a code of the application or a backup
code alike.

## The parameters

| Parameter | Value |
|---|---|
| Period | Thirty seconds (RFC 6238 §5.2) |
| Digits | Six |
| Algorithm | HMAC-SHA-1 (RFC 6238 §5.1) |
| Secret | 160 bits, the length RFC 4226 §4 recommends, drawn from the randomness of the deployment |
| Window | The current time step and one on each side (RFC 6238 §5.2) |

They are the parameters every authenticator application implements, and none of them is an option. The secret
is stored sealed by the key management service of the tenant, an envelope that opens for that tenant and for that
use only, and the code is computed in memory when one is checked.

## Setting one up

On [the page of the second factor](../../symfony-bundle/account.md#enrolling-a-second-factor),
`/account/two-factor`, a person who holds none is offered to set one up, where the floor of the tenant admits a
one-time code. The enrolment is the two steps it is:

1. **The secret is handed to the application.** The page shows the provisioning URI as a QR code, an SVG the
   bundle draws and embeds, with no image loaded from anywhere, and the same secret in base32, in groups of four,
   for an application in front of no camera. The URI is the Key Uri Format: the name of the tenant as the issuer
   and the username as the account, a colon in either shown as a space.
2. **The first code confirms it.** A code the application computes for the current step, or one on each side,
   creates the credential, its secret sealed and its backup codes hashed, and the step of that code is recorded as
   accepted, so the code that enrolled the application signs nobody in. The response is the page of the ten
   backup codes, shown this once.

What the first step drew, the secret, the URI and the backup codes, is kept in the session of that browser for
ten minutes, sealed by the key management service of the tenant, and nowhere else: an enrolment abandoned leaves
nothing behind, and a code that does not match shows the same QR code again, so the application is not scanned
twice. Both steps ask for a proof made in the last five minutes.

A person who holds an active TOTP is refused a second one, and removes the first before setting up another. A
tenant whose floor reads no `otp`, `phishing_resistant` or `phishing_resistant_hardware`, sets up none, and nor
does a person of a domain an [upstream identity provider](../../saml/federated-sign-in.md) answers for. A TOTP
set up writes the act `credential.enrolled` to the journal of the person.

## The code page

A password verified for a person who holds an active TOTP opens nothing: the login is held in the session of the
browser for five minutes, and the browser is sent to the code page, `/login/code`, which asks for the code the
application shows, or one of the backup codes.

What was typed is read without the spaces somebody puts between the digits. Six digits are a code of the
application; anything else is read as a backup code.

| Rule | What it refuses |
|---|---|
| The login is held for five minutes | A code typed later. The password is asked again, before any code is read |
| Five codes per person in a sliding window of one minute, counted with the user codes they get wrong on the device page | The sixth, before the secret is even opened. An attempt is counted once the secret is open, so a key management service that does not answer costs the person nothing |
| A code is accepted once, and the accepted step only moves forward | A code already accepted, and the code of an earlier step after a later one was accepted (RFC 6238 §5.2), whatever the drift |
| The window | A code of no step of the window |
| A disabled account | Its code, after the code was checked, so the refusal costs what a wrong code costs |
| A person of a federated domain | Any code, before it is read |

A code accepted writes the act `totp.used`, or `backup_code.used` for a backup code, and once the form token of
the page holds, the session opens on `pwd` and `otp`, both dated when the code was accepted. Every refusal of a
code is written as a refused login with its reason, and the page never says that reason: it says that the code,
or the backup code, was refused, by the shape of what was typed, and too many codes tried is the one reason it
names. A post with no code, or from a browser with no login waiting, is refused before any of it and writes
nothing. When the key management service does not open the secret, the page answers `503` with a `Retry-After`
of ten seconds, and nothing is counted.

## Removing it

On the page of the second factor, a person removes the application with a proof made in the last five minutes:
the TOTP is revoked, its row stays, its backup codes stop working with it, and the password alone signs them in
again where the floor of the tenant is `single_factor`; under `two_factors`, a password alone is under the floor
and opens nothing. The sessions it completed are left as they are. An operator revokes it with
`beffroi:user:revoke-credential`, and raising the floor of the tenant to one that reads no `otp` forgets it, row
and secret.
