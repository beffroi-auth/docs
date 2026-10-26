---
title: Credentials
description: Several per person, each of a kind of its own, each declaring what it can do and what it proves.
---

# Credentials

A person holds credentials, not a password: a password, passkeys and a TOTP with its backup codes can exist at
the same time. Each kind is a class of its own, which names itself and declares what it can do by the interfaces
it implements, so a credential that can be revoked and one that completes a password are told apart by their
type and never by a `match` on a string.

## The kinds

| Kind | Per person | Proves | Taken out of use | Page |
|---|---|---|---|---|
| `password` | One | `pwd` | Replaced, never revoked, or forgotten by the floor of the tenant | [Passwords](passwords.md) |
| `passkey` | Several | `hwk` or `swk`, and `user` | Revoked, or forgotten by the floor of the tenant | [Passkeys](passkeys.md) |
| `totp` | One active | `otp`, a code or a backup code alike | Revoked, or forgotten by the floor of the tenant | [TOTP](totp.md) |

[Backup codes](backup-codes.md) are not a kind: they are held by the TOTP credential they stand in for, ten of
them, and a renewal replaces the set.

Every credential holds its identifier, the person and the tenant it belongs to, when it was created and when it
was last used, and each kind keeps what makes it that kind in a table of its own: a hash for a password, a
public key and its counters for a passkey, a sealed secret and hashed codes for a TOTP. The provider holds
nothing a credential could be presented with: a hash does not open, a passkey's private key never leaves the
authenticator, and the secret of a TOTP is an envelope only the key management service of the tenant opens.

## What a kind declares

| Interface | What it says | Kinds |
|---|---|---|
| `ProvingCredentialInterface` | What one authentication with it may prove, as `amr` values (RFC 8176 §2), nothing for a revoked one | `password`, `passkey`, `totp` |
| `RevocableCredentialInterface` | It can be taken out of use and keep its row | `passkey`, `totp` |
| `SecondFactorCredentialInterface` | It completes a password rather than replacing it: while one is active, a password alone signs nobody in | `totp` |
| `NameableCredentialInterface` | Its holder names it, and renames it | `passkey` |
| `ExternallyIdentifiedCredentialInterface` | A party presents it by an identifier of its own before anything is verified, unique in the tenant | `passkey`, by its credential ID |

What a person can still prove, and so which class a [step-up](../authentication-sessions.md#proving-again) may
reach for them, is read credential by credential from `ProvingCredentialInterface`, never from a kind.

## What the floor of the tenant admits

The [floor of the logins](../tenants.md#the-floor-of-its-logins) of a tenant admits a credential when it reads at
least one of the methods that credential proves. A credential it does not admit is not offered at the login,
cannot be enrolled, and is forgotten, row and secret, when the floor is raised.

| Floor | Password | Passkey | TOTP and backup codes |
|---|---|---|---|
| `single_factor` | Admitted | Admitted | Admitted |
| `two_factors` | Admitted | Admitted | Admitted |
| `phishing_resistant` | Not admitted | Admitted | Not admitted |
| `phishing_resistant_hardware` | Not admitted | A passkey bound to its authenticator only | Not admitted |

A person whose address is of a domain an [upstream identity provider](../../saml/federated-sign-in.md) answers
for is posed no local credential at all, whatever the floor, and a credential they held before their domain was
federated signs them in no more.

## Revoked and forgotten

**A revoked credential keeps its row.** It never authenticates again, it stays listed with the date it was revoked
in `beffroi:user:show` and in the archive of the person, and a revoked passkey on the page of the passkeys too,
where a revoked TOTP leaves the page of the second factor. The first revocation wins: revoking it again changes
nothing and announces nothing. A person revokes their own on [the pages of their
account](../../symfony-bundle/account.md#taking-it-back), and an operator any of them:

``` bash
bin/console beffroi:user:revoke-credential alice 0199f1c2-7b3a-7c4d-9e5f-1a2b3c4d5e6f
```

The identifier is the one `beffroi:user:show` lists. A password is refused there, a password being replaced and
never revoked. What happens to the sessions a credential opened is the caller's: revoking a passkey or a TOTP
leaves them as they are.

**A forgotten credential keeps nothing.** Raising the floor of a tenant forgets every credential the floor does
not admit, its row and its secret, and a credential revoked earlier, which proves nothing any more, is left
where it was. The act, `credential.forgotten`, stays in the journal of the person, and it is the only trace left.

## Where a person reads them

The pages of the account show the password with the date its hash was last written, which a rehash moves as a
new password does, each passkey with its name, its dates and its state, and the authenticator application with
its dates and the number of backup codes left. The archive a
person asks for lists every credential with its kind, its identifier, its name, its credential ID when it has
one, and its dates, and never a hash, a secret or a public key.

## Adding a kind

A kind is a class that extends `Credential`, or `RevocableCredential` when it can be revoked, names itself in
`kind()` and implements the interfaces of what it can do, with a table of its own in the Doctrine mapping: the
store reads the kinds from the entities mapped under `Credential` and names none of them. For it to sign
anybody in, the firewall needs a login that proves it, a class tagged `beffroi.login`, which
[security](../../symfony-bundle/security.md) describes.
