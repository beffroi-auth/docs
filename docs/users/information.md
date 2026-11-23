---
title: Your information
description: What your account holds about you, what you can correct, the history of the changes, confirming an email address or a phone number, and encrypting the email sent to you.
---

# Your information

**Your information** shows what the sign-in service of your organisation holds about you, and lets you correct
what your organisation opens to you. **Change history**, beside the title, lists what changed and who changed it.

## What the page shows

The page shows what your account holds in two parts.

- **Your account**: your **Username**, when the account was created, **Account created**, and when it last changed,
  **Last change**. Nobody changes these here.
- **About you**: one line per detail, such as **Email address**, **Phone number**, **Full name**, **Given name**,
  **Family name**, **Date of birth**, **Language**, **Time zone** or **Postal address**. An email address and a phone
  number say whether they were confirmed: **verified** or **not verified**. **Nothing yet.** means your account
  holds no detail about you.

## Correcting a detail

Your organisation decides which details you may correct. They can include your names, **Nickname**, **Preferred
username**, **Date of birth**, **Gender**, **Language**, **Time zone**, **Profile page**, **Picture**, **Website**
and **Phone number**. Your username, your email address and your postal address are never changed here; ask your
organisation. When you sign in through your organisation's own sign-in service, the details it fills cannot be
changed here either: they follow what your organisation holds.

A detail you may correct is a field. Type in it, and press **Save**, which appears beside the field while you point
at it or type in it. **Empty a field to remove it.** **Date of birth** takes a full date; when your account holds
only the year, the field takes text instead, written like **1815-12-10, or 1815**. A value the field does not accept
is answered **This value is not valid.**

When there is nothing you may correct, the page says **This information cannot be changed here.**

What you choose under **Language** is the language of the pages of your account and of the messages sent to you.
**Time zone** is the zone every date of your account is written in.

## Change history

**Change history** lists, for each change: the **Detail**, what it said **Before**, what it says **After**, **When**
it changed, and **By**: **You**, or **An administrator of your organisation**, who is never named. **No change yet.**
means nothing changed. Changes are kept for a period your organisation sets.

## Confirming an email address or a phone number

An email address or a phone number that is **not verified** receives no [notification](notifications.md) from the
sign-in service. When your organisation can send you email or text messages, the page lists such addresses under
**Addresses to confirm**, with **Until an address is confirmed, it receives only its confirmation code.** and **Send
a code** beside each.

1. Press **Send a code**. The page **Confirm your email address**, or **Confirm your phone number**, says **A code
   was sent to** the address, **Enter it here or open the link that came with it.**
2. The message says **Your confirmation code:** followed by six digits and the moment it stops being valid. Type the
   code under **Code** and press **Confirm**. Or open the link in the message: its page says **Confirm that this
   address is yours.**, and **Confirm this address** confirms it. The link needs you signed in on that browser.
3. The address is then marked **verified**.

A code sent by email is valid for 24 hours, a code sent by text message for 10 minutes. Five wrong codes end it, and
**Send another code** replaces it with a new one. If you did not ask for a code, ignore the message.

| The page says | What to do |
|---|---|
| **Wrong or expired code. Check it or ask for another one.** | Check the code, or press **Send another code** |
| **This link was already used, has expired or was replaced. Send a new code from your account.** | Press **Send a code** on **Your information** again |

A phone number you correct yourself is **not verified** until you confirm it.

## Encrypted email

Beside an email address that is **verified**, **Encrypted email** opens the page where you give an S/MIME
certificate or an OpenPGP public key: the email the sign-in service sends you is then encrypted to it. The page
opens only when you signed in less than five minutes ago; otherwise the sign-in page comes first.

The page says **Emails sent to** your address **can be encrypted to your S/MIME certificate or OpenPGP key, which
must carry this address. The sender, recipient, date and subject stay readable.**

Choose the **Format**, **S/MIME** or **OpenPGP**, paste the **Certificate or public key**, and press **Encrypt my
emails**: **S/MIME: the certificate alone, in PEM. OpenPGP: the public key alone, ASCII-armoured. Replaces the
previous one.** The page then says **Your emails are encrypted with** the format **to the key** and its fingerprint,
followed by **An email that cannot be encrypted is not sent.** and, when the key has an end, **Valid until** its
date. **Stop encrypting my emails** takes it away.

| The page says | What to do |
|---|---|
| **This certificate or public key cannot be read.** | Paste the certificate or the key alone, in the form the format asks for |
| **This certificate or key cannot encrypt: it needs an RSA key of at least 2048 bits (S/MIME) or an encryption subkey (OpenPGP).** | Give a certificate or a key made for encryption |
| **This certificate or key has expired, is revoked or is not valid yet.** | Give one that is valid today |
| **This certificate or key does not carry your verified address.** | Give one made for the address shown on the page |
| **Encryption needs a verified email address, and your account has none.** | Confirm your email address first |

The email that carries a confirmation code is never encrypted.
