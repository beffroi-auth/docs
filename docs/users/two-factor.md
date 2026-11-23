---
title: Two-factor authentication
description: Setting up an authenticator app so that a code follows your password, the ten backup codes that stand in for it, renewing them, and removing the app.
---

# Two-factor authentication

An authenticator app on your phone or your computer shows a new six-digit code every thirty seconds. Once you set
one up, your password alone no longer signs you in: the sign-in page asks for the code the app shows after it. A
passkey signs you in on its own, without a code.

**Two-factor authentication** opens only when you signed in less than five minutes ago; otherwise the sign-in page
comes first. What it says depends on your account:

- **No authenticator app. Once one is set up, its code is asked after your password.**, with **Set up an
  authenticator app** beside the title;
- **Authenticator app set up on** a date, with when it was **Last used** and how many **Backup codes** are left;
- **You sign in with a passkey: no authenticator app is needed.**, when your organisation signs its people in by
  passkey only;
- **You sign in through your organisation: there is nothing to set up here.**, when your organisation signs you in
  through its own sign-in service.

## Setting up the app

Press **Set up an authenticator app**. The page **Set up your authenticator app** has two steps.

1. **Give the key to your app**. **Scan this QR code with your authenticator app.** If your app cannot scan, **Or
   enter this key by hand:** the key is written under the code, and, where your browser allows it, **Copy the key**
   copies it.
2. **Confirm with the code it shows**. Type the code your app now shows under **Code shown by the app**, and press
   **Confirm**.

The page that follows, **Your backup codes**, says **Your authenticator app is set up. Its code will be asked after
your password.** and shows your ten backup codes.

| The page says | What to do |
|---|---|
| **Wrong code. Enter the code shown now.** | Type the code your app shows at this moment. The same QR code stays on the page, so there is nothing to scan again |
| **The set-up has expired. Start again.** | The set-up waits ten minutes for its code. Press **Set up an authenticator app** again, and replace the entry in your app |
| **An authenticator app is already set up. Remove it before setting up another one.** | Your account holds one app at a time |

Setting up the app is [told to you](notifications.md) and listed in [Account activity](activity.md) as **Way of
signing in added**.

## Your backup codes

Backup codes stand in for the app when you cannot reach it. **Keep these codes somewhere safe: they will not be
shown again. Each one replaces a code from the app once, if you lose it.** Where your browser allows it, **Copy them
all**, beside the title, copies the ten of them; if copying fails, the page says **Copying failed. Select the codes
and copy them.**

A code is ten letters and digits, written as two groups of five. On the page **Enter your code**, type one instead
of the code of your app: with or without the hyphen, in capitals or not. Each code works once.

When the last one is used, nothing else changes: the app goes on signing you in, and the page says **No backup code
left**. Generate new ones then.

### Generating new ones

Press **Generate new backup codes**, beside the title. The page **Your new backup codes** says **Your previous codes
no longer work.** and shows ten new ones, once. Do it when your list is spent, lost or seen by somebody else.

Generating new codes is told to you and listed in [Account activity](activity.md) as **Backup codes renewed**.

## Removing the app

Press **Remove the authenticator app**. The app stops working for your account, and its backup codes with it. Your
password alone signs you in again, unless your organisation asks for a second step at every sign-in: then your
password alone no longer opens anything. Set up another app while you are still signed in, or sign in with a
passkey from then on.

The sessions the app helped open stay open: end them on [Open sessions](sessions.md) if you need to. Removing the
app is told to you and listed in [Account activity](activity.md) as **Way of signing in removed**.

## If you lost the app

Sign in with your password and a backup code, then remove the app and set up the new one. A passkey signs you in as
well.

When you cannot sign in at all, your organisation can send you a link that sets up a new app in place of the old
one. It opens the page **Set up a new authenticator app**, which names your account, says **This link works only
once.** and warns **The previous app will stop working and all your sessions will end.** The two steps are the same
as above. Once the code is confirmed, the page **Your backup codes** says **Your new authenticator app is set up and
your sessions have ended.**, shows your ten backup codes once, and offers **Sign in**.

The link works once, within 72 hours, and a new one makes the previous one stop working. A link that no longer
works opens a page that says **This link was already used or has expired. Ask for a new one.**
