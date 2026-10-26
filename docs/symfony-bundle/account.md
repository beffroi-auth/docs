---
title: The account pages
description: What a person reads of themselves, what they can take back, and what a page asks before it opens.
---

# The account pages

A person signs in at the issuer, reads what the provider holds of them, and takes any of it back without
asking an administrator. The same facts are available to an operator through
[the console](console-commands.md), and the two read the same code.

None of these pages belongs to a client or to an authorization request. They are reached by typing the
issuer in a browser, and the home of the account is where they hang from: every other page carries the
link back to it, and nothing else.

## The pages

The home is a card per page, in this order, each card carrying what the account holds there. The
titles below are the ones the English catalogue carries.

| Page | Path | What is on it |
|---|---|---|
| Requests waiting for you | `/account/approvals` | What somebody is waiting on an answer for right now. It is first because every other card says what the account holds and this one says that a request is open |
| Your information | `/account/profile` | What the provider holds of this person: the name they sign in with, the two dates of the record, and one line per claim of OIDC Core §5.1 |
| Your passkeys | `/account/passkeys` | Their passkeys, with the name each one was given, its dates and its state |
| Two-factor authentication | `/account/two-factor` | The authenticator application, when there is one, and how many backup codes are left |
| Applications you have allowed | `/account/consents` | One line per client in force, with the scopes it holds, and a page per application behind it |
| Where you are signed in | `/account/sessions` | Where this person is signed in at this moment, what each session proved, and where it was last seen |
| Your password | `/account/password` | When the password was last written, and the form that replaces it |
| What happened to your account | `/account/acts` | What the journal holds of the account: who signed in as them and with what, the attempts that were refused, what signed out, what changed of the means of signing in and what they did of their own record. Its card counts the refused attempts the journal holds, twenty at most, since a failure is what somebody comes to look for |
| Notifications | `/account/notifications` | The browsers this provider can reach by web push |
| Your data | `/account/archive` | The one file holding everything the provider knows of them, and where their last request for it has got to |

The subject identifier clients know this person by is on none of them. It is the `sub` of a token, not
something a person comes to read of themselves, and a client of a sector that asked for a pairwise
identifier is given a different one, so a page naming one of them would be saying something false.

[:beffroi-arrow-right: Every route, with the one each form posts to](../reference/endpoints.md)

### What a person may change of themselves

The information page is one line per claim this provider can hold, read where it is held and written where
the tenant opens it: the same thing is not read in one list and offered in another, so the line somebody
corrects is the line they were reading. What the tenant opens is `tenant.self_served_claims`, a rule of
the tenant and never an option of the deployment, and a tenant that opens none of them serves a page that
only reads.

A claim says what field it is, which is what the page renders: the kind its input carries, the whole set
when the set is closed, and the pattern or the length when it is not. A closed set is closed on the server
too, for whatever that page posts and not only in its field, and a birthdate that has not the shape of one,
a year or a year, a month and a day, is refused rather than stored. What those lines said before, and when
they changed, is at `/account/profile/changes`.

### What the password page says

Besides the date the password was last written and the form that replaces it, the password page is where a
person is told something rather than asked: a password already in use that a list of compromised values
was later found to hold. The lookup happens after a login, on a lane, at most once a month per person, so
no sign-in waits on somebody else's service, and the answer outlives the request that noticed it.

So the person is not left to find it: the next login that serves no authorization request sends them to this
page, which says why, before the page they were going to, and asks again at every such login until the
password is replaced. A login that answers an authorization request of OpenID Connect is not diverted; the
logins a page of the provider asks for are, the pages of the account, the approval of a device or of a
backchannel request, and the single sign-on of a SAML service provider among them.

A password posed here is typed twice and the two are compared in constant time, and the counter beside the
field is local to the browser: what the page says of a password as it is typed asks nobody anything, and a
password is never sent anywhere to be scored. The length it asks for is the one the floor of the tenant
sets, fifteen characters or eight, and the field and the core read the same number.

[:beffroi-arrow-right: Passwords](../core/credentials/passwords.md)

### A person of an organisation

A person whose address is of a domain an [upstream identity provider](../saml/federated-sign-in.md) answers
for signs in at their organisation and nowhere else. The pages of their account offer no form that would pose
a password, a passkey or an authenticator application, and say so: their organisation signs them in, no
password, passkey or authenticator application of this account signs them in, and none is added to it. A form
posted by hand is refused all the same, and what the source of their account holds of their profile is read
there and not changed.

## What a page asks before it opens

A page of the account needs the session this browser holds, and the form token when it posts. Without the
session it refuses with `login_required`, and the refusal offers the home of the account, which is the one
page of the plane that sends a browser to the login and brings it back: there is nowhere else to send it,
a page of the account belonging to no client and to no interaction.

A session outlives the moment it was opened, by construction: a person signs in once and reads their
account for the rest of the day, and so does whoever sits down in front of a screen left unlocked. That is
the right trade for a page that shows what the account holds, and the wrong one for the gesture somebody
else would lock its owner out with, so **a page that adds or takes away a way in asks for the proof
again** when the newest proof of the session is more than five minutes old. A step-up or a login made again
in that session counts as a proof like the first one.

=== "Asks for a recent proof"

    The password page and the form that replaces it, the passkeys page, the enrolment of a passkey and its
    revocation, the second factor page, its enrolment, its revocation and the renewal of its backup codes.

    The proof is asked for by the login of the firewall, the one every other page of the provider uses, so
    what this person holds is what proves them again: a password, a passkey or a code. Nothing here asks
    for a kind, which would be a page deciding what a credential is worth in place of the tenant's policy.

