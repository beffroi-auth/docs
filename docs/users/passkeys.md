---
title: Your passkeys
description: Adding a passkey to your account, naming it, reading what the list says of it, revoking it, and adding a first one from a link your organisation sends you.
---

# Your passkeys

A passkey signs you in with your device, without a password. It is kept by your phone, your computer, your
password manager or a security key, which asks you to confirm each time it is used, and nothing your account holds
could sign in in its place. You can hold as many as you like, one per device for example.

**Your passkeys** lists them. The page opens only when you signed in less than five minutes ago; otherwise the
sign-in page comes first.

## Adding one

Press **Add a passkey**, beside the title. Your browser asks your device to create the passkey and to confirm it is
you. The new passkey is listed under the name **New passkey**: type the name you want in its line, such as the name
of the device, and press **Rename**. A name is 1 to 255 characters.

The button is shown only in a browser that can create a passkey. Another browser shows **This browser cannot create
a passkey.**

| The page says | What it means |
|---|---|
| **The passkey could not be created. Try again.** | Your browser or your device did not complete it. Try again, or use another device |
| **Adding the passkey timed out. Try again.** | The sign-in service was no longer waiting for this passkey. Press **Add a passkey** again |
| **This passkey was refused. Try another one.** | The sign-in service does not accept this passkey, for example one your account already holds, or one your organisation's rules do not allow |
| **Only the keys your organisation gave you are accepted.** | Your organisation accepts only the security keys it hands out. Use one of those |
| **This model is under a security alert and is no longer accepted. Use another one.** | That model of device was found to be unsafe. Use another one |
| **Give the passkey a name of 1 to 255 characters.** | The name was empty or too long |

Adding a passkey is [told to you](notifications.md) and listed in [Account activity](activity.md) as **Way of
signing in added**.

## What the list shows

| Column | What it says |
|---|---|
| **Name** | The name you gave it |
| **Authenticator** | The make and model of the device, when they are known, with its certification, or **Unknown authenticator**. Then how far the model was checked: **Declared model, not verified**, **Verified model**, or **Your organisation's key** with its **Serial number**. **Model under a security alert** marks a model your organisation still accepts although it was found unsafe |
| **Features** | **Device-bound** for a passkey that never leaves its device, **Synced** for one copied to your other devices, **Syncable, not backed up** for one that may be copied but was not yet. Then how it is reached: **Via** the device, a nearby phone, USB, NFC, Bluetooth or a smart card |
| **Created** | When it was added |
| **Last used** | When it last signed you in, or **Never** |
| **State** | **Active**, or **Revoked on** a date |

The list shows the active passkeys. To see the revoked ones, choose **Revoked** or **All** under **State** above the
table and press **Filter**.

## Revoking one

Press **Revoke** in its line. The passkey never signs you in again, and moves from the active passkeys to the
revoked ones, with the date. Revoke a passkey as soon as you lose the device that holds it.

Revoking a passkey leaves open the sessions it opened: end them on [Open sessions](sessions.md). It is told to you,
and listed in [Account activity](activity.md) as **Way of signing in removed**.

## A first passkey from a link

Your organisation can send you a link that adds a passkey to your account without signing in, for example when you
have nothing to sign in with yet, or lost the device that held your passkey.

The link opens the page **Add a passkey**, which names your account and says **This link works only once.** Press
**Add my passkey**, and your device creates the passkey. Once it is added, the page takes you to your account: sign
in with the new passkey if that browser is not signed in yet. The link itself signs you in to nothing.

- A browser that cannot create a passkey says **This browser cannot create a passkey. Open the link on another
  device.** Open it on the device that will hold the passkey.
- The link works once, within 72 hours. When your organisation issues a new one, the previous one stops working.
- A link that no longer works opens a page that says **This link was already used or has expired. Ask for a new
  one.** Ask your organisation.

Issuing such a link is told to you: **A link to add a passkey to your account was issued on** followed by the date.
If you did not expect it, contact your organisation.

## When your organisation signs you in

If you sign in through your organisation's own sign-in service, no passkey signs you in here, and the page says
**You sign in through your organisation: there is nothing to set up here.**
