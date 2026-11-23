---
title: Account activity
description: What the activity page of your account lists, how an administrator of your organisation appears in it, and what to do about a line you do not recognise.
---

# Account activity

**Account activity** lists what happened to your account, newest first: the sign-ins, the attempts that were
refused, the changes, and what an administrator of your organisation looked at or changed. It says **If you do not
recognise a line, change your password.**

On the home of your account, its card counts the refused attempts among your last twenty attempts to sign in.

## What each line says

| Column | What it says |
|---|---|
| **Event** | What happened |
| **Date** | When it happened |
| **From** | Where it came from: the place when it is known, or **Place unknown**, the address, and the browser and its system. For what an administrator of your organisation did, **An administrator of your organisation** |

The fields above the table narrow it: an **Event**, **From** with **A browser or an application** or **An
administrator of your organisation**, and the dates under **Date**.

## What it lists

| Kind | The events |
|---|---|
| Signing in | **Signed in**, **Sign-in refused**, **Password accepted**, **Passkey used**, **Authenticator code accepted**, **Backup code used**, **Session ended** |
| Ways of signing in | **Way of signing in added**, **Way of signing in removed**, **Way of signing in renamed**, **Way of signing in deleted, as no longer allowed**, **Password changed**, **Backup codes renewed**, **Passkey set-up link issued**, **New password link issued**, **Authenticator app set-up link issued** |
| Your account | **Account created**, **Account created through your organisation**, **Information changed**, **Account disabled**, **Account enabled again**, **Added to a group**, **Taken out of a group**, **Notification channels changed**, **Confirmation code sent**, **Address confirmed** |
| Applications | **Application allowed**, **Application access revoked** |
| Your data | **Copy of your data requested**, **Copy of your data downloaded**, **Copy of your data deleted** |
| What an administrator looked at | **Account viewed**, **Sessions viewed**, **Group membership viewed**, **Allowed applications viewed**, **Account activity viewed** |

**Way of signing in deleted, as no longer allowed** means your organisation stopped allowing a way you held, such as
a password where it now asks for passkeys only.

An administrator of your organisation is never named, nor where they acted from. Lines are kept for a period your
organisation sets, then deleted.

## A line you do not recognise

A **Sign-in refused** alone means a sign-in as you failed, which a mistyped password of yours does too. A
**Signed in**, a change or a new way of signing in you did not make means somebody may hold a way into your
account. Then:

1. [Change your password](password.md), if you have one.
2. End the sessions you do not recognise on [Open sessions](sessions.md).
3. Revoke the passkeys you do not recognise on [Your passkeys](passkeys.md). If a code of your authenticator app or a
   backup code was used without you, [generate new backup codes](two-factor.md#generating-new-ones), or remove the
   app and set it up again.
4. Revoke the applications you did not allow on [Allowed applications](applications.md).
5. Tell your organisation.
