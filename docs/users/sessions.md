---
title: Open sessions
description: The browsers signed in to your account, what each line says, and how to sign one of them out, or every one but yours.
---

# Open sessions

Signing in on a browser that is not signed in yet opens a session. It lasts twelve hours at most from that sign-in,
and it is what lets the applications of your organisation sign you in without asking again on that browser. **Open
sessions** lists the sessions of your account that are open at this moment, and says **Ending a session signs you
out of every application it was used for.**

## What each line says

| Column | What it says |
|---|---|
| **Method** | How you proved who you are in that session, in short codes, for example `pwd` for a password, `otp` for a code of your authenticator app or a backup code, `hwk` or `swk` for a passkey, `fed` for a sign-in through your organisation. Your organisation's name for the level the session reaches comes first |
| **Opened** | When the session opened |
| **Last active** | When you last signed in within that session |
| **From** | Where that last sign-in came from: the place when it is known, or **Place unknown**, the address, and the browser and its system |

The line of the browser you are reading the page on says **this browser**.

## Ending a session

- **End**, in the line of another session, signs that browser out at once, without asking for your password first.
- **End and sign out**, in the line of this browser, ends your own session and signs you out, as [signing
  out](signing-in.md#signing-out) does.
- **End every other session**, beside the title, ends every session but the one of this browser. It is offered when
  more than one session is open.

What the applications were given under an ended session is withdrawn, and those that can be told are told.
[Allowed applications](applications.md) says what remains valid until it expires.

Some changes end sessions on their own: changing your password ends every session but the one you changed it from,
and a new password or a new authenticator app set up from a link your organisation sent ends every session of your
account. Revoking a passkey or removing your authenticator app ends none: end here the sessions they opened if you
need to.

## A session you do not recognise

End it, then [change your password](password.md) if you have one, and look at [Account activity](activity.md) for
what was done. If you cannot explain it, tell your organisation.
