---
title: Signing in
description: What the sign-in pages ask, what they answer when something is refused, how long you stay signed in, and how to sign out.
---

# Signing in

An application of your organisation that needs to know who you are sends you to the sign-in pages. The page
**Sign in** says **Sign in to continue to** followed by the name of that application, or **Sign in to continue.**
when you opened your account yourself.

## With a password

Type your **Username** and your **Password**, then press **Sign in**.

If the sign-in is refused, the page says **Wrong username or password.**, whatever the reason, so that it never
tells anybody whether an account exists. After five wrong passwords within a minute, the next attempts are refused,
even with the right password: wait a minute, then try again.

## With a passkey

In a browser that can use passkeys, the page shows **Use a passkey**: press it, and your device asks you to
confirm. The **Username** field can also offer the passkeys your browser holds as you click into it. A passkey
signs you in on its own: no code is asked after it.

When your organisation signs its people in by passkey only, the page says **Sign in with your passkey.** and
shows no password field. [Your passkeys](passkeys.md) says how to add one.

If your device cannot complete the passkey, the page says **The passkey did not work. Try again.** A passkey the
sign-in service refuses is answered like a password, **Wrong username or password.**

## The second step: a code

If you set up an [authenticator app](two-factor.md), your password is followed by the page **Enter your code**:
**Enter the code from your authenticator app or a backup code.** Type the six digits your app shows, or one of
your backup codes, then press **Continue**. Spaces do not matter.

| The page says | What to do |
|---|---|
| **Wrong code. Enter the code shown now.** | Type the code your app shows at this moment. A code works once: to sign in twice in a row, wait for the next one |
| **This backup code is wrong or already used.** | Each backup code works once. Type another one |
| **Too many attempts. Wait a moment, then try again.** | Too many codes were tried within a minute. Wait a minute, then try again |

You have five minutes to type the code. After that, the page asks for your password again.

## With your organisation's own sign-in

When your organisation signs some of its people in through a sign-in service of its own, the first page asks for
your **Email address** and nothing else. Press **Continue**:

- an address of a domain your organisation signs in that way takes you to its sign-in page, and you come back
  signed in;
- any other address, or a username, takes you to the usual page, where **Use another address** takes you back.

**This address is not valid.** means the address could not be read: check what you typed. If the sign-in at your
organisation fails, the page says **The sign-in with your organisation did not go through. Start again from the
application.**

People who sign in that way cannot sign in here with a password, a passkey or an authenticator app. **Your
password**, **Your passkeys** and **Two-factor authentication** say **You sign in through your organisation: there
is nothing to set up here.**

## When the page asks again

You are sometimes asked to sign in although you already are:

- **Sign in again to continue.** An application asked you to prove again who you are.
- **A stronger sign-in is required.**, or the name of an application followed by **requires a stronger sign-in.**
  The page then names, among the ways you hold, those that will do: **A passkey will do.**, **Your password will
  do.** or **Your password followed by a code from your authenticator app will do.**
- **Sign in to continue.** on the way to **Your password**, **Your passkeys**, **Two-factor authentication** or
  **Encrypted email**. These pages change how you sign in or who can read the email sent to you, so they open only
  when you proved who you are less than five minutes ago. Sign in with any way you hold, and the page opens.

If your organisation checks passwords against lists of passwords published after a data breach and finds yours,
the pages take you to **Your password** first each time you sign in to your account, and on the way to some
applications, until you change it. [Your password](password.md#a-password-found-in-a-data-breach) says what to do.

## How long you stay signed in

A sign-in lasts at most twelve hours on that browser, counted from when you signed in, and signing in again during
those hours does not extend them. A sign-in through your organisation's own sign-in service can end sooner, when that
service says so. Until then, the other applications of your organisation can sign you in without asking again,
unless one of them asks you to prove again who you are.

[Open sessions](sessions.md) lists the browsers signed in to your account.

## Language and theme

The pages are written in the language your browser prefers, among those your organisation offers. When it offers
more than one, a control at the top of the page shows the name of the current language and lists the languages
offered: the one you choose is kept in that browser for a year, and comes before what an application suggests.

Once you are signed in, and your account names one of those languages under **Language** on [Your
information](information.md), the pages of your account are written in it and the control is not shown. While your
account names none, choosing one in the control also writes it to your account, unless your organisation fills
that detail for you.

The theme control, at the top of the page as well, offers **Light**, **Dark** and **System**, which follows your
device. The choice is kept in that browser for a year.

## Signing out

On a page of your account, open the menu under your username and choose **Sign out**. The page **Sign out** names
the account you are signed in with and asks whether you want to sign out: **Sign out** or **Stay signed in**.

- **Sign out** ends your session, which signs you out of every application it was used for. The page then says
  **You are signed out** and **You can close this window.** When some applications are told through your
  browser, the page is **Signing you out of your applications** instead, and says **Your applications were asked
  to sign you out. Those your browser blocks will do so on your next visit.**
- **Stay signed in** changes nothing, and the page says **You are still signed in**.

An application can send you to the same page to sign you out; the page then names it.

## When a page cannot continue

A page titled **Unable to continue** says why, such as **This request has expired. Start again from the
application.** Go back to the application and start again from there.
