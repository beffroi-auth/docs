---
title: Notifications
description: What the sign-in service tells you about, the browsers, email and text messages it reaches you by, and how to choose them.
---

# Notifications

The sign-in service of your organisation tells you of two things:

- **Request to approve**: a request waits for your answer on [Pending requests](requests.md);
- **Change to how you sign in**: a passkey or an authenticator app was added to your account or removed from it, a
  password was set or changed, a link to add a passkey to your account was issued, or your backup codes were
  renewed. You are told whoever made the change, you included.

It reaches you by the channels your organisation offers, among **Browsers**, **Email** and **Text message**. An email
goes only to an email address that is verified, and a text only to a phone number that is verified: [Your
information](information.md#confirming-an-email-address-or-a-phone-number) says how to confirm them. Messages are
written in the **Language** of your account, or in the language your organisation uses by default.

**Notifications** is where you add the browsers that receive them, and choose the channels.

## What a message says

A request names the application and what it asks you to approve, then says **Open your account to answer.** Email
and text messages add the address of **Pending requests**. Nothing in a message answers a request: you answer on
your account, signed in.

A change says what changed and when, for example **A passkey was added to your account on** followed by the date,
then **If it was not you, open your account**, followed by **and contact** and the contact of your organisation when
it gave one. Email and text messages add the address of your account. In an email, the subject is the name of your
organisation followed by **a change to how you sign in**.

If you did not make the change: look at [Account activity](activity.md), end the sessions you do not recognise on
[Open sessions](sessions.md), and contact your organisation.

## A message that could not be delivered

A channel that cannot deliver the message of a change tries again for a while. When it gives up, [Account
activity](activity.md) lists **Change notification not delivered**, and the pages tell you once, after you sign in:
**A change to how you sign in could not be notified to you. If it was not you, check your account activity.**

- On the way to some applications, the page **A change could not be notified** comes right after you sign in. Its
  link **Account activity** opens, in a new tab, the lines **Change notification not delivered**, and **Continue**
  takes you on to the application.
- **Your account** says it above its cards, with the same link.

## Browsers

Your organisation may let the sign-in service show notifications in your browsers. **A browser added here gets a
notification when a request waits for your answer and when how you sign in changes. You always answer here.**

1. Open **Notifications** in the browser you want to add, and press **Add this browser**.
2. Your browser asks whether the page may show notifications: allow it.
3. The browser is listed as **New browser**. Type the name you want in its line, and press **Rename**.

Your account keeps ten browsers at most: adding an eleventh removes the one added longest ago.

A notification shows the name of your organisation and the message. Clicking it opens **Pending requests** for a
request, and the home of your account for a change.

| Column | What it says |
|---|---|
| **Browser** | The name you gave it. The browser you are reading the page on says **This browser** |
| **Added** | When it was added |
| **Last notified** | When it last received a notification, or **Never** |

**Remove** stops notifications to that browser.

| The page says | What it means |
|---|---|
| **The browser was not added. Check that notifications are allowed.** | Check in the settings of your browser that this site may show notifications, then try again |
| **This browser sent an invalid subscription. Try again.** | Press **Add this browser** again |
| **This browser does not support notifications.** | Use another browser |
| **Browser notifications are not available.** | Your organisation does not send notifications to browsers |
| **Give the browser a name of 1 to 255 characters.** | The name was empty, too long, or held a line break, a control character or an invisible formatting character other than the joiners some scripts need |

## Choosing the channels

The table under **Channels** has one column per channel your organisation offers. **Choose the default channels, or
customise them for one notification. An email or a text goes only to a verified address or number.**

- **Default**: tick the channels you want.
- **Request to approve** follows the **Default channels**, unless you tick **Customise** in its line and choose its
  own.
- **Change to how you sign in** says **Always sent on every channel.** It cannot be turned off.

Press **Save**. Until you save a choice, every channel is ticked. **No notification channel is available.** means
your organisation offers none; requests still wait for you on [Pending requests](requests.md).

The choice is listed in [Account activity](activity.md) as **Notification channels changed**.
