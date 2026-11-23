---
title: Allowed applications
description: The page where an application asks for your agreement, what you agree to, the list of the applications you allowed, and what taking an agreement back does.
---

# Allowed applications

An application that wants to obtain something about you asks for your agreement on the sign-in pages. What you
agree to is recorded, and **Allowed applications** lists it, one line per application, with the way to take it back.

## When an application asks

The page **Authorise** followed by the name of the application appears after you sign in:

- the first time the application asks for something about you;
- each time it asks for more than you agreed to before;
- each time it asks you again on purpose.

It does not appear when the application asks for no more than you already agreed to. An application your
organisation declared as one of its own may be set never to ask.

The page shows the logo of the application when it has one, **You are signed in as** with your username, and
**asks for access to:** after the name of the application, followed by the list of what it asks for:

| On the list | What the application obtains |
|---|---|
| **Your identifier** | The identifier it knows you by |
| **Your profile: name, picture, language** | The details of your profile on [Your information](information.md) |
| **Your email address** | Your email address |
| **Your postal address** | Your postal address |
| **Your phone number** | Your phone number |
| **Access while you are away, until you revoke it** | The right to keep its access without you signing in again, until you take it back |

An application can also ask for one detail by its name, such as **Date of birth**, and for other things, listed
after **also asks to:**. Links under the list open, in a new tab, the pages the application gave about itself: for
an application named Billing, **How Billing uses your data**, **Billing terms of service** and **Billing website**.
A logo or a link only the application itself vouches for is shown only when it is on the site the application sends
you back to.

- **Allow** records your agreement and takes you on to the application. Agreeing to a new request adds what it
  asked to what you had agreed to before.
- **Deny** takes you back to the application, which is told you refused. No agreement is recorded.

Approving a [device](requests.md#connecting-a-device) or a [request waiting for you](requests.md#requests-waiting-for-you)
records an agreement in the same way.

## The list

**Allowed applications** says **Revoking an application's access makes it ask for your permission again.** Its
table has one line per application:

| Column | What it says |
|---|---|
| **Application** | Its name, which opens its own page |
| **Access** | Everything you agreed to let it obtain |
| **Allowed on** | When you last agreed |

**No application allowed.** means no application holds an agreement of yours.

## The page of an application

- **What you agreed to**: the **Access** and the date it was **Allowed on**.
- **Its current access**: **It can extend its access without you.** when it holds the means to renew its access on
  its own, followed by **Last access issued:** and the date it was last given them, or **It cannot extend its
  access.**
- **What it is waiting for**: **It is waiting for nothing from you.**, or the requests it made that wait for your
  answer, with **See pending requests**.

## Taking it back

Press **Revoke access** on the list, or beside the title of the page of the application, where **Its current access**
says **It will ask for your permission again next time.**

The application can no longer extend its access, and what the sign-in service gave it on the strength of your
agreement is withdrawn. The requests it made that wait for your answer are withdrawn too, and leave [Pending
requests](requests.md). As the page says, **Access already issued stays valid until it expires, even if you revoke
it.** The next time the application asks, the page **Authorise** asks you again.

Agreeing and taking back are both listed in [Account activity](activity.md), as **Application allowed** and
**Application access revoked**.
