---
title: Your data
description: Asking for the file that holds everything the sign-in service of your organisation knows about you, what it contains, downloading it, and when it is deleted.
---

# Your data

**Your data** gives you one file holding everything the sign-in service of your organisation knows about you. **All
your data in one file, ready a few minutes after you ask.**

## What the file holds

Under **What the file holds**, the page lists its parts:

- **Your account and your information**
- **Your ways of signing in, without their secrets**
- **Your linked accounts and what they shared**
- **Your groups and where each comes from**
- **Allowed applications and what each obtains**
- **Your open sessions**
- **Your account activity**
- **The history of changes to your information**
- **What each application obtained from you, and when**

The file is in JSON, a structured text format that programs read, so you can take your data elsewhere.

## Asking for it

Press **Ask for my data**, beside the title. Under **Your request**, the page then says where it has got to:

| The page says | What you can do |
|---|---|
| **You have not asked for your data yet.** | **Ask for my data** |
| **Your file is being prepared. Come back in a few minutes.** | Wait, or take the request back with **Delete this request** |
| **Your file is ready.** | Download it, delete it with **Delete this file**, or press **Ask for a new file** |
| **Your file could not be prepared. Ask for a new one.** | The file was not ready within a quarter of an hour. Press **Ask for a new file**, or **Delete this request** |
| **Your file has expired. Ask for a new one.** | Press **Ask for a new file** |

Until the file is ready, the page also says when you asked, **Asked for on**. Once it is ready, it says when it was
**Prepared on** and until when it is **Available until**.

You can ask for a file five times an hour. Beyond that, nothing is prepared, and the page says **Too many attempts.
Wait a moment, then try again.**

## Downloading it

- **Download your data** downloads the file as it was prepared.
- **Download encrypted** downloads it inside a ZIP archive locked by a passphrase you type in **Passphrase**, of at
  least 16 characters. **It is kept nowhere: lose it and the file cannot be opened.** Open the archive with 7-Zip or
  Keka. A passphrase that is too short is refused with **Passphrase too weak: use several words, at least 16
  characters.**

Each download is listed in [Account activity](activity.md) as **Copy of your data downloaded**.

## When it is deleted

**A file is kept for 7 days, then deleted.** The seven days count from when you asked.

Asking for a new file deletes the previous one, so you hold one file at a time.

You do not have to wait: **Once you have downloaded the file, you can delete it without waiting for it to expire.**
Press **Delete this file**, and the sign-in service no longer holds it. **There is nothing left to delete.** means
it was deleted already.