=== "Reached on the session alone"

    Everything that reads, plus ending a session, closing every other session, renaming a passkey and the
    options of a ceremony.

    Ending a session is not taking away a way in: a session is closed because it is feared, and asking for
    a password first would be asking somebody to type it on the browser they are worried about. It is the
    one gesture of these pages that can only ever put an attacker outside.

Which pages ask is declared by the pages themselves, and the rule is applied before the controller runs,
so it bounds the `GET` and the `POST` of a page alike: a guard a form does not repeat is a guard that a
form submission walks around.

### Enrolling a second factor

The enrolment is the two steps it is, handing the secret to an authenticator application and then
confirming the code that application shows. The provisioning URI is drawn as an SVG QR code by the bundle
itself and embedded in the page, with no image loaded from anywhere: that URI carries the secret, and a QR
code service would read it. The same key is printed in base32 in groups of four for a person who types it,
and taken in one click.

What was drawn lives in the session of that browser for ten minutes, sealed by the key management service
of the tenant, and nowhere else: an enrolment abandoned in front of the QR code leaves nothing behind. A
code that does not match renders the same page with the same QR code, so the application is not rescanned.

The ten backup codes are shown exactly once, as the response to the request that confirmed the enrolment:
one numbered block taken in one click, hashed in the row, and displayed by nothing afterwards. Drawing
another set replaces the previous one whole.

## Every table reads the same way

What a reader learns of one table serves them on the others.

- **Paging** is one word in the query string, `page`, and one number of rows, twenty, for all of them. The
  control under a table is rendered only where there is more than one page, a page nobody can reach is the
  same words without a link, and a number past the last page is the last page.
- **A period** is two words, `from` and `to`, read on the clock of the person the page is served to. Each
  table reads the date a reader looks for: an act by when it happened, a session by when it was opened, a
  passkey or a browser by when it was enrolled, a consent by when it was given.
- **An empty table keeps its head** and says which of the two emptinesses it is, nothing at all or nothing
  over those days, rather than replacing itself with a sentence.
- **Where a request came from** reads the same way everywhere: the place the enrichment of a provenance
  derived from the address, and the browser the user agent names. A deployment that derives no place says
  the address and no place.

## Taking it back

| On this page | The gesture | What it does |
|---|---|---|
| Applications you have allowed | Revoke | Takes back the consent and the access that client holds. The next authorization request asks again |
| Where you are signed in | Close | Ends that session and revokes the tokens issued under it; its OpenID Connect clients are told through the back channel, and when it is the session of this very browser, its SAML service providers are told through it before the page comes back |
| Where you are signed in | Close every other one | Ends every session of this person but the one reading the page, with the same revocation and the same back channel. Those sessions have no browser here, so their SAML service providers are not told |
| Your passkeys | Revoke | Revokes that credential. The line stays, listed as revoked |
| Two-factor authentication | Remove | Revokes the authenticator. The sessions it completed stay as they are |
| Notifications | Revoke | Drops that subscription, and this provider stops reaching that browser |

## Your data

A person asks for everything the provider holds of them and is handed one file, structured and machine
readable, which is what GDPR article 20 asks for. The page says where the last request has got to: never
asked, being built, ready, stalled, or expired.

- **It expires a week after it was asked for**, and that week is a figure in the code rather than an
  option: every day that file exists is a day it exists. The expiry is counted from the ask and not from
  the build, so a request that never ran is forgotten on the same day as one that did.
- **A build is given a quarter of an hour.** Past that, the page says nobody is building this one rather
  than showing a week of work in progress, and asking again opens a new request in its place.
- **It leaves under a passphrase when the person wants one.** The file is then wrapped, and the floor on
  the length of that passphrase, sixteen characters, is refused rather than warned about: what stands
  between that file and whoever took it is the length of what was typed. A person who asks for no
  passphrase downloads the file as it was built.
- **It is sealed where it sits** like every other personal column, in a scope of its own. It is the one
  file in which everything this provider knows of a person stands in clear at once, so it carries no
  exemption.
- **It is dropped when they say so**, in whatever state the request is in: a file they already downloaded
  is a file this provider no longer holds, and a build still on its way finds nothing to write to, which
  is what makes a request something a person can take back. The row goes rather than staying as a row
  marked dropped, since the only state worth keeping of that file is none.

What is in it is one chapter per family the provider holds: the profile, the credentials, the linked
identities, the groups, what was consented to, the sessions, the journal of the acts, and what the record
used to say.

[:beffroi-arrow-right: Personal data](../core/personal-data.md)

## What a form answers

Every form of these pages answers `303 See Other` towards the page it came from, accepted or refused, so
reloading reads the page again instead of sending the form a second time. A refusal travels in the session
of that browser for the one reading that follows: a code the page translates and the field it is about,
never the value that was typed.

Three answers are the response itself and are read once: the backup codes that end an enrolment, the
notice that the session this browser was reading on has ended, and an archive wrapped under a passphrase,
which is the file.

## Dates and language

A signed-in person reads these pages in the language of their record, and changes it where that record is
changed. A date is written on the clock that person holds, with the words and the order of the language
the page is written in, and the clock is always named: an hour without its zone is an hour a reader cannot
check.

[:beffroi-arrow-right: Translations](translations.md)

## Adding a page

A page of the account is a class implementing `Beffroi\Bundle\Http\Account\AccountSectionInterface`,
tagged `beffroi.account_section`: it names the route it opens, the key of its title and what this account
holds there. The home reads the tagged sections in the order they are wired, so a page added is a class
and a line in the wiring, and neither the home nor its template is edited. Two sections naming one route
are a fault of the wiring, and they are refused as such.
